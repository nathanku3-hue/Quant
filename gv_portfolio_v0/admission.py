"""Authoritative decision admission and capital competition for GV Portfolio V0.

The decision snapshot is the sole strategy authority. Product-level reviews and
cash outcome objects are projections and must equal snapshot-derived values.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.thesis import validate_living_thesis_lite

ID_DOMAIN = "GV-PORTFOLIO-V0"
COMPETITION_METHOD = "MAX_NET_SCORE_BPS_THEN_LEXICAL"
ACCEPTED_OUTCOMES = frozenset({"ADMIT", "REJECT", "ABSTAIN", "CASH"})
INSTRUMENT_OUTCOMES = frozenset({"ADMIT", "REJECT", "ABSTAIN"})
ELIGIBLE_OUTCOMES = frozenset({"ADMIT", "CASH"})


class StrategyAdmissionError(ValueError):
    """Raised when decision authority or admission semantics fail closed."""


def _require_text(value: Any, *, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StrategyAdmissionError(code)
    return value


def _require_bps(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StrategyAdmissionError(f"{field.upper()}_INTEGER_REQUIRED")
    return value


def instrument_decision_record(
    *,
    instrument_id: str,
    symbol: str,
    relationship: str,
    outcome: str,
    living_thesis: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one instrument decision record without inventing eligibility."""

    if outcome not in INSTRUMENT_OUTCOMES:
        raise StrategyAdmissionError("INSTRUMENT_OUTCOME_INVALID")
    if not isinstance(living_thesis, Mapping):
        raise StrategyAdmissionError("LIVING_THESIS_MAPPING_REQUIRED")
    return {
        "instrument_id": _require_text(
            instrument_id, code="DECISION_INSTRUMENT_ID_REQUIRED"
        ),
        "symbol": _require_text(symbol, code="DECISION_SYMBOL_REQUIRED"),
        "relationship": _require_text(
            relationship, code="DECISION_RELATIONSHIP_REQUIRED"
        ),
        "outcome": outcome,
        "living_thesis_lite": deepcopy(dict(living_thesis)),
    }


def cash_decision_record(
    *, classifications: Iterable[str], role: str
) -> dict[str, Any]:
    """Build the one explicit CASH decision record."""

    rows = list(classifications)
    if not rows:
        raise StrategyAdmissionError("CASH_CLASSIFICATION_REQUIRED")
    normalized = [
        _require_text(row, code="CASH_CLASSIFICATION_INVALID") for row in rows
    ]
    if len(normalized) != len(set(normalized)):
        raise StrategyAdmissionError("CASH_CLASSIFICATION_DUPLICATE")
    return {
        "outcome": "CASH",
        "classification": normalized,
        "role": _require_text(role, code="CASH_ROLE_REQUIRED"),
    }


def validate_decision_records(
    reviews: Iterable[Mapping[str, Any]],
    cash_outcome: Mapping[str, Any],
    *,
    available_evidence_reference_ids: Iterable[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate unique instrument decisions and exactly one explicit cash record."""

    rows = list(reviews)
    if not rows:
        raise StrategyAdmissionError("INSTRUMENT_DECISION_REQUIRED")
    canonical_rows: list[dict[str, Any]] = []
    instrument_ids: set[str] = set()
    symbols: set[str] = set()
    expected_review_keys = {
        "instrument_id",
        "symbol",
        "relationship",
        "outcome",
        "living_thesis_lite",
    }
    evidence_ids = list(available_evidence_reference_ids)
    for row in rows:
        if not isinstance(row, Mapping):
            raise StrategyAdmissionError("INSTRUMENT_DECISION_MAPPING_REQUIRED")
        if set(row) != expected_review_keys:
            raise StrategyAdmissionError("INSTRUMENT_DECISION_KEYS_INVALID")
        canonical = instrument_decision_record(
            instrument_id=row["instrument_id"],
            symbol=row["symbol"],
            relationship=row["relationship"],
            outcome=row["outcome"],
            living_thesis=row["living_thesis_lite"],
        )
        if canonical["instrument_id"] in instrument_ids:
            raise StrategyAdmissionError("DUPLICATE_INSTRUMENT_DECISION")
        if canonical["symbol"] in symbols:
            raise StrategyAdmissionError("DUPLICATE_DECISION_SYMBOL")
        instrument_ids.add(canonical["instrument_id"])
        symbols.add(canonical["symbol"])
        validate_living_thesis_lite(
            canonical["living_thesis_lite"],
            available_evidence_reference_ids=evidence_ids,
        )
        if canonical_document_bytes(canonical) != canonical_document_bytes(dict(row)):
            raise StrategyAdmissionError("INSTRUMENT_DECISION_NOT_CANONICAL")
        canonical_rows.append(canonical)

    if not isinstance(cash_outcome, Mapping):
        raise StrategyAdmissionError("CASH_DECISION_MAPPING_REQUIRED")
    if set(cash_outcome) != {"outcome", "classification", "role"}:
        raise StrategyAdmissionError("CASH_DECISION_KEYS_INVALID")
    if cash_outcome.get("outcome") != "CASH":
        raise StrategyAdmissionError("CASH_OUTCOME_REQUIRED")
    canonical_cash = cash_decision_record(
        classifications=cash_outcome["classification"], role=cash_outcome["role"]
    )
    if canonical_document_bytes(canonical_cash) != canonical_document_bytes(
        dict(cash_outcome)
    ):
        raise StrategyAdmissionError("CASH_DECISION_NOT_CANONICAL")
    return canonical_rows, canonical_cash


def _candidate_from_source(
    candidate: Mapping[str, Any],
    *,
    decisions_by_instrument: Mapping[str, Mapping[str, Any]],
    cash_outcome: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "candidate",
        "instrument_id",
        "outcome",
        "expected_value_bps",
        "risk_penalty_bps",
        "cost_penalty_bps",
    }
    if not isinstance(candidate, Mapping) or not required.issubset(candidate):
        raise StrategyAdmissionError("COMPETITION_CANDIDATE_FIELDS_MISSING")
    candidate_id = _require_text(
        candidate["candidate"], code="COMPETITION_CANDIDATE_ID_REQUIRED"
    )
    outcome = candidate["outcome"]
    if outcome not in ACCEPTED_OUTCOMES:
        raise StrategyAdmissionError("COMPETITION_OUTCOME_INVALID")
    instrument_id = candidate["instrument_id"]
    if candidate_id == "CASH":
        if instrument_id is not None or outcome != cash_outcome["outcome"]:
            raise StrategyAdmissionError("COMPETITION_CASH_CANDIDATE_INVALID")
    else:
        if not isinstance(instrument_id, str):
            raise StrategyAdmissionError("COMPETITION_INSTRUMENT_ID_REQUIRED")
        decision = decisions_by_instrument.get(instrument_id)
        if decision is None:
            raise StrategyAdmissionError("COMPETITION_DECISION_MISSING")
        if decision["symbol"] != candidate_id:
            raise StrategyAdmissionError("COMPETITION_CANDIDATE_SYMBOL_MISMATCH")
        if decision["outcome"] != outcome:
            raise StrategyAdmissionError("COMPETITION_REVIEW_OUTCOME_MISMATCH")
    expected = _require_bps(candidate["expected_value_bps"], field="expected_value_bps")
    risk = _require_bps(candidate["risk_penalty_bps"], field="risk_penalty_bps")
    cost = _require_bps(candidate["cost_penalty_bps"], field="cost_penalty_bps")
    if risk < 0:
        raise StrategyAdmissionError("RISK_PENALTY_MUST_BE_NONNEGATIVE")
    if cost < 0:
        raise StrategyAdmissionError("COST_PENALTY_MUST_BE_NONNEGATIVE")
    return {
        "candidate": candidate_id,
        "instrument_id": instrument_id,
        "outcome": outcome,
        "expected_value_bps": expected,
        "risk_penalty_bps": risk,
        "cost_penalty_bps": cost,
        "net_score_bps": expected - risk - cost,
        "eligible": outcome in ELIGIBLE_OUTCOMES,
    }


def build_capital_competition(
    candidates: Iterable[Mapping[str, Any]],
    *,
    reviews: Iterable[Mapping[str, Any]],
    cash_outcome: Mapping[str, Any],
    available_evidence_reference_ids: Iterable[str],
) -> dict[str, Any]:
    """Recompute eligibility, net scores, ordering, and winner from source inputs."""

    canonical_reviews, canonical_cash = validate_decision_records(
        reviews,
        cash_outcome,
        available_evidence_reference_ids=available_evidence_reference_ids,
    )
    by_instrument = {row["instrument_id"]: row for row in canonical_reviews}
    candidate_rows = list(candidates)
    if not candidate_rows:
        raise StrategyAdmissionError("COMPETITION_CANDIDATE_REQUIRED")
    canonical_candidates = [
        _candidate_from_source(
            row,
            decisions_by_instrument=by_instrument,
            cash_outcome=canonical_cash,
        )
        for row in candidate_rows
    ]
    candidate_ids = [row["candidate"] for row in canonical_candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise StrategyAdmissionError("DUPLICATE_COMPETITION_CANDIDATE")
    if candidate_ids.count("CASH") != 1:
        raise StrategyAdmissionError("EXACTLY_ONE_CASH_CANDIDATE_REQUIRED")
    eligible = [row for row in canonical_candidates if row["eligible"]]
    if not eligible:
        raise StrategyAdmissionError("COMPETITION_ELIGIBLE_CANDIDATE_REQUIRED")
    winner = min(
        eligible,
        key=lambda row: (-row["net_score_bps"], row["candidate"]),
    )
    return {
        "method": COMPETITION_METHOD,
        "candidates": canonical_candidates,
        "selected_candidate": winner["candidate"],
        "selected_instrument_id": winner["instrument_id"],
        "selected_net_score_bps": winner["net_score_bps"],
    }


def validate_capital_competition(
    competition: Mapping[str, Any],
    *,
    reviews: Iterable[Mapping[str, Any]],
    cash_outcome: Mapping[str, Any],
    available_evidence_reference_ids: Iterable[str],
) -> None:
    """Require stored competition bytes to equal independent recomputation."""

    if not isinstance(competition, Mapping):
        raise StrategyAdmissionError("CAPITAL_COMPETITION_MAPPING_REQUIRED")
    if set(competition) != {
        "method",
        "candidates",
        "selected_candidate",
        "selected_instrument_id",
        "selected_net_score_bps",
    }:
        raise StrategyAdmissionError("CAPITAL_COMPETITION_KEYS_INVALID")
    if competition.get("method") != COMPETITION_METHOD:
        raise StrategyAdmissionError("CAPITAL_COMPETITION_METHOD_INVALID")
    recomputed = build_capital_competition(
        competition.get("candidates") or [],
        reviews=reviews,
        cash_outcome=cash_outcome,
        available_evidence_reference_ids=available_evidence_reference_ids,
    )
    if canonical_document_bytes(recomputed) != canonical_document_bytes(
        dict(competition)
    ):
        raise StrategyAdmissionError("CAPITAL_COMPETITION_MISMATCH")


def _decision_snapshot_id(payload: Mapping[str, Any]) -> str:
    return "DSN_" + domain_hash(f"{ID_DOMAIN}:DSN:V1", dict(payload))


def build_decision_snapshot(
    *,
    created_at: str,
    portfolio_aim_id: str,
    reviews: Iterable[Mapping[str, Any]],
    cash_outcome: Mapping[str, Any],
    competition_candidates: Iterable[Mapping[str, Any]],
    available_evidence_reference_ids: Iterable[str],
    selected_quantity: Any,
    reference_price: Any,
    fee: Any,
) -> dict[str, Any]:
    """Build the sole authoritative decision snapshot for Strategy Stream 3."""

    evidence_ids = list(available_evidence_reference_ids)
    canonical_reviews, canonical_cash = validate_decision_records(
        reviews,
        cash_outcome,
        available_evidence_reference_ids=evidence_ids,
    )
    competition = build_capital_competition(
        competition_candidates,
        reviews=canonical_reviews,
        cash_outcome=canonical_cash,
        available_evidence_reference_ids=evidence_ids,
    )
    selected = next(
        row
        for row in competition["candidates"]
        if row["candidate"] == competition["selected_candidate"]
    )
    selected_action = "BUY" if selected["outcome"] == "ADMIT" else "CASH"
    payload = {
        "created_at": _require_text(created_at, code="DECISION_CREATED_AT_REQUIRED"),
        "portfolio_aim_id": _require_text(
            portfolio_aim_id, code="PORTFOLIO_AIM_ID_REQUIRED"
        ),
        "reviews": canonical_reviews,
        "cash_outcome": canonical_cash,
        "capital_competition": competition,
        "selected_action": selected_action,
        "selected_instrument_id": competition["selected_instrument_id"],
        "selected_quantity": deepcopy(selected_quantity),
        "reference_price": deepcopy(reference_price),
        "fee": deepcopy(fee),
    }
    return {"decision_snapshot_id": _decision_snapshot_id(payload), **payload}


def validate_decision_snapshot(
    snapshot: Mapping[str, Any], *, available_evidence_reference_ids: Iterable[str]
) -> None:
    """Validate snapshot identity and every independently derivable decision field."""

    if not isinstance(snapshot, Mapping):
        raise StrategyAdmissionError("DECISION_SNAPSHOT_MAPPING_REQUIRED")
    expected_keys = {
        "decision_snapshot_id",
        "created_at",
        "portfolio_aim_id",
        "reviews",
        "cash_outcome",
        "capital_competition",
        "selected_action",
        "selected_instrument_id",
        "selected_quantity",
        "reference_price",
        "fee",
    }
    if set(snapshot) != expected_keys:
        raise StrategyAdmissionError("DECISION_SNAPSHOT_KEYS_INVALID")
    _require_text(snapshot["created_at"], code="DECISION_CREATED_AT_REQUIRED")
    _require_text(snapshot["portfolio_aim_id"], code="PORTFOLIO_AIM_ID_REQUIRED")
    evidence_ids = list(available_evidence_reference_ids)
    canonical_reviews, canonical_cash = validate_decision_records(
        snapshot["reviews"],
        snapshot["cash_outcome"],
        available_evidence_reference_ids=evidence_ids,
    )
    validate_capital_competition(
        snapshot["capital_competition"],
        reviews=canonical_reviews,
        cash_outcome=canonical_cash,
        available_evidence_reference_ids=evidence_ids,
    )
    competition = snapshot["capital_competition"]
    selected = next(
        row
        for row in competition["candidates"]
        if row["candidate"] == competition["selected_candidate"]
    )
    expected_action = "BUY" if selected["outcome"] == "ADMIT" else "CASH"
    if (
        snapshot["selected_action"] != expected_action
        or snapshot["selected_instrument_id"]
        != competition["selected_instrument_id"]
    ):
        raise StrategyAdmissionError("DECISION_SELECTION_MISMATCH")
    payload = {
        key: deepcopy(value)
        for key, value in snapshot.items()
        if key != "decision_snapshot_id"
    }
    if snapshot["decision_snapshot_id"] != _decision_snapshot_id(payload):
        raise StrategyAdmissionError("DECISION_SNAPSHOT_ID_MISMATCH")


def decision_projections(snapshot: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return read-only product projections derived from canonical snapshot truth."""

    return deepcopy(list(snapshot["reviews"])), deepcopy(dict(snapshot["cash_outcome"]))


def validate_decision_projections(
    snapshot: Mapping[str, Any],
    *,
    reviews_projection: Iterable[Mapping[str, Any]],
    cash_projection: Mapping[str, Any],
    available_evidence_reference_ids: Iterable[str],
) -> None:
    """Reject persisted projections that contradict the authoritative snapshot."""

    validate_decision_snapshot(
        snapshot, available_evidence_reference_ids=available_evidence_reference_ids
    )
    expected_reviews, expected_cash = decision_projections(snapshot)
    if canonical_document_bytes(expected_reviews) != canonical_document_bytes(
        list(reviews_projection)
    ):
        raise StrategyAdmissionError("REVIEWS_PROJECTION_MISMATCH")
    if canonical_document_bytes(expected_cash) != canonical_document_bytes(
        dict(cash_projection)
    ):
        raise StrategyAdmissionError("CASH_PROJECTION_MISMATCH")
