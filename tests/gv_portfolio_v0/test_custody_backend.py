from __future__ import annotations

from copy import deepcopy

import pytest

from contracts.gv_portfolio.v0.identity import (
    CustodyContractError,
    evidence_reference,
    instrument_identity,
    verify_evidence_reference,
    verify_instrument_identity,
)
from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_portfolio_v0.events import (
    CanonicalEventStream,
    CustodyEventError,
    build_exercised_opening_stream,
    portfolio_book_event,
    verify_portfolio_book_event,
)
from gv_portfolio_v0.vertical import (
    build_draft_workspace,
    evidence_reference as vertical_evidence_reference,
    reduce_events,
)


def _principal_identity() -> dict[str, str]:
    return instrument_identity("ISSUER:NORTHSTAR:COMMON")


def test_instrument_identity_is_permanent_and_display_metadata_is_outside_hash() -> None:
    identity = _principal_identity()
    enriched_a = {**identity, "symbol": "NSTAR", "name": "Northstar Systems"}
    enriched_b = {**identity, "symbol": "NST", "name": "Northstar Systems plc"}

    verify_instrument_identity(enriched_a)
    verify_instrument_identity(enriched_b)
    assert enriched_a["instrument_id"] == enriched_b["instrument_id"]

    tampered = {**identity, "permanent_key": "ISSUER:OTHER:COMMON"}
    with pytest.raises(CustodyContractError, match="INSTRUMENT_ID_MISMATCH"):
        verify_instrument_identity(tampered)


def test_evidence_reference_binds_exact_content_and_canonical_source_metadata() -> None:
    reference = evidence_reference(
        content="Exact evidence bytes.",
        locator="fixture://custody/evidence-v1",
        observed_at="2026-07-19T12:00:00.000000Z",
    )
    verify_evidence_reference(reference)

    tampered_content = {**reference, "content": "Changed evidence bytes."}
    with pytest.raises(CustodyContractError, match="EVIDENCE_CONTENT_HASH_MISMATCH"):
        verify_evidence_reference(tampered_content)

    tampered_locator = {**reference, "locator": "fixture://custody/other-v1"}
    with pytest.raises(CustodyContractError, match="EVIDENCE_REFERENCE_ID_MISMATCH"):
        verify_evidence_reference(tampered_locator)

    expanded = {**reference, "unbound_note": "must not enter canonical evidence"}
    with pytest.raises(CustodyContractError, match="EVIDENCE_REFERENCE_FIELDS_INVALID"):
        verify_evidence_reference(expanded)

    with pytest.raises(CustodyContractError, match="OBSERVED_AT_NOT_CANONICAL"):
        evidence_reference(
            content="Exact evidence bytes.",
            locator="fixture://custody/evidence-v1",
            observed_at="2026-07-19T12:00:00Z",
        )


def test_new_identity_and_evidence_contracts_match_existing_slice_zero_bytes() -> None:
    workspace = build_draft_workspace()
    principal = workspace["instruments"][0]
    expected_identity = _principal_identity()
    assert principal["instrument_id"] == expected_identity["instrument_id"]

    new_reference = evidence_reference(
        content="Northstar recurring revenue and renewal evidence supports the principal thesis.",
        locator="fixture://northstar/principal-v1",
        observed_at="2026-07-19T12:00:00.000000Z",
    )
    old_reference = vertical_evidence_reference(
        content="Northstar recurring revenue and renewal evidence supports the principal thesis.",
        locator="fixture://northstar/principal-v1",
        observed_at="2026-07-19T12:00:00.000000Z",
    )
    assert canonical_document_bytes(new_reference) == canonical_document_bytes(old_reference)


def test_portfolio_book_event_freezes_envelope_and_detects_tampering() -> None:
    event = portfolio_book_event(
        0,
        "CASH_OPENING",
        "2026-07-20T08:55:00.000000Z",
        "FIXTURE:CASH:AVAILABLE",
        cash_bucket="AVAILABLE",
        payload={"amount": "975"},
    )
    verify_portfolio_book_event(event)

    tampered = deepcopy(event)
    tampered["payload"]["amount"] = "976"
    with pytest.raises(CustodyContractError, match="IDENTITY_MISMATCH:event_id"):
        verify_portfolio_book_event(tampered)

    expanded = {**event, "unowned_field": "must-not-enter-envelope"}
    with pytest.raises(CustodyEventError, match="EVENT_ENVELOPE_FIELDS_INVALID"):
        verify_portfolio_book_event(expanded)

    with pytest.raises(CustodyEventError, match="SPLIT_NUMERATOR_DECIMAL_INVALID"):
        portfolio_book_event(
            0,
            "CORPORATE_ACTION_SPLIT",
            "2026-07-20T08:57:00.000000Z",
            "FIXTURE:SPLIT:NSTAR:2FOR1",
            instrument_id=_principal_identity()["instrument_id"],
            payload={
                "numerator": "02",
                "denominator": "1",
                "pre_quantity": "10",
                "pre_reference_price": "50",
            },
        )


def test_canonical_stream_is_immutable_append_only_and_defensively_copied() -> None:
    prior = build_exercised_opening_stream(_principal_identity()["instrument_id"])
    prior_bytes = prior.canonical_bytes()
    exposed = prior.events
    exposed[0]["payload"]["amount"] = "999999"
    assert prior.canonical_bytes() == prior_bytes

    advanced = prior.append(
        "PORTFOLIO_AIM_CONFIRMED",
        "2026-07-20T09:05:30.000000Z",
        "AIM_TEST",
        payload={"portfolio_aim_id": "AIM_TEST"},
    )
    advanced.assert_extends(prior)
    assert prior.event_count == 4
    assert advanced.event_count == 5
    assert advanced.event_stream_id != prior.event_stream_id
    assert prior.canonical_bytes() == prior_bytes

    rewritten_events = list(prior.events)
    rewritten_events[0] = portfolio_book_event(
        0,
        "CASH_OPENING",
        "2026-07-20T08:55:00.000000Z",
        "FIXTURE:CASH:AVAILABLE",
        cash_bucket="AVAILABLE",
        payload={"amount": "976"},
    )
    rewritten = CanonicalEventStream(rewritten_events)
    with pytest.raises(CustodyEventError, match="EVENT_STREAM_HISTORY_REWRITTEN"):
        rewritten.assert_extends(prior)


def test_stream_snapshot_round_trip_is_byte_exact_and_tamper_evident() -> None:
    stream = build_exercised_opening_stream(_principal_identity()["instrument_id"])
    snapshot = stream.snapshot()
    reopened = CanonicalEventStream.from_snapshot(snapshot)
    assert reopened.canonical_bytes() == stream.canonical_bytes()

    tampered = deepcopy(snapshot)
    tampered["events"][0]["payload"]["amount"] = "976"
    with pytest.raises(CustodyContractError):
        CanonicalEventStream.from_snapshot(tampered)

    wrong_claim = deepcopy(snapshot)
    wrong_claim["event_stream_id"] = "PES_" + "0" * 64
    with pytest.raises(CustodyEventError, match="EVENT_STREAM_SNAPSHOT_MISMATCH"):
        CanonicalEventStream.from_snapshot(wrong_claim)


def test_stream_rejects_noncontiguous_sequence_before_integration() -> None:
    event = portfolio_book_event(
        1,
        "CASH_OPENING",
        "2026-07-20T08:55:00.000000Z",
        "FIXTURE:CASH:AVAILABLE",
        cash_bucket="AVAILABLE",
        payload={"amount": "975"},
    )
    with pytest.raises(CustodyEventError, match="EVENT_SEQUENCE_NOT_CONTIGUOUS"):
        CanonicalEventStream([event])


def test_exercised_split_stream_matches_slice_zero_and_preserves_value() -> None:
    workspace = build_draft_workspace()
    principal_id = workspace["instruments"][0]["instrument_id"]
    stream = build_exercised_opening_stream(principal_id)

    assert canonical_document_bytes(list(stream.events)) == canonical_document_bytes(
        workspace["events"]
    )
    book = reduce_events(stream.events)
    assert book["split_value_residual"] == "0"
    position = book["positions"][0]
    assert position["quantity"] == "20"
    assert position["valuation_price"] == "25"
    assert position["market_value"] == "500"
