"""Frozen W2 preregistration for PREBREAKOUT_DISCOVERY_v1.

This file owns breakout-B, TTFLD, horizons, falsifiers, smoke obligations, and
search-budget identity.  It deliberately does not own W3 PIT adapters, W4
Atlas construction, W5 walk-forward mechanics, or W6 outcome evaluation.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash


CONTRACT_SCHEMA = "prebreakout_discovery_contract_v1"
FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
RISK_SET_SPEC_ID = "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"
PRIMARY_LABEL_SPEC_ID = "PREBREAKOUT_RIGHT_TAIL_20D_TOP5_V1"
SECONDARY_LABEL_SPEC_ID = "PREBREAKOUT_RIGHT_TAIL_10D_TOP5_V1"

BREAKOUT_SPEC_ID = "PREBREAKOUT_ALGORITHMIC_BREAKOUT_B_20D_HIGH_V1"
BREAKOUT_CLOSE_SEMANTICS = "PIT_CORPORATE_ACTION_NORMALIZED_PRIMARY_LISTING_CLOSE_AS_OF_SESSION"
BREAKOUT_LOOKBACK_SESSIONS = 20
BREAKOUT_EPISODE_COOLDOWN_SESSIONS = 20
BREAKOUT_COMPARATOR = "STRICT_GT_PRIOR_20_SESSION_HIGH"

PRIMARY_HORIZON_SESSIONS = 20
SECONDARY_HORIZON_SESSIONS = 10
WINNER_FRACTION = 0.05
WINNER_COUNT_LAW = "CEIL_WINNER_FRACTION_TIMES_DATE_LOCAL_RISK_SET_COUNT"
FORWARD_RETURN_LAW = "COMPOUND_NEXT_H_OBSERVED_PRIMARY_LISTING_SESSIONS_AFTER_DECISION"
WINNER_TIE_BREAK = "FORWARD_TOTAL_RETURN_DESC_SECURITY_ID_ASC_TRADING_ITEM_ID_ASC"
INCOMPLETE_HORIZON_LAW = "INCOMPLETE_HORIZON_NO_IMPUTATION_NO_MATURED_DENOMINATOR_CREDIT"
LEAD_LOOKBACK_SESSIONS = 20
MIN_LEGITIMATE_LEAD_SESSIONS = 1
TTFLD_SPEC_ID = "PREBREAKOUT_TTFLD_BOUNDED_20_TO_B_MINUS_1_V1"
MISSED_TTFLD_EFFECTIVE_SESSIONS = 0

SEARCH_FAMILY_ID = "PREBREAKOUT_SEARCH_v1"
TRIAL_LEDGER_SCOPE = "PREBREAKOUT_V1_TRIAL_LEDGER"
PREDICTION_LEDGER_SCOPE = "PREBREAKOUT_V1_PREDICTION_LEDGER"
ARTIFACT_NAMESPACE = "prebreakout_discovery_v1/"
TRIAL_BUDGET_MAX = 8
TRIAL_COST_PER_MATERIAL_VARIANT = 1

SMOKE_ACCEPTANCE_WEIGHT = 0
SMOKE_SPECIAL_CASE_BRANCHING = "FORBIDDEN"
SMOKE_REQUIRED_REFERENCE = "FLAG_AT_OR_BEFORE_B_MINUS_1_OR_DETERMINISTIC_EXCLUSION"

SMOKE_EXCLUSION_REASON_CODES = (
    "NON_US_LISTING",
    "NON_COMMON_EQUITY",
    "NON_PRIMARY_LISTING",
    "AMBIGUOUS_PRIMARY_LISTING",
    "NOT_ACTIVE_TRADABLE",
    "CORPORATE_ACTION_UNRESOLVED",
    "CORPORATE_ACTION_TERMINAL_EFFECTIVE",
    "NOT_IN_DATE_LOCAL_SOURCE_POPULATION",
)

SMOKE_UNAVAILABLE_REASON_CODES = (
    "BREAKOUT_CONTRACT_UNBOUND",
    "B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE",
    "IDENTITY_UNBOUND",
)

FALSIFIER_SPECS = (
    {
        "falsifier_id": "PIT_OR_CUSTODY_BREACH",
        "class": "INVALIDATION",
        "trigger": "ANY future leakage, survivor back-projection, identity fallback, unresolved corporate-action substitution, prediction-after-label, or mutable outcome authority",
    },
    {
        "falsifier_id": "SEARCH_CONTAMINATION_OR_BUDGET_BREACH",
        "class": "INVALIDATION",
        "trigger": "material variant inspected without a charged Trial-Ledger entry or cumulative material trials > 8",
    },
    {
        "falsifier_id": "NO_RIGHT_TAIL_ENRICHMENT",
        "class": "ECONOMIC",
        "trigger": "untouched primary 20d prebreakout Recall/Lift is <= breadth-matched baseline",
    },
    {
        "falsifier_id": "NO_POSITIVE_PREBREAKOUT_LEAD",
        "class": "ECONOMIC",
        "trigger": "eligible true-winner episodes have median effective TTFLD <= 0 sessions",
    },
    {
        "falsifier_id": "CATASTROPHIC_FALSE_WINNER_NOT_IMPROVED",
        "class": "ECONOMIC",
        "trigger": "bottom-5%-return false-winner rate is >= the preregistered matched-control rate on untouched evaluation",
    },
    {
        "falsifier_id": "NO_INCREMENTAL_I_PLUS_X",
        "class": "ECONOMIC",
        "trigger": "I+X preregistered net utility is <= incumbent I on untouched evaluation",
    },
    {
        "falsifier_id": "PROSPECTIVE_EFFECT_FAILS",
        "class": "ECONOMIC",
        "trigger": "prospective eligible winner episodes fail to retain positive ex-ante lead/right-tail enrichment under the frozen evaluator",
    },
    {
        "falsifier_id": "INDEPENDENT_REPLICATION_FAILS",
        "class": "ECONOMIC",
        "trigger": "quarantined identity/PIT/license replication does not reproduce the frozen-direction prebreakout effect",
    },
)

SEARCH_CHARGE_FIELDS = (
    "feature_family_or_representation",
    "transform_or_window_variant",
    "model_class",
    "hyperparameter_set",
    "training_window",
    "calibration_method",
    "ranking_threshold_or_top_k",
    "control_definition",
    "cross_sectional_holdout_definition",
)

NEW_VERSION_FIELDS = (
    "risk_set_semantics",
    "primary_horizon",
    "primary_outcome_label",
    "breakout_B_definition",
    "TTFLD_law",
    "winner_fraction",
    "material_economic_mechanism",
    "falsifier_constitution",
    "search_budget",
)


def contract_snapshot() -> dict[str, Any]:
    return {
        "schema_version": CONTRACT_SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "secondary_label_spec_id": SECONDARY_LABEL_SPEC_ID,
        "breakout": {
            "spec_id": BREAKOUT_SPEC_ID,
            "close_semantics": BREAKOUT_CLOSE_SEMANTICS,
            "lookback_sessions": BREAKOUT_LOOKBACK_SESSIONS,
            "episode_cooldown_sessions": BREAKOUT_EPISODE_COOLDOWN_SESSIONS,
            "comparator": BREAKOUT_COMPARATOR,
        },
        "horizons": {
            "primary_sessions": PRIMARY_HORIZON_SESSIONS,
            "secondary_sessions": SECONDARY_HORIZON_SESSIONS,
            "winner_fraction": WINNER_FRACTION,
            "winner_count_law": WINNER_COUNT_LAW,
            "forward_return_law": FORWARD_RETURN_LAW,
            "winner_tie_break": WINNER_TIE_BREAK,
            "incomplete_horizon_law": INCOMPLETE_HORIZON_LAW,
        },
        "ttfld": {
            "spec_id": TTFLD_SPEC_ID,
            "lead_lookback_sessions": LEAD_LOOKBACK_SESSIONS,
            "minimum_legitimate_lead_sessions": MIN_LEGITIMATE_LEAD_SESSIONS,
            "missed_effective_sessions": MISSED_TTFLD_EFFECTIVE_SESSIONS,
        },
        "search": {
            "search_family_id": SEARCH_FAMILY_ID,
            "trial_ledger_scope": TRIAL_LEDGER_SCOPE,
            "prediction_ledger_scope": PREDICTION_LEDGER_SCOPE,
            "artifact_namespace": ARTIFACT_NAMESPACE,
            "trial_budget_max": TRIAL_BUDGET_MAX,
            "trial_cost_per_material_variant": TRIAL_COST_PER_MATERIAL_VARIANT,
            "charged_fields": list(SEARCH_CHARGE_FIELDS),
            "new_version_fields": list(NEW_VERSION_FIELDS),
        },
        "smoke": {
            "acceptance_weight": SMOKE_ACCEPTANCE_WEIGHT,
            "special_case_branching": SMOKE_SPECIAL_CASE_BRANCHING,
            "required_reference": SMOKE_REQUIRED_REFERENCE,
            "deterministic_exclusion_reason_codes": list(SMOKE_EXCLUSION_REASON_CODES),
            "deterministic_unavailable_reason_codes": list(SMOKE_UNAVAILABLE_REASON_CODES),
            "deterministic_unavailable_satisfies_obligation": False,
        },
        "falsifiers": list(FALSIFIER_SPECS),
        "authority": {
            "provider_capture": "NOT_AUTHORIZED_BY_W2",
            "outcome_open": "FORBIDDEN",
            "prospective_clock_start": "FORBIDDEN_UNTIL_W3_W4_W5_W6_GATES",
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
        },
    }


def hash_safe(value: Any) -> Any:
    """Normalize numeric scalars for the repository's strict canonical hasher."""

    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, Mapping):
        return {str(key): hash_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [hash_safe(item) for item in value]
    raise ValueError(f"prebreakout_hash_value_type_unsupported:{type(value).__name__}")


CONTRACT_SHA256 = domain_hash("PREBREAKOUT_DISCOVERY_V1:W2_CONTRACT", hash_safe(contract_snapshot()))


def validate_contract() -> None:
    if FAMILY_ID != "PREBREAKOUT_DISCOVERY_v1":
        raise ValueError("prebreakout_family_id_drift")
    if RISK_SET_SPEC_ID != "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1":
        raise ValueError("prebreakout_risk_set_spec_id_drift")
    if PRIMARY_LABEL_SPEC_ID != "PREBREAKOUT_RIGHT_TAIL_20D_TOP5_V1":
        raise ValueError("prebreakout_primary_label_spec_id_drift")
    if SECONDARY_LABEL_SPEC_ID != "PREBREAKOUT_RIGHT_TAIL_10D_TOP5_V1":
        raise ValueError("prebreakout_secondary_label_spec_id_drift")
    if BREAKOUT_SPEC_ID != "PREBREAKOUT_ALGORITHMIC_BREAKOUT_B_20D_HIGH_V1":
        raise ValueError("prebreakout_breakout_spec_id_drift")
    if BREAKOUT_CLOSE_SEMANTICS != "PIT_CORPORATE_ACTION_NORMALIZED_PRIMARY_LISTING_CLOSE_AS_OF_SESSION":
        raise ValueError("prebreakout_breakout_close_semantics_drift")
    if (PRIMARY_HORIZON_SESSIONS, SECONDARY_HORIZON_SESSIONS) != (20, 10):
        raise ValueError("prebreakout_horizon_drift")
    if WINNER_FRACTION != 0.05:
        raise ValueError("prebreakout_winner_fraction_drift")
    if WINNER_COUNT_LAW != "CEIL_WINNER_FRACTION_TIMES_DATE_LOCAL_RISK_SET_COUNT":
        raise ValueError("prebreakout_winner_count_law_drift")
    if FORWARD_RETURN_LAW != "COMPOUND_NEXT_H_OBSERVED_PRIMARY_LISTING_SESSIONS_AFTER_DECISION":
        raise ValueError("prebreakout_forward_return_law_drift")
    if WINNER_TIE_BREAK != "FORWARD_TOTAL_RETURN_DESC_SECURITY_ID_ASC_TRADING_ITEM_ID_ASC":
        raise ValueError("prebreakout_winner_tie_break_drift")
    if (BREAKOUT_LOOKBACK_SESSIONS, BREAKOUT_EPISODE_COOLDOWN_SESSIONS) != (20, 20):
        raise ValueError("prebreakout_breakout_B_drift")
    if BREAKOUT_COMPARATOR != "STRICT_GT_PRIOR_20_SESSION_HIGH":
        raise ValueError("prebreakout_breakout_comparator_drift")
    if (LEAD_LOOKBACK_SESSIONS, MIN_LEGITIMATE_LEAD_SESSIONS, MISSED_TTFLD_EFFECTIVE_SESSIONS) != (20, 1, 0):
        raise ValueError("prebreakout_ttfld_drift")
    if TTFLD_SPEC_ID != "PREBREAKOUT_TTFLD_BOUNDED_20_TO_B_MINUS_1_V1":
        raise ValueError("prebreakout_ttfld_spec_id_drift")
    if SEARCH_FAMILY_ID != "PREBREAKOUT_SEARCH_v1":
        raise ValueError("prebreakout_search_family_id_drift")
    if TRIAL_LEDGER_SCOPE != "PREBREAKOUT_V1_TRIAL_LEDGER":
        raise ValueError("prebreakout_trial_ledger_scope_drift")
    if PREDICTION_LEDGER_SCOPE != "PREBREAKOUT_V1_PREDICTION_LEDGER":
        raise ValueError("prebreakout_prediction_ledger_scope_drift")
    if ARTIFACT_NAMESPACE != "prebreakout_discovery_v1/":
        raise ValueError("prebreakout_artifact_namespace_drift")
    if TRIAL_BUDGET_MAX != 8 or TRIAL_COST_PER_MATERIAL_VARIANT != 1:
        raise ValueError("prebreakout_search_budget_drift")
    if SMOKE_ACCEPTANCE_WEIGHT != 0 or SMOKE_SPECIAL_CASE_BRANCHING != "FORBIDDEN":
        raise ValueError("prebreakout_smoke_policy_drift")
    if SMOKE_REQUIRED_REFERENCE != "FLAG_AT_OR_BEFORE_B_MINUS_1_OR_DETERMINISTIC_EXCLUSION":
        raise ValueError("prebreakout_smoke_reference_law_drift")
    if SMOKE_EXCLUSION_REASON_CODES != (
        "NON_US_LISTING",
        "NON_COMMON_EQUITY",
        "NON_PRIMARY_LISTING",
        "AMBIGUOUS_PRIMARY_LISTING",
        "NOT_ACTIVE_TRADABLE",
        "CORPORATE_ACTION_UNRESOLVED",
        "CORPORATE_ACTION_TERMINAL_EFFECTIVE",
        "NOT_IN_DATE_LOCAL_SOURCE_POPULATION",
    ):
        raise ValueError("prebreakout_smoke_exclusion_vocabulary_drift")
    if SMOKE_UNAVAILABLE_REASON_CODES != (
        "BREAKOUT_CONTRACT_UNBOUND",
        "B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE",
        "IDENTITY_UNBOUND",
    ):
        raise ValueError("prebreakout_smoke_unavailable_vocabulary_drift")
    expected_falsifier_ids = (
        "PIT_OR_CUSTODY_BREACH",
        "SEARCH_CONTAMINATION_OR_BUDGET_BREACH",
        "NO_RIGHT_TAIL_ENRICHMENT",
        "NO_POSITIVE_PREBREAKOUT_LEAD",
        "CATASTROPHIC_FALSE_WINNER_NOT_IMPROVED",
        "NO_INCREMENTAL_I_PLUS_X",
        "PROSPECTIVE_EFFECT_FAILS",
        "INDEPENDENT_REPLICATION_FAILS",
    )
    if tuple(item.get("falsifier_id") for item in FALSIFIER_SPECS) != expected_falsifier_ids:
        raise ValueError("prebreakout_falsifier_identity_drift")
    expected = domain_hash("PREBREAKOUT_DISCOVERY_V1:W2_CONTRACT", hash_safe(contract_snapshot()))
    if CONTRACT_SHA256 != expected:
        raise ValueError("prebreakout_contract_hash_drift")
