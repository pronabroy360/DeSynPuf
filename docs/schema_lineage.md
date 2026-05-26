# Schema And Lineage

This page summarizes the current warehouse lineage. The production build is implemented with DuckDB SQL generated from Python so the pipeline can tolerate CMS file variants.

```mermaid
flowchart TD
    raw[CMS DE-SynPUF CSV/ZIP files] --> ingest[src.ingest.load_raw_files]

    ingest --> b2008[bronze_beneficiary_2008]
    ingest --> b2009[bronze_beneficiary_2009]
    ingest --> b2010[bronze_beneficiary_2010]
    ingest --> bip[bronze_inpatient_claims]
    ingest --> bop[bronze_outpatient_claims]
    ingest --> bcarA[bronze_carrier_claims_a]
    ingest --> bcarB[bronze_carrier_claims_b]
    ingest --> bpde[bronze_prescription_drug_events]

    b2008 --> sben[silver_beneficiaries]
    b2009 --> sben
    b2010 --> sben
    bip --> sip[silver_inpatient_claims]
    bop --> sop[silver_outpatient_claims]
    bcarA --> scar[silver_carrier_claims]
    bcarB --> scar
    bpde --> spde[silver_prescription_events]

    sip --> sdx[silver_diagnosis_codes]
    sop --> sdx
    scar --> sdx
    sip --> sprc[silver_procedure_codes]
    sop --> sprc
    scar --> sprc

    sben --> gpy[gold_patient_year_summary]
    sip --> gpy
    sop --> gpy
    scar --> gpy
    spde --> gpy
    sdx --> gpy
    sprc --> gpy

    gpy --> gutil[gold_patient_utilization_summary]
    gpy --> gcost[gold_patient_cost_summary]
    gpy --> gchronic[gold_patient_chronic_condition_summary]
    gpy --> gmodel[gold_high_cost_prediction_dataset]

    gpy --> dashboard[Streamlit dashboard]
    gmodel --> model[High-cost model]
    gpy --> explainer[LLM explanation report]
```

## Primary Keys And Grains

| Table | Grain |
| --- | --- |
| `silver_beneficiaries` | `beneficiary_id`, `year` |
| `silver_inpatient_claims` | one inpatient claim |
| `silver_outpatient_claims` | one outpatient claim |
| `silver_carrier_claims` | one carrier/professional claim |
| `silver_prescription_events` | one prescription drug event |
| `silver_diagnosis_codes` | one diagnosis-code position per claim |
| `silver_procedure_codes` | one procedure/HCPCS-code position per claim |
| `gold_patient_year_summary` | `beneficiary_id`, `year` |
| `gold_high_cost_prediction_dataset` | `beneficiary_id`, `input_year`, `target_year` |

## Validation

The quality checker validates required tables, required Gold columns, non-null patient-year keys, unique patient-year grain, valid years, nonnegative measures, and next-year model-label consistency.
