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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(DEFAULT_DB_PATH)}


@app.get("/patient-year/{beneficiary_id}/{year}")
def patient_year(beneficiary_id: str, year: int) -> dict[str, Any]:
    con = _connect()
    result = con.execute(
        """
        SELECT *
        FROM gold_patient_year_summary
        WHERE beneficiary_id = ?
          AND year = ?
        LIMIT 1
        """,
        [beneficiary_id, year],
    ).df()
    if result.empty:
        raise HTTPException(status_code=404, detail="Synthetic beneficiary-year not found")
    record = result.astype(object).where(result.notna(), None).iloc[0].to_dict()
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in record.items()
    }


@app.get("/patient-year/{beneficiary_id}/{year}/explain")
def patient_year_explanation(beneficiary_id: str, year: int) -> dict[str, Any]:
    features = patient_year(beneficiary_id, year)
    return {
        "beneficiary_id": beneficiary_id,
        "year": year,
        "explanation": explain_patient_year(features),
    }
