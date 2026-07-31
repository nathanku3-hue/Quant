# Bridge Contract — Current

- **CANONICAL_AUTHORITY:** `docs/context/gv_endgame_authority_current.md`.
- **ACTIVE_PHASE:** `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` only.
- **BASE:** Challenger terminal `3e4dc957f475945169ddf33ed359254bd98dc64d`.
- **ACTIVE_STATUS:** acceptance-kernel repair locally green and banked at current branch HEAD; candidate frozen locally; not terminal; not shipped.
- **PRODUCT_RESULT:** one ten-instrument, two-cluster portfolio with decision-authorized multi-position funding, explicit no-change, real SELL/REDUCE plus BUY/FUND transition, event-derived projections, persistence/reopen, exact replay, complete certification history validation, correction lineage, and changed-why UI.
- **ENTRYPOINT:** `operated_portfolio_app.py`; launcher `launch_operated_portfolio.py`.
- **ACCEPTED_LOWER_LAYERS:** Slice 0 product and Replay 0 integrity only.
- **RECLASSIFIED_SUBSTRATE:** Bounded persisted sessions; Scale multi-session harness; Universe multi-cell harness; Challenger shadow-custody primitive.
- **ORIGINAL_GATES_INCOMPLETE:** Bounded breadth, 25–50 operated portfolio, 100–300+ distinct custody, challenger promotion chain.
- **LOCAL_PINNED_EVIDENCE:** narrow `requirements-alpha.txt` environment on Windows Python 3.12.10 with pytest 9.0.2 and Streamlit 1.54.0; `pip check` PASS; complete operated/context gate `178/178 PASS`, including correction and fresh-process corrected reopen AppTest with network denied.
- **CI_REPAIR:** `.github/workflows/gv-operated-portfolio.yml` now triggers on operated-product and authority files and runs the narrow Python 3.12 gate on `ubuntu-latest` and `windows-latest` using `requirements-alpha.txt`.
- **ROOT_LOCK_BOUNDARY:** the 119-package monorepo `requirements.lock` is unrelated to this product acceptance and is not a blocker for the operated slice.
- **TERMINAL_BLOCKERS:** no pushed immutable candidate SHA; no hosted Windows/Linux parity result; no fresh-checkout exact-SHA proof; no full repository/failset comparison; no independent A/B/C.
- **SCORE:** accepted endgame progress remains `52/100`; expected after terminal PASS `61–63/100`.
- **LIMITED_LIVE:** `CLOSED; NOT_AUTHORIZED`.
- **NEXT:** push the frozen current-HEAD candidate, then run hosted parity, fresh-checkout proof, full failset comparison, and A/B/C concurrently; fast-forward and tag only on exact-SHA PASS.
- **DO_NOT_START:** Scale, Universe, Challenger compatibility work; providers; optimizer; broker; alpha/score uplift; Limited Live; live capital.
