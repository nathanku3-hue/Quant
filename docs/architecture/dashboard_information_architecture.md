# Dashboard Information Architecture

Status: `ACTIVE — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

## Decision

The dashboard is organized around one all-capital PIT operator loop. Pages are read projections, not architectural or authority boundaries.

## Active page map

```text
Command Center                 default
Discovery & Analysis
Decisions & Thesis
Portfolio & Rotation
Strategy Modules
Operations & Replay
```

`dashboard.py` remains the sole future GodView application.

## Page responsibilities

### Command Center

Slice 1 owns a read-only view of:

- exact five-field PIT identity;
- certified capital and cash;
- real MU-operated, MU-shadow, and cash-baseline proposal rows;
- accepted/identity-rejected status;
- target intent/unit/normalization summary;
- disagreement and evidence gaps;
- compact event/projection/system health.

Selection, preview, confirmation, mutation, and certification are not available in Slice 1.

### Discovery & Analysis

Owns opportunity/evidence intake, source identity, reconciliation, and confluence analysis. It creates no proposal or portfolio authority merely by displaying evidence.

### Decisions & Thesis

Owns proposal claims, supporting/contradicting evidence, missing discriminators, falsifiers/boundaries, and decision history. In Slice 1 it is read-only.

### Portfolio & Rotation

Slice 1 owns certified-book and historical transition display only. Later slices add transition candidate, risk/cost preview, explicit authorization, and applied/certified history.

### Strategy Modules

Owns module registry, proposal diagnostics, bounded research replay, backtests, and optimizer research. Outputs are non-authoritative until admitted through the canonical proposal/command/event boundary.

### Operations & Replay

Owns source freshness, adapter receipts, event stream integrity, digest chain, projection/replay, AST authority-state checks, and later preview/certification replay.

## Cross-page law

- No page reads canonical governance authority from raw `st.session_state`.
- Ephemeral UI state remains permitted.
- No page validates proposal identity or emits accepted/rejected facts directly.
- No page calculates strategy signals or portfolio authority.
- Useful content is relocated before broad extraction; deletion follows dependency and behavior proof.
