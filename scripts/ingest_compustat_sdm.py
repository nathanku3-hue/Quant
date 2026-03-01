"""
ingest_compustat_sdm.py — Phase 23 Pillar 1 + 2
================================================
Pulls Compustat quarterly fundamentals (comp.fundq) and Peters & Taylor
Total Q (totalq.total_q) from WRDS via psycopg2, engineers 6 trajectory
features, and writes data/processed/fundamentals_sdm.parquet.

PIT FIREWALL: published_at is ALWAYS mapped from rdq (report date of
quarter).  datadate (fiscal period end) is NEVER used as a PIT anchor —
it is kept only for TTM window arithmetic.

Peters & Taylor note: totalq is annual.  We lag its datadate by 90 days
to simulate the 10-K filing disclosure delay before joining to our
quarterly PIT timeline.

Usage
-----
  python scripts/ingest_compustat_sdm.py                      # full universe
  python scripts/ingest_compustat_sdm.py --dry-run            # no write
  python scripts/ingest_compustat_sdm.py --start-date 2022-01-01 --end-date 2024-12-31

Features engineered
--------------------
  rev_accel      YoY change in TTM revenue growth   (2nd derivative)
  inv_vel_traj   YoY change in inventory velocity   (rev_ttm / invtq)
  gm_traj        YoY change in gross margin         (pp delta)
  op_lev         EBITDA growth minus revenue growth  (operating leverage)
  intang_intensity  k_int / (k_int + ppentq)        (Pillar 2)
  invest_disc    YoY % change in k_int              (intangible capex proxy)
  q_regime       1 if q_tot > 1 else 0              (over/under-investment)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
from core.security_policy import assert_egress_host_allowed
from core.security_policy import get_required_env

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger("ingest_compustat_sdm")

# ── Constants ─────────────────────────────────────────────────────────────────
WRDS_HOST   = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT   = 9737
WRDS_DBNAME = "wrds"
WRDS_USER_ENV = "WRDS_USER"
WRDS_PASS_ENV = "WRDS_PASS"

OUT_PATH = Path("data/processed/fundamentals_sdm.parquet")
UNMAPPED_AUDIT_PATH = Path("data/processed/fundamentals_sdm_unmapped_permno_audit.csv")

# Fiscal-period columns to pull from comp.fundq
FUNDQ_COLS = [
    "gvkey", "tic", "datadate", "rdq",
    "fyearq", "fqtr",
    "revtq",    # Revenue
    "cogsq",    # Cost of goods sold
    "oibdpq",   # Operating income before D&P  (EBITDA proxy)
    "capsq",    # CapEx (physical)
    "ppentq",   # PP&E net  ← physical capital proxy for intang_intensity
    "invtq",    # Inventory
    "dpq",      # Depreciation & Amortisation
    "atq",      # Total assets
    "niq",      # Net income
    "xsgaq",    # SG&A
]

# Peters & Taylor columns from totalq.total_q
TOTALQ_REQUIRED_COLS = ["gvkey", "datadate"]
TOTALQ_STABLE_COLS = ["k_int", "k_int_know", "k_int_org", "q_tot"]
TOTALQ_OPTIONAL_COLS = ["k_phy", "invest_int", "invest_phy", "ik_tot"]

# 90-day filing lag applied to totalq.datadate before PIT join
TOTALQ_LAG_DAYS = 90

DEFAULT_START = "2015-01-01"


# ── DB Connection ─────────────────────────────────────────────────────────────

def _connect() -> psycopg2.extensions.connection:
    assert_egress_host_allowed(WRDS_HOST, context="ingest_compustat_sdm_wrds")
    wrds_user = get_required_env(WRDS_USER_ENV)
    wrds_pass = get_required_env(WRDS_PASS_ENV)
    LOG.info("Connecting to WRDS PostgreSQL at %s:%s …", WRDS_HOST, WRDS_PORT)
    conn = psycopg2.connect(
        host=WRDS_HOST, port=WRDS_PORT, dbname=WRDS_DBNAME,
        user=wrds_user, password=wrds_pass,
        sslmode="require", connect_timeout=30,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    LOG.info("Connected.")
    return conn


# ── Query helpers ─────────────────────────────────────────────────────────────

def _query_fundq(
    conn: psycopg2.extensions.connection,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Pull quarterly fundamentals from comp.fundq."""
    cols_sql = ", ".join(FUNDQ_COLS)
    params: list[Any] = [start_date, end_date]

    sql = f"""
        SELECT {cols_sql}
        FROM comp.fundq
        WHERE datafmt = 'STD'
          AND popsrc  = 'D'
          AND consol  = 'C'
          AND indfmt  = 'INDL'
          AND datadate BETWEEN %s AND %s
        ORDER BY gvkey, datadate
    """
    LOG.info("Querying comp.fundq … (start=%s end=%s universe=ALL)",
             start_date, end_date)
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    elapsed = time.perf_counter() - t0
    df = pd.DataFrame([dict(r) for r in rows])
    LOG.info("  fundq → %d rows in %.1fs", len(df), elapsed)
    # Cast Decimal → float for all numeric columns
    for c in df.columns:
        if c not in ("gvkey", "tic", "datadate", "rdq"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _select_totalq_columns(available_cols: set[str]) -> list[str]:
    """Build a stable + dynamic column list for totalq.total_q."""
    selected: list[str] = [c for c in TOTALQ_REQUIRED_COLS if c in available_cols]
    selected.extend(c for c in TOTALQ_STABLE_COLS if c in available_cols)
    selected.extend(c for c in TOTALQ_OPTIONAL_COLS if c in available_cols)
    # Keep order stable while removing duplicates.
    return list(dict.fromkeys(selected))


def _probe_totalq_columns(conn: psycopg2.extensions.connection) -> list[str]:
    """Probe available columns in totalq.total_q so ingestion degrades gracefully."""
    sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'totalq'
          AND table_name = 'total_q'
        ORDER BY ordinal_position
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    cols = [str(r["column_name"]).lower() for r in rows]
    if not cols:
        raise RuntimeError("Unable to probe totalq.total_q columns (empty schema result).")
    LOG.info("Probed totalq.total_q columns: %s", cols)
    return cols


def _query_totalq(
    conn: psycopg2.extensions.connection,
    gvkeys: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Pull annual Peters & Taylor intangible capital."""
    if not gvkeys:
        cols = TOTALQ_REQUIRED_COLS + TOTALQ_STABLE_COLS + TOTALQ_OPTIONAL_COLS
        return pd.DataFrame(columns=cols)

    available_cols = set(_probe_totalq_columns(conn))
    selected_cols = _select_totalq_columns(available_cols)
    missing_required = [c for c in TOTALQ_REQUIRED_COLS if c not in selected_cols]
    if missing_required:
        raise RuntimeError(f"totalq.total_q missing required columns: {missing_required}")
    missing_stable = [c for c in TOTALQ_STABLE_COLS if c not in selected_cols]
    if missing_stable:
        LOG.warning("totalq.total_q missing stable optional columns: %s", missing_stable)
    present_optional = [c for c in TOTALQ_OPTIONAL_COLS if c in selected_cols]
    if present_optional:
        LOG.info("totalq.total_q enrichment columns enabled: %s", present_optional)

    cols_sql = ", ".join(selected_cols)
    placeholders = ", ".join(["%s"] * len(gvkeys))
    sql = f"""
        SELECT {cols_sql}
        FROM totalq.total_q
        WHERE gvkey IN ({placeholders})
          AND datadate BETWEEN %s AND %s
        ORDER BY gvkey, datadate
    """
    params = gvkeys + [start_date, end_date]
    LOG.info("Querying totalq.total_q … (%d gvkeys)", len(gvkeys))
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    elapsed = time.perf_counter() - t0
    df = pd.DataFrame([dict(r) for r in rows])
    LOG.info("  totalq → %d rows in %.1fs", len(df), elapsed)
    # Cast Decimal → float
    for c in df.columns:
        if c not in ("gvkey", "datadate"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ── PIT Validation ────────────────────────────────────────────────────────────

def _validate_pit(df: pd.DataFrame) -> pd.DataFrame:
    """Drop invalid PIT rows and return a strictly PIT-safe frame."""
    # Strip tz from published_at (UTC-aware) for comparison with tz-naive fiscal_date.
    pub_naive  = pd.to_datetime(df["published_at"], utc=True).dt.tz_convert(None)
    fisc_naive = pd.to_datetime(df["fiscal_date"])
    null_pit_mask = df["published_at"].isna()
    early_mask = pub_naive <= fisc_naive
    bad_mask = null_pit_mask | early_mask
    bad = df[bad_mask]
    if not bad.empty:
        sample = bad[["ticker", "fiscal_date", "published_at"]].head(5).to_string(index=False)
        LOG.warning(
            "PIT firewall dropped %d rows with invalid anchors (null or published_at <= fiscal_date).\n%s",
            len(bad),
            sample,
        )
    out = df[~bad_mask].copy()
    if out.empty:
        raise ValueError("PIT FIREWALL VIOLATION: all rows invalid after PIT filtering.")
    LOG.info(
        "PIT validation passed — retained %d rows, dropped %d invalid PIT rows.",
        len(out),
        len(bad),
    )
    return out


# ── Feature Engineering ───────────────────────────────────────────────────────

def _accumulate_ttm(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling 4-quarter TTM sum per gvkey, ordered by datadate."""
    df = df.sort_values(["gvkey", "datadate"]).copy()
    g = df.groupby("gvkey")
    for col in ("revtq", "cogsq", "oibdpq", "capsq", "dpq", "niq"):
        ttm_col = col.replace("q", "_ttm").replace("tq", "_ttm")
        # standardise naming
        ttm_col = f"{col.rstrip('q')}_ttm" if col.endswith("q") else f"{col}_ttm"
        df[ttm_col] = g[col].transform(lambda s: s.rolling(4, min_periods=4).sum())

    # point-in-time inventory (no TTM — use quarter-end value directly)
    # invtq and ppentq kept as-is
    return df


def _compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """YoY trajectory features. lag4 = same quarter prior year."""
    df = df.sort_values(["gvkey", "datadate"]).copy()
    g  = df.groupby("gvkey")

    # Gross margin (TTM)
    df["gross_margin"] = (
        (df["rev_ttm"] - df["cogsq_ttm"]) / df["rev_ttm"]
    ).where(df["rev_ttm"] > 0)

    # YoY revenue growth (lag4 = 4 quarters)
    df["rev_lag4"]    = g["rev_ttm"].transform(lambda s: s.shift(4))
    df["rev_growth"]  = (df["rev_ttm"] / df["rev_lag4"] - 1).where(df["rev_lag4"] > 0)

    # Revenue acceleration (2nd derivative)
    df["rev_growth_lag4"] = g["rev_growth"].transform(lambda s: s.shift(4))
    df["rev_accel"]       = df["rev_growth"] - df["rev_growth_lag4"]

    # Inventory velocity
    df["inv_vel"]      = (df["rev_ttm"] / df["invtq"]).where(df["invtq"] > 0)
    df["inv_vel_lag4"] = g["inv_vel"].transform(lambda s: s.shift(4))
    df["inv_vel_traj"] = (df["inv_vel"] / df["inv_vel_lag4"] - 1).where(df["inv_vel_lag4"] > 0)

    # Gross margin trajectory (pp delta YoY)
    df["gm_lag4"] = g["gross_margin"].transform(lambda s: s.shift(4))
    df["gm_traj"] = df["gross_margin"] - df["gm_lag4"]

    # Operating leverage = EBITDA growth minus revenue growth
    df["ebitda_lag4"]    = g["ebitda_ttm"].transform(lambda s: s.shift(4))
    df["ebitda_growth"]  = (df["ebitda_ttm"] / df["ebitda_lag4"] - 1).where(df["ebitda_lag4"] > 0)
    df["op_lev"]         = df["ebitda_growth"] - df["rev_growth"]

    return df


def _assert_merge_asof_sorted(df: pd.DataFrame, key_col: str, side: str) -> None:
    """Guardrail for merge_asof: key must be globally monotonic and non-null."""
    key = pd.to_datetime(df[key_col], errors="coerce")
    if key.isna().any():
        raise ValueError(f"{side} merge_asof key {key_col} contains null/invalid timestamps.")
    if not key.is_monotonic_increasing:
        sample = df[[key_col]].head(5).to_string(index=False)
        raise ValueError(
            f"{side} keys must be globally sorted by {key_col} for merge_asof.\n{sample}"
        )


def _join_totalq(df_fundq: pd.DataFrame, df_tq: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join Peters & Taylor (annual) into quarterly fundq rows.

    Lag: totalq.datadate + 90 days = PIT-safe disclosure date.
    Join strategy: merge_asof on published_at (forward-filled annual value
    into each quarterly row — each quarter gets the most recent annual
    Peters & Taylor observation that was already public).
    """
    if df_tq.empty:
        LOG.warning("Peters & Taylor DataFrame is empty — skipping Pillar 2 join.")
        for col in TOTALQ_STABLE_COLS + TOTALQ_OPTIONAL_COLS:
            if col not in df_fundq.columns:
                df_fundq[col] = np.nan
        if "invest_disc" not in df_fundq.columns:
            df_fundq["invest_disc"] = np.nan
        if "intang_intensity" not in df_fundq.columns:
            df_fundq["intang_intensity"] = np.nan
        if "q_regime" not in df_fundq.columns:
            df_fundq["q_regime"] = np.nan
        return df_fundq

    df_tq = df_tq.copy()
    df_tq["datadate"] = pd.to_datetime(df_tq["datadate"])
    # Apply 90-day filing lag
    df_tq["pit_date"] = df_tq["datadate"] + pd.Timedelta(days=TOTALQ_LAG_DAYS)
    df_tq = df_tq.sort_values(["pit_date", "gvkey"]).reset_index(drop=True)
    _assert_merge_asof_sorted(df_tq, "pit_date", side="right")

    df_fundq = df_fundq.copy()
    # Strip tz from published_at for merge_asof (tz_convert handles tz-aware series)
    raw_pit = pd.to_datetime(df_fundq["published_at"], utc=True)
    if raw_pit.dt.tz is not None:
        df_fundq["published_at_dt"] = raw_pit.dt.tz_convert(None)
    else:
        df_fundq["published_at_dt"] = raw_pit
    # merge_asof requires BOTH sides sorted by the timeline key first.
    df_fundq = df_fundq.sort_values(["published_at_dt", "gvkey"]).reset_index(drop=True)
    _assert_merge_asof_sorted(df_fundq, "published_at_dt", side="left")

    tq_cols = ["gvkey", "pit_date"] + [
        c for c in TOTALQ_STABLE_COLS + TOTALQ_OPTIONAL_COLS if c in df_tq.columns
    ]
    merged = pd.merge_asof(
        df_fundq,
        df_tq[tq_cols],
        left_on="published_at_dt",
        right_on="pit_date",
        by="gvkey",
        direction="backward",   # use most recent lagged annual value
    )

    for col in TOTALQ_STABLE_COLS + TOTALQ_OPTIONAL_COLS:
        if col not in merged.columns:
            merged[col] = np.nan

    # Intangible intensity: k_int / (k_int + ppentq)
    denom = merged["k_int"] + merged["ppentq"]
    merged["intang_intensity"] = (merged["k_int"] / denom).where(denom > 0)

    # Investment discipline:
    # Prefer ik_tot YoY delta when available, else fallback to YoY k_int growth.
    merged = merged.sort_values(["gvkey", "published_at_dt"])
    g = merged.groupby("gvkey")
    if "ik_tot" in merged.columns and merged["ik_tot"].notna().any():
        merged["ik_tot_lag4"] = g["ik_tot"].transform(lambda s: s.shift(4))
        merged["invest_disc"] = merged["ik_tot"] - merged["ik_tot_lag4"]
    else:
        merged["k_int_lag4"] = g["k_int"].transform(lambda s: s.shift(4))
        merged["invest_disc"] = (
            (merged["k_int"] - merged["k_int_lag4"]) / merged["k_int_lag4"]
        ).where(merged["k_int_lag4"] > 0)

    # Capital cycle regime
    merged["q_regime"] = np.where(merged["q_tot"].notna(), (merged["q_tot"] > 1.0).astype(float), np.nan)

    merged = merged.drop(columns=["published_at_dt", "pit_date"], errors="ignore")
    n_joined = merged["k_int"].notna().sum()
    LOG.info("Peters & Taylor joined — %d/%d rows have k_int.", n_joined, len(merged))
    return merged


def _build_final_df(df: pd.DataFrame) -> pd.DataFrame:
    """Select and type-cast output columns."""
    keep = [
        "permno", "gvkey", "ticker", "published_at", "fiscal_date",
        "fyearq", "fqtr",
        # raw TTM
        "rev_ttm", "ebitda_ttm", "capsq_ttm", "depr_ttm",
        "invtq", "ppentq", "atq",
        # trajectory features
        "gross_margin", "rev_growth", "rev_accel",
        "inv_vel", "inv_vel_traj",
        "gm_traj", "ebitda_growth", "op_lev",
        # Pillar 2
        "k_int", "k_int_know", "k_int_org", "q_tot",
        "k_phy", "invest_int", "invest_phy", "ik_tot",
        "intang_intensity", "invest_disc", "q_regime",
    ]
    # Only keep columns that exist
    keep = [c for c in keep if c in df.columns]
    out = df[keep].copy()
    out["fyearq"] = out["fyearq"].astype("Int64")
    out["fqtr"]   = out["fqtr"].astype("Int8")
    return out.sort_values(["gvkey", "published_at"]).reset_index(drop=True)


def _atomic_write(df: pd.DataFrame, path: Path) -> None:
    """Write parquet atomically via temp file."""
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


def _atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write CSV atomically via temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp.csv")
    try:
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
        LOG.info("Written audit → %s  (%d rows)", path, len(df))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _crosswalk_permno(
    df: pd.DataFrame,
    sm_path: Path = Path("data/static/sector_map.parquet"),
    audit_path: Path = UNMAPPED_AUDIT_PATH,
    write_audit: bool = True,
) -> pd.DataFrame:
    """Map ticker → permno via sector_map.parquet (allow+audit policy)."""
    out = df.copy()
    out["ticker"] = out["ticker"].astype(str).str.upper()

    if not sm_path.exists():
        LOG.warning("sector_map.parquet not found — permno will be NaN for all rows.")
        out["permno"] = pd.NA
        if write_audit:
            audit = out[["gvkey", "ticker", "fiscal_date", "published_at"]].copy()
            audit["reason"] = "sector_map_missing"
            _atomic_write_csv(audit, audit_path)
        else:
            LOG.info("DRY-RUN: skipped unmapped permno audit write (%s).", audit_path)
        return out

    sm = pd.read_parquet(sm_path, columns=["ticker", "permno"])
    sm["ticker"] = sm["ticker"].astype(str).str.upper()
    sm = sm.drop_duplicates("ticker")
    out = out.merge(sm, on="ticker", how="left")

    n_mapped = out["permno"].notna().sum()
    LOG.info("permno crosswalk: %d/%d rows mapped.", n_mapped, len(out))

    unmapped = out[out["permno"].isna()][["gvkey", "ticker", "fiscal_date", "published_at"]].copy()
    if not unmapped.empty:
        unmapped = unmapped.drop_duplicates().sort_values(["ticker", "published_at"])
        unmapped["reason"] = "ticker_not_found_in_sector_map"
        if write_audit:
            _atomic_write_csv(unmapped, audit_path)
        else:
            LOG.info("DRY-RUN: skipped unmapped permno audit write (%s).", audit_path)
        LOG.warning(
            "Unmapped permno rows retained (allow+audit): %d rows, %d tickers.",
            len(unmapped),
            unmapped["ticker"].nunique(),
        )
    else:
        if write_audit:
            _atomic_write_csv(
                pd.DataFrame(columns=["gvkey", "ticker", "fiscal_date", "published_at", "reason"]),
                audit_path,
            )
        else:
            LOG.info("DRY-RUN: skipped empty audit write (%s).", audit_path)
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Compustat SDM (Pillar 1+2)")
    parser.add_argument("--start-date", default=DEFAULT_START)
    parser.add_argument("--end-date",   default=pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run",    action="store_true",
                        help="Fetch and compute but do not write parquet.")
    parser.add_argument("--log-level",  default="INFO",
                        choices=["DEBUG", "INFO", "WARNING"])
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    conn = _connect()
    try:
        # ── Pillar 1: comp.fundq ──────────────────────────────────────────
        df_fq = _query_fundq(conn, args.start_date, args.end_date)
        if df_fq.empty:
            LOG.error("No rows returned from comp.fundq. Aborting.")
            sys.exit(1)

        df_fq["datadate"] = pd.to_datetime(df_fq["datadate"])
        df_fq["rdq"]      = pd.to_datetime(df_fq["rdq"])

        # Drop rows without a report date (rdq) — cannot anchor PIT
        n_before = len(df_fq)
        df_fq = df_fq[df_fq["rdq"].notna()].copy()
        LOG.info("Dropped %d rows with null rdq.", n_before - len(df_fq))

        df_fq["published_at"] = df_fq["rdq"].dt.tz_localize("UTC")
        df_fq["fiscal_date"]  = df_fq["datadate"]
        df_fq = df_fq.rename(columns={"tic": "ticker"})
        df_fq["ticker"] = df_fq["ticker"].str.upper()

        # TTM accumulation
        df_fq = _accumulate_ttm(df_fq)
        # Recompute cleanly with explicit names
        def rolling4(s): return s.rolling(4, min_periods=4).sum()
        grp = df_fq.groupby("gvkey")
        df_fq["rev_ttm"]    = grp["revtq"].transform(rolling4)
        df_fq["cogsq_ttm"]  = grp["cogsq"].transform(rolling4)
        df_fq["ebitda_ttm"] = grp["oibdpq"].transform(rolling4)
        df_fq["capsq_ttm"]  = grp["capsq"].transform(rolling4)
        df_fq["depr_ttm"]   = grp["dpq"].transform(rolling4)

        df_fq = _compute_features(df_fq)

        # ── PIT validation ────────────────────────────────────────────────
        df_fq = _validate_pit(df_fq)

        # ── Pillar 2: totalq.total_q ──────────────────────────────────────
        gvkeys = df_fq["gvkey"].dropna().unique().tolist()
        df_tq  = _query_totalq(conn, gvkeys, args.start_date, args.end_date)
        df_fq  = _join_totalq(df_fq, df_tq)

        # ── Crosswalk permno ──────────────────────────────────────────────
        df_fq = _crosswalk_permno(df_fq, write_audit=not args.dry_run)

        # ── Build final output ────────────────────────────────────────────
        out = _build_final_df(df_fq)

        LOG.info("Output shape: %d rows × %d cols", *out.shape)
        LOG.info("Columns: %s", list(out.columns))
        LOG.info("Date range: %s → %s",
                 out["published_at"].min(), out["published_at"].max())

        # ── Dry-run preview ───────────────────────────────────────────────
        if args.dry_run:
            LOG.info("DRY-RUN — showing sample (no write):")
            preview_cols = ["ticker", "fiscal_date", "published_at", "fyearq", "fqtr",
                            "rev_ttm", "rev_growth", "rev_accel",
                            "gm_traj", "op_lev", "q_tot", "intang_intensity"]
            preview_cols = [c for c in preview_cols if c in out.columns]
            print(out[preview_cols].tail(20).to_string(index=False))
            LOG.info("DRY-RUN complete. Row count: %d", len(out))
            return

        # ── Write ─────────────────────────────────────────────────────────
        _atomic_write(out, OUT_PATH)

    finally:
        conn.close()
        LOG.info("WRDS connection closed.")


if __name__ == "__main__":
    main()

