"""Rule of 100 strategy adapter.

Supplies validation and allocation hooks to the replay engine.
Does NOT produce replay rows, events, or artifacts.
"""

from __future__ import annotations

import pandas as pd

from strategies.adapter import StrategyAdapter, ValidationResult
from strategies.optimizer import OptimizationMethod
from strategies.rule100_softmax import rule100_config_from_max_weight, softmax_v1_weights


class Rule100Adapter(StrategyAdapter):
    """Adapter for Rule of 100 softmax v1 sizing."""

    strategy_id = "rule_of_100_softmax_v1"
    display_name = "Rule of 100"
    method = OptimizationMethod.RULE_OF_100
    required_inputs = ("factor_positive_count", "technical_quality")
    input_coverage_start = "2025-01-06"

    def validate_inputs(
        self, as_of_date: str, pit_inputs: pd.DataFrame
    ) -> ValidationResult:
        warnings: list[str] = []

        if str(as_of_date) < self.input_coverage_start:
            return ValidationResult(
                ok=False,
                reason="no_pit_candidate_data_before_coverage_start",
                warnings=[
                    f"requested {as_of_date} < input_coverage_start {self.input_coverage_start}"
                ],
            )

        if not isinstance(pit_inputs, pd.DataFrame) or pit_inputs.empty:
            return ValidationResult(ok=False, reason="empty_pit_inputs")

        missing = [c for c in self.required_inputs if c not in pit_inputs.columns]
        if missing:
            return ValidationResult(
                ok=False,
                reason=f"missing_required_columns:{','.join(missing)}",
            )

        if "sizing_eligible" in pit_inputs.columns:
            eligible_count = int(pit_inputs["sizing_eligible"].astype(bool).sum())
            if eligible_count == 0:
                warnings.append("no_sizing_eligible_candidates")

        return ValidationResult(ok=True, reason="ok", warnings=warnings)

    def allocation_fn(
        self, as_of_date: str, pit_inputs: pd.DataFrame, controls: object
    ) -> pd.Series:
        if not isinstance(pit_inputs, pd.DataFrame) or pit_inputs.empty:
            return pd.Series(dtype=float)

        max_weight = 0.35
        if controls is not None:
            if isinstance(controls, dict):
                max_weight = controls.get("max_weight", max_weight)
            else:
                max_weight = getattr(controls, "max_weight", max_weight)

        eligible = pit_inputs
        if "sizing_eligible" in pit_inputs.columns:
            eligible = pit_inputs[pit_inputs["sizing_eligible"].astype(bool)].copy()

        if eligible.empty:
            return pd.Series(0.0, index=pit_inputs.index, dtype=float)

        cfg = rule100_config_from_max_weight(max_weight)
        weights = softmax_v1_weights(eligible, cfg)
        return weights.reindex(pit_inputs.index, fill_value=0.0)
