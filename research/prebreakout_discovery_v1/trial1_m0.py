"""Uncharged Trial-1 M0 candidate for PREBREAKOUT_DISCOVERY_v1.

Trial-1 is deliberately deterministic and pre-fit.  This module freezes the
market-only early-warning representation, scoring rule, split/holdout/control
identities, primary development objective, and the source-manifest gate needed
before a W2 ``TRIAL_OPEN`` may be appended.

Nothing in this module appends a trial, opens labels, reads W6, queries a
provider, or grants financial/capital authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
import re
from statistics import median
from typing import Any, Mapping, Sequence

import pandas as pd

from core.gv_fs0_canonical import assert_sha256, domain_hash
from research.prebreakout_discovery_v1 import preregistration as w2
from research.prebreakout_discovery_v1.contracts import (
    DevelopmentCandidate,
    PrebreakoutWalkForwardError,
    TemporalFold,
    WalkForwardMode,
    WalkForwardSpec,
)


TRIAL_ID = "PREBREAKOUT_TRIAL_1_M0"
IMPLEMENTATION_ID = "PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1"
FEATURE_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_MARKET_20_60_5_15_V1"
TRANSFORM_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_FIXED_COMPONENT_TRANSFORMS_V1"
MODEL_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_DETERMINISTIC_AND_GATE_V1"
TRAINING_WINDOW_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_EXPANDING_126_V1"
CALIBRATION_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_NO_CALIBRATION_V1"
RANKING_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_TRIGGERED_SCORE_DESC_SECURITY_ID_ASC_V1"
CONTROL_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_DATE_LOCAL_FULL_ORDINARY_CONTROL_V1"
CROSS_SECTIONAL_HOLDOUT_SPEC_ID = "PREBREAKOUT_TRIAL1_M0_CIQSEC_HASH_MOD5_REM0_V1"
TEMPORAL_FOLD_PLAN_ID = "PREBREAKOUT_TRIAL1_M0_EXPANDING_126_20E_4X20OOS_V1"
PRIMARY_OBJECTIVE_ID = "PREBREAKOUT_TRIAL1_M0_RIGHT_TAIL_LIFT_THEN_TTFLD_V1"
SOURCE_MANIFEST_SCHEMA = "prebreakout_trial1_m0_source_manifest_v1"
SOURCE_AUTHORITY_CLASS = "W3_W4_BOUND_DEVELOPMENT_SOURCE_ZERO_FINANCIAL_AUTHORITY"

MARKET_INPUT_COLUMNS = (
    "security_id",
    "trading_item_id",
    "session_date",
    "close",
    "total_return_1d",
    "volume",
)
FEATURE_COLUMNS = (
    "near_high_component",
    "vol_compression_component",
    "volume_pressure_component",
    "prebreakout_trigger",
)

MIN_HISTORY_SESSIONS = 60
PRIOR_HIGH_WINDOW = 20
RV_SHORT_WINDOW = 20
RV_LONG_WINDOW = 60
RECENT_VOLUME_WINDOW = 5
PRIOR_VOLUME_WINDOW = 15
NEAR_HIGH_FLOOR_RATIO = 0.95
COMPONENT_CAP_RATIO = 2.0
COMPONENT_CAP_LOG = log(COMPONENT_CAP_RATIO)

WALK_FORWARD_MODE = WalkForwardMode.EXPANDING
FOLD_COUNT = 4
MINIMUM_TRAINING_SESSIONS = 126
EMBARGO_SESSIONS = 20
OOS_SESSIONS_PER_FOLD = 20
HOLDOUT_SEED = "PREBREAKOUT_TRIAL1_M0_XS_HOLDOUT_20260810_V1"
HOLDOUT_MODULUS = 5
HOLDOUT_REMAINDERS = (0,)

_CIQ_SECURITY_RE = re.compile(r"^CIQSEC:IQ\d+$")
_TRADING_ITEM_RE = re.compile(r"^\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_SOURCE_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "family_id",
        "w2_contract_sha256",
        "risk_set_spec_id",
        "primary_label_spec_id",
        "market_history_payload_sha256",
        "w3_pit_authority_bundle_sha256",
        "w4_control_definition_sha256",
        "w4_development_label_custody_sha256",
        "w4_episode_custody_sha256",
        "decision_spine_sha256",
        "source_receipt_bundle_sha256",
        "development_label_visibility_at_manifest",
        "smoke_statistical_weight",
        "holdout_label_tuning_authority",
        "w6_lockbox_included",
        "financial_alpha_evidence",
        "capital_authority",
        "authority_class",
        "manifest_sha256",
    }
)


PRIMARY_OBJECTIVE_SPEC = {
    "objective_id": PRIMARY_OBJECTIVE_ID,
    "population": "POSITIVE_WEIGHT_NON_HOLDOUT_TEMPORAL_OOS_ONLY",
    "flag_rule": "FORECAST_SCORE_STRICTLY_GREATER_THAN_ZERO",
    "right_tail_label_spec_id": w2.PRIMARY_LABEL_SPEC_ID,
    "control_spec_id": CONTROL_SPEC_ID,
    "fold_recall_lift_formula": (
        "(SUM_FLAGGED_WINNERS/SUM_WINNERS) / "
        "(SUM_DATE_WINNER_COUNT_WEIGHTED_FLAG_BREADTH/SUM_WINNERS)"
    ),
    "right_tail_aggregate": "MEDIAN_ACROSS_INFORMATIVE_TEMPORAL_OOS_FOLDS",
    "lead_metric": "MEDIAN_EFFECTIVE_TTFLD_SESSIONS_WITH_MISS_EQUALS_ZERO",
    "lead_window_spec_id": w2.TTFLD_SPEC_ID,
    "selection_rule": "LEXICOGRAPHIC_MAX_RIGHT_TAIL_RECALL_LIFT_THEN_MEDIAN_EFFECTIVE_TTFLD",
    "null_law": (
        "NULL_IF_FEWER_THAN_TWO_INFORMATIVE_FOLDS_OR_NO_ELIGIBLE_WINNER_EPISODES;"
        "TRIAL_COST_REMAINS_ONE"
    ),
    "cagr_primary": False,
    "sharpe_primary": False,
}

CONTROL_SPEC = {
    "control_spec_id": CONTROL_SPEC_ID,
    "type": "DATE_LOCAL_FULL_ORDINARY_CONTROL",
    "denominator": "POSITIVE_WEIGHT_NON_HOLDOUT_W3_ELIGIBLE_ROWS",
    "baseline_recall": "FLAGGED_COUNT_DIVIDED_BY_ELIGIBLE_COUNT_ON_EACH_DATE",
    "aggregation": "WINNER_COUNT_WEIGHTED_WITHIN_FOLD",
    "sampled_control_rows": False,
    "w4_match_columns": ["trial1_control_stratum"],
    "w4_match_value": "ALL_W3_ELIGIBLE",
    "w4_matched_controls_role": "ALL_SAME_SESSION_POSITIVE_WEIGHT_ORDINARY_CONTROLS",
}

TRIAL1_W4_CONTROL_DEFINITION_SHA256 = domain_hash(
    "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_CONTROL_DEFINITION",
    w2.hash_safe(
        {
            "methodology_contract_sha256": w2.CONTRACT_SHA256,
            "control_spec_id": CONTROL_SPEC_ID,
            "match_columns": ["trial1_control_stratum"],
            "match_value": "ALL_W3_ELIGIBLE",
            "sampled_control_rows": False,
        }
    ),
)


@dataclass(frozen=True)
class PreparedTrial1M0:
    """An exact charge-ready declaration that has not been appended to W2."""

    trial_id: str
    implementation_id: str
    source_manifest_sha256: str
    code_sha256: str
    variant: Mapping[str, str]
    variant_sha256: str
    trial_cost: int = 1
    trial_open_appended: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "implementation_id": self.implementation_id,
            "source_manifest_sha256": self.source_manifest_sha256,
            "code_sha256": self.code_sha256,
            "variant": dict(self.variant),
            "variant_sha256": self.variant_sha256,
            "trial_cost": self.trial_cost,
            "trial_open_appended": self.trial_open_appended,
            "remaining_budget_after_open_if_appended": w2.TRIAL_BUDGET_MAX - self.trial_cost,
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
            "w6_lockbox_access": "FORBIDDEN",
        }


def build_trial1_walk_forward_spec() -> WalkForwardSpec:
    """Return the exact Trial-1 split/holdout declaration.

    Trial-1 uses one expanding plan. A later rolling variant is a different
    material training-window choice and therefore requires another charged
    trial rather than an in-place switch after label visibility.
    """

    return WalkForwardSpec(
        walk_forward_plan_id=TEMPORAL_FOLD_PLAN_ID,
        training_window_spec_id=TRAINING_WINDOW_SPEC_ID,
        cross_sectional_holdout_spec_id=CROSS_SECTIONAL_HOLDOUT_SPEC_ID,
        development_objective_id=PRIMARY_OBJECTIVE_ID,
        family_id=w2.FAMILY_ID,
        risk_set_spec_id=w2.RISK_SET_SPEC_ID,
        primary_label_spec_id=w2.PRIMARY_LABEL_SPEC_ID,
        primary_horizon_sessions=w2.PRIMARY_HORIZON_SESSIONS,
        search_family_id=w2.SEARCH_FAMILY_ID,
        trial_ledger_scope=w2.TRIAL_LEDGER_SCOPE,
        trial_budget_max=w2.TRIAL_BUDGET_MAX,
        mode=WALK_FORWARD_MODE,
        fold_count=FOLD_COUNT,
        minimum_training_sessions=MINIMUM_TRAINING_SESSIONS,
        rolling_training_sessions=None,
        embargo_sessions=EMBARGO_SESSIONS,
        oos_sessions_per_fold=OOS_SESSIONS_PER_FOLD,
        feature_columns=FEATURE_COLUMNS,
        holdout_seed=HOLDOUT_SEED,
        holdout_modulus=HOLDOUT_MODULUS,
        holdout_remainders=HOLDOUT_REMAINDERS,
    )


def uncharged_trial1_declaration() -> dict[str, Any]:
    """Expose the frozen candidate without inventing a source-manifest hash."""

    spec = build_trial1_walk_forward_spec()
    body = {
        "trial_id": TRIAL_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "feature_spec_id": FEATURE_SPEC_ID,
        "transform_spec_id": TRANSFORM_SPEC_ID,
        "model_spec_id": MODEL_SPEC_ID,
        "training_window_spec_id": TRAINING_WINDOW_SPEC_ID,
        "calibration_spec_id": CALIBRATION_SPEC_ID,
        "ranking_spec_id": RANKING_SPEC_ID,
        "control_spec": CONTROL_SPEC,
        "cross_sectional_holdout_spec_id": CROSS_SECTIONAL_HOLDOUT_SPEC_ID,
        "temporal_fold_plan_id": TEMPORAL_FOLD_PLAN_ID,
        "walk_forward_spec_sha256": spec.spec_sha256,
        "primary_objective": PRIMARY_OBJECTIVE_SPEC,
        "feature_formula": feature_formula_contract(),
        "source_manifest_sha256": None,
        "trial_open_status": "BLOCKED_WAITING_EXACT_W3_W4_SOURCE_MANIFEST",
        "trial_cost_if_opened": w2.TRIAL_COST_PER_MATERIAL_VARIANT,
        "trial_budget_max": w2.TRIAL_BUDGET_MAX,
        "labels_may_be_inspected": False,
        "w6_lockbox_access": "FORBIDDEN",
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return {
        **body,
        "declaration_sha256": domain_hash(
            "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_UNCHARGED_DECLARATION",
            w2.hash_safe(body),
        ),
    }


def feature_formula_contract() -> dict[str, Any]:
    return {
        "market_inputs": ["market.close", "market.total_return_1d", "market.volume"],
        "minimum_history_sessions": MIN_HISTORY_SESSIONS,
        "prior_high20": "MAX_CLOSE_OVER_IMMEDIATELY_PRIOR_20_OBSERVED_SESSIONS_EXCLUDING_T",
        "near_high_gate": "0.95*PRIOR_HIGH20 <= CLOSE_T <= PRIOR_HIGH20",
        "near_high_component": "CLIP((CLOSE_T/PRIOR_HIGH20 - 0.95)/0.05,0,1)",
        "rv20": "SAMPLE_STD_LAST_20_TOTAL_RETURN_1D_THROUGH_T_DDOF_1",
        "rv60": "SAMPLE_STD_LAST_60_TOTAL_RETURN_1D_THROUGH_T_DDOF_1",
        "vol_compression_gate": "RV20 < RV60",
        "vol_compression_component": "CLIP(LOG(RV60/RV20)/LOG(2),0,1)",
        "recent_volume5": "MEDIAN_VOLUME_T_MINUS_4_THROUGH_T",
        "prior_volume15": "MEDIAN_VOLUME_T_MINUS_19_THROUGH_T_MINUS_5",
        "volume_pressure_gate": "RECENT_VOLUME5 > PRIOR_VOLUME15",
        "volume_pressure_component": "CLIP(LOG(RECENT_VOLUME5/PRIOR_VOLUME15)/LOG(2),0,1)",
        "trigger": "NEAR_HIGH_GATE AND VOL_COMPRESSION_GATE AND VOLUME_PRESSURE_GATE",
        "forecast_score": (
            "IF_TRIGGER_THEN_MEAN(NEAR_HIGH_COMPONENT,VOL_COMPRESSION_COMPONENT,"
            "VOLUME_PRESSURE_COMPONENT)_ELSE_ZERO"
        ),
        "fit_parameters": 0,
        "calibration": "NONE",
        "invalid_history_policy": "ABSTAIN_SCORE_ZERO_NO_IMPUTATION",
    }


def verify_trial1_source_manifest(manifest: Mapping[str, Any]) -> str:
    """Verify an exact W3/W4-bound source manifest without reading label values."""

    if not isinstance(manifest, Mapping):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_mapping_required")
    if set(manifest) != _SOURCE_MANIFEST_FIELDS:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_fields_invalid")
    if manifest.get("schema_version") != SOURCE_MANIFEST_SCHEMA:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_schema_invalid")
    if manifest.get("family_id") != w2.FAMILY_ID:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_family_invalid")
    if manifest.get("w2_contract_sha256") != w2.CONTRACT_SHA256:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_w2_hash_invalid")
    if manifest.get("risk_set_spec_id") != w2.RISK_SET_SPEC_ID:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_risk_set_invalid")
    if manifest.get("primary_label_spec_id") != w2.PRIMARY_LABEL_SPEC_ID:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_label_invalid")
    for field in (
        "market_history_payload_sha256",
        "w3_pit_authority_bundle_sha256",
        "w4_control_definition_sha256",
        "w4_development_label_custody_sha256",
        "w4_episode_custody_sha256",
        "decision_spine_sha256",
        "source_receipt_bundle_sha256",
    ):
        _sha256(manifest.get(field), field)
    if manifest.get("w4_control_definition_sha256") != TRIAL1_W4_CONTROL_DEFINITION_SHA256:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_control_definition_invalid")
    if manifest.get("development_label_visibility_at_manifest") != "HASHED_NOT_INSPECTED":
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_label_visibility_invalid")
    if manifest.get("smoke_statistical_weight") != 0:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_smoke_weight_must_be_zero")
    if manifest.get("holdout_label_tuning_authority") != "FORBIDDEN":
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_holdout_tuning_invalid")
    if manifest.get("w6_lockbox_included") is not False:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_w6_forbidden")
    if manifest.get("financial_alpha_evidence") != 0 or manifest.get("capital_authority") != "NONE":
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_authority_invalid")
    if manifest.get("authority_class") != SOURCE_AUTHORITY_CLASS:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_authority_class_invalid")
    sealed = _sha256(manifest.get("manifest_sha256"), "manifest_sha256")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    expected = domain_hash(
        "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_SOURCE_MANIFEST",
        w2.hash_safe(body),
    )
    if sealed != expected:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_source_manifest_hash_mismatch")
    return sealed


def prepare_trial1_m0_for_trial_open(
    *,
    source_manifest: Mapping[str, Any],
    code_sha256: str,
) -> PreparedTrial1M0:
    """Prepare exact W2 variant bytes; never append ``TRIAL_OPEN`` here."""

    source_manifest_sha256 = verify_trial1_source_manifest(source_manifest)
    code_hash = _sha256(code_sha256, "code_sha256")
    spec = build_trial1_walk_forward_spec()
    variant = {
        "implementation_id": IMPLEMENTATION_ID,
        "feature_spec_id": FEATURE_SPEC_ID,
        "transform_spec_id": TRANSFORM_SPEC_ID,
        "model_spec_id": MODEL_SPEC_ID,
        "training_window_spec_id": TRAINING_WINDOW_SPEC_ID,
        "calibration_spec_id": CALIBRATION_SPEC_ID,
        "ranking_spec_id": RANKING_SPEC_ID,
        "control_spec_id": CONTROL_SPEC_ID,
        "cross_sectional_holdout_spec_id": CROSS_SECTIONAL_HOLDOUT_SPEC_ID,
        "temporal_fold_plan_id": TEMPORAL_FOLD_PLAN_ID,
        "source_manifest_sha256": source_manifest_sha256,
        "code_sha256": code_hash,
    }
    if spec.walk_forward_plan_id != variant["temporal_fold_plan_id"]:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_fold_plan_binding_invalid")
    if spec.training_window_spec_id != variant["training_window_spec_id"]:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_training_window_binding_invalid")
    if spec.cross_sectional_holdout_spec_id != variant["cross_sectional_holdout_spec_id"]:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_holdout_binding_invalid")
    variant_sha256 = domain_hash(
        "PREBREAKOUT_DISCOVERY_V1:TRIAL_VARIANT",
        w2.hash_safe(variant),
    )
    return PreparedTrial1M0(
        trial_id=TRIAL_ID,
        implementation_id=IMPLEMENTATION_ID,
        source_manifest_sha256=source_manifest_sha256,
        code_sha256=code_hash,
        variant=variant,
        variant_sha256=variant_sha256,
    )


def as_development_candidate(prepared: PreparedTrial1M0) -> DevelopmentCandidate:
    if prepared.trial_open_appended:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_prepared_state_must_remain_uncharged")
    return DevelopmentCandidate(
        trial_id=prepared.trial_id,
        implementation_id=prepared.implementation_id,
        variant_sha256=prepared.variant_sha256,
    )


def compute_trial1_m0_features(market_history: pd.DataFrame) -> pd.DataFrame:
    """Compute the exact deterministic market-only M0 representation.

    The function is outcome-blind. It accepts only exact listing/session market
    columns and intentionally rejects ticker, company, fundamentals, labels,
    sector, or fitted-model inputs by requiring an exact column set.
    """

    frame = _normalize_market_history(market_history)
    grouped = frame.groupby(["security_id", "trading_item_id"], sort=False, group_keys=False)

    frame["prior_high20"] = grouped["close"].transform(
        lambda series: series.shift(1).rolling(PRIOR_HIGH_WINDOW, min_periods=PRIOR_HIGH_WINDOW).max()
    )
    frame["rv20"] = grouped["total_return_1d"].transform(
        lambda series: series.rolling(RV_SHORT_WINDOW, min_periods=RV_SHORT_WINDOW).std(ddof=1)
    )
    frame["rv60"] = grouped["total_return_1d"].transform(
        lambda series: series.rolling(RV_LONG_WINDOW, min_periods=RV_LONG_WINDOW).std(ddof=1)
    )
    frame["recent_volume5"] = grouped["volume"].transform(
        lambda series: series.rolling(RECENT_VOLUME_WINDOW, min_periods=RECENT_VOLUME_WINDOW).median()
    )
    frame["prior_volume15"] = grouped["volume"].transform(
        lambda series: series.shift(RECENT_VOLUME_WINDOW)
        .rolling(PRIOR_VOLUME_WINDOW, min_periods=PRIOR_VOLUME_WINDOW)
        .median()
    )

    valid = (
        frame["prior_high20"].notna()
        & frame["rv20"].notna()
        & frame["rv60"].notna()
        & frame["recent_volume5"].notna()
        & frame["prior_volume15"].notna()
        & (frame["prior_high20"] > 0.0)
        & (frame["rv20"] > 0.0)
        & (frame["rv60"] > 0.0)
        & (frame["recent_volume5"] > 0.0)
        & (frame["prior_volume15"] > 0.0)
    )
    price_ratio = frame["close"] / frame["prior_high20"]
    near_high_gate = valid & price_ratio.ge(NEAR_HIGH_FLOOR_RATIO) & price_ratio.le(1.0)
    compression_gate = valid & frame["rv20"].lt(frame["rv60"])
    volume_gate = valid & frame["recent_volume5"].gt(frame["prior_volume15"])
    trigger = near_high_gate & compression_gate & volume_gate

    near_component = ((price_ratio - NEAR_HIGH_FLOOR_RATIO) / (1.0 - NEAR_HIGH_FLOOR_RATIO)).clip(0.0, 1.0)
    compression_component = (
        (frame["rv60"] / frame["rv20"]).map(lambda value: log(value) if value > 0 and isfinite(value) else float("nan"))
        / COMPONENT_CAP_LOG
    ).clip(0.0, 1.0)
    volume_component = (
        (frame["recent_volume5"] / frame["prior_volume15"])
        .map(lambda value: log(value) if value > 0 and isfinite(value) else float("nan"))
        / COMPONENT_CAP_LOG
    ).clip(0.0, 1.0)

    frame["near_high_component"] = near_component.where(valid, 0.0).fillna(0.0)
    frame["vol_compression_component"] = compression_component.where(valid, 0.0).fillna(0.0)
    frame["volume_pressure_component"] = volume_component.where(valid, 0.0).fillna(0.0)
    frame["prebreakout_trigger"] = trigger.astype(bool)
    frame["forecast_score"] = (
        frame[["near_high_component", "vol_compression_component", "volume_pressure_component"]]
        .mean(axis=1)
        .where(frame["prebreakout_trigger"], 0.0)
    )
    frame["feature_status"] = valid.map(
        {True: "READY", False: "INSUFFICIENT_OR_INVALID_MARKET_HISTORY"}
    )

    return frame[
        [
            *MARKET_INPUT_COLUMNS,
            "feature_status",
            "prior_high20",
            "rv20",
            "rv60",
            "recent_volume5",
            "prior_volume15",
            *FEATURE_COLUMNS,
            "forecast_score",
        ]
    ].reset_index(drop=True)


def trial1_m0_scorer(
    candidate: DevelopmentCandidate,
    training: pd.DataFrame,
    score_source: pd.DataFrame,
    fold: TemporalFold,
) -> pd.DataFrame:
    """W5 scorer adapter that intentionally ignores all training labels."""

    del training, fold
    if candidate.trial_id != TRIAL_ID or candidate.implementation_id != IMPLEMENTATION_ID:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_candidate_identity_invalid")
    required = {"decision_date", "security_id", "trading_item_id", *FEATURE_COLUMNS}
    if set(score_source.columns) != required:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_score_source_columns_invalid")
    trigger = score_source["prebreakout_trigger"]
    if not pd.api.types.is_bool_dtype(trigger.dtype):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_trigger_boolean_required")
    components = score_source[
        ["near_high_component", "vol_compression_component", "volume_pressure_component"]
    ].apply(pd.to_numeric, errors="coerce")
    if components.isna().any().any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_component_numeric_required")
    if ((components < 0.0) | (components > 1.0)).any().any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_component_out_of_bounds")
    score = components.mean(axis=1).where(trigger, 0.0)
    return pd.DataFrame(
        {
            "decision_date": score_source["decision_date"].astype(str),
            "security_id": score_source["security_id"].astype(str),
            "forecast_score": score.astype(float),
        }
    )


def trial1_m0_fold_recall_lift_objective(
    rows: pd.DataFrame,
    fold: TemporalFold,
) -> float | None:
    """Compute the frozen fold-level right-tail recall lift.

    The fold object is intentionally not used to alter the formula. The
    denominator is the complete positive-weight non-holdout temporal-OOS
    population supplied by the W5 runner. A fold is uninformative when it has
    no winners or zero breadth baseline; the frozen Trial-1 null law handles
    the aggregate rather than inventing a finite replacement.
    """

    del fold
    required = {"decision_date", "security_id", "forecast_score", "target_label"}
    if not isinstance(rows, pd.DataFrame) or set(rows.columns) != required or rows.empty:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_objective_rows_invalid")
    frame = rows.copy()
    frame["decision_date"] = frame["decision_date"].astype(str)
    frame["forecast_score"] = pd.to_numeric(frame["forecast_score"], errors="coerce")
    if frame["forecast_score"].isna().any() or not frame["forecast_score"].map(
        lambda value: isfinite(float(value))
    ).all():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_objective_score_finite_required")
    labels = pd.to_numeric(frame["target_label"], errors="coerce")
    if labels.isna().any() or not labels.isin([0, 1]).all():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_objective_binary_label_required")
    frame["winner"] = labels.astype(int)
    frame["flagged"] = frame["forecast_score"].gt(0.0)

    grouped = frame.groupby("decision_date", sort=True)
    date_stats = grouped.agg(
        eligible_count=("security_id", "size"),
        winner_count=("winner", "sum"),
        flagged_count=("flagged", "sum"),
    )
    flagged_winner_count = grouped.apply(
        lambda group: int((group["flagged"] & group["winner"].eq(1)).sum()),
        include_groups=False,
    )
    date_stats["flagged_winner_count"] = flagged_winner_count
    total_winners = int(date_stats["winner_count"].sum())
    if total_winners <= 0:
        return None
    total_flagged_winners = int(date_stats["flagged_winner_count"].sum())
    observed_recall = total_flagged_winners / total_winners
    breadth = date_stats["flagged_count"] / date_stats["eligible_count"]
    breadth_baseline = float((date_stats["winner_count"] * breadth).sum()) / total_winners
    if not isfinite(breadth_baseline) or breadth_baseline <= 0.0:
        return None
    lift = observed_recall / breadth_baseline
    if not isfinite(lift):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_objective_lift_nonfinite")
    return float(lift)


def summarize_trial1_recall_lift(run: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the frozen median/NULL law to Trial-1 fold recall-lift values."""

    if not isinstance(run, Mapping):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_run_mapping_required")
    if run.get("development_objective_id") != PRIMARY_OBJECTIVE_ID:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_run_objective_identity_invalid")
    folds = run.get("folds")
    if not isinstance(folds, list) or len(folds) != FOLD_COUNT:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_run_fold_count_invalid")
    values: list[float] = []
    for fold in folds:
        if not isinstance(fold, Mapping):
            raise PrebreakoutWalkForwardError("prebreakout_trial1_run_fold_mapping_required")
        status = str(fold.get("development_objective_status") or "")
        raw = fold.get("development_objective_value")
        if status == "UNINFORMATIVE":
            if raw is not None:
                raise PrebreakoutWalkForwardError("prebreakout_trial1_uninformative_fold_value_forbidden")
            continue
        if status != "INFORMATIVE":
            raise PrebreakoutWalkForwardError("prebreakout_trial1_fold_objective_status_invalid")
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise PrebreakoutWalkForwardError("prebreakout_trial1_fold_objective_value_invalid") from exc
        if not isfinite(value):
            raise PrebreakoutWalkForwardError("prebreakout_trial1_fold_objective_value_nonfinite")
        values.append(value)
    if len(values) < 2:
        return {
            "status": "NULL",
            "informative_fold_count": len(values),
            "median_temporal_oos_recall_lift": None,
        }
    return {
        "status": "INFORMATIVE",
        "informative_fold_count": len(values),
        "median_temporal_oos_recall_lift": format(float(median(values)), ".17g"),
    }


def _normalize_market_history(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise PrebreakoutWalkForwardError("prebreakout_trial1_market_history_required")
    if set(frame.columns) != set(MARKET_INPUT_COLUMNS):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_market_history_columns_invalid")
    out = frame.copy()
    out["security_id"] = out["security_id"].map(_security_id)
    out["trading_item_id"] = out["trading_item_id"].map(_trading_item_id)
    out["session_date"] = pd.to_datetime(out["session_date"], errors="coerce").dt.date.astype(str)
    if out["session_date"].eq("NaT").any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_session_date_invalid")
    for field in ("close", "volume"):
        out[field] = pd.to_numeric(out[field], errors="coerce")
        if out[field].isna().any() or not out[field].map(lambda value: isfinite(float(value))).all():
            raise PrebreakoutWalkForwardError(f"prebreakout_trial1_{field}_finite_required")

    raw_total_return = out["total_return_1d"]
    provider_missing = raw_total_return.isna() | raw_total_return.astype(str).str.strip().eq("")
    out["total_return_1d"] = pd.to_numeric(raw_total_return, errors="coerce")
    invalid_nonmissing = (~provider_missing) & out["total_return_1d"].isna()
    nonfinite_nonmissing = out["total_return_1d"].notna() & ~out["total_return_1d"].map(
        lambda value: isfinite(float(value))
    )
    if invalid_nonmissing.any() or nonfinite_nonmissing.any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_total_return_1d_finite_required")
    if (out["close"] <= 0.0).any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_close_positive_required")
    if (out["volume"] < 0.0).any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_volume_nonnegative_required")
    if out.duplicated(["security_id", "trading_item_id", "session_date"]).any():
        raise PrebreakoutWalkForwardError("prebreakout_trial1_market_history_duplicate_exact_listing_session")
    out.sort_values(["security_id", "trading_item_id", "session_date"], inplace=True, kind="stable")
    out.reset_index(drop=True, inplace=True)
    return out


def _security_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _CIQ_SECURITY_RE.fullmatch(text):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_ciq_security_id_required")
    return text


def _trading_item_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _TRADING_ITEM_RE.fullmatch(text):
        raise PrebreakoutWalkForwardError("prebreakout_trial1_trading_item_id_required")
    return text


def _sha256(value: Any, field: str) -> str:
    text = str(value or "").strip().lower()
    try:
        assert_sha256(text)
    except ValueError as exc:
        raise PrebreakoutWalkForwardError(f"prebreakout_trial1_{field}_invalid") from exc
    if not _SHA256_RE.fullmatch(text):  # defensive normalization closure
        raise PrebreakoutWalkForwardError(f"prebreakout_trial1_{field}_invalid")
    return text


__all__ = [
    "CALIBRATION_SPEC_ID",
    "CONTROL_SPEC",
    "CONTROL_SPEC_ID",
    "CROSS_SECTIONAL_HOLDOUT_SPEC_ID",
    "FEATURE_COLUMNS",
    "FEATURE_SPEC_ID",
    "IMPLEMENTATION_ID",
    "MODEL_SPEC_ID",
    "PRIMARY_OBJECTIVE_ID",
    "PRIMARY_OBJECTIVE_SPEC",
    "PreparedTrial1M0",
    "RANKING_SPEC_ID",
    "SOURCE_AUTHORITY_CLASS",
    "SOURCE_MANIFEST_SCHEMA",
    "TEMPORAL_FOLD_PLAN_ID",
    "TRAINING_WINDOW_SPEC_ID",
    "TRIAL1_W4_CONTROL_DEFINITION_SHA256",
    "TRANSFORM_SPEC_ID",
    "TRIAL_ID",
    "as_development_candidate",
    "build_trial1_walk_forward_spec",
    "compute_trial1_m0_features",
    "feature_formula_contract",
    "prepare_trial1_m0_for_trial_open",
    "summarize_trial1_recall_lift",
    "trial1_m0_fold_recall_lift_objective",
    "trial1_m0_scorer",
    "uncharged_trial1_declaration",
    "verify_trial1_source_manifest",
]
