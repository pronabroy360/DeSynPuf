# Professor Packet (Demo)

This packet summarizes the latest reproducible pipeline outputs for outreach and review.
All metrics and explanations are based on synthetic CMS DE-SynPUF-style data workflows.

## Snapshot

- Overall quality status: **PASS**
- Failed checks: **0**
- Modeling rows: **6**
- Train rows: **3**
- Test rows: **3**
- Best model by AUPRC selection rule: **logistic_regression**
- logistic_regression: F1@0.50=0.5, Precision@10%=1.0, Brier=0.4921175143128145
- random_forest: F1@0.50=0.0, Precision@10%=1.0, Brier=0.381924
- Explanation examples generated: **5**
- Explanations are explicitly non-diagnostic and synthetic-data-only.

## Linked Reports

### Quality
- Available: `data/processed/demo_quality_report.json`
- Available: `docs/demo_quality_report.md`

### Modeling
- Available: `data/processed/demo_model_metrics.json`
- Available: `data/processed/demo_model_evaluation.json`
- Available: `data/processed/demo_model_comparison.json`
- Available: `docs/demo_model_report.md`
- Available: `docs/demo_model_comparison_report.md`

### LLM Explainer
- Available: `data/processed/demo_llm_explanation_examples.json`
- Available: `docs/demo_llm_explanation_report.md`

## Responsible Use

- This project demonstrates claims data engineering and analytics pipeline design.
- DE-SynPUF is synthetic; outputs should not be interpreted as clinical evidence.
- LLM explanations are non-diagnostic and are not medical advice.
