from __future__ import annotations

from pathlib import Path
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
            {
                "date": "2026-01-03",
                "method": "Rule of 100",
                "ticker": "BBB",
                "permno": 102,
                "target_weight": 0.30,
                "cash_residual": 0.70,
                "row_role": "daily_portfolio",
                "source": "rule100_softmax_v1_replay",
            },
            {
                "date": "2026-01-03",
                "method": "Rule of 100",
                "ticker": "CASH",
                "permno": "CASH",
                "target_weight": 0.70,
                "cash_residual": 0.70,
                "row_role": "daily_portfolio",
                "source": "rule100_softmax_v1_replay",
            },
            {
                "date": "2026-01-02",
                "method": "Rule of 100",
                "ticker": "AAA",
                "permno": 101,
                "target_weight": 0.35,
                "cash_residual": 0.65,
                "row_role": "daily_portfolio",
                "source": "rule100_softmax_v1_replay",
            },
            {
                "date": "2026-01-02",
                "method": "Rule of 100",
                "ticker": "CASH",
                "permno": "CASH",
                "target_weight": 0.65,
                "cash_residual": 0.65,
                "row_role": "daily_portfolio",
                "source": "rule100_softmax_v1_replay",
            },
        ]
    )


def test_rule100_adapter_excludes_cash_rows_and_pivots_runner_weights() -> None:
    result = adapt_rule100_replay_to_target_weights(_replay_frame())

    assert result.promotion_status == DEFAULT_PROMOTION_STATUS
    assert result.strategy_role == DEFAULT_STRATEGY_ROLE
    assert result.diagnostic_only is True
    assert result.metadata["no_strategy_promotion"] is True
    assert result.metadata["engine_cash_policy"] == "implicit_residual_cash_no_cash_column"

    expected = pd.DataFrame(
        {101: [0.35, 0.0], 102: [0.0, 0.30]},
        index=pd.DatetimeIndex(["2026-01-02", "2026-01-03"], name="date"),
    )
    expected.columns.name = "permno"
    pd.testing.assert_frame_equal(result.target_weights, expected)
    assert "CASH" not in {str(col).upper() for col in result.target_weights.columns}
    assert result.metadata["excluded_cash_row_count"] == 2
    assert result.metadata["cash_residual_by_date"] == {
        "2026-01-02": 0.65,
        "2026-01-03": 0.70,
    }


def test_rule100_adapter_filters_daily_portfolio_rows_from_mixed_artifact_frame() -> None:
    mixed = pd.DataFrame(
        [
            {
                "row_type": "daily_portfolio",
                "date": "2026-01-02",
                "ticker": "AAA",
                "permno": 101,
                "target_weight": 0.25,
            },
            {
                "row_type": "buy_sell_decision",
                "date": "2026-01-02",
                "ticker": "AAA",
                "permno": 101,
                "target_weight": 0.99,
            },
            {
                "row_type": "event_annotation",
                "date": "2026-01-02",
                "ticker": "BBB",
                "permno": 102,
                "target_weight": 0.99,
            },
            {
                "row_type": "daily_portfolio",
                "date": "2026-01-02",
                "ticker": "CASH",
                "permno": "CASH",
                "target_weight": 0.75,
            },
        ]
    )

    weights = rule100_replay_to_target_weights(mixed)

    assert list(weights.columns) == [101]
    assert float(weights.loc[pd.Timestamp("2026-01-02"), 101]) == pytest.approx(0.25)


def test_rule100_adapter_preserves_bundle_and_selected_result_identity_metadata() -> None:
    bundle = SimpleNamespace(
        replay=_replay_frame(),
        run_metadata=SimpleNamespace(
            run_id="run-123",
            source_id="selected_method_replay:rule100",
            method_id="Rule of 100",
            input_signatures=({"name": "fixture"},),
            date_window={"requested_start": "2026-01-02", "requested_end": "2026-01-03"},
            row_counts={"daily_portfolio": 4},
            status_counts={"daily_portfolio": {"ok": 4}},
            timing={"elapsed_ms": 7.5},
            controls_signature={"max_weight": 0.35},
            input_coverage_start="2025-01-06",
            effective_start="2026-01-02",
            coverage_warnings=("fixture warning",),
        ),
    )
    selected_result = SimpleNamespace(
        status="ok",
        reason="cache_hit",
        available=True,
        bundle=bundle,
        artifact_path=Path("data/runtime_cache/strategy_replay/rule100.parquet"),
        manifest_path=Path("data/runtime_cache/strategy_replay/rule100.manifest.json"),
        manifest={
            "run_id": "run-123",
            "source_id": "selected_method_replay:rule100",
            "method_id": "Rule of 100",
            "artifact_type": "selected_method_replay_output",
        },
    )

    result = adapt_rule100_replay_to_target_weights(selected_result)

    assert result.metadata["run_id"] == "run-123"
    assert result.metadata["source_id"] == "selected_method_replay:rule100"
    assert result.metadata["method_id"] == "Rule of 100"
    assert result.metadata["input_signatures"] == [{"name": "fixture"}]
    assert result.metadata["date_window"] == {"requested_start": "2026-01-02", "requested_end": "2026-01-03"}
    assert result.metadata["selected_result_status"] == "ok"
    assert result.metadata["selected_result_reason"] == "cache_hit"
    assert result.metadata["manifest_run_id"] == "run-123"
    assert result.metadata["artifact_path"].endswith("rule100.parquet")
    assert result.metadata["promotion_status"] == "diagnostic_only"


def test_rule100_adapter_preserves_raw_artifact_identity_columns() -> None:
    replay = _replay_frame().assign(
        run_id="run-raw",
        source_id="source-raw",
        method_id="Rule of 100",
        artifact_scope="selected_method_replay_output",
    )

    result = adapt_rule100_replay_to_target_weights(replay)

    assert result.metadata["run_id"] == "run-raw"
    assert result.metadata["source_id"] == "source-raw"
    assert result.metadata["method_id"] == "Rule of 100"
    assert result.metadata["artifact_scope"] == "selected_method_replay_output"


def test_rule100_adapter_cash_only_replay_keeps_residual_cash_implicit() -> None:
    replay = pd.DataFrame(
        [
            {
                "date": "2026-01-02",
                "ticker": "CASH",
                "permno": "CASH",
                "target_weight": 1.0,
                "cash_residual": 1.0,
                "row_role": "daily_portfolio",
            }
        ]
    )

    result = adapt_rule100_replay_to_target_weights(replay)

    assert result.target_weights.empty
    assert list(result.target_weights.index) == [pd.Timestamp("2026-01-02")]
    assert result.metadata["excluded_cash_row_count"] == 1
    assert result.metadata["cash_residual_by_date"] == {"2026-01-02": 1.0}


def test_rule100_adapter_collapses_exact_duplicate_targets_with_metadata_reason() -> None:
    replay = pd.concat(
        [
            _replay_frame(),
            pd.DataFrame(
                [
                    {
                        "date": "2026-01-02",
                        "ticker": "AAA",
                        "permno": 101,
                        "target_weight": 0.35,
                        "cash_residual": 0.65,
                        "row_role": "daily_portfolio",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    result = adapt_rule100_replay_to_target_weights(replay)

    assert result.metadata["duplicate_handling"] == ["exact_duplicate_date_asset_rows_collapsed_last_value"]
    assert float(result.target_weights.loc[pd.Timestamp("2026-01-02"), 101]) == pytest.approx(0.35)


def test_rule100_adapter_rejects_conflicting_duplicate_targets() -> None:
    replay = pd.concat(
        [
            _replay_frame(),
            pd.DataFrame(
                [
                    {
                        "date": "2026-01-02",
                        "ticker": "AAA",
                        "permno": 101,
                        "target_weight": 0.15,
                        "cash_residual": 0.85,
                        "row_role": "daily_portfolio",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="conflicting duplicate date/asset"):
        adapt_rule100_replay_to_target_weights(replay)


def test_rule100_adapter_rejects_replay_equity_as_authoritative() -> None:
    replay = _replay_frame()
    replay["portfolio_equity"] = [10_000.0, 999_999.0, 1.0, 2.0]
    replay["portfolio_return"] = [0.50, 0.50, -0.50, -0.50]

    with_equity = adapt_rule100_replay_to_target_weights(replay)
    without_equity = adapt_rule100_replay_to_target_weights(replay.drop(columns=["portfolio_equity", "portfolio_return"]))

    pd.testing.assert_frame_equal(with_equity.target_weights, without_equity.target_weights)
    assert set(with_equity.metadata["ignored_replay_performance_columns"]) == {
        "portfolio_equity",
        "portfolio_return",
    }
    assert "portfolio_equity" not in with_equity.target_weights.columns
