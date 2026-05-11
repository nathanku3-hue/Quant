# Phase 65 G7.1F Context Selector Alias

This file intentionally mirrors the G7.1F CFTC TFF tiny fixture handover so the current context packet builder selects the latest same-phase alpha substep. It is not a new phase and does not authorize provider, runtime, state-machine, scoring, alert, broker, search, backtest, replay, or dashboard behavior.

## New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, G7.1D, and G7.1E as inherited baseline truth.
- Approved and executed G7.1F as one tiny CFTC COT/TFF fixture proof.
- Added a static CFTC TFF CSV for report date `2026-05-08` and as-of position date `2026-05-05` with `E-Mini S&P 500` and `UST 10Y Note`.
- Added a sidecar manifest with official source URL, source quality, weekly freshness policy, row count, date range, hash, allowed use, forbidden use, and observed label.
- Added fixture-only validation tests; no CFTC provider, live API call, bulk download, CTA score, single-name CTA inference, state machine, alerts, broker calls, or dashboard runtime behavior was added.

## What Is Locked
- Terminal Zero remains the Unified Opportunity Engine.
- G7.1F is fixture-only.
- CFTC TFF is broad futures-positioning / systematic-regime context, not single-name CTA buying evidence.
- CFTC TFF may say "systematic/regime positioning context is supportive or hostile"; it may not say "CTAs are buying this stock today."
- `source_quality = public_official_observed`, `dataset_type = futures_positioning`, and `observed_estimated_or_inferred = observed` are required for this fixture proof.
- G7.2 state machine, FRED/Ken French, Reg SHO, ATS/dark-pool, options/IV/gamma/whale data, signal scoring, candidate generation, dashboard runtime behavior, alerts, and broker calls remain held.

## What Is Next
- Recommended next action: `approve_g7_1g_fred_ken_french_tiny_fixture_or_g7_2_state_machine_or_hold`.
- Preferred data-grounded sequence: G7.1G FRED/Ken French macro fixture, then G7.2.
- Alternative: approve G7.2 only if speed matters more than proving macro/factor context first.
- ConfirmationRequired: YES
- Prompt: Reply "approve G7.1G FRED Ken French tiny fixture", "approve G7.2 state machine", or "hold" to choose the next step.
- NextPhaseApproval: PENDING

## First Command
```text
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Next Todos
- G7.1F final validation matrix and SAW are complete.
- Keep CFTC provider code, live calls, bulk downloads, CTA scoring, single-name inference, state-machine consumption, alerts, broker calls, and dashboard runtime behavior held.
