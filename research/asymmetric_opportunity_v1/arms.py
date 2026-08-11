"""OK-SBI-0 multi-arm formula contracts — implement formulas, never evaluate outcomes.

A5 residual is a probe, not a presumed scientific winner.  No post-label tuning,
no arm-specific K_t / denominator / tail / cost / lag.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from research.asymmetric_opportunity_v1.orthogonalization import (
    orthogonalize_cross_sections,
    percentile_rank,
)


A1_Q_NATIVE = "A1_Q_NATIVE"
A1C_Q_COMMON = "A1C_Q_COMMON"
A2_M_RAW = "A2_M_RAW"
A3_Q_PLUS_M = "A3_Q_PLUS_M"
A4_Q_TIMES_M = "A4_Q_TIMES_M"
A5_Q_PLUS_M_PERP = "A5_Q_PLUS_M_PERP"

ARM_IDS = (
    A1_Q_NATIVE,
    A1C_Q_COMMON,
    A2_M_RAW,
    A3_Q_PLUS_M,
    A4_Q_TIMES_M,
    A5_Q_PLUS_M_PERP,
)

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


@dataclass(frozen=True)
class ArmDefinition:
    arm_id: str
    definition: str
    role: str
    formula: str
    presumed_winner: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ARM_TABLE: tuple[ArmDefinition, ...] = (
    ArmDefinition(
        arm_id=A1_Q_NATIVE,
        definition="date-local Q rank on Q-observed",
        role="full/applicable Q baseline",
        formula="rank_date_local(Q | Q_observed)",
    ),
    ArmDefinition(
        arm_id=A1C_Q_COMMON,
        definition="Q re-ranked on Q∩M",
        role="paired conditional baseline",
        formula="rank_date_local(Q | Q_and_M_observed)",
    ),
    ArmDefinition(
        arm_id=A2_M_RAW,
        definition="M rank on common support",
        role="raw M",
        formula="rank_date_local(M | Q_and_M_observed)",
    ),
    ArmDefinition(
        arm_id=A3_Q_PLUS_M,
        definition="0.5·rank(Q)+0.5·rank(M)",
        role="additive raw",
        formula="0.5 * rank_Q_joint + 0.5 * rank_M_joint",
    ),
    ArmDefinition(
        arm_id=A4_Q_TIMES_M,
        definition="min(rank(Q),rank(M))",
        role="sparse conjunction",
        formula="min(rank_Q_joint, rank_M_joint)",
    ),
    ArmDefinition(
        arm_id=A5_Q_PLUS_M_PERP,
        definition="0.5·rank(Q)+0.5·rank(M⊥)",
        role="K0A residual incumbent probe",
        formula="0.5 * rank_Q_joint + 0.5 * percentile_rank(M_perp | joint)",
        presumed_winner=False,
    ),
)

# Low-DOF Q×M 2D surface template — bins fixed pre-open; no post-label change.
QX_M_SURFACE_TEMPLATE_V1 = {
    "template_id": "Q_X_M_2D_SURFACE_TEMPLATE_V1",
    "q_bins": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    "m_bins": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    "binning": "fixed_preopen_equal_width_rank",
    "post_label_bin_change": "FORBIDDEN",
    "outcome_input": False,
}

ARM_CONSTRAINTS = {
    "post_label_tuning": "FORBIDDEN",
    "arm_specific_k_t": "FORBIDDEN",
    "arm_specific_denominator": "FORBIDDEN",
    "arm_specific_tail_label_cost_lag": "FORBIDDEN",
    "extra_sector_size_beta_vol_neutralization_in_arm_scores": "FORBIDDEN",
    "a5_presumed_scientific_winner": "FORBIDDEN",
    "composite_trophy": "FORBIDDEN",
    "cross_horizon_leaderboard": "FORBIDDEN",
}


def arm_catalog() -> dict[str, Any]:
    return {
        "slice_id": "OK-SBI-0",
        "spec_version": "v1.2",
        "arms": [a.to_dict() for a in ARM_TABLE],
        "qx_m_surface_template": QX_M_SURFACE_TEMPLATE_V1,
        "constraints": ARM_CONSTRAINTS,
        "evaluation": "FORBIDDEN_UNTIL_CARVEOUT",
    }


def _canonical_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def arm_formula_hashes() -> dict[str, str]:
    return {a.arm_id: _canonical_hash(a.to_dict()) for a in ARM_TABLE}


def compute_arm_scores(
    frame: pd.DataFrame,
    *,
    q_column: str = "q_raw",
    m_column: str = "m_raw",
) -> pd.DataFrame:
    """Compute arm score columns only.  Never ranks empirically for trophies.

    Requires numeric Q and M inputs already present.  Refuses outcome columns.
    Does not select portfolios or report performance.
    """

    forbidden = _FORBIDDEN_OUTCOME_COLUMNS & set(frame.columns)
    if forbidden:
        raise ValueError(f"ok_sbi_0_outcome_columns_forbidden:{sorted(forbidden)}")

    base = orthogonalize_cross_sections(frame, q_column=q_column, m_column=m_column)
    out = base.copy()
    out["score_A1_Q_NATIVE"] = out["q_rank_arm"]
    out["score_A1C_Q_COMMON"] = out["q_rank_joint"]
    out["score_A2_M_RAW"] = out["m_rank_joint"]
    out["score_A3_Q_PLUS_M"] = 0.5 * out["q_rank_joint"] + 0.5 * out["m_rank_joint"]
    out["score_A4_Q_TIMES_M"] = np.minimum(out["q_rank_joint"], out["m_rank_joint"])

    # A5: 0.5 * rank_Q_joint + 0.5 * rank(M_perp) on the joint sample, date-local.
    out["score_A5_Q_PLUS_M_PERP"] = np.nan
    for _, index in out.groupby("decision_date", sort=True).groups.items():
        idx = pd.Index(index)
        joint = out.loc[idx, "m_perp"].notna()
        joint_idx = idx[joint.to_numpy()]
        if len(joint_idx) == 0:
            continue
        m_perp_rank = percentile_rank(out.loc[joint_idx, "m_perp"])
        out.loc[joint_idx, "score_A5_Q_PLUS_M_PERP"] = (
            0.5 * out.loc[joint_idx, "q_rank_joint"] + 0.5 * m_perp_rank
        )

    if len(out) != len(frame):
        raise AssertionError("ok_sbi_0_arm_score_row_loss")
    return out


def refuse_empirical_ranking() -> dict[str, Any]:
    return {
        "empirical_arm_performance": "FORBIDDEN",
        "composite_trophy": "FORBIDDEN",
        "overall_winner": "FORBIDDEN",
        "cross_horizon_leaderboard": "FORBIDDEN",
        "a5_presumed_winner": False,
    }
