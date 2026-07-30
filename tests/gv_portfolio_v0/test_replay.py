"""GV-DETERMINISTIC-REPLAY-0 focused acceptance tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.book import PortfolioBookError, build_portfolio_book
from gv_portfolio_v0.replay import (
    CUSTODY_BASE_SHA,
    PROMOTION_TIP_SHA,
    ReplayError,
    SLICE0_TERMINAL_SHA,
    append_correction_and_recertify,
    branch_pins,
    build_replay_report,
    certify_replay_prefix,
    event_ledger_hash,
    partial_fill_residuals,
    reconstruct_book,
    reconstruct_exact,
    replay_idempotent,
    reopen_with_stable_prior,
    slice0_workspace_replay_report,
    valuation_pending_book,
)
from gv_portfolio_v0.vertical import build_draft_workspace, confirm_draft_workspace


def _evt(
    sequence: int,
    event_type: str,
    *,
    instrument_id: str | None = None,
    cash_bucket: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = {
        "sequence": sequence,
        "event_type": event_type,
        "effective_at": f"2026-07-20T10:00:{sequence:02d}.000000Z",
        "source_identity": f"FIXTURE:{event_type}:{sequence}",
        "instrument_id": instrument_id,
        "cash_bucket": cash_bucket,
        "payload": payload or {},
    }
    body["event_id"] = "EVT_" + domain_hash("GV-PORTFOLIO-V0:EVT:V1", body)
    return body


def _partial_fill_events() -> list[dict[str, Any]]:
    return [
        _evt(0, "CASH_OPENING", cash_bucket="AVAILABLE", payload={"amount": "1000"}),
        _evt(
            1,
            "ORDER_CREATED",
            instrument_id="INS_HARBOR",
            payload={
                "order": {
                    "order_id": "ORD_PARTIAL_1",
                    "instrument_id": "INS_HARBOR",
                    "side": "BUY",
                    "quantity": "10",
                    "reference_price": "40",
                }
            },
        ),
        _evt(
            2,
            "FILL_COMPLETED",
            instrument_id="INS_HARBOR",
            cash_bucket="AVAILABLE",
            payload={
                "fill": {
                    "fill_id": "FIL_PARTIAL_A",
                    "order_id": "ORD_PARTIAL_1",
                    "instrument_id": "INS_HARBOR",
                    "side": "BUY",
                    "quantity": "4",
                    "price": "40",
                    "fee": "1",
                    "cash_bucket": "AVAILABLE",
                }
            },
        ),
        _evt(
            3,
            "FILL_COMPLETED",
            instrument_id="INS_HARBOR",
            cash_bucket="AVAILABLE",
            payload={
                "fill": {
                    "fill_id": "FIL_PARTIAL_B",
                    "order_id": "ORD_PARTIAL_1",
                    "instrument_id": "INS_HARBOR",
                    "side": "BUY",
                    "quantity": "3",
                    "price": "40",
                    "fee": "0",
                    "cash_bucket": "AVAILABLE",
                }
            },
        ),
    ]


def test_branch_pins_record_promotion_tip_and_custody_base() -> None:
    pins = branch_pins()
    assert pins["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert pins["custody_base_sha"] == CUSTODY_BASE_SHA
    assert pins["slice0_terminal_sha"] == SLICE0_TERMINAL_SHA
    assert pins["active_implementation_base"] == PROMOTION_TIP_SHA


def test_exact_reconstruction_of_slice0_certified_book() -> None:
    certified = confirm_draft_workspace(build_draft_workspace())
    book = reconstruct_exact(
        certified["events"], expected_book=certified["book"]
    )
    assert book["terminal_nav"] == "1499"
    assert book["unexplained_residual"] == "0"
    assert book["book_hash"] == certified["book"]["book_hash"]


def test_idempotent_replay_of_same_event_prefix() -> None:
    events = confirm_draft_workspace(build_draft_workspace())["events"]
    book = replay_idempotent(events)
    assert book["book_hash"] == reconstruct_book(events)["book_hash"]
    assert event_ledger_hash(events) == event_ledger_hash(deepcopy(events))


def test_partial_fill_residual_state() -> None:
    events = _partial_fill_events()
    residuals = partial_fill_residuals(events)
    assert residuals == [
        {
            "order_id": "ORD_PARTIAL_1",
            "instrument_id": "INS_HARBOR",
            "ordered_quantity": "10",
            "filled_quantity": "7",
            "residual_quantity": "3",
        }
    ]
    book = reconstruct_book(events)
    # 4*40+1 + 3*40 = 281 cash spent from 1000
    assert book["total_cash"] == "719"
    assert book["positions"][0]["quantity"] == "7"
    assert book["partial_fill_residuals"] == residuals


def test_fill_quantity_cannot_exceed_remaining() -> None:
    events = _partial_fill_events()
    events[3]["payload"]["fill"]["quantity"] = "8"
    events[3]["event_id"] = "EVT_OVERFILL"
    with pytest.raises(PortfolioBookError, match="FILL_QUANTITY_EXCEEDS_REMAINING"):
        build_portfolio_book(events)


def test_valuation_pending_does_not_fabricate_prices() -> None:
    events = [
        _evt(
            0,
            "POSITION_OPENING",
            instrument_id="INS_PENDING",
            payload={"quantity": "3", "valuation_price": None},
        )
    ]
    book = valuation_pending_book(events)
    assert book["valuation_status"] == "VALUATION_PENDING"
    assert book["nav"] is None
    assert book["position_value"] is None


def test_correction_lineage_preserves_prior_certification_bytes() -> None:
    events = confirm_draft_workspace(build_draft_workspace())["events"]
    # Use economic subject events only for replay-native cert (drop product CRT markers).
    economic = [
        row
        for row in events
        if row["event_type"] != "CERTIFICATION_RECORDED"
    ]
    for index, row in enumerate(economic):
        row["sequence"] = index
    prior = certify_replay_prefix(
        economic,
        decision_snapshot_id="DSN_REPLAY",
        portfolio_aim_id="AIM_REPLAY",
    )
    prior_bytes = canonical_document_bytes(prior)
    result = append_correction_and_recertify(
        economic,
        prior_certification=prior,
        correction_payload={
            "correction_kind": "ANNOTATION",
            "reason": "operator_note_only",
            "details": {"note": "lineage proof"},
        },
        decision_snapshot_id="DSN_REPLAY",
        portfolio_aim_id="AIM_REPLAY",
        effective_at="2026-07-20T12:00:00.000000Z",
        source_identity="REPLAY:CORRECTION:1",
    )
    assert canonical_document_bytes(result["prior_certification"]) == prior_bytes
    assert result["certification"]["prior_certification_id"] == prior["certification_id"]
    assert result["certification"]["certification_id"] != prior["certification_id"]
    # Book economics unchanged by non-economic correction annotation.
    assert result["book"]["book_hash"] == reconstruct_book(economic)["book_hash"]


def test_reopen_replay_native_cert_is_byte_stable() -> None:
    events = confirm_draft_workspace(build_draft_workspace())["events"]
    economic = [
        row
        for row in events
        if row["event_type"] != "CERTIFICATION_RECORDED"
    ]
    for index, row in enumerate(economic):
        row["sequence"] = index
    prior = certify_replay_prefix(
        economic,
        decision_snapshot_id="DSN_REPLAY",
        portfolio_aim_id="AIM_REPLAY",
    )
    # Later non-economic observation-style no-op: append correction as reopen delta.
    extended_result = append_correction_and_recertify(
        economic,
        prior_certification=prior,
        correction_payload={"reason": "reopen_annotation"},
        decision_snapshot_id="DSN_REPLAY",
        portfolio_aim_id="AIM_REPLAY",
        effective_at="2026-08-01T00:00:00.000000Z",
        source_identity="REPLAY:REOPEN",
    )
    reopened = reopen_with_stable_prior(
        pre_observation_events=economic,
        full_events=extended_result["events"],
        prior_certification=prior,
        decision_snapshot_id="DSN_REPLAY",
        portfolio_aim_id="AIM_REPLAY",
    )
    assert (
        canonical_document_bytes(reopened["prior_certification"])
        == canonical_document_bytes(prior)
    )
    assert reopened["certification"]["prior_certification_id"] == prior["certification_id"]


def test_slice0_end_to_end_replay_report() -> None:
    report = slice0_workspace_replay_report()
    assert report["schema_version"] == "gv_portfolio_v0_replay_report_v1"
    assert report["branch_pins"]["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert report["branch_pins"]["custody_base_sha"] == CUSTODY_BASE_SHA
    assert report["prior_certification_byte_stable"] is True
    assert report["book"]["terminal_nav"] == "1499"
    assert report["unexplained_residual"] == "0"
    assert report["valuation_status"] == "COMPLETE"
    assert report["partial_fill_residuals"] == []
    # Idempotence embedded.
    assert report["idempotent_book_hash"] == report["book_hash"]


def test_reconstruction_mismatch_fails_closed() -> None:
    certified = confirm_draft_workspace(build_draft_workspace())
    expected = deepcopy(certified["book"])
    expected["terminal_nav"] = "1"
    with pytest.raises(ReplayError, match="RECONSTRUCTION_MISMATCH"):
        reconstruct_exact(certified["events"], expected_book=expected)


def test_build_replay_report_hashes_deterministically() -> None:
    events = confirm_draft_workspace(build_draft_workspace())["events"]
    first = build_replay_report(events)
    second = build_replay_report(deepcopy(events))
    assert first["report_hash"] == second["report_hash"]
    assert first["event_ledger_hash"] == second["event_ledger_hash"]
