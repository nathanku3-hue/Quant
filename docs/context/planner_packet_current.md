# Planner Packet — Current

Date: 2026-08-03
Status: `ACTIVE PLANNING AUTHORITY — FINAL ROUND FROZEN`
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Accepted score: `62/100`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

## Current truth

- Hosted-green closure `d84c675` and all accepted 10/25, repair, date-repair, and real-evidence identities remain immutable.
- The same-evidence MU shadow baseline passed 9 focused tests under Python 3.12.10 / pytest 9.1.0 and is banked at `a520f475bfa4fca42a68a22165ab3ad8960c0bc9`.
- Repository inspection confirms `views/command_center.py` is absent and will be new.
- Repository inspection confirms the real operated source is the existing prospective workspace/proposal object path; the shadow source is `core/gv_v2_mu_nvda_shadow_decision.py`.
- Cash baseline must derive from certified workspace/book cash; no standalone cash file is assumed.
- The former human-smoke-first and seven-file shell-first sequences are superseded.
- Limited Live remains closed.

## Active decision

Build the all-capital PIT dashboard pipeline now, layer first, as one functional Slice 1 transaction:

```text
compact contracts
→ verified adapters
→ bounded in-memory governance
→ pure projector/read models
→ six-page registry
→ read-only Command Center
```

The dashboard is the strategy consumer/comparator/operator surface. It does not make identity decisions, accept events, calculate strategy logic, or mutate capital.

## Frozen visible pages

```text
Command Center
Discovery & Analysis
Decisions & Thesis
Portfolio & Rotation
Strategy Modules
Operations & Replay
```

## Immediate sequence

1. Regenerate context and commit the planning authority separately as docs-only.
2. Verify a fully clean worktree.
3. Freeze exact operated, shadow, certified cash, certified event-prefix head, evidence, no-market proof, and as-of mappings.
4. Execute the exact ten-file Slice 1 transaction.
5. Stop at the read-only Command Center.

## P0/P1 risks

- P0: treating `events[-1]` as the certified book head instead of the final authoritative event in the certified prefix.
- P0: assigning the cash-only no-market identity without proving empty positions/orders/fills, zero residual/targets, and zero market-data consumption.
- P0: inventing a conventional market snapshot, cash yield, or source artifact to satisfy the contract.
- P0: allowing adapter/dashboard/projector code to decide accepted versus rejected authority.
- P0: creating any durable governance persistence in Slice 1 instead of the approved bounded digest-chained in-memory stream.
- P1: mixing proposal, decision snapshot, and lifecycle state in the MU-operated adapter.
- P1: disconnected contract/event framework work that does not reach the real Command Center.

## Boundary

No selection, target composition, CTA/macro formulas, provider acquisition, optimizer/risk authority, preview, authorization, book mutation, certification change, deletion, broker behavior, live capital, backward compatibility, or score uplift in Slice 1.
