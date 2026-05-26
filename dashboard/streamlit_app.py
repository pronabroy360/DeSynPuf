from __future__ import annotations

import json
import os
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from src.llm.patient_risk_explainer import explain_patient_year


DB_PATH = Path(os.environ.get("DESYNPUF_DB", "data/processed/desynpuf.duckdb"))
if DB_PATH.name.startswith("demo_"):
    METRICS_PATH = Path("data/processed/demo_model_metrics.json")
    FEATURE_IMPORTANCE_PATH = Path("data/processed/demo_model_feature_importance.json")
    EVALUATION_PATH = Path("data/processed/demo_model_evaluation.json")
    COMPARISON_PATH = Path("data/processed/demo_model_comparison.json")
    QUALITY_REPORT_JSON = Path("data/processed/demo_quality_report.json")
    QUALITY_REPORT_MD = Path("docs/demo_quality_report.md")
    MODEL_REPORT_MD = Path("docs/demo_model_report.md")
    COMPARISON_REPORT_MD = Path("docs/demo_model_comparison_report.md")
    LLM_REPORT_MD = Path("docs/demo_llm_explanation_report.md")
    PROFESSOR_PACKET_MD = Path("docs/demo_professor_packet.md")
else:
    METRICS_PATH = Path("data/processed/model_metrics.json")
    FEATURE_IMPORTANCE_PATH = Path("data/processed/model_feature_importance.json")
    EVALUATION_PATH = Path("data/processed/model_evaluation.json")
    COMPARISON_PATH = Path("data/processed/model_comparison.json")
    QUALITY_REPORT_JSON = Path("data/processed/quality_report.json")
    QUALITY_REPORT_MD = Path("docs/latest_quality_report.md")
    MODEL_REPORT_MD = Path("docs/latest_model_report.md")
    COMPARISON_REPORT_MD = Path("docs/latest_model_comparison_report.md")
    LLM_REPORT_MD = Path("docs/latest_llm_explanation_report.md")
    PROFESSOR_PACKET_MD = Path("docs/latest_professor_packet.md")


st.set_page_config(
    page_title="DE-SynPUF Claims Analytics",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
      --ink: #17201c;
      --sage: #7f9172;
      --linen: #f6efe3;
      --clay: #b8664d;
      --teal: #1d6f73;
    }
    .stApp {
      background:
        radial-gradient(circle at top left, rgba(184,102,77,.18), transparent 30rem),
        linear-gradient(135deg, #fbf7ef 0%, #edf3ed 55%, #e6f0f1 100%);
      color: var(--ink);
    }
    div[data-testid="stMetric"] {
      background: rgba(255,255,255,.70);
      border: 1px solid rgba(23,32,28,.10);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 10px 28px rgba(23,32,28,.08);
    }
    section[data-testid="stSidebar"] {
      background: #17201c;
    }
    section[data-testid="stSidebar"] * {
      color: #f6efe3;
    }
    .hero-card {
      background:
        linear-gradient(135deg, rgba(23,32,28,.92), rgba(29,111,115,.84)),
        radial-gradient(circle at top right, rgba(215,168,79,.35), transparent 22rem);
      border-radius: 26px;
      padding: 28px 30px;
      color: #f6efe3;
      box-shadow: 0 18px 48px rgba(23,32,28,.18);
      margin-bottom: 20px;
    }
    .hero-card h1 {
      margin-bottom: 8px;
      color: #fff8ec;
    }
    .hero-card p {
      font-size: 1.05rem;
      max-width: 850px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_connection(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path, read_only=True)


@st.cache_data(show_spinner=False)
def query_df(sql: str, db_path: str = str(DB_PATH)) -> pd.DataFrame:
    con = get_connection(db_path)
    return con.execute(sql).df()


def database_ready() -> bool:
    return DB_PATH.exists()


def jsonable_record(record: dict) -> dict:
    clean = {}
    for key, value in record.items():
        if pd.isna(value):
            clean[key] = None
        elif hasattr(value, "isoformat"):
            clean[key] = value.isoformat()
        else:
            clean[key] = value
    return clean


def require_database() -> bool:
    if database_ready():
        return True
    st.title("DE-SynPUF Claims Analytics")
    st.info("No DuckDB database found yet. Download CMS Sample 1 files into data/raw, then run `make ingest` and `make transform`.")
    st.code(
        "python3 -m src.ingest.load_raw_files --raw-dir data/raw --db data/processed/desynpuf.duckdb\n"
        "python3 -m src.transform.build_claims_mart --db data/processed/desynpuf.duckdb",
        language="bash",
    )
    return False


def hero() -> None:
    st.markdown(
        f"""
        <div class="hero-card">
          <h1>DE-SynPUF Claims Analytics Workbench</h1>
          <p>
            A reproducible synthetic Medicare claims warehouse, risk modeling, and explanation layer.
            Active database: <strong>{DB_PATH}</strong>.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(summary: pd.DataFrame) -> None:
    total_beneficiaries = int(summary["beneficiaries"].sum()) if not summary.empty else 0
    total_cost = float(summary["total_synthetic_cost"].sum()) if not summary.empty else 0
    avg_cost = float(summary["avg_synthetic_cost"].mean()) if not summary.empty else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Beneficiary-years", f"{total_beneficiaries:,}")
    col2.metric("Total synthetic cost", f"${total_cost:,.0f}")
    col3.metric("Avg annual cost", f"${avg_cost:,.0f}")


def markdown_report(path: Path, title: str) -> None:
    if path.exists():
        with st.expander(title, expanded=False):
            st.markdown(path.read_text())
    else:
        st.info(f"{title} has not been generated yet: `{path}`")


def overview_page() -> None:
    hero()
    st.title("Claims Warehouse Overview")
    st.caption("Synthetic CMS DE-SynPUF analytics. Not clinical evidence.")
    summary = query_df("SELECT * FROM gold_patient_cost_summary ORDER BY year")
    utilization = query_df("SELECT * FROM gold_patient_utilization_summary ORDER BY year")
    metric_row(summary)
    col1, col2 = st.columns([1.2, 1])
    with col1:
        chart = alt.Chart(summary).mark_area(opacity=0.75, color="#1d6f73").encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("total_synthetic_cost:Q", title="Total synthetic cost"),
            tooltip=["year", alt.Tooltip("total_synthetic_cost:Q", format="$,.0f")],
        )
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.subheader("Utilization Summary")
        st.dataframe(utilization, use_container_width=True, hide_index=True)
    st.subheader("Highest-Cost Synthetic Beneficiary-Years")
    top_patients = query_df(
        """
        SELECT
            beneficiary_id,
            year,
            age,
            chronic_condition_count,
            inpatient_claims_count,
            outpatient_claims_count,
            carrier_claims_count,
            prescription_events_count,
            total_synthetic_cost
        FROM gold_patient_year_summary
        ORDER BY total_synthetic_cost DESC
        LIMIT 10
        """
    )
    st.dataframe(top_patients, use_container_width=True, hide_index=True)


def cost_analytics_page() -> None:
    st.title("Cost Analytics")
    summary = query_df("SELECT * FROM gold_patient_cost_summary ORDER BY year")
    if summary.empty:
        st.warning("No cost summary rows found.")
        return
    long_costs = summary.melt(
        id_vars=["year"],
        value_vars=["inpatient_total_paid", "outpatient_total_paid", "carrier_total_paid", "prescription_total_cost"],
        var_name="claim_type",
        value_name="cost",
    )
    chart = alt.Chart(long_costs).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("cost:Q", title="Synthetic cost"),
        color=alt.Color("claim_type:N", scale=alt.Scale(range=["#b8664d", "#1d6f73", "#7f9172", "#d7a84f"])),
        tooltip=["year", "claim_type", alt.Tooltip("cost:Q", format="$,.0f")],
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)


def utilization_page() -> None:
    st.title("Utilization Analytics")
    utilization = query_df("SELECT * FROM gold_patient_utilization_summary ORDER BY year")
    if utilization.empty:
        st.warning("No utilization rows found.")
        return
    long_counts = utilization.melt(
        id_vars=["year"],
        value_vars=["inpatient_claims", "outpatient_claims", "carrier_claims", "prescription_events"],
        var_name="event_type",
        value_name="events",
    )
    chart = alt.Chart(long_counts).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("events:Q", title="Claims/events"),
        color=alt.Color("event_type:N", scale=alt.Scale(range=["#b8664d", "#1d6f73", "#7f9172", "#d7a84f"])),
        tooltip=["year", "event_type", alt.Tooltip("events:Q", format=",")],
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(utilization, use_container_width=True, hide_index=True)


def chronic_conditions_page() -> None:
    st.title("Chronic Condition Analytics")
    chronic = query_df(
        """
        SELECT
            year,
            condition_name,
            beneficiaries_with_condition,
            avg_cost_with_condition,
            avg_cost_without_condition,
            avg_cost_with_condition - avg_cost_without_condition AS avg_cost_difference
        FROM gold_patient_chronic_condition_summary
        ORDER BY year, avg_cost_difference DESC
        """
    )
    if chronic.empty:
        st.warning("No chronic-condition summary rows found.")
        return

    year_options = sorted(chronic["year"].dropna().unique())
    selected_year = st.selectbox("Year", year_options, index=len(year_options) - 1)
    year_df = chronic[chronic["year"] == selected_year].copy()
    chart = alt.Chart(year_df).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
        x=alt.X("avg_cost_difference:Q", title="Avg synthetic cost difference"),
        y=alt.Y("condition_name:N", sort="-x", title="Condition flag"),
        color=alt.condition(
            alt.datum.avg_cost_difference > 0,
            alt.value("#b8664d"),
            alt.value("#1d6f73"),
        ),
        tooltip=[
            "condition_name",
            alt.Tooltip("beneficiaries_with_condition:Q", format=","),
            alt.Tooltip("avg_cost_with_condition:Q", format="$,.0f"),
            alt.Tooltip("avg_cost_without_condition:Q", format="$,.0f"),
            alt.Tooltip("avg_cost_difference:Q", format="$,.0f"),
        ],
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(year_df, use_container_width=True, hide_index=True)


def cohort_explorer_page() -> None:
    st.title("Cohort Explorer")
    bounds = query_df(
        """
        SELECT
            MIN(year) AS min_year,
            MAX(year) AS max_year,
            MIN(total_synthetic_cost) AS min_cost,
            MAX(total_synthetic_cost) AS max_cost
        FROM gold_patient_year_summary
        """
    ).iloc[0]
    selected_years = st.slider(
        "Year range",
        min_value=int(bounds["min_year"]),
        max_value=int(bounds["max_year"]),
        value=(int(bounds["min_year"]), int(bounds["max_year"])),
    )
    min_cost = st.number_input(
        "Minimum total synthetic cost",
        min_value=0.0,
        max_value=float(bounds["max_cost"] or 0),
        value=0.0,
        step=100.0,
    )
    repeated_only = st.checkbox("Repeated inpatient only")
    repeated_clause = "AND repeated_inpatient = 1" if repeated_only else ""
    cohort = query_df(
        f"""
        SELECT
            beneficiary_id,
            year,
            age,
            chronic_condition_count,
            inpatient_claims_count,
            outpatient_claims_count,
            carrier_claims_count,
            prescription_events_count,
            total_synthetic_cost,
            repeated_inpatient
        FROM gold_patient_year_summary
        WHERE year BETWEEN {int(selected_years[0])} AND {int(selected_years[1])}
          AND total_synthetic_cost >= {float(min_cost)}
          {repeated_clause}
        ORDER BY total_synthetic_cost DESC
        LIMIT 200
        """
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{len(cohort):,}")
    col2.metric("Avg synthetic cost", f"${cohort['total_synthetic_cost'].mean() if not cohort.empty else 0:,.0f}")
    col3.metric("Repeated inpatient rows", f"{int(cohort['repeated_inpatient'].sum()) if not cohort.empty else 0:,}")
    st.dataframe(cohort, use_container_width=True, hide_index=True)


def risk_model_page() -> None:
    st.title("Risk Model")
    model_data = query_df(
        """
        SELECT input_year, target_year, COUNT(*) AS rows, AVG(high_cost_next_year) AS high_cost_rate
        FROM gold_high_cost_prediction_dataset
        GROUP BY input_year, target_year
        ORDER BY input_year, target_year
        """
    )
    st.dataframe(model_data, use_container_width=True, hide_index=True)
    metrics_payload: dict = {}
    if METRICS_PATH.exists():
        st.subheader("Saved Model Metrics")
        metrics_payload = json.loads(METRICS_PATH.read_text())
        st.json(metrics_payload)
        metric_rows = []
        for model_name, values in metrics_payload.items():
            if model_name in {"best_model", "dataset"} or not isinstance(values, dict):
                continue
            metric_rows.append(
                {
                    "model": model_name,
                    "auprc": values.get("auprc"),
                    "auroc": values.get("auroc"),
                    "f1": values.get("f1"),
                    "precision": values.get("precision"),
                    "precision_at_10_percent": values.get("precision_at_10_percent"),
                }
            )
        metrics_df = pd.DataFrame(metric_rows)
        if not metrics_df.empty:
            st.subheader("Model Comparison")
            comparison_long = metrics_df.melt(
                id_vars=["model"],
                value_vars=["f1", "precision", "precision_at_10_percent"],
                var_name="metric",
                value_name="value",
            )
            comp_chart = alt.Chart(comparison_long).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("metric:N", title="Metric"),
                y=alt.Y("value:Q", title="Score"),
                color=alt.Color("model:N", scale=alt.Scale(range=["#b8664d", "#1d6f73"])),
                column=alt.Column("model:N", title="Model"),
                tooltip=["model", "metric", alt.Tooltip("value:Q", format=".4f")],
            )
            st.altair_chart(comp_chart, use_container_width=True)
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    else:
        st.info("No trained model metrics yet. Run `make train` after building the Gold tables.")
    if COMPARISON_PATH.exists():
        st.subheader("Comparison Artifact")
        comparison_df = pd.DataFrame(json.loads(COMPARISON_PATH.read_text()))
        if not comparison_df.empty:
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    if FEATURE_IMPORTANCE_PATH.exists():
        st.subheader("Top Feature Importance")
        importance = pd.DataFrame(json.loads(FEATURE_IMPORTANCE_PATH.read_text()))
        if not importance.empty:
            chart = alt.Chart(importance.head(20)).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X("importance:Q", title="Importance"),
                y=alt.Y("feature:N", sort="-x", title="Feature"),
                color=alt.value("#b8664d"),
                tooltip=["feature", alt.Tooltip("importance:Q", format=".4f")],
            )
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(importance, use_container_width=True, hide_index=True)
    if EVALUATION_PATH.exists():
        st.subheader("Evaluation Curves")
        evaluation = json.loads(EVALUATION_PATH.read_text())
        model_names = sorted(list((evaluation.get("models") or {}).keys()))
        if not model_names:
            st.warning("Evaluation file exists but contains no model entries.")
            return
        default_model = evaluation.get("best_model") if evaluation.get("best_model") in model_names else model_names[0]
        selected_model = st.selectbox("Model for curve inspection", model_names, index=model_names.index(default_model))
        model_eval = (evaluation.get("models") or {}).get(selected_model, {})
        pr_df = pd.DataFrame(model_eval.get("precision_recall_curve") or [])
        roc_df = pd.DataFrame(model_eval.get("roc_curve") or [])
        calibration_df = pd.DataFrame(model_eval.get("calibration") or [])
        cm = model_eval.get("confusion_matrix") or {}
        threshold_metrics_df = pd.DataFrame(model_eval.get("threshold_metrics") or [])
        selected_threshold = st.slider("Threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
        selected_threshold_row = None
        if not threshold_metrics_df.empty:
            threshold_metrics_df["threshold_delta"] = (threshold_metrics_df["threshold"] - selected_threshold).abs()
            selected_threshold_row = threshold_metrics_df.sort_values("threshold_delta").iloc[0].to_dict()
        if not pr_df.empty:
            pr_chart = alt.Chart(pr_df).mark_line(strokeWidth=3, color="#1d6f73").encode(
                x=alt.X("recall:Q", title="Recall"),
                y=alt.Y("precision:Q", title="Precision"),
                tooltip=[
                    alt.Tooltip("threshold:Q", format=".4f"),
                    alt.Tooltip("recall:Q", format=".4f"),
                    alt.Tooltip("precision:Q", format=".4f"),
                ],
            )
            st.caption(f"Precision-Recall curve ({selected_model})")
            st.altair_chart(pr_chart, use_container_width=True)
        if not roc_df.empty:
            roc_chart = alt.Chart(roc_df).mark_line(strokeWidth=3, color="#b8664d").encode(
                x=alt.X("fpr:Q", title="False positive rate"),
                y=alt.Y("tpr:Q", title="True positive rate"),
                tooltip=[
                    alt.Tooltip("threshold:Q", format=".4f"),
                    alt.Tooltip("fpr:Q", format=".4f"),
                    alt.Tooltip("tpr:Q", format=".4f"),
                ],
            )
            st.caption(f"ROC curve ({selected_model})")
            st.altair_chart(roc_chart, use_container_width=True)
        if not calibration_df.empty:
            cal_chart = (
                alt.Chart(calibration_df)
                .mark_line(point=True, strokeWidth=3, color="#7f9172")
                .encode(
                    x=alt.X("mean_predicted_probability:Q", title="Mean predicted probability"),
                    y=alt.Y("observed_rate:Q", title="Observed event rate"),
                    tooltip=[
                        alt.Tooltip("mean_predicted_probability:Q", format=".4f"),
                        alt.Tooltip("observed_rate:Q", format=".4f"),
                    ],
                )
            )
            st.caption(f"Calibration curve ({selected_model})")
            st.altair_chart(cal_chart, use_container_width=True)
        if selected_threshold_row:
            st.subheader(f"Threshold Metrics ({selected_threshold_row['threshold']:.2f})")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Precision", f"{selected_threshold_row['precision']:.3f}")
            col2.metric("Recall", f"{selected_threshold_row['recall']:.3f}")
            col3.metric("Specificity", f"{selected_threshold_row['specificity']:.3f}")
            col4.metric("Predicted positive rate", f"{selected_threshold_row['predicted_positive_rate']:.3f}")
            cm_df = pd.DataFrame(
                [
                    {"metric": "True negatives", "value": int(selected_threshold_row["true_negative"])},
                    {"metric": "False positives", "value": int(selected_threshold_row["false_positive"])},
                    {"metric": "False negatives", "value": int(selected_threshold_row["false_negative"])},
                    {"metric": "True positives", "value": int(selected_threshold_row["true_positive"])},
                ]
            )
            st.dataframe(cm_df, use_container_width=True, hide_index=True)
        if cm:
            st.subheader("Confusion Matrix At Threshold 0.50")
            cm_df = pd.DataFrame(
                [
                    {"metric": "True negatives", "value": cm.get("true_negative", 0)},
                    {"metric": "False positives", "value": cm.get("false_positive", 0)},
                    {"metric": "False negatives", "value": cm.get("false_negative", 0)},
                    {"metric": "True positives", "value": cm.get("true_positive", 0)},
                ]
            )
            st.dataframe(cm_df, use_container_width=True, hide_index=True)
    else:
        st.info("No evaluation artifact yet. Re-run `make train` or `make demo-train`.")
    markdown_report(MODEL_REPORT_MD, "Model Report")
    markdown_report(COMPARISON_REPORT_MD, "Model Comparison Report")


def patient_explainer_page() -> None:
    st.title("Patient Explainer")
    ids = query_df(
        """
        SELECT beneficiary_id, year, total_synthetic_cost
        FROM gold_patient_year_summary
        ORDER BY total_synthetic_cost DESC
        LIMIT 1000
        """
    )
    if ids.empty:
        st.warning("No patient-year rows available.")
        return

    labels = [f"{row.beneficiary_id} | {int(row.year)} | ${row.total_synthetic_cost:,.0f}" for row in ids.itertuples()]
    selected = st.selectbox("Select a synthetic beneficiary-year", labels)
    selected_index = labels.index(selected)
    row = ids.iloc[selected_index]
    features = query_df(
        f"""
        SELECT *
        FROM gold_patient_year_summary
        WHERE beneficiary_id = '{str(row.beneficiary_id).replace("'", "''")}'
          AND year = {int(row.year)}
        LIMIT 1
        """
    )
    feature_dict = jsonable_record(features.iloc[0].to_dict())
    st.write(explain_patient_year(feature_dict))
    with st.expander("Structured features"):
        st.json(feature_dict)
    markdown_report(LLM_REPORT_MD, "Batch Explanation Examples")


def quality_reports_page() -> None:
    st.title("Quality & Reports")
    if QUALITY_REPORT_JSON.exists():
        report = json.loads(QUALITY_REPORT_JSON.read_text())
        col1, col2 = st.columns(2)
        col1.metric("Quality status", str(report.get("status", "unknown")).upper())
        checks = pd.DataFrame(report.get("checks", []))
        failures = 0 if checks.empty else int((checks["status"] != "pass").sum())
        col2.metric("Failed checks", f"{failures:,}")
        if not checks.empty:
            st.subheader("Validation Checks")
            st.dataframe(checks, use_container_width=True, hide_index=True)
        table_summary = pd.DataFrame(report.get("table_summary", []))
        if not table_summary.empty:
            st.subheader("Warehouse Table Row Counts")
            st.dataframe(table_summary, use_container_width=True, hide_index=True)
    else:
        st.info(f"No quality JSON report found yet: `{QUALITY_REPORT_JSON}`")
    markdown_report(QUALITY_REPORT_MD, "Quality Markdown Report")
    markdown_report(MODEL_REPORT_MD, "Model Markdown Report")
    markdown_report(COMPARISON_REPORT_MD, "Model Comparison Markdown Report")
    markdown_report(LLM_REPORT_MD, "LLM Explanation Markdown Report")
    markdown_report(PROFESSOR_PACKET_MD, "Professor Packet")


def main() -> None:
    if not require_database():
        return
    page = st.sidebar.radio(
        "Dashboard Pages",
        [
            "Overview",
            "Cost Analytics",
            "Utilization Analytics",
            "Chronic Conditions",
            "Cohort Explorer",
            "Risk Model",
            "Patient Explainer",
            "Quality & Reports",
        ],
    )
    if page == "Overview":
        overview_page()
    elif page == "Cost Analytics":
        cost_analytics_page()
    elif page == "Utilization Analytics":
        utilization_page()
    elif page == "Chronic Conditions":
        chronic_conditions_page()
    elif page == "Cohort Explorer":
        cohort_explorer_page()
    elif page == "Risk Model":
        risk_model_page()
    elif page == "Patient Explainer":
        patient_explainer_page()
    else:
        quality_reports_page()


if __name__ == "__main__":
    main()
