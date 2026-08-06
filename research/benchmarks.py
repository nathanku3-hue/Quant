"""Strict benchmark constructors for canonical AOV research runs."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from research.strategy_cartridge import MANDATORY_BENCHMARKS


PITEligibilityProvider = Callable[[pd.Timestamp], Iterable[Any]]


def build_cash_benchmark(target_weights: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(0.0, index=target_weights.index.copy(), columns=target_weights.columns.copy())


def strategy_rebalance_dates(target_weights: pd.DataFrame) -> pd.DatetimeIndex:
    if target_weights.empty:
        return pd.DatetimeIndex([])
    numeric = target_weights.astype(float)
    changed = numeric.ne(numeric.shift(1)).any(axis=1)
    changed.iloc[0] = True
    return pd.DatetimeIndex(target_weights.index[changed])


def build_pit_equal_weight_benchmark(
    dates: Sequence[Any],
    asset_columns: Sequence[Any],
    eligibility_provider: PITEligibilityProvider,
    *,
    rebalance_dates: Sequence[Any],
) -> pd.DataFrame:
    """Build PIT equal-weight targets only at strategy decision dates, then hold."""

    date_index = pd.DatetimeIndex(pd.to_datetime(list(dates)))
    columns = pd.Index(asset_columns)
    rebalance_index = pd.DatetimeIndex(pd.to_datetime(list(rebalance_dates)))
    if not rebalance_index.isin(date_index).all():
        raise ValueError("benchmark_rebalance_date_outside_calendar")

    output = pd.DataFrame(np.nan, index=date_index, columns=columns, dtype=float)
    for date in rebalance_index:
        eligible_raw = tuple(eligibility_provider(pd.Timestamp(date)))
        eligible = [asset for asset in eligible_raw if asset in columns]
        if len(set(eligible)) != len(eligible):
            raise ValueError(f"duplicate_pit_eligible_assets:{pd.Timestamp(date).date().isoformat()}")
        row = pd.Series(0.0, index=columns, dtype=float)
        if eligible:
            row.loc[eligible] = 1.0 / float(len(eligible))
        output.loc[date] = row
    if output.iloc[0].isna().any():
        raise ValueError("benchmark_first_date_must_rebalance")
    return output.ffill().fillna(0.0)


def build_economic_cash_frames(
    target_dates: Sequence[Any],
    economic_cash_returns: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.DatetimeIndex(pd.to_datetime(list(target_dates)))
    series = pd.to_numeric(economic_cash_returns, errors="coerce")
    series.index = pd.DatetimeIndex(pd.to_datetime(series.index))
    series = series.reindex(dates)
    if series.isna().any() or not np.isfinite(series.to_numpy(dtype=float)).all():
        raise ValueError("economic_cash_returns_invalid")
    weights = pd.DataFrame({"ECONOMIC_CASH": 1.0}, index=dates)
    returns = pd.DataFrame({"ECONOMIC_CASH": series.to_numpy(dtype=float)}, index=dates)
    return weights, returns


def required_benchmark_names(policy: Mapping[str, Any]) -> tuple[str, ...]:
    required = policy.get("required")
    if not isinstance(required, Mapping) or set(required) != set(MANDATORY_BENCHMARKS):
        raise ValueError("mandatory_benchmark_contracts_missing")
    return tuple(MANDATORY_BENCHMARKS)


def build_required_risky_benchmark_weights(
    target_weights: pd.DataFrame,
    policy: Mapping[str, Any],
    *,
    pit_eligibility_provider: PITEligibilityProvider | None,
) -> dict[str, pd.DataFrame]:
    names = required_benchmark_names(policy)
    benchmarks: dict[str, pd.DataFrame] = {}
    if "cash" in names:
        benchmarks["cash"] = build_cash_benchmark(target_weights)
    if "pit_equal_weight_eligible_universe" in names:
        if pit_eligibility_provider is None:
            raise ValueError("missing_pit_eligibility_provider")
        benchmarks["pit_equal_weight_eligible_universe"] = build_pit_equal_weight_benchmark(
            target_weights.index,
            target_weights.columns,
            pit_eligibility_provider,
            rebalance_dates=strategy_rebalance_dates(target_weights),
        )
    return benchmarks
