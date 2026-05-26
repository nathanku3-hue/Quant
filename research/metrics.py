"""Research metrics derived from canonical engine output."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


def build_equity_curve(net_returns: pd.Series) -> pd.Series:
    """Compound net returns into an equity curve starting at 1.0."""

    returns = pd.to_numeric(net_returns, errors="coerce").fillna(0.0)
    return (1.0 + returns).cumprod()


def max_drawdown(equity_curve: pd.Series) -> float:
    """Return minimum peak-to-trough drawdown for an equity curve."""

    if equity_curve.empty:
        return 0.0
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    return float(drawdown.min())


def drawdown_duration(equity_curve: pd.Series) -> int:
    """Return the longest number of consecutive rows spent below prior high."""

    if equity_curve.empty:
        return 0
    running_max = equity_curve.cummax()
    underwater = equity_curve < running_max
    longest = 0
    current = 0
    for is_underwater in underwater:
        if bool(is_underwater):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return int(longest)


def compute_metrics(
    simulation_result: pd.DataFrame,
    executed_weights: pd.DataFrame,
    target_weights: pd.DataFrame,
    *,
    benchmark_result: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Compute mandatory V0 metrics from canonical simulation output."""

    net_ret = pd.to_numeric(simulation_result.get("net_ret", pd.Series(dtype=float)), errors="coerce")
    gross_ret = pd.to_numeric(simulation_result.get("gross_ret", pd.Series(dtype=float)), errors="coerce")
    turnover = pd.to_numeric(simulation_result.get("turnover", pd.Series(dtype=float)), errors="coerce")
    costs = pd.to_numeric(simulation_result.get("cost", pd.Series(dtype=float)), errors="coerce")
    equity_curve = build_equity_curve(net_ret)
    trading_days = int(len(net_ret))

    cumulative_return = float(equity_curve.iloc[-1] - 1.0) if trading_days else 0.0
    annualized_volatility = float(net_ret.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR)) if trading_days else 0.0
    sharpe = (
        float(net_ret.mean() / net_ret.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR))
        if trading_days and float(net_ret.std(ddof=0)) > 0
        else None
    )
    downside = net_ret[net_ret < 0]
    sortino = (
        float(net_ret.mean() / downside.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR))
        if len(downside) > 0 and float(downside.std(ddof=0)) > 0
        else None
    )
    cagr = (
        float(equity_curve.iloc[-1] ** (TRADING_DAYS_PER_YEAR / trading_days) - 1.0)
        if trading_days >= TRADING_DAYS_PER_YEAR and equity_curve.iloc[-1] > 0
        else None
    )

    gross_exposure = executed_weights.abs().sum(axis=1) if not executed_weights.empty else pd.Series(dtype=float)
    cash_residual = 1.0 - executed_weights.sum(axis=1) if not executed_weights.empty else pd.Series(dtype=float)
    rebalance_count = int((target_weights.diff().abs().sum(axis=1).fillna(0.0) > 0).sum())

    metrics: dict[str, Any] = {
        "cumulative_return": cumulative_return,
        "CAGR": cagr,
        "annualized_volatility": annualized_volatility,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "max_drawdown": max_drawdown(equity_curve),
        "drawdown_duration": drawdown_duration(equity_curve),
        "average_turnover": float(turnover.mean()) if len(turnover) else 0.0,
        "total_turnover": float(turnover.sum()) if len(turnover) else 0.0,
        "total_cost_drag": float(costs.sum()) if len(costs) else 0.0,
        "average_gross_exposure": float(gross_exposure.mean()) if len(gross_exposure) else 0.0,
        "average_cash_residual": float(cash_residual.mean()) if len(cash_residual) else 1.0,
        "benchmark_excess_return": None,
        "tracking_error": None,
        "information_ratio": None,
        "missing_executed_return_count": 0,
        "non_finite_input_count": 0,
        "trading_days": trading_days,
        "rebalance_count": rebalance_count,
        "gross_return_sum": float(gross_ret.sum()) if len(gross_ret) else 0.0,
    }

    if benchmark_result is not None and "net_ret" in benchmark_result:
        benchmark_ret = pd.to_numeric(benchmark_result["net_ret"], errors="coerce").reindex(net_ret.index).fillna(0.0)
        benchmark_equity = build_equity_curve(benchmark_ret)
        benchmark_cumulative = float(benchmark_equity.iloc[-1] - 1.0) if len(benchmark_equity) else 0.0
        excess = net_ret.fillna(0.0) - benchmark_ret
        tracking_error = float(excess.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR)) if len(excess) else 0.0
        metrics["benchmark_excess_return"] = cumulative_return - benchmark_cumulative
        metrics["tracking_error"] = tracking_error
        metrics["information_ratio"] = (
            float(excess.mean() / excess.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR))
            if len(excess) and float(excess.std(ddof=0)) > 0
            else None
        )

    return _json_sanitize(metrics)


def _json_sanitize(metrics: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, (float, np.floating)) and not math.isfinite(float(value)):
            sanitized[key] = None
        else:
            sanitized[key] = value
    return sanitized
