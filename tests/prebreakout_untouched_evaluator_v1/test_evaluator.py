from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_untouched_evaluator_v1 import (
    LABEL_ROW_SCHEMA,
    PREDICTION_ROW_SCHEMA,
    UTILITY_ROW_SCHEMA,
    ZERO_WEIGHT_REASON,
    UntouchedEvaluationContractError,
    build_evaluation_contract,
    build_label_open_record,
    build_prediction_freeze_record,
    evaluate_untouched_lockboxes,
    identity_key,
    verify_evaluation_report,
)


FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
IMPLEMENTATION_ID = "PREBREAKOUT_FIXTURE_IMPL_v1"
LABEL_SPEC_ID = "PREBREAKOUT_BREAKOUT_EPISODE_v1"
LOCKBOX_ID = "LOCKBOX_2026Q1_FIXTURE"


def _sha(domain: str) -> str:
    return domain_hash("PREBREAKOUT_W6_TEST", {"domain": domain})


def _contract(*, lockbox_ids=(LOCKBOX_ID,)) -> dict[str, object]:
    return build_evaluation_contract(
        family_id=FAMILY_ID,
        implementation_id=IMPLEMENTATION_ID,
        primary_label_spec_id=LABEL_SPEC_ID,
        lockbox_ids=lockbox_ids,
        k_values=(1, 2),
        min_legitimate_lead_sessions=1,
        zero_weight_identity_keys=(identity_key("CIQSEC:404", "SPT404"),),
        prediction_ledger_sha256=_sha("prediction-ledger"),
        implementation_manifest_sha256=_sha("implementation-manifest"),
        search_ledger_sha256=_sha("search-ledger"),
        evaluator_code_sha256=_sha("evaluator-code"),
    )


def _fixture_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    predictions: list[dict[str, object]] = []
    labels: list[dict[str, object]] = []
    identities = (
        ("CIQSEC:101", "SPT101", "EP_WIN_DETECTED", True, False, 2.0, 13, "2026-01-06"),
        ("CIQSEC:202", "SPT202", "EP_WIN_MISSED", True, False, 3.0, 13, "2026-01-06"),
        ("CIQSEC:303", "SPT303", "EP_FALSE_CATA", False, True, 0.0, None, None),
        ("CIQSEC:404", "SPT404", "EP_SMOKE", False, False, 0.0, None, None),
    )
    scores = {
        10: {"CIQSEC:101": 0.90, "CIQSEC:202": 0.80, "CIQSEC:303": 0.10, "CIQSEC:404": 1.00},
        11: {"CIQSEC:101": 0.95, "CIQSEC:202": 0.70, "CIQSEC:303": 0.20, "CIQSEC:404": 1.00},
        12: {"CIQSEC:101": 0.90, "CIQSEC:202": 0.10, "CIQSEC:303": 0.99, "CIQSEC:404": 1.00},
    }
    session_dates = {10: "2026-01-02", 11: "2026-01-05", 12: "2026-01-06"}
    made_times = {
        10: "2026-01-02T21:00:01.000000Z",
        11: "2026-01-05T21:00:01.000000Z",
        12: "2026-01-06T21:00:01.000000Z",
    }
    recorded_times = {
        10: "2026-01-02T21:00:02.000000Z",
        11: "2026-01-05T21:00:02.000000Z",
        12: "2026-01-06T21:00:02.000000Z",
    }
    for ordinal in (10, 11, 12):
        for security_id, trading_item_id, episode_id, winner, catastrophic, wealth, breakout_ordinal, breakout_date in identities:
            zero = security_id == "CIQSEC:404"
            if security_id == "CIQSEC:101":
                flagged = ordinal >= 11
                eligibility = "ELIGIBLE"
                exclusion_reason = None
            elif security_id == "CIQSEC:202":
                flagged = False
                eligibility = "EXCLUDED" if ordinal == 12 else "ELIGIBLE"
                exclusion_reason = "PIT_REQUIRED_FEATURE_UNAVAILABLE" if ordinal == 12 else None
            elif security_id == "CIQSEC:303":
                flagged = ordinal == 12
                eligibility = "ELIGIBLE"
                exclusion_reason = None
            else:
                flagged = True
                eligibility = "ELIGIBLE"
                exclusion_reason = None
            predictions.append(
                {
                    "schema_version": PREDICTION_ROW_SCHEMA,
                    "family_id": FAMILY_ID,
                    "implementation_id": IMPLEMENTATION_ID,
                    "lockbox_id": LOCKBOX_ID,
                    "prediction_id": _sha(f"prediction:{ordinal}:{security_id}"),
                    "decision_context_id": f"CTX_{ordinal}",
                    "decision_session_date": session_dates[ordinal],
                    "decision_session_ordinal": ordinal,
                    "decision_listing_session_ordinal": ordinal,
                    "security_id": security_id,
                    "trading_item_id": trading_item_id,
                    "score": scores[ordinal][security_id],
                    "flagged": flagged,
                    "eligibility_status": eligibility,
                    "exclusion_reason": exclusion_reason,
                    "knowledge_cutoff": session_dates[ordinal] + "T20:59:00.000000Z",
                    "prediction_made_at": made_times[ordinal],
                    "prediction_recorded_at": recorded_times[ordinal],
                    "statistical_weight": 0 if zero else 1,
                    "zero_weight_reason": ZERO_WEIGHT_REASON if zero else None,
                }
            )
            labels.append(
                {
                    "schema_version": LABEL_ROW_SCHEMA,
                    "family_id": FAMILY_ID,
                    "implementation_id": IMPLEMENTATION_ID,
                    "label_spec_id": LABEL_SPEC_ID,
                    "lockbox_id": LOCKBOX_ID,
                    "decision_session_date": session_dates[ordinal],
                    "decision_session_ordinal": ordinal,
                    "decision_listing_session_ordinal": ordinal,
                    "security_id": security_id,
                    "trading_item_id": trading_item_id,
                    "winner_label": winner,
                    "catastrophic_outcome_label": catastrophic,
                    "realized_total_return": 1.0 if security_id == "CIQSEC:101" else (0.8 if security_id == "CIQSEC:202" else (-0.7 if catastrophic else 0.0)),
                    "right_tail_wealth": wealth,
                    "effective_episode_id": episode_id,
                    "breakout_session_date": breakout_date,
                    "breakout_session_ordinal": breakout_ordinal,
                    "breakout_listing_session_ordinal": breakout_ordinal,
                    "statistical_weight": 0 if zero else 1,
                    "zero_weight_reason": ZERO_WEIGHT_REASON if zero else None,
                }
            )
    utilities = [
        {
            "schema_version": UTILITY_ROW_SCHEMA,
            "family_id": FAMILY_ID,
            "implementation_id": IMPLEMENTATION_ID,
            "lockbox_id": LOCKBOX_ID,
            "evaluation_period_id": "PERIOD_1",
            "incumbent_net_utility": 0.10,
            "incumbent_plus_candidate_net_utility": 0.15,
        },
        {
            "schema_version": UTILITY_ROW_SCHEMA,
            "family_id": FAMILY_ID,
            "implementation_id": IMPLEMENTATION_ID,
            "lockbox_id": LOCKBOX_ID,
            "evaluation_period_id": "PERIOD_2",
            "incumbent_net_utility": 0.20,
            "incumbent_plus_candidate_net_utility": 0.10,
        },
    ]
    return predictions, labels, utilities


def _custody(
    contract: dict[str, object],
    predictions: list[dict[str, object]],
    labels: list[dict[str, object]],
    utilities: list[dict[str, object]],
):
    freeze = build_prediction_freeze_record(
        contract=contract,
        lockbox_id=LOCKBOX_ID,
        prediction_rows=predictions,
        sealed_at=datetime(2026, 1, 6, 22, 0, tzinfo=UTC),
        custody_authority="FIXTURE_CUSTODY_ONLY",
        custody_evidence_sha256=_sha("freeze-custody"),
    )
    label_open = build_label_open_record(
        contract=contract,
        lockbox_id=LOCKBOX_ID,
        prediction_freeze_record=freeze,
        label_rows=labels,
        utility_rows=utilities,
        opened_at=datetime(2026, 2, 2, 15, 0, tzinfo=UTC),
        custody_authority="FIXTURE_CUSTODY_ONLY",
        custody_evidence_sha256=_sha("label-open-custody"),
    )
    return freeze, label_open


def _report():
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    freeze, label_open = _custody(contract, predictions, labels, utilities)
    report = evaluate_untouched_lockboxes(
        contract=contract,
        prediction_rows=predictions,
        label_rows=labels,
        utility_rows=utilities,
        prediction_freeze_records=[freeze],
        label_open_records=[label_open],
    )
    return contract, predictions, labels, utilities, freeze, label_open, report


def test_evaluator_requires_at_least_one_preregistered_lockbox() -> None:
    with pytest.raises(UntouchedEvaluationContractError, match="at_least_one_lockbox_required"):
        _contract(lockbox_ids=())


def test_untouched_evaluator_computes_required_right_tail_metrics_and_zero_authority() -> None:
    _, _, _, _, _, _, report = _report()
    verify_evaluation_report(report)

    assert report["lockbox_count"] == 1
    assert report["raw_security_observation_count"] == 12
    assert report["statistical_security_observation_count"] == 9
    assert report["zero_weight_security_observation_count"] == 3
    assert report["effective_episode_count"] == 3
    assert report["zero_weight_effective_episode_count"] == 1

    k1 = report["precision_recall_lift_at_k"]["1"]
    assert float(k1["micro_precision"]) == pytest.approx(2 / 3)
    assert float(k1["micro_recall"]) == pytest.approx(1 / 3)
    assert float(k1["micro_lift"]) == pytest.approx(1.0)
    assert report["pr_auc_average_precision"] is not None

    detection = report["detection_and_false_winners"]
    assert detection["winner_effective_episode_count"] == 2
    assert detection["detected_winner_effective_episode_count"] == 1
    assert detection["missed_winner_effective_episode_count"] == 1
    assert float(detection["prebreakout_detection_recall_by_effective_episode"]) == pytest.approx(0.5)
    assert detection["false_winner_effective_episode_count"] == 1
    assert detection["catastrophic_false_winner_effective_episode_count"] == 1
    assert detection["raw_false_flag_count"] == 1
    assert detection["ttfld_sessions"]["minimum"] == 2
    assert detection["ttfld_sessions"]["maximum"] == 2

    wealth = report["right_tail_wealth_capture"]
    assert float(wealth["total_right_tail_wealth"]) == pytest.approx(5.0)
    assert float(wealth["flagged_prebreakout_captured_right_tail_wealth"]) == pytest.approx(2.0)
    assert float(wealth["flagged_prebreakout_right_tail_wealth_capture_ratio"]) == pytest.approx(0.4)
    assert float(wealth["top_k_prebreakout_capture"]["1"]["right_tail_wealth_capture_ratio"]) == pytest.approx(0.4)

    utility = report["i_vs_i_plus_x_incremental_net_utility"]
    assert utility["period_count"] == 2
    assert float(utility["incremental_net_utility_sum"]) == pytest.approx(-0.05)
    assert float(utility["positive_incremental_period_fraction"]) == pytest.approx(0.5)

    assert report["financial_alpha_evidence"] == 0
    assert report["promotion_authority"] == "NONE"
    assert report["capital_authority"] == "NONE"
    assert report["refit_or_rescue"] == "FORBIDDEN"


def test_zero_weight_smoke_is_traced_but_has_no_statistical_effect() -> None:
    _, _, _, _, _, _, report = _report()
    smoke = report["zero_weight_episode_diagnostics"]
    assert len(smoke) == 1
    assert smoke[0]["security_id"] == "CIQSEC:404"
    assert smoke[0]["false_winner_detected"] is True
    assert report["detection_and_false_winners"]["false_winner_effective_episode_count"] == 1


def test_prediction_statistical_weight_cannot_be_changed_after_preregistration() -> None:
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    predictions[0]["statistical_weight"] = 0
    predictions[0]["zero_weight_reason"] = ZERO_WEIGHT_REASON
    with pytest.raises(UntouchedEvaluationContractError, match="statistical_weight_not_preregistered"):
        build_prediction_freeze_record(
            contract=contract,
            lockbox_id=LOCKBOX_ID,
            prediction_rows=predictions,
            sealed_at=datetime(2026, 1, 6, 22, 0, tzinfo=UTC),
            custody_authority="FIXTURE_CUSTODY_ONLY",
            custody_evidence_sha256=_sha("freeze-custody"),
        )


def test_prediction_snapshot_must_be_frozen_after_all_prediction_records_and_before_label_open() -> None:
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    with pytest.raises(UntouchedEvaluationContractError, match="prediction_recorded_after_freeze"):
        build_prediction_freeze_record(
            contract=contract,
            lockbox_id=LOCKBOX_ID,
            prediction_rows=predictions,
            sealed_at=datetime(2026, 1, 6, 20, 0, tzinfo=UTC),
            custody_authority="FIXTURE_CUSTODY_ONLY",
            custody_evidence_sha256=_sha("freeze-custody"),
        )

    freeze = build_prediction_freeze_record(
        contract=contract,
        lockbox_id=LOCKBOX_ID,
        prediction_rows=predictions,
        sealed_at=datetime(2026, 1, 6, 22, 0, tzinfo=UTC),
        custody_authority="FIXTURE_CUSTODY_ONLY",
        custody_evidence_sha256=_sha("freeze-custody"),
    )
    with pytest.raises(UntouchedEvaluationContractError, match="label_open_must_be_after_prediction_freeze"):
        build_label_open_record(
            contract=contract,
            lockbox_id=LOCKBOX_ID,
            prediction_freeze_record=freeze,
            label_rows=labels,
            utility_rows=utilities,
            opened_at=datetime(2026, 1, 6, 21, 30, tzinfo=UTC),
            custody_authority="FIXTURE_CUSTODY_ONLY",
            custody_evidence_sha256=_sha("label-open-custody"),
        )


def test_exact_prediction_label_join_rejects_denominator_drop() -> None:
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    freeze, label_open = _custody(contract, predictions, labels, utilities)
    missing = labels[:-1]
    # Re-open receipt is intentionally not rebuilt: either the custody hash or
    # exact join must fail rather than silently shrink the denominator.
    with pytest.raises(UntouchedEvaluationContractError, match="label_snapshot_hash_mismatch|row_count_invalid"):
        evaluate_untouched_lockboxes(
            contract=contract,
            prediction_rows=predictions,
            label_rows=missing,
            utility_rows=utilities,
            prediction_freeze_records=[freeze],
            label_open_records=[label_open],
        )


def test_label_bytes_cannot_change_after_open_record() -> None:
    contract, predictions, labels, utilities, freeze, label_open, _ = _report()
    tampered = deepcopy(labels)
    tampered[0]["realized_total_return"] = 999.0
    with pytest.raises(UntouchedEvaluationContractError, match="label_snapshot_hash_mismatch"):
        evaluate_untouched_lockboxes(
            contract=contract,
            prediction_rows=predictions,
            label_rows=tampered,
            utility_rows=utilities,
            prediction_freeze_records=[freeze],
            label_open_records=[label_open],
        )


def test_exact_listing_identity_rejects_ticker_fallback() -> None:
    contract = _contract()
    predictions, _, _ = _fixture_rows()
    predictions[0]["security_id"] = "MU"
    with pytest.raises(ValueError, match="ciq_security_id_namespace_required"):
        build_prediction_freeze_record(
            contract=contract,
            lockbox_id=LOCKBOX_ID,
            prediction_rows=predictions,
            sealed_at=datetime(2026, 1, 6, 22, 0, tzinfo=UTC),
            custody_authority="FIXTURE_CUSTODY_ONLY",
            custody_evidence_sha256=_sha("freeze-custody"),
        )


def test_post_breakout_rows_cannot_rescue_prebreakout_evaluation() -> None:
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    # Move one winner observation onto breakout session B.  Rebuild custody so
    # the failure is semantic rather than merely a stale snapshot hash.
    for prediction, label in zip(predictions, labels):
        if prediction["security_id"] == "CIQSEC:101" and prediction["decision_session_ordinal"] == 12:
            prediction["decision_session_ordinal"] = 13
            prediction["decision_listing_session_ordinal"] = 13
            prediction["decision_session_date"] = "2026-01-07"
            label["decision_session_ordinal"] = 13
            label["decision_listing_session_ordinal"] = 13
            label["decision_session_date"] = "2026-01-07"
            break
    freeze, label_open = _custody(contract, predictions, labels, utilities)
    with pytest.raises(UntouchedEvaluationContractError, match="winner_prediction_not_prebreakout"):
        evaluate_untouched_lockboxes(
            contract=contract,
            prediction_rows=predictions,
            label_rows=labels,
            utility_rows=utilities,
            prediction_freeze_records=[freeze],
            label_open_records=[label_open],
        )


def test_global_session_gap_preserves_listing_local_ttfld() -> None:
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    for prediction, label in zip(predictions, labels):
        if prediction["security_id"] != "CIQSEC:101":
            continue
        # Preserve the three observed listing ordinals 10/11/12 while moving
        # their global market-spine ordinals apart. Breakout remains the next
        # observed listing session at local ordinal 13, but global ordinal 16.
        local = int(prediction["decision_listing_session_ordinal"])
        global_ordinal = {10: 10, 11: 13, 12: 15}[local]
        prediction["decision_session_ordinal"] = global_ordinal
        label["decision_session_ordinal"] = global_ordinal
        label["breakout_session_ordinal"] = 16
        label["breakout_listing_session_ordinal"] = 13
    freeze, label_open = _custody(contract, predictions, labels, utilities)
    report = evaluate_untouched_lockboxes(
        contract=contract,
        prediction_rows=predictions,
        label_rows=labels,
        utility_rows=utilities,
        prediction_freeze_records=[freeze],
        label_open_records=[label_open],
    )
    detection = report["detection_and_false_winners"]
    assert detection["ttfld_sessions"]["minimum"] == 2
    assert detection["ttfld_sessions"]["maximum"] == 2


def test_effective_episode_identity_and_wealth_cannot_drift_across_dates() -> None:
    contract = _contract()
    predictions, labels, utilities = _fixture_rows()
    freeze = build_prediction_freeze_record(
        contract=contract,
        lockbox_id=LOCKBOX_ID,
        prediction_rows=predictions,
        sealed_at=datetime(2026, 1, 6, 22, 0, tzinfo=UTC),
        custody_authority="FIXTURE_CUSTODY_ONLY",
        custody_evidence_sha256=_sha("freeze-custody"),
    )
    labels[4]["right_tail_wealth"] = 9.0
    label_open = build_label_open_record(
        contract=contract,
        lockbox_id=LOCKBOX_ID,
        prediction_freeze_record=freeze,
        label_rows=labels,
        utility_rows=utilities,
        opened_at=datetime(2026, 2, 2, 15, 0, tzinfo=UTC),
        custody_authority="FIXTURE_CUSTODY_ONLY",
        custody_evidence_sha256=_sha("label-open-custody-mutated-consistently"),
    )
    with pytest.raises(UntouchedEvaluationContractError, match="effective_episode_invariant_drift"):
        evaluate_untouched_lockboxes(
            contract=contract,
            prediction_rows=predictions,
            label_rows=labels,
            utility_rows=utilities,
            prediction_freeze_records=[freeze],
            label_open_records=[label_open],
        )


def test_evaluation_report_is_content_addressed_and_tamper_evident() -> None:
    _, _, _, _, _, _, report = _report()
    verify_evaluation_report(report)
    tampered = deepcopy(report)
    tampered["financial_alpha_evidence"] = 1
    with pytest.raises(UntouchedEvaluationContractError, match="report_authority_invalid"):
        verify_evaluation_report(tampered)

    tampered = deepcopy(report)
    tampered["effective_episode_count"] = 999
    with pytest.raises(UntouchedEvaluationContractError, match="report_hash_mismatch"):
        verify_evaluation_report(tampered)


def test_w6_package_has_no_discovery_provider_model_fit_or_broker_dependency() -> None:
    root = Path("research/prebreakout_untouched_evaluator_v1")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = (
        "discovery_outcomes",
        "research.prebreakout_discovery_v1",
        "requests.",
        "wrds",
        "submit_order",
        "fit(",
        "train(",
    )
    assert not any(token in text for token in forbidden)
