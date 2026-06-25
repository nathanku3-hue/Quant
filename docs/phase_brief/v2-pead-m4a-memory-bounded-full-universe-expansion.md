# V2 PEAD M4A Memory-Bounded Full-Universe Expansion Brief

Mode: EXECUTION_PACKET
Status: Local implementation, focused validation, execution_microstructure rerun, and full-suite clean exit PASS; strict independent Reviewer A/B/C remains a separate governance caveat
Date: 2026-06-22
RoundID: ROUND-20260622-V2-PEAD-M4A-MEMORY-BOUNDED-FULL-UNIVERSE
ScopeID: V2_PEAD_M4A_MEMORY_BOUNDED_D2A_D2B_EXPANSION
Owner: Data + Docs/Ops

## Objective

Implement the approved M4A slice: make D2A security-level return expansion and D2B fixed event-security window expansion executable in bounded memory for full-universe local artifacts, without provider access, PIT EPS claims, estimator/UI changes, alpha verdicts, ranking/scoring, alerts, recommendations, or broker/order actions.

## Contract

- D2A sample behavior remains available; --sample still builds the 500-GVKEY sample through the existing pandas path.
- D2A --build now uses bounded DuckDB operators, one thread, a 512 MB memory limit, disk spill, and Parquet row groups instead of materializing the full source/output as pandas frames.
- D2A formula semantics are unchanged: TR_level_t = prccd_t * trfd_t / ajexdi_t, total_return_t = TR_level_t / TR_level_{t-1} - 1, and fallback price return lags remain within (gvkey, iid).
- D2B sample behavior remains available; --build now resolves D1/D2A manifests by metadata/hash, lazily validates full D2A with DuckDB, and writes the full event-window artifact through bounded SQL and row-grouped Parquet.
- D2B event-security semantics are unchanged: prior 20 authoritative sessions, at least 15 finite dollar_volume observations, deterministic score/count/IID/security ordering, one fixed security per event, and exact +1..+60 sessions.
- Publication remains immutable hash-named Parquet first, then atomic manifest pointer replacement under a writer lock; failed pre-commit publication cleans temporary files and preserves the prior manifest pointer.

## Acceptance criteria

- [x] D2A full build has a bounded out-of-core path and focused tests prove semantic equivalence on fixture data without calling the pandas source/output materialization path.
- [x] D2B full build has a bounded out-of-core path and focused tests prove semantic equivalence on fixture data without capturing full Parquet bytes, loading full D2A into pandas, or returning a full output DataFrame.
- [x] D2A and D2B full-build duplicate/invalid input gates fail closed before publication.
- [x] D2A and D2B full-build interruption tests preserve the old manifest pointer and clean temporary files.
- [x] Focused M4A tests pass: .venv\Scripts\python -m pytest tests\test_pead_d2_returns.py tests\test_pead_d2b_event_window_contract.py -q.
- [x] Broader PEAD D2/D3/event-study regression passes: .venv\Scripts\python -m pytest tests\test_pead_d2_returns.py tests\test_pead_d2b_event_window_contract.py tests\test_pead_d3_benchmark_artifact.py tests\test_pead_event_study.py -q.
- [x] Full repository pytest returns a clean exit code after stale pytest/Streamlit smoke processes are stopped.
- [ ] Terminal independent Reviewer A/B/C SAW passes. Blocked by subagent usage limit before reviewer capacity could be reserved; this is a governance caveat, not a remaining execution_microstructure/full-suite clean-exit blocker.

## Ship-Fast Decision Gate

Reference: docs/templates/ship_fast_decision_gate.md.

- One decision answered: approve M4A implementation only; do not reopen M3 WRDS/PIT or downstream alpha/product/action scope.
- Current delta: D2A/D2B full-universe local builders now have bounded-memory execution paths and focused regression coverage.
- Evidence needed: none for the execution_microstructure/full-suite clean-exit blocker; optional strict governance evidence is terminal Reviewer A/B/C after subagent capacity returns.
- Forbidden scope: providers, PIT claims, estimator/UI changes, alpha verdicts, ranking/scoring, alerts, recommendations, broker/order actions, and new data artifact publication in this round.
- Preconditions: local manifests only; no provider fetch; authoritative session source remains the existing D2B contract input.
- Stop rules: stop on changed IID tie-break semantics, changed +1..+60 session semantics, non-atomic publication, full-frame D2A/D2B materialization, provider access, or action-surface expansion.
- Next action: move to M4B full-universe artifact dry-run/publication, unless strict independent Reviewer A/B/C is required first.

## Validation evidence

- Focused M4A tests: PASS, 55 tests.
- Broader PEAD regression: PASS, 79 tests.
- Latest targeted non-M4A rerun: PASS, 54 tests across execution_microstructure, context hygiene, and policy-target AppTest after stopping stale pytest/Streamlit smoke processes.
- Execution microstructure focused checks: PASS, 44 tests; orchestrator spool-flush regression PASS; local submit async flush-failure regression PASS.
- Full repository pytest rerun: PASS, `.venv\Scripts\python -m pytest -q` returned exit 0 in 264.6s with no lingering Python processes afterward.
- Clean-exit rerun SAW: PASS for the narrow blocker-fix evidence at `docs/saw_reports/saw_v2_pead_m4a_clean_exit_rerun_20260622.md`.
- Terminal independent Reviewer A/B/C for the original M4A implementation: still pending if strict governance closure is required before M4B.

## Rollback

Code rollback is limited to the M4A edits in scripts/pead_d2_return_contract.py, scripts/pead_d2b_event_window_contract.py, tests/test_pead_d2_returns.py, and tests/test_pead_d2b_event_window_contract.py. No data artifacts were published by this round. If a future full build publishes an artifact, rollback remains the manifest-pointer restore protocol: atomically restore the prior manifest bytes and retain immutable hash-named Parquet files.

## Next action

Move to M4B full-universe artifact dry-run/publication, with M3/M5 WRDS/CRSP entitlement paths and all product/action scope still blocked. Run strict independent Reviewer A/B/C first only if the owner requires that governance gate before M4B.
