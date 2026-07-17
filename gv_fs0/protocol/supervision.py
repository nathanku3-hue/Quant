"""Pure verifier-supervision primitives for GV-FS0 Protocol V1.

This module freezes controller decisions without launching a verifier or
executing certification over any fixture. Process orchestration remains blocked
until the protocol-freeze commit passes a clean audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import ProtocolValueError, canonical_document_bytes, load_canonical_document
from .definitions import verifier_result_hash

EXECUTION_DEADLINE_SECONDS = 30.000
SHUTDOWN_OBSERVATION_SECONDS = 2.000
STDOUT_VALIDITY_LIMIT = 1_048_576
STDERR_VALIDITY_LIMIT = 65_536
STDOUT_OBSERVATION_CAP = 1_048_577
STDERR_OBSERVATION_CAP = 65_537

CONTROLLER_CODE_RANKS = {
    "VERIFIER_SUPERVISION_INCOMPLETE": 10,
    "VERIFIER_TIMEOUT": 20,
    "VERIFIER_OUTPUT_LIMIT_EXCEEDED": 30,
    "VERIFIER_PROCESS_FAILED": 40,
    "VERIFIER_STDERR_NONEMPTY": 50,
    "VERIFIER_OUTPUT_INVALID_UTF8": 60,
    "VERIFIER_OUTPUT_NOT_CANONICAL": 70,
    "VERIFIER_OUTPUT_SCHEMA_INVALID": 80,
    "VERIFIER_RESULT_BINDING_INVALID": 90,
}

POSIX_ENVIRONMENT_KEYS = ("HOME", "TMPDIR", "TZ", "LC_ALL", "LANG")
WINDOWS_ENVIRONMENT_KEYS = ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TZ")


@dataclass(frozen=True)
class StreamObservation:
    captured_prefix: bytes
    total_bytes_observed: int
    overflow_observed: bool
    eof_observed: bool

    def __post_init__(self) -> None:
        if self.total_bytes_observed < 0:
            raise ValueError("total_bytes_observed must be non-negative")
        if self.total_bytes_observed < len(self.captured_prefix):
            raise ValueError("observed byte count cannot be smaller than captured prefix")


@dataclass(frozen=True)
class AttemptComparison:
    independent_reconstruction_passed: str
    canonical_hash_reproduced: str


def build_verifier_command(executable: Path, script: Path, input_file: Path) -> tuple[str, ...]:
    """Return the exact frozen isolated invocation."""

    paths = (executable, script, input_file)
    if any(not path.is_absolute() for path in paths):
        raise ValueError("verifier invocation paths must be absolute")
    return (
        str(executable),
        "-I",
        "-X",
        "utf8",
        str(script),
        "--input",
        str(input_file),
    )


def build_minimal_environment(
    platform_name: str,
    inherited: Mapping[str, str],
    isolated_temp: Path,
    *,
    minimal_path: str | None = None,
) -> dict[str, str]:
    """Construct the platform-specific allowlisted verifier environment."""

    if not isolated_temp.is_absolute():
        raise ValueError("isolated temporary directory must be absolute")
    platform_key = platform_name.lower()
    if platform_key in {"posix", "linux", "darwin"}:
        result = {
            "HOME": str(isolated_temp),
            "TMPDIR": str(isolated_temp),
            "TZ": "UTC",
            "LC_ALL": "C",
            "LANG": "C",
        }
    elif platform_key in {"nt", "windows", "win32"}:
        result = {}
        for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT"):
            if key not in inherited:
                raise ValueError(f"required Windows environment value missing: {key}")
            result[key] = inherited[key]
        result.update({"TEMP": str(isolated_temp), "TMP": str(isolated_temp), "TZ": "UTC"})
        if minimal_path is not None:
            result["PATH"] = minimal_path
    else:
        raise ValueError(f"unsupported platform: {platform_name}")
    return result


def select_first_hard_boundary(
    *, timeout_observed_at: float | None,
    output_limit_observed_at: float | None,
    termination_requested_at: float | None = None,
) -> str | None:
    """Select the initiating hard boundary using frozen time and tie rules."""

    candidates: list[tuple[float, int, str]] = []
    if timeout_observed_at is not None:
        candidates.append((timeout_observed_at, 10, "VERIFIER_TIMEOUT"))
    if output_limit_observed_at is not None:
        candidates.append((output_limit_observed_at, 20, "VERIFIER_OUTPUT_LIMIT_EXCEEDED"))
    if termination_requested_at is not None:
        candidates = [candidate for candidate in candidates if candidate[0] <= termination_requested_at]
    if not candidates:
        return None
    return min(candidates)[2]


def select_controller_code(observed_predicates: Iterable[str]) -> str | None:
    """Choose the lowest-ranked stable controller code."""

    unique = set(observed_predicates)
    unknown = unique.difference(CONTROLLER_CODE_RANKS)
    if unknown:
        raise ValueError(f"unknown controller predicates: {sorted(unknown)}")
    if not unique:
        return None
    return min(unique, key=CONTROLLER_CODE_RANKS.__getitem__)


def observe_stream(prefix: bytes, total_bytes: int, validity_limit: int, observation_cap: int, *, eof: bool) -> StreamObservation:
    """Validate a bounded stream observation without decoding."""

    if validity_limit < 0 or observation_cap != validity_limit + 1:
        raise ValueError("observation cap must equal validity limit plus one")
    retained = prefix[:observation_cap]
    bounded_total = min(total_bytes, observation_cap)
    return StreamObservation(
        captured_prefix=retained,
        total_bytes_observed=bounded_total,
        overflow_observed=total_bytes >= observation_cap,
        eof_observed=eof,
    )


def classify_completed_streams(stdout: StreamObservation, stderr: StreamObservation) -> tuple[str, ...]:
    """Apply byte, stderr, UTF-8, and canonical-document predicates in order."""

    predicates: list[str] = []
    if stdout.overflow_observed or stderr.overflow_observed:
        predicates.append("VERIFIER_OUTPUT_LIMIT_EXCEEDED")
        return tuple(predicates)
    if stderr.total_bytes_observed:
        predicates.append("VERIFIER_STDERR_NONEMPTY")
    try:
        stdout.captured_prefix.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        predicates.append("VERIFIER_OUTPUT_INVALID_UTF8")
        return tuple(predicates)
    try:
        load_canonical_document(stdout.captured_prefix)
    except ProtocolValueError:
        predicates.append("VERIFIER_OUTPUT_NOT_CANONICAL")
    return tuple(predicates)


def validate_attempts_and_retained_results(
    attempts: list[dict[str, Any]],
    retained_results: list[dict[str, Any]],
) -> None:
    """Enforce exact attempts and unique hash-addressed retained results."""

    if len(attempts) != 2 or [attempt.get("ordinal") for attempt in attempts] != [1, 2]:
        raise ValueError("exact verifier attempt ordinals 1 then 2 are required")
    retained_hashes = [entry.get("verifier_result_hash") for entry in retained_results]
    if retained_hashes != sorted(retained_hashes):
        raise ValueError("retained verifier results must be sorted by hash")
    if len(retained_hashes) != len(set(retained_hashes)):
        raise ValueError("duplicate retained verifier-result hash")
    retained_map: dict[str, dict[str, Any]] = {}
    for entry in retained_results:
        result_hash = entry.get("verifier_result_hash")
        result = entry.get("verifier_result")
        if not isinstance(result_hash, str) or not isinstance(result, dict):
            raise ValueError("retained verifier-result entry is malformed")
        if verifier_result_hash(result) != result_hash:
            raise ValueError("forged retained verifier-result hash")
        retained_map[result_hash] = result
    referenced: set[str] = set()
    for attempt in attempts:
        outcome = attempt.get("outcome")
        result_hash = attempt.get("verifier_result_hash")
        controller_code = attempt.get("controller_failure_code")
        if outcome == "RESULT":
            if not isinstance(result_hash, str) or controller_code is not None:
                raise ValueError("RESULT attempt binding is invalid")
            if result_hash not in retained_map:
                raise ValueError("RESULT attempt has no retained verifier result")
            referenced.add(result_hash)
        elif outcome == "INFRASTRUCTURE_FAILURE":
            if result_hash is not None or controller_code not in CONTROLLER_CODE_RANKS:
                raise ValueError("INFRASTRUCTURE_FAILURE attempt binding is invalid")
        else:
            raise ValueError("unknown verifier-attempt outcome")
    if referenced != set(retained_map):
        raise ValueError("unreferenced retained verifier result")


def _result_for_attempt(attempt: dict[str, Any], retained_map: Mapping[str, dict[str, Any]]) -> dict[str, Any] | None:
    if attempt["outcome"] == "INFRASTRUCTURE_FAILURE":
        return None
    return retained_map[attempt["verifier_result_hash"]]


def compare_verifier_attempts(
    attempts: list[dict[str, Any]],
    retained_results: list[dict[str, Any]],
    *,
    primary_payload_hash: str,
    primary_payload_bytes: bytes | None,
) -> AttemptComparison:
    """Apply the frozen TRUE/FALSE/UNKNOWN comparison semantics."""

    validate_attempts_and_retained_results(attempts, retained_results)
    retained_map = {entry["verifier_result_hash"]: entry["verifier_result"] for entry in retained_results}
    results = [_result_for_attempt(attempt, retained_map) for attempt in attempts]
    available = [result for result in results if result is not None]
    if not available:
        return AttemptComparison("UNKNOWN", "UNKNOWN")

    def hash_outcome(result: dict[str, Any]) -> str:
        payload_hash = result.get("reconstructed_economic_payload_hash")
        payload = result.get("reconstructed_economic_payload")
        if payload_hash is None or payload is None:
            return "UNKNOWN"
        if payload_hash != primary_payload_hash:
            return "FALSE"
        if primary_payload_bytes is not None and canonical_document_bytes(payload) != primary_payload_bytes:
            return "FALSE"
        return "TRUE"

    hash_outcomes = [hash_outcome(result) for result in available]
    aggregate_hash = "FALSE" if "FALSE" in hash_outcomes else ("UNKNOWN" if "UNKNOWN" in hash_outcomes else "TRUE")

    if len(available) == 1:
        if available[0].get("verifier_status") == "REJECTED":
            return AttemptComparison("FALSE", aggregate_hash)
        independent = "FALSE" if aggregate_hash == "FALSE" else "UNKNOWN"
        return AttemptComparison(independent, aggregate_hash if aggregate_hash == "FALSE" else "UNKNOWN")

    first, second = available
    identical = canonical_document_bytes(first) == canonical_document_bytes(second)
    first_status = first.get("verifier_status")
    second_status = second.get("verifier_status")
    if first_status == second_status == "RECONSTRUCTED" and identical:
        independent = "TRUE" if aggregate_hash == "TRUE" else "FALSE"
        return AttemptComparison(independent, aggregate_hash)
    if first_status == second_status == "REJECTED" and identical:
        return AttemptComparison("FALSE", aggregate_hash if aggregate_hash == "FALSE" else "UNKNOWN")
    if first_status == second_status == "RECONSTRUCTED":
        return AttemptComparison("FALSE", "FALSE")
    return AttemptComparison("FALSE", aggregate_hash if aggregate_hash == "FALSE" else "UNKNOWN")
