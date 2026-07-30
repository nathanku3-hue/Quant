# GV-PORTFOLIO-SCALE-1 Brief

Date: 2026-07-30
Mode: `EXECUTION_PACKET`
Status: `ACCEPTED_IMMUTABLE at c37abf0; tag gv-portfolio-scale-1-terminal`
Authority: Portfolio Scale 1 accepted; next active slice is Universe Scale only

## Immutable pins (do not rewrite)

| Role | Exact SHA | Tag |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | `gv-replay-0-base` |
| Replay 0 code terminal | `0e4b93fb370f67956502edc02e9c6f56ceb2eba3` | `gv-replay-0-terminal` |
| Bounded Portfolio 1 terminal | `abaa814ce99ea78afadc33dd40506f4e13a742ef` | `gv-bounded-portfolio-1-terminal` |
| **Portfolio Scale 1 terminal** | **`c37abf00293937b9b99eb6e560f6b5b77a92ea1f`** | **`gv-portfolio-scale-1-terminal`** |

Ancestry: … → `abaa814` (Bounded) → `eedf853` (docs open Scale) → **`c37abf0`** (ACCEPT_PORTFOLIO_SCALE_1) → docs-only open of Universe Scale.

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 phase: **`GV-PORTFOLIO-SCALE-1` accepted immutable** at `c37abf0`.
- L2 active phase: **`GV-UNIVERSE-SCALE-1` only** (see `docs/context/ACTIVE_BRIEF`).
- L2 closed / immutable: Slice 0 @ `85e6601`; Replay 0 @ `0e4b93f`; Bounded Portfolio 1 @ `abaa814`; Portfolio Scale 1 @ `c37abf0`.
- L2 deferred: Challenger Promotion, Limited Live Capital.

## Acceptance proof

- Concurrent multi-session scale: default 3 portfolios × 4 securities = 12 slots (> Bounded V1 universe of 4).
- Path-free cross-portfolio economic determinism (workspace content hash, NAV, residual, event counts, cycle/cert ids).
- Absolute session path may differ `bounded_report_hash` (identity, not product drift).
- Frozen Bounded/Replay/book/vertical modules byte-identical to `abaa814`.
- Replay freeze + Bounded multi-cycle + Scale suites green.
- Full-suite failsets tip vs `eedf853` identical; true candidate-only = 0.
- Independent Reviewer A/B/C: PASS / PASS / PASS (0 High).
- PR #13 merged retaining exact SHA (FF push `eedf853 → c37abf0`, no squash/rebase/merge commit).

## Product delivered

```text
bounded multi-cycle paper operation remains green
→ scale repeated operation across independent portfolio sessions
→ exact replay and residual zero every cycle
→ append-only certification lineage under scale
→ restart/reopen and session custody at scale
```

## Module

- `gv_portfolio_v0/scale.py`
- `tests/gv_portfolio_v0/test_scale.py`
- `docs/architecture/gv_portfolio_scale_1_branch_pins.md`

## Carried Medium debt (from prior slices — not blockers)

| ID | Debt | Notes |
|---|---|---|
| R0-D1 | Multi-hop `reopen_with_stable_prior` parent handling | Replay residual |
| R0-D2 | `book_hash` excludes `partial_fill_residuals` | Field/ledger authoritative |
| B1-D1 | Product `validate_workspace` single-observation rule | Bounded multi-observe uses bounded authority |

## Operational gates

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         1/1
Portfolio scale                    1/1
```

## Forbidden after acceptance

Rewrite of terminal `c37abf0`; squash of audited terminals; reopening Challenger/Live before Universe Scale PASS; providers · optimizer · live capital · alpha claim.

## Next

See `docs/phase_brief/phase4-gv-universe-scale-1-brief.md` — only Universe Scale is implementation-authorized.
