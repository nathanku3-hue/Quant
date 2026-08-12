"""Mode-bound read capabilities for alpha_pit_data_api_v1.

The confirmatory and prospective capability objects have no outcome method.
Discovery is constructed through a separate, lazily imported subclass so the
label surface is absent from normal prospective/confirmatory dependency state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from research.alpha_pit_v1.contracts import (
    API_SCHEMA_ID,
    CRV1_FAMILY_DATA_CONTRACT,
    AlphaPITBackendV1,
    ArtifactRef,
    FamilyDataContract,
    ResearchMode,
    utc_datetime,
    validate_observation_fields,
    validate_security_ids,
)
from research.alpha_pit_v1.manifests import verify_artifact_ref


class AlphaPITReadAPIv1:
    """Provider-blind Alpha PIT read capability for one frozen research mode."""

    __slots__ = ("_mode", "_family_id", "_family_contract", "_decision_context_id", "_backend")

    def __init__(
        self,
        *,
        mode: ResearchMode,
        family_id: str,
        decision_context_id: str,
        backend: AlphaPITBackendV1,
        family_contract: FamilyDataContract = CRV1_FAMILY_DATA_CONTRACT,
    ) -> None:
        normalized = ResearchMode(mode)
        if normalized is ResearchMode.DISCOVERY:
            raise ValueError("alpha_pit_discovery_capability_required")
        self._initialize(
            mode=normalized,
            family_id=family_id,
            decision_context_id=decision_context_id,
            backend=backend,
            family_contract=family_contract,
        )

    def _initialize(
        self,
        *,
        mode: ResearchMode,
        family_id: str,
        decision_context_id: str,
        backend: AlphaPITBackendV1,
        family_contract: FamilyDataContract = CRV1_FAMILY_DATA_CONTRACT,
    ) -> None:
        if not isinstance(family_contract, FamilyDataContract):
            raise TypeError("alpha_pit_family_data_contract_required")
        if family_id != family_contract.family_id:
            raise ValueError("alpha_pit_family_invalid")
        if not str(decision_context_id).strip():
            raise ValueError("alpha_pit_decision_context_required")
        if not isinstance(backend, AlphaPITBackendV1):
            raise TypeError("alpha_pit_backend_v1_required")
        self._mode = ResearchMode(mode)
        self._family_id = family_id
        self._family_contract = family_contract
        self._decision_context_id = str(decision_context_id)
        self._backend = backend

    @property
    def research_mode(self) -> ResearchMode:
        return self._mode

    @property
    def family_id(self) -> str:
        return self._family_id

    @property
    def family_contract(self) -> FamilyDataContract:
        return self._family_contract

    @property
    def decision_context_id(self) -> str:
        return self._decision_context_id

    def risk_set(self, *, as_of: datetime) -> ArtifactRef:
        cutoff = utc_datetime(as_of)
        ref = self._backend.risk_set(as_of=cutoff, research_mode=self._mode)
        _validate_ref(
            ref,
            artifact_type="RISK_SET",
            research_mode=self._mode,
            as_of=cutoff,
            family_contract=self._family_contract,
        )
        payload = _mapping_payload(ref, artifact_type="RISK_SET")
        if payload.get("family_id") != self._family_contract.family_id:
            raise ValueError("alpha_pit_risk_set_family_invalid")
        if payload.get("risk_set_spec_id") != self._family_contract.risk_set_spec_id:
            raise ValueError("alpha_pit_risk_set_spec_invalid")
        rows = _rows(payload, artifact_type="RISK_SET")
        if int(payload.get("row_count", -1)) != len(rows):
            raise ValueError("alpha_pit_risk_set_row_count_invalid")
        _validate_row_availability(rows, as_of=cutoff)
        security_ids = [str(row.get("security_id") or "") for row in rows]
        validate_security_ids(security_ids)
        if len(set(security_ids)) != len(security_ids):
            raise ValueError("alpha_pit_risk_set_duplicate_security_id")
        return ref

    def observations(
        self,
        *,
        ids: Sequence[str],
        fields: Sequence[str],
        as_of: datetime,
    ) -> ArtifactRef:
        cutoff = utc_datetime(as_of)
        security_ids = validate_security_ids(ids)
        field_ids = validate_observation_fields(fields)
        disallowed = sorted(set(field_ids) - set(self._family_contract.allowed_observation_surface))
        if disallowed:
            raise ValueError("alpha_pit_observation_surface_forbidden:" + disallowed[0])
        ref = self._backend.observations(
            ids=security_ids,
            fields=field_ids,
            as_of=cutoff,
            research_mode=self._mode,
        )
        _validate_ref(
            ref,
            artifact_type="OBSERVATIONS",
            research_mode=self._mode,
            as_of=cutoff,
            family_contract=self._family_contract,
        )
        payload = _mapping_payload(ref, artifact_type="OBSERVATIONS")
        rows = _rows(payload, artifact_type="OBSERVATIONS")
        _validate_row_availability(rows, as_of=cutoff)
        expected_pairs = sorted(
            (security_id, field_id)
            for security_id in security_ids
            for field_id in field_ids
        )
        actual_pairs = sorted(
            (str(row.get("security_id") or ""), str(row.get("field_id") or ""))
            for row in rows
        )
        if actual_pairs != expected_pairs:
            raise ValueError("alpha_pit_observation_pairs_not_exact")
        for row in rows:
            status = str(row.get("coverage_status") or "")
            if status not in {
                "PRESENT",
                "MISSING_HISTORY",
                "MISSING_SOURCE",
                "NOT_ENTITLED",
                "NOT_APPLICABLE",
                "STALE",
            }:
                raise ValueError("alpha_pit_observation_coverage_status_invalid")
            if status != "PRESENT" and not str(row.get("missingness_reason") or "").strip():
                raise ValueError("alpha_pit_observation_missingness_reason_required")
        return ref

    def source_claims(self, *, ids: Sequence[str], as_of: datetime) -> ArtifactRef:
        if not self._family_contract.allowed_claim_surface:
            raise ValueError("alpha_pit_claim_surface_forbidden")
        cutoff = utc_datetime(as_of)
        security_ids = validate_security_ids(ids)
        ref = self._backend.source_claims(
            ids=security_ids,
            as_of=cutoff,
            research_mode=self._mode,
        )
        _validate_ref(
            ref,
            artifact_type="SOURCE_CLAIMS",
            research_mode=self._mode,
            as_of=cutoff,
            family_contract=self._family_contract,
        )
        payload = _mapping_payload(ref, artifact_type="SOURCE_CLAIMS")
        rows = _rows(payload, artifact_type="SOURCE_CLAIMS")
        _validate_row_availability(rows, as_of=cutoff)
        requested = set(security_ids)
        for row in rows:
            security_id = validate_security_ids([str(row.get("security_id") or "")])[0]
            if security_id not in requested:
                raise ValueError("alpha_pit_source_claim_unrequested_security")
            if row.get("epistemic_class") != "OBSERVED_SOURCE_CLAIM":
                raise ValueError("alpha_pit_source_claim_epistemic_class_invalid")
            if str(row.get("claim_topic") or "") not in self._family_contract.allowed_claim_surface:
                raise ValueError("alpha_pit_source_claim_topic_forbidden")
        return ref

    def expectations(self, *, ids: Sequence[str], as_of: datetime) -> ArtifactRef:
        if not self._family_contract.allowed_expectation_surface:
            raise ValueError("alpha_pit_expectation_surface_forbidden")
        cutoff = utc_datetime(as_of)
        security_ids = validate_security_ids(ids)
        ref = self._backend.expectations(
            ids=security_ids,
            as_of=cutoff,
            research_mode=self._mode,
        )
        _validate_ref(
            ref,
            artifact_type="EXPECTATIONS",
            research_mode=self._mode,
            as_of=cutoff,
            family_contract=self._family_contract,
        )
        payload = _mapping_payload(ref, artifact_type="EXPECTATIONS")
        rows = _rows(payload, artifact_type="EXPECTATIONS")
        _validate_row_availability(rows, as_of=cutoff)
        requested = set(security_ids)
        expected_pairs = sorted(
            (security_id, measure)
            for security_id in security_ids
            for measure in self._family_contract.allowed_expectation_surface
        )
        actual_pairs = sorted(
            (str(row.get("security_id") or ""), str(row.get("measure") or ""))
            for row in rows
        )
        if actual_pairs != expected_pairs:
            raise ValueError("alpha_pit_expectation_pairs_not_exact")
        for row in rows:
            security_id = validate_security_ids([str(row.get("security_id") or "")])[0]
            if security_id not in requested:
                raise ValueError("alpha_pit_expectation_unrequested_security")
            if row.get("epistemic_class") not in {"OBSERVED_CONSENSUS", "INFERRED_MARKET_IMPLIED"}:
                raise ValueError("alpha_pit_expectation_epistemic_class_invalid")
            status = str(row.get("coverage_status") or "")
            if status not in {
                "PRESENT",
                "MISSING_HISTORY",
                "MISSING_SOURCE",
                "NOT_ENTITLED",
                "NOT_APPLICABLE",
                "STALE",
            }:
                raise ValueError("alpha_pit_expectation_coverage_status_invalid")
            if status != "PRESENT" and not str(row.get("missingness_reason") or "").strip():
                raise ValueError("alpha_pit_expectation_missingness_reason_required")
        return ref


def open_alpha_pit_session(
    *,
    mode: ResearchMode,
    family_id: str,
    decision_context_id: str,
    backend: AlphaPITBackendV1,
    family_contract: FamilyDataContract = CRV1_FAMILY_DATA_CONTRACT,
) -> AlphaPITReadAPIv1:
    normalized = ResearchMode(mode)
    if normalized is ResearchMode.DISCOVERY:
        from research.alpha_pit_v1.discovery_outcomes import AlphaPITDiscoveryAPIv1

        return AlphaPITDiscoveryAPIv1(
            family_id=family_id,
            decision_context_id=decision_context_id,
            backend=backend,
            family_contract=family_contract,
        )
    return AlphaPITReadAPIv1(
        mode=normalized,
        family_id=family_id,
        decision_context_id=decision_context_id,
        backend=backend,
        family_contract=family_contract,
    )


def _mapping_payload(ref: ArtifactRef, *, artifact_type: str) -> Mapping[str, Any]:
    if not isinstance(ref.payload, Mapping):
        raise ValueError(f"alpha_pit_{artifact_type.lower()}_payload_mapping_required")
    return ref.payload


def _rows(payload: Mapping[str, Any], *, artifact_type: str) -> list[Mapping[str, Any]]:
    raw = payload.get("rows")
    if not isinstance(raw, list) or any(not isinstance(row, Mapping) for row in raw):
        raise ValueError(f"alpha_pit_{artifact_type.lower()}_rows_required")
    return raw


def _validate_ref(
    ref: ArtifactRef,
    *,
    artifact_type: str,
    research_mode: ResearchMode,
    as_of: datetime | None,
    family_contract: FamilyDataContract,
) -> None:
    if not isinstance(ref, ArtifactRef):
        raise TypeError("alpha_pit_artifact_ref_required")
    verify_artifact_ref(ref, family_contract=family_contract)
    if ref.artifact_type != artifact_type:
        raise ValueError("alpha_pit_artifact_type_mismatch")
    manifest = ref.manifest
    if manifest.get("api_schema_id") != API_SCHEMA_ID:
        raise ValueError("alpha_pit_api_schema_invalid")
    if manifest.get("family_id") != family_contract.family_id:
        raise ValueError("alpha_pit_manifest_family_invalid")
    if manifest.get("research_mode") != research_mode.value:
        raise ValueError("alpha_pit_manifest_research_mode_invalid")
    if manifest.get("financial_alpha_evidence") != 0:
        raise ValueError("alpha_pit_financial_alpha_evidence_must_be_zero")
    if not isinstance(manifest.get("source_receipts"), list) or not manifest.get("source_receipts"):
        raise ValueError("alpha_pit_source_receipts_required")
    coverage = manifest.get("coverage_summary")
    if not isinstance(coverage, Mapping) or "missingness_by_reason" not in coverage:
        raise ValueError("alpha_pit_coverage_summary_required")
    if as_of is not None:
        expected = as_of.isoformat(timespec="microseconds").replace("+00:00", "Z")
        if manifest.get("as_of") != expected:
            raise ValueError("alpha_pit_manifest_as_of_mismatch")


def _validate_row_availability(rows: Sequence[Mapping[str, Any]], *, as_of: datetime) -> None:
    for row in rows:
        raw = str(row.get("available_at") or "")
        if not raw:
            raise ValueError("alpha_pit_available_at_required")
        try:
            available = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("alpha_pit_available_at_invalid") from exc
        if available.tzinfo is None or available.utcoffset() is None:
            raise ValueError("alpha_pit_available_at_timezone_required")
        if available > as_of:
            raise ValueError("alpha_pit_available_at_after_as_of")
