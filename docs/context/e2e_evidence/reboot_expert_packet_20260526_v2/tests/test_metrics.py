from __future__ import annotations

import numpy as np
import pandas as pd

from utils.metrics import compute_cagr
from utils.metrics import compute_max_drawdown
from utils.metrics import compute_sharpe
from utils.metrics import compute_turnover
from utils.metrics import compute_ulcer_index


def test_compute_cagr_matches_expected_period_annualization():
    idx = pd.date_range("2026-01-01", periods=252, freq="B")
    daily = pd.Series(0.001, index=idx)
    curve = (1.0 + daily).cumprod()
    expected = float(curve.iloc[-1] / curve.iloc[0] - 1.0)
    assert compute_cagr(curve) == expected


def test_compute_sharpe_supports_risk_free_returns():
    idx = pd.date_range("2026-01-01", periods=5, freq="B")
    ret = pd.Series([0.01, 0.02, 0.0, 0.01, -0.005], index=idx)
    rf = pd.Series([0.001, 0.001, 0.001, 0.001, 0.001], index=idx)
    excess = ret - rf
    expected = float((excess.mean() / excess.std(ddof=1)) * np.sqrt(252.0))
    assert compute_sharpe(ret, rf_returns=rf) == expected


def test_compute_drawdown_metrics_contract():
    idx = pd.date_range("2026-01-01", periods=4, freq="B")
    curve = pd.Series([1.0, 1.2, 0.9, 1.0], index=idx)
    dd = (curve / curve.cummax()) - 1.0
    expected_max_dd = float(dd.min())
    expected_ulcer = float(np.sqrt(((dd * 100.0) ** 2.0).mean()))

    assert compute_max_drawdown(curve) == expected_max_dd
    assert compute_ulcer_index(curve) == expected_ulcer


def test_compute_turnover_for_series_and_frame():
    idx = pd.date_range("2026-01-01", periods=4, freq="B")
    series = pd.Series([0.0, 0.5, 0.5, 1.0], index=idx)
    expected_series = pd.Series([0.0, 0.5, 0.0, 0.5], index=idx)
    pd.testing.assert_series_equal(compute_turnover(series), expected_series.astype(float))

    frame = pd.DataFrame(
        {
            "a": [0.0, 0.5, 0.5, 1.0],
            "b": [1.0, 0.5, 0.5, 0.0],
        },
        index=idx,
    )
    expected_frame = pd.Series([0.0, 1.0, 0.0, 1.0], index=idx, dtype=float)
    pd.testing.assert_series_equal(compute_turnover(frame), expected_frame)
