# Phase 65 G7.1G Compatibility Alias - FRED / Ken French Tiny Fixture Proof

This compatibility alias mirrors the G7.1G new-context packet for humans looking for an alpha-suffix handover.

## New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, G7.1D, G7.1E, and G7.1F as inherited baseline truth.
- Approved and executed G7.1G as one tiny FRED / Ken French macro-factor fixture proof.
- Added a static FRED macro CSV with `DGS10`, `M2SL`, and `BAA10Y`, three dates per series.
- Added a static Ken French factor CSV with Fama-French 3 factors monthly rows across four dates.
- Added sidecar manifests with official source URLs, source quality, row count, date range, hash, allowed use, forbidden use, and observed labels.
- Added fixture-only validation tests; no FRED provider, Ken French provider, live API call, API key handling, bulk download, macro/factor score, state machine, alerts, broker calls, or dashboard runtime behavior was added.

## What Is Locked
- Terminal Zero remains the Unified Opportunity Engine.
- G7.1G is fixture-only.
- FRED is macro liquidity / rates / credit context, not a macro regime score.
- Ken French is factor-return / benchmark context, not alpha proof or candidate ranking.
- FRED live API use requires a registered API key and separate future provider approval; G7.1G uses no key.
- `source_quality`, `dataset_type`, and `observed_estimated_or_inferred = observed` are required for both fixture proofs.
- G7.2 state machine, Reg SHO, ATS/dark-pool, options/IV/gamma/whale data, signal scoring, candidate generation, dashboard runtime behavior, alerts, and broker calls remain held.

## What Is Next
- Recommended next action: `approve_g7_2_unified_opportunity_state_machine_or_hold`.
- G7.2 remains separate approval and must still avoid scoring, ranking, alerts, broker calls, candidate generation, live providers, and dashboard runtime behavior unless explicitly authorized.
- Alternative: hold with four public-source fixture pillars complete.
- ConfirmationRequired: YES
- Prompt: Reply "approve G7.2 state machine" or "hold" to choose the next step.
- NextPhaseApproval: PENDING

## First Command
```text
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Next Todos
- G7.1G final validation matrix and SAW are complete.
- Keep FRED/Ken French provider code, live calls, API key handling, bulk downloads, macro/factor scoring, state-machine consumption, alerts, broker calls, and dashboard runtime behavior held.
