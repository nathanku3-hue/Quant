# Phase 65 G7.2 Handover - Unified Opportunity State Machine

Date: 2026-05-09
Status: COMPLETE
Owner: Codex / Backend + Docs/Ops

## 1) Executive Summary

- Objective completed: defined the Unified Opportunity State Machine with finite states, transition schemas, forbidden jumps, reason-code requirements, source-class requirements, and focused tests.
- Business/user impact: Terminal Zero can now describe opportunity state without starting alpha search or turning source fixtures into trade actions.
- Current readiness: state definition and transition validation are ready for G7.3 source eligibility mapping; scoring, ranking, alerts, candidates, providers, and dashboard runtime remain held.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `docs/architecture/unified_opportunity_state_machine.md`
- `docs/architecture/opportunity_state_transition_policy.md`
- `docs/architecture/opportunity_state_forbidden_jumps.md`
- `opportunity_engine/__init__.py`
- `opportunity_engine/states.py`
- `opportunity_engine/schemas.py`
- `opportunity_engine/transitions.py`
- `tests/test_g7_2_opportunity_state_machine.py`

Deferred:

- signal-to-state source eligibility policy beyond source classes;
- dashboard product wireframe;
- candidate card creation;
- scoring/ranking;
- providers, live API calls, ingestion, alerts, broker calls, and dashboard runtime.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
| --- | --- | --- | --- | --- |
| F-G72-01 | `opportunity_state = thesis_quality + market_behavior + risk_discipline + source_quality_controls` | state components | Keeps state language separate from scoring and orders | `docs/architecture/unified_opportunity_state_machine.md` |
| F-G72-02 | `transition_valid = reason_codes_present and source_classes_present and forbidden_jump_not_requested and no_action_metadata` | transition request/evidence | Fails closed when evidence or boundary metadata is missing | `opportunity_engine/transitions.py` |
| F-G72-03 | `thesis_broken_override = thesis_broken ? THESIS_BROKEN : requested_state` | thesis-broken evidence | Prevents market behavior from overriding invalidation | `opportunity_engine/transitions.py` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
| --- | --- | --- | --- | --- |
| L-G72-01 | thesis evidence + market behavior + risk evidence | labeled transition request | accept only if reason/source labels and transition path are valid | allowed state transition |
| L-G72-02 | thesis invalidation evidence | override check | thesis broken wins over behavior strength | `THESIS_BROKEN` |
| L-G72-03 | estimated/inferred-only evidence | action-state guard | block `BUYING_RANGE` or `LET_WINNER_RUN` if source class is insufficient | no action state |

## 5) Evidence Matrix

| Check ID | Command | Result | Artifact |
| --- | --- | --- | --- |
| CHK-G72-01 | `.venv\Scripts\python -m pytest tests\test_g7_2_opportunity_state_machine.py -q` | PASS | focused state-machine tests |
| CHK-G72-02 | scoped compile | PASS | `opportunity_engine` |
| CHK-G72-03 | forbidden-scope scan | PASS | owned G7.2 docs/code/tests |
| CHK-G72-04 | closure packet validation | PASS | G7.2 closure packet |
| CHK-G72-05 | SAW block validation | PASS | G7.2 SAW report |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- inherited yfinance migration, stale sidecar, Reg SHO policy gap, GodView provider gap, options/license gap, and broad compileall workspace hygiene remain open.
- State vocabulary can be overread as trading advice if future dashboard copy drops the no-order/no-alert boundary.

Assumptions:

- G7.2 approval from user directive authorizes definition-only state-machine code and schema validation, not scoring or runtime UI.
- Source classes are sufficient until G7.3 maps full eligibility.

Rollback Note:

- Revert only G7.2 state-machine docs, `opportunity_engine` files, focused test, context/governance updates, handover, and SAW report.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
| --- | --- | --- | --- |
| 1 | G7.3 Signal-to-State Source Eligibility Map | proceed only after G7.2 PASS | Backend + Docs/Ops |
| 2 | G7.4 Dashboard Wireframe / Product-State Spec | proceed only after G7.3 PASS | Frontend/UI + Docs/Ops |

## 8) New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, G7.1D, G7.1E, G7.1F, G7.1G as inherited baseline truth.
- Completed G7.2 as definition-only Unified Opportunity State Machine work.
- Added finite opportunity states, reason-code enums, transition evidence schemas, and transition validator.
- Added policies for forbidden jumps, thesis-broken override, estimated/inferred source-class gates, and no action/alert/broker/score/ranking metadata.
- Added focused tests for required G7.2 invariants.

## What Is Locked
- No state creates buy/sell orders.
- No state emits alerts in this phase.
- No state computes score or ranking.
- `THESIS_BROKEN` overrides market-behavior strength.
- `THESIS_CANDIDATE` cannot jump directly to `BUYING_RANGE`.
- `LEFT_SIDE_RISK` must pass through `ACCUMULATION_WATCH` or `CONFIRMATION_WATCH` before `BUYING_RANGE`.
- Estimated-only evidence cannot create `BUYING_RANGE`.
- Inferred-only evidence cannot create `LET_WINNER_RUN`.
- Provider code, live API calls, ingestion, candidate generation, search, replay, proxy, dashboard runtime behavior, alerts, and broker paths remain held.

## What Is Next
- Recommended next action: `approve_g7_3_signal_to_state_source_map_or_hold`.
- G7.3 may map source eligibility, confidence, freshness, and forbidden influence only if G7.2 closes PASS.
- G8 remains held unless G7.4 later passes.

## First Command
```text
.venv\Scripts\python -m pytest tests\test_g7_2_opportunity_state_machine.py -q
```

## Next Todos
- Proceed to G7.3 source eligibility map only after G7.2 PASS.
- Keep scoring, ranking, provider ingestion, alerts, broker calls, candidate generation, and dashboard runtime held.
