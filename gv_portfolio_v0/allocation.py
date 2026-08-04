"""Deterministic allocation handoff for GV Portfolio V0.

This module consumes canonical strategy records and produces the one bounded
portfolio transition exercised by Slice 0. It does not mutate accounting state,
persist workspaces, render product views, or certify replay.
"""

from __future__ import annotations

from decimal import Decimal, DecimalException, InvalidOperation
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from gv_portfolio_v0.decimal_utils import (
    MAX_DECIMAL_FRACTION_DIGITS,
    MAX_DECIMAL_INTEGER_DIGITS,
    decimal_text,
    deterministic_decimal_context,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
ELIGIBLE_OUTCOMES = frozenset({"ADMIT", "CASH"})


class AllocationError(ValueError):
    """Raised when strategy-to-execution allocation authority is inconsistent."""


def _decimal(value: Any, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise AllocationError(f"{field.upper()}_INVALID") from exc
    if not parsed.is_finite():
        raise AllocationError(f"{field.upper()}_FINITE_REQUIRED")
    return parsed


def _decimal_text(value: Any, *, field: str) -> str:
    parsed = _decimal(value, field=field)
    try:
        return decimal_text(parsed)
    except ValueError as exc:
        raise AllocationError(f"{field.upper()}_OUT_OF_BOUNDS") from exc


def _money(value: Any, *, field: str) -> Decimal:
    parsed = _decimal(value, field=field)
    _, digits, exponent = parsed.as_tuple()
    effective_digits = list(digits)
    while len(effective_digits) > 1 and effective_digits[-1] == 0:
        effective_digits.pop()
        exponent += 1
    integer_digits = len(effective_digits) + max(exponent, 0)
    fraction_digits = max(-exponent, 0)
    if (
        integer_digits > MAX_DECIMAL_INTEGER_DIGITS
        or fraction_digits > MAX_DECIMAL_FRACTION_DIGITS
    ):
        raise AllocationError(f"{field.upper()}_OUT_OF_BOUNDS")
    if exponent < -2:
        raise AllocationError(f"DECLARED_PRECISION_EXCEEDED:{field}")
    return parsed


def _identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", dict(payload))


def _verify_record_id(
    record: Mapping[str, Any], *, kind: str, id_key: str
) -> None:
    if not isinstance(record, Mapping):
        raise AllocationError(f"{id_key.upper()}_RECORD_REQUIRED")
    body = {key: value for key, value in record.items() if key != id_key}
    if record.get(id_key) != _identifier(kind, body):
        raise AllocationError(f"IDENTITY_MISMATCH:{id_key}")


def validate_execution_handoff(
    decision_snapshot: Mapping[str, Any], portfolio_aim: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate the exact strategy projection consumed by execution.

    Strategy owns how the competition was computed. Execution independently
    proves that the selected action and instrument are the recorded eligible
    winner and that the snapshot is bound to the confirmed aim.
    """

    _verify_record_id(
        decision_snapshot, kind="DSN", id_key="decision_snapshot_id"
    )
    _verify_record_id(portfolio_aim, kind="AIM", id_key="portfolio_aim_id")

    aim_id = portfolio_aim["portfolio_aim_id"]
    if decision_snapshot.get("portfolio_aim_id") != aim_id:
        raise AllocationError("SNAPSHOT_AIM_BINDING_MISMATCH")

    competition = decision_snapshot.get("capital_competition")
    if not isinstance(competition, Mapping):
        raise AllocationError("CAPITAL_COMPETITION_REQUIRED")
    candidates = list(competition.get("candidates") or [])
    selected_name = competition.get("selected_candidate")
    selected_rows = [
        row
        for row in candidates
        if isinstance(row, Mapping) and row.get("candidate") == selected_name
    ]
    if len(selected_rows) != 1:
        raise AllocationError("CAPITAL_COMPETITION_WINNER_INVALID")
    winner = selected_rows[0]
    outcome = winner.get("outcome")
    if outcome not in ELIGIBLE_OUTCOMES:
        raise AllocationError("EXECUTION_WINNER_INELIGIBLE")
    if winner.get("eligible") is False:
        raise AllocationError("EXECUTION_WINNER_MARKED_INELIGIBLE")
    if competition.get("selected_instrument_id") != winner.get("instrument_id"):
        raise AllocationError("COMPETITION_INSTRUMENT_PROJECTION_MISMATCH")
    if _decimal(
        competition.get("selected_net_score_bps"), field="selected_net_score_bps"
    ) != _decimal(winner.get("net_score_bps"), field="winner_net_score_bps"):
        raise AllocationError("COMPETITION_SCORE_PROJECTION_MISMATCH")

    action = decision_snapshot.get("selected_action")
    allowed_actions = set(portfolio_aim.get("allowed_actions") or [])
    if action not in allowed_actions:
        raise AllocationError("ACTION_NOT_ALLOWED_BY_AIM")

    if outcome == "ADMIT":
        if action != "BUY":
            raise AllocationError("ADMIT_WINNER_REQUIRES_BUY")
        instrument_id = winner.get("instrument_id")
        if not isinstance(instrument_id, str) or not instrument_id:
            raise AllocationError("BUY_INSTRUMENT_REQUIRED")
        if decision_snapshot.get("selected_instrument_id") != instrument_id:
            raise AllocationError("DECISION_INSTRUMENT_PROJECTION_MISMATCH")
        quantity = _decimal(
            decision_snapshot.get("selected_quantity"), field="selected_quantity"
        )
        reference_price = _money(
            decision_snapshot.get("reference_price"), field="reference_price"
        )
        fee = _money(decision_snapshot.get("fee"), field="fee")
        if quantity <= 0:
            raise AllocationError("SELECTED_QUANTITY_MUST_BE_POSITIVE")
        if reference_price <= 0:
            raise AllocationError("REFERENCE_PRICE_MUST_BE_POSITIVE")
        if fee < 0:
            raise AllocationError("FEE_MUST_BE_NONNEGATIVE")
    else:
        if action != "CASH":
            raise AllocationError("CASH_WINNER_REQUIRES_CASH_ACTION")
        if winner.get("instrument_id") is not None:
            raise AllocationError("CASH_WINNER_INSTRUMENT_PROHIBITED")
        if decision_snapshot.get("selected_instrument_id") is not None:
            raise AllocationError("CASH_DECISION_INSTRUMENT_PROHIBITED")
        quantity = _decimal(
            decision_snapshot.get("selected_quantity", "0"),
            field="selected_quantity",
        )
        reference_price = _money(
            decision_snapshot.get("reference_price", "0"), field="reference_price"
        )
        fee = _money(decision_snapshot.get("fee", "0"), field="fee")
        if any(value != 0 for value in (quantity, reference_price, fee)):
            raise AllocationError("CASH_DECISION_ECONOMICS_MUST_BE_ZERO")
        instrument_id = None

    return {
        "decision_snapshot_id": decision_snapshot["decision_snapshot_id"],
        "portfolio_aim_id": aim_id,
        "selected_candidate": selected_name,
        "outcome": outcome,
        "action": action,
        "instrument_id": instrument_id,
        "quantity": _decimal_text(quantity, field="quantity"),
        "reference_price": _decimal_text(
            reference_price, field="reference_price"
        ),
        "fee": _decimal_text(fee, field="fee"),
    }


def plan_transition(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    *,
    current_quantity: Any,
    cash_bucket: str = "AVAILABLE",
) -> dict[str, Any]:
    """Create the immutable payload for one Slice 0 portfolio transition."""

    selection = validate_execution_handoff(decision_snapshot, portfolio_aim)
    current = _decimal(current_quantity, field="current_quantity")
    if current < 0:
        raise AllocationError("CURRENT_QUANTITY_MUST_BE_NONNEGATIVE")
    if not isinstance(cash_bucket, str) or not cash_bucket:
        raise AllocationError("CASH_BUCKET_REQUIRED")

    try:
        with deterministic_decimal_context():
            delta = _decimal(selection["quantity"], field="selected_quantity")
            if selection["action"] == "BUY":
                target = current + delta
            else:
                delta = Decimal("0")
                target = current
    except DecimalException as exc:
        raise AllocationError("DECIMAL_ARITHMETIC_INVALID") from exc

    return {
        "decision_snapshot_id": selection["decision_snapshot_id"],
        "portfolio_aim_id": selection["portfolio_aim_id"],
        "selected_candidate": selection["selected_candidate"],
        "outcome": selection["outcome"],
        "action": selection["action"],
        "instrument_id": selection["instrument_id"],
        "current_quantity": _decimal_text(current, field="current_quantity"),
        "target_quantity": _decimal_text(target, field="target_quantity"),
        "quantity_delta": _decimal_text(delta, field="quantity_delta"),
        "reference_price": selection["reference_price"],
        "expected_fee": selection["fee"],
        "cash_bucket": cash_bucket,
    }
