from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from data import build_macro_tri as macro_mod
from data import build_tri as tri_mod


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_build_prices_tri_schema_and_patch_priority(tmp_path, monkeypatch):
    base = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-01-02",
                    "2020-01-03",
                    "2020-01-01",
                    "2020-01-02",
                    "2020-01-03",
                ]
            ),
            "permno": [1, 1, 1, 2, 2, 2],
            "raw_close": [100.0, 110.0, 121.0, 50.0, 52.5, 55.125],
            "adj_close": [100.0, 110.0, 121.0, 50.0, 52.5, 55.125],
            "total_ret": [0.0, 0.1, 0.1, 0.0, 0.05, 0.05],
            "volume": [1_000_000.0] * 6,
        }
    )
    patch = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-02"]),
            "permno": [1],
            "raw_close": [120.0],
            "adj_close": [120.0],
            "total_ret": [0.2],  # should override base on duplicate key
            "volume": [1_100_000.0],
        }
    )
    tickers = pd.DataFrame({"permno": [1, 2], "ticker": ["AAA", "BBB"]})

    base_path = tmp_path / "prices.parquet"
    patch_path = tmp_path / "yahoo_patch.parquet"
    tickers_path = tmp_path / "tickers.parquet"
    output_path = tmp_path / "prices_tri.parquet"
    _write_parquet(base, base_path)
    _write_parquet(patch, patch_path)
    _write_parquet(tickers, tickers_path)

    monkeypatch.setattr(tri_mod, "PRICES_PATH", base_path)
    monkeypatch.setattr(tri_mod, "PATCH_PATH", patch_path)
    monkeypatch.setattr(tri_mod, "TICKERS_PATH", tickers_path)
    monkeypatch.setattr(tri_mod, "MACRO_TRI_PATH", tmp_path / "macro_features_tri.parquet")

    summary = tri_mod.build_prices_tri(
        start_date=pd.Timestamp("2020-01-01"),
        end_date=pd.Timestamp("2020-01-03"),
        output_path=output_path,
        base_value=100.0,
    )

    assert summary.rows == 6
    out = pd.read_parquet(output_path).sort_values(["permno", "date"]).reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    assert {"date", "permno", "ticker", "tri", "total_ret", "legacy_adj_close", "raw_close", "volume"} == set(out.columns)
    assert "adj_close" not in out.columns

    # Patch precedence check: permno=1 date=2020-01-02 should carry total_ret=0.2 from patch.
    row = out[(out["permno"] == 1) & (out["date"] == pd.Timestamp("2020-01-02"))].iloc[0]
    assert np.isclose(float(row["total_ret"]), 0.2, rtol=0.0, atol=1e-8)

    # TRI math check for permno=1 with base=100:
    # day1: 100, day2: 120, day3: 132.
    p1 = out[out["permno"] == 1].sort_values("date")
    np.testing.assert_allclose(p1["tri"].to_numpy(), np.array([100.0, 120.0, 132.0]), rtol=1e-6, atol=1e-6)


def test_build_validation_report_split_continuity(tmp_path, monkeypatch):
    tri_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-08-28", "2020-08-31", "2020-09-01"]),
            "permno": [14593, 14593, 14593],
            "ticker": ["AAPL", "AAPL", "AAPL"],
            "tri": [100.0, 101.0, 102.0],
            "total_ret": [0.0, 0.01, 0.01],
            "legacy_adj_close": [500.0, 125.0, 126.0],  # split jump in legacy series
            "raw_close": [500.0, 125.0, 126.0],
            "volume": [1_000_000.0, 1_100_000.0, 1_200_000.0],
        }
    )
    tri_path = tmp_path / "prices_tri.parquet"
    report_path = tmp_path / "tri_validation.csv"
    _write_parquet(tri_df, tri_path)

    monkeypatch.setattr(tri_mod, "KNOWN_SPLITS", [("AAPL", "2020-08-31", 4.0)])
    monkeypatch.setattr(tri_mod, "DIVIDEND_TICKERS", [])
    monkeypatch.setattr(tri_mod, "MACRO_TRI_PATH", tmp_path / "missing_macro_features_tri.parquet")

    report = tri_mod.build_validation_report(
        tri_path=tri_path,
        output_csv_path=report_path,
        split_tolerance=0.02,
    )

    assert report_path.exists()
    assert len(report) == 1
    row = report.iloc[0]
    assert row["check_type"] == "split_continuity"
    assert bool(row["pass"]) is True
    assert abs(float(row["value"])) < 0.02


def test_build_validation_report_dividend_capture(tmp_path, monkeypatch):
    dates = pd.date_range("2023-01-02", periods=260, freq="B")
    tri_vals = np.linspace(100.0, 120.0, len(dates))
    legacy_vals = np.linspace(100.0, 110.0, len(dates))
    tri_df = pd.DataFrame(
        {
            "date": dates,
            "permno": [11850] * len(dates),
            "ticker": ["XOM"] * len(dates),
            "tri": tri_vals,
            "total_ret": np.r_[0.0, pd.Series(tri_vals).pct_change(fill_method=None).iloc[1:].to_numpy()],
            "legacy_adj_close": legacy_vals,
            "raw_close": legacy_vals,
            "volume": [2_000_000.0] * len(dates),
        }
    )
    tri_path = tmp_path / "prices_tri.parquet"
    report_path = tmp_path / "tri_validation.csv"
    _write_parquet(tri_df, tri_path)

    monkeypatch.setattr(tri_mod, "KNOWN_SPLITS", [])
    monkeypatch.setattr(tri_mod, "DIVIDEND_TICKERS", ["XOM"])
    monkeypatch.setattr(tri_mod, "MACRO_TRI_PATH", tmp_path / "missing_macro_features_tri.parquet")

    report = tri_mod.build_validation_report(
        tri_path=tri_path,
        output_csv_path=report_path,
    )
    assert len(report) == 1
    row = report.iloc[0]
    assert row["check_type"] == "dividend_capture"
    assert bool(row["pass"]) is True
    assert float(row["value"]) > 0.0


def test_build_macro_tri_uses_prices_tri_spy_series(tmp_path, monkeypatch):
    dates = pd.date_range("2020-01-01", periods=80, freq="B")
    macro_df = pd.DataFrame(
        {
            "date": dates,
            "spy_close": np.linspace(300.0, 340.0, len(dates)),
            "vix_level": np.linspace(20.0, 22.0, len(dates)),
            "mtum_px": np.linspace(100.0, 120.0, len(dates)),
            "dxy_px": np.linspace(95.0, 97.0, len(dates)),
            "mtum_spy_corr_60d": np.nan,
            "dxy_spx_corr_20d": np.nan,
        }
    )
    prices_tri_df = pd.DataFrame(
        {
            "date": dates,
            "permno": [84398] * len(dates),
            "ticker": ["SPY"] * len(dates),
            "tri": np.linspace(100.0, 130.0, len(dates)),
            "total_ret": np.r_[0.0, np.repeat(0.002, len(dates) - 1)],
            "legacy_adj_close": np.linspace(300.0, 340.0, len(dates)),
            "raw_close": np.linspace(300.0, 340.0, len(dates)),
            "volume": [3_000_000.0] * len(dates),
        }
    )

    macro_path = tmp_path / "macro_features.parquet"
    prices_tri_path = tmp_path / "prices_tri.parquet"
    output_path = tmp_path / "macro_features_tri.parquet"
    _write_parquet(macro_df, macro_path)
    _write_parquet(prices_tri_df, prices_tri_path)

    monkeypatch.setattr(macro_mod, "MACRO_FEATURES_PATH", macro_path)
    monkeypatch.setattr(macro_mod, "PRICES_TRI_PATH", prices_tri_path)

    summary = macro_mod.build_macro_tri(
        input_path=macro_path,
        output_path=output_path,
        start_date=None,
        end_date=None,
        base_value=100.0,
    )
    assert summary.rows == len(dates)

    out = pd.read_parquet(output_path).sort_values("date")
    assert {"spy_tri", "vix_tri", "mtum_tri", "dxy_tri", "vix_proxy", "mtum_spy_corr_60d", "dxy_spx_corr_20d"}.issubset(
        set(out.columns)
    )

    merged = out[["date", "spy_tri"]].merge(prices_tri_df[["date", "tri"]], on="date", how="inner")
    diff = np.abs(merged["spy_tri"].to_numpy() - merged["tri"].to_numpy()).max()
    assert diff < 1e-5
