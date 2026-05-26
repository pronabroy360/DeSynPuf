from __future__ import annotations

from tests.test_schema import build_tiny_database


def test_gold_patient_year_row_count(tmp_path):
    con = build_tiny_database(tmp_path)
    rows = con.execute("SELECT COUNT(*) FROM gold_patient_year_summary").fetchone()[0]
    assert rows == 4


def test_high_cost_dataset_row_count(tmp_path):
    con = build_tiny_database(tmp_path)
    rows = con.execute("SELECT COUNT(*) FROM gold_high_cost_prediction_dataset").fetchone()[0]
    assert rows == 2
