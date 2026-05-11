# Phase 65 G7.1A Handover: Starter Docs / PRD / Product Spec Rewrite

Status: CLOSED - DOCS ONLY
Authority: Phase 65 G7.1A product canon
Date: 2026-05-09
Audience: PM / Planner / Architecture Office

## Executive Summary (PM-Friendly)

G7.1A locks the real product before any further family definition.

Terminal Zero is now framed as the **Unified Opportunity Engine**:

```text
Primary Alpha: Supercycle Gem Discovery
Secondary Alpha: GodView Market Behavior Intelligence
Output Layer: Decision Augmentation
```

The system is not a trading bot. It is a discretionary augmentation cockpit for finding de-risked asymmetric upside and reading market behavior so the user avoids buying too early and selling too early.

## Delivered Scope vs Deferred Scope

Delivered in G7.1A:

- root `README.md` rewrite;
- root `PRD.md`;
- root `PRODUCT_SPEC.md`;
- lowercase `docs/prd.md` and `docs/spec.md` canon notice;
- top-level roadmap;
- Unified Opportunity Engine architecture;
- GodView signal taxonomy;
- data and infrastructure gap assessment;
- Codex/Chrome research-agent SOP;
- dashboard product spec;
- phase brief and current truth-surface refresh;
- SAW report and closure packet.

Deferred:

- G7.1B data/infra deepening;
- G7.1C research-agent SOP expansion;
- G7.2 Unified Opportunity Engine state machine;
- G7.3 GodView source policy;
- G7.4 Supercycle Gem family definition;
- G7.5 Market Behavior signal family definitions;
- G8/G9 candidate cards;
- G10 dashboard prototype;
- G11 discovery;
- G12 paper-only prompts.

Blocked:

- search;
- candidate generation;
- backtest;
- replay;
- proxy run;
- provider ingestion;
- options ingestion;
- ranking;
- alerts;
- broker calls;
- Alpaca live behavior;
- OpenClaw notifications;
- new dashboard runtime behavior.

## Derivation and Formula Register

Product formula:

```text
Unified Opportunity Engine = Supercycle Gem Discovery + GodView Market Behavior Intelligence + Decision Augmentation
```

Future state-engine concept:

```text
dashboard_state = f(thesis_state, market_behavior_state, entry_discipline_state, hold_discipline_state, source_quality_state)
```

This is a product formula, not implemented code.

Signal metadata contract:

```text
signal_context = {
  source_quality,
  provider,
  provider_feed,
  freshness,
  latency,
  confidence,
  observed_vs_estimated,
  allowed_use,
  forbidden_use,
  manifest_uri
}
```

Source paths:

- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/architecture/unified_opportunity_engine.md`
- `docs/architecture/godview_signal_taxonomy.md`
- `docs/architecture/data_infra_gap_assessment.md`
- `docs/architecture/dashboard_product_spec.md`

## Logic Chain

```text
User problem
  -> product truth rewrite
  -> root PRD/spec canon
  -> architecture package
  -> current truth surfaces
  -> next decision becomes G7.1B data gap or G7.2 state machine
```

## Evidence Matrix

| Evidence | Result | Artifact |
| --- | --- | --- |
| Starter-doc rewrite | PASS | `README.md`, `PRD.md`, `PRODUCT_SPEC.md` |
| Architecture package | PASS | `docs/architecture/*.md` G7.1A set |
| Context packet rebuild | PASS | `docs/context/current_context.*` |
| Dashboard drift regression | PASS | `tests/test_dashboard_drift_monitor_integration.py` |
| Full regression | PASS | pytest |
| Data readiness / minimal validation | PASS | `data/processed/*readiness*`, `data/processed/*validation*` |
| SAW validation | PASS | `docs/saw_reports/saw_phase65_g7_1a_starter_docs_product_spec_20260509.md` |

## Open Risks / Assumptions / Rollback

Open risks:

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Full GodView requires future provider policy and ingestion design.

Assumptions:

- G7.1A remains docs-only.
- Root `PRD.md` and `PRODUCT_SPEC.md` are accepted as product canon.
- Lowercase historical docs remain for continuity but defer to root canon.

Rollback note:

- Revert only G7.1A starter-docs/product-spec/context/SAW/handover updates.
- Do not revert G7.1, G7 family artifacts, dashboard drift-monitor fix, or prior G phases.

## Next Phase Roadmap

```text
G7.1B - Data + Infra Gap Assessment for GodView signals
G7.1C - Codex/Chrome Research Agent SOP
G7.2  - Unified Opportunity Engine State Machine
G7.3  - GodView Signal Source Policy
G7.4  - Supercycle Gem Family Definition, no search
G7.5  - Market Behavior Signal Family Definitions, no search
G8    - One Supercycle Gem Candidate Card, no search
G9    - One Market Behavior Signal Card, no search
G10   - Dashboard Prototype: watchlist state view
G11   - Bounded discovery under sealed families
G12   - Paper-only buying-range / hold-discipline alerts
```

Immediate next action:

```text
approve_g7_1b_data_infra_gap_or_g7_2_state_machine
```

## NewContextPacket

## What Was Done
- Preserved D-353 provenance/validation gates, R64.1 dependency hygiene, Candidate Registry, G0/G1/G2/G3/G4/G5/G6/G7, and G7.1 artifacts as inherited baseline truth.
- Rewrote the starter product truth around the Unified Opportunity Engine.
- Created root `PRD.md` and `PRODUCT_SPEC.md` as canon.
- Added architecture docs for roadmap, engine architecture, GodView taxonomy, data/infra gaps, Codex/Chrome research workflow, and dashboard product spec.
- Aligned lowercase `docs/prd.md` and `docs/spec.md` with canon notices.
- Published G7.1A SAW report and validated closure packet/SAW blocks.
- Validated context packet, dashboard drift regression, full regression, pip check, scoped compile, data readiness, and minimal validation lab.
- Kept G7.2, G7.4, G7.5, G8, search, candidate generation, backtests, replays, proxy runs, provider ingestion, ranking, alerts, broker calls, and new dashboard runtime behavior held.

## What Is Locked
- Terminal Zero is not a trading bot.
- Unified Opportunity Engine is the product center.
- Primary alpha is Supercycle Gem Discovery.
- Secondary alpha is GodView Market Behavior Intelligence.
- Output layer is Decision Augmentation through dashboard states and paper-only prompts.
- `PEAD_DAILY_V0` remains tactical and not the product center.
- G7.2 is not approved by G7.1A.
- G8 PEAD generation remains held.

## What Is Next
- Choose `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`.
- Keep G7.4 family definition, G8 candidate cards, search, provider ingestion, alerts, broker calls, and dashboard-runtime implementation held.
- ConfirmationRequired: YES
- Prompt: Reply "approve next phase" only after G7.1A closeout if the next phase should start.
- NextPhaseApproval: PENDING

## First Command
```text
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Next Todos
- Next action after closeout: `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`.
- Keep G7.2, G7.4, G7.5, G8, search, provider ingestion, alerts, broker calls, and dashboard-runtime implementation held until separately approved.
