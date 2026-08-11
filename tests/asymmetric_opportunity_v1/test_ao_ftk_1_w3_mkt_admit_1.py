"""AO-FTK-1-W3-MKT-ADMIT-1 acceptance tests.

Custody admit + D2 preflight only. No debit. No economic L5.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1 import ao_ftk_1_w3_mkt_admit_1 as m


REPO = Path(__file__).resolve().parents[2]


def test_authority_receipts_landed() -> None:
    for rel in (m.SURVEY_REL, m.ADMIT_REL, m.D2_REL, m.SUMMARY_REL):
        assert (REPO / rel).is_file(), rel


def test_aov_only_panel_cannot_pass_full_w3_admit() -> None:
    aov = {
        "candidate_id": "AOV_HISTORICAL_MARKET_PRODUCTQUERY_104",
        "full_w3_compatible": False,
        "status": "NOT_FULL_W3",
        "security_count": {"entity_count": 104},
        "admitted_as_full_w3": True,
    }
    with pytest.raises(m.W3MktAdmitError, match="AOV_104_AS_FULL_W3"):
        m.assert_aov_cannot_pass_full_w3_admit(aov)

    survey = m.survey_candidates(REPO)
    aov_cands = [
        c for c in survey["candidates"] if "AOV" in str(c.get("candidate_id", "")).upper()
    ]
    assert aov_cands
    for c in aov_cands:
        assert c.get("full_w3_compatible") is False
        assert c.get("status") in {"NOT_FULL_W3", "MISSING_OR_NOT_PRESENT"}


def test_proxy_full_w3_fails_closed() -> None:
    with pytest.raises(m.W3MktAdmitError, match="AOV_104_AS_FULL_W3"):
        m.refuse_aov_as_full_w3()
    with pytest.raises(m.W3MktAdmitError, match="AOV_104_AS_FULL_W3"):
        m.refuse_proxy_full_w3()


def test_d2_cannot_be_green_without_admit_receipt() -> None:
    assert m.d2_cannot_be_green_without_admit(None) == "RED"
    assert m.d2_cannot_be_green_without_admit({"admitted": False}) == "RED"
    d2 = m.evaluate_d2_preflight(None)
    assert d2["D2_PRECHECK"] == "RED"
    assert "NO_ADMIT_RECEIPT" in d2["blockers"]
    assert d2["debit_allowed_now"] is False
    assert d2["l5_ready_recommendation"] is False


def test_symmetry_required_for_green() -> None:
    admit = m.build_admit_receipt(repo=REPO)
    if not admit.get("admitted"):
        pytest.skip("Full-W3 custody not present in this environment")
    d2_bad = m.evaluate_d2_preflight(admit, symmetry_ftk_w3=False)
    assert d2_bad["D2_PRECHECK"] == "RED"
    assert "SYMMETRY_FTK_W3_FALSE" in d2_bad["blockers"]
    d2_ok = m.evaluate_d2_preflight(admit, symmetry_ftk_w3=True)
    assert d2_ok["D2_PRECHECK"] == "GREEN"
    assert d2_ok["symmetry"]["same_return_convention_ftk_and_w3"] is True


def test_no_debit_and_no_economic_l5_in_slice() -> None:
    with pytest.raises(m.W3MktAdmitError, match="DEBIT_LAST_TRIAL_THIS_TURN"):
        m.refuse_debit()
    with pytest.raises(m.W3MktAdmitError, match="ECONOMIC_L5_RUN_THIS_TURN"):
        m.refuse_economic_l5_run()

    admit = json.loads((REPO / m.ADMIT_REL).read_text(encoding="utf-8"))
    d2 = json.loads((REPO / m.D2_REL).read_text(encoding="utf-8"))
    assert admit["material_trial_debit_this_turn"] is False
    assert admit["economic_l5_authorized"] is False
    assert d2["debit_allowed_now"] is False
    assert d2["economic_l5_authorized"] is False
    assert d2["material_trials_remaining"] == 1
    assert admit.get("financial_alpha_evidence") == 0
    assert d2.get("financial_alpha_evidence") == 0


def test_full_w3_admit_and_d2_green_on_authority_worktree() -> None:
    survey = m.survey_candidates(REPO)
    assert "PREBREAKOUT_W3_DATE_LOCAL_MARKET_CORPUS" in survey["lawful_full_w3_candidates"]
    admit = m.build_admit_receipt(survey, repo=REPO)
    assert admit["admitted"] is True
    assert admit["full_w3_compatible"] is True
    assert admit["aov_104_promoted"] is False
    assert admit["proxy_full_w3"] is False
    assert int(admit["security_count"]) >= 1000
    d2 = m.evaluate_d2_preflight(admit)
    assert d2["D2_PRECHECK"] == "GREEN"
    assert d2["blockers"] == []
    assert d2["l5_ready_recommendation"] is True
    assert d2["debit_allowed_now"] is False
    terminal = m.classify_terminal(admit, d2)
    assert terminal == "W3_MKT_ADMIT_PASS_D2_GREEN"


def test_landed_receipts_consistent() -> None:
    survey = json.loads((REPO / m.SURVEY_REL).read_text(encoding="utf-8"))
    admit = json.loads((REPO / m.ADMIT_REL).read_text(encoding="utf-8"))
    d2 = json.loads((REPO / m.D2_REL).read_text(encoding="utf-8"))
    assert survey["work_id"] == m.WORK_ID
    assert admit["admitted"] is True
    assert d2["D2_PRECHECK"] == "GREEN"
    assert d2["full_w3_admitted"] is True
    assert d2["material_trials_remaining"] == 1
    # GREEN requires admit
    assert admit["receipt_id"] == d2["admit_receipt_id"] or d2["admit_receipt_id"] == admit.get(
        "receipt_id"
    )
