# Phase 65 G7.3 Handover - Signal-to-State Source Eligibility Map

Date: 2026-05-09
Status: COMPLETE
Owner: Codex / Backend + Data + Docs/Ops

## 1) Executive Summary

- Objective completed: mapped every GodView signal family to source class, observed/estimated/inferred label, allowed state influence, forbidden influence, freshness requirement, and confidence label.
- Business/user impact: state transitions now have source eligibility rules before any scoring, ranking, provider, or dashboard runtime work exists.
- Current readiness: policy-only source map is ready for G7.4 dashboard state spec; provider, ingestion, live API, alerts, broker paths, and candidate work remain held.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `docs/architecture/godview_signal_to_state_map.md`
- `docs/architecture/godview_source_eligibility_policy.md`
- `docs/architecture/godview_signal_confidence_policy.md`
- `opportunity_engine/source_classes.py`
- `opportunity_engine/signal_policy.py`
- `tests/test_g7_3_signal_to_state_source_map.py`

Deferred:

- provider implementations;
- source registry implementation;
- live data ingestion;
- scoring/ranking;
- candidate generation;
- alerts;
- broker calls;
- dashboard runtime behavior.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
| --- | --- | --- | --- | --- |
| F-G73-01 | `state_eligible = source_class_allowed and freshness_known and forbidden_state_influence_excludes(target_state)` | signal policy fields | Prevents source creep into action states | `opportunity_engine/signal_policy.py` |
| F-G73-02 | `tier2_action_state_allowed = false` | Tier 2/yfinance source class | Keeps convenience data out of buying/hold states | `docs/architecture/godview_source_eligibility_policy.md` |
| F-G73-03 | `estimated_action_state_alone = false` | estimated model label | Keeps estimates as context/confidence only | `docs/architecture/godview_signal_to_state_map.md` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
| --- | --- | --- | --- | --- |
| L-G73-01 | signal family | policy lookup | require source class + allowed/forbidden influence | source eligibility result |
| L-G73-02 | public fixture pillar | context-only mapping | allow reason codes, block rankings/alerts/action states | governed context |
| L-G73-03 | provider-gap family | licensed-required label | block state advancement until provider decision | held signal |

## 5) Evidence Matrix

| Check ID | Command | Result | Artifact |
| --- | --- | --- | --- |
| CHK-G73-01 | `.venv\Scripts\python -m pytest tests\test_g7_3_signal_to_state_source_map.py -q` | PASS | focused policy tests |
| CHK-G73-02 | scoped compile | PASS | `opportunity_engine` |
| CHK-G73-03 | forbidden-scope scan | PASS | owned G7.3 files |
| CHK-G73-04 | closure packet validation | PASS | G7.3 closure packet |
| CHK-G73-05 | SAW block validation | PASS | G7.3 SAW report |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- inherited yfinance migration, stale sidecar, Reg SHO policy gap, GodView provider gap, options/license gap, and broad compileall workspace hygiene remain open.
- Provider-gap families can be overread as available unless labels stay visible.

Assumptions:

- G7.3 stays policy-only and does not implement source registry or provider adapters.

Rollback Note:

- Revert only G7.3 source-policy docs, policy modules, focused test, context/governance updates, handover, and SAW report.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
| --- | --- | --- | --- |
| 1 | G7.4 Dashboard Wireframe / Product-State Spec | proceed only after G7.3 PASS | Frontend/UI + Docs/Ops |
| 2 | Hold G8 | no candidate card unless G7.4 passes | PM / Architecture |

## 8) New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, G7.1D, G7.1E, G7.1F, G7.1G as inherited baseline truth.
- Completed G7.3 as policy-only Signal-to-State Source Eligibility Map work.
- Added source classes, signal-family enums, confidence labels, and policy lookups.
- Mapped SEC, FINRA, CFTC, FRED, and Ken French as context/reason-code sources only.
- Kept options, IV, gamma, whales, dark-pool, ETF, and microstructure families behind provider/license decisions.
- Added focused tests for source-map completeness and forbidden action-state influence.

## What Is Locked
- SEC/FINRA/CFTC/FRED/KF fixtures may support context and reason codes, not rankings or alerts.
- Estimated signals cannot alone move to `BUYING_RANGE`.
- Tier 2/yfinance cannot move any state toward `BUYING_RANGE` or `LET_WINNER_RUN`.
- Options/IV/gamma/whales remain provider-gap signals.
- Short interest is squeeze-base context only.
- CFTC is broad regime/positioning context only.
- FRED/Ken French are macro/factor context only.
- Provider code, live API calls, ingestion, source registry implementation, candidate generation, search, scoring, ranking, alerts, broker paths, and dashboard runtime behavior remain held.

## What Is Next
- Recommended next action: `approve_g7_4_dashboard_state_wireframe_or_hold`.
- G7.4 may define dashboard state wireframes and specs only if G7.3 closes PASS.
- G8 remains held unless G7.4 passes.

## First Command
```text
.venv\Scripts\python -m pytest tests\test_g7_3_signal_to_state_source_map.py -q
```

## Next Todos
- Proceed to G7.4 dashboard state wireframe only after G7.3 PASS.
- Keep candidate card, search, ranking, alerts, providers, broker paths, and dashboard runtime held.
