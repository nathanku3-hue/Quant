# SAW V2-D0.1 Expert 1-6 TODO Gates - 2026-06-02

SAW Verdict: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Data, Docs/Ops, Security | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md
RoundID: ROUND-20260602-V2-D0-1-EXPERT-1-6-TODO-GATES
ScopeID: V2_D0_1_EXPERT_1_6_AGREEMENT_TODO_GATES

Scope: execute the high-confidence offline TODOs while waiting for Expert 1-6 follow-up responses: harden direct Python validators, refresh current truth surfaces, document approval/quarantine gates, and verify no provider-facing work was authorized or run.

Owned files changed in this round:
- `v2_discovery/data_lab/permission_matrix.py`
- `v2_discovery/data_lab/snapshot_manifest.py`
- `tests/test_v2_wrds_permission_matrix.py`
- `tests/test_v2_snapshot_manifest_contract.py`
- `docs/context/planner_packet_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/saw_reports/saw_v2_d0_1_expert_1_6_todo_gates_20260602.md`

Acceptance checks:
- CHK-01 Permission-matrix direct validator rejects row-level extra/missing fields and raw payload coercion.
- CHK-02 Snapshot-manifest direct validator rejects dataset row drift and raw payload coercion.
- CHK-03 Current truth/product/spec docs record Expert 1-6 agreement as advisory gates only.
- CHK-04 Security boundary records explicit approval text requirement and inherited legacy WRDS/BvD quarantine risk without repeating secret-like values.
- CHK-05 Focused V2-D0 tests, compileall, and security/provider-port tests pass.
- CHK-06 Context packet rebuilds and validates.
- CHK-07 Subagent reviewer passes return no in-scope Critical/High/Medium findings.

Subagent passes:
- Implementer support: Backend worker hardened `snapshot_manifest.py` and tests; Docs/Ops worker refreshed truth surfaces and governance docs; Security explorer classified allowed/blocked boundary and legacy quarantine risk.
- Reviewer A strategy/regression pass: Copernicus PASS.
- Reviewer B runtime/docs/operational pass: Wegener PASS; no authorization leak across reviewed truth surfaces.
- Reviewer C data-integrity/security pass: McClintock PASS; no provider/probe/snapshot/data-output/write path introduced.
- Ownership check: PASS. Parent orchestrator reconciled and integrated; Reviewer A/B/C were distinct subagents.

Findings table:
Severity | Impact | Fix | Owner | Status
Low | Direct validators previously needed row-level parity with JSON Schema | Added exact entry/dataset key and raw-type/case validation; focused regressions pass | Backend/Data | Fixed
Low | Expert agreement could be overread as WRDS/PIT/probe authorization | Refreshed truth surfaces to mark V2-D0.1 entitlement-only and all provider/runtime/data paths blocked | Docs/Ops | Fixed
Low | Legacy WRDS/BvD helper files remain in tracked history/current tree | Documented quarantine risk and did not execute or alter them without explicit approval | Security/Ops | Open inherited

Scope split summary:
in-scope findings/actions: direct validator hardening, focused regressions, current truth refresh, approval-text gate, quarantine-risk documentation, context packet refresh, and subagent review reconciliation.
inherited out-of-scope findings/actions: actual WRDS entitlement evidence, approval text, read-only probe execution, provider credentials, snapshot generation, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, and cleanup/retirement of legacy provider-touching files.

Document Changes Showing:
- `v2_discovery/data_lab/permission_matrix.py`: direct payload validator now rejects entry extra/missing fields, non-string text fields, non-bool `pit_required`, uppercase/invalid allowed uses, non-false safety flags, invalid approval refs, and non-string notes before dataclass normalization.
- `v2_discovery/data_lab/snapshot_manifest.py`: direct payload validator now rejects dataset extra/missing fields and raw-type/status drift before dataclass normalization.
- `tests/test_v2_wrds_permission_matrix.py`: adversarial regressions cover entry extra fields and raw coercion drift.
- `tests/test_v2_snapshot_manifest_contract.py`: adversarial regressions cover dataset row key drift and raw coercion drift.
- `docs/context/*_current.md`: Expert 1-6 agreement gates, V2-D0.1 entitlement-only authority, blocked runtime/provider paths, and next action updated.
- `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`, `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md`: product/governance record refreshed with advisory-only agreement gates and open TODOs.

Document Sorting: implementation files first for validator parity, tests second for regression proof, current truth surfaces third, product/spec/governance docs fourth, SAW report last for round closeout.

Verification evidence:
- `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` -> PASS, 37 passed.
- `.venv\Scripts\python -m compileall v2_discovery\data_lab tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_security_policy.py tests\test_provider_ports.py -q` -> PASS, 14 passed; one third-party `websockets.legacy` deprecation warning.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `git grep -l "wrds.Connection\|import wrds\|getpass" --` -> tracked legacy provider-touching files found; treated as inherited quarantine risk only.

Open Risks:
- Non-secret WRDS entitlement evidence is still missing.
- Explicit V2-D0.1 approval text is still missing.
- Legacy WRDS/BvD helper surfaces remain inherited quarantine risk until separately audited, retired, or cleaned with explicit approval.
- V2 alpha validity packet template remains pending future docs/design work.

Next action:
Collect V2-D0.1 non-secret WRDS entitlement evidence and explicit approval text, or hold. Do not run a WRDS probe or prepare provider-facing execution from this round.

ClosurePacket: RoundID=ROUND-20260602-V2-D0-1-EXPERT-1-6-TODO-GATES; ScopeID=V2_D0_1_EXPERT_1_6_AGREEMENT_TODO_GATES; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=entitlement_evidence_missing_approval_text_missing_legacy_wrds_quarantine_open_v2_alpha_validity_template_pending; NextAction=collect_v2_d0_1_entitlement_evidence_and_approval_text_or_hold
ClosureValidation: PASS
SAWBlockValidation: PASS
