"""Strategy adapter contract for selected-method replay.

The adapter supplies identity, input validation, and allocation hooks.
It does NOT own replay rows, events, artifacts, or bundle assembly —
those remain the sole responsibility of build_selected_method_replay()
in strategies/strategy_replay.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd

from strategies.optimizer import OptimizationMethod


@dataclass(frozen=True)
class ValidationResult:
    """Typed validation output from a strategy adapter."""

    ok: bool
    reason: str
    warnings: list[str] = field(default_factory=list)


class StrategyAdapter(ABC):
    """Minimal contract for a replay-compatible strategy.

    Adapters declare what they need and how to size. The replay engine
    calls these hooks — the adapter never produces replay bundles itself.
    """

    strategy_id: str
    display_name: str
    method: OptimizationMethod
    required_inputs: tuple[str, ...]
    input_coverage_start: str  # ISO date: earliest date with PIT candidate data

    @abstractmethod
    def validate_inputs(
        self, as_of_date: str, pit_inputs: pd.DataFrame
    ) -> ValidationResult:
        """Check whether PIT inputs are sufficient for this date.

        Must return ok=False with reason when as_of_date < input_coverage_start
        or required columns are missing.
        """
        ...

    @abstractmethod
    def allocation_fn(
        self, as_of_date: str, pit_inputs: pd.DataFrame, controls: object
    ) -> pd.Series:
        """Produce target weights for one PIT date.

        Returns a Series indexed by asset identifier (permno or ticker)
        with float weights summing to <= 1.0. Cash residual is implicit.
        """
        ...
