from __future__ import annotations

from dataclasses import dataclass

from opportunity_engine.source_classes import ConfidenceLabel, SignalFamily, SourceClass
from opportunity_engine.states import OpportunityState, ReasonCode


@dataclass(frozen=True)
class SignalPolicy:
    signal_family: SignalFamily
    source_class: SourceClass
    observed_estimated_inferred: str
    allowed_reason_codes: frozenset[ReasonCode]
    allowed_state_influence: frozenset[OpportunityState]
    forbidden_state_influence: frozenset[OpportunityState]
    freshness_requirement: str
    confidence_label: ConfidenceLabel
    provider_gap: bool = False
    notes: str = ""


ACTION_STATES = frozenset(
    {
        OpportunityState.BUYING_RANGE,
        OpportunityState.ADD_ON_SETUP,
        OpportunityState.LET_WINNER_RUN,
    }
)

ALL_STATES = frozenset(OpportunityState)

SIGNAL_POLICIES: dict[SignalFamily, SignalPolicy] = {
    SignalFamily.SUPERCYCLE_THESIS: SignalPolicy(
        signal_family=SignalFamily.SUPERCYCLE_THESIS,
        source_class=SourceClass.INFERRED_RESEARCH,
        observed_estimated_inferred="inferred",
        allowed_reason_codes=frozenset({ReasonCode.THESIS_EVIDENCE}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.THEME_WATCH,
                OpportunityState.THESIS_CANDIDATE,
                OpportunityState.EVIDENCE_BUILDING,
            }
        ),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="manual thesis evidence as-of date required",
        confidence_label=ConfidenceLabel.INFERRED_RESEARCH_ONLY,
        notes="Supports thesis quality only; cannot create action states alone.",
    ),
    SignalFamily.SEC_FILINGS_OWNERSHIP: SignalPolicy(
        signal_family=SignalFamily.SEC_FILINGS_OWNERSHIP,
        source_class=SourceClass.OBSERVED_OFFICIAL,
        observed_estimated_inferred="observed",
        allowed_reason_codes=frozenset({ReasonCode.THESIS_EVIDENCE, ReasonCode.OWNERSHIP_WHALE_CONTEXT}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.EVIDENCE_BUILDING,
                OpportunityState.CONFIRMATION_WATCH,
                OpportunityState.LET_WINNER_RUN,
                OpportunityState.EXIT_RISK,
                OpportunityState.THESIS_BROKEN,
            }
        ),
        forbidden_state_influence=frozenset({OpportunityState.BUYING_RANGE, OpportunityState.ADD_ON_SETUP}),
        freshness_requirement="filing-lagged as-of filing date and accession required",
        confidence_label=ConfidenceLabel.OBSERVED_CONTEXT,
        notes="Official filings support thesis and ownership context, not rankings or alerts.",
    ),
    SignalFamily.FINRA_SHORT_INTEREST: SignalPolicy(
        signal_family=SignalFamily.FINRA_SHORT_INTEREST,
        source_class=SourceClass.OBSERVED_OFFICIAL,
        observed_estimated_inferred="observed",
        allowed_reason_codes=frozenset({ReasonCode.SHORT_SQUEEZE_BASE}),
        allowed_state_influence=frozenset({OpportunityState.EVIDENCE_BUILDING, OpportunityState.CROWDED_FROTHY}),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="twice-monthly settlement date and publication lag required",
        confidence_label=ConfidenceLabel.OBSERVED_CONTEXT,
        notes="Squeeze-base context only; not real-time squeeze ignition.",
    ),
    SignalFamily.CFTC_TFF_POSITIONING: SignalPolicy(
        signal_family=SignalFamily.CFTC_TFF_POSITIONING,
        source_class=SourceClass.OBSERVED_OFFICIAL,
        observed_estimated_inferred="observed",
        allowed_reason_codes=frozenset({ReasonCode.CTA_SYSTEMATIC_CONTEXT}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.EVIDENCE_BUILDING,
                OpportunityState.CONFIRMATION_WATCH,
                OpportunityState.CROWDED_FROTHY,
            }
        ),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="weekly report date plus Tuesday as-of position date required",
        confidence_label=ConfidenceLabel.OBSERVED_CONTEXT,
        notes="Broad regime/positioning context only, not single-name CTA buying.",
    ),
    SignalFamily.FRED_MACRO_LIQUIDITY: SignalPolicy(
        signal_family=SignalFamily.FRED_MACRO_LIQUIDITY,
        source_class=SourceClass.OBSERVED_OFFICIAL,
        observed_estimated_inferred="observed",
        allowed_reason_codes=frozenset({ReasonCode.MACRO_LIQUIDITY_CONTEXT}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.THEME_WATCH,
                OpportunityState.EVIDENCE_BUILDING,
                OpportunityState.CONFIRMATION_WATCH,
                OpportunityState.CROWDED_FROTHY,
            }
        ),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="series as-of date, realtime vintage, and live API-key policy required",
        confidence_label=ConfidenceLabel.OBSERVED_CONTEXT,
        notes="Macro context only; not alpha evidence or macro score.",
    ),
    SignalFamily.KEN_FRENCH_FACTOR_CONTEXT: SignalPolicy(
        signal_family=SignalFamily.KEN_FRENCH_FACTOR_CONTEXT,
        source_class=SourceClass.OBSERVED_OFFICIAL,
        observed_estimated_inferred="observed",
        allowed_reason_codes=frozenset({ReasonCode.FACTOR_REGIME_CONTEXT}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.THEME_WATCH,
                OpportunityState.EVIDENCE_BUILDING,
                OpportunityState.CONFIRMATION_WATCH,
                OpportunityState.CROWDED_FROTHY,
            }
        ),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="factor dataset date and library citation required",
        confidence_label=ConfidenceLabel.OBSERVED_CONTEXT,
        notes="Factor context only; not alpha evidence or candidate ranking.",
    ),
    SignalFamily.PRICE_VOLUME_BEHAVIOR: SignalPolicy(
        signal_family=SignalFamily.PRICE_VOLUME_BEHAVIOR,
        source_class=SourceClass.OBSERVED_CANONICAL,
        observed_estimated_inferred="observed",
        allowed_reason_codes=frozenset({ReasonCode.PRICE_VOLUME_BEHAVIOR}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.LEFT_SIDE_RISK,
                OpportunityState.ACCUMULATION_WATCH,
                OpportunityState.CONFIRMATION_WATCH,
                OpportunityState.BUYING_RANGE,
                OpportunityState.ADD_ON_SETUP,
                OpportunityState.LET_WINNER_RUN,
                OpportunityState.TRIM_OPTIONAL,
                OpportunityState.CROWDED_FROTHY,
                OpportunityState.EXIT_RISK,
            }
        ),
        forbidden_state_influence=frozenset({OpportunityState.THESIS_BROKEN}),
        freshness_requirement="canonical daily as-of date and manifest required",
        confidence_label=ConfidenceLabel.CANONICAL_BEHAVIOR,
        notes="Can influence state only with reason/source metadata; never emits orders.",
    ),
    SignalFamily.ROTATION_SCORE: SignalPolicy(
        signal_family=SignalFamily.ROTATION_SCORE,
        source_class=SourceClass.ESTIMATED_MODEL,
        observed_estimated_inferred="estimated",
        allowed_reason_codes=frozenset({ReasonCode.ROTATION_CONTEXT}),
        allowed_state_influence=frozenset(
            {
                OpportunityState.THEME_WATCH,
                OpportunityState.EVIDENCE_BUILDING,
                OpportunityState.CONFIRMATION_WATCH,
                OpportunityState.CROWDED_FROTHY,
            }
        ),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="model as-of date, input manifest, and confidence label required",
        confidence_label=ConfidenceLabel.ESTIMATED_CONTEXT,
        notes="May modify confidence, but cannot alone create action states.",
    ),
    SignalFamily.RISK_INVALIDATION: SignalPolicy(
        signal_family=SignalFamily.RISK_INVALIDATION,
        source_class=SourceClass.INFERRED_RESEARCH,
        observed_estimated_inferred="inferred",
        allowed_reason_codes=frozenset({ReasonCode.RISK_INVALIDATION}),
        allowed_state_influence=frozenset({OpportunityState.EXIT_RISK, OpportunityState.THESIS_BROKEN}),
        forbidden_state_influence=frozenset(
            {
                OpportunityState.BUYING_RANGE,
                OpportunityState.ADD_ON_SETUP,
                OpportunityState.LET_WINNER_RUN,
            }
        ),
        freshness_requirement="contradiction/invalidation evidence as-of date required",
        confidence_label=ConfidenceLabel.INFERRED_RESEARCH_ONLY,
        notes="Can block or break a thesis; cannot create bullish action states.",
    ),
}

for family in (
    SignalFamily.IV_VOL_INTELLIGENCE,
    SignalFamily.OPTIONS_WHALE_RADAR,
    SignalFamily.GAMMA_DEALER_MAP,
    SignalFamily.ETF_PASSIVE_FLOW,
    SignalFamily.DARK_POOL_BLOCK_RADAR,
    SignalFamily.MICROSTRUCTURE_LIQUIDITY,
    SignalFamily.NEWS_NARRATIVE_VELOCITY,
):
    SIGNAL_POLICIES[family] = SignalPolicy(
        signal_family=family,
        source_class=SourceClass.OBSERVED_LICENSED
        if family
        in {
            SignalFamily.IV_VOL_INTELLIGENCE,
            SignalFamily.ETF_PASSIVE_FLOW,
            SignalFamily.MICROSTRUCTURE_LIQUIDITY,
        }
        else SourceClass.ESTIMATED_MODEL,
        observed_estimated_inferred="observed"
        if family
        in {
            SignalFamily.ETF_PASSIVE_FLOW,
            SignalFamily.MICROSTRUCTURE_LIQUIDITY,
        }
        else "estimated",
        allowed_reason_codes=frozenset(
            {
                ReasonCode.IV_VOL_BEHAVIOR
                if family == SignalFamily.IV_VOL_INTELLIGENCE
                else ReasonCode.OPTIONS_WHALE_BEHAVIOR
                if family in {SignalFamily.OPTIONS_WHALE_RADAR, SignalFamily.GAMMA_DEALER_MAP}
                else ReasonCode.ROTATION_CONTEXT
                if family == SignalFamily.ETF_PASSIVE_FLOW
                else ReasonCode.PRICE_VOLUME_BEHAVIOR
                if family in {SignalFamily.DARK_POOL_BLOCK_RADAR, SignalFamily.MICROSTRUCTURE_LIQUIDITY}
                else ReasonCode.THESIS_EVIDENCE
            }
        ),
        allowed_state_influence=frozenset({OpportunityState.EVIDENCE_BUILDING}),
        forbidden_state_influence=ACTION_STATES,
        freshness_requirement="licensed provider decision and source policy required before state advancement",
        confidence_label=ConfidenceLabel.LICENSED_REQUIRED,
        provider_gap=True,
        notes="Provider-gap signal family held from action-state influence in G7.3.",
    )


def policy_for(signal_family: SignalFamily) -> SignalPolicy:
    return SIGNAL_POLICIES[signal_family]


def can_influence_state(signal_family: SignalFamily, state: OpportunityState) -> bool:
    policy = policy_for(signal_family)
    return state in policy.allowed_state_influence and state not in policy.forbidden_state_influence


def tier2_can_move_to_action_state() -> bool:
    return False
