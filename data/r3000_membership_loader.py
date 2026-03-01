"""
Russell 3000 PIT Membership Loader

Builds forward-testing universe artifacts from WRDS index constituent history:
  1) r3000_membership.parquet
  2) universe_r3000_daily.parquet
  3) r3000_unmatched.csv

Input gate (institutional safety):
  - Required columns: gvkey, from, thru
  - Minimum usable rows (default 1000) with non-null gvkey
  - Reject metadata-only exports
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "data", "t1nd1jyzkjc3hsmq.csv")
MEMBERSHIP_PATH = os.path.join(PROCESSED_DIR, "r3000_membership.parquet")
UNIVERSE_DAILY_PATH = os.path.join(PROCESSED_DIR, "universe_r3000_daily.parquet")
UNMATCHED_PATH = os.path.join(PROCESSED_DIR, "r3000_unmatched.csv")
RUN_AUDIT_PATH = os.path.join(PROCESSED_DIR, "r3000_loader_run_audit.json")

REQUIRED_COLUMNS = {"gvkey", "from", "thru"}


def _log(msg: str):
    print(msg)


def _candidate_ticker_forms(raw_ticker: str) -> list[tuple[str, str]]:
    s = str(raw_ticker).upper().strip()
    if not s:
        return []

    candidates: list[tuple[str, str]] = [(s, "exact")]
    no_numeric_suffix = re.sub(r"\.[0-9]+$", "", s)  # e.g. BRK.B.1 -> BRK.B
    if no_numeric_suffix and no_numeric_suffix != s:
        candidates.append((no_numeric_suffix, "drop_numeric_suffix"))
    no_trailing_dot = re.sub(r"\.$", "", s)  # e.g. IDAI. -> IDAI
    if no_trailing_dot and no_trailing_dot != s:
        candidates.append((no_trailing_dot, "drop_trailing_dot"))
    dot_to_dash = s.replace(".", "-")  # e.g. BRK.B -> BRK-B
    if dot_to_dash != s:
        candidates.append((dot_to_dash, "dot_to_dash"))

    out: list[tuple[str, str]] = []
    seen = set()
    for val, rule in candidates:
        if val and val not in seen:
            out.append((val, rule))
            seen.add(val)
    return out


def _input_gate(raw: pd.DataFrame, min_rows: int) -> tuple[bool, str]:
    cols = {str(c).strip().lower() for c in raw.columns}
    missing = sorted(REQUIRED_COLUMNS - cols)
    if missing:
        return False, f"missing required columns: {missing}"

    # Normalize access by lower names.
    df = raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    usable = df[df["gvkey"].notna()].copy()
    usable = usable[usable["gvkey"].astype(str).str.strip() != ""]

    if len(usable) < min_rows:
        return (
            False,
            (
                f"insufficient constituent rows ({len(usable)}). "
                "Likely metadata-only export; re-download WRDS index constituents history."
            ),
        )
    return True, ""


def _load_and_normalize_membership(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, low_memory=False)
    raw.columns = [str(c).strip().lower() for c in raw.columns]

    keep_cols = ["gvkey", "from", "thru", "tic", "cusip", "conm", "conm_cst"]
    for c in keep_cols:
        if c not in raw.columns:
            raw[c] = np.nan
    df = raw[keep_cols].copy()

    df["gvkey"] = df["gvkey"].astype(str).str.strip()
    df = df[df["gvkey"].ne("") & df["gvkey"].ne("nan")]

    df["from_date"] = pd.to_datetime(df["from"], errors="coerce")
    df["thru_date"] = pd.to_datetime(df["thru"], errors="coerce")
    df["ticker_raw"] = df["tic"].astype(str).str.upper().str.strip()
    df["cusip"] = df["cusip"].astype(str).str.upper().str.strip()

    # Normalize empty strings to NA.
    for c in ["ticker_raw", "cusip"]:
        df.loc[df[c].isin(["", "NAN", "NONE"]), c] = pd.NA

    # Basic date hygiene.
    # If thru < from, drop thru (treat as open-ended bad source row).
    bad_window = df["from_date"].notna() & df["thru_date"].notna() & (df["thru_date"] < df["from_date"])
    df.loc[bad_window, "thru_date"] = pd.NaT

    # Keep latest duplicate if fully duplicated key.
    df = df.drop_duplicates(subset=["gvkey", "from_date", "thru_date", "ticker_raw"], keep="last")
    return df.reset_index(drop=True)


def _load_ticker_permno_map() -> pd.DataFrame:
    if not os.path.exists(TICKERS_PATH):
        raise FileNotFoundError(f"missing ticker map: {TICKERS_PATH}")
    tmap = pd.read_parquet(TICKERS_PATH)
    tmap["ticker"] = tmap["ticker"].astype(str).str.upper().str.strip()
    tmap["permno"] = pd.to_numeric(tmap["permno"], errors="coerce").astype("Int64")
    tmap = tmap.dropna(subset=["permno", "ticker"])
    tmap["permno"] = tmap["permno"].astype(np.uint32)
    tmap = tmap.drop_duplicates(subset=["ticker"], keep="last")
    return tmap[["ticker", "permno"]].reset_index(drop=True)


def _map_membership_to_permno(df: pd.DataFrame, tmap: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    lookup = dict(zip(tmap["ticker"], tmap["permno"]))
    rows = []
    for row in df.itertuples(index=False):
        raw_ticker = row.ticker_raw
        permno = None
        match_rule = None
        norm_ticker = None

        if pd.notna(raw_ticker):
            for cand, rule in _candidate_ticker_forms(raw_ticker):
                p = lookup.get(cand)
                if p is not None:
                    permno = np.uint32(p)
                    match_rule = rule
                    norm_ticker = cand
                    break

        rows.append(
            {
                "gvkey": row.gvkey,
                "from_date": row.from_date,
                "thru_date": row.thru_date,
                "ticker_raw": raw_ticker,
                "ticker": norm_ticker,
                "permno": permno,
                "cusip": row.cusip,
                "match_rule": match_rule,
            }
        )

    mapped = pd.DataFrame(rows)
    matched = mapped[mapped["permno"].notna()].copy()
    unmatched = mapped[mapped["permno"].isna()].copy()
    return matched.reset_index(drop=True), unmatched.reset_index(drop=True)


def _build_daily_universe(membership: pd.DataFrame) -> pd.DataFrame:
    if membership.empty:
        return pd.DataFrame(columns=["date", "permno", "ticker", "gvkey"])

    con = duckdb.connect()
    try:
        # Date spine from tradable price dates.
        if os.path.exists(PATCH_PATH):
            date_src = f"""(
                SELECT CAST(date AS DATE) AS date FROM '{PRICES_PATH}'
                UNION ALL
                SELECT CAST(date AS DATE) AS date FROM '{PATCH_PATH}'
            )"""
        else:
            date_src = f"(SELECT CAST(date AS DATE) AS date FROM '{PRICES_PATH}')"

        con.register("membership", membership)

        q = f"""
            WITH dates AS (
                SELECT DISTINCT date
                FROM {date_src}
                WHERE date >= DATE '2000-01-01'
            ),
            m AS (
                SELECT
                    CAST(permno AS UBIGINT) AS permno,
                    ticker,
                    gvkey,
                    CAST(from_date AS DATE) AS from_date,
                    CAST(thru_date AS DATE) AS thru_date
                FROM membership
            )
            SELECT
                d.date,
                m.permno,
                m.ticker,
                m.gvkey
            FROM dates d
            JOIN m
              ON d.date >= COALESCE(m.from_date, DATE '1900-01-01')
             AND d.date <= COALESCE(m.thru_date, DATE '2999-12-31')
        """
        out = con.execute(q).df()
    finally:
        con.close()

    if out.empty:
        return out
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["date", "permno"])
    out["permno"] = out["permno"].astype(np.uint32)
    out = out.drop_duplicates(subset=["date", "permno"], keep="last")
    return out.sort_values(["date", "permno"]).reset_index(drop=True)


def run_loader(csv_path: str, min_rows: int = 1000) -> dict:
    status = {
        "success": False,
        "csv_path": csv_path,
        "rows_input": 0,
        "rows_membership": 0,
        "rows_matched": 0,
        "rows_unmatched": 0,
        "mapped_permnos": 0,
        "daily_rows": 0,
        "daily_dates": 0,
        "coverage_vs_top3000": None,
        "error": None,
    }

    _log("=" * 72)
    _log("R3000 PIT Membership Loader")
    _log("=" * 72)
    _log(f"Input CSV: {csv_path}")

    if not os.path.exists(csv_path):
        status["error"] = "input file not found"
        _log(f"✗ {status['error']}")
        return status

    raw = pd.read_csv(csv_path, low_memory=False)
    status["rows_input"] = int(len(raw))
    ok, reason = _input_gate(raw, min_rows=min_rows)
    if not ok:
        status["error"] = reason
        _log(f"✗ Input gate failed: {reason}")
        _log("  Expected WRDS constituent history export (thousands of rows).")
        return status

    membership = _load_and_normalize_membership(csv_path)
    status["rows_membership"] = int(len(membership))
    _log(f"✓ Normalized membership rows: {status['rows_membership']:,}")

    tmap = _load_ticker_permno_map()
    matched, unmatched = _map_membership_to_permno(membership, tmap)
    status["rows_matched"] = int(len(matched))
    status["rows_unmatched"] = int(len(unmatched))
    status["mapped_permnos"] = int(matched["permno"].nunique()) if not matched.empty else 0
    _log(
        f"✓ Mapped rows: {status['rows_matched']:,} | "
        f"Unmatched rows: {status['rows_unmatched']:,} | "
        f"Unique permnos: {status['mapped_permnos']:,}"
    )

    # Save membership and unmatched audit.
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    run_ts = pd.Timestamp.utcnow().tz_localize(None)
    matched["source_file"] = os.path.basename(csv_path)
    matched["loaded_at"] = run_ts
    updater.atomic_parquet_write(matched, MEMBERSHIP_PATH, index=False)
    unmatched["source_file"] = os.path.basename(csv_path)
    unmatched["loaded_at"] = run_ts
    unmatched.to_csv(UNMATCHED_PATH, index=False)
    _log(f"✓ Wrote membership: {MEMBERSHIP_PATH}")
    _log(f"✓ Wrote unmatched audit: {UNMATCHED_PATH}")

    daily = _build_daily_universe(matched)
    status["daily_rows"] = int(len(daily))
    status["daily_dates"] = int(daily["date"].nunique()) if not daily.empty else 0
    updater.atomic_parquet_write(daily, UNIVERSE_DAILY_PATH, index=False)
    _log(f"✓ Wrote PIT daily universe: {UNIVERSE_DAILY_PATH} ({status['daily_rows']:,} rows)")

    # Coverage metric vs current Top 3000 liquid universe.
    top3k = {str(t).upper().strip() for t in updater.get_top_liquid_tickers(3000)}
    mapped_tickers = set(matched["ticker"].dropna().astype(str).str.upper().str.strip())
    cov = len(mapped_tickers.intersection(top3k)) / 3000.0
    status["coverage_vs_top3000"] = float(cov)
    _log(f"✓ Coverage vs Top3000 tickers: {cov:.2%}")

    status["success"] = True
    _log("✓ Loader complete.")
    _log("=" * 72)

    # Lightweight audit JSON for CI/ops visibility.
    try:
        import json

        payload = status.copy()
        payload["generated_at"] = dt.datetime.now(dt.UTC).isoformat()
        with open(RUN_AUDIT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass

    return status


def main():
    parser = argparse.ArgumentParser(description="Load Russell 3000 PIT membership history")
    parser.add_argument("--csv-path", default=DEFAULT_INPUT, help="WRDS constituent history CSV path")
    parser.add_argument("--min-rows", type=int, default=1000, help="Input gate minimum usable rows")
    args = parser.parse_args()

    result = run_loader(csv_path=args.csv_path, min_rows=args.min_rows)
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

