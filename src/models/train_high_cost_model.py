from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DEFAULT_DB_PATH = Path("data/processed/desynpuf.duckdb")
DEFAULT_MODEL_PATH = Path("data/processed/high_cost_model.joblib")
DEFAULT_METRICS_PATH = Path("data/processed/model_metrics.json")

NUMERIC_FEATURES = [
    "age",
    "chronic_condition_count",
    "inpatient_claims_count",
    "outpatient_claims_count",
    "carrier_claims_count",
    "prescription_events_count",
    "inpatient_total_paid",
    "outpatient_total_paid",
    "carrier_total_paid",
    "prescription_total_cost",
    "total_synthetic_cost",
    "unique_diagnosis_codes",
    "unique_procedure_codes",
    "any_inpatient",
    "repeated_inpatient",
]

CATEGORICAL_FEATURES = [
    "sex_code",
    "race_code",
    "state_code",
    "county_code",
    "esrd_indicator",
]

TARGET = "high_cost_next_year"


def precision_at_k(y_true: np.ndarray, y_score: np.ndarray, k_fraction: float = 0.10) -> float:
    if len(y_true) == 0:
        return float("nan")
    k = max(1, int(np.ceil(len(y_true) * k_fraction)))
    top_indices = np.argsort(y_score)[-k:]
    return float(np.mean(y_true[top_indices]))


def load_dataset(db_path: Path) -> pd.DataFrame:
    con = duckdb.connect(str(db_path), read_only=True)
    return con.execute(
        """
        SELECT *
        FROM gold_high_cost_prediction_dataset
        WHERE high_cost_next_year IS NOT NULL
        """
    ).df()


def build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    numeric = [column for column in NUMERIC_FEATURES if column in df.columns]
    categorical = [column for column in CATEGORICAL_FEATURES if column in df.columns]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric),
            ("categorical", categorical_pipeline, categorical),
        ],
        remainder="drop",
    )


def train_models(df: pd.DataFrame) -> tuple[Pipeline, dict[str, dict[str, float]]]:
    if df.empty:
        raise ValueError("gold_high_cost_prediction_dataset is empty. Build the Gold tables after loading raw data.")

    train_df = df[df["input_year"] == df["input_year"].min()].copy()
    test_df = df[df["input_year"] == df["input_year"].max()].copy()
    if test_df.empty or train_df["input_year"].iloc[0] == test_df["input_year"].iloc[0]:
        train_df = df.sample(frac=0.75, random_state=42)
        test_df = df.drop(train_df.index)

    if test_df.empty:
        raise ValueError("Not enough rows to create a test set.")

    feature_columns = [column for column in NUMERIC_FEATURES + CATEGORICAL_FEATURES if column in df.columns]
    x_train = train_df[feature_columns]
    y_train = train_df[TARGET].astype(int)
    x_test = test_df[feature_columns]
    y_test = test_df[TARGET].astype(int).to_numpy()

    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=5,
            random_state=42,
            class_weight="balanced_subsample",
            n_jobs=-1,
        ),
    }

    metrics: dict[str, dict[str, float]] = {}
    fitted_models: dict[str, Pipeline] = {}
    for name, estimator in models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocess", build_preprocessor(df)),
                ("model", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        if hasattr(pipeline.named_steps["model"], "predict_proba"):
            y_score = pipeline.predict_proba(x_test)[:, 1]
        else:
            y_score = pipeline.decision_function(x_test)
        y_pred = (y_score >= 0.5).astype(int)

        precision, recall, _ = precision_recall_curve(y_test, y_score)
        metrics[name] = {
            "auroc": float(roc_auc_score(y_test, y_score)) if len(np.unique(y_test)) > 1 else float("nan"),
            "auprc": float(average_precision_score(y_test, y_score)) if len(np.unique(y_test)) > 1 else float("nan"),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "precision_at_10_percent": precision_at_k(y_test, y_score, 0.10),
            "pr_curve_points": int(len(precision)),
            "recall_max": float(np.max(recall)) if len(recall) else float("nan"),
        }
        fitted_models[name] = pipeline

    best_name = max(
        metrics,
        key=lambda name: metrics[name]["auprc"] if not np.isnan(metrics[name]["auprc"]) else -1,
    )
    return fitted_models[best_name], {"best_model": {"name": best_name}, **metrics}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train high-cost beneficiary prediction models.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--model-out", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_dataset(args.db)
    model, metrics = train_models(df)

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_out)
    args.metrics_out.write_text(json.dumps(metrics, indent=2, sort_keys=True))

    print(f"Saved model: {args.model_out}")
    print(f"Saved metrics: {args.metrics_out}")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
