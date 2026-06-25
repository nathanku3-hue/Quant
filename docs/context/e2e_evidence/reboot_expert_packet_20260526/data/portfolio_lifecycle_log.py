"""Append-only JSONL event log for portfolio position lifecycle.

Each line records one ENTER or EXIT event from the optimizer lifecycle.
No synthetic seeding. If the file is empty or missing, the system shows
a truthful empty state.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pandas as pd

DEFAULT_LIFECYCLE_LOG_PATH = Path("data/portfolio_lifecycle_log.jsonl")

VALID_ACTIONS = ("ENTER", "EXIT")
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_POLL_SECONDS = 0.05


def _acquire_lock(path: Path) -> Path:
    lock_path = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return lock_path
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for lifecycle log lock: {lock_path}")
            time.sleep(LOCK_POLL_SECONDS)


def append_lifecycle_event(
    ticker: str,
    action: str,
    date: str,
    weight: float,
    rating: str = "",
    reason: str = "",
    price: float | None = None,
    permno: int | None = None,
    path: Path | str | None = None,
) -> None:
    """Append one lifecycle event to the JSONL log with temp->replace semantics."""
    if action not in VALID_ACTIONS:
        raise ValueError(f"action must be one of {VALID_ACTIONS}, got {action!r}")
    path = Path(path) if path else DEFAULT_LIFECYCLE_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "ticker": ticker.upper(),
        "action": action,
        "date": str(date),
        "weight": round(float(weight), 6),
        "rating": rating,
        "reason": reason,
        "price": round(float(price), 4) if price is not None else None,
        "permno": permno,
    }
    line = json.dumps(event, default=str) + "\n"

    lock_path = _acquire_lock(path)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(existing)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
        if lock_path.exists():
            lock_path.unlink()


LIFECYCLE_COLUMNS = ["ticker", "action", "date", "weight", "rating", "reason", "price", "permno"]


def read_lifecycle_log(path: Path | str | None = None) -> pd.DataFrame:
    """Read all lifecycle events. Returns empty DataFrame if no events."""
    path = Path(path) if path else DEFAULT_LIFECYCLE_LOG_PATH
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=LIFECYCLE_COLUMNS)

    records = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            record["_event_order"] = len(records)
            records.append(record)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed lifecycle JSONL row {line_no} in {path}") from exc

    if not records:
        return pd.DataFrame(columns=LIFECYCLE_COLUMNS)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    sort_cols = ["date"]
    if "_event_order" in df.columns:
        sort_cols.append("_event_order")
    return df.sort_values(sort_cols, ascending=True, kind="mergesort").reset_index(drop=True)


def _coerce_as_of(as_of: str | pd.Timestamp | None) -> pd.Timestamp:
    if as_of is None:
        return pd.Timestamp.now()
    ts = pd.Timestamp(as_of)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    return ts


def get_open_lifecycle_positions(
    as_of: str | pd.Timestamp | None = None,
    path: Path | str | None = None,
) -> dict[str, dict]:
    """Return tickers whose latest PIT-safe lifecycle event is ENTER.

    Future-dated replay rows are ignored. The returned shape matches the
    position-memory contract consumed by portfolio universe construction.
    """
    df = read_lifecycle_log(path)
    if df.empty:
        return {}

    cutoff = _coerce_as_of(as_of)
    df = df[df["date"].notna() & (df["date"] <= cutoff)].copy()
    if df.empty:
        return {}

    open_positions: dict[str, dict] = {}
    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()
        action = str(row.get("action", "")).upper().strip()
        if not ticker:
            continue

        if action == "EXIT":
            open_positions.pop(ticker, None)
            continue

        if action != "ENTER":
            continue

        weight = pd.to_numeric(pd.Series([row.get("weight", 0.0)]), errors="coerce").fillna(0.0).iloc[0]
        date_value = row.get("date")
        if pd.isna(date_value):
            entry_date = ""
        else:
            entry_date = pd.Timestamp(date_value).isoformat()
        open_positions[ticker] = {
            "permno": row.get("permno"),
            "last_weight": max(float(weight), 0.0),
            "entry_date": entry_date,
            "last_updated": entry_date,
            "source": "lifecycle_replay",
            "last_reason": row.get("reason", ""),
            "last_rating": row.get("rating", ""),
        }

    return open_positions
