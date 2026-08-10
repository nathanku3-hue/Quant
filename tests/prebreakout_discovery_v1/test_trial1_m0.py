from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_discovery_v1 import preregistration as w2
from research.prebreakout_discovery_v1.contracts import DevelopmentCandidate, PrebreakoutWalkForwardError
from research.prebreakout_discovery_v1.trial1_m0 import (
    CALIBRATION_SPEC_ID,
    CONTROL_SPEC,
    CONTROL_SPEC_ID,
    CROSS_SECTIONAL_HOLDOUT_SPEC_ID,
    FEATURE_COLUMNS,
    FEATURE_SPEC_ID,
    IMPLEMENTATION_ID,
    MODEL_SPEC_ID,
    PRIMARY_OBJECTIVE_ID,
    PRIMARY_OBJECTIVE_SPEC,
    RANKING_SPEC_ID,
    SOURCE_AUTHORITY_CLASS,
    SOURCE_MANIFEST_SCHEMA,
    TEMPORAL_FOLD_PLAN_ID,
    TRAINING_WINDOW_SPEC_ID,
    TRIAL1_W4_CONTROL_DEFINITION_SHA256,
    TRANSFORM_SPEC_ID,
    TRIAL_ID,
    as_development_candidate,
    build_trial1_walk_forward_spec,
    compute_trial1_m0_features,
    feature_formula_contract,
    prepare_trial1_m0_for_trial_open,
    summarize_trial1_recall_lift,
    trial1_m0_fold_recall_lift_objective,
    trial1_m0_scorer,
    uncharged_trial1_declaration,
    verify_trial1_source_manifest,
)
from research.prebreakout_discovery_v1.walk_forward import build_temporal_folds, is_cross_sectional_holdout


def _source_manifest() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": SOURCE_MANIFEST_SCHEMA,
        "family_id": w2.FAMILY_ID,
        "w2_contract_sha256": w2.CONTRACT_SHA256,
        "risk_set_spec_id": w2.RISK_SET_SPEC_ID,
        "primary_label_spec_id": w2.PRIMARY_LABEL_SPEC_ID,
        "market_history_payload_sha256": domain_hash("PREBREAKOUT:T1:MARKET", {"v": 1}),
        "w3_pit_authority_bundle_sha256": domain_hash("PREBREAKOUT:T1:W3", {"v": 1}),
        "w4_control_definition_sha256": TRIAL1_W4_CONTROL_DEFINITION_SHA256,
        "w4_development_label_custody_sha256": domain_hash("PREBREAKOUT:T1:W4DEV", {"v": 1}),
        "w4_episode_custody_sha256": domain_hash("PREBREAKOUT:T1:W4EP", {"v": 1}),
        "decision_spine_sha256": domain_hash("PREBREAKOUT:T1:SPINE", {"v": 1}),
        "source_receipt_bundle_sha256": domain_hash("PREBREAKOUT:T1:RECEIPTS", {"v": 1}),
        "development_label_visibility_at_manifest": "HASHED_NOT_INSPECTED",
        "smoke_statistical_weight": 0,
        "holdout_label_tuning_authority": "FORBIDDEN",
        "w6_lockbox_included": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "authority_class": SOURCE_AUTHORITY_CLASS,
    }
    return {
        **body,
        "manifest_sha256": domain_hash(
            "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_SOURCE_MANIFEST",
            w2.hash_safe(body),
        ),
    }


def _market_rows(*, breakout_last: bool = False, near_high_last: bool = True) -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-02", periods=60)
    rows: list[dict[str, object]] = []
    for security_id, trading_item_id, mode in (
        ("CIQSEC:IQ1001", "1001", "trigger"),
        ("CIQSEC:IQ1002", "1002", "far"),
    ):
        returns = [0.02 if index % 2 == 0 else -0.02 for index in range(40)] + [
            0.005 if index % 2 == 0 else -0.005 for index in range(20)
        ]
        closes = [100.0] * 60
        volumes = [100_000.0] * 55 + [200_000.0] * 5
        if mode == "trigger":
            if breakout_last:
                closes[-1] = 101.0
            elif near_high_last:
                closes[-1] = 99.5
            else:
                closes[-1] = 90.0
        else:
            closes[-1] = 90.0
        for index, stamp in enumerate(dates):
            rows.append(
                {
                    "security_id": security_id,
                    "trading_item_id": trading_item_id,
                    "session_date": stamp.date().isoformat(),
                    "close": closes[index],
                    "total_return_1d": returns[index],
                    "volume": volumes[index],
                }
            )
    return pd.DataFrame(rows)


def test_trial1_is_frozen_uncharged_and_primary_objective_is_right_tail_then_lead() -> None:
    declaration = uncharged_trial1_declaration()
    spec = build_trial1_walk_forward_spec()

    assert declaration["trial_id"] == TRIAL_ID == "PREBREAKOUT_TRIAL_1_M0"
    assert declaration["implementation_id"] == IMPLEMENTATION_ID
    assert declaration["source_manifest_sha256"] is None
    assert declaration["trial_open_status"] == "BLOCKED_WAITING_EXACT_W3_W4_SOURCE_MANIFEST"
    assert declaration["trial_cost_if_opened"] == 1
    assert declaration["trial_budget_max"] == 8
    assert declaration["labels_may_be_inspected"] is False
    assert declaration["w6_lockbox_access"] == "FORBIDDEN"

    assert spec.training_window_spec_id == TRAINING_WINDOW_SPEC_ID
    assert spec.mode.value == "EXPANDING"
    assert spec.minimum_training_sessions == 126
    assert spec.embargo_sessions == w2.PRIMARY_HORIZON_SESSIONS == 20
    assert spec.fold_count == 4
    assert spec.oos_sessions_per_fold == 20
    assert spec.cross_sectional_holdout_spec_id == CROSS_SECTIONAL_HOLDOUT_SPEC_ID
    assert spec.holdout_modulus == 5
    assert spec.holdout_remainders == (0,)
    assert spec.feature_columns == FEATURE_COLUMNS

    assert PRIMARY_OBJECTIVE_SPEC["objective_id"] == PRIMARY_OBJECTIVE_ID
    assert "RECALL_LIFT" in str(PRIMARY_OBJECTIVE_SPEC["selection_rule"])
    assert "TTFLD" in str(PRIMARY_OBJECTIVE_SPEC["selection_rule"])
    assert PRIMARY_OBJECTIVE_SPEC["cagr_primary"] is False
    assert PRIMARY_OBJECTIVE_SPEC["sharpe_primary"] is False
    assert CONTROL_SPEC["control_spec_id"] == CONTROL_SPEC_ID
    assert CONTROL_SPEC["sampled_control_rows"] is False
    assert CONTROL_SPEC["w4_match_columns"] == ["trial1_control_stratum"]
    assert CONTROL_SPEC["w4_match_value"] == "ALL_W3_ELIGIBLE"


def test_exact_split_builds_four_oos_folds_and_holdout_is_deterministic() -> None:
    spec = build_trial1_walk_forward_spec()
    dates = pd.bdate_range("2024-01-02", periods=226).date.astype(str).tolist()
    folds = build_temporal_folds(decision_dates=dates, spec=spec)
    assert len(folds) == 4
    assert [fold.train_session_count for fold in folds] == [126, 146, 166, 186]
    assert all(fold.embargo_session_count == 20 for fold in folds)
    assert all(fold.oos_session_count == 20 for fold in folds)

    securities = [f"CIQSEC:IQ{1000 + index}" for index in range(100)]
    first = [is_cross_sectional_holdout(value, spec=spec) for value in securities]
    second = [is_cross_sectional_holdout(value, spec=spec) for value in securities]
    assert first == second
    assert 10 <= sum(first) <= 30


def test_market_only_m0_formula_is_prefit_and_blocks_post_breakout() -> None:
    features = compute_trial1_m0_features(_market_rows())
    final = features.groupby("security_id", sort=True).tail(1).set_index("security_id")
    trigger = final.loc["CIQSEC:IQ1001"]
    far = final.loc["CIQSEC:IQ1002"]

    assert trigger["feature_status"] == "READY"
    assert trigger["prebreakout_trigger"] is True or bool(trigger["prebreakout_trigger"]) is True
    assert 0.0 < float(trigger["near_high_component"]) <= 1.0
    assert 0.0 < float(trigger["vol_compression_component"]) <= 1.0
    assert 0.0 < float(trigger["volume_pressure_component"]) <= 1.0
    assert float(trigger["forecast_score"]) > 0.0

    assert bool(far["prebreakout_trigger"]) is False
    assert float(far["forecast_score"]) == 0.0

    breakout = compute_trial1_m0_features(_market_rows(breakout_last=True))
    breakout_final = breakout[breakout["security_id"] == "CIQSEC:IQ1001"].iloc[-1]
    assert bool(breakout_final["prebreakout_trigger"]) is False
    assert float(breakout_final["forecast_score"]) == 0.0

    formula = feature_formula_contract()
    assert formula["fit_parameters"] == 0
    assert formula["calibration"] == "NONE"
    assert formula["market_inputs"] == ["market.close", "market.total_return_1d", "market.volume"]


def test_provider_missing_total_return_abstains_locally_without_imputation_or_frame_abort() -> None:
    market = _market_rows()
    missing_mask = market["security_id"].eq("CIQSEC:IQ1001") & market["session_date"].eq(
        market.loc[market["security_id"].eq("CIQSEC:IQ1001"), "session_date"].iloc[-1]
    )
    market.loc[missing_mask, "total_return_1d"] = float("nan")

    features = compute_trial1_m0_features(market)
    final = features.groupby("security_id", sort=True).tail(1).set_index("security_id")
    missing = final.loc["CIQSEC:IQ1001"]
    complete = final.loc["CIQSEC:IQ1002"]

    assert missing["feature_status"] == "INSUFFICIENT_OR_INVALID_MARKET_HISTORY"
    assert bool(missing["prebreakout_trigger"]) is False
    assert float(missing["forecast_score"]) == 0.0
    assert pd.isna(missing["total_return_1d"])
    assert complete["feature_status"] == "READY"

    malformed = _market_rows()
    malformed.loc[0, "total_return_1d"] = float("inf")
    with pytest.raises(PrebreakoutWalkForwardError, match="total_return_1d_finite_required"):
        compute_trial1_m0_features(malformed)


def test_market_features_are_exact_listing_local_when_one_security_changes_trading_item() -> None:
    base = _market_rows()
    second_listing = base[base["security_id"].eq("CIQSEC:IQ1001")].copy()
    second_listing["trading_item_id"] = "2001"
    second_listing["close"] = second_listing["close"] * 2.0
    features = compute_trial1_m0_features(pd.concat([base, second_listing], ignore_index=True))
    assert len(features) == len(base) + len(second_listing)
    counts = features.groupby(["security_id", "trading_item_id"])["session_date"].nunique()
    assert counts.loc[("CIQSEC:IQ1001", "1001")] == 60
    assert counts.loc[("CIQSEC:IQ1001", "2001")] == 60

    duplicate = pd.concat([base, base.iloc[[0]]], ignore_index=True)
    with pytest.raises(PrebreakoutWalkForwardError, match="duplicate_exact_listing_session"):
        compute_trial1_m0_features(duplicate)


def test_fold_recall_lift_objective_and_null_aggregate_follow_frozen_law() -> None:
    fold = build_temporal_folds(
        decision_dates=pd.bdate_range("2024-01-02", periods=226).date.astype(str).tolist(),
        spec=build_trial1_walk_forward_spec(),
    )[0]
    rows = pd.DataFrame(
        [
            {"decision_date": "2026-01-02", "security_id": "CIQSEC:IQ1", "forecast_score": 1.0, "target_label": 1},
            {"decision_date": "2026-01-02", "security_id": "CIQSEC:IQ2", "forecast_score": 0.0, "target_label": 0},
            {"decision_date": "2026-01-02", "security_id": "CIQSEC:IQ3", "forecast_score": 0.0, "target_label": 0},
            {"decision_date": "2026-01-02", "security_id": "CIQSEC:IQ4", "forecast_score": 0.0, "target_label": 0},
        ]
    )
    assert trial1_m0_fold_recall_lift_objective(rows, fold) == pytest.approx(4.0)
    no_flags = rows.copy()
    no_flags["forecast_score"] = 0.0
    assert trial1_m0_fold_recall_lift_objective(no_flags, fold) is None

    run = {
        "development_objective_id": PRIMARY_OBJECTIVE_ID,
        "folds": [
            {"development_objective_status": "INFORMATIVE", "development_objective_value": "1.5"},
            {"development_objective_status": "UNINFORMATIVE", "development_objective_value": None},
            {"development_objective_status": "INFORMATIVE", "development_objective_value": "2.5"},
            {"development_objective_status": "INFORMATIVE", "development_objective_value": "3.5"},
        ],
    }
    summary = summarize_trial1_recall_lift(run)
    assert summary["status"] == "INFORMATIVE"
    assert summary["informative_fold_count"] == 3
    assert float(summary["median_temporal_oos_recall_lift"]) == pytest.approx(2.5)

    null_run = {
        "development_objective_id": PRIMARY_OBJECTIVE_ID,
        "folds": [
            {"development_objective_status": "UNINFORMATIVE", "development_objective_value": None},
            {"development_objective_status": "UNINFORMATIVE", "development_objective_value": None},
            {"development_objective_status": "INFORMATIVE", "development_objective_value": "2.5"},
            {"development_objective_status": "UNINFORMATIVE", "development_objective_value": None},
        ],
    }
    assert summarize_trial1_recall_lift(null_run)["status"] == "NULL"


def test_scorer_ignores_training_labels_and_only_uses_frozen_components() -> None:
    features = compute_trial1_m0_features(_market_rows())
    last = features.groupby("security_id", sort=True).tail(1).copy()
    score_source = last[
        ["session_date", "security_id", "trading_item_id", *FEATURE_COLUMNS]
    ].rename(columns={"session_date": "decision_date"})
    candidate = DevelopmentCandidate(
        trial_id=TRIAL_ID,
        implementation_id=IMPLEMENTATION_ID,
        variant_sha256="a" * 64,
    )
    fold = build_temporal_folds(
        decision_dates=pd.bdate_range("2024-01-02", periods=226).date.astype(str).tolist(),
        spec=build_trial1_walk_forward_spec(),
    )[0]
    training_a = pd.DataFrame(
        {"decision_date": ["2025-01-02"], "security_id": ["CIQSEC:IQ9999"], "target_label": [0]}
    )
    training_b = training_a.copy()
    training_b["target_label"] = 1
    first = trial1_m0_scorer(candidate, training_a, score_source, fold)
    second = trial1_m0_scorer(candidate, training_b, score_source, fold)
    pd.testing.assert_frame_equal(first, second)
    assert float(first.loc[first["security_id"] == "CIQSEC:IQ1001", "forecast_score"].iloc[0]) > 0.0


def test_trial_open_preparation_requires_exact_source_manifest_and_does_not_charge(tmp_path: Path) -> None:
    declaration = uncharged_trial1_declaration()
    assert declaration["source_manifest_sha256"] is None
    assert list(tmp_path.iterdir()) == []

    with pytest.raises(PrebreakoutWalkForwardError, match="source_manifest_mapping_required"):
        prepare_trial1_m0_for_trial_open(source_manifest=None, code_sha256="b" * 64)  # type: ignore[arg-type]

    manifest = _source_manifest()
    prepared = prepare_trial1_m0_for_trial_open(source_manifest=manifest, code_sha256="b" * 64)
    verify_trial1_source_manifest(manifest)
    assert prepared.trial_open_appended is False
    assert prepared.trial_cost == 1
    assert prepared.source_manifest_sha256 == manifest["manifest_sha256"]
    assert prepared.variant == {
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
        "source_manifest_sha256": manifest["manifest_sha256"],
        "code_sha256": "b" * 64,
    }
    assert prepared.variant_sha256 == domain_hash(
        "PREBREAKOUT_DISCOVERY_V1:TRIAL_VARIANT",
        w2.hash_safe(prepared.variant),
    )
    candidate = as_development_candidate(prepared)
    assert candidate.trial_id == TRIAL_ID
    assert list(tmp_path.iterdir()) == []


def test_source_manifest_rejects_label_peek_holdout_tuning_w6_or_hash_drift() -> None:
    manifest = _source_manifest()

    peeked = deepcopy(manifest)
    peeked["development_label_visibility_at_manifest"] = "INSPECTED"
    with pytest.raises(PrebreakoutWalkForwardError, match="label_visibility_invalid"):
        verify_trial1_source_manifest(peeked)

    holdout = deepcopy(manifest)
    holdout["holdout_label_tuning_authority"] = "ALLOWED"
    with pytest.raises(PrebreakoutWalkForwardError, match="holdout_tuning_invalid"):
        verify_trial1_source_manifest(holdout)

    w6 = deepcopy(manifest)
    w6["w6_lockbox_included"] = True
    with pytest.raises(PrebreakoutWalkForwardError, match="w6_forbidden"):
        verify_trial1_source_manifest(w6)

    control = deepcopy(manifest)
    control["w4_control_definition_sha256"] = "d" * 64
    with pytest.raises(PrebreakoutWalkForwardError, match="control_definition_invalid"):
        verify_trial1_source_manifest(control)

    tampered = deepcopy(manifest)
    tampered["market_history_payload_sha256"] = "c" * 64
    with pytest.raises(PrebreakoutWalkForwardError, match="hash_mismatch"):
        verify_trial1_source_manifest(tampered)


def test_trial1_core_has_no_named_smoke_branch_or_nonmarket_feature_surface() -> None:
    text = Path("research/prebreakout_discovery_v1/trial1_m0.py").read_text(encoding="utf-8")
    assert '"MU"' not in text
    assert '"SNDK"' not in text
    forbidden_feature_tokens = (
        "fund.revenue",
        "gross_margin",
        "cash_from_ops",
        "sector_map",
        "submit_order",
        "w6_lockbox_payload",
    )
    assert not any(token in text for token in forbidden_feature_tokens)

    extra = _market_rows()
    extra["ticker"] = "SHOULD_FAIL"
    with pytest.raises(PrebreakoutWalkForwardError, match="market_history_columns_invalid"):
        compute_trial1_m0_features(extra)
