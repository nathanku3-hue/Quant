import numpy as np
import pandas as pd
import pytest

from core.engine import run_simulation


def test_run_simulation_matches_ma_crossover_returns():
    idx = pd.date_range("2026-01-01", periods=8, freq="B")
    prices = pd.Series([100.0, 102.0, 104.0, 103.0, 101.0, 99.0, 100.0, 102.0], index=idx)
    returns = prices.pct_change(fill_method=None).fillna(0.0)

    ma_fast = prices.rolling(2).mean()
    signal = (prices > ma_fast).astype(float)
    target_weights = signal.to_frame("asset")
    returns_df = returns.to_frame("asset")

    sim = run_simulation(target_weights, returns_df, cost_bps=0.0)
    expected = signal.shift(1).fillna(0.0) * returns

    np.testing.assert_allclose(sim["net_ret"].values, expected.values, rtol=1e-12, atol=1e-12)


def test_run_simulation_applies_turnover_costs():
    idx = pd.date_range("2026-01-01", periods=4, freq="B")
    target_weights = pd.DataFrame({"asset": [0.0, 1.0, 0.0, 1.0]}, index=idx)
    returns_df = pd.DataFrame({"asset": [0.0, 0.0, 0.0, 0.0]}, index=idx)

    sim = run_simulation(target_weights, returns_df, cost_bps=0.001)

    # Executed weights are shifted by one bar: [0,0,1,0]
    # Turnover sequence: [0,0,1,1], so cost at bars 3-4 only.
    expected_turnover = np.array([0.0, 0.0, 1.0, 1.0])
    expected_cost = expected_turnover * 0.001

    np.testing.assert_allclose(sim["turnover"].values, expected_turnover, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(sim["cost"].values, expected_cost, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(sim["net_ret"].values, -expected_cost, rtol=1e-12, atol=1e-12)


def test_run_simulation_strict_missing_returns_no_false_positive_on_entry_bar():
    idx = pd.date_range("2026-01-01", periods=2, freq="B")
    target_weights = pd.DataFrame({"asset": [1.0, 1.0]}, index=idx)
    returns_df = pd.DataFrame({"asset": [np.nan, 0.02]}, index=idx)

    sim = run_simulation(
        target_weights=target_weights,
        returns_df=returns_df,
        cost_bps=0.0,
        strict_missing_returns=True,
    )

    # Entry-day target at t has no execution until t+1, so missing t return is allowed.
    np.testing.assert_allclose(sim["net_ret"].values, np.array([0.0, 0.02]), rtol=1e-12, atol=1e-12)


def test_run_simulation_strict_missing_returns_fails_on_exit_bar_exposure():
    idx = pd.date_range("2026-01-01", periods=2, freq="B")
    target_weights = pd.DataFrame({"asset": [1.0, 0.0]}, index=idx)
    returns_df = pd.DataFrame({"asset": [0.01, np.nan]}, index=idx)

    with pytest.raises(RuntimeError, match="executed exposures"):
        run_simulation(
            target_weights=target_weights,
            returns_df=returns_df,
            cost_bps=0.0,
            strict_missing_returns=True,
        )
