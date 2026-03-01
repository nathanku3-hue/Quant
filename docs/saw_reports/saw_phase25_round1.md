SAW Report: Phase 25 (Operational Hardening Cycle) Round 1

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init (inherited) | Domains: Ops, Backend, Frontend/UI | FallbackSource: docs/spec.md + docs/phase_brief/phase25-brief.md

RoundID: R_PHASE25_20260228_01
ScopeID: S_PHASE25_OPS_HARDENING

Scope (one-line):
Close orchestrator E2E idempotency proof, Streamlit cache-reset UX hardening, and deprecation cleanup with full SAW reconciliation to zero in-scope Critical/High findings.

Top-Down Snapshot
L1: Backtest Engine (Signal System)
L2 Active Streams: Ops, Backend, Frontend/UI
L2 Deferred Streams: Data
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Ops
Active Stage Level: L3

+--------------------+---------------------------------------------------------+--------+------------------------------------------------------------------------+
| Stage              | Current Scope                                           | Rating | Next Scope                                                             |
+--------------------+---------------------------------------------------------+--------+------------------------------------------------------------------------+
| Planning           | Boundary=P25 ops hardening; Owner/Handoff=Impl->RevA/B/C| 100/100| 1) Execute E2E retry+UX hardening [98/100]: close inherited execution risk |
| Executing          | Orchestrator retry contract + UX tests + dep cleanup    | 100/100| 1) Run SAW reviewer matrix [98/100]: identify residual Critical/High   |
| Iterate Loop       | Reconcile reviewer findings with fail-closed patches    | 100/100| 1) Re-run targeted matrix + reviewer rechecks [99/100]: verify closure |
| Final Verification | Publish docs-as-code + SAW validators + closure packet  | 100/100| 1) Mark phase brief SAW PASS [99/100]: lock audit trail                |
+--------------------+---------------------------------------------------------+--------+------------------------------------------------------------------------+

Owned files changed this round:
- `main_bot_orchestrator.py`
- `tests/test_main_bot_orchestrator.py`
- `tests/test_auto_backtest_view.py`
- `scripts/high_freq_data.py`
- `pyproject.toml`
- `requirements.txt`
- `docs/phase_brief/phase25-brief.md`
- `docs/runbook_ops.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/saw_reports/saw_phase25_round1.md`

Ownership check:
- Implementer: `019ca44b-6b02-7e43-b670-a074b7f64039` (Rawls)
- Reviewer A: `019ca45e-c605-7c93-b44c-909d7384124b` (Wegener)
- Reviewer B: `019ca45a-20dc-7f41-b9eb-6921b2b51868` (Epicurus)
- Reviewer C: `019ca45e-c66f-7090-ab4a-b565ce0222e7` (Huygens)
- Implementer/Reviewers distinct: PASS

Acceptance checks:
- CHK-01: Orchestrator idempotent retry helper exists and is used for E2E proof path -> PASS
- CHK-02: Static `client_order_id` preserved across retries -> PASS
- CHK-03: `already exists` accepted only on strict payload parity -> PASS
- CHK-04: Recovery mismatch is terminal fail-closed (`recovery_mismatch`) -> PASS
- CHK-05: Partial batch results cannot silently drop CIDs (`Expected-Observed` reconciliation) -> PASS
- CHK-06: Missing rows fail closed as `batch_result_missing` after retries -> PASS
- CHK-07: Duplicate symbols in initial order set are rejected pre-submit -> PASS
- CHK-08: Malformed non-dict `result` rows are ignored and reconciled via missing-CID path -> PASS
- CHK-09: Retryable faults terminalize as explicit `retry_exhausted` at max attempts -> PASS
- CHK-10: Streamlit cache-corruption/reset behavior covered by integration-style tests -> PASS
- CHK-11: Start-state persist failure aborts simulation (fail closed) -> PASS
- CHK-12: `pandas_datareader` deprecation-noise mitigation implemented with local import + manifest parity -> PASS
- CHK-13: Targeted regression + compile matrix passes in `.venv` -> PASS

Verification evidence:
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py tests/test_main_console.py tests/test_execution_controls.py` -> PASS (`54 passed`).
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`16 passed`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Reviewer rechecks after reconciliation:
  - Reviewer A: PASS (no in-scope Critical/High)
  - Reviewer B: PASS (no in-scope Critical/High)
  - Reviewer C: PASS (no in-scope Critical/High)

Findings table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Partial downstream batch response could silently drop order intents | Added expected-vs-observed CID reconciliation and `batch_result_missing` fail-closed terminalization | Implementer + Reviewer B | Resolved |
| High | Recovery/retry intent could drift if downstream row echoed mismatched order payload | Anchored intent to original `pending_by_cid[cid]` order and added adversarial drift test | Implementer + Reviewer A | Resolved |
| High | Duplicate symbol intents could cause partial side effects before deterministic closure | Added preflight duplicate-symbol rejection before first submit | Implementer + Reviewer C | Resolved |
| High | Malformed row (`order=dict`, `result=non-dict`) could bypass explicit fail-closed classification | Filtered non-dict result rows as malformed/unobserved and added targeted regression test | Implementer + Reviewer A/C | Resolved |
| Medium | Scanner hard-stop does not yet enforce process-tree termination for descendant fan-out | Carry to follow-up ops hardening slice | Ops owner | Open |
| Medium | Deterministic CID fallback still depends on runtime date when no `trade_day`/CID provided | Require explicit CID or canonical `trade_day` in production entrypoint wiring | Execution owner | Open |
| Medium | Helper proof exists in module/test seam but broader production entrypoint wiring remains follow-up | Track as operational integration TODO | Ops owner | Open |

Scope split summary:
- in-scope findings/actions:
  - all in-scope Critical/High findings raised by reviewer passes were reconciled in this round and rechecked to PASS.
  - regression coverage was expanded for retry exhaustion, non-retryable failures, partial/malformed batch responses, and intent anchoring.
- inherited out-of-scope findings/actions:
  - medium process-tree kill semantics and entrypoint wiring follow-up remain open without violating paper-lock policy.

Document Changes Showing (sorted per `docs/checklist_milestone_review.md`):
- `docs/phase_brief/phase25-brief.md` - set status to `SAW PASS`, added reconciliation checks and updated evidence counts - reviewer status: A/B/C reviewed
- `docs/runbook_ops.md` - added Phase 25 orchestrator E2E reconciliation validation pack and fail-closed contracts - reviewer status: A/B/C reviewed
- `docs/notes.md` - added explicit orchestrator formulas/contracts for intent anchoring, completeness, malformed-row handling, and terminalization rules - reviewer status: A/B/C reviewed
- `docs/lessonss.md` - appended self-learning entry for Phase 25 SAW closure and adversarial retry-loop guardrail - reviewer status: A/B/C reviewed
- `docs/decision log.md` - appended D-140 decision with reconciliation rationale, evidence, and carried risks - reviewer status: A/B/C reviewed
- `docs/saw_reports/saw_phase25_round1.md` - published final SAW report and closure packet - reviewer status: A/B/C reviewed

Evidence:
- `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_auto_backtest_view.py`
- `.venv` pytest/py_compile command outputs listed above
- Subagent reviewer passes and rechecks (Implementer + Reviewer A/B/C)

Assumptions:
- Scope is limited to Phase 25 hardening objectives and does not include live-trading unlock.
- Paper-trading lock (`TZ_ALPACA_ALLOW_LIVE`) remains the governing guardrail.

Open Risks:
- Medium: process-tree termination for scanner subprocess descendants not yet implemented.
- Medium: CID fallback date dependence when upstream does not pass `trade_day` or explicit CID.
- Medium: helper integration into broader production entrypoints remains a follow-up task.

Next action:
- Maintain paper-lock and execute follow-up hardening for process-tree timeout semantics plus entrypoint wiring coverage.

Rollback Note:
- Revert `main_bot_orchestrator.py` and corresponding new `tests/test_main_bot_orchestrator.py` cases if this reconciliation policy is rejected.

SAW Verdict: PASS

ClosurePacket: RoundID=R_PHASE25_20260228_01; ScopeID=S_PHASE25_OPS_HARDENING; ChecksTotal=13; ChecksPassed=13; ChecksFailed=0; Verdict=PASS; OpenRisks=Medium_process_tree_timeout_gap+Medium_cid_date_fallback_dependency+Medium_entrypoint_wiring_followup; NextAction=Maintain_paper_lock_and_schedule_process_tree_and_entrypoint_wiring_hardening_in_next_ops_slice

ClosureValidation: PASS
SAWBlockValidation: PASS

PhaseEndValidation: N/A
PhaseEndChecks: CHK-PH-01, CHK-PH-02, CHK-PH-03, CHK-PH-04, CHK-PH-05, CHK-PH-06
HandoverDoc: N/A
HandoverAudience: PM
ContextPacketReady: N/A
ConfirmationRequired: N/A
