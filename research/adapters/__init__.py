"""Research-runner adapters for strategy/replay outputs."""

from research.adapters.rule100_replay_adapter import (
    DEFAULT_PROMOTION_STATUS,
    DEFAULT_STRATEGY_ROLE,
    Rule100ReplayAdapterResult,
    adapt_rule100_replay_to_target_weights,
    rule100_replay_to_target_weights,
)

__all__ = [
    "DEFAULT_PROMOTION_STATUS",
    "DEFAULT_STRATEGY_ROLE",
    "Rule100ReplayAdapterResult",
    "adapt_rule100_replay_to_target_weights",
    "rule100_replay_to_target_weights",
]
