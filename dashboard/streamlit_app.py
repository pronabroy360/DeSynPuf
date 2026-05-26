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
METRICS_PATH = Path("data/processed/model_metrics.json")


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


def metric_row(summary: pd.DataFrame) -> None:
    total_beneficiaries = int(summary["beneficiaries"].sum()) if not summary.empty else 0
    total_cost = float(summary["total_synthetic_cost"].sum()) if not summary.empty else 0
    avg_cost = float(summary["avg_synthetic_cost"].mean()) if not summary.empty else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Beneficiary-years", f"{total_beneficiaries:,}")
    col2.metric("Total synthetic cost", f"${total_cost:,.0f}")
    col3.metric("Avg annual cost", f"${avg_cost:,.0f}")


def overview_page() -> None:
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
        st.dataframe(utilization, use_container_width=True, hide_index=True)


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
    if METRICS_PATH.exists():
        st.subheader("Saved Model Metrics")
        st.json(json.loads(METRICS_PATH.read_text()))
    else:
        st.info("No trained model metrics yet. Run `make train` after building the Gold tables.")


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


def main() -> None:
    if not require_database():
        return
    page = st.sidebar.radio(
        "Dashboard Pages",
        ["Overview", "Cost Analytics", "Utilization Analytics", "Risk Model", "Patient Explainer"],
    )
    if page == "Overview":
        overview_page()
    elif page == "Cost Analytics":
        cost_analytics_page()
    elif page == "Utilization Analytics":
        utilization_page()
    elif page == "Risk Model":
        risk_model_page()
    else:
        patient_explainer_page()


if __name__ == "__main__":
    main()
