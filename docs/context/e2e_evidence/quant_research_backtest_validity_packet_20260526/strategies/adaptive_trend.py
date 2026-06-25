"""
Terminal Zero — Adaptive Trend Strategy

Implements the "Transparent Advisor" logic:
  1. Attack (1.0): SPY > MA200 & VIX < 20 (Strong Trend)
  2. Caution (0.7): SPY > MA200 & VIX >= 20 (High Vol, Tight Risk)
  3. Defense (0.5): SPY < MA200 (Broken Trend / Bear Market)
"""

import numpy as np
import pandas as pd
from strategies.base import BaseStrategy


class AdaptiveTrendStrategy(BaseStrategy):
    """
    Regime-adaptive trend-following strategy with Macro Defense.
    """

    def __init__(
        self,
        atr_period: int = 20,
        stop_lookback: int = 22,
        vol_target: float = 0.15,
        vol_lookback: int = 20,
        ma_lookback: int = 200,
        rsi_period: int = 14,
        rsi_exit_lookback: int = 10,
        max_positions: int = 50,
        min_price: float = 5.0,
        min_dollar_vol: float = 1_000_000.0,
    ):
        self.atr_period = atr_period
        self.stop_lookback = stop_lookback
        self.vol_target = vol_target
        self.vol_lookback = vol_lookback
        self.ma_lookback = ma_lookback
        self.rsi_period = rsi_period
        self.rsi_exit_lookback = rsi_exit_lookback
        self.max_positions = max_positions
        self.min_price = min_price
        self.min_dollar_vol = min_dollar_vol

    # ── Core API ────────────────────────────────────────────────────────────

    def generate_weights(
        self,
        prices: pd.DataFrame,
        fundamentals: pd.DataFrame | None,
        macro: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        Full pipeline: Filter → Signal → Size → Macro Defense → Explainability
        """
        # Align macro to price dates
        vix = macro["vix_proxy"].reindex(prices.index).ffill().fillna(15.0)
        spy = macro["spy_close"].reindex(prices.index).ffill()

        # ── 1. Liquidity Filter ─────────────────────────────────────────────
        dollar_vol = (prices * prices.pct_change().abs()).rolling(20).mean()
        liquid = (prices > self.min_price) & (dollar_vol > self.min_dollar_vol / 1e6)

        # ── 2. Trend Signal: Price > MA ─────────────────────────────────────
        ma = prices.rolling(self.ma_lookback, min_periods=self.ma_lookback).mean()
        trend_up = prices > ma

        # ── 3. Chandelier Stop (FR-005) ─────────────────────────────────────
        k = self.get_regime_k(vix)
        daily_range = prices.diff().abs()
        atr = daily_range.rolling(self.atr_period).mean()
        highest = prices.rolling(self.stop_lookback).max()
        stop_level = highest.sub(atr.mul(k, axis=0))
        above_stop = prices > stop_level

        # ── 4. RSI Divergence Exit (FR-007) ─────────────────────────────────
        rsi = self._compute_rsi(prices, self.rsi_period)
        price_new_high = prices > prices.rolling(self.rsi_exit_lookback).max().shift(1)
        rsi_prev_high = rsi.rolling(self.rsi_exit_lookback).max().shift(1)
        bearish_divergence = price_new_high & (rsi < rsi_prev_high)
        rsi_scale = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)
        rsi_scale[bearish_divergence] = 0.5

        # ── 5. Combine Signals ──────────────────────────────────────────────
        raw_signal = (liquid & trend_up & above_stop).astype(float)
        raw_signal = raw_signal * rsi_scale

        # ── 6. Volatility Sizing (FR-006) ───────────────────────────────────
        realized_vol = (
            prices.pct_change()
            .rolling(self.vol_lookback)
            .std()
            * np.sqrt(252)
        )
        realized_vol = realized_vol.clip(lower=0.05)
        # Scale specific volatility targeting based on regime (see below)
        inv_vol = self.vol_target / realized_vol
        sized_signal = raw_signal * inv_vol

        # ── 7. Normalize ────────────────────────────────────────────────────
        rank = sized_signal.rank(axis=1, ascending=False, method="first")
        sized_signal[rank > self.max_positions] = 0.0

        row_sum = sized_signal.sum(axis=1).replace(0, np.nan)
        weights = sized_signal.div(row_sum, axis=0).fillna(0.0)

        weights = weights.clip(upper=1.0)
        # Scale back excess > 1.0
        exceeds = (weights.sum(axis=1) > 1.0)
        scale_fac = 1.0 / weights.sum(axis=1)
        scale_fac[~exceeds] = 1.0
        weights = weights.mul(scale_fac, axis=0)

        # ── 8. THREE-REGIME MACRO DEFENSE ───────────────────────────────────
        spy_ma200 = spy.rolling(200).mean()
        
        # Default: Attack (1.0)
        regime = pd.Series(1.0, index=spy.index)
        
        # Caution (0.7): SPY > MA200 but VIX >= 20 ("Volatile Bull")
        caution_mask = (spy > spy_ma200) & (vix >= 20)
        regime[caution_mask] = 0.7
        
        # Defense (0.5): SPY < MA200 ("Bear Market")
        defense_mask = (spy < spy_ma200)
        regime[defense_mask] = 0.5

        # Apply the Regime Scalar
        weights = weights.mul(regime, axis=0)

        # ── 9. EXPLAINABILITY (The "Why") ───────────────────────────────────
        latest_val = regime.iloc[-1]
        latest_vix = vix.iloc[-1]
        spy_status = "ABOVE" if spy.iloc[-1] > spy_ma200.iloc[-1] else "BELOW"
        
        if latest_val == 0.5:
            status = "🛡️ DEFENSE (0.5x)"
            reason = f"SPY {spy_status} MA200 (Bear Trend)"
            color = "#ff4444"
        elif latest_val == 0.7:
            status = "⚠️ CAUTION (0.7x)"
            reason = f"SPY {spy_status} MA200 but VIX={latest_vix:.1f} (High Vol)"
            color = "#ffaa00"
        else:
            status = "🚀 ATTACK (1.0x)"
            reason = f"SPY {spy_status} MA200 + VIX={latest_vix:.1f} (Clear Trend)"
            color = "#00ff88"

        details = {
            "status": status,
            "multiplier": float(latest_val),
            "reason": reason,
            "color": color
        }

        return weights, regime, details

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_rsi(prices: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        delta = prices.diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)
