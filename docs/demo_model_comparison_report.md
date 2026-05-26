# Latest Model Comparison Report

This report compares candidate high-cost prediction models on synthetic DE-SynPUF data.
Use these metrics as workflow diagnostics only, not clinical validation.

Selected best model: **logistic_regression**

| Model | AUROC | AUPRC | F1@0.50 | Precision@0.50 | Precision@10% | Brier | Best F1 Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `logistic_regression` | N/A | N/A | 0.5000 | 1.0000 | 1.0000 | 0.4921 | 0.0000 |
| `random_forest` | N/A | N/A | 0.0000 | 0.0000 | 1.0000 | 0.3819 | 0.0000 |
