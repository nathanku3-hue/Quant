from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_FACTOR_SCORES_PATH = PROCESSED_DIR / "phase34_factor_scores.parquet"
DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_TARGET_WEIGHTS_PATH = PROCESSED_DIR / "phase34_target_weights.parquet"
DEFAULT_REGIME_HISTORY_PATH = PROCESSED_DIR / "regime_history.csv"

DEFAULT_OUTPUT_DIR = PROCESSED_DIR


def _atomic_write(content: str | bytes, path: Path, mode: str = "w") -> None:
    """Atomic write using temp file + replace pattern."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        if mode == "wb":
            with open(tmp, "wb") as f:
                f.write(content if isinstance(content, bytes) else content.encode())
        else:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(content if isinstance(content, str) else content.decode())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _atomic_csv_write(df: pd.DataFrame, path: Path, index: bool = True) -> None:
    """Atomic CSV write using temp file + replace pattern."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_csv(tmp, index=index)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _atomic_json_write(data: dict, path: Path) -> None:
    """Atomic JSON write using temp file + replace pattern."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    _atomic_write(content, path, mode="w")


def _to_ts(value: str | None) -> pd.Timestamp | None:
    """Convert string to pandas Timestamp."""
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date value: {value}")
    return pd.Timestamp(ts).normalize()


def _load_parquet_with_retry(path: Path, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> pd.DataFrame:
    """Load parquet file with optional date filtering using pyarrow filters for memory efficiency."""
    if not path.exists():
        raise FileNotFoundError(f"Missing parquet file: {path}")

    # Use pyarrow filters for memory-efficient date filtering BEFORE loading into memory
    filters = []
    if start is not None or end is not None:
        if start is not None:
            filters.append(("date", ">=", start))
        if end is not None:
            filters.append(("date", "<=", end))

    if filters:
        df = pd.read_parquet(path, filters=filters)
    else:
        df = pd.read_parquet(path)

    # Ensure date column is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def load_backtest_data(
    factor_scores_path: Path,
    prices_tri_path: Path,
    target_weights_path: Path,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load backtest data from parquet files with retry/fallback.

    Handles long-form data (prices_tri, factor_scores) and wide-form data (target_weights).
    Pivots long-form data to wide format for analysis.

    Returns:
        tuple: (factor_scores_wide, returns_wide, target_weights_wide, factor_scores_long)
    """
    print(f"Loading factor scores from {factor_scores_path}")
    factor_scores_long = _load_parquet_with_retry(factor_scores_path, start, end)

    print(f"Loading prices TRI from {prices_tri_path}")
    prices_tri_long = _load_parquet_with_retry(prices_tri_path, start, end)

    print(f"Loading target weights from {target_weights_path}")
    target_weights = _load_parquet_with_retry(target_weights_path, start, end)

    # Convert target_weights to wide format if needed
    if "date" in target_weights.columns:
        target_weights = target_weights.set_index("date")

    # Pivot prices_tri from long to wide format (Date × Permno)
    print("Pivoting prices_tri to wide format...")
    if "date" in prices_tri_long.columns and "permno" in prices_tri_long.columns:
        # Use total_ret if available, otherwise tri
        ret_col = "total_ret" if "total_ret" in prices_tri_long.columns else "tri"
        prices_wide = prices_tri_long.pivot(index="date", columns="permno", values=ret_col)
        prices_wide.index = pd.to_datetime(prices_wide.index)

        # Convert permno columns to strings to match target_weights
        prices_wide.columns = prices_wide.columns.astype(str)

        # Calculate returns from prices
        print("Calculating returns...")
        returns_wide = prices_wide.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    else:
        raise ValueError("prices_tri must have 'date' and 'permno' columns")

    # Pivot factor_scores from long to wide format for each factor
    print("Pivoting factor scores to wide format...")
    factor_cols = [col for col in factor_scores_long.columns if col not in ["date", "permno"]]

    # Create a multi-level wide format: Date × (Factor, Permno)
    # For IC calculation, we need Date × Permno for each factor
    factor_scores_wide = {}
    for factor in factor_cols:
        factor_wide = factor_scores_long.pivot(index="date", columns="permno", values=factor)
        factor_wide.index = pd.to_datetime(factor_wide.index)
        # Convert permno columns to strings to match target_weights
        factor_wide.columns = factor_wide.columns.astype(str)
        factor_scores_wide[factor] = factor_wide

    return factor_scores_wide, returns_wide, target_weights, factor_scores_long


def load_regime_history(
    regime_history_path: Path,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Load regime history from CSV file.

    Returns:
        DataFrame with governor_state column
    """
    if not regime_history_path.exists():
        raise FileNotFoundError(f"Missing regime history file: {regime_history_path}")

    print(f"Loading regime history from {regime_history_path}")
    df = pd.read_csv(regime_history_path)

    # Ensure date column is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.set_index("date")

    # Filter by date range if provided
    if start is not None:
        df = df[df.index >= start]
    if end is not None:
        df = df[df.index <= end]

    if "governor_state" not in df.columns:
        raise ValueError("regime_history.csv must contain 'governor_state' column")

    return df


def calculate_factor_ic(factor_scores_wide: dict[str, pd.DataFrame], returns: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Information Coefficient (IC) for each factor.

    Args:
        factor_scores_wide: Dict of {factor_name: DataFrame(Date × Permno)}
        returns: DataFrame(Date × Permno)

    Returns:
        DataFrame with columns ['date', 'factor', 'ic', 'p_value', 'n_assets'] in long format
    """
    from scipy import stats

    ic_results = []

    # Get common dates across all factors and returns
    all_dates = returns.index
    for factor_name, factor_df in factor_scores_wide.items():
        all_dates = all_dates.intersection(factor_df.index)

    print(f"Computing IC for {len(all_dates)} dates across {len(factor_scores_wide)} factors...")

    for date in all_dates:
        # Get returns for this date
        return_row = returns.loc[date]

        # Calculate IC for each factor
        for factor_name, factor_df in factor_scores_wide.items():
            if date not in factor_df.index:
                continue

            factor_row = factor_df.loc[date]

            # Align by permno (columns)
            common_permnos = factor_row.index.intersection(return_row.index)

            if len(common_permnos) < 3:
                continue

            factor_vals = factor_row[common_permnos]
            return_vals = return_row[common_permnos]

            # Remove NaN values
            valid_mask = factor_vals.notna() & return_vals.notna()
            if valid_mask.sum() < 3:
                continue

            # Calculate Spearman correlation (cross-sectional) and p-value
            factor_valid = factor_vals[valid_mask]
            return_valid = return_vals[valid_mask]

            ic, p_value = stats.spearmanr(factor_valid, return_valid)
            n_assets = len(factor_valid)

            ic_results.append({
                "date": date,
                "factor": factor_name,
                "ic": ic,
                "p_value": p_value,
                "n_assets": n_assets,
            })

    ic_df = pd.DataFrame(ic_results)
    return ic_df


def calculate_regime_ic(
    factor_scores_wide: dict[str, pd.DataFrame],
    returns: pd.DataFrame,
    regime_history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate IC by regime state.

    Args:
        factor_scores_wide: Dict of {factor_name: DataFrame(Date × Permno)}
        returns: DataFrame(Date × Permno)
        regime_history: DataFrame with governor_state column

    Returns:
        DataFrame with regime and IC statistics
    """
    # Get common dates
    all_dates = returns.index.intersection(regime_history.index)
    for factor_name, factor_df in factor_scores_wide.items():
        all_dates = all_dates.intersection(factor_df.index)

    regime_history = regime_history.loc[all_dates]
    returns = returns.loc[all_dates]

    regime_ic_results = []

    print(f"Computing regime IC for {len(regime_history['governor_state'].unique())} regimes...")

    for regime in regime_history["governor_state"].unique():
        regime_mask = regime_history["governor_state"] == regime
        regime_dates = regime_history[regime_mask].index

        if len(regime_dates) == 0:
            continue

        # Calculate IC for each factor in this regime
        for factor_name, factor_df in factor_scores_wide.items():
            ic_values = []

            for date in regime_dates:
                if date not in factor_df.index or date not in returns.index:
                    continue

                factor_row = factor_df.loc[date]
                return_row = returns.loc[date]

                # Align by permno
                common_permnos = factor_row.index.intersection(return_row.index)
                if len(common_permnos) < 3:
                    continue

                factor_vals = factor_row[common_permnos]
                return_vals = return_row[common_permnos]

                valid_mask = factor_vals.notna() & return_vals.notna()
                if valid_mask.sum() < 3:
                    continue

                ic = factor_vals[valid_mask].corr(return_vals[valid_mask], method="spearman")
                ic_values.append(ic)

            if ic_values:
                regime_ic_results.append({
                    "regime": regime,
                    "factor": factor_name,
                    "mean_ic": np.mean(ic_values),
                    "std_ic": np.std(ic_values),
                    "n_obs": len(ic_values),
                })

    return pd.DataFrame(regime_ic_results)


def calculate_attribution(
    target_weights: pd.DataFrame,
    returns: pd.DataFrame,
    factor_scores_long: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate performance attribution with proper factor contributions and residual.

    Attribution logic using factor regression:
    - For each date, regress portfolio returns against factor exposures
    - Factor contribution = factor_loading × factor_return
    - Residual = actual_portfolio_return - sum(factor_contributions)

    Args:
        target_weights: DataFrame(Date × Permno) with portfolio weights
        returns: DataFrame(Date × Permno) with asset returns
        factor_scores_long: Long-form DataFrame with (date, permno, factor1, factor2, ...)

    Returns:
        DataFrame with attribution by factor and residual
    """
    # Convert permno to string in factor_scores_long to match target_weights
    factor_scores_long = factor_scores_long.copy()
    factor_scores_long['permno'] = factor_scores_long['permno'].astype(str)

    # Align indices
    common_dates = target_weights.index.intersection(returns.index)
    target_weights = target_weights.loc[common_dates]
    returns = returns.loc[common_dates]

    # Get factor columns
    factor_cols = [col for col in factor_scores_long.columns if col not in ["date", "permno"]]

    attribution_results = []

    print(f"Computing attribution for {len(common_dates)} dates...")

    for date in common_dates:
        weight_row = target_weights.loc[date]
        return_row = returns.loc[date]

        # Calculate actual portfolio return
        common_permnos = weight_row.index.intersection(return_row.index)
        weights = weight_row[common_permnos].fillna(0.0)
        rets = return_row[common_permnos].fillna(0.0)
        portfolio_return = (weights * rets).sum()

        # Get factor exposures for this date
        date_factors = factor_scores_long[factor_scores_long["date"] == pd.Timestamp(date)]

        if len(date_factors) == 0:
            # No factor data for this date
            attr_row = {
                "date": date,
                "portfolio_return": portfolio_return,
                "residual": portfolio_return,
            }
            for factor in factor_cols:
                attr_row[f"{factor}_contribution"] = 0.0
            attribution_results.append(attr_row)
            continue

        # Build factor exposure matrix for portfolio holdings
        factor_exposures = {}
        for factor in factor_cols:
            factor_exp = date_factors.set_index("permno")[factor]
            aligned_exp = factor_exp.reindex(common_permnos).fillna(0.0)
            factor_exposures[factor] = aligned_exp

        # Calculate portfolio-level factor exposures (weighted average)
        portfolio_factor_exposures = {}
        for factor, exposures in factor_exposures.items():
            portfolio_factor_exposures[factor] = (weights * exposures).sum()

        # Calculate factor returns (cross-sectional regression of returns on factor exposures)
        # Returns = beta_1 * factor_1 + beta_2 * factor_2 + ... + alpha + residual
        X = np.column_stack([factor_exposures[f].values for f in factor_cols])
        y = rets.values

        # Remove NaN rows
        valid_mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        if valid_mask.sum() < len(factor_cols) + 1:
            # Not enough data for regression
            attr_row = {
                "date": date,
                "portfolio_return": portfolio_return,
                "residual": portfolio_return,
            }
            for factor in factor_cols:
                attr_row[f"{factor}_contribution"] = 0.0
            attribution_results.append(attr_row)
            continue

        X_valid = X[valid_mask]
        y_valid = y[valid_mask]

        # Add intercept column
        X_with_intercept = np.column_stack([np.ones(len(X_valid)), X_valid])

        # Fit regression using numpy least squares
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y_valid, rcond=None)
            intercept = coeffs[0]
            factor_returns = coeffs[1:]
        except np.linalg.LinAlgError:
            # Singular matrix, can't compute regression
            attr_row = {
                "date": date,
                "portfolio_return": portfolio_return,
                "residual": portfolio_return,
            }
            for factor in factor_cols:
                attr_row[f"{factor}_contribution"] = 0.0
            attribution_results.append(attr_row)
            continue

        # Factor contributions = portfolio_factor_exposure × factor_return (beta)
        factor_contributions = {}
        for i, factor in enumerate(factor_cols):
            factor_return = factor_returns[i]
            factor_contribution = portfolio_factor_exposures[factor] * factor_return
            factor_contributions[f"{factor}_contribution"] = factor_contribution

        # Calculate residual: unexplained return after accounting for factor contributions
        total_factor_contribution = sum(factor_contributions.values())
        residual = portfolio_return - total_factor_contribution

        # Build attribution row
        attr_row = {
            "date": date,
            "portfolio_return": portfolio_return,
            "residual": residual,
            **factor_contributions,
        }

        attribution_results.append(attr_row)

    attr_df = pd.DataFrame(attribution_results)
    if "date" in attr_df.columns:
        attr_df = attr_df.set_index("date")

    return attr_df


def generate_behavior_ledger(
    target_weights: pd.DataFrame,
    regime_history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate behavior ledger tracking weight changes and regime transitions.

    Returns:
        DataFrame with behavior events
    """
    # Align indices
    common_dates = target_weights.index.intersection(regime_history.index)
    target_weights = target_weights.loc[common_dates].sort_index()
    regime_history = regime_history.loc[common_dates].sort_index()

    behavior_events = []

    for i in range(1, len(common_dates)):
        date = common_dates[i]
        prev_date = common_dates[i - 1]

        # Check for regime change
        current_regime = regime_history.loc[date, "governor_state"]
        prev_regime = regime_history.loc[prev_date, "governor_state"]
        regime_changed = current_regime != prev_regime

        # Calculate weight changes
        current_weights = target_weights.loc[date]
        prev_weights = target_weights.loc[prev_date]
        weight_changes = (current_weights - prev_weights).abs().sum()

        behavior_events.append({
            "date": date,
            "regime": current_regime,
            "regime_changed": regime_changed,
            "total_weight_change": weight_changes,
            "n_positions": (current_weights > 0).sum(),
        })

    return pd.DataFrame(behavior_events)


def generate_summary_stats(
    factor_ic: pd.DataFrame,
    regime_ic: pd.DataFrame,
    attribution: pd.DataFrame,
) -> dict:
    """
    Generate summary statistics including IC stability, regime hit-rate,
    contribution R², and IC consistency.

    Returns:
        Dictionary with summary statistics
    """
    summary = {}

    # IC stability: mean and std of IC across time (now using long-format data)
    if not factor_ic.empty and "ic" in factor_ic.columns and "factor" in factor_ic.columns:
        # Group by factor and calculate mean/std for each factor
        factor_stats = factor_ic.groupby("factor")["ic"].agg(["mean", "std"])

        summary["ic_stability"] = {
            "mean_ic": float(factor_stats["mean"].mean()),
            "std_ic": float(factor_stats["std"].mean()),
            "ic_consistency": float((factor_stats["mean"] / factor_stats["std"]).mean()) if factor_stats["std"].mean() > 0 else 0.0,
        }

    # Regime hit-rate: proportion of positive IC by regime
    if not regime_ic.empty:
        regime_hit_rates = {}
        for regime in regime_ic["regime"].unique():
            regime_data = regime_ic[regime_ic["regime"] == regime]
            hit_rate = (regime_data["mean_ic"] > 0).sum() / len(regime_data) if len(regime_data) > 0 else 0.0
            regime_hit_rates[str(regime)] = float(hit_rate)
        summary["regime_hit_rate"] = regime_hit_rates

    # Contribution R²: explained variance of portfolio returns
    if not attribution.empty and "portfolio_return" in attribution.columns:
        portfolio_returns = attribution["portfolio_return"]
        contribution_cols = [col for col in attribution.columns if col.endswith("_contribution")]

        if contribution_cols:
            total_contributions = attribution[contribution_cols].sum(axis=1)
            if portfolio_returns.std() > 0:
                r_squared = 1 - ((portfolio_returns - total_contributions) ** 2).sum() / ((portfolio_returns - portfolio_returns.mean()) ** 2).sum()
                summary["contribution_r_squared"] = float(r_squared)
            else:
                summary["contribution_r_squared"] = 0.0

    # IC consistency: information ratio (mean IC / std IC) by factor
    if not factor_ic.empty and "ic" in factor_ic.columns and "factor" in factor_ic.columns:
        ic_consistency = {}
        for factor_name in factor_ic["factor"].unique():
            factor_data = factor_ic[factor_ic["factor"] == factor_name]["ic"].dropna()
            if len(factor_data) > 0 and factor_data.std() > 0:
                ic_consistency[factor_name] = float(factor_data.mean() / factor_data.std())
            else:
                ic_consistency[factor_name] = 0.0
        summary["ic_consistency_by_factor"] = ic_consistency

    return summary


def run_attribution_analysis(
    factor_scores_wide: dict[str, pd.DataFrame],
    returns: pd.DataFrame,
    target_weights: pd.DataFrame,
    regime_history: pd.DataFrame,
    factor_scores_long: pd.DataFrame,
    output_dir: Path,
) -> None:
    """
    Run full attribution analysis pipeline and export results.

    Exports:
        - phase34_factor_ic.csv
        - phase34_regime_ic.csv
        - phase34_attribution.csv (with residual column)
        - phase34_behavior_ledger.csv
        - phase34_summary.json
    """
    print("\nCalculating factor IC...")
    factor_ic = calculate_factor_ic(factor_scores_wide, returns)

    print("Calculating regime IC...")
    regime_ic = calculate_regime_ic(factor_scores_wide, returns, regime_history)

    print("Calculating attribution...")
    attribution = calculate_attribution(target_weights, returns, factor_scores_long)

    print("Generating behavior ledger...")
    behavior_ledger = generate_behavior_ledger(target_weights, regime_history)

    print("Generating summary statistics...")
    summary_stats = generate_summary_stats(factor_ic, regime_ic, attribution)

    # Export all results with atomic writes
    print("\nExporting results...")
    _atomic_csv_write(factor_ic, output_dir / "phase34_factor_ic.csv", index=False)
    print(f"  - {output_dir / 'phase34_factor_ic.csv'}")

    _atomic_csv_write(regime_ic, output_dir / "phase34_regime_ic.csv", index=False)
    print(f"  - {output_dir / 'phase34_regime_ic.csv'}")

    _atomic_csv_write(attribution, output_dir / "phase34_attribution.csv", index=True)  # Date index intentional
    print(f"  - {output_dir / 'phase34_attribution.csv'}")

    _atomic_csv_write(behavior_ledger, output_dir / "phase34_behavior_ledger.csv", index=False)
    print(f"  - {output_dir / 'phase34_behavior_ledger.csv'}")

    _atomic_json_write(summary_stats, output_dir / "phase34_summary.json")
    print(f"  - {output_dir / 'phase34_summary.json'}")

    print("\nAttribution analysis complete.")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Phase 34 Attribution Report: Factor IC, Regime Analysis, and Performance Attribution"
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Inclusive start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Inclusive end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--factor-scores-path",
        default=str(DEFAULT_FACTOR_SCORES_PATH),
        help=f"Path to factor scores parquet (default: {DEFAULT_FACTOR_SCORES_PATH})",
    )
    parser.add_argument(
        "--prices-tri-path",
        default=str(DEFAULT_PRICES_TRI_PATH),
        help=f"Path to prices TRI parquet (default: {DEFAULT_PRICES_TRI_PATH})",
    )
    parser.add_argument(
        "--target-weights-path",
        default=str(DEFAULT_TARGET_WEIGHTS_PATH),
        help=f"Path to target weights parquet (default: {DEFAULT_TARGET_WEIGHTS_PATH})",
    )
    parser.add_argument(
        "--regime-history-path",
        default=str(DEFAULT_REGIME_HISTORY_PATH),
        help=f"Path to regime history CSV (default: {DEFAULT_REGIME_HISTORY_PATH})",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse dates
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)

    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    # Resolve paths
    factor_scores_path = Path(args.factor_scores_path)
    prices_tri_path = Path(args.prices_tri_path)
    target_weights_path = Path(args.target_weights_path)
    regime_history_path = Path(args.regime_history_path)
    output_dir = Path(args.output_dir)

    # Load data
    print("=" * 78)
    print("PHASE 34 ATTRIBUTION REPORT")
    print("=" * 78)

    factor_scores_wide, returns_wide, target_weights, factor_scores_long = load_backtest_data(
        factor_scores_path=factor_scores_path,
        prices_tri_path=prices_tri_path,
        target_weights_path=target_weights_path,
        start=start,
        end=end,
    )

    regime_history = load_regime_history(
        regime_history_path=regime_history_path,
        start=start,
        end=end,
    )

    # Run analysis
    run_attribution_analysis(
        factor_scores_wide=factor_scores_wide,
        returns=returns_wide,
        target_weights=target_weights,
        regime_history=regime_history,
        factor_scores_long=factor_scores_long,
        output_dir=output_dir,
    )

    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
