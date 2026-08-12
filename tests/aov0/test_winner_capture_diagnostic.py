from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.aov0.winner_capture import (
    WinnerCaptureError,
    build_regime_series,
    deterministic_top_fraction,
    diagnose_stage,
    state_change_anchors,
)


def _dates(count: int) -> pd.DatetimeIndex:
    return pd.bdate_range("2026-01-05", periods=count)


def test_state_change_anchors_use_first_row_and_actual_target_changes_only() -> None:
    dates = _dates(5)
    targets = pd.DataFrame(
        {
            "CIQSEC:1": [0.0, 0.0, 0.2, 0.2, 0.0],
            "CIQSEC:2": [0.5, 0.5, 0.5, 0.5, 0.5],
        },
        index=dates,
    )
    assert list(state_change_anchors(targets)) == [dates[0], dates[2], dates[4]]


def test_top_fraction_has_security_id_ascending_tie_break() -> None:
    values = pd.Series(
        [1.0, 1.0, 0.5, 0.4],
        index=["CIQSEC:20", "CIQSEC:10", "CIQSEC:30", "CIQSEC:40"],
    )
    assert deterministic_top_fraction(values, fraction=0.25) == ("CIQSEC:10",)


def test_regime_rolls_observed_security_rows_not_query_grid_placeholders() -> None:
    dates = _dates(8)
    closes = pd.DataFrame(
        {
            "CIQSEC:1": [1.0, 2.0, np.nan, 3.0, 4.0, np.nan, 5.0, 6.0],
            "CIQSEC:2": [6.0, 5.0, np.nan, 4.0, 3.0, np.nan, 2.0, 1.0],
        },
        index=dates,
    )
    regime = build_regime_series(
        closes,
        active_security_ids=["CIQSEC:1", "CIQSEC:2"],
        sma_window=3,
    )
    assert pd.isna(regime.loc[dates[2]])
    assert regime.loc[dates[3]] == 0.0
    assert regime.loc[dates[7]] == 0.0


def test_diagnostic_funnel_keeps_late_capture_separate_from_entry_lead() -> None:
    dates = _dates(6)
    ids = [f"CIQSEC:{value:02d}" for value in range(20)]
    returns = pd.DataFrame(0.0, index=dates, columns=ids)
    winner = ids[0]
    returns.loc[dates[1], winner] = 0.20
    returns.loc[dates[2], winner] = 0.20
    returns.loc[dates[3], winner] = 0.20

    rule = pd.DataFrame(0.0, index=dates, columns=ids)
    rule.loc[:, ids[1]] = 1.0
    rule.loc[dates[2]:, ids[1]] = 0.0
    rule.loc[dates[2]:, winner] = 1.0
    parent = rule.copy()
    child = parent * 0.5
    parent_exec = parent.shift(1).fillna(0.0)
    child_exec = child.shift(1).fillna(0.0)
    regime = pd.Series(-0.5, index=dates)

    report = diagnose_stage(
        stage="SYNTHETIC",
        total_returns=returns,
        rule100_targets=rule,
        parent_targets=parent,
        child_targets=child,
        parent_executed=parent_exec,
        child_executed=child_exec,
        regime=regime,
        horizons=(3,),
    )
    first = report["horizons"]["3"]["episodes"][0]
    assert first["funnel_counts"]["sizing_eligible"] == 0
    assert first["funnel_counts"]["entry_lead"] == 0
    assert first["funnel_counts"]["contribution_captured"] == 0
    assert first["late_entry_capture_count"] == 1
    winner_row = first["winners"][0]
    assert winner_row["security_id"] == winner
    assert winner_row["late_entry_captured"] is True


def test_child_exposure_above_parent_fails_closed() -> None:
    dates = _dates(4)
    ids = [f"CIQSEC:{value:02d}" for value in range(20)]
    returns = pd.DataFrame(0.0, index=dates, columns=ids)
    parent = pd.DataFrame(0.0, index=dates, columns=ids)
    parent.loc[:, ids[0]] = 0.5
    child = parent.copy()
    child.loc[dates[1], ids[0]] = 0.6
    parent_exec = parent.shift(1).fillna(0.0)
    child_exec = child.shift(1).fillna(0.0)
    with pytest.raises(WinnerCaptureError, match="child_target_exceeds_parent"):
        diagnose_stage(
            stage="SYNTHETIC",
            total_returns=returns,
            rule100_targets=parent,
            parent_targets=parent,
            child_targets=child,
            parent_executed=parent_exec,
            child_executed=child_exec,
            regime=pd.Series(0.0, index=dates),
            horizons=(2,),
        )
