"""GV-FS0 deterministic bundle assembly and atomic publication.

Publication follows contract section 15 exactly: observe before construction,
acquire a non-waiting exclusive lock, compare under lock, write+fsync a unique
temporary file, atomically replace, verify exact bytes, and retain a durable
recovery-required lock after any post-replace verification failure.

The dual-role permanent bundle and the single-current-decision artifact share
the same atomic publication helpers with distinct targets and lock files.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import Any

from core.gv_fs0_bundle import (
    certified_bundle_bytes,
    build_certified_bundle,
    parse_certified_bundle_bytes,
)
from core.gv_fs0_canonical import canonical_document_bytes, sha256_bytes
from core.gv_fs0_certify import (
    build_no_position_certified_result,
    build_open_certified_result,
)
from core.gv_fs0_current_decision import (
    GvFs0CurrentDecisionError,
    certified_decision_result_bytes as _certified_decision_result_bytes,
    parse_current_decision_bytes as _parse_current_decision_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "data" / "gv_fs0" / "gv_fs0_certified_bundle.json"
DEFAULT_LOCK = ROOT / "data" / "gv_fs0" / ".gv_fs0_certified_bundle.lock"
DEFAULT_CURRENT_DECISION_TARGET = ROOT / "data" / "gv_fs0" / "gv_fs0_current_decision.json"
DEFAULT_CURRENT_DECISION_LOCK = (
    ROOT / "data" / "gv_fs0" / ".gv_fs0_current_decision.lock"
)
ABSENT = "ABSENT"

PUBLICATION_LOCKED = "PUBLICATION_LOCKED"
PUBLICATION_TARGET_CHANGED = "PUBLICATION_TARGET_CHANGED"
PUBLICATION_POST_REPLACE_VERIFICATION_FAILED = (
    "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED"
)
PUBLICATION_RECOVERY_RECORD_FAILED = "PUBLICATION_RECOVERY_RECORD_FAILED"

BUNDLE_TARGET_TOKEN = "GV_FS0_CERTIFIED_BUNDLE"
CURRENT_DECISION_TARGET_TOKEN = "GV_FS0_CURRENT_DECISION"


class GvFs0PublicationError(RuntimeError):
    """Stable registered publication failure."""

    def __init__(self, code: str, stage: str) -> None:
        super().__init__(code)
        self.code = code
        self.stage = stage


@dataclass(frozen=True)
class PublicationResult:
    status: str
    target_path: str
    target_file_sha256: str
    bundle_hash: str
    bundle_id: str


@dataclass(frozen=True)
class CurrentDecisionPublicationResult:
    status: str
    target_path: str
    target_file_sha256: str
    certified_decision_result_hash: str
    certified_decision_result_id: str


BundleBuilder = Callable[[], Mapping[str, Any]]
ParsePublished = Callable[[bytes], Mapping[str, Any]]


def build_default_certified_bundle() -> dict[str, Any]:
    """Build OPEN then NO_POSITION through the already-certified shared path."""

    return build_certified_bundle(
        [
            build_open_certified_result(),
            build_no_position_certified_result(),
        ]
    )


def certified_decision_result_bytes(result: Mapping[str, Any]) -> bytes:
    """Canonical bytes for one certified decision result (single-current path)."""

    try:
        return _certified_decision_result_bytes(result)
    except GvFs0CurrentDecisionError as exc:
        raise ValueError(str(exc)) from exc


def parse_current_decision_bytes(raw: bytes) -> dict[str, Any]:
    """Require canonical bytes and return one fully validated certified result.

    Thin publication-facing wrapper over the shared read-only current-decision
    parser; maps identity failures to publication recovery codes.
    """

    try:
        return _parse_current_decision_bytes(raw)
    except GvFs0CurrentDecisionError as exc:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            str(exc),
        ) from exc


def _read_optional(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _target_hash(path: Path) -> str:
    raw = _read_optional(path)
    return ABSENT if raw is None else sha256_bytes(raw)


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory fsync; Windows does not expose a portable handle."""

    flags = getattr(os, "O_RDONLY", 0)
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        return
    finally:
        os.close(descriptor)


def _acquire_lock(lock_path: Path) -> None:
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise GvFs0PublicationError(PUBLICATION_LOCKED, "lock_acquisition") from exc
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(lock_path.parent)


def _release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        return
    _fsync_directory(lock_path.parent)


def _write_candidate_temp(target: Path, candidate: bytes) -> Path:
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temp_path = Path(raw_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise
    return temp_path


def _replace_file(source: Path, target: Path) -> None:
    os.replace(source, target)


def _verify_published_bytes(
    target: Path, candidate: bytes, parse_fn: ParsePublished
) -> str:
    observed = target.read_bytes()
    if observed != candidate:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            "post_replace_exact_bytes",
        )
    expected_sha = sha256_bytes(candidate)
    if sha256_bytes(observed) != expected_sha:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            "post_replace_sha256",
        )
    parse_fn(observed)
    return expected_sha


def _verify_published_target(target: Path, candidate: bytes) -> str:
    """Dual-bundle verify hook (monkeypatched by publication tests)."""

    return _verify_published_bytes(target, candidate, parse_certified_bundle_bytes)


def _recovery_record(
    *,
    observed_prebuild_target_hash: str,
    candidate_hash: str,
    observed_post_replace_target_hash: str,
    failure_stage: str,
    target_token: str = BUNDLE_TARGET_TOKEN,
) -> dict[str, str]:
    return {
        "record_version": "GV-FS0-PUBLICATION-RECOVERY-V1",
        "state": "RECOVERY_REQUIRED",
        "target_token": target_token,
        "observed_prebuild_target_hash": observed_prebuild_target_hash,
        "candidate_hash": candidate_hash,
        "observed_post_replace_target_hash": observed_post_replace_target_hash,
        "failure_code": PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
        "failure_stage": failure_stage,
    }


def _write_recovery_record(lock_path: Path, record: Mapping[str, str]) -> None:
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{lock_path.name}.", suffix=".tmp", dir=lock_path.parent
    )
    temp_path = Path(raw_name)
    try:
        payload = canonical_document_bytes(dict(record))
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, lock_path)
        _fsync_directory(lock_path.parent)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _convert_lock_to_recovery(
    *,
    lock_path: Path,
    target: Path,
    observed_prebuild_target_hash: str,
    candidate_hash: str,
    failure_stage: str,
    target_token: str,
) -> None:
    observed_post = _target_hash(target)
    record = _recovery_record(
        observed_prebuild_target_hash=observed_prebuild_target_hash,
        candidate_hash=candidate_hash,
        observed_post_replace_target_hash=observed_post,
        failure_stage=failure_stage,
        target_token=target_token,
    )
    try:
        _write_recovery_record(lock_path, record)
    except Exception as exc:
        raise GvFs0PublicationError(
            PUBLICATION_RECOVERY_RECORD_FAILED,
            "recovery_record",
        ) from exc


def _publish_canonical_bytes(
    *,
    target: Path,
    lock_path: Path,
    candidate: bytes,
    parse_fn: ParsePublished,
    target_token: str,
    observed_prebuild_hash: str,
) -> tuple[str, str]:
    """Section-15 atomic publish under lock. Returns (status, verified_sha256).

    Caller must observe ``observed_prebuild_hash`` before constructing
    ``candidate`` so concurrent target changes during build are fail-closed.
    """

    target = Path(target)
    lock_path = Path(lock_path)
    if lock_path.parent != target.parent:
        raise ValueError("LOCK_AND_TARGET_DIRECTORY_MUST_MATCH")
    target.parent.mkdir(parents=True, exist_ok=True)

    candidate_hash = sha256_bytes(candidate)

    _acquire_lock(lock_path)
    temp_path: Path | None = None
    replaced = False
    normal_release = False
    try:
        current = _read_optional(target)
        current_hash = ABSENT if current is None else sha256_bytes(current)
        if current == candidate:
            parse_fn(current)
            normal_release = True
            return "IDEMPOTENT", candidate_hash
        if current_hash != observed_prebuild_hash:
            normal_release = True
            raise GvFs0PublicationError(
                PUBLICATION_TARGET_CHANGED,
                "compare_under_lock",
            )

        parse_fn(candidate)
        temp_path = _write_candidate_temp(target, candidate)
        _replace_file(temp_path, target)
        temp_path = None
        replaced = True
        _fsync_directory(target.parent)
        # Preserve dual-bundle test monkeypatch on `_verify_published_target`.
        if parse_fn is parse_certified_bundle_bytes:
            verified_hash = _verify_published_target(target, candidate)
        else:
            verified_hash = _verify_published_bytes(target, candidate, parse_fn)
        normal_release = True
        return "REPLACED", verified_hash
    except GvFs0PublicationError as exc:
        if replaced:
            try:
                _convert_lock_to_recovery(
                    lock_path=lock_path,
                    target=target,
                    observed_prebuild_target_hash=observed_prebuild_hash,
                    candidate_hash=candidate_hash,
                    failure_stage=exc.stage,
                    target_token=target_token,
                )
            except GvFs0PublicationError:
                raise
            raise GvFs0PublicationError(
                PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
                exc.stage,
            ) from exc
        raise
    except Exception as exc:
        if replaced:
            try:
                _convert_lock_to_recovery(
                    lock_path=lock_path,
                    target=target,
                    observed_prebuild_target_hash=observed_prebuild_hash,
                    candidate_hash=candidate_hash,
                    failure_stage="post_replace_unexpected",
                    target_token=target_token,
                )
            except GvFs0PublicationError:
                raise
            raise GvFs0PublicationError(
                PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
                "post_replace_unexpected",
            ) from exc
        normal_release = True
        raise
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
        if normal_release:
            _release_lock(lock_path)


def publish_default_certified_bundle(
    *,
    target: Path = DEFAULT_TARGET,
    lock_path: Path = DEFAULT_LOCK,
    bundle_builder: BundleBuilder = build_default_certified_bundle,
) -> PublicationResult:
    """Build and publish the permanent complete bundle with fail-closed recovery."""

    target = Path(target)
    lock_path = Path(lock_path)
    if lock_path.parent != target.parent:
        raise ValueError("LOCK_AND_TARGET_DIRECTORY_MUST_MATCH")
    target.parent.mkdir(parents=True, exist_ok=True)

    # Section 15: observe before construction.
    observed_prebuild_hash = _target_hash(target)
    bundle = dict(bundle_builder())
    candidate = certified_bundle_bytes(bundle)
    status, verified_hash = _publish_canonical_bytes(
        target=target,
        lock_path=lock_path,
        candidate=candidate,
        parse_fn=parse_certified_bundle_bytes,
        target_token=BUNDLE_TARGET_TOKEN,
        observed_prebuild_hash=observed_prebuild_hash,
    )
    return PublicationResult(
        status=status,
        target_path=str(target),
        target_file_sha256=verified_hash,
        bundle_hash=bundle["bundle_hash"],
        bundle_id=bundle["bundle_id"],
    )


def publish_current_decision(
    result: Mapping[str, Any],
    *,
    target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    lock_path: Path = DEFAULT_CURRENT_DECISION_LOCK,
) -> CurrentDecisionPublicationResult:
    """Atomically publish one certified current decision (single-active product path)."""

    target = Path(target)
    lock_path = Path(lock_path)
    if lock_path.parent != target.parent:
        raise ValueError("LOCK_AND_TARGET_DIRECTORY_MUST_MATCH")
    target.parent.mkdir(parents=True, exist_ok=True)

    # Section 15: observe before construction/serialization.
    observed_prebuild_hash = _target_hash(target)
    candidate = certified_decision_result_bytes(result)
    status, verified_hash = _publish_canonical_bytes(
        target=target,
        lock_path=lock_path,
        candidate=candidate,
        parse_fn=parse_current_decision_bytes,
        target_token=CURRENT_DECISION_TARGET_TOKEN,
        observed_prebuild_hash=observed_prebuild_hash,
    )
    return CurrentDecisionPublicationResult(
        status=status,
        target_path=str(target),
        target_file_sha256=verified_hash,
        certified_decision_result_hash=str(result["certified_decision_result_hash"]),
        certified_decision_result_id=str(result["certified_decision_result_id"]),
    )


__all__ = [
    "ABSENT",
    "BUNDLE_TARGET_TOKEN",
    "CURRENT_DECISION_TARGET_TOKEN",
    "DEFAULT_CURRENT_DECISION_LOCK",
    "DEFAULT_CURRENT_DECISION_TARGET",
    "DEFAULT_LOCK",
    "DEFAULT_TARGET",
    "CurrentDecisionPublicationResult",
    "GvFs0PublicationError",
    "PUBLICATION_LOCKED",
    "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
    "PUBLICATION_RECOVERY_RECORD_FAILED",
    "PUBLICATION_TARGET_CHANGED",
    "PublicationResult",
    "build_default_certified_bundle",
    "certified_decision_result_bytes",
    "parse_current_decision_bytes",
    "publish_current_decision",
    "publish_default_certified_bundle",
]
