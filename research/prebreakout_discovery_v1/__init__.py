"""PREBREAKOUT_DISCOVERY_v1 public development walk-forward surface."""

from research.prebreakout_discovery_v1.contracts import (
    DEVELOPMENT_AUTHORITY_CLASS,
    FAMILY_ID,
    DevelopmentCandidate,
    PrebreakoutWalkForwardError,
    TemporalFold,
    WalkForwardMode,
    WalkForwardSpec,
)
from research.prebreakout_discovery_v1.walk_forward import (
    build_temporal_folds,
    is_cross_sectional_holdout,
    run_charged_development_candidate,
)
from research.prebreakout_discovery_v1.trial1_m0 import (
    IMPLEMENTATION_ID as TRIAL1_M0_IMPLEMENTATION_ID,
    TRIAL_ID as TRIAL1_M0_TRIAL_ID,
    build_trial1_walk_forward_spec,
    compute_trial1_m0_features,
    prepare_trial1_m0_for_trial_open,
    trial1_m0_scorer,
    uncharged_trial1_declaration,
    verify_trial1_source_manifest,
)

__all__ = [
    "DEVELOPMENT_AUTHORITY_CLASS",
    "FAMILY_ID",
    "DevelopmentCandidate",
    "PrebreakoutWalkForwardError",
    "TemporalFold",
    "WalkForwardMode",
    "WalkForwardSpec",
    "build_temporal_folds",
    "is_cross_sectional_holdout",
    "run_charged_development_candidate",
    "TRIAL1_M0_IMPLEMENTATION_ID",
    "TRIAL1_M0_TRIAL_ID",
    "build_trial1_walk_forward_spec",
    "compute_trial1_m0_features",
    "prepare_trial1_m0_for_trial_open",
    "trial1_m0_scorer",
    "uncharged_trial1_declaration",
    "verify_trial1_source_manifest",
]
