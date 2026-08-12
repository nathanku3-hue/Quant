#!/usr/bin/env python3
"""Print canonical research loop phase + next actions.

Usage (from authority worktree root):
  python scripts/print_research_loop_state.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    path = root / "docs" / "context" / "research_loop_state_current.json"
    if not path.is_file():
        print(f"MISSING {path}", file=sys.stderr)
        return 2
    state = json.loads(path.read_text(encoding="utf-8"))
    proc = state.get("process", {})
    prod = state.get("product", {})
    nxt = state.get("next_worker_slice", {})
    print("=== RESEARCH LOOP STATE ===")
    print(f"updated_at_utc:     {state.get('updated_at_utc')}")
    print(f"method:             {proc.get('method_id')} ({proc.get('method_status')})")
    print(f"loop_phase:         {proc.get('loop_phase')}")
    print(f"loop_phase_label:   {proc.get('loop_phase_label')}")
    print(f"last_completed:     {proc.get('last_completed_phase')} — {proc.get('last_completed_note')}")
    print(f"next_phase:         {proc.get('next_phase')} — {proc.get('next_phase_note')}")
    print(f"product.state:       {prod.get('state')}")
    print(f"alpha_evidence:     {prod.get('financial_alpha_evidence')}")
    print(f"next_worker:        {nxt.get('primary')} / recommended={nxt.get('recommended')}")
    print("forbidden_now:")
    for item in state.get("forbidden_now", []):
        print(f"  - {item}")
    print("active_tracks:")
    for t in state.get("active_tracks", []):
        print(
            f"  - {t.get('track_id')}: {t.get('status')} | phase={t.get('loop_phase')} | next={t.get('next')}"
        )
    diag = state.get("last_empirical_diagnosis")
    if diag:
        print(
            f"last_diagnosis:     {diag.get('slice')} → {diag.get('result')} "
            f"fail={diag.get('first_fail_layer')} route={diag.get('route')}"
        )
    print(f"source: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
