"""
ingest_ff_factors.py — Phase 23 Pillar 3b
==========================================
Pulls Fama-French 5-Factor + Momentum daily returns from WRDS
(ff.fivefactors_daily) and writes data/processed/ff_factors.parquet.

Factors confirmed accessible under WRDS entitlement:
  mktrf  Market excess return
  smb    Small minus Big        (size premium)
  hml    High minus Low         (value premium)
  rmw    Robust minus Weak      (profitability premium)
  cma    Conservative vs Aggr.  (investment premium)
  umd    Up minus Down          (momentum)
  rf     Risk-free rate

Derived features
-----------------
  cum_mkt_63d    63-day cumulative mktrf (trend in market return)
  cum_umd_63d    63-day cumulative momentum (momentum regime)
  hml_smb_ratio  hml / smb (value vs size leadership)

Usage
-----
  python scripts/ingest_ff_factors.py
  python scripts/ingest_ff_factors.py --start-date 2015-01-01
  python scripts/ingest_ff_factors.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
from core.security_policy import assert_egress_host_allowed
from core.security_policy import get_required_env

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger("ingest_ff_factors")

# ── Constants ─────────────────────────────────────────────────────────────────
WRDS_HOST   = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT   = 9737
WRDS_DBNAME = "wrds"
WRDS_USER_ENV = "WRDS_USER"
WRDS_PASS_ENV = "WRDS_PASS"

OUT_PATH = Path("data/processed/ff_factors.parquet")

DEFAULT_START = "2010-01-01"

# All 8 columns confirmed present in live probe
FF_COLS = ["date", "mktrf", "smb", "hml", "rmw", "cma", "rf", "umd"]


# ── DB Connection ─────────────────────────────────────────────────────────────

def _connect() -> psycopg2.extensions.connection:
    assert_egress_host_allowed(WRDS_HOST, context="ingest_ff_factors_wrds")
    wrds_user = get_required_env(WRDS_USER_ENV)
    wrds_pass = get_required_env(WRDS_PASS_ENV)
    LOG.info("Connecting to WRDS at %s:%s …", WRDS_HOST, WRDS_PORT)
    conn = psycopg2.connect(
        host=WRDS_HOST, port=WRDS_PORT, dbname=WRDS_DBNAME,
        user=wrds_user, password=wrds_pass,
        sslmode="require", connect_timeout=30,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    LOG.info("Connected.")
    return conn


# ── Query ─────────────────────────────────────────────────────────────────────

def _query_factors(
    conn: psycopg2.extensions.connection,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    cols_sql = ", ".join(FF_COLS)
    sql = f"""
        SELECT {cols_sql}
        FROM ff.fivefactors_daily
        WHERE date BETWEEN %s AND %s
        ORDER BY date
    """
    LOG.info("Querying ff.fivefactors_daily … (start=%s end=%s)", start_date, end_date)
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql, [start_date, end_date])
        rows = cur.fetchall()
    elapsed = time.perf_counter() - t0
    df = pd.DataFrame([dict(r) for r in rows])
    LOG.info("  ff.fivefactors_daily → %d rows in %.1fs", len(df), elapsed)
    return df


# ── Feature Engineering ───────────────────────────────────────────────────────

def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Cast Decimal → float
    for c in FF_COLS[1:]:   # skip "date"
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 63-day (≈ 1 quarter) cumulative returns — rolling trend signals
    df["cum_mkt_63d"]  = df["mktrf"].rolling(63, min_periods=21).sum()
    df["cum_umd_63d"]  = df["umd"].rolling(63, min_periods=21).sum()

    # Value vs size leadership ratio
    # Guard: avoid div by zero when smb ≈ 0
    df["hml_smb_ratio"] = np.where(
        df["smb"].abs() > 1e-6,
        df["hml"] / df["smb"],
        np.nan,
    )

    # Profitability momentum: 21-day centred rmw trend
    df["rmw_21d_mean"] = df["rmw"].rolling(21, min_periods=10).mean()

    return df


def _build_final_df(df: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "date",
        "mktrf", "smb", "hml", "rmw", "cma", "umd", "rf",
        "cum_mkt_63d", "cum_umd_63d",
        "hml_smb_ratio", "rmw_21d_mean",
    ]
    keep = [c for c in keep if c in df.columns]
    return df[keep].reset_index(drop=True)


def _atomic_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp.parquet")
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
        LOG.info("Written → %s  (%d rows, %d cols)", path, len(df), df.shape[1])
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest FF 5-Factor + Momentum (Pillar 3b)")
    parser.add_argument("--start-date", default=DEFAULT_START)
    parser.add_argument("--end-date",   default=pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run",    action="store_true")
    parser.add_argument("--log-level",  default="INFO",
                        choices=["DEBUG", "INFO", "WARNING"])
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    conn = _connect()
    try:
        df = _query_factors(conn, args.start_date, args.end_date)
        if df.empty:
            LOG.error("No rows returned from ff.fivefactors_daily. Aborting.")
            sys.exit(1)

        df  = _engineer_features(df)
        out = _build_final_df(df)

        LOG.info("Output shape: %d rows × %d cols", *out.shape)
        LOG.info("Date range: %s → %s",
                 out["date"].min().date(), out["date"].max().date())
        LOG.info("Null pct — rmw: %.1f%%  cma: %.1f%%",
                 out["rmw"].isna().mean() * 100,
                 out["cma"].isna().mean() * 100)

        if args.dry_run:
            preview = ["date", "mktrf", "smb", "hml", "rmw", "cma", "umd",
                       "cum_mkt_63d", "cum_umd_63d", "hml_smb_ratio"]
            preview = [c for c in preview if c in out.columns]
            print(out[preview].tail(10).to_string(index=False))
            LOG.info("DRY-RUN complete. Row count: %d", len(out))
            return

        _atomic_write(out, OUT_PATH)

    finally:
        conn.close()
        LOG.info("WRDS connection closed.")


if __name__ == "__main__":
    main()
