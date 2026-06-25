# V2 PEAD M4B Full-Universe Artifact Dry-Run and Publication Brief

Mode: CLOSURE_REPORT
Status: BLOCKED
Date: 2026-06-23
RoundID: ROUND-20260623-V2-PEAD-M4B1-EVIDENCE-CONTRACT-REPAIR
ScopeID: V2_PEAD_M4B1_EVIDENCE_CONTRACT_REPAIR
Owner: Data + Docs/Ops

## Authoritative M4B.1 BLOCK

Superseded on authorization status by ROUND-20260623-V2-PEAD-M4B1-EVIDENCE-CONTRACT-REPAIR; still valid only for guardrails.

- M4B.1 is BLOCK before baseline because the current evidence does not yet satisfy the required same-window, same-cost, same-`engine.run_simulation` delta-metric gate against the latest baseline.
- The prior M4B PASS and Strategy Research Replay dashboard recommendation are stale on authorization status. Historical execution text remains below for provenance and guardrails only.
- M4C / dashboard work is blocked.
- The single next action is a separately authorized read-only, write-isolated baseline. It must not write canonical evidence, canonical JSON, manifests, processed artifacts, strategy output, or UI state.
- This repair round does not run PEAD generation, the baseline, broader tests, provider access, or any data/product action.

## Current acceptance criteria

- [x] Authoritative M4B.1 BLOCK truth precedes the historical baseline.
- [x] Stale M4B PASS/dashboard authorization is explicitly superseded without deleting historical evidence.
- [x] M4C/dashboard is blocked.
- [x] The next action is constrained to a read-only, write-isolated baseline with no canonical evidence writes.
- [x] Context packet regenerated and validated after source truth is blocked.
- [ ] Baseline executed; explicitly outside this round.
- [ ] M4B.1 closure or M4C/dashboard authority granted; explicitly blocked.

## Superseded Historical Objective

Build and publish the full-universe D2A and D2B local data artifacts and the daily benchmark artifact D3 in bounded memory. Execute the dry-run, publish the immutable full-universe files and atomic manifest pointers, and run the real-data validation and calendar-time inference against the full-universe artifacts to produce separate evidence verification documents, while keeping yfinance provider access, PIT claims, estimator/UI changes, alpha verdicts, ranking/scoring, alerts, recommendations, and broker/order actions blocked.

## Superseded Historical Execution Contract

- D2A full build is run via `--build` on `scripts/pead_d2_return_contract.py` to produce `pead_d2_daily_returns.parquet` and its manifest pointer.
- D2B full build is run via `--build` on `scripts/pead_d2b_event_window_contract.py` to resolve D1 and the new full D2A manifest, and publish `pead_d2b_event_windows.parquet` and its manifest.
- D3 benchmark artifact is built via `--build` on `scripts/pead_d3_benchmark_artifact.py` passing `--d2b-manifest data/processed/pead_d2b_event_windows.parquet.manifest.json` to publish the daily benchmark artifact.
- Validation and calendar-time inference are run against the published full-universe artifacts to generate separate evidence files:
  - `docs/context/e2e_evidence/pead_real_data_validation_full_universe.json`
  - `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`
- The legacy/sample evidence files `pead_real_data_validation_20260620.json` and `pead_calendar_time_inference_m1b.json` must remain unchanged and protected at their respective SHA256 hashes.
- All operations must run in bounded memory using DuckDB and disk spill as implemented.

## Superseded Historical Ship-Fast Decision Gate

Reference: `docs/templates/ship_fast_decision_gate.md`.

- What is done: M4A memory-bounded builders for D2A/D2B implemented, and focused tests verify semantic equivalence and atomic replacement.
- What is blocked: M3/M5 WRDS/CRSP entitlement paths remain blocked.
- User order: Move to M4B full-universe artifact dry-run/publication.
- Recommended next step: Execute the dry-run, publish the full dataset, run the validation script against them, and verify everything with tests.
- Decision needed from user: APPROVED.
- Scope limit: Execution-only. No changes to strategy logic, mathematical formulas, or build code.

## Superseded Historical Acceptance Criteria

- [ ] Full-universe D2A artifact built and published atomically. Manifest `pead_d2_daily_returns.parquet.manifest.json` points to the new immutable parquet file.
- [ ] Full-universe D2B artifact built and published atomically. Manifest `pead_d2b_event_windows.parquet.manifest.json` points to the new immutable parquet file.
- [ ] Daily benchmark D3 artifact built and published atomically against the new D2B manifest.
- [ ] Full-universe real-data validation JSON generated at `docs/context/e2e_evidence/pead_real_data_validation_full_universe.json`.
- [ ] Full-universe calendar-time inference JSON generated at `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.
- [ ] Legacy validation and calendar-time JSON hashes are verified unchanged.
- [ ] Full repository pytest passes and no Python processes remain.
- [ ] Implementer and Reviewer A/B/C SAW passes.

## Rollback

Rollback protocol is to atomically restore the prior manifest pointers (`pead_d2_daily_returns.parquet.manifest.json` and `pead_d2b_event_windows.parquet.manifest.json`) to point to the sample Parquet files, and update any pointers back.
