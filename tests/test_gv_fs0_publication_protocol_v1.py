from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest


class PublicationFailure(RuntimeError):
    def __init__(self, code: str, stage: str) -> None:
        super().__init__(code)
        self.code = code
        self.stage = stage


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _publish_test_harness(
    target: Path,
    lock: Path,
    candidate: bytes,
    observed_prebuild_hash: str,
    *,
    fail_stage: str | None = None,
) -> str:
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise PublicationFailure("PUBLICATION_LOCKED", "lock") from exc
    os.close(descriptor)
    temp = target.with_name(target.name + ".candidate")
    replaced = False
    try:
        current = target.read_bytes() if target.exists() else None
        current_hash = _sha(current) if current is not None else "ABSENT"
        if current == candidate:
            return "IDEMPOTENT"
        if current_hash != observed_prebuild_hash:
            raise PublicationFailure("PUBLICATION_TARGET_CHANGED", "compare_under_lock")
        if fail_stage == "validation":
            raise PublicationFailure("VALIDATION_FAILED", "validation")
        temp.write_bytes(candidate)
        if fail_stage == "temp_write":
            raise PublicationFailure("TEMP_WRITE_FAILED", "temp_write")
        with temp.open("rb+") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        if fail_stage == "pre_replace":
            raise PublicationFailure("PRE_REPLACE_FAILED", "pre_replace")
        os.replace(temp, target)
        replaced = True
        if fail_stage == "post_replace":
            raise PublicationFailure(
                "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
                "post_replace_verification",
            )
        observed = target.read_bytes()
        if observed != candidate or _sha(observed) != _sha(candidate):
            raise PublicationFailure(
                "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
                "post_replace_verification",
            )
        return "REPLACED"
    except PublicationFailure:
        if replaced:
            recovery = (
                '{"failure_code":"PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",'
                '"record_version":"GV-FS0-PUBLICATION-RECOVERY-V1",'
                '"state":"RECOVERY_REQUIRED","target_token":"GV_FS0_CERTIFIED_BUNDLE"}\n'
            ).encode("utf-8")
            lock.write_bytes(recovery)
        raise
    finally:
        if temp.exists():
            temp.unlink()
        if lock.exists() and not replaced:
            lock.unlink()
        elif lock.exists() and fail_stage != "post_replace":
            lock.unlink()


def test_all_pre_replace_failures_preserve_prior_target(tmp_path: Path) -> None:
    target = tmp_path / "bundle.json"
    lock = tmp_path / ".bundle.lock"
    prior = b'{"bundle":"prior"}\n'
    target.write_bytes(prior)
    for stage in ["validation", "temp_write", "pre_replace"]:
        with pytest.raises(PublicationFailure):
            _publish_test_harness(target, lock, b'{"bundle":"candidate"}\n', _sha(prior), fail_stage=stage)
        assert target.read_bytes() == prior
        assert not lock.exists()


def test_post_replace_failure_makes_no_prior_preservation_claim(tmp_path: Path) -> None:
    target = tmp_path / "bundle.json"
    lock = tmp_path / ".bundle.lock"
    prior = b'{"bundle":"prior"}\n'
    candidate = b'{"bundle":"candidate"}\n'
    target.write_bytes(prior)
    with pytest.raises(PublicationFailure, match="PUBLICATION_POST_REPLACE_VERIFICATION_FAILED"):
        _publish_test_harness(target, lock, candidate, _sha(prior), fail_stage="post_replace")
    assert target.read_bytes() == candidate
    assert target.read_bytes() != prior
    assert lock.exists()
    assert b'"state":"RECOVERY_REQUIRED"' in lock.read_bytes()


def test_recovery_lock_is_durable_and_not_auto_deleted(tmp_path: Path) -> None:
    target = tmp_path / "bundle.json"
    lock = tmp_path / ".bundle.lock"
    target.write_bytes(b'{"bundle":"prior"}\n')
    lock.write_bytes(b'{"state":"RECOVERY_REQUIRED"}\n')
    with pytest.raises(PublicationFailure, match="PUBLICATION_LOCKED"):
        _publish_test_harness(target, lock, b'{"bundle":"new"}\n', _sha(target.read_bytes()))
    assert lock.exists()


def test_identical_candidate_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "bundle.json"
    lock = tmp_path / ".bundle.lock"
    candidate = b'{"bundle":"same"}\n'
    target.write_bytes(candidate)
    before = target.stat().st_mtime_ns
    assert _publish_test_harness(target, lock, candidate, _sha(candidate)) == "IDEMPOTENT"
    assert target.read_bytes() == candidate
    assert target.stat().st_mtime_ns == before


def test_changed_target_under_lock_cannot_be_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "bundle.json"
    lock = tmp_path / ".bundle.lock"
    observed = b'{"bundle":"observed"}\n'
    concurrent = b'{"bundle":"concurrent"}\n'
    target.write_bytes(concurrent)
    with pytest.raises(PublicationFailure, match="PUBLICATION_TARGET_CHANGED"):
        _publish_test_harness(target, lock, b'{"bundle":"candidate"}\n', _sha(observed))
    assert target.read_bytes() == concurrent


def test_differing_concurrent_candidate_is_rejected_by_exclusive_lock(tmp_path: Path) -> None:
    target = tmp_path / "bundle.json"
    lock = tmp_path / ".bundle.lock"
    target.write_bytes(b'{"bundle":"prior"}\n')
    lock.write_bytes(b"active")
    with pytest.raises(PublicationFailure, match="PUBLICATION_LOCKED"):
        _publish_test_harness(target, lock, b'{"bundle":"other"}\n', _sha(target.read_bytes()))
    assert target.read_bytes() == b'{"bundle":"prior"}\n'
