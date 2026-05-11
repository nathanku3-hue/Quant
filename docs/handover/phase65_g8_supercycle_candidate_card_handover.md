# Phase 65 G8 Handover - One Supercycle Candidate Card

Status: Completed pending validation closeout
Authority: G8 candidate-card-only scope
Date: 2026-05-10

## Executive Summary

G8 creates one human-nominated Supercycle Gem Candidate Card for `MU`.

The card proves that Terminal Zero can represent a thesis candidate as a structured research object after G7.2 state logic, G7.3 source eligibility, and G7.4 dashboard state specs are sealed. It does not search, rank, score, backtest, replay, ingest providers, emit alerts, or call a broker.

## Delivered Scope

- Added candidate-card schema and validator.
- Added one static MU card and manifest.
- Added focused G8 tests for required fields, state limits, forbidden outputs, source quality, yfinance canonical rejection, estimated/observed separation, and provider-gap visibility.
- Added policy and schema docs.

## Deferred Scope

- Alpha search.
- Candidate screening or ranking.
- Backtest or replay.
- Provider ingestion.
- Dashboard runtime.
- Buy/sell alerting.
- Broker calls.

## Logic Chain

Human nomination -> candidate-card schema -> source-quality labels -> state-machine mapping -> forbidden-output validation -> static research object.

## Formula Register

- `g8_card_valid = required_fields_present and manifest_present and initial_state in {THESIS_CANDIDATE,EVIDENCE_BUILDING} and no_action_states and no_score_rank_signal_alert_broker and provider_gaps_explicit`.
- Source paths: `opportunity_engine/candidate_card_schema.py`, `opportunity_engine/candidate_card.py`, `tests/test_g8_supercycle_candidate_card.py`.

## Open Risks / Assumptions / Rollback

Open risks remain inherited: yfinance migration debt, stale sidecar freshness, Reg SHO policy gap, GodView provider gap, options/license gap, and broad compileall workspace hygiene debt.

Assumption: `MU` is the approved default ticker for the first clean established public-company fixture.

Rollback: remove only the G8 candidate-card code, card data, focused tests, G8 docs, handover, SAW report, and G8 context/governance edits. Do not revert G7.2-G7.4 sealed state/source/dashboard work or inherited fixture work.

## Next Phase Roadmap

Recommended next step: G9 one market behavior signal card, likely `FINRA_SHORT_INTEREST_SIGNAL_CARD_V0`, with no search, ranking, scoring, alerts, or provider ingestion.

## New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, and G7.1-G7.4 as inherited baseline truth.
- Created exactly one human-nominated Supercycle Gem Candidate Card for `MU`.
- Added G8 candidate-card schema, validator, static card, manifest, focused tests, policy docs, and handover.
- Proved the research-object workflow without search, ranking, scoring, backtest, replay, provider ingestion, dashboard runtime, alerts, or broker calls.

## What Is Locked
- G8 is candidate-card-only and not an investment recommendation.
- `MU_SUPERCYCLE_CANDIDATE_CARD_V0` may start only as `THESIS_CANDIDATE` or `EVIDENCE_BUILDING`.
- `BUYING_RANGE`, `ADD_ON_SETUP`, `LET_WINNER_RUN`, and `TRIM_OPTIONAL` remain forbidden for G8.
- yfinance cannot be canonical evidence.
- Options/IV/gamma/whale families remain provider-gap signals until licensed/provider approval.

## What Is Next
- Recommended next decision: approve G9 one market behavior signal card or hold.
- Recommended G9 candidate: `FINRA_SHORT_INTEREST_SIGNAL_CARD_V0`.
- Do not jump to alpha search, screening, ranking, backtest, replay, providers, alerts, or broker calls.

## First Command
```text
.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g7_2_opportunity_state_machine.py tests\test_g7_3_signal_to_state_source_map.py tests\test_g7_4_dashboard_state_spec.py -q
```

## Next Todos
- Validate G8 focused tests plus G7.2/G7.3/G7.4 regression tests.
- Refresh current context surfaces after G8 closeout.
- Hold for explicit G9 approval.

ConfirmationRequired: YES
Prompt: Reply "approve G9 one market behavior signal card" or "hold" to choose the next step.
NextPhaseApproval: PENDING
