from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "contracts/gv_fs0/v1/tables"
REGISTRIES = ROOT / "contracts/gv_fs0/v1/registries"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _assign_intra_rank(candidates: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, int], list[dict]] = {}
    for candidate in candidates:
        group = (
            candidate["effective_timestamp"],
            candidate["session"],
            candidate["event_type_rank"],
        )
        groups.setdefault(group, []).append(candidate)
    result: list[dict] = []
    for group in sorted(groups):
        seen: set[tuple[int, str, int]] = set()
        ordered = []
        for candidate in groups[group]:
            key = (
                candidate["source_sequence"],
                candidate["source_intent_id"],
                candidate["generated_event_slot"],
            )
            if key in seen:
                raise ValueError("DUPLICATE_ORIGIN_ORDER_KEY")
            seen.add(key)
            ordered.append((key, candidate))
        for index, (_, candidate) in enumerate(sorted(ordered, key=lambda item: item[0])):
            result.append({**candidate, "intra_rank_sequence": index})
    return result


def test_event_ranks_are_exact_and_monotonic() -> None:
    table = _load(TABLES / "gv_fs0_event_ranks_v1.json")
    observed = [(entry["event_type_rank"], entry["event_type"]) for entry in table["entries"]]
    assert observed == [
        (10, "DECISION_ACCEPTED"),
        (20, "EXECUTION"),
        (30, "FEE_OR_COST"),
        (40, "CASH_MOVEMENT"),
        (50, "POSITION_MOVEMENT"),
        (60, "DIVIDEND_ENTITLEMENT"),
        (70, "DIVIDEND_PAYMENT"),
        (80, "SESSION_VALUATION"),
        (90, "CERTIFICATION_REFERENCE"),
    ]
    assert len({rank for rank, _ in observed}) == len(observed)


def test_generated_slots_are_exact_and_not_hidden_in_python_only() -> None:
    table = _load(TABLES / "gv_fs0_generated_event_slots_v1.json")
    observed = {
        (entry["source_type"], entry["event_type"]): entry["generated_event_slot"]
        for entry in table["entries"]
    }
    assert observed[("EXECUTION_INTENT", "EXECUTION")] == 10
    assert observed[("EXECUTION_INTENT", "CASH_MOVEMENT")] == 20
    assert observed[("EXECUTION_INTENT", "POSITION_MOVEMENT")] == 30
    assert observed[("EXPLICIT_FEE", "FEE_OR_COST")] == 10
    assert observed[("EXPLICIT_FEE", "CASH_MOVEMENT")] == 20
    assert observed[("DIVIDEND_PAYMENT_INSTRUCTION", "DIVIDEND_PAYMENT")] == 10
    assert observed[("CERTIFICATION", "CERTIFICATION_REFERENCE")] == 10
    assert ("DIVIDEND_PAYMENT_INSTRUCTION", "CASH_MOVEMENT") not in observed


def test_origin_order_key_deterministically_assigns_contiguous_intra_rank_sequence() -> None:
    base = {
        "effective_timestamp": "2026-07-17T00:00:00.000000Z",
        "session": "2026-07-17",
        "event_type_rank": 40,
    }
    candidates = [
        {**base, "source_sequence": 2, "source_intent_id": "X:C", "generated_event_slot": 20},
        {**base, "source_sequence": 0, "source_intent_id": "X:A", "generated_event_slot": 20},
        {**base, "source_sequence": 1, "source_intent_id": "X:B", "generated_event_slot": 10},
    ]
    ordered = _assign_intra_rank(candidates)
    assert [row["source_sequence"] for row in ordered] == [0, 1, 2]
    assert [row["intra_rank_sequence"] for row in ordered] == [0, 1, 2]


def test_duplicate_origin_key_is_registered_and_maps_to_causality_false() -> None:
    duplicate = {
        "effective_timestamp": "2026-07-17T00:00:00.000000Z",
        "session": "2026-07-17",
        "event_type_rank": 40,
        "source_sequence": 0,
        "source_intent_id": "X:A",
        "generated_event_slot": 20,
    }
    with pytest.raises(ValueError, match="DUPLICATE_ORIGIN_ORDER_KEY"):
        _assign_intra_rank([duplicate, dict(duplicate)])

    registry = _load(REGISTRIES / "gv_fs0_certification_failure_registry_v1.json")
    entry = next(item for item in registry["entries"] if item["code"] == "DUPLICATE_ORIGIN_ORDER_KEY")
    assert entry["applicable_checks"] == ["timestamp_causality_valid"]
    assert entry["applicable_outcomes"] == ["FALSE"]
    assert entry["applicable_emitters"] == ["PRIMARY", "VERIFIER"]


def test_global_order_assigns_semantic_sequence_after_event_id_exists() -> None:
    events = [
        {
            "effective_timestamp": "2026-07-17T00:00:00.000000Z",
            "session": "2026-07-17",
            "event_type_rank": 40,
            "intra_rank_sequence": 0,
            "event_id": "EVT_" + "b" * 64,
        },
        {
            "effective_timestamp": "2026-07-17T00:00:00.000000Z",
            "session": "2026-07-17",
            "event_type_rank": 20,
            "intra_rank_sequence": 0,
            "event_id": "EVT_" + "a" * 64,
        },
    ]
    ordered = sorted(
        events,
        key=lambda row: (
            row["effective_timestamp"],
            row["session"],
            row["event_type_rank"],
            row["intra_rank_sequence"],
            row["event_id"],
        ),
    )
    persisted = [{**event, "semantic_sequence": index} for index, event in enumerate(ordered)]
    assert [event["event_type_rank"] for event in persisted] == [20, 40]
    assert [event["semantic_sequence"] for event in persisted] == [0, 1]
