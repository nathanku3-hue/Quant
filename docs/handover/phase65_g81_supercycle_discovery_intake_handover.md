# Phase 65 G8.1 Handover - Supercycle Discovery Intake

Status: Complete
Authority: Phase 65 G8.1 intake-only work
Date: 2026-05-10
Owner: PM / Architecture Office

## Executive Summary (PM-friendly)

G8.1 creates a controlled discovery intake layer. It lets Terminal Zero map broad supercycle themes into candidate intake items for `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` without ranking, scoring, validating, recommending, or creating new candidate cards.

`MU` remains the only full candidate card. The other five names are intake-only.

## Delivered Scope vs Deferred Scope

Delivered:

- discovery theme taxonomy;
- static candidate intake queue;
- queue manifest with hash and row-count controls;
- Python validator and loader;
- focused invariant tests;
- policy and schema docs.

Deferred:

- G8.2 one additional candidate card;
- G9 one market-behavior signal card;
- candidate ranking;
- alpha search;
- thesis validation;
- buying range;
- provider ingestion;
- dashboard runtime behavior;
- alerts;
- broker behavior.

## Derivation and Formula Register

G8.1 validity formula:

```text
g8_1_intake_valid =
  required_seed_tickers_exact
  and theme_candidates_present
  and evidence_needed_present
  and thesis_breakers_present
  and provider_gaps_present
  and no_score_fields
  and no_rank_fields
  and no_buy_sell_hold_calls
  and validated_status_absent
  and action_states_absent
  and yfinance_canonical_absent
  and manifest_hash_matches
```

Implementation paths:

- `opportunity_engine/discovery_intake_schema.py`
- `opportunity_engine/discovery_intake.py`
- `tests/test_g8_1_supercycle_discovery_intake.py`

## Logic Chain

```text
Broad themes -> static theme taxonomy -> six seed intake items -> evidence requirements -> provider gaps -> future PM choice
```

## Evidence Matrix

| Check | Result | Artifact |
| --- | --- | --- |
| Focused G8.1 tests | PASS | `tests/test_g8_1_supercycle_discovery_intake.py` |
| Queue artifact | Present | `data/discovery/supercycle_candidate_intake_queue_v0.json` |
| Queue manifest | Present | `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json` |
| Theme taxonomy | Present | `data/discovery/supercycle_discovery_themes_v0.json` |
| Full pytest | PASS | `.venv\Scripts\python -m pytest -q` |
| Context rebuild/validate | PASS | `docs/context/current_context.json`, `docs/context/current_context.md` |
| Closure packet validation | PASS | `docs/saw_reports/saw_phase65_g8_1_supercycle_discovery_intake_20260510.md` |
| SAW block validation | PASS | `docs/saw_reports/saw_phase65_g8_1_supercycle_discovery_intake_20260510.md` |

## Open Risks / Assumptions / Rollback

Open risks:

- inherited yfinance migration debt;
- inherited sidecar freshness debt;
- inherited Reg SHO and provider-policy gaps;
- inherited options/license gap;
- inherited dashboard runtime dirty worktree;
- broad compileall workspace hygiene debt.

Assumptions:

- user-supplied ticker examples are seed intake examples only;
- source locators are candidate leads, not canonical evidence;
- G8.1 is allowed to supersede the previous G9-next bridge.

Rollback:

- revert only G8.1 schema, loader, discovery data, focused tests, G8.1 docs, context surfaces, handover, and SAW report.
- do not revert G8 or earlier Phase 65 work.

## Next Phase Roadmap

1. `G8.2`: create one additional candidate card from the intake queue, such as DELL or AMD.
2. `G9`: create one market-behavior signal card, such as FINRA short-interest context.
3. Hold.

## New Context Packet

## What Was Done

- Completed G8.1 Supercycle Discovery Intake as an intake-only layer.
- Preserved the R64.1/D-353 provenance anchor while superseding the old G9-next bridge with the G8.1 intake-only bridge.
- Added a controlled theme taxonomy for nine supercycle discovery themes.
- Added one manifest-backed candidate intake queue seeded with exactly `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`.
- Preserved `MU` as the only existing candidate card and marked all other seed names `intake_only`.
- Added validator tests that reject missing evidence requirements, ranking, scoring, action calls, validated status, action-state promotion, yfinance canonical evidence, and missing manifests.

## What Is Locked

- Candidate intake item means only: this name may belong in the discovery universe.
- Candidate card remains a separate object; only `MU` has one.
- Validated thesis and buying range remain later states and are blocked in G8.1.
- No ranking, scoring, alpha search, backtest, provider ingestion, dashboard runtime behavior, alerts, broker behavior, or recommendations are authorized.
- yfinance cannot be canonical evidence.

## What Is Next

- Recommended next action: `approve_g8_2_one_additional_candidate_card_or_g9_one_market_behavior_signal_card_or_hold`.
- Preferred next action from the user directive: `approve_g8_2_one_additional_candidate_card_from_intake_queue`.
- Alternative: `approve_g9_one_market_behavior_signal_card`.
- Alternative: hold.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g8_1_supercycle_discovery_intake.py -q
```

## Next Todos

- Wait for explicit G8.2, G9, or hold decision.

## Confirmation

ConfirmationRequired: YES
Prompt: Reply "approve G8.2 one additional candidate card" or "approve G9 one market behavior signal card" or "hold".
NextPhaseApproval: PENDING
