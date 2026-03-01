from __future__ import annotations

from collections import deque
from contextlib import contextmanager
import hashlib
import itertools
import json
import math
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TELEMETRY_PARQUET = PROJECT_ROOT / "data" / "processed" / "execution_microstructure.parquet"
DEFAULT_TELEMETRY_FILLS_PARQUET = PROJECT_ROOT / "data" / "processed" / "execution_microstructure_fills.parquet"
DEFAULT_TELEMETRY_DUCKDB = PROJECT_ROOT / "data" / "processed" / "execution_microstructure.duckdb"
DEFAULT_TELEMETRY_TABLE = "execution_microstructure"
DEFAULT_TELEMETRY_SPOOL = PROJECT_ROOT / "data" / "processed" / "execution_microstructure_spool.jsonl"
SPOOL_RECORD_UID_COLUMN = "_spool_record_uid"
PARQUET_EXPORT_BATCH_ROWS = 50_000
TRAILING_PARTIAL_LINE_STALE_SECONDS = 2.0
SPOOL_APPEND_LOCK_TIMEOUT_SECONDS = 0.001
SPOOL_FLUSH_LOCK_TIMEOUT_SECONDS = 0.010
SPOOL_LOCK_RETRY_SLEEP_SECONDS = 0.001
SPOOL_BUFFER_MAX_RECORDS = 20_000
SPOOL_BUFFER_MAX_BYTES = 64 * 1024 * 1024
SPOOL_BUFFER_DRAIN_BATCH_RECORDS = 1_024
SPOOL_RETRY_BACKOFF_BASE_SECONDS = 0.010
SPOOL_RETRY_BACKOFF_MAX_SECONDS = 0.250
DUCKDB_WAL_AUTOCHECKPOINT_PAGES = 10_000
DUCKDB_CHECKPOINT_INTERVAL_SECONDS = 30.0
ATOMIC_REPLACE_MAX_RETRIES = 8
ATOMIC_REPLACE_BASE_SLEEP_SECONDS = 0.01
HEARTBEAT_ROLLING_WINDOW = 64
HEARTBEAT_MIN_SAMPLES = 12
HEARTBEAT_MAD_SCALE = 1.4826
HEARTBEAT_SIGMA_MULTIPLIER = 4.0
HEARTBEAT_SIGMA_FLOOR_MS = 5.0
HEARTBEAT_BOOTSTRAP_LIMIT_MS = 150.0
HEARTBEAT_MIN_LIMIT_MS = 25.0
HEARTBEAT_HARD_CEILING_MS_DEFAULT = 500.0
HEARTBEAT_HARD_CEILING_ENV = "TZ_EXEC_HEARTBEAT_HARD_CEILING_MS"

_SPOOLER_REGISTRY: dict[tuple[str, str, str, str, str], "_TelemetrySpooler"] = {}
_SPOOLER_REGISTRY_LOCK = threading.Lock()
_DUCKDB_MAINTENANCE_LOCK = threading.Lock()
_DUCKDB_LAST_CHECKPOINT_TS: dict[str, float] = {}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _to_positive_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed <= 0.0:
        return None
    return parsed


def _to_iso_now_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _to_utc_datetime(value: Any) -> datetime | None:
    text = _clean_text(value)
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ms_diff(start: Any, end: Any) -> float | None:
    dt_start = _to_utc_datetime(start)
    dt_end = _to_utc_datetime(end)
    if dt_start is None or dt_end is None:
        return None
    latency_ms = float((dt_end - dt_start).total_seconds() * 1000.0)
    return float(max(0.0, latency_ms))


def _to_non_negative_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed < 0.0:
        return None
    return float(parsed)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(float(v) for v in values)
    count = len(sorted_values)
    midpoint = count // 2
    if count % 2 == 1:
        return float(sorted_values[midpoint])
    return float((sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2.0)


def _resolve_heartbeat_hard_ceiling_ms(override_ms: float | None = None) -> float:
    if override_ms is not None:
        parsed = _to_non_negative_float_or_none(override_ms)
        if parsed is not None and parsed > 0.0:
            return float(max(parsed, HEARTBEAT_MIN_LIMIT_MS))

    env_raw = _clean_text(os.environ.get(HEARTBEAT_HARD_CEILING_ENV))
    env_ms = _to_non_negative_float_or_none(env_raw) if env_raw else None
    if env_ms is not None and env_ms > 0.0:
        return float(max(env_ms, HEARTBEAT_MIN_LIMIT_MS))
    return float(HEARTBEAT_HARD_CEILING_MS_DEFAULT)


def _sanitize_heartbeat_latency_history(
    values: list[float] | tuple[float, ...] | None,
    *,
    window_size: int = HEARTBEAT_ROLLING_WINDOW,
) -> list[float]:
    if not isinstance(values, (list, tuple)):
        return []
    out: list[float] = []
    for raw in values:
        parsed = _to_non_negative_float_or_none(raw)
        if parsed is None:
            continue
        out.append(float(parsed))
    if window_size > 0 and len(out) > int(window_size):
        return out[-int(window_size):]
    return out


def evaluate_heartbeat_freshness(
    *,
    submit_to_ack_latency_ms: float | None,
    latency_history_ms: list[float] | tuple[float, ...] | None = None,
    hard_ceiling_ms: float | None = None,
    window_size: int = HEARTBEAT_ROLLING_WINDOW,
) -> dict[str, Any]:
    limit_window = max(int(window_size), 1)
    history = _sanitize_heartbeat_latency_history(latency_history_ms, window_size=limit_window)
    hard_limit_ms = _resolve_heartbeat_hard_ceiling_ms(hard_ceiling_ms)

    median_ms = _median(history)
    mad_ms: float | None = None
    robust_sigma_ms: float | None = None
    if median_ms is not None:
        mad_candidates = [abs(float(v) - float(median_ms)) for v in history]
        mad_ms = _median(mad_candidates)
        if mad_ms is not None:
            robust_sigma_ms = max(float(mad_ms) * float(HEARTBEAT_MAD_SCALE), float(HEARTBEAT_SIGMA_FLOOR_MS))

    if (
        len(history) >= int(HEARTBEAT_MIN_SAMPLES)
        and median_ms is not None
        and robust_sigma_ms is not None
    ):
        adaptive_limit_ms = float(median_ms + float(HEARTBEAT_SIGMA_MULTIPLIER) * float(robust_sigma_ms))
        mode = "adaptive_mad"
    else:
        adaptive_limit_ms = float(HEARTBEAT_BOOTSTRAP_LIMIT_MS)
        mode = "bootstrap"

    adaptive_limit_ms = float(min(max(adaptive_limit_ms, float(HEARTBEAT_MIN_LIMIT_MS)), hard_limit_ms))

    latency_ms = _to_non_negative_float_or_none(submit_to_ack_latency_ms)
    z_score: float | None = None
    if latency_ms is not None and median_ms is not None and robust_sigma_ms is not None and robust_sigma_ms > 0.0:
        z_score = float((latency_ms - median_ms) / robust_sigma_ms)

    if latency_ms is None:
        decision = "BLOCK"
        reason = "latency_missing"
        is_hard_block = False
    elif latency_ms > hard_limit_ms:
        decision = "BLOCK"
        reason = "hard_ceiling_exceeded"
        is_hard_block = True
    elif latency_ms > adaptive_limit_ms:
        decision = "BLOCK"
        reason = "adaptive_limit_exceeded"
        is_hard_block = False
    else:
        decision = "PASS"
        reason = "within_limit"
        is_hard_block = False

    return {
        "heartbeat_decision": decision,
        "heartbeat_reason": reason,
        "heartbeat_is_blocked": bool(decision == "BLOCK"),
        "heartbeat_is_hard_block": bool(is_hard_block),
        "heartbeat_mode": mode,
        "heartbeat_window_count": int(len(history)),
        "heartbeat_window_median_ms": float(median_ms) if median_ms is not None else None,
        "heartbeat_window_mad_ms": float(mad_ms) if mad_ms is not None else None,
        "heartbeat_robust_sigma_ms": float(robust_sigma_ms) if robust_sigma_ms is not None else None,
        "heartbeat_adaptive_limit_ms": float(adaptive_limit_ms),
        "heartbeat_hard_ceiling_ms": float(hard_limit_ms),
        "heartbeat_latency_ms": float(latency_ms) if latency_ms is not None else None,
        "heartbeat_latency_zscore": float(z_score) if z_score is not None else None,
    }


def annotate_heartbeat_freshness_frame(
    frame: pd.DataFrame,
    *,
    latency_col: str = "latency_ms_submit_to_ack",
    history_ms: list[float] | tuple[float, ...] | None = None,
    window_size: int = HEARTBEAT_ROLLING_WINDOW,
) -> pd.DataFrame:
    if latency_col not in frame.columns:
        raise ValueError(f"missing latency column: {latency_col}")
    if frame.empty:
        return frame.copy()

    out = frame.copy()
    rolling_history = _sanitize_heartbeat_latency_history(history_ms, window_size=max(int(window_size), 1))
    annotations: list[dict[str, Any]] = []
    for raw_latency in out[latency_col].tolist():
        annotation = evaluate_heartbeat_freshness(
            submit_to_ack_latency_ms=_to_non_negative_float_or_none(raw_latency),
            latency_history_ms=rolling_history,
            window_size=max(int(window_size), 1),
        )
        annotations.append(annotation)
        current_latency = _to_non_negative_float_or_none(raw_latency)
        if current_latency is not None:
            rolling_history.append(float(current_latency))
            if len(rolling_history) > max(int(window_size), 1):
                rolling_history = rolling_history[-max(int(window_size), 1):]

    annotation_df = pd.DataFrame(annotations, index=out.index)
    for column in annotation_df.columns:
        out[column] = annotation_df[column]
    return out


def _load_recent_submit_to_ack_history_ms(
    *,
    duckdb_path: Path,
    table_name: str,
    window_size: int = HEARTBEAT_ROLLING_WINDOW,
) -> list[float]:
    if not duckdb_path.exists():
        return []
    table = _validate_table_name(table_name)
    limit = max(int(window_size), 1)

    rows: list[tuple[Any, ...]] = []
    with duckdb.connect(str(duckdb_path)) as conn:
        table_columns = _duckdb_table_columns(conn, table)
        event_time_columns = [
            column
            for column in (
                "arrival_ts",
                "submit_sent_ts",
                "broker_ack_ts",
                "filled_at",
                "execution_ts",
                "captured_at_utc",
                "created_at",
                "updated_at",
            )
            if column in table_columns
        ]
        if not event_time_columns:
            return []

        tie_breakers: list[str] = []
        for column in (SPOOL_RECORD_UID_COLUMN, "client_order_id", "order_id"):
            if column in table_columns:
                tie_breakers.append(f"{_quote_identifier(column)} DESC")
        if "captured_at_utc" in table_columns:
            tie_breakers.append(f"{_quote_identifier('captured_at_utc')} DESC")
        tie_breaker_sql = f", {', '.join(tie_breakers)}" if tie_breakers else ""

        queries: list[str] = []
        for cast_target in ("TIMESTAMPTZ", "TIMESTAMP"):
            event_time_expr = "COALESCE(" + ", ".join(
                f"TRY_CAST({_quote_identifier(column)} AS {cast_target})"
                for column in event_time_columns
            ) + ")"
            queries.append(
                f"""
                SELECT latency_ms_submit_to_ack
                FROM {table}
                WHERE latency_ms_submit_to_ack IS NOT NULL
                  AND ({event_time_expr}) IS NOT NULL
                ORDER BY {event_time_expr} DESC NULLS LAST{tie_breaker_sql}
                LIMIT {limit}
                """
            )

        for sql in queries:
            try:
                rows = conn.execute(sql).fetchall()
                break
            except duckdb.Error:
                rows = []
                continue

    raw = [row[0] for row in rows if isinstance(row, tuple) and len(row) > 0]
    raw = list(reversed(raw))
    return _sanitize_heartbeat_latency_history(raw, window_size=limit)


def _resolve_latency_anchors(result: dict[str, Any]) -> tuple[str | None, str | None]:
    submit_sent_ts = (
        _clean_text(result.get("submit_sent_ts"))
        or _clean_text(result.get("submitted_at"))
        or _clean_text(result.get("created_at"))
        or _clean_text(result.get("updated_at"))
        or None
    )
    broker_ack_ts = (
        _clean_text(result.get("broker_ack_ts"))
        or _clean_text(result.get("ack_ts"))
        or _clean_text(result.get("updated_at"))
        or None
    )
    return submit_sent_ts, broker_ack_ts


def _summarize_partial_fills(partial_fills: list[dict[str, Any]]) -> dict[str, Any]:
    if not partial_fills:
        return {
            "fill_count": 0,
            "fill_qty": None,
            "fill_notional": None,
            "fill_vwap": None,
            "first_fill_ts": None,
            "last_fill_ts": None,
        }

    fill_count = 0
    fill_qty = 0.0
    fill_notional = 0.0
    fill_timestamps: list[str] = []
    for row in partial_fills:
        if not isinstance(row, dict):
            continue
        qty = _to_positive_float_or_none(row.get("fill_qty"))
        price = _to_positive_float_or_none(row.get("fill_price"))
        if qty is None or price is None:
            continue
        fill_count += 1
        fill_qty += float(qty)
        fill_notional += float(qty * price)
        fill_ts = _clean_text(row.get("fill_ts"))
        if fill_ts:
            fill_timestamps.append(fill_ts)

    fill_vwap = (fill_notional / fill_qty) if fill_qty > 0.0 else None
    return {
        "fill_count": int(fill_count),
        "fill_qty": float(fill_qty) if fill_qty > 0.0 else None,
        "fill_notional": float(fill_notional) if fill_notional > 0.0 else None,
        "fill_vwap": float(fill_vwap) if fill_vwap is not None else None,
        "first_fill_ts": min(fill_timestamps) if fill_timestamps else None,
        "last_fill_ts": max(fill_timestamps) if fill_timestamps else None,
    }


def _calc_execution_cost_metrics(
    *,
    side: str,
    arrival_price: float | None,
    fill_vwap: float | None,
    fill_qty: float | None,
) -> dict[str, float | None]:
    side_l = _clean_text(side).lower()
    if side_l not in {"buy", "sell"}:
        return {
            "implementation_shortfall_dollars": None,
            "slippage_bps": None,
        }
    if arrival_price is None or fill_vwap is None or fill_qty is None:
        return {
            "implementation_shortfall_dollars": None,
            "slippage_bps": None,
        }
    if arrival_price <= 0.0 or fill_qty <= 0.0:
        return {
            "implementation_shortfall_dollars": None,
            "slippage_bps": None,
        }

    if side_l == "buy":
        delta = float(fill_vwap - arrival_price)
    else:
        delta = float(arrival_price - fill_vwap)

    return {
        "implementation_shortfall_dollars": float(delta * fill_qty),
        "slippage_bps": float((delta / arrival_price) * 10_000.0),
    }


def _extract_fill_rows(
    *,
    base_order_row: dict[str, Any],
    partial_fills: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    batch_id = _clean_text(base_order_row.get("batch_id"))
    client_order_id = _clean_text(base_order_row.get("client_order_id"))
    symbol = _clean_text(base_order_row.get("symbol")).upper()
    side = _clean_text(base_order_row.get("side")).lower()

    for idx, fill in enumerate(partial_fills, start=1):
        if not isinstance(fill, dict):
            continue
        fill_qty = _to_positive_float_or_none(fill.get("fill_qty"))
        fill_price = _to_positive_float_or_none(fill.get("fill_price"))
        if fill_qty is None or fill_price is None:
            continue
        out.append(
            {
                "captured_at_utc": _to_iso_now_ms(),
                "batch_id": batch_id,
                "client_order_id": client_order_id,
                "symbol": symbol,
                "side": side,
                "fill_index": int(fill.get("fill_index") or idx),
                "fill_ts": _clean_text(fill.get("fill_ts")) or None,
                "fill_qty": float(fill_qty),
                "fill_price": float(fill_price),
                "fill_notional": float(fill_qty * fill_price),
                "fill_venue": _clean_text(fill.get("fill_venue")) or None,
                "fill_source": _clean_text(fill.get("source")) or None,
            }
        )
    return out


def build_execution_telemetry_rows(
    execute_results: list[dict[str, Any]],
    *,
    batch_id: str,
    strategy: str,
    submit_to_ack_history_ms: list[float] | tuple[float, ...] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    order_rows: list[dict[str, Any]] = []
    fill_rows: list[dict[str, Any]] = []
    rolling_submit_to_ack_history = _sanitize_heartbeat_latency_history(
        submit_to_ack_history_ms,
        window_size=HEARTBEAT_ROLLING_WINDOW,
    )

    for row in execute_results:
        if not isinstance(row, dict):
            continue
        order_map = row.get("order", {})
        result_map = row.get("result", {})
        order = order_map if isinstance(order_map, dict) else {}
        result = result_map if isinstance(result_map, dict) else {}

        fill_summary = result.get("fill_summary", {})
        if not isinstance(fill_summary, dict):
            fill_summary = {}
        partial_fills = result.get("partial_fills", [])
        if not isinstance(partial_fills, list):
            partial_fills = []
        partial_fill_summary = _summarize_partial_fills(partial_fills)

        arrival_price = _to_positive_float_or_none(order.get("arrival_price"))
        fill_vwap = _to_positive_float_or_none(fill_summary.get("fill_vwap"))
        if fill_vwap is None:
            fill_vwap = _to_positive_float_or_none(partial_fill_summary.get("fill_vwap"))
        if fill_vwap is None:
            fill_vwap = _to_positive_float_or_none(result.get("filled_avg_price"))

        fill_qty = _to_positive_float_or_none(fill_summary.get("fill_qty"))
        if fill_qty is None:
            fill_qty = _to_positive_float_or_none(partial_fill_summary.get("fill_qty"))
        if fill_qty is None:
            fill_qty = _to_positive_float_or_none(result.get("filled_qty"))
        fill_notional = _to_positive_float_or_none(fill_summary.get("fill_notional"))
        if fill_notional is None:
            fill_notional = _to_positive_float_or_none(partial_fill_summary.get("fill_notional"))
        first_fill_ts = (
            _clean_text(fill_summary.get("first_fill_ts"))
            or _clean_text(partial_fill_summary.get("first_fill_ts"))
            or (_clean_text(result.get("filled_at")) or None)
        )
        last_fill_ts = (
            _clean_text(fill_summary.get("last_fill_ts"))
            or _clean_text(partial_fill_summary.get("last_fill_ts"))
            or (_clean_text(result.get("filled_at")) or None)
        )
        fill_count = int(fill_summary.get("fill_count") or 0)
        if fill_count <= 0:
            fill_count = int(partial_fill_summary.get("fill_count") or 0)
        fills_for_rows: list[dict[str, Any]] = [
            fill for fill in partial_fills if isinstance(fill, dict)
        ]
        if (
            not fills_for_rows
            and fill_count > 0
            and fill_qty is not None
            and fill_vwap is not None
        ):
            fills_for_rows = [
                {
                    "fill_index": 1,
                    "fill_qty": float(fill_qty),
                    "fill_price": float(fill_vwap),
                    "fill_ts": first_fill_ts,
                    "fill_venue": None,
                    "source": "summary_fallback",
                }
            ]

        side = _clean_text(order.get("side") or result.get("side", "")).lower()
        cost_metrics = _calc_execution_cost_metrics(
            side=side,
            arrival_price=arrival_price,
            fill_vwap=fill_vwap,
            fill_qty=fill_qty,
        )
        submit_sent_ts, broker_ack_ts = _resolve_latency_anchors(result)
        latency_ms_command_to_submit = _ms_diff(order.get("arrival_ts"), submit_sent_ts)
        latency_ms_submit_to_ack = _ms_diff(submit_sent_ts, broker_ack_ts)
        latency_ms_ack_to_first_fill = _ms_diff(broker_ack_ts, first_fill_ts)
        latency_ms_command_to_first_fill = _ms_diff(order.get("arrival_ts"), first_fill_ts)
        heartbeat_metrics = evaluate_heartbeat_freshness(
            submit_to_ack_latency_ms=latency_ms_submit_to_ack,
            latency_history_ms=rolling_submit_to_ack_history,
        )

        order_row = {
            "captured_at_utc": _to_iso_now_ms(),
            "batch_id": _clean_text(batch_id),
            "strategy": _clean_text(strategy),
            "client_order_id": _clean_text(order.get("client_order_id") or result.get("client_order_id", "")),
            "order_id": _clean_text(result.get("order_id")) or None,
            "symbol": _clean_text(order.get("symbol") or result.get("symbol", "")).upper(),
            "side": side,
            "qty": _to_positive_float_or_none(order.get("qty")),
            "order_type": _clean_text(order.get("order_type") or result.get("order_type", "")).lower() or None,
            "limit_price": _to_positive_float_or_none(order.get("limit_price") if order.get("limit_price") is not None else result.get("limit_price")),
            "arrival_ts": _clean_text(order.get("arrival_ts")) or None,
            "arrival_quote_ts": _clean_text(order.get("arrival_quote_ts")) or None,
            "arrival_price": arrival_price,
            "arrival_bid_price": _to_positive_float_or_none(order.get("arrival_bid_price")),
            "arrival_ask_price": _to_positive_float_or_none(order.get("arrival_ask_price")),
            "submit_sent_ts": submit_sent_ts,
            "broker_ack_ts": broker_ack_ts,
            "broker_submitted_at": _clean_text(result.get("submitted_at")) or None,
            "broker_created_at": _clean_text(result.get("created_at")) or None,
            "broker_updated_at": _clean_text(result.get("updated_at")) or None,
            "filled_at": _clean_text(result.get("filled_at")) or None,
            "first_fill_ts": first_fill_ts,
            "last_fill_ts": last_fill_ts,
            "fill_count": fill_count,
            "fill_qty": fill_qty,
            "fill_vwap": fill_vwap,
            "fill_notional": fill_notional,
            "implementation_shortfall_dollars": cost_metrics["implementation_shortfall_dollars"],
            "slippage_bps": cost_metrics["slippage_bps"],
            "latency_ms_command_to_submit": latency_ms_command_to_submit,
            "latency_ms_submit_to_ack": latency_ms_submit_to_ack,
            "latency_ms_ack_to_first_fill": latency_ms_ack_to_first_fill,
            "latency_ms_command_to_first_fill": latency_ms_command_to_first_fill,
            "heartbeat_decision": heartbeat_metrics["heartbeat_decision"],
            "heartbeat_reason": heartbeat_metrics["heartbeat_reason"],
            "heartbeat_is_blocked": heartbeat_metrics["heartbeat_is_blocked"],
            "heartbeat_is_hard_block": heartbeat_metrics["heartbeat_is_hard_block"],
            "heartbeat_mode": heartbeat_metrics["heartbeat_mode"],
            "heartbeat_window_count": heartbeat_metrics["heartbeat_window_count"],
            "heartbeat_window_median_ms": heartbeat_metrics["heartbeat_window_median_ms"],
            "heartbeat_window_mad_ms": heartbeat_metrics["heartbeat_window_mad_ms"],
            "heartbeat_robust_sigma_ms": heartbeat_metrics["heartbeat_robust_sigma_ms"],
            "heartbeat_adaptive_limit_ms": heartbeat_metrics["heartbeat_adaptive_limit_ms"],
            "heartbeat_hard_ceiling_ms": heartbeat_metrics["heartbeat_hard_ceiling_ms"],
            "heartbeat_latency_ms": heartbeat_metrics["heartbeat_latency_ms"],
            "heartbeat_latency_zscore": heartbeat_metrics["heartbeat_latency_zscore"],
            "status": _clean_text(result.get("status")) or None,
            "ok": bool(result.get("ok") is True),
            "error": _clean_text(result.get("error")) or None,
            "recovered": bool(result.get("recovered") is True),
            "recovery_reason": _clean_text(result.get("recovery_reason")) or None,
        }
        order_rows.append(order_row)
        fill_rows.extend(_extract_fill_rows(base_order_row=order_row, partial_fills=fills_for_rows))
        if latency_ms_submit_to_ack is not None:
            rolling_submit_to_ack_history.append(float(latency_ms_submit_to_ack))
            if len(rolling_submit_to_ack_history) > int(HEARTBEAT_ROLLING_WINDOW):
                rolling_submit_to_ack_history = rolling_submit_to_ack_history[-int(HEARTBEAT_ROLLING_WINDOW):]

    return order_rows, fill_rows


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.{os.getpid()}.{int(datetime.now(timezone.utc).timestamp() * 1000)}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace_with_retry(tmp_path, path)
        _fsync_parent_dir_if_possible(path.parent)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.{os.getpid()}.{int(datetime.now(timezone.utc).timestamp() * 1000)}.tmp")
    try:
        df.to_parquet(tmp_path, index=False)
        _fsync_path_if_possible(tmp_path)
        _atomic_replace_with_retry(tmp_path, path)
        _fsync_parent_dir_if_possible(path.parent)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_replace_with_retry(
    src: Path,
    dst: Path,
    *,
    max_retries: int = ATOMIC_REPLACE_MAX_RETRIES,
    base_sleep_seconds: float = ATOMIC_REPLACE_BASE_SLEEP_SECONDS,
) -> None:
    attempts = max(int(max_retries), 1)
    for attempt in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt >= attempts - 1:
                raise
            time.sleep(max(float(base_sleep_seconds), 0.001) * float(attempt + 1))


def _fsync_path_if_possible(path: Path) -> None:
    try:
        with path.open("rb") as handle:
            os.fsync(handle.fileno())
    except OSError:
        return


def _fsync_parent_dir_if_possible(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _stable_row_uid_fallback(row: dict[str, Any], *, prefix: str, idx: int) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha1(f"{prefix}:{idx}:{payload}".encode("utf-8")).hexdigest()


def _ensure_spool_uid_column(df: pd.DataFrame, *, prefix: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if SPOOL_RECORD_UID_COLUMN not in out.columns:
        records = out.to_dict("records")
        out[SPOOL_RECORD_UID_COLUMN] = [
            _stable_row_uid_fallback(record, prefix=prefix, idx=idx)
            for idx, record in enumerate(records)
        ]
        return out

    normalized: list[str] = []
    records = out.to_dict("records")
    for idx, record in enumerate(records):
        raw = _clean_text(record.get(SPOOL_RECORD_UID_COLUMN))
        if raw:
            normalized.append(raw)
            continue
        normalized.append(_stable_row_uid_fallback(record, prefix=prefix, idx=idx))
    out[SPOOL_RECORD_UID_COLUMN] = normalized
    return out


def _quote_identifier(identifier: str) -> str:
    return f'"{str(identifier).replace(chr(34), chr(34) * 2)}"'


def _duckdb_table_columns(conn: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    columns: list[str] = []
    for row in rows:
        if not isinstance(row, tuple) or len(row) < 2:
            continue
        name = _clean_text(row[1])
        if name:
            columns.append(name)
    return columns


def _append_duckdb_table_rows(
    *,
    conn: duckdb.DuckDBPyConnection,
    table: str,
    frame: pd.DataFrame,
    register_name: str,
) -> int:
    if frame.empty:
        return 0
    deduped = frame.drop_duplicates(subset=[SPOOL_RECORD_UID_COLUMN], keep="first")
    conn.register(register_name, deduped)
    try:
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM {register_name} LIMIT 0")
        conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {SPOOL_RECORD_UID_COLUMN} VARCHAR")

        table_columns = _duckdb_table_columns(conn, table)
        table_column_set = set(table_columns)
        register_columns = [str(column) for column in deduped.columns]
        register_types = conn.execute(f"DESCRIBE SELECT * FROM {register_name}").fetchall()
        for row in register_types:
            if not isinstance(row, tuple) or len(row) < 2:
                continue
            column_name = _clean_text(row[0])
            column_type = _clean_text(row[1]) or "VARCHAR"
            if not column_name or column_name in table_column_set:
                continue
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {_quote_identifier(column_name)} {column_type}"
            )

        table_columns = _duckdb_table_columns(conn, table)
        table_column_set = set(table_columns)
        insert_columns = [column for column in register_columns if column in table_column_set]
        if not insert_columns:
            return 0

        insert_column_sql = ", ".join(_quote_identifier(column) for column in insert_columns)
        select_column_sql = ", ".join(f"n.{_quote_identifier(column)}" for column in insert_columns)
        spool_uid_col = _quote_identifier(SPOOL_RECORD_UID_COLUMN)
        before_count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        conn.execute(
            f"""
            INSERT INTO {table} ({insert_column_sql})
            SELECT {select_column_sql}
            FROM {register_name} n
            WHERE NOT EXISTS (
                SELECT 1
                FROM {table} t
                WHERE t.{spool_uid_col} = n.{spool_uid_col}
            )
            """
        )
        after_count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return max(after_count - before_count, 0)
    finally:
        conn.unregister(register_name)


def _parquet_export_cursor_path(parquet_path: Path) -> Path:
    return parquet_path.with_suffix(f"{parquet_path.suffix}.cursor")


def _read_parquet_export_cursor(cursor_path: Path) -> int:
    return _read_spool_offset(cursor_path)


def _write_parquet_export_cursor(cursor_path: Path, row_count: int) -> None:
    _write_spool_offset(cursor_path, row_count)


def _append_parquet_legacy_file(path: Path, rows_df: pd.DataFrame) -> int:
    if rows_df.empty:
        return 0
    existing_df = pd.DataFrame()
    if path.exists():
        existing_df = pd.read_parquet(path)
    existing_count = int(len(existing_df))
    merged_df = pd.concat([existing_df, rows_df], ignore_index=True)
    dedupe_subset = [
        column
        for column in ("record_id", "uid", SPOOL_RECORD_UID_COLUMN)
        if column in merged_df.columns
    ]
    for key in dedupe_subset:
        key_series = merged_df[key]
        key_text = key_series.astype(str).str.strip().str.lower()
        has_key = key_series.notna() & (~key_text.isin({"", "none", "null", "nan"}))
        with_key = merged_df.loc[has_key]
        without_key = merged_df.loc[~has_key]
        if not with_key.empty:
            with_key = with_key.drop_duplicates(subset=[key], keep="first")
        merged_df = pd.concat([without_key, with_key], ignore_index=True)
    _atomic_write_parquet(merged_df, path)
    return int(max(len(merged_df) - existing_count, 0))


def _export_duckdb_table_to_parquet(
    *,
    duckdb_path: Path,
    table_name: str,
    parquet_path: Path,
    batch_rows: int = PARQUET_EXPORT_BATCH_ROWS,
) -> int:
    table = _validate_table_name(table_name)
    if not duckdb_path.exists():
        return 0

    cursor_path = _parquet_export_cursor_path(parquet_path)
    with duckdb.connect(str(duckdb_path)) as conn:
        try:
            total_rows = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        except duckdb.Error:
            return 0

        start_row = _read_parquet_export_cursor(cursor_path)
        if start_row > total_rows:
            start_row = 0
            _write_parquet_export_cursor(cursor_path, 0)

        if start_row >= total_rows:
            return 0

        end_row = min(start_row + max(int(batch_rows), 1), total_rows)
        write_count = int(end_row - start_row)
        table_columns = _duckdb_table_columns(conn, table)
        export_df: pd.DataFrame | None = None
        candidate_queries: list[str] = [f"SELECT * FROM {table} ORDER BY rowid LIMIT ? OFFSET ?"]
        if SPOOL_RECORD_UID_COLUMN in table_columns:
            uid_col = _quote_identifier(SPOOL_RECORD_UID_COLUMN)
            candidate_queries.append(f"SELECT * FROM {table} ORDER BY {uid_col} LIMIT ? OFFSET ?")
        candidate_queries.append(f"SELECT * FROM {table} ORDER BY ALL LIMIT ? OFFSET ?")

        for sql in candidate_queries:
            try:
                export_df = conn.execute(sql, [write_count, start_row]).df()
                break
            except duckdb.Error:
                export_df = None
                continue

        if export_df is None:
            return 0

    if parquet_path.exists() and parquet_path.is_file():
        wrote = _append_parquet_legacy_file(parquet_path, export_df)
        _write_parquet_export_cursor(cursor_path, end_row)
        return wrote

    parquet_path.mkdir(parents=True, exist_ok=True)
    part_path = parquet_path / f"part-{start_row:020d}-{end_row:020d}.parquet"
    if not part_path.exists():
        _atomic_write_parquet(export_df, part_path)
    _write_parquet_export_cursor(cursor_path, end_row)
    return write_count


def _validate_table_name(table_name: str) -> str:
    name = _clean_text(table_name)
    if not name:
        raise ValueError("table_name must not be empty")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"invalid DuckDB table name: {table_name}")
    return name


def _duckdb_maintenance_key(duckdb_path: Path) -> str:
    return str(Path(duckdb_path).resolve())


def _duckdb_checkpoint_due(*, duckdb_path: Path, now_monotonic: float) -> bool:
    key = _duckdb_maintenance_key(duckdb_path)
    with _DUCKDB_MAINTENANCE_LOCK:
        last_checkpoint = _DUCKDB_LAST_CHECKPOINT_TS.get(key)
    if last_checkpoint is None:
        return True
    return (float(now_monotonic) - float(last_checkpoint)) >= max(float(DUCKDB_CHECKPOINT_INTERVAL_SECONDS), 0.0)


def _mark_duckdb_checkpoint(*, duckdb_path: Path, checkpoint_ts_monotonic: float) -> None:
    key = _duckdb_maintenance_key(duckdb_path)
    with _DUCKDB_MAINTENANCE_LOCK:
        _DUCKDB_LAST_CHECKPOINT_TS[key] = float(checkpoint_ts_monotonic)


def _manage_duckdb_wal_checkpoint(*, duckdb_path: Path) -> dict[str, Any]:
    if not duckdb_path.exists():
        return {
            "wal_autocheckpoint_set": 0,
            "checkpoint_attempted": 0,
            "checkpoint_completed": 0,
            "maintenance_error": None,
        }

    wal_autocheckpoint_set = 0
    checkpoint_attempted = 0
    checkpoint_completed = 0
    maintenance_error: str | None = None

    now_monotonic = time.monotonic()
    should_checkpoint = _duckdb_checkpoint_due(duckdb_path=duckdb_path, now_monotonic=now_monotonic)
    try:
        with duckdb.connect(str(duckdb_path)) as conn:
            try:
                # DuckDB expects memory units here on newer versions. Convert legacy
                # page-based target (~4 KiB/page) into a deterministic MiB budget.
                target_pages = max(int(DUCKDB_WAL_AUTOCHECKPOINT_PAGES), 1)
                target_mib = max(int(math.ceil((target_pages * 4.0) / 1024.0)), 1)
                conn.execute(f"PRAGMA wal_autocheckpoint='{target_mib} MiB'")
                wal_autocheckpoint_set = 1
            except duckdb.Error as exc:
                maintenance_error = str(exc)

            if should_checkpoint:
                checkpoint_attempted = 1
                try:
                    conn.execute("CHECKPOINT")
                    checkpoint_completed = 1
                    _mark_duckdb_checkpoint(
                        duckdb_path=duckdb_path,
                        checkpoint_ts_monotonic=now_monotonic,
                    )
                except duckdb.Error as exc:
                    if not maintenance_error:
                        maintenance_error = str(exc)
    except duckdb.Error as exc:
        if not maintenance_error:
            maintenance_error = str(exc)

    return {
        "wal_autocheckpoint_set": int(wal_autocheckpoint_set),
        "checkpoint_attempted": int(checkpoint_attempted),
        "checkpoint_completed": int(checkpoint_completed),
        "maintenance_error": maintenance_error,
    }


def _append_duckdb_rows(
    *,
    rows_df: pd.DataFrame,
    fills_df: pd.DataFrame,
    duckdb_path: Path,
    table_name: str,
) -> tuple[int, int]:
    table = _validate_table_name(table_name)
    fills_table = f"{table}_fills"
    normalized_rows_df = _ensure_spool_uid_column(rows_df, prefix=f"{table}:order")
    normalized_fills_df = _ensure_spool_uid_column(fills_df, prefix=f"{table}:fill")

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(duckdb_path))
    try:
        order_inserted = 0
        fill_inserted = 0

        if not normalized_rows_df.empty:
            order_inserted = _append_duckdb_table_rows(
                conn=conn,
                table=table,
                frame=normalized_rows_df,
                register_name="new_rows",
            )

        if not normalized_fills_df.empty:
            fill_inserted = _append_duckdb_table_rows(
                conn=conn,
                table=fills_table,
                frame=normalized_fills_df,
                register_name="new_fill_rows",
            )

        return order_inserted, fill_inserted
    finally:
        conn.close()


def _spool_offset_path(spool_path: Path) -> Path:
    return spool_path.with_suffix(f"{spool_path.suffix}.offset")


def _spool_bad_path(spool_path: Path) -> Path:
    return spool_path.with_suffix(f"{spool_path.suffix}.bad")


def _spool_generation_path(spool_path: Path) -> Path:
    return spool_path.with_suffix(f"{spool_path.suffix}.gen")


def _spool_lock_path(spool_path: Path) -> Path:
    return spool_path.with_suffix(f"{spool_path.suffix}.lock")


def _lock_file_handle_non_blocking(handle: Any) -> bool:
    if os.name == "nt":
        import msvcrt

        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    else:
        import fcntl

        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False


def _unlock_file_handle(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            return
    else:
        import fcntl

        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            return


@contextmanager
def _acquire_spool_cross_process_lock(
    *,
    spool_path: Path,
    timeout_seconds: float,
):
    lock_path = _spool_lock_path(spool_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    acquired = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() <= 0:
            handle.write(b"0")
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass

        timeout = max(float(timeout_seconds), 0.0)
        deadline = time.monotonic() + timeout
        while True:
            if _lock_file_handle_non_blocking(handle):
                acquired = True
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(max(float(SPOOL_LOCK_RETRY_SLEEP_SECONDS), 0.0))
        yield acquired
    finally:
        if acquired:
            _unlock_file_handle(handle)
        handle.close()


def _read_spool_offset(offset_path: Path) -> int:
    if not offset_path.exists():
        return 0
    try:
        raw = _clean_text(offset_path.read_text(encoding="utf-8"))
    except OSError:
        return 0
    if not raw:
        return 0
    try:
        offset = int(raw)
    except ValueError:
        return 0
    return max(offset, 0)


def _write_spool_offset(offset_path: Path, offset: int) -> None:
    _atomic_write_text(offset_path, f"{max(int(offset), 0)}\n")


def _read_spool_generation(generation_path: Path) -> int:
    if not generation_path.exists():
        return 0
    try:
        raw = _clean_text(generation_path.read_text(encoding="utf-8"))
    except OSError:
        return 0
    if not raw:
        return 0
    try:
        generation = int(raw)
    except ValueError:
        return 0
    return max(generation, 0)


def _write_spool_generation(generation_path: Path, generation: int) -> None:
    _atomic_write_text(generation_path, f"{max(int(generation), 0)}\n")


def _resolve_spool_state(
    *,
    spool_path: Path,
    offset_path: Path,
    generation_path: Path,
) -> tuple[int, int, bool]:
    generation = _read_spool_generation(generation_path)
    if not spool_path.exists():
        return 0, generation, False

    file_size = int(spool_path.stat().st_size)
    offset = _read_spool_offset(offset_path)
    if offset <= file_size:
        return offset, generation, False

    # Spool was truncated or replaced; reset to avoid skipping unread data.
    _write_spool_offset(offset_path, 0)
    generation += 1
    _write_spool_generation(generation_path, generation)
    return 0, generation, True


def _quarantine_bad_spool_line(
    *,
    bad_path: Path,
    line_start: int,
    reason: str,
    raw_line: str,
) -> None:
    entry = {
        "captured_at_utc": _to_iso_now_ms(),
        "byte_offset": int(max(line_start, 0)),
        "reason": _clean_text(reason) or "invalid_spool_line",
        "line": raw_line.rstrip("\n"),
    }
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entry, ensure_ascii=True, separators=(",", ":"))
    with bad_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _build_spool_record_uid(*, generation: int, line_start: int, payload: str) -> str:
    material = f"{int(generation)}:{int(line_start)}:{payload}"
    return hashlib.sha1(material.encode("utf-8")).hexdigest()


def _pending_spool_bytes(*, spool_path: Path, offset_path: Path) -> int:
    if not spool_path.exists():
        return 0
    size = int(spool_path.stat().st_size)
    offset = _read_spool_offset(offset_path)
    if offset > size:
        return int(size)
    if offset >= size:
        return 0
    return int(size - offset)


def _build_spool_records(
    *,
    order_rows: list[dict[str, Any]],
    fill_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def _deterministic_uid(record_type: str, row: dict[str, Any]) -> str:
        uid_payload = {
            "record_type": str(record_type),
            # Exclude capture-time wall clock so retries of the same logical event collapse.
            "row": {k: v for k, v in row.items() if k != "captured_at_utc"},
        }
        material = json.dumps(uid_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha1(material.encode("utf-8")).hexdigest()

    records: list[dict[str, Any]] = []
    records.extend(
        {
            "record_type": "order",
            "row": row,
            SPOOL_RECORD_UID_COLUMN: _deterministic_uid("order", row),
        }
        for row in order_rows
    )
    records.extend(
        {
            "record_type": "fill",
            "row": row,
            SPOOL_RECORD_UID_COLUMN: _deterministic_uid("fill", row),
        }
        for row in fill_rows
    )
    return records


def _serialize_spool_records(records: list[dict[str, Any]]) -> str:
    return "".join(f"{json.dumps(record, separators=(',', ':'), ensure_ascii=True)}\n" for record in records)


def _append_prebuilt_spool_records(
    *,
    spool_path: Path,
    records: list[dict[str, Any]],
    lock_timeout_seconds: float,
) -> int:
    if not records:
        return 0
    payload = _serialize_spool_records(records)
    if not payload:
        return 0

    spool_path.parent.mkdir(parents=True, exist_ok=True)
    with _acquire_spool_cross_process_lock(
        spool_path=spool_path,
        timeout_seconds=lock_timeout_seconds,
    ) as lock_acquired:
        if not lock_acquired:
            return 0
        with spool_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    return int(len(records))


def _append_spool_records(
    *,
    spool_path: Path,
    order_rows: list[dict[str, Any]],
    fill_rows: list[dict[str, Any]],
    lock_timeout_seconds: float = SPOOL_APPEND_LOCK_TIMEOUT_SECONDS,
) -> int:
    records = _build_spool_records(order_rows=order_rows, fill_rows=fill_rows)
    if not records:
        return 0
    return _append_prebuilt_spool_records(
        spool_path=spool_path,
        records=records,
        lock_timeout_seconds=lock_timeout_seconds,
    )


def _validate_spool_record_schema(decoded: dict[str, Any]) -> str | None:
    record_type = _clean_text(decoded.get("record_type")).lower()
    if record_type not in {"order", "fill"}:
        return "schema_invalid_record_type"
    if not isinstance(decoded.get("row"), dict):
        return "schema_row_not_object"
    return None


def _read_spool_records_since(
    *,
    spool_path: Path,
    start_offset: int,
    generation: int,
    bad_path: Path,
    partial_line_stale_seconds: float = TRAILING_PARTIAL_LINE_STALE_SECONDS,
) -> tuple[list[dict[str, Any]], int, int]:
    if not spool_path.exists():
        return [], 0, 0

    file_size = int(spool_path.stat().st_size)
    cursor = max(min(int(start_offset), file_size), 0)
    records: list[dict[str, Any]] = []
    quarantined_lines = 0

    with spool_path.open("r", encoding="utf-8") as handle:
        handle.seek(cursor)
        while True:
            line_start = handle.tell()
            line = handle.readline()
            if line == "":
                break
            if not line.endswith("\n"):
                stale_after = max(float(partial_line_stale_seconds), 0.0)
                file_age_seconds = 0.0
                try:
                    file_age_seconds = max(time.time() - float(spool_path.stat().st_mtime), 0.0)
                except OSError:
                    file_age_seconds = stale_after
                if file_age_seconds >= stale_after:
                    cursor = handle.tell()
                    _quarantine_bad_spool_line(
                        bad_path=bad_path,
                        line_start=line_start,
                        reason="trailing_partial_line_stale",
                        raw_line=line,
                    )
                    quarantined_lines += 1
                    continue
                break

            payload = line.strip()
            cursor = handle.tell()
            if not payload:
                continue
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError:
                _quarantine_bad_spool_line(
                    bad_path=bad_path,
                    line_start=line_start,
                    reason="json_decode_error",
                    raw_line=line,
                )
                quarantined_lines += 1
                continue
            if not isinstance(decoded, dict):
                _quarantine_bad_spool_line(
                    bad_path=bad_path,
                    line_start=line_start,
                    reason="json_root_not_object",
                    raw_line=line,
                )
                quarantined_lines += 1
                continue
            schema_error = _validate_spool_record_schema(decoded)
            if schema_error:
                _quarantine_bad_spool_line(
                    bad_path=bad_path,
                    line_start=line_start,
                    reason=schema_error,
                    raw_line=line,
                )
                quarantined_lines += 1
                continue
            spool_uid = _clean_text(decoded.get(SPOOL_RECORD_UID_COLUMN))
            if not spool_uid:
                spool_uid = _build_spool_record_uid(
                    generation=generation,
                    line_start=line_start,
                    payload=payload,
                )
            decoded[SPOOL_RECORD_UID_COLUMN] = spool_uid
            records.append(decoded)

    return records, cursor, quarantined_lines


def _split_spool_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    order_rows: list[dict[str, Any]] = []
    fill_rows: list[dict[str, Any]] = []
    for record in records:
        record_type = _clean_text(record.get("record_type")).lower()
        row = record.get("row")
        if not isinstance(row, dict):
            continue
        row_copy = dict(row)
        spool_uid = _clean_text(record.get(SPOOL_RECORD_UID_COLUMN))
        if spool_uid:
            row_copy[SPOOL_RECORD_UID_COLUMN] = spool_uid
        if record_type == "order":
            order_rows.append(row_copy)
        elif record_type == "fill":
            fill_rows.append(row_copy)
    return order_rows, fill_rows


def _compact_spool_if_drained(
    *,
    spool_path: Path,
    offset_path: Path,
    generation_path: Path,
) -> bool:
    if not spool_path.exists():
        return False
    file_size = int(spool_path.stat().st_size)
    offset = _read_spool_offset(offset_path)
    if file_size <= 0:
        if offset != 0:
            _write_spool_offset(offset_path, 0)
        return False
    if offset < file_size:
        return False

    # Fully consumed spool; truncate to cap growth and reset cursor for the next segment.
    _atomic_write_text(spool_path, "")
    _write_spool_offset(offset_path, 0)
    _write_spool_generation(generation_path, _read_spool_generation(generation_path) + 1)
    return True


def _flush_spool_to_sinks(
    *,
    spool_path: Path,
    parquet_path: Path,
    fills_parquet_path: Path,
    duckdb_path: Path,
    table_name: str,
) -> dict[str, Any]:
    offset_path = _spool_offset_path(spool_path)
    bad_path = _spool_bad_path(spool_path)
    generation_path = _spool_generation_path(spool_path)

    stale_offset_reset = False
    quarantined_lines = 0
    spool_compacted = False
    records: list[dict[str, Any]] = []
    duckdb_orders_written = 0
    duckdb_fills_written = 0

    with _acquire_spool_cross_process_lock(
        spool_path=spool_path,
        timeout_seconds=SPOOL_FLUSH_LOCK_TIMEOUT_SECONDS,
    ) as lock_acquired:
        if not lock_acquired:
            return {
                "records_flushed": 0,
                "quarantined_lines": 0,
                "parquet_orders_written": 0,
                "parquet_fills_written": 0,
                "duckdb_orders_written": 0,
                "duckdb_fills_written": 0,
                "stale_offset_reset": 0,
                "spool_compacted": 0,
                "spool_lock_contended": 1,
                "wal_autocheckpoint_set": 0,
                "duckdb_checkpoint_attempted": 0,
                "duckdb_checkpoint_completed": 0,
                "duckdb_maintenance_error": None,
                "parquet_export_error": None,
            }

        start_offset, generation, stale_offset_reset = _resolve_spool_state(
            spool_path=spool_path,
            offset_path=offset_path,
            generation_path=generation_path,
        )
        records, next_offset, quarantined_lines = _read_spool_records_since(
            spool_path=spool_path,
            start_offset=start_offset,
            generation=generation,
            bad_path=bad_path,
        )

        if records:
            order_rows, fill_rows = _split_spool_records(records)
            order_df = pd.DataFrame(order_rows)
            fill_df = pd.DataFrame(fill_rows)
            duckdb_orders_written, duckdb_fills_written = _append_duckdb_rows(
                rows_df=order_df,
                fills_df=fill_df,
                duckdb_path=duckdb_path,
                table_name=table_name,
            )

        if next_offset != start_offset or quarantined_lines > 0 or stale_offset_reset:
            _write_spool_offset(offset_path, next_offset)

        spool_compacted = _compact_spool_if_drained(
            spool_path=spool_path,
            offset_path=offset_path,
            generation_path=generation_path,
        )

    duckdb_maintenance = _manage_duckdb_wal_checkpoint(duckdb_path=duckdb_path)

    parquet_export_error: str | None = None
    parquet_orders_written = 0
    parquet_fills_written = 0
    try:
        parquet_orders_written = _export_duckdb_table_to_parquet(
            duckdb_path=duckdb_path,
            table_name=table_name,
            parquet_path=parquet_path,
        )
        parquet_fills_written = _export_duckdb_table_to_parquet(
            duckdb_path=duckdb_path,
            table_name=f"{table_name}_fills",
            parquet_path=fills_parquet_path,
        )
    except Exception as exc:
        parquet_export_error = str(exc)

    return {
        "records_flushed": int(len(records)),
        "quarantined_lines": int(quarantined_lines),
        "parquet_orders_written": parquet_orders_written,
        "parquet_fills_written": parquet_fills_written,
        "duckdb_orders_written": duckdb_orders_written,
        "duckdb_fills_written": duckdb_fills_written,
        "stale_offset_reset": int(stale_offset_reset),
        "spool_compacted": int(spool_compacted),
        "spool_lock_contended": 0,
        "wal_autocheckpoint_set": int(duckdb_maintenance["wal_autocheckpoint_set"]),
        "duckdb_checkpoint_attempted": int(duckdb_maintenance["checkpoint_attempted"]),
        "duckdb_checkpoint_completed": int(duckdb_maintenance["checkpoint_completed"]),
        "duckdb_maintenance_error": _clean_text(duckdb_maintenance["maintenance_error"]) or None,
        "parquet_export_error": parquet_export_error,
    }


class _TelemetrySpooler:
    def __init__(
        self,
        *,
        spool_path: Path,
        parquet_path: Path,
        fills_parquet_path: Path,
        duckdb_path: Path,
        table_name: str,
    ) -> None:
        self.spool_path = Path(spool_path)
        self.parquet_path = Path(parquet_path)
        self.fills_parquet_path = Path(fills_parquet_path)
        self.duckdb_path = Path(duckdb_path)
        self.table_name = _validate_table_name(table_name)
        self._flush_lock = threading.Lock()
        self._buffer_lock = threading.Lock()
        self._buffered_records: deque[tuple[dict[str, Any], int]] = deque()
        self._buffered_bytes = 0
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._last_flush_error: str | None = None
        self._last_flush_ts_utc: str | None = None
        self._append_lock_contention_count = 0
        self._append_error_count = 0
        self._buffer_drop_count = 0
        self._buffer_drop_events = 0
        self._retry_backoff_seconds = max(float(SPOOL_RETRY_BACKOFF_BASE_SECONDS), 0.0)
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"microstructure-spool-{abs(hash(str(self.spool_path))) % 10_000}",
            daemon=True,
        )
        self._thread.start()

    def _buffer_records_for_retry(self, records: list[dict[str, Any]]) -> tuple[int, int]:
        if not records:
            return 0, 0
        max_records = max(int(SPOOL_BUFFER_MAX_RECORDS), 1)
        max_bytes = max(int(SPOOL_BUFFER_MAX_BYTES), 1)
        encoded: list[tuple[dict[str, Any], int]] = [
            (
                record,
                len(f"{json.dumps(record, separators=(',', ':'), ensure_ascii=True)}\n"),
            )
            for record in records
        ]
        required_records = len(encoded)
        required_bytes = sum(int(line_len) for _, line_len in encoded)

        buffered_count = 0
        dropped_count = 0
        with self._buffer_lock:
            projected_records = len(self._buffered_records) + int(required_records)
            projected_bytes = int(self._buffered_bytes) + int(required_bytes)
            if projected_records <= max_records and projected_bytes <= max_bytes:
                self._buffered_records.extend(encoded)
                self._buffered_bytes += int(required_bytes)
                buffered_count = int(required_records)
            else:
                dropped_count = int(required_records)
            if dropped_count > 0:
                self._buffer_drop_count += int(dropped_count)
                self._buffer_drop_events += 1
        return int(buffered_count), int(dropped_count)

    def _drain_buffered_records_to_spool(self) -> int:
        with self._buffer_lock:
            if not self._buffered_records:
                return 0
            batch_size = min(
                len(self._buffered_records),
                max(int(SPOOL_BUFFER_DRAIN_BATCH_RECORDS), 1),
            )
            head_batch = list(itertools.islice(self._buffered_records, 0, batch_size))
            pending_records = [record for record, _ in head_batch]
        if not pending_records:
            return 0

        wrote = _append_prebuilt_spool_records(
            spool_path=self.spool_path,
            records=pending_records,
            lock_timeout_seconds=SPOOL_FLUSH_LOCK_TIMEOUT_SECONDS,
        )
        if wrote <= 0:
            return 0

        drained = min(int(wrote), len(pending_records))
        with self._buffer_lock:
            for _ in range(drained):
                _, line_len = self._buffered_records.popleft()
                self._buffered_bytes = max(int(self._buffered_bytes) - int(line_len), 0)
        return int(drained)

    def append(self, *, order_rows: list[dict[str, Any]], fill_rows: list[dict[str, Any]]) -> dict[str, Any]:
        records = _build_spool_records(order_rows=order_rows, fill_rows=fill_rows)
        if not records:
            return {
                "records_total": 0,
                "records_appended": 0,
                "records_buffered": 0,
                "records_dropped": 0,
                "append_lock_contended": 0,
                "append_error": None,
            }

        appended = 0
        append_error: str | None = None
        try:
            appended = _append_prebuilt_spool_records(
                spool_path=self.spool_path,
                records=records,
                lock_timeout_seconds=SPOOL_APPEND_LOCK_TIMEOUT_SECONDS,
            )
        except OSError as exc:
            append_error = str(exc)
            self._last_flush_error = append_error
            with self._buffer_lock:
                self._append_error_count += 1
            appended = 0

        append_lock_contended = 1 if (appended <= 0 and append_error is None and bool(records)) else 0
        if append_lock_contended:
            with self._buffer_lock:
                self._append_lock_contention_count += 1

        buffered_count = 0
        dropped_count = 0
        if appended < len(records):
            retry_records = records[int(max(appended, 0)) :]
            buffered_count, dropped_count = self._buffer_records_for_retry(retry_records)
            if dropped_count > 0:
                overflow_error = (
                    "telemetry spool retry buffer overflow: "
                    f"dropped_records={int(dropped_count)} "
                    f"max_records={int(SPOOL_BUFFER_MAX_RECORDS)} "
                    f"max_bytes={int(SPOOL_BUFFER_MAX_BYTES)}"
                )
                self._last_flush_error = overflow_error
                raise RuntimeError(overflow_error)

        self._wake_event.set()
        return {
            "records_total": int(len(records)),
            "records_appended": int(appended),
            "records_buffered": int(buffered_count),
            "records_dropped": int(dropped_count),
            "append_lock_contended": int(append_lock_contended),
            "append_error": append_error,
        }

    def request_flush(self) -> None:
        self._wake_event.set()

    def flush_once(self) -> dict[str, Any]:
        with self._flush_lock:
            buffered_records_written = self._drain_buffered_records_to_spool()
            summary = _flush_spool_to_sinks(
                spool_path=self.spool_path,
                parquet_path=self.parquet_path,
                fills_parquet_path=self.fills_parquet_path,
                duckdb_path=self.duckdb_path,
                table_name=self.table_name,
            )
            export_error = _clean_text(summary.get("parquet_export_error"))
            maintenance_error = _clean_text(summary.get("duckdb_maintenance_error"))
            summary["buffered_records_written"] = int(buffered_records_written)

            with self._buffer_lock:
                buffered_records_pending = len(self._buffered_records)
                buffered_bytes_pending = int(self._buffered_bytes)
                append_lock_contention_count = int(self._append_lock_contention_count)
                append_error_count = int(self._append_error_count)
                buffer_drop_count = int(self._buffer_drop_count)
                buffer_drop_events = int(self._buffer_drop_events)
            summary["buffered_records_pending"] = int(buffered_records_pending)
            summary["buffered_bytes_pending"] = int(buffered_bytes_pending)
            summary["append_lock_contention_count"] = int(append_lock_contention_count)
            summary["append_error_count"] = int(append_error_count)
            summary["buffer_drop_count"] = int(buffer_drop_count)
            summary["buffer_drop_events"] = int(buffer_drop_events)

            self._last_flush_error = export_error or maintenance_error or None
            self._last_flush_ts_utc = _to_iso_now_ms()
            if buffered_records_pending > 0 or int(summary.get("pending_bytes", 0)) > 0:
                self._wake_event.set()
            return summary

    def status(self) -> dict[str, Any]:
        offset_path = _spool_offset_path(self.spool_path)
        spool_pending = _pending_spool_bytes(spool_path=self.spool_path, offset_path=offset_path)
        with self._buffer_lock:
            buffered_records_pending = len(self._buffered_records)
            buffered_bytes_pending = int(self._buffered_bytes)
            append_lock_contention_count = int(self._append_lock_contention_count)
            append_error_count = int(self._append_error_count)
            buffer_drop_count = int(self._buffer_drop_count)
            buffer_drop_events = int(self._buffer_drop_events)
        return {
            "spool_path": str(self.spool_path),
            "offset_path": str(offset_path),
            "pending_bytes": int(spool_pending + buffered_bytes_pending),
            "spool_pending_bytes": int(spool_pending),
            "buffered_records_pending": int(buffered_records_pending),
            "buffered_bytes_pending": int(buffered_bytes_pending),
            "append_lock_contention_count": int(append_lock_contention_count),
            "append_error_count": int(append_error_count),
            "buffer_drop_count": int(buffer_drop_count),
            "buffer_drop_events": int(buffer_drop_events),
            "last_flush_error": self._last_flush_error,
            "last_flush_ts_utc": self._last_flush_ts_utc,
        }

    def stop(self, *, timeout_seconds: float = 2.0) -> None:
        deadline = time.monotonic() + max(float(timeout_seconds), 0.1)
        self._stop_event.set()
        self._wake_event.set()
        # Best-effort synchronous drain before shutdown hard-stop.
        while time.monotonic() <= deadline:
            status = self.status()
            if int(status.get("pending_bytes", 0)) <= 0:
                break
            try:
                self.flush_once()
            except Exception as exc:
                self._last_flush_error = str(exc)
            time.sleep(0.01)

        remaining_join_timeout = max(deadline - time.monotonic(), 0.1)
        self._thread.join(timeout=remaining_join_timeout)
        final_status = self.status()
        pending_bytes = int(final_status.get("pending_bytes", 0))
        if pending_bytes > 0:
            buffered_records = int(final_status.get("buffered_records_pending", 0))
            raise RuntimeError(
                "telemetry spool shutdown fail-closed: "
                f"pending_bytes={pending_bytes} "
                f"buffered_records_pending={buffered_records} "
                f"last_flush_error={_clean_text(final_status.get('last_flush_error')) or 'none'}"
            )

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._wake_event.wait(timeout=0.250)
            self._wake_event.clear()
            if self._stop_event.is_set():
                break
            try:
                summary = self.flush_once()
                pending_bytes = int(summary.get("pending_bytes", 0))
                buffered_pending = int(summary.get("buffered_records_pending", 0))
                progress = (
                    int(summary.get("records_flushed", 0)) > 0
                    or int(summary.get("buffered_records_written", 0)) > 0
                )
                if (pending_bytes > 0 or buffered_pending > 0) and not progress:
                    backoff = max(float(self._retry_backoff_seconds), 0.0)
                    if backoff > 0.0:
                        time.sleep(backoff)
                    self._retry_backoff_seconds = min(
                        max(backoff * 2.0, float(SPOOL_RETRY_BACKOFF_BASE_SECONDS)),
                        float(SPOOL_RETRY_BACKOFF_MAX_SECONDS),
                    )
                    self._wake_event.set()
                else:
                    self._retry_backoff_seconds = max(float(SPOOL_RETRY_BACKOFF_BASE_SECONDS), 0.0)
            except Exception as exc:
                self._last_flush_error = str(exc)
                backoff = max(float(self._retry_backoff_seconds), 0.010)
                time.sleep(backoff)
                self._retry_backoff_seconds = min(
                    max(backoff * 2.0, float(SPOOL_RETRY_BACKOFF_BASE_SECONDS)),
                    float(SPOOL_RETRY_BACKOFF_MAX_SECONDS),
                )
                self._wake_event.set()


def _spooler_key(
    *,
    spool_path: Path,
    parquet_path: Path,
    fills_parquet_path: Path,
    duckdb_path: Path,
    table_name: str,
) -> tuple[str, str, str, str, str]:
    return (
        str(Path(spool_path).resolve()),
        str(Path(parquet_path).resolve()),
        str(Path(fills_parquet_path).resolve()),
        str(Path(duckdb_path).resolve()),
        _validate_table_name(table_name),
    )


def _get_or_create_spooler(
    *,
    spool_path: Path,
    parquet_path: Path,
    fills_parquet_path: Path,
    duckdb_path: Path,
    table_name: str,
    create_if_missing: bool = True,
) -> _TelemetrySpooler | None:
    key = _spooler_key(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name=table_name,
    )
    with _SPOOLER_REGISTRY_LOCK:
        spooler = _SPOOLER_REGISTRY.get(key)
        if spooler is None and create_if_missing:
            spooler = _TelemetrySpooler(
                spool_path=spool_path,
                parquet_path=parquet_path,
                fills_parquet_path=fills_parquet_path,
                duckdb_path=duckdb_path,
                table_name=table_name,
            )
            _SPOOLER_REGISTRY[key] = spooler
        return spooler


def _shutdown_execution_microstructure_spoolers() -> None:
    with _SPOOLER_REGISTRY_LOCK:
        spoolers = list(_SPOOLER_REGISTRY.values())
        _SPOOLER_REGISTRY.clear()
    shutdown_errors: list[str] = []
    for spooler in spoolers:
        try:
            spooler.stop()
        except RuntimeError as exc:
            shutdown_errors.append(str(exc))
    if shutdown_errors:
        raise RuntimeError("; ".join(shutdown_errors))


def wait_for_execution_microstructure_flush(
    *,
    spool_path: Path = DEFAULT_TELEMETRY_SPOOL,
    parquet_path: Path = DEFAULT_TELEMETRY_PARQUET,
    fills_parquet_path: Path = DEFAULT_TELEMETRY_FILLS_PARQUET,
    duckdb_path: Path = DEFAULT_TELEMETRY_DUCKDB,
    table_name: str = DEFAULT_TELEMETRY_TABLE,
    timeout_seconds: float = 5.0,
    poll_interval_seconds: float = 0.05,
) -> bool:
    spooler = _get_or_create_spooler(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name=table_name,
        create_if_missing=True,
    )
    assert spooler is not None
    initial_status = spooler.status()
    initial_pending = int(initial_status["pending_bytes"])
    initial_last_flush_ts = _clean_text(initial_status.get("last_flush_ts_utc"))
    spooler.request_flush()
    deadline = time.monotonic() + max(float(timeout_seconds), 0.0)
    while time.monotonic() <= deadline:
        status = spooler.status()
        pending_bytes = int(status["pending_bytes"])
        current_flush_ts = _clean_text(status.get("last_flush_ts_utc"))
        current_last_flush_error = _clean_text(status.get("last_flush_error"))
        current_buffer_drop_count = int(status.get("buffer_drop_count", 0))
        flush_completed_since_request = (
            bool(current_flush_ts)
            and (
                not initial_last_flush_ts
                or current_flush_ts != initial_last_flush_ts
            )
        )
        no_flush_error = not bool(current_last_flush_error)
        no_drop_evidence = current_buffer_drop_count <= 0
        if (
            pending_bytes <= 0
            and (initial_pending <= 0 or flush_completed_since_request)
            and no_flush_error
            and no_drop_evidence
        ):
            return True
        time.sleep(max(float(poll_interval_seconds), 0.01))
    final_status = spooler.status()
    final_pending = int(final_status["pending_bytes"])
    final_flush_ts = _clean_text(final_status.get("last_flush_ts_utc"))
    final_last_flush_error = _clean_text(final_status.get("last_flush_error"))
    final_buffer_drop_count = int(final_status.get("buffer_drop_count", 0))
    final_flush_completed = (
        bool(final_flush_ts)
        and (
            not initial_last_flush_ts
            or final_flush_ts != initial_last_flush_ts
        )
    )
    return (
        final_pending <= 0
        and (initial_pending <= 0 or final_flush_completed)
        and not bool(final_last_flush_error)
        and final_buffer_drop_count <= 0
    )


def get_execution_microstructure_spool_status(
    *,
    spool_path: Path = DEFAULT_TELEMETRY_SPOOL,
    parquet_path: Path = DEFAULT_TELEMETRY_PARQUET,
    fills_parquet_path: Path = DEFAULT_TELEMETRY_FILLS_PARQUET,
    duckdb_path: Path = DEFAULT_TELEMETRY_DUCKDB,
    table_name: str = DEFAULT_TELEMETRY_TABLE,
) -> dict[str, Any]:
    spooler = _get_or_create_spooler(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name=table_name,
        create_if_missing=False,
    )
    if spooler is not None:
        return spooler.status()
    offset_path = _spool_offset_path(spool_path)
    return {
        "spool_path": str(spool_path),
        "offset_path": str(offset_path),
        "pending_bytes": _pending_spool_bytes(spool_path=spool_path, offset_path=offset_path),
        "buffer_drop_count": 0,
        "buffer_drop_events": 0,
        "last_flush_error": None,
        "last_flush_ts_utc": None,
    }


def append_execution_microstructure(
    execute_results: list[dict[str, Any]],
    *,
    batch_id: str,
    strategy: str,
    parquet_path: Path = DEFAULT_TELEMETRY_PARQUET,
    fills_parquet_path: Path = DEFAULT_TELEMETRY_FILLS_PARQUET,
    duckdb_path: Path = DEFAULT_TELEMETRY_DUCKDB,
    table_name: str = DEFAULT_TELEMETRY_TABLE,
    spool_path: Path = DEFAULT_TELEMETRY_SPOOL,
) -> dict[str, Any]:
    submit_to_ack_history_ms = _load_recent_submit_to_ack_history_ms(
        duckdb_path=duckdb_path,
        table_name=table_name,
        window_size=HEARTBEAT_ROLLING_WINDOW,
    )
    order_rows, fill_rows = build_execution_telemetry_rows(
        execute_results,
        batch_id=batch_id,
        strategy=strategy,
        submit_to_ack_history_ms=submit_to_ack_history_ms,
    )

    spooler = _get_or_create_spooler(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name=table_name,
        create_if_missing=True,
    )
    assert spooler is not None
    append_summary = spooler.append(order_rows=order_rows, fill_rows=fill_rows)
    spooler.request_flush()
    status = spooler.status()
    fully_appended = int(append_summary["records_appended"]) == int(append_summary["records_total"])
    orders_prepared = int(len(order_rows))
    fills_prepared = int(len(fill_rows))
    orders_written = int(orders_prepared if fully_appended else 0)
    fills_written = int(fills_prepared if fully_appended else 0)
    heartbeat_blocked_rows = sum(1 for row in order_rows if bool(row.get("heartbeat_is_blocked")))
    heartbeat_hard_blocked_rows = sum(1 for row in order_rows if bool(row.get("heartbeat_is_hard_block")))

    return {
        "orders_prepared": int(orders_prepared),
        "fills_prepared": int(fills_prepared),
        "orders_written": int(orders_written),
        "fills_written": int(fills_written),
        "parquet_orders_written": 0,
        "parquet_fills_written": 0,
        "duckdb_orders_written": 0,
        "duckdb_fills_written": 0,
        "parquet_path": str(parquet_path),
        "fills_parquet_path": str(fills_parquet_path),
        "duckdb_path": str(duckdb_path),
        "duckdb_table": _validate_table_name(table_name),
        "spool_path": str(spool_path),
        "spool_offset_path": str(_spool_offset_path(spool_path)),
        "spool_records_total": int(append_summary["records_total"]),
        "spool_records_appended": int(append_summary["records_appended"]),
        "spool_records_buffered": int(append_summary["records_buffered"]),
        "spool_records_dropped": int(append_summary["records_dropped"]),
        "spool_append_lock_contended": int(append_summary["append_lock_contended"]),
        "spool_append_error": _clean_text(append_summary.get("append_error")) or None,
        "flush_pending_bytes": int(status["pending_bytes"]),
        "buffered_records_pending": int(status.get("buffered_records_pending", 0)),
        "buffered_bytes_pending": int(status.get("buffered_bytes_pending", 0)),
        "spool_append_lock_contention_count": int(status.get("append_lock_contention_count", 0)),
        "spool_append_error_count": int(status.get("append_error_count", 0)),
        "spool_buffer_drop_count": int(status.get("buffer_drop_count", 0)),
        "spool_buffer_drop_events": int(status.get("buffer_drop_events", 0)),
        "heartbeat_blocked_rows": int(heartbeat_blocked_rows),
        "heartbeat_hard_blocked_rows": int(heartbeat_hard_blocked_rows),
        "async_flush_scheduled": True,
    }
