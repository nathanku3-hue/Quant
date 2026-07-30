# GV-DETERMINISTIC-REPLAY-0 Brief

Date: 2026-07-30
Mode: `EXECUTION_PACKET`
Status: `ACCEPTED_IMMUTABLE`
Authority: independent A/B/C PASS; PR #11 merged as exact SHA; tag `gv-replay-0-terminal`
Terminal SHA: `0e4b93fb370f67956502edc02e9c6f56ceb2eba3`

## Immutable bases

| Role | Exact SHA | Note |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | immutable; do not rewrite |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | tag `gv-replay-0-base` |
| **Replay 0 code terminal** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | **tag `gv-replay-0-terminal`; ACCEPTED** |

Ancestry: `85e6601` → … → `03a5c92` → `9bee439` → **`0e4b93f`**.

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 phase: `GV-DETERMINISTIC-REPLAY-0` — **accepted immutable** at `0e4b93f`.
- L2 active phase: `GV-BOUNDED-PORTFOLIO-1` (see `docs/context/ACTIVE_BRIEF`).
- L2 deferred: Portfolio Scale, Universe Scale, Challenger Promotion, Limited Live Capital.

## Recommended next action

Do not reopen Replay feature work except explicit Medium debt (R0-D1 multi-hop reopen; R0-D2 residual-vs-`book_hash` consumer docs). Execute only `GV-BOUNDED-PORTFOLIO-1` pinned to Replay code base `0e4b93f`.

## Product target

```text
frozen Slice 0 event log + manifests
→ reconstruct exact book, cash, quantities, costs, NAV
→ reconstruct thesis / decision state
→ preserve byte-stable prior certifications under corrections
→ exercise corporate-action correction, partial fill, idempotence
→ valuation-pending without fabricated prices
→ zero unexplained residual at declared precision
```

## Acceptance

- exact cash, quantities, costs, NAV, and thesis state versus Slice 0 operated books;
- prior certifications remain byte-stable under append-only corrections;
- idempotent replay of the same event prefix;
- correction lineage without rewrite of prior certs;
- partial-fill residual state;
- valuation-pending without inventing prices;
- one split or equivalent value transfer already exercised by Slice 0;
- zero unexplained residual at declared precision;
- no optimizer, provider programme, alpha claim, broker, or live capital.

## Custody gates already banked (do not reopen)

- Relocatable G4 path + `repo_root` resolve (`docs/architecture/gv_relocatable_custody_gate.md`).
- MSFT G8.2 hash hygiene retained.
- MU live package keeps historical non-binding `368c4fb3…` for V2-B0; G8 same-path hash-match PASS is **retired** from the custody gate with replacement truth test.
- Independent A/B/C PASS on `03a5c92`; candidate-only failures versus `85e6601` = 0.

## Operational gates

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Terminal remote Slice 0            1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         0/1
```

## Carried Medium debt

| ID | Item |
|---|---|
| R0-D1 | Multi-hop `reopen_with_stable_prior` parent handling |
| R0-D2 | `book_hash` excludes `partial_fill_residuals` (field/ledger authoritative) |

## Forbidden scope

providers · WRDS acquisition · broad historical loaders · optimizer · copula/MES production · automated graph propagation · adaptive intraday execution · tactical capital · broad tax · multi-currency · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · reopening Slice 0 product feature work · “fixing” MU declared hash to green old G8 · squash of terminal `0e4b93f`

## Stop rules

1. Stop if Replay terminal `0e4b93f` is rewritten or force-moved.
2. Stop if Slice 0 base `85e6601` is rewritten or force-moved.
3. Stop if MU historical non-binding is broken without a full V2-B0 product redesign packet.
