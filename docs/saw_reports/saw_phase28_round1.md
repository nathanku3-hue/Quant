SAW Report: Phase 28 (Entrypoint Contract Remediation) Round 1

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init (inherited) | Domains: Ops, Backend | FallbackSource: docs/spec.md + docs/phase_brief/phase28-brief.md

RoundID: R_PHASE28_20260228_01
ScopeID: S_PHASE28_ENTRYPOINT_CONTRACT_REMEDIATION

Scope (one-line):
Execute Step 1 production entrypoint wiring remediation by enforcing atomic payload validation, strict CID lineage, exact local-submit intent parity, and fail-closed broker recovery contracts without changing paper-lock boundaries.

Top-Down Snapshot
L1: Backtest Engine (Signal System)
L2 Active Streams: Ops, Backend
L2 Deferred Streams: Data, Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Ops
Active Stage Level: L3

+--------------------+----------------------------------------------------------+--------+------------------------------------------------------------------------+
| Stage              | Current Scope                                            | Rating | Next Scope                                                             |
+--------------------+----------------------------------------------------------+--------+------------------------------------------------------------------------+
| Planning           | Boundary=P28 remediation; Owner/Handoff=Impl->RevA/B/C  | 100/100| 1) Implement strict seam contracts [98/100]: close SAW BLOCK findings |
| Executing          | Atomic gate + CID lineage + parity + recovery strictness| 100/100| 1) Expand negative tests [98/100]: lock malformed/recovery branches   |
| Iterate Loop       | Reconcile reviewer findings including null-semantics     | 100/100| 1) Patch final blocker [99/100]: align lookup/matcher semantics       |
| Final Verification | Impacted matrix + SAW rechecks + docs-as-code closure    | 100/100| 1) Publish PASS artifact [99/100]: lock institutional evidence        |
+--------------------+----------------------------------------------------------+--------+------------------------------------------------------------------------+

Owned files changed this round:
- `main_console.py`
- `execution/rebalancer.py`
- `execution/broker_api.py`
- `main_bot_orchestrator.py`
- `tests/test_main_console.py`
- `tests/test_execution_controls.py`
- `tests/test_main_bot_orchestrator.py`
- `docs/phase_brief/phase28-brief.md`
- `docs/runbook_ops.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_phase28_round1.md`

Ownership check:
- Implementer: `019ca55a-c6bd-7070-8e71-d6572af8338c` (Carver)
- Reviewer A: `019ca57a-6587-7c01-9d9c-15f07696bae8` (Dalton)
- Reviewer B: `019ca57c-4ddd-7de3-a310-c65e01af4f74` (Zeno)
- Reviewer C: `019ca57d-92da-74d3-817b-605ac277dd09` (Faraday)
- Implementer/Reviewers distinct: PASS

Acceptance checks:
- CHK-01: malformed payload rows trigger full-batch abort (no partial execution) -> PASS
- CHK-02: payload duplicate ticker rejected -> PASS
- CHK-03: payload duplicate client_order_id rejected -> PASS
- CHK-04: payload trade_day required and calendar-valid -> PASS
- CHK-05: payload/calculated symbol-set parity enforced -> PASS
- CHK-06: payload client_order_id preserved through local submit -> PASS
- CHK-07: strict local parity enforced (`symbol/side/qty/order_type/limit_price/client_order_id`) -> PASS
- CHK-08: limit intent (`order_type/limit_price`) passes rebalancer -> broker boundary -> PASS
- CHK-09: broker submit rejects bool qty -> PASS
- CHK-10: broker recovery requires CID parity -> PASS
- CHK-11: market recovery limit semantics strict (`None/""/"none"/"null"` only) -> PASS
- CHK-12: local-submit post-submit notify failure aborts non-zero -> PASS
- CHK-13: targeted regression suite passes -> PASS
- CHK-14: impacted matrix passes (`109 passed`) -> PASS
- CHK-15: final SAW A/B/C rechecks report no in-scope unresolved Critical/High -> PASS

Verification evidence:
- `.venv\Scripts\python -m pytest tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py -q` -> PASS.
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS (`109 passed in 5.03s`).
- `.venv\Scripts\python -m py_compile main_console.py main_bot_orchestrator.py execution/broker_api.py execution/rebalancer.py tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py` -> PASS.
- Final SAW rechecks:
  - Reviewer A: PASS
  - Reviewer B: PASS (prior BLOCK condition cleared)
  - Reviewer C: PASS

Findings table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Malformed payload rows could execute partially (fail-open) | Added atomic payload validator with whole-batch abort on any invalid row | Implementer + Reviewer C | Resolved |
| High | Payload CID lineage was dropped in local-submit path | Seeded and enforced payload CID continuity through helper->broker submit | Implementer + Reviewer A | Resolved |
| High | Local seam could drift from payload intent (`order_type/limit_price`) | Added strict parity seeding and validation for local submit order envelope | Implementer + Reviewer A | Resolved |
| High | Recovery parity excluded `order_type/limit_price/client_order_id` semantics | Upgraded recovery matcher and coverage for strict parity paths | Implementer + Reviewer B | Resolved |
| Medium | Market recovery null-semantics inconsistent across lookup vs matcher | Preserved raw recovered `limit_price` and aligned strict market null semantics | Implementer + Reviewer B | Resolved |
| Low | Bool qty could coerce to numeric in direct broker submit | Added explicit bool-qty rejection + regression test | Implementer + Reviewer B | Resolved |
| Low | Semantic date drift risk on payload trade_day | Enforced calendar-valid `trade_day` check + regression test | Implementer + Reviewer C | Resolved |
| Low | Unknown broker null sentinels may fail closed as recovery mismatch | Keep fail-closed behavior; consider sentinel expansion only with broker evidence | Ops owner | Open |

Scope split summary:
- in-scope findings/actions:
  - all in-scope Critical/High findings from prior SAW BLOCK were reconciled in-round,
  - all acceptance checks passed with impacted matrix proof.
- inherited out-of-scope findings/actions:
  - none promoted as blockers in this round; paper-lock remains unchanged.

Document Changes Showing (sorted per `docs/checklist_milestone_review.md`):
- `docs/phase_brief/phase28-brief.md` - published Phase 28 brief with acceptance checks/evidence/open risks - reviewer status: A/B/C reviewed
- `docs/runbook_ops.md` - added Phase 28 validation pack and contract gates - reviewer status: A/B/C reviewed
- `docs/notes.md` - appended Phase 28 contract/formula notes for atomic gate and strict recovery semantics - reviewer status: A/B/C reviewed
- `docs/lessonss.md` - appended Phase 28 lessons-learned entry - reviewer status: A/B/C reviewed
- `docs/decision log.md` - appended D-143 decision/rationale/evidence/open risks - reviewer status: A/B/C reviewed
- `docs/saw_reports/saw_phase28_round1.md` - published SAW closure artifact - reviewer status: A/B/C reviewed

Evidence:
- `main_console.py`, `execution/rebalancer.py`, `execution/broker_api.py`, `main_bot_orchestrator.py`
- `tests/test_main_console.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py`
- `.venv` pytest and py_compile command outputs listed above
- Subagent rechecks (Implementer + Reviewer A/B/C)

Assumptions:
- Scope remains limited to Step 1 entrypoint remediation; no feature, UI, or live-unlock changes are included.
- Paper-lock controls in `execution/broker_api.py` remain mandatory and unchanged.

Open Risks:
- Low: broker null sentinel encodings outside `{None, "", "none", "null"}` on market recovery will intentionally fail closed as `recovery_mismatch`.

Next action:
- Keep paper-lock active and proceed to the next approved hardening slice (process-tree descendant verification / broader entrypoint coverage), with this Phase 28 contract set treated as baseline.

Rollback Note:
- Revert `main_console.py`, `execution/rebalancer.py`, `execution/broker_api.py`, `main_bot_orchestrator.py`, `tests/test_main_console.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py`, and associated Phase 28 docs if this bundle is rejected.

SAW Verdict: PASS

ClosurePacket: RoundID=R_PHASE28_20260228_01; ScopeID=S_PHASE28_ENTRYPOINT_CONTRACT_REMEDIATION; ChecksTotal=15; ChecksPassed=15; ChecksFailed=0; Verdict=PASS; OpenRisks=Low_unknown_market_limit_null_sentinel_encodings_fail_closed; NextAction=Proceed_to_next_approved_hardening_slice_under_paper_lock

ClosureValidation: PASS
SAWBlockValidation: PASS

PhaseEndValidation: N/A
PhaseEndChecks: CHK-PH-01, CHK-PH-02, CHK-PH-03, CHK-PH-04, CHK-PH-05, CHK-PH-06
HandoverDoc: N/A
HandoverAudience: PM
ContextPacketReady: N/A
ConfirmationRequired: N/A
