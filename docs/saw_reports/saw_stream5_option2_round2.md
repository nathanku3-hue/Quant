# SAW Report: Stream 5 Option 2 Production Reconciliation (Round 2)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Microstructure / Execution Quant (Stream 5)

RoundID: R20260301-STREAM5-OPT2-R2
ScopeID: STREAM5-OPT2-PROD-RECON-R2
Scope: Reconcile Stream 5 Option 2 production hardening on broker/orchestrator seam and telemetry sink integrity (terminal semantics, latency anchors, slippage integrity, fill aggregation consistency, legacy parquet safety).

Ownership Check:
- Implementer: `Zeno` (`019ca8a5-a0bf-7c00-a49c-9ccfe5bf41b3`)
- Reviewer A: `Copernicus` (`019ca8a5-a0d6-7e13-a0a8-8f9df605c8e2`)
- Reviewer B: `Euclid` (`019ca8a4-543a-7810-9e7f-63f515e17612`)
- Reviewer C: `Copernicus` (`019ca8a5-a0d6-7e13-a0a8-8f9df605c8e2`)
- Result: Implementer and reviewers are distinct agents.

Acceptance Checks:
- CHK-01: Broker quote snapshot supports Alpaca v2 snake_case fields (`bid_price`/`ask_price`) with legacy compatibility.
- CHK-02: Orchestrator fail-closed for malformed `ok` and terminal unfilled outcomes with no retry thrash.
- CHK-03: Terminal status with partial fills is fail-closed and non-retryable.
- CHK-04: Telemetry reconstructs order-level aggregates from `partial_fills` when `fill_summary` is sparse/missing.
- CHK-05: Telemetry synthesizes fill rows for summary-only fill payloads to keep order/fill tables consistent.
- CHK-06: Legacy parquet append dedupe preserves rows lacking `_spool_record_uid`, `record_id`, or `uid`.
- CHK-07: Focused Stream 5 regression matrix passes in `.venv`.
- CHK-08: Compile sanity passes for touched modules.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Terminal status with non-zero fills could enter retry path and resubmit full size | Added terminal-status fail-closed branch for partial-fill outcomes in retry loop; added regression test (`calls == 1`) | Implementer | Fixed |
| High | Missing Alpaca v2 quote field coverage risked midpoint resolution regressions | Added explicit v2 snake_case quote snapshot test alongside legacy-field compatibility test | Implementer | Fixed |
| High | Summary-only fill payloads produced aggregate order fills but empty fill table rows | Added `summary_fallback` synthesized fill row path and regression coverage | Implementer | Fixed |
| Critical | Legacy parquet dedupe could collapse historical rows when `_spool_record_uid`/`record_id`/`uid` were null | Implemented null-safe per-key dedupe path preserving null-key rows; added three regression tests for null-key scenarios | Implementer | Fixed |
| High (Inherited/Out-of-scope) | Sparse `ok=True` payloads can still be accepted via row-order fallback contract in orchestrator success path | Carried as inherited control-plane contract risk for separate scope decision (strict broker-owned success payload policy) | Owner: Orchestrator Control-Plane backlog | Open |

Scope Split Summary:
- in-scope:
  - Closed all in-scope Critical/High findings from Stream 5 Option 2 reconciliation.
  - Added test coverage for Alpaca v2 quote fields.
  - Added terminal partial-fill no-retry fail-closed guard.
  - Added telemetry fill-row synthesis for summary-only payloads.
  - Hardened legacy parquet dedupe for null key columns and added regressions.
- inherited out-of-scope:
  - Sparse `ok=True` acceptance fallback contract in orchestrator success-path validation; requires separate policy decision and compatibility review.

Document Changes Showing:
1. `execution/microstructure.py`
   - Added `summary_fallback` fill-row synthesis for summary-only fills.
   - Hardened legacy parquet dedupe to preserve null-key rows across `_spool_record_uid`/`record_id`/`uid`.
   - Reviewer status: Reviewed (A/C), no unresolved in-scope Critical/High.
2. `main_bot_orchestrator.py`
   - Added terminal-status fail-closed handling for partial-fill outcomes (`terminal_partial_fill:*`) to block retry thrash.
   - Reviewer status: Reviewed (A/B), no unresolved in-scope Critical/High.
3. `tests/test_execution_controls.py`
   - Added Alpaca v2 snake_case quote snapshot coverage (`bid_price`/`ask_price`).
   - Reviewer status: Reviewed (B/C), no unresolved in-scope Critical/High.
4. `tests/test_execution_microstructure.py`
   - Added sparse-fill summary reconstruction assertions.
   - Added summary-only fill-row synthesis regression.
   - Added null-key legacy parquet dedupe preservation regressions for `_spool_record_uid`, `record_id`, and `uid`.
   - Reviewer status: Reviewed (A/C), no unresolved in-scope Critical/High.
5. `tests/test_main_bot_orchestrator.py`
   - Added terminal partial-fill no-retry fail-closed regression.
   - Reviewer status: Reviewed (A/B), no unresolved in-scope Critical/High.
6. `docs/lessonss.md`
   - Added round lesson entry for adversarial telemetry/legacy-schema SAW reconciliation.
   - Reviewer status: Parent reconciliation.

Document Sorting (GitHub-optimized):
1. `docs/lessonss.md`
2. `docs/saw_reports/saw_stream5_option2_round2.md`

Evidence:
- `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py`
- Result: pass
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/microstructure.py tests/test_main_bot_orchestrator.py tests/test_execution_microstructure.py tests/test_execution_controls.py`
- Result: pass

Open Risks:
- Inherited out-of-scope: sparse `ok=True` acceptance fallback contract in orchestrator success-path validation (`order_map` fallback). No in-scope Critical/High unresolved for Stream 5 Option 2 reconciliation.

Next action:
- If approved, execute a dedicated control-plane hardening slice to decide whether to keep or remove sparse-success fallback and migrate tests/contracts accordingly.

ClosurePacket: RoundID=R20260301-STREAM5-OPT2-R2; ScopeID=STREAM5-OPT2-PROD-RECON-R2; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=sparse-ok-true-success-fallback-contract-inherited; NextAction=separate-control-plane-hardening-slice-for-strict-success-payload-policy
ClosureValidation: PASS
SAWBlockValidation: PASS
