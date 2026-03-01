from __future__ import annotations

import numpy as np
import pandas as pd


def _clean_series(values: pd.Series | np.ndarray | list[float]) -> pd.Series:
    series = pd.Series(values) if not isinstance(values, pd.Series) else values.copy()
    series = pd.to_numeric(series, errors="coerce")
    series = series.replace([np.inf, -np.inf], np.nan)
    return series


def _drawdown_series(equity_curve: pd.Series | np.ndarray | list[float]) -> pd.Series:
    eq = _clean_series(equity_curve)
    peak = eq.cummax()
    return (eq / peak) - 1.0


def compute_cagr(equity_curve: pd.Series | np.ndarray | list[float]) -> float:
    eq = _clean_series(equity_curve).dropna()
    if len(eq) < 2:
        return float("nan")
    start = float(eq.iloc[0])
    end = float(eq.iloc[-1])
    if start <= 0.0 or end <= 0.0:
        return float("nan")
    years = max(len(eq) / 252.0, 1e-12)
    return float((end / start) ** (1.0 / years) - 1.0)


def compute_sharpe(
    returns: pd.Series | np.ndarray | list[float],
    rf_returns: pd.Series | np.ndarray | list[float] | None = None,
    periods_per_year: float = 252.0,
) -> float:
    r = _clean_series(returns)
    if rf_returns is not None:
        rf = _clean_series(rf_returns).reindex(r.index)
        r = r - rf
    r = r.dropna()
    if len(r) < 2:
        return float("nan")
    sigma = float(r.std(ddof=1))
    if not np.isfinite(sigma) or sigma <= 0.0:
        return float("nan")
    return float((r.mean() / sigma) * np.sqrt(float(periods_per_year)))


def compute_max_drawdown(equity_curve: pd.Series | np.ndarray | list[float]) -> float:
    dd = _drawdown_series(equity_curve).dropna()
    if dd.empty:
        return float("nan")
    return float(dd.min())


def compute_ulcer_index(equity_curve: pd.Series | np.ndarray | list[float]) -> float:
    dd = _drawdown_series(equity_curve).dropna()
    if dd.empty:
        return float("nan")
    dd_pct = dd * 100.0
    return float(np.sqrt((dd_pct**2.0).mean()))


def compute_turnover(weights: pd.Series | pd.DataFrame) -> pd.Series:
    if isinstance(weights, pd.DataFrame):
        frame = weights.apply(pd.to_numeric, errors="coerce")
        return frame.diff().abs().sum(axis=1).fillna(0.0).astype(float)

    series = _clean_series(weights)
    return series.diff().abs().fillna(0.0).astype(float)

