from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "day6_walkforward_validation.py"


def _load_script_module():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("day6_walkforward_validation", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_build_c3_specs_decay_to_alpha_mapping():
    mod = _load_script_module()
    specs = mod._build_c3_specs(0.95)
    assert len(specs) == 4
    assert all(s.use_leaky_integrator for s in specs)
    assert all(not s.use_sigmoid_blend for s in specs)
    assert all(not s.use_dirty_derivative for s in specs)
    assert all(abs(float(s.leaky_alpha) - 0.05) < 1e-12 for s in specs)


def test_compute_drawdown_duration_counts_underwater_run():
    mod = _load_script_module()
    # This path never recovers previous high after the first drop.
    ret = pd.Series([0.05, -0.02, -0.01, -0.01, 0.03, 0.01])
    duration = mod._compute_drawdown_duration(ret)
    assert duration == 5


def test_days_to_new_high_finds_recovery_length():
    mod = _load_script_module()
    idx = pd.date_range("2022-10-01", periods=6, freq="B")
    ret = pd.Series([0.00, -0.02, 0.03, 0.02, 0.01, 0.01], index=idx)
    days = mod._days_to_new_high(ret, "2022-10-03")
    assert np.isfinite(days)
    assert float(days) >= 0.0


def test_evaluate_checks_emits_expected_ids():
    mod = _load_script_module()
    wf = pd.DataFrame(
        [
            {"window_id": "W1_COVID", "test_maxdd_c3": -0.1, "test_maxdd_baseline": -0.2, "test_turnover_c3": 0.2, "test_turnover_baseline": 0.3, "covid_recovery_capture": 0.95},
            {"window_id": "W2_INFLATION", "rotation_rank_stability_c3": 0.98, "rotation_rank_stability_baseline": 0.96, "rotation_turnover_c3": 0.08, "rotation_turnover_baseline": 0.10, "test_sharpe_c3": 1.2, "test_sharpe_baseline": 1.1},
            {"window_id": "W3_BEAR", "test_drawdown_duration_c3": 100, "test_drawdown_duration_baseline": 120, "bear_beta_c3": 0.8, "bear_beta_baseline": 0.9, "bear_recovery_days_c3": 30, "bear_recovery_days_baseline": 40},
            {"window_id": "W4_RECOVERY", "upside_capture_c3": 1.02, "upside_capture_baseline": 1.00, "test_turnover_c3": 0.2, "test_turnover_baseline": 0.3, "test_sharpe_c3": 1.5, "test_sharpe_baseline": 1.4},
        ]
    )
    decay = pd.DataFrame(
        {
            "decay": [0.85, 0.90, 0.95, 0.98, 0.99],
            "sharpe": [1.50, 1.55, 1.58, 1.56, 1.52],
        }
    )
    crisis = pd.DataFrame(
        {
            "window": ["A", "B", "C", "D"],
            "reduction_pct": [20.0, 18.0, 17.0, 16.0],
            "pass": [True, True, True, True],
        }
    )
    checks = mod.evaluate_checks(wf, decay, crisis)
    ids = set(checks["check_id"].tolist())
    assert "CHK-39" in ids
    assert "CHK-54" in ids
    assert len(ids) == 16


def test_simulate_from_scores_missing_entry_bar_is_not_counted():
    mod = _load_script_module()
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    scores = pd.DataFrame(
        {
            "date": [d1, d2],
            "permno": [101, 101],
            "score": [1.0, 1.0],
            "score_valid": [True, True],
        }
    )
    returns = pd.DataFrame(
        {
            "date": [d2],
            "permno": [101],
            "ret": [0.01],
        }
    )

    sim, missing = mod._simulate_from_scores(
        scores=scores,
        returns_long=returns,
        top_quantile=1.0,
        cost_bps=0.0,
        allow_missing_returns=False,
        max_matrix_cells=1_000,
    )
    assert len(sim) == 2
    assert int(missing) == 0


def test_simulate_from_scores_missing_exit_bar_raises_in_strict_mode():
    mod = _load_script_module()
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    scores = pd.DataFrame(
        {
            "date": [d1, d2],
            "permno": [101, 101],
            "score": [1.0, 1.0],
            "score_valid": [True, False],
        }
    )
    returns = pd.DataFrame(
        {
            "date": [d1],
            "permno": [101],
            "ret": [0.01],
        }
    )

    with pytest.raises(RuntimeError, match="executed exposures"):
        mod._simulate_from_scores(
            scores=scores,
            returns_long=returns,
            top_quantile=1.0,
            cost_bps=0.0,
            allow_missing_returns=False,
            max_matrix_cells=1_000,
        )
