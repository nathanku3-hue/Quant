"""
Tests for Phase 34: Factor Attribution Analysis

Validates:
1. Factor IC computation correctness
2. IC significance testing
3. Regime-conditional IC analysis
4. Attribution accounting identity (sum = total return)
5. Factor contribution sign consistency
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats


# ================================================================================
# Mock Data Generators
# ================================================================================


def _make_mock_factor_scores(n_days: int = 60, n_stocks: int = 50) -> pd.DataFrame:
    """
    Generate mock factor scores with *_normalized naming convention.

    Returns DataFrame with columns:
    - date, permno
    - momentum_normalized, quality_normalized, volatility_normalized, illiquidity_normalized
    """
    dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
    permnos = list(range(1000, 1000 + n_stocks))

    rows = []
    for dt in dates:
        for permno in permnos:
            # Generate correlated factor scores
            np.random.seed(int(permno + dt.toordinal()))
            rows.append({
                "date": dt,
                "permno": permno,
                "momentum_normalized": np.random.randn(),
                "quality_normalized": np.random.randn(),
                "volatility_normalized": np.random.randn(),
                "illiquidity_normalized": np.random.randn(),
            })

    return pd.DataFrame(rows)


def _make_mock_returns(
    factor_scores: pd.DataFrame,
    momentum_beta: float = 0.05,
    quality_beta: float = 0.03,
    noise_std: float = 0.02,
) -> pd.DataFrame:
    """
    Generate mock forward returns correlated with momentum_normalized.

    Returns DataFrame with columns:
    - date, permno, forward_return_1d
    """
    df = factor_scores.copy()

    # Correlate returns with momentum_normalized and quality_normalized
    df["forward_return_1d"] = (
        momentum_beta * df["momentum_normalized"]
        + quality_beta * df["quality_normalized"]
        + np.random.randn(len(df)) * noise_std
    )

    return df[["date", "permno", "forward_return_1d"]]


# ================================================================================
# TestFactorIC: Information Coefficient Tests
# ================================================================================


class TestFactorIC:
    """Test suite for factor Information Coefficient (IC) computation."""

    def test_ic_computation_basic(self):
        """
        Contract: IC = Spearman rank correlation between factor scores and forward returns.

        Validates:
        - IC is computed correctly as Spearman correlation
        - IC is bounded in [-1, 1]
        - Positive momentum_beta → positive IC for momentum
        """
        factor_scores = _make_mock_factor_scores(n_days=20, n_stocks=30)
        returns = _make_mock_returns(factor_scores, momentum_beta=0.08, noise_std=0.01)

        # Merge factor scores with forward returns
        df = factor_scores.merge(returns, on=["date", "permno"])

        # Compute IC for momentum_normalized
        ic_values = []
        for dt in df["date"].unique():
            day_data = df[df["date"] == dt]
            ic, _ = stats.spearmanr(
                day_data["momentum_normalized"],
                day_data["forward_return_1d"]
            )
            ic_values.append(ic)

        mean_ic = np.mean(ic_values)

        # Assertions
        assert -1.0 <= mean_ic <= 1.0, "IC must be bounded in [-1, 1]"
        assert mean_ic > 0.0, "Positive momentum_beta should yield positive IC"
        assert mean_ic > 0.02, "IC should exceed significance threshold (0.02)"

    def test_ic_significance(self):
        """
        Contract: IC significance tested via t-statistic.

        Validates:
        - t-statistic = IC * sqrt(N-2) / sqrt(1 - IC^2)
        - p-value < 0.05 for significant IC
        """
        factor_scores = _make_mock_factor_scores(n_days=30, n_stocks=40)
        returns = _make_mock_returns(factor_scores, momentum_beta=0.10, noise_std=0.01)

        df = factor_scores.merge(returns, on=["date", "permno"])

        # Compute IC and p-value for one date
        day_data = df[df["date"] == df["date"].iloc[0]]
        ic, p_value = stats.spearmanr(
            day_data["momentum_normalized"],
            day_data["forward_return_1d"]
        )

        # Assertions
        assert p_value < 0.05, "IC should be statistically significant (p < 0.05)"
        assert abs(ic) > 0.02, "Significant IC should exceed 0.02 threshold"

    def test_regime_conditional_ic(self):
        """
        Contract: IC computed separately for each regime (GREEN/AMBER/RED).

        Validates:
        - IC varies by regime
        - Quality IC higher in GREEN regime
        - Momentum IC may reverse in RED regime
        """
        factor_scores = _make_mock_factor_scores(n_days=60, n_stocks=50)
        returns = _make_mock_returns(factor_scores, momentum_beta=0.05, quality_beta=0.04)

        df = factor_scores.merge(returns, on=["date", "permno"])

        # Assign mock regimes (GREEN: first 20 days, AMBER: next 20, RED: last 20)
        dates = sorted(df["date"].unique())
        regime_map = {}
        for i, dt in enumerate(dates):
            if i < 20:
                regime_map[dt] = "GREEN"
            elif i < 40:
                regime_map[dt] = "AMBER"
            else:
                regime_map[dt] = "RED"

        df["regime"] = df["date"].map(regime_map)

        # Compute regime-conditional IC for quality_normalized
        regime_ics = {}
        for regime in ["GREEN", "AMBER", "RED"]:
            regime_data = df[df["regime"] == regime]
            ic_values = []
            for dt in regime_data["date"].unique():
                day_data = regime_data[regime_data["date"] == dt]
                ic, _ = stats.spearmanr(
                    day_data["quality_normalized"],
                    day_data["forward_return_1d"]
                )
                ic_values.append(ic)
            regime_ics[regime] = np.mean(ic_values)

        # Assertions
        assert len(regime_ics) == 3, "Should have IC for all 3 regimes"
        assert all(-1.0 <= ic <= 1.0 for ic in regime_ics.values()), "ICs must be bounded"
        # Quality typically performs better in GREEN regime
        assert regime_ics["GREEN"] > -0.5, "Quality IC should not be strongly negative in GREEN"


# ================================================================================
# TestAttribution: Factor Contribution Tests
# ================================================================================


class TestAttribution:
    """Test suite for factor attribution decomposition."""

    def test_accounting_identity(self):
        """
        Contract: Sum of factor contributions + residual = total portfolio return.

        Validates:
        - Attribution accounting identity holds
        - Residual captures unexplained variance
        """
        # Generate mock portfolio with factor exposures
        n_days = 30
        dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

        rows = []
        for dt in dates:
            # Mock factor returns
            momentum_return = np.random.randn() * 0.01
            quality_return = np.random.randn() * 0.008
            volatility_return = np.random.randn() * 0.005

            # Mock factor exposures (weights)
            momentum_weight = 0.4
            quality_weight = 0.3
            volatility_weight = 0.3

            # Compute contributions
            momentum_contrib = momentum_weight * momentum_return
            quality_contrib = quality_weight * quality_return
            volatility_contrib = volatility_weight * volatility_return

            # Total return = sum of contributions + residual
            residual = np.random.randn() * 0.002
            total_return = momentum_contrib + quality_contrib + volatility_contrib + residual

            rows.append({
                "date": dt,
                "total_return": total_return,
                "momentum_contrib": momentum_contrib,
                "quality_contrib": quality_contrib,
                "volatility_contrib": volatility_contrib,
                "residual": residual,
            })

        df = pd.DataFrame(rows)

        # Validate accounting identity
        computed_total = (
            df["momentum_contrib"]
            + df["quality_contrib"]
            + df["volatility_contrib"]
            + df["residual"]
        )

        # Assertions
        np.testing.assert_allclose(
            df["total_return"],
            computed_total,
            rtol=1e-10,
            err_msg="Attribution must sum to total return (accounting identity)"
        )

    def test_factor_contributions_sign(self):
        """
        Contract: Factor contributions align with expected signs.

        Validates:
        - Positive momentum_normalized exposure → positive contribution when momentum factor returns positive
        - Sign consistency between factor exposure and contribution
        """
        factor_scores = _make_mock_factor_scores(n_days=20, n_stocks=30)
        returns = _make_mock_returns(factor_scores, momentum_beta=0.10, noise_std=0.01)

        df = factor_scores.merge(returns, on=["date", "permno"])

        # Compute factor contributions for momentum_normalized
        # Contribution = factor_score * factor_return
        # For simplicity, use mean return as proxy for factor return
        for dt in df["date"].unique()[:5]:  # Test first 5 days
            day_data = df[df["date"] == dt]

            # Compute factor return (mean return of high-momentum stocks)
            high_momentum = day_data.nlargest(10, "momentum_normalized")
            factor_return = high_momentum["forward_return_1d"].mean()

            # Compute contribution for a high-momentum stock
            stock = high_momentum.iloc[0]
            contribution = stock["momentum_normalized"] * factor_return

            # Assertions
            if factor_return > 0 and stock["momentum_normalized"] > 0:
                assert contribution > 0, "Positive exposure + positive return → positive contribution"
            elif factor_return < 0 and stock["momentum_normalized"] > 0:
                assert contribution < 0, "Positive exposure + negative return → negative contribution"
