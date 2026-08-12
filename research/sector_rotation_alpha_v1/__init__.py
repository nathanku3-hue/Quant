"""Provider-blind ETF-first SECTOR_ROTATION_ALPHA_v1 research core."""

from research.sector_rotation_alpha_v1.acquisition import (
    build_frozen_acquisition_request,
    require_capture_reopen,
    verify_frozen_acquisition_request,
)
from research.sector_rotation_alpha_v1.contracts import (
    FAMILY_ID,
    IMPLEMENTATION_ID,
    PRIMARY_LABEL_SPEC_ID,
    RISK_SET_SPEC_ID,
    SEARCH_FAMILY_ID,
    SECONDARY_LABEL_SPEC_ID,
)
from research.sector_rotation_alpha_v1.features import compute_m0_features
from research.sector_rotation_alpha_v1.ledger import append_prediction_batch, load_prediction_tape
from research.sector_rotation_alpha_v1.model import score_m0_features
from research.sector_rotation_alpha_v1.pit_packet import build_sector_rotation_input_packet
from research.sector_rotation_alpha_v1.runner import seal_m0_predictions, verify_prediction_batch
from research.sector_rotation_alpha_v1.source import build_sector_rotation_source_production
from research.sector_rotation_alpha_v1.trial_ledger import (
    append_trial_receipt,
    build_code_manifest,
    build_trial_receipt,
    load_trial_ledger,
)

__all__ = [
    "FAMILY_ID",
    "IMPLEMENTATION_ID",
    "PRIMARY_LABEL_SPEC_ID",
    "RISK_SET_SPEC_ID",
    "SEARCH_FAMILY_ID",
    "SECONDARY_LABEL_SPEC_ID",
    "build_frozen_acquisition_request",
    "verify_frozen_acquisition_request",
    "require_capture_reopen",
    "build_sector_rotation_source_production",
    "build_sector_rotation_input_packet",
    "compute_m0_features",
    "score_m0_features",
    "build_code_manifest",
    "build_trial_receipt",
    "append_trial_receipt",
    "load_trial_ledger",
    "seal_m0_predictions",
    "verify_prediction_batch",
    "append_prediction_batch",
    "load_prediction_tape",
]
