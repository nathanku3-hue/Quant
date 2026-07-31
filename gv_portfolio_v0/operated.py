"""One real deterministic ten-instrument operated portfolio product slice.

GV-OPERATED-PORTFOLIO-10-TRANSITION-1R owns one portfolio book across review,
initial funding, a justified no-change observation, one authorized economic
transition, exact replay, correction lineage, and changed-why explanation.
It is paper-only and has no provider, broker, network, alpha, or live-capital
path.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.book import (
    PortfolioBookError,
    build_portfolio_book,
    certification_eligible,
)
from gv_portfolio_v0.execution import (
    ExecutionError,
    emit_trade_chain,
    portfolio_book_event,
    validate_trade_chain,
)
from gv_portfolio_v0.replay import (
    ReplayError,
    append_correction_and_recertify,
    certify_replay_prefix,
    reconstruct_exact,
    replay_idempotent,
)

ID_DOMAIN = "GV-OPERATED-PORTFOLIO-10"
SCHEMA_VERSION = "gv_operated_portfolio_10_transition_1r_v2"
FIXTURE_ID = "GV_OPERATED_PORTFOLIO_10_TRANSITION_1R"
CLAIM_BOUNDARY = (
    "Deterministic operated paper portfolio only; no alpha or live-capital claim."
)
AVAILABLE = "AVAILABLE"
RESEARCH_RESERVE = "RESEARCH_RESERVE"

STATUS_DRAFT = "DRAFT_REVIEW"
STATUS_FUNDED = "FUNDED_CERTIFIED"
STATUS_NO_CHANGE = "OBSERVED_NO_CHANGE_CERTIFIED"
STATUS_TRANSITION = "TRANSITION_CERTIFIED"
STATUS_CORRECTED = "CORRECTED_CERTIFIED"

STATUS_EXPLANATIONS = {
    STATUS_DRAFT: (
        "Ten distinct instruments and one portfolio aim await operator confirmation."
    ),
    STATUS_FUNDED: (
        "The operator confirmed one portfolio; four positions were funded and residual cash remained classified."
    ),
    STATUS_NO_CHANGE: (
        "A later observation was admitted but did not cross a transition threshold, so holdings and cash were preserved."
    ),
    STATUS_TRANSITION: (
        "A later observation weakened Harbor and strengthened Meridian; Harbor was reduced and Meridian was funded."
    ),
    STATUS_CORRECTED: (
        "A non-economic annotation was corrected append-only; portfolio economics and prior certifications remained stable."
    ),
}


class OperatedPortfolioError(ValueError):
    """Fail-closed operated-portfolio error."""


def _identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", dict(payload))


def _record(kind: str, id_key: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    return {id_key: _identifier(kind, body), **body}


def _verify_id(record: Mapping[str, Any], *, kind: str, id_key: str) -> None:
    body = {key: value for key, value in record.items() if key != id_key}
    if record.get(id_key) != _identifier(kind, body):
        raise OperatedPortfolioError(f"IDENTITY_MISMATCH:{id_key}")


def _instrument(
    permanent_key: str,
    symbol: str,
    name: str,
    cluster: str,
) -> dict[str, Any]:
    identity = {
        "namespace": "GV_SYNTHETIC_PERMANENT_V1",
        "permanent_key": permanent_key,
        "security_class": "COMMON_STOCK",
    }
    return {
        "instrument_id": _identifier("INS", identity),
        **identity,
        "symbol": symbol,
        "name": name,
        "economic_cluster": cluster,
    }


def instrument_registry() -> list[dict[str, Any]]:
    """Return exactly ten permanent identities across two economic clusters."""

    return [
        _instrument("ISSUER:NORTHSTAR:COMMON", "NSTAR", "Northstar Systems", "DIGITAL_INFRASTRUCTURE"),
        _instrument("ISSUER:HARBOR:COMMON", "HARBOR", "Harbor Automation", "DIGITAL_INFRASTRUCTURE"),
        _instrument("ISSUER:ORBIT:COMMON", "ORBIT", "Orbit Networks", "DIGITAL_INFRASTRUCTURE"),
        _instrument("ISSUER:QUANTA:COMMON", "QUANTA", "Quanta Compute", "DIGITAL_INFRASTRUCTURE"),
        _instrument("ISSUER:MESH:COMMON", "MESH", "Mesh Security", "DIGITAL_INFRASTRUCTURE"),
        _instrument("ISSUER:ATLAS:COMMON", "ATLAS", "Atlas Logistics", "REAL_ECONOMY"),
        _instrument("ISSUER:VITAL:COMMON", "VITAL", "Vital Diagnostics", "REAL_ECONOMY"),
        _instrument("ISSUER:MERIDIAN:COMMON", "MERID", "Meridian Components", "REAL_ECONOMY"),
        _instrument("ISSUER:FOUNDRY:COMMON", "FNDRY", "Foundry Materials", "REAL_ECONOMY"),
        _instrument("ISSUER:AGRI:COMMON", "AGRI", "Agri Inputs", "REAL_ECONOMY"),
    ]


def _evidence(
    *, content: str, locator: str, observed_at: str
) -> dict[str, Any]:
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    identity = {
        "content_sha256": content_sha256,
        "media_type": "text/plain",
        "locator": locator,
        "observed_at": observed_at,
    }
    return {
        "evidence_reference_id": _identifier("EVD", identity),
        **identity,
        "content": content,
    }


def _initial_evidence() -> list[dict[str, Any]]:
    rows = [
        ("NSTAR", "Recurring platform renewals remain above the principal-thesis floor.", "renewals"),
        ("HARBOR", "Automation backlog supports near-term cash conversion but concentration risk remains.", "backlog"),
        ("ORBIT", "Network bookings improved, but customer concentration evidence is incomplete.", "bookings"),
        ("QUANTA", "Compute demand is strong while power availability constrains the bull case.", "power"),
        ("MESH", "Security growth does not offset a mandate-breaking leverage ratio.", "leverage"),
        ("ATLAS", "Freight utilization and contract repricing support resilient base economics.", "utilization"),
        ("VITAL", "Diagnostic consumables produce stable recurring demand and low balance-sheet risk.", "consumables"),
        ("MERID", "Component qualification is progressing, but the initial order evidence is not yet decisive.", "qualification"),
        ("FNDRY", "Materials spreads normalized and remain below the capital-entry threshold.", "spreads"),
        ("AGRI", "Input-volume recovery is offset by adverse working-capital intensity.", "working-capital"),
    ]
    return [
        _evidence(
            content=content,
            locator=f"fixture://operated-10/{symbol.lower()}/{slug}-v1",
            observed_at=f"2026-07-21T12:{index:02d}:00.000000Z",
        )
        for index, (symbol, content, slug) in enumerate(rows)
    ]


def _no_change_evidence() -> dict[str, Any]:
    return _evidence(
        content="Northstar renewal movement remained inside the declared watch band; no score crossed a funding threshold.",
        locator="fixture://operated-10/nstar/no-change-v1",
        observed_at="2026-08-05T12:00:00.000000Z",
    )


def _transition_evidence() -> dict[str, Any]:
    return _evidence(
        content="Harbor backlog quality weakened below its funding band while Meridian qualification converted into a firm order.",
        locator="fixture://operated-10/harbor-meridian/transition-v1",
        observed_at="2026-08-20T12:00:00.000000Z",
    )


def _initial_reviews(
    instruments: list[dict[str, Any]], evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    specifications = {
        "NSTAR": ("ADMIT", 620, "Renewal durability supports a funded principal position.", "20", "25"),
        "HARBOR": ("ADMIT", 560, "Backlog quality supports a bounded funded position.", "10", "40"),
        "ORBIT": ("ABSTAIN", 300, "Concentration evidence is insufficient for commitment.", "0", "35"),
        "QUANTA": ("ABSTAIN", 250, "Power constraints keep the thesis observable but unfunded.", "0", "60"),
        "MESH": ("REJECT", 180, "Leverage violates the mandate screen.", "0", "20"),
        "ATLAS": ("ADMIT", 540, "Contract repricing supports a funded real-economy position.", "15", "30"),
        "VITAL": ("ADMIT", 520, "Recurring consumables support a funded defensive position.", "12", "50"),
        "MERID": ("ADMIT", 470, "Qualification progress makes Meridian eligible but initially unfunded.", "0", "30"),
        "FNDRY": ("ABSTAIN", 350, "Normalized spreads remain below entry threshold.", "0", "45"),
        "AGRI": ("REJECT", 220, "Working-capital intensity blocks admission.", "0", "25"),
    }
    evidence_by_symbol = {
        instrument["symbol"]: evidence_row
        for instrument, evidence_row in zip(instruments, evidence, strict=True)
    }
    rows: list[dict[str, Any]] = []
    for instrument in instruments:
        outcome, score, thesis, target_quantity, price = specifications[instrument["symbol"]]
        evidence_row = evidence_by_symbol[instrument["symbol"]]
        rows.append(
            {
                "instrument_id": instrument["instrument_id"],
                "symbol": instrument["symbol"],
                "economic_cluster": instrument["economic_cluster"],
                "outcome": outcome,
                "net_score_bps": score,
                "target_quantity": target_quantity,
                "reference_price": price,
                "living_thesis_lite": {
                    "principal_claim": thesis,
                    "evidence_reference_ids": [
                        evidence_row["evidence_reference_id"]
                    ],
                    "hard_falsifiers": [f"{instrument['symbol'].lower()}_hard_falsifier"],
                    "watch_conditions": [f"{instrument['symbol'].lower()}_watch_condition"],
                },
            }
        )
    return rows


def _expected_reviews_for_status(
    *,
    status: str,
    instruments: list[dict[str, Any]],
    initial_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reviews = _initial_reviews(instruments, initial_evidence)
    if status not in {STATUS_TRANSITION, STATUS_CORRECTED}:
        return reviews
    transition_evidence_id = _transition_evidence()["evidence_reference_id"]
    for review in reviews:
        if review["symbol"] == "HARBOR":
            review["net_score_bps"] = 260
            review["target_quantity"] = "6"
            review["living_thesis_lite"]["principal_claim"] = (
                "Backlog quality weakened; retain only a reduced monitoring position."
            )
            review["living_thesis_lite"]["evidence_reference_ids"].append(
                transition_evidence_id
            )
        elif review["symbol"] == "MERID":
            review["net_score_bps"] = 590
            review["target_quantity"] = "5"
            review["living_thesis_lite"]["principal_claim"] = (
                "A firm qualification order now supports bounded funding."
            )
            review["living_thesis_lite"]["evidence_reference_ids"].append(
                transition_evidence_id
            )
    return reviews


def _portfolio_aim() -> dict[str, Any]:
    return _record(
        "AIM",
        "portfolio_aim_id",
        {
            "objective": "Operate one diversified paper portfolio with explicit residual liquidity.",
            "instrument_count": 10,
            "minimum_funded_positions": 3,
            "minimum_total_cash_bps": 1000,
            "allowed_actions": ["BUY", "SELL", "REDUCE", "HOLD", "CASH"],
            "effective_at": "2026-07-22T09:00:00.000000Z",
        },
    )


def _competition_candidates(
    reviews: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "instrument_id": row["instrument_id"],
            "symbol": row["symbol"],
            "economic_cluster": row["economic_cluster"],
            "outcome": row["outcome"],
            "eligible": row["outcome"] == "ADMIT",
            "net_score_bps": row["net_score_bps"],
            "target_quantity": row["target_quantity"],
            "reference_price": row["reference_price"],
        }
        for row in reviews
    ]


def _selected_funded_ids(candidates: Iterable[Mapping[str, Any]]) -> list[str]:
    ranked = sorted(
        (row for row in candidates if row["eligible"]),
        key=lambda row: (-int(row["net_score_bps"]), row["instrument_id"]),
    )
    return [
        str(row["instrument_id"])
        for row in ranked
        if int(row["target_quantity"]) > 0
    ]


def _decision_snapshot(
    *,
    aim_id: str,
    reviews: Iterable[Mapping[str, Any]],
    created_at: str,
    reason: str,
) -> dict[str, Any]:
    candidates = _competition_candidates(reviews)
    payload = {
        "created_at": created_at,
        "portfolio_aim_id": aim_id,
        "decision_reason": reason,
        "capital_competition": {
            "method": "NET_SCORE_DESC_THEN_INSTRUMENT_ID",
            "cash_score_bps": 100,
            "candidates": candidates,
            "selected_funded_instrument_ids": _selected_funded_ids(candidates),
        },
    }
    return _record("DSN", "decision_snapshot_id", payload)


def _event(
    sequence: int,
    event_type: str,
    effective_at: str,
    source_identity: str,
    *,
    instrument_id: str | None = None,
    cash_bucket: str | None = None,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return portfolio_book_event(
            sequence,
            event_type,
            effective_at,
            source_identity,
            instrument_id=instrument_id,
            cash_bucket=cash_bucket,
            payload=payload,
        )
    except ExecutionError as exc:
        raise OperatedPortfolioError(str(exc)) from exc


def _reduce(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    try:
        return build_portfolio_book(events)
    except PortfolioBookError as exc:
        raise OperatedPortfolioError(str(exc)) from exc


def _append_certification(
    workspace: dict[str, Any], *, effective_at: str
) -> None:
    prior = workspace.get("certification")
    if prior is not None:
        workspace["certification_history"] = [
            *workspace["certification_history"],
            deepcopy(prior),
        ]
    try:
        certification = certify_replay_prefix(
            workspace["events"],
            decision_snapshot_id=workspace["current_decision_snapshot"][
                "decision_snapshot_id"
            ],
            portfolio_aim_id=workspace["portfolio_aim"]["portfolio_aim_id"],
            prior_certification=prior,
        )
    except ReplayError as exc:
        raise OperatedPortfolioError(f"CERTIFICATION_FAILED:{exc}") from exc
    workspace["certification"] = certification
    workspace["events"].append(
        _event(
            len(workspace["events"]),
            "CERTIFICATION_RECORDED",
            effective_at,
            certification["certification_id"],
            payload={"certification_id": certification["certification_id"]},
        )
    )
    workspace["book"] = _reduce(workspace["events"])


def build_draft_workspace() -> dict[str, Any]:
    instruments = instrument_registry()
    evidence = _initial_evidence()
    reviews = _initial_reviews(instruments, evidence)
    aim = _portfolio_aim()
    snapshot = _decision_snapshot(
        aim_id=aim["portfolio_aim_id"],
        reviews=reviews,
        created_at="2026-07-22T09:05:00.000000Z",
        reason="INITIAL_CAPITAL_COMPETITION",
    )
    events = [
        _event(
            0,
            "CASH_OPENING",
            "2026-07-22T08:55:00.000000Z",
            "OPERATED10:CASH:AVAILABLE",
            cash_bucket=AVAILABLE,
            payload={"amount": "4500"},
        ),
        _event(
            1,
            "CASH_OPENING",
            "2026-07-22T08:55:00.000000Z",
            "OPERATED10:CASH:RESEARCH_RESERVE",
            cash_bucket=RESEARCH_RESERVE,
            payload={"amount": "500"},
        ),
    ]
    workspace = {
        "schema_version": SCHEMA_VERSION,
        "fixture_id": FIXTURE_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "status": STATUS_DRAFT,
        "explanation": STATUS_EXPLANATIONS[STATUS_DRAFT],
        "portfolio_count": 1,
        "instruments": instruments,
        "evidence_references": evidence,
        "reviews": reviews,
        "portfolio_aim": aim,
        "decision_snapshots": [snapshot],
        "current_decision_snapshot": snapshot,
        "events": events,
        "orders": [],
        "fills": [],
        "trade_authority_chains": [],
        "observations": [],
        "changed_why": None,
        "book": _reduce(events),
        "certification": None,
        "certification_history": [],
        "correction_history": [],
    }
    validate_workspace(workspace, allow_draft=True)
    return workspace


def _append_transition_event(
    workspace: dict[str, Any],
    *,
    transition_kind: str,
    effective_at: str,
    legs: list[dict[str, str]],
) -> dict[str, Any]:
    event = _event(
        len(workspace["events"]),
        "PORTFOLIO_TRANSITION_PLANNED",
        effective_at,
        workspace["current_decision_snapshot"]["decision_snapshot_id"],
        payload={
            "transition_kind": transition_kind,
            "portfolio_aim_id": workspace["portfolio_aim"]["portfolio_aim_id"],
            "legs": legs,
        },
    )
    workspace["events"].append(event)
    return event


def _append_trade(
    workspace: dict[str, Any],
    *,
    transition_event_id: str,
    instrument_id: str,
    side: str,
    quantity: str,
    price: str,
    fee: str,
    order_created_at: str,
    filled_at: str,
) -> None:
    try:
        trade = emit_trade_chain(
            decision_snapshot_id=workspace["current_decision_snapshot"][
                "decision_snapshot_id"
            ],
            portfolio_aim_id=workspace["portfolio_aim"]["portfolio_aim_id"],
            transition_event_id=transition_event_id,
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            reference_price=price,
            expected_fee=fee,
            cash_bucket=AVAILABLE,
            start_sequence=len(workspace["events"]),
            order_created_at=order_created_at,
            filled_at=filled_at,
        )
    except ExecutionError as exc:
        raise OperatedPortfolioError(f"TRADE_EXECUTION_FAILED:{exc}") from exc
    workspace["events"].extend(trade["events"])
    workspace["orders"].append(trade["order"])
    workspace["fills"].append(trade["fill"])
    workspace["trade_authority_chains"].append(trade["authority_chain"])


def confirm_initial_portfolio(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace, allow_draft=True)
    if workspace["status"] != STATUS_DRAFT:
        raise OperatedPortfolioError("DRAFT_CONFIRMATION_REQUIRED")
    result = deepcopy(dict(workspace))
    result["events"].append(
        _event(
            len(result["events"]),
            "PORTFOLIO_AIM_CONFIRMED",
            "2026-07-22T09:05:30.000000Z",
            result["portfolio_aim"]["portfolio_aim_id"],
            payload={
                "decision_snapshot_id": result["current_decision_snapshot"][
                    "decision_snapshot_id"
                ]
            },
        )
    )
    selected_ids = result["current_decision_snapshot"]["capital_competition"][
        "selected_funded_instrument_ids"
    ]
    review_by_id = {row["instrument_id"]: row for row in result["reviews"]}
    if selected_ids != _selected_funded_ids(
        result["current_decision_snapshot"]["capital_competition"]["candidates"]
    ):
        raise OperatedPortfolioError("DECISION_SELECTION_MISMATCH")
    try:
        funded_reviews = [review_by_id[instrument_id] for instrument_id in selected_ids]
    except KeyError as exc:
        raise OperatedPortfolioError("DECISION_SELECTION_UNKNOWN_INSTRUMENT") from exc
    legs = [
        {
            "instrument_id": row["instrument_id"],
            "side": "BUY",
            "quantity": row["target_quantity"],
            "reference_price": row["reference_price"],
        }
        for row in funded_reviews
    ]
    transition = _append_transition_event(
        result,
        transition_kind="INITIAL_FUNDING",
        effective_at="2026-07-22T09:06:00.000000Z",
        legs=legs,
    )
    for index, row in enumerate(funded_reviews):
        minute = 7 + index
        _append_trade(
            result,
            transition_event_id=transition["event_id"],
            instrument_id=row["instrument_id"],
            side="BUY",
            quantity=row["target_quantity"],
            price=row["reference_price"],
            fee="2",
            order_created_at=f"2026-07-22T09:{minute:02d}:00.000000Z",
            filled_at=f"2026-07-22T09:{minute:02d}:01.000000Z",
        )
    result["book"] = _reduce(result["events"])
    result["status"] = STATUS_FUNDED
    result["explanation"] = STATUS_EXPLANATIONS[STATUS_FUNDED]
    result["changed_why"] = {
        "change_type": "INITIAL_FUNDING",
        "reason": "The four highest-scoring eligible instruments received capital; residual cash remained explicit.",
        "funded_symbols": [row["symbol"] for row in funded_reviews],
        "position_count_after": 4,
        "cash_after": result["book"]["total_cash"],
        "costs_after": result["book"]["total_costs"],
    }
    _append_certification(result, effective_at="2026-07-22T09:12:00.000000Z")
    validate_workspace(result)
    return result


def admit_no_change_observation(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] != STATUS_FUNDED:
        raise OperatedPortfolioError("FUNDED_WORKSPACE_REQUIRED")
    result = deepcopy(dict(workspace))
    prior_book = canonical_document_bytes(result["book"])
    observation = _no_change_evidence()
    result["evidence_references"].append(observation)
    observation_record = _record(
        "OBS",
        "observation_id",
        {
            "evidence_reference_id": observation["evidence_reference_id"],
            "disposition": "AIM_UNCHANGED_NO_TRANSITION",
            "instrument_id": result["instruments"][0]["instrument_id"],
            "threshold_crossed": False,
            "observed_at": observation["observed_at"],
        },
    )
    result["observations"].append(observation_record)
    result["events"].append(
        _event(
            len(result["events"]),
            "LATER_OBSERVATION_ADMITTED",
            observation["observed_at"],
            observation_record["observation_id"],
            instrument_id=observation_record["instrument_id"],
            payload=dict(observation_record),
        )
    )
    result["book"] = _reduce(result["events"])
    if canonical_document_bytes(result["book"]) != prior_book:
        raise OperatedPortfolioError("NO_CHANGE_OBSERVATION_CHANGED_BOOK")
    result["status"] = STATUS_NO_CHANGE
    result["explanation"] = STATUS_EXPLANATIONS[STATUS_NO_CHANGE]
    result["changed_why"] = {
        "change_type": "NO_CHANGE",
        "reason": "The observation stayed inside the watch band; no hard falsifier or funding threshold fired.",
        "holdings_changed": False,
        "cash_changed": False,
        "orders_created": 0,
    }
    _append_certification(result, effective_at="2026-08-05T12:01:00.000000Z")
    validate_workspace(result)
    return result


def authorize_portfolio_transition(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] != STATUS_NO_CHANGE:
        raise OperatedPortfolioError("NO_CHANGE_OBSERVATION_REQUIRED_BEFORE_TRANSITION")
    result = deepcopy(dict(workspace))
    by_symbol = {row["symbol"]: row for row in result["instruments"]}
    observation = _transition_evidence()
    result["evidence_references"].append(observation)

    updated_reviews = deepcopy(result["reviews"])
    before_scores: dict[str, int] = {}
    after_scores: dict[str, int] = {}
    for review in updated_reviews:
        symbol = review["symbol"]
        before_scores[symbol] = int(review["net_score_bps"])
        if symbol == "HARBOR":
            review["net_score_bps"] = 260
            review["target_quantity"] = "6"
            review["living_thesis_lite"]["principal_claim"] = (
                "Backlog quality weakened; retain only a reduced monitoring position."
            )
            review["living_thesis_lite"]["evidence_reference_ids"].append(
                observation["evidence_reference_id"]
            )
        elif symbol == "MERID":
            review["net_score_bps"] = 590
            review["target_quantity"] = "5"
            review["living_thesis_lite"]["principal_claim"] = (
                "A firm qualification order now supports bounded funding."
            )
            review["living_thesis_lite"]["evidence_reference_ids"].append(
                observation["evidence_reference_id"]
            )
        after_scores[symbol] = int(review["net_score_bps"])
    result["reviews"] = updated_reviews
    transition_snapshot = _decision_snapshot(
        aim_id=result["portfolio_aim"]["portfolio_aim_id"],
        reviews=updated_reviews,
        created_at="2026-08-20T12:01:00.000000Z",
        reason="AUTHORIZED_HARBOR_TO_MERIDIAN_TRANSITION",
    )
    result["decision_snapshots"].append(transition_snapshot)
    result["current_decision_snapshot"] = transition_snapshot
    observation_record = _record(
        "OBS",
        "observation_id",
        {
            "evidence_reference_id": observation["evidence_reference_id"],
            "disposition": "AUTHORIZED_TRANSITION",
            "instrument_ids": [
                by_symbol["HARBOR"]["instrument_id"],
                by_symbol["MERID"]["instrument_id"],
            ],
            "threshold_crossed": True,
            "observed_at": observation["observed_at"],
            "decision_snapshot_id": transition_snapshot["decision_snapshot_id"],
        },
    )
    result["observations"].append(observation_record)
    result["events"].append(
        _event(
            len(result["events"]),
            "LATER_OBSERVATION_ADMITTED",
            observation["observed_at"],
            observation_record["observation_id"],
            payload=dict(observation_record),
        )
    )
    legs = [
        {
            "instrument_id": by_symbol["HARBOR"]["instrument_id"],
            "side": "SELL",
            "quantity": "4",
            "reference_price": "40",
        },
        {
            "instrument_id": by_symbol["MERID"]["instrument_id"],
            "side": "BUY",
            "quantity": "5",
            "reference_price": "30",
        },
    ]
    transition = _append_transition_event(
        result,
        transition_kind="REDUCE_AND_FUND",
        effective_at="2026-08-20T12:02:00.000000Z",
        legs=legs,
    )
    _append_trade(
        result,
        transition_event_id=transition["event_id"],
        instrument_id=by_symbol["HARBOR"]["instrument_id"],
        side="SELL",
        quantity="4",
        price="40",
        fee="2",
        order_created_at="2026-08-20T12:03:00.000000Z",
        filled_at="2026-08-20T12:03:01.000000Z",
    )
    _append_trade(
        result,
        transition_event_id=transition["event_id"],
        instrument_id=by_symbol["MERID"]["instrument_id"],
        side="BUY",
        quantity="5",
        price="30",
        fee="2",
        order_created_at="2026-08-20T12:04:00.000000Z",
        filled_at="2026-08-20T12:04:01.000000Z",
    )
    result["book"] = _reduce(result["events"])
    result["status"] = STATUS_TRANSITION
    result["explanation"] = STATUS_EXPLANATIONS[STATUS_TRANSITION]
    result["changed_why"] = {
        "change_type": "AUTHORIZED_TRANSITION",
        "reason": "Harbor fell below its prior funding band while Meridian moved above the incremental-capital threshold.",
        "reduced": {
            "symbol": "HARBOR",
            "quantity_before": "10",
            "quantity_after": "6",
            "score_before_bps": before_scores["HARBOR"],
            "score_after_bps": after_scores["HARBOR"],
        },
        "funded_or_increased": {
            "symbol": "MERID",
            "quantity_before": "0",
            "quantity_after": "5",
            "score_before_bps": before_scores["MERID"],
            "score_after_bps": after_scores["MERID"],
        },
        "cash_after": result["book"]["total_cash"],
        "total_costs_after": result["book"]["total_costs"],
        "unexplained_residual": result["book"]["unexplained_residual"],
    }
    _append_certification(result, effective_at="2026-08-20T12:05:00.000000Z")
    validate_workspace(result)
    return result


def append_non_economic_correction(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] not in {STATUS_TRANSITION, STATUS_CORRECTED}:
        raise OperatedPortfolioError("TRANSITION_CERTIFICATION_REQUIRED")
    if workspace["status"] == STATUS_CORRECTED:
        return deepcopy(dict(workspace))
    result = deepcopy(dict(workspace))
    prior = deepcopy(result["certification"])
    try:
        corrected = append_correction_and_recertify(
            result["events"],
            prior_certification=prior,
            correction_payload={
                "correction_kind": "ANNOTATION",
                "reason": "Clarify that Meridian evidence is a firm qualification order, not a shipment.",
                "details": {"economic_effect": "NONE"},
            },
            decision_snapshot_id=result["current_decision_snapshot"][
                "decision_snapshot_id"
            ],
            portfolio_aim_id=result["portfolio_aim"]["portfolio_aim_id"],
            effective_at="2026-08-20T12:06:00.000000Z",
            source_identity="OPERATED10:CORRECTION:MERIDIAN-ANNOTATION",
        )
    except ReplayError as exc:
        raise OperatedPortfolioError(f"CORRECTION_FAILED:{exc}") from exc
    result["certification_history"] = [
        *result["certification_history"],
        prior,
    ]
    result["events"] = corrected["events"]
    result["book"] = corrected["book"]
    result["certification"] = corrected["certification"]
    correction_event = result["events"][-1]
    result["correction_history"] = [
        *result["correction_history"],
        {
            "event_id": correction_event["event_id"],
            "prior_certification_id": prior["certification_id"],
            "certification_id": result["certification"]["certification_id"],
            "economic_effect": "NONE",
        },
    ]
    result["events"].append(
        _event(
            len(result["events"]),
            "CERTIFICATION_RECORDED",
            "2026-08-20T12:07:00.000000Z",
            result["certification"]["certification_id"],
            payload={
                "certification_id": result["certification"]["certification_id"]
            },
        )
    )
    result["book"] = _reduce(result["events"])
    result["status"] = STATUS_CORRECTED
    result["explanation"] = STATUS_EXPLANATIONS[STATUS_CORRECTED]
    validate_workspace(result)
    return result


def _funded_positions(book: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [row for row in book["positions"] if int(row["quantity"]) > 0]


def _initial_review_state(
    instruments: list[dict[str, Any]], initial_evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return _initial_reviews(instruments, initial_evidence)


def _expected_snapshots(
    *,
    status: str,
    aim_id: str,
    instruments: list[dict[str, Any]],
    initial_evidence: list[dict[str, Any]],
    current_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    initial_reviews = _initial_review_state(instruments, initial_evidence)
    snapshots = [
        _decision_snapshot(
            aim_id=aim_id,
            reviews=initial_reviews,
            created_at="2026-07-22T09:05:00.000000Z",
            reason="INITIAL_CAPITAL_COMPETITION",
        )
    ]
    if status in {STATUS_TRANSITION, STATUS_CORRECTED}:
        snapshots.append(
            _decision_snapshot(
                aim_id=aim_id,
                reviews=current_reviews,
                created_at="2026-08-20T12:01:00.000000Z",
                reason="AUTHORIZED_HARBOR_TO_MERIDIAN_TRANSITION",
            )
        )
    return snapshots


def _expected_transition_legs(
    *,
    status: str,
    instruments: list[dict[str, Any]],
    initial_reviews: list[dict[str, Any]],
    current_reviews: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> list[tuple[str, str, list[dict[str, str]]]]:
    if status == STATUS_DRAFT:
        return []
    initial_by_id = {row["instrument_id"]: row for row in initial_reviews}
    selected_ids = snapshots[0]["capital_competition"][
        "selected_funded_instrument_ids"
    ]
    initial_legs = [
        {
            "instrument_id": instrument_id,
            "side": "BUY",
            "quantity": initial_by_id[instrument_id]["target_quantity"],
            "reference_price": initial_by_id[instrument_id]["reference_price"],
        }
        for instrument_id in selected_ids
    ]
    expected = [
        (
            "INITIAL_FUNDING",
            snapshots[0]["decision_snapshot_id"],
            initial_legs,
        )
    ]
    if status in {STATUS_TRANSITION, STATUS_CORRECTED}:
        current_by_id = {row["instrument_id"]: row for row in current_reviews}
        rebalance_legs: list[dict[str, str]] = []
        for instrument in instruments:
            instrument_id = instrument["instrument_id"]
            before = int(initial_by_id[instrument_id]["target_quantity"])
            after = int(current_by_id[instrument_id]["target_quantity"])
            delta = after - before
            if delta == 0:
                continue
            rebalance_legs.append(
                {
                    "instrument_id": instrument_id,
                    "side": "BUY" if delta > 0 else "SELL",
                    "quantity": str(abs(delta)),
                    "reference_price": current_by_id[instrument_id][
                        "reference_price"
                    ],
                }
            )
        expected.append(
            (
                "REDUCE_AND_FUND",
                snapshots[-1]["decision_snapshot_id"],
                rebalance_legs,
            )
        )
    return expected


def _execution_projections(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    order_events = [row for row in events if row["event_type"] == "ORDER_CREATED"]
    fill_events = [row for row in events if row["event_type"] == "FILL_COMPLETED"]
    if len(order_events) != len(fill_events):
        raise OperatedPortfolioError("ORDER_FILL_EVENT_COUNT_MISMATCH")
    orders: list[dict[str, Any]] = []
    fills: list[dict[str, Any]] = []
    chains: list[dict[str, Any]] = []
    for order_event, fill_event in zip(order_events, fill_events, strict=True):
        order = order_event.get("payload", {}).get("order")
        fill = fill_event.get("payload", {}).get("fill")
        if not isinstance(order, Mapping) or not isinstance(fill, Mapping):
            raise OperatedPortfolioError("TRADE_EVENT_PROJECTION_REQUIRED")
        try:
            chain = validate_trade_chain(order, order_event, fill, fill_event)
        except ExecutionError as exc:
            raise OperatedPortfolioError(f"TRADE_AUTHORITY_CHAIN_INVALID:{exc}") from exc
        orders.append(dict(order))
        fills.append(dict(fill))
        chains.append(chain)
    return orders, fills, chains


def _expected_changed_why(
    *,
    status: str,
    book: Mapping[str, Any],
    instruments: list[dict[str, Any]],
    initial_reviews: list[dict[str, Any]],
    current_reviews: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if status == STATUS_DRAFT:
        return None
    initial_by_id = {row["instrument_id"]: row for row in initial_reviews}
    symbol_by_id = {row["instrument_id"]: row["symbol"] for row in instruments}
    if status == STATUS_FUNDED:
        selected_ids = snapshots[0]["capital_competition"][
            "selected_funded_instrument_ids"
        ]
        return {
            "change_type": "INITIAL_FUNDING",
            "reason": "The four highest-scoring eligible instruments received capital; residual cash remained explicit.",
            "funded_symbols": [symbol_by_id[row] for row in selected_ids],
            "position_count_after": len(_funded_positions(book)),
            "cash_after": book["total_cash"],
            "costs_after": book["total_costs"],
        }
    if status == STATUS_NO_CHANGE:
        return {
            "change_type": "NO_CHANGE",
            "reason": "The observation stayed inside the watch band; no hard falsifier or funding threshold fired.",
            "holdings_changed": False,
            "cash_changed": False,
            "orders_created": 0,
        }
    current_by_id = {row["instrument_id"]: row for row in current_reviews}
    by_symbol = {row["symbol"]: row["instrument_id"] for row in instruments}
    harbor_id = by_symbol["HARBOR"]
    meridian_id = by_symbol["MERID"]
    return {
        "change_type": "AUTHORIZED_TRANSITION",
        "reason": "Harbor fell below its prior funding band while Meridian moved above the incremental-capital threshold.",
        "reduced": {
            "symbol": "HARBOR",
            "quantity_before": initial_by_id[harbor_id]["target_quantity"],
            "quantity_after": current_by_id[harbor_id]["target_quantity"],
            "score_before_bps": int(initial_by_id[harbor_id]["net_score_bps"]),
            "score_after_bps": int(current_by_id[harbor_id]["net_score_bps"]),
        },
        "funded_or_increased": {
            "symbol": "MERID",
            "quantity_before": initial_by_id[meridian_id]["target_quantity"],
            "quantity_after": current_by_id[meridian_id]["target_quantity"],
            "score_before_bps": int(initial_by_id[meridian_id]["net_score_bps"]),
            "score_after_bps": int(current_by_id[meridian_id]["net_score_bps"]),
        },
        "cash_after": book["total_cash"],
        "total_costs_after": book["total_costs"],
        "unexplained_residual": book["unexplained_residual"],
    }


def _validate_certification_lineage(
    *,
    events: list[dict[str, Any]],
    history: list[dict[str, Any]],
    certification: Mapping[str, Any],
    aim_id: str,
    snapshot_ids: set[str],
) -> None:
    certification_events = [
        event for event in events if event["event_type"] == "CERTIFICATION_RECORDED"
    ]
    lineage = [*history, dict(certification)]
    if len(certification_events) != len(lineage):
        raise OperatedPortfolioError("CERTIFICATION_LINEAGE_COUNT_MISMATCH")
    prior: dict[str, Any] | None = None
    for marker, record in zip(certification_events, lineage, strict=True):
        if record.get("portfolio_aim_id") != aim_id:
            raise OperatedPortfolioError("CERTIFICATION_AIM_MISMATCH")
        if record.get("decision_snapshot_id") not in snapshot_ids:
            raise OperatedPortfolioError("CERTIFICATION_DECISION_MISMATCH")
        expected_prior_id = None if prior is None else prior["certification_id"]
        if record.get("prior_certification_id") != expected_prior_id:
            raise OperatedPortfolioError("CERTIFICATION_PRIOR_LINK_MISMATCH")
        if marker.get("source_identity") != record.get("certification_id"):
            raise OperatedPortfolioError("CERTIFICATION_EVENT_SOURCE_MISMATCH")
        if marker.get("payload") != {
            "certification_id": record.get("certification_id")
        }:
            raise OperatedPortfolioError("CERTIFICATION_EVENT_PAYLOAD_MISMATCH")
        prefix = events[: marker["sequence"]]
        try:
            expected = certify_replay_prefix(
                prefix,
                decision_snapshot_id=record["decision_snapshot_id"],
                portfolio_aim_id=aim_id,
                prior_certification=prior,
            )
        except ReplayError as exc:
            raise OperatedPortfolioError(
                f"CERTIFICATION_HISTORY_REPLAY_FAILED:{exc}"
            ) from exc
        if canonical_document_bytes(expected) != canonical_document_bytes(record):
            raise OperatedPortfolioError("CERTIFICATION_HISTORY_OBJECT_MISMATCH")
        prior = record


def validate_workspace(
    workspace: Mapping[str, Any], *, allow_draft: bool = False
) -> None:
    if workspace.get("schema_version") != SCHEMA_VERSION:
        raise OperatedPortfolioError("WORKSPACE_SCHEMA_INVALID")
    if workspace.get("fixture_id") != FIXTURE_ID:
        raise OperatedPortfolioError("WORKSPACE_FIXTURE_ID_INVALID")
    if workspace.get("claim_boundary") != CLAIM_BOUNDARY:
        raise OperatedPortfolioError("WORKSPACE_CLAIM_BOUNDARY_INVALID")
    if workspace.get("portfolio_count") != 1:
        raise OperatedPortfolioError("EXACTLY_ONE_PORTFOLIO_REQUIRED")
    status = workspace.get("status")
    if status not in STATUS_EXPLANATIONS:
        raise OperatedPortfolioError("WORKSPACE_STATUS_INVALID")
    if workspace.get("explanation") != STATUS_EXPLANATIONS[status]:
        raise OperatedPortfolioError("WORKSPACE_EXPLANATION_INVALID")

    instruments = list(workspace.get("instruments") or [])
    if len(instruments) != 10:
        raise OperatedPortfolioError("EXACTLY_TEN_INSTRUMENTS_REQUIRED")
    if canonical_document_bytes(instruments) != canonical_document_bytes(
        instrument_registry()
    ):
        raise OperatedPortfolioError("INSTRUMENT_REGISTRY_MISMATCH")
    instrument_ids = [row["instrument_id"] for row in instruments]
    permanent_keys = [row["permanent_key"] for row in instruments]
    if len(set(instrument_ids)) != 10 or len(set(permanent_keys)) != 10:
        raise OperatedPortfolioError("PERMANENT_IDENTITY_DUPLICATE")
    if len({row["economic_cluster"] for row in instruments}) < 2:
        raise OperatedPortfolioError("TWO_ECONOMIC_CLUSTERS_REQUIRED")
    for row in instruments:
        identity = {
            "namespace": row["namespace"],
            "permanent_key": row["permanent_key"],
            "security_class": row["security_class"],
        }
        if row["instrument_id"] != _identifier("INS", identity):
            raise OperatedPortfolioError("INSTRUMENT_ID_MISMATCH")

    evidence = list(workspace.get("evidence_references") or [])
    for row in evidence:
        raw_hash = hashlib.sha256(row["content"].encode("utf-8")).hexdigest()
        if raw_hash != row["content_sha256"]:
            raise OperatedPortfolioError("EVIDENCE_CONTENT_HASH_MISMATCH")
        identity = {
            "content_sha256": row["content_sha256"],
            "media_type": row["media_type"],
            "locator": row["locator"],
            "observed_at": row["observed_at"],
        }
        if row["evidence_reference_id"] != _identifier("EVD", identity):
            raise OperatedPortfolioError("EVIDENCE_ID_MISMATCH")
    initial_evidence = evidence[:10]
    if len(initial_evidence) != 10:
        raise OperatedPortfolioError("INSTRUMENT_SPECIFIC_EVIDENCE_REQUIRED")
    if canonical_document_bytes(initial_evidence) != canonical_document_bytes(
        _initial_evidence()
    ):
        raise OperatedPortfolioError("INITIAL_EVIDENCE_REGISTRY_MISMATCH")
    if len({row["content_sha256"] for row in initial_evidence}) != 10:
        raise OperatedPortfolioError("COPIED_EVIDENCE_PROHIBITED")
    expected_evidence = [*initial_evidence]
    if status in {STATUS_NO_CHANGE, STATUS_TRANSITION, STATUS_CORRECTED}:
        expected_evidence.append(_no_change_evidence())
    if status in {STATUS_TRANSITION, STATUS_CORRECTED}:
        expected_evidence.append(_transition_evidence())
    if canonical_document_bytes(evidence) != canonical_document_bytes(
        expected_evidence
    ):
        raise OperatedPortfolioError("EVIDENCE_LINEAGE_MISMATCH")

    reviews = list(workspace.get("reviews") or [])
    if len(reviews) != 10:
        raise OperatedPortfolioError("TEN_REVIEWS_REQUIRED")
    if {row["instrument_id"] for row in reviews} != set(instrument_ids):
        raise OperatedPortfolioError("REVIEW_INSTRUMENT_COVERAGE_MISMATCH")
    claims = [row["living_thesis_lite"]["principal_claim"] for row in reviews]
    if len(set(claims)) != 10:
        raise OperatedPortfolioError("COPIED_THESIS_PROHIBITED")
    evidence_ids = {row["evidence_reference_id"] for row in evidence}
    initial_evidence_ids = {
        row["evidence_reference_id"] for row in initial_evidence
    }
    owned_initial_evidence = {
        instrument["instrument_id"]: evidence_row["evidence_reference_id"]
        for instrument, evidence_row in zip(
            instruments, initial_evidence, strict=True
        )
    }
    for review in reviews:
        refs = review["living_thesis_lite"]["evidence_reference_ids"]
        if (
            not refs
            or len(refs) != len(set(refs))
            or any(ref not in evidence_ids for ref in refs)
        ):
            raise OperatedPortfolioError("THESIS_EVIDENCE_BINDING_INVALID")
        owner_ref = owned_initial_evidence[review["instrument_id"]]
        if owner_ref not in refs:
            raise OperatedPortfolioError("THESIS_INSTRUMENT_EVIDENCE_OWNER_MISMATCH")
        if any(ref in initial_evidence_ids and ref != owner_ref for ref in refs):
            raise OperatedPortfolioError("THESIS_CROSS_INSTRUMENT_EVIDENCE_PROHIBITED")
    expected_reviews = _expected_reviews_for_status(
        status=status,
        instruments=instruments,
        initial_evidence=initial_evidence,
    )
    if canonical_document_bytes(reviews) != canonical_document_bytes(
        expected_reviews
    ):
        raise OperatedPortfolioError("REVIEW_DECISION_STATE_MISMATCH")

    _verify_id(workspace["portfolio_aim"], kind="AIM", id_key="portfolio_aim_id")
    aim_id = workspace["portfolio_aim"]["portfolio_aim_id"]
    snapshots = list(workspace.get("decision_snapshots") or [])
    expected_snapshots = _expected_snapshots(
        status=status,
        aim_id=aim_id,
        instruments=instruments,
        initial_evidence=initial_evidence,
        current_reviews=reviews,
    )
    if canonical_document_bytes(snapshots) != canonical_document_bytes(
        expected_snapshots
    ):
        raise OperatedPortfolioError("DECISION_SNAPSHOT_AUTHORITY_MISMATCH")
    for snapshot in snapshots:
        _verify_id(snapshot, kind="DSN", id_key="decision_snapshot_id")
        candidates = snapshot["capital_competition"]["candidates"]
        if len(candidates) != 10:
            raise OperatedPortfolioError("CAPITAL_COMPETITION_TEN_REQUIRED")
        if {row["instrument_id"] for row in candidates} != set(instrument_ids):
            raise OperatedPortfolioError("CAPITAL_COMPETITION_COVERAGE_MISMATCH")
        selected = snapshot["capital_competition"][
            "selected_funded_instrument_ids"
        ]
        if selected != _selected_funded_ids(candidates):
            raise OperatedPortfolioError("DECISION_SELECTION_MISMATCH")
    current_snapshot = workspace.get("current_decision_snapshot")
    if not isinstance(current_snapshot, Mapping):
        raise OperatedPortfolioError("CURRENT_DECISION_SNAPSHOT_REQUIRED")
    if canonical_document_bytes(current_snapshot) != canonical_document_bytes(
        snapshots[-1]
    ):
        raise OperatedPortfolioError("CURRENT_DECISION_SNAPSHOT_MISMATCH")

    events = [dict(row) for row in workspace.get("events") or []]
    if [row.get("sequence") for row in events] != list(range(len(events))):
        raise OperatedPortfolioError("EVENT_SEQUENCE_NOT_CONTIGUOUS")
    for event in events:
        body = {key: value for key, value in event.items() if key != "event_id"}
        expected = "EVT_" + domain_hash("GV-PORTFOLIO-V0:EVT:V1", body)
        if event.get("event_id") != expected:
            raise OperatedPortfolioError("EVENT_ID_MISMATCH")

    aim_events = [
        event for event in events if event["event_type"] == "PORTFOLIO_AIM_CONFIRMED"
    ]
    expected_aim_event_count = 0 if status == STATUS_DRAFT else 1
    if len(aim_events) != expected_aim_event_count:
        raise OperatedPortfolioError("PORTFOLIO_AIM_CONFIRMATION_COUNT_MISMATCH")
    if aim_events:
        if aim_events[0].get("source_identity") != aim_id:
            raise OperatedPortfolioError("PORTFOLIO_AIM_CONFIRMATION_SOURCE_MISMATCH")
        if aim_events[0].get("payload") != {
            "decision_snapshot_id": snapshots[0]["decision_snapshot_id"]
        }:
            raise OperatedPortfolioError("PORTFOLIO_AIM_CONFIRMATION_DECISION_MISMATCH")

    observation_events = [
        event for event in events if event["event_type"] == "LATER_OBSERVATION_ADMITTED"
    ]
    expected_observation_count = {
        STATUS_DRAFT: 0,
        STATUS_FUNDED: 0,
        STATUS_NO_CHANGE: 1,
        STATUS_TRANSITION: 2,
        STATUS_CORRECTED: 2,
    }[status]
    if len(observation_events) != expected_observation_count:
        raise OperatedPortfolioError("OBSERVATION_COUNT_MISMATCH")
    projected_observations: list[dict[str, Any]] = []
    evidence_by_id = {
        row["evidence_reference_id"]: row for row in evidence
    }
    for observation_event in observation_events:
        observation = observation_event.get("payload")
        if not isinstance(observation, Mapping):
            raise OperatedPortfolioError("OBSERVATION_EVENT_PAYLOAD_REQUIRED")
        _verify_id(observation, kind="OBS", id_key="observation_id")
        if observation_event.get("source_identity") != observation["observation_id"]:
            raise OperatedPortfolioError("OBSERVATION_EVENT_SOURCE_MISMATCH")
        evidence_row = evidence_by_id.get(observation["evidence_reference_id"])
        if evidence_row is None:
            raise OperatedPortfolioError("OBSERVATION_EVIDENCE_MISSING")
        if observation.get("observed_at") != evidence_row["observed_at"]:
            raise OperatedPortfolioError("OBSERVATION_EVIDENCE_TIMESTAMP_MISMATCH")
        projected_observations.append(dict(observation))
    if canonical_document_bytes(workspace.get("observations") or []) != canonical_document_bytes(
        projected_observations
    ):
        raise OperatedPortfolioError("OBSERVATION_PROJECTION_MISMATCH")

    book = _reduce(events)
    if canonical_document_bytes(book) != canonical_document_bytes(workspace["book"]):
        raise OperatedPortfolioError("BOOK_REDUCTION_MISMATCH")
    try:
        reconstruct_exact(events, expected_book=workspace["book"])
        idempotent = replay_idempotent(events)
    except ReplayError as exc:
        raise OperatedPortfolioError(f"REPLAY_FAILED:{exc}") from exc
    if idempotent["book_hash"] != workspace["book"]["book_hash"]:
        raise OperatedPortfolioError("REPLAY_IDEMPOTENCE_MISMATCH")

    projected_orders, projected_fills, projected_chains = _execution_projections(
        events
    )
    orders = list(workspace.get("orders") or [])
    fills = list(workspace.get("fills") or [])
    authority_chains = list(workspace.get("trade_authority_chains") or [])
    if canonical_document_bytes(orders) != canonical_document_bytes(
        projected_orders
    ):
        raise OperatedPortfolioError("ORDER_PROJECTION_MISMATCH")
    if canonical_document_bytes(fills) != canonical_document_bytes(projected_fills):
        raise OperatedPortfolioError("FILL_PROJECTION_MISMATCH")
    if canonical_document_bytes(authority_chains) != canonical_document_bytes(
        projected_chains
    ):
        raise OperatedPortfolioError("TRADE_AUTHORITY_CHAIN_PROJECTION_MISMATCH")

    initial_reviews = _initial_review_state(instruments, initial_evidence)
    expected_transitions = _expected_transition_legs(
        status=status,
        instruments=instruments,
        initial_reviews=initial_reviews,
        current_reviews=reviews,
        snapshots=snapshots,
    )
    transition_events = [
        event
        for event in events
        if event["event_type"] == "PORTFOLIO_TRANSITION_PLANNED"
    ]
    if len(transition_events) != len(expected_transitions):
        raise OperatedPortfolioError("TRANSITION_EVENT_COUNT_MISMATCH")
    known_transition_ids: set[str] = set()
    for transition_event, expected_transition in zip(
        transition_events, expected_transitions, strict=True
    ):
        transition_kind, decision_snapshot_id, expected_legs = expected_transition
        expected_payload = {
            "transition_kind": transition_kind,
            "portfolio_aim_id": aim_id,
            "legs": expected_legs,
        }
        if transition_event.get("source_identity") != decision_snapshot_id:
            raise OperatedPortfolioError("TRANSITION_DECISION_AUTHORITY_MISMATCH")
        if canonical_document_bytes(transition_event.get("payload", {})) != canonical_document_bytes(
            expected_payload
        ):
            raise OperatedPortfolioError("TRANSITION_LEGS_MISMATCH")
        known_transition_ids.add(transition_event["event_id"])
        transition_orders = [
            order
            for order in projected_orders
            if order["transition_event_id"] == transition_event["event_id"]
        ]
        order_legs = [
            {
                "instrument_id": order["instrument_id"],
                "side": order["side"],
                "quantity": order["quantity"],
                "reference_price": order["reference_price"],
            }
            for order in transition_orders
        ]
        if canonical_document_bytes(order_legs) != canonical_document_bytes(
            expected_legs
        ):
            raise OperatedPortfolioError("TRANSITION_EXECUTION_DELTA_MISMATCH")
        for order in transition_orders:
            if order["decision_snapshot_id"] != decision_snapshot_id:
                raise OperatedPortfolioError("ORDER_DECISION_AUTHORITY_MISMATCH")
            if order["portfolio_aim_id"] != aim_id:
                raise OperatedPortfolioError("ORDER_AIM_AUTHORITY_MISMATCH")
    if any(
        order["transition_event_id"] not in known_transition_ids
        for order in projected_orders
    ):
        raise OperatedPortfolioError("ORDER_TRANSITION_AUTHORITY_MISSING")

    expected_changed_why = _expected_changed_why(
        status=status,
        book=workspace["book"],
        instruments=instruments,
        initial_reviews=initial_reviews,
        current_reviews=reviews,
        snapshots=snapshots,
    )
    if canonical_document_bytes(workspace.get("changed_why")) != canonical_document_bytes(
        expected_changed_why
    ):
        raise OperatedPortfolioError("CHANGED_WHY_PROJECTION_MISMATCH")

    if status == STATUS_DRAFT:
        if not allow_draft:
            raise OperatedPortfolioError("UNCERTIFIED_DRAFT")
        if orders or fills or workspace.get("certification") is not None:
            raise OperatedPortfolioError("DRAFT_HAS_EXECUTION_OR_CERTIFICATION")
        if workspace["book"]["nav"] != "5000":
            raise OperatedPortfolioError("DRAFT_NAV_INVALID")
        return

    if not certification_eligible(workspace["book"]):
        raise OperatedPortfolioError("BOOK_NOT_CERTIFICATION_ELIGIBLE")
    if workspace["book"]["unexplained_residual"] != "0":
        raise OperatedPortfolioError("UNEXPLAINED_RESIDUAL_NONZERO")
    if len(_funded_positions(workspace["book"])) < 3:
        raise OperatedPortfolioError("THREE_FUNDED_POSITIONS_REQUIRED")
    cash_buckets = {row["bucket"] for row in workspace["book"]["classified_cash"]}
    if {AVAILABLE, RESEARCH_RESERVE} - cash_buckets:
        raise OperatedPortfolioError("CLASSIFIED_RESIDUAL_CASH_REQUIRED")

    certification = workspace.get("certification")
    if not isinstance(certification, Mapping):
        raise OperatedPortfolioError("CERTIFICATION_REQUIRED")
    certification_history = list(workspace.get("certification_history") or [])
    if any(not isinstance(row, Mapping) for row in certification_history):
        raise OperatedPortfolioError("CERTIFICATION_HISTORY_OBJECT_REQUIRED")
    _validate_certification_lineage(
        events=events,
        history=[dict(row) for row in certification_history],
        certification=certification,
        aim_id=aim_id,
        snapshot_ids={row["decision_snapshot_id"] for row in snapshots},
    )
    correction_events = [
        event for event in events if event["event_type"] == "CORRECTION_RECORDED"
    ]
    correction_history = list(workspace.get("correction_history") or [])
    if status == STATUS_CORRECTED:
        if len(correction_events) != 1 or len(correction_history) != 1:
            raise OperatedPortfolioError("CORRECTION_LINEAGE_REQUIRED")
        if not certification_history:
            raise OperatedPortfolioError("CORRECTION_PRIOR_CERTIFICATION_REQUIRED")
        correction_event = correction_events[0]
        prior_certification = certification_history[-1]
        expected_correction = {
            "event_id": correction_event["event_id"],
            "prior_certification_id": prior_certification["certification_id"],
            "certification_id": certification["certification_id"],
            "economic_effect": "NONE",
        }
        if correction_event.get("payload", {}).get(
            "prior_certification_id"
        ) != prior_certification["certification_id"]:
            raise OperatedPortfolioError("CORRECTION_PRIOR_LINK_MISMATCH")
        if canonical_document_bytes(correction_history) != canonical_document_bytes(
            [expected_correction]
        ):
            raise OperatedPortfolioError("CORRECTION_HISTORY_PROJECTION_MISMATCH")
    elif correction_events or correction_history:
        raise OperatedPortfolioError("CORRECTION_BEFORE_CORRECTED_STATUS")

    if status == STATUS_FUNDED:
        if len(orders) != 4 or {row["side"] for row in orders} != {"BUY"}:
            raise OperatedPortfolioError("INITIAL_FUNDING_TRADES_INVALID")
        if workspace["book"]["nav"] != "4992":
            raise OperatedPortfolioError("FUNDED_NAV_INVALID")
    elif status == STATUS_NO_CHANGE:
        if len(orders) != 4:
            raise OperatedPortfolioError("NO_CHANGE_CREATED_TRADE")
        if workspace["book"]["nav"] != "4992":
            raise OperatedPortfolioError("NO_CHANGE_NAV_INVALID")
        if workspace.get("changed_why", {}).get("change_type") != "NO_CHANGE":
            raise OperatedPortfolioError("NO_CHANGE_EXPLANATION_REQUIRED")
    else:
        if len(orders) != 6:
            raise OperatedPortfolioError("TRANSITION_TRADE_COUNT_INVALID")
        if [row["side"] for row in orders[-2:]] != ["SELL", "BUY"]:
            raise OperatedPortfolioError("REDUCE_AND_FUND_SEQUENCE_REQUIRED")
        positions = {
            row["instrument_id"]: row["quantity"]
            for row in workspace["book"]["positions"]
        }
        by_symbol = {row["symbol"]: row["instrument_id"] for row in instruments}
        if positions.get(by_symbol["HARBOR"]) != "6":
            raise OperatedPortfolioError("HARBOR_REDUCTION_MISSING")
        if positions.get(by_symbol["MERID"]) != "5":
            raise OperatedPortfolioError("MERIDIAN_FUNDING_MISSING")
        if workspace["book"]["nav"] != "4988":
            raise OperatedPortfolioError("TRANSITION_NAV_INVALID")
        if workspace.get("changed_why", {}).get("change_type") != "AUTHORIZED_TRANSITION":
            raise OperatedPortfolioError("CHANGED_WHY_REQUIRED")
        if status == STATUS_CORRECTED:
            corrections = workspace.get("correction_history") or []
            if len(corrections) != 1:
                raise OperatedPortfolioError("CORRECTION_LINEAGE_REQUIRED")
            if corrections[0].get("economic_effect") != "NONE":
                raise OperatedPortfolioError("CORRECTION_MUST_BE_NON_ECONOMIC")
