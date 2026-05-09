from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from validation.metrics import coerce_return_series


def run_permutation_test(
    frame: pd.DataFrame,
    *,
    return_col: str = "net_ret",
    n_permutations: int = 250,
    seed: int = 42,
) -> dict[str, Any]:
    if n_permutations <= 0:
        raise ValueError("n_permutations must be positive")
    returns = coerce_return_series(frame, return_col=return_col).to_numpy(dtype=float)
    if len(returns) < 3:
        raise ValueError("permutation test requires at least 3 observations")
    observed = float(np.mean(returns))
    rng = np.random.default_rng(seed)
    null_means = []
    signs = np.array([-1.0, 1.0])
    for _ in range(int(n_permutations)):
        flips = rng.choice(signs, size=len(returns), replace=True)
        null_means.append(float(np.mean(returns * flips)))
    exceed = sum(1 for value in null_means if value >= observed)
    p_value = (exceed + 1.0) / (len(null_means) + 1.0)
    return {
        "observed_mean_daily_return": observed,
        "n_permutations": int(n_permutations),
        "p_value": float(p_value),
        "passed": bool(observed > 0.0 and p_value <= 0.10),
    }

