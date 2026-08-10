from __future__ import annotations

import pandas as pd
import pytest

from research.prebreakout_discovery_v1.failure_packet_v1 import (
    FailurePacketError,
    _false_winner_diagnostics,
    _observability_map,
    _smoke_diagnostics,
)


def test_smoke_diagnostic_supersedes_only_smoke_truth() -> None:
    diagnostic = _smoke_diagnostics(
        {
            "checked_development_smoke_episode_count": 19,
            "deferred_postdevelopment_smoke_episode_count": 4,
            "failure_count": 16,
            "all_checked_pass": False,
        }
    )

    assert diagnostic["sealed_trial1_atlas_statistical_close_affected"] is False
    assert diagnostic["sealed_trial1_atlas_mu_sndk_smoke_is_acceptance_truth"] is False
    assert diagnostic["independent_checker"]["legitimate_pre_b_flag_episode_count"] == 3
    assert diagnostic["independent_checker"]["no_legitimate_pre_b_flag_episode_count"] == 16


def test_smoke_diagnostic_fails_closed_on_expected_custody_drift() -> None:
    with pytest.raises(FailurePacketError, match="smoke_checker_drift"):
        _smoke_diagnostics(
            {
                "checked_development_smoke_episode_count": 18,
                "deferred_postdevelopment_smoke_episode_count": 4,
                "failure_count": 15,
            }
        )


def test_false_winner_persistence_is_diagnostic_only_aggregation() -> None:
    frame = pd.DataFrame(
        [
            {"security_id": "CIQSEC:IQ1", "trading_item_id": "1", "decision_session_ordinal": 1, "statistical_weight": 1},
            {"security_id": "CIQSEC:IQ1", "trading_item_id": "1", "decision_session_ordinal": 2, "statistical_weight": 1},
            {"security_id": "CIQSEC:IQ1", "trading_item_id": "1", "decision_session_ordinal": 4, "statistical_weight": 1},
            {"security_id": "CIQSEC:IQ2", "trading_item_id": "2", "decision_session_ordinal": 2, "statistical_weight": 1},
            {"security_id": "CIQSEC:IQ2", "trading_item_id": "2", "decision_session_ordinal": 3, "statistical_weight": 0},
        ]
    )

    diagnostic = _false_winner_diagnostics(frame)

    assert diagnostic["false_winner_decision_row_count"] == 4
    assert diagnostic["unique_false_winner_identity_count"] == 2
    assert diagnostic["max_consecutive_false_winner_sessions"] == 2
    assert diagnostic["false_winner_days_per_identity_max"] == 3


def test_observability_map_is_demand_only_and_keeps_market_downstream() -> None:
    node_ids = [
        "SUPPLY_CAPACITY_STATE",
        "INVENTORY_CHANNEL_STATE",
        "DEMAND_ORDER_STATE",
        "PRICING_MIX_STATE",
        "UTILIZATION_COST_STATE",
        "MARGIN_CASH_STATE",
        "REVISION_GUIDANCE_STATE",
        "EXPECTATION_GAP_STATE",
        "MARKET_CONFIRMATION_STATE",
    ]
    manifest = {
        "schema_version": "econphysics_prebreakout_pit_observable_manifest_v1",
        "family_id": "ECONPHYSICS_PREBREAKOUT_v1",
        "capture_authority": "NONE",
        "w6_authority": "HOLD_UNTOUCHED",
        "nodes": [
            {
                "node_id": node_id,
                "structured_observables": [],
                "source_claim_topics": [],
                "expectation_measures": [],
            }
            for node_id in node_ids
        ],
    }

    diagnostic = _observability_map(manifest)
    by_node = {row["node_id"]: row for row in diagnostic["nodes"]}

    assert diagnostic["capture_authority"] == "NONE"
    assert diagnostic["map_role"] == "DATA_GAP_AND_OBSERVABILITY_DEMAND_ONLY"
    assert by_node["SUPPLY_CAPACITY_STATE"]["blocking"] is True
    assert by_node["INVENTORY_CHANNEL_STATE"]["blocking"] is True
    assert by_node["DEMAND_ORDER_STATE"]["blocking"] is True
    assert by_node["PRICING_MIX_STATE"]["status"] == "UNOBSERVED"
    assert by_node["EXPECTATION_GAP_STATE"]["blocking"] is True
    assert by_node["MARKET_CONFIRMATION_STATE"]["status"] == "EXISTING_PIT_AUTHORITY_DOWNSTREAM_ONLY"
    assert by_node["MARKET_CONFIRMATION_STATE"]["blocking"] is False
