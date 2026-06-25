# SAW V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping - 2026-06-02

SAW Verdict: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: parent-orchestrated-subagent-request | Domains: Backend/Data Contracts, Docs/Ops Governance, Security/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md
RoundID: ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING
ScopeID: V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING

Scope: resolve the high-confidence `TODO-MATRIX-001` gap by adding an offline V2-D0.1 permission-truth builder/validator, focused regressions, and docs/context bookkeeping. This round does not authorize WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, legacy cleanup, public/main closure, or V2 validity/C3 lock claims.

Owned files changed in this round:
- `v2_discovery/data_lab/permission_truth.py`
- `v2_discovery/data_lab/__init__.py`
- `tests/test_v2_wrds_permission_truth_scope.py`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`
- `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`
- `docs/architecture/v2_wrds_data_lab_policy.md`
- `docs/context/planner_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_v2_d0_1_scope_cleanroom_runtime_20260602.md`
- `docs/saw_reports/saw_v2_d0_1_todo_matrix_bookkeeping_20260602.md`

Acceptance checks:
- CHK-01 `TODO-MATRIX-001` is resolved by an offline V2-D0.1 permission-truth builder/validator.
- CHK-02 V2-D0.1 entitlement truth covers exactly five rows: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus`.
- CHK-03 PEAD_V2_001 starter scope is separate and excludes `ibes.det_epsus` as `not_requested`.
- CHK-04 Approved V2-D0.1 rows require row/table `approval_ref` and `allowed_uses=["provenance_contract"]`.
- CHK-05 Direct validator rejects root/row drift, root constants, duplicate rows, unknown approval refs, credentials, query/output fields, and widened flags.
- CHK-06 Docs/current truth mark `TODO-MATRIX-001` resolved while preserving entitlement, approval, clean-room, legacy, validity/C3, and public/main gaps.
- CHK-07 No provider/probe/snapshot/data-write/runtime/dashboard/scoring/broker/SQLite/SafeBoot/BootReady/cleanup authorization or primitive is introduced.
- CHK-08 Focused tests, compileall, context build/validate, and SAW validators pass.

Subagent passes:
- Implementer Worker A: PASS. Added `permission_truth.py`, exports, and focused tests.
- Docs/Ops Worker B: PASS. Updated docs/current truth and initial SAW bookkeeping report.
- Reviewer A strategy/research correctness: PASS. Low stale PEAD wording in `docs/architecture/v2_wrds_data_lab_policy.md` fixed by parent.
- Reviewer B runtime/ops resilience: PASS. No provider/runtime/write primitive or approval-gate drift found.
- Reviewer C data integrity/security: PASS. Low root-constant test coverage gap fixed by parent.
- Ownership check: PASS. Implementer/docs workers and Reviewer A/B/C are different subagents; parent reconciled findings only.

Findings table:

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | Stale WRDS policy wording still said the PEAD starter signal was unresolved. | Updated policy to say that wording was historical and is superseded by the four-row Compustat PEAD starter decision. | Parent | Fixed |
| Low | `permission_truth` root constants were rejected by code but not all had direct regression mutations. | Added root constant drift tests for schema version, artifact id, scope id, authority, code ref, and denied actions. | Parent | Fixed |
| Low | Matrix closure could be overread as WRDS/provider approval. | Repeated boundary language and kept entitlement/approval/provider/probe gates open across truth surfaces. | Worker B / Parent | Fixed |

Scope split summary:
- in-scope findings/actions: offline permission-truth metadata, focused tests, docs/context TODO closure, reviewer reconciliation, and validation.
- inherited out-of-scope findings/actions: entitlement evidence, explicit approval text, clean-room proof packet, legacy WRDS cleanup, V2 validity/C3 lock, public/main mismatch, provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, and BootReady.

Document Changes Showing:
- `v2_discovery/data_lab/permission_truth.py`: offline V2-D0.1 builder/validator; reviewer status PASS.
- `v2_discovery/data_lab/__init__.py`: exports new offline contract helpers; reviewer status PASS.
- `tests/test_v2_wrds_permission_truth_scope.py`: exact-row, PEAD-scope, approval-ref, allowed-use, root drift, and forbidden-field regressions; reviewer status PASS.
- `docs/context/planner_packet_current.md`: latest addendum and next todos updated; reviewer status PASS.
- `docs/context/done_checklist_current.md`: `TODO-MATRIX-001` checked resolved and blocked gates preserved; reviewer status PASS.
- `docs/context/bridge_contract_current.md`: PM/planner delta and boundary updated; reviewer status PASS.
- `docs/context/impact_packet_current.md`: changed files, touched interfaces, evidence, and open gaps updated; reviewer status PASS.
- `docs/context/post_phase_alignment_current.md`: stream alignment and remaining bottleneck updated; reviewer status PASS.
- `docs/context/observability_pack_current.md`: drift and forbidden-attempt visibility updated; reviewer status PASS.
- `docs/context/multi_stream_contract_current.md`: stream coordination updated; reviewer status PASS.
- `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`: superseding TODO-MATRIX update added; reviewer status PASS.
- `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`: stale TODO-MATRIX open status superseded; reviewer status PASS.
- `docs/architecture/v2_wrds_data_lab_policy.md`: permission-truth addendum and stale PEAD wording fixed; reviewer status PASS.
- `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`: product/spec notices updated; reviewer status PASS.
- `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md`: phase, formula, decision, and lesson records updated; reviewer status PASS.
- `docs/saw_reports/saw_v2_d0_1_scope_cleanroom_runtime_20260602.md`: historical TODO-MATRIX row marked superseded; reviewer status PASS.

Document Sorting (GitHub-optimized): product/spec first, phase brief, handover/policy, notes/lessons/decision log, current truth surfaces, SAW report.

Verification evidence:
- `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_truth_scope.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` -> PASS, 51 passed.
- `.venv\Scripts\python -m compileall v2_discovery\data_lab tests\test_v2_wrds_permission_truth_scope.py -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py ...` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_v2_d0_1_todo_matrix_bookkeeping_20260602.md` -> PASS.

Open Risks:
- `TODO-ENTITLEMENT-001`: five-row non-secret entitlement evidence is still missing.
- `TODO-APPROVAL-001`: explicit V2-D0.1 approval text is still missing.
- `TODO-CLEANROOM-001`: full clean-room surface and proof packet remain pending.
- `TODO-LEGACY-WRDS-001`: legacy WRDS/BvD cleanup authority remains unapproved.
- `TODO-VALIDITY-001`: V2 alpha validity packet and `C3_LOCK_PEAD_V2_001_v1` are not built.
- `TODO-PUBLIC-MAIN-001`: public/main status mismatch remains open.

Next action:
Collect or decline five-row V2-D0.1 entitlement evidence and explicit approval text, or hold. Keep provider/probe/snapshot/runtime/cleanup actions blocked.

ClosurePacket: RoundID=ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING; ScopeID=V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=entitlement_approval_cleanroom_legacy_validity_public_main_open; NextAction=collect_or_decline_v2_d0_1_entitlement_approval_or_hold
ClosureValidation: PASS
SAWBlockValidation: PASS
