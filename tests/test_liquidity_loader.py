import numpy as np
import pandas as pd

from data.liquidity_loader import LiquidityConfig, build_features


def test_build_features_adds_realized_vol_and_vrp():
    calendar = pd.date_range("2025-01-01", periods=30, freq="B")
    n = len(calendar)

    fred = pd.DataFrame(
        {
            "walcl_mm": np.linspace(8_500.0, 8_700.0, n),
            "wdtgal_mm": np.linspace(400.0, 420.0, n),
            "rrp_bn": np.linspace(150.0, 155.0, n),
            "sofr_rate": np.linspace(5.2, 5.1, n),
            "effr_rate": np.linspace(5.1, 5.0, n),
            "dtb3_rate": np.linspace(5.0, 4.8, n),
        },
        index=calendar,
    )
    yclose = pd.DataFrame(
        {
            "vix_level": np.linspace(18.0, 22.0, n),
            "dxy_px": np.linspace(104.0, 106.0, n),
            "spx_px": np.linspace(5_000.0, 5_100.0, n),
        },
        index=calendar,
    )
    spy_ohlc = pd.DataFrame(
        {
            "open": np.linspace(500.0, 530.0, n),
            "close": np.linspace(501.0, 533.0, n),
        },
        index=calendar,
    )

    features = build_features(calendar, fred, yclose, spy_ohlc, LiquidityConfig()).set_index("date")

    assert "realized_vol_21d" in features.columns
    assert "vrp" in features.columns
    assert features["realized_vol_21d"].dtype == np.float32
    assert features["vrp"].dtype == np.float32

    expected_realized = (
        spy_ohlc["close"].pct_change(fill_method=None).rolling(window=21, min_periods=21).std()
        * np.sqrt(252.0)
        * 100.0
    )
    expected_vrp = yclose["vix_level"] - expected_realized

    valid_mask = expected_realized.notna()
    assert int(valid_mask.sum()) == n - 21
    np.testing.assert_allclose(
        features.loc[valid_mask, "realized_vol_21d"].to_numpy(dtype="float64"),
        expected_realized.loc[valid_mask].to_numpy(dtype="float64"),
        rtol=1e-5,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        features.loc[valid_mask, "vrp"].to_numpy(dtype="float64"),
        expected_vrp.loc[valid_mask].to_numpy(dtype="float64"),
        rtol=1e-5,
        atol=1e-5,
    )
