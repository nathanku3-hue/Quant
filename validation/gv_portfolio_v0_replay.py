"""CLI evidence builder for GV-DETERMINISTIC-REPLAY-0."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.replay import ReplayV0Error, build_replay_evidence
from gv_portfolio_v0.storage import load_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("docs/context/e2e_evidence/gv_deterministic_replay_0_shadow_local.json")


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplayV0Error(f"JSON_INPUT_INVALID:{path.name}") from exc
    if not isinstance(value, dict):
        raise ReplayV0Error(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ReplayV0Error("EVIDENCE_ROOT_SYMLINK_PROHIBITED")
    raw = canonical_document_bytes(dict(payload))
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild GV Portfolio V0 state and emit deterministic replay evidence. "
            "Without an independent Slice 0 audit receipt, output remains shadow-only."
        )
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Root containing micro_portfolio_workspace.json; defaults to GV_PORTFOLIO_V0_HOME.",
    )
    parser.add_argument(
        "--audit-receipt",
        type=Path,
        default=None,
        help="Optional exact independent Slice 0 audit receipt JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Evidence output path (default: {DEFAULT_OUTPUT.as_posix()}).",
    )
    parser.add_argument(
        "--implementer-github-login",
        default=os.environ.get("GV_PORTFOLIO_V0_IMPLEMENTER_GITHUB_LOGIN"),
        help=(
            "Provider-authenticated implementer GitHub login. Required when an "
            "audit receipt is supplied so reviewer accounts can be proven distinct."
        ),
    )
    parser.add_argument(
        "--require-certification",
        action="store_true",
        help="Return exit 2 unless the external audit gate permits replay certification.",
    )
    return parser


def _run_git(*arguments: str) -> str:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReplayV0Error("CANDIDATE_GIT_IDENTITY_UNAVAILABLE") from exc


def _git_identity() -> tuple[str, str]:
    dirty = _run_git("status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise ReplayV0Error("CANDIDATE_CHECKOUT_NOT_CLEAN")
    return _run_git("rev-parse", "HEAD"), _run_git("rev-parse", "HEAD^{tree}")


def _github_repository_from_remote(remote_url: str) -> str:
    value = remote_url.strip()
    patterns = (
        r"^https://github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$",
        r"^git@github\.com:(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        r"^ssh://git@github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, value, flags=re.IGNORECASE)
        if match:
            return match.group("repo")
    raise ReplayV0Error("CANDIDATE_ORIGIN_GITHUB_REPOSITORY_REQUIRED")


def _github_origin_repository() -> str:
    return _github_repository_from_remote(_run_git("remote", "get-url", "origin"))


def _verify_receipt_repository_against_origin(
    audit_receipt: Mapping[str, Any], *, origin_repository: str
) -> None:
    reviewers = audit_receipt.get("reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != 3:
        raise ReplayV0Error("AUDIT_RECEIPT_THREE_REVIEWERS_REQUIRED")
    repositories = {
        str(reviewer.get("repository", "")).casefold()
        for reviewer in reviewers
        if isinstance(reviewer, Mapping)
    }
    if repositories != {origin_repository.casefold()}:
        raise ReplayV0Error("AUDIT_RECEIPT_REPOSITORY_NOT_ORIGIN")


def _github_api_json(url: str) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gv-portfolio-v0-replay-verifier",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
    except HTTPError as exc:
        raise ReplayV0Error(f"GITHUB_PROVIDER_HTTP_ERROR:{exc.code}") from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise ReplayV0Error("GITHUB_PROVIDER_UNAVAILABLE") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReplayV0Error("GITHUB_PROVIDER_RESPONSE_INVALID") from exc
    if not isinstance(payload, dict):
        raise ReplayV0Error("GITHUB_PROVIDER_OBJECT_REQUIRED")
    return payload


def verify_github_provider_receipt(receipt: Mapping[str, Any]) -> None:
    """Verify reviewer identity and exact report bytes from the public GitHub API."""

    repository = str(receipt.get("repository", ""))
    submission_sha = str(receipt.get("submission_commit_sha", ""))
    report_path = str(receipt.get("report_path", ""))
    if repository.count("/") != 1 or not submission_sha or not report_path:
        raise ReplayV0Error("GITHUB_PROVIDER_RECEIPT_FIELDS_INVALID")
    encoded_repository = "/".join(quote(part, safe="") for part in repository.split("/"))
    commit_url = f"https://api.github.com/repos/{encoded_repository}/commits/{quote(submission_sha, safe='')}"
    commit = _github_api_json(commit_url)
    if commit.get("sha") != submission_sha:
        raise ReplayV0Error("GITHUB_PROVIDER_COMMIT_SHA_MISMATCH")
    author = commit.get("author")
    committer = commit.get("committer")
    if not isinstance(author, Mapping) or author.get("login") != receipt.get(
        "github_author_login"
    ):
        raise ReplayV0Error("GITHUB_PROVIDER_AUTHOR_LOGIN_MISMATCH")
    if not isinstance(committer, Mapping) or committer.get("login") != receipt.get(
        "github_committer_login"
    ):
        raise ReplayV0Error("GITHUB_PROVIDER_COMMITTER_LOGIN_MISMATCH")
    if commit.get("html_url") != receipt.get("receipt_url"):
        raise ReplayV0Error("GITHUB_PROVIDER_RECEIPT_URL_MISMATCH")

    candidate_sha = str(receipt.get("candidate_commit", ""))
    expected_tree = str(receipt.get("candidate_tree", ""))
    candidate_url = (
        f"https://api.github.com/repos/{encoded_repository}/commits/"
        f"{quote(candidate_sha, safe='')}"
    )
    candidate = _github_api_json(candidate_url)
    if candidate.get("sha") != candidate_sha:
        raise ReplayV0Error("GITHUB_PROVIDER_CANDIDATE_COMMIT_MISMATCH")
    candidate_commit = candidate.get("commit")
    candidate_tree = (
        candidate_commit.get("tree") if isinstance(candidate_commit, Mapping) else None
    )
    if not isinstance(candidate_tree, Mapping) or candidate_tree.get("sha") != expected_tree:
        raise ReplayV0Error("GITHUB_PROVIDER_CANDIDATE_TREE_MISMATCH")

    encoded_path = "/".join(quote(part, safe="") for part in report_path.split("/"))
    content_url = (
        f"https://api.github.com/repos/{encoded_repository}/contents/{encoded_path}"
        f"?ref={quote(submission_sha, safe='')}"
    )
    content = _github_api_json(content_url)
    if content.get("type") != "file" or content.get("encoding") != "base64":
        raise ReplayV0Error("GITHUB_PROVIDER_REPORT_FILE_INVALID")
    encoded = content.get("content")
    if not isinstance(encoded, str):
        raise ReplayV0Error("GITHUB_PROVIDER_REPORT_CONTENT_MISSING")
    compact_encoded = "".join(encoded.split())
    try:
        remote_bytes = base64.b64decode(compact_encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ReplayV0Error("GITHUB_PROVIDER_REPORT_BASE64_INVALID") from exc
    report = receipt.get("report")
    if not isinstance(report, Mapping):
        raise ReplayV0Error("GITHUB_PROVIDER_REPORT_OBJECT_REQUIRED")
    if remote_bytes != canonical_document_bytes(dict(report)):
        raise ReplayV0Error("GITHUB_PROVIDER_REPORT_BYTES_MISMATCH")


def run(
    *,
    workspace_root: Path | None,
    output: Path,
    audit_receipt: Mapping[str, Any] | None,
    require_certification: bool,
    expected_candidate_commit: str | None = None,
    expected_candidate_tree: str | None = None,
    expected_implementer_github_login: str | None = None,
) -> int:
    workspace = load_workspace(root=workspace_root)
    evidence = build_replay_evidence(
        workspace,
        audit_receipt=audit_receipt,
        expected_candidate_commit=expected_candidate_commit,
        expected_candidate_tree=expected_candidate_tree,
        expected_implementer_github_login=expected_implementer_github_login,
    )
    _atomic_write(output, evidence)
    certified = evidence["replay_certification"] is not None
    print(
        "GV-DETERMINISTIC-REPLAY-0 "
        + ("CERTIFIED" if certified else "SHADOW_READY_AUDIT_BLOCKED")
        + f" evidence={output}"
    )
    if require_certification and not certified:
        return 2
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    receipt = (
        None
        if args.audit_receipt is None
        else _load_json_object(args.audit_receipt)
    )
    try:
        commit: str | None = None
        tree: str | None = None
        if receipt is not None:
            commit, tree = _git_identity()
            _verify_receipt_repository_against_origin(
                receipt, origin_repository=_github_origin_repository()
            )
            if not args.implementer_github_login:
                raise ReplayV0Error("IMPLEMENTER_GITHUB_LOGIN_REQUIRED")
        if receipt is not None:
            reviewers = receipt.get("reviewers")
            if not isinstance(reviewers, list) or len(reviewers) != 3:
                raise ReplayV0Error("AUDIT_RECEIPT_THREE_REVIEWERS_REQUIRED")
            for reviewer in reviewers:
                if not isinstance(reviewer, Mapping):
                    raise ReplayV0Error("AUDIT_RECEIPT_REVIEWER_OBJECT_REQUIRED")
                verify_github_provider_receipt(reviewer)
            workspace = load_workspace(root=args.workspace_root)
            shadow_evidence = build_replay_evidence(
                workspace,
                audit_receipt=receipt,
                expected_candidate_commit=commit,
                expected_candidate_tree=tree,
                expected_implementer_github_login=args.implementer_github_login,
            )
            _atomic_write(args.output, shadow_evidence)
            print(
                "GV-DETERMINISTIC-REPLAY-0 PROVIDER_PREFLIGHT_PASS_"
                f"TERMINAL_AUTHORITY_BLOCKED evidence={args.output}"
            )
            return 2 if args.require_certification else 0
        return run(
            workspace_root=args.workspace_root,
            output=args.output,
            audit_receipt=None,
            require_certification=args.require_certification,
        )
    except ReplayV0Error as exc:
        print(f"GV-DETERMINISTIC-REPLAY-0 BLOCKED reason={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
