"""
Factor Attribution Engine

Provides IC analysis, regime-conditional IC, rolling IC windows,
factor returns computation, and portfolio return decomposition with residual tracking.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


@dataclass
class FactorICResult:
    """Information Coefficient result for a single factor."""
    factor_name: str
    ic: float
    p_value: float
    n_observations: int
    timestamp: pd.Timestamp


@dataclass
class RegimeICResult:
    """Regime-conditional IC results."""
    factor_name: str
    green_ic: float
    amber_ic: float
    red_ic: float
    green_pval: float
    amber_pval: float
    red_pval: float
    green_n: int
    amber_n: int
    red_n: int


@dataclass
class AttributionResult:
    """Portfolio return attribution with residual."""
    total_return: float
    factor_contributions: Dict[str, float]
    residual: float
    timestamp: pd.Timestamp

    def validate(self) -> bool:
        """Check accounting identity: total = sum(contributions) + residual."""
        computed_total = sum(self.factor_contributions.values()) + self.residual
        return np.isclose(computed_total, self.total_return, atol=1e-6)


class FactorAttributionEngine:
    """
    Engine for factor IC analysis and portfolio return attribution.

    Computes:
    - Spearman IC between factor scores and forward returns
    - Regime-conditional IC (GREEN/AMBER/RED)
    - Rolling IC windows
    - Long-short quintile factor returns
    - Portfolio return decomposition with residual
    """

    def __init__(self, rolling_window: int = 60):
        """
        Initialize attribution engine.

        Args:
            rolling_window: Window size for rolling IC computation (default 60 days)
        """
        self.rolling_window = rolling_window

    def compute_factor_ic(
        self,
        factor_scores: pd.Series,
        forward_returns: pd.Series,
        timestamp: Optional[pd.Timestamp] = None
    ) -> FactorICResult:
        """
        Compute Spearman IC between factor scores and forward returns.

        Args:
            factor_scores: Factor scores for assets
            forward_returns: Forward returns for assets
            timestamp: Timestamp for this IC computation

        Returns:
            FactorICResult with IC, p-value, and observation count
        """
        # Align and drop NaN
        aligned = pd.DataFrame({
            'factor': factor_scores,
            'returns': forward_returns
        }).dropna()

        if len(aligned) < 2:
            return FactorICResult(
                factor_name=factor_scores.name or "unknown",
                ic=np.nan,
                p_value=np.nan,
                n_observations=len(aligned),
                timestamp=timestamp or pd.Timestamp.now()
            )

        ic, p_value = spearmanr(aligned['factor'], aligned['returns'])

        return FactorICResult(
            factor_name=factor_scores.name or "unknown",
            ic=ic,
            p_value=p_value,
            n_observations=len(aligned),
            timestamp=timestamp or pd.Timestamp.now()
        )

    def compute_regime_conditional_ic(
        self,
        factor_scores: pd.Series,
        forward_returns: pd.Series,
        regime_labels: pd.Series
    ) -> RegimeICResult:
        """
        Compute IC separately for GREEN/AMBER/RED regimes.

        Args:
            factor_scores: Factor scores for assets
            forward_returns: Forward returns for assets
            regime_labels: Regime classification (GREEN/AMBER/RED)

        Returns:
            RegimeICResult with IC and p-values for each regime
        """
        # Align all series
        aligned = pd.DataFrame({
            'factor': factor_scores,
            'returns': forward_returns,
            'regime': regime_labels
        }).dropna()

        results = {}
        for regime in ['GREEN', 'AMBER', 'RED']:
            regime_data = aligned[aligned['regime'] == regime]

            if len(regime_data) >= 2:
                ic, p_val = spearmanr(regime_data['factor'], regime_data['returns'])
                results[regime] = {'ic': ic, 'pval': p_val, 'n': len(regime_data)}
            else:
                results[regime] = {'ic': np.nan, 'pval': np.nan, 'n': len(regime_data)}

        return RegimeICResult(
            factor_name=factor_scores.name or "unknown",
            green_ic=results['GREEN']['ic'],
            amber_ic=results['AMBER']['ic'],
            red_ic=results['RED']['ic'],
            green_pval=results['GREEN']['pval'],
            amber_pval=results['AMBER']['pval'],
            red_pval=results['RED']['pval'],
            green_n=results['GREEN']['n'],
            amber_n=results['AMBER']['n'],
            red_n=results['RED']['n']
        )

    def compute_rolling_ic(
        self,
        factor_scores: pd.DataFrame,
        forward_returns: pd.DataFrame,
        factor_name: str
    ) -> pd.DataFrame:
        """
        Compute rolling IC over time windows.

        Args:
            factor_scores: DataFrame with dates as index, assets as columns
            forward_returns: DataFrame with dates as index, assets as columns
            factor_name: Name of the factor being analyzed

        Returns:
            DataFrame with columns: date, ic, p_value, n_observations
        """
        # Ensure aligned indices
        common_dates = factor_scores.index.intersection(forward_returns.index)
        factor_scores = factor_scores.loc[common_dates]
        forward_returns = forward_returns.loc[common_dates]

        rolling_results = []

        for i in range(self.rolling_window, len(common_dates) + 1):
            window_dates = common_dates[i - self.rolling_window:i]

            # Stack data for window
            factor_window = factor_scores.loc[window_dates].stack().dropna()
            returns_window = forward_returns.loc[window_dates].stack().dropna()

            # Align
            aligned_idx = factor_window.index.intersection(returns_window.index)
            factor_aligned = factor_window.loc[aligned_idx]
            returns_aligned = returns_window.loc[aligned_idx]

            if len(factor_aligned) >= 2:
                ic, p_val = spearmanr(factor_aligned, returns_aligned)
            else:
                ic, p_val = np.nan, np.nan

            rolling_results.append({
                'date': window_dates[-1],
                'ic': ic,
                'p_value': p_val,
                'n_observations': len(factor_aligned)
            })

        return pd.DataFrame(rolling_results)

    def compute_factor_returns(
        self,
        factor_scores: pd.Series,
        forward_returns: pd.Series,
        n_quintiles: int = 5
    ) -> Dict[str, float]:
        """
        Compute long-short quintile portfolio returns.

        Args:
            factor_scores: Factor scores for assets
            forward_returns: Forward returns for assets
            n_quintiles: Number of quintiles (default 5)

        Returns:
            Dictionary with quintile returns and long-short spread
        """
        # Align and drop NaN
        aligned = pd.DataFrame({
            'factor': factor_scores,
            'returns': forward_returns
        }).dropna()

        if len(aligned) < n_quintiles:
            return {f'Q{i+1}': np.nan for i in range(n_quintiles)} | {'long_short': np.nan}

        # Assign quintiles
        aligned['quintile'] = pd.qcut(
            aligned['factor'],
            q=n_quintiles,
            labels=[f'Q{i+1}' for i in range(n_quintiles)],
            duplicates='drop'
        )

        # Compute equal-weighted returns per quintile
        quintile_returns = aligned.groupby('quintile')['returns'].mean()

        results = quintile_returns.to_dict()

        # Long-short: Q5 - Q1 (assuming higher factor score = better)
        if 'Q5' in results and 'Q1' in results:
            results['long_short'] = results['Q5'] - results['Q1']
        else:
            results['long_short'] = np.nan

        return results

    def decompose_portfolio_return(
        self,
        portfolio_return: float,
        factor_exposures: Dict[str, float],
        factor_returns: Dict[str, float],
        timestamp: Optional[pd.Timestamp] = None
    ) -> AttributionResult:
        """
        Decompose portfolio return into factor contributions and residual.

        Formula: portfolio_return = Σ(exposure_i × factor_return_i) + residual

        Args:
            portfolio_return: Actual portfolio return
            factor_exposures: Dictionary of factor exposures
            factor_returns: Dictionary of factor returns
            timestamp: Timestamp for this attribution

        Returns:
            AttributionResult with factor contributions and residual
        """
        factor_contributions = {}

        for factor_name in factor_exposures:
            if factor_name in factor_returns:
                contribution = factor_exposures[factor_name] * factor_returns[factor_name]
                factor_contributions[factor_name] = contribution

        # Residual = actual - explained
        explained_return = sum(factor_contributions.values())
        residual = portfolio_return - explained_return

        return AttributionResult(
            total_return=portfolio_return,
            factor_contributions=factor_contributions,
            residual=residual,
            timestamp=timestamp or pd.Timestamp.now()
        )

    def validate_attribution(self, attribution: AttributionResult) -> Tuple[bool, float]:
        """
        Validate attribution accounting identity.

        Checks: total_return = sum(factor_contributions) + residual

        Args:
            attribution: AttributionResult to validate

        Returns:
            Tuple of (is_valid, error_magnitude)
        """
        computed_total = sum(attribution.factor_contributions.values()) + attribution.residual
        error = abs(computed_total - attribution.total_return)
        is_valid = error < 1e-6

        return is_valid, error
