from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_cross_section.py"


def _load_script_module():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("evaluate_cross_section", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_auto_newey_west_lags_formula_contract():
    mod = _load_script_module()
    n_obs = 250
    expected = int(np.floor(4.0 * ((n_obs / 100.0) ** (2.0 / 9.0))))
    assert mod.auto_newey_west_lags(n_obs) == expected
    assert mod.auto_newey_west_lags(1) == 0


def test_compute_double_sort_builds_positive_spread_when_proxy_monotonic():
    mod = _load_script_module()
    rows: list[dict] = []
    dates = [pd.Timestamp("2024-01-31"), pd.Timestamp("2024-02-29"), pd.Timestamp("2024-03-29")]
    for dt in dates:
        for i in range(1, 101):
            rows.append(
                {
                    "date": dt,
                    "permno": i,
                    "industry": "Semiconductors",
                    "asset_growth_yoy": float(i),
                    "z_inventory_quality_proxy": float(i),
                    "fwd_return": float(i) / 1000.0,
                }
            )
    frame = pd.DataFrame(rows)
    spread_df, high = mod.compute_double_sort(
        frame=frame,
        high_asset_growth_pct=0.30,
        min_high_group_size=1,
    )
    assert not high.empty
    assert not spread_df.empty
    assert (spread_df["spread"] > 0.0).all()


def test_run_fama_macbeth_interaction_recovers_positive_sign():
    mod = _load_script_module()
    rng = np.random.default_rng(42)
    rows: list[dict] = []
    dates = pd.date_range("2022-01-31", periods=36, freq="ME")
    for dt in dates:
        for i in range(60):
            ag = rng.normal(0.0, 1.0)
            zp = rng.normal(0.0, 1.0)
            interaction = ag * zp
            noise = rng.normal(0.0, 0.01)
            fwd = (0.02 * ag) + (0.01 * zp) + (0.05 * interaction) + noise
            rows.append(
                {
                    "date": dt,
                    "fwd_return": fwd,
                    "asset_growth_yoy": ag,
                    "z_inventory_quality_proxy": zp,
                }
            )
    frame = pd.DataFrame(rows)
    betas, summary = mod.run_fama_macbeth(frame=frame, nw_lags=None, min_obs=30)
    assert not betas.empty
    assert not summary.empty
    inter = summary.loc[summary["coefficient"] == "beta_interaction"]
    assert len(inter) == 1
    assert float(inter["mean_beta"].iloc[0]) > 0.0
