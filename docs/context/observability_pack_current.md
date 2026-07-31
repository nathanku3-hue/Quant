# Observability Pack — Current

Date: 2026-07-30
Active slice: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R`

## Product sentinels

- **Authority:** `docs/context/gv_endgame_authority_current.md` exists and `docs/context/ACTIVE_BRIEF` selects the operated-portfolio brief.
- **Identity:** exactly ten unique permanent instrument IDs and permanent keys.
- **Economic diversity:** at least two cluster values and ten unique initial evidence hashes and thesis claims.
- **Portfolio count:** exactly one portfolio book; no session/cell/run/slot breadth metric.
- **Funding:** at least three positive positions and both `AVAILABLE` and `RESEARCH_RESERVE` cash buckets.
- **Competition:** every decision snapshot contains exactly one candidate row for each of the ten instruments.
- **No-change:** no-change observation leaves order count, holdings, cash, NAV, and book hash unchanged.
- **Transition:** terminal economic cycle contains `SELL HARBOR 4` then `BUY MERID 5`.
- **Accounting:** no negative position or cash; total explicit costs `12`; terminal NAV `4988`; unexplained residual `0`.
- **Replay:** reconstructed and idempotent book hashes equal the persisted book hash.
- **Correction:** one append-only non-economic correction links to the prior certification and preserves book hash/NAV.
- **Persistence:** content-addressed atomic envelope reloads byte-equivalent workspace state after every stage.
- **Product UI:** fresh-checkout AppTest must traverse confirm → no-change → transition → reopen with network denied.

## Authority sentinels

- Slice 0 and Replay 0 are accepted.
- Bounded, Scale, Universe, and Challenger are substrates with original gates incomplete.
- The frozen roadmap's 8–15, 25–50, 100–300+, and challenger-promotion requirements remain verbatim.
- Limited Live remains closed and unauthorized.
- Accepted endgame score remains `52/100` until terminal evidence is complete.

## Current signal

- **GREEN:** Python compile; complete manual domain path; legacy Slice 0 manual flow; oversell rejection; correction lineage; atomic save/load equality.
- **AMBER:** one locally frozen candidate commit exists, but hosted exact-SHA parity and independent terminal review are pending.
- **RED:** pinned `.venv` absent; pytest/AppTest not run; full terminal regression not run; independent A/B/C not run; no immutable candidate, push, main fast-forward, or terminal tag.
