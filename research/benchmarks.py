"""Benchmark constructors for canonical research runs."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import pandas as pd


PITEligibilityProvider = Callable[[pd.Timestamp], Iterable[Any]]


def build_cash_benchmark(target_weights: pd.DataFrame) -> pd.DataFrame:
    """Return zero risky-asset weights on the same dates and columns."""

    return pd.DataFrame(0.0, index=target_weights.index.copy(), columns=target_weights.columns.copy())


def build_pit_equal_weight_benchmark(
    dates: Sequence[Any],
    asset_columns: Sequence[Any],
    eligibility_provider: PITEligibilityProvider,
) -> pd.DataFrame:
    """Build a same-calendar PIT equal-weight risky-asset benchmark."""

    date_index = pd.DatetimeIndex(pd.to_datetime(list(dates)))
    columns = pd.Index(asset_columns)
    rows: list[pd.Series] = []
    for date in date_index:
        eligible_raw = tuple(eligibility_provider(pd.Timestamp(date)))
        eligible = [asset for asset in eligible_raw if asset in columns]
        if len(set(eligible)) != len(eligible):
            raise ValueError(f"duplicate_pit_eligible_assets:{pd.Timestamp(date).date().isoformat()}")
        row = pd.Series(0.0, index=columns, dtype=float)
        if eligible:
            weight = 1.0 / float(len(eligible))
            row.loc[eligible] = weight
        rows.append(row)
    return pd.DataFrame(rows, index=date_index, columns=columns, dtype=float)


def required_benchmark_names(policy: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Read required benchmark names from a cartridge policy."""

    if not policy:
        return ()
    return tuple(str(name) for name in (policy.get("required") or ()))


def build_required_benchmark_weights(
    target_weights: pd.DataFrame,
    policy: Mapping[str, Any],
    *,
    pit_eligibility_provider: PITEligibilityProvider | None = None,
) -> dict[str, pd.DataFrame]:
    """Build required benchmark target matrices for the runner."""

    benchmarks: dict[str, pd.DataFrame] = {}
    for name in required_benchmark_names(policy):
        if name == "cash":
            benchmarks[name] = build_cash_benchmark(target_weights)
        elif name == "pit_equal_weight_eligible_universe":
            if pit_eligibility_provider is None:
                raise ValueError("missing_pit_eligibility_provider")
            benchmarks[name] = build_pit_equal_weight_benchmark(
                target_weights.index,
                target_weights.columns,
                pit_eligibility_provider,
            )
        else:
            raise ValueError(f"unsupported_required_benchmark:{name}")
    return benchmarks
