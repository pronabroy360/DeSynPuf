# Latest Model Comparison Report

This report compares candidate high-cost prediction models on synthetic DE-SynPUF data.
Use these metrics as workflow diagnostics only, not clinical validation.

Selected best model: **random_forest**

| Model | AUROC | AUPRC | F1@0.50 | Precision@0.50 | Precision@10% | Brier | Best F1 Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `logistic_regression` | 0.7432 | 0.2515 | 0.2909 | 0.1862 | 0.2738 | 0.2168 | 0.6400 |
| `random_forest` | 0.7485 | 0.2657 | 0.3024 | 0.2057 | 0.2917 | 0.1688 | 0.6000 |
