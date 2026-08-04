# Bridge Contract — Current

Date: 2026-08-05
Active slice: `GV-OPERATED-ROTATION-1`
Status: `VALIDATED — READY TO PUBLISH`
Accepted score: `62/100`
Post-PASS assessment: `69–71/100` (non-canonical)

## FROM

A certified, persisted, fresh-process-replayable episode-one paper book with MU `7 @ 101.25`, plus the default Command Center’s displayed eligible `GV_REAL_MU_OPERATED` proposal.

## TO

One repeatable proposal-to-capital operation:

```text
displayed eligible proposal
→ exact PIT + active book/certification/event binding
→ two identified market packets
→ mutation-free SELL+BUY preview
→ explicit confirm or reject-all
→ atomic persistence
→ certification lineage
→ exact fresh-process reopen
```

## Frozen product behavior

- The funded source is the single certified MU position.
- The governed companion is MERID derived from the accepted operated-10 substrate.
- Rotation requires exactly two ADMIT targets: reduce MU and fund MERID.
- The source market mark remains certified `101.25`, avoiding invented mark-to-market P&L.
- SELL executes before BUY; both use complete fills and the existing deterministic fee path.
- Reject-all records a certified rejection without adding MERID or changing economics.
- Stale proposal/book/certification/event bindings, mismatched prices, tampering, and buy-only top-ups fail closed.

## Validation truth

The sealed native validation passed all 31 declared tests, including the default Command Center AppTest and separate-process exact reopen. The retained task outcome is `DONE`.

## Authority boundary

The Command Center composes the request and displays the result. Proposal validation, transition construction, accounting, persistence, certification, and replay remain in existing domain authorities. No strategy calculation or optimizer logic moves into the dashboard.

## Next step

Commit and push the exact pre-authorized slice once to `origin/codex/gv-operated-rotation-1`. Alpha, provider-quality, sizing-quality, and realized-value claims remain closed.
