from __future__ import annotations

from typing import Any

import pandas as pd

from validation.metrics import coerce_return_series
from validation.metrics import summarize_returns


def run_oos_test(
    frame: pd.DataFrame,
    *,
    return_col: str = "net_ret",
    split_date: str | pd.Timestamp | None = None,
    train_fraction: float = 0.7,
) -> dict[str, Any]:
    if frame.empty:
        raise ValueError("OOS validation requires non-empty returns")
    work = frame.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.dropna(subset=["date"]).sort_values("date")
    else:
        work = work.reset_index(drop=True)

    if split_date is not None:
        if "date" not in work.columns:
            raise ValueError("split_date requires a date column")
        split_ts = pd.Timestamp(split_date)
        train = work.loc[work["date"] <= split_ts]
        test = work.loc[work["date"] > split_ts]
    else:
        if not 0.0 < float(train_fraction) < 1.0:
            raise ValueError("train_fraction must be in (0, 1)")
        split_idx = max(1, min(len(work) - 1, int(len(work) * float(train_fraction))))
        train = work.iloc[:split_idx]
        test = work.iloc[split_idx:]

    if train.empty or test.empty:
        raise ValueError("OOS validation requires non-empty train and test slices")

    train_returns = coerce_return_series(train, return_col=return_col)
    test_returns = coerce_return_series(test, return_col=return_col)
    return {
        "train": summarize_returns(train_returns),
        "test": summarize_returns(test_returns),
        "passed": bool(len(test_returns) > 0 and float(test_returns.mean()) > 0.0),
    }

