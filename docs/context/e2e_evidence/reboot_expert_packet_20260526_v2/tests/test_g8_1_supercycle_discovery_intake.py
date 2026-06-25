from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from opportunity_engine.discovery_intake import (
    load_candidate_intake_manifest,
    load_candidate_intake_queue,
    load_discovery_theme_taxonomy,
    validate_discovery_intake_bundle,
)
from opportunity_engine.discovery_intake_schema import (
    REQUIRED_THEME_IDS,
    validate_candidate_intake_queue,
    validate_discovery_theme_taxonomy,
)


THEME_PATH = Path("data/discovery/supercycle_discovery_themes_v0.json")
QUEUE_PATH = Path("data/discovery/supercycle_candidate_intake_queue_v0.json")
MANIFEST_PATH = Path("data/discovery/supercycle_candidate_intake_queue_v0.manifest.json")


def _queue() -> dict:
    return load_candidate_intake_queue(QUEUE_PATH)


def _manifest() -> dict:
    return load_candidate_intake_manifest(MANIFEST_PATH)


def _errors(queue: dict, manifest: dict | None = None) -> tuple[str, ...]:
    return validate_candidate_intake_queue(queue, manifest=manifest or _manifest()).errors


def test_g8_1_discovery_themes_define_required_taxonomy():
    taxonomy = load_discovery_theme_taxonomy(THEME_PATH)

    result = validate_discovery_theme_taxonomy(taxonomy)

    assert result.valid, result.errors
    assert {theme["theme_id"] for theme in taxonomy["themes"]} == REQUIRED_THEME_IDS


def test_g8_1_intake_queue_requires_ticker():
    queue = _queue()
    queue["candidate_intake_items"][1]["ticker"] = ""

    assert any("ticker is required" in error for error in _errors(queue))


def test_g8_1_intake_queue_requires_theme_candidates():
    queue = _queue()
    queue["candidate_intake_items"][1]["theme_candidates"] = []

    assert any("theme_candidates is required" in error for error in _errors(queue))


def test_g8_1_intake_queue_requires_evidence_needed():
    queue = _queue()
    queue["candidate_intake_items"][1]["evidence_needed"] = []

    assert any("evidence_needed is required" in error for error in _errors(queue))


def test_g8_1_intake_queue_requires_thesis_breakers():
    queue = _queue()
    queue["candidate_intake_items"][1]["thesis_breakers_to_check"] = []

    assert any("thesis_breakers_to_check is required" in error for error in _errors(queue))


def test_g8_1_intake_queue_requires_provider_gaps():
    queue = _queue()
    queue["candidate_intake_items"][1]["provider_gaps"] = []

    assert any("provider_gaps is required" in error for error in _errors(queue))


def test_g8_1_intake_queue_cannot_rank():
    queue = _queue()
    queue["candidate_intake_items"][1]["candidate_rank"] = 1

    assert any("candidate_rank" in error for error in _errors(queue))


def test_g8_1_intake_queue_cannot_score():
    queue = _queue()
    queue["candidate_intake_items"][1]["candidate_score"] = 99

    assert any("candidate_score" in error for error in _errors(queue))


def test_g8_1_intake_queue_cannot_emit_buy_sell_hold():
    queue = _queue()
    queue["candidate_intake_items"][1]["decision_call"] = "buy"

    assert any("forbidden action call" in error for error in _errors(queue))


def test_g8_1_intake_queue_cannot_mark_validated():
    queue = _queue()
    queue["candidate_intake_items"][1]["current_status"] = "validated_thesis"

    errors = _errors(queue)
    assert any("current_status must be intake_only or candidate_card_exists" in error for error in errors)
    assert any("DELL current_status must be intake_only" in error for error in errors)


def test_g8_1_intake_queue_cannot_promote_to_action_state():
    queue = _queue()
    queue["candidate_intake_items"][1]["state"] = "BUYING_RANGE"

    assert any("forbidden promotion state" in error for error in _errors(queue))


def test_g8_1_mu_is_only_existing_candidate_card():
    queue = _queue()
    result = validate_candidate_intake_queue(queue, manifest=_manifest())

    assert result.valid, result.errors
    statuses = {item["ticker"]: item["current_status"] for item in queue["candidate_intake_items"]}
    assert statuses == {
        "MU": "candidate_card_exists",
        "DELL": "intake_only",
        "INTC": "intake_only",
        "AMD": "intake_only",
        "LRCX": "intake_only",
        "ALB": "intake_only",
    }

    bad_queue = deepcopy(queue)
    bad_queue["candidate_intake_items"][3]["current_status"] = "candidate_card_exists"

    assert any("MU must be the only candidate_card_exists item" in error for error in _errors(bad_queue))


def test_g8_1_yfinance_not_canonical():
    queue = _queue()
    queue["candidate_intake_items"][1]["known_source_candidates"].append(
        {
            "source_id": "yfinance",
            "canonical": True,
            "note": "bad canonical source",
        }
    )

    assert any("yfinance cannot be a canonical source" in error for error in _errors(queue))


def test_g8_1_any_canonical_source_is_rejected():
    queue = _queue()
    queue["candidate_intake_items"][1]["known_source_candidates"].append(
        {
            "source_id": "official_source_probe",
            "canonical": True,
            "note": "canonical source should not be allowed in intake",
        }
    )

    assert any("canonical sources are not allowed" in error for error in _errors(queue))


def test_g8_1_scope_and_authority_are_exact():
    queue = _queue()
    queue["scope"] = "PH65_G8_1_CANDIDATE_RANKING"
    queue["authority"] = "candidate_ranking_authority"

    errors = _errors(queue)
    assert any("scope must be PH65_G8_1_INTAKE_ONLY" in error for error in errors)
    assert any("authority must be candidate_discovery_intake_only" in error for error in errors)


def test_g8_1_intake_queue_cannot_claim_second_candidate_card_authority():
    queue = _queue()
    queue["second_candidate_card"] = "approved"
    queue["candidate_intake_items"][1]["promotion_note"] = "promote to candidate card"

    errors = _errors(queue)
    assert any("second_candidate_card" in error for error in errors)
    assert any("forbidden promotion wording" in error for error in errors)


def test_g8_1_intake_queue_cannot_claim_second_candidate_card_authority_variant():
    queue = _queue()
    queue["second_candidate_card_authority"] = "approved"

    assert any("second_candidate_card_authority" in error for error in _errors(queue))


def test_g8_1_arbitrary_nested_canonical_true_is_rejected():
    queue = _queue()
    queue["metadata"] = {"nested": {"canonical": True}}

    assert any("canonical=true is not allowed" in error for error in _errors(queue))


def test_g8_1_manifest_required():
    queue = _queue()

    assert any("manifest is required" in error for error in validate_candidate_intake_queue(queue).errors)


def test_g8_1_manifest_required_fields_are_enforced():
    queue = _queue()
    manifest = _manifest()
    manifest.pop("artifact_uri")

    assert any("manifest missing fields: artifact_uri" in error for error in _errors(queue, manifest))


def test_g8_1_manifest_queue_id_must_match_queue():
    queue = _queue()
    manifest = _manifest()
    manifest["queue_id"] = "WRONG_QUEUE"

    assert any("manifest queue_id must match queue queue_id" in error for error in _errors(queue, manifest))


def test_g8_1_manifest_row_count_must_match_queue_length():
    queue = _queue()
    manifest = _manifest()
    manifest["row_count"] = 999

    assert any("manifest row_count must match candidate_intake_items length" in error for error in _errors(queue, manifest))


def test_g8_1_manifest_seed_tickers_must_match_required_order():
    queue = _queue()
    manifest = _manifest()
    manifest["seed_tickers"] = ["MU", "AMD", "DELL", "INTC", "LRCX", "ALB"]

    assert any("manifest seed_tickers must match required seed ticker order" in error for error in _errors(queue, manifest))


def test_g8_1_manifest_status_policy_must_match_queue_status_policy():
    queue = _queue()
    manifest = _manifest()
    manifest["status_policy"]["candidate_card_exists"] = ["MU", "AMD"]

    assert any("manifest status_policy.candidate_card_exists" in error for error in _errors(queue, manifest))


def test_g8_1_manifest_canonical_sources_must_be_empty():
    queue = _queue()
    manifest = _manifest()
    manifest["source_policy"]["canonical_sources"] = [{"source_id": "official", "canonical": True}]

    errors = _errors(queue, manifest)
    assert any("canonical sources are not allowed" in error for error in errors)
    assert any("manifest source_policy.canonical_sources must be empty" in error for error in errors)


def test_g8_1_manifest_hash_validates():
    result = validate_discovery_intake_bundle(QUEUE_PATH, MANIFEST_PATH)

    assert result.valid, result.errors
