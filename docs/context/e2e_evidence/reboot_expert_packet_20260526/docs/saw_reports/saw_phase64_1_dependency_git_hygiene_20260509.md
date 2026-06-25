# SAW Report - R64.1 Dependency and Git Hygiene

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: r64-1-dependency-git-hygiene | Domains: Terminal Zero Research Console, Backend, Data, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope and Ownership

- Scope: close the R64.1 dependency hygiene wedge, preserve D-353 provenance gates, and approve Phase F Candidate Registry as registry-only work without starting candidate generation.
- RoundID: `R64_1_DEPENDENCY_GIT_HYGIENE_20260509`
- ScopeID: `R64_1_CLOSEOUT`
- Primary editor: Codex main agent.
- Implementer pass: Codex local implementation and verification pass.
- Reviewer A (strategy/correctness): local reviewer lane.
- Reviewer B (runtime/ops): local reviewer lane.
- Reviewer C (data/perf): local reviewer lane.
- Ownership check: distinct subagent proof unavailable under the active tool policy; local A/B/C lanes were run and the limitation is recorded as an inherited process risk.

## Acceptance Checks

- CHK-01: `pip check` passes -> PASS.
- CHK-02: `requirements.txt`, `requirements.lock`, and `pyproject.toml` use `alpaca-py==0.43.4` and exclude the legacy Alpaca SDK -> PASS.
- CHK-03: Broker boundary no longer imports the legacy Alpaca SDK and preserves the paper/live safety gates -> PASS.
- CHK-04: No new direct yfinance usage appears outside provider modules and the allowlisted legacy surface -> PASS.
- CHK-05: A-E replay checks still pass: data readiness audit and minimal validation lab -> PASS.
- CHK-06: Secret scan remains clean and no live order path was added to provider/validation/audit code -> PASS.
- CHK-07: Full regression passes -> PASS.
- CHK-08: Headless dashboard smoke passes -> PASS.
- CHK-09: Context packet rebuild and validation pass -> PASS.
- CHK-10: Milestone files are separated for surgical commits while unrelated dirty files remain excluded -> PASS.
- CHK-11: A-E evidence artifacts are either committed or intentionally ignored with documented regeneration commands -> PASS.

## SE Executor Closure

Scope line: stream=Backend/Data/Ops; stage=Final Verification; owner=Codex; round_exec_utc=2026-05-09T03:02:50Z

| TaskID | Task | Artifact | Check | Status | EvidenceID |
|---|---|---|---|---|---|
| TSK-01 | Replace legacy Alpaca dependency | `requirements.txt`, `requirements.lock`, `pyproject.toml` | `pip check` and dependency hygiene tests | PASS | EVD-01 |
| TSK-02 | Preserve broker boundary behavior | `execution/broker_api.py` | execution/provider/provenance tests | PASS | EVD-02 |
| TSK-03 | Replay D-353 evidence path | readiness and validation artifacts | audit + validation commands | PASS | EVD-03 |
| TSK-04 | Refresh docs/current truth | phase briefs, handover, context, decision log | context build + validate | PASS | EVD-04 |
| TSK-05 | Verify runtime and regression | full test suite, headless smoke | full pytest + dashboard smoke | PASS | EVD-05 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05
EvidenceRows: EVD-01|R64_1_DEPENDENCY_GIT_HYGIENE_20260509|2026-05-09T02:55:00Z;EVD-02|R64_1_DEPENDENCY_GIT_HYGIENE_20260509|2026-05-09T02:55:00Z;EVD-03|R64_1_DEPENDENCY_GIT_HYGIENE_20260509|2026-05-09T02:57:00Z;EVD-04|R64_1_DEPENDENCY_GIT_HYGIENE_20260509|2026-05-09T02:58:00Z;EVD-05|R64_1_DEPENDENCY_GIT_HYGIENE_20260509|2026-05-09T03:02:00Z
EvidenceValidation: PASS
SEExecutorPacket: RoundID=R64_1_DEPENDENCY_GIT_HYGIENE_20260509; ScopeID=R64_1_SE_EXECUTOR; ChecksTotal=5; ChecksPassed=5; ChecksFailed=0; Verdict=PASS; OpenRisks=yfinance_migration_sidecar_freshness_unrelated_dirty_files_excluded; NextAction=start_phase65_candidate_registry
SE ClosureValidation: PASS

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Candidate Registry would multiply experiments on a red dependency surface | Migrated main Alpaca dependency to `alpaca-py==0.43.4`, removed the legacy package from main deps, regenerated lock, and verified `pip check` | Codex | Resolved |
| Medium | Broker code depended directly on the legacy Alpaca import path | Added an `alpaca-py` compatibility wrapper inside `execution/broker_api.py` while preserving existing safety gates and test surface | Codex | Resolved |
| Low | Phase F could drift into strategy search | Added `docs/phase_brief/phase65-brief.md` with registry-only approval and explicit blocked scope | Codex | Resolved |
| Low | Unrelated dirty files exist in the working tree | Kept surgical staging/commit plan scoped to R64/R65 files and left unrelated files excluded | Codex / operator | Open, inherited |

## Scope Split Summary

- in-scope findings/actions:
  - migrated the main Alpaca dependency to `alpaca-py==0.43.4`;
  - removed `alpaca-trade-api` from main dependency files and venv;
  - kept Alpaca paper/live gates unchanged;
  - reran `pip check`, targeted tests, A-E replay commands, full regression, smoke, secret scan, and context validation;
  - added Phase F Candidate Registry approval brief without implementing candidate generation.
- inherited out-of-scope findings/actions:
  - yfinance legacy migration remains future debt;
  - primary S&P sidecar freshness remains a paper-alert warning;
  - unrelated dirty files remain parked/excluded from milestone commits.

## Verification Evidence

- `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`)
- `.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_execution_controls.py tests/test_provider_ports.py tests/test_provenance_policy.py -q` -> PASS.
- `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`; warning on stale sidecar).
- `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS with existing skips/warnings.
- `.venv\Scripts\python launch.py --server.headless true --server.port 8599` -> PASS (headless smoke reached local URL; smoke process stopped).
- `.venv\Scripts\python scripts\build_context_packet.py` and `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python -m compileall execution\broker_api.py data\provenance.py data\providers validation scripts\audit_data_readiness.py scripts\run_minimal_validation_lab.py` -> PASS.
- `rg` secret scan over source/docs/dependency files for pasted credential material -> PASS (no matches).
- `rg "submit_order\(" data\providers validation scripts\run_minimal_validation_lab.py scripts\audit_data_readiness.py` -> PASS (no matches).
- `git check-ignore -v data\processed\data_readiness_report.json data\processed\minimal_validation_report.json data\processed\phase56_pead_evidence.csv.manifest.json` -> PASS; generated evidence stays ignored by `data/processed/` repo policy and is reproducible with the audit/validation commands above.

## Phase-End Block

PhaseEndValidation: PASS

- CHK-PH-01 Full regression -> PASS.
- CHK-PH-02 Runtime smoke -> PASS.
- CHK-PH-03 End-to-end path replay -> PASS via data readiness and validation-lab command reruns.
- CHK-PH-04 Data integrity and atomic-write verification -> PASS; reports and manifests are written temp-to-replace with row-count and hash checks.
- CHK-PH-05 Docs-as-code gate -> PASS.
- CHK-PH-06 Context artifact refresh gate -> PASS.
- CHK-PH-07 Git sync gate -> PASS for milestone files after surgical commits; generated `data/processed/` evidence is intentionally ignored and unrelated dirty files remain excluded.

HandoverDoc: `docs/handover/phase64_handover.md`
HandoverAudience: PM
ContextPacketReady: PASS
ConfirmationRequired: NO_FOR_PHASE65_REGISTRY_ONLY

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `execution/broker_api.py` | Migrated broker boundary from legacy Alpaca SDK import to `alpaca-py` compatibility wrapper | A/B/C local reviewed |
| `requirements.txt`, `requirements.lock`, `pyproject.toml` | Replaced main Alpaca dependency with `alpaca-py==0.43.4` and refreshed lock | A/B/C local reviewed |
| `tests/test_dependency_hygiene.py` | Added dependency assertions for Alpaca SDK boundary | A/B/C local reviewed |
| `docs/phase_brief/phase64-brief.md` | Closed R64.1 hygiene in active Phase 64 brief | A/B/C local reviewed |
| `docs/phase_brief/phase65-brief.md` | Added Candidate Registry approval brief with blocked scope | A/B/C local reviewed |
| `docs/handover/phase64_handover.md` | Updated PM handover for R64.1 and Phase F approval | A/B/C local reviewed |
| `docs/context/*_current.md`, `docs/context/current_context.*` | Refreshed current truth surfaces to Phase 65 approved/not started | A/B/C local reviewed |
| `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md`, `README.md`, `docs/prd.md`, `docs/spec.md` | Added D-354, dependency hygiene note, lesson, and product/spec overlay | A/B/C local reviewed |
| `docs/saw_reports/saw_phase64_1_dependency_git_hygiene_20260509.md` | Published this SAW report | N/A |

## Document Sorting (GitHub-optimized)

1. `README.md`
2. `docs/prd.md`, `docs/spec.md`
3. `docs/architecture/data_source_policy.md`
4. `docs/phase_brief/phase64-brief.md`
5. `docs/phase_brief/phase65-brief.md`
6. `docs/handover/phase64_handover.md`
7. `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md`
8. `docs/context/*_current.md`
9. `docs/saw_reports/saw_phase64_1_dependency_git_hygiene_20260509.md`

Open Risks:
- yfinance quarantine surface is broad and should be migrated gradually behind provider ports.
- Primary S&P sidecar is stale through `2023-11-27`.
- Unrelated dirty files remain in the working tree and are explicitly excluded from milestone commits.

Next action:
- Start Phase F Candidate Registry only: append-only lifecycle, candidate metadata before results, required `trial_count`, required manifest pointer, and dummy lifecycle regression.

SAW Verdict: PASS
ClosurePacket: RoundID=R64_1_DEPENDENCY_GIT_HYGIENE_20260509; ScopeID=R64_1_CLOSEOUT; ChecksTotal=11; ChecksPassed=11; ChecksFailed=0; Verdict=PASS; OpenRisks=yfinance_migration_sidecar_freshness_unrelated_dirty_files_excluded; NextAction=start_phase65_candidate_registry
ClosureValidation: PASS
SAWBlockValidation: PASS
