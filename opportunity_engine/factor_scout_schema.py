from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Any, Mapping


class FactorScoutStatus(StrEnum):
    INTAKE_ONLY = "intake_only"


SCOUT_MODEL_ID = "LOCAL_FACTOR_EQUAL_WEIGHT_V0"
SCOUT_MODEL_NAME = "4-Factor Equal-Weight Scout Baseline"
SCOUT_DISCOVERY_ORIGIN = "LOCAL_FACTOR_SCOUT"
EXPECTED_BASELINE_SCOPE = "PH65_G8_1B_SCOUT_BASELINE_ONLY"
EXPECTED_OUTPUT_SCOPE = "PH65_G8_1B_SCOUT_OUTPUT_TINY"
EXPECTED_AUTHORITY = "local_factor_scout_intake_only"
EXPECTED_SOURCE_ARTIFACT = "data/processed/phase34_factor_scores.parquet"
EXPECTED_BASELINE_ARTIFACT_URI = "data/discovery/local_factor_scout_baseline_v0.json"
EXPECTED_OUTPUT_ARTIFACT_URI = "data/discovery/local_factor_scout_output_tiny_v0.json"
EXPECTED_BASELINE_MANIFEST_URI = "data/discovery/local_factor_scout_baseline_v0.manifest.json"
EXPECTED_OUTPUT_MANIFEST_URI = "data/discovery/local_factor_scout_output_tiny_v0.manifest.json"

REQUIRED_FACTOR_NAMES = (
    "momentum_normalized",
    "quality_normalized",
    "volatility_normalized",
    "illiquidity_normalized",
)

REQUIRED_BASELINE_FIELDS = frozenset(
    {
        "scout_model_id",
        "scout_model_name",
        "scout_model_version",
        "source_artifact",
        "source_artifact_row_count",
        "source_artifact_date_range",
        "source_artifact_universe_count",
        "factor_names",
        "factor_weights",
        "output_manifest",
        "asof_date",
        "universe",
        "not_alpha_evidence",
        "no_rank",
        "no_score_display",
        "no_buy_sell_signal",
    }
)

REQUIRED_OUTPUT_FIELDS = frozenset(
    {
        "scout_output_id",
        "created_at",
        "scope",
        "authority",
        "scout_model_id",
        "scout_model_version",
        "scout_model_manifest",
        "output_manifest",
        "asof_date",
        "items",
        "forbidden_outputs",
    }
)

REQUIRED_OUTPUT_ITEM_FIELDS = frozenset(
    {
        "ticker",
        "company_name",
        "discovery_origin",
        "scout_model_id",
        "asof_date",
        "reason_bucket",
        "factor_exposures_available",
        "evidence_needed",
        "thesis_breakers_to_check",
        "provider_gaps",
        "status",
        "not_alpha_evidence",
        "is_user_seeded",
        "is_system_scouted",
        "is_validated",
        "is_actionable",
    }
)

REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "manifest_id",
        "artifact_uri",
        "artifact_sha256",
        "created_at",
        "scope",
        "scout_model_id",
        "scout_model_version",
        "row_count",
        "allowed_use",
        "forbidden_use",
        "source_policy",
    }
)

REQUIRED_OUTPUT_FORBIDDEN_FLAGS = {
    "no_score_display": True,
    "no_rank": True,
    "no_buy_sell_signal": True,
    "no_candidate_card": True,
    "no_dashboard_change": True,
}

ALLOWED_NEGATED_KEYS = frozenset(
    {
        "not_alpha_evidence",
        "no_alpha_evidence",
        "no_score",
        "no_score_display",
        "no_rank",
        "no_buy_sell_signal",
        "no_candidate_ranking",
        "no_candidate_card",
        "no_dashboard_change",
        "no_validated_thesis",
        "no_buying_range",
    }
)

ALLOWED_FALSE_STATE_KEYS = frozenset({"is_validated", "is_actionable"})

FORBIDDEN_SCORE_RANK_KEYS = frozenset(
    {
        "score",
        "scores",
        "factor_score",
        "factor_scores",
        "alpha",
        "alpha_score",
        "signal_score",
        "candidate_score",
        "expected_return",
        "expected_returns",
        "rank",
        "ranking",
        "candidate_rank",
        "rank_position",
        "top_pick",
        "best",
        "best_candidate",
        "validated",
        "actionable",
    }
)

FORBIDDEN_ACTION_KEYS = frozenset(
    {
        "buy",
        "sell",
        "hold",
        "buy_sell_signal",
        "buy_signal",
        "sell_signal",
        "hold_signal",
        "trade_signal",
        "recommendation",
        "rating",
        "buy_range",
        "buying_range",
        "entry_price",
        "alert",
        "alert_emitted",
        "broker_action",
        "broker_call",
        "order",
        "order_action",
        "buy_order",
        "sell_order",
    }
)

FORBIDDEN_PROMOTION_KEYS = frozenset(
    {
        "candidate_card",
        "candidate_card_authority",
        "candidate_card_created",
        "candidate_card_promotion",
        "candidate_card_status",
        "full_candidate_card",
        "new_candidate_card",
        "second_candidate_card",
        "promote_to_candidate_card",
    }
)

FORBIDDEN_OUTPUT_TEXT = (
    "alpha model",
    "alpha proof",
    "validated discovery model",
    "validated model",
    "ranking engine",
    "ranked candidate",
    "recommendation engine",
    "actionable candidate",
    "top pick",
    "best candidate",
    "candidate card created",
    "promote to candidate card",
)


@dataclass(frozen=True)
class FactorScoutValidationResult:
    valid: bool
    errors: tuple[str, ...]


class FactorScoutValidationError(ValueError):
    pass


def validate_factor_scout_baseline(
    baseline: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> FactorScoutValidationResult:
    errors: list[str] = []

    _validate_required_fields(baseline, REQUIRED_BASELINE_FIELDS, "baseline", errors)
    _validate_baseline_identity(baseline, errors)
    _validate_factor_contract(baseline, errors)
    _validate_source_artifact_metadata(baseline, errors)
    _validate_input_manifest_reference(baseline, errors)
    _validate_required_flags(
        baseline,
        {
            "not_alpha_evidence": True,
            "no_rank": True,
            "no_score_display": True,
            "no_buy_sell_signal": True,
        },
        "baseline",
        errors,
    )
    _validate_no_forbidden_fields(baseline, errors)
    _validate_no_forbidden_text(baseline, errors)
    _validate_no_yfinance_canonical(baseline, manifest, errors)
    _validate_manifest(
        manifest,
        expected_artifact_uri=EXPECTED_BASELINE_ARTIFACT_URI,
        expected_scope=EXPECTED_BASELINE_SCOPE,
        expected_row_count=1,
        context="baseline manifest",
        errors=errors,
    )

    return FactorScoutValidationResult(valid=not errors, errors=tuple(errors))


def validate_factor_scout_output(
    output: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
    baseline: Mapping[str, Any] | None = None,
) -> FactorScoutValidationResult:
    errors: list[str] = []

    _validate_required_fields(output, REQUIRED_OUTPUT_FIELDS, "scout output", errors)
    _validate_output_identity(output, baseline, errors)
    _validate_output_forbidden_flags(output, errors)
    _validate_output_items(output, errors)
    _validate_no_forbidden_fields(output, errors)
    _validate_no_forbidden_text(output, errors)
    _validate_no_yfinance_canonical(output, manifest, errors)
    _validate_manifest(
        manifest,
        expected_artifact_uri=EXPECTED_OUTPUT_ARTIFACT_URI,
        expected_scope=EXPECTED_OUTPUT_SCOPE,
        expected_row_count=1,
        context="output manifest",
        errors=errors,
    )

    return FactorScoutValidationResult(valid=not errors, errors=tuple(errors))


def assert_valid_factor_scout_baseline(
    baseline: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> None:
    result = validate_factor_scout_baseline(baseline, manifest=manifest)
    if not result.valid:
        raise FactorScoutValidationError("; ".join(result.errors))


def assert_valid_factor_scout_output(
    output: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
    baseline: Mapping[str, Any] | None = None,
) -> None:
    result = validate_factor_scout_output(output, manifest=manifest, baseline=baseline)
    if not result.valid:
        raise FactorScoutValidationError("; ".join(result.errors))


def _validate_required_fields(
    obj: Mapping[str, Any],
    required_fields: frozenset[str],
    context: str,
    errors: list[str],
) -> None:
    missing = sorted(required_fields.difference(obj))
    if missing:
        errors.append(f"{context} missing fields: {', '.join(missing)}")


def _validate_baseline_identity(baseline: Mapping[str, Any], errors: list[str]) -> None:
    if baseline.get("scout_model_id") != SCOUT_MODEL_ID:
        errors.append(f"scout_model_id must be {SCOUT_MODEL_ID}")
    if baseline.get("scout_model_name") != SCOUT_MODEL_NAME:
        errors.append(f"scout_model_name must be {SCOUT_MODEL_NAME}")
    if not _non_empty_string(baseline.get("scout_model_version")):
        errors.append("scout_model_version is required")
    if baseline.get("source_artifact") != EXPECTED_SOURCE_ARTIFACT:
        errors.append(f"source_artifact must be {EXPECTED_SOURCE_ARTIFACT}")
    if baseline.get("output_manifest") != EXPECTED_BASELINE_MANIFEST_URI:
        errors.append(f"output_manifest must be {EXPECTED_BASELINE_MANIFEST_URI}")
    if not _non_empty_string(baseline.get("asof_date")):
        errors.append("asof_date is required")
    universe = baseline.get("universe")
    if not isinstance(universe, Mapping) or not universe:
        errors.append("universe is required")


def _validate_output_identity(
    output: Mapping[str, Any],
    baseline: Mapping[str, Any] | None,
    errors: list[str],
) -> None:
    if output.get("scope") != EXPECTED_OUTPUT_SCOPE:
        errors.append(f"scope must be {EXPECTED_OUTPUT_SCOPE}")
    if output.get("authority") != EXPECTED_AUTHORITY:
        errors.append(f"authority must be {EXPECTED_AUTHORITY}")
    if output.get("scout_model_id") != SCOUT_MODEL_ID:
        errors.append(f"scout_model_id must be {SCOUT_MODEL_ID}")
    if not _non_empty_string(output.get("scout_model_version")):
        errors.append("scout_model_version is required")
    if output.get("scout_model_manifest") != EXPECTED_BASELINE_MANIFEST_URI:
        errors.append(f"scout_model_manifest must be {EXPECTED_BASELINE_MANIFEST_URI}")
    if output.get("output_manifest") != EXPECTED_OUTPUT_MANIFEST_URI:
        errors.append(f"output_manifest must be {EXPECTED_OUTPUT_MANIFEST_URI}")
    if not _non_empty_string(output.get("asof_date")):
        errors.append("asof_date is required")

    if baseline is None:
        return
    for field_name in ("scout_model_id", "scout_model_version", "asof_date"):
        if output.get(field_name) != baseline.get(field_name):
            errors.append(f"output {field_name} must match baseline {field_name}")


def _validate_factor_contract(baseline: Mapping[str, Any], errors: list[str]) -> None:
    factor_names = baseline.get("factor_names")
    if not isinstance(factor_names, list) or not factor_names:
        errors.append("factor_names must be a non-empty list")
    elif tuple(factor_names) != REQUIRED_FACTOR_NAMES:
        errors.append("factor_names must match the approved 4-factor baseline order")

    factor_weights = baseline.get("factor_weights")
    if not isinstance(factor_weights, Mapping) or not factor_weights:
        errors.append("factor_weights must be a non-empty object")
        return

    missing_weights = [name for name in REQUIRED_FACTOR_NAMES if name not in factor_weights]
    if missing_weights:
        errors.append(f"factor_weights missing factors: {', '.join(missing_weights)}")
        return

    total = 0.0
    for name in REQUIRED_FACTOR_NAMES:
        value = factor_weights.get(name)
        if not isinstance(value, (int, float)) or not isfinite(float(value)):
            errors.append(f"factor_weights.{name} must be finite")
            continue
        if float(value) < 0:
            errors.append(f"factor_weights.{name} must be non-negative")
        total += float(value)
    if abs(total - 1.0) > 1e-9:
        errors.append("factor_weights must sum to 1.0")


def _validate_source_artifact_metadata(baseline: Mapping[str, Any], errors: list[str]) -> None:
    row_count = baseline.get("source_artifact_row_count")
    if not isinstance(row_count, int) or row_count <= 0:
        errors.append("source_artifact_row_count must be a positive integer")

    universe_count = baseline.get("source_artifact_universe_count")
    if not isinstance(universe_count, int) or universe_count <= 0:
        errors.append("source_artifact_universe_count must be a positive integer")

    date_range = baseline.get("source_artifact_date_range")
    if not isinstance(date_range, Mapping):
        errors.append("source_artifact_date_range is required")
        return
    for field_name in ("start", "end"):
        if not _non_empty_string(date_range.get(field_name)):
            errors.append(f"source_artifact_date_range.{field_name} is required")


def _validate_input_manifest_reference(baseline: Mapping[str, Any], errors: list[str]) -> None:
    input_manifest = baseline.get("input_data_manifest")
    source_manifest = baseline.get("source_artifact_manifest")
    if not input_manifest and not source_manifest:
        errors.append("input_data_manifest or source_artifact_manifest is required")
        return

    if isinstance(input_manifest, Mapping):
        if input_manifest.get("artifact_uri") != EXPECTED_SOURCE_ARTIFACT:
            errors.append(f"input_data_manifest.artifact_uri must be {EXPECTED_SOURCE_ARTIFACT}")
        if not _non_empty_string(input_manifest.get("artifact_sha256")):
            errors.append("input_data_manifest.artifact_sha256 is required")
        if input_manifest.get("row_count") != baseline.get("source_artifact_row_count"):
            errors.append("input_data_manifest.row_count must match source_artifact_row_count")
    elif input_manifest is not None and not _non_empty_string(input_manifest):
        errors.append("input_data_manifest must be an object or non-empty reference")


def _validate_output_forbidden_flags(output: Mapping[str, Any], errors: list[str]) -> None:
    forbidden_outputs = output.get("forbidden_outputs")
    if not isinstance(forbidden_outputs, Mapping):
        errors.append("forbidden_outputs is required")
        return
    _validate_required_flags(forbidden_outputs, REQUIRED_OUTPUT_FORBIDDEN_FLAGS, "forbidden_outputs", errors)


def _validate_output_items(output: Mapping[str, Any], errors: list[str]) -> None:
    items = output.get("items")
    if not isinstance(items, list) or not items:
        errors.append("items must contain exactly one intake-only scout item")
        return
    if len(items) != 1:
        errors.append("items must contain exactly one intake-only scout item")

    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"items[{index}] must be an object")
            continue
        _validate_output_item(index, item, output, errors)


def _validate_output_item(
    index: int,
    item: Mapping[str, Any],
    output: Mapping[str, Any],
    errors: list[str],
) -> None:
    _validate_required_fields(item, REQUIRED_OUTPUT_ITEM_FIELDS, f"items[{index}]", errors)

    for field_name in ("ticker", "company_name", "reason_bucket"):
        if not _non_empty_string(item.get(field_name)):
            errors.append(f"items[{index}].{field_name} is required")

    if item.get("discovery_origin") != SCOUT_DISCOVERY_ORIGIN:
        errors.append(f"items[{index}].discovery_origin must be {SCOUT_DISCOVERY_ORIGIN}")
    if item.get("scout_model_id") != output.get("scout_model_id"):
        errors.append(f"items[{index}].scout_model_id must match output scout_model_id")
    if item.get("asof_date") != output.get("asof_date"):
        errors.append(f"items[{index}].asof_date must match output asof_date")
    if item.get("status") != FactorScoutStatus.INTAKE_ONLY.value:
        errors.append(f"items[{index}].status must be intake_only")
    if item.get("factor_exposures_available") is not True:
        errors.append(f"items[{index}].factor_exposures_available must be true")
    if item.get("not_alpha_evidence") is not True:
        errors.append(f"items[{index}].not_alpha_evidence must be true")
    if item.get("is_user_seeded") is not False:
        errors.append(f"items[{index}].is_user_seeded must be false")
    if item.get("is_system_scouted") is not True:
        errors.append(f"items[{index}].is_system_scouted must be true")
    if item.get("is_validated") is not False:
        errors.append(f"items[{index}].is_validated must be false")
    if item.get("is_actionable") is not False:
        errors.append(f"items[{index}].is_actionable must be false")

    for field_name in ("evidence_needed", "thesis_breakers_to_check", "provider_gaps"):
        value = item.get(field_name)
        if not isinstance(value, list) or not value:
            errors.append(f"items[{index}].{field_name} is required")


def _validate_required_flags(
    obj: Mapping[str, Any],
    required_flags: Mapping[str, bool],
    context: str,
    errors: list[str],
) -> None:
    for field_name, expected_value in required_flags.items():
        if obj.get(field_name) is not expected_value:
            errors.append(f"{context}.{field_name} must be {str(expected_value).lower()}")


def _validate_manifest(
    manifest: Mapping[str, Any] | None,
    *,
    expected_artifact_uri: str,
    expected_scope: str,
    expected_row_count: int,
    context: str,
    errors: list[str],
) -> None:
    if manifest is None:
        errors.append(f"{context} is required")
        return

    _validate_required_fields(manifest, REQUIRED_MANIFEST_FIELDS, context, errors)
    if manifest.get("artifact_uri") != expected_artifact_uri:
        errors.append(f"{context}.artifact_uri must be {expected_artifact_uri}")
    if not _non_empty_string(manifest.get("artifact_sha256")):
        errors.append(f"{context}.artifact_sha256 is required")
    if manifest.get("scope") != expected_scope:
        errors.append(f"{context}.scope must be {expected_scope}")
    if manifest.get("scout_model_id") != SCOUT_MODEL_ID:
        errors.append(f"{context}.scout_model_id must be {SCOUT_MODEL_ID}")
    if not _non_empty_string(manifest.get("scout_model_version")):
        errors.append(f"{context}.scout_model_version is required")
    if manifest.get("row_count") != expected_row_count:
        errors.append(f"{context}.row_count must be {expected_row_count}")
    for list_field in ("allowed_use", "forbidden_use"):
        value = manifest.get(list_field)
        if not isinstance(value, list) or not value:
            errors.append(f"{context}.{list_field} must be a non-empty list")
    source_policy = manifest.get("source_policy")
    if not isinstance(source_policy, Mapping):
        errors.append(f"{context}.source_policy is required")
    elif source_policy.get("yfinance_canonical") is True:
        errors.append("yfinance cannot be canonical in factor scout")


def _validate_no_forbidden_fields(obj: Any, errors: list[str]) -> None:
    forbidden_keys = FORBIDDEN_SCORE_RANK_KEYS.union(FORBIDDEN_ACTION_KEYS).union(FORBIDDEN_PROMOTION_KEYS)
    for path, key, value in _walk_mapping_keys(obj):
        normalized = _normalize_key(key)
        if normalized in ALLOWED_NEGATED_KEYS:
            continue
        if normalized in ALLOWED_FALSE_STATE_KEYS and value is False:
            continue
        if normalized in forbidden_keys or _is_forbidden_candidate_card_key(normalized):
            errors.append(f"forbidden field present at {'.'.join((*path, key))}")
        if isinstance(value, str) and _contains_forbidden_action_call(value):
            errors.append(f"forbidden action call present at {'.'.join((*path, key))}")


def _validate_no_forbidden_text(obj: Any, errors: list[str]) -> None:
    for path, key, value in _walk_mapping_keys(obj):
        if isinstance(value, str):
            normalized = _normalize_text(value)
            if any(pattern in normalized for pattern in FORBIDDEN_OUTPUT_TEXT):
                errors.append(f"forbidden scout wording present at {'.'.join((*path, key))}")


def _validate_no_yfinance_canonical(
    obj: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    errors: list[str],
) -> None:
    for candidate in (obj, manifest):
        if candidate is None:
            continue
        if "yfinance" in _stringify(_canonical_source_entries(candidate)).lower():
            errors.append("yfinance cannot be canonical in factor scout")
        for path, key, value in _walk_mapping_keys(candidate):
            if _normalize_key(key) == "yfinance_canonical" and value is True:
                errors.append(f"yfinance cannot be canonical in factor scout at {'.'.join((*path, key))}")


def _canonical_source_entries(obj: Any) -> list[Any]:
    entries: list[Any] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            normalized = _normalize_key(str(key))
            if normalized in {"canonical_source", "canonical_sources"}:
                if isinstance(value, list):
                    entries.extend(value)
                else:
                    entries.append(value)
            else:
                entries.extend(_canonical_source_entries(value))
    elif isinstance(obj, list):
        for item in obj:
            entries.extend(_canonical_source_entries(item))
    return entries


def _walk_mapping_keys(obj: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str, Any]]:
    entries: list[tuple[tuple[str, ...], str, Any]] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_text = str(key)
            entries.append((path, key_text, value))
            entries.extend(_walk_mapping_keys(value, (*path, key_text)))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (Mapping, list)):
                entries.extend(_walk_mapping_keys(value, (*path, str(index))))
            else:
                entries.append((path, str(index), value))
    return entries


def _contains_forbidden_action_call(value: str) -> bool:
    normalized = _normalize_text(value)
    if normalized in {"buy", "sell", "hold", "buy/sell", "buy_sell", "buy sell"}:
        return True
    return any(
        token in normalized
        for token in (
            "buy signal",
            "sell signal",
            "hold signal",
            "buy rating",
            "sell rating",
            "hold rating",
            "buy call",
            "sell call",
            "hold call",
        )
    )


def _is_forbidden_candidate_card_key(normalized_key: str) -> bool:
    return normalized_key.startswith("candidate_card") and normalized_key not in ALLOWED_NEGATED_KEYS


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _stringify(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_stringify(inner)}" for key, inner in value.items())
    if isinstance(value, list):
        return " ".join(_stringify(item) for item in value)
    return str(value)
