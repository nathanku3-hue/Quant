from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from data.provenance import utc_now_iso
from v2_discovery.data_lab.permission_matrix import ALLOWED_USE_PROVENANCE_CONTRACT
from v2_discovery.data_lab.permission_matrix import DENIED_ACTIONS


PERMISSION_TRUTH_SCHEMA_VERSION = "1.0.0"
PERMISSION_TRUTH_ARTIFACT_ID = "V2_D0_1_WRDS_PERMISSION_TRUTH_SCOPE"
V2_D0_1_SCOPE_ID = "V2-D0.1_WRDS_ENTITLEMENT_TRUTH_SCOPE"
V2_D0_1_CODE_REF = "v2_discovery/data_lab/permission_truth.py@v2-d0.1"

ENTITLEMENT_STATUS_PENDING = "pending"
ENTITLEMENT_STATUS_APPROVED = "approved"
ENTITLEMENT_STATUSES = frozenset({ENTITLEMENT_STATUS_PENDING, ENTITLEMENT_STATUS_APPROVED})

PEAD_STARTER_SCOPE_REQUESTED = "requested"
PEAD_STARTER_SCOPE_NOT_REQUESTED = "not_requested"
PEAD_STARTER_SCOPES = frozenset(
    {PEAD_STARTER_SCOPE_REQUESTED, PEAD_STARTER_SCOPE_NOT_REQUESTED}
)

ROOT_KEYS = frozenset(
    {
        "schema_version",
        "artifact_id",
        "scope_id",
        "authority",
        "provider",
        "provider_access_allowed",
        "snapshot_generation_allowed",
        "data_output_allowed",
        "v1_canonical_write_allowed",
        "rows",
        "denied_actions",
        "created_at_utc",
        "code_ref",
    }
)
ROW_KEYS = frozenset(
    {
        "dataset_id",
        "wrds_library",
        "wrds_table",
        "dataset_name",
        "allowed_uses",
        "v2_d0_1_entitlement_status",
        "pead_v2_001_starter_scope",
        "provider_access_allowed",
        "snapshot_generation_allowed",
        "data_output_allowed",
        "v1_canonical_write_allowed",
        "approval_ref",
        "notes",
    }
)
FORBIDDEN_EXTRA_KEY_TOKENS = (
    "credential",
    "password",
    "token",
    "secret",
    "username",
    "connection",
    "query",
    "output",
    "snapshot_path",
    "storage_path",
)


class PermissionTruthError(RuntimeError):
    """Raised when the V2-D0.1 permission-truth scope is widened."""


DEFAULT_V2_D0_1_ROWS = (
    {
        "dataset_id": "crsp_daily_stock_file",
        "wrds_library": "crsp",
        "wrds_table": "dsf",
        "dataset_name": "CRSP Daily Stock File",
        "pead_v2_001_starter_scope": PEAD_STARTER_SCOPE_REQUESTED,
        "notes": ("V2-D0.1 entitlement truth row; PEAD_V2_001 starter dependency.",),
    },
    {
        "dataset_id": "crsp_stocknames",
        "wrds_library": "crsp",
        "wrds_table": "stocknames",
        "dataset_name": "CRSP Stock Names",
        "pead_v2_001_starter_scope": PEAD_STARTER_SCOPE_REQUESTED,
        "notes": ("V2-D0.1 entitlement truth row; PEAD_V2_001 starter dependency.",),
    },
    {
        "dataset_id": "crsp_ccm_linktable",
        "wrds_library": "crsp",
        "wrds_table": "ccmxpf_linktable",
        "dataset_name": "CRSP/Compustat Link Table",
        "pead_v2_001_starter_scope": PEAD_STARTER_SCOPE_REQUESTED,
        "notes": ("V2-D0.1 entitlement truth row; PEAD_V2_001 starter dependency.",),
    },
    {
        "dataset_id": "compustat_fundamentals_quarterly",
        "wrds_library": "comp",
        "wrds_table": "fundq",
        "dataset_name": "Compustat Quarterly Fundamentals",
        "pead_v2_001_starter_scope": PEAD_STARTER_SCOPE_REQUESTED,
        "notes": ("V2-D0.1 entitlement truth row; PEAD_V2_001 starter dependency.",),
    },
    {
        "dataset_id": "ibes_detail_eps_us",
        "wrds_library": "ibes",
        "wrds_table": "det_epsus",
        "dataset_name": "IBES Detail EPS US",
        "pead_v2_001_starter_scope": PEAD_STARTER_SCOPE_NOT_REQUESTED,
        "notes": (
            "V2-D0.1 entitlement truth row; deliberately not requested for PEAD_V2_001 starter.",
        ),
    },
)
EXPECTED_ROW_KEYS = tuple(row["dataset_id"] for row in DEFAULT_V2_D0_1_ROWS)
EXPECTED_LIBRARY_TABLES = tuple(
    f"{row['wrds_library']}.{row['wrds_table']}" for row in DEFAULT_V2_D0_1_ROWS
)
EXPECTED_PEAD_STARTER_SCOPES = {
    row["dataset_id"]: row["pead_v2_001_starter_scope"] for row in DEFAULT_V2_D0_1_ROWS
}


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
        raise PermissionTruthError(f"{field} is required")
    return text


def _require_raw_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PermissionTruthError(f"{field} must be a non-empty string")
    return value


def _require_raw_optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PermissionTruthError(f"{field} must be a string or null")
    return value


def _require_false(value: Any, field: str) -> bool:
    if value is not False:
        raise PermissionTruthError(f"{field} must remain false in V2-D0.1")
    return False


def _normalize_allowed_uses(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or isinstance(value, (str, bytes)):
        raise PermissionTruthError("allowed_uses must be a list")
    if tuple(value) != (ALLOWED_USE_PROVENANCE_CONTRACT,):
        raise PermissionTruthError('allowed_uses must equal ["provenance_contract"]')
    return (ALLOWED_USE_PROVENANCE_CONTRACT,)


def _normalize_status(value: Any) -> str:
    status = _require_text(value, "v2_d0_1_entitlement_status").lower()
    if status not in ENTITLEMENT_STATUSES:
        raise PermissionTruthError(f"invalid v2_d0_1_entitlement_status: {value!r}")
    return status


def _normalize_starter_scope(value: Any) -> str:
    scope = _require_text(value, "pead_v2_001_starter_scope").lower()
    if scope not in PEAD_STARTER_SCOPES:
        raise PermissionTruthError(f"invalid pead_v2_001_starter_scope: {value!r}")
    return scope


def _normalize_notes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)) or isinstance(value, (str, bytes)):
        raise PermissionTruthError("notes must be a list")
    return tuple(_require_text(item, "notes") for item in value if _clean_text(item))


def _raise_extra_fields(fields: list[str], label: str) -> None:
    lowered = [field.lower() for field in fields]
    if any(token in field for field in lowered for token in FORBIDDEN_EXTRA_KEY_TOKENS):
        raise PermissionTruthError(
            f"{label} unexpected credential/connection/query/output field(s): "
            + ", ".join(fields)
        )
    raise PermissionTruthError(f"{label} unexpected field(s): " + ", ".join(fields))


def _approval_lookup_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row["dataset_id"]), f"{row['wrds_library']}.{row['wrds_table']}")


@dataclass(frozen=True)
class V2D01PermissionTruthRow:
    dataset_id: str
    wrds_library: str
    wrds_table: str
    dataset_name: str
    pead_v2_001_starter_scope: str
    v2_d0_1_entitlement_status: str = ENTITLEMENT_STATUS_PENDING
    allowed_uses: tuple[str, ...] = (ALLOWED_USE_PROVENANCE_CONTRACT,)
    provider_access_allowed: bool = False
    snapshot_generation_allowed: bool = False
    data_output_allowed: bool = False
    v1_canonical_write_allowed: bool = False
    approval_ref: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", _require_text(self.dataset_id, "dataset_id"))
        object.__setattr__(self, "wrds_library", _require_text(self.wrds_library, "wrds_library"))
        object.__setattr__(self, "wrds_table", _require_text(self.wrds_table, "wrds_table"))
        object.__setattr__(self, "dataset_name", _require_text(self.dataset_name, "dataset_name"))
        object.__setattr__(self, "allowed_uses", _normalize_allowed_uses(self.allowed_uses))
        status = _normalize_status(self.v2_d0_1_entitlement_status)
        object.__setattr__(self, "v2_d0_1_entitlement_status", status)
        starter_scope = _normalize_starter_scope(self.pead_v2_001_starter_scope)
        object.__setattr__(self, "pead_v2_001_starter_scope", starter_scope)
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
            "data_output_allowed",
            _require_false(self.data_output_allowed, "data_output_allowed"),
        )
        object.__setattr__(
            self,
            "v1_canonical_write_allowed",
            _require_false(self.v1_canonical_write_allowed, "v1_canonical_write_allowed"),
        )
        approval_ref = _clean_text(self.approval_ref) or None
        if status == ENTITLEMENT_STATUS_APPROVED and not approval_ref:
            raise PermissionTruthError("approved V2-D0.1 rows require approval_ref")
        object.__setattr__(self, "approval_ref", approval_ref)
        object.__setattr__(self, "notes", _normalize_notes(self.notes))
        json.dumps(self.to_dict(), sort_keys=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "wrds_library": self.wrds_library,
            "wrds_table": self.wrds_table,
            "dataset_name": self.dataset_name,
            "allowed_uses": list(self.allowed_uses),
            "v2_d0_1_entitlement_status": self.v2_d0_1_entitlement_status,
            "pead_v2_001_starter_scope": self.pead_v2_001_starter_scope,
            "provider_access_allowed": False,
            "snapshot_generation_allowed": False,
            "data_output_allowed": False,
            "v1_canonical_write_allowed": False,
            "approval_ref": self.approval_ref,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> V2D01PermissionTruthRow:
        return cls(
            dataset_id=payload.get("dataset_id"),
            wrds_library=payload.get("wrds_library"),
            wrds_table=payload.get("wrds_table"),
            dataset_name=payload.get("dataset_name"),
            allowed_uses=tuple(payload.get("allowed_uses") or ()),
            v2_d0_1_entitlement_status=payload.get(
                "v2_d0_1_entitlement_status",
                ENTITLEMENT_STATUS_PENDING,
            ),
            pead_v2_001_starter_scope=payload.get("pead_v2_001_starter_scope"),
            provider_access_allowed=payload.get("provider_access_allowed", False),
            snapshot_generation_allowed=payload.get("snapshot_generation_allowed", False),
            data_output_allowed=payload.get("data_output_allowed", False),
            v1_canonical_write_allowed=payload.get("v1_canonical_write_allowed", False),
            approval_ref=payload.get("approval_ref"),
            notes=tuple(payload.get("notes") or ()),
        )


@dataclass(frozen=True)
class V2D01PermissionTruthScope:
    rows: tuple[V2D01PermissionTruthRow, ...]
    schema_version: str = PERMISSION_TRUTH_SCHEMA_VERSION
    artifact_id: str = PERMISSION_TRUTH_ARTIFACT_ID
    scope_id: str = V2_D0_1_SCOPE_ID
    authority: str = "offline_contract_only"
    provider: str = "wrds"
    provider_access_allowed: bool = False
    snapshot_generation_allowed: bool = False
    data_output_allowed: bool = False
    v1_canonical_write_allowed: bool = False
    created_at_utc: str | None = None
    code_ref: str = V2_D0_1_CODE_REF

    def __post_init__(self) -> None:
        rows = tuple(self.rows)
        if not rows or not all(isinstance(row, V2D01PermissionTruthRow) for row in rows):
            raise PermissionTruthError("rows must be V2D01PermissionTruthRow entries")
        _validate_exact_rows(rows)
        object.__setattr__(self, "rows", rows)
        if _require_text(self.schema_version, "schema_version") != PERMISSION_TRUTH_SCHEMA_VERSION:
            raise PermissionTruthError("schema_version mismatch")
        if _require_text(self.artifact_id, "artifact_id") != PERMISSION_TRUTH_ARTIFACT_ID:
            raise PermissionTruthError("artifact_id mismatch")
        if _require_text(self.scope_id, "scope_id") != V2_D0_1_SCOPE_ID:
            raise PermissionTruthError("scope_id mismatch")
        if _require_text(self.authority, "authority") != "offline_contract_only":
            raise PermissionTruthError("authority must be offline_contract_only")
        if _require_text(self.provider, "provider").lower() != "wrds":
            raise PermissionTruthError("provider must be wrds")
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
            "data_output_allowed",
            _require_false(self.data_output_allowed, "data_output_allowed"),
        )
        object.__setattr__(
            self,
            "v1_canonical_write_allowed",
            _require_false(self.v1_canonical_write_allowed, "v1_canonical_write_allowed"),
        )
        object.__setattr__(self, "created_at_utc", _clean_text(self.created_at_utc) or utc_now_iso())
        if _require_text(self.code_ref, "code_ref") != V2_D0_1_CODE_REF:
            raise PermissionTruthError("code_ref mismatch")
        json.dumps(self.to_dict(), sort_keys=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_id": self.artifact_id,
            "scope_id": self.scope_id,
            "authority": self.authority,
            "provider": self.provider,
            "provider_access_allowed": False,
            "snapshot_generation_allowed": False,
            "data_output_allowed": False,
            "v1_canonical_write_allowed": False,
            "rows": [row.to_dict() for row in self.rows],
            "denied_actions": list(DENIED_ACTIONS),
            "created_at_utc": self.created_at_utc,
            "code_ref": self.code_ref,
        }

    def stable_hash(self) -> str:
        payload = self.to_dict()
        payload = {key: value for key, value in payload.items() if key != "created_at_utc"}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> V2D01PermissionTruthScope:
        return cls(
            schema_version=payload.get("schema_version", PERMISSION_TRUTH_SCHEMA_VERSION),
            artifact_id=payload.get("artifact_id", PERMISSION_TRUTH_ARTIFACT_ID),
            scope_id=payload.get("scope_id", V2_D0_1_SCOPE_ID),
            authority=payload.get("authority", "offline_contract_only"),
            provider=payload.get("provider", "wrds"),
            provider_access_allowed=payload.get("provider_access_allowed", False),
            snapshot_generation_allowed=payload.get("snapshot_generation_allowed", False),
            data_output_allowed=payload.get("data_output_allowed", False),
            v1_canonical_write_allowed=payload.get("v1_canonical_write_allowed", False),
            rows=tuple(V2D01PermissionTruthRow.from_dict(row) for row in payload.get("rows") or ()),
            created_at_utc=payload.get("created_at_utc"),
            code_ref=payload.get("code_ref", V2_D0_1_CODE_REF),
        )


def build_v2_d0_1_permission_truth_scope(
    *,
    approval_refs: Mapping[str, str] | None = None,
    created_at_utc: str | None = None,
) -> V2D01PermissionTruthScope:
    refs = dict(approval_refs or {})
    valid_ref_keys = set(EXPECTED_ROW_KEYS) | set(EXPECTED_LIBRARY_TABLES)
    unexpected_refs = sorted(set(refs) - valid_ref_keys)
    if unexpected_refs:
        raise PermissionTruthError(
            "approval_refs contains unknown V2-D0.1 row key(s): " + ", ".join(unexpected_refs)
        )
    for key, value in refs.items():
        if not isinstance(value, str) or not value.strip():
            raise PermissionTruthError(f"approval_refs[{key}] must be a non-empty string")
    rows: list[V2D01PermissionTruthRow] = []
    for raw_row in DEFAULT_V2_D0_1_ROWS:
        dataset_key, table_key = _approval_lookup_key(raw_row)
        approval_ref = refs.get(dataset_key) or refs.get(table_key)
        rows.append(
            V2D01PermissionTruthRow(
                dataset_id=raw_row["dataset_id"],
                wrds_library=raw_row["wrds_library"],
                wrds_table=raw_row["wrds_table"],
                dataset_name=raw_row["dataset_name"],
                pead_v2_001_starter_scope=raw_row["pead_v2_001_starter_scope"],
                v2_d0_1_entitlement_status=(
                    ENTITLEMENT_STATUS_APPROVED
                    if _clean_text(approval_ref)
                    else ENTITLEMENT_STATUS_PENDING
                ),
                approval_ref=approval_ref,
                notes=tuple(raw_row.get("notes") or ()),
            )
        )
    return V2D01PermissionTruthScope(rows=tuple(rows), created_at_utc=created_at_utc)


def validate_v2_d0_1_permission_truth_payload(
    payload: Mapping[str, Any],
) -> V2D01PermissionTruthScope:
    if not isinstance(payload, Mapping):
        raise PermissionTruthError("V2-D0.1 permission truth payload must be a mapping")
    actual_keys = set(payload)
    missing = sorted(ROOT_KEYS - actual_keys)
    extra = sorted(actual_keys - ROOT_KEYS)
    if missing:
        raise PermissionTruthError("permission truth missing field(s): " + ", ".join(missing))
    if extra:
        _raise_extra_fields(extra, "permission truth")
    if payload["denied_actions"] != list(DENIED_ACTIONS):
        raise PermissionTruthError("denied_actions mismatch")
    if payload["schema_version"] != PERMISSION_TRUTH_SCHEMA_VERSION:
        raise PermissionTruthError("schema_version mismatch")
    if payload["artifact_id"] != PERMISSION_TRUTH_ARTIFACT_ID:
        raise PermissionTruthError("artifact_id mismatch")
    if payload["scope_id"] != V2_D0_1_SCOPE_ID:
        raise PermissionTruthError("scope_id mismatch")
    if payload["authority"] != "offline_contract_only":
        raise PermissionTruthError("authority must be offline_contract_only")
    if payload["provider"] != "wrds":
        raise PermissionTruthError("provider must be wrds")
    if payload["code_ref"] != V2_D0_1_CODE_REF:
        raise PermissionTruthError("code_ref mismatch")
    for field in (
        "provider_access_allowed",
        "snapshot_generation_allowed",
        "data_output_allowed",
        "v1_canonical_write_allowed",
    ):
        if payload[field] is not False:
            raise PermissionTruthError(f"{field} must remain false")
    if not isinstance(payload["created_at_utc"], str) or not payload["created_at_utc"].strip():
        raise PermissionTruthError("created_at_utc must be a non-empty string")
    rows = payload["rows"]
    if not isinstance(rows, list):
        raise PermissionTruthError("rows must be a list")
    _validate_raw_rows(rows)
    return V2D01PermissionTruthScope.from_dict(payload)


def _validate_raw_rows(rows: list[Any]) -> None:
    if len(rows) != len(DEFAULT_V2_D0_1_ROWS):
        raise PermissionTruthError("V2-D0.1 permission truth requires exactly five rows")
    seen_dataset_ids: set[str] = set()
    seen_library_tables: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise PermissionTruthError("permission truth rows must be mappings")
        actual_keys = set(row)
        missing = sorted(ROW_KEYS - actual_keys)
        extra = sorted(actual_keys - ROW_KEYS)
        if missing:
            raise PermissionTruthError(f"row {index} missing field(s): " + ", ".join(missing))
        if extra:
            _raise_extra_fields(extra, f"row {index}")
        dataset_id = _require_raw_text(row["dataset_id"], f"rows[{index}].dataset_id")
        wrds_library = _require_raw_text(row["wrds_library"], f"rows[{index}].wrds_library")
        wrds_table = _require_raw_text(row["wrds_table"], f"rows[{index}].wrds_table")
        _require_raw_text(row["dataset_name"], f"rows[{index}].dataset_name")
        if dataset_id in seen_dataset_ids:
            raise PermissionTruthError("dataset_id values must be unique")
        seen_dataset_ids.add(dataset_id)
        library_table = f"{wrds_library}.{wrds_table}"
        if library_table in seen_library_tables:
            raise PermissionTruthError("wrds library.table values must be unique")
        seen_library_tables.add(library_table)
        if row["allowed_uses"] != [ALLOWED_USE_PROVENANCE_CONTRACT]:
            raise PermissionTruthError(
                f'rows[{index}].allowed_uses must equal ["provenance_contract"]'
            )
        status = row["v2_d0_1_entitlement_status"]
        if status not in ENTITLEMENT_STATUSES:
            raise PermissionTruthError(f"rows[{index}].v2_d0_1_entitlement_status invalid")
        starter_scope = row["pead_v2_001_starter_scope"]
        if starter_scope not in PEAD_STARTER_SCOPES:
            raise PermissionTruthError(f"rows[{index}].pead_v2_001_starter_scope invalid")
        for field in (
            "provider_access_allowed",
            "snapshot_generation_allowed",
            "data_output_allowed",
            "v1_canonical_write_allowed",
        ):
            if row[field] is not False:
                raise PermissionTruthError(f"rows[{index}].{field} must remain false")
        approval_ref = _require_raw_optional_text(row["approval_ref"], f"rows[{index}].approval_ref")
        if status == ENTITLEMENT_STATUS_APPROVED and not (approval_ref or "").strip():
            raise PermissionTruthError("approved V2-D0.1 rows require approval_ref")
        notes = row["notes"]
        if not isinstance(notes, list) or any(not isinstance(note, str) for note in notes):
            raise PermissionTruthError(f"rows[{index}].notes must be a string list")
    if tuple(row["dataset_id"] for row in rows) != EXPECTED_ROW_KEYS:
        raise PermissionTruthError("V2-D0.1 rows must match the exact default dataset order")
    if tuple(f"{row['wrds_library']}.{row['wrds_table']}" for row in rows) != EXPECTED_LIBRARY_TABLES:
        raise PermissionTruthError("V2-D0.1 rows must match the exact default library.table set")
    for row in rows:
        expected_scope = EXPECTED_PEAD_STARTER_SCOPES[row["dataset_id"]]
        if row["pead_v2_001_starter_scope"] != expected_scope:
            raise PermissionTruthError(
                f"{row['dataset_id']} pead_v2_001_starter_scope must be {expected_scope}"
            )


def _validate_exact_rows(rows: tuple[V2D01PermissionTruthRow, ...]) -> None:
    if len(rows) != len(DEFAULT_V2_D0_1_ROWS):
        raise PermissionTruthError("V2-D0.1 permission truth requires exactly five rows")
    dataset_ids = tuple(row.dataset_id for row in rows)
    if dataset_ids != EXPECTED_ROW_KEYS:
        raise PermissionTruthError("V2-D0.1 rows must match the exact default dataset order")
    library_tables = tuple(f"{row.wrds_library}.{row.wrds_table}" for row in rows)
    if library_tables != EXPECTED_LIBRARY_TABLES:
        raise PermissionTruthError("V2-D0.1 rows must match the exact default library.table set")
    if len(set(dataset_ids)) != len(dataset_ids):
        raise PermissionTruthError("dataset_id values must be unique")
    if len(set(library_tables)) != len(library_tables):
        raise PermissionTruthError("wrds library.table values must be unique")
    for row in rows:
        expected_scope = EXPECTED_PEAD_STARTER_SCOPES[row.dataset_id]
        if row.pead_v2_001_starter_scope != expected_scope:
            raise PermissionTruthError(
                f"{row.dataset_id} pead_v2_001_starter_scope must be {expected_scope}"
            )
