from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from research.adapters import (
    DEFAULT_PROMOTION_STATUS,
    DEFAULT_STRATEGY_ROLE,
    adapt_rule100_replay_to_target_weights,
    rule100_replay_to_target_weights,
)


def _replay_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"date": "2026-01-02", "permno": 101, "target_weight": 0.35, "cash_residual": 0.65, "row_role": "daily_portfolio", "context_role": "current_holding"},
            {"date": "2026-01-02", "permno": None, "target_weight": 0.65, "cash_residual": 0.65, "row_role": "daily_portfolio", "context_role": "cash"},
            {"date": "2026-01-03", "permno": 102, "target_weight": 0.30, "cash_residual": 0.70, "row_role": "daily_portfolio", "context_role": "current_holding"},
            {"date": "2026-01-03", "permno": None, "target_weight": 0.70, "cash_residual": 0.70, "row_role": "daily_portfolio", "context_role": "cash"},
        ]
    )


def test_strict_adapter_excludes_explicit_cash_and_requires_permno() -> None:
    result = adapt_rule100_replay_to_target_weights(_replay_frame())
    expected = pd.DataFrame(
        {101: [0.35, 0.0], 102: [0.0, 0.30]},
        index=pd.DatetimeIndex(["2026-01-02", "2026-01-03"], name="date"),
    )
    expected.columns.name = "permno"
    pd.testing.assert_frame_equal(result.target_weights, expected)
    assert result.promotion_status == DEFAULT_PROMOTION_STATUS
    assert result.strategy_role == DEFAULT_STRATEGY_ROLE
    assert result.metadata["identity_contract"] == "PERMNO_REQUIRED_NO_TICKER_ALIAS"
    assert result.metadata["cash_residual_source"] == "validated_replay_cash_residual"


def test_no_ticker_or_asset_fallback_is_allowed() -> None:
    frame = _replay_frame().drop(columns=["permno"]).assign(ticker=["AAA", "CASH", "BBB", "CASH"])
    with pytest.raises(ValueError, match="rule100_replay_missing_required_columns:permno"):
        rule100_replay_to_target_weights(frame)


def test_non_daily_rows_do_not_fail_open() -> None:
    frame = _replay_frame().assign(row_role="buy_sell_decision")
    with pytest.raises(ValueError, match="rule100_replay_no_daily_portfolio_rows"):
        adapt_rule100_replay_to_target_weights(frame)


def test_risky_row_without_permanent_id_blocks() -> None:
    frame = _replay_frame()
    frame.loc[0, "permno"] = None
    with pytest.raises(ValueError, match="rule100_permanent_id_required"):
        adapt_rule100_replay_to_target_weights(frame)


def test_reported_cash_must_equal_mechanical_residual() -> None:
    frame = _replay_frame()
    frame.loc[frame["date"] == "2026-01-02", "cash_residual"] = 0.90
    with pytest.raises(ValueError, match="rule100_cash_residual_mismatch"):
        adapt_rule100_replay_to_target_weights(frame)


def test_duplicate_date_permno_rows_block_instead_of_collapsing() -> None:
    frame = pd.concat([_replay_frame(), _replay_frame().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="rule100_duplicate_date_permno_rows"):
        adapt_rule100_replay_to_target_weights(frame)


def test_replay_performance_columns_are_ignored() -> None:
    frame = _replay_frame()
    frame["portfolio_equity"] = [1.0, 1.0, 999.0, 999.0]
    frame["portfolio_return"] = [0.0, 0.0, 0.9, 0.9]
    with_perf = adapt_rule100_replay_to_target_weights(frame)
    without_perf = adapt_rule100_replay_to_target_weights(frame.drop(columns=["portfolio_equity", "portfolio_return"]))
    pd.testing.assert_frame_equal(with_perf.target_weights, without_perf.target_weights)
    assert set(with_perf.metadata["ignored_replay_performance_columns"]) == {"portfolio_equity", "portfolio_return"}


def test_bundle_identity_metadata_is_preserved_without_aliasing() -> None:
    bundle = SimpleNamespace(
        replay=_replay_frame(),
        run_metadata=SimpleNamespace(
            run_id="run-123",
            source_id="rule100-replay",
            method_id="Rule100",
            input_signatures=({"name": "fixture"},),
        ),
    )
    result = adapt_rule100_replay_to_target_weights(bundle)
    assert result.metadata["run_id"] == "run-123"
    assert result.metadata["source_id"] == "rule100-replay"
    assert result.metadata["method_id"] == "Rule100"
