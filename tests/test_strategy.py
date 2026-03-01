import numpy as np
import pandas as pd

from strategies.investor_cockpit import InvestorCockpitStrategy


def test_generate_weights_handles_empty_prices():
    prices = pd.DataFrame(index=pd.DatetimeIndex([]), columns=[101, 202], dtype=float)
    macro = pd.DataFrame(index=pd.DatetimeIndex([]), columns=["vix_proxy"], dtype=float)
    strat = InvestorCockpitStrategy()

    weights, regime, details = strat.generate_weights(prices, fundamentals=None, macro=macro)

    assert isinstance(weights, pd.DataFrame)
    assert isinstance(regime, pd.Series)
    assert weights.empty
    assert regime.empty
    assert details["status"] == "⚪ NO DATA"
    assert details["states"] == {}


def test_generate_weights_handles_single_row_as_neutral_hold():
    idx = pd.to_datetime(["2026-02-14"])
    prices = pd.DataFrame({101: [100.0], 202: [50.0]}, index=idx)
    macro = pd.DataFrame({"vix_proxy": [15.0]}, index=idx)
    strat = InvestorCockpitStrategy()

    weights, regime, details = strat.generate_weights(prices, fundamentals=None, macro=macro)

    assert weights.shape == prices.shape
    assert (weights.iloc[-1] == 0.0).all()
    assert regime.iloc[-1] == 1.0
    assert details["status"] == "⚪ NEUTRAL (<2 bars)"
    assert details["states"][101]["state"] == "HOLD"
    assert details["states"][202]["state"] == "HOLD"


def test_generate_weights_known_trend_conviction_score():
    idx = pd.date_range("2025-01-01", periods=260, freq="B")
    prices = pd.DataFrame({101: np.linspace(100.0, 220.0, len(idx))}, index=idx)
    # Falling VIX should score Macro=2 under current logic.
    macro = pd.DataFrame({"vix_proxy": np.linspace(30.0, 10.0, len(idx))}, index=idx)
    strat = InvestorCockpitStrategy(green_candle=True, use_dynamic_params=False)

    _, _, details = strat.generate_weights(prices, fundamentals=None, macro=macro)

    # Trend(3) + Value(0) + Macro(2) + Momentum(2) = 7
    assert details["conviction"][101] == 7
    assert details["cv_trend"][101] == 3
    assert details["cv_value"][101] == 0
    assert details["cv_macro"] == 2
    assert details["cv_mom"][101] == 2
