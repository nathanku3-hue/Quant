"""
Data Layer Integrity Validation (Phase 8 sign-off gate)

Checks:
1) Zombie audit (survivorship/staleness pressure)
2) Alignment audit (prices/ticker universe vs fundamentals coverage)
3) PIT audit (release_date should not precede fiscal_period_end)

Exit code:
  0 -> PASS
  1 -> FAIL
"""

from __future__ import annotations

import os
import sys

import duckdb
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater

FUND_PATH = "data/processed/fundamentals.parquet"
SNAP_PATH = "data/processed/fundamentals_snapshot.parquet"
PRICES_PATH = "data/processed/prices.parquet"
PATCH_PATH = "data/processed/yahoo_patch.parquet"
TICKERS_PATH = "data/processed/tickers.parquet"
FEATURES_PATH = "data/processed/features.parquet"


def _safe_load():
    try:
        fund = pd.read_parquet(FUND_PATH)
        snap = pd.read_parquet(SNAP_PATH)
        prices = pd.read_parquet(PRICES_PATH, columns=["permno", "date"])
        tmap = pd.read_parquet(TICKERS_PATH)
    except FileNotFoundError as exc:
        print(f"CRITICAL: missing file -> {exc}")
        return None, None, None, None
    return fund, snap, prices, tmap


def _normalize_ticker(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().str.strip()


def _validate_feature_store_layer() -> bool:
    print("\n[Check 0] Feature Store Integrity")
    if not os.path.exists(FEATURES_PATH):
        print(f"CRITICAL: missing file -> {FEATURES_PATH}")
        return False
    if not os.path.exists(PRICES_PATH):
        print(f"CRITICAL: missing file -> {PRICES_PATH}")
        return False

    con = duckdb.connect()
    try:
        summary = con.execute(
            f"""
            SELECT
                COUNT(*) AS total_rows,
                SUM(CASE WHEN date IS NULL OR permno IS NULL THEN 1 ELSE 0 END) AS null_key_rows,
                MIN(CAST(date AS DATE)) AS min_date,
                MAX(CAST(date AS DATE)) AS max_date
            FROM '{FEATURES_PATH}'
            """
        ).fetchone()

        duplicate_keys = con.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT CAST(date AS DATE) AS date_key,
                       CAST(permno AS BIGINT) AS permno_key,
                       COUNT(*) AS n
                FROM '{FEATURES_PATH}'
                GROUP BY 1, 2
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        if os.path.exists(PATCH_PATH):
            max_price_date = con.execute(
                f"""
                SELECT MAX(d) FROM (
                    SELECT MAX(CAST(date AS DATE)) AS d FROM '{PRICES_PATH}'
                    UNION ALL
                    SELECT MAX(CAST(date AS DATE)) AS d FROM '{PATCH_PATH}'
                )
                """
            ).fetchone()[0]
        else:
            max_price_date = con.execute(
                f"SELECT MAX(CAST(date AS DATE)) AS d FROM '{PRICES_PATH}'"
            ).fetchone()[0]

        score_nan_ratio = con.execute(
            f"""
            SELECT AVG(
                CASE
                    WHEN composite_score IS NULL OR NOT isfinite(CAST(composite_score AS DOUBLE)) THEN 1.0
                    ELSE 0.0
                END
            )
            FROM '{FEATURES_PATH}'
            """
        ).fetchone()[0]
    finally:
        con.close()

    total_rows = int(summary[0]) if summary and summary[0] is not None else 0
    null_key_rows = int(summary[1]) if summary and summary[1] is not None else 0
    min_date = pd.to_datetime(summary[2], errors="coerce") if summary and summary[2] is not None else pd.NaT
    max_date = pd.to_datetime(summary[3], errors="coerce") if summary and summary[3] is not None else pd.NaT
    max_price_ts = pd.to_datetime(max_price_date, errors="coerce") if max_price_date is not None else pd.NaT
    freshness_gap_days = (
        int((max_price_ts - max_date).days)
        if pd.notna(max_price_ts) and pd.notna(max_date)
        else None
    )

    print(f"Rows: {total_rows:,}")
    print(f"Null key rows: {null_key_rows}")
    print(f"Duplicate (date, permno) keys: {int(duplicate_keys)}")
    print(f"Date range: {str(min_date.date()) if pd.notna(min_date) else 'NA'} -> {str(max_date.date()) if pd.notna(max_date) else 'NA'}")
    if freshness_gap_days is not None:
        print(f"Freshness gap vs latest prices: {freshness_gap_days} day(s)")
    if score_nan_ratio is not None:
        print(f"Composite-score NaN ratio: {float(score_nan_ratio):.2%}")

    passed = (
        total_rows > 0
        and null_key_rows == 0
        and int(duplicate_keys) == 0
        and (freshness_gap_days is None or freshness_gap_days <= 7)
    )
    if not passed:
        print("FAIL: feature store integrity checks failed.")
    else:
        print("PASS: feature store integrity checks passed.")
    return passed


def validate() -> bool:
    print("Starting Data Layer Integrity Check...")
    fund, snap, prices, tmap = _safe_load()
    if fund is None:
        return False

    features_ok = _validate_feature_store_layer()

    # Normalize
    fund = fund.copy()
    fund["ticker"] = _normalize_ticker(fund["ticker"])
    fund["release_date"] = pd.to_datetime(fund["release_date"], errors="coerce")
    fund["fiscal_period_end"] = pd.to_datetime(fund["fiscal_period_end"], errors="coerce")
    fund["ingested_at"] = pd.to_datetime(fund["ingested_at"], errors="coerce")

    tmap = tmap.copy()
    tmap["ticker"] = _normalize_ticker(tmap["ticker"])
    tmap["permno"] = pd.to_numeric(tmap["permno"], errors="coerce").astype("Int64")
    tmap = tmap.dropna(subset=["permno"])
    tmap["permno"] = tmap["permno"].astype("int64")

    snap = snap.copy()
    snap["ticker"] = _normalize_ticker(snap["ticker"])
    snap["release_date"] = pd.to_datetime(snap["release_date"], errors="coerce")

    # Top 3000 investable scope
    top3000 = [str(t).upper().strip() for t in updater.get_top_liquid_tickers(3000)]
    top3000_set = set(top3000)
    top_universe_n = max(len(top3000_set), 1)

    # Check 1: Zombie Audit
    # Snapshot should be scanner-clean (active-only after remediation).
    zombie_cutoff = pd.Timestamp.utcnow().tz_localize(None).normalize() - pd.DateOffset(months=6)
    zombies_snap = snap[snap["release_date"] <= zombie_cutoff]
    latest_dates = fund.groupby("ticker", dropna=True)["release_date"].max()
    zombies_global_hist = latest_dates[latest_dates < pd.Timestamp("2024-01-01")]

    print("\n[Check 1] Zombie Audit")
    print(f"Snapshot zombies (release_date <= {zombie_cutoff.date()}): {len(zombies_snap)} / {len(snap)}")
    print(f"Historical zombies in fundamentals (<2024-01-01, advisory only): {len(zombies_global_hist)} / {len(latest_dates)}")

    # Check 2: Frankenstein Audit (alignment)
    # prices.parquet is long format, so use ticker map + Top3000
    price_tickers_top = set(tmap[tmap["ticker"].isin(top3000_set)]["ticker"])
    # Coverage should be measured on canonical fundamentals universe,
    # not the scanner-clean snapshot (which intentionally culls stale names).
    fund_tickers_top = set(fund[fund["ticker"].isin(top3000_set)]["ticker"])
    common = price_tickers_top.intersection(fund_tickers_top)
    missing_in_price = fund_tickers_top - price_tickers_top
    missing_in_fund = price_tickers_top - fund_tickers_top
    coverage = len(common) / float(top_universe_n)
    missing_in_price_pct = (len(missing_in_price) / float(top_universe_n)) * 100.0

    print("\n[Check 2] Alignment Audit")
    print(f"Universe Coverage: {len(common)} / {top_universe_n} ({coverage:.1%})")
    print(f"Tickers with fundamentals but no price map (Top3000): {len(missing_in_price)} ({missing_in_price_pct:.2f}%)")
    print(f"Tickers with price map but no fundamentals (Top3000): {len(missing_in_fund)}")
    if missing_in_price_pct > 5.0:
        print("WARNING: missing_in_price > 5% of Top3000. Ticker mapping likely degraded.")

    # Check 3: Time Traveler Audit
    # Deduplicate fiscal rows with source precedence before PIT check.
    pri = {"yfinance": 0, "compustat_csv": 1}
    pit_base = fund.copy()
    pit_base["_pri"] = pit_base["source"].map(pri).fillna(0)
    pit_base = pit_base.sort_values(["permno", "fiscal_period_end", "_pri", "ingested_at"])
    pit_base = pit_base.drop_duplicates(subset=["permno", "fiscal_period_end"], keep="last")

    pit_rows = pit_base[
        pit_base["fiscal_period_end"].notna()
        & pit_base["release_date"].notna()
    ].copy()
    pit_violations = pit_rows[pit_rows["release_date"] <= pit_rows["fiscal_period_end"]]

    print("\n[Check 3] PIT Audit")
    print(f"PIT violations (release_date <= fiscal_period_end): {len(pit_violations)} / {len(pit_rows)}")

    sample = pit_base[pit_base["ticker"].isin(["NVDA", "AAPL"])].sort_values("release_date").tail(10)
    print("\nPIT Sample (NVDA/AAPL latest rows):")
    print(sample[["ticker", "fiscal_period_end", "release_date", "revenue", "source"]].to_string(index=False))

    # Snapshot-quality metrics (scanner-facing)
    nan_growth_snap = snap["revenue_growth_yoy"].isna().mean() if len(snap) else 1.0
    nan_roic_snap = snap["roic"].isna().mean() if len(snap) else 1.0
    print(f"\nSnapshot Data Quality: {(1 - nan_growth_snap):.1%} rows have non-null revenue_growth_yoy")
    print(f"Snapshot Data Quality: {(1 - nan_roic_snap):.1%} rows have non-null roic")

    # Legacy historical quality (informational only)
    nan_growth_hist = fund["revenue_growth_yoy"].isna().mean()
    print(f"Historical fundamentals quality (informational): {(1 - nan_growth_hist):.1%} non-null growth")

    # Hard sign-off criteria for scanner readiness + PIT integrity.
    passed = (
        features_ok
        and
        coverage > 0.85
        and nan_growth_snap < 0.05
        and nan_roic_snap < 0.05
        and len(zombies_snap) == 0
        and len(pit_violations) == 0
    )
    if passed:
        print("\nDATA LAYER: PASSED. Ready for Catalyst Radar.")
    else:
        print("\nDATA LAYER: FAILED. Fix before proceeding.")
        if not features_ok:
            print("- Reason: feature store integrity checks failed")
        if coverage <= 0.85:
            print("- Reason: coverage <= 85%")
        if nan_growth_snap >= 0.05:
            print("- Reason: snapshot revenue_growth_yoy NaN >= 5%")
        if nan_roic_snap >= 0.05:
            print("- Reason: snapshot roic NaN >= 5%")
        if len(zombies_snap) > 0:
            print("- Reason: snapshot has zombie rows")
        if len(pit_violations) > 0:
            print("- Reason: PIT violations present")

    return passed


if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
