# Terminal Zero / GodView Certified Portfolio OS

Status: `GV-DASHBOARD-ALL-CAPITAL-PIT-1 FINAL PLANNING FROZEN; IMPLEMENTATION NOT STARTED; LIVE CLOSED`
Date: 2026-08-03
Accepted product score: `62/100`
Active brief: `docs/context/ACTIVE_BRIEF`
Canonical architecture: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`
Canonical roadmap: `docs/architecture/top_level_roadmap.md`

GodView is a local-first, point-in-time certified portfolio operating system. Its product unit is one portfolio-wide capital decision across every eligible strategy proposal, not one stock case and not one dashboard page.

```text
certified five-field PIT identity
→ verified real proposal adapters
→ immutable proposals
→ typed governance commands
→ ordered append-only events
→ deterministic read projections
→ dashboard comparison
→ later intent-aware selection
→ later calculation-only preview and explicit authority
→ applied/certified events
→ exact replay
```

## Current truth

- Accepted operated portfolio and replay foundations remain immutable.
- Hosted-green real-MU closure `d84c675` remains preserved.
- Accepted score remains `62/100`; no documentation/refactor uplift is claimed.
- The current worktree contains an unbanked five-path MU operated-versus-shadow baseline.
- MU is the first real proposal case, not the pipeline model.
- The final planning round added explicit command-handler, event-ordering, digest-chain, and pure-projector authority.
- Limited Live, broker behavior, client assets, advice activity, and live capital remain closed.

## Active product decision

`dashboard.py` becomes the sole GodView application and operator surface. It exposes six read-projection pages:

```text
Command Center
Discovery & Analysis
Decisions & Thesis
Portfolio & Rotation
Strategy Modules
Operations & Replay
```

Command Center is default. Strategy modules own immutable proposals. Governance command handling owns identity acceptance/rejection. Ordered events own historical facts. Projectors own read models. Portfolio authority later owns target resolution, preview, confirmation, application, certification, and replay. The dashboard owns no strategy formulas or capital mutation.

## Layer-first immediate sequence

```text
bank current five-file shadow baseline
→ update status/context and bank final planning authority separately as docs-only
→ verify a fully clean worktree
→ immutable PIT/proposal contracts
→ verified MU operated/shadow and book-cash adapters
→ identity command handler
→ ordered event envelope/store contract
→ deterministic projector/read models
→ six-page shell and read-only Command Center
→ stop
```

Slice 1 has zero selection, optimizer, risk math, preview, authorization, book mutation, certification change, or deletion.

## Local commands

```text
python -m pytest tests/gv_portfolio_v0/test_same_evidence_shadow.py tests/gv_portfolio_v0/test_real_evidence_mu.py -q
python scripts/build_context_packet.py
python scripts/build_context_packet.py --validate
```

Use the repository's approved Python 3.12 environment. Do not use the dirty root checkout as execution or publication authority.
