from __future__ import annotations

from pathlib import Path


WIREFRAME = Path("docs/architecture/godview_dashboard_wireframe.md")
CARD_SPEC = Path("docs/architecture/godview_watchlist_card_spec.md")
DAILY_BRIEF = Path("docs/architecture/godview_daily_brief_spec.md")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dashboard_spec_artifacts_exist():
    assert WIREFRAME.exists()
    assert CARD_SPEC.exists()
    assert DAILY_BRIEF.exists()


def test_dashboard_sections_are_state_first():
    text = _text(WIREFRAME).lower()
    for section in (
        "commander view",
        "watchlist opportunity states",
        "thesis health",
        "entry discipline",
        "hold discipline",
        "godview market behavior",
        "risk and invalidation",
        "what changed today",
        "why not buy yet",
        "why not sell yet",
    ):
        assert section in text

    forbidden_runtime_terms = ("button handler",)
    assert not any(term in text for term in forbidden_runtime_terms)


def test_watchlist_card_fields_are_complete():
    text = _text(CARD_SPEC)
    for field in (
        "ticker",
        "theme",
        "current_state",
        "previous_state",
        "state_change_reason",
        "thesis_state",
        "entry_discipline",
        "hold_discipline",
        "market_behavior_summary",
        "risk_state",
        "freshness_summary",
        "observed_estimated_inferred_breakdown",
        "blocked_actions",
        "next_monitoring_questions",
    ):
        assert field in text


def test_dashboard_spec_forbids_orders_alerts_scores_and_rankings():
    combined = "\n".join(_text(path) for path in (WIREFRAME, CARD_SPEC, DAILY_BRIEF)).lower()

    assert "no dashboard runtime code" in combined
    assert "no buy or sell orders" in combined
    assert "no alerts" in combined
    assert "no scores" in combined
    assert "no rankings" in combined
