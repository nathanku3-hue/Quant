from __future__ import annotations

from typing import Any, Mapping

from data.provenance import utc_now_iso
from v2_discovery.data_lab.permission_matrix import DENIED_ACTIONS
from v2_discovery.data_lab.permission_matrix import PERMISSION_MATRIX_ID
from v2_discovery.data_lab.permission_matrix import PERMISSION_STATUS_APPROVED
from v2_discovery.data_lab.permission_matrix import PERMISSION_STATUSES
from v2_discovery.data_lab.permission_matrix import PermissionMatrixError
from v2_discovery.data_lab.permission_matrix import V2_D0_SCOPE_ID
from v2_discovery.data_lab.permission_matrix import WrdsPermissionMatrix
from v2_discovery.data_lab.permission_matrix import build_default_wrds_permission_matrix
from v2_discovery.data_lab.permission_matrix import validate_permission_matrix_payload


WRDS_PROBE_SCHEMA_VERSION = "1.0.0"
WRDS_PROBE_ID = "V2_D0_WRDS_PERMISSION_PROBE_CONTRACT"
WRDS_PROBE_CODE_REF = "v2_discovery/data_lab/wrds_probe.py@v2-d0"
WRDS_PROBE_NEXT_ALLOWED_ACTION = "record_permission_decision_only"
WRDS_PROBE_REQUIRED_MANUAL_INPUTS = (
    "WRDS account/license owner",
    "library/table permission truth",
    "approved read-only probe scope",
    "snapshot generation approval if later requested",
    "rollback/removal rule for any future snapshot",
)
WRDS_PROBE_ROOT_KEYS = frozenset(
    {
        "schema_version",
        "probe_id",
        "scope_id",
        "permission_matrix_id",
        "execution_mode",
        "provider",
        "provider_access_allowed",
        "wrds_connection_attempted",
        "snapshot_generation_allowed",
        "data_output_allowed",
        "v1_canonical_write_allowed",
        "requested_by",
        "datasets",
        "required_manual_inputs",
        "next_allowed_action",
        "denied_actions",
        "created_at_utc",
        "code_ref",
    }
)
WRDS_PROBE_DATASET_KEYS = frozenset(
    {
        "dataset_id",
        "wrds_library",
        "wrds_table",
        "permission_status",
        "approval_ref",
    }
)
WRDS_PROBE_FORBIDDEN_EXTRA_KEY_TOKENS = (
    "credential",
    "password",
    "token",
    "secret",
    "username",
    "connection_uri",
    "connection_string",
    "query",
    "output_path",
    "snapshot_path",
)


def build_wrds_permission_probe_contract(
    matrix: WrdsPermissionMatrix | Mapping[str, Any] | None = None,
    *,
    requested_by: str = "terminal_zero_v2_d0",
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    permission_matrix = _coerce_matrix(matrix)
    return {
        "schema_version": WRDS_PROBE_SCHEMA_VERSION,
        "probe_id": WRDS_PROBE_ID,
        "scope_id": V2_D0_SCOPE_ID,
        "permission_matrix_id": permission_matrix.matrix_id,
        "execution_mode": "offline_contract_only",
        "provider": "wrds",
        "provider_access_allowed": False,
        "wrds_connection_attempted": False,
        "snapshot_generation_allowed": False,
        "data_output_allowed": False,
        "v1_canonical_write_allowed": False,
        "requested_by": str(requested_by).strip() or "terminal_zero_v2_d0",
        "datasets": [
            {
                "dataset_id": entry.dataset_id,
                "wrds_library": entry.wrds_library,
                "wrds_table": entry.wrds_table,
                "permission_status": entry.permission_status,
                "approval_ref": entry.approval_ref,
            }
            for entry in permission_matrix.entries
        ],
        "required_manual_inputs": list(WRDS_PROBE_REQUIRED_MANUAL_INPUTS),
        "next_allowed_action": WRDS_PROBE_NEXT_ALLOWED_ACTION,
        "denied_actions": list(DENIED_ACTIONS),
        "created_at_utc": created_at_utc or utc_now_iso(),
        "code_ref": WRDS_PROBE_CODE_REF,
    }


def validate_wrds_permission_probe_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise PermissionMatrixError("WRDS probe contract must be a mapping")
    actual_keys = set(payload)
    missing = sorted(WRDS_PROBE_ROOT_KEYS - actual_keys)
    extra = sorted(actual_keys - WRDS_PROBE_ROOT_KEYS)
    if missing:
        raise PermissionMatrixError("WRDS probe contract missing field(s): " + ", ".join(missing))
    if extra:
        _raise_probe_extra_fields(extra, "WRDS probe contract")
    if payload["schema_version"] != WRDS_PROBE_SCHEMA_VERSION:
        raise PermissionMatrixError("WRDS probe schema_version mismatch")
    if payload["probe_id"] != WRDS_PROBE_ID:
        raise PermissionMatrixError("WRDS probe id mismatch")
    if payload["scope_id"] != V2_D0_SCOPE_ID:
        raise PermissionMatrixError("WRDS probe scope_id mismatch")
    if payload["permission_matrix_id"] != PERMISSION_MATRIX_ID:
        raise PermissionMatrixError("WRDS probe permission_matrix_id mismatch")
    if payload["execution_mode"] != "offline_contract_only":
        raise PermissionMatrixError("WRDS probe execution_mode must be offline_contract_only")
    if str(payload["provider"]).lower() != "wrds":
        raise PermissionMatrixError("WRDS probe provider must be wrds")
    for field in (
        "provider_access_allowed",
        "wrds_connection_attempted",
        "snapshot_generation_allowed",
        "data_output_allowed",
        "v1_canonical_write_allowed",
    ):
        if payload[field] is not False:
            raise PermissionMatrixError(f"WRDS probe {field} must remain false")
    requested_by = _require_probe_text(payload["requested_by"], "requested_by")
    if not requested_by:
        raise PermissionMatrixError("WRDS probe requested_by is required")
    if not isinstance(payload["required_manual_inputs"], list) or tuple(
        payload["required_manual_inputs"]
    ) != WRDS_PROBE_REQUIRED_MANUAL_INPUTS:
        raise PermissionMatrixError("WRDS probe required_manual_inputs mismatch")
    if payload["next_allowed_action"] != WRDS_PROBE_NEXT_ALLOWED_ACTION:
        raise PermissionMatrixError("WRDS probe next_allowed_action mismatch")
    if payload["denied_actions"] != list(DENIED_ACTIONS):
        raise PermissionMatrixError("WRDS probe denied_actions mismatch")
    _require_probe_text(payload["created_at_utc"], "created_at_utc")
    if payload["code_ref"] != WRDS_PROBE_CODE_REF:
        raise PermissionMatrixError("WRDS probe code_ref mismatch")
    if not isinstance(payload["datasets"], list) or not payload["datasets"]:
        raise PermissionMatrixError("WRDS probe datasets must be a non-empty list")
    _validate_probe_datasets(payload["datasets"])
    return dict(payload)


def _raise_probe_extra_fields(fields: list[str], label: str) -> None:
    lowered = [field.lower() for field in fields]
    if any(
        token in field
        for field in lowered
        for token in WRDS_PROBE_FORBIDDEN_EXTRA_KEY_TOKENS
    ):
        raise PermissionMatrixError(
            f"{label} unexpected credential/connection/output field(s): "
            + ", ".join(fields)
        )
    raise PermissionMatrixError(f"{label} unexpected field(s): " + ", ".join(fields))


def _require_probe_text(value: Any, field: str) -> str:
    if value is None:
        raise PermissionMatrixError(f"WRDS probe {field} is required")
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan"}:
        raise PermissionMatrixError(f"WRDS probe {field} is required")
    return text


def _validate_probe_datasets(rows: list[Any]) -> None:
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise PermissionMatrixError("WRDS probe dataset entries must be mappings")
        actual_keys = set(row)
        missing = sorted(WRDS_PROBE_DATASET_KEYS - actual_keys)
        extra = sorted(actual_keys - WRDS_PROBE_DATASET_KEYS)
        if missing:
            raise PermissionMatrixError(
                "WRDS probe dataset missing field(s): " + ", ".join(missing)
            )
        if extra:
            _raise_probe_extra_fields(extra, "WRDS probe dataset")
        dataset_id = _require_probe_text(row["dataset_id"], "dataset_id")
        if dataset_id in seen:
            raise PermissionMatrixError("WRDS probe dataset_id values must be unique")
        seen.add(dataset_id)
        _require_probe_text(row["wrds_library"], "wrds_library")
        _require_probe_text(row["wrds_table"], "wrds_table")
        permission_status = _require_probe_text(row["permission_status"], "permission_status")
        if permission_status not in PERMISSION_STATUSES:
            raise PermissionMatrixError(
                f"WRDS probe invalid permission_status: {permission_status!r}"
            )
        approval_ref = row["approval_ref"]
        if approval_ref is not None:
            _require_probe_text(approval_ref, "approval_ref")
        if permission_status == PERMISSION_STATUS_APPROVED and approval_ref is None:
            raise PermissionMatrixError(
                "WRDS probe approved dataset entries require approval_ref"
            )


def _coerce_matrix(matrix: WrdsPermissionMatrix | Mapping[str, Any] | None) -> WrdsPermissionMatrix:
    if matrix is None:
        return build_default_wrds_permission_matrix()
    if isinstance(matrix, WrdsPermissionMatrix):
        return matrix
    return validate_permission_matrix_payload(matrix)
