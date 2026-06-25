from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategies.adaptive_trend import AdaptiveTrendStrategy


def _prices(days: int = 240) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=days, freq="B")
    return pd.DataFrame(
        {
            101: np.linspace(100.0, 180.0, days),
            202: np.linspace(50.0, 90.0, days),
        },
        index=idx,
    )


def _macro(spy_close: np.ndarray, vix_proxy: float) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=len(spy_close), freq="B")
    return pd.DataFrame(
        {
            "spy_close": spy_close,
            "vix_proxy": np.full(len(spy_close), vix_proxy),
        },
        index=idx,
    )


@pytest.mark.parametrize(
    ("spy_close", "vix_proxy", "expected_multiplier", "expected_status"),
    [
        (np.linspace(300.0, 520.0, 240), 15.0, 1.0, "ATTACK"),
        (np.linspace(300.0, 520.0, 240), 25.0, 0.7, "CAUTION"),
        (np.linspace(520.0, 300.0, 240), 15.0, 0.5, "DEFENSE"),
    ],
)
def test_adaptive_trend_regime_transitions(
    spy_close: np.ndarray,
    vix_proxy: float,
    expected_multiplier: float,
    expected_status: str,
) -> None:
    prices = _prices(len(spy_close))
    strat = AdaptiveTrendStrategy(
        atr_period=5,
        stop_lookback=10,
        vol_lookback=5,
        ma_lookback=50,
        min_price=1.0,
        min_dollar_vol=0.0,
    )

    weights, regime, details = strat.generate_weights(prices, fundamentals=None, macro=_macro(spy_close, vix_proxy))

    assert details["multiplier"] == pytest.approx(expected_multiplier)
    assert expected_status in details["status"]
    assert regime.iloc[-1] == pytest.approx(expected_multiplier)
    assert weights.sum(axis=1).iloc[-1] <= expected_multiplier + 1e-12
    assert weights.index.equals(prices.index)


def test_adaptive_trend_handles_empty_signal_as_zero_weights() -> None:
    prices = _prices()
    macro = _macro(np.linspace(300.0, 520.0, len(prices)), 15.0)
    strat = AdaptiveTrendStrategy(min_price=10_000.0)

    weights, regime, details = strat.generate_weights(prices, fundamentals=None, macro=macro)

    assert (weights == 0.0).all().all()
    assert regime.iloc[-1] == pytest.approx(1.0)
    assert "ATTACK" in details["status"]
