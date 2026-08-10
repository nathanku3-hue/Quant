"""Leakage-resistant W5 development walk-forward for PREBREAKOUT_DISCOVERY_v1.

This module does not define breakout B, features, winner labels, TTFLD,
falsifiers, or untouched evaluation. It consumes already-frozen development
inputs and enforces only temporal/cross-sectional/search-custody mechanics.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from math import isfinite
import re
from typing import Any

import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_discovery_v1.contracts import (
    DEVELOPMENT_AUTHORITY_CLASS,
    FAMILY_ID,
    DevelopmentCandidate,
    PrebreakoutWalkForwardError,
    TemporalFold,
    WalkForwardMode,
    WalkForwardSpec,
)
from research.prebreakout_discovery_v1.ledger import EVENT_CLOSE, EVENT_OPEN, verify_trial_ledger


FEATURE_KEY_COLUMNS = ("decision_date", "security_id")
FEATURE_META_COLUMNS = (
    "trading_item_id",
    "statistical_weight",
    "source_manifest_sha256",
    "pit_authority_sha256",
    "pit_risk_set_spec_id",
)
LABEL_STATUS_MATURED = "MATURED"
LABEL_STATUS_INCOMPLETE = "INCOMPLETE_HORIZON"
LABEL_COLUMNS = (
    "decision_date",
    "security_id",
    "target_label",
    "label_available_date",
    "label_status",
)
SCORE_COLUMNS = ("decision_date", "security_id", "forecast_score")

_CIQ_SECURITY_RE = re.compile(r"^CIQSEC:IQ\d+$")
_TRADING_ITEM_RE = re.compile(r"^\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

Scorer = Callable[[DevelopmentCandidate, pd.DataFrame, pd.DataFrame, TemporalFold], pd.DataFrame]
Objective = Callable[[pd.DataFrame, TemporalFold], float | None]


def build_temporal_folds(
    *,
    decision_dates: Sequence[str],
    spec: WalkForwardSpec,
) -> tuple[TemporalFold, ...]:
    """Build an exact chronological fold plan with an explicit label embargo."""

    dates = tuple(sorted({_date_text(value, "decision_date") for value in decision_dates}))
    if not dates:
        raise PrebreakoutWalkForwardError("prebreakout_decision_dates_required")

    mode = WalkForwardMode(spec.mode)
    initial_training = (
        spec.minimum_training_sessions
        if mode is WalkForwardMode.EXPANDING
        else int(spec.rolling_training_sessions or 0)
    )
    first_oos_index = initial_training + spec.embargo_sessions
    required_sessions = first_oos_index + spec.fold_count * spec.oos_sessions_per_fold
    if len(dates) < required_sessions:
        raise PrebreakoutWalkForwardError(
            "prebreakout_insufficient_sessions_for_requested_walk_forward:"
            f"required={required_sessions};actual={len(dates)}"
        )

    folds: list[TemporalFold] = []
    for fold_index in range(spec.fold_count):
        oos_start_index = first_oos_index + fold_index * spec.oos_sessions_per_fold
        oos_end_index = oos_start_index + spec.oos_sessions_per_fold - 1
        train_end_index = oos_start_index - spec.embargo_sessions - 1
        if mode is WalkForwardMode.EXPANDING:
            train_start_index = 0
        else:
            rolling = int(spec.rolling_training_sessions or 0)
            train_start_index = train_end_index - rolling + 1
        if train_start_index < 0:
            raise PrebreakoutWalkForwardError("prebreakout_negative_training_window_start")
        train_session_count = train_end_index - train_start_index + 1
        if train_session_count < spec.minimum_training_sessions:
            raise PrebreakoutWalkForwardError("prebreakout_training_window_below_minimum")

        embargo_start_index = train_end_index + 1
        embargo_end_index = oos_start_index - 1
        if embargo_end_index - embargo_start_index + 1 != spec.embargo_sessions:
            raise PrebreakoutWalkForwardError("prebreakout_embargo_session_count_drift")

        body = {
            "spec_sha256": spec.spec_sha256,
            "fold_index": fold_index,
            "train_start_date": dates[train_start_index],
            "train_end_date": dates[train_end_index],
            "embargo_start_date": dates[embargo_start_index],
            "embargo_end_date": dates[embargo_end_index],
            "oos_start_date": dates[oos_start_index],
            "oos_end_date": dates[oos_end_index],
            "train_session_count": train_session_count,
            "embargo_session_count": spec.embargo_sessions,
            "oos_session_count": spec.oos_sessions_per_fold,
        }
        fold_id = domain_hash("PREBREAKOUT_DISCOVERY_V1:TEMPORAL_FOLD", _hash_safe(body))
        folds.append(TemporalFold(fold_id=fold_id, **body_without_spec(body)))

    _verify_fold_order(folds)
    return tuple(folds)


def is_cross_sectional_holdout(security_id: str, *, spec: WalkForwardSpec) -> bool:
    """Stable security-level holdout assignment; never ticker- or outcome-based."""

    normalized = _security_id(security_id)
    digest = domain_hash(
        "PREBREAKOUT_DISCOVERY_V1:CROSS_SECTIONAL_HOLDOUT",
        {
            "holdout_id": spec.cross_sectional_holdout_spec_id,
            "holdout_seed": spec.holdout_seed,
            "security_id": normalized,
        },
    )
    bucket = int(digest[:16], 16) % spec.holdout_modulus
    return bucket in set(spec.holdout_remainders)


def run_charged_development_candidate(
    *,
    feature_frame: pd.DataFrame,
    label_frame: pd.DataFrame,
    spec: WalkForwardSpec,
    candidate: DevelopmentCandidate,
    trial_ledger_entries: Sequence[Mapping[str, Any]],
    scorer: Scorer,
    objective: Objective,
) -> dict[str, Any]:
    """Run one already-charged development candidate.

    The caller must persist/retain the search charge before calling this
    function. The function intentionally has no path that auto-charges after
    labels are visible.
    """

    features = _normalize_feature_frame(feature_frame, spec=spec)
    folds = build_temporal_folds(
        decision_dates=features["decision_date"].tolist(),
        spec=spec,
    )
    _validate_label_schema_only(label_frame)
    trial_open = _find_bound_trial_open(
        entries=trial_ledger_entries,
        spec=spec,
        candidate=candidate,
    )
    charged_source_manifest = str(trial_open["payload"]["variant"]["source_manifest_sha256"])
    development_source_manifest = str(features["source_manifest_sha256"].iloc[0])
    if development_source_manifest != charged_source_manifest:
        raise PrebreakoutWalkForwardError(
            "prebreakout_trial_open_source_manifest_binding_invalid"
        )

    # Material label values are first normalized only after the persistent W2
    # TRIAL_OPEN charge is proven present in the bound search ledger.
    labels = _normalize_label_frame(label_frame, feature_keys=features[list(FEATURE_KEY_COLUMNS)])
    holdout_by_security = {
        security_id: is_cross_sectional_holdout(security_id, spec=spec)
        for security_id in sorted(features["security_id"].unique())
    }
    _validate_holdout_feasibility(features, holdout_by_security=holdout_by_security)

    fold_results: list[dict[str, Any]] = []
    for fold in folds:
        fold_results.append(
            _run_fold(
                features=features,
                labels=labels,
                spec=spec,
                candidate=candidate,
                fold=fold,
                scorer=scorer,
                objective=objective,
                holdout_by_security=holdout_by_security,
            )
        )

    body = {
        "schema_version": "prebreakout_development_walk_forward_run_v1",
        "family_id": FAMILY_ID,
        "walk_forward_spec_sha256": spec.spec_sha256,
        "walk_forward_plan_id": spec.walk_forward_plan_id,
        "risk_set_spec_id": spec.risk_set_spec_id,
        "primary_label_spec_id": spec.primary_label_spec_id,
        "development_objective_id": spec.development_objective_id,
        "candidate": {
            "trial_id": candidate.trial_id,
            "implementation_id": candidate.implementation_id,
            "variant_sha256": candidate.variant_sha256,
        },
        "search_charge": trial_open,
        "development_source_manifest_sha256": development_source_manifest,
        "pit_risk_set_spec_id": spec.risk_set_spec_id,
        "pit_authority_sha256s": sorted(features["pit_authority_sha256"].unique()),
        "fold_count": len(fold_results),
        "folds": fold_results,
        "cross_sectional_holdout_id": spec.cross_sectional_holdout_spec_id,
        "cross_sectional_holdout_assignment_sha256": _holdout_assignment_hash(
            holdout_by_security=holdout_by_security,
            spec=spec,
        ),
        "label_scope": spec.label_scope,
        "oos_labels_exposed_in_prediction_rows": False,
        "cross_sectional_holdout_labels_used_by_search": False,
        "zero_weight_trace_rows_used_by_search": False,
        "authority_class": DEVELOPMENT_AUTHORITY_CLASS,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "untouched_evaluator_authority": "NONE",
        "prospective_clock_started": False,
    }
    run_sha256 = domain_hash("PREBREAKOUT_DISCOVERY_V1:DEVELOPMENT_RUN", _hash_safe(body))
    return {**body, "run_sha256": run_sha256}


def _run_fold(
    *,
    features: pd.DataFrame,
    labels: pd.DataFrame,
    spec: WalkForwardSpec,
    candidate: DevelopmentCandidate,
    fold: TemporalFold,
    scorer: Scorer,
    objective: Objective,
    holdout_by_security: dict[str, bool],
) -> dict[str, Any]:
    train_mask = (
        features["decision_date"].between(fold.train_start_date, fold.train_end_date)
        & (features["statistical_weight"] > 0.0)
        & ~features["security_id"].map(holdout_by_security)
    )
    train_features = features.loc[train_mask].copy()
    if train_features.empty:
        raise PrebreakoutWalkForwardError("prebreakout_fold_training_rows_empty")

    train_labels = labels.merge(
        train_features[list(FEATURE_KEY_COLUMNS)],
        on=list(FEATURE_KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    if len(train_labels) != len(train_features):
        raise PrebreakoutWalkForwardError("prebreakout_fold_training_label_key_mismatch")
    usable_train_labels = train_labels[
        train_labels["label_status"].eq(LABEL_STATUS_MATURED)
        & train_labels["label_available_date"].notna()
        & train_labels["label_available_date"].lt(fold.oos_start_date)
    ].copy()
    if usable_train_labels.empty:
        raise PrebreakoutWalkForwardError("prebreakout_fold_training_matured_labels_empty")

    training = train_features[
        [*FEATURE_KEY_COLUMNS, "trading_item_id", *spec.feature_columns]
    ].merge(
        usable_train_labels[[*FEATURE_KEY_COLUMNS, "target_label"]],
        on=list(FEATURE_KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )

    oos_mask = features["decision_date"].between(fold.oos_start_date, fold.oos_end_date)
    score_source = features.loc[
        oos_mask,
        [*FEATURE_KEY_COLUMNS, "trading_item_id", *spec.feature_columns],
    ].copy()
    if score_source.empty:
        raise PrebreakoutWalkForwardError("prebreakout_fold_oos_rows_empty")
    if "target_label" in score_source.columns or "label_available_date" in score_source.columns:
        raise PrebreakoutWalkForwardError("prebreakout_oos_label_surface_leak")

    scored = scorer(candidate, training.copy(), score_source.copy(), fold)
    predictions = _validate_score_frame(scored, expected_keys=score_source[list(FEATURE_KEY_COLUMNS)])

    # Freeze the development prediction bytes before any OOS label join.
    prediction_records = _prediction_records(predictions)
    prediction_sha256 = domain_hash(
        "PREBREAKOUT_DISCOVERY_V1:DEVELOPMENT_FOLD_PREDICTIONS",
        {
            "spec_sha256": spec.spec_sha256,
            "trial_id": candidate.trial_id,
            "fold_id": fold.fold_id,
            "rows": prediction_records,
        },
    )

    classified = predictions.merge(
        features.loc[oos_mask, [*FEATURE_KEY_COLUMNS, "statistical_weight"]],
        on=list(FEATURE_KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    classified["is_cross_sectional_holdout"] = classified["security_id"].map(holdout_by_security)

    temporal_mask = (classified["statistical_weight"] > 0.0) & ~classified[
        "is_cross_sectional_holdout"
    ]
    holdout_mask = (classified["statistical_weight"] > 0.0) & classified[
        "is_cross_sectional_holdout"
    ]
    trace_mask = classified["statistical_weight"] == 0.0
    if not temporal_mask.any():
        raise PrebreakoutWalkForwardError("prebreakout_fold_temporal_objective_rows_empty")
    if not holdout_mask.any():
        raise PrebreakoutWalkForwardError("prebreakout_fold_cross_sectional_holdout_rows_empty")

    # Only positive-weight, non-holdout temporal OOS rows can enter the W5
    # tuning objective. Holdout and trace-only labels are never joined here.
    matured_objective_labels = labels[
        labels["label_status"].eq(LABEL_STATUS_MATURED)
    ][[*FEATURE_KEY_COLUMNS, "target_label"]]
    objective_rows = classified.loc[
        temporal_mask,
        [*FEATURE_KEY_COLUMNS, "forecast_score"],
    ].merge(
        matured_objective_labels,
        on=list(FEATURE_KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    if objective_rows["target_label"].isna().any():
        raise PrebreakoutWalkForwardError("prebreakout_fold_objective_label_missing")
    raw_value = None if objective_rows.empty else objective(objective_rows.copy(), fold)
    if raw_value is None:
        value: float | None = None
        objective_status = "UNINFORMATIVE"
    else:
        value = float(raw_value)
        if not isfinite(value):
            raise PrebreakoutWalkForwardError("prebreakout_development_objective_must_be_finite_or_none")
        objective_status = "INFORMATIVE"

    temporal_predictions = _prediction_records(classified.loc[temporal_mask, list(SCORE_COLUMNS)])
    holdout_predictions = _prediction_records(classified.loc[holdout_mask, list(SCORE_COLUMNS)])
    trace_predictions = _prediction_records(classified.loc[trace_mask, list(SCORE_COLUMNS)])
    if len(temporal_predictions) + len(holdout_predictions) + len(trace_predictions) != len(predictions):
        raise PrebreakoutWalkForwardError("prebreakout_fold_prediction_role_partition_invalid")

    return {
        **fold.as_dict(),
        "development_objective_status": objective_status,
        "development_objective_value": None if value is None else format(value, ".17g"),
        "prediction_sha256": prediction_sha256,
        "prediction_row_count": len(predictions),
        "training_row_count": len(training),
        "training_label_excluded_row_count": len(train_labels) - len(usable_train_labels),
        "temporal_objective_prediction_row_count": len(temporal_predictions),
        "temporal_objective_matured_label_row_count": len(objective_rows),
        "cross_sectional_holdout_row_count": len(holdout_predictions),
        "zero_weight_trace_row_count": len(trace_predictions),
        "temporal_oos_predictions": temporal_predictions,
        "cross_sectional_holdout_predictions": holdout_predictions,
        "zero_weight_trace_predictions": trace_predictions,
        "prediction_before_oos_label_join": True,
        "holdout_labels_joined": False,
        "trace_only_labels_joined": False,
    }


def _normalize_feature_frame(frame: pd.DataFrame, *, spec: WalkForwardSpec) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise PrebreakoutWalkForwardError("prebreakout_feature_frame_required")
    required = {*FEATURE_KEY_COLUMNS, *FEATURE_META_COLUMNS, *spec.feature_columns}
    if set(frame.columns) != required:
        missing = sorted(required - set(frame.columns))
        extra = sorted(set(frame.columns) - required)
        raise PrebreakoutWalkForwardError(
            "prebreakout_feature_columns_invalid:"
            f"missing={','.join(missing)};extra={','.join(extra)}"
        )
    out = frame.copy()
    out["decision_date"] = out["decision_date"].map(lambda value: _date_text(value, "decision_date"))
    out["security_id"] = out["security_id"].map(_security_id)
    out["trading_item_id"] = out["trading_item_id"].map(_trading_item_id)
    out["source_manifest_sha256"] = out["source_manifest_sha256"].map(
        lambda value: _sha256(value, "source_manifest_sha256")
    )
    out["pit_authority_sha256"] = out["pit_authority_sha256"].map(
        lambda value: _sha256(value, "pit_authority_sha256")
    )
    out["pit_risk_set_spec_id"] = out["pit_risk_set_spec_id"].map(lambda value: str(value or "").strip())
    if out["source_manifest_sha256"].nunique() != 1:
        raise PrebreakoutWalkForwardError("prebreakout_source_manifest_must_be_exactly_one")
    if out["pit_risk_set_spec_id"].ne(spec.risk_set_spec_id).any():
        raise PrebreakoutWalkForwardError("prebreakout_pit_risk_set_spec_binding_invalid")
    if (out.groupby("decision_date")["pit_authority_sha256"].nunique() != 1).any():
        raise PrebreakoutWalkForwardError("prebreakout_pit_authority_not_exactly_one_per_decision_date")
    try:
        out["statistical_weight"] = pd.to_numeric(out["statistical_weight"], errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise PrebreakoutWalkForwardError("prebreakout_statistical_weight_numeric_required") from exc
    if any(not isfinite(value) or value < 0.0 for value in out["statistical_weight"]):
        raise PrebreakoutWalkForwardError("prebreakout_statistical_weight_nonnegative_finite_required")
    if out.duplicated(list(FEATURE_KEY_COLUMNS)).any():
        raise PrebreakoutWalkForwardError("prebreakout_feature_key_duplicate")
    if not (out["statistical_weight"] > 0.0).any():
        raise PrebreakoutWalkForwardError("prebreakout_positive_statistical_weight_rows_required")
    out.sort_values(list(FEATURE_KEY_COLUMNS), inplace=True, kind="stable")
    out.reset_index(drop=True, inplace=True)
    return out


def _validate_label_schema_only(frame: pd.DataFrame) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise PrebreakoutWalkForwardError("prebreakout_label_frame_required")
    if set(frame.columns) != set(LABEL_COLUMNS):
        raise PrebreakoutWalkForwardError("prebreakout_label_columns_invalid")


def _normalize_label_frame(frame: pd.DataFrame, *, feature_keys: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["decision_date"] = out["decision_date"].map(lambda value: _date_text(value, "decision_date"))
    out["security_id"] = out["security_id"].map(_security_id)
    out["label_status"] = out["label_status"].map(lambda value: str(value or "").strip().upper())
    if not out["label_status"].isin({LABEL_STATUS_MATURED, LABEL_STATUS_INCOMPLETE}).all():
        raise PrebreakoutWalkForwardError("prebreakout_label_status_invalid")
    normalized_available: list[str | None] = []
    for value in out["label_available_date"]:
        if value is None or (isinstance(value, float) and pd.isna(value)) or not str(value).strip():
            normalized_available.append(None)
        else:
            normalized_available.append(_date_text(value, "label_available_date"))
    out["label_available_date"] = normalized_available
    numeric_labels = pd.to_numeric(out["target_label"], errors="coerce")
    matured = out["label_status"].eq(LABEL_STATUS_MATURED)
    incomplete = out["label_status"].eq(LABEL_STATUS_INCOMPLETE)
    if numeric_labels[matured].isna().any() or not numeric_labels[matured].isin([0.0, 1.0]).all():
        raise PrebreakoutWalkForwardError("prebreakout_target_label_binary_required_when_matured")
    if numeric_labels[incomplete].notna().any():
        raise PrebreakoutWalkForwardError("prebreakout_incomplete_horizon_target_label_forbidden")
    if out.loc[matured, "label_available_date"].isna().any():
        raise PrebreakoutWalkForwardError("prebreakout_matured_label_available_date_required")
    out["target_label"] = numeric_labels.astype("Int64")
    available = out["label_available_date"].notna()
    if (out.loc[available, "label_available_date"] <= out.loc[available, "decision_date"]).any():
        raise PrebreakoutWalkForwardError("prebreakout_label_must_be_available_after_decision_date")
    if out.duplicated(list(FEATURE_KEY_COLUMNS)).any():
        raise PrebreakoutWalkForwardError("prebreakout_label_key_duplicate")

    expected = set(map(tuple, feature_keys[list(FEATURE_KEY_COLUMNS)].itertuples(index=False, name=None)))
    actual = set(map(tuple, out[list(FEATURE_KEY_COLUMNS)].itertuples(index=False, name=None)))
    if actual != expected:
        raise PrebreakoutWalkForwardError("prebreakout_label_key_set_must_match_feature_key_set")
    out.sort_values(list(FEATURE_KEY_COLUMNS), inplace=True, kind="stable")
    out.reset_index(drop=True, inplace=True)
    return out


def _validate_score_frame(frame: pd.DataFrame, *, expected_keys: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise PrebreakoutWalkForwardError("prebreakout_scorer_dataframe_required")
    if set(frame.columns) != set(SCORE_COLUMNS):
        raise PrebreakoutWalkForwardError("prebreakout_scorer_output_columns_invalid")
    out = frame.copy()
    out["decision_date"] = out["decision_date"].map(lambda value: _date_text(value, "decision_date"))
    out["security_id"] = out["security_id"].map(_security_id)
    try:
        out["forecast_score"] = pd.to_numeric(out["forecast_score"], errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise PrebreakoutWalkForwardError("prebreakout_forecast_score_finite_required") from exc
    if any(not isfinite(value) for value in out["forecast_score"]):
        raise PrebreakoutWalkForwardError("prebreakout_forecast_score_finite_required")
    if out.duplicated(list(FEATURE_KEY_COLUMNS)).any():
        raise PrebreakoutWalkForwardError("prebreakout_scorer_output_key_duplicate")
    expected = set(map(tuple, expected_keys.itertuples(index=False, name=None)))
    actual = set(map(tuple, out[list(FEATURE_KEY_COLUMNS)].itertuples(index=False, name=None)))
    if actual != expected:
        raise PrebreakoutWalkForwardError("prebreakout_scorer_output_key_set_not_exact")
    out.sort_values(list(FEATURE_KEY_COLUMNS), inplace=True, kind="stable")
    out.reset_index(drop=True, inplace=True)
    return out


def _validate_holdout_feasibility(
    features: pd.DataFrame,
    *,
    holdout_by_security: dict[str, bool],
) -> None:
    positive = features.loc[features["statistical_weight"] > 0.0, "security_id"].drop_duplicates()
    holdout = [security_id for security_id in positive if holdout_by_security[security_id]]
    development = [security_id for security_id in positive if not holdout_by_security[security_id]]
    if not holdout:
        raise PrebreakoutWalkForwardError("prebreakout_cross_sectional_holdout_not_feasible")
    if not development:
        raise PrebreakoutWalkForwardError("prebreakout_cross_sectional_development_set_empty")


def _find_bound_trial_open(
    *,
    entries: Sequence[Mapping[str, Any]],
    spec: WalkForwardSpec,
    candidate: DevelopmentCandidate,
) -> dict[str, Any]:
    """Verify the persistent W2 ledger and return this candidate's open charge."""

    try:
        verify_trial_ledger(entries)
    except (TypeError, ValueError) as exc:
        raise PrebreakoutWalkForwardError("prebreakout_w2_trial_ledger_invalid") from exc

    opens = [
        dict(entry)
        for entry in entries
        if entry.get("event_type") == EVENT_OPEN
        and isinstance(entry.get("payload"), Mapping)
        and str(entry["payload"].get("trial_id") or "") == candidate.trial_id
    ]
    if len(opens) != 1:
        raise PrebreakoutWalkForwardError("prebreakout_charged_trial_open_not_exactly_one")
    if any(
        entry.get("event_type") == EVENT_CLOSE
        and isinstance(entry.get("payload"), Mapping)
        and str(entry["payload"].get("trial_id") or "") == candidate.trial_id
        for entry in entries
    ):
        raise PrebreakoutWalkForwardError("prebreakout_charged_trial_already_closed")

    opened = opens[0]
    if opened.get("family_id") != spec.family_id:
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_family_binding_invalid")
    if opened.get("search_family_id") != spec.search_family_id:
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_search_family_binding_invalid")
    if opened.get("trial_ledger_scope") != spec.trial_ledger_scope:
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_ledger_scope_binding_invalid")
    if int(opened.get("trial_budget_max", -1)) != spec.trial_budget_max:
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_budget_binding_invalid")

    payload = opened.get("payload")
    if not isinstance(payload, Mapping):  # pragma: no cover - verified above
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_payload_required")
    if str(payload.get("variant_sha256") or "") != candidate.variant_sha256:
        raise PrebreakoutWalkForwardError("prebreakout_search_charge_candidate_binding_invalid")
    variant = payload.get("variant")
    if not isinstance(variant, Mapping):  # pragma: no cover - W2 verifier owns this too
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_variant_required")
    if str(variant.get("implementation_id") or "") != candidate.implementation_id:
        raise PrebreakoutWalkForwardError("prebreakout_search_charge_candidate_binding_invalid")
    expected_variant_bindings = {
        "training_window_spec_id": spec.training_window_spec_id,
        "cross_sectional_holdout_spec_id": spec.cross_sectional_holdout_spec_id,
        "temporal_fold_plan_id": spec.walk_forward_plan_id,
    }
    for field, expected in expected_variant_bindings.items():
        if str(variant.get(field) or "") != expected:
            raise PrebreakoutWalkForwardError(f"prebreakout_trial_open_{field}_binding_invalid")
    if payload.get("outcome_access_class") != "DISCOVERY_DEVELOPMENT_ONLY":
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_outcome_access_invalid")
    if payload.get("untouched_lockbox_access") != "FORBIDDEN":
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_lockbox_access_invalid")
    if payload.get("prospective_outcome_access") != "FORBIDDEN":
        raise PrebreakoutWalkForwardError("prebreakout_trial_open_prospective_access_invalid")
    return opened


def _verify_fold_order(folds: Sequence[TemporalFold]) -> None:
    prior_oos_end: str | None = None
    for fold in folds:
        if not (
            fold.train_start_date <= fold.train_end_date
            < fold.embargo_start_date
            <= fold.embargo_end_date
            < fold.oos_start_date
            <= fold.oos_end_date
        ):
            raise PrebreakoutWalkForwardError("prebreakout_temporal_fold_order_invalid")
        if prior_oos_end is not None and fold.oos_start_date <= prior_oos_end:
            raise PrebreakoutWalkForwardError("prebreakout_oos_folds_overlap")
        prior_oos_end = fold.oos_end_date


def _prediction_records(frame: pd.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ordered = frame.loc[:, list(SCORE_COLUMNS)].sort_values(list(FEATURE_KEY_COLUMNS), kind="stable")
    for row in ordered.itertuples(index=False):
        rows.append(
            {
                "decision_date": str(row.decision_date),
                "security_id": str(row.security_id),
                "forecast_score": format(float(row.forecast_score), ".17g"),
            }
        )
    return rows


def _holdout_assignment_hash(
    *,
    holdout_by_security: dict[str, bool],
    spec: WalkForwardSpec,
) -> str:
    return domain_hash(
        "PREBREAKOUT_DISCOVERY_V1:CROSS_SECTIONAL_HOLDOUT_ASSIGNMENT",
        {
            "holdout_id": spec.cross_sectional_holdout_spec_id,
            "assignments": [
                {"security_id": security_id, "holdout": holdout_by_security[security_id]}
                for security_id in sorted(holdout_by_security)
            ],
        },
    )


def _date_text(value: Any, field: str) -> str:
    try:
        parsed = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise PrebreakoutWalkForwardError(f"prebreakout_{field}_invalid") from exc
    if pd.isna(parsed):
        raise PrebreakoutWalkForwardError(f"prebreakout_{field}_invalid")
    return parsed.date().isoformat()


def _security_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _CIQ_SECURITY_RE.fullmatch(text):
        raise PrebreakoutWalkForwardError("prebreakout_ciq_security_id_namespace_required")
    return text


def _trading_item_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _TRADING_ITEM_RE.fullmatch(text):
        raise PrebreakoutWalkForwardError("prebreakout_trading_item_id_required")
    return text


def _sha256(value: Any, field: str) -> str:
    text = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(text):
        raise PrebreakoutWalkForwardError(f"prebreakout_{field}_invalid")
    return text


def body_without_spec(body: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in body.items() if key != "spec_sha256"}


def _hash_safe(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, dict):
        return {str(key): _hash_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_hash_safe(item) for item in value]
    raise PrebreakoutWalkForwardError(
        f"prebreakout_hash_value_type_unsupported:{type(value).__name__}"
    )
