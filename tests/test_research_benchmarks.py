from __future__ import annotations

import pandas as pd
import pytest

from research.benchmarks import (
    build_cash_benchmark,
    build_economic_cash_frames,
    build_pit_equal_weight_benchmark,
    build_required_risky_benchmark_weights,
    strategy_rebalance_dates,
)


def _target_weights() -> pd.DataFrame:
    return pd.DataFrame(
        {"101": [0.5, 0.5, 0.3, 0.3], "202": [0.0, 0.0, 0.2, 0.2]},
        index=pd.date_range("2026-01-02", periods=4, freq="B"),
    )


def _policy() -> dict[str, object]:
    return {
        "primary": "pit_equal_weight_eligible_universe",
        "required": {
            "cash": {"kind": "implicit_zero_return_cash"},
            "pit_equal_weight_eligible_universe": {"kind": "pit_equal_weight_match_strategy_schedule"},
            "economic_cash": {"kind": "economic_cash_total_return"},
        },
    }


def test_cash_benchmark_uses_same_dates_and_zero_risky_weights() -> None:
    target = _target_weights()
    cash = build_cash_benchmark(target)
    assert cash.index.equals(target.index)
    assert list(cash.columns) == list(target.columns)
    assert float(cash.to_numpy().sum()) == 0.0


def test_pit_equal_weight_rebalances_only_when_strategy_targets_change() -> None:
    target = _target_weights()
    calls: list[pd.Timestamp] = []

    def eligible(as_of: pd.Timestamp) -> tuple[str, ...]:
        calls.append(as_of)
        return ("101",) if as_of == target.index[0] else ("101", "202")

    rebalances = strategy_rebalance_dates(target)
    benchmark = build_pit_equal_weight_benchmark(
        target.index,
        target.columns,
        eligible,
        rebalance_dates=rebalances,
    )
    assert calls == [target.index[0], target.index[2]]
    assert benchmark.loc[target.index[0], "101"] == 1.0
    assert benchmark.loc[target.index[1], "101"] == 1.0
    assert benchmark.loc[target.index[2], "101"] == 0.5
    assert benchmark.loc[target.index[3], "202"] == 0.5


def test_required_pit_benchmark_requires_provider() -> None:
    with pytest.raises(ValueError, match="missing_pit_eligibility_provider"):
        build_required_risky_benchmark_weights(_target_weights(), _policy(), pit_eligibility_provider=None)


def test_pit_equal_weight_rejects_duplicate_provider_assets() -> None:
    target = _target_weights()
    with pytest.raises(ValueError, match="duplicate_pit_eligible_assets"):
        build_pit_equal_weight_benchmark(
            target.index,
            target.columns,
            lambda _as_of: ("101", "101"),
            rebalance_dates=strategy_rebalance_dates(target),
        )


def test_economic_cash_requires_complete_finite_same_calendar_returns() -> None:
    target = _target_weights()
    series = pd.Series([0.0, 0.0001, 0.0001, 0.0001], index=target.index)
    weights, returns = build_economic_cash_frames(target.index, series)
    assert list(weights.columns) == ["ECONOMIC_CASH"]
    assert float(weights.iloc[-1, 0]) == 1.0
    assert returns.index.equals(target.index)

    bad = series.copy()
    bad.iloc[2] = float("nan")
    with pytest.raises(ValueError, match="economic_cash_returns_invalid"):
        build_economic_cash_frames(target.index, bad)
