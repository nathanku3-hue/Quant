from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import subprocess
import sys

import pytest

import core.gv_one_case_delta as delta
from core.gv_fs0_canonical import canonical_document_bytes, sha256_bytes
import scripts.gv_one_case_delta_capture as cli


_HOSTED_PROOF_KEY = "ssh-ed25519 AAAATESTHOSTEDPROOFKEY"
_IDENTITY_ISSUER_KEY = "ssh-ed25519 AAAATESTIDENTITYISSUERKEY"
_OPERATOR_KEY = "ssh-ed25519 AAAATESTOPERATORKEY"


def _successful_runner(*args, **kwargs) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(args=args, returncode=0, stdout=b"", stderr=b"")


def _hosted_proof(*, windows: str = "SUCCESS", candidate_sha: str = "a" * 40) -> dict:
    return {
        "schema_version": delta.SCHEMA_HOSTED_PROOF,
        "adapter": delta.IDENTITY_ADAPTER,
        "proof_provider": "trusted-hosted-proof-issuer",
        "provider_public_key": _HOSTED_PROOF_KEY,
        "payload": {
            "proof_id": "hosted-proof-1",
            "candidate_sha": candidate_sha,
            "candidate_tree": "b" * 40,
            "workflow_name": "GV-FS0 Product",
            "windows_run_id": "win-1",
            "windows_conclusion": windows,
            "linux_run_id": "linux-1",
            "linux_conclusion": "SUCCESS",
            "verified_at": "2026-07-28T00:00:00.000000Z",
        },
        "signature": "test-signature",
    }


def _manifest() -> dict:
    return delta.create_session_manifest(
        candidate_sha="a" * 40,
        candidate_tree="b" * 40,
        experiment_binding_hash="c" * 64,
        evidence_bundle_hash="3" * 64,
        projection_hash="4" * 64,
        projection_manifest_hash="5" * 64,
        projection_schema_hash=delta.PROJECTION_SCHEMA_HASH,
        operator_instruction_hash="e" * 64,
        reviewer_instruction_hash="f" * 64,
        hosted_proof_identity=_hosted_proof(),
        trusted_proof_issuers={"trusted-hosted-proof-issuer": _HOSTED_PROOF_KEY},
        session_nonce="1" * 64,
        runner=_successful_runner,
    )


def _fake_operator_identity(manifest: dict) -> dict:
    fingerprint = delta._public_key_fingerprint(_OPERATOR_KEY)
    evidence_id = "identity-operator-principal"
    signed_at = "2026-07-28T00:30:00.000000Z"
    issuer_claim = {
        "identity_evidence_id": evidence_id,
        "signed_at": signed_at,
        "verified_human_subject_commitment": "operator-subject-commitment-00000000000000000001",
        "principal_id": "operator-principal",
        "credential_fingerprint": fingerprint,
        "identity_verification_level": delta.IDENTITY_VERIFICATION_LEVEL,
        "identity_evidence_issuer": "trusted-human-issuer",
    }
    challenge = {
        "identity_evidence_id": evidence_id,
        "role": delta.ROLE_OPERATOR,
        "principal_id": "operator-principal",
        "verified_human_subject_commitment": issuer_claim["verified_human_subject_commitment"],
        "credential_fingerprint": fingerprint,
        "session_nonce": manifest["session_nonce"],
        "session_manifest_hash": manifest["session_manifest_hash"],
    }
    return {
        "schema_version": delta.SCHEMA_IDENTITY,
        "adapter": delta.IDENTITY_ADAPTER,
        "identity_evidence_id": evidence_id,
        "signed_at": signed_at,
        "role": delta.ROLE_OPERATOR,
        "principal_id": "operator-principal",
        "verified_human_subject_commitment": issuer_claim["verified_human_subject_commitment"],
        "credential_public_key": _OPERATOR_KEY,
        "credential_fingerprint": fingerprint,
        "identity_evidence_issuer": "trusted-human-issuer",
        "issuer_public_key": _IDENTITY_ISSUER_KEY,
        "identity_verification_level": delta.IDENTITY_VERIFICATION_LEVEL,
        "session_nonce": manifest["session_nonce"],
        "session_manifest_hash": manifest["session_manifest_hash"],
        "issuer_claim": issuer_claim,
        "issuer_signature": "test-issuer-signature",
        "role_specific_challenge": challenge,
        "role_signature": "test-role-signature",
    }


def _new_state(manifest: dict) -> dict:
    return delta.create_session_state(
        manifest,
        trusted_proof_issuers={"trusted-hosted-proof-issuer": _HOSTED_PROOF_KEY},
        runner=_successful_runner,
    )


def _open_baseline(state: dict, manifest: dict, occurred_at: str) -> dict:
    return delta.open_baseline(
        state,
        session_manifest=manifest,
        operator_identity_evidence=_fake_operator_identity(manifest),
        trusted_issuers={"trusted-human-issuer": _IDENTITY_ISSUER_KEY},
        eligibility=_eligibility(),
        occurred_at=occurred_at,
        runner=_successful_runner,
    )


def _eligibility() -> dict[str, bool]:
    return {
        "no_prior_alpha_claim_exposure": True,
        "no_alpha_implementation_dogfood_audit_or_review": True,
        "no_material_post_cutoff_information": True,
        "no_current_price_or_subsequent_event_use": True,
        "no_outside_research": True,
        "no_projection_access_before_baseline_seal": True,
    }


def _submission(action: str, suffix: str) -> dict:
    return {
        "current_research_action": action,
        "rationale": f"Evidence custody and missing telemetry support this research action {suffix}.",
        "indispensable_missing_evidence": [f"Physical telemetry {suffix}"],
        "falsifiers_or_contradictions": [f"Peer language is not issuer telemetry {suffix}"],
        "claim_separation_statements": [f"Supply context is distinct from business capture {suffix}"],
        "evidence_locator_ids": ["SRC_MU_001", "SRC_NVDA_001"],
    }


def _advance_to_post_sealed() -> tuple[dict, dict]:
    manifest = _manifest()
    state = _new_state(manifest)
    start = datetime(2026, 7, 28, 1, 0, tzinfo=timezone.utc)
    state = _open_baseline(state, manifest, delta.canonical_timestamp(start))
    state = delta.seal_arm(
        state,
        arm="BASELINE",
        submission=_submission("HOLD_FOR_EVIDENCE", "one"),
        occurred_at=delta.canonical_timestamp(start + timedelta(minutes=17)),
    )
    state = delta.release_projection(
        state,
        evidence_bundle_hash="3" * 64,
        projection_hash="4" * 64,
        occurred_at=delta.canonical_timestamp(start + timedelta(minutes=18)),
    )
    state = delta.open_post(
        state, occurred_at=delta.canonical_timestamp(start + timedelta(minutes=19))
    )
    state = delta.seal_arm(
        state,
        arm="POST",
        submission=_submission("ADVANCE_TO_FULL_RESEARCH", "two"),
        occurred_at=delta.canonical_timestamp(start + timedelta(minutes=31)),
    )
    return manifest, state


def test_cli_atomic_write_is_canonical_and_leaves_no_temp(tmp_path) -> None:
    target = tmp_path / "nested" / "record.json"
    record = {"z": 1, "a": [2, 3]}
    cli._write(target, record)
    assert target.read_bytes() == canonical_document_bytes(record)
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []


def test_cli_direct_entrypoint_loads_repository_modules() -> None:
    completed = subprocess.run(
        [sys.executable, str(delta.ROOT / "scripts/gv_one_case_delta_capture.py"), "--help"],
        cwd=delta.ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "create-session-manifest" in completed.stdout
    assert "preflight-identities" in completed.stdout


def test_session_manifest_binds_hosted_candidate_after_static_binding() -> None:
    manifest = _manifest()
    assert manifest["candidate_sha"] == "a" * 40
    assert manifest["candidate_tree"] == "b" * 40
    assert manifest["one_shot_state"] == "AVAILABLE_PRE_EXPOSURE"
    assert manifest["hosted_proof_identity"]["payload"]["windows_conclusion"] == "SUCCESS"
    assert manifest["hosted_proof_identity"]["payload"]["linux_conclusion"] == "SUCCESS"
    assert len(manifest["hosted_proof_hash"]) == 64
    with pytest.raises(delta.OneCaseDeltaError, match="HOSTED_WINDOWS_NOT_GREEN"):
        delta.create_session_manifest(
            candidate_sha="a" * 40,
            candidate_tree="b" * 40,
            experiment_binding_hash="c" * 64,
            evidence_bundle_hash="3" * 64,
            projection_hash="4" * 64,
            projection_manifest_hash="5" * 64,
            projection_schema_hash=delta.PROJECTION_SCHEMA_HASH,
            operator_instruction_hash="e" * 64,
            reviewer_instruction_hash="f" * 64,
            hosted_proof_identity=_hosted_proof(windows="FAILURE"),
            trusted_proof_issuers={"trusted-hosted-proof-issuer": _HOSTED_PROOF_KEY},
            runner=_successful_runner,
        )
    with pytest.raises(delta.OneCaseDeltaError, match="HOSTED_PROOF_CANDIDATE_MISMATCH"):
        delta.create_session_manifest(
            candidate_sha="a" * 40,
            candidate_tree="b" * 40,
            experiment_binding_hash="c" * 64,
            evidence_bundle_hash="3" * 64,
            projection_hash="4" * 64,
            projection_manifest_hash="5" * 64,
            projection_schema_hash=delta.PROJECTION_SCHEMA_HASH,
            operator_instruction_hash="e" * 64,
            reviewer_instruction_hash="f" * 64,
            hosted_proof_identity=_hosted_proof(candidate_sha="9" * 40),
            trusted_proof_issuers={"trusted-hosted-proof-issuer": _HOSTED_PROOF_KEY},
            runner=_successful_runner,
        )


def test_pre_exposure_abort_does_not_consume_one_shot() -> None:
    manifest = _manifest()
    state = _new_state(manifest)
    aborted = delta.pre_exposure_abort(
        state,
        reason="participant unavailable",
        occurred_at="2026-07-28T01:00:00.000000Z",
    )
    assert aborted["phase"] == delta.PHASE_PRE_EXPOSURE_ABORTED
    assert aborted["one_shot_consumed"] is False
    delta.verify_event_chain(aborted)


def test_baseline_open_consumes_one_shot_and_later_abort_is_terminal() -> None:
    manifest = _manifest()
    state = _new_state(manifest)
    state = _open_baseline(state, manifest, "2026-07-28T01:00:00.000000Z")
    assert state["one_shot_consumed"] is True
    aborted = delta.consumed_abort(
        state,
        reason="contamination discovered",
        occurred_at="2026-07-28T01:01:00.000000Z",
    )
    assert aborted["phase"] == delta.PHASE_TERMINAL_INELIGIBLE
    assert aborted["one_shot_consumed"] is True


def test_equal_maximum_budget_allows_early_submit_and_rejects_late_submit() -> None:
    manifest = _manifest()
    state = _new_state(manifest)
    state = _open_baseline(state, manifest, "2026-07-28T01:00:00.000000Z")
    early = delta.seal_arm(
        state,
        arm="BASELINE",
        submission=_submission("HOLD_FOR_EVIDENCE", "early"),
        occurred_at="2026-07-28T01:10:00.000000Z",
    )
    payload = early["events"][-1]["payload"]
    assert payload["elapsed_seconds"] == 600
    assert payload["maximum_budget_seconds"] == 3600
    assert payload["early_submission_allowed"] is True
    assert payload["latency_endpoint"] == "NONE"

    with pytest.raises(delta.OneCaseDeltaError, match="ARM_BUDGET_EXCEEDED"):
        delta.seal_arm(
            state,
            arm="BASELINE",
            submission=_submission("HOLD_FOR_EVIDENCE", "late"),
            occurred_at="2026-07-28T02:00:00.000001Z",
        )


def test_projection_release_rejects_session_artifact_substitution() -> None:
    manifest = _manifest()
    state = _new_state(manifest)
    state = _open_baseline(state, manifest, "2026-07-28T01:00:00.000000Z")
    state = delta.seal_arm(
        state,
        arm="BASELINE",
        submission=_submission("HOLD_FOR_EVIDENCE", "bound"),
        occurred_at="2026-07-28T01:10:00.000000Z",
    )
    with pytest.raises(delta.OneCaseDeltaError, match="EVIDENCE_BUNDLE_SESSION_MISMATCH"):
        delta.release_projection(
            state,
            evidence_bundle_hash="9" * 64,
            projection_hash=manifest["projection_hash"],
            occurred_at="2026-07-28T01:11:00.000000Z",
        )
    with pytest.raises(delta.OneCaseDeltaError, match="PROJECTION_SESSION_MISMATCH"):
        delta.release_projection(
            state,
            evidence_bundle_hash=manifest["evidence_bundle_hash"],
            projection_hash="9" * 64,
            occurred_at="2026-07-28T01:11:00.000000Z",
        )


def test_review_package_retains_current_actions_and_scrubs_origin_metadata() -> None:
    _, state = _advance_to_post_sealed()
    package, mapping, state = delta.build_review_package(
        state,
        random_bit=1,
        occurred_at="2026-07-28T01:32:00.000000Z",
    )
    assert state["phase"] == delta.PHASE_REVIEW_PACKAGE_SEALED
    assert mapping["arm_a_origin"] == "POST"
    assert mapping["arm_b_origin"] == "BASELINE"
    assert package["arms"]["ARM_A"]["current_research_action"] == "ADVANCE_TO_FULL_RESEARCH"
    assert package["arms"]["ARM_B"]["current_research_action"] == "HOLD_FOR_EVIDENCE"
    text = str(package)
    for forbidden in ("elapsed_seconds", "session_nonce", "case_id", "portfolio_action"):
        assert forbidden not in text


def test_replay_detects_mutation_omission_reorder_and_aliasing() -> None:
    _, state = _advance_to_post_sealed()
    delta.verify_event_chain(state)

    mutated = copy.deepcopy(state)
    mutated["events"][0]["payload"]["eligibility_attestation_hash"] = "0" * 64
    mutated_body = delta._without_hash(mutated, "session_state_hash")
    mutated["session_state_hash"] = delta._hash(delta.DOMAIN_STATE, mutated_body)
    with pytest.raises(delta.OneCaseDeltaError, match="EVENT_HASH_INVALID"):
        delta.verify_event_chain(mutated)

    omitted = copy.deepcopy(state)
    omitted["events"].pop(1)
    omitted_body = delta._without_hash(omitted, "session_state_hash")
    omitted["session_state_hash"] = delta._hash(delta.DOMAIN_STATE, omitted_body)
    with pytest.raises(delta.OneCaseDeltaError, match="EVENT_SEQUENCE_INVALID|EVENT_CHAIN_PREVIOUS_INVALID"):
        delta.verify_event_chain(omitted)

    reordered = copy.deepcopy(state)
    reordered["events"][1], reordered["events"][2] = reordered["events"][2], reordered["events"][1]
    reordered_body = delta._without_hash(reordered, "session_state_hash")
    reordered["session_state_hash"] = delta._hash(delta.DOMAIN_STATE, reordered_body)
    with pytest.raises(delta.OneCaseDeltaError):
        delta.verify_event_chain(reordered)

    aliased = copy.deepcopy(state)
    aliased["events"].append(copy.deepcopy(aliased["events"][-1]))
    aliased_body = delta._without_hash(aliased, "session_state_hash")
    aliased["session_state_hash"] = delta._hash(delta.DOMAIN_STATE, aliased_body)
    with pytest.raises(delta.OneCaseDeltaError, match="EVENT_SEQUENCE_INVALID"):
        delta.verify_event_chain(aliased)


def test_disposition_positive_zero_and_negative_are_sign_independent_observations() -> None:
    base = {item: 1 for item in delta.RUBRIC_ITEMS}
    positive = dict(base)
    positive["indispensable_missing_evidence_identification"] = 2
    assert delta.decision_value_disposition(
        baseline_scores=base, post_scores=positive
    )[0] == "IMPROVED"
    assert delta.decision_value_disposition(
        baseline_scores=base, post_scores=base
    )[0] == "NOT_IMPROVED"
    negative = dict(base)
    negative["selected_action_defensibility"] = 0
    assert delta.decision_value_disposition(
        baseline_scores=base, post_scores=negative
    )[0] == "NOT_IMPROVED"


def test_commit_a_machinery_does_not_mutate_current_authority() -> None:
    current_path = delta.ROOT / "data/gv_fs0/gv_fs0_current_decision.json"
    before = sha256_bytes(current_path.read_bytes())
    delta.build_pre_human_artifacts()
    _advance_to_post_sealed()
    after = sha256_bytes(current_path.read_bytes())
    assert after == before
