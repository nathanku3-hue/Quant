"""GV-BOUNDED-PORTFOLIO-1 acceptance tests (separate from Replay suite)."""

from __future__ import annotations

from copy import deepcopy

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.bounded import (
    BOUNDED_SCHEMA,
    DEFAULT_CYCLE_COUNT,
    PROMOTION_TIP_SHA,
    REPLAY_CODE_PIN_SHA,
    BoundedPortfolioError,
    assert_replay_baseline_pins,
    branch_pins,
    run_bounded_portfolio,
    run_operating_cycle,
)
from gv_portfolio_v0.replay import reconstruct_exact, replay_idempotent


def test_branch_pins_separate_promotion_tip_from_replay_code_pin() -> None:
    pins = branch_pins()
    assert pins["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert pins["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA
    assert pins["active_implementation_base"] == PROMOTION_TIP_SHA
    assert pins["immutable_replay_code_pin"] == REPLAY_CODE_PIN_SHA
    assert pins["promotion_tip_sha"] != pins["replay_code_pin_sha"]
    assert_replay_baseline_pins()


def test_single_operating_cycle_replay_non_drift() -> None:
    cycle = run_operating_cycle(cycle_index=0)
    assert cycle["replay_non_drift"] is True
    assert cycle["prior_certification_byte_stable"] is True
    assert cycle["security_count"] == 4
    assert cycle["terminal_nav"] == "1499"
    assert cycle["unexplained_residual"] == "0"
    assert cycle["partial_fill_residuals"] == []
    assert cycle["prior_certification_id"]
    assert cycle["certification_id"]
    assert cycle["prior_certification_id"] != cycle["certification_id"]

    observed = cycle["observed_workspace"]
    reconstruct_exact(observed["events"], expected_book=observed["book"])
    replay_idempotent(observed["events"])


def test_bounded_portfolio_repeated_cycles_are_deterministic() -> None:
    report = run_bounded_portfolio(cycles=DEFAULT_CYCLE_COUNT)
    assert report["schema_version"] == BOUNDED_SCHEMA
    assert report["cycle_count"] == DEFAULT_CYCLE_COUNT
    assert report["deterministic_across_cycles"] is True
    assert report["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA
    assert report["terminal_nav"] == "1499"
    assert report["unexplained_residual"] == "0"
    assert len(report["cycles"]) == DEFAULT_CYCLE_COUNT

    # Cycle identities differ by index; economic hashes must match.
    cycle_ids = {row["cycle_id"] for row in report["cycles"]}
    assert len(cycle_ids) == DEFAULT_CYCLE_COUNT
    hashes = {row["observed_book_hash"] for row in report["cycles"]}
    assert len(hashes) == 1
    ledgers = {row["observed_event_ledger_hash"] for row in report["cycles"]}
    assert len(ledgers) == 1
    reports = {row["replay_report_hash"] for row in report["cycles"]}
    assert len(reports) == 1

    correction = report["correction_lineage_probe"]
    assert correction["prior_byte_stable"] is True
    assert correction["certification_id"] != correction["prior_certification_id"]
    assert correction["book_hash"] == report["cycles"][0]["certified_book_hash"]


def test_bounded_report_hash_is_byte_stable() -> None:
    first = run_bounded_portfolio(cycles=2)
    second = run_bounded_portfolio(cycles=2)
    assert first["report_hash"] == second["report_hash"]
    assert canonical_document_bytes(first) == canonical_document_bytes(second)


def test_cycle_count_bounds() -> None:
    with pytest.raises(BoundedPortfolioError, match="BOUNDED_CYCLE_COUNT_MIN_2"):
        run_bounded_portfolio(cycles=1)
    with pytest.raises(BoundedPortfolioError, match="BOUNDED_CYCLE_COUNT_CAP_8"):
        run_bounded_portfolio(cycles=9)


def test_forged_book_is_detected_as_replay_drift() -> None:
    cycle = run_operating_cycle(cycle_index=0)
    forged = deepcopy(cycle["observed_workspace"])
    forged["book"] = dict(forged["book"])
    forged["book"]["terminal_nav"] = "1"
    # reconstruct_exact used by bounded path: direct probe
    with pytest.raises(Exception):
        reconstruct_exact(forged["events"], expected_book=forged["book"])
