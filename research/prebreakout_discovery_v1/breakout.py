"""Pure algorithmic breakout-B and TTFLD mechanics for PREBREAKOUT_DISCOVERY_v1.

This module does not fetch data, open labels, score a predictive model, or name
smoke tickers.  It operates only on already-admitted session/close inputs and
immutable flag-session identities supplied by later workstreams.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import math
import re
from typing import Any, Mapping, Sequence

from research.prebreakout_discovery_v1.preregistration import (
    BREAKOUT_EPISODE_COOLDOWN_SESSIONS,
    BREAKOUT_LOOKBACK_SESSIONS,
    CONTRACT_SHA256,
    FAMILY_ID,
    LEAD_LOOKBACK_SESSIONS,
    MISSED_TTFLD_EFFECTIVE_SESSIONS,
    SMOKE_EXCLUSION_REASON_CODES,
    SMOKE_UNAVAILABLE_REASON_CODES,
)


_CIQSEC_RE = re.compile(r"^CIQSEC:IQ\d+$")
_TRADING_ITEM_RE = re.compile(r"^\d+$")


@dataclass(frozen=True)
class BreakoutEvent:
    """One deterministic episode-level algorithmic breakout B."""

    security_id: str
    trading_item_id: str
    session_date: str
    session_index: int
    close: float
    prior_high_20: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TTFLDResult:
    """Time to first legitimate detection, measured in observed sessions."""

    breakout_session: str
    b_minus_one_session: str
    first_legitimate_detection_session: str | None
    ttfld_sessions: int | None
    effective_ttfld_sessions: int
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SmokeObligationResult:
    """Generic B-1 smoke obligation result; no ticker-specific logic exists."""

    security_id: str
    breakout_session: str
    b_minus_one_session: str
    status: str
    deterministic_exclusion_reason: str | None
    first_legitimate_detection_session: str | None
    ttfld_sessions: int | None
    acceptance_weight: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def algorithmic_breakout_events(rows: Sequence[Mapping[str, Any]]) -> list[BreakoutEvent]:
    """Compute frozen B episodes from one exact listing's PIT-normalized closes.

    Raw breakout at session t:
        close_t > max(close over the immediately prior 20 observed sessions)

    Episode de-duplication:
        after accepting B, at least 20 full observed sessions must lie between
        it and the next accepted B.  Thus another episode can be accepted only
        when current_index - previous_B_index > 20.

    Equality with the prior high is not a breakout.  Invalid or duplicate rows
    fail closed rather than being skipped/repaired.
    """

    materialized = _validated_close_rows(rows)
    events: list[BreakoutEvent] = []
    previous_b_index: int | None = None
    for index in range(BREAKOUT_LOOKBACK_SESSIONS, len(materialized)):
        current = materialized[index]
        prior = materialized[index - BREAKOUT_LOOKBACK_SESSIONS : index]
        prior_high = max(item["close"] for item in prior)
        if current["close"] <= prior_high:
            continue
        if previous_b_index is not None and index - previous_b_index <= BREAKOUT_EPISODE_COOLDOWN_SESSIONS:
            continue
        event = BreakoutEvent(
            security_id=current["security_id"],
            trading_item_id=current["trading_item_id"],
            session_date=current["session_date"],
            session_index=index,
            close=current["close"],
            prior_high_20=prior_high,
        )
        events.append(event)
        previous_b_index = index
    return events


def measure_ttfld(
    *,
    ordered_sessions: Sequence[str],
    breakout_session: str,
    flag_sessions: Sequence[str],
) -> TTFLDResult:
    """Measure earliest legitimate flag in [B-20, B-1].

    A flag at B is too late.  Flags earlier than B-20 are stale for this frozen
    component and do not receive TTFLD credit.  Misses have an effective TTFLD
    of zero so aggregate lead statistics cannot condition only on successes.
    """

    sessions = _validated_sessions(ordered_sessions)
    index_by_session = {session: index for index, session in enumerate(sessions)}
    if breakout_session not in index_by_session:
        raise ValueError("prebreakout_breakout_session_not_in_calendar")
    b_index = index_by_session[breakout_session]
    if b_index < 1:
        raise ValueError("prebreakout_breakout_has_no_b_minus_one_session")
    b_minus_one = sessions[b_index - 1]
    lower_index = max(0, b_index - LEAD_LOOKBACK_SESSIONS)

    flag_indices: list[int] = []
    for raw in flag_sessions:
        session = str(raw)
        if session not in index_by_session:
            raise ValueError("prebreakout_flag_session_not_in_calendar")
        index = index_by_session[session]
        if lower_index <= index <= b_index - 1:
            flag_indices.append(index)

    if not flag_indices:
        return TTFLDResult(
            breakout_session=breakout_session,
            b_minus_one_session=b_minus_one,
            first_legitimate_detection_session=None,
            ttfld_sessions=None,
            effective_ttfld_sessions=MISSED_TTFLD_EFFECTIVE_SESSIONS,
            status="MISSED_PREBREAKOUT",
        )

    first_index = min(flag_indices)
    lead = b_index - first_index
    if lead < 1 or lead > LEAD_LOOKBACK_SESSIONS:  # defensive closure around the frozen bounds
        raise ValueError("prebreakout_ttfld_out_of_frozen_bounds")
    return TTFLDResult(
        breakout_session=breakout_session,
        b_minus_one_session=b_minus_one,
        first_legitimate_detection_session=sessions[first_index],
        ttfld_sessions=lead,
        effective_ttfld_sessions=lead,
        status="DETECTED_PREBREAKOUT",
    )


def verify_b_minus_one_smoke_obligation(
    *,
    security_id: str,
    ordered_sessions: Sequence[str],
    breakout_session: str,
    b_minus_one_eligible: bool,
    deterministic_exclusion_reason: str | None,
    flag_sessions: Sequence[str],
) -> SmokeObligationResult:
    """Enforce: eligible at B-1 => flag by B-1; otherwise deterministic exclusion.

    The function is deliberately generic.  W4 may call it for named smoke
    cases, but W2 contains no ticker literals and gives every smoke row zero
    statistical acceptance weight.
    """

    if not str(security_id).strip():
        raise ValueError("prebreakout_smoke_security_id_required")
    sessions = _validated_sessions(ordered_sessions)
    index_by_session = {session: index for index, session in enumerate(sessions)}
    if breakout_session not in index_by_session:
        raise ValueError("prebreakout_breakout_session_not_in_calendar")
    b_index = index_by_session[breakout_session]
    if b_index < 1:
        raise ValueError("prebreakout_breakout_has_no_b_minus_one_session")
    b_minus_one = sessions[b_index - 1]

    if not b_minus_one_eligible:
        if deterministic_exclusion_reason not in SMOKE_EXCLUSION_REASON_CODES:
            raise ValueError("prebreakout_smoke_deterministic_exclusion_reason_required")
        return SmokeObligationResult(
            security_id=str(security_id),
            breakout_session=breakout_session,
            b_minus_one_session=b_minus_one,
            status="DETERMINISTIC_EXCLUSION",
            deterministic_exclusion_reason=deterministic_exclusion_reason,
            first_legitimate_detection_session=None,
            ttfld_sessions=None,
        )

    if deterministic_exclusion_reason is not None:
        raise ValueError("prebreakout_smoke_eligible_cannot_have_exclusion_reason")
    ttfld = measure_ttfld(
        ordered_sessions=sessions,
        breakout_session=breakout_session,
        flag_sessions=flag_sessions,
    )
    if ttfld.status != "DETECTED_PREBREAKOUT":
        raise ValueError("prebreakout_b_minus_one_eligible_without_prebreakout_flag")
    return SmokeObligationResult(
        security_id=str(security_id),
        breakout_session=breakout_session,
        b_minus_one_session=b_minus_one,
        status="FLAGGED_PREBREAKOUT",
        deterministic_exclusion_reason=None,
        first_legitimate_detection_session=ttfld.first_legitimate_detection_session,
        ttfld_sessions=ttfld.ttfld_sessions,
    )


def enforce_b_minus_one_pit_proof(
    *,
    pit_proof: Any,
    ordered_sessions: Sequence[str],
    flag_sessions: Sequence[str],
) -> SmokeObligationResult:
    """Consume one verified W3-style B-1 proof under the frozen W2 obligation.

    ``DETERMINISTIC_UNAVAILABLE`` never satisfies the W2 smoke obligation. It
    blocks the case until upstream authority exists. A genuine deterministic
    W3 exclusion is acceptable; an eligible B-1 row requires a flag no later
    than B-1. Display symbols remain trace metadata and carry zero weight.
    """

    if isinstance(pit_proof, Mapping):
        proof = dict(pit_proof)
    elif hasattr(pit_proof, "as_dict") and callable(pit_proof.as_dict):
        proof = dict(pit_proof.as_dict())
    else:
        raise ValueError("prebreakout_smoke_pit_proof_mapping_required")

    if proof.get("family_id") != FAMILY_ID:
        raise ValueError("prebreakout_smoke_pit_proof_family_invalid")
    if proof.get("breakout_contract_sha256") != CONTRACT_SHA256:
        raise ValueError("prebreakout_smoke_pit_proof_breakout_contract_unbound")
    if proof.get("display_symbol_used_for_logic") is not False:
        raise ValueError("prebreakout_smoke_display_symbol_logic_forbidden")
    if proof.get("statistical_weight") != 0 or proof.get("promotion_denominator_weight") != 0:
        raise ValueError("prebreakout_smoke_zero_weight_required")
    if proof.get("outcome_access_performed") is not False:
        raise ValueError("prebreakout_smoke_outcome_access_forbidden")
    if proof.get("financial_alpha_evidence") != 0 or proof.get("capital_authority") != "NONE":
        raise ValueError("prebreakout_smoke_authority_invalid")

    breakout_session = str(proof.get("breakout_session") or "")
    b_minus_one_session = str(proof.get("b_minus_1_session") or "")
    sessions = _validated_sessions(ordered_sessions)
    if breakout_session not in sessions:
        raise ValueError("prebreakout_breakout_session_not_in_calendar")
    b_index = sessions.index(breakout_session)
    if b_index < 1 or b_minus_one_session != sessions[b_index - 1]:
        raise ValueError("prebreakout_smoke_pit_proof_b_minus_one_not_exact")

    security_id = str(proof.get("security_id") or "").strip()
    status = str(proof.get("status") or "")
    reason = proof.get("reason")
    if status == "DETERMINISTIC_UNAVAILABLE":
        if reason not in SMOKE_UNAVAILABLE_REASON_CODES:
            raise ValueError("prebreakout_smoke_unavailable_reason_invalid")
        raise ValueError("prebreakout_smoke_upstream_authority_unavailable")
    if status == "DETERMINISTIC_EXCLUSION":
        return verify_b_minus_one_smoke_obligation(
            security_id=security_id,
            ordered_sessions=sessions,
            breakout_session=breakout_session,
            b_minus_one_eligible=False,
            deterministic_exclusion_reason=None if reason is None else str(reason),
            flag_sessions=flag_sessions,
        )
    if status != "PIT_ELIGIBLE_B_MINUS_1":
        raise ValueError("prebreakout_smoke_pit_proof_status_invalid")
    if reason is not None:
        raise ValueError("prebreakout_smoke_eligible_cannot_have_exclusion_reason")
    if not str(proof.get("trading_item_id") or "").strip():
        raise ValueError("prebreakout_smoke_trading_item_id_required")
    return verify_b_minus_one_smoke_obligation(
        security_id=security_id,
        ordered_sessions=sessions,
        breakout_session=breakout_session,
        b_minus_one_eligible=True,
        deterministic_exclusion_reason=None,
        flag_sessions=flag_sessions,
    )


def _validated_close_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("prebreakout_close_rows_sequence_required")
    materialized: list[dict[str, Any]] = []
    seen_sessions: set[str] = set()
    listing_keys: set[tuple[str, str]] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError("prebreakout_close_row_mapping_required")
        session = str(raw.get("session_date") or "")
        _validate_iso_date(session, "close_row_session_date")
        if session in seen_sessions:
            raise ValueError("prebreakout_duplicate_close_session")
        seen_sessions.add(session)
        try:
            close = float(raw.get("close"))
        except (TypeError, ValueError) as exc:
            raise ValueError("prebreakout_close_invalid") from exc
        if not math.isfinite(close) or close <= 0:
            raise ValueError("prebreakout_close_must_be_finite_positive")
        security_id = str(raw.get("security_id") or "").strip()
        trading_item_id = str(raw.get("trading_item_id") or "").strip()
        if not _CIQSEC_RE.fullmatch(security_id):
            raise ValueError("prebreakout_breakout_ciqsec_security_id_required")
        if not _TRADING_ITEM_RE.fullmatch(trading_item_id):
            raise ValueError("prebreakout_breakout_trading_item_id_required")
        listing_keys.add((security_id, trading_item_id))
        materialized.append(
            {
                "session_date": session,
                "close": close,
                "security_id": security_id,
                "trading_item_id": trading_item_id,
            }
        )
    materialized.sort(key=lambda item: item["session_date"])
    if len(listing_keys) > 1:
        raise ValueError("prebreakout_breakout_rows_must_be_one_exact_listing")
    return materialized


def _validated_sessions(ordered_sessions: Sequence[str]) -> list[str]:
    if not isinstance(ordered_sessions, Sequence) or isinstance(ordered_sessions, (str, bytes)):
        raise ValueError("prebreakout_ordered_sessions_sequence_required")
    sessions = [str(value) for value in ordered_sessions]
    if not sessions:
        raise ValueError("prebreakout_ordered_sessions_empty")
    for session in sessions:
        _validate_iso_date(session, "ordered_session")
    if len(set(sessions)) != len(sessions):
        raise ValueError("prebreakout_ordered_sessions_duplicate")
    if sessions != sorted(sessions):
        raise ValueError("prebreakout_ordered_sessions_not_ascending")
    return sessions


def _validate_iso_date(value: str, field: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"prebreakout_{field}_invalid") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"prebreakout_{field}_invalid")
