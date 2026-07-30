"""GV-PORTFOLIO-SCALE-1 acceptance tests (separate from Replay and Bounded suites)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gv_portfolio_v0.bounded import DECLARED_SECURITY_COUNT, load_session
from gv_portfolio_v0.scale import (
    BOUNDED_TERMINAL_SHA,
    DEFAULT_CYCLES_PER_PORTFOLIO,
    DEFAULT_SCALE_PORTFOLIOS,
    PROMOTION_TIP_SHA,
    REPLAY_CODE_PIN_SHA,
    SCALE_SCHEMA,
    PortfolioScaleError,
    assert_scale_pins,
    branch_pins,
    run_portfolio_scale,
)
from gv_portfolio_v0.replay import reconstruct_exact


def test_scale_pins_separate_promotion_from_terminals() -> None:
    pins = branch_pins()
    assert pins["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert pins["bounded_terminal_sha"] == BOUNDED_TERMINAL_SHA
    assert pins["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA
    assert pins["active_implementation_base"] == PROMOTION_TIP_SHA
    assert pins["promotion_tip_sha"] != pins["bounded_terminal_sha"]
    assert pins["promotion_tip_sha"] != pins["replay_code_pin_sha"]
    assert_scale_pins()


def test_scale_exceeds_bounded_v1_universe_and_is_deterministic(
    tmp_path: Path,
) -> None:
    report = run_portfolio_scale(
        root=tmp_path,
        portfolios=DEFAULT_SCALE_PORTFOLIOS,
        cycles_per_portfolio=DEFAULT_CYCLES_PER_PORTFOLIO,
    )
    assert report["schema_version"] == SCALE_SCHEMA
    assert report["portfolio_count"] == DEFAULT_SCALE_PORTFOLIOS
    assert report["cycles_per_portfolio"] == DEFAULT_CYCLES_PER_PORTFOLIO
    assert report["declared_security_count_per_portfolio"] == DECLARED_SECURITY_COUNT
    assert report["declared_scale_security_slots"] == (
        DEFAULT_SCALE_PORTFOLIOS * DECLARED_SECURITY_COUNT
    )
    assert report["exceeds_bounded_v1_universe"] is True
    assert report["declared_scale_security_slots"] > DECLARED_SECURITY_COUNT
    assert report["cross_portfolio_economic_determinism"] is True
    assert report["restart_reopen_verified_at_scale"] is True
    assert report["terminal_nav"] == "1499"
    assert report["unexplained_residual"] == "0"
    assert report["bounded_terminal_sha"] == BOUNDED_TERMINAL_SHA
    assert report["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA

    # Each portfolio consumed prior state with growing event logs
    for seal in report["portfolios"]:
        assert seal["consumed_prior_persisted_state"] is True
        assert seal["replay_non_drift"] is True
        counts = seal["event_counts"]
        assert counts == sorted(counts)
        assert counts[0] < counts[-1]

    # Cross-portfolio economic equality (path-free). Report hashes may differ
    # because each seal's bounded report embeds a distinct session_path.
    finals = {row["final_workspace_content_hash"] for row in report["portfolios"]}
    assert len(finals) == 1
    paths = {row["session_path"] for row in report["portfolios"]}
    assert len(paths) == len(report["portfolios"])
    cycle_id_sets = {tuple(row["cycle_ids"]) for row in report["portfolios"]}
    assert len(cycle_id_sets) == 1
    cert_id_sets = {tuple(row["certification_ids"]) for row in report["portfolios"]}
    assert len(cert_id_sets) == 1
    report_hashes = {row["bounded_report_hash"] for row in report["portfolios"]}
    assert len(report_hashes) == len(report["portfolios"])  # path identity differs


def test_scale_restart_reload_all_sessions(tmp_path: Path) -> None:
    report = run_portfolio_scale(root=tmp_path, portfolios=2, cycles_per_portfolio=2)
    for seal in report["portfolios"]:
        session = load_session(Path(seal["session_root"]))
        assert session["workspace_content_hash"] == seal["final_workspace_content_hash"]
        reconstruct_exact(
            session["workspace"]["events"],
            expected_book=session["workspace"]["book"],
        )


def test_scale_bounds(tmp_path: Path) -> None:
    with pytest.raises(PortfolioScaleError, match="SCALE_PORTFOLIOS_MIN_2"):
        run_portfolio_scale(root=tmp_path / "a", portfolios=1, cycles_per_portfolio=2)
    with pytest.raises(PortfolioScaleError, match="SCALE_CYCLES_MIN_2"):
        run_portfolio_scale(root=tmp_path / "b", portfolios=2, cycles_per_portfolio=1)


def test_scale_rejects_repopulated_root(tmp_path: Path) -> None:
    run_portfolio_scale(root=tmp_path, portfolios=2, cycles_per_portfolio=2)
    with pytest.raises(PortfolioScaleError, match="SCALE_ROOT_ALREADY_POPULATED"):
        run_portfolio_scale(root=tmp_path, portfolios=2, cycles_per_portfolio=2)
