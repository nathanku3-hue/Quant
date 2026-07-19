from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

from core.gv_fs0_canonical import (
    CanonicalizationError,
    canonical_decimal,
    canonical_document_bytes,
    canonical_timestamp,
    domain_hash,
    domain_preimage,
    encode_json_string,
    parse_canonical_document_bytes,
    parse_json_text,
    prepare_descriptive_string,
    prepare_identity_string,
    terminal_newline_count,
)
ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = ROOT / "validation"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))
import gv_fs0_ci_reference_encoder as reference  # noqa: E402

VECTORS = ROOT / "contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json"


def test_primary_and_independent_encoders_match_every_accepted_vector() -> None:
    vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert vectors["byte_representation"] == "lowercase_hex"
    for vector in vectors["accepted"]:
        value = vector["semantic_value"]
        domain = vector["domain_prefix"]
        primary_document = canonical_document_bytes(value)
        independent_document = reference.canonical_document_bytes(value)
        primary_preimage = domain_preimage(domain, value)
        independent_preimage = reference.domain_preimage(domain, value)
        assert primary_document == independent_document
        assert primary_preimage == independent_preimage
        assert primary_document.hex() == vector["canonical_document_hex"]
        assert primary_preimage.hex() == vector["domain_preimage_hex"]
        assert len(primary_preimage) == vector["preimage_byte_length"]
        assert hashlib.sha256(primary_preimage).hexdigest() == vector["sha256"]
        assert domain_hash(domain, value) == vector["sha256"]


def test_exact_string_escaping_and_direct_unicode() -> None:
    value = 'quote=" slash=/ backslash=\\ controls=\b\t\n\f\r\x00\x0b\x1f'
    assert encode_json_string(value) == (
        '"quote=\\" slash=/ backslash=\\\\ controls='
        "\\b\\t\\n\\f\\r\\u0000\\u000b\\u001f\""
    )
    unicode_value = "CJK=漢字 separators=\u2028\u2029 emoji=😀"
    encoded = encode_json_string(unicode_value)
    assert "漢字" in encoded
    assert "\u2028" in encoded
    assert "\u2029" in encoded
    assert "😀" in encoded
    assert "\\u2028" not in encoded
    assert "\\ud83d" not in encoded.lower()


def test_string_preparation_rules() -> None:
    assert prepare_descriptive_string("e\u0301") == "é"
    with pytest.raises(CanonicalizationError, match="IDENTITY_STRING_NOT_NFC"):
        prepare_identity_string("e\u0301")
    for value in ["\ud800", "\ufdd0", "\U0001ffff"]:
        with pytest.raises(CanonicalizationError):
            prepare_descriptive_string(value)


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("-1", "INTEGER_TOKEN_INVALID"),
        ("+1", "INTEGER_TOKEN_INVALID"),
        ("01", "INTEGER_TOKEN_INVALID"),
        ("1.0", "JSON_FLOAT_PROHIBITED"),
        ("1e0", "JSON_FLOAT_PROHIBITED"),
        ('{"value":01}', "INTEGER_TOKEN_INVALID"),
        ('{"value":1e-3}', "JSON_FLOAT_PROHIBITED"),
    ],
)
def test_raw_number_tokens_reject_before_conversion(raw: str, code: str) -> None:
    with pytest.raises(CanonicalizationError, match=code):
        parse_json_text(raw)
    with pytest.raises(reference.ReferenceEncodingError, match=code):
        reference.parse_json_text(raw)


def test_integer_boundaries_and_duplicate_keys() -> None:
    assert parse_json_text("9007199254740991") == 9_007_199_254_740_991
    with pytest.raises(CanonicalizationError, match="INTEGER_OUT_OF_RANGE"):
        parse_json_text("9007199254740992")
    with pytest.raises(CanonicalizationError, match="DUPLICATE_JSON_KEY"):
        parse_json_text('{"a":0,"a":1}')


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.230000", "1.23"),
        ("1.2300000", "1.23"),
        ("0.000000", "0"),
        ("1000", "1000"),
    ],
)
def test_decimal_canonicalization(raw: str, expected: str) -> None:
    assert canonical_decimal(raw) == expected


def test_decimal_excess_precision_rejects_without_rounding() -> None:
    with pytest.raises(CanonicalizationError, match="DECIMAL_EXCESS_PRECISION"):
        canonical_decimal("1.2300001")
    with pytest.raises(CanonicalizationError, match="DECIMAL_TOKEN_INVALID"):
        canonical_decimal("-0")


def test_timestamp_normalization_and_rejections() -> None:
    assert canonical_timestamp("2026-07-17T08:30:00.000000+08:00") == "2026-07-17T00:30:00.000000Z"
    assert canonical_timestamp("2026-07-17T00:30:00Z") == "2026-07-17T00:30:00.000000Z"
    with pytest.raises(CanonicalizationError, match="TIMESTAMP_TIMEZONE_REQUIRED"):
        canonical_timestamp("2026-07-17T00:30:00")
    with pytest.raises(CanonicalizationError, match="TIMESTAMP_PRECISION_EXCEEDS_MICROSECONDS"):
        canonical_timestamp("2026-07-17T00:30:00.0000001Z")
    with pytest.raises(CanonicalizationError, match="LEAP_SECOND_PROHIBITED"):
        canonical_timestamp("2026-07-17T00:30:60.000000Z")


def test_canonical_document_framing_and_validation() -> None:
    canonical = b'{"a":0,"z":"ok"}\n'
    assert canonical_document_bytes({"z": "ok", "a": 0}) == canonical
    assert terminal_newline_count(canonical) == 1
    assert parse_canonical_document_bytes(canonical) == {"a": 0, "z": "ok"}
    for invalid in [
        b'\xef\xbb\xbf{"a":0}\n',
        b'{"a":0}\r\n',
        b'{"a":0}\n\n',
        b'{ "a":0}\n',
        b'{"z":0,"a":0}\n',
    ]:
        with pytest.raises(CanonicalizationError):
            parse_canonical_document_bytes(invalid)


def test_domain_framing_has_exactly_two_lf_boundaries() -> None:
    value = {"a": 0}
    preimage = domain_preimage("GV-FS0:FIXTURE:V1", value)
    assert preimage == b"GV-FS0:FIXTURE:V1\n{\"a\":0}\n"
    assert preimage.count(b"\n") == 2
    with pytest.raises(CanonicalizationError, match="DOMAIN_PREFIX_LF_PROHIBITED"):
        domain_preimage("bad\ndomain", value)
