"""Immutable contracts for the read-only all-capital point-in-time episode.

The module owns value contracts and deterministic identity derivation only. It
contains no adapter I/O, lifecycle state, portfolio calculation, or mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash


PIT_ID_DOMAIN = "GV-PIT:IDENTITY:V1"
NO_MARKET_VALIDATION_DOMAIN = "GV-PIT:NO-MARKET-CASH-ONLY:V1"
PROPOSAL_ID_DOMAIN = "GV-PIT:CAPITAL-PROPOSAL:V1"
SCHEMA_DIGEST_DOMAIN = "GV-PIT:EXTENSION-SCHEMA:V1"
PAYLOAD_DIGEST_DOMAIN = "GV-PIT:EXTENSION-PAYLOAD:V1"


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


@dataclass(frozen=True, slots=True)
class NumericNormalizationPolicy:
    unit_quantum: Decimal
    rounding_mode: RoundingMode
    currency: str
    price_identity: str | None
    contract_multiplier: Decimal | None
    lot_size_policy: LotSizePolicy


@dataclass(frozen=True, slots=True)
class InstrumentTarget:
    instrument_id: str
    symbol: str
    intent: TargetIntent
    unit: InstrumentUnit
    target_value: Decimal
    normalization: NumericNormalizationPolicy


@dataclass(frozen=True, slots=True)
class RiskTarget:
    measure: RiskMeasure
    unit: RiskUnit
    value: Decimal


@dataclass(frozen=True, slots=True)
class CashBucketAmount:
    bucket: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class EquityFundamentalPayloadV1:
    subject: str
    permanent_key: str
    net_score_bps: int
    missing_discriminator: str


@dataclass(frozen=True, slots=True)
class CashBaselinePayloadV1:
    nav: Decimal
    classified_cash: tuple[CashBucketAmount, ...]
    yield_status: str


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


@dataclass(frozen=True, slots=True)
class NoMarketValidationFacts:
    certified_book_id: str
    certified_book_head_event_id: str
    certified_book_hash: str
    positions_count: int
    orders_count: int
    fills_count: int
    unexplained_residual: Decimal
    proposal_target_quantities: tuple[Decimal, ...]
    consumes_notional_conversion: bool
    consumes_weight_conversion: bool
    consumes_price_data: bool
    claims_yield: bool
    claims_market_return: bool


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


def build_no_market_identity(
    facts: NoMarketValidationFacts,
) -> NoMarketDependencyCashOnlyV1:
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
    evidence_set_id: str,
    market_snapshot_id: NoMarketDependencyCashOnlyV1,
    as_of_utc: str,
) -> PointInTimeIdentity:
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
