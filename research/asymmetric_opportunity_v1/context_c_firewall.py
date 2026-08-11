"""OK-SBI-0 Context C firewall — allowlist only; never in arm score / K fill."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


C_FIREWALL_ID = "ContextCFirewallV1"

C_ALLOWLIST = (
    "decision_date_block",
    "sector_group",
    "market_cap_bucket",
    "liquidity_bucket",
    "ipo_age_bucket",
    "volatility_bucket",
    "drawdown_bucket",
    "distress_bucket",
    "corporate_action_state",
)

C_FORBIDDEN_USES = (
    "arm_score",
    "q_rank",
    "m_rank",
    "k_t_fill",
    "applicability_rewrite",
    "threshold_selection",
    "domain_router_discovery",
    "position_sizing",
    "cost_lag_choice",
)

# Post-S2 reporting hooks only — implement now, do not run outcome-bearing C adjust.
C_FUTURE_REPORTING_HOOKS = (
    "unadjusted_paired_result",
    "c_adjusted_diagnostic_result",
    "difference",
)


def firewall_semantics() -> dict[str, Any]:
    return {
        "firewall_id": C_FIREWALL_ID,
        "slice_id": "OK-SBI-0",
        "allowlist": list(C_ALLOWLIST),
        "forbidden_uses": list(C_FORBIDDEN_USES),
        "future_reporting_hooks": list(C_FUTURE_REPORTING_HOOKS),
        "promotion_may_rely_on_c_adjusted_alone": False,
        "outcome_blind_buckets_only": True,
        "source_bound_buckets_only": True,
    }


def assert_c_keys_allowed(keys: Iterable[str]) -> None:
    allow = set(C_ALLOWLIST)
    bad = [k for k in keys if k not in allow]
    if bad:
        raise ValueError(f"ok_sbi_0_c_key_not_allowlisted:{sorted(bad)}")


def assert_c_not_used_for(use: str) -> None:
    if use in C_FORBIDDEN_USES:
        raise ValueError(f"ok_sbi_0_c_forbidden_use:{use}")


def validate_c_payload(payload: Mapping[str, Any], *, intended_use: str) -> dict[str, Any]:
    """Validate a C context payload is allowlisted and not used for forbidden purposes."""

    assert_c_keys_allowed(payload.keys())
    if intended_use in C_FORBIDDEN_USES:
        raise ValueError(f"ok_sbi_0_c_forbidden_use:{intended_use}")
    return {
        "accepted": True,
        "keys": sorted(payload.keys()),
        "intended_use": intended_use,
        "firewall_id": C_FIREWALL_ID,
    }


def future_reporting_hook_stubs() -> dict[str, Any]:
    """Hooks for post-S2 C-adjusted diagnostics — not runnable this turn."""

    return {
        name: {
            "status": "HOOK_ONLY_NOT_RUN",
            "runnable_evaluation": False,
            "requires": "OK-SBI-0-DEV-OPEN-1 + post-S2 protocol",
        }
        for name in C_FUTURE_REPORTING_HOOKS
    }
