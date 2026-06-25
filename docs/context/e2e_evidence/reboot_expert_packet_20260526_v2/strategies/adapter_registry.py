"""Explicit strategy adapter registry.

Imported by strategy_replay.py to discover adapters without circular imports.
Registration is explicit — each adapter is imported and inserted here.
"""

from __future__ import annotations

from strategies.adapter import StrategyAdapter
from strategies.optimizer import OptimizationMethod


def _build_registry() -> dict[OptimizationMethod, StrategyAdapter]:
    """Build the adapter registry. Called once at module load."""
    from strategies.rule100_adapter import Rule100Adapter

    return {
        OptimizationMethod.RULE_OF_100: Rule100Adapter(),
    }


STRATEGY_ADAPTERS: dict[OptimizationMethod, StrategyAdapter] = _build_registry()


def get_adapter(method: OptimizationMethod | str) -> StrategyAdapter | None:
    """Return the adapter for a method, or None if not registered."""
    if isinstance(method, str):
        try:
            method = OptimizationMethod(method)
        except ValueError:
            return None
    return STRATEGY_ADAPTERS.get(method)
