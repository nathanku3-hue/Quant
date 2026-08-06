"""Source-derived common-object market packet authority."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

import gv_portfolio_v0.market_source_adapter as market_source_adapter

from gv_portfolio_v0.market_packet import (
    MARKET_PACKET_SCHEMA_VERSION,
    MarketPacketError,
    content_sha256_for_market_packet,
    normalize_immutable_market_packet,
)
from gv_portfolio_v0.market_source_adapter import (
    PAIR_SYMBOLS,
    load_source_derived_market_packets,
    load_verified_episode_contract,
    load_verified_pair_source,
    verified_pair_summary,
)
from gv_portfolio_v0.operated_scenarios import PAIR_DECISION_SERIES_SCENARIO_ID
from gv_portfolio_v0.prospective import build_prospective_workspace


def _utc(value: str, *, field: str = "ts") -> datetime:
    del field
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc
    )


ROOT = Path(__file__).resolve().parents[1]


def _packets() -> tuple[dict[str, object], list[dict[str, str]]]:
    workspace = build_prospective_workspace(PAIR_DECISION_SERIES_SCENARIO_ID)
    packets = load_source_derived_market_packets(workspace["instruments"])
    return workspace, packets


def _raw_episode_contract(episode_number: int) -> dict[str, object]:
    path = ROOT / (
        f"data/gv_pair_decision_series/mu_nvda_episode_{episode_number}/"
        "episode_preregistration.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _install_contract_registry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    contracts: dict[int, dict[str, object]],
) -> None:
    registry: dict[int, dict[str, object]] = {}
    for episode_number, contract in contracts.items():
        relative = Path(f"episode_{episode_number}.json")
        raw = (
            json.dumps(contract, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        (tmp_path / relative).write_bytes(raw)
        registry[episode_number] = {
            "episode_path": relative,
            "episode_preregistration_sha256": hashlib.sha256(raw).hexdigest(),
        }
    monkeypatch.setattr(market_source_adapter, "EPISODE_REGISTRY", registry)
    monkeypatch.setattr(market_source_adapter, "_repo_root", lambda: tmp_path)


def test_common_source_produces_two_instrument_bound_packets() -> None:
    workspace, packets = _packets()
    assert tuple(row["symbol"] for row in workspace["instruments"]) == PAIR_SYMBOLS
    assert len(packets) == 2
    assert {row["value"] for row in packets} == {"866.15", "219.77"}
    assert len({row["instrument_id"] for row in packets}) == 2
    assert len({row["permanent_instrument_identity"] for row in packets}) == 2
    assert len({row["row_locator"] for row in packets}) == 2
    assert len({row["row_sha256"] for row in packets}) == 2
    assert len({row["content_sha256"] for row in packets}) == 2


def test_packets_share_object_permission_parser_and_cut() -> None:
    _workspace, packets = _packets()
    shared_fields = (
        "schema_version",
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
    )
    for field in shared_fields:
        assert packets[0][field] == packets[1][field]
    assert packets[0]["schema_version"] == MARKET_PACKET_SCHEMA_VERSION


def test_packet_hash_round_trip_is_canonical() -> None:
    workspace, packets = _packets()
    latest = max(_utc(row["effective_at"]) for row in workspace["events"])
    observed = _utc("2026-08-06T09:05:00.000000Z")
    for instrument, packet in zip(workspace["instruments"], packets, strict=True):
        normalized = normalize_immutable_market_packet(
            packet,
            expected_instrument_id=instrument["instrument_id"],
            expected_permanent_key=instrument["permanent_key"],
            latest_time=latest,
            observed_time=observed,
            utc_datetime=_utc,
        )
        assert normalized == packet
        assert packet["content_sha256"] == content_sha256_for_market_packet(packet)


def test_declared_packet_hash_tamper_fails_closed() -> None:
    workspace, packets = _packets()
    tampered = deepcopy(packets[0])
    tampered["value"] = "1"
    with pytest.raises(MarketPacketError, match="SHA256_MISMATCH"):
        normalize_immutable_market_packet(
            tampered,
            expected_instrument_id=workspace["instruments"][0]["instrument_id"],
            expected_permanent_key=workspace["instruments"][0]["permanent_key"],
            latest_time=_utc("2026-08-06T08:00:00.000000Z"),
            observed_time=_utc("2026-08-06T09:05:00.000000Z"),
            utc_datetime=_utc,
        )


def test_manual_market_authority_fields_fail_closed() -> None:
    workspace, packets = _packets()
    manual = deepcopy(packets[0])
    manual["market_price"] = manual["value"]
    with pytest.raises(MarketPacketError, match="MANUAL_AUTHORITY_PROHIBITED"):
        normalize_immutable_market_packet(
            manual,
            expected_instrument_id=workspace["instruments"][0]["instrument_id"],
            expected_permanent_key=workspace["instruments"][0]["permanent_key"],
            latest_time=_utc("2026-08-06T08:00:00.000000Z"),
            observed_time=_utc("2026-08-06T09:05:00.000000Z"),
            utc_datetime=_utc,
        )


def test_unknown_packet_field_fails_closed() -> None:
    workspace, packets = _packets()
    extra = deepcopy(packets[0])
    extra["receipt_text"] = "operator supplied"
    with pytest.raises(MarketPacketError, match="FIELD_SET_INVALID"):
        normalize_immutable_market_packet(
            extra,
            expected_instrument_id=workspace["instruments"][0]["instrument_id"],
            expected_permanent_key=workspace["instruments"][0]["permanent_key"],
            latest_time=_utc("2026-08-06T08:00:00.000000Z"),
            observed_time=_utc("2026-08-06T09:05:00.000000Z"),
            utc_datetime=_utc,
        )


def test_instrument_and_permanent_identity_mismatch_fail_closed() -> None:
    workspace, packets = _packets()
    packet = packets[0]
    with pytest.raises(MarketPacketError, match="INSTRUMENT_MISMATCH"):
        normalize_immutable_market_packet(
            packet,
            expected_instrument_id="INS_WRONG",
            expected_permanent_key=workspace["instruments"][0]["permanent_key"],
            latest_time=_utc("2026-08-06T08:00:00.000000Z"),
            observed_time=_utc("2026-08-06T09:05:00.000000Z"),
            utc_datetime=_utc,
        )
    with pytest.raises(MarketPacketError, match="PERMANENT_IDENTITY_MISMATCH"):
        normalize_immutable_market_packet(
            packet,
            expected_instrument_id=workspace["instruments"][0]["instrument_id"],
            expected_permanent_key="SEC_CIK:WRONG",
            latest_time=_utc("2026-08-06T08:00:00.000000Z"),
            observed_time=_utc("2026-08-06T09:05:00.000000Z"),
            utc_datetime=_utc,
        )


def test_temporal_invalidity_fails_closed() -> None:
    workspace, packets = _packets()
    packet = packets[0]
    with pytest.raises(MarketPacketError, match="VALID_NOT_AFTER_AUTHORITY"):
        normalize_immutable_market_packet(
            packet,
            expected_instrument_id=workspace["instruments"][0]["instrument_id"],
            expected_permanent_key=workspace["instruments"][0]["permanent_key"],
            latest_time=_utc("2026-08-06T08:55:50.000000Z"),
            observed_time=_utc("2026-08-06T09:05:00.000000Z"),
            utc_datetime=_utc,
        )
    with pytest.raises(MarketPacketError, match="KNOWLEDGE_AFTER_DECISION"):
        normalize_immutable_market_packet(
            packet,
            expected_instrument_id=workspace["instruments"][0]["instrument_id"],
            expected_permanent_key=workspace["instruments"][0]["permanent_key"],
            latest_time=_utc("2026-08-06T08:00:00.000000Z"),
            observed_time=_utc("2026-08-06T09:00:00.000000Z"),
            utc_datetime=_utc,
        )


def test_verified_source_binds_permission_and_banked_subject_evidence() -> None:
    source = load_verified_pair_source()
    assert tuple(row["symbol"] for row in source["rows"]) == PAIR_SYMBOLS
    assert source["permission"]["authorized_symbols"] == list(PAIR_SYMBOLS)
    assert source["permission"]["authorized_fields"] == ["last"]
    assert source["subjects"]["MU"]["portfolio_action"] == "NO_POSITION"
    assert source["subjects"]["MU"]["portfolio_mutation_authorized"] is False
    assert source["subjects"]["NVDA"]["outcome"] == "ABSTAIN"
    assert source["subjects"]["NVDA"]["portfolio_action"] == "NO_POSITION"


def test_episode_preregistration_keeps_outcomes_closed() -> None:
    contract = load_verified_episode_contract(1)
    summary = verified_pair_summary(1)
    assert contract["decision_series_id"] == "PAIR_DECISION_SERIES_1"
    assert contract["episode_number"] == 1
    assert contract["outcome_status"] == "SEALED_NOT_OPENED"
    assert contract["outcome_data_loaded"] is False
    assert contract["source_contract_version"] == summary["source_contract_version"]
    assert contract["decision_cut_id"] == summary["decision_cut_id"]
    assert len(contract["episode_preregistration_sha256"]) == 64


def test_episode_two_is_later_distinct_cut_under_series_invariants() -> None:
    first = load_verified_episode_contract(1)
    second = load_verified_episode_contract(2)
    first_source = load_verified_pair_source(1)
    second_source = load_verified_pair_source(2)
    assert second["episode_number"] == 2
    assert second["decision_cut_id"] != first["decision_cut_id"]
    assert second["decision_cut_knowledge_at"] > first["decision_cut_knowledge_at"]
    assert second["decision_cut_knowledge_at"] == second_source["capture"][
        "retrieval_knowledge_at"
    ]
    assert second["comparator_spec"] == first["comparator_spec"]
    assert second["cost_model_id"] == first["cost_model_id"]
    assert second["decision_policy_version"] == first["decision_policy_version"]
    assert second["source_contract_version"] == first["source_contract_version"]
    assert second["outcome_horizon_spec"] == first["outcome_horizon_spec"]
    assert second["outcome_status"] == "SEALED_NOT_OPENED"
    assert second["outcome_data_loaded"] is False
    assert second_source["capture"]["full_response_sha256"] != first_source["capture"][
        "full_response_sha256"
    ]
    assert {row["value"] for row in second_source["rows"]} == {"852.19", "221.71"}


def test_decision_time_is_strictly_after_exact_minute_knowledge_cut() -> None:
    assert market_source_adapter.decision_observed_at_for_knowledge(
        "2026-08-06T12:00:00.000000Z"
    ) == "2026-08-06T12:01:00.000000Z"


def test_episode_three_must_follow_immediately_prior_knowledge_cut(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _raw_episode_contract(1)
    second = _raw_episode_contract(2)
    third = deepcopy(second)
    third["episode_number"] = 3
    third["decision_cut_id"] = "CUT_" + ("3" * 64)
    third["decision_cut_knowledge_at"] = "2026-08-06T10:00:00.000000Z"
    third["outcome_open_not_before"] = "2026-09-05T10:00:00.000000Z"
    _install_contract_registry(
        monkeypatch,
        tmp_path,
        {1: first, 2: second, 3: third},
    )
    with pytest.raises(
        market_source_adapter.MarketSourceAdapterError,
        match="PAIR_EPISODE_NOT_AFTER_PRIOR_CUT",
    ):
        market_source_adapter.load_verified_episode_contract(3)


def test_outcome_open_date_must_follow_preregistered_horizon_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _raw_episode_contract(1)
    first["outcome_open_not_before"] = "2026-09-05T09:04:15.959920Z"
    _install_contract_registry(monkeypatch, tmp_path, {1: first})
    with pytest.raises(
        market_source_adapter.MarketSourceAdapterError,
        match="PAIR_EPISODE_OUTCOME_OPEN_RULE_INVALID",
    ):
        market_source_adapter.load_verified_episode_contract(1)
