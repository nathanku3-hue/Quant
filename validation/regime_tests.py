from __future__ import annotations

from typing import Any

import pandas as pd

from validation.metrics import coerce_return_series
from validation.metrics import summarize_returns


def run_regime_tests(
    frame: pd.DataFrame,
    *,
    return_col: str = "net_ret",
    regime_col: str = "regime",
    min_observations: int = 5,
) -> dict[str, Any]:
    work = frame.copy()
    if regime_col not in work.columns:
        returns = coerce_return_series(work, return_col=return_col)
        median = returns.rolling(20, min_periods=1).std().median()
        work = work.loc[returns.index].copy()
        vol = returns.rolling(20, min_periods=1).std()
        work[regime_col] = ["high_vol" if v > median else "low_vol" for v in vol]
    regimes: dict[str, Any] = {}
    for label, group in work.groupby(regime_col, dropna=False):
        label_s = str(label)
        values = coerce_return_series(group, return_col=return_col)
        regimes[label_s] = summarize_returns(values)
    enough = [
        label
        for label, stats in regimes.items()
        if int(stats.get("observations") or 0) >= int(min_observations)
    ]
    worst_mean = min(
        float(stats["mean_daily_return"])
        for stats in regimes.values()
        if stats.get("mean_daily_return") is not None
    )
    return {
        "regimes": regimes,
        "regimes_with_min_observations": enough,
        "worst_mean_daily_return": float(worst_mean),
        "passed": bool(enough and worst_mean > -0.01),
    }

