"""Non-UI claim-boundary tokens for locked PEAD evidence JSON.

These field names and forbidden-use tokens are part of the locked M1B
evidence_policy contract. They live outside views/ so GOV-002 UI-string
scans do not treat schema keys as product-action language.
"""

from __future__ import annotations

EXPECTED_M1B_FORBIDDEN_USE: tuple[str, ...] = (
    "alerts",
    "alpha_claims",
    "broker_or_order_paths",
    "causal_claims",
    "full_factor_alpha_claims",
    "net_performance_claims",
    "population_validity_claims",
    "ranking_or_scoring",
    "recommendations",
    "strategy_promotion",
    "strict_point_in_time_claims",
    "tradability_claims",
)

M1B_FALSE_AUTH_KEYS: tuple[str, ...] = (
    "strategy_promotion_authorized",
    "ranking_or_scoring_authorized",
    "alerts_or_recommendations_authorized",
    "broker_or_order_path_authorized",
)
