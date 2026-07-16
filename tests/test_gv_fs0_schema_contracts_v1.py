from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "contracts/gv_fs0/v1"
SCHEMA_ROOT = ARTIFACT_ROOT / "schemas"
SCHEMA_BASE = "https://terminal-zero.invalid/contracts/gv_fs0/v1/schemas/"

EXPECTED_SCHEMAS = {
    "gv_fs0_source_fixture_v1.schema.json",
    "gv_fs0_decision_envelope_v1.schema.json",
    "gv_fs0_source_intent_v1.schema.json",
    "gv_fs0_portfolio_event_v1.schema.json",
    "gv_fs0_snapshot_v1.schema.json",
    "gv_fs0_verifier_input_v1.schema.json",
    "gv_fs0_verifier_result_v1.schema.json",
    "gv_fs0_verifier_attempt_v1.schema.json",
    "gv_fs0_certification_v1.schema.json",
    "gv_fs0_certified_decision_result_v1.schema.json",
    "gv_fs0_certified_bundle_v1.schema.json",
    "gv_fs0_blocked_evidence_v1.schema.json",
}
EXPECTED_OTHER = {
    "registries/gv_fs0_certification_failure_registry_v1.json",
    "registries/gv_fs0_operational_error_registry_v1.json",
    "tables/gv_fs0_event_ranks_v1.json",
    "tables/gv_fs0_generated_event_slots_v1.json",
    "tables/gv_fs0_transition_ownership_v1.json",
    "vectors/gv_fs0_canonical_vectors_v1.json",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _schemas() -> list[dict[str, Any]]:
    return [_load(SCHEMA_ROOT / filename) for filename in sorted(EXPECTED_SCHEMAS)]


def _registry() -> Registry:
    registry = Registry()
    for schema in _schemas():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


def _source_intent(intent_type: str, sequence: int = 0) -> dict[str, Any]:
    values: dict[str, Any] = {
        "schema_version": "gv_fs0_source_intent_v1",
        "source_intent_id": f"{intent_type}:INTENT_{sequence}",
        "source_sequence": sequence,
        "intent_type": intent_type,
        "effective_timestamp": "2026-07-17T00:00:00.000000Z",
        "session": "2026-07-17",
        "security_id": "SEC_1",
        "quantity": None,
        "execution_price": None,
        "fee": None,
        "dividend_amount_per_share": None,
        "referenced_entitlement_source_intent_id": None,
        "valuation_timestamp": None,
    }
    if intent_type == "EXECUTION_INTENT":
        values.update(quantity=10, execution_price="10")
    elif intent_type == "EXPLICIT_FEE":
        values["fee"] = "1"
    elif intent_type == "DIVIDEND_DECLARATION":
        values["dividend_amount_per_share"] = "0.5"
    elif intent_type == "DIVIDEND_PAYMENT_INSTRUCTION":
        values["referenced_entitlement_source_intent_id"] = "DIVIDEND_DECLARATION:INTENT_2"
    elif intent_type == "VALUATION_INSTRUCTION":
        values["valuation_timestamp"] = "2026-07-17T23:59:59.000000Z"
    return values


def _verifier_input(action: str, intents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "gv_fs0_verifier_input_v1",
        "protocol": {
            "protocol_id": "GV_FS0_PROTOCOL_V1",
            "fixture_id": "FIXTURE_1",
            "fixture_hash": "f" * 64,
            "currency": "USD",
            "initial_cash": "1000",
        },
        "decision": {
            "decision_id": f"DECISION_{action}",
            "decision_hash": "d" * 64,
            "authority": "MANUAL_OWNER_PAPER",
            "action": action,
            "decision_timestamp": "2026-07-16T00:00:00.000000Z",
            "effective_timestamp": "2026-07-17T00:00:00.000000Z",
            "security_id": "SEC_1",
            "requested_sizing": {"quantity": 10 if action == "OPEN" else None},
            "rationale_reference": f"RATIONALE:{action}",
        },
        "source_prices": [],
        "source_intents": intents,
    }


def test_exact_twelve_schemas_and_six_other_normative_artifacts() -> None:
    assert {path.name for path in SCHEMA_ROOT.glob("*.json")} == EXPECTED_SCHEMAS
    observed_other = {
        path.relative_to(ARTIFACT_ROOT).as_posix()
        for directory in ["registries", "tables", "vectors"]
        for path in (ARTIFACT_ROOT / directory).glob("*.json")
    }
    assert observed_other == EXPECTED_OTHER


@pytest.mark.parametrize("filename", sorted(EXPECTED_SCHEMAS))
def test_schema_is_draft_2020_12_and_meta_schema_valid(filename: str) -> None:
    schema = _load(SCHEMA_ROOT / filename)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == f"{SCHEMA_BASE}{filename}"
    Draft202012Validator.check_schema(schema)
    expected_const = filename.removesuffix(".schema.json")
    assert schema["properties"]["schema_version"]["const"] == expected_const


@pytest.mark.parametrize("filename", sorted(EXPECTED_SCHEMAS))
def test_every_typed_object_schema_is_closed(filename: str) -> None:
    schema = _load(SCHEMA_ROOT / filename)
    for node in _walk(schema):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, (filename, node)


def test_all_relative_refs_resolve_from_committed_local_bundle() -> None:
    registry = _registry()
    for schema in _schemas():
        resolver = registry.resolver(schema["$id"])
        for node in _walk(schema):
            reference = node.get("$ref")
            if reference is not None:
                resolved = resolver.lookup(reference).contents
                assert resolved["$id"].startswith(SCHEMA_BASE)


def test_source_intent_type_specific_nullability_is_exact() -> None:
    schema = _load(SCHEMA_ROOT / "gv_fs0_source_intent_v1.schema.json")
    validator = Draft202012Validator(schema)
    intent_types = [
        "EXECUTION_INTENT",
        "EXPLICIT_FEE",
        "DIVIDEND_DECLARATION",
        "DIVIDEND_PAYMENT_INSTRUCTION",
        "VALUATION_INSTRUCTION",
    ]
    for sequence, intent_type in enumerate(intent_types):
        valid = _source_intent(intent_type, sequence)
        validator.validate(valid)
        invalid = dict(valid)
        if intent_type == "EXECUTION_INTENT":
            invalid["fee"] = "1"
        else:
            invalid["quantity"] = 1
        assert list(validator.iter_errors(invalid)), intent_type


def test_verifier_input_enforces_no_position_and_open_intent_cardinality() -> None:
    schema = _load(SCHEMA_ROOT / "gv_fs0_verifier_input_v1.schema.json")
    validator = Draft202012Validator(schema, registry=_registry())

    no_position = _verifier_input("NO_POSITION", [_source_intent("VALUATION_INSTRUCTION")])
    validator.validate(no_position)
    invalid_no_position = _verifier_input(
        "NO_POSITION",
        [_source_intent("EXECUTION_INTENT"), _source_intent("VALUATION_INSTRUCTION", 1)],
    )
    assert list(validator.iter_errors(invalid_no_position))

    open_intents = [
        _source_intent("EXECUTION_INTENT", 0),
        _source_intent("EXPLICIT_FEE", 1),
        _source_intent("DIVIDEND_DECLARATION", 2),
        _source_intent("DIVIDEND_PAYMENT_INSTRUCTION", 3),
        _source_intent("VALUATION_INSTRUCTION", 4),
    ]
    validator.validate(_verifier_input("OPEN", open_intents))
    assert list(validator.iter_errors(_verifier_input("OPEN", open_intents[1:])))
    assert list(validator.iter_errors(_verifier_input("OPEN", [open_intents[0], *open_intents])))


def test_verifier_attempt_enforces_result_and_infrastructure_nullability() -> None:
    schema = _load(SCHEMA_ROOT / "gv_fs0_verifier_attempt_v1.schema.json")
    validator = Draft202012Validator(schema)
    digest = "a" * 64
    valid_result = {
        "schema_version": "gv_fs0_verifier_attempt_v1",
        "ordinal": 1,
        "outcome": "RESULT",
        "verifier_result_hash": digest,
        "controller_failure_code": None,
    }
    valid_failure = {
        "schema_version": "gv_fs0_verifier_attempt_v1",
        "ordinal": 2,
        "outcome": "INFRASTRUCTURE_FAILURE",
        "verifier_result_hash": None,
        "controller_failure_code": "VERIFIER_TIMEOUT",
    }
    validator.validate(valid_result)
    validator.validate(valid_failure)

    invalid_result = dict(valid_result, controller_failure_code="VERIFIER_TIMEOUT")
    invalid_failure = dict(valid_failure, verifier_result_hash=digest)
    assert list(validator.iter_errors(invalid_result))
    assert list(validator.iter_errors(invalid_failure))


def test_attempt_ordinals_and_bundle_roles_are_frozen_in_prefix_order() -> None:
    certification = _load(SCHEMA_ROOT / "gv_fs0_certification_v1.schema.json")
    attempts = certification["properties"]["verifier_attempts"]["prefixItems"]
    assert attempts[0]["allOf"][1]["properties"]["ordinal"]["const"] == 1
    assert attempts[1]["allOf"][1]["properties"]["ordinal"]["const"] == 2

    bundle = _load(SCHEMA_ROOT / "gv_fs0_certified_bundle_v1.schema.json")
    components = bundle["properties"]["components"]["prefixItems"]
    assert components[0]["allOf"][1]["properties"]["role"]["const"] == "OPEN"
    assert components[1]["allOf"][1]["properties"]["role"]["const"] == "NO_POSITION"


def test_no_position_projection_permits_zero_execution_intents() -> None:
    verifier_input = _load(SCHEMA_ROOT / "gv_fs0_verifier_input_v1.schema.json")
    action_values = verifier_input["properties"]["decision"]["properties"]["action"]["enum"]
    assert "NO_POSITION" in action_values
    source_intents = verifier_input["properties"]["source_intents"]
    assert source_intents.get("minItems", 0) == 0


def test_blocked_evidence_cannot_be_publishable() -> None:
    blocked = _load(SCHEMA_ROOT / "gv_fs0_blocked_evidence_v1.schema.json")
    assert blocked["properties"]["publishable"] == {"type": "boolean", "const": False}
    assert blocked["properties"]["certification_status"]["const"] == "BLOCKED"
