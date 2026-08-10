from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_discovery_v1 import (
    FAMILY_ID,
    DevelopmentCandidate,
    PrebreakoutWalkForwardError,
    WalkForwardMode,
    WalkForwardSpec,
    build_temporal_folds,
    is_cross_sectional_holdout,
    run_charged_development_candidate,
)
from research.prebreakout_discovery_v1 import preregistration as w2
from research.prebreakout_discovery_v1.ledger import (
    append_trial_close,
    append_trial_open,
    load_trial_ledger,
)


BASE = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
SOURCE_MANIFEST_SHA256 = domain_hash("PREBREAKOUT:W5:FIXTURE:SOURCE_MANIFEST", {"v": 1})


def _spec(*, mode: WalkForwardMode = WalkForwardMode.EXPANDING) -> WalkForwardSpec:
    return WalkForwardSpec(
        walk_forward_plan_id="FOUR_TEMPORAL_OOS_FOLDS_WHERE_LEGITIMATE_V1",
        training_window_spec_id=(
            "EXPANDING_WALK_FORWARD_V1"
            if mode is WalkForwardMode.EXPANDING
            else "ROLLING_24_SESSION_WALK_FORWARD_V1"
        ),
        cross_sectional_holdout_spec_id="HASH_BUCKET_HOLDOUT_V1",
        development_objective_id="MECHANISM_RIGHT_TAIL_FIXTURE_SCORE_v1",
        family_id=w2.FAMILY_ID,
        risk_set_spec_id=w2.RISK_SET_SPEC_ID,
        primary_label_spec_id=w2.PRIMARY_LABEL_SPEC_ID,
        primary_horizon_sessions=w2.PRIMARY_HORIZON_SESSIONS,
        search_family_id=w2.SEARCH_FAMILY_ID,
        trial_ledger_scope=w2.TRIAL_LEDGER_SCOPE,
        trial_budget_max=w2.TRIAL_BUDGET_MAX,
        mode=mode,
        fold_count=4,
        minimum_training_sessions=24,
        rolling_training_sessions=24 if mode is WalkForwardMode.ROLLING else None,
        embargo_sessions=w2.PRIMARY_HORIZON_SESSIONS,
        oos_sessions_per_fold=3,
        feature_columns=("signal", "falsifier_distance"),
        holdout_seed="prebreakout-w5-fixture-seed",
        holdout_modulus=4,
        holdout_remainders=(0,),
    )


def _variant(spec: WalkForwardSpec, index: int, **overrides: str) -> dict[str, str]:
    variant = {
        "implementation_id": f"PREBREAKOUT_W5_DEV_{index:02d}",
        "feature_spec_id": "PREBREAKOUT_W5_FIXTURE_FEATURES_V1",
        "transform_spec_id": "PREBREAKOUT_W5_FIXTURE_TRANSFORMS_V1",
        "model_spec_id": f"PREBREAKOUT_W5_FIXTURE_MODEL_{index:02d}",
        "training_window_spec_id": spec.training_window_spec_id,
        "calibration_spec_id": "NO_CALIBRATION_V1",
        "ranking_spec_id": "DATE_LOCAL_RANK_V1",
        "control_spec_id": "BREADTH_MATCHED_CONTROL_V1",
        "cross_sectional_holdout_spec_id": spec.cross_sectional_holdout_spec_id,
        "temporal_fold_plan_id": spec.walk_forward_plan_id,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "code_sha256": f"{index + 101:064x}",
    }
    variant.update(overrides)
    return variant


def _open_trial(
    ledger_path: Path,
    *,
    spec: WalkForwardSpec,
    index: int = 1,
    variant_overrides: dict[str, str] | None = None,
) -> tuple[DevelopmentCandidate, list[dict[str, object]], dict[str, object]]:
    variant = _variant(spec, index, **(variant_overrides or {}))
    opened = append_trial_open(
        ledger_path,
        trial_id=f"w5-trial-{index:02d}",
        variant=variant,
        recorded_at=BASE + timedelta(seconds=index),
    )
    candidate = DevelopmentCandidate(
        trial_id=f"w5-trial-{index:02d}",
        implementation_id=variant["implementation_id"],
        variant_sha256=str(opened["payload"]["variant_sha256"]),
    )
    return candidate, load_trial_ledger(ledger_path), opened


def _frames(spec: WalkForwardSpec) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2025-12-01", periods=76)
    security_ids = [f"CIQSEC:IQ{1000 + index}" for index in range(24)]
    positive_holdout = [
        security_id for security_id in security_ids if is_cross_sectional_holdout(security_id, spec=spec)
    ]
    positive_development = [
        security_id for security_id in security_ids if not is_cross_sectional_holdout(security_id, spec=spec)
    ]
    assert positive_holdout and positive_development

    trace_only_id = positive_development[-1]
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    for date_index, stamp in enumerate(dates):
        decision_date = stamp.date().isoformat()
        available_date = (stamp + pd.offsets.BDay(spec.primary_horizon_sessions)).date().isoformat()
        pit_authority_sha256 = domain_hash(
            "PREBREAKOUT:W5:FIXTURE:PIT_AUTHORITY",
            {"decision_date": decision_date, "risk_set_spec_id": spec.risk_set_spec_id},
        )
        for security_index, security_id in enumerate(security_ids):
            feature_rows.append(
                {
                    "decision_date": decision_date,
                    "security_id": security_id,
                    "trading_item_id": str(1000 + security_index),
                    "statistical_weight": 0.0 if security_id == trace_only_id else 1.0,
                    "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
                    "pit_authority_sha256": pit_authority_sha256,
                    "pit_risk_set_spec_id": spec.risk_set_spec_id,
                    "signal": float(date_index) / 100.0 + float(security_index) / 1000.0,
                    "falsifier_distance": float((security_index % 5) - 2),
                }
            )
            label_rows.append(
                {
                    "decision_date": decision_date,
                    "security_id": security_id,
                    "target_label": int((date_index + security_index) % 5 == 0),
                    "label_available_date": available_date,
                    "label_status": "MATURED",
                }
            )
    return pd.DataFrame(feature_rows), pd.DataFrame(label_rows)


def _scorer_with_audit(audit: dict[str, object]):
    def scorer(candidate, training, score_source, fold):
        assert candidate.trial_id
        assert "target_label" in training.columns
        assert "target_label" not in score_source.columns
        assert "label_available_date" not in score_source.columns
        assert "statistical_weight" not in training.columns
        assert "statistical_weight" not in score_source.columns
        assert "source_manifest_sha256" not in training.columns
        assert "source_manifest_sha256" not in score_source.columns
        assert "pit_authority_sha256" not in training.columns
        assert "pit_authority_sha256" not in score_source.columns
        assert "pit_risk_set_spec_id" not in training.columns
        assert "pit_risk_set_spec_id" not in score_source.columns
        audit.setdefault("train_ids", []).append(set(training["security_id"]))
        audit.setdefault("score_columns", []).append(tuple(score_source.columns))
        return pd.DataFrame(
            {
                "decision_date": score_source["decision_date"],
                "security_id": score_source["security_id"],
                "forecast_score": score_source["signal"] - 0.01 * score_source["falsifier_distance"],
            }
        )

    return scorer


def _objective_with_audit(audit: dict[str, object]):
    def objective(rows, fold):
        assert list(rows.columns) == ["decision_date", "security_id", "forecast_score", "target_label"]
        audit.setdefault("objective_ids", []).append(set(rows["security_id"]))
        signed = rows["target_label"].map({0: -1.0, 1: 1.0})
        return float((rows["forecast_score"] * signed).mean())

    return objective


def _charged_run(
    *,
    ledger_path: Path,
    spec: WalkForwardSpec,
    features: pd.DataFrame,
    labels: pd.DataFrame,
    index: int = 1,
    audit: dict[str, object] | None = None,
):
    candidate, ledger_entries, opened = _open_trial(ledger_path, spec=spec, index=index)
    audit = {} if audit is None else audit
    run = run_charged_development_candidate(
        feature_frame=features,
        label_frame=labels,
        spec=spec,
        candidate=candidate,
        trial_ledger_entries=ledger_entries,
        scorer=_scorer_with_audit(audit),
        objective=_objective_with_audit(audit),
    )
    return run, candidate, ledger_entries, opened, audit


def test_expanding_plan_has_four_temporal_oos_folds_with_frozen_primary_horizon_embargo() -> None:
    spec = _spec(mode=WalkForwardMode.EXPANDING)
    features, _ = _frames(spec)
    folds = build_temporal_folds(decision_dates=features["decision_date"], spec=spec)

    assert FAMILY_ID == w2.FAMILY_ID
    assert spec.primary_horizon_sessions == w2.PRIMARY_HORIZON_SESSIONS == 20
    assert spec.trial_budget_max == w2.TRIAL_BUDGET_MAX == 8
    assert len(folds) == 4
    assert [fold.train_session_count for fold in folds] == [24, 27, 30, 33]
    assert all(fold.embargo_session_count == w2.PRIMARY_HORIZON_SESSIONS for fold in folds)
    assert all(fold.oos_session_count == 3 for fold in folds)
    assert all(left.oos_end_date < right.oos_start_date for left, right in zip(folds, folds[1:]))


def test_rolling_plan_keeps_fixed_training_window_and_insufficient_history_fails_closed() -> None:
    spec = _spec(mode=WalkForwardMode.ROLLING)
    features, _ = _frames(spec)
    folds = build_temporal_folds(decision_dates=features["decision_date"], spec=spec)
    assert len(folds) == 4
    assert [fold.train_session_count for fold in folds] == [24, 24, 24, 24]
    assert folds[0].train_start_date < folds[1].train_start_date < folds[2].train_start_date

    too_short = sorted(features["decision_date"].unique())[:50]
    with pytest.raises(PrebreakoutWalkForwardError, match="insufficient_sessions_for_requested_walk_forward"):
        build_temporal_folds(decision_dates=too_short, spec=spec)


def test_holdout_never_fits_or_tunes_and_zero_weight_smoke_rows_are_trace_only(tmp_path: Path) -> None:
    spec = _spec()
    features, labels = _frames(spec)
    audit: dict[str, object] = {}
    run, _, _, opened, audit = _charged_run(
        ledger_path=tmp_path / "w5-ledger.jsonl",
        spec=spec,
        features=features,
        labels=labels,
        audit=audit,
    )

    positive_ids = set(features.loc[features["statistical_weight"] > 0.0, "security_id"])
    holdout_ids = {
        security_id for security_id in positive_ids if is_cross_sectional_holdout(security_id, spec=spec)
    }
    trace_ids = set(features.loc[features["statistical_weight"] == 0.0, "security_id"])
    assert holdout_ids
    assert trace_ids
    for train_ids in audit["train_ids"]:
        assert not (train_ids & holdout_ids)
        assert not (train_ids & trace_ids)
    for objective_ids in audit["objective_ids"]:
        assert not (objective_ids & holdout_ids)
        assert not (objective_ids & trace_ids)

    assert run["fold_count"] == 4
    assert run["search_charge"] == opened
    assert run["development_source_manifest_sha256"] == SOURCE_MANIFEST_SHA256
    assert run["pit_risk_set_spec_id"] == w2.RISK_SET_SPEC_ID
    assert len(run["pit_authority_sha256s"]) == features["decision_date"].nunique()
    assert run["cross_sectional_holdout_labels_used_by_search"] is False
    assert run["zero_weight_trace_rows_used_by_search"] is False
    assert run["financial_alpha_evidence"] == 0
    assert run["capital_authority"] == "NONE"
    assert all(fold["cross_sectional_holdout_row_count"] > 0 for fold in run["folds"])
    assert all(fold["zero_weight_trace_row_count"] > 0 for fold in run["folds"])


def test_poisoning_holdout_and_trace_labels_cannot_change_search_result(tmp_path: Path) -> None:
    spec = _spec()
    features, labels = _frames(spec)
    first, *_ = _charged_run(
        ledger_path=tmp_path / "first.jsonl",
        spec=spec,
        features=features,
        labels=labels,
    )

    poisoned = labels.copy()
    weight_by_key = features.set_index(["decision_date", "security_id"])["statistical_weight"]
    for index, row in poisoned.iterrows():
        key = (row["decision_date"], row["security_id"])
        is_holdout = is_cross_sectional_holdout(str(row["security_id"]), spec=spec)
        is_trace = float(weight_by_key.loc[key]) == 0.0
        if is_holdout or is_trace:
            poisoned.at[index, "target_label"] = 1 - int(row["target_label"])

    second, *_ = _charged_run(
        ledger_path=tmp_path / "second.jsonl",
        spec=spec,
        features=features,
        labels=poisoned,
    )
    assert second == first


def test_prediction_precedes_oos_label_join_and_late_training_label_is_excluded(tmp_path: Path) -> None:
    spec = _spec()
    features, labels = _frames(spec)
    folds = build_temporal_folds(decision_dates=features["decision_date"], spec=spec)
    first_fold = folds[0]

    bad = labels.copy()
    mask = bad["decision_date"] == first_fold.train_end_date
    bad.loc[mask, "label_available_date"] = first_fold.oos_start_date

    candidate, entries, _ = _open_trial(tmp_path / "w5-ledger.jsonl", spec=spec)
    audit: dict[str, object] = {}
    run = run_charged_development_candidate(
        feature_frame=features,
        label_frame=bad,
        spec=spec,
        candidate=candidate,
        trial_ledger_entries=entries,
        scorer=_scorer_with_audit(audit),
        objective=_objective_with_audit(audit),
    )
    assert len(audit["score_columns"]) == 4
    assert run["folds"][0]["training_label_excluded_row_count"] > 0


def test_incomplete_horizon_labels_are_never_imputed_into_objective(tmp_path: Path) -> None:
    spec = _spec()
    features, labels = _frames(spec)
    folds = build_temporal_folds(decision_dates=features["decision_date"], spec=spec)
    target_date = folds[0].oos_start_date
    mask = labels["decision_date"].eq(target_date)
    labels.loc[mask, "target_label"] = None
    labels.loc[mask, "label_status"] = "INCOMPLETE_HORIZON"

    candidate, entries, _ = _open_trial(tmp_path / "incomplete.jsonl", spec=spec)
    audit: dict[str, object] = {}
    run = run_charged_development_candidate(
        feature_frame=features,
        label_frame=labels,
        spec=spec,
        candidate=candidate,
        trial_ledger_entries=entries,
        scorer=_scorer_with_audit(audit),
        objective=_objective_with_audit(audit),
    )
    first = run["folds"][0]
    assert first["temporal_objective_matured_label_row_count"] < first["temporal_objective_prediction_row_count"]


def test_w2_trial_open_must_bind_candidate_and_w5_plan_before_label_values_are_read(tmp_path: Path) -> None:
    spec = _spec()
    features, labels = _frames(spec)
    candidate, entries, _ = _open_trial(tmp_path / "charge.jsonl", spec=spec)

    poisoned = deepcopy(labels)
    poisoned["target_label"] = poisoned["target_label"].astype(object)
    poisoned.loc[:, "target_label"] = "OUTCOME_VALUES_MUST_NOT_BE_READ"
    impostor = DevelopmentCandidate(
        trial_id=candidate.trial_id,
        implementation_id=candidate.implementation_id,
        variant_sha256=domain_hash("PREBREAKOUT:W5:IMPOSTOR", {"v": 1}),
    )
    with pytest.raises(PrebreakoutWalkForwardError, match="search_charge_candidate_binding_invalid"):
        run_charged_development_candidate(
            feature_frame=features,
            label_frame=poisoned,
            spec=spec,
            candidate=impostor,
            trial_ledger_entries=entries,
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )

    wrong_candidate, wrong_entries, _ = _open_trial(
        tmp_path / "wrong-plan.jsonl",
        spec=spec,
        index=2,
        variant_overrides={"cross_sectional_holdout_spec_id": "OTHER_HOLDOUT_V1"},
    )
    with pytest.raises(PrebreakoutWalkForwardError, match="cross_sectional_holdout_spec_id_binding_invalid"):
        run_charged_development_candidate(
            feature_frame=features,
            label_frame=labels,
            spec=spec,
            candidate=wrong_candidate,
            trial_ledger_entries=wrong_entries,
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )

    source_candidate, source_entries, _ = _open_trial(
        tmp_path / "wrong-source.jsonl",
        spec=spec,
        index=3,
        variant_overrides={"source_manifest_sha256": "a" * 64},
    )
    with pytest.raises(PrebreakoutWalkForwardError, match="source_manifest_binding_invalid"):
        run_charged_development_candidate(
            feature_frame=features,
            label_frame=poisoned,
            spec=spec,
            candidate=source_candidate,
            trial_ledger_entries=source_entries,
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )


def test_closed_trial_noncanonical_identity_and_w2_contract_drift_fail_closed(tmp_path: Path) -> None:
    spec = _spec()
    features, labels = _frames(spec)
    ledger_path = tmp_path / "closed.jsonl"
    candidate, _, _ = _open_trial(ledger_path, spec=spec)
    append_trial_close(
        ledger_path,
        trial_id=candidate.trial_id,
        result_status="ABORTED",
        result_artifact_sha256="f" * 64,
        result_summary={"reason": "fixture-close-before-run"},
        recorded_at=BASE + timedelta(seconds=20),
    )
    with pytest.raises(PrebreakoutWalkForwardError, match="charged_trial_already_closed"):
        run_charged_development_candidate(
            feature_frame=features,
            label_frame=labels,
            spec=spec,
            candidate=candidate,
            trial_ledger_entries=load_trial_ledger(ledger_path),
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )

    with pytest.raises(PrebreakoutWalkForwardError, match="w2_primary_horizon_mismatch"):
        replace(spec, primary_horizon_sessions=w2.SECONDARY_HORIZON_SESSIONS)
    with pytest.raises(PrebreakoutWalkForwardError, match="economic_primary_search_objective_forbidden"):
        replace(spec, development_objective_id="SHARPE_SEARCH_IS_FORBIDDEN")

    open_candidate, open_entries, _ = _open_trial(tmp_path / "identity.jsonl", spec=spec, index=4)
    bad_features = features.copy()
    bad_features.loc[0, "security_id"] = "AAPL"
    with pytest.raises(PrebreakoutWalkForwardError, match="ciq_security_id_namespace_required"):
        run_charged_development_candidate(
            feature_frame=bad_features,
            label_frame=labels,
            spec=spec,
            candidate=open_candidate,
            trial_ledger_entries=open_entries,
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )

    bad_trading_item = features.copy()
    bad_trading_item.loc[0, "trading_item_id"] = "SPT1000"
    with pytest.raises(PrebreakoutWalkForwardError, match="trading_item_id_required"):
        run_charged_development_candidate(
            feature_frame=bad_trading_item,
            label_frame=labels,
            spec=spec,
            candidate=open_candidate,
            trial_ledger_entries=open_entries,
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )

    bad_risk_set = features.copy()
    bad_risk_set.loc[0, "pit_risk_set_spec_id"] = "CURRENT_SURVIVOR_SUBSTITUTE_FORBIDDEN"
    with pytest.raises(PrebreakoutWalkForwardError, match="pit_risk_set_spec_binding_invalid"):
        run_charged_development_candidate(
            feature_frame=bad_risk_set,
            label_frame=labels,
            spec=spec,
            candidate=open_candidate,
            trial_ledger_entries=open_entries,
            scorer=lambda *args: pd.DataFrame(),
            objective=lambda rows, fold: 0.0,
        )
