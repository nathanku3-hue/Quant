"""Development-only negative-knowledge diagnostics for closed Trial #1.

FailurePacketV1 consumes only already-opened PREBREAKOUT Trial #1 development
bytes plus retained historical AOV diagnostics.  It cannot append a trial,
change the frozen successor methodology, query a provider, open W6, start a
prediction clock, or create financial/capital authority.
"""

from __future__ import annotations

from collections import Counter
from math import ceil
from statistics import median
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_discovery_v1.trial1_m0 import IMPLEMENTATION_ID, TRIAL_ID


SCHEMA_VERSION = "prebreakout_failure_packet_v1"
AUTHORITY_CLASS = "DEVELOPMENT_NEGATIVE_KNOWLEDGE_ONLY_ZERO_FINANCIAL_AUTHORITY"
DISCOVERY_STATUS = "FAIL"
DEFENSIVE_STATUS = "DIAGNOSTIC_POSITIVE"


class FailurePacketError(ValueError):
    """Fail-closed validation error for FailurePacketV1."""


def build_failure_packet(
    *,
    w5_run: Mapping[str, Any],
    eligible_labeled_features: pd.DataFrame,
    winner_census: pd.DataFrame,
    flag_projection: pd.DataFrame,
    false_winners: pd.DataFrame,
    smoke_check: Mapping[str, Any],
    econphysics_manifest: Mapping[str, Any],
    a2_result: Mapping[str, Any],
    winner_capture_diagnostic: Mapping[str, Any],
    source_sha256s: Mapping[str, str],
) -> dict[str, Any]:
    """Build one deterministic read-only Trial #1 failure packet."""

    oos = _oos_diagnostics(w5_run, eligible_labeled_features)
    episode = _winner_episode_diagnostics(
        winner_census=winner_census,
        flag_projection=flag_projection,
        eligible_labeled_features=eligible_labeled_features,
    )
    false_diag = _false_winner_diagnostics(false_winners)
    smoke = _smoke_diagnostics(smoke_check)
    cross_audit = _cross_a2_trial1_audit(
        oos=oos,
        episode=episode,
        a2_result=a2_result,
        winner_capture=winner_capture_diagnostic,
    )
    observability = _observability_map(econphysics_manifest)

    body = {
        "schema_version": SCHEMA_VERSION,
        "family_id": "PREBREAKOUT_DISCOVERY_v1",
        "trial_id": TRIAL_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "status": "FAILURE_PACKET_COMPLETE",
        "authority": {
            "authority_class": AUTHORITY_CLASS,
            "trial_cost": 0,
            "discovery_status": DISCOVERY_STATUS,
            "defensive_quality_status": DEFENSIVE_STATUS,
            "defensive_quality_is_acceptance_truth": False,
            "untouched_evidence": False,
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
            "capture_authority": "NONE",
            "successor_empirical_trial_authority": "NONE",
            "successor_prediction_clock_authority": "NONE",
            "w6_authority": "HOLD_UNTOUCHED",
            "causal_edge_mutation": "FORBIDDEN",
            "causal_sign_mutation": "FORBIDDEN",
            "causal_lag_mutation": "FORBIDDEN",
            "threshold_mutation": "FORBIDDEN",
            "selection_budget_mutation": "FORBIDDEN",
            "successor_model_mutation": "FORBIDDEN",
            "trial1_future_market_confirmation_reuse": "REQUIRES_SEPARATE_PREREGISTRATION",
        },
        "source_sha256s": dict(sorted(source_sha256s.items())),
        "mu_sndk_smoke_correction": smoke,
        "discovery_failure_diagnostics": {
            "temporal_oos": oos,
            "winner_episode": episode,
            "false_winner_persistence_concentration": false_diag,
        },
        "role_split": {
            "DISCOVERY": "FAIL",
            "DEFENSIVE_QUALITY": "DIAGNOSTIC_POSITIVE",
            "interpretation": (
                "Trial #1 carries useful downside/market-quality information but failed its "
                "winner-discovery role; the defensive result is outcome-visible development "
                "evidence only and cannot be promoted or reused as untouched evidence."
            ),
        },
        "cross_a2_trial1_right_tail_clipping_audit": cross_audit,
        "econphysics_prebreakout_v1_observability_demand_map": observability,
    }
    return {
        **body,
        "packet_sha256": domain_hash(
            "PREBREAKOUT_DISCOVERY_V1:FAILURE_PACKET_V1",
            _hash_safe(body),
        ),
    }


def _oos_diagnostics(
    w5_run: Mapping[str, Any],
    eligible_labeled_features: pd.DataFrame,
) -> dict[str, Any]:
    folds = list(w5_run.get("folds") or [])
    if len(folds) != 4:
        raise FailurePacketError("failure_packet_w5_four_folds_required")
    prediction_records: list[dict[str, Any]] = []
    fold_lifts: list[float] = []
    expected_matured = 0
    for fold in folds:
        prediction_records.extend(dict(row) for row in fold.get("temporal_oos_predictions") or [])
        value = fold.get("development_objective_value")
        if value is None:
            raise FailurePacketError("failure_packet_informative_fold_required")
        fold_lifts.append(float(value))
        expected_matured += int(fold.get("temporal_objective_matured_label_row_count", 0))

    predictions = pd.DataFrame(prediction_records)
    _require_columns(predictions, ["decision_date", "security_id", "forecast_score"])
    predictions["forecast_score"] = pd.to_numeric(predictions["forecast_score"], errors="raise")
    if predictions.duplicated(["decision_date", "security_id"]).any():
        raise FailurePacketError("failure_packet_prediction_key_duplicate")

    facts = eligible_labeled_features.copy()
    _require_columns(
        facts,
        [
            "decision_date",
            "security_id",
            "trading_item_id",
            "feature_status",
            "near_high_component",
            "vol_compression_component",
            "volume_pressure_component",
            "flagged",
            "forward_total_return",
            "winner_label",
        ],
    )
    if facts.duplicated(["decision_date", "security_id"]).any():
        raise FailurePacketError("failure_packet_eligible_fact_key_duplicate")
    facts["forward_total_return"] = pd.to_numeric(facts["forward_total_return"], errors="coerce")

    joined = predictions.merge(
        facts,
        on=["decision_date", "security_id"],
        how="left",
        validate="one_to_one",
    )
    matured = joined[joined["winner_label"].notna() & joined["forward_total_return"].notna()].copy()
    if len(matured) != expected_matured:
        raise FailurePacketError(
            f"failure_packet_matured_oos_count_drift:{len(matured)}!={expected_matured}"
        )
    matured["winner_label"] = matured["winner_label"].astype(bool)
    matured["triggered"] = matured["forecast_score"].gt(0.0)

    base_rate = float(matured["winner_label"].mean())
    triggered = matured[matured["triggered"]].copy()
    trigger_winner_rate = float(triggered["winner_label"].mean())
    trigger_lift = _safe_ratio(trigger_winner_rate, base_rate)

    matured["month"] = matured["decision_date"].astype(str).str.slice(0, 7)
    monthly: list[dict[str, Any]] = []
    for month, group in matured.groupby("month", sort=True):
        group_trigger = group[group["triggered"]]
        month_base = float(group["winner_label"].mean())
        month_trigger = float(group_trigger["winner_label"].mean())
        monthly.append(
            {
                "month": str(month),
                "row_count": int(len(group)),
                "trigger_count": int(len(group_trigger)),
                "base_winner_rate": month_base,
                "trigger_winner_rate": month_trigger,
                "trigger_lift_vs_base": _safe_ratio(month_trigger, month_base),
            }
        )

    quintile_frame = triggered.copy()
    quintile_frame["score_quintile"] = pd.qcut(
        quintile_frame["forecast_score"],
        q=5,
        labels=False,
        duplicates="raise",
    ).astype(int) + 1
    quintiles: list[dict[str, Any]] = []
    for quintile, group in quintile_frame.groupby("score_quintile", sort=True):
        rate = float(group["winner_label"].mean())
        quintiles.append(
            {
                "score_quintile": int(quintile),
                "row_count": int(len(group)),
                "score_min": float(group["forecast_score"].min()),
                "score_max": float(group["forecast_score"].max()),
                "winner_rate": rate,
                "lift_vs_oos_base": _safe_ratio(rate, base_rate),
            }
        )

    # Bottom-tail labels are defined date-locally on the complete eligible,
    # matured development population, then projected into the W5 temporal OOS
    # rows.  This avoids re-defining the tail after holdout removal.
    bottom = facts[facts["winner_label"].notna() & facts["forward_total_return"].notna()].copy()
    bottom.sort_values(
        ["decision_date", "forward_total_return", "security_id", "trading_item_id"],
        inplace=True,
        kind="stable",
    )
    bottom["date_rank_asc"] = bottom.groupby("decision_date", sort=False).cumcount() + 1
    bottom["date_count"] = bottom.groupby("decision_date", sort=False)["security_id"].transform("size")
    bottom["bottom_5pct"] = bottom["date_rank_asc"] <= bottom["date_count"].map(
        lambda value: ceil(float(value) * 0.05)
    )
    bottom["bottom_1pct"] = bottom["date_rank_asc"] <= bottom["date_count"].map(
        lambda value: ceil(float(value) * 0.01)
    )
    matured = matured.merge(
        bottom[["decision_date", "security_id", "bottom_5pct", "bottom_1pct"]],
        on=["decision_date", "security_id"],
        how="left",
        validate="one_to_one",
    )

    flagged_nonwinner = matured[matured["triggered"] & ~matured["winner_label"]]
    ordinary_nonwinner = matured[~matured["triggered"] & ~matured["winner_label"]]
    defensive = {
        "flagged_nonwinner_count": int(len(flagged_nonwinner)),
        "ordinary_nonwinner_count": int(len(ordinary_nonwinner)),
        "flagged_nonwinner_forward_20d_mean": float(flagged_nonwinner["forward_total_return"].mean()),
        "flagged_nonwinner_forward_20d_median": float(flagged_nonwinner["forward_total_return"].median()),
        "ordinary_nonwinner_forward_20d_mean": float(ordinary_nonwinner["forward_total_return"].mean()),
        "ordinary_nonwinner_forward_20d_median": float(ordinary_nonwinner["forward_total_return"].median()),
        "flagged_nonwinner_date_local_bottom_5pct_rate": float(flagged_nonwinner["bottom_5pct"].mean()),
        "ordinary_nonwinner_date_local_bottom_5pct_rate": float(ordinary_nonwinner["bottom_5pct"].mean()),
        "bottom_5pct_rate_ratio_flagged_vs_ordinary": _safe_ratio(
            float(flagged_nonwinner["bottom_5pct"].mean()),
            float(ordinary_nonwinner["bottom_5pct"].mean()),
        ),
        "flagged_nonwinner_date_local_bottom_1pct_rate": float(flagged_nonwinner["bottom_1pct"].mean()),
        "ordinary_nonwinner_date_local_bottom_1pct_rate": float(ordinary_nonwinner["bottom_1pct"].mean()),
        "flagged_nonwinner_return_le_minus_20pct_rate": float(
            flagged_nonwinner["forward_total_return"].le(-0.20).mean()
        ),
        "ordinary_nonwinner_return_le_minus_20pct_rate": float(
            ordinary_nonwinner["forward_total_return"].le(-0.20).mean()
        ),
        "flagged_nonwinner_return_le_minus_40pct_rate": float(
            flagged_nonwinner["forward_total_return"].le(-0.40).mean()
        ),
        "ordinary_nonwinner_return_le_minus_40pct_rate": float(
            ordinary_nonwinner["forward_total_return"].le(-0.40).mean()
        ),
    }

    all_folds_below_one = all(value < 1.0 for value in fold_lifts)
    all_months_below_one = all(row["trigger_lift_vs_base"] < 1.0 for row in monthly)
    all_quintiles_below_one = all(row["lift_vs_oos_base"] < 1.0 for row in quintiles)
    highest_quintile_worst = quintiles[-1]["winner_rate"] == min(row["winner_rate"] for row in quintiles)

    return {
        "matured_temporal_oos_row_count": int(len(matured)),
        "trigger_count": int(matured["triggered"].sum()),
        "universe_winner_rate": base_rate,
        "trigger_winner_rate": trigger_winner_rate,
        "trigger_lift_vs_universe": trigger_lift,
        "fold_recall_lifts": fold_lifts,
        "median_fold_recall_lift": float(median(fold_lifts)),
        "all_four_folds_below_one": all_folds_below_one,
        "monthly": monthly,
        "all_months_below_one": all_months_below_one,
        "trigger_score_quintiles": quintiles,
        "all_trigger_score_quintiles_below_one": all_quintiles_below_one,
        "highest_score_quintile_is_worst": bool(highest_quintile_worst),
        "ranking_information_status": (
            "ABSENT_OR_ANTI_MONOTONE_IN_DEVELOPMENT"
            if all_quintiles_below_one and highest_quintile_worst
            else "MIXED_DIAGNOSTIC"
        ),
        "threshold_rescue_interpretation": "NOT_SUPPORTED_BY_SCORE_RANKING_DIAGNOSTIC",
        "defensive_quality": defensive,
    }


def _winner_episode_diagnostics(
    *,
    winner_census: pd.DataFrame,
    flag_projection: pd.DataFrame,
    eligible_labeled_features: pd.DataFrame,
) -> dict[str, Any]:
    winners = winner_census.copy()
    _require_columns(
        winners,
        [
            "census_class",
            "effective_episode_id",
            "security_id",
            "trading_item_id",
            "breakout_listing_session_ordinal",
            "b_minus_1_session_date",
            "b_minus_1_listing_session_ordinal",
            "first_legitimate_flag_listing_session_ordinal",
            "statistical_weight",
        ],
    )
    winners = winners[winners["statistical_weight"].eq(1)].copy()
    if len(winners) != 2381:
        raise FailurePacketError(f"failure_packet_winner_count_drift:{len(winners)}")

    facts = eligible_labeled_features[
        ["decision_date", "security_id", "trading_item_id", "forward_total_return"]
    ].copy()
    payoff = winners.merge(
        facts,
        left_on=["b_minus_1_session_date", "security_id", "trading_item_id"],
        right_on=["decision_date", "security_id", "trading_item_id"],
        how="left",
        validate="one_to_one",
    )
    if payoff["forward_total_return"].isna().any():
        raise FailurePacketError("failure_packet_winner_bminus1_payoff_missing")
    payoff["detected"] = payoff["census_class"].eq("TRUE_WINNER")
    payoff["payoff_quartile"] = pd.qcut(
        payoff["forward_total_return"], q=4, labels=False, duplicates="raise"
    ).astype(int) + 1
    payoff_quartiles: list[dict[str, Any]] = []
    for quartile, group in payoff.groupby("payoff_quartile", sort=True):
        payoff_quartiles.append(
            {
                "winner_payoff_quartile": int(quartile),
                "episode_count": int(len(group)),
                "detection_rate": float(group["detected"].mean()),
                "median_forward_20d_return": float(group["forward_total_return"].median()),
            }
        )

    detected = winners[winners["census_class"].eq("TRUE_WINNER")].copy()
    detected["lead_sessions"] = (
        pd.to_numeric(detected["breakout_listing_session_ordinal"], errors="raise")
        - pd.to_numeric(detected["first_legitimate_flag_listing_session_ordinal"], errors="raise")
    ).astype(int)
    lead_counts = Counter(int(value) for value in detected["lead_sessions"])
    lead_shape = {
        "detected_episode_count": int(len(detected)),
        "lead_sessions_mean": float(detected["lead_sessions"].mean()),
        "lead_sessions_median": float(detected["lead_sessions"].median()),
        "lead_sessions_p25": float(detected["lead_sessions"].quantile(0.25)),
        "lead_sessions_p75": float(detected["lead_sessions"].quantile(0.75)),
        "lead_session_counts": [
            {"lead_sessions": lead, "episode_count": int(lead_counts.get(lead, 0))}
            for lead in range(1, 21)
        ],
    }

    misses = winners[winners["census_class"].eq("MISSED_WINNER")].copy()
    projection = flag_projection.copy()
    _require_columns(
        projection,
        [
            "security_id",
            "trading_item_id",
            "decision_listing_session_ordinal",
            "feature_status",
            "near_high_component",
            "vol_compression_component",
            "volume_pressure_component",
            "flagged",
        ],
    )
    grouped = {
        key: group.sort_values("decision_listing_session_ordinal", kind="stable")
        for key, group in projection.groupby(["security_id", "trading_item_id"], sort=False)
    }
    taxonomy = Counter()
    for row in misses.itertuples(index=False):
        key = (row.security_id, row.trading_item_id)
        group = grouped.get(key)
        if group is None:
            raise FailurePacketError("failure_packet_miss_identity_missing_from_projection")
        lower = int(row.breakout_listing_session_ordinal) - 20
        upper = int(row.b_minus_1_listing_session_ordinal)
        lead = group[
            group["decision_listing_session_ordinal"].between(lower, upper, inclusive="both")
        ].copy()
        ready = lead["feature_status"].eq("READY")
        has_ready = bool(ready.any())
        has_near = bool((ready & lead["near_high_component"].gt(0.0)).any())
        has_comp = bool((ready & lead["vol_compression_component"].gt(0.0)).any())
        has_vol = bool((ready & lead["volume_pressure_component"].gt(0.0)).any())
        component_sync = bool(
            (
                ready
                & lead["near_high_component"].gt(0.0)
                & lead["vol_compression_component"].gt(0.0)
                & lead["volume_pressure_component"].gt(0.0)
            ).any()
        )
        has_legal_trigger = bool(lead["flagged"].astype(bool).any())
        if has_legal_trigger:
            raise FailurePacketError("failure_packet_missed_winner_has_legal_trigger")
        if not has_ready:
            taxonomy["NO_READY_MARKET_HISTORY"] += 1
        elif not has_near:
            taxonomy["NEVER_NEAR_HIGH"] += 1
        elif not has_comp:
            taxonomy["NO_COMPRESSION_COMPONENT"] += 1
        elif not has_vol:
            taxonomy["NO_VOLUME_PRESSURE_COMPONENT"] += 1
        elif not component_sync:
            taxonomy["COMPONENTS_PRESENT_SEPARATELY_NO_COMPONENT_SYNC"] += 1
        else:
            taxonomy["COMPONENT_SYNC_BUT_NO_LEGAL_TRIGGER"] += 1

    if sum(taxonomy.values()) != len(misses):
        raise FailurePacketError("failure_packet_miss_taxonomy_not_exhaustive")

    return {
        "statistical_winner_episode_count": int(len(winners)),
        "detected_winner_episode_count": int(payoff["detected"].sum()),
        "missed_winner_episode_count": int((~payoff["detected"]).sum()),
        "winner_payoff_quartiles": payoff_quartiles,
        "detected_winner_forward_20d_median": float(
            payoff.loc[payoff["detected"], "forward_total_return"].median()
        ),
        "missed_winner_forward_20d_median": float(
            payoff.loc[~payoff["detected"], "forward_total_return"].median()
        ),
        "anti_convex_capture_status": (
            "DETECTION_RATE_DECLINES_IN_LARGEST_PAYOFF_QUARTILE"
            if payoff_quartiles[-1]["detection_rate"] < payoff_quartiles[0]["detection_rate"]
            else "NOT_ESTABLISHED"
        ),
        "lead_shape": lead_shape,
        "miss_taxonomy": {
            "episode_count": int(len(misses)),
            "leaves": [
                {
                    "reason": reason,
                    "count": int(taxonomy[reason]),
                    "share_of_misses": float(taxonomy[reason] / len(misses)),
                }
                for reason in (
                    "NO_READY_MARKET_HISTORY",
                    "NEVER_NEAR_HIGH",
                    "NO_COMPRESSION_COMPONENT",
                    "NO_VOLUME_PRESSURE_COMPONENT",
                    "COMPONENTS_PRESENT_SEPARATELY_NO_COMPONENT_SYNC",
                    "COMPONENT_SYNC_BUT_NO_LEGAL_TRIGGER",
                )
            ],
            "coverage_failure_share": float(taxonomy["NO_READY_MARKET_HISTORY"] / len(misses)),
            "noncoverage_failure_share": float(1.0 - taxonomy["NO_READY_MARKET_HISTORY"] / len(misses)),
            "interpretation": "REPRESENTATION_TEMPORAL_COMPOSITION_DOMINATES_DATA_COVERAGE_FAILURE",
        },
    }


def _false_winner_diagnostics(false_winners: pd.DataFrame) -> dict[str, Any]:
    frame = false_winners.copy()
    _require_columns(
        frame,
        ["security_id", "trading_item_id", "decision_session_ordinal", "statistical_weight"],
    )
    frame = frame[frame["statistical_weight"].eq(1)].copy()
    frame["identity_key"] = frame["security_id"].astype(str) + "|" + frame["trading_item_id"].astype(str)
    identity_counts = frame.groupby("identity_key", sort=False).size().sort_values(ascending=False)
    date_counts = frame.groupby("decision_session_ordinal", sort=False).size().sort_values(ascending=False)
    unique_identities = int(len(identity_counts))
    top_1pct_n = max(1, ceil(unique_identities * 0.01))

    streaks: list[int] = []
    for _, group in frame.groupby("identity_key", sort=False):
        ordinals = sorted(set(int(value) for value in group["decision_session_ordinal"]))
        best = current = 0
        previous: int | None = None
        for value in ordinals:
            if previous is not None and value == previous + 1:
                current += 1
            else:
                current = 1
            best = max(best, current)
            previous = value
        streaks.append(best)

    return {
        "false_winner_decision_row_count": int(len(frame)),
        "unique_false_winner_identity_count": unique_identities,
        "false_winner_days_per_identity_median": float(identity_counts.median()),
        "false_winner_days_per_identity_p90": float(identity_counts.quantile(0.90)),
        "false_winner_days_per_identity_max": int(identity_counts.max()),
        "max_consecutive_false_winner_sessions_per_identity_median": float(np.median(streaks)),
        "max_consecutive_false_winner_sessions_per_identity_p90": float(np.quantile(streaks, 0.90)),
        "max_consecutive_false_winner_sessions": int(max(streaks)),
        "top_1pct_identity_share_of_false_winner_rows": float(
            identity_counts.head(top_1pct_n).sum() / len(frame)
        ),
        "top_10_identity_share_of_false_winner_rows": float(identity_counts.head(10).sum() / len(frame)),
        "false_winner_rows_per_date_median": float(date_counts.median()),
        "false_winner_rows_per_date_p90": float(date_counts.quantile(0.90)),
        "false_winner_rows_per_date_max": int(date_counts.max()),
    }


def _smoke_diagnostics(smoke_check: Mapping[str, Any]) -> dict[str, Any]:
    checked = int(smoke_check.get("checked_development_smoke_episode_count", -1))
    deferred = int(smoke_check.get("deferred_postdevelopment_smoke_episode_count", -1))
    failures = int(smoke_check.get("failure_count", -1))
    if checked != 19 or deferred != 4 or failures != 16:
        raise FailurePacketError(
            f"failure_packet_smoke_checker_drift:checked={checked};deferred={deferred};failures={failures}"
        )
    return {
        "sealed_trial1_atlas_statistical_close_affected": False,
        "sealed_trial1_atlas_mu_sndk_smoke_is_acceptance_truth": False,
        "defect": "W4_SMOKE_ANY_LEGITIMATE_PREBREAKOUT_FLAG_WAS_CONTAMINATED_BY_WINNER_LABEL",
        "correct_law": "ALL_PIT_ELIGIBLE_BREAKOUT_B_EPISODES_ZERO_WEIGHT_ENGINEERING_SMOKE_INDEPENDENT_OF_WINNER_LABEL",
        "independent_checker": {
            "checked_development_episode_count": checked,
            "legitimate_pre_b_flag_episode_count": checked - failures,
            "no_legitimate_pre_b_flag_episode_count": failures,
            "deferred_postdevelopment_episode_count": deferred,
        },
        "supersession": "INDEPENDENT_CHECKER_SUPERSEDES_SEALED_ATLAS_SMOKE_NUMBERS_ONLY",
    }


def _cross_a2_trial1_audit(
    *,
    oos: Mapping[str, Any],
    episode: Mapping[str, Any],
    a2_result: Mapping[str, Any],
    winner_capture: Mapping[str, Any],
) -> dict[str, Any]:
    pvc = dict(a2_result.get("parent_vs_child") or {})
    a2 = dict((winner_capture.get("stage_diagnostics") or {}).get("A2") or {})
    a2_20 = dict((a2.get("horizons") or {}).get("20") or {})
    aggregate = dict(a2_20.get("aggregate") or {})
    attribution = dict(a2.get("whole_stage_parent_child_attribution") or {})
    winners = list(attribution.get("largest_realized_winners") or [])
    if not pvc or not aggregate or not attribution:
        raise FailurePacketError("failure_packet_a2_diagnostic_inputs_missing")

    trial_quartiles = list(episode["winner_payoff_quartiles"])
    return {
        "status": "CONVERGENT_DIAGNOSTIC_RIGHT_TAIL_CLIPPING_RISK_NOT_SYSTEM_PROOF",
        "trial1": {
            "highest_payoff_quartile_detection_rate": trial_quartiles[-1]["detection_rate"],
            "lowest_payoff_quartile_detection_rate": trial_quartiles[0]["detection_rate"],
            "detected_winner_forward_20d_median": episode["detected_winner_forward_20d_median"],
            "missed_winner_forward_20d_median": episode["missed_winner_forward_20d_median"],
            "flagged_nonwinner_bottom_5pct_rate_ratio_vs_ordinary": oos["defensive_quality"][
                "bottom_5pct_rate_ratio_flagged_vs_ordinary"
            ],
        },
        "a2_child_vs_parent": {
            "child_minus_parent_cumulative_return": float(pvc["child_minus_parent_cumulative_return"]),
            "child_minus_parent_Sharpe": float(pvc["child_minus_parent_Sharpe"]),
            "child_minus_parent_max_drawdown": float(pvc["child_minus_parent_max_drawdown"]),
            "child_CVaR_improvement_vs_parent": float(pvc["child_CVaR_improvement_vs_parent"]),
            "horizon20_clipped_winner_rate": float(aggregate["child_clipping"]["clipped_winner_rate"]),
            "horizon20_winner_gross_giveup_sum": float(
                aggregate["child_clipping"]["winner_gross_giveup_sum"]
            ),
            "largest_five_realized_winner_gap_share": float(
                attribution["largest_realized_winner_gap_share"]
            ),
            "largest_five_realized_winner_tickers": [row.get("ticker") for row in winners[:5]],
        },
        "interpretation": (
            "Independent development/historical diagnostics are directionally consistent with a clean-state "
            "bias: downside improves while the largest convex winners are under-captured. This creates a "
            "system-level audit hypothesis only; it cannot mutate Parent/Child or the successor methodology."
        ),
    }


def _observability_map(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "econphysics_prebreakout_pit_observable_manifest_v1":
        raise FailurePacketError("failure_packet_econphysics_manifest_identity_invalid")
    if manifest.get("capture_authority") != "NONE" or manifest.get("w6_authority") != "HOLD_UNTOUCHED":
        raise FailurePacketError("failure_packet_econphysics_authority_boundary_drift")

    status_by_node = {
        "SUPPLY_CAPACITY_STATE": {
            "status": "PARTIAL_CAPABILITY_DIRECT_STATE_UNOBSERVED",
            "banked": ["fund.capex_q logical/PIT mechanics"],
            "unobserved": ["direct capacity/supply claim evidence in successor corpus"],
            "blocking": True,
        },
        "INVENTORY_CHANNEL_STATE": {
            "status": "PARTIAL_STRUCTURED_CAPABILITY_CHANNEL_STATE_UNOBSERVED",
            "banked": ["fund.inventory_q", "fund.revenue_q logical/PIT mechanics"],
            "unobserved": ["channel/inventory source claims in successor corpus"],
            "blocking": True,
        },
        "DEMAND_ORDER_STATE": {
            "status": "PARTIAL_REALIZED_DEMAND_ORDERS_GUIDANCE_UNOBSERVED",
            "banked": ["fund.revenue_q logical/PIT mechanics"],
            "unobserved": ["orders/backlog/demand claims", "guidance claims"],
            "blocking": True,
        },
        "PRICING_MIX_STATE": {
            "status": "UNOBSERVED",
            "banked": [],
            "unobserved": ["pricing claims", "competition claims"],
            "blocking": True,
        },
        "UTILIZATION_COST_STATE": {
            "status": "UNOBSERVED",
            "banked": [],
            "unobserved": ["utilization/throughput claims", "direct unit-cost evidence"],
            "blocking": True,
        },
        "MARGIN_CASH_STATE": {
            "status": "PARTIAL_CURRENT_SOURCE_GAPS",
            "banked": ["fund.revenue_q", "fund.operating_margin_q logical/PIT mechanics"],
            "unobserved": ["fund.gross_margin_q current source MISSING_SOURCE", "fund.cash_from_ops_q current source MISSING_SOURCE"],
            "blocking": True,
        },
        "REVISION_GUIDANCE_STATE": {
            "status": "UNOBSERVED",
            "banked": ["expectation row contract/measures frozen"],
            "unobserved": ["current expectations source MISSING_SOURCE", "guidance source claims unlanded"],
            "blocking": True,
        },
        "EXPECTATION_GAP_STATE": {
            "status": "BLOCKED_BY_EXPECTATION_OBSERVABILITY",
            "banked": ["derived-state law frozen"],
            "unobserved": ["lawful consensus/revision trajectory needed to construct expectation gap"],
            "blocking": True,
        },
        "MARKET_CONFIRMATION_STATE": {
            "status": "EXISTING_PIT_AUTHORITY_DOWNSTREAM_ONLY",
            "banked": ["close", "total_return_1d", "volume", "derived ADV/realized-vol/SMA mechanics"],
            "unobserved": [],
            "blocking": False,
        },
    }

    nodes = list(manifest.get("nodes") or [])
    result_nodes: list[dict[str, Any]] = []
    for node in nodes:
        node_id = str(node.get("node_id") or "")
        if node_id not in status_by_node:
            raise FailurePacketError(f"failure_packet_observability_node_unmapped:{node_id}")
        result_nodes.append(
            {
                "node_id": node_id,
                "manifest_structured_observables": list(node.get("structured_observables") or []),
                "manifest_source_claim_topics": list(node.get("source_claim_topics") or []),
                "manifest_expectation_measures": list(node.get("expectation_measures") or []),
                **status_by_node[node_id],
            }
        )

    return {
        "family_id": manifest.get("family_id"),
        "capture_authority": "NONE",
        "map_role": "DATA_GAP_AND_OBSERVABILITY_DEMAND_ONLY",
        "nodes": result_nodes,
        "true_state_transition_validation_blockers": [
            "SUCCESSOR_SPECIFIC_PIT_CORPUS_NOT_CAPTURED_OR_ADMITTED_TODAY",
            "SOURCE_CLAIMS_UNLANDED_FOR_PRICING_UTILIZATION_AND_GUIDANCE_MECHANISMS",
            "EXPECTATIONS_UNOBSERVED_SO_EXPECTATION_GAP_CANNOT_BE_VALIDATED",
            "GROSS_MARGIN_AND_CASH_FROM_OPERATIONS_CURRENT_SOURCE_GAPS",
        ],
        "non_blocking_existing_surface": (
            "MARKET_CONFIRMATION_STATE is already observable but is downstream-only and cannot substitute "
            "for missing economic state."
        ),
        "authority_interpretation": (
            "This map identifies demand only. It does not authorize capture, define a new observable, "
            "or alter any frozen causal edge/sign/lag/threshold/SelectionBudget."
        ),
    }


def _require_columns(frame: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise FailurePacketError(f"failure_packet_columns_missing:{','.join(missing)}")


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        raise FailurePacketError("failure_packet_ratio_denominator_nonpositive")
    return float(numerator / denominator)


def _hash_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _hash_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_hash_safe(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        if np.isnan(numeric):
            return None
        return format(numeric, ".17g")
    if pd.isna(value):
        return None
    raise FailurePacketError(f"failure_packet_hash_value_type_unsupported:{type(value).__name__}")
