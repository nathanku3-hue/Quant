"""Single definition surface for all GV-FS0 Protocol V1 machine artifacts.

The checked-in JSON files are canonical projections of the values returned here.
No reducer, fixture-event generator, snapshot builder, certification executor,
publication path, or UI adapter is implemented in this module.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

from .canonical import canonical_document_bytes, canonical_json_text, domain_hash, domain_preimage

PROTOCOL_ID = "GV_FS0_PROTOCOL_V1"
PROTOCOL_VERSION = "V1"
CONTRACT_PATH = "docs/architecture/gv_fs0_certification_and_data_authority_contract.md"
PHASE_BRIEF_PATH = "docs/phase_brief/phase-E0-brief.md"
CONTRACT_SHA256 = "085a4bcf672069320e69a40c010bbc6ad7bd5c63a844214cb140cb6292de8a02"
CONTRACT_SIZE = 60_173
PHASE_BRIEF_SHA256 = "9b356b39a91190cd3c3f4aa74a7e85ea014323aff1827959c2ba77ceb522f5c6"
PHASE_BRIEF_SIZE = 13_688

ARTIFACT_ROOT = "docs/context/e2e_evidence/gv_fs0_protocol_v1"
SCHEMA_BUNDLE_PATH = "schemas/gv_fs0/v1/gv_fs0_schema_bundle_v1.json"
CERTIFICATION_FAILURE_REGISTRY_PATH = f"{ARTIFACT_ROOT}/gv_fs0_certification_failure_registry_v1.json"
OPERATIONAL_ERROR_REGISTRY_PATH = f"{ARTIFACT_ROOT}/gv_fs0_operational_error_registry_v1.json"
EVENT_RANKS_PATH = f"{ARTIFACT_ROOT}/gv_fs0_event_ranks_v1.json"
GENERATED_EVENT_SLOTS_PATH = f"{ARTIFACT_ROOT}/gv_fs0_generated_event_slots_v1.json"
TRANSITION_OWNERSHIP_PATH = f"{ARTIFACT_ROOT}/gv_fs0_transition_ownership_v1.json"
CANONICAL_VECTORS_PATH = f"{ARTIFACT_ROOT}/gv_fs0_canonical_vectors_v1.json"
FREEZE_MANIFEST_PATH = f"{ARTIFACT_ROOT}/gv_fs0_freeze_manifest_v1.json"

SCHEMA_NAMES = (
    "gv_fs0_source_fixture_v1",
    "gv_fs0_decision_envelope_v1",
    "gv_fs0_source_intent_v1",
    "gv_fs0_portfolio_event_v1",
    "gv_fs0_snapshot_v1",
    "gv_fs0_verifier_input_v1",
    "gv_fs0_verifier_result_v1",
    "gv_fs0_verifier_attempt_v1",
    "gv_fs0_certification_v1",
    "gv_fs0_certified_decision_result_v1",
    "gv_fs0_certified_bundle_v1",
    "gv_fs0_blocked_evidence_v1",
)

MANDATORY_CHECKS = (
    "decision_authority_valid",
    "timestamp_causality_valid",
    "price_freshness_valid",
    "cash_conserved",
    "holdings_valid",
    "nav_reconciled",
    "receivables_reconciled",
    "unsupported_events_absent",
    "independent_reconstruction_passed",
    "canonical_hash_reproduced",
)
CHECK_RANKS = {check: (index + 1) * 10 for index, check in enumerate(MANDATORY_CHECKS)}
OUTCOME_RANKS = {"FALSE": 10, "UNKNOWN": 20}

DOMAINS = (
    "GV-FS0:FIXTURE:V1",
    "GV-FS0:DECISION_ENVELOPE:V1",
    "GV-FS0:BOOK_ID:V1",
    "GV-FS0:PORTFOLIO_EVENT_ID:V1",
    "GV-FS0:SNAPSHOT_ID:V1",
    "GV-FS0:ECONOMIC_PAYLOAD:V1",
    "GV-FS0:VERIFIER_INPUT:V1",
    "GV-FS0:VERIFIER_RESULT:V1",
    "GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1",
    "GV-FS0:OPERATIONAL_ERROR_REGISTRY:V1",
    "GV-FS0:CERTIFICATION_ID:V1",
    "GV-FS0:CERTIFICATION_REFERENCE_EVENT_ID:V1",
    "GV-FS0:CERTIFIED_DECISION_RESULT:V1",
    "GV-FS0:PRESENTATION:V1",
    "GV-FS0:CERTIFIED_BUNDLE:V1",
)

_DRAFT = "https://json-schema.org/draft/2020-12/schema"
_SCHEMA_URN_PREFIX = "urn:terminal-zero:gv-fs0:protocol-v1:"
_HASH_PATTERN = "^[0-9a-f]{64}$"
_DECIMAL_PATTERN = "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"
_NONNEGATIVE_DECIMAL_PATTERN = "^(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"
_DATE_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
_TIMESTAMP_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{6}Z$"
_TOKEN_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"
_SOURCE_INTENT_ID_PATTERN = "^[A-Z][A-Z0-9_]*:[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"
_RATIONALE_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
_EVENT_ID_PATTERN = "^EVT_[0-9a-f]{64}$"
_BOOK_ID_PATTERN = "^BOOK_[0-9a-f]{64}$"
_SNAPSHOT_ID_PATTERN = "^SNAP_[0-9a-f]{64}$"
_CERTIFICATION_ID_PATTERN = "^CERT_[0-9a-f]{64}$"
_CDR_ID_PATTERN = "^CDR_[0-9a-f]{64}$"
_BUNDLE_ID_PATTERN = "^BUNDLE_[0-9a-f]{64}$"
_MAX_INTEGER = 9_007_199_254_740_991


def _urn(name: str) -> str:
    return _SCHEMA_URN_PREFIX + name


def _ref(name: str) -> dict[str, str]:
    return {"$ref": _urn(name)}


def _object(required: list[str], properties: dict[str, Any], **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }
    result.update(extra)
    return result


def _schema(name: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": _DRAFT,
        "$id": _urn(name),
        "title": name,
        **body,
    }


def _string(*, pattern: str | None = None, enum: list[str] | None = None, min_length: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "string"}
    if pattern is not None:
        result["pattern"] = pattern
    if enum is not None:
        result["enum"] = enum
    if min_length is not None:
        result["minLength"] = min_length
    return result


def _integer(*, minimum: int = 0, maximum: int = _MAX_INTEGER, const: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "integer", "minimum": minimum, "maximum": maximum}
    if const is not None:
        result["const"] = const
    return result


def _array(items: dict[str, Any], *, min_items: int | None = None, max_items: int | None = None, unique: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "array", "items": items}
    if min_items is not None:
        result["minItems"] = min_items
    if max_items is not None:
        result["maxItems"] = max_items
    if unique:
        result["uniqueItems"] = True
    return result


def _hash() -> dict[str, Any]:
    return _string(pattern=_HASH_PATTERN)


def _timestamp() -> dict[str, Any]:
    return _string(pattern=_TIMESTAMP_PATTERN)


def _date() -> dict[str, Any]:
    return _string(pattern=_DATE_PATTERN)


def _decimal(*, nonnegative: bool = False) -> dict[str, Any]:
    return _string(pattern=_NONNEGATIVE_DECIMAL_PATTERN if nonnegative else _DECIMAL_PATTERN)


def _binding_properties() -> dict[str, Any]:
    return {
        "protocol_binding": _object(
            ["protocol_id", "protocol_version"],
            {
                "protocol_id": {"const": PROTOCOL_ID},
                "protocol_version": {"const": PROTOCOL_VERSION},
            },
        ),
        "fixture_binding": _object(
            ["fixture_id", "fixture_hash"],
            {"fixture_id": _string(pattern=_TOKEN_PATTERN), "fixture_hash": _hash()},
        ),
        "decision_binding": _object(
            ["decision_id", "decision_hash"],
            {"decision_id": _string(pattern=_TOKEN_PATTERN), "decision_hash": _hash()},
        ),
    }


def build_schemas() -> dict[str, dict[str, Any]]:
    """Return the twelve self-identified Draft 2020-12 schemas."""

    common_intent = {
        "source_sequence": _integer(),
        "source_intent_id": _string(pattern=_SOURCE_INTENT_ID_PATTERN),
        "effective_timestamp": _timestamp(),
        "session": _date(),
        "security_id": _string(pattern=_TOKEN_PATTERN),
    }
    intent_variants = [
        _object(
            [*common_intent, "intent_type", "quantity", "execution_price"],
            {
                **deepcopy(common_intent),
                "intent_type": {"const": "EXECUTION_INTENT"},
                "quantity": _integer(minimum=1),
                "execution_price": _decimal(nonnegative=True),
            },
        ),
        _object(
            [*common_intent, "intent_type", "explicit_fee"],
            {
                **deepcopy(common_intent),
                "intent_type": {"const": "EXPLICIT_FEE"},
                "explicit_fee": _decimal(nonnegative=True),
            },
        ),
        _object(
            [*common_intent, "intent_type", "amount_per_share", "pay_session"],
            {
                **deepcopy(common_intent),
                "intent_type": {"const": "DIVIDEND_DECLARATION"},
                "amount_per_share": _decimal(nonnegative=True),
                "pay_session": _date(),
            },
        ),
        _object(
            [*common_intent, "intent_type", "referenced_entitlement_source_intent_id"],
            {
                **deepcopy(common_intent),
                "intent_type": {"const": "DIVIDEND_PAYMENT_INSTRUCTION"},
                "referenced_entitlement_source_intent_id": _string(pattern=_SOURCE_INTENT_ID_PATTERN),
            },
        ),
        _object(
            [*common_intent, "intent_type"],
            {**deepcopy(common_intent), "intent_type": {"const": "VALUATION_INSTRUCTION"}},
        ),
    ]

    source_intent = _schema("gv_fs0_source_intent_v1", {"oneOf": intent_variants})

    price_record = _object(
        ["security_id", "session", "price_timestamp", "close_price", "source_sequence"],
        {
            "security_id": _string(pattern=_TOKEN_PATTERN),
            "session": _date(),
            "price_timestamp": _timestamp(),
            "close_price": _decimal(nonnegative=True),
            "source_sequence": _integer(),
        },
    )
    source_fixture = _schema(
        "gv_fs0_source_fixture_v1",
        _object(
            [
                "schema_version",
                "protocol_id",
                "fixture_id",
                "fixture_hash",
                "currency",
                "security_id",
                "initial_cash",
                "prices",
                "source_intents",
            ],
            {
                "schema_version": {"const": "GV_FS0_SOURCE_FIXTURE_V1"},
                "protocol_id": {"const": PROTOCOL_ID},
                "fixture_id": _string(pattern=_TOKEN_PATTERN),
                "fixture_hash": _hash(),
                "currency": _string(pattern="^[A-Z]{3}$"),
                "security_id": _string(pattern=_TOKEN_PATTERN),
                "initial_cash": _decimal(nonnegative=True),
                "prices": _array(price_record, min_items=5, max_items=10),
                "source_intents": _array(_ref("gv_fs0_source_intent_v1"), min_items=5),
            },
        ),
    )

    requested_sizing = _object(
        ["kind", "quantity"],
        {
            "kind": _string(enum=["WHOLE_SHARES", "NONE"]),
            "quantity": _integer(),
        },
    )
    decision_envelope = _schema(
        "gv_fs0_decision_envelope_v1",
        _object(
            [
                "schema_version",
                "decision_id",
                "decision_hash",
                "fixture_hash",
                "authority_tier",
                "action",
                "decision_timestamp",
                "effective_timestamp",
                "security_id",
                "requested_quantity_or_sizing_input",
                "rationale_ref",
                "protocol_id",
                "fixture_id",
                "operator_id",
                "supersedes_decision_id",
            ],
            {
                "schema_version": {"const": "GV_FS0_DECISION_ENVELOPE_V1"},
                "decision_id": _string(pattern=_TOKEN_PATTERN),
                "decision_hash": _hash(),
                "fixture_hash": _hash(),
                "authority_tier": {"const": "MANUAL_OWNER_PAPER"},
                "action": _string(enum=["OPEN", "NO_POSITION"]),
                "decision_timestamp": _timestamp(),
                "effective_timestamp": _timestamp(),
                "security_id": _string(pattern=_TOKEN_PATTERN),
                "requested_quantity_or_sizing_input": requested_sizing,
                "rationale_ref": _string(pattern=_RATIONALE_PATTERN),
                "protocol_id": {"const": PROTOCOL_ID},
                "fixture_id": _string(pattern=_TOKEN_PATTERN),
                "operator_id": _string(pattern=_TOKEN_PATTERN),
                "supersedes_decision_id": {"oneOf": [{"type": "null"}, _string(pattern=_TOKEN_PATTERN)]},
            },
            allOf=[
                {
                    "if": {"properties": {"action": {"const": "NO_POSITION"}}, "required": ["action"]},
                    "then": {
                        "properties": {
                            "requested_quantity_or_sizing_input": {
                                "properties": {"kind": {"const": "NONE"}, "quantity": {"const": 0}}
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"action": {"const": "OPEN"}}, "required": ["action"]},
                    "then": {
                        "properties": {
                            "requested_quantity_or_sizing_input": {
                                "properties": {
                                    "kind": {"const": "WHOLE_SHARES"},
                                    "quantity": {"type": "integer", "minimum": 1, "maximum": _MAX_INTEGER},
                                }
                            }
                        }
                    },
                },
            ],
        ),
    )

    semantic_payload = _object(
        [],
        {
            "security_id": _string(pattern=_TOKEN_PATTERN),
            "quantity": _integer(),
            "execution_price": _decimal(nonnegative=True),
            "fee": _decimal(nonnegative=True),
            "cash_delta": _decimal(),
            "dividend_amount_per_share": _decimal(nonnegative=True),
            "entitled_quantity": _integer(),
            "receivable_amount": _decimal(nonnegative=True),
            "payment_amount": _decimal(nonnegative=True),
            "referenced_entitlement_id": _string(pattern=_EVENT_ID_PATTERN),
            "valuation_price": _decimal(nonnegative=True),
            "terminal_snapshot_id": _string(pattern=_SNAPSHOT_ID_PATTERN),
            "certification_id": _string(pattern=_CERTIFICATION_ID_PATTERN),
        },
    )
    portfolio_event = _schema(
        "gv_fs0_portfolio_event_v1",
        _object(
            [
                "schema_version",
                "book_id",
                "decision_id",
                "event_id",
                "source_sequence",
                "source_intent_id",
                "generated_event_slot",
                "event_type",
                "effective_timestamp",
                "session",
                "event_type_rank",
                "intra_rank_sequence",
                "semantic_sequence",
                "semantic_payload",
            ],
            {
                "schema_version": {"const": "GV_FS0_PORTFOLIO_EVENT_V1"},
                "book_id": _string(pattern=_BOOK_ID_PATTERN),
                "decision_id": _string(pattern=_TOKEN_PATTERN),
                "event_id": _string(pattern=_EVENT_ID_PATTERN),
                "source_sequence": _integer(),
                "source_intent_id": _string(pattern=_SOURCE_INTENT_ID_PATTERN),
                "generated_event_slot": _integer(minimum=10, maximum=30),
                "event_type": _string(
                    enum=[
                        "DECISION_ACCEPTED",
                        "EXECUTION",
                        "FEE_OR_COST",
                        "CASH_MOVEMENT",
                        "POSITION_MOVEMENT",
                        "DIVIDEND_ENTITLEMENT",
                        "DIVIDEND_PAYMENT",
                        "SESSION_VALUATION",
                        "CERTIFICATION_REFERENCE",
                    ]
                ),
                "effective_timestamp": _timestamp(),
                "session": _date(),
                "event_type_rank": _integer(minimum=10, maximum=90),
                "intra_rank_sequence": _integer(),
                "semantic_sequence": _integer(),
                "semantic_payload": semantic_payload,
            },
        ),
    )

    snapshot = _schema(
        "gv_fs0_snapshot_v1",
        _object(
            [
                "schema_version",
                "snapshot_id",
                "session",
                "valuation_timestamp",
                "book_id",
                "decision_id",
                "fixture_hash",
                "authority_tier",
                "action",
                "rationale_ref",
                "security_id",
                "shares",
                "cash",
                "receivables",
                "market_value",
                "nav",
                "session_contribution",
                "cumulative_contribution",
                "applied_event_ids",
            ],
            {
                "schema_version": {"const": "GV_FS0_SNAPSHOT_V1"},
                "snapshot_id": _string(pattern=_SNAPSHOT_ID_PATTERN),
                "session": _date(),
                "valuation_timestamp": _timestamp(),
                "book_id": _string(pattern=_BOOK_ID_PATTERN),
                "decision_id": _string(pattern=_TOKEN_PATTERN),
                "fixture_hash": _hash(),
                "authority_tier": {"const": "MANUAL_OWNER_PAPER"},
                "action": _string(enum=["OPEN", "NO_POSITION"]),
                "rationale_ref": _string(pattern=_RATIONALE_PATTERN),
                "security_id": _string(pattern=_TOKEN_PATTERN),
                "shares": _integer(),
                "cash": _decimal(nonnegative=True),
                "receivables": _decimal(nonnegative=True),
                "market_value": _decimal(nonnegative=True),
                "nav": _decimal(nonnegative=True),
                "session_contribution": _decimal(),
                "cumulative_contribution": _decimal(),
                "applied_event_ids": _array(_string(pattern=_EVENT_ID_PATTERN), unique=True),
            },
        ),
    )

    verifier_protocol = _object(
        ["protocol_id", "protocol_version", "fixture_id", "fixture_hash", "currency", "initial_cash"],
        {
            "protocol_id": {"const": PROTOCOL_ID},
            "protocol_version": {"const": PROTOCOL_VERSION},
            "fixture_id": _string(pattern=_TOKEN_PATTERN),
            "fixture_hash": _hash(),
            "currency": _string(pattern="^[A-Z]{3}$"),
            "initial_cash": _decimal(nonnegative=True),
        },
    )
    verifier_decision = _object(
        [
            "decision_id",
            "decision_hash",
            "authority",
            "action",
            "decision_timestamp",
            "effective_timestamp",
            "security_id",
            "requested_sizing",
            "rationale_reference",
        ],
        {
            "decision_id": _string(pattern=_TOKEN_PATTERN),
            "decision_hash": _hash(),
            "authority": {"const": "MANUAL_OWNER_PAPER"},
            "action": _string(enum=["OPEN", "NO_POSITION"]),
            "decision_timestamp": _timestamp(),
            "effective_timestamp": _timestamp(),
            "security_id": _string(pattern=_TOKEN_PATTERN),
            "requested_sizing": deepcopy(requested_sizing),
            "rationale_reference": _string(pattern=_RATIONALE_PATTERN),
        },
    )
    verifier_input = _schema(
        "gv_fs0_verifier_input_v1",
        _object(
            ["schema_version", "protocol", "decision", "prices", "source_intents"],
            {
                "schema_version": {"const": "GV_FS0_VERIFIER_INPUT_V1"},
                "protocol": verifier_protocol,
                "decision": verifier_decision,
                "prices": _array(price_record, min_items=5, max_items=10),
                "source_intents": _array(_ref("gv_fs0_source_intent_v1"), min_items=5),
            },
        ),
    )

    economic_payload = _object(
        [
            "schema_version",
            "protocol_id",
            "fixture_id",
            "fixture_hash",
            "decision_id",
            "decision_hash",
            "book_id",
            "ordered_economic_event_ids",
            "snapshots",
            "terminal_snapshot_id",
        ],
        {
            "schema_version": {"const": "GV_FS0_ECONOMIC_PAYLOAD_V1"},
            "protocol_id": {"const": PROTOCOL_ID},
            "fixture_id": _string(pattern=_TOKEN_PATTERN),
            "fixture_hash": _hash(),
            "decision_id": _string(pattern=_TOKEN_PATTERN),
            "decision_hash": _hash(),
            "book_id": _string(pattern=_BOOK_ID_PATTERN),
            "ordered_economic_event_ids": _array(_string(pattern=_EVENT_ID_PATTERN), min_items=1, unique=True),
            "snapshots": _array(_ref("gv_fs0_snapshot_v1"), min_items=5, max_items=10),
            "terminal_snapshot_id": _string(pattern=_SNAPSHOT_ID_PATTERN),
        },
    )
    verifier_result_properties = {
        "schema_version": {"const": "GV_FS0_VERIFIER_RESULT_V1"},
        **_binding_properties(),
        "verifier_input_hash": _hash(),
        "verifier_status": _string(enum=["RECONSTRUCTED", "REJECTED"]),
        "reconstructed_economic_payload": {"oneOf": [{"type": "null"}, economic_payload]},
        "reconstructed_economic_payload_hash": {"oneOf": [{"type": "null"}, _hash()]},
        "failure_codes": _array(_string(pattern="^[A-Z][A-Z0-9_]{0,127}$"), unique=True),
    }
    verifier_result = _schema(
        "gv_fs0_verifier_result_v1",
        _object(
            list(verifier_result_properties),
            verifier_result_properties,
            allOf=[
                {
                    "if": {"properties": {"verifier_status": {"const": "RECONSTRUCTED"}}, "required": ["verifier_status"]},
                    "then": {
                        "properties": {
                            "reconstructed_economic_payload": {"not": {"type": "null"}},
                            "reconstructed_economic_payload_hash": _hash(),
                            "failure_codes": {"maxItems": 0},
                        }
                    },
                },
                {
                    "if": {"properties": {"verifier_status": {"const": "REJECTED"}}, "required": ["verifier_status"]},
                    "then": {
                        "properties": {
                            "reconstructed_economic_payload": {"type": "null"},
                            "reconstructed_economic_payload_hash": {"type": "null"},
                            "failure_codes": {"minItems": 1},
                        }
                    },
                },
            ],
        ),
    )

    verifier_attempt = _schema(
        "gv_fs0_verifier_attempt_v1",
        _object(
            ["ordinal", "outcome", "verifier_result_hash", "controller_failure_code"],
            {
                "ordinal": _integer(minimum=1, maximum=2),
                "outcome": _string(enum=["RESULT", "INFRASTRUCTURE_FAILURE"]),
                "verifier_result_hash": {"oneOf": [{"type": "null"}, _hash()]},
                "controller_failure_code": {
                    "oneOf": [{"type": "null"}, _string(pattern="^VERIFIER_[A-Z0-9_]+$")]
                },
            },
            allOf=[
                {
                    "if": {"properties": {"outcome": {"const": "RESULT"}}, "required": ["outcome"]},
                    "then": {
                        "properties": {
                            "verifier_result_hash": _hash(),
                            "controller_failure_code": {"type": "null"},
                        }
                    },
                },
                {
                    "if": {
                        "properties": {"outcome": {"const": "INFRASTRUCTURE_FAILURE"}},
                        "required": ["outcome"],
                    },
                    "then": {
                        "properties": {
                            "verifier_result_hash": {"type": "null"},
                            "controller_failure_code": _string(pattern="^VERIFIER_[A-Z0-9_]+$"),
                        }
                    },
                },
            ],
        ),
    )

    checks_object = _object(
        list(MANDATORY_CHECKS),
        {check: _string(enum=["TRUE", "FALSE", "UNKNOWN"]) for check in MANDATORY_CHECKS},
    )
    failure_binding = _object(
        ["check", "outcome", "code"],
        {
            "check": _string(enum=list(MANDATORY_CHECKS)),
            "outcome": _string(enum=["FALSE", "UNKNOWN"]),
            "code": _string(pattern="^[A-Z][A-Z0-9_]{0,127}$"),
        },
    )
    certification = _schema(
        "gv_fs0_certification_v1",
        _object(
            [
                "schema_version",
                "certification_id",
                "protocol_id",
                "protocol_version",
                "fixture_id",
                "fixture_hash",
                "decision_id",
                "decision_hash",
                "book_id",
                "terminal_snapshot_id",
                "primary_economic_payload_hash",
                "verifier_input_hash",
                "verifier_attempts",
                "checks",
                "certification_status",
                "certification_failure_registry_version",
                "certification_failure_registry_hash",
                "failure_bindings",
            ],
            {
                "schema_version": {"const": "GV_FS0_CERTIFICATION_V1"},
                "certification_id": _string(pattern=_CERTIFICATION_ID_PATTERN),
                "protocol_id": {"const": PROTOCOL_ID},
                "protocol_version": {"const": PROTOCOL_VERSION},
                "fixture_id": _string(pattern=_TOKEN_PATTERN),
                "fixture_hash": _hash(),
                "decision_id": _string(pattern=_TOKEN_PATTERN),
                "decision_hash": _hash(),
                "book_id": _string(pattern=_BOOK_ID_PATTERN),
                "terminal_snapshot_id": _string(pattern=_SNAPSHOT_ID_PATTERN),
                "primary_economic_payload_hash": _hash(),
                "verifier_input_hash": _hash(),
                "verifier_attempts": _array(_ref("gv_fs0_verifier_attempt_v1"), min_items=2, max_items=2),
                "checks": checks_object,
                "certification_status": _string(enum=["CERTIFIED", "BLOCKED"]),
                "certification_failure_registry_version": {"const": "GV_FS0_CERTIFICATION_FAILURE_REGISTRY_V1"},
                "certification_failure_registry_hash": _hash(),
                "failure_bindings": _array(failure_binding, unique=True),
            },
        ),
    )

    retained_result = _object(
        ["verifier_result_hash", "verifier_result"],
        {"verifier_result_hash": _hash(), "verifier_result": _ref("gv_fs0_verifier_result_v1")},
    )
    binding = _object(
        ["fixture_id", "fixture_hash", "decision_id", "decision_hash"],
        {
            "fixture_id": _string(pattern=_TOKEN_PATTERN),
            "fixture_hash": _hash(),
            "decision_id": _string(pattern=_TOKEN_PATTERN),
            "decision_hash": _hash(),
        },
    )
    presentation = _object(
        ["authority", "action", "rationale_ref", "canonical_hashes", "certification_status"],
        {
            "authority": {"const": "MANUAL_OWNER_PAPER"},
            "action": _string(enum=["OPEN", "NO_POSITION"]),
            "rationale_ref": _string(pattern=_RATIONALE_PATTERN),
            "canonical_hashes": _array(_hash(), min_items=1, unique=True),
            "certification_status": {"const": "CERTIFIED"},
        },
    )
    certified_decision_result = _schema(
        "gv_fs0_certified_decision_result_v1",
        _object(
            [
                "schema_version",
                "certified_decision_result_id",
                "certified_decision_result_hash",
                "binding",
                "book_id",
                "canonical_event_trail",
                "snapshots",
                "economic_payload_hash",
                "verifier_attempts",
                "retained_verifier_results",
                "certification",
                "certification_reference_event",
                "presentation",
                "presentation_hash",
            ],
            {
                "schema_version": {"const": "GV_FS0_CERTIFIED_DECISION_RESULT_V1"},
                "certified_decision_result_id": _string(pattern=_CDR_ID_PATTERN),
                "certified_decision_result_hash": _hash(),
                "binding": binding,
                "book_id": _string(pattern=_BOOK_ID_PATTERN),
                "canonical_event_trail": _array(_ref("gv_fs0_portfolio_event_v1"), min_items=1),
                "snapshots": _array(_ref("gv_fs0_snapshot_v1"), min_items=5, max_items=10),
                "economic_payload_hash": _hash(),
                "verifier_attempts": _array(_ref("gv_fs0_verifier_attempt_v1"), min_items=2, max_items=2),
                "retained_verifier_results": _array(retained_result, min_items=1, max_items=2),
                "certification": _ref("gv_fs0_certification_v1"),
                "certification_reference_event": _ref("gv_fs0_portfolio_event_v1"),
                "presentation": presentation,
                "presentation_hash": _hash(),
            },
        ),
    )

    certified_bundle = _schema(
        "gv_fs0_certified_bundle_v1",
        _object(
            ["schema_version", "protocol_id", "protocol_version", "currency", "open_result", "no_position_result", "bundle_hash", "bundle_id"],
            {
                "schema_version": {"const": "GV_FS0_CERTIFIED_BUNDLE_V1"},
                "protocol_id": {"const": PROTOCOL_ID},
                "protocol_version": {"const": PROTOCOL_VERSION},
                "currency": _string(pattern="^[A-Z]{3}$"),
                "open_result": _ref("gv_fs0_certified_decision_result_v1"),
                "no_position_result": _ref("gv_fs0_certified_decision_result_v1"),
                "bundle_hash": _hash(),
                "bundle_id": _string(pattern=_BUNDLE_ID_PATTERN),
            },
        ),
    )

    blocked_evidence = _schema(
        "gv_fs0_blocked_evidence_v1",
        _object(
            ["schema_version", "protocol_id", "publishable", "certification_status", "decision_id", "failure_bindings", "verifier_attempts"],
            {
                "schema_version": {"const": "GV_FS0_BLOCKED_EVIDENCE_V1"},
                "protocol_id": {"const": PROTOCOL_ID},
                "publishable": {"const": False},
                "certification_status": {"const": "BLOCKED"},
                "decision_id": _string(pattern=_TOKEN_PATTERN),
                "failure_bindings": _array(failure_binding, min_items=1, unique=True),
                "verifier_attempts": _array(_ref("gv_fs0_verifier_attempt_v1"), min_items=2, max_items=2),
            },
        ),
    )

    schemas = {
        "gv_fs0_source_fixture_v1": source_fixture,
        "gv_fs0_decision_envelope_v1": decision_envelope,
        "gv_fs0_source_intent_v1": source_intent,
        "gv_fs0_portfolio_event_v1": portfolio_event,
        "gv_fs0_snapshot_v1": snapshot,
        "gv_fs0_verifier_input_v1": verifier_input,
        "gv_fs0_verifier_result_v1": verifier_result,
        "gv_fs0_verifier_attempt_v1": verifier_attempt,
        "gv_fs0_certification_v1": certification,
        "gv_fs0_certified_decision_result_v1": certified_decision_result,
        "gv_fs0_certified_bundle_v1": certified_bundle,
        "gv_fs0_blocked_evidence_v1": blocked_evidence,
    }
    if tuple(schemas) != SCHEMA_NAMES:
        raise AssertionError("schema order does not match the frozen artifact set")
    return schemas


def build_schema_bundle() -> dict[str, Any]:
    return {
        "protocol_id": PROTOCOL_ID,
        "schema_version": "GV_FS0_SCHEMA_BUNDLE_V1",
        "schemas": build_schemas(),
    }


def _failure_entry(
    code: str,
    category: str,
    terminal_or_recoverable: str,
    checks: list[str],
    outcomes: list[str],
    emitters: list[str],
    message: str,
    recovery: str,
) -> dict[str, Any]:
    return {
        "applicable_checks": checks,
        "applicable_emitters": emitters,
        "applicable_outcomes": outcomes,
        "applicable_schema_versions": ["GV_FS0_CERTIFICATION_V1"],
        "category": category,
        "code": code,
        "operator_recovery_reference": recovery,
        "stable_user_message": message,
        "terminal_or_recoverable": terminal_or_recoverable,
    }


def build_certification_failure_registry() -> dict[str, Any]:
    entries = [
        _failure_entry("DECISION_AUTHORITY_INVALID", "PRIMARY_VALIDATION", "TERMINAL", ["decision_authority_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Decision authority is invalid.", "GV_FS0_RECOVERY:DECISION_AUTHORITY"),
        _failure_entry("TIMESTAMP_CAUSALITY_INVALID", "PRIMARY_VALIDATION", "TERMINAL", ["timestamp_causality_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Timestamp causality is invalid.", "GV_FS0_RECOVERY:TIMESTAMP_CAUSALITY"),
        _failure_entry("PRICE_FRESHNESS_INVALID", "PRIMARY_VALIDATION", "TERMINAL", ["price_freshness_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "A required price is missing, stale, duplicated, non-positive, mismatched, or unordered.", "GV_FS0_RECOVERY:PRICE_FRESHNESS"),
        _failure_entry("CASH_CONSERVATION_FAILED", "ECONOMIC_RECONCILIATION", "TERMINAL", ["cash_conserved"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Cash does not reconcile under the V1 transition rules.", "GV_FS0_RECOVERY:CASH_RECONCILIATION"),
        _failure_entry("HOLDINGS_INVALID", "ECONOMIC_RECONCILIATION", "TERMINAL", ["holdings_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Holdings violate the V1 constraints.", "GV_FS0_RECOVERY:HOLDINGS"),
        _failure_entry("NAV_RECONCILIATION_FAILED", "ECONOMIC_RECONCILIATION", "TERMINAL", ["nav_reconciled"], ["FALSE"], ["PRIMARY", "VERIFIER"], "NAV does not reconcile exactly.", "GV_FS0_RECOVERY:NAV_RECONCILIATION"),
        _failure_entry("RECEIVABLES_RECONCILIATION_FAILED", "ECONOMIC_RECONCILIATION", "TERMINAL", ["receivables_reconciled"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Dividend receivables do not reconcile exactly.", "GV_FS0_RECOVERY:RECEIVABLES"),
        _failure_entry("UNSUPPORTED_EVENT", "PROTOCOL_VALIDATION", "TERMINAL", ["unsupported_events_absent"], ["FALSE"], ["PRIMARY", "VERIFIER"], "An unsupported event, rank, slot, or transition is present.", "GV_FS0_RECOVERY:UNSUPPORTED_EVENT"),
        _failure_entry("VERIFIER_REJECTED", "VERIFIER_RESULT", "TERMINAL", ["independent_reconstruction_passed"], ["FALSE"], ["VERIFIER"], "The independent verifier deterministically rejected the input.", "GV_FS0_RECOVERY:VERIFIER_REJECTION"),
        _failure_entry("CANONICAL_HASH_MISMATCH", "CANONICALIZATION", "TERMINAL", ["canonical_hash_reproduced"], ["FALSE"], ["PRIMARY", "VERIFIER", "CONTROLLER"], "Canonical bytes or hashes differ.", "GV_FS0_RECOVERY:CANONICAL_HASH"),
    ]
    controller_codes = (
        ("VERIFIER_SUPERVISION_INCOMPLETE", "Verifier supervision did not reach a classifiable terminal state."),
        ("VERIFIER_TIMEOUT", "The independent verifier exceeded the execution deadline."),
        ("VERIFIER_OUTPUT_LIMIT_EXCEEDED", "The independent verifier exceeded a stream byte limit."),
        ("VERIFIER_PROCESS_FAILED", "The independent verifier process failed."),
        ("VERIFIER_STDERR_NONEMPTY", "The independent verifier emitted stderr on a nominal result path."),
        ("VERIFIER_OUTPUT_INVALID_UTF8", "The independent verifier output is not strict UTF-8."),
        ("VERIFIER_OUTPUT_NOT_CANONICAL", "The independent verifier output is not one canonical JSON document."),
        ("VERIFIER_OUTPUT_SCHEMA_INVALID", "The independent verifier output does not satisfy the result schema."),
        ("VERIFIER_RESULT_BINDING_INVALID", "The independent verifier result bindings are invalid."),
    )
    for code, message in controller_codes:
        entries.append(
            _failure_entry(
                code,
                "VERIFIER_INFRASTRUCTURE",
                "RECOVERABLE",
                ["independent_reconstruction_passed", "canonical_hash_reproduced"],
                ["UNKNOWN"],
                ["CONTROLLER"],
                message,
                f"GV_FS0_RECOVERY:{code}",
            )
        )
    entries.sort(key=lambda item: item["code"])
    registry = {
        "entries": entries,
        "protocol_id": PROTOCOL_ID,
        "registry_version": "GV_FS0_CERTIFICATION_FAILURE_REGISTRY_V1",
    }
    return {
        "registry": registry,
        "registry_hash": domain_hash("GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1", registry),
        "schema_version": "GV_FS0_CERTIFICATION_FAILURE_REGISTRY_ARTIFACT_V1",
    }


def build_operational_error_registry() -> dict[str, Any]:
    entries = [
        {
            "applicable_schema_versions": ["GV_FS0_CERTIFIED_BUNDLE_V1"],
            "category": "PUBLICATION",
            "code": "PUBLICATION_LOCKED",
            "operator_recovery_reference": "GV_FS0_RECOVERY:PUBLICATION_LOCK",
            "stable_user_message": "Publication is locked by another or recovery-required operation.",
            "terminal_or_recoverable": "RECOVERABLE",
        },
        {
            "applicable_schema_versions": ["GV_FS0_CERTIFIED_BUNDLE_V1"],
            "category": "PUBLICATION",
            "code": "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
            "operator_recovery_reference": "GV_FS0_RECOVERY:POST_REPLACE_VERIFICATION",
            "stable_user_message": "The replaced target could not be verified; automatic publication remains blocked.",
            "terminal_or_recoverable": "TERMINAL",
        },
        {
            "applicable_schema_versions": ["GV_FS0_CERTIFIED_BUNDLE_V1"],
            "category": "PUBLICATION",
            "code": "PUBLICATION_RECOVERY_RECORD_FAILED",
            "operator_recovery_reference": "GV_FS0_RECOVERY:RECOVERY_RECORD",
            "stable_user_message": "The durable recovery record could not be replaced; operator inspection is required.",
            "terminal_or_recoverable": "TERMINAL",
        },
        {
            "applicable_schema_versions": ["GV_FS0_CERTIFIED_BUNDLE_V1"],
            "category": "PUBLICATION",
            "code": "PUBLICATION_TARGET_CHANGED",
            "operator_recovery_reference": "GV_FS0_RECOVERY:TARGET_CHANGED",
            "stable_user_message": "The publication target changed after candidate construction.",
            "terminal_or_recoverable": "RECOVERABLE",
        },
    ]
    entries.sort(key=lambda item: item["code"])
    registry = {
        "entries": entries,
        "protocol_id": PROTOCOL_ID,
        "registry_version": "GV_FS0_OPERATIONAL_ERROR_REGISTRY_V1",
    }
    return {
        "registry": registry,
        "registry_hash": domain_hash("GV-FS0:OPERATIONAL_ERROR_REGISTRY:V1", registry),
        "schema_version": "GV_FS0_OPERATIONAL_ERROR_REGISTRY_ARTIFACT_V1",
    }


def build_event_ranks() -> dict[str, Any]:
    return {
        "event_ranks": [
            {"event_type": "DECISION_ACCEPTED", "rank": 10},
            {"event_type": "EXECUTION", "rank": 20},
            {"event_type": "FEE_OR_COST", "rank": 30},
            {"event_type": "CASH_MOVEMENT", "rank": 40},
            {"event_type": "POSITION_MOVEMENT", "rank": 50},
            {"event_type": "DIVIDEND_ENTITLEMENT", "rank": 60},
            {"event_type": "DIVIDEND_PAYMENT", "rank": 70},
            {"event_type": "SESSION_VALUATION", "rank": 80},
            {"event_type": "CERTIFICATION_REFERENCE", "rank": 90},
        ],
        "protocol_id": PROTOCOL_ID,
        "schema_version": "GV_FS0_EVENT_RANKS_V1",
    }


def build_generated_event_slots() -> dict[str, Any]:
    return {
        "generated_event_slots": [
            {"generated_event_slot": 10, "generated_event_type": "DECISION_ACCEPTED", "source_intent_type": "DECISION_ENVELOPE"},
            {"generated_event_slot": 10, "generated_event_type": "EXECUTION", "source_intent_type": "EXECUTION_INTENT"},
            {"generated_event_slot": 20, "generated_event_type": "CASH_MOVEMENT", "source_intent_type": "EXECUTION_INTENT"},
            {"generated_event_slot": 30, "generated_event_type": "POSITION_MOVEMENT", "source_intent_type": "EXECUTION_INTENT"},
            {"generated_event_slot": 10, "generated_event_type": "FEE_OR_COST", "source_intent_type": "EXPLICIT_FEE"},
            {"generated_event_slot": 20, "generated_event_type": "CASH_MOVEMENT", "source_intent_type": "EXPLICIT_FEE"},
            {"generated_event_slot": 10, "generated_event_type": "DIVIDEND_ENTITLEMENT", "source_intent_type": "DIVIDEND_DECLARATION"},
            {"generated_event_slot": 10, "generated_event_type": "DIVIDEND_PAYMENT", "source_intent_type": "DIVIDEND_PAYMENT_INSTRUCTION"},
            {"generated_event_slot": 10, "generated_event_type": "SESSION_VALUATION", "source_intent_type": "VALUATION_INSTRUCTION"},
            {"generated_event_slot": 10, "generated_event_type": "CERTIFICATION_REFERENCE", "source_intent_type": "CERTIFICATION"},
        ],
        "protocol_id": PROTOCOL_ID,
        "schema_version": "GV_FS0_GENERATED_EVENT_SLOTS_V1",
    }


def build_transition_ownership() -> dict[str, Any]:
    return {
        "protocol_id": PROTOCOL_ID,
        "schema_version": "GV_FS0_TRANSITION_OWNERSHIP_V1",
        "transition_ownership": [
            {"cash": "NONE", "event_type": "DECISION_ACCEPTED", "other_responsibility": "AUDIT_ONLY", "receivables": "NONE", "shares": "NONE"},
            {"cash": "NONE", "event_type": "EXECUTION", "other_responsibility": "EXECUTION_AUTHORITY_ONLY", "receivables": "NONE", "shares": "NONE"},
            {"cash": "NONE", "event_type": "FEE_OR_COST", "other_responsibility": "FEE_AUTHORITY_ONLY", "receivables": "NONE", "shares": "NONE"},
            {"cash": "APPLY_DECLARED_DELTA_ONCE", "event_type": "CASH_MOVEMENT", "other_responsibility": "NONE", "receivables": "NONE", "shares": "NONE"},
            {"cash": "NONE", "event_type": "POSITION_MOVEMENT", "other_responsibility": "NONE", "receivables": "NONE", "shares": "APPLY_DECLARED_DELTA_ONCE"},
            {"cash": "NONE", "event_type": "DIVIDEND_ENTITLEMENT", "other_responsibility": "CREATE_RECEIVABLE_ONCE", "receivables": "INCREASE_ONCE", "shares": "NONE"},
            {"cash": "INCREASE_ONCE", "event_type": "DIVIDEND_PAYMENT", "other_responsibility": "ATOMICALLY_SETTLE_ONE_ENTITLEMENT", "receivables": "DECREASE_ONCE", "shares": "NONE"},
            {"cash": "NONE", "event_type": "SESSION_VALUATION", "other_responsibility": "RECORD_POST_TRANSITION_VALUATION_ONLY", "receivables": "NONE", "shares": "NONE"},
            {"cash": "NONE", "event_type": "CERTIFICATION_REFERENCE", "other_responsibility": "AUDIT_REFERENCE_ONLY", "receivables": "NONE", "shares": "NONE"},
        ],
    }


def build_canonical_vectors() -> dict[str, Any]:
    raw_vectors = [
        {
            "domain": "GV-FS0:FIXTURE:V1",
            "name": "unicode_controls_and_integer_bounds",
            "value": {
                "a": "slash/ line paragraph  CJK漢字 emoji😀",
                "controls": "\b\t\n\f\r\u0000\u000b\u001f",
                "quote_and_slash": "\"\\/",
                "z": [0, 1, 9_007_199_254_740_991],
            },
        },
        {
            "domain": "GV-FS0:VERIFIER_INPUT:V1",
            "name": "normalized_scalar_projection",
            "value": {
                "date": "2026-07-17",
                "decimal": "1.23",
                "text": "é",
                "timestamp": "2026-07-16T17:00:00.000000Z",
            },
        },
        {
            "domain": "GV-FS0:BOOK_ID:V1",
            "name": "book_identity_preimage",
            "value": {
                "decision_hash": "1" * 64,
                "decision_id": "DECISION:OPEN:001",
                "fixture_hash": "2" * 64,
                "fixture_id": "FIXTURE:GV_FS0:OPEN:001",
                "protocol_id": PROTOCOL_ID,
            },
        },
    ]
    vectors: list[dict[str, Any]] = []
    for vector in raw_vectors:
        document = canonical_document_bytes(vector["value"])
        preimage = domain_preimage(vector["domain"], vector["value"])
        vectors.append(
            {
                "canonical_document_hex": document.hex(),
                "canonical_json_text_utf8_hex": document[:-1].hex(),
                "domain": vector["domain"],
                "hash_preimage_hex": preimage.hex(),
                "hash_preimage_length": len(preimage),
                "name": vector["name"],
                "sha256": hashlib.sha256(preimage).hexdigest(),
            }
        )
    return {
        "protocol_id": PROTOCOL_ID,
        "schema_version": "GV_FS0_CANONICAL_VECTORS_V1",
        "vectors": vectors,
    }


def base_artifact_objects() -> dict[str, dict[str, Any]]:
    return {
        SCHEMA_BUNDLE_PATH: build_schema_bundle(),
        CERTIFICATION_FAILURE_REGISTRY_PATH: build_certification_failure_registry(),
        OPERATIONAL_ERROR_REGISTRY_PATH: build_operational_error_registry(),
        EVENT_RANKS_PATH: build_event_ranks(),
        GENERATED_EVENT_SLOTS_PATH: build_generated_event_slots(),
        TRANSITION_OWNERSHIP_PATH: build_transition_ownership(),
        CANONICAL_VECTORS_PATH: build_canonical_vectors(),
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_freeze_manifest() -> dict[str, Any]:
    base_documents = {path: canonical_document_bytes(value) for path, value in base_artifact_objects().items()}
    schemas = build_schemas()
    return {
        "authority_transfer": [
            {"path": CONTRACT_PATH, "sha256": CONTRACT_SHA256, "size_bytes": CONTRACT_SIZE},
            {"path": PHASE_BRIEF_PATH, "sha256": PHASE_BRIEF_SHA256, "size_bytes": PHASE_BRIEF_SIZE},
        ],
        "frozen_files": [
            {"path": path, "sha256": _sha256(data), "size_bytes": len(data)}
            for path, data in sorted(base_documents.items())
        ],
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "schema_hashes": [
            {
                "name": name,
                "sha256": _sha256(canonical_document_bytes(schema)),
                "size_bytes": len(canonical_document_bytes(schema)),
            }
            for name, schema in schemas.items()
        ],
        "schema_version": "GV_FS0_FREEZE_MANIFEST_V1",
    }


def expected_documents() -> dict[str, bytes]:
    documents = {path: canonical_document_bytes(value) for path, value in base_artifact_objects().items()}
    documents[FREEZE_MANIFEST_PATH] = canonical_document_bytes(build_freeze_manifest())
    return documents


def verifier_result_hash(result: dict[str, Any]) -> str:
    return domain_hash("GV-FS0:VERIFIER_RESULT:V1", result)


def canonical_failure_binding_key(binding: dict[str, str]) -> tuple[int, int, str]:
    return (CHECK_RANKS[binding["check"]], OUTCOME_RANKS[binding["outcome"]], binding["code"])


def project_verifier_input(source_fixture: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    """Project original source facts without creating events or economic state."""

    return {
        "decision": {
            "action": decision["action"],
            "authority": decision["authority_tier"],
            "decision_hash": decision["decision_hash"],
            "decision_id": decision["decision_id"],
            "decision_timestamp": decision["decision_timestamp"],
            "effective_timestamp": decision["effective_timestamp"],
            "rationale_reference": decision["rationale_ref"],
            "requested_sizing": decision["requested_quantity_or_sizing_input"],
            "security_id": decision["security_id"],
        },
        "prices": source_fixture["prices"],
        "protocol": {
            "currency": source_fixture["currency"],
            "fixture_hash": source_fixture["fixture_hash"],
            "fixture_id": source_fixture["fixture_id"],
            "initial_cash": source_fixture["initial_cash"],
            "protocol_id": source_fixture["protocol_id"],
            "protocol_version": PROTOCOL_VERSION,
        },
        "schema_version": "GV_FS0_VERIFIER_INPUT_V1",
        "source_intents": source_fixture["source_intents"],
    }


def assert_authority_files(root: Path) -> None:
    contract = (root / CONTRACT_PATH).read_bytes()
    brief = (root / PHASE_BRIEF_PATH).read_bytes()
    if len(contract) != CONTRACT_SIZE or _sha256(contract) != CONTRACT_SHA256:
        raise ValueError("reviewed GV-FS0 contract bytes do not match")
    if len(brief) != PHASE_BRIEF_SIZE or _sha256(brief) != PHASE_BRIEF_SHA256:
        raise ValueError("reviewed GV-FS0 phase brief bytes do not match")


def assert_sole_normative_protocol_source(root: Path) -> None:
    marker = b"Protocol ID: `GV_FS0_PROTOCOL_V1`"
    matches: list[str] = []
    for path in (root / "docs").rglob("*.md"):
        if marker in path.read_bytes():
            matches.append(path.relative_to(root).as_posix())
    if matches != [CONTRACT_PATH]:
        raise ValueError(f"sole normative V1 source violated: {matches}")


def assert_documents_match(root: Path) -> None:
    assert_authority_files(root)
    assert_sole_normative_protocol_source(root)
    for relative_path, expected in expected_documents().items():
        actual = (root / relative_path).read_bytes()
        if actual != expected:
            raise ValueError(f"generated V1 artifact differs: {relative_path}")
