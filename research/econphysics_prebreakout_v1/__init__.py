"""ECONPHYSICS_PREBREAKOUT_v1 S0 structured-state proof surface."""

from research.econphysics_prebreakout_v1.contracts import (
    FAMILY_ID,
    IMPLEMENTATION_ID,
    NodeState,
    NodeTransition,
    StructuredQuarterRow,
    StructuredSnapshot,
    StructuredStateContractError,
    build_structured_snapshots,
    conservative_available_at,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.structured_state import (
    DirectionalEvidence,
    NodeResult,
    StructuredState,
    aggregate_evidence,
    build_structured_state,
)
from research.econphysics_prebreakout_v1.transition_evaluator import (
    CORE_TARGETS,
    evaluate_structured_transition_rows,
    evaluate_structured_transitions,
)

__all__ = [
    "CORE_TARGETS",
    "DirectionalEvidence",
    "FAMILY_ID",
    "IMPLEMENTATION_ID",
    "NodeResult",
    "NodeState",
    "NodeTransition",
    "StructuredQuarterRow",
    "StructuredSnapshot",
    "StructuredState",
    "StructuredStateContractError",
    "aggregate_evidence",
    "build_structured_snapshots",
    "build_structured_state",
    "conservative_available_at",
    "deterministic_xs_holdout",
    "evaluate_structured_transition_rows",
    "evaluate_structured_transitions",
]
