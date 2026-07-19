"""E0B-DV1 Contradiction Case (G08) focused tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from core.gv_e0b_dv1_contradiction import (
    BLOCK_REASON,
    CASE_ID,
    EXPECTED_CERTIFIED_RESULT_HASH,
    RUBRIC_ITEMS,
    GvE0bDv1Error,
    build_comparison,
    build_comparison_presentation,
    build_godview_packet,
    render_e0b_dv1_comparison,
    sealed_adversarial_bundle,
    sealed_human_baseline,
    sealed_post_packet_decision,
)

ROOT = Path(__file__).resolve().parents[2]


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def subheader(self, body: str) -> None:
        self.calls.append(("subheader", body))

    def table(self, data: Any) -> None:
        self.calls.append(("table", data))

    def caption(self, body: str) -> None:
        self.calls.append(("caption", body))


def test_sealed_bundle_has_indispensable_contradiction() -> None:
    bundle = sealed_adversarial_bundle()
    assert bundle["case_id"] == CASE_ID
    claims = bundle["indispensable_claims"]
    assert len(claims) == 2
    assert all(c["indispensable"] for c in claims)
    assert claims[0]["fact_key"] == claims[1]["fact_key"]
    assert claims[0]["value"] != claims[1]["value"]
    assert isinstance(bundle["bundle_hash"], str) and len(bundle["bundle_hash"]) == 64


def test_godview_packet_blocks_g08_without_average() -> None:
    packet = build_godview_packet()
    assert packet["run_state"] == "BLOCKED"
    assert packet["block_reason"] == BLOCK_REASON
    assert packet["acceptance_case"] == "G08"
    assert packet["engine_may_not_average"] is True
    assert packet["engine_may_not_majority_vote"] is True
    assert packet["candidate"] == "NONE"
    assert packet["alpha_claim"] is False
    contradictions = packet["contradictions"]
    assert len(contradictions) == 1
    values = contradictions[0]["values"]
    assert set(values) == {2, 8}
    # Must not emit a single reconciled mean as the claim value.
    assert 5 not in values
    assert (2 + 8) / 2 not in values


def test_baseline_advances_before_packet_post_holds() -> None:
    baseline = sealed_human_baseline()
    post = sealed_post_packet_decision()
    assert baseline["sealed_before_packet"] is True
    assert baseline["action"] == "ADVANCE_TO_FULL_RESEARCH"
    assert list(baseline["contradictions_recognized"]) == []
    assert post["action"] == "HOLD_FOR_EVIDENCE"
    assert post["portfolio_action"] == "NO_POSITION"
    assert "qualified_sellable_supply_relief" in post["missing_evidence"][0]
    assert post["contradictions_recognized"]


def test_comparison_binds_no_position_cert_and_rubric_delta() -> None:
    comparison = build_comparison()
    assert comparison["acceptance_case"] == "G08"
    assert comparison["score_claim"]["shipped_product_score"] == 39
    assert comparison["score_claim"]["score_frozen"] is True
    assert comparison["score_claim"]["alpha_claim"] is False
    assert comparison["delta"]["action_change"] is True
    assert comparison["delta"]["total_score_difference"] > 0
    assert set(comparison["delta"]["rubric_item_deltas"]) == set(RUBRIC_ITEMS)
    binding = comparison["no_position_cert_binding"]
    assert binding["certified_decision_result_hash"] == EXPECTED_CERTIFIED_RESULT_HASH
    assert binding["portfolio_action"] == "NO_POSITION"
    assert len(comparison["comparison_hash"]) == 64


def test_comparison_is_deterministic() -> None:
    a = build_comparison()
    b = build_comparison()
    assert a["comparison_hash"] == b["comparison_hash"]
    assert a["bundle_hash"] == b["bundle_hash"]
    assert a["packet_hash"] == b["packet_hash"]


def test_presentation_rows_and_render() -> None:
    comparison = build_comparison()
    presentation = build_comparison_presentation(comparison)
    rows = {row["label"]: row["value"] for row in presentation["rows"]}
    assert rows["BlockReason"] == BLOCK_REASON
    assert rows["BaselineAction"] == "ADVANCE_TO_FULL_RESEARCH"
    assert rows["PostPacketAction"] == "HOLD_FOR_EVIDENCE"
    assert rows["BoundCertifiedResultHash"] == EXPECTED_CERTIFIED_RESULT_HASH
    assert rows["AlphaClaim"] == "FALSE"
    assert rows["ShippedProductScore"] == "39"
    renderer = FakeRenderer()
    rendered = render_e0b_dv1_comparison(renderer, comparison=comparison)
    assert rendered["title"].startswith("GV-E0B-DV1")
    assert [name for name, _ in renderer.calls] == ["subheader", "table", "caption"]


def test_cert_binding_fails_on_tampered_current(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"certified_decision_result_hash":"0"*64,"decision":{"decision_id":"X","action":"NO_POSITION"}}', encoding="utf-8")
    with pytest.raises(GvE0bDv1Error):
        build_comparison(current_decision_path=bad)
