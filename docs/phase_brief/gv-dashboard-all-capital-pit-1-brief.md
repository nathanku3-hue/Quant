# Phase Brief — GV-DASHBOARD-ALL-CAPITAL-PIT-1

Date: 2026-08-03
Status: `FINAL PLANNING FROZEN; SLICE 0 BASELINE BANKED; DOCS CUSTODY PENDING; IMPLEMENTATION NOT STARTED`
Accepted product score: `62/100`
Limited Live: `CLOSED; NOT AUTHORIZED`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`
Roadmap: `docs/architecture/top_level_roadmap.md`

## Objective

Turn `dashboard.py` into the actual GodView product: one portfolio-wide PIT decision surface that renders every real eligible proposal against one certified book, with governed identity acceptance and deterministic replayable read projections.

This phase deliberately stops before selection, risk math, preview, authorization, book mutation, certification changes, or deletion.

MU is the first real evidence case. It is not the pipeline model.

## Layer-first phase scope

### Layer 0 — bank the current real baseline

Verify and commit the existing five-path MU operated-versus-shadow slice:

```text
M  gv_portfolio_v0/prospective.py
M  views/gv_prospective_paper_workspace.py
M  tests/gv_portfolio_v0/test_real_evidence_mu.py
A  core/gv_v2_mu_nvda_shadow_decision.py
A  tests/gv_portfolio_v0/test_same_evidence_shadow.py
```

Banked result:

- approved executable: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe`;
- Python `3.12.10`; pytest `9.1.0`;
- focused tests: `9 passed`;
- exact baseline commit: `a520f475bfa4fca42a68a22165ab3ad8960c0bc9`;
- documentation and unrelated paths excluded;
- no tag and no push;
- no score uplift or terminal acceptance claimed;
- planning authority must now be committed separately as docs-only;
- a fully clean worktree remains mandatory before Slice 1 implementation.

### Layer 1 — immutable contracts

Create the minimum canonical contracts required by the real episode:

- one five-field `PointInTimeIdentity` whose certified head is the final authoritative event in the exact prefix certified by the active certification;
- `as_of_utc` bound to that certified head event's timestamp, never merely the last array element or wall clock;
- typed proof-carrying `NoMarketDependencyCashOnlyV1` for the current zero-market-dependency episode;
- typed cryptographic `EvidenceReference`;
- closed proposal outcome;
- `InstrumentTarget` with explicit `TARGET_FINAL`/`DELTA`/`OVERLAY` intent;
- `QUANTITY`/`NOTIONAL`/`WEIGHT` units only;
- orthogonal risk measure and risk unit;
- explicit numeric normalization policy;
- strict discriminated extension envelopes;
- immutable `CapitalProposal`.

No untyped module-details dictionary is permitted.

The no-market proof binds kind, certified book ID, certified head event ID, certified book hash, and validation digest. It is admitted only when positions, orders, and fills are empty; unexplained residual and all proposal target quantities are zero; and no notional/weight conversion, price data, yield, or market-derived return claim is consumed. The existing `reference_price = "1"` is not an admitted market observation.

### Layer 2 — verified real adapters

Adapt repository-grounded sources:

- operated MU from the active prospective workspace/proposal objects;
- independent shadow MU from `core/gv_v2_mu_nvda_shadow_decision.py`;
- cash baseline from the active certified workspace/book cash balance.

No new JSON/Parquet production format is introduced. Cash yield remains unavailable unless an admitted source is already present.

### Layer 3 — governance command authority

Add typed submission command and command handler. The handler:

- opens or receives the active episode identity;
- compares exact five-field identity;
- emits accepted or identity-rejected events;
- retains the complete immutable proposal on both paths;
- does not perform selection, target composition, preview, or mutation.

### Layer 4 — ordered event authority

Add a bounded deterministic digest-chained in-memory append/read stream with:

```text
stream_id
sequence_number
event_id
event_schema_version
timestamp_utc
correlation_id
causation_id
previous_event_digest
event_digest
```

Reject duplicate IDs, duplicate sequence positions, gaps, previous-digest mismatch, and conflicting idempotent replay.

Create no durable governance persistence in Slice 1. Durable storage is deferred until Slice 2 operator selections must survive restart.

### Layer 5 — deterministic read projections

Project valid events into:

- `ProposalRecordReadModel`;
- `DecisionEpisodeReadModel`.

Slice 1 statuses are only:

```text
proposal: ELIGIBLE | REJECTED_IDENTITY_MISMATCH
episode:  OPEN | ABORTED
```

No staged/selected state exists. Proposal ordering is canonical: event sequence, then record ID.

### Layer 6 — six-page product surface

`dashboard.py` remains the sole future GodView application. Page order:

```text
Command Center
Discovery & Analysis
Decisions & Thesis
Portfolio & Rotation
Strategy Modules
Operations & Replay
```

Command Center is default and renders the real projected episode. It shows:

- five-field PIT identity;
- current certified capital and classified cash;
- MU-operated, MU-shadow, and cash-baseline rows;
- eligibility/identity rejection;
- target intent and normalization summary;
- proposal disagreement and evidence gaps;
- compact system/replay health.

It emits no authoritative command beyond future explicitly scoped actions and performs no portfolio mutation in this phase.

## Expected Slice 1 bill of materials

The implementation is restricted to this exact compact ten-file scope:

```text
A  core/gv_pit/__init__.py
A  core/gv_pit/contracts.py
A  core/gv_pit/adapters.py
A  core/gv_pit/governance.py
A  core/gv_pit/read_models.py
A  views/command_center.py
M  views/page_registry.py
M  dashboard.py
M  tests/test_dash_1_page_registry_shell.py
A  tests/test_gv_pit_transaction.py
```

These files are one functional transaction, not independently bankable framework products. Slice 1 passes only as the complete real read-only episode through `dashboard.py`.

## Acceptance checks

### Contract and evidence

- [ ] Every proposal embeds the same five-field identity object.
- [ ] Certified book head is the final authoritative event in the exact certified prefix, not merely `events[-1]`.
- [ ] `as_of_utc` equals the certified head event timestamp.
- [ ] `NoMarketDependencyCashOnlyV1` is proof-carrying and rejected when any no-market predicate fails.
- [ ] `reference_price = "1"` is not consumed as market evidence.
- [ ] Evidence, schema, and payload digests have distinct canonical derivations.
- [ ] Extension schema/payload pairs are statically and runtime validated.
- [ ] Canonical financial values avoid unrestricted float authority.
- [ ] Normalization fields are explicit and no cross-asset defaults silently apply.

### Adapter integrity

- [ ] MU operated maps from the verified active object without an alternate serialization path.
- [ ] MU shadow maps from the verified pure shadow object.
- [ ] Cash maps from certified book/workspace cash.
- [ ] Missing cash yield or market identity fails closed or renders unavailable; nothing is fabricated.
- [ ] Production Command Center contains zero dummy proposal dictionaries.

### Command and event authority

- [ ] Identity validation occurs in the command handler, not adapter/projector/dashboard.
- [ ] Accepted and rejected events retain the complete proposal.
- [ ] Event envelope ordering and digest chain are deterministic.
- [ ] Duplicate IDs, duplicate positions, sequence gaps, and digest mismatch fail closed.
- [ ] Event reads return canonical order.

### Projection

- [ ] The projector is a pure fold over valid events.
- [ ] Slice 1 exposes only event-backed statuses.
- [ ] Identity-rejected proposal projects without `None` or a synthetic proposal.
- [ ] Equivalent streams yield byte-identical read models.
- [ ] Proposal rows are ordered by event sequence then record ID.

### Product surface

- [ ] Six page titles/order match the canonical contract.
- [ ] Command Center is default.
- [ ] Discovery & Analysis remains functional.
- [ ] The real three-row episode renders.
- [ ] Compact health is visible; full diagnostics live in Operations & Replay.
- [ ] Existing research/optimizer surfaces are visibly non-authoritative.
- [ ] AST scan reports zero raw session-state reads of governance authority.
- [ ] Ephemeral UI session state remains permitted.

### Negative authority proof

- [ ] Zero proposal selection.
- [ ] Zero target composition.
- [ ] Zero optimizer execution.
- [ ] Zero VaR/Sortino/risk implementation.
- [ ] Zero transition preview.
- [ ] Zero authorization.
- [ ] Zero portfolio book mutation.
- [ ] Zero certification change.
- [ ] Zero physical deletion.

## Later slices

### Slice 2 — selection and intent-aware composition

Add reject-all, one base `TARGET_FINAL`, compatible `DELTA`/`OVERLAY` legs, explicit per-leg acceptance, collision handling, and deterministic replayable selection events. No portfolio preview or mutation.

### Slice 3 — preview and capital authority

Add deterministic target resolution, costs, liquidity, cash, concentration, margin, multi-model risk receipt, immutable preview, stale-bound authorization, application, certification, and exact replay.

### Slice 4 — placement/extraction/deletion

Place all useful content under final pages and delete only verified displaced paths after dependency and behavior proof.

### Slice 5 — repeated operation

Operate 3–5 real identities and at least one independent module before any score uplift.

### Slice 6 — new modules

Add CTA/macro/cascade only through the frozen seam. Strategy formulas remain outside neutral core.

### Slice 7 — separately authorized Limited Live

Remains closed.

## Forbidden scope

No CTA or macro formulas, provider acquisition, optimizer authority, risk implementation, broker credentials, autonomous orders, client assets, advice activity, live capital, backward compatibility for obsolete authority paths, score uplift, or deletion in Slice 1.

## What Was Done

- Completed the planning-round reconciliation.
- Replaced the earlier seven-file shell-first Slice 1 with a layer-first real product transaction.
- Added explicit command-handler, ordered event-envelope/store, and pure projector authority.
- Grounded adapters in current repository objects and book cash.
- Separated evidence, schema, and payload digests.
- Restricted Slice 1 lifecycle states to its event vocabulary.
- Corrected session-state, risk, normalization, cash-yield, and deletion semantics.
- Published a complete planning checklist of locked and pending items.

## What Is Locked

- Accepted terminals and hosted-green evidence remain immutable.
- Accepted score remains `62/100`.
- The five-path shadow baseline is banked at `a520f475bfa4fca42a68a22165ab3ad8960c0bc9`.
- `dashboard.py` remains the sole future application.
- Slice 1 ends at the read-only Command Center.
- Limited Live remains closed.

## What Is Next

- Regenerate context and bank this planning authority as a separate docs-only commit.
- Verify a fully clean worktree.
- Freeze exact operated, shadow, certified cash, certified-prefix head, evidence, no-market proof, and as-of mappings.
- Execute the exact ten-file Layers 1–6 transaction and stop at the read-only Command Center.

## First Command

```text
python scripts/build_context_packet.py
```

## Next Todos

- Bank the final planning authority separately as docs-only and verify a clean tree.
- Freeze exact adapter, certified-prefix head, evidence, and no-market proof mappings.
- Implement the exact ten-file real read-only PIT episode using bounded in-memory governance.
- Stop before selection, durable governance persistence, preview, mutation, risk math, certification, or deletion.
