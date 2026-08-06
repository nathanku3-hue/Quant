from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE61_BRIEF = ROOT / "docs" / "phase_brief" / "phase61-brief.md"
CURRENT_CONTEXT_JSON = ROOT / "docs" / "context" / "current_context.json"
PLANNER = ROOT / "docs" / "context" / "planner_packet_current.md"
BRIDGE = ROOT / "docs" / "context" / "bridge_contract_current.md"
README = ROOT / "README.md"
ACTIVE_BRIEF = ROOT / "docs" / "context" / "ACTIVE_BRIEF"


def test_phase61_brief_exposes_new_context_packet() -> None:
    text = PHASE61_BRIEF.read_text(encoding="utf-8")
    assert "## New Context Packet" in text
    assert "## What Was Done" in text
    assert "## What Is Locked" in text
    assert "## What Is Next" in text
    assert "## First Command" in text


def test_current_context_preserves_terminal_and_active_named_product_gates() -> None:
    payload = json.loads(CURRENT_CONTEXT_JSON.read_text(encoding="utf-8"))
    assert int(payload["active_phase"]) == -1
    joined = " ".join(
        str(x)
        for key in ("what_was_done", "what_is_locked", "what_is_next")
        for x in payload[key]
    )
    assert "9af5259" in joined
    assert "pit-alpha-authority-cut-1-terminal" in joined
    assert "70/100" in joined
    assert "market" in joined.lower() and "packet" in joined.lower()
    assert "PAIR-DECISION-SERIES-1" in joined
    assert "episode 1" in joined.lower()
    assert "portfolio-alpha evidence" in joined.lower() and "0" in joined
    assert "Limited Live" in joined and "closed" in joined.lower()


def test_current_surfaces_select_one_active_operated_portfolio_gate() -> None:
    planner_text = PLANNER.read_text(encoding="utf-8")
    bridge_text = BRIDGE.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")
    active_brief = ACTIVE_BRIEF.read_text(encoding="utf-8").strip()

    assert active_brief == "docs/phase_brief/pair-decision-series-1-brief.md"
    for text in (planner_text, bridge_text, readme_text):
        assert "PAIR-DECISION-SERIES-1" in text
        assert "9af5259" in text
        assert "70/100" in text
        assert "portfolio-alpha evidence" in text.lower() and "0" in text
        assert "live" in text.lower() and "closed" in text.lower()
        assert "GV-CHALLENGER-PROMOTION-1 OPEN" not in text
