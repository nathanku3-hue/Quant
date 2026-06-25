from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from data.provenance import utc_now_iso


PERMISSION_MATRIX_SCHEMA_VERSION = "1.0.0"
PERMISSION_MATRIX_ID = "V2_D0_WRDS_PERMISSION_MATRIX"
V2_D0_SCOPE_ID = "V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT"
V2_D0_CODE_REF = "v2_discovery/data_lab/permission_matrix.py@v2-d0"

PERMISSION_STATUS_UNKNOWN = "unknown"
PERMISSION_STATUS_PENDING = "pending"
PERMISSION_STATUS_APPROVED = "approved"
PERMISSION_STATUS_DENIED = "denied"
PERMISSION_STATUS_NOT_REQUESTED = "not_requested"
PERMISSION_STATUSES = frozenset(
    {
        PERMISSION_STATUS_UNKNOWN,
        PERMISSION_STATUS_PENDING,
        PERMISSION_STATUS_APPROVED,
        PERMISSION_STATUS_DENIED,
        PERMISSION_STATUS_NOT_REQUESTED,
    }
)

ALLOWED_USE_READ_ONLY_PROBE = "read_only_permission_probe"
ALLOWED_USE_PIT_DESIGN = "pit_snapshot_design"
ALLOWED_USE_SCHEMA_DISCOVERY = "schema_discovery"
ALLOWED_USE_PROVENANCE_CONTRACT = "provenance_contract"
ALLOWED_USES = frozenset(
    {
        ALLOWED_USE_READ_ONLY_PROBE,
        ALLOWED_USE_PIT_DESIGN,
        ALLOWED_USE_SCHEMA_DISCOVERY,
        ALLOWED_USE_PROVENANCE_CONTRACT,
    }
)

DENIED_ACTIONS = (
    "wrds_provider_connection",
    "pit_snapshot_generation",
    "committed_wrds_output",
    "v1_canonical_data_write",
    "data_processed_write",
    "candidate_ranking",
    "candidate_scoring",
    "candidate_promotion",
    "recommendations",
    "dashboard_runtime_integration",
    "alert_or_broker_path",
    "sqlite_storage",
    "safe_boot_claim",
    "boot_ready_claim",
)


class PermissionMatrixError(RuntimeError):
    """Raised when the V2-D0 WRDS permission contract is widened."""


ENTRY_KEYS = frozenset(
    {
        "dataset_id",
        "wrds_library",
        "wrds_table",
        "dataset_name",
        "permission_status",
        "allowed_uses",
        "license_scope",
        "pit_required",
        "provider_access_allowed",
        "snapshot_generation_allowed",
        "data_output_allowed",
        "v1_canonical_write_allowed",
        "approval_ref",
        "notes",
    }
)


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
        raise PermissionMatrixError(f"{field} is required")
    return text


def _normalize_status(value: Any) -> str:
    status = _require_text(value, "permission_status").lower()
    if status not in PERMISSION_STATUSES:
        raise PermissionMatrixError(f"invalid permission_status: {value!r}")
    return status


def _normalize_allowed_uses(values: Any) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)) or isinstance(values, (str, bytes)):
        raise PermissionMatrixError("allowed_uses must be a finite sequence")
    if not values:
        raise PermissionMatrixError("allowed_uses must not be empty")
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        use = _require_text(raw, "allowed_uses").lower()
        if use not in ALLOWED_USES:
            raise PermissionMatrixError(f"invalid allowed_use: {raw!r}")
        if use not in seen:
            out.append(use)
            seen.add(use)
    return tuple(out)


def _normalize_notes(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)) or isinstance(values, (str, bytes)):
        raise PermissionMatrixError("notes must be a finite sequence")
    return tuple(_require_text(item, "notes") for item in values if _clean_text(item))


def _require_false(value: Any, field: str) -> bool:
    if value is not False:
        raise PermissionMatrixError(f"{field} must remain false in V2-D0")
    return False


def _require_jsonable(value: Mapping[str, Any], field: str) -> None:
    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise PermissionMatrixError(f"{field} must be JSON serializable") from exc


def _require_raw_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PermissionMatrixError(f"{field} must be a non-empty string")
    return value


def _require_raw_optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PermissionMatrixError(f"{field} must be a string or null")
    return value


@dataclass(frozen=True)
class WrdsPermissionEntry:
    dataset_id: str
    wrds_library: str
    wrds_table: str
    dataset_name: str
    permission_status: str = PERMISSION_STATUS_UNKNOWN
    allowed_uses: tuple[str, ...] = (
        ALLOWED_USE_READ_ONLY_PROBE,
        ALLOWED_USE_PIT_DESIGN,
        ALLOWED_USE_PROVENANCE_CONTRACT,
    )
    license_scope: str = "permission_unknown"
    pit_required: bool = True
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
        object.__setattr__(self, "permission_status", _normalize_status(self.permission_status))
        object.__setattr__(self, "allowed_uses", _normalize_allowed_uses(self.allowed_uses))
        object.__setattr__(self, "license_scope", _require_text(self.license_scope, "license_scope"))
        object.__setattr__(self, "pit_required", bool(self.pit_required))
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
        if self.permission_status == PERMISSION_STATUS_APPROVED and not approval_ref:
            raise PermissionMatrixError("approved permission entries require approval_ref")
        object.__setattr__(self, "approval_ref", approval_ref)
        object.__setattr__(self, "notes", _normalize_notes(self.notes))
        _require_jsonable(self.to_dict(), "permission entry")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "wrds_library": self.wrds_library,
            "wrds_table": self.wrds_table,
            "dataset_name": self.dataset_name,
            "permission_status": self.permission_status,
            "allowed_uses": list(self.allowed_uses),
            "license_scope": self.license_scope,
            "pit_required": self.pit_required,
            "provider_access_allowed": False,
            "snapshot_generation_allowed": False,
            "data_output_allowed": False,
            "v1_canonical_write_allowed": False,
            "approval_ref": self.approval_ref,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> WrdsPermissionEntry:
        return cls(
            dataset_id=payload.get("dataset_id"),
            wrds_library=payload.get("wrds_library"),
            wrds_table=payload.get("wrds_table"),
            dataset_name=payload.get("dataset_name"),
            permission_status=payload.get("permission_status", PERMISSION_STATUS_UNKNOWN),
            allowed_uses=tuple(
                payload.get("allowed_uses")
                or (
                    ALLOWED_USE_READ_ONLY_PROBE,
                    ALLOWED_USE_PIT_DESIGN,
                    ALLOWED_USE_PROVENANCE_CONTRACT,
                )
            ),
            license_scope=payload.get("license_scope", "permission_unknown"),
            pit_required=payload.get("pit_required", True),
            provider_access_allowed=payload.get("provider_access_allowed", False),
            snapshot_generation_allowed=payload.get("snapshot_generation_allowed", False),
            data_output_allowed=payload.get("data_output_allowed", False),
            v1_canonical_write_allowed=payload.get("v1_canonical_write_allowed", False),
            approval_ref=payload.get("approval_ref"),
            notes=tuple(payload.get("notes") or ()),
        )


@dataclass(frozen=True)
class WrdsPermissionMatrix:
    entries: tuple[WrdsPermissionEntry, ...]
    matrix_id: str = PERMISSION_MATRIX_ID
    scope_id: str = V2_D0_SCOPE_ID
    authority: str = "offline_contract_only"
    provider: str = "wrds"
    provider_access_allowed: bool = False
    snapshot_generation_allowed: bool = False
    data_output_allowed: bool = False
    v1_canonical_write_allowed: bool = False
    schema_version: str = PERMISSION_MATRIX_SCHEMA_VERSION
    created_at_utc: str | None = None
    code_ref: str = V2_D0_CODE_REF

    def __post_init__(self) -> None:
        entries = tuple(self.entries)
        if not entries:
            raise PermissionMatrixError("permission matrix requires at least one entry")
        if not all(isinstance(entry, WrdsPermissionEntry) for entry in entries):
            raise PermissionMatrixError("permission matrix entries must be WrdsPermissionEntry")
        ids = [entry.dataset_id for entry in entries]
        if len(ids) != len(set(ids)):
            raise PermissionMatrixError("dataset_id values must be unique")
        object.__setattr__(self, "entries", entries)
        matrix_id = _require_text(self.matrix_id, "matrix_id")
        if matrix_id != PERMISSION_MATRIX_ID:
            raise PermissionMatrixError("matrix_id mismatch")
        object.__setattr__(self, "matrix_id", matrix_id)
        scope_id = _require_text(self.scope_id, "scope_id")
        if scope_id != V2_D0_SCOPE_ID:
            raise PermissionMatrixError("scope_id mismatch")
        object.__setattr__(self, "scope_id", scope_id)
        authority = _require_text(self.authority, "authority")
        if authority != "offline_contract_only":
            raise PermissionMatrixError("authority must be offline_contract_only")
        object.__setattr__(self, "authority", authority)
        if _require_text(self.provider, "provider").lower() != "wrds":
            raise PermissionMatrixError("provider must be wrds")
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
        schema_version = _require_text(self.schema_version, "schema_version")
        if schema_version != PERMISSION_MATRIX_SCHEMA_VERSION:
            raise PermissionMatrixError("schema_version mismatch")
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(
            self,
            "created_at_utc",
            _clean_text(self.created_at_utc) or utc_now_iso(),
        )
        code_ref = _require_text(self.code_ref, "code_ref")
        if code_ref != V2_D0_CODE_REF:
            raise PermissionMatrixError("code_ref mismatch")
        object.__setattr__(self, "code_ref", code_ref)
        _require_jsonable(self.to_dict(), "permission matrix")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "matrix_id": self.matrix_id,
            "scope_id": self.scope_id,
            "authority": self.authority,
            "provider": self.provider,
            "provider_access_allowed": False,
            "snapshot_generation_allowed": False,
            "data_output_allowed": False,
            "v1_canonical_write_allowed": False,
            "entries": [entry.to_dict() for entry in self.entries],
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
    def from_dict(cls, payload: Mapping[str, Any]) -> WrdsPermissionMatrix:
        entries = tuple(WrdsPermissionEntry.from_dict(item) for item in payload.get("entries") or ())
        return cls(
            entries=entries,
            matrix_id=payload.get("matrix_id", PERMISSION_MATRIX_ID),
            scope_id=payload.get("scope_id", V2_D0_SCOPE_ID),
            authority=payload.get("authority", "offline_contract_only"),
            provider=payload.get("provider", "wrds"),
            provider_access_allowed=payload.get("provider_access_allowed", False),
            snapshot_generation_allowed=payload.get("snapshot_generation_allowed", False),
            data_output_allowed=payload.get("data_output_allowed", False),
            v1_canonical_write_allowed=payload.get("v1_canonical_write_allowed", False),
            schema_version=payload.get("schema_version", PERMISSION_MATRIX_SCHEMA_VERSION),
            created_at_utc=payload.get("created_at_utc"),
            code_ref=payload.get("code_ref", V2_D0_CODE_REF),
        )


DEFAULT_WRDS_DATASETS = (
    {
        "dataset_id": "crsp_daily_stock_file",
        "wrds_library": "crsp",
        "wrds_table": "dsf",
        "dataset_name": "CRSP Daily Stock File",
        "notes": ("Needed for PIT prices/returns after explicit approval.",),
    },
    {
        "dataset_id": "crsp_stocknames",
        "wrds_library": "crsp",
        "wrds_table": "stocknames",
        "dataset_name": "CRSP Stock Names",
        "notes": ("Needed for identifier history and ticker/permno drift.",),
    },
    {
        "dataset_id": "crsp_ccm_linktable",
        "wrds_library": "crsp",
        "wrds_table": "ccmxpf_linktable",
        "dataset_name": "CRSP/Compustat Link Table",
        "notes": ("Needed for PIT issuer joins after permission approval.",),
    },
    {
        "dataset_id": "compustat_fundamentals_quarterly",
        "wrds_library": "comp",
        "wrds_table": "fundq",
        "dataset_name": "Compustat Quarterly Fundamentals",
        "notes": ("Needed for release-date aligned fundamentals after approval.",),
    },
    {
        "dataset_id": "ibes_detail_eps_us",
        "wrds_library": "ibes",
        "wrds_table": "det_epsus",
        "dataset_name": "IBES Detail EPS US",
        "notes": ("Needed for PEAD estimate/surprise variants after approval.",),
    },
)


def build_default_wrds_permission_matrix(
    datasets: Iterable[Mapping[str, Any] | WrdsPermissionEntry] | None = None,
    *,
    created_at_utc: str | None = None,
) -> WrdsPermissionMatrix:
    raw_entries = tuple(datasets or DEFAULT_WRDS_DATASETS)
    entries = tuple(
        item if isinstance(item, WrdsPermissionEntry) else WrdsPermissionEntry.from_dict(item)
        for item in raw_entries
    )
    return WrdsPermissionMatrix(entries=entries, created_at_utc=created_at_utc)


def validate_permission_matrix_payload(payload: Mapping[str, Any]) -> WrdsPermissionMatrix:
    expected_keys = set(WrdsPermissionMatrix(entries=(WrdsPermissionEntry(
        dataset_id="placeholder",
        wrds_library="placeholder",
        wrds_table="placeholder",
        dataset_name="placeholder",
    ),)).to_dict())
    actual_keys = set(payload)
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    if missing:
        raise PermissionMatrixError("permission matrix missing field(s): " + ", ".join(missing))
    if extra:
        raise PermissionMatrixError("permission matrix unexpected field(s): " + ", ".join(extra))
    if payload.get("denied_actions") != list(DENIED_ACTIONS):
        raise PermissionMatrixError("denied_actions mismatch")
    if payload.get("provider") != "wrds":
        raise PermissionMatrixError("provider must be wrds")
    if not isinstance(payload.get("created_at_utc"), str) or not payload.get("created_at_utc", "").strip():
        raise PermissionMatrixError("created_at_utc must be a non-empty string")
    entries = payload.get("entries")
    if not isinstance(entries, (list, tuple)) or not entries:
        raise PermissionMatrixError("entries must be a non-empty sequence")
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise PermissionMatrixError("permission matrix entries must be mappings")
        entry_keys = set(entry)
        entry_missing = sorted(ENTRY_KEYS - entry_keys)
        entry_extra = sorted(entry_keys - ENTRY_KEYS)
        if entry_missing:
            raise PermissionMatrixError(
                f"permission matrix entry {index} missing field(s): " + ", ".join(entry_missing)
            )
        if entry_extra:
            raise PermissionMatrixError(
                f"permission matrix entry {index} unexpected field(s): " + ", ".join(entry_extra)
            )
        for field in ("dataset_id", "wrds_library", "wrds_table", "dataset_name", "license_scope"):
            _require_raw_text(entry.get(field), f"entries[{index}].{field}")
        if entry.get("permission_status") not in PERMISSION_STATUSES:
            raise PermissionMatrixError(f"entries[{index}].permission_status invalid")
        allowed_uses = entry.get("allowed_uses")
        if not isinstance(allowed_uses, list) or not allowed_uses:
            raise PermissionMatrixError(f"entries[{index}].allowed_uses must be a non-empty list")
        for use in allowed_uses:
            if not isinstance(use, str) or use not in ALLOWED_USES:
                raise PermissionMatrixError(f"entries[{index}].allowed_uses invalid")
        if not isinstance(entry.get("pit_required"), bool):
            raise PermissionMatrixError(f"entries[{index}].pit_required must be boolean")
        for field in (
            "provider_access_allowed",
            "snapshot_generation_allowed",
            "data_output_allowed",
            "v1_canonical_write_allowed",
        ):
            if entry.get(field) is not False:
                raise PermissionMatrixError(f"entries[{index}].{field} must remain false")
        approval_ref = _require_raw_optional_text(entry.get("approval_ref"), f"entries[{index}].approval_ref")
        if entry.get("permission_status") == PERMISSION_STATUS_APPROVED and not (approval_ref or "").strip():
            raise PermissionMatrixError(f"entries[{index}].approval_ref is required when approved")
        notes = entry.get("notes")
        if not isinstance(notes, list):
            raise PermissionMatrixError(f"entries[{index}].notes must be a list")
        if any(not isinstance(note, str) for note in notes):
            raise PermissionMatrixError(f"entries[{index}].notes must contain only strings")
    return WrdsPermissionMatrix.from_dict(payload)
