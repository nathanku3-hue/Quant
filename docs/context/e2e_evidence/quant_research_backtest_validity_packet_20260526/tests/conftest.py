from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def sample_prices_wide() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=6, freq="B")
    return pd.DataFrame(
        {
            "AAA": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            "BBB": [50.0, 49.5, 50.5, 51.0, 50.8, 51.5],
        },
        index=idx,
    )


@pytest.fixture
def sample_returns_wide(sample_prices_wide: pd.DataFrame) -> pd.DataFrame:
    return sample_prices_wide.pct_change().fillna(0.0)


@pytest.fixture
def sample_macro() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=6, freq="B")
    return pd.DataFrame(
        {
            "spy_close": [500.0, 502.0, 503.0, 504.0, 505.0, 506.0],
            "vix_proxy": [15.0, 16.0, 15.5, 16.5, 17.0, 16.0],
            "regime_scalar": [1.0, 1.0, 0.8, 0.8, 1.0, 1.0],
        },
        index=idx,
    )


@pytest.fixture
def sample_ticker_map() -> dict[int, str]:
    return {101: "AAA", 202: "BBB"}
