"""
Terminal Zero — Earnings Calendar Updater (FR-034)

Purpose:
  - Fetch upcoming/recent earnings dates from Yahoo Finance.
  - Persist a lightweight scanner-ready calendar table.
  - Integrate with lock + atomic write safety guarantees.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
CALENDAR_PATH = os.path.join(PROCESSED_DIR, "earnings_calendar.parquet")

CALENDAR_COLUMNS = [
    "permno",
    "ticker",
    "next_earnings_date",
    "last_earnings_date",
    "fetched_at",
    "source",
]


def _new_status() -> dict:
    return {
        "log": [],
        "success": False,
        "tickers_requested": 0,
        "tickers_fetched": 0,
        "rows_written": 0,
        "latest_next_earnings_date": None,
    }


def _log(status: dict, msg: str):
    print(msg)
    status["log"].append(msg)


def _normalize_tickers(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip().upper()
        if s:
            out.append(s)
    return list(dict.fromkeys(out))


def _scope_to_n(scope: str) -> int:
    s = str(scope).upper()
    if "3000" in s:
        return 3000
    if "500" in s:
        return 500
    if "200" in s:
        return 200
    if "100" in s:
        return 100
    if "50" in s:
        return 50
    if "20" in s:
        return 20
    return 100


def _resolve_targets(scope: str, custom_list: str | None) -> list[str]:
    if str(scope).upper() == "CUSTOM" and custom_list:
        return _normalize_tickers(custom_list.split(","))
    n = _scope_to_n(scope)
    return _normalize_tickers(updater.get_top_liquid_tickers(n))


def _to_naive_date(ts_like) -> pd.Timestamp | None:
    ts = pd.to_datetime(ts_like, errors="coerce")
    if pd.isna(ts):
        return None
    if getattr(ts, "tzinfo", None) is not None:
        ts = ts.tz_convert(None)
    return ts.normalize()


def _extract_candidate_dates(ticker_obj: yf.Ticker) -> list[pd.Timestamp]:
    dates: list[pd.Timestamp] = []

    # Primary source: full earnings dates table.
    try:
        e = ticker_obj.get_earnings_dates(limit=12)
    except Exception:
        e = pd.DataFrame()
    if isinstance(e, pd.DataFrame) and not e.empty:
        idx = pd.to_datetime(e.index, errors="coerce")
        idx = idx[~idx.isna()]
        if len(idx) > 0:
            if idx.tz is not None:
                idx = idx.tz_convert(None)
            dates.extend([pd.Timestamp(x).normalize() for x in idx.tolist()])

    # Fallback source: calendar endpoint.
    if not dates:
        try:
            cal = ticker_obj.calendar
        except Exception:
            cal = None
        if isinstance(cal, pd.DataFrame) and not cal.empty:
            for col in cal.columns:
                for val in cal[col].tolist():
                    ts = _to_naive_date(val)
                    if ts is not None:
                        dates.append(ts)
        elif isinstance(cal, dict):
            val = cal.get("Earnings Date") or cal.get("EarningsDate")
            if isinstance(val, (list, tuple, pd.Series, np.ndarray)):
                for x in val:
                    ts = _to_naive_date(x)
                    if ts is not None:
                        dates.append(ts)
            else:
                ts = _to_naive_date(val)
                if ts is not None:
                    dates.append(ts)

    if not dates:
        return []
    uniq = sorted(set(dates))
    return uniq


def _fetch_one(ticker: str, permno: int, asof_date: pd.Timestamp) -> dict:
    obj = yf.Ticker(ticker)
    candidates = _extract_candidate_dates(obj)
    next_dt = None
    last_dt = None
    if candidates:
        future = [d for d in candidates if d >= asof_date]
        past = [d for d in candidates if d < asof_date]
        next_dt = future[0] if future else None
        last_dt = past[-1] if past else None
    return {
        "permno": np.uint32(permno),
        "ticker": ticker,
        "next_earnings_date": next_dt,
        "last_earnings_date": last_dt,
        "fetched_at": pd.Timestamp.utcnow().tz_localize(None),
        "source": "yfinance",
    }


def _load_existing() -> pd.DataFrame:
    if not os.path.exists(CALENDAR_PATH):
        return pd.DataFrame(columns=CALENDAR_COLUMNS)
    try:
        df = pd.read_parquet(CALENDAR_PATH)
    except Exception:
        return pd.DataFrame(columns=CALENDAR_COLUMNS)

    for c in CALENDAR_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df = df[CALENDAR_COLUMNS]
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["permno"])
    df["permno"] = df["permno"].astype("uint32")
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    for c in ("next_earnings_date", "last_earnings_date", "fetched_at"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["source"] = df["source"].fillna("yfinance").astype(str)
    return df


def run_update(
    scope: str = "Top 100",
    custom_list: str | None = None,
    sleep_sec: float = 0.05,
    force_refresh: bool = False,
) -> dict:
    status = _new_status()
    _log(status, "=" * 58)
    _log(status, f"📅 Earnings Calendar Update (FR-034) — Scope: {scope}")
    _log(status, "=" * 58)

    if not os.path.exists(TICKERS_PATH):
        _log(status, "✗ Missing tickers.parquet. Run ETL/updater first.")
        return status

    targets = _resolve_targets(scope=scope, custom_list=custom_list)
    if not targets:
        _log(status, "✗ No target tickers found.")
        return status
    status["tickers_requested"] = len(targets)

    tmap = pd.read_parquet(TICKERS_PATH, columns=["permno", "ticker"])
    tmap["permno"] = pd.to_numeric(tmap["permno"], errors="coerce").astype("Int64")
    tmap = tmap.dropna(subset=["permno"])
    tmap["permno"] = tmap["permno"].astype(int)
    tmap["ticker"] = tmap["ticker"].astype(str).str.upper().str.strip()
    ticker_to_permno = dict(zip(tmap["ticker"], tmap["permno"]))

    unknown = [t for t in targets if t not in ticker_to_permno]
    if unknown:
        _log(status, f"⚠ Skipping {len(unknown)} symbols not in ticker map.")
    targets = [t for t in targets if t in ticker_to_permno]
    if not targets:
        _log(status, "✗ No mappable target tickers found.")
        return status

    try:
        updater._acquire_update_lock()
    except TimeoutError as e:
        _log(status, f"⏳ Update skipped: {e}")
        return status

    try:
        asof = pd.Timestamp.utcnow().tz_localize(None).normalize()
        existing = _load_existing()
        skip_today: set[str] = set()
        if not force_refresh and not existing.empty:
            fetched_today = pd.to_datetime(existing["fetched_at"], errors="coerce").dt.normalize()
            skip_today = set(existing.loc[fetched_today == asof, "ticker"].tolist())

        queue = [t for t in targets if t not in skip_today]
        _log(status, f"🎯 Targets: {len(targets)} | Fetch: {len(queue)} | Reuse today: {len(targets) - len(queue)}")
        rows: list[dict] = []
        for i, ticker in enumerate(queue, start=1):
            permno = int(ticker_to_permno[ticker])
            _log(status, f"[{i:>4}/{len(queue)}] Fetching {ticker} ...")
            try:
                rows.append(_fetch_one(ticker=ticker, permno=permno, asof_date=asof))
            except Exception as e:
                _log(status, f"      ⚠ Failed: {e}")
                continue
            status["tickers_fetched"] += 1
            if sleep_sec > 0:
                time.sleep(sleep_sec)

        new_df = pd.DataFrame(rows, columns=CALENDAR_COLUMNS) if rows else pd.DataFrame(columns=CALENDAR_COLUMNS)
        if new_df.empty:
            merged = existing.copy()
        elif existing.empty:
            merged = new_df.copy()
        else:
            merged = pd.concat([existing, new_df], ignore_index=True)

        if not merged.empty:
            merged["permno"] = pd.to_numeric(merged["permno"], errors="coerce").astype("Int64")
            merged = merged.dropna(subset=["permno"])
            merged["permno"] = merged["permno"].astype("uint32")
            merged["ticker"] = merged["ticker"].astype(str).str.upper().str.strip()
            for c in ("next_earnings_date", "last_earnings_date", "fetched_at"):
                merged[c] = pd.to_datetime(merged[c], errors="coerce")
            merged["source"] = merged["source"].fillna("yfinance").astype(str)
            merged = merged.sort_values(["permno", "fetched_at"]).drop_duplicates(subset=["permno"], keep="last")
            merged = merged[CALENDAR_COLUMNS].sort_values("ticker").reset_index(drop=True)

        updater.atomic_parquet_write(merged, CALENDAR_PATH, index=False)
        status["rows_written"] = int(len(merged))
        if not merged.empty and merged["next_earnings_date"].notna().any():
            status["latest_next_earnings_date"] = str(pd.to_datetime(merged["next_earnings_date"]).max().date())
        status["success"] = True
        _log(status, f"💾 earnings_calendar.parquet rows: {status['rows_written']:,}")
        if status["latest_next_earnings_date"]:
            _log(status, f"📌 Max upcoming earnings date: {status['latest_next_earnings_date']}")
        _log(status, "✅ Calendar update complete.")
    finally:
        updater._release_update_lock()

    return status


def main():
    parser = argparse.ArgumentParser(description="Terminal Zero Earnings Calendar Updater")
    parser.add_argument(
        "--scope",
        default="Top 100",
        help="'Top 20', 'Top 50', 'Top 100', 'Top 200', 'Top 500', 'Top 3000', or 'Custom'",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated tickers when --scope=Custom",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.05,
        help="Delay between Yahoo calls in seconds",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Fetch even if ticker was fetched today.",
    )
    args = parser.parse_args()
    result = run_update(
        scope=args.scope,
        custom_list=args.tickers,
        sleep_sec=max(0.0, float(args.sleep)),
        force_refresh=bool(args.force_refresh),
    )
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
