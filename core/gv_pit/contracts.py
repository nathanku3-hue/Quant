"""Immutable contracts for the read-only all-capital point-in-time episode.

The module owns value contracts and deterministic identity derivation only. It
contains no adapter I/O, lifecycle state, portfolio calculation, or mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, TypeAlias

from core.gv_fs0_canonical import (
    assert_sha256,
    canonical_document_bytes,
    canonical_timestamp,
    domain_hash,
)


PIT_ID_DOMAIN = "GV-PIT:IDENTITY:V1"
NO_MARKET_VALIDATION_DOMAIN = "GV-PIT:NO-MARKET-CASH-ONLY:V1"
NO_MARKET_SOURCE_STATE_DOMAIN = "GV-PIT:NO-MARKET-SOURCE-STATE:V1"
PROPOSAL_ID_DOMAIN = "GV-PIT:CAPITAL-PROPOSAL:V1"
SCHEMA_DIGEST_DOMAIN = "GV-PIT:EXTENSION-SCHEMA:V1"
PAYLOAD_DIGEST_DOMAIN = "GV-PIT:EXTENSION-PAYLOAD:V1"
PORTFOLIO_EVENT_ID_DOMAIN = "GV-PORTFOLIO-V0:EVT:V1"

MAX_CERTIFIED_PREFIX_EVENTS = 256
MAX_CERTIFIED_PREFIX_BYTES = 1_000_000
MAX_CERTIFICATION_BYTES = 64_000
MAX_SOURCE_WORKSPACE_BYTES = 2_000_000

AUTHORITATIVE_PORTFOLIO_EVENT_TYPES = frozenset(
    {
        "CASH_OPENING",
        "POSITION_OPENING",
        "CORPORATE_ACTION_SPLIT",
        "ORDER_CREATED",
        "FILL_COMPLETED",
        "PORTFOLIO_AIM_CONFIRMED",
        "PORTFOLIO_TRANSITION_PLANNED",
    }
)
NON_AUTHORITATIVE_PORTFOLIO_EVENT_TYPES = frozenset(
    {
        "LATER_OBSERVATION_ADMITTED",
        "PROSPECTIVE_PROPOSAL_REJECTED",
        "CERTIFICATION_RECORDED",
        "CORRECTION_RECORDED",
    }
)


class ProposalOutcome(str, Enum):
    ADMIT = "ADMIT"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"
    HOLD_CASH = "HOLD_CASH"


class TargetIntent(str, Enum):
    TARGET_FINAL = "TARGET_FINAL"
    DELTA = "DELTA"
    OVERLAY = "OVERLAY"


class InstrumentUnit(str, Enum):
    QUANTITY = "QUANTITY"
    NOTIONAL = "NOTIONAL"
    WEIGHT = "WEIGHT"


class RiskMeasure(str, Enum):
    VAR = "VAR"
    VOL = "VOL"
    GROSS = "GROSS"
    MARGIN = "MARGIN"
    DELTA = "DELTA"


class RiskUnit(str, Enum):
    BPS = "BPS"
    PERCENT = "PERCENT"
    USD = "USD"
    NOTIONAL = "NOTIONAL"


class RoundingMode(str, Enum):
    EXACT = "EXACT"
    DOWN = "DOWN"
    HALF_EVEN = "HALF_EVEN"


class LotSizePolicy(str, Enum):
    WHOLE_UNITS = "WHOLE_UNITS"
    FRACTIONAL_ALLOWED = "FRACTIONAL_ALLOWED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    evidence_id: str
    sha256_digest: str
    source_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not isinstance(
            self.source_identity, str
        ):
            raise TypeError("EVIDENCE_REFERENCE_TEXT_TYPE_INVALID")
        if not self.evidence_id.strip() or not self.source_identity.strip():
            raise ValueError("EVIDENCE_REFERENCE_IDENTITY_REQUIRED")
        assert_sha256(self.sha256_digest)


@dataclass(frozen=True, slots=True)
class NumericNormalizationPolicy:
    unit_quantum: Decimal
    rounding_mode: RoundingMode
    currency: str
    price_identity: str | None
    contract_multiplier: Decimal | None
    lot_size_policy: LotSizePolicy

    def __post_init__(self) -> None:
        if not isinstance(self.unit_quantum, Decimal):
            raise TypeError("NORMALIZATION_UNIT_QUANTUM_TYPE_INVALID")
        if not isinstance(self.rounding_mode, RoundingMode):
            raise TypeError("NORMALIZATION_ROUNDING_MODE_TYPE_INVALID")
        if not isinstance(self.lot_size_policy, LotSizePolicy):
            raise TypeError("NORMALIZATION_LOT_POLICY_TYPE_INVALID")
        if not self.unit_quantum.is_finite() or self.unit_quantum <= Decimal("0"):
            raise ValueError("NORMALIZATION_UNIT_QUANTUM_POSITIVE_REQUIRED")
        if (
            not isinstance(self.currency, str)
            or len(self.currency) != 3
            or not self.currency.isalpha()
            or self.currency != self.currency.upper()
        ):
            raise ValueError("NORMALIZATION_CURRENCY_CANONICAL_REQUIRED")
        if self.price_identity is not None and (
            not isinstance(self.price_identity, str) or not self.price_identity.strip()
        ):
            raise ValueError("NORMALIZATION_PRICE_IDENTITY_INVALID")
        if self.contract_multiplier is not None and not isinstance(
            self.contract_multiplier, Decimal
        ):
            raise TypeError("NORMALIZATION_MULTIPLIER_TYPE_INVALID")
        if self.contract_multiplier is not None and (
            not self.contract_multiplier.is_finite()
            or self.contract_multiplier <= Decimal("0")
        ):
            raise ValueError("NORMALIZATION_MULTIPLIER_POSITIVE_REQUIRED")


@dataclass(frozen=True, slots=True)
class InstrumentTarget:
    instrument_id: str
    symbol: str
    intent: TargetIntent
    unit: InstrumentUnit
    target_value: Decimal
    normalization: NumericNormalizationPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, str) or not isinstance(self.symbol, str):
            raise TypeError("INSTRUMENT_TARGET_TEXT_TYPE_INVALID")
        if not self.instrument_id.strip() or not self.symbol.strip():
            raise ValueError("INSTRUMENT_TARGET_IDENTITY_REQUIRED")
        if not isinstance(self.intent, TargetIntent):
            raise TypeError("INSTRUMENT_TARGET_INTENT_TYPE_INVALID")
        if not isinstance(self.unit, InstrumentUnit):
            raise TypeError("INSTRUMENT_TARGET_UNIT_TYPE_INVALID")
        if not isinstance(self.target_value, Decimal):
            raise TypeError("INSTRUMENT_TARGET_VALUE_TYPE_INVALID")
        if not isinstance(self.normalization, NumericNormalizationPolicy):
            raise TypeError("INSTRUMENT_TARGET_NORMALIZATION_TYPE_INVALID")
        if not self.target_value.is_finite():
            raise ValueError("INSTRUMENT_TARGET_FINITE_REQUIRED")
        if self.target_value % self.normalization.unit_quantum != Decimal("0"):
            raise ValueError("INSTRUMENT_TARGET_NOT_NORMALIZED_TO_QUANTUM")
        if self.unit is InstrumentUnit.WEIGHT and (
            self.target_value < Decimal("-1") or self.target_value > Decimal("1")
        ):
            raise ValueError("INSTRUMENT_WEIGHT_OUT_OF_RANGE")
        if self.unit is InstrumentUnit.QUANTITY:
            if self.normalization.lot_size_policy is LotSizePolicy.NOT_APPLICABLE:
                raise ValueError("QUANTITY_LOT_POLICY_REQUIRED")
            if self.normalization.lot_size_policy is LotSizePolicy.WHOLE_UNITS and (
                self.normalization.unit_quantum
                != self.normalization.unit_quantum.to_integral_value()
                or self.target_value != self.target_value.to_integral_value()
            ):
                raise ValueError("WHOLE_UNIT_TARGET_NOT_INTEGRAL")
        elif self.normalization.lot_size_policy is not LotSizePolicy.NOT_APPLICABLE:
            raise ValueError("NON_QUANTITY_LOT_POLICY_NOT_APPLICABLE_REQUIRED")


@dataclass(frozen=True, slots=True)
class RiskTarget:
    measure: RiskMeasure
    unit: RiskUnit
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.measure, RiskMeasure):
            raise TypeError("RISK_TARGET_MEASURE_TYPE_INVALID")
        if not isinstance(self.unit, RiskUnit):
            raise TypeError("RISK_TARGET_UNIT_TYPE_INVALID")
        if not isinstance(self.value, Decimal):
            raise TypeError("RISK_TARGET_VALUE_TYPE_INVALID")
        if not self.value.is_finite():
            raise ValueError("RISK_TARGET_FINITE_REQUIRED")


@dataclass(frozen=True, slots=True)
class CashBucketAmount:
    bucket: str
    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.bucket, str):
            raise TypeError("CASH_BUCKET_TYPE_INVALID")
        if not self.bucket.strip():
            raise ValueError("CASH_BUCKET_REQUIRED")
        if not isinstance(self.amount, Decimal):
            raise TypeError("CASH_BUCKET_AMOUNT_TYPE_INVALID")
        if not self.amount.is_finite() or self.amount < Decimal("0"):
            raise ValueError("CASH_BUCKET_NONNEGATIVE_FINITE_REQUIRED")


@dataclass(frozen=True, slots=True)
class EquityFundamentalPayloadV1:
    subject: str
    permanent_key: str
    net_score_bps: int
    missing_discriminator: str

    def __post_init__(self) -> None:
        for field_name in ("subject", "permanent_key", "missing_discriminator"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"EQUITY_PAYLOAD_{field_name.upper()}_REQUIRED")
        if isinstance(self.net_score_bps, bool) or not isinstance(
            self.net_score_bps, int
        ):
            raise TypeError("EQUITY_PAYLOAD_NET_SCORE_BPS_TYPE_INVALID")


@dataclass(frozen=True, slots=True)
class CashBaselinePayloadV1:
    nav: Decimal
    classified_cash: tuple[CashBucketAmount, ...]
    yield_status: str

    def __post_init__(self) -> None:
        if not isinstance(self.nav, Decimal):
            raise TypeError("CASH_PAYLOAD_NAV_TYPE_INVALID")
        if not self.nav.is_finite() or self.nav < Decimal("0"):
            raise ValueError("CASH_PAYLOAD_NAV_NONNEGATIVE_FINITE_REQUIRED")
        if not isinstance(self.classified_cash, tuple) or not all(
            isinstance(row, CashBucketAmount) for row in self.classified_cash
        ):
            raise TypeError("CASH_PAYLOAD_CLASSIFIED_CASH_TYPE_INVALID")
        buckets = tuple(row.bucket for row in self.classified_cash)
        if len(set(buckets)) != len(buckets):
            raise ValueError("CASH_PAYLOAD_DUPLICATE_BUCKET")
        if sum(
            (row.amount for row in self.classified_cash), start=Decimal("0")
        ) != self.nav:
            raise ValueError("CASH_PAYLOAD_CLASSIFIED_CASH_NAV_MISMATCH")
        if not isinstance(self.yield_status, str) or not self.yield_status.strip():
            raise ValueError("CASH_PAYLOAD_YIELD_STATUS_REQUIRED")


@dataclass(frozen=True, slots=True)
class EquityFundamentalExtensionV1:
    schema_id: str
    schema_version: str
    schema_digest: str
    canonical_payload_digest: str
    payload: EquityFundamentalPayloadV1

    def __post_init__(self) -> None:
        validate_extension_envelope(self)


@dataclass(frozen=True, slots=True)
class CashBaselineExtensionV1:
    schema_id: str
    schema_version: str
    schema_digest: str
    canonical_payload_digest: str
    payload: CashBaselinePayloadV1

    def __post_init__(self) -> None:
        validate_extension_envelope(self)


ExtensionEnvelope: TypeAlias = (
    EquityFundamentalExtensionV1 | CashBaselineExtensionV1
)


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CERTIFIED_SOURCE_PROOF_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _load_canonical_json(
    value: str,
    *,
    field: str,
    expected_type: type[list[Any]] | type[dict[str, Any]],
) -> list[Any] | dict[str, Any]:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field}_REQUIRED")
    try:
        parsed = json.loads(value, object_pairs_hook=_strict_json_object)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field}_JSON_INVALID") from exc
    if not isinstance(parsed, expected_type):
        raise ValueError(f"{field}_ROOT_TYPE_INVALID")
    if canonical_document_bytes(parsed) != value.encode("utf-8"):
        raise ValueError(f"{field}_NOT_CANONICAL")
    return parsed


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CertifiedSourcePrefixProofV1:
    kind: str
    source_workspace_json: str
    source_workspace_size_bytes: int
    source_workspace_sha256: str
    source_scenario_id: str
    certified_prefix_json: str
    certified_prefix_event_count: int
    certified_prefix_size_bytes: int
    certified_prefix_sha256: str
    certification_json: str
    certification_size_bytes: int
    certification_sha256: str
    prior_certification_json: str | None
    prior_certification_size_bytes: int
    prior_certification_sha256: str | None
    decision_snapshot_id: str
    portfolio_aim_id: str

    def __post_init__(self) -> None:
        if self.kind != "CERTIFIED_SOURCE_PREFIX_PROOF_V1":
            raise ValueError("CERTIFIED_SOURCE_PROOF_KIND_INVALID")
        if not isinstance(self.decision_snapshot_id, str) or not self.decision_snapshot_id:
            raise ValueError("CERTIFIED_SOURCE_DECISION_SNAPSHOT_REQUIRED")
        if not isinstance(self.portfolio_aim_id, str) or not self.portfolio_aim_id:
            raise ValueError("CERTIFIED_SOURCE_PORTFOLIO_AIM_REQUIRED")
        workspace = _load_canonical_json(
            self.source_workspace_json,
            field="CERTIFIED_SOURCE_WORKSPACE",
            expected_type=dict,
        )
        workspace_size = len(self.source_workspace_json.encode("utf-8"))
        if self.source_workspace_size_bytes != workspace_size:
            raise ValueError("CERTIFIED_SOURCE_WORKSPACE_SIZE_MISMATCH")
        if workspace_size > MAX_SOURCE_WORKSPACE_BYTES:
            raise ValueError("CERTIFIED_SOURCE_WORKSPACE_SIZE_OUT_OF_BOUNDS")
        assert_sha256(self.source_workspace_sha256)
        if self.source_workspace_sha256 != _sha256_text(self.source_workspace_json):
            raise ValueError("CERTIFIED_SOURCE_WORKSPACE_SHA256_MISMATCH")
        if (
            not isinstance(self.source_scenario_id, str)
            or not self.source_scenario_id
            or workspace.get("scenario_id") != self.source_scenario_id
        ):
            raise ValueError("CERTIFIED_SOURCE_WORKSPACE_SCENARIO_MISMATCH")

        prefix = _load_canonical_json(
            self.certified_prefix_json,
            field="CERTIFIED_SOURCE_PREFIX",
            expected_type=list,
        )
        if isinstance(self.certified_prefix_event_count, bool) or not isinstance(
            self.certified_prefix_event_count, int
        ):
            raise TypeError("CERTIFIED_SOURCE_PREFIX_EVENT_COUNT_TYPE_INVALID")
        if self.certified_prefix_event_count != len(prefix):
            raise ValueError("CERTIFIED_SOURCE_PREFIX_EVENT_COUNT_MISMATCH")
        if not 1 <= self.certified_prefix_event_count <= MAX_CERTIFIED_PREFIX_EVENTS:
            raise ValueError("CERTIFIED_SOURCE_PREFIX_EVENT_COUNT_OUT_OF_BOUNDS")
        prefix_size = len(self.certified_prefix_json.encode("utf-8"))
        if self.certified_prefix_size_bytes != prefix_size:
            raise ValueError("CERTIFIED_SOURCE_PREFIX_SIZE_MISMATCH")
        if prefix_size > MAX_CERTIFIED_PREFIX_BYTES:
            raise ValueError("CERTIFIED_SOURCE_PREFIX_SIZE_OUT_OF_BOUNDS")
        assert_sha256(self.certified_prefix_sha256)
        if self.certified_prefix_sha256 != _sha256_text(self.certified_prefix_json):
            raise ValueError("CERTIFIED_SOURCE_PREFIX_SHA256_MISMATCH")

        _load_canonical_json(
            self.certification_json,
            field="CERTIFIED_SOURCE_CERTIFICATION",
            expected_type=dict,
        )
        certification_size = len(self.certification_json.encode("utf-8"))
        if self.certification_size_bytes != certification_size:
            raise ValueError("CERTIFIED_SOURCE_CERTIFICATION_SIZE_MISMATCH")
        if certification_size > MAX_CERTIFICATION_BYTES:
            raise ValueError("CERTIFIED_SOURCE_CERTIFICATION_SIZE_OUT_OF_BOUNDS")
        assert_sha256(self.certification_sha256)
        if self.certification_sha256 != _sha256_text(self.certification_json):
            raise ValueError("CERTIFIED_SOURCE_CERTIFICATION_SHA256_MISMATCH")

        if self.prior_certification_json is None:
            if self.prior_certification_size_bytes != 0:
                raise ValueError("CERTIFIED_SOURCE_PRIOR_SIZE_WITHOUT_DOCUMENT")
            if self.prior_certification_sha256 is not None:
                raise ValueError("CERTIFIED_SOURCE_PRIOR_SHA_WITHOUT_DOCUMENT")
        else:
            _load_canonical_json(
                self.prior_certification_json,
                field="CERTIFIED_SOURCE_PRIOR_CERTIFICATION",
                expected_type=dict,
            )
            prior_size = len(self.prior_certification_json.encode("utf-8"))
            if self.prior_certification_size_bytes != prior_size:
                raise ValueError("CERTIFIED_SOURCE_PRIOR_SIZE_MISMATCH")
            if prior_size > MAX_CERTIFICATION_BYTES:
                raise ValueError("CERTIFIED_SOURCE_PRIOR_SIZE_OUT_OF_BOUNDS")
            if self.prior_certification_sha256 is None:
                raise ValueError("CERTIFIED_SOURCE_PRIOR_SHA_REQUIRED")
            assert_sha256(self.prior_certification_sha256)
            if self.prior_certification_sha256 != _sha256_text(
                self.prior_certification_json
            ):
                raise ValueError("CERTIFIED_SOURCE_PRIOR_SHA256_MISMATCH")


@dataclass(frozen=True, slots=True)
class NoMarketValidationFacts:
    source_proof: CertifiedSourcePrefixProofV1
    certified_book_id: str
    certified_book_head_event_id: str
    certified_book_head_timestamp_utc: str
    certified_book_hash: str
    positions_count: int
    orders_count: int
    fills_count: int
    unexplained_residual: Decimal
    proposal_target_quantities: tuple[Decimal, ...]
    consumes_notional_conversion: bool
    consumes_weight_conversion: bool
    consumes_price_data: bool
    consumes_reference_price: bool
    claims_yield: bool
    claims_market_return: bool
    source_state_digest: str


@dataclass(frozen=True, slots=True)
class NoMarketDependencyCashOnlyV1:
    kind: str
    certified_book_id: str
    certified_book_head_event_id: str
    certified_book_hash: str
    validation_digest: str

    def __post_init__(self) -> None:
        if self.kind != "NO_MARKET_DEPENDENCY_CASH_ONLY_V1":
            raise ValueError("NO_MARKET_KIND_INVALID")
        if not self.certified_book_id or not self.certified_book_head_event_id:
            raise ValueError("NO_MARKET_BOOK_IDENTITY_REQUIRED")
        assert_sha256(self.certified_book_hash)
        assert_sha256(self.validation_digest)


@dataclass(frozen=True, slots=True)
class PointInTimeIdentity:
    certified_book_id: str
    certified_book_head_event_id: str
    evidence_set_id: str
    market_snapshot_id: NoMarketDependencyCashOnlyV1
    as_of_utc: str

    def __post_init__(self) -> None:
        if not isinstance(self.market_snapshot_id, NoMarketDependencyCashOnlyV1):
            raise TypeError("PIT_MARKET_CONTEXT_TYPE_INVALID")
        if not all(
            (
                self.certified_book_id,
                self.certified_book_head_event_id,
                self.evidence_set_id,
                self.as_of_utc,
            )
        ):
            raise ValueError("PIT_IDENTITY_FIELD_REQUIRED")
        if canonical_timestamp(self.as_of_utc) != self.as_of_utc:
            raise ValueError("PIT_AS_OF_TIMESTAMP_NOT_CANONICAL")
        assert_sha256(self.certified_book_id)
        assert_sha256(self.evidence_set_id)
        if self.market_snapshot_id.certified_book_id != self.certified_book_id:
            raise ValueError("PIT_MARKET_BOOK_ID_MISMATCH")
        if (
            self.market_snapshot_id.certified_book_head_event_id
            != self.certified_book_head_event_id
        ):
            raise ValueError("PIT_MARKET_HEAD_EVENT_MISMATCH")


@dataclass(frozen=True, slots=True)
class CapitalProposal:
    proposal_id: str
    module_id: str
    module_version: str
    pit_identity: PointInTimeIdentity
    sleeve_id: str
    outcome: ProposalOutcome
    targets: tuple[InstrumentTarget, ...]
    risk_targets: tuple[RiskTarget, ...]
    quantitative_boundaries: tuple[str, ...]
    principal_claim: str
    supporting_evidence: tuple[EvidenceReference, ...]
    contradicting_evidence: tuple[EvidenceReference, ...]
    missing_discriminator: str
    reason_not_to_act: str
    extension: ExtensionEnvelope

    def __post_init__(self) -> None:
        validate_capital_proposal(self)


def canonical_value(value: object) -> object:
    """Convert immutable contracts into GV canonical primitives."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return format(value, "f")
    if is_dataclass(value):
        return {
            field.name: canonical_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [canonical_value(item) for item in value]
    if isinstance(value, list):
        return [canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): canonical_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(f"UNSUPPORTED_PIT_CANONICAL_TYPE:{type(value).__name__}")


def canonical_contract_bytes(value: object) -> bytes:
    return canonical_document_bytes(canonical_value(value))


def validate_portfolio_source_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the frozen PortfolioBookEvent envelope without execution imports."""

    if not isinstance(event, Mapping):
        raise TypeError("PORTFOLIO_SOURCE_EVENT_MAPPING_REQUIRED")
    sequence = event.get("sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("PORTFOLIO_SOURCE_EVENT_SEQUENCE_INVALID")
    event_type = event.get("event_type")
    if not isinstance(event_type, str) or not event_type:
        raise ValueError("PORTFOLIO_SOURCE_EVENT_TYPE_REQUIRED")
    effective_at = event.get("effective_at")
    if not isinstance(effective_at, str):
        raise TypeError("PORTFOLIO_SOURCE_EVENT_TIMESTAMP_TYPE_INVALID")
    if canonical_timestamp(effective_at) != effective_at:
        raise ValueError("PORTFOLIO_SOURCE_EVENT_TIMESTAMP_NOT_CANONICAL")
    source_identity = event.get("source_identity")
    if not isinstance(source_identity, str) or not source_identity:
        raise ValueError("PORTFOLIO_SOURCE_EVENT_IDENTITY_REQUIRED")
    instrument_id = event.get("instrument_id")
    if instrument_id is not None and (
        not isinstance(instrument_id, str) or not instrument_id
    ):
        raise ValueError("PORTFOLIO_SOURCE_EVENT_INSTRUMENT_INVALID")
    cash_bucket = event.get("cash_bucket")
    if cash_bucket is not None and (
        not isinstance(cash_bucket, str) or not cash_bucket
    ):
        raise ValueError("PORTFOLIO_SOURCE_EVENT_CASH_BUCKET_INVALID")
    payload = event.get("payload")
    if not isinstance(payload, Mapping):
        raise TypeError("PORTFOLIO_SOURCE_EVENT_PAYLOAD_MAPPING_REQUIRED")
    preimage = {
        "sequence": sequence,
        "event_type": event_type,
        "effective_at": effective_at,
        "source_identity": source_identity,
        "instrument_id": instrument_id,
        "cash_bucket": cash_bucket,
        "payload": dict(payload),
    }
    expected = {
        "event_id": "EVT_" + domain_hash(PORTFOLIO_EVENT_ID_DOMAIN, preimage),
        **preimage,
    }
    if canonical_document_bytes(expected) != canonical_document_bytes(dict(event)):
        raise ValueError("PORTFOLIO_SOURCE_EVENT_ID_MISMATCH")
    return expected


def _schema_digest(schema_id: str, schema_version: str, fields_: tuple[str, ...]) -> str:
    return domain_hash(
        SCHEMA_DIGEST_DOMAIN,
        {
            "schema_id": schema_id,
            "schema_version": schema_version,
            "fields": list(fields_),
        },
    )


def validate_extension_envelope(extension: ExtensionEnvelope) -> None:
    if isinstance(extension, EquityFundamentalExtensionV1):
        schema_id = "EQUITY_FUNDAMENTAL_V1"
        schema_version = "1.0.0"
        if not isinstance(extension.payload, EquityFundamentalPayloadV1):
            raise TypeError("EQUITY_EXTENSION_PAYLOAD_TYPE_INVALID")
        expected_schema = _schema_digest(
            schema_id,
            schema_version,
            ("subject", "permanent_key", "net_score_bps", "missing_discriminator"),
        )
    elif isinstance(extension, CashBaselineExtensionV1):
        schema_id = "CASH_BASELINE_V1"
        schema_version = "1.0.0"
        if not isinstance(extension.payload, CashBaselinePayloadV1):
            raise TypeError("CASH_EXTENSION_PAYLOAD_TYPE_INVALID")
        expected_schema = _schema_digest(
            schema_id,
            schema_version,
            ("nav", "classified_cash", "yield_status"),
        )
    else:
        raise TypeError("EXTENSION_ENVELOPE_TYPE_INVALID")
    if extension.schema_id != schema_id:
        raise ValueError("EXTENSION_SCHEMA_ID_MISMATCH")
    if extension.schema_version != schema_version:
        raise ValueError("EXTENSION_SCHEMA_VERSION_MISMATCH")
    if extension.schema_digest != expected_schema:
        raise ValueError("EXTENSION_SCHEMA_DIGEST_MISMATCH")
    expected_payload = domain_hash(
        PAYLOAD_DIGEST_DOMAIN, canonical_value(extension.payload)
    )
    if extension.canonical_payload_digest != expected_payload:
        raise ValueError("EXTENSION_PAYLOAD_DIGEST_MISMATCH")


def validate_capital_proposal(proposal: CapitalProposal) -> None:
    validate_extension_envelope(proposal.extension)
    if not isinstance(proposal.pit_identity, PointInTimeIdentity):
        raise TypeError("PROPOSAL_PIT_IDENTITY_TYPE_INVALID")
    if not isinstance(proposal.outcome, ProposalOutcome):
        raise TypeError("PROPOSAL_OUTCOME_TYPE_INVALID")
    if not isinstance(proposal.targets, tuple) or not all(
        isinstance(row, InstrumentTarget) for row in proposal.targets
    ):
        raise TypeError("PROPOSAL_TARGETS_TYPE_INVALID")
    if not isinstance(proposal.risk_targets, tuple) or not all(
        isinstance(row, RiskTarget) for row in proposal.risk_targets
    ):
        raise TypeError("PROPOSAL_RISK_TARGETS_TYPE_INVALID")
    if not isinstance(proposal.supporting_evidence, tuple) or not all(
        isinstance(row, EvidenceReference) for row in proposal.supporting_evidence
    ):
        raise TypeError("PROPOSAL_SUPPORTING_EVIDENCE_TYPE_INVALID")
    if not isinstance(proposal.contradicting_evidence, tuple) or not all(
        isinstance(row, EvidenceReference) for row in proposal.contradicting_evidence
    ):
        raise TypeError("PROPOSAL_CONTRADICTING_EVIDENCE_TYPE_INVALID")
    if not isinstance(proposal.quantitative_boundaries, tuple) or not all(
        isinstance(row, str) and row.strip()
        for row in proposal.quantitative_boundaries
    ):
        raise TypeError("PROPOSAL_QUANTITATIVE_BOUNDARIES_TYPE_INVALID")
    for field_name in (
        "module_id",
        "module_version",
        "sleeve_id",
        "principal_claim",
        "missing_discriminator",
        "reason_not_to_act",
    ):
        value = getattr(proposal, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"PROPOSAL_{field_name.upper()}_REQUIRED")
    body = {
        "module_id": proposal.module_id,
        "module_version": proposal.module_version,
        "pit_identity": canonical_value(proposal.pit_identity),
        "sleeve_id": proposal.sleeve_id,
        "outcome": proposal.outcome.value,
        "targets": canonical_value(proposal.targets),
        "risk_targets": canonical_value(proposal.risk_targets),
        "quantitative_boundaries": list(proposal.quantitative_boundaries),
        "principal_claim": proposal.principal_claim,
        "supporting_evidence": canonical_value(proposal.supporting_evidence),
        "contradicting_evidence": canonical_value(proposal.contradicting_evidence),
        "missing_discriminator": proposal.missing_discriminator,
        "reason_not_to_act": proposal.reason_not_to_act,
        "extension": canonical_value(proposal.extension),
    }
    expected_id = "CPP_" + domain_hash(PROPOSAL_ID_DOMAIN, body)
    if proposal.proposal_id != expected_id:
        raise ValueError("CAPITAL_PROPOSAL_ID_MISMATCH")


def build_equity_extension(
    payload: EquityFundamentalPayloadV1,
) -> EquityFundamentalExtensionV1:
    schema_id = "EQUITY_FUNDAMENTAL_V1"
    schema_version = "1.0.0"
    return EquityFundamentalExtensionV1(
        schema_id=schema_id,
        schema_version=schema_version,
        schema_digest=_schema_digest(
            schema_id,
            schema_version,
            ("subject", "permanent_key", "net_score_bps", "missing_discriminator"),
        ),
        canonical_payload_digest=domain_hash(
            PAYLOAD_DIGEST_DOMAIN, canonical_value(payload)
        ),
        payload=payload,
    )


def build_cash_extension(payload: CashBaselinePayloadV1) -> CashBaselineExtensionV1:
    schema_id = "CASH_BASELINE_V1"
    schema_version = "1.0.0"
    return CashBaselineExtensionV1(
        schema_id=schema_id,
        schema_version=schema_version,
        schema_digest=_schema_digest(
            schema_id,
            schema_version,
            ("nav", "classified_cash", "yield_status"),
        ),
        canonical_payload_digest=domain_hash(
            PAYLOAD_DIGEST_DOMAIN, canonical_value(payload)
        ),
        payload=payload,
    )


def build_certified_source_prefix_proof(
    *,
    source_workspace: Mapping[str, Any],
    certified_prefix: list[Mapping[str, Any]],
    certification: Mapping[str, Any],
    prior_certification: Mapping[str, Any] | None,
    decision_snapshot_id: str,
    portfolio_aim_id: str,
) -> CertifiedSourcePrefixProofV1:
    workspace_json = canonical_document_bytes(dict(source_workspace)).decode("utf-8")
    prefix_json = canonical_document_bytes([dict(row) for row in certified_prefix]).decode(
        "utf-8"
    )
    certification_json = canonical_document_bytes(dict(certification)).decode("utf-8")
    prior_json = (
        None
        if prior_certification is None
        else canonical_document_bytes(dict(prior_certification)).decode("utf-8")
    )
    return CertifiedSourcePrefixProofV1(
        kind="CERTIFIED_SOURCE_PREFIX_PROOF_V1",
        source_workspace_json=workspace_json,
        source_workspace_size_bytes=len(workspace_json.encode("utf-8")),
        source_workspace_sha256=_sha256_text(workspace_json),
        source_scenario_id=str(source_workspace.get("scenario_id") or ""),
        certified_prefix_json=prefix_json,
        certified_prefix_event_count=len(certified_prefix),
        certified_prefix_size_bytes=len(prefix_json.encode("utf-8")),
        certified_prefix_sha256=_sha256_text(prefix_json),
        certification_json=certification_json,
        certification_size_bytes=len(certification_json.encode("utf-8")),
        certification_sha256=_sha256_text(certification_json),
        prior_certification_json=prior_json,
        prior_certification_size_bytes=(
            0 if prior_json is None else len(prior_json.encode("utf-8"))
        ),
        prior_certification_sha256=(
            None if prior_json is None else _sha256_text(prior_json)
        ),
        decision_snapshot_id=decision_snapshot_id,
        portfolio_aim_id=portfolio_aim_id,
    )


def decode_certified_source_prefix_proof(
    proof: CertifiedSourcePrefixProofV1,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any] | None,
]:
    if not isinstance(proof, CertifiedSourcePrefixProofV1):
        raise TypeError("CERTIFIED_SOURCE_PROOF_TYPE_INVALID")
    workspace_raw = _load_canonical_json(
        proof.source_workspace_json,
        field="CERTIFIED_SOURCE_WORKSPACE",
        expected_type=dict,
    )
    prefix_raw = _load_canonical_json(
        proof.certified_prefix_json,
        field="CERTIFIED_SOURCE_PREFIX",
        expected_type=list,
    )
    prefix: list[dict[str, Any]] = []
    for row in prefix_raw:
        if not isinstance(row, dict):
            raise ValueError("CERTIFIED_SOURCE_PREFIX_EVENT_MAPPING_REQUIRED")
        prefix.append(dict(row))
    certification_raw = _load_canonical_json(
        proof.certification_json,
        field="CERTIFIED_SOURCE_CERTIFICATION",
        expected_type=dict,
    )
    prior: dict[str, Any] | None = None
    if proof.prior_certification_json is not None:
        prior_raw = _load_canonical_json(
            proof.prior_certification_json,
            field="CERTIFIED_SOURCE_PRIOR_CERTIFICATION",
            expected_type=dict,
        )
        prior = dict(prior_raw)
    return dict(workspace_raw), prefix, dict(certification_raw), prior


def no_market_source_state_body(facts: NoMarketValidationFacts) -> dict[str, object]:
    return {
        "source_proof": canonical_value(facts.source_proof),
        "certified_book_id": facts.certified_book_id,
        "certified_book_head_event_id": facts.certified_book_head_event_id,
        "certified_book_head_timestamp_utc": facts.certified_book_head_timestamp_utc,
        "certified_book_hash": facts.certified_book_hash,
        "positions_count": facts.positions_count,
        "orders_count": facts.orders_count,
        "fills_count": facts.fills_count,
        "unexplained_residual": canonical_value(facts.unexplained_residual),
        "proposal_target_quantities": canonical_value(
            facts.proposal_target_quantities
        ),
        "consumes_notional_conversion": facts.consumes_notional_conversion,
        "consumes_weight_conversion": facts.consumes_weight_conversion,
        "consumes_price_data": facts.consumes_price_data,
        "consumes_reference_price": facts.consumes_reference_price,
        "claims_yield": facts.claims_yield,
        "claims_market_return": facts.claims_market_return,
    }


def validate_no_market_facts(facts: NoMarketValidationFacts) -> None:
    if not isinstance(facts.source_proof, CertifiedSourcePrefixProofV1):
        raise TypeError("NO_MARKET_SOURCE_PROOF_TYPE_INVALID")
    if not facts.certified_book_id or not facts.certified_book_head_event_id:
        raise ValueError("NO_MARKET_CERTIFIED_BOOK_IDENTITY_REQUIRED")
    for field_name in ("positions_count", "orders_count", "fills_count"):
        value = getattr(facts, field_name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TypeError(f"NO_MARKET_{field_name.upper()}_TYPE_INVALID")
    if not isinstance(facts.unexplained_residual, Decimal):
        raise TypeError("NO_MARKET_RESIDUAL_TYPE_INVALID")
    if not isinstance(facts.proposal_target_quantities, tuple) or not all(
        isinstance(quantity, Decimal) for quantity in facts.proposal_target_quantities
    ):
        raise TypeError("NO_MARKET_TARGET_QUANTITIES_TYPE_INVALID")
    for field_name in (
        "consumes_notional_conversion",
        "consumes_weight_conversion",
        "consumes_price_data",
        "consumes_reference_price",
        "claims_yield",
        "claims_market_return",
    ):
        if not isinstance(getattr(facts, field_name), bool):
            raise TypeError(f"NO_MARKET_{field_name.upper()}_TYPE_INVALID")
    assert_sha256(facts.certified_book_id)
    assert_sha256(facts.certified_book_hash)
    if facts.certified_book_id != facts.certified_book_hash:
        raise ValueError("NO_MARKET_CERTIFIED_BOOK_HASH_MISMATCH")
    if canonical_timestamp(facts.certified_book_head_timestamp_utc) != (
        facts.certified_book_head_timestamp_utc
    ):
        raise ValueError("NO_MARKET_HEAD_TIMESTAMP_NOT_CANONICAL")
    if facts.positions_count != 0:
        raise ValueError("NO_MARKET_POSITIONS_NOT_EMPTY")
    if facts.orders_count != 0:
        raise ValueError("NO_MARKET_ORDERS_NOT_EMPTY")
    if facts.fills_count != 0:
        raise ValueError("NO_MARKET_FILLS_NOT_EMPTY")
    if not facts.unexplained_residual.is_finite():
        raise ValueError("NO_MARKET_RESIDUAL_FINITE_REQUIRED")
    if facts.unexplained_residual != Decimal("0"):
        raise ValueError("NO_MARKET_RESIDUAL_NONZERO")
    if any(not quantity.is_finite() for quantity in facts.proposal_target_quantities):
        raise ValueError("NO_MARKET_TARGET_QUANTITY_FINITE_REQUIRED")
    if any(quantity != Decimal("0") for quantity in facts.proposal_target_quantities):
        raise ValueError("NO_MARKET_TARGET_QUANTITY_NONZERO")
    if facts.consumes_notional_conversion:
        raise ValueError("NO_MARKET_NOTIONAL_CONVERSION_PROHIBITED")
    if facts.consumes_weight_conversion:
        raise ValueError("NO_MARKET_WEIGHT_CONVERSION_PROHIBITED")
    if facts.consumes_price_data:
        raise ValueError("NO_MARKET_PRICE_CONSUMPTION_PROHIBITED")
    if facts.consumes_reference_price:
        raise ValueError("NO_MARKET_REFERENCE_PRICE_CONSUMPTION_PROHIBITED")
    if facts.claims_yield:
        raise ValueError("NO_MARKET_YIELD_CLAIM_PROHIBITED")
    if facts.claims_market_return:
        raise ValueError("NO_MARKET_RETURN_CLAIM_PROHIBITED")
    expected_source_state_digest = domain_hash(
        NO_MARKET_SOURCE_STATE_DOMAIN, no_market_source_state_body(facts)
    )
    if facts.source_state_digest != expected_source_state_digest:
        raise ValueError("NO_MARKET_SOURCE_STATE_DIGEST_MISMATCH")


def build_no_market_source_state_digest(
    *,
    source_proof: CertifiedSourcePrefixProofV1,
    certified_book_id: str,
    certified_book_head_event_id: str,
    certified_book_head_timestamp_utc: str,
    certified_book_hash: str,
    positions_count: int,
    orders_count: int,
    fills_count: int,
    unexplained_residual: Decimal,
    proposal_target_quantities: tuple[Decimal, ...],
    consumes_notional_conversion: bool,
    consumes_weight_conversion: bool,
    consumes_price_data: bool,
    consumes_reference_price: bool,
    claims_yield: bool,
    claims_market_return: bool,
) -> str:
    body = {
        "source_proof": canonical_value(source_proof),
        "certified_book_id": certified_book_id,
        "certified_book_head_event_id": certified_book_head_event_id,
        "certified_book_head_timestamp_utc": certified_book_head_timestamp_utc,
        "certified_book_hash": certified_book_hash,
        "positions_count": positions_count,
        "orders_count": orders_count,
        "fills_count": fills_count,
        "unexplained_residual": canonical_value(unexplained_residual),
        "proposal_target_quantities": canonical_value(proposal_target_quantities),
        "consumes_notional_conversion": consumes_notional_conversion,
        "consumes_weight_conversion": consumes_weight_conversion,
        "consumes_price_data": consumes_price_data,
        "consumes_reference_price": consumes_reference_price,
        "claims_yield": claims_yield,
        "claims_market_return": claims_market_return,
    }
    return domain_hash(NO_MARKET_SOURCE_STATE_DOMAIN, body)


def build_no_market_identity(
    facts: NoMarketValidationFacts,
) -> NoMarketDependencyCashOnlyV1:
    validate_no_market_facts(facts)
    return NoMarketDependencyCashOnlyV1(
        kind="NO_MARKET_DEPENDENCY_CASH_ONLY_V1",
        certified_book_id=facts.certified_book_id,
        certified_book_head_event_id=facts.certified_book_head_event_id,
        certified_book_hash=facts.certified_book_hash,
        validation_digest=domain_hash(
            NO_MARKET_VALIDATION_DOMAIN, canonical_value(facts)
        ),
    )


def build_pit_identity(
    *,
    certified_book_id: str,
    certified_book_head_event_id: str,
    certified_book_head_timestamp_utc: str,
    evidence_set_id: str,
    market_snapshot_id: NoMarketDependencyCashOnlyV1,
    as_of_utc: str,
) -> PointInTimeIdentity:
    if canonical_timestamp(certified_book_head_timestamp_utc) != (
        certified_book_head_timestamp_utc
    ):
        raise ValueError("PIT_CERTIFIED_HEAD_TIMESTAMP_NOT_CANONICAL")
    if as_of_utc != certified_book_head_timestamp_utc:
        raise ValueError("PIT_AS_OF_NOT_CERTIFIED_HEAD_TIMESTAMP")
    identity = PointInTimeIdentity(
        certified_book_id=certified_book_id,
        certified_book_head_event_id=certified_book_head_event_id,
        evidence_set_id=evidence_set_id,
        market_snapshot_id=market_snapshot_id,
        as_of_utc=as_of_utc,
    )
    domain_hash(PIT_ID_DOMAIN, canonical_value(identity))
    return identity


def with_proposal_id(
    *,
    module_id: str,
    module_version: str,
    pit_identity: PointInTimeIdentity,
    sleeve_id: str,
    outcome: ProposalOutcome,
    targets: tuple[InstrumentTarget, ...],
    risk_targets: tuple[RiskTarget, ...],
    quantitative_boundaries: tuple[str, ...],
    principal_claim: str,
    supporting_evidence: tuple[EvidenceReference, ...],
    contradicting_evidence: tuple[EvidenceReference, ...],
    missing_discriminator: str,
    reason_not_to_act: str,
    extension: ExtensionEnvelope,
) -> CapitalProposal:
    body = {
        "module_id": module_id,
        "module_version": module_version,
        "pit_identity": canonical_value(pit_identity),
        "sleeve_id": sleeve_id,
        "outcome": outcome.value,
        "targets": canonical_value(targets),
        "risk_targets": canonical_value(risk_targets),
        "quantitative_boundaries": list(quantitative_boundaries),
        "principal_claim": principal_claim,
        "supporting_evidence": canonical_value(supporting_evidence),
        "contradicting_evidence": canonical_value(contradicting_evidence),
        "missing_discriminator": missing_discriminator,
        "reason_not_to_act": reason_not_to_act,
        "extension": canonical_value(extension),
    }
    return CapitalProposal(
        proposal_id="CPP_" + domain_hash(PROPOSAL_ID_DOMAIN, body),
        module_id=module_id,
        module_version=module_version,
        pit_identity=pit_identity,
        sleeve_id=sleeve_id,
        outcome=outcome,
        targets=targets,
        risk_targets=risk_targets,
        quantitative_boundaries=quantitative_boundaries,
        principal_claim=principal_claim,
        supporting_evidence=supporting_evidence,
        contradicting_evidence=contradicting_evidence,
        missing_discriminator=missing_discriminator,
        reason_not_to_act=reason_not_to_act,
        extension=extension,
    )
