"""Tests for GV-ALPHA0 source family two vertical."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.gv_fs0_current_decision import parse_current_decision_bytes
from core.gv_v2_alpha0_source_family_two import (
    ACCESSION,
    DECISION_ID,
    EXPECTED_AUTH_HASH,
    FACT_NEEDLES,
    FAMILY_ONE_ID,
    PACKAGE_OBJECTS,
    PORTFOLIO_ACTION_NO_POSITION,
    RESEARCH_ACTION_HOLD,
    SLICE_CLASSIFICATION,
    SOURCE_FAMILY_ID,
    GvAlpha0Sf2Error,
    build_package_manifest,
    capture_operator_decision,
    extract_case_facts,
    load_access_authorization,
    run_admission_checks,
    run_v2_alpha0_source_family_two,
)

ROOT = Path(__file__).resolve().parents[2]


def test_pre_read_auth_null_receipt_and_pin() -> None:
    auth = load_access_authorization(root=ROOT)
    assert auth["authorization_hash"] == EXPECTED_AUTH_HASH
    assert auth["retrieval_or_receipt_time"] is None
    assert auth["accession"] == ACCESSION
    assert auth["source_family_id"] == SOURCE_FAMILY_ID


def test_package_exact_three_objects_independent_of_family_one() -> None:
    package = build_package_manifest(root=ROOT)
    assert package["source_family_id"] == SOURCE_FAMILY_ID
    assert package["family_one_reference"] == FAMILY_ONE_ID
    assert package["independent_source_count"] == 1
    assert {o["filename"] for o in package["objects"]} == {
        s["filename"] for s in PACKAGE_OBJECTS
    }
    assert package["source_family_id"] != FAMILY_ONE_ID


def test_admission_and_three_to_five_byte_facts() -> None:
    admission = run_admission_checks(root=ROOT)
    assert admission["status"] == "ADMITTED"
    assert admission["admission_certificate"] is not None
    facts = extract_case_facts(root=ROOT, admission=admission)
    assert 3 <= facts["fact_count"] <= 5
    assert facts["fact_count"] == len(FACT_NEEDLES)
    for fact in facts["facts"]:
        assert fact["byte_end"] > fact["byte_start"]
        assert fact["source_family_id"] == SOURCE_FAMILY_ID
        assert fact["independent_source_count_contribution"] == 1


def test_operator_capture_and_certified_vertical(tmp_path: Path) -> None:
    out = run_v2_alpha0_source_family_two(
        root=ROOT,
        case_dir=tmp_path / "case",
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
    assert out["slice_classification"] == SLICE_CLASSIFICATION
    assert out["admission_status"] == "ADMITTED"
    assert out["fact_count"] == 5
    assert out["research_action"] == RESEARCH_ACTION_HOLD
    assert out["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert out["decision_id"] == DECISION_ID
    assert out["certification_status"] == "CERTIFIED"
    assert out["shipped_product_score"] == 39
    assert out["observed_comparison_count"] == 0
    assert out["reconciliation_status"] == "NOT_RUN"
    assert out["formal_comparison_status"] == "DEFERRED_AFTER_ALPHA"
    assert out["published"] is True

    case = tmp_path / "case"
    for name in (
        "access_authorization.json",
        "package_manifest.json",
        "admission_result.json",
        "fact_set.json",
        "operator_decision_capture.json",
        "research_decision.json",
        "result.json",
        "decision_packet.md",
    ):
        assert (case / name).is_file()
    assert not (case / ".alpha0_tx").exists()

    component = parse_current_decision_bytes((tmp_path / "current.json").read_bytes())
    assert component["decision"]["decision_id"] == DECISION_ID
    assert component["decision"]["action"] == PORTFOLIO_ACTION_NO_POSITION


def test_auth_object_mismatch_rejected() -> None:
    auth = load_access_authorization(root=ROOT)
    fake = dict(auth)
    objects = [dict(o) for o in fake["authorized_objects"]]
    objects[0] = dict(objects[0])
    objects[0]["official_locator"] = "https://evil.example/x"
    fake["authorized_objects"] = objects
    with pytest.raises(GvAlpha0Sf2Error, match="AUTHORIZED_OBJECTS_MISMATCH"):
        build_package_manifest(root=ROOT, access_authorization=fake)


def test_operator_requires_admitted_facts() -> None:
    admission = run_admission_checks(root=ROOT)
    fact_set = extract_case_facts(root=ROOT, admission=admission)
    blocked = dict(admission)
    blocked["status"] = "BLOCKED"
    with pytest.raises(GvAlpha0Sf2Error, match="OPERATOR_REQUIRES_ADMITTED"):
        capture_operator_decision(admission=blocked, fact_set=fact_set)
