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
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_e0b_dv1_contradiction import (  # noqa: E402
    BUDGET_MINUTES,
    CASE_ID,
    DEFAULT_CASE_DIR,
    GvE0bDv1Error,
    load_capture_session,
    open_capture_session,
    run_e0b_dv1_case,
    sealed_adversarial_bundle,
    stage_build_review_package,
    stage_capture_baseline,
    stage_capture_post,
    stage_capture_rubric,
    stage_generate_packet,
    stage_open_arm,
)


def _case_paths(case_dir: Path) -> dict[str, Path]:
    captures = case_dir / "captures"
    return {
        "case_dir": case_dir,
        "baseline": captures / "baseline_seal.json",
        "packet": captures / "packet.json",
        "post": captures / "post_packet_seal.json",
        "rubric": captures / "rubric_scores.json",
        "session": captures / "session.json",
        "package": captures / "review_package.json",
        "mapping": captures / "review_mapping.sealed.json",
        "result": case_dir / "result.json",
        "decision_packet": case_dir / "decision_packet.md",
        "authoring_dir": captures / "authoring",
    }


def _load_authoring(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("authoring file must be a JSON object")
    return data


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
        print(f"reviewer_export: {paths['package']}")
        print("mapping: withheld from reviewer export (sealed separately)")
    print(
        "ledger_custody: tamper-evident under capture-process custody; "
        "local hashes do not prove personhood or independent wall-clock history"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gv_e0b_g08_capture",
        description="Narrow G08 capture runner (single-case, local, non-generic).",
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=DEFAULT_CASE_DIR,
        help="Case directory (default: data/gv_e0b/dv1_g08)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show capture ledger status")
    sub.add_parser("open-session", help="Open capture session + SESSION_OPEN event")

    p_open = sub.add_parser("open-arm", help="Open BASELINE or POST arm (starts budget clock)")
    p_open.add_argument("--arm", choices=("BASELINE", "POST"), required=True)

    p_base = sub.add_parser("submit-baseline", help="Submit baseline decision (early OK)")
    p_base.add_argument("--authoring", type=Path, required=True)

    sub.add_parser("generate-packet", help="Reveal GodView packet after baseline")

    p_post = sub.add_parser("submit-post", help="Submit post-packet decision (early OK)")
    p_post.add_argument("--authoring", type=Path, required=True)

    sub.add_parser(
        "export-review-package",
        help="Build blinded REVIEW_PACKAGE for independent reviewer",
    )

    p_rub = sub.add_parser("submit-rubric", help="Submit blinded rubric scores")
    p_rub.add_argument("--authoring", type=Path, required=True)

    p_fin = sub.add_parser("finalize", help="Verify chain, write result, optional publish")
    p_fin.add_argument(
        "--publish",
        action="store_true",
        help="Publish current decision only if close-eligible (real two-human)",
    )

    args = parser.parse_args(argv)
    paths = _case_paths(args.case_dir.resolve())
    paths["case_dir"].mkdir(parents=True, exist_ok=True)
    (paths["case_dir"] / "captures").mkdir(parents=True, exist_ok=True)

    try:
        if args.cmd == "status":
            return _print_status(paths)

        if args.cmd == "open-session":
            session = open_capture_session(
                bundle=sealed_adversarial_bundle(),
                session_path=paths["session"],
            )
            print("SESSION_OPEN")
            print(f"session_nonce={session['session_nonce']}")
            print(f"events_dir={session['events_dir']}")
            return 0

        if args.cmd == "open-arm":
            open_payload = stage_open_arm(
                args.arm,
                session_path=paths["session"],
            )
            print(f"{args.arm}_OPEN")
            print(f"opened_at={open_payload['opened_at']}")
            print(f"deadline_at={open_payload['deadline_at']}")
            print(f"allowed_budget_minutes={open_payload['allowed_budget_minutes']}")
            print("early_submit=allowed; late_submit=rejected")
            return 0

        if args.cmd == "submit-baseline":
            authoring = _load_authoring(args.authoring)
            sealed = stage_capture_baseline(
                authoring,
                baseline_path=paths["baseline"],
                session_path=paths["session"],
            )
            print("BASELINE_CLOSE")
            print(f"baseline_hash={sealed['baseline_hash']}")
            print(f"elapsed_seconds={sealed['elapsed_seconds']}")
            print(f"allowed_budget_minutes={sealed['allowed_budget_minutes']}")
            return 0

        if args.cmd == "generate-packet":
            packet = stage_generate_packet(
                baseline_path=paths["baseline"],
                packet_path=paths["packet"],
                session_path=paths["session"],
            )
            print("PACKET")
            print(f"packet_hash={packet['packet_hash']}")
            print(f"run_state={packet['run_state']}")
            print(f"block_reason={packet['block_reason']}")
            return 0

        if args.cmd == "submit-post":
            authoring = _load_authoring(args.authoring)
            sealed = stage_capture_post(
                authoring,
                post_path=paths["post"],
                baseline_path=paths["baseline"],
                packet_path=paths["packet"],
                session_path=paths["session"],
            )
            print("POST_CLOSE")
            print(f"post_packet_hash={sealed['post_packet_hash']}")
            print(f"elapsed_seconds={sealed['elapsed_seconds']}")
            return 0

        if args.cmd == "export-review-package":
            package = stage_build_review_package(
                baseline_path=paths["baseline"],
                post_path=paths["post"],
                packet_path=paths["packet"],
                session_path=paths["session"],
                package_path=paths["package"],
                mapping_path=paths["mapping"],
            )
            print("REVIEW_PACKAGE")
            print(f"review_package_hash={package['review_package_hash']}")
            print(f"export_path={paths['package']}")
            print("mapping withheld until rubric seal")
            print("Give only the export_path file to the blinded reviewer.")
            return 0

        if args.cmd == "submit-rubric":
            authoring = _load_authoring(args.authoring)
            sealed = stage_capture_rubric(
                authoring,
                rubric_path=paths["rubric"],
                baseline_path=paths["baseline"],
                post_path=paths["post"],
                packet_path=paths["packet"],
                session_path=paths["session"],
                package_path=paths["package"],
                mapping_path=paths["mapping"],
            )
            print("RUBRIC_CLOSE")
            print(f"rubric_hash={sealed['rubric_hash']}")
            print("mapping reveal sidecar written after seal")
            return 0

        if args.cmd == "finalize":
            out = run_e0b_dv1_case(
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
            )
            print("FINALIZE")
            print(f"comparison_hash={out['comparison']['comparison_hash']}")
            print(f"e0b_close_eligible={out['e0b_close_eligible']}")
            print(f"observed_comparison_count={out['observed_comparison_count']}")
            print(f"result={paths['result']}")
            return 0

        raise SystemExit(f"unknown command: {args.cmd}")
    except GvE0bDv1Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
