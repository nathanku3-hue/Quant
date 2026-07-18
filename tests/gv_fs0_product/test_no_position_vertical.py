from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from core.gv_fs0_book import (
    GvFs0BookError,
    _build_economic_events,
    build_no_position_book,
    validate_schema,
)
from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from core.gv_fs0_certify import (
    GvFs0CertificationError,
    build_no_position_certified_result,
    run_isolated_verifier,
)
from views.gv_fs0_portfolio_adapter import render_gv_fs0_portfolio

ROOT = Path(__file__).resolve().parents[2]
PERMANENT_BUNDLE = ROOT / "data" / "gv_fs0" / "gv_fs0_certified_bundle.json"


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def subheader(self, body: str) -> None:
        self.calls.append(("subheader", body))

    def table(self, data: Any) -> None:
        self.calls.append(("table", data))

    def caption(self, body: str) -> None:
        self.calls.append(("caption", body))


def _non_valuation_intent() -> dict[str, Any]:
    return {
        "schema_version": "gv_fs0_source_intent_v1",
        "source_intent_id": "EXECUTION_INTENT:99",
        "source_sequence": 99,
        "intent_type": "EXECUTION_INTENT",
        "effective_timestamp": "2026-07-14T14:30:00.000000Z",
        "session": "2026-07-14",
        "security_id": "SEC_1",
        "quantity": 1,
        "execution_price": "10",
        "fee": None,
        "dividend_amount_per_share": None,
        "referenced_entitlement_source_intent_id": None,
        "valuation_timestamp": None,
    }


def test_no_position_book_uses_zero_execution_intents_and_flat_economics() -> None:
    build = build_no_position_book()

    assert build.decision.action == "NO_POSITION"
    assert build.decision.authority_tier == "MANUAL_OWNER_PAPER"
    assert build.decision.requested_quantity is None
    assert {intent["intent_type"] for intent in build.source_fixture["source_intents"]} == {
        "VALUATION_INSTRUCTION"
    }
    assert [event["event_type"] for event in build.book.events] == [
        "DECISION_ACCEPTED",
        "SESSION_VALUATION",
        "SESSION_VALUATION",
        "SESSION_VALUATION",
        "SESSION_VALUATION",
        "SESSION_VALUATION",
    ]
    assert [event["semantic_sequence"] for event in build.book.events] == list(range(6))
    assert len({event["event_id"] for event in build.book.events}) == 6

    assert [
        {
            "session": row["session"],
            "shares": row["shares"],
            "cash": row["cash"],
            "receivables": row["receivables"],
            "market_value": row["market_value"],
            "nav": row["nav"],
            "session_contribution": row["session_contribution"],
            "cumulative_contribution": row["cumulative_contribution"],
        }
        for row in build.book.snapshots
    ] == [
        {
            "session": session,
            "shares": 0,
            "cash": "1000",
            "receivables": "0",
            "market_value": "0",
            "nav": "1000",
            "session_contribution": "0",
            "cumulative_contribution": "0",
        }
        for session in build.source_fixture["sessions"]
    ]
    assert build.book.economic_payload_hash == domain_hash(
        "GV-FS0:ECONOMIC_PAYLOAD:V1", build.book.economic_payload
    )


def test_no_position_verifier_input_contains_only_original_projected_inputs() -> None:
    verifier_input = build_no_position_book().verifier_input
    assert set(verifier_input) == {
        "schema_version",
        "protocol",
        "decision",
        "source_prices",
        "source_intents",
    }
    assert verifier_input["decision"]["action"] == "NO_POSITION"
    assert verifier_input["decision"]["requested_sizing"] == {"quantity": None}
    assert all(
        intent["intent_type"] == "VALUATION_INSTRUCTION"
        for intent in verifier_input["source_intents"]
    )
    encoded = canonical_document_bytes(verifier_input)
    for prohibited in (
        b'"events"',
        b'"book_id"',
        b'"snapshot_id"',
        b'"certification_id"',
        b'"bundle_id"',
    ):
        assert prohibited not in encoded


def test_no_position_primary_book_rejects_non_valuation_intent() -> None:
    build = build_no_position_book()
    fixture = copy.deepcopy(build.source_fixture)
    fixture["source_intents"].append(_non_valuation_intent())
    with pytest.raises(
        GvFs0BookError, match="NO_POSITION_NON_VALUATION_INTENT_PROHIBITED"
    ):
        _build_economic_events(fixture, build.decision, build.book.book_id)


def test_no_position_verifier_rejects_non_valuation_intent() -> None:
    verifier_input = copy.deepcopy(build_no_position_book().verifier_input)
    verifier_input["source_intents"].append(_non_valuation_intent())
    with pytest.raises(GvFs0CertificationError, match="VERIFIER_PROCESS_FAILED"):
        run_isolated_verifier(verifier_input)


def test_no_position_certification_runs_exactly_two_attempts_and_certifies() -> None:
    calls = 0

    def counted_runner(verifier_input: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return run_isolated_verifier(verifier_input)

    result = build_no_position_certified_result(counted_runner)
    assert calls == 2
    assert result["role"] == "NO_POSITION"
    assert result["decision"]["requested_quantity_or_sizing_input"] == {
        "quantity": None
    }
    assert result["certification"]["certification_status"] == "CERTIFIED"
    assert set(result["certification"]["checks"].values()) == {"TRUE"}
    assert [attempt["ordinal"] for attempt in result["verifier_attempts"]] == [1, 2]
    assert len(result["retained_verifier_results"]) == 1
    assert result["events"][-1]["event_type"] == "CERTIFICATION_REFERENCE"
    assert result["events"][-1]["semantic_sequence"] == 6
    assert result["snapshots"][-1]["nav"] == "1000"
    assert result["economic_payload_hash"] == result["certification"][
        "primary_economic_payload_hash"
    ]
    validate_schema(result, "gv_fs0_certified_decision_result_v1.schema.json")


def test_no_position_complete_runs_are_byte_identical() -> None:
    first = build_no_position_certified_result()
    second = build_no_position_certified_result()
    assert canonical_document_bytes(first) == canonical_document_bytes(second)
    assert first["certified_decision_result_hash"] == second[
        "certified_decision_result_hash"
    ]
    assert first["presentation"]["presentation_hash"] == second["presentation"][
        "presentation_hash"
    ]


def test_no_position_verifier_semantic_tampering_blocks_certification() -> None:
    def tampered_runner(verifier_input: dict[str, Any]) -> dict[str, Any]:
        changed = copy.deepcopy(run_isolated_verifier(verifier_input))
        changed["economic_payload"]["action"] = "OPEN"
        changed["canonical_payload_hash"] = domain_hash(
            "GV-FS0:ECONOMIC_PAYLOAD:V1", changed["economic_payload"]
        )
        without_hash = {
            key: value for key, value in changed.items() if key != "verifier_result_hash"
        }
        changed["verifier_result_hash"] = domain_hash(
            "GV-FS0:VERIFIER_RESULT:V1", without_hash
        )
        return changed

    with pytest.raises(GvFs0CertificationError, match="CERTIFICATION_BLOCKED"):
        build_no_position_certified_result(tampered_runner)


def test_final_adapter_renders_injected_no_position_through_same_path() -> None:
    result = build_no_position_certified_result()
    renderer = FakeRenderer()
    model = render_gv_fs0_portfolio(
        renderer,
        presentation=result["presentation"],
        terminal_snapshot=result["snapshots"][-1],
        certification=result["certification"],
    )
    assert model["status"] == "CERTIFIED"
    assert model["title"].endswith("NO_POSITION")
    row_map = {row["label"]: row["value"] for row in model["rows"]}
    assert row_map["Action"] == "NO_POSITION"
    assert row_map["Shares"] == "0"
    assert row_map["Cash"] == "1000"
    assert row_map["NAV"] == "1000"
    assert row_map["CertificationStatus"] == "CERTIFIED"
    assert [name for name, _ in renderer.calls] == ["subheader", "table", "caption"]


def test_f1b_never_publishes_permanent_bundle() -> None:
    before = PERMANENT_BUNDLE.read_bytes() if PERMANENT_BUNDLE.exists() else None
    build_no_position_certified_result()
    after = PERMANENT_BUNDLE.read_bytes() if PERMANENT_BUNDLE.exists() else None
    assert after == before
    assert before is None
