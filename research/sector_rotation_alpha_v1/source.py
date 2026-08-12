"""No-network prospective source admission for ETF-first sector rotation.

This module accepts already-landed, hash-receipted ETF identity/risk-set rows and
daily market history. It performs no provider acquisition and has no dependency
on the legacy stock-sector map, stock breadth, or underlying-stock membership.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from math import isfinite
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    AlphaPITBackendV1,
    ArtifactRef,
    ResearchMode,
    validate_security_ids,
    validate_source_receipt_binding,
)
from research.alpha_pit_v1.manifests import build_artifact_ref, canonical_value
from research.alpha_pit_v1.session import open_alpha_pit_session
from research.sector_rotation_alpha_v1.contracts import (
    EXPECTED_SECTOR_KEYS,
    FAMILY_DATA_CONTRACT,
    FAMILY_DATA_CONTRACT_SHA256,
    FAMILY_ID,
    IMPLEMENTATION_ID,
    MARKET_HISTORY_ARTIFACT_TYPE,
    MARKET_HISTORY_SCHEMA,
    MIN_HISTORY_SESSIONS,
    RISK_SET_SPEC_ID,
)
from research.sector_rotation_alpha_v1.pit_packet import build_sector_rotation_input_packet


RISK_SET_SOURCE_AUTHORITY_SCHEMA = "sra_us_select_sector_etf_source_authority_v1"
RISK_SET_SOURCE_ROW_SCHEMA = "sra_us_select_sector_etf_source_row_v1"
MARKET_SOURCE_ROW_SCHEMA = "sra_etf_primary_market_source_row_v1"
SOURCE_PRODUCTION_SCHEMA = "sector_rotation_alpha_source_production_v1"
PROSPECTIVE_CAPTURE_MODE = "PROSPECTIVE_SAME_DAY_ETF_SNAPSHOT"
BENCHMARK_FAMILY_ID = "US_SELECT_SECTOR_ETF_11_V1"
REAL_PROVIDER_NAMES = {"S&P CAPITAL IQ PRO", "S&P CAPITAL IQ", "SPCIQPRO"}
FIXTURE_PROVIDER_NAME = "DETERMINISTIC_FIXTURE_ONLY"
NYSE_TZ = ZoneInfo("America/New_York")
NYSE_2026_CLOSED_DATES = frozenset(
    {
        "2026-01-01",
        "2026-01-19",
        "2026-02-16",
        "2026-04-03",
        "2026-05-25",
        "2026-06-19",
        "2026-07-03",
        "2026-09-07",
        "2026-11-26",
        "2026-12-25",
    }
)
CONSERVATIVE_PRIMARY_CLOSE = time(16, 0)

RISK_SET_SOURCE_AUTHORITY_FIELDS = {
    "schema_version",
    "family_id",
    "risk_set_spec_id",
    "capture_mode",
    "decision_date",
    "benchmark_family_id",
    "expected_sector_keys",
    "stock_sector_map_used",
    "stock_breadth_used",
    "underlying_stock_membership_used",
    "current_survivor_back_projection_used",
    "alternate_listing_backfill_used",
    "legacy_identity_fallback_used",
    "etf_flow_vendor_used",
    "corporate_action_total_return_authority_bound",
    "source_receipt_sha256s",
}
RISK_SET_SOURCE_ROW_FIELDS = {
    "schema_version",
    "security_id",
    "trading_item_id",
    "primary_listing_id",
    "sector_key",
    "benchmark_family_id",
    "benchmark_membership_receipt_sha256",
    "instrument_type",
    "listing_country",
    "primary_listing",
    "active_tradable",
    "unique_security_mapping",
    "membership_effective_at",
    "observed_at",
    "available_at",
    "source_id",
    "source_receipt_sha256",
    "identity_receipt_sha256",
}
MARKET_SOURCE_ROW_FIELDS = {
    "schema_version",
    "security_id",
    "trading_item_id",
    "sector_key",
    "session_date",
    "close",
    "total_return_1d",
    "volume",
    "observed_at",
    "available_at",
    "source_id",
    "source_receipt_sha256",
}


@dataclass(frozen=True)
class SectorRotationSourceProduction:
    risk_set: ArtifactRef
    market_history: ArtifactRef
    input_packet: Mapping[str, Any]
    source_production_sha256: str


class SectorRotationSourceBoundBackend(AlphaPITBackendV1):
    """One-object backend exposing only the already-sealed ETF risk set."""

    def __init__(self, risk_set: ArtifactRef) -> None:
        self._risk_set = risk_set

    def risk_set(self, *, as_of: datetime, research_mode: ResearchMode) -> ArtifactRef:
        expected_as_of = as_of.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        if self._risk_set.manifest.get("as_of") != expected_as_of:
            raise ValueError("sra_source_backend_as_of_mismatch")
        if self._risk_set.manifest.get("research_mode") != ResearchMode(research_mode).value:
            raise ValueError("sra_source_backend_mode_mismatch")
        return self._risk_set

    def observations(self, **_: Any) -> ArtifactRef:
        raise ValueError("sra_source_backend_snapshot_observations_forbidden")

    def source_claims(self, **_: Any) -> ArtifactRef:
        raise ValueError("sra_source_backend_claims_forbidden")

    def expectations(self, **_: Any) -> ArtifactRef:
        raise ValueError("sra_source_backend_expectations_forbidden")

    def outcomes(self, **_: Any) -> ArtifactRef:
        raise ValueError("sra_source_backend_outcomes_forbidden")


def build_sector_rotation_source_production(
    *,
    as_of: datetime,
    decision_date: date | str,
    decision_context_id: str,
    research_mode: ResearchMode,
    risk_set_source_authority: Mapping[str, Any],
    risk_set_source_rows: Sequence[Mapping[str, Any]],
    risk_set_source_receipts: Sequence[Mapping[str, Any]],
    market_source_rows: Sequence[Mapping[str, Any]],
    market_source_receipts: Sequence[Mapping[str, Any]],
    fixture: bool = False,
) -> SectorRotationSourceProduction:
    """Close source bytes into the ETF-only input packet without outcome access."""

    mode = ResearchMode(research_mode)
    if mode is ResearchMode.DISCOVERY:
        raise ValueError("sra_source_discovery_mode_forbidden")
    cutoff = _timestamp_value(as_of, field="as_of")
    day = _date_value(decision_date, field="decision_date")
    completed_close = _require_completed_primary_close(cutoff=cutoff, decision_date=day)
    context = _nonempty_text(decision_context_id, field="decision_context_id")

    risk_receipts = _validate_receipts(
        risk_set_source_receipts,
        cutoff=cutoff,
        completed_close=completed_close,
        fixture=fixture,
        label="risk_set",
    )
    market_receipts = _validate_receipts(
        market_source_receipts,
        cutoff=cutoff,
        completed_close=completed_close,
        fixture=fixture,
        label="market",
    )
    risk_receipt_hashes = {str(row["raw_receipt_sha256"]) for row in risk_receipts}
    market_receipt_hashes = {str(row["raw_receipt_sha256"]) for row in market_receipts}
    authority = _validate_risk_set_authority(
        risk_set_source_authority,
        decision_date=day,
        receipt_hashes=risk_receipt_hashes,
    )
    risk_rows = _validate_risk_set_source_rows(
        risk_set_source_rows,
        cutoff=cutoff,
        decision_date=day,
        receipt_hashes=risk_receipt_hashes,
    )
    listing_by_security = {str(row["security_id"]): str(row["trading_item_id"]) for row in risk_rows}
    sector_by_security = {str(row["security_id"]): str(row["sector_key"]) for row in risk_rows}
    market_rows = _validate_market_source_rows(
        market_source_rows,
        listing_by_security=listing_by_security,
        sector_by_security=sector_by_security,
        decision_date=day,
        cutoff=cutoff,
        receipt_hashes=market_receipt_hashes,
    )

    risk_authority_sha = domain_hash(
        "SECTOR_ROTATION_ALPHA_V1:RISK_SET_SOURCE_AUTHORITY",
        canonical_value(authority),
    )
    risk_set_id = domain_hash(
        "SECTOR_ROTATION_ALPHA_V1:RISK_SET",
        canonical_value(
            {
                "family_id": FAMILY_ID,
                "risk_set_spec_id": RISK_SET_SPEC_ID,
                "as_of": _timestamp_text(cutoff),
                "source_authority_sha256": risk_authority_sha,
                "rows": risk_rows,
            }
        ),
    )
    risk_set = build_artifact_ref(
        artifact_type="RISK_SET",
        research_mode=mode,
        request={
            "family_id": FAMILY_ID,
            "risk_set_spec_id": RISK_SET_SPEC_ID,
            "as_of": _timestamp_text(cutoff),
            "decision_date": day.isoformat(),
            "source_authority_sha256": risk_authority_sha,
        },
        payload={
            "risk_set_id": risk_set_id,
            "family_id": FAMILY_ID,
            "risk_set_spec_id": RISK_SET_SPEC_ID,
            "as_of": _timestamp_text(cutoff),
            "source_authority": authority,
            "source_authority_sha256": risk_authority_sha,
            "rows": risk_rows,
            "row_count": len(risk_rows),
            "exclusion_counts": {},
        },
        as_of=cutoff,
        created_at=cutoff,
        risk_set_id=risk_set_id,
        source_receipts=risk_receipts,
        coverage_summary={
            "requested_security_count": len(EXPECTED_SECTOR_KEYS),
            "returned_security_count": len(risk_rows),
            "requested_field_count": None,
            "present_count": len(risk_rows),
            "missing_count": 0,
            "not_entitled_count": 0,
            "stale_count": 0,
            "coverage_rate": "1",
            "missingness_by_reason": {},
        },
        family_contract=FAMILY_DATA_CONTRACT,
        fixture=fixture,
    )

    market_history = build_artifact_ref(
        artifact_type=MARKET_HISTORY_ARTIFACT_TYPE,
        research_mode=mode,
        request={
            "risk_set_id": risk_set_id,
            "decision_session_date": day.isoformat(),
            "source_authority_sha256": domain_hash(
                "SECTOR_ROTATION_ALPHA_V1:MARKET_SOURCE_AUTHORITY",
                canonical_value(
                    {
                        "receipt_sha256s": sorted(market_receipt_hashes),
                        "decision_date": day.isoformat(),
                        "corporate_action_total_return_authority_bound": True,
                    }
                ),
            ),
        },
        payload={
            "schema_version": MARKET_HISTORY_SCHEMA,
            "family_id": FAMILY_ID,
            "risk_set_id": risk_set_id,
            "decision_session_date": day.isoformat(),
            "rows": market_rows,
            "row_count": len(market_rows),
        },
        as_of=cutoff,
        created_at=cutoff,
        risk_set_id=risk_set_id,
        source_receipts=market_receipts,
        coverage_summary={
            "requested_security_count": len(risk_rows),
            "returned_security_count": len(risk_rows),
            "requested_field_count": 3,
            "present_count": len(market_rows) * 3,
            "missing_count": 0,
            "not_entitled_count": 0,
            "stale_count": 0,
            "coverage_rate": "1",
            "missingness_by_reason": {},
        },
        family_contract=FAMILY_DATA_CONTRACT,
        fixture=fixture,
    )

    api = open_alpha_pit_session(
        mode=mode,
        family_id=FAMILY_ID,
        decision_context_id=context,
        backend=SectorRotationSourceBoundBackend(risk_set),
        family_contract=FAMILY_DATA_CONTRACT,
    )
    input_packet = build_sector_rotation_input_packet(
        api=api,
        market_history=market_history,
        implementation_id=IMPLEMENTATION_ID,
        as_of=cutoff,
    )
    production_body = {
        "schema_version": SOURCE_PRODUCTION_SCHEMA,
        "family_id": FAMILY_ID,
        "family_data_contract_sha256": FAMILY_DATA_CONTRACT_SHA256,
        "research_mode": mode.value,
        "decision_context_id": context,
        "decision_date": day.isoformat(),
        "as_of": _timestamp_text(cutoff),
        "risk_set_id": risk_set_id,
        "risk_set_manifest_sha256": risk_set.manifest_sha256,
        "market_history_manifest_sha256": market_history.manifest_sha256,
        "input_packet_sha256": str(input_packet["input_packet_sha256"]),
        "risk_set_source_receipt_sha256s": sorted(risk_receipt_hashes),
        "market_source_receipt_sha256s": sorted(market_receipt_hashes),
        "provider_acquisition_performed": False,
        "stock_sector_map_used": False,
        "stock_breadth_used": False,
        "underlying_stock_membership_used": False,
        "etf_flow_vendor_used": False,
        "financial_alpha_evidence": 0,
    }
    return SectorRotationSourceProduction(
        risk_set=risk_set,
        market_history=market_history,
        input_packet=input_packet,
        source_production_sha256=domain_hash(
            "SECTOR_ROTATION_ALPHA_V1:SOURCE_PRODUCTION",
            canonical_value(production_body),
        ),
    )


def _validate_risk_set_authority(
    raw: Mapping[str, Any],
    *,
    decision_date: date,
    receipt_hashes: set[str],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != RISK_SET_SOURCE_AUTHORITY_FIELDS:
        raise ValueError("sra_risk_set_source_authority_fields_invalid")
    authority = dict(raw)
    if authority.get("schema_version") != RISK_SET_SOURCE_AUTHORITY_SCHEMA:
        raise ValueError("sra_risk_set_source_authority_schema_invalid")
    if authority.get("family_id") != FAMILY_ID or authority.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise ValueError("sra_risk_set_source_authority_identity_invalid")
    if authority.get("capture_mode") != PROSPECTIVE_CAPTURE_MODE:
        raise ValueError("sra_risk_set_source_capture_mode_invalid")
    if _date_value(authority.get("decision_date"), field="source_authority_decision_date") != decision_date:
        raise ValueError("sra_risk_set_source_decision_date_mismatch")
    if authority.get("benchmark_family_id") != BENCHMARK_FAMILY_ID:
        raise ValueError("sra_risk_set_source_benchmark_family_invalid")
    if tuple(authority.get("expected_sector_keys") or ()) != EXPECTED_SECTOR_KEYS:
        raise ValueError("sra_risk_set_source_sector_keys_invalid")
    for field in (
        "stock_sector_map_used",
        "stock_breadth_used",
        "underlying_stock_membership_used",
        "current_survivor_back_projection_used",
        "alternate_listing_backfill_used",
        "legacy_identity_fallback_used",
        "etf_flow_vendor_used",
    ):
        if authority.get(field) is not False:
            raise ValueError("sra_risk_set_source_forbidden_flag:" + field)
    if authority.get("corporate_action_total_return_authority_bound") is not True:
        raise ValueError("sra_risk_set_source_total_return_authority_required")
    bound_hashes = authority.get("source_receipt_sha256s")
    if not isinstance(bound_hashes, list) or set(map(str, bound_hashes)) != receipt_hashes:
        raise ValueError("sra_risk_set_source_receipts_not_exact")
    authority["source_receipt_sha256s"] = sorted(receipt_hashes)
    return canonical_value(authority)


def _validate_risk_set_source_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    cutoff: datetime,
    decision_date: date,
    receipt_hashes: set[str],
) -> list[dict[str, Any]]:
    if len(rows) != len(EXPECTED_SECTOR_KEYS):
        raise ValueError("sra_risk_set_source_exact_11_rows_required")
    output: list[dict[str, Any]] = []
    security_ids: list[str] = []
    trading_items: list[str] = []
    primary_listing_ids: list[str] = []
    sector_keys: list[str] = []
    for raw in rows:
        if not isinstance(raw, Mapping) or set(raw) != RISK_SET_SOURCE_ROW_FIELDS:
            raise ValueError("sra_risk_set_source_row_fields_invalid")
        if raw.get("schema_version") != RISK_SET_SOURCE_ROW_SCHEMA:
            raise ValueError("sra_risk_set_source_row_schema_invalid")
        security_id = validate_security_ids([str(raw.get("security_id") or "")])[0]
        trading_item_id = _nonempty_text(raw.get("trading_item_id"), field="source_trading_item_id")
        primary_listing_id = _nonempty_text(raw.get("primary_listing_id"), field="source_primary_listing_id")
        sector_key = _nonempty_text(raw.get("sector_key"), field="source_sector_key")
        if sector_key not in EXPECTED_SECTOR_KEYS:
            raise ValueError("sra_risk_set_source_sector_key_invalid")
        if raw.get("benchmark_family_id") != BENCHMARK_FAMILY_ID:
            raise ValueError("sra_risk_set_source_benchmark_family_invalid")
        benchmark_membership_receipt_sha = str(raw.get("benchmark_membership_receipt_sha256") or "")
        if benchmark_membership_receipt_sha not in receipt_hashes:
            raise ValueError("sra_risk_set_source_benchmark_membership_receipt_unbound")
        if str(raw.get("instrument_type") or "").upper() != "ETF":
            raise ValueError("sra_risk_set_source_instrument_type_invalid")
        if str(raw.get("listing_country") or "").upper() != "US":
            raise ValueError("sra_risk_set_source_non_us_listing")
        for field in ("primary_listing", "active_tradable", "unique_security_mapping"):
            if raw.get(field) is not True:
                raise ValueError("sra_risk_set_source_required_true:" + field)
        membership = _timestamp_value(raw.get("membership_effective_at"), field="membership_effective_at")
        observed = _timestamp_value(raw.get("observed_at"), field="risk_observed_at")
        available = _timestamp_value(raw.get("available_at"), field="risk_available_at")
        if membership.date() != decision_date or observed.date() != decision_date:
            raise ValueError("sra_risk_set_source_not_same_day")
        if membership > observed or observed > available or available > cutoff:
            raise ValueError("sra_risk_set_source_time_order_invalid")
        source_receipt_sha = str(raw.get("source_receipt_sha256") or "")
        identity_receipt_sha = str(raw.get("identity_receipt_sha256") or "")
        if source_receipt_sha not in receipt_hashes or identity_receipt_sha not in receipt_hashes:
            raise ValueError("sra_risk_set_source_row_receipt_unbound")
        security_ids.append(security_id)
        trading_items.append(trading_item_id)
        primary_listing_ids.append(primary_listing_id)
        sector_keys.append(sector_key)
        output.append(
            canonical_value(
                {
                    "schema_version": "alpha_pit_risk_set_row_v1",
                    "security_id": security_id,
                    "sector_key": sector_key,
                    "benchmark_family_id": BENCHMARK_FAMILY_ID,
                    "benchmark_membership_receipt_sha256": benchmark_membership_receipt_sha,
                    "trading_item_id": trading_item_id,
                    "primary_listing_id": primary_listing_id,
                    "membership_effective_at": _timestamp_text(membership),
                    "observed_at": _timestamp_text(observed),
                    "available_at": _timestamp_text(available),
                    "source_id": _nonempty_text(raw.get("source_id"), field="risk_source_id"),
                    "source_receipt_sha256": source_receipt_sha,
                    "identity_receipt_sha256": identity_receipt_sha,
                    "eligibility_status": "ELIGIBLE",
                    "sra_source_proof": {
                        "instrument_type": "ETF",
                        "listing_country": "US",
                        "primary_listing": True,
                        "active_tradable": True,
                        "unique_security_mapping": True,
                        "benchmark_family_id": BENCHMARK_FAMILY_ID,
                    },
                }
            )
        )
    validate_security_ids(security_ids)
    if len(set(security_ids)) != len(security_ids):
        raise ValueError("sra_risk_set_source_duplicate_security_id")
    if len(set(trading_items)) != len(trading_items):
        raise ValueError("sra_risk_set_source_duplicate_trading_item_id")
    if len(set(primary_listing_ids)) != len(primary_listing_ids):
        raise ValueError("sra_risk_set_source_duplicate_primary_listing_id")
    if set(sector_keys) != set(EXPECTED_SECTOR_KEYS) or len(set(sector_keys)) != len(EXPECTED_SECTOR_KEYS):
        raise ValueError("sra_risk_set_source_sector_set_not_exact")
    return sorted(output, key=lambda row: str(row["sector_key"]))


def _validate_market_source_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    listing_by_security: Mapping[str, str],
    sector_by_security: Mapping[str, str],
    decision_date: date,
    cutoff: datetime,
    receipt_hashes: set[str],
) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("sra_market_source_rows_required")
    counts = {security_id: 0 for security_id in listing_by_security}
    latest_dates: dict[str, date] = {}
    seen: set[tuple[str, date]] = set()
    output: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, Mapping) or set(raw) != MARKET_SOURCE_ROW_FIELDS:
            raise ValueError("sra_market_source_row_fields_invalid")
        if raw.get("schema_version") != MARKET_SOURCE_ROW_SCHEMA:
            raise ValueError("sra_market_source_row_schema_invalid")
        security_id = validate_security_ids([str(raw.get("security_id") or "")])[0]
        if security_id not in listing_by_security:
            raise ValueError("sra_market_source_security_outside_risk_set")
        trading_item_id = _nonempty_text(raw.get("trading_item_id"), field="market_trading_item_id")
        if trading_item_id != listing_by_security[security_id]:
            raise ValueError("sra_market_source_trading_item_mismatch")
        sector_key = _nonempty_text(raw.get("sector_key"), field="market_sector_key")
        if sector_key != sector_by_security[security_id]:
            raise ValueError("sra_market_source_sector_binding_invalid")
        session_date = _date_value(raw.get("session_date"), field="market_session_date")
        if session_date > decision_date:
            raise ValueError("sra_market_source_after_decision_date")
        key = (security_id, session_date)
        if key in seen:
            raise ValueError("sra_market_source_duplicate_security_session")
        seen.add(key)
        observed = _timestamp_value(raw.get("observed_at"), field="market_observed_at")
        available = _timestamp_value(raw.get("available_at"), field="market_available_at")
        if observed > available or available > cutoff:
            raise ValueError("sra_market_source_time_order_invalid")
        close = _finite(raw.get("close"), field="market_close")
        total_return = _finite(raw.get("total_return_1d"), field="market_total_return_1d")
        volume = _finite(raw.get("volume"), field="market_volume")
        if close <= 0:
            raise ValueError("sra_market_source_close_must_be_positive")
        if total_return <= -1:
            raise ValueError("sra_market_source_total_return_below_minus_one")
        if volume <= 0:
            raise ValueError("sra_market_source_volume_must_be_positive")
        source_receipt_sha = str(raw.get("source_receipt_sha256") or "")
        if source_receipt_sha not in receipt_hashes:
            raise ValueError("sra_market_source_row_receipt_unbound")
        _nonempty_text(raw.get("source_id"), field="market_source_id")
        counts[security_id] += 1
        latest_dates[security_id] = max(latest_dates.get(security_id, session_date), session_date)
        output.append(
            {
                "security_id": security_id,
                "sector_key": sector_key,
                "session_date": session_date.isoformat(),
                "close": format(close, ".17g"),
                "total_return_1d": format(total_return, ".17g"),
                "volume": format(volume, ".17g"),
                "observed_at": _timestamp_text(observed),
                "available_at": _timestamp_text(available),
                "coverage_status": "PRESENT",
            }
        )
    for security_id in sorted(listing_by_security):
        if counts.get(security_id, 0) < MIN_HISTORY_SESSIONS:
            raise ValueError("sra_market_source_insufficient_60_session_history:" + security_id)
        if latest_dates.get(security_id) != decision_date:
            raise ValueError("sra_market_source_decision_session_missing:" + security_id)
    return sorted(output, key=lambda row: (str(row["sector_key"]), str(row["session_date"])))


def _validate_receipts(
    receipts: Sequence[Mapping[str, Any]],
    *,
    cutoff: datetime,
    completed_close: datetime,
    fixture: bool,
    label: str,
) -> list[dict[str, Any]]:
    if not receipts:
        raise ValueError(f"sra_{label}_source_receipts_required")
    output: list[dict[str, Any]] = []
    hashes: set[str] = set()
    for raw in receipts:
        if not isinstance(raw, Mapping):
            raise ValueError(f"sra_{label}_source_receipt_mapping_required")
        binding = dict(raw)
        validate_source_receipt_binding(binding)
        provider = str(binding.get("provider") or "").strip().upper()
        if fixture:
            if provider != FIXTURE_PROVIDER_NAME:
                raise ValueError(f"sra_{label}_fixture_provider_invalid")
        elif provider not in REAL_PROVIDER_NAMES:
            raise ValueError(f"sra_{label}_provider_not_ciq")
        retrieved_at = _timestamp_value(binding.get("retrieved_at"), field=f"{label}_retrieved_at")
        if retrieved_at > cutoff:
            raise ValueError(f"sra_{label}_source_retrieved_after_as_of")
        if retrieved_at < completed_close:
            raise ValueError(f"sra_{label}_source_retrieved_before_completed_close")
        digest = str(binding["raw_receipt_sha256"])
        if digest in hashes:
            raise ValueError(f"sra_{label}_source_receipt_duplicate")
        hashes.add(digest)
        output.append(canonical_value(binding))
    return sorted(output, key=lambda row: str(row["raw_receipt_sha256"]))


def _require_completed_primary_close(*, cutoff: datetime, decision_date: date) -> datetime:
    local_cutoff = cutoff.astimezone(NYSE_TZ)
    if decision_date.year != 2026:
        raise ValueError("sra_source_execution_calendar_out_of_scope")
    if decision_date != local_cutoff.date():
        raise ValueError("sra_source_decision_date_must_match_nyse_local_as_of_date")
    if decision_date.weekday() >= 5 or decision_date.isoformat() in NYSE_2026_CLOSED_DATES:
        raise ValueError("sra_source_decision_date_not_admitted_nyse_session")
    completed_close = datetime.combine(decision_date, CONSERVATIVE_PRIMARY_CLOSE, tzinfo=NYSE_TZ).astimezone(timezone.utc)
    if cutoff < completed_close:
        raise ValueError("sra_source_primary_close_not_completed")
    return completed_close


def _date_value(value: Any, *, field: str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value or ""))
    except ValueError as exc:
        raise ValueError(f"sra_{field}_invalid") from exc


def _timestamp_value(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"sra_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"sra_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _nonempty_text(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"sra_{field}_required")
    return text


def _finite(value: Any, *, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"sra_{field}_finite_required") from exc
    if not isfinite(parsed):
        raise ValueError(f"sra_{field}_finite_required")
    return parsed
