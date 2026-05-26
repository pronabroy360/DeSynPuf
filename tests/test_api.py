from __future__ import annotations

import json

import pytest

TestClient = pytest.importorskip("fastapi.testclient").TestClient

from src.api import main as api_main
from tests.test_schema import build_tiny_database


def build_client(tmp_path, monkeypatch) -> TestClient:
    con = build_tiny_database(tmp_path)
    con.close()
    db_path = tmp_path / "tiny.duckdb"
    monkeypatch.setattr(api_main, "DEFAULT_DB_PATH", db_path)
    return TestClient(api_main.app)


def test_health_endpoint(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"].endswith("tiny.duckdb")


def test_patient_year_and_explanation_endpoints(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)

    patient_response = client.get("/patient-year/B1/2008")
    assert patient_response.status_code == 200
    patient = patient_response.json()
    assert patient["beneficiary_id"] == "B1"
    assert patient["year"] == 2008

    explanation_response = client.get("/patient-year/B1/2008/explain")
    assert explanation_response.status_code == 200
    explanation = explanation_response.json()
    assert explanation["beneficiary_id"] == "B1"
    assert explanation["year"] == 2008
    assert isinstance(explanation["explanation"], str)
    assert len(explanation["explanation"]) > 0


def test_analytics_endpoints(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)

    overview = client.get("/overview/metrics")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["min_year"] == 2008
    assert overview_payload["max_year"] == 2009

    cost_summary = client.get("/analytics/cost-summary")
    assert cost_summary.status_code == 200
    cost_rows = cost_summary.json()
    assert len(cost_rows) >= 1
    assert "total_synthetic_cost" in cost_rows[0]

    utilization_summary = client.get("/analytics/utilization-summary")
    assert utilization_summary.status_code == 200
    utilization_rows = utilization_summary.json()
    assert len(utilization_rows) >= 1
    assert "inpatient_claims" in utilization_rows[0]

    chronic_summary = client.get("/analytics/chronic-conditions?year=2008")
    assert chronic_summary.status_code == 200
    chronic_rows = chronic_summary.json()
    assert len(chronic_rows) >= 1
    assert all(row["year"] == 2008 for row in chronic_rows)


def test_artifact_endpoints(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)

    model_metrics_path = tmp_path / "model_metrics.json"
    model_comparison_path = tmp_path / "model_comparison.json"
    quality_report_path = tmp_path / "quality_report.json"

    model_metrics_path.write_text(json.dumps({"best_model": {"name": "random_forest"}}))
    model_comparison_path.write_text(json.dumps([{"model": "random_forest", "auprc": 0.25}]))
    quality_report_path.write_text(json.dumps({"status": "pass", "checks": []}))

    monkeypatch.setattr(
        api_main,
        "_artifact_paths",
        lambda: {
            "model_metrics": model_metrics_path,
            "model_comparison": model_comparison_path,
            "quality_report": quality_report_path,
        },
    )

    metrics_response = client.get("/model/metrics")
    assert metrics_response.status_code == 200
    assert metrics_response.json()["best_model"]["name"] == "random_forest"

    comparison_response = client.get("/model/comparison")
    assert comparison_response.status_code == 200
    assert comparison_response.json()[0]["model"] == "random_forest"

    quality_response = client.get("/quality/report")
    assert quality_response.status_code == 200
    assert quality_response.json()["status"] == "pass"
