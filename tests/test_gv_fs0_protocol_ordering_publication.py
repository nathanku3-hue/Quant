from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path

import pytest

from gv_fs0.protocol.definitions import (
    build_event_ranks,
    build_generated_event_slots,
    build_transition_ownership,
)
from gv_fs0.protocol.ordering import (
    OrderingError,
    assign_intra_rank_sequences,
    calculate_certification_reference_event_id,
    calculate_event_id,
    certification_reference_identity_preimage,
    collapse_and_order_events,
    event_identity_preimage,
)
from gv_fs0.protocol.publication import (
    automatic_lock_release_allowed,
    build_recovery_record,
    compare_under_lock,
    post_replace_verification_failure,
)

ROOT = Path(__file__).resolve().parents[1]


def _candidate(
    *,
    source_sequence: int,
    source_intent_id: str,
    slot: int,
    event_type: str = "CASH_MOVEMENT",
    rank: int = 40,
    timestamp: str = "2026-07-17T00:00:00.000000Z",
    session: str = "2026-07-17",
    cash_delta: str = "-10",
) -> dict[str, object]:
    return {
        "schema_version": "GV_FS0_PORTFOLIO_EVENT_V1",
        "book_id": "BOOK_" + "1" * 64,
        "decision_id": "DECISION:001",
        "source_sequence": source_sequence,
        "source_intent_id": source_intent_id,
        "generated_event_slot": slot,
        "event_type": event_type,
        "effective_timestamp": timestamp,
        "session": session,
        "event_type_rank": rank,
        "semantic_payload": {"cash_delta": cash_delta},
        "economic_effect_key": {
            "book_id": "BOOK_" + "1" * 64,
            "event_type": event_type,
            "effective_timestamp": timestamp,
            "session": session,
            "cash_delta": cash_delta,
        },
    }


def test_intra_rank_sequence_is_deterministic_contiguous_and_origin_ordered() -> None:
    candidates = [
        _candidate(source_sequence=2, source_intent_id="INTENT:B", slot=10),
        _candidate(source_sequence=1, source_intent_id="INTENT:Z", slot=20),
        _candidate(source_sequence=1, source_intent_id="INTENT:A", slot=20),
    ]
    ordered = assign_intra_rank_sequences(candidates)
    assert [(row["source_sequence"], row["source_intent_id"], row["generated_event_slot"]) for row in ordered] == [
        (1, "INTENT:A", 20),
        (1, "INTENT:Z", 20),
        (2, "INTENT:B", 10),
    ]
    assert [row["intra_rank_sequence"] for row in ordered] == [0, 1, 2]


def test_duplicate_origin_keys_block() -> None:
    duplicate = _candidate(source_sequence=1, source_intent_id="INTENT:A", slot=10)
    with pytest.raises(OrderingError, match="DUPLICATE_ORIGIN_ORDER_KEY"):
        assign_intra_rank_sequences([duplicate, deepcopy(duplicate)])


def test_event_id_requires_intra_rank_and_excludes_global_semantic_sequence() -> None:
    event = _candidate(source_sequence=1, source_intent_id="INTENT:A", slot=10)
    with pytest.raises(OrderingError, match="INTRA_RANK_SEQUENCE_REQUIRED"):
        calculate_event_id(event)
    event["intra_rank_sequence"] = 0
    first = calculate_event_id(event)
    event["semantic_sequence"] = 999
    second = calculate_event_id(event)
    assert first == second
    assert "event_id" not in event_identity_preimage(event)
    assert "semantic_sequence" not in event_identity_preimage(event)


def test_exact_duplicate_collapses_before_global_semantic_sequence() -> None:
    event = assign_intra_rank_sequences([_candidate(source_sequence=1, source_intent_id="INTENT:A", slot=10)])[0]
    event["event_id"] = calculate_event_id(event)
    result = collapse_and_order_events([event, deepcopy(event)])
    assert len(result) == 1
    assert result[0]["semantic_sequence"] == 0


def test_forged_or_conflicting_event_id_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    first, second = assign_intra_rank_sequences(
        [
            _candidate(source_sequence=1, source_intent_id="INTENT:A", slot=10),
            _candidate(source_sequence=2, source_intent_id="INTENT:B", slot=10, cash_delta="-11"),
        ]
    )
    first["event_id"] = "EVT_" + "f" * 64
    second["event_id"] = "EVT_" + "f" * 64
    monkeypatch.setattr("gv_fs0.protocol.ordering.calculate_event_id", lambda event: "EVT_" + "f" * 64)
    with pytest.raises(OrderingError, match="CONFLICTING_EVENT_ID"):
        collapse_and_order_events([first, second])


def test_provenance_distinct_duplicate_economic_effect_blocks() -> None:
    first, second = assign_intra_rank_sequences(
        [
            _candidate(source_sequence=1, source_intent_id="INTENT:A", slot=10),
            _candidate(source_sequence=2, source_intent_id="INTENT:B", slot=10),
        ]
    )
    with pytest.raises(OrderingError, match="DUPLICATE_SEMANTIC_EVENT"):
        collapse_and_order_events([first, second])


def test_global_order_and_semantic_sequence_follow_event_ids() -> None:
    later = _candidate(
        source_sequence=1,
        source_intent_id="INTENT:LATER",
        slot=10,
        timestamp="2026-07-18T00:00:00.000000Z",
        session="2026-07-18",
    )
    earlier = _candidate(source_sequence=1, source_intent_id="INTENT:EARLIER", slot=10)
    events = assign_intra_rank_sequences([later, earlier])
    result = collapse_and_order_events(reversed(events))
    assert [row["session"] for row in result] == ["2026-07-17", "2026-07-18"]
    assert [row["semantic_sequence"] for row in result] == [0, 1]
    assert all(str(row["event_id"]).startswith("EVT_") for row in result)


def test_certification_reference_identity_binds_certification_not_semantic_sequence() -> None:
    event = {
        "schema_version": "GV_FS0_PORTFOLIO_EVENT_V1",
        "book_id": "BOOK_" + "1" * 64,
        "decision_id": "DECISION:001",
        "terminal_snapshot_id": "SNAP_" + "2" * 64,
        "certification_id": "CERT_" + "3" * 64,
        "event_type": "CERTIFICATION_REFERENCE",
        "event_type_rank": 90,
        "effective_timestamp": "2026-07-17T00:00:00.000000Z",
        "session": "2026-07-17",
        "source_sequence": 0,
        "source_intent_id": "CERTIFICATION:CERT_" + "3" * 64,
        "generated_event_slot": 10,
        "intra_rank_sequence": 0,
        "semantic_sequence": 100,
    }
    preimage = certification_reference_identity_preimage(event)
    first = calculate_certification_reference_event_id(event)
    assert preimage["certification_id"] == event["certification_id"]
    assert "semantic_sequence" not in preimage
    event["semantic_sequence"] = 0
    assert calculate_certification_reference_event_id(event) == first
    event["certification_id"] = "CERT_" + "4" * 64
    assert calculate_certification_reference_event_id(event) != first


def test_transition_ownership_has_no_unowned_or_multiply_owned_effect() -> None:
    ranks = build_event_ranks()["event_ranks"]
    ownership = build_transition_ownership()["transition_ownership"]
    slots = build_generated_event_slots()["generated_event_slots"]
    assert [entry["event_type"] for entry in ownership] == [entry["event_type"] for entry in ranks]
    assert len({entry["event_type"] for entry in ownership}) == len(ownership)
    by_type = {entry["event_type"]: entry for entry in ownership}
    assert by_type["EXECUTION"]["cash"] == by_type["EXECUTION"]["shares"] == "NONE"
    assert by_type["FEE_OR_COST"]["cash"] == "NONE"
    assert by_type["DIVIDEND_ENTITLEMENT"]["receivables"] == "INCREASE_ONCE"
    assert by_type["DIVIDEND_PAYMENT"]["cash"] == "INCREASE_ONCE"
    assert by_type["DIVIDEND_PAYMENT"]["receivables"] == "DECREASE_ONCE"
    payment_slots = [entry for entry in slots if entry["source_intent_type"] == "DIVIDEND_PAYMENT_INSTRUCTION"]
    assert payment_slots == [
        {"generated_event_slot": 10, "generated_event_type": "DIVIDEND_PAYMENT", "source_intent_type": "DIVIDEND_PAYMENT_INSTRUCTION"}
    ]
    assert ranks.index({"event_type": "DIVIDEND_PAYMENT", "rank": 70}) < ranks.index(
        {"event_type": "SESSION_VALUATION", "rank": 80}
    )


def test_compare_under_lock_is_idempotent_for_identical_concurrent_candidates() -> None:
    assert compare_under_lock(
        observed_prebuild_target_hash="old",
        current_target_hash="new",
        candidate_bytes=b"same",
        current_target_bytes=b"same",
        current_target_valid=True,
    ) == "IDEMPOTENT_SUCCESS"


def test_differing_concurrent_candidate_cannot_overwrite_changed_target() -> None:
    assert compare_under_lock(
        observed_prebuild_target_hash="old",
        current_target_hash="new",
        candidate_bytes=b"candidate",
        current_target_bytes=b"other",
        current_target_valid=True,
    ) == "PUBLICATION_TARGET_CHANGED"
    assert compare_under_lock(
        observed_prebuild_target_hash="old",
        current_target_hash="old",
        candidate_bytes=b"candidate",
        current_target_bytes=b"other",
        current_target_valid=True,
    ) == "REPLACE_AUTHORIZED"


def test_post_replace_failure_claims_no_preservation_or_rollback() -> None:
    failure = post_replace_verification_failure()
    assert failure.failure_code == "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED"
    assert failure.prior_target_preservation_claimed is False
    assert failure.automatic_rollback_allowed is False
    assert failure.recovery_record_required is True
    assert failure.automatic_publication_blocked is True
    record = build_recovery_record(
        observed_prebuild_target_hash="1" * 64,
        candidate_hash="2" * 64,
        observed_post_replace_target_hash="3" * 64,
        failure_code=failure.failure_code,
        failure_stage="POST_REPLACE_REREAD",
    )
    assert record["state"] == "RECOVERY_REQUIRED"
    assert record["record_version"] == "GV-FS0-PUBLICATION-RECOVERY-V1"


def test_recovery_lock_is_never_automatically_released() -> None:
    assert not automatic_lock_release_allowed(
        replace_occurred=True,
        target_verified_unchanged=False,
        post_replace_verification_succeeded=False,
        candidate_was_identical=False,
        recovery_required=True,
    )
    assert automatic_lock_release_allowed(
        replace_occurred=False,
        target_verified_unchanged=True,
        post_replace_verification_succeeded=False,
        candidate_was_identical=False,
        recovery_required=False,
    )
    assert automatic_lock_release_allowed(
        replace_occurred=True,
        target_verified_unchanged=False,
        post_replace_verification_succeeded=True,
        candidate_was_identical=False,
        recovery_required=False,
    )


def test_protocol_publication_module_performs_no_filesystem_publication() -> None:
    import gv_fs0.protocol.publication as publication

    source = inspect.getsource(publication)
    for forbidden in ("open(", ".write_", "os.replace", "Path.replace", "fsync(", "unlink("):
        assert forbidden not in source


def test_protocol_package_has_no_streamlit_or_reducer_ownership() -> None:
    for path in (ROOT / "gv_fs0" / "protocol").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "streamlit" not in source.lower()
        assert "PortfolioBook" not in source
        assert "apply_reducer" not in source
