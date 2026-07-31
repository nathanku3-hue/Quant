from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE60_BRIEF = ROOT / "docs" / "phase_brief" / "phase60-brief.md"
BRIDGE = ROOT / "docs" / "context" / "bridge_contract_current.md"
HANDOVER = ROOT / "docs" / "handover" / "phase60_execution_handover_20260318.md"


def test_phase60_brief_status_is_formally_closed_blocked_hold() -> None:
    text = PHASE60_BRIEF.read_text(encoding="utf-8")
    assert "**Status**: CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD" in text
    assert "274" in text
    assert "D-345 Outcome" in text


def test_historical_handover_remains_closed_while_current_bridge_moves_forward() -> None:
    bridge_text = BRIDGE.read_text(encoding="utf-8")
    handover_text = HANDOVER.read_text(encoding="utf-8")
    assert "GV-OPERATED-PORTFOLIO-10-TRANSITION-1R" in bridge_text
    assert "ACTIVE_STATUS" in bridge_text
    assert "BLOCKED_EVIDENCE_ONLY_HOLD" in handover_text or "CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD" in handover_text
    assert "`D-284`..`D-347`" in handover_text
