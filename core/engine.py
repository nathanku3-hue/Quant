"""
Terminal Zero — Vectorized Simulation Kernel

The "Source of Truth" for PnL calculation.
Implements the three Invisible Walls:
  D-04: shift(1) — no look-ahead bias
  D-05: Turnover tax — transaction cost deduction
  D-08: Matrix alignment — engine accepts pre-pivoted wide DataFrames
"""

import pandas as pd
import numpy as np


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
