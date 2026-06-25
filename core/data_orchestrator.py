"""
Data Orchestrator: Unified Data Loading Abstraction Layer

Provides a unified interface for loading dashboard data, supporting both:
- Live mode: yfinance fetching (dashboard.py legacy path)
- Historical mode: processed parquet files (app.py institutional-grade path)

Enables gradual migration from yfinance to parquet-based data pipeline.
"""

from __future__ import annotations

import bisect
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable, Iterable

import duckdb
import numpy as np
import pandas as pd

from data.dashboard_data_loader import load_dashboard_data
from data.providers.registry import build_market_data_provider


BACKTEST_RESULTS_PATH = Path("data/backtest_results.json")
OPTIMIZER_LIVE_OVERLAY_CACHE_DIR = Path("data/runtime_cache/optimizer_live_overlay")
OPTIMIZER_LIVE_OVERLAY_CACHE_VERSION = 1
STRATEGY_REPLAY_CACHE_DIR = Path("data/runtime_cache/strategy_replay")
STRATEGY_REPLAY_CACHE_VERSION = 1
STRATEGY_REPLAY_PRICE_FILE_NAMES = (
    "prices_tri.parquet",
    "prices.parquet",
    "yahoo_patch.parquet",
)
STRATEGY_REPLAY_CONTEXT_FILE_NAMES = (
    "tickers.parquet",
    "universe_r3000_daily.parquet",
)
STRATEGY_REPLAY_REQUIRED_UNIVERSE_MODE = "r3000_pit"
STRATEGY_REPLAY_ARTIFACT_COLUMNS = [
    "matrix",
    "date",
    "as_of_date",
    "cache_key",
    "artifact_scope",
]
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


@dataclass(frozen=True)
class StrategyReplayInputs:
    """Local PIT-safe matrix slice for forward-walk strategy replay."""

    as_of_date: pd.Timestamp
    prices: pd.DataFrame
    returns: pd.DataFrame
    ticker_map: dict[int, str]
    cache_signature: dict[str, Any]
    cache_key: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class PriceEndpointFreshness:
    """Per-column price endpoints computed once for a loaded price matrix."""

    latest_by_column: dict[object, pd.Timestamp | None]
    required_latest: pd.Timestamp | None
    columns: tuple[object, ...]
    row_count: int
    column_count: int

    def latest_for(self, column: object | None) -> pd.Timestamp | None:
        if column is None:
            return None
        return self.latest_by_column.get(column)

    def required_latest_for(self, columns: Iterable[object] | None = None) -> pd.Timestamp | None:
        if columns is None:
            return self.required_latest
        latest_dates = [
            self.latest_by_column.get(column)
            for column in columns
            if self.latest_by_column.get(column) is not None
        ]
        return max(latest_dates) if latest_dates else None


@dataclass(frozen=True)
class PriceEndpointRepairResult:
    """Display-only stale endpoint repair overlay for local price matrices."""

    prices: pd.DataFrame
    freshness: PriceEndpointFreshness
    requested_columns: tuple[object, ...]
    repaired_columns: tuple[object, ...]
    unrepaired_columns: tuple[object, ...]
    required_latest: pd.Timestamp | None
    source: str
    diagnostics: tuple[dict[str, object], ...]
    display_only: bool = True
    canonical_market_data_write: bool = False


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


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.date().isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    return value


def _reject_non_finite(value: Any, *, path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_non_finite(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _reject_non_finite(item, path=f"{path}[{idx}]")
        return
    if isinstance(value, (float, np.floating)) and not np.isfinite(float(value)):
        raise ValueError(f"Strategy replay control contains non-finite value at {path}")


def _validate_strategy_replay_controls(
    *,
    max_weight: float,
    controls: dict[str, Any] | None,
) -> float:
    max_weight_value = float(max_weight)
    if not np.isfinite(max_weight_value):
        raise ValueError("Strategy replay max_weight must be finite.")
    _reject_non_finite(controls or {}, path="controls")
    return max_weight_value


def _coerce_replay_date(value: Any, *, field_name: str) -> pd.Timestamp:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid {field_name}: {value}")
    ts = pd.Timestamp(ts)
    if ts.tz is not None:
        ts = ts.tz_convert(None)
    return ts.normalize()


def _iso_date_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return _coerce_replay_date(value, field_name="date").date().isoformat()


def build_strategy_replay_cache_signature(
    *,
    method: str,
    controls: dict[str, Any] | None,
    start_date: Any,
    end_date: Any,
    as_of_date: Any,
    max_weight: float,
    processed_dir: str | Path = "./data/processed",
    static_dir: str | Path = "./data/static",
    top_n: int = 2000,
    start_year: int = 2000,
    universe_mode: str = "r3000_pit",
) -> dict[str, Any]:
    """
    Fingerprint local replay inputs and controls for display-only artifact caching.

    Portfolio replay uses local price/return matrices built from
    `data/processed/prices_tri.parquet` when present. The signature intentionally
    includes source file stats plus strategy controls so stale artifacts are not
    reused across input rewrites, method changes, date ranges, or max-weight edits.
    """
    max_weight_value = _validate_strategy_replay_controls(
        max_weight=max_weight,
        controls=controls,
    )
    if str(universe_mode) != STRATEGY_REPLAY_REQUIRED_UNIVERSE_MODE:
        raise ValueError("Strategy replay cache signatures require universe_mode='r3000_pit' for PIT-safe membership.")
    processed_root = Path(processed_dir)
    static_root = Path(static_dir)
    source_paths = [processed_root / name for name in STRATEGY_REPLAY_PRICE_FILE_NAMES]
    source_paths.extend(processed_root / name for name in STRATEGY_REPLAY_CONTEXT_FILE_NAMES)
    source_paths.append(static_root / "sector_map.parquet")
    return {
        "version": STRATEGY_REPLAY_CACHE_VERSION,
        "source_files": [_file_signature(path) for path in source_paths],
        "method": str(method),
        "controls": _json_safe(controls or {}),
        "start_date": _iso_date_or_none(start_date),
        "end_date": _iso_date_or_none(end_date),
        "as_of_date": _iso_date_or_none(as_of_date),
        "max_weight": max_weight_value,
        "top_n": int(top_n),
        "start_year": int(start_year),
        "universe_mode": str(universe_mode),
    }


def strategy_replay_cache_key(signature: dict[str, Any]) -> str:
    payload = json.dumps(_json_safe(signature), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def strategy_replay_cache_path(
    signature: dict[str, Any],
    *,
    cache_dir: str | Path = STRATEGY_REPLAY_CACHE_DIR,
) -> Path:
    return Path(cache_dir) / f"{strategy_replay_cache_key(signature)}.parquet"


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


def build_price_endpoint_freshness(
    prices: pd.DataFrame,
    columns: tuple | list | None = None,
    *,
    column_chunk_size: int = 512,
) -> PriceEndpointFreshness:
    """Return a reusable per-column endpoint snapshot for a wide price frame."""
    cleaned = clean_price_frame(prices)
    if columns is None:
        selected = list(cleaned.columns) if isinstance(cleaned, pd.DataFrame) else []
    else:
        selected = list(columns)
    if cleaned.empty:
        latest_by_column = {col: None for col in selected}
        return PriceEndpointFreshness(
            latest_by_column=latest_by_column,
            required_latest=None,
            columns=tuple(selected),
            row_count=0,
            column_count=len(selected),
        )

    present = [col for col in selected if col in cleaned.columns]
    latest_by_column: dict[object, pd.Timestamp | None] = {col: None for col in selected}
    chunk_size = max(1, int(column_chunk_size))
    positions = np.arange(len(cleaned.index), dtype="int64")
    for start in range(0, len(present), chunk_size):
        chunk = present[start: start + chunk_size]
        selected_frame = cleaned.reindex(columns=chunk)
        valid = selected_frame.where(selected_frame > 0)
        mask = valid.notna()
        if not bool(mask.any().any()):
            continue
        latest_positions = pd.Series(
            np.where(mask.to_numpy(), positions[:, None], -1).max(axis=0),
            index=valid.columns,
        )
        for col, pos in latest_positions.items():
            if int(pos) >= 0:
                latest_by_column[col] = pd.Timestamp(valid.index[int(pos)]).normalize()

    available_latest = [latest for latest in latest_by_column.values() if latest is not None]
    return PriceEndpointFreshness(
        latest_by_column=latest_by_column,
        required_latest=max(available_latest) if available_latest else None,
        columns=tuple(selected),
        row_count=int(cleaned.shape[0]),
        column_count=len(selected),
    )


def price_latest_dates_by_column(
    prices: pd.DataFrame,
    columns: tuple | list | None = None,
) -> dict[object, pd.Timestamp | None]:
    """Return each column's own last valid positive price date."""
    return build_price_endpoint_freshness(prices, columns).latest_by_column


def price_column_latest_date(
    prices: pd.DataFrame,
    column: object | None,
    freshness: PriceEndpointFreshness | None = None,
) -> pd.Timestamp | None:
    """Return one column's own last valid positive price date."""
    if column is None:
        return None
    if freshness is not None:
        return freshness.latest_for(column)
    return price_latest_dates_by_column(prices, [column]).get(column)


def price_frame_latest_date(
    prices: pd.DataFrame,
    freshness: PriceEndpointFreshness | None = None,
    columns: tuple | list | None = None,
) -> pd.Timestamp | None:
    """Return the freshest endpoint across valid positive price columns."""
    if freshness is not None:
        return freshness.required_latest_for(columns)
    return build_price_endpoint_freshness(prices, columns).required_latest


def price_endpoint_is_fresh(
    endpoint: pd.Timestamp | None,
    required_latest: pd.Timestamp | None,
    *,
    max_staleness_days: int = 0,
) -> bool:
    """Return whether an endpoint is fresh enough for a caller's policy."""
    if endpoint is None or pd.isna(endpoint):
        return False
    if required_latest is None or pd.isna(required_latest):
        return True
    gap_days = (pd.Timestamp(required_latest).normalize() - pd.Timestamp(endpoint).normalize()).days
    return gap_days <= int(max_staleness_days)


def _resolve_price_column_ticker(column: object, ticker_map: dict | None) -> str | None:
    if not isinstance(ticker_map, dict):
        return None
    candidates: list[object] = [column, str(column)]
    try:
        candidates.append(int(column))
    except (TypeError, ValueError):
        pass
    for key in candidates:
        ticker = ticker_map.get(key)
        if ticker is not None and str(ticker).strip():
            return str(ticker).upper().strip()
    return None


def _endpoint_date_label(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def filter_price_frame_to_fresh_columns(
    prices: pd.DataFrame,
    columns: tuple | list | None = None,
    *,
    required_latest: pd.Timestamp | None = None,
    freshness: PriceEndpointFreshness | None = None,
) -> tuple[pd.DataFrame, pd.Timestamp | None, tuple[object, ...]]:
    """
    Keep only columns whose own endpoint reaches the required freshness date.

    If no required endpoint is supplied, the freshest endpoint in the provided
    frame becomes the target. This prevents ragged columns from being silently
    forward-filled and reported as current.
    """
    cleaned = clean_price_frame(prices)
    selected = list(columns) if columns is not None else list(cleaned.columns)
    if not selected:
        return pd.DataFrame(index=cleaned.index), None, ()

    latest_by_column = (
        freshness.latest_by_column
        if freshness is not None
        else build_price_endpoint_freshness(cleaned, selected).latest_by_column
    )
    available_latest = [
        latest_by_column.get(column)
        for column in selected
        if latest_by_column.get(column) is not None
    ]
    target_latest = (
        pd.Timestamp(required_latest).normalize()
        if required_latest is not None and not pd.isna(required_latest)
        else (max(available_latest) if available_latest else None)
    )
    if target_latest is None:
        return cleaned.reindex(columns=[]), None, tuple(selected)

    fresh_cols = [
        col
        for col in selected
        if latest_by_column.get(col) is not None
        and pd.Timestamp(latest_by_column[col]).normalize() >= target_latest
    ]
    stale_cols = tuple(col for col in selected if col not in fresh_cols)
    return cleaned.reindex(columns=fresh_cols), target_latest, stale_cols


def repair_stale_price_endpoints_with_live_overlay(
    prices: pd.DataFrame,
    ticker_map: dict,
    stale_columns: Iterable[object] | None = None,
    *,
    required_latest: pd.Timestamp | None = None,
    price_freshness: PriceEndpointFreshness | None = None,
    max_staleness_days: int = 0,
    schedule_background: bool = True,
    cache_dir: str | Path = OPTIMIZER_LIVE_OVERLAY_CACHE_DIR,
    live_loader: Callable[..., pd.DataFrame] | None = None,
) -> PriceEndpointRepairResult:
    """
    Repair stale local price endpoints with anchored, display-only live overlays.

    The overlay is capped to the caller's required endpoint so a successful
    repair does not move the matrix-wide freshness target and accidentally make
    unrelated local columns look stale. No canonical parquet is written.
    """
    cleaned = clean_price_frame(prices)
    if price_freshness is None:
        price_freshness = build_price_endpoint_freshness(cleaned)
    required_ts = (
        pd.Timestamp(required_latest).normalize()
        if required_latest is not None and not pd.isna(required_latest)
        else price_frame_latest_date(cleaned, freshness=price_freshness)
    )
    selected = (
        list(dict.fromkeys(stale_columns))
        if stale_columns is not None
        else list(cleaned.columns)
    )
    diagnostics: dict[object, dict[str, object]] = {}
    candidates: list[object] = []

    for column in selected:
        endpoint = price_column_latest_date(cleaned, column, freshness=price_freshness)
        ticker = _resolve_price_column_ticker(column, ticker_map)
        base = {
            "column": str(column),
            "ticker": ticker or "",
            "before_latest": _endpoint_date_label(endpoint),
            "after_latest": _endpoint_date_label(endpoint),
            "display_only": True,
            "canonical_market_data_write": False,
        }
        if column not in cleaned.columns or endpoint is None:
            diagnostics[column] = {
                **base,
                "status": "unrepaired",
                "reason": "missing_local_price_history",
            }
            continue
        if price_endpoint_is_fresh(
            endpoint,
            required_ts,
            max_staleness_days=max_staleness_days,
        ):
            diagnostics[column] = {
                **base,
                "status": "skipped",
                "reason": "endpoint_already_fresh",
            }
            continue
        if not ticker:
            diagnostics[column] = {
                **base,
                "status": "unrepaired",
                "reason": "ticker_mapping_unavailable",
            }
            continue
        diagnostics[column] = {
            **base,
            "status": "pending",
            "reason": "repair_not_attempted",
        }
        candidates.append(column)

    if not candidates or required_ts is None:
        unrepaired = tuple(
            column for column, row in diagnostics.items()
            if row.get("status") == "unrepaired"
        )
        source = "local_no_stale_endpoint" if not candidates else "local_required_endpoint_unavailable"
        return PriceEndpointRepairResult(
            prices=cleaned,
            freshness=price_freshness,
            requested_columns=tuple(selected),
            repaired_columns=tuple(),
            unrepaired_columns=unrepaired,
            required_latest=required_ts,
            source=source,
            diagnostics=tuple(diagnostics[column] for column in selected if column in diagnostics),
        )

    endpoint_values = [
        price_column_latest_date(cleaned, column, freshness=price_freshness)
        for column in candidates
    ]
    local_start = min(pd.Timestamp(value).normalize() for value in endpoint_values if value is not None)
    start_iso = (local_start - pd.Timedelta(days=10)).date().isoformat()
    column_to_ticker = {
        column: _resolve_price_column_ticker(column, ticker_map)
        for column in candidates
    }
    tickers = tuple(sorted({ticker for ticker in column_to_ticker.values() if ticker}))
    loader = live_loader or download_recent_close_prices

    try:
        live_close = loader(
            tickers,
            start_iso,
            cache_dir=cache_dir,
            schedule_background=schedule_background,
        )
    except Exception as exc:
        for column in candidates:
            row = dict(diagnostics[column])
            row.update(status="unrepaired", reason=f"live_overlay_failed:{type(exc).__name__}")
            diagnostics[column] = row
        return PriceEndpointRepairResult(
            prices=cleaned,
            freshness=price_freshness,
            requested_columns=tuple(selected),
            repaired_columns=tuple(),
            unrepaired_columns=tuple(candidates),
            required_latest=required_ts,
            source="display_live_overlay_failed",
            diagnostics=tuple(diagnostics[column] for column in selected if column in diagnostics),
        )

    live_close = clean_price_frame(live_close)
    if live_close.empty:
        for column in candidates:
            row = dict(diagnostics[column])
            row.update(status="unrepaired", reason="live_overlay_unavailable_or_pending")
            diagnostics[column] = row
        return PriceEndpointRepairResult(
            prices=cleaned,
            freshness=price_freshness,
            requested_columns=tuple(selected),
            repaired_columns=tuple(),
            unrepaired_columns=tuple(candidates),
            required_latest=required_ts,
            source="display_live_overlay_unavailable",
            diagnostics=tuple(diagnostics[column] for column in selected if column in diagnostics),
        )

    live_by_column = pd.DataFrame(index=live_close.index)
    for column, ticker in column_to_ticker.items():
        if ticker and ticker in live_close.columns:
            live_by_column[column] = live_close[ticker]
    live_by_column = clean_price_frame(live_by_column)
    scaled = scale_live_overlay_to_local(
        cleaned.reindex(columns=candidates),
        live_by_column,
    )
    if required_ts is not None and not scaled.empty:
        scaled = scaled.loc[scaled.index <= required_ts]
    scaled = clean_price_frame(scaled)
    if scaled.empty:
        for column in candidates:
            row = dict(diagnostics[column])
            row.update(status="unrepaired", reason="overlay_anchor_unavailable")
            diagnostics[column] = row
        return PriceEndpointRepairResult(
            prices=cleaned,
            freshness=price_freshness,
            requested_columns=tuple(selected),
            repaired_columns=tuple(),
            unrepaired_columns=tuple(candidates),
            required_latest=required_ts,
            source="display_live_overlay_unanchored",
            diagnostics=tuple(diagnostics[column] for column in selected if column in diagnostics),
        )

    repaired_prices = cleaned.copy()
    for column in candidates:
        if column not in scaled.columns:
            continue
        series = pd.to_numeric(scaled[column], errors="coerce")
        series = series.replace([np.inf, -np.inf], np.nan)
        series = series.where(series > 0).dropna()
        if required_ts is not None:
            series = series.loc[series.index <= required_ts]
        if series.empty:
            continue
        repaired_prices = repaired_prices.reindex(repaired_prices.index.union(series.index).sort_values())
        repaired_prices.loc[series.index, column] = series
    repaired_prices = clean_price_frame(repaired_prices)
    repaired_freshness = build_price_endpoint_freshness(repaired_prices)

    repaired_columns: list[object] = []
    unrepaired_columns: list[object] = []
    for column in candidates:
        before = price_column_latest_date(cleaned, column, freshness=price_freshness)
        after = price_column_latest_date(repaired_prices, column, freshness=repaired_freshness)
        is_repaired = (
            after is not None
            and before is not None
            and pd.Timestamp(after).normalize() > pd.Timestamp(before).normalize()
            and price_endpoint_is_fresh(
                after,
                required_ts,
                max_staleness_days=max_staleness_days,
            )
        )
        row = dict(diagnostics[column])
        row["after_latest"] = _endpoint_date_label(after)
        if is_repaired:
            row.update(status="repaired", reason="anchored_display_overlay")
            repaired_columns.append(column)
        else:
            row.update(status="unrepaired", reason="overlay_did_not_reach_required_endpoint")
            unrepaired_columns.append(column)
        diagnostics[column] = row

    if repaired_columns and unrepaired_columns:
        source = "display_live_overlay_partial"
    elif repaired_columns:
        source = "display_live_overlay"
    else:
        source = "display_live_overlay_unavailable"
    return PriceEndpointRepairResult(
        prices=repaired_prices,
        freshness=repaired_freshness,
        requested_columns=tuple(selected),
        repaired_columns=tuple(repaired_columns),
        unrepaired_columns=tuple(unrepaired_columns),
        required_latest=required_ts,
        source=source,
        diagnostics=tuple(diagnostics[column] for column in selected if column in diagnostics),
    )


def benchmark_tickers_requiring_live_overlay(
    local_prices: pd.DataFrame,
    tickers: tuple[str, ...],
) -> tuple[str, ...]:
    """Return benchmark tickers whose local series is missing or stale vs local peers."""

    normalized = tuple(str(ticker).upper().strip() for ticker in tickers if str(ticker).strip())
    if not normalized:
        return ()
    if not isinstance(local_prices, pd.DataFrame) or local_prices.empty:
        return normalized

    cleaned = clean_price_frame(local_prices)
    latest_by_ticker: dict[str, pd.Timestamp | None] = {}
    for ticker in normalized:
        if ticker not in cleaned.columns:
            latest_by_ticker[ticker] = None
            continue
        series = pd.to_numeric(cleaned[ticker], errors="coerce")
        series = series.where(series > 0).dropna()
        latest_by_ticker[ticker] = pd.Timestamp(series.index.max()).normalize() if not series.empty else None

    available_dates = [value for value in latest_by_ticker.values() if value is not None]
    if not available_dates:
        return normalized
    freshest = max(available_dates)
    return tuple(
        ticker
        for ticker in normalized
        if latest_by_ticker.get(ticker) is None or latest_by_ticker[ticker] < freshest
    )


def merge_benchmark_live_overlay(
    local_prices: pd.DataFrame,
    live_prices: pd.DataFrame,
    tickers: tuple[str, ...],
) -> pd.DataFrame:
    """Overlay live benchmark prices by ticker without mutating local history.

    Live adjusted-close data can only be scaled onto a local TRI series when
    the same ticker has an actual overlap date. No overlap means no verified
    anchor, so the ticker remains stale for the downstream freshness gate.
    """

    normalized = tuple(str(ticker).upper().strip() for ticker in tickers if str(ticker).strip())
    local_clean = clean_price_frame(local_prices)
    live_clean = clean_price_frame(live_prices)
    if local_clean.empty:
        return live_clean.reindex(columns=list(normalized))
    if live_clean.empty:
        return local_clean.reindex(columns=list(normalized))

    merged = local_clean.copy()
    for ticker in normalized:
        if ticker not in live_clean.columns:
            continue
        live_series = pd.to_numeric(live_clean[ticker], errors="coerce")
        live_series = live_series.where(live_series > 0).dropna()
        if live_series.empty:
            continue
        if ticker not in merged.columns:
            continue

        local_series = pd.to_numeric(merged[ticker], errors="coerce")
        local_valid = local_series.where(local_series > 0).dropna()
        if local_valid.empty:
            continue
        overlap = local_valid.index.intersection(live_series.index)
        if len(overlap) == 0:
            continue
        anchor = overlap.max()
        local_anchor = float(local_valid.loc[anchor])
        live_anchor = float(live_series.loc[anchor])
        if not (np.isfinite(local_anchor) and np.isfinite(live_anchor) and live_anchor > 0):
            continue
        overlay = live_series * (local_anchor / live_anchor)
        merged = merged.reindex(merged.index.union(overlay.index).sort_values())
        merged.loc[overlay.index, ticker] = overlay

    return clean_price_frame(merged.reindex(columns=list(normalized)))


def _fresh_benchmark_columns(bench_data: pd.DataFrame, tickers: tuple[str, ...], stale_tickers_without_overlay: tuple[str, ...] = ()) -> pd.DataFrame:
    """Keep benchmark columns with valid local/live endpoints and drop stale misses."""
    normalized = [str(ticker).upper().strip() for ticker in tickers if str(ticker).strip()]
    cleaned = clean_price_frame(bench_data).reindex(columns=normalized)
    if cleaned.empty:
        return cleaned
    required_latest = price_frame_latest_date(cleaned.drop(columns=list(stale_tickers_without_overlay), errors="ignore"))
    fresh, _latest, _stale = filter_price_frame_to_fresh_columns(
        cleaned,
        normalized,
        required_latest=required_latest,
    )
    return fresh.drop(columns=list(stale_tickers_without_overlay), errors="ignore")


def build_benchmark_equity_from_prices(
    tickers: tuple[str, ...],
    ytd_start: pd.Timestamp,
    local_prices: pd.DataFrame,
    live_loader: Callable[[tuple[str, ...], str], pd.DataFrame],
) -> tuple[dict[str, pd.Series], pd.Timestamp | None, str]:
    """Build benchmark equity from local prices plus per-ticker stale live overlay."""

    normalized = tuple(str(ticker).upper().strip() for ticker in tickers if str(ticker).strip())
    bench_data = clean_price_frame(local_prices)
    source = "local"
    stale_without_overlay: tuple[str, ...] = ()
    if bench_data.empty:
        try:
            bench_data = clean_price_frame(live_loader(normalized, pd.Timestamp(ytd_start).strftime("%Y-%m-%d")))
            source = "live"
        except Exception:
            bench_data = pd.DataFrame()
    else:
        stale_tickers = benchmark_tickers_requiring_live_overlay(bench_data, normalized)
        if stale_tickers:
            try:
                live_overlay = live_loader(stale_tickers, pd.Timestamp(ytd_start).strftime("%Y-%m-%d"))
            except Exception:
                live_overlay = pd.DataFrame()
            if isinstance(live_overlay, pd.DataFrame) and not live_overlay.empty:
                local_required_latest = price_frame_latest_date(bench_data)
                merged_data = merge_benchmark_live_overlay(bench_data, live_overlay, normalized)
                latest_after_overlay = price_latest_dates_by_column(merged_data, list(stale_tickers))
                overlaid = {
                    str(ticker).upper().strip()
                    for ticker, latest in latest_after_overlay.items()
                    if latest is not None
                    and local_required_latest is not None
                    and pd.Timestamp(latest).normalize() >= pd.Timestamp(local_required_latest).normalize()
                }
                bench_data = merged_data
                overlay_clean = clean_price_frame(live_overlay)
                live_available = {
                    str(col).upper().strip()
                    for col in overlay_clean.columns
                    if not pd.to_numeric(overlay_clean[col], errors="coerce").where(lambda s: s > 0).dropna().empty
                }
                stale_without_overlay = tuple(t for t in stale_tickers if t not in overlaid)
                if not live_available:
                    source = "local_stale_dropped"
                elif not overlaid:
                    source = "local_overlay_unavailable"
                else:
                    source = "local+live_overlay" if not stale_without_overlay else "local+live_overlay_stale_dropped"
            else:
                stale_without_overlay = stale_tickers
                source = "local_stale_dropped"

    bench_data = _fresh_benchmark_columns(bench_data, normalized, stale_without_overlay)
    if bench_data.empty:
        return {}, None, "unavailable"

    benchmark_equity: dict[str, pd.Series] = {}
    for col in normalized:
        if col not in bench_data.columns:
            continue
        series = pd.to_numeric(bench_data[col], errors="coerce")
        series = series.replace([np.inf, -np.inf], np.nan)
        series = series.where(series > 0).dropna()
        if len(series) < 2:
            continue
        returns = series.pct_change(fill_method=None).iloc[1:]
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        eq = (1 + returns).cumprod()
        eq = eq.replace([np.inf, -np.inf], np.nan).dropna()
        if not eq.empty:
            eq.name = col
            benchmark_equity[col] = eq
    if not benchmark_equity:
        return {}, None, "unavailable"
    benchmark_latest = min(eq.index.max() for eq in benchmark_equity.values())
    benchmark_equity = {
        ticker: eq.loc[eq.index <= benchmark_latest]
        for ticker, eq in benchmark_equity.items()
    }
    return benchmark_equity, benchmark_latest, source


def _normalize_replay_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame()
    cleaned = frame.apply(pd.to_numeric, errors="coerce")
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    idx = pd.to_datetime(cleaned.index, errors="coerce")
    valid_idx = ~pd.isna(idx)
    cleaned = cleaned.loc[valid_idx]
    cleaned.index = pd.DatetimeIndex(idx[valid_idx])
    if cleaned.index.tz is not None:
        cleaned.index = cleaned.index.tz_localize(None)
    cleaned = cleaned.sort_index()
    cleaned = cleaned[~cleaned.index.duplicated(keep="last")]
    return cleaned.dropna(how="all")


def _slice_replay_matrix(
    frame: pd.DataFrame,
    *,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
) -> pd.DataFrame:
    cleaned = _normalize_replay_matrix(frame)
    if cleaned.empty:
        return cleaned
    return cleaned[(cleaned.index >= start_ts) & (cleaned.index <= end_ts)].copy()


def _strategy_replay_source_matrix(processed_dir: str | Path) -> dict[str, str]:
    processed_root = Path(processed_dir)
    tri_path = processed_root / "prices_tri.parquet"
    if tri_path.exists():
        return {
            "price_matrix_path": str(tri_path.resolve(strict=False)),
            "source_matrix_paths": [str(tri_path.resolve(strict=False))],
            "source_merge_mode": "tri_preferred",
            "source_precedence": "prices_tri",
            "price_column": "tri",
            "return_column": "total_ret",
        }
    prices_path = processed_root / "prices.parquet"
    patch_path = processed_root / "yahoo_patch.parquet"
    source_paths = [str(prices_path.resolve(strict=False))]
    merge_mode = "base_prices_only"
    precedence = "prices"
    if patch_path.exists():
        source_paths.append(str(patch_path.resolve(strict=False)))
        merge_mode = "base_prices_with_yahoo_patch"
        precedence = "yahoo_patch_overrides_prices"
    return {
        "price_matrix_path": str(prices_path.resolve(strict=False)),
        "source_matrix_paths": source_paths,
        "source_merge_mode": merge_mode,
        "source_precedence": precedence,
        "price_column": "adj_close",
        "return_column": "total_ret",
    }


def load_strategy_replay_inputs(
    *,
    as_of_date: Any,
    start_date: Any | None = None,
    end_date: Any | None = None,
    method: str = "portfolio_replay",
    controls: dict[str, Any] | None = None,
    max_weight: float = 0.35,
    top_n: int = 2000,
    start_year: int = 2000,
    universe_mode: str = "r3000_pit",
    processed_dir: str | Path = "./data/processed",
    static_dir: str | Path = "./data/static",
) -> StrategyReplayInputs:
    """
    Return a local PIT-safe replay input slice through `as_of_date`.

    This loader intentionally uses the historical parquet path only. It does
    not invoke live display overlays or synchronous providers; callers that need
    full forward-walk behavior should call this once per replay date.
    """
    as_of_ts = _coerce_replay_date(as_of_date, field_name="as_of_date")
    if str(universe_mode) != STRATEGY_REPLAY_REQUIRED_UNIVERSE_MODE:
        raise ValueError("Strategy replay inputs require universe_mode='r3000_pit' for PIT-safe membership.")
    max_weight_value = _validate_strategy_replay_controls(
        max_weight=max_weight,
        controls=controls,
    )
    start_ts = (
        _coerce_replay_date(start_date, field_name="start_date")
        if start_date is not None
        else pd.Timestamp(f"{int(start_year)}-01-01")
    )
    requested_end_ts = (
        _coerce_replay_date(end_date, field_name="end_date")
        if end_date is not None
        else as_of_ts
    )
    effective_end_ts = min(requested_end_ts, as_of_ts)

    signature = build_strategy_replay_cache_signature(
        method=method,
        controls=controls,
        start_date=start_ts,
        end_date=requested_end_ts,
        as_of_date=as_of_ts,
        max_weight=max_weight_value,
        processed_dir=processed_dir,
        static_dir=static_dir,
        top_n=top_n,
        start_year=start_year,
        universe_mode=universe_mode,
    )
    cache_key = strategy_replay_cache_key(signature)

    returns_wide, prices_wide, _macro, ticker_map, _fundamentals_wide = load_dashboard_data(
        top_n=top_n,
        start_year=start_year,
        universe_mode=universe_mode,
        asof_date=as_of_ts,
        processed_dir=str(processed_dir),
        static_dir=str(static_dir),
    )
    prices_slice = _slice_replay_matrix(
        prices_wide,
        start_ts=start_ts,
        end_ts=effective_end_ts,
    )
    returns_slice = _slice_replay_matrix(
        returns_wide,
        start_ts=start_ts,
        end_ts=effective_end_ts,
    )

    metadata = {
        "source": "local_parquet",
        "display_only": True,
        "canonical_market_data_write": False,
        "as_of_date": as_of_ts.date().isoformat(),
        "requested_date_range": {
            "start": start_ts.date().isoformat(),
            "end": requested_end_ts.date().isoformat(),
        },
        "effective_date_range": {
            "start": start_ts.date().isoformat(),
            "end": effective_end_ts.date().isoformat(),
        },
        "future_rows_excluded": True,
        "method": str(method),
        "max_weight": max_weight_value,
        "controls": _json_safe(controls or {}),
        "top_n": int(top_n),
        "start_year": int(start_year),
        "universe_mode": str(universe_mode),
        **_strategy_replay_source_matrix(processed_dir),
    }

    return StrategyReplayInputs(
        as_of_date=as_of_ts,
        prices=prices_slice,
        returns=returns_slice,
        ticker_map={int(k): str(v) for k, v in (ticker_map or {}).items()},
        cache_signature=signature,
        cache_key=cache_key,
        metadata=metadata,
    )


def iter_strategy_replay_inputs(
    replay_dates: list[Any] | tuple[Any, ...],
    **kwargs: Any,
):
    """Yield one PIT-safe matrix slice per replay date."""
    for replay_date in replay_dates:
        yield load_strategy_replay_inputs(as_of_date=replay_date, **kwargs)


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


def _atomic_write_parquet(path: Path, frame: pd.DataFrame, *, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        frame.to_parquet(tmp_path, index=index)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _serialize_json_payload(payload: dict[str, Any]) -> str:
    return json.dumps(_json_safe(payload), indent=2, sort_keys=True, allow_nan=False) + "\n"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, _serialize_json_payload(payload))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(__file__).resolve().parents[1] / candidate
    return candidate.resolve(strict=False)


def _validate_strategy_replay_artifact_path(
    output_path: Path,
    *,
    cache_dir: str | Path,
) -> None:
    resolved_output = _resolve_project_path(output_path)
    repo_root = Path(__file__).resolve().parents[1]
    data_root = (repo_root / "data").resolve(strict=False)
    canonical_runtime_cache = (repo_root / STRATEGY_REPLAY_CACHE_DIR).resolve(strict=False)
    resolved_cache = _resolve_project_path(cache_dir)
    if _is_relative_to(resolved_cache, data_root) and not _is_relative_to(resolved_cache, canonical_runtime_cache):
        raise ValueError(
            "Strategy replay cache_dir must stay under data/runtime_cache/strategy_replay for repo data writes."
        )
    if _is_relative_to(resolved_output, data_root) and not _is_relative_to(resolved_output, canonical_runtime_cache):
        raise ValueError(
            "Strategy replay artifacts are display-only and may not be written under data/ "
            "outside data/runtime_cache/strategy_replay."
        )


def _ticker_for_permno(permno: Any, ticker_map: dict[int, str]) -> str:
    try:
        normalized = int(permno)
    except (TypeError, ValueError):
        normalized = permno
    ticker = ticker_map.get(normalized)
    return str(ticker) if ticker else str(permno)


def _replay_matrix_to_artifact_rows(
    frame: pd.DataFrame,
    *,
    matrix_name: str,
    inputs: StrategyReplayInputs,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=STRATEGY_REPLAY_ARTIFACT_COLUMNS)
    wide = frame.copy()
    wide.columns = [str(col) for col in wide.columns]
    wide.insert(0, "date", wide.index)
    wide.insert(0, "matrix", matrix_name)
    wide["as_of_date"] = inputs.as_of_date.date().isoformat()
    wide["cache_key"] = inputs.cache_key
    wide["artifact_scope"] = "display_only_strategy_replay_input"
    leading = STRATEGY_REPLAY_ARTIFACT_COLUMNS
    asset_cols = [col for col in wide.columns if col not in leading]
    return wide[leading + asset_cols].reset_index(drop=True)


def _empty_strategy_replay_artifact_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=STRATEGY_REPLAY_ARTIFACT_COLUMNS)


def strategy_replay_inputs_to_frame(inputs: StrategyReplayInputs) -> pd.DataFrame:
    """Pack replay matrices into one compact display-only wide artifact frame."""
    prices = _normalize_replay_matrix(inputs.prices)
    returns = _normalize_replay_matrix(inputs.returns)
    if prices.empty and returns.empty:
        return _empty_strategy_replay_artifact_frame()

    parts = [
        _replay_matrix_to_artifact_rows(prices, matrix_name="price", inputs=inputs),
        _replay_matrix_to_artifact_rows(returns, matrix_name="return", inputs=inputs),
    ]
    artifact = pd.concat([part for part in parts if not part.empty], ignore_index=True, sort=False)
    if artifact.empty:
        return _empty_strategy_replay_artifact_frame()
    asset_cols = sorted([col for col in artifact.columns if col not in STRATEGY_REPLAY_ARTIFACT_COLUMNS])
    return artifact[STRATEGY_REPLAY_ARTIFACT_COLUMNS + asset_cols].sort_values(["matrix", "date"]).reset_index(drop=True)


def write_strategy_replay_artifact_atomic(
    inputs: StrategyReplayInputs,
    *,
    artifact_path: str | Path | None = None,
    cache_dir: str | Path = STRATEGY_REPLAY_CACHE_DIR,
) -> dict[str, Path | str]:
    """
    Persist a display-only replay artifact with temp-file replacement.

    The artifact is a cache/rendering aid. It is not canonical market data and
    should stay under `data/runtime_cache/strategy_replay` unless a caller
    explicitly points it at a temporary test path.
    """
    output_path = (
        Path(artifact_path)
        if artifact_path is not None
        else strategy_replay_cache_path(inputs.cache_signature, cache_dir=cache_dir)
    )
    _validate_strategy_replay_artifact_path(output_path, cache_dir=cache_dir)
    artifact = strategy_replay_inputs_to_frame(inputs)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    date_values = pd.to_datetime(artifact["date"], errors="coerce") if "date" in artifact else pd.Series(dtype="datetime64[ns]")
    manifest = {
        "artifact_type": "display_only_strategy_replay_input",
        "display_only": True,
        "canonical_market_data_write": False,
        "cache_key": inputs.cache_key,
        "cache_signature": inputs.cache_signature,
        "metadata": inputs.metadata,
        "ticker_map": {str(k): str(v) for k, v in sorted(inputs.ticker_map.items())},
        "row_count": int(len(artifact)),
        "date_range": {
            "start": None if date_values.empty or date_values.isna().all() else str(date_values.min().date()),
            "end": None if date_values.empty or date_values.isna().all() else str(date_values.max().date()),
        },
    }
    manifest_text = _serialize_json_payload(manifest)
    _atomic_write_parquet(output_path, artifact, index=False)
    _atomic_write_text(manifest_path, manifest_text)
    return {
        "artifact_path": output_path,
        "manifest_path": manifest_path,
        "cache_key": inputs.cache_key,
    }


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
    if live_prices.empty:
        return live_prices
    if local_prices.empty:
        return pd.DataFrame(index=live_prices.index)
    local_prices = clean_price_frame(local_prices)
    live_prices = clean_price_frame(live_prices)
    if live_prices.empty:
        return live_prices
    if local_prices.empty:
        return pd.DataFrame(index=live_prices.index)
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
            continue

        overlap = local_series.index.intersection(live_series.index)
        if len(overlap) > 0:
            anchor_date = overlap.max()
            local_anchor = float(local_series.loc[anchor_date])
            live_anchor = float(live_series.loc[anchor_date])
        else:
            continue

        if np.isfinite(local_anchor) and np.isfinite(live_anchor) and live_anchor > 0:
            scaled[col] = live_series * (local_anchor / live_anchor)

    cleaned = clean_price_frame(scaled)
    _scale_cache_put(cache_key, cleaned)
    return cleaned


def refresh_selected_prices_with_live_overlay(
    prices_selected: pd.DataFrame,
    ticker_map: dict,
    *,
    schedule_background: bool = True,
    cache_dir: str | Path = OPTIMIZER_LIVE_OVERLAY_CACHE_DIR,
    required_latest: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.Timestamp | None, str]:
    """
    Stitch a non-canonical live display overlay onto local TRI optimizer prices.

    This path is intentionally in-memory and display freshness only; it does not
    write canonical market data or promote yfinance as evidence.
    """
    prices_selected = clean_price_frame(prices_selected)
    if prices_selected.empty:
        return prices_selected, None, "local-empty"
    selected_columns = list(prices_selected.columns)
    local_endpoint = price_frame_latest_date(prices_selected)
    if local_endpoint is None:
        return prices_selected.iloc[:, 0:0], None, "local-empty"
    local_fresh, latest_local, stale_local = filter_price_frame_to_fresh_columns(
        prices_selected,
        selected_columns,
        required_latest=required_latest,
    )
    if local_fresh.empty:
        latest_local = None

    ticker_by_permno: dict[object, str] = {}
    for permno in prices_selected.columns:
        ticker = (ticker_map or {}).get(permno)
        if ticker:
            ticker_by_permno[permno] = str(ticker).upper()

    if not ticker_by_permno:
        source = "local" if not stale_local else "local_stale_dropped"
        return local_fresh, latest_local, source

    start = pd.Timestamp(local_endpoint).normalize() - pd.Timedelta(days=10)
    live_close = download_recent_close_prices(
        tuple(ticker_by_permno.values()),
        start.strftime("%Y-%m-%d"),
        cache_dir=cache_dir,
        schedule_background=schedule_background,
    )
    if live_close.empty:
        source = "local" if not stale_local else "local_stale_dropped"
        return local_fresh, latest_local, source

    live_by_permno = pd.DataFrame(index=live_close.index)
    for permno, ticker in ticker_by_permno.items():
        if ticker in live_close.columns:
            live_by_permno[permno] = live_close[ticker]
    live_by_permno = clean_price_frame(live_by_permno)
    if live_by_permno.empty:
        source = "local" if not stale_local else "local_stale_dropped"
        return local_fresh, latest_local, source
    live_by_permno = scale_live_overlay_to_local(prices_selected, live_by_permno)
    if live_by_permno.empty:
        source = "local" if not stale_local else "local_stale_dropped"
        return local_fresh, latest_local, source

    refreshed = live_by_permno.combine_first(prices_selected).sort_index()
    refreshed = clean_price_frame(refreshed)
    live_latest = price_frame_latest_date(refreshed)
    if required_latest is not None and live_latest is not None:
        endpoint = max(pd.Timestamp(required_latest).normalize(), pd.Timestamp(live_latest).normalize())
    else:
        endpoint = live_latest if live_latest is not None else latest_local
    refreshed_fresh, latest_live, stale_live = filter_price_frame_to_fresh_columns(
        refreshed,
        selected_columns,
        required_latest=endpoint,
    )
    if refreshed_fresh.empty:
        latest_live = None
    source = "live" if not stale_live else "live_stale_dropped"
    return refreshed_fresh, latest_live, source


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
    returns_wide, prices_wide, macro, ticker_map, fundamentals_wide = load_dashboard_data(
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



# ---------------------------------------------------------------------------
# Batched PIT Replay Loader (v6)
# ---------------------------------------------------------------------------

@dataclass
class BatchedPITReplayData:
    """One raw load + per-date PIT membership for forward-walk replay."""

    raw_prices: pd.DataFrame
    raw_returns: pd.DataFrame
    membership_dates: list[str]  # sorted iso dates with membership data
    membership_index: dict[str, set[int]]  # iso_date -> set of permnos
    ticker_map: dict[int, str]
    trading_dates: list[pd.Timestamp]
    metadata: dict[str, Any] = field(default_factory=dict)


def load_replay_date_index(
    processed_dir: str | Path = "./data/processed",
    start_date: Any = None,
    end_date: Any = None,
) -> list[pd.Timestamp]:
    """Return sorted unique trading dates from prices_tri.parquet via DuckDB."""
    processed_root = Path(processed_dir)
    tri_path = processed_root / "prices_tri.parquet"
    prices_path = processed_root / "prices.parquet"
    src = str(tri_path) if tri_path.exists() else str(prices_path)
    if not Path(src).exists():
        return []
    con = duckdb.connect()
    try:
        where_parts = []
        if start_date is not None:
            s = pd.Timestamp(pd.to_datetime(start_date, errors="coerce")).strftime("%Y-%m-%d")
            where_parts.append(f"CAST(date AS DATE) >= DATE '{s}'")
        if end_date is not None:
            e = pd.Timestamp(pd.to_datetime(end_date, errors="coerce")).strftime("%Y-%m-%d")
            where_parts.append(f"CAST(date AS DATE) <= DATE '{e}'")
        where_clause = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
        q = f"SELECT DISTINCT CAST(date AS DATE) AS date FROM '{src}'{where_clause} ORDER BY date"
        df = con.execute(q).df()
    finally:
        con.close()
    if df.empty:
        return []
    dates = pd.to_datetime(df["date"], errors="coerce").dropna().sort_values()
    return [pd.Timestamp(d).normalize() for d in dates]


def load_batched_pit_replay_data(
    processed_dir: str | Path = "./data/processed",
    static_dir: str | Path = "./data/static",
    start_date: Any = None,
    end_date: Any = None,
    start_year: int = 2000,
    selected_permnos: Iterable[Any] | None = None,
) -> BatchedPITReplayData:
    """Load PIT membership proof plus raw prices for the requested replay scope."""
    processed_root = Path(processed_dir)
    universe_path = processed_root / "universe_r3000_daily.parquet"
    tri_path = processed_root / "prices_tri.parquet"
    prices_path = processed_root / "prices.parquet"
    tickers_path = processed_root / "tickers.parquet"

    price_src = str(tri_path) if tri_path.exists() else str(prices_path)
    has_tri = tri_path.exists()
    if not Path(price_src).exists():
        raise RuntimeError(f"No price source found at {tri_path} or {prices_path}")
    if not universe_path.exists():
        raise RuntimeError(f"universe_r3000_daily.parquet not found at {universe_path}")

    start_ts = pd.Timestamp(pd.to_datetime(start_date, errors="coerce")).normalize() if start_date else pd.Timestamp(f"{start_year}-01-01")
    end_ts = pd.Timestamp(pd.to_datetime(end_date, errors="coerce")).normalize() if end_date else pd.Timestamp("2099-12-31")
    start_str = start_ts.strftime("%Y-%m-%d")
    end_str = end_ts.strftime("%Y-%m-%d")
    selected_permno_set: set[int] | None = None
    if selected_permnos is not None:
        selected_permno_set = set()
        for raw_permno in selected_permnos:
            parsed = pd.to_numeric(pd.Series([raw_permno]), errors="coerce").iloc[0]
            if pd.notna(parsed) and np.isfinite(float(parsed)):
                selected_permno_set.add(int(parsed))

    con = duckdb.connect()
    try:
        # 1. Load membership for the window
        mem_df = con.execute(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno
            FROM '{universe_path}'
            WHERE CAST(date AS DATE) >= DATE '{start_str}'
              AND CAST(date AS DATE) <= DATE '{end_str}'
            """
        ).df()

        if mem_df.empty:
            raise RuntimeError("No R3000 membership data in requested date window.")

        mem_df["date"] = pd.to_datetime(mem_df["date"], errors="coerce")
        mem_df = mem_df.dropna(subset=["date"])
        mem_df["permno"] = pd.to_numeric(mem_df["permno"], errors="coerce").dropna().astype(int)

        # Build membership index
        membership_index: dict[str, set[int]] = {}
        for d, grp in mem_df.groupby(mem_df["date"].dt.normalize()):
            membership_index[pd.Timestamp(d).date().isoformat()] = set(grp["permno"].tolist())
        membership_dates = sorted(membership_index.keys())

        # Union of all permnos in window. This remains the PIT membership proof
        # even when price loading is limited to the selected replay assets.
        union_permnos = sorted(set(mem_df["permno"].tolist()))
        price_permnos = (
            sorted(set(union_permnos).intersection(selected_permno_set))
            if selected_permno_set is not None
            else union_permnos
        )

        # 2. Load prices for requested replay permnos in date range
        batch_size = 250
        price_col = "tri" if has_tri else "adj_close"
        parts: list[pd.DataFrame] = []
        for i in range(0, len(price_permnos), batch_size):
            batch = price_permnos[i: i + batch_size]
            batch_list = ",".join(str(int(p)) for p in batch)
            q = f"""
                SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno,
                       CAST(total_ret AS DOUBLE) AS total_ret,
                       CAST({price_col} AS DOUBLE) AS signal_price
                FROM '{price_src}'
                WHERE permno IN ({batch_list})
                  AND CAST(date AS DATE) >= DATE '{start_str}'
                  AND CAST(date AS DATE) <= DATE '{end_str}'
            """
            parts.append(con.execute(q).df())

        # 3. Load ticker map
        ticker_map: dict[int, str] = {}
        if tickers_path.exists():
            tmap = con.execute(
                f"SELECT CAST(permno AS BIGINT) AS permno, ticker FROM '{tickers_path}'"
            ).df()
            ticker_map = {int(r["permno"]): str(r["ticker"]).upper().strip() for _, r in tmap.iterrows() if pd.notna(r["permno"])}
    finally:
        con.close()

    if not parts:
        raw_prices = pd.DataFrame()
        raw_returns = pd.DataFrame()
    else:
        combined = pd.concat(parts, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
        combined = combined.dropna(subset=["date"])
        raw_prices = combined.pivot(index="date", columns="permno", values="signal_price").sort_index()
        raw_returns = combined.pivot(index="date", columns="permno", values="total_ret").sort_index()
        raw_prices.columns = [int(c) for c in raw_prices.columns]
        raw_returns.columns = [int(c) for c in raw_returns.columns]

    trading_dates = [pd.Timestamp(d).normalize() for d in raw_prices.index] if not raw_prices.empty else []

    return BatchedPITReplayData(
        raw_prices=raw_prices,
        raw_returns=raw_returns,
        membership_dates=membership_dates,
        membership_index=membership_index,
        ticker_map=ticker_map,
        trading_dates=trading_dates,
        metadata={
            "permnos_loaded": len(union_permnos),
            "price_permnos_loaded": int(len(raw_prices.columns)) if not raw_prices.empty else 0,
            "price_load_scope": "selected_pit_membership_intersection" if selected_permno_set is not None else "full_pit_membership_union",
            "selected_permnos_requested": sorted(selected_permno_set) if selected_permno_set is not None else None,
            "selected_permnos_in_pit_window": sorted(set(union_permnos).intersection(selected_permno_set)) if selected_permno_set is not None else None,
            "pit_membership_proof": "full_window_membership_index",
            "trading_dates_count": len(trading_dates),
            "membership_dates_count": len(membership_dates),
            "date_range": {"start": start_str, "end": end_str},
        },
    )


def pit_members_for_date(
    batched: BatchedPITReplayData,
    replay_date: pd.Timestamp,
    *,
    max_gap_days: int = 30,
) -> set[int] | None:
    """Return R3000 members as-of replay_date, or None if gap exceeds threshold."""
    date_iso = pd.Timestamp(replay_date).normalize().date().isoformat()
    idx = bisect.bisect_right(batched.membership_dates, date_iso) - 1
    if idx < 0:
        return None
    latest_date = batched.membership_dates[idx]
    gap = (pd.Timestamp(date_iso) - pd.Timestamp(latest_date)).days
    if gap > max_gap_days:
        return None
    return batched.membership_index.get(latest_date, set())


def build_batched_pit_input_loader(
    batched: BatchedPITReplayData,
    *,
    max_membership_gap_days: int = 30,
    max_price_endpoint_gap_days: int = 5,
) -> Callable[..., "StrategyReplayInputs"]:
    """Return an input_loader closure for build_selected_method_replay."""

    def _loader(**kwargs: Any) -> "StrategyReplayInputs":
        replay_date = pd.Timestamp(pd.to_datetime(kwargs["as_of_date"], errors="coerce")).normalize()
        members = pit_members_for_date(batched, replay_date, max_gap_days=max_membership_gap_days)

        if members is None:
            return StrategyReplayInputs(
                as_of_date=replay_date,
                prices=pd.DataFrame(),
                returns=pd.DataFrame(),
                ticker_map={},
                cache_signature={"universe_mode": "r3000_pit", "batched": True},
                cache_key=f"batched_pit_gap_{replay_date.date().isoformat()}",
                metadata={
                    "unavailable_reason": "membership_gap_exceeded",
                    "expected_members": [],
                    "source": "batched_pit_replay",
                    "display_only": True,
                },
            )

        valid_cols = [p for p in members if p in batched.raw_prices.columns]
        if not valid_cols:
            return StrategyReplayInputs(
                as_of_date=replay_date,
                prices=pd.DataFrame(),
                returns=pd.DataFrame(),
                ticker_map={int(p): batched.ticker_map.get(int(p), str(p)) for p in members},
                cache_signature={"universe_mode": "r3000_pit", "batched": True},
                cache_key=f"batched_pit_nopriced_{replay_date.date().isoformat()}",
                metadata={
                    "unavailable_reason": "no_priced_members",
                    "expected_members": sorted(members),
                    "source": "batched_pit_replay",
                    "display_only": True,
                },
            )

        prices_slice_all = batched.raw_prices.loc[batched.raw_prices.index <= replay_date, valid_cols]
        fresh_cols: list[int] = []
        endpoint_by_col: dict[int, str] = {}
        for col in valid_cols:
            series = pd.to_numeric(prices_slice_all[col], errors="coerce")
            series = series.replace([np.inf, -np.inf], np.nan).where(lambda s: s > 0).dropna()
            latest = pd.Timestamp(series.index.max()).normalize() if not series.empty else None
            if latest is not None:
                endpoint_by_col[int(col)] = latest.date().isoformat()
            if price_endpoint_is_fresh(
                latest,
                replay_date,
                max_staleness_days=max_price_endpoint_gap_days,
            ):
                fresh_cols.append(int(col))
        if not fresh_cols:
            return StrategyReplayInputs(
                as_of_date=replay_date,
                prices=pd.DataFrame(),
                returns=pd.DataFrame(),
                ticker_map={int(p): batched.ticker_map.get(int(p), str(p)) for p in members},
                cache_signature={"universe_mode": "r3000_pit", "batched": True},
                cache_key=f"batched_pit_nofresh_{replay_date.date().isoformat()}",
                metadata={
                    "unavailable_reason": "no_fresh_priced_members",
                    "expected_members": sorted(members),
                    "priced_members_before_endpoint_gate": sorted(int(p) for p in valid_cols),
                    "price_endpoint_by_member": endpoint_by_col,
                    "max_price_endpoint_gap_days": int(max_price_endpoint_gap_days),
                    "source": "batched_pit_replay",
                    "display_only": True,
                },
            )

        prices_slice = prices_slice_all.reindex(columns=fresh_cols)
        returns_slice = batched.raw_returns.loc[batched.raw_returns.index <= replay_date, fresh_cols]

        return StrategyReplayInputs(
            as_of_date=replay_date,
            prices=prices_slice,
            returns=returns_slice,
            ticker_map={int(p): batched.ticker_map.get(int(p), str(p)) for p in valid_cols},
            cache_signature={"universe_mode": "r3000_pit", "batched": True},
            cache_key=f"batched_pit_{replay_date.date().isoformat()}",
            metadata={
                "expected_members": sorted(members),
                "priced_member_count": len(fresh_cols),
                "priced_members_before_endpoint_gate": sorted(int(p) for p in valid_cols),
                "price_endpoint_by_member": endpoint_by_col,
                "max_price_endpoint_gap_days": int(max_price_endpoint_gap_days),
                "source": "batched_pit_replay",
                "display_only": True,
            },
        )

    return _loader
