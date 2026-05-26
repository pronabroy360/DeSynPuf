from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException

from src.llm.patient_risk_explainer import explain_patient_year


DEFAULT_DB_PATH = Path(os.environ.get("DESYNPUF_DB", "data/processed/desynpuf.duckdb"))

app = FastAPI(
    title="CMS DE-SynPUF Claims Analytics API",
    description="Synthetic Medicare-style claims analytics API backed by DuckDB.",
    version="0.1.0",
)


def _connect() -> duckdb.DuckDBPyConnection:
    if not DEFAULT_DB_PATH.exists():
        raise HTTPException(status_code=503, detail=f"DuckDB database not found at {DEFAULT_DB_PATH}")
    return duckdb.connect(str(DEFAULT_DB_PATH), read_only=True)


def _artifact_paths() -> dict[str, Path]:
    if DEFAULT_DB_PATH.name.startswith("demo_"):
        return {
            "model_metrics": Path("data/processed/demo_model_metrics.json"),
            "model_comparison": Path("data/processed/demo_model_comparison.json"),
            "quality_report": Path("data/processed/demo_quality_report.json"),
        }
    return {
        "model_metrics": Path("data/processed/model_metrics.json"),
        "model_comparison": Path("data/processed/model_comparison.json"),
        "quality_report": Path("data/processed/quality_report.json"),
    }


def _as_jsonable_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in row.items()
    }


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {path}")
    import json

    return json.loads(path.read_text())


def _query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    con = _connect()
    df = con.execute(sql, params or []).df()
    if df.empty:
        return []
    rows = df.astype(object).where(df.notna(), None).to_dict(orient="records")
    return [_as_jsonable_row(row) for row in rows]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(DEFAULT_DB_PATH)}


@app.get("/overview/metrics")
def overview_metrics() -> dict[str, Any]:
    rows = _query(
        """
        SELECT
            MIN(year) AS min_year,
            MAX(year) AS max_year,
            SUM(beneficiaries) AS beneficiary_years,
            SUM(total_synthetic_cost) AS total_synthetic_cost,
            AVG(avg_synthetic_cost) AS avg_annual_cost
        FROM gold_patient_cost_summary
        """
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No overview metrics found")
    summary = rows[0]
    summary["database"] = str(DEFAULT_DB_PATH)
    return summary


@app.get("/analytics/cost-summary")
def cost_summary() -> list[dict[str, Any]]:
    rows = _query("SELECT * FROM gold_patient_cost_summary ORDER BY year")
    if not rows:
        raise HTTPException(status_code=404, detail="No cost summary rows found")
    return rows


@app.get("/analytics/utilization-summary")
def utilization_summary() -> list[dict[str, Any]]:
    rows = _query("SELECT * FROM gold_patient_utilization_summary ORDER BY year")
    if not rows:
        raise HTTPException(status_code=404, detail="No utilization summary rows found")
    return rows


@app.get("/analytics/chronic-conditions")
def chronic_condition_summary(year: int | None = None) -> list[dict[str, Any]]:
    if year is None:
        rows = _query(
            """
            SELECT *
            FROM gold_patient_chronic_condition_summary
            ORDER BY year, condition_name
            """
        )
    else:
        rows = _query(
            """
            SELECT *
            FROM gold_patient_chronic_condition_summary
            WHERE year = ?
            ORDER BY condition_name
            """,
            [year],
        )
    if not rows:
        raise HTTPException(status_code=404, detail="No chronic-condition summary rows found")
    return rows


@app.get("/patient-year/{beneficiary_id}/{year}")
def patient_year(beneficiary_id: str, year: int) -> dict[str, Any]:
    rows = _query(
        """
        SELECT *
        FROM gold_patient_year_summary
        WHERE beneficiary_id = ?
          AND year = ?
        LIMIT 1
        """,
        [beneficiary_id, year],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Synthetic beneficiary-year not found")
    return rows[0]


@app.get("/patient-year/{beneficiary_id}/{year}/explain")
def patient_year_explanation(beneficiary_id: str, year: int) -> dict[str, Any]:
    features = patient_year(beneficiary_id, year)
    return {
        "beneficiary_id": beneficiary_id,
        "year": year,
        "explanation": explain_patient_year(features),
    }


@app.get("/model/metrics")
def model_metrics() -> dict[str, Any]:
    paths = _artifact_paths()
    payload = _read_json(paths["model_metrics"])
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Model metrics artifact has invalid format")
    return payload


@app.get("/model/comparison")
def model_comparison() -> list[dict[str, Any]]:
    paths = _artifact_paths()
    payload = _read_json(paths["model_comparison"])
    if not isinstance(payload, list):
        raise HTTPException(status_code=500, detail="Model comparison artifact has invalid format")
    return payload


@app.get("/quality/report")
def quality_report() -> dict[str, Any]:
    paths = _artifact_paths()
    payload = _read_json(paths["quality_report"])
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Quality report artifact has invalid format")
    return payload
