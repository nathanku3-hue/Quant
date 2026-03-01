from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from utils.metrics import compute_cagr as ssot_compute_cagr
from utils.metrics import compute_max_drawdown as ssot_compute_max_drawdown
from utils.metrics import compute_sharpe as ssot_compute_sharpe
from utils.metrics import compute_ulcer_index as ssot_compute_ulcer_index


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = ROOT / "backtests" / "verify_phase13_walkforward.py"


def _load_verifier():
    assert VERIFIER_PATH.exists(), f"Missing verifier script: {VERIFIER_PATH}"
    spec = importlib.util.spec_from_file_location("verify_phase13_walkforward", VERIFIER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_map_governor_to_signal_weight():
    mod = _load_verifier()
    idx = pd.date_range("2026-01-01", periods=4, freq="B")
    gov = pd.Series(["GREEN", "AMBER", "RED", "UNKNOWN"], index=idx)
    w = mod.map_governor_to_signal_weight(gov)
    np.testing.assert_allclose(w.values, [1.0, 0.5, 0.0, 0.5], rtol=1e-12, atol=1e-12)


def test_run_walkforward_enforces_t_plus_one_execution():
    mod = _load_verifier()
    idx = pd.date_range("2026-01-01", periods=3, freq="B")
    governor = pd.Series(["GREEN", "GREEN", "RED"], index=idx)
    spy_close = pd.Series([100.0, 110.0, 121.0], index=idx)
    cash_ret = pd.Series([0.0, 0.0, 0.0], index=idx)

    out = mod.run_walkforward(governor_state=governor, spy_close=spy_close, cash_ret=cash_ret, cost_bps=0.0)
    # signal weights: [1,1,0] -> executed at t+1: [0,1,1]
    np.testing.assert_allclose(out["executed_weight"].values, [0.0, 1.0, 1.0], rtol=1e-12, atol=1e-12)
    # spy returns: [0,0.1,0.1], strategy uses executed weights
    np.testing.assert_allclose(out["strategy_ret"].values, [0.0, 0.1, 0.1], rtol=1e-12, atol=1e-12)


def test_cash_return_hierarchy_prefers_bil_then_effr_then_flat():
    mod = _load_verifier()
    idx = pd.date_range("2026-01-01", periods=3, freq="B")
    bil_ret = pd.Series([np.nan, 0.001, np.nan], index=idx)
    effr = pd.Series([5.0, 5.0, np.nan], index=idx)  # annual percent

    cash_ret, source = mod.build_cash_return(idx=idx, bil_ret=bil_ret, effr_rate=effr, flat_annual_rate=0.02)
    effr_daily = 0.05 / 252.0

    assert source.iloc[0] == "EFFR"
    assert source.iloc[1] == "BIL"
    assert source.iloc[2] == "EFFR"  # EFFR path is forward-filled.
    assert cash_ret.iloc[0] == np.float64(effr_daily)
    assert cash_ret.iloc[1] == np.float64(0.001)

    # Explicit no-EFFR case should hit flat fallback.
    cash_ret2, source2 = mod.build_cash_return(
        idx=idx,
        bil_ret=pd.Series([np.nan, np.nan, np.nan], index=idx),
        effr_rate=pd.Series([np.nan, np.nan, np.nan], index=idx),
        flat_annual_rate=0.02,
    )
    assert (source2 == "FLAT").all()
    np.testing.assert_allclose(cash_ret2.values, np.full(len(idx), 0.02 / 252.0), rtol=1e-12, atol=1e-12)


def test_compute_summary_contract_fields_exist():
    mod = _load_verifier()
    idx = pd.date_range("2026-01-01", periods=10, freq="B")
    history = pd.DataFrame(
        {
            "equity_curve": np.linspace(1.0, 1.08, len(idx)),
            "buyhold_curve": np.linspace(1.0, 1.05, len(idx)),
            "strategy_ret": np.full(len(idx), 0.001),
            "buyhold_ret": np.full(len(idx), 0.0008),
        },
        index=idx,
    )
    summary = mod.compute_summary(history)
    required = {
        "cagr_strategy",
        "cagr_buyhold",
        "sharpe_strategy",
        "sharpe_buyhold",
        "max_dd_strategy",
        "max_dd_buyhold",
        "ulcer_strategy",
        "ulcer_buyhold",
        "total_return_strategy",
        "total_return_buyhold",
        "pass_ulcer",
        "pass_maxdd",
        "pass_sharpe",
        "pass_total_return",
        "overall_pass",
    }
    assert required.issubset(set(summary.keys()))


def test_metric_helpers_delegate_to_ssot():
    mod = _load_verifier()
    idx = pd.date_range("2026-01-01", periods=8, freq="B")
    ret = pd.Series([0.0, 0.01, -0.005, 0.004, -0.003, 0.006, 0.002, -0.001], index=idx)
    curve = (1.0 + ret).cumprod()

    assert mod.compute_cagr(curve) == ssot_compute_cagr(curve)
    assert mod.compute_sharpe(ret) == ssot_compute_sharpe(ret)
    assert mod.compute_max_drawdown(curve) == ssot_compute_max_drawdown(curve)
    assert mod.compute_ulcer_index(curve) == ssot_compute_ulcer_index(curve)
