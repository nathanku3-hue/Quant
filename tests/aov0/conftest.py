from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from research.aov0.contracts import DEFAULT_CONTRACT


@pytest.fixture
def development_contract():
    return replace(
        DEFAULT_CONTRACT,
        insurance_materiality_floor_ratio=0.05,
        insurance_premium_ceiling_annual_return=0.005,
    )


@pytest.fixture
def aov_dates() -> pd.DatetimeIndex:
    return pd.date_range("2026-07-27", periods=8, freq="B")


@pytest.fixture
def aov_primitives(aov_dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for i, date in enumerate(aov_dates):
        for security_id, sign, quality in (("CIQSEC:101", 1.0, 1.2), ("CIQSEC:202", -1.0, 0.6)):
            known = pd.Timestamp(date, tz="UTC") + pd.Timedelta(hours=21)
            valid = pd.Timestamp(date, tz="UTC") + pd.Timedelta(hours=20)
            rows.append(
                {
                    "date": date,
                    "security_id": security_id,
                    "valid_at": valid.isoformat(),
                    "known_at": known.isoformat(),
                    "total_return": sign * (0.004 + i * 0.0005),
                    "realized_vol": 0.02 + (0.001 if security_id == "CIQSEC:202" else 0.0),
                    "dollar_volume": 120_000_000 + i * 3_000_000 + (20_000_000 if security_id == "CIQSEC:101" else 0),
                    "adv20": 100_000_000 + (10_000_000 if security_id == "CIQSEC:101" else 0),
                    "quality": quality,
                    "trend_fast": sign * (0.8 + i * 0.03),
                    "trend_slow": sign * 0.5,
                    "exit_capacity": 0.85 if security_id == "CIQSEC:101" else 0.55,
                    "regime": -0.2 if i >= 4 else 0.2,
                    "uncertainty": 0.15 if security_id == "CIQSEC:101" else 0.30,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def rule100_weights(aov_dates: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CIQSEC:101": [0.30, 0.30, 0.30, 0.25, 0.25, 0.25, 0.25, 0.25],
            "CIQSEC:202": [0.20, 0.20, 0.20, 0.25, 0.25, 0.25, 0.25, 0.25],
        },
        index=aov_dates,
    )


@pytest.fixture
def aov_returns(aov_dates: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CIQSEC:101": [0.0, 0.012, -0.008, 0.005, -0.018, 0.009, -0.004, 0.006],
            "CIQSEC:202": [0.0, -0.006, 0.010, -0.004, -0.025, 0.007, 0.003, -0.005],
        },
        index=aov_dates,
    )


@pytest.fixture
def economic_cash_returns(aov_dates: pd.DatetimeIndex) -> pd.Series:
    return pd.Series([0.0] + [0.00018] * 7, index=aov_dates, name="economic_cash")
