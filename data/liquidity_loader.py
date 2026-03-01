"""
Terminal Zero — Global Liquidity & Flow Loader (FR-040)

Builds a PIT-safe liquidity feature layer:
  data/processed/liquidity_features.parquet
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import os
import sys
import time
import urllib.request
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
LIQUIDITY_PATH = os.path.join(PROCESSED_DIR, "liquidity_features.parquet")

FRED_SERIES = {
    "WALCL": "walcl_mm",
    "WDTGAL": "wdtgal_mm",
    "RRPONTSYD": "rrp_bn",
    "SOFR": "sofr_rate",
    "DFF": "effr_rate",
    "DTB3": "dtb3_rate",
}

YAHOO_CLOSE = {
    "^VIX": "vix_level",
    "DX-Y.NYB": "dxy_px",
    "^GSPC": "spx_px",
}


@dataclass(frozen=True)
class LiquidityConfig:
    weekly_release_lag_days: int = 2   # H.4.1: Wed reported -> Thu PM release -> use Fri session
    weekly_ffill_limit: int = 14
    daily_ffill_limit: int = 3
    impulse_roc_days: int = 20
    z_window: int = 63
    z_min_periods: int = 20
    corr_window: int = 20
    corr_min_periods: int = 20
    repo_stress_bps: float = 5.0
    dollar_stress_corr: float = 0.50


def _new_status() -> dict:
    return {
        "log": [],
        "warnings": [],
        "success": False,
        "rows_written": 0,
    }


def _log(status: dict, msg: str):
    print(msg)
    status["log"].append(msg)


def _warn(status: dict, msg: str):
    _log(status, f"⚠ {msg}")
    status["warnings"].append(msg)


def _sql_escape_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _load_trading_calendar(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp | None = None,
) -> pd.DatetimeIndex:
    if not os.path.exists(PRICES_PATH):
        raise FileNotFoundError(f"Missing prices parquet: {PRICES_PATH}")

    start_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
    end_str = pd.Timestamp(end_date).strftime("%Y-%m-%d") if end_date is not None else None
    where_clause = f"CAST(date AS DATE) >= DATE '{start_str}'"
    if end_str is not None:
        where_clause = where_clause + f" AND CAST(date AS DATE) <= DATE '{end_str}'"
    con = duckdb.connect()
    try:
        if os.path.exists(PATCH_PATH):
            q = f"""
                SELECT DISTINCT CAST(date AS DATE) AS date
                FROM (
                    SELECT date FROM '{_sql_escape_path(PRICES_PATH)}'
                    WHERE {where_clause}
                    UNION ALL
                    SELECT date FROM '{_sql_escape_path(PATCH_PATH)}'
                    WHERE {where_clause}
                )
                ORDER BY date
            """
        else:
            q = f"""
                SELECT DISTINCT CAST(date AS DATE) AS date
                FROM '{_sql_escape_path(PRICES_PATH)}'
                WHERE {where_clause}
                ORDER BY date
            """
        df = con.execute(q).df()
    finally:
        con.close()

    if df.empty:
        return pd.DatetimeIndex([])
    idx = pd.DatetimeIndex(pd.to_datetime(df["date"], errors="coerce"))
    idx = idx[~idx.isna()]
    return idx.sort_values().unique()


def _read_csv_url_with_retry(url: str, retries: int = 3, timeout_sec: int = 15) -> pd.DataFrame:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout_sec) as resp:
                payload = resp.read().decode("utf-8")
            return pd.read_csv(io.StringIO(payload))
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break
            time.sleep(0.75 * attempt)
    raise RuntimeError(f"failed to fetch url after {retries} attempts: {url}") from last_err


def _download_fred_series(series_id: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.Series:
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={start_date.strftime('%Y-%m-%d')}&coed={end_date.strftime('%Y-%m-%d')}"
    )
    df = _read_csv_url_with_retry(url)
    date_col = "DATE" if "DATE" in df.columns else "observation_date" if "observation_date" in df.columns else None
    if df.empty or date_col is None or series_id not in df.columns:
        return pd.Series(dtype="float64")

    vals = pd.to_numeric(df[series_id], errors="coerce")
    idx = pd.to_datetime(df[date_col], errors="coerce")
    s = pd.Series(vals.values, index=idx, name=series_id)
    s = s[~s.index.isna()].sort_index()
    return s[(s.index >= start_date) & (s.index <= end_date)]


def _download_fred(series_map: dict[str, str], start_date: pd.Timestamp, end_date: pd.Timestamp) -> tuple[pd.DataFrame, list[str]]:
    cols: dict[str, pd.Series] = {}
    failed: list[str] = []
    workers = min(4, len(series_map)) if series_map else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(_download_fred_series, sid, start_date, end_date): (sid, col)
            for sid, col in series_map.items()
        }
        for fut in as_completed(futs):
            sid, col = futs[fut]
            try:
                s = fut.result()
                cols[col] = s
                if s is None or s.empty:
                    failed.append(f"{sid}->{col}")
            except Exception:
                cols[col] = pd.Series(dtype="float64")
                failed.append(f"{sid}->{col}")

    if not cols:
        return pd.DataFrame(), failed
    return pd.DataFrame(cols).sort_index(), failed


def _parse_close(raw: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        layer = raw["Adj Close"] if "Adj Close" in raw.columns.get_level_values(0) else raw["Close"]
        out = layer.copy()
    else:
        col = "Adj Close" if "Adj Close" in raw.columns else "Close"
        out = raw[[col]].copy()
        out.columns = [symbols[0]]

    out.index = pd.DatetimeIndex(pd.to_datetime(out.index, errors="coerce"))
    out = out[~out.index.isna()]
    if out.index.tz is not None:
        out.index = out.index.tz_convert(None)
    return out.sort_index()


def _download_yahoo_close(symbol_map: dict[str, str], start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    symbols = list(symbol_map.keys())
    raw = yf.download(
        symbols,
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
        threads=True,
    )
    df = _parse_close(raw, symbols)
    if df.empty:
        return df
    return df.rename(columns={s: symbol_map[s] for s in df.columns if s in symbol_map})


def _download_spy_ohlc(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    raw = yf.download(
        "SPY",
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
        threads=True,
    )
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["open", "close"])
    if isinstance(raw.columns, pd.MultiIndex):
        # yfinance can emit multiindex even for single symbol in some versions.
        raw.columns = [c[0] for c in raw.columns]
    out = raw.rename(columns={"Open": "open", "Close": "close"})[["open", "close"]]
    out.index = pd.DatetimeIndex(pd.to_datetime(out.index, errors="coerce"))
    out = out[~out.index.isna()]
    if out.index.tz is not None:
        out.index = out.index.tz_convert(None)
    return out.sort_index()


def _zscore(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    mu = series.rolling(window=window, min_periods=min_periods).mean()
    sd = series.rolling(window=window, min_periods=min_periods).std()
    return (series - mu) / sd.replace(0, np.nan)


def build_features(
    calendar: pd.DatetimeIndex,
    fred: pd.DataFrame,
    yclose: pd.DataFrame,
    spy_ohlc: pd.DataFrame,
    cfg: LiquidityConfig,
) -> pd.DataFrame:
    out = pd.DataFrame(index=calendar)

    # FRED series alignment.
    for c in FRED_SERIES.values():
        s = pd.to_numeric(fred[c], errors="coerce") if c in fred.columns else pd.Series(dtype="float64")
        out[c] = s.reindex(calendar).ffill(limit=cfg.daily_ffill_limit).astype("float32")

    # H.4.1 weekly PIT lag for WALCL/WDTGAL only.
    for c in ("walcl_mm", "wdtgal_mm"):
        s = pd.to_numeric(fred[c], errors="coerce") if c in fred.columns else pd.Series(dtype="float64")
        if not s.empty:
            s = s.copy()
            s.index = (pd.DatetimeIndex(s.index) + pd.Timedelta(days=cfg.weekly_release_lag_days)).normalize()
        out[c] = s.reindex(calendar).ffill(limit=cfg.weekly_ffill_limit).astype("float32")

    # Yahoo close series.
    for c in YAHOO_CLOSE.values():
        s = pd.to_numeric(yclose[c], errors="coerce") if c in yclose.columns else pd.Series(dtype="float64")
        out[c] = s.reindex(calendar).ffill(limit=cfg.daily_ffill_limit).astype("float32")

    # SPY open/close for smart money flow.
    spy = spy_ohlc.reindex(calendar).ffill(limit=cfg.daily_ffill_limit)
    spy_open = pd.to_numeric(spy.get("open"), errors="coerce")
    spy_close = pd.to_numeric(spy.get("close"), errors="coerce")

    # Core FR-040 features.
    out["us_net_liquidity_mm"] = (
        out["walcl_mm"] - out["wdtgal_mm"] - (out["rrp_bn"] * 1000.0)
    ).astype("float32")
    roc20 = out["us_net_liquidity_mm"].pct_change(cfg.impulse_roc_days, fill_method=None)
    out["liquidity_impulse"] = _zscore(roc20, cfg.z_window, cfg.z_min_periods).fillna(0.0).astype("float32")

    out["repo_spread_bps"] = ((out["sofr_rate"] - out["effr_rate"]) * 100.0).fillna(0.0).astype("float32")
    out["repo_stress"] = out["repo_spread_bps"].gt(cfg.repo_stress_bps).fillna(False)

    dtb3_z = _zscore(out["dtb3_rate"], cfg.z_window, cfg.z_min_periods)
    vix_z = _zscore(out["vix_level"], cfg.z_window, cfg.z_min_periods)
    out["lrp_index"] = (dtb3_z - vix_z).ffill(limit=cfg.daily_ffill_limit).fillna(0.0).astype("float32")

    dxy_ret = out["dxy_px"].pct_change(fill_method=None)
    spx_ret = out["spx_px"].pct_change(fill_method=None)
    out["dollar_stress_corr"] = (
        dxy_ret.rolling(cfg.corr_window, min_periods=cfg.corr_min_periods).corr(spx_ret)
    ).ffill(limit=cfg.daily_ffill_limit).fillna(0.0).astype("float32")
    out["global_dollar_stress"] = out["dollar_stress_corr"].gt(cfg.dollar_stress_corr).fillna(False)

    intraday = (spy_close - spy_open).fillna(0.0)
    out["smart_money_flow"] = intraday.cumsum().astype("float32")

    spy_ret = spy_close.pct_change(fill_method=None)
    realized_vol_21d = spy_ret.rolling(window=21, min_periods=21).std() * np.sqrt(252.0) * 100.0
    out["realized_vol_21d"] = realized_vol_21d.astype("float32")
    out["vrp"] = (out["vix_level"] - out["realized_vol_21d"]).astype("float32")

    return out.reset_index().rename(columns={"index": "date"})


def run_build(start_year: int = 2000, end_date: str | None = None) -> dict:
    status = _new_status()
    cfg = LiquidityConfig()
    _log(status, "=" * 62)
    _log(status, "💧 Liquidity Layer Build (FR-040)")
    _log(status, "=" * 62)
    t0 = time.perf_counter()

    start_ts = pd.Timestamp(f"{int(start_year)}-01-01")
    end_ts = pd.Timestamp(end_date) if end_date else pd.Timestamp.utcnow().tz_localize(None).normalize()

    try:
        updater._acquire_update_lock()
    except TimeoutError as e:
        _warn(status, f"Build skipped: {e}")
        return status

    try:
        calendar = _load_trading_calendar(start_ts, end_ts)
        if len(calendar) == 0:
            _warn(status, "No trading calendar rows found.")
            return status
        t_calendar = time.perf_counter()
        _log(status, f"📅 Trading calendar rows: {len(calendar):,}")

        fred_df, fred_failed = _download_fred(FRED_SERIES, start_ts, end_ts)
        if fred_failed:
            _warn(status, "FRED series failed/empty: " + ", ".join(sorted(set(fred_failed))))
            _warn(status, "Aborting build due to missing critical series.")
            return status
        t_fred = time.perf_counter()
        _log(status, f"🏦 FRED columns fetched: {len(fred_df.columns)}")

        yclose = _download_yahoo_close(YAHOO_CLOSE, start_ts, end_ts)
        spy_ohlc = _download_spy_ohlc(start_ts, end_ts)
        t_yahoo = time.perf_counter()
        _log(status, f"📈 Yahoo close columns fetched: {len(yclose.columns)}")

        expected_close = sorted(set(YAHOO_CLOSE.values()))
        missing_close = sorted(set(expected_close) - set(yclose.columns))
        if yclose.empty or missing_close:
            _warn(
                status,
                "Aborting build: critical Yahoo close inputs missing "
                f"(missing={missing_close if missing_close else 'all'}).",
            )
            return status
        if yclose[expected_close].dropna(how="all").empty:
            _warn(status, "Aborting build: Yahoo close inputs are all-NaN in requested window.")
            return status

        if spy_ohlc.empty or not {"open", "close"}.issubset(spy_ohlc.columns):
            _warn(status, "Aborting build: SPY OHLC inputs missing (need open/close).")
            return status
        if spy_ohlc[["open", "close"]].dropna(how="all").empty:
            _warn(status, "Aborting build: SPY OHLC is all-NaN in requested window.")
            return status

        features = build_features(calendar, fred_df, yclose, spy_ohlc, cfg)
        if features.empty:
            _warn(status, "Built feature frame is empty.")
            return status
        t_features = time.perf_counter()

        updater.atomic_parquet_write(features, LIQUIDITY_PATH, index=False)
        t_write = time.perf_counter()

        status["success"] = True
        status["rows_written"] = int(len(features))
        _log(status, f"💾 liquidity_features.parquet rows: {status['rows_written']:,}")
        _log(
            status,
            "⏱ Stage timings (s): "
            f"calendar={t_calendar - t0:.3f}, "
            f"fred={t_fred - t_calendar:.3f}, "
            f"yahoo={t_yahoo - t_fred:.3f}, "
            f"features={t_features - t_yahoo:.3f}, "
            f"write={t_write - t_features:.3f}, "
            f"total={t_write - t0:.3f}",
        )
        _log(status, "✅ Liquidity build complete.")
        return status
    except Exception as e:
        _warn(status, f"Liquidity build failed unexpectedly: {e}")
        return status
    finally:
        updater._release_update_lock()


def main():
    parser = argparse.ArgumentParser(description="Build liquidity_features.parquet for FR-040")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()

    result = run_build(start_year=args.start_year, end_date=args.end_date)
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
