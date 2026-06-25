from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from scripts.phase20_full_backtest import _build_phase20_plan
from scripts.phase20_full_backtest import _load_regime_states


def test_load_regime_states_consumes_macro_gates_with_shift(tmp_path: Path) -> None:
    gates_path = tmp_path / "macro_gates.parquet"
    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
            "state": ["GREEN", "RED"],
            "scalar": [1.0, 0.0],
            "cash_buffer": [0.0, 0.5],
            "momentum_entry": [True, False],
            "reasons": ["risk_normalized", "vix_backwardation"],
        }
    ).to_parquet(gates_path, index=False)

    feature_dates = pd.DatetimeIndex(
        [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-04")]
    )
    regime, reason, controls = _load_regime_states(
        start_date=pd.Timestamp("2024-01-01"),
        end_date=pd.Timestamp("2024-01-10"),
        feature_dates=feature_dates,
        macro_path=tmp_path / "missing_macro.parquet",
        liquidity_path=tmp_path / "missing_liq.parquet",
        macro_gates_path=gates_path,
        return_controls=True,
    )

    # Warmup after shift.
    d0 = pd.Timestamp("2024-01-02")
    assert regime.loc[d0] == "AMBER"
    assert float(controls.loc[d0, "gate_scalar"]) == 0.5
    assert float(controls.loc[d0, "cash_pct"]) == 0.25
    assert bool(controls.loc[d0, "momentum_entry"]) is False

    # Day t consumes controls from t-1.
    d1 = pd.Timestamp("2024-01-03")
    assert regime.loc[d1] == "GREEN"
    assert float(controls.loc[d1, "gate_scalar"]) == 1.0
    assert float(controls.loc[d1, "cash_pct"]) == 0.0
    assert bool(controls.loc[d1, "momentum_entry"]) is True
    assert str(reason.loc[d1]) == "risk_normalized"

    d2 = pd.Timestamp("2024-01-04")
    assert regime.loc[d2] == "RED"
    assert float(controls.loc[d2, "gate_scalar"]) == 0.0
    assert float(controls.loc[d2, "cash_pct"]) == 0.5
    assert bool(controls.loc[d2, "momentum_entry"]) is False
    assert str(reason.loc[d2]) == "vix_backwardation"


def test_build_phase20_plan_applies_macro_momentum_and_scalar_budget() -> None:
    dt = pd.Timestamp("2024-12-31")
    conviction = pd.DataFrame(
        {
            "date": [dt, dt, dt, dt],
            "permno": [101, 202, 303, 404],
            "score": [9.0, 8.0, 7.0, 6.0],
            "conviction_score": [9.0, 8.5, 8.0, 7.5],
            "regime": ["GREEN", "GREEN", "GREEN", "GREEN"],
            "entry_gate": [True, True, True, True],
            "avoid_or_short_flag": [False, False, False, False],
        }
    )

    controls_block = pd.DataFrame(
        {
            "gate_scalar": [0.3],
            "cash_pct": [0.9],
            "momentum_entry": [False],
        },
        index=pd.DatetimeIndex([dt]),
    )
    plan_block, weights_block, exposure_block = _build_phase20_plan(
        conviction_df=conviction,
        top_n_green=4,
        top_n_amber=2,
        max_gross_exposure=1.0,
        softmax_temperature=1.0,
        gate_controls=controls_block,
    )
    assert plan_block["selected"].sum() == 0
    assert np.isclose(float(weights_block.sum(axis=1).iloc[0]), 0.0, atol=1e-12)
    assert np.isclose(float(exposure_block["gross_exposure"].iloc[0]), 0.0, atol=1e-12)

    controls_live = controls_block.copy()
    controls_live["momentum_entry"] = True
    plan_live, weights_live, exposure_live = _build_phase20_plan(
        conviction_df=conviction,
        top_n_green=4,
        top_n_amber=2,
        max_gross_exposure=1.0,
        softmax_temperature=1.0,
        gate_controls=controls_live,
    )

    assert plan_live["selected"].sum() == 4
    # risk_budget=min(1-cash_pct, gate_scalar)=min(0.1,0.3)=0.1
    assert np.isclose(float(weights_live.sum(axis=1).iloc[0]), 0.1, atol=1e-9)
    assert np.isclose(float(exposure_live["gross_exposure"].iloc[0]), 0.1, atol=1e-9)
    assert bool(exposure_live["momentum_entry"].iloc[0]) is True
    assert np.isclose(float(exposure_live["gate_scalar"].iloc[0]), 0.3, atol=1e-12)
