# Multi-Stream Contract — Current

Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Status: `ONE SERIAL PRODUCT TRANSACTION; BOUNDED PARALLELISM ONLY`

## Active layers and ownership

### Layer 0 — baseline custody

Owns the exact five current code/test paths and focused test/commit evidence.

### Layer 1 — contracts

Owns PIT identity, evidence/digests, targets/normalization, strict extensions, and proposal.

### Layer 2 — adapters

Owns mapping from verified operated, shadow, and certified-book cash sources. It owns no business decisions.

### Layer 3 — governance commands

Owns proposal submission, five-field identity decision, and accepted/rejected event emission.

### Layer 4 — event authority

Owns stream ordering, digest chain, append/read, duplicate/gap rejection, and idempotence.

### Layer 5 — projections

Owns pure deterministic read-model folding and canonical ordering.

### Layer 6 — product surface

Owns six-page registry, Command Center, read rendering, AppTest, and session-state authority scan.

## Deferred streams

- selection and intent-aware composition;
- portfolio risk/cost preview and stale-bound authorization;
- application/certification replay changes;
- content deletion;
- CTA/macro/provider expansion;
- broker/live work.

## Parallelism law

Layers are acceptance dependencies and execute in order. Parallel implementation is allowed only after the shared lower-layer contract is frozen, files are disjoint, and each lane can merge without creating a second event, persistence, identity, or dashboard authority.

No layer may be reviewed or banked as standalone product progress. Slice 1 passes only when the real three-row episode renders through `dashboard.py`.

## Handoffs

```text
contracts → adapters: exact typed inputs and canonical digests
adapters → handler: full immutable proposal
handler → event authority: accepted/rejected fact
ordered events → projector: valid canonical stream
projector → dashboard: immutable read model
```

## Stop condition

Any ambiguity in book head, market snapshot, cash yield, evidence digest, event ordering, or lifecycle source is surfaced and resolved against repository truth; it is never filled by assumption.
