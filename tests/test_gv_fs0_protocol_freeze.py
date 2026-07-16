from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest

from gv_fs0.protocol.canonical import canonical_document_bytes, load_canonical_document
from gv_fs0.protocol.definitions import (
    CONTRACT_PATH,
    FREEZE_MANIFEST_PATH,
    PHASE_BRIEF_PATH,
    SCHEMA_BUNDLE_PATH,
    assert_authority_files,
    assert_documents_match,
    assert_sole_normative_protocol_source,
    build_schemas,
    expected_documents,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_script(relative_path: str, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reviewed_authority_files_are_byte_exact_and_sole() -> None:
    assert_authority_files(ROOT)
    assert_sole_normative_protocol_source(ROOT)
    contract = (ROOT / CONTRACT_PATH).read_text(encoding="utf-8")
    brief = (ROOT / PHASE_BRIEF_PATH).read_text(encoding="utf-8")
    assert contract.count("This document is the single normative consolidation") == 1
    assert "Do not begin economic reduction" in contract
    assert "REDUCER_BLOCKED" in brief
    for marker in ("<<<<<<<", "=======", ">>>>>>>", "*** Begin Patch", "*** End Patch"):
        assert marker not in contract


def test_every_checked_in_machine_artifact_matches_the_definition_surface() -> None:
    assert_documents_match(ROOT)
    for relative_path, expected in expected_documents().items():
        actual = (ROOT / relative_path).read_bytes()
        assert actual == expected
        assert load_canonical_document(actual) is not None


def test_freeze_manifest_records_exact_repository_hashes() -> None:
    manifest = load_canonical_document((ROOT / FREEZE_MANIFEST_PATH).read_bytes())
    for entry in manifest["authority_transfer"]:
        data = (ROOT / entry["path"]).read_bytes()
        assert len(data) == entry["size_bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    for entry in manifest["frozen_files"]:
        data = (ROOT / entry["path"]).read_bytes()
        assert len(data) == entry["size_bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    schemas = build_schemas()
    assert {entry["name"] for entry in manifest["schema_hashes"]} == set(schemas)
    for entry in manifest["schema_hashes"]:
        data = canonical_document_bytes(schemas[entry["name"]])
        assert len(data) == entry["size_bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]


def test_schema_bundle_is_manifested_as_one_repository_file_and_each_schema_separately() -> None:
    manifest = load_canonical_document((ROOT / FREEZE_MANIFEST_PATH).read_bytes())
    file_paths = {entry["path"] for entry in manifest["frozen_files"]}
    assert SCHEMA_BUNDLE_PATH in file_paths
    assert len(manifest["schema_hashes"]) == 12


def test_terminal_protocol_freeze_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "validation" / "gv_fs0_protocol_freeze.py")],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "GV_FS0_PROTOCOL_FREEZE: PASS"


def test_immutability_validator_allows_first_freeze_when_base_has_no_manifest() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "validation" / "gv_fs0_v1_immutability.py"),
            "--base-ref",
            "6a8bb6c9410bc91940d53ca727b561aa86776ec7",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "GV_FS0_V1_IMMUTABILITY: PASS"


def test_immutability_validator_rejects_same_version_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script("validation/gv_fs0_v1_immutability.py", "gv_fs0_v1_immutability_test")
    monkeypatch.setattr(module, "assert_documents_match", lambda root: None)
    monkeypatch.setattr(module, "_base_contains_manifest", lambda base_ref: True)
    monkeypatch.setattr(module, "_changed_paths", lambda base_ref: {CONTRACT_PATH, "unrelated.txt"})
    with pytest.raises(RuntimeError, match="already frozen"):
        module.validate("origin/main")


def test_frozen_path_set_covers_all_protocol_implementation_surfaces() -> None:
    module = _load_script("validation/gv_fs0_v1_immutability.py", "gv_fs0_v1_immutability_paths")
    expected = {
        CONTRACT_PATH,
        PHASE_BRIEF_PATH,
        *expected_documents().keys(),
        "gv_fs0/protocol/canonical.py",
        "gv_fs0/protocol/definitions.py",
        "gv_fs0/protocol/ordering.py",
        "gv_fs0/protocol/publication.py",
        "gv_fs0/protocol/supervision.py",
        "gv_fs0/protocol/validation.py",
        "validation/gv_fs0_canonical_reference.py",
        "validation/gv_fs0_protocol_freeze.py",
        "validation/gv_fs0_v1_immutability.py",
    }
    assert expected.issubset(module.FROZEN_V1_PATHS)
