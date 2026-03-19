from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE60_BRIEF = ROOT / "docs" / "phase_brief" / "phase60-brief.md"
BRIDGE = ROOT / "docs" / "context" / "bridge_contract_current.md"


def test_phase60_brief_no_longer_lists_resolved_validator_failures_as_active_blocker() -> None:
    text = PHASE60_BRIEF.read_text(encoding="utf-8")
    assert "Operational Validator Failures (Must Clear Immediately)" not in text
    assert "14-day feature freshness gap" not in text
    assert "2 zombie snapshot rows" not in text
    assert "**D-339 Outcome**:" in text
    assert "**Status**: CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD" in text


def test_bridge_evidence_used_points_to_execution_handover_not_kickoff_memo() -> None:
    text = BRIDGE.read_text(encoding="utf-8")
    assert "docs/handover/phase60_execution_handover_20260318.md" in text
    assert "docs/handover/phase60_kickoff_memo_20260318.md" not in text
