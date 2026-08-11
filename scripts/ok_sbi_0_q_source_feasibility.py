"""OK-SBI-0 Step-1 Q source feasibility (outcome-blind, no provider calls)."""

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
    args = parser.parse_args()

    contract = conceptual_candidate_contract()
    assert_no_silent_bridge(contract)
    packet = evaluate_q_source_feasibility(contract)
    text = json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    # Non-zero if blocked so CI can see status without failing the freeze write path.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
