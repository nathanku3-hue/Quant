"""Economic-cash construction for AOV-0.

Contract: official SOFR only, minus 25 bp, ACT/360, no zero floor, and no
proxy substitution. A rate may be used only after its publication timestamp.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_SOFR_COLUMNS = ("effective_date", "published_at", "sofr_percent")


def build_economic_cash_returns(
    target_dates: pd.DatetimeIndex,
    official_sofr: pd.DataFrame,
) -> pd.Series:
    dates = pd.DatetimeIndex(pd.to_datetime(target_dates)).normalize()
    if dates.empty or not dates.is_monotonic_increasing or not dates.is_unique:
        raise ValueError("aov0_cash_target_dates_invalid")
    missing = [column for column in REQUIRED_SOFR_COLUMNS if column not in official_sofr.columns]
    if missing:
        raise ValueError(f"aov0_cash_missing_sofr_columns:{','.join(missing)}")
    rows = official_sofr.loc[:, REQUIRED_SOFR_COLUMNS].copy()
    rows["effective_date"] = pd.to_datetime(rows["effective_date"], errors="raise").dt.normalize()
    rows["published_at"] = pd.to_datetime(rows["published_at"], utc=True, errors="raise")
    rows["sofr_percent"] = pd.to_numeric(rows["sofr_percent"], errors="coerce")
    if rows["sofr_percent"].isna().any() or not np.isfinite(rows["sofr_percent"].to_numpy(dtype=float)).all():
        raise ValueError("aov0_cash_sofr_non_finite")
    if rows.duplicated(["effective_date", "published_at"]).any():
        raise ValueError("aov0_cash_duplicate_sofr_identity")
    rows = rows.sort_values(["published_at", "effective_date"]).reset_index(drop=True)

    result = pd.Series(0.0, index=dates, name="economic_cash", dtype=float)
    for index in range(1, len(dates)):
        interval_start = dates[index - 1]
        interval_end = dates[index]
        cutoff = pd.Timestamp(interval_start).tz_localize("UTC") + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        eligible = rows.loc[
            (rows["effective_date"] <= interval_start)
            & (rows["published_at"] <= cutoff)
        ]
        if eligible.empty:
            raise ValueError(f"aov0_cash_official_sofr_unavailable:{interval_start.date().isoformat()}")
        latest = eligible.sort_values(["effective_date", "published_at"]).iloc[-1]
        calendar_days = int((interval_end - interval_start).days)
        annual_rate = float(latest["sofr_percent"]) / 100.0 - 0.0025
        result.iloc[index] = annual_rate * float(calendar_days) / 360.0
    return result
