"""Focused tests for GV-V2-B0A local-source abstention vertical."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.gv_v2_b0_real_block_only import (
    AUTH_PROVENANCE_LOCAL,
    BLOCK_MANIFEST_BINDING,
    BLOCK_MISSING_PIT,
    BLOCK_POSITIVE_ADMISSION,
    CASE_ID,
    DECISION_ID,
    EXPECTED_MU_CARD_SHA256,
    MU_CARD_REL,
    PORTFOLIO_ACTION_NO_POSITION,
    PURPOSE_LOCAL_ABSTENTION,
    RESEARCH_ACTION_ADVANCE,
    RESEARCH_ACTION_HOLD,
    RATIONALE_REF_PREFIX,
    SLICE_CLASSIFICATION,
    GvV2B0Error,
    build_data_access_authorization,
    build_g_supply_research_decision,
    build_source_manifest,
    run_admission_checks,
    run_v2_b0_real_block_only,
    v2b0_rationale_ref,
)
from core.gv_fs0_current_decision import parse_current_decision_bytes

ROOT = Path(__file__).resolve().parents[2]


def test_mu_card_package_hash_pinned() -> None:
    path = ROOT / MU_CARD_REL
    assert path.is_file()
    from hashlib import sha256

    assert sha256(path.read_bytes()).hexdigest() == EXPECTED_MU_CARD_SHA256


def test_access_authorization_has_no_credentials_and_binds_hash() -> None:
    auth = build_data_access_authorization(root=ROOT)
    raw = json.dumps(auth)
    assert "password" not in raw.lower()
    assert "secret" not in raw.lower()
    assert "token" not in raw.lower() or "token" in "credentials_boundary"
    assert auth["repository_artifact_sha256"] == EXPECTED_MU_CARD_SHA256
    assert auth["coverage"]["real_provider_read_authorized"] is False
    assert auth["retrieval_or_receipt_time"] is None
    assert auth["authorization_recorded_at"] == "2026-07-22T00:00:00.000000Z"
    assert auth["authorization_provenance"] == AUTH_PROVENANCE_LOCAL
    assert auth["purpose"] == PURPOSE_LOCAL_ABSTENTION
    assert auth["slice_classification"] == SLICE_CLASSIFICATION
    assert "authorization_hash" in auth


def test_admission_blocks_missing_pit_for_research_card() -> None:
    admission = run_admission_checks(root=ROOT)
    assert admission["status"] == "BLOCKED"
    assert admission["primary_block_reason"] == BLOCK_MISSING_PIT
    assert BLOCK_MISSING_PIT in admission["block_reasons"]
    assert BLOCK_MANIFEST_BINDING in admission["block_reasons"]
    assert admission["admission_certificate"] is None
    assert admission["checks"]["point_in_time_availability"]["pass"] is False
    assert admission["checks"]["package_manifest_binding"]["pass"] is False
    assert admission["checks"]["immutable_byte_identity"]["pass"] is True
    assert admission["slice_classification"] == SLICE_CLASSIFICATION


def test_research_decision_holds_and_binds_admission() -> None:
    admission = run_admission_checks(root=ROOT)
    research = build_g_supply_research_decision(admission)
    assert research["research_action"] == RESEARCH_ACTION_HOLD
    assert research["research_action"] != RESEARCH_ACTION_ADVANCE
    assert research["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert research["decision_id"] == DECISION_ID
    assert research["rationale_ref"] == v2b0_rationale_ref(admission["admission_hash"])
    assert research["rationale_ref"].startswith(RATIONALE_REF_PREFIX)
    assert research["slice_classification"] == SLICE_CLASSIFICATION


def test_full_vertical_publishes_certified_no_position(tmp_path: Path) -> None:
    out = run_v2_b0_real_block_only(
        root=ROOT,
        case_dir=tmp_path / "case",
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
    assert out["case_id"] == CASE_ID
    assert out["slice_classification"] == SLICE_CLASSIFICATION
    assert out["admission_status"] == "BLOCKED"
    assert out["primary_block_reason"] == BLOCK_MISSING_PIT
    assert BLOCK_MANIFEST_BINDING in out["block_reasons"]
    assert out["research_action"] == RESEARCH_ACTION_HOLD
    assert out["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert out["certification_status"] == "CERTIFIED"
    assert out["shipped_product_score"] == 39
    assert out["observed_comparison_count"] == 0
    assert out["published"] is True

    case = tmp_path / "case"
    for name in (
        "access_authorization.json",
        "source_manifest.json",
        "admission_result.json",
        "research_decision.json",
        "result.json",
        "decision_packet.md",
    ):
        assert (case / name).is_file()

    admission = json.loads((case / "admission_result.json").read_text(encoding="utf-8"))
    assert admission["admission_certificate"] is None
    assert admission["status"] == "BLOCKED"
    auth = json.loads((case / "access_authorization.json").read_text(encoding="utf-8"))
    assert auth["retrieval_or_receipt_time"] is None
    assert auth["authorization_provenance"] == AUTH_PROVENANCE_LOCAL
    result = json.loads((case / "result.json").read_text(encoding="utf-8"))
    assert result["data_admission_certificates_earned"] == 0
    assert result["real_external_source_packages_processed"] == 0
    packet = (case / "decision_packet.md").read_text(encoding="utf-8")
    assert "Local Source Abstention" in packet
    assert "real block-only" not in packet.lower() or "not a real external" in packet.lower()

    component = parse_current_decision_bytes((tmp_path / "current.json").read_bytes())
    assert component["decision"]["decision_id"] == DECISION_ID
    assert component["decision"]["action"] == PORTFOLIO_ACTION_NO_POSITION
    assert component["decision"]["rationale_ref"] == out["rationale_ref"]
    assert component["certification"]["certification_status"] == "CERTIFIED"


def test_source_manifest_binds_access_hash() -> None:
    auth = build_data_access_authorization(root=ROOT)
    manifest = build_source_manifest(root=ROOT, access_authorization=auth)
    assert manifest["access_authorization_hash"] == auth["authorization_hash"]
    assert manifest["point_in_time_available"] is False
    assert any(f["path"] == MU_CARD_REL for f in manifest["files"])


def test_package_manifest_binding_invalid_retained() -> None:
    """Historical package declares a non-matching artifact_sha256; must block."""
    admission = run_admission_checks(root=ROOT)
    assert BLOCK_MANIFEST_BINDING in admission["block_reasons"]
    assert admission["checks"]["package_manifest_binding"]["pass"] is False
    detail = str(admission["checks"]["package_manifest_binding"]["detail"])
    assert "sha_mismatch" in detail
    # Historical package bytes are preserved (declared hash still wrong on disk).
    pkg = json.loads(
        (ROOT / "data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert pkg["artifact_sha256"] != EXPECTED_MU_CARD_SHA256


def test_positive_admission_input_rejected() -> None:
    """ADMITTED input must not auto-advance research."""
    fake_admitted = {
        "status": "ADMITTED",
        "admission_hash": "a" * 64,
        "primary_block_reason": None,
        "block_reasons": [],
    }
    with pytest.raises(GvV2B0Error, match=BLOCK_POSITIVE_ADMISSION):
        build_g_supply_research_decision(fake_admitted)


def test_forbidden_use_failure_blocks() -> None:
    """Computed forbidden-use result is used; missing ban fails closed."""
    auth = build_data_access_authorization(root=ROOT)
    auth["forbidden_use"] = [
        u for u in auth["forbidden_use"] if u != "synthetic_as_real_evidence"
    ]
    # Re-hash after mutation so domain binding still forms a coherent object
    # for the admission path that only checks fields (manifest rebind separately).
    from core.gv_fs0_canonical import domain_hash
    from core.gv_v2_b0_real_block_only import ACCESS_AUTH_DOMAIN

    auth.pop("authorization_hash", None)
    auth["authorization_hash"] = domain_hash(ACCESS_AUTH_DOMAIN, auth)
    manifest = build_source_manifest(root=ROOT, access_authorization=auth)
    admission = run_admission_checks(
        root=ROOT, access_authorization=auth, source_manifest=manifest
    )
    assert admission["status"] == "BLOCKED"
    assert admission["checks"]["forbidden_use_enforcement"]["pass"] is False
    assert admission["admission_certificate"] is None


def test_no_automatic_advancement_on_blocked_path() -> None:
    admission = run_admission_checks(root=ROOT)
    research = build_g_supply_research_decision(admission)
    assert research["research_action"] == RESEARCH_ACTION_HOLD
    assert research["research_action"] != RESEARCH_ACTION_ADVANCE
    # Rationale may mention ADVANCE as forbidden; action field must not be it.
    assert research["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION


def test_admission_never_emits_admitted_status() -> None:
    admission = run_admission_checks(root=ROOT)
    assert admission["status"] != "ADMITTED"
    assert admission["status"] == "BLOCKED"
    assert admission["admission_certificate"] is None
