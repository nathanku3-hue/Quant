"""Tests for GV-ALPHA0-CLOSE multi-source case vertical."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.gv_v2_alpha0_case_close import (
    CASE_DIR,
    CASE_ID,
    CAPTURE_SURFACE_UI,
    CLAIM_OUTCOME_INSUFFICIENT,
    COVERAGE_PARTIAL,
    DECISION_ID,
    FUNCTIONAL_STAGE_BANKED,
    FUNCTIONAL_STAGE_OPERABLE,
    FUNCTIONAL_STAGE_PRE_ADJUDICATION,
    OBSERVED_COMPARISON_COUNT,
    OPERATOR_CONFIRMATION_PHRASE,
    PORTFOLIO_ACTION_NO_POSITION,
    RESEARCH_ACTION_HOLD,
    SHIPPED_PRODUCT_SCORE,
    SLICE_CLASSIFICATION,
    GvAlpha0CloseError,
    build_case_claim,
    build_case_manifest,
    build_coverage_assessment,
    build_operator_confirmation,
    capture_case_workspace_adjudication,
    confirm_operator_and_certify,
    load_banked_case_workspace,
    load_family_pins,
    rebuild_canonical_close_chain,
    rebuild_pre_adjudication_chain,
    replay_export_bundle,
    run_v2_alpha0_case_close,
    seal_pre_adjudication_case,
    verify_close_chain,
)

ROOT = Path(__file__).resolve().parents[2]


def test_family_pins_bind_both_hashes_not_ids_alone() -> None:
    pins = load_family_pins(root=ROOT)
    f1 = pins["family_one"]
    f2 = pins["family_two"]
    assert f1["package_manifest_hash"]
    assert f1["admission_hash"]
    assert f1["claim_evaluation_hash"]
    assert f2["package_manifest_hash"]
    assert f2["admission_hash"]
    assert f2["fact_set_hash"]
    assert f1["source_family_id"] != f2["source_family_id"]
    assert f2["fact_count"] == 5


def test_case_manifest_contains_cutoff_and_both_family_hashes() -> None:
    manifest = build_case_manifest(root=ROOT)
    assert manifest["case_id"] == CASE_ID
    assert manifest["slice_classification"] == SLICE_CLASSIFICATION
    assert "cutoff_at" in manifest["cutoff"]
    assert manifest["family_one"]["package_manifest_hash"]
    assert manifest["family_two"]["package_manifest_hash"]
    assert manifest["family_one"]["admission_hash"]
    assert manifest["family_two"]["admission_hash"]
    assert manifest["family_two"]["fact_set_hash"]
    assert manifest["independent_source_count"] == 2
    assert manifest["case_manifest_hash"]


def test_coverage_partial_is_not_claim_sufficiency() -> None:
    manifest = build_case_manifest(root=ROOT)
    coverage = build_coverage_assessment(manifest, root=ROOT)
    claim = build_case_claim(manifest, coverage)
    assert coverage["coverage_status"] == COVERAGE_PARTIAL
    meaning = coverage["coverage_meaning"].lower()
    assert "overlap" in meaning
    assert "does not assert claim sufficiency" in meaning
    assert claim["claim_outcome"] == CLAIM_OUTCOME_INSUFFICIENT
    assert claim["coverage_status"] == COVERAGE_PARTIAL
    assert claim["claim_outcome"] != coverage["coverage_status"]


def test_evidence_panel_has_both_source_excerpts_and_locators() -> None:
    sealed = rebuild_pre_adjudication_chain(root=ROOT)
    panel = sealed["evidence_panel"]
    assert panel["overlap_count"] >= 1
    row = panel["overlap_panels"][0]
    f1 = row["family_one"]
    f2 = row["family_two"]
    assert f1["exact_excerpt"]
    assert f1["document_locator"]
    assert f1["official_locator"]
    assert isinstance(f1["byte_start"], int)
    assert f2["exact_excerpt"]
    assert f2["document_locator"]
    assert f2["byte_start"] < f2["byte_end"]
    assert sealed["pre_adjudication_seal"]["functional_stage"] == (
        FUNCTIONAL_STAGE_PRE_ADJUDICATION
    )


def test_adjudication_requires_operator_confirmation() -> None:
    sealed = rebuild_pre_adjudication_chain(root=ROOT)
    confirm = build_operator_confirmation(
        case_manifest=sealed["case_manifest"],
        coverage=sealed["coverage"],
        case_claim=sealed["case_claim"],
        pre_adjudication_seal=sealed["pre_adjudication_seal"],
        adjudicator_label="SELF_LABELLED_OPERATOR",
        confirmed_at="2026-07-23T12:00:00.000000Z",
    )
    adj = capture_case_workspace_adjudication(
        case_manifest=sealed["case_manifest"],
        coverage=sealed["coverage"],
        case_claim=sealed["case_claim"],
        operator_confirmation=confirm,
    )
    assert adj["trusted_identity"] is False
    assert adj["discretionary_decision"] is False
    assert adj["adjudicator_identity_claim"] == "SELF_LABELLED_ONLY"
    assert adj["selected_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert adj["research_stance"] == RESEARCH_ACTION_HOLD
    assert adj["operator_confirmation_hash"] == confirm["operator_confirmation_hash"]


def test_position_action_forbidden() -> None:
    sealed = rebuild_pre_adjudication_chain(root=ROOT)
    with pytest.raises(GvAlpha0CloseError, match="ACTION_NOT_PERMITTED|POSITION_FORBIDDEN|PHRASE"):
        build_operator_confirmation(
            case_manifest=sealed["case_manifest"],
            coverage=sealed["coverage"],
            case_claim=sealed["case_claim"],
            pre_adjudication_seal=sealed["pre_adjudication_seal"],
            adjudicator_label="SELF_LABELLED_OPERATOR",
            confirmed_at="2026-07-23T12:00:00.000000Z",
            selected_action="OPEN",
        )


def test_seal_then_confirm_path(tmp_path: Path) -> None:
    case = tmp_path / "case"
    sealed = seal_pre_adjudication_case(root=ROOT, case_dir=case)
    assert sealed["functional_stage"] == FUNCTIONAL_STAGE_PRE_ADJUDICATION
    assert (case / "pre_adjudication_seal.json").is_file()
    assert (case / "evidence_panel.json").is_file()
    assert not (case / "result.json").is_file()
    assert not (case / "operator_confirmation.json").is_file()

    out = confirm_operator_and_certify(
        root=ROOT,
        case_dir=case,
        adjudicator_label="SELF_LABELLED_OPERATOR",
        confirmed_at="2026-07-23T12:00:00.000000Z",
        confirmation_phrase=OPERATOR_CONFIRMATION_PHRASE,
        capture_surface=CAPTURE_SURFACE_UI,
    )
    assert out["certification_status"] == "CERTIFIED"
    # UI surface earns OPERABLE; offline bank tooling does not.
    assert out["functional_stage"] == FUNCTIONAL_STAGE_OPERABLE
    assert (case / "operator_confirmation.json").is_file()
    assert (case / "result.json").is_file()
    assert (case / "certified_decision_result.json").is_file()
    confirm = json.loads((case / "operator_confirmation.json").read_text(encoding="utf-8"))
    assert confirm["confirmed"] is True
    assert confirm["confirmation_phrase"] == OPERATOR_CONFIRMATION_PHRASE
    assert confirm["capture_surface"] == CAPTURE_SURFACE_UI
    certified = json.loads(
        (case / "certified_decision_result.json").read_text(encoding="utf-8")
    )
    result = json.loads((case / "result.json").read_text(encoding="utf-8"))
    assert certified["role"] == "NO_POSITION"
    assert certified["certified_decision_result_hash"] == (
        result["certified_decision_result_hash"]
    )
    from core.gv_fs0_current_decision import certified_decision_result_bytes

    # Same role-bearing object publish_current_decision requires.
    certified_decision_result_bytes(certified)


def test_product_bank_sealed_or_operable() -> None:
    """Product bank is either sealed-only (pre-dogfood) or UI-OPERABLE (post RC2)."""

    case = CASE_DIR
    assert (case / "pre_adjudication_seal.json").is_file()
    assert (case / "evidence_panel.json").is_file()
    model = load_banked_case_workspace(
        root=ROOT, case_dir=case, verify=True, allow_pre_adjudication=True
    )
    assert model["seal_verified_on_load"] is True
    assert model["overlap_panels"]
    if (case / "result.json").exists():
        # Post Commit B / dogfood: OPERABLE bank with full certified custody.
        assert (case / "operator_confirmation.json").is_file()
        assert (case / "certified_decision_result.json").is_file()
        assert (case / "export_bundle.json").is_file()
        assert model["functional_stage"] == FUNCTIONAL_STAGE_OPERABLE
        assert model["awaiting_operator_confirmation"] is False
        confirm = json.loads(
            (case / "operator_confirmation.json").read_text(encoding="utf-8")
        )
        assert confirm.get("capture_surface") == CAPTURE_SURFACE_UI
        result = json.loads((case / "result.json").read_text(encoding="utf-8"))
        assert result["shipped_product_score"] == SHIPPED_PRODUCT_SCORE
        assert result["observed_comparison_count"] == OBSERVED_COMPARISON_COUNT
        assert result["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    else:
        # Pre-dogfood sealed-only candidate.
        assert not (case / "operator_confirmation.json").exists()
        assert not (case / "adjudication.json").exists()
        assert not (case / "certified_decision_result.json").exists()
        assert model["functional_stage"] == FUNCTIONAL_STAGE_PRE_ADJUDICATION
        assert model["awaiting_operator_confirmation"] is True


def test_close_vertical_certified_no_position_no_publish(tmp_path: Path) -> None:
    out = run_v2_alpha0_case_close(
        root=ROOT,
        case_dir=tmp_path / "case",
        publish=False,
    )
    assert out["slice_classification"] == SLICE_CLASSIFICATION
    assert out["decision_id"] == DECISION_ID
    assert out["coverage_status"] == COVERAGE_PARTIAL
    assert out["claim_outcome"] == CLAIM_OUTCOME_INSUFFICIENT
    assert out["research_action"] == RESEARCH_ACTION_HOLD
    assert out["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert out["certification_status"] == "CERTIFIED"
    assert out["shipped_product_score"] == SHIPPED_PRODUCT_SCORE
    assert out["observed_comparison_count"] == OBSERVED_COMPARISON_COUNT
    # Offline bank tool path is BANKED, never OPERABLE.
    assert out["functional_stage"] == FUNCTIONAL_STAGE_BANKED
    assert out["publication_authorized"] is False
    assert out["published"] is False

    case = tmp_path / "case"
    for name in (
        "case_manifest.json",
        "coverage.json",
        "case_claim.json",
        "evidence_panel.json",
        "pre_adjudication_seal.json",
        "operator_confirmation.json",
        "adjudication.json",
        "research_decision.json",
        "certified_decision_result.json",
        "export_bundle.json",
        "decision_packet.md",
        "case_workspace_view.json",
        "result.json",
    ):
        assert (case / name).is_file(), name
    assert not (case / ".alpha0_close_tx").exists()

    result = json.loads((case / "result.json").read_text(encoding="utf-8"))
    assert result["portfolio_action_invariant"] is True
    assert result["coverage_status"] == COVERAGE_PARTIAL
    assert result["claim_outcome"] == CLAIM_OUTCOME_INSUFFICIENT
    certified = json.loads(
        (case / "certified_decision_result.json").read_text(encoding="utf-8")
    )
    assert certified["role"] == "NO_POSITION"
    assert certified["certified_decision_result_hash"] == (
        result["certified_decision_result_hash"]
    )
    export = json.loads((case / "export_bundle.json").read_text(encoding="utf-8"))
    assert "certified_decision_result" in export["artifacts"]
    assert export["artifacts"]["certified_decision_result"][
        "certified_decision_result_hash"
    ] == result["certified_decision_result_hash"]


def test_publish_blocked_until_authorized() -> None:
    with pytest.raises(GvAlpha0CloseError, match="PUBLICATION_NOT_YET_AUTHORIZED"):
        run_v2_alpha0_case_close(root=ROOT, case_dir=Path("unused"), publish=True)


def test_rebuild_and_verify_banked_exact(tmp_path: Path) -> None:
    run_v2_alpha0_case_close(root=ROOT, case_dir=tmp_path / "case", publish=False)
    rebuilt = verify_close_chain(root=ROOT, case_dir=tmp_path / "case")
    assert rebuilt["result"]["result_hash"]
    assert rebuilt["export"]["export_hash"]
    assert rebuilt["operator_confirmation"]["confirmed"] is True


def test_adversarial_claim_flip_fails_verify(tmp_path: Path) -> None:
    case = tmp_path / "case"
    run_v2_alpha0_case_close(root=ROOT, case_dir=case, publish=False)
    claim_path = case / "case_claim.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim["claim_outcome"] = "SUFFICIENT_FOR_RESEARCH_TRIAGE"
    # rehash to look self-consistent but non-canonical
    from core.gv_fs0_canonical import domain_hash
    from core.gv_v2_alpha0_case_close import CLAIM_DOMAIN

    body = {k: v for k, v in claim.items() if k != "case_claim_hash"}
    claim = body
    claim["case_claim_hash"] = domain_hash(CLAIM_DOMAIN, claim)
    claim_path.write_text(
        json.dumps(claim, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(GvAlpha0CloseError, match="NOT_CANONICAL|CLAIM"):
        verify_close_chain(root=ROOT, case_dir=case)


def test_export_replay_matches(tmp_path: Path) -> None:
    case = tmp_path / "case"
    run_v2_alpha0_case_close(root=ROOT, case_dir=case, publish=False)
    export = json.loads((case / "export_bundle.json").read_text(encoding="utf-8"))
    replayed = replay_export_bundle(export, root=ROOT)
    assert replayed["result"]["result_hash"] == export["artifacts"]["result"]["result_hash"]
    assert replayed["export"]["export_hash"] == export["export_hash"]
    assert (
        replayed["certified"]["certified_decision_result_hash"]
        == export["artifacts"]["certified_decision_result"][
            "certified_decision_result_hash"
        ]
    )


def test_certified_object_is_publish_current_ready(tmp_path: Path) -> None:
    """RC1.1: full role-bearing object, not hash-only custody."""

    from core.gv_fs0_current_decision import certified_decision_result_bytes
    from core.gv_fs0_publish import publish_current_decision

    case = tmp_path / "case"
    run_v2_alpha0_case_close(root=ROOT, case_dir=case, publish=False)
    certified = json.loads(
        (case / "certified_decision_result.json").read_text(encoding="utf-8")
    )
    target = tmp_path / "gv_fs0_current_decision.json"
    lock = tmp_path / "gv_fs0_current_decision.lock"
    raw = certified_decision_result_bytes(certified)
    assert raw
    pub = publish_current_decision(certified, target=target, lock_path=lock)
    assert pub.certified_decision_result_hash == certified[
        "certified_decision_result_hash"
    ]
    assert target.is_file()


def test_case_workspace_view_model_fields(tmp_path: Path) -> None:
    case = tmp_path / "case"
    out = run_v2_alpha0_case_close(root=ROOT, case_dir=case, publish=False)
    view = out["view"]
    assert view["page"] == "CASE_WORKSPACE"
    assert view["coverage_status"] == COVERAGE_PARTIAL
    assert view["claim_outcome"] == CLAIM_OUTCOME_INSUFFICIENT
    assert view["portfolio_action_invariant"] == PORTFOLIO_ACTION_NO_POSITION
    assert view["adjudication_kind"] == "CASE_WORKSPACE_ADJUDICATION"
    assert view["operator_confirmation_present"] is True
    assert view["overlap_panels"]
    assert view["functional_stage"] == FUNCTIONAL_STAGE_BANKED
    loaded = load_banked_case_workspace(
        root=ROOT, case_dir=case, verify=True
    )
    assert loaded["case_id"] == CASE_ID
    assert loaded["functional_stage"] == FUNCTIONAL_STAGE_BANKED
    assert loaded["seal_verified_on_load"] is True


def test_load_refuses_missing_bank(tmp_path: Path) -> None:
    with pytest.raises(GvAlpha0CloseError, match="CASE_BANK_MISSING|MANIFEST_MISSING|SEAL"):
        load_banked_case_workspace(
            root=ROOT, case_dir=tmp_path / "empty", verify=False
        )


def test_two_run_determinism(tmp_path: Path) -> None:
    a = rebuild_canonical_close_chain(root=ROOT)
    b = rebuild_canonical_close_chain(root=ROOT)
    assert a["case_manifest"]["case_manifest_hash"] == b["case_manifest"]["case_manifest_hash"]
    assert a["result"]["result_hash"] == b["result"]["result_hash"]
    assert a["export"]["export_hash"] == b["export"]["export_hash"]
    assert a["operator_confirmation"]["operator_confirmation_hash"] == (
        b["operator_confirmation"]["operator_confirmation_hash"]
    )
