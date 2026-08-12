"""Frozen no-network acquisition request for ETF-first sector rotation W8.

This module describes the exact provider objects that must be acquired when W8
is later reopened on truly independent provider capacity. It performs no
network/provider access. The capture hold is binding in this build slice.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.sector_rotation_alpha_v1.contracts import (
    EXPECTED_SECTOR_KEYS,
    FAMILY_ID,
    IMPLEMENTATION_ID,
    MIN_HISTORY_SESSIONS,
    PRIMARY_HORIZON_SESSIONS,
    RISK_SET_SPEC_ID,
    SEARCH_FAMILY_ID,
    SECONDARY_HORIZON_SESSIONS,
    TRIAL_BUDGET_MAX,
)
from research.sector_rotation_alpha_v1.source import BENCHMARK_FAMILY_ID


ACQUISITION_REQUEST_SCHEMA = "sra_etf_source_acquisition_request_v1"
ACQUISITION_REQUEST_ID = "SRA_ETF_11_CIQ_ACQUISITION_V1"
PROVIDER = "S&P Capital IQ Pro"
CAPTURE_STATE = "PARKED_CAPTURE_HOLD"
REOPEN_CONDITION = "TRULY_INDEPENDENT_PROVIDER_CAPACITY_AVAILABLE"
IDENTITY_PROVIDER_FIELDS = ("SP_CIQ_ID", "SP_TRADING_ITEM_ID")
MARKET_PROVIDER_FIELDS = ("SP_TOTAL_RETURN", "SP_PRICE_CLOSE", "SP_VOLUME")


def build_frozen_acquisition_request() -> dict[str, Any]:
    """Return the exact parked W8 source-acquisition request.

    Exact CIQ security/trading-item values are deliberately not guessed in this
    packet. They must be returned by and hash-bound to the source-authorized
    benchmark-membership receipt for each sector key before market history can
    be admitted. Unresolved identity is a blocking state, never a ticker/entity
    fallback.
    """

    sector_requests = [
        {
            "sector_key": sector_key,
            "benchmark_family_id": BENCHMARK_FAMILY_ID,
            "instrument_type": "ETF",
            "listing_country": "US",
            "primary_listing_required": True,
            "exact_security_id_required": True,
            "exact_trading_item_id_required": True,
            "identity_provider_fields": list(IDENTITY_PROVIDER_FIELDS),
            "benchmark_membership_receipt_required": True,
            "unresolved_identity_action": "BLOCK",
        }
        for sector_key in EXPECTED_SECTOR_KEYS
    ]
    body = {
        "schema_version": ACQUISITION_REQUEST_SCHEMA,
        "request_id": ACQUISITION_REQUEST_ID,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "trial_budget_max": TRIAL_BUDGET_MAX,
        "primary_horizon_sessions": PRIMARY_HORIZON_SESSIONS,
        "secondary_horizon_sessions": SECONDARY_HORIZON_SESSIONS,
        "provider": PROVIDER,
        "capture_state": CAPTURE_STATE,
        "provider_acquisition_allowed": False,
        "reopen_condition": REOPEN_CONDITION,
        "independent_capacity_must_not_delay_stock_path": True,
        "benchmark_family_id": BENCHMARK_FAMILY_ID,
        "sector_count": len(EXPECTED_SECTOR_KEYS),
        "sector_requests": sector_requests,
        "market_history_request": {
            "provider_fields": list(MARKET_PROVIDER_FIELDS),
            "minimum_observed_sessions_per_security": MIN_HISTORY_SESSIONS,
            "decision_session_included": True,
            "future_sessions_forbidden": True,
            "total_return_is_corporate_action_authority": True,
            "close_required": True,
            "volume_required": True,
            "source_receipt_sha256_required": True,
            "availability_timestamp_required": True,
        },
        "identity_and_membership_law": {
            "identity_authority": "CIQSEC_PLUS_TRADING_ITEM_FROM_SOURCE_BOUND_MEMBERSHIP_RECEIPT",
            "sector_key_membership_receipt_required": True,
            "ticker_identity_fallback": False,
            "entity_identity_fallback": False,
            "permno_identity_fallback": False,
            "alternate_listing_backfill": False,
            "current_survivor_back_projection": False,
        },
        "forbidden_inputs_or_methods": {
            "old_sector_map": False,
            "stock_breadth": False,
            "underlying_stock_membership": False,
            "etf_flow_vendor": False,
            "machine_learning": False,
            "optimizer": False,
        },
        "frozen_model_summary": {
            "relative_strength_windows": [20, 60],
            "dollar_volume_participation_windows": [5, 20],
            "material_trials": 1,
            "comparator": "I_RELATIVE_STRENGTH_ONLY_VS_I_PLUS_X_DVP_PRE_LABEL",
            "retune_allowed": False,
        },
        "provider_acquisition_performed": False,
        "prediction_append_performed": False,
        "outcome_accessed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return {**body, "request_sha256": _request_hash(body)}


def verify_frozen_acquisition_request(request: Mapping[str, Any]) -> None:
    if not isinstance(request, Mapping):
        raise ValueError("sra_acquisition_request_mapping_required")
    expected = build_frozen_acquisition_request()
    if canonical_value(request) != canonical_value(expected):
        raise ValueError("sra_acquisition_request_not_exact_frozen_v1")
    if request.get("provider_acquisition_allowed") is not False:
        raise ValueError("sra_capture_hold_must_remain_active")
    if request.get("capture_state") != CAPTURE_STATE:
        raise ValueError("sra_capture_state_invalid")


def require_capture_reopen(*, independent_provider_capacity_available: bool) -> None:
    """Fail closed while this W8 build-slice capture hold remains active."""

    if not independent_provider_capacity_available:
        raise RuntimeError("sra_independent_provider_capacity_required")
    raise RuntimeError("sra_capture_hold_active_reopen_requires_new_explicit_authority")


def _request_hash(body: Mapping[str, Any]) -> str:
    return domain_hash("SECTOR_ROTATION_ALPHA_V1:ACQUISITION_REQUEST", canonical_value(body))
