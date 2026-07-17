#!/usr/bin/env python3
"""Terminal validator for the GV-FS0 Protocol V1 freeze boundary."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gv_fs0.protocol.canonical import load_canonical_document
from gv_fs0.protocol.definitions import (
    CANONICAL_VECTORS_PATH,
    CONTRACT_PATH,
    expected_documents,
    assert_documents_match,
)
from gv_fs0.protocol.validation import validate_all_definitions, validate_schema_bundle


class FreezeValidationError(RuntimeError):
    pass


def _validate_contract_surface() -> None:
    contract = (ROOT / CONTRACT_PATH).read_text(encoding="utf-8")
    prohibited_markers = ("<<<<<<<", "=======", ">>>>>>>", "*** Begin Patch", "*** End Patch")
    present = [marker for marker in prohibited_markers if marker in contract]
    if present:
        raise FreezeValidationError(f"malformed patch or merge markers in contract: {present}")
    if contract.count("This document is the single normative consolidation") != 1:
        raise FreezeValidationError("contract does not contain exactly one sole-authority declaration")


def _validate_checked_in_documents() -> None:
    assert_documents_match(ROOT)
    for relative_path in expected_documents():
        document = (ROOT / relative_path).read_bytes()
        load_canonical_document(document)


def _validate_checked_in_schemas() -> None:
    bundle_path = ROOT / "schemas/gv_fs0/v1/gv_fs0_schema_bundle_v1.json"
    bundle = load_canonical_document(bundle_path.read_bytes())
    validate_schema_bundle(bundle)


def _validate_golden_vectors() -> None:
    artifact = load_canonical_document((ROOT / CANONICAL_VECTORS_PATH).read_bytes())
    for vector in artifact["vectors"]:
        document = bytes.fromhex(vector["canonical_document_hex"])
        text_bytes = bytes.fromhex(vector["canonical_json_text_utf8_hex"])
        preimage = bytes.fromhex(vector["hash_preimage_hex"])
        if document != text_bytes + b"\n":
            raise FreezeValidationError(f"golden text/document mismatch: {vector['name']}")
        load_canonical_document(document)
        expected_preimage = vector["domain"].encode("utf-8") + b"\n" + document
        if preimage != expected_preimage:
            raise FreezeValidationError(f"golden preimage mismatch: {vector['name']}")
        if len(preimage) != vector["hash_preimage_length"]:
            raise FreezeValidationError(f"golden preimage length mismatch: {vector['name']}")
        if hashlib.sha256(preimage).hexdigest() != vector["sha256"]:
            raise FreezeValidationError(f"golden digest mismatch: {vector['name']}")


def validate() -> None:
    _validate_contract_surface()
    _validate_checked_in_documents()
    _validate_checked_in_schemas()
    validate_all_definitions()
    _validate_golden_vectors()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        validate()
    except Exception as exc:
        print(f"GV_FS0_PROTOCOL_FREEZE: FAIL: {exc}", file=sys.stderr)
        return 1
    print("GV_FS0_PROTOCOL_FREEZE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
