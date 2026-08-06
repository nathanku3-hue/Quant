"""Adversarial source, pair, and episode-1 certification acceptance."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.market_packet import content_sha256_for_market_packet
from gv_portfolio_v0.market_source_adapter import (
    load_source_derived_market_packets,
    load_verified_episode_contract,
    load_verified_pair_source,
)
from gv_portfolio_v0.operated_scenarios import PAIR_DECISION_SERIES_SCENARIO_ID
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    build_pair_episode_request,
    preview_runtime_observation,
)


def _workspace(tmp_path: Path) -> dict[str, object]:
    return ensure_prospective_workspace(
        root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )


def _request(workspace: dict[str, object]) -> dict[str, object]:
    return build_pair_episode_request(
        workspace,
        operator_rationale=(
            "Both real subjects remain below the banked-evidence capital threshold; "
            "retain certified cash and seal the forward episode."
        ),
    )


def _rehash(packet: dict[str, str]) -> None:
    packet["content_sha256"] = content_sha256_for_market_packet(packet)


def test_acceptance_path_contains_no_synthetic_merid_or_companion() -> None:
    scenario_source = Path("gv_portfolio_v0/operated_scenarios.py").read_text(
        encoding="utf-8"
    )
    prospective_source = Path("gv_portfolio_v0/prospective.py").read_text(
        encoding="utf-8"
    )
    command_center_source = Path("views/command_center.py").read_text(
        encoding="utf-8"
    )
    scenario = __import__(
        "gv_portfolio_v0.operated_scenarios", fromlist=["get_scenario"]
    ).get_scenario(PAIR_DECISION_SERIES_SCENARIO_ID)
    assert [row["symbol"] for row in scenario["instruments"]] == ["MU", "NVDA"]
    for source in (prospective_source, command_center_source):
        assert "operated_rotation_companion" not in source
        assert '"MERID"' not in source
    assert "SELL+BUY rotation" not in command_center_source


def test_command_center_contains_no_manual_market_authority_controls() -> None:
    source = Path("views/command_center.py").read_text(encoding="utf-8")
    forbidden = (
        "gv_command_center_market_price",
        "gv_command_center_market_observed_at",
        "gv_command_center_market_knowledge_at",
        "gv_command_center_market_source_identity",
        "gv_command_center_market_receipt",
        "Market packet value",
        "Market raw bytes or receipt",
        "owner-local/permission/manual-v1",
    )
    for value in forbidden:
        assert value not in source
    assert "build_pair_episode_request" in source
    assert "source_derived_market_packets" in source


def test_market_source_adapter_has_no_network_or_provider_framework_authority() -> None:
    path = Path("gv_portfolio_v0/market_source_adapter.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert imported.isdisjoint(
        {"requests", "urllib", "httpx", "aiohttp", "yfinance", "socket"}
    )
    assert "Invoke-WebRequest" not in source
    assert "http_get" not in source
    assert "data.providers" not in source


def test_parser_permission_and_row_substitution_fail_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    mutators = (
        ("parser_identity", "UNAUTHORIZED_PARSER"),
        ("parser_version", "999"),
        ("permission_manifest_sha256", "0" * 64),
        ("row_locator", "/wrong/row"),
        ("row_sha256", "1" * 64),
    )
    for field, value in mutators:
        request = _request(workspace)
        packet = request["source_derived_market_packets"][0]
        packet[field] = value
        _rehash(packet)
        with pytest.raises(ProspectiveOperationError, match="NOT_SOURCE_DERIVED"):
            preview_runtime_observation(workspace, request)


def test_packet_instrument_swap_and_duplicate_fail_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    first, second = request["source_derived_market_packets"]
    first["instrument_id"], second["instrument_id"] = (
        second["instrument_id"],
        first["instrument_id"],
    )
    _rehash(first)
    _rehash(second)
    with pytest.raises(ProspectiveOperationError, match="PERMANENT_IDENTITY_MISMATCH"):
        preview_runtime_observation(workspace, request)

    request = _request(workspace)
    request["source_derived_market_packets"][1] = deepcopy(
        request["source_derived_market_packets"][0]
    )
    with pytest.raises(ProspectiveOperationError, match="INSTRUMENT_DUPLICATE"):
        preview_runtime_observation(workspace, request)


def test_common_cut_time_drift_fails_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    packet = request["source_derived_market_packets"][0]
    packet["retrieval_knowledge_at"] = "2026-08-06T09:06:00.000000Z"
    _rehash(packet)
    with pytest.raises(ProspectiveOperationError, match="KNOWLEDGE_AFTER_DECISION"):
        preview_runtime_observation(workspace, request)

    request = _request(workspace)
    packet = request["source_derived_market_packets"][1]
    packet["valid_effective_at"] = "2026-08-02T12:06:00.000000Z"
    _rehash(packet)
    with pytest.raises(ProspectiveOperationError, match="VALID_NOT_AFTER_AUTHORITY"):
        preview_runtime_observation(workspace, request)


def test_one_source_permission_parser_and_cut_bind_two_unique_packets(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    packets = load_source_derived_market_packets(workspace["instruments"])
    contract = load_verified_episode_contract()
    source = load_verified_pair_source()
    assert len(packets) == 2
    for field in (
        "source_contract_version",
        "source_object_identity",
        "source_object_sha256",
        "permission_manifest_identity",
        "permission_manifest_sha256",
        "parser_identity",
        "parser_version",
        "decision_cut_id",
        "valid_effective_at",
        "retrieval_knowledge_at",
    ):
        assert packets[0][field] == packets[1][field]
    assert packets[0]["decision_cut_id"] == contract["decision_cut_id"]
    assert packets[0]["source_object_sha256"] == source["capture_sha256"]
    assert packets[0]["permission_manifest_sha256"] == source["permission_sha256"]
    assert packets[0]["row_locator"] != packets[1]["row_locator"]
    assert packets[0]["row_sha256"] != packets[1]["row_sha256"]
    assert packets[0]["content_sha256"] != packets[1]["content_sha256"]


def test_confirmed_event_and_certification_bind_series_and_packets(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    proposal = preview_runtime_observation(workspace, request)
    tampered = deepcopy(proposal)
    tampered["changed_why"]["reason"] = "Mutated after preview."
    with pytest.raises(ProspectiveOperationError, match="STALE_OR_MUTATED_PROPOSAL"):
        confirm_prospective_observation_and_persist(
            tampered, root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
        )
    confirmed = confirm_prospective_observation_and_persist(
        proposal, root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    episode_events = [
        row for row in confirmed["events"] if row["event_type"] == "LATER_OBSERVATION_ADMITTED"
    ]
    assert len(episode_events) == 1
    stored = episode_events[0]["payload"]["prospective_proposal"]
    assert stored["request"]["decision_series_contract"]["episode_number"] == 1
    assert stored["request"]["decision_series_contract"]["outcome_data_loaded"] is False
    assert len(stored["request"]["source_derived_market_packets"]) == 2
    assert canonical_document_bytes(stored) == canonical_document_bytes(proposal)
    assert confirmed["certification"]["subject_event_ledger_hash"] != workspace[
        "certification"
    ]["subject_event_ledger_hash"]
