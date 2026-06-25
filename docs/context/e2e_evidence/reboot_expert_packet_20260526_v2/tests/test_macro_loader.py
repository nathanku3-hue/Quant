from __future__ import annotations

import numpy as np
import pandas as pd

from data import macro_loader as ml


def _synthetic_macro_inputs() -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.DataFrame]:
    calendar = pd.date_range("2020-01-01", periods=340, freq="B")
    n = len(calendar)

    qqq_ret = np.full(n, 0.0005, dtype=float)
    qqq_ret[220:300] = -0.0060
    qqq_ret[300] = -0.12
    qqq_ret[315:325] = 0.04  # future rebound to verify no lookahead in 252d peak.
    qqq_close = 100.0 * np.cumprod(1.0 + qqq_ret)

    vix3m = np.full(n, 22.0, dtype=float)
    vix = np.full(n, 18.0, dtype=float)
    vix[295:305] = 35.0
    vvix = np.full(n, 95.0, dtype=float)
    vvix[295:305] = 130.0

    base_prices = {
        "vix_level": vix,
        "vix3m_level": vix3m,
        "vvix_level": vvix,
        "dxy_px": np.linspace(100.0, 104.0, n),
        "spx_px": 3000.0 * (qqq_close / qqq_close[0]),
        "hyg_px": np.linspace(85.0, 92.0, n),
        "lqd_px": np.linspace(110.0, 114.0, n),
        "mtum_px": 120.0 * np.cumprod(1.0 + (qqq_ret * 0.8)),
        "spy_close": 420.0 * (qqq_close / qqq_close[0]),
        "qqq_close": qqq_close,
        "bnd_px": np.linspace(80.0, 82.0, n),
        "btc_px": np.linspace(9000.0, 11000.0, n),
    }
    yahoo_df = pd.DataFrame(index=calendar)
    for col in ml.YAHOO_SYMBOLS.values():
        if col in base_prices:
            yahoo_df[col] = base_prices[col]
        else:
            yahoo_df[col] = np.linspace(100.0, 101.0, n)

    fred_df = pd.DataFrame(
        {
            "sofr_rate": np.full(n, 5.25, dtype=float),
            "effr_rate": np.full(n, 5.10, dtype=float),
            "t10y2y_rate": np.linspace(0.20, -0.10, n),
            "dfii10_rate": np.linspace(1.80, 2.00, n),
        },
        index=calendar,
    )
    return calendar, yahoo_df, fred_df


def test_build_macro_gates_schema_and_red_behavior():
    calendar, yahoo_df, fred_df = _synthetic_macro_inputs()
    feats = ml.build_macro_features(
        calendar=calendar,
        yahoo_df=yahoo_df,
        fred_df=fred_df,
        thresholds=ml.MacroThresholds(),
    )
    assert len(feats) == len(calendar)

    feature_required = {
        "date",
        "qqq_peak_252d",
        "qqq_drawdown_252d",
        "qqq_drawdown_252d_z_adapt",
        "qqq_sma50",
        "qqq_ma200",
        "qqq_ma200_trend_gate",
        "qqq_ret_5d_z_adapt",
        "qqq_ret_21d_z_adapt",
        "slow_bleed_label",
        "sharp_shock_label",
        "vix_term_ratio",
        "vix_backwardation",
    }
    assert feature_required.issubset(set(feats.columns))

    assert feats["slow_bleed_label"].fillna(False).any()
    assert feats["sharp_shock_label"].fillna(False).any()

    shock_idx = 300
    shock_date = pd.Timestamp(calendar[shock_idx])
    expected_peak = float(feats.loc[shock_idx - 251:shock_idx, "qqq_close"].max())
    shock_peak = float(feats.loc[feats["date"] == shock_date, "qqq_peak_252d"].iloc[0])
    np.testing.assert_allclose(shock_peak, expected_peak, rtol=0.0, atol=1e-6)

    gates = ml.build_macro_gates(feats)
    gate_required = {
        "date",
        "state",
        "scalar",
        "cash_buffer",
        "momentum_entry",
        "reasons",
        "qqq_drawdown_252d",
        "qqq_sma50",
        "qqq_ma200_trend_gate",
        "slow_bleed",
        "sharp_shock",
        "qqq_ret_5d_z_adapt",
        "qqq_ret_21d_z_adapt",
        "qqq_drawdown_252d_z_adapt",
        "vix_term_ratio",
        "vix_backwardation",
    }
    assert gate_required.issubset(set(gates.columns))

    shock_gate = gates.loc[gates["date"] == shock_date].iloc[0]
    assert shock_gate["state"] == "RED"
    assert float(shock_gate["scalar"]) == 0.0
    assert bool(shock_gate["momentum_entry"]) is False
    assert "sharp_shock" in str(shock_gate["reasons"])


def test_run_build_writes_macro_gates_and_status(tmp_path, monkeypatch):
    calendar, yahoo_df, fred_df = _synthetic_macro_inputs()
    macro_features_path = tmp_path / "macro_features.parquet"
    macro_gates_path = tmp_path / "macro_gates.parquet"
    end_date = pd.Timestamp("2020-12-31")
    expected_rows = int((calendar <= end_date).sum())

    monkeypatch.setattr(ml, "MACRO_FEATURES_PATH", str(macro_features_path))
    monkeypatch.setattr(ml, "MACRO_GATES_PATH", str(macro_gates_path))
    monkeypatch.setattr(ml, "_load_trading_calendar", lambda start_date: calendar)
    monkeypatch.setattr(ml, "_download_yahoo", lambda symbol_map, start_date, end_date: yahoo_df)
    monkeypatch.setattr(ml, "_download_fred", lambda series_map, start_date, end_date: (fred_df, []))
    monkeypatch.setattr(
        ml,
        "_load_legacy_macro",
        lambda: pd.DataFrame(columns=["spy_close", "vix_proxy"]),
    )
    monkeypatch.setattr(ml.updater, "_acquire_update_lock", lambda: None)
    monkeypatch.setattr(ml.updater, "_release_update_lock", lambda: None)

    result = ml.run_build(start_year=2020, end_date=str(end_date.date()))

    assert result["success"] is True
    assert result["rows_written"] == expected_rows
    assert result["gates_rows_written"] == expected_rows
    assert result["macro_features_path"] == str(macro_features_path)
    assert result["macro_gates_path"] == str(macro_gates_path)

    assert macro_features_path.exists()
    assert macro_gates_path.exists()

    gates = pd.read_parquet(macro_gates_path)
    assert len(gates) == expected_rows
    assert pd.to_datetime(gates["date"], errors="coerce").max() <= end_date
    assert {"state", "scalar", "cash_buffer", "momentum_entry", "reasons"}.issubset(set(gates.columns))
