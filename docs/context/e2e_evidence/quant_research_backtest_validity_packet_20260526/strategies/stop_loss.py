"""
Phase 21 Day 1: position-level stop-loss and drawdown control.

Implements:
  1) ATR proxy from close-only data using SMA (not EMA),
  2) two-stage stops with D-57 ratchet constraint,
  3) portfolio drawdown circuit-breaker scaling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


ATRMode = Literal["proxy_close_only"]


@dataclass(frozen=True)
class StopLossConfig:
    # ATR parameters
    atr_window: int = 20
    atr_mode: ATRMode = "proxy_close_only"

    # Stop multipliers
    initial_stop_atr_multiple: float = 2.0
    trailing_stop_atr_multiple: float = 1.5

    # Time-based exit
    max_underwater_days: int = 60

    # Optional safety floor for zero-vol cases (disabled by default).
    min_stop_distance_abs: float = 0.0

    # Drawdown tiers
    dd_tier1_threshold: float = -0.08
    dd_tier1_scale: float = 0.75
    dd_tier2_threshold: float = -0.12
    dd_tier2_scale: float = 0.50
    dd_tier3_threshold: float = -0.15
    dd_tier3_scale: float = 0.00
    dd_recovery_threshold: float = -0.04

    def __post_init__(self) -> None:
        if self.atr_mode != "proxy_close_only":
            raise ValueError("atr_mode must be proxy_close_only for Phase 21 Day 1")
        if int(self.atr_window) <= 1:
            raise ValueError("atr_window must be > 1")
        if float(self.initial_stop_atr_multiple) <= 0.0:
            raise ValueError("initial_stop_atr_multiple must be > 0")
        if float(self.trailing_stop_atr_multiple) <= 0.0:
            raise ValueError("trailing_stop_atr_multiple must be > 0")
        if int(self.max_underwater_days) < 0:
            raise ValueError("max_underwater_days must be >= 0")
        if float(self.min_stop_distance_abs) < 0.0:
            raise ValueError("min_stop_distance_abs must be >= 0")
        if not (
            float(self.dd_tier3_threshold)
            <= float(self.dd_tier2_threshold)
            <= float(self.dd_tier1_threshold)
            < 0.0
        ):
            raise ValueError(
                "drawdown thresholds must satisfy tier3 <= tier2 <= tier1 < 0"
            )
        if not (0.0 <= float(self.dd_tier3_scale) <= float(self.dd_tier2_scale) <= float(self.dd_tier1_scale) <= 1.0):
            raise ValueError("drawdown scales must satisfy 0 <= tier3 <= tier2 <= tier1 <= 1")


class ATRCalculator:
    """
    ATR proxy for close-only environments.

    ATR_t = SMA(|close_t - close_{t-1}|, atr_window)
    """

    def __init__(self, config: StopLossConfig):
        self.config = config

    def compute_atr(self, close_prices: pd.Series) -> pd.Series:
        if self.config.atr_mode != "proxy_close_only":
            raise ValueError(
                f"Unsupported atr_mode={self.config.atr_mode}; expected proxy_close_only"
            )
        series = pd.to_numeric(close_prices, errors="coerce")
        daily_range = series.diff().abs()
        return daily_range.rolling(
            window=int(self.config.atr_window),
            min_periods=int(self.config.atr_window),
        ).mean()

    def compute_atr_at_date(self, close_prices: pd.Series, date: pd.Timestamp) -> float:
        atr = self.compute_atr(close_prices)
        ts = pd.Timestamp(date)
        if ts not in atr.index:
            raise ValueError(f"Date {ts} not in ATR index")
        value = atr.loc[ts]
        if pd.isna(value):
            raise ValueError(f"ATR at {ts} is NaN (insufficient history)")
        return float(value)


@dataclass
class PositionStop:
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    atr_at_entry: float
    current_stop: float
    is_trailing: bool = False
    days_held: int = 0
    highest_price: float | None = None

    def __post_init__(self) -> None:
        if self.highest_price is None:
            self.highest_price = float(self.entry_price)


class StopLossManager:
    """
    Two-stage stop logic with D-57 ratchet invariant.

    Invariant:
      stop_t = max(stop_{t-1}, stop_candidate_t)
      => stop_t never decreases.
    """

    def __init__(self, config: StopLossConfig):
        self.config = config
        self.atr_calc = ATRCalculator(config)
        self.positions: dict[str, PositionStop] = {}

    def _enforce_min_stop_distance(self, reference_price: float, stop_candidate: float) -> float:
        min_dist = float(self.config.min_stop_distance_abs)
        if min_dist <= 0.0:
            return float(stop_candidate)
        # For long positions, stop must be at least `min_dist` below reference.
        capped_stop = float(reference_price) - min_dist
        return float(min(stop_candidate, capped_stop))

    def enter_position(
        self,
        ticker: str,
        entry_date: pd.Timestamp,
        entry_price: float,
        close_prices: pd.Series,
    ) -> PositionStop:
        atr_at_entry = self.atr_calc.compute_atr_at_date(close_prices, entry_date)
        initial_stop = float(entry_price) - (
            float(self.config.initial_stop_atr_multiple) * float(atr_at_entry)
        )
        initial_stop = self._enforce_min_stop_distance(
            reference_price=float(entry_price),
            stop_candidate=initial_stop,
        )

        position = PositionStop(
            ticker=str(ticker),
            entry_date=pd.Timestamp(entry_date),
            entry_price=float(entry_price),
            atr_at_entry=float(atr_at_entry),
            current_stop=float(initial_stop),
        )
        self.positions[position.ticker] = position
        return position

    def update_stop(
        self,
        ticker: str,
        current_date: pd.Timestamp,
        current_price: float,
        close_prices: pd.Series,
    ) -> tuple[float, bool]:
        key = str(ticker)
        if key not in self.positions:
            raise ValueError(f"Position {key} not found")

        position = self.positions[key]
        price = float(current_price)
        position.days_held += 1
        position.highest_price = max(float(position.highest_price), price)

        is_profitable = price > float(position.entry_price)
        if (not is_profitable) and position.days_held > int(self.config.max_underwater_days):
            return float(position.current_stop), True

        try:
            atr_current = self.atr_calc.compute_atr_at_date(close_prices, current_date)
        except ValueError:
            return float(position.current_stop), False

        if is_profitable and not position.is_trailing:
            position.is_trailing = True

        if position.is_trailing:
            candidate = price - (float(self.config.trailing_stop_atr_multiple) * atr_current)
            candidate = self._enforce_min_stop_distance(
                reference_price=price,
                stop_candidate=candidate,
            )
        else:
            candidate = float(position.entry_price) - (
                float(self.config.initial_stop_atr_multiple) * atr_current
            )
            candidate = self._enforce_min_stop_distance(
                reference_price=float(position.entry_price),
                stop_candidate=candidate,
            )

        # D-57 ratchet constraint: stop cannot move down.
        new_stop = float(max(float(position.current_stop), float(candidate)))
        position.current_stop = new_stop
        should_exit = price <= new_stop
        return new_stop, bool(should_exit)

    def check_stop_hit(self, ticker: str, current_price: float) -> bool:
        key = str(ticker)
        if key not in self.positions:
            return False
        return float(current_price) <= float(self.positions[key].current_stop)

    def remove_position(self, ticker: str) -> None:
        self.positions.pop(str(ticker), None)


class PortfolioDrawdownMonitor:
    """
    Portfolio circuit breaker by drawdown tiers.
    """

    def __init__(self, config: StopLossConfig):
        self.config = config
        self.peak_equity: float = 0.0
        self.current_tier: int = 0

    def update_equity(self, current_equity: float) -> tuple[int, float]:
        equity = float(current_equity)
        self.peak_equity = max(float(self.peak_equity), equity)

        if self.peak_equity <= 0.0:
            drawdown = 0.0
        else:
            drawdown = (equity - self.peak_equity) / self.peak_equity

        if drawdown <= float(self.config.dd_tier3_threshold):
            tier = 3
            scale = float(self.config.dd_tier3_scale)
        elif drawdown <= float(self.config.dd_tier2_threshold):
            tier = 2
            scale = float(self.config.dd_tier2_scale)
        elif drawdown <= float(self.config.dd_tier1_threshold):
            tier = 1
            scale = float(self.config.dd_tier1_scale)
        else:
            tier = 0
            scale = 1.0

        if self.current_tier > 0 and drawdown > float(self.config.dd_recovery_threshold):
            tier = 0
            scale = 1.0

        self.current_tier = int(tier)
        return int(tier), float(scale)

    def get_current_scale(self) -> float:
        if self.current_tier == 3:
            return float(self.config.dd_tier3_scale)
        if self.current_tier == 2:
            return float(self.config.dd_tier2_scale)
        if self.current_tier == 1:
            return float(self.config.dd_tier1_scale)
        return 1.0


def create_stop_loss_system(
    config: StopLossConfig | None = None,
) -> tuple[StopLossManager, PortfolioDrawdownMonitor]:
    cfg = config if config is not None else StopLossConfig()
    return StopLossManager(cfg), PortfolioDrawdownMonitor(cfg)
