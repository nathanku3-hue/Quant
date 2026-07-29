# Planner Packet — Current

## Active — R0 custody repair banked; independent audit pending (2026-07-29)

### Current truth

- Released substrate remains `gv-alpha0-paper-decision-v0.1.0` at `a88ed05`; release-proof tip `93e7a55`.
- Shipped product score remains **39/100**; observed comparisons remain **0**; no alpha or live-capital claim.
- The prior roadmap was a validated but unbanked candidate. R0 repairs its custody and semantic contradictions.
- Standalone `GV-CANON-RESET-0` is removed from the product sequence.
- The first product slice is `GV-MICRO-PORTFOLIO-VERTICAL-0`; exact replay follows immediately.
- `docs/context/ACTIVE_BRIEF` is the explicit active authority selector. Highest-numeric-phase discovery is migration-only.

### Binding sequence

```text
R0 ROADMAP-CUSTODY-REPAIR
→ bank ROADMAP_FREEZE_COMMIT
→ independent audit
→ GV-MICRO-PORTFOLIO-VERTICAL-0
→ GV-DETERMINISTIC-REPLAY-0
→ evidence-gated later slices
```

### Execution model

Use three mergeable work packages, not seven automatic branches:

- Package A — Truth core: identity, evidence, events, book, reconciliation, replay skeleton.
- Package B — Decision vertical: thesis, scenarios, admission, capital competition, aim, transition, order/fill.
- Package C — Product closure: operator flow, read models, acceptance fixture, later-observation explanation, docs/ops.

Freeze minimum cross-layer IDs/events before parallel work. Freeze field-level detail only when the operator fixture exercises it.

### Immediate gate

Wait for independent audit of the banked R0 repair. After audit PASS, create one clean isolated implementation worktree from `ROADMAP_FREEZE_COMMIT` and ship the complete micro-portfolio loop. Do not start from raw `93e7a55`.

### Binary gate score

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      0/1
Prospective later observation      0/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

### Root checkout warning

The source checkout at `E:\Code\Quant` remains massively dirty and is not execution or publication authority. Do not clean, revert, or use it for this programme without separate authorization.

### Do not reopen

Alpha release machinery; released `gv_fs0_v1`; providers or WRDS; PEAD; legacy Phase 62–80+ queues; optimizer, copula, graph, adaptive-execution, or tactical-capital programmes; score uplift; broker; live capital.

### First action after audit PASS

```text
verify exact ROADMAP_FREEZE_COMMIT
→ create clean isolated implementation worktree
→ ship GV-MICRO-PORTFOLIO-VERTICAL-0 through Packages A/B/C
→ certify GV-DETERMINISTIC-REPLAY-0 from real vertical events
```

Active brief: `docs/phase_brief/phase0-gv-micro-portfolio-vertical-0-brief.md`.
