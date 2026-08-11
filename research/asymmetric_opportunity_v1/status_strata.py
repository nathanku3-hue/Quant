"""OK-SBI-0 status-stratified missingness — extension of AO-K0A, no rewrite.

Mandatory strata are reported separately.  Mixed prose like "~20% Q missing"
is forbidden.  Coverage-cube mechanics are outcome-blind.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Set

import pandas as pd

from research.asymmetric_opportunity_v1.orthogonalization import (
    ELIGIBLE_COMPLETE,
    M_MISSING_HISTORY,
    M_OBSERVED,
    M_WARMUP,
    Q_AND_M_MISSING,
    Q_UNOBSERVED,
    W3_DENOMINATOR_ID,
    assign_basis_status,
    build_basis_status_frame,
)

# K0A strata (inherited, never rewritten)
# + OK-SBI-0 applicability / other explicit strata
Q_NOT_APPLICABLE = "Q_NOT_APPLICABLE"
M_NOT_APPLICABLE = "M_NOT_APPLICABLE"
OTHER_EXPLICIT_STATUS = "OTHER_EXPLICIT_STATUS"

MANDATORY_STATUS_STRATA = (
    ELIGIBLE_COMPLETE,
    Q_UNOBSERVED,
    M_WARMUP,
    M_MISSING_HISTORY,
    Q_AND_M_MISSING,
    Q_NOT_APPLICABLE,
    M_NOT_APPLICABLE,
    OTHER_EXPLICIT_STATUS,
)

STATUS_STRATA_CONTRACT_ID = "StatusStrataContractV1"
MIXED_UNOBSERVED_LANGUAGE = "FORBIDDEN"


def contract_semantics() -> dict[str, Any]:
    return {
        "contract_id": STATUS_STRATA_CONTRACT_ID,
        "slice_id": "OK-SBI-0",
        "denominator": W3_DENOMINATOR_ID,
        "denominator_rewrite": "FORBIDDEN",
        "k0a_statuses_preserved": True,
        "mandatory_strata": list(MANDATORY_STATUS_STRATA),
        "mixed_unobserved_mashup_language": MIXED_UNOBSERVED_LANGUAGE,
        "coverage_cube_label_join": "FORBIDDEN_THIS_TURN",
        "row_deletion_for_missingness": "FORBIDDEN",
        "missingness": "PERSISTENT_ABSTENTION_PLUS_APPLICABILITY_STRATA",
    }


def assign_extended_status(
    *,
    q_observed: bool,
    m_state: str,
    q_applicable: bool = True,
    m_applicable: bool = True,
    other_explicit_status: str | None = None,
) -> str:
    """Assign one status stratum without rewriting K0A precedence for core cases.

    Applicability overlays take precedence for explicit out-of-domain names.
    `other_explicit_status` may only supply OTHER_EXPLICIT_STATUS when set.
    """

    if other_explicit_status:
        if other_explicit_status != OTHER_EXPLICIT_STATUS:
            raise ValueError(f"ok_sbi_0_invalid_other_status:{other_explicit_status}")
        return OTHER_EXPLICIT_STATUS
    if not q_applicable:
        return Q_NOT_APPLICABLE
    if not m_applicable:
        return M_NOT_APPLICABLE
    return assign_basis_status(q_observed=q_observed, m_state=m_state)


def build_status_strata_frame(
    w3_rows: pd.DataFrame,
    *,
    q_observed_keys: Set[tuple[str, str]],
    m_state_by_key: Mapping[tuple[str, str, str], str],
    q_not_applicable_keys: Set[tuple[str, str]] | None = None,
    m_not_applicable_keys: Set[tuple[str, str]] | None = None,
    other_explicit_keys: Set[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """Left-preserve W3 rows; attach extended strata + K0A basis_status.

    Does not drop rows.  Does not join labels.
    """

    q_na = q_not_applicable_keys or set()
    m_na = m_not_applicable_keys or set()
    other = other_explicit_keys or set()

    base = build_basis_status_frame(
        w3_rows,
        q_observed_keys=q_observed_keys,
        m_state_by_key=m_state_by_key,
    )
    extended: list[str] = []
    for row in base.itertuples(index=False):
        key = (str(row.decision_date), str(row.security_id))
        if key in other:
            extended.append(OTHER_EXPLICIT_STATUS)
            continue
        if key in q_na:
            extended.append(Q_NOT_APPLICABLE)
            continue
        if key in m_na:
            extended.append(M_NOT_APPLICABLE)
            continue
        extended.append(str(row.basis_status))
    base["status_stratum"] = extended
    if len(base) != len(w3_rows):
        raise AssertionError("ok_sbi_0_status_strata_row_loss")
    return base


def coverage_cube(
    status_frame: pd.DataFrame,
    *,
    stratum_col: str = "status_stratum",
    date_col: str = "decision_date",
) -> dict[str, Any]:
    """Outcome-blind coverage cube: counts by stratum (and optional date).

    Never computes retention metrics that require label join.
    """

    if stratum_col not in status_frame.columns:
        raise ValueError(f"ok_sbi_0_status_col_missing:{stratum_col}")
    total = len(status_frame)
    counts = Counter(str(v) for v in status_frame[stratum_col].tolist())
    by_stratum = {name: int(counts.get(name, 0)) for name in MANDATORY_STATUS_STRATA}
    # Preserve any unexpected labels without collapsing them into a mashup.
    for name, count in counts.items():
        if name not in by_stratum:
            by_stratum[name] = int(count)

    by_date: dict[str, dict[str, int]] = {}
    if date_col in status_frame.columns:
        for decision_date, group in status_frame.groupby(date_col, sort=True):
            c = Counter(str(v) for v in group[stratum_col].tolist())
            by_date[str(decision_date)] = {
                name: int(c.get(name, 0)) for name in MANDATORY_STATUS_STRATA
            }

    return {
        "contract_id": STATUS_STRATA_CONTRACT_ID,
        "total_rows": total,
        "rows_removed": 0,
        "by_stratum": by_stratum,
        "by_decision_date": by_date,
        "mixed_unobserved_mashup": None,
        "label_join": False,
        "forbidden_language_examples": [
            "~20% unobserved",
            "about one fifth Q missing",
            "mixed missingness ~X%",
        ],
    }


def refuse_mixed_unobserved_language(text: str) -> None:
    lowered = text.lower()
    banned_fragments = (
        "~20% unobserved",
        "about 20% missing",
        "roughly 20% q missing",
        "mixed missingness",
    )
    for fragment in banned_fragments:
        if fragment in lowered:
            raise ValueError(f"ok_sbi_0_mixed_unobserved_language_forbidden:{fragment}")
