# GodView Dashboard Wireframe — All-Capital PIT Loop

Status: `ACTIVE PRODUCT WIREFRAME — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`

## Command Center — Slice 1

```text
┌ Certified PIT identity ──────────────────────────────────────────────────────┐
│ book_id | book_head | evidence_set | market_snapshot | certified_as_of     │
│ identity_status: exact | stream_id | head_sequence | head_digest           │
└─────────────────────────────────────────────────────────────────────────────┘

┌ Current certified capital ─────────────┐ ┌ Product state ───────────────────┐
│ positions | sleeves | classified cash │ │ READ_ONLY_PIT_COMPARISON         │
│ NAV/residual from certified book       │ │ selection/preview unavailable    │
└────────────────────────────────────────┘ └───────────────────────────────────┘

┌ Proposal comparison ─────────────────────────────────────────────────────────┐
│ seq | module       | outcome | intent       | unit     | governance status   │
│ 001 | MU-OPERATED  | ...     | TARGET_FINAL | ...      | ELIGIBLE            │
│ 002 | MU-SHADOW    | ...     | TARGET_FINAL | ...      | ELIGIBLE/ID_REJECT  │
│ 003 | CASH-BASE    | ...     | TARGET_FINAL | ...      | ELIGIBLE            │
│ claim | evidence support/contradiction | missing discriminator | not-act    │
└──────────────────────────────────────────────────────────────────────────────┘

┌ Comparison summary ────────────────────┐ ┌ Integrity summary ───────────────┐
│ disagreement | evidence gaps          │ │ adapters | event chain | replay   │
│ target-intent conflict: informational │ │ AST authority-state | mock rows   │
└────────────────────────────────────────┘ └───────────────────────────────────┘
```

Slice 1 contains no Select, Stage, Preview, Confirm, Apply, or Certify controls. The future location may be visibly reserved but must be disabled and labeled unavailable rather than simulated.

## Command Center interaction law

- Opening proposal/evidence detail is allowed.
- Sorting/filtering/expansion may use ephemeral session state.
- Raw certified book/proposal/episode state cannot be read from session state.
- Identity acceptance/rejection is already represented by events before rendering.
- No production dummy proposal row is allowed.

## Discovery & Analysis

```text
source/evidence intake
→ exact source identity and freshness
→ reconciliation and contradiction view
→ open existing evidence/proposal detail
```

It remains functional during Slice 1 and creates no capital authority.

## Decisions & Thesis

```text
proposal claim
supporting/contradicting EvidenceReference rows
missing discriminator
reason not to act
extension schema/payload identities
proposal governance history
```

Read-only in Slice 1.

## Portfolio & Rotation

Slice 1:

```text
current certified book
historical transitions/certifications
no candidate or preview
```

Later:

```text
intent-aware candidate
→ costs/limits/multi-model risk
→ immutable preview
→ explicit stale-bound authorization
→ application/certification history
```

## Strategy Modules

```text
module registry
non-authoritative diagnostics
research replay/backtests/optimizer research
proposal output history
```

No module can mutate book state through this page.

## Operations & Replay

```text
adapter mappings and unavailable fields
event stream order/digest chain
accepted/rejected event lineage
projection replay equality
canonical row ordering
session-state authority scan
production-mock absence
negative-authority proof
```

## Later-slice visual boundary

Slice 2 adds selection/composition. Slice 3 adds preview/authorization/application/certification. The Slice 1 wireframe must not imply those authorities already exist.
