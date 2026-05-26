from __future__ import annotations

import pandas as pd
import pytest

from research.benchmarks import (
    build_cash_benchmark,
    build_pit_equal_weight_benchmark,
    build_required_benchmark_weights,
)


def _target_weights() -> pd.DataFrame:
    return pd.DataFrame(
        {"101": [0.5, 0.0, 0.3], "202": [0.0, 0.4, 0.2]},
        index=pd.date_range("2026-01-02", periods=3, freq="B"),
    )


def test_cash_benchmark_uses_same_dates_and_zero_risky_weights() -> None:
    target_weights = _target_weights()

    cash = build_cash_benchmark(target_weights)

    assert cash.index.equals(target_weights.index)
    assert list(cash.columns) == list(target_weights.columns)
    assert float(cash.to_numpy().sum()) == 0.0


def test_pit_equal_weight_benchmark_uses_same_dates() -> None:
    target_weights = _target_weights()
    calls: list[pd.Timestamp] = []

    def eligible(as_of: pd.Timestamp) -> tuple[str, ...]:
        calls.append(as_of)
        if as_of == target_weights.index[0]:
            return ("101", "not_in_returns")
        return ("101", "202")

    benchmark = build_pit_equal_weight_benchmark(
        target_weights.index,
        target_weights.columns,
        eligible,
    )

    assert calls == list(target_weights.index)
    assert benchmark.index.equals(target_weights.index)
    assert benchmark.loc[target_weights.index[0], "101"] == 1.0
    assert benchmark.loc[target_weights.index[0], "202"] == 0.0
    assert benchmark.loc[target_weights.index[1], "101"] == 0.5
    assert benchmark.loc[target_weights.index[1], "202"] == 0.5


def test_required_pit_benchmark_requires_provider() -> None:
    with pytest.raises(ValueError, match="missing_pit_eligibility_provider"):
        build_required_benchmark_weights(
            _target_weights(),
            {"required": ["pit_equal_weight_eligible_universe"]},
        )


def test_pit_equal_weight_benchmark_rejects_duplicate_provider_assets() -> None:
    target_weights = _target_weights()

    with pytest.raises(ValueError, match="duplicate_pit_eligible_assets"):
        build_pit_equal_weight_benchmark(
            target_weights.index,
            target_weights.columns,
            lambda as_of: ("101", "101", "202"),
        )
