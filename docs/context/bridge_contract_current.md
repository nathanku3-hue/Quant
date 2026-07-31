# Bridge Contract — Current

- **CANONICAL_AUTHORITY:** `docs/context/gv_endgame_authority_current.md`.
- **ACTIVE_PHASE:** `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` only; `TERMINAL_ACCEPTED; SHIPPED; NO_SUCCESSOR_AUTHORIZED`.
- **BASE:** Challenger terminal `3e4dc957f475945169ddf33ed359254bd98dc64d`.
- **ACTIVE_STATUS:** terminally accepted at executable candidate `0d15e9c59c6b3ca051b3aa815018889d1e94857f`; documentation-only closure preserves all non-doc bytes; terminal tag `gv-operated-portfolio-10-transition-1r-terminal`.
- **PRODUCT_RESULT:** one ten-instrument, two-cluster portfolio with decision-authorized multi-position funding, explicit no-change, real SELL/REDUCE plus BUY/FUND transition, event-derived projections, persistence/reopen, exact replay, complete certification history validation, correction lineage, and changed-why UI.
- **ENTRYPOINT:** `operated_portfolio_app.py`; launcher `launch_operated_portfolio.py`.
- **ACCEPTED_LOWER_LAYERS:** Slice 0 product and Replay 0 integrity only.
- **RECLASSIFIED_SUBSTRATE:** Bounded persisted sessions; Scale multi-session harness; Universe multi-cell harness; Challenger shadow-custody primitive.
- **ORIGINAL_GATES_INCOMPLETE:** Bounded breadth, 25–50 operated portfolio, 100–300+ distinct custody, challenger promotion chain.
- **LOCAL_PINNED_EVIDENCE:** Python 3.12.10; `pip check` PASS; operated/context gate `178/178 PASS`; complete candidate suite `2718` tests, `19` inherited failures, `0` errors, `16` skips, `0` candidate-only failures.
- **HOSTED_EVIDENCE:** exact-head run `30640915560`; `windows-latest` PASS; `ubuntu-latest` PASS; complete operated and FS0 package, generated-context validation, and post-test tracked-byte check PASS.
- **REVIEW_EVIDENCE:** independent Reviewer A/B/C PASS/PASS/PASS against exact `0d15e9c`.
- **ROOT_LOCK_BOUNDARY:** the monorepo dependency surface does not authorize provider, broker, or live behavior; dependency installation in CI is import/test provisioning only.
- **TERMINAL_BLOCKERS:** none for this slice.
- **SCORE:** pre-terminal accepted endgame progress was `52/100`; terminal accepted endgame progress is `62/100`.
- **LIMITED_LIVE:** `CLOSED; NOT_AUTHORIZED`.
- **NEXT:** preserve terminal identities, stop, and await explicit owner selection and `approve next phase` before any new implementation.
- **DO_NOT_START:** Scale, Universe, Challenger compatibility work; providers; optimizer; broker; alpha/score uplift; Limited Live; live capital.
