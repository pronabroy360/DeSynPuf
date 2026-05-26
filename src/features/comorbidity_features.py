from __future__ import annotations

import math
from collections.abc import Mapping


CHRONIC_CONDITION_COLUMNS = [
    "alzheimers",
    "heart_failure",
    "kidney_disease",
    "cancer",
    "copd",
    "depression",
    "diabetes",
    "ischemic_heart",
    "osteoporosis",
    "rheumatoid_arthritis",
    "stroke_tia",
]


def _safe_int(value: object) -> int:
    try:
        if value is None:
            return 0
        if isinstance(value, float) and math.isnan(value):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def chronic_condition_count(row: Mapping[str, object]) -> int:
    return sum(1 for column in CHRONIC_CONDITION_COLUMNS if _safe_int(row.get(column)) == 1)


def active_chronic_conditions(row: Mapping[str, object]) -> list[str]:
    return [column for column in CHRONIC_CONDITION_COLUMNS if _safe_int(row.get(column)) == 1]
