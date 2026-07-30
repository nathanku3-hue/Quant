"""GV-UNIVERSE-SCALE-1 acceptance tests (separate from Replay/Bounded/Scale)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gv_portfolio_v0.bounded import DECLARED_SECURITY_COUNT, load_session
from gv_portfolio_v0.replay import reconstruct_exact
from gv_portfolio_v0.scale import DEFAULT_SCALE_PORTFOLIOS
from gv_portfolio_v0.universe import (
    BOUNDED_TERMINAL_SHA,
    DEFAULT_CYCLES_PER_CELL,
    DEFAULT_UNIVERSE_CELLS,
    PROMOTION_TIP_SHA,
    REPLAY_CODE_PIN_SHA,
    SCALE_MULTI_SESSION_SECURITY_SLOTS,
    SCALE_TERMINAL_SHA,
    UNIVERSE_SCHEMA,
    UniverseScaleError,
    assert_universe_pins,
    branch_pins,
    run_universe_scale,
)


def test_universe_pins_separate_promotion_from_terminals() -> None:
    pins = branch_pins()
    assert pins["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert pins["scale_terminal_sha"] == SCALE_TERMINAL_SHA
    assert pins["bounded_terminal_sha"] == BOUNDED_TERMINAL_SHA
    assert pins["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA
    assert pins["active_implementation_base"] == PROMOTION_TIP_SHA
    assert pins["promotion_tip_sha"] != pins["scale_terminal_sha"]
    assert pins["promotion_tip_sha"] != pins["bounded_terminal_sha"]
    assert pins["promotion_tip_sha"] != pins["replay_code_pin_sha"]
    assert SCALE_MULTI_SESSION_SECURITY_SLOTS == (
        DEFAULT_SCALE_PORTFOLIOS * DECLARED_SECURITY_COUNT
    )
    assert_universe_pins()


def test_universe_exceeds_scale_slots_and_is_deterministic(tmp_path: Path) -> None:
    report = run_universe_scale(
        root=tmp_path,
        cells=DEFAULT_UNIVERSE_CELLS,
        cycles_per_cell=DEFAULT_CYCLES_PER_CELL,
        scale_control_portfolios=2,
        scale_control_cycles=2,
    )
    assert report["schema_version"] == UNIVERSE_SCHEMA
    assert report["cell_count"] == DEFAULT_UNIVERSE_CELLS
    assert report["cycles_per_cell"] == DEFAULT_CYCLES_PER_CELL
    assert report["declared_security_count_per_cell"] == DECLARED_SECURITY_COUNT
    assert report["declared_universe_security_slots"] == (
        DEFAULT_UNIVERSE_CELLS * DECLARED_SECURITY_COUNT
    )
    assert report["scale_multi_session_security_slots"] == (
        DEFAULT_SCALE_PORTFOLIOS * DECLARED_SECURITY_COUNT
    )
    assert report["exceeds_scale_multi_session_slots"] is True
    assert (
        report["declared_universe_security_slots"]
        > report["scale_multi_session_security_slots"]
    )
    assert report["exceeds_bounded_v1_universe"] is True
    assert report["cross_cell_economic_determinism"] is True
    assert report["restart_reopen_verified_at_universe"] is True
    assert report["scale_non_drift"] is True
    assert report["terminal_nav"] == "1499"
    assert report["unexplained_residual"] == "0"
    assert report["scale_terminal_sha"] == SCALE_TERMINAL_SHA
    assert report["bounded_terminal_sha"] == BOUNDED_TERMINAL_SHA
    assert report["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA

    scale_ctrl = report["scale_control"]
    assert scale_ctrl["cross_portfolio_economic_determinism"] is True
    assert scale_ctrl["restart_reopen_verified_at_scale"] is True
    assert scale_ctrl["unexplained_residual"] == "0"
    assert scale_ctrl["terminal_nav"] == "1499"

    for seal in report["cells"]:
        assert seal["consumed_prior_persisted_state"] is True
        assert seal["replay_non_drift"] is True
        counts = seal["event_counts"]
        assert counts == sorted(counts)
        assert counts[0] < counts[-1]

    finals = {row["final_workspace_content_hash"] for row in report["cells"]}
    assert len(finals) == 1
    paths = {row["session_path"] for row in report["cells"]}
    assert len(paths) == len(report["cells"])
    cycle_id_sets = {tuple(row["cycle_ids"]) for row in report["cells"]}
    assert len(cycle_id_sets) == 1
    cert_id_sets = {tuple(row["certification_ids"]) for row in report["cells"]}
    assert len(cert_id_sets) == 1
    report_hashes = {row["bounded_report_hash"] for row in report["cells"]}
    assert len(report_hashes) == len(report["cells"])


def test_universe_restart_reload_all_cells(tmp_path: Path) -> None:
    report = run_universe_scale(
        root=tmp_path,
        cells=4,
        cycles_per_cell=2,
        scale_control_portfolios=2,
        scale_control_cycles=2,
    )
    for seal in report["cells"]:
        session = load_session(Path(seal["session_root"]))
        assert session["workspace_content_hash"] == seal["final_workspace_content_hash"]
        reconstruct_exact(
            session["workspace"]["events"],
            expected_book=session["workspace"]["book"],
        )


def test_universe_bounds(tmp_path: Path) -> None:
    with pytest.raises(UniverseScaleError, match="UNIVERSE_CELLS_MIN_2"):
        run_universe_scale(
            root=tmp_path / "a",
            cells=1,
            cycles_per_cell=2,
            scale_control_portfolios=2,
            scale_control_cycles=2,
        )
    with pytest.raises(UniverseScaleError, match="UNIVERSE_CYCLES_MIN_2"):
        run_universe_scale(
            root=tmp_path / "b",
            cells=4,
            cycles_per_cell=1,
            scale_control_portfolios=2,
            scale_control_cycles=2,
        )
    # 3 cells × 4 = 12 is NOT greater than Scale multi-session slots (12)
    with pytest.raises(UniverseScaleError, match="UNIVERSE_MUST_EXCEED_SCALE_SLOTS"):
        run_universe_scale(
            root=tmp_path / "c",
            cells=3,
            cycles_per_cell=2,
            scale_control_portfolios=2,
            scale_control_cycles=2,
        )


def test_universe_rejects_repopulated_root(tmp_path: Path) -> None:
    run_universe_scale(
        root=tmp_path,
        cells=4,
        cycles_per_cell=2,
        scale_control_portfolios=2,
        scale_control_cycles=2,
    )
    with pytest.raises(UniverseScaleError, match="UNIVERSE_ROOT_ALREADY_POPULATED"):
        run_universe_scale(
            root=tmp_path,
            cells=4,
            cycles_per_cell=2,
            scale_control_portfolios=2,
            scale_control_cycles=2,
        )
