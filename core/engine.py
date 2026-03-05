"""
Terminal Zero — Vectorized Simulation Kernel

The "Source of Truth" for PnL calculation.
Implements the three Invisible Walls:
  D-04: shift(1) — no look-ahead bias
  D-05: Turnover tax — transaction cost deduction
  D-08: Matrix alignment — engine accepts pre-pivoted wide DataFrames

Phase 33A Step 2: Baseline Export Wiring
- Added run_backtest_with_baseline_export() for drift detection
- Extracts rebalance schedule from target weights
- Computes data snapshot hash from returns DataFrame
- Saves baseline to registry with deterministic ID
"""

from __future__ import annotations

import copy
import hashlib
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from core.baseline_registry import BacktestBaseline, BaselineRegistry


def run_simulation(
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    cost_bps: float = 0.0010,
    strict_missing_returns: bool = False,
) -> pd.DataFrame:
    """
    Core Vectorized Engine.

    Args:
        target_weights: DataFrame (Index=Date, Cols=Permno) — The "Intent"
                        Values should sum to <= 1.0 per row.
        returns_df:     DataFrame (Index=Date, Cols=Permno) — The "Reality"
                        Pre-computed total returns from ETL.
        cost_bps:       Transaction cost in decimal (0.0010 = 10 basis points).
        strict_missing_returns:
                        If True, raise when any executed (t->t+1) exposure has
                        a missing aligned return cell.

    Returns:
        DataFrame with columns: gross_ret, net_ret, turnover, cost
    """
    # ── WALL 1: The Law of Time (D-04) ──────────────────────────────────────
    # Execute TOMORROW (t+1) based on TODAY'S (t) signal.
    # fillna(0) → assume cash before start date.
    executed_weights = target_weights.shift(1).fillna(0.0)

    # ── WALL 2: Matrix Alignment (D-08) ─────────────────────────────────────
    # Ensure returns matrix matches weights matrix perfectly.
    # Missing assets → 0.0 (cash equivalent) to prevent NaN explosion.
    aligned_returns = (
        returns_df
        .reindex(index=executed_weights.index, columns=executed_weights.columns)
    )
    if strict_missing_returns:
        executed_exposure = executed_weights.ne(0.0)
        missing_executed = int((aligned_returns.isna() & executed_exposure).sum().sum())
        if missing_executed > 0:
            raise RuntimeError(
                f"Missing {missing_executed:,} return cells on executed exposures."
            )
    aligned_returns = aligned_returns.fillna(0.0)

    # ── Gross Return ────────────────────────────────────────────────────────
    # Element-wise multiplication (Weight × Return), summed across all assets.
    gross_ret = (executed_weights * aligned_returns).sum(axis=1)

    # ── WALL 3: The Turnover Tax (D-05) ─────────────────────────────────────
    # Absolute change in allocation → cost proportional to trading activity.
    turnover = executed_weights.diff().abs().sum(axis=1).fillna(0.0)
    costs = turnover * cost_bps

    # ── Net Result ──────────────────────────────────────────────────────────
    net_ret = gross_ret - costs

    return pd.DataFrame({
        "gross_ret": gross_ret,
        "net_ret": net_ret,
        "turnover": turnover,
        "cost": costs,
    })


def extract_rebalance_dates(target_weights: pd.DataFrame) -> list[datetime]:
    """
    Extract rebalance schedule from target weights DataFrame.

    Rebalance dates are identified as rows where allocation changed
    from previous row (excluding first row which is initial allocation).

    Args:
        target_weights: DataFrame with DatetimeIndex and target allocations

    Returns:
        List of datetime objects representing rebalance dates
    """
    if target_weights.empty:
        return []

    # First date is always a "rebalance" (initial allocation)
    rebalance_dates = [target_weights.index[0].to_pydatetime()]

    # Find dates where allocation changed
    for i in range(1, len(target_weights)):
        prev_row = target_weights.iloc[i - 1]
        curr_row = target_weights.iloc[i]

        # Check if any weight changed (tolerance for floating point comparison)
        if not np.allclose(prev_row.values, curr_row.values, atol=1e-6):
            rebalance_dates.append(target_weights.index[i].to_pydatetime())

    return rebalance_dates


def compute_data_snapshot_hash(returns_df: pd.DataFrame) -> str:
    """
    Compute deterministic hash of returns DataFrame for baseline identity.

    Uses SHA256 of DataFrame shape + index + column names + sample values
    to create a stable identifier for the data snapshot.

    Args:
        returns_df: DataFrame with returns data

    Returns:
        SHA256 hex string (full 64-char hash)
    """
    # Build fingerprint from DataFrame metadata
    fingerprint_parts = [
        f"shape:{returns_df.shape[0]}x{returns_df.shape[1]}",
        f"index_min:{returns_df.index.min()}",
        f"index_max:{returns_df.index.max()}",
        f"columns:{sorted(map(str, returns_df.columns))}",
    ]

    # Add sample of actual data (first/last row means) for content verification
    if not returns_df.empty:
        first_mean = returns_df.iloc[0].mean()
        last_mean = returns_df.iloc[-1].mean()
        fingerprint_parts.append(f"first_mean:{first_mean:.10f}")
        fingerprint_parts.append(f"last_mean:{last_mean:.10f}")

    fingerprint = "|".join(fingerprint_parts)
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def run_backtest_with_baseline_export(
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    strategy_config: dict[str, Any],
    *,
    strategy_name: str = "custom_strategy",
    strategy_version: str = "1.0.0",
    calendar_version: str = "NYSE_2026",
    run_environment: str = "dev",
    cost_bps: float = 0.0010,
    strict_missing_returns: bool = False,
    save_baseline: bool = True,
) -> tuple[pd.DataFrame, BacktestBaseline]:
    """
    Run backtest and export baseline for drift detection.

    Phase 33A Step 2: Wires baseline export to backtest execution path.
    Creates immutable baseline identity with deterministic ID binding.

    Args:
        target_weights: DataFrame (Date index × permno columns) with target allocations
        returns_df: DataFrame (Date index × permno columns) with returns
        strategy_config: Dict of strategy parameters (will be hashed for baseline ID)
        strategy_name: Human-readable strategy name
        strategy_version: Semantic version (e.g., "1.2.0")
        calendar_version: Trading calendar identifier (e.g., "NYSE_2026")
        run_environment: "dev" | "staging" | "prod"
        cost_bps: Transaction cost in decimal (0.0010 = 10 bps)
        strict_missing_returns: If True, raise on missing returns for executed positions
        save_baseline: If True, persist baseline to registry (default True)

    Returns:
        results: DataFrame with gross_ret, net_ret, turnover, cost
        baseline: BacktestBaseline with expected_allocation for drift comparison

    Example:
        >>> results, baseline = run_backtest_with_baseline_export(
        ...     target_weights=weights_df,
        ...     returns_df=returns_df,
        ...     strategy_config={"momentum_lookback": 20, "entry": 0.5},
        ...     strategy_name="momentum_quality",
        ...     strategy_version="1.0.0",
        ... )
        >>> print(f"Baseline ID: {baseline.baseline_id}")
        >>> print(f"Sharpe: {results['net_ret'].mean() / results['net_ret'].std() * np.sqrt(252):.2f}")
    """
    # Run core simulation
    results = run_simulation(
        target_weights=target_weights,
        returns_df=returns_df,
        cost_bps=cost_bps,
        strict_missing_returns=strict_missing_returns,
    )

    # Compute baseline identity components
    config_hash = BacktestBaseline.compute_config_hash(strategy_config)
    data_snapshot_hash = compute_data_snapshot_hash(returns_df)

    baseline_id = BacktestBaseline.compute_baseline_id(
        config_hash=config_hash,
        data_snapshot_hash=data_snapshot_hash,
        calendar_version=calendar_version,
        strategy_version=strategy_version,
    )

    # Extract rebalance schedule
    rebalance_schedule = extract_rebalance_dates(target_weights)

    # Create baseline artifact
    baseline = BacktestBaseline(
        baseline_id=baseline_id,
        strategy_name=strategy_name,
        strategy_version=strategy_version,
        config_hash=config_hash,
        data_snapshot_hash=data_snapshot_hash,
        calendar_version=calendar_version,
        execution_timestamp=datetime.now(),
        run_environment=run_environment,
        expected_allocation=target_weights.copy(),  # Deep copy for immutability
        rebalance_schedule=rebalance_schedule,
        full_config=copy.deepcopy(strategy_config),  # Deep copy for immutability (handles nested objects)
    )

    # Persist to baseline registry
    if save_baseline:
        registry = BaselineRegistry()
        registry.save_baseline(baseline)

    return results, baseline
