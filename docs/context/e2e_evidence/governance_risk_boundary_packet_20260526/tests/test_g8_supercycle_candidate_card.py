from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from opportunity_engine.candidate_card import (
    load_candidate_card,
    load_candidate_manifest,
    validate_candidate_card_bundle,
)
from opportunity_engine.candidate_card_schema import validate_candidate_card


CARD_PATH = Path("data/candidate_cards/MU_supercycle_candidate_card_v0.json")
MANIFEST_PATH = Path("data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json")


def _card() -> dict:
    return load_candidate_card(CARD_PATH)


def _manifest() -> dict:
    return load_candidate_manifest(MANIFEST_PATH)


def _errors(card: dict, manifest: dict | None = None) -> tuple[str, ...]:
    return validate_candidate_card(card, manifest=manifest or _manifest()).errors


def test_g8_candidate_card_requires_ticker():
    card = _card()
    card["ticker"] = ""

    assert any("ticker is required" in error for error in _errors(card))


def test_g8_candidate_card_requires_theme():
    card = _card()
    card["theme"] = ""

    assert any("theme is required" in error for error in _errors(card))


def test_g8_candidate_card_requires_manifest():
    card = _card()
    card["manifest_uri"] = ""

    assert any("manifest_uri is required" in error for error in _errors(card))


def test_g8_candidate_card_source_quality_summary_required():
    card = _card()
    card.pop("source_quality_summary")

    assert any("source_quality_summary" in error for error in _errors(card))


def test_g8_initial_state_limited_to_thesis_candidate_or_evidence_building():
    valid = validate_candidate_card(_card(), manifest=_manifest())
    assert valid.valid, valid.errors

    card = _card()
    card["state_mapping"]["initial_state"] = "BUYING_RANGE"

    assert any("initial_state" in error for error in _errors(card))


def test_g8_candidate_card_bundle_hash_validates_against_manifest():
    result = validate_candidate_card_bundle(CARD_PATH, MANIFEST_PATH)

    assert result.valid, result.errors


def test_g8_card_cannot_contain_score_or_rank():
    card = _card()
    card["primary_alpha"]["score"] = 99
    card["candidate_rank"] = 1

    errors = _errors(card)
    assert any("score" in error for error in errors)
    assert any("candidate_rank" in error for error in errors)


def test_g8_card_cannot_contain_buy_sell_signal():
    card = _card()
    card["secondary_alpha"]["buy_sell_signal"] = "buy"

    assert any("buy_sell_signal" in error for error in _errors(card))


def test_g8_card_cannot_emit_alert_or_broker_action():
    card = _card()
    card["forbidden_runtime"] = {"alert_emitted": True, "broker_action": "submit_order"}

    errors = _errors(card)
    assert any("alert_emitted" in error for error in errors)
    assert any("broker_action" in error for error in errors)


def test_g8_card_cannot_claim_buying_range():
    card = _card()
    card["state_mapping"]["allowed_next_states"].append("BUYING_RANGE")

    assert any("forbidden action states" in error for error in _errors(card))


def test_g8_yfinance_cannot_be_canonical_source():
    card = _card()
    card["source_quality_summary"]["canonical_sources"].append(
        {
            "source_id": "yfinance",
            "source_type": "tier2_discovery",
            "canonical": True,
        }
    )

    assert any("yfinance cannot be a canonical source" in error for error in _errors(card))


def test_g8_estimated_signals_cannot_be_presented_as_observed():
    card = _card()
    card["secondary_alpha"]["observed_signals_available"].append(
        {
            "signal_family": "ROTATION_SCORE",
            "quality_label": "estimated",
            "observed_estimated_or_inferred": "estimated",
        }
    )

    errors = _errors(card)
    assert any("estimated-only signal presented as observed" in error for error in errors)
    assert any("estimated signal cannot be presented as observed" in error for error in errors)


def test_g8_missing_provider_gap_is_explicit_for_options_iv_gamma_whales():
    card = deepcopy(_card())
    card["secondary_alpha"]["blocked_signals_due_to_provider_gap"] = [
        entry
        for entry in card["secondary_alpha"]["blocked_signals_due_to_provider_gap"]
        if entry["signal_family"] != "GAMMA_DEALER_MAP"
    ]

    assert any("GAMMA_DEALER_MAP" in error for error in _errors(card))
