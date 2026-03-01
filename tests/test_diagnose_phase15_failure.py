from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "backtests" / "diagnose_phase15_failure.py"


def _load_script():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("diagnose_phase15_failure", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_yearly_summary_contract_and_values():
    mod = _load_script()
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2025-01-02", "2025-01-03"])
    phase15_ret = pd.Series([0.01, -0.005, 0.02, 0.01], index=dates)
    phase15_curve = (1.0 + phase15_ret).cumprod()

    df = pd.DataFrame(
        {
            "date": dates,
            "phase15_ret": phase15_ret.values,
            "phase15_curve": phase15_curve.values,
            "num_positions": [0, 2, 1, 1],
            "entry_trigger": [0, 1, 1, 0],
            "turnover": [0.0, 0.5, 0.2, 0.3],
        }
    )

    yearly = mod.build_yearly_summary(df)
    assert list(yearly["year"].astype(int)) == [2024, 2025]
    assert list(yearly["rows"].astype(int)) == [2, 2]
    assert list(yearly["entry_count"].astype(int)) == [1, 1]
    np.testing.assert_allclose(yearly["mean_positions"].values, [1.0, 1.0], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(yearly["turnover_sum"].values, [0.5, 0.5], rtol=1e-12, atol=1e-12)

    expected_2024_cagr = mod.compute_cagr(df.loc[df["date"].dt.year == 2024, "phase15_curve"])
    expected_2025_cagr = mod.compute_cagr(df.loc[df["date"].dt.year == 2025, "phase15_curve"])
    np.testing.assert_allclose(
        yearly["cagr"].values,
        [expected_2024_cagr, expected_2025_cagr],
        rtol=1e-12,
        atol=1e-12,
    )


def test_coerce_bool_handles_stability_inputs():
    mod = _load_script()
    assert mod.coerce_bool(True) is True
    assert mod.coerce_bool(False) is False
    assert mod.coerce_bool("true") is True
    assert mod.coerce_bool("False") is False
    assert mod.coerce_bool("1") is True
    assert mod.coerce_bool("0") is False
    assert mod.coerce_bool("on") is True
    assert mod.coerce_bool("off") is False
    assert mod.coerce_bool(float("nan")) is False


def test_summarize_frontier_uses_stability_coercion():
    mod = _load_script()
    optimizer = pd.DataFrame(
        [
            {"candidate_id": 1, "stability_pass": "true", "test_cagr": 0.11, "train_robust_score": 1.2},
            {"candidate_id": 2, "stability_pass": "False", "test_cagr": 0.40, "train_robust_score": 0.8},
            {"candidate_id": 3, "stability_pass": "1", "test_cagr": 0.09, "train_robust_score": 1.6},
            {"candidate_id": 4, "stability_pass": "on", "test_cagr": 0.25, "train_robust_score": 1.1},
            {"candidate_id": 5, "stability_pass": np.nan, "test_cagr": 0.30, "train_robust_score": 0.9},
        ]
    )

    stats, top_test, top_robust = mod.summarize_frontier(optimizer)
    assert stats["optimizer_rows"] == 5
    assert stats["stable_candidates"] == 3
    assert stats["stable_candidates_test_cagr_gt_10"] == 2
    assert len(top_test) == 5
    assert len(top_robust) == 5
