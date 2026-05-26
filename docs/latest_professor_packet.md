# Professor Packet (Sample 1)

This packet summarizes the latest reproducible pipeline outputs for outreach and review.
All metrics and explanations are based on synthetic CMS DE-SynPUF-style data workflows.

## Snapshot

- Overall quality status: **FAIL**
- Failed checks: **1**
- Modeling rows: **227292**
- Train rows: **114538**
- Test rows: **112754**
- Best model by AUPRC selection rule: **random_forest**
- random_forest: F1@0.50=0.3023822922528606, Precision@10%=0.2916814473217453, Brier=0.16879622485820858
- logistic_regression: F1@0.50=0.2909408003100475, Precision@10%=0.273767293366442, Brier=0.21680261108331794
- Explanation examples generated: **5**
- Explanations are explicitly non-diagnostic and synthetic-data-only.

## Linked Reports

### Quality
- Available: `data/processed/quality_report.json`
- Available: `docs/latest_quality_report.md`

### Modeling
- Available: `data/processed/model_metrics.json`
- Available: `data/processed/model_evaluation.json`
- Available: `data/processed/model_comparison.json`
- Available: `docs/latest_model_report.md`
- Available: `docs/latest_model_comparison_report.md`

### LLM Explainer
- Available: `data/processed/llm_explanation_examples.json`
- Available: `docs/latest_llm_explanation_report.md`

## Responsible Use

- This project demonstrates claims data engineering and analytics pipeline design.
- DE-SynPUF is synthetic; outputs should not be interpreted as clinical evidence.
- LLM explanations are non-diagnostic and are not medical advice.
