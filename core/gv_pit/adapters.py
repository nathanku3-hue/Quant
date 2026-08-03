"""Verified adapters for the first real all-capital PIT episode.

Adapters translate existing immutable repository objects into neutral contracts.
They do not decide eligibility, append governance facts, persist state, or
consume market observations for the current cash-only episode.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_v2_mu_nvda_reconciliation import load_verified_mu_nvda_reconciliation
from core.gv_v2_mu_nvda_shadow_decision import (
    load_mu_nvda_shadow_decision,
    verify_mu_nvda_shadow_decision,
)
from gv_portfolio_v0.operated_scenarios import REAL_MU_PROSPECTIVE_SCENARIO_ID
from gv_portfolio_v0.prospective import (
    build_prospective_workspace,
    validate_prospective_workspace,
)
from gv_portfolio_v0.replay import certify_replay_prefix

from core.gv_pit.contracts import (
    CapitalProposal,
    CashBaselinePayloadV1,
    CashBucketAmount,
    EquityFundamentalPayloadV1,
    EvidenceReference,
    InstrumentTarget,
    InstrumentUnit,
    LotSizePolicy,
    NoMarketValidationFacts,
    NumericNormalizationPolicy,
    PointInTimeIdentity,
    ProposalOutcome,
    RoundingMode,
    TargetIntent,
    build_cash_extension,
    build_equity_extension,
    build_no_market_identity,
    build_pit_identity,
    with_proposal_id,
)


class PitAdapterError(ValueError):
    """Fail-closed source mapping error."""


@dataclass(frozen=True, slots=True)
class RealPitSourceBundle:
    pit_identity: PointInTimeIdentity
    proposals: tuple[CapitalProposal, ...]
    no_market_facts: NoMarketValidationFacts
    certified_nav: Decimal
    classified_cash: tuple[CashBucketAmount, ...]
    certification_id: str
    certified_prefix_event_count: int


def _required_mapping(value: object, *, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PitAdapterError(code)
    return value


def _required_list(value: object, *, code: str) -> list[Any]:
    if not isinstance(value, list):
        raise PitAdapterError(code)
    return value


def _decision_free_evidence_identity(
    reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    corroboration = reconciliation.get("corroboration") or []
    mu_statement_ids = sorted(
        {
            str(statement_id)
            for row in corroboration
            for statement_id in row.get("mu_statement_ids", [])
        }
    )
    nvda_fact_ids = sorted(
        {
            str(fact_id)
            for row in corroboration
            for fact_id in row.get("nvda_fact_ids", [])
        }
    )
    bindings = _required_mapping(
        reconciliation.get("source_bindings"),
        code="PIT_EVIDENCE_BINDINGS_REQUIRED",
    )
    return {
        "source_families": list(reconciliation.get("source_families") or []),
        "source_bindings": {
            "mu_claim_evaluation_hash": bindings.get("mu_claim_evaluation_hash"),
            "nvda_fact_set_hash": bindings.get("nvda_fact_set_hash"),
        },
        "mu_statement_ids": mu_statement_ids,
        "nvda_fact_ids": nvda_fact_ids,
    }


def _certified_prefix(
    workspace: Mapping[str, Any],
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], Mapping[str, Any]]:
    events = _required_list(workspace.get("events"), code="PIT_EVENTS_REQUIRED")
    certification = _required_mapping(
        workspace.get("certification"), code="PIT_CERTIFICATION_REQUIRED"
    )
    certification_id = certification.get("certification_id")
    markers = [
        row
        for row in events
        if isinstance(row, Mapping)
        and row.get("event_type") == "CERTIFICATION_RECORDED"
        and row.get("source_identity") == certification_id
    ]
    if len(markers) != 1:
        raise PitAdapterError("PIT_ACTIVE_CERTIFICATION_MARKER_REQUIRED")
    marker = markers[0]
    marker_sequence = marker.get("sequence")
    if not isinstance(marker_sequence, int) or marker_sequence <= 0:
        raise PitAdapterError("PIT_CERTIFICATION_PREFIX_INVALID")
    if marker_sequence >= len(events) or events[marker_sequence] is not marker:
        raise PitAdapterError("PIT_CERTIFICATION_MARKER_ORDER_INVALID")
    prefix = [
        _required_mapping(row, code="PIT_EVENT_MAPPING_REQUIRED")
        for row in events[:marker_sequence]
    ]
    if not prefix:
        raise PitAdapterError("PIT_CERTIFIED_PREFIX_EMPTY")

    prior: Mapping[str, Any] | None = None
    prior_id = certification.get("prior_certification_id")
    if prior_id is not None:
        history = _required_list(
            workspace.get("certification_history"),
            code="PIT_CERTIFICATION_HISTORY_REQUIRED",
        )
        matching_prior = [
            row
            for row in history
            if isinstance(row, Mapping) and row.get("certification_id") == prior_id
        ]
        if len(matching_prior) != 1:
            raise PitAdapterError("PIT_PRIOR_CERTIFICATION_REQUIRED")
        prior = matching_prior[0]

    expected = certify_replay_prefix(
        prefix,
        decision_snapshot_id=str(certification.get("decision_snapshot_id") or ""),
        portfolio_aim_id=str(certification.get("portfolio_aim_id") or ""),
        prior_certification=prior,
    )
    if canonical_document_bytes(expected) != canonical_document_bytes(dict(certification)):
        raise PitAdapterError("PIT_CERTIFICATION_PREFIX_MISMATCH")
    return certification, prefix, marker


def _equity_target(
    *, instrument_id: str, symbol: str, quantity: Decimal
) -> InstrumentTarget:
    return InstrumentTarget(
        instrument_id=instrument_id,
        symbol=symbol,
        intent=TargetIntent.TARGET_FINAL,
        unit=InstrumentUnit.QUANTITY,
        target_value=quantity,
        normalization=NumericNormalizationPolicy(
            unit_quantum=Decimal("1"),
            rounding_mode=RoundingMode.EXACT,
            currency="USD",
            price_identity=None,
            contract_multiplier=None,
            lot_size_policy=LotSizePolicy.WHOLE_UNITS,
        ),
    )


def build_real_pit_source_bundle(
    *, workspace: Mapping[str, Any] | None = None
) -> RealPitSourceBundle:
    """Build the real MU-operated, MU-shadow, and certified-cash source bundle."""

    source_workspace = (
        build_prospective_workspace(REAL_MU_PROSPECTIVE_SCENARIO_ID)
        if workspace is None
        else deepcopy(dict(workspace))
    )
    validate_prospective_workspace(source_workspace)

    book = _required_mapping(source_workspace.get("book"), code="PIT_BOOK_REQUIRED")
    certification, certified_prefix, _marker = _certified_prefix(source_workspace)
    certified_head = certified_prefix[-1]
    certified_book_hash = str(book.get("book_hash") or "")
    certified_book_id = str(certification.get("terminal_book_hash") or "")
    if not certified_book_hash or certified_book_id != certified_book_hash:
        raise PitAdapterError("PIT_CERTIFIED_BOOK_ID_MISMATCH")

    reconciliation = load_verified_mu_nvda_reconciliation()
    shadow = load_mu_nvda_shadow_decision()
    verify_mu_nvda_shadow_decision(shadow)
    operated_evidence_identity = _decision_free_evidence_identity(reconciliation)
    if canonical_document_bytes(operated_evidence_identity) != canonical_document_bytes(
        shadow["evidence_identity"]
    ):
        raise PitAdapterError("PIT_OPERATED_SHADOW_EVIDENCE_MISMATCH")
    evidence_set_id = str(shadow.get("evidence_hash") or "")
    if not evidence_set_id:
        raise PitAdapterError("PIT_EVIDENCE_SET_ID_REQUIRED")

    reviews = _required_list(source_workspace.get("reviews"), code="PIT_REVIEWS_REQUIRED")
    instruments = _required_list(
        source_workspace.get("instruments"), code="PIT_INSTRUMENTS_REQUIRED"
    )
    if len(reviews) != 1 or len(instruments) != 1:
        raise PitAdapterError("PIT_REAL_MU_SINGLE_INSTRUMENT_REQUIRED")
    review = _required_mapping(reviews[0], code="PIT_REVIEW_REQUIRED")
    instrument = _required_mapping(instruments[0], code="PIT_INSTRUMENT_REQUIRED")
    thesis = _required_mapping(
        review.get("living_thesis_lite"), code="PIT_OPERATED_THESIS_REQUIRED"
    )
    source_evidence_rows = _required_list(
        source_workspace.get("evidence_references"), code="PIT_EVIDENCE_REQUIRED"
    )
    if len(source_evidence_rows) != 1:
        raise PitAdapterError("PIT_REAL_MU_EVIDENCE_COUNT_INVALID")
    source_evidence = _required_mapping(
        source_evidence_rows[0], code="PIT_SOURCE_EVIDENCE_REQUIRED"
    )
    common_evidence = EvidenceReference(
        evidence_id=str(source_evidence.get("evidence_reference_id") or ""),
        sha256_digest=str(source_evidence.get("content_sha256") or ""),
        source_identity=str(source_evidence.get("locator") or ""),
    )
    if not all(
        (
            common_evidence.evidence_id,
            common_evidence.sha256_digest,
            common_evidence.source_identity,
        )
    ):
        raise PitAdapterError("PIT_SOURCE_EVIDENCE_IDENTITY_REQUIRED")

    classified_cash_rows = _required_list(
        book.get("classified_cash"), code="PIT_CLASSIFIED_CASH_REQUIRED"
    )
    classified_cash = tuple(
        CashBucketAmount(
            bucket=str(_required_mapping(row, code="PIT_CASH_ROW_REQUIRED").get("bucket")),
            amount=Decimal(
                str(_required_mapping(row, code="PIT_CASH_ROW_REQUIRED").get("amount"))
            ),
        )
        for row in classified_cash_rows
    )
    nav = Decimal(str(book.get("nav")))

    target_quantities = (
        Decimal(str(review.get("target_quantity"))),
        Decimal("0"),
    )
    facts = NoMarketValidationFacts(
        certified_book_id=certified_book_id,
        certified_book_head_event_id=str(certified_head.get("event_id") or ""),
        certified_book_hash=certified_book_hash,
        positions_count=len(_required_list(book.get("positions"), code="PIT_POSITIONS_REQUIRED")),
        orders_count=len(
            _required_list(source_workspace.get("orders"), code="PIT_ORDERS_REQUIRED")
        ),
        fills_count=len(
            _required_list(source_workspace.get("fills"), code="PIT_FILLS_REQUIRED")
        ),
        unexplained_residual=Decimal(str(book.get("unexplained_residual"))),
        proposal_target_quantities=target_quantities,
        consumes_notional_conversion=False,
        consumes_weight_conversion=False,
        consumes_price_data=False,
        claims_yield=False,
        claims_market_return=False,
    )
    no_market_identity = build_no_market_identity(facts)
    pit_identity = build_pit_identity(
        certified_book_id=certified_book_id,
        certified_book_head_event_id=facts.certified_book_head_event_id,
        evidence_set_id=evidence_set_id,
        market_snapshot_id=no_market_identity,
        as_of_utc=str(certified_head.get("effective_at") or ""),
    )

    instrument_id = str(instrument.get("instrument_id") or "")
    symbol = str(instrument.get("symbol") or "")
    permanent_key = str(instrument.get("permanent_key") or "")
    missing_discriminator = str(reconciliation.get("missing_discriminator") or "")
    operated_target = _equity_target(
        instrument_id=instrument_id,
        symbol=symbol,
        quantity=target_quantities[0],
    )
    shadow_target = _equity_target(
        instrument_id=instrument_id,
        symbol=symbol,
        quantity=target_quantities[1],
    )

    operated = with_proposal_id(
        module_id="GV_REAL_MU_OPERATED",
        module_version="1.0.0",
        pit_identity=pit_identity,
        sleeve_id="CORE_EQUITY",
        outcome=ProposalOutcome(str(review.get("outcome"))),
        targets=(operated_target,),
        risk_targets=(),
        quantitative_boundaries=(
            "target_quantity=0",
            "net_score_bps=0",
            "portfolio_mutation_authorized=false",
        ),
        principal_claim=str(thesis.get("principal_claim") or ""),
        supporting_evidence=(common_evidence,),
        contradicting_evidence=(),
        missing_discriminator=missing_discriminator,
        reason_not_to_act=(
            "Micron-specific physical supply persistence remains unestablished."
        ),
        extension=build_equity_extension(
            EquityFundamentalPayloadV1(
                subject=symbol,
                permanent_key=permanent_key,
                net_score_bps=int(review.get("net_score_bps") or 0),
                missing_discriminator=missing_discriminator,
            )
        ),
    )
    shadow_proposal = with_proposal_id(
        module_id="GV_MU_NVDA_SHADOW",
        module_version="1.0.0",
        pit_identity=pit_identity,
        sleeve_id="CORE_EQUITY",
        outcome=ProposalOutcome(str(shadow.get("outcome"))),
        targets=(shadow_target,),
        risk_targets=(),
        quantitative_boundaries=(
            "target_quantity=0",
            "reads_existing_portfolio_decision=false",
            "portfolio_mutation_authorized=false",
        ),
        principal_claim=str(shadow.get("principal_claim") or ""),
        supporting_evidence=(common_evidence,),
        contradicting_evidence=(),
        missing_discriminator=str(shadow.get("missing_discriminator") or ""),
        reason_not_to_act=str(shadow.get("missing_discriminator") or ""),
        extension=build_equity_extension(
            EquityFundamentalPayloadV1(
                subject=symbol,
                permanent_key=permanent_key,
                net_score_bps=0,
                missing_discriminator=str(
                    shadow.get("missing_discriminator") or ""
                ),
            )
        ),
    )
    cash_evidence = EvidenceReference(
        evidence_id=str(certification.get("certification_id") or ""),
        sha256_digest=str(certification.get("subject_event_ledger_hash") or ""),
        source_identity=str(certification.get("certification_id") or ""),
    )
    cash = with_proposal_id(
        module_id="GV_CERTIFIED_CASH_BASELINE",
        module_version="1.0.0",
        pit_identity=pit_identity,
        sleeve_id="CASH",
        outcome=ProposalOutcome.HOLD_CASH,
        targets=(),
        risk_targets=(),
        quantitative_boundaries=(
            f"nav={format(nav, 'f')}",
            "yield_status=UNAVAILABLE_NO_ADMITTED_SOURCE",
            "market_return_claim=false",
        ),
        principal_claim=(
            "Preserve the certified classified cash baseline while no security "
            "proposal has an admitted non-zero target."
        ),
        supporting_evidence=(cash_evidence,),
        contradicting_evidence=(),
        missing_discriminator="An admitted identified cash-yield source.",
        reason_not_to_act=(
            "No admitted yield or market-return source exists for the cash baseline."
        ),
        extension=build_cash_extension(
            CashBaselinePayloadV1(
                nav=nav,
                classified_cash=classified_cash,
                yield_status="UNAVAILABLE_NO_ADMITTED_SOURCE",
            )
        ),
    )

    return RealPitSourceBundle(
        pit_identity=pit_identity,
        proposals=(operated, shadow_proposal, cash),
        no_market_facts=facts,
        certified_nav=nav,
        classified_cash=classified_cash,
        certification_id=str(certification.get("certification_id") or ""),
        certified_prefix_event_count=len(certified_prefix),
    )
