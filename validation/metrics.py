from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def coerce_return_series(frame: pd.DataFrame, return_col: str = "net_ret") -> pd.Series:
    if return_col not in frame.columns:
        raise ValueError(f"Missing return column: {return_col}")
    series = pd.to_numeric(frame[return_col], errors="coerce").dropna()
    return series.astype(float)


def summarize_returns(values: pd.Series | np.ndarray | list[float]) -> dict[str, Any]:
    series = pd.Series(values, dtype="float64").dropna()
    observations = int(len(series))
    if observations == 0:
        return {
            "observations": 0,
            "mean_daily_return": None,
            "volatility_daily": None,
            "sharpe_annualized": None,
            "cumulative_return": None,
            "max_drawdown": None,
        }

    mean = float(series.mean())
    vol = float(series.std(ddof=1)) if observations > 1 else 0.0
    sharpe = float((mean / vol) * math.sqrt(252.0)) if vol > 0.0 else None
    equity = (1.0 + series.fillna(0.0)).cumprod()
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    return {
        "observations": observations,
        "mean_daily_return": mean,
        "volatility_daily": vol,
        "sharpe_annualized": sharpe,
        "cumulative_return": float(equity.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
    }

