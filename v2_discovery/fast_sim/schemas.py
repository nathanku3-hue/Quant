from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from data.provenance import SOURCE_QUALITIES
from data.provenance import SOURCE_QUALITY_CANONICAL


PROXY_SCHEMA_VERSION = "1.0.0"
PROXY_ENGINE_NAME = "v2_proxy"
V1_CANONICAL_ENGINE_NAME = "core.engine.run_simulation"


class ProxyBoundaryError(RuntimeError):
    """Raised when the V2 proxy boundary is violated."""


class ProxyRunStatus(StrEnum):
    CREATED = "created"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ProxyBoundaryVerdict(StrEnum):
    BLOCKED_FROM_PROMOTION = "blocked_from_promotion"
    TIER2_BLOCKED = "tier2_blocked"
    V1_CANONICAL_REQUIRED = "v1_canonical_required"


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
        raise ProxyBoundaryError(f"{field} is required")
    return text


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise ProxyBoundaryError(f"{field} must be a non-empty mapping")
    payload = dict(value)
    _require_json_finite(payload, field)
    return MappingProxyType(payload)


def _require_json_finite(value: Any, field: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            value_class = "nan"
        elif value > 0:
            value_class = "+inf"
        else:
            value_class = "-inf"
        raise ProxyBoundaryError(
            f"{field} contains non-finite numeric value; bad value class: {value_class}"
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require_json_finite(item, f"{field}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _require_json_finite(item, f"{field}[{index}]")
        return
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProxyBoundaryError(f"{field} must be strict JSON serializable") from exc


def _normalize_source_quality(value: Any) -> str:
    quality = _require_text(value, "source_quality").lower()
    if quality not in SOURCE_QUALITIES:
        raise ProxyBoundaryError(f"Invalid source_quality: {value!r}")
    return quality


def _normalize_status(value: Any) -> ProxyRunStatus:
    try:
        return value if isinstance(value, ProxyRunStatus) else ProxyRunStatus(str(value))
    except ValueError as exc:
        raise ProxyBoundaryError(f"Invalid proxy run status: {value!r}") from exc


def _normalize_verdict(value: Any) -> ProxyBoundaryVerdict:
    try:
        return (
            value
            if isinstance(value, ProxyBoundaryVerdict)
            else ProxyBoundaryVerdict(str(value))
        )
    except ValueError as exc:
        raise ProxyBoundaryError(f"Invalid proxy boundary verdict: {value!r}") from exc


@dataclass(frozen=True)
class ProxyRunSpec:
    proxy_run_id: str
    candidate_id: str
    registry_event_id: str
    manifest_uri: str
    source_quality: str
    data_snapshot: Mapping[str, Any]
    code_ref: str
    engine_version: str
    cost_model: Mapping[str, Any]
    train_window: Mapping[str, Any]
    test_window: Mapping[str, Any]
    created_at: str
    engine_name: str = PROXY_ENGINE_NAME
    promotion_ready: bool = False
    canonical_engine_required: bool = True
    status: ProxyRunStatus = ProxyRunStatus.CREATED
    schema_version: str = PROXY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "proxy_run_id", _require_text(self.proxy_run_id, "proxy_run_id"))
        object.__setattr__(self, "candidate_id", _require_text(self.candidate_id, "candidate_id"))
        object.__setattr__(
            self,
            "registry_event_id",
            _require_text(self.registry_event_id, "registry_event_id"),
        )
        object.__setattr__(self, "manifest_uri", _require_text(self.manifest_uri, "manifest_uri"))
        object.__setattr__(
            self,
            "source_quality",
            _normalize_source_quality(self.source_quality),
        )
        object.__setattr__(self, "data_snapshot", _require_mapping(self.data_snapshot, "data_snapshot"))
        object.__setattr__(self, "code_ref", _require_text(self.code_ref, "code_ref"))
        object.__setattr__(self, "engine_version", _require_text(self.engine_version, "engine_version"))
        object.__setattr__(self, "cost_model", _require_mapping(self.cost_model, "cost_model"))
        object.__setattr__(self, "train_window", _require_mapping(self.train_window, "train_window"))
        object.__setattr__(self, "test_window", _require_mapping(self.test_window, "test_window"))
        object.__setattr__(self, "created_at", _require_text(self.created_at, "created_at"))
        object.__setattr__(self, "engine_name", _require_text(self.engine_name, "engine_name"))
        if self.engine_name != PROXY_ENGINE_NAME:
            raise ProxyBoundaryError("ProxyRunSpec engine_name must be v2_proxy")
        if self.promotion_ready:
            raise ProxyBoundaryError("V2 proxy runs cannot be promotion_ready")
        object.__setattr__(self, "promotion_ready", False)
        if not self.canonical_engine_required:
            raise ProxyBoundaryError("V2 proxy runs require a future canonical engine rerun")
        object.__setattr__(self, "canonical_engine_required", True)
        object.__setattr__(self, "status", _normalize_status(self.status))
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proxy_run_id": self.proxy_run_id,
            "candidate_id": self.candidate_id,
            "registry_event_id": self.registry_event_id,
            "manifest_uri": self.manifest_uri,
            "source_quality": self.source_quality,
            "data_snapshot": dict(self.data_snapshot),
            "code_ref": self.code_ref,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "cost_model": dict(self.cost_model),
            "train_window": dict(self.train_window),
            "test_window": dict(self.test_window),
            "created_at": self.created_at,
            "promotion_ready": False,
            "canonical_engine_required": True,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class ProxyRunResult:
    proxy_run_id: str
    candidate_id: str
    registry_event_id: str
    manifest_uri: str
    source_quality: str
    data_snapshot: Mapping[str, Any]
    code_ref: str
    engine_version: str
    cost_model: Mapping[str, Any]
    train_window: Mapping[str, Any]
    test_window: Mapping[str, Any]
    created_at: str
    status: ProxyRunStatus
    boundary_verdict: ProxyBoundaryVerdict
    registry_note_event_id: str
    engine_name: str = PROXY_ENGINE_NAME
    promotion_ready: bool = False
    canonical_engine_required: bool = True
    schema_version: str = PROXY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "proxy_run_id", _require_text(self.proxy_run_id, "proxy_run_id"))
        object.__setattr__(self, "candidate_id", _require_text(self.candidate_id, "candidate_id"))
        object.__setattr__(
            self,
            "registry_event_id",
            _require_text(self.registry_event_id, "registry_event_id"),
        )
        object.__setattr__(self, "manifest_uri", _require_text(self.manifest_uri, "manifest_uri"))
        object.__setattr__(
            self,
            "source_quality",
            _normalize_source_quality(self.source_quality),
        )
        object.__setattr__(self, "data_snapshot", _require_mapping(self.data_snapshot, "data_snapshot"))
        object.__setattr__(self, "code_ref", _require_text(self.code_ref, "code_ref"))
        object.__setattr__(self, "engine_version", _require_text(self.engine_version, "engine_version"))
        object.__setattr__(self, "cost_model", _require_mapping(self.cost_model, "cost_model"))
        object.__setattr__(self, "train_window", _require_mapping(self.train_window, "train_window"))
        object.__setattr__(self, "test_window", _require_mapping(self.test_window, "test_window"))
        object.__setattr__(self, "created_at", _require_text(self.created_at, "created_at"))
        object.__setattr__(self, "status", _normalize_status(self.status))
        object.__setattr__(self, "boundary_verdict", _normalize_verdict(self.boundary_verdict))
        object.__setattr__(
            self,
            "registry_note_event_id",
            _require_text(self.registry_note_event_id, "registry_note_event_id"),
        )
        object.__setattr__(self, "engine_name", _require_text(self.engine_name, "engine_name"))
        if self.engine_name != PROXY_ENGINE_NAME:
            raise ProxyBoundaryError("ProxyRunResult engine_name must be v2_proxy")
        if self.promotion_ready:
            raise ProxyBoundaryError("V2 proxy results cannot be promotion_ready")
        object.__setattr__(self, "promotion_ready", False)
        if not self.canonical_engine_required:
            raise ProxyBoundaryError("V2 proxy results require a future canonical engine rerun")
        object.__setattr__(self, "canonical_engine_required", True)
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )

    @classmethod
    def from_spec(
        cls,
        spec: ProxyRunSpec,
        *,
        status: ProxyRunStatus,
        boundary_verdict: ProxyBoundaryVerdict,
        registry_note_event_id: str,
    ) -> ProxyRunResult:
        return cls(
            **{
                **spec.to_dict(),
                "status": status,
                "boundary_verdict": boundary_verdict,
                "registry_note_event_id": registry_note_event_id,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **ProxyRunSpec(
                proxy_run_id=self.proxy_run_id,
                candidate_id=self.candidate_id,
                registry_event_id=self.registry_event_id,
                manifest_uri=self.manifest_uri,
                source_quality=self.source_quality,
                data_snapshot=self.data_snapshot,
                code_ref=self.code_ref,
                engine_name=self.engine_name,
                engine_version=self.engine_version,
                cost_model=self.cost_model,
                train_window=self.train_window,
                test_window=self.test_window,
                created_at=self.created_at,
                promotion_ready=False,
                canonical_engine_required=True,
                status=self.status,
                schema_version=self.schema_version,
            ).to_dict(),
            "boundary_verdict": self.boundary_verdict.value,
            "registry_note_event_id": self.registry_note_event_id,
        }


@dataclass(frozen=True)
class PromotionPacketDraft:
    candidate_id: str
    source_quality: str
    manifest_uri: str
    canonical_engine_name: str
    canonical_result_ref: str
    created_at: str
    promotion_ready: bool = False
    canonical_engine_required: bool = True
    schema_version: str = PROXY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_text(self.candidate_id, "candidate_id"))
        object.__setattr__(
            self,
            "source_quality",
            _normalize_source_quality(self.source_quality),
        )
        if self.source_quality != SOURCE_QUALITY_CANONICAL:
            raise ProxyBoundaryError("PromotionPacketDraft requires canonical source_quality")
        object.__setattr__(self, "manifest_uri", _require_text(self.manifest_uri, "manifest_uri"))
        object.__setattr__(
            self,
            "canonical_engine_name",
            _require_text(self.canonical_engine_name, "canonical_engine_name"),
        )
        if self.canonical_engine_name != V1_CANONICAL_ENGINE_NAME:
            raise ProxyBoundaryError("PromotionPacketDraft requires V1 canonical engine rerun")
        object.__setattr__(
            self,
            "canonical_result_ref",
            _require_text(self.canonical_result_ref, "canonical_result_ref"),
        )
        object.__setattr__(self, "created_at", _require_text(self.created_at, "created_at"))
        if self.promotion_ready:
            raise ProxyBoundaryError("Phase G0 drafts are not promotion-ready")
        object.__setattr__(self, "promotion_ready", False)
        if not self.canonical_engine_required:
            raise ProxyBoundaryError("PromotionPacketDraft must require canonical engine evidence")
        object.__setattr__(self, "canonical_engine_required", True)
