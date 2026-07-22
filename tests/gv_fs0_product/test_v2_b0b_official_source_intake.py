"""Focused tests for GV-V2-B0B official-source intake vertical."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from core.gv_fs0_current_decision import parse_current_decision_bytes
from core.gv_v2_b0b_official_source_intake import (
    ACCESSION,
    CLAIM_INSUFFICIENT,
    CLAIM_SUFFICIENT,
    CONTRADICTION_NOT_EVALUATED,
    DECISION_ID,
    EXPECTED_AUTH_HASH,
    PACKAGE_OBJECTS,
    PORTFOLIO_ACTION_NO_POSITION,
    RESEARCH_ACTION_ADVANCE,
    RESEARCH_ACTION_HOLD,
    RATIONALE_REF_PREFIX,
    SLICE_CLASSIFICATION,
    SOURCE_FAMILY_ID,
    GvV2B0BError,
    build_g_supply_research_decision,
    build_package_manifest,
    evaluate_g_supply_claim,
    load_access_authorization,
    run_admission_checks,
    run_v2_b0b_official_source_intake,
    v2b0b_rationale_ref,
)

ROOT = Path(__file__).resolve().parents[2]


def test_authorization_pre_read_and_null_receipt() -> None:
    auth = load_access_authorization(root=ROOT)
    assert auth["authorization_hash"] == EXPECTED_AUTH_HASH
    assert auth["retrieval_or_receipt_time"] is None
    assert auth["accession"] == ACCESSION
    assert "password" not in json.dumps(auth).lower()
    raw = json.dumps(auth)
    assert "secret" not in raw.lower() or "none" in str(auth.get("credentials_boundary")).lower()


def test_package_exact_three_objects_and_hashes() -> None:
    package = build_package_manifest(root=ROOT)
    assert package["independent_source_count"] == 1
    assert package["source_family_id"] == SOURCE_FAMILY_ID
    names = {o["filename"] for o in package["objects"]}
    assert names == {spec["filename"] for spec in PACKAGE_OBJECTS}
    for spec in PACKAGE_OBJECTS:
        path = ROOT / "data/gv_v2_b0b/mu_0000723125-26-000015/raw" / spec["filename"]
        assert path.is_file()
        assert sha256(path.read_bytes()).hexdigest() == spec["expected_sha256"]
        assert str(path.stat().st_size) == spec["expected_byte_length"]


def test_auth_before_retrieval_ordering() -> None:
    auth = load_access_authorization(root=ROOT)
    package = build_package_manifest(root=ROOT)
    assert auth["authorization_recorded_at"] < package["retrieved_at"]
    for obj in package["objects"]:
        assert auth["authorization_recorded_at"] < obj["retrieved_at"]


def test_admission_admitted_with_certificate_and_not_evaluated_contradiction() -> None:
    admission = run_admission_checks(root=ROOT)
    assert admission["status"] == "ADMITTED"
    assert admission["admission_certificate"] is not None
    assert admission["admission_certificate"]["admission_certificate_hash"]
    contradiction = admission["checks"]["contradictions"]
    assert contradiction["status"] == CONTRADICTION_NOT_EVALUATED
    assert contradiction["pass"] is None
    assert admission["independent_source_count"] == 1


def test_claim_insufficient_one_issuer_source() -> None:
    claim = evaluate_g_supply_claim(root=ROOT)
    assert claim["claim_outcome"] == CLAIM_INSUFFICIENT
    assert claim["independent_source_count"] == 1
    assert len(claim["statements"]) >= 3
    for stmt in claim["statements"]:
        assert stmt["source_object_hash"]
        assert stmt["document_locator"]
        assert stmt["section_or_element_locator"]
        assert stmt["exact_excerpt_hash"]
        assert stmt["statement_class"] in {
            "FINANCIAL_FACT",
            "CONTRACTUAL_DISCLOSURE",
            "ISSUER_ASSERTION",
            "FORWARD_LOOKING_STATEMENT",
            "RISK_DISCLOSURE",
        }
        assert stmt["independent_source_count_contribution"] == 0


def test_admitted_does_not_auto_advance() -> None:
    admission = run_admission_checks(root=ROOT)
    claim = evaluate_g_supply_claim(root=ROOT, admission=admission)
    research = build_g_supply_research_decision(admission, claim)
    assert admission["status"] == "ADMITTED"
    assert research["research_action"] == RESEARCH_ACTION_HOLD
    assert research["research_action"] != RESEARCH_ACTION_ADVANCE
    assert research["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert research["rationale_ref"].startswith(RATIONALE_REF_PREFIX)
    assert research["claim_evaluation_hash"] == claim["claim_evaluation_hash"]
    assert research["admission_hash"] == admission["admission_hash"]


def test_advance_requires_sufficient_claim() -> None:
    admission = run_admission_checks(root=ROOT)
    claim = evaluate_g_supply_claim(root=ROOT, admission=admission)
    fake = dict(claim)
    fake["claim_outcome"] = CLAIM_SUFFICIENT
    # Hash is stale; research still maps by outcome fields.
    research = build_g_supply_research_decision(admission, fake)
    assert research["research_action"] == RESEARCH_ACTION_ADVANCE
    assert research["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION


def test_full_vertical_publishes_certified_no_position(tmp_path: Path) -> None:
    out = run_v2_b0b_official_source_intake(
        root=ROOT,
        case_dir=tmp_path / "case",
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
    # case_dir lacks pre-read auth bank — runner requires auth in ROOT auth path
    # but writes other artifacts to case_dir. Re-run with default case under tmp
    # is awkward; instead assert via tracked bank path after publish-only.
    assert out["case_id"]
    assert out["slice_classification"] == SLICE_CLASSIFICATION
    assert out["admission_status"] == "ADMITTED"
    assert out["claim_outcome"] == CLAIM_INSUFFICIENT
    assert out["research_action"] == RESEARCH_ACTION_HOLD
    assert out["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert out["decision_id"] == DECISION_ID
    assert out["certification_status"] == "CERTIFIED"
    assert out["shipped_product_score"] == 39
    assert out["observed_comparison_count"] == 0
    assert out["real_external_source_packages_processed"] == 1
    assert out["data_admission_certificates_earned"] == 1
    assert out["published"] is True

    component = parse_current_decision_bytes((tmp_path / "current.json").read_bytes())
    assert component["decision"]["decision_id"] == DECISION_ID
    assert component["decision"]["action"] == PORTFOLIO_ACTION_NO_POSITION
    assert component["decision"]["rationale_ref"] == out["rationale_ref"]
    assert component["certification"]["certification_status"] == "CERTIFIED"


def test_full_vertical_on_banked_case_dir(tmp_path: Path) -> None:
    """Banked case keeps pre-read auth; other artifacts rewrite under same dir."""
    import shutil

    src = ROOT / "data/gv_v2_b0b/mu_0000723125-26-000015"
    case = tmp_path / "bank"
    shutil.copytree(src, case)
    out = run_v2_b0b_official_source_intake(
        root=ROOT,
        case_dir=case,
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
    assert out["admission_status"] == "ADMITTED"
    for name in (
        "package_manifest.json",
        "source_manifest.json",
        "admission_result.json",
        "claim_evaluation.json",
        "research_decision.json",
        "result.json",
        "decision_packet.md",
        "access_authorization.json",
    ):
        assert (case / name).is_file()
    result = json.loads((case / "result.json").read_text(encoding="utf-8"))
    assert result["admission_hash"]
    assert result["claim_evaluation_hash"]
    assert result["data_admission_certificates_earned"] == 1


def test_rationale_ref_helper() -> None:
    claim = evaluate_g_supply_claim(root=ROOT)
    assert v2b0b_rationale_ref(claim["claim_evaluation_hash"]).startswith(RATIONALE_REF_PREFIX)
    with pytest.raises(GvV2B0BError):
        v2b0b_rationale_ref("not-a-hash")


def test_reversed_auth_receipt_order_rejected(tmp_path: Path) -> None:
    from core.gv_v2_b0b_official_source_intake import _assert_auth_before_receipt

    with pytest.raises(GvV2B0BError, match="AUTH_RECEIPT_ORDERING"):
        _assert_auth_before_receipt(
            "2026-07-22T18:00:00.000000Z",
            "2026-07-22T17:00:00.000000Z",
        )
    with pytest.raises(GvV2B0BError, match="AUTH_RECEIPT_ORDERING"):
        _assert_auth_before_receipt(
            "2026-07-22T17:00:00.000000Z",
            "2026-07-22T17:00:00.000000Z",
        )
