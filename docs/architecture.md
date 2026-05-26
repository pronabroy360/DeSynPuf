# Architecture

The project follows a Bronze -> Silver -> Gold data modeling pattern.

## Bronze

Bronze tables are direct DuckDB imports of CMS CSV files with standardized lower-case snake-case column names. Values are loaded as text to preserve raw fidelity and avoid premature type assumptions.

Expected Sample 1 Bronze tables:

- `bronze_beneficiary_2008`
- `bronze_beneficiary_2009`
- `bronze_beneficiary_2010`
- `bronze_inpatient_claims`
- `bronze_outpatient_claims`
- `bronze_carrier_claims_a`
- `bronze_carrier_claims_b`
- `bronze_prescription_drug_events`

## Silver

Silver tables normalize identifiers, parse dates, cast numeric amounts, standardize chronic-condition flags, and create long diagnosis/procedure-code tables.

## Gold

Gold tables are analytics-ready outputs:

- `gold_patient_year_summary`
- `gold_patient_utilization_summary`
- `gold_patient_cost_summary`
- `gold_patient_chronic_condition_summary`
- `gold_high_cost_prediction_dataset`

## Execution Flow

```text
data/raw/*.zip or *.csv
        |
        v
src.ingest.load_raw_files
        |
        v
Bronze DuckDB tables
        |
        v
src.transform.build_claims_mart
        |
        v
Silver cleaned tables
        |
        v
Gold patient-year marts
        |
        v
dashboard / API / ML / LLM explainer
```

## Design Choices

- **DuckDB** keeps the first version lightweight, reproducible, and easy to run locally.
- **All raw data stays out of git** using `.gitignore`.
- **Dynamic column handling** makes the transforms tolerant of missing optional CMS fields.
- **Safe explanation layer** avoids clinical claims and explicitly states that the data is synthetic.
