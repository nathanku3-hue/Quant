"""GV-FS0 V1 canonical JSON, raw-token validation, and domain hashing.

This module implements protocol primitives only. It owns no portfolio economics,
certification aggregation, publication, or UI behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import unicodedata
from typing import Any, Iterable

MAX_CANONICAL_INTEGER = 9_007_199_254_740_991
INTEGER_TOKEN_RE = re.compile(r"^(0|[1-9][0-9]*)$")
DECIMAL_TOKEN_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
CANONICAL_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented by GV-FS0 V1."""


def _validate_scalar_values(value: str) -> None:
    for codepoint in map(ord, value):
        if 0xD800 <= codepoint <= 0xDFFF:
            raise CanonicalizationError("UNICODE_SURROGATE_PROHIBITED")
        if 0xFDD0 <= codepoint <= 0xFDEF:
            raise CanonicalizationError("UNICODE_NONCHARACTER_PROHIBITED")
        if (codepoint & 0xFFFF) in {0xFFFE, 0xFFFF}:
            raise CanonicalizationError("UNICODE_NONCHARACTER_PROHIBITED")


def prepare_descriptive_string(value: str) -> str:
    if not isinstance(value, str):
        raise CanonicalizationError("STRING_REQUIRED")
    _validate_scalar_values(value)
    normalized = unicodedata.normalize("NFC", value)
    _validate_scalar_values(normalized)
    return normalized


def prepare_identity_string(value: str) -> str:
    if not isinstance(value, str):
        raise CanonicalizationError("STRING_REQUIRED")
    _validate_scalar_values(value)
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise CanonicalizationError("IDENTITY_STRING_NOT_NFC")
    _validate_scalar_values(normalized)
    return normalized


def encode_json_string(value: str) -> str:
    """Encode one already semantically prepared string exactly under V1."""
    _validate_scalar_values(value)
    pieces: list[str] = ['"']
    short_escapes = {
        0x08: "\\b",
        0x09: "\\t",
        0x0A: "\\n",
        0x0C: "\\f",
        0x0D: "\\r",
    }
    for character in value:
        codepoint = ord(character)
        if character == '"':
            pieces.append('\\"')
        elif character == "\\":
            pieces.append("\\\\")
        elif codepoint in short_escapes:
            pieces.append(short_escapes[codepoint])
        elif 0 <= codepoint <= 0x1F:
            pieces.append(f"\\u{codepoint:04x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces)


def _encode_value(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if value < 0 or value > MAX_CANONICAL_INTEGER:
            raise CanonicalizationError("INTEGER_OUT_OF_RANGE")
        return str(value)
    if isinstance(value, str):
        return encode_json_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode_value(item) for item in value) + "]"
    if isinstance(value, dict):
        prepared: list[tuple[str, Any]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("OBJECT_KEY_STRING_REQUIRED")
            prepared_key = prepare_identity_string(key)
            prepared.append((prepared_key, item))
        prepared.sort(key=lambda pair: tuple(map(ord, pair[0])))
        if len({key for key, _ in prepared}) != len(prepared):
            raise CanonicalizationError("DUPLICATE_OBJECT_KEY")
        return "{" + ",".join(
            f"{encode_json_string(key)}:{_encode_value(item)}"
            for key, item in prepared
        ) + "}"
    raise CanonicalizationError(f"UNSUPPORTED_CANONICAL_TYPE:{type(value).__name__}")


def canonical_json_text(value: Any) -> str:
    return _encode_value(value)


def canonical_document_bytes(value: Any) -> bytes:
    return canonical_json_text(value).encode("utf-8") + b"\n"


def canonical_document_hex(value: Any) -> str:
    return canonical_document_bytes(value).hex()


def domain_preimage(domain_prefix: str, value: Any) -> bytes:
    domain = prepare_identity_string(domain_prefix)
    if "\n" in domain:
        raise CanonicalizationError("DOMAIN_PREFIX_LF_PROHIBITED")
    return domain.encode("utf-8") + b"\n" + canonical_document_bytes(value)


def domain_preimage_hex(domain_prefix: str, value: Any) -> str:
    return domain_preimage(domain_prefix, value).hex()


def domain_hash(domain_prefix: str, value: Any) -> str:
    return hashlib.sha256(domain_preimage(domain_prefix, value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def terminal_newline_count(value: bytes) -> int:
    count = 0
    for byte in reversed(value):
        if byte != 0x0A:
            break
        count += 1
    return count


def _validate_raw_number_tokens(raw: str) -> None:
    """Validate number spellings before the host JSON parser converts them."""
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
                raise CanonicalizationError(f"JSON_FLOAT_PROHIBITED:{token}")
            if not INTEGER_TOKEN_RE.fullmatch(token):
                raise CanonicalizationError("INTEGER_TOKEN_INVALID")
            index = end
            continue
        index += 1


def _parse_integer_token(raw: str) -> int:
    if not INTEGER_TOKEN_RE.fullmatch(raw):
        raise CanonicalizationError("INTEGER_TOKEN_INVALID")
    value = int(raw)
    if value > MAX_CANONICAL_INTEGER:
        raise CanonicalizationError("INTEGER_OUT_OF_RANGE")
    return value


def _reject_float(raw: str) -> Any:
    raise CanonicalizationError(f"JSON_FLOAT_PROHIBITED:{raw}")


def _reject_constant(raw: str) -> Any:
    raise CanonicalizationError(f"JSON_CONSTANT_PROHIBITED:{raw}")


def _object_without_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        prepare_identity_string(key)
        if key in result:
            raise CanonicalizationError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def parse_json_text(raw: str) -> Any:
    if not isinstance(raw, str):
        raise CanonicalizationError("JSON_TEXT_REQUIRED")
    _validate_scalar_values(raw)
    _validate_raw_number_tokens(raw)
    try:
        return json.loads(
            raw,
            parse_int=_parse_integer_token,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except CanonicalizationError:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise CanonicalizationError("JSON_SYNTAX_INVALID") from exc


def parse_canonical_document_bytes(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CanonicalizationError("UTF8_BOM_PROHIBITED")
    if terminal_newline_count(raw) != 1:
        raise CanonicalizationError("TERMINAL_NEWLINE_COUNT_INVALID")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CanonicalizationError("UTF8_INVALID") from exc
    value = parse_json_text(text[:-1])
    if canonical_document_bytes(value) != raw:
        raise CanonicalizationError("DOCUMENT_NOT_CANONICAL")
    return value


def canonical_decimal(raw: str, *, quantum_places: int = 6) -> str:
    if not isinstance(raw, str) or not DECIMAL_TOKEN_RE.fullmatch(raw):
        raise CanonicalizationError("DECIMAL_TOKEN_INVALID")
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise CanonicalizationError("DECIMAL_TOKEN_INVALID") from exc
    if not value.is_finite() or value.is_signed():
        raise CanonicalizationError("DECIMAL_NONNEGATIVE_FINITE_REQUIRED")
    exponent = value.as_tuple().exponent
    if exponent < -quantum_places:
        excess = raw.rsplit(".", 1)[1][quantum_places:]
        if any(digit != "0" for digit in excess):
            raise CanonicalizationError("DECIMAL_EXCESS_PRECISION")
    if value == 0:
        return "0"
    normalized = format(value.normalize(), "f")
    return normalized.rstrip("0").rstrip(".") if "." in normalized else normalized


def canonical_timestamp(raw: str) -> str:
    if not isinstance(raw, str):
        raise CanonicalizationError("TIMESTAMP_TEXT_REQUIRED")
    if re.search(r":60(?:\.|Z|[+-])", raw):
        raise CanonicalizationError("LEAP_SECOND_PROHIBITED")
    fractional = re.search(r"\.(\d+)", raw)
    if fractional and len(fractional.group(1)) > 6:
        raise CanonicalizationError("TIMESTAMP_PRECISION_EXCEEDS_MICROSECONDS")
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CanonicalizationError("TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CanonicalizationError("TIMESTAMP_TIMEZONE_REQUIRED")
    utc_value = parsed.astimezone(timezone.utc)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def assert_sha256(value: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise CanonicalizationError("SHA256_INVALID")
    return value
