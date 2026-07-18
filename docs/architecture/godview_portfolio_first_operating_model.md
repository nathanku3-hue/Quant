# GodView Portfolio-First Operating Model

Status: Active Canon — GV-FS0 First
Date: 2026-07-16
Authority: `godview_endgame_vision.md`, `top_level_roadmap.md`, `godview_portfolio_p0_owner_freeze.md`, and `gv_fs0_certification_and_data_authority_contract.md`

## Product Decision

The first product is a deterministic, certified synthetic paper-book slice. It is not an optimizer-first product, broker, autonomous allocator, provider programme, or evidence of persistent alpha.

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot
→ Fs0Certification
→ Streamlit adapter
```

The prior six-stream concurrent execution authority is revoked. Streams A–F remain later endgame work packages activated through GV-FS1, GV-FS2, GV-RA0, GV-E0, and GV-P1.

## Active Authority

Authorized now:

- one new canonical `PortfolioBook` for GV-FS0;
- one synthetic `MANUAL_OWNER_PAPER / OPEN` decision;
- one synthetic `MANUAL_OWNER_PAPER / NO_POSITION` decision;
- 5–10 deterministic sessions for one security;
- one execution and explicit cost;
- one dividend ex-date and one pay date;
- exact cash, shares, receivables, NAV, and contribution;
- independent reconstruction from original inputs;
- immutable `Fs0Certification`;
- cross-platform canonical hash parity;
- a read-only Streamlit adapter.

Not authorized in GV-FS0:

- provider or network reads;
- real candidate admission;
- benchmark paths;
- C0/C1/P1/P2/P7;
- optimizer or return-aware challengers;
- 252-session replay;
- broad corporate-action matrices;
- inference or search-ledger implementation;
- broker, live orders, live capital, or live-trading monitoring;
- financial-alpha claims.

## Canonical Economic Book

`PortfolioBook` is the sole active official GodView economic truth for GV-FS0. It owns:

- accepted decisions;
- executions and costs;
- cash movements;
- whole-share holdings;
- dividend receivables and payments;
- session valuation;
- NAV and contribution;
- canonical serialization.

`strategies/strategy_replay.py` is not official GodView return truth. It may remain physically present for unrelated historical screens and regression coverage, but FS0 cannot import it, write its artifacts, or use its performance to upgrade authority.

`data/portfolio_lifecycle_log.py` is not the FS0 book. No compatibility conversion from legacy lifecycle events or target weights into `PortfolioBook` is permitted.

## DecisionEnvelope

Allowed FS0 cases:

```text
MANUAL_OWNER_PAPER / OPEN
MANUAL_OWNER_PAPER / NO_POSITION
```

Every envelope binds authority, action, decision/effective timestamps, security identity, requested quantity or deterministic sizing input, rationale reference, protocol, fixture, operator, and supersession identity.

Unknown authority, missing timestamps, ambiguous identity, or unsupported action blocks before book mutation.

## Portfolio Truth Invariants

1. quantities and cash are non-negative;
2. no implicit leverage exists;
3. `NAV = cash + market_value + receivables` every session;
4. prior effective holdings earn the interval result;
5. no post-decision information enters an earlier decision or execution;
6. dividend entitlement is created on ex-date and paid exactly once on pay date;
7. duplicate events are idempotent and conflicting duplicates block;
8. out-of-order events block;
9. missing returns, stale prices, and unsupported events never silently become zero;
10. `NO_POSITION` preserves all-cash economics while recording the decision;
11. identical normalized semantic inputs reproduce identical canonical hashes;
12. rendering cannot recompute or override official truth.

## Fs0PortfolioSnapshot

The snapshot is an immutable projection of one book/session. It reports authority, action, rationale reference, security, shares, cash, receivables, market value, NAV, contribution, book-event range, canonical hash, and certification status.

It cannot mutate the book or certify itself.

## Fs0Certification

Certification is a first-class immutable result with independent checks:

```text
decision_authority_valid
timestamp_causality_valid
price_freshness_valid
cash_conserved
holdings_valid
nav_reconciled
receivables_reconciled
unsupported_events_absent
independent_reconstruction_passed
canonical_hash_reproduced
certification_status
failure_reasons
```

Any false or unknown mandatory check produces `BLOCKED`.

## Independent Reconstruction

The independent path starts from the original decision, price, event, and protocol inputs. It shares no accounting, mutation, NAV, or canonical-serialization implementation with the primary path.

For FS0, primary and independent shares, cash, receivables, market value, NAV, and canonical payload hash must match exactly.

## Frozen Long-Run Mandate

The owner-freeze mandate remains unchanged for later real and policy stages:

- point-in-time Russell 1000 U.S. primary-listed common equities;
- IWB market-price total return in USD as primary benchmark;
- IWB NAV total return as secondary reconciliation only;
- USD 10 million reference NAV;
- daily SOFR minus 25 bp ACT/360 cash accrual, no zero floor;
- point-in-time ICB Level 1 sector classification;
- permanent capped equal weight;
- 10% security/issuer cap and 30% sector cap against total NAV;
- maximum 20 issuers;
- minimum ADV20 USD 20 million;
- maximum order 2% ADV20 and position 5% ADV20;
- 25% rolling-21-session and 150% rolling-252-session one-way turnover;
- residual cash and no forced full investment;
- no leverage, shorts, derivatives, FX positions, broker, or live orders.

These semantics do not enlarge GV-FS0 scope.

## Data Authority

Real-data permission and factual admission are separate.

### DataAccessAuthorization

Required before any real provider read. It identifies the exact provider/datasets, licence owner, permitted use, coverage, restrictions, accountable authorizer, repository/artifact identity, authorized actions, and expiration/revocation state.

It contains no credentials and cannot self-authorise.

### DataAdmissionCertificate

Created only after acquired bytes pass exact hashes, delivery/availability timing, bitemporal lineage, completeness, contradiction, schema, semantic, purpose, and rejected-use checks.

Synthetic fixtures require neither artifact. Real reads require the first. Real candidate admission requires both plus the unchanged full owner-freeze gate.

Current constituents, IWB holdings, ticker continuity, current sectors, adjusted close, yfinance, or silent proxies cannot authorize a real decision.

## Streamlit Boundary

Streamlit belongs only to presentation entrypoints and `views/**`.

The FS0 adapter consumes only `Fs0PortfolioSnapshot` and `Fs0Certification`. It cannot import the reducer, mutate the book, calculate NAV, create receivables, decide freshness, or aggregate certification.

A static import-boundary test is mandatory in the FS0 implementation round. No migration framework is required.

## Portability Boundary

All new FS0 paths use:

- `sys.executable`;
- `pathlib`;
- normalized path-independent payloads;
- canonical hashes without absolute paths, platform timestamps, machine names, or environment-specific interpreter locations.

No new FS0 path may use drive-letter paths or `.venv/Scripts/python.exe`. Historical portability debt is not a prerequisite for FS0.

## Staged Activation

### GV-FS0

One decision, one book, one certification, one screen.

### GV-FS1

Add C0/C1/P1/P2/P7, capped equal weight, costs, turnover, IWB shadow, and 252-session deterministic replay. Still synthetic.

### GV-FS2

Add bitemporal authority fixtures, correction handling, broad corporate actions/delistings, 20+ goldens, property tests, reconciliation tolerances, and certification aggregation.

### GV-RA0

Require `DataAccessAuthorization`, authorised acquisition, `DataAdmissionCertificate`, 60 authoritative sessions, 99.95% completeness, zero unresolved contradictions, and independent review.

### GV-E0

Connect the MU `G_supply` research packet to the same decision, book, snapshot, and certification path. The four frozen E0 artifacts remain unchanged.

### GV-P1

Add challengers, timing variants, search history, stationary bootstrap, multiplicity control, and long-horizon prospective assessment only after earlier gates pass.

## Legacy Boundary

Legacy code and artifacts may remain temporarily, but:

- legacy replay is not imported by FS0;
- legacy lifecycle is not written by FS0;
- legacy artifacts cannot certify FS0;
- legacy performance cannot upgrade authority;
- deletion is not a prerequisite;
- compatibility conversion is prohibited.

## Held

- real provider reads without detached authorization;
- real candidate admission without both data artifacts and full admission;
- yfinance or convenience-data authority;
- WRDS-dependent PEAD reopening;
- optimizer production preference;
- event-alpha implementation;
- broker, live orders, leverage, shorts, derivatives, or live capital;
- any alpha claim from architecture, synthetic tests, or accounting success.
