"""
Terminal Zero — Strategy Base Class ("The Cartridge API")

All strategies must inherit from BaseStrategy and implement generate_weights().
Updated Contract (Transparent Advisor):
  Returns (weights, regime_signal, debug_details)
"""

from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """
    Abstract contract between Strategy and Engine.
    """

    @abstractmethod
    def generate_weights(
        self,
        prices: pd.DataFrame,
        fundamentals: pd.DataFrame | None,
        macro: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        Generate target portfolio weights with explainability.

        Args:
            prices:        Wide DataFrame of adj_close (Index=Date, Cols=Permno)
            fundamentals:  Wide DataFrame (None for MVP)
            macro:         DataFrame with spy_close, vix_proxy

        Returns:
            weights:       DataFrame (Index=Date, Cols=Permno)
            regime_signal: DataFrame/Series (Values: 0.5, 0.7, 1.0)
            debug_details: dict (Metadata for UI explainer)
        """
        pass

    # ── Shared Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def get_regime_k(vix_series: pd.Series) -> pd.Series:
        """
        Adaptive Chandelier Stop multiplier based on VIX level (FR-005).
        """
        k = pd.Series(3.0, index=vix_series.index)
        k[vix_series < 15] = 2.5
        k[vix_series > 25] = 4.0
        return k
