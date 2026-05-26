from __future__ import annotations

from collections.abc import Mapping


SYSTEM_GUARDRAILS = """You explain synthetic CMS DE-SynPUF claims features for educational analytics.
Do not diagnose, recommend treatment, infer real patient facts, or present synthetic outputs as clinical truth.
Always state that the data is synthetic and the explanation is not clinical advice."""


def build_claims_explanation_prompt(features: Mapping[str, object]) -> str:
    lines = [
        SYSTEM_GUARDRAILS,
        "",
        "Explain this synthetic beneficiary-year profile in plain English:",
    ]
    for key, value in features.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("Focus on cost, utilization, chronic-condition indicators, and model risk drivers.")
    return "\n".join(lines)
