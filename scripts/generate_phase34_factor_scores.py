"""
Generate phase34_factor_scores.parquet artifact.

Loads features, computes normalized factor scores using CompanyScorecard,
and saves the factor scores to data/processed/phase34_factor_scores.parquet.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.factor_specs import (  # noqa: E402
    build_default_factor_specs,
    build_phase19_5_candidate_factor_sets,
    build_phase35_wave1_candidate_specs,
)


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FEATURES_PATH = PROCESSED_DIR / "features.parquet"
OUTPUT_PATH = PROCESSED_DIR / "phase34_factor_scores.parquet"

# Build preset registry
FACTOR_PRESETS = {
    "DEFAULT_DAY4": build_default_factor_specs(),
    **build_phase19_5_candidate_factor_sets(),
    "PHASE35_W1_CANDIDATES": build_phase35_wave1_candidate_specs(),
}


def _atomic_parquet_write(df: pd.DataFrame, path: Path) -> None:
    """Atomic write for parquet files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        df.to_parquet(tmp, index=False, engine="pyarrow")
        for i in range(tries):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if i == tries - 1:
                    raise
                time.sleep(0.1 * (2 ** i))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


def main() -> None:
    """Generate phase34_factor_scores.parquet."""
    parser = argparse.ArgumentParser(
        description="Generate factor scores parquet with preset-based factor specs"
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="DEFAULT_DAY4",
        help="Factor preset name to use (default: DEFAULT_DAY4)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_PATH),
        help=f"Output path for factor scores parquet (default: {OUTPUT_PATH})",
    )
    args = parser.parse_args()

    # Validate preset exists
    if args.preset not in FACTOR_PRESETS:
        available = ", ".join(FACTOR_PRESETS.keys())
        raise ValueError(f"Unknown preset '{args.preset}'. Available presets: {available}")

    output_path = Path(args.output)

    print(f"Loading features from {FEATURES_PATH}")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")

    # Only load columns needed for scoring to reduce memory usage
    # Based on actual columns available in features.parquet
    required_input_cols = [
        "date",
        "permno",
        # Momentum candidates (only resid_mom_60d exists)
        "resid_mom_60d",
        # Quality candidates
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "z_moat",
        # Volatility candidates
        "yz_vol_20d",
        "atr_14d",
        # Illiquidity candidates
        "amihud_20d",
        "z_flow_proxy",
    ]

    features = pd.read_parquet(FEATURES_PATH, columns=required_input_cols)
    print(f"Loaded {len(features):,} rows from features.parquet")

    # Build scorecard with specified preset
    print(f"Building CompanyScorecard with preset '{args.preset}'")
    factor_specs = FACTOR_PRESETS[args.preset]
    scorecard = CompanyScorecard(factor_specs=factor_specs)

    # Compute scores (returns tuple: scores_df, summary)
    print("Computing scores...")
    scores_df, summary = scorecard.compute_scores(features)
    print(f"Computed scores for {len(scores_df):,} rows")
    print(f"Summary: n_dates={summary.n_dates}, coverage={summary.coverage:.2%}")

    # Rename 'score' to 'composite_score' for AlphaEngine compatibility
    if 'score' in scores_df.columns:
        scores_df = scores_df.rename(columns={'score': 'composite_score'})

    # Extract required columns
    required_cols = [
        "date",
        "permno",
        "momentum_normalized",
        "quality_normalized",
        "volatility_normalized",
        "illiquidity_normalized",
        "composite_score",
    ]

    missing_cols = [col for col in required_cols if col not in scores_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in scores_df: {missing_cols}")

    factor_scores = scores_df[required_cols].copy()

    # Normalize dates to tz-naive
    factor_scores["date"] = pd.to_datetime(factor_scores["date"], errors="coerce")
    if factor_scores["date"].dt.tz is not None:
        factor_scores["date"] = factor_scores["date"].dt.tz_localize(None)

    print(f"Extracted {len(factor_scores):,} rows with {len(required_cols)} columns")

    # Save with atomic write
    print(f"Writing to {output_path}")
    _atomic_parquet_write(factor_scores, output_path)
    print(f"Successfully wrote {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
