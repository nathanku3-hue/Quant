# Phase 65 G7.1E Handover - FINRA Short Interest Tiny Fixture Proof

Date: 2026-05-10
Phase Window: 2026-05-10 to 2026-05-10
Status: COMPLETE
Owner: Codex / Data + Docs/Ops

## 1) Executive Summary

- Objective completed: built one tiny static FINRA Equity Short Interest fixture with a manifest and validation tests.
- Business/user impact: GodView now has the first official public market-behavior base-layer fixture proof after SEC.
- Current readiness: fixture-only proof is ready; FINRA provider code, Reg SHO, OTC/ATS, squeeze scoring, alerts, and G7.2 state-machine work remain held.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `docs/architecture/finra_short_interest_tiny_fixture_policy.md`
- `docs/architecture/finra_short_interest_vs_short_volume_policy.md`
- `docs/architecture/finra_public_provider_fixture_plan.md`
- `data/fixtures/finra/finra_short_interest_tiny.csv`
- `data/fixtures/finra/finra_short_interest_tiny.manifest.json`
- `tests/test_g7_1e_finra_short_interest_tiny_fixture.py`

Deferred:

- FINRA live provider implementation;
- Reg SHO daily short-sale-volume fixture/provider;
- OTC / ATS transparency fixture/provider;
- CFTC, FRED, Ken French, options, IV, OPRA, and vendor feeds;
- squeeze scoring, short-squeeze ranking, candidate generation, dashboard runtime behavior, alerts, broker calls, and G7.2 state machine.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-01 | `g7_1e_finra_fixture_valid = static_fixture and dataset_type == short_interest and manifest_hash_matches and row_count_reconciles and settlement_date_parses and ticker_present and non_negative_numeric_fields and duplicate_primary_keys == 0 and observed_label == observed and reg_sho_fields_present == false and provider_code_added == false` | fixture rows, manifest, test validators | Prevents delayed short-interest context from becoming a provider, score, alert, or state-machine authority | `docs/architecture/finra_short_interest_tiny_fixture_policy.md`, `tests/test_g7_1e_finra_short_interest_tiny_fixture.py` |
| F-02 | `squeeze_signal_allowed = short_interest_context + additional_validated_evidence + explicit_future_scoring_approval` | delayed short interest, later evidence, later approval | Encodes that short interest alone cannot emit a squeeze signal | `docs/architecture/finra_short_interest_vs_short_volume_policy.md` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-01 | FINRA Equity Short Interest file for one settlement date | Tiny static CSV + manifest sidecar | Accept only if static validation passes and forbidden scope remains absent | G7.1E FINRA short-interest fixture proof |
| L-02 | FINRA short interest vs Reg SHO distinction | Policy labels and forbidden-use manifest fields | Short interest may say short base exists; it may not say forced covering is happening now | Delayed short-crowding context only |

## 5) Validation Evidence Matrix

| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-G71E-01 | `.venv\Scripts\python -m pytest tests\test_g7_1e_finra_short_interest_tiny_fixture.py -q` | PASS | `tests/test_g7_1e_finra_short_interest_tiny_fixture.py` | `8 passed` |
| CHK-G71E-02 | `.venv\Scripts\python -m pytest -q` | PASS | test suite | full regression evidence in SAW |
| CHK-G71E-03 | `.venv\Scripts\python -m pip check` | PASS | environment | no broken requirements |
| CHK-G71E-04 | scoped compile checks | PASS | active packages/tests | G7.1E files and active code compile |
| CHK-G71E-05 | data readiness | PASS | readiness report | inherited stale sidecar warning only |
| CHK-G71E-06 | minimal validation lab | PASS | validation lab report | no new alpha evidence |
| CHK-G71E-07 | forbidden implementation scan | PASS | G7.1E scope | no provider/runtime/scoring/state-machine code added |
| CHK-G71E-08 | secret scan | PASS | G7.1E docs/fixtures/test | no credential-shaped secrets found |
| CHK-G71E-09 | artifact hash audit | PASS | `data/fixtures/finra/*.manifest.json` | row count `3`; hash matches |
| CHK-G71E-10 | context rebuild + validation | PASS | `docs/context/current_context.*` | context selector points to G7.1E alias |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Reg SHO policy and fixture remain future work.
- GodView provider gap remains open after this static proof.
- Broad compileall workspace hygiene remains inherited debt.

Assumptions:

- One official FINRA settlement-date file is acceptable for a tiny fixture proof.
- `AAPL`, `TSLA`, and `GME` are acceptable public large/liquid/squeeze-context test entities for schema/provenance validation.
- Static tiny fixture use remains local research/governance validation only.

Rollback Note:

- Revert only G7.1E FINRA fixture docs, fixture files, test file, handover/context/SAW/governance-log updates.
- Do not revert G7.1D SEC fixture docs or earlier Phase 65 artifacts.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | G7.1F CFTC COT/TFF tiny fixture | one report-date futures positioning fixture, broad-regime-only labels | PM / Data |
| 2 | G7.1G FRED/Ken French macro fixture | macro/factor fixture with rights/API-key/citation caveats | PM / Data |
| 3 | G7.2 Unified Opportunity State Machine | only after explicit approval; no scoring without source labels | PM / Architecture |

## 8) New Context Packet

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

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve G7.1F CFTC tiny fixture", "approve G7.2 state machine", or "hold" to choose the next step.
