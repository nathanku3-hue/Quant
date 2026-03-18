import math

import numpy as np
import pandas as pd

from utils.spa import BootstrapConfig, spa_p_value, spa_wrc_pvalues, wrc_p_value


def test_spa_deterministic_seed():
    rng = np.random.default_rng(0)
    returns = pd.Series(rng.normal(size=200))
    cfg = BootstrapConfig(n_boot=200, seed=123, block_size=5)
    p1 = spa_p_value(returns, config=cfg)
    p2 = spa_p_value(returns, config=cfg)
    assert math.isfinite(p1)
    assert p1 == p2


def test_wrc_deterministic_seed():
    rng = np.random.default_rng(1)
    returns = pd.Series(rng.normal(size=200))
    cfg = BootstrapConfig(n_boot=200, seed=321, block_size=4)
    p1 = wrc_p_value(returns, config=cfg)
    p2 = wrc_p_value(returns, config=cfg)
    assert math.isfinite(p1)
    assert p1 == p2


def test_p_value_bounds():
    rng = np.random.default_rng(2)
    data = pd.DataFrame(
        {
            "a": rng.normal(size=300),
            "b": rng.normal(size=300),
        }
    )
    cfg = BootstrapConfig(n_boot=200, seed=7, block_size=6)
    spa_p = spa_p_value(data, config=cfg)
    wrc_p = wrc_p_value(data, config=cfg)
    assert 0.0 <= spa_p <= 1.0
    assert 0.0 <= wrc_p <= 1.0


def test_nan_short_series():
    short = pd.Series([0.01, -0.02])
    cfg = BootstrapConfig(n_boot=50, seed=9)
    spa_p = spa_p_value(short, config=cfg, min_obs=5)
    assert math.isnan(spa_p)

    nan_series = pd.Series([np.nan, np.nan, np.nan])
    wrc_p = wrc_p_value(nan_series, config=cfg, min_obs=3)
    assert math.isnan(wrc_p)


def test_wrc_diagnostic_co_report():
    rng = np.random.default_rng(3)
    returns = pd.Series(rng.normal(size=150))
    cfg = BootstrapConfig(n_boot=150, seed=5, block_size=5)
    out = spa_wrc_pvalues(returns, config=cfg)
    assert set(out.keys()) == {"spa_p", "wrc_p"}
    assert out["spa_p"] == spa_p_value(returns, config=cfg)
    assert out["wrc_p"] == wrc_p_value(returns, config=cfg)


def test_sequence_benchmark_aligns_by_position_for_indexed_returns():
    idx = pd.date_range("2022-01-01", periods=120, freq="D")
    returns = pd.DataFrame(
        {
            "a": np.linspace(0.001, 0.010, num=120),
            "b": np.linspace(-0.002, 0.008, num=120),
        },
        index=idx,
    )
    benchmark = np.linspace(0.0005, 0.0025, num=120)
    cfg = BootstrapConfig(n_boot=100, seed=11, block_size=4)

    out = spa_wrc_pvalues(returns, benchmark=benchmark, config=cfg, min_obs=20)

    assert 0.0 <= out["spa_p"] <= 1.0
    assert 0.0 <= out["wrc_p"] <= 1.0
