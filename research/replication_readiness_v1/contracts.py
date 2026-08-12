"""Fail-closed quarantine contract for independent-replication readiness.

This surface is intentionally metadata-only.  It cannot store replication
outcomes, labels, performance statistics, raw data, credentials, or provider
query output.  Actual family-specific replication acquisition remains a later,
demand-pulled authority decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


REPLICATION_READINESS_SCHEMA = "independent_replication_readiness_v1"
REPLICATION_RESEARCH_VISIBILITY = "READINESS_METADATA_ONLY"
REPLICATION_OUTCOME_ACCESS_DENIED = "DENIED"
REPLICATION_ACQUISITION_AUTHORITY = "NOT_AUTHORIZED"
_QUARANTINE_COMPONENT = "replication_quarantine"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_STATUS = {
    "FEASIBLE",
    "EVIDENCE_MISSING",
    "REVIEW_REQUIRED",
    "BLOCKED",
    "UNKNOWN",
}
_ALLOWED_LATENCY = {"HOURS", "DAYS", "WEEKS", "MONTHS", "UNKNOWN"}
_FORBIDDEN_IDENTITY_SCHEMES = {"TICKER", "SYMBOL", "CURRENT_TICKER", "NAME"}


class ReplicationReadinessError(ValueError):
    """Fail-closed replication-readiness contract error."""


def _required_text(value: Any, *, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ReplicationReadinessError(f"{field} is required")
    return text


def _status(value: Any, *, field: str) -> str:
    text = _required_text(value, field=field).upper()
    if text not in _ALLOWED_STATUS:
        raise ReplicationReadinessError(f"{field} must be one of {sorted(_ALLOWED_STATUS)}")
    return text


def _hash_or_none(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text == "":
        return None
    if not _HASH_RE.fullmatch(text):
        raise ReplicationReadinessError(f"{field} must be a lowercase SHA-256 digest")
    return text


def _hash_tuple(values: tuple[str, ...], *, field: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for idx, value in enumerate(values):
        digest = _hash_or_none(value, field=f"{field}[{idx}]")
        if digest is None:
            raise ReplicationReadinessError(f"{field}[{idx}] cannot be empty")
        normalized.append(digest)
    if len(normalized) != len(set(normalized)):
        raise ReplicationReadinessError(f"{field} contains duplicate evidence hashes")
    return tuple(normalized)


def _aware_timestamp(value: Any, *, field: str) -> str:
    text = _required_text(value, field=field)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise ReplicationReadinessError(f"{field} must be an ISO-8601 timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReplicationReadinessError(f"{field} must include a UTC offset")
    return text


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _fsync_parent_dir_if_possible(path: Path) -> None:
    if os.name == "nt":
        return
    fd: int | None = None
    try:
        fd = os.open(str(path), os.O_RDONLY)
        os.fsync(fd)
    except OSError:
        return
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


@dataclass(frozen=True, slots=True)
class ReplicationReadinessManifestV1:
    """Outcome-blind independent-replication lead-time record."""

    replication_surface_id: str
    created_at: str
    candidate_provider_id: str
    candidate_source_id: str
    entitlement_status: str
    source_feasibility_status: str
    permanent_identity_status: str
    permanent_identity_scheme: str
    permanent_identity_contract_id: str | None
    permanent_identity_contract_hash: str | None
    pit_vintage_status: str
    pit_vintage_contract_id: str | None
    pit_vintage_contract_hash: str | None
    license_status: str
    retention_status: str
    expected_acquisition_latency_class: str
    entitlement_evidence_hashes: tuple[str, ...] = ()
    license_evidence_hashes: tuple[str, ...] = ()
    source_evidence_hashes: tuple[str, ...] = ()
    quarantine_namespace: str = "replication_quarantine/readiness_v1"
    storage_policy_id: str = "IMMUTABLE_WRITE_ONCE_JSON_V1"
    research_visibility: str = REPLICATION_RESEARCH_VISIBILITY
    replication_outcome_access: str = REPLICATION_OUTCOME_ACCESS_DENIED
    family_specific_acquisition_authority: str = REPLICATION_ACQUISITION_AUTHORITY

    def __post_init__(self) -> None:
        surface = _required_text(self.replication_surface_id, field="replication_surface_id")
        created_at = _aware_timestamp(self.created_at, field="created_at")
        provider = _required_text(self.candidate_provider_id, field="candidate_provider_id")
        source = _required_text(self.candidate_source_id, field="candidate_source_id")
        entitlement = _status(self.entitlement_status, field="entitlement_status")
        source_status = _status(self.source_feasibility_status, field="source_feasibility_status")
        identity_status = _status(self.permanent_identity_status, field="permanent_identity_status")
        identity_scheme = _required_text(self.permanent_identity_scheme, field="permanent_identity_scheme").upper()
        if identity_scheme in _FORBIDDEN_IDENTITY_SCHEMES:
            raise ReplicationReadinessError("ticker/name-only identity cannot be independent-replication authority")
        identity_contract_id = (
            None
            if self.permanent_identity_contract_id is None
            else _required_text(self.permanent_identity_contract_id, field="permanent_identity_contract_id")
        )
        identity_contract_hash = _hash_or_none(
            self.permanent_identity_contract_hash,
            field="permanent_identity_contract_hash",
        )
        pit_status = _status(self.pit_vintage_status, field="pit_vintage_status")
        pit_contract_id = (
            None
            if self.pit_vintage_contract_id is None
            else _required_text(self.pit_vintage_contract_id, field="pit_vintage_contract_id")
        )
        pit_contract_hash = _hash_or_none(
            self.pit_vintage_contract_hash,
            field="pit_vintage_contract_hash",
        )
        license_status = _status(self.license_status, field="license_status")
        retention_status = _status(self.retention_status, field="retention_status")
        latency = _required_text(
            self.expected_acquisition_latency_class,
            field="expected_acquisition_latency_class",
        ).upper()
        if latency not in _ALLOWED_LATENCY:
            raise ReplicationReadinessError(
                f"expected_acquisition_latency_class must be one of {sorted(_ALLOWED_LATENCY)}"
            )
        entitlement_hashes = _hash_tuple(
            tuple(self.entitlement_evidence_hashes),
            field="entitlement_evidence_hashes",
        )
        license_hashes = _hash_tuple(tuple(self.license_evidence_hashes), field="license_evidence_hashes")
        source_hashes = _hash_tuple(tuple(self.source_evidence_hashes), field="source_evidence_hashes")
        quarantine_namespace = _required_text(self.quarantine_namespace, field="quarantine_namespace")
        normalized_namespace = quarantine_namespace.replace("\\", "/").strip("/")
        if not normalized_namespace.startswith(f"{_QUARANTINE_COMPONENT}/"):
            raise ReplicationReadinessError("quarantine_namespace must live under replication_quarantine/")
        storage_policy_id = _required_text(self.storage_policy_id, field="storage_policy_id")
        research_visibility = _required_text(self.research_visibility, field="research_visibility").upper()
        if research_visibility != REPLICATION_RESEARCH_VISIBILITY:
            raise ReplicationReadinessError(
                f"research_visibility must remain {REPLICATION_RESEARCH_VISIBILITY}"
            )
        outcome_access = _required_text(
            self.replication_outcome_access,
            field="replication_outcome_access",
        ).upper()
        if outcome_access != REPLICATION_OUTCOME_ACCESS_DENIED:
            raise ReplicationReadinessError("replication outcome access must remain DENIED")
        acquisition_authority = _required_text(
            self.family_specific_acquisition_authority,
            field="family_specific_acquisition_authority",
        ).upper()
        if acquisition_authority != REPLICATION_ACQUISITION_AUTHORITY:
            raise ReplicationReadinessError("family-specific replication acquisition is not authorized by readiness")

        if identity_status == "FEASIBLE" and (identity_contract_id is None or identity_contract_hash is None):
            raise ReplicationReadinessError("FEASIBLE permanent identity requires a hash-bound identity contract")
        if pit_status == "FEASIBLE" and (pit_contract_id is None or pit_contract_hash is None):
            raise ReplicationReadinessError("FEASIBLE PIT/vintage requires a hash-bound PIT contract")
        if entitlement == "FEASIBLE" and not entitlement_hashes:
            raise ReplicationReadinessError("FEASIBLE entitlement requires non-secret evidence hashes")
        if source_status == "FEASIBLE" and not source_hashes:
            raise ReplicationReadinessError("FEASIBLE source requires source-feasibility evidence hashes")
        if (license_status == "FEASIBLE" or retention_status == "FEASIBLE") and not license_hashes:
            raise ReplicationReadinessError("FEASIBLE license/retention requires evidence hashes")

        object.__setattr__(self, "replication_surface_id", surface)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "candidate_provider_id", provider)
        object.__setattr__(self, "candidate_source_id", source)
        object.__setattr__(self, "entitlement_status", entitlement)
        object.__setattr__(self, "source_feasibility_status", source_status)
        object.__setattr__(self, "permanent_identity_status", identity_status)
        object.__setattr__(self, "permanent_identity_scheme", identity_scheme)
        object.__setattr__(self, "permanent_identity_contract_id", identity_contract_id)
        object.__setattr__(self, "permanent_identity_contract_hash", identity_contract_hash)
        object.__setattr__(self, "pit_vintage_status", pit_status)
        object.__setattr__(self, "pit_vintage_contract_id", pit_contract_id)
        object.__setattr__(self, "pit_vintage_contract_hash", pit_contract_hash)
        object.__setattr__(self, "license_status", license_status)
        object.__setattr__(self, "retention_status", retention_status)
        object.__setattr__(self, "expected_acquisition_latency_class", latency)
        object.__setattr__(self, "entitlement_evidence_hashes", entitlement_hashes)
        object.__setattr__(self, "license_evidence_hashes", license_hashes)
        object.__setattr__(self, "source_evidence_hashes", source_hashes)
        object.__setattr__(self, "quarantine_namespace", normalized_namespace)
        object.__setattr__(self, "storage_policy_id", storage_policy_id)
        object.__setattr__(self, "research_visibility", research_visibility)
        object.__setattr__(self, "replication_outcome_access", outcome_access)
        object.__setattr__(self, "family_specific_acquisition_authority", acquisition_authority)

    @property
    def readiness_status(self) -> str:
        statuses = {
            self.entitlement_status,
            self.source_feasibility_status,
            self.permanent_identity_status,
            self.pit_vintage_status,
            self.license_status,
            self.retention_status,
        }
        if "BLOCKED" in statuses:
            return "BLOCKED"
        if statuses == {"FEASIBLE"} and self.expected_acquisition_latency_class != "UNKNOWN":
            return "READY_FOR_FAMILY_SPECIFIC_PREREGISTRATION"
        return "NOT_READY"

    def authority_body(self) -> dict[str, Any]:
        return {
            "schema": REPLICATION_READINESS_SCHEMA,
            "replication_surface_id": self.replication_surface_id,
            "created_at": self.created_at,
            "candidate_provider_id": self.candidate_provider_id,
            "candidate_source_id": self.candidate_source_id,
            "entitlement_status": self.entitlement_status,
            "source_feasibility_status": self.source_feasibility_status,
            "permanent_identity_status": self.permanent_identity_status,
            "permanent_identity_scheme": self.permanent_identity_scheme,
            "permanent_identity_contract_id": self.permanent_identity_contract_id,
            "permanent_identity_contract_hash": self.permanent_identity_contract_hash,
            "pit_vintage_status": self.pit_vintage_status,
            "pit_vintage_contract_id": self.pit_vintage_contract_id,
            "pit_vintage_contract_hash": self.pit_vintage_contract_hash,
            "license_status": self.license_status,
            "retention_status": self.retention_status,
            "expected_acquisition_latency_class": self.expected_acquisition_latency_class,
            "entitlement_evidence_hashes": list(self.entitlement_evidence_hashes),
            "license_evidence_hashes": list(self.license_evidence_hashes),
            "source_evidence_hashes": list(self.source_evidence_hashes),
            "quarantine_namespace": self.quarantine_namespace,
            "storage_policy_id": self.storage_policy_id,
            "research_visibility": self.research_visibility,
            "replication_outcome_access": self.replication_outcome_access,
            "family_specific_acquisition_authority": self.family_specific_acquisition_authority,
            "readiness_status": self.readiness_status,
            "financial_alpha_evidence": 0,
        }

    @property
    def manifest_hash(self) -> str:
        return _content_hash(self.authority_body())

    def to_dict(self) -> dict[str, Any]:
        return {**self.authority_body(), "manifest_hash": self.manifest_hash}


def write_manifest_once(path: str | Path, manifest: ReplicationReadinessManifestV1) -> Path:
    """Write one manifest immutably under a replication_quarantine path.

    The function never opens a provider, never reads credentials, and refuses to
    overwrite prior readiness custody.
    """

    if not isinstance(manifest, ReplicationReadinessManifestV1):
        raise ReplicationReadinessError("manifest must be ReplicationReadinessManifestV1")
    target = Path(path)
    normalized_parts = [part.lower() for part in target.parts]
    if _QUARANTINE_COMPONENT not in normalized_parts:
        raise ReplicationReadinessError("replication readiness artifacts must be stored under replication_quarantine")
    if target.suffix.lower() != ".json":
        raise ReplicationReadinessError("replication readiness manifest path must end in .json")
    if target.exists():
        raise FileExistsError(f"replication readiness manifest is immutable: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_bytes(manifest.to_dict()) + b"\n"
    temp_path = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    if temp_path.exists():
        raise FileExistsError(f"temporary manifest path already exists: {temp_path}")
    try:
        fd = os.open(str(temp_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(str(temp_path), str(target))
        _fsync_parent_dir_if_possible(target.parent)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return target
