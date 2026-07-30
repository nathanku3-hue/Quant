# Bridge Contract — Current

- **ACTIVE_PHASE:** `GV-MICRO-PORTFOLIO-VERTICAL-0` only.
- **BASE_CANDIDATE:** `9ebc973a8cc3cfbd4899ed724733cc22c606fbbf`, previously local/remote-equal.
- **REPAIR_SCOPE:** Integrator/Accounting/Strategy invariants, stale test authority, and checkout custody only.
- **READ_ONLY:** Product runtime and Replay implementation.
- **ENVIRONMENT:** unchanged `requirements.lock` installs on Python 3.12.10; `pip check` PASS.
- **AFFECTED_GATES:** portfolio 92/92 PASS; context + protocol 175/175 PASS; legacy product 263/263 PASS.
- **FULL_GATE:** 2664 collected; 2598 passed, 16 skipped, 50 failed in an LF-preserving clean clone.
- **BLOCKERS:** non-relocatable historical Replay manifest; absent generated datasets/evidence; stale historical authority tests; feature-store historical fixture drift; stale candidate-card hashes; Rule100 historical failure; independent A/B/C pending.
- **SCORE:** shipped product score remains **39/100**; observed remains **0**; no alpha or live-capital claim.
- **NEXT:** publish exact terminal SHA, run independent A/B/C, and repair repository-wide environment/custody in a separate bounded phase.
- **DO_NOT_START:** Product features, Replay implementation, providers, optimizer/copula/graph/adaptive execution, broker, score uplift, or live capital.
