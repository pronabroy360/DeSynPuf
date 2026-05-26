# Bronze Layer

Bronze tables are created by:

```bash
python -m src.ingest.load_raw_files --raw-dir data/raw --db data/processed/desynpuf.duckdb
```

The loader reads CMS CSV files directly, extracts CSV/TXT members from ZIP files into `data/interim/extracted`, standardizes column names to lower-case snake-case, and keeps raw values as strings.

Expected tables:

- `bronze_beneficiary_2008`
- `bronze_beneficiary_2009`
- `bronze_beneficiary_2010`
- `bronze_inpatient_claims`
- `bronze_outpatient_claims`
- `bronze_carrier_claims_a`
- `bronze_carrier_claims_b`
- `bronze_prescription_drug_events`
