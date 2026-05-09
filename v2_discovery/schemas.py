from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from data.provenance import SOURCE_QUALITIES
from data.provenance import utc_now_iso


CANDIDATE_SCHEMA_VERSION = "1.0.0"
EVENT_SCHEMA_VERSION = "1.0.0"
GENESIS_EVENT_HASH = "GENESIS"


class CandidateRegistryError(RuntimeError):
    """Raised when candidate registry policy is violated."""


class CandidateStatus(StrEnum):
    GENERATED = "generated"
    INCUBATING = "incubating"
    REJECTED = "rejected"
    RETIRED = "retired"
    QUARANTINED = "quarantined"
    PROMOTED = "promoted"
    ALERTED = "alerted"
    EXECUTED = "executed"


ALLOWED_PHASE_F_STATUSES = frozenset(
    {
        CandidateStatus.GENERATED,
        CandidateStatus.INCUBATING,
        CandidateStatus.REJECTED,
        CandidateStatus.RETIRED,
        CandidateStatus.QUARANTINED,
    }
)

FORBIDDEN_PHASE_F_STATUSES = frozenset(
    {
        CandidateStatus.PROMOTED,
        CandidateStatus.ALERTED,
        CandidateStatus.EXECUTED,
    }
)

ALLOWED_STATUS_TRANSITIONS = {
    CandidateStatus.GENERATED: frozenset(
        {
            CandidateStatus.INCUBATING,
            CandidateStatus.REJECTED,
            CandidateStatus.RETIRED,
            CandidateStatus.QUARANTINED,
        }
    ),
    CandidateStatus.INCUBATING: frozenset({CandidateStatus.REJECTED}),
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
        raise CandidateRegistryError(f"{field} is required")
    return text


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise CandidateRegistryError(f"{field} must be a non-empty mapping")
    return MappingProxyType(dict(value))


def _require_sequence(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise CandidateRegistryError(f"{field} must be a non-empty sequence")
    cleaned = tuple(_require_text(item, field) for item in value)
    return cleaned


def _require_jsonable(value: Any, field: str) -> None:
    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise CandidateRegistryError(f"{field} must be JSON serializable") from exc


def _normalize_status(value: Any) -> CandidateStatus:
    try:
        return value if isinstance(value, CandidateStatus) else CandidateStatus(str(value))
    except ValueError as exc:
        raise CandidateRegistryError(f"Invalid candidate status: {value!r}") from exc


def _normalize_source_quality(value: Any) -> str:
    quality = _require_text(value, "source_quality").lower()
    if quality not in SOURCE_QUALITIES:
        raise CandidateRegistryError(f"Invalid source_quality: {value!r}")
    return quality


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_event_hash(event_without_hash: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(event_without_hash).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    family_id: str
    hypothesis: str
    universe: str
    features: tuple[str, ...]
    parameters_searched: Mapping[str, Any]
    trial_count: int
    train_window: Mapping[str, Any]
    test_window: Mapping[str, Any]
    cost_model: Mapping[str, Any]
    data_snapshot: Mapping[str, Any]
    manifest_uri: str
    source_quality: str
    created_at: str
    created_by: str
    code_ref: str
    status: CandidateStatus = CandidateStatus.GENERATED
    schema_version: str = CANDIDATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_text(self.candidate_id, "candidate_id"))
        object.__setattr__(self, "family_id", _require_text(self.family_id, "family_id"))
        object.__setattr__(self, "hypothesis", _require_text(self.hypothesis, "hypothesis"))
        object.__setattr__(self, "universe", _require_text(self.universe, "universe"))
        object.__setattr__(self, "features", _require_sequence(self.features, "features"))
        object.__setattr__(
            self,
            "parameters_searched",
            _require_mapping(self.parameters_searched, "parameters_searched"),
        )
        if isinstance(self.trial_count, bool):
            raise CandidateRegistryError("trial_count must be an integer")
        try:
            trial_count = int(self.trial_count)
        except (TypeError, ValueError) as exc:
            raise CandidateRegistryError("trial_count must be an integer") from exc
        if trial_count < 0:
            raise CandidateRegistryError("trial_count must be non-negative")
        object.__setattr__(self, "trial_count", trial_count)
        object.__setattr__(self, "train_window", _require_mapping(self.train_window, "train_window"))
        object.__setattr__(self, "test_window", _require_mapping(self.test_window, "test_window"))
        object.__setattr__(self, "cost_model", _require_mapping(self.cost_model, "cost_model"))
        object.__setattr__(self, "data_snapshot", _require_mapping(self.data_snapshot, "data_snapshot"))
        object.__setattr__(self, "manifest_uri", _require_text(self.manifest_uri, "manifest_uri"))
        object.__setattr__(
            self,
            "source_quality",
            _normalize_source_quality(self.source_quality),
        )
        object.__setattr__(self, "created_at", _require_text(self.created_at, "created_at"))
        object.__setattr__(self, "created_by", _require_text(self.created_by, "created_by"))
        object.__setattr__(self, "code_ref", _require_text(self.code_ref, "code_ref"))
        status = _normalize_status(self.status)
        if status in FORBIDDEN_PHASE_F_STATUSES:
            raise CandidateRegistryError(f"status {status.value!r} is forbidden in Phase F")
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )
        _require_jsonable(self.to_dict(), "candidate spec")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "family_id": self.family_id,
            "hypothesis": self.hypothesis,
            "universe": self.universe,
            "features": list(self.features),
            "parameters_searched": dict(self.parameters_searched),
            "trial_count": self.trial_count,
            "train_window": dict(self.train_window),
            "test_window": dict(self.test_window),
            "cost_model": dict(self.cost_model),
            "data_snapshot": dict(self.data_snapshot),
            "manifest_uri": self.manifest_uri,
            "source_quality": self.source_quality,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "code_ref": self.code_ref,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CandidateSpec:
        return cls(
            candidate_id=payload.get("candidate_id"),
            family_id=payload.get("family_id"),
            hypothesis=payload.get("hypothesis"),
            universe=payload.get("universe"),
            features=payload.get("features"),
            parameters_searched=payload.get("parameters_searched"),
            trial_count=payload.get("trial_count"),
            train_window=payload.get("train_window"),
            test_window=payload.get("test_window"),
            cost_model=payload.get("cost_model"),
            data_snapshot=payload.get("data_snapshot"),
            manifest_uri=payload.get("manifest_uri"),
            source_quality=payload.get("source_quality"),
            created_at=payload.get("created_at"),
            created_by=payload.get("created_by"),
            code_ref=payload.get("code_ref"),
            status=payload.get("status", CandidateStatus.GENERATED.value),
            schema_version=payload.get("schema_version", CANDIDATE_SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class CandidateEvent:
    event_id: str
    candidate_id: str
    event_type: str
    created_at: str
    actor: str
    payload: Mapping[str, Any]
    previous_event_hash: str
    event_hash: str
    schema_version: str = EVENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text(self.event_id, "event_id"))
        object.__setattr__(self, "candidate_id", _require_text(self.candidate_id, "candidate_id"))
        object.__setattr__(self, "event_type", _require_text(self.event_type, "event_type"))
        object.__setattr__(self, "created_at", _require_text(self.created_at, "created_at"))
        object.__setattr__(self, "actor", _require_text(self.actor, "actor"))
        object.__setattr__(self, "payload", _require_mapping(self.payload, "payload"))
        object.__setattr__(
            self,
            "previous_event_hash",
            _require_text(self.previous_event_hash, "previous_event_hash"),
        )
        object.__setattr__(self, "event_hash", _require_text(self.event_hash, "event_hash"))
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )
        _require_jsonable(self.to_dict(), "candidate event")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "candidate_id": self.candidate_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "actor": self.actor,
            "payload": dict(self.payload),
            "previous_event_hash": self.previous_event_hash,
        }
        if include_hash:
            payload["event_hash"] = self.event_hash
        return payload

    def recompute_hash(self) -> str:
        return compute_event_hash(self.to_dict(include_hash=False))

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        candidate_id: str,
        event_type: str,
        actor: str,
        payload: Mapping[str, Any],
        previous_event_hash: str,
        created_at: str | None = None,
    ) -> CandidateEvent:
        body = {
            "schema_version": EVENT_SCHEMA_VERSION,
            "event_id": event_id,
            "candidate_id": candidate_id,
            "event_type": event_type,
            "created_at": created_at or utc_now_iso(),
            "actor": actor,
            "payload": dict(payload),
            "previous_event_hash": previous_event_hash,
        }
        return cls(event_hash=compute_event_hash(body), **body)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CandidateEvent:
        return cls(
            schema_version=payload.get("schema_version", EVENT_SCHEMA_VERSION),
            event_id=payload.get("event_id"),
            candidate_id=payload.get("candidate_id"),
            event_type=payload.get("event_type"),
            created_at=payload.get("created_at"),
            actor=payload.get("actor"),
            payload=payload.get("payload"),
            previous_event_hash=payload.get("previous_event_hash"),
            event_hash=payload.get("event_hash"),
        )


@dataclass(frozen=True)
class CandidateSnapshot:
    candidate_id: str
    spec: CandidateSpec
    status: CandidateStatus
    event_count: int
    last_event_hash: str
    notes: tuple[Mapping[str, Any], ...] = ()
    promotion_ready: bool = False
    promotion_block_reason: str = "phase_f_registry_only"

    def __post_init__(self) -> None:
        status = _normalize_status(self.status)
        object.__setattr__(self, "status", status)
        if self.spec.source_quality != "canonical":
            object.__setattr__(self, "promotion_block_reason", "non_canonical_source_quality")
        if self.promotion_ready:
            raise CandidateRegistryError("Phase F snapshots cannot be promotion-ready")

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "spec": self.spec.to_dict(),
            "status": self.status.value,
            "event_count": self.event_count,
            "last_event_hash": self.last_event_hash,
            "notes": [dict(note) for note in self.notes],
            "promotion_ready": False,
            "promotion_block_reason": self.promotion_block_reason,
        }
