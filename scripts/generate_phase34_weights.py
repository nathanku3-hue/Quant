#!/usr/bin/env python3
"""
Generate phase34_target_weights.parquet

Loads features with 60-day lookback, uses AlphaEngine to generate target weights
for each date, and saves as parquet with atomic write.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from strategies.alpha_engine import AlphaEngine, AlphaEngineConfig

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_REGIME_HISTORY_PATH = PROCESSED_DIR / "regime_history.csv"
DEFAULT_OUTPUT_PATH = PROCESSED_DIR / "phase34_target_weights.parquet"

LOOKBACK_DAYS = 60


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _atomic_parquet_write(df: pd.DataFrame, path: Path):
    """Atomic write with temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_parquet(temp_path, index=False)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def load_features_with_lookback(
    features_path: Path,
    lookback_days: int = 60,
    factor_scores_path: Path | None = None
) -> pd.DataFrame:
    """
    Load features from parquet with lookback for rolling history using DuckDB.

    If factor_scores_path is provided, merges factor scores with technical indicators
    from features_path. Otherwise, loads directly from features_path.
    """
    if not features_path.exists():
        raise FileNotFoundError(f"Missing feature store: {features_path}")

    # If factor scores provided, merge with technical features
    if factor_scores_path and factor_scores_path.exists():
        print(f"Loading factor scores from {factor_scores_path}...")

        # Load factor scores (includes composite_score and wave-specific factors)
        factor_query = f"""
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            CAST(composite_score AS DOUBLE) AS composite_score
        FROM read_parquet('{_sql_escape_path(factor_scores_path)}')
        ORDER BY date, permno
        """

        con = duckdb.connect()
        try:
            factor_scores = con.execute(factor_query).df()
        finally:
            con.close()

        print(f"Loaded {len(factor_scores):,} factor score rows")

        # Load technical indicators from baseline features
        print(f"Loading technical indicators from {features_path}...")
        technical_query = f"""
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            CAST(adj_close AS DOUBLE) AS adj_close,
            CAST(volume AS DOUBLE) AS volume,
            CAST(sma200 AS DOUBLE) AS sma200,
            CAST(dist_sma20 AS DOUBLE) AS dist_sma20,
            CAST(rsi_14d AS DOUBLE) AS rsi_14d,
            CAST(atr_14d AS DOUBLE) AS atr_14d,
            CAST(yz_vol_20d AS DOUBLE) AS yz_vol_20d,
            trend_veto
        FROM read_parquet('{_sql_escape_path(features_path)}')
        ORDER BY date, permno
        """

        con = duckdb.connect()
        try:
            technical_features = con.execute(technical_query).df()
        finally:
            con.close()

        print(f"Loaded {len(technical_features):,} technical indicator rows")

        # Merge on (date, permno)
        print("Merging factor scores with technical indicators...")
        df = factor_scores.merge(
            technical_features,
            on=["date", "permno"],
            how="inner"
        )

        print(f"Merged dataset: {len(df):,} rows (inner join on date, permno)")

    else:
        # Fallback: load directly from features_path
        print(f"Loading features from {features_path} using DuckDB...")

        query = f"""
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            CAST(adj_close AS DOUBLE) AS adj_close,
            CAST(volume AS DOUBLE) AS volume,
            CAST(sma200 AS DOUBLE) AS sma200,
            CAST(dist_sma20 AS DOUBLE) AS dist_sma20,
            CAST(rsi_14d AS DOUBLE) AS rsi_14d,
            CAST(atr_14d AS DOUBLE) AS atr_14d,
            CAST(yz_vol_20d AS DOUBLE) AS yz_vol_20d,
            CAST(composite_score AS DOUBLE) AS composite_score,
            trend_veto
        FROM read_parquet('{_sql_escape_path(features_path)}')
        ORDER BY date, permno
        """

        con = duckdb.connect()
        try:
            df = con.execute(query).df()
        finally:
            con.close()

    if df.empty:
        raise RuntimeError("No features loaded from parquet")

    # Normalize dates to tz-naive (already tz-naive from DuckDB)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["date", "permno"])
    df = df.sort_values(["date", "permno"])

    print(f"Final dataset: {len(df):,} feature rows, date range: {df['date'].min()} to {df['date'].max()}")
    return df


def load_regime_history(regime_path: Path) -> pd.DataFrame:
    """Load regime_history.csv and normalize dates to tz-naive."""
    if not regime_path.exists():
        raise FileNotFoundError(f"Missing regime history: {regime_path}")

    print(f"Loading regime history from {regime_path}...")
    df = pd.read_csv(regime_path)

    if "date" not in df.columns or "governor_state" not in df.columns:
        raise ValueError("regime_history.csv missing required columns `date` or `governor_state`.")

    # Normalize dates to tz-naive (already tz-naive from CSV)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"])
    df = df.set_index("date").sort_index()

    print(f"Loaded {len(df):,} regime rows, date range: {df.index.min()} to {df.index.max()}")
    return df


def generate_target_weights(
    features: pd.DataFrame,
    regime_history: pd.DataFrame,
    target_dates: pd.DatetimeIndex,
    lookback_days: int = 60,
) -> pd.DataFrame:
    """
    Generate target weights for each date using AlphaEngine.

    For each target date:
    - Get rolling history up to that date (with lookback)
    - Get actual regime via reindex/ffill
    - Call engine.build_daily_plan() with rolling history + regime
    """
    engine = AlphaEngine(AlphaEngineConfig())

    print(f"Processing {len(target_dates):,} unique dates...")

    # Prepare feature history once (compute adv20 and thresholds)
    print("Preparing feature history (computing adv20 and thresholds)...")
    prepared_features = engine.prepare_feature_history(features)

    # Reindex regime to full target_dates range, then ffill, then fillna("AMBER")
    regime_series = regime_history["governor_state"].reindex(target_dates)
    regime_series = regime_series.ffill().fillna("AMBER")

    results = []

    for i, target_date in enumerate(target_dates):
        if i % 100 == 0:
            print(f"Processing date {i+1}/{len(target_dates)}: {target_date.date()}")

        # Get rolling history up to target date (with lookback)
        start_date = target_date - pd.Timedelta(days=lookback_days)
        rolling_hist = prepared_features[
            (prepared_features["date"] >= start_date) &
            (prepared_features["date"] <= target_date)
        ].copy()

        if rolling_hist.empty:
            continue

        # Get actual regime from pre-computed series
        regime_state = regime_series.loc[target_date]

        # Call engine.build_daily_plan() with rolling history + regime
        try:
            plan = engine.build_daily_plan(
                features=rolling_hist,
                regime_state=regime_state,
                asof_date=target_date,
                market_vol=None,
            )

            # Extract weights (Series with permno as index)
            if not plan.empty and not plan.weights.empty:
                for permno, weight in plan.weights.items():
                    results.append({
                        "date": target_date,
                        "permno": int(permno),
                        "weight": float(weight),
                    })
        except Exception as e:
            print(f"Warning: Failed to generate plan for {target_date.date()}: {e}")
            continue

    if not results:
        raise RuntimeError("No target weights generated")

    print(f"Generated {len(results):,} weight records")
    return pd.DataFrame(results)


def pivot_to_wide_format(weights_long: pd.DataFrame) -> pd.DataFrame:
    """Pivot to wide format (Date × Permno)."""
    print("Pivoting to wide format (Date × Permno)...")
    wide = weights_long.pivot(index="date", columns="permno", values="weight")
    wide = wide.fillna(0.0)
    print(f"Wide format shape: {wide.shape[0]} dates × {wide.shape[1]} permnos")
    return wide


def main():
    parser = argparse.ArgumentParser(description="Generate phase34_target_weights.parquet")
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD) for weight generation",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD) for weight generation",
    )
    parser.add_argument(
        "--factor-scores",
        type=str,
        default=str(PROCESSED_DIR / "phase34_factor_scores.parquet"),
        help="Path to factor scores parquet file (default: data/processed/phase34_factor_scores.parquet)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output path for target weights parquet (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    # Parse dates
    start_date = pd.to_datetime(args.start_date).normalize()
    end_date = pd.to_datetime(args.end_date).normalize()

    # Validate factor scores path exists
    factor_scores_path = Path(args.factor_scores)
    if not factor_scores_path.exists():
        raise FileNotFoundError(f"Factor scores file not found: {factor_scores_path}")

    features_path = DEFAULT_FEATURES_PATH
    regime_path = DEFAULT_REGIME_HISTORY_PATH
    output_path = Path(args.output)

    print("=" * 70)
    print("Phase 34: Generate Target Weights")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print("=" * 70)

    # Load features with lookback (merge factor scores if provided)
    features = load_features_with_lookback(
        features_path,
        lookback_days=LOOKBACK_DAYS,
        factor_scores_path=factor_scores_path
    )

    # Load regime history
    regime_history = load_regime_history(regime_path)

    # Filter target_dates to only process requested range
    all_dates = sorted(features["date"].unique())
    target_dates = pd.DatetimeIndex([d for d in all_dates if start_date <= d <= end_date])

    if len(target_dates) == 0:
        raise ValueError(f"No dates found in range [{start_date.date()}, {end_date.date()}]")

    print(f"Filtered to {len(target_dates):,} dates in requested range")

    # Generate target weights
    weights_long = generate_target_weights(
        features, regime_history, target_dates, lookback_days=LOOKBACK_DAYS
    )

    # Pivot to wide format
    weights_wide = pivot_to_wide_format(weights_long)

    # Reset index to make date a column for parquet
    weights_wide = weights_wide.reset_index()

    # Save with atomic write
    print(f"Saving to {output_path}...")
    _atomic_parquet_write(weights_wide, output_path)

    print("=" * 70)
    print(f"SUCCESS: Generated {output_path}")
    print(f"  Shape: {weights_wide.shape[0]} dates × {weights_wide.shape[1]-1} permnos")
    print(f"  Date range: {weights_wide['date'].min()} to {weights_wide['date'].max()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
