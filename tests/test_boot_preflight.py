from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import launch
from core.boot_status import BootStatus
from scripts import boot_preflight
from scripts.boot_preflight import CommandResult, DirtyEntry


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


def _data_gate_status(overall_status: str = "PASS") -> dict[str, object]:
    return {
        "schema_version": "data_readiness_gate.v0",
        "generated_at_utc": "2026-05-26T00:00:00Z",
        "mode": "strict",
        "overall_status": overall_status,
        "planning_status": overall_status,
        "strict_status": overall_status,
        "route_id": "portfolio_allocation.strict.v0",
        "route_readiness": {"portfolio_allocation_route_status": overall_status},
        "summary": {
            "blockers": ["missing strict-required artifacts"] if overall_status == "FAIL" else [],
            "warnings": ["missing optional artifacts"] if overall_status == "WARN" else [],
            "next_actions": [],
        },
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
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("PASS"))

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
    assert status["checks"]["data_readiness_gate"]["overall_status"] == "PASS"
    assert status["checks"]["governance_preflight"]["status"] == "DEFERRED"
    assert status["checks"]["portfolio_apptest_smoke"]["status"] == "DEFERRED"
    assert status["checks"]["focused_replay_dashboard_contract"]["status"] == "DEFERRED"
    assert boot_status.primary_verdict == "degraded"
    assert boot_status.flags.boot_candidate is True
    assert boot_status.flags.safe_boot is False


def test_planning_mode_does_not_run_tests(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("PASS"))
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
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("PASS"))
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
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("PASS"))
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
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("PASS"))
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
    states = [first_state, post_state]

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("PASS"))
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
            "data_readiness_gate": _data_gate_status("PASS"),
            "boot_control_tests": {"status": "PASS", "command": "pytest"},
        },
    }

    boot_status = boot_preflight.make_boot_status_from_preflight(preflight_status)
    round_trip = BootStatus.from_json_dict(json.loads(boot_status.to_json_text()))

    assert round_trip.primary_verdict == "degraded"
    assert any(check.id == "data_readiness_gate" and check.status == "pass" for check in round_trip.checks)


def test_data_readiness_gate_failure_blocks_preflight(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("FAIL"))
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict"])
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 1
    assert "data-readiness gate failed" in status["failures"]
    classification = status["checks"]["data_readiness_gate"]["boot_phase_close_classification"]
    assert classification["CodeReady"] == "PASS_WITH_DATA_QUARANTINE"
    assert classification["DataReadyStrict"] == "BLOCKED_MISSING_LOCAL_ARTIFACTS"
    assert classification["BootReady"] == "BLOCKED_DATA_READY_STRICT"
    assert boot_status.primary_verdict == "blocked"
    data_check = next(check for check in boot_status.checks if check.id == "data_readiness_gate")
    assert data_check.status == "fail"
    assert data_check.details["boot_phase_close_classification"]["CodeReady"] == "PASS_WITH_DATA_QUARANTINE"


def test_failed_preflight_does_not_write_runtime_status_without_write_status(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_status = tmp_path / "runtime" / "boot_status_current.json"
    writes: list[Any] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("FAIL"))
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )
    monkeypatch.setattr(
        boot_preflight,
        "write_boot_status_file",
        lambda *args, **kwargs: writes.append((args, kwargs)) or "written",
    )

    args = boot_preflight.parse_args(
        ["--repo-root", str(tmp_path), "--strict", "--status-out", str(runtime_status)]
    )
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["verdict"] == "FAIL"
    assert "status_write" not in status
    assert writes == []
    assert not runtime_status.exists()


def test_mixed_data_contract_failure_is_not_data_quarantine(tmp_path: Path, monkeypatch) -> None:
    mixed_status = {
        **_data_gate_status("FAIL"),
        "checks": [
            {
                "id": "canonical_presence.portfolio_allocation",
                "status": "FAIL",
                "mode_effect": {"planning": "WARN", "strict": "FAIL"},
                "reason": "missing strict-required artifacts",
                "metrics": {
                    "required_missing": ["data/processed/prices_tri.parquet"],
                    "optional_missing": ["data/processed/yahoo_patch.parquet"],
                },
            },
            {
                "id": "price_return_integrity.selected_sample",
                "status": "FAIL",
                "mode_effect": {"planning": "WARN", "strict": "FAIL"},
                "reason": "return_values_outside_unit_bound",
            },
        ],
        "summary": {"blockers": ["missing strict-required artifacts", "return_values_outside_unit_bound"], "warnings": []},
    }

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: mixed_status)
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    classification = status["checks"]["data_readiness_gate"]["boot_phase_close_classification"]
    assert classification["CodeReady"] == "BLOCKED_DATA_CONTRACT"
    assert classification["DataReadyStrict"] == "BLOCKED_DATA_CONTRACT"
    assert classification["BootReady"] == "BLOCKED_DATA_READY_STRICT"
    assert classification["missing_local_artifacts"] == ["data/processed/prices_tri.parquet"]
    assert classification["data_contract_blockers"] == ["return_values_outside_unit_bound"]


def test_missing_schema_failure_is_not_data_quarantine(tmp_path: Path, monkeypatch) -> None:
    schema_status = {
        **_data_gate_status("FAIL"),
        "checks": [
            {
                "id": "price_return_integrity.selected_sample",
                "status": "FAIL",
                "mode_effect": {"planning": "WARN", "strict": "FAIL"},
                "reason": "missing_required_columns",
            },
        ],
        "summary": {"blockers": ["missing_required_columns"], "warnings": []},
    }

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: schema_status)
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    classification = status["checks"]["data_readiness_gate"]["boot_phase_close_classification"]
    assert classification["CodeReady"] == "BLOCKED_DATA_CONTRACT"
    assert classification["DataReadyStrict"] == "BLOCKED_DATA_CONTRACT"
    assert classification["missing_local_artifacts"] == []
    assert classification["data_contract_blockers"] == ["missing_required_columns"]


def test_data_readiness_gate_warning_degrades_without_failing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("WARN"))
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict"])
    status, exit_code = boot_preflight.build_status(args)
    boot_status = boot_preflight.make_boot_status_from_preflight(status)

    assert exit_code == 0
    assert status["verdict"] == "PASS"
    assert "Data readiness gate is degraded or uncertified." in status["warnings"]
    assert boot_status.primary_verdict == "degraded"
    assert any(check.id == "data_readiness_gate" and check.status == "warn" for check in boot_status.checks)


def test_write_status_is_blocked_until_preflight_passes(tmp_path: Path, monkeypatch) -> None:
    writes: list[Path] = []

    monkeypatch.setattr(boot_preflight, "validate_boot_core", lambda _repo: {"status": "PASS", "blockers": []})
    monkeypatch.setattr(boot_preflight, "collect_git_state", lambda _repo, **_kwargs: _clean_git_state())
    monkeypatch.setattr(boot_preflight, "_run_data_readiness_check", lambda _repo, _mode: _data_gate_status("FAIL"))
    monkeypatch.setattr(
        boot_preflight,
        "_run_pytest_gate",
        lambda *_args, **_kwargs: {"status": "PASS", "command": "pytest", "returncode": 0},
    )
    monkeypatch.setattr(
        boot_preflight,
        "write_boot_status_file",
        lambda _status, path, *, repo_root: writes.append(Path(path)) or "written",
    )

    args = boot_preflight.parse_args(["--repo-root", str(tmp_path), "--strict", "--write-status"])
    status, exit_code = boot_preflight.build_status(args)

    assert exit_code == 1
    assert status["status_write"]["result"] == "blocked-until-pass"
    assert writes == []


def test_data_readiness_gate_next_actions_are_not_boot_status_copy() -> None:
    raw_status = _data_gate_status("FAIL")
    raw_status["summary"]["next_actions"] = ["Fix checks before trusting research output."]

    sanitized = boot_preflight._boot_safe_data_readiness_status(raw_status)
    check = boot_preflight._check_from_data_readiness_gate(sanitized)

    assert "next_actions" not in sanitized["summary"]
    assert "next_actions" not in check.details["summary"]
    assert "research output" not in json.dumps(check.to_json_dict())


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


def test_no_boot_core_imports_for_deferred_dependency_modules() -> None:
    source = Path(boot_preflight.__file__).read_text(encoding="utf-8")

    assert "from scripts.governance_preflight" not in source
    assert "import scripts.governance_preflight" not in source
    assert "from core.data_readiness_gate import run_data_readiness_gate" in source


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
