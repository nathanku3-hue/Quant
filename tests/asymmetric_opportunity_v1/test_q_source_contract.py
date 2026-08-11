from __future__ import annotations

import pytest

from research.asymmetric_opportunity_v1.q_source_contract import (
    MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES,
    Q_AMENDED_BOUND,
    Q_GF_BOUND,
    Q_MINIMAL_AMENDMENT_REQUIRED,
    Q_SOURCE_BLOCKED,
    QSourceContractV1,
    conceptual_candidate_contract,
    evaluate_q_source_feasibility,
    primitive_from_mapping,
    required_field_names,
    validate_amendment_budget,
)


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
    packet = evaluate_q_source_feasibility()
    assert packet["Q_feasibility"] == Q_SOURCE_BLOCKED
    assert packet["stop_q_binding"] is True
    assert packet["q_amendment_cycles_used"] == 0
    contract = packet["contract"]
    assert contract["numeric_q_status"] == "NOT_BOUND_S0"
    assert "RevGrowth_12m" in contract["unbound_inventory"]
    assert "ROIC" in contract["unbound_inventory"]


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
