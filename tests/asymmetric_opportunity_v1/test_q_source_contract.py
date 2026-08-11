from __future__ import annotations

from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1.q_source_contract import (
    MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES,
    Q_AMENDED_BOUND,
    Q_GF_BOUND,
    Q_MINIMAL_AMENDMENT_REQUIRED,
    Q_SOURCE_BLOCKED,
    QSourceContractV1,
    audit_admitted_custody_for_q,
    conceptual_candidate_contract,
    evaluate_q_source_feasibility,
    primitive_from_mapping,
    required_field_names,
    validate_amendment_budget,
)

REPO = Path(__file__).resolve().parents[2]


def _fully_bound_primitive(primitive_id: str = "RevGrowth_12m"):
    return primitive_from_mapping(
        {
            name: f"bound_{name}_{primitive_id}"
            for name in required_field_names()
        }
        | {
            "primitive_id": primitive_id,
            "provider_source_object": "ADMITTED_SOURCE_OBJECT",
            "exact_field_identifier": f"field::{primitive_id}",
            "source_receipt_hash": "a" * 64,
            "no_bridge_proof": "no_ticker_permno_entity_bridge",
        }
    )


def test_conceptual_candidate_is_source_blocked_not_invented() -> None:
    contract = conceptual_candidate_contract()
    packet = evaluate_q_source_feasibility(
        contract, repo_root=REPO, include_custody_audit=False
    )
    assert packet["Q_feasibility"] == Q_SOURCE_BLOCKED
    assert packet["stop_q_binding"] is True
    assert packet["q_amendment_cycles_used"] == 0
    body = packet["contract"]
    assert body["numeric_q_status"] == "NOT_BOUND_S0"
    assert "RevGrowth_12m" in body["unbound_inventory"]
    assert "ROIC" in body["unbound_inventory"]


def test_admitted_custody_audit_blocks_without_inventing_roic() -> None:
    attempt = audit_admitted_custody_for_q(repo_root=REPO)
    assert attempt["Q_feasibility"] == Q_SOURCE_BLOCKED
    audit = attempt["audit"]
    assert audit["q_amendment_cycles_used"] == 0
    assert audit["amendment_consumed"] is False
    assert audit["q_source_binding_hash"] == "BLOCKED_UNSET"
    assert audit["has_roic_metric"] is False
    assert audit["outcome_input"] is False
    assert audit["financial_alpha_evidence"] == 0
    assert any("roic_no_admitted_metric" in b for b in audit["blockers"])
    assert any(
        "trading_item" in b for b in audit["blockers"]
    ) or audit["s0_has_trading_item"] is False
    # No silent bridge language in contract bind values.
    for prim in attempt["contract"].primitives:
        blob = " ".join(str(v) for v in prim.to_dict().values()).upper()
        assert "RULE100_ARTIFACT_BRIDGE" not in blob
        assert "SYNTHETIC_FILL" not in blob


def test_evaluate_with_custody_audit_stays_blocked() -> None:
    packet = evaluate_q_source_feasibility(repo_root=REPO, include_custody_audit=True)
    assert packet["Q_feasibility"] == Q_SOURCE_BLOCKED
    assert packet["q_source_binding_hash"] == "BLOCKED_UNSET"
    assert packet["financial_alpha_evidence"] == 0
    assert "custody_audit" in packet
    assert packet["custody_audit"]["numeric_q_status"] == "NOT_BOUND_S0"


def test_fully_bound_without_amendment_is_gf_bound() -> None:
    contract = QSourceContractV1(
        primitives=[
            _fully_bound_primitive("RevGrowth_12m"),
            _fully_bound_primitive("ROIC"),
        ]
    )
    assert contract.feasibility_verdict() == Q_GF_BOUND
    assert evaluate_q_source_feasibility(contract)["Q_feasibility"] == Q_GF_BOUND


def test_single_amendment_then_bound_is_amended_bound() -> None:
    contract = QSourceContractV1(
        primitives=[
            _fully_bound_primitive("RevGrowth_12m"),
            _fully_bound_primitive("ROIC"),
        ]
    )
    contract.record_amendment(reason="bind_exact_ciq_fields")
    assert contract.q_amendment_cycles_used == 1
    assert contract.feasibility_verdict() == Q_AMENDED_BOUND


def test_second_amendment_forbidden() -> None:
    contract = conceptual_candidate_contract()
    contract.record_amendment(reason="first")
    with pytest.raises(ValueError, match="second_q_redesign_forbidden"):
        contract.record_amendment(reason="second")
    with pytest.raises(ValueError, match="second_q_redesign_forbidden"):
        validate_amendment_budget(MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES + 1)


def test_near_complete_map_requests_minimal_amendment() -> None:
    # Exact field present but one supporting field still open → amendment path.
    p = _fully_bound_primitive("RevGrowth_12m")
    raw = p.to_dict()
    raw["unit_currency_law"] = "BLOCKED_UNSET"
    raw["provider_source_object"] = "ADMITTED_SOURCE_OBJECT"
    raw["exact_field_identifier"] = "field::RevGrowth_12m"
    contract = QSourceContractV1(primitives=[primitive_from_mapping(raw)])
    assert contract.feasibility_verdict() == Q_MINIMAL_AMENDMENT_REQUIRED
