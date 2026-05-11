"""
Data Orchestrator: Unified Data Loading Abstraction Layer

Provides a unified interface for loading dashboard data, supporting both:
- Live mode: yfinance fetching (dashboard.py legacy path)
- Historical mode: processed parquet files (app.py institutional-grade path)

Enables gradual migration from yfinance to parquet-based data pipeline.
"""

from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from data.dashboard_data_loader import load_dashboard_data
from data.providers.registry import build_market_data_provider


BACKTEST_RESULTS_PATH = Path("data/backtest_results.json")
OPTIMIZER_LIVE_OVERLAY_CACHE_DIR = Path("data/runtime_cache/optimizer_live_overlay")
OPTIMIZER_LIVE_OVERLAY_CACHE_VERSION = 1
UNIFIED_DATA_CACHE_FILE_NAMES = (
    "prices_tri.parquet",
    "prices.parquet",
    "yahoo_patch.parquet",
    "macro_features_tri.parquet",
    "macro_features.parquet",
    "macro.parquet",
    "liquidity_features.parquet",
    "universe_r3000_daily.parquet",
    "tickers.parquet",
    "fundamentals.parquet",
    "fundamentals_snapshot.parquet",
    "earnings_calendar.parquet",
)
UNIFIED_DATA_STATIC_CACHE_FILE_NAMES = (
    "sector_map.parquet",
)
_SCALE_CACHE_MAXSIZE = 64
_scaled_overlay_cache: OrderedDict[str, pd.DataFrame] = OrderedDict()
_scaled_overlay_cache_lock = threading.Lock()
_overlay_inflight_lock = threading.Lock()
_overlay_inflight_keys: set[str] = set()
_overlay_refresh_executor: ThreadPoolExecutor | None = None


@dataclass
class UnifiedDataPackage:
    """
    Unified data structure for dashboard consumption.

    All dashboards consume this standardized format regardless of underlying source.
    """
    prices: pd.DataFrame  # Wide format: date index, ticker columns
    returns: pd.DataFrame  # Wide format: date index, ticker columns
    macro: pd.DataFrame  # Date index with macro/liquidity/regime features
    ticker_map: dict[int, str]  # permno → ticker mapping
    sector_map: dict[int, str] | None  # permno → sector mapping (optional)
    fundamentals: dict[str, Any] | None  # Fundamentals dict (optional)
    metadata: dict[str, Any]  # Metadata about data source, staleness, etc.


def _file_signature(path: Path) -> tuple[str, int | None, int | None]:
    resolved = path.resolve(strict=False)
    try:
        stat = resolved.stat()
    except OSError:
        return (str(resolved), None, None)
    return (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))


def build_unified_data_cache_signature(
    *,
    processed_dir: str | Path = "./data/processed",
    static_dir: str | Path = "./data/static",
) -> tuple[tuple[str, int | None, int | None], ...]:
    """
    Build a lightweight signature for dashboard-level unified data caching.

    Streamlit reruns should reuse the expensive DuckDB/parquet wide-frame load,
    but updates to any source parquet file must invalidate that cached package.
    """
    processed_root = Path(processed_dir)
    static_root = Path(static_dir)
    paths = [processed_root / name for name in UNIFIED_DATA_CACHE_FILE_NAMES]
    paths.extend(static_root / name for name in UNIFIED_DATA_STATIC_CACHE_FILE_NAMES)
    return tuple(_file_signature(path) for path in paths)


def clean_price_frame(prices: pd.DataFrame) -> pd.DataFrame:
    """Normalize a wide price frame for optimizer/runtime display paths."""
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        return pd.DataFrame()
    cleaned = prices.apply(pd.to_numeric, errors="coerce")
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    cleaned = cleaned.dropna(how="all")
    if cleaned.empty:
        return cleaned
    idx = pd.to_datetime(cleaned.index, errors="coerce")
    valid_idx = ~pd.isna(idx)
    cleaned = cleaned.loc[valid_idx]
    cleaned.index = pd.DatetimeIndex(idx[valid_idx])
    if cleaned.index.tz is not None:
        cleaned.index = cleaned.index.tz_localize(None)
    cleaned = cleaned.sort_index()
    return cleaned[~cleaned.index.duplicated(keep="last")]


def extract_close_prices(raw: pd.DataFrame, tickers: tuple[str, ...]) -> pd.DataFrame:
    """Extract adjusted-close-compatible columns from provider bar output."""
    if not isinstance(raw, pd.DataFrame) or raw.empty:
        return pd.DataFrame()

    close = pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        levels_0 = set(raw.columns.get_level_values(0))
        levels_1 = set(raw.columns.get_level_values(1))
        if "Adj Close" in levels_0:
            close = raw["Adj Close"]
        elif "Close" in levels_0:
            close = raw["Close"]
        elif "Adj Close" in levels_1:
            close = raw.xs("Adj Close", axis=1, level=1)
        elif "Close" in levels_1:
            close = raw.xs("Close", axis=1, level=1)
    elif "Adj Close" in raw.columns:
        close = raw["Adj Close"]
    elif "Close" in raw.columns:
        close = raw["Close"]

    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0] if tickers else "Close")
    if not isinstance(close, pd.DataFrame) or close.empty:
        return pd.DataFrame()
    close.columns = [str(col).upper() for col in close.columns]
    return clean_price_frame(close)


def _overlay_executor() -> ThreadPoolExecutor:
    global _overlay_refresh_executor
    if _overlay_refresh_executor is None:
        _overlay_refresh_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="optimizer-overlay",
        )
    return _overlay_refresh_executor


def _normalize_recent_close_tickers(tickers: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({str(ticker).upper().strip() for ticker in tickers if str(ticker).strip()}))


def _overlay_cache_key(tickers: tuple[str, ...], start_iso: str) -> str:
    payload = json.dumps(
        {
            "version": OPTIMIZER_LIVE_OVERLAY_CACHE_VERSION,
            "tickers": list(tickers),
            "start_iso": str(start_iso),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _overlay_cache_path(
    tickers: tuple[str, ...],
    start_iso: str,
    cache_dir: str | Path,
) -> Path:
    return Path(cache_dir) / f"{_overlay_cache_key(tickers, start_iso)}.parquet"


def _read_overlay_cache(
    cache_path: Path,
    cache_ttl_seconds: int,
) -> tuple[pd.DataFrame, bool]:
    if not cache_path.exists():
        return pd.DataFrame(), False
    try:
        cached = clean_price_frame(pd.read_parquet(cache_path))
        age_seconds = time.time() - cache_path.stat().st_mtime
        if age_seconds < 0:
            return cached, False
        return cached, age_seconds <= max(int(cache_ttl_seconds), 1)
    except Exception:
        return pd.DataFrame(), False


def _write_overlay_cache_atomic(cache_path: Path, prices: pd.DataFrame) -> None:
    cleaned = clean_price_frame(prices)
    if cleaned.empty:
        return
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_name(
        f".{cache_path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        cleaned.to_parquet(tmp_path)
        os.replace(tmp_path, cache_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _fetch_recent_close_prices(
    tickers: tuple[str, ...],
    start_iso: str,
) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()
    provider = build_market_data_provider("yahoo")
    raw = provider.download_daily_bars(
        list(tickers),
        start=start_iso,
        threads=True,
    )
    return extract_close_prices(raw, tickers)


def _refresh_recent_close_prices_cache(
    tickers: tuple[str, ...],
    start_iso: str,
    cache_path: Path,
    cache_key: str,
) -> pd.DataFrame:
    try:
        prices = _fetch_recent_close_prices(tickers, start_iso)
        _write_overlay_cache_atomic(cache_path, prices)
        return prices
    except Exception:
        return pd.DataFrame()
    finally:
        with _overlay_inflight_lock:
            _overlay_inflight_keys.discard(cache_key)


def _schedule_overlay_refresh(
    tickers: tuple[str, ...],
    start_iso: str,
    cache_path: Path,
    cache_key: str,
) -> None:
    with _overlay_inflight_lock:
        if cache_key in _overlay_inflight_keys:
            return
        _overlay_inflight_keys.add(cache_key)
    try:
        _overlay_executor().submit(
            _refresh_recent_close_prices_cache,
            tickers,
            start_iso,
            cache_path,
            cache_key,
        )
    except Exception:
        with _overlay_inflight_lock:
            _overlay_inflight_keys.discard(cache_key)


def download_recent_close_prices(
    tickers: tuple[str, ...],
    start_iso: str,
    *,
    cache_ttl_seconds: int = 900,
    cache_dir: str | Path = OPTIMIZER_LIVE_OVERLAY_CACHE_DIR,
    schedule_background: bool = True,
) -> pd.DataFrame:
    """
    Load recent non-canonical display prices from cache and refresh asynchronously.

    When `schedule_background` is true this intentionally returns any stale
    cache immediately and schedules a refresh, falling back to local prices when
    no cache exists. The overlay is display freshness only.
    """
    normalized = _normalize_recent_close_tickers(tickers)
    if not normalized:
        return pd.DataFrame()
    start_iso = str(start_iso)
    cache_path = _overlay_cache_path(normalized, start_iso, cache_dir)
    cache_key = _overlay_cache_key(normalized, start_iso)
    cached, is_fresh = _read_overlay_cache(cache_path, cache_ttl_seconds)
    if is_fresh:
        return cached.copy()

    if schedule_background:
        _schedule_overlay_refresh(normalized, start_iso, cache_path, cache_key)
        return cached.copy()

    fresh = _fetch_recent_close_prices(normalized, start_iso)
    _write_overlay_cache_atomic(cache_path, fresh)
    return fresh.copy()


def _frame_digest(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        digest.update(b"empty")
        return digest.hexdigest()
    digest.update(str(frame.shape).encode("utf-8"))
    digest.update("|".join(str(col) for col in frame.columns).encode("utf-8"))
    row_hashes = pd.util.hash_pandas_object(frame, index=True).to_numpy()
    digest.update(row_hashes.tobytes())
    return digest.hexdigest()


def _scale_cache_get(cache_key: str) -> pd.DataFrame | None:
    with _scaled_overlay_cache_lock:
        cached = _scaled_overlay_cache.get(cache_key)
        if cached is None:
            return None
        _scaled_overlay_cache.move_to_end(cache_key)
        return cached.copy()


def _scale_cache_put(cache_key: str, value: pd.DataFrame) -> None:
    with _scaled_overlay_cache_lock:
        _scaled_overlay_cache[cache_key] = value.copy()
        _scaled_overlay_cache.move_to_end(cache_key)
        while len(_scaled_overlay_cache) > _SCALE_CACHE_MAXSIZE:
            _scaled_overlay_cache.popitem(last=False)


def scale_live_overlay_to_local(
    local_prices: pd.DataFrame,
    live_prices: pd.DataFrame,
) -> pd.DataFrame:
    """Scale live adjusted-close overlay to local TRI levels on overlap."""
    if local_prices.empty or live_prices.empty:
        return live_prices
    local_prices = clean_price_frame(local_prices)
    live_prices = clean_price_frame(live_prices)
    if local_prices.empty or live_prices.empty:
        return live_prices
    cache_key = f"{_frame_digest(local_prices)}:{_frame_digest(live_prices)}"
    cached = _scale_cache_get(cache_key)
    if cached is not None:
        return cached

    scaled = pd.DataFrame(index=live_prices.index)
    for col in live_prices.columns:
        live_series = pd.to_numeric(live_prices[col], errors="coerce").dropna()
        if live_series.empty:
            continue
        local_series = pd.to_numeric(local_prices.get(col), errors="coerce").dropna()
        if local_series.empty:
            scaled[col] = live_series
            continue

        overlap = local_series.index.intersection(live_series.index)
        if len(overlap) > 0:
            anchor_date = overlap.max()
            local_anchor = float(local_series.loc[anchor_date])
            live_anchor = float(live_series.loc[anchor_date])
        else:
            local_anchor = float(local_series.iloc[-1])
            live_anchor = float(live_series.iloc[0])

        if np.isfinite(local_anchor) and np.isfinite(live_anchor) and live_anchor > 0:
            scaled[col] = live_series * (local_anchor / live_anchor)
        else:
            scaled[col] = live_series

    cleaned = clean_price_frame(scaled)
    _scale_cache_put(cache_key, cleaned)
    return cleaned


def refresh_selected_prices_with_live_overlay(
    prices_selected: pd.DataFrame,
    ticker_map: dict,
    *,
    schedule_background: bool = True,
    cache_dir: str | Path = OPTIMIZER_LIVE_OVERLAY_CACHE_DIR,
) -> tuple[pd.DataFrame, pd.Timestamp | None, str]:
    """
    Stitch a non-canonical live display overlay onto local TRI optimizer prices.

    This path is intentionally in-memory and display freshness only; it does not
    write canonical market data or promote yfinance as evidence.
    """
    prices_selected = clean_price_frame(prices_selected)
    if prices_selected.empty:
        return prices_selected, None, "local-empty"

    ticker_by_permno: dict[object, str] = {}
    for permno in prices_selected.columns:
        ticker = (ticker_map or {}).get(permno)
        if ticker:
            ticker_by_permno[permno] = str(ticker).upper()

    latest_local = prices_selected.ffill().dropna(how="all").index.max()
    if not ticker_by_permno:
        return prices_selected, latest_local, "local"

    start = pd.Timestamp(latest_local).normalize() - pd.Timedelta(days=10)
    live_close = download_recent_close_prices(
        tuple(ticker_by_permno.values()),
        start.strftime("%Y-%m-%d"),
        cache_dir=cache_dir,
        schedule_background=schedule_background,
    )
    if live_close.empty:
        return prices_selected, latest_local, "local"

    live_by_permno = pd.DataFrame(index=live_close.index)
    for permno, ticker in ticker_by_permno.items():
        if ticker in live_close.columns:
            live_by_permno[permno] = live_close[ticker]
    live_by_permno = clean_price_frame(live_by_permno)
    if live_by_permno.empty:
        return prices_selected, latest_local, "local"
    live_by_permno = scale_live_overlay_to_local(prices_selected, live_by_permno)
    if live_by_permno.empty:
        return prices_selected, latest_local, "local"

    refreshed = live_by_permno.combine_first(prices_selected).sort_index()
    refreshed = clean_price_frame(refreshed)
    latest_live = refreshed.ffill().dropna(how="all").index.max()
    return refreshed, latest_live, "live"


@contextmanager
def _optional_file_lock(lock_path: Path, *, timeout: float = 2.0):
    try:
        from filelock import FileLock
    except Exception:
        yield
        return

    try:
        lock = FileLock(str(lock_path), timeout=timeout)
        lock.acquire()
    except Exception:
        yield
        return

    try:
        yield
    finally:
        lock.release()


def load_strategy_metrics_from_results(
    results_path: str | Path = BACKTEST_RESULTS_PATH,
) -> dict[str, dict]:
    """
    Load strategy metrics from the canonical backtest results repository file.

    Source: data/backtest_results.json
    """
    path = Path(results_path)
    if not path.exists():
        return {}

    try:
        with _optional_file_lock(Path(str(path) + ".lock")):
            data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return {}

    if not isinstance(data, dict):
        return {}

    metrics = {}
    for name, values in data.items():
        if not isinstance(values, dict):
            continue
        try:
            metrics[str(name)] = {
                "cagr": float(values.get("cagr", 0)),
                "sharpe": float(values.get("sharpe", 0)),
                "max_dd": float(values.get("max_dd", 0)),
                "timestamp": str(values.get("timestamp", "unknown")),
            }
        except (TypeError, ValueError):
            continue
    return metrics


def load_unified_data(
    mode: str = "historical",
    top_n: int = 2000,
    start_year: int = 2000,
    universe_mode: str = "top_liquid",
    asof_date: Any = None,
    *,
    processed_dir: str = "./data/processed",
    static_dir: str = "./data/static",
) -> UnifiedDataPackage:
    """
    Load dashboard data with unified interface.

    Args:
        mode: "historical" (parquet, institutional-grade) or "live" (yfinance, legacy)
        top_n: Number of top liquid tickers
        start_year: Start year for historical data
        universe_mode: "top_liquid" or "r3000_pit"
        asof_date: Optional as-of date for point-in-time universe
        processed_dir: Path to processed data directory
        static_dir: Path to static data directory

    Returns:
        UnifiedDataPackage with standardized data structure
    """
    if mode == "historical":
        return _load_historical_data(
            top_n=top_n,
            start_year=start_year,
            universe_mode=universe_mode,
            asof_date=asof_date,
            processed_dir=processed_dir,
            static_dir=static_dir,
        )
    elif mode == "live":
        return _load_live_data(
            top_n=top_n,
            start_year=start_year,
            processed_dir=processed_dir,
            static_dir=static_dir,
        )
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'historical' or 'live'")


def _load_historical_data(
    top_n: int,
    start_year: int,
    universe_mode: str,
    asof_date: Any,
    processed_dir: str,
    static_dir: str,
) -> UnifiedDataPackage:
    """
    Load data from processed parquet files (institutional-grade path).

    This is the preferred mode for production use with app.py's data pipeline.
    """
    # Use app.py's dashboard_data_loader
    prices_wide, returns_wide, macro, ticker_map, fundamentals_wide = load_dashboard_data(
        top_n=top_n,
        start_year=start_year,
        universe_mode=universe_mode,
        asof_date=asof_date,
        processed_dir=processed_dir,
        static_dir=static_dir,
    )

    # Extract sector_map if available
    sector_map = None
    if isinstance(fundamentals_wide, dict) and "sector_map" in fundamentals_wide:
        sector_map = fundamentals_wide["sector_map"]

    # Build metadata
    metadata = {
        "mode": "historical",
        "source": "parquet",
        "universe_mode": universe_mode,
        "top_n": top_n,
        "start_year": start_year,
        "prices_shape": prices_wide.shape,
        "returns_shape": returns_wide.shape,
        "macro_shape": macro.shape,
        "data_quality": "institutional_grade",
    }

    return UnifiedDataPackage(
        prices=prices_wide,
        returns=returns_wide,
        macro=macro,
        ticker_map=ticker_map,
        sector_map=sector_map,
        fundamentals=fundamentals_wide,
        metadata=metadata,
    )


def _load_live_data(
    top_n: int,
    start_year: int,
    processed_dir: str,
    static_dir: str,
) -> UnifiedDataPackage:
    """
    Load data from live yfinance fetching (dashboard.py legacy path).

    This mode is a fallback for when parquet files are unavailable.
    Provides compatibility with dashboard.py's original data fetching.
    """
    # Check if macro features exist (required for regime manager)
    macro_features_tri_path = f"{processed_dir}/macro_features_tri.parquet"
    macro_features_path = f"{processed_dir}/macro_features.parquet"

    macro = None
    if os.path.exists(macro_features_tri_path):
        macro = pd.read_parquet(macro_features_tri_path)
    elif os.path.exists(macro_features_path):
        macro = pd.read_parquet(macro_features_path)
    else:
        # Fallback: create minimal macro DataFrame
        # This allows dashboard to function without regime manager
        import datetime
        date_range = pd.date_range(
            start=f"{start_year}-01-01",
            end=datetime.datetime.now(),
            freq="D",
        )
        macro = pd.DataFrame(index=date_range)
        macro.index.name = "date"

    # Load sector_map if available
    sector_map_path = f"{static_dir}/sector_map.parquet"
    sector_map = None
    if os.path.exists(sector_map_path):
        sector_map_df = pd.read_parquet(sector_map_path)
        if "permno" in sector_map_df.columns and "sector" in sector_map_df.columns:
            sector_map = dict(zip(sector_map_df["permno"], sector_map_df["sector"]))

    # Build metadata
    metadata = {
        "mode": "live",
        "source": "yfinance",
        "universe_mode": "yfinance_live",
        "top_n": top_n,
        "start_year": start_year,
        "data_quality": "live_fetch",
        "warning": "Live mode is legacy path. Migrate to historical mode for institutional-grade data.",
    }

    # Return minimal package (dashboard.py will populate via its own fetching)
    # This allows dashboard.py to use orchestrator without breaking existing code
    return UnifiedDataPackage(
        prices=pd.DataFrame(),  # Empty - dashboard.py fetches via yfinance
        returns=pd.DataFrame(),  # Empty - dashboard.py computes
        macro=macro,
        ticker_map={},  # Empty - dashboard.py builds dynamically
        sector_map=sector_map,
        fundamentals=None,
        metadata=metadata,
    )


def get_macro_features(
    processed_dir: str = "./data/processed",
    prefer_tri: bool = True,
) -> pd.DataFrame:
    """
    Load macro features for regime manager.

    Args:
        processed_dir: Path to processed data directory
        prefer_tri: If True, prefer macro_features_tri.parquet over macro_features.parquet

    Returns:
        Macro features DataFrame with date index
    """
    macro_features_tri_path = f"{processed_dir}/macro_features_tri.parquet"
    macro_features_path = f"{processed_dir}/macro_features.parquet"

    if prefer_tri and os.path.exists(macro_features_tri_path):
        return pd.read_parquet(macro_features_tri_path)
    elif os.path.exists(macro_features_path):
        return pd.read_parquet(macro_features_path)
    else:
        raise FileNotFoundError(
            f"Macro features not found. Expected at:\n"
            f"  - {macro_features_tri_path} OR\n"
            f"  - {macro_features_path}\n"
            f"Run macro feature builder first."
        )


def derive_data_health(package: UnifiedDataPackage) -> dict[str, Any]:
    """
    Assess data health and return status dict.

    Returns dict with:
        - status: "HEALTHY" | "DEGRADED" | "FAILED"
        - issues: List of issues found
        - metrics: Dict of health metrics
    """
    issues = []
    metrics = {}

    # Check prices coverage
    if package.prices.empty:
        issues.append("Prices DataFrame is empty")
    else:
        null_pct = package.prices.isnull().sum().sum() / (package.prices.shape[0] * package.prices.shape[1])
        metrics["prices_null_pct"] = f"{null_pct * 100:.2f}%"
        if null_pct > 0.10:
            issues.append(f"Prices have {null_pct*100:.1f}% null values (threshold: 10%)")

    # Check returns coverage
    if package.returns.empty:
        issues.append("Returns DataFrame is empty")
    else:
        null_pct = package.returns.isnull().sum().sum() / (package.returns.shape[0] * package.returns.shape[1])
        metrics["returns_null_pct"] = f"{null_pct * 100:.2f}%"

    # Check macro features
    if package.macro.empty:
        issues.append("Macro DataFrame is empty")
    else:
        metrics["macro_rows"] = len(package.macro)
        metrics["macro_cols"] = len(package.macro.columns)

    # Check ticker map
    if not package.ticker_map:
        issues.append("Ticker map is empty")
    else:
        metrics["ticker_count"] = len(package.ticker_map)

    # Determine overall status
    if len(issues) == 0:
        status = "HEALTHY"
    elif len(issues) <= 2:
        status = "DEGRADED"
    else:
        status = "FAILED"

    return {
        "status": status,
        "issues": issues,
        "metrics": metrics,
        "data_mode": package.metadata.get("mode", "unknown"),
        "data_quality": package.metadata.get("data_quality", "unknown"),
    }
