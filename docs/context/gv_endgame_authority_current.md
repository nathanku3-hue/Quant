# GodView Endgame Authority — Current

Date: 2026-08-03
Status: `ACTIVE — FINAL PLANNING ROUND FROZEN`
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

GodView's product center is one all-capital PIT portfolio decision loop operated through `dashboard.py`.

## Layered authority chain

```text
Accepted custody/book/evidence
→ verified source adapters
→ immutable CapitalProposal
→ SubmitProposalCommand
→ governance handler: exact five-field identity decision
→ ordered append-only governance events
→ pure ProposalRecordReadModel / DecisionEpisodeReadModel projection
→ dashboard read surface
→ later selection/composition
→ later PortfolioAuthority preview/authorization/application/certification/replay
```

## Immediate action

```text
run focused same-evidence and real-MU tests
→ commit exactly five code/test baseline paths with no tag
→ update status/context and bank final planning authority separately as docs-only
→ verify a fully clean worktree
→ inspect exact operated/book/event fields
→ execute Slice 1 contracts → adapters → handler → events → projector → read-only Command Center
```

## Slice 1 terminal boundary

```text
zero selection
zero optimizer or risk math
zero preview or authorization
zero book mutation
zero certification change
zero deletion
```

## Closed authority

CTA/macro formulas, provider expansion, optimizer-led allocation, broker behavior, live capital, client assets, and advice activity remain unauthorized. Accepted score remains `62/100`.
