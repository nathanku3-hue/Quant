from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm


EULER_GAMMA = 0.5772156649015329


def safe_sharpe(returns: pd.Series, periods_per_year: float = 252.0) -> float:
    r = pd.to_numeric(returns, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(r) < 2:
        return float("nan")
    sigma = float(r.std(ddof=1))
    if not np.isfinite(sigma) or sigma <= 0.0:
        return float("nan")
    return float((r.mean() / sigma) * np.sqrt(float(periods_per_year)))


def average_pairwise_correlation(return_matrix: pd.DataFrame) -> float:
    if return_matrix is None or return_matrix.empty:
        return 0.0
    corr = return_matrix.corr(min_periods=2)
    if corr.empty:
        return 0.0
    arr = corr.to_numpy(dtype=float)
    if arr.shape[0] <= 1:
        return 0.0
    mask = ~np.eye(arr.shape[0], dtype=bool)
    off_diag = arr[mask]
    off_diag = off_diag[np.isfinite(off_diag)]
    if off_diag.size == 0:
        return 0.0
    return float(np.clip(np.mean(off_diag), -1.0, 1.0))


def effective_number_of_trials(return_matrix: pd.DataFrame) -> float:
    if return_matrix is None or return_matrix.empty:
        return 1.0
    n_trials = int(return_matrix.shape[1])
    if n_trials <= 1:
        return 1.0
    rho = average_pairwise_correlation(return_matrix)
    neff = float(n_trials) * (1.0 - rho) + 1.0
    return float(np.clip(neff, 1.0, float(n_trials)))


def probabilistic_sharpe_ratio(
    sr_hat: float,
    sr_benchmark: float,
    n_obs: int,
    skewness: float,
    kurtosis: float,
) -> float:
    if n_obs <= 1 or not np.isfinite(sr_hat) or not np.isfinite(sr_benchmark):
        return float("nan")
    denom = 1.0 - (skewness * sr_hat) + (((kurtosis - 1.0) / 4.0) * (sr_hat**2))
    if not np.isfinite(denom) or denom <= 0.0:
        return float("nan")
    z = (sr_hat - sr_benchmark) * np.sqrt(max(float(n_obs) - 1.0, 1.0)) / np.sqrt(denom)
    return float(norm.cdf(z))


def expected_max_sharpe(sr_estimates: pd.Series, n_trials_eff: float) -> float:
    sr = pd.to_numeric(sr_estimates, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if sr.empty:
        return float("nan")
    mu = float(sr.mean())
    sigma = float(sr.std(ddof=1))
    if not np.isfinite(sigma) or sigma <= 0.0:
        return mu
    n_eff = float(max(1.0, n_trials_eff))
    z1 = float(norm.ppf(1.0 - (1.0 / n_eff)))
    z2 = float(norm.ppf(1.0 - (1.0 / (n_eff * math.e))))
    return float(mu + (sigma * (((1.0 - EULER_GAMMA) * z1) + (EULER_GAMMA * z2))))


def deflated_sharpe_ratio(
    returns: pd.Series,
    sr_estimates: pd.Series,
    n_trials_eff: float,
    periods_per_year: float = 252.0,
) -> dict[str, float]:
    r = pd.to_numeric(returns, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    n_obs = int(len(r))
    sr_hat = safe_sharpe(r, periods_per_year=periods_per_year)
    if n_obs <= 2 or not np.isfinite(sr_hat):
        return {
            "sr_hat": float("nan"),
            "sr_benchmark": float("nan"),
            "psr": float("nan"),
            "dsr": float("nan"),
            "n_obs": float(n_obs),
            "skewness": float("nan"),
            "kurtosis": float("nan"),
        }
    skewness = float(r.skew())
    kurtosis = float(r.kurt()) + 3.0
    sr_benchmark = expected_max_sharpe(sr_estimates=sr_estimates, n_trials_eff=n_trials_eff)
    psr = probabilistic_sharpe_ratio(
        sr_hat=sr_hat,
        sr_benchmark=sr_benchmark,
        n_obs=n_obs,
        skewness=skewness,
        kurtosis=kurtosis,
    )
    return {
        "sr_hat": float(sr_hat),
        "sr_benchmark": float(sr_benchmark),
        "psr": float(psr),
        "dsr": float(psr),
        "n_obs": float(n_obs),
        "skewness": float(skewness),
        "kurtosis": float(kurtosis),
    }


def build_cscv_splits(n_blocks: int) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    blocks = int(n_blocks)
    if blocks < 2 or blocks % 2 != 0:
        raise ValueError("n_blocks must be an even integer >= 2")
    all_blocks = tuple(range(blocks))
    half = blocks // 2
    splits: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for train in itertools.combinations(all_blocks, half):
        train_set = set(train)
        test = tuple([b for b in all_blocks if b not in train_set])
        splits.append((tuple(sorted(train)), tuple(sorted(test))))
    return splits


def build_cscv_block_series(index: pd.Index, n_blocks: int) -> pd.Series:
    if len(index) == 0:
        return pd.Series(dtype=int)
    idx = pd.DatetimeIndex(pd.to_datetime(index, errors="coerce")).dropna().sort_values().unique()
    if len(idx) == 0:
        return pd.Series(dtype=int)
    n_blocks = int(n_blocks)
    if n_blocks < 2 or n_blocks % 2 != 0:
        raise ValueError("n_blocks must be an even integer >= 2")
    positions = np.arange(len(idx), dtype=int)
    raw = np.floor((positions * n_blocks) / len(idx)).astype(int)
    raw = np.clip(raw, 0, n_blocks - 1)
    return pd.Series(raw, index=idx, dtype=int)


@dataclass(frozen=True)
class CSCVResult:
    split_results: pd.DataFrame
    summary: dict[str, Any]


def cscv_analysis(
    return_matrix: pd.DataFrame,
    n_blocks: int = 6,
    periods_per_year: float = 252.0,
) -> CSCVResult:
    if return_matrix is None or return_matrix.empty:
        return CSCVResult(split_results=pd.DataFrame(), summary={"pbo": float("nan"), "n_splits": 0, "n_variants": 0})

    work = return_matrix.copy()
    work.index = pd.to_datetime(work.index, errors="coerce")
    work = work[~work.index.isna()].sort_index()
    if work.empty:
        return CSCVResult(split_results=pd.DataFrame(), summary={"pbo": float("nan"), "n_splits": 0, "n_variants": 0})

    block_map = build_cscv_block_series(work.index, n_blocks=n_blocks)
    splits = build_cscv_splits(n_blocks=n_blocks)
    rows: list[dict[str, Any]] = []

    for split_id, (train_blocks, test_blocks) in enumerate(splits, start=1):
        train_dates = block_map.index[block_map.isin(train_blocks)]
        test_dates = block_map.index[block_map.isin(test_blocks)]
        train_slice = work.loc[work.index.isin(train_dates)]
        test_slice = work.loc[work.index.isin(test_dates)]
        if train_slice.empty or test_slice.empty:
            continue

        train_sharpes = train_slice.apply(lambda col: safe_sharpe(col, periods_per_year=periods_per_year))
        train_sharpes = train_sharpes.replace([np.inf, -np.inf], np.nan).dropna()
        if train_sharpes.empty:
            continue

        selected_variant = str(train_sharpes.idxmax())
        selected_train_sharpe = float(train_sharpes.loc[selected_variant])
        test_sharpes = test_slice.apply(lambda col: safe_sharpe(col, periods_per_year=periods_per_year))
        test_sharpes = test_sharpes.replace([np.inf, -np.inf], np.nan).dropna()
        if selected_variant not in test_sharpes.index or test_sharpes.empty:
            continue

        selected_test_sharpe = float(test_sharpes.loc[selected_variant])
        ranks = test_sharpes.rank(method="average", ascending=True)
        rel_rank = float(ranks.loc[selected_variant] / float(len(test_sharpes) + 1))
        rel_rank = float(np.clip(rel_rank, 1e-9, 1.0 - 1e-9))
        logit = float(np.log(rel_rank / (1.0 - rel_rank)))
        rows.append(
            {
                "split_id": int(split_id),
                "train_blocks": ",".join(str(x) for x in train_blocks),
                "test_blocks": ",".join(str(x) for x in test_blocks),
                "selected_variant": selected_variant,
                "selected_train_sharpe": selected_train_sharpe,
                "selected_test_sharpe": selected_test_sharpe,
                "selected_test_rank_pct": rel_rank * 100.0,
                "lambda_logit_rank": logit,
            }
        )

    split_df = pd.DataFrame(rows)
    if split_df.empty:
        return CSCVResult(
            split_results=split_df,
            summary={
                "pbo": float("nan"),
                "n_splits": 0,
                "n_variants": int(work.shape[1]),
                "n_blocks": int(n_blocks),
            },
        )

    pbo = float((split_df["lambda_logit_rank"] <= 0.0).mean())
    summary = {
        "pbo": pbo,
        "n_splits": int(len(split_df)),
        "n_variants": int(work.shape[1]),
        "n_blocks": int(n_blocks),
        "median_selected_train_sharpe": float(split_df["selected_train_sharpe"].median()),
        "median_selected_test_sharpe": float(split_df["selected_test_sharpe"].median()),
        "mean_selected_test_rank_pct": float(split_df["selected_test_rank_pct"].mean()),
    }
    return CSCVResult(split_results=split_df, summary=summary)

