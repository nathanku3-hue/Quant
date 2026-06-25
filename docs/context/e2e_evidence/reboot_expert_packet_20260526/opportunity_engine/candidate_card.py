from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from opportunity_engine.candidate_card_schema import (
    CandidateCardValidationResult,
    assert_valid_candidate_card,
    validate_candidate_card,
)


def load_candidate_card(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def load_candidate_manifest(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def validate_candidate_card_bundle(
    card_path: str | Path,
    manifest_path: str | Path,
) -> CandidateCardValidationResult:
    card = load_candidate_card(card_path)
    manifest = load_candidate_manifest(manifest_path)
    result = validate_candidate_card(card, manifest=manifest)
    hash_error = _validate_manifest_hash(Path(card_path), manifest)
    if hash_error is None:
        return result
    return CandidateCardValidationResult(
        valid=False,
        errors=(*result.errors, hash_error),
    )


def assert_valid_candidate_card_bundle(card_path: str | Path, manifest_path: str | Path) -> None:
    result = validate_candidate_card_bundle(card_path, manifest_path)
    if not result.valid:
        from opportunity_engine.candidate_card_schema import CandidateCardValidationError

        raise CandidateCardValidationError("; ".join(result.errors))

    card = load_candidate_card(card_path)
    manifest = load_candidate_manifest(manifest_path)
    assert_valid_candidate_card(card, manifest=manifest)


def artifact_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _validate_manifest_hash(card_path: Path, manifest: Mapping[str, Any]) -> str | None:
    expected = manifest.get("artifact_sha256")
    if not expected:
        return "manifest artifact_sha256 is required"
    observed = artifact_sha256(card_path)
    if expected != observed:
        return "manifest artifact_sha256 does not match candidate card bytes"
    return None


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data
