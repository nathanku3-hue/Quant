from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "day5_ablation_report.py"


def _load_script_module():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("day5_ablation_report", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_build_ablation_configs_contract():
    mod = _load_script_module()
    configs = mod.build_ablation_configs()
    ids = [cfg.config_id for cfg in configs]
    assert len(configs) == 9
    assert ids == [
        "BASELINE_DAY4",
        "ABLATION_A1_PARTIAL",
        "ABLATION_B1_IR_WEIGHT",
        "ABLATION_C3_INTEGRATOR",
        "ABLATION_C1_SIGMOID",
        "ABLATION_C4_FULL",
        "ABLATION_AC_OPTIMAL",
        "ABLATION_B3_HIERARCHICAL",
        "ABLATION_A3_FALLBACK",
    ]


def test_build_deltas_sets_baseline_deltas_to_zero():
    mod = _load_script_module()
    metrics = pd.DataFrame(
        [
            {
                "config_id": "BASELINE_DAY4",
                "coverage": 0.80,
                "quartile_spread_sigma": 1.5,
                "adjacent_rank_correlation": 0.9,
                "factor_balance_max_share": 0.4,
                "sharpe": 0.5,
                "cagr": 0.1,
                "max_dd": -0.2,
                "ulcer": 5.0,
                "turnover_annual": 1.0,
            },
            {
                "config_id": "ALT",
                "coverage": 0.90,
                "quartile_spread_sigma": 1.8,
                "adjacent_rank_correlation": 0.92,
                "factor_balance_max_share": 0.35,
                "sharpe": 0.6,
                "cagr": 0.12,
                "max_dd": -0.18,
                "ulcer": 4.5,
                "turnover_annual": 0.7,
            },
        ]
    )
    deltas = mod._build_deltas(metrics=metrics, baseline_id="BASELINE_DAY4")
    base = deltas[deltas["config_id"] == "BASELINE_DAY4"].iloc[0]
    assert float(base["delta_coverage"]) == 0.0
    assert float(base["delta_sharpe"]) == 0.0
    assert float(base["turnover_reduction_vs_baseline"]) == 0.0


def test_build_target_weights_respects_top_quantile_cardinality():
    mod = _load_script_module()
    one_day = pd.Timestamp("2024-01-02")
    scores = pd.DataFrame(
        {
            "date": [one_day] * 10,
            "permno": list(range(100, 110)),
            "score": list(range(10)),
            "score_valid": [True] * 10,
        }
    )
    weights = mod._build_target_weights(scores=scores, top_quantile=0.10)
    assert one_day in set(weights.index)
    selected = int((weights.loc[one_day] > 0).sum())
    assert selected == 1


def test_simulate_scores_strategy_returns_metrics():
    mod = _load_script_module()
    dates = pd.to_datetime(
        ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04", "2024-01-04"]
    )
    scores = pd.DataFrame(
        {
            "date": dates,
            "permno": [101, 202, 101, 202, 101, 202],
            "score": [1.0, 0.5, 0.7, 1.2, 1.1, 0.9],
            "score_valid": [True, True, True, True, True, True],
        }
    )
    returns = pd.DataFrame(
        {
            "date": dates,
            "permno": [101, 202, 101, 202, 101, 202],
            "ret": [0.01, -0.01, 0.02, 0.00, -0.005, 0.015],
        }
    )
    sim, metrics = mod._simulate_scores_strategy(
        scores=scores,
        returns_long=returns,
        top_quantile=0.5,
        cost_bps=5.0,
        allow_missing_returns=False,
        max_matrix_cells=10_000,
    )
    assert not sim.empty
    assert len(sim) == 3
    assert np.isfinite(metrics["turnover_annual"])
    assert metrics["avg_positions"] > 0.0


def test_simulate_scores_strategy_missing_entry_bar_is_not_counted():
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

    sim, metrics = mod._simulate_scores_strategy(
        scores=scores,
        returns_long=returns,
        top_quantile=1.0,
        cost_bps=0.0,
        allow_missing_returns=False,
        max_matrix_cells=1_000,
    )
    assert len(sim) == 2
    assert np.isfinite(metrics["turnover_total"])


def test_simulate_scores_strategy_missing_exit_bar_raises_in_strict_mode():
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
        mod._simulate_scores_strategy(
            scores=scores,
            returns_long=returns,
            top_quantile=1.0,
            cost_bps=0.0,
            allow_missing_returns=False,
            max_matrix_cells=1_000,
        )
