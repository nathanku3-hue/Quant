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
    derive_sec_package_identity,
    evaluate_g_supply_claim,
    load_access_authorization,
    load_verified_b0b_result,
    run_admission_checks,
    run_v2_b0b_official_source_intake,
    v2b0b_rationale_ref,
    verify_b0b_chain,
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


def test_source_pit_derived_from_sec_header() -> None:
    derived = derive_sec_package_identity(root=ROOT)
    assert derived["accession"] == ACCESSION
    assert derived["cik"] == "0000723125"
    assert derived["form"] == "10-Q"
    assert derived["acceptance_datetime"] == "2026-06-24T18:59:46.000000Z"
    assert derived["period_ended"] == "2026-05-28"
    assert derived["filed_at"] == "2026-06-25"
    assert derived["primary_document_filename"] == "mu-20260528.htm"

    admission = run_admission_checks(root=ROOT)
    # Rebuild source path via admission bindings.
    from core.gv_v2_b0b_official_source_intake import build_source_manifest

    source = build_source_manifest(root=ROOT)
    assert source["publication_time"] == derived["acceptance_datetime"]
    assert source["known_at"] == derived["acceptance_datetime"]
    assert source["source_derived_pit"]["filed_at"] == derived["filed_at"]
    assert source["entity_identity"]["primary_document_filename"] == "mu-20260528.htm"
    assert admission["status"] == "ADMITTED"


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
    assert claim["contradiction_status"] == CONTRADICTION_NOT_EVALUATED
    dims = claim["evidence_dimensions"]
    assert dims["official_filing_admitted"] == "PASS"
    assert dims["relevant_issuer_supply_assertions_present"] == "PASS"
    assert dims["capacity_facility_disclosures_present"] == "PASS"
    assert dims["independent_source_corroboration"] == "FAIL"
    assert dims["physical_supply_telemetry"] == "FAIL"
    assert dims["cross_source_contradiction_evaluation"] == "NOT_EVALUATED"
    assert dims["sufficient_for_research_advancement"] == "FAIL"
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
    research = build_g_supply_research_decision(admission, claim, root=ROOT)
    assert admission["status"] == "ADMITTED"
    assert research["research_action"] == RESEARCH_ACTION_HOLD
    assert research["research_action"] != RESEARCH_ACTION_ADVANCE
    assert research["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert research["rationale_ref"].startswith(RATIONALE_REF_PREFIX)
    assert research["claim_evaluation_hash"] == claim["claim_evaluation_hash"]
    assert research["admission_hash"] == admission["admission_hash"]


def test_stale_claim_hash_mutation_raises_integrity_error() -> None:
    """Tampering claim_outcome while leaving hash stale must fail closed."""

    admission = run_admission_checks(root=ROOT)
    claim = evaluate_g_supply_claim(root=ROOT, admission=admission)
    fake = dict(claim)
    fake["claim_outcome"] = CLAIM_SUFFICIENT
    # Hash is intentionally stale relative to mutated outcome.
    with pytest.raises(GvV2B0BError, match="CLAIM_EVALUATION_HASH_MISMATCH"):
        build_g_supply_research_decision(admission, fake, root=ROOT)


def test_sufficient_claim_not_authorized_in_b0b() -> None:
    """Even a rehashed SUFFICIENT claim cannot ADVANCE in the B0B slice."""

    from core.gv_fs0_canonical import domain_hash
    from core.gv_v2_b0b_official_source_intake import CLAIM_DOMAIN

    admission = run_admission_checks(root=ROOT)
    claim = evaluate_g_supply_claim(root=ROOT, admission=admission)
    fake = {k: v for k, v in claim.items() if k != "claim_evaluation_hash"}
    fake["claim_outcome"] = CLAIM_SUFFICIENT
    fake["claim_evaluation_hash"] = domain_hash(CLAIM_DOMAIN, fake)
    with pytest.raises(GvV2B0BError, match="CLAIM_OUTCOME_NOT_AUTHORIZED_IN_B0B"):
        build_g_supply_research_decision(admission, fake, root=ROOT)


def test_rehashed_contradicted_claim_not_authorized_in_b0b() -> None:
    """Rehashed CLAIM_CONTRADICTED must not open REJECT_THESIS in B0B."""

    from core.gv_fs0_canonical import domain_hash
    from core.gv_v2_b0b_official_source_intake import CLAIM_CONTRADICTED, CLAIM_DOMAIN

    admission = run_admission_checks(root=ROOT)
    claim = evaluate_g_supply_claim(root=ROOT, admission=admission)
    fake = {k: v for k, v in claim.items() if k != "claim_evaluation_hash"}
    fake["claim_outcome"] = CLAIM_CONTRADICTED
    fake["claim_evaluation_hash"] = domain_hash(CLAIM_DOMAIN, fake)
    with pytest.raises(GvV2B0BError, match="CLAIM_OUTCOME_NOT_AUTHORIZED_IN_B0B"):
        build_g_supply_research_decision(admission, fake, root=ROOT)


def test_rehashed_false_locator_rejected_by_canonical_rebuild() -> None:
    """Hash-self-consistent package with false SEC locator fails rebuild compare."""

    from core.gv_fs0_canonical import domain_hash
    from core.gv_v2_b0b_official_source_intake import (
        PACKAGE_MANIFEST_DOMAIN,
        build_source_manifest,
        verify_b0b_chain,
    )

    auth = load_access_authorization(root=ROOT)
    package = build_package_manifest(root=ROOT, access_authorization=auth)
    # Mutate an official locator and rehash — proves hash self-consistency is not enough.
    fake_package = {k: v for k, v in package.items() if k != "package_manifest_hash"}
    objects = [dict(o) for o in fake_package["objects"]]
    objects[0] = dict(objects[0])
    objects[0]["official_locator"] = "https://evil.example/false-sec-locator"
    fake_package["objects"] = objects
    fake_package["package_manifest_hash"] = domain_hash(PACKAGE_MANIFEST_DOMAIN, fake_package)

    # Rehashed body is self-consistent.
    from core.gv_v2_b0b_official_source_intake import recompute_domain_hash

    assert (
        recompute_domain_hash(
            PACKAGE_MANIFEST_DOMAIN, fake_package, "package_manifest_hash"
        )
        == fake_package["package_manifest_hash"]
    )

    source = build_source_manifest(
        root=ROOT, access_authorization=auth, package_manifest=package
    )
    admission = run_admission_checks(
        root=ROOT,
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
    )
    claim = evaluate_g_supply_claim(
        root=ROOT, admission=admission, package_manifest=package
    )
    research = build_g_supply_research_decision(admission, claim, root=ROOT)
    with pytest.raises(GvV2B0BError, match="PACKAGE_NOT_CANONICAL"):
        verify_b0b_chain(
            root=ROOT,
            access_authorization=auth,
            package_manifest=fake_package,
            source_manifest=source,
            admission=admission,
            claim=claim,
            research=research,
            result=None,
        )


def test_load_verified_rejects_rehashed_claim_outcome(tmp_path: Path) -> None:
    """Banked rehashed CLAIM_CONTRADICTED fails canonical rebuild compare."""

    import shutil

    from core.gv_fs0_canonical import domain_hash
    from core.gv_v2_b0b_official_source_intake import CLAIM_CONTRADICTED, CLAIM_DOMAIN

    src = ROOT / "data/gv_v2_b0b/mu_0000723125-26-000015"
    case = tmp_path / "bank"
    shutil.copytree(src, case)
    claim_path = case / "claim_evaluation.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    body = {k: v for k, v in claim.items() if k != "claim_evaluation_hash"}
    body["claim_outcome"] = CLAIM_CONTRADICTED
    body["claim_evaluation_hash"] = domain_hash(CLAIM_DOMAIN, body)
    claim_path.write_bytes(
        (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    )
    with pytest.raises(GvV2B0BError, match="CLAIM_NOT_CANONICAL"):
        load_verified_b0b_result(root=ROOT, case_dir=case)


def test_full_vertical_publishes_certified_no_position(tmp_path: Path) -> None:
    out = run_v2_b0b_official_source_intake(
        root=ROOT,
        case_dir=tmp_path / "case",
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
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
    verified = load_verified_b0b_result(root=ROOT, case_dir=case)
    assert verified["admission_hash"]
    assert verified["claim_evaluation_hash"]
    assert verified["data_admission_certificates_earned"] == 1
    assert verified["claim_outcome"] == CLAIM_INSUFFICIENT


def test_load_verified_b0b_result_rejects_tampered_claim_field(tmp_path: Path) -> None:
    import shutil

    src = ROOT / "data/gv_v2_b0b/mu_0000723125-26-000015"
    case = tmp_path / "bank"
    shutil.copytree(src, case)
    run_v2_b0b_official_source_intake(
        root=ROOT,
        case_dir=case,
        publish=False,
    )
    claim_path = case / "claim_evaluation.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    # Stale hash (no rehash) — fails canonical rebuild compare.
    claim["claim_outcome"] = CLAIM_SUFFICIENT
    claim_path.write_text(
        json.dumps(claim, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(GvV2B0BError, match="CLAIM_NOT_CANONICAL"):
        load_verified_b0b_result(root=ROOT, case_dir=case)


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
