"""Provider-blind VOL_SQUEEZE_BREAKOUT_v1 M0 research core."""

from research.vol_squeeze_breakout_v1.contracts import (
    CONFIRMATION_ROLE_ID,
    FAMILY_ID,
    GUARDIAN_CONTRACT_SHA256,
    IMPLEMENTATION_ID,
    PRIMARY_LABEL_SPEC_ID,
    RISK_SET_SPEC_ID,
    SEARCH_FAMILY_ID,
    SECONDARY_LABEL_SPEC_ID,
)
from research.vol_squeeze_breakout_v1.features import compute_m0_features
from research.vol_squeeze_breakout_v1.guardian import evaluate_vsb_confirmation, verify_confirmation_result
from research.vol_squeeze_breakout_v1.ledger import append_prediction_batch, load_prediction_tape
from research.vol_squeeze_breakout_v1.model import score_m0_features
from research.vol_squeeze_breakout_v1.pit_packet import build_vsb_input_packet
from research.vol_squeeze_breakout_v1.runner import seal_m0_predictions, verify_prediction_batch
from research.vol_squeeze_breakout_v1.source import build_vsb_source_production

__all__ = [
    "CONFIRMATION_ROLE_ID",
    "FAMILY_ID",
    "GUARDIAN_CONTRACT_SHA256",
    "IMPLEMENTATION_ID",
    "PRIMARY_LABEL_SPEC_ID",
    "RISK_SET_SPEC_ID",
    "SEARCH_FAMILY_ID",
    "SECONDARY_LABEL_SPEC_ID",
    "build_vsb_source_production",
    "build_vsb_input_packet",
    "compute_m0_features",
    "score_m0_features",
    "evaluate_vsb_confirmation",
    "verify_confirmation_result",
    "seal_m0_predictions",
    "verify_prediction_batch",
    "append_prediction_batch",
    "load_prediction_tape",
]
