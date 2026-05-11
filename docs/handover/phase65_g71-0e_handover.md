# Phase 65 G7.1E Handover Selector - FINRA Short Interest Tiny Fixture Proof

Status: G7.1E FINRA tiny fixture complete; provider and scoring work held
Date: 2026-05-10
Authority: selector alias for current context only
Selector note: this filename keeps the context builder on the latest G7.1E state because alpha suffix ordering is filename-sensitive. The canonical handover is `docs/handover/phase65_g71e_finra_tiny_fixture_handover.md`. This alias is not G7.2 and does not authorize state-machine work.

## Executive Summary (PM-friendly)

G7.1E approved and completed one tiny FINRA Equity Short Interest fixture proof.

The proof uses settlement date `2026-04-15`, with three tickers: `AAPL`, `TSLA`, and `GME`. The fixture has a manifest with official source identity, delayed freshness policy, row count, date range, SHA-256 hash, allowed use, forbidden use, and observed label.

No FINRA provider, live API call, bulk download, Reg SHO ingestion, squeeze score, short-squeeze ranking, candidate generation, state machine, alert, broker call, or dashboard runtime behavior was added.

## Delivered Scope vs Deferred Scope

Delivered:

- static FINRA short-interest CSV fixture;
- sidecar manifest;
- fixture-only validation tests;
- FINRA short-interest tiny fixture policy;
- FINRA short-interest-vs-short-sale-volume policy;
- FINRA fixture plan;
- handover/context/SAW refresh.

Deferred:

- G7.2 state machine;
- Reg SHO provider or fixture;
- ATS / OTC block provider or fixture;
- CFTC provider proof;
- FRED provider proof;
- options / IV / OPRA;
- signal scoring;
- candidate generation;
- dashboard runtime behavior;
- alerts;
- broker calls.

## Logic Chain

```text
FINRA official short-interest file -> one-settlement static fixture -> manifest proof -> validation tests -> next approval decision
```

## Evidence Matrix

| Evidence | Result | Artifact |
| --- | --- | --- |
| FINRA fixture policy | PASS | `docs/architecture/finra_short_interest_tiny_fixture_policy.md` |
| FINRA SI vs volume policy | PASS | `docs/architecture/finra_short_interest_vs_short_volume_policy.md` |
| FINRA fixture plan | PASS | `docs/architecture/finra_public_provider_fixture_plan.md` |
| FINRA short-interest fixture | PASS | `data/fixtures/finra/finra_short_interest_tiny.csv` |
| FINRA manifest | PASS | `data/fixtures/finra/finra_short_interest_tiny.manifest.json` |
| Fixture validation tests | PASS | `tests/test_g7_1e_finra_short_interest_tiny_fixture.py` |

## Open Risks / Assumptions / Rollback

Open risks:

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Reg SHO policy and fixture remain future work.
- GodView provider gap remains open after this static proof.
- Broad compileall workspace hygiene remains inherited debt.

Assumptions:

- One official FINRA settlement-date file is acceptable for a tiny fixture proof.
- Static tiny fixture use remains local research/governance validation only.
- FINRA API/terms review remains mandatory for any future automated request path.

Rollback:

- Revert only G7.1E FINRA fixture docs, fixture files, test file, handover/context/SAW/governance-log updates.
- Do not revert G7.1D SEC fixture docs or earlier Phase 65 artifacts.

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, and G7.1D as inherited baseline truth.
- Approved and executed G7.1E as one tiny FINRA Equity Short Interest fixture proof.
- Added a static FINRA short-interest CSV for settlement date `2026-04-15` with `AAPL`, `TSLA`, and `GME`.
- Added a sidecar manifest with official source URL, source quality, delayed freshness policy, row count, date range, hash, allowed use, forbidden use, and observed label.
- Added fixture-only validation tests; no FINRA provider, live API call, bulk download, Reg SHO ingestion, squeeze score, candidate generation, state machine, alerts, broker calls, or dashboard runtime behavior was added.

## What Is Locked
- G7.1E is fixture-only.
- FINRA short interest is delayed positioning context, not a real-time squeeze trigger.
- `Short interest = slow squeeze base`; `Reg SHO short-sale volume = daily trading context`; neither one alone is a squeeze signal.
- `source_quality = public_official_observed`, `dataset_type = short_interest`, and `observed_estimated_or_inferred = observed` are required for this fixture proof.
- G7.2 state machine, Reg SHO, ATS/OTC, CFTC, FRED, options/IV/OPRA, signal scoring, candidate generation, dashboard runtime behavior, alerts, and broker calls remain held.

## What Is Next
- Recommended next action: `approve_g7_1f_cftc_tiny_fixture_or_g7_2_state_machine_or_hold`.
- Preferred data-grounded sequence: G7.1F CFTC COT/TFF tiny fixture, then G7.1G FRED/Ken French macro fixture, then G7.2.
- Alternative: approve G7.2 only if speed matters more than proving CFTC/macro context first.
- ConfirmationRequired: YES
- Prompt: Reply "approve G7.1F CFTC tiny fixture", "approve G7.2 state machine", or "hold" to choose the next step.
- NextPhaseApproval: PENDING

## First Command
```text
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Next Todos
- Keep FINRA provider code, Reg SHO ingestion, squeeze scoring, state-machine consumption, alerts, broker calls, and dashboard runtime behavior held.
- Use G7.1F only after explicit approval.
