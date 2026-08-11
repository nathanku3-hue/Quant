"""AO-K0A denominator alignment and date-local orthogonalization mechanics.

The module is deliberately outcome-blind.  Missing Q/M never changes the W3
row set: it changes only the per-arm action to ABSTENTION.  Coverage is a
reported state, not a PASS/FAIL admission gate.
"""

from __future__ import annotations

from collections.abc import Mapping, Set
from typing import Any

import numpy as np
import pandas as pd


ORTHOGONALIZATION_CONTRACT_ID = "OrthogonalizationContractV1"
W3_DENOMINATOR_ID = "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"

ELIGIBLE_COMPLETE = "ELIGIBLE_COMPLETE"
Q_UNOBSERVED = "Q_UNOBSERVED"
M_WARMUP = "M_WARMUP"
M_MISSING_HISTORY = "M_MISSING_HISTORY"
Q_AND_M_MISSING = "Q_AND_M_MISSING"

M_OBSERVED = "M_OBSERVED"
_M_STATES = frozenset({M_OBSERVED, M_WARMUP, M_MISSING_HISTORY})

SELECTABLE = "SELECTABLE"
ABSTENTION = "ABSTENTION"

_FORBIDDEN_OUTCOME_COLUMNS = frozenset(
    {
        "winner_label",
        "right_tail_label",
        "bottom_tail_label",
        "catastrophic_downside_label",
        "future_return",
        "forward_return",
        "outcome_return",
        "w6_label",
    }
)


def contract_semantics() -> dict[str, Any]:
    """Return the frozen AO-K0A semantics as machine-readable constants."""

    return {
        "contract_id": ORTHOGONALIZATION_CONTRACT_ID,
        "denominator": W3_DENOMINATOR_ID,
        "missingness": "PERSISTENT_ABSTENTION_STATE_NEVER_ELIGIBILITY_REWRITE",
        "q_normalization": "DATE_LOCAL_AVERAGE_TIE_PERCENTILE_RANK_OVER_Q_OBSERVED_W3",
        "m_normalization": "DATE_LOCAL_AVERAGE_TIE_PERCENTILE_RANK_OVER_Q_AND_M_OBSERVED_W3",
        "orthogonalization": "OLS_RANK_M_ON_INTERCEPT_AND_RANK_Q_WITHIN_DECISION_DATE",
        "temporal_fit": False,
        "outcome_input": False,
        "q_arm_observability": "Q_OBSERVED",
        "m_residual_arm_observability": "Q_AND_M_OBSERVED",
        "q_plus_m_residual_arm_observability": "Q_AND_M_OBSERVED",
        "right_tail_denominator": "ALL_MATURED_W3_ELIGIBLE_WINNERS",
        "breadth_denominator": "ALL_W3_ELIGIBLE_SECURITIES",
        "abstention_selected": False,
        "abstention_risky_weight": 0.0,
        "residual_capital": "ECONOMIC_CASH",
        "residual_capital_builder": "research.benchmarks.build_economic_cash_frames",
        "opportunity_benchmark": "PIT_EQUAL_WEIGHT_FULL_W3",
        "opportunity_benchmark_builder": "research.benchmarks.build_pit_equal_weight_benchmark",
        "security_level_return_imputation": "FORBIDDEN",
        "peer_return_imputation": "FORBIDDEN",
        "complete_case_denominator": "FORBIDDEN",
        "observed_subset_renormalization": "FORBIDDEN",
        "coverage_pass_fail_gate": "FORBIDDEN",
    }


def assign_basis_status(*, q_observed: bool, m_state: str) -> str:
    """Map source observability into one persistent full-W3 basis state."""

    if m_state not in _M_STATES:
        raise ValueError(f"ao_k0a_unknown_m_state:{m_state}")
    if not q_observed and m_state != M_OBSERVED:
        return Q_AND_M_MISSING
    if not q_observed:
        return Q_UNOBSERVED
    if m_state == M_WARMUP:
        return M_WARMUP
    if m_state == M_MISSING_HISTORY:
        return M_MISSING_HISTORY
    return ELIGIBLE_COMPLETE


def build_basis_status_frame(
    w3_rows: pd.DataFrame,
    *,
    q_observed_keys: Set[tuple[str, str]],
    m_state_by_key: Mapping[tuple[str, str, str], str],
) -> pd.DataFrame:
    """Left-preserve exact W3 rows and attach basis/arm observability states.

    `q_observed_keys` is keyed by (decision_date, security_id).  M is bound to
    the exact date-local listing identity via (decision_date, security_id,
    trading_item_id).  Absence of a Q key means Q_UNOBSERVED; absence of an M
    key is a contract error because it would silently turn missing history into
    an unspecified state.
    """

    required = {"decision_date", "security_id", "trading_item_id"}
    missing = required - set(w3_rows.columns)
    if missing:
        raise ValueError(f"ao_k0a_w3_columns_missing:{sorted(missing)}")
    out = w3_rows.loc[:, ["decision_date", "security_id", "trading_item_id"]].copy()
    if out.isna().any().any():
        raise ValueError("ao_k0a_w3_identity_null")
    if out.duplicated(list(required)).any():
        raise ValueError("ao_k0a_w3_duplicate_date_security_listing")

    q_flags: list[bool] = []
    m_states: list[str] = []
    statuses: list[str] = []
    q_actions: list[str] = []
    joint_actions: list[str] = []
    for row in out.itertuples(index=False):
        decision_date = str(row.decision_date)
        security_id = str(row.security_id)
        trading_item_id = str(row.trading_item_id)
        q_observed = (decision_date, security_id) in q_observed_keys
        m_key = (decision_date, security_id, trading_item_id)
        if m_key not in m_state_by_key:
            raise ValueError(f"ao_k0a_m_state_missing:{m_key}")
        m_state = str(m_state_by_key[m_key])
        status = assign_basis_status(q_observed=q_observed, m_state=m_state)
        q_flags.append(q_observed)
        m_states.append(m_state)
        statuses.append(status)
        q_actions.append(SELECTABLE if q_observed else ABSTENTION)
        joint_actions.append(
            SELECTABLE if (q_observed and m_state == M_OBSERVED) else ABSTENTION
        )

    out["q_observed"] = q_flags
    out["m_history_state"] = m_states
    out["basis_status"] = statuses
    out["q_arm_action"] = q_actions
    out["m_residual_arm_action"] = joint_actions
    out["q_plus_m_residual_arm_action"] = joint_actions
    out["abstention_risky_weight"] = np.where(
        out["basis_status"].eq(ELIGIBLE_COMPLETE), np.nan, 0.0
    )
    if len(out) != len(w3_rows):
        raise AssertionError("ao_k0a_denominator_row_loss")
    return out


def percentile_rank(values: pd.Series) -> pd.Series:
    """Standard date-local percentile rank: average ties, rank / observed N."""

    numeric = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)
    result = pd.Series(np.nan, index=values.index, dtype=float)
    observed = numeric.notna()
    if observed.any():
        result.loc[observed] = numeric.loc[observed].rank(method="average", pct=True)
    return result


def orthogonalize_cross_sections(
    frame: pd.DataFrame,
    *,
    q_column: str = "q_raw",
    m_column: str = "m_raw",
) -> pd.DataFrame:
    """Compute Q arm ranks and M-perp on independent date-local rank bases.

    Q rank uses every Q-observed W3 row.  For residualization, Q and M are both
    re-ranked on the exact Q∩M sample before OLS.  No complete-case denominator
    is exported and no missing row is dropped from the returned frame.
    """

    required = {"decision_date", "security_id", q_column, m_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"ao_k0a_orthogonal_columns_missing:{sorted(missing)}")
    forbidden = _FORBIDDEN_OUTCOME_COLUMNS & set(frame.columns)
    if forbidden:
        raise ValueError(f"ao_k0a_outcome_columns_forbidden:{sorted(forbidden)}")

    out = frame.copy()
    out["q_rank_arm"] = np.nan
    out["q_rank_joint"] = np.nan
    out["m_rank_joint"] = np.nan
    out["m_perp"] = np.nan
    out["orthogonal_intercept"] = np.nan
    out["orthogonal_slope"] = np.nan

    for _, index in out.groupby("decision_date", sort=True).groups.items():
        idx = pd.Index(index)
        q = pd.to_numeric(out.loc[idx, q_column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
        m = pd.to_numeric(out.loc[idx, m_column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
        out.loc[idx, "q_rank_arm"] = percentile_rank(q)

        joint = q.notna() & m.notna()
        joint_idx = idx[joint.to_numpy()]
        if len(joint_idx) == 0:
            continue
        q_joint = percentile_rank(q.loc[joint_idx])
        m_joint = percentile_rank(m.loc[joint_idx])
        out.loc[joint_idx, "q_rank_joint"] = q_joint
        out.loc[joint_idx, "m_rank_joint"] = m_joint

        x = q_joint.to_numpy(dtype=float)
        y = m_joint.to_numpy(dtype=float)
        design = np.column_stack((np.ones(len(x), dtype=float), x))
        beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        residual = y - design @ beta
        out.loc[joint_idx, "m_perp"] = residual
        out.loc[joint_idx, "orthogonal_intercept"] = float(beta[0])
        out.loc[joint_idx, "orthogonal_slope"] = float(beta[1])

        # Numerical assertions establish projection geometry, not a coverage
        # tolerance gate.  They never admit/drop a cohort.
        if not np.isclose(float(residual.sum()), 0.0, atol=1e-10):
            raise AssertionError("ao_k0a_residual_not_intercept_orthogonal")
        if not np.isclose(float(np.dot(residual, x)), 0.0, atol=1e-10):
            raise AssertionError("ao_k0a_residual_not_q_orthogonal")

    if len(out) != len(frame):
        raise AssertionError("ao_k0a_orthogonalization_row_loss")
    return out


def full_w3_breadth(*, selected_count: int, w3_eligible_count: int) -> float:
    """Return selected breadth against the immutable full-W3 denominator."""

    if selected_count < 0 or w3_eligible_count <= 0 or selected_count > w3_eligible_count:
        raise ValueError("ao_k0a_invalid_full_w3_breadth_counts")
    return float(selected_count) / float(w3_eligible_count)
