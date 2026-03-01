from __future__ import annotations

import numpy as np
import pandas as pd

from scripts import cash_overlay_report as report_mod
from strategies.cash_overlay import TrendFollowingOverlay
from strategies.cash_overlay import VolatilityTargetOverlay


def test_vol_target_overlay_enforces_bounds_and_warmup():
    idx = pd.date_range("2024-01-01", periods=15, freq="B")
    spy_ret = pd.Series([0.0] * len(idx), index=idx, dtype=float)
    spy_tri = pd.Series(np.linspace(100.0, 110.0, len(idx)), index=idx, dtype=float)

    overlay = VolatilityTargetOverlay(target_vol=0.15, lookback_window=5, max_leverage=1.0)
    exposure = overlay.compute_exposure(spy_tri=spy_tri, spy_returns=spy_ret, macro=None)

    assert len(exposure) == len(idx)
    assert float(exposure.iloc[0]) == 1.0
    assert np.isfinite(exposure.to_numpy()).all()
    assert ((exposure >= 0.0) & (exposure <= 1.0)).all()


def test_vol_target_overlay_uses_lagged_returns():
    idx = pd.date_range("2024-02-01", periods=16, freq="B")
    spy_ret = pd.Series(0.005, index=idx, dtype=float)
    spy_ret.iloc[10] = 0.25
    spy_tri = pd.Series(np.linspace(100.0, 130.0, len(idx)), index=idx, dtype=float)

    overlay = VolatilityTargetOverlay(target_vol=0.15, lookback_window=5, max_leverage=1.0)
    exposure = overlay.compute_exposure(spy_tri=spy_tri, spy_returns=spy_ret, macro=None)

    # Shock should not affect the same-day target because realized vol uses shift(1).
    assert float(exposure.loc[idx[10]]) == 1.0
    assert float(exposure.loc[idx[11]]) < 1.0


def test_trend_following_overlay_range_and_direction():
    idx = pd.date_range("2024-03-01", periods=260, freq="B")
    up = np.linspace(100.0, 170.0, 160)
    down = np.linspace(170.0, 120.0, 100)
    spy_tri = pd.Series(np.concatenate([up, down]), index=idx, dtype=float)
    spy_ret = spy_tri.pct_change(fill_method=None).fillna(0.0)

    overlay = TrendFollowingOverlay(ma_windows=[50, 100, 200], ma_weights=[0.5, 0.3, 0.2])
    exposure = overlay.compute_exposure(spy_tri=spy_tri, spy_returns=spy_ret, macro=None)

    assert np.isfinite(exposure.to_numpy()).all()
    assert ((exposure >= 0.0) & (exposure <= 1.0)).all()
    assert float(exposure.iloc[230:].mean()) < float(exposure.iloc[170:200].mean())


def test_simulate_overlay_strategy_lag_and_cost_contract():
    idx = pd.date_range("2024-04-01", periods=5, freq="B")
    target_exposure = pd.Series([0.0, 1.0, 0.0, 1.0, 0.0], index=idx, dtype=float)
    spy_ret = pd.Series([0.0, 0.10, -0.10, 0.05, 0.02], index=idx, dtype=float)
    cash_ret = pd.Series(0.0, index=idx, dtype=float)

    out = report_mod.simulate_overlay_strategy(
        name="toggle",
        target_exposure=target_exposure,
        spy_ret=spy_ret,
        cash_ret=cash_ret,
        cost_bps=10.0,
    )

    expected_executed = np.array([0.0, 0.0, 1.0, 0.0, 1.0], dtype=float)
    expected_turnover = np.array([0.0, 0.0, 1.0, 1.0, 1.0], dtype=float)
    expected_cost = expected_turnover * (10.0 / 10000.0)
    expected_net = expected_executed * spy_ret.to_numpy() - expected_cost

    np.testing.assert_allclose(out["exposure_executed"].to_numpy(), expected_executed, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(out["turnover"].to_numpy(), expected_turnover, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(out["cost"].to_numpy(), expected_cost, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(out["net_return"].to_numpy(), expected_net, rtol=1e-12, atol=1e-12)


def test_simulate_overlay_strategy_cash_component_applied():
    idx = pd.date_range("2024-05-01", periods=4, freq="B")
    target_exposure = pd.Series([1.0, 1.0, 1.0, 1.0], index=idx, dtype=float)
    spy_ret = pd.Series([0.0, 0.02, 0.02, 0.02], index=idx, dtype=float)
    cash_ret = pd.Series([0.001, 0.001, 0.001, 0.001], index=idx, dtype=float)

    out = report_mod.simulate_overlay_strategy(
        name="cash_check",
        target_exposure=target_exposure,
        spy_ret=spy_ret,
        cash_ret=cash_ret,
        cost_bps=5.0,
    )

    expected_executed = np.array([0.0, 1.0, 1.0, 1.0], dtype=float)
    expected_turnover = np.array([0.0, 1.0, 0.0, 0.0], dtype=float)
    expected_cost = expected_turnover * (5.0 / 10000.0)
    expected_net = (expected_executed * spy_ret.to_numpy()) + ((1.0 - expected_executed) * cash_ret.to_numpy()) - expected_cost

    np.testing.assert_allclose(out["net_return"].to_numpy(), expected_net, rtol=1e-12, atol=1e-12)


def test_run_scenarios_and_metrics_summary_contract():
    idx = pd.date_range("2023-01-02", periods=280, freq="B")
    spy_tri = pd.Series(np.linspace(100.0, 140.0, len(idx)), index=idx, dtype=float)
    spy_ret = spy_tri.pct_change(fill_method=None).fillna(0.0)
    cash_ret = pd.Series(0.0001, index=idx, dtype=float)
    macro = pd.DataFrame(index=idx)
    inputs = report_mod.Day3Inputs(spy_tri=spy_tri, spy_ret=spy_ret, cash_ret=cash_ret, macro=macro)

    scenarios = report_mod.run_scenarios(
        data=inputs,
        target_vol=0.15,
        vol_lookbacks=[20, 60, 120],
        cost_bps=5.0,
    )

    expected = {
        "Buy & Hold",
        "Trend SMA200",
        "Vol Target 15% (20d)",
        "Vol Target 15% (60d)",
        "Vol Target 15% (120d)",
        "Trend Multi-Horizon",
    }
    assert expected.issubset(set(scenarios.keys()))

    metrics = report_mod.compute_metrics_summary(scenarios)
    required_cols = {
        "scenario",
        "cagr",
        "ann_vol",
        "sharpe",
        "max_dd",
        "ulcer",
        "turnover_annual",
        "turnover_total",
        "start_date",
        "end_date",
        "n_days",
    }
    assert required_cols.issubset(set(metrics.columns))
    assert expected.issubset(set(metrics["scenario"].tolist()))


def test_load_inputs_uses_datetime_index_for_fr050_context(monkeypatch, tmp_path):
    idx = pd.date_range("2024-06-03", periods=10, freq="B")
    macro_idx = pd.DatetimeIndex(idx)

    macro_df = pd.DataFrame({"spy_tri": np.linspace(100.0, 102.0, len(idx))}, index=macro_idx)
    tri = pd.Series(np.linspace(100.0, 102.0, len(idx)), index=idx, dtype=float)
    ret = tri.pct_change(fill_method=None).fillna(0.0)

    monkeypatch.setattr(report_mod, "_load_macro_frame", lambda path, start, end: macro_df)
    monkeypatch.setattr(report_mod, "_load_spy_tri_from_prices_tri", lambda *args, **kwargs: (tri, ret))

    class _FakeFr050:
        BIL_PERMNO = 92027

        @staticmethod
        def _load_frame(path, start, end):
            return pd.DataFrame({"effr_rate": 5.0}, index=idx)

        @staticmethod
        def _build_context(macro, liquidity):
            assert isinstance(macro.index, pd.DatetimeIndex)
            assert isinstance(liquidity.index, pd.DatetimeIndex)
            return pd.DataFrame({"effr_rate": 5.0}, index=macro.index.union(liquidity.index))

        @staticmethod
        def _load_price_series_from_parquet(permno, prices_path, patch_path, start, end):
            return pd.Series(np.linspace(100.0, 100.5, len(idx)), index=idx, dtype=float)

        @staticmethod
        def build_cash_return(idx, bil_ret, effr_rate, flat_annual_rate=0.02):
            return pd.Series(0.0001, index=idx, dtype=float), pd.Series("BIL", index=idx, dtype=object)

    monkeypatch.setattr(report_mod.baseline_report, "_load_fr050_module", lambda: _FakeFr050())

    liquidity_path = tmp_path / "liquidity_features.parquet"
    liquidity_path.touch()

    out = report_mod._load_inputs(
        start=idx.min(),
        end=idx.max(),
        prices_tri_path=tmp_path / "prices_tri.parquet",
        macro_tri_path=tmp_path / "macro_features_tri.parquet",
        macro_path=tmp_path / "macro_features.parquet",
        liquidity_path=liquidity_path,
        prices_path=tmp_path / "prices.parquet",
        patch_path=tmp_path / "yahoo_patch.parquet",
    )

    assert isinstance(out.spy_tri.index, pd.DatetimeIndex)
    assert isinstance(out.cash_ret.index, pd.DatetimeIndex)
    assert len(out.spy_tri) == len(idx)
