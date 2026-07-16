"""Exact canonical JSON and scalar primitives for GV-FS0 Protocol V1.

This module deliberately does not use ``json.dumps`` for canonical output. The
V1 contract freezes escaping, Unicode, integer-token, framing, and hash rules
that are narrower than ordinary language JSON defaults.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import unicodedata
from typing import Any

MAX_CANONICAL_INTEGER = 9_007_199_254_740_991
_INTEGER_TOKEN_RE = re.compile(r"^(0|[1-9][0-9]*)$")
_DECIMAL_RE = re.compile(r"^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_TIMESTAMP_RE = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})$"
)
_SHORT_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
}


class ProtocolValueError(ValueError):
    """A stable fail-closed protocol-value error."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _validate_code_points(value: str) -> None:
    for character in value:
        code_point = ord(character)
        if 0xD800 <= code_point <= 0xDFFF:
            raise ProtocolValueError("UNICODE_SURROGATE_PROHIBITED")
        if 0xFDD0 <= code_point <= 0xFDEF:
            raise ProtocolValueError("UNICODE_NONCHARACTER_PROHIBITED")
        if code_point & 0xFFFF in {0xFFFE, 0xFFFF}:
            raise ProtocolValueError("UNICODE_NONCHARACTER_PROHIBITED")


def normalize_descriptive_string(value: str) -> str:
    """Validate raw scalars, normalize to NFC, then validate again."""

    if not isinstance(value, str):
        raise ProtocolValueError("STRING_REQUIRED")
    _validate_code_points(value)
    normalized = unicodedata.normalize("NFC", value)
    _validate_code_points(normalized)
    return normalized


def require_identity_string(value: str) -> str:
    """Require a pre-normalized NFC identity string."""

    if not isinstance(value, str):
        raise ProtocolValueError("STRING_REQUIRED")
    _validate_code_points(value)
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise ProtocolValueError("IDENTITY_STRING_NOT_NFC")
    _validate_code_points(normalized)
    return normalized


def _encode_string(value: str) -> str:
    require_identity_string(value)
    pieces = ['"']
    for character in value:
        code_point = ord(character)
        if code_point == 0x22:
            pieces.append('\\"')
        elif code_point == 0x5C:
            pieces.append("\\\\")
        elif code_point in _SHORT_ESCAPES:
            pieces.append(_SHORT_ESCAPES[code_point])
        elif code_point <= 0x1F:
            pieces.append(f"\\u{code_point:04x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces)


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, int) and not isinstance(value, bool):
        if not 0 <= value <= MAX_CANONICAL_INTEGER:
            raise ProtocolValueError("CANONICAL_INTEGER_OUT_OF_RANGE")
        return str(value)
    if isinstance(value, float) or isinstance(value, Decimal):
        raise ProtocolValueError("JSON_NUMBER_TYPE_PROHIBITED")
    if isinstance(value, Mapping):
        encoded_items: list[tuple[str, str]] = []
        seen: set[str] = set()
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProtocolValueError("OBJECT_KEY_STRING_REQUIRED")
            require_identity_string(key)
            if key in seen:
                raise ProtocolValueError("DUPLICATE_JSON_KEY", key)
            seen.add(key)
            encoded_items.append((key, f"{_encode_string(key)}:{_encode(item)}"))
        encoded_items.sort(key=lambda pair: tuple(ord(ch) for ch in pair[0]))
        return "{" + ",".join(item for _, item in encoded_items) + "}"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "[" + ",".join(_encode(item) for item in value) + "]"
    raise ProtocolValueError("CANONICAL_JSON_TYPE_UNSUPPORTED", type(value).__name__)


def canonical_json_text(value: Any) -> str:
    """Return canonical JSON text without the document terminal LF."""

    return _encode(value)


def canonical_document_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON with exactly one terminal LF."""

    return canonical_json_text(value).encode("utf-8") + b"\n"


def _parse_integer_token(raw: str) -> int:
    if not _INTEGER_TOKEN_RE.fullmatch(raw):
        raise ProtocolValueError("CANONICAL_INTEGER_TOKEN_INVALID", raw)
    parsed = int(raw)
    if parsed > MAX_CANONICAL_INTEGER:
        raise ProtocolValueError("CANONICAL_INTEGER_OUT_OF_RANGE", raw)
    return parsed


def _reject_float_token(raw: str) -> Any:
    raise ProtocolValueError("JSON_FLOAT_PROHIBITED", raw)


def _reject_constant(raw: str) -> Any:
    raise ProtocolValueError("JSON_NONFINITE_PROHIBITED", raw)


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require_identity_string(key)
        if key in result:
            raise ProtocolValueError("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def _validate_loaded_strings(value: Any) -> None:
    if isinstance(value, str):
        require_identity_string(value)
        return
    if isinstance(value, list):
        for item in value:
            _validate_loaded_strings(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            require_identity_string(key)
            _validate_loaded_strings(item)


def load_canonical_document(document: bytes) -> Any:
    """Parse and prove an exact canonical JSON document.

    Raw integer spellings and duplicate keys are checked before conversion.
    Canonical equality is then established by re-encoding the parsed value.
    """

    if not isinstance(document, bytes):
        raise ProtocolValueError("DOCUMENT_BYTES_REQUIRED")
    if document.startswith(b"\xef\xbb\xbf"):
        raise ProtocolValueError("UTF8_BOM_PROHIBITED")
    if not document.endswith(b"\n") or document.endswith(b"\n\n"):
        raise ProtocolValueError("TERMINAL_LF_INVALID")
    try:
        text = document[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ProtocolValueError("UTF8_INVALID", str(exc)) from exc
    try:
        value = json.loads(
            text,
            parse_int=_parse_integer_token,
            parse_float=_reject_float_token,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_without_duplicates,
        )
    except ProtocolValueError:
        raise
    except json.JSONDecodeError as exc:
        raise ProtocolValueError("JSON_INVALID", str(exc)) from exc
    _validate_loaded_strings(value)
    if canonical_document_bytes(value) != document:
        raise ProtocolValueError("DOCUMENT_NOT_CANONICAL")
    return value


def canonical_decimal(raw: str, *, allow_negative: bool = True, quantum_places: int = 6) -> str:
    """Canonicalize an exact plain-base-10 decimal string without rounding."""

    if not isinstance(raw, str):
        raise ProtocolValueError("DECIMAL_STRING_REQUIRED")
    match = _DECIMAL_RE.fullmatch(raw)
    if match is None:
        raise ProtocolValueError("DECIMAL_TOKEN_INVALID", raw)
    sign, whole, fraction = match.groups()
    fraction = fraction or ""
    if sign and not allow_negative:
        raise ProtocolValueError("NEGATIVE_DECIMAL_PROHIBITED", raw)
    if sign and set(fraction or "0") == {"0"} and whole == "0":
        raise ProtocolValueError("NEGATIVE_ZERO_PROHIBITED", raw)
    significant_fraction = fraction.rstrip("0")
    if len(significant_fraction) > quantum_places:
        raise ProtocolValueError("DECIMAL_EXCESS_PRECISION", raw)
    try:
        parsed = Decimal(raw)
    except InvalidOperation as exc:
        raise ProtocolValueError("DECIMAL_TOKEN_INVALID", raw) from exc
    if not parsed.is_finite():
        raise ProtocolValueError("DECIMAL_NONFINITE", raw)
    if parsed == 0:
        return "0"
    suffix = f".{significant_fraction}" if significant_fraction else ""
    return f"{sign}{whole}{suffix}"


def canonical_date(raw: str) -> str:
    """Validate an exact Gregorian session date."""

    if not isinstance(raw, str) or _DATE_RE.fullmatch(raw) is None:
        raise ProtocolValueError("DATE_TOKEN_INVALID")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ProtocolValueError("DATE_TOKEN_INVALID", raw) from exc
    if parsed.isoformat() != raw:
        raise ProtocolValueError("DATE_TOKEN_INVALID", raw)
    return raw


def canonical_timestamp(raw: str) -> str:
    """Normalize an aware timestamp losslessly to six-digit UTC form."""

    if not isinstance(raw, str):
        raise ProtocolValueError("TIMESTAMP_STRING_REQUIRED")
    match = _TIMESTAMP_RE.fullmatch(raw)
    if match is None:
        raise ProtocolValueError("TIMESTAMP_TOKEN_INVALID", raw)
    second = int(match.group("second"))
    if second > 59:
        raise ProtocolValueError("LEAP_SECOND_PROHIBITED", raw)
    fraction = match.group("fraction") or ""
    if len(fraction) > 6:
        raise ProtocolValueError("TIMESTAMP_PRECISION_EXCEEDED", raw)
    zone = match.group("zone")
    normalized = raw[:-1] + "+00:00" if zone == "Z" else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ProtocolValueError("TIMESTAMP_TOKEN_INVALID", raw) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProtocolValueError("TIMESTAMP_TIMEZONE_REQUIRED", raw)
    utc_value = parsed.astimezone(timezone.utc)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def domain_preimage(domain_prefix: str, value: Any) -> bytes:
    """Build the exact V1 domain-separated hash preimage."""

    require_identity_string(domain_prefix)
    if "\n" in domain_prefix:
        raise ProtocolValueError("HASH_DOMAIN_LF_PROHIBITED")
    return domain_prefix.encode("utf-8") + b"\n" + canonical_document_bytes(value)


def domain_hash(domain_prefix: str, value: Any) -> str:
    """Return lowercase SHA-256 over the exact V1 preimage."""

    return hashlib.sha256(domain_preimage(domain_prefix, value)).hexdigest()
