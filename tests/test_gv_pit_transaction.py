from __future__ import annotations

import ast
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from core.gv_pit.adapters import build_real_pit_source_bundle
from core.gv_pit.contracts import (
    CapitalProposal,
    CashBaselinePayloadV1,
    EquityFundamentalExtensionV1,
    EquityFundamentalPayloadV1,
    InstrumentTarget,
    InstrumentUnit,
    LotSizePolicy,
    NumericNormalizationPolicy,
    PointInTimeIdentity,
    ProposalOutcome,
    RoundingMode,
    TargetIntent,
    build_equity_extension,
    build_no_market_identity,
    build_pit_identity,
    canonical_contract_bytes,
    canonical_value,
    with_proposal_id,
)
from core.gv_pit.governance import (
    GENESIS_DIGEST,
    InMemoryGovernanceStream,
    OpenDecisionEpisodeCommand,
    PitGovernanceError,
    ProposalSubmitted,
    SubmitProposalCommand,
    govern_real_pit_bundle,
    open_decision_episode,
    submit_proposal,
    validate_no_market_identity,
)
from core.gv_pit.read_models import project_decision_episode


EXPECTED_BOOK_HASH = (
    "074a47c7cdb7755a34c1d257e4e2ff99552cf9419033828b304cc5cf16016c22"
)
EXPECTED_HEAD_EVENT_ID = (
    "EVT_9e7435f4b14d9cfb2b0220129a8515b034926c89394dd096564585a727b2efc1"
)
EXPECTED_HEAD_AS_OF = "2026-08-02T12:06:00.000000Z"


def _open_stream() -> tuple[object, InMemoryGovernanceStream, str]:
    bundle = build_real_pit_source_bundle()
    episode_id = "TEST_EPISODE"
    stream = InMemoryGovernanceStream("TEST_STREAM")
    open_decision_episode(
        stream,
        OpenDecisionEpisodeCommand(
            episode_id=episode_id,
            pit_identity=bundle.pit_identity,
            no_market_facts=bundle.no_market_facts,
            certified_nav=bundle.certified_nav,
            classified_cash=bundle.classified_cash,
        ),
        timestamp_utc="2026-08-02T12:06:01.000000Z",
    )
    return bundle, stream, episode_id


def _proposal_with_identity(
    proposal: CapitalProposal,
    *,
    pit_identity: PointInTimeIdentity,
    targets: tuple[InstrumentTarget, ...] | None = None,
) -> CapitalProposal:
    return with_proposal_id(
        module_id=proposal.module_id,
        module_version=proposal.module_version,
        pit_identity=pit_identity,
        sleeve_id=proposal.sleeve_id,
        outcome=proposal.outcome,
        targets=proposal.targets if targets is None else targets,
        risk_targets=proposal.risk_targets,
        quantitative_boundaries=proposal.quantitative_boundaries,
        principal_claim=proposal.principal_claim,
        supporting_evidence=proposal.supporting_evidence,
        contradicting_evidence=proposal.contradicting_evidence,
        missing_discriminator=proposal.missing_discriminator,
        reason_not_to_act=proposal.reason_not_to_act,
        extension=proposal.extension,
    )


def test_real_bundle_binds_certified_prefix_head_and_cash_only_identity() -> None:
    bundle = build_real_pit_source_bundle()
    identity = bundle.pit_identity
    market_context = identity.market_snapshot_id

    assert identity.certified_book_id == EXPECTED_BOOK_HASH
    assert identity.certified_book_head_event_id == EXPECTED_HEAD_EVENT_ID
    assert identity.as_of_utc == EXPECTED_HEAD_AS_OF
    assert bundle.certified_prefix_event_count == 4
    assert market_context.kind == "NO_MARKET_DEPENDENCY_CASH_ONLY_V1"
    assert market_context.certified_book_id == EXPECTED_BOOK_HASH
    assert market_context.certified_book_head_event_id == EXPECTED_HEAD_EVENT_ID
    assert market_context.certified_book_hash == EXPECTED_BOOK_HASH
    assert len(market_context.validation_digest) == 64

    assert bundle.no_market_facts.positions_count == 0
    assert bundle.no_market_facts.orders_count == 0
    assert bundle.no_market_facts.fills_count == 0
    assert bundle.no_market_facts.unexplained_residual == Decimal("0")
    assert bundle.no_market_facts.proposal_target_quantities == (
        Decimal("0"),
        Decimal("0"),
    )
    assert bundle.no_market_facts.consumes_price_data is False
    assert bundle.no_market_facts.claims_yield is False
    assert bundle.no_market_facts.claims_market_return is False


def test_real_adapters_emit_three_real_rows_without_consuming_reference_price() -> None:
    bundle = build_real_pit_source_bundle()
    operated, shadow, cash = bundle.proposals

    assert tuple(row.module_id for row in bundle.proposals) == (
        "GV_REAL_MU_OPERATED",
        "GV_MU_NVDA_SHADOW",
        "GV_CERTIFIED_CASH_BASELINE",
    )
    assert operated.outcome is ProposalOutcome.ABSTAIN
    assert shadow.outcome is ProposalOutcome.ABSTAIN
    assert cash.outcome is ProposalOutcome.HOLD_CASH
    assert all(row.pit_identity is bundle.pit_identity for row in bundle.proposals)

    for proposal in (operated, shadow):
        assert len(proposal.targets) == 1
        target = proposal.targets[0]
        assert target.unit is InstrumentUnit.QUANTITY
        assert target.target_value == Decimal("0")
        assert target.normalization.price_identity is None
        assert b"reference_price" not in canonical_contract_bytes(proposal)
    assert cash.targets == ()
    assert cash.extension.payload.yield_status == "UNAVAILABLE_NO_ADMITTED_SOURCE"
    assert bundle.certified_nav == Decimal("11000")
    assert sum((row.amount for row in bundle.classified_cash), Decimal("0")) == Decimal(
        "11000"
    )


def test_extension_envelopes_fail_closed_on_schema_payload_or_digest_drift() -> None:
    payload = EquityFundamentalPayloadV1(
        subject="MU",
        permanent_key="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
        net_score_bps=0,
        missing_discriminator="physical supply persistence",
    )
    valid = build_equity_extension(payload)

    with pytest.raises(ValueError, match="EXTENSION_SCHEMA_ID_MISMATCH"):
        EquityFundamentalExtensionV1(
            schema_id="CASH_BASELINE_V1",
            schema_version=valid.schema_version,
            schema_digest=valid.schema_digest,
            canonical_payload_digest=valid.canonical_payload_digest,
            payload=payload,
        )
    with pytest.raises(ValueError, match="EXTENSION_SCHEMA_DIGEST_MISMATCH"):
        EquityFundamentalExtensionV1(
            schema_id=valid.schema_id,
            schema_version=valid.schema_version,
            schema_digest="0" * 64,
            canonical_payload_digest=valid.canonical_payload_digest,
            payload=payload,
        )
    with pytest.raises(ValueError, match="EXTENSION_PAYLOAD_DIGEST_MISMATCH"):
        EquityFundamentalExtensionV1(
            schema_id=valid.schema_id,
            schema_version=valid.schema_version,
            schema_digest=valid.schema_digest,
            canonical_payload_digest="0" * 64,
            payload=payload,
        )
    with pytest.raises(TypeError, match="EQUITY_EXTENSION_PAYLOAD_TYPE_INVALID"):
        EquityFundamentalExtensionV1(
            schema_id=valid.schema_id,
            schema_version=valid.schema_version,
            schema_digest=valid.schema_digest,
            canonical_payload_digest=valid.canonical_payload_digest,
            payload=CashBaselinePayloadV1(
                nav=Decimal("0"),
                classified_cash=(),
                yield_status="UNAVAILABLE",
            ),
        )


def test_content_addressed_proposal_rejects_post_id_field_drift() -> None:
    proposal = build_real_pit_source_bundle().proposals[0]
    with pytest.raises(ValueError, match="CAPITAL_PROPOSAL_ID_MISMATCH"):
        replace(proposal, principal_claim="tampered after proposal identity")


def test_no_market_identity_is_proof_carrying_for_every_required_predicate() -> None:
    bundle = build_real_pit_source_bundle()
    cases = (
        ("positions_count", 1, "NO_MARKET_POSITIONS_NOT_EMPTY"),
        ("orders_count", 1, "NO_MARKET_ORDERS_NOT_EMPTY"),
        ("fills_count", 1, "NO_MARKET_FILLS_NOT_EMPTY"),
        ("unexplained_residual", Decimal("0.01"), "NO_MARKET_RESIDUAL_NONZERO"),
        (
            "proposal_target_quantities",
            (Decimal("1"), Decimal("0")),
            "NO_MARKET_TARGET_QUANTITY_NONZERO",
        ),
        (
            "consumes_notional_conversion",
            True,
            "NO_MARKET_NOTIONAL_CONVERSION_PROHIBITED",
        ),
        (
            "consumes_weight_conversion",
            True,
            "NO_MARKET_WEIGHT_CONVERSION_PROHIBITED",
        ),
        ("consumes_price_data", True, "NO_MARKET_PRICE_CONSUMPTION_PROHIBITED"),
        ("claims_yield", True, "NO_MARKET_YIELD_CLAIM_PROHIBITED"),
        ("claims_market_return", True, "NO_MARKET_RETURN_CLAIM_PROHIBITED"),
    )
    for field_name, value, error in cases:
        bad_facts = replace(bundle.no_market_facts, **{field_name: value})
        bad_identity = replace(
            bundle.pit_identity,
            market_snapshot_id=build_no_market_identity(bad_facts),
        )
        with pytest.raises(PitGovernanceError, match=error):
            validate_no_market_identity(bad_identity, bad_facts)


def test_no_market_episode_rejects_nonzero_or_conversion_targets() -> None:
    bundle, stream, episode_id = _open_stream()
    proposal = bundle.proposals[0]
    nonzero = replace(proposal.targets[0], target_value=Decimal("1"))
    nonzero_proposal = _proposal_with_identity(
        proposal,
        pit_identity=bundle.pit_identity,
        targets=(nonzero,),
    )
    with pytest.raises(
        PitGovernanceError, match="NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_TARGET"
    ):
        submit_proposal(
            stream,
            SubmitProposalCommand(episode_id=episode_id, proposal=nonzero_proposal),
            submitted_at_utc="2026-08-02T12:06:02.000000Z",
            decided_at_utc="2026-08-02T12:06:03.000000Z",
        )

    conversion_target = replace(
        proposal.targets[0],
        unit=InstrumentUnit.NOTIONAL,
        normalization=NumericNormalizationPolicy(
            unit_quantum=Decimal("0.01"),
            rounding_mode=RoundingMode.EXACT,
            currency="USD",
            price_identity="UNADMITTED_PRICE",
            contract_multiplier=Decimal("1"),
            lot_size_policy=LotSizePolicy.NOT_APPLICABLE,
        ),
    )
    conversion_proposal = _proposal_with_identity(
        proposal,
        pit_identity=bundle.pit_identity,
        targets=(conversion_target,),
    )
    with pytest.raises(
        PitGovernanceError,
        match="NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_CONVERSION",
    ):
        submit_proposal(
            stream,
            SubmitProposalCommand(episode_id=episode_id, proposal=conversion_proposal),
            submitted_at_utc="2026-08-02T12:06:02.000000Z",
            decided_at_utc="2026-08-02T12:06:03.000000Z",
        )


def test_identity_mismatch_creates_complete_immutable_rejection_projection() -> None:
    bundle, stream, episode_id = _open_stream()
    mismatched_identity = build_pit_identity(
        certified_book_id=bundle.pit_identity.certified_book_id,
        certified_book_head_event_id=bundle.pit_identity.certified_book_head_event_id,
        evidence_set_id=bundle.pit_identity.evidence_set_id,
        market_snapshot_id=bundle.pit_identity.market_snapshot_id,
        as_of_utc="2026-08-02T12:06:00.000001Z",
    )
    proposal = _proposal_with_identity(
        bundle.proposals[0], pit_identity=mismatched_identity
    )
    submit_proposal(
        stream,
        SubmitProposalCommand(episode_id=episode_id, proposal=proposal),
        submitted_at_utc="2026-08-02T12:06:02.000000Z",
        decided_at_utc="2026-08-02T12:06:03.000000Z",
    )

    model = project_decision_episode(stream.read())
    assert len(model.proposal_records) == 1
    row = model.proposal_records[0]
    assert row.status == "REJECTED_IDENTITY_MISMATCH"
    assert row.proposal_id == proposal.proposal_id
    assert row.module_id == proposal.module_id
    assert row.principal_claim == proposal.principal_claim
    assert row.missing_discriminator == proposal.missing_discriminator
    assert row.target_summary == ("MU TARGET_FINAL QUANTITY 0",)
    assert model.selected_record_ids == ()


def test_governance_stream_rejects_duplicate_gap_digest_and_conflicting_replay() -> None:
    bundle, stream, episode_id = _open_stream()
    opened = stream.read()[0]

    with pytest.raises(PitGovernanceError, match="GOVERNANCE_DUPLICATE_EVENT_ID"):
        stream.append(opened)
    with pytest.raises(
        PitGovernanceError, match="GOVERNANCE_CONFLICTING_IDEMPOTENT_REPLAY"
    ):
        stream.append(replace(opened, event_digest="0" * 64))

    payload = ProposalSubmitted(
        episode_id=episode_id,
        record_id="REC_TEST",
        proposal=bundle.proposals[0],
    )
    duplicate_position = stream.build_event(
        payload,
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opened.event_id,
        sequence_number=0,
    )
    with pytest.raises(
        PitGovernanceError, match="GOVERNANCE_DUPLICATE_SEQUENCE_POSITION"
    ):
        stream.append(duplicate_position)

    gap = stream.build_event(
        payload,
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opened.event_id,
        sequence_number=3,
    )
    with pytest.raises(PitGovernanceError, match="GOVERNANCE_SEQUENCE_GAP"):
        stream.append(gap)

    wrong_previous = stream.build_event(
        payload,
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opened.event_id,
        previous_event_digest=GENESIS_DIGEST,
    )
    with pytest.raises(
        PitGovernanceError, match="GOVERNANCE_PREVIOUS_DIGEST_MISMATCH"
    ):
        stream.append(wrong_previous)

    valid = stream.build_event(
        payload,
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opened.event_id,
    )
    with pytest.raises(PitGovernanceError, match="GOVERNANCE_EVENT_DIGEST_MISMATCH"):
        stream.append(replace(valid, event_digest="0" * 64))


def test_real_governance_replay_and_projection_are_byte_identical() -> None:
    first_bundle = build_real_pit_source_bundle()
    second_bundle = build_real_pit_source_bundle()
    first_events = govern_real_pit_bundle(first_bundle).read()
    second_events = govern_real_pit_bundle(second_bundle).read()
    first_model = project_decision_episode(first_events)
    second_model = project_decision_episode(second_events)

    assert canonical_contract_bytes(first_events) == canonical_contract_bytes(second_events)
    assert canonical_contract_bytes(first_model) == canonical_contract_bytes(second_model)
    assert first_model.event_count == 7
    assert first_model.status == "OPEN"
    assert first_model.selected_record_ids == ()
    assert first_model.disagreement_summary == (
        "No material outcome disagreement across comparable sleeves."
    )
    assert tuple(row.status for row in first_model.proposal_records) == (
        "ELIGIBLE",
        "ELIGIBLE",
        "ELIGIBLE",
    )
    assert first_model.replay_status == "DETERMINISTIC_IN_MEMORY_VERIFIED"
    assert first_model.terminal_event_digest == first_events[-1].event_digest


def test_slice_1_new_modules_have_no_storage_or_session_state_authority() -> None:
    source_paths = (
        Path("core/gv_pit/contracts.py"),
        Path("core/gv_pit/adapters.py"),
        Path("core/gv_pit/governance.py"),
        Path("core/gv_pit/read_models.py"),
        Path("views/command_center.py"),
    )
    forbidden_imports = {
        "gv_portfolio_v0.operated_storage",
        "gv_portfolio_v0.execution",
        "strategies.optimizer",
        "sqlite3",
    }
    for path in source_paths:
        source = path.read_text(encoding="utf-8")
        assert "session_state" not in source
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert imported.isdisjoint(forbidden_imports)

    governance_source = Path("core/gv_pit/governance.py").read_text(encoding="utf-8")
    assert "Path(" not in governance_source
    assert "write_text" not in governance_source
    assert "write_bytes" not in governance_source
    assert "parquet" not in governance_source.lower()
    assert "sqlite" not in governance_source.lower()

    view_source = Path("views/command_center.py").read_text(encoding="utf-8")
    assert "GV_REAL_MU_OPERATED" not in view_source
    assert "GV_MU_NVDA_SHADOW" not in view_source
    assert "GV_CERTIFIED_CASH_BASELINE" not in view_source


def test_slice_1_contract_uses_exact_numeric_and_intent_types() -> None:
    proposal = build_real_pit_source_bundle().proposals[0]
    target = proposal.targets[0]
    assert isinstance(target.target_value, Decimal)
    assert isinstance(target.normalization.unit_quantum, Decimal)
    assert target.intent is TargetIntent.TARGET_FINAL
    assert target.unit is InstrumentUnit.QUANTITY
    canonical = canonical_value(proposal)
    assert isinstance(canonical, dict)
    assert canonical["targets"][0]["target_value"] == "0"
    assert canonical["targets"][0]["normalization"]["unit_quantum"] == "1"
