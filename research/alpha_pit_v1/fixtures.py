"""Deterministic zero-authority fixtures for Alpha PIT v1 engineering."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    EXPECTATION_MEASURES,
    CRV1_FAMILY_DATA_CONTRACT,
    AlphaPITBackendV1,
    ArtifactRef,
    FamilyDataContract,
    ResearchMode,
)
from research.alpha_pit_v1.manifests import build_artifact_ref


FIXTURE_CREATED_AT = "2026-01-01T00:00:01.000000Z"
FIXTURE_SOURCE_RECEIPT = {
    "source_id": "FIXTURE:ALPHA_PIT_V1",
    "provider": "DETERMINISTIC_FIXTURE_ONLY",
    "retrieved_at": "2026-01-01T00:00:00.000000Z",
    "observed_range_start": "2025-01-01",
    "observed_range_end": "2025-12-31",
    "raw_receipt_path": "fixture://alpha_pit_v1/source_receipt",
    "raw_receipt_sha256": domain_hash("ALPHA_PIT_V1:FIXTURE:SOURCE_RECEIPT", {"version": 1}),
    "parser_id": "alpha_pit_fixture_v1",
    "parser_sha256": domain_hash("ALPHA_PIT_V1:FIXTURE:PARSER", {"version": 1}),
    "license_scope": "TEST_ONLY",
    "retention_class": "TEST_FIXTURE",
}


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class DeterministicAlphaPITFixtureBackend(AlphaPITBackendV1):
    """Small family-bound fixture backend with zero empirical authority."""

    security_ids = ("CIQSEC:101", "CIQSEC:202")

    def __init__(
        self,
        *,
        family_contract: FamilyDataContract = CRV1_FAMILY_DATA_CONTRACT,
    ) -> None:
        if not isinstance(family_contract, FamilyDataContract):
            raise TypeError("alpha_pit_fixture_family_data_contract_required")
        self.family_contract = family_contract

    def risk_set(self, *, as_of: datetime, research_mode: ResearchMode) -> ArtifactRef:
        rows = [
            {
                "security_id": security_id,
                "company_id": f"COMPANY:{security_id.split(':', 1)[1]}",
                "trading_item_id": f"SPT{security_id.split(':', 1)[1]}",
                "primary_listing_id": f"PRIMARY:{security_id}",
                "membership_effective_at": "2025-01-01T00:00:00.000000Z",
                "observed_at": "2025-12-31T20:00:00.000000Z",
                "available_at": "2025-12-31T21:00:00.000000Z",
                "source_id": "FIXTURE:ALPHA_PIT_V1",
                "source_receipt_sha256": FIXTURE_SOURCE_RECEIPT["raw_receipt_sha256"],
                "identity_receipt_sha256": FIXTURE_SOURCE_RECEIPT["raw_receipt_sha256"],
                "eligibility_status": "ELIGIBLE",
                "schema_version": "alpha_pit_risk_set_row_v1",
            }
            for security_id in self.security_ids
        ]
        self._reject_future(rows, as_of=as_of)
        risk_set_id = domain_hash(
            "ALPHA_PIT_V1:FIXTURE:RISK_SET",
            {
                "family_id": self.family_contract.family_id,
                "risk_set_spec_id": self.family_contract.risk_set_spec_id,
                "as_of": _iso(as_of),
                "rows": rows,
            },
        )
        payload = {
            "risk_set_id": risk_set_id,
            "family_id": self.family_contract.family_id,
            "risk_set_spec_id": self.family_contract.risk_set_spec_id,
            "as_of": _iso(as_of),
            "rows": rows,
            "row_count": len(rows),
            "exclusion_counts": {},
        }
        return build_artifact_ref(
            artifact_type="RISK_SET",
            research_mode=research_mode,
            request={"as_of": _iso(as_of)},
            payload=payload,
            as_of=as_of,
            created_at=FIXTURE_CREATED_AT,
            risk_set_id=risk_set_id,
            source_receipts=[FIXTURE_SOURCE_RECEIPT],
            coverage_summary=self._coverage(len(rows), len(rows), 0),
            family_contract=self.family_contract,
            fixture=True,
        )

    def observations(
        self,
        *,
        ids: Sequence[str],
        fields: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        rows: list[dict[str, Any]] = []
        for security_id in ids:
            for field_id in fields:
                value = self._observation_value(security_id, field_id)
                rows.append(
                    {
                        "security_id": security_id,
                        "field_id": field_id,
                        "value_type": "FLOAT",
                        "value": value,
                        "unit": None,
                        "period_end": "2025-12-31" if field_id.startswith("fund.") else None,
                        "effective_at": None,
                        "observed_at": "2025-12-31T20:00:00.000000Z",
                        "available_at": "2025-12-31T21:00:00.000000Z",
                        "source_id": "FIXTURE:ALPHA_PIT_V1",
                        "source_receipt_sha256": FIXTURE_SOURCE_RECEIPT["raw_receipt_sha256"],
                        "schema_version": "alpha_pit_observation_row_v1",
                        "coverage_status": "PRESENT",
                        "missingness_reason": None,
                        "artifact_row_hash": domain_hash(
                            "ALPHA_PIT_V1:FIXTURE:OBS_ROW",
                            {"security_id": security_id, "field_id": field_id, "value": value},
                        ),
                    }
                )
        self._reject_future(rows, as_of=as_of)
        expected = len(ids) * len(fields)
        return build_artifact_ref(
            artifact_type="OBSERVATIONS",
            research_mode=research_mode,
            request={"ids": list(ids), "fields": list(fields), "as_of": _iso(as_of)},
            payload={"rows": rows, "row_count": len(rows)},
            as_of=as_of,
            created_at=FIXTURE_CREATED_AT,
            source_receipts=[FIXTURE_SOURCE_RECEIPT],
            coverage_summary=self._coverage(len(ids), len(rows), 0, requested_field_count=len(fields)),
            family_contract=self.family_contract,
            fixture=True,
        )

    def source_claims(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        rows = [
            {
                "claim_id": domain_hash("ALPHA_PIT_V1:FIXTURE:CLAIM", {"security_id": security_id}),
                "security_id": security_id,
                "related_security_id": None,
                "claim_topic": "INVENTORY_CHANNEL",
                "claim_normalized": "fixture inventory normalization statement",
                "claim_direction": "DOWN",
                "claim_horizon": "NEXT_QUARTER",
                "source_document_id": f"FIXTURE-DOC-{security_id}",
                "source_document_type": "TEST_FIXTURE",
                "source_locator": "fixture:section:1",
                "source_published_at": "2025-12-31T19:00:00.000000Z",
                "source_accepted_at": "2025-12-31T19:00:00.000000Z",
                "observed_at": "2025-12-31T20:00:00.000000Z",
                "available_at": "2025-12-31T21:00:00.000000Z",
                "source_receipt_sha256": FIXTURE_SOURCE_RECEIPT["raw_receipt_sha256"],
                "extraction_procedure_id": "fixture_rule_v1",
                "extraction_procedure_sha256": domain_hash("ALPHA_PIT_V1:FIXTURE:CLAIM_PROC", {"version": 1}),
                "schema_version": "alpha_pit_source_claim_row_v1",
                "epistemic_class": "OBSERVED_SOURCE_CLAIM",
                "coverage_status": "PRESENT",
                "artifact_row_hash": domain_hash("ALPHA_PIT_V1:FIXTURE:CLAIM_ROW", {"security_id": security_id}),
            }
            for security_id in ids
        ]
        self._reject_future(rows, as_of=as_of)
        return build_artifact_ref(
            artifact_type="SOURCE_CLAIMS",
            research_mode=research_mode,
            request={"ids": list(ids), "as_of": _iso(as_of)},
            payload={"rows": rows, "row_count": len(rows)},
            as_of=as_of,
            created_at=FIXTURE_CREATED_AT,
            source_receipts=[FIXTURE_SOURCE_RECEIPT],
            coverage_summary=self._coverage(len(ids), len(rows), 0),
            family_contract=self.family_contract,
            fixture=True,
        )

    def expectations(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        rows = []
        for security_id in ids:
            for measure in EXPECTATION_MEASURES:
                rows.append(
                    {
                        "expectation_id": domain_hash(
                            "ALPHA_PIT_V1:FIXTURE:EXPECTATION", {"security_id": security_id, "measure": measure}
                        ),
                        "security_id": security_id,
                        "measure": measure,
                        "value": "1",
                        "unit": None,
                        "forecast_period_end": "2026-12-31",
                        "observed_at": "2025-12-31T20:00:00.000000Z",
                        "available_at": "2025-12-31T21:00:00.000000Z",
                        "source_id": "FIXTURE:ALPHA_PIT_V1",
                        "source_receipt_sha256": FIXTURE_SOURCE_RECEIPT["raw_receipt_sha256"],
                        "method_id": None,
                        "method_sha256": None,
                        "epistemic_class": "OBSERVED_CONSENSUS",
                        "schema_version": "alpha_pit_expectation_row_v1",
                        "coverage_status": "PRESENT",
                        "missingness_reason": None,
                        "artifact_row_hash": domain_hash(
                            "ALPHA_PIT_V1:FIXTURE:EXPECTATION_ROW",
                            {"security_id": security_id, "measure": measure},
                        ),
                    }
                )
        self._reject_future(rows, as_of=as_of)
        expected = len(ids) * len(EXPECTATION_MEASURES)
        return build_artifact_ref(
            artifact_type="EXPECTATIONS",
            research_mode=research_mode,
            request={"ids": list(ids), "as_of": _iso(as_of)},
            payload={"rows": rows, "row_count": len(rows)},
            as_of=as_of,
            created_at=FIXTURE_CREATED_AT,
            source_receipts=[FIXTURE_SOURCE_RECEIPT],
            coverage_summary=self._coverage(len(ids), len(rows), 0, requested_field_count=len(EXPECTATION_MEASURES)),
            family_contract=self.family_contract,
            fixture=True,
        )

    def outcomes(self, *, risk_set_id: str, label_spec_id: str) -> ArtifactRef:
        if label_spec_id != self.family_contract.primary_label_spec_id:
            raise ValueError("alpha_pit_fixture_label_spec_invalid")
        rows = [
            {
                "risk_set_id": risk_set_id,
                "security_id": security_id,
                "label_spec_id": label_spec_id,
                "execution_boundary": "2025-01-02T21:00:00.000000Z",
                "horizon_end": "2025-12-31",
                "realized_total_return": "1" if security_id == "CIQSEC:101" else "0",
                "cross_section_percentile": "1" if security_id == "CIQSEC:101" else "0",
                "winner_label": security_id == "CIQSEC:101",
                "observed_at": "2025-12-31T21:00:00.000000Z",
                "available_at": "2025-12-31T21:00:00.000000Z",
                "source_id": "FIXTURE:ALPHA_PIT_V1",
                "source_receipt_sha256": FIXTURE_SOURCE_RECEIPT["raw_receipt_sha256"],
                "schema_version": "alpha_pit_outcome_row_v1",
                "coverage_status": "PRESENT",
                "missingness_reason": None,
                "artifact_row_hash": domain_hash(
                    "ALPHA_PIT_V1:FIXTURE:OUTCOME_ROW", {"risk_set_id": risk_set_id, "security_id": security_id}
                ),
            }
            for security_id in self.security_ids
        ]
        return build_artifact_ref(
            artifact_type="OUTCOMES",
            research_mode=ResearchMode.DISCOVERY,
            request={"risk_set_id": risk_set_id, "label_spec_id": label_spec_id},
            payload={
                "family_id": self.family_contract.family_id,
                "risk_set_id": risk_set_id,
                "label_spec_id": label_spec_id,
                "rows": rows,
                "risk_set_denominator": len(rows),
                "denominator_count": len(rows),
                "finite_label_count": len(rows),
                "missing_label_count": 0,
            },
            as_of=None,
            created_at=FIXTURE_CREATED_AT,
            risk_set_id=risk_set_id,
            source_receipts=[FIXTURE_SOURCE_RECEIPT],
            coverage_summary=self._coverage(len(rows), len(rows), 0),
            family_contract=self.family_contract,
            fixture=True,
        )

    @staticmethod
    def _observation_value(security_id: str, field_id: str) -> str:
        base = 2 if security_id.endswith("101") else 1
        field_offset = sum(ord(char) for char in field_id) % 13
        return format((base * 100 + field_offset) / 10.0, ".17g")

    @staticmethod
    def _reject_future(rows: Sequence[dict[str, Any]], *, as_of: datetime) -> None:
        for row in rows:
            available = datetime.fromisoformat(str(row["available_at"]).replace("Z", "+00:00"))
            if available > as_of:
                raise ValueError("alpha_pit_fixture_available_at_after_as_of")

    @staticmethod
    def _coverage(
        requested_security_count: int,
        present: int,
        missing: int,
        *,
        requested_field_count: int | None = None,
    ) -> dict[str, Any]:
        requested_items = present + missing
        rate = present / requested_items if requested_items else 1.0
        return {
            "requested_security_count": requested_security_count,
            "returned_security_count": requested_security_count,
            "requested_field_count": requested_field_count,
            "present_count": present,
            "missing_count": missing,
            "not_entitled_count": 0,
            "stale_count": 0,
            "coverage_rate": format(rate, ".17g"),
            "missingness_by_reason": {},
        }
