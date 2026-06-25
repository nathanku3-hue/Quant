# Supercycle Candidate Card Schema

Status: G8 schema contract
Authority: Phase 65 G8, definition/evidence-card only
Date: 2026-05-10

## Required Top-Level Fields

- `candidate_id`
- `ticker`
- `company_name`
- `theme`
- `supercycle_family_id`
- `candidate_status`
- `created_at`
- `created_by`
- `source_quality_summary`
- `manifest_uri`
- `state_machine_version`
- `primary_alpha`
- `secondary_alpha`
- `state_mapping`
- `risk_discipline`
- `forbidden_outputs`

`candidate_status` must be `candidate_card_only`.

## Source Quality Summary

`source_quality_summary` must include:
- `observed`
- `estimated`
- `inferred`
- `research_only`
- `not_canonical`
- `missing`
- `stale`
- `forbidden`
- `canonical_sources`

`yfinance` must not appear as a canonical source. Tier 2 discovery may be mentioned only as forbidden or not canonical.

## State Mapping

`state_mapping.initial_state` must be one of:
- `THESIS_CANDIDATE`
- `EVIDENCE_BUILDING`

`state_mapping.allowed_next_states` must not include:
- `BUYING_RANGE`
- `ADD_ON_SETUP`
- `LET_WINNER_RUN`
- `TRIM_OPTIONAL`

`state_mapping.forbidden_jumps` must explicitly block those action states.

## Secondary Alpha Boundary

`secondary_alpha.observed_signals_available` must not include estimated-only signals.

`secondary_alpha.blocked_signals_due_to_provider_gap` must explicitly include:
- `IV_VOL_INTELLIGENCE`
- `OPTIONS_WHALE_RADAR`
- `GAMMA_DEALER_MAP`

## Forbidden Outputs

`forbidden_outputs` must set all fields to `true`:
- `no_score`
- `no_rank`
- `no_buy_sell_signal`
- `no_alert`
- `no_broker_action`

The card schema rejects direct score, rank, buy/sell, alert, broker, order, target-price, and buying-range fields outside these negated guardrail flags.
