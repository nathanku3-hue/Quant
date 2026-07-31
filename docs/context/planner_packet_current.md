# Planner Packet — Current

Date: 2026-07-31
Canonical authority: `docs/context/gv_endgame_authority_current.md`

## Current truth

- One product phase is active: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R`.
- Base authority is immutable Challenger terminal `3e4dc957f475945169ddf33ed359254bd98dc64d`.
- Slice 0 is an accepted product slice; Replay 0 is an accepted integrity slice.
- Bounded, Portfolio Scale, Universe Scale, and Challenger terminals remain immutable but are reclassified as substrates or validation harnesses with their original roadmap gates incomplete.
- Limited Live is closed and unauthorized.
- Accepted endgame progress remains `52/100`.

## Product delta in the current candidate

The operator path is:

```text
review 10 distinct instruments across 2 clusters
→ confirm one portfolio and fund 4 selected positions
→ retain classified residual cash
→ persist and reopen
→ admit one explicit no-change observation
→ persist and reopen
→ SELL/REDUCE Harbor by 4 shares
→ BUY/FUND Meridian by 5 shares
→ reconcile positions, cash, costs, NAV, and zero residual
→ persist, reopen, explain changed why
→ append one non-economic correction
→ fresh-process reopen of corrected state
```

The repaired acceptance kernel now makes canonical decisions and events authoritative:

- deterministic selected funded IDs control initial execution;
- initial evidence is instrument-owned and cross-instrument rebinding fails closed;
- orders, fills, authority chains, observations, changed-why, cash, and costs are exact event-derived projections;
- transition legs equal exact target deltas;
- complete certification history objects are replayed at their original prefixes;
- correction lineage contains derived links rather than self-asserted stability flags;
- persistence rejects symlink and Windows-junction ancestors.

## Verification state

Windows Python 3.12.10 diagnostic evidence:

- operated domain + black-box AppTest: `15/15 PASS`;
- book/execution/replay/operated focused set: `70/70 PASS`;
- context/authority set: `33/33 PASS`;
- complete `tests/gv_portfolio_v0`: `145/145 PASS`;
- black-box flow completes correction and fresh-process corrected reopen with network denied.

A clean narrow Windows environment now passes using `requirements-alpha.txt`: Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0, and `pip check` green. The 119-package monorepo `requirements.lock` is outside this product slice and is not an acceptance gate.

The real shipping gap was CI custody: existing workflows did not trigger on operated-product files and did not run the 178-test operated/context gate. `.github/workflows/gv-operated-portfolio.yml` now defines narrow Windows/Linux Python 3.12 parity using `requirements-alpha.txt`, but hosted execution remains pending until one candidate SHA is pushed.

## Current score

| Dimension | Current |
|---|---:|
| Authority alignment | 92/100 |
| Happy-path product behavior | 85/100 |
| Semantic authority enforcement | 88/100 |
| Persistence/custody | 86/100 |
| Black-box operator proof | 88/100 |
| Terminal readiness | 50/100 |
| Accepted endgame progress | 52/100 unchanged |

After exact-SHA hosted Windows/Linux parity, immutable fresh-checkout proof, full failset comparison, and Reviewer A/B/C, this slice should raise accepted endgame progress to approximately `61–63/100`.

## Next valid action

Push the locally frozen current-HEAD candidate, then run hosted Windows/Linux parity, fresh-checkout correction/reopen AppTest, full repository/failset comparison, and Reviewer A/B/C concurrently against that immutable SHA.

## Stop conditions

Do not claim terminal acceptance, uplift the accepted score, fast-forward main, tag, or open Scale, Universe, Challenger, providers, or Live before exact-SHA hosted parity and independent terminal review. Stop on workflow non-trigger, Windows/Linux divergence, any projection mismatch, linked-ancestor escape, replay drift, nonzero residual, candidate mutation, or weakened frozen acceptance.
