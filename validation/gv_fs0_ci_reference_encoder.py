"""Independent stdlib-only GV-FS0 V1 canonical-vector verifier.

This module intentionally does not import ``core.gv_fs0_canonical``. CI uses it
as an independent implementation when proving canonical byte and hash parity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any, Iterable

MAX_INTEGER = 9_007_199_254_740_991
INTEGER_TOKEN = re.compile(r"^(0|[1-9][0-9]*)$")


class ReferenceEncodingError(ValueError):
    """Raised when input is outside the frozen V1 canonical domain."""


def _validate_scalars(value: str) -> None:
    for codepoint in map(ord, value):
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ReferenceEncodingError("UNICODE_SURROGATE_PROHIBITED")
        if 0xFDD0 <= codepoint <= 0xFDEF or (codepoint & 0xFFFF) in {0xFFFE, 0xFFFF}:
            raise ReferenceEncodingError("UNICODE_NONCHARACTER_PROHIBITED")


def _identity(value: str) -> str:
    if not isinstance(value, str):
        raise ReferenceEncodingError("STRING_REQUIRED")
    _validate_scalars(value)
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise ReferenceEncodingError("IDENTITY_STRING_NOT_NFC")
    _validate_scalars(normalized)
    return normalized


def _string(value: str) -> str:
    _validate_scalars(value)
    escaped: list[str] = ['"']
    short = {8: "\\b", 9: "\\t", 10: "\\n", 12: "\\f", 13: "\\r"}
    for character in value:
        codepoint = ord(character)
        if character == '"':
            escaped.append('\\"')
        elif character == "\\":
            escaped.append("\\\\")
        elif codepoint in short:
            escaped.append(short[codepoint])
        elif codepoint <= 0x1F:
            escaped.append(f"\\u{codepoint:04x}")
        else:
            escaped.append(character)
    escaped.append('"')
    return "".join(escaped)


def _value(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if value < 0 or value > MAX_INTEGER:
            raise ReferenceEncodingError("INTEGER_OUT_OF_RANGE")
        return str(value)
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list):
        return "[" + ",".join(_value(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = [(_identity(key), item) for key, item in value.items()]
        pairs.sort(key=lambda pair: tuple(map(ord, pair[0])))
        if len({key for key, _ in pairs}) != len(pairs):
            raise ReferenceEncodingError("DUPLICATE_OBJECT_KEY")
        return "{" + ",".join(f"{_string(key)}:{_value(item)}" for key, item in pairs) + "}"
    raise ReferenceEncodingError(f"UNSUPPORTED_CANONICAL_TYPE:{type(value).__name__}")


def canonical_document_bytes(value: Any) -> bytes:
    return _value(value).encode("utf-8") + b"\n"


def domain_preimage(domain_prefix: str, value: Any) -> bytes:
    domain = _identity(domain_prefix)
    if "\n" in domain:
        raise ReferenceEncodingError("DOMAIN_PREFIX_LF_PROHIBITED")
    return domain.encode("utf-8") + b"\n" + canonical_document_bytes(value)


def domain_hash(domain_prefix: str, value: Any) -> str:
    return hashlib.sha256(domain_preimage(domain_prefix, value)).hexdigest()


def _validate_raw_number_tokens(raw: str) -> None:
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
                raise ReferenceEncodingError(f"JSON_FLOAT_PROHIBITED:{token}")
            if not INTEGER_TOKEN.fullmatch(token):
                raise ReferenceEncodingError("INTEGER_TOKEN_INVALID")
            index = end
            continue
        index += 1


def _integer(raw: str) -> int:
    if not INTEGER_TOKEN.fullmatch(raw):
        raise ReferenceEncodingError("INTEGER_TOKEN_INVALID")
    value = int(raw)
    if value > MAX_INTEGER:
        raise ReferenceEncodingError("INTEGER_OUT_OF_RANGE")
    return value


def _float(raw: str) -> Any:
    raise ReferenceEncodingError(f"JSON_FLOAT_PROHIBITED:{raw}")


def _constant(raw: str) -> Any:
    raise ReferenceEncodingError(f"JSON_CONSTANT_PROHIBITED:{raw}")


def _object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _identity(key)
        if key in result:
            raise ReferenceEncodingError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def parse_json_text(raw: str) -> Any:
    _validate_scalars(raw)
    _validate_raw_number_tokens(raw)
    try:
        return json.loads(
            raw,
            parse_int=_integer,
            parse_float=_float,
            parse_constant=_constant,
            object_pairs_hook=_object,
        )
    except ReferenceEncodingError:
        raise
    except json.JSONDecodeError as exc:
        raise ReferenceEncodingError("JSON_SYNTAX_INVALID") from exc


def verify_vectors(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        vectors = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"vector file unreadable: {type(exc).__name__}"]

    if vectors.get("byte_representation") != "lowercase_hex":
        failures.append("byte_representation must be lowercase_hex")

    for vector in vectors.get("accepted", []):
        vector_id = vector.get("vector_id", "<missing>")
        value = vector.get("semantic_value")
        domain = vector.get("domain_prefix")
        document = canonical_document_bytes(value)
        preimage = domain_preimage(domain, value)
        checks = {
            "canonical_document_hex": document.hex(),
            "domain_preimage_hex": preimage.hex(),
            "preimage_byte_length": len(preimage),
            "sha256": hashlib.sha256(preimage).hexdigest(),
        }
        for field, observed in checks.items():
            if vector.get(field) != observed:
                failures.append(f"{vector_id}:{field}:mismatch")

    rejection_map = {
        "integer_negative": "-1",
        "integer_plus": "+1",
        "integer_leading_zero": "01",
        "integer_decimal": "1.0",
        "integer_exponent": "1e0",
    }
    for vector in vectors.get("rejected", []):
        vector_id = vector.get("vector_id")
        raw = rejection_map.get(vector_id)
        if raw is None:
            continue
        try:
            parse_json_text(raw)
        except ReferenceEncodingError as exc:
            expected = vector.get("expected_code")
            if not str(exc).startswith(expected):
                failures.append(f"{vector_id}:expected={expected}:observed={exc}")
        else:
            failures.append(f"{vector_id}:accepted unexpectedly")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vectors",
        type=Path,
        default=Path("contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json"),
    )
    args = parser.parse_args(argv)
    failures = verify_vectors(args.vectors)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("GV-FS0 CI reference vectors: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
