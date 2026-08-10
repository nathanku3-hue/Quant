"""Immutable CRV1 input-packet closure over Alpha PIT read artifacts only."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import FAMILY_ID, ArtifactRef, utc_datetime
from research.alpha_pit_v1.manifests import canonical_value
from research.alpha_pit_v1.session import AlphaPITReadAPIv1
from research.cycle_resonance_v1.contracts import (
    FIXTURE_AUTHORITY_CLASS,
    INPUT_PACKET_SCHEMA,
    REAL_PIT_AUTHORITY_CLASS,
    REQUESTED_OBSERVATION_FIELDS,
    validate_family_constants,
)


def build_cycle_resonance_input_packet(
    *,
    api: AlphaPITReadAPIv1,
    implementation_id: str,
    decision_context_id: str,
    as_of: datetime,
    coverage_policy_id: str,
) -> dict[str, Any]:
    """Close one deterministic CRV1 packet without provider or outcome access."""

    validate_family_constants()
    cutoff = utc_datetime(as_of)
    implementation = str(implementation_id).strip()
    decision_context = str(decision_context_id).strip()
    coverage_policy = str(coverage_policy_id).strip()
    if not implementation:
        raise ValueError("cycle_resonance_implementation_id_required")
    if not decision_context:
        raise ValueError("cycle_resonance_decision_context_id_required")
    if not coverage_policy:
        raise ValueError("cycle_resonance_coverage_policy_id_required")
    if api.family_id != FAMILY_ID:
        raise ValueError("cycle_resonance_alpha_pit_family_mismatch")
    if api.decision_context_id != decision_context:
        raise ValueError("cycle_resonance_decision_context_mismatch")

    risk_set = api.risk_set(as_of=cutoff)
    risk_payload = _payload_mapping(risk_set, artifact_type="RISK_SET")
    rows = risk_payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("cycle_resonance_empty_risk_set")
    security_ids = tuple(str(row["security_id"]) for row in rows)

    observations = api.observations(
        ids=security_ids,
        fields=REQUESTED_OBSERVATION_FIELDS,
        as_of=cutoff,
    )
    claims = api.source_claims(ids=security_ids, as_of=cutoff)
    expectations = api.expectations(ids=security_ids, as_of=cutoff)
    refs = (risk_set, observations, claims, expectations)

    authority_classes = {str(ref.manifest.get("authority_class") or "") for ref in refs}
    if authority_classes == {FIXTURE_AUTHORITY_CLASS}:
        authority_class = FIXTURE_AUTHORITY_CLASS
    elif authority_classes == {"PIT_ARTIFACT"}:
        authority_class = REAL_PIT_AUTHORITY_CLASS
    else:
        raise ValueError("cycle_resonance_mixed_input_authority_forbidden")

    source_receipt_hashes = tuple(sorted(_source_receipt_hashes(refs)))
    as_of_text = cutoff.isoformat(timespec="microseconds").replace("+00:00", "Z")
    body: dict[str, Any] = {
        "schema_version": INPUT_PACKET_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": implementation,
        "research_mode": api.research_mode.value,
        "decision_context_id": decision_context,
        "as_of": as_of_text,
        "risk_set_id": str(risk_payload.get("risk_set_id") or ""),
        "risk_set_manifest_sha256": risk_set.manifest_sha256,
        "observations_manifest_sha256": observations.manifest_sha256,
        "claims_manifest_sha256": claims.manifest_sha256,
        "expectations_manifest_sha256": expectations.manifest_sha256,
        "source_manifest_sha256s": list(source_receipt_hashes),
        "coverage_policy_id": coverage_policy,
        "authority_class": authority_class,
        "financial_alpha_evidence": 0,
    }
    if not body["risk_set_id"]:
        raise ValueError("cycle_resonance_risk_set_id_required")
    packet_hash = domain_hash("CYCLE_RESONANCE_V1:INPUT_PACKET", canonical_value(body))
    return {**body, "input_packet_sha256": packet_hash}


def _payload_mapping(ref: ArtifactRef, *, artifact_type: str) -> Mapping[str, Any]:
    if ref.artifact_type != artifact_type:
        raise ValueError("cycle_resonance_artifact_type_mismatch")
    if not isinstance(ref.payload, Mapping):
        raise ValueError("cycle_resonance_payload_mapping_required")
    return ref.payload


def _source_receipt_hashes(refs: Sequence[ArtifactRef]) -> set[str]:
    hashes: set[str] = set()
    for ref in refs:
        receipts = ref.manifest.get("source_receipts")
        if not isinstance(receipts, list) or not receipts:
            raise ValueError("cycle_resonance_source_receipts_required")
        for binding in receipts:
            if not isinstance(binding, Mapping):
                raise ValueError("cycle_resonance_source_receipt_mapping_required")
            digest = str(binding.get("raw_receipt_sha256") or "")
            if len(digest) != 64:
                raise ValueError("cycle_resonance_source_receipt_hash_invalid")
            hashes.add(digest)
    return hashes
