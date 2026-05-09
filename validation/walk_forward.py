from __future__ import annotations

from typing import Any

import pandas as pd

from validation.metrics import coerce_return_series
from validation.metrics import summarize_returns


def run_walk_forward(
    frame: pd.DataFrame,
    *,
    return_col: str = "net_ret",
    train_size: int = 60,
    test_size: int = 20,
    step_size: int | None = None,
) -> dict[str, Any]:
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    step = int(step_size or test_size)
    if step <= 0:
        raise ValueError("step_size must be positive")
    work = frame.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.dropna(subset=["date"]).sort_values("date")
    returns = coerce_return_series(work, return_col=return_col)
    windows: list[dict[str, Any]] = []
    start = 0
    while start + train_size + test_size <= len(returns):
        train = returns.iloc[start : start + train_size]
        test = returns.iloc[start + train_size : start + train_size + test_size]
        windows.append(
            {
                "window": len(windows) + 1,
                "train": summarize_returns(train),
                "test": summarize_returns(test),
            }
        )
        start += step
    if not windows:
        raise ValueError("walk-forward validation produced no windows")
    positive = sum(1 for row in windows if (row["test"]["mean_daily_return"] or 0.0) > 0.0)
    return {
        "windows": windows,
        "positive_test_windows": int(positive),
        "window_count": int(len(windows)),
        "passed": bool(positive >= max(1, len(windows) // 2)),
    }

