"""Living Thesis Lite and bounded later-observation rules for GV Portfolio V0.

This module owns strategy semantics only. It does not own custody identities,
portfolio accounting, allocation, execution, persistence, or product wiring.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import canonical_document_bytes


class StrategyThesisError(ValueError):
    """Raised when thesis authority is incomplete or contradictory."""


def _require_text(value: Any, *, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StrategyThesisError(code)
    return value


def _unique_texts(values: Iterable[Any], *, code: str, allow_empty: bool) -> list[str]:
    rows = list(values)
    if not allow_empty and not rows:
        raise StrategyThesisError(code)
    normalized = [_require_text(value, code=code) for value in rows]
    if len(normalized) != len(set(normalized)):
        raise StrategyThesisError(f"{code}_DUPLICATE")
    return normalized


def _decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise StrategyThesisError(f"{field.upper()}_INVALID")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise StrategyThesisError(f"{field.upper()}_INVALID") from exc
    if not parsed.is_finite():
        raise StrategyThesisError(f"{field.upper()}_FINITE_REQUIRED")
    return parsed


def _decimal_text(value: Any, *, field: str) -> str:
    parsed = _decimal(value, field=field)
    if parsed == 0:
        return "0"
    text = format(parsed.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def scenario_range(*, bear_value: Any, base_value: Any, bull_value: Any) -> dict[str, str]:
    """Return an ordered finite Bear/Base/Bull scenario range."""

    bear = _decimal(bear_value, field="bear_value")
    base = _decimal(base_value, field="base_value")
    bull = _decimal(bull_value, field="bull_value")
    if not bear <= base <= bull:
        raise StrategyThesisError("SCENARIO_RANGE_ORDER_INVALID")
    return {
        "bear_value": _decimal_text(bear, field="bear_value"),
        "base_value": _decimal_text(base, field="base_value"),
        "bull_value": _decimal_text(bull, field="bull_value"),
    }


def living_thesis_lite(
    *,
    principal_claim: str,
    scenario: Mapping[str, Any],
    evidence_reference_ids: Iterable[str],
    hard_falsifiers: Iterable[str],
    watch_conditions: Iterable[str],
) -> dict[str, Any]:
    """Build the minimum authoritative thesis record exercised by Slice 0."""

    if not isinstance(scenario, Mapping):
        raise StrategyThesisError("SCENARIO_RANGE_MAPPING_REQUIRED")
    expected_keys = {"bear_value", "base_value", "bull_value"}
    if set(scenario) != expected_keys:
        raise StrategyThesisError("SCENARIO_RANGE_KEYS_INVALID")
    declared_hard = _unique_texts(
        hard_falsifiers,
        code="HARD_FALSIFIER_INVALID",
        allow_empty=True,
    )
    declared_watch = _unique_texts(
        watch_conditions,
        code="WATCH_CONDITION_INVALID",
        allow_empty=True,
    )
    if set(declared_hard).intersection(declared_watch):
        raise StrategyThesisError("THESIS_RULE_CLASSIFICATION_OVERLAP")
    return {
        "principal_claim": _require_text(
            principal_claim, code="PRINCIPAL_CLAIM_REQUIRED"
        ),
        "scenario_range": scenario_range(
            bear_value=scenario["bear_value"],
            base_value=scenario["base_value"],
            bull_value=scenario["bull_value"],
        ),
        "evidence_reference_ids": _unique_texts(
            evidence_reference_ids,
            code="THESIS_EVIDENCE_REFERENCE_REQUIRED",
            allow_empty=False,
        ),
        "hard_falsifiers": declared_hard,
        "watch_conditions": declared_watch,
    }


def validate_living_thesis_lite(
    thesis: Mapping[str, Any], *, available_evidence_reference_ids: Iterable[str]
) -> None:
    """Require exact thesis shape and resolvable evidence references."""

    if not isinstance(thesis, Mapping):
        raise StrategyThesisError("LIVING_THESIS_MAPPING_REQUIRED")
    expected_keys = {
        "principal_claim",
        "scenario_range",
        "evidence_reference_ids",
        "hard_falsifiers",
        "watch_conditions",
    }
    if set(thesis) != expected_keys:
        raise StrategyThesisError("LIVING_THESIS_KEYS_INVALID")
    rebuilt = living_thesis_lite(
        principal_claim=thesis["principal_claim"],
        scenario=thesis["scenario_range"],
        evidence_reference_ids=thesis["evidence_reference_ids"],
        hard_falsifiers=thesis["hard_falsifiers"],
        watch_conditions=thesis["watch_conditions"],
    )
    if canonical_document_bytes(rebuilt) != canonical_document_bytes(dict(thesis)):
        raise StrategyThesisError("LIVING_THESIS_NOT_CANONICAL")
    available = set(
        _unique_texts(
            available_evidence_reference_ids,
            code="AVAILABLE_EVIDENCE_REFERENCE_INVALID",
            allow_empty=True,
        )
    )
    if not set(rebuilt["evidence_reference_ids"]).issubset(available):
        raise StrategyThesisError("DANGLING_EVIDENCE_REFERENCE")


def unchanged_aim_watch_observation(
    *,
    living_thesis: Mapping[str, Any],
    available_evidence_reference_ids: Iterable[str],
    evidence_reference_id: str,
    watch_condition_matches: Iterable[str],
    hard_falsifier_matches: Iterable[str],
    portfolio_aim_id_before: str,
    portfolio_aim_id_after: str,
) -> dict[str, Any]:
    """Reduce the sole exercised later-observation path.

    Slice 0 supports WATCH plus no hard-falsifier match plus unchanged aim. A
    matched hard falsifier fails closed here; the changed-aim workflow belongs
    to a later explicitly authorized slice.
    """

    validate_living_thesis_lite(
        living_thesis,
        available_evidence_reference_ids=available_evidence_reference_ids,
    )
    evidence_id = _require_text(
        evidence_reference_id, code="OBSERVATION_EVIDENCE_REFERENCE_REQUIRED"
    )
    available_evidence_ids = set(
        _unique_texts(
            available_evidence_reference_ids,
            code="AVAILABLE_EVIDENCE_REFERENCE_INVALID",
            allow_empty=True,
        )
    )
    if evidence_id not in available_evidence_ids:
        raise StrategyThesisError("DANGLING_OBSERVATION_EVIDENCE_REFERENCE")
    declared_watches = set(living_thesis["watch_conditions"])
    declared_hard = set(living_thesis["hard_falsifiers"])
    watches = sorted(
        _unique_texts(
            watch_condition_matches,
            code="WATCH_CONDITION_MATCH_REQUIRED",
            allow_empty=False,
        )
    )
    hard_matches = sorted(
        _unique_texts(
            hard_falsifier_matches,
            code="HARD_FALSIFIER_MATCH_INVALID",
            allow_empty=True,
        )
    )
    if not set(watches).issubset(declared_watches):
        raise StrategyThesisError("UNDECLARED_WATCH_CONDITION_MATCH")
    if not set(hard_matches).issubset(declared_hard):
        raise StrategyThesisError("UNDECLARED_HARD_FALSIFIER_MATCH")
    before = _require_text(portfolio_aim_id_before, code="AIM_ID_BEFORE_REQUIRED")
    after = _require_text(portfolio_aim_id_after, code="AIM_ID_AFTER_REQUIRED")
    if hard_matches:
        raise StrategyThesisError("HARD_FALSIFIER_BLOCKS_UNCHANGED_AIM")
    if before != after:
        raise StrategyThesisError("WATCH_PATH_REQUIRES_UNCHANGED_AIM")
    return {
        "evidence_reference_id": evidence_id,
        "classification": "WATCH",
        "watch_condition_matches": watches,
        "hard_falsifier_matches": [],
        "hard_falsifier_fired": False,
        "portfolio_aim_id_before": before,
        "portfolio_aim_id_after": after,
        "aim_changed": False,
    }
