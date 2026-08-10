"""Frozen implementation-manifest contract for ``CYCLE_RESONANCE_v1``.

The manifest is deliberately configuration-strict.  Scientific choices have no
runtime defaults: callers must supply every preregistered field before a
confirmatory/prospective implementation can be frozen.  This module validates
and content-addresses that declaration; it does not fit a model or inspect
outcomes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import assert_sha256, domain_hash
from research.alpha_pit_v1.contracts import (
    CLAIM_TOPICS,
    EXPECTATION_MEASURES,
    FAMILY_ID,
    OBSERVATION_FIELDS,
    PRIMARY_LABEL_SPEC_ID,
    RISK_SET_SPEC_ID,
)
from research.cycle_resonance_v1.contracts import IMPLEMENTATION_MANIFEST_SCHEMA


MANIFEST_DOMAIN = "CYCLE_RESONANCE_V1:IMPLEMENTATION_MANIFEST"
MANIFEST_AUTHORITY_CLASS = "FROZEN_IMPLEMENTATION_MANIFEST_ZERO_EVIDENCE"

REQUIRED_FIELDS = (
    "schema_version",
    "family_id",
    "implementation_id",
    "family_contract_sha256",
    "risk_set_spec_id",
    "primary_label_spec_id",
    "requested_observation_fields",
    "requested_expectation_measures",
    "claim_topics",
    "coverage_policy",
    "clock_transform_ids_and_hashes",
    "claim_interpreter_id",
    "claim_interpreter_sha256",
    "ordered_sequence_spec",
    "falsifier_spec",
    "model_class",
    "model_hyperparameters",
    "training_window_rule",
    "calibration_method",
    "ranking_rule",
    "search_family_id",
    "preregistered_search_budget",
    "actual_trials_consumed_at_freeze",
    "cost_assumptions",
    "code_byte_manifest",
)

ORDERED_SEQUENCE_REQUIRED_FIELDS = {
    "required_edges",
    "allowed_skipped_edges",
    "maximum_temporal_lag",
    "clock_inflection_definitions",
    "contradiction_scoring",
    "missing_clock_policy",
}


def freeze_implementation_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and hash one explicit CRV1 implementation declaration."""

    if not isinstance(payload, Mapping):
        raise ValueError("cycle_resonance_implementation_manifest_mapping_required")
    raw = dict(payload)
    if "manifest_sha256" in raw:
        raise ValueError("cycle_resonance_implementation_manifest_hash_must_not_be_predeclared")
    if "financial_alpha_evidence" in raw or "authority_class" in raw:
        raise ValueError("cycle_resonance_implementation_manifest_authority_fields_reserved")
    if set(raw) != set(REQUIRED_FIELDS):
        missing = sorted(set(REQUIRED_FIELDS) - set(raw))
        extra = sorted(set(raw) - set(REQUIRED_FIELDS))
        raise ValueError(
            "cycle_resonance_implementation_manifest_fields_invalid:"
            f"missing={','.join(missing)};extra={','.join(extra)}"
        )

    _validate_manifest_body(raw)
    body = deepcopy(raw)
    body["authority_class"] = MANIFEST_AUTHORITY_CLASS
    body["financial_alpha_evidence"] = 0
    manifest_sha256 = domain_hash(MANIFEST_DOMAIN, _hash_safe(body))
    return {**body, "manifest_sha256": manifest_sha256}


def verify_implementation_manifest(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest, Mapping):
        raise ValueError("cycle_resonance_implementation_manifest_mapping_required")
    expected_fields = set(REQUIRED_FIELDS) | {
        "authority_class",
        "financial_alpha_evidence",
        "manifest_sha256",
    }
    if set(manifest) != expected_fields:
        raise ValueError("cycle_resonance_implementation_manifest_sealed_fields_invalid")
    if manifest.get("authority_class") != MANIFEST_AUTHORITY_CLASS:
        raise ValueError("cycle_resonance_implementation_manifest_authority_invalid")
    if manifest.get("financial_alpha_evidence") != 0:
        raise ValueError("cycle_resonance_implementation_manifest_financial_alpha_evidence_must_be_zero")
    body = {key: deepcopy(value) for key, value in manifest.items() if key != "manifest_sha256"}
    _validate_manifest_body({key: body[key] for key in REQUIRED_FIELDS})
    expected = domain_hash(MANIFEST_DOMAIN, _hash_safe(body))
    if str(manifest.get("manifest_sha256") or "") != expected:
        raise ValueError("cycle_resonance_implementation_manifest_hash_mismatch")


def _validate_manifest_body(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != IMPLEMENTATION_MANIFEST_SCHEMA:
        raise ValueError("cycle_resonance_implementation_manifest_schema_invalid")
    if payload.get("family_id") != FAMILY_ID:
        raise ValueError("cycle_resonance_implementation_manifest_family_invalid")
    if payload.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise ValueError("cycle_resonance_implementation_manifest_risk_set_invalid")
    if payload.get("primary_label_spec_id") != PRIMARY_LABEL_SPEC_ID:
        raise ValueError("cycle_resonance_implementation_manifest_label_invalid")
    _nonempty_text(payload.get("implementation_id"), "implementation_id")
    _sha(payload.get("family_contract_sha256"), "family_contract_sha256")

    observation_fields = _unique_text_sequence(
        payload.get("requested_observation_fields"), "requested_observation_fields"
    )
    if not observation_fields:
        raise ValueError("cycle_resonance_requested_observation_fields_required")
    unknown_observation = sorted(set(observation_fields) - set(OBSERVATION_FIELDS))
    if unknown_observation:
        raise ValueError(
            "cycle_resonance_requested_observation_field_unknown:" + ",".join(unknown_observation)
        )

    expectation_measures = _unique_text_sequence(
        payload.get("requested_expectation_measures"), "requested_expectation_measures"
    )
    if not expectation_measures:
        raise ValueError("cycle_resonance_requested_expectation_measures_required")
    unknown_expectations = sorted(set(expectation_measures) - set(EXPECTATION_MEASURES))
    if unknown_expectations:
        raise ValueError(
            "cycle_resonance_requested_expectation_measure_unknown:" + ",".join(unknown_expectations)
        )

    claim_topics = _unique_text_sequence(payload.get("claim_topics"), "claim_topics")
    if not claim_topics:
        raise ValueError("cycle_resonance_claim_topics_required")
    unknown_topics = sorted(set(claim_topics) - set(CLAIM_TOPICS))
    if unknown_topics:
        raise ValueError("cycle_resonance_claim_topic_unknown:" + ",".join(unknown_topics))

    _nonempty_mapping(payload.get("coverage_policy"), "coverage_policy")
    transforms = _nonempty_mapping(
        payload.get("clock_transform_ids_and_hashes"), "clock_transform_ids_and_hashes"
    )
    for transform_id, digest in transforms.items():
        _nonempty_text(transform_id, "clock_transform_id")
        _sha(digest, f"clock_transform_sha256:{transform_id}")

    _nonempty_text(payload.get("claim_interpreter_id"), "claim_interpreter_id")
    _sha(payload.get("claim_interpreter_sha256"), "claim_interpreter_sha256")

    ordered = _nonempty_mapping(payload.get("ordered_sequence_spec"), "ordered_sequence_spec")
    if set(ordered) != ORDERED_SEQUENCE_REQUIRED_FIELDS:
        raise ValueError("cycle_resonance_ordered_sequence_spec_fields_invalid")
    if not _sequence(ordered.get("required_edges"), "ordered_sequence_required_edges"):
        raise ValueError("cycle_resonance_ordered_sequence_required_edges_required")
    _sequence(ordered.get("allowed_skipped_edges"), "ordered_sequence_allowed_skipped_edges")
    _nonempty_mapping(ordered.get("maximum_temporal_lag"), "ordered_sequence_maximum_temporal_lag")
    _nonempty_mapping(
        ordered.get("clock_inflection_definitions"),
        "ordered_sequence_clock_inflection_definitions",
    )
    _nonempty_mapping(ordered.get("contradiction_scoring"), "ordered_sequence_contradiction_scoring")
    _nonempty_mapping(ordered.get("missing_clock_policy"), "ordered_sequence_missing_clock_policy")

    _nonempty_mapping(payload.get("falsifier_spec"), "falsifier_spec")
    _nonempty_text(payload.get("model_class"), "model_class")
    _mapping(payload.get("model_hyperparameters"), "model_hyperparameters")
    _nonempty_mapping(payload.get("training_window_rule"), "training_window_rule")
    _nonempty_text(payload.get("calibration_method"), "calibration_method")
    _nonempty_mapping(payload.get("ranking_rule"), "ranking_rule")
    _nonempty_text(payload.get("search_family_id"), "search_family_id")

    budget = _nonnegative_int(payload.get("preregistered_search_budget"), "preregistered_search_budget")
    if budget < 1:
        raise ValueError("cycle_resonance_preregistered_search_budget_must_be_positive")
    consumed = _nonnegative_int(
        payload.get("actual_trials_consumed_at_freeze"), "actual_trials_consumed_at_freeze"
    )
    if consumed > budget:
        raise ValueError("cycle_resonance_actual_trials_exceed_preregistered_budget")

    _nonempty_mapping(payload.get("cost_assumptions"), "cost_assumptions")
    code_manifest = _nonempty_mapping(payload.get("code_byte_manifest"), "code_byte_manifest")
    if "manifest_sha256" not in code_manifest:
        raise ValueError("cycle_resonance_code_byte_manifest_sha256_required")
    _sha(code_manifest["manifest_sha256"], "code_byte_manifest_sha256")


def _unique_text_sequence(value: Any, field: str) -> tuple[str, ...]:
    seq = _sequence(value, field)
    text = tuple(str(item).strip() for item in seq)
    if any(not item for item in text):
        raise ValueError(f"cycle_resonance_{field}_blank")
    if len(set(text)) != len(text):
        raise ValueError(f"cycle_resonance_{field}_duplicate")
    return text


def _sequence(value: Any, field: str) -> Sequence[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"cycle_resonance_{field}_sequence_required")
    return value


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"cycle_resonance_{field}_mapping_required")
    return value


def _nonempty_mapping(value: Any, field: str) -> Mapping[str, Any]:
    mapping = _mapping(value, field)
    if not mapping:
        raise ValueError(f"cycle_resonance_{field}_required")
    return mapping


def _nonempty_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"cycle_resonance_{field}_required")
    return text


def _sha(value: Any, field: str) -> str:
    try:
        return assert_sha256(str(value or ""))
    except ValueError as exc:
        raise ValueError(f"cycle_resonance_{field}_invalid") from exc


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"cycle_resonance_{field}_nonnegative_int_required")
    return value


def _hash_safe(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, Mapping):
        return {str(key): _hash_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_hash_safe(item) for item in value]
    raise ValueError(f"cycle_resonance_manifest_value_type_unsupported:{type(value).__name__}")
