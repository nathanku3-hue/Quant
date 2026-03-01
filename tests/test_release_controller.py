from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

import scripts.release_controller as rc
from core.release_metadata import ReleaseMetadata, ReleaseRecord, build_release_cache_fingerprint


def _release_ref(tag: str, digest_char: str) -> str:
    return f"ghcr.io/terminal-zero/quant:{tag}@sha256:{digest_char * 64}"


def _now_factory(*timestamps: str):
    values = iter(timestamps)
    return lambda: next(values)


def _cp(command: list[str], *, rc_value: int, out: str = "", err: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=command, returncode=rc_value, stdout=out, stderr=err)


def test_require_digest_locked_release_ref_accepts_and_normalizes() -> None:
    ref = "ghcr.io/terminal-zero/quant:2026.03.01@sha256:" + ("A" * 64)
    normalized = rc.require_digest_locked_release_ref(ref)
    assert normalized.endswith("a" * 64)


def test_require_digest_locked_release_ref_rejects_unlocked_ref() -> None:
    with pytest.raises(ValueError, match="digest-locked"):
        rc.require_digest_locked_release_ref("ghcr.io/terminal-zero/quant:latest")


def test_execute_release_controller_promotes_candidate_when_probe_passes(tmp_path: Path) -> None:
    metadata_path = tmp_path / "release_metadata.json"
    initial_state = ReleaseMetadata(
        current_release=ReleaseRecord(
            version="2026.02.28",
            release_ref=_release_ref("2026.02.28", "a"),
            deployed_at="2026-02-28T00:00:00Z",
        ),
        previous_release=ReleaseRecord(
            version="2026.02.27",
            release_ref=_release_ref("2026.02.27", "b"),
            deployed_at="2026-02-27T00:00:00Z",
        ),
        status="active",
        last_action="promoted",
        updated_at="2026-02-28T00:00:00Z",
    )
    rc.write_release_metadata(metadata_path, initial_state)

    result = rc.execute_release_controller(
        metadata_path=metadata_path,
        candidate_version="2026.03.01",
        candidate_ref=_release_ref("2026.03.01", "c"),
        startup_probe=lambda: {"ok": True, "details": "startup-check-ok"},
        now_utc=_now_factory("2026-03-01T10:00:00Z", "2026-03-01T10:00:03Z"),
    )

    assert result["status"] == "promoted"
    assert result["probe_ok"] is True
    assert result["active_version"] == "2026.03.01"
    assert result["rollback_target"] is None

    final_state = rc.load_release_metadata(metadata_path)
    assert final_state.status == "active"
    assert final_state.current_release is not None
    assert final_state.current_release.version == "2026.03.01"
    assert final_state.previous_release is not None
    assert final_state.previous_release.version == "2026.02.28"
    assert final_state.pending_release is None
    assert final_state.last_probe == {
        "ok": True,
        "details": "startup-check-ok",
        "checked_at": "2026-03-01T10:00:03Z",
    }


def test_execute_release_controller_rolls_back_to_n_minus_1_when_probe_fails(tmp_path: Path) -> None:
    metadata_path = tmp_path / "release_metadata.json"
    initial_state = ReleaseMetadata(
        current_release=ReleaseRecord(
            version="2026.02.28",
            release_ref=_release_ref("2026.02.28", "d"),
            deployed_at="2026-02-28T00:00:00Z",
        ),
        previous_release=ReleaseRecord(
            version="2026.02.27",
            release_ref=_release_ref("2026.02.27", "e"),
            deployed_at="2026-02-27T00:00:00Z",
        ),
        status="active",
        last_action="promoted",
        updated_at="2026-02-28T00:00:00Z",
    )
    rc.write_release_metadata(metadata_path, initial_state)

    result = rc.execute_release_controller(
        metadata_path=metadata_path,
        candidate_version="2026.03.01",
        candidate_ref=_release_ref("2026.03.01", "f"),
        startup_probe=lambda: {"ok": False, "details": "probe-failed", "rollback_ok": True},
        now_utc=_now_factory("2026-03-01T10:00:00Z", "2026-03-01T10:00:04Z"),
    )

    assert result["status"] == "rolled_back"
    assert result["rollback_verified"] is True
    assert result["probe_ok"] is False
    assert result["active_version"] == "2026.02.28"
    assert result["rollback_target"] == "n-1"

    final_state = rc.load_release_metadata(metadata_path)
    assert final_state.status == "rolled_back"
    assert final_state.last_action == "rolled_back_to_n_minus_1"
    assert final_state.current_release is not None
    assert final_state.current_release.version == "2026.02.28"
    assert final_state.previous_release is not None
    assert final_state.previous_release.version == "2026.02.27"
    assert final_state.pending_release is None
    assert final_state.last_candidate_release is not None
    assert final_state.last_candidate_release.version == "2026.03.01"
    assert final_state.last_probe == {
        "ok": False,
        "details": "probe-failed",
        "rollback_ok": True,
        "checked_at": "2026-03-01T10:00:04Z",
    }


def test_execute_release_controller_handles_interrupted_pending_probe_state(tmp_path: Path) -> None:
    metadata_path = tmp_path / "release_metadata.json"
    interrupted_candidate = ReleaseRecord(
        version="2026.03.01",
        release_ref=_release_ref("2026.03.01", "c"),
        deployed_at="2026-03-01T09:59:00Z",
    )
    last_known_good = ReleaseRecord(
        version="2026.02.28",
        release_ref=_release_ref("2026.02.28", "d"),
        deployed_at="2026-02-28T00:00:00Z",
    )
    interrupted_state = ReleaseMetadata(
        current_release=interrupted_candidate,
        previous_release=last_known_good,
        pending_release=interrupted_candidate,
        last_candidate_release=interrupted_candidate,
        status="pending_probe",
        last_action="candidate_staged",
        updated_at="2026-03-01T09:59:00Z",
    )
    rc.write_release_metadata(metadata_path, interrupted_state)

    result = rc.execute_release_controller(
        metadata_path=metadata_path,
        candidate_version="2026.03.02",
        candidate_ref=_release_ref("2026.03.02", "e"),
        startup_probe=lambda: {"ok": False, "details": "new-candidate-failed", "rollback_ok": True},
        now_utc=_now_factory("2026-03-02T10:00:00Z", "2026-03-02T10:00:03Z"),
    )

    assert result["status"] == "rolled_back"
    assert result["active_version"] == "2026.02.28"
    final_state = rc.load_release_metadata(metadata_path)
    assert final_state.current_release is not None
    assert final_state.current_release.version == "2026.02.28"
    assert final_state.status == "rolled_back"


def test_execute_release_controller_marks_rollback_failed_when_not_verified(tmp_path: Path) -> None:
    metadata_path = tmp_path / "release_metadata.json"
    initial_state = ReleaseMetadata(
        current_release=ReleaseRecord(
            version="2026.02.28",
            release_ref=_release_ref("2026.02.28", "a"),
            deployed_at="2026-02-28T00:00:00Z",
        ),
        previous_release=ReleaseRecord(
            version="2026.02.27",
            release_ref=_release_ref("2026.02.27", "b"),
            deployed_at="2026-02-27T00:00:00Z",
        ),
        status="active",
        last_action="promoted",
        updated_at="2026-02-28T00:00:00Z",
    )
    rc.write_release_metadata(metadata_path, initial_state)

    result = rc.execute_release_controller(
        metadata_path=metadata_path,
        candidate_version="2026.03.01",
        candidate_ref=_release_ref("2026.03.01", "c"),
        startup_probe=lambda: {"ok": False, "details": "probe-failed", "rollback_ok": False},
        now_utc=_now_factory("2026-03-01T10:00:00Z", "2026-03-01T10:00:04Z"),
    )

    assert result["status"] == "rollback_failed"
    assert result["rollback_verified"] is False
    assert result["active_version"] is None
    final_state = rc.load_release_metadata(metadata_path)
    assert final_state.status == "rollback_failed"
    assert final_state.current_release is None
    assert final_state.last_action == "rollback_not_verified"
    assert final_state.last_probe == {
        "ok": False,
        "details": "probe-failed",
        "rollback_ok": False,
        "checked_at": "2026-03-01T10:00:04Z",
    }


def test_run_startup_diagnostic_converts_exceptions_to_failures() -> None:
    result = rc.run_startup_diagnostic(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert result.ok is False
    assert "probe_exception:RuntimeError:boom" in result.details


def test_atomic_write_json_preserves_old_file_and_cleans_temp_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "release_metadata.json"
    path.write_text('{"state":"old"}\n', encoding="utf-8")

    def _raise_permission_error(_src, _dst):
        raise PermissionError("file is locked")

    monkeypatch.setattr(rc.os, "replace", _raise_permission_error)

    with pytest.raises(PermissionError):
        rc.atomic_write_json(path, {"state": "new"})

    assert json.loads(path.read_text(encoding="utf-8")) == {"state": "old"}
    assert list(tmp_path.glob("*.tmp")) == []


def test_release_cache_fingerprint_binds_version_and_digest() -> None:
    assert build_release_cache_fingerprint("3.9", "ab" * 32) == f"3.9@sha256:{'ab' * 32}"
    assert build_release_cache_fingerprint("3.9", "") == "3.9@sha256:local-dev"


def test_build_docker_startup_probe_rolls_back_on_candidate_exit() -> None:
    service_name = "tz_test"
    candidate_ref = _release_ref("2026.03.01", "c")
    rollback_ref = _release_ref("2026.02.28", "d")

    responses = [
        _cp(["docker", "rm", "-f", f"{service_name}__candidate"], rc_value=1, err="No such container"),
        _cp(["docker", "run", "-d"], rc_value=0, out="candidate_container"),
        _cp(["docker", "inspect"], rc_value=0, out="false|1|none"),
        _cp(["docker", "logs", "--tail", "40", f"{service_name}__candidate"], rc_value=0, err="terminal scanner failure"),
        _cp(["docker", "rm", "-f", f"{service_name}__candidate"], rc_value=0, out="removed"),
        _cp(["docker", "inspect"], rc_value=1, err="No such object"),
        _cp(["docker", "rm", "-f", service_name], rc_value=1, err="No such container"),
        _cp(["docker", "run", "-d"], rc_value=0, out="rollback_container"),
        _cp(["docker", "inspect"], rc_value=0, out="true|0|none"),
        _cp(["docker", "inspect"], rc_value=0, out="true|0|none"),
    ]

    calls: list[list[str]] = []

    def _runner(command, *, timeout_seconds):
        calls.append([str(x) for x in command])
        return responses.pop(0)

    monotonic_values = iter([0.0, 0.1, 0.2, 0.3, 2.5, 2.6, 2.7])
    probe = rc.build_docker_startup_probe(
        service_name=service_name,
        candidate_ref=candidate_ref,
        rollback_ref=rollback_ref,
        startup_wait_seconds=2.0,
        rollback_wait_seconds=2.0,
        runner=_runner,
        monotonic=lambda: next(monotonic_values),
        sleep_fn=lambda _seconds: None,
    )
    result = probe()

    assert result.ok is False
    assert result.rollback_ok is True
    assert "candidate_not_ready" in result.details
    assert "rollback_ok=True" in result.details
    assert len(calls) == 10
    assert calls[1][0:6] == ["docker", "run", "-d", "--name", f"{service_name}__candidate", "--restart"]
    assert any(token.startswith("TZ_RELEASE_DIGEST=") for token in calls[1])
    assert calls[7][0:6] == ["docker", "run", "-d", "--name", service_name, "--restart"]


def test_build_docker_startup_probe_passes_when_container_survives_watch_window() -> None:
    service_name = "tz_test"
    candidate_ref = _release_ref("2026.03.01", "f")

    responses = [
        _cp(["docker", "rm", "-f", f"{service_name}__candidate"], rc_value=1, err="Error: No such container"),
        _cp(["docker", "run", "-d"], rc_value=0, out="candidate_container"),
        _cp(["docker", "inspect"], rc_value=0, out="true|0|none"),
        _cp(["docker", "inspect"], rc_value=0, out="true|0|none"),
        _cp(["docker", "rm", "-f", service_name], rc_value=0, out="removed"),
        _cp(["docker", "rename", f"{service_name}__candidate", service_name], rc_value=0, out=""),
        _cp(["docker", "inspect"], rc_value=0, out="true|0|none"),
        _cp(["docker", "inspect"], rc_value=0, out="true|0|none"),
    ]
    calls: list[list[str]] = []

    def _runner(command, *, timeout_seconds):
        calls.append([str(x) for x in command])
        return responses.pop(0)

    monotonic_values = iter([0.0, 0.1, 2.1, 3.0, 3.1, 5.5])
    probe = rc.build_docker_startup_probe(
        service_name=service_name,
        candidate_ref=candidate_ref,
        rollback_ref=None,
        startup_wait_seconds=2.0,
        rollback_wait_seconds=2.0,
        runner=_runner,
        monotonic=lambda: next(monotonic_values),
        sleep_fn=lambda _seconds: None,
    )
    result = probe()

    assert result.ok is True
    assert result.rollback_ok is None
    assert "candidate_promoted" in result.details
    assert len(calls) == 8
    candidate_run_idx = next(i for i, c in enumerate(calls) if c[:3] == ["docker", "run", "-d"])
    active_remove_idx = next(i for i, c in enumerate(calls) if c[:4] == ["docker", "rm", "-f", service_name])
    assert candidate_run_idx < active_remove_idx


def test_main_docker_mode_uses_stable_rollback_ref_after_interrupted_pending_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata_path = tmp_path / "release_metadata.json"
    interrupted_candidate = ReleaseRecord(
        version="2026.03.01",
        release_ref=_release_ref("2026.03.01", "a"),
        deployed_at="2026-03-01T09:00:00Z",
    )
    last_known_good = ReleaseRecord(
        version="2026.02.28",
        release_ref=_release_ref("2026.02.28", "b"),
        deployed_at="2026-02-28T00:00:00Z",
    )
    rc.write_release_metadata(
        metadata_path,
        ReleaseMetadata(
            current_release=interrupted_candidate,
            previous_release=last_known_good,
            pending_release=interrupted_candidate,
            last_candidate_release=interrupted_candidate,
            status="pending_probe",
            last_action="candidate_staged",
            updated_at="2026-03-01T09:00:00Z",
        ),
    )

    captured: dict[str, object] = {}

    def _fake_build_docker_startup_probe(**kwargs):
        captured.update(kwargs)
        return lambda: {"ok": True, "details": "ok"}

    monkeypatch.setattr(rc, "build_docker_startup_probe", _fake_build_docker_startup_probe)
    monkeypatch.setattr(
        rc,
        "execute_release_controller",
        lambda **_kwargs: {
            "status": "promoted",
            "candidate_version": "2026.03.02",
            "candidate_ref": _release_ref("2026.03.02", "c"),
            "active_version": "2026.03.02",
            "active_ref": _release_ref("2026.03.02", "c"),
            "rollback_target": None,
            "probe_ok": True,
            "probe_details": "ok",
        },
    )

    exit_code = rc.main(
        [
            "--mode",
            "docker",
            "--metadata-path",
            str(metadata_path),
            "--candidate-version",
            "2026.03.02",
            "--candidate-ref",
            _release_ref("2026.03.02", "c"),
            "--service-name",
            "tz_test_main",
            "--startup-wait-seconds",
            "5",
        ]
    )

    assert exit_code == 0
    assert captured["rollback_ref"] == last_known_good.release_ref


def test_release_run_lock_refuses_non_owner_unlock(tmp_path: Path) -> None:
    lock_path = tmp_path / "release_controller.lock"
    owner_token = rc._acquire_run_lock(lock_path, stale_seconds=60.0)
    assert lock_path.exists()
    assert rc._release_run_lock(lock_path, owner_token="not-owner") is False
    assert lock_path.exists()
    assert rc._release_run_lock(lock_path, owner_token=owner_token) is True
    assert not lock_path.exists()


def test_acquire_run_lock_rejects_stale_lock_when_owner_pid_alive(tmp_path: Path) -> None:
    lock_path = tmp_path / "release_controller.lock"
    lock_path.write_text(f"token=existing\npid={os.getpid()}\ncreated_at_utc=2026-03-01T00:00:00Z\n", encoding="utf-8")
    os.utime(lock_path, (1, 1))

    with pytest.raises(RuntimeError, match="active pid"):
        rc._acquire_run_lock(lock_path, stale_seconds=1.0)

    assert lock_path.exists()


def test_acquire_run_lock_takes_over_stale_lock_when_owner_pid_dead(tmp_path: Path) -> None:
    lock_path = tmp_path / "release_controller.lock"
    lock_path.write_text("token=old\npid=999999\ncreated_at_utc=2026-03-01T00:00:00Z\n", encoding="utf-8")
    os.utime(lock_path, (1, 1))

    owner_token = rc._acquire_run_lock(lock_path, stale_seconds=1.0)
    fields = rc._read_lock_fields(lock_path)
    assert fields.get("token") == owner_token
    assert fields.get("pid") == str(os.getpid())
    assert rc._release_run_lock(lock_path, owner_token=owner_token) is True


def test_main_external_probe_requires_explicit_ack() -> None:
    with pytest.raises(SystemExit):
        rc.main(
            [
                "--mode",
                "external-probe",
                "--candidate-version",
                "2026.03.02",
                "--candidate-ref",
                _release_ref("2026.03.02", "c"),
                "--probe-command",
                "echo",
                "ok",
            ]
        )


def test_main_returns_distinct_code_for_rollback_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata_path = tmp_path / "release_metadata.json"
    monkeypatch.setattr(
        rc,
        "execute_release_controller",
        lambda **_kwargs: {
            "status": "rollback_failed",
            "candidate_version": "2026.03.02",
            "candidate_ref": _release_ref("2026.03.02", "c"),
            "active_version": None,
            "active_ref": None,
            "rollback_target": "n-1",
            "rollback_verified": False,
            "probe_ok": False,
            "probe_details": "rollback failed",
        },
    )
    exit_code = rc.main(
        [
            "--mode",
            "metadata-only",
            "--metadata-path",
            str(metadata_path),
            "--candidate-version",
            "2026.03.02",
            "--candidate-ref",
            _release_ref("2026.03.02", "c"),
        ]
    )
    assert exit_code == 4
