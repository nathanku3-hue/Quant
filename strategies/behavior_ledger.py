"""
Behavior Ledger: Bootstrap-based confidence intervals for patience and exit metrics.

Provides statistical validation that behavioral improvements (patience gain, avoiding
premature exits) are significant with hard gates on CI lower bounds.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class BehaviorLedgerResult:
    """Result container for behavior ledger metrics with bootstrap confidence intervals."""

    # Patience gain: CAGR(wait_rule) - CAGR(immediate)
    patience_gain: float
    patience_gain_ci_lower: float
    patience_gain_ci_upper: float

    # Premature exit drag: return_if_held - actual_return
    premature_exit_drag: float
    premature_exit_drag_ci_lower: float
    premature_exit_drag_ci_upper: float

    # Adherence and capture ratios
    holding_adherence_ratio: float
    signal_capture_ratio: float

    # Sample sizes
    n_trades: int
    n_bootstrap_samples: int

    def passes_hard_gate(self) -> bool:
        """
        Hard gate: Both patience_gain and premature_exit_drag must have ci_lower > 0.

        Returns:
            True if both metrics are statistically significant (lower CI > 0)
        """
        return (self.patience_gain_ci_lower > 0 and
                self.premature_exit_drag_ci_lower > 0)


class BehaviorLedger:
    """
    Computes behavioral metrics with bootstrap confidence intervals.

    Validates that patience (waiting for better entry) and holding discipline
    (avoiding premature exits) provide statistically significant improvements.
    """

    def __init__(self, n_bootstrap: int = 1000, random_seed: int = None):
        """
        Initialize behavior ledger.

        Args:
            n_bootstrap: Number of bootstrap samples for CI estimation
            random_seed: Random seed for reproducibility
        """
        self.n_bootstrap = n_bootstrap
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)

    def compute_patience_gain(
        self,
        wait_returns: np.ndarray,
        immediate_returns: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Compute patience gain: CAGR(wait_rule) - CAGR(immediate) with bootstrap CI.

        Args:
            wait_returns: Returns from waiting for better entry (1D array)
            immediate_returns: Returns from immediate execution (1D array)

        Returns:
            Tuple of (patience_gain, ci_lower, ci_upper)
        """
        if len(wait_returns) != len(immediate_returns):
            raise ValueError("wait_returns and immediate_returns must have same length")

        n = len(wait_returns)
        if n == 0:
            return 0.0, 0.0, 0.0

        # Compute point estimate
        wait_cagr = self._compute_cagr(wait_returns)
        immediate_cagr = self._compute_cagr(immediate_returns)
        patience_gain = wait_cagr - immediate_cagr

        # Bootstrap CI
        bootstrap_gains = []
        for _ in range(self.n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            boot_wait = wait_returns[indices]
            boot_immediate = immediate_returns[indices]

            boot_wait_cagr = self._compute_cagr(boot_wait)
            boot_immediate_cagr = self._compute_cagr(boot_immediate)
            bootstrap_gains.append(boot_wait_cagr - boot_immediate_cagr)

        # Percentile CI (2.5th and 97.5th percentiles)
        ci_lower = np.percentile(bootstrap_gains, 2.5)
        ci_upper = np.percentile(bootstrap_gains, 97.5)

        return patience_gain, ci_lower, ci_upper

    def compute_premature_exit_drag(
        self,
        held_returns: np.ndarray,
        actual_returns: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Compute premature exit drag: return_if_held - actual_return with bootstrap CI.

        Args:
            held_returns: Returns if position was held to target (1D array)
            actual_returns: Actual returns with premature exits (1D array)

        Returns:
            Tuple of (exit_drag, ci_lower, ci_upper)
        """
        if len(held_returns) != len(actual_returns):
            raise ValueError("held_returns and actual_returns must have same length")

        n = len(held_returns)
        if n == 0:
            return 0.0, 0.0, 0.0

        # Compute point estimate (mean drag)
        drag_per_trade = held_returns - actual_returns
        exit_drag = np.mean(drag_per_trade)

        # Bootstrap CI
        bootstrap_drags = []
        for _ in range(self.n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            boot_drag = np.mean(drag_per_trade[indices])
            bootstrap_drags.append(boot_drag)

        # Percentile CI (2.5th and 97.5th percentiles)
        ci_lower = np.percentile(bootstrap_drags, 2.5)
        ci_upper = np.percentile(bootstrap_drags, 97.5)

        return exit_drag, ci_lower, ci_upper

    def compute_full_ledger(
        self,
        wait_returns: np.ndarray,
        immediate_returns: np.ndarray,
        held_returns: np.ndarray,
        actual_returns: np.ndarray,
        n_adherent_holds: int,
        n_total_holds: int,
        n_signals_captured: int,
        n_total_signals: int
    ) -> BehaviorLedgerResult:
        """
        Compute all behavioral metrics with confidence intervals.

        Args:
            wait_returns: Returns from waiting for better entry
            immediate_returns: Returns from immediate execution
            held_returns: Returns if positions held to target
            actual_returns: Actual returns with premature exits
            n_adherent_holds: Number of trades that adhered to holding rules
            n_total_holds: Total number of holding opportunities
            n_signals_captured: Number of signals successfully captured
            n_total_signals: Total number of signals generated

        Returns:
            BehaviorLedgerResult with all metrics and CIs
        """
        # Compute patience gain
        patience_gain, patience_ci_lower, patience_ci_upper = self.compute_patience_gain(
            wait_returns, immediate_returns
        )

        # Compute premature exit drag
        exit_drag, exit_ci_lower, exit_ci_upper = self.compute_premature_exit_drag(
            held_returns, actual_returns
        )

        # Compute adherence and capture ratios
        holding_adherence_ratio = (n_adherent_holds / n_total_holds
                                   if n_total_holds > 0 else 0.0)
        signal_capture_ratio = (n_signals_captured / n_total_signals
                               if n_total_signals > 0 else 0.0)

        return BehaviorLedgerResult(
            patience_gain=patience_gain,
            patience_gain_ci_lower=patience_ci_lower,
            patience_gain_ci_upper=patience_ci_upper,
            premature_exit_drag=exit_drag,
            premature_exit_drag_ci_lower=exit_ci_lower,
            premature_exit_drag_ci_upper=exit_ci_upper,
            holding_adherence_ratio=holding_adherence_ratio,
            signal_capture_ratio=signal_capture_ratio,
            n_trades=len(wait_returns),
            n_bootstrap_samples=self.n_bootstrap
        )

    @staticmethod
    def _compute_cagr(returns: np.ndarray) -> float:
        """
        Compute CAGR from array of returns.

        Args:
            returns: Array of returns (e.g., 0.05 for 5% return)

        Returns:
            CAGR as decimal (e.g., 0.15 for 15% CAGR)
        """
        if len(returns) == 0:
            return 0.0

        # Compound returns: (1 + r1) * (1 + r2) * ... - 1
        cumulative_return = np.prod(1 + returns) - 1

        # Annualize assuming each return is per trade
        # For simplicity, use geometric mean: (1 + total_return)^(1/n) - 1
        n = len(returns)
        cagr = (1 + cumulative_return) ** (1 / n) - 1

        return cagr
