"""
Phase 18 Day 3 — Cash overlay strategies.

Signal layer uses TRI and enforces lag-safe computations.
Execution lag and costs are still enforced by engine.run_simulation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class CashOverlay(ABC):
    @abstractmethod
    def compute_exposure(
        self,
        spy_tri: pd.Series,
        spy_returns: pd.Series,
        macro: pd.DataFrame | None = None,
    ) -> pd.Series:
        """
        Return target exposure in [0, 1] indexed by date.
        """

    @abstractmethod
    def get_name(self) -> str:
        """
        Human-readable scenario label.
        """


class VolatilityTargetOverlay(CashOverlay):
    """
    Exposure scaler:
      w_t = clip(target_vol / realized_vol_t, 0, max_leverage)
    where realized_vol_t is computed from lagged returns.
    """

    def __init__(
        self,
        target_vol: float = 0.15,
        lookback_window: int = 60,
        max_leverage: float = 1.0,
    ):
        if not 0.01 <= float(target_vol) <= 0.60:
            raise ValueError(f"target_vol must be in [0.01, 0.60], got {target_vol}")
        if not 5 <= int(lookback_window) <= 252:
            raise ValueError(f"lookback_window must be in [5, 252], got {lookback_window}")
        if not 0.0 < float(max_leverage) <= 1.0:
            raise ValueError(f"max_leverage must be in (0, 1], got {max_leverage}")
        self.target_vol = float(target_vol)
        self.lookback_window = int(lookback_window)
        self.max_leverage = float(max_leverage)

    def compute_exposure(
        self,
        spy_tri: pd.Series,
        spy_returns: pd.Series,
        macro: pd.DataFrame | None = None,
    ) -> pd.Series:
        idx = pd.DatetimeIndex(pd.to_datetime(spy_returns.index, errors="coerce"))
        idx = idx[~idx.isna()].sort_values()
        # Preserve NaNs so missing-data windows are not interpreted as zero volatility.
        ret = pd.to_numeric(spy_returns, errors="coerce").reindex(idx)
        ret = ret.replace([np.inf, -np.inf], np.nan)

        # D-04 guardrail: build realized vol from t-1 information.
        realized_vol = (
            ret.shift(1)
            .rolling(self.lookback_window, min_periods=self.lookback_window)
            .std()
            * np.sqrt(252.0)
        )
        exposure_raw = self.target_vol / realized_vol.replace(0.0, np.nan)
        exposure = exposure_raw.clip(lower=0.0, upper=self.max_leverage)
        exposure = exposure.fillna(self.max_leverage)
        return exposure.astype(float)

    def get_name(self) -> str:
        return f"Vol Target {self.target_vol:.0%} ({self.lookback_window}d)"


class TrendFollowingOverlay(CashOverlay):
    """
    Multi-horizon trend score:
      score_t = sum_i(w_i * sign(price_t-1 - MA_i,t-1))
      exposure_t = clip(0.5 + 0.5 * score_t, 0, 1)
    """

    def __init__(
        self,
        ma_windows: list[int] | None = None,
        ma_weights: list[float] | None = None,
    ):
        self.ma_windows = ma_windows if ma_windows is not None else [50, 100, 200]
        self.ma_weights = ma_weights if ma_weights is not None else [0.5, 0.3, 0.2]

        if len(self.ma_windows) != len(self.ma_weights):
            raise ValueError("ma_windows and ma_weights length mismatch")
        if any(int(w) <= 1 for w in self.ma_windows):
            raise ValueError("all ma_windows must be > 1")
        if any(float(w) <= 0.0 for w in self.ma_weights):
            raise ValueError("all ma_weights must be > 0")
        if abs(float(sum(self.ma_weights)) - 1.0) > 1e-6:
            raise ValueError("ma_weights must sum to 1.0")

        self.ma_windows = [int(x) for x in self.ma_windows]
        self.ma_weights = [float(x) for x in self.ma_weights]

    def compute_exposure(
        self,
        spy_tri: pd.Series,
        spy_returns: pd.Series,
        macro: pd.DataFrame | None = None,
    ) -> pd.Series:
        idx = pd.DatetimeIndex(pd.to_datetime(spy_tri.index, errors="coerce"))
        idx = idx[~idx.isna()].sort_values()
        tri = pd.to_numeric(spy_tri, errors="coerce").reindex(idx).ffill()

        # D-04 guardrail: use lagged prices in signal construction.
        tri_lag = tri.shift(1)
        score = pd.Series(0.0, index=idx, dtype=float)
        for win, wt in zip(self.ma_windows, self.ma_weights):
            ma = tri_lag.rolling(win, min_periods=win).mean()
            signal = (tri_lag > ma).astype(float) * 2.0 - 1.0
            score = score + (wt * signal)

        exposure = 0.5 + 0.5 * score
        exposure = exposure.clip(lower=0.0, upper=1.0).fillna(0.5)
        return exposure.astype(float)

    def get_name(self) -> str:
        wins = "/".join(str(x) for x in self.ma_windows)
        return f"Trend Multi-Horizon ({wins})"
