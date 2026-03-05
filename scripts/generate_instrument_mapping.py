"""
Generate instrument_mapping.parquet from tickers.parquet

Phase 33A Step 3: Creates canonical permno ↔ symbol mapping file.

Run once to initialize the mapping file, then update monthly or after corporate actions.
"""

from datetime import date
from pathlib import Path

import pandas as pd


def generate_instrument_mapping(
    tickers_path: str | Path = "data/processed/tickers.parquet",
    output_path: str | Path = "data/static/instrument_mapping.parquet",
    snapshot_date: date | None = None,
) -> None:
    """
    Generate instrument_mapping.parquet from tickers.parquet.

    Args:
        tickers_path: Path to source tickers.parquet (permno, ticker columns)
        output_path: Path to output instrument_mapping.parquet
        snapshot_date: Snapshot date for mapping (defaults to 1900-01-01 for point-in-time)

    Note:
        Phase 33 uses fixed floor date (1900-01-01) for point-in-time mapping.
        This ensures all reasonable as_of queries (1900+ onwards) resolve successfully.
        Temporal ticker-change support deferred to Phase 34+.
    """
    # Load source tickers
    print(f"Loading tickers from: {tickers_path}")
    tickers_df = pd.read_parquet(tickers_path)

    if "permno" not in tickers_df.columns or "ticker" not in tickers_df.columns:
        raise ValueError("tickers.parquet must have 'permno' and 'ticker' columns")

    # Use 1900-01-01 floor date if not specified (point-in-time mapping)
    # This allows all reasonable as_of queries to succeed (snapshot_date <= as_of)
    if snapshot_date is None:
        snapshot_date = date(1900, 1, 1)  # Fixed floor date for point-in-time contract

    # Create instrument mapping with required schema
    mapping_df = pd.DataFrame({
        "permno": tickers_df["permno"].astype(int),
        "symbol": tickers_df["ticker"].astype(str).str.upper().str.strip(),
        "cusip": None,  # CUSIP not available in tickers.parquet, fill with None
        "snapshot_date": pd.to_datetime(snapshot_date).date(),
    })

    # Remove duplicates (keep first occurrence)
    mapping_df = mapping_df.drop_duplicates(subset=["permno", "symbol"], keep="first")

    # Sort by permno for readability
    mapping_df = mapping_df.sort_values("permno")

    # Save to output path with atomic write (temp + replace)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file first
    temp_path = output_path.parent / f"{output_path.name}.tmp"
    mapping_df.to_parquet(temp_path, index=False)

    # Atomic replace
    temp_path.replace(output_path)

    print(f"Generated instrument mapping: {output_path}")
    print(f"  Entries: {len(mapping_df):,}")
    print(f"  Snapshot date: {snapshot_date}")
    print(f"  Schema: {list(mapping_df.columns)}")
    print(f"  Sample:\n{mapping_df.head(10)}")


if __name__ == "__main__":
    generate_instrument_mapping()
