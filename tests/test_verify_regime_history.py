from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = ROOT / "backtests" / "verify_regime_history.py"


def _load_verifier():
    assert VERIFIER_PATH.exists(), f"Missing verifier script: {VERIFIER_PATH}"
    spec = importlib.util.spec_from_file_location("verify_regime_history", VERIFIER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_synthetic_history(mod) -> pd.DataFrame:
    def make_rows(start: str, end: str, states: list[str]) -> pd.DataFrame:
        idx = pd.date_range(start, end, freq="B")
        n = len(idx)
        assert n == len(states)
        return pd.DataFrame(
            {
                "governor_state": states,
                "market_state": ["NEUT"] * n,
                "target_exposure": np.ones(n, dtype=float),
                "matrix_exposure": np.ones(n, dtype=float),
                "throttle_score": np.zeros(n, dtype=float),
                "bocpd_prob": np.zeros(n, dtype=float),
                "reason": ["synthetic"] * n,
                "spy_close": np.linspace(100.0, 110.0, n),
                "equity_curve": np.linspace(1.0, 1.1, n),
                "buyhold_curve": np.linspace(1.0, 1.1, n),
            },
            index=idx,
        )

    h_2008_idx = pd.date_range("2008-10-01", "2008-12-31", freq="B")
    h_2008 = make_rows("2008-10-01", "2008-12-31", ["RED"] * int(len(h_2008_idx) * 0.9) + ["AMBER"] * (len(h_2008_idx) - int(len(h_2008_idx) * 0.9)))

    h_2020_idx = pd.date_range("2020-03-01", "2020-03-31", freq="B")
    h_2020 = make_rows("2020-03-01", "2020-03-31", ["RED"] * int(len(h_2020_idx) * 0.9) + ["AMBER"] * (len(h_2020_idx) - int(len(h_2020_idx) * 0.9)))

    h_2022_idx = pd.date_range("2022-01-01", "2022-06-30", freq="B")
    n_2022 = len(h_2022_idx)
    s_2022 = ["RED"] * 30 + ["AMBER"] * 80 + ["GREEN"] * (n_2022 - 110)
    h_2022 = make_rows("2022-01-01", "2022-06-30", s_2022)

    h_2017_idx = pd.date_range("2017-01-01", "2017-12-31", freq="B")
    n_2017 = len(h_2017_idx)
    s_2017 = ["GREEN"] * int(n_2017 * 0.85) + ["AMBER"] * (n_2017 - int(n_2017 * 0.85))
    h_2017 = make_rows("2017-01-01", "2017-12-31", s_2017)

    h_2023_idx = pd.date_range("2023-11-01", "2023-11-30", freq="B")
    n_2023 = len(h_2023_idx)
    s_2023 = ["AMBER"] * n_2023
    for i in range(min(2, n_2023)):
        s_2023[i] = "GREEN"
    for i in range(max(0, n_2023 - 8), n_2023):
        s_2023[i] = "GREEN"
    h_2023 = make_rows("2023-11-01", "2023-11-30", s_2023)

    out = pd.concat([h_2008, h_2017, h_2020, h_2022, h_2023]).sort_index()
    return out


def test_truth_table_window_verdicts_pass_on_synthetic_data():
    mod = _load_verifier()
    history = _build_synthetic_history(mod)
    verdicts = mod.evaluate_truth_table_windows(history)

    assert isinstance(verdicts, pd.DataFrame)
    required = {"truth_window", "rows", "truth_expected", "truth_pass"}
    assert required.issubset(set(verdicts.columns))
    assert (verdicts["truth_pass"] == 1).all()


def test_metric_helpers_match_expected_values():
    mod = _load_verifier()
    idx = pd.date_range("2025-01-01", periods=7, freq="B")
    equity = pd.Series([100.0, 110.0, 90.0, 95.0, 109.0, 111.0, 112.0], index=idx)

    dd = mod.compute_max_drawdown(equity)
    rec = mod.compute_recovery_days(equity)

    expected_dd = (90.0 / 110.0) - 1.0
    assert dd == pytest.approx(expected_dd, rel=1e-8, abs=1e-8)
    assert int(rec) == 3


def test_equity_curve_builder_schema_and_shape():
    mod = _load_verifier()
    idx = pd.date_range("2024-01-01", periods=40, freq="B")
    spy = pd.Series(np.linspace(100.0, 120.0, len(idx)), index=idx)
    exposure = pd.Series(np.linspace(0.0, 1.0, len(idx)), index=idx)
    eq, bh = mod._equity_curves(spy, exposure)

    assert isinstance(eq, pd.Series)
    assert isinstance(bh, pd.Series)
    assert len(eq) == len(idx)
    assert len(bh) == len(idx)
    assert eq.index.equals(idx)
    assert bh.index.equals(idx)


def test_window_performance_helper_returns_expected_schema():
    mod = _load_verifier()
    history = _build_synthetic_history(mod)
    perf = mod.compute_window_performance(history)

    assert isinstance(perf, pd.DataFrame)
    required = {
        "truth_window",
        "rows",
        "max_dd_strategy",
        "max_dd_buyhold",
        "dd_reduction_pct",
        "recovery_days_strategy",
        "recovery_days_buyhold",
        "recovery_gain_days",
    }
    assert required.issubset(set(perf.columns))
    assert set(mod.WINDOWS.keys()).issubset(set(perf["truth_window"]))
