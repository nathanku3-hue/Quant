"""Frozen contracts for VOL_SQUEEZE_BREAKOUT_v1 M0."""

from __future__ import annotations

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT,
    VOL_SQUEEZE_BREAKOUT_FAMILY_ID,
    VOL_SQUEEZE_BREAKOUT_PRIMARY_LABEL_SPEC_ID,
    VOL_SQUEEZE_BREAKOUT_RISK_SET_SPEC_ID,
)


FAMILY_ID = VOL_SQUEEZE_BREAKOUT_FAMILY_ID
RISK_SET_SPEC_ID = VOL_SQUEEZE_BREAKOUT_RISK_SET_SPEC_ID
PRIMARY_LABEL_SPEC_ID = VOL_SQUEEZE_BREAKOUT_PRIMARY_LABEL_SPEC_ID
SECONDARY_LABEL_SPEC_ID = "VSB_RIGHT_TAIL_20D_TOP5_V1"

REQUESTED_OBSERVATION_FIELDS = (
    "market.close",
    "market.total_return_1d",
    "market.volume",
)

MARKET_HISTORY_ARTIFACT_TYPE = "VSB_MARKET_HISTORY"
MARKET_HISTORY_SCHEMA = "vsb_market_history_payload_v1"
INPUT_PACKET_SCHEMA = "vsb_input_packet_v1"
FEATURE_PACKET_SCHEMA = "vsb_m0_feature_packet_v1"
MODEL_OUTPUT_SCHEMA = "vsb_m0_model_output_v1"
PREDICTION_BATCH_SCHEMA = "vsb_m0_prediction_batch_v1"
PREDICTION_SCHEMA = PREDICTION_BATCH_SCHEMA
MATURED_DATE_RECORD_SCHEMA = "vsb_confirmation_matured_10d_date_v1"
CONFIRMATION_RESULT_SCHEMA = "vsb_confirmation_guardian_result_v1"

SEARCH_FAMILY_ID = "VSB_M0_SEARCH_v1"
IMPLEMENTATION_ID = "VSB_M0_EQUAL_RANK_20_60_20_v1"
PREDICTION_LEDGER_SCOPE = "VSB_V1_PREDICTION_LEDGER"
TRIAL_LEDGER_SCOPE = "VSB_V1_TRIAL_LEDGER"
ARTIFACT_NAMESPACE = "vol_squeeze_breakout_v1/"
TRIAL_BUDGET_MAX = 1

RV_SHORT_WINDOW = 20
RV_LONG_WINDOW = 60
BREAKOUT_WINDOW = 20
VOLUME_WINDOW = 20
MIN_HISTORY_SESSIONS = 60
PRIMARY_HORIZON_SESSIONS = 10
SECONDARY_HORIZON_SESSIONS = 20
WINNER_FRACTION = 0.05

CONFIRMATION_ROLE_ID = "VSB_CONFIRMATION_v1"
MIN_MATURED_PRIMARY_DECISION_DATES = 20
ACCEPTANCE_LIFT_THRESHOLD = 1.0
BOOTSTRAP_METHOD_ID = "NONCIRCULAR_MOVING_BLOCK_TRUNCATE_TYPE7_V1"
BOOTSTRAP_BLOCK_LENGTH = 10
BOOTSTRAP_REPLICATES = 10000
BOOTSTRAP_SEED = 20260810
BOOTSTRAP_CONFIDENCE = 0.80
BOOTSTRAP_LOWER_TAIL_PROBABILITY = 0.10
MATURITY_STATUS = "MATURED_PRIMARY_10D"
OUTCOME_AUTHORITY_CLASS = "UNTOUCHED_OR_PROSPECTIVE_MATURED_LABEL"

FAMILY_DATA_CONTRACT = VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT
FAMILY_DATA_CONTRACT_SHA256 = domain_hash(
    "ALPHA_PIT_V1:FAMILY_DATA_CONTRACT",
    FAMILY_DATA_CONTRACT.as_dict(),
)


def confirmation_guardian_contract() -> dict[str, object]:
    """Return the frozen W7 confirmation-only acceptance law."""

    return {
        "confirmation_role_id": CONFIRMATION_ROLE_ID,
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "primary_horizon_sessions": PRIMARY_HORIZON_SESSIONS,
        "winner_fraction": format(WINNER_FRACTION, ".17g"),
        "minimum_matured_primary_decision_dates": MIN_MATURED_PRIMARY_DECISION_DATES,
        "acceptance_lift_threshold": format(ACCEPTANCE_LIFT_THRESHOLD, ".17g"),
        "bootstrap_method_id": BOOTSTRAP_METHOD_ID,
        "bootstrap_block_length": BOOTSTRAP_BLOCK_LENGTH,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_confidence": format(BOOTSTRAP_CONFIDENCE, ".17g"),
        "bootstrap_lower_tail_probability": format(BOOTSTRAP_LOWER_TAIL_PROBABILITY, ".17g"),
        "maturity_status": MATURITY_STATUS,
        "outcome_authority_class": OUTCOME_AUTHORITY_CLASS,
        "retune_authority": "NONE",
        "prebreakout_authority": "NONE",
        "capital_authority": "NONE",
    }


GUARDIAN_CONTRACT_SHA256 = domain_hash(
    "VOL_SQUEEZE_BREAKOUT_V1:CONFIRMATION_GUARDIAN_CONTRACT",
    confirmation_guardian_contract(),
)


def validate_vsb_contract() -> None:
    if FAMILY_DATA_CONTRACT.family_id != FAMILY_ID:
        raise ValueError("vsb_family_contract_family_invalid")
    if FAMILY_DATA_CONTRACT.risk_set_spec_id != RISK_SET_SPEC_ID:
        raise ValueError("vsb_family_contract_risk_set_invalid")
    if FAMILY_DATA_CONTRACT.primary_label_spec_id != PRIMARY_LABEL_SPEC_ID:
        raise ValueError("vsb_family_contract_primary_label_invalid")
    if FAMILY_DATA_CONTRACT.allowed_observation_surface != REQUESTED_OBSERVATION_FIELDS:
        raise ValueError("vsb_family_contract_observation_surface_invalid")
    if FAMILY_DATA_CONTRACT.allowed_expectation_surface:
        raise ValueError("vsb_family_contract_expectation_surface_must_be_empty")
    if FAMILY_DATA_CONTRACT.allowed_claim_surface:
        raise ValueError("vsb_family_contract_claim_surface_must_be_empty")
    if (RV_SHORT_WINDOW, RV_LONG_WINDOW, BREAKOUT_WINDOW, VOLUME_WINDOW) != (20, 60, 20, 20):
        raise ValueError("vsb_m0_window_drift")
    if SEARCH_FAMILY_ID != "VSB_M0_SEARCH_v1" or IMPLEMENTATION_ID != "VSB_M0_EQUAL_RANK_20_60_20_v1":
        raise ValueError("vsb_m0_search_identity_drift")
    if TRIAL_BUDGET_MAX != 1:
        raise ValueError("vsb_m0_trial_budget_drift")
    if PRIMARY_HORIZON_SESSIONS != 10 or SECONDARY_HORIZON_SESSIONS != 20 or WINNER_FRACTION != 0.05:
        raise ValueError("vsb_m0_label_law_drift")
    if CONFIRMATION_ROLE_ID != "VSB_CONFIRMATION_v1":
        raise ValueError("vsb_confirmation_role_drift")
    if MIN_MATURED_PRIMARY_DECISION_DATES != 20 or ACCEPTANCE_LIFT_THRESHOLD != 1.0:
        raise ValueError("vsb_confirmation_gate_drift")
    if (
        BOOTSTRAP_METHOD_ID != "NONCIRCULAR_MOVING_BLOCK_TRUNCATE_TYPE7_V1"
        or BOOTSTRAP_BLOCK_LENGTH != 10
        or BOOTSTRAP_REPLICATES != 10000
        or BOOTSTRAP_SEED != 20260810
        or BOOTSTRAP_CONFIDENCE != 0.80
        or BOOTSTRAP_LOWER_TAIL_PROBABILITY != 0.10
    ):
        raise ValueError("vsb_confirmation_bootstrap_law_drift")
    if MATURITY_STATUS != "MATURED_PRIMARY_10D" or OUTCOME_AUTHORITY_CLASS != "UNTOUCHED_OR_PROSPECTIVE_MATURED_LABEL":
        raise ValueError("vsb_confirmation_outcome_contract_drift")
