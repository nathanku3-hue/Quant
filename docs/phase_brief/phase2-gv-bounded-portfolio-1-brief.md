# GV-BOUNDED-PORTFOLIO-1 Brief

Date: 2026-07-30
Mode: `EXECUTION_PACKET`
Status: `IMPLEMENTATION_IN_PROGRESS; BRANCH_FROM_5fc2e4c`
Authority: Replay 0 accepted at exact terminal `0e4b93f`; implementation branch `codex/gv-bounded-portfolio-1`

## Immutable pins (do not rewrite)

| Role | Exact SHA | Note |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | tag `gv-slice-0-terminal` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | tag `gv-replay-0-base` |
| **Replay 0 code terminal** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | **tag `gv-replay-0-terminal`; pin for Bounded Portfolio implementation** |

Ancestry: `85e6601` → … → `03a5c92` → `9bee439` → **`0e4b93f`** (ACCEPT_REPLAY_0) → this docs-only promotion tip.

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 active phase: **`GV-BOUNDED-PORTFOLIO-1` only**.
- L2 closed / immutable: Slice 0 @ `85e6601`; Replay 0 code @ `0e4b93f`.
- L2 deferred: Portfolio Scale, Universe Scale, Challenger Promotion, Limited Live Capital.

## Recommended next action

Continue on branch `codex/gv-bounded-portfolio-1` (from promotion tip `5fc2e4c`). Keep Replay code pin `0e4b93f` frozen. Every cycle: Replay baseline `105 pass / 1 skip` unchanged; bounded tests separate. Stop on any Replay byte/hash/certification drift.

## Product target

```text
exact replay of Slice 0 events remains green
→ operate a bounded multi-security paper portfolio repeatedly
→ admit later prospective observations without custody drift
→ re-certify with append-only lineage
→ prove residual and reopen stability under repeated cycles
```

## Acceptance (slice gate)

- repeated bounded portfolio operation over a declared small universe;
- every cycle reconstructible via Replay 0 machinery from event logs;
- prior certifications remain byte-stable under corrections and reopen;
- no unexplained residual at declared precision;
- no optimizer-first allocation, provider programme, alpha claim, broker, or live capital.

## Carried Medium debt (from Replay A/B/C — not blockers)

| ID | Debt | Notes |
|---|---|---|
| R0-D1 | Multi-hop `reopen_with_stable_prior` parent handling | First-gen / product reopen paths PASS; multi-hop parent-id recompute residual |
| R0-D2 | `book_hash` excludes `partial_fill_residuals` | Residual is field- and ledger-authoritative; document consumers must not treat `book_hash` alone as residual custody |

## Operational gates

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         0/1
```

## Forbidden scope

providers · WRDS · broad historical loaders · optimizer · copula/MES production · adaptive intraday execution · tactical capital · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · rewriting Slice 0 or Replay 0 terminal SHAs · silent squash of audited `0e4b93f`

## Stop rules

1. Stop if work is not descended from a tip that preserves exact Replay code base `0e4b93f`.
2. Stop if exact replay of Slice 0 events regresses.
3. Stop if scope expands to portfolio/universe scale before bounded gate PASS.
