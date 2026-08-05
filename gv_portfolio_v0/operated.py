"""One scalable deterministic operated-portfolio engine.

The same domain path executes the retained ten-security regression scenario and
the 25-security Portfolio Scale product scenario. Scenario data is declarative;
books, execution, replay, certification, correction, and validation remain one
shared authority path. The engine is paper-only and has no provider, broker,
network, alpha, or live-capital path.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
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
from gv_portfolio_v0.operated_scenarios import (
    DEFAULT_SCENARIO_ID,
    get_scenario,
    scenario_hash,
)
from gv_portfolio_v0.replay import (
    ReplayError,
    append_correction_and_recertify,
    certify_replay_prefix,
    reconstruct_exact,
    replay_idempotent,
)

AVAILABLE = "AVAILABLE"
RESEARCH_RESERVE = "RESEARCH_RESERVE"

STATUS_DRAFT = "DRAFT_REVIEW"
STATUS_FUNDED = "FUNDED_CERTIFIED"
STATUS_NO_CHANGE = "OBSERVED_NO_CHANGE_CERTIFIED"
STATUS_TRANSITION = "TRANSITION_CERTIFIED"
STATUS_CORRECTED = "CORRECTED_CERTIFIED"
STATUSES = {
    STATUS_DRAFT,
    STATUS_FUNDED,
    STATUS_NO_CHANGE,
    STATUS_TRANSITION,
    STATUS_CORRECTED,
}


class OperatedPortfolioError(ValueError):
    """Fail-closed operated-portfolio error."""


def _load_scenario(scenario_id: str) -> dict[str, Any]:
    try:
        return get_scenario(scenario_id)
    except ValueError as exc:
        raise OperatedPortfolioError(str(exc)) from exc


def _workspace_scenario(workspace: Mapping[str, Any]) -> dict[str, Any]:
    scenario_id = workspace.get("scenario_id")
    if not isinstance(scenario_id, str):
        raise OperatedPortfolioError("WORKSPACE_SCENARIO_REQUIRED")
    scenario = _load_scenario(scenario_id)
    if workspace.get("scenario_hash") != scenario_hash(scenario):
        raise OperatedPortfolioError("WORKSPACE_SCENARIO_HASH_MISMATCH")
    return scenario


def _identifier(
    scenario: Mapping[str, Any], kind: str, payload: Mapping[str, Any]
) -> str:
    return f"{kind}_" + domain_hash(
        f"{scenario['id_domain']}:{kind}:V1", dict(payload)
    )


def _record(
    scenario: Mapping[str, Any],
    kind: str,
    id_key: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    body = dict(payload)
    return {id_key: _identifier(scenario, kind, body), **body}


def _verify_id(
    scenario: Mapping[str, Any],
    record: Mapping[str, Any],
    *,
    kind: str,
    id_key: str,
) -> None:
    body = {key: value for key, value in record.items() if key != id_key}
    if record.get(id_key) != _identifier(scenario, kind, body):
        raise OperatedPortfolioError(f"IDENTITY_MISMATCH:{id_key}")


def _instrument(
    scenario: Mapping[str, Any], specification: Mapping[str, Any]
) -> dict[str, Any]:
    identity = {
        "namespace": specification.get(
            "identity_namespace",
            scenario.get("identity_namespace", "GV_SYNTHETIC_PERMANENT_V1"),
        ),
        "permanent_key": specification["permanent_key"],
        "security_class": specification.get("security_class", "COMMON_STOCK"),
    }
    return {
        "instrument_id": _identifier(scenario, "INS", identity),
        **identity,
        "symbol": specification["symbol"],
        "name": specification["name"],
        "economic_cluster": specification["economic_cluster"],
    }


def instrument_registry(
    scenario_id: str = DEFAULT_SCENARIO_ID,
) -> list[dict[str, Any]]:
    scenario = _load_scenario(scenario_id)
    return [_instrument(scenario, row) for row in scenario["instruments"]]


def _evidence(
    scenario: Mapping[str, Any],
    *,
    content: str,
    locator: str,
    observed_at: str,
    owned_instrument_ids: Iterable[str],
) -> dict[str, Any]:
    owners = sorted(str(value) for value in owned_instrument_ids)
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    identity = {
        "content_sha256": content_sha256,
        "media_type": "text/plain",
        "locator": locator,
        "observed_at": observed_at,
        "owned_instrument_ids": owners,
    }
    return {
        "evidence_reference_id": _identifier(scenario, "EVD", identity),
        **identity,
        "content": content,
    }


def _initial_evidence(
    scenario: Mapping[str, Any], instruments: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (specification, instrument) in enumerate(
        zip(scenario["instruments"], instruments, strict=True)
    ):
        rows.append(
            _evidence(
                scenario,
                content=specification["evidence_content"],
                locator=specification.get(
                    "evidence_locator",
                    (
                        f"fixture://{scenario['fixture_namespace']}/"
                        f"{specification['symbol'].lower()}/"
                        f"{specification['evidence_slug']}-v1"
                    ),
                ),
                observed_at=_minute_timestamp(
                    f"{scenario['timeline']['cash_opened_at'][:11]}12:00:00.000000Z",
                    index,
                ),
                owned_instrument_ids=[instrument["instrument_id"]],
            )
        )
    return rows


def _no_change_evidence(
    scenario: Mapping[str, Any], instruments: list[dict[str, Any]]
) -> dict[str, Any]:
    by_symbol = {row["symbol"]: row for row in instruments}
    config = scenario["no_change"]
    return _evidence(
        scenario,
        content=config["content"],
        locator=config["locator"],
        observed_at=config["observed_at"],
        owned_instrument_ids=[by_symbol[config["instrument_symbol"]]["instrument_id"]],
    )


def _transition_evidence(
    scenario: Mapping[str, Any], instruments: list[dict[str, Any]]
) -> dict[str, Any]:
    by_symbol = {row["symbol"]: row for row in instruments}
    config = scenario["transition"]
    return _evidence(
        scenario,
        content=config["content"],
        locator=config["locator"],
        observed_at=config["observed_at"],
        owned_instrument_ids=[
            by_symbol[symbol]["instrument_id"]
            for symbol in config["review_updates"]
        ],
    )


def _thesis(
    scenario: Mapping[str, Any],
    *,
    instrument_id: str,
    principal_claim: str,
    evidence_reference_ids: list[str],
    hard_falsifiers: list[str],
    watch_conditions: list[str],
) -> dict[str, Any]:
    payload = {
        "instrument_id": instrument_id,
        "principal_claim": principal_claim,
        "evidence_reference_ids": list(evidence_reference_ids),
        "hard_falsifiers": list(hard_falsifiers),
        "watch_conditions": list(watch_conditions),
    }
    return {
        "thesis_id": _identifier(scenario, "THS", payload),
        **payload,
    }


def _initial_reviews(
    scenario: Mapping[str, Any],
    instruments: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for specification, instrument, evidence_row in zip(
        scenario["instruments"], instruments, evidence, strict=True
    ):
        rows.append(
            {
                "instrument_id": instrument["instrument_id"],
                "symbol": instrument["symbol"],
                "economic_cluster": instrument["economic_cluster"],
                "outcome": specification["outcome"],
                "net_score_bps": specification["net_score_bps"],
                "target_quantity": specification["target_quantity"],
                "reference_price": specification["reference_price"],
                "living_thesis_lite": _thesis(
                    scenario,
                    instrument_id=instrument["instrument_id"],
                    principal_claim=specification["principal_claim"],
                    evidence_reference_ids=[
                        evidence_row["evidence_reference_id"]
                    ],
                    hard_falsifiers=specification["hard_falsifiers"],
                    watch_conditions=specification["watch_conditions"],
                ),
            }
        )
    return rows


def _expected_reviews_for_status(
    scenario: Mapping[str, Any],
    *,
    status: str,
    instruments: list[dict[str, Any]],
    initial_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reviews = _initial_reviews(scenario, instruments, initial_evidence)
    if status not in {STATUS_TRANSITION, STATUS_CORRECTED}:
        return reviews
    transition_evidence_id = _transition_evidence(
        scenario, instruments
    )["evidence_reference_id"]
    for review in reviews:
        update = scenario["transition"]["review_updates"].get(review["symbol"])
        if update is None:
            continue
        old_thesis = review["living_thesis_lite"]
        review["net_score_bps"] = update["net_score_bps"]
        review["target_quantity"] = update["target_quantity"]
        review["living_thesis_lite"] = _thesis(
            scenario,
            instrument_id=review["instrument_id"],
            principal_claim=update["principal_claim"],
            evidence_reference_ids=[
                *old_thesis["evidence_reference_ids"],
                transition_evidence_id,
            ],
            hard_falsifiers=old_thesis["hard_falsifiers"],
            watch_conditions=old_thesis["watch_conditions"],
        )
    return reviews


def _portfolio_aim(scenario: Mapping[str, Any]) -> dict[str, Any]:
    config = scenario["portfolio_aim"]
    return _record(
        scenario,
        "AIM",
        "portfolio_aim_id",
        {
            "objective": config["objective"],
            "instrument_count": len(scenario["instruments"]),
            "minimum_funded_positions": scenario["minimum_funded_positions"],
            "minimum_total_cash_bps": scenario["minimum_total_cash_bps"],
            "allowed_actions": config["allowed_actions"],
            "effective_at": config["effective_at"],
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
    scenario: Mapping[str, Any],
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
    return _record(scenario, "DSN", "decision_snapshot_id", payload)


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


def _utc_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def _utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _minute_timestamp(anchor: str, minute: int, second: int = 0) -> str:
    hour_start = _utc_datetime(anchor).replace(
        minute=0, second=0, microsecond=0
    )
    return _utc_timestamp(
        hour_start + timedelta(minutes=minute, seconds=second)
    )


def _timestamp_after(configured: str, prior: str) -> str:
    minimum = _utc_datetime(prior) + timedelta(seconds=1)
    return _utc_timestamp(max(_utc_datetime(configured), minimum))


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


def build_draft_workspace(
    scenario_id: str = DEFAULT_SCENARIO_ID,
) -> dict[str, Any]:
    scenario = _load_scenario(scenario_id)
    instruments = instrument_registry(scenario_id)
    evidence = _initial_evidence(scenario, instruments)
    reviews = _initial_reviews(scenario, instruments, evidence)
    aim = _portfolio_aim(scenario)
    snapshot = _decision_snapshot(
        scenario,
        aim_id=aim["portfolio_aim_id"],
        reviews=reviews,
        created_at=scenario["timeline"]["initial_decision_at"],
        reason=scenario["initial_decision_reason"],
    )
    events: list[dict[str, Any]] = []
    for opening in scenario["cash_openings"]:
        events.append(
            _event(
                len(events),
                "CASH_OPENING",
                scenario["timeline"]["cash_opened_at"],
                f"{scenario['id_domain']}:CASH:{opening['bucket']}",
                cash_bucket=opening["bucket"],
                payload={"amount": opening["amount"]},
            )
        )
    workspace = {
        "schema_version": scenario["schema_version"],
        "fixture_id": scenario["scenario_id"],
        "scenario_id": scenario["scenario_id"],
        "scenario_hash": scenario_hash(scenario),
        "claim_boundary": scenario["claim_boundary"],
        "status": STATUS_DRAFT,
        "explanation": scenario["status_explanations"][STATUS_DRAFT],
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
    scenario = _workspace_scenario(workspace)
    result = deepcopy(dict(workspace))
    result["events"].append(
        _event(
            len(result["events"]),
            "PORTFOLIO_AIM_CONFIRMED",
            scenario["timeline"]["aim_confirmed_at"],
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
        effective_at=scenario["timeline"]["initial_transition_at"],
        legs=legs,
    )
    start_minute = int(scenario["timeline"]["initial_order_start_minute"])
    for index, row in enumerate(funded_reviews):
        minute = start_minute + index
        _append_trade(
            result,
            transition_event_id=transition["event_id"],
            instrument_id=row["instrument_id"],
            side="BUY",
            quantity=row["target_quantity"],
            price=row["reference_price"],
            fee="2",
            order_created_at=_minute_timestamp(
                scenario["timeline"]["initial_transition_at"], minute
            ),
            filled_at=_minute_timestamp(
                scenario["timeline"]["initial_transition_at"], minute, 1
            ),
        )
    result["book"] = _reduce(result["events"])
    result["status"] = STATUS_FUNDED
    result["explanation"] = scenario["status_explanations"][STATUS_FUNDED]
    result["changed_why"] = {
        "change_type": "INITIAL_FUNDING",
        "reason": scenario["initial_changed_why_reason"],
        "funded_symbols": [row["symbol"] for row in funded_reviews],
        "position_count_after": len(funded_reviews),
        "cash_after": result["book"]["total_cash"],
        "costs_after": result["book"]["total_costs"],
    }
    _append_certification(
        result,
        effective_at=_timestamp_after(
            scenario["timeline"]["initial_certified_at"],
            result["events"][-1]["effective_at"],
        ),
    )
    validate_workspace(result)
    return result


def admit_no_change_observation(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] != STATUS_FUNDED:
        raise OperatedPortfolioError("FUNDED_WORKSPACE_REQUIRED")
    scenario = _workspace_scenario(workspace)
    result = deepcopy(dict(workspace))
    prior_book = canonical_document_bytes(result["book"])
    observation = _no_change_evidence(scenario, result["instruments"])
    result["evidence_references"].append(observation)
    instrument_id = observation["owned_instrument_ids"][0]
    observation_record = _record(
        scenario,
        "OBS",
        "observation_id",
        {
            "evidence_reference_id": observation["evidence_reference_id"],
            "disposition": "AIM_UNCHANGED_NO_TRANSITION",
            "instrument_id": instrument_id,
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
            instrument_id=instrument_id,
            payload=dict(observation_record),
        )
    )
    result["book"] = _reduce(result["events"])
    if canonical_document_bytes(result["book"]) != prior_book:
        raise OperatedPortfolioError("NO_CHANGE_OBSERVATION_CHANGED_BOOK")
    result["status"] = STATUS_NO_CHANGE
    result["explanation"] = scenario["status_explanations"][STATUS_NO_CHANGE]
    result["changed_why"] = {
        "change_type": "NO_CHANGE",
        "reason": scenario["no_change"]["reason"],
        "holdings_changed": False,
        "cash_changed": False,
        "orders_created": 0,
    }
    _append_certification(
        result, effective_at=scenario["timeline"]["no_change_certified_at"]
    )
    validate_workspace(result)
    return result


def _transition_legs_from_reviews(
    instruments: list[dict[str, Any]],
    before_reviews: list[dict[str, Any]],
    after_reviews: list[dict[str, Any]],
) -> list[dict[str, str]]:
    before_by_id = {row["instrument_id"]: row for row in before_reviews}
    after_by_id = {row["instrument_id"]: row for row in after_reviews}
    legs: list[dict[str, str]] = []
    for instrument in instruments:
        instrument_id = instrument["instrument_id"]
        before = int(before_by_id[instrument_id]["target_quantity"])
        after = int(after_by_id[instrument_id]["target_quantity"])
        delta = after - before
        if delta == 0:
            continue
        legs.append(
            {
                "instrument_id": instrument_id,
                "side": "BUY" if delta > 0 else "SELL",
                "quantity": str(abs(delta)),
                "reference_price": after_by_id[instrument_id]["reference_price"],
            }
        )
    return sorted(legs, key=lambda row: (0 if row["side"] == "SELL" else 1))


def authorize_portfolio_transition(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] != STATUS_NO_CHANGE:
        raise OperatedPortfolioError("NO_CHANGE_OBSERVATION_REQUIRED_BEFORE_TRANSITION")
    scenario = _workspace_scenario(workspace)
    result = deepcopy(dict(workspace))
    instruments = result["instruments"]
    before_reviews = deepcopy(result["reviews"])
    observation = _transition_evidence(scenario, instruments)
    result["evidence_references"].append(observation)
    initial_evidence = result["evidence_references"][: len(instruments)]
    updated_reviews = _expected_reviews_for_status(
        scenario,
        status=STATUS_TRANSITION,
        instruments=instruments,
        initial_evidence=initial_evidence,
    )
    result["reviews"] = updated_reviews
    transition_snapshot = _decision_snapshot(
        scenario,
        aim_id=result["portfolio_aim"]["portfolio_aim_id"],
        reviews=updated_reviews,
        created_at=scenario["timeline"]["transition_decision_at"],
        reason=scenario["transition"]["decision_reason"],
    )
    result["decision_snapshots"].append(transition_snapshot)
    result["current_decision_snapshot"] = transition_snapshot
    affected_ids = list(observation["owned_instrument_ids"])
    observation_record = _record(
        scenario,
        "OBS",
        "observation_id",
        {
            "evidence_reference_id": observation["evidence_reference_id"],
            "disposition": "AUTHORIZED_TRANSITION",
            "instrument_ids": affected_ids,
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
    legs = _transition_legs_from_reviews(
        instruments, before_reviews, updated_reviews
    )
    if not any(row["side"] == "SELL" for row in legs):
        raise OperatedPortfolioError("TRANSITION_SELL_REQUIRED")
    if not any(row["side"] == "BUY" for row in legs):
        raise OperatedPortfolioError("TRANSITION_BUY_REQUIRED")
    transition = _append_transition_event(
        result,
        transition_kind=scenario["transition"]["transition_kind"],
        effective_at=scenario["timeline"]["transition_planned_at"],
        legs=legs,
    )
    start_minute = int(scenario["timeline"]["transition_order_start_minute"])
    for index, leg in enumerate(legs):
        minute = start_minute + index
        _append_trade(
            result,
            transition_event_id=transition["event_id"],
            instrument_id=leg["instrument_id"],
            side=leg["side"],
            quantity=leg["quantity"],
            price=leg["reference_price"],
            fee="2",
            order_created_at=_minute_timestamp(
                scenario["timeline"]["transition_planned_at"], minute
            ),
            filled_at=_minute_timestamp(
                scenario["timeline"]["transition_planned_at"], minute, 1
            ),
        )
    result["book"] = _reduce(result["events"])
    result["status"] = STATUS_TRANSITION
    result["explanation"] = scenario["status_explanations"][STATUS_TRANSITION]
    initial_by_symbol = {row["symbol"]: row for row in before_reviews}
    current_by_symbol = {row["symbol"]: row for row in updated_reviews}
    reduced_symbol = scenario["transition"]["primary_reduced_symbol"]
    funded_symbol = scenario["transition"]["primary_funded_symbol"]
    result["changed_why"] = {
        "change_type": "AUTHORIZED_TRANSITION",
        "reason": scenario["transition"]["reason"],
        "reduced": {
            "symbol": reduced_symbol,
            "quantity_before": initial_by_symbol[reduced_symbol]["target_quantity"],
            "quantity_after": current_by_symbol[reduced_symbol]["target_quantity"],
            "score_before_bps": int(initial_by_symbol[reduced_symbol]["net_score_bps"]),
            "score_after_bps": int(current_by_symbol[reduced_symbol]["net_score_bps"]),
        },
        "funded_or_increased": {
            "symbol": funded_symbol,
            "quantity_before": initial_by_symbol[funded_symbol]["target_quantity"],
            "quantity_after": current_by_symbol[funded_symbol]["target_quantity"],
            "score_before_bps": int(initial_by_symbol[funded_symbol]["net_score_bps"]),
            "score_after_bps": int(current_by_symbol[funded_symbol]["net_score_bps"]),
        },
        "cash_after": result["book"]["total_cash"],
        "total_costs_after": result["book"]["total_costs"],
        "unexplained_residual": result["book"]["unexplained_residual"],
    }
    _append_certification(
        result, effective_at=scenario["timeline"]["transition_certified_at"]
    )
    validate_workspace(result)
    return result


def append_non_economic_correction(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] not in {STATUS_TRANSITION, STATUS_CORRECTED}:
        raise OperatedPortfolioError("TRANSITION_CERTIFICATION_REQUIRED")
    if workspace["status"] == STATUS_CORRECTED:
        return deepcopy(dict(workspace))
    scenario = _workspace_scenario(workspace)
    result = deepcopy(dict(workspace))
    prior = deepcopy(result["certification"])
    try:
        corrected = append_correction_and_recertify(
            result["events"],
            prior_certification=prior,
            correction_payload={
                "correction_kind": "ANNOTATION",
                "reason": scenario["correction"]["reason"],
                "details": {"economic_effect": "NONE"},
            },
            decision_snapshot_id=result["current_decision_snapshot"][
                "decision_snapshot_id"
            ],
            portfolio_aim_id=result["portfolio_aim"]["portfolio_aim_id"],
            effective_at=scenario["timeline"]["correction_at"],
            source_identity=scenario["correction"]["source_identity"],
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
            scenario["timeline"]["correction_recorded_at"],
            result["certification"]["certification_id"],
            payload={
                "certification_id": result["certification"]["certification_id"]
            },
        )
    )
    result["book"] = _reduce(result["events"])
    result["status"] = STATUS_CORRECTED
    result["explanation"] = scenario["status_explanations"][STATUS_CORRECTED]
    validate_workspace(result)
    return result


def _funded_positions(book: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [row for row in book["positions"] if int(row["quantity"]) > 0]


def _expected_snapshots(
    scenario: Mapping[str, Any],
    *,
    status: str,
    aim_id: str,
    instruments: list[dict[str, Any]],
    initial_evidence: list[dict[str, Any]],
    current_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    initial_reviews = _initial_reviews(scenario, instruments, initial_evidence)
    snapshots = [
        _decision_snapshot(
            scenario,
            aim_id=aim_id,
            reviews=initial_reviews,
            created_at=scenario["timeline"]["initial_decision_at"],
            reason=scenario["initial_decision_reason"],
        )
    ]
    if status in {STATUS_TRANSITION, STATUS_CORRECTED}:
        snapshots.append(
            _decision_snapshot(
                scenario,
                aim_id=aim_id,
                reviews=current_reviews,
                created_at=scenario["timeline"]["transition_decision_at"],
                reason=scenario["transition"]["decision_reason"],
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
        expected.append(
            (
                "REDUCE_AND_FUND",
                snapshots[-1]["decision_snapshot_id"],
                _transition_legs_from_reviews(
                    instruments, initial_reviews, current_reviews
                ),
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
    scenario: Mapping[str, Any],
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
    symbol_by_id = {row["instrument_id"]: row["symbol"] for row in instruments}
    if status == STATUS_FUNDED:
        selected_ids = snapshots[0]["capital_competition"][
            "selected_funded_instrument_ids"
        ]
        return {
            "change_type": "INITIAL_FUNDING",
            "reason": scenario["initial_changed_why_reason"],
            "funded_symbols": [symbol_by_id[row] for row in selected_ids],
            "position_count_after": len(_funded_positions(book)),
            "cash_after": book["total_cash"],
            "costs_after": book["total_costs"],
        }
    if status == STATUS_NO_CHANGE:
        return {
            "change_type": "NO_CHANGE",
            "reason": scenario["no_change"]["reason"],
            "holdings_changed": False,
            "cash_changed": False,
            "orders_created": 0,
        }
    initial_by_symbol = {row["symbol"]: row for row in initial_reviews}
    current_by_symbol = {row["symbol"]: row for row in current_reviews}
    reduced_symbol = scenario["transition"]["primary_reduced_symbol"]
    funded_symbol = scenario["transition"]["primary_funded_symbol"]
    return {
        "change_type": "AUTHORIZED_TRANSITION",
        "reason": scenario["transition"]["reason"],
        "reduced": {
            "symbol": reduced_symbol,
            "quantity_before": initial_by_symbol[reduced_symbol]["target_quantity"],
            "quantity_after": current_by_symbol[reduced_symbol]["target_quantity"],
            "score_before_bps": int(initial_by_symbol[reduced_symbol]["net_score_bps"]),
            "score_after_bps": int(current_by_symbol[reduced_symbol]["net_score_bps"]),
        },
        "funded_or_increased": {
            "symbol": funded_symbol,
            "quantity_before": initial_by_symbol[funded_symbol]["target_quantity"],
            "quantity_after": current_by_symbol[funded_symbol]["target_quantity"],
            "score_before_bps": int(initial_by_symbol[funded_symbol]["net_score_bps"]),
            "score_after_bps": int(current_by_symbol[funded_symbol]["net_score_bps"]),
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
    scenario = _workspace_scenario(workspace)
    if workspace.get("schema_version") != scenario["schema_version"]:
        raise OperatedPortfolioError("WORKSPACE_SCHEMA_INVALID")
    if workspace.get("fixture_id") != scenario["scenario_id"]:
        raise OperatedPortfolioError("WORKSPACE_FIXTURE_ID_INVALID")
    if workspace.get("claim_boundary") != scenario["claim_boundary"]:
        raise OperatedPortfolioError("WORKSPACE_CLAIM_BOUNDARY_INVALID")
    if workspace.get("portfolio_count") != 1:
        raise OperatedPortfolioError("EXACTLY_ONE_PORTFOLIO_REQUIRED")
    status = workspace.get("status")
    if status not in STATUSES:
        raise OperatedPortfolioError("WORKSPACE_STATUS_INVALID")
    if workspace.get("explanation") != scenario["status_explanations"][status]:
        raise OperatedPortfolioError("WORKSPACE_EXPLANATION_INVALID")

    expected_instruments = instrument_registry(scenario["scenario_id"])
    instruments = list(workspace.get("instruments") or [])
    instrument_count = len(expected_instruments)
    if len(instruments) != instrument_count:
        raise OperatedPortfolioError("SCENARIO_INSTRUMENT_COUNT_MISMATCH")
    if canonical_document_bytes(instruments) != canonical_document_bytes(
        expected_instruments
    ):
        raise OperatedPortfolioError("INSTRUMENT_REGISTRY_MISMATCH")
    instrument_ids = [row["instrument_id"] for row in instruments]
    permanent_keys = [row["permanent_key"] for row in instruments]
    if (
        len(set(instrument_ids)) != instrument_count
        or len(set(permanent_keys)) != instrument_count
    ):
        raise OperatedPortfolioError("PERMANENT_IDENTITY_DUPLICATE")
    minimum_clusters = int(scenario.get("minimum_economic_clusters", 2))
    if len({row["economic_cluster"] for row in instruments}) < minimum_clusters:
        raise OperatedPortfolioError("MINIMUM_ECONOMIC_CLUSTERS_REQUIRED")
    for row in instruments:
        identity = {
            "namespace": row["namespace"],
            "permanent_key": row["permanent_key"],
            "security_class": row["security_class"],
        }
        if row["instrument_id"] != _identifier(scenario, "INS", identity):
            raise OperatedPortfolioError("INSTRUMENT_ID_MISMATCH")

    evidence = list(workspace.get("evidence_references") or [])
    evidence_ids: set[str] = set()
    for row in evidence:
        raw_hash = hashlib.sha256(row["content"].encode("utf-8")).hexdigest()
        if raw_hash != row["content_sha256"]:
            raise OperatedPortfolioError("EVIDENCE_CONTENT_HASH_MISMATCH")
        owners = row.get("owned_instrument_ids")
        if (
            not isinstance(owners, list)
            or not owners
            or len(owners) != len(set(owners))
            or any(owner not in instrument_ids for owner in owners)
        ):
            raise OperatedPortfolioError("EVIDENCE_INSTRUMENT_OWNERSHIP_INVALID")
        identity = {
            "content_sha256": row["content_sha256"],
            "media_type": row["media_type"],
            "locator": row["locator"],
            "observed_at": row["observed_at"],
            "owned_instrument_ids": sorted(owners),
        }
        if row["evidence_reference_id"] != _identifier(scenario, "EVD", identity):
            raise OperatedPortfolioError("EVIDENCE_ID_MISMATCH")
        if row["evidence_reference_id"] in evidence_ids:
            raise OperatedPortfolioError("EVIDENCE_ID_DUPLICATE")
        evidence_ids.add(row["evidence_reference_id"])
    initial_evidence = evidence[:instrument_count]
    expected_initial_evidence = _initial_evidence(scenario, instruments)
    if canonical_document_bytes(initial_evidence) != canonical_document_bytes(
        expected_initial_evidence
    ):
        raise OperatedPortfolioError("INITIAL_EVIDENCE_REGISTRY_MISMATCH")
    expected_evidence = [*expected_initial_evidence]
    if status in {STATUS_NO_CHANGE, STATUS_TRANSITION, STATUS_CORRECTED}:
        expected_evidence.append(_no_change_evidence(scenario, instruments))
    if status in {STATUS_TRANSITION, STATUS_CORRECTED}:
        expected_evidence.append(_transition_evidence(scenario, instruments))
    if canonical_document_bytes(evidence) != canonical_document_bytes(
        expected_evidence
    ):
        raise OperatedPortfolioError("EVIDENCE_LINEAGE_MISMATCH")

    reviews = list(workspace.get("reviews") or [])
    if len(reviews) != instrument_count:
        raise OperatedPortfolioError("REVIEW_INSTRUMENT_COUNT_MISMATCH")
    if {row["instrument_id"] for row in reviews} != set(instrument_ids):
        raise OperatedPortfolioError("REVIEW_INSTRUMENT_COVERAGE_MISMATCH")
    evidence_by_id = {
        row["evidence_reference_id"]: row for row in evidence
    }
    for review in reviews:
        thesis = review.get("living_thesis_lite")
        if not isinstance(thesis, Mapping):
            raise OperatedPortfolioError("THESIS_OBJECT_REQUIRED")
        if thesis.get("instrument_id") != review["instrument_id"]:
            raise OperatedPortfolioError("THESIS_INSTRUMENT_OWNER_MISMATCH")
        refs = thesis.get("evidence_reference_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or len(refs) != len(set(refs))
            or any(ref not in evidence_by_id for ref in refs)
        ):
            raise OperatedPortfolioError("THESIS_EVIDENCE_BINDING_INVALID")
        for ref in refs:
            if review["instrument_id"] not in evidence_by_id[ref][
                "owned_instrument_ids"
            ]:
                raise OperatedPortfolioError(
                    "THESIS_INSTRUMENT_EVIDENCE_OWNER_MISMATCH"
                )
        thesis_payload = {
            key: value for key, value in thesis.items() if key != "thesis_id"
        }
        if thesis.get("thesis_id") != _identifier(scenario, "THS", thesis_payload):
            raise OperatedPortfolioError("THESIS_ID_MISMATCH")
    expected_reviews = _expected_reviews_for_status(
        scenario,
        status=status,
        instruments=instruments,
        initial_evidence=initial_evidence,
    )
    if canonical_document_bytes(reviews) != canonical_document_bytes(
        expected_reviews
    ):
        raise OperatedPortfolioError("REVIEW_DECISION_STATE_MISMATCH")

    expected_aim = _portfolio_aim(scenario)
    if canonical_document_bytes(workspace["portfolio_aim"]) != canonical_document_bytes(
        expected_aim
    ):
        raise OperatedPortfolioError("PORTFOLIO_AIM_AUTHORITY_MISMATCH")
    _verify_id(
        scenario,
        workspace["portfolio_aim"],
        kind="AIM",
        id_key="portfolio_aim_id",
    )
    aim_id = workspace["portfolio_aim"]["portfolio_aim_id"]
    snapshots = list(workspace.get("decision_snapshots") or [])
    expected_snapshots = _expected_snapshots(
        scenario,
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
        _verify_id(
            scenario,
            snapshot,
            kind="DSN",
            id_key="decision_snapshot_id",
        )
        candidates = snapshot["capital_competition"]["candidates"]
        if len(candidates) != instrument_count:
            raise OperatedPortfolioError("CAPITAL_COMPETITION_COUNT_MISMATCH")
        candidate_ids = [row["instrument_id"] for row in candidates]
        if (
            set(candidate_ids) != set(instrument_ids)
            or len(candidate_ids) != len(set(candidate_ids))
        ):
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
    for observation_event in observation_events:
        observation = observation_event.get("payload")
        if not isinstance(observation, Mapping):
            raise OperatedPortfolioError("OBSERVATION_EVENT_PAYLOAD_REQUIRED")
        _verify_id(
            scenario,
            observation,
            kind="OBS",
            id_key="observation_id",
        )
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

    initial_reviews = _initial_reviews(scenario, instruments, initial_evidence)
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
    expected_order_sides: list[str] = []
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
        expected_order_sides.extend(row["side"] for row in expected_legs)
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
    if [row["side"] for row in orders] != expected_order_sides:
        raise OperatedPortfolioError("TRADE_SIDE_SEQUENCE_MISMATCH")

    expected_changed_why = _expected_changed_why(
        scenario,
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
        return

    if not certification_eligible(workspace["book"]):
        raise OperatedPortfolioError("BOOK_NOT_CERTIFICATION_ELIGIBLE")
    if workspace["book"]["unexplained_residual"] != "0":
        raise OperatedPortfolioError("UNEXPLAINED_RESIDUAL_NONZERO")
    if len(_funded_positions(workspace["book"])) < int(
        scenario["minimum_funded_positions"]
    ):
        raise OperatedPortfolioError("MINIMUM_FUNDED_POSITIONS_REQUIRED")
    cash_buckets = {row["bucket"] for row in workspace["book"]["classified_cash"]}
    required_cash_buckets = {row["bucket"] for row in scenario["cash_openings"]}
    if required_cash_buckets - cash_buckets:
        raise OperatedPortfolioError("CLASSIFIED_RESIDUAL_CASH_REQUIRED")

    expected_quantities = {
        row["instrument_id"]: row["target_quantity"] for row in reviews
    }
    actual_quantities = {
        row["instrument_id"]: row["quantity"]
        for row in workspace["book"]["positions"]
    }
    for instrument_id, expected_quantity in expected_quantities.items():
        if actual_quantities.get(instrument_id, "0") != expected_quantity:
            raise OperatedPortfolioError("POSITION_TARGET_MISMATCH")

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

    expected_order_count = sum(
        len(transition[2]) for transition in expected_transitions
    )
    if len(orders) != expected_order_count:
        raise OperatedPortfolioError("TRADE_COUNT_INVALID")
    if status == STATUS_NO_CHANGE and workspace.get("changed_why", {}).get(
        "change_type"
    ) != "NO_CHANGE":
        raise OperatedPortfolioError("NO_CHANGE_EXPLANATION_REQUIRED")
    if status in {STATUS_TRANSITION, STATUS_CORRECTED}:
        later_legs = expected_transitions[-1][2]
        if not any(row["side"] == "SELL" for row in later_legs):
            raise OperatedPortfolioError("REDUCTION_REQUIRED")
        if not any(row["side"] == "BUY" for row in later_legs):
            raise OperatedPortfolioError("FUNDING_REQUIRED")
        if workspace.get("changed_why", {}).get("change_type") != "AUTHORIZED_TRANSITION":
            raise OperatedPortfolioError("CHANGED_WHY_REQUIRED")
        if status == STATUS_CORRECTED:
            corrections = workspace.get("correction_history") or []
            if len(corrections) != 1:
                raise OperatedPortfolioError("CORRECTION_LINEAGE_REQUIRED")
            if corrections[0].get("economic_effect") != "NONE":
                raise OperatedPortfolioError("CORRECTION_MUST_BE_NON_ECONOMIC")
