# High-Cost Prediction Modeling

The modeling task predicts whether a synthetic beneficiary will be in the top 10% of next-year total annual cost.

## Demo Training

After running the demo warehouse smoke test:

```bash
make demo-smoke
make demo-train
```

Demo outputs:

```text
data/processed/demo_high_cost_model.joblib
data/processed/demo_model_metrics.json
data/processed/demo_model_feature_importance.json
data/processed/demo_model_evaluation.json
docs/demo_model_report.md
```

The demo dataset is intentionally tiny. Use it only to verify that the workflow runs end-to-end.

## Real Sample 1 Training

After loading CMS DE1.0 Sample 1 and building Gold tables:

```bash
make train
```

Default outputs:

```text
data/processed/high_cost_model.joblib
data/processed/model_metrics.json
data/processed/model_feature_importance.json
data/processed/model_evaluation.json
docs/latest_model_report.md
```

## Evaluation Artifacts

`model_evaluation.json` contains aggregate, non-identifiable evaluation structures for the best model:

- precision-recall curve points
- ROC curve points
- calibration curve points
- confusion matrix at threshold 0.50
- Brier score and predicted positive rate

## Features

Current feature groups:

- Demographics: age, sex, race, state, county, ESRD indicator.
- Chronic-condition burden: chronic-condition count.
- Utilization: inpatient, outpatient, carrier, and prescription counts.
- Cost: paid amounts by claim type and total synthetic cost.
- Code breadth: unique diagnosis and procedure-code counts.

## Responsible Interpretation

Metrics from DE-SynPUF are workflow signals, not clinical validation. The dataset is synthetic and should not be used to claim real-world predictive performance.
