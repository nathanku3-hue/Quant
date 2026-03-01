from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
OPTIMIZER_PATH = ROOT / "backtests" / "optimize_phase16_parameters.py"


def _load_optimizer():
    assert OPTIMIZER_PATH.exists(), f"Missing optimizer script: {OPTIMIZER_PATH}"
    spec = importlib.util.spec_from_file_location("optimize_phase16_parameters", OPTIMIZER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parameter_grid_enforces_hysteresis_constraint():
    mod = _load_optimizer()
    grid = mod.build_parameter_grid(
        alpha_top_n_values=[5, 10, 15],
        hysteresis_exit_values=[12, 20],
        adaptive_rsi_values=[0.05],
        atr_presets=[2.0],
        entry_logic_values=["dip", "breakout", "combined"],
    )
    assert grid
    assert {str(row["entry_logic"]) for row in grid} == {"dip", "breakout", "combined"}
    assert all(int(row["hysteresis_exit_rank"]) >= int(row["alpha_top_n"]) for row in grid)
    assert any(int(row["alpha_top_n"]) == 5 and int(row["hysteresis_exit_rank"]) == 12 for row in grid)
    assert not any(int(row["alpha_top_n"]) == 15 and int(row["hysteresis_exit_rank"]) == 12 for row in grid)


def test_parameter_grid_rejects_invalid_entry_logic():
    mod = _load_optimizer()
    with pytest.raises(ValueError):
        mod.build_parameter_grid(
            alpha_top_n_values=[10],
            hysteresis_exit_values=[20],
            adaptive_rsi_values=[0.05],
            atr_presets=[2.0],
            entry_logic_values=["dip", "bad_logic"],
        )


def test_resolve_worker_count_contract():
    mod = _load_optimizer()
    assert mod.resolve_worker_count(max_workers=0, total_tasks=1) == 1
    assert mod.resolve_worker_count(max_workers=1, total_tasks=10) == 1
    assert mod.resolve_worker_count(max_workers=999, total_tasks=4) == 4
    assert mod.resolve_worker_count(max_workers=-1, total_tasks=3) >= 1


def test_should_use_parallel_contract():
    mod = _load_optimizer()
    assert mod.should_use_parallel(disable_parallel=True, worker_count=8, total_tasks=10) is False
    assert mod.should_use_parallel(disable_parallel=False, worker_count=1, total_tasks=10) is False
    assert mod.should_use_parallel(disable_parallel=False, worker_count=8, total_tasks=1) is False
    assert mod.should_use_parallel(disable_parallel=False, worker_count=4, total_tasks=10) is True


def test_coerce_bool_handles_strings_and_nan():
    mod = _load_optimizer()
    assert mod.coerce_bool(True) is True
    assert mod.coerce_bool(False) is False
    assert mod.coerce_bool("true") is True
    assert mod.coerce_bool("False") is False
    assert mod.coerce_bool("0") is False
    assert mod.coerce_bool("1") is True
    assert mod.coerce_bool(float("nan")) is False


def test_compute_activity_metrics_from_weights():
    mod = _load_optimizer()
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    weights = pd.DataFrame(
        {
            10001: [0.0, 0.50, 0.50, 0.0, 0.0, 0.30, 0.30, 0.30, 0.0, 0.0],
        },
        index=idx,
    )
    metrics = mod.compute_activity_metrics(weights)
    assert metrics["exposure_time"] == pytest.approx(0.50)
    assert metrics["trades_per_year"] == pytest.approx(100.8)


def test_compute_window_activity_metrics_uses_only_requested_window():
    mod = _load_optimizer()
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    weights = pd.DataFrame(
        {
            10001: [0.0, 0.50, 0.50, 0.0, 0.0, 0.30, 0.30, 0.30, 0.0, 0.0],
        },
        index=idx,
    )
    metrics = mod.compute_window_activity_metrics(
        weights=weights,
        start=idx[5],
        end=idx[9],
    )
    # Window has 5 rows with exposure on 3 rows.
    assert metrics["exposure_time"] == pytest.approx(0.60)
    # Two turnover changes over a 5-row (~0.01984y) window.
    assert metrics["trades_per_year"] == pytest.approx(100.8)


def test_activity_guards_require_strictly_greater_than_thresholds():
    mod = _load_optimizer()
    assert (
        mod.evaluate_activity_guards(
            exposure_time=0.30,
            trades_per_year=10.0,
            min_exposure_time=0.30,
            min_trades_per_year=10.0,
        )
        is False
    )
    assert (
        mod.evaluate_activity_guards(
            exposure_time=0.31,
            trades_per_year=10.1,
            min_exposure_time=0.30,
            min_trades_per_year=10.0,
        )
        is True
    )


def test_is_candidate_promotable_requires_stability_and_activity():
    mod = _load_optimizer()
    assert mod.is_candidate_promotable({"stability_pass": True, "activity_guard_pass": True}) is True
    assert mod.is_candidate_promotable({"stability_pass": True, "activity_guard_pass": False}) is False
    assert mod.is_candidate_promotable({"stability_pass": False, "activity_guard_pass": True}) is False


def test_select_best_candidate_falls_back_to_train_only_when_no_promotable():
    mod = _load_optimizer()
    candidates = pd.DataFrame(
        [
            {
                "alpha_top_n": 5,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.05,
                "atr_preset": 2.0,
                "objective_score": 2.10,
                "train_cagr": 0.20,
                "train_robust_score": 2.10,
                "train_ulcer": 3.0,
                "test_robust_score": 0.10,
                "sharpe_degradation": 1.80,
                "stability_pass": False,
                "activity_guard_pass": False,
            },
            {
                "alpha_top_n": 10,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.10,
                "atr_preset": 3.0,
                "objective_score": 1.45,
                "train_cagr": 0.15,
                "train_robust_score": 1.45,
                "train_ulcer": 4.0,
                "test_robust_score": 1.10,
                "sharpe_degradation": 0.20,
                "stability_pass": True,
                "activity_guard_pass": False,
            },
            {
                "alpha_top_n": 15,
                "hysteresis_exit_rank": 30,
                "adaptive_rsi_percentile": 0.15,
                "atr_preset": 4.0,
                "objective_score": 1.30,
                "train_cagr": 0.10,
                "train_robust_score": 1.30,
                "train_ulcer": 5.0,
                "test_robust_score": 1.00,
                "sharpe_degradation": 0.10,
                "stability_pass": True,
                "activity_guard_pass": False,
            },
        ]
    )

    best, used_promotable_pool = mod.select_best_candidate(candidates)
    assert best is not None
    assert used_promotable_pool is False
    assert int(best["alpha_top_n"]) == 5
    assert bool(best["stability_pass"]) is False


def test_select_best_candidate_returns_none_when_no_valid_candidates():
    mod = _load_optimizer()
    candidates = pd.DataFrame(
        [
            {
                "alpha_top_n": 5,
                "hysteresis_exit_rank": 12,
                "adaptive_rsi_percentile": 0.05,
                "atr_preset": 2.0,
                "objective_score": 1.2,
                "train_cagr": float("nan"),
                "train_robust_score": 1.2,
                "train_ulcer": 3.5,
                "stability_pass": False,
                "activity_guard_pass": False,
                "error": "runtime-failure",
            },
            {
                "alpha_top_n": 10,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.10,
                "atr_preset": 3.0,
                "objective_score": float("nan"),
                "train_cagr": 0.10,
                "train_robust_score": float("nan"),
                "train_ulcer": 4.0,
                "stability_pass": False,
                "activity_guard_pass": False,
                "error": "",
            },
        ]
    )
    best, used_promotable_pool = mod.select_best_candidate(candidates)
    assert best is None
    assert used_promotable_pool is False


def test_select_best_candidate_prefers_promotable_pool_over_higher_train_non_promotable():
    mod = _load_optimizer()
    candidates = pd.DataFrame(
        [
            {
                "alpha_top_n": 5,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.10,
                "atr_preset": 3.0,
                "objective_score": 2.00,
                "train_cagr": 0.22,
                "train_robust_score": 2.00,
                "train_ulcer": 3.0,
                "stability_pass": True,
                "activity_guard_pass": False,
                "error": "",
            },
            {
                "alpha_top_n": 10,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.10,
                "atr_preset": 3.0,
                "objective_score": 1.60,
                "train_cagr": 0.18,
                "train_robust_score": 1.60,
                "train_ulcer": 4.0,
                "stability_pass": True,
                "activity_guard_pass": True,
                "error": "",
            },
        ]
    )

    best, used_promotable_pool = mod.select_best_candidate(candidates)
    assert best is not None
    assert used_promotable_pool is True
    assert int(best["alpha_top_n"]) == 10
    assert bool(best["activity_guard_pass"]) is True


def test_select_best_candidate_ignores_oos_tiebreak_and_invalid_rows():
    mod = _load_optimizer()
    candidates = pd.DataFrame(
        [
            {
                "alpha_top_n": 5,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.10,
                "atr_preset": 3.0,
                "objective_score": 1.50,
                "train_cagr": 0.12,
                "train_robust_score": 1.50,
                "train_ulcer": 4.5,
                "test_robust_score": 0.10,
                "sharpe_degradation": 0.80,
                "stability_pass": True,
                "activity_guard_pass": True,
                "error": "",
            },
            {
                "alpha_top_n": 10,
                "hysteresis_exit_rank": 20,
                "adaptive_rsi_percentile": 0.10,
                "atr_preset": 3.0,
                "objective_score": 1.50,
                "train_cagr": 0.12,
                "train_robust_score": 1.50,
                "train_ulcer": 4.5,
                "test_robust_score": 1.90,
                "sharpe_degradation": 0.10,
                "stability_pass": True,
                "activity_guard_pass": True,
                "error": "",
            },
            {
                # Should be ignored due to runtime error marker.
                "alpha_top_n": 3,
                "hysteresis_exit_rank": 12,
                "adaptive_rsi_percentile": 0.05,
                "atr_preset": 2.0,
                "objective_score": 9.99,
                "train_cagr": 0.40,
                "train_robust_score": 9.99,
                "train_ulcer": 2.0,
                "stability_pass": True,
                "activity_guard_pass": True,
                "error": "runtime-failure",
            },
        ]
    )
    best, used_promotable_pool = mod.select_best_candidate(candidates)
    assert used_promotable_pool is True
    assert best is not None
    assert int(best["alpha_top_n"]) == 5


def test_summary_contains_required_fields():
    mod = _load_optimizer()
    args = SimpleNamespace(
        train_start="2015-01-01",
        train_end="2021-12-31",
        test_start="2022-01-01",
        test_end="2024-12-31",
        strict=False,
        max_sharpe_degradation=0.75,
        min_test_sharpe=0.0,
        min_trades_per_year=10.0,
        min_exposure_time=0.30,
    )
    best_row = pd.Series(
        {
            "alpha_top_n": 10,
            "hysteresis_exit_rank": 20,
            "adaptive_rsi_percentile": 0.10,
            "atr_preset": 3.0,
            "atr_mult_low_vol": 3.0,
            "atr_mult_mid_vol": 4.0,
            "atr_mult_high_vol": 5.0,
            "train_cagr": 0.12,
            "train_sharpe": 1.25,
            "train_max_dd": -0.14,
            "train_ulcer": 4.8,
            "test_cagr": 0.09,
            "test_sharpe": 0.95,
            "test_max_dd": -0.16,
            "test_ulcer": 5.2,
            "train_robust_score": 0.85,
            "test_robust_score": 0.66,
            "sharpe_degradation": 0.30,
            "stability_pass": True,
            "exposure_time": 0.45,
            "trades_per_year": 12.0,
            "activity_guard_pass": True,
            "objective_score": 0.85,
        }
    )

    summary = mod.build_oos_summary(
        best_row=best_row,
        args=args,
        total_candidates=72,
        stable_candidates=40,
        activity_guard_candidates=38,
        promotable_candidates=34,
        selection_pool="promotable_train_ranked",
    )
    assert set(mod.REQUIRED_SUMMARY_FIELDS).issubset(set(summary.keys()))
    assert summary["min_trades_per_year_guard"] == pytest.approx(10.0)
    assert summary["min_exposure_time_guard"] == pytest.approx(0.30)
    assert summary["exposure_time"] == pytest.approx(0.45)
    assert summary["trades_per_year"] == pytest.approx(12.0)


def test_best_params_payload_contains_guard_thresholds_and_activity():
    mod = _load_optimizer()
    args = SimpleNamespace(
        strict=True,
        max_sharpe_degradation=0.75,
        min_test_sharpe=0.0,
        min_trades_per_year=10.0,
        min_exposure_time=0.30,
    )
    promoted_row = pd.Series(
        {
            "alpha_top_n": 10,
            "hysteresis_exit_rank": 20,
            "adaptive_rsi_percentile": 0.10,
            "atr_preset": 3.0,
            "stability_pass": True,
            "activity_guard_pass": True,
            "exposure_time": 0.44,
            "trades_per_year": 11.5,
        }
    )
    payload = mod.build_best_params_payload(
        args=args,
        train_start=pd.Timestamp("2015-01-01"),
        train_end=pd.Timestamp("2021-12-31"),
        test_start=pd.Timestamp("2022-01-01"),
        test_end=pd.Timestamp("2024-12-31"),
        total_candidates=72,
        stable_candidates=40,
        activity_guard_candidates=38,
        promotable_candidates=34,
        selection_pool="train_only_rejected_guardrails",
        promoted_row=promoted_row,
        train_best_row=promoted_row,
    )
    assert payload["min_trades_per_year_guard"] == pytest.approx(10.0)
    assert payload["min_exposure_time_guard"] == pytest.approx(0.30)
    assert payload["selected_activity"]["exposure_time"] == pytest.approx(0.44)
    assert payload["selected_activity"]["trades_per_year"] == pytest.approx(11.5)


def test_commit_artifact_bundle_rolls_back_on_partial_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    mod = _load_optimizer()
    target_a = tmp_path / "a.csv"
    target_b = tmp_path / "b.csv"
    stage_a = tmp_path / "a.csv.stage"
    stage_b = tmp_path / "b.csv.stage"
    target_a.write_text("old-a", encoding="utf-8")
    target_b.write_text("old-b", encoding="utf-8")
    stage_a.write_text("new-a", encoding="utf-8")
    stage_b.write_text("new-b", encoding="utf-8")

    real_replace = mod.os.replace

    def flaky_replace(src, dst):
        src_p = Path(src)
        dst_p = Path(dst)
        if src_p == stage_b and dst_p == target_b:
            raise OSError("inject commit failure on second promote")
        return real_replace(src, dst)

    monkeypatch.setattr(mod.os, "replace", flaky_replace)

    with pytest.raises(Exception):
        mod._commit_artifact_bundle(
            stage_to_target=[(stage_a, target_a), (stage_b, target_b)],
            run_tag="testrun",
        )

    assert target_a.read_text(encoding="utf-8") == "old-a"
    assert target_b.read_text(encoding="utf-8") == "old-b"
