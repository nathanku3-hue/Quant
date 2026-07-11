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
    deferred_check,
    make_boot_status,
)
from scripts.governance_preflight import run_governance_preflight


SCHEMA_VERSION = "boot-preflight.v1"
DEFAULT_STATUS_JSON = BOOT_STATUS_CURRENT_PATH
DEFAULT_PYTEST_GATE_TIMEOUT_SECONDS = 180.0
BOOT_CONTROL_TEST_COMMAND = (
    "-m",
    "pytest",
    "tests/test_boot_preflight.py",
    "tests/test_boot_status_contract.py",
    "tests/test_boot_preflight_governance.py",
    "-q",
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
DEFERRED_DEPENDENCY_CHECKS = (
    (
        "data_readiness_gate",
        "Data readiness gate",
        "Deferred from boot-core v0; stage data-readiness in its own slice.",
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
GIT_IDENTITY_REDIRECTION_ENVIRONMENT_VARIABLES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
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
        "dirt_scope": "superproject_porcelain",
    }


def build_dirty_check(
    *,
    status_command_ok: bool,
    entries: Sequence[DirtyEntry],
    total_gitlinks: int,
) -> dict[str, Any]:
    """Classify superproject dirty state without lying about remaining gitlinks.

    Plain dirty_state ``clean`` is allowed only when status succeeded, porcelain is
    empty, and the index contains zero mode-160000 gitlinks. Empty porcelain with
    remaining gitlinks is ``clean_superproject_only`` (never plain clean).
    """
    base = {
        "dirt_scope": "superproject_porcelain",
        "status_ignore_submodules": "all",
        "status_command_ok": bool(status_command_ok),
        "total_gitlinks": int(total_gitlinks),
    }
    if not status_command_ok:
        return {
            **base,
            "status": "FAIL",
            "dirty_state": "STATUS_UNAVAILABLE",
            "counts": {},
            "blockers": [],
            "warnings": [],
            "classifications": [],
            "reason": "git status command failed; dirty state cannot be claimed clean",
        }
    if entries:
        classified = classify_dirty_entries(entries)
        classified.update(base)
        return classified
    if total_gitlinks > 0:
        return {
            **base,
            "status": "FAIL",
            "dirty_state": "clean_superproject_only",
            "counts": {},
            "blockers": [],
            "warnings": [],
            "classifications": [],
            "reason": (
                "superproject porcelain is empty but index still contains gitlinks; "
                "not a full-tree clean state"
            ),
        }
    return {
        **base,
        "status": "PASS",
        "dirty_state": "clean",
        "counts": {},
        "blockers": [],
        "warnings": [],
        "classifications": [],
    }


def _run_command(
    args: Sequence[str] | str,
    *,
    cwd: Path,
    shell: bool = False,
    timeout: float | None = None,
    env: Mapping[str, str] | None = None,
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
            env=dict(env) if env is not None else None,
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
    environment = os.environ.copy()
    for name in GIT_IDENTITY_REDIRECTION_ENVIRONMENT_VARIABLES:
        environment.pop(name, None)
    for name in tuple(environment):
        if name.startswith("GIT_CONFIG_"):
            environment.pop(name, None)
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    return _run_command(["git", *args], cwd=repo_root, env=environment)


def _replacement_refs(repo_root: Path) -> tuple[str, list[str], str]:
    result = _git(repo_root, "for-each-ref", "--format=%(refname)", "refs/replace/")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Git replacement-ref enumeration failed").strip()
        return "ERROR", [], detail
    refs = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if refs:
        return "DETECTED", refs, "Git replacement refs are present; identity verification is refused."
    return "CLEAR", [], ""


def _is_git_object_id(value: str) -> bool:
    return len(value) in {40, 64} and all(character in "0123456789abcdef" for character in value)


def _failed_git_identity_state(
    *,
    replacement_refs_status: str,
    replacement_refs: Sequence[str],
    reason: str,
    identity_errors: Sequence[str],
    branch: str = "",
    head: str = "",
    tree: str = "",
    upstream: str = "",
    upstream_head: str = "",
    ahead: int | None = None,
    behind: int | None = None,
    has_upstream: bool = False,
    aligned: bool | None = None,
    worktree_clean: bool | None = None,
    entries: Sequence[Mapping[str, Any]] | None = None,
    status_command_ok: bool | None = None,
    status_ignore_submodules: str | None = None,
    dirt_scope: str | None = None,
    gitlinks: Mapping[str, Any] | None = None,
    dirt_complete: bool | None = None,
) -> dict[str, Any]:
    """Identity FAIL payload that preserves every successfully collected field."""
    payload: dict[str, Any] = {
        "available": True,
        "status": "FAIL",
        "reason": reason,
        "replacement_refs_status": replacement_refs_status,
        "replacement_refs": list(replacement_refs),
        "identity_verified": False,
        "identity_errors": list(identity_errors),
        "branch": branch,
        "head": head,
        "tree": tree,
        "upstream": upstream,
        "upstream_head": upstream_head,
        "ahead": ahead,
        "behind": behind,
        "has_upstream": has_upstream,
        "aligned": aligned,
        "worktree_clean": worktree_clean,
        "entries": list(entries) if entries is not None else [],
    }
    if status_command_ok is not None:
        payload["status_command_ok"] = status_command_ok
    if status_ignore_submodules is not None:
        payload["status_ignore_submodules"] = status_ignore_submodules
    if dirt_scope is not None:
        payload["dirt_scope"] = dirt_scope
    if gitlinks is not None:
        payload["gitlinks"] = dict(gitlinks)
    if dirt_complete is not None:
        payload["dirt_complete"] = dirt_complete
    return payload


def _parse_ls_files_stage_z(stdout: str) -> list[dict[str, Any]]:
    """Parse ``git ls-files -s -z`` records; paths may contain spaces."""
    records: list[dict[str, Any]] = []
    for raw in stdout.split("\0"):
        if not raw:
            continue
        # Format: <mode> SP <object> SP <stage> TAB <path>
        tab = raw.find("\t")
        if tab < 0:
            continue
        meta = raw[:tab]
        path = raw[tab + 1 :]
        parts = meta.split(" ")
        if len(parts) != 3:
            continue
        mode, object_id, stage_text = parts
        try:
            stage = int(stage_text)
        except ValueError:
            continue
        records.append(
            {
                "mode": mode,
                "object": object_id,
                "stage": stage,
                "path": path,
            }
        )
    return records


def _parse_gitmodules_paths(repo_root: Path) -> tuple[str, set[str], str]:
    """Return (status, registered_paths, reason). Fail-closed when unreadable."""
    path = repo_root / ".gitmodules"
    if not path.exists():
        return "ABSENT", set(), "no .gitmodules; no gitlinks are registered"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return "UNREADABLE", set(), f".gitmodules unreadable: {exc}"
    registered: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.lower().startswith("path"):
            continue
        # path = foo/bar
        if "=" not in stripped:
            return "MALFORMED", set(), ".gitmodules path line missing '='"
        _, value = stripped.split("=", 1)
        candidate = _normalize_path(value.strip())
        if not candidate:
            return "MALFORMED", set(), ".gitmodules path value empty"
        registered.add(candidate)
    return "OK", registered, "parsed .gitmodules paths"


def collect_gitlink_inventory(repo_root: Path) -> dict[str, Any]:
    """Enumerate index gitlinks with space-safe -z parse and unregistered check."""
    listed = _git(repo_root, "ls-files", "-s", "-z")
    if listed.returncode != 0:
        return {
            "status": "FAIL",
            "reason": (listed.stderr or listed.stdout or "git ls-files -s -z failed").strip(),
            "ls_files_ok": False,
            "total_gitlinks": 0,
            "stage0_gitlinks": 0,
            "unregistered_gitlinks": 0,
            "unregistered_paths": [],
            "non_stage0_gitlinks": 0,
            "non_stage0_paths": [],
            "unmerged_entries": 0,
            "unmerged_paths": [],
            "unmerged_or_nonzero_stage_status": "FAIL",
            "unregistered_status": "FAIL",
            "gitmodules_status": "NOT_CHECKED",
            "registered_paths": [],
        }
    records = _parse_ls_files_stage_z(listed.stdout)
    gitlinks = [row for row in records if row["mode"] == "160000"]
    non_gitlink_unmerged = [
        row for row in records if row["mode"] != "160000" and int(row["stage"]) != 0
    ]
    stage0 = [row for row in gitlinks if int(row["stage"]) == 0]
    non_stage0_gitlinks = [row for row in gitlinks if int(row["stage"]) != 0]
    gitmodules_status, registered, gitmodules_reason = _parse_gitmodules_paths(repo_root)
    if gitmodules_status == "OK":
        unregistered = [
            row for row in stage0 if _normalize_path(str(row["path"])) not in registered
        ]
    else:
        # Fail-closed: missing/unreadable/malformed .gitmodules ⇒ none registered.
        unregistered = list(stage0)
    unmerged_paths = sorted(
        {
            _normalize_path(str(row["path"]))
            for row in (*non_stage0_gitlinks, *non_gitlink_unmerged)
        }
    )
    unmerged_or_nonzero = bool(non_stage0_gitlinks or non_gitlink_unmerged)
    return {
        "status": "PASS",
        "reason": gitmodules_reason,
        "ls_files_ok": True,
        "total_gitlinks": len(gitlinks),
        "stage0_gitlinks": len(stage0),
        "unregistered_gitlinks": len(unregistered),
        "unregistered_paths": sorted(_normalize_path(str(row["path"])) for row in unregistered),
        "non_stage0_gitlinks": len(non_stage0_gitlinks),
        "non_stage0_paths": sorted(
            _normalize_path(str(row["path"])) for row in non_stage0_gitlinks
        ),
        "unmerged_entries": len(non_gitlink_unmerged) + len(non_stage0_gitlinks),
        "unmerged_paths": unmerged_paths,
        "unmerged_or_nonzero_stage_status": "FAIL" if unmerged_or_nonzero else "PASS",
        "unregistered_status": "FAIL" if unregistered else "PASS",
        "gitmodules_status": gitmodules_status,
        "registered_paths": sorted(registered),
    }


def collect_git_state(repo_root: Path) -> dict[str, Any]:
    inside = _git(repo_root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "available": False,
            "status": "WARN",
            "reason": (inside.stderr or inside.stdout or "not a Git worktree").strip(),
            "replacement_refs_status": "NOT_CHECKED",
            "replacement_refs": [],
            "identity_verified": False,
            "identity_errors": ["not_a_git_worktree"],
            "tree": None,
            "entries": [],
            "worktree_clean": None,
            "aligned": None,
            "status_command_ok": False,
            "dirt_complete": False,
        }
    replacement_refs_status, replacement_refs, replacement_refs_reason = _replacement_refs(repo_root)
    if replacement_refs_status != "CLEAR":
        return _failed_git_identity_state(
            replacement_refs_status=replacement_refs_status,
            replacement_refs=replacement_refs,
            reason=replacement_refs_reason,
            identity_errors=["replacement_refs_not_clear"],
            dirt_complete=False,
        )

    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    head = _git(repo_root, "rev-parse", "HEAD")
    head_commit = _git(repo_root, "rev-parse", "--verify", "HEAD^{commit}")
    head_tree = _git(repo_root, "rev-parse", "--verify", "HEAD^{tree}")
    upstream = _git(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream_head = _git(repo_root, "rev-parse", "@{u}")
    upstream_commit = _git(repo_root, "rev-parse", "--verify", "@{u}^{commit}")
    ahead_behind = _git(repo_root, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    # Superproject dirt only; broken nested gitlink worktrees must not block porcelain.
    status = _git(repo_root, "status", "--porcelain=v1", "-z", "--ignore-submodules=all")
    gitlinks = collect_gitlink_inventory(repo_root)

    branch_name = branch.stdout.strip() if branch.returncode == 0 else ""
    head_sha = head.stdout.strip() if head.returncode == 0 else ""
    head_commit_sha = head_commit.stdout.strip() if head_commit.returncode == 0 else ""
    head_tree_sha = head_tree.stdout.strip() if head_tree.returncode == 0 else ""
    upstream_name = upstream.stdout.strip() if upstream.returncode == 0 else ""
    upstream_sha = upstream_head.stdout.strip() if upstream_head.returncode == 0 else ""
    upstream_commit_sha = upstream_commit.stdout.strip() if upstream_commit.returncode == 0 else ""

    # Preserve only successfully collected fields (empty string / None when failed).
    preserved_branch = branch_name if branch.returncode == 0 and branch_name else ""
    preserved_head = head_sha if head.returncode == 0 and _is_git_object_id(head_sha) else ""
    preserved_tree = (
        head_tree_sha if head_tree.returncode == 0 and _is_git_object_id(head_tree_sha) else ""
    )
    preserved_upstream = upstream_name if upstream.returncode == 0 and upstream_name else ""
    preserved_upstream_head = (
        upstream_sha if upstream_head.returncode == 0 and _is_git_object_id(upstream_sha) else ""
    )

    ahead: int | None = None
    behind: int | None = None
    identity_errors: list[str] = []
    if branch.returncode != 0:
        identity_errors.append("branch_command_failed")
    elif not branch_name:
        identity_errors.append("branch_missing")
    elif branch_name == "HEAD":
        identity_errors.append("detached_head")
    if head.returncode != 0:
        identity_errors.append("head_command_failed")
    elif not _is_git_object_id(head_sha):
        identity_errors.append("head_invalid")
    if head_commit.returncode != 0:
        identity_errors.append("head_commit_command_failed")
    elif not _is_git_object_id(head_commit_sha):
        identity_errors.append("head_commit_invalid")
    elif head_sha != head_commit_sha:
        identity_errors.append("head_not_commit")
    if head_tree.returncode != 0:
        identity_errors.append("head_tree_command_failed")
    elif not _is_git_object_id(head_tree_sha):
        identity_errors.append("head_tree_invalid")
    if upstream.returncode != 0:
        identity_errors.append("upstream_command_failed")
    elif not upstream_name:
        identity_errors.append("upstream_missing")
    if upstream_head.returncode != 0:
        identity_errors.append("upstream_head_command_failed")
    elif not _is_git_object_id(upstream_sha):
        identity_errors.append("upstream_head_invalid")
    if upstream_commit.returncode != 0:
        identity_errors.append("upstream_commit_command_failed")
    elif not _is_git_object_id(upstream_commit_sha):
        identity_errors.append("upstream_commit_invalid")
    elif upstream_sha != upstream_commit_sha:
        identity_errors.append("upstream_not_commit")
    if ahead_behind.returncode == 0:
        parts = ahead_behind.stdout.strip().split()
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            ahead, behind = int(parts[0]), int(parts[1])
        else:
            identity_errors.append("ahead_behind_invalid")
    else:
        identity_errors.append("ahead_behind_command_failed")

    status_command_ok = status.returncode == 0
    if not status_command_ok:
        identity_errors.append("status_command_failed")
        entries: list[DirtyEntry] = []
    else:
        entries = _parse_porcelain_z(status.stdout)

    has_upstream = bool(preserved_upstream)
    aligned = bool(
        has_upstream
        and preserved_head
        and preserved_upstream_head
        and preserved_head == preserved_upstream_head
        and ahead == 0
        and behind == 0
    )
    total_gitlinks = int(gitlinks.get("total_gitlinks") or 0)
    # Full-tree clean requires empty superproject porcelain and zero gitlinks.
    worktree_clean = bool(status_command_ok and not entries and total_gitlinks == 0)
    # Completeness under C0A: no recursive submodule verify; gitlinks must be zero.
    dirt_complete = bool(status_command_ok and total_gitlinks == 0)

    entry_payloads = [entry.__dict__ for entry in entries]
    common = {
        "status_command_ok": status_command_ok,
        "status_ignore_submodules": "all",
        "dirt_scope": "superproject_porcelain",
        "gitlinks": gitlinks,
        "dirt_complete": dirt_complete,
    }

    if identity_errors:
        return _failed_git_identity_state(
            replacement_refs_status=replacement_refs_status,
            replacement_refs=replacement_refs,
            reason="Git identity verification failed: " + ", ".join(identity_errors),
            identity_errors=identity_errors,
            branch=preserved_branch,
            head=preserved_head,
            tree=preserved_tree,
            upstream=preserved_upstream,
            upstream_head=preserved_upstream_head,
            ahead=ahead,
            behind=behind,
            has_upstream=has_upstream,
            aligned=aligned,
            worktree_clean=worktree_clean if status_command_ok else None,
            entries=entry_payloads,
            **common,
        )

    return {
        "available": True,
        "status": "PASS",
        "replacement_refs_status": replacement_refs_status,
        "replacement_refs": replacement_refs,
        "identity_verified": True,
        "identity_errors": [],
        "branch": preserved_branch,
        "head": preserved_head,
        "tree": preserved_tree,
        "upstream": preserved_upstream,
        "upstream_head": preserved_upstream_head,
        "ahead": ahead,
        "behind": behind,
        "has_upstream": has_upstream,
        "aligned": aligned,
        "worktree_clean": worktree_clean,
        "entries": entry_payloads,
        **common,
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
    if gate.get("status") == "WARN":
        return ReadinessCheck(
            id=check_id,
            label=label,
            status="warn",
            severity="degraded",
            summary=f"{label} reported warnings.",
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
    if git.get("status") == "FAIL" or not git.get("identity_verified", True):
        return ReadinessCheck(
            id="git_state",
            label="Git state",
            status="fail",
            severity="blocked",
            summary=str(git.get("reason", "Git identity verification failed.")),
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
    governance = checks_map.get("governance", {})
    checks: list[ReadinessCheck] = [
        _check_from_gate("boot_core", "Boot-core file contract", boot_core if isinstance(boot_core, Mapping) else {}),
        _status_from_git(
            checks_map.get("git", {}) if isinstance(checks_map.get("git", {}), Mapping) else {},
            bool(preflight_status.get("require_github")),
        ),
        _check_from_gate("dirty_worktree", "Dirty worktree classification", dirty if isinstance(dirty, Mapping) else {}),
        _check_from_gate(
            "governance_preflight",
            "Governance preflight",
            governance if isinstance(governance, Mapping) else {},
        ),
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
            "deferred_scope": "data-readiness/dashboard/replay/optimizer",
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

    governance_result = run_governance_preflight(repo_root).to_dict()
    checks["governance"] = governance_result
    if governance_result["status"] == "FAIL":
        failures.append("governance preflight did not pass: FAIL")
    elif governance_result["status"] == "WARN":
        warnings.append("governance preflight warning")

    git_state = collect_git_state(repo_root)
    checks["git"] = git_state
    if git_state.get("available") and (
        git_state.get("status") == "FAIL" or not git_state.get("identity_verified", True)
    ):
        failures.append(str(git_state.get("reason", "Git identity verification failed")))

    gitlinks = git_state.get("gitlinks") if isinstance(git_state.get("gitlinks"), Mapping) else {}
    if not git_state.get("available"):
        # Non-git roots remain planning-soft (historical WARN path); no index claims.
        dirty = {
            "status": "PASS",
            "dirty_state": "not_a_git_worktree",
            "counts": {},
            "blockers": [],
            "warnings": [],
            "classifications": [],
            "dirt_scope": "none",
            "status_command_ok": False,
            "total_gitlinks": 0,
        }
        checks["dirty"] = dirty
        checks["unregistered_gitlinks"] = {
            "status": "PASS",
            "unregistered_gitlinks": 0,
            "paths": [],
            "gitmodules_status": "NOT_APPLICABLE",
            "reason": "not a git worktree",
        }
        checks["unmerged_or_nonzero_stage_index"] = {
            "status": "PASS",
            "unmerged_entries": 0,
            "paths": [],
            "reason": "not a git worktree",
        }
        checks["dirt_complete"] = {
            "status": "PASS",
            "dirt_complete": False,
            "reason": "not a git worktree; dirt completeness not applicable",
        }
    else:
        total_gitlinks = int(gitlinks.get("total_gitlinks") or 0) if gitlinks else 0
        status_command_ok = bool(git_state.get("status_command_ok", False))
        dirty_entries = [DirtyEntry(**entry) for entry in git_state.get("entries", [])]
        dirty = build_dirty_check(
            status_command_ok=status_command_ok,
            entries=dirty_entries,
            total_gitlinks=total_gitlinks,
        )
        checks["dirty"] = dirty
        if dirty["status"] != "PASS":
            if dirty.get("dirty_state") == "STATUS_UNAVAILABLE":
                failures.append("git status unavailable; dirty state is STATUS_UNAVAILABLE")
            elif dirty.get("dirty_state") == "clean_superproject_only":
                failures.append(
                    "superproject porcelain clean but gitlinks remain (clean_superproject_only)"
                )
            else:
                failures.append("unclassified source/test/runtime dirty files are present")

        unregistered_count = int(gitlinks.get("unregistered_gitlinks") or 0) if gitlinks else 0
        ls_files_ok = bool(gitlinks.get("ls_files_ok")) if gitlinks else False
        unregistered_check_status = "PASS" if ls_files_ok and unregistered_count == 0 else "FAIL"
        checks["unregistered_gitlinks"] = {
            "status": unregistered_check_status,
            "unregistered_gitlinks": unregistered_count,
            "paths": list(gitlinks.get("unregistered_paths") or []) if gitlinks else [],
            "gitmodules_status": gitlinks.get("gitmodules_status") if gitlinks else "NOT_CHECKED",
            "reason": (
                f"unregistered_gitlinks={unregistered_count}"
                if unregistered_count or not ls_files_ok
                else "no unregistered stage-0 gitlinks"
            ),
        }
        if unregistered_check_status != "PASS":
            failures.append(f"unregistered gitlinks present: {unregistered_count}")

        unmerged_status = (
            str(gitlinks.get("unmerged_or_nonzero_stage_status") or "FAIL") if gitlinks else "FAIL"
        )
        checks["unmerged_or_nonzero_stage_index"] = {
            "status": unmerged_status,
            "unmerged_entries": int(gitlinks.get("unmerged_entries") or 0) if gitlinks else 0,
            "paths": list(gitlinks.get("unmerged_paths") or []) if gitlinks else [],
            "reason": (
                "non-stage-0 gitlinks or other unmerged index entries present"
                if unmerged_status == "FAIL"
                else "no unmerged or non-stage-0 index entries"
            ),
        }
        if unmerged_status != "PASS":
            failures.append("unmerged or non-stage-0 index entries present")

        checks["dirt_complete"] = {
            "status": "PASS" if git_state.get("dirt_complete") else "FAIL",
            "dirt_complete": bool(git_state.get("dirt_complete")),
            "reason": (
                "status ok and total gitlinks == 0"
                if git_state.get("dirt_complete")
                else "dirt incomplete: status failed and/or gitlinks remain "
                "(registered submodules require recursive verification outside C0A)"
            ),
        }

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

    write_allowed = (
        status["verdict"] == "PASS"
        and args.mode == "strict"
        and not args.no_tests
        and not args.smoke
        and not args.run_focused_contract
    )
    if args.write_status and write_allowed:
        boot_status = make_boot_status_from_preflight(status)
        write_result = _write_boot_status_file(boot_status, args.status_out, repo_root=repo_root)
        status["status_write"] = {"path": _normalize_path(args.status_out), "result": write_result}
    elif args.write_status:
        status["status_write"] = {"path": _normalize_path(args.status_out), "result": "blocked-until-pass"}

    if args.require_github:
        post_git = collect_git_state(repo_root)
        status["post_git"] = post_git
        if post_git.get("status") == "FAIL" or not post_git.get("identity_verified", True):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append("--require-github post-write Git identity verification failed")
        elif not post_git.get("worktree_clean") or not post_git.get("aligned"):
            status["verdict"] = "FAIL"
            status["exit_code"] = 1
            status["failures"].append("--require-github post-write check is not clean/aligned")

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
    parser.add_argument(
        "--write-status",
        action="store_true",
        help=f"Write {BOOT_STATUS_CURRENT_PATH.as_posix()}.",
    )
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
