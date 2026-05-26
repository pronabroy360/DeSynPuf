# Latest High-Cost Prediction Model Report

This report summarizes aggregate model-training outputs from synthetic CMS DE-SynPUF data.
It is not a clinical validation report and should not be interpreted as real-world model performance.

Best model: **logistic_regression**

## Dataset

| Metric | Value |
| --- | ---: |
| `rows` | 6 |
| `train_rows` | 3 |
| `test_rows` | 3 |
| `input_years` | [2008, 2009] |
| `target_positive_rate` | 0.6666666666666666 |

## Metrics

| Model | AUROC | AUPRC | F1 | Precision | Precision@10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| `logistic_regression` | N/A | N/A | 0.5000 | 1.0000 | 1.0000 |
| `random_forest` | N/A | N/A | 0.0000 | 0.0000 | 1.0000 |

## Top Feature Importance

| Rank | Feature | Importance |
| ---: | --- | ---: |
| 1 | `numeric__total_synthetic_cost` | 0.223818 |
| 2 | `numeric__prescription_total_cost` | 0.222515 |
| 3 | `numeric__inpatient_claims_count` | 0.222515 |
| 4 | `numeric__prescription_events_count` | 0.222515 |
| 5 | `numeric__inpatient_total_paid` | 0.222515 |
| 6 | `numeric__unique_procedure_codes` | 0.222515 |
| 7 | `numeric__any_inpatient` | 0.222515 |
| 8 | `numeric__chronic_condition_count` | 0.222182 |
| 9 | `numeric__age` | 0.201996 |
| 10 | `numeric__carrier_total_paid` | 0.197071 |
| 11 | `categorical__state_code_10` | 0.104886 |
| 12 | `categorical__county_code_001` | 0.104886 |
| 13 | `numeric__outpatient_claims_count` | 0.088972 |
| 14 | `numeric__carrier_claims_count` | 0.088972 |
| 15 | `numeric__outpatient_total_paid` | 0.088972 |
| 16 | `categorical__state_code_30` | 0.062961 |
| 17 | `categorical__county_code_005` | 0.062961 |
| 18 | `categorical__sex_code_2` | 0.041950 |
| 19 | `categorical__race_code_2` | 0.041950 |
| 20 | `categorical__state_code_20` | 0.041950 |
