# Warehouse Quality Checks

The validation command checks the DuckDB warehouse after Bronze/Silver/Gold transforms.

```bash
make validate
```

Or run it directly:

```bash
python3 -m src.quality.validate_warehouse --db data/processed/desynpuf.duckdb
```

## Checks

- Required Silver and Gold tables exist.
- `gold_patient_year_summary` contains required analytics columns.
- The patient-year mart has one row per `beneficiary_id` and `year`.
- Patient-year keys are non-null.
- Years are limited to 2008, 2009, and 2010.
- Negative cost adjustments are tracked as informational (expected in claims reversals/adjustments).
- Cost rows below an extreme threshold (default `< -5000`) fail validation.
- Utilization measures are nonnegative.
- The high-cost prediction dataset has rows.
- High-cost labels are non-null.
- Target years equal input years plus one.
- At least one high-cost positive label exists.

## Outputs

Default real-data outputs:

```text
data/processed/quality_report.json
docs/latest_quality_report.md
```

Demo-data outputs:

```text
data/processed/demo_quality_report.json
docs/demo_quality_report.md
```

These reports contain aggregate validation results only. They should not include raw row-level CMS data.
