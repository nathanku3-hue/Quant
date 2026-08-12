from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

import pytest

from research.aov0.weekly_tape import (
    CLOCK1_FROZEN_CANDIDATE_ENTITY_IDS,
    CLOCK1_FROZEN_CANDIDATE_SOURCE_SHA256,
    CLOCK1_FROZEN_CANDIDATE_UNIVERSE_SHA256,
    build_weekly_tape_preflight,
    frozen_candidate_universe_hash,
)


def _ids() -> list[str]:
    return list(CLOCK1_FROZEN_CANDIDATE_ENTITY_IDS)


def _receipts() -> dict[str, dict[str, object]]:
    common_time = "2026-08-14T20:10:00Z"
    return {
        "ciq_quarterly_fundamentals": {
            "source_id": "SPCIQPRO:QUARTERLY_FUNDAMENTALS",
            "retrieved_at": common_time,
            "raw_object_sha256": "1" * 64,
            "company_universe_entity_count": 109,
        },
        "ciq_security_master": {
            "source_id": "SPCIQPRO:PRIMARY_SECURITY_MASTER",
            "retrieved_at": common_time,
            "raw_object_sha256": "2" * 64,
            "frozen_entity_count": 109,
        },
        "ciq_market_data": {
            "source_id": "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA",
            "retrieved_at": common_time,
            "raw_object_sha256": "3" * 64,
            "frozen_entity_count": 109,
        },
        "nyfed_sofr": {
            "source_id": "NYFED:SOFR",
            "retrieved_at": common_time,
            "raw_object_sha256": "4" * 64,
        },
    }


def test_weekly_tape_preflight_accepts_same_109_with_fresh_required_receipts() -> None:
    ids = _ids()
    packet = build_weekly_tape_preflight(
        frozen_candidate_entity_ids=ids,
        refreshed_candidate_entity_ids=list(reversed(ids)),
        previous_cut_at="2026-08-08T19:48:38Z",
        current_cut_at=datetime(2026, 8, 14, 20, 30, tzinfo=UTC),
        source_receipts=_receipts(),
    )
    assert packet["status"] == "READY_FOR_V3_DECISION_CUT_CONSTRUCTION"
    assert packet["candidate_count"] == 109
    assert packet["candidate_universe_sha256"] == CLOCK1_FROZEN_CANDIDATE_UNIVERSE_SHA256
    assert packet["candidate_source_sha256"] == CLOCK1_FROZEN_CANDIDATE_SOURCE_SHA256
    assert frozen_candidate_universe_hash(_ids()) == CLOCK1_FROZEN_CANDIDATE_UNIVERSE_SHA256
    assert packet["growth_screen_rerun_authorized"] is False
    assert packet["parent_child_mutation_authority"] == "NONE"
    assert packet["outcome_open_authority"] == "NONE"
    assert packet["financial_alpha_evidence"] == 0
    assert len(packet["preflight_id"]) == 64


def test_weekly_tape_preflight_rejects_self_consistent_wrong_109() -> None:
    wrong = [str(1_000_000 + index) for index in range(109)]
    with pytest.raises(ValueError, match="frozen_candidate_universe_not_clock1"):
        build_weekly_tape_preflight(
            frozen_candidate_entity_ids=wrong,
            refreshed_candidate_entity_ids=wrong,
            previous_cut_at="2026-08-08T19:48:38Z",
            current_cut_at="2026-08-14T20:30:00Z",
            source_receipts=_receipts(),
        )


def test_weekly_tape_preflight_fails_closed_on_candidate_membership_drift() -> None:
    frozen = _ids()
    refreshed = frozen.copy()
    refreshed[-1] = "9999999"
    with pytest.raises(ValueError, match="frozen_candidate_membership_drift"):
        build_weekly_tape_preflight(
            frozen_candidate_entity_ids=frozen,
            refreshed_candidate_entity_ids=refreshed,
            previous_cut_at="2026-08-08T19:48:38Z",
            current_cut_at="2026-08-14T20:30:00Z",
            source_receipts=_receipts(),
        )


def test_weekly_tape_preflight_fails_closed_on_stale_required_source() -> None:
    receipts = deepcopy(_receipts())
    receipts["ciq_quarterly_fundamentals"]["retrieved_at"] = "2026-08-08T19:48:38Z"
    with pytest.raises(ValueError, match="stale_required_source:ciq_quarterly_fundamentals"):
        build_weekly_tape_preflight(
            frozen_candidate_entity_ids=_ids(),
            refreshed_candidate_entity_ids=_ids(),
            previous_cut_at="2026-08-08T19:48:38Z",
            current_cut_at="2026-08-14T20:30:00Z",
            source_receipts=receipts,
        )


def test_weekly_tape_preflight_requires_exact_source_set() -> None:
    receipts = _receipts()
    del receipts["nyfed_sofr"]
    with pytest.raises(ValueError, match="required_source_set_invalid"):
        build_weekly_tape_preflight(
            frozen_candidate_entity_ids=_ids(),
            refreshed_candidate_entity_ids=_ids(),
            previous_cut_at="2026-08-08T19:48:38Z",
            current_cut_at="2026-08-14T20:30:00Z",
            source_receipts=receipts,
        )
