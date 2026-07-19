from __future__ import annotations

import json
from pathlib import Path

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts/gv_fs0/v1/schemas"
VECTORS = ROOT / "contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json"
CONTRACT = ROOT / "docs/architecture/gv_fs0_certification_and_data_authority_contract.md"


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_verifier_projection_contains_only_declared_original_inputs() -> None:
    schema = _schema("gv_fs0_verifier_input_v1.schema.json")
    assert set(schema["properties"]) == {
        "schema_version",
        "protocol",
        "decision",
        "source_prices",
        "source_intents",
    }
    assert set(schema["properties"]["protocol"]["properties"]) == {
        "protocol_id",
        "fixture_id",
        "fixture_hash",
        "currency",
        "initial_cash",
    }
    assert set(schema["properties"]["decision"]["properties"]) == {
        "decision_id",
        "decision_hash",
        "authority",
        "action",
        "decision_timestamp",
        "effective_timestamp",
        "security_id",
        "requested_sizing",
        "rationale_reference",
    }


def test_governance_and_primary_derived_fields_are_omitted() -> None:
    schema_text = (SCHEMAS / "gv_fs0_verifier_input_v1.schema.json").read_text(encoding="utf-8")
    for prohibited in [
        "operator_id",
        "supersedes_decision_id",
        "book_id",
        "event_id",
        "snapshot_id",
        "certification_id",
        "semantic_sequence",
        "nav",
        "contribution",
        "bundle_id",
    ]:
        assert f'"{prohibited}"' not in schema_text


def test_source_price_projection_is_exact_and_freshness_fields_are_visible() -> None:
    price = _schema("gv_fs0_verifier_input_v1.schema.json")["properties"]["source_prices"]["items"]
    assert set(price["properties"]) == {
        "security_id",
        "session",
        "price_timestamp",
        "close_price",
        "source_sequence",
    }
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "max_session_lag = 0" in contract
    assert "price_timestamp <= valuation_timestamp" in contract
    assert "Cross-session carry-forward is prohibited" in contract


def test_no_position_zero_execution_intents_is_normative_and_hashable() -> None:
    vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
    vector = next(item for item in vectors["accepted"] if item["vector_id"] == "no_position_projection")
    assert vector["semantic_value"] == {"action": "NO_POSITION", "source_intents": []}
    assert canonical_document_bytes(vector["semantic_value"]).hex() == vector["canonical_document_hex"]
    assert domain_hash(vector["domain_prefix"], vector["semantic_value"]) == vector["sha256"]
    assert "Zero execution intents are valid and normative for NO_POSITION" in CONTRACT.read_text(encoding="utf-8")


def test_decision_projection_renames_without_changing_values() -> None:
    decision = {
        "decision_id": "DECISION_OPEN_1",
        "decision_hash": "a" * 64,
        "authority": "MANUAL_OWNER_PAPER",
        "action": "OPEN",
        "decision_timestamp": "2026-07-17T00:00:00.000000Z",
        "effective_timestamp": "2026-07-18T00:00:00.000000Z",
        "security_id": "SEC_1",
        "requested_sizing": {"quantity": 10},
        "rationale_reference": "RATIONALE:OPEN_1",
    }
    encoded = canonical_document_bytes(decision)
    assert b'"authority":"MANUAL_OWNER_PAPER"' in encoded
    assert b'"requested_sizing":{"quantity":10}' in encoded
    assert b'"rationale_reference":"RATIONALE:OPEN_1"' in encoded


def test_verifier_result_conditional_payload_contract_is_explicit() -> None:
    schema = _schema("gv_fs0_verifier_result_v1.schema.json")
    statuses = schema["properties"]["verifier_status"]["enum"]
    assert statuses == ["RECONSTRUCTED", "REJECTED"]
    reconstructed = schema["allOf"][0]["then"]["properties"]
    rejected = schema["allOf"][1]["then"]["properties"]
    assert reconstructed["failure_codes"]["maxItems"] == 0
    assert reconstructed["reconstructed_economic_payload_hash"]["type"] == "string"
    assert rejected["failure_codes"]["minItems"] == 1
    assert rejected["reconstructed_economic_payload"] == {"type": "null"}
