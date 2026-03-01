"""
ingest_frb_macro.py — Phase 23 Pillar 3a
==========================================
Pulls Federal Reserve Board daily interest rate and credit spread data
from WRDS (frb.rates_daily) and writes data/processed/macro_rates.parquet.

This table is consumed by assemble_sdm_features.py, which merge_asof-joins
it onto the quarterly fundamentals_sdm panel using published_at as the key.
All macro data is public on the day it is published — no PIT lag required.

Key columns extracted
---------------------
  Yield curve:      dgs2, dgs10, t10y2y (pre-computed slope), t10y3m,
                    t10yie (10Y breakeven inflation), t5yie
  Credit spreads:   bamlh0a0hym2 (HY OAS), bamlc0a0cmey (IG OAS),
                    bamlh0a1hybbey (BB), bamlh0a3hycey (CCC),
                    daaa, dbaa (Moody's corporates), tedrate
  Policy rate:      dff (Fed Funds effective), sofr, dfedtaru/l (target range)

Derived features (computed locally)
-------------------------------------
  baa_aaa_spread   = dbaa - daaa          (Baa−Aaa corporate spread)
  real_yield_10y   = dgs10 - t10yie       (ex-ante real rate)
  curve_regime     = sign(t10y2y)         (+1 normal, −1 inverted, 0 flat)
  hy_ig_spread     = bamlh0a0hym2 - bamlc0a0cmey  (risk appetite gauge)

Usage
-----
  python scripts/ingest_frb_macro.py                         # full history
  python scripts/ingest_frb_macro.py --start-date 2015-01-01
  python scripts/ingest_frb_macro.py --dry-run
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
LOG = logging.getLogger("ingest_frb_macro")

# ── Constants ─────────────────────────────────────────────────────────────────
WRDS_HOST   = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT   = 9737
WRDS_DBNAME = "wrds"
WRDS_USER_ENV = "WRDS_USER"
WRDS_PASS_ENV = "WRDS_PASS"

OUT_PATH = Path("data/processed/macro_rates.parquet")

DEFAULT_START = "2010-01-01"

# Exact column names confirmed from live schema probe
FRB_COLS = [
    "date",
    # Treasuries
    "dgs2",          # 2Y CMT
    "dgs10",         # 10Y CMT
    "dgs3mo",        # 3M CMT
    "dgs1",          # 1Y CMT
    "dgs5",          # 5Y CMT
    "dgs30",         # 30Y CMT
    # Pre-computed spreads (direct from FRED/FRB)
    "t10y2y",        # 10Y minus 2Y slope  ← primary cycle signal
    "t10y3m",        # 10Y minus 3M slope
    "t10yie",        # 10Y inflation breakeven
    "t5yie",         # 5Y inflation breakeven
    # Credit spreads (BAML ICE indices)
    "bamlh0a0hym2",  # HY OAS spread  ← primary risk signal
    "bamlc0a0cmey",  # IG OAS EY
    "bamlh0a1hybbey",# BB-rated HY
    "bamlh0a3hycey", # CCC-rated HY
    # Corporate yields (Moody's)
    "daaa",          # Moody's Aaa
    "dbaa",          # Moody's Baa
    # Policy & systemic
    "dff",           # Fed Funds effective rate
    "sofr",          # SOFR
    "tedrate",       # TED spread (LIBOR minus T-bill)
    "dfedtaru",      # Fed Funds upper target
    "dfedtarl",      # Fed Funds lower target
]


# ── DB Connection ─────────────────────────────────────────────────────────────

def _connect() -> psycopg2.extensions.connection:
    assert_egress_host_allowed(WRDS_HOST, context="ingest_frb_macro_wrds")
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

def _query_rates(
    conn: psycopg2.extensions.connection,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    cols_sql = ", ".join(FRB_COLS)
    sql = f"""
        SELECT {cols_sql}
        FROM frb.rates_daily
        WHERE date BETWEEN %s AND %s
        ORDER BY date
    """
    LOG.info("Querying frb.rates_daily … (start=%s end=%s)", start_date, end_date)
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql, [start_date, end_date])
        rows = cur.fetchall()
    elapsed = time.perf_counter() - t0
    df = pd.DataFrame([dict(r) for r in rows])
    LOG.info("  frb.rates_daily → %d rows in %.1fs", len(df), elapsed)
    return df


# ── Feature Engineering ───────────────────────────────────────────────────────

def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived macro features from raw FRB columns."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Cast all numeric columns (they come as Decimal from psycopg2)
    num_cols = [c for c in df.columns if c != "date"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Derived features
    df["baa_aaa_spread"] = df["dbaa"]  - df["daaa"]          # corporate quality spread
    df["real_yield_10y"] = df["dgs10"] - df["t10yie"]        # ex-ante real 10Y rate
    df["hy_ig_spread"]   = df["bamlh0a0hym2"] - df["bamlc0a0cmey"]  # risk appetite

    # Curve regime: +1 normal, -1 inverted, 0 flat (|slope| < 5bp)
    df["curve_regime"] = np.sign(df["t10y2y"].fillna(0))

    # Forward-fill sparse columns (FRB data has weekends/holidays as NaN)
    # Use limit=5 to avoid filling across long gaps (e.g. discontinued series)
    df = df.sort_values("date")
    for c in num_cols + ["baa_aaa_spread", "real_yield_10y", "hy_ig_spread", "curve_regime"]:
        if c in df.columns:
            df[c] = df[c].ffill(limit=5)

    return df


def _build_final_df(df: pd.DataFrame) -> pd.DataFrame:
    """Select output columns, rename for clarity, sort."""
    rename = {
        "dgs2":          "yield_2y",
        "dgs10":         "yield_10y",
        "dgs3mo":        "yield_3m",
        "dgs1":          "yield_1y",
        "dgs5":          "yield_5y",
        "dgs30":         "yield_30y",
        "t10y2y":        "yield_slope_10y2y",
        "t10y3m":        "yield_slope_10y3m",
        "t10yie":        "inflation_breakeven_10y",
        "t5yie":         "inflation_breakeven_5y",
        "bamlh0a0hym2":  "credit_spread_hy",
        "bamlc0a0cmey":  "credit_spread_ig",
        "bamlh0a1hybbey":"credit_spread_bb",
        "bamlh0a3hycey": "credit_spread_ccc",
        "daaa":          "yield_aaa",
        "dbaa":          "yield_baa",
        "dff":           "fed_funds",
        "sofr":          "sofr",
        "tedrate":       "ted_spread",
        "dfedtaru":      "fed_target_upper",
        "dfedtarl":      "fed_target_lower",
    }
    df = df.rename(columns=rename)

    # Final column order
    keep = [
        "date",
        "yield_2y", "yield_10y", "yield_3m", "yield_1y", "yield_5y", "yield_30y",
        "yield_slope_10y2y", "yield_slope_10y3m",
        "inflation_breakeven_10y", "inflation_breakeven_5y",
        "real_yield_10y", "curve_regime",
        "credit_spread_hy", "credit_spread_ig",
        "credit_spread_bb", "credit_spread_ccc",
        "baa_aaa_spread", "hy_ig_spread",
        "yield_aaa", "yield_baa",
        "fed_funds", "sofr", "ted_spread",
        "fed_target_upper", "fed_target_lower",
    ]
    keep = [c for c in keep if c in df.columns]
    return df[keep].sort_values("date").reset_index(drop=True)


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
    parser = argparse.ArgumentParser(description="Ingest FRB macro rates (Pillar 3a)")
    parser.add_argument("--start-date", default=DEFAULT_START)
    parser.add_argument("--end-date",   default=pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run",    action="store_true")
    parser.add_argument("--log-level",  default="INFO",
                        choices=["DEBUG", "INFO", "WARNING"])
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    conn = _connect()
    try:
        df = _query_rates(conn, args.start_date, args.end_date)
        if df.empty:
            LOG.error("No rows returned from frb.rates_daily. Aborting.")
            sys.exit(1)

        df = _engineer_features(df)
        out = _build_final_df(df)

        LOG.info("Output shape: %d rows × %d cols", *out.shape)
        LOG.info("Date range: %s → %s", out["date"].min().date(), out["date"].max().date())
        LOG.info("Null pct — yield_slope_10y2y: %.1f%%  credit_spread_hy: %.1f%%",
                 out["yield_slope_10y2y"].isna().mean() * 100,
                 out["credit_spread_hy"].isna().mean() * 100)

        if args.dry_run:
            preview_cols = [
                "date", "yield_2y", "yield_10y", "yield_slope_10y2y",
                "credit_spread_hy", "real_yield_10y", "curve_regime",
                "baa_aaa_spread", "ted_spread", "fed_funds",
            ]
            preview_cols = [c for c in preview_cols if c in out.columns]
            print(out[preview_cols].tail(10).to_string(index=False))
            LOG.info("DRY-RUN complete. Row count: %d", len(out))
            return

        _atomic_write(out, OUT_PATH)

    finally:
        conn.close()
        LOG.info("WRDS connection closed.")


if __name__ == "__main__":
    main()
