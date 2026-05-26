# Latest High-Cost Prediction Model Report

This report summarizes aggregate model-training outputs from synthetic CMS DE-SynPUF data.
It is not a clinical validation report and should not be interpreted as real-world model performance.

Best model: **random_forest**

## Dataset

| Metric | Value |
| --- | ---: |
| `rows` | 227292 |
| `train_rows` | 114538 |
| `test_rows` | 112754 |
| `input_years` | [2008, 2009] |
| `target_positive_rate` | 0.10010911074740862 |

## Metrics

| Model | AUROC | AUPRC | F1 | Precision | Precision@10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| `logistic_regression` | 0.7432 | 0.2515 | 0.2909 | 0.1862 | 0.2738 |
| `random_forest` | 0.7485 | 0.2657 | 0.3024 | 0.2057 | 0.2917 |

## Top Feature Importance

| Rank | Feature | Importance |
| ---: | --- | ---: |
| 1 | `numeric__unique_diagnosis_codes` | 0.131874 |
| 2 | `numeric__carrier_claims_count` | 0.123915 |
| 3 | `numeric__chronic_condition_count` | 0.101593 |
| 4 | `numeric__total_synthetic_cost` | 0.072808 |
| 5 | `numeric__unique_procedure_codes` | 0.072254 |
| 6 | `numeric__outpatient_total_paid` | 0.067585 |
| 7 | `numeric__outpatient_claims_count` | 0.059451 |
| 8 | `numeric__prescription_total_cost` | 0.048699 |
| 9 | `numeric__prescription_events_count` | 0.047232 |
| 10 | `numeric__age` | 0.030862 |
| 11 | `numeric__inpatient_total_paid` | 0.017889 |
| 12 | `numeric__inpatient_claims_count` | 0.016493 |
| 13 | `categorical__esrd_indicator_Y` | 0.013096 |
| 14 | `numeric__any_inpatient` | 0.012310 |
| 15 | `categorical__esrd_indicator_0` | 0.011919 |
| 16 | `numeric__repeated_inpatient` | 0.006238 |
| 17 | `categorical__sex_code_2` | 0.004168 |
| 18 | `categorical__sex_code_1` | 0.004165 |
| 19 | `categorical__race_code_1` | 0.003495 |
| 20 | `categorical__state_code_05` | 0.003209 |
