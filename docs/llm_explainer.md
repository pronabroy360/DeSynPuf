# LLM Claims Explainer

The project includes a safe explanation layer for synthetic beneficiary-year claims profiles.

## Purpose

The explainer converts structured DE-SynPUF-style features into plain-English summaries of synthetic cost, utilization, chronic-condition indicators, and model risk drivers.

It is designed for portfolio demonstration only. It must not be framed as clinical advice, diagnosis, treatment guidance, or real-world patient inference.

## Demo Workflow

```bash
make demo-smoke
make demo-explain
```

Demo outputs:

```text
data/processed/demo_llm_explanation_examples.json
docs/demo_llm_explanation_report.md
```

## Real Sample 1 Workflow

After building the real CMS Sample 1 Gold tables:

```bash
make explain
```

Default outputs:

```text
data/processed/llm_explanation_examples.json
docs/latest_llm_explanation_report.md
```

## Guardrails

- Use only structured synthetic or aggregate fields.
- Avoid raw notes, free-text clinical records, or identifiers from real patients.
- Do not diagnose, recommend treatment, or infer clinical truth.
- Always state that outputs are based on synthetic CMS DE-SynPUF data.
- Always state that outputs are not clinical advice.

## Implementation

The current default implementation is deterministic and rule-based. It also exposes an LLM prompt template in `src/llm/claims_summary_prompt.py` for future integration with a local model or API.
