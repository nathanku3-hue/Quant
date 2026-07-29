"""CLI evidence builder for GV-DETERMINISTIC-REPLAY-0."""

from __future__ import annotations

import argparse
import base64
from copy import deepcopy
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

from contracts.gv_portfolio.v0 import identifier as custody_identifier
from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.replay import (
    REPLAY_CERTIFICATION_SCHEMA,
    REPLAY_DOMAIN,
    ReplayV0Error,
    build_replay_evidence,
)
from gv_portfolio_v0.storage import load_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("docs/context/e2e_evidence/gv_deterministic_replay_0_shadow_local.json")
CERTIFIED_EVIDENCE_SCHEMA = "gv_portfolio_v0_replay_certified_evidence_v1"
PROVIDER_VERIFICATION_SCHEMA = "gv_portfolio_v0_github_provider_verification_v1"


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


def _build_provider_verification_record(
    audit_receipt: Mapping[str, Any],
    *,
    candidate_commit: str,
    candidate_tree: str,
) -> dict[str, Any]:
    reviewers = audit_receipt.get("reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != 3:
        raise ReplayV0Error("AUDIT_RECEIPT_THREE_REVIEWERS_REQUIRED")
    reviewer_records: list[dict[str, Any]] = []
    for reviewer in reviewers:
        if not isinstance(reviewer, Mapping):
            raise ReplayV0Error("AUDIT_RECEIPT_REVIEWER_OBJECT_REQUIRED")
        reviewer_records.append(
            {
                "domain": reviewer.get("domain"),
                "repository": reviewer.get("repository"),
                "github_author_login": reviewer.get("github_author_login"),
                "github_committer_login": reviewer.get("github_committer_login"),
                "submission_commit_sha": reviewer.get("submission_commit_sha"),
                "report_path": reviewer.get("report_path"),
                "report_sha256": reviewer.get("report_sha256"),
                "receipt_hash": reviewer.get("receipt_hash"),
            }
        )
    reviewer_records.sort(key=lambda row: str(row["domain"]))
    body = {
        "schema_version": PROVIDER_VERIFICATION_SCHEMA,
        "provider": "GITHUB",
        "verification_method": "GITHUB_REST_API_2022-11-28",
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "audit_receipt_hash": audit_receipt.get("audit_receipt_hash"),
        "checks": {
            "clean_local_checkout": True,
            "origin_repository_exact": True,
            "candidate_commit_and_tree_remote": True,
            "reviewer_submission_accounts_remote": True,
            "reviewer_report_bytes_remote": True,
        },
        "reviewers": reviewer_records,
    }
    return {
        **body,
        "provider_verification_hash": domain_hash(
            f"{REPLAY_DOMAIN}:GITHUB_PROVIDER_VERIFICATION:V1", body
        ),
    }


def _promote_verified_replay_evidence(
    shadow_evidence: Mapping[str, Any],
    *,
    provider_verification: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = deepcopy(dict(shadow_evidence))
    gate = evidence.get("audit_gate")
    if not isinstance(gate, Mapping):
        raise ReplayV0Error("REPLAY_AUDIT_GATE_OBJECT_REQUIRED")
    if gate.get("status") != "BLOCKED" or gate.get("reason") != (
        "EXTERNAL_PROVIDER_VERIFICATION_REQUIRED"
    ):
        raise ReplayV0Error("REPLAY_AUDIT_GATE_NOT_READY_FOR_PROVIDER_PROMOTION")
    if evidence.get("replay_certification") is not None:
        raise ReplayV0Error("REPLAY_CERTIFICATION_ALREADY_PRESENT")
    checks = evidence.get("checks")
    if not isinstance(checks, Mapping) or not checks or any(
        value is not True for value in checks.values()
    ):
        raise ReplayV0Error("REPLAY_CHECKS_NOT_ALL_PASS")

    verification = deepcopy(dict(provider_verification))
    verification_hash = verification.get("provider_verification_hash")
    verification_body = {
        key: value
        for key, value in verification.items()
        if key != "provider_verification_hash"
    }
    expected_verification_hash = domain_hash(
        f"{REPLAY_DOMAIN}:GITHUB_PROVIDER_VERIFICATION:V1",
        verification_body,
    )
    if verification_hash != expected_verification_hash:
        raise ReplayV0Error("PROVIDER_VERIFICATION_HASH_MISMATCH")
    if verification.get("schema_version") != PROVIDER_VERIFICATION_SCHEMA:
        raise ReplayV0Error("PROVIDER_VERIFICATION_SCHEMA_INVALID")
    audit_receipt_hash = gate.get("audit_receipt_hash")
    if not audit_receipt_hash or verification.get("audit_receipt_hash") != audit_receipt_hash:
        raise ReplayV0Error("PROVIDER_VERIFICATION_AUDIT_HASH_MISMATCH")
    verification_checks = verification.get("checks")
    if not isinstance(verification_checks, Mapping) or not verification_checks or any(
        value is not True for value in verification_checks.values()
    ):
        raise ReplayV0Error("PROVIDER_VERIFICATION_CHECK_FAILED")

    source_shadow_evidence_hash = evidence.get("evidence_hash")
    if not isinstance(source_shadow_evidence_hash, str) or not source_shadow_evidence_hash:
        raise ReplayV0Error("SHADOW_EVIDENCE_HASH_REQUIRED")
    certification_payload = {
        "schema_version": REPLAY_CERTIFICATION_SCHEMA,
        "candidate_commit": verification["candidate_commit"],
        "candidate_tree": verification["candidate_tree"],
        "source_shadow_evidence_hash": source_shadow_evidence_hash,
        "source_event_ledger_hash": evidence["source_event_ledger_hash"],
        "normalized_event_stream_hash": evidence["normalized_event_stream_hash"],
        "replay_state_hash": evidence["replay_state_hash"],
        "terminal_book_hash": evidence["terminal_book_hash"],
        "decision_state_hash": evidence["decision_state_hash"],
        "execution_hash": evidence["execution_hash"],
        "fixture_matrix_hash": evidence["fixture_matrix_hash"],
        "product_certification_ids": evidence["product_certification_ids"],
        "audit_receipt_hash": audit_receipt_hash,
        "provider_verification_hash": verification_hash,
        "checks": dict(checks),
        "declared_precision": evidence["declared_precision"],
    }
    certification = {
        "certification_id": custody_identifier("CRT", certification_payload),
        **certification_payload,
    }
    evidence["schema_version"] = CERTIFIED_EVIDENCE_SCHEMA
    evidence["provider_verification"] = verification
    evidence["audit_gate"] = {
        "status": "PASS",
        "reason": None,
        "audit_receipt_hash": audit_receipt_hash,
        "provider_verification_hash": verification_hash,
        "reviewer_github_logins": [
            row["github_author_login"] for row in verification["reviewers"]
        ],
    }
    evidence["claim_boundary"] = (
        "Terminal replay certification issued by the clean-checkout CLI only after "
        "GitHub verified the candidate commit/tree, reviewer accounts, and exact "
        "remote report bytes. Natural-person identity is not claimed."
    )
    evidence["replay_certification"] = certification
    evidence["evidence_hash"] = domain_hash(
        f"{REPLAY_DOMAIN}:CERTIFIED_EVIDENCE:V1",
        {key: value for key, value in evidence.items() if key != "evidence_hash"},
    )
    return evidence


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
            provider_verification = _build_provider_verification_record(
                receipt,
                candidate_commit=commit or "",
                candidate_tree=tree or "",
            )
            certified_evidence = _promote_verified_replay_evidence(
                shadow_evidence,
                provider_verification=provider_verification,
            )
            _atomic_write(args.output, certified_evidence)
            print(f"GV-DETERMINISTIC-REPLAY-0 CERTIFIED evidence={args.output}")
            return 0
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
