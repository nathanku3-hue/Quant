"""Deterministically derive the 18 GV-FS0 Protocol V1 artifacts.

The consolidated contract is the semantic authority. The emitted artifacts are
its machine-readable normative expression. This generator is derivation
machinery only; CI checks that its protocol literals are present in the
contract and that its output exactly matches the checked-in artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_fs0_canonical import (
    CanonicalizationError,
    canonical_decimal,
    canonical_document_bytes,
    canonical_timestamp,
    domain_hash,
    domain_preimage,
)

CONTRACT = ROOT / "docs/architecture/gv_fs0_certification_and_data_authority_contract.md"
ARTIFACT_ROOT = ROOT / "contracts/gv_fs0/v1"
PROTOCOL_ID = "GV_FS0_PROTOCOL_V1"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
HASH_PATTERN = "^[0-9a-f]{64}$"
DECIMAL_PATTERN = "^(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"
DATE_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
TIMESTAMP_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{6}Z$"
TOKEN_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"
SOURCE_INTENT_PATTERN = "^[A-Z][A-Z0-9_]*:[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"


def _object(properties: dict[str, Any], required: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
        **extra,
    }


def _schema(name: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": DRAFT,
        "$id": f"urn:terminal-zero:gv-fs0:{name}",
        "title": name,
        **body,
    }


def _string(*, pattern: str | None = None, enum: list[str] | None = None, const: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "string"}
    if pattern is not None:
        result["pattern"] = pattern
    if enum is not None:
        result["enum"] = enum
    if const is not None:
        result["const"] = const
    return result


def _uint(maximum: int = 9_007_199_254_740_991) -> dict[str, Any]:
    return {"type": "integer", "minimum": 0, "maximum": maximum}


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"anyOf": [schema, {"type": "null"}]}


def _source_price_schema() -> dict[str, Any]:
    return _object(
        {
            "security_id": _string(pattern=TOKEN_PATTERN),
            "session": _string(pattern=DATE_PATTERN),
            "price_timestamp": _string(pattern=TIMESTAMP_PATTERN),
            "close_price": _string(pattern=DECIMAL_PATTERN),
            "source_sequence": _uint(),
        },
        ["security_id", "session", "price_timestamp", "close_price", "source_sequence"],
    )


def _source_intent_schema() -> dict[str, Any]:
    properties = {
        "schema_version": _string(const="gv_fs0_source_intent_v1"),
        "source_intent_id": _string(pattern=SOURCE_INTENT_PATTERN),
        "source_sequence": _uint(),
        "intent_type": _string(enum=[
            "EXECUTION_INTENT",
            "EXPLICIT_FEE",
            "DIVIDEND_DECLARATION",
            "DIVIDEND_PAYMENT_INSTRUCTION",
            "VALUATION_INSTRUCTION",
        ]),
        "effective_timestamp": _string(pattern=TIMESTAMP_PATTERN),
        "session": _string(pattern=DATE_PATTERN),
        "security_id": _string(pattern=TOKEN_PATTERN),
        "quantity": _nullable(_uint()),
        "execution_price": _nullable(_string(pattern=DECIMAL_PATTERN)),
        "fee": _nullable(_string(pattern=DECIMAL_PATTERN)),
        "dividend_amount_per_share": _nullable(_string(pattern=DECIMAL_PATTERN)),
        "referenced_entitlement_source_intent_id": _nullable(_string(pattern=SOURCE_INTENT_PATTERN)),
        "valuation_timestamp": _nullable(_string(pattern=TIMESTAMP_PATTERN)),
    }
    common = ["schema_version", "source_intent_id", "source_sequence", "intent_type", "effective_timestamp", "session", "security_id", "quantity", "execution_price", "fee", "dividend_amount_per_share", "referenced_entitlement_source_intent_id", "valuation_timestamp"]
    return _schema(
        "gv_fs0_source_intent_v1",
        _object(
            properties,
            common,
            allOf=[
                {
                    "if": {"properties": {"intent_type": {"const": "EXECUTION_INTENT"}}},
                    "then": {"properties": {"quantity": _uint(), "execution_price": _string(pattern=DECIMAL_PATTERN)}},
                },
                {
                    "if": {"properties": {"intent_type": {"const": "EXPLICIT_FEE"}}},
                    "then": {"properties": {"fee": _string(pattern=DECIMAL_PATTERN)}},
                },
                {
                    "if": {"properties": {"intent_type": {"const": "DIVIDEND_DECLARATION"}}},
                    "then": {"properties": {"dividend_amount_per_share": _string(pattern=DECIMAL_PATTERN)}},
                },
                {
                    "if": {"properties": {"intent_type": {"const": "VALUATION_INSTRUCTION"}}},
                    "then": {"properties": {"valuation_timestamp": _string(pattern=TIMESTAMP_PATTERN)}},
                },
            ],
        ),
    )


def _schemas() -> dict[str, dict[str, Any]]:
    source_intent = _source_intent_schema()
    source_fixture = _schema(
        "gv_fs0_source_fixture_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_source_fixture_v1"),
                "protocol_id": _string(const=PROTOCOL_ID),
                "fixture_id": _string(pattern=TOKEN_PATTERN),
                "currency": _string(pattern="^[A-Z]{3}$"),
                "security_id": _string(pattern=TOKEN_PATTERN),
                "initial_cash": _string(pattern=DECIMAL_PATTERN),
                "sessions": {"type": "array", "minItems": 5, "maxItems": 10, "uniqueItems": True, "items": _string(pattern=DATE_PATTERN)},
                "source_prices": {"type": "array", "minItems": 1, "items": _source_price_schema()},
                "source_intents": {"type": "array", "minItems": 1, "items": {"$ref": "gv_fs0_source_intent_v1.schema.json"}},
            },
            ["schema_version", "protocol_id", "fixture_id", "currency", "security_id", "initial_cash", "sessions", "source_prices", "source_intents"],
        ),
    )
    decision = _schema(
        "gv_fs0_decision_envelope_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_decision_envelope_v1"),
                "decision_id": _string(pattern=TOKEN_PATTERN),
                "decision_hash": _string(pattern=HASH_PATTERN),
                "fixture_hash": _string(pattern=HASH_PATTERN),
                "authority_tier": _string(const="MANUAL_OWNER_PAPER"),
                "action": _string(enum=["OPEN", "NO_POSITION"]),
                "decision_timestamp": _string(pattern=TIMESTAMP_PATTERN),
                "effective_timestamp": _string(pattern=TIMESTAMP_PATTERN),
                "security_id": _string(pattern=TOKEN_PATTERN),
                "requested_quantity_or_sizing_input": _object(
                    {"quantity": _nullable(_uint())}, ["quantity"]
                ),
                "rationale_ref": _string(pattern="^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"),
                "protocol_id": _string(const=PROTOCOL_ID),
                "fixture_id": _string(pattern=TOKEN_PATTERN),
                "operator_id": _string(pattern=TOKEN_PATTERN),
                "supersedes_decision_id": _nullable(_string(pattern=TOKEN_PATTERN)),
            },
            ["schema_version", "decision_id", "decision_hash", "fixture_hash", "authority_tier", "action", "decision_timestamp", "effective_timestamp", "security_id", "requested_quantity_or_sizing_input", "rationale_ref", "protocol_id", "fixture_id", "operator_id", "supersedes_decision_id"],
        ),
    )
    event_payload = _object(
        {
            "quantity": _nullable(_uint()),
            "execution_price": _nullable(_string(pattern=DECIMAL_PATTERN)),
            "fee": _nullable(_string(pattern=DECIMAL_PATTERN)),
            "cash_delta": _nullable(_string(pattern="^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$")),
            "position_delta": _nullable(_string(pattern="^-?(?:0|[1-9][0-9]*)$")),
            "dividend_amount_per_share": _nullable(_string(pattern=DECIMAL_PATTERN)),
            "entitled_quantity": _nullable(_uint()),
            "receivable_amount": _nullable(_string(pattern=DECIMAL_PATTERN)),
            "payment_amount": _nullable(_string(pattern=DECIMAL_PATTERN)),
            "referenced_entitlement_id": _nullable(_string(pattern="^EVT_[0-9a-f]{64}$")),
            "valuation_price": _nullable(_string(pattern=DECIMAL_PATTERN)),
            "terminal_snapshot_id": _nullable(_string(pattern="^SNAP_[0-9a-f]{64}$")),
            "certification_id": _nullable(_string(pattern="^CERT_[0-9a-f]{64}$")),
        },
        ["quantity", "execution_price", "fee", "cash_delta", "position_delta", "dividend_amount_per_share", "entitled_quantity", "receivable_amount", "payment_amount", "referenced_entitlement_id", "valuation_price", "terminal_snapshot_id", "certification_id"],
    )
    event = _schema(
        "gv_fs0_portfolio_event_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_portfolio_event_v1"),
                "event_id": _string(pattern="^EVT_[0-9a-f]{64}$"),
                "book_id": _string(pattern="^BOOK_[0-9a-f]{64}$"),
                "decision_id": _string(pattern=TOKEN_PATTERN),
                "source_sequence": _uint(),
                "source_intent_id": _string(pattern=SOURCE_INTENT_PATTERN),
                "generated_event_slot": _uint(),
                "event_type": _string(enum=["DECISION_ACCEPTED", "EXECUTION", "FEE_OR_COST", "CASH_MOVEMENT", "POSITION_MOVEMENT", "DIVIDEND_ENTITLEMENT", "DIVIDEND_PAYMENT", "SESSION_VALUATION", "CERTIFICATION_REFERENCE"]),
                "effective_timestamp": _string(pattern=TIMESTAMP_PATTERN),
                "session": _string(pattern=DATE_PATTERN),
                "event_type_rank": _uint(90),
                "intra_rank_sequence": _uint(),
                "semantic_sequence": _uint(),
                "security_id": _string(pattern=TOKEN_PATTERN),
                "payload": event_payload,
            },
            ["schema_version", "event_id", "book_id", "decision_id", "source_sequence", "source_intent_id", "generated_event_slot", "event_type", "effective_timestamp", "session", "event_type_rank", "intra_rank_sequence", "semantic_sequence", "security_id", "payload"],
        ),
    )
    snapshot = _schema(
        "gv_fs0_snapshot_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_snapshot_v1"),
                "snapshot_id": _string(pattern="^SNAP_[0-9a-f]{64}$"),
                "session": _string(pattern=DATE_PATTERN),
                "valuation_timestamp": _string(pattern=TIMESTAMP_PATTERN),
                "book_id": _string(pattern="^BOOK_[0-9a-f]{64}$"),
                "decision_id": _string(pattern=TOKEN_PATTERN),
                "fixture_hash": _string(pattern=HASH_PATTERN),
                "authority_tier": _string(const="MANUAL_OWNER_PAPER"),
                "action": _string(enum=["OPEN", "NO_POSITION"]),
                "rationale_ref": _string(pattern="^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"),
                "security_id": _string(pattern=TOKEN_PATTERN),
                "shares": _uint(),
                "cash": _string(pattern=DECIMAL_PATTERN),
                "receivables": _string(pattern=DECIMAL_PATTERN),
                "market_value": _string(pattern=DECIMAL_PATTERN),
                "nav": _string(pattern=DECIMAL_PATTERN),
                "session_contribution": _string(pattern="^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"),
                "cumulative_contribution": _string(pattern="^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"),
                "applied_event_ids": {"type": "array", "uniqueItems": True, "items": _string(pattern="^EVT_[0-9a-f]{64}$")},
            },
            ["schema_version", "snapshot_id", "session", "valuation_timestamp", "book_id", "decision_id", "fixture_hash", "authority_tier", "action", "rationale_ref", "security_id", "shares", "cash", "receivables", "market_value", "nav", "session_contribution", "cumulative_contribution", "applied_event_ids"],
        ),
    )
    verifier_input = _schema(
        "gv_fs0_verifier_input_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_verifier_input_v1"),
                "protocol": _object(
                    {
                        "protocol_id": _string(const=PROTOCOL_ID),
                        "fixture_id": _string(pattern=TOKEN_PATTERN),
                        "fixture_hash": _string(pattern=HASH_PATTERN),
                        "currency": _string(pattern="^[A-Z]{3}$"),
                        "initial_cash": _string(pattern=DECIMAL_PATTERN),
                    },
                    ["protocol_id", "fixture_id", "fixture_hash", "currency", "initial_cash"],
                ),
                "decision": _object(
                    {
                        "decision_id": _string(pattern=TOKEN_PATTERN),
                        "decision_hash": _string(pattern=HASH_PATTERN),
                        "authority": _string(const="MANUAL_OWNER_PAPER"),
                        "action": _string(enum=["OPEN", "NO_POSITION"]),
                        "decision_timestamp": _string(pattern=TIMESTAMP_PATTERN),
                        "effective_timestamp": _string(pattern=TIMESTAMP_PATTERN),
                        "security_id": _string(pattern=TOKEN_PATTERN),
                        "requested_sizing": _object({"quantity": _nullable(_uint())}, ["quantity"]),
                        "rationale_reference": _string(pattern="^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"),
                    },
                    ["decision_id", "decision_hash", "authority", "action", "decision_timestamp", "effective_timestamp", "security_id", "requested_sizing", "rationale_reference"],
                ),
                "source_prices": {"type": "array", "items": _source_price_schema()},
                "source_intents": {"type": "array", "items": {"$ref": "gv_fs0_source_intent_v1.schema.json"}},
            },
            ["schema_version", "protocol", "decision", "source_prices", "source_intents"],
        ),
    )
    economic_payload = _object(
        {
            "protocol_id": _string(const=PROTOCOL_ID),
            "fixture_id": _string(pattern=TOKEN_PATTERN),
            "fixture_hash": _string(pattern=HASH_PATTERN),
            "decision_id": _string(pattern=TOKEN_PATTERN),
            "decision_hash": _string(pattern=HASH_PATTERN),
            "book_id": _string(pattern="^BOOK_[0-9a-f]{64}$"),
            "ordered_economic_event_ids": {"type": "array", "items": _string(pattern="^EVT_[0-9a-f]{64}$")},
            "snapshots": {"type": "array", "items": {"$ref": "gv_fs0_snapshot_v1.schema.json"}},
            "terminal_snapshot_id": _string(pattern="^SNAP_[0-9a-f]{64}$"),
        },
        ["protocol_id", "fixture_id", "fixture_hash", "decision_id", "decision_hash", "book_id", "ordered_economic_event_ids", "snapshots", "terminal_snapshot_id"],
    )
    verifier_result = _schema(
        "gv_fs0_verifier_result_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_verifier_result_v1"),
                "protocol_binding": _string(const=PROTOCOL_ID),
                "fixture_binding": _string(pattern=HASH_PATTERN),
                "decision_binding": _string(pattern=HASH_PATTERN),
                "verifier_input_hash": _string(pattern=HASH_PATTERN),
                "verifier_status": _string(enum=["RECONSTRUCTED", "REJECTED"]),
                "reconstructed_economic_payload": _nullable(economic_payload),
                "reconstructed_economic_payload_hash": _nullable(_string(pattern=HASH_PATTERN)),
                "failure_codes": {"type": "array", "uniqueItems": True, "items": _string(pattern="^[A-Z][A-Z0-9_]*$")},
            },
            ["schema_version", "protocol_binding", "fixture_binding", "decision_binding", "verifier_input_hash", "verifier_status", "reconstructed_economic_payload", "reconstructed_economic_payload_hash", "failure_codes"],
            allOf=[
                {"if": {"properties": {"verifier_status": {"const": "RECONSTRUCTED"}}}, "then": {"properties": {"reconstructed_economic_payload": economic_payload, "reconstructed_economic_payload_hash": _string(pattern=HASH_PATTERN), "failure_codes": {"maxItems": 0}}}},
                {"if": {"properties": {"verifier_status": {"const": "REJECTED"}}}, "then": {"properties": {"reconstructed_economic_payload": {"type": "null"}, "reconstructed_economic_payload_hash": {"type": "null"}, "failure_codes": {"minItems": 1}}}},
            ],
        ),
    )
    verifier_attempt = _schema(
        "gv_fs0_verifier_attempt_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_verifier_attempt_v1"),
                "ordinal": {"type": "integer", "enum": [1, 2]},
                "outcome": _string(enum=["RESULT", "INFRASTRUCTURE_FAILURE"]),
                "verifier_result_hash": _nullable(_string(pattern=HASH_PATTERN)),
                "controller_failure_code": _nullable(_string(pattern="^[A-Z][A-Z0-9_]*$")),
            },
            ["schema_version", "ordinal", "outcome", "verifier_result_hash", "controller_failure_code"],
            allOf=[
                {
                    "if": {"properties": {"outcome": {"const": "RESULT"}}},
                    "then": {"properties": {"verifier_result_hash": _string(pattern=HASH_PATTERN), "controller_failure_code": {"type": "null"}}},
                },
                {
                    "if": {"properties": {"outcome": {"const": "INFRASTRUCTURE_FAILURE"}}},
                    "then": {"properties": {"verifier_result_hash": {"type": "null"}, "controller_failure_code": _string(pattern="^[A-Z][A-Z0-9_]*$")}},
                },
            ],
        ),
    )
    check_properties = {name: _string(enum=["TRUE", "FALSE", "UNKNOWN"]) for name in [
        "decision_authority_valid", "timestamp_causality_valid", "price_freshness_valid", "cash_conserved", "holdings_valid", "nav_reconciled", "receivables_reconciled", "unsupported_events_absent", "independent_reconstruction_passed", "canonical_hash_reproduced"
    ]}
    binding = _object(
        {"check": _string(enum=list(check_properties)), "outcome": _string(enum=["FALSE", "UNKNOWN"]), "code": _string(pattern="^[A-Z][A-Z0-9_]*$")},
        ["check", "outcome", "code"],
    )
    certification = _schema(
        "gv_fs0_certification_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_certification_v1"),
                "certification_id": _string(pattern="^CERT_[0-9a-f]{64}$"),
                "protocol_id": _string(const=PROTOCOL_ID),
                "protocol_version": _string(const="V1"),
                "fixture_id": _string(pattern=TOKEN_PATTERN),
                "fixture_hash": _string(pattern=HASH_PATTERN),
                "decision_id": _string(pattern=TOKEN_PATTERN),
                "decision_hash": _string(pattern=HASH_PATTERN),
                "book_id": _string(pattern="^BOOK_[0-9a-f]{64}$"),
                "terminal_snapshot_id": _string(pattern="^SNAP_[0-9a-f]{64}$"),
                "primary_economic_payload_hash": _string(pattern=HASH_PATTERN),
                "verifier_input_hash": _string(pattern=HASH_PATTERN),
                "verifier_attempts": {"type": "array", "minItems": 2, "maxItems": 2, "prefixItems": [{"allOf": [{"$ref": "gv_fs0_verifier_attempt_v1.schema.json"}, {"properties": {"ordinal": {"const": 1}}}]}, {"allOf": [{"$ref": "gv_fs0_verifier_attempt_v1.schema.json"}, {"properties": {"ordinal": {"const": 2}}}]}], "items": False},
                "checks": _object(check_properties, list(check_properties)),
                "certification_status": _string(enum=["CERTIFIED", "BLOCKED"]),
                "certification_failure_registry_version": _string(const="gv_fs0_certification_failure_registry_v1"),
                "certification_failure_registry_hash": _string(pattern=HASH_PATTERN),
                "failure_bindings": {"type": "array", "items": binding},
            },
            ["schema_version", "certification_id", "protocol_id", "protocol_version", "fixture_id", "fixture_hash", "decision_id", "decision_hash", "book_id", "terminal_snapshot_id", "primary_economic_payload_hash", "verifier_input_hash", "verifier_attempts", "checks", "certification_status", "certification_failure_registry_version", "certification_failure_registry_hash", "failure_bindings"],
        ),
    )
    retained = _object(
        {"verifier_result_hash": _string(pattern=HASH_PATTERN), "verifier_result": {"$ref": "gv_fs0_verifier_result_v1.schema.json"}},
        ["verifier_result_hash", "verifier_result"],
    )
    certified_decision = _schema(
        "gv_fs0_certified_decision_result_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_certified_decision_result_v1"),
                "certified_decision_result_id": _string(pattern="^CDR_[0-9a-f]{64}$"),
                "certified_decision_result_hash": _string(pattern=HASH_PATTERN),
                "role": _string(enum=["OPEN", "NO_POSITION"]),
                "decision": {"$ref": "gv_fs0_decision_envelope_v1.schema.json"},
                "book_id": _string(pattern="^BOOK_[0-9a-f]{64}$"),
                "events": {"type": "array", "items": {"$ref": "gv_fs0_portfolio_event_v1.schema.json"}},
                "snapshots": {"type": "array", "minItems": 1, "items": {"$ref": "gv_fs0_snapshot_v1.schema.json"}},
                "economic_payload_hash": _string(pattern=HASH_PATTERN),
                "verifier_attempts": {"type": "array", "minItems": 2, "maxItems": 2, "prefixItems": [{"allOf": [{"$ref": "gv_fs0_verifier_attempt_v1.schema.json"}, {"properties": {"ordinal": {"const": 1}}}]}, {"allOf": [{"$ref": "gv_fs0_verifier_attempt_v1.schema.json"}, {"properties": {"ordinal": {"const": 2}}}]}], "items": False},
                "retained_verifier_results": {"type": "array", "uniqueItems": True, "items": retained},
                "certification": {"$ref": "gv_fs0_certification_v1.schema.json"},
                "certification_reference_event": {"$ref": "gv_fs0_portfolio_event_v1.schema.json"},
                "presentation": _object({"presentation_hash": _string(pattern=HASH_PATTERN), "rows": {"type": "array", "items": _object({"label": _string(pattern=TOKEN_PATTERN), "value": _string()}, ["label", "value"])}}, ["presentation_hash", "rows"]),
            },
            ["schema_version", "certified_decision_result_id", "certified_decision_result_hash", "role", "decision", "book_id", "events", "snapshots", "economic_payload_hash", "verifier_attempts", "retained_verifier_results", "certification", "certification_reference_event", "presentation"],
        ),
    )
    bundle = _schema(
        "gv_fs0_certified_bundle_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_certified_bundle_v1"),
                "protocol_id": _string(const=PROTOCOL_ID),
                "currency": _string(pattern="^[A-Z]{3}$"),
                "bundle_hash": _string(pattern=HASH_PATTERN),
                "bundle_id": _string(pattern="^BUNDLE_[0-9a-f]{64}$"),
                "components": {"type": "array", "minItems": 2, "maxItems": 2, "prefixItems": [{"allOf": [{"$ref": "gv_fs0_certified_decision_result_v1.schema.json"}, {"properties": {"role": {"const": "OPEN"}}}]}, {"allOf": [{"$ref": "gv_fs0_certified_decision_result_v1.schema.json"}, {"properties": {"role": {"const": "NO_POSITION"}}}]}], "items": False},
            },
            ["schema_version", "protocol_id", "currency", "bundle_hash", "bundle_id", "components"],
        ),
    )
    blocked = _schema(
        "gv_fs0_blocked_evidence_v1",
        _object(
            {
                "schema_version": _string(const="gv_fs0_blocked_evidence_v1"),
                "publishable": {"type": "boolean", "const": False},
                "certification_status": _string(const="BLOCKED"),
                "fixture_hash": _string(pattern=HASH_PATTERN),
                "decision_hash": _string(pattern=HASH_PATTERN),
                "verifier_attempts": {"type": "array", "minItems": 2, "maxItems": 2, "prefixItems": [{"allOf": [{"$ref": "gv_fs0_verifier_attempt_v1.schema.json"}, {"properties": {"ordinal": {"const": 1}}}]}, {"allOf": [{"$ref": "gv_fs0_verifier_attempt_v1.schema.json"}, {"properties": {"ordinal": {"const": 2}}}]}], "items": False},
                "failure_bindings": {"type": "array", "minItems": 1, "items": binding},
            },
            ["schema_version", "publishable", "certification_status", "fixture_hash", "decision_hash", "verifier_attempts", "failure_bindings"],
        ),
    )
    return {
        "gv_fs0_source_fixture_v1.schema.json": source_fixture,
        "gv_fs0_decision_envelope_v1.schema.json": decision,
        "gv_fs0_source_intent_v1.schema.json": source_intent,
        "gv_fs0_portfolio_event_v1.schema.json": event,
        "gv_fs0_snapshot_v1.schema.json": snapshot,
        "gv_fs0_verifier_input_v1.schema.json": verifier_input,
        "gv_fs0_verifier_result_v1.schema.json": verifier_result,
        "gv_fs0_verifier_attempt_v1.schema.json": verifier_attempt,
        "gv_fs0_certification_v1.schema.json": certification,
        "gv_fs0_certified_decision_result_v1.schema.json": certified_decision,
        "gv_fs0_certified_bundle_v1.schema.json": bundle,
        "gv_fs0_blocked_evidence_v1.schema.json": blocked,
    }


def _failure_entry(code: str, category: str, checks: list[str], outcomes: list[str], emitters: list[str], message: str) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "terminal_or_recoverable": "TERMINAL",
        "applicable_schema_versions": ["V1"],
        "applicable_checks": checks,
        "applicable_outcomes": outcomes,
        "applicable_emitters": emitters,
        "stable_user_message": message,
        "operator_recovery_reference": f"GV_FS0_RECOVERY:{code}",
    }


def _certification_registry() -> dict[str, Any]:
    entries = [
        _failure_entry("DECISION_AUTHORITY_INVALID", "AUTHORITY", ["decision_authority_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Decision authority is invalid."),
        _failure_entry("AUTHORITY_VALIDATION_UNAVAILABLE", "AUTHORITY", ["decision_authority_valid"], ["UNKNOWN"], ["PRIMARY", "CONTROLLER"], "Decision authority could not be validated."),
        _failure_entry("TIMESTAMP_CAUSALITY_INVALID", "CAUSALITY", ["timestamp_causality_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Timestamp or session causality is invalid."),
        _failure_entry("DUPLICATE_ORIGIN_ORDER_KEY", "CAUSALITY", ["timestamp_causality_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "A duplicate origin-order key was detected."),
        _failure_entry("PRICE_FRESHNESS_INVALID", "PRICE", ["price_freshness_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "A required same-session price is missing or invalid."),
        _failure_entry("PRICE_VALIDATION_UNAVAILABLE", "PRICE", ["price_freshness_valid"], ["UNKNOWN"], ["PRIMARY", "CONTROLLER"], "Price freshness could not be validated."),
        _failure_entry("CASH_CONSERVATION_FAILED", "ACCOUNTING", ["cash_conserved"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Cash did not reconcile."),
        _failure_entry("HOLDINGS_INVALID", "ACCOUNTING", ["holdings_valid"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Holdings are invalid."),
        _failure_entry("NAV_RECONCILIATION_FAILED", "ACCOUNTING", ["nav_reconciled"], ["FALSE"], ["PRIMARY", "VERIFIER"], "NAV did not reconcile."),
        _failure_entry("RECEIVABLES_RECONCILIATION_FAILED", "ACCOUNTING", ["receivables_reconciled"], ["FALSE"], ["PRIMARY", "VERIFIER"], "Receivables did not reconcile."),
        _failure_entry("UNSUPPORTED_EVENT", "EVENT", ["unsupported_events_absent"], ["FALSE"], ["PRIMARY", "VERIFIER"], "An unsupported event, rank, slot, or transition was found."),
        _failure_entry("INDEPENDENT_RECONSTRUCTION_FAILED", "VERIFIER", ["independent_reconstruction_passed"], ["FALSE"], ["VERIFIER", "CONTROLLER"], "Independent reconstruction did not match."),
        _failure_entry("INDEPENDENT_RECONSTRUCTION_UNAVAILABLE", "VERIFIER", ["independent_reconstruction_passed"], ["UNKNOWN"], ["CONTROLLER"], "Independent reconstruction was unavailable."),
        _failure_entry("CANONICAL_HASH_MISMATCH", "CANONICAL", ["canonical_hash_reproduced"], ["FALSE"], ["PRIMARY", "VERIFIER", "CONTROLLER"], "Canonical bytes or hashes differ."),
        _failure_entry("CANONICAL_HASH_UNAVAILABLE", "CANONICAL", ["canonical_hash_reproduced"], ["UNKNOWN"], ["CONTROLLER"], "Canonical hash reproduction was unavailable."),
    ]
    controller_codes = [
        "VERIFIER_SUPERVISION_INCOMPLETE", "VERIFIER_TIMEOUT", "VERIFIER_OUTPUT_LIMIT_EXCEEDED", "VERIFIER_PROCESS_FAILED", "VERIFIER_STDERR_NONEMPTY", "VERIFIER_OUTPUT_INVALID_UTF8", "VERIFIER_OUTPUT_NOT_CANONICAL", "VERIFIER_OUTPUT_SCHEMA_INVALID", "VERIFIER_RESULT_BINDING_INVALID"
    ]
    entries.extend(
        _failure_entry(code, "VERIFIER_INFRASTRUCTURE", ["independent_reconstruction_passed", "canonical_hash_reproduced"], ["UNKNOWN"], ["CONTROLLER"], code.replace("_", " ").title() + ".")
        for code in controller_codes
    )
    entries.sort(key=lambda entry: entry["code"])
    return {
        "registry_version": "gv_fs0_certification_failure_registry_v1",
        "protocol_id": PROTOCOL_ID,
        "entries": entries,
    }


def _operational_registry() -> dict[str, Any]:
    entries = []
    for code, category, recovery, message in [
        ("PUBLICATION_LOCKED", "PUBLICATION", "RECOVERABLE", "Publication is locked."),
        ("PUBLICATION_TARGET_CHANGED", "PUBLICATION", "RECOVERABLE", "The publication target changed concurrently."),
        ("PUBLICATION_POST_REPLACE_VERIFICATION_FAILED", "PUBLICATION", "TERMINAL", "Post-replace verification failed; no rollback is claimed."),
        ("PUBLICATION_RECOVERY_RECORD_FAILED", "RECOVERY", "TERMINAL", "The durable recovery record could not be written."),
    ]:
        entries.append({
            "code": code,
            "category": category,
            "terminal_or_recoverable": recovery,
            "applicable_schema_versions": ["V1"],
            "stable_user_message": message,
            "operator_recovery_reference": f"GV_FS0_RECOVERY:{code}",
        })
    entries.sort(key=lambda entry: entry["code"])
    return {"registry_version": "gv_fs0_operational_error_registry_v1", "protocol_id": PROTOCOL_ID, "entries": entries}


def _event_ranks() -> dict[str, Any]:
    ranks = [
        (10, "DECISION_ACCEPTED"), (20, "EXECUTION"), (30, "FEE_OR_COST"),
        (40, "CASH_MOVEMENT"), (50, "POSITION_MOVEMENT"), (60, "DIVIDEND_ENTITLEMENT"),
        (70, "DIVIDEND_PAYMENT"), (80, "SESSION_VALUATION"), (90, "CERTIFICATION_REFERENCE"),
    ]
    return {"table_version": "gv_fs0_event_ranks_v1", "protocol_id": PROTOCOL_ID, "entries": [{"event_type_rank": rank, "event_type": name} for rank, name in ranks]}


def _slots() -> dict[str, Any]:
    rows = [
        ("DECISION_ENVELOPE", "DECISION_ACCEPTED", 10),
        ("EXECUTION_INTENT", "EXECUTION", 10), ("EXECUTION_INTENT", "CASH_MOVEMENT", 20), ("EXECUTION_INTENT", "POSITION_MOVEMENT", 30),
        ("EXPLICIT_FEE", "FEE_OR_COST", 10), ("EXPLICIT_FEE", "CASH_MOVEMENT", 20),
        ("DIVIDEND_DECLARATION", "DIVIDEND_ENTITLEMENT", 10),
        ("DIVIDEND_PAYMENT_INSTRUCTION", "DIVIDEND_PAYMENT", 10),
        ("VALUATION_INSTRUCTION", "SESSION_VALUATION", 10),
        ("CERTIFICATION", "CERTIFICATION_REFERENCE", 10),
    ]
    return {"table_version": "gv_fs0_generated_event_slots_v1", "protocol_id": PROTOCOL_ID, "entries": [{"source_type": source, "event_type": event, "generated_event_slot": slot} for source, event, slot in rows]}


def _transition_ownership() -> dict[str, Any]:
    rows = [
        ("DECISION_ACCEPTED", "NONE", "NONE", "NONE", "AUDIT_ONLY"),
        ("EXECUTION", "NONE", "NONE", "NONE", "EXECUTION_AUTHORITY_ONLY"),
        ("FEE_OR_COST", "NONE", "NONE", "NONE", "FEE_AUTHORITY_ONLY"),
        ("CASH_MOVEMENT", "MUTATE_ONCE", "NONE", "NONE", "DECLARED_CASH_DELTA"),
        ("POSITION_MOVEMENT", "NONE", "MUTATE_ONCE", "NONE", "DECLARED_POSITION_DELTA"),
        ("DIVIDEND_ENTITLEMENT", "NONE", "NONE", "INCREASE_ONCE", "CREATE_RECEIVABLE"),
        ("DIVIDEND_PAYMENT", "INCREASE_ONCE", "NONE", "DECREASE_ONCE", "ATOMIC_SETTLEMENT"),
        ("SESSION_VALUATION", "NONE", "NONE", "NONE", "VALUATION_ONLY"),
        ("CERTIFICATION_REFERENCE", "NONE", "NONE", "NONE", "AUDIT_REFERENCE_ONLY"),
    ]
    return {"table_version": "gv_fs0_transition_ownership_v1", "protocol_id": PROTOCOL_ID, "entries": [{"event_type": event, "cash": cash, "shares": shares, "receivables": receivables, "responsibility": responsibility} for event, cash, shares, receivables, responsibility in rows]}


def _canonical_vectors() -> dict[str, Any]:
    accepted_inputs = [
        ("ascii", "GV-FS0:FIXTURE:V1", {"a": "plain", "z": 0}),
        ("escaping", "GV-FS0:FIXTURE:V1", {"text": "quote=\" slash=/ backslash=\\ controls=\b\t\n\f\r\u0000\u000b\u001f"}),
        ("unicode", "GV-FS0:FIXTURE:V1", {"text": "CJK=漢字 separators=   emoji=😀"}),
        ("decimal", "GV-FS0:ECONOMIC_PAYLOAD:V1", {"canonical": canonical_decimal("1.2300000"), "zero": canonical_decimal("0.000000")}),
        ("timestamp", "GV-FS0:VERIFIER_INPUT:V1", {"canonical": canonical_timestamp("2026-07-17T08:30:00+08:00")}),
        ("no_position_projection", "GV-FS0:VERIFIER_INPUT:V1", {"action": "NO_POSITION", "source_intents": []}),
    ]
    accepted = []
    for vector_id, domain, value in accepted_inputs:
        document = canonical_document_bytes(value)
        preimage = domain_preimage(domain, value)
        accepted.append({
            "vector_id": vector_id,
            "domain_prefix": domain,
            "semantic_value": value,
            "canonical_document_hex": document.hex(),
            "domain_preimage_hex": preimage.hex(),
            "preimage_byte_length": len(preimage),
            "sha256": domain_hash(domain, value),
        })
    rejected = [
        {"vector_id": "integer_negative", "input_token": "-1", "expected_code": "INTEGER_TOKEN_INVALID"},
        {"vector_id": "integer_plus", "input_token": "+1", "expected_code": "INTEGER_TOKEN_INVALID"},
        {"vector_id": "integer_leading_zero", "input_token": "01", "expected_code": "INTEGER_TOKEN_INVALID"},
        {"vector_id": "integer_decimal", "input_token": "1.0", "expected_code": "JSON_FLOAT_PROHIBITED"},
        {"vector_id": "integer_exponent", "input_token": "1e0", "expected_code": "JSON_FLOAT_PROHIBITED"},
        {"vector_id": "decimal_excess_precision", "input_token": "1.2300001", "expected_code": "DECIMAL_EXCESS_PRECISION"},
        {"vector_id": "duplicate_origin_order_key", "input_token": "same timestamp/session/rank/source_sequence/source_intent_id/slot", "expected_code": "DUPLICATE_ORIGIN_ORDER_KEY"},
    ]
    return {"vector_version": "gv_fs0_canonical_vectors_v1", "protocol_id": PROTOCOL_ID, "byte_representation": "lowercase_hex", "accepted": accepted, "rejected": rejected}


def artifact_objects() -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for filename, value in _schemas().items():
        artifacts[f"schemas/{filename}"] = value
    artifacts["registries/gv_fs0_certification_failure_registry_v1.json"] = _certification_registry()
    artifacts["registries/gv_fs0_operational_error_registry_v1.json"] = _operational_registry()
    artifacts["tables/gv_fs0_event_ranks_v1.json"] = _event_ranks()
    artifacts["tables/gv_fs0_generated_event_slots_v1.json"] = _slots()
    artifacts["tables/gv_fs0_transition_ownership_v1.json"] = _transition_ownership()
    artifacts["vectors/gv_fs0_canonical_vectors_v1.json"] = _canonical_vectors()
    if len(artifacts) != 18:
        raise AssertionError(f"expected 18 artifacts, found {len(artifacts)}")
    return dict(sorted(artifacts.items()))


def rendered_artifacts() -> dict[str, bytes]:
    return {path: canonical_document_bytes(value) for path, value in artifact_objects().items()}


def contract_literal_check() -> list[str]:
    contract = CONTRACT.read_text(encoding="utf-8")
    required = [
        PROTOCOL_ID,
        "DUPLICATE_ORIGIN_ORDER_KEY",
        "max_session_lag",
        "BOOTSTRAP",
        "ENFORCED",
        "gv_fs0_certification_failure_registry_v1",
        "gv_fs0_operational_error_registry_v1",
        "gv_fs0_event_ranks_v1",
        "gv_fs0_generated_event_slots_v1",
        "gv_fs0_transition_ownership_v1",
        "gv_fs0_canonical_vectors_v1",
    ]
    return [literal for literal in required if literal not in contract]


def check_checked_in() -> list[str]:
    failures = []
    missing_literals = contract_literal_check()
    if missing_literals:
        failures.append("contract missing literals: " + ", ".join(missing_literals))
    expected = rendered_artifacts()
    actual_paths = {
        path.relative_to(ARTIFACT_ROOT).as_posix()
        for path in ARTIFACT_ROOT.rglob("*.json")
        if path.name != "gv_fs0_freeze_manifest_v1.json"
    } if ARTIFACT_ROOT.exists() else set()
    expected_paths = set(expected)
    for extra in sorted(actual_paths - expected_paths):
        failures.append(f"extra artifact: {extra}")
    for missing in sorted(expected_paths - actual_paths):
        failures.append(f"missing artifact: {missing}")
    for relative, expected_bytes in expected.items():
        path = ARTIFACT_ROOT / relative
        if path.exists() and path.read_bytes() != expected_bytes:
            failures.append(f"artifact drift: {relative}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--render", metavar="RELATIVE_PATH")
    args = parser.parse_args(argv)
    rendered = rendered_artifacts()
    if args.list:
        for path in rendered:
            print(path)
        return 0
    if args.render:
        try:
            sys.stdout.buffer.write(rendered[args.render])
        except KeyError:
            parser.error(f"unknown artifact: {args.render}")
        return 0
    if args.check:
        failures = check_checked_in()
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print("GV-FS0 V1 artifacts: PASS")
        return 0
    parser.error("choose --check, --list, or --render")


if __name__ == "__main__":
    raise SystemExit(main())
