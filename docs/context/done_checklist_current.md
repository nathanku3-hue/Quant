# Done Checklist — GV-DASHBOARD-ALL-CAPITAL-PIT-1

Date: 2026-08-03
Status: `OPEN — BASELINE BANKED; DOCS CUSTODY PENDING`
Canonical detailed checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

## Slice 0 — baseline bank

- [x] Focused real-MU and same-evidence shadow tests passed: 9 tests under Python 3.12.10 / pytest 9.1.0.
- [x] Exactly five code/test paths are committed at `a520f475bfa4fca42a68a22165ab3ad8960c0bc9`.
- [x] No documentation or unrelated files entered the baseline commit.
- [x] No Git tag or push was created.
- [ ] Documentation authority is committed separately and the worktree is fully clean before Slice 1 implementation.

## Slice 1A — immutable contracts

- [ ] One five-field `PointInTimeIdentity` is embedded unchanged in proposals and episode.
- [ ] Certified head is the final authoritative event in the exact prefix certified by the active certification, not merely `events[-1]`.
- [ ] `as_of_utc` equals that certified head event's timestamp.
- [ ] `NoMarketDependencyCashOnlyV1` carries book/head/hash/validation proof and is admitted only when every no-market predicate passes.
- [ ] Existing `reference_price = "1"` is not consumed as market evidence.
- [ ] Proposal outcome and evidence references are typed.
- [ ] Evidence digest, schema digest, and canonical payload digest have distinct derivations.
- [ ] Target intent is `TARGET_FINAL`, `DELTA`, or `OVERLAY`.
- [ ] Instrument units are `QUANTITY`, `NOTIONAL`, or `WEIGHT`; no `RISK_BPS` instrument unit.
- [ ] Risk measure and unit are orthogonal.
- [ ] Authoritative financial values use exact numeric representations.
- [ ] Normalization policy explicitly binds quantum, rounding, currency, price identity, multiplier, and lot policy.
- [ ] Strict discriminated extension envelopes reject mismatched/untyped payloads.

## Slice 1B — verified real adapters

- [ ] MU operated maps from the existing prospective workspace/proposal object path.
- [ ] MU shadow maps from `core/gv_v2_mu_nvda_shadow_decision.py`.
- [ ] Cash baseline derives from active certified workspace/book cash.
- [ ] No new JSON/Parquet production path is created.
- [ ] Missing cash yield or market identity is unavailable/fail-closed, never fabricated.
- [ ] Adapter mapping does not mix proposal, decision snapshot, and lifecycle state.
- [ ] Production Command Center contains zero dummy proposal dictionaries.

## Slice 1C — command authority

- [ ] Typed submission command contains the full immutable proposal.
- [ ] Command handler, not adapter/dashboard/projector, validates exact five-field identity.
- [ ] Handler emits accepted or identity-rejected event.
- [ ] Rejection path retains the complete immutable proposal.
- [ ] No selection, target composition, preview, or mutation occurs.

## Slice 1D — ordered event authority

- [ ] Event envelope contains stream, sequence, event/schema, time, correlation, causation, previous digest, and event digest.
- [ ] Canonical event bytes and domain-separated digest rules are frozen.
- [ ] Duplicate event IDs fail closed.
- [ ] Duplicate sequence positions fail closed.
- [ ] Sequence gaps fail closed.
- [ ] Previous-digest mismatch fails closed.
- [ ] Conflicting idempotent replay fails closed.
- [ ] Reads return canonical sequence order.
- [ ] Governance uses the bounded deterministic digest-chained in-memory stream; no durable governance persistence is created.

## Slice 1E — event-derived projections

- [ ] Projector is a pure deterministic fold over valid events.
- [ ] Slice 1 proposal states are only `ELIGIBLE` and `REJECTED_IDENTITY_MISMATCH`.
- [ ] Slice 1 episode states are only `OPEN` and `ABORTED`.
- [ ] No staged/selected/authorized state exists.
- [ ] Identity-rejected row projects without `None` or fabricated proposal data.
- [ ] Canonical row order is event sequence then record ID.
- [ ] Equivalent streams produce byte-identical read models.

## Slice 1F — six-page product surface

- [ ] `dashboard.py` remains the sole future GodView app.
- [ ] Page order matches the canonical six-page contract.
- [ ] Command Center is default.
- [ ] Discovery & Analysis remains functional.
- [ ] Real MU-operated, MU-shadow, and book-derived cash rows render under one PIT identity.
- [ ] Current capital, identity status, disagreement, evidence gaps, and compact health render.
- [ ] Operations & Replay owns full diagnostics.
- [ ] Existing strategy/replay/optimizer outputs are visibly non-authoritative.
- [ ] AST scan finds zero raw session-state reads of governance authority.
- [ ] Ephemeral UI session state remains permitted.
- [ ] AppTest uses real production adapters with isolated storage/clock/UI boundaries.

## Slice 1 negative proof

- [ ] Zero proposal selection.
- [ ] Zero target composition.
- [ ] Zero optimizer execution.
- [ ] Zero VaR/Sortino/risk implementation.
- [ ] Zero transition preview.
- [ ] Zero authorization.
- [ ] Zero book mutation.
- [ ] Zero certification change.
- [ ] Zero physical deletion.

## Slice 2 — selection and composition

- [ ] Reject-all/no-action is first-class.
- [ ] At most one base `TARGET_FINAL` is selected.
- [ ] Compatible `DELTA`/`OVERLAY` legs are explicit.
- [ ] Multiple absolute targets fail closed until arbitration.
- [ ] Selection commands/events replay deterministically.
- [ ] No preview or portfolio mutation occurs.

## Slice 3 — portfolio authority

- [ ] Target resolution binds exact price/multiplier/currency/lot identities.
- [ ] Preview is immutable and mutation-free.
- [ ] Risk receipt is multi-model and exposes disagreement.
- [ ] Authorization binds preview digest, current book head, episode, operator, and expiry.
- [ ] Changed, expired, blocked, or stale preview cannot authorize.
- [ ] Authorization, application, and certification are distinct events.
- [ ] Exact replay reconstructs resulting authority.

## Holds

- [ ] No CTA/macro/Leningrad formulas in Slice 1.
- [ ] No provider or optimizer-authority expansion.
- [ ] No broker/live-capital path.
- [ ] No deletion before repository-grounded dependency and behavior proof.
- [ ] No accepted-score uplift without new operated evidence.
