"""Isolated standard-library-only GV-FS0 synthetic reconstruction.

Production-style invocation is exactly::

    <absolute sys.executable> -I -X utf8 <absolute script> --input <absolute file>

Protocol V1.1 verifier I/O compatibility: this engine accepts only schema-valid
``gv_fs0_verifier_input_v1`` documents (source_prices + source_intents). Legacy
``prices``/``events`` inputs are rejected. It imports no repository module and
writes no repository artifact.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any, Iterable

INPUT_SCHEMA_VERSION = "gv_fs0_verifier_input_v1"
ECONOMIC_SCHEMA_VERSION = "GV_FS0_ECONOMIC_PAYLOAD_V1"
RESULT_SCHEMA_VERSION = "GV_FS0_RECONSTRUCTION_RESULT_V1_1"
ERROR_SCHEMA_VERSION = "GV_FS0_RECONSTRUCTION_ERROR_V1"
RECONSTRUCTION_ENGINE = "GV_FS0_STDLIB_ISOLATED_V1_1"
PROTOCOL_COMPAT_VERSION = "GV_FS0_PROTOCOL_V1_1_VERIFIER_IO"

VERIFIER_INPUT_DOMAIN = "GV-FS0:VERIFIER_INPUT:V1"
ECONOMIC_PAYLOAD_DOMAIN = "GV-FS0:ECONOMIC_PAYLOAD:V1"
VERIFIER_RESULT_DOMAIN = "GV-FS0:VERIFIER_RESULT:V1"

MAX_INTEGER = 9_007_199_254_740_991
INTEGER_TOKEN = re.compile(r"^(0|[1-9][0-9]*)$")
DECIMAL_TOKEN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
EVENT_RANK = {"EXECUTION": 0, "DIVIDEND_EX": 1, "DIVIDEND_PAY": 2}
ROOT_KEYS = {"schema_version", "protocol", "decision", "source_prices", "source_intents"}
LEGACY_ROOT_KEYS = {"prices", "events"}
PROTOCOL_KEYS = {"protocol_id", "fixture_id", "fixture_hash", "currency", "initial_cash"}
DECISION_KEYS = {
    "decision_id",
    "decision_hash",
    "authority",
    "action",
    "decision_timestamp",
    "effective_timestamp",
    "security_id",
    "requested_sizing",
    "rationale_reference",
}
PRICE_KEYS = {"security_id", "session", "price_timestamp", "close_price", "source_sequence"}
INTENT_KEYS = {
    "schema_version",
    "source_intent_id",
    "source_sequence",
    "intent_type",
    "effective_timestamp",
    "session",
    "security_id",
    "quantity",
    "execution_price",
    "fee",
    "dividend_amount_per_share",
    "referenced_entitlement_source_intent_id",
    "valuation_timestamp",
}


class ReconstructionError(ValueError):
    """Deterministic fail-closed reconstruction error."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ReconstructionError("CLI_ARGUMENTS_INVALID", message)


def _validate_scalars(value: str) -> None:
    for codepoint in map(ord, value):
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ReconstructionError("UNICODE_SURROGATE_PROHIBITED")
        if 0xFDD0 <= codepoint <= 0xFDEF or (codepoint & 0xFFFF) in {0xFFFE, 0xFFFF}:
            raise ReconstructionError("UNICODE_NONCHARACTER_PROHIBITED")


def _identity(value: str) -> str:
    if not isinstance(value, str):
        raise ReconstructionError("STRING_REQUIRED")
    _validate_scalars(value)
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise ReconstructionError("IDENTITY_STRING_NOT_NFC")
    _validate_scalars(normalized)
    return normalized


def _encode_string(value: str) -> str:
    _validate_scalars(value)
    output: list[str] = ['"']
    short = {8: "\\b", 9: "\\t", 10: "\\n", 12: "\\f", 13: "\\r"}
    for character in value:
        codepoint = ord(character)
        if character == '"':
            output.append('\\"')
        elif character == "\\":
            output.append("\\\\")
        elif codepoint in short:
            output.append(short[codepoint])
        elif codepoint <= 0x1F:
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    output.append('"')
    return "".join(output)


def _encode_value(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if value < 0 or value > MAX_INTEGER:
            raise ReconstructionError("INTEGER_OUT_OF_RANGE")
        return str(value)
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, list):
        return "[" + ",".join(_encode_value(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = [(_identity(key), item) for key, item in value.items()]
        pairs.sort(key=lambda pair: tuple(map(ord, pair[0])))
        if len({key for key, _ in pairs}) != len(pairs):
            raise ReconstructionError("DUPLICATE_OBJECT_KEY")
        return "{" + ",".join(f"{_encode_string(key)}:{_encode_value(item)}" for key, item in pairs) + "}"
    raise ReconstructionError(f"UNSUPPORTED_CANONICAL_TYPE:{type(value).__name__}")


def _canonical_document_bytes(value: Any) -> bytes:
    return _encode_value(value).encode("utf-8") + b"\n"


def _domain_preimage(domain: str, value: Any) -> bytes:
    prepared = _identity(domain)
    if "\n" in prepared:
        raise ReconstructionError("DOMAIN_PREFIX_LF_PROHIBITED")
    return prepared.encode("utf-8") + b"\n" + _canonical_document_bytes(value)


def _domain_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(_domain_preimage(domain, value)).hexdigest()


def _terminal_lf_count(raw: bytes) -> int:
    count = 0
    for byte in reversed(raw):
        if byte != 0x0A:
            break
        count += 1
    return count


def _validate_number_tokens(raw: str) -> None:
    index = 0
    in_string = False
    escaped = False
    delimiters = set(" \t\r\n,]}:")
    while index < len(raw):
        character = raw[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            index += 1
            continue
        if character in "-+0123456789":
            end = index + 1
            while end < len(raw) and raw[end] not in delimiters:
                end += 1
            token = raw[index:end]
            if "." in token or "e" in token.lower():
                raise ReconstructionError("JSON_FLOAT_PROHIBITED", token)
            if not INTEGER_TOKEN.fullmatch(token):
                raise ReconstructionError("INTEGER_TOKEN_INVALID", token)
            index = end
            continue
        index += 1


def _parse_integer(raw: str) -> int:
    if not INTEGER_TOKEN.fullmatch(raw):
        raise ReconstructionError("INTEGER_TOKEN_INVALID", raw)
    value = int(raw)
    if value > MAX_INTEGER:
        raise ReconstructionError("INTEGER_OUT_OF_RANGE", raw)
    return value


def _reject_float(raw: str) -> Any:
    raise ReconstructionError("JSON_FLOAT_PROHIBITED", raw)


def _reject_constant(raw: str) -> Any:
    raise ReconstructionError("JSON_CONSTANT_PROHIBITED", raw)


def _object_without_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _identity(key)
        if key in result:
            raise ReconstructionError("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def _load_input(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_absolute():
        raise ReconstructionError("ABSOLUTE_INPUT_PATH_REQUIRED")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReconstructionError("INPUT_READ_FAILED", type(exc).__name__) from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ReconstructionError("UTF8_BOM_PROHIBITED")
    if _terminal_lf_count(raw) != 1 or b"\r" in raw:
        raise ReconstructionError("TERMINAL_NEWLINE_COUNT_INVALID")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ReconstructionError("UTF8_INVALID") from exc
    _validate_scalars(text)
    body = text[:-1]
    _validate_number_tokens(body)
    try:
        payload = json.loads(
            body,
            parse_int=_parse_integer,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ReconstructionError:
        raise
    except json.JSONDecodeError as exc:
        raise ReconstructionError("INPUT_JSON_INVALID", str(exc)) from exc
    if not isinstance(payload, dict):
        raise ReconstructionError("INPUT_ROOT_NOT_OBJECT")
    if _canonical_document_bytes(payload) != raw:
        raise ReconstructionError("INPUT_NOT_CANONICAL")
    return payload, _domain_hash(VERIFIER_INPUT_DOMAIN, payload)


def _expect_keys(value: Any, expected: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReconstructionError("SCHEMA_OBJECT_REQUIRED", context)
    actual = set(value)
    if actual != expected:
        raise ReconstructionError(
            "SCHEMA_KEYS_INVALID",
            f"{context};missing={sorted(expected - actual)};unknown={sorted(actual - expected)}",
        )
    return value


def _text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReconstructionError("TEXT_REQUIRED", context)
    _validate_scalars(value)
    return value


def _reference(value: Any, context: str) -> str:
    text = _text(value, context)
    if "/" in text or "\\" in text or re.match(r"^[A-Za-z]:", text):
        raise ReconstructionError("PATH_DEPENDENT_IDENTITY_PROHIBITED", context)
    return _identity(text)


def _decimal(value: Any, context: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_TOKEN.fullmatch(value):
        raise ReconstructionError("CANONICAL_DECIMAL_REQUIRED", context)
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ReconstructionError("DECIMAL_INVALID", context) from exc
    if not parsed.is_finite() or parsed.is_signed():
        raise ReconstructionError("DECIMAL_NONNEGATIVE_FINITE_REQUIRED", context)
    if positive and parsed <= 0:
        raise ReconstructionError("DECIMAL_MUST_BE_POSITIVE", context)
    return parsed


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _shares(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ReconstructionError("POSITIVE_WHOLE_SHARES_REQUIRED", context)
    return value


def _session(value: Any, context: str) -> date:
    raw = _text(value, context)
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ReconstructionError("SESSION_DATE_INVALID", context) from exc
    if parsed.isoformat() != raw:
        raise ReconstructionError("SESSION_DATE_INVALID", context)
    return parsed


def _timestamp(value: Any, context: str) -> datetime:
    raw = _text(value, context)
    if re.search(r":60(?:\.|Z|[+-])", raw):
        raise ReconstructionError("LEAP_SECOND_PROHIBITED", context)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ReconstructionError("TIMESTAMP_INVALID", context) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReconstructionError("TIMESTAMP_TIMEZONE_REQUIRED", context)
    return parsed.astimezone(timezone.utc)


def _nullable_text(value: Any, context: str) -> str | None:
    if value is None:
        return None
    return _text(value, context)


def _nullable_decimal(value: Any, context: str, *, positive: bool = False) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value, context, positive=positive)


def _nullable_int(value: Any, context: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReconstructionError("NONNEGATIVE_INTEGER_REQUIRED", context)
    return value


def _map_intents_to_events(
    intents: list[dict[str, Any]],
    *,
    action: str,
    security_id: str,
    price_sessions: set[date],
) -> list[dict[str, Any]]:
    """Map original source intents to independent economic events (never primary ledger)."""
    by_type: dict[str, list[dict[str, Any]]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for intent in intents:
        intent_id = intent["source_intent_id"]
        if intent_id in by_id:
            if intent != by_id[intent_id]:
                raise ReconstructionError("CONFLICTING_DUPLICATE_EVENT", intent_id)
            continue
        by_id[intent_id] = intent
        by_type.setdefault(intent["intent_type"], []).append(intent)

    if action == "NO_POSITION":
        if any(intent_type != "VALUATION_INSTRUCTION" for intent_type in by_type):
            raise ReconstructionError("NO_POSITION_NON_VALUATION_INTENT_PROHIBITED")
        if "EXECUTION_INTENT" in by_type:
            raise ReconstructionError("NO_POSITION_EVENTS_PROHIBITED")
        return []

    executions = by_type.get("EXECUTION_INTENT", [])
    fees = by_type.get("EXPLICIT_FEE", [])
    declarations = by_type.get("DIVIDEND_DECLARATION", [])
    payments = by_type.get("DIVIDEND_PAYMENT_INSTRUCTION", [])
    valuations = by_type.get("VALUATION_INSTRUCTION", [])
    if len(executions) != 1:
        raise ReconstructionError("OPEN_REQUIRES_ONE_EXECUTION")
    if len(fees) != 1:
        raise ReconstructionError("OPEN_REQUIRES_ONE_EXPLICIT_FEE")
    if len(declarations) != 1 or len(payments) != 1:
        raise ReconstructionError("OPEN_REQUIRES_ONE_DIVIDEND_EX_AND_PAY")
    if not valuations:
        raise ReconstructionError("OPEN_REQUIRES_VALUATION_INSTRUCTION")

    execution = executions[0]
    fee = fees[0]
    declaration = declarations[0]
    payment = payments[0]
    if execution["security_id"] != security_id or fee["security_id"] != security_id:
        raise ReconstructionError("EVENT_SECURITY_MISMATCH", execution["source_intent_id"])
    if declaration["security_id"] != security_id or payment["security_id"] != security_id:
        raise ReconstructionError("EVENT_SECURITY_MISMATCH", declaration["source_intent_id"])
    if execution["quantity"] is None or execution["execution_price"] is None:
        raise ReconstructionError("EXECUTION_FIELDS_REQUIRED", execution["source_intent_id"])
    if fee["fee"] is None:
        raise ReconstructionError("FEE_FIELD_REQUIRED", fee["source_intent_id"])
    if declaration["dividend_amount_per_share"] is None:
        raise ReconstructionError("DIVIDEND_AMOUNT_REQUIRED", declaration["source_intent_id"])
    if payment["referenced_entitlement_source_intent_id"] != declaration["source_intent_id"]:
        raise ReconstructionError("DIVIDEND_ENTITLEMENT_REFERENCE_MISMATCH")
    if execution["session"] != fee["session"]:
        raise ReconstructionError("FEE_SESSION_MISMATCH", fee["source_intent_id"])
    if execution["session"] not in price_sessions or declaration["session"] not in price_sessions:
        raise ReconstructionError("EVENT_SESSION_WITHOUT_PRICE", execution["source_intent_id"])
    if payment["session"] not in price_sessions:
        raise ReconstructionError("EVENT_SESSION_WITHOUT_PRICE", payment["source_intent_id"])
    if execution["session"] >= declaration["session"]:
        raise ReconstructionError("EXECUTION_NOT_BEFORE_DIVIDEND_EX")
    if declaration["session"] >= payment["session"]:
        raise ReconstructionError("DIVIDEND_PAY_NOT_AFTER_EX")

    events = [
        {
            "event_id": execution["source_intent_id"],
            "event_type": "EXECUTION",
            "session": execution["session"],
            "security_id": security_id,
            "shares": _shares(execution["quantity"], "execution.quantity"),
            "price": execution["execution_price"],
            "fee": fee["fee"],
        },
        {
            "event_id": declaration["source_intent_id"],
            "event_type": "DIVIDEND_EX",
            "session": declaration["session"],
            "security_id": security_id,
            "amount_per_share": declaration["dividend_amount_per_share"],
            "pay_session": payment["session"],
        },
        {
            "event_id": payment["source_intent_id"],
            "event_type": "DIVIDEND_PAY",
            "session": payment["session"],
            "security_id": security_id,
            "entitlement_event_id": declaration["source_intent_id"],
        },
    ]
    prior_key: tuple[date, int] | None = None
    for event in events:
        key = (event["session"], EVENT_RANK[event["event_type"]])
        if prior_key is not None and key < prior_key:
            raise ReconstructionError("EVENTS_OUT_OF_ORDER", event["event_id"])
        prior_key = key
    return events


def _validate(payload: dict[str, Any]) -> dict[str, Any]:
    if any(key in payload for key in LEGACY_ROOT_KEYS):
        raise ReconstructionError(
            "LEGACY_VERIFIER_INPUT_PROHIBITED",
            "Protocol V1.1 rejects legacy prices/events; use source_prices/source_intents",
        )
    root = _expect_keys(payload, ROOT_KEYS, "root")
    if root["schema_version"] != INPUT_SCHEMA_VERSION:
        raise ReconstructionError("INPUT_SCHEMA_VERSION_UNSUPPORTED")

    protocol = _expect_keys(root["protocol"], PROTOCOL_KEYS, "protocol")
    protocol_id = _reference(protocol["protocol_id"], "protocol.protocol_id")
    if protocol_id != "GV_FS0_PROTOCOL_V1":
        raise ReconstructionError("PROTOCOL_ID_UNSUPPORTED", protocol_id)
    fixture_id = _reference(protocol["fixture_id"], "protocol.fixture_id")
    fixture_hash = _text(protocol["fixture_hash"], "protocol.fixture_hash")
    if not re.fullmatch(r"[0-9a-f]{64}", fixture_hash):
        raise ReconstructionError("FIXTURE_HASH_INVALID", fixture_hash)
    currency = _text(protocol["currency"], "protocol.currency")
    if currency != "USD":
        raise ReconstructionError("FS0_CURRENCY_UNSUPPORTED", currency)
    initial_cash = _decimal(protocol["initial_cash"], "protocol.initial_cash", positive=True)

    decision = _expect_keys(root["decision"], DECISION_KEYS, "decision")
    authority = _text(decision["authority"], "decision.authority")
    action = _text(decision["action"], "decision.action")
    if authority != "MANUAL_OWNER_PAPER":
        raise ReconstructionError("DECISION_AUTHORITY_UNSUPPORTED", authority)
    if action not in {"OPEN", "NO_POSITION"}:
        raise ReconstructionError("DECISION_ACTION_UNSUPPORTED", action)
    decision_hash = _text(decision["decision_hash"], "decision.decision_hash")
    if not re.fullmatch(r"[0-9a-f]{64}", decision_hash):
        raise ReconstructionError("DECISION_HASH_INVALID", decision_hash)
    sizing = _expect_keys(decision["requested_sizing"], {"quantity"}, "decision.requested_sizing")
    _nullable_int(sizing["quantity"], "decision.requested_sizing.quantity")
    validated_decision = {
        "decision_id": _reference(decision["decision_id"], "decision.decision_id"),
        "decision_hash": decision_hash,
        "authority": authority,
        "action": action,
        "security_id": _reference(decision["security_id"], "decision.security_id"),
        "decision_timestamp": _timestamp(decision["decision_timestamp"], "decision.decision_timestamp"),
        "effective_timestamp": _timestamp(decision["effective_timestamp"], "decision.effective_timestamp"),
        "rationale_reference": _reference(decision["rationale_reference"], "decision.rationale_reference"),
    }

    raw_prices = root["source_prices"]
    if not isinstance(raw_prices, list) or not 5 <= len(raw_prices) <= 10:
        raise ReconstructionError("FS0_PRICE_SESSION_COUNT_INVALID")
    ordered_prices = sorted(
        enumerate(raw_prices),
        key=lambda item: (
            item[1].get("source_sequence") if isinstance(item[1], dict) else -1,
            item[0],
        ),
    )
    prices: list[dict[str, Any]] = []
    prior: date | None = None
    seen_sequences: set[int] = set()
    for index, raw_price in ordered_prices:
        row = _expect_keys(raw_price, PRICE_KEYS, f"source_prices[{index}]")
        sequence = row["source_sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ReconstructionError("SOURCE_SEQUENCE_INVALID", f"source_prices[{index}]")
        if sequence in seen_sequences:
            raise ReconstructionError("DUPLICATE_SOURCE_SEQUENCE", str(sequence))
        seen_sequences.add(sequence)
        session = _session(row["session"], f"source_prices[{index}].session")
        if prior is not None and session <= prior:
            raise ReconstructionError("PRICE_SESSIONS_NOT_STRICTLY_ORDERED", str(index))
        prior = session
        security_id = _reference(row["security_id"], f"source_prices[{index}].security_id")
        if security_id != validated_decision["security_id"]:
            raise ReconstructionError("PRICE_SECURITY_MISMATCH", str(index))
        price_timestamp = _timestamp(row["price_timestamp"], f"source_prices[{index}].price_timestamp")
        if price_timestamp.date() != session:
            raise ReconstructionError("PRICE_TIMESTAMP_SESSION_MISMATCH", str(index))
        prices.append(
            {
                "session": session,
                "session_text": session.isoformat(),
                "security_id": security_id,
                "close": _decimal(row["close_price"], f"source_prices[{index}].close_price", positive=True),
            }
        )

    price_sessions = {row["session"] for row in prices}
    raw_intents = root["source_intents"]
    if not isinstance(raw_intents, list):
        raise ReconstructionError("SOURCE_INTENTS_LIST_REQUIRED")
    intents: list[dict[str, Any]] = []
    for index, raw_intent in enumerate(raw_intents):
        row = _expect_keys(raw_intent, INTENT_KEYS, f"source_intents[{index}]")
        if row["schema_version"] != "gv_fs0_source_intent_v1":
            raise ReconstructionError("SOURCE_INTENT_SCHEMA_UNSUPPORTED", f"source_intents[{index}]")
        intent_type = _text(row["intent_type"], f"source_intents[{index}].intent_type")
        if intent_type not in {
            "EXECUTION_INTENT",
            "EXPLICIT_FEE",
            "DIVIDEND_DECLARATION",
            "DIVIDEND_PAYMENT_INSTRUCTION",
            "VALUATION_INSTRUCTION",
        }:
            raise ReconstructionError("UNSUPPORTED_INTENT_TYPE", intent_type)
        sequence = row["source_sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ReconstructionError("SOURCE_SEQUENCE_INVALID", f"source_intents[{index}]")
        session = _session(row["session"], f"source_intents[{index}].session")
        security = _reference(row["security_id"], f"source_intents[{index}].security_id")
        intents.append(
            {
                "source_intent_id": _reference(row["source_intent_id"], f"source_intents[{index}].source_intent_id"),
                "source_sequence": sequence,
                "intent_type": intent_type,
                "effective_timestamp": _timestamp(
                    row["effective_timestamp"], f"source_intents[{index}].effective_timestamp"
                ),
                "session": session,
                "security_id": security,
                "quantity": _nullable_int(row["quantity"], f"source_intents[{index}].quantity"),
                "execution_price": _nullable_decimal(
                    row["execution_price"], f"source_intents[{index}].execution_price", positive=True
                ),
                "fee": _nullable_decimal(row["fee"], f"source_intents[{index}].fee"),
                "dividend_amount_per_share": _nullable_decimal(
                    row["dividend_amount_per_share"],
                    f"source_intents[{index}].dividend_amount_per_share",
                    positive=True,
                ),
                "referenced_entitlement_source_intent_id": _nullable_text(
                    row["referenced_entitlement_source_intent_id"],
                    f"source_intents[{index}].referenced_entitlement_source_intent_id",
                ),
                "valuation_timestamp": (
                    None
                    if row["valuation_timestamp"] is None
                    else _timestamp(row["valuation_timestamp"], f"source_intents[{index}].valuation_timestamp")
                ),
            }
        )

    events = _map_intents_to_events(
        intents,
        action=action,
        security_id=validated_decision["security_id"],
        price_sessions=price_sessions,
    )

    first_session = prices[0]["session"]
    if validated_decision["decision_timestamp"].date() > first_session:
        raise ReconstructionError("DECISION_AFTER_FIRST_SESSION")
    if action == "OPEN":
        execution = next(event for event in events if event["event_type"] == "EXECUTION")
        if validated_decision["decision_timestamp"].date() >= execution["session"]:
            raise ReconstructionError("DECISION_NOT_BEFORE_EXECUTION_SESSION")

    return {
        "protocol": {
            "protocol_id": protocol_id,
            "fixture_id": fixture_id,
            "fixture_hash": fixture_hash,
            "currency": currency,
            "initial_cash": initial_cash,
        },
        "decision": validated_decision,
        "prices": prices,
        "events": events,
    }


def _reconstruct(validated: dict[str, Any]) -> dict[str, Any]:
    protocol = validated["protocol"]
    decision = validated["decision"]
    grouped: dict[date, list[dict[str, Any]]] = {}
    for event in validated["events"]:
        grouped.setdefault(event["session"], []).append(event)

    cash: Decimal = protocol["initial_cash"]
    shares = 0
    total_costs = Decimal("0")
    receivables: dict[str, dict[str, Any]] = {}
    paid: set[str] = set()
    previous_nav: Decimal = protocol["initial_cash"]
    sessions: list[dict[str, Any]] = []

    for price in validated["prices"]:
        session = price["session"]
        for event in grouped.get(session, []):
            if event["event_type"] == "EXECUTION":
                if shares != 0:
                    raise ReconstructionError("MULTIPLE_POSITION_OPENINGS_PROHIBITED")
                cash -= Decimal(event["shares"]) * event["price"] + event["fee"]
                total_costs += event["fee"]
                shares = event["shares"]
                if cash < 0:
                    raise ReconstructionError("NEGATIVE_CASH_BLOCKED")
            elif event["event_type"] == "DIVIDEND_EX":
                amount = Decimal(shares) * event["amount_per_share"]
                if amount <= 0:
                    raise ReconstructionError("DIVIDEND_ENTITLEMENT_NONPOSITIVE")
                receivables[event["event_id"]] = {"amount": amount, "pay_session": event["pay_session"]}
            else:
                entitlement_id = event["entitlement_event_id"]
                if entitlement_id in paid:
                    raise ReconstructionError("DIVIDEND_ALREADY_PAID", entitlement_id)
                entitlement = receivables.get(entitlement_id)
                if entitlement is None:
                    raise ReconstructionError("DIVIDEND_ENTITLEMENT_MISSING", entitlement_id)
                if entitlement["pay_session"] != session:
                    raise ReconstructionError("DIVIDEND_PAY_SESSION_MISMATCH", entitlement_id)
                cash += entitlement["amount"]
                paid.add(entitlement_id)
                del receivables[entitlement_id]

        receivable_total = sum((entry["amount"] for entry in receivables.values()), Decimal("0"))
        market_value = Decimal(shares) * price["close"]
        nav = cash + market_value + receivable_total
        contribution = nav - previous_nav
        previous_nav = nav
        sessions.append(
            {
                "cash": _decimal_text(cash),
                "contribution": _decimal_text(contribution),
                "market_value": _decimal_text(market_value),
                "nav": _decimal_text(nav),
                "receivables": _decimal_text(receivable_total),
                "session": price["session_text"],
                "shares": shares,
            }
        )
    if receivables:
        raise ReconstructionError("UNPAID_DIVIDEND_ENTITLEMENT")
    return {
        "action": decision["action"],
        "authority": decision["authority"],
        "currency": protocol["currency"],
        "decision_id": decision["decision_id"],
        "final_state": sessions[-1],
        "fixture_id": protocol["fixture_id"],
        "protocol_id": protocol["protocol_id"],
        "rationale_reference": decision["rationale_reference"],
        "schema_version": ECONOMIC_SCHEMA_VERSION,
        "security_id": decision["security_id"],
        "sessions": sessions,
        "total_costs": _decimal_text(total_costs),
    }


def _result(payload: dict[str, Any], input_hash: str) -> dict[str, Any]:
    economic_payload = _reconstruct(_validate(payload))
    result_without_hash = {
        "canonical_payload_hash": _domain_hash(ECONOMIC_PAYLOAD_DOMAIN, economic_payload),
        "economic_payload": economic_payload,
        "input_hash": input_hash,
        "isolation": {
            "artifact_output": "STDOUT_ONLY",
            "input_contract": "GV_FS0_VERIFIER_INPUT_V1_ONLY",
            "legacy_prices_events": "PROHIBITED",
            "primary_intermediate_artifacts": "PROHIBITED",
            "python_isolated_mode": True,
            "repository_imports": "PROHIBITED",
        },
        "protocol_compat_version": PROTOCOL_COMPAT_VERSION,
        "reconstruction_engine": RECONSTRUCTION_ENGINE,
        "schema_version": RESULT_SCHEMA_VERSION,
    }
    return {**result_without_hash, "verifier_result_hash": _domain_hash(VERIFIER_RESULT_DOMAIN, result_without_hash)}


def _error(error: ReconstructionError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "failure_reasons": [error.code],
        "schema_version": ERROR_SCHEMA_VERSION,
        "status": "BLOCKED",
    }
    if error.detail:
        payload["detail"] = error.detail
    return payload


def _args() -> argparse.Namespace:
    parser = _ArgumentParser(description="Run isolated GV-FS0 independent reconstruction.")
    parser.add_argument("--input", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    try:
        if not sys.flags.isolated or not sys.flags.utf8_mode:
            raise ReconstructionError(
                "ISOLATED_UTF8_MODE_REQUIRED",
                "invoke with sys.executable -I -X utf8 validation/gv_fs0_reconstruction.py",
            )
        args = _args()
        payload, input_hash = _load_input(args.input)
        result = _result(payload, input_hash)
    except ReconstructionError as exc:
        sys.stderr.buffer.write(_canonical_document_bytes(_error(exc)))
        return 2
    except Exception as exc:
        internal = ReconstructionError("INTERNAL_RECONSTRUCTION_ERROR", type(exc).__name__)
        sys.stderr.buffer.write(_canonical_document_bytes(_error(internal)))
        return 2
    sys.stdout.buffer.write(_canonical_document_bytes(result))
    return 0


if __name__ != "__main__":
    raise RuntimeError("GV_FS0_RECONSTRUCTION_PROCESS_ONLY")

raise SystemExit(main())
