from __future__ import annotations

import base64
from copy import deepcopy
import json
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash, sha256_bytes
from gv_portfolio_v0.replay import (
    AUDIT_RECEIPT_SCHEMA,
    EXTERNAL_REVIEW_RECEIPT_SCHEMA,
    REPLAY_DOMAIN,
    REVIEW_REPORT_SCHEMA,
    ReplayV0Error,
    build_event_correction,
    build_replay_evidence,
    event_with_updates,
    normalize_event_stream,
    replay_workspace,
)
from gv_portfolio_v0.storage import (
    admit_later_watch_observation,
    confirm_and_certify,
    load_workspace,
)
from gv_portfolio_v0.vertical import (
    ID_DOMAIN,
    admit_watch_observation,
    build_draft_workspace,
    confirm_draft_workspace,
)
import validation.gv_portfolio_v0_replay as replay_cli
from validation.gv_portfolio_v0_replay import run, verify_github_provider_receipt


def _observed_workspace() -> dict[str, object]:
    return admit_watch_observation(confirm_draft_workspace(build_draft_workspace()))


def _record_with_id(
    kind: str, id_key: str, payload: dict[str, object]
) -> dict[str, object]:
    return {
        id_key: f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", payload),
        **payload,
    }


def _partial_fill_correction(
    workspace: dict[str, object], *, quantity: str, fee: str = "1"
) -> dict[str, object]:
    fill_event = next(
        event for event in workspace["events"] if event["event_type"] == "FILL_COMPLETED"
    )
    source_fill = fill_event["payload"]["fill"]
    fill_payload = {
        key: deepcopy(value)
        for key, value in source_fill.items()
        if key != "fill_id"
    }
    fill_payload["quantity"] = quantity
    fill_payload["fee"] = fee
    replacement_fill = _record_with_id("FIL", "fill_id", fill_payload)
    replacement_event = event_with_updates(
        fill_event,
        payload_updates={"fill": replacement_fill},
        source_identity=replacement_fill["fill_id"],
    )
    return build_event_correction(
        target_event=fill_event,
        replacement_event=replacement_event,
        reason="Exercise deterministic partial-fill replay residual.",
        recorded_at="2026-07-22T00:00:00.000000Z",
    )


def _synthetic_audit_receipt(
    subject_event_ledger_hash: str,
) -> tuple[dict[str, object], str, str, str]:
    candidate_commit = "a" * 40
    candidate_tree = "b" * 40
    implementer_login = "slice0-implementer"
    locked_environment = {
        "python": "3.12.10",
        "pytest": "9.0.2",
        "streamlit": "1.54.0",
        "jsonschema": "4.26.0",
    }
    review_package_hash = domain_hash(
        f"{REPLAY_DOMAIN}:SLICE0_AUDIT_PACKAGE:V2",
        {
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "subject_event_ledger_hash": subject_event_ledger_hash,
            "locked_environment": locked_environment,
        },
    )
    reviewers: list[dict[str, object]] = []
    for index, domain in enumerate(("A", "B", "C"), start=1):
        login = f"slice0-reviewer-{domain.lower()}"
        report = {
            "schema_version": REVIEW_REPORT_SCHEMA,
            "domain": domain,
            "verdict": "PASS",
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "subject_event_ledger_hash": subject_event_ledger_hash,
            "checks": {"exact_candidate_reproduced": True},
            "findings": [],
            "reviewer_summary": f"Synthetic fixture review {domain} passed.",
        }
        body = {
            "schema_version": EXTERNAL_REVIEW_RECEIPT_SCHEMA,
            "domain": domain,
            "verdict": "PASS",
            "provider": "GITHUB",
            "repository": "example/quant",
            "authenticated_submitter_id": login,
            "github_author_login": login,
            "github_committer_login": login,
            "submission_commit_sha": str(index) * 40,
            "report_path": f"reviews/slice0-review-{domain.lower()}.json",
            "report_sha256": sha256_bytes(canonical_document_bytes(report)),
            "report": report,
            "receipt_url": f"https://github.com/example/quant/commit/{str(index) * 40}",
            "submitted_at": f"2026-07-2{index}T12:00:00.000000Z",
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "review_package_hash": review_package_hash,
            "claim_boundary": {
                "provider_authenticated_account_separation_required": True,
                "natural_personhood_proven": False,
                "operational_separation_only": True,
            },
        }
        reviewers.append(
            {
                **body,
                "receipt_hash": domain_hash(
                    f"{REPLAY_DOMAIN}:EXTERNAL_REVIEW_RECEIPT:V2", body
                ),
            }
        )
    body = {
        "schema_version": AUDIT_RECEIPT_SCHEMA,
        "verdict": "PASS",
        "independent": True,
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "subject_event_ledger_hash": subject_event_ledger_hash,
        "locked_environment": locked_environment,
        "implementer_github_login": implementer_login,
        "review_package_hash": review_package_hash,
        "reviewers": reviewers,
        "claim_boundary": {
            "provider_account_separation_proven": True,
            "natural_personhood_proven": False,
            "terminal_acceptance_requires_exact_git_and_report_bytes": True,
        },
    }
    return (
        {
            **body,
            "audit_receipt_hash": domain_hash(
                f"{REPLAY_DOMAIN}:AUDIT_RECEIPT:V2", body
            ),
        },
        candidate_commit,
        candidate_tree,
        implementer_login,
    )


def test_shadow_replay_reconstructs_exact_slice0_state_and_prior_certifications() -> None:
    workspace = _observed_workspace()
    evidence = build_replay_evidence(workspace)

    assert all(evidence["checks"].values())
    assert evidence["terminal_book_hash"] == workspace["book"]["book_hash"]
    assert evidence["product_certification_ids"] == [
        workspace["certification_history"][0]["certification_id"],
        workspace["certification"]["certification_id"],
    ]
    assert evidence["audit_gate"] == {
        "status": "BLOCKED",
        "reason": "SLICE0_AUDIT_PASS_REQUIRED",
        "audit_receipt_hash": None,
    }
    assert evidence["replay_certification"] is None


def test_replay_is_byte_idempotent_under_exact_duplicate_delivery() -> None:
    workspace = _observed_workspace()
    baseline = replay_workspace(workspace)
    duplicate_delivery = deepcopy(workspace)
    duplicate_delivery["events"].append(deepcopy(workspace["events"][2]))

    replayed = replay_workspace(duplicate_delivery)

    assert canonical_document_bytes(replayed) == canonical_document_bytes(baseline)
    normalized, _ = normalize_event_stream(duplicate_delivery["events"])
    assert len(normalized) == len(workspace["events"])


def test_partial_fill_reconstructs_residual_quantity_without_mutating_source() -> None:
    workspace = confirm_draft_workspace(build_draft_workspace())
    original_bytes = canonical_document_bytes(workspace)
    correction = _partial_fill_correction(workspace, quantity="2")

    replayed = replay_workspace(workspace, corrections=[correction])
    order = replayed["execution"]["orders"][0]
    harbor = next(
        row
        for row in replayed["book"]["positions"]
        if row["instrument_id"] == order["instrument_id"]
    )

    assert order["status"] == "PARTIAL"
    assert order["filled_quantity"] == "2"
    assert order["remaining_quantity"] == "3"
    assert order["cash_cost"] == "81"
    assert harbor["quantity"] == "2"
    assert replayed["book"]["classified_cash"] == [
        {"bucket": "AVAILABLE", "amount": "894"},
        {"bucket": "RESEARCH_RESERVE", "amount": "25"},
    ]
    assert replayed["book"]["nav"] == "1499"
    assert replayed["correction_lineage"][0]["target_event_id"] == next(
        event["event_id"]
        for event in workspace["events"]
        if event["event_type"] == "FILL_COMPLETED"
    )
    assert canonical_document_bytes(workspace) == original_bytes


def test_correction_lineage_changes_costs_explicitly_and_preserves_zero_split_residual() -> None:
    workspace = confirm_draft_workspace(build_draft_workspace())
    correction = _partial_fill_correction(workspace, quantity="3", fee="2")

    replayed = replay_workspace(workspace, corrections=[correction])

    assert replayed["execution"]["orders"][0]["remaining_quantity"] == "2"
    assert replayed["execution"]["cash_cost"] == "122"
    assert replayed["book"]["nav"] == "1498"
    assert replayed["book"]["split_value_residual"] == "0"
    assert replayed["product_certification_chain"] == []


def test_multiple_corrections_for_one_target_fail_closed() -> None:
    workspace = confirm_draft_workspace(build_draft_workspace())
    first = _partial_fill_correction(workspace, quantity="2")
    second = _partial_fill_correction(workspace, quantity="3")

    with pytest.raises(
        ReplayV0Error, match="MULTIPLE_CORRECTIONS_PER_TARGET_PROHIBITED"
    ):
        replay_workspace(workspace, corrections=[first, second])


def test_overfill_fixture_fails_closed() -> None:
    workspace = confirm_draft_workspace(build_draft_workspace())
    correction = _partial_fill_correction(workspace, quantity="6")

    with pytest.raises(ReplayV0Error, match="ORDER_OVERFILLED"):
        replay_workspace(workspace, corrections=[correction])


def test_valuation_pending_replay_never_invents_price_or_nav() -> None:
    workspace = build_draft_workspace()
    opening = next(
        event
        for event in workspace["events"]
        if event["event_type"] == "POSITION_OPENING"
    )
    pending_event = event_with_updates(
        opening,
        sequence=0,
        payload_updates={"valuation_price": None},
    )
    fixture = deepcopy(workspace)
    fixture["events"] = [pending_event]
    fixture["certification"] = None
    fixture["certification_history"] = []

    replayed = replay_workspace(fixture)

    assert replayed["book"]["valuation_status"] == "VALUATION_PENDING"
    assert replayed["book"]["positions"][0]["valuation_price"] is None
    assert replayed["book"]["positions"][0]["market_value"] is None
    assert replayed["book"]["nav"] is None
    assert replayed["book"]["position_value"] is None
    assert replayed["execution"]["order_count"] == 0


def test_synthetic_valid_audit_receipt_cannot_self_authorize_replay() -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )

    evidence = build_replay_evidence(
        workspace,
        audit_receipt=receipt,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )

    assert evidence["audit_gate"]["status"] == "BLOCKED"
    assert evidence["audit_gate"]["reason"] == "EXTERNAL_PROVIDER_VERIFICATION_REQUIRED"
    assert evidence["audit_gate"]["reviewer_github_logins"] == [
        "slice0-reviewer-a",
        "slice0-reviewer-b",
        "slice0-reviewer-c",
    ]
    assert evidence["audit_gate"]["audit_receipt_hash"] is not None
    assert evidence["replay_certification"] is None


def test_provider_preflight_cannot_authorize_core_replay() -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    verified_domains: list[str] = []
    for reviewer in receipt["reviewers"]:
        assert reviewer["repository"] == "example/quant"
        assert str(reviewer["receipt_url"]).startswith(
            "https://github.com/example/quant/commit/"
        )
        verified_domains.append(str(reviewer["domain"]))

    evidence = build_replay_evidence(
        workspace,
        audit_receipt=receipt,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )

    assert verified_domains == ["A", "B", "C"]
    assert evidence["audit_gate"]["status"] == "BLOCKED"
    assert evidence["audit_gate"]["reason"] == "EXTERNAL_PROVIDER_VERIFICATION_REQUIRED"
    assert evidence["replay_certification"] is None


def test_github_provider_verifier_binds_commit_identity_and_report_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, _commit, _tree, _implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    reviewer = receipt["reviewers"][0]

    def _provider_json(url: str) -> dict[str, object]:
        if url.endswith(f"/{reviewer['candidate_commit']}"):
            return {
                "sha": reviewer["candidate_commit"],
                "commit": {"tree": {"sha": reviewer["candidate_tree"]}},
            }
        if "/commits/" in url:
            return {
                "sha": reviewer["submission_commit_sha"],
                "author": {"login": reviewer["github_author_login"]},
                "committer": {"login": reviewer["github_committer_login"]},
                "html_url": reviewer["receipt_url"],
            }
        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(
                canonical_document_bytes(reviewer["report"])
            ).decode("ascii"),
        }

    monkeypatch.setattr(replay_cli, "_github_api_json", _provider_json)
    verify_github_provider_receipt(reviewer)


def test_provider_verification_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, _commit, _tree, _implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    reviewer = receipt["reviewers"][0]

    def _provider_json(_url: str) -> dict[str, object]:
        return {
            "sha": reviewer["submission_commit_sha"],
            "author": {"login": "wrong-reviewer"},
            "committer": {"login": reviewer["github_committer_login"]},
            "html_url": reviewer["receipt_url"],
        }

    monkeypatch.setattr(replay_cli, "_github_api_json", _provider_json)
    with pytest.raises(ReplayV0Error, match="GITHUB_PROVIDER_AUTHOR_LOGIN_MISMATCH"):
        verify_github_provider_receipt(reviewer)


def test_github_provider_verifier_rejects_candidate_tree_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, _commit, _tree, _implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    reviewer = receipt["reviewers"][0]

    def _provider_json(url: str) -> dict[str, object]:
        if url.endswith(f"/{reviewer['candidate_commit']}"):
            return {
                "sha": reviewer["candidate_commit"],
                "commit": {"tree": {"sha": "f" * 40}},
            }
        if "/commits/" in url:
            return {
                "sha": reviewer["submission_commit_sha"],
                "author": {"login": reviewer["github_author_login"]},
                "committer": {"login": reviewer["github_committer_login"]},
                "html_url": reviewer["receipt_url"],
            }
        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(
                canonical_document_bytes(reviewer["report"])
            ).decode("ascii"),
        }

    monkeypatch.setattr(replay_cli, "_github_api_json", _provider_json)
    with pytest.raises(ReplayV0Error, match="GITHUB_PROVIDER_CANDIDATE_TREE_MISMATCH"):
        verify_github_provider_receipt(reviewer)


def test_git_identity_rejects_dirty_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        replay_cli,
        "_run_git",
        lambda *arguments: "?? audit-receipt.json" if arguments[0] == "status" else "",
    )
    with pytest.raises(ReplayV0Error, match="CANDIDATE_CHECKOUT_NOT_CLEAN"):
        replay_cli._git_identity()


def test_github_origin_and_receipt_repository_must_match() -> None:
    assert (
        replay_cli._github_repository_from_remote(
            "https://github.com/example/quant.git"
        )
        == "example/quant"
    )
    assert (
        replay_cli._github_repository_from_remote("git@github.com:example/quant.git")
        == "example/quant"
    )
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, _commit, _tree, _implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    replay_cli._verify_receipt_repository_against_origin(
        receipt, origin_repository="example/quant"
    )
    with pytest.raises(ReplayV0Error, match="AUDIT_RECEIPT_REPOSITORY_NOT_ORIGIN"):
        replay_cli._verify_receipt_repository_against_origin(
            receipt, origin_repository="other/quant"
        )


def test_cli_provider_boundary_promotes_shadow_to_terminal_certification() -> None:
    workspace = _observed_workspace()
    initial_shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        initial_shadow["source_event_ledger_hash"]
    )
    receipt_bound_shadow = build_replay_evidence(
        workspace,
        audit_receipt=receipt,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )
    provider_verification = replay_cli._build_provider_verification_record(
        receipt,
        candidate_commit=commit,
        candidate_tree=tree,
    )

    certified = replay_cli._promote_verified_replay_evidence(
        receipt_bound_shadow,
        provider_verification=provider_verification,
    )
    certified_again = replay_cli._promote_verified_replay_evidence(
        receipt_bound_shadow,
        provider_verification=provider_verification,
    )

    assert canonical_document_bytes(certified) == canonical_document_bytes(
        certified_again
    )
    assert certified["schema_version"] == replay_cli.CERTIFIED_EVIDENCE_SCHEMA
    assert certified["audit_gate"]["status"] == "PASS"
    assert certified["replay_certification"]["certification_id"].startswith("CRT_")
    assert certified["replay_certification"]["candidate_commit"] == commit
    assert certified["replay_certification"]["candidate_tree"] == tree
    assert certified["replay_certification"]["source_shadow_evidence_hash"] == (
        receipt_bound_shadow["evidence_hash"]
    )
    assert certified["provider_verification"] == provider_verification


def test_cli_provider_promotion_rejects_tampered_verification_hash() -> None:
    workspace = _observed_workspace()
    initial_shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        initial_shadow["source_event_ledger_hash"]
    )
    receipt_bound_shadow = build_replay_evidence(
        workspace,
        audit_receipt=receipt,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )
    provider_verification = replay_cli._build_provider_verification_record(
        receipt,
        candidate_commit=commit,
        candidate_tree=tree,
    )
    provider_verification["candidate_tree"] = "f" * 40

    with pytest.raises(ReplayV0Error, match="PROVIDER_VERIFICATION_HASH_MISMATCH"):
        replay_cli._promote_verified_replay_evidence(
            receipt_bound_shadow,
            provider_verification=provider_verification,
        )


def test_legacy_self_asserted_audit_receipt_cannot_certify() -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    legacy = {
        "schema_version": "gv_portfolio_v0_slice0_audit_receipt_v1",
        "verdict": "PASS",
        "independent": True,
        "candidate_commit": "a" * 40,
        "subject_event_ledger_hash": shadow["source_event_ledger_hash"],
        "reviewers": {"A": "PASS", "B": "PASS", "C": "PASS"},
        "locked_environment": {
            "python": "3.12",
            "pytest": "9.0.2",
            "streamlit": "1.54.0",
        },
    }

    evidence = build_replay_evidence(
        workspace,
        audit_receipt=legacy,
        expected_candidate_commit="a" * 40,
        expected_candidate_tree="b" * 40,
        expected_implementer_github_login="slice0-implementer",
    )

    assert evidence["audit_gate"]["status"] == "BLOCKED"
    assert "AUDIT_RECEIPT_FIELDS_INVALID" in evidence["audit_gate"]["reason"]
    assert evidence["replay_certification"] is None


def test_audit_receipt_subject_mismatch_keeps_certification_blocked() -> None:
    workspace = _observed_workspace()
    receipt, commit, tree, implementer = _synthetic_audit_receipt("0" * 64)

    evidence = build_replay_evidence(
        workspace,
        audit_receipt=receipt,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )

    assert evidence["audit_gate"]["status"] == "BLOCKED"
    assert "AUDIT_RECEIPT_SUBJECT_MISMATCH" in evidence["audit_gate"]["reason"]
    assert evidence["replay_certification"] is None


def test_audit_receipt_rejects_reviewer_account_reuse() -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    duplicated = deepcopy(receipt)
    reviewer_a = duplicated["reviewers"][0]["authenticated_submitter_id"]
    duplicated["reviewers"][1]["authenticated_submitter_id"] = reviewer_a
    duplicated["reviewers"][1]["github_author_login"] = reviewer_a

    evidence = build_replay_evidence(
        workspace,
        audit_receipt=duplicated,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )

    assert evidence["audit_gate"]["status"] == "BLOCKED"
    assert "EXTERNAL_REVIEW_RECEIPT_HASH_MISMATCH" in evidence["audit_gate"]["reason"]
    assert evidence["replay_certification"] is None


def test_audit_receipt_rejects_report_byte_mismatch() -> None:
    workspace = _observed_workspace()
    shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        shadow["source_event_ledger_hash"]
    )
    tampered = deepcopy(receipt)
    tampered["reviewers"][2]["report"]["reviewer_summary"] = "Changed after receipt."

    evidence = build_replay_evidence(
        workspace,
        audit_receipt=tampered,
        expected_candidate_commit=commit,
        expected_candidate_tree=tree,
        expected_implementer_github_login=implementer,
    )

    assert evidence["audit_gate"]["status"] == "BLOCKED"
    assert "EXTERNAL_REVIEW_REPORT_BYTE_MISMATCH" in evidence["audit_gate"]["reason"]
    assert evidence["replay_certification"] is None


def test_cli_main_promotes_only_after_provider_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    confirm_and_certify(root=workspace_root)
    admit_later_watch_observation(root=workspace_root)
    workspace = load_workspace(root=workspace_root)
    initial_shadow = build_replay_evidence(workspace)
    receipt, commit, tree, implementer = _synthetic_audit_receipt(
        initial_shadow["source_event_ledger_hash"]
    )
    receipt_path = tmp_path / "audit-receipt.json"
    receipt_path.write_bytes(canonical_document_bytes(receipt))
    output = tmp_path / "certified-evidence.json"
    verified_domains: list[str] = []

    monkeypatch.setattr(replay_cli, "_git_identity", lambda: (commit, tree))
    monkeypatch.setattr(
        replay_cli, "_github_origin_repository", lambda: "example/quant"
    )
    monkeypatch.setattr(
        replay_cli,
        "verify_github_provider_receipt",
        lambda reviewer: verified_domains.append(str(reviewer["domain"])),
    )

    assert (
        replay_cli.main(
            [
                "--workspace-root",
                str(workspace_root),
                "--audit-receipt",
                str(receipt_path),
                "--output",
                str(output),
                "--implementer-github-login",
                implementer,
                "--require-certification",
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert verified_domains == ["A", "B", "C"]
    assert payload["audit_gate"]["status"] == "PASS"
    assert payload["replay_certification"] is not None
    assert payload["replay_certification"]["candidate_commit"] == commit
    assert payload["replay_certification"]["candidate_tree"] == tree


def test_cli_writes_byte_stable_shadow_evidence_and_require_gate_returns_two(
    tmp_path: Path,
) -> None:
    root_a = tmp_path / "workspace-a"
    root_b = tmp_path / "workspace-b"
    confirm_and_certify(root=root_a)
    confirm_and_certify(root=root_b)
    admit_later_watch_observation(root=root_a)
    admit_later_watch_observation(root=root_b)
    output_a = tmp_path / "evidence-a.json"
    output_b = tmp_path / "evidence-b.json"

    assert (
        run(
            workspace_root=root_a,
            output=output_a,
            audit_receipt=None,
            require_certification=False,
        )
        == 0
    )
    assert (
        run(
            workspace_root=root_b,
            output=output_b,
            audit_receipt=None,
            require_certification=True,
        )
        == 2
    )
    assert output_a.read_bytes() == output_b.read_bytes()
    payload = json.loads(output_a.read_text(encoding="utf-8"))
    assert payload["audit_gate"]["status"] == "BLOCKED"
    assert payload["replay_certification"] is None
