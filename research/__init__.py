"""Canonical research evidence runner package."""

from research.backtest_runner import ResearchBacktestResult, run_research_backtest
from research.status import ResearchStatus, validate_research_status
from research.strategy_cartridge import StrategyCartridge, validate_cartridge

__all__ = [
    "ResearchBacktestResult",
    "ResearchStatus",
    "StrategyCartridge",
    "run_research_backtest",
    "validate_cartridge",
    "validate_research_status",
]
