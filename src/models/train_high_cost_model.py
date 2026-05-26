from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    roc_curve,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DEFAULT_DB_PATH = Path("data/processed/desynpuf.duckdb")
DEFAULT_MODEL_PATH = Path("data/processed/high_cost_model.joblib")
DEFAULT_METRICS_PATH = Path("data/processed/model_metrics.json")
DEFAULT_IMPORTANCE_PATH = Path("data/processed/model_feature_importance.json")
DEFAULT_EVALUATION_PATH = Path("data/processed/model_evaluation.json")
DEFAULT_REPORT_PATH = Path("docs/latest_model_report.md")

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


def sanitize_for_json(value):
    if isinstance(value, dict):
        return {key: sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def precision_at_k(y_true: np.ndarray, y_score: np.ndarray, k_fraction: float = 0.10) -> float:
    if len(y_true) == 0:
        return float("nan")
    k = max(1, int(np.ceil(len(y_true) * k_fraction)))
    top_indices = np.argsort(y_score)[-k:]
    return float(np.mean(y_true[top_indices]))


def _downsample_curve(points: list[dict[str, float]], max_points: int = 200) -> list[dict[str, float]]:
    if len(points) <= max_points:
        return points
    indices = np.linspace(0, len(points) - 1, max_points, dtype=int)
    return [points[idx] for idx in indices]


def build_evaluation_artifacts(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, object]:
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    precision, recall, pr_thresholds = precision_recall_curve(y_true, y_score)
    pr_points = [
        {
            "recall": float(recall[idx]),
            "precision": float(precision[idx]),
            "threshold": float(pr_thresholds[idx]) if idx < len(pr_thresholds) else 1.0,
        }
        for idx in range(len(precision))
    ]

    roc_points: list[dict[str, float]] = []
    if len(np.unique(y_true)) > 1:
        fpr, tpr, roc_thresholds = roc_curve(y_true, y_score)
        roc_points = [
            {
                "fpr": float(fpr[idx]),
                "tpr": float(tpr[idx]),
                "threshold": float(roc_thresholds[idx]),
            }
            for idx in range(len(fpr))
        ]

    bin_count = int(min(10, max(3, len(y_true))))
    prob_true, prob_pred = calibration_curve(y_true, y_score, n_bins=bin_count, strategy="quantile")
    calibration_points = [
        {"mean_predicted_probability": float(prob_pred[idx]), "observed_rate": float(prob_true[idx])}
        for idx in range(len(prob_true))
    ]

    return {
        "threshold": float(threshold),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "calibration": _downsample_curve(calibration_points, max_points=50),
        "precision_recall_curve": _downsample_curve(pr_points),
        "roc_curve": _downsample_curve(roc_points),
        "brier_score": float(brier_score_loss(y_true, y_score)),
        "positive_rate_test": float(np.mean(y_true)),
        "predicted_positive_rate_test": float(np.mean(y_pred)),
    }


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


def train_models(df: pd.DataFrame) -> tuple[Pipeline, dict[str, object], dict[str, object]]:
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
    evaluations: dict[str, dict[str, object]] = {}
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
        evaluations[name] = build_evaluation_artifacts(y_true=y_test, y_score=y_score, threshold=0.5)

    best_name = max(
        metrics,
        key=lambda name: metrics[name]["auprc"] if not np.isnan(metrics[name]["auprc"]) else -1,
    )
    return fitted_models[best_name], {
        "best_model": {"name": best_name},
        "dataset": {
            "rows": int(len(df)),
            "train_rows": int(len(train_df)),
            "test_rows": int(len(test_df)),
            "input_years": [int(year) for year in sorted(df["input_year"].dropna().unique())],
            "target_positive_rate": float(df[TARGET].mean()),
        },
        **metrics,
    }, {
        "best_model": best_name,
        "models": evaluations,
    }


def extract_feature_importance(model: Pipeline, top_n: int = 30) -> list[dict[str, float | str]]:
    preprocessor = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    try:
        feature_names = list(preprocessor.get_feature_names_out())
    except Exception:
        feature_names = [f"feature_{idx}" for idx in range(getattr(estimator, "n_features_in_", 0))]

    if hasattr(estimator, "feature_importances_"):
        values = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        values = np.abs(np.asarray(estimator.coef_, dtype=float)).ravel()
    else:
        return []

    rows = [
        {
            "feature": feature_names[idx],
            "importance": float(values[idx]),
        }
        for idx in range(min(len(feature_names), len(values)))
    ]
    rows.sort(key=lambda row: row["importance"], reverse=True)
    return rows[:top_n]


def write_model_report(
    metrics: dict[str, object],
    feature_importance: list[dict[str, float | str]],
    output_path: Path,
) -> None:
    def display_metric(value: object) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    best_name = metrics.get("best_model", {}).get("name", "unknown")  # type: ignore[union-attr]
    dataset = metrics.get("dataset", {})  # type: ignore[assignment]
    lines = [
        "# Latest High-Cost Prediction Model Report",
        "",
        "This report summarizes aggregate model-training outputs from synthetic CMS DE-SynPUF data.",
        "It is not a clinical validation report and should not be interpreted as real-world model performance.",
        "",
        f"Best model: **{best_name}**",
        "",
        "## Dataset",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    if isinstance(dataset, dict):
        for key, value in dataset.items():
            lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| Model | AUROC | AUPRC | F1 | Precision | Precision@10% |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for model_name, values in metrics.items():
        if model_name in {"best_model", "dataset"} or not isinstance(values, dict):
            continue
        lines.append(
            "| "
            + f"`{model_name}` | "
            + f"{display_metric(values.get('auroc'))} | "
            + f"{display_metric(values.get('auprc'))} | "
            + f"{display_metric(values.get('f1'))} | "
            + f"{display_metric(values.get('precision'))} | "
            + f"{display_metric(values.get('precision_at_10_percent'))} |"
        )

    lines.extend(
        [
            "",
            "## Top Feature Importance",
            "",
            "| Rank | Feature | Importance |",
            "| ---: | --- | ---: |",
        ]
    )
    for idx, row in enumerate(feature_importance[:20], start=1):
        lines.append(f"| {idx} | `{row['feature']}` | {row['importance']:.6f} |")
    output_path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train high-cost beneficiary prediction models.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--model-out", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--feature-importance-out", type=Path, default=DEFAULT_IMPORTANCE_PATH)
    parser.add_argument("--evaluation-out", type=Path, default=DEFAULT_EVALUATION_PATH)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_dataset(args.db)
    model, metrics, evaluation = train_models(df)
    feature_importance = extract_feature_importance(model)

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_out)
    args.metrics_out.write_text(json.dumps(sanitize_for_json(metrics), indent=2, sort_keys=True))
    args.feature_importance_out.write_text(
        json.dumps(sanitize_for_json(feature_importance), indent=2, sort_keys=True)
    )
    args.evaluation_out.write_text(json.dumps(sanitize_for_json(evaluation), indent=2, sort_keys=True))
    write_model_report(sanitize_for_json(metrics), feature_importance, args.report_md)

    print(f"Saved model: {args.model_out}")
    print(f"Saved metrics: {args.metrics_out}")
    print(f"Saved feature importance: {args.feature_importance_out}")
    print(f"Saved evaluation artifacts: {args.evaluation_out}")
    print(f"Saved model report: {args.report_md}")
    print(json.dumps(sanitize_for_json(metrics), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
