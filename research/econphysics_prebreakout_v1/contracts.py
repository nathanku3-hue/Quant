"""Narrow S0 contracts for structured ECONPHYSICS state-transition proof.

This module owns only point-in-time structured-fundamental semantics.  It has
no equity-return, market-confirmation, selection, model-fit, or provider-access
surface.  All inputs are already-captured Original-filing snapshots whose
historical as-of boundary is explicit in every row.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import hashlib
from typing import Any, Mapping, Sequence

from research.aov0.contracts import normalize_security_id


FAMILY_ID = "ECONPHYSICS_PREBREAKOUT_v1"
IMPLEMENTATION_ID = "ECONPHYSICS_PREBREAKOUT_S0_STRUCTURED_STATE_v1"
STRUCTURED_ROW_SCHEMA = "econphysics_prebreakout_s0_structured_row_v1"
STRUCTURED_SNAPSHOT_SCHEMA = "econphysics_prebreakout_s0_structured_snapshot_v1"
TRANSITION_REPORT_SCHEMA = "econphysics_prebreakout_s0_transition_report_v1"

RELATIVE_PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")
VALUE_METRICS = ("IQ_TOTAL_REV", "IQ_INVENTORY", "IQ_OPER_INC", "IQ_CAPEX_BNK")
REQUEST_METRICS = ("IQ_PERIOD_END", *VALUE_METRICS)
FILING_VERSION = "Original"
VALUE_UNIT = "USD_THOUSANDS"
XS_HOLDOUT_BUCKET_COUNT = 5
XS_HOLDOUT_BUCKET = 0
TEMPORAL_FOLD_COUNT = 4


class CoverageState(StrEnum):
    OBSERVED = "OBSERVED"
    UNOBSERVED = "UNOBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class NodeState(StrEnum):
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    MIXED = "MIXED"
    UNOBSERVED = "UNOBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class NodeTransition(StrEnum):
    DETERIORATING = "DETERIORATING"
    STABLE = "STABLE"
    IMPROVING = "IMPROVING"
    INFLECTING_NEGATIVE = "INFLECTING_NEGATIVE"
    INFLECTING_POSITIVE = "INFLECTING_POSITIVE"
    UNOBSERVED = "UNOBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StructuredStateContractError(ValueError):
    """Fail-closed S0 structured-state contract error."""


@dataclass(frozen=True)
class StructuredQuarterRow:
    security_id: str
    source_entity_id: str
    as_of_date: date
    available_at: datetime
    relative_period: str
    period_end: date | None
    total_revenue: Decimal | None
    inventory: Decimal | None
    operating_income: Decimal | None
    capex: Decimal | None
    source_receipt_sha256: str
    filing_version: str = FILING_VERSION
    value_unit: str = VALUE_UNIT


@dataclass(frozen=True)
class StructuredSnapshot:
    security_id: str
    source_entity_id: str
    as_of_date: date
    available_at: datetime
    rows: tuple[StructuredQuarterRow, ...]
    source_receipt_sha256: str

    def by_period(self) -> dict[str, StructuredQuarterRow]:
        return {row.relative_period: row for row in self.rows}

    @property
    def fq0_period_end(self) -> date:
        value = self.by_period()["FQ0"].period_end
        if value is None:
            raise StructuredStateContractError("econphysics_s0_fq0_period_end_required")
        return value


def normalize_structured_rows(rows: Sequence[Mapping[str, Any]]) -> list[StructuredQuarterRow]:
    """Validate and normalize already-captured five-quarter S0 rows.

    Required timestamps are explicit.  `available_at` is the conservative
    historical-as-of boundary assigned by the successor capture admission, not
    the later retrieval timestamp.
    """

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise StructuredStateContractError("econphysics_s0_structured_rows_required")
    normalized: list[StructuredQuarterRow] = []
    seen: set[tuple[str, date, str]] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise StructuredStateContractError("econphysics_s0_structured_row_mapping_required")
        security_id = normalize_security_id(str(raw.get("security_id") or ""))
        entity = str(raw.get("source_entity_id") or "").strip()
        if not entity.isdigit():
            raise StructuredStateContractError("econphysics_s0_source_entity_id_invalid")
        as_of = _date(raw.get("as_of_date"), "as_of_date")
        available_at = _datetime(raw.get("available_at"), "available_at")
        if available_at.date() > as_of:
            raise StructuredStateContractError("econphysics_s0_available_at_after_as_of_date")
        relative_period = str(raw.get("relative_period") or "").strip().upper()
        if relative_period not in RELATIVE_PERIODS:
            raise StructuredStateContractError("econphysics_s0_relative_period_invalid")
        key = (security_id, as_of, relative_period)
        if key in seen:
            raise StructuredStateContractError("econphysics_s0_duplicate_security_asof_period")
        seen.add(key)
        period_end = _optional_date(raw.get("period_end"), "period_end")
        if period_end is not None and period_end > as_of:
            raise StructuredStateContractError("econphysics_s0_future_period_end")
        filing_version = str(raw.get("filing_version") or "").strip()
        if filing_version != FILING_VERSION:
            raise StructuredStateContractError("econphysics_s0_original_filing_required")
        value_unit = str(raw.get("value_unit") or "").strip().upper()
        if value_unit != VALUE_UNIT:
            raise StructuredStateContractError("econphysics_s0_value_unit_invalid")
        receipt = str(raw.get("source_receipt_sha256") or "").strip().lower()
        if not _is_sha256(receipt):
            raise StructuredStateContractError("econphysics_s0_source_receipt_sha256_invalid")
        normalized.append(
            StructuredQuarterRow(
                security_id=security_id,
                source_entity_id=entity,
                as_of_date=as_of,
                available_at=available_at,
                relative_period=relative_period,
                period_end=period_end,
                total_revenue=_optional_decimal(raw.get("IQ_TOTAL_REV"), "IQ_TOTAL_REV"),
                inventory=_optional_decimal(raw.get("IQ_INVENTORY"), "IQ_INVENTORY"),
                operating_income=_optional_decimal(raw.get("IQ_OPER_INC"), "IQ_OPER_INC"),
                capex=_optional_decimal(raw.get("IQ_CAPEX_BNK"), "IQ_CAPEX_BNK"),
                source_receipt_sha256=receipt,
                filing_version=filing_version,
                value_unit=value_unit,
            )
        )
    return sorted(
        normalized,
        key=lambda row: (row.as_of_date, int(row.source_entity_id), RELATIVE_PERIODS.index(row.relative_period)),
    )


def build_structured_snapshots(rows: Sequence[Mapping[str, Any]]) -> list[StructuredSnapshot]:
    normalized = normalize_structured_rows(rows)
    grouped: dict[tuple[str, str, date], list[StructuredQuarterRow]] = {}
    for row in normalized:
        grouped.setdefault((row.security_id, row.source_entity_id, row.as_of_date), []).append(row)
    snapshots: list[StructuredSnapshot] = []
    for (security_id, entity, as_of), group in grouped.items():
        if {row.relative_period for row in group} != set(RELATIVE_PERIODS) or len(group) != len(RELATIVE_PERIODS):
            raise StructuredStateContractError("econphysics_s0_five_quarter_grid_required")
        entities = {row.source_entity_id for row in group}
        securities = {row.security_id for row in group}
        receipts = {row.source_receipt_sha256 for row in group}
        available = {row.available_at for row in group}
        units = {row.value_unit for row in group}
        versions = {row.filing_version for row in group}
        if len(entities) != 1 or len(securities) != 1:
            raise StructuredStateContractError("econphysics_s0_snapshot_identity_drift")
        if len(receipts) != 1:
            raise StructuredStateContractError("econphysics_s0_snapshot_receipt_drift")
        if len(available) != 1:
            raise StructuredStateContractError("econphysics_s0_snapshot_available_at_drift")
        if units != {VALUE_UNIT} or versions != {FILING_VERSION}:
            raise StructuredStateContractError("econphysics_s0_snapshot_semantics_drift")
        ordered = tuple(sorted(group, key=lambda row: RELATIVE_PERIODS.index(row.relative_period)))
        fq0 = ordered[0]
        if fq0.period_end is None:
            raise StructuredStateContractError("econphysics_s0_fq0_period_end_required")
        period_ends = [row.period_end for row in ordered if row.period_end is not None]
        if len(period_ends) != len(set(period_ends)):
            raise StructuredStateContractError("econphysics_s0_duplicate_period_end_within_snapshot")
        snapshots.append(
            StructuredSnapshot(
                security_id=security_id,
                source_entity_id=entity,
                as_of_date=as_of,
                available_at=next(iter(available)),
                rows=ordered,
                source_receipt_sha256=next(iter(receipts)),
            )
        )
    _validate_identity_and_time_order(snapshots)
    return sorted(snapshots, key=lambda snap: (snap.as_of_date, int(snap.source_entity_id)))


def deterministic_xs_holdout(security_id: str) -> bool:
    security = normalize_security_id(security_id)
    digest = hashlib.sha256(f"ECONPHYSICS_S0_XS_HOLDOUT_V1|{security}".encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:8], "big") % XS_HOLDOUT_BUCKET_COUNT
    return bucket == XS_HOLDOUT_BUCKET


def conservative_available_at(as_of: date | str) -> datetime:
    """Return the frozen conservative end-of-UTC-date availability boundary."""

    day = _date(as_of, "as_of_date")
    return datetime(day.year, day.month, day.day, 23, 59, 59, 999999, tzinfo=UTC)


def _validate_identity_and_time_order(snapshots: Sequence[StructuredSnapshot]) -> None:
    entity_to_security: dict[str, str] = {}
    security_to_entity: dict[str, str] = {}
    by_security: dict[str, list[StructuredSnapshot]] = {}
    for snapshot in snapshots:
        old_security = entity_to_security.setdefault(snapshot.source_entity_id, snapshot.security_id)
        old_entity = security_to_entity.setdefault(snapshot.security_id, snapshot.source_entity_id)
        if old_security != snapshot.security_id or old_entity != snapshot.source_entity_id:
            raise StructuredStateContractError("econphysics_s0_security_entity_mapping_not_one_to_one")
        by_security.setdefault(snapshot.security_id, []).append(snapshot)
    for security_id, group in by_security.items():
        ordered = sorted(group, key=lambda snapshot: snapshot.as_of_date)
        if len({snapshot.as_of_date for snapshot in ordered}) != len(ordered):
            raise StructuredStateContractError("econphysics_s0_duplicate_security_asof_snapshot")
        prior_period_end: date | None = None
        for snapshot in ordered:
            if snapshot.available_at.date() > snapshot.as_of_date:
                raise StructuredStateContractError("econphysics_s0_pit_violation")
            if prior_period_end is not None and snapshot.fq0_period_end <= prior_period_end:
                raise StructuredStateContractError(
                    f"econphysics_s0_nonadvancing_fq0_period_end:{security_id}:{snapshot.as_of_date.isoformat()}"
                )
            prior_period_end = snapshot.fq0_period_end


def _date(value: object, field: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise StructuredStateContractError(f"econphysics_s0_{field}_invalid") from exc


def _optional_date(value: object, field: str) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    return _date(value, field)


def _datetime(value: object, field: str) -> datetime:
    if isinstance(value, datetime):
        stamp = value
    else:
        text = str(value or "").strip()
        try:
            stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise StructuredStateContractError(f"econphysics_s0_{field}_invalid") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise StructuredStateContractError(f"econphysics_s0_{field}_timezone_required")
    return stamp.astimezone(UTC)


def _optional_decimal(value: object, field: str) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() in {"NA", "N/A", "NAN", "NULL", "NONE"} or text.startswith("#"):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise StructuredStateContractError(f"econphysics_s0_{field}_numeric_invalid") from exc
    if not number.is_finite():
        return None
    return number


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
