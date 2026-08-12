from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.replication_readiness_v1 import (
    ReplicationReadinessError,
    ReplicationReadinessManifestV1,
    write_manifest_once,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _pending_manifest(**overrides: object) -> ReplicationReadinessManifestV1:
    kwargs: dict[str, object] = {
        "replication_surface_id": "IRR-WRDS-CRSP-20260810",
        "created_at": "2026-08-10T12:20:00Z",
        "candidate_provider_id": "WRDS",
        "candidate_source_id": "CRSP_DSF_STOCKNAMES",
        "entitlement_status": "EVIDENCE_MISSING",
        "source_feasibility_status": "EVIDENCE_MISSING",
        "permanent_identity_status": "UNKNOWN",
        "permanent_identity_scheme": "CRSP_PERMNO+PERMCO",
        "permanent_identity_contract_id": None,
        "permanent_identity_contract_hash": None,
        "pit_vintage_status": "REVIEW_REQUIRED",
        "pit_vintage_contract_id": None,
        "pit_vintage_contract_hash": None,
        "license_status": "REVIEW_REQUIRED",
        "retention_status": "REVIEW_REQUIRED",
        "expected_acquisition_latency_class": "UNKNOWN",
    }
    kwargs.update(overrides)
    return ReplicationReadinessManifestV1(**kwargs)  # type: ignore[arg-type]


def _ready_manifest() -> ReplicationReadinessManifestV1:
    return _pending_manifest(
        entitlement_status="FEASIBLE",
        source_feasibility_status="FEASIBLE",
        permanent_identity_status="FEASIBLE",
        permanent_identity_contract_id="CRSP_PERMANENT_IDENTITY_V1",
        permanent_identity_contract_hash=HASH_A,
        pit_vintage_status="FEASIBLE",
        pit_vintage_contract_id="CRSP_PIT_VINTAGE_V1",
        pit_vintage_contract_hash=HASH_B,
        license_status="FEASIBLE",
        retention_status="FEASIBLE",
        expected_acquisition_latency_class="DAYS",
        entitlement_evidence_hashes=(HASH_A,),
        source_evidence_hashes=(HASH_B,),
        license_evidence_hashes=(HASH_C,),
    )


def test_pending_readiness_is_outcome_blind_and_does_not_authorize_acquisition() -> None:
    manifest = _pending_manifest()
    payload = manifest.to_dict()

    assert payload["readiness_status"] == "NOT_READY"
    assert payload["research_visibility"] == "READINESS_METADATA_ONLY"
    assert payload["replication_outcome_access"] == "DENIED"
    assert payload["family_specific_acquisition_authority"] == "NOT_AUTHORIZED"
    assert payload["financial_alpha_evidence"] == 0
    assert len(payload["manifest_hash"]) == 64


def test_readiness_contract_rejects_outcome_visibility_or_acquisition_authority() -> None:
    with pytest.raises(ReplicationReadinessError, match="outcome access"):
        _pending_manifest(replication_outcome_access="ALLOWED")
    with pytest.raises(ReplicationReadinessError, match="acquisition is not authorized"):
        _pending_manifest(family_specific_acquisition_authority="AUTHORIZED")
    with pytest.raises(ReplicationReadinessError, match="research_visibility"):
        _pending_manifest(research_visibility="FULL_RESEARCH_ACCESS")


def test_readiness_contract_rejects_ticker_only_identity() -> None:
    with pytest.raises(ReplicationReadinessError, match="ticker/name-only"):
        _pending_manifest(permanent_identity_scheme="TICKER")


def test_feasible_statuses_require_hash_bound_non_secret_evidence() -> None:
    with pytest.raises(ReplicationReadinessError, match="FEASIBLE entitlement"):
        _pending_manifest(entitlement_status="FEASIBLE")
    with pytest.raises(ReplicationReadinessError, match="FEASIBLE source"):
        _pending_manifest(source_feasibility_status="FEASIBLE")
    with pytest.raises(ReplicationReadinessError, match="FEASIBLE permanent identity"):
        _pending_manifest(permanent_identity_status="FEASIBLE")
    with pytest.raises(ReplicationReadinessError, match="FEASIBLE PIT/vintage"):
        _pending_manifest(pit_vintage_status="FEASIBLE")
    with pytest.raises(ReplicationReadinessError, match="FEASIBLE license/retention"):
        _pending_manifest(license_status="FEASIBLE")


def test_fully_feasible_readiness_still_stops_before_family_specific_acquisition() -> None:
    manifest = _ready_manifest()
    assert manifest.readiness_status == "READY_FOR_FAMILY_SPECIFIC_PREREGISTRATION"
    assert manifest.replication_outcome_access == "DENIED"
    assert manifest.family_specific_acquisition_authority == "NOT_AUTHORIZED"


def test_manifest_hash_changes_on_readiness_authority_mutation() -> None:
    pending = _pending_manifest()
    blocked = _pending_manifest(entitlement_status="BLOCKED")
    assert pending.manifest_hash != blocked.manifest_hash
    assert blocked.readiness_status == "BLOCKED"


def test_write_manifest_once_is_quarantine_only_and_immutable(tmp_path) -> None:
    manifest = _pending_manifest()
    target = tmp_path / "replication_quarantine" / "readiness" / "wrds.json"
    written = write_manifest_once(target, manifest)

    assert written == target
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload == manifest.to_dict()

    with pytest.raises(FileExistsError, match="immutable"):
        write_manifest_once(target, manifest)


def test_write_manifest_once_rejects_non_quarantine_path(tmp_path) -> None:
    with pytest.raises(ReplicationReadinessError, match="replication_quarantine"):
        write_manifest_once(tmp_path / "research" / "wrds.json", _pending_manifest())


def test_quarantine_namespace_cannot_point_to_research_tree() -> None:
    with pytest.raises(ReplicationReadinessError, match="replication_quarantine"):
        _pending_manifest(quarantine_namespace="research/current/replication")


def test_frozen_wrds_identity_pit_contracts_are_hash_bound_but_readiness_stays_not_ready() -> None:
    root = Path(__file__).resolve().parents[1]
    identity_path = root / "data/replication_quarantine/contracts_v1/wrds_5table_permanent_identity_contract_v1.json"
    pit_path = root / "data/replication_quarantine/contracts_v1/wrds_5table_pit_vintage_contract_v1.json"
    manifest_path = root / "data/replication_quarantine/readiness_v1/wrds_5table_readiness_20260810_v2.json"

    identity_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
    pit_hash = hashlib.sha256(pit_path.read_bytes()).hexdigest()
    assert identity_hash == "0c2beb0aa3f3e6e9a03fd218315fd8d738dd82ff176e08b6299ec04361427d4a"
    assert pit_hash == "a1afea3b0fad48404bec14f28e5c5c59c795bd2224619c0a7b2f6eb4a30661c9"

    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    pit = json.loads(pit_path.read_text(encoding="utf-8"))
    assert identity["canonical_security_identity"]["scheme"] == "CRSP_PERMNO"
    assert identity["replication_outcome_access"] == "DENIED"
    assert identity["family_specific_acquisition_authority"] == "NOT_AUTHORIZED"
    assert pit["replication_outcome_access"] == "DENIED"
    assert pit["family_specific_acquisition_authority"] == "NOT_AUTHORIZED"
    assert any("restated/current" in rule for rule in pit["fail_closed_rules"])

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = ReplicationReadinessManifestV1(
        replication_surface_id=payload["replication_surface_id"],
        created_at=payload["created_at"],
        candidate_provider_id=payload["candidate_provider_id"],
        candidate_source_id=payload["candidate_source_id"],
        entitlement_status=payload["entitlement_status"],
        source_feasibility_status=payload["source_feasibility_status"],
        permanent_identity_status=payload["permanent_identity_status"],
        permanent_identity_scheme=payload["permanent_identity_scheme"],
        permanent_identity_contract_id=payload["permanent_identity_contract_id"],
        permanent_identity_contract_hash=payload["permanent_identity_contract_hash"],
        pit_vintage_status=payload["pit_vintage_status"],
        pit_vintage_contract_id=payload["pit_vintage_contract_id"],
        pit_vintage_contract_hash=payload["pit_vintage_contract_hash"],
        license_status=payload["license_status"],
        retention_status=payload["retention_status"],
        expected_acquisition_latency_class=payload["expected_acquisition_latency_class"],
        entitlement_evidence_hashes=tuple(payload["entitlement_evidence_hashes"]),
        license_evidence_hashes=tuple(payload["license_evidence_hashes"]),
        source_evidence_hashes=tuple(payload["source_evidence_hashes"]),
        quarantine_namespace=payload["quarantine_namespace"],
        storage_policy_id=payload["storage_policy_id"],
        research_visibility=payload["research_visibility"],
        replication_outcome_access=payload["replication_outcome_access"],
        family_specific_acquisition_authority=payload["family_specific_acquisition_authority"],
    )
    assert manifest.to_dict() == payload
    assert manifest.readiness_status == "NOT_READY"
    assert manifest.permanent_identity_status == "FEASIBLE"
    assert manifest.pit_vintage_status == "FEASIBLE"
    assert manifest.entitlement_status == "EVIDENCE_MISSING"
    assert manifest.license_status == "REVIEW_REQUIRED"
    assert manifest.retention_status == "REVIEW_REQUIRED"

    evidence_status = json.loads(
        (root / "data/replication_quarantine/evidence_status/wrds_entitlement_license_retention_status_20260810.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence_status["entitlement_status"] == "EVIDENCE_MISSING"
    assert evidence_status["license_status"] == "REVIEW_REQUIRED"
    assert evidence_status["retention_status"] == "REVIEW_REQUIRED"
    assert evidence_status["credential_or_secret_contents_read"] is False
    assert evidence_status["wrds_provider_query_performed"] is False
    assert evidence_status["family_specific_replication_acquisition_performed"] is False
    assert evidence_status["replication_outcome_access"] == "DENIED"
    assert evidence_status["readiness_effect"] == "REMAINS_NOT_READY"
