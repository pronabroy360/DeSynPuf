# Latest Warehouse Quality Report

Overall status: **FAIL**

This report is generated from the local DuckDB warehouse. It contains aggregate validation results only.

## Table Summary

| Table | Rows |
| --- | ---: |
| `bronze_beneficiary_2008` | 116,352 |
| `bronze_beneficiary_2009` | 114,538 |
| `bronze_beneficiary_2010` | 112,754 |
| `bronze_carrier_claims_a` | 2,370,667 |
| `bronze_carrier_claims_b` | 2,370,668 |
| `bronze_inpatient_claims` | 66,773 |
| `bronze_outpatient_claims` | 790,790 |
| `bronze_prescription_drug_events` | 5,552,421 |
| `gold_high_cost_prediction_dataset` | 227,292 |
| `gold_patient_chronic_condition_summary` | 33 |
| `gold_patient_cost_summary` | 3 |
| `gold_patient_utilization_summary` | 3 |
| `gold_patient_year_summary` | 343,644 |
| `silver_beneficiaries` | 343,644 |
| `silver_carrier_claims` | 4,741,335 |
| `silver_diagnosis_codes` | 11,728,369 |
| `silver_inpatient_claims` | 66,773 |
| `silver_outpatient_claims` | 790,790 |
| `silver_prescription_events` | 5,552,421 |
| `silver_procedure_codes` | 3,870,718 |

## Checks

| Check | Status | Observed | Expectation |
| --- | --- | ---: | --- |
| `table_exists:silver_beneficiaries` | PASS | 343644 | table exists and is queryable |
| `table_exists:silver_inpatient_claims` | PASS | 66773 | table exists and is queryable |
| `table_exists:silver_outpatient_claims` | PASS | 790790 | table exists and is queryable |
| `table_exists:silver_carrier_claims` | PASS | 4741335 | table exists and is queryable |
| `table_exists:silver_prescription_events` | PASS | 5552421 | table exists and is queryable |
| `table_exists:silver_diagnosis_codes` | PASS | 11728369 | table exists and is queryable |
| `table_exists:silver_procedure_codes` | PASS | 3870718 | table exists and is queryable |
| `table_exists:gold_patient_year_summary` | PASS | 343644 | table exists and is queryable |
| `table_exists:gold_patient_utilization_summary` | PASS | 3 | table exists and is queryable |
| `table_exists:gold_patient_cost_summary` | PASS | 3 | table exists and is queryable |
| `table_exists:gold_patient_chronic_condition_summary` | PASS | 33 | table exists and is queryable |
| `table_exists:gold_high_cost_prediction_dataset` | PASS | 227292 | table exists and is queryable |
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
| `patient_year_nonnegative_costs` | FAIL | 228 | 0 rows with negative cost values |
| `patient_year_nonnegative_counts` | PASS | 0 | 0 rows with negative utilization counts |
| `model_dataset_has_rows` | PASS | 227292 | at least 1 modeling row |
| `model_dataset_non_null_labels` | PASS | 0 | 0 null high-cost labels |
| `model_dataset_next_year_pairs` | PASS | 0 | target_year equals input_year + 1 |
| `model_dataset_positive_labels` | PASS | 22754 | at least 1 high-cost positive label |
