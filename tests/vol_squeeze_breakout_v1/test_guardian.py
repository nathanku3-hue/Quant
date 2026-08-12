from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta

import pytest

from core.gv_fs0_canonical import domain_hash
from research.vol_squeeze_breakout_v1.contracts import (
    BOOTSTRAP_BLOCK_LENGTH,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    CONFIRMATION_ROLE_ID,
    FAMILY_ID,
    GUARDIAN_CONTRACT_SHA256,
    IMPLEMENTATION_ID,
    MATURED_DATE_RECORD_SCHEMA,
    MATURITY_STATUS,
    MIN_MATURED_PRIMARY_DECISION_DATES,
    OUTCOME_AUTHORITY_CLASS,
    PRIMARY_LABEL_SPEC_ID,
    SEARCH_FAMILY_ID,
    validate_vsb_contract,
)
from research.vol_squeeze_breakout_v1.guardian import (
    evaluate_vsb_confirmation,
    verify_confirmation_result,
)


def _record(index: int, *, support_count: int = 20, hit_count: int = 2) -> dict[str, object]:
    decision_date = (date(2026, 9, 1) + timedelta(days=index)).isoformat()
    return {
        "schema_version": MATURED_DATE_RECORD_SCHEMA,
        "confirmation_role_id": CONFIRMATION_ROLE_ID,
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
        "decision_session_date": decision_date,
        "prediction_batch_sha256": domain_hash("VSB:TEST:PREDICTION", {"index": index}),
        "outcome_evaluation_receipt_sha256": domain_hash("VSB:TEST:OUTCOME", {"index": index}),
        "prediction_before_label_open": True,
        "maturity_status": MATURITY_STATUS,
        "outcome_authority_class": OUTCOME_AUTHORITY_CLASS,
        "custody_violation_count": 0,
        "risk_set_count": 100,
        "support_count": support_count,
        "winner_count": 5,
        "winner_support_hit_count": hit_count,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }


def test_guardian_contract_freezes_confirmation_only_gate() -> None:
    validate_vsb_contract()
    assert CONFIRMATION_ROLE_ID == "VSB_CONFIRMATION_v1"
    assert MIN_MATURED_PRIMARY_DECISION_DATES == 20
    assert BOOTSTRAP_BLOCK_LENGTH == 10
    assert BOOTSTRAP_REPLICATES == 10000
    assert BOOTSTRAP_SEED == 20260810
    assert len(GUARDIAN_CONTRACT_SHA256) == 64


def test_guardian_refuses_early_peeking_before_twenty_matured_dates() -> None:
    result = evaluate_vsb_confirmation([_record(index) for index in range(19)])
    verify_confirmation_result(result)
    assert result["gate_status"] == "BLOCKED_INSUFFICIENT_MATURED_PRIMARY_DATES"
    assert result["gate_passed"] is None
    assert result["matured_primary_decision_dates"] == 19
    assert result["winner_recall_10d"] is None
    assert result["support_breadth"] is None
    assert result["winner_recall_lift_10d"] is None
    assert result["bootstrap_lower_bound_80pct"] is None
    assert result["bootstrap_upper_bound_80pct"] is None


def test_guardian_passes_only_when_lift_and_bootstrap_lower_bound_both_exceed_one() -> None:
    records = [_record(index, support_count=20, hit_count=2) for index in range(20)]
    first = evaluate_vsb_confirmation(records)
    second = evaluate_vsb_confirmation(records)
    assert first == second
    verify_confirmation_result(first)
    assert first["gate_status"] == "CONFIRMATION_GATE_PASS"
    assert first["gate_passed"] is True
    assert float(first["winner_recall_10d"]) == pytest.approx(0.4)
    assert float(first["support_breadth"]) == pytest.approx(0.2)
    assert float(first["winner_recall_lift_10d"]) == pytest.approx(2.0)
    assert float(first["bootstrap_lower_bound_80pct"]) == pytest.approx(2.0)
    assert first["retune_authority"] == "NONE"
    assert first["prebreakout_authority"] == "NONE"
    assert first["financial_alpha_evidence"] == 0
    assert first["capital_authority"] == "NONE"


def test_guardian_fails_strict_greater_than_one_boundary() -> None:
    result = evaluate_vsb_confirmation([_record(index, support_count=20, hit_count=1) for index in range(20)])
    verify_confirmation_result(result)
    assert result["gate_status"] == "CONFIRMATION_GATE_FAIL"
    assert result["gate_passed"] is False
    assert float(result["winner_recall_lift_10d"]) == pytest.approx(1.0)
    assert float(result["bootstrap_lower_bound_80pct"]) == pytest.approx(1.0)


def test_guardian_rejects_custody_identity_and_top5_label_drift() -> None:
    base = _record(0)
    mutations = (
        ({"implementation_id": "RETUNED_M0"}, "implementation_invalid"),
        ({"guardian_contract_sha256": "f" * 64}, "guardian_contract_invalid"),
        ({"prediction_before_label_open": False}, "prediction_before_label_proof_required"),
        ({"custody_violation_count": 1}, "custody_violation"),
        ({"winner_count": 4}, "winner_count_not_frozen_top5"),
        ({"outcome_authority_class": "DISCOVERY_VISIBLE"}, "outcome_authority_invalid"),
    )
    for patch, error in mutations:
        mutated = {**base, **patch}
        with pytest.raises(ValueError, match=error):
            evaluate_vsb_confirmation([mutated] * 20)


def test_guardian_rejects_duplicate_dates_and_result_tamper() -> None:
    records = [_record(index) for index in range(20)]
    duplicate = deepcopy(records)
    duplicate[-1]["decision_session_date"] = duplicate[0]["decision_session_date"]
    with pytest.raises(ValueError, match="duplicate_decision_date"):
        evaluate_vsb_confirmation(duplicate)

    result = evaluate_vsb_confirmation(records)
    tampered = deepcopy(result)
    tampered["winner_recall_lift_10d"] = "999"
    with pytest.raises(ValueError, match="result_hash_mismatch"):
        verify_confirmation_result(tampered)
