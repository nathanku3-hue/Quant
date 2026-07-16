"""Pure publication-state decisions for GV-FS0 Protocol V1.

No function in this module opens, writes, replaces, fsyncs, or deletes a file.
It freezes only compare-under-lock, recovery, and lock-release semantics so the
later publication implementation has one mechanically tested contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PublicationDecision = Literal[
    "IDEMPOTENT_SUCCESS",
    "PUBLICATION_TARGET_CHANGED",
    "REPLACE_AUTHORIZED",
]


@dataclass(frozen=True)
class PostReplaceFailure:
    failure_code: str
    prior_target_preservation_claimed: bool
    automatic_rollback_allowed: bool
    recovery_record_required: bool
    automatic_publication_blocked: bool


def compare_under_lock(
    *,
    observed_prebuild_target_hash: str,
    current_target_hash: str,
    candidate_bytes: bytes,
    current_target_bytes: bytes | None,
    current_target_valid: bool,
) -> PublicationDecision:
    """Apply the V1 compare-under-lock decision in normative order."""

    if current_target_valid and current_target_bytes is not None and candidate_bytes == current_target_bytes:
        return "IDEMPOTENT_SUCCESS"
    if current_target_hash != observed_prebuild_target_hash:
        return "PUBLICATION_TARGET_CHANGED"
    return "REPLACE_AUTHORIZED"


def post_replace_verification_failure() -> PostReplaceFailure:
    """Return the frozen fail-safe claims after a replace cannot be verified."""

    return PostReplaceFailure(
        failure_code="PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
        prior_target_preservation_claimed=False,
        automatic_rollback_allowed=False,
        recovery_record_required=True,
        automatic_publication_blocked=True,
    )


def build_recovery_record(
    *,
    observed_prebuild_target_hash: str,
    candidate_hash: str,
    observed_post_replace_target_hash: str,
    failure_code: str,
    failure_stage: str,
) -> dict[str, str]:
    """Build canonical durable-recovery content without writing it."""

    if failure_code not in {
        "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
        "PUBLICATION_RECOVERY_RECORD_FAILED",
    }:
        raise ValueError("failure code cannot create a V1 recovery record")
    return {
        "candidate_hash": candidate_hash,
        "failure_code": failure_code,
        "failure_stage": failure_stage,
        "observed_post_replace_target_hash": observed_post_replace_target_hash,
        "observed_prebuild_target_hash": observed_prebuild_target_hash,
        "record_version": "GV-FS0-PUBLICATION-RECOVERY-V1",
        "state": "RECOVERY_REQUIRED",
        "target_token": "GV_FS0_CERTIFIED_BUNDLE",
    }


def automatic_lock_release_allowed(
    *,
    replace_occurred: bool,
    target_verified_unchanged: bool,
    post_replace_verification_succeeded: bool,
    candidate_was_identical: bool,
    recovery_required: bool,
) -> bool:
    """Return true only for the three normal-release cases."""

    if recovery_required:
        return False
    if candidate_was_identical:
        return True
    if replace_occurred:
        return post_replace_verification_succeeded
    return target_verified_unchanged
