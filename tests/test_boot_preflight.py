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


class _GovernanceResult:
    def __init__(self, status: str = "PASS") -> None:
        self.status = status

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, "findings": []}


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
        "upstream_aligned": True,
        "expected_remote_proof": {
            "requested": False,
            "aligned": False,
            "proof_available": False,
            "reason": "not_requested",
        },
        "worktree_clean": True,
        "entries": [],
    }


@pytest.fixture(autouse=True)
def _default_dependency_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        boot_preflight,
        "_run_data_readiness_gate_check",
        lambda _repo, _mode: {
            "status": "PASS",
            "command": "data-readiness",
            "summary": "Data readiness gate passed.",
        },
    )
    monkeypatch.setattr(
        boot_preflight,
        "_run_script_gate",
        lambda _repo, command_parts, **_kwargs: {
            "status": "PASS",
            "command": " ".join(boot_preflight._python_command(command_parts)),
            "returncode": 0,
        },
    )


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


def test_strict_gates_run_real_checks_when_requested(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pytest_commands: list[tuple[str, ...]] = []
    script_commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())

    def fake_pytest_gate(
        _repo: Path,
        command_parts: tuple[str, ...],
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        pytest_commands.append(command_parts)
        return {"status": "PASS", "command": "pytest", "returncode": 0}

    monkeypatch.setattr(boot_preflight, "_run_pytest_gate", fake_pytest_gate)
    monkeypatch.setattr(
        boot_preflight,
        "_run_script_gate",
        lambda _repo, command_parts, **_kwargs: script_commands.append(command_parts)
        or {"status": "PASS", "command": "context", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--smoke", "--run-focused-contract"])
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    assert pytest_commands == [
        boot_preflight.BOOT_CONTROL_TEST_COMMAND,
        boot_preflight.PORTFOLIO_APPTEST_SMOKE_COMMAND,
        boot_preflight.FOCUSED_REPLAY_DASHBOARD_CONTRACT_COMMAND,
    ]
    assert "tests/test_rendered_apptest_governance.py" in boot_preflight.PORTFOLIO_APPTEST_SMOKE_COMMAND
    assert (
        "tests/test_optimizer_view.py::test_optimizer_view_rendered_labels_are_governance_safe"
        in boot_preflight.PORTFOLIO_APPTEST_SMOKE_COMMAND
    )
    assert script_commands == [boot_preflight.CONTEXT_PACKET_VALIDATION_COMMAND]
    assert status["checks"]["data_readiness_gate"]["status"] == "PASS"
    assert status["checks"]["governance"]["status"] == "PASS"
    assert status["checks"]["portfolio_apptest_smoke"]["status"] == "PASS"
    assert status["checks"]["focused_replay_dashboard_contract"]["status"] == "PASS"
    assert boot_status.primary_verdict == "degraded"
    assert boot_status.flags.boot_candidate is True
    assert boot_status.flags.safe_boot is False


def test_strict_smoke_blocks_status_write_when_rendered_governance_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest_commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())

    def fake_pytest_gate(
        _repo: Path,
        command_parts: tuple[str, ...],
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        pytest_commands.append(command_parts)
        if "tests/test_rendered_apptest_governance.py" in command_parts:
            return {
                "status": "FAIL",
                "command": "pytest rendered-governance",
                "returncode": 1,
            }
        return {"status": "PASS", "command": "pytest", "returncode": 0}

    monkeypatch.setattr(boot_preflight, "_run_pytest_gate", fake_pytest_gate)

    args = boot_preflight.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "--strict",
            "--require-github",
            "--smoke",
            "--run-focused-contract",
            "--write-status",
        ]
    )
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert status["checks"]["portfolio_apptest_smoke"]["status"] == "FAIL"
    assert "Portfolio AppTest smoke failed" in status["failures"]
    assert boot_preflight.PORTFOLIO_APPTEST_SMOKE_COMMAND in pytest_commands
    assert status["status_write"] == {
        "path": CANONICAL_BOOT_STATUS_PATH.as_posix(),
        "result": "blocked-until-pass",
    }
    assert boot_status.flags.safe_boot is False
    assert not (tmp_path / CANONICAL_BOOT_STATUS_PATH).exists()


def test_strict_default_marks_unrequested_dashboard_gates_as_safe_boot_blockers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict"])
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 0
    assert status["checks"]["portfolio_apptest_smoke"]["status"] == "SKIPPED"
    assert status["checks"]["focused_replay_dashboard_contract"]["status"] == "SKIPPED"
    assert boot_status.primary_verdict == "degraded"
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
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
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
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(
        ["--repo-root", str(tmp_path), "--strict", "--require-github", "--smoke", "--run-focused-contract", "--write-status"]
    )
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
    assert boot_status.flags.safe_boot is True


def test_require_github_write_status_detects_post_write_dirty_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    git_states = [
        _clean_git_state(),
        _clean_git_state(),
        {
            **_clean_git_state(),
            "worktree_clean": False,
            "entries": [{"status": "M", "path": CANONICAL_BOOT_STATUS_PATH.as_posix()}],
        },
    ]
    observed_paths: list[Path] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: git_states.pop(0))
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
        ["--repo-root", str(tmp_path), "--strict", "--require-github", "--smoke", "--run-focused-contract", "--write-status"]
    )
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert status["status_write"] == {
        "path": CANONICAL_BOOT_STATUS_PATH.as_posix(),
        "result": "written",
    }
    assert observed_paths == [CANONICAL_BOOT_STATUS_PATH]
    assert status["post_git"]["worktree_clean"] is True
    assert status["final_git"]["worktree_clean"] is False
    assert status["final_git"]["entries"] == [
        {"status": "M", "path": CANONICAL_BOOT_STATUS_PATH.as_posix()}
    ]
    assert "--require-github final post-write check requires a clean worktree" in status["failures"]
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
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
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
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
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
            "--require-github",
            "--smoke",
            "--run-focused-contract",
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
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
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
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(
        boot_preflight,
        "collect_git_state",
        lambda _repo, **_kwargs: {
            **_clean_git_state(),
            "aligned": False,
            "upstream_aligned": False,
            "ahead": 1,
        },
    )
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--require-github"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert "--require-github upstream mismatch:ahead=1,behind=0" in status["failures"]


def test_detached_expected_ref_and_sha_satisfy_require_github(tmp_path: Path, monkeypatch) -> None:
    head = "fb31170abc123"
    calls: list[tuple[str, ...]] = []

    def fake_git(_repo: Path, *args: str) -> CommandResult:
        calls.append(args)
        if args == ("rev-parse", "--is-inside-work-tree"):
            return CommandResult(args=args, returncode=0, stdout="true\n")
        if args == ("rev-parse", "--abbrev-ref", "HEAD"):
            return CommandResult(args=args, returncode=0, stdout="HEAD\n")
        if args == ("rev-parse", "HEAD"):
            return CommandResult(args=args, returncode=0, stdout=f"{head}\n")
        if args == ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"):
            return CommandResult(args=args, returncode=128, stderr="no upstream\n")
        if args == ("rev-parse", "@{u}"):
            return CommandResult(args=args, returncode=128, stderr="no upstream\n")
        if args == ("rev-list", "--left-right", "--count", "HEAD...@{u}"):
            return CommandResult(args=args, returncode=128, stderr="no upstream\n")
        if args == ("status", "--porcelain=v1", "-z"):
            return CommandResult(args=args, returncode=0, stdout="")
        if args == ("ls-remote", "origin", "refs/heads/codex/phase-close"):
            return CommandResult(
                args=args,
                returncode=0,
                stdout=f"{head}\trefs/heads/codex/phase-close\n",
            )
        return CommandResult(args=args, returncode=1, stderr=f"unexpected:{args!r}")

    monkeypatch.setattr(boot_preflight, "_git", fake_git)
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
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
            "--require-github",
            "--expected-ref",
            "codex/phase-close",
            "--expected-sha",
            head,
        ]
    )
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    proof = status["checks"]["git"]["expected_remote_proof"]
    assert proof["aligned"] is True
    assert proof["proof_available"] is True
    assert proof["remote_sha"] == head
    assert proof["local_head_matches_remote"] is True
    assert proof["local_head_matches_expected_sha"] is True
    assert proof["remote_matches_expected_sha"] is True
    assert proof["reason"] == "expected_ref_sha_aligned"
    assert ("ls-remote", "origin", "refs/heads/codex/phase-close") in calls


def test_data_readiness_warn_degrades_safe_boot_even_when_preflight_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )
    monkeypatch.setattr(
        boot_preflight,
        "_run_data_readiness_gate_check",
        lambda _repo, _mode: {
            "status": "WARN",
            "summary": "Data readiness gate warned: 1 warning(s).",
            "details": {"strict_status": "WARN", "summary": {"warnings": ["uncertified"]}},
        },
    )

    args = boot_preflight.parse_args(
        ["--repo-root", str(tmp_path), "--strict", "--require-github", "--smoke", "--run-focused-contract"]
    )
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    assert status["checks"]["data_readiness_gate"]["status"] == "WARN"
    assert boot_status.primary_verdict == "degraded"
    assert boot_status.flags.safe_boot is False


def test_detached_require_github_without_expected_proof_fails_as_unavailable(tmp_path: Path, monkeypatch) -> None:
    def fake_git(_repo: Path, *args: str) -> CommandResult:
        if args == ("rev-parse", "--is-inside-work-tree"):
            return CommandResult(args=args, returncode=0, stdout="true\n")
        if args == ("rev-parse", "--abbrev-ref", "HEAD"):
            return CommandResult(args=args, returncode=0, stdout="HEAD\n")
        if args == ("rev-parse", "HEAD"):
            return CommandResult(args=args, returncode=0, stdout="fb31170abc123\n")
        if args == ("status", "--porcelain=v1", "-z"):
            return CommandResult(args=args, returncode=0, stdout="")
        if "@{u}" in args:
            return CommandResult(args=args, returncode=128, stderr="no upstream\n")
        return CommandResult(args=args, returncode=1, stderr=f"unexpected:{args!r}")

    monkeypatch.setattr(boot_preflight, "_git", fake_git)
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--require-github"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert "--require-github proof_unavailable:no upstream or explicit expected ref/SHA" in status["failures"]
    proof = status["checks"]["git"]["expected_remote_proof"]
    assert proof["requested"] is False
    assert proof["proof_available"] is False
    assert proof["reason"] == "not_requested"
    assert status["checks"]["git"]["has_upstream"] is False
    assert status["checks"]["git"]["aligned"] is False


def test_expected_sha_without_expected_ref_does_not_satisfy_github_proof(tmp_path: Path, monkeypatch) -> None:
    def fake_git(_repo: Path, *args: str) -> CommandResult:
        if args == ("rev-parse", "--is-inside-work-tree"):
            return CommandResult(args=args, returncode=0, stdout="true\n")
        if args == ("rev-parse", "--abbrev-ref", "HEAD"):
            return CommandResult(args=args, returncode=0, stdout="HEAD\n")
        if args == ("rev-parse", "HEAD"):
            return CommandResult(args=args, returncode=0, stdout="fb31170abc123\n")
        if args == ("status", "--porcelain=v1", "-z"):
            return CommandResult(args=args, returncode=0, stdout="")
        if "@{u}" in args:
            return CommandResult(args=args, returncode=128, stderr="no upstream\n")
        return CommandResult(args=args, returncode=1, stderr=f"unexpected:{args!r}")

    monkeypatch.setattr(boot_preflight, "_git", fake_git)

    git_state = boot_preflight.collect_git_state(tmp_path, expected_sha="fb31170abc123")

    proof = git_state["expected_remote_proof"]
    assert proof["requested"] is True
    assert proof["proof_available"] is False
    assert proof["aligned"] is False
    assert proof["local_head_matches_expected_sha"] is True
    assert proof["reason"] == "expected_ref_and_sha_required"


def test_require_github_post_check_reports_expected_proof_mismatch(tmp_path: Path, monkeypatch) -> None:
    first_state = {
        **_clean_git_state(),
        "has_upstream": False,
        "upstream_aligned": False,
        "aligned": True,
        "expected_remote_proof": {
            "requested": True,
            "aligned": True,
            "proof_available": True,
            "reason": "expected_ref_sha_aligned",
        },
    }
    post_state = {
        **first_state,
        "aligned": False,
        "expected_remote_proof": {
            "requested": True,
            "aligned": False,
            "proof_available": True,
            "reason": "remote_sha_mismatch",
        },
    }
    states = [first_state, post_state, post_state]

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "run_governance_preflight", lambda _repo: _GovernanceResult("PASS"))
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: states.pop(0))
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
            "--require-github",
            "--expected-ref",
            "codex/phase-close",
            "--expected-sha",
            "abc123",
        ]
    )
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert "--require-github post-check expected ref/SHA proof failed:remote_sha_mismatch" in status["failures"]


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
            "data_readiness_gate": {"status": "PASS", "command": "data-readiness"},
            "context_packet_validation": {"status": "PASS", "command": "context"},
            "portfolio_apptest_smoke": {"status": "SKIPPED", "reason": "not requested"},
            "focused_replay_dashboard_contract": {"status": "SKIPPED", "reason": "not requested"},
        },
    }

    boot_status = boot_preflight.make_boot_status_from_preflight(preflight_status)
    round_trip = BootStatus.from_json_dict(json.loads(boot_status.to_json_text()))

    assert round_trip.primary_verdict == "degraded"
    assert any(check.id == "portfolio_apptest_smoke" and check.status == "not_applicable" for check in round_trip.checks)
    assert round_trip.flags.safe_boot is False


def test_make_boot_status_from_preflight_sets_safe_boot_only_after_required_gate_truth() -> None:
    preflight_status = {
        "schema_version": boot_preflight.SCHEMA_VERSION,
        "generated_at_utc": "2026-05-26T00:00:00Z",
        "mode": "strict",
        "require_github": True,
        "verdict": "PASS",
        "exit_code": 0,
        "warnings": [],
        "checks": {
            "boot_core": {"status": "PASS", "command": "file-contract"},
            "git": _clean_git_state(),
            "post_git": _clean_git_state(),
            "dirty": {"status": "PASS", "dirty_state": "clean"},
            "governance": {"status": "PASS", "command": "governance"},
            "boot_control_tests": {"status": "PASS", "command": "pytest"},
            "data_readiness_gate": {"status": "PASS", "command": "data-readiness"},
            "context_packet_validation": {"status": "PASS", "command": "context"},
            "portfolio_apptest_smoke": {"status": "PASS", "command": "apptest"},
            "focused_replay_dashboard_contract": {"status": "PASS", "command": "focused"},
        },
    }

    boot_status = boot_preflight.make_boot_status_from_preflight(preflight_status)

    assert boot_status.primary_verdict == "ready"
    assert boot_status.flags.safe_boot is True
    assert boot_status.metadata["safe_boot_required_gates"] == [
        *boot_preflight.SAFE_BOOT_REQUIRED_GATES,
        "post_git_state",
    ]


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


def test_boot_core_imports_governance_and_data_readiness_gate() -> None:
    source = Path(boot_preflight.__file__).read_text(encoding="utf-8")

    assert "from scripts.governance_preflight import run_governance_preflight" in source
    assert "from core.data_readiness_gate import run_data_readiness_gate" in source


def test_boot_preflight_integration_blocks_on_governance_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        boot_preflight,
        "collect_git_state",
        lambda _repo, **_kwargs: {
            "available": True,
            "status": "PASS",
            "branch": "main",
            "head": "abc",
            "upstream": "origin/main",
            "upstream_head": "abc",
            "ahead": 0,
            "behind": 0,
            "has_upstream": True,
            "aligned": True,
            "upstream_aligned": True,
            "expected_remote_proof": {
                "requested": False,
                "aligned": False,
                "proof_available": False,
                "reason": "not_requested",
            },
            "worktree_clean": True,
            "entries": [],
        },
    )
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    (tmp_path / "dashboard.py").write_text('TITLE = "Strong Buy"\n', encoding="utf-8")

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--mode", "planning", "--no-tests"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert "governance preflight did not pass: FAIL" in status["failures"]
    assert status["checks"]["governance"]["status"] == "FAIL"


def test_strict_boot_blocks_on_unclassified_execution_inventory_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    broker_path = tmp_path / "execution" / "broker_api.py"
    broker_path.parent.mkdir(parents=True)
    broker_path.write_text(
        "class AlpacaBroker:\n"
        "    def submit_order(self):\n"
        "        return {'ok': True}\n",
        encoding="utf-8",
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--mode", "strict", "--no-tests"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert status["checks"]["governance"]["status"] == "FAIL"
    assert any(finding["code"] == "GOV-009" for finding in status["checks"]["governance"]["findings"])


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
