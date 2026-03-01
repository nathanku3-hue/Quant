"""
Terminal Zero — Macro Regime Loader (FR-035)

Builds PIT-safe macro regime features into one canonical artifact:
  data/processed/macro_features.parquet
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
PRICES_TRI_PATH = os.path.join(PROCESSED_DIR, "prices_tri.parquet")
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
LEGACY_MACRO_PATH = os.path.join(PROCESSED_DIR, "macro.parquet")
MACRO_FEATURES_PATH = os.path.join(PROCESSED_DIR, "macro_features.parquet")
MACRO_GATES_PATH = os.path.join(PROCESSED_DIR, "macro_gates.parquet")

YAHOO_SYMBOLS = {
    "^VIX": "vix_level",
    "^VIX3M": "vix3m_level",
    "^VVIX": "vvix_level",
    "DX-Y.NYB": "dxy_px",
    "^GSPC": "spx_px",
    "HYG": "hyg_px",
    "LQD": "lqd_px",
    "MTUM": "mtum_px",
    "SPY": "spy_close",
    "QQQ": "qqq_close",
    "BND": "bnd_px",
    "BTC-USD": "btc_px",
}

# FRED series IDs via CSV endpoint.
FRED_SERIES = {
    "SOFR": "sofr_rate",
    "DFF": "effr_rate",        # Effective Federal Funds Rate
    "T10Y2Y": "t10y2y_rate",   # 10Y-2Y spread
    "DFII10": "dfii10_rate",   # 10Y real rate
}


@dataclass(frozen=True)
class MacroThresholds:
    vvix_panic: float = 110.0
    collateral_crisis_bps10: float = 0.10
    credit_freeze_z: float = -2.0
    momentum_crowding_corr: float = 0.85
    dollar_squeeze_corr: float = 0.50
    sofr_start_cutoff: str = "2018-04-03"


@dataclass(frozen=True)
class MacroGateThresholds:
    vix_backwardation_ratio: float = 1.0
    slow_bleed_ret_21d_z: float = -1.0
    slow_bleed_drawdown_z: float = -0.5
    sharp_shock_ret_5d_z: float = -2.5
    sharp_shock_dd_5d_z: float = -2.5


def _new_status() -> dict:
    return {
        "log": [],
        "success": False,
        "rows_written": 0,
        "gates_rows_written": 0,
        "macro_features_path": MACRO_FEATURES_PATH,
        "macro_gates_path": MACRO_GATES_PATH,
        "start_date": None,
        "end_date": None,
        "warnings": [],
    }


def _log(status: dict, msg: str):
    print(msg)
    status["log"].append(msg)


def _warn(status: dict, msg: str):
    _log(status, f"⚠ {msg}")
    status["warnings"].append(msg)


def _sql_escape_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _load_trading_calendar(start_date: pd.Timestamp) -> pd.DatetimeIndex:
    if not os.path.exists(PRICES_PATH) and not os.path.exists(PRICES_TRI_PATH):
        raise FileNotFoundError(f"Missing prices parquet: {PRICES_PATH}")

    con = duckdb.connect()
    try:
        start_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
        if os.path.exists(PRICES_TRI_PATH):
            q = f"""
                SELECT DISTINCT CAST(date AS DATE) AS date
                FROM '{_sql_escape_path(PRICES_TRI_PATH)}'
                WHERE CAST(date AS DATE) >= DATE '{start_str}'
                ORDER BY date
            """
        elif os.path.exists(PATCH_PATH):
            q = f"""
                SELECT DISTINCT CAST(date AS DATE) AS date
                FROM (
                    SELECT date FROM '{_sql_escape_path(PRICES_PATH)}'
                    WHERE CAST(date AS DATE) >= DATE '{start_str}'
                    UNION ALL
                    SELECT date FROM '{_sql_escape_path(PATCH_PATH)}'
                    WHERE CAST(date AS DATE) >= DATE '{start_str}'
                )
                ORDER BY date
            """
        else:
            q = f"""
                SELECT DISTINCT CAST(date AS DATE) AS date
                FROM '{_sql_escape_path(PRICES_PATH)}'
                WHERE CAST(date AS DATE) >= DATE '{start_str}'
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


def _read_csv_url_with_retry(
    url: str,
    retries: int = 3,
    timeout_sec: int = 15,
    backoff_sec: float = 0.75,
) -> pd.DataFrame:
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
            time.sleep(backoff_sec * attempt)
    raise RuntimeError(f"failed to fetch url after {retries} attempts: {url}") from last_err


def _parse_yf_close(raw: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    # Multi-symbol path.
    if isinstance(raw.columns, pd.MultiIndex):
        close_layer = None
        for attr in ("Adj Close", "Close"):
            if attr in raw.columns.get_level_values(0):
                close_layer = raw[attr]
                break
        if close_layer is None:
            return pd.DataFrame()
        out = close_layer.copy()
    else:
        # Single-symbol path.
        col = "Adj Close" if "Adj Close" in raw.columns else "Close" if "Close" in raw.columns else None
        if col is None:
            return pd.DataFrame()
        out = raw[[col]].copy()
        out.columns = [symbols[0]]

    out.index = pd.DatetimeIndex(pd.to_datetime(out.index, errors="coerce"))
    out = out[~out.index.isna()]
    if out.index.tz is not None:
        out.index = out.index.tz_convert(None)
    return out.sort_index()


def _download_yahoo(symbol_map: dict[str, str], start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    symbols = list(symbol_map.keys())
    if not symbols:
        return pd.DataFrame()

    raw = yf.download(
        symbols,
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        progress=False,
        auto_adjust=False,
        threads=True,
    )
    close_df = _parse_yf_close(raw, symbols)
    if close_df.empty:
        return pd.DataFrame()

    # Standardize columns to target names.
    ren = {sym: symbol_map[sym] for sym in close_df.columns if sym in symbol_map}
    close_df = close_df.rename(columns=ren)
    return close_df


def _download_fred_series(series_id: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.Series:
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={start_date.strftime('%Y-%m-%d')}&coed={end_date.strftime('%Y-%m-%d')}"
    )
    df = _read_csv_url_with_retry(url)
    date_col = "DATE" if "DATE" in df.columns else "observation_date" if "observation_date" in df.columns else None
    if df.empty or date_col is None or series_id not in df.columns:
        return pd.Series(dtype="float64")

    s = pd.to_numeric(df[series_id], errors="coerce")
    idx = pd.to_datetime(df[date_col], errors="coerce")
    out = pd.Series(s.values, index=idx, name=series_id)
    out = out[~out.index.isna()]
    out = out.sort_index()
    out = out[(out.index >= start_date) & (out.index <= end_date)]
    return out


def _download_fred(
    series_map: dict[str, str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> tuple[pd.DataFrame, list[str]]:
    cols: dict[str, pd.Series] = {}
    failed: list[str] = []
    if not series_map:
        return pd.DataFrame(), failed

    workers = min(4, len(series_map))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fut_to_sid_col = {
            pool.submit(_download_fred_series, sid, start_date, end_date): (sid, col)
            for sid, col in series_map.items()
        }
        for fut in as_completed(fut_to_sid_col):
            sid, col = fut_to_sid_col[fut]
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


def _rolling_zscore(series: pd.Series, window: int = 63, min_periods: int = 20) -> pd.Series:
    mu = series.rolling(window=window, min_periods=min_periods).mean()
    sigma = series.rolling(window=window, min_periods=min_periods).std()
    return (series - mu) / sigma.replace(0, np.nan)


def _rolling_pct_rank(series: pd.Series, window: int = 252, min_periods: int = 63) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    try:
        # Vectorized C-level path: percentile rank of the latest value in each rolling window.
        return s.rolling(window=window, min_periods=min_periods).rank(pct=True, method="average")
    except Exception:
        # Fallback for environments lacking rolling.rank support.
        def rank_last(x: np.ndarray) -> float:
            if len(x) == 0 or np.isnan(x[-1]):
                return np.nan
            return pd.Series(x).rank(pct=True).iloc[-1]

        return s.rolling(window=window, min_periods=min_periods).apply(rank_last, raw=True)


def _adaptive_zscore(
    series: pd.Series,
    mean_span: int = 20,
    vol_span: int = 63,
    min_periods: int = 20,
) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mu = s.ewm(span=mean_span, adjust=False, min_periods=min_periods).mean()
    sigma = s.ewm(span=vol_span, adjust=False, min_periods=min_periods).std()
    return (s - mu) / sigma.replace(0, np.nan)


def _month_end_last3_flags(index: pd.DatetimeIndex) -> pd.Series:
    if len(index) == 0:
        return pd.Series(dtype=bool)
    idx = pd.DatetimeIndex(index)
    per = idx.to_period("M")
    pos = pd.Series(1, index=idx).groupby(per).cumsum()
    size = pd.Series(1, index=idx).groupby(per).transform("sum")
    days_left = size - pos + 1
    return (days_left <= 3).astype(bool)


def _coalesce(base: pd.Series, fallback: pd.Series) -> pd.Series:
    if base is None or base.empty:
        return fallback
    if fallback is None or fallback.empty:
        return base
    idx = base.index.union(fallback.index)
    b = base.reindex(idx).sort_index()
    f = fallback.reindex(idx).sort_index()
    return b.where(b.notna(), f)


def _atomic_pair_parquet_write(
    left_df: pd.DataFrame,
    left_path: str,
    right_df: pd.DataFrame,
    right_path: str,
    index: bool = False,
) -> None:
    """
    Best-effort paired publish: both artifacts swap together or roll back.
    """
    stamp = f"{os.getpid()}.{int(time.time() * 1000)}"
    left_tmp = f"{left_path}.{stamp}.tmp"
    right_tmp = f"{right_path}.{stamp}.tmp"
    left_bak = f"{left_path}.{stamp}.bak"
    right_bak = f"{right_path}.{stamp}.bak"

    left_swapped = False
    right_swapped = False
    left_backed_up = False
    right_backed_up = False
    try:
        left_df.to_parquet(left_tmp, index=index)
        right_df.to_parquet(right_tmp, index=index)

        if os.path.exists(left_path):
            os.replace(left_path, left_bak)
            left_backed_up = True
        if os.path.exists(right_path):
            os.replace(right_path, right_bak)
            right_backed_up = True

        os.replace(left_tmp, left_path)
        left_swapped = True
        os.replace(right_tmp, right_path)
        right_swapped = True
    except Exception:
        try:
            if left_swapped and os.path.exists(left_path):
                os.remove(left_path)
        except OSError:
            pass
        try:
            if right_swapped and os.path.exists(right_path):
                os.remove(right_path)
        except OSError:
            pass

        if left_backed_up and os.path.exists(left_bak):
            os.replace(left_bak, left_path)
        if right_backed_up and os.path.exists(right_bak):
            os.replace(right_bak, right_path)
        raise
    finally:
        for p in (left_tmp, right_tmp, left_bak, right_bak):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def _load_legacy_macro() -> pd.DataFrame:
    if not os.path.exists(LEGACY_MACRO_PATH):
        return pd.DataFrame(columns=["spy_close", "vix_proxy"])
    try:
        m = pd.read_parquet(LEGACY_MACRO_PATH)
        if m.empty:
            return pd.DataFrame(columns=["spy_close", "vix_proxy"])
        m["date"] = pd.to_datetime(m["date"], errors="coerce")
        m = m.dropna(subset=["date"]).set_index("date").sort_index()
        for c in ("spy_close", "vix_proxy"):
            if c in m.columns:
                m[c] = pd.to_numeric(m[c], errors="coerce")
            else:
                m[c] = np.nan
        return m[["spy_close", "vix_proxy"]]
    except Exception:
        return pd.DataFrame(columns=["spy_close", "vix_proxy"])


def build_macro_features(
    calendar: pd.DatetimeIndex,
    yahoo_df: pd.DataFrame,
    fred_df: pd.DataFrame,
    thresholds: MacroThresholds,
) -> pd.DataFrame:
    if len(calendar) == 0:
        return pd.DataFrame(columns=["date"])

    out = pd.DataFrame(index=calendar)

    # Fast market data (same-day allowed).
    for col in YAHOO_SYMBOLS.values():
        s = yahoo_df[col] if col in yahoo_df.columns else pd.Series(dtype="float64")
        s = pd.to_numeric(s, errors="coerce")
        s = s.reindex(calendar).ffill(limit=3)
        out[col] = s.astype("float32")

    # Slow macro data (conservative T+1 shift).
    for col in FRED_SERIES.values():
        s = fred_df[col] if col in fred_df.columns else pd.Series(dtype="float64")
        s = pd.to_numeric(s, errors="coerce")
        s = s.reindex(calendar).ffill(limit=3).shift(1)
        out[col] = s.astype("float32")

    # Use legacy fallback for core SPY/VIX if external fetch is sparse.
    legacy = _load_legacy_macro().reindex(calendar)
    out["spy_close"] = _coalesce(out["spy_close"], legacy["spy_close"]).astype("float32")
    spy_ret = out["spy_close"].pct_change(fill_method=None)
    vix_proxy_new = (spy_ret.rolling(20, min_periods=20).std() * np.sqrt(252) * 100.0).astype("float32")
    out["vix_proxy"] = _coalesce(vix_proxy_new, legacy["vix_proxy"]).astype("float32")

    gate_thresholds = MacroGateThresholds()

    # Derived stress features.
    out["vix_vix3m_spread"] = (out["vix_level"] - out["vix3m_level"]).astype("float32")
    out["vix_term_ratio"] = (out["vix_level"] / out["vix3m_level"].replace(0, np.nan)).astype("float32")
    out["vix_backwardation"] = out["vix_term_ratio"].gt(gate_thresholds.vix_backwardation_ratio).fillna(False)
    out["liquidity_air_pocket"] = (
        out["vix_vix3m_spread"].gt(0.0) & out["vvix_level"].gt(thresholds.vvix_panic)
    ).fillna(False)

    qqq_ret_1d = out["qqq_close"].pct_change(fill_method=None)
    qqq_ret_5d = out["qqq_close"].pct_change(5, fill_method=None)
    qqq_ret_21d = out["qqq_close"].pct_change(21, fill_method=None)
    qqq_peak_252d = out["qqq_close"].rolling(252, min_periods=252).max()
    qqq_drawdown_252d = out["qqq_close"] / qqq_peak_252d - 1.0
    qqq_drawdown_5d_delta = qqq_drawdown_252d.diff(5)
    qqq_drawdown_21d_delta = qqq_drawdown_252d.diff(21)
    out["qqq_ret_1d"] = qqq_ret_1d.astype("float32")
    out["qqq_ret_5d"] = qqq_ret_5d.astype("float32")
    out["qqq_ret_21d"] = qqq_ret_21d.astype("float32")
    out["qqq_peak_252d"] = qqq_peak_252d.astype("float32")
    out["qqq_drawdown_252d"] = qqq_drawdown_252d.astype("float32")
    out["qqq_sma50"] = out["qqq_close"].rolling(50, min_periods=50).mean().astype("float32")
    out["qqq_ma200"] = out["qqq_close"].rolling(200, min_periods=200).mean().astype("float32")
    out["qqq_ma200_trend_gate"] = out["qqq_close"].ge(out["qqq_ma200"]).fillna(False)
    out["qqq_ret_1d_z_adapt"] = _adaptive_zscore(qqq_ret_1d, mean_span=20, vol_span=63, min_periods=20).astype("float32")
    out["qqq_ret_5d_z_adapt"] = (
        _adaptive_zscore(qqq_ret_5d, mean_span=20, vol_span=126, min_periods=40).astype("float32")
    )
    out["qqq_ret_21d_z_adapt"] = (
        _rolling_zscore(qqq_ret_21d, window=252, min_periods=63).astype("float32")
    )
    out["qqq_drawdown_252d_z_adapt"] = (
        _rolling_zscore(qqq_drawdown_252d, window=252, min_periods=63).astype("float32")
    )
    out["qqq_drawdown_5d_delta"] = qqq_drawdown_5d_delta.astype("float32")
    out["qqq_drawdown_21d_delta"] = qqq_drawdown_21d_delta.astype("float32")
    out["qqq_drawdown_5d_delta_z_adapt"] = (
        _adaptive_zscore(qqq_drawdown_5d_delta, mean_span=20, vol_span=126, min_periods=40).astype("float32")
    )
    out["qqq_drawdown_21d_delta_z_adapt"] = (
        _adaptive_zscore(qqq_drawdown_21d_delta, mean_span=20, vol_span=126, min_periods=40).astype("float32")
    )
    out["slow_bleed_label"] = (
        out["qqq_ret_21d_z_adapt"].le(gate_thresholds.slow_bleed_ret_21d_z)
        & out["qqq_drawdown_252d_z_adapt"].le(gate_thresholds.slow_bleed_drawdown_z)
    ).fillna(False)
    out["sharp_shock_label"] = (
        out["qqq_ret_5d_z_adapt"].le(gate_thresholds.sharp_shock_ret_5d_z)
        | out["qqq_drawdown_5d_delta_z_adapt"].le(gate_thresholds.sharp_shock_dd_5d_z)
    ).fillna(False)

    dxy_ret = out["dxy_px"].pct_change(fill_method=None)
    spx_ret = out["spx_px"].pct_change(fill_method=None)
    out["dxy_spx_corr_20d"] = dxy_ret.rolling(20, min_periods=20).corr(spx_ret).astype("float32")
    out["dollar_squeeze"] = out["dxy_spx_corr_20d"].gt(thresholds.dollar_squeeze_corr).fillna(False)

    out["sofr_effr_spread"] = (out["sofr_rate"] - out["effr_rate"]).astype("float32")
    sofr_cut = pd.Timestamp(thresholds.sofr_start_cutoff)
    pre_sofr = out.index < sofr_cut
    out.loc[pre_sofr & out["sofr_effr_spread"].isna(), "sofr_effr_spread"] = 0.0
    out["collateral_crisis"] = out["sofr_effr_spread"].gt(thresholds.collateral_crisis_bps10).fillna(False)

    out["hyg_lqd_ratio"] = (out["hyg_px"] / out["lqd_px"]).astype("float32")
    out["hyg_lqd_ratio_z63"] = _rolling_zscore(out["hyg_lqd_ratio"], window=63, min_periods=20).astype("float32")
    out["credit_freeze"] = out["hyg_lqd_ratio_z63"].lt(thresholds.credit_freeze_z).fillna(False)

    mtum_ret = out["mtum_px"].pct_change(fill_method=None)
    spy_ret = out["spy_close"].pct_change(fill_method=None)
    out["mtum_spy_corr_60d"] = mtum_ret.rolling(60, min_periods=40).corr(spy_ret).astype("float32")
    out["momentum_crowding"] = out["mtum_spy_corr_60d"].gt(thresholds.momentum_crowding_corr).fillna(False)

    out["vvix_pct_252"] = _rolling_pct_rank(out["vvix_level"], window=252, min_periods=63).astype("float32")
    out["repo_spread_diff_1d"] = out["sofr_effr_spread"].diff().astype("float32")

    out["month_end_rebalance_flag"] = _month_end_last3_flags(out.index).astype(bool)
    per = out.index.to_period("M")
    spy_mtd = out["spy_close"] / out["spy_close"].groupby(per).transform("first") - 1.0
    bnd_mtd = out["bnd_px"] / out["bnd_px"].groupby(per).transform("first") - 1.0
    out["month_end_rebalance_direction"] = np.sign(spy_mtd - bnd_mtd).astype("float32")

    stress_cols = [
        "liquidity_air_pocket",
        "dollar_squeeze",
        "collateral_crisis",
        "credit_freeze",
        "momentum_crowding",
    ]
    out["stress_count"] = out[stress_cols].astype(int).sum(axis=1).astype("int8")
    out["regime_scalar"] = np.select(
        [
            out["stress_count"] >= 3,
            out["stress_count"] == 2,
            out["stress_count"] == 1,
        ],
        [0.0, 0.5, 0.7],
        default=1.0,
    ).astype("float32")

    out = out.reset_index().rename(columns={"index": "date"})
    return out


def build_macro_gates(macro_features: pd.DataFrame) -> pd.DataFrame:
    gate_cols = [
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
    ]
    if macro_features is None or macro_features.empty:
        return pd.DataFrame(columns=gate_cols)
    if "date" not in macro_features.columns:
        raise ValueError("macro_features must include date column")

    df = macro_features.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
    df = df.reset_index(drop=True)
    if df.empty:
        return pd.DataFrame(columns=gate_cols)

    idx = df.index
    drawdown = pd.to_numeric(df.get("qqq_drawdown_252d"), errors="coerce") if "qqq_drawdown_252d" in df else pd.Series(
        np.nan, index=idx
    )
    trend_gate = (
        df.get("qqq_ma200_trend_gate", pd.Series(True, index=idx))
        .astype("boolean")
        .fillna(True)
        .astype(bool)
    )
    slow_bleed = (
        df.get("slow_bleed_label", pd.Series(False, index=idx))
        .astype("boolean")
        .fillna(False)
        .astype(bool)
    )
    sharp_shock = (
        df.get("sharp_shock_label", pd.Series(False, index=idx))
        .astype("boolean")
        .fillna(False)
        .astype(bool)
    )
    if "vix_term_ratio" in df:
        term_ratio = pd.to_numeric(df["vix_term_ratio"], errors="coerce")
    else:
        vix = pd.to_numeric(df.get("vix_level", np.nan), errors="coerce")
        vix3m = pd.to_numeric(df.get("vix3m_level", np.nan), errors="coerce")
        term_ratio = vix / vix3m.replace(0, np.nan)
    vix_backwardation = (
        df.get("vix_backwardation", term_ratio.gt(1.0))
        .astype("boolean")
        .fillna(False)
        .astype(bool)
    )
    qqq_ret_5d_z = pd.to_numeric(df.get("qqq_ret_5d_z_adapt"), errors="coerce")
    qqq_ret_21d_z = pd.to_numeric(df.get("qqq_ret_21d_z_adapt"), errors="coerce")
    qqq_drawdown_z = pd.to_numeric(df.get("qqq_drawdown_252d_z_adapt"), errors="coerce")
    qqq_close = (
        pd.to_numeric(df["qqq_close"], errors="coerce")
        if "qqq_close" in df
        else pd.Series(np.nan, index=idx, dtype=float)
    )
    qqq_sma50 = (
        pd.to_numeric(df["qqq_sma50"], errors="coerce")
        if "qqq_sma50" in df
        else pd.Series(np.nan, index=idx, dtype=float)
    )
    if qqq_sma50.notna().sum() == 0:
        qqq_sma50 = qqq_close.rolling(50, min_periods=50).mean()
    below_ma200 = ~trend_gate

    red_state = sharp_shock | vix_backwardation
    amber_state = (~red_state) & (slow_bleed | below_ma200)

    state = np.select([red_state, amber_state], ["RED", "AMBER"], default="GREEN")
    scalar = np.select([red_state, amber_state], [0.0, 0.5], default=1.0).astype("float32")
    cash_buffer = np.select([red_state, amber_state], [0.50, 0.25], default=0.0).astype("float32")
    momentum_entry = (
        (state == "GREEN")
        & (~vix_backwardation.to_numpy())
        & trend_gate.to_numpy()
        & (~slow_bleed.to_numpy())
        & (~sharp_shock.to_numpy())
    )

    reason_masks: list[tuple[str, pd.Series]] = [
        ("sharp_shock", sharp_shock),
        ("vix_backwardation", vix_backwardation),
        ("slow_bleed", slow_bleed),
        ("below_ma200", below_ma200),
    ]
    reasons = pd.Series("", index=idx, dtype="object")
    for label, mask in reason_masks:
        m = mask.to_numpy(dtype=bool, na_value=False)
        cur = reasons.to_numpy(dtype=object)
        reasons = pd.Series(
            np.where(m, np.where(cur == "", label, cur + "|" + label), cur),
            index=idx,
        )
    reasons = reasons.where(reasons != "", "risk_normalized")

    out = pd.DataFrame(
        {
            "date": df["date"],
            "state": state.astype(str),
            "scalar": scalar,
            "cash_buffer": cash_buffer,
            "momentum_entry": momentum_entry.astype(bool),
            "reasons": reasons.astype(str),
            "qqq_drawdown_252d": drawdown.astype("float32"),
            "qqq_sma50": qqq_sma50.astype("float32"),
            "qqq_ma200_trend_gate": trend_gate.astype(bool),
            "slow_bleed": slow_bleed.astype(bool),
            "sharp_shock": sharp_shock.astype(bool),
            "qqq_ret_5d_z_adapt": qqq_ret_5d_z.astype("float32"),
            "qqq_ret_21d_z_adapt": qqq_ret_21d_z.astype("float32"),
            "qqq_drawdown_252d_z_adapt": qqq_drawdown_z.astype("float32"),
            "vix_term_ratio": pd.to_numeric(term_ratio, errors="coerce").astype("float32"),
            "vix_backwardation": vix_backwardation.astype(bool),
        }
    )
    return out[gate_cols]


def run_build(
    start_year: int = 2000,
    end_date: str | None = None,
) -> dict:
    status = _new_status()
    _log(status, "=" * 62)
    _log(status, "🧠 Macro Layer Build (FR-035)")
    _log(status, "=" * 62)
    t0 = time.perf_counter()

    start_ts = pd.Timestamp(f"{int(start_year)}-01-01")
    end_ts = pd.Timestamp(end_date) if end_date else pd.Timestamp.utcnow().tz_localize(None).normalize()
    status["start_date"] = str(start_ts.date())
    status["end_date"] = str(end_ts.date())

    try:
        updater._acquire_update_lock()
    except TimeoutError as e:
        _warn(status, f"Build skipped: {e}")
        return status

    try:
        calendar = _load_trading_calendar(start_ts)
        calendar = pd.DatetimeIndex(calendar)
        calendar = calendar[calendar <= end_ts]
        if len(calendar) == 0:
            _warn(status, "No trading calendar rows found.")
            return status
        t_calendar = time.perf_counter()
        _log(status, f"📅 Trading calendar rows: {len(calendar):,} ({calendar.min().date()} -> {calendar.max().date()})")

        try:
            yahoo_df = _download_yahoo(YAHOO_SYMBOLS, start_ts, end_ts)
            _log(status, f"📈 Yahoo columns fetched: {len(yahoo_df.columns)}")
        except Exception as e:
            _warn(status, f"Yahoo download failed: {e}")
            yahoo_df = pd.DataFrame()
        t_yahoo = time.perf_counter()

        try:
            fred_df, fred_failed = _download_fred(FRED_SERIES, start_ts, end_ts)
            _log(status, f"🏦 FRED columns fetched: {len(fred_df.columns)}")
            if fred_failed:
                _warn(status, "FRED series failed/empty: " + ", ".join(sorted(set(fred_failed))))
                # Do not silently emit partial macro regime features.
                _warn(status, "Aborting macro build due to missing critical FRED series.")
                return status
        except Exception as e:
            _warn(status, f"FRED download failed: {e}")
            fred_df = pd.DataFrame()
        t_fred = time.perf_counter()

        feats = build_macro_features(
            calendar=calendar,
            yahoo_df=yahoo_df,
            fred_df=fred_df,
            thresholds=MacroThresholds(),
        )
        if feats.empty:
            _warn(status, "Feature frame is empty.")
            return status
        t_features = time.perf_counter()

        gates = build_macro_gates(feats)
        if gates.empty:
            _warn(status, "Macro gates frame is empty.")
            return status
        t_gates = time.perf_counter()

        # Safety check for post-2020 null density on critical columns.
        post_2020 = feats[pd.to_datetime(feats["date"]) >= pd.Timestamp("2020-01-01")]
        crit = ["spy_close", "vix_proxy", "vix_level", "sofr_effr_spread", "hyg_lqd_ratio", "mtum_spy_corr_60d"]
        if not post_2020.empty:
            null_rates = post_2020[crit].isna().mean()
            bad = null_rates[null_rates > 0.05]
            if not bad.empty:
                _warn(status, "Post-2020 null-rate > 5%: " + ", ".join([f"{k}={v:.1%}" for k, v in bad.items()]))

        _atomic_pair_parquet_write(
            left_df=feats,
            left_path=MACRO_FEATURES_PATH,
            right_df=gates,
            right_path=MACRO_GATES_PATH,
            index=False,
        )
        t_write = time.perf_counter()
        status["rows_written"] = int(len(feats))
        status["gates_rows_written"] = int(len(gates))
        status["macro_features_path"] = MACRO_FEATURES_PATH
        status["macro_gates_path"] = MACRO_GATES_PATH
        status["success"] = True
        _log(status, f"💾 macro_features.parquet rows: {status['rows_written']:,}")
        _log(status, f"💾 macro_gates.parquet rows: {status['gates_rows_written']:,}")
        _log(
            status,
            "⏱ Stage timings (s): "
            f"calendar={t_calendar - t0:.3f}, "
            f"yahoo={t_yahoo - t_calendar:.3f}, "
            f"fred={t_fred - t_yahoo:.3f}, "
            f"features={t_features - t_fred:.3f}, "
            f"gates={t_gates - t_features:.3f}, "
            f"write={t_write - t_gates:.3f}, "
            f"total={t_write - t0:.3f}",
        )
        _log(status, "✅ Macro build complete.")
        _log(status, "=" * 62)
        return status
    except Exception as e:
        _warn(status, f"Macro build failed unexpectedly: {e}")
        return status
    finally:
        updater._release_update_lock()


def main():
    parser = argparse.ArgumentParser(description="Build macro_features.parquet for FR-035")
    parser.add_argument("--start-year", type=int, default=2000, help="Start year for build window")
    parser.add_argument("--end-date", default=None, help="Optional end date (YYYY-MM-DD)")
    args = parser.parse_args()

    result = run_build(start_year=args.start_year, end_date=args.end_date)
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
