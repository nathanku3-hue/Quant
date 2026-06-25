from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from utils.statistics import (
    build_cscv_block_series,
    build_cscv_splits,
    cscv_analysis,
    deflated_sharpe_ratio,
    effective_number_of_trials,
)


def test_build_cscv_splits_matches_binomial_for_even_blocks():
    splits = build_cscv_splits(6)
    assert len(splits) == 20  # C(6, 3)
    for train, test in splits:
        assert len(train) == 3
        assert len(test) == 3
        assert set(train).isdisjoint(set(test))
        assert set(train).union(set(test)) == set(range(6))


def test_build_cscv_splits_rejects_odd_blocks():
    with pytest.raises(ValueError):
        build_cscv_splits(5)


def test_build_cscv_block_series_uses_all_blocks():
    idx = pd.date_range("2020-01-01", periods=24, freq="ME")
    block_map = build_cscv_block_series(idx, n_blocks=6)
    assert sorted(block_map.unique().tolist()) == [0, 1, 2, 3, 4, 5]
    assert len(block_map) == 24


def test_effective_number_of_trials_bounds_and_perfect_corr_case():
    idx = pd.date_range("2020-01-01", periods=30, freq="D")

    base = pd.Series(np.linspace(-0.02, 0.02, len(idx)), index=idx)
    perfect = pd.concat(
        [
            base.rename("v1"),
            base.rename("v2"),
            base.rename("v3"),
        ],
        axis=1,
    )
    neff_perfect = effective_number_of_trials(perfect)
    assert neff_perfect == pytest.approx(1.0)

    rng = np.random.default_rng(42)
    noisy = pd.DataFrame(
        {
            "v1": rng.normal(0.0, 0.01, len(idx)),
            "v2": rng.normal(0.0, 0.01, len(idx)),
            "v3": rng.normal(0.0, 0.01, len(idx)),
            "v4": rng.normal(0.0, 0.01, len(idx)),
        },
        index=idx,
    )
    neff_noisy = effective_number_of_trials(noisy)
    assert 1.0 <= neff_noisy <= float(noisy.shape[1])


def test_deflated_sharpe_ratio_returns_probability_like_metrics():
    rng = np.random.default_rng(7)
    idx = pd.date_range("2021-01-01", periods=120, freq="D")
    returns = pd.Series(rng.normal(0.001, 0.01, len(idx)), index=idx)
    sr_pool = pd.Series([0.2, 0.4, 0.6, 0.8], dtype=float)

    out = deflated_sharpe_ratio(
        returns=returns,
        sr_estimates=sr_pool,
        n_trials_eff=3.0,
        periods_per_year=252.0,
    )
    assert np.isfinite(out["sr_hat"])
    assert np.isfinite(out["sr_benchmark"])
    assert 0.0 <= out["psr"] <= 1.0
    assert 0.0 <= out["dsr"] <= 1.0


def test_cscv_analysis_returns_expected_split_count_for_six_blocks():
    idx = pd.date_range("2022-01-01", periods=60, freq="D")
    t = np.linspace(0.0, 2.0 * np.pi, len(idx))
    returns = pd.DataFrame(
        {
            "a": 0.001 + 0.01 * np.sin(t),
            "b": 0.0005 + 0.008 * np.cos(t),
            "c": 0.0008 + 0.009 * np.sin(t + 0.5),
        },
        index=idx,
    )
    out = cscv_analysis(return_matrix=returns, n_blocks=6, periods_per_year=252.0)
    assert not out.split_results.empty
    assert out.summary["n_splits"] == 20
    assert out.summary["n_variants"] == 3
    assert 0.0 <= out.summary["pbo"] <= 1.0
