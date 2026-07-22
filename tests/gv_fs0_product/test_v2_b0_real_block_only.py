"""Focused tests for GV-V2-B0 real block-only MU admission."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.gv_v2_b0_real_block_only import (
    BLOCK_MISSING_PIT,
    CASE_ID,
    DECISION_ID,
    EXPECTED_MU_CARD_SHA256,
    MU_CARD_REL,
    PORTFOLIO_ACTION_NO_POSITION,
    RESEARCH_ACTION_HOLD,
    RATIONALE_REF_PREFIX,
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
    assert "authorization_hash" in auth


def test_admission_blocks_missing_pit_for_research_card() -> None:
    admission = run_admission_checks(root=ROOT)
    assert admission["status"] == "BLOCKED"
    assert admission["primary_block_reason"] == BLOCK_MISSING_PIT
    assert BLOCK_MISSING_PIT in admission["block_reasons"]
    assert admission["admission_certificate"] is None
    assert admission["checks"]["point_in_time_availability"]["pass"] is False
    assert admission["checks"]["immutable_byte_identity"]["pass"] is True


def test_research_decision_holds_and_binds_admission() -> None:
    admission = run_admission_checks(root=ROOT)
    research = build_g_supply_research_decision(admission)
    assert research["research_action"] == RESEARCH_ACTION_HOLD
    assert research["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert research["decision_id"] == DECISION_ID
    assert research["rationale_ref"] == v2b0_rationale_ref(admission["admission_hash"])
    assert research["rationale_ref"].startswith(RATIONALE_REF_PREFIX)


def test_full_vertical_publishes_certified_no_position(tmp_path: Path) -> None:
    out = run_v2_b0_real_block_only(
        root=ROOT,
        case_dir=tmp_path / "case",
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
    assert out["case_id"] == CASE_ID
    assert out["admission_status"] == "BLOCKED"
    assert out["primary_block_reason"] == BLOCK_MISSING_PIT
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
