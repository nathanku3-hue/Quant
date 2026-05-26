from __future__ import annotations

import json
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


def _cartridge(tmp_path: Path, **overrides) -> StrategyCartridge:
    fields = {
        "strategy_id": "fixture_strategy",
        "strategy_version": "0.1.0",
        "strategy_role": "signal_strategy",
        "universe_mode": "r3000_pit",
        "input_loader_name": "fixture_pit_loader",
        "rebalance_schedule": "daily",
        "execution_lag": "one_bar",
        "turnover_cost_rate": 0.001,
        "benchmark_policy": {"required": ["cash", "pit_equal_weight_eligible_universe"]},
        "start_date": "2026-01-02",
        "end_date": "2026-01-07",
        "output_dir": tmp_path,
        "min_required_trading_days": 252,
    }
    fields.update(overrides)
    return StrategyCartridge(**fields)


def _pit_members(as_of: pd.Timestamp) -> tuple[str, ...]:
    return ("101", "202")


def _valid_run(tmp_path: Path, **kwargs):
    return run_research_backtest(
        cartridge=_cartridge(tmp_path, **kwargs.pop("cartridge_overrides", {})),
        target_weights=kwargs.pop("target_weights", _target_weights()),
        returns_df=kwargs.pop("returns_df", _returns()),
        input_signatures={"returns": "fixture-signature"},
        pit_membership_proof={"proof_type": "fixture_pit_membership", "dates": 4},
        leakage_checks={"pit_inputs_only": True, "no_dashboard_labels": True},
        pit_eligibility_provider=_pit_members,
        run_id=kwargs.pop("run_id", "fixture_run"),
        **kwargs,
    )


def test_runner_calls_core_engine_with_strict_missing_returns_true(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_simulation(target_weights, returns_df, cost_bps=0.001, strict_missing_returns=False):
        calls.append(
            {
                "columns": tuple(target_weights.columns),
                "cost_bps": cost_bps,
                "strict_missing_returns": strict_missing_returns,
            }
        )
        return pd.DataFrame(
            {
                "gross_ret": [0.0] * len(target_weights),
                "net_ret": [0.0] * len(target_weights),
                "turnover": [0.0] * len(target_weights),
                "cost": [0.0] * len(target_weights),
            },
            index=target_weights.index,
        )

    monkeypatch.setattr("research.backtest_runner.engine.run_simulation", fake_run_simulation)

    result = _valid_run(tmp_path, emit_artifacts=False)

    assert result.status == ResearchStatus.EXPLORATORY
    assert len(calls) == 3
    assert all(call["strict_missing_returns"] is True for call in calls)
    assert all(call["cost_bps"] == 0.001 for call in calls)


def test_runner_blocks_missing_cost_policy(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={"turnover_cost_rate": None},
        emit_artifacts=False,
    )

    assert result.status == ResearchStatus.BLOCKED
    assert "missing_cost_policy" in result.gate_results["failures"]


def test_runner_blocks_missing_benchmark_policy(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={"benchmark_policy": None},
        emit_artifacts=False,
    )

    assert result.status == ResearchStatus.BLOCKED
    assert "missing_benchmark_policy" in result.gate_results["failures"]


def test_runner_blocks_cash_column_in_target_weights(tmp_path: Path) -> None:
    weights = _target_weights().copy()
    weights["CASH"] = 0.1

    result = _valid_run(tmp_path, target_weights=weights, emit_artifacts=False)

    assert result.status == ResearchStatus.BLOCKED
    assert "cash_column_forbidden_v0" in result.gate_results["failures"]


def test_runner_blocks_missing_executed_returns(tmp_path: Path) -> None:
    returns = _returns()
    returns.loc[returns.index[1], "101"] = pd.NA

    result = _valid_run(tmp_path, returns_df=returns, emit_artifacts=False)

    assert result.status == ResearchStatus.BLOCKED
    assert "missing_executed_returns" in result.gate_results["failures"]
    assert result.evidence_packet["data_quality_report"]["missing_executed_return_count"] == 1


def test_runner_requires_target_weights_to_match_returns_calendar_v0(tmp_path: Path) -> None:
    weights = _target_weights().iloc[[0, 2, 3]]

    result = _valid_run(tmp_path, target_weights=weights, emit_artifacts=False)

    assert result.status == ResearchStatus.BLOCKED
    assert "target_weights_must_match_returns_calendar_v0" in result.gate_results["failures"]


def test_runner_blocks_malformed_target_weight_dates_without_raising(tmp_path: Path) -> None:
    weights = _target_weights().copy()
    weights.index = ["not-a-date", "also-not-a-date", "still-bad", "bad-again"]

    result = _valid_run(tmp_path, target_weights=weights, emit_artifacts=False)

    assert result.status == ResearchStatus.BLOCKED
    assert "target_weight_index_not_date_like" in result.gate_results["failures"]


@pytest.mark.parametrize("unsafe_run_id", ["../escape", "nested/run", "nested\\run", "bad:name", "", "."])
def test_runner_rejects_unsafe_run_id_before_artifact_path_creation(tmp_path: Path, unsafe_run_id: str) -> None:
    with pytest.raises(ValueError, match="unsafe_run_id"):
        _valid_run(tmp_path, run_id=unsafe_run_id, emit_artifacts=False)


def test_runner_blocks_non_finite_executed_returns(tmp_path: Path) -> None:
    returns = _returns()
    returns.loc[returns.index[1], "101"] = float("inf")

    result = _valid_run(tmp_path, returns_df=returns, emit_artifacts=False)

    assert result.status == ResearchStatus.BLOCKED
    assert "returns_non_finite" in result.gate_results["failures"]
    assert "non_finite_executed_returns" in result.gate_results["failures"]


def test_placeholder_pit_proof_cannot_be_research_valid(tmp_path: Path) -> None:
    result = run_research_backtest(
        cartridge=_cartridge(tmp_path, min_required_trading_days=4),
        target_weights=_target_weights(),
        returns_df=_returns(),
        input_signatures={"returns": "fixture-signature"},
        pit_membership_proof={"proof_type": "placeholder"},
        leakage_checks={"pit_inputs_only": True, "no_dashboard_labels": True},
        pit_eligibility_provider=_pit_members,
        run_id="placeholder_pit",
        emit_artifacts=False,
    )

    assert result.status == ResearchStatus.BLOCKED
    assert "placeholder_pit_membership_proof" in result.gate_results["failures"]


def test_runner_turnover_and_cost_artifacts_match_engine_output(tmp_path: Path) -> None:
    result = _valid_run(tmp_path)

    turnover = pd.read_csv(result.artifacts["turnover.csv"], index_col="date")
    costs = pd.read_csv(result.artifacts["costs.csv"], index_col="date")

    pd.testing.assert_series_equal(
        turnover["turnover"].reset_index(drop=True),
        result.simulation_result["turnover"].reset_index(drop=True),
        check_names=False,
    )
    pd.testing.assert_series_equal(
        costs["cost"].reset_index(drop=True),
        result.simulation_result["cost"].reset_index(drop=True),
        check_names=False,
    )


def test_benchmark_missing_executed_return_blocks_instead_of_prefiltering(tmp_path: Path) -> None:
    returns = _returns()
    returns.loc[returns.index[1], "202"] = pd.NA

    result = run_research_backtest(
        cartridge=_cartridge(tmp_path),
        target_weights=pd.DataFrame(
            {"101": [0.5, 0.5, 0.5, 0.5], "202": [0.0, 0.0, 0.0, 0.0]},
            index=_returns().index,
        ),
        returns_df=returns,
        input_signatures={"returns": "fixture-signature"},
        pit_membership_proof={"proof_type": "fixture_pit_membership", "dates": 4},
        leakage_checks={"pit_inputs_only": True, "no_dashboard_labels": True},
        pit_eligibility_provider=lambda as_of: ("101", "202"),
        run_id="benchmark_missing_return",
        emit_artifacts=False,
    )

    assert result.status == ResearchStatus.BLOCKED
    assert "benchmark_pit_equal_weight_eligible_universe_missing_executed_returns" in result.gate_results["failures"]


def test_runner_emits_required_evidence_files(tmp_path: Path) -> None:
    result = _valid_run(tmp_path)

    assert result.status == ResearchStatus.EXPLORATORY
    required_files = {
        "cartridge.json",
        "run_metadata.json",
        "verdict.json",
        "gate_results.json",
        "input_signatures.json",
        "pit_membership_proof.json",
        "leakage_checks.json",
        "metrics.json",
        "benchmark_metrics.json",
        "data_quality_report.json",
        "evidence_packet.json",
        "target_weights.csv",
        "executed_weights.csv",
        "equity_curve.csv",
        "benchmark_curves.csv",
        "turnover.csv",
        "costs.csv",
        "exposure.csv",
    }
    assert required_files.issubset(result.artifacts)
    verdict = json.loads(Path(result.artifacts["verdict.json"]).read_text(encoding="utf-8"))
    metadata = json.loads(Path(result.artifacts["run_metadata.json"]).read_text(encoding="utf-8"))

    assert verdict["promotion_status"] == "exploratory"
    assert metadata["strict_missing_returns"] is True
    assert metadata["cost_policy"]["turnover_cost_rate"] == 0.001
    assert metadata["cost_policy"]["turnover_cost_bps"] == 10.0
    assert metadata["cash_policy"] == "implicit_residual_cash"
    assert "CASH" not in pd.read_csv(result.artifacts["target_weights.csv"]).columns


def test_runner_can_emit_research_valid_when_min_window_is_met(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={"min_required_trading_days": 4},
        emit_artifacts=False,
    )

    assert result.status == ResearchStatus.RESEARCH_VALID
    assert result.verdict["research_valid"] is True


def test_diagnostic_lifecycle_policy_cannot_emit_research_valid(tmp_path: Path) -> None:
    result = _valid_run(
        tmp_path,
        cartridge_overrides={
            "strategy_role": "diagnostic_lifecycle_policy",
            "min_required_trading_days": 4,
        },
        emit_artifacts=False,
    )

    assert result.status == ResearchStatus.DIAGNOSTIC_ONLY
    assert result.verdict["promotion_status"] == "diagnostic_only"
    assert result.verdict["research_valid"] is False


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
    failures = validate_target_weights(mutate(_target_weights()))

    assert expected_failure in failures
