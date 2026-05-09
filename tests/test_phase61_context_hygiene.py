from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE61_BRIEF = ROOT / "docs" / "phase_brief" / "phase61-brief.md"
CURRENT_CONTEXT_JSON = ROOT / "docs" / "context" / "current_context.json"
PLANNER = ROOT / "docs" / "context" / "planner_packet_current.md"
BRIDGE = ROOT / "docs" / "context" / "bridge_contract_current.md"
README = ROOT / "README.md"


def test_phase61_brief_exposes_new_context_packet() -> None:
    text = PHASE61_BRIEF.read_text(encoding="utf-8")
    assert "## New Context Packet" in text
    assert "## What Was Done" in text
    assert "## What Is Locked" in text
    assert "## What Is Next" in text
    assert "## First Command" in text


def test_current_context_promotes_latest_active_phase() -> None:
    payload = json.loads(CURRENT_CONTEXT_JSON.read_text(encoding="utf-8"))
    assert int(payload["active_phase"]) == 65
    joined_done = " ".join(str(x) for x in payload["what_was_done"])
    assert "R64.1" in joined_done


def test_planner_bridge_and_readme_no_longer_advertise_phase60_hold_as_current() -> None:
    planner_text = PLANNER.read_text(encoding="utf-8")
    bridge_text = BRIDGE.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")

    for text in (planner_text, bridge_text, readme_text):
        assert "D-353" in text or "Phase 64" in text
        assert "provenance" in text.lower()
        assert "Phase 61 bootstrap authorized" not in text
        assert "not yet publicly executed" not in text
