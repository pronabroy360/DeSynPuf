from __future__ import annotations

import math

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("pandas")

import pandas as pd

from src.models.train_high_cost_model import (
    sanitize_for_json,
    train_models,
    extract_feature_importance,
    build_evaluation_artifacts,
)


def test_sanitize_for_json_replaces_nan():
    payload = {"metric": float("nan"), "nested": {"value": float("inf")}}
    assert sanitize_for_json(payload) == {"metric": None, "nested": {"value": None}}


def test_train_models_returns_feature_importance():
    df = pd.DataFrame(
        {
            "beneficiary_id": ["A", "B", "C", "D", "A", "B", "C", "D"],
            "input_year": [2008, 2008, 2008, 2008, 2009, 2009, 2009, 2009],
            "target_year": [2009, 2009, 2009, 2009, 2010, 2010, 2010, 2010],
            "age": [70, 72, 80, 66, 71, 73, 81, 67],
            "chronic_condition_count": [3, 1, 4, 0, 3, 1, 4, 0],
            "inpatient_claims_count": [2, 0, 3, 0, 2, 0, 3, 0],
            "outpatient_claims_count": [8, 2, 10, 1, 8, 2, 10, 1],
            "carrier_claims_count": [20, 5, 30, 2, 20, 5, 30, 2],
            "prescription_events_count": [15, 2, 20, 1, 15, 2, 20, 1],
            "inpatient_total_paid": [5000, 0, 9000, 0, 5000, 0, 9000, 0],
            "outpatient_total_paid": [800, 100, 1000, 50, 800, 100, 1000, 50],
            "carrier_total_paid": [600, 80, 900, 30, 600, 80, 900, 30],
            "prescription_total_cost": [400, 20, 700, 10, 400, 20, 700, 10],
            "total_synthetic_cost": [6800, 200, 11600, 90, 6800, 200, 11600, 90],
            "unique_diagnosis_codes": [5, 1, 7, 1, 5, 1, 7, 1],
            "unique_procedure_codes": [3, 1, 4, 0, 3, 1, 4, 0],
            "any_inpatient": [1, 0, 1, 0, 1, 0, 1, 0],
            "repeated_inpatient": [1, 0, 1, 0, 1, 0, 1, 0],
            "sex_code": ["1", "2", "1", "2", "1", "2", "1", "2"],
            "race_code": ["1", "1", "2", "2", "1", "1", "2", "2"],
            "state_code": ["10", "10", "20", "20", "10", "10", "20", "20"],
            "county_code": ["001", "003", "001", "003", "001", "003", "001", "003"],
            "esrd_indicator": ["0", "0", "1", "0", "0", "0", "1", "0"],
            "high_cost_next_year": [1, 0, 1, 0, 1, 0, 1, 0],
        }
    )
    model, metrics, evaluation = train_models(df)
    importance = extract_feature_importance(model)
    assert metrics["best_model"]["name"] in {"logistic_regression", "random_forest"}
    assert not math.isnan(metrics["dataset"]["target_positive_rate"])
    assert len(importance) > 0
    best_name = metrics["best_model"]["name"]
    assert best_name in evaluation["models"]


def test_build_evaluation_artifacts_shapes():
    y_true = pd.Series([0, 1, 0, 1, 1, 0]).to_numpy()
    y_score = pd.Series([0.1, 0.9, 0.4, 0.8, 0.7, 0.2]).to_numpy()
    artifacts = build_evaluation_artifacts(y_true=y_true, y_score=y_score, threshold=0.5)
    assert artifacts["threshold"] == 0.5
    assert len(artifacts["precision_recall_curve"]) > 0
    assert len(artifacts["calibration"]) > 0
    assert "true_positive" in artifacts["confusion_matrix"]
