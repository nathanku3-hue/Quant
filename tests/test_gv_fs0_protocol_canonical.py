from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from gv_fs0.protocol.canonical import (
    MAX_CANONICAL_INTEGER,
    ProtocolValueError,
    canonical_date,
    canonical_decimal,
    canonical_document_bytes,
    canonical_timestamp,
    domain_hash,
    domain_preimage,
    load_canonical_document,
    normalize_descriptive_string,
    require_identity_string,
)
from gv_fs0.protocol.definitions import CANONICAL_VECTORS_PATH

ROOT = Path(__file__).resolve().parents[1]


def test_exact_string_escaping_and_document_framing() -> None:
    value = {
        "z": [0, MAX_CANONICAL_INTEGER],
        "a": 'quote" slash/ backslash\\ line\u2028paragraph\u2029 CJK漢字 emoji😀',
        "b": "\b\t\n\f\r\x00\x0b\x1f",
    }
    expected = (
        '{"a":"quote\\\" slash/ backslash\\\\ line\u2028paragraph\u2029 CJK漢字 emoji😀",'
        '"b":"\\b\\t\\n\\f\\r\\u0000\\u000b\\u001f",'
        '"z":[0,9007199254740991]}\n'
    ).encode("utf-8")
    document = canonical_document_bytes(value)
    assert document == expected
    assert document.endswith(b"\n")
    assert not document.endswith(b"\n\n")
    assert b"\\/" not in document
    assert "😀".encode("utf-8") in document
    assert b"\\ud83d" not in document


def test_unicode_validation_precedes_normalization() -> None:
    assert normalize_descriptive_string("e\u0301") == "é"
    assert require_identity_string("é") == "é"
    with pytest.raises(ProtocolValueError, match="IDENTITY_STRING_NOT_NFC"):
        require_identity_string("e\u0301")
    for prohibited in ("\ud800", "\ufdd0", "\ufffe", "\U0010ffff"):
        with pytest.raises(ProtocolValueError):
            normalize_descriptive_string(prohibited)


def test_raw_integer_tokens_are_proven_before_conversion() -> None:
    assert load_canonical_document(b'{"n":0}\n') == {"n": 0}
    assert load_canonical_document(b'{"n":9007199254740991}\n') == {"n": MAX_CANONICAL_INTEGER}
    invalid_documents = (
        b'{"n":-0}\n',
        b'{"n":-1}\n',
        b'{"n":+1}\n',
        b'{"n":00}\n',
        b'{"n":01}\n',
        b'{"n":1.0}\n',
        b'{"n":1e0}\n',
        b'{"n":9007199254740992}\n',
    )
    for document in invalid_documents:
        with pytest.raises(ProtocolValueError):
            load_canonical_document(document)


def test_duplicate_keys_bom_and_noncanonical_whitespace_block() -> None:
    for document in (
        b'{"a":1,"a":1}\n',
        b'\xef\xbb\xbf{"a":1}\n',
        b'{ "a":1}\n',
        b'{"a":1}',
        b'{"a":1}\n\n',
    ):
        with pytest.raises(ProtocolValueError):
            load_canonical_document(document)


def test_decimal_date_and_timestamp_rules() -> None:
    assert canonical_decimal("1.230000") == "1.23"
    assert canonical_decimal("1.2300000") == "1.23"
    assert canonical_decimal("0.000000") == "0"
    assert canonical_decimal("-12.340000") == "-12.34"
    for invalid in ("-0", "-0.000000", "+1", "01", "1e0", "1.2300001", "0.0000004"):
        with pytest.raises(ProtocolValueError):
            canonical_decimal(invalid)
    assert canonical_date("2026-07-17") == "2026-07-17"
    with pytest.raises(ProtocolValueError):
        canonical_date("2026-02-30")
    assert canonical_timestamp("2026-07-17T01:30:00+08:00") == "2026-07-16T17:30:00.000000Z"
    assert canonical_timestamp("2026-07-16T17:30:00.1Z") == "2026-07-16T17:30:00.100000Z"
    for invalid in (
        "2026-07-16T17:30:00",
        "2026-07-16T17:30:60Z",
        "2026-07-16T17:30:00.1234567Z",
    ):
        with pytest.raises(ProtocolValueError):
            canonical_timestamp(invalid)


def test_domain_hash_framing_is_exact() -> None:
    value = {"a": 1}
    preimage = domain_preimage("GV-FS0:FIXTURE:V1", value)
    assert preimage == b'GV-FS0:FIXTURE:V1\n{"a":1}\n'
    assert len(preimage) == 26
    assert domain_hash("GV-FS0:FIXTURE:V1", value) == "c1e7c6e22429a93ade7b0f768e3166b649a865846b2ea5cbc0604e7aa5d8fdfb"


def test_checked_in_golden_vectors_assert_all_five_proofs() -> None:
    artifact = load_canonical_document((ROOT / CANONICAL_VECTORS_PATH).read_bytes())
    for vector in artifact["vectors"]:
        text = bytes.fromhex(vector["canonical_json_text_utf8_hex"])
        document = bytes.fromhex(vector["canonical_document_hex"])
        preimage = bytes.fromhex(vector["hash_preimage_hex"])
        value = load_canonical_document(document)
        assert document == text + b"\n"
        assert preimage == vector["domain"].encode("utf-8") + b"\n" + document
        assert preimage == domain_preimage(vector["domain"], value)
        assert len(preimage) == vector["hash_preimage_length"]
        assert domain_hash(vector["domain"], value) == vector["sha256"]


def test_independent_reference_encoder_matches_primary(tmp_path: Path) -> None:
    value = {
        "z": [2, 1, 0],
        "a": "slash/ line\u2028paragraph\u2029 漢字 😀",
        "controls": "\b\t\n\f\r\x00\x0b\x1f",
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    script = ROOT / "validation" / "gv_fs0_canonical_reference.py"
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(script), "--input", str(input_path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stderr == b""
    assert result.stdout == canonical_document_bytes(value)
