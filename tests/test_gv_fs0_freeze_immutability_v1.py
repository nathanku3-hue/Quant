from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.gv_fs0_canonical import parse_canonical_document_bytes, terminal_newline_count
from scripts.generate_gv_fs0_protocol_v1 import rendered_artifacts
from scripts.verify_gv_fs0_protocol_freeze import (
    FROZEN_PATHS,
    MANIFEST,
    check_current_tree,
    git_blob_oid,
    git_object_format,
    manifest_object,
    mutation_probe_failures,
    rendered_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_freeze_verifier_has_no_failures() -> None:
    assert check_current_tree() == []


def test_all_six_mutation_classes_are_rejected() -> None:
    assert mutation_probe_failures() == []


def test_manifest_is_exact_canonical_derivation_and_excludes_itself() -> None:
    observed = MANIFEST.read_bytes()
    assert observed == rendered_manifest()
    parsed = parse_canonical_document_bytes(observed)
    assert parsed == manifest_object()
    paths = [entry["path"] for entry in parsed["entries"]]
    assert MANIFEST.relative_to(ROOT).as_posix() not in paths
    assert paths == FROZEN_PATHS
    assert parsed["frozen_surface_count"] == 19


def test_manifest_representation_rules_are_frozen() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["git_object_format"] in {"sha1", "sha256"}
    expected_oid_length = 40 if manifest["git_object_format"] == "sha1" else 64
    for entry in manifest["entries"]:
        assert entry["terminal_newline_count"] == 1
        assert len(entry["sha256"]) == 64
        assert entry["sha256"] == entry["sha256"].lower()
        int(entry["sha256"], 16)
        assert len(entry["git_blob_oid"]) == expected_oid_length
        assert entry["git_blob_oid"] == entry["git_blob_oid"].lower()
        int(entry["git_blob_oid"], 16)


def test_manifest_hashes_and_git_blob_oids_match_exact_file_bytes() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["git_object_format"] == git_object_format()
    for entry in manifest["entries"]:
        data = (ROOT / entry["path"]).read_bytes()
        assert entry["byte_length"] == len(data)
        assert entry["sha256"] == hashlib.sha256(data).hexdigest()
        assert entry["git_blob_oid"] == git_blob_oid(data, manifest["git_object_format"])
        assert entry["terminal_newline_count"] == terminal_newline_count(data) == 1


def test_no_extra_or_missing_generated_artifact() -> None:
    expected = set(rendered_artifacts())
    observed = {
        path.relative_to(ROOT / "contracts/gv_fs0/v1").as_posix()
        for path in (ROOT / "contracts/gv_fs0/v1").rglob("*.json")
        if path != MANIFEST
    }
    assert observed == expected


def test_every_frozen_surface_is_lf_only_and_one_terminal_lf() -> None:
    for relative in FROZEN_PATHS:
        data = (ROOT / relative).read_bytes()
        assert b"\r" not in data
        assert terminal_newline_count(data) == 1


def test_gitattributes_prevents_autocrlf_from_changing_frozen_bytes() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "docs/architecture/gv_fs0_certification_and_data_authority_contract.md text eol=lf" in attributes
    assert "contracts/gv_fs0/v1/**/*.json text eol=lf" in attributes


def test_generator_is_declared_non_authoritative_and_disagreement_fails() -> None:
    contract = (ROOT / "docs/architecture/gv_fs0_certification_and_data_authority_contract.md").read_text(encoding="utf-8")
    assert "The generator is only a deterministic derivation mechanism" in contract
    assert "It is not a third protocol authority" in contract
    assert "Any disagreement among this contract, generated artifacts, canonical vectors, or generator output fails the freeze" in contract


def test_same_version_semantic_correction_requires_v2() -> None:
    contract = (ROOT / "docs/architecture/gv_fs0_certification_and_data_authority_contract.md").read_text(encoding="utf-8")
    assert "Any correction to a frozen V1 surface" in contract
    assert "requires a new protocol version and re-audit" in contract
