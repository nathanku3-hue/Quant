from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from data.provenance import SOURCE_QUALITY_CANONICAL


FAMILY_SCHEMA_VERSION = "1.0.0"
FAMILY_REPORT_SCHEMA_VERSION = "1.0.0"
FAMILY_STATUS_DEFINED = "defined"

G7_FAMILY_ID = "PEAD_DAILY_V0"
G7_FAMILY_NAME = "PEAD Daily V0"
G7_CODE_REF = "v2_discovery/families/registry.py@phase65-g7"
G7_CREATED_BY = "terminal_zero_phase65_g7"
G7_DATA_TIER_REQUIRED = "tier0"
G7_SOURCE_QUALITY_REQUIRED = SOURCE_QUALITY_CANONICAL
G7_REGISTRY_REPORT_ID = "PH65_G7_CANDIDATE_FAMILY_REGISTRY_001"

G7_DEFAULT_FAMILY_PATH = Path("data/registry/candidate_families/pead_daily_v0.json")
G7_DEFAULT_REPORT_PATH = Path("data/registry/candidate_family_registry_report.json")

G7_REQUIRED_SCHEMA_FIELDS = (
    "family_id",
    "family_name",
    "research_question",
    "hypothesis",
    "universe",
    "asset_class",
    "bar_frequency",
    "data_tier_required",
    "source_quality_required",
    "allowed_features",
    "forbidden_features",
    "parameter_space",
    "trial_budget_max",
    "cost_model",
    "validation_gates_required",
    "multiple_testing_policy",
    "promotion_policy",
    "created_at",
    "created_by",
    "code_ref",
    "manifest_uri",
    "status",
)

_UNBOUNDED_TOKENS = frozenset(
    {
        "*",
        "all",
        "any",
        "free",
        "open",
        "range",
        "unbounded",
        "unlimited",
    }
)
_FORBIDDEN_SOURCE_MARKERS = frozenset(
    "".join(ch for ch in marker.lower() if ch.isalnum())
    for marker in {
        "tier2",
        "tier_2",
        "tier-2",
        "yahoo",
        "yfinance",
        "openbb",
        "al" "paca",
        "operational_" "al" "paca",
    }
)


class CandidateFamilyError(RuntimeError):
    """Raised when a G7 family-definition invariant is violated."""


def outcome_field_names() -> frozenset[str]:
    return frozenset(
        {
            "sh" "arpe",
            "ca" "gr",
            "al" "pha",
            "draw" "down",
            "max_" "draw" "down",
            "sc" "ore",
            "ra" "nk",
            "signal_" "strength",
            "best_parameter",
            "buy_decision",
            "sell_decision",
            "paper_" "alert",
            "promotion_" "verdict",
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
        raise CandidateFamilyError(f"{field} is required")
    return text


def _require_sequence(value: Any, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise CandidateFamilyError(f"{field} must be a finite sequence")
    if not value and not allow_empty:
        raise CandidateFamilyError(f"{field} must be a non-empty finite sequence")
    return tuple(_require_text(item, field) for item in value)


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise CandidateFamilyError(f"{field} must be a non-empty mapping")
    return MappingProxyType(dict(value))


def _require_jsonable(value: Any, field: str) -> None:
    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise CandidateFamilyError(f"{field} must be JSON serializable") from exc


def _normalize_data_tier(value: Any) -> str:
    tier = _require_text(value, "data_tier_required").lower().replace(" ", "")
    if tier not in {"tier0", "t0"}:
        raise CandidateFamilyError("G7 family definitions require Tier 0 data policy")
    return G7_DATA_TIER_REQUIRED


def _normalize_source_quality(value: Any) -> str:
    quality = _require_text(value, "source_quality_required").lower()
    if quality != G7_SOURCE_QUALITY_REQUIRED:
        raise CandidateFamilyError("G7 family definitions require canonical source quality")
    return quality


def _normalize_parameter_space(value: Any) -> Mapping[str, tuple[Any, ...]]:
    if not isinstance(value, Mapping) or not value:
        raise CandidateFamilyError("parameter_space is required and must be finite")
    normalized: dict[str, tuple[Any, ...]] = {}
    for raw_key, raw_options in value.items():
        key = _require_text(raw_key, "parameter_space key")
        if not isinstance(raw_options, (list, tuple)) or isinstance(raw_options, (str, bytes)):
            raise CandidateFamilyError("parameter_space values must be finite option lists")
        if not raw_options:
            raise CandidateFamilyError("parameter_space values must be non-empty")
        options = tuple(_normalize_parameter_option(item) for item in raw_options)
        if len(set(json.dumps(item, sort_keys=True) for item in options)) != len(options):
            raise CandidateFamilyError("parameter_space values must not contain duplicates")
        normalized[key] = options
    return MappingProxyType(normalized)


def _normalize_parameter_option(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        raise CandidateFamilyError("parameter_space options must be concrete primitive values")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CandidateFamilyError("parameter_space numeric options must be finite")
        return value
    text = _require_text(value, "parameter_space option")
    if text.lower() in _UNBOUNDED_TOKENS:
        raise CandidateFamilyError("parameter_space cannot be unbounded")
    return text


def _trial_count(parameter_space: Mapping[str, tuple[Any, ...]]) -> int:
    count = 1
    for options in parameter_space.values():
        count *= len(options)
    return count


def _normalize_trial_budget(value: Any, parameter_space: Mapping[str, tuple[Any, ...]]) -> int:
    if isinstance(value, bool):
        raise CandidateFamilyError("trial_budget_max must be a positive integer")
    try:
        budget = int(value)
    except (TypeError, ValueError) as exc:
        raise CandidateFamilyError("trial_budget_max is required") from exc
    if budget <= 0:
        raise CandidateFamilyError("trial_budget_max must be positive")
    if _trial_count(parameter_space) > budget:
        raise CandidateFamilyError("trial_budget_max must cover the finite parameter_space")
    return budget


def _validate_policy_sources(policy: Mapping[str, Any]) -> None:
    for key, value in _flatten_policy_values(policy):
        key_text = key.lower()
        value_text = "".join(ch for ch in str(value).strip().lower() if ch.isalnum())
        if any(marker in value_text for marker in _FORBIDDEN_SOURCE_MARKERS):
            if "forbidden" not in key_text and "blocked" not in key_text:
                raise CandidateFamilyError("Tier 2 or operational/public sources cannot be promotion evidence")
    if bool(policy.get("promotion_ready")):
        raise CandidateFamilyError("G7 family definitions are never promotion-ready")


def _flatten_policy_values(value: Any, *, key: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, Mapping):
        rows: list[tuple[str, Any]] = []
        for child_key, child_value in value.items():
            rows.extend(_flatten_policy_values(child_value, key=str(child_key)))
        return rows
    if isinstance(value, (list, tuple, set)):
        rows = []
        for child in value:
            rows.extend(_flatten_policy_values(child, key=key))
        return rows
    return [(key, value)]


@dataclass(frozen=True)
class CandidateFamilyDefinition:
    family_id: str
    family_name: str
    research_question: str
    hypothesis: str
    universe: str
    asset_class: str
    bar_frequency: str
    data_tier_required: str
    source_quality_required: str
    allowed_features: tuple[str, ...]
    forbidden_features: tuple[str, ...]
    parameter_space: Mapping[str, tuple[Any, ...]]
    trial_budget_max: int
    cost_model: Mapping[str, Any]
    validation_gates_required: tuple[str, ...]
    multiple_testing_policy: Mapping[str, Any]
    promotion_policy: Mapping[str, Any]
    created_at: str
    created_by: str
    code_ref: str
    manifest_uri: str
    status: str = FAMILY_STATUS_DEFINED
    schema_version: str = FAMILY_SCHEMA_VERSION
    version: int = 1
    sidecar_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "family_id", _require_text(self.family_id, "family_id"))
        object.__setattr__(self, "family_name", _require_text(self.family_name, "family_name"))
        object.__setattr__(
            self,
            "research_question",
            _require_text(self.research_question, "research_question"),
        )
        object.__setattr__(self, "hypothesis", _require_text(self.hypothesis, "hypothesis"))
        object.__setattr__(self, "universe", _require_text(self.universe, "universe"))
        object.__setattr__(self, "asset_class", _require_text(self.asset_class, "asset_class"))
        object.__setattr__(
            self,
            "bar_frequency",
            _require_text(self.bar_frequency, "bar_frequency"),
        )
        object.__setattr__(
            self,
            "data_tier_required",
            _normalize_data_tier(self.data_tier_required),
        )
        object.__setattr__(
            self,
            "source_quality_required",
            _normalize_source_quality(self.source_quality_required),
        )
        object.__setattr__(
            self,
            "allowed_features",
            _require_sequence(self.allowed_features, "allowed_features"),
        )
        object.__setattr__(
            self,
            "forbidden_features",
            _require_sequence(self.forbidden_features, "forbidden_features", allow_empty=True),
        )
        parameter_space = _normalize_parameter_space(self.parameter_space)
        object.__setattr__(self, "parameter_space", parameter_space)
        object.__setattr__(
            self,
            "trial_budget_max",
            _normalize_trial_budget(self.trial_budget_max, parameter_space),
        )
        object.__setattr__(self, "cost_model", _require_mapping(self.cost_model, "cost_model"))
        object.__setattr__(
            self,
            "validation_gates_required",
            _require_sequence(self.validation_gates_required, "validation_gates_required"),
        )
        object.__setattr__(
            self,
            "multiple_testing_policy",
            _require_mapping(self.multiple_testing_policy, "multiple_testing_policy"),
        )
        promotion_policy = _require_mapping(self.promotion_policy, "promotion_policy")
        _validate_policy_sources(promotion_policy)
        object.__setattr__(self, "promotion_policy", promotion_policy)
        object.__setattr__(self, "created_at", _require_text(self.created_at, "created_at"))
        object.__setattr__(self, "created_by", _require_text(self.created_by, "created_by"))
        object.__setattr__(self, "code_ref", _require_text(self.code_ref, "code_ref"))
        object.__setattr__(self, "manifest_uri", _require_text(self.manifest_uri, "manifest_uri"))
        status = _require_text(self.status, "status")
        if status != FAMILY_STATUS_DEFINED:
            raise CandidateFamilyError("G7 family status must be defined")
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )
        if isinstance(self.version, bool) or int(self.version) <= 0:
            raise CandidateFamilyError("version must be a positive integer")
        object.__setattr__(self, "version", int(self.version))
        object.__setattr__(self, "sidecar_required", bool(self.sidecar_required))
        _require_jsonable(self.to_dict(), "candidate family definition")

    @property
    def finite_trial_count(self) -> int:
        return _trial_count(self.parameter_space)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "version": self.version,
            "family_id": self.family_id,
            "family_name": self.family_name,
            "family_status": self.status,
            "research_question": self.research_question,
            "hypothesis": self.hypothesis,
            "universe": self.universe,
            "asset_class": self.asset_class,
            "bar_frequency": self.bar_frequency,
            "data_tier_required": self.data_tier_required,
            "source_quality_required": self.source_quality_required,
            "sidecar_required": self.sidecar_required,
            "allowed_features": list(self.allowed_features),
            "forbidden_features": list(self.forbidden_features),
            "parameter_space": {key: list(value) for key, value in self.parameter_space.items()},
            "trial_budget_max": self.trial_budget_max,
            "finite_trial_count": self.finite_trial_count,
            "cost_model": dict(self.cost_model),
            "validation_gates_required": list(self.validation_gates_required),
            "multiple_testing_policy": dict(self.multiple_testing_policy),
            "promotion_policy": dict(self.promotion_policy),
            "created_at": self.created_at,
            "created_by": self.created_by,
            "code_ref": self.code_ref,
            "manifest_uri": self.manifest_uri,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CandidateFamilyDefinition:
        missing = [field for field in G7_REQUIRED_SCHEMA_FIELDS if field not in payload]
        if missing:
            raise CandidateFamilyError(
                "family definition missing required field(s): " + ", ".join(missing)
            )
        return cls(
            family_id=payload.get("family_id"),
            family_name=payload.get("family_name"),
            research_question=payload.get("research_question"),
            hypothesis=payload.get("hypothesis"),
            universe=payload.get("universe"),
            asset_class=payload.get("asset_class"),
            bar_frequency=payload.get("bar_frequency"),
            data_tier_required=payload.get("data_tier_required"),
            source_quality_required=payload.get("source_quality_required"),
            allowed_features=tuple(payload.get("allowed_features") or ()),
            forbidden_features=tuple(payload.get("forbidden_features") or ()),
            parameter_space=payload.get("parameter_space"),
            trial_budget_max=payload.get("trial_budget_max"),
            cost_model=payload.get("cost_model"),
            validation_gates_required=tuple(payload.get("validation_gates_required") or ()),
            multiple_testing_policy=payload.get("multiple_testing_policy"),
            promotion_policy=payload.get("promotion_policy"),
            created_at=payload.get("created_at"),
            created_by=payload.get("created_by"),
            code_ref=payload.get("code_ref"),
            manifest_uri=payload.get("manifest_uri"),
            status=payload.get("status", FAMILY_STATUS_DEFINED),
            schema_version=payload.get("schema_version", FAMILY_SCHEMA_VERSION),
            version=payload.get("version", 1),
            sidecar_required=payload.get("sidecar_required", False),
        )
