# Phase 65 G7.1G Handover - FRED / Ken French Tiny Fixture Proof

Date: 2026-05-09
Phase Window: 2026-05-09 to 2026-05-09
Status: COMPLETE
Owner: Codex / Data + Docs/Ops

## 1) Executive Summary

- Objective completed: built one tiny static FRED macro fixture and one tiny static Ken French factor fixture, each with a manifest and validation tests.
- Business/user impact: GodView now has a fourth public-source proof pillar after SEC, FINRA, and CFTC: macro liquidity / rates / credit / factor-regime context.
- Current readiness: fixture-only proof is ready; FRED provider code, Ken French provider code, live calls, API key handling, bulk downloads, macro scoring, factor scoring, alerts, and G7.2 state-machine work remain held.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `docs/architecture/fred_ken_french_tiny_fixture_policy.md`
- `docs/architecture/macro_factor_context_usage_policy.md`
- `docs/architecture/fred_ken_french_public_provider_fixture_plan.md`
- `data/fixtures/fred/fred_macro_tiny.csv`
- `data/fixtures/fred/fred_macro_tiny.manifest.json`
- `data/fixtures/ken_french/ken_french_factor_tiny.csv`
- `data/fixtures/ken_french/ken_french_factor_tiny.manifest.json`
- `tests/test_g7_1g_fred_ken_french_tiny_fixture.py`

Deferred:

- FRED live provider implementation;
- Ken French live provider implementation;
- live API calls, API key handling, or bulk downloads;
- macro regime score or factor regime score;
- G7.2 Unified Opportunity State Machine;
- Reg SHO, ATS / dark-pool, options / IV / gamma / whale data;
- signal scoring, candidate generation, search, backtest, replay, dashboard runtime behavior, alerts, broker calls, and promotion packets.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-01 | `g7_1g_fred_fixture_valid = static_fixture and dataset_type == macro_series and manifest_hash_matches and row_count_reconciles and date_range_reconciles and date_fields_parse and series_id_present and value_is_finite and duplicate_primary_keys == 0 and observed_label == observed and api_key_required == true_for_live_api and provider_code_added == false` | FRED rows, manifest, test validators | Prevents macro context from becoming live provider, score, alert, or state-machine authority | `docs/architecture/fred_ken_french_tiny_fixture_policy.md`, `tests/test_g7_1g_fred_ken_french_tiny_fixture.py` |
| F-02 | `g7_1g_ken_french_fixture_valid = static_fixture and dataset_type == factor_returns and manifest_hash_matches and row_count_reconciles and date_range_reconciles and date_fields_parse and dataset_id_present and factor_name_present and factor_return_is_finite and duplicate_primary_keys == 0 and observed_label == observed and provider_code_added == false` | Ken French rows, manifest, test validators | Prevents factor context from becoming alpha proof, ranking, alert, or state-machine authority | `docs/architecture/fred_ken_french_tiny_fixture_policy.md`, `tests/test_g7_1g_fred_ken_french_tiny_fixture.py` |
| F-03 | `macro_factor_context_only = observed_macro_or_factor_rows and allowed_use_present and forbidden_use_present and macro_score == 0 and factor_score == 0 and candidate_rank == 0` | source labels, manifest use labels, forbidden fields | Locks macro/factor rows as context only | `docs/architecture/macro_factor_context_usage_policy.md` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-01 | FRED `DGS10`, `M2SL`, `BAA10Y` observed rows | Tiny static CSV + manifest sidecar | Accept only if static validation passes and no provider/key/score scope appears | G7.1G FRED macro fixture proof |
| L-02 | Ken French Fama-French 3 factor monthly rows | Long-form static CSV + manifest sidecar | Accept only if static validation passes and no alpha/ranking/runtime scope appears | G7.1G Ken French factor fixture proof |
| L-03 | Macro/factor source vocabulary | Policy labels and forbidden-use manifest fields | Context may support future panels; it may not emit scores or rank candidates now | Macro/factor context only |

## 5) Validation Evidence Matrix

| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-G71G-01 | `.venv\Scripts\python -m pytest tests\test_g7_1g_fred_ken_french_tiny_fixture.py -q` | PASS | `tests/test_g7_1g_fred_ken_french_tiny_fixture.py` | `8 passed` |
| CHK-G71G-02 | focused FRED/Ken French fixture + context-builder tests | PASS | test suite | fixture/context proof |
| CHK-G71G-03 | `.venv\Scripts\python -m pytest -q` | PASS | test suite | full regression evidence in SAW |
| CHK-G71G-04 | `.venv\Scripts\python -m pip check` | PASS | environment | no broken requirements |
| CHK-G71G-05 | scoped compile checks | PASS | active packages/tests | G7.1G files and active code compile |
| CHK-G71G-06 | data readiness | PASS | readiness report | inherited stale sidecar warning only |
| CHK-G71G-07 | minimal validation lab | PASS | validation lab report | no new alpha evidence |
| CHK-G71G-08 | forbidden implementation scan | PASS | G7.1G scope | no provider/runtime/scoring/state-machine code added |
| CHK-G71G-09 | secret scan | PASS | G7.1G docs/fixtures/test | no credential-shaped secrets found |
| CHK-G71G-10 | artifact hash audit | PASS | FRED and Ken French manifests | row counts `9` and `12`; hashes match |
| CHK-G71G-11 | context rebuild + validation | PASS | `docs/context/current_context.*` | context selector points to G7.1G alias |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Reg SHO policy and fixture remain future work.
- GodView provider gap remains open after this static proof.
- FRED live API key handling and series-rights handling remain future provider-policy work.
- Broad compileall workspace hygiene remains inherited debt.

Assumptions:

- Three FRED series with three dates each are sufficient for tiny macro fixture proof.
- One Ken French 3-factor monthly dataset with four dates is sufficient for tiny factor fixture proof.
- Static tiny fixture use remains local research/governance validation only.

Rollback Note:

- Revert only G7.1G FRED / Ken French fixture docs, fixture files, test file, handover/context/SAW/governance-log updates.
- Do not revert G7.1F CFTC, G7.1E FINRA, G7.1D SEC, or earlier Phase 65 work.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | G7.2 Unified Opportunity State Machine | only after explicit approval; no scoring/ranking/alerts/trading | PM / Architecture |
| 2 | Hold | no new source/runtime work | PM |

## 8) New Context Packet

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

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve G7.2 state machine" or "hold" to choose the next step.
