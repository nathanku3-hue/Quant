from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.asymmetric_opportunity_v1.orthogonalization import (
    ABSTENTION,
    ELIGIBLE_COMPLETE,
    M_MISSING_HISTORY,
    M_OBSERVED,
    M_WARMUP,
    Q_AND_M_MISSING,
    Q_UNOBSERVED,
    SELECTABLE,
    assign_basis_status,
    build_basis_status_frame,
    contract_semantics,
    full_w3_breadth,
    orthogonalize_cross_sections,
)


def test_missingness_is_persistent_state_not_coverage_gate() -> None:
    assert assign_basis_status(q_observed=True, m_state=M_OBSERVED) == ELIGIBLE_COMPLETE
    assert assign_basis_status(q_observed=False, m_state=M_OBSERVED) == Q_UNOBSERVED
    assert assign_basis_status(q_observed=True, m_state=M_WARMUP) == M_WARMUP
    assert assign_basis_status(q_observed=True, m_state=M_MISSING_HISTORY) == M_MISSING_HISTORY
    assert assign_basis_status(q_observed=False, m_state=M_WARMUP) == Q_AND_M_MISSING
    assert assign_basis_status(q_observed=False, m_state=M_MISSING_HISTORY) == Q_AND_M_MISSING
    semantics = contract_semantics()
    assert semantics["coverage_pass_fail_gate"] == "FORBIDDEN"
    assert semantics["complete_case_denominator"] == "FORBIDDEN"
    assert semantics["observed_subset_renormalization"] == "FORBIDDEN"


def test_basis_status_frame_preserves_every_w3_row_and_arm_specific_abstention() -> None:
    w3 = pd.DataFrame(
        [
            ("2026-01-02", "CIQSEC:IQ1", "101"),
            ("2026-01-02", "CIQSEC:IQ2", "102"),
            ("2026-01-02", "CIQSEC:IQ3", "103"),
            ("2026-01-02", "CIQSEC:IQ4", "104"),
        ],
        columns=["decision_date", "security_id", "trading_item_id"],
    )
    q_observed = {
        ("2026-01-02", "CIQSEC:IQ1"),
        ("2026-01-02", "CIQSEC:IQ2"),
        ("2026-01-02", "CIQSEC:IQ3"),
    }
    m_states = {
        ("2026-01-02", "CIQSEC:IQ1", "101"): M_OBSERVED,
        ("2026-01-02", "CIQSEC:IQ2", "102"): M_MISSING_HISTORY,
        ("2026-01-02", "CIQSEC:IQ3", "103"): M_WARMUP,
        ("2026-01-02", "CIQSEC:IQ4", "104"): M_OBSERVED,
    }
    out = build_basis_status_frame(
        w3,
        q_observed_keys=q_observed,
        m_state_by_key=m_states,
    )

    assert len(out) == len(w3)
    assert out["security_id"].tolist() == w3["security_id"].tolist()
    assert out["basis_status"].tolist() == [
        ELIGIBLE_COMPLETE,
        M_MISSING_HISTORY,
        M_WARMUP,
        Q_UNOBSERVED,
    ]
    # Q keeps its observability advantage; it is not forced to Q∩M.
    assert out["q_arm_action"].tolist() == [SELECTABLE, SELECTABLE, SELECTABLE, ABSTENTION]
    assert out["m_residual_arm_action"].tolist() == [SELECTABLE, ABSTENTION, ABSTENTION, ABSTENTION]
    assert out["q_plus_m_residual_arm_action"].tolist() == [SELECTABLE, ABSTENTION, ABSTENTION, ABSTENTION]
    assert out.loc[out["basis_status"].ne(ELIGIBLE_COMPLETE), "abstention_risky_weight"].eq(0.0).all()


def test_missing_m_state_cannot_be_silently_inferred_or_dropped() -> None:
    w3 = pd.DataFrame(
        [("2026-01-02", "CIQSEC:IQ1", "101")],
        columns=["decision_date", "security_id", "trading_item_id"],
    )
    with pytest.raises(ValueError, match="ao_k0a_m_state_missing"):
        build_basis_status_frame(w3, q_observed_keys=set(), m_state_by_key={})


def test_q_rank_uses_all_q_observed_but_residualization_reranks_on_joint_sample() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2026-01-02"] * 4,
            "security_id": ["A", "B", "C", "D"],
            "q_raw": [10.0, 20.0, 30.0, 40.0],
            "m_raw": [3.0, 1.0, np.nan, 2.0],
        }
    )
    out = orthogonalize_cross_sections(frame)
    by_id = out.set_index("security_id")

    assert by_id.loc["B", "q_rank_arm"] == pytest.approx(0.50)
    assert by_id.loc["C", "q_rank_arm"] == pytest.approx(0.75)
    assert np.isnan(by_id.loc["C", "q_rank_joint"])
    # Joint sample is A/B/D, so B is re-ranked 2/3 rather than retaining 1/2.
    assert by_id.loc["B", "q_rank_joint"] == pytest.approx(2.0 / 3.0)
    assert by_id.loc["A", "m_rank_joint"] == pytest.approx(1.0)
    assert by_id.loc["B", "m_rank_joint"] == pytest.approx(1.0 / 3.0)
    assert by_id.loc["D", "m_rank_joint"] == pytest.approx(2.0 / 3.0)

    joint = out["m_perp"].notna()
    residual = out.loc[joint, "m_perp"].to_numpy(dtype=float)
    q_joint = out.loc[joint, "q_rank_joint"].to_numpy(dtype=float)
    assert residual.sum() == pytest.approx(0.0, abs=1e-10)
    assert float(np.dot(residual, q_joint)) == pytest.approx(0.0, abs=1e-10)


def test_orthogonalization_is_outcome_blind() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2026-01-02"],
            "security_id": ["A"],
            "q_raw": [1.0],
            "m_raw": [2.0],
            "winner_label": [True],
        }
    )
    with pytest.raises(ValueError, match="ao_k0a_outcome_columns_forbidden"):
        orthogonalize_cross_sections(frame)


def test_breadth_is_full_w3_not_complete_case() -> None:
    assert full_w3_breadth(selected_count=368, w3_eligible_count=4600) == pytest.approx(0.08)
    assert full_w3_breadth(selected_count=368, w3_eligible_count=3680) == pytest.approx(0.10)
    # The contract fixes the first denominator; the second number is shown only
    # to prove why observed-subset renormalization is a different statistic.
    assert contract_semantics()["breadth_denominator"] == "ALL_W3_ELIGIBLE_SECURITIES"


def test_return_imputation_and_peer_fill_are_forbidden() -> None:
    semantics = contract_semantics()
    assert semantics["security_level_return_imputation"] == "FORBIDDEN"
    assert semantics["peer_return_imputation"] == "FORBIDDEN"
    assert semantics["abstention_risky_weight"] == 0.0
    assert semantics["residual_capital"] == "ECONOMIC_CASH"
    assert semantics["opportunity_benchmark"] == "PIT_EQUAL_WEIGHT_FULL_W3"
