from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from opportunity_engine.candidate_card import (
    load_candidate_card,
    load_candidate_manifest,
    validate_candidate_card_bundle,
)
from opportunity_engine.candidate_card_schema import validate_candidate_card
from opportunity_engine.factor_scout import (
    load_factor_scout_manifest,
    load_factor_scout_output,
)
from opportunity_engine.factor_scout_schema import SCOUT_DISCOVERY_ORIGIN, SCOUT_MODEL_ID


CARD_PATH = Path("data/candidate_cards/MSFT_supercycle_candidate_card_v0.json")
MANIFEST_PATH = Path("data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json")
SCOUT_OUTPUT_PATH = Path("data/discovery/local_factor_scout_output_tiny_v0.json")
SCOUT_MANIFEST_PATH = Path("data/discovery/local_factor_scout_output_tiny_v0.manifest.json")
CANDIDATE_CARD_DIR = Path("data/candidate_cards")


def _card() -> dict:
    return load_candidate_card(CARD_PATH)


def _manifest() -> dict:
    return load_candidate_manifest(MANIFEST_PATH)


def _scout_output() -> dict:
    return load_factor_scout_output(SCOUT_OUTPUT_PATH)


def _scout_manifest() -> dict:
    return load_factor_scout_manifest(SCOUT_MANIFEST_PATH)


def _scout_item() -> dict:
    return _scout_output()["items"][0]


def _errors(card: dict, manifest: dict | None = None) -> tuple[str, ...]:
    return validate_candidate_card(card, manifest=manifest or _manifest()).errors


def _g8_2_errors(card: dict, manifest: dict | None = None) -> tuple[str, ...]:
    errors = list(_errors(card, manifest=manifest or _manifest()))
    scout_output = _scout_output()
    scout_manifest = _scout_manifest()
    item = scout_output["items"][0]

    if card.get("ticker") != item.get("ticker"):
        errors.append("card ticker must match LOCAL_FACTOR_SCOUT output ticker")
    if card.get("company_name") != item.get("company_name"):
        errors.append("card company_name must match LOCAL_FACTOR_SCOUT output company_name")
    if card.get("discovery_origin") != SCOUT_DISCOVERY_ORIGIN:
        errors.append(f"discovery_origin must be {SCOUT_DISCOVERY_ORIGIN}")
    if card.get("scout_model_id") != SCOUT_MODEL_ID:
        errors.append(f"scout_model_id must be {SCOUT_MODEL_ID}")
    if card.get("source_intake_item_id") != f"{scout_output['scout_output_id']}:MSFT:{item['asof_date']}":
        errors.append("source_intake_item_id must identify the existing MSFT scout item")
    if card.get("source_intake_manifest_uri") != str(SCOUT_MANIFEST_PATH).replace("\\", "/"):
        errors.append("source_intake_manifest_uri must reference the scout output manifest")
    if card.get("candidate_card_manifest_uri") != str(MANIFEST_PATH).replace("\\", "/"):
        errors.append("candidate_card_manifest_uri must reference the card manifest")

    if scout_manifest.get("tickers") != ["MSFT"]:
        errors.append("LOCAL_FACTOR_SCOUT manifest must contain only MSFT for G8.2")
    return tuple(errors)


def test_g8_2_card_requires_existing_local_factor_scout_item():
    card = _card()
    scout = _scout_output()
    item = _scout_item()

    assert scout["scout_model_id"] == SCOUT_MODEL_ID
    assert len(scout["items"]) == 1
    assert item["ticker"] == "MSFT"
    assert card["source_intake_item_id"] == f"{scout['scout_output_id']}:MSFT:{item['asof_date']}"
    assert card["source_intake_manifest_uri"] == str(SCOUT_MANIFEST_PATH).replace("\\", "/")
    assert not _g8_2_errors(card)


def test_g8_2_card_ticker_must_match_scout_output():
    card = _card()
    scout_item = _scout_item()
    assert card["ticker"] == scout_item["ticker"]

    mismatch = deepcopy(card)
    mismatch["ticker"] = "AMD"

    assert any("ticker must match" in error for error in _g8_2_errors(mismatch))


def test_g8_2_discovery_origin_is_local_factor_scout():
    card = _card()

    assert card["discovery_origin"] == SCOUT_DISCOVERY_ORIGIN
    assert card["scout_model_id"] == SCOUT_MODEL_ID
    assert card["governance"]["not_validated"] is True
    assert card["governance"]["not_actionable"] is True


def test_g8_2_card_requires_source_intake_manifest():
    card = _card()
    card["source_intake_manifest_uri"] = ""

    assert any("source_intake_manifest_uri" in error for error in _g8_2_errors(card))


def test_g8_2_card_requires_manifest():
    result = validate_candidate_card_bundle(CARD_PATH, MANIFEST_PATH)
    assert result.valid, result.errors

    card = _card()
    card["manifest_uri"] = ""

    assert any("manifest_uri is required" in error for error in _errors(card))


def test_g8_2_card_cannot_expose_factor_score():
    card = _card()
    card["primary_alpha"]["factor_score"] = 0.99

    assert any("factor_score" in error for error in _errors(card))


def test_g8_2_card_cannot_expose_rank():
    card = _card()
    card["candidate_rank"] = 1

    assert any("candidate_rank" in error for error in _errors(card))


def test_g8_2_card_cannot_emit_buy_sell_hold():
    card = _card()
    card["secondary_alpha"]["buy_sell_signal"] = "buy"

    assert any("buy_sell_signal" in error for error in _errors(card))


def test_g8_2_card_cannot_mark_validated():
    card = _card()
    card["governance"]["not_validated"] = False

    assert any("governance.not_validated must be true" in error for error in _errors(card))


def test_g8_2_card_cannot_mark_actionable():
    card = _card()
    card["governance"]["not_actionable"] = False

    assert any("governance.not_actionable must be true" in error for error in _errors(card))


def test_g8_2_card_cannot_claim_buying_range():
    card = _card()
    card["state_mapping"]["allowed_next_states"].append("BUYING_RANGE")

    assert any("forbidden action states" in error for error in _errors(card))


def test_g8_2_card_cannot_emit_alert_or_broker_action():
    card = _card()
    card["runtime"] = {"alert_emitted": True, "broker_action": "submit_order"}

    errors = _errors(card)
    assert any("alert_emitted" in error for error in errors)
    assert any("broker_action" in error for error in errors)


def test_g8_2_mu_and_msft_are_only_candidate_cards():
    card_files = sorted(path.name for path in CANDIDATE_CARD_DIR.glob("*_candidate_card_v0.json"))
    manifest_files = sorted(path.name for path in CANDIDATE_CARD_DIR.glob("*_candidate_card_v0.manifest.json"))

    assert card_files == [
        "MSFT_supercycle_candidate_card_v0.json",
        "MU_supercycle_candidate_card_v0.json",
    ]
    assert manifest_files == [
        "MSFT_supercycle_candidate_card_v0.manifest.json",
        "MU_supercycle_candidate_card_v0.manifest.json",
    ]
    assert _manifest()["source_intake_manifest_uri"] == str(SCOUT_MANIFEST_PATH).replace("\\", "/")
    assert _scout_manifest()["tickers"] == ["MSFT"]
