from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.asymmetric_opportunity_v1.arms import (
    A5_Q_PLUS_M_PERP,
    arm_catalog,
    arm_formula_hashes,
    compute_arm_scores,
    refuse_empirical_ranking,
)
from research.asymmetric_opportunity_v1.label_packs import (
    default_m_clock_pack,
    default_q_clock_pack,
    refuse_outcome_join,
    seal_dual_label_packs,
    seal_label_pack,
)
from research.asymmetric_opportunity_v1.release_gates import (
    default_blocked_gates,
    machine_law,
    refuse_outcome_open,
)


def test_machine_law_blocks_evaluation_while_unset() -> None:
    law = machine_law(default_blocked_gates())
    assert law["runnable_evaluation"] is False
    assert law["blocked_field_count"] > 0
    assert law["outcome_open_authorized"] is False
    assert law["STATE"] == "S0_DESIGN_LOCKED_RELEASE_BLOCKED"


def test_refuse_outcome_open_and_join() -> None:
    with pytest.raises(ValueError, match="outcome_open_forbidden"):
        refuse_outcome_open(blocked_field_count=3)
    with pytest.raises(ValueError, match="outcome_open_forbidden"):
        refuse_outcome_open(blocked_field_count=0)
    with pytest.raises(ValueError, match="outcome_join_forbidden"):
        refuse_outcome_join()


def test_label_packs_seal_structure_without_join_while_cuts_blocked() -> None:
    dual = seal_dual_label_packs()
    assert dual["join_forbidden"] is True
    assert dual["both_fully_sealed"] is False
    q = dual["Q_CLOCK_LABEL_PACK"]
    m = dual["M_CLOCK_LABEL_PACK"]
    assert q["seal_status"] == "PACK_BLOCKED_UNSET"
    assert m["seal_status"] == "PACK_BLOCKED_UNSET"
    assert q["joined"] is False
    assert m["outcome_inspected"] is False
    # Structural fingerprint still content-addressed.
    assert len(q["structural_fingerprint_sha256"]) == 64


def test_full_seal_when_all_fields_bound_still_unjoined() -> None:
    pack = default_q_clock_pack()
    pack.right_tail_cut = "top_5pct"
    pack.catastrophe_cut = "bottom_5pct"
    pack.maturity_cutoff = "horizon_complete"
    pack.eligible_decision_date_list = "sha256:dates"
    pack.row_key_set = "sha256:rows"
    pack.label_source_receipt = "sha256:receipt"
    sealed = seal_label_pack(pack)
    assert sealed["seal_status"] == "SEALED_UNJOINED"
    assert sealed["sha256"]
    assert sealed["joined"] is False
    assert sealed["seal_means_open"] is False


def test_arm_formulas_compute_without_outcomes_and_a5_not_winner() -> None:
    catalog = arm_catalog()
    assert catalog["evaluation"] == "FORBIDDEN_UNTIL_CARVEOUT"
    assert catalog["constraints"]["a5_presumed_scientific_winner"] == "FORBIDDEN"
    a5 = next(a for a in catalog["arms"] if a["arm_id"] == A5_Q_PLUS_M_PERP)
    assert a5["presumed_winner"] is False
    assert refuse_empirical_ranking()["composite_trophy"] == "FORBIDDEN"
    assert len(arm_formula_hashes()) == 6

    frame = pd.DataFrame(
        {
            "decision_date": ["2026-01-02"] * 3,
            "security_id": ["A", "B", "C"],
            "q_raw": [1.0, 2.0, 3.0],
            "m_raw": [3.0, 1.0, 2.0],
        }
    )
    out = compute_arm_scores(frame)
    assert "score_A5_Q_PLUS_M_PERP" in out.columns
    assert out["score_A3_Q_PLUS_M"].notna().all()
    # Outcome columns forbidden.
    bad = frame.copy()
    bad["winner_label"] = True
    with pytest.raises(ValueError, match="outcome_columns_forbidden"):
        compute_arm_scores(bad)


def test_zero_blockers_still_requires_carveout_for_open() -> None:
    gates = {k: f"bound_{k}" for k in default_blocked_gates()}
    law = machine_law(gates)
    assert law["runnable_evaluation"] is True
    assert law["blocked_field_count"] == 0
    assert law["outcome_open_authorized"] is False
    with pytest.raises(ValueError, match="DEV-OPEN-1"):
        refuse_outcome_open(blocked_field_count=0)
