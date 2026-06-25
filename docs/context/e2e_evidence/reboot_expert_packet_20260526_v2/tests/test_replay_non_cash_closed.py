"""
Integration test: verify Strategy Replay produces real PIT output (not cash_closed fallback).

Requires:
  - data/processed/prices_tri.parquet
  - data/processed/universe_r3000_daily.parquet
"""
from __future__ import annotations

import os

import pandas as pd
import pytest

PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
PRICES_TRI = os.path.join(PROCESSED_DIR, "prices_tri.parquet")
UNIVERSE_R3000 = os.path.join(PROCESSED_DIR, "universe_r3000_daily.parquet")

skip_if_no_data = pytest.mark.skipif(
    not (os.path.exists(PRICES_TRI) and os.path.exists(UNIVERSE_R3000)),
    reason="Requires prices_tri.parquet and universe_r3000_daily.parquet",
)


@skip_if_no_data
def test_replay_inputs_load_without_error():
    from core.data_orchestrator import load_strategy_replay_inputs

    inputs = load_strategy_replay_inputs(
        as_of_date="2026-05-09",
        start_date="2000-01-01",
        end_date="2026-05-09",
        method="Inverse Volatility",
        controls={"max_weight": 0.35},
        max_weight=0.35,
        universe_mode="r3000_pit",
    )
    assert inputs.prices.shape[0] > 100
    assert inputs.prices.shape[1] > 0
    assert inputs.returns.shape == inputs.prices.shape


@skip_if_no_data
def test_replay_produces_non_cash_closed_output():
    from core.data_orchestrator import load_strategy_replay_inputs
    from strategies.strategy_replay import build_strategy_replay

    inputs = load_strategy_replay_inputs(
        as_of_date="2026-05-09",
        start_date="2026-01-01",
        end_date="2026-05-09",
        method="Inverse Volatility",
        controls={"max_weight": 0.35},
        max_weight=0.35,
        universe_mode="r3000_pit",
    )
    result = build_strategy_replay(
        method="Inverse Volatility",
        controls={"max_weight": 0.35},
        prices=inputs,
        ticker_map=None,
        as_of_range=None,
    )
    assert isinstance(result, pd.DataFrame)
    assert not result.empty, "Replay produced empty DataFrame"
    assert "status" in result.columns
    non_cash = result[result["status"] != "cash_closed"]
    assert not non_cash.empty, (
        "All replay rows are cash_closed — replay is not producing real PIT output. "
        f"Statuses found: {result['status'].unique().tolist()}"
    )
