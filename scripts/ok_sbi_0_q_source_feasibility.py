"""OK-SBI-0 Step-1 Q source feasibility (outcome-blind, no provider calls).

Default path runs the admitted-custody audit for OK-SBI-0-S0-Q-SOURCE-BIND.
Use --conceptual-only to emit the unbound conceptual candidate without file IO.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is importable when invoked as a script.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from research.asymmetric_opportunity_v1.q_source_contract import (  # noqa: E402
    assert_no_silent_bridge,
    audit_admitted_custody_for_q,
    conceptual_candidate_contract,
    evaluate_q_source_feasibility,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON output path",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_ROOT,
        help="Authority worktree / repo root for admitted custody",
    )
    parser.add_argument(
        "--conceptual-only",
        action="store_true",
        help="Skip custody audit; emit conceptual candidate only",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()

    if args.conceptual_only:
        contract = conceptual_candidate_contract()
        assert_no_silent_bridge(contract)
        packet = evaluate_q_source_feasibility(
            contract, repo_root=root, include_custody_audit=False
        )
    else:
        attempt = audit_admitted_custody_for_q(repo_root=root)
        contract = attempt["contract"]
        assert_no_silent_bridge(contract)
        packet = evaluate_q_source_feasibility(
            contract, repo_root=root, include_custody_audit=False
        )
        packet["custody_audit"] = attempt["audit"]
        packet["q_source_binding_hash"] = attempt["audit"]["q_source_binding_hash"]
        packet["bind_slice_id"] = attempt["audit"]["bind_slice_id"]

    text = json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
