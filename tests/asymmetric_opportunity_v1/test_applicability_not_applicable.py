from __future__ import annotations

import pandas as pd

from research.asymmetric_opportunity_v1.applicability import (
    APPLICABLE_OBSERVED,
    APPLICABLE_UNOBSERVED,
    CLAIM_SCOPE_DOMAIN_LIMITED_EX_ANTE,
    NOT_APPLICABLE,
    W3_INELIGIBLE,
    applicable_system_fill_population,
    build_applicability_frame,
    classify_applicability,
    domain_limited_ex_ante_claim,
    law_semantics,
)


def test_not_applicable_is_not_missingness_or_k_consumer() -> None:
    law = law_semantics()
    assert law["not_applicable_is_missingness"] is False
    assert law["not_applicable_is_strategy_abstention"] is False
    assert law["not_applicable_consumes_k_t"] is False
    assert law["not_applicable_creates_kernel_cash_drag_narrative"] is False
    assert law["full_w3_denominator_rewrite"] == "FORBIDDEN"


def test_classify_matrix() -> None:
    assert (
        classify_applicability(
            in_full_w3=False, in_kernel_claim_domain=True, kernel_feature_observed=True
        )
        == W3_INELIGIBLE
    )
    assert (
        classify_applicability(
            in_full_w3=True, in_kernel_claim_domain=False, kernel_feature_observed=True
        )
        == NOT_APPLICABLE
    )
    assert (
        classify_applicability(
            in_full_w3=True, in_kernel_claim_domain=True, kernel_feature_observed=True
        )
        == APPLICABLE_OBSERVED
    )
    assert (
        classify_applicability(
            in_full_w3=True, in_kernel_claim_domain=True, kernel_feature_observed=False
        )
        == APPLICABLE_UNOBSERVED
    )


def test_frame_preserves_rows_and_not_applicable_out_of_domain() -> None:
    w3 = pd.DataFrame(
        [
            ("2026-01-02", "CIQSEC:A"),
            ("2026-01-02", "CIQSEC:B"),
            ("2026-01-02", "CIQSEC:C"),
        ],
        columns=["decision_date", "security_id"],
    )
    domain = {("2026-01-02", "CIQSEC:A"), ("2026-01-02", "CIQSEC:B")}
    observed = {("2026-01-02", "CIQSEC:A")}
    out = build_applicability_frame(
        w3,
        kernel_claim_domain_keys=domain,
        observed_keys=observed,
    )
    assert len(out) == 3
    assert out["applicability_state"].tolist() == [
        APPLICABLE_OBSERVED,
        APPLICABLE_UNOBSERVED,
        NOT_APPLICABLE,
    ]
    assert out["applicability_action"].tolist() == [
        "CANDIDATE",
        "ABSTAIN",
        "OUT_OF_DOMAIN",
    ]


def test_not_applicable_not_in_fill_pool() -> None:
    parts = applicable_system_fill_population(
        {
            ("d", "a"): APPLICABLE_OBSERVED,
            ("d", "b"): APPLICABLE_UNOBSERVED,
            ("d", "c"): NOT_APPLICABLE,
        }
    )
    assert ("d", "a") in parts["select_pool_APPLICABLE_OBSERVED"]
    assert ("d", "c") in parts["not_candidate_NOT_APPLICABLE"]
    assert ("d", "c") in parts["not_backfill_pool_NOT_APPLICABLE"]


def test_domain_limited_ex_ante() -> None:
    claim = domain_limited_ex_ante_claim(
        domains=["banks_if_q_roic_economics_require"],
        rationale="ROIC economics not defined for regulated bank book v1.2",
    )
    assert claim["claim_scope"] == CLAIM_SCOPE_DOMAIN_LIMITED_EX_ANTE
    assert claim["outcome_conditioned"] is False
    assert claim["post_label_exception"] == "FORBIDDEN"
