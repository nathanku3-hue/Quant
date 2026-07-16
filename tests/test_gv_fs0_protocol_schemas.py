from __future__ import annotations

from copy import deepcopy

import pytest

from gv_fs0.protocol.definitions import (
    MANDATORY_CHECKS,
    SCHEMA_NAMES,
    build_certification_failure_registry,
    build_operational_error_registry,
    build_schema_bundle,
    project_verifier_input,
)
from gv_fs0.protocol.validation import (
    ProtocolValidationError,
    validate_all_definitions,
    validate_certification_status,
    validate_failure_bindings,
    validate_instance,
)


def _infrastructure_attempt(ordinal: int, code: str = "VERIFIER_TIMEOUT") -> dict[str, object]:
    return {
        "ordinal": ordinal,
        "outcome": "INFRASTRUCTURE_FAILURE",
        "verifier_result_hash": None,
        "controller_failure_code": code,
    }


def _rejected_result() -> dict[str, object]:
    return {
        "schema_version": "GV_FS0_VERIFIER_RESULT_V1",
        "protocol_binding": {"protocol_id": "GV_FS0_PROTOCOL_V1", "protocol_version": "V1"},
        "fixture_binding": {"fixture_id": "FIXTURE:001", "fixture_hash": "1" * 64},
        "decision_binding": {"decision_id": "DECISION:001", "decision_hash": "2" * 64},
        "verifier_input_hash": "3" * 64,
        "verifier_status": "REJECTED",
        "reconstructed_economic_payload": None,
        "reconstructed_economic_payload_hash": None,
        "failure_codes": ["VERIFIER_REJECTED"],
    }


def test_all_twelve_draft_2020_12_schemas_are_closed_and_valid() -> None:
    validate_all_definitions()
    bundle = build_schema_bundle()
    assert tuple(bundle["schemas"]) == SCHEMA_NAMES
    assert len(bundle["schemas"]) == 12
    for name, schema in bundle["schemas"].items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"] == name
        assert schema["$id"].endswith(name)


def test_verifier_result_conditional_nullability_is_enforced() -> None:
    rejected = _rejected_result()
    validate_instance("gv_fs0_verifier_result_v1", rejected)

    invalid_rejected = deepcopy(rejected)
    invalid_rejected["failure_codes"] = []
    with pytest.raises(ProtocolValidationError):
        validate_instance("gv_fs0_verifier_result_v1", invalid_rejected)

    invalid_reconstructed = deepcopy(rejected)
    invalid_reconstructed.update(
        {
            "verifier_status": "RECONSTRUCTED",
            "failure_codes": [],
            "reconstructed_economic_payload": None,
            "reconstructed_economic_payload_hash": "4" * 64,
        }
    )
    with pytest.raises(ProtocolValidationError):
        validate_instance("gv_fs0_verifier_result_v1", invalid_reconstructed)


def test_exact_attempt_ordinals_and_bindings_are_schema_valid() -> None:
    validate_instance("gv_fs0_verifier_attempt_v1", _infrastructure_attempt(1))
    validate_instance("gv_fs0_verifier_attempt_v1", _infrastructure_attempt(2))
    invalid = _infrastructure_attempt(1)
    invalid["verifier_result_hash"] = "a" * 64
    with pytest.raises(ProtocolValidationError):
        validate_instance("gv_fs0_verifier_attempt_v1", invalid)


def test_blocked_evidence_is_nonpublishable_and_not_a_certified_result() -> None:
    blocked = {
        "schema_version": "GV_FS0_BLOCKED_EVIDENCE_V1",
        "protocol_id": "GV_FS0_PROTOCOL_V1",
        "publishable": False,
        "certification_status": "BLOCKED",
        "decision_id": "DECISION:001",
        "failure_bindings": [
            {"check": "independent_reconstruction_passed", "outcome": "UNKNOWN", "code": "VERIFIER_TIMEOUT"}
        ],
        "verifier_attempts": [_infrastructure_attempt(1), _infrastructure_attempt(2)],
    }
    validate_instance("gv_fs0_blocked_evidence_v1", blocked)
    with pytest.raises(ProtocolValidationError):
        validate_instance("gv_fs0_certified_decision_result_v1", blocked)


def test_partial_final_bundle_is_schema_invalid() -> None:
    partial = {
        "schema_version": "GV_FS0_CERTIFIED_BUNDLE_V1",
        "protocol_id": "GV_FS0_PROTOCOL_V1",
        "protocol_version": "V1",
        "currency": "USD",
        "open_result": {},
        "bundle_hash": "a" * 64,
        "bundle_id": "BUNDLE_" + "a" * 64,
    }
    with pytest.raises(ProtocolValidationError):
        validate_instance("gv_fs0_certified_bundle_v1", partial)


def test_unknown_fields_are_rejected() -> None:
    result = _rejected_result()
    result["runtime_duration"] = 1
    with pytest.raises(ProtocolValidationError):
        validate_instance("gv_fs0_verifier_result_v1", result)


def test_registries_are_separate_sorted_and_hashed() -> None:
    failure = build_certification_failure_registry()
    operational = build_operational_error_registry()
    failure_codes = [entry["code"] for entry in failure["registry"]["entries"]]
    operational_codes = [entry["code"] for entry in operational["registry"]["entries"]]
    assert failure_codes == sorted(failure_codes)
    assert operational_codes == sorted(operational_codes)
    assert not set(failure_codes).intersection(operational_codes)
    assert failure["registry_hash"] != operational["registry_hash"]


def test_failure_bindings_require_exact_tri_state_coverage_and_order() -> None:
    checks = {check: "TRUE" for check in MANDATORY_CHECKS}
    checks["independent_reconstruction_passed"] = "UNKNOWN"
    checks["canonical_hash_reproduced"] = "UNKNOWN"
    bindings = [
        {"check": "independent_reconstruction_passed", "outcome": "UNKNOWN", "code": "VERIFIER_TIMEOUT"},
        {"check": "canonical_hash_reproduced", "outcome": "UNKNOWN", "code": "VERIFIER_TIMEOUT"},
    ]
    validate_failure_bindings(checks, bindings, emitter_by_code={"VERIFIER_TIMEOUT": "CONTROLLER"})
    validate_certification_status(checks, "BLOCKED")

    with pytest.raises(ProtocolValidationError):
        validate_failure_bindings({**checks, "independent_reconstruction_passed": "TRUE"}, bindings)
    with pytest.raises(ProtocolValidationError):
        validate_certification_status(checks, "CERTIFIED")


def test_all_true_is_the_only_certified_state() -> None:
    checks = {check: "TRUE" for check in MANDATORY_CHECKS}
    validate_failure_bindings(checks, [])
    validate_certification_status(checks, "CERTIFIED")


def test_full_envelope_projection_retains_renames_transforms_and_omits() -> None:
    fixture = {
        "protocol_id": "GV_FS0_PROTOCOL_V1",
        "fixture_id": "FIXTURE:001",
        "fixture_hash": "1" * 64,
        "currency": "USD",
        "initial_cash": "1000",
        "prices": [{"security_id": "ABC", "session": "2026-07-17", "price_timestamp": "2026-07-17T00:00:00.000000Z", "close_price": "10", "source_sequence": 0}],
        "source_intents": [{"intent_type": "VALUATION_INSTRUCTION", "source_sequence": 0}],
    }
    decision = {
        "decision_id": "DECISION:001",
        "decision_hash": "2" * 64,
        "authority_tier": "MANUAL_OWNER_PAPER",
        "action": "NO_POSITION",
        "decision_timestamp": "2026-07-16T00:00:00.000000Z",
        "effective_timestamp": "2026-07-17T00:00:00.000000Z",
        "security_id": "ABC",
        "requested_quantity_or_sizing_input": {"kind": "NONE", "quantity": 0},
        "rationale_ref": "RATIONALE:001",
        "protocol_id": "GV_FS0_PROTOCOL_V1",
        "fixture_id": "FIXTURE:001",
        "operator_id": "OWNER:001",
        "supersedes_decision_id": None,
    }
    projected = project_verifier_input(fixture, decision)
    assert projected["decision"]["authority"] == decision["authority_tier"]
    assert projected["decision"]["requested_sizing"] == decision["requested_quantity_or_sizing_input"]
    assert projected["decision"]["rationale_reference"] == decision["rationale_ref"]
    assert projected["protocol"]["protocol_id"] == decision["protocol_id"]
    assert "operator_id" not in projected["decision"]
    assert "supersedes_decision_id" not in projected["decision"]
    assert "protocol_id" not in projected["decision"]
    assert "fixture_id" not in projected["decision"]
