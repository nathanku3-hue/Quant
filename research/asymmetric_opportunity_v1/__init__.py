"""Asymmetric-opportunity basis mechanics.

AO-K0A is a source/denominator/orthogonalization preflight only.
OK-SBI-0 / AO-K0B-D S0 adds pre-open contracts only: Q source binding,
applicability, status strata, arm formulas, C firewall, claim schema,
label-pack seals, and honest release blockers.  No outcome reader, no
selector tuning, no W6 access, no provider acquisition, no capital authority.
"""

from research.asymmetric_opportunity_v1.orthogonalization import (
    ABSTENTION,
    ELIGIBLE_COMPLETE,
    M_MISSING_HISTORY,
    M_OBSERVED,
    M_WARMUP,
    ORTHOGONALIZATION_CONTRACT_ID,
    Q_AND_M_MISSING,
    Q_UNOBSERVED,
    SELECTABLE,
    assign_basis_status,
    build_basis_status_frame,
    contract_semantics,
    full_w3_breadth,
    orthogonalize_cross_sections,
    percentile_rank,
)

__all__ = [
    "ABSTENTION",
    "ELIGIBLE_COMPLETE",
    "M_MISSING_HISTORY",
    "M_OBSERVED",
    "M_WARMUP",
    "ORTHOGONALIZATION_CONTRACT_ID",
    "Q_AND_M_MISSING",
    "Q_UNOBSERVED",
    "SELECTABLE",
    "assign_basis_status",
    "build_basis_status_frame",
    "contract_semantics",
    "full_w3_breadth",
    "orthogonalize_cross_sections",
    "percentile_rank",
]
