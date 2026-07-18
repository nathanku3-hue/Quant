"""Section-15 recovery matrix for the single-current-decision publication path."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import core.gv_fs0_publish as publication
from core.gv_e0a_operable import build_e0a_certified_result
from core.gv_fs0_canonical import canonical_document_bytes, sha256_bytes
from core.gv_fs0_current_decision import certified_decision_result_bytes
from core.gv_fs0_publish import (
    CURRENT_DECISION_TARGET_TOKEN,
    GvFs0PublicationError,
    PUBLICATION_LOCKED,
    PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
    PUBLICATION_RECOVERY_RECORD_FAILED,
    PUBLICATION_TARGET_CHANGED,
    publish_current_decision,
)

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CURRENT_FILE_SHA256 = (
    "7ba9c7c48dfc89ceae2a5a88aba8bfebbe6d5032272b0d254f4139478699b5c9"
)


def _paths(tmp_path: Path) -> tuple[Path, Path]:
    target = tmp_path / "data" / "gv_fs0" / "gv_fs0_current_decision.json"
    lock = target.parent / ".gv_fs0_current_decision.lock"
    return target, lock


@pytest.fixture(scope="module")
def e0a_result() -> dict:
    return build_e0a_certified_result(root=ROOT)


def test_current_decision_locked_blocks_without_age_or_pid_recovery(
    tmp_path: Path, e0a_result: dict
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    lock.write_bytes(
        b'{"record_version":"GV-FS0-PUBLICATION-RECOVERY-V1",'
        b'"state":"RECOVERY_REQUIRED","target_token":"GV_FS0_CURRENT_DECISION"}\n'
    )
    os.utime(lock, (1, 1))
    original = lock.read_bytes()

    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_LOCKED) as caught:
        publish_current_decision(e0a_result, target=target, lock_path=lock)
    assert caught.value.code == PUBLICATION_LOCKED
    assert lock.read_bytes() == original
    assert not target.exists()


def test_current_decision_target_changed_after_observation_not_overwritten(
    tmp_path: Path, e0a_result: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    prior = b'{"state":"prior"}\n'
    concurrent = b'{"state":"concurrent"}\n'
    target.write_bytes(prior)
    real_acquire = publication._acquire_lock

    def mutate_then_lock(path: Path) -> None:
        target.write_bytes(concurrent)
        real_acquire(path)

    monkeypatch.setattr(publication, "_acquire_lock", mutate_then_lock)
    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_TARGET_CHANGED):
        publish_current_decision(e0a_result, target=target, lock_path=lock)
    assert target.read_bytes() == concurrent
    assert not lock.exists()


def test_current_decision_pre_replace_failure_preserves_prior(
    tmp_path: Path, e0a_result: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    prior = b'{"state":"prior"}\n'
    target.write_bytes(prior)

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("injected pre-replace failure")

    monkeypatch.setattr(publication, "_replace_file", fail_replace)
    with pytest.raises(OSError, match="injected pre-replace failure"):
        publish_current_decision(e0a_result, target=target, lock_path=lock)
    assert target.read_bytes() == prior
    assert not lock.exists()
    assert not list(target.parent.glob("*.tmp"))


def test_current_decision_post_replace_creates_recovery_lock_with_token(
    tmp_path: Path, e0a_result: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    prior = b'{"state":"prior"}\n'
    target.write_bytes(prior)
    candidate = certified_decision_result_bytes(e0a_result)
    candidate_hash = sha256_bytes(candidate)

    def fail_verify(
        _target: Path, _candidate: bytes, _parse_fn: object
    ) -> str:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            "injected_current_post_replace",
        )

    monkeypatch.setattr(publication, "_verify_published_bytes", fail_verify)
    with pytest.raises(
        GvFs0PublicationError, match=PUBLICATION_POST_REPLACE_VERIFICATION_FAILED
    ):
        publish_current_decision(e0a_result, target=target, lock_path=lock)

    assert target.read_bytes() == candidate
    recovery = lock.read_bytes()
    assert b'"state":"RECOVERY_REQUIRED"' in recovery
    assert CURRENT_DECISION_TARGET_TOKEN.encode("utf-8") in recovery
    assert candidate_hash.encode("utf-8") in recovery
    # No automatic removal of recovery lock.
    assert lock.exists()


def test_current_decision_recovery_write_failure_retains_lock(
    tmp_path: Path, e0a_result: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)

    def fail_verify(
        _target: Path, _candidate: bytes, _parse_fn: object
    ) -> str:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            "injected_current_post_replace",
        )

    def fail_recovery(_lock: Path, _record: dict[str, str]) -> None:
        raise OSError("injected recovery failure")

    monkeypatch.setattr(publication, "_verify_published_bytes", fail_verify)
    monkeypatch.setattr(publication, "_write_recovery_record", fail_recovery)
    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_RECOVERY_RECORD_FAILED):
        publish_current_decision(e0a_result, target=target, lock_path=lock)
    assert target.exists()
    assert lock.exists()


def test_current_decision_recovery_lock_is_not_auto_removed(
    tmp_path: Path, e0a_result: dict
) -> None:
    """A pre-existing recovery lock is never age/PID cleared by publish."""

    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    recovery = canonical_document_bytes(
        publication._recovery_record(
            observed_prebuild_target_hash="0" * 64,
            candidate_hash=EXPECTED_CURRENT_FILE_SHA256,
            observed_post_replace_target_hash=EXPECTED_CURRENT_FILE_SHA256,
            failure_stage="prior_failure",
            target_token=CURRENT_DECISION_TARGET_TOKEN,
        )
    )
    lock.write_bytes(recovery)
    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_LOCKED):
        publish_current_decision(e0a_result, target=target, lock_path=lock)
    assert lock.read_bytes() == recovery
