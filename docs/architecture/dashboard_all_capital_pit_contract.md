# Dashboard All-Capital PIT Contract

Status: `ACTIVE ARCHITECTURE AUTHORITY — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`
Decision: `DASHBOARD_FIRST; ALL_PROPOSAL_PIT; LAYER_FIRST AUTHORITY; STRATEGY LOGIC OUTSIDE UI`

## 1. Product law

GodView is one portfolio-wide operator decision loop:

```text
certified point-in-time identity
→ verified strategy/book adapters
→ immutable proposals
→ typed submission commands
→ five-field identity decision
→ ordered append-only governance events
→ deterministic read projections
→ dashboard comparison
→ later intent-aware selection
→ later calculation-only preview
→ later explicit authorization
→ applied and certified portfolio events
→ exact replay
```

MU is the first real case, not the workflow unit. The product question is:

> Given the certified book and every eligible proposal available at this PIT, what capital transition—if any—should be staged?

Pages are read projections over this loop. They are not domain boundaries and cannot create authority merely by rendering a control.

## 2. Layer-first architecture

The roadmap is layer-first because higher layers cannot safely exist without the lower identity and event contracts. Layers are not independently shippable architecture programmes; Slice 1 passes only when the real read-only PIT episode reaches the Command Center.

### Layer 0 — accepted custody and baseline

Owns accepted operated portfolio, certified book, evidence, existing event/replay substrate, and the focused current MU operated-versus-shadow baseline.

### Layer 1 — immutable domain contracts

Owns `PointInTimeIdentity`, cryptographic evidence references, normalized targets, strict module-extension envelopes, and immutable `CapitalProposal`.

### Layer 2 — verified source adapters

Adapts the real active MU-operated workspace/proposal, independent MU-shadow decision, and certified-book cash balance. It creates no new JSON/Parquet production path and invents no missing yield or market identity.

### Layer 3 — governance command authority

Receives typed proposal-submission commands, validates the exact PIT identity, and decides accepted versus rejected facts. The dashboard, adapters, event store, and projector cannot make this decision.

### Layer 4 — ordered event authority

Owns append-only stream ordering, event identity, digest chaining, duplicate/gap rejection, and canonical reads. Existing persistence should be adapted rather than replaced by a competing authority path.

### Layer 5 — deterministic projections

Purely folds valid events into `ProposalRecordReadModel` and `DecisionEpisodeReadModel`. It makes no decisions, emits no events, calls no providers, and mutates no storage.

### Layer 6 — product surface

`dashboard.py`, six-page navigation, and read-only Command Center consume projected state. Streamlit session state is UI convenience only.

### Layer 7 — selection and composition

Later Slice 2 owns reject-all/select-one/base-plus-overlay selection and intent-aware target resolution. It owns no preview or portfolio mutation.

### Layer 8 — portfolio preview and authority

Later Slice 3 owns risk/cost/limit evaluation, immutable preview, stale-bound authorization, application, certification, and exact authority replay.

### Layer 9 — consolidation, repeated operation, and expansion

Places all useful content, deletes displaced paths after proof, runs repeated real episodes, and later adds independent CTA/macro/cascade modules through the neutral seam. Limited Live remains separately gated.

## 3. Canonical five-field PIT identity

One immutable `PointInTimeIdentity` is embedded unchanged in every proposal and episode:

```text
certified_book_id
certified_book_head_event_id
evidence_set_id
market_snapshot_id
as_of_utc
```

Rules:

- `certified_book_head_event_id` is the final authoritative event in the exact event prefix certified by the active certification; it is never inferred as merely `events[-1]`.
- `as_of_utc` is that certified head event's timestamp, not wall-clock `now()` and not a later observation, rejection, UI, or certification marker.
- Proposal compatibility is exact object equality.
- Partial matches and warning-only mismatches are forbidden.
- A mismatch is ineligible and produces an immutable rejection fact.
- The active certified-book head field must map to the repository’s actual exact certified-prefix identity; implementation must not fabricate a new identity merely to satisfy this name.

### 3.1 Proof-carrying cash-only no-market identity

The current real MU episode has no admitted production market snapshot and consumes no market data. Slice 1 may therefore bind `market_snapshot_id` to a typed `NoMarketDependencyCashOnlyV1` proof object containing:

```text
kind = NO_MARKET_DEPENDENCY_CASH_ONLY_V1
certified_book_id
certified_book_head_event_id
certified_book_hash
validation_digest
```

The handler may construct or admit this variant only after verifying all predicates:

```text
positions == []
orders == []
fills == []
unexplained_residual == 0
all proposal instrument target quantities == 0
no notional or weight conversion
no price-data consumption
no yield or market-derived return claim
```

The existing scenario field `reference_price = "1"` is not an admitted market observation and must not be consumed by Slice 1 adapters. Any violated predicate rejects the no-market variant and requires a real identified market snapshot in a later slice.

## 4. Immutable proposal and evidence contract

`CapitalProposal` is evidence, not lifecycle state. It contains:

```text
proposal_id
module_id
module_version
pit_identity
sleeve_id
outcome
targets
risk_targets
quantitative_boundaries
principal_claim
supporting_evidence
contradicting_evidence
missing_discriminator
reason_not_to_act
extension
```

### 4.1 Proposal outcome

Use a closed typed outcome vocabulary appropriate to the proposal layer. Exact enum members are frozen during implementation after mapping the existing operated and shadow semantics. Unrestricted free-text outcomes are not canonical authority.

### 4.2 Evidence references

Evidence uses typed references containing:

```text
evidence_id
sha256_digest
source_identity
```

Evidence references must identify immutable upstream bytes or an equivalent content-addressed repository object.

### 4.3 Three distinct digests

These identities are never interchangeable:

```text
EvidenceReference.sha256_digest
    = digest of the upstream evidence artifact

extension.schema_digest
    = digest of the canonical schema definition

extension.canonical_payload_digest
    = digest of canonical serialized extension payload bytes
```

Canonical serialization and domain-separated hashing must be frozen before persistence/replay authority is claimed.

## 5. Strict extension envelopes

The contract layer permits no `Mapping[str, object]`, `Mapping[str, Any]`, generic module-details bucket, or required-key-only validator.

Use a discriminated union of complete envelope types. Each envelope binds:

```text
schema_id
schema_version
schema_digest
canonical_payload_digest
typed payload
```

The schema ID and payload type cannot be independently paired. Unknown schemas, unexpected fields, mismatched payload types, schema drift, digest drift, and post-open mutation fail closed.

Initial live schemas are limited to the real equity/MU and cash-baseline needs. A CTA envelope may be frozen as a future seam only; no CTA formulas or sizing enter Slice 1.

## 6. Target intent, unit, and normalization

### 6.1 Intent

Every instrument target declares one intent:

- `TARGET_FINAL` — absolute desired final exposure.
- `DELTA` — incremental movement relative to the certified book.
- `OVERLAY` — bounded additive exposure in an explicit overlay sleeve.

Intent is not inferred from unit type.

### 6.2 Instrument units

Initial instrument units are:

```text
QUANTITY
NOTIONAL
WEIGHT
```

`RISK_BPS` is not an instrument unit and is never generically converted to quantity/notional by the neutral core.

### 6.3 Risk target

Risk target separates metric from unit:

```text
measure = VAR | VOL | GROSS | MARGIN | DELTA
unit    = BPS | PERCENT | USD | NOTIONAL
```

### 6.4 Numeric normalization

Authoritative prices, quantities, notionals, and target values use `Decimal` or exact integer minor units. Authoritative bps fields use integers. Analytics-only z-scores/ratios may use floats when excluded from economic authority and canonical hashes.

Every target binds an explicit normalization policy:

```text
unit_quantum
rounding_mode
currency
price_identity
contract_multiplier
lot_size_policy
```

No asset-class-wide fallback silently assumes USD, multiplier 1, canonical close, or fractional lots. Contract multiplier has one canonical location in normalization, not duplicated inside strategy diagnostics.

Some fields may be conditionally unnecessary at ingestion—for example, a pure weight proposal may not yet need a price conversion—but portfolio preview must fail closed until every required conversion identity is available.

## 7. Intent-aware composition

The initial transition grammar is:

```text
zero or one selected base TARGET_FINAL proposal
+ zero or more compatible DELTA/OVERLAY legs
+ explicit per-target acceptance or override records
```

Rules:

- Multiple selected base targets are a conflict until explicit arbitration chooses one or constructs a new operator-owned target.
- Absolute targets are never combined by repeatedly subtracting the current book.
- Valid outcomes include reject all, select one base, base plus compatible overlays, and partial acceptance of explicit target legs.
- Selection need not be winner-take-all.
- Selection/composition is Slice 2 and is absent from Slice 1 read models.

## 8. Governance commands and decisions

A typed proposal-submission command enters a governance command handler.

Correct path:

```text
verified adapter
→ SubmitProposalCommand containing the full immutable proposal
→ handler compares proposal.pit_identity with episode.pit_identity
→ accepted or identity-rejected governance event
→ event append
→ pure projector
→ read model
```

The natural event vocabulary must retain the full proposal before or with rejection. A rejected proposal row cannot depend on a prior accepted event and cannot project a fabricated `None` proposal.

The exact event names may align with existing `gv_portfolio_v0` conventions, but these semantics are fixed:

- adapters translate source objects only;
- handler decides acceptance/rejection;
- event store orders facts only;
- projector folds facts only;
- dashboard renders projections only.

## 9. Ordered append-only event authority

Each event is wrapped by an ordered envelope containing at least:

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
payload
```

The append/read contract must:

- append only at the expected next sequence;
- reject duplicate event IDs;
- reject duplicate sequence positions;
- reject sequence gaps;
- reject previous-digest mismatch;
- reject conflicting idempotent replay;
- return canonical sequence order;
- verify canonical event bytes and digest chain.

Slice 1 uses one bounded deterministic digest-chained in-memory stream sourced from existing immutable artifacts. It proves ordering, duplicate/gap rejection, digest-chain validation, canonical reads, and replay without creating durable governance persistence or a second authority path. Durable governance storage becomes decision-relevant in Slice 2 when operator selections must survive restart.

## 10. Slice 1 event-derived read models

`ProposalRecordReadModel` and `DecisionEpisodeReadModel` are projections only.

Slice 1 proposal statuses are limited to event-backed states:

```text
ELIGIBLE
REJECTED_IDENTITY_MISMATCH
```

Slice 1 episode statuses are:

```text
OPEN
ABORTED
```

Slice 1 has no staged state, selected proposal state, authorization, preview, or mutation semantics. `selected_record_ids` is absent or mechanically empty.

The projector:

- is a pure deterministic fold;
- validates event shape/order assumptions but does not make business decisions;
- projects proposal rows in declared canonical order: event sequence, then record ID;
- produces byte-identical read models from equivalent streams;
- never consults wall-clock time, providers, session state, or mutable external state.

## 11. Verified adapter seam

Repository-grounded current sources are:

- MU operated: current prospective workspace/proposal objects in `gv_portfolio_v0/prospective.py` and their existing composition path in `views/gv_prospective_paper_workspace.py`.
- MU shadow: `core/gv_v2_mu_nvda_shadow_decision.py`.
- Cash baseline: classified/unallocated cash from the active certified workspace/book.

Rules:

- Production Command Center contains zero static dummy proposal rows.
- Do not invent new JSON/Parquet production files.
- Adapter tests may use deterministic fixtures.
- Cash yield/collateral rate requires an identified admitted source. When unavailable, the adapter exposes unavailable yield rather than fabricating a value.
- The cash-only no-market proof must not consume `reference_price`, price data, notional/weight conversion, yield, or market-derived return claims.
- Implementation must determine whether the operated adapter reads a current proposal, review, or authoritative decision snapshot without silently mixing lifecycle layers.

## 12. Dashboard and session-state boundary

`dashboard.py` remains the sole future GodView application. `views/page_registry.py` owns the six-page route. `views/command_center.py` is a new file in the current checkout.

Command Center receives a projected `DecisionEpisodeReadModel` through an explicit composition root.

Allowed Streamlit session state:

```text
active tab
pagination
sort/filter controls
expanded rows
ephemeral form inputs
```

Forbidden raw session-state authority:

```text
certified book
active proposals
episode state
transition candidate
preview
authorization
certification
```

The AST gate detects raw access to authoritative governance keys; it does not prohibit every `st.session_state` use.

A meaningful AppTest uses real production adapters while isolating storage, clock, and Streamlit boundaries. The invariant is no fabricated production proposal rows and no alternate production serialization path.

## 13. Six visible pages

| Page | Operator question | Slice 1 behavior | Later behavior | Prohibited authority |
|---|---|---|---|---|
| Command Center | What capital decision needs me now? | Read-only PIT identity, capital, real proposal rows, identity status, disagreement/evidence gaps, compact health | Selection, preview request, confirmation entry | Strategy math, event decisions, portfolio mutation |
| Discovery & Analysis | What evidence or opportunity changed? | Preserve current discovery/evidence functionality | Open admitted evidence into proposal workflow | Ranking authority, book mutation |
| Decisions & Thesis | Why does each module propose action or abstention? | Read-only proposal/evidence detail and history | Typed annotations and later commands | Signal calculation, lifecycle mutation |
| Portfolio & Rotation | What would a selected transition do? | Current certified book/history only | Candidate, preview, explicit confirmation, applied/certified history | Strategy generation, direct book writes |
| Strategy Modules | What modules and diagnostics exist? | Registry and non-authoritative research/replay | Additional modules through neutral seam | Canonical allocation or authorization |
| Operations & Replay | Can the system be trusted and reconstructed? | Source freshness, event/read-model integrity, current replay health | Preview/authorization/certification replay and deletion proof | Proposal selection, strategy logic |

## 14. Slice sequence

### Slice 0 — bank current same-evidence baseline

One focused commit, no tag and no release ceremony:

```text
M  gv_portfolio_v0/prospective.py
M  views/gv_prospective_paper_workspace.py
M  tests/gv_portfolio_v0/test_real_evidence_mu.py
A  core/gv_v2_mu_nvda_shadow_decision.py
A  tests/gv_portfolio_v0/test_same_evidence_shadow.py
```

It is banked at commit `a520f475bfa4fca42a68a22165ab3ad8960c0bc9` after the two focused test modules passed. It is known-good refactor input, not the pipeline model and not score uplift.

### Slice 1 — real read-only all-proposal PIT transaction

Layer order:

```text
contracts
→ verified adapters
→ commands/handler
→ ordered event authority
→ pure projector/read models
→ six-page registry
→ read-only Command Center
```

Exact ten-file bill of materials:

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

The compact modules retain the required layers without creating a speculative framework. Slice 1 is accepted only when the real MU-operated, MU-shadow, and book-derived cash rows render under one PIT episode through `dashboard.py`.

Slice 1 explicitly has:

```text
zero selection
zero optimizer
zero risk math
zero preview
zero authorization
zero book mutation
zero certification change
zero deletion
```

### Slice 2 — deterministic selection and composition

Add reject-all, one-base-plus-compatible-overlay selection, explicit per-leg acceptance, conflict handling, and deterministic target normalization. Joint optimization remains a research challenger.

### Slice 3 — preview, authorization, application, certification, replay

Add multi-model risk/cost/limit receipts, immutable preview, stale-preview protection, explicit authorization, applied/certified events, and exact authority replay.

## 15. Preview and authorization law

`TransitionPreview` is immutable calculation output with zero execution authority. It binds:

```text
preview_id
preview_digest
candidate_id
episode_id
certified_book_id
certified_book_head_event_id
as_of_utc
expires_at_utc
risk_and_cost_results
```

Authorization binds exact preview ID/digest, episode, current book/head, operator, and expiry. Changed, expired, blocked, or stale previews cannot authorize.

Authorization, application, and certification are distinct facts unless a separately approved product definition changes what a certified book represents.

## 16. Risk model boundary

No VaR or Sortino implementation belongs in Slice 1.

Future risk authority emits a multi-model receipt that may include:

- historical simulation as a primary estimate;
- delta-normal as a diagnostic control;
- deterministic stress scenarios;
- concentration and liquidity constraints;
- visible model disagreement.

No single estimator is allocation truth. Joint scaling/optimization remains a challenger until return calibration, downside/covariance policy, constraints, and prospective evidence are explicit.

## 17. Deletion mandate

No physical deletion occurs in Slice 1.

Repository-grounded facts:

- current standalone path is `operated_portfolio_app.py`, not `operated_app.py`;
- `views/command_center.py` is currently absent and will be added;
- legacy view names require existence/import proof before becoming deletion authority.

Deletion requires:

```text
verified path exists
+ zero active imports/callers
+ behavior parity through dashboard
+ focused and regression tests
+ rollback evidence
```

Session-state cleanup targets raw governance authority, not ephemeral UI controls.

## 18. Explicitly deferred and forbidden

- CTA, macro, microstructure, Leningrad, carry, absorption, cascade, or sizing formulas;
- provider acquisition or canonical data expansion;
- optimizer-led allocation authority;
- broker credentials or autonomous submission;
- client assets, advice activity, or live capital;
- backward-compatibility adapters for obsolete page/challenger authority;
- accepted-score uplift;
- deletion before dependency proof.

## 19. Immediate execution boundary

The next round is not another architecture round. It is:

```text
baseline commit a520f475 is banked
→ correct and bank documentation authority
→ verify a fully clean worktree
→ freeze exact operated/shadow/book/certified-prefix mappings
→ execute the exact ten-file Slice 1 transaction
→ stop at read-only Command Center
```

The approved interpreter is `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe` (`Python 3.12.10`, `pytest 9.1.0`) and the two focused baseline modules passed before the baseline commit.

Stop and report rather than inventing data when:

- real proposal sources cannot bind one five-field identity;
- the certified event-prefix head cannot be mapped to existing custody;
- the proof-carrying cash-only no-market predicates fail and no real market snapshot exists;
- cash yield would need to be fabricated;
- event ordering would require durable or competing persistence in Slice 1;
- implementation crosses into selection, preview, mutation, risk math, certification, or deletion.
