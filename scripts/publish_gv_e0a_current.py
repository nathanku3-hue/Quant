#!/usr/bin/env python
"""Operator CLI: E0 custody → certify E0A → publish current single decision.

Streamlit remains presentation-only. Operators use this path (not dashboard)
to refresh ``data/gv_fs0/gv_fs0_current_decision.json``.

Publication always re-verifies exact custody bytes and rebuilds the bound
research decision internally; there is no inject path for results or hashes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_e0a_operable import (  # noqa: E402
    E0A_DECISION_ID,
    E0A_PORTFOLIO_ACTION,
    E0A_RESEARCH_ACTION,
    build_e0a_research_decision,
    publish_e0a_current_decision,
    verify_e0_custody,
)
from core.gv_fs0_publish import (  # noqa: E402
    DEFAULT_CURRENT_DECISION_LOCK,
    DEFAULT_CURRENT_DECISION_TARGET,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish the single active E0A certified paper decision."
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_CURRENT_DECISION_TARGET,
        help="Publication target path for current decision JSON",
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=DEFAULT_CURRENT_DECISION_LOCK,
        help="Publication lock path",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root for E0 custody verification",
    )
    args = parser.parse_args(argv)

    custody = verify_e0_custody(args.root)
    research = build_e0a_research_decision(root=args.root)
    publication = publish_e0a_current_decision(
        target=args.target,
        lock_path=args.lock,
        root=args.root,
    )
    summary = {
        "status": publication.status,
        "target_path": publication.target_path,
        "target_file_sha256": publication.target_file_sha256,
        "certified_decision_result_id": publication.certified_decision_result_id,
        "certified_decision_result_hash": publication.certified_decision_result_hash,
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "subject": research["subject"],
        "module": research["module"],
        "decision_id": E0A_DECISION_ID,
        "research_decision_hash": research["research_decision_hash"],
        "rationale_ref": research["rationale_ref"],
        "mapping": f"{E0A_RESEARCH_ACTION} -> {E0A_PORTFOLIO_ACTION}",
        "custody_files": sorted(custody.keys()),
        "custody_hashes": dict(custody),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
