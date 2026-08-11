from __future__ import annotations

import pytest

from research.asymmetric_opportunity_v1.context_c_firewall import (
    C_ALLOWLIST,
    C_FORBIDDEN_USES,
    assert_c_keys_allowed,
    assert_c_not_used_for,
    firewall_semantics,
    future_reporting_hook_stubs,
    validate_c_payload,
)


def test_allowlist_and_forbidden_uses_frozen() -> None:
    sem = firewall_semantics()
    assert set(sem["allowlist"]) == set(C_ALLOWLIST)
    assert "arm_score" in C_FORBIDDEN_USES
    assert "k_t_fill" in C_FORBIDDEN_USES
    assert "applicability_rewrite" in C_FORBIDDEN_USES
    assert sem["promotion_may_rely_on_c_adjusted_alone"] is False


def test_reject_non_allowlisted_key() -> None:
    with pytest.raises(ValueError, match="c_key_not_allowlisted"):
        assert_c_keys_allowed(["sector_group", "secret_router_feature"])


def test_reject_forbidden_use() -> None:
    for use in ("arm_score", "q_rank", "k_t_fill", "position_sizing"):
        with pytest.raises(ValueError, match="c_forbidden_use"):
            assert_c_not_used_for(use)


def test_validate_payload_happy_path() -> None:
    out = validate_c_payload(
        {"sector_group": "TECH", "market_cap_bucket": "LARGE"},
        intended_use="diagnostic_stratification",
    )
    assert out["accepted"] is True


def test_future_hooks_not_run() -> None:
    hooks = future_reporting_hook_stubs()
    assert hooks["c_adjusted_diagnostic_result"]["status"] == "HOOK_ONLY_NOT_RUN"
    assert hooks["c_adjusted_diagnostic_result"]["runnable_evaluation"] is False
