"""Deterministic four-security micro-portfolio product integrator.

The module owns the bounded acceptance fixture, workspace orchestration, and
certification. Strategy, execution events, and accounting remain authoritative
in their dedicated modules. No provider, broker, network, optimization, or
live-capital work is performed.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.admission import (
    StrategyAdmissionError,
    build_decision_snapshot,
    decision_projections,
    validate_decision_projections,
)
from gv_portfolio_v0.book import (
    PortfolioBookError,
    build_portfolio_book,
    certification_eligible,
)
from gv_portfolio_v0.execution import (
    ExecutionError,
    emit_execution_chain,
    portfolio_book_event,
    validate_execution_chain,
)
from gv_portfolio_v0.thesis import (
    StrategyThesisError,
    living_thesis_lite,
    scenario_range,
    unchanged_aim_watch_observation,
)

SCHEMA_VERSION = "gv_portfolio_v0_workspace_v2"
ID_DOMAIN = "GV-PORTFOLIO-V0"
DECLARED_PRECISION = "0.01"


class PortfolioV0Error(ValueError):
    """Fail-closed micro-portfolio error."""


def _identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", dict(payload))


def _record_with_id(kind: str, id_key: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    return {id_key: _identifier(kind, body), **body}


def _instrument(
    permanent_key: str,
    symbol: str,
    name: str,
    role: str,
) -> dict[str, Any]:
    identity = {
        "namespace": "GV_SYNTHETIC_PERMANENT_V0",
        "permanent_key": permanent_key,
        "security_class": "COMMON_STOCK",
    }
    return {
        "instrument_id": _identifier("INS", identity),
        **identity,
        "symbol": symbol,
        "name": name,
        "role": role,
    }


def evidence_reference(
    *, content: str, locator: str, observed_at: str, media_type: str = "text/plain"
) -> dict[str, Any]:
    raw = content.encode("utf-8")
    content_sha256 = hashlib.sha256(raw).hexdigest()
    identity = {
        "content_sha256": content_sha256,
        "media_type": media_type,
        "locator": locator,
        "observed_at": observed_at,
    }
    return {
        "evidence_reference_id": _identifier("EVD", identity),
        **identity,
        "content": content,
    }


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
    """Bind all vertical events to Stream 4's frozen executable seam."""

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
        raise PortfolioV0Error(str(exc)) from exc


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
    try:
        return scenario_range(bear_value=bear, base_value=base, bull_value=bull)
    except StrategyThesisError as exc:
        raise PortfolioV0Error(str(exc)) from exc


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
    try:
        return {
            "instrument_id": instrument["instrument_id"],
            "symbol": instrument["symbol"],
            "relationship": relationship,
            "outcome": outcome,
            "living_thesis_lite": living_thesis_lite(
                principal_claim=thesis,
                scenario=scenario,
                evidence_reference_ids=evidence_ids,
                hard_falsifiers=hard_falsifiers,
                watch_conditions=watch_conditions,
            ),
        }
    except StrategyThesisError as exc:
        raise PortfolioV0Error(str(exc)) from exc


def _competition_candidates(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return fixture inputs; Strategy recomputes scores, eligibility, and winner."""

    by_symbol = {row["symbol"]: row for row in reviews}
    return [
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


def _decision_snapshot(
    *,
    aim: Mapping[str, Any],
    reviews: list[dict[str, Any]],
    cash_outcome: Mapping[str, Any],
    competition_candidates: Iterable[Mapping[str, Any]],
    evidence_reference_ids: Iterable[str],
) -> dict[str, Any]:
    try:
        return build_decision_snapshot(
            created_at="2026-07-20T09:05:00.000000Z",
            portfolio_aim_id=aim["portfolio_aim_id"],
            reviews=reviews,
            cash_outcome=cash_outcome,
            competition_candidates=competition_candidates,
            available_evidence_reference_ids=evidence_reference_ids,
            selected_quantity="5",
            reference_price="40",
            fee="1",
        )
    except StrategyAdmissionError as exc:
        raise PortfolioV0Error(str(exc)) from exc


def reduce_events(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return Stream 2's reconciled PortfolioBook as the sole vertical book."""

    try:
        return build_portfolio_book(events)
    except PortfolioBookError as exc:
        raise PortfolioV0Error(str(exc)) from exc


def _certification_subject_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in events if row["event_type"] != "CERTIFICATION_RECORDED"]


def certify_workspace(
    workspace: Mapping[str, Any], *, prior_certification_id: str | None = None
) -> dict[str, Any]:
    events = _certification_subject_events(workspace["events"])
    book = reduce_events(events)
    evidence_ids = [
        row["evidence_reference_id"] for row in workspace["evidence_references"]
    ]
    try:
        validate_decision_projections(
            workspace["decision_snapshot"],
            reviews_projection=workspace["reviews"],
            cash_projection=workspace["cash_outcome"],
            available_evidence_reference_ids=evidence_ids,
        )
        execution_events = [
            row
            for row in events
            if row["event_type"]
            in {
                "PORTFOLIO_AIM_CONFIRMED",
                "PORTFOLIO_TRANSITION_PLANNED",
                "ORDER_CREATED",
                "FILL_COMPLETED",
            }
        ]
        execution_chain = validate_execution_chain(
            workspace["decision_snapshot"],
            workspace["portfolio_aim"],
            execution_events,
            order=workspace.get("order"),
            fill=workspace.get("fill"),
        )
    except (StrategyAdmissionError, ExecutionError) as exc:
        raise PortfolioV0Error(str(exc)) from exc

    event_ledger_hash = domain_hash(f"{ID_DOMAIN}:EVENT_LEDGER:V1", events)
    order_count = sum(row["event_type"] == "ORDER_CREATED" for row in events)
    fill_count = sum(row["event_type"] == "FILL_COMPLETED" for row in events)
    transition_count = sum(
        row["event_type"] == "PORTFOLIO_TRANSITION_PLANNED" for row in events
    )
    checks = {
        "event_ids_unique": len({row["event_id"] for row in events}) == len(events),
        "split_value_preserved": book["split_value_residual"] == "0",
        "classified_cash_nonnegative": book["classified_cash_nonnegative"] is True,
        "nav_reconciled": book["nav"] == "1499",
        "decision_snapshot_present": bool(workspace.get("decision_snapshot")),
        "portfolio_aim_present": bool(workspace.get("portfolio_aim")),
        "exactly_one_transition": transition_count == 1,
        "exactly_one_order": order_count == 1,
        "exactly_one_fill": fill_count == 1,
        "valuation_complete": book["valuation_status"] == "COMPLETE",
        "book_reconciled": certification_eligible(book),
        "unexplained_residual_zero": book["unexplained_residual"] == "0",
        "execution_costs_explicit": book["total_costs"] == "1",
        "execution_chain_valid": bool(execution_chain.get("fill_id")),
    }
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise PortfolioV0Error(f"CERTIFICATION_CHECK_FAILED:{','.join(failed)}")
    payload = {
        "subject_event_ledger_hash": event_ledger_hash,
        "terminal_book_hash": book["book_hash"],
        "decision_snapshot_id": workspace["decision_snapshot"]["decision_snapshot_id"],
        "portfolio_aim_id": workspace["portfolio_aim"]["portfolio_aim_id"],
        "transition_event_id": execution_chain["transition_event_id"],
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
    cash_outcome = {
        "outcome": "CASH",
        "classification": ["AVAILABLE", "RESEARCH_RESERVE"],
        "role": "explicit_competing_allocation",
    }
    snapshot = _decision_snapshot(
        aim=aim,
        reviews=reviews,
        cash_outcome=cash_outcome,
        competition_candidates=_competition_candidates(reviews),
        evidence_reference_ids=evd,
    )
    reviews, cash_outcome = decision_projections(snapshot)

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
        "cash_outcome": cash_outcome,
        "portfolio_aim": aim,
        "decision_snapshot": snapshot,
        "events": events,
        "book": reduce_events(events),
        "transition_event": None,
        "execution_authority_chain": None,
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
    selected_instrument_id = result["decision_snapshot"]["selected_instrument_id"]
    selected_position = next(
        (
            row
            for row in result["book"]["positions"]
            if row["instrument_id"] == selected_instrument_id
        ),
        None,
    )
    current_quantity = "0" if selected_position is None else selected_position["quantity"]
    try:
        execution = emit_execution_chain(
            result["decision_snapshot"],
            result["portfolio_aim"],
            current_quantity=current_quantity,
            cash_bucket="AVAILABLE",
            start_sequence=len(result["events"]),
            aim_confirmed_at="2026-07-20T09:05:30.000000Z",
            transition_effective_at="2026-07-20T09:05:45.000000Z",
            order_created_at="2026-07-20T09:06:00.000000Z",
            filled_at="2026-07-20T09:06:01.000000Z",
        )
    except ExecutionError as exc:
        raise PortfolioV0Error(str(exc)) from exc
    events = [*result["events"], *execution["events"]]
    result["events"] = events
    result["transition_event"] = execution["transition_event"]
    result["execution_authority_chain"] = execution["authority_chain"]
    result["order"] = execution["order"]
    result["fill"] = execution["fill"]
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
        observed_at="2026-08-20T12:00:00.000000Z",
    )
    result["evidence_references"].append(observation)
    principal_review = next(
        row for row in result["reviews"] if row["relationship"] == "PRINCIPAL_THESIS"
    )
    try:
        observation_state = unchanged_aim_watch_observation(
            living_thesis=principal_review["living_thesis_lite"],
            available_evidence_reference_ids=[
                row["evidence_reference_id"] for row in result["evidence_references"]
            ],
            evidence_reference_id=observation["evidence_reference_id"],
            watch_condition_matches=[
                "order_intake_softens_without_covenant_breach"
            ],
            hard_falsifier_matches=[],
            portfolio_aim_id_before=original_aim_id,
            portfolio_aim_id_after=original_aim_id,
        )
    except StrategyThesisError as exc:
        raise PortfolioV0Error(str(exc)) from exc
    result["events"].append(
        _event(
            len(result["events"]),
            "LATER_OBSERVATION_ADMITTED",
            "2026-08-20T12:00:00.000000Z",
            observation["evidence_reference_id"],
            instrument_id=result["instruments"][0]["instrument_id"],
            payload=observation_state,
        )
    )
    result["later_observation"] = observation_state
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
            "2026-08-20T12:01:00.000000Z",
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
    body = {key: value for key, value in record.items() if key != id_key}
    expected = _identifier(kind, body)
    if record.get(id_key) != expected:
        raise PortfolioV0Error(f"IDENTITY_MISMATCH:{id_key}")


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
        identity = {
            "namespace": row["namespace"],
            "permanent_key": row["permanent_key"],
            "security_class": row["security_class"],
        }
        if row["instrument_id"] != _identifier("INS", identity):
            raise PortfolioV0Error("INSTRUMENT_ID_MISMATCH")
    outcomes = {row["outcome"] for row in workspace.get("reviews") or []}
    if not {"ADMIT", "REJECT", "ABSTAIN"}.issubset(outcomes):
        raise PortfolioV0Error("DECISION_OUTCOME_COVERAGE_INCOMPLETE")
    if workspace.get("cash_outcome", {}).get("outcome") != "CASH":
        raise PortfolioV0Error("CASH_OUTCOME_REQUIRED")

    for evidence in workspace.get("evidence_references") or []:
        raw_hash = hashlib.sha256(evidence["content"].encode("utf-8")).hexdigest()
        if raw_hash != evidence["content_sha256"]:
            raise PortfolioV0Error("EVIDENCE_CONTENT_HASH_MISMATCH")
        identity = {
            "content_sha256": evidence["content_sha256"],
            "media_type": evidence["media_type"],
            "locator": evidence["locator"],
            "observed_at": evidence["observed_at"],
        }
        if evidence["evidence_reference_id"] != _identifier("EVD", identity):
            raise PortfolioV0Error("EVIDENCE_REFERENCE_ID_MISMATCH")

    _verify_id(workspace["portfolio_aim"], kind="AIM", id_key="portfolio_aim_id")
    evidence_ids = [
        row["evidence_reference_id"] for row in workspace["evidence_references"]
    ]
    try:
        validate_decision_projections(
            workspace["decision_snapshot"],
            reviews_projection=workspace["reviews"],
            cash_projection=workspace["cash_outcome"],
            available_evidence_reference_ids=evidence_ids,
        )
    except StrategyAdmissionError as exc:
        raise PortfolioV0Error(str(exc)) from exc
    workspace_events = list(workspace.get("events") or [])
    workspace_sequences = [event["sequence"] for event in workspace_events]
    if workspace_sequences != list(range(len(workspace_events))):
        raise PortfolioV0Error("EVENT_SEQUENCE_NOT_CONTIGUOUS")
    for event in workspace_events:
        _verify_id(event, kind="EVT", id_key="event_id")
    rebuilt = reduce_events(workspace_events)
    if canonical_document_bytes(rebuilt) != canonical_document_bytes(workspace["book"]):
        raise PortfolioV0Error("BOOK_REDUCTION_MISMATCH")

    status = workspace.get("status")
    if status == "DRAFT_REVIEW":
        if not allow_uncertified:
            raise PortfolioV0Error("UNCERTIFIED_WORKSPACE")
        if any(
            workspace.get(key) is not None
            for key in (
                "transition_event",
                "execution_authority_chain",
                "order",
                "fill",
            )
        ):
            raise PortfolioV0Error("DRAFT_HAS_EXECUTION")
        if workspace.get("certification") is not None:
            raise PortfolioV0Error("DRAFT_HAS_CERTIFICATION")
        return
    if status not in {"CERTIFIED", "OBSERVED_WATCH_AIM_UNCHANGED"}:
        raise PortfolioV0Error("WORKSPACE_STATUS_INVALID")
    execution_events = [
        row
        for row in workspace_events
        if row["event_type"]
        in {
            "PORTFOLIO_AIM_CONFIRMED",
            "PORTFOLIO_TRANSITION_PLANNED",
            "ORDER_CREATED",
            "FILL_COMPLETED",
        }
    ]
    try:
        execution_chain = validate_execution_chain(
            workspace["decision_snapshot"],
            workspace["portfolio_aim"],
            execution_events,
            order=workspace.get("order"),
            fill=workspace.get("fill"),
        )
    except ExecutionError as exc:
        raise PortfolioV0Error(str(exc)) from exc
    transition_event = workspace.get("transition_event")
    if not isinstance(transition_event, Mapping):
        raise PortfolioV0Error("TRANSITION_EVENT_REQUIRED")
    expected_transition = next(
        row
        for row in execution_events
        if row["event_type"] == "PORTFOLIO_TRANSITION_PLANNED"
    )
    if canonical_document_bytes(transition_event) != canonical_document_bytes(
        expected_transition
    ):
        raise PortfolioV0Error("TRANSITION_EVENT_PROJECTION_MISMATCH")
    if canonical_document_bytes(
        workspace.get("execution_authority_chain")
    ) != canonical_document_bytes(execution_chain):
        raise PortfolioV0Error("EXECUTION_AUTHORITY_CHAIN_MISMATCH")
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
        principal_review = next(
            row
            for row in workspace["reviews"]
            if row["relationship"] == "PRINCIPAL_THESIS"
        )
        try:
            expected_observation = unchanged_aim_watch_observation(
                living_thesis=principal_review["living_thesis_lite"],
                available_evidence_reference_ids=evidence_ids,
                evidence_reference_id=observation.get("evidence_reference_id"),
                watch_condition_matches=observation.get("watch_condition_matches") or [],
                hard_falsifier_matches=observation.get("hard_falsifier_matches") or [],
                portfolio_aim_id_before=observation.get("portfolio_aim_id_before"),
                portfolio_aim_id_after=observation.get("portfolio_aim_id_after"),
            )
        except StrategyThesisError as exc:
            raise PortfolioV0Error(str(exc)) from exc
        if canonical_document_bytes(observation) != canonical_document_bytes(
            expected_observation
        ):
            raise PortfolioV0Error("WATCH_OBSERVATION_STATE_INVALID")
        admitted_events = [
            row
            for row in workspace_events
            if row["event_type"] == "LATER_OBSERVATION_ADMITTED"
        ]
        if len(admitted_events) != 1 or canonical_document_bytes(
            admitted_events[0]["payload"]
        ) != canonical_document_bytes(expected_observation):
            raise PortfolioV0Error("WATCH_OBSERVATION_EVENT_MISMATCH")
        if len(workspace.get("certification_history") or []) != 1:
            raise PortfolioV0Error("PRIOR_CERTIFICATION_HISTORY_REQUIRED")
