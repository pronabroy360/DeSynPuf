# Data Dictionary

This dictionary focuses on the standardized Silver and Gold tables produced by the pipeline. Raw CMS columns are preserved in Bronze tables after lower-case snake-case standardization.

## Silver Tables

### `silver_beneficiaries`

One row per synthetic beneficiary-year where beneficiary summary data exists.

| Column | Meaning |
| --- | --- |
| `beneficiary_id` | Synthetic CMS beneficiary identifier from `DESYNPUF_ID`. |
| `year` | Beneficiary summary year: 2008, 2009, or 2010. |
| `birth_date` | Beneficiary birth date parsed from CMS date format. |
| `death_date` | Beneficiary death date, if present. |
| `age` | Approximate age at year end. |
| `sex_code` | CMS sex identifier code. |
| `race_code` | CMS race identifier code. |
| `state_code` | CMS state code. |
| `county_code` | CMS county code. |
| `esrd_indicator` | ESRD indicator from beneficiary summary data. |
| `alzheimers`, `heart_failure`, `kidney_disease`, `cancer`, `copd`, `depression`, `diabetes`, `ischemic_heart`, `osteoporosis`, `rheumatoid_arthritis`, `stroke_tia` | Chronic-condition flags normalized to 0/1. |
| `medicare_ip_reimbursement`, `medicare_op_reimbursement`, `medicare_carrier_reimbursement` | Annual summary reimbursement values from beneficiary files, when present. |

### `silver_inpatient_claims`

One row per inpatient claim.

Key fields include `beneficiary_id`, `claim_id`, `claim_start_date`, `claim_end_date`, `claim_year`, `payment_amount`, `primary_payer_amount`, `provider_number`, `admission_date`, `discharge_date`, `utilization_days`, diagnosis codes, and procedure codes.

### `silver_outpatient_claims`

One row per outpatient claim.

Key fields include `beneficiary_id`, `claim_id`, dates, `claim_year`, `payment_amount`, provider fields, diagnosis codes, ICD procedure codes, and HCPCS codes.

### `silver_carrier_claims`

One row per carrier/professional claim.

Key fields include `beneficiary_id`, `claim_id`, dates, `claim_year`, `payment_amount`, source carrier split (`a` or `b`), line diagnosis codes, and line HCPCS codes.

### `silver_prescription_events`

One row per Part D prescription drug event.

Key fields include `beneficiary_id`, `event_id`, `service_date`, `service_year`, `product_service_id`, `quantity_dispensed`, `days_supply`, `patient_pay_amount`, and `total_rx_cost`.

### `silver_diagnosis_codes`

Long-format diagnosis-code table extracted from claim tables.

### `silver_procedure_codes`

Long-format ICD procedure and HCPCS-code table extracted from claim tables.

## Gold Tables

### `gold_patient_year_summary`

One row per synthetic beneficiary-year. This is the main analytics and ML feature table.

Important fields:

- Demographics: age, sex, race, state, county.
- Chronic-condition flags and `chronic_condition_count`.
- Utilization: claim/event counts by inpatient, outpatient, carrier, and prescription.
- Cost: paid amounts and total synthetic cost by year.
- Code breadth: unique diagnosis and procedure-code counts.
- Risk-oriented flags: `any_inpatient`, `repeated_inpatient`.

### `gold_high_cost_prediction_dataset`

Modeling table where each row uses one input year to predict next-year high-cost status.

Current implementation labels a beneficiary as high-cost when next-year `total_synthetic_cost` is at or above that year's 90th percentile.
