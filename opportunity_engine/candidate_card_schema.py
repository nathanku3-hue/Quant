from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from opportunity_engine.source_classes import SignalFamily
from opportunity_engine.states import OpportunityState


class CandidateStatus(StrEnum):
    CANDIDATE_CARD_ONLY = "candidate_card_only"


ALLOWED_INITIAL_STATES = frozenset(
    {
        OpportunityState.THESIS_CANDIDATE.value,
        OpportunityState.EVIDENCE_BUILDING.value,
    }
)

FORBIDDEN_ACTION_STATES = frozenset(
    {
        OpportunityState.BUYING_RANGE.value,
        OpportunityState.ADD_ON_SETUP.value,
        OpportunityState.LET_WINNER_RUN.value,
        OpportunityState.TRIM_OPTIONAL.value,
    }
)

REQUIRED_TOP_LEVEL_FIELDS = frozenset(
    {
        "candidate_id",
        "ticker",
        "company_name",
        "theme",
        "supercycle_family_id",
        "candidate_status",
        "created_at",
        "created_by",
        "source_quality_summary",
        "manifest_uri",
        "state_machine_version",
        "primary_alpha",
        "secondary_alpha",
        "state_mapping",
        "risk_discipline",
        "forbidden_outputs",
    }
)

REQUIRED_SOURCE_QUALITY_BUCKETS = frozenset(
    {
        "observed",
        "estimated",
        "inferred",
        "research_only",
        "not_canonical",
        "missing",
        "stale",
        "forbidden",
        "canonical_sources",
    }
)

REQUIRED_FORBIDDEN_OUTPUT_FLAGS = {
    "no_score": True,
    "no_rank": True,
    "no_buy_sell_signal": True,
    "no_alert": True,
    "no_broker_action": True,
}

ALLOWED_NEGATED_OUTPUT_KEYS = frozenset(REQUIRED_FORBIDDEN_OUTPUT_FLAGS)

FORBIDDEN_SCORE_RANK_KEYS = frozenset(
    {
        "score",
        "alpha_score",
        "signal_score",
        "candidate_score",
        "factor_score",
        "factor_scores",
        "rank",
        "ranking",
        "candidate_rank",
        "upside",
        "upside_pct",
        "price_target",
        "target_price",
    }
)

FORBIDDEN_ACTION_KEYS = frozenset(
    {
        "buy_sell_signal",
        "buy_signal",
        "sell_signal",
        "trade_signal",
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

ESTIMATED_ONLY_SIGNAL_FAMILIES = frozenset(
    {
        SignalFamily.ROTATION_SCORE.value,
        SignalFamily.OPTIONS_WHALE_RADAR.value,
        SignalFamily.GAMMA_DEALER_MAP.value,
        SignalFamily.DARK_POOL_BLOCK_RADAR.value,
        SignalFamily.NEWS_NARRATIVE_VELOCITY.value,
    }
)

REQUIRED_PROVIDER_GAP_SIGNALS = frozenset(
    {
        SignalFamily.IV_VOL_INTELLIGENCE.value,
        SignalFamily.OPTIONS_WHALE_RADAR.value,
        SignalFamily.GAMMA_DEALER_MAP.value,
    }
)

REQUIRED_GOVERNANCE_FLAGS = {
    "not_validated": True,
    "not_actionable": True,
    "no_score": True,
    "no_rank": True,
    "no_buy_sell_signal": True,
    "no_alert": True,
    "no_broker_action": True,
}


@dataclass(frozen=True)
class CandidateCardValidationResult:
    valid: bool
    errors: tuple[str, ...]


class CandidateCardValidationError(ValueError):
    pass


def validate_candidate_card(
    card: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> CandidateCardValidationResult:
    errors: list[str] = []

    _validate_required_top_level_fields(card, errors)
    _validate_candidate_identity(card, errors)
    _validate_source_quality_summary(card, errors)
    _validate_state_mapping(card, errors)
    _validate_forbidden_outputs(card, errors)
    _validate_no_forbidden_fields(card, errors)
    _validate_observed_estimated_boundaries(card, errors)
    _validate_provider_gap_signals(card, errors)
    _validate_governance_flags(card, errors)
    _validate_yfinance_not_canonical(card, manifest, errors)

    return CandidateCardValidationResult(valid=not errors, errors=tuple(errors))


def assert_valid_candidate_card(
    card: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> None:
    result = validate_candidate_card(card, manifest=manifest)
    if not result.valid:
        raise CandidateCardValidationError("; ".join(result.errors))


def _validate_required_top_level_fields(card: Mapping[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS.difference(card))
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(missing)}")


def _validate_candidate_identity(card: Mapping[str, Any], errors: list[str]) -> None:
    for field_name in ("ticker", "theme", "manifest_uri"):
        value = card.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} is required")

    if card.get("candidate_status") != CandidateStatus.CANDIDATE_CARD_ONLY.value:
        errors.append("candidate_status must be candidate_card_only")


def _validate_source_quality_summary(card: Mapping[str, Any], errors: list[str]) -> None:
    summary = card.get("source_quality_summary")
    if not isinstance(summary, Mapping):
        errors.append("source_quality_summary is required")
        return

    missing = sorted(REQUIRED_SOURCE_QUALITY_BUCKETS.difference(summary))
    if missing:
        errors.append(f"source_quality_summary missing buckets: {', '.join(missing)}")


def _validate_state_mapping(card: Mapping[str, Any], errors: list[str]) -> None:
    state_mapping = card.get("state_mapping")
    if not isinstance(state_mapping, Mapping):
        errors.append("state_mapping is required")
        return

    initial_state = state_mapping.get("initial_state")
    if initial_state not in ALLOWED_INITIAL_STATES:
        errors.append("initial_state must be THESIS_CANDIDATE or EVIDENCE_BUILDING")

    allowed_next_states = state_mapping.get("allowed_next_states", ())
    if not isinstance(allowed_next_states, list):
        errors.append("allowed_next_states must be a list")
        allowed_next_states = []

    forbidden_allowed = sorted(FORBIDDEN_ACTION_STATES.intersection(set(allowed_next_states)))
    if forbidden_allowed:
        errors.append(f"allowed_next_states includes forbidden action states: {', '.join(forbidden_allowed)}")

    forbidden_jumps = state_mapping.get("forbidden_jumps", ())
    if not isinstance(forbidden_jumps, list):
        errors.append("forbidden_jumps must be a list")
        return

    forbidden_text = " ".join(str(item) for item in forbidden_jumps)
    missing_forbidden = sorted(state for state in FORBIDDEN_ACTION_STATES if state not in forbidden_text)
    if missing_forbidden:
        errors.append(f"forbidden_jumps must explicitly block: {', '.join(missing_forbidden)}")


def _validate_forbidden_outputs(card: Mapping[str, Any], errors: list[str]) -> None:
    forbidden_outputs = card.get("forbidden_outputs")
    if not isinstance(forbidden_outputs, Mapping):
        errors.append("forbidden_outputs is required")
        return

    for field_name, expected_value in REQUIRED_FORBIDDEN_OUTPUT_FLAGS.items():
        if forbidden_outputs.get(field_name) is not expected_value:
            errors.append(f"forbidden_outputs.{field_name} must be true")


def _validate_no_forbidden_fields(card: Mapping[str, Any], errors: list[str]) -> None:
    forbidden_keys = FORBIDDEN_SCORE_RANK_KEYS.union(FORBIDDEN_ACTION_KEYS)
    for path, key, _value in _walk_mapping_keys(card):
        normalized = _normalize_key(key)
        if normalized in ALLOWED_NEGATED_OUTPUT_KEYS:
            continue
        if normalized in forbidden_keys:
            errors.append(f"forbidden field present at {'.'.join((*path, key))}")


def _validate_observed_estimated_boundaries(card: Mapping[str, Any], errors: list[str]) -> None:
    secondary_alpha = card.get("secondary_alpha")
    if not isinstance(secondary_alpha, Mapping):
        errors.append("secondary_alpha is required")
        return

    observed = secondary_alpha.get("observed_signals_available", ())
    if not isinstance(observed, list):
        errors.append("secondary_alpha.observed_signals_available must be a list")
        return

    for entry in observed:
        signal_family = _entry_value(entry, "signal_family")
        quality_label = _entry_value(entry, "quality_label")
        source_label = _entry_value(entry, "observed_estimated_or_inferred")
        if signal_family in ESTIMATED_ONLY_SIGNAL_FAMILIES:
            errors.append(f"estimated-only signal presented as observed: {signal_family}")
        if _normalize_text(quality_label) == "estimated" or _normalize_text(source_label) == "estimated":
            errors.append("estimated signal cannot be presented as observed")


def _validate_provider_gap_signals(card: Mapping[str, Any], errors: list[str]) -> None:
    secondary_alpha = card.get("secondary_alpha")
    if not isinstance(secondary_alpha, Mapping):
        return

    blocked = secondary_alpha.get("blocked_signals_due_to_provider_gap", ())
    if not isinstance(blocked, list):
        errors.append("secondary_alpha.blocked_signals_due_to_provider_gap must be a list")
        return

    blocked_families = {_entry_value(entry, "signal_family") for entry in blocked}
    missing = sorted(REQUIRED_PROVIDER_GAP_SIGNALS.difference(blocked_families))
    if missing:
        errors.append(f"provider gap must explicitly include: {', '.join(missing)}")


def _validate_governance_flags(card: Mapping[str, Any], errors: list[str]) -> None:
    governance = card.get("governance")
    if governance is None:
        return
    if not isinstance(governance, Mapping):
        errors.append("governance must be an object when present")
        return

    for field_name, expected_value in REQUIRED_GOVERNANCE_FLAGS.items():
        if governance.get(field_name) is not expected_value:
            errors.append(f"governance.{field_name} must be true")


def _validate_yfinance_not_canonical(
    card: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    errors: list[str],
) -> None:
    canonical_entries = list(_canonical_source_entries(card))
    if manifest is not None:
        canonical_entries.extend(_canonical_source_entries(manifest))

    for entry in canonical_entries:
        if "yfinance" in _stringify(entry).lower():
            errors.append("yfinance cannot be a canonical source for a G8 candidate card")


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
            elif normalized in {"source_notes", "sources"} and isinstance(value, list):
                entries.extend(
                    entry
                    for entry in value
                    if isinstance(entry, Mapping) and bool(entry.get("canonical"))
                )
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
            entries.extend(_walk_mapping_keys(value, (*path, str(index))))
    return entries


def _entry_value(entry: Any, field_name: str) -> str:
    if isinstance(entry, Mapping):
        value = entry.get(field_name, "")
    else:
        value = entry
    return str(value)


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
