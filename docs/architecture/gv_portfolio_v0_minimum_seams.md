# GV Portfolio V0 — Minimum Cross-Layer Seams

Status: frozen for `GV-MICRO-PORTFOLIO-VERTICAL-0`
Base authority: `1db250169cdfe57ffa5d5cc5e5d24b2e937d5d33`
Namespace: `gv_portfolio_v0`

This contract freezes only the identities exercised by the first complete operator loop. It does not create a general ontology or mutate released `gv_fs0_v1`.

## Canonical basis

- Canonical documents use the existing frozen UTF-8 canonical JSON encoder without changing its code or contracts.
- Every identifier is derived from a domain-separated SHA-256 hash of its immutable preimage.
- Monetary and quantity values are decimal strings at declared precision; binary floats are prohibited from authority surfaces.

## Nine seams

| Seam | Required preimage fields | Vertical use |
|---|---|---|
| `InstrumentId` | issuer/asset identity key, security class, permanent namespace | four reviewed securities plus benchmark |
| `EventId` | book, event type, effective timestamp, source identity, immutable payload | split, aim, order, fill, observation, certification reference |
| `EvidenceReference` | content SHA-256, media type, locator, observed-at timestamp | thesis and later WATCH observation |
| `PortfolioBookEvent` | `EventId`, event type, effective timestamp, instrument or cash bucket, payload | sole economic truth input |
| `DecisionSnapshotId` | reviewed instruments, evidence references, outcomes, capital competition result | immutable original decision snapshot |
| `PortfolioAimId` | mandate text, benchmark, risk/cash constraints, effective timestamp | confirmed aim and unchanged later-observation comparison |
| `OrderId` | decision snapshot, aim, instrument, side, quantity, limit/reference price | one deterministic paper order |
| `FillId` | order, quantity, price, fee, fill timestamp | one deterministic complete fill |
| `CertificationId` | canonical event ledger hash, terminal book hash, checks, declared precision | persisted/reopened certification |

## Invariants

1. A 2:1 split doubles quantity and halves reference price with zero value transfer residual at declared precision.
2. Classified cash is part of the book and NAV; fees reduce cash and NAV explicitly.
3. The original `DecisionSnapshotId` never changes after order creation.
4. Later evidence creates a new evidence/event identity but cannot rewrite the original snapshot.
5. Reopen must recompute and match event, book, and certification hashes before presenting authority.
6. A WATCH observation without a hard falsifier preserves the `PortfolioAimId` and must explain that no aim-changing rule fired.
7. No price may be invented. Missing valuation produces `VALUATION_PENDING`, not a fabricated NAV.

## Deliberately deferred

Provider schemas, tax lots, FX, derivatives, shorting, leverage, optimization, broad corporate-action catalogues, broker integration, live capital, and score uplift.
