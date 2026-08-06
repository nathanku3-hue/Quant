from __future__ import annotations

import pandas as pd
import pytest

from research.aov0.cash import build_economic_cash_returns


def test_official_sofr_minus_25bp_act360_accrual() -> None:
    dates = pd.DatetimeIndex(["2026-01-02", "2026-01-05", "2026-01-06"])
    sofr = pd.DataFrame({
        "effective_date": ["2026-01-01", "2026-01-02", "2026-01-05"],
        "published_at": ["2026-01-02T08:00:00Z", "2026-01-05T08:00:00Z", "2026-01-06T08:00:00Z"],
        "sofr_percent": [4.50, 4.60, 4.70],
    })
    result = build_economic_cash_returns(dates, sofr)
    assert result.iloc[0] == 0.0
    assert result.iloc[1] == pytest.approx((0.045 - 0.0025) * 3 / 360)
    assert result.iloc[2] == pytest.approx((0.046 - 0.0025) * 1 / 360)


def test_missing_published_sofr_blocks_instead_of_proxy_substitution() -> None:
    dates = pd.DatetimeIndex(["2026-01-02", "2026-01-05"])
    sofr = pd.DataFrame({
        "effective_date": ["2026-01-02"],
        "published_at": ["2026-01-05T08:00:00Z"],
        "sofr_percent": [4.60],
    })
    with pytest.raises(ValueError, match="official_sofr_unavailable"):
        build_economic_cash_returns(dates, sofr)
