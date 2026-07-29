"""Deterministic four-security micro-portfolio vertical.

The module owns the bounded acceptance fixture, immutable event identities,
book reduction, decision/order/fill identities, and certification. It performs
no provider, broker, network, optimization, or live-capital work.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from contracts.gv_portfolio.v0 import (
    CustodyContractError,
    evidence_reference as custody_evidence_reference,
    identifier as custody_identifier,
    instrument_identity,
    record_with_id as custody_record_with_id,
    verify_evidence_reference,
    verify_instrument_identity,
    verify_record_id,
)
from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from core.gv_portfolio_v0.events import (
    CanonicalEventStream,
    CustodyEventError,
    portfolio_book_event,
)

SCHEMA_VERSION = "gv_portfolio_v0_workspace_v1"
ID_DOMAIN = "GV-PORTFOLIO-V0"
DECLARED_PRECISION = "0.01"


class PortfolioV0Error(ValueError):
    """Fail-closed micro-portfolio error."""


def _decimal(value: str | int | Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PortfolioV0Error(f"DECIMAL_INVALID:{value}") from exc
    if not parsed.is_finite():
        raise PortfolioV0Error("DECIMAL_FINITE_REQUIRED")
    return parsed


def _decimal_text(value: str | int | Decimal) -> str:
    parsed = _decimal(value)
    if parsed == 0:
        return "0"
    text = format(parsed.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return custody_identifier(kind, payload)


def _record_with_id(kind: str, id_key: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return custody_record_with_id(kind, id_key, payload)


def _instrument(
    permanent_key: str,
    symbol: str,
    name: str,
    role: str,
) -> dict[str, Any]:
    identity = instrument_identity(permanent_key)
    return {
        **identity,
        "symbol": symbol,
        "name": name,
        "role": role,
    }


def evidence_reference(
    *, content: str, locator: str, observed_at: str, media_type: str = "text/plain"
) -> dict[str, Any]:
    return custody_evidence_reference(
        content=content,
        locator=locator,
        observed_at=observed_at,
        media_type=media_type,
    )


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
    return portfolio_book_event(
        sequence,
        event_type,
        effective_at,
        source_identity,
        instrument_id=instrument_id,
        cash_bucket=cash_bucket,
        payload=payload,
    )


def _aim(benchmark_instrument_id: str) -> dict[str, Any]:
    payload = {
        "objective": "Compound capital while preserving mandate safety and explicit liquidity.",
        "benchmark_instrument_id": benchmark_instrument_id,
        "maximum_single_name_bps": 6000,
        "minimum_total_cash_bps": 1000,
        "allowed_actions": ["HOLD", "BUY", "CASH"],
        "hard_falsifiers": [
            "accounting_identity_break",
            "mandate_breach",
            "principal_thesis_hard_falsifier",
        ],
        "effective_at": "2026-07-20T09:00:00.000000Z",
    }
    return _record_with_id("AIM", "portfolio_aim_id", payload)


def _scenario(bear: str, base: str, bull: str) -> dict[str, str]:
    return {"bear_value": bear, "base_value": base, "bull_value": bull}


def _review(
    *,
    instrument: Mapping[str, Any],
    relationship: str,
    outcome: str,
    thesis: str,
    scenario: Mapping[str, str],
    evidence_ids: Iterable[str],
    hard_falsifiers: Iterable[str],
    watch_conditions: Iterable[str],
) -> dict[str, Any]:
    return {
        "instrument_id": instrument["instrument_id"],
        "symbol": instrument["symbol"],
        "relationship": relationship,
        "outcome": outcome,
        "living_thesis_lite": {
            "principal_claim": thesis,
            "scenario_range": dict(scenario),
            "evidence_reference_ids": list(evidence_ids),
            "hard_falsifiers": list(hard_falsifiers),
            "watch_conditions": list(watch_conditions),
            "state": "WATCH",
        },
    }


def _capital_competition(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    by_symbol = {row["symbol"]: row for row in reviews}
    candidates = [
        {
            "candidate": "HARBOR",
            "instrument_id": by_symbol["HARBOR"]["instrument_id"],
            "outcome": "ADMIT",
            "expected_value_bps": 700,
            "risk_penalty_bps": 200,
            "cost_penalty_bps": 25,
        },
        {
            "candidate": "ORBIT",
            "instrument_id": by_symbol["ORBIT"]["instrument_id"],
            "outcome": "ABSTAIN",
            "expected_value_bps": 600,
            "risk_penalty_bps": 500,
            "cost_penalty_bps": 25,
        },
        {
            "candidate": "CASH",
            "instrument_id": None,
            "outcome": "CASH",
            "expected_value_bps": 150,
            "risk_penalty_bps": 0,
            "cost_penalty_bps": 0,
        },
    ]
    for row in candidates:
        row["net_score_bps"] = (
            row["expected_value_bps"]
            - row["risk_penalty_bps"]
            - row["cost_penalty_bps"]
        )
        row["eligible"] = row["outcome"] in {"ADMIT", "CASH"}
    eligible = [row for row in candidates if row["eligible"]]
    eligible.sort(key=lambda row: (-row["net_score_bps"], row["candidate"]))
    winner = eligible[0]
    return {
        "method": "MAX_NET_SCORE_BPS_THEN_LEXICAL",
        "candidates": candidates,
        "selected_candidate": winner["candidate"],
        "selected_instrument_id": winner["instrument_id"],
        "selected_net_score_bps": winner["net_score_bps"],
    }


def _decision_snapshot(
    *, aim: Mapping[str, Any], reviews: list[dict[str, Any]], competition: Mapping[str, Any]
) -> dict[str, Any]:
    payload = {
        "created_at": "2026-07-20T09:05:00.000000Z",
        "portfolio_aim_id": aim["portfolio_aim_id"],
        "reviews": reviews,
        "capital_competition": dict(competition),
        "selected_action": "BUY",
        "selected_instrument_id": competition["selected_instrument_id"],
        "selected_quantity": "5",
        "reference_price": "40",
        "fee": "1",
    }
    return _record_with_id("DSN", "decision_snapshot_id", payload)


def _order(snapshot: Mapping[str, Any], aim: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "decision_snapshot_id": snapshot["decision_snapshot_id"],
        "portfolio_aim_id": aim["portfolio_aim_id"],
        "instrument_id": snapshot["selected_instrument_id"],
        "side": "BUY",
        "quantity": snapshot["selected_quantity"],
        "reference_price": snapshot["reference_price"],
        "created_at": "2026-07-20T09:06:00.000000Z",
        "execution_mode": "DETERMINISTIC_PAPER",
    }
    return _record_with_id("ORD", "order_id", payload)


def _fill(order: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "order_id": order["order_id"],
        "instrument_id": order["instrument_id"],
        "side": order["side"],
        "quantity": order["quantity"],
        "price": order["reference_price"],
        "fee": "1",
        "cash_bucket": "AVAILABLE",
        "filled_at": "2026-07-20T09:06:01.000000Z",
    }
    return _record_with_id("FIL", "fill_id", payload)


def reduce_events(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = sorted((dict(row) for row in events), key=lambda row: row["sequence"])
    sequences = [row["sequence"] for row in rows]
    if not sequences or sequences[0] != 0 or sequences != sorted(set(sequences)):
        raise PortfolioV0Error("EVENT_SEQUENCE_ORDER_INVALID")
    event_ids = [row["event_id"] for row in rows]
    if len(event_ids) != len(set(event_ids)):
        raise PortfolioV0Error("DUPLICATE_EVENT_ID")

    cash: dict[str, Decimal] = {}
    positions: dict[str, dict[str, Decimal | None]] = {}
    split_residuals: list[Decimal] = []

    for row in rows:
        event_type = row["event_type"]
        payload = row["payload"]
        instrument_id = row.get("instrument_id")
        cash_bucket = row.get("cash_bucket")
        if event_type == "CASH_OPENING":
            if not cash_bucket:
                raise PortfolioV0Error("CASH_BUCKET_REQUIRED")
            cash[cash_bucket] = cash.get(cash_bucket, Decimal("0")) + _decimal(
                payload["amount"]
            )
        elif event_type == "POSITION_OPENING":
            if not instrument_id:
                raise PortfolioV0Error("INSTRUMENT_REQUIRED")
            if instrument_id in positions:
                raise PortfolioV0Error("DUPLICATE_OPENING_POSITION")
            positions[instrument_id] = {
                "quantity": _decimal(payload["quantity"]),
                "valuation_price": (
                    None
                    if payload.get("valuation_price") is None
                    else _decimal(payload["valuation_price"])
                ),
            }
        elif event_type == "CORPORATE_ACTION_SPLIT":
            if not instrument_id or instrument_id not in positions:
                raise PortfolioV0Error("SPLIT_POSITION_MISSING")
            position = positions[instrument_id]
            before_quantity = _decimal(payload["pre_quantity"])
            before_price = _decimal(payload["pre_reference_price"])
            if position["quantity"] != before_quantity:
                raise PortfolioV0Error("SPLIT_PRE_QUANTITY_MISMATCH")
            if position["valuation_price"] != before_price:
                raise PortfolioV0Error("SPLIT_PRE_PRICE_MISMATCH")
            numerator = _decimal(payload["numerator"])
            denominator = _decimal(payload["denominator"])
            if numerator <= 0 or denominator <= 0:
                raise PortfolioV0Error("SPLIT_RATIO_INVALID")
            after_quantity = before_quantity * numerator / denominator
            after_price = before_price * denominator / numerator
            before_value = before_quantity * before_price
            after_value = after_quantity * after_price
            residual = after_value - before_value
            if residual != 0:
                raise PortfolioV0Error("SPLIT_VALUE_NOT_PRESERVED")
            split_residuals.append(residual)
            position["quantity"] = after_quantity
            position["valuation_price"] = after_price
        elif event_type == "FILL_COMPLETED":
            fill = payload["fill"]
            if fill["side"] != "BUY":
                raise PortfolioV0Error("UNSUPPORTED_FILL_SIDE")
            quantity = _decimal(fill["quantity"])
            price = _decimal(fill["price"])
            fee = _decimal(fill["fee"])
            bucket = fill["cash_bucket"]
            required_cash = quantity * price + fee
            available = cash.get(bucket, Decimal("0"))
            if available < required_cash:
                raise PortfolioV0Error("INSUFFICIENT_CLASSIFIED_CASH")
            cash[bucket] = available - required_cash
            position = positions.setdefault(
                fill["instrument_id"],
                {"quantity": Decimal("0"), "valuation_price": None},
            )
            position["quantity"] = _decimal(position["quantity"] or "0") + quantity
            position["valuation_price"] = price
        elif event_type in {
            "PORTFOLIO_AIM_CONFIRMED",
            "ORDER_CREATED",
            "LATER_OBSERVATION_ADMITTED",
            "CERTIFICATION_RECORDED",
        }:
            continue
        else:
            raise PortfolioV0Error(f"UNSUPPORTED_EVENT_TYPE:{event_type}")

    cash_rows = [
        {"bucket": bucket, "amount": _decimal_text(amount)}
        for bucket, amount in sorted(cash.items())
    ]
    position_rows: list[dict[str, Any]] = []
    valuation_pending = False
    position_value = Decimal("0")
    for instrument_id, position in sorted(positions.items()):
        quantity = _decimal(position["quantity"] or "0")
        price = position["valuation_price"]
        if price is None:
            market_value = None
            valuation_pending = True
        else:
            market_value = quantity * _decimal(price)
            position_value += market_value
        position_rows.append(
            {
                "instrument_id": instrument_id,
                "quantity": _decimal_text(quantity),
                "valuation_price": None if price is None else _decimal_text(price),
                "market_value": None if market_value is None else _decimal_text(market_value),
            }
        )
    total_cash = sum((_decimal(row["amount"]) for row in cash_rows), Decimal("0"))
    nav = None if valuation_pending else position_value + total_cash
    book = {
        "positions": position_rows,
        "classified_cash": cash_rows,
        "total_cash": _decimal_text(total_cash),
        "position_value": None if valuation_pending else _decimal_text(position_value),
        "nav": None if nav is None else _decimal_text(nav),
        "valuation_status": "VALUATION_PENDING" if valuation_pending else "COMPLETE",
        "split_value_residual": _decimal_text(sum(split_residuals, Decimal("0"))),
        "declared_precision": DECLARED_PRECISION,
    }
    book["book_hash"] = domain_hash(f"{ID_DOMAIN}:BOOK:V1", book)
    return book


def _certification_subject_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in events if row["event_type"] != "CERTIFICATION_RECORDED"]


def certify_workspace(
    workspace: Mapping[str, Any], *, prior_certification_id: str | None = None
) -> dict[str, Any]:
    events = _certification_subject_events(workspace["events"])
    book = reduce_events(events)
    event_ledger_hash = domain_hash(f"{ID_DOMAIN}:EVENT_LEDGER:V1", events)
    order_count = sum(row["event_type"] == "ORDER_CREATED" for row in events)
    fill_count = sum(row["event_type"] == "FILL_COMPLETED" for row in events)
    cash_nonnegative = all(_decimal(row["amount"]) >= 0 for row in book["classified_cash"])
    checks = {
        "event_ids_unique": len({row["event_id"] for row in events}) == len(events),
        "split_value_preserved": book["split_value_residual"] == "0",
        "classified_cash_nonnegative": cash_nonnegative,
        "nav_reconciled": book["valuation_status"] == "COMPLETE" and book["nav"] == "1499",
        "decision_snapshot_present": bool(workspace.get("decision_snapshot")),
        "portfolio_aim_present": bool(workspace.get("portfolio_aim")),
        "exactly_one_order": order_count == 1,
        "exactly_one_fill": fill_count == 1,
        "valuation_complete": book["valuation_status"] == "COMPLETE",
    }
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise PortfolioV0Error(f"CERTIFICATION_CHECK_FAILED:{','.join(failed)}")
    payload = {
        "subject_event_ledger_hash": event_ledger_hash,
        "terminal_book_hash": book["book_hash"],
        "decision_snapshot_id": workspace["decision_snapshot"]["decision_snapshot_id"],
        "portfolio_aim_id": workspace["portfolio_aim"]["portfolio_aim_id"],
        "checks": checks,
        "declared_precision": DECLARED_PRECISION,
        "prior_certification_id": prior_certification_id,
    }
    return _record_with_id("CRT", "certification_id", payload)


def build_draft_workspace() -> dict[str, Any]:
    principal = _instrument("ISSUER:NORTHSTAR:COMMON", "NSTAR", "Northstar Systems", "PRINCIPAL")
    substitute = _instrument("ISSUER:HARBOR:COMMON", "HARBOR", "Harbor Automation", "SUBSTITUTE")
    competitor = _instrument("ISSUER:RIVAL:COMMON", "RIVAL", "Rival Dynamics", "COMPETITOR")
    abstain = _instrument("ISSUER:ORBIT:COMMON", "ORBIT", "Orbit Networks", "ALTERNATIVE")
    benchmark = _instrument("INDEX:BENCH100:TOTAL_RETURN", "BENCH100", "Benchmark 100", "BENCHMARK")
    instruments = [principal, substitute, competitor, abstain]

    evidence = [
        evidence_reference(
            content="Northstar recurring revenue and renewal evidence supports the principal thesis.",
            locator="fixture://northstar/principal-v1",
            observed_at="2026-07-19T12:00:00.000000Z",
        ),
        evidence_reference(
            content="Harbor has positive base-case economics with lower concentration than adding Northstar.",
            locator="fixture://harbor/substitute-v1",
            observed_at="2026-07-19T12:01:00.000000Z",
        ),
        evidence_reference(
            content="Rival leverage breaches the mandate screen and blocks admission.",
            locator="fixture://rival/reject-v1",
            observed_at="2026-07-19T12:02:00.000000Z",
        ),
        evidence_reference(
            content="Orbit evidence is directionally positive but insufficient for a capital decision.",
            locator="fixture://orbit/abstain-v1",
            observed_at="2026-07-19T12:03:00.000000Z",
        ),
    ]
    evd = [row["evidence_reference_id"] for row in evidence]
    reviews = [
        _review(
            instrument=principal,
            relationship="PRINCIPAL_THESIS",
            outcome="ADMIT",
            thesis="Recurring revenue durability remains intact; maintain the principal position.",
            scenario=_scenario("20", "30", "42"),
            evidence_ids=[evd[0]],
            hard_falsifiers=["renewal_rate_below_70_percent"],
            watch_conditions=["order_intake_softens_without_covenant_breach"],
        ),
        _review(
            instrument=substitute,
            relationship="SUBSTITUTE",
            outcome="ADMIT",
            thesis="Harbor is the best incremental use of available cash under the current aim.",
            scenario=_scenario("30", "48", "70"),
            evidence_ids=[evd[1]],
            hard_falsifiers=["net_debt_to_ebitda_above_4"],
            watch_conditions=["margin_compression_below_base_band"],
        ),
        _review(
            instrument=competitor,
            relationship="COMPETITOR",
            outcome="REJECT",
            thesis="Rival is rejected because leverage violates the mandate screen.",
            scenario=_scenario("10", "28", "55"),
            evidence_ids=[evd[2]],
            hard_falsifiers=["mandate_leverage_screen_failed"],
            watch_conditions=[],
        ),
        _review(
            instrument=abstain,
            relationship="ALTERNATIVE",
            outcome="ABSTAIN",
            thesis="Orbit remains observable but the evidence is insufficient for commitment.",
            scenario=_scenario("18", "44", "80"),
            evidence_ids=[evd[3]],
            hard_falsifiers=[],
            watch_conditions=["obtain_customer_concentration_evidence"],
        ),
    ]
    aim = _aim(benchmark["instrument_id"])
    competition = _capital_competition(reviews)
    snapshot = _decision_snapshot(aim=aim, reviews=reviews, competition=competition)

    events = [
        _event(
            0,
            "CASH_OPENING",
            "2026-07-20T08:55:00.000000Z",
            "FIXTURE:CASH:AVAILABLE",
            cash_bucket="AVAILABLE",
            payload={"amount": "975"},
        ),
        _event(
            1,
            "CASH_OPENING",
            "2026-07-20T08:55:00.000000Z",
            "FIXTURE:CASH:RESEARCH_RESERVE",
            cash_bucket="RESEARCH_RESERVE",
            payload={"amount": "25"},
        ),
        _event(
            2,
            "POSITION_OPENING",
            "2026-07-20T08:56:00.000000Z",
            "FIXTURE:POSITION:NSTAR",
            instrument_id=principal["instrument_id"],
            payload={"quantity": "10", "valuation_price": "50"},
        ),
        _event(
            3,
            "CORPORATE_ACTION_SPLIT",
            "2026-07-20T08:57:00.000000Z",
            "FIXTURE:SPLIT:NSTAR:2FOR1",
            instrument_id=principal["instrument_id"],
            payload={
                "numerator": "2",
                "denominator": "1",
                "pre_quantity": "10",
                "pre_reference_price": "50",
            },
        ),
    ]
    workspace = {
        "schema_version": SCHEMA_VERSION,
        "fixture_id": "GV_MICRO_PORTFOLIO_VERTICAL_0",
        "status": "DRAFT_REVIEW",
        "instruments": instruments,
        "benchmark": benchmark,
        "evidence_references": evidence,
        "reviews": reviews,
        "cash_outcome": {
            "outcome": "CASH",
            "classification": ["AVAILABLE", "RESEARCH_RESERVE"],
            "role": "explicit_competing_allocation",
        },
        "portfolio_aim": aim,
        "decision_snapshot": snapshot,
        "events": events,
        "book": reduce_events(events),
        "order": None,
        "fill": None,
        "certification": None,
        "certification_history": [],
        "later_observation": None,
        "explanation": "Awaiting operator confirmation; no order has been created.",
        "claim_boundary": "Deterministic paper fixture only; no alpha or live-capital claim.",
    }
    validate_workspace(workspace, allow_uncertified=True)
    return workspace


def confirm_draft_workspace(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace, allow_uncertified=True)
    if workspace["status"] != "DRAFT_REVIEW":
        raise PortfolioV0Error("DRAFT_CONFIRMATION_REQUIRED")
    result = deepcopy(dict(workspace))
    snapshot_before = canonical_document_bytes(result["decision_snapshot"])
    order = _order(result["decision_snapshot"], result["portfolio_aim"])
    fill = _fill(order)
    events = list(result["events"])
    events.extend(
        [
            _event(
                len(events),
                "PORTFOLIO_AIM_CONFIRMED",
                "2026-07-20T09:05:30.000000Z",
                result["portfolio_aim"]["portfolio_aim_id"],
                payload={"portfolio_aim_id": result["portfolio_aim"]["portfolio_aim_id"]},
            ),
            _event(
                len(events) + 1,
                "ORDER_CREATED",
                order["created_at"],
                order["order_id"],
                instrument_id=order["instrument_id"],
                payload={"order": order},
            ),
            _event(
                len(events) + 2,
                "FILL_COMPLETED",
                fill["filled_at"],
                fill["fill_id"],
                instrument_id=fill["instrument_id"],
                cash_bucket=fill["cash_bucket"],
                payload={"fill": fill},
            ),
        ]
    )
    result["events"] = events
    result["order"] = order
    result["fill"] = fill
    result["book"] = reduce_events(events)
    result["status"] = "CERTIFIED"
    result["explanation"] = (
        "Harbor won deterministic capital competition; one paper BUY order and fill "
        "were recorded. Northstar's 2:1 split preserved value exactly."
    )
    certification = certify_workspace(result)
    result["certification"] = certification
    result["events"].append(
        _event(
            len(result["events"]),
            "CERTIFICATION_RECORDED",
            "2026-07-20T09:07:00.000000Z",
            certification["certification_id"],
            payload={"certification_id": certification["certification_id"]},
        )
    )
    result["book"] = reduce_events(result["events"])
    if canonical_document_bytes(result["decision_snapshot"]) != snapshot_before:
        raise PortfolioV0Error("DECISION_SNAPSHOT_MUTATED")
    validate_workspace(result)
    return result


def admit_watch_observation(workspace: Mapping[str, Any]) -> dict[str, Any]:
    validate_workspace(workspace)
    if workspace["status"] != "CERTIFIED":
        raise PortfolioV0Error("CERTIFIED_WORKSPACE_REQUIRED")
    result = deepcopy(dict(workspace))
    original_snapshot = canonical_document_bytes(result["decision_snapshot"])
    original_aim_id = result["portfolio_aim"]["portfolio_aim_id"]
    prior = deepcopy(result["certification"])
    observation = evidence_reference(
        content=(
            "Northstar order intake slowed 2 percent, inside the declared WATCH band; "
            "no accounting break, mandate breach, or thesis hard falsifier fired."
        ),
        locator="fixture://northstar/later-watch-v1",
        observed_at="2026-07-21T12:00:00.000000Z",
    )
    result["evidence_references"].append(observation)
    result["events"].append(
        _event(
            len(result["events"]),
            "LATER_OBSERVATION_ADMITTED",
            "2026-07-21T12:00:00.000000Z",
            observation["evidence_reference_id"],
            instrument_id=result["instruments"][0]["instrument_id"],
            payload={
                "evidence_reference_id": observation["evidence_reference_id"],
                "classification": "WATCH",
                "hard_falsifier_fired": False,
                "portfolio_aim_id_before": original_aim_id,
                "portfolio_aim_id_after": original_aim_id,
            },
        )
    )
    result["later_observation"] = {
        "evidence_reference_id": observation["evidence_reference_id"],
        "classification": "WATCH",
        "hard_falsifier_fired": False,
        "aim_changed": False,
    }
    result["certification_history"] = [*result["certification_history"], prior]
    result["status"] = "OBSERVED_WATCH_AIM_UNCHANGED"
    result["explanation"] = (
        "The later observation changed the evidence set but not the portfolio aim: "
        "it remained inside the WATCH band and no hard falsifier fired."
    )
    certification = certify_workspace(
        result, prior_certification_id=prior["certification_id"]
    )
    result["certification"] = certification
    result["events"].append(
        _event(
            len(result["events"]),
            "CERTIFICATION_RECORDED",
            "2026-07-21T12:01:00.000000Z",
            certification["certification_id"],
            payload={"certification_id": certification["certification_id"]},
        )
    )
    result["book"] = reduce_events(result["events"])
    if result["portfolio_aim"]["portfolio_aim_id"] != original_aim_id:
        raise PortfolioV0Error("WATCH_OBSERVATION_CHANGED_AIM")
    if canonical_document_bytes(result["decision_snapshot"]) != original_snapshot:
        raise PortfolioV0Error("WATCH_OBSERVATION_MUTATED_SNAPSHOT")
    validate_workspace(result)
    return result


def _verify_id(record: Mapping[str, Any], *, kind: str, id_key: str) -> None:
    try:
        verify_record_id(record, kind=kind, id_key=id_key)
    except CustodyContractError as exc:
        raise PortfolioV0Error(str(exc)) from exc


def validate_workspace(
    workspace: Mapping[str, Any], *, allow_uncertified: bool = False
) -> None:
    if workspace.get("schema_version") != SCHEMA_VERSION:
        raise PortfolioV0Error("WORKSPACE_SCHEMA_INVALID")
    instruments = list(workspace.get("instruments") or [])
    if len(instruments) != 4:
        raise PortfolioV0Error("FOUR_REVIEWED_SECURITIES_REQUIRED")
    all_instruments = [*instruments, workspace.get("benchmark")]
    for row in all_instruments:
        if not isinstance(row, Mapping):
            raise PortfolioV0Error("INSTRUMENT_OBJECT_REQUIRED")
        try:
            verify_instrument_identity(row)
        except CustodyContractError as exc:
            raise PortfolioV0Error(str(exc)) from exc
    outcomes = {row["outcome"] for row in workspace.get("reviews") or []}
    if not {"ADMIT", "REJECT", "ABSTAIN"}.issubset(outcomes):
        raise PortfolioV0Error("DECISION_OUTCOME_COVERAGE_INCOMPLETE")
    if workspace.get("cash_outcome", {}).get("outcome") != "CASH":
        raise PortfolioV0Error("CASH_OUTCOME_REQUIRED")

    for evidence in workspace.get("evidence_references") or []:
        try:
            verify_evidence_reference(evidence)
        except CustodyContractError as exc:
            raise PortfolioV0Error(str(exc)) from exc

    _verify_id(workspace["portfolio_aim"], kind="AIM", id_key="portfolio_aim_id")
    _verify_id(
        workspace["decision_snapshot"], kind="DSN", id_key="decision_snapshot_id"
    )
    workspace_events = list(workspace.get("events") or [])
    try:
        CanonicalEventStream(workspace_events)
    except (CustodyContractError, CustodyEventError) as exc:
        raise PortfolioV0Error(str(exc)) from exc
    rebuilt = reduce_events(workspace_events)
    if canonical_document_bytes(rebuilt) != canonical_document_bytes(workspace["book"]):
        raise PortfolioV0Error("BOOK_REDUCTION_MISMATCH")

    status = workspace.get("status")
    if status == "DRAFT_REVIEW":
        if not allow_uncertified:
            raise PortfolioV0Error("UNCERTIFIED_WORKSPACE")
        if workspace.get("order") is not None or workspace.get("fill") is not None:
            raise PortfolioV0Error("DRAFT_HAS_EXECUTION")
        if workspace.get("certification") is not None:
            raise PortfolioV0Error("DRAFT_HAS_CERTIFICATION")
        return
    if status not in {"CERTIFIED", "OBSERVED_WATCH_AIM_UNCHANGED"}:
        raise PortfolioV0Error("WORKSPACE_STATUS_INVALID")
    _verify_id(workspace["order"], kind="ORD", id_key="order_id")
    _verify_id(workspace["fill"], kind="FIL", id_key="fill_id")
    certification = workspace.get("certification")
    if not isinstance(certification, Mapping):
        raise PortfolioV0Error("CERTIFICATION_REQUIRED")
    expected = certify_workspace(
        workspace, prior_certification_id=certification.get("prior_certification_id")
    )
    if canonical_document_bytes(expected) != canonical_document_bytes(certification):
        raise PortfolioV0Error("CERTIFICATION_MISMATCH")
    if status == "OBSERVED_WATCH_AIM_UNCHANGED":
        observation = workspace.get("later_observation") or {}
        if observation.get("classification") != "WATCH":
            raise PortfolioV0Error("WATCH_OBSERVATION_REQUIRED")
        if observation.get("hard_falsifier_fired") or observation.get("aim_changed"):
            raise PortfolioV0Error("WATCH_OBSERVATION_STATE_INVALID")
        if len(workspace.get("certification_history") or []) != 1:
            raise PortfolioV0Error("PRIOR_CERTIFICATION_HISTORY_REQUIRED")
