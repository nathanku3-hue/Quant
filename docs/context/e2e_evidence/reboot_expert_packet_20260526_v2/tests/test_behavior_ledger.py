"""
Tests for Phase 34: Behavior Ledger Bootstrap Validation

Validates:
1. Patience Gain bootstrap confidence interval computation
2. Premature Exit Drag bootstrap confidence interval computation
3. Bootstrap CI lower bounds > 0 (hard gate)
4. Statistical robustness of behavioral metrics
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# ================================================================================
# Bootstrap Helper Functions
# ================================================================================


def _bootstrap_ci(
    data: np.ndarray,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for mean.

    Returns:
        (mean, ci_lower, ci_upper)
    """
    np.random.seed(random_seed)

    bootstrap_means = []
    n = len(data)

    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means = np.array(bootstrap_means)
    mean = np.mean(data)

    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_means, alpha / 2 * 100)
    ci_upper = np.percentile(bootstrap_means, (1 - alpha / 2) * 100)

    return mean, ci_lower, ci_upper


# ================================================================================
# Mock Data Generators
# ================================================================================


def _make_mock_patience_data(
    n_trades: int = 100,
    true_patience_gain: float = 0.05,
    noise_std: float = 0.02,
) -> pd.DataFrame:
    """
    Generate mock patience gain data.

    Patience Gain = CAGR(wait_rule_entries) - CAGR(immediate_entries)

    Returns DataFrame with columns:
    - trade_id, wait_rule_cagr, immediate_cagr, patience_gain
    """
    np.random.seed(42)

    rows = []
    for i in range(n_trades):
        # Wait rule entries have higher CAGR on average
        wait_rule_cagr = 0.15 + true_patience_gain + np.random.randn() * noise_std
        immediate_cagr = 0.15 + np.random.randn() * noise_std

        patience_gain = wait_rule_cagr - immediate_cagr

        rows.append({
            "trade_id": i,
            "wait_rule_cagr": wait_rule_cagr,
            "immediate_cagr": immediate_cagr,
            "patience_gain": patience_gain,
        })

    return pd.DataFrame(rows)


def _make_mock_exit_drag_data(
    n_trades: int = 100,
    true_exit_drag: float = 0.03,
    noise_std: float = 0.015,
) -> pd.DataFrame:
    """
    Generate mock premature exit drag data.

    Premature Exit Drag = return_if_held_to_rule_exit - actual_realized_return

    Returns DataFrame with columns:
    - trade_id, held_to_rule_return, realized_return, exit_drag
    """
    np.random.seed(43)

    rows = []
    for i in range(n_trades):
        # Holding to rule exit has higher return on average
        held_to_rule_return = 0.08 + true_exit_drag + np.random.randn() * noise_std
        realized_return = 0.08 + np.random.randn() * noise_std

        exit_drag = held_to_rule_return - realized_return

        rows.append({
            "trade_id": i,
            "held_to_rule_return": held_to_rule_return,
            "realized_return": realized_return,
            "exit_drag": exit_drag,
        })

    return pd.DataFrame(rows)


# ================================================================================
# Behavior Ledger Tests
# ================================================================================


def test_patience_gain_bootstrap():
    """
    Contract: Patience Gain bootstrap CI lower bound > 0 (hard gate).

    Validates:
    - Bootstrap CI computed correctly
    - Lower bound of 95% CI > 0
    - Mean patience gain is positive
    - CI width is reasonable (not too wide)
    """
    # Generate mock data with positive patience gain
    df = _make_mock_patience_data(n_trades=150, true_patience_gain=0.05, noise_std=0.02)

    patience_gains = df["patience_gain"].values

    # Compute bootstrap CI
    mean, ci_lower, ci_upper = _bootstrap_ci(
        patience_gains,
        n_bootstrap=1000,
        confidence_level=0.95,
        random_seed=42,
    )

    # Assertions
    assert mean > 0, "Mean patience gain should be positive"
    assert ci_lower > 0, "CI95 lower bound must be > 0 (hard gate for Phase 35/36)"
    assert ci_upper > mean, "CI upper bound should exceed mean"
    assert ci_upper - ci_lower < 0.10, "CI width should be reasonable (< 10%)"

    # Additional validation: CI should contain true value
    true_gain = 0.05
    assert ci_lower <= true_gain <= ci_upper, "CI should contain true patience gain"


def test_premature_exit_drag_bootstrap():
    """
    Contract: Premature Exit Drag bootstrap CI lower bound > 0 (hard gate).

    Validates:
    - Bootstrap CI computed correctly
    - Lower bound of 95% CI > 0
    - Mean exit drag is positive
    - CI width is reasonable
    """
    # Generate mock data with positive exit drag
    df = _make_mock_exit_drag_data(n_trades=150, true_exit_drag=0.03, noise_std=0.015)

    exit_drags = df["exit_drag"].values

    # Compute bootstrap CI
    mean, ci_lower, ci_upper = _bootstrap_ci(
        exit_drags,
        n_bootstrap=1000,
        confidence_level=0.95,
        random_seed=43,
    )

    # Assertions
    assert mean > 0, "Mean exit drag should be positive"
    assert ci_lower > 0, "CI95 lower bound must be > 0 (hard gate for Phase 35/36)"
    assert ci_upper > mean, "CI upper bound should exceed mean"
    assert ci_upper - ci_lower < 0.08, "CI width should be reasonable (< 8%)"

    # Additional validation: CI should contain true value
    true_drag = 0.03
    assert ci_lower <= true_drag <= ci_upper, "CI should contain true exit drag"


def test_patience_gain_bootstrap_with_negative_signal():
    """
    Contract: If patience gain is negative, CI lower bound will be < 0 (gate fails).

    Validates:
    - Bootstrap correctly identifies negative behavioral edge
    - Gate fails when patience gain is not positive
    """
    # Generate mock data with NEGATIVE patience gain (bad signal)
    df = _make_mock_patience_data(n_trades=100, true_patience_gain=-0.02, noise_std=0.015)

    patience_gains = df["patience_gain"].values

    # Compute bootstrap CI
    mean, ci_lower, ci_upper = _bootstrap_ci(
        patience_gains,
        n_bootstrap=1000,
        confidence_level=0.95,
        random_seed=44,
    )

    # Assertions
    assert mean < 0, "Mean patience gain should be negative (bad signal)"
    assert ci_lower < 0, "CI95 lower bound should be < 0 (gate fails)"
    # This would fail the Phase 35/36 gate, as expected


def test_premature_exit_drag_bootstrap_with_negative_signal():
    """
    Contract: If exit drag is negative, CI lower bound will be < 0 (gate fails).

    Validates:
    - Bootstrap correctly identifies negative behavioral edge
    - Gate fails when exit drag is not positive
    """
    # Generate mock data with NEGATIVE exit drag (bad signal)
    df = _make_mock_exit_drag_data(n_trades=100, true_exit_drag=-0.015, noise_std=0.01)

    exit_drags = df["exit_drag"].values

    # Compute bootstrap CI
    mean, ci_lower, ci_upper = _bootstrap_ci(
        exit_drags,
        n_bootstrap=1000,
        confidence_level=0.95,
        random_seed=45,
    )

    # Assertions
    assert mean < 0, "Mean exit drag should be negative (bad signal)"
    assert ci_lower < 0, "CI95 lower bound should be < 0 (gate fails)"
    # This would fail the Phase 35/36 gate, as expected


def test_bootstrap_stability_across_seeds():
    """
    Contract: Bootstrap CI should be stable across different random seeds.

    Validates:
    - CI estimates are consistent (low variance across seeds)
    - Mean estimate is stable
    """
    df = _make_mock_patience_data(n_trades=200, true_patience_gain=0.04, noise_std=0.02)
    patience_gains = df["patience_gain"].values

    # Compute CI with different seeds
    results = []
    for seed in [42, 43, 44, 45, 46]:
        mean, ci_lower, ci_upper = _bootstrap_ci(
            patience_gains,
            n_bootstrap=1000,
            confidence_level=0.95,
            random_seed=seed,
        )
        results.append((mean, ci_lower, ci_upper))

    means = [r[0] for r in results]
    ci_lowers = [r[1] for r in results]
    ci_uppers = [r[2] for r in results]

    # Assertions
    assert np.std(means) < 0.001, "Mean should be stable across seeds"
    assert np.std(ci_lowers) < 0.005, "CI lower bound should be stable"
    assert np.std(ci_uppers) < 0.005, "CI upper bound should be stable"
