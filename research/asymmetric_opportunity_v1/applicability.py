"""OK-SBI-0 applicability law — NOT_APPLICABLE is not missingness.

Applicability is an outcome-blind domain statement.  It never rewrites the
full-W3 denominator, never consumes K_t, and never creates a cash-drag narrative
for names outside the kernel claim domain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Set

import pandas as pd


W3_INELIGIBLE = "W3_INELIGIBLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
APPLICABLE_OBSERVED = "APPLICABLE_OBSERVED"
APPLICABLE_UNOBSERVED = "APPLICABLE_UNOBSERVED"

APPLICABILITY_STATES = frozenset(
    {
        W3_INELIGIBLE,
        NOT_APPLICABLE,
        APPLICABLE_OBSERVED,
        APPLICABLE_UNOBSERVED,
    }
)

CLAIM_SCOPE_DOMAIN_LIMITED_EX_ANTE = "DOMAIN_LIMITED_EX_ANTE"

# Outcome-blind ex-ante domain limitations (not post-label carve-outs).
DEFAULT_EX_ANTE_DOMAIN_LIMITS: tuple[str, ...] = (
    "banks_if_q_roic_economics_require",
    "insurers_if_q_roic_economics_require",
)


@dataclass(frozen=True)
class ApplicabilityLawV1:
    """Frozen semantics for applicability vs missingness."""

    law_id: str = "ApplicabilityLawV1"
    slice_id: str = "OK-SBI-0"
    not_applicable_is_missingness: bool = False
    not_applicable_is_strategy_abstention: bool = False
    not_applicable_consumes_k_t: bool = False
    not_applicable_creates_kernel_cash_drag_narrative: bool = False
    not_applicable_is_backfill_pool: bool = False
    not_applicable_is_candidate: bool = False
    applicable_unobserved_action: str = "ABSTAIN"
    applicable_unobserved_unfilled_breadth: str = "ECONOMIC_CASH"
    applicable_unobserved_counts_in: tuple[str, ...] = (
        "foregone_right_tail_attribution",
        "avoided_catastrophe_attribution",
    )
    claim_scope_allowed: tuple[str, ...] = (CLAIM_SCOPE_DOMAIN_LIMITED_EX_ANTE,)
    full_w3_denominator_rewrite: str = "FORBIDDEN"
    outcome_conditioned_domain_discovery: str = "FORBIDDEN"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_applicability(
    *,
    in_full_w3: bool,
    in_kernel_claim_domain: bool,
    kernel_feature_observed: bool,
) -> str:
    """Map W3 membership + domain + observability into one applicability state."""

    if not in_full_w3:
        return W3_INELIGIBLE
    if not in_kernel_claim_domain:
        return NOT_APPLICABLE
    if kernel_feature_observed:
        return APPLICABLE_OBSERVED
    return APPLICABLE_UNOBSERVED


def assert_not_applicable_is_not_missingness(state: str) -> None:
    if state == NOT_APPLICABLE:
        # Structural assertion for callers / tests.
        law = ApplicabilityLawV1()
        assert law.not_applicable_is_missingness is False
        assert law.not_applicable_consumes_k_t is False
        assert law.not_applicable_is_strategy_abstention is False


def build_applicability_frame(
    w3_rows: pd.DataFrame,
    *,
    kernel_claim_domain_keys: Set[tuple[str, str]],
    observed_keys: Set[tuple[str, str]],
    key_cols: tuple[str, str] = ("decision_date", "security_id"),
) -> pd.DataFrame:
    """Left-preserve W3 rows and attach applicability without row deletion.

    Names present in `w3_rows` are treated as full-W3 opportunity census members.
    Domain membership is outcome-blind and must be predeclared.
    """

    required = set(key_cols)
    missing = required - set(w3_rows.columns)
    if missing:
        raise ValueError(f"ok_sbi_0_applicability_columns_missing:{sorted(missing)}")

    out = w3_rows.copy()
    states: list[str] = []
    actions: list[str] = []
    for row in out.itertuples(index=False):
        key = (str(getattr(row, key_cols[0])), str(getattr(row, key_cols[1])))
        in_domain = key in kernel_claim_domain_keys
        observed = key in observed_keys
        state = classify_applicability(
            in_full_w3=True,
            in_kernel_claim_domain=in_domain,
            kernel_feature_observed=observed,
        )
        states.append(state)
        if state == APPLICABLE_OBSERVED:
            actions.append("CANDIDATE")
        elif state == APPLICABLE_UNOBSERVED:
            actions.append("ABSTAIN")
        elif state == NOT_APPLICABLE:
            actions.append("OUT_OF_DOMAIN")
        else:
            actions.append("W3_INELIGIBLE")

    out["applicability_state"] = states
    out["applicability_action"] = actions
    if len(out) != len(w3_rows):
        raise AssertionError("ok_sbi_0_applicability_row_loss")
    return out


def domain_limited_ex_ante_claim(
    *,
    domains: Iterable[str] | None = None,
    rationale: str,
) -> dict[str, Any]:
    """Declare an outcome-blind DOMAIN_LIMITED_EX_ANTE claim scope."""

    declared = tuple(domains) if domains is not None else DEFAULT_EX_ANTE_DOMAIN_LIMITS
    if not rationale.strip():
        raise ValueError("ok_sbi_0_domain_limit_rationale_required")
    return {
        "claim_scope": CLAIM_SCOPE_DOMAIN_LIMITED_EX_ANTE,
        "domains": list(declared),
        "rationale": rationale,
        "outcome_conditioned": False,
        "post_label_exception": "FORBIDDEN",
    }


def applicable_system_fill_population(
    applicability_states: Mapping[tuple[str, str], str],
) -> dict[str, list[tuple[str, str]]]:
    """Partition keys for applicable-system breadth fill law."""

    candidates: list[tuple[str, str]] = []
    abstain: list[tuple[str, str]] = []
    out_of_domain: list[tuple[str, str]] = []
    for key, state in applicability_states.items():
        if state == APPLICABLE_OBSERVED:
            candidates.append(key)
        elif state == APPLICABLE_UNOBSERVED:
            abstain.append(key)
        elif state == NOT_APPLICABLE:
            out_of_domain.append(key)
    return {
        "select_pool_APPLICABLE_OBSERVED": candidates,
        "abstain_APPLICABLE_UNOBSERVED": abstain,
        "not_candidate_NOT_APPLICABLE": out_of_domain,
        "not_abstention_NOT_APPLICABLE": out_of_domain,
        "not_backfill_pool_NOT_APPLICABLE": out_of_domain,
    }


def law_semantics() -> dict[str, Any]:
    return ApplicabilityLawV1().to_dict()
