from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import wrds

GLOBAL_OUTPUT_PATH = Path("data/processed/osiris_global_hardware_daily.parquet")
REGIONAL_OUTPUT_PATH = Path("data/processed/osiris_regional_hardware_daily.parquet")
KEY_REGIONS = ("TW", "KR", "DE", "JP", "CN")


def _atomic_write_parquet(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".parquet",
        prefix=f".{output_path.stem}.",
        dir=output_path.parent,
        delete=False,
    ) as tmp:
        temp_path = Path(tmp.name)
    try:
        df.to_parquet(temp_path, index=False)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def fetch_osiris_hardware_non_us(db: wrds.Connection) -> pd.DataFrame:
    # Critical duplication fix at SQL layer: DISTINCT over joined rows.
    sql = """
    SELECT DISTINCT
        f.os_id_number,
        f.closdate,
        g.cntrycde AS iso_country,
        g.country,
        COALESCE(f.data13004, f.data13002, f.data13000) AS revenue,
        f.data20010 AS inventory,
        f.data31220 AS stock_turnover,
        g.caics12cod AS core_naics12,
        a.naics12cde AS sec_naics12
    FROM bvd_osiris.os_fin_ind AS f
    INNER JOIN bvd_osiris.os_gen AS g
        ON f.os_id_number = g.os_id_number
    LEFT JOIN bvd_osiris.os_activ_naics12cde AS a
        ON f.os_id_number = a.os_id_number
    WHERE f.closdate IS NOT NULL
      AND COALESCE(f.data13004, f.data13002, f.data13000) IS NOT NULL
      AND f.data20010 IS NOT NULL
      AND f.data20010 > 0
      AND g.cntrycde IS NOT NULL
      AND g.cntrycde <> 'US'
      AND (
            g.caics12cod LIKE '334%%'
         OR a.naics12cde LIKE '334%%'
      )
    """
    return db.raw_sql(sql)


def build_daily_signals(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if raw_df.empty:
        empty_global = pd.DataFrame(columns=["closdate", "median_inv_turnover", "n_companies"])
        empty_regional = pd.DataFrame(
            columns=["closdate", "iso_country", "median_inv_turnover", "n_companies"]
        )
        return raw_df, empty_global, empty_regional

    df = raw_df.copy()
    df["closdate"] = pd.to_datetime(df["closdate"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["inventory"] = pd.to_numeric(df["inventory"], errors="coerce")
    df["iso_country"] = df["iso_country"].astype(str).str.upper().str.strip()

    # Ensure one company-date row after SQL DISTINCT.
    # Prefer rows where core NAICS clearly indicates hardware.
    df["core_334_flag"] = df["core_naics12"].fillna("").astype(str).str.startswith("334")
    df = df.sort_values(
        by=["os_id_number", "closdate", "core_334_flag"],
        ascending=[True, True, False],
    )
    df = df.drop_duplicates(subset=["os_id_number", "closdate"], keep="first")

    df = df[df["closdate"].notna()].copy()
    df = df[(df["inventory"] > 0) & df["revenue"].notna()].copy()
    df["inv_turnover"] = df["revenue"] / df["inventory"]
    df = df[df["inv_turnover"].notna() & (df["inv_turnover"] != float("inf"))].copy()

    global_daily = (
        df.groupby("closdate", as_index=False)
        .agg(
            median_inv_turnover=("inv_turnover", "median"),
            n_companies=("os_id_number", "nunique"),
        )
        .sort_values("closdate")
    )

    regional_base = df[df["iso_country"].isin(KEY_REGIONS)].copy()
    regional_daily = (
        regional_base.groupby(["closdate", "iso_country"], as_index=False)
        .agg(
            median_inv_turnover=("inv_turnover", "median"),
            n_companies=("os_id_number", "nunique"),
        )
        .sort_values(["closdate", "iso_country"])
    )

    return df, global_daily, regional_daily


def main() -> None:
    print("Connecting to WRDS...")
    db = wrds.Connection()
    try:
        print("Running Osiris hardware extraction query...")
        raw = fetch_osiris_hardware_non_us(db)
    finally:
        db.close()

    print(f"Raw extracted rows: {len(raw)}")

    deduped, global_daily, regional_daily = build_daily_signals(raw)

    _atomic_write_parquet(global_daily, GLOBAL_OUTPUT_PATH)
    _atomic_write_parquet(regional_daily, REGIONAL_OUTPUT_PATH)

    unique_companies = int(deduped["os_id_number"].nunique()) if not deduped.empty else 0
    print(f"Total unique hardware companies extracted: {unique_companies}")
    print("\nGlobal signal tail (last 5 rows):")
    if global_daily.empty:
        print("<empty>")
    else:
        print(global_daily.tail(5).to_string(index=False))

    print(f"\nSaved: {GLOBAL_OUTPUT_PATH}")
    print(f"Saved: {REGIONAL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
