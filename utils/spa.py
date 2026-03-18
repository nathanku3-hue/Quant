from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BootstrapConfig:
    """Bootstrap configuration for SPA/WRC tests."""

    n_boot: int = 1000
    seed: int | None = 7
    block_size: int | None = None


def spa_p_value(
    returns: pd.Series | pd.DataFrame | Sequence[float],
    benchmark: pd.Series | Sequence[float] | None = None,
    config: BootstrapConfig | None = None,
    min_obs: int = 20,
) -> float:
    """Compute Hansen SPA bootstrap p-value for excess returns."""
    matrix = _prepare_excess_matrix(returns, benchmark=benchmark)
    return _spa_p_from_matrix(matrix, config=config, min_obs=min_obs)


def wrc_p_value(
    returns: pd.Series | pd.DataFrame | Sequence[float],
    benchmark: pd.Series | Sequence[float] | None = None,
    config: BootstrapConfig | None = None,
    min_obs: int = 20,
) -> float:
    """Compute White Reality Check bootstrap p-value for excess returns."""
    matrix = _prepare_excess_matrix(returns, benchmark=benchmark)
    return _wrc_p_from_matrix(matrix, config=config, min_obs=min_obs)


def spa_wrc_pvalues(
    returns: pd.Series | pd.DataFrame | Sequence[float],
    benchmark: pd.Series | Sequence[float] | None = None,
    config: BootstrapConfig | None = None,
    min_obs: int = 20,
) -> dict[str, float]:
    """Return both SPA and WRC p-values for the same input surface."""
    matrix = _prepare_excess_matrix(returns, benchmark=benchmark)
    return {
        "spa_p": _spa_p_from_matrix(matrix, config=config, min_obs=min_obs),
        "wrc_p": _wrc_p_from_matrix(matrix, config=config, min_obs=min_obs),
    }


def _spa_p_from_matrix(
    matrix: np.ndarray,
    config: BootstrapConfig | None,
    min_obs: int,
) -> float:
    matrix = _as_float_matrix(matrix)
    n_obs, n_strat = matrix.shape
    if n_obs < min_obs or n_strat == 0:
        return float("nan")

    mu = np.mean(matrix, axis=0)
    sigma = np.std(matrix, axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        t_obs = mu / (sigma / math.sqrt(float(n_obs)))
    t_obs = t_obs[np.isfinite(t_obs)]
    if t_obs.size == 0:
        return float("nan")
    t_obs_max = float(np.max(t_obs))

    adjust = np.maximum(mu, 0.0)
    centered = matrix - adjust
    idx = _bootstrap_indices(n_obs, config=config)
    boot = centered[idx]
    boot_mean = boot.mean(axis=1)
    boot_std = boot.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        boot_t = boot_mean / (boot_std / math.sqrt(float(n_obs)))
    boot_t = np.where(np.isfinite(boot_t), boot_t, -np.inf)
    boot_max = np.max(boot_t, axis=1)
    return float(np.mean(boot_max >= t_obs_max))


def _wrc_p_from_matrix(
    matrix: np.ndarray,
    config: BootstrapConfig | None,
    min_obs: int,
) -> float:
    matrix = _as_float_matrix(matrix)
    n_obs, n_strat = matrix.shape
    if n_obs < min_obs or n_strat == 0:
        return float("nan")

    mu = np.mean(matrix, axis=0)
    obs_max = float(np.max(mu))
    centered = matrix - mu
    idx = _bootstrap_indices(n_obs, config=config)
    boot = centered[idx]
    boot_mean = boot.mean(axis=1)
    boot_max = np.max(boot_mean, axis=1)
    return float(np.mean(boot_max >= obs_max))


def _prepare_excess_matrix(
    returns: pd.Series | pd.DataFrame | Sequence[float],
    benchmark: pd.Series | Sequence[float] | None,
) -> np.ndarray:
    frame = _coerce_frame(returns)
    if benchmark is not None:
        if isinstance(benchmark, pd.Series):
            bench = benchmark.copy()
        else:
            benchmark_values = list(benchmark)
            if len(benchmark_values) != len(frame.index):
                raise ValueError("benchmark length must match returns length when benchmark has no index")
            bench = pd.Series(benchmark_values, index=frame.index, name="benchmark")
        frame, bench = frame.align(bench, join="inner", axis=0)
        bench = pd.to_numeric(bench, errors="coerce")
        frame = frame.loc[bench.notna()]
        bench = bench.loc[bench.notna()]
        frame = frame.sub(bench, axis=0)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(how="any")
    if frame.empty:
        return np.empty((0, 0), dtype=float)
    return frame.to_numpy(dtype=float)


def _coerce_frame(returns: pd.Series | pd.DataFrame | Sequence[float]) -> pd.DataFrame:
    if isinstance(returns, pd.DataFrame):
        frame = returns.copy()
    elif isinstance(returns, pd.Series):
        frame = returns.to_frame(name="strategy")
    else:
        frame = pd.Series(list(returns), name="strategy").to_frame()
    for col in frame.columns:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def _as_float_matrix(matrix: np.ndarray) -> np.ndarray:
    if matrix is None:
        return np.empty((0, 0), dtype=float)
    arr = np.asarray(matrix, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    return arr


def _bootstrap_indices(n_obs: int, config: BootstrapConfig | None) -> np.ndarray:
    cfg = config or BootstrapConfig()
    n_boot = int(max(cfg.n_boot, 1))
    rng = np.random.default_rng(cfg.seed)
    block = cfg.block_size or 0
    if block <= 1:
        return rng.integers(0, n_obs, size=(n_boot, n_obs))

    block = int(min(block, n_obs))
    n_blocks = int(math.ceil(n_obs / float(block)))
    starts = rng.integers(0, n_obs, size=(n_boot, n_blocks))
    offsets = np.arange(block, dtype=int)
    idx = (starts[:, :, None] + offsets[None, None, :]) % n_obs
    idx = idx.reshape(n_boot, n_blocks * block)
    return idx[:, :n_obs]
