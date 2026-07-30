# GV-PORTFOLIO-SCALE-1 Brief

Date: 2026-07-30
Mode: `EXECUTION_PACKET`
Status: `OPEN; IMPLEMENTATION_AUTHORIZED`
Authority: Bounded Portfolio 1 accepted at exact terminal `abaa814`; docs-only promotion open

## Immutable pins (do not rewrite)

| Role | Exact SHA | Tag |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | `gv-replay-0-base` |
| Replay 0 code terminal | `0e4b93fb370f67956502edc02e9c6f56ceb2eba3` | `gv-replay-0-terminal` |
| **Bounded Portfolio 1 terminal** | **`abaa814ce99ea78afadc33dd40506f4e13a742ef`** | **`gv-bounded-portfolio-1-terminal`** |

Ancestry: … → `0e4b93f` (Replay) → `5fc2e4c` (open Bounded) → `4f3bc6b` → **`abaa814`** (ACCEPT_BOUNDED) → this docs-only promotion tip.

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 active phase: **`GV-PORTFOLIO-SCALE-1` only**.
- L2 closed / immutable: Slice 0 @ `85e6601`; Replay 0 @ `0e4b93f`; Bounded Portfolio 1 @ `abaa814`.
- L2 deferred: Universe Scale, Challenger Promotion, Limited Live Capital.

## Recommended next action

Create a clean isolated implementation worktree from **this promotion tip** (docs open) while treating **`abaa814` as the immutable Bounded Portfolio code pin** (and Replay pin `0e4b93f`). Implement only portfolio-scale custody/replay stability. Do not reopen Bounded or Replay feature work except explicit carried Medium debt.

## Product target

```text
bounded multi-cycle paper operation remains green
→ scale repeated operation across a larger declared portfolio set
→ keep exact replay and residual zero every cycle
→ preserve append-only certification lineage under scale
→ prove restart/reopen and session custody at scale
```

## Acceptance (slice gate)

- repeated portfolio operation at declared scale above Bounded V1 universe size;
- every cycle reconstructible via Replay 0 machinery;
- prior certifications byte-stable under corrections and reopen;
- no unexplained residual at declared precision;
- no optimizer-first allocation, provider programme, alpha claim, broker, or live capital.

## Carried Medium debt (from prior slices — not blockers)

| ID | Debt | Notes |
|---|---|---|
| R0-D1 | Multi-hop `reopen_with_stable_prior` parent handling | Replay residual |
| R0-D2 | `book_hash` excludes `partial_fill_residuals` | Field/ledger authoritative |
| B1-D1 | Product `validate_workspace` single-observation rule | Bounded multi-observe uses bounded authority; scale must not silently bypass custody |

## Operational gates

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         1/1
Portfolio scale                    0/1
```

## Forbidden scope

providers · WRDS · broad historical loaders · optimizer · copula/MES · adaptive intraday · tactical capital · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · rewriting Slice 0 / Replay 0 / Bounded terminals · squash of audited `abaa814`

## Stop rules

1. Stop if work is not descended from a tip that preserves exact Bounded terminal `abaa814` and Replay pin `0e4b93f`.
2. Stop if bounded multi-cycle or Replay reconstruction regresses.
3. Stop if scope expands to universe scale or live capital before portfolio-scale PASS.
