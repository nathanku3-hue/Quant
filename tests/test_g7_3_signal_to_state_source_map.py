from __future__ import annotations

from opportunity_engine.signal_policy import ACTION_STATES, SIGNAL_POLICIES, can_influence_state
from opportunity_engine.source_classes import ConfidenceLabel, SignalFamily, SourceClass
from opportunity_engine.states import OpportunityState


EXPECTED_SOURCE_CLASSES = {
    "OBSERVED_OFFICIAL",
    "OBSERVED_CANONICAL",
    "OBSERVED_LICENSED",
    "ESTIMATED_MODEL",
    "INFERRED_RESEARCH",
    "TIER2_DISCOVERY",
    "REJECTED",
}

EXPECTED_SIGNAL_FAMILIES = {
    "SUPERCYCLE_THESIS",
    "SEC_FILINGS_OWNERSHIP",
    "FINRA_SHORT_INTEREST",
    "CFTC_TFF_POSITIONING",
    "FRED_MACRO_LIQUIDITY",
    "KEN_FRENCH_FACTOR_CONTEXT",
    "PRICE_VOLUME_BEHAVIOR",
    "IV_VOL_INTELLIGENCE",
    "OPTIONS_WHALE_RADAR",
    "GAMMA_DEALER_MAP",
    "ROTATION_SCORE",
    "ETF_PASSIVE_FLOW",
    "DARK_POOL_BLOCK_RADAR",
    "MICROSTRUCTURE_LIQUIDITY",
    "NEWS_NARRATIVE_VELOCITY",
    "RISK_INVALIDATION",
}


def test_source_class_enum_complete():
    assert {source.value for source in SourceClass} == EXPECTED_SOURCE_CLASSES


def test_signal_family_map_complete():
    assert {family.value for family in SignalFamily} == EXPECTED_SIGNAL_FAMILIES
    assert set(SIGNAL_POLICIES) == set(SignalFamily)


def test_public_fixtures_are_context_only():
    context_families = {
        SignalFamily.SEC_FILINGS_OWNERSHIP,
        SignalFamily.FINRA_SHORT_INTEREST,
        SignalFamily.CFTC_TFF_POSITIONING,
        SignalFamily.FRED_MACRO_LIQUIDITY,
        SignalFamily.KEN_FRENCH_FACTOR_CONTEXT,
    }

    for family in context_families:
        policy = SIGNAL_POLICIES[family]
        assert policy.source_class == SourceClass.OBSERVED_OFFICIAL
        assert policy.forbidden_state_influence.issuperset(ACTION_STATES - {OpportunityState.LET_WINNER_RUN})
        assert not policy.provider_gap


def test_estimated_signals_do_not_create_buying_range():
    estimated_families = [
        family
        for family, policy in SIGNAL_POLICIES.items()
        if policy.source_class == SourceClass.ESTIMATED_MODEL
    ]

    assert estimated_families
    for family in estimated_families:
        assert not can_influence_state(family, OpportunityState.BUYING_RANGE)


def test_tier2_discovery_cannot_move_to_action_states():
    for policy in SIGNAL_POLICIES.values():
        if policy.source_class == SourceClass.TIER2_DISCOVERY:
            assert policy.forbidden_state_influence.issuperset(ACTION_STATES)

    assert SourceClass.TIER2_DISCOVERY.value == "TIER2_DISCOVERY"


def test_options_iv_gamma_whales_remain_provider_gap():
    for family in {
        SignalFamily.IV_VOL_INTELLIGENCE,
        SignalFamily.OPTIONS_WHALE_RADAR,
        SignalFamily.GAMMA_DEALER_MAP,
    }:
        policy = SIGNAL_POLICIES[family]
        assert policy.provider_gap
        assert policy.confidence_label == ConfidenceLabel.LICENSED_REQUIRED
        assert policy.forbidden_state_influence.issuperset(ACTION_STATES)


def test_short_interest_is_squeeze_base_only():
    policy = SIGNAL_POLICIES[SignalFamily.FINRA_SHORT_INTEREST]

    assert policy.allowed_state_influence == {
        OpportunityState.EVIDENCE_BUILDING,
        OpportunityState.CROWDED_FROTHY,
    }
    assert policy.forbidden_state_influence.issuperset(ACTION_STATES)


def test_cftc_is_broad_regime_only():
    policy = SIGNAL_POLICIES[SignalFamily.CFTC_TFF_POSITIONING]

    assert "not single-name CTA buying" in policy.notes
    assert OpportunityState.BUYING_RANGE in policy.forbidden_state_influence


def test_fred_and_ken_french_are_not_alpha_evidence():
    for family in {SignalFamily.FRED_MACRO_LIQUIDITY, SignalFamily.KEN_FRENCH_FACTOR_CONTEXT}:
        policy = SIGNAL_POLICIES[family]
        assert "not alpha" in policy.notes or "not alpha evidence" in policy.notes
        assert policy.forbidden_state_influence.issuperset(ACTION_STATES)
