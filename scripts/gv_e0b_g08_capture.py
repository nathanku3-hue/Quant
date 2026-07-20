#!/usr/bin/env python3
"""Narrow local G08 capture runner (not a generic platform).

Owns the operator workflow:

  session start
  → baseline timer + submission
  → packet reveal
  → post timer + submission
  → blinded review-package export
  → rubric submission
  → verify / finalize / optional publish

Usage examples:

  python scripts/gv_e0b_g08_capture.py init-forms --case-dir data/gv_e0b/dv1_g08
  python scripts/gv_e0b_g08_capture.py open-session --case-dir data/gv_e0b/dv1_g08
  python scripts/gv_e0b_g08_capture.py open-arm --arm BASELINE
  python scripts/gv_e0b_g08_capture.py submit-baseline --authoring path/to/baseline.json
  python scripts/gv_e0b_g08_capture.py generate-packet
  python scripts/gv_e0b_g08_capture.py open-arm --arm POST
  python scripts/gv_e0b_g08_capture.py submit-post --authoring path/to/post.json
  python scripts/gv_e0b_g08_capture.py export-review-package
  python scripts/gv_e0b_g08_capture.py submit-rubric --authoring path/to/rubric.json
  python scripts/gv_e0b_g08_capture.py finalize
  python scripts/gv_e0b_g08_capture.py status

Authoring JSON must not include timing fields (system-stamped).
Reviewer receives only reviewer_export/ contents (package + blank ARM rubric).
Private mapping stays under operator_custody/ until after rubric seal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_e0b_dv1_contradiction import (  # noqa: E402
    BUDGET_MINUTES,
    CAPTURE_STATE_ACTIVE,
    CAPTURE_STATE_COMPLETE,
    CAPTURE_STATE_RESUMABLE,
    CASE_ID,
    DEFAULT_CASE_DIR,
    GvE0bDv1Error,
    STAGE_BASELINE_CLOSE,
    STAGE_BASELINE_OPEN,
    STAGE_PACKET,
    STAGE_POST_CLOSE,
    STAGE_POST_OPEN,
    STAGE_REVIEW_PACKAGE,
    STAGE_RUBRIC_CLOSE,
    abort_capture_session,
    append_capture_checkpoint,
    capture_lifecycle_state,
    load_capture_checkpoints,
    load_capture_session,
    load_session_manifest,
    open_capture_session,
    recover_capture_checkpoint,
    require_capture_resumable,
    run_e0b_dv1_case,
    sealed_adversarial_bundle,
    stage_build_review_package,
    stage_capture_baseline,
    stage_capture_post,
    stage_capture_rubric,
    stage_generate_packet,
    stage_open_arm,
    write_authoring_templates,
)


def _case_paths(case_dir: Path, *, session_nonce: str | None = None) -> dict[str, Path]:
    captures = case_dir / "captures"
    # Session-nonce-specific export reduces accidental reuse of stale files.
    export_root = captures / "reviewer_export"
    export_dir = (
        export_root / session_nonce if session_nonce else export_root / "_pending"
    )
    custody_dir = captures / "operator_custody"
    return {
        "case_dir": case_dir,
        "baseline": captures / "baseline_seal.json",
        "packet": captures / "packet.json",
        "post": captures / "post_packet_seal.json",
        "rubric": captures / "rubric_scores.json",
        "session": captures / "session.json",
        "session_manifest": captures / "session_manifest.json",
        "checkpoints_dir": captures / "checkpoints",
        "export_root": export_root,
        "export_dir": export_dir,
        "package": export_dir / "review_package.json",
        "rubric_authoring_export": export_dir / "rubric_authoring.json",
        "custody_dir": custody_dir,
        "mapping": custody_dir / "review_mapping.private.json",
        "result": case_dir / "result.json",
        "decision_packet": case_dir / "decision_packet.md",
        "authoring_dir": captures / "authoring",
        "baseline_authoring": captures / "authoring" / "baseline_authoring.json",
        "post_authoring": captures / "authoring" / "post_authoring.json",
        "rubric_authoring": captures / "authoring" / "rubric_authoring.json",
    }


def _resolve_paths(case_dir: Path) -> dict[str, Path]:
    base = _case_paths(case_dir)
    if not base["session"].is_file():
        return base
    try:
        session = load_capture_session(base["session"])
    except GvE0bDv1Error:
        return base
    return _case_paths(case_dir, session_nonce=str(session["session_nonce"]))


def _load_authoring(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("authoring file must be a JSON object")
    return data


def _git_text(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GvE0bDv1Error(f"E0B_GIT_IDENTITY_FAILED:{args[0]}")
    return result.stdout.strip()


def _verify_protocol_freeze() -> str:
    verifier = ROOT / "scripts" / "verify_gv_fs0_protocol_freeze.py"
    result = subprocess.run(
        [
            sys.executable,
            str(verifier),
            "--mode",
            "enforced",
            "--base-ref",
            "origin/main",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GvE0bDv1Error("E0B_PROTOCOL_FREEZE_ENFORCEMENT_FAILED")
    manifest = ROOT / "contracts" / "gv_fs0" / "v1" / "gv_fs0_freeze_manifest_v1.json"
    if not manifest.is_file():
        raise GvE0bDv1Error("E0B_PROTOCOL_FREEZE_MANIFEST_MISSING")
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def _capture_preflight(case_dir: Path) -> tuple[str, str, str, dict[str, Path]]:
    try:
        relative_case = case_dir.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise GvE0bDv1Error("E0B_CASE_DIR_OUTSIDE_REPOSITORY") from exc
    authoring_dir = case_dir / "captures" / "authoring"
    forms = {
        "baseline": authoring_dir / "baseline_authoring.json",
        "post": authoring_dir / "post_authoring.json",
        "rubric": authoring_dir / "rubric_authoring.json",
    }
    allowed = {
        path.resolve().relative_to(ROOT.resolve()).as_posix()
        for path in forms.values()
    }
    status = _git_text("status", "--porcelain=v1", "--untracked-files=all")
    tracked_dirty: list[str] = []
    untracked: set[str] = set()
    for line in status.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:].replace("\\", "/")
        if code == "??":
            untracked.add(path)
        else:
            tracked_dirty.append(line)
    if tracked_dirty:
        raise GvE0bDv1Error("E0B_CAPTURE_TRACKED_TREE_DIRTY")
    if untracked != allowed:
        raise GvE0bDv1Error("E0B_CAPTURE_UNTRACKED_ALLOWLIST_MISMATCH")
    if relative_case.as_posix() != "data/gv_e0b/dv1_g08":
        raise GvE0bDv1Error("E0B_CANONICAL_CASE_DIR_REQUIRED")
    return (
        _git_text("rev-parse", "HEAD"),
        _git_text("rev-parse", "HEAD^{tree}"),
        _verify_protocol_freeze(),
        forms,
    )


def _assert_session_source_identity(case_dir: Path, session_path: Path) -> None:
    """Fail closed if the executing checkout moved after SESSION_OPEN."""

    try:
        relative_case = case_dir.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise GvE0bDv1Error("E0B_CASE_DIR_OUTSIDE_REPOSITORY") from exc
    if relative_case.as_posix() != "data/gv_e0b/dv1_g08":
        raise GvE0bDv1Error("E0B_CANONICAL_CASE_DIR_REQUIRED")

    status = _git_text("status", "--porcelain=v1", "--untracked-files=all")
    case_prefix = relative_case.as_posix() + "/"
    for line in status.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:].replace("\\", "/")
        if code != "??":
            raise GvE0bDv1Error("E0B_CAPTURE_TRACKED_TREE_DIRTY")
        if not path.startswith(case_prefix):
            raise GvE0bDv1Error("E0B_CAPTURE_UNTRACKED_OUTSIDE_CASE")

    manifest = load_session_manifest(session_path.parent / "session_manifest.json")
    if _git_text("rev-parse", "HEAD") != manifest["source_commit"]:
        raise GvE0bDv1Error("E0B_SESSION_SOURCE_COMMIT_DRIFT")
    if _git_text("rev-parse", "HEAD^{tree}") != manifest["source_tree"]:
        raise GvE0bDv1Error("E0B_SESSION_SOURCE_TREE_DRIFT")
    if _verify_protocol_freeze() != manifest["protocol_freeze_manifest_sha256"]:
        raise GvE0bDv1Error("E0B_SESSION_PROTOCOL_FREEZE_DRIFT")


def _operation_expectation(
    paths: dict[str, Path],
    operation: str,
) -> tuple[str | None, tuple[Path, ...]]:
    mapping: dict[str, tuple[str | None, tuple[Path, ...]]] = {
        "OPEN_BASELINE": (STAGE_BASELINE_OPEN, ()),
        "SUBMIT_BASELINE": (STAGE_BASELINE_CLOSE, (paths["baseline"],)),
        "GENERATE_PACKET": (STAGE_PACKET, (paths["packet"],)),
        "OPEN_POST": (STAGE_POST_OPEN, ()),
        "SUBMIT_POST": (STAGE_POST_CLOSE, (paths["post"],)),
        "EXPORT_REVIEW_PACKAGE": (
            STAGE_REVIEW_PACKAGE,
            (paths["package"], paths["mapping"], paths["rubric_authoring_export"]),
        ),
        "SUBMIT_RUBRIC": (STAGE_RUBRIC_CLOSE, (paths["rubric"],)),
        "FINALIZE": (None, (paths["result"], paths["decision_packet"])),
    }
    if operation not in mapping:
        raise GvE0bDv1Error("E0B_CAPTURE_OPERATION_UNKNOWN")
    return mapping[operation]


def _checkpointed(
    *,
    paths: dict[str, Path],
    operation: str,
    action: Callable[[], Any],
    complete: bool = False,
) -> Any:
    require_capture_resumable(paths["session"])
    append_capture_checkpoint(
        session_path=paths["session"],
        operation=operation,
        state=CAPTURE_STATE_ACTIVE,
        detail="operation_started",
    )
    try:
        value = action()
    except BaseException:
        expected_stage, expected_artifacts = _operation_expectation(paths, operation)
        recover_capture_checkpoint(
            session_path=paths["session"],
            operation=operation,
            expected_stage=expected_stage,
            expected_artifacts=expected_artifacts,
        )
        raise
    append_capture_checkpoint(
        session_path=paths["session"],
        operation=operation,
        state=CAPTURE_STATE_COMPLETE if complete else CAPTURE_STATE_RESUMABLE,
        detail="operation_committed",
    )
    return value


def _print_status(paths: dict[str, Path]) -> int:
    print(f"case_id: {CASE_ID}")
    print(f"case_dir: {paths['case_dir']}")
    print(f"budget_cap_minutes: {BUDGET_MINUTES} (early submit allowed)")
    if not paths["session"].is_file():
        print("session: NOT_OPEN")
        return 0
    try:
        session = load_capture_session(paths["session"])
    except GvE0bDv1Error as exc:
        print(f"session: INVALID ({exc})")
        return 1
    stages = [e["stage"] for e in session["chain"]]
    print(f"session_nonce: {session['session_nonce'][:16]}...")
    print(f"event_count: {len(stages)}")
    print(f"stages: {' → '.join(stages)}")
    print(f"session_manifest_hash: {session['session_manifest_hash']}")
    print(f"capture_lifecycle_state: {capture_lifecycle_state(paths['session'])}")
    print(f"checkpoint_count: {len(load_capture_checkpoints(paths['session']))}")
    for label, key in (
        ("baseline", "baseline"),
        ("packet", "packet"),
        ("post", "post"),
        ("review_package", "package"),
        ("rubric", "rubric"),
        ("result", "result"),
    ):
        present = "yes" if paths[key].is_file() else "no"
        print(f"{label}: {present}")
    if paths["package"].is_file():
        print(f"reviewer_export_dir: {paths['export_dir']}")
        print(f"review_package: {paths['package']}")
        print(f"blank_rubric_form: {paths['rubric_authoring_export']}")
        print(
            "mapping: private under operator_custody "
            f"({paths['mapping']}); commitment only in ledger"
        )
    print(
        "ledger_custody: arm-label blinding under separated export custody; "
        "local hashes do not prove personhood or absolute reviewer ignorance"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gv_e0b_g08_capture",
        description="Narrow G08 capture runner (single-case, local, non-generic).",
    )
    case_parent = argparse.ArgumentParser(add_help=False)
    case_parent.add_argument(
        "--case-dir",
        type=Path,
        default=DEFAULT_CASE_DIR,
        help="Case directory (default: data/gv_e0b/dv1_g08)",
    )
    # Accept --case-dir before or after the subcommand.
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=DEFAULT_CASE_DIR,
        help=argparse.SUPPRESS,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", parents=[case_parent], help="Show capture ledger status")
    sub.add_parser(
        "init-forms",
        parents=[case_parent],
        help="Emit blank baseline/post/ARM rubric authoring templates",
    )
    p_session = sub.add_parser(
        "open-session",
        parents=[case_parent],
        help="Bind Git/forms/principals and open SESSION_OPEN",
    )
    p_session.add_argument("--operator-id", required=True)
    p_session.add_argument("--reviewer-id", required=True)

    p_recover = sub.add_parser(
        "recover-session",
        parents=[case_parent],
        help="Classify the last interrupted ACTIVE checkpoint",
    )
    p_abort = sub.add_parser(
        "abort-session",
        parents=[case_parent],
        help="Permanently abort the current capture session",
    )
    p_abort.add_argument("--reason", required=True)

    p_open = sub.add_parser(
        "open-arm",
        parents=[case_parent],
        help="Open BASELINE or POST arm (starts budget clock)",
    )
    p_open.add_argument("--arm", choices=("BASELINE", "POST"), required=True)

    p_base = sub.add_parser(
        "submit-baseline",
        parents=[case_parent],
        help="Submit baseline decision (early OK)",
    )
    p_base.add_argument("--authoring", type=Path, required=True)

    sub.add_parser(
        "generate-packet",
        parents=[case_parent],
        help="Reveal GodView packet after baseline",
    )

    p_post = sub.add_parser(
        "submit-post",
        parents=[case_parent],
        help="Submit post-packet decision (early OK)",
    )
    p_post.add_argument("--authoring", type=Path, required=True)

    sub.add_parser(
        "export-review-package",
        parents=[case_parent],
        help="Build blinded REVIEW_PACKAGE for independent reviewer",
    )

    p_rub = sub.add_parser(
        "submit-rubric",
        parents=[case_parent],
        help="Submit blinded rubric scores",
    )
    p_rub.add_argument("--authoring", type=Path, required=True)

    p_fin = sub.add_parser(
        "finalize",
        parents=[case_parent],
        help="Verify chain, write result, optional publish",
    )
    p_fin.add_argument(
        "--publish",
        action="store_true",
        help=(
            "Publish current decision only if the real two-human comparison is "
            "observation-eligible; value disposition may be IMPROVED or NOT_IMPROVED"
        ),
    )

    args = parser.parse_args(argv)
    case_dir = args.case_dir.resolve()
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "captures").mkdir(parents=True, exist_ok=True)
    paths = _resolve_paths(case_dir)
    # Do not pre-create export_dir: package generation requires absent/empty.
    paths["custody_dir"].mkdir(parents=True, exist_ok=True)
    paths["authoring_dir"].mkdir(parents=True, exist_ok=True)
    paths["export_root"].mkdir(parents=True, exist_ok=True)

    try:
        if args.cmd == "status":
            return _print_status(paths)

        if args.cmd == "init-forms":
            written = write_authoring_templates(paths["authoring_dir"])
            print("INIT_FORMS")
            for label, path in written.items():
                print(f"{label}={path}")
            print(
                "Fill baseline/post under authoring/; give only reviewer_export/ "
                "to the blinded reviewer after export-review-package."
            )
            return 0

        if args.cmd == "open-session":
            source_commit, source_tree, freeze_manifest_sha256, forms = _capture_preflight(
                case_dir
            )
            session = open_capture_session(
                bundle=sealed_adversarial_bundle(),
                session_path=paths["session"],
                source_commit=source_commit,
                source_tree=source_tree,
                protocol_freeze_manifest_sha256=freeze_manifest_sha256,
                operator_principal_id=args.operator_id,
                reviewer_principal_id=args.reviewer_id,
                authoring_template_paths=forms,
            )
            print("SESSION_OPEN")
            print(f"session_nonce={session['session_nonce']}")
            print(f"source_commit={source_commit}")
            print(f"source_tree={source_tree}")
            print(f"protocol_freeze_manifest_sha256={freeze_manifest_sha256}")
            print(f"session_manifest_hash={session['session_manifest_hash']}")
            print(f"events_dir={session['events_dir']}")
            return 0

        if args.cmd == "recover-session":
            _assert_session_source_identity(case_dir, paths["session"])
            checkpoints = load_capture_checkpoints(paths["session"])
            if not checkpoints:
                manifest = load_session_manifest(paths["session"].parent / "session_manifest.json")
                forms = {
                    "baseline": paths["authoring_dir"] / "baseline_authoring.json",
                    "post": paths["authoring_dir"] / "post_authoring.json",
                    "rubric": paths["authoring_dir"] / "rubric_authoring.json",
                }
                open_capture_session(
                    bundle=sealed_adversarial_bundle(),
                    session_path=paths["session"],
                    source_commit=str(manifest["source_commit"]),
                    source_tree=str(manifest["source_tree"]),
                    protocol_freeze_manifest_sha256=str(
                        manifest["protocol_freeze_manifest_sha256"]
                    ),
                    operator_principal_id=str(manifest["operator_principal_id"]),
                    reviewer_principal_id=str(manifest["reviewer_principal_id"]),
                    authoring_template_paths=forms,
                )
                checkpoint = load_capture_checkpoints(paths["session"])[-1]
                print("RECOVER_SESSION")
                print("operation=OPEN_SESSION")
                print(f"state={checkpoint['state']}")
                print(f"detail={checkpoint['detail']}")
                return 0
            operation = str(checkpoints[-1]["operation"])
            expected_stage, expected_artifacts = _operation_expectation(paths, operation)
            checkpoint = recover_capture_checkpoint(
                session_path=paths["session"],
                operation=operation,
                expected_stage=expected_stage,
                expected_artifacts=expected_artifacts,
            )
            print("RECOVER_SESSION")
            print(f"operation={operation}")
            print(f"state={checkpoint['state']}")
            print(f"detail={checkpoint['detail']}")
            return 0 if checkpoint["state"] == CAPTURE_STATE_RESUMABLE else 2

        _assert_session_source_identity(case_dir, paths["session"])

        if args.cmd == "abort-session":
            checkpoint = abort_capture_session(
                session_path=paths["session"],
                reason=args.reason,
            )
            print("ABORT_SESSION")
            print(f"state={checkpoint['state']}")
            print(f"detail={checkpoint['detail']}")
            return 0

        if args.cmd == "open-arm":
            operation = "OPEN_BASELINE" if args.arm == "BASELINE" else "OPEN_POST"
            open_payload = _checkpointed(
                paths=paths,
                operation=operation,
                action=lambda: stage_open_arm(
                    args.arm,
                    session_path=paths["session"],
                ),
            )
            print(f"{args.arm}_OPEN")
            print(f"opened_at={open_payload['opened_at']}")
            print(f"deadline_at={open_payload['deadline_at']}")
            print(f"allowed_budget_minutes={open_payload['allowed_budget_minutes']}")
            print("early_submit=allowed; late_submit=rejected")
            return 0

        if args.cmd == "submit-baseline":
            authoring = _load_authoring(args.authoring)
            sealed = _checkpointed(
                paths=paths,
                operation="SUBMIT_BASELINE",
                action=lambda: stage_capture_baseline(
                    authoring,
                    baseline_path=paths["baseline"],
                    session_path=paths["session"],
                ),
            )
            print("BASELINE_CLOSE")
            print(f"baseline_hash={sealed['baseline_hash']}")
            print(f"elapsed_seconds={sealed['elapsed_seconds']}")
            print(f"allowed_budget_minutes={sealed['allowed_budget_minutes']}")
            return 0

        if args.cmd == "generate-packet":
            packet = _checkpointed(
                paths=paths,
                operation="GENERATE_PACKET",
                action=lambda: stage_generate_packet(
                    baseline_path=paths["baseline"],
                    packet_path=paths["packet"],
                    session_path=paths["session"],
                ),
            )
            print("PACKET")
            print(f"packet_hash={packet['packet_hash']}")
            print(f"run_state={packet['run_state']}")
            print(f"block_reason={packet['block_reason']}")
            return 0

        if args.cmd == "submit-post":
            authoring = _load_authoring(args.authoring)
            sealed = _checkpointed(
                paths=paths,
                operation="SUBMIT_POST",
                action=lambda: stage_capture_post(
                    authoring,
                    post_path=paths["post"],
                    baseline_path=paths["baseline"],
                    packet_path=paths["packet"],
                    session_path=paths["session"],
                ),
            )
            print("POST_CLOSE")
            print(f"post_packet_hash={sealed['post_packet_hash']}")
            print(f"elapsed_seconds={sealed['elapsed_seconds']}")
            return 0

        if args.cmd == "export-review-package":
            package = _checkpointed(
                paths=paths,
                operation="EXPORT_REVIEW_PACKAGE",
                action=lambda: stage_build_review_package(
                    baseline_path=paths["baseline"],
                    post_path=paths["post"],
                    packet_path=paths["packet"],
                    session_path=paths["session"],
                    package_path=paths["package"],
                    mapping_path=paths["mapping"],
                    rubric_authoring_path=paths["rubric_authoring_export"],
                ),
            )
            print("REVIEW_PACKAGE")
            print(f"review_package_hash={package['review_package_hash']}")
            print(f"export_dir={paths['export_dir']}")
            print(f"export_package={paths['package']}")
            print(f"export_blank_rubric={paths['rubric_authoring_export']}")
            print(f"private_mapping={paths['mapping']}")
            print(
                "Arm-label blinding under separated export custody: give ONLY "
                "export_dir contents to the blinded reviewer."
            )
            return 0

        if args.cmd == "submit-rubric":
            authoring = _load_authoring(args.authoring)
            sealed = _checkpointed(
                paths=paths,
                operation="SUBMIT_RUBRIC",
                action=lambda: stage_capture_rubric(
                    authoring,
                    rubric_path=paths["rubric"],
                    baseline_path=paths["baseline"],
                    post_path=paths["post"],
                    packet_path=paths["packet"],
                    session_path=paths["session"],
                    package_path=paths["package"],
                    mapping_path=paths["mapping"],
                ),
            )
            print("RUBRIC_CLOSE")
            print(f"rubric_hash={sealed['rubric_hash']}")
            print("mapping reveal sidecar written after seal")
            return 0

        if args.cmd == "finalize":
            out = _checkpointed(
                paths=paths,
                operation="FINALIZE",
                complete=True,
                action=lambda: run_e0b_dv1_case(
                    baseline_path=paths["baseline"],
                    post_path=paths["post"],
                    rubric_path=paths["rubric"],
                    packet_path=paths["packet"],
                    session_path=paths["session"],
                    package_path=paths["package"],
                    mapping_path=paths["mapping"],
                    result_json_path=paths["result"],
                    decision_packet_path=paths["decision_packet"],
                    publish=bool(args.publish),
                ),
            )
            print("FINALIZE")
            print(f"comparison_hash={out['comparison']['comparison_hash']}")
            print(
                "comparison_observed_eligible="
                f"{out['comparison_observed_eligible']}"
            )
            print(f"observed_comparison_count={out['observed_comparison_count']}")
            print(
                "decision_value_disposition="
                f"{out['decision_value_disposition']}"
            )
            print(f"result={paths['result']}")
            return 0

        raise SystemExit(f"unknown command: {args.cmd}")
    except GvE0bDv1Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
