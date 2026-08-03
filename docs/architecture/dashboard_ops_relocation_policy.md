# Dashboard Operations and Replay Policy

Status: `ACTIVE — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`

## Operations & Replay owns in Slice 1

- exact source/evidence/market/book identity status;
- verified adapter mapping receipts and unavailable-field reasons;
- proposal-submission command lineage;
- governance stream ID, sequence, schema, correlation, causation, and digest chain;
- duplicate/gap/idempotence validation;
- accepted and identity-rejected proposal events;
- deterministic projector and canonical-order replay;
- AST scan for raw session-state governance authority;
- proof of zero production mock rows;
- proof of zero selection, optimization, risk math, preview, mutation, certification change, or deletion.

## Command Center may show only compact summaries

```text
five-field PIT identity health
adapter/source health
eligible and identity-rejected counts
current capital and classified cash
stream head sequence/digest
projection/replay status
open evidence gaps
```

Full event traces, digest receipts, adapter mappings, drift history, reconstruction traces, and dependency scans belong in Operations & Replay.

## Authority boundary

Operations & Replay diagnoses and reconstructs. It does not select proposals, calculate targets, authorize capital, or mutate the certified book.

Ephemeral UI state may use Streamlit session state. Portfolio, proposal, episode, preview, authorization, and certification authority may not.

## Later slices

After authority exists, this page adds target-conflict receipts, preview expiry/staleness, multi-model risk disagreement, authorization/application/certification lineage, and deletion proof.
