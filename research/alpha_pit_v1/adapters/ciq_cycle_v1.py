"""Concrete Capital IQ producer for ``alpha_pit_data_api_v1``.

The adapter is intentionally narrow and source-explicit.  It can canonicalize
landed current-cut CIQ market/fundamental custody immediately, but it will not
pretend the AOV growth-screen 109 is the CRV1 date-local risk set.  ``risk_set``
therefore requires a separately captured CRV1 risk-set source artifact whose
receipt explicitly declares ``CRV1_US_PRIMARY_COMMON_V1`` and no growth screen.

Current AOV market/fundamental custody is also deliberately *not* reused as
historical PIT authority: those sources are admitted only for ``as_of`` values
on or after their conservative current-cut availability boundary.  Historical
CIQ as-of captures can be added later without weakening this rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    EXPECTATION_MEASURES,
    FAMILY_ID,
    RISK_SET_SPEC_ID,
    AlphaPITContractError,
    ArtifactRef,
    ResearchMode,
    hash_safe,
    iso_utc,
    validate_security_ids,
)
from research.alpha_pit_v1.manifests import build_artifact_ref
from research.aov0.contracts import normalize_security_id


CIQ_PROVIDER = "S&P Capital IQ Pro"
CIQ_RISK_SET_SOURCE_ID = "SPCIQPRO:CRV1_US_PRIMARY_COMMON_RISK_SET"
CIQ_EXPECTATIONS_SOURCE_ID = "SPCIQPRO:CRV1_EXPECTATIONS"
RISK_SET_SOURCE_SCHEMA = "alpha_pit_ciq_crv1_risk_set_source_v1"
RISK_SET_RECEIPT_SCHEMA = "alpha_pit_ciq_crv1_risk_set_source_receipt_v1"
EXPECTATIONS_SOURCE_SCHEMA = "alpha_pit_ciq_expectations_source_v1"
EXPECTATIONS_RECEIPT_SCHEMA = "alpha_pit_ciq_expectations_source_receipt_v1"
RISK_SET_ELIGIBILITY_CONTRACT_ID = "CRV1_US_PRIMARY_COMMON_ELIGIBILITY_V1"
RISK_SET_ELIGIBILITY_CONTRACT = {
    "listing_country": "US",
    "primary_listing_required": True,
    "security_class": "COMMON_EQUITY",
    "trading_status": "ACTIVE_TRADABLE",
    "unique_permanent_identity_required": True,
    "minimum_prior_market_observations": 200,
    "growth_screen_allowed": False,
    "current_survivor_filter_allowed": False,
    "future_membership_filter_allowed": False,
}
RISK_SET_ELIGIBILITY_CONTRACT_SHA256 = domain_hash(
    "ALPHA_PIT_V1:CRV1_RISK_SET_ELIGIBILITY_CONTRACT",
    RISK_SET_ELIGIBILITY_CONTRACT,
)

MARKET_SOURCE_ID = "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA"
FUNDAMENTAL_SOURCE_ID = "SPCIQPRO:QUARTERLY_FUNDAMENTALS"
IDENTITY_SOURCE_ID = "SPCIQPRO:PRIMARY_SECURITY_MASTER"
CRV1_IDENTITY_RECEIPT_SCHEMA = "alpha_pit_ciq_crv1_primary_security_master_receipt_v1"
CRV1_MARKET_RECEIPT_SCHEMA = "alpha_pit_ciq_crv1_primary_security_market_data_receipt_v1"
CRV1_FUNDAMENTAL_RECEIPT_SCHEMA = "alpha_pit_ciq_crv1_quarterly_fundamentals_receipt_v1"
CRV1_STRUCTURED_SOURCE_SCOPE = "CRV1_INDEPENDENT_NON_GROWTH_STRUCTURED_CUSTODY_V1"
CRV1_FUNDAMENTALS_MISSING_REASON = "CIQ_CRV1_FUNDAMENTALS_CAPTURE_NOT_LANDED"

MARKET_FIELDS = {
    "market.close",
    "market.total_return_1d",
    "market.volume",
    "market.adv20",
    "market.realized_vol20",
    "market.sma20",
    "market.sma200",
}
FUNDAMENTAL_FIELDS = {
    "fund.revenue_q",
    "fund.inventory_q",
    "fund.capex_q",
    "fund.gross_margin_q",
    "fund.operating_margin_q",
    "fund.cash_from_ops_q",
}
FUNDAMENTAL_COLUMN_MAP = {
    "fund.revenue_q": "total_revenue_q",
    "fund.inventory_q": "inventory_q",
    "fund.capex_q": "capex_q",
    "fund.operating_margin_q": "operating_margin_q",
}
FUNDAMENTAL_GLOBAL_MISSING = {
    "fund.gross_margin_q": "RUN4_CUSTODY_HAS_NO_GROSS_MARGIN_INPUT",
    "fund.cash_from_ops_q": "RUN4_CUSTODY_HAS_NO_CASH_FROM_OPERATIONS_INPUT",
}


@dataclass(frozen=True)
class _Receipt:
    path: Path
    payload: Mapping[str, Any]
    sha256: str
    binding: Mapping[str, Any]

    @property
    def retrieved_at(self) -> datetime:
        raw = str(self.binding["retrieved_at"])
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)


class CiqCycleV1Adapter:
    """First-family CIQ adapter; no registry, fallback chain, or legacy identity."""

    def __init__(
        self,
        *,
        security_master_path: str | Path,
        security_master_receipt_path: str | Path,
        market_history_path: str | Path,
        market_receipt_path: str | Path,
        fundamental_panel_path: str | Path | None = None,
        fundamental_receipt_path: str | Path | None = None,
        risk_set_source_path: str | Path | None = None,
        risk_set_receipt_path: str | Path | None = None,
        expectations_source_path: str | Path | None = None,
        expectations_receipt_path: str | Path | None = None,
    ) -> None:
        self._parser_sha256 = _sha256_file(Path(__file__))
        self._security_master_path = Path(security_master_path)
        self._market_history_path = Path(market_history_path)
        if (fundamental_panel_path is None) != (fundamental_receipt_path is None):
            raise AlphaPITContractError("alpha_pit_ciq_fundamental_source_pair_required")
        self._fundamental_panel_path = Path(fundamental_panel_path) if fundamental_panel_path is not None else None

        self._identity_receipt = self._load_current_receipt(
            path=Path(security_master_receipt_path),
            source_id=IDENTITY_SOURCE_ID,
            observed_range=(None, None),
            parser_id="CIQCycleV1Adapter:identity_v1",
        )
        self._market_receipt = self._load_current_receipt(
            path=Path(market_receipt_path),
            source_id=MARKET_SOURCE_ID,
            observed_range=None,
            parser_id="CIQCycleV1Adapter:market_v1",
        )
        self._fundamental_receipt = (
            self._load_current_receipt(
                path=Path(fundamental_receipt_path),
                source_id=FUNDAMENTAL_SOURCE_ID,
                observed_range=None,
                parser_id="CIQCycleV1Adapter:fundamentals_v1",
            )
            if fundamental_receipt_path is not None
            else None
        )

        self._verify_current_custody()
        self._master = self._load_master()
        self._market = self._load_market()
        self._fundamentals = self._load_fundamentals() if self._fundamental_panel_path is not None else None

        if (risk_set_source_path is None) != (risk_set_receipt_path is None):
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_source_pair_required")
        self._risk_set_source_path = Path(risk_set_source_path) if risk_set_source_path is not None else None
        self._risk_set_receipt = (
            self._load_special_receipt(
                path=Path(risk_set_receipt_path),
                expected_schema=RISK_SET_RECEIPT_SCHEMA,
                source_id=CIQ_RISK_SET_SOURCE_ID,
                source_path=self._risk_set_source_path,
                parser_id="CIQCycleV1Adapter:risk_set_v1",
            )
            if risk_set_receipt_path is not None
            else None
        )
        if self._risk_set_receipt is not None:
            _validate_crv1_structured_receipt_contract(
                self._identity_receipt.payload,
                expected_schema=CRV1_IDENTITY_RECEIPT_SCHEMA,
                label="identity",
            )
            _validate_crv1_structured_receipt_contract(
                self._market_receipt.payload,
                expected_schema=CRV1_MARKET_RECEIPT_SCHEMA,
                label="market",
            )
            if self._fundamental_receipt is not None:
                _validate_crv1_structured_receipt_contract(
                    self._fundamental_receipt.payload,
                    expected_schema=CRV1_FUNDAMENTAL_RECEIPT_SCHEMA,
                    label="fundamentals",
                )

        if (expectations_source_path is None) != (expectations_receipt_path is None):
            raise AlphaPITContractError("alpha_pit_ciq_expectations_source_pair_required")
        self._expectations_source_path = (
            Path(expectations_source_path) if expectations_source_path is not None else None
        )
        self._expectations_receipt = (
            self._load_special_receipt(
                path=Path(expectations_receipt_path),
                expected_schema=EXPECTATIONS_RECEIPT_SCHEMA,
                source_id=CIQ_EXPECTATIONS_SOURCE_ID,
                source_path=self._expectations_source_path,
                parser_id="CIQCycleV1Adapter:expectations_v1",
            )
            if expectations_receipt_path is not None
            else None
        )
        self._expectations = self._load_expectations() if self._expectations_source_path is not None else None

    @property
    def custody_verified_at(self) -> datetime:
        return max(
            self._identity_receipt.retrieved_at,
            self._market_receipt.retrieved_at,
            *([self._fundamental_receipt.retrieved_at] if self._fundamental_receipt is not None else []),
            *([self._risk_set_receipt.retrieved_at] if self._risk_set_receipt is not None else []),
            *([self._expectations_receipt.retrieved_at] if self._expectations_receipt is not None else []),
        )

    def risk_set(self, *, as_of: datetime, research_mode: ResearchMode) -> ArtifactRef:
        cutoff = _aware(as_of)
        if self._risk_set_source_path is None or self._risk_set_receipt is None:
            raise AlphaPITContractError("alpha_pit_crv1_risk_set_source_not_landed")

        self._require_current_cut_available(self._identity_receipt, cutoff, "identity")
        self._require_current_cut_available(self._market_receipt, cutoff, "market")
        source = _load_json(self._risk_set_source_path)
        if source.get("schema_version") != RISK_SET_SOURCE_SCHEMA:
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_source_schema_invalid")
        if source.get("family_id") != FAMILY_ID or source.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_contract_invalid")
        _validate_risk_set_source_contract(source)
        source_as_of = _parse_timestamp(source.get("as_of"), field="risk_set_source_as_of")
        if source_as_of != cutoff:
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_as_of_exact_match_required")

        rows_raw = source.get("rows")
        if not isinstance(rows_raw, list) or not rows_raw:
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_rows_required")
        receipt_hash = self._risk_set_receipt.sha256
        identity_receipt_sha256 = str(self._risk_set_receipt.payload["identity_receipt_sha256"])
        if str(source.get("identity_receipt_sha256") or "") != identity_receipt_sha256:
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_identity_receipt_binding_mismatch")
        if identity_receipt_sha256 != self._identity_receipt.sha256:
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_not_bound_to_structured_identity_receipt")
        master_by_security = self._master.set_index("security_id", drop=False)
        market_available = self._market.loc[
            self._market["date"].dt.date <= cutoff.date()
        ].copy()
        market_available["complete"] = market_available[["close", "volume", "total_return"]].notna().all(axis=1)
        complete_history_counts = (
            market_available.loc[market_available["complete"]]
            .groupby("security_id")
            .size()
            .to_dict()
        )
        rows: list[dict[str, Any]] = []
        security_ids: list[str] = []
        for raw in rows_raw:
            if not isinstance(raw, Mapping):
                raise AlphaPITContractError("alpha_pit_ciq_risk_set_row_mapping_required")
            security_id = normalize_security_id(str(raw.get("security_id") or ""))
            security_ids.append(security_id)
            if security_id not in master_by_security.index:
                raise AlphaPITContractError("alpha_pit_ciq_risk_set_security_outside_structured_identity_source")
            master_row = master_by_security.loc[security_id]
            if str(raw.get("trading_item_id") or "").strip() != str(master_row["trading_item_id"]):
                raise AlphaPITContractError("alpha_pit_ciq_risk_set_trading_item_not_bound_to_structured_identity")
            company_id = _optional_text(raw.get("company_id"))
            if company_id is not None:
                normalized_company = company_id.removeprefix("COMPANY:")
                if normalized_company != str(master_row["source_entity_id"]):
                    raise AlphaPITContractError("alpha_pit_ciq_risk_set_company_not_bound_to_structured_identity")
            membership_effective = _parse_timestamp(
                raw.get("membership_effective_at"), field="membership_effective_at"
            )
            observed = _parse_timestamp(raw.get("observed_at"), field="risk_set_observed_at")
            available = _parse_timestamp(raw.get("available_at"), field="risk_set_available_at")
            if not (membership_effective <= cutoff and observed <= available <= cutoff):
                raise AlphaPITContractError("alpha_pit_ciq_risk_set_temporal_contract_invalid")
            _validate_risk_set_row_eligibility(raw)
            declared_history_count = int(raw["prior_market_observation_count"])
            actual_history_count = int(complete_history_counts.get(security_id, 0))
            if declared_history_count != actual_history_count:
                raise AlphaPITContractError("alpha_pit_ciq_risk_set_market_history_count_not_source_derived")
            row = {
                "security_id": security_id,
                "company_id": company_id,
                "trading_item_id": _optional_text(raw.get("trading_item_id")),
                "primary_listing_id": _optional_text(raw.get("primary_listing_id")),
                "membership_effective_at": iso_utc(membership_effective),
                "observed_at": iso_utc(observed),
                "available_at": iso_utc(available),
                "source_id": CIQ_RISK_SET_SOURCE_ID,
                "source_receipt_sha256": receipt_hash,
                "identity_receipt_sha256": identity_receipt_sha256,
                "eligibility_status": "ELIGIBLE",
                "schema_version": "alpha_pit_risk_set_row_v1",
            }
            rows.append(row)
        validate_security_ids(security_ids)
        if len(set(security_ids)) != len(security_ids):
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_security_collision")
        rows = sorted(rows, key=lambda row: row["security_id"])
        exclusion_counts = source.get("exclusion_counts") or {}
        if not isinstance(exclusion_counts, Mapping):
            raise AlphaPITContractError("alpha_pit_ciq_risk_set_exclusion_counts_invalid")

        risk_set_id = domain_hash(
            "ALPHA_PIT_V1:CIQ:RISK_SET",
            {
                "family_id": FAMILY_ID,
                "risk_set_spec_id": RISK_SET_SPEC_ID,
                "as_of": iso_utc(cutoff),
                "rows": rows,
                "exclusion_counts": dict(sorted((str(k), int(v)) for k, v in exclusion_counts.items())),
            },
        )
        payload = {
            "risk_set_id": risk_set_id,
            "family_id": FAMILY_ID,
            "risk_set_spec_id": RISK_SET_SPEC_ID,
            "as_of": iso_utc(cutoff),
            "rows": rows,
            "row_count": len(rows),
            "exclusion_counts": dict(sorted((str(k), int(v)) for k, v in exclusion_counts.items())),
            "coverage_summary": _coverage(
                requested_security_count=len(rows),
                requested_item_count=len(rows),
                present_count=len(rows),
                missing_reasons={},
            ),
        }
        return build_artifact_ref(
            artifact_type="RISK_SET",
            research_mode=research_mode,
            request={"as_of": iso_utc(cutoff)},
            payload=payload,
            as_of=cutoff,
            created_at=_max_retrieved([self._risk_set_receipt]),
            risk_set_id=risk_set_id,
            source_receipts=[self._risk_set_receipt.binding],
            coverage_summary=payload["coverage_summary"],
        )

    def observations(
        self,
        *,
        ids: Sequence[str],
        fields: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        cutoff = _aware(as_of)
        security_ids = validate_security_ids(ids)
        requested_fields = tuple(str(field) for field in fields)
        unknown = set(requested_fields) - (MARKET_FIELDS | FUNDAMENTAL_FIELDS)
        if unknown:
            raise AlphaPITContractError("alpha_pit_ciq_observation_field_unsupported:" + ",".join(sorted(unknown)))
        self._require_known_ids(security_ids)

        uses_market = bool(set(requested_fields) & MARKET_FIELDS)
        uses_fundamentals = bool(set(requested_fields) & FUNDAMENTAL_FIELDS)
        receipts: list[_Receipt] = [self._identity_receipt]
        missing_fundamental_binding: dict[str, Any] | None = None
        if uses_market:
            self._require_current_cut_available(self._market_receipt, cutoff, "market")
            receipts.append(self._market_receipt)
        if uses_fundamentals:
            if self._fundamental_receipt is not None:
                self._require_current_cut_available(self._fundamental_receipt, cutoff, "fundamentals")
                receipts.append(self._fundamental_receipt)
            else:
                missing_fundamental_binding = _missing_source_binding(
                    source_id=FUNDAMENTAL_SOURCE_ID,
                    reason=CRV1_FUNDAMENTALS_MISSING_REASON,
                    retrieved_at=cutoff,
                    parser_sha256=self._parser_sha256,
                    parser_id="CIQCycleV1Adapter:fundamentals_missing_v1",
                )

        rows: list[dict[str, Any]] = []
        missing_reasons: dict[str, int] = {}
        for security_id in security_ids:
            for field_id in requested_fields:
                if field_id in MARKET_FIELDS:
                    row = self._market_observation(security_id=security_id, field_id=field_id, as_of=cutoff)
                else:
                    row = self._fundamental_observation(
                        security_id=security_id,
                        field_id=field_id,
                        as_of=cutoff,
                        missing_receipt_sha256=(
                            str(missing_fundamental_binding["raw_receipt_sha256"])
                            if missing_fundamental_binding is not None
                            else None
                        ),
                    )
                rows.append(row)
                if row["coverage_status"] != "PRESENT":
                    reason = str(row["missingness_reason"])
                    missing_reasons[reason] = missing_reasons.get(reason, 0) + 1

        present_count = sum(row["coverage_status"] == "PRESENT" for row in rows)
        coverage = _coverage(
            requested_security_count=len(security_ids),
            requested_item_count=len(rows),
            requested_field_count=len(requested_fields),
            present_count=present_count,
            missing_reasons=missing_reasons,
        )
        return build_artifact_ref(
            artifact_type="OBSERVATIONS",
            research_mode=research_mode,
            request={"ids": list(security_ids), "fields": list(requested_fields), "as_of": iso_utc(cutoff)},
            payload={"family_id": FAMILY_ID, "as_of": iso_utc(cutoff), "rows": rows, "row_count": len(rows)},
            as_of=cutoff,
            created_at=(
                max(_max_retrieved(receipts), cutoff)
                if missing_fundamental_binding is not None
                else _max_retrieved(receipts)
            ),
            source_receipts=[
                *[receipt.binding for receipt in _dedupe_receipts(receipts)],
                *([missing_fundamental_binding] if missing_fundamental_binding is not None else []),
            ],
            coverage_summary=coverage,
        )

    def expectations(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        cutoff = _aware(as_of)
        security_ids = validate_security_ids(ids)
        self._require_known_ids(security_ids)

        if self._expectations is None or self._expectations_receipt is None:
            sentinel = _missing_source_binding(
                source_id=CIQ_EXPECTATIONS_SOURCE_ID,
                reason="CIQ_EXPECTATIONS_CAPTURE_NOT_LANDED",
                retrieved_at=cutoff,
                parser_sha256=self._parser_sha256,
                parser_id="CIQCycleV1Adapter:expectations_missing_v1",
            )
            rows = [
                _expectation_row(
                    security_id=security_id,
                    measure=measure,
                    value=None,
                    unit=None,
                    forecast_period_end=None,
                    observed_at=cutoff,
                    available_at=cutoff,
                    source_id=CIQ_EXPECTATIONS_SOURCE_ID,
                    receipt_sha256=str(sentinel["raw_receipt_sha256"]),
                    coverage_status="MISSING_SOURCE",
                    missingness_reason="CIQ_EXPECTATIONS_CAPTURE_NOT_LANDED",
                )
                for security_id in security_ids
                for measure in EXPECTATION_MEASURES
            ]
            missing = len(rows)
            coverage = _coverage(
                requested_security_count=len(security_ids),
                requested_item_count=missing,
                requested_field_count=len(EXPECTATION_MEASURES),
                present_count=0,
                missing_reasons={"CIQ_EXPECTATIONS_CAPTURE_NOT_LANDED": missing},
            )
            return build_artifact_ref(
                artifact_type="EXPECTATIONS",
                research_mode=research_mode,
                request={"ids": list(security_ids), "as_of": iso_utc(cutoff)},
                payload={"family_id": FAMILY_ID, "as_of": iso_utc(cutoff), "rows": rows, "row_count": len(rows)},
                as_of=cutoff,
                created_at=str(sentinel["retrieved_at"]),
                source_receipts=[sentinel],
                coverage_summary=coverage,
            )

        receipt = self._expectations_receipt
        frame = self._expectations
        rows: list[dict[str, Any]] = []
        missing_reasons: dict[str, int] = {}
        for security_id in security_ids:
            for measure in EXPECTATION_MEASURES:
                candidates = frame.loc[
                    frame["security_id"].eq(security_id)
                    & frame["measure"].eq(measure)
                    & frame["available_at"].le(pd.Timestamp(cutoff))
                ].sort_values(["available_at", "observed_at"])
                if candidates.empty:
                    row = _expectation_row(
                        security_id=security_id,
                        measure=measure,
                        value=None,
                        unit=None,
                        forecast_period_end=None,
                        observed_at=cutoff,
                        available_at=cutoff,
                        source_id=CIQ_EXPECTATIONS_SOURCE_ID,
                        receipt_sha256=receipt.sha256,
                        coverage_status="MISSING_HISTORY",
                        missingness_reason="NO_EXPECTATION_AVAILABLE_AT_AS_OF",
                    )
                else:
                    current = candidates.iloc[-1]
                    value = current["value"]
                    status = "PRESENT" if pd.notna(value) else str(current["coverage_status"])
                    reason = None if status == "PRESENT" else str(current.get("missingness_reason") or "EXPECTATION_VALUE_MISSING")
                    row = _expectation_row(
                        security_id=security_id,
                        measure=measure,
                        value=float(value) if pd.notna(value) else None,
                        unit=_optional_text(current.get("unit")),
                        forecast_period_end=_optional_text(current.get("forecast_period_end")),
                        observed_at=current["observed_at"].to_pydatetime(),
                        available_at=current["available_at"].to_pydatetime(),
                        source_id=CIQ_EXPECTATIONS_SOURCE_ID,
                        receipt_sha256=receipt.sha256,
                        coverage_status=status,
                        missingness_reason=reason,
                    )
                rows.append(row)
                if row["coverage_status"] != "PRESENT":
                    reason = str(row["missingness_reason"])
                    missing_reasons[reason] = missing_reasons.get(reason, 0) + 1

        present_count = sum(row["coverage_status"] == "PRESENT" for row in rows)
        coverage = _coverage(
            requested_security_count=len(security_ids),
            requested_item_count=len(rows),
            requested_field_count=len(EXPECTATION_MEASURES),
            present_count=present_count,
            missing_reasons=missing_reasons,
        )
        return build_artifact_ref(
            artifact_type="EXPECTATIONS",
            research_mode=research_mode,
            request={"ids": list(security_ids), "as_of": iso_utc(cutoff)},
            payload={"family_id": FAMILY_ID, "as_of": iso_utc(cutoff), "rows": rows, "row_count": len(rows)},
            as_of=cutoff,
            created_at=receipt.retrieved_at,
            source_receipts=[receipt.binding],
            coverage_summary=coverage,
        )

    def _market_observation(self, *, security_id: str, field_id: str, as_of: datetime) -> dict[str, Any]:
        source = self._market_receipt
        group = self._market.loc[self._market["security_id"].eq(security_id)].sort_values("date")
        receipt_time = source.retrieved_at
        if group.empty:
            return _observation_row(
                security_id=security_id,
                field_id=field_id,
                value=None,
                unit=_market_unit(field_id),
                period_end=None,
                effective_at=None,
                observed_at=receipt_time,
                available_at=receipt_time,
                source_id=MARKET_SOURCE_ID,
                receipt_sha256=source.sha256,
                coverage_status="MISSING_HISTORY",
                missingness_reason="NO_CURRENT_CUSTODY_MARKET_HISTORY",
            )
        latest = group.iloc[-1]
        period_end = pd.Timestamp(latest["date"]).date().isoformat()
        effective_at = pd.Timestamp(latest["date"]).tz_localize("UTC").isoformat().replace("+00:00", "Z")
        values = group[["close", "volume", "total_return"]].apply(pd.to_numeric, errors="coerce")
        value: float | None
        reason: str | None = None
        if field_id == "market.close":
            value = _finite_or_none(latest["close"])
        elif field_id == "market.total_return_1d":
            raw = _finite_or_none(latest["total_return"])
            value = None if raw is None else raw / 100.0
        elif field_id == "market.volume":
            value = _finite_or_none(latest["volume"])
        elif field_id == "market.adv20":
            tail = values.assign(dollar_volume=values["close"] * values["volume"])["dollar_volume"].dropna().tail(20)
            value = float(tail.mean()) if len(tail) == 20 else None
            reason = None if value is not None else "INSUFFICIENT_20D_MARKET_HISTORY"
        elif field_id == "market.realized_vol20":
            tail = (values["total_return"] / 100.0).dropna().tail(20)
            value = float(tail.std(ddof=1) * np.sqrt(252.0)) if len(tail) == 20 else None
            reason = None if value is not None else "INSUFFICIENT_20D_MARKET_HISTORY"
        elif field_id == "market.sma20":
            tail = values["close"].dropna().tail(20)
            value = float(tail.mean()) if len(tail) == 20 else None
            reason = None if value is not None else "INSUFFICIENT_20D_MARKET_HISTORY"
        elif field_id == "market.sma200":
            tail = values["close"].dropna().tail(200)
            value = float(tail.mean()) if len(tail) == 200 else None
            reason = None if value is not None else "INSUFFICIENT_200D_MARKET_HISTORY"
        else:  # pragma: no cover - guarded by caller
            raise AlphaPITContractError("alpha_pit_ciq_market_field_unreachable")
        if value is None and reason is None:
            reason = "CURRENT_MARKET_VALUE_MISSING"
        return _observation_row(
            security_id=security_id,
            field_id=field_id,
            value=value,
            unit=_market_unit(field_id),
            period_end=period_end,
            effective_at=effective_at,
            observed_at=receipt_time,
            available_at=receipt_time,
            source_id=MARKET_SOURCE_ID,
            receipt_sha256=source.sha256,
            coverage_status="PRESENT" if value is not None else "MISSING_HISTORY",
            missingness_reason=reason,
        )

    def _fundamental_observation(
        self,
        *,
        security_id: str,
        field_id: str,
        as_of: datetime,
        missing_receipt_sha256: str | None = None,
    ) -> dict[str, Any]:
        source = self._fundamental_receipt
        entity_id = self._security_to_entity[security_id]
        if source is None or self._fundamentals is None:
            return _observation_row(
                security_id=security_id,
                field_id=field_id,
                value=None,
                unit=_fundamental_unit(field_id),
                period_end=None,
                effective_at=None,
                observed_at=as_of,
                available_at=as_of,
                source_id=FUNDAMENTAL_SOURCE_ID,
                receipt_sha256=(
                    missing_receipt_sha256
                    if missing_receipt_sha256 is not None
                    else domain_hash(
                        "ALPHA_PIT_V1:CRV1:FUNDAMENTALS_MISSING",
                        {"security_id": security_id, "as_of": iso_utc(as_of)},
                    )
                ),
                coverage_status="MISSING_SOURCE",
                missingness_reason=CRV1_FUNDAMENTALS_MISSING_REASON,
            )
        if field_id in FUNDAMENTAL_GLOBAL_MISSING:
            return _observation_row(
                security_id=security_id,
                field_id=field_id,
                value=None,
                unit=_fundamental_unit(field_id),
                period_end=None,
                effective_at=None,
                observed_at=source.retrieved_at,
                available_at=source.retrieved_at,
                source_id=FUNDAMENTAL_SOURCE_ID,
                receipt_sha256=source.sha256,
                coverage_status="MISSING_SOURCE",
                missingness_reason=FUNDAMENTAL_GLOBAL_MISSING[field_id],
            )
        candidates = self._fundamentals.loc[
            self._fundamentals["source_entity_id"].eq(entity_id)
            & self._fundamentals["known_at"].le(pd.Timestamp(as_of))
        ].sort_values(["period_end", "known_at"])
        if candidates.empty:
            return _observation_row(
                security_id=security_id,
                field_id=field_id,
                value=None,
                unit=_fundamental_unit(field_id),
                period_end=None,
                effective_at=None,
                observed_at=source.retrieved_at,
                available_at=source.retrieved_at,
                source_id=FUNDAMENTAL_SOURCE_ID,
                receipt_sha256=source.sha256,
                coverage_status="MISSING_HISTORY",
                missingness_reason="NO_CURRENT_CUSTODY_FUNDAMENTAL_HISTORY",
            )
        current = candidates.iloc[-1]
        period_end = pd.Timestamp(current["period_end"]).date().isoformat()
        available = pd.Timestamp(current["known_at"]).to_pydatetime()
        column = FUNDAMENTAL_COLUMN_MAP[field_id]
        value = _finite_or_none(current.get(column))
        status = "PRESENT" if value is not None else "MISSING_HISTORY"
        reason = None if value is not None else f"ENTITY_VALUE_MISSING:{column}"
        return _observation_row(
            security_id=security_id,
            field_id=field_id,
            value=value,
            unit=_fundamental_unit(field_id),
            period_end=period_end,
            effective_at=None,
            observed_at=source.retrieved_at,
            available_at=available,
            source_id=FUNDAMENTAL_SOURCE_ID,
            receipt_sha256=source.sha256,
            coverage_status=status,
            missingness_reason=reason,
        )

    def _verify_current_custody(self) -> None:
        identity = self._identity_receipt.payload
        market = self._market_receipt.payload
        fundamental = self._fundamental_receipt.payload if self._fundamental_receipt is not None else None
        if _sha256_file(self._security_master_path) != str(identity.get("raw_object_sha256") or ""):
            raise AlphaPITContractError("alpha_pit_ciq_security_master_hash_mismatch")
        if _sha256_file(self._market_history_path) != str(market.get("raw_object_sha256") or ""):
            raise AlphaPITContractError("alpha_pit_ciq_market_history_hash_mismatch")
        if fundamental is not None:
            assert self._fundamental_panel_path is not None
            panel_meta = (fundamental.get("outputs") or {}).get("quarterly_panel") or {}
            if _sha256_file(self._fundamental_panel_path) != str(panel_meta.get("sha256") or ""):
                raise AlphaPITContractError("alpha_pit_ciq_fundamental_panel_hash_mismatch")

    def _load_master(self) -> pd.DataFrame:
        frame = pd.read_csv(self._security_master_path, dtype=str)
        required = {"SP_ENTITY_ID", "SP_CIQ_ID", "SPT_INSTRUMENT_ITEM_ID", "Exchange", "Description", "Status"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise AlphaPITContractError("alpha_pit_ciq_master_columns_missing:" + ",".join(missing))
        out = pd.DataFrame(
            {
                "source_entity_id": frame["SP_ENTITY_ID"].fillna("").astype(str).str.strip(),
                "security_id": frame["SP_CIQ_ID"].map(lambda value: normalize_security_id(f"CIQSEC:{str(value).strip()}")),
                "trading_item_id": frame["SPT_INSTRUMENT_ITEM_ID"].fillna("").astype(str).str.strip(),
                "exchange": frame["Exchange"].fillna("").astype(str).str.strip(),
                "security_type": frame["Description"].fillna("").astype(str).str.strip(),
                "status": frame["Status"].fillna("").astype(str).str.strip(),
            }
        )
        if out["source_entity_id"].eq("").any() or out["trading_item_id"].eq("").any():
            raise AlphaPITContractError("alpha_pit_ciq_master_identity_blank")
        if out["security_id"].duplicated().any() or out["trading_item_id"].duplicated().any():
            raise AlphaPITContractError("alpha_pit_ciq_master_identity_collision")
        self._security_to_entity = dict(zip(out["security_id"], out["source_entity_id"], strict=True))
        return out.sort_values("security_id").reset_index(drop=True)

    def _load_market(self) -> pd.DataFrame:
        frame = pd.read_csv(self._market_history_path, dtype=str)
        required = {"SPT_DATE", "SP_CIQ_ID", "SPT_INSTRUMENT_ITEM_ID", "SP_TOTAL_RETURN", "SP_PRICE_CLOSE", "SP_VOLUME"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise AlphaPITContractError("alpha_pit_ciq_market_columns_missing:" + ",".join(missing))
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(frame["SPT_DATE"], errors="coerce"),
                "security_id": frame["SP_CIQ_ID"].map(lambda value: normalize_security_id(f"CIQSEC:{str(value).strip()}")),
                "trading_item_id": frame["SPT_INSTRUMENT_ITEM_ID"].fillna("").astype(str).str.strip(),
                "total_return": pd.to_numeric(frame["SP_TOTAL_RETURN"], errors="coerce"),
                "close": pd.to_numeric(frame["SP_PRICE_CLOSE"], errors="coerce"),
                "volume": pd.to_numeric(frame["SP_VOLUME"], errors="coerce"),
            }
        )
        if out["date"].isna().any():
            raise AlphaPITContractError("alpha_pit_ciq_market_date_invalid")
        known = set(self._master["security_id"])
        if not set(out["security_id"]).issubset(known):
            raise AlphaPITContractError("alpha_pit_ciq_market_unknown_security")
        expected_trading = dict(zip(self._master["security_id"], self._master["trading_item_id"], strict=True))
        mismatch = out.apply(lambda row: expected_trading[row["security_id"]] != row["trading_item_id"], axis=1)
        if mismatch.any():
            raise AlphaPITContractError("alpha_pit_ciq_market_trading_item_mismatch")
        if out.duplicated(["security_id", "date"]).any():
            raise AlphaPITContractError("alpha_pit_ciq_market_duplicate_security_date")
        return out.sort_values(["security_id", "date"]).reset_index(drop=True)

    def _load_fundamentals(self) -> pd.DataFrame:
        frame = pd.read_parquet(self._fundamental_panel_path)
        required = {"source_entity_id", "period_end", "known_at", *FUNDAMENTAL_COLUMN_MAP.values()}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise AlphaPITContractError("alpha_pit_ciq_fundamental_columns_missing:" + ",".join(missing))
        out = frame.copy()
        out["source_entity_id"] = out["source_entity_id"].astype(str)
        out["period_end"] = pd.to_datetime(out["period_end"], errors="coerce")
        out["known_at"] = pd.to_datetime(out["known_at"], errors="coerce", utc=True)
        if out["period_end"].isna().any() or out["known_at"].isna().any():
            raise AlphaPITContractError("alpha_pit_ciq_fundamental_time_invalid")
        return out.sort_values(["source_entity_id", "period_end"]).reset_index(drop=True)

    def _load_expectations(self) -> pd.DataFrame:
        assert self._expectations_source_path is not None
        source = _load_json(self._expectations_source_path)
        if source.get("schema_version") != EXPECTATIONS_SOURCE_SCHEMA:
            raise AlphaPITContractError("alpha_pit_ciq_expectations_source_schema_invalid")
        rows = source.get("rows")
        if not isinstance(rows, list):
            raise AlphaPITContractError("alpha_pit_ciq_expectations_rows_required")
        frame = pd.DataFrame(rows)
        required = {"security_id", "measure", "value", "observed_at", "available_at", "coverage_status"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise AlphaPITContractError("alpha_pit_ciq_expectations_columns_missing:" + ",".join(missing))
        frame["security_id"] = frame["security_id"].map(normalize_security_id)
        frame["measure"] = frame["measure"].astype(str)
        unknown = sorted(set(frame["measure"]) - set(EXPECTATION_MEASURES))
        if unknown:
            raise AlphaPITContractError("alpha_pit_ciq_expectations_measure_unknown:" + ",".join(unknown))
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame["observed_at"] = pd.to_datetime(frame["observed_at"], errors="coerce", utc=True)
        frame["available_at"] = pd.to_datetime(frame["available_at"], errors="coerce", utc=True)
        if frame[["observed_at", "available_at"]].isna().any().any():
            raise AlphaPITContractError("alpha_pit_ciq_expectations_time_invalid")
        if frame.duplicated(["security_id", "measure", "available_at"]).any():
            raise AlphaPITContractError("alpha_pit_ciq_expectations_duplicate_key")
        return frame.sort_values(["security_id", "measure", "available_at"]).reset_index(drop=True)

    def _load_current_receipt(
        self,
        *,
        path: Path,
        source_id: str,
        observed_range: tuple[str | None, str | None] | None,
        parser_id: str,
    ) -> _Receipt:
        payload = _load_json(path)
        if str(payload.get("source_id") or "") != source_id:
            raise AlphaPITContractError(f"alpha_pit_ciq_receipt_source_id_invalid:{source_id}")
        retrieved = _timestamp_text(payload.get("retrieved_at"), field="receipt_retrieved_at")
        if observed_range is None:
            if source_id == MARKET_SOURCE_ID:
                start = None
                end = str(payload.get("decision_target_date") or "") or None
            elif source_id == FUNDAMENTAL_SOURCE_ID:
                start = _optional_text(payload.get("quarter_min"))
                end = _optional_text(payload.get("quarter_max"))
            else:
                start, end = None, None
        else:
            start, end = observed_range
        sha = _sha256_file(path)
        binding = _binding(
            source_id=source_id,
            provider=CIQ_PROVIDER,
            retrieved_at=retrieved,
            observed_range_start=start,
            observed_range_end=end,
            receipt_path=path,
            receipt_sha256=sha,
            parser_id=parser_id,
            parser_sha256=self._parser_sha256,
            license_scope="LOCAL_LICENSED_PROVIDER_BYTES_NO_REDISTRIBUTION",
            retention_class="LOCAL_PROVIDER_EVIDENCE",
        )
        return _Receipt(path=path, payload=payload, sha256=sha, binding=binding)

    def _load_special_receipt(
        self,
        *,
        path: Path,
        expected_schema: str,
        source_id: str,
        source_path: Path | None,
        parser_id: str,
    ) -> _Receipt:
        if source_path is None:
            raise AlphaPITContractError("alpha_pit_ciq_special_source_path_required")
        payload = _load_json(path)
        if payload.get("schema_version") != expected_schema or payload.get("source_id") != source_id:
            raise AlphaPITContractError("alpha_pit_ciq_special_receipt_contract_invalid")
        if str(payload.get("risk_set_spec_id") or RISK_SET_SPEC_ID) != RISK_SET_SPEC_ID:
            raise AlphaPITContractError("alpha_pit_ciq_special_receipt_risk_set_invalid")
        if source_id == CIQ_RISK_SET_SOURCE_ID:
            _validate_risk_set_receipt_contract(payload, receipt_path=path)
        if _sha256_file(source_path) != str(payload.get("raw_object_sha256") or ""):
            raise AlphaPITContractError("alpha_pit_ciq_special_source_hash_mismatch")
        retrieved = _timestamp_text(payload.get("retrieved_at"), field="special_receipt_retrieved_at")
        sha = _sha256_file(path)
        binding = _binding(
            source_id=source_id,
            provider=CIQ_PROVIDER,
            retrieved_at=retrieved,
            observed_range_start=_optional_text(payload.get("observed_range_start")),
            observed_range_end=_optional_text(payload.get("observed_range_end")),
            receipt_path=path,
            receipt_sha256=sha,
            parser_id=parser_id,
            parser_sha256=self._parser_sha256,
            license_scope="LOCAL_LICENSED_PROVIDER_BYTES_NO_REDISTRIBUTION",
            retention_class="LOCAL_PROVIDER_EVIDENCE",
        )
        return _Receipt(path=path, payload=payload, sha256=sha, binding=binding)

    def _require_known_ids(self, ids: Sequence[str]) -> None:
        unknown = sorted(set(ids) - set(self._security_to_entity))
        if unknown:
            raise AlphaPITContractError("alpha_pit_ciq_identity_not_in_current_master:" + ",".join(unknown))

    @staticmethod
    def _require_current_cut_available(receipt: _Receipt, as_of: datetime, label: str) -> None:
        if as_of < receipt.retrieved_at:
            raise AlphaPITContractError(f"alpha_pit_ciq_current_{label}_not_available_at_as_of")


def _validate_crv1_structured_receipt_contract(
    payload: Mapping[str, Any],
    *,
    expected_schema: str,
    label: str,
) -> None:
    if payload.get("schema_version") != expected_schema:
        raise AlphaPITContractError(f"alpha_pit_ciq_crv1_{label}_receipt_schema_invalid")
    if payload.get("family_id") != FAMILY_ID or payload.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise AlphaPITContractError(f"alpha_pit_ciq_crv1_{label}_receipt_family_contract_invalid")
    if payload.get("structured_source_scope") != CRV1_STRUCTURED_SOURCE_SCOPE:
        raise AlphaPITContractError(f"alpha_pit_ciq_crv1_{label}_receipt_source_scope_invalid")
    for field in (
        "growth_screen_applied",
        "current_survivor_filter_applied",
        "future_membership_filter_applied",
        "aov_109_reused",
        "legacy_identity_fallback_used",
    ):
        if payload.get(field) is not False:
            raise AlphaPITContractError(f"alpha_pit_ciq_crv1_{label}_receipt_forbidden_flag:{field}")


def _validate_risk_set_source_contract(source: Mapping[str, Any]) -> None:
    if source.get("eligibility_contract_id") != RISK_SET_ELIGIBILITY_CONTRACT_ID:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_eligibility_contract_id_invalid")
    if source.get("eligibility_contract_sha256") != RISK_SET_ELIGIBILITY_CONTRACT_SHA256:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_eligibility_contract_hash_invalid")
    if source.get("eligibility_contract") != RISK_SET_ELIGIBILITY_CONTRACT:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_eligibility_contract_invalid")
    if bool(source.get("growth_screen_applied")):
        raise AlphaPITContractError("alpha_pit_ciq_growth_screen_risk_set_forbidden")
    if bool(source.get("current_survivor_filter_applied")):
        raise AlphaPITContractError("alpha_pit_ciq_current_survivor_filter_forbidden")
    if bool(source.get("future_membership_filter_applied")):
        raise AlphaPITContractError("alpha_pit_ciq_future_membership_filter_forbidden")
    if source.get("aov_109_reused") is not False:
        raise AlphaPITContractError("alpha_pit_ciq_aov_109_risk_set_forbidden")


def _validate_risk_set_receipt_contract(payload: Mapping[str, Any], *, receipt_path: Path) -> None:
    if payload.get("eligibility_contract_id") != RISK_SET_ELIGIBILITY_CONTRACT_ID:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_receipt_eligibility_contract_id_invalid")
    if payload.get("eligibility_contract_sha256") != RISK_SET_ELIGIBILITY_CONTRACT_SHA256:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_receipt_eligibility_contract_hash_invalid")
    if bool(payload.get("growth_screen_applied")):
        raise AlphaPITContractError("alpha_pit_ciq_growth_screen_risk_set_forbidden")
    if bool(payload.get("current_survivor_filter_applied")):
        raise AlphaPITContractError("alpha_pit_ciq_current_survivor_filter_forbidden")
    if bool(payload.get("future_membership_filter_applied")):
        raise AlphaPITContractError("alpha_pit_ciq_future_membership_filter_forbidden")
    if payload.get("aov_109_reused") is not False:
        raise AlphaPITContractError("alpha_pit_ciq_aov_109_risk_set_forbidden")
    identity_path_raw = str(payload.get("identity_receipt_path") or "").strip()
    identity_sha = str(payload.get("identity_receipt_sha256") or "").strip()
    if not identity_path_raw or len(identity_sha) != 64:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_identity_receipt_binding_required")
    identity_path = Path(identity_path_raw)
    if not identity_path.is_absolute():
        identity_path = receipt_path.parent / identity_path
    if _sha256_file(identity_path) != identity_sha:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_identity_receipt_hash_mismatch")


def _validate_risk_set_row_eligibility(row: Mapping[str, Any]) -> None:
    if str(row.get("eligibility_status") or "") != "ELIGIBLE":
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_noneligible_row_forbidden")
    if str(row.get("listing_country") or "") != "US":
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_listing_country_invalid")
    if row.get("primary_listing") is not True:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_primary_listing_required")
    if str(row.get("security_class") or "") != "COMMON_EQUITY":
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_security_class_invalid")
    if str(row.get("trading_status") or "") != "ACTIVE_TRADABLE":
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_trading_status_invalid")
    if str(row.get("identity_status") or "") != "UNIQUE_PERMANENT_MAPPING":
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_identity_status_invalid")
    try:
        history_count = int(row.get("prior_market_observation_count"))
    except (TypeError, ValueError) as exc:
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_market_history_count_invalid") from exc
    if history_count < int(RISK_SET_ELIGIBILITY_CONTRACT["minimum_prior_market_observations"]):
        raise AlphaPITContractError("alpha_pit_ciq_risk_set_market_history_insufficient")


def _observation_row(
    *,
    security_id: str,
    field_id: str,
    value: float | None,
    unit: str | None,
    period_end: str | None,
    effective_at: str | None,
    observed_at: datetime,
    available_at: datetime,
    source_id: str,
    receipt_sha256: str,
    coverage_status: str,
    missingness_reason: str | None,
) -> dict[str, Any]:
    body = {
        "security_id": security_id,
        "field_id": field_id,
        "value_type": "FLOAT" if value is not None else "NULL",
        "value": value,
        "unit": unit,
        "period_end": period_end,
        "effective_at": effective_at,
        "observed_at": iso_utc(observed_at),
        "available_at": iso_utc(available_at),
        "source_id": source_id,
        "source_receipt_sha256": receipt_sha256,
        "schema_version": "alpha_pit_observation_row_v1",
        "coverage_status": coverage_status,
        "missingness_reason": missingness_reason,
    }
    return {**body, "artifact_row_hash": domain_hash("ALPHA_PIT_V1:OBSERVATION_ROW", hash_safe(body))}


def _expectation_row(
    *,
    security_id: str,
    measure: str,
    value: float | None,
    unit: str | None,
    forecast_period_end: str | None,
    observed_at: datetime,
    available_at: datetime,
    source_id: str,
    receipt_sha256: str,
    coverage_status: str,
    missingness_reason: str | None,
) -> dict[str, Any]:
    body = {
        "expectation_id": domain_hash(
            "ALPHA_PIT_V1:EXPECTATION_ID",
            {"security_id": security_id, "measure": measure, "available_at": iso_utc(available_at)},
        ),
        "security_id": security_id,
        "measure": measure,
        "value": value,
        "unit": unit,
        "forecast_period_end": forecast_period_end,
        "observed_at": iso_utc(observed_at),
        "available_at": iso_utc(available_at),
        "source_id": source_id,
        "source_receipt_sha256": receipt_sha256,
        "method_id": None,
        "method_sha256": None,
        "epistemic_class": "OBSERVED_CONSENSUS",
        "schema_version": "alpha_pit_expectation_row_v1",
        "coverage_status": coverage_status,
        "missingness_reason": missingness_reason,
    }
    return {**body, "artifact_row_hash": domain_hash("ALPHA_PIT_V1:EXPECTATION_ROW", hash_safe(body))}


def _coverage(
    *,
    requested_security_count: int,
    requested_item_count: int,
    present_count: int,
    missing_reasons: Mapping[str, int],
    requested_field_count: int | None = None,
) -> dict[str, Any]:
    missing_count = requested_item_count - present_count
    return {
        "requested_security_count": requested_security_count,
        "returned_security_count": requested_security_count,
        "requested_field_count": requested_field_count,
        "present_count": present_count,
        "missing_count": missing_count,
        "not_entitled_count": int(missing_reasons.get("NOT_ENTITLED", 0)),
        "stale_count": int(missing_reasons.get("STALE", 0)),
        "coverage_rate": format(present_count / requested_item_count if requested_item_count else 1.0, ".17g"),
        "missingness_by_reason": dict(sorted((str(k), int(v)) for k, v in missing_reasons.items())),
    }


def _missing_source_binding(
    *,
    source_id: str,
    reason: str,
    retrieved_at: datetime,
    parser_id: str,
    parser_sha256: str,
) -> dict[str, Any]:
    body = {
        "schema_version": "alpha_pit_missing_source_receipt_v1",
        "source_id": source_id,
        "reason": reason,
        "retrieved_at": iso_utc(retrieved_at),
    }
    digest = domain_hash("ALPHA_PIT_V1:MISSING_SOURCE_RECEIPT", body)
    return _binding(
        source_id=source_id,
        provider="LOCAL_CUSTODY_SENTINEL_NO_PROVIDER_BYTES",
        retrieved_at=body["retrieved_at"],
        observed_range_start=None,
        observed_range_end=None,
        receipt_path=Path(f"missing/{source_id.replace(':', '_')}/{digest}.json"),
        receipt_sha256=digest,
        parser_id=parser_id,
        parser_sha256=parser_sha256,
        license_scope="NO_PROVIDER_BYTES_CAPTURED",
        retention_class="MECHANICAL_MISSINGNESS_SENTINEL",
    )


def _binding(
    *,
    source_id: str,
    provider: str,
    retrieved_at: str,
    observed_range_start: str | None,
    observed_range_end: str | None,
    receipt_path: Path,
    receipt_sha256: str,
    parser_id: str,
    parser_sha256: str,
    license_scope: str,
    retention_class: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "provider": provider,
        "retrieved_at": retrieved_at,
        "observed_range_start": observed_range_start,
        "observed_range_end": observed_range_end,
        "raw_receipt_path": receipt_path.as_posix(),
        "raw_receipt_sha256": receipt_sha256,
        "parser_id": parser_id,
        "parser_sha256": parser_sha256,
        "license_scope": license_scope,
        "retention_class": retention_class,
    }


def _market_unit(field_id: str) -> str | None:
    return {
        "market.close": "USD",
        "market.total_return_1d": "DECIMAL_RETURN",
        "market.volume": "SHARES",
        "market.adv20": "USD",
        "market.realized_vol20": "ANNUALIZED_DECIMAL_VOL",
        "market.sma20": "USD",
        "market.sma200": "USD",
    }.get(field_id)


def _fundamental_unit(field_id: str) -> str | None:
    if field_id in {"fund.revenue_q", "fund.inventory_q", "fund.capex_q", "fund.cash_from_ops_q"}:
        return "USD_THOUSANDS"
    if field_id in {"fund.gross_margin_q", "fund.operating_margin_q"}:
        return "RATIO"
    return None


def _finite_or_none(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise AlphaPITContractError("alpha_pit_as_of_timezone_required")
    return value.astimezone(UTC)


def _timestamp_text(value: Any, *, field: str) -> str:
    return iso_utc(_parse_timestamp(value, field=field))


def _parse_timestamp(value: Any, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AlphaPITContractError(f"alpha_pit_ciq_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AlphaPITContractError(f"alpha_pit_ciq_{field}_timezone_required")
    return parsed.astimezone(UTC)


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _load_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise AlphaPITContractError(f"alpha_pit_source_file_missing:{path.as_posix()}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AlphaPITContractError(f"alpha_pit_source_json_invalid:{path.as_posix()}") from exc
    if not isinstance(payload, Mapping):
        raise AlphaPITContractError("alpha_pit_source_json_mapping_required")
    return payload


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        raise AlphaPITContractError(f"alpha_pit_source_file_missing:{path.as_posix()}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _max_retrieved(receipts: Sequence[_Receipt]) -> datetime:
    if not receipts:
        raise AlphaPITContractError("alpha_pit_source_receipt_required")
    return max(receipt.retrieved_at for receipt in receipts)


def _dedupe_receipts(receipts: Sequence[_Receipt]) -> list[_Receipt]:
    by_hash: dict[str, _Receipt] = {}
    for receipt in receipts:
        by_hash[receipt.sha256] = receipt
    return [by_hash[key] for key in sorted(by_hash)]
