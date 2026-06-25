# SAW V2-D0 WRDS Data Lab

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited execution | Domains: Backend, Data, Docs/Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase65-brief.md`

RoundID: ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT
ScopeID: V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT

## Scope And Ownership

Work round scope: implement the offline WRDS permission matrix, WRDS probe contract, snapshot manifest contract, schema registry, tests, and governance docs for V2-D0 while keeping G9 context-only and dashboard reader on HOLD.

Owned files changed in this round:

- `v2_discovery/data_lab/__init__.py`
- `v2_discovery/data_lab/wrds_probe.py`
- `v2_discovery/data_lab/permission_matrix.py`
- `v2_discovery/data_lab/snapshot_manifest.py`
- `v2_discovery/data_lab/schema_registry.py`
- `contracts/data_snapshot/wrds_permission_matrix.schema.json`
- `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`
- `tests/test_v2_wrds_permission_matrix.py`
- `tests/test_v2_snapshot_manifest_contract.py`
- `tests/test_v2_data_lab_no_v1_writes.py`
- `pyproject.toml`
- `requirements.txt`
- `docs/architecture/v2_wrds_data_lab_policy.md`
- `docs/handover/v2_d0_wrds_permission_snapshot_handover.md`
- `docs/context/*_current.md`
- `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md`

Acceptance checks:

- CHK-01 permission matrix validates through dataclass and JSON Schema with root provider/output/V1 flags false.
- CHK-02 WRDS probe contract is offline-only and records no WRDS connection attempt.
- CHK-03 snapshot manifest validates PIT policy and rejects V1, boot-status, absolute, drive-letter, UNC, URI, traversal, and non-sandbox storage paths.
- CHK-04 schema registry and dataclass payload validators reject constant drift, missing approval refs, denied-action drift, and extra PIT fields.
- CHK-05 source guard covers every `v2_discovery/data_lab/*.py` module and finds no provider/runtime/write/candidate-promotion surface.
- CHK-06 dependency manifests declare direct `jsonschema==4.26.0` and `pip check` passes.
- CHK-07 focused compile and V2-D0 pytest pass.
- CHK-08 current context packet rebuilds and validates.

## Subagent Passes

Ownership check: PASS. Parent implementation owner differs from SAW Implementer and Reviewer A/B/C agents.

| Agent | Role | Status | Summary |
|---|---|---|---|
| Descartes | Implementer pass | BLOCK then reconciled PASS | Found missing SAW report artifact reference; no code high/critical issue. |
| Gibbs | Reviewer A strategy correctness/regression | BLOCK then reconciled PASS | Found falsey flag, denied vocabulary, source guard, and missing SAW report gaps. |
| Euclid | Reviewer B runtime/operational resilience | BLOCK then reconciled PASS | Found Windows/UNC path bypass, schema-only validation gap, missing SAW report, and undeclared direct `jsonschema`. |
| Meitner | Reviewer C data integrity/performance | BLOCK then reconciled PASS | Found schema/dataclass parity gap, storage path confinement gap, and missing SAW report. |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Referenced SAW report was missing, blocking SAWBlockValidation. | Published this report at `docs/saw_reports/saw_v2_d0_wrds_data_lab_20260601.md`. | Parent | Fixed |
| High | Windows absolute/UNC and rooted planned storage paths could bypass the relative prefix guard. | Required repo-relative storage under `data/runtime_cache/v2_data_lab/`; rejected absolute, drive-letter, UNC, URI, traversal, V1, registry, and boot paths; added regressions. | Parent | Fixed |
| High | Schema registry and dataclass validators could disagree on invalid payloads. | Made schema registry call dataclass validators after JSON Schema validation; enforced constants, denied-action equality, and exact PIT policy fields; added regressions. | Parent | Fixed |
| Medium | Root false flags accepted falsey non-bool values. | Required literal `False` in permission and snapshot validators; added regressions for `0`, `None`, and empty string. | Parent | Fixed |
| Medium | Denied-action vocabulary did not explicitly include recommendations, promotion, SQLite, SafeBoot, or BootReady. | Expanded `DENIED_ACTIONS`; JSON Schemas require the exact list; tests assert the full set. | Parent | Fixed |
| Medium | Source guard did not scan every new data-lab module. | Reworked test to scan every `v2_discovery/data_lab/*.py` file. | Parent | Fixed |
| Medium | `jsonschema` was imported directly but not declared directly. | Added `jsonschema==4.26.0` to `pyproject.toml` and `requirements.txt`; `requirements.lock` already contained it. | Parent | Fixed |
| Low | `allowed_uses` could be overread as execution approval. | Root contract flags, denied actions, policy docs, and context surfaces state future uses require separate approval; no code path executes them. | Parent | Documented |

## Scope Split Summary

In-scope findings/actions:

- All Reviewer A/B/C High and Medium findings against V2-D0 contracts were fixed in this round.
- Focused tests, dependency hygiene, pip check, context-builder tests, context rebuild, closure packet validation, and SAW block validation were rerun after reconciliation.

Inherited out-of-scope findings/actions:

- Existing broad dirty worktree state predates this V2-D0 round and remains outside this scope.
- Actual WRDS permission truth is still pending user/source approval and is not a defect in the offline contract.
- DataReadyStrict, SafeBoot, and BootReady remain governed-data/boot-control gates outside V2-D0.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/architecture/v2_wrds_data_lab_policy.md` | Added V2-D0 authority, contract, PIT policy, formulas, acceptance checks, and rollback. | Reviewed |
| `docs/handover/v2_d0_wrds_permission_snapshot_handover.md` | Added PM handover, evidence matrix, roadmap, and new-context packet. | Reviewed |
| `docs/context/planner_packet_current.md` | Added V2-D0 latest addendum and first command. | Reviewed |
| `docs/context/impact_packet_current.md` | Added changed files, interfaces, evidence, and forbidden actions. | Reviewed |
| `docs/context/bridge_contract_current.md` | Added PM/planner bridge and next decision. | Reviewed |
| `docs/context/done_checklist_current.md` | Added machine-checkable V2-D0 done criteria. | Reviewed |
| `docs/context/multi_stream_contract_current.md` | Added Backend/Data/Frontend/Docs stream split. | Reviewed |
| `docs/context/post_phase_alignment_current.md` | Added bottleneck and no-change alignment. | Reviewed |
| `docs/context/observability_pack_current.md` | Added drift signals and skill activation notes. | Reviewed |
| `docs/decision log.md` | Added V2-D0 decision, evidence, and contract lock. | Reviewed |
| `docs/notes.md` | Added formula register and reconciliation notes. | Reviewed |
| `docs/lessonss.md` | Added contract-substrate guardrail lesson. | Reviewed |

## Document Sorting

GitHub-optimized document order is maintained according to `docs/checklist_milestone_review.md`: product/spec surfaces, phase brief, handover, notes/lessons/decision log, then SAW/current context artifacts.

## Evidence

| EvidenceID | Command | Result |
|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile v2_discovery\data_lab\__init__.py v2_discovery\data_lab\permission_matrix.py v2_discovery\data_lab\wrds_probe.py v2_discovery\data_lab\snapshot_manifest.py v2_discovery\data_lab\schema_registry.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py` | PASS |
| EVD-02 | `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` | PASS, 17 passed |
| EVD-03 | `.venv\Scripts\python -m pytest tests\test_dependency_hygiene.py -q` | PASS, 3 passed |
| EVD-04 | `.venv\Scripts\python -m pip check` | PASS, no broken requirements |
| EVD-05 | `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` | PASS, 21 passed |
| EVD-06 | `.venv\Scripts\python scripts\build_context_packet.py` and `--validate` | PASS |
| EVD-07 | `.venv\Scripts\python .codex\skills\_shared\scripts\validate_se_evidence.py ...` | VALID |
| EVD-08 | `.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py ...` | VALID |

## Open Risks

Open Risks:

- Actual WRDS permission truth remains pending explicit user/source approval.
- Any future read-only WRDS probe, snapshot generation, storage path, extraction log, or rollback/removal policy requires a new explicit approval.
- Inherited broad dirty worktree state remains out of scope and is not V2-D0 evidence.

## Next Action

Next action:

Approve exact WRDS account/library/table permission truth before any read-only probe, or hold.

ClosurePacket: RoundID=ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT; ScopeID=V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=actual_WRDS_permission_truth_pending_user_source_approval_and_inherited_dirty_worktree_out_of_scope; NextAction=approve_exact_wrds_permission_truth_before_read_only_probe_or_hold

ClosureValidation: PASS

SAWBlockValidation: PASS
