from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping

from data.provenance import utc_now_iso
from v2_discovery.data_lab.permission_matrix import DENIED_ACTIONS
from v2_discovery.data_lab.permission_matrix import PERMISSION_STATUSES
from v2_discovery.data_lab.permission_matrix import PERMISSION_MATRIX_ID
from v2_discovery.data_lab.permission_matrix import PermissionMatrixError
from v2_discovery.data_lab.permission_matrix import V2_D0_SCOPE_ID
from v2_discovery.data_lab.permission_matrix import WrdsPermissionMatrix
from v2_discovery.data_lab.permission_matrix import build_default_wrds_permission_matrix
from v2_discovery.data_lab.permission_matrix import validate_permission_matrix_payload


SNAPSHOT_MANIFEST_SCHEMA_VERSION = "1.0.0"
SNAPSHOT_MANIFEST_ID = "V2_D0_WRDS_SNAPSHOT_MANIFEST_CONTRACT"
SNAPSHOT_MANIFEST_STATUS = "contract_only"
SNAPSHOT_MANIFEST_CODE_REF = "v2_discovery/data_lab/snapshot_manifest.py@v2-d0"
DEFAULT_PLANNED_STORAGE_URI = (
    "data/runtime_cache/v2_data_lab/wrds_snapshots/v2_d0_contract_only/"
)
APPROVED_STORAGE_PREFIX = "data/runtime_cache/v2_data_lab/"
SNAPSHOT_SCHEMA_URI = "contracts/data_snapshot/wrds_snapshot_manifest.schema.json"

FORBIDDEN_STORAGE_PREFIXES = (
    "data/processed/",
    "data/registry/",
    "runtime/boot_status_current.json",
    "docs/context/boot_status_current.json",
)

DATASET_KEYS = frozenset(
    {
        "dataset_id",
        "wrds_library",
        "wrds_table",
        "permission_status",
        "primary_key",
        "point_in_time_fields",
        "release_date_field",
        "effective_date_field",
    }
)


class SnapshotManifestError(RuntimeError):
    """Raised when the WRDS snapshot manifest contract is widened."""


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _require_text(value: Any, field: str) -> str:
    text = _clean_text(value)
    if not text:
        raise SnapshotManifestError(f"{field} is required")
    return text


def _require_raw_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotManifestError(f"{field} must be a non-empty string")
    return value


def _require_raw_optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SnapshotManifestError(f"{field} must be a string or null")
    return value


def _require_false(value: Any, field: str) -> bool:
    if value is not False:
        raise SnapshotManifestError(f"{field} must remain false in V2-D0")
    return False


def _normalize_storage_uri(value: Any) -> str:
    raw_uri = _require_text(value, "planned_storage_uri")
    if "://" in raw_uri or raw_uri.lower().startswith(("file:", "s3:", "http:", "https:")):
        raise SnapshotManifestError("planned_storage_uri must be repo-relative")
    if raw_uri.startswith(("/", "\\")):
        raise SnapshotManifestError("planned_storage_uri must be repo-relative")
    if len(raw_uri) >= 2 and raw_uri[1] == ":":
        raise SnapshotManifestError("planned_storage_uri must not include a drive letter")
    uri = raw_uri.replace("\\", "/")
    if uri.startswith("//"):
        raise SnapshotManifestError("planned_storage_uri must not be a UNC path")
    normalized = PurePosixPath(uri).as_posix()
    path_parts = PurePosixPath(normalized).parts
    if ".." in path_parts or "." in path_parts:
        raise SnapshotManifestError("planned_storage_uri must be path-confined")
    lowered = normalized.lower()
    for prefix in FORBIDDEN_STORAGE_PREFIXES:
        if lowered == prefix.rstrip("/") or lowered.startswith(prefix):
            raise SnapshotManifestError(f"planned_storage_uri cannot target {prefix}")
    if not lowered.startswith(APPROVED_STORAGE_PREFIX):
        raise SnapshotManifestError(
            f"planned_storage_uri must be under {APPROVED_STORAGE_PREFIX}"
        )
    return normalized if uri.endswith("/") else normalized


def _require_pit_policy(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SnapshotManifestError("pit_policy must be a mapping")
    required_true = (
        "point_in_time_required",
        "release_date_required",
        "no_future_leakage",
        "snapshot_as_of_required",
        "extraction_log_required",
        "manifest_hash_required",
    )
    policy = dict(value)
    expected = set(required_true)
    actual = set(policy)
    extra = sorted(actual - expected)
    missing = sorted(expected - actual)
    if missing:
        raise SnapshotManifestError("pit_policy missing field(s): " + ", ".join(missing))
    if extra:
        raise SnapshotManifestError("pit_policy unexpected field(s): " + ", ".join(extra))
    for field in required_true:
        if policy.get(field) is not True:
            raise SnapshotManifestError(f"pit_policy.{field} must be true")
    return policy


def _require_datasets(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise SnapshotManifestError("datasets must be a non-empty sequence")
    datasets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping):
            raise SnapshotManifestError("dataset entries must be mappings")
        item_keys = set(item)
        missing = sorted(DATASET_KEYS - item_keys)
        extra = sorted(item_keys - DATASET_KEYS)
        if missing:
            raise SnapshotManifestError("dataset missing field(s): " + ", ".join(missing))
        if extra:
            raise SnapshotManifestError("dataset unexpected field(s): " + ", ".join(extra))
        if item.get("permission_status") not in PERMISSION_STATUSES:
            raise SnapshotManifestError("dataset permission_status invalid")
        row = {
            "dataset_id": _require_raw_text(item.get("dataset_id"), "dataset_id"),
            "wrds_library": _require_raw_text(item.get("wrds_library"), "wrds_library"),
            "wrds_table": _require_raw_text(item.get("wrds_table"), "wrds_table"),
            "permission_status": item["permission_status"],
            "primary_key": _require_string_list(item.get("primary_key"), "primary_key"),
            "point_in_time_fields": _require_string_list(
                item.get("point_in_time_fields"),
                "point_in_time_fields",
            ),
            "release_date_field": _require_raw_optional_text(
                item.get("release_date_field"),
                "release_date_field",
            ),
            "effective_date_field": _require_raw_optional_text(
                item.get("effective_date_field"),
                "effective_date_field",
            ),
        }
        if row["dataset_id"] in seen:
            raise SnapshotManifestError("dataset_id values must be unique")
        seen.add(row["dataset_id"])
        datasets.append(row)
    return tuple(datasets)


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise SnapshotManifestError(f"{field} must be a non-empty sequence")
    return [_require_raw_text(item, field) for item in value]


@dataclass(frozen=True)
class WrdsSnapshotManifest:
    manifest_id: str
    permission_matrix_id: str
    permission_matrix_sha256: str
    datasets: tuple[dict[str, Any], ...]
    planned_storage_uri: str = DEFAULT_PLANNED_STORAGE_URI
    pit_policy: Mapping[str, Any] | None = None
    schema_version: str = SNAPSHOT_MANIFEST_SCHEMA_VERSION
    scope_id: str = V2_D0_SCOPE_ID
    manifest_status: str = SNAPSHOT_MANIFEST_STATUS
    provider: str = "wrds"
    provider_access_allowed: bool = False
    snapshot_generation_allowed: bool = False
    committed_wrds_output_allowed: bool = False
    data_output_allowed: bool = False
    v1_canonical_write_allowed: bool = False
    schema_registry_uri: str = SNAPSHOT_SCHEMA_URI
    created_at_utc: str | None = None
    code_ref: str = SNAPSHOT_MANIFEST_CODE_REF

    def __post_init__(self) -> None:
        manifest_id = _require_text(self.manifest_id, "manifest_id")
        if manifest_id != SNAPSHOT_MANIFEST_ID:
            raise SnapshotManifestError("manifest_id mismatch")
        object.__setattr__(self, "manifest_id", manifest_id)
        object.__setattr__(
            self,
            "permission_matrix_id",
            _require_text(self.permission_matrix_id, "permission_matrix_id"),
        )
        if self.permission_matrix_id != PERMISSION_MATRIX_ID:
            raise SnapshotManifestError("permission_matrix_id mismatch")
        sha = _require_text(self.permission_matrix_sha256, "permission_matrix_sha256")
        if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha.lower()):
            raise SnapshotManifestError("permission_matrix_sha256 must be lowercase SHA256")
        object.__setattr__(self, "permission_matrix_sha256", sha.lower())
        object.__setattr__(self, "datasets", _require_datasets(self.datasets))
        object.__setattr__(
            self,
            "planned_storage_uri",
            _normalize_storage_uri(self.planned_storage_uri),
        )
        object.__setattr__(
            self,
            "pit_policy",
            _require_pit_policy(self.pit_policy or default_pit_policy()),
        )
        schema_version = _require_text(self.schema_version, "schema_version")
        if schema_version != SNAPSHOT_MANIFEST_SCHEMA_VERSION:
            raise SnapshotManifestError("schema_version mismatch")
        object.__setattr__(self, "schema_version", schema_version)
        if self.scope_id != V2_D0_SCOPE_ID:
            raise SnapshotManifestError("scope_id mismatch")
        if self.manifest_status != SNAPSHOT_MANIFEST_STATUS:
            raise SnapshotManifestError("manifest_status must be contract_only")
        if str(self.provider).lower() != "wrds":
            raise SnapshotManifestError("provider must be wrds")
        object.__setattr__(self, "provider", "wrds")
        object.__setattr__(
            self,
            "provider_access_allowed",
            _require_false(self.provider_access_allowed, "provider_access_allowed"),
        )
        object.__setattr__(
            self,
            "snapshot_generation_allowed",
            _require_false(self.snapshot_generation_allowed, "snapshot_generation_allowed"),
        )
        object.__setattr__(
            self,
            "committed_wrds_output_allowed",
            _require_false(self.committed_wrds_output_allowed, "committed_wrds_output_allowed"),
        )
        object.__setattr__(
            self,
            "data_output_allowed",
            _require_false(self.data_output_allowed, "data_output_allowed"),
        )
        object.__setattr__(
            self,
            "v1_canonical_write_allowed",
            _require_false(self.v1_canonical_write_allowed, "v1_canonical_write_allowed"),
        )
        schema_registry_uri = _require_text(
            self.schema_registry_uri,
            "schema_registry_uri",
        ).replace("\\", "/")
        if schema_registry_uri != SNAPSHOT_SCHEMA_URI:
            raise SnapshotManifestError("schema_registry_uri mismatch")
        object.__setattr__(self, "schema_registry_uri", schema_registry_uri)
        object.__setattr__(
            self,
            "created_at_utc",
            _clean_text(self.created_at_utc) or utc_now_iso(),
        )
        code_ref = _require_text(self.code_ref, "code_ref")
        if code_ref != SNAPSHOT_MANIFEST_CODE_REF:
            raise SnapshotManifestError("code_ref mismatch")
        object.__setattr__(self, "code_ref", code_ref)
        json.dumps(self.to_dict(), sort_keys=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "scope_id": self.scope_id,
            "manifest_status": self.manifest_status,
            "provider": self.provider,
            "provider_access_allowed": False,
            "snapshot_generation_allowed": False,
            "committed_wrds_output_allowed": False,
            "data_output_allowed": False,
            "v1_canonical_write_allowed": False,
            "planned_storage_uri": self.planned_storage_uri,
            "permission_matrix_id": self.permission_matrix_id,
            "permission_matrix_sha256": self.permission_matrix_sha256,
            "datasets": [dict(item) for item in self.datasets],
            "pit_policy": dict(self.pit_policy or {}),
            "schema_registry_uri": self.schema_registry_uri,
            "denied_actions": list(DENIED_ACTIONS),
            "created_at_utc": self.created_at_utc,
            "code_ref": self.code_ref,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> WrdsSnapshotManifest:
        return cls(
            schema_version=payload.get("schema_version", SNAPSHOT_MANIFEST_SCHEMA_VERSION),
            manifest_id=payload.get("manifest_id"),
            scope_id=payload.get("scope_id", V2_D0_SCOPE_ID),
            manifest_status=payload.get("manifest_status", SNAPSHOT_MANIFEST_STATUS),
            provider=payload.get("provider", "wrds"),
            provider_access_allowed=payload.get("provider_access_allowed", False),
            snapshot_generation_allowed=payload.get("snapshot_generation_allowed", False),
            committed_wrds_output_allowed=payload.get("committed_wrds_output_allowed", False),
            data_output_allowed=payload.get("data_output_allowed", False),
            v1_canonical_write_allowed=payload.get("v1_canonical_write_allowed", False),
            planned_storage_uri=payload.get("planned_storage_uri", DEFAULT_PLANNED_STORAGE_URI),
            permission_matrix_id=payload.get("permission_matrix_id"),
            permission_matrix_sha256=payload.get("permission_matrix_sha256"),
            datasets=tuple(payload.get("datasets") or ()),
            pit_policy=payload.get("pit_policy"),
            schema_registry_uri=payload.get("schema_registry_uri", SNAPSHOT_SCHEMA_URI),
            created_at_utc=payload.get("created_at_utc"),
            code_ref=payload.get("code_ref", SNAPSHOT_MANIFEST_CODE_REF),
        )


def default_pit_policy() -> dict[str, bool]:
    return {
        "point_in_time_required": True,
        "release_date_required": True,
        "no_future_leakage": True,
        "snapshot_as_of_required": True,
        "extraction_log_required": True,
        "manifest_hash_required": True,
    }


def build_wrds_snapshot_manifest(
    matrix: WrdsPermissionMatrix | Mapping[str, Any] | None = None,
    *,
    manifest_id: str = SNAPSHOT_MANIFEST_ID,
    planned_storage_uri: str = DEFAULT_PLANNED_STORAGE_URI,
    created_at_utc: str | None = None,
) -> WrdsSnapshotManifest:
    permission_matrix = _coerce_matrix(matrix)
    datasets = tuple(
        {
            "dataset_id": entry.dataset_id,
            "wrds_library": entry.wrds_library,
            "wrds_table": entry.wrds_table,
            "permission_status": entry.permission_status,
            "primary_key": _default_primary_key(entry.dataset_id),
            "point_in_time_fields": _default_pit_fields(entry.dataset_id),
            "release_date_field": _default_release_date_field(entry.dataset_id),
            "effective_date_field": _default_effective_date_field(entry.dataset_id),
        }
        for entry in permission_matrix.entries
    )
    return WrdsSnapshotManifest(
        manifest_id=manifest_id,
        permission_matrix_id=permission_matrix.matrix_id,
        permission_matrix_sha256=permission_matrix.stable_hash(),
        datasets=datasets,
        planned_storage_uri=planned_storage_uri,
        created_at_utc=created_at_utc,
    )


def validate_snapshot_manifest_payload(payload: Mapping[str, Any]) -> WrdsSnapshotManifest:
    expected_keys = set(
        WrdsSnapshotManifest(
            manifest_id=SNAPSHOT_MANIFEST_ID,
            permission_matrix_id=PERMISSION_MATRIX_ID,
            permission_matrix_sha256="0" * 64,
            datasets=(
                {
                    "dataset_id": "placeholder",
                    "wrds_library": "placeholder",
                    "wrds_table": "placeholder",
                    "permission_status": "unknown",
                    "primary_key": ["placeholder"],
                    "point_in_time_fields": ["placeholder"],
                    "release_date_field": None,
                    "effective_date_field": None,
                },
            ),
        ).to_dict()
    )
    actual_keys = set(payload)
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    if missing:
        raise SnapshotManifestError("snapshot manifest missing field(s): " + ", ".join(missing))
    if extra:
        raise SnapshotManifestError("snapshot manifest unexpected field(s): " + ", ".join(extra))
    _require_datasets(payload["datasets"])
    if payload.get("denied_actions") != list(DENIED_ACTIONS):
        raise SnapshotManifestError("denied_actions mismatch")
    if payload.get("provider") != "wrds":
        raise SnapshotManifestError("provider must be wrds")
    if not isinstance(payload.get("permission_matrix_sha256"), str) or payload[
        "permission_matrix_sha256"
    ] != payload["permission_matrix_sha256"].lower():
        raise SnapshotManifestError("permission_matrix_sha256 must be lowercase SHA256")
    if payload.get("schema_registry_uri") != SNAPSHOT_SCHEMA_URI:
        raise SnapshotManifestError("schema_registry_uri mismatch")
    if not isinstance(payload.get("created_at_utc"), str) or not payload.get("created_at_utc", "").strip():
        raise SnapshotManifestError("created_at_utc must be a non-empty string")
    return WrdsSnapshotManifest.from_dict(payload)


def _coerce_matrix(matrix: WrdsPermissionMatrix | Mapping[str, Any] | None) -> WrdsPermissionMatrix:
    if matrix is None:
        return build_default_wrds_permission_matrix()
    if isinstance(matrix, WrdsPermissionMatrix):
        return matrix
    try:
        return validate_permission_matrix_payload(matrix)
    except PermissionMatrixError as exc:
        raise SnapshotManifestError(f"invalid permission matrix: {exc}") from exc


def _default_primary_key(dataset_id: str) -> list[str]:
    if dataset_id in {"crsp_daily_stock_file"}:
        return ["date", "permno"]
    if dataset_id in {"crsp_stocknames"}:
        return ["permno", "namedt", "nameendt"]
    if dataset_id in {"crsp_ccm_linktable"}:
        return ["gvkey", "lpermno", "linkdt", "linkenddt"]
    if dataset_id.startswith("compustat"):
        return ["gvkey", "datadate"]
    if dataset_id.startswith("ibes"):
        return ["ticker", "anndats", "fpedats"]
    return ["dataset_native_key", "as_of_date"]


def _default_pit_fields(dataset_id: str) -> list[str]:
    if dataset_id in {"crsp_daily_stock_file"}:
        return ["date"]
    if dataset_id in {"crsp_stocknames"}:
        return ["namedt", "nameendt"]
    if dataset_id in {"crsp_ccm_linktable"}:
        return ["linkdt", "linkenddt"]
    if dataset_id.startswith("compustat"):
        return ["datadate", "rdq"]
    if dataset_id.startswith("ibes"):
        return ["anndats", "fpedats", "revdats"]
    return ["as_of_date"]


def _default_release_date_field(dataset_id: str) -> str | None:
    if dataset_id.startswith("compustat"):
        return "rdq"
    if dataset_id.startswith("ibes"):
        return "anndats"
    return None


def _default_effective_date_field(dataset_id: str) -> str | None:
    if dataset_id in {"crsp_stocknames"}:
        return "namedt"
    if dataset_id in {"crsp_ccm_linktable"}:
        return "linkdt"
    return None
