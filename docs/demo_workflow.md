# Demo Workflow

This repository keeps real CMS files out of git, so the project includes a tiny CMS-like synthetic fixture for quick verification.

## Create Demo Raw Files

```bash
make demo-data
```

This writes small CSV files to:

```text
data/raw/demo_sample/
```

The files mimic the naming and column patterns expected by the ingestion script. They are intentionally tiny and are not intended for analysis.

## Run End-To-End Smoke Test

```bash
make demo-smoke
```

The smoke test:

- creates demo raw CSV files,
- loads Bronze DuckDB tables,
- builds Silver claim and beneficiary tables,
- builds Gold patient-year summaries,
- runs warehouse quality checks,
- validates expected row counts,
- verifies that at least one high-cost label exists.

The demo database is written to:

```text
data/processed/demo_desynpuf.duckdb
```

Aggregate quality reports are written to:

```text
data/processed/demo_quality_report.json
docs/demo_quality_report.md
```

## Launch Dashboard Against Demo Data

```bash
DESYNPUF_DB=data/processed/demo_desynpuf.duckdb make dashboard
```

Use this only as a UI and pipeline demonstration. For portfolio results, run the same pipeline against CMS DE1.0 Sample 1.

## Generate Demo Explanation Examples

```bash
make demo-explain
```

Outputs:

```text
data/processed/demo_llm_explanation_examples.json
docs/demo_llm_explanation_report.md
```

These examples are generated from structured synthetic beneficiary-year features only. They are non-diagnostic and include explicit responsible-use language.
