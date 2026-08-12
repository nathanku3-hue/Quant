"""Deterministic content-addressed envelopes for Alpha PIT v1 artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    API_SCHEMA_ID,
    CRV1_FAMILY_DATA_CONTRACT,
    AlphaPITContractError,
    ArtifactRef,
    FamilyDataContract,
    ResearchMode,
    validate_source_receipt_binding,
)


def canonical_value(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("alpha_pit_manifest_timezone_required")
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    return value


def _mode_value(research_mode: ResearchMode | str) -> str:
    try:
        return ResearchMode(research_mode).value
    except ValueError as exc:
        raise AlphaPITContractError("alpha_pit_research_mode_invalid") from exc


def _timestamp_text(value: datetime | str, *, field: str) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise AlphaPITContractError(f"alpha_pit_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AlphaPITContractError(f"alpha_pit_{field}_timezone_required")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def build_artifact_ref(
    *,
    artifact_type: str,
    research_mode: ResearchMode | str,
    request: Mapping[str, Any],
    payload: Any,
    as_of: datetime | None,
    created_at: datetime | str,
    risk_set_id: str | None = None,
    source_receipts: list[Mapping[str, Any]] | None = None,
    coverage_summary: Mapping[str, Any] | None = None,
    family_contract: FamilyDataContract = CRV1_FAMILY_DATA_CONTRACT,
    fixture: bool = False,
) -> ArtifactRef:
    if not isinstance(family_contract, FamilyDataContract):
        raise AlphaPITContractError("alpha_pit_family_data_contract_required")
    created_at_text = _timestamp_text(created_at, field="created_at")
    created_at_dt = datetime.fromisoformat(created_at_text.replace("Z", "+00:00"))
    for binding in source_receipts or []:
        validate_source_receipt_binding(binding)
        retrieved = datetime.fromisoformat(str(binding["retrieved_at"]).replace("Z", "+00:00"))
        if retrieved.astimezone(timezone.utc) > created_at_dt:
            raise AlphaPITContractError("alpha_pit_source_retrieved_after_created_at")
    request_value = canonical_value(request)
    payload_value = canonical_value(payload)
    request_sha256 = domain_hash("ALPHA_PIT_V1:REQUEST", request_value)
    payload_sha256 = domain_hash(f"ALPHA_PIT_V1:PAYLOAD:{artifact_type}", payload_value)
    manifest_body = {
        "api_schema_id": API_SCHEMA_ID,
        "artifact_type": artifact_type,
        "family_id": family_contract.family_id,
        "family_data_contract": family_contract.as_dict(),
        "research_mode": _mode_value(research_mode),
        "request_canonical_json": request_value,
        "request_sha256": request_sha256,
        "as_of": canonical_value(as_of) if as_of is not None else None,
        "risk_set_id": risk_set_id,
        "created_at": created_at_text,
        "source_receipts": canonical_value(source_receipts or []),
        "coverage_summary": canonical_value(coverage_summary or {}),
        "payload_path": f"fixture://{artifact_type.lower()}/{payload_sha256}" if fixture else f"content://{payload_sha256}",
        "payload_sha256": payload_sha256,
        "schema_version": f"alpha_pit_{artifact_type.lower()}_artifact_v1",
        "authority_class": "MECHANICAL_FIXTURE_ZERO_EVIDENCE" if fixture else "PIT_ARTIFACT",
        "financial_alpha_evidence": 0,
    }
    manifest_sha256 = domain_hash("ALPHA_PIT_V1:MANIFEST", manifest_body)
    manifest = {**manifest_body, "manifest_sha256": manifest_sha256}
    return ArtifactRef(
        artifact_type=artifact_type,
        manifest_sha256=manifest_sha256,
        payload_sha256=payload_sha256,
        manifest=manifest,
        payload=payload_value,
    )


def verify_artifact_ref(
    ref: ArtifactRef,
    *,
    family_contract: FamilyDataContract = CRV1_FAMILY_DATA_CONTRACT,
) -> None:
    """Recompute an in-memory Alpha PIT artifact closure and fail on drift."""

    if not isinstance(ref, ArtifactRef):
        raise TypeError("alpha_pit_artifact_ref_required")
    if not isinstance(family_contract, FamilyDataContract):
        raise AlphaPITContractError("alpha_pit_family_data_contract_required")
    manifest = dict(ref.manifest)
    manifest_sha256 = str(manifest.pop("manifest_sha256", ""))
    expected_manifest = domain_hash("ALPHA_PIT_V1:MANIFEST", canonical_value(manifest))
    if ref.manifest_sha256 != manifest_sha256 or manifest_sha256 != expected_manifest:
        raise AlphaPITContractError("alpha_pit_manifest_hash_mismatch")
    expected_payload = domain_hash(
        f"ALPHA_PIT_V1:PAYLOAD:{ref.artifact_type}", canonical_value(ref.payload)
    )
    if ref.payload_sha256 != expected_payload or manifest.get("payload_sha256") != expected_payload:
        raise AlphaPITContractError("alpha_pit_payload_hash_mismatch")
    if (
        manifest.get("api_schema_id") != API_SCHEMA_ID
        or manifest.get("family_id") != family_contract.family_id
        or manifest.get("family_data_contract") != family_contract.as_dict()
    ):
        raise AlphaPITContractError("alpha_pit_manifest_contract_invalid")
    if manifest.get("financial_alpha_evidence") != 0:
        raise AlphaPITContractError("alpha_pit_financial_alpha_evidence_must_be_zero")
    receipts = manifest.get("source_receipts")
    if not isinstance(receipts, list) or not receipts:
        raise AlphaPITContractError("alpha_pit_source_receipts_required")
    for binding in receipts:
        validate_source_receipt_binding(binding)
