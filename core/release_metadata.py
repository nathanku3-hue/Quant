from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


RELEASE_METADATA_SCHEMA_VERSION = 1
_DIGEST_TOKEN = "@sha256:"
_HEX_DIGITS = frozenset("0123456789abcdef")
_ALLOWED_STATUS = frozenset({"idle", "pending_probe", "active", "rolled_back", "rollback_failed"})


def is_digest_locked_release_ref(value: str) -> bool:
    """Return True when a release ref includes a valid sha256 digest lock."""
    if not isinstance(value, str):
        return False
    ref = value.strip()
    if not ref:
        return False

    head, token, digest = ref.rpartition(_DIGEST_TOKEN)
    if token != _DIGEST_TOKEN:
        return False
    if not head or "@" in head:
        return False

    digest_norm = digest.lower()
    return len(digest_norm) == 64 and all(ch in _HEX_DIGITS for ch in digest_norm)


def require_digest_locked_release_ref(value: str) -> str:
    """Normalize and validate a digest-locked release reference."""
    if not isinstance(value, str):
        raise ValueError("release_ref must be a string.")
    ref = value.strip()
    if not is_digest_locked_release_ref(ref):
        raise ValueError("release_ref must be digest-locked (name[:tag]@sha256:<64-hex>).")

    head, _, digest = ref.rpartition(_DIGEST_TOKEN)
    return f"{head}{_DIGEST_TOKEN}{digest.lower()}"


def extract_release_digest(value: str) -> str:
    """Extract and normalize sha256 digest from a digest-locked release ref."""
    normalized = require_digest_locked_release_ref(value)
    _, _, digest = normalized.rpartition(_DIGEST_TOKEN)
    return digest.lower()


def build_release_cache_fingerprint(version: str, release_digest: str | None) -> str:
    """
    Bind cache keys to immutable artifact identity.

    Formula:
      cache_fingerprint = "<version>@sha256:<digest|local-dev>"
    """
    version_text = _require_str(version, "version")
    digest = str(release_digest or "").strip().lower()
    if not digest:
        digest = "local-dev"
    return f"{version_text}@sha256:{digest}"


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    out = value.strip()
    if not out:
        raise ValueError(f"{field_name} must be non-empty.")
    return out


@dataclass(frozen=True)
class ReleaseRecord:
    """Immutable release payload stored in controller metadata."""

    version: str
    release_ref: str
    deployed_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", _require_str(self.version, "version"))
        object.__setattr__(self, "release_ref", require_digest_locked_release_ref(self.release_ref))
        object.__setattr__(self, "deployed_at", _require_str(self.deployed_at, "deployed_at"))

    def to_dict(self) -> dict[str, str]:
        return {
            "version": self.version,
            "release_ref": self.release_ref,
            "deployed_at": self.deployed_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReleaseRecord":
        if not isinstance(payload, Mapping):
            raise ValueError("release record must be a mapping.")
        return cls(
            version=payload.get("version"),
            release_ref=payload.get("release_ref"),
            deployed_at=payload.get("deployed_at"),
        )


def _parse_release_or_none(value: Any, field_name: str) -> ReleaseRecord | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping or null.")
    return ReleaseRecord.from_dict(value)


def _parse_probe(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("last_probe must be a mapping or null.")

    ok = value.get("ok")
    details = value.get("details")
    checked_at = value.get("checked_at")
    rollback_ok = value.get("rollback_ok", None)

    if not isinstance(ok, bool):
        raise ValueError("last_probe.ok must be bool.")
    if not isinstance(details, str):
        raise ValueError("last_probe.details must be str.")
    if not isinstance(checked_at, str):
        raise ValueError("last_probe.checked_at must be str.")
    if rollback_ok is not None and not isinstance(rollback_ok, bool):
        raise ValueError("last_probe.rollback_ok must be bool when provided.")

    payload = {"ok": ok, "details": details, "checked_at": checked_at}
    if rollback_ok is not None:
        payload["rollback_ok"] = rollback_ok
    return payload


@dataclass(frozen=True)
class ReleaseMetadata:
    """Controller state for candidate promotion and rollback operations."""

    schema_version: int = RELEASE_METADATA_SCHEMA_VERSION
    current_release: ReleaseRecord | None = None
    previous_release: ReleaseRecord | None = None
    pending_release: ReleaseRecord | None = None
    last_candidate_release: ReleaseRecord | None = None
    status: str = "idle"
    last_action: str = "initialized"
    last_probe: dict[str, Any] | None = None
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != RELEASE_METADATA_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {RELEASE_METADATA_SCHEMA_VERSION}, got {self.schema_version}."
            )
        if self.status not in _ALLOWED_STATUS:
            raise ValueError(f"status must be one of {sorted(_ALLOWED_STATUS)}.")
        if not isinstance(self.last_action, str) or not self.last_action.strip():
            raise ValueError("last_action must be a non-empty string.")
        if not isinstance(self.updated_at, str):
            raise ValueError("updated_at must be a string.")
        release_fields = (
            ("current_release", self.current_release),
            ("previous_release", self.previous_release),
            ("pending_release", self.pending_release),
            ("last_candidate_release", self.last_candidate_release),
        )
        for field_name, record in release_fields:
            if record is not None and not isinstance(record, ReleaseRecord):
                raise ValueError(f"{field_name} must be ReleaseRecord or None.")
        if self.status == "active" and self.current_release is None:
            raise ValueError("current_release is required when status=active.")
        if self.status == "pending_probe" and self.pending_release is None:
            raise ValueError("pending_release is required when status=pending_probe.")
        if self.status == "rolled_back" and self.current_release is None:
            raise ValueError("current_release is required when status=rolled_back.")
        if self.last_probe is not None:
            _parse_probe(self.last_probe)

    def to_dict(self) -> dict[str, Any]:
        def _serialize(record: ReleaseRecord | None) -> dict[str, str] | None:
            return None if record is None else record.to_dict()

        return {
            "schema_version": self.schema_version,
            "current_release": _serialize(self.current_release),
            "previous_release": _serialize(self.previous_release),
            "pending_release": _serialize(self.pending_release),
            "last_candidate_release": _serialize(self.last_candidate_release),
            "status": self.status,
            "last_action": self.last_action,
            "last_probe": self.last_probe,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReleaseMetadata":
        if not isinstance(payload, Mapping):
            raise ValueError("release metadata payload must be a mapping.")

        schema_version = payload.get("schema_version", RELEASE_METADATA_SCHEMA_VERSION)
        if schema_version != RELEASE_METADATA_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported release metadata schema version: {schema_version}."
            )

        status = payload.get("status", "idle")
        if not isinstance(status, str):
            raise ValueError("status must be a string.")

        last_action = payload.get("last_action", "initialized")
        if not isinstance(last_action, str):
            raise ValueError("last_action must be a string.")

        updated_at = payload.get("updated_at", "")
        if not isinstance(updated_at, str):
            raise ValueError("updated_at must be a string.")

        return cls(
            schema_version=schema_version,
            current_release=_parse_release_or_none(payload.get("current_release"), "current_release"),
            previous_release=_parse_release_or_none(payload.get("previous_release"), "previous_release"),
            pending_release=_parse_release_or_none(payload.get("pending_release"), "pending_release"),
            last_candidate_release=_parse_release_or_none(
                payload.get("last_candidate_release"), "last_candidate_release"
            ),
            status=status,
            last_action=last_action.strip() or "initialized",
            last_probe=_parse_probe(payload.get("last_probe")),
            updated_at=updated_at,
        )
