# Latest Warehouse Quality Report

Overall status: **PASS**

This report is generated from the local DuckDB warehouse. It contains aggregate validation results only.

## Table Summary

| Table | Rows |
| --- | ---: |
| `bronze_beneficiary_2008` | 3 |
| `bronze_beneficiary_2009` | 3 |
| `bronze_beneficiary_2010` | 3 |
| `bronze_carrier_claims_a` | 2 |
| `bronze_carrier_claims_b` | 1 |
| `bronze_inpatient_claims` | 2 |
| `bronze_outpatient_claims` | 2 |
| `bronze_prescription_drug_events` | 3 |
| `gold_high_cost_prediction_dataset` | 6 |
| `gold_patient_chronic_condition_summary` | 33 |
| `gold_patient_cost_summary` | 3 |
| `gold_patient_utilization_summary` | 3 |
| `gold_patient_year_summary` | 9 |
| `silver_beneficiaries` | 9 |
| `silver_carrier_claims` | 3 |
| `silver_diagnosis_codes` | 7 |
| `silver_inpatient_claims` | 2 |
| `silver_outpatient_claims` | 2 |
| `silver_prescription_events` | 3 |
| `silver_procedure_codes` | 7 |

## Checks

| Check | Status | Observed | Expectation |
| --- | --- | ---: | --- |
| `table_exists:silver_beneficiaries` | PASS | 9 | table exists and is queryable |
| `table_exists:silver_inpatient_claims` | PASS | 2 | table exists and is queryable |
| `table_exists:silver_outpatient_claims` | PASS | 2 | table exists and is queryable |
| `table_exists:silver_carrier_claims` | PASS | 3 | table exists and is queryable |
| `table_exists:silver_prescription_events` | PASS | 3 | table exists and is queryable |
| `table_exists:silver_diagnosis_codes` | PASS | 7 | table exists and is queryable |
| `table_exists:silver_procedure_codes` | PASS | 7 | table exists and is queryable |
| `table_exists:gold_patient_year_summary` | PASS | 9 | table exists and is queryable |
| `table_exists:gold_patient_utilization_summary` | PASS | 3 | table exists and is queryable |
| `table_exists:gold_patient_cost_summary` | PASS | 3 | table exists and is queryable |
| `table_exists:gold_patient_chronic_condition_summary` | PASS | 33 | table exists and is queryable |
| `table_exists:gold_high_cost_prediction_dataset` | PASS | 6 | table exists and is queryable |
| `gold_column:beneficiary_id` | PASS | present | required Gold patient-year column is present |
| `gold_column:year` | PASS | present | required Gold patient-year column is present |
| `gold_column:age` | PASS | present | required Gold patient-year column is present |
| `gold_column:chronic_condition_count` | PASS | present | required Gold patient-year column is present |
| `gold_column:inpatient_claims_count` | PASS | present | required Gold patient-year column is present |
| `gold_column:outpatient_claims_count` | PASS | present | required Gold patient-year column is present |
| `gold_column:carrier_claims_count` | PASS | present | required Gold patient-year column is present |
| `gold_column:prescription_events_count` | PASS | present | required Gold patient-year column is present |
| `gold_column:total_synthetic_cost` | PASS | present | required Gold patient-year column is present |
| `gold_column:unique_diagnosis_codes` | PASS | present | required Gold patient-year column is present |
| `gold_column:unique_procedure_codes` | PASS | present | required Gold patient-year column is present |
| `patient_year_unique_grain` | PASS | 0 | 0 duplicate beneficiary_id/year grains |
| `patient_year_non_null_keys` | PASS | 0 | 0 rows with null beneficiary_id or year |
| `patient_year_valid_years` | PASS | 0 | 0 rows outside 2008-2010 |
| `patient_year_nonnegative_costs` | PASS | 0 | 0 rows with negative cost values |
| `patient_year_nonnegative_counts` | PASS | 0 | 0 rows with negative utilization counts |
| `model_dataset_has_rows` | PASS | 6 | at least 1 modeling row |
| `model_dataset_non_null_labels` | PASS | 0 | 0 null high-cost labels |
| `model_dataset_next_year_pairs` | PASS | 0 | target_year equals input_year + 1 |
| `model_dataset_positive_labels` | PASS | 4 | at least 1 high-cost positive label |
