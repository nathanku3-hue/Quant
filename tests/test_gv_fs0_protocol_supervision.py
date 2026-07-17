from __future__ import annotations

from itertools import permutations
import os
from pathlib import Path

import pytest

from gv_fs0.protocol.canonical import canonical_document_bytes, domain_hash
from gv_fs0.protocol.definitions import verifier_result_hash
from gv_fs0.protocol.supervision import (
    CONTROLLER_CODE_RANKS,
    EXECUTION_DEADLINE_SECONDS,
    SHUTDOWN_OBSERVATION_SECONDS,
    STDERR_OBSERVATION_CAP,
    STDERR_VALIDITY_LIMIT,
    STDOUT_OBSERVATION_CAP,
    STDOUT_VALIDITY_LIMIT,
    AttemptComparison,
    build_minimal_environment,
    build_verifier_command,
    classify_completed_streams,
    compare_verifier_attempts,
    observe_stream,
    select_controller_code,
    select_first_hard_boundary,
    validate_attempts_and_retained_results,
)


def _result(status: str, payload: dict[str, object] | None, payload_hash: str | None, codes: list[str]) -> dict[str, object]:
    return {
        "schema_version": "GV_FS0_VERIFIER_RESULT_V1",
        "protocol_binding": {"protocol_id": "GV_FS0_PROTOCOL_V1", "protocol_version": "V1"},
        "fixture_binding": {"fixture_id": "FIXTURE:001", "fixture_hash": "1" * 64},
        "decision_binding": {"decision_id": "DECISION:001", "decision_hash": "2" * 64},
        "verifier_input_hash": "3" * 64,
        "verifier_status": status,
        "reconstructed_economic_payload": payload,
        "reconstructed_economic_payload_hash": payload_hash,
        "failure_codes": codes,
    }


def _retained(*results: dict[str, object]) -> list[dict[str, object]]:
    records = [{"verifier_result_hash": verifier_result_hash(result), "verifier_result": result} for result in results]
    return sorted(records, key=lambda entry: str(entry["verifier_result_hash"]))


def _result_attempt(ordinal: int, result: dict[str, object]) -> dict[str, object]:
    return {
        "ordinal": ordinal,
        "outcome": "RESULT",
        "verifier_result_hash": verifier_result_hash(result),
        "controller_failure_code": None,
    }


def _infrastructure_attempt(ordinal: int, code: str = "VERIFIER_TIMEOUT") -> dict[str, object]:
    return {
        "ordinal": ordinal,
        "outcome": "INFRASTRUCTURE_FAILURE",
        "verifier_result_hash": None,
        "controller_failure_code": code,
    }


def test_exact_supervision_constants() -> None:
    assert EXECUTION_DEADLINE_SECONDS == 30.000
    assert SHUTDOWN_OBSERVATION_SECONDS == 2.000
    assert STDOUT_VALIDITY_LIMIT == 1_048_576
    assert STDERR_VALIDITY_LIMIT == 65_536
    assert STDOUT_OBSERVATION_CAP == 1_048_577
    assert STDERR_OBSERVATION_CAP == 65_537


def test_exact_isolated_invocation_requires_absolute_paths(tmp_path: Path) -> None:
    command = build_verifier_command(
        Path("C:/Python/python.exe") if os.name == "nt" else tmp_path / "python.exe",
        tmp_path / "verifier.py",
        tmp_path / "input.json",
    )
    assert command[1:4] == ("-I", "-X", "utf8")
    assert command[-2] == "--input"
    with pytest.raises(ValueError):
        build_verifier_command(Path("python"), tmp_path / "verifier.py", tmp_path / "input.json")


def test_platform_environment_is_allowlisted(tmp_path: Path) -> None:
    posix = build_minimal_environment("linux", {"SECRET": "no"}, tmp_path)
    assert posix == {"HOME": str(tmp_path), "TMPDIR": str(tmp_path), "TZ": "UTC", "LC_ALL": "C", "LANG": "C"}
    inherited = {"SystemRoot": "C:/Windows", "WINDIR": "C:/Windows", "COMSPEC": "cmd.exe", "PATHEXT": ".EXE", "SECRET": "no"}
    windows = build_minimal_environment("windows", inherited, tmp_path, minimal_path="C:/Python")
    assert set(windows) == {"SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TZ", "PATH"}
    assert "SECRET" not in windows


def test_simultaneous_boundary_precedence_and_termination_freeze() -> None:
    assert select_first_hard_boundary(timeout_observed_at=30.0, output_limit_observed_at=30.0) == "VERIFIER_TIMEOUT"
    assert select_first_hard_boundary(timeout_observed_at=30.0, output_limit_observed_at=29.0) == "VERIFIER_OUTPUT_LIMIT_EXCEEDED"
    assert select_first_hard_boundary(
        timeout_observed_at=30.0,
        output_limit_observed_at=29.0,
        termination_requested_at=29.0,
    ) == "VERIFIER_OUTPUT_LIMIT_EXCEEDED"
    assert select_first_hard_boundary(
        timeout_observed_at=30.0,
        output_limit_observed_at=None,
        termination_requested_at=29.0,
    ) is None


def test_reader_scheduling_cannot_change_controller_code() -> None:
    predicates = ["VERIFIER_RESULT_BINDING_INVALID", "VERIFIER_TIMEOUT", "VERIFIER_STDERR_NONEMPTY"]
    outcomes = {select_controller_code(order) for order in permutations(predicates)}
    assert outcomes == {"VERIFIER_TIMEOUT"}
    assert select_controller_code(CONTROLLER_CODE_RANKS) == "VERIFIER_SUPERVISION_INCOMPLETE"
    with pytest.raises(ValueError):
        select_controller_code(["UNKNOWN"])


def test_byte_limit_is_enforced_before_utf8_decode() -> None:
    stdout = observe_stream(b"\xff" * STDOUT_OBSERVATION_CAP, STDOUT_OBSERVATION_CAP, STDOUT_VALIDITY_LIMIT, STDOUT_OBSERVATION_CAP, eof=False)
    stderr = observe_stream(b"", 0, STDERR_VALIDITY_LIMIT, STDERR_OBSERVATION_CAP, eof=True)
    assert classify_completed_streams(stdout, stderr) == ("VERIFIER_OUTPUT_LIMIT_EXCEEDED",)


def test_completed_stream_predicates_are_deterministic() -> None:
    valid = canonical_document_bytes({"status": "ok"})
    stdout = observe_stream(valid, len(valid), STDOUT_VALIDITY_LIMIT, STDOUT_OBSERVATION_CAP, eof=True)
    stderr = observe_stream(b"diagnostic", 10, STDERR_VALIDITY_LIMIT, STDERR_OBSERVATION_CAP, eof=True)
    assert classify_completed_streams(stdout, stderr) == ("VERIFIER_STDERR_NONEMPTY",)

    invalid_utf8 = observe_stream(b"\xff\n", 2, STDOUT_VALIDITY_LIMIT, STDOUT_OBSERVATION_CAP, eof=True)
    assert classify_completed_streams(invalid_utf8, observe_stream(b"", 0, STDERR_VALIDITY_LIMIT, STDERR_OBSERVATION_CAP, eof=True)) == (
        "VERIFIER_OUTPUT_INVALID_UTF8",
    )

    noncanonical = observe_stream(b'{ "a":1}\n', 9, STDOUT_VALIDITY_LIMIT, STDOUT_OBSERVATION_CAP, eof=True)
    assert classify_completed_streams(noncanonical, observe_stream(b"", 0, STDERR_VALIDITY_LIMIT, STDERR_OBSERVATION_CAP, eof=True)) == (
        "VERIFIER_OUTPUT_NOT_CANONICAL",
    )


def test_identical_attempts_reference_one_retained_result() -> None:
    payload = {"x": 1}
    payload_hash = domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", payload)
    result = _result("RECONSTRUCTED", payload, payload_hash, [])
    attempts = [_result_attempt(1, result), _result_attempt(2, result)]
    retained = _retained(result)
    validate_attempts_and_retained_results(attempts, retained)
    comparison = compare_verifier_attempts(
        attempts,
        retained,
        primary_payload_hash=payload_hash,
        primary_payload_bytes=canonical_document_bytes(payload),
    )
    assert comparison == AttemptComparison("TRUE", "TRUE")


def test_differing_valid_attempts_retain_two_results_and_fail_comparison() -> None:
    first_payload = {"x": 1}
    second_payload = {"x": 2}
    first = _result("RECONSTRUCTED", first_payload, domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", first_payload), [])
    second = _result("RECONSTRUCTED", second_payload, domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", second_payload), [])
    attempts = [_result_attempt(1, first), _result_attempt(2, second)]
    retained = _retained(first, second)
    assert len(retained) == 2
    assert compare_verifier_attempts(
        attempts,
        retained,
        primary_payload_hash=domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", first_payload),
        primary_payload_bytes=canonical_document_bytes(first_payload),
    ) == AttemptComparison("FALSE", "FALSE")


def test_one_result_plus_infrastructure_failure_is_unknown_unless_mismatch() -> None:
    payload = {"x": 1}
    payload_hash = domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", payload)
    result = _result("RECONSTRUCTED", payload, payload_hash, [])
    attempts = [_result_attempt(1, result), _infrastructure_attempt(2)]
    retained = _retained(result)
    assert compare_verifier_attempts(
        attempts,
        retained,
        primary_payload_hash=payload_hash,
        primary_payload_bytes=canonical_document_bytes(payload),
    ) == AttemptComparison("UNKNOWN", "UNKNOWN")
    assert compare_verifier_attempts(
        attempts,
        retained,
        primary_payload_hash="f" * 64,
        primary_payload_bytes=canonical_document_bytes(payload),
    ) == AttemptComparison("FALSE", "FALSE")


def test_two_infrastructure_failures_are_unknown() -> None:
    attempts = [_infrastructure_attempt(1), _infrastructure_attempt(2, "VERIFIER_PROCESS_FAILED")]
    assert compare_verifier_attempts(
        attempts,
        [],
        primary_payload_hash="f" * 64,
        primary_payload_bytes=None,
    ) == AttemptComparison("UNKNOWN", "UNKNOWN")


def test_identical_rejected_results_are_false_unknown() -> None:
    result = _result("REJECTED", None, None, ["VERIFIER_REJECTED"])
    attempts = [_result_attempt(1, result), _result_attempt(2, result)]
    retained = _retained(result)
    assert compare_verifier_attempts(
        attempts,
        retained,
        primary_payload_hash="f" * 64,
        primary_payload_bytes=None,
    ) == AttemptComparison("FALSE", "UNKNOWN")


def test_retained_result_integrity_failures_block() -> None:
    result = _result("REJECTED", None, None, ["VERIFIER_REJECTED"])
    result_hash = verifier_result_hash(result)
    attempts = [_result_attempt(1, result), _result_attempt(2, result)]
    retained = _retained(result)

    with pytest.raises(ValueError, match="duplicate retained"):
        validate_attempts_and_retained_results(attempts, retained + retained)
    with pytest.raises(ValueError, match="forged"):
        validate_attempts_and_retained_results(
            attempts,
            [{"verifier_result_hash": "0" * 64, "verifier_result": result}],
        )
    with pytest.raises(ValueError, match="no retained"):
        validate_attempts_and_retained_results(attempts, [])
    with pytest.raises(ValueError, match="unreferenced"):
        other = _result("REJECTED", None, None, ["DECISION_AUTHORITY_INVALID"])
        extra = _retained(result, other)
        validate_attempts_and_retained_results(attempts, extra)
    assert result_hash == retained[0]["verifier_result_hash"]
