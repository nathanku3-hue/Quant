from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

import core.gv_one_case_delta as delta
from core.gv_fs0_canonical import canonical_document_bytes


_HOSTED_PROOF_KEY = "ssh-ed25519 AAAATESTHOSTEDPROOFKEY"


def _successful_runner(*args, **kwargs) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(args=args, returncode=0, stdout=b"", stderr=b"")


def _hosted_proof() -> dict:
    return {
        "schema_version": delta.SCHEMA_HOSTED_PROOF,
        "adapter": delta.IDENTITY_ADAPTER,
        "proof_provider": "trusted-hosted-proof-issuer",
        "provider_public_key": _HOSTED_PROOF_KEY,
        "payload": {
            "proof_id": "hosted-proof-1",
            "candidate_sha": "a" * 40,
            "candidate_tree": "b" * 40,
            "workflow_name": "GV-FS0 Product",
            "windows_run_id": "win-1",
            "windows_conclusion": "SUCCESS",
            "linux_run_id": "linux-1",
            "linux_conclusion": "SUCCESS",
            "verified_at": "2026-07-28T00:00:00.000000Z",
        },
        "signature": "test-signature",
    }


def _require_ssh_keygen() -> str:
    executable = shutil.which("ssh-keygen")
    if executable is None:
        pytest.fail("OPENSSH_SSHSIG_V1 requires ssh-keygen on hosted runners")
    return executable


def _make_key(tmp_path: Path, name: str) -> tuple[Path, str]:
    executable = _require_ssh_keygen()
    private = tmp_path / name
    subprocess.run(
        [executable, "-q", "-t", "ed25519", "-N", "", "-f", str(private)],
        check=True,
        capture_output=True,
        text=True,
    )
    fields = private.with_suffix(".pub").read_text(encoding="utf-8").strip().split()
    return private, " ".join(fields[:2])


def _sign(tmp_path: Path, private: Path, namespace: str, name: str, payload: dict) -> str:
    executable = _require_ssh_keygen()
    message = tmp_path / f"{name}.json"
    message.write_bytes(canonical_document_bytes(payload))
    subprocess.run(
        [executable, "-Y", "sign", "-f", str(private), "-n", namespace, str(message)],
        check=True,
        capture_output=True,
        text=True,
    )
    signature_path = Path(str(message) + ".sig")
    return signature_path.read_text(encoding="utf-8")


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
        "rationale": f"Current evidence supports this research action {suffix}.",
        "indispensable_missing_evidence": [f"Physical telemetry {suffix}"],
        "falsifiers_or_contradictions": [f"Peer language is not issuer telemetry {suffix}"],
        "claim_separation_statements": [f"Supply context differs from business capture {suffix}"],
        "evidence_locator_ids": ["SRC_MU_001", "SRC_NVDA_001"],
    }


def _review_state(
    manifest: dict,
    *,
    operator_identity: dict,
    trusted_issuers: dict[str, str],
    runner=subprocess.run,
) -> tuple[dict, dict, dict]:
    state = delta.create_session_state(
        manifest,
        trusted_proof_issuers={"trusted-hosted-proof-issuer": _HOSTED_PROOF_KEY},
        runner=_successful_runner,
    )
    state = delta.open_baseline(
        state,
        session_manifest=manifest,
        operator_identity_evidence=operator_identity,
        trusted_issuers=trusted_issuers,
        eligibility=_eligibility(),
        occurred_at="2026-07-28T01:00:00.000000Z",
        runner=runner,
    )
    state = delta.seal_arm(
        state,
        arm="BASELINE",
        submission=_submission("HOLD_FOR_EVIDENCE", "one"),
        occurred_at="2026-07-28T01:10:00.000000Z",
    )
    state = delta.release_projection(
        state,
        evidence_bundle_hash="3" * 64,
        projection_hash="4" * 64,
        occurred_at="2026-07-28T01:11:00.000000Z",
    )
    state = delta.open_post(state, occurred_at="2026-07-28T01:12:00.000000Z")
    state = delta.seal_arm(
        state,
        arm="POST",
        submission=_submission("ADVANCE_TO_FULL_RESEARCH", "two"),
        occurred_at="2026-07-28T01:22:00.000000Z",
    )
    package, mapping, state = delta.build_review_package(
        state,
        random_bit=0,
        occurred_at="2026-07-28T01:23:00.000000Z",
    )
    return package, mapping, state


def _identity_record(
    tmp_path: Path,
    *,
    role: str,
    principal: str,
    subject: str,
    credential_private: Path,
    credential_public: str,
    issuer_private: Path,
    issuer_public: str,
    issuer_id: str,
    manifest: dict,
    review_package_hash: str | None = None,
    rubric_digest: str | None = None,
    preflight_only: bool = False,
) -> dict:
    fingerprint = delta._public_key_fingerprint(credential_public)
    evidence_id = f"identity-{principal}"
    signed_at = "2026-07-28T01:00:00.000000Z"
    issuer_claim = {
        "identity_evidence_id": evidence_id,
        "signed_at": signed_at,
        "verified_human_subject_commitment": subject,
        "principal_id": principal,
        "credential_fingerprint": fingerprint,
        "identity_verification_level": delta.IDENTITY_VERIFICATION_LEVEL,
        "identity_evidence_issuer": issuer_id,
    }
    challenge = {
        "identity_evidence_id": evidence_id,
        "role": role,
        "principal_id": principal,
        "verified_human_subject_commitment": subject,
        "credential_fingerprint": fingerprint,
        "session_nonce": manifest["session_nonce"],
        "session_manifest_hash": manifest["session_manifest_hash"],
    }
    if role == delta.ROLE_REVIEWER:
        if preflight_only:
            challenge.update(
                {
                    "preflight_only": True,
                    "review_package_hash": "PREFLIGHT_PENDING",
                    "rubric_hash": "PREFLIGHT_PENDING",
                }
            )
        else:
            assert review_package_hash is not None
            assert rubric_digest is not None
            challenge.update(
                {
                    "preflight_only": False,
                    "review_package_hash": review_package_hash,
                    "rubric_hash": rubric_digest,
                }
            )
    return {
        "schema_version": delta.SCHEMA_IDENTITY,
        "adapter": delta.IDENTITY_ADAPTER,
        "identity_evidence_id": evidence_id,
        "signed_at": signed_at,
        "role": role,
        "principal_id": principal,
        "verified_human_subject_commitment": subject,
        "credential_public_key": credential_public,
        "credential_fingerprint": fingerprint,
        "identity_evidence_issuer": issuer_id,
        "issuer_public_key": issuer_public,
        "identity_verification_level": delta.IDENTITY_VERIFICATION_LEVEL,
        "session_nonce": manifest["session_nonce"],
        "session_manifest_hash": manifest["session_manifest_hash"],
        "issuer_claim": issuer_claim,
        "issuer_signature": _sign(
            tmp_path,
            issuer_private,
            delta.IDENTITY_NAMESPACE,
            f"{principal}-issuer",
            issuer_claim,
        ),
        "role_specific_challenge": challenge,
        "role_signature": _sign(
            tmp_path,
            credential_private,
            delta.ROLE_NAMESPACE,
            f"{principal}-role",
            challenge,
        ),
    }


def test_hosted_proof_requires_pinned_signed_candidate_and_matrix(tmp_path: Path) -> None:
    private, public = _make_key(tmp_path, "hosted-proof-issuer")
    payload = {
        "proof_id": "hosted-proof-real-1",
        "candidate_sha": "a" * 40,
        "candidate_tree": "b" * 40,
        "workflow_name": "GV-FS0 Product",
        "windows_run_id": "win-123",
        "windows_conclusion": "SUCCESS",
        "linux_run_id": "linux-456",
        "linux_conclusion": "SUCCESS",
        "verified_at": "2026-07-28T00:00:00.000000Z",
    }
    proof = {
        "schema_version": delta.SCHEMA_HOSTED_PROOF,
        "adapter": delta.IDENTITY_ADAPTER,
        "proof_provider": "trusted-hosted-proof-issuer",
        "provider_public_key": public,
        "payload": payload,
        "signature": _sign(
            tmp_path,
            private,
            delta.HOSTED_PROOF_NAMESPACE,
            "hosted-proof",
            payload,
        ),
    }
    manifest = delta.create_session_manifest(
        candidate_sha="a" * 40,
        candidate_tree="b" * 40,
        experiment_binding_hash="c" * 64,
        evidence_bundle_hash="3" * 64,
        projection_hash="4" * 64,
        projection_manifest_hash="5" * 64,
        projection_schema_hash=delta.PROJECTION_SCHEMA_HASH,
        operator_instruction_hash="e" * 64,
        reviewer_instruction_hash="f" * 64,
        hosted_proof_identity=proof,
        trusted_proof_issuers={"trusted-hosted-proof-issuer": public},
        session_nonce="1" * 64,
    )
    assert manifest["hosted_proof_hash"]
    with pytest.raises(delta.OneCaseDeltaError, match="HOSTED_PROOF_PROVIDER_UNTRUSTED"):
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
            hosted_proof_identity=proof,
            trusted_proof_issuers={},
        )
    tampered = dict(proof)
    tampered["payload"] = dict(payload)
    tampered["payload"]["linux_run_id"] = "substituted"
    with pytest.raises(delta.OneCaseDeltaError, match="SSHSIG_VERIFICATION_FAILED"):
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
            hosted_proof_identity=tampered,
            trusted_proof_issuers={"trusted-hosted-proof-issuer": public},
        )


def test_two_separately_signed_verified_humans_pass(tmp_path: Path) -> None:
    manifest = _manifest()
    issuer_private, issuer_public = _make_key(tmp_path, "issuer")
    operator_private, operator_public = _make_key(tmp_path, "operator")
    reviewer_private, reviewer_public = _make_key(tmp_path, "reviewer")
    operator = _identity_record(
        tmp_path,
        role=delta.ROLE_OPERATOR,
        principal="operator-principal",
        subject="operator-subject-commitment-00000000000000000001",
        credential_private=operator_private,
        credential_public=operator_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
    )
    reviewer = _identity_record(
        tmp_path,
        role=delta.ROLE_REVIEWER,
        principal="reviewer-principal",
        subject="reviewer-subject-commitment-00000000000000000001",
        credential_private=reviewer_private,
        credential_public=reviewer_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
        review_package_hash="8" * 64,
        rubric_digest="9" * 64,
    )
    trusted = {"trusted-human-issuer": issuer_public}
    operator_hash = delta.verify_identity_evidence(
        operator,
        expected_role=delta.ROLE_OPERATOR,
        session_manifest=manifest,
        trusted_issuers=trusted,
    )
    reviewer_hash = delta.verify_identity_evidence(
        reviewer,
        expected_role=delta.ROLE_REVIEWER,
        session_manifest=manifest,
        trusted_issuers=trusted,
        review_package_hash="8" * 64,
        rubric_digest="9" * 64,
    )
    delta.require_distinct_humans(operator, reviewer)
    assert len(operator_hash) == 64
    assert len(reviewer_hash) == 64
    assert operator_hash != reviewer_hash


def test_unequal_principal_strings_do_not_override_same_human_subject(tmp_path: Path) -> None:
    manifest = _manifest()
    issuer_private, issuer_public = _make_key(tmp_path, "issuer")
    operator_private, operator_public = _make_key(tmp_path, "operator")
    reviewer_private, reviewer_public = _make_key(tmp_path, "reviewer")
    shared_subject = "same-human-subject-commitment-000000000000000000001"
    operator = _identity_record(
        tmp_path,
        role=delta.ROLE_OPERATOR,
        principal="principal-one",
        subject=shared_subject,
        credential_private=operator_private,
        credential_public=operator_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
    )
    reviewer = _identity_record(
        tmp_path,
        role=delta.ROLE_REVIEWER,
        principal="principal-two",
        subject=shared_subject,
        credential_private=reviewer_private,
        credential_public=reviewer_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
        preflight_only=True,
    )
    with pytest.raises(delta.OneCaseDeltaError, match="SAME_HUMAN_SUBJECT_PROHIBITED"):
        delta.require_distinct_humans(operator, reviewer)


def test_signature_role_session_and_issuer_substitution_fail(tmp_path: Path) -> None:
    manifest = _manifest()
    issuer_private, issuer_public = _make_key(tmp_path, "issuer")
    operator_private, operator_public = _make_key(tmp_path, "operator")
    record = _identity_record(
        tmp_path,
        role=delta.ROLE_OPERATOR,
        principal="operator-principal",
        subject="operator-subject-commitment-00000000000000000001",
        credential_private=operator_private,
        credential_public=operator_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
    )
    trusted = {"trusted-human-issuer": issuer_public}

    wrong_role = dict(record)
    wrong_role["role"] = delta.ROLE_REVIEWER
    with pytest.raises(delta.OneCaseDeltaError, match="IDENTITY_ROLE_INVALID"):
        delta.verify_identity_evidence(
            wrong_role,
            expected_role=delta.ROLE_OPERATOR,
            session_manifest=manifest,
            trusted_issuers=trusted,
        )

    wrong_session = dict(record)
    wrong_session["session_nonce"] = "9" * 64
    with pytest.raises(delta.OneCaseDeltaError, match="IDENTITY_NONCE_MISMATCH"):
        delta.verify_identity_evidence(
            wrong_session,
            expected_role=delta.ROLE_OPERATOR,
            session_manifest=manifest,
            trusted_issuers=trusted,
        )

    with pytest.raises(delta.OneCaseDeltaError, match="IDENTITY_ISSUER_UNTRUSTED"):
        delta.verify_identity_evidence(
            record,
            expected_role=delta.ROLE_OPERATOR,
            session_manifest=manifest,
            trusted_issuers={},
        )

    tampered = dict(record)
    tampered["role_specific_challenge"] = dict(record["role_specific_challenge"])
    tampered["role_specific_challenge"]["principal_id"] = "substituted"
    with pytest.raises(delta.OneCaseDeltaError, match="IDENTITY_ROLE_CHALLENGE_INVALID"):
        delta.verify_identity_evidence(
            tampered,
            expected_role=delta.ROLE_OPERATOR,
            session_manifest=manifest,
            trusted_issuers=trusted,
        )


def test_detached_attestation_binds_all_session_authority(tmp_path: Path) -> None:
    private, public = _make_key(tmp_path, "attestor")
    payload = {
        "session_manifest_hash": "1" * 64,
        "sealed_record_hashes": ["2" * 64, "3" * 64],
        "review_package_hash": "4" * 64,
        "rubric_hash": "5" * 64,
        "operator_identity_evidence_hash": "6" * 64,
        "reviewer_identity_evidence_hash": "7" * 64,
        "attestation_statements": ["records independently replayed", "mapping remained sealed"],
        "attestation_id": "attestation-1",
        "attestation_provider": "LOCAL_OPENSSH",
    }
    record = {
        "schema_version": delta.SCHEMA_ATTESTATION,
        "adapter": delta.IDENTITY_ADAPTER,
        "payload": payload,
        "attestation_statements": payload["attestation_statements"],
        "attestation_id": payload["attestation_id"],
        "attestation_provider": payload["attestation_provider"],
        "attestor_id": "independent-attestor",
        "attestor_public_key": public,
        "signature": _sign(
            tmp_path,
            private,
            delta.ATTESTATION_NAMESPACE,
            "session-attestation",
            payload,
        ),
    }
    digest = delta.validate_session_attestation(
        record,
        session_manifest_hash="1" * 64,
        sealed_record_hashes=["2" * 64, "3" * 64],
        review_package_hash="4" * 64,
        rubric_digest="5" * 64,
        operator_identity_evidence_hash="6" * 64,
        reviewer_identity_evidence_hash="7" * 64,
    )
    assert len(digest) == 64
    with pytest.raises(delta.OneCaseDeltaError, match="ATTESTATION_PAYLOAD_INVALID"):
        delta.validate_session_attestation(
            record,
            session_manifest_hash="9" * 64,
            sealed_record_hashes=["2" * 64, "3" * 64],
            review_package_hash="4" * 64,
            rubric_digest="5" * 64,
            operator_identity_evidence_hash="6" * 64,
            reviewer_identity_evidence_hash="7" * 64,
        )


def test_reviewer_preflight_signature_cannot_authorize_final_review(tmp_path: Path) -> None:
    manifest = _manifest()
    issuer_private, issuer_public = _make_key(tmp_path, "issuer")
    reviewer_private, reviewer_public = _make_key(tmp_path, "reviewer")
    reviewer = _identity_record(
        tmp_path,
        role=delta.ROLE_REVIEWER,
        principal="reviewer-principal",
        subject="reviewer-subject-commitment-00000000000000000001",
        credential_private=reviewer_private,
        credential_public=reviewer_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
        preflight_only=True,
    )
    trusted = {"trusted-human-issuer": issuer_public}
    digest = delta.verify_identity_evidence(
        reviewer,
        expected_role=delta.ROLE_REVIEWER,
        session_manifest=manifest,
        trusted_issuers=trusted,
        preflight_only=True,
    )
    assert len(digest) == 64
    with pytest.raises(delta.OneCaseDeltaError, match="IDENTITY_ROLE_CHALLENGE_INVALID"):
        delta.verify_identity_evidence(
            reviewer,
            expected_role=delta.ROLE_REVIEWER,
            session_manifest=manifest,
            trusted_issuers=trusted,
            review_package_hash="8" * 64,
            rubric_digest="9" * 64,
        )


def test_terminal_result_replays_signed_identity_rubric_attestation_and_mapping(
    tmp_path: Path,
) -> None:
    manifest = _manifest()
    issuer_private, issuer_public = _make_key(tmp_path, "issuer")
    operator_private, operator_public = _make_key(tmp_path, "operator")
    reviewer_private, reviewer_public = _make_key(tmp_path, "reviewer")
    substitute_private, substitute_public = _make_key(tmp_path, "operator-substitute")
    attestor_private, attestor_public = _make_key(tmp_path, "attestor")
    operator = _identity_record(
        tmp_path,
        role=delta.ROLE_OPERATOR,
        principal="operator-principal",
        subject="operator-subject-commitment-00000000000000000001",
        credential_private=operator_private,
        credential_public=operator_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
    )
    trusted = {"trusted-human-issuer": issuer_public}
    package, mapping, state = _review_state(
        manifest,
        operator_identity=operator,
        trusted_issuers=trusted,
    )
    scores = {
        "ARM_A": {item: 1 for item in delta.RUBRIC_ITEMS},
        "ARM_B": {item: 1 for item in delta.RUBRIC_ITEMS},
    }
    scores["ARM_B"]["indispensable_missing_evidence_identification"] = 2
    rubric_digest = delta.rubric_hash(scores)
    reviewer = _identity_record(
        tmp_path,
        role=delta.ROLE_REVIEWER,
        principal="reviewer-principal",
        subject="reviewer-subject-commitment-00000000000000000001",
        credential_private=reviewer_private,
        credential_public=reviewer_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
        review_package_hash=package["review_package_hash"],
        rubric_digest=rubric_digest,
    )
    operator_hash = delta.verify_identity_evidence(
        operator,
        expected_role=delta.ROLE_OPERATOR,
        session_manifest=manifest,
        trusted_issuers=trusted,
    )
    reviewer_hash = delta.verify_identity_evidence(
        reviewer,
        expected_role=delta.ROLE_REVIEWER,
        session_manifest=manifest,
        trusted_issuers=trusted,
        review_package_hash=package["review_package_hash"],
        rubric_digest=rubric_digest,
    )
    attestation_payload = {
        "session_manifest_hash": manifest["session_manifest_hash"],
        "sealed_record_hashes": delta.sealed_record_hashes(state),
        "review_package_hash": package["review_package_hash"],
        "rubric_hash": rubric_digest,
        "operator_identity_evidence_hash": operator_hash,
        "reviewer_identity_evidence_hash": reviewer_hash,
        "attestation_statements": [
            "records independently replayed",
            "mapping remained sealed until review authority was sealed",
        ],
        "attestation_id": "attestation-terminal-1",
        "attestation_provider": "LOCAL_OPENSSH",
    }
    attestation = {
        "schema_version": delta.SCHEMA_ATTESTATION,
        "adapter": delta.IDENTITY_ADAPTER,
        "payload": attestation_payload,
        "attestation_statements": attestation_payload["attestation_statements"],
        "attestation_id": attestation_payload["attestation_id"],
        "attestation_provider": attestation_payload["attestation_provider"],
        "attestor_id": "independent-attestor",
        "attestor_public_key": attestor_public,
        "signature": _sign(
            tmp_path,
            attestor_private,
            delta.ATTESTATION_NAMESPACE,
            "terminal-attestation",
            attestation_payload,
        ),
    }
    substituted_operator = _identity_record(
        tmp_path,
        role=delta.ROLE_OPERATOR,
        principal="operator-substitute-principal",
        subject="operator-substitute-subject-commitment-000000000001",
        credential_private=substitute_private,
        credential_public=substitute_public,
        issuer_private=issuer_private,
        issuer_public=issuer_public,
        issuer_id="trusted-human-issuer",
        manifest=manifest,
    )
    with pytest.raises(
        delta.OneCaseDeltaError,
        match="OPERATOR_IDENTITY_CHANGED_AFTER_EXPOSURE",
    ):
        delta.seal_review_authority(
            state=state,
            session_manifest=manifest,
            review_package=package,
            scores=scores,
            operator_identity_evidence=substituted_operator,
            reviewer_identity_evidence=reviewer,
            trusted_issuers=trusted,
            session_attestation=attestation,
            occurred_at="2026-07-28T01:24:00.000000Z",
        )

    state = delta.seal_review_authority(
        state=state,
        session_manifest=manifest,
        review_package=package,
        scores=scores,
        operator_identity_evidence=operator,
        reviewer_identity_evidence=reviewer,
        trusted_issuers=trusted,
        session_attestation=attestation,
        occurred_at="2026-07-28T01:24:00.000000Z",
    )
    assert state["phase"] == delta.PHASE_REVIEW_AUTHORITY_SEALED
    result, terminal_state = delta.reveal_mapping_and_finalize(
        state=state,
        review_package=package,
        review_mapping=mapping,
        occurred_at="2026-07-28T01:25:00.000000Z",
    )
    assert terminal_state["phase"] == delta.PHASE_TERMINAL_ELIGIBLE
    assert result["eligible"] is True
    assert result["observed_comparison_count"] == 1
    assert result["decision_value_disposition"] == "IMPROVED"
    assert result["score_change"] == 0
    assert result["alpha_claim"] is False
    assert result["publication_authority"] is False
    assert result["terminal_session_state_hash"] == terminal_state["session_state_hash"]
