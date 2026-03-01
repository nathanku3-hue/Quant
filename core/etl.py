"""
Terminal Zero — ETL Pipeline
Reads raw CRSP daily CSV → prices.parquet + macro.parquet

Decisions Implemented:
  D-01: Merge dlret into ret → total_ret (captures delistings)
  D-02: adj_close = abs(PRC) [no cfacpr available — split trap acknowledged]
  D-06: Forward-fill NaN policy applied post-load
"""

import duckdb
import os
import numpy as np
import pandas as pd

# ── Config ───────────────────────────────────────────────────────────────────
RAW_CSV = "./hkcj1itkyvfsmibz.csv"          # Raw CRSP daily file (already extracted)
PROCESSED_DIR = "./data/processed"
SPY_PERMNO = 84398

def build_prices(con: duckdb.DuckDBPyConnection) -> None:
    """
    Prices Parquet — The Asset Universe.
    Columns: date, permno, raw_close, adj_close, total_ret, volume
    """
    print("[1/3] Building prices.parquet ...")

    query = f"""
        COPY (
            SELECT
                CAST(date AS DATE)                                       AS date,
                CAST(PERMNO AS UINTEGER)                                 AS permno,
                ABS(TRY_CAST(PRC AS DOUBLE))                             AS raw_close,
                ABS(TRY_CAST(PRC AS DOUBLE))                             AS adj_close,
                COALESCE(TRY_CAST(RET AS DOUBLE), 0.0)
                  + COALESCE(TRY_CAST(DLRET AS DOUBLE), 0.0)             AS total_ret,
                COALESCE(TRY_CAST(VOL AS DOUBLE), 0.0)                   AS volume
            FROM read_csv_auto('{RAW_CSV}', all_varchar=true)
            WHERE PERMNO IS NOT NULL
              AND date   IS NOT NULL
            ORDER BY permno, date
        ) TO '{PROCESSED_DIR}/prices.parquet' (FORMAT 'PARQUET', CODEC 'SNAPPY');
    """
    con.execute(query)
    print("      ✓ prices.parquet written")


def build_macro(con: duckdb.DuckDBPyConnection) -> None:
    """
    Macro Parquet — SPY close + synthesised VIX proxy.
    VIX proxy = 20-day realised vol of SPY returns × √252 × 100.
    """
    print("[2/3] Building macro.parquet ...")

    # Extract SPY series via DuckDB (fast scan)
    spy_df = con.execute(f"""
        SELECT
            CAST(date AS DATE)          AS date,
            ABS(TRY_CAST(PRC AS DOUBLE))    AS spy_close,
            TRY_CAST(RET AS DOUBLE)         AS spy_ret
        FROM read_csv_auto('{RAW_CSV}', all_varchar=true)
        WHERE CAST(PERMNO AS INTEGER) = {SPY_PERMNO}
          AND date IS NOT NULL
        ORDER BY date
    """).df()

    spy_df["date"] = pd.to_datetime(spy_df["date"])
    spy_df = spy_df.set_index("date").sort_index()

    # Forward-fill price gaps (D-06)
    spy_df["spy_close"] = spy_df["spy_close"].ffill()

    # Synthesise VIX proxy: annualised 20-day realised vol × 100
    spy_df["vix_proxy"] = (
        spy_df["spy_ret"]
        .fillna(0.0)
        .rolling(20)
        .std()
        * np.sqrt(252)
        * 100
    )
    spy_df["vix_proxy"] = spy_df["vix_proxy"].fillna(15.0)  # default calm

    macro = spy_df[["spy_close", "vix_proxy"]].reset_index()
    macro.to_parquet(f"{PROCESSED_DIR}/macro.parquet", engine="pyarrow", compression="snappy")
    print("      ✓ macro.parquet written")


def validate() -> None:
    """Quick sanity check on generated files."""
    print("[3/3] Validating outputs ...")

    prices = pd.read_parquet(f"{PROCESSED_DIR}/prices.parquet")
    macro  = pd.read_parquet(f"{PROCESSED_DIR}/macro.parquet")

    print(f"      prices : {prices.shape[0]:,} rows × {prices.shape[1]} cols  "
          f"| permnos: {prices['permno'].nunique():,}")
    print(f"      macro  : {macro.shape[0]:,} rows × {macro.shape[1]} cols")
    print(f"      date range : {prices['date'].min()} → {prices['date'].max()}")

    nan_counts = prices.isna().sum()
    if nan_counts.any():
        print(f"      ⚠ NaN counts: {nan_counts[nan_counts > 0].to_dict()}")
    else:
        print("      ✓ No NaNs in prices")

    spy_check = prices[prices["permno"] == SPY_PERMNO]
    print(f"      SPY rows: {len(spy_check):,}")
    print("      ✓ Validation complete")


if __name__ == "__main__":
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    con = duckdb.connect(":memory:")
    build_prices(con)
    build_macro(con)
    con.close()

    validate()
    print("\n✅ ETL Complete — Terminal Zero data lake is ready.")
