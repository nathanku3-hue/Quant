from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import hashlib
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_pit.adapters import (
    _validated_authoritative_head,
    build_real_pit_source_bundle,
)
from core.gv_pit.contracts import (
    MAX_SOURCE_WORKSPACE_BYTES,
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
    build_certified_source_prefix_proof,
    build_equity_extension,
    build_no_market_identity,
    build_no_market_source_state_digest,
    build_pit_identity,
    canonical_contract_bytes,
    canonical_value,
    decode_certified_source_prefix_proof,
    with_proposal_id,
)
from core.gv_pit.governance import (
    GENESIS_DIGEST,
    DecisionEpisodeOpened,
    InMemoryGovernanceStream,
    OpenDecisionEpisodeCommand,
    PitGovernanceError,
    ProposalAccepted,
    ProposalSubmitted,
    SubmitProposalCommand,
    expected_proposal_record_id,
    govern_real_pit_bundle,
    open_decision_episode,
    submit_proposal,
)
from gv_portfolio_v0.execution import portfolio_book_event
from core.gv_pit.read_models import PitProjectionError, project_decision_episode


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
            proposal_set=bundle.proposals,
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


def _rebind_no_market_facts(facts: object, **changes: object) -> object:
    draft = replace(facts, source_state_digest="0" * 64, **changes)
    digest = build_no_market_source_state_digest(
        source_proof=draft.source_proof,
        certified_book_id=draft.certified_book_id,
        certified_book_head_event_id=draft.certified_book_head_event_id,
        certified_book_head_timestamp_utc=draft.certified_book_head_timestamp_utc,
        certified_book_hash=draft.certified_book_hash,
        positions_count=draft.positions_count,
        orders_count=draft.orders_count,
        fills_count=draft.fills_count,
        unexplained_residual=draft.unexplained_residual,
        proposal_target_quantities=draft.proposal_target_quantities,
        consumes_notional_conversion=draft.consumes_notional_conversion,
        consumes_weight_conversion=draft.consumes_weight_conversion,
        consumes_price_data=draft.consumes_price_data,
        consumes_reference_price=draft.consumes_reference_price,
        claims_yield=draft.claims_yield,
        claims_market_return=draft.claims_market_return,
    )
    return replace(draft, source_state_digest=digest)


def _identity_for_facts(bundle: object, facts: object) -> PointInTimeIdentity:
    market_identity = build_no_market_identity(facts)
    return build_pit_identity(
        certified_book_id=facts.certified_book_id,
        certified_book_head_event_id=facts.certified_book_head_event_id,
        certified_book_head_timestamp_utc=facts.certified_book_head_timestamp_utc,
        evidence_set_id=bundle.pit_identity.evidence_set_id,
        market_snapshot_id=market_identity,
        as_of_utc=facts.certified_book_head_timestamp_utc,
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
        (
            "consumes_reference_price",
            True,
            "NO_MARKET_REFERENCE_PRICE_CONSUMPTION_PROHIBITED",
        ),
        ("claims_yield", True, "NO_MARKET_YIELD_CLAIM_PROHIBITED"),
        ("claims_market_return", True, "NO_MARKET_RETURN_CLAIM_PROHIBITED"),
    )
    for field_name, value, error in cases:
        bad_facts = replace(bundle.no_market_facts, **{field_name: value})
        with pytest.raises(ValueError, match=error):
            build_no_market_identity(bad_facts)

    with pytest.raises(ValueError, match="NO_MARKET_SOURCE_STATE_DIGEST_MISMATCH"):
        build_no_market_identity(
            replace(bundle.no_market_facts, source_state_digest="0" * 64)
        )


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


def test_matching_identity_proposal_must_be_in_opening_set() -> None:
    bundle, stream, episode_id = _open_stream()
    proposal = with_proposal_id(
        module_id="UNREGISTERED_ZERO_TARGET_MODULE",
        module_version="1.0.0",
        pit_identity=bundle.pit_identity,
        sleeve_id=bundle.proposals[0].sleeve_id,
        outcome=bundle.proposals[0].outcome,
        targets=bundle.proposals[0].targets,
        risk_targets=(),
        quantitative_boundaries=bundle.proposals[0].quantitative_boundaries,
        principal_claim=bundle.proposals[0].principal_claim,
        supporting_evidence=bundle.proposals[0].supporting_evidence,
        contradicting_evidence=bundle.proposals[0].contradicting_evidence,
        missing_discriminator=bundle.proposals[0].missing_discriminator,
        reason_not_to_act=bundle.proposals[0].reason_not_to_act,
        extension=bundle.proposals[0].extension,
    )

    with pytest.raises(PitGovernanceError, match="PIT_PROPOSAL_NOT_IN_OPENING_SET"):
        submit_proposal(
            stream,
            SubmitProposalCommand(episode_id=episode_id, proposal=proposal),
            submitted_at_utc="2026-08-02T12:06:02.000000Z",
            decided_at_utc="2026-08-02T12:06:03.000000Z",
        )
    assert len(stream.read()) == 1


def test_projector_rejects_matching_identity_proposal_outside_opening_set() -> None:
    bundle, stream, episode_id = _open_stream()
    opening = stream.read()[0]
    proposal = with_proposal_id(
        module_id="UNREGISTERED_REPLAY_MODULE",
        module_version="1.0.0",
        pit_identity=bundle.pit_identity,
        sleeve_id=bundle.proposals[0].sleeve_id,
        outcome=bundle.proposals[0].outcome,
        targets=bundle.proposals[0].targets,
        risk_targets=(),
        quantitative_boundaries=bundle.proposals[0].quantitative_boundaries,
        principal_claim=bundle.proposals[0].principal_claim,
        supporting_evidence=bundle.proposals[0].supporting_evidence,
        contradicting_evidence=bundle.proposals[0].contradicting_evidence,
        missing_discriminator=bundle.proposals[0].missing_discriminator,
        reason_not_to_act=bundle.proposals[0].reason_not_to_act,
        extension=bundle.proposals[0].extension,
    )
    record_id = expected_proposal_record_id(
        episode_id=episode_id,
        proposal_id=proposal.proposal_id,
    )
    submitted = stream.append_payload(
        ProposalSubmitted(
            episode_id=episode_id,
            record_id=record_id,
            proposal=proposal,
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opening.event_id,
    )
    stream.append_payload(
        ProposalAccepted(
            episode_id=episode_id,
            record_id=record_id,
            proposal=proposal,
        ),
        timestamp_utc="2026-08-02T12:06:03.000000Z",
        correlation_id=episode_id,
        causation_id=submitted.event_id,
    )

    with pytest.raises(PitProjectionError, match="PIT_PROPOSAL_NOT_IN_OPENING_SET"):
        project_decision_episode(stream.read())


def test_identity_mismatch_creates_complete_immutable_rejection_projection() -> None:
    bundle, stream, episode_id = _open_stream()
    mismatched_identity = replace(
        bundle.pit_identity, as_of_utc="2026-08-02T12:06:00.000001Z"
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
    assert row.target_summary == (
        "MU TARGET_FINAL QUANTITY 0 quantum=1 rounding=EXACT currency=USD "
        "price=UNAVAILABLE multiplier=UNAVAILABLE lot=WHOLE_UNITS",
    )
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
    with pytest.raises(
        PitGovernanceError, match="GOVERNANCE_EVENT_SCHEMA_VERSION_INVALID"
    ):
        stream.append(replace(valid, event_schema_version="9.0.0"))
    with pytest.raises(PitGovernanceError, match="GOVERNANCE_EVENT_DIGEST_MISMATCH"):
        stream.append(replace(valid, event_digest="0" * 64))

    timestamp_regression = stream.build_event(
        payload,
        timestamp_utc="2026-08-02T12:05:59.000000Z",
        correlation_id=episode_id,
        causation_id=opened.event_id,
    )
    with pytest.raises(PitGovernanceError, match="GOVERNANCE_EVENT_TIMESTAMP_REGRESSION"):
        stream.append(timestamp_regression)
    assert stream.read() == (opened,)


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


def test_fresh_process_runtime_blocks_transitive_side_effects() -> None:
    import json
    import os
    import subprocess
    import sys
    import textwrap

    script = textwrap.dedent(
        """
        import json
        import os
        import sys

        write_flags = (
            os.O_WRONLY
            | os.O_RDWR
            | os.O_APPEND
            | os.O_CREAT
            | os.O_TRUNC
        )
        forbidden_events = {
            "os.mkdir",
            "os.remove",
            "os.rename",
            "os.rmdir",
            "shutil.copyfile",
            "shutil.copymode",
            "shutil.copystat",
            "socket.connect",
            "socket.connect_ex",
            "sqlite3.connect",
            "subprocess.Popen",
        }

        def audit(event, args):
            if event == "open":
                mode = args[1] if len(args) > 1 else None
                flags = args[2] if len(args) > 2 else 0
                mode_writes = isinstance(mode, str) and any(
                    marker in mode for marker in ("w", "a", "x", "+")
                )
                flags_write = isinstance(flags, int) and bool(flags & write_flags)
                if mode_writes or flags_write:
                    raise RuntimeError(f"FORBIDDEN_RUNTIME_OPEN:{args[0]}")
            if event in forbidden_events:
                raise RuntimeError(f"FORBIDDEN_RUNTIME_EFFECT:{event}")

        sys.addaudithook(audit)

        from core.gv_pit.adapters import build_real_pit_source_bundle
        from core.gv_pit.governance import govern_real_pit_bundle
        from core.gv_pit.read_models import project_decision_episode
        import views.command_center

        bundle = build_real_pit_source_bundle()
        events = govern_real_pit_bundle(bundle).read()
        model = project_decision_episode(events)
        print(
            json.dumps(
                {
                    "proposal_count": len(bundle.proposals),
                    "event_count": model.event_count,
                    "head_sequence_number": model.head_sequence_number,
                    "selected_record_ids": list(model.selected_record_ids),
                },
                sort_keys=True,
            )
        )
        """
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path.cwd(),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout.strip()) == {
        "event_count": 7,
        "head_sequence_number": 6,
        "proposal_count": 3,
        "selected_record_ids": [],
    }


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

    with pytest.raises(
        ValueError, match="NORMALIZATION_UNIT_QUANTUM_POSITIVE_REQUIRED"
    ):
        replace(target.normalization, unit_quantum=Decimal("0"))
    with pytest.raises(ValueError, match="NORMALIZATION_CURRENCY_CANONICAL_REQUIRED"):
        replace(target.normalization, currency="usd")
    with pytest.raises(ValueError, match="INSTRUMENT_TARGET_FINITE_REQUIRED"):
        replace(target, target_value=Decimal("NaN"))
    with pytest.raises(ValueError, match="INSTRUMENT_WEIGHT_OUT_OF_RANGE"):
        replace(target, unit=InstrumentUnit.WEIGHT, target_value=Decimal("2"))


def test_real_proposals_bind_direct_decision_free_evidence_provenance() -> None:
    operated, shadow, _cash = build_real_pit_source_bundle().proposals
    expected_ids = (
        "EVD_bf117aaf4ee675512b7b5d326c24cd90023bafad4fd037f1c7e62481a707bb7c",
        "MU_CLAIM_EVALUATION",
        "NVDA_FACT_SET",
    )
    for proposal in (operated, shadow):
        assert tuple(row.evidence_id for row in proposal.supporting_evidence) == expected_ids
        assert proposal.supporting_evidence[1].sha256_digest == (
            "21e4f669bbaa337e963ecaa7e7ff7ccdcb1187e30a3db7afaeb9300794eac6c0"
        )
        assert proposal.supporting_evidence[2].sha256_digest == (
            "7a90e429bd2f52e83a2cf67b51d2173363a7a115d4a2b949c8c31d6e4f4265dd"
        )
        assert "statement_ids=" in proposal.supporting_evidence[1].source_identity
        assert "fact_ids=" in proposal.supporting_evidence[2].source_identity


def test_episode_open_binds_as_of_to_certified_head_timestamp() -> None:
    bundle = build_real_pit_source_bundle()
    with pytest.raises(ValueError, match="PIT_AS_OF_NOT_CERTIFIED_HEAD_TIMESTAMP"):
        build_pit_identity(
            certified_book_id=bundle.pit_identity.certified_book_id,
            certified_book_head_event_id=(
                bundle.pit_identity.certified_book_head_event_id
            ),
            certified_book_head_timestamp_utc=EXPECTED_HEAD_AS_OF,
            evidence_set_id=bundle.pit_identity.evidence_set_id,
            market_snapshot_id=bundle.pit_identity.market_snapshot_id,
            as_of_utc="2026-08-02T12:06:00.000001Z",
        )
    mismatched_identity = replace(
        bundle.pit_identity, as_of_utc="2026-08-02T12:06:00.000001Z"
    )
    stream = InMemoryGovernanceStream("AS_OF_BINDING_TEST")
    with pytest.raises(
        PitGovernanceError, match="PIT_AS_OF_NOT_CERTIFIED_HEAD_TIMESTAMP"
    ):
        open_decision_episode(
            stream,
            OpenDecisionEpisodeCommand(
                episode_id="AS_OF_EPISODE",
                pit_identity=mismatched_identity,
                no_market_facts=bundle.no_market_facts,
                proposal_set=bundle.proposals,
                certified_nav=bundle.certified_nav,
                classified_cash=bundle.classified_cash,
            ),
            timestamp_utc="2026-08-02T12:06:01.000000Z",
        )
    assert stream.read() == ()


def test_identity_rejection_precedes_market_dependent_target_admission() -> None:
    bundle, stream, episode_id = _open_stream()
    mismatched_identity = replace(
        bundle.pit_identity, as_of_utc="2026-08-02T12:06:00.000001Z"
    )
    nonzero_target = replace(
        bundle.proposals[0].targets[0], target_value=Decimal("1")
    )
    mismatched_nonzero = _proposal_with_identity(
        bundle.proposals[0],
        pit_identity=mismatched_identity,
        targets=(nonzero_target,),
    )
    submit_proposal(
        stream,
        SubmitProposalCommand(episode_id=episode_id, proposal=mismatched_nonzero),
        submitted_at_utc="2026-08-02T12:06:02.000000Z",
        decided_at_utc="2026-08-02T12:06:03.000000Z",
    )
    model = project_decision_episode(stream.read())
    assert model.proposal_records[0].status == "REJECTED_IDENTITY_MISMATCH"

    matching_bundle, matching_stream, matching_episode_id = _open_stream()
    matching_nonzero = _proposal_with_identity(
        matching_bundle.proposals[0],
        pit_identity=matching_bundle.pit_identity,
        targets=(
            replace(
                matching_bundle.proposals[0].targets[0],
                target_value=Decimal("1"),
            ),
        ),
    )
    with pytest.raises(
        PitGovernanceError, match="NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_TARGET"
    ):
        submit_proposal(
            matching_stream,
            SubmitProposalCommand(
                episode_id=matching_episode_id, proposal=matching_nonzero
            ),
            submitted_at_utc="2026-08-02T12:06:02.000000Z",
            decided_at_utc="2026-08-02T12:06:03.000000Z",
        )
    assert len(matching_stream.read()) == 1


def test_projector_rejects_orphan_undisposed_and_malformed_facts() -> None:
    bundle, orphan_stream, episode_id = _open_stream()
    orphan_stream.append_payload(
        ProposalAccepted(
            episode_id=episode_id,
            record_id="REC_ORPHAN",
            proposal=bundle.proposals[0],
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=orphan_stream.read()[0].event_id,
    )
    with pytest.raises(PitProjectionError, match="PIT_ORPHAN_PROPOSAL_DISPOSITION"):
        project_decision_episode(orphan_stream.read())

    bundle, undisposed_stream, episode_id = _open_stream()
    opening_event = undisposed_stream.read()[0]
    undisposed_record_id = expected_proposal_record_id(
        episode_id=episode_id,
        proposal_id=bundle.proposals[0].proposal_id,
    )
    undisposed_stream.append_payload(
        ProposalSubmitted(
            episode_id=episode_id,
            record_id=undisposed_record_id,
            proposal=bundle.proposals[0],
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opening_event.event_id,
    )
    with pytest.raises(PitProjectionError, match="PIT_UNDISPOSED_PROPOSAL_SUBMISSION"):
        project_decision_episode(undisposed_stream.read())

    bundle, malformed_stream, episode_id = _open_stream()
    opening_event = malformed_stream.read()[0]
    malformed_record_id = expected_proposal_record_id(
        episode_id=episode_id,
        proposal_id=bundle.proposals[0].proposal_id,
    )
    submitted = malformed_stream.append_payload(
        ProposalSubmitted(
            episode_id=episode_id,
            record_id=malformed_record_id,
            proposal=bundle.proposals[0],
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opening_event.event_id,
    )
    malformed_stream.append_payload(
        ProposalAccepted(
            episode_id=episode_id,
            record_id=malformed_record_id,
            proposal=bundle.proposals[1],
        ),
        timestamp_utc="2026-08-02T12:06:03.000000Z",
        correlation_id=episode_id,
        causation_id=submitted.event_id,
    )
    with pytest.raises(PitProjectionError, match="PIT_DISPOSITION_PROPOSAL_MISMATCH"):
        project_decision_episode(malformed_stream.read())

    bundle, forged_stream, episode_id = _open_stream()
    opening_event = forged_stream.read()[0]
    submitted = forged_stream.append_payload(
        ProposalSubmitted(
            episode_id=episode_id,
            record_id="REC_FORGED",
            proposal=bundle.proposals[0],
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opening_event.event_id,
    )
    forged_stream.append_payload(
        ProposalAccepted(
            episode_id=episode_id,
            record_id="REC_FORGED",
            proposal=bundle.proposals[0],
        ),
        timestamp_utc="2026-08-02T12:06:03.000000Z",
        correlation_id=episode_id,
        causation_id=submitted.event_id,
    )
    with pytest.raises(PitProjectionError, match="PIT_PROPOSAL_RECORD_ID_MISMATCH"):
        project_decision_episode(forged_stream.read())

    bundle, nonzero_stream, episode_id = _open_stream()
    opening_event = nonzero_stream.read()[0]
    nonzero_proposal = _proposal_with_identity(
        bundle.proposals[0],
        pit_identity=bundle.pit_identity,
        targets=(
            replace(
                bundle.proposals[0].targets[0],
                target_value=Decimal("1"),
            ),
        ),
    )
    record_id = expected_proposal_record_id(
        episode_id=episode_id,
        proposal_id=nonzero_proposal.proposal_id,
    )
    submitted = nonzero_stream.append_payload(
        ProposalSubmitted(
            episode_id=episode_id,
            record_id=record_id,
            proposal=nonzero_proposal,
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opening_event.event_id,
    )
    nonzero_stream.append_payload(
        ProposalAccepted(
            episode_id=episode_id,
            record_id=record_id,
            proposal=nonzero_proposal,
        ),
        timestamp_utc="2026-08-02T12:06:03.000000Z",
        correlation_id=episode_id,
        causation_id=submitted.event_id,
    )
    with pytest.raises(
        PitProjectionError, match="NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_TARGET"
    ):
        project_decision_episode(nonzero_stream.read())

    bundle = build_real_pit_source_bundle()
    invalid_open_stream = InMemoryGovernanceStream("INVALID_OPEN_STREAM")
    invalid_open_stream.append_payload(
        DecisionEpisodeOpened(
            episode_id="INVALID_OPEN_EPISODE",
            pit_identity=bundle.pit_identity,
            no_market_facts=bundle.no_market_facts,
            proposal_set=bundle.proposals,
            certified_nav=bundle.certified_nav + Decimal("1"),
            classified_cash=bundle.classified_cash,
        ),
        timestamp_utc="2026-08-02T12:06:01.000000Z",
        correlation_id="INVALID_OPEN_EPISODE",
        causation_id=bundle.pit_identity.certified_book_head_event_id,
    )
    with pytest.raises(PitProjectionError, match="PIT_CLASSIFIED_CASH_NAV_MISMATCH"):
        project_decision_episode(invalid_open_stream.read())


def test_projection_exposes_complete_operational_replay_lineage() -> None:
    events = govern_real_pit_bundle(build_real_pit_source_bundle()).read()
    model = project_decision_episode(events)
    assert model.stream_id == events[0].stream_id
    assert model.head_sequence_number == 6
    assert len(model.governance_events) == 7
    assert tuple(row.sequence_number for row in model.governance_events) == tuple(range(7))
    assert model.governance_events[0].event_type == "DECISION_EPISODE_OPENED"
    assert model.governance_events[-1].event_digest == model.terminal_event_digest
    assert all(row.correlation_id == model.episode_id for row in model.governance_events)


def test_certified_source_proof_enforces_event_and_workspace_byte_bounds() -> None:
    proof = build_real_pit_source_bundle().no_market_facts.source_proof
    workspace, prefix, _certification, _prior = decode_certified_source_prefix_proof(
        proof
    )

    oversized_prefix = [prefix[0] for _ in range(257)]
    oversized_prefix_json = canonical_document_bytes(oversized_prefix).decode("utf-8")
    with pytest.raises(
        ValueError, match="CERTIFIED_SOURCE_PREFIX_EVENT_COUNT_OUT_OF_BOUNDS"
    ):
        replace(
            proof,
            certified_prefix_json=oversized_prefix_json,
            certified_prefix_event_count=len(oversized_prefix),
            certified_prefix_size_bytes=len(oversized_prefix_json.encode("utf-8")),
            certified_prefix_sha256=hashlib.sha256(
                oversized_prefix_json.encode("utf-8")
            ).hexdigest(),
        )

    oversized_workspace = deepcopy(workspace)
    oversized_workspace["_proof_padding"] = "x" * MAX_SOURCE_WORKSPACE_BYTES
    oversized_workspace_json = canonical_document_bytes(oversized_workspace).decode(
        "utf-8"
    )
    with pytest.raises(
        ValueError, match="CERTIFIED_SOURCE_WORKSPACE_SIZE_OUT_OF_BOUNDS"
    ):
        replace(
            proof,
            source_workspace_json=oversized_workspace_json,
            source_workspace_size_bytes=len(
                oversized_workspace_json.encode("utf-8")
            ),
            source_workspace_sha256=hashlib.sha256(
                oversized_workspace_json.encode("utf-8")
            ).hexdigest(),
        )


def test_no_market_open_rejects_rehashed_workspace_forgery() -> None:
    bundle = build_real_pit_source_bundle()
    proof = bundle.no_market_facts.source_proof
    workspace, prefix, certification, prior = decode_certified_source_prefix_proof(
        proof
    )
    forged_workspace = deepcopy(workspace)
    forged_workspace["book"]["nav"] = "999999"
    forged_proof = build_certified_source_prefix_proof(
        source_workspace=forged_workspace,
        certified_prefix=prefix,
        certification=certification,
        prior_certification=prior,
        decision_snapshot_id=proof.decision_snapshot_id,
        portfolio_aim_id=proof.portfolio_aim_id,
    )
    forged_facts = _rebind_no_market_facts(
        bundle.no_market_facts, source_proof=forged_proof
    )
    forged_identity = _identity_for_facts(bundle, forged_facts)
    stream = InMemoryGovernanceStream("FORGED_SOURCE_WORKSPACE")
    with pytest.raises(PitGovernanceError, match="NO_MARKET_SOURCE_WORKSPACE_INVALID"):
        open_decision_episode(
            stream,
            OpenDecisionEpisodeCommand(
                episode_id="FORGED_SOURCE_EPISODE",
                pit_identity=forged_identity,
                no_market_facts=forged_facts,
                proposal_set=bundle.proposals,
                certified_nav=bundle.certified_nav,
                classified_cash=bundle.classified_cash,
            ),
            timestamp_utc="2026-08-02T12:06:01.000000Z",
        )
    assert stream.read() == ()


def test_no_market_open_rejects_rehashed_authoritative_head_claim() -> None:
    bundle = build_real_pit_source_bundle()
    _workspace, prefix, _certification, _prior = decode_certified_source_prefix_proof(
        bundle.no_market_facts.source_proof
    )
    forged_head = prefix[-2]
    forged_facts = _rebind_no_market_facts(
        bundle.no_market_facts,
        certified_book_head_event_id=forged_head["event_id"],
        certified_book_head_timestamp_utc=forged_head["effective_at"],
    )
    forged_identity = _identity_for_facts(bundle, forged_facts)
    stream = InMemoryGovernanceStream("FORGED_SOURCE_HEAD")
    with pytest.raises(
        PitGovernanceError,
        match="NO_MARKET_SOURCE_CERTIFIED_BOOK_HEAD_EVENT_ID_MISMATCH",
    ):
        open_decision_episode(
            stream,
            OpenDecisionEpisodeCommand(
                episode_id="FORGED_HEAD_EPISODE",
                pit_identity=forged_identity,
                no_market_facts=forged_facts,
                proposal_set=bundle.proposals,
                certified_nav=bundle.certified_nav,
                classified_cash=bundle.classified_cash,
            ),
            timestamp_utc="2026-08-02T12:05:31.000000Z",
        )
    assert stream.read() == ()


def test_authoritative_head_ignores_valid_non_authoritative_tail() -> None:
    proof = build_real_pit_source_bundle().no_market_facts.source_proof
    _workspace, prefix, _certification, _prior = decode_certified_source_prefix_proof(
        proof
    )
    observation = portfolio_book_event(
        len(prefix),
        "LATER_OBSERVATION_ADMITTED",
        "2026-08-02T12:07:00.000000Z",
        "OBS_TEST_NON_AUTHORITATIVE_TAIL",
        payload={"preview_only": False},
    )
    head = _validated_authoritative_head([*prefix, observation])
    assert head["event_id"] == EXPECTED_HEAD_EVENT_ID
    assert head["effective_at"] == EXPECTED_HEAD_AS_OF


def test_runtime_enum_and_normalization_invariants_fail_closed() -> None:
    target = build_real_pit_source_bundle().proposals[0].targets[0]
    with pytest.raises(TypeError, match="NORMALIZATION_ROUNDING_MODE_TYPE_INVALID"):
        replace(target.normalization, rounding_mode="EXACT")
    with pytest.raises(TypeError, match="INSTRUMENT_TARGET_INTENT_TYPE_INVALID"):
        replace(target, intent="TARGET_FINAL")
    with pytest.raises(
        ValueError, match="INSTRUMENT_TARGET_NOT_NORMALIZED_TO_QUANTUM"
    ):
        replace(target, target_value=Decimal("0.5"))
    with pytest.raises(ValueError, match="QUANTITY_LOT_POLICY_REQUIRED"):
        replace(
            target,
            normalization=replace(
                target.normalization,
                lot_size_policy=LotSizePolicy.NOT_APPLICABLE,
            ),
        )
    with pytest.raises(
        ValueError, match="NON_QUANTITY_LOT_POLICY_NOT_APPLICABLE_REQUIRED"
    ):
        replace(target, unit=InstrumentUnit.NOTIONAL)


def test_append_validation_is_incremental_not_full_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, stream, episode_id = _open_stream()
    opening = stream.read()[0]
    proposal = bundle.proposals[0]
    event = stream.build_event(
        ProposalSubmitted(
            episode_id=episode_id,
            record_id=expected_proposal_record_id(
                episode_id=episode_id, proposal_id=proposal.proposal_id
            ),
            proposal=proposal,
        ),
        timestamp_utc="2026-08-02T12:06:02.000000Z",
        correlation_id=episode_id,
        causation_id=opening.event_id,
    )

    def _unexpected_full_validation(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("append must not replay the complete stream")

    monkeypatch.setattr(
        "core.gv_pit.governance.validate_governance_event_stream",
        _unexpected_full_validation,
    )
    stream.append(event)
    assert stream.read() == (opening, event)
