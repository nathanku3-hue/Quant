from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from research.backtest_runner import run_research_backtest, validate_target_weights
from research.status import ResearchStatus
from research.strategy_cartridge import StrategyCartridge


def _target_weights() -> pd.DataFrame:
    return pd.DataFrame(
        {"101": [0.5, 0.5, 0.0, 0.4], "202": [0.0, 0.2, 0.2, 0.1]},
        index=pd.date_range("2026-01-02", periods=4, freq="B"),
    )


def _returns() -> pd.DataFrame:
    return pd.DataFrame(
        {"101": [0.00, 0.02, -0.01, 0.03], "202": [0.00, -0.01, 0.01, 0.02]},
        index=pd.date_range("2026-01-02", periods=4, freq="B"),
    )


def _economic_cash() -> pd.Series:
    return pd.Series([0.0, 0.0001, 0.0001, 0.0001], index=_returns().index, name="economic_cash")


def _benchmark_policy(*, reverse: bool = False) -> dict[str, object]:
    items = [
        ("cash", {"kind": "implicit_zero_return_cash"}),
        ("pit_equal_weight_eligible_universe", {"kind": "pit_equal_weight_match_strategy_schedule"}),
        ("economic_cash", {"kind": "economic_cash_total_return"}),
    ]
    if reverse:
        items.reverse()
    return {
        "primary": "pit_equal_weight_eligible_universe",
        "required": dict(items),
    }


def _cartridge(tmp_path: Path, **overrides) -> StrategyCartridge:
    fields = {
        "strategy_id": "fixture_strategy",
        "strategy_version": "0.2.0",
        "strategy_role": "signal_strategy",
        "universe_mode": "r3000_pit",
        "input_loader_name": "fixture_pit_loader",
        "rebalance_schedule": "on_target_change",
        "execution_lag": "one_bar",
        "turnover_cost_rate": 0.001,
        "benchmark_policy": _benchmark_policy(),
        "start_date": "2026-01-02",
        "end_date": "2026-01-07",
        "output_dir": tmp_path,
        "min_required_trading_days": 252,
    }
    fields.update(overrides)
    return StrategyCartridge(**fields)


def _pit_members(_as_of: pd.Timestamp) -> tuple[str, ...]:
    return ("101", "202")


def _valid_run(tmp_path: Path, **kwargs):
    return run_research_backtest(
        cartridge=_cartridge(tmp_path, **kwargs.pop("cartridge_overrides", {})),
        target_weights=kwargs.pop("target_weights", _target_weights()),
        returns_df=kwargs.pop("returns_df", _returns()),
        economic_cash_returns=kwargs.pop("economic_cash_returns", _economic_cash()),
        input_signatures={"returns": "fixture-signature"},
        pit_membership_proof={"proof_type": "fixture_pit_membership", "dates": 4},
        leakage_checks={"pit_inputs_only": True, "no_dashboard_labels": True},
        pit_eligibility_provider=_pit_members,
        run_id=kwargs.pop("run_id", "fixture_run"),
        **kwargs,
    )


def test_runner_calls_canonical_engine_strictly_for_strategy_and_three_benchmarks(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_simulation(target_weights, returns_df, cost_bps=0.001, strict_missing_returns=False):
        calls.append({
            "columns": tuple(target_weights.columns),
            "cost_bps": cost_bps,
            "strict_missing_returns": strict_missing_returns,
        })
        return pd.DataFrame(
            {"gross_ret": [0.0] * len(target_weights), "net_ret": [0.0] * len(target_weights), "turnover": [0.0] * len(target_weights), "cost": [0.0] * len(target_weights)},
            index=target_weights.index,
        )

    monkeypatch.setattr("research.backtest_runner.engine.run_simulation", fake_run_simulation)
    result = _valid_run(tmp_path, emit_artifacts=False)
    assert result.status == ResearchStatus.EXPLORATORY
    assert len(calls) == 4
    assert all(call["strict_missing_returns"] is True for call in calls)
    assert all(call["cost_bps"] == 0.001 for call in calls)
    assert any(call["columns"] == ("ECONOMIC_CASH",) for call in calls)


@pytest.mark.parametrize("bad_cost", [None, float("nan"), float("inf"), -0.001])
def test_non_finite_or_invalid_cost_policy_blocks(tmp_path: Path, bad_cost: float | None) -> None:
    result = _valid_run(tmp_path, cartridge_overrides={"turnover_cost_rate": bad_cost}, emit_artifacts=False)
    assert result.status == ResearchStatus.BLOCKED
    assert any(name in result.gate_results["failures"] for name in ("missing_cost_policy", "invalid_cost_policy"))


def test_old_unnamed_benchmark_list_is_invalid(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={"benchmark_policy": {"required": ["cash"]}},
        emit_artifacts=False,
    )
    assert result.status == ResearchStatus.BLOCKED
    assert "benchmark_policy_field_set_invalid" in result.gate_results["failures"]


def test_economic_cash_is_mandatory(tmp_path: Path) -> None:
    result = _valid_run(tmp_path, economic_cash_returns=None, emit_artifacts=False)
    assert result.status == ResearchStatus.BLOCKED
    assert "missing_economic_cash_returns" in result.gate_results["failures"]


def test_primary_benchmark_metrics_are_independent_of_mapping_order(tmp_path: Path) -> None:
    first = _valid_run(
        tmp_path,
        cartridge_overrides={"benchmark_policy": _benchmark_policy(reverse=False)},
        run_id="order_a",
        emit_artifacts=False,
    )
    second = _valid_run(
        tmp_path,
        cartridge_overrides={"benchmark_policy": _benchmark_policy(reverse=True)},
        run_id="order_b",
        emit_artifacts=False,
    )
    assert first.metrics["benchmark_excess_return"] == second.metrics["benchmark_excess_return"]
    assert first.evidence_packet["run_metadata"]["primary_benchmark"] == "pit_equal_weight_eligible_universe"


def test_content_signature_changes_when_one_cell_changes(tmp_path: Path) -> None:
    first = _valid_run(tmp_path, run_id="sig_a", emit_artifacts=False)
    mutated = _target_weights()
    mutated.iloc[1, 0] = 0.49
    second = _valid_run(tmp_path, target_weights=mutated, run_id="sig_b", emit_artifacts=False)
    sig_a = first.evidence_packet["run_metadata"]["target_weight_signature"]["sha256"]
    sig_b = second.evidence_packet["run_metadata"]["target_weight_signature"]["sha256"]
    assert sig_a != sig_b


def test_runner_blocks_cash_column_and_missing_executed_returns(tmp_path: Path) -> None:
    weights = _target_weights().copy()
    weights["CASH"] = 0.1
    blocked = _valid_run(tmp_path, target_weights=weights, emit_artifacts=False)
    assert "cash_column_forbidden_v0" in blocked.gate_results["failures"]

    returns = _returns()
    returns.loc[returns.index[1], "101"] = pd.NA
    blocked_returns = _valid_run(tmp_path, returns_df=returns, emit_artifacts=False)
    assert "missing_executed_returns" in blocked_returns.gate_results["failures"]


def test_runner_can_emit_research_valid_only_with_full_contract(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={"min_required_trading_days": 4},
        emit_artifacts=False,
    )
    assert result.status == ResearchStatus.RESEARCH_VALID
    assert set(result.benchmark_metrics) == {
        "cash",
        "pit_equal_weight_eligible_universe",
        "economic_cash",
    }


def test_diagnostic_lifecycle_policy_cannot_emit_research_valid(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={"strategy_role": "diagnostic_lifecycle_policy", "min_required_trading_days": 4},
        emit_artifacts=False,
    )
    assert result.status == ResearchStatus.DIAGNOSTIC_ONLY


@pytest.mark.parametrize(
    ("mutate", "expected_failure"),
    [
        (lambda frame: frame.sort_index(ascending=False), "target_weight_index_not_sorted"),
        (lambda frame: pd.concat([frame, frame.iloc[[0]]]), "target_weight_index_not_unique"),
        (lambda frame: frame.assign(**{"101": [1.1, 0.5, 0.0, 0.4]}), "target_weight_row_sum_gt_one"),
        (lambda frame: frame.assign(**{"101": [-0.1, 0.5, 0.0, 0.4]}), "target_weights_negative_long_only"),
    ],
)
def test_validate_target_weights_blocks_invalid_shapes(mutate, expected_failure) -> None:
    assert expected_failure in validate_target_weights(mutate(_target_weights()))
