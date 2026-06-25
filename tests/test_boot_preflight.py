from __future__ import annotations

import json
from pathlib import Path

import launch
import pytest

from core.boot_status import BootStatus
from scripts import boot_preflight
from scripts.boot_preflight import CommandResult, DirtyEntry

CANONICAL_BOOT_STATUS_PATH = Path("runtime/boot_status_current.json")
CONTEXT_BOOT_STATUS_SNAPSHOT_PATH = Path("docs/context/boot_status_current.json")


def _clean_git_state() -> dict[str, object]:
    return {
        "available": True,
        "status": "PASS",
        "branch": "codex/optimizer-core-structured-diagnostics",
        "head": "abc123",
        "upstream": "origin/codex/optimizer-core-structured-diagnostics",
        "upstream_head": "abc123",
        "ahead": 0,
        "behind": 0,
        "has_upstream": True,
        "aligned": True,
        "worktree_clean": True,
        "entries": [],
    }


def test_generated_expert_packets_are_advisory_evidence() -> None:
    bucket, severity, reason = boot_preflight.classify_path(
        "docs/context/e2e_evidence/reboot_expert_packet_20260526/PACKET_INDEX.md"
    )

    assert bucket == "generated-evidence"
    assert severity == "advisory"
    assert "evidence" in reason


def test_dirty_classifier_fails_closed_on_unclassified_source() -> None:
    summary = boot_preflight.classify_dirty_entries(
        [DirtyEntry(status="??", path="core/new_runtime_surface.py")]
    )

    assert summary["status"] == "FAIL"
    assert summary["dirty_state"] == "unclassified-source"
    assert summary["blockers"][0]["path"] == "core/new_runtime_surface.py"


def test_dirty_classifier_marks_boot_core_files_as_classified() -> None:
    summary = boot_preflight.classify_dirty_entries(
        [
            DirtyEntry(status="??", path="BOOT.md"),
            DirtyEntry(status="M", path="launch.py"),
        ]
    )

    assert summary["status"] == "PASS"
    assert summary["counts"]["boot-core-candidate"] == 2


def test_validate_boot_core_requires_exact_schema_path(tmp_path: Path) -> None:
    for relative in boot_preflight.BOOT_CORE_REQUIRED_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "docs/context/boot_status_current.schema.json":
            path.write_text(
                json.dumps(
                    {
                        "properties": {
                            "schema_version": {"const": "boot-status/v1"},
                            "checks": {
                                "items": {
                                    "properties": {
                                        "status": {
                                            "enum": [
                                                "pass",
                                                "warn",
                                                "fail",
                                                "not_applicable",
                                                "deferred",
                                            ]
                                        }
                                    }
                                }
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
        else:
            path.write_text("ok\n", encoding="utf-8")

    result = boot_preflight.validate_boot_core(tmp_path)

    assert result["status"] == "PASS"
    assert result["required_files"] == list(boot_preflight.BOOT_CORE_REQUIRED_FILES)


def test_strict_default_runs_only_boot_control_tests_and_defers_broader_gates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pytest_commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: _clean_git_state())

    def fake_pytest_gate(
        _repo: Path,
        command_parts: tuple[str, ...],
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        pytest_commands.append(command_parts)
        return {"status": "PASS", "command": "pytest", "returncode": 0}

    monkeypatch.setattr(boot_preflight, "_run_pytest_gate", fake_pytest_gate)

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--smoke", "--run-focused-contract"])
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    assert pytest_commands == [boot_preflight.BOOT_CONTROL_TEST_COMMAND]
    assert status["checks"]["data_readiness_gate"]["status"] == "DEFERRED"
    assert status["checks"]["governance"]["status"] == "PASS"
    assert status["checks"]["portfolio_apptest_smoke"]["status"] == "DEFERRED"
    assert status["checks"]["focused_replay_dashboard_contract"]["status"] == "DEFERRED"
    assert boot_status.primary_verdict == "degraded"
    assert boot_status.flags.boot_candidate is True
    assert boot_status.flags.safe_boot is False


def test_boot_preflight_uses_runtime_boot_status_contract(capsys) -> None:
    assert boot_preflight.BOOT_STATUS_CURRENT_PATH == CANONICAL_BOOT_STATUS_PATH
    assert boot_preflight.DEFAULT_STATUS_JSON == CANONICAL_BOOT_STATUS_PATH

    with pytest.raises(SystemExit):
        boot_preflight.parse_args(["--help"])

    help_text = capsys.readouterr().out
    assert "runtime/boot_status_current.json" in help_text


def test_strict_preflight_without_write_flag_creates_no_status_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    assert "status_write" not in status
    assert not (tmp_path / CANONICAL_BOOT_STATUS_PATH).exists()
    assert not (tmp_path / CONTEXT_BOOT_STATUS_SNAPSHOT_PATH).exists()


def test_strict_write_status_writes_only_runtime_canonical_after_pass(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--write-status"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    assert status["status_write"]["path"] == CANONICAL_BOOT_STATUS_PATH.as_posix()
    assert (tmp_path / CANONICAL_BOOT_STATUS_PATH).exists()
    assert not (tmp_path / CONTEXT_BOOT_STATUS_SNAPSHOT_PATH).exists()
    boot_status = BootStatus.from_json_dict(
        json.loads((tmp_path / CANONICAL_BOOT_STATUS_PATH).read_text(encoding="utf-8"))
    )
    assert boot_status.metadata["mode"] == "strict"


def test_require_github_write_status_detects_post_write_dirty_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    git_states = [
        _clean_git_state(),
        {
            **_clean_git_state(),
            "worktree_clean": False,
            "entries": [{"status": "M", "path": CANONICAL_BOOT_STATUS_PATH.as_posix()}],
        },
    ]
    observed_paths: list[Path] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: git_states.pop(0))
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    def fake_write_boot_status_file(
        status: BootStatus,
        path: str | Path,
        *,
        repo_root: Path,
    ) -> str:
        observed_paths.append(Path(path))
        target = repo_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(status.to_json_text(), encoding="utf-8")
        assert git_states, "final GitHub proof must run after status write"
        return "written"

    monkeypatch.setattr(boot_preflight, "_write_boot_status_file", fake_write_boot_status_file)

    args = boot_preflight.parse_args(
        ["--repo-root", str(tmp_path), "--strict", "--require-github", "--write-status"]
    )
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert status["status_write"] == {
        "path": CANONICAL_BOOT_STATUS_PATH.as_posix(),
        "result": "written",
    }
    assert observed_paths == [CANONICAL_BOOT_STATUS_PATH]
    assert status["post_git"]["worktree_clean"] is False
    assert status["post_git"]["entries"] == [
        {"status": "M", "path": CANONICAL_BOOT_STATUS_PATH.as_posix()}
    ]
    assert "--require-github post-write check is not clean/aligned" in status["failures"]
    assert git_states == []


def test_strict_write_status_does_not_create_status_after_failed_preflight(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        boot_preflight,
        "validate_boot_core",
        lambda _repo: {"status": "FAIL", "blockers": ["missing:BOOT.md"]},
    )
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--write-status"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert status["status_write"] == {
        "path": CANONICAL_BOOT_STATUS_PATH.as_posix(),
        "result": "blocked-until-pass",
    }
    assert not (tmp_path / CANONICAL_BOOT_STATUS_PATH).exists()
    assert not (tmp_path / CONTEXT_BOOT_STATUS_SNAPSHOT_PATH).exists()


def test_strict_write_status_rejects_docs_context_snapshot_status_out(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "--strict",
            "--write-status",
            "--status-out",
            CONTEXT_BOOT_STATUS_SNAPSHOT_PATH.as_posix(),
        ]
    )

    with pytest.raises(boot_preflight.PreflightConfigError):
        boot_preflight.build_status(args)

    assert not (tmp_path / CANONICAL_BOOT_STATUS_PATH).exists()
    assert not (tmp_path / CONTEXT_BOOT_STATUS_SNAPSHOT_PATH).exists()


def test_planning_mode_does_not_run_tests(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "FAIL", "command": "should not run"},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--mode", "planning"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 0
    assert status["checks"]["boot_control_tests"]["status"] == "SKIPPED"


def test_require_github_blocks_dirty_or_unaligned_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(
        boot_preflight,
        "collect_git_state",
        lambda _repo: {**_clean_git_state(), "aligned": False, "ahead": 1},
    )
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--require-github"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert "--require-github requires HEAD to match upstream" in status["failures"]


def test_make_boot_status_from_preflight_is_schema_valid() -> None:
    preflight_status = {
        "schema_version": boot_preflight.SCHEMA_VERSION,
        "generated_at_utc": "2026-05-26T00:00:00Z",
        "mode": "strict",
        "require_github": False,
        "verdict": "PASS",
        "exit_code": 0,
        "warnings": [],
        "checks": {
            "boot_core": {"status": "PASS", "command": "file-contract"},
            "git": _clean_git_state(),
            "dirty": {"status": "PASS", "dirty_state": "clean"},
            "governance": {"status": "PASS", "command": "governance"},
            "boot_control_tests": {"status": "PASS", "command": "pytest"},
        },
    }

    boot_status = boot_preflight.make_boot_status_from_preflight(preflight_status)
    round_trip = BootStatus.from_json_dict(json.loads(boot_status.to_json_text()))

    assert round_trip.primary_verdict == "degraded"
    assert any(check.id == "data_readiness_gate" and check.status == "deferred" for check in round_trip.checks)


def test_launch_preflight_dispatch_adds_repo_root(monkeypatch) -> None:
    seen: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        seen.append(argv)
        return 17

    monkeypatch.setattr(boot_preflight, "main", fake_main)
    monkeypatch.setattr(launch, "_project_root", lambda: "E:\\Code\\Quant")

    result = launch._run_preflight(["--preflight", "--strict"])

    assert result == 17
    assert seen == [["--repo-root", "E:\\Code\\Quant", "--strict"]]


def test_launch_preflight_strict_alias_cannot_be_downgraded(monkeypatch) -> None:
    seen: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        seen.append(argv)
        return 0

    monkeypatch.setattr(boot_preflight, "main", fake_main)
    monkeypatch.setattr(launch, "_project_root", lambda: "E:\\Code\\Quant")

    assert launch._run_preflight(["--preflight-strict", "--mode", "planning"]) == 0
    assert seen == [["--repo-root", "E:\\Code\\Quant", "--mode", "planning", "--mode", "strict"]]


def test_launch_preflight_enforces_project_venv(monkeypatch) -> None:
    monkeypatch.setattr(launch, "_is_preflight_request", lambda _argv: True)
    monkeypatch.setattr(launch, "_check_python_version", lambda: [])
    monkeypatch.setattr(launch, "_check_venv", lambda: ["Python executable is not from project .venv."])
    monkeypatch.setattr(launch, "_print_errors", lambda _errors: None)
    monkeypatch.setattr(launch, "_run_preflight", lambda _argv: 0)

    assert launch.main() == 1


def test_boot_core_imports_governance_but_not_data_readiness() -> None:
    source = Path(boot_preflight.__file__).read_text(encoding="utf-8")

    assert "from scripts.governance_preflight import run_governance_preflight" in source
    assert "core.data_readiness_gate" not in source


def test_pytest_gate_uses_argv_not_shell(tmp_path: Path, monkeypatch) -> None:
    seen: list[tuple[object, bool, float | None]] = []

    def fake_run_command(
        args: object,
        *,
        cwd: Path,
        shell: bool = False,
        timeout: float | None = None,
    ) -> CommandResult:
        seen.append((args, shell, timeout))
        return CommandResult(args=args, returncode=0)

    monkeypatch.setattr(boot_preflight, "_run_command", fake_run_command)

    result = boot_preflight._run_pytest_gate(tmp_path, boot_preflight.BOOT_CONTROL_TEST_COMMAND, timeout=12.5)

    assert result["status"] == "PASS"
    assert seen
    assert seen[0][1] is False
    assert seen[0][2] == 12.5
