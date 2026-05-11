from __future__ import annotations

import math
from typing import Any, Mapping

from v2_discovery.replay.schemas import G3ReplayError


ALLOWED_COMPARISON_FIELDS = (
    "positions",
    "cash",
    "turnover",
    "transaction_cost",
    "gross_exposure",
    "net_exposure",
    "row_count",
    "date_range",
    "manifest_uri",
    "source_quality",
    "candidate_id",
)

def compare_allowed_mechanical_fields(
    v1_fields: Mapping[str, Any],
    v2_fields: Mapping[str, Any],
) -> dict[str, Any]:
    missing_v1 = [field for field in ALLOWED_COMPARISON_FIELDS if field not in v1_fields]
    missing_v2 = [field for field in ALLOWED_COMPARISON_FIELDS if field not in v2_fields]
    if missing_v1 or missing_v2:
        raise G3ReplayError(
            "G3 comparison missing allowed field(s): "
            f"v1={','.join(missing_v1) or 'none'}; "
            f"v2={','.join(missing_v2) or 'none'}"
        )

    field_results: dict[str, str] = {}
    mismatch_fields: list[str] = []
    for field in ALLOWED_COMPARISON_FIELDS:
        matched = _values_match(v1_fields[field], v2_fields[field])
        field_results[field] = "match" if matched else "mismatch"
        if not matched:
            mismatch_fields.append(field)

    return {
        "comparison_fields": list(ALLOWED_COMPARISON_FIELDS),
        "comparison_result": "match" if not mismatch_fields else "mismatch",
        "mismatch_count": len(mismatch_fields),
        "mismatch_fields": mismatch_fields,
        "field_results": field_results,
    }


def _values_match(left: Any, right: Any) -> bool:
    if isinstance(left, float) or isinstance(right, float):
        return _float_equal(left, right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left) != set(right):
            return False
        return all(_values_match(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return False
        return all(_values_match(left_item, right_item) for left_item, right_item in zip(left, right))
    return left == right


def _float_equal(left: Any, right: Any) -> bool:
    try:
        left_float = float(left)
        right_float = float(right)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(left_float) or not math.isfinite(right_float):
        return False
    return abs(left_float - right_float) <= 0.000001
