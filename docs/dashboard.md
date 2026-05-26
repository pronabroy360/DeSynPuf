# Streamlit Dashboard

The project includes a local Streamlit frontend for exploring the DuckDB warehouse.

## Run With Demo Data

```bash
make demo-all
DESYNPUF_DB=data/processed/demo_desynpuf.duckdb make dashboard
```

## Run With CMS Sample 1 Data

```bash
make ingest
make transform
make validate
make train
make explain
make dashboard
```

## Pages

- **Overview**: beneficiary-year counts, total synthetic cost, utilization summary, and highest-cost synthetic beneficiary-years.
- **Cost Analytics**: cost distribution by year and claim type.
- **Utilization Analytics**: inpatient, outpatient, carrier, and prescription event frequencies.
- **Chronic Conditions**: average synthetic cost differences by chronic-condition flag.
- **Cohort Explorer**: filter beneficiary-years by year, cost threshold, and repeated inpatient use.
- **Risk Model**: high-cost modeling rows, saved metrics, feature importance, and model report.
- **Patient Explainer**: select a synthetic beneficiary-year and generate a safe non-diagnostic explanation.
- **Quality & Reports**: quality-check results, table row counts, model report, and LLM explanation report.

## Responsible Use

The dashboard displays synthetic CMS DE-SynPUF-derived outputs only. It is a portfolio and engineering demonstration, not clinical evidence or medical advice.
