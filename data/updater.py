"""
Terminal Zero — Yahoo Bridge (Live Data Updater)

Architecture: "Append-Only Hybrid Lake"
  - Base layer:  prices.parquet  (47M rows, WRDS 2000-2024, NEVER touched)
  - Patch layer: yahoo_patch.parquet (Yahoo 2025+, partitioned incremental upserts)
  - app.py reads BOTH via DuckDB UNION ALL

Features:
  - Batch download via yf.download([...]) — 50x faster than looping
  - Memory-safe: never loads base parquet into pandas
  - Idempotent: safe to run multiple times
  - Dashboard API: run_update() returns status dict for UI display
"""

import datetime
import ctypes
import glob
import logging
import os
import shutil
import sys
import time

import numpy as np
import pandas as pd
import duckdb
import yfinance as yf

# CONFIG
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
from utils.parallel import parallel_execute  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
MACRO_PATH = os.path.join(PROCESSED_DIR, "macro.parquet")
UPDATE_LOCK_PATH = os.path.join(PROCESSED_DIR, ".update.lock")
UPDATE_LOCK_TIMEOUT_SEC = 180
UPDATE_LOCK_POLL_SEC = 0.25
# Crash-safety: only break a lock when it is clearly stale.
UPDATE_LOCK_STALE_SEC = max(UPDATE_LOCK_TIMEOUT_SEC * 4, 900)
YAHOO_CHUNK_SIZE = 64
YAHOO_MAX_WORKERS = 8
PATCH_COLUMNS = ["date", "permno", "raw_close", "adj_close", "total_ret", "volume"]
PATCH_PART_FILE = "part-0.parquet"
logger = logging.getLogger(__name__)
_OWNED_UPDATE_LOCK_TOKEN: str | None = None


# ── Liquidity Ranking (DuckDB — memory safe) ───────────────────────────────


def _safe_remove_path(path: str) -> None:
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        return
    try:
        os.remove(path)
    except OSError:
        pass


def _list_existing_paths_sorted(pattern: str) -> list[str]:
    ranked: list[tuple[float, str]] = []
    for candidate in glob.glob(pattern):
        try:
            ranked.append((float(os.path.getmtime(candidate)), candidate))
        except OSError:
            continue
    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [item[1] for item in ranked]


def atomic_parquet_write(df: pd.DataFrame, filename: str, index: bool = False):
    """
    Write parquet atomically:
      1) write to temp file
      2) os.replace -> single metadata swap
    """
    temp_file = f"{filename}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        df.to_parquet(temp_file, index=index)
        os.replace(temp_file, filename)
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass


def _parse_lock_payload(payload: str) -> tuple[int, int, str]:
    try:
        tokens = dict(part.split("=", 1) for part in str(payload).split() if "=" in part)
        pid = int(tokens.get("pid", "0"))
        ts = int(tokens.get("ts", "0"))
        token = str(tokens.get("token", "")).strip()
        return pid, ts, token
    except Exception:
        return 0, 0, ""


def _pid_is_running(pid: int) -> bool:
    if int(pid) <= 0:
        return False
    if os.name == "nt":
        # Windows-safe probe: never use os.kill(pid, 0) here.
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        ERROR_ACCESS_DENIED = 5
        ERROR_INVALID_PARAMETER = 87
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            open_process = kernel32.OpenProcess
            open_process.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
            open_process.restype = ctypes.c_void_p
            get_exit_code = kernel32.GetExitCodeProcess
            get_exit_code.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            get_exit_code.restype = ctypes.c_int
            close_handle = kernel32.CloseHandle
            close_handle.argtypes = [ctypes.c_void_p]
            close_handle.restype = ctypes.c_int

            handle = open_process(PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid))
            if not handle:
                err = ctypes.get_last_error()
                if err == ERROR_ACCESS_DENIED:
                    return True
                if err == ERROR_INVALID_PARAMETER:
                    return False
                return False

            try:
                exit_code = ctypes.c_uint32(0)
                ok = get_exit_code(handle, ctypes.byref(exit_code))
                if not ok:
                    err = ctypes.get_last_error()
                    if err == ERROR_ACCESS_DENIED:
                        return True
                    return True
                return int(exit_code.value) == STILL_ACTIVE
            finally:
                close_handle(handle)
        except Exception:
            # Conservative fallback to avoid deleting a potentially live owner lock.
            return True

    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _update_lock_owner_live(*, allow_self_owner: bool = False) -> bool:
    if not os.path.exists(UPDATE_LOCK_PATH):
        return False
    try:
        with open(UPDATE_LOCK_PATH, "r", encoding="utf-8") as f:
            payload_raw = f.read().strip()
        lock_pid, _lock_ts, _token = _parse_lock_payload(payload_raw)
    except Exception:
        # Conservative: if lock metadata cannot be parsed, do not recover swap targets.
        return True
    if int(lock_pid) <= 0:
        return True
    if allow_self_owner and int(lock_pid) == int(os.getpid()):
        return False
    return _pid_is_running(lock_pid)


def _recover_backup_swap(target_path: str, backup_pattern: str) -> bool:
    backups = _list_existing_paths_sorted(backup_pattern)
    if not backups:
        return False
    if os.path.exists(target_path):
        for stale in backups:
            _safe_remove_path(stale)
        return True
    if _update_lock_owner_live(allow_self_owner=True):
        return False

    restore_from = backups[0]
    parent = os.path.dirname(target_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    os.replace(restore_from, target_path)
    for stale in backups[1:]:
        _safe_remove_path(stale)
    logger.warning(
        "Recovered interrupted atomic swap target=%s from backup=%s",
        target_path,
        restore_from,
    )
    return True


def _recover_patch_root_swap_if_needed(patch_path: str) -> bool:
    return _recover_backup_swap(patch_path, f"{patch_path}.legacy_bak.*")


def _recover_partition_swap_if_needed(partition_dir: str) -> bool:
    return _recover_backup_swap(partition_dir, f"{partition_dir}.bak.*")


def _acquire_update_lock(timeout_sec: int = UPDATE_LOCK_TIMEOUT_SEC) -> str:
    """
    Simple cross-process file lock using O_EXCL create.
    Raises TimeoutError if another updater holds the lock too long.
    """
    start_ts = time.time()
    while True:
        try:
            fd = os.open(UPDATE_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            lock_token = f"{os.getpid()}-{int(time.time() * 1000000)}"
            with os.fdopen(fd, "w") as f:
                f.write(f"pid={os.getpid()} ts={int(start_ts)} token={lock_token}")
            global _OWNED_UPDATE_LOCK_TOKEN
            _OWNED_UPDATE_LOCK_TOKEN = lock_token
            return lock_token
        except FileExistsError:
            # Recover from stale lock files left by crashed/terminated writers.
            payload_raw = ""
            try:
                with open(UPDATE_LOCK_PATH, "r", encoding="utf-8") as f:
                    payload_raw = f.read().strip()
                lock_pid, lock_ts, _lock_token = _parse_lock_payload(payload_raw)
            except Exception:
                lock_pid = 0
                lock_ts = 0

            now = time.time()
            lock_is_stale = lock_ts > 0 and (now - lock_ts) >= UPDATE_LOCK_STALE_SEC
            owner_alive = _pid_is_running(lock_pid)

            if lock_is_stale and not owner_alive:
                try:
                    # Token/payload recheck prevents deleting a newly-acquired lock file.
                    with open(UPDATE_LOCK_PATH, "r", encoding="utf-8") as f:
                        latest_payload = f.read().strip()
                    if payload_raw and latest_payload != payload_raw:
                        continue
                    os.remove(UPDATE_LOCK_PATH)
                    logger.warning(
                        "Removed stale update lock older than %ss: %s",
                        UPDATE_LOCK_STALE_SEC,
                        UPDATE_LOCK_PATH,
                    )
                    continue
                except FileNotFoundError:
                    continue
                except OSError:
                    pass

            if time.time() - start_ts >= timeout_sec:
                raise TimeoutError("another update is already running")
            time.sleep(UPDATE_LOCK_POLL_SEC)


def _release_update_lock(expected_token: str | None = None):
    global _OWNED_UPDATE_LOCK_TOKEN
    token = expected_token or _OWNED_UPDATE_LOCK_TOKEN
    if not token:
        logger.warning("Skipping lock release because no ownership token is available.")
        return
    try:
        if token and os.path.exists(UPDATE_LOCK_PATH):
            try:
                with open(UPDATE_LOCK_PATH, "r", encoding="utf-8") as f:
                    payload_raw = f.read().strip()
                _pid, _ts, live_token = _parse_lock_payload(payload_raw)
                if live_token and live_token != token:
                    logger.warning(
                        "Skipping lock release due to token mismatch (expected=%s, actual=%s).",
                        token,
                        live_token,
                    )
                    return
            except Exception:
                pass
        os.remove(UPDATE_LOCK_PATH)
    except FileNotFoundError:
        pass
    finally:
        if expected_token is None or _OWNED_UPDATE_LOCK_TOKEN == expected_token:
            _OWNED_UPDATE_LOCK_TOKEN = None


def _sql_escape_path(path: str) -> str:
    return str(path).replace("'", "''")


def _empty_patch_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=PATCH_COLUMNS)


def _normalize_patch_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return _empty_patch_frame()

    normalized = frame.copy()
    normalized = normalized.drop(columns=["year", "month"], errors="ignore")
    for col in PATCH_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = np.nan

    normalized = normalized[PATCH_COLUMNS]
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce").dt.tz_localize(None)
    normalized = normalized.dropna(subset=["date", "permno"])
    return normalized.reset_index(drop=True)


def _dedupe_patch_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    deduped = frame.copy()
    deduped["_source_idx"] = np.arange(len(deduped), dtype=np.int64)
    deduped = deduped.sort_values(["permno", "date", "_source_idx"])
    deduped = deduped.drop_duplicates(subset=["permno", "date"], keep="last")
    deduped = deduped.drop(columns=["_source_idx"])
    return deduped.sort_values(["permno", "date"]).reset_index(drop=True)


def _patch_with_partitions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        out = frame.copy()
        out["year"] = pd.Series(dtype="int64")
        out["month"] = pd.Series(dtype="int64")
        return out

    out = frame.copy()
    out["year"] = out["date"].dt.year.astype(int)
    out["month"] = out["date"].dt.month.astype(int)
    return out


def _patch_partition_dir(root_path: str, year: int, month: int) -> str:
    return os.path.join(root_path, f"year={int(year):04d}", f"month={int(month):02d}")


def _count_patch_rows(patch_path: str) -> int:
    _recover_patch_root_swap_if_needed(patch_path)
    if not os.path.exists(patch_path):
        return 0

    con = duckdb.connect()
    try:
        escaped = _sql_escape_path(patch_path)
        count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{escaped}')").fetchone()[0]
        return int(count or 0)
    except Exception:
        try:
            fallback = pd.read_parquet(patch_path)
            return int(len(fallback))
        except Exception:
            return 0
    finally:
        con.close()


def _read_full_patch_rows(patch_path: str) -> pd.DataFrame:
    _recover_patch_root_swap_if_needed(patch_path)
    if not os.path.exists(patch_path):
        return _empty_patch_frame()

    try:
        frame = pd.read_parquet(patch_path)
    except Exception:
        return _empty_patch_frame()
    frame = _normalize_patch_rows(frame)
    if frame.empty:
        return frame
    return _dedupe_patch_rows(frame)


def _read_partition_rows(patch_path: str, year: int, month: int) -> pd.DataFrame:
    _recover_patch_root_swap_if_needed(patch_path)
    if not os.path.isdir(patch_path):
        return _empty_patch_frame()

    partition_dir = _patch_partition_dir(patch_path, year=year, month=month)
    _recover_partition_swap_if_needed(partition_dir)
    if not os.path.exists(partition_dir):
        return _empty_patch_frame()

    try:
        frame = pd.read_parquet(partition_dir)
    except Exception:
        logger.exception(
            "Failed reading patch partition year=%s month=%s path=%s",
            year,
            month,
            partition_dir,
        )
        raise
    return _normalize_patch_rows(frame)


def _atomic_partition_swap(
    patch_path: str,
    *,
    year: int,
    month: int,
    partition_df: pd.DataFrame,
):
    partition_dir = _patch_partition_dir(patch_path, year=year, month=month)
    year_dir = os.path.dirname(partition_dir)
    os.makedirs(year_dir, exist_ok=True)
    _recover_partition_swap_if_needed(partition_dir)

    stamp = f"{os.getpid()}.{int(time.time() * 1000)}"
    staged_dir = os.path.join(year_dir, f".stage.month={int(month):02d}.{stamp}")
    backup_dir = f"{partition_dir}.bak.{stamp}"
    staged_file = os.path.join(staged_dir, PATCH_PART_FILE)
    has_existing = os.path.exists(partition_dir)

    os.makedirs(staged_dir, exist_ok=False)
    partition_df.to_parquet(staged_file, index=False)

    if has_existing:
        os.replace(partition_dir, backup_dir)

    try:
        os.replace(staged_dir, partition_dir)
    except Exception:
        if has_existing and os.path.exists(backup_dir) and not os.path.exists(partition_dir):
            os.replace(backup_dir, partition_dir)
        raise
    finally:
        if os.path.exists(staged_dir):
            _safe_remove_path(staged_dir)

    if has_existing and os.path.exists(backup_dir):
        _safe_remove_path(backup_dir)


def _write_partition_dataset(frame: pd.DataFrame, *, dataset_root: str):
    partitioned = _patch_with_partitions(_dedupe_patch_rows(_normalize_patch_rows(frame)))
    if partitioned.empty:
        return

    for (year, month), group in partitioned.groupby(["year", "month"], sort=True, dropna=False):
        part_rows = _normalize_patch_rows(group.drop(columns=["year", "month"], errors="ignore"))
        if part_rows.empty:
            continue

        partition_dir = _patch_partition_dir(dataset_root, year=int(year), month=int(month))
        os.makedirs(partition_dir, exist_ok=True)
        part_file = os.path.join(partition_dir, PATCH_PART_FILE)
        part_rows.to_parquet(part_file, index=False)


def _migrate_legacy_patch_to_partitioned(patch_path: str):
    _recover_patch_root_swap_if_needed(patch_path)
    if not os.path.isfile(patch_path):
        return

    legacy_rows = _read_full_patch_rows(patch_path)
    stamp = f"{os.getpid()}.{int(time.time() * 1000)}"
    staged_root = f"{patch_path}.stage_migrate.{stamp}"
    backup_file = f"{patch_path}.legacy_bak.{stamp}"

    try:
        os.makedirs(staged_root, exist_ok=False)
        if not legacy_rows.empty:
            _write_partition_dataset(legacy_rows, dataset_root=staged_root)

        os.replace(patch_path, backup_file)
        try:
            os.replace(staged_root, patch_path)
        except Exception:
            if os.path.exists(backup_file) and not os.path.exists(patch_path):
                os.replace(backup_file, patch_path)
            raise
    finally:
        if os.path.exists(staged_root):
            _safe_remove_path(staged_root)

    if os.path.exists(backup_file):
        _safe_remove_path(backup_file)


def _upsert_partitioned_patch_rows(
    incoming_rows: pd.DataFrame,
    *,
    patch_path: str,
) -> tuple[list[str], int]:
    incoming = _dedupe_patch_rows(_normalize_patch_rows(incoming_rows))
    if incoming.empty:
        return [], 0

    _recover_patch_root_swap_if_needed(patch_path)
    if os.path.isfile(patch_path):
        _migrate_legacy_patch_to_partitioned(patch_path)
    if os.path.exists(patch_path) and not os.path.isdir(patch_path):
        raise RuntimeError(f"Patch path is not a directory dataset: {patch_path}")
    os.makedirs(patch_path, exist_ok=True)

    incoming = _patch_with_partitions(incoming)
    touched_keys = sorted(
        {(int(year), int(month)) for year, month in zip(incoming["year"], incoming["month"])}
    )
    touched_partitions: list[str] = []
    rows_upserted = 0

    for year, month in touched_keys:
        new_rows = incoming[(incoming["year"] == year) & (incoming["month"] == month)]
        new_rows = _normalize_patch_rows(new_rows.drop(columns=["year", "month"], errors="ignore"))
        if new_rows.empty:
            continue

        existing_rows = _read_partition_rows(patch_path, year=year, month=month)
        if existing_rows.empty:
            merged_rows = _dedupe_patch_rows(new_rows)
        else:
            merged_rows = _dedupe_patch_rows(
                pd.concat([existing_rows, new_rows], ignore_index=True)
            )
        _atomic_partition_swap(
            patch_path,
            year=year,
            month=month,
            partition_df=merged_rows,
        )
        touched_partitions.append(f"{year:04d}-{month:02d}")
        rows_upserted += int(len(new_rows))

    return touched_partitions, rows_upserted


def publish_patch_rows(
    patch_rows: pd.DataFrame,
    *,
    patch_path: str = PATCH_PATH,
    lock_already_held: bool = False,
    timeout_sec: int = UPDATE_LOCK_TIMEOUT_SEC,
) -> tuple[pd.DataFrame, int]:
    """
    Patch write facade with serialized lock + atomic partitioned upsert.

    Args:
        patch_rows: New long-format patch rows to merge/write.
        patch_path: Destination patch dataset root path.
        lock_already_held: True when caller already owns UPDATE_LOCK_PATH.
        timeout_sec: Lock wait timeout when lock_already_held is False.

    Returns:
        (combined_patch_df, previous_patch_row_count)
    """
    previous_count = 0
    should_release_lock = False
    lock_token: str | None = None
    if not lock_already_held:
        lock_token = _acquire_update_lock(timeout_sec=timeout_sec)
        should_release_lock = True

    try:
        _recover_patch_root_swap_if_needed(patch_path)
        previous_count = _count_patch_rows(patch_path)
        if not os.path.exists(patch_path):
            bootstrap = _dedupe_patch_rows(_normalize_patch_rows(patch_rows))
            if not bootstrap.empty:
                # Compatibility bootstrap: preserve root-path atomic write semantics for first publish.
                atomic_parquet_write(bootstrap, patch_path, index=False)
        touched_partitions, rows_upserted = _upsert_partitioned_patch_rows(
            patch_rows,
            patch_path=patch_path,
        )
        combined = _read_full_patch_rows(patch_path)
        combined.attrs["touched_partitions"] = touched_partitions
        combined.attrs["rows_upserted"] = int(rows_upserted)
        return combined, previous_count
    finally:
        if should_release_lock:
            _release_update_lock(expected_token=lock_token)


def get_top_liquid_tickers(n: int = 50) -> list[str]:
    """
    Returns the top N ticker symbols ranked by total dollar volume.
    Uses DuckDB to query parquet without loading into pandas.
    """
    con = duckdb.connect()

    # Build source: base + patch if patch exists
    if os.path.exists(PATCH_PATH):
        src = f"""(
            SELECT permno, adj_close, volume FROM '{PRICES_PATH}'
            UNION ALL
            SELECT permno, adj_close, volume FROM '{PATCH_PATH}'
        )"""
    else:
        src = f"'{PRICES_PATH}'"

    # Rank by total dollar volume
    top_df = con.execute(f"""
        SELECT s.permno, t.ticker, SUM(s.adj_close * s.volume) as dollar_vol
        FROM {src} s
        JOIN '{TICKERS_PATH}' t ON s.permno = t.permno
        WHERE s.volume > 0
        GROUP BY s.permno, t.ticker
        ORDER BY dollar_vol DESC
        LIMIT {n}
    """).df()

    con.close()
    return top_df["ticker"].tolist()


# ── Batch Yahoo Download ───────────────────────────────────────────────────


def fetch_quarterly_fundamental_frames(
    ticker: str,
    ticker_obj: object | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Fetch quarterly financial statements from Yahoo for one ticker.

    Returns a dict with keys:
      - income: quarterly income statement
      - balance: quarterly balance sheet
      - cashflow: quarterly cash flow statement

    This is a thin, failure-tolerant fetch utility used by the fundamentals
    data layer. It does not enforce schema because source line-item labels may
    vary by ticker.
    """
    symbol = str(ticker).strip().upper()
    tk = ticker_obj if ticker_obj is not None else yf.Ticker(symbol)

    out: dict[str, pd.DataFrame] = {}
    for key, attr in (
        ("income", "quarterly_income_stmt"),
        ("balance", "quarterly_balance_sheet"),
        ("cashflow", "quarterly_cashflow"),
    ):
        try:
            frame = getattr(tk, attr)
            if not isinstance(frame, pd.DataFrame):
                frame = pd.DataFrame()
        except Exception:
            frame = pd.DataFrame()
        out[key] = frame
    return out


def batch_download_yahoo(
    tickers_list: list[str], start_date: str, threads: bool = True
) -> pd.DataFrame:
    """
    Download multiple tickers in ONE yfinance call (parallel, batched).
    Returns a long-format DataFrame: date, ticker, raw_close, adj_close, total_ret, volume.
    """
    if not tickers_list:
        return pd.DataFrame()

    try:
        raw = yf.download(
            tickers_list,
            start=start_date,
            progress=False,
            auto_adjust=False,
            threads=bool(threads),
        )

        if raw.empty:
            return pd.DataFrame()

        if isinstance(raw.columns, pd.MultiIndex):
            # Multi-ticker: columns are (Attribute, Ticker)
            stacked = raw.stack(level=1, future_stack=True).reset_index()
            # Rename the ticker level column
            col_names = stacked.columns.tolist()
            # The stacked level might be named 'Ticker', 'level_1', or the ticker index name
            ticker_col = [c for c in col_names if c not in [
                "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"
            ]]
            if ticker_col:
                stacked = stacked.rename(columns={ticker_col[0]: "ticker"})
        else:
            # Single ticker: flat columns
            stacked = raw.reset_index()
            stacked["ticker"] = tickers_list[0]

        stacked = stacked.rename(columns={
            "Date": "date",
            "Close": "raw_close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        })

        # Strip timezone from dates
        stacked["date"] = pd.to_datetime(stacked["date"]).dt.tz_localize(None)

        # Calculate per-ticker returns
        stacked = stacked.sort_values(["ticker", "date"])
        stacked["total_ret"] = (
            stacked.groupby("ticker")["adj_close"].pct_change().fillna(0.0)
        )

        return stacked[["date", "ticker", "raw_close", "adj_close", "total_ret", "volume"]]

    except Exception:
        logger.exception(
            "Yahoo batch download failed (tickers=%s, start_date=%s)",
            tickers_list,
            start_date,
        )
        failed = pd.DataFrame()
        failed.attrs["chunk_failed"] = True
        return failed


def _chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
    if chunk_size <= 0:
        return [items]
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _download_chunk(tickers_chunk: list[str], start_date: str) -> pd.DataFrame:
    # Avoid nested thread pools: chunk-level concurrency is managed by parallel_execute.
    return batch_download_yahoo(tickers_chunk, start_date, threads=False)


def parallel_batch_download_yahoo(
    tickers_list: list[str],
    start_date: str,
    chunk_size: int = YAHOO_CHUNK_SIZE,
    max_workers: int = YAHOO_MAX_WORKERS,
) -> pd.DataFrame:
    """
    Download Yahoo data in chunked parallel batches.
    Falls back to sequential execution when chunks/workers collapse to 1.
    """
    clean_tickers = sorted({str(t).upper().strip() for t in tickers_list if str(t).strip()})
    if not clean_tickers:
        return pd.DataFrame()

    chunks = _chunk_list(clean_tickers, chunk_size=max(1, int(chunk_size)))
    tasks = [(chunk, start_date) for chunk in chunks]
    results = parallel_execute(
        func=_download_chunk,
        tasks=tasks,
        n_jobs=max_workers,
        desc="yahoo_download",
        backend="threading",
        fail_fast=False,
    )
    failed_chunks = sum(
        1
        for item in results
        if item is None
        or (isinstance(item, pd.DataFrame) and bool(item.attrs.get("chunk_failed", False)))
    )
    total_chunks = len(results)
    frames = [
        df
        for df in results
        if isinstance(df, pd.DataFrame)
        and not bool(df.attrs.get("chunk_failed", False))
        and not df.empty
    ]
    if not frames:
        empty = pd.DataFrame()
        empty.attrs["failed_chunks"] = int(failed_chunks)
        empty.attrs["total_chunks"] = int(total_chunks)
        empty.attrs["all_chunks_failed"] = bool(total_chunks > 0 and failed_chunks == total_chunks)
        return empty

    merged = pd.concat(frames, ignore_index=True)
    if {"ticker", "date"}.issubset(set(merged.columns)):
        merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.tz_localize(None)
        merged = (
            merged.sort_values(["ticker", "date"])
            .drop_duplicates(subset=["ticker", "date"], keep="last")
            .reset_index(drop=True)
        )
    merged.attrs["failed_chunks"] = int(failed_chunks)
    merged.attrs["total_chunks"] = int(total_chunks)
    merged.attrs["all_chunks_failed"] = bool(total_chunks > 0 and failed_chunks == total_chunks)
    return merged


# ── Main Update Function (Dashboard API) ───────────────────────────────────


def run_update(
    scope: str = "Top 50",
    custom_list: str | None = None,
) -> dict:
    """
    Main entry point — called from dashboard or CLI.

    Args:
        scope: "Top 50", "Top 100", "Top 200", "Top 500", "Top 3000", or "Custom"
        custom_list: Comma-separated tickers (only when scope="Custom")

    Returns:
        dict with keys: log (list[str]), success (bool), tickers_updated (int)
    """
    status = {
        "log": [],
        "success": False,
        "tickers_updated": 0,
        "last_date": None,
        "touched_partitions": [],
        "rows_upserted": 0,
    }

    def log(msg: str):
        print(msg)
        status["log"].append(msg)

    log("=" * 50)
    log(f"🚀 Yahoo Bridge Update — Scope: {scope}")
    log("=" * 50)

    lock_token: str | None = None
    try:
        lock_token = _acquire_update_lock()
    except TimeoutError as e:
        log(f"⏳ Update skipped: {e}")
        return status

    # ── 1. Validate prerequisites ───────────────────────────────────────────
    try:
        for path, name in [(PRICES_PATH, "prices"), (TICKERS_PATH, "tickers")]:
            if not os.path.exists(path):
                log(f"✗ Missing {name}.parquet. Run etl.py first.")
                return status

        # ── 2. Load metadata via DuckDB (no pandas OOM risk) ────────────────────
        con = duckdb.connect()
        try:
            # Determine last system date (from base OR existing patch)
            if os.path.exists(PATCH_PATH):
                last_date_val = con.execute(f"""
                    SELECT MAX(d) FROM (
                        SELECT MAX(date) as d FROM '{PRICES_PATH}'
                        UNION ALL
                        SELECT MAX(date) as d FROM '{PATCH_PATH}'
                    )
                """).fetchone()[0]
            else:
                last_date_val = con.execute(
                    f"SELECT MAX(date) FROM '{PRICES_PATH}'"
                ).fetchone()[0]

            last_date = pd.to_datetime(last_date_val)
            start_date = (last_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            today = datetime.datetime.now()

            log(f"📅 System Date : {last_date.date()}")
            log(f"📅 Target Date : {today.date()}")

            if pd.to_datetime(start_date) > today:
                log("✅ Data is already up to date.")
                status["success"] = True
                status["last_date"] = str(last_date.date())
                return status

            # ── 3. Determine target tickers ─────────────────────────────────────────
            tickers_df = con.execute(f"SELECT * FROM '{TICKERS_PATH}'").df()
            t2p = dict(zip(tickers_df["ticker"], tickers_df["permno"]))

            if scope == "Custom" and custom_list:
                target_tickers = [t.strip().upper() for t in custom_list.split(",") if t.strip()]
            else:
                n = 50
                if "3000" in scope:
                    n = 3000
                elif "500" in scope:
                    n = 500
                elif "200" in scope:
                    n = 200
                elif "100" in scope:
                    n = 100
                log(f"🔍 Ranking top {n} by liquidity...")
                target_tickers = get_top_liquid_tickers(n)

            # Always include SPY for macro
            if "SPY" not in target_tickers:
                target_tickers.append("SPY")
            target_tickers = sorted({str(t).upper().strip() for t in target_tickers if str(t).strip()})

            log(f"📦 Downloading {len(target_tickers)} tickers from {start_date} ...")

            # ── 4. Batch download from Yahoo ────────────────────────────────────────
            new_data = parallel_batch_download_yahoo(
                target_tickers,
                start_date,
                chunk_size=YAHOO_CHUNK_SIZE,
                max_workers=YAHOO_MAX_WORKERS,
            )
            all_chunks_failed = bool(new_data.attrs.get("all_chunks_failed", False))
            failed_chunks = int(new_data.attrs.get("failed_chunks", 0))
            total_chunks = int(new_data.attrs.get("total_chunks", 0))

            if new_data.empty:
                if all_chunks_failed:
                    log(
                        f"✗ Yahoo download failed across all chunks ({failed_chunks}/{total_chunks}). "
                        "Treating as update failure."
                    )
                    status["success"] = False
                    status["tickers_updated"] = 0
                    status["last_date"] = str(last_date.date())
                    return status
                log("ℹ No new Yahoo rows returned. Treating as no-op success (market closed/holiday or unchanged data).")
                status["success"] = True
                status["tickers_updated"] = 0
                status["last_date"] = str(last_date.date())
                return status
            if failed_chunks > 0:
                log(
                    f"✗ Yahoo partial download failures: {failed_chunks}/{total_chunks} chunks failed. "
                    "Aborting update before writes to preserve complete truth-layer refresh semantics."
                )
                status["success"] = False
                status["tickers_updated"] = 0
                status["last_date"] = str(last_date.date())
                status["failed_chunks"] = failed_chunks
                status["total_chunks"] = total_chunks
                return status

            downloaded_tickers = new_data["ticker"].unique()
            log(f"✓ Downloaded {len(downloaded_tickers)} tickers, {len(new_data):,} rows")

            # ── 5. Map tickers → permnos ────────────────────────────────────────────
            max_permno = int(tickers_df["permno"].max())
            next_permno = max(900000, max_permno + 1)
            new_ticker_count = 0

            rows = []
            for ticker in downloaded_tickers:
                if ticker not in t2p:
                    log(f"   🆕 New: {ticker} → ID {next_permno}")
                    t2p[ticker] = next_permno
                    next_permno += 1
                    new_ticker_count += 1

                subset = new_data[new_data["ticker"] == ticker].copy()
                subset["permno"] = np.uint32(t2p[ticker])
                rows.append(subset[["date", "permno", "raw_close", "adj_close", "total_ret", "volume"]])

            patch_df = pd.concat(rows, ignore_index=True)

            # ── 6. Save ticker map first (prevents permno-map drift on patch publish) ─
            new_map = pd.DataFrame(
                [{"permno": np.uint32(v), "ticker": k} for k, v in t2p.items()]
            )
            atomic_parquet_write(new_map, TICKERS_PATH, index=False)
            log(f"💾 Ticker map: {len(new_map)} entries ({new_ticker_count} new)")
            combined, previous_patch_rows = publish_patch_rows(
                patch_df,
                patch_path=PATCH_PATH,
                lock_already_held=True,
            )
            status["touched_partitions"] = list(combined.attrs.get("touched_partitions", []))
            status["rows_upserted"] = int(combined.attrs.get("rows_upserted", len(patch_df)))
            if previous_patch_rows > 0:
                patch_write_msg = (
                    f"💾 Patch updated: {len(combined):,} total rows "
                    f"(was {previous_patch_rows:,})"
                )
            else:
                patch_write_msg = f"💾 Patch created: {len(combined):,} rows"
            log(patch_write_msg)
            if status["touched_partitions"]:
                log(
                    "   ↳ partitions touched: "
                    f"{len(status['touched_partitions'])} ({', '.join(status['touched_partitions'])})"
                )
            log(f"   ↳ rows upserted: {status['rows_upserted']:,}")

            # ── 7. Rebuild macro (SPY + VIX Proxy) ──────────────────────────────────
            log("📊 Rebuilding macro (SPY + VIX Proxy) ...")
            spy_permno = t2p.get("SPY")

            if spy_permno is None:
                log("   ⚠ SPY not found! Macro NOT updated.")
            else:
                spy_df = con.execute(f"""
                    SELECT date, adj_close, total_ret
                    FROM (
                        SELECT date, adj_close, total_ret FROM '{PRICES_PATH}'
                        WHERE permno = {spy_permno}
                        UNION ALL
                        SELECT date, adj_close, total_ret FROM '{PATCH_PATH}'
                        WHERE permno = {spy_permno}
                    )
                    ORDER BY date
                """).df()

                # Deduplicate SPY (patch priority)
                spy_df = spy_df.drop_duplicates(subset=["date"], keep="last")

                spy_df["vix_proxy"] = (
                    spy_df["total_ret"].rolling(20).std() * np.sqrt(252) * 100
                )
                new_macro = spy_df[["date", "adj_close", "vix_proxy"]].rename(
                    columns={"adj_close": "spy_close"}
                )
                new_macro = new_macro.dropna(subset=["vix_proxy"])
                if new_macro.empty:
                    log("   ⚠ Macro rebuild skipped (insufficient SPY history for vix_proxy window).")
                else:
                    atomic_parquet_write(new_macro, MACRO_PATH, index=False)
                    latest_vix = new_macro.iloc[-1]["vix_proxy"]
                    latest_spy = new_macro.iloc[-1]["spy_close"]
                    log(f"   SPY: ${latest_spy:.2f} | VIX: {latest_vix:.1f}")

            # ── Done ────────────────────────────────────────────────────────────────
            new_last = patch_df["date"].max().date()
            status["success"] = True
            status["tickers_updated"] = len(downloaded_tickers)
            status["last_date"] = str(new_last)

            log("")
            log(f"✅ COMPLETE. {len(downloaded_tickers)} tickers → {new_last}")
            log("=" * 50)
            return status
        finally:
            con.close()
    finally:
        _release_update_lock(expected_token=lock_token)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Yahoo Bridge Updater")
    parser.add_argument(
        "--scope", default="Top 50",
        help="'Top 50', 'Top 100', 'Top 200', 'Top 500', 'Top 3000', or 'Custom'"
    )
    parser.add_argument(
        "--tickers", default=None,
        help="Comma-separated tickers (when --scope=Custom)"
    )
    args = parser.parse_args()

    result = run_update(scope=args.scope, custom_list=args.tickers)
    if not result["success"]:
        sys.exit(1)
