"""Frozen contracts for ETF-first SECTOR_ROTATION_ALPHA_v1 M0."""

from __future__ import annotations

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import FamilyDataContract


FAMILY_ID = "SECTOR_ROTATION_ALPHA_v1"
RISK_SET_SPEC_ID = "SRA_US_SELECT_SECTOR_ETF_11_V1"
PRIMARY_LABEL_SPEC_ID = "SRA_RIGHT_TAIL_20D_TOP2_V1"
SECONDARY_LABEL_SPEC_ID = "SRA_RIGHT_TAIL_40D_TOP2_V1"

REQUESTED_OBSERVATION_FIELDS = (
    "market.close",
    "market.total_return_1d",
    "market.volume",
)
FAMILY_DATA_CONTRACT = FamilyDataContract(
    family_id=FAMILY_ID,
    risk_set_spec_id=RISK_SET_SPEC_ID,
    primary_label_spec_id=PRIMARY_LABEL_SPEC_ID,
    allowed_observation_surface=REQUESTED_OBSERVATION_FIELDS,
    allowed_expectation_surface=(),
    allowed_claim_surface=(),
)
FAMILY_DATA_CONTRACT_SHA256 = domain_hash(
    "ALPHA_PIT_V1:FAMILY_DATA_CONTRACT",
    FAMILY_DATA_CONTRACT.as_dict(),
)

EXPECTED_SECTOR_KEYS = (
    "COMMUNICATION_SERVICES",
    "CONSUMER_DISCRETIONARY",
    "CONSUMER_STAPLES",
    "ENERGY",
    "FINANCIALS",
    "HEALTH_CARE",
    "INDUSTRIALS",
    "INFORMATION_TECHNOLOGY",
    "MATERIALS",
    "REAL_ESTATE",
    "UTILITIES",
)
EXPECTED_SECTOR_COUNT = len(EXPECTED_SECTOR_KEYS)

MARKET_HISTORY_ARTIFACT_TYPE = "SRA_ETF_MARKET_HISTORY"
MARKET_HISTORY_SCHEMA = "sra_etf_market_history_payload_v1"
INPUT_PACKET_SCHEMA = "sra_input_packet_v1"
FEATURE_PACKET_SCHEMA = "sra_m0_feature_packet_v1"
MODEL_OUTPUT_SCHEMA = "sra_m0_model_output_v1"
PREDICTION_SCHEMA = "sra_m0_prediction_batch_v1"
TRIAL_RECEIPT_SCHEMA = "sra_m0_trial_receipt_v1"

SEARCH_FAMILY_ID = "SRA_M0_SEARCH_v1"
IMPLEMENTATION_ID = "SRA_M0_RELSTR_20_60_DVP_5_20_EQUAL_RANK_v1"
PREDICTION_LEDGER_SCOPE = "SRA_V1_PREDICTION_LEDGER"
TRIAL_LEDGER_SCOPE = "SRA_V1_TRIAL_LEDGER"
ARTIFACT_NAMESPACE = "sector_rotation_alpha_v1/"
TRIAL_BUDGET_MAX = 1

RELATIVE_SHORT_WINDOW = 20
RELATIVE_LONG_WINDOW = 60
PARTICIPATION_SHORT_WINDOW = 5
PARTICIPATION_LONG_WINDOW = 20
MIN_HISTORY_SESSIONS = 60
PRIMARY_HORIZON_SESSIONS = 20
SECONDARY_HORIZON_SESSIONS = 40
PRIMARY_WINNER_COUNT = 2
SECONDARY_WINNER_COUNT = 2

MIN_MATURED_PRIMARY_DECISION_DATES = 30
BOOTSTRAP_BLOCK_LENGTH = 20
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 20260810
BOOTSTRAP_CONFIDENCE = 0.80
PRIMARY_LIFT_GATE = 1.0

MECHANISM_FALSIFIERS = (
    "PRIMARY_WINNER_RECALL_LIFT_NOT_ABOVE_ONE",
    "PRIMARY_80PCT_BLOCK_BOOTSTRAP_LB_NOT_ABOVE_ONE",
    "NO_INCREMENTAL_VALUE_VS_RELATIVE_STRENGTH_ONLY_BASELINE",
    "PIT_IDENTITY_OR_AVAILABILITY_VIOLATION",
    "MATERIAL_TRIAL_BUDGET_EXCEEDED",
)


def validate_sector_rotation_contract() -> None:
    if FAMILY_DATA_CONTRACT.family_id != FAMILY_ID:
        raise ValueError("sra_family_contract_family_invalid")
    if FAMILY_DATA_CONTRACT.risk_set_spec_id != RISK_SET_SPEC_ID:
        raise ValueError("sra_family_contract_risk_set_invalid")
    if FAMILY_DATA_CONTRACT.primary_label_spec_id != PRIMARY_LABEL_SPEC_ID:
        raise ValueError("sra_family_contract_primary_label_invalid")
    if FAMILY_DATA_CONTRACT.allowed_observation_surface != REQUESTED_OBSERVATION_FIELDS:
        raise ValueError("sra_family_contract_observation_surface_invalid")
    if FAMILY_DATA_CONTRACT.allowed_expectation_surface or FAMILY_DATA_CONTRACT.allowed_claim_surface:
        raise ValueError("sra_family_contract_nonmarket_surface_forbidden")
    if EXPECTED_SECTOR_COUNT != 11 or len(set(EXPECTED_SECTOR_KEYS)) != 11:
        raise ValueError("sra_expected_sector_universe_drift")
    if (RELATIVE_SHORT_WINDOW, RELATIVE_LONG_WINDOW) != (20, 60):
        raise ValueError("sra_relative_strength_window_drift")
    if (PARTICIPATION_SHORT_WINDOW, PARTICIPATION_LONG_WINDOW) != (5, 20):
        raise ValueError("sra_participation_window_drift")
    if (PRIMARY_HORIZON_SESSIONS, SECONDARY_HORIZON_SESSIONS) != (20, 40):
        raise ValueError("sra_horizon_drift")
    if (PRIMARY_WINNER_COUNT, SECONDARY_WINNER_COUNT) != (2, 2):
        raise ValueError("sra_winner_count_drift")
    if TRIAL_BUDGET_MAX != 1:
        raise ValueError("sra_trial_budget_drift")
    if SEARCH_FAMILY_ID != "SRA_M0_SEARCH_v1":
        raise ValueError("sra_search_family_drift")
