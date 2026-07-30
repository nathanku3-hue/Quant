"""GV-CHALLENGER-PROMOTION-1 shadow-first acceptance tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from gv_portfolio_v0.bounded import load_session
from gv_portfolio_v0.challenger import (
    BOUNDED_TERMINAL_SHA,
    CHALLENGER_SCHEMA,
    DISPOSITION_LIVE,
    DISPOSITION_PRODUCTION_PROMOTE,
    DISPOSITION_SHADOW_ONLY,
    PROMOTION_TIP_SHA,
    REPLAY_CODE_PIN_SHA,
    SCALE_TERMINAL_SHA,
    UNIVERSE_TERMINAL_SHA,
    ChallengerPromotionError,
    assert_challenger_pins,
    branch_pins,
    reject_live_promotion,
    run_challenger_shadow,
)
from gv_portfolio_v0.replay import reconstruct_exact


def test_challenger_pins_separate_promotion_from_terminals() -> None:
    pins = branch_pins()
    assert pins["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert pins["universe_terminal_sha"] == UNIVERSE_TERMINAL_SHA
    assert pins["scale_terminal_sha"] == SCALE_TERMINAL_SHA
    assert pins["bounded_terminal_sha"] == BOUNDED_TERMINAL_SHA
    assert pins["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA
    assert pins["active_implementation_base"] == PROMOTION_TIP_SHA
    assert pins["promotion_tip_sha"] != pins["universe_terminal_sha"]
    assert pins["promotion_tip_sha"] != pins["scale_terminal_sha"]
    assert_challenger_pins()


def test_challenger_shadow_first_preserves_certified_custody(tmp_path: Path) -> None:
    report = run_challenger_shadow(
        root=tmp_path,
        disposition=DISPOSITION_SHADOW_ONLY,
        challenger_label="shadow_candidate_a",
        universe_cells=4,
        universe_cycles=2,
        scale_control_portfolios=2,
        scale_control_cycles=2,
    )
    assert report["schema_version"] == CHALLENGER_SCHEMA
    assert report["shadow_first"] is True
    assert report["disposition"] == DISPOSITION_SHADOW_ONLY
    assert report["live_capital_authorized"] is False
    assert report["limited_live_slice_closed"] is True
    assert report["production_mutation"] is False
    assert report["certified_custody_unmutated"] is True
    assert report["universe_non_drift"] is True
    assert report["scale_non_drift"] is True
    assert report["bounded_non_drift"] is True
    assert report["replay_non_drift"] is True
    assert report["terminal_nav"] == "1499"
    assert report["unexplained_residual"] == "0"
    assert report["universe_terminal_sha"] == UNIVERSE_TERMINAL_SHA
    assert report["scale_terminal_sha"] == SCALE_TERMINAL_SHA
    assert report["bounded_terminal_sha"] == BOUNDED_TERMINAL_SHA
    assert report["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA

    ctrl = report["universe_control"]
    assert ctrl["exceeds_scale_multi_session_slots"] is True
    assert ctrl["scale_non_drift"] is True
    assert ctrl["cross_cell_economic_determinism"] is True
    assert ctrl["unexplained_residual"] == "0"

    evidence_path = Path(report["shadow_evidence_path"])
    assert evidence_path.is_file()
    assert "shadow" in str(evidence_path).replace("\\", "/")

    for proof in report["certified_custody_proofs"]:
        assert proof["certified_unmutated"] is True
        assert proof["replay_non_drift"] is True
        session = load_session(Path(proof["session_path"]).parent)
        assert session["workspace_content_hash"] == proof["workspace_content_hash"]
        reconstruct_exact(
            session["workspace"]["events"],
            expected_book=session["workspace"]["book"],
        )


def test_challenger_rejects_live_dispositions(tmp_path: Path) -> None:
    with pytest.raises(ChallengerPromotionError, match="LIVE_PATH_FORBIDDEN"):
        run_challenger_shadow(
            root=tmp_path / "live",
            disposition=DISPOSITION_LIVE,
        )
    with pytest.raises(ChallengerPromotionError, match="LIVE_PATH_FORBIDDEN"):
        run_challenger_shadow(
            root=tmp_path / "prod",
            disposition=DISPOSITION_PRODUCTION_PROMOTE,
        )
    with pytest.raises(ChallengerPromotionError, match="LIVE_PATH_FORBIDDEN"):
        reject_live_promotion(disposition=DISPOSITION_LIVE)


def test_challenger_rejects_repopulated_root(tmp_path: Path) -> None:
    run_challenger_shadow(
        root=tmp_path,
        universe_cells=4,
        universe_cycles=2,
        scale_control_portfolios=2,
        scale_control_cycles=2,
    )
    with pytest.raises(ChallengerPromotionError, match="CHALLENGER_ROOT_ALREADY_POPULATED"):
        run_challenger_shadow(
            root=tmp_path,
            universe_cells=4,
            universe_cycles=2,
            scale_control_portfolios=2,
            scale_control_cycles=2,
        )


def test_challenger_rejects_unknown_disposition(tmp_path: Path) -> None:
    with pytest.raises(ChallengerPromotionError, match="DISPOSITION_NOT_SHADOW_ONLY"):
        run_challenger_shadow(
            root=tmp_path,
            disposition="SNEAKY_PROMOTE",
            universe_cells=4,
            universe_cycles=2,
        )
