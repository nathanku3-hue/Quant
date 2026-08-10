from __future__ import annotations

from copy import deepcopy

import pytest

from research.alpha_pit_v1.contracts import (
    FAMILY_ID,
    PRIMARY_LABEL_SPEC_ID,
    RISK_SET_SPEC_ID,
)
from research.cycle_resonance_v1.contracts import IMPLEMENTATION_MANIFEST_SCHEMA
from research.cycle_resonance_v1.implementation_manifest import (
    MANIFEST_AUTHORITY_CLASS,
    freeze_implementation_manifest,
    verify_implementation_manifest,
)


def _payload() -> dict[str, object]:
    return {
        "schema_version": IMPLEMENTATION_MANIFEST_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": "CRV1_FIXTURE_IMPLEMENTATION_EXPLICIT_V1",
        "family_contract_sha256": "1" * 64,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "requested_observation_fields": [
            "market.close",
            "market.total_return_1d",
            "market.volume",
            "market.adv20",
            "market.realized_vol20",
            "market.sma20",
            "market.sma200",
            "fund.revenue_q",
            "fund.inventory_q",
            "fund.capex_q",
            "fund.gross_margin_q",
            "fund.operating_margin_q",
            "fund.cash_from_ops_q",
        ],
        "requested_expectation_measures": [
            "EPS_FY1",
            "EPS_FY2",
            "REVENUE_FY1",
            "REVENUE_FY2",
            "EPS_FY1_REVISION_30D",
            "EPS_FY1_REVISION_90D",
            "REVENUE_FY1_REVISION_30D",
            "REVENUE_FY1_REVISION_90D",
            "FORWARD_PE",
        ],
        "claim_topics": [
            "SUPPLY_CAPACITY",
            "INVENTORY_CHANNEL",
            "PRICING",
            "DEMAND",
            "UTILIZATION",
            "MARGIN",
            "GUIDANCE",
            "COMPETITION",
            "OTHER_RELEVANT_CYCLE",
        ],
        "coverage_policy": {
            "policy_id": "CRV1_FIXTURE_EXPLICIT_COVERAGE_V1",
            "minimum_active_clock_count": 4,
            "missing_expectations_action": "INSUFFICIENT",
        },
        "clock_transform_ids_and_hashes": {
            "SUPPLY_CAPACITY_CLOCK": "2" * 64,
            "INVENTORY_CLOCK": "3" * 64,
            "PRICING_CLOCK": "4" * 64,
            "UTILIZATION_MARGIN_CLOCK": "5" * 64,
            "EARNINGS_REVISIONS_CLOCK": "6" * 64,
            "EXPECTATION_GAP_CLOCK": "7" * 64,
        },
        "claim_interpreter_id": "CRV1_FIXTURE_RULE_INTERPRETER_V1",
        "claim_interpreter_sha256": "8" * 64,
        "ordered_sequence_spec": {
            "required_edges": [
                "SUPPLY_CAPACITY_CLOCK->INVENTORY_CLOCK",
                "INVENTORY_CLOCK->PRICING_CLOCK",
                "PRICING_CLOCK->UTILIZATION_MARGIN_CLOCK",
                "UTILIZATION_MARGIN_CLOCK->EARNINGS_REVISIONS_CLOCK",
                "EARNINGS_REVISIONS_CLOCK->EXPECTATION_GAP_CLOCK",
            ],
            "allowed_skipped_edges": [],
            "maximum_temporal_lag": {"unit": "calendar_days", "value": 365},
            "clock_inflection_definitions": {"definition_id": "CRV1_FIXTURE_INFLECTION_V1"},
            "contradiction_scoring": {"rule_id": "CRV1_FIXTURE_CONTRADICTION_V1"},
            "missing_clock_policy": {"rule_id": "CRV1_FIXTURE_MISSING_CLOCK_V1"},
        },
        "falsifier_spec": {
            "spec_id": "CRV1_FIXTURE_FALSIFIER_V1",
            "trigger": "NO_INCREMENTAL_I_PLUS_X_VALUE",
        },
        "model_class": "EXPLICIT_FIXTURE_LINEAR_RANKER",
        "model_hyperparameters": {"l2_penalty": 0.0},
        "training_window_rule": {"rule_id": "CRV1_FIXTURE_TRAINING_WINDOW_V1"},
        "calibration_method": "NONE",
        "ranking_rule": {"rule_id": "CRV1_FIXTURE_DESCENDING_SCORE_V1"},
        "search_family_id": "CRV1_FIXTURE_SEARCH_FAMILY_V1",
        "preregistered_search_budget": 5,
        "actual_trials_consumed_at_freeze": 2,
        "cost_assumptions": {"diagnostic_turnover_cost_bps": 10.0},
        "code_byte_manifest": {"manifest_sha256": "9" * 64},
    }


def test_explicit_manifest_freezes_deterministically_with_zero_evidence_authority() -> None:
    first = freeze_implementation_manifest(_payload())
    second = freeze_implementation_manifest(_payload())
    assert first == second
    assert first["authority_class"] == MANIFEST_AUTHORITY_CLASS
    assert first["financial_alpha_evidence"] == 0
    assert len(first["manifest_sha256"]) == 64
    verify_implementation_manifest(first)


def test_missing_scientific_parameter_fails_instead_of_using_a_code_default() -> None:
    payload = _payload()
    payload.pop("coverage_policy")
    with pytest.raises(ValueError, match="implementation_manifest_fields_invalid"):
        freeze_implementation_manifest(payload)

    payload = _payload()
    payload["ordered_sequence_spec"] = {
        key: value
        for key, value in payload["ordered_sequence_spec"].items()
        if key != "missing_clock_policy"
    }
    with pytest.raises(ValueError, match="ordered_sequence_spec_fields_invalid"):
        freeze_implementation_manifest(payload)


def test_manifest_rejects_family_semantic_drift_and_search_budget_overrun() -> None:
    payload = _payload()
    payload["risk_set_spec_id"] = "CURRENT_AOV_GROWTH_SCREEN_109"
    with pytest.raises(ValueError, match="risk_set_invalid"):
        freeze_implementation_manifest(payload)

    payload = _payload()
    payload["actual_trials_consumed_at_freeze"] = 6
    with pytest.raises(ValueError, match="actual_trials_exceed_preregistered_budget"):
        freeze_implementation_manifest(payload)


def test_sealed_manifest_tamper_fails_hash_verification() -> None:
    manifest = freeze_implementation_manifest(_payload())
    tampered = deepcopy(manifest)
    tampered["ranking_rule"]["rule_id"] = "TAMPERED"
    with pytest.raises(ValueError, match="hash_mismatch"):
        verify_implementation_manifest(tampered)
