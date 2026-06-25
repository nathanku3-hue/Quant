"""
Generate universe_r3000_daily.parquet — SYNTHETIC liquidity proxy.

NOT actual Russell 3000 membership. Uses top-3000 liquid permnos per date
(rolling 63-day dollar volume from prices_tri.parquet) as a proxy when WRDS
constituent history is unavailable.

Provenance: synthetic_liquidity_top3000
Source: prices_tri.parquet (volume * tri, 63-day rolling average)
"""
import json
import os
from datetime import datetime, timezone

import duckdb
import pandas as pd

PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
PRICES_TRI_PATH = os.path.join(PROCESSED_DIR, "prices_tri.parquet")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "universe_r3000_daily.parquet")
MANIFEST_PATH = os.path.join(PROCESSED_DIR, "universe_r3000_daily_manifest.json")

PROVENANCE = "synthetic_liquidity_top3000"


def build_synthetic_r3000_universe() -> pd.DataFrame:
    con = duckdb.connect()
    df = con.execute(f"""
        WITH dvol AS (
            SELECT
                date,
                permno,
                ticker,
                volume * tri AS dollar_vol
            FROM '{PRICES_TRI_PATH}'
            WHERE date >= DATE '2000-01-01'
              AND volume > 0
              AND tri > 0
        ),
        rolling AS (
            SELECT
                date,
                permno,
                ticker,
                AVG(dollar_vol) OVER (
                    PARTITION BY permno
                    ORDER BY date
                    ROWS BETWEEN 62 PRECEDING AND CURRENT ROW
                ) AS avg_dvol_63d
            FROM dvol
        ),
        ranked AS (
            SELECT
                date,
                permno,
                ticker,
                ROW_NUMBER() OVER (PARTITION BY date ORDER BY avg_dvol_63d DESC) AS rk
            FROM rolling
            WHERE avg_dvol_63d IS NOT NULL
        )
        SELECT date, CAST(permno AS UINTEGER) AS permno, ticker, '' AS gvkey
        FROM ranked
        WHERE rk <= 3000
        ORDER BY date, permno
    """).df()
    con.close()
    df["provenance"] = PROVENANCE
    return df


def write_manifest(df: pd.DataFrame) -> None:
    manifest = {
        "artifact": "universe_r3000_daily.parquet",
        "provenance": PROVENANCE,
        "description": (
            "Synthetic universe proxy: top-3000 permnos by rolling 63-day dollar volume. "
            "NOT actual Russell 3000 index membership."
        ),
        "source": "prices_tri.parquet",
        "method": "rolling_63d_dollar_volume_rank_top_3000",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": len(df),
        "dates": int(df["date"].nunique()),
        "permnos": int(df["permno"].nunique()),
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main():
    print(f"Building SYNTHETIC R3000 PIT universe proxy from {PRICES_TRI_PATH}")
    print(f"  provenance: {PROVENANCE}")
    df = build_synthetic_r3000_universe()
    print(f"  rows: {len(df):,}  dates: {df['date'].nunique():,}  permnos: {df['permno'].nunique():,}")
    df.to_parquet(OUTPUT_PATH, index=False)
    write_manifest(df)
    print(f"  wrote: {OUTPUT_PATH}")
    print(f"  wrote: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
