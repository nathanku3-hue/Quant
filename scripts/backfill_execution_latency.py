from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import sys
import time
from typing import Any

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from execution.microstructure import HEARTBEAT_ROLLING_WINDOW
from execution.microstructure import annotate_heartbeat_freshness_frame

DEFAULT_SOURCE_PARQUET = PROJECT_ROOT / "data" / "processed" / "execution_microstructure.parquet"
DEFAULT_SOURCE_DUCKDB = PROJECT_ROOT / "data" / "processed" / "execution_microstructure.duckdb"
DEFAULT_SOURCE_TABLE = "execution_microstructure"
DEFAULT_OUTPUT_PARQUET = PROJECT_ROOT / "data" / "processed" / "execution_microstructure_latency_backfill.parquet"
DEFAULT_OUTPUT_SUMMARY_JSON = PROJECT_ROOT / "data" / "processed" / "execution_microstructure_latency_backfill_summary.json"
SOURCE_MODE_DUCKDB_STRICT = "duckdb_strict"
SOURCE_MODE_PARQUET_OVERRIDE = "parquet_override"
SOURCE_MODE_CHOICES = (SOURCE_MODE_DUCKDB_STRICT, SOURCE_MODE_PARQUET_OVERRIDE)
SOURCE_MODE_ENV = "TZ_EXEC_TELEMETRY_SOURCE_MODE"
_TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ATOMIC_REPLACE_MAX_RETRIES = 8
ATOMIC_REPLACE_BASE_SLEEP_SECONDS = 0.01


class PrimarySinkUnavailableError(RuntimeError):
    """Raised when strict-mode DuckDB source cannot be loaded."""


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _validate_table_name(table_name: str) -> str:
    candidate = str(table_name).strip()
    if not candidate:
        raise ValueError("table_name must be non-empty")
    if _TABLE_NAME_PATTERN.fullmatch(candidate) is None:
        raise ValueError(f"unsafe table_name: {table_name}")
    return candidate


def _atomic_write_parquet(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(f"{output_path.suffix}.{os.getpid()}.tmp")
    try:
        df.to_parquet(tmp_path, index=False)
        with tmp_path.open("r+b") as handle:
            os.fsync(handle.fileno())
        _atomic_replace_with_retry(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_write_text(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(f"{output_path.suffix}.{os.getpid()}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace_with_retry(tmp_path, output_path)
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
            delay = max(float(base_sleep_seconds), 0.001) * float(attempt + 1)
            time.sleep(delay)


def _load_source_rows(
    *,
    duckdb_path: Path,
    parquet_path: Path,
    table_name: str,
    source_mode: str | None = None,
) -> pd.DataFrame:
    mode = _resolve_source_mode(source_mode)
    if mode == SOURCE_MODE_PARQUET_OVERRIDE:
        if not parquet_path.exists():
            raise FileNotFoundError(
                "Parquet override requested but source parquet is missing. "
                f"parquet={parquet_path}"
            )
        return pd.read_parquet(parquet_path)

    if not duckdb_path.exists():
        raise PrimarySinkUnavailableError(
            "DuckDB strict mode requires primary sink availability. "
            f"missing duckdb={duckdb_path}"
        )

    table = _validate_table_name(table_name)
    try:
        with duckdb.connect(str(duckdb_path)) as conn:
            return conn.execute(f"SELECT * FROM {table}").df()
    except duckdb.Error as exc:
        raise PrimarySinkUnavailableError(
            "DuckDB strict mode failed to read primary sink. "
            f"duckdb={duckdb_path}, table={table}"
        ) from exc


def _resolve_source_mode(source_mode: str | None) -> str:
    if source_mode is None:
        candidate = str(os.getenv(SOURCE_MODE_ENV, "")).strip().lower()
    else:
        candidate = str(source_mode).strip().lower()
    if not candidate:
        return SOURCE_MODE_DUCKDB_STRICT
    if candidate not in SOURCE_MODE_CHOICES:
        raise ValueError(
            f"Unsupported source mode: {candidate}. "
            f"choices={SOURCE_MODE_CHOICES}, env={SOURCE_MODE_ENV}"
        )
    return candidate


def _sort_backfill_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    ordered = frame.copy()
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
        if column in ordered.columns
    ]
    if not event_time_columns:
        return ordered.reset_index(drop=True)

    event_time_series = pd.Series(pd.NaT, index=ordered.index, dtype="datetime64[ns, UTC]")
    for column in event_time_columns:
        parsed = pd.to_datetime(ordered[column], errors="coerce", utc=True)
        event_time_series = event_time_series.fillna(parsed)

    ordered["_event_time_sort_key"] = event_time_series
    sort_columns = ["_event_time_sort_key"] + [
        column
        for column in ("captured_at_utc", "client_order_id", "order_id")
        if column in ordered.columns
    ]
    ordered = ordered.sort_values(
        by=sort_columns,
        ascending=[True] * len(sort_columns),
        na_position="last",
        kind="mergesort",
    ).reset_index(drop=True)
    return ordered.drop(columns=["_event_time_sort_key"], errors="ignore")


def backfill_heartbeat_latency_columns(
    frame: pd.DataFrame,
    *,
    history_ms: list[float] | tuple[float, ...] | None = None,
) -> pd.DataFrame:
    ordered = _sort_backfill_rows(frame)
    return annotate_heartbeat_freshness_frame(
        ordered,
        latency_col="latency_ms_submit_to_ack",
        history_ms=history_ms,
        window_size=HEARTBEAT_ROLLING_WINDOW,
    )


def build_backfill_summary(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "generated_at_utc": _utc_now_iso_ms(),
            "rows": 0,
            "latency_observed_rows": 0,
            "heartbeat_blocked_rows": 0,
            "heartbeat_hard_block_rows": 0,
            "decision_counts": {},
        }
    decisions = frame.get("heartbeat_decision")
    if decisions is None:
        decision_counts: dict[str, int] = {}
    else:
        decision_counts = {
            str(key): int(value)
            for key, value in decisions.fillna("UNKNOWN").value_counts().to_dict().items()
        }
    latency_source = frame.get("latency_ms_submit_to_ack")
    if latency_source is None:
        latency_series = pd.Series([None] * len(frame), index=frame.index, dtype="float64")
    else:
        latency_series = pd.to_numeric(latency_source, errors="coerce")
        if not isinstance(latency_series, pd.Series):
            latency_series = pd.Series([latency_series] * len(frame), index=frame.index)
    blocked_series = frame.get("heartbeat_is_blocked")
    if blocked_series is None:
        blocked_series = pd.Series(False, index=frame.index)
    hard_block_series = frame.get("heartbeat_is_hard_block")
    if hard_block_series is None:
        hard_block_series = pd.Series(False, index=frame.index)
    return {
        "generated_at_utc": _utc_now_iso_ms(),
        "rows": int(len(frame)),
        "latency_observed_rows": int(latency_series.notna().sum()),
        "heartbeat_blocked_rows": int(pd.Series(blocked_series).fillna(False).astype(bool).sum()),
        "heartbeat_hard_block_rows": int(pd.Series(hard_block_series).fillna(False).astype(bool).sum()),
        "decision_counts": decision_counts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill adaptive heartbeat freshness annotations for execution telemetry.")
    parser.add_argument("--source-duckdb", default=str(DEFAULT_SOURCE_DUCKDB))
    parser.add_argument("--source-parquet", default=str(DEFAULT_SOURCE_PARQUET))
    parser.add_argument("--source-mode", choices=SOURCE_MODE_CHOICES, default=None)
    parser.add_argument("--table-name", default=DEFAULT_SOURCE_TABLE)
    parser.add_argument("--output-parquet", default=str(DEFAULT_OUTPUT_PARQUET))
    parser.add_argument("--summary-json", default=str(DEFAULT_OUTPUT_SUMMARY_JSON))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_duckdb = Path(args.source_duckdb)
    source_parquet = Path(args.source_parquet)
    output_parquet = Path(args.output_parquet)
    summary_json = Path(args.summary_json)
    table_name = str(args.table_name)

    source_df = _load_source_rows(
        duckdb_path=source_duckdb,
        parquet_path=source_parquet,
        table_name=table_name,
        source_mode=args.source_mode,
    )
    enriched_df = backfill_heartbeat_latency_columns(source_df)
    summary = build_backfill_summary(enriched_df)

    _atomic_write_parquet(enriched_df, output_parquet)
    _atomic_write_text(json.dumps(summary, indent=2, ensure_ascii=True), summary_json)

    print(
        "heartbeat backfill complete | "
        f"rows={summary['rows']} blocked={summary['heartbeat_blocked_rows']} "
        f"hard_block={summary['heartbeat_hard_block_rows']} "
        f"output={output_parquet}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
