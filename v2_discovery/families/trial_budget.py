from __future__ import annotations

import math
from typing import Any, Mapping

from v2_discovery.families.schemas import CandidateFamilyDefinition
from v2_discovery.families.schemas import CandidateFamilyError


def calculate_trial_budget(parameter_space: Mapping[str, Any]) -> int:
    if not isinstance(parameter_space, Mapping) or not parameter_space:
        raise CandidateFamilyError("parameter_space is required")
    total = 1
    for key, options in parameter_space.items():
        if not isinstance(options, (list, tuple)) or isinstance(options, (str, bytes)):
            raise CandidateFamilyError(f"parameter_space[{key!r}] must be a finite option list")
        if not options:
            raise CandidateFamilyError(f"parameter_space[{key!r}] must be non-empty")
        for option in options:
            if isinstance(option, float) and not math.isfinite(option):
                raise CandidateFamilyError("parameter_space options must be finite")
        total *= len(options)
    return total


def validate_trial_budget(definition: CandidateFamilyDefinition) -> int:
    trial_count = calculate_trial_budget(definition.parameter_space)
    if trial_count > definition.trial_budget_max:
        raise CandidateFamilyError("trial_budget_max is smaller than the finite option product")
    return trial_count
