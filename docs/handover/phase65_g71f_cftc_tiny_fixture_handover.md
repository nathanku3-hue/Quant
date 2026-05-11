# Phase 65 G7.1F Handover - CFTC TFF Tiny Fixture Proof

Date: 2026-05-10
Phase Window: 2026-05-10 to 2026-05-10
Status: COMPLETE
Owner: Codex / Data + Docs/Ops

## 1) Executive Summary

- Objective completed: built one tiny static CFTC COT/TFF fixture with a manifest and validation tests.
- Business/user impact: GodView now has a third official public fixture pillar after SEC and FINRA: broad futures-positioning / systematic-regime context.
- Current readiness: fixture-only proof is ready; CFTC provider code, live calls, bulk downloads, CTA scoring, single-name inference, alerts, and G7.2 state-machine work remain held.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `docs/architecture/cftc_tff_tiny_fixture_policy.md`
- `docs/architecture/cftc_cot_tff_usage_policy.md`
- `docs/architecture/cftc_public_provider_fixture_plan.md`
- `data/fixtures/cftc/cftc_tff_tiny.csv`
- `data/fixtures/cftc/cftc_tff_tiny.manifest.json`
- `tests/test_g7_1f_cftc_tff_tiny_fixture.py`

Deferred:

- CFTC live provider implementation;
- live CFTC API calls or bulk downloads;
- CTA score or single-name CTA inference;
- FRED / Ken French macro fixture;
- Reg SHO, ATS / dark-pool, options / IV / gamma / whale data;
- signal scoring, candidate generation, search, backtest, replay, dashboard runtime behavior, alerts, broker calls, and G7.2 state machine.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-01 | `g7_1f_cftc_fixture_valid = static_fixture and dataset_type == futures_positioning and manifest_hash_matches and row_count_reconciles and report_date_parses and asof_position_date_parses and market_name_present and contract_market_code_present and trader_category_allowed and non_negative_numeric_fields and duplicate_primary_keys == 0 and observed_label == observed and single_name_inference_forbidden == true and provider_code_added == false` | fixture rows, manifest, test validators | Prevents broad CFTC futures-positioning context from becoming a provider, score, alert, or state-machine authority | `docs/architecture/cftc_tff_tiny_fixture_policy.md`, `tests/test_g7_1f_cftc_tff_tiny_fixture.py` |
| F-02 | `cftc_tff_allowed_context = observed_futures_positioning and broad_market_contract and weekly_delayed and source_quality == public_official_observed and single_name_inference == false` | report date, as-of date, market, trader category, source quality | Encodes broad-regime-only use | `docs/architecture/cftc_cot_tff_usage_policy.md` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-01 | CFTC TFF current futures-only report for one report date | Tiny static CSV + manifest sidecar | Accept only if static validation passes and forbidden scope remains absent | G7.1F CFTC TFF fixture proof |
| L-02 | Weekly TFF trader categories and positions | Policy labels and forbidden-use manifest fields | TFF may support broad systematic/regime context; it may not claim single-stock CTA buying | Broad futures-positioning context only |

## 5) Validation Evidence Matrix

| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-G71F-01 | `.venv\Scripts\python -m pytest tests\test_g7_1f_cftc_tff_tiny_fixture.py -q` | PASS | `tests/test_g7_1f_cftc_tff_tiny_fixture.py` | `8 passed` |
| CHK-G71F-02 | focused CFTC fixture + context-builder tests | PASS | test suite | fixture/context proof |
| CHK-G71F-03 | `.venv\Scripts\python -m pytest -q` | PASS | test suite | full regression evidence in SAW |
| CHK-G71F-04 | `.venv\Scripts\python -m pip check` | PASS | environment | no broken requirements |
| CHK-G71F-05 | scoped compile checks | PASS | active packages/tests | G7.1F files and active code compile |
| CHK-G71F-06 | data readiness | PASS | readiness report | inherited stale sidecar warning only |
| CHK-G71F-07 | minimal validation lab | PASS | validation lab report | no new alpha evidence |
| CHK-G71F-08 | forbidden implementation scan | PASS | G7.1F scope | no provider/runtime/scoring/state-machine code added |
| CHK-G71F-09 | secret scan | PASS | G7.1F docs/fixtures/test | no credential-shaped secrets found |
| CHK-G71F-10 | artifact hash audit | PASS | `data/fixtures/cftc/*.manifest.json` | row count `8`; hash matches |
| CHK-G71F-11 | context rebuild + validation | PASS | `docs/context/current_context.*` | context selector points to G7.1F alias |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Reg SHO policy and fixture remain future work.
- GodView provider gap remains open after this static proof.
- Broad compileall workspace hygiene remains inherited debt.

Assumptions:

- One official CFTC report date and two broad financial futures markets are acceptable for a tiny fixture proof.
- `E-Mini S&P 500` and `UST 10Y Note` are acceptable broad regime markets for schema/provenance validation.
- Static tiny fixture use remains local research/governance validation only.

Rollback Note:

- Revert only G7.1F CFTC fixture docs, fixture files, test file, handover/context/SAW/governance-log updates.
- Do not revert G7.1E FINRA, G7.1D SEC, or earlier Phase 65 work.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | G7.1G FRED / Ken French macro fixture | one tiny macro/factor fixture with source rights and no provider creep | PM / Data |
| 2 | G7.2 Unified Opportunity State Machine | only after explicit approval; no scoring without source labels | PM / Architecture |
| 3 | Hold | no new source/runtime work | PM |

## 8) New Context Packet

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

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve G7.1G FRED Ken French tiny fixture", "approve G7.2 state machine", or "hold" to choose the next step.
