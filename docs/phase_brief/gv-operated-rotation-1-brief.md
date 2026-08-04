# GV-OPERATED-ROTATION-1 Brief

Date: 2026-08-05
Branch: `codex/gv-operated-rotation-1`
Base: `b98dab62e175716755b33eda0205b93bf98b0007`
Status: `VALIDATED — PUBLICATION AUTHORIZED`
Accepted product score: `62/100` (canonical, unchanged)
Post-PASS assessment: `69–71/100` (non-canonical)

## Product result

GodView now repeats an already-operated paper-capital journey through the default Command Center:

```text
certified episode-one MU book
→ displayed eligible GV_REAL_MU_OPERATED proposal
→ proposal/PIT/book/price-bound mutation-free preview
→ explicit confirm or reject-all
→ atomic persistence and replay certification
→ fresh-process reopen of the exact changed book
```

## Delivered functional slice

- Preserves episode one: MU `7 @ 101.25`, classified cash, cost `2`, residual `0`.
- Derives governed companion `MERID` from the accepted operated-10 substrate.
- Requires exactly one funded source, a genuine source reduction, and non-zero companion funding.
- Binds the displayed proposal, full PIT identity, active book hash, certification ID, event count, and two market packets.
- Executes complete-fill SELL before BUY through the existing deterministic fee and accounting path.
- Reuses existing preview, confirmation, rejection, persistence, certification, and replay authorities.
- Exposes the bounded rotation from the funded Command Center state.

## Acceptance evidence

The exact sealed validation passed all 31 declared tests:

```text
C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe -m pytest \
  tests/test_gv_pit_operated_rotation.py \
  tests/test_gv_pit_operated_capital.py \
  tests/gv_portfolio_v0/test_prospective.py \
  tests/gv_portfolio_v0/test_prospective_app.py -q

............................... [100%]
```

Validated behavior includes mutation-free preview, displayed-proposal and PIT binding, SELL `3 MU` plus BUY `5 MERID`, reject-all preservation, stale/tampered and buy-only rejection, atomic confirmation, certification lineage, Command Center AppTest operation, and separate-process exact reopen of MU `4` plus MERID `5` with residual `0`.

## Claim boundary

This proves repeat operation, proposal-to-capital integration, SELL+BUY accounting, operator-surface usability, persistence, certification, and replay. It does not prove provider data quality, strategy-generated targets, advantageous sizing, alpha, realized economic value, investment advice, broker authority, or live-capital authority.

## Publication

The sealed native task retained outcome is `DONE`; exact pre-authorized paths may be committed and pushed once to `origin/codex/gv-operated-rotation-1`.
