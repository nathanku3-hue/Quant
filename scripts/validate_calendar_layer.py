"""
Validate earnings calendar layer integrity for FR-034.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CALENDAR_PATH = os.path.join(PROCESSED_DIR, "earnings_calendar.parquet")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")

REQUIRED_COLUMNS = {
    "permno",
    "ticker",
    "next_earnings_date",
    "last_earnings_date",
    "fetched_at",
    "source",
}


def _print(msg: str):
    print(msg)


def validate() -> int:
    _print("🧪 Calendar Layer Validation (FR-034)")
    _print("=" * 58)

    if not os.path.exists(CALENDAR_PATH):
        _print(f"❌ Missing file: {CALENDAR_PATH}")
        return 1
    if not os.path.exists(TICKERS_PATH):
        _print(f"❌ Missing file: {TICKERS_PATH}")
        return 1

    cal = pd.read_parquet(CALENDAR_PATH)
    if cal.empty:
        _print("❌ earnings_calendar.parquet is empty.")
        return 1

    missing = REQUIRED_COLUMNS - set(cal.columns)
    if missing:
        _print(f"❌ Missing required columns: {sorted(missing)}")
        return 1

    cal["permno"] = pd.to_numeric(cal["permno"], errors="coerce").astype("Int64")
    cal = cal.dropna(subset=["permno"]).copy()
    cal["permno"] = cal["permno"].astype("int64")
    cal["ticker"] = cal["ticker"].astype(str).str.upper().str.strip()
    cal["next_earnings_date"] = pd.to_datetime(cal["next_earnings_date"], errors="coerce")
    cal["last_earnings_date"] = pd.to_datetime(cal["last_earnings_date"], errors="coerce")
    cal["fetched_at"] = pd.to_datetime(cal["fetched_at"], errors="coerce")

    dupes = int(cal.duplicated(subset=["permno"]).sum())
    events_known = cal["next_earnings_date"].notna() | cal["last_earnings_date"].notna()
    known_ratio = float(events_known.mean()) if len(cal) else 0.0

    now = pd.Timestamp.utcnow().tz_localize(None).normalize()
    stale_ratio = float((now - cal["fetched_at"]).dt.days.gt(14).fillna(True).mean()) if len(cal) else 1.0
    upcoming_5d = int(((cal["next_earnings_date"] - now).dt.days.between(0, 4, inclusive="both")).sum())
    fresh_7d = int(((now - cal["last_earnings_date"]).dt.days.between(0, 7, inclusive="both")).sum())

    tmap = pd.read_parquet(TICKERS_PATH, columns=["permno"])
    tmap["permno"] = pd.to_numeric(tmap["permno"], errors="coerce").astype("Int64")
    tmap = tmap.dropna(subset=["permno"])
    mapped = int(cal["permno"].isin(tmap["permno"].astype("int64")).sum())
    map_ratio = mapped / max(1, len(cal))

    _print(f"✅ Rows: {len(cal):,}")
    _print(f"✅ Unique permnos: {cal['permno'].nunique():,}")
    _print(f"✅ Duplicate permno rows: {dupes:,}")
    _print(f"✅ Event-known coverage: {known_ratio:.1%}")
    _print(f"✅ Mapped-to-ticker coverage: {map_ratio:.1%}")
    _print(f"✅ Upcoming (<5d): {upcoming_5d:,}")
    _print(f"✅ Fresh catalysts (last 7d): {fresh_7d:,}")
    _print(f"✅ Stale fetch ratio (>14d): {stale_ratio:.1%}")

    failures: list[str] = []
    if dupes > 0:
        failures.append("duplicate permno rows found")
    if known_ratio < 0.50:
        failures.append("event-known coverage below 50%")
    if map_ratio < 0.95:
        failures.append("permno mapping coverage below 95%")

    if failures:
        _print("\n❌ CALENDAR LAYER: FAILED")
        for msg in failures:
            _print(f" - {msg}")
        return 1

    _print("\n✅ CALENDAR LAYER: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
