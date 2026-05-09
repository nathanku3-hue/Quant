from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from validation.metrics import coerce_return_series


def run_bootstrap_ci(
    frame: pd.DataFrame,
    *,
    return_col: str = "net_ret",
    n_bootstrap: int = 500,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict[str, Any]:
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    if not 0.0 < float(confidence) < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    returns = coerce_return_series(frame, return_col=return_col).to_numpy(dtype=float)
    if len(returns) < 3:
        raise ValueError("bootstrap requires at least 3 observations")
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(int(n_bootstrap)):
        sample = rng.choice(returns, size=len(returns), replace=True)
        means.append(float(np.mean(sample)))
    alpha = 1.0 - float(confidence)
    low = float(np.quantile(means, alpha / 2.0))
    high = float(np.quantile(means, 1.0 - alpha / 2.0))
    observed = float(np.mean(returns))
    return {
        "observed_mean_daily_return": observed,
        "n_bootstrap": int(n_bootstrap),
        "confidence": float(confidence),
        "mean_ci_low": low,
        "mean_ci_high": high,
        "passed": bool(low > 0.0),
    }

