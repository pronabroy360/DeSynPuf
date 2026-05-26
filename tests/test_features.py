from __future__ import annotations

from tests.test_schema import build_tiny_database


def test_patient_year_cost_rollup(tmp_path):
    con = build_tiny_database(tmp_path)
    total_cost = con.execute(
        """
        SELECT total_synthetic_cost
        FROM gold_patient_year_summary
        WHERE beneficiary_id = 'B1'
          AND year = 2008
        """
    ).fetchone()[0]
    assert total_cost == 2250


def test_high_cost_label(tmp_path):
    con = build_tiny_database(tmp_path)
    labels = con.execute(
        """
        SELECT beneficiary_id, high_cost_next_year
        FROM gold_high_cost_prediction_dataset
        WHERE input_year = 2008
        ORDER BY beneficiary_id
        """
    ).fetchall()
    assert labels == [("B1", 1), ("B2", 0)]
