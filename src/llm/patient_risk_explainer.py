from __future__ import annotations

import math
from collections.abc import Mapping

from src.features.comorbidity_features import active_chronic_conditions
from src.llm.claims_summary_prompt import build_claims_explanation_prompt


def _money(value: object) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "an unavailable cost amount"


def _safe_int(value: object) -> int:
    try:
        if value is None:
            return 0
        if isinstance(value, float) and math.isnan(value):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def rule_based_claims_explanation(features: Mapping[str, object]) -> str:
    beneficiary_id = features.get("beneficiary_id", "selected synthetic beneficiary")
    year = features.get("year", "the selected year")
    total_cost = _money(features.get("total_synthetic_cost"))
    risk_percentile = features.get("risk_percentile")

    drivers: list[str] = []
    if _safe_int(features.get("inpatient_claims_count")) >= 2:
        drivers.append("repeated inpatient utilization")
    elif _safe_int(features.get("inpatient_claims_count")) == 1:
        drivers.append("at least one inpatient claim")
    if _safe_int(features.get("carrier_claims_count")) >= 20:
        drivers.append("frequent professional/carrier claims")
    if _safe_int(features.get("outpatient_claims_count")) >= 10:
        drivers.append("frequent outpatient facility claims")
    if _safe_int(features.get("prescription_events_count")) >= 10:
        drivers.append("multiple prescription drug events")
    if _safe_int(features.get("chronic_condition_count")) >= 2:
        drivers.append("multiple chronic-condition indicators")
    if not drivers:
        drivers.append("the combined synthetic cost and utilization profile")

    conditions = active_chronic_conditions(features)
    condition_text = ", ".join(condition.replace("_", " ") for condition in conditions) if conditions else "none flagged"
    percentile_text = f" The risk percentile is approximately {risk_percentile}." if risk_percentile is not None else ""

    return (
        f"For {beneficiary_id} in {year}, total synthetic cost is {total_cost}.{percentile_text} "
        f"The main cost/utilization drivers are {', '.join(drivers)}. "
        f"Flagged chronic-condition indicators include: {condition_text}. "
        "This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice."
    )


def build_llm_prompt(features: Mapping[str, object]) -> str:
    return build_claims_explanation_prompt(features)


def explain_patient_year(features: Mapping[str, object], use_prompt_only: bool = False) -> str:
    if use_prompt_only:
        return build_llm_prompt(features)
    return rule_based_claims_explanation(features)
