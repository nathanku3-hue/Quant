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
    AUTHORITATIVE_PORTFOLIO_EVENT_TYPES,
    NON_AUTHORITATIVE_PORTFOLIO_EVENT_TYPES,
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
    build_certified_source_prefix_proof,
    build_equity_extension,
    build_no_market_identity,
    build_no_market_source_state_digest,
    build_pit_identity,
    validate_portfolio_source_event,
    with_proposal_id,
)


REAL_MU_OPERATED_MODULE_ID = "GV_REAL_MU_OPERATED"


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


def _decision_free_evidence_references(
    evidence_identity: Mapping[str, Any],
) -> tuple[EvidenceReference, EvidenceReference]:
    source_families = _required_list(
        evidence_identity.get("source_families"),
        code="PIT_EVIDENCE_SOURCE_FAMILIES_REQUIRED",
    )
    bindings = _required_mapping(
        evidence_identity.get("source_bindings"),
        code="PIT_EVIDENCE_BINDINGS_REQUIRED",
    )
    mu_statement_ids = tuple(
        str(value)
        for value in _required_list(
            evidence_identity.get("mu_statement_ids"),
            code="PIT_MU_STATEMENT_IDS_REQUIRED",
        )
    )
    nvda_fact_ids = tuple(
        str(value)
        for value in _required_list(
            evidence_identity.get("nvda_fact_ids"),
            code="PIT_NVDA_FACT_IDS_REQUIRED",
        )
    )
    source_family_by_accession = {
        str(source_family).removeprefix("SEC:"): str(source_family)
        for source_family in source_families
    }
    mu_source_family = source_family_by_accession.get("0000723125-26-000015")
    nvda_source_family = source_family_by_accession.get("0001045810-26-000052")
    if (
        len(source_families) != 2
        or len(source_family_by_accession) != 2
        or mu_source_family is None
        or nvda_source_family is None
        or not mu_statement_ids
        or not nvda_fact_ids
    ):
        raise PitAdapterError("PIT_DECISION_FREE_EVIDENCE_PROVENANCE_INCOMPLETE")
    mu_digest = str(bindings.get("mu_claim_evaluation_hash") or "")
    nvda_digest = str(bindings.get("nvda_fact_set_hash") or "")
    return (
        EvidenceReference(
            evidence_id="MU_CLAIM_EVALUATION",
            sha256_digest=mu_digest,
            source_identity=(
                f"repo://data/gv_v2_b0b/mu_0000723125-26-000015/"
                f"claim_evaluation.json#source_family={mu_source_family}"
                f"&statement_ids={','.join(mu_statement_ids)}"
            ),
        ),
        EvidenceReference(
            evidence_id="NVDA_FACT_SET",
            sha256_digest=nvda_digest,
            source_identity=(
                f"repo://data/gv_v2_alpha0/"
                f"family_two_nvda_0001045810-26-000052/fact_set.json"
                f"#source_family={nvda_source_family}"
                f"&fact_ids={','.join(nvda_fact_ids)}"
            ),
        ),
    )


def _certified_prefix(
    workspace: Mapping[str, Any],
) -> tuple[
    Mapping[str, Any],
    list[Mapping[str, Any]],
    Mapping[str, Any] | None,
]:
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
    return certification, prefix, prior


def _validated_authoritative_head(
    certified_prefix: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Validate exact source-event bytes and return the final economic/decision fact."""

    allowed_types = (
        AUTHORITATIVE_PORTFOLIO_EVENT_TYPES
        | NON_AUTHORITATIVE_PORTFOLIO_EVENT_TYPES
    )
    authoritative_head: Mapping[str, Any] | None = None
    for row in certified_prefix:
        event_type = row.get("event_type")
        if event_type not in allowed_types:
            raise PitAdapterError("PIT_CERTIFIED_PREFIX_EVENT_TYPE_UNRECOGNIZED")
        try:
            validate_portfolio_source_event(row)
        except (TypeError, ValueError) as exc:
            raise PitAdapterError("PIT_CERTIFIED_PREFIX_EVENT_INVALID") from exc
        if event_type in AUTHORITATIVE_PORTFOLIO_EVENT_TYPES:
            authoritative_head = row
    if authoritative_head is None:
        raise PitAdapterError("PIT_CERTIFIED_PREFIX_AUTHORITATIVE_HEAD_REQUIRED")
    return authoritative_head


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
    certification, certified_prefix, prior_certification = _certified_prefix(
        source_workspace
    )
    certified_head = _validated_authoritative_head(certified_prefix)
    source_proof = build_certified_source_prefix_proof(
        source_workspace=source_workspace,
        certified_prefix=certified_prefix,
        certification=certification,
        prior_certification=prior_certification,
        decision_snapshot_id=str(certification.get("decision_snapshot_id") or ""),
        portfolio_aim_id=str(certification.get("portfolio_aim_id") or ""),
    )
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
    direct_source_evidence = _decision_free_evidence_references(
        operated_evidence_identity
    )
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
    positions = _required_list(book.get("positions"), code="PIT_POSITIONS_REQUIRED")
    orders = _required_list(source_workspace.get("orders"), code="PIT_ORDERS_REQUIRED")
    fills = _required_list(source_workspace.get("fills"), code="PIT_FILLS_REQUIRED")
    certified_head_event_id = str(certified_head.get("event_id") or "")
    certified_head_timestamp_utc = str(certified_head.get("effective_at") or "")
    residual = Decimal(str(book.get("unexplained_residual")))
    source_state_digest = build_no_market_source_state_digest(
        source_proof=source_proof,
        certified_book_id=certified_book_id,
        certified_book_head_event_id=certified_head_event_id,
        certified_book_head_timestamp_utc=certified_head_timestamp_utc,
        certified_book_hash=certified_book_hash,
        positions_count=len(positions),
        orders_count=len(orders),
        fills_count=len(fills),
        unexplained_residual=residual,
        proposal_target_quantities=target_quantities,
        consumes_notional_conversion=False,
        consumes_weight_conversion=False,
        consumes_price_data=False,
        consumes_reference_price=False,
        claims_yield=False,
        claims_market_return=False,
    )
    facts = NoMarketValidationFacts(
        source_proof=source_proof,
        certified_book_id=certified_book_id,
        certified_book_head_event_id=certified_head_event_id,
        certified_book_head_timestamp_utc=certified_head_timestamp_utc,
        certified_book_hash=certified_book_hash,
        positions_count=len(positions),
        orders_count=len(orders),
        fills_count=len(fills),
        unexplained_residual=residual,
        proposal_target_quantities=target_quantities,
        consumes_notional_conversion=False,
        consumes_weight_conversion=False,
        consumes_price_data=False,
        consumes_reference_price=False,
        claims_yield=False,
        claims_market_return=False,
        source_state_digest=source_state_digest,
    )
    no_market_identity = build_no_market_identity(facts)
    pit_identity = build_pit_identity(
        certified_book_id=certified_book_id,
        certified_book_head_event_id=facts.certified_book_head_event_id,
        certified_book_head_timestamp_utc=certified_head_timestamp_utc,
        evidence_set_id=evidence_set_id,
        market_snapshot_id=no_market_identity,
        as_of_utc=certified_head_timestamp_utc,
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
        module_id=REAL_MU_OPERATED_MODULE_ID,
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
        supporting_evidence=(common_evidence, *direct_source_evidence),
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
        supporting_evidence=(common_evidence, *direct_source_evidence),
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
