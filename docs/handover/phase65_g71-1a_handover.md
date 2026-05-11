# Phase 65 G7.1B Selector Alias

Status: SELECTOR ALIAS FOR CONTEXT PACKET BUILDER
Authority: G7.1B docs-only context routing
Date: 2026-05-09

This file exists because `scripts/build_context_packet.py` ranks numeric G-suffix handovers and does not yet understand alphabetic suffixes such as `G7.1B`. It is not a new phase and does not authorize implementation.

Canonical handover:

```text
docs/handover/phase65_g71b_handover.md
```

## NewContextPacket

## What Was Done
- Preserved D-353 provenance/validation gates, R64.1 dependency hygiene, Candidate Registry, G0/G1/G2/G3/G4/G5/G6/G7, G7.1, and G7.1A artifacts as inherited baseline truth.
- Completed G7.1B docs/architecture/source mapping for GodView data and infrastructure readiness.
- Published the GodView data/infra gap assessment, signal-source matrix, provider roadmap, freshness policy, observed-vs-estimated policy, and Codex/Chrome research SOP.
- Confirmed current repo support is governance-ready and daily-price-ready, but not full-GodView-ready.
- Confirmed future options, short-interest, CFTC, SEC filings, ETF/passive, ATS/block, microstructure, and news/narrative providers are not implemented.
- Kept G7.2, G7.4, G7.5, G8, search, candidate generation, backtests, replays, proxy runs, provider ingestion, signal ranking, alerts, broker calls, and new dashboard runtime behavior held.

## What Is Locked
- Terminal Zero remains the Unified Opportunity Engine.
- G7.1B is docs/architecture/source mapping only.
- Current infra is sufficient for governance foundations, not full GodView.
- Future GodView signals must carry source-quality, provider/feed, observed-vs-estimated label, freshness, latency, as-of timestamp, confidence, allowed use, forbidden use, and manifest identity.
- Codex/Chrome research agents may support research capture and documentation only.
- Observed, estimated, and inferred signals must be labeled differently.
- G7.2 state-machine work is still held until separately approved.

## What Is Next
- Choose `approve_g7_2_unified_opportunity_state_machine_or_hold`.
- Keep G7.4/G7.5 family definitions, G8 candidate cards, search, provider ingestion, signal ranking, alerts, broker calls, and dashboard-runtime implementation held.
- ConfirmationRequired: YES
- Prompt: Reply "approve next phase" only after G7.1B closeout if the next phase should start.
- NextPhaseApproval: PENDING

## First Command
```text
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Next Todos
- Next action after closeout: `approve_g7_2_unified_opportunity_state_machine_or_hold`.
- Keep provider ingestion, state-machine implementation, candidate generation, ranking, alerts, broker calls, and dashboard-runtime implementation held until separately approved.
