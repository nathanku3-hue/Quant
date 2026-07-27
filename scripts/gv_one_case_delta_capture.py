"""CLI for pre-human one-case evidence-gap triage machinery.

The CLI deliberately has no command that publishes current authority or opens a
human session automatically. Session creation requires an exact hosted-green
candidate and explicit inputs.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_fs0_canonical import canonical_document_bytes, sha256_bytes  # noqa: E402
from core.gv_one_case_delta import (
    DEFAULT_BINDING_PATH,
    DEFAULT_BUNDLE_PATH,
    DEFAULT_PROJECTION_MANIFEST_PATH,
    DEFAULT_PROJECTION_PATH,
    PROJECTION_SCHEMA_HASH,
    build_pre_human_artifacts,
    create_session_manifest,
    load_experiment_binding,
    verify_identity_evidence,
    require_distinct_humans,
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON object required: {path}")
    return value


def _write(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise SystemExit(f"refusing to replace symlink output: {path}")
    raw = canonical_document_bytes(record)
    temp = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def command_build(_: argparse.Namespace) -> int:
    bundle, projection, manifest = build_pre_human_artifacts(ROOT, DEFAULT_BINDING_PATH)
    _write(DEFAULT_BUNDLE_PATH, bundle)
    _write(DEFAULT_PROJECTION_PATH, projection)
    _write(DEFAULT_PROJECTION_MANIFEST_PATH, manifest)
    print(json.dumps({
        "evidence_bundle_hash": bundle["evidence_bundle_hash"],
        "projection_hash": projection["projection_hash"],
        "projection_manifest_hash": manifest["projection_manifest_hash"],
    }, sort_keys=True))
    return 0


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def command_create_session_manifest(args: argparse.Namespace) -> int:
    binding = load_experiment_binding(DEFAULT_BINDING_PATH)
    evidence_bundle = _read_json(DEFAULT_BUNDLE_PATH)
    projection = _read_json(DEFAULT_PROJECTION_PATH)
    projection_manifest = _read_json(DEFAULT_PROJECTION_MANIFEST_PATH)
    proof = _read_json(Path(args.hosted_proof))
    trusted_proof_issuers = _read_json(Path(args.trusted_proof_issuers))
    candidate_sha = _git("rev-parse", "HEAD")
    candidate_tree = _git("rev-parse", "HEAD^{tree}")
    if args.candidate_sha and args.candidate_sha != candidate_sha:
        raise SystemExit("candidate SHA does not match checked-out HEAD")
    manifest = create_session_manifest(
        candidate_sha=candidate_sha,
        candidate_tree=candidate_tree,
        experiment_binding_hash=binding["experiment_binding_hash"],
        evidence_bundle_hash=evidence_bundle["evidence_bundle_hash"],
        projection_hash=projection["projection_hash"],
        projection_manifest_hash=projection_manifest["projection_manifest_hash"],
        projection_schema_hash=PROJECTION_SCHEMA_HASH,
        operator_instruction_hash=sha256_bytes((DEFAULT_BINDING_PATH.parent / "instructions_operator.md").read_bytes()),
        reviewer_instruction_hash=sha256_bytes((DEFAULT_BINDING_PATH.parent / "instructions_reviewer.md").read_bytes()),
        hosted_proof_identity=proof,
        trusted_proof_issuers=trusted_proof_issuers,
    )
    _write(Path(args.output), manifest)
    print(manifest["session_manifest_hash"])
    return 0


def command_preflight_identities(args: argparse.Namespace) -> int:
    manifest = _read_json(Path(args.session_manifest))
    operator = _read_json(Path(args.operator_identity))
    reviewer = _read_json(Path(args.reviewer_identity))
    trusted = _read_json(Path(args.trusted_issuers))
    operator_hash = verify_identity_evidence(
        operator,
        expected_role="OPERATOR",
        session_manifest=manifest,
        trusted_issuers=trusted,
    )
    reviewer_hash = verify_identity_evidence(
        reviewer,
        expected_role="REVIEWER",
        session_manifest=manifest,
        trusted_issuers=trusted,
        preflight_only=True,
    )
    require_distinct_humans(operator, reviewer)
    print(json.dumps({
        "adapter": "OPENSSH_SSHSIG_V1",
        "operator_identity_evidence_hash": operator_hash,
        "reviewer_identity_evidence_hash": reviewer_hash,
        "distinct_verified_humans": True,
        "human_exposure_opened": False,
    }, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build deterministic pre-human artifacts")
    build.set_defaults(func=command_build)

    session = subparsers.add_parser(
        "create-session-manifest",
        help="bind a checked-out hosted-green candidate; does not expose a human",
    )
    session.add_argument("--hosted-proof", required=True)
    session.add_argument("--trusted-proof-issuers", required=True)
    session.add_argument("--output", required=True)
    session.add_argument("--candidate-sha")
    session.set_defaults(func=command_create_session_manifest)

    identity = subparsers.add_parser(
        "preflight-identities",
        help="verify two signed identity records without opening a session",
    )
    identity.add_argument("--session-manifest", required=True)
    identity.add_argument("--operator-identity", required=True)
    identity.add_argument("--reviewer-identity", required=True)
    identity.add_argument("--trusted-issuers", required=True)
    identity.set_defaults(func=command_preflight_identities)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
