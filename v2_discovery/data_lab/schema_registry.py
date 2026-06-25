from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


SCHEMA_ROOT = Path("contracts/data_snapshot")
PERMISSION_MATRIX_SCHEMA = "wrds_permission_matrix.schema.json"
SNAPSHOT_MANIFEST_SCHEMA = "wrds_snapshot_manifest.schema.json"


class SchemaRegistryError(RuntimeError):
    """Raised when a V2 data snapshot payload fails a schema contract."""


def registered_schemas() -> dict[str, str]:
    return {
        "wrds_permission_matrix": PERMISSION_MATRIX_SCHEMA,
        "wrds_snapshot_manifest": SNAPSHOT_MANIFEST_SCHEMA,
    }


def load_schema(schema_name: str, *, repo_root: str | Path = ".") -> dict[str, Any]:
    if schema_name in registered_schemas():
        file_name = registered_schemas()[schema_name]
    else:
        file_name = schema_name
    path = Path(repo_root) / SCHEMA_ROOT / file_name
    if not path.exists():
        raise SchemaRegistryError(f"schema not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SchemaRegistryError(f"schema must be a JSON object: {path}")
    Draft202012Validator.check_schema(payload)
    return payload


def validate_payload(
    payload: Mapping[str, Any],
    schema_name: str,
    *,
    repo_root: str | Path = ".",
) -> None:
    schema = load_schema(schema_name, repo_root=repo_root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(dict(payload)), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise SchemaRegistryError(f"{schema_name} schema violation at {path}: {first.message}")


def validate_permission_matrix_schema(
    payload: Mapping[str, Any],
    *,
    repo_root: str | Path = ".",
) -> None:
    validate_payload(payload, "wrds_permission_matrix", repo_root=repo_root)
    from v2_discovery.data_lab.permission_matrix import validate_permission_matrix_payload

    validate_permission_matrix_payload(payload)


def validate_snapshot_manifest_schema(
    payload: Mapping[str, Any],
    *,
    repo_root: str | Path = ".",
) -> None:
    validate_payload(payload, "wrds_snapshot_manifest", repo_root=repo_root)
    from v2_discovery.data_lab.snapshot_manifest import validate_snapshot_manifest_payload

    validate_snapshot_manifest_payload(payload)
