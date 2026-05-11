from __future__ import annotations

from pathlib import Path

from opportunity_engine.discovery_intake import (
    load_candidate_intake_manifest,
    load_candidate_intake_queue,
)
from opportunity_engine.discovery_intake_schema import (
    REQUIRED_DISCOVERY_ORIGINS,
    DiscoveryOrigin,
    validate_candidate_intake_queue,
)


QUEUE_PATH = Path("data/discovery/supercycle_candidate_intake_queue_v0.json")
MANIFEST_PATH = Path("data/discovery/supercycle_candidate_intake_queue_v0.manifest.json")


def _queue() -> dict:
    return load_candidate_intake_queue(QUEUE_PATH)


def _manifest() -> dict:
    return load_candidate_intake_manifest(MANIFEST_PATH)


def _errors(queue: dict, manifest: dict | None = None) -> tuple[str, ...]:
    return validate_candidate_intake_queue(queue, manifest=manifest or _manifest()).errors


def _item(queue: dict, ticker: str) -> dict:
    return next(item for item in queue["candidate_intake_items"] if item["ticker"] == ticker)


def test_discovery_origin_required():
    queue = _queue()
    del _item(queue, "DELL")["discovery_origin"]

    assert any("discovery_origin" in error for error in _errors(queue))


def test_origin_evidence_required():
    queue = _queue()
    _item(queue, "DELL")["origin_evidence"] = []

    assert any("origin_evidence is required" in error for error in _errors(queue))


def test_scout_path_required_for_system_scouted():
    queue = _queue()
    dell = _item(queue, "DELL")
    dell["discovery_origin"] = [DiscoveryOrigin.SYSTEM_SCOUTED.value]
    dell["is_user_seeded"] = False
    dell["is_system_scouted"] = True
    dell["scout_path"] = []

    assert any("scout_path is required for system_scouted" in error for error in _errors(queue))


def test_existing_six_not_pure_system_scouted():
    queue = _queue()
    result = validate_candidate_intake_queue(queue, manifest=_manifest())

    assert result.valid, result.errors
    assert {item["ticker"] for item in queue["candidate_intake_items"]} == {
        "MU",
        "DELL",
        "INTC",
        "AMD",
        "LRCX",
        "ALB",
    }
    for item in queue["candidate_intake_items"]:
        assert item["is_system_scouted"] is False
        assert DiscoveryOrigin.SYSTEM_SCOUTED.value not in item["discovery_origin"]


def test_user_seeded_distinct_from_system_scouted():
    queue = _queue()
    dell = _item(queue, "DELL")
    dell["discovery_origin"] = [
        DiscoveryOrigin.USER_SEEDED.value,
        DiscoveryOrigin.SYSTEM_SCOUTED.value,
    ]
    dell["is_system_scouted"] = True

    assert any("user_seeded and system_scouted must remain distinct" in error for error in _errors(queue))


def test_mu_candidate_card_exists_but_not_validated():
    queue = _queue()
    mu = _item(queue, "MU")

    assert mu["current_status"] == "candidate_card_exists"
    assert mu["is_validated"] is False
    assert mu["is_actionable"] is False

    mu["is_validated"] = True

    assert any("is_validated must be false" in error for error in _errors(queue))


def test_no_intake_item_is_actionable():
    queue = _queue()

    assert all(item["is_actionable"] is False for item in queue["candidate_intake_items"])

    _item(queue, "ALB")["is_actionable"] = True

    assert any("is_actionable must be false" in error for error in _errors(queue))


def test_intake_queue_cannot_rank():
    queue = _queue()
    _item(queue, "DELL")["candidate_rank"] = 1

    assert any("candidate_rank" in error for error in _errors(queue))


def test_intake_queue_cannot_score():
    queue = _queue()
    _item(queue, "DELL")["candidate_score"] = 99

    assert any("candidate_score" in error for error in _errors(queue))


def test_intake_queue_cannot_emit_buy_sell_hold():
    queue = _queue()
    _item(queue, "DELL")["decision_call"] = "buy"

    assert any("forbidden action call" in error for error in _errors(queue))


def test_intake_queue_cannot_hide_buy_sell_hold_in_list_values():
    queue = _queue()
    _item(queue, "DELL")["evidence_needed"].append("buy signal")

    assert any("forbidden action call" in error for error in _errors(queue))


def test_research_capture_is_not_canonical_evidence():
    queue = _queue()
    dell = _item(queue, "DELL")
    dell["discovery_origin"] = [
        DiscoveryOrigin.USER_SEEDED.value,
        DiscoveryOrigin.NEWS_RESEARCH_CAPTURE.value,
    ]
    dell["origin_evidence"].append(
        {
            "origin": DiscoveryOrigin.NEWS_RESEARCH_CAPTURE.value,
            "source_id": "research_capture_example",
            "canonical": True,
            "note": "research capture cannot become canonical evidence",
        }
    )

    assert any("canonical=true is not allowed" in error for error in _errors(queue))


def test_local_factor_scout_origin_defined_but_not_used_until_g8_1b():
    queue = _queue()

    assert DiscoveryOrigin.LOCAL_FACTOR_SCOUT.value in REQUIRED_DISCOVERY_ORIGINS
    assert all(
        DiscoveryOrigin.LOCAL_FACTOR_SCOUT.value not in item["discovery_origin"]
        for item in queue["candidate_intake_items"]
    )

    _item(queue, "DELL")["discovery_origin"].append(DiscoveryOrigin.LOCAL_FACTOR_SCOUT.value)

    assert any("LOCAL_FACTOR_SCOUT is defined but held until G8.1B" in error for error in _errors(queue))
