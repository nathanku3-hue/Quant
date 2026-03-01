from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "baseline_report.py"


def _load_script_module():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("baseline_report", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_execution_lag_via_engine_path(monkeypatch):
    mod = _load_script_module()
    idx = pd.date_range("2026-01-01", periods=4, freq="B")
    spy_close = pd.Series([100.0, 110.0, 121.0, 133.1], index=idx)
    cash_ret = pd.Series([0.0, 0.0, 0.0, 0.0], index=idx)

    call_counter = {"n": 0}
    original = mod.engine.run_simulation

    def _wrapped(*args, **kwargs):
        call_counter["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(mod.engine, "run_simulation", _wrapped)
    out = mod.run_baselines(
        spy_close=spy_close,
        cash_ret=cash_ret,
        cost_bps=0.0,
        trend_sma_window=2,
    )

    detail = out.details["buy_hold_spy"]
    np.testing.assert_allclose(
        detail["executed_weight_spy"].values,
        np.array([0.0, 1.0, 1.0, 1.0]),
        rtol=1e-12,
        atol=1e-12,
    )

    spy_ret = spy_close.pct_change(fill_method=None).fillna(0.0)
    expected_net = np.array([0.0, spy_ret.iloc[1], spy_ret.iloc[2], spy_ret.iloc[3]], dtype=float)
    np.testing.assert_allclose(detail["net_ret"].values, expected_net, rtol=1e-12, atol=1e-12)
    assert call_counter["n"] == 3


def test_turnover_and_cost_handling():
    mod = _load_script_module()
    idx = pd.date_range("2026-02-02", periods=5, freq="B")
    spy_close = pd.Series([100.0, 110.0, 90.0, 120.0, 80.0], index=idx)
    spy_ret = spy_close.pct_change(fill_method=None).fillna(0.0)
    cash_ret = pd.Series(0.0, index=idx)
    target_spy = pd.Series([0.0, 1.0, 0.0, 1.0, 0.0], index=idx)

    detail, metrics = mod.simulate_single_baseline(
        name="toggle",
        target_weight_spy=target_spy,
        spy_ret=spy_ret,
        cash_ret=cash_ret,
        cost_bps=10.0,
    )

    expected_executed = np.array([0.0, 0.0, 1.0, 0.0, 1.0], dtype=float)
    expected_turnover = np.array([0.0, 0.0, 1.0, 1.0, 1.0], dtype=float)
    expected_cost = expected_turnover * (10.0 / 10000.0)
    expected_net = expected_executed * spy_ret.values - expected_cost

    np.testing.assert_allclose(detail["executed_weight_spy"].values, expected_executed, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(detail["turnover"].values, expected_turnover, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(detail["cost"].values, expected_cost, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(detail["net_ret"].values, expected_net, rtol=1e-12, atol=1e-12)
    assert float(metrics["turnover_total"]) == float(expected_turnover.sum())
    assert float(metrics["turnover_annual"]) == float(expected_turnover.mean() * 252.0)


def test_trend_filter_state_transitions_default_risk_off():
    mod = _load_script_module()
    idx = pd.date_range("2026-03-02", periods=5, freq="B")
    spy_close = pd.Series([100.0, 110.0, 90.0, 120.0, 80.0], index=idx)
    cash_ret = pd.Series(0.0, index=idx)

    out = mod.run_baselines(
        spy_close=spy_close,
        cash_ret=cash_ret,
        cost_bps=0.0,
        trend_sma_window=2,
    )
    trend_target = out.details["trend_sma200"]["target_weight_spy"]

    np.testing.assert_allclose(
        trend_target.values,
        np.array([0.5, 1.0, 0.5, 1.0, 0.5]),
        rtol=1e-12,
        atol=1e-12,
    )


def test_metric_field_contract():
    mod = _load_script_module()
    idx = pd.date_range("2026-04-01", periods=12, freq="B")
    spy_close = pd.Series(np.linspace(100.0, 112.0, len(idx)), index=idx)
    cash_ret = pd.Series(0.0001, index=idx)

    out = mod.run_baselines(
        spy_close=spy_close,
        cash_ret=cash_ret,
        cost_bps=5.0,
        trend_sma_window=3,
    )

    required = {
        "baseline",
        "cagr",
        "sharpe",
        "max_dd",
        "ulcer",
        "turnover_total",
        "turnover_annual",
        "start_date",
        "end_date",
        "n_days",
    }
    assert required.issubset(set(out.metrics.columns))
    assert set(out.metrics["baseline"].tolist()) == {"Buy & Hold SPY", "Static 50/50", "Trend SMA200"}


def test_cli_output_args_defaults(monkeypatch):
    mod = _load_script_module()
    monkeypatch.setattr(sys, "argv", ["baseline_report.py"])
    args = mod.parse_args()
    assert args.output_csv.endswith("data\\processed\\phase18_day1_baselines.csv")
    assert args.output_plot.endswith("data\\processed\\phase18_day1_equity_curves.png")
