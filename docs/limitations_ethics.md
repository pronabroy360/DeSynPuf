# Limitations And Ethics

## Synthetic Data Limitation

DE-SynPUF is synthetic. Analyses may resemble Medicare claims workflows, but outputs should not be interpreted as real-world clinical, epidemiological, or policy evidence.

## No Clinical Advice

The dashboard, API, notebooks, model outputs, and LLM explanations are for educational and portfolio purposes only. They should not be used for clinical decisions, care management, diagnosis, treatment, coverage determinations, or patient prioritization.

## Privacy

CMS designed DE-SynPUF to provide Medicare-style data while protecting beneficiary privacy. This repository still avoids committing raw files, generated databases, model artifacts, or row-level data extracts.

## Model Risk

The high-cost prediction model is a workflow demonstration. It can show how to structure claims-based ML, but it should not be treated as validated or generalizable.

## LLM Risk Controls

LLM explanations must:

- State that the beneficiary profile is synthetic.
- Avoid diagnosis, treatment, or clinical advice.
- Explain cost/utilization drivers in plain language.
- Avoid presenting model output as clinical truth.
