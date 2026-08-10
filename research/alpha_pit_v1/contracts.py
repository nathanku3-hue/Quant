"""Frozen schemas and validation primitives for alpha_pit_data_api_v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import assert_sha256
from research.aov0.contracts import normalize_security_id


API_SCHEMA_ID = "alpha_pit_data_api_v1"
FAMILY_ID = "CYCLE_RESONANCE_v1"
RISK_SET_SPEC_ID = "CRV1_US_PRIMARY_COMMON_V1"
PRIMARY_LABEL_SPEC_ID = "CRV1_RIGHT_TAIL_252D_TOP5_V1"

OBSERVATION_FIELDS = (
    "market.close",
    "market.total_return_1d",
    "market.volume",
    "market.adv20",
    "market.realized_vol20",
    "market.sma20",
    "market.sma200",
    "fund.revenue_q",
    "fund.inventory_q",
    "fund.capex_q",
    "fund.gross_margin_q",
    "fund.operating_margin_q",
    "fund.cash_from_ops_q",
)
EXPECTATION_MEASURES = (
    "EPS_FY1",
    "EPS_FY2",
    "REVENUE_FY1",
    "REVENUE_FY2",
    "EPS_FY1_REVISION_30D",
    "EPS_FY1_REVISION_90D",
    "REVENUE_FY1_REVISION_30D",
    "REVENUE_FY1_REVISION_90D",
    "FORWARD_PE",
)
CLAIM_TOPICS = (
    "SUPPLY_CAPACITY",
    "INVENTORY_CHANNEL",
    "PRICING",
    "DEMAND",
    "UTILIZATION",
    "MARGIN",
    "GUIDANCE",
    "COMPETITION",
    "OTHER_RELEVANT_CYCLE",
)

# Versioned aliases consumed by the frozen CRV1 contract. Keep the original
# names exported for the narrow API surface; these aliases prevent consumer
# code from inventing a second field namespace.
FIELD_IDS_V1 = OBSERVATION_FIELDS
EXPECTATION_MEASURES_V1 = EXPECTATION_MEASURES
OBSERVATION_COVERAGE_STATUSES = (
    "PRESENT",
    "MISSING_HISTORY",
    "MISSING_SOURCE",
    "NOT_ENTITLED",
    "NOT_APPLICABLE",
    "STALE",
)
OUTCOME_COVERAGE_STATUSES = (
    "PRESENT",
    "INCOMPLETE_HORIZON",
    "MISSING_SOURCE",
    "DELISTING_UNRESOLVED",
    "OTHER_MISSING",
)


class AlphaPITContractError(ValueError):
    """Fail-closed Alpha PIT contract violation."""


class ResearchMode(str, Enum):
    DISCOVERY = "DISCOVERY"
    CONFIRMATORY = "CONFIRMATORY"
    PROSPECTIVE = "PROSPECTIVE"


@dataclass(frozen=True)
class ArtifactRef:
    artifact_type: str
    manifest_sha256: str
    payload_sha256: str
    manifest: Mapping[str, Any]
    payload: Any

    def __post_init__(self) -> None:
        assert_sha256(self.manifest_sha256)
        assert_sha256(self.payload_sha256)


class AlphaPITBackendV1:
    """Narrow backend contract; explicit adapters or fixtures implement this seam."""

    def risk_set(self, *, as_of: datetime, research_mode: ResearchMode) -> ArtifactRef:
        raise NotImplementedError

    def observations(
        self,
        *,
        ids: Sequence[str],
        fields: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        raise NotImplementedError

    def source_claims(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        raise NotImplementedError

    def expectations(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        raise NotImplementedError

    def outcomes(self, *, risk_set_id: str, label_spec_id: str) -> ArtifactRef:
        raise NotImplementedError


def utc_datetime(value: datetime, *, field: str = "as_of") -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"alpha_pit_{field}_datetime_required")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"alpha_pit_{field}_timezone_required")
    return value.astimezone(timezone.utc)


def validate_security_ids(ids: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(normalize_security_id(value) for value in ids)
    if len(set(normalized)) != len(normalized):
        raise ValueError("alpha_pit_duplicate_security_id")
    return normalized


def validate_observation_fields(fields: Sequence[str]) -> tuple[str, ...]:
    values = tuple(str(value) for value in fields)
    if not values:
        raise ValueError("alpha_pit_observation_fields_required")
    unknown = sorted(set(values) - set(OBSERVATION_FIELDS))
    if unknown:
        raise ValueError("alpha_pit_unknown_observation_field:" + ",".join(unknown))
    if len(set(values)) != len(values):
        raise ValueError("alpha_pit_duplicate_observation_field")
    return values


def require_aware_datetime(value: datetime) -> datetime:
    return utc_datetime(value)


def iso_utc(value: datetime) -> str:
    return utc_datetime(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def require_security_ids(ids: Sequence[str]) -> tuple[str, ...]:
    if not ids:
        raise AlphaPITContractError("alpha_pit_security_ids_required")
    try:
        return validate_security_ids(ids)
    except ValueError as exc:
        raise AlphaPITContractError(str(exc)) from exc


def require_field_ids(fields: Sequence[str]) -> tuple[str, ...]:
    try:
        return validate_observation_fields(fields)
    except ValueError as exc:
        raise AlphaPITContractError(str(exc)) from exc


def validate_available_at(row: Mapping[str, Any], *, as_of: datetime) -> None:
    raw = str(row.get("available_at") or "")
    if not raw:
        raise AlphaPITContractError("alpha_pit_available_at_required")
    try:
        available = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AlphaPITContractError("alpha_pit_available_at_invalid") from exc
    if available.tzinfo is None or available.utcoffset() is None:
        raise AlphaPITContractError("alpha_pit_available_at_timezone_required")
    if available.astimezone(timezone.utc) > utc_datetime(as_of):
        raise AlphaPITContractError("alpha_pit_available_at_after_as_of")


def validate_source_receipt_binding(binding: Mapping[str, Any]) -> None:
    required = {
        "source_id",
        "provider",
        "retrieved_at",
        "observed_range_start",
        "observed_range_end",
        "raw_receipt_path",
        "raw_receipt_sha256",
        "parser_id",
        "parser_sha256",
        "license_scope",
        "retention_class",
    }
    if set(binding) != required:
        raise AlphaPITContractError("alpha_pit_source_receipt_binding_fields_invalid")
    for field in required - {"observed_range_start", "observed_range_end"}:
        if not str(binding.get(field) or "").strip():
            raise AlphaPITContractError(f"alpha_pit_source_receipt_{field}_required")
    try:
        assert_sha256(str(binding["raw_receipt_sha256"]))
        assert_sha256(str(binding["parser_sha256"]))
    except ValueError as exc:
        raise AlphaPITContractError("alpha_pit_source_receipt_hash_invalid") from exc
    try:
        retrieved = datetime.fromisoformat(str(binding["retrieved_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AlphaPITContractError("alpha_pit_source_receipt_retrieved_at_invalid") from exc
    if retrieved.tzinfo is None or retrieved.utcoffset() is None:
        raise AlphaPITContractError("alpha_pit_source_receipt_retrieved_at_timezone_required")


def hash_safe(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, datetime):
        return iso_utc(value)
    if isinstance(value, Mapping):
        return {str(key): hash_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [hash_safe(item) for item in value]
    return value
