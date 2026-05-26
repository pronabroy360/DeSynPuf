from __future__ import annotations

import math
from collections.abc import Mapping


UTILIZATION_COLUMNS = [
    "inpatient_claims_count",
    "outpatient_claims_count",
    "carrier_claims_count",
    "prescription_events_count",
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


def total_events(row: Mapping[str, object]) -> int:
    return sum(_safe_int(row.get(column)) for column in UTILIZATION_COLUMNS)


def has_repeated_hospital_use(row: Mapping[str, object], threshold: int = 2) -> bool:
    return _safe_int(row.get("inpatient_claims_count")) >= threshold
