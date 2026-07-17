#!/usr/bin/env python3
"""Independent standard-library reference encoder for GV-FS0 Protocol V1 tests.

This file intentionally imports no ``gv_fs0`` module. It is a CI/verifier-side
cross-check, not a production reducer, certification executor, or artifact
publisher.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any

MAX_INTEGER = 9_007_199_254_740_991
INTEGER_RE = re.compile(r"^(0|[1-9][0-9]*)$")
SHORT_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
}


def _validate_string(value: str) -> str:
    for character in value:
        code_point = ord(character)
        if 0xD800 <= code_point <= 0xDFFF:
            raise ValueError("surrogate prohibited")
        if 0xFDD0 <= code_point <= 0xFDEF or (code_point & 0xFFFF) in {0xFFFE, 0xFFFF}:
            raise ValueError("noncharacter prohibited")
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise ValueError("identity string must already be NFC")
    return value


def _string(value: str) -> str:
    _validate_string(value)
    output = ['"']
    for character in value:
        code_point = ord(character)
        if code_point == 0x22:
            output.append('\\"')
        elif code_point == 0x5C:
            output.append("\\\\")
        elif code_point in SHORT_ESCAPES:
            output.append(SHORT_ESCAPES[code_point])
        elif code_point <= 0x1F:
            output.append(f"\\u{code_point:04x}")
        else:
            output.append(character)
    output.append('"')
    return "".join(output)


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, int) and not isinstance(value, bool):
        if not 0 <= value <= MAX_INTEGER:
            raise ValueError("integer out of range")
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(_encode(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value, key=lambda key: tuple(ord(character) for character in key))
        return "{" + ",".join(f"{_string(key)}:{_encode(value[key])}" for key in keys) + "}"
    raise ValueError(f"unsupported JSON type: {type(value).__name__}")


def _integer(raw: str) -> int:
    if INTEGER_RE.fullmatch(raw) is None:
        raise ValueError("invalid integer token")
    value = int(raw)
    if value > MAX_INTEGER:
        raise ValueError("integer out of range")
    return value


def _float(raw: str) -> Any:
    raise ValueError(f"float token prohibited: {raw}")


def _constant(raw: str) -> Any:
    raise ValueError(f"non-finite token prohibited: {raw}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _validate_string(key)
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        text = args.input.read_text(encoding="utf-8")
        value = json.loads(
            text,
            parse_int=_integer,
            parse_float=_float,
            parse_constant=_constant,
            object_pairs_hook=_object,
        )
        document = _encode(value).encode("utf-8") + b"\n"
    except Exception as exc:
        print(f"GV_FS0_CANONICAL_REFERENCE: FAIL: {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(document)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
