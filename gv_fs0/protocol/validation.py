"""Repository-owned semantic validation for frozen GV-FS0 V1 artifacts."""

from __future__ import annotations

from collections import Counter
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .canonical import domain_hash
from .definitions import (
    CHECK_RANKS,
    MANDATORY_CHECKS,
    OUTCOME_RANKS,
    build_certification_failure_registry,
    build_event_ranks,
    build_generated_event_slots,
    build_operational_error_registry,
    build_schema_bundle,
    build_transition_ownership,
    canonical_failure_binding_key,
)


class ProtocolValidationError(ValueError):
    """Stable fail-closed semantic validation error."""


def validate_schema_bundle(bundle: dict[str, Any] | None = None) -> None:
    bundle = build_schema_bundle() if bundle is None else bundle
    schemas = bundle.get("schemas")
    if not isinstance(schemas, dict) or len(schemas) != 12:
        raise ProtocolValidationError("exactly twelve schemas are required")
    for name, schema in schemas.items():
        if schema.get("title") != name:
            raise ProtocolValidationError(f"schema title mismatch: {name}")
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ProtocolValidationError(f"schema draft mismatch: {name}")
        Draft202012Validator.check_schema(schema)
        _assert_all_object_schemas_closed(schema, path=name)


def _assert_all_object_schemas_closed(node: Any, *, path: str) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            raise ProtocolValidationError(f"open object schema: {path}")
        for key, value in node.items():
            _assert_all_object_schemas_closed(value, path=f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _assert_all_object_schemas_closed(value, path=f"{path}/{index}")


def validate_instance(schema_name: str, instance: Any) -> None:
    bundle = build_schema_bundle()
    schemas = bundle["schemas"]
    if schema_name not in schemas:
        raise ProtocolValidationError(f"unknown schema: {schema_name}")
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    root_schema = schemas[schema_name]
    errors = sorted(
        Draft202012Validator(root_schema, registry=registry).iter_errors(instance),
        key=lambda err: list(err.path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path)
        raise ProtocolValidationError(f"{schema_name}:{location}:{first.message}")


def validate_registries() -> None:
    failure_artifact = build_certification_failure_registry()
    failure_registry = failure_artifact["registry"]
    if failure_artifact["registry_hash"] != domain_hash("GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1", failure_registry):
        raise ProtocolValidationError("certification failure registry hash mismatch")
    failure_codes = [entry["code"] for entry in failure_registry["entries"]]
    if failure_codes != sorted(failure_codes) or len(failure_codes) != len(set(failure_codes)):
        raise ProtocolValidationError("certification failure codes must be unique and sorted")
    required_controller_codes = {
        "VERIFIER_SUPERVISION_INCOMPLETE",
        "VERIFIER_TIMEOUT",
        "VERIFIER_OUTPUT_LIMIT_EXCEEDED",
        "VERIFIER_PROCESS_FAILED",
        "VERIFIER_STDERR_NONEMPTY",
        "VERIFIER_OUTPUT_INVALID_UTF8",
        "VERIFIER_OUTPUT_NOT_CANONICAL",
        "VERIFIER_OUTPUT_SCHEMA_INVALID",
        "VERIFIER_RESULT_BINDING_INVALID",
    }
    if not required_controller_codes.issubset(failure_codes):
        raise ProtocolValidationError("controller failure registry is incomplete")
    for entry in failure_registry["entries"]:
        if not entry["applicable_outcomes"] or "TRUE" in entry["applicable_outcomes"]:
            raise ProtocolValidationError(f"invalid outcomes for {entry['code']}")
        if not set(entry["applicable_checks"]).issubset(MANDATORY_CHECKS):
            raise ProtocolValidationError(f"invalid checks for {entry['code']}")
        if not set(entry["applicable_emitters"]).issubset({"PRIMARY", "VERIFIER", "CONTROLLER"}):
            raise ProtocolValidationError(f"invalid emitters for {entry['code']}")

    operational_artifact = build_operational_error_registry()
    operational_registry = operational_artifact["registry"]
    if operational_artifact["registry_hash"] != domain_hash("GV-FS0:OPERATIONAL_ERROR_REGISTRY:V1", operational_registry):
        raise ProtocolValidationError("operational error registry hash mismatch")
    operational_codes = [entry["code"] for entry in operational_registry["entries"]]
    expected = {
        "PUBLICATION_LOCKED",
        "PUBLICATION_TARGET_CHANGED",
        "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
        "PUBLICATION_RECOVERY_RECORD_FAILED",
    }
    if set(operational_codes) != expected or operational_codes != sorted(operational_codes):
        raise ProtocolValidationError("operational error registry is incomplete or unsorted")
    if set(operational_codes).intersection(failure_codes):
        raise ProtocolValidationError("certification and operational registries overlap")


def validate_frozen_tables() -> None:
    ranks = build_event_ranks()["event_ranks"]
    if [entry["rank"] for entry in ranks] != list(range(10, 100, 10)):
        raise ProtocolValidationError("event ranks are not the frozen 10..90 sequence")
    event_types = [entry["event_type"] for entry in ranks]
    if len(event_types) != len(set(event_types)):
        raise ProtocolValidationError("event ranks contain duplicate event types")

    slots = build_generated_event_slots()["generated_event_slots"]
    slot_keys = [(entry["source_intent_type"], entry["generated_event_slot"]) for entry in slots]
    if len(slot_keys) != len(set(slot_keys)):
        raise ProtocolValidationError("generated slot origin keys are not unique")
    payment = [entry for entry in slots if entry["source_intent_type"] == "DIVIDEND_PAYMENT_INSTRUCTION"]
    if payment != [{"generated_event_slot": 10, "generated_event_type": "DIVIDEND_PAYMENT", "source_intent_type": "DIVIDEND_PAYMENT_INSTRUCTION"}]:
        raise ProtocolValidationError("dividend payment must emit no separate cash movement")

    ownership = build_transition_ownership()["transition_ownership"]
    if [entry["event_type"] for entry in ownership] != event_types:
        raise ProtocolValidationError("transition ownership must cover event ranks exactly once")
    payment_owner = next(entry for entry in ownership if entry["event_type"] == "DIVIDEND_PAYMENT")
    if payment_owner["cash"] != "INCREASE_ONCE" or payment_owner["receivables"] != "DECREASE_ONCE":
        raise ProtocolValidationError("dividend payment transition ownership is invalid")
    for event_type in ("EXECUTION", "FEE_OR_COST", "SESSION_VALUATION", "CERTIFICATION_REFERENCE"):
        entry = next(item for item in ownership if item["event_type"] == event_type)
        if any(entry[field] != "NONE" for field in ("cash", "shares", "receivables")):
            raise ProtocolValidationError(f"{event_type} must not mutate balances")


def validate_failure_bindings(
    checks: dict[str, str],
    bindings: list[dict[str, str]],
    *,
    emitter_by_code: dict[str, str] | None = None,
) -> None:
    if set(checks) != set(MANDATORY_CHECKS):
        raise ProtocolValidationError("certification check set is incomplete")
    if any(value not in {"TRUE", "FALSE", "UNKNOWN"} for value in checks.values()):
        raise ProtocolValidationError("invalid certification check outcome")
    if bindings != sorted(bindings, key=canonical_failure_binding_key):
        raise ProtocolValidationError("failure bindings are not in canonical order")
    binding_tuples = [(binding["check"], binding["outcome"], binding["code"]) for binding in bindings]
    if len(binding_tuples) != len(set(binding_tuples)):
        raise ProtocolValidationError("duplicate failure binding")

    registry_entries = build_certification_failure_registry()["registry"]["entries"]
    registry = {entry["code"]: entry for entry in registry_entries}
    counts = Counter(binding["check"] for binding in bindings)
    for check, outcome in checks.items():
        if outcome == "TRUE" and counts[check]:
            raise ProtocolValidationError(f"TRUE check has a failure binding: {check}")
        if outcome in {"FALSE", "UNKNOWN"} and not counts[check]:
            raise ProtocolValidationError(f"non-TRUE check lacks a failure binding: {check}")
    for binding in bindings:
        check = binding["check"]
        outcome = binding["outcome"]
        code = binding["code"]
        if checks[check] != outcome:
            raise ProtocolValidationError(f"binding outcome does not match check: {check}")
        if code not in registry:
            raise ProtocolValidationError(f"unknown certification failure code: {code}")
        entry = registry[code]
        if check not in entry["applicable_checks"] or outcome not in entry["applicable_outcomes"]:
            raise ProtocolValidationError(f"incompatible check/outcome/code binding: {code}")
        if emitter_by_code is not None:
            emitter = emitter_by_code.get(code)
            if emitter not in entry["applicable_emitters"]:
                raise ProtocolValidationError(f"incompatible emitter for {code}")


def validate_certification_status(checks: dict[str, str], certification_status: str) -> None:
    expected = "CERTIFIED" if all(checks.get(check) == "TRUE" for check in MANDATORY_CHECKS) else "BLOCKED"
    if certification_status != expected:
        raise ProtocolValidationError(f"certification status must be {expected}")


def validate_all_definitions() -> None:
    validate_schema_bundle()
    validate_registries()
    validate_frozen_tables()
