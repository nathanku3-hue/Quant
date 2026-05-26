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
    BootContextFlags,
    BootStatus,
    ReadinessCheck,
    deferred_check,
    make_boot_status,
    write_boot_status_file,
)


SCHEMA_VERSION = "boot-preflight.v1"
DEFAULT_STATUS_JSON = BOOT_STATUS_CURRENT_PATH
DEFAULT_PYTEST_GATE_TIMEOUT_SECONDS = 180.0
BOOT_CONTROL_TEST_COMMAND = (
    "-m",
    "pytest",
    "tests/test_boot_preflight.py",
    "tests/test_boot_status_contract.py",
    "-q",
)
BOOT_CORE_REQUIRED_FILES = (
    "BOOT.md",
    "launch.py",
    "core/boot_status.py",
    "scripts/boot_preflight.py",
    "tests/test_boot_preflight.py",
    "tests/test_boot_status_contract.py",
    "docs/architecture/boot_preflight_contract.md",
    "docs/context/boot_status_current.schema.json",
)
DEFERRED_DEPENDENCY_CHECKS = (
    (
        "data_readiness_gate",
        "Data readiness gate",
        "Deferred from boot-core v0; stage data-readiness/governance in its own slice.",
    ),
    (
        "governance_preflight",
        "Governance boundary preflight",
        "Deferred from boot-core v0; no governance module is imported or executed by default.",
    ),
    (
        "context_packet_validation",
        "Context packet rebuild/validation",
        "Deferred from boot-core v0; context generation remains a separate governance step.",
    ),
    (
        "portfolio_apptest_smoke",
        "Portfolio AppTest smoke",
        "Deferred from boot-core v0; dashboard smoke must be approved as a later slice.",
    ),
    (
        "focused_replay_dashboard_contract",
        "Focused replay/dashboard contract",
        "Deferred from boot-core v0; replay/dashboard tests are not default boot-core gates.",
    ),
)

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
    if relative != "docs/context/boot_status_current.schema.json":
        return False, "schema path must be docs/context/boot_status_current.schema.json"
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
        if relative == "docs/context/boot_status_current.schema.json":
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


def collect_git_state(repo_root: Path) -> dict[str, Any]:
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
    aligned = bool(has_upstream and head_sha and upstream_sha and head_sha == upstream_sha and ahead == 0 and behind == 0)
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


def _check_from_gate(
    check_id: str,
    label: str,
    gate: Mapping[str, Any],
    *,
    destination: str = "Boot Status",
) -> ReadinessCheck:
    if gate.get("status") == "PASS":
        return ReadinessCheck(
            id=check_id,
            label=label,
            status="pass",
            severity="ready",
            summary=f"{label} passed.",
            evidence_ref=str(gate.get("command", "")) or None,
            destination=destination,
            details=dict(gate),
        )
    if gate.get("status") in {"SKIPPED", "DEFERRED"}:
        return ReadinessCheck(
            id=check_id,
            label=label,
            status="not_applicable" if gate.get("status") == "SKIPPED" else "deferred",
            severity="ready" if gate.get("status") == "SKIPPED" else "degraded",
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
        summary=f"{label} failed.",
        evidence_ref=str(gate.get("command", "")) or None,
        destination=destination,
        details=dict(gate),
    )


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
            summary="--require-github requires clean worktree and upstream-aligned HEAD.",
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
        summary="Git worktree is clean and HEAD matches upstream.",
        evidence_ref=str(git.get("head", "")) or None,
        destination="Boot Status",
        details=dict(git),
    )


def make_boot_status_from_preflight(preflight_status: Mapping[str, Any]) -> BootStatus:
    checks_payload = preflight_status.get("checks")
    checks_map = checks_payload if isinstance(checks_payload, Mapping) else {}
    boot_core = checks_map.get("boot_core", {})
    dirty = checks_map.get("dirty", {})
    boot_tests = checks_map.get("boot_control_tests", {})
    checks: list[ReadinessCheck] = [
        _check_from_gate("boot_core", "Boot-core file contract", boot_core if isinstance(boot_core, Mapping) else {}),
        _status_from_git(
            checks_map.get("git", {}) if isinstance(checks_map.get("git", {}), Mapping) else {},
            bool(preflight_status.get("require_github")),
        ),
        _check_from_gate("dirty_worktree", "Dirty worktree classification", dirty if isinstance(dirty, Mapping) else {}),
        _check_from_gate(
            "boot_control_tests",
            "Boot-control tests",
            boot_tests if isinstance(boot_tests, Mapping) else {},
        ),
    ]
    checks.extend(
        deferred_check(check_id, label, summary)
        for check_id, label, summary in DEFERRED_DEPENDENCY_CHECKS
    )
    flags = BootContextFlags(
        safe_boot=False,
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
            "deferred_scope": "data-readiness/governance/dashboard/replay/optimizer",
        },
    )


def _boot_status_json_text(preflight_status: Mapping[str, Any]) -> str:
    return make_boot_status_from_preflight(preflight_status).to_json_text()


def build_status(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    boot_core = validate_boot_core(repo_root)
    checks["boot_core"] = boot_core
    if boot_core["status"] != "PASS":
        failures.append("boot-core file contract failed")

    git_state = collect_git_state(repo_root)
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
            failures.append("--require-github requires HEAD to match upstream")

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

    for key, _label, summary in DEFERRED_DEPENDENCY_CHECKS:
        checks[key] = {"status": "DEFERRED", "reason": summary}
    if args.smoke:
        warnings.append("Portfolio AppTest smoke is deferred from boot-core v0 and was not run.")
    if args.run_focused_contract:
        warnings.append("Focused replay/dashboard contract is deferred from boot-core v0 and was not run.")

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
        post_git = collect_git_state(repo_root)
        status["post_git"] = post_git
        if not post_git.get("worktree_clean") or not post_git.get("aligned"):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append("--require-github post-check is not clean/aligned")

    if args.write_status:
        boot_status = make_boot_status_from_preflight(status)
        write_result = write_boot_status_file(boot_status, args.status_out, repo_root=repo_root)
        status["status_write"] = {"path": _normalize_path(args.status_out), "result": write_result}

    return status, int(status["exit_code"])


def render_human(status: Mapping[str, Any]) -> str:
    boot_status = make_boot_status_from_preflight(status)
    lines = [
        f"BOOT VERDICT: {status.get('verdict')}",
        f"Mode: {status.get('mode')}",
        f"Boot status: {boot_status.primary_verdict}",
    ]
    failures = status.get("failures") or []
    warnings = status.get("warnings") or []
    if failures:
        lines.append("Failures:")
        lines.extend(f"- {item}" for item in failures)
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in warnings)
    lines.append("Deferred:")
    for _check_id, label, _summary in DEFERRED_DEPENDENCY_CHECKS:
        lines.append(f"- {label}")
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal Zero boot-core preflight v0")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument("--mode", choices=("planning", "strict"), default="planning")
    parser.add_argument("--strict", action="store_true", help="Alias for --mode strict.")
    parser.add_argument("--require-github", action="store_true", help="Require clean upstream-aligned Git state.")
    parser.add_argument("--write-status", action="store_true", help="Write docs/context/boot_status_current.json.")
    parser.add_argument("--status-out", default=DEFAULT_STATUS_JSON.as_posix())
    parser.add_argument("--json", action="store_true", help="Print machine-readable preflight JSON.")
    parser.add_argument("--no-tests", action="store_true", help="Skip strict boot-control pytest gate.")
    parser.add_argument("--smoke", action="store_true", help="Accepted for compatibility; deferred in boot-core v0.")
    parser.add_argument(
        "--run-focused-contract",
        action="store_true",
        help="Accepted for compatibility; deferred in boot-core v0.",
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
