from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from opportunity_engine.discovery_intake_schema import (
    DiscoveryIntakeValidationError,
    DiscoveryIntakeValidationResult,
    assert_valid_candidate_intake_queue,
    validate_candidate_intake_queue,
    validate_discovery_theme_taxonomy,
)


def load_discovery_theme_taxonomy(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def load_candidate_intake_queue(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def load_candidate_intake_manifest(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def validate_discovery_intake_bundle(
    queue_path: str | Path,
    manifest_path: str | Path,
) -> DiscoveryIntakeValidationResult:
    queue = load_candidate_intake_queue(queue_path)
    manifest = load_candidate_intake_manifest(manifest_path)
    result = validate_candidate_intake_queue(queue, manifest=manifest)
    hash_error = _validate_manifest_hash(Path(queue_path), manifest)
    if hash_error is None:
        return result
    return DiscoveryIntakeValidationResult(
        valid=False,
        errors=(*result.errors, hash_error),
    )


def assert_valid_discovery_intake_bundle(queue_path: str | Path, manifest_path: str | Path) -> None:
    result = validate_discovery_intake_bundle(queue_path, manifest_path)
    if not result.valid:
        raise DiscoveryIntakeValidationError("; ".join(result.errors))

    queue = load_candidate_intake_queue(queue_path)
    manifest = load_candidate_intake_manifest(manifest_path)
    assert_valid_candidate_intake_queue(queue, manifest=manifest)


def validate_theme_and_queue_bundle(
    theme_path: str | Path,
    queue_path: str | Path,
    manifest_path: str | Path,
) -> DiscoveryIntakeValidationResult:
    themes = load_discovery_theme_taxonomy(theme_path)
    theme_result = validate_discovery_theme_taxonomy(themes)
    queue_result = validate_discovery_intake_bundle(queue_path, manifest_path)
    return DiscoveryIntakeValidationResult(
        valid=theme_result.valid and queue_result.valid,
        errors=(*theme_result.errors, *queue_result.errors),
    )


def artifact_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _validate_manifest_hash(queue_path: Path, manifest: Mapping[str, Any]) -> str | None:
    expected = manifest.get("artifact_sha256")
    if not expected:
        return "manifest artifact_sha256 is required"
    observed = artifact_sha256(queue_path)
    if expected != observed:
        return "manifest artifact_sha256 does not match candidate intake queue bytes"
    return None


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data
