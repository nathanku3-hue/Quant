from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)

from core.boot_status import (
    BOOT_STATUS_CURRENT_PATH,
    BOOT_STATUS_SCHEMA_PATH,
    BootContextFlags,
    BootStatus,
    ReadinessCheck,
    checks_allow_safe_boot,
    make_boot_status,
)
from core.data_readiness_gate import run_data_readiness_gate
from scripts.governance_preflight import run_governance_preflight


SCHEMA_VERSION = "boot-preflight.v1"
DEFAULT_STATUS_JSON = BOOT_STATUS_CURRENT_PATH
DEFAULT_PYTEST_GATE_TIMEOUT_SECONDS = 180.0
DEFAULT_CONTEXT_GATE_TIMEOUT_SECONDS = 60.0
BOOT_CONTROL_TEST_COMMAND = (
    "-m",
    "pytest",
    "tests/test_boot_preflight.py",
    "tests/test_boot_status_contract.py",
    "tests/test_boot_preflight_governance.py",
    "-q",
)
PORTFOLIO_APPTEST_SMOKE_COMMAND = (
    "-m",
    "pytest",
    "tests/test_optimizer_view.py::test_optimizer_view_renders_with_streamlit_testing",
    "tests/test_optimizer_view.py::test_optimizer_view_exercises_mean_variance_and_sector_cap_controls",
    "-q",
)
FOCUSED_REPLAY_DASHBOARD_CONTRACT_COMMAND = (
    "-m",
    "pytest",
    "tests/test_dashboard_scanner_display.py",
    "tests/test_portfolio_universe.py::test_watch_is_research_only_by_default",
    "tests/test_dash_2_portfolio_ytd.py::test_dash_2_no_forbidden_runtime_scope",
    "-q",
)
CONTEXT_PACKET_VALIDATION_COMMAND = (
    "scripts/build_context_packet.py",
    "--validate",
)
BOOT_CORE_REQUIRED_FILES = (
    "BOOT.md",
    "launch.py",
    "core/boot_status.py",
    "opportunity_engine/candidate_card_schema.py",
    "scripts/boot_preflight.py",
    "scripts/governance_preflight.py",
    "tests/test_boot_preflight.py",
    "tests/test_boot_status_contract.py",
    "tests/test_boot_preflight_governance.py",
    "docs/architecture/boot_preflight_contract.md",
    "docs/architecture/governance_boundary_policy.md",
    BOOT_STATUS_SCHEMA_PATH.as_posix(),
)
SAFE_BOOT_REQUIRED_GATES = (
    "git_state",
    "governance_preflight",
    "boot_control_tests",
    "data_readiness_gate",
    "context_packet_validation",
    "portfolio_apptest_smoke",
    "focused_replay_dashboard_contract",
)
BOOT_STATUS_CHECK_ORDER = (
    "boot_core",
    "git_state",
    "dirty_worktree",
    "governance_preflight",
    "boot_control_tests",
    "data_readiness_gate",
    "context_packet_validation",
    "portfolio_apptest_smoke",
    "focused_replay_dashboard_contract",
)
GATE_LABELS = {
    "boot_core": "Boot-core file contract",
    "git_state": "Git state",
    "dirty_worktree": "Dirty worktree classification",
    "governance_preflight": "Governance preflight",
    "boot_control_tests": "Boot-control tests",
    "data_readiness_gate": "Data readiness gate",
    "context_packet_validation": "Context packet validation",
    "portfolio_apptest_smoke": "Portfolio AppTest smoke",
    "focused_replay_dashboard_contract": "Focused replay/dashboard contract",
}
GATE_STATUS_TO_CHECK_STATUS = {
    "PASS": "pass",
    "WARN": "warn",
    "SKIPPED": "not_applicable",
    "DEFERRED": "deferred",
    "FAIL": "fail",
}
GATE_STATUS_TO_SEVERITY = {
    "PASS": "ready",
    "WARN": "degraded",
    "SKIPPED": "degraded",
    "DEFERRED": "degraded",
    "FAIL": "blocked",
}
COMMAND_GATE_SKIP_REASONS = {
    "context_packet_validation": "Context packet validation runs only in strict mode.",
    "portfolio_apptest_smoke": "Portfolio AppTest smoke runs only when --smoke is supplied.",
    "focused_replay_dashboard_contract": "Focused replay/dashboard contract runs only when --run-focused-contract is supplied.",
}
COMMAND_GATE_PASS_SUMMARIES = {
    "context_packet_validation": "Existing context packet artifacts are fresh and schema-valid.",
    "portfolio_apptest_smoke": "Deterministic Portfolio AppTest smoke passed without status mutation.",
    "focused_replay_dashboard_contract": "Focused replay/dashboard governance contract passed.",
}

BOOT_CORE_SOURCE = set(BOOT_CORE_REQUIRED_FILES)
GENERATED_EVIDENCE_PATTERNS = (
    "docs/context/e2e_evidence/**",
    "docs/saw_reports/**",
    "**/*expert_packet*.zip",
    "**/*_stdout.txt",
    "**/*_stderr.txt",
    "**/*_pid.txt",
    "**/*_status.json",
)
IGNORE_PATTERNS = (
    ".pytest_cache/**",
    "__pycache__/**",
    "**/__pycache__/**",
)
SENSITIVE_PATTERNS = (
    "*.py",
    "core/**",
    "dashboard.py",
    "data/**/*.py",
    "launch.py",
    "opportunity_engine/**",
    "pyproject.toml",
    "requirements*.txt",
    "scripts/**",
    "strategies/**",
    "tests/**",
    "views/**",
)


@dataclass(frozen=True)
class CommandResult:
    args: Sequence[str] | str
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class DirtyEntry:
    status: str
    path: str


@dataclass(frozen=True)
class DirtyClassification:
    status: str
    path: str
    bucket: str
    severity: str
    reason: str


class PreflightConfigError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_path(path: str | Path) -> str:
    raw = str(path).replace(os.sep, "/")
    while raw.startswith("./"):
        raw = raw[2:]
    return raw


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def classify_path(path: str) -> tuple[str, str, str]:
    normalized = _normalize_path(path)
    if normalized in BOOT_CORE_SOURCE:
        return "boot-core-candidate", "advisory", "approved boot-core v0 file"
    if _matches(normalized, IGNORE_PATTERNS):
        return "ignore", "advisory", "local runtime/temp output"
    if _matches(normalized, GENERATED_EVIDENCE_PATTERNS):
        return "generated-evidence", "advisory", "generated context/evidence packet or runtime capture"
    if normalized.startswith("docs/context/") or normalized.startswith("docs/architecture/"):
        return "context-governance", "advisory", "docs/context or architecture governance surface"
    if _matches(normalized, SENSITIVE_PATTERNS):
        return "unclassified-source", "fail", "unclassified source/test/runtime file"
    return "unclassified-advisory", "advisory", "unclassified non-runtime file"


def classify_dirty_entries(entries: Sequence[DirtyEntry]) -> dict[str, Any]:
    classifications: list[DirtyClassification] = []
    for entry in entries:
        bucket, severity, reason = classify_path(entry.path)
        classifications.append(
            DirtyClassification(
                status=entry.status,
                path=_normalize_path(entry.path),
                bucket=bucket,
                severity=severity,
                reason=reason,
            )
        )
    counts: dict[str, int] = {}
    for item in classifications:
        counts[item.bucket] = counts.get(item.bucket, 0) + 1
    blockers = [item for item in classifications if item.severity == "fail"]
    warnings = [item for item in classifications if item.severity != "fail"]
    dirty_state = "clean" if not classifications else "classified"
    if blockers:
        dirty_state = "unclassified-source"
    return {
        "status": "FAIL" if blockers else "PASS",
        "dirty_state": dirty_state,
        "counts": counts,
        "blockers": [item.__dict__ for item in blockers],
        "warnings": [item.__dict__ for item in warnings],
        "classifications": [item.__dict__ for item in classifications],
    }


def _run_command(
    args: Sequence[str] | str,
    *,
    cwd: Path,
    shell: bool = False,
    timeout: float | None = None,
) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            shell=shell,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return CommandResult(args=args, returncode=127, stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CommandResult(
            args=args,
            returncode=124,
            stdout=stdout,
            stderr=stderr or f"Command timed out after {timeout} seconds",
        )
    return CommandResult(
        args=args,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _python_command(parts: Sequence[str]) -> list[str]:
    return [sys.executable, *parts]


def _tail(text: str, limit: int = 2000) -> str:
    return text[-limit:] if len(text) > limit else text


def _file_signature(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = path.stat()
    return {"sha256": digest.hexdigest(), "size_bytes": stat.st_size}


def _validate_status_schema_file(repo_root: Path, schema_path: Path) -> tuple[bool, str]:
    try:
        payload = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"schema JSON is unreadable: {exc}"
    if not isinstance(payload, dict):
        return False, "schema JSON must be an object"
    properties = payload.get("properties", {})
    checks = properties.get("checks", {}) if isinstance(properties, dict) else {}
    items = checks.get("items", {}) if isinstance(checks, dict) else {}
    check_properties = items.get("properties", {}) if isinstance(items, dict) else {}
    status_enum = check_properties.get("status", {}).get("enum", [])
    required_statuses = {"pass", "warn", "fail", "not_applicable", "deferred"}
    if not required_statuses.issubset(set(status_enum)):
        return False, "schema check status enum is missing boot-core statuses"
    if properties.get("schema_version", {}).get("const") != "boot-status/v1":
        return False, "schema_version const must be boot-status/v1"
    try:
        relative = schema_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return False, "schema path must stay inside repository"
    if relative != BOOT_STATUS_SCHEMA_PATH.as_posix():
        return False, f"schema path must be {BOOT_STATUS_SCHEMA_PATH.as_posix()}"
    return True, "schema JSON matches boot-core v0 status vocabulary"


def validate_boot_core(repo_root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    blockers: list[str] = []
    for relative in BOOT_CORE_REQUIRED_FILES:
        path = repo_root / relative
        if not path.exists():
            blockers.append(f"missing:{relative}")
            files.append({"path": relative, "status": "missing"})
            continue
        if not path.is_file():
            blockers.append(f"not_file:{relative}")
            files.append({"path": relative, "status": "not_file"})
            continue
        entry: dict[str, Any] = {"path": relative, "status": "present", "signature": _file_signature(path)}
        if relative == BOOT_STATUS_SCHEMA_PATH.as_posix():
            ok, summary = _validate_status_schema_file(repo_root, path)
            entry["schema_validation"] = "PASS" if ok else "FAIL"
            entry["schema_summary"] = summary
            if not ok:
                blockers.append(f"invalid_schema:{summary}")
        files.append(entry)
    return {
        "status": "PASS" if not blockers else "FAIL",
        "required_files": list(BOOT_CORE_REQUIRED_FILES),
        "files": files,
        "blockers": blockers,
    }


def _parse_porcelain_z(stdout: str) -> list[DirtyEntry]:
    entries: list[DirtyEntry] = []
    raw_entries = [part for part in stdout.split("\0") if part]
    idx = 0
    while idx < len(raw_entries):
        raw = raw_entries[idx]
        if len(raw) < 4:
            idx += 1
            continue
        status = raw[:2].strip() or raw[:2]
        path = raw[3:]
        if raw[0] in {"R", "C"} or raw[1] in {"R", "C"}:
            idx += 1
        entries.append(DirtyEntry(status=status, path=path))
        idx += 1
    return entries


def _git(repo_root: Path, *args: str) -> CommandResult:
    return _run_command(["git", *args], cwd=repo_root)


def _expected_refspec(expected_ref: str | None) -> str:
    ref = (expected_ref or "").strip()
    if not ref:
        return ""
    if ref.startswith("refs/heads/"):
        return ref
    return f"refs/heads/{ref}"


def _collect_expected_remote_proof(
    repo_root: Path,
    *,
    head_sha: str,
    expected_ref: str | None,
    expected_sha: str | None,
) -> dict[str, Any]:
    refspec = _expected_refspec(expected_ref)
    expected_sha = (expected_sha or "").strip()
    proof: dict[str, Any] = {
        "requested": bool(refspec or expected_sha),
        "expected_ref": (expected_ref or "").strip(),
        "expected_refspec": refspec,
        "expected_sha": expected_sha,
        "remote": "origin",
        "remote_sha": "",
        "remote_ref_found": None,
        "local_head_matches_remote": None,
        "local_head_matches_expected_sha": None,
        "remote_matches_expected_sha": None,
        "aligned": False,
        "proof_available": False,
        "reason": "not_requested",
    }
    if not proof["requested"]:
        return proof
    if not refspec or not expected_sha:
        proof["reason"] = "expected_ref_and_sha_required"
        if expected_sha:
            proof["local_head_matches_expected_sha"] = bool(head_sha and head_sha == expected_sha)
        return proof
    if expected_sha:
        proof["local_head_matches_expected_sha"] = bool(head_sha and head_sha == expected_sha)
    if refspec:
        remote = _git(repo_root, "ls-remote", "origin", refspec)
        proof["ls_remote_returncode"] = remote.returncode
        proof["ls_remote_stdout"] = _tail(remote.stdout, 1000)
        proof["ls_remote_stderr"] = _tail(remote.stderr, 1000)
        if remote.returncode == 0:
            parts = remote.stdout.strip().split()
            remote_sha = parts[0] if len(parts) >= 2 else ""
            proof["remote_sha"] = remote_sha
            proof["remote_ref_found"] = bool(remote_sha)
            proof["local_head_matches_remote"] = bool(head_sha and remote_sha and head_sha == remote_sha)
            if expected_sha:
                proof["remote_matches_expected_sha"] = bool(remote_sha and remote_sha == expected_sha)
        else:
            proof["remote_ref_found"] = False
            proof["reason"] = "ls_remote_failed"
            return proof
    proof["proof_available"] = bool(refspec and proof.get("remote_ref_found"))
    if not proof["proof_available"]:
        proof["reason"] = "remote_ref_missing"
        return proof
    proof["aligned"] = bool(
        proof.get("local_head_matches_remote")
        and proof.get("local_head_matches_expected_sha")
        and proof.get("remote_matches_expected_sha")
    )
    if proof["aligned"]:
        proof["reason"] = "expected_ref_sha_aligned"
    elif not proof.get("local_head_matches_expected_sha"):
        proof["reason"] = "local_head_mismatch"
    elif not proof.get("remote_matches_expected_sha"):
        proof["reason"] = "remote_sha_mismatch"
    else:
        proof["reason"] = "local_remote_mismatch"
    return proof


def collect_git_state(
    repo_root: Path,
    *,
    expected_ref: str | None = None,
    expected_sha: str | None = None,
) -> dict[str, Any]:
    inside = _git(repo_root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "available": False,
            "status": "WARN",
            "reason": (inside.stderr or inside.stdout or "not a Git worktree").strip(),
            "entries": [],
            "worktree_clean": None,
            "aligned": None,
        }
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    head = _git(repo_root, "rev-parse", "HEAD")
    upstream = _git(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream_head = _git(repo_root, "rev-parse", "@{u}")
    ahead_behind = _git(repo_root, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    status = _git(repo_root, "status", "--porcelain=v1", "-z")
    entries = _parse_porcelain_z(status.stdout if status.returncode == 0 else "")
    upstream_name = upstream.stdout.strip() if upstream.returncode == 0 else ""
    head_sha = head.stdout.strip() if head.returncode == 0 else ""
    upstream_sha = upstream_head.stdout.strip() if upstream_head.returncode == 0 else ""
    ahead = behind = None
    if ahead_behind.returncode == 0:
        parts = ahead_behind.stdout.strip().split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])
    has_upstream = bool(upstream_name and upstream_sha)
    upstream_aligned = bool(has_upstream and head_sha and upstream_sha and head_sha == upstream_sha and ahead == 0 and behind == 0)
    expected_remote_proof = _collect_expected_remote_proof(
        repo_root,
        head_sha=head_sha,
        expected_ref=expected_ref,
        expected_sha=expected_sha,
    )
    aligned = bool(upstream_aligned or expected_remote_proof.get("aligned"))
    return {
        "available": True,
        "status": "PASS",
        "branch": branch.stdout.strip() if branch.returncode == 0 else "",
        "head": head_sha,
        "upstream": upstream_name,
        "upstream_head": upstream_sha,
        "ahead": ahead,
        "behind": behind,
        "has_upstream": has_upstream,
        "aligned": aligned,
        "upstream_aligned": upstream_aligned,
        "expected_remote_proof": expected_remote_proof,
        "worktree_clean": not entries,
        "entries": [entry.__dict__ for entry in entries],
    }


def _run_pytest_gate(
    repo_root: Path,
    command_parts: tuple[str, ...],
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    result = _run_command(_python_command(command_parts), cwd=repo_root, timeout=timeout)
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": " ".join(_python_command(command_parts)),
        "returncode": result.returncode,
        "stdout_tail": _tail(result.stdout),
        "stderr_tail": _tail(result.stderr),
    }


def _run_script_gate(
    repo_root: Path,
    command_parts: tuple[str, ...],
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    result = _run_command(_python_command(command_parts), cwd=repo_root, timeout=timeout)
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": " ".join(_python_command(command_parts)),
        "returncode": result.returncode,
        "stdout_tail": _tail(result.stdout),
        "stderr_tail": _tail(result.stderr),
    }


def _run_data_readiness_gate_check(repo_root: Path, mode: str) -> dict[str, Any]:
    command = "core.data_readiness_gate.run_data_readiness_gate(read_only=True)"
    try:
        status = run_data_readiness_gate(repo_root, mode=mode)
    except Exception as exc:
        return {
            "status": "FAIL",
            "command": command,
            "summary": f"Data readiness gate failed to run: {exc}",
            "details": {"exception": repr(exc), "read_only": True},
        }
    raw_status = str(status.get("overall_status", "FAIL")).strip().upper()
    if raw_status == "PASS":
        gate_status = "PASS"
        summary = "Data readiness gate passed."
    elif raw_status in {"WARN", "DEFER", "DEFERRED"}:
        gate_status = "WARN"
        summary = "Data readiness gate is degraded or uncertified."
    else:
        gate_status = "FAIL"
        summary = "Data readiness gate failed."
    summary_payload = status.get("summary") if isinstance(status.get("summary"), Mapping) else {}
    blockers = summary_payload.get("blockers", []) if isinstance(summary_payload, Mapping) else []
    warnings = summary_payload.get("warnings", []) if isinstance(summary_payload, Mapping) else []
    if gate_status == "FAIL" and blockers:
        summary = f"Data readiness gate failed: {len(blockers)} blocker(s)."
    elif gate_status == "WARN" and warnings:
        summary = f"Data readiness gate warned: {len(warnings)} warning(s)."
    return {
        "status": gate_status,
        "command": command,
        "summary": summary,
        "details": {
            "overall_status": raw_status,
            "planning_status": status.get("planning_status"),
            "strict_status": status.get("strict_status"),
            "mode": status.get("mode"),
            "route_id": status.get("route_id"),
            "route_readiness": status.get("route_readiness"),
            "summary": {
                "blockers": list(blockers) if isinstance(blockers, list) else [],
                "warnings": list(warnings) if isinstance(warnings, list) else [],
            },
            "read_only": True,
        },
    }


def _skipped_gate(check_id: str) -> dict[str, Any]:
    return {
        "status": "SKIPPED",
        "reason": COMMAND_GATE_SKIP_REASONS[check_id],
    }


def _check_from_gate(
    check_id: str,
    label: str,
    gate: Mapping[str, Any],
    *,
    destination: str = "Boot Status",
) -> ReadinessCheck:
    gate_status = str(gate.get("status", "FAIL")).upper()
    summary = str(gate.get("summary") or gate.get("reason") or "")
    if gate_status == "PASS":
        return ReadinessCheck(
            id=check_id,
            label=label,
            status="pass",
            severity="ready",
            summary=summary or f"{label} passed.",
            evidence_ref=str(gate.get("command", "")) or None,
            destination=destination,
            details=dict(gate),
        )
    if gate_status == "WARN":
        return ReadinessCheck(
            id=check_id,
            label=label,
            status="warn",
            severity="degraded",
            summary=summary or f"{label} reported warnings.",
            evidence_ref=str(gate.get("command", "")) or None,
            destination=destination,
            details=dict(gate),
        )
    if gate_status in {"SKIPPED", "DEFERRED"}:
        return ReadinessCheck(
            id=check_id,
            label=label,
            status="not_applicable" if gate_status == "SKIPPED" else "deferred",
            severity="degraded",
            summary=str(gate.get("reason", f"{label} was not run.")),
            evidence_ref=str(gate.get("command", "")) or None,
            destination=destination,
            details=dict(gate),
        )
    return ReadinessCheck(
        id=check_id,
        label=label,
        status="fail",
        severity="blocked",
        summary=summary or f"{label} failed.",
        evidence_ref=str(gate.get("command", "")) or None,
        destination=destination,
        details=dict(gate),
    )


def _github_alignment_failure(git: Mapping[str, Any], *, post_check: bool = False) -> str:
    prefix = "--require-github post-check" if post_check else "--require-github"
    proof = git.get("expected_remote_proof", {})
    proof_requested = bool(isinstance(proof, Mapping) and proof.get("requested"))
    if git.get("has_upstream") and not proof_requested:
        ahead = git.get("ahead")
        behind = git.get("behind")
        return f"{prefix} upstream mismatch:ahead={ahead},behind={behind}"
    if proof_requested:
        reason = str(proof.get("reason") or "unknown") if isinstance(proof, Mapping) else "unknown"
        if isinstance(proof, Mapping) and not proof.get("proof_available"):
            return f"{prefix} proof_unavailable:{reason}"
        return f"{prefix} expected ref/SHA proof failed:{reason}"
    return f"{prefix} proof_unavailable:no upstream or explicit expected ref/SHA"


def _status_from_git(git: Mapping[str, Any], require_github: bool) -> ReadinessCheck:
    if not git.get("available"):
        severity = "blocked" if require_github else "degraded"
        return ReadinessCheck(
            id="git_state",
            label="Git state",
            status="fail" if require_github else "warn",
            severity=severity,
            summary=str(git.get("reason", "Git state unavailable.")),
            destination="Boot Status",
            details=dict(git),
        )
    if require_github and (not git.get("worktree_clean") or not git.get("aligned")):
        return ReadinessCheck(
            id="git_state",
            label="Git state",
            status="fail",
            severity="blocked",
            summary=_github_alignment_failure(git),
            evidence_ref=str(git.get("head", "")) or None,
            destination="Boot Status",
            details=dict(git),
        )
    if not git.get("worktree_clean") or not git.get("aligned"):
        return ReadinessCheck(
            id="git_state",
            label="Git state",
            status="warn",
            severity="degraded",
            summary="Git is available, but the worktree or upstream alignment is not clean.",
            evidence_ref=str(git.get("head", "")) or None,
            destination="Boot Status",
            details=dict(git),
        )
    return ReadinessCheck(
        id="git_state",
        label="Git state",
        status="pass",
        severity="ready",
        summary="Git worktree is clean and HEAD matches GitHub proof.",
        evidence_ref=str(git.get("head", "")) or None,
        destination="Boot Status",
        details=dict(git),
    )


def _post_status_from_git(git: Mapping[str, Any], require_github: bool) -> ReadinessCheck:
    check = _status_from_git(git, require_github)
    summary = check.summary
    if check.status == "pass":
        summary = "Post-write Git check remains clean and aligned."
    elif check.status == "fail":
        summary = _github_alignment_failure(git, post_check=True)
    return ReadinessCheck(
        id="post_git_state",
        label="Post-write Git state",
        status=check.status,
        severity=check.severity,
        summary=summary,
        evidence_ref=check.evidence_ref,
        destination=check.destination,
        details=check.details,
    )


def _required_gate_ids(preflight_status: Mapping[str, Any]) -> tuple[str, ...]:
    return (
        (*SAFE_BOOT_REQUIRED_GATES, "post_git_state")
        if isinstance(preflight_status.get("checks"), Mapping)
        and "post_git" in preflight_status.get("checks", {})
        else SAFE_BOOT_REQUIRED_GATES
    )


def make_boot_status_from_preflight(preflight_status: Mapping[str, Any]) -> BootStatus:
    checks_payload = preflight_status.get("checks")
    checks_map = checks_payload if isinstance(checks_payload, Mapping) else {}
    checks: list[ReadinessCheck] = []
    for check_id in BOOT_STATUS_CHECK_ORDER:
        if check_id == "git_state":
            checks.append(
                _status_from_git(
                    checks_map.get("git", {}) if isinstance(checks_map.get("git", {}), Mapping) else {},
                    bool(preflight_status.get("require_github")),
                )
            )
            continue
        key = "dirty" if check_id == "dirty_worktree" else "governance" if check_id == "governance_preflight" else check_id
        gate = checks_map.get(key, {})
        checks.append(_check_from_gate(check_id, GATE_LABELS[check_id], gate if isinstance(gate, Mapping) else {}))
    if isinstance(checks_map.get("post_git"), Mapping):
        checks.append(_post_status_from_git(checks_map["post_git"], bool(preflight_status.get("require_github"))))
    required_gate_ids = _required_gate_ids(preflight_status)
    check_by_id = {check.id: check for check in checks}
    required_checks = [check_by_id[check_id] for check_id in required_gate_ids if check_id in check_by_id]
    safe_boot = (
        preflight_status.get("mode") == "strict"
        and bool(preflight_status.get("require_github"))
        and preflight_status.get("verdict") == "PASS"
        and len(required_checks) == len(required_gate_ids)
        and checks_allow_safe_boot(required_checks)
    )
    flags = BootContextFlags(
        safe_boot=safe_boot,
        boot_candidate=preflight_status.get("mode") == "strict" and preflight_status.get("verdict") == "PASS",
        local_planning=preflight_status.get("mode") == "planning",
    )
    return make_boot_status(
        source="scripts.boot_preflight",
        flags=flags,
        checks=checks,
        generated_at=str(preflight_status.get("generated_at_utc") or _utc_now()),
        git_commit=(checks_map.get("git", {}) or {}).get("head") if isinstance(checks_map.get("git", {}), Mapping) else None,
        warnings=tuple(str(item) for item in preflight_status.get("warnings", [])),
        metadata={
            "preflight_schema_version": preflight_status.get("schema_version"),
            "mode": preflight_status.get("mode"),
            "require_github": preflight_status.get("require_github"),
            "safe_boot_required_gates": list(required_gate_ids),
            "deferred_scope": [],
        },
    )


def _boot_status_json_text(preflight_status: Mapping[str, Any]) -> str:
    return make_boot_status_from_preflight(preflight_status).to_json_text()


def _resolve_boot_status_target(path: str | Path, repo_root: Path) -> Path:
    target = Path(path)
    resolved = target if target.is_absolute() else repo_root / target
    try:
        relative = resolved.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise PreflightConfigError("boot status output must stay inside repository") from exc
    if relative != BOOT_STATUS_CURRENT_PATH.as_posix():
        raise PreflightConfigError(
            f"boot status output must be {BOOT_STATUS_CURRENT_PATH.as_posix()}; got {relative}"
        )
    return resolved


def _write_boot_status_file(status: BootStatus, path: str | Path, *, repo_root: Path) -> str:
    target = _resolve_boot_status_target(path, repo_root)
    text = status.to_json_text()
    existing = target.read_text(encoding="utf-8") if target.exists() else None
    if existing == text:
        return "unchanged"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return "written"


def build_status(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    boot_core = validate_boot_core(repo_root)
    checks["boot_core"] = boot_core
    if boot_core["status"] != "PASS":
        failures.append("boot-core file contract failed")

    git_state = collect_git_state(
        repo_root,
        expected_ref=args.expected_ref,
        expected_sha=args.expected_sha,
    )
    governance_result = run_governance_preflight(repo_root).to_dict()
    checks["governance"] = governance_result
    if governance_result["status"] == "FAIL":
        failures.append("governance preflight did not pass: FAIL")
    elif governance_result["status"] == "WARN":
        warnings.append("governance preflight warning")

    checks["git"] = git_state
    dirty_entries = [DirtyEntry(**entry) for entry in git_state.get("entries", [])]
    dirty = classify_dirty_entries(dirty_entries)
    checks["dirty"] = dirty
    if dirty["status"] != "PASS":
        failures.append("unclassified source/test/runtime dirty files are present")

    if args.require_github:
        if not git_state.get("available"):
            failures.append("--require-github requires a Git worktree")
        if not git_state.get("worktree_clean"):
            failures.append("--require-github requires a clean worktree")
        if not git_state.get("aligned"):
            failures.append(_github_alignment_failure(git_state))

    if args.mode == "strict" and not args.no_tests:
        checks["boot_control_tests"] = _run_pytest_gate(
            repo_root,
            BOOT_CONTROL_TEST_COMMAND,
            timeout=DEFAULT_PYTEST_GATE_TIMEOUT_SECONDS,
        )
        if checks["boot_control_tests"]["status"] != "PASS":
            failures.append("boot-control tests failed")
    else:
        checks["boot_control_tests"] = {
            "status": "SKIPPED",
            "reason": "boot-control tests run only in strict mode unless --no-tests is used",
            "command": " ".join(_python_command(BOOT_CONTROL_TEST_COMMAND)),
        }

    checks["data_readiness_gate"] = _run_data_readiness_gate_check(repo_root, args.mode)
    if checks["data_readiness_gate"]["status"] == "FAIL":
        failures.append("data-readiness gate did not pass: FAIL")
    elif checks["data_readiness_gate"]["status"] != "PASS":
        warnings.append("data-readiness gate is degraded")

    if args.mode == "strict" and not args.no_tests:
        checks["context_packet_validation"] = _run_script_gate(
            repo_root,
            CONTEXT_PACKET_VALIDATION_COMMAND,
            timeout=DEFAULT_CONTEXT_GATE_TIMEOUT_SECONDS,
        )
        if checks["context_packet_validation"]["status"] == "PASS":
            checks["context_packet_validation"]["summary"] = COMMAND_GATE_PASS_SUMMARIES["context_packet_validation"]
        else:
            failures.append("context packet validation failed")
    else:
        checks["context_packet_validation"] = _skipped_gate("context_packet_validation")

    if args.smoke:
        checks["portfolio_apptest_smoke"] = _run_pytest_gate(
            repo_root,
            PORTFOLIO_APPTEST_SMOKE_COMMAND,
            timeout=DEFAULT_PYTEST_GATE_TIMEOUT_SECONDS,
        )
        if checks["portfolio_apptest_smoke"]["status"] == "PASS":
            checks["portfolio_apptest_smoke"]["summary"] = COMMAND_GATE_PASS_SUMMARIES["portfolio_apptest_smoke"]
        else:
            failures.append("Portfolio AppTest smoke failed")
    else:
        checks["portfolio_apptest_smoke"] = _skipped_gate("portfolio_apptest_smoke")

    if args.run_focused_contract:
        checks["focused_replay_dashboard_contract"] = _run_pytest_gate(
            repo_root,
            FOCUSED_REPLAY_DASHBOARD_CONTRACT_COMMAND,
            timeout=DEFAULT_PYTEST_GATE_TIMEOUT_SECONDS,
        )
        if checks["focused_replay_dashboard_contract"]["status"] == "PASS":
            checks["focused_replay_dashboard_contract"]["summary"] = COMMAND_GATE_PASS_SUMMARIES[
                "focused_replay_dashboard_contract"
            ]
        else:
            failures.append("focused replay/dashboard contract failed")
    else:
        checks["focused_replay_dashboard_contract"] = _skipped_gate("focused_replay_dashboard_contract")

    if checks["portfolio_apptest_smoke"]["status"] == "SKIPPED":
        warnings.append(COMMAND_GATE_SKIP_REASONS["portfolio_apptest_smoke"])
    if checks["focused_replay_dashboard_contract"]["status"] == "SKIPPED":
        warnings.append(COMMAND_GATE_SKIP_REASONS["focused_replay_dashboard_contract"])

    status: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "mode": args.mode,
        "require_github": bool(args.require_github),
        "verdict": "FAIL" if failures else "PASS",
        "exit_code": 1 if failures else 0,
        "failures": failures,
        "warnings": warnings,
        "checks": checks,
    }

    if args.require_github:
        post_git = collect_git_state(
            repo_root,
            expected_ref=args.expected_ref,
            expected_sha=args.expected_sha,
        )
        status["post_git"] = post_git
        status["checks"]["post_git"] = post_git
        if not post_git.get("worktree_clean"):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append("--require-github post-check requires a clean worktree")
        if not post_git.get("aligned"):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append(_github_alignment_failure(post_git, post_check=True))

    write_allowed = (
        status["verdict"] == "PASS"
        and args.mode == "strict"
        and args.require_github
        and not args.no_tests
        and args.smoke
        and args.run_focused_contract
        and make_boot_status_from_preflight(status).flags.safe_boot
    )
    if args.write_status and write_allowed:
        boot_status = make_boot_status_from_preflight(status)
        write_result = _write_boot_status_file(boot_status, args.status_out, repo_root=repo_root)
        status["status_write"] = {"path": _normalize_path(args.status_out), "result": write_result}
    elif args.write_status:
        status["status_write"] = {"path": _normalize_path(args.status_out), "result": "blocked-until-pass"}

    if args.require_github:
        final_git = collect_git_state(
            repo_root,
            expected_ref=args.expected_ref,
            expected_sha=args.expected_sha,
        )
        status["final_git"] = final_git
        if not final_git.get("worktree_clean"):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append("--require-github final post-write check requires a clean worktree")
        if not final_git.get("aligned"):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append(_github_alignment_failure(final_git, post_check=True))

    return status, int(status["exit_code"])


def render_human(status: Mapping[str, Any]) -> str:
    boot_status = make_boot_status_from_preflight(status)
    boot_checks = {check.id: check for check in boot_status.checks}
    lines = [
        f"BOOT VERDICT: {status.get('verdict')}",
        f"Mode: {status.get('mode')}",
        f"Boot status: {boot_status.primary_verdict}",
        f"Safe boot: {str(boot_status.flags.safe_boot).lower()}",
    ]
    failures = status.get("failures") or []
    warnings = status.get("warnings") or []
    if failures:
        lines.append("Failures:")
        lines.extend(f"- {item}" for item in failures)
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in warnings)
    lines.append("Safe-boot gates:")
    for check_id in SAFE_BOOT_REQUIRED_GATES:
        check = boot_checks.get(check_id)
        effective_status = check.status.upper() if check else "MISSING"
        lines.append(f"- {GATE_LABELS[check_id]}: {effective_status}")
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal Zero boot-core preflight v0")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument("--mode", choices=("planning", "strict"), default="planning")
    parser.add_argument("--strict", action="store_true", help="Alias for --mode strict.")
    parser.add_argument("--require-github", action="store_true", help="Require clean upstream-aligned Git state.")
    parser.add_argument(
        "--expected-ref",
        help="Remote branch name or refs/heads/* ref used as explicit GitHub proof in detached worktrees.",
    )
    parser.add_argument(
        "--expected-sha",
        help="Expected commit SHA used as explicit GitHub proof in detached worktrees.",
    )
    parser.add_argument(
        "--write-status",
        action="store_true",
        help=f"Write {BOOT_STATUS_CURRENT_PATH.as_posix()}.",
    )
    parser.add_argument("--status-out", default=DEFAULT_STATUS_JSON.as_posix())
    parser.add_argument("--json", action="store_true", help="Print machine-readable preflight JSON.")
    parser.add_argument("--no-tests", action="store_true", help="Skip strict boot-control pytest gate.")
    parser.add_argument("--smoke", action="store_true", help="Run deterministic Portfolio AppTest smoke gate.")
    parser.add_argument(
        "--run-focused-contract",
        action="store_true",
        help="Run focused replay/dashboard governance contract gate.",
    )
    args = parser.parse_args(argv)
    if args.strict:
        args.mode = "strict"
    return args


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        status, exit_code = build_status(args)
    except PreflightConfigError as exc:
        print(f"Boot preflight configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Boot preflight internal error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_human(status), end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
