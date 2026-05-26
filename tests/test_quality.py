from __future__ import annotations

from tests.test_schema import build_tiny_database

from src.quality.validate_warehouse import build_report


def test_quality_report_passes_for_tiny_database(tmp_path):
    con = build_tiny_database(tmp_path)
    report = build_report(con)
    assert report["status"] == "pass"
    assert len(report["checks"]) > 0


def test_quality_report_includes_table_summary(tmp_path):
    con = build_tiny_database(tmp_path)
    report = build_report(con)
    table_names = {row["table_name"] for row in report["table_summary"]}
    assert "gold_patient_year_summary" in table_names
    assert "silver_beneficiaries" in table_names
