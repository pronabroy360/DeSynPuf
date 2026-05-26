from __future__ import annotations

from tests.test_schema import build_tiny_database

from src.llm.generate_explanation_report import build_explanation_examples, write_markdown_report
from src.llm.patient_risk_explainer import explain_patient_year


def test_explanation_contains_safety_language():
    explanation = explain_patient_year(
        {
            "beneficiary_id": "SYNTH_001",
            "year": 2009,
            "total_synthetic_cost": 12000,
            "inpatient_claims_count": 2,
            "carrier_claims_count": 25,
            "chronic_condition_count": 3,
        }
    )
    assert "synthetic CMS DE-SynPUF data" in explanation
    assert "not clinical advice" in explanation


def test_build_explanation_examples_from_tiny_database(tmp_path):
    con = build_tiny_database(tmp_path)
    db_path = tmp_path / "tiny.duckdb"
    con.close()
    examples = build_explanation_examples(db_path, limit=2)
    assert len(examples) == 2
    assert "explanation" in examples[0]
    assert "features" in examples[0]


def test_write_markdown_report_has_guardrails(tmp_path):
    report_path = tmp_path / "llm_report.md"
    write_markdown_report(
        [
            {
                "beneficiary_id": "SYNTH_001",
                "year": 2009,
                "features": {
                    "age": 74,
                    "chronic_condition_count": 2,
                    "inpatient_claims_count": 1,
                    "outpatient_claims_count": 3,
                    "carrier_claims_count": 5,
                    "prescription_events_count": 2,
                    "total_synthetic_cost": 1000,
                    "risk_percentile": 80,
                },
                "explanation": "This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.",
            }
        ],
        report_path,
    )
    text = report_path.read_text()
    assert "Do not diagnose" in text
    assert "not clinical advice" in text
