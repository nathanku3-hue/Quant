# SAW Report - Phase 65 G6 V1/V2 Real-Slice Mechanical Comparison

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase65-g6-v1-v2-real-slice-mechanical | Domains: Terminal Zero Research Console, Backend, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope and Ownership

- Scope: Phase G6 V1/V2 real-slice mechanical comparison, no alpha; one tiny Tier 0 `prices_tri` daily-bar slice, predeclared neutral weights, V1 official replay versus V2 proxy mechanics, mechanical comparison report only.
- RoundID: `PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509`
- ScopeID: `PH65_G6_MECHANICAL_COMPARISON_ONLY`
- Primary editor: Codex main agent.
- Implementer pass: Averroes.
- Reviewer A (strategy/correctness): Socrates.
- Reviewer B (runtime/ops): Cicero.
- Reviewer C (data/perf): Wegener.
- Ownership check: implementer and reviewers were different agents; PASS.

## Acceptance Checks

- CHK-01: G6 requires Tier 0 canonical source evidence through the G4/G5 loaders -> PASS.
- CHK-02: G6 rejects yfinance, OpenBB, Tier 2, Alpaca, and operational artifacts before comparison -> PASS.
- CHK-03: G6 requires a manifest and reconciles hash, row count, schema, and date range -> PASS.
- CHK-04: G6 validates finite numeric values before replay/comparison -> PASS.
- CHK-05: G6 uses predeclared neutral fixture weights only -> PASS.
- CHK-06: G6 calls official V1 `core.engine.run_simulation` through the G5 replay path -> PASS.
- CHK-07: G6 calls V2 proxy ledger mechanics separately -> PASS.
- CHK-08: G6 compares approved mechanical fields only -> PASS.
- CHK-09: G6 keeps `promotion_ready=false` and `v2_promotion_ready=false` even on exact match -> PASS.
- CHK-10: G6 emits no alpha, performance, ranking, signal, buy/sell, alert, broker, paper-trade, or promotion fields -> PASS.
- CHK-11: Default G6 execution uses `report_path=None`; artifact writes are explicit only -> PASS.
- CHK-12: Focused G6 tests and G5/G4/G3/G2/G1/G0/Candidate Registry matrix pass -> PASS.
- CHK-13: Full regression, `pip check`, data readiness, minimal validation lab, compileall, runtime smoke, forbidden-path scan, secret scan, artifact audit, and context validation pass -> PASS.
- CHK-14: SAW implementer/reviewer passes are reconciled with no unresolved in-scope High/Medium findings -> PASS.
- CHK-15: Closure packet and SAW report validators pass -> PASS.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Reviewer B found G6 closeout docs and current truth surfaces incomplete, blocking phase-close PASS | Published G6 policy and SAW report, refreshed planner/bridge/impact/done/alignment/observability/current-context surfaces, and attached closeout evidence | Codex | Resolved |
| Medium | Full regression found the G6 bridge dropped the required `docs/phase_brief/phase64-brief.md` hygiene anchor | Restored the phase64 brief evidence anchor and reran the hygiene test plus full regression | Codex | Resolved |
| Low | yfinance migration remains future debt | Carry outside G6 comparison scope | Future Data owner | Open, inherited |
| Low | Primary S&P sidecar freshness remains stale through `2023-11-27` | Keep as paper-alert warning; do not repair in G6 | Future Data owner | Open, inherited |

## Scope Split Summary

- in-scope findings/actions:
  - added G6 V1/V2 real-slice comparison package and mechanical report validator/writer;
  - reused the G4 tiny real Tier 0 `prices_tri` fixture and the G5 predeclared equal weights;
  - invoked V1 official replay and V2 proxy ledger mechanics separately;
  - compared only approved mechanical fields and kept V2 non-promotable;
  - emitted optional G6 report and manifest only through explicit `report_path`;
  - added focused tests for all requested G6 invariants;
  - refreshed G6 policy, handover, phase brief, context surfaces, and report evidence;
  - resolved Reviewer B's closeout blocker and the bridge hygiene regression before SAW close.
- inherited out-of-scope findings/actions:
  - yfinance migration remains future debt;
  - primary S&P sidecar freshness remains stale through `2023-11-27`;
  - G7 must not convert mechanical equivalence into search, rankings, alerts, broker calls, paper trading, or promotion packets without explicit approval.

## Reviewer Passes

| Pass | Agent | Verdict | Notes |
|---|---|---|---|
| Implementer | Averroes | PASS | Verified G6 canonical gates, V1/V2 calls, approved comparison fields, non-promotion, `report_path=None`, and focused tests |
| Reviewer A | Socrates | PASS | Confirmed mechanical-only boundary; no strategy search, alpha/performance/ranking output, buy/sell decisions, or promotion verdict |
| Reviewer B | Cicero | PASS after reconciliation | Initial BLOCK on incomplete docs/current truth/SAW closeout; resolved by publishing missing docs and running closeout evidence |
| Reviewer C | Wegener | PASS | Confirmed fixture/report hashes, row count, schema/date range, finite values, strict V1/V2 table equality, and no forbidden report fields |

## SE Executor Closure

Scope line: stream=Backend/Data/Docs-Ops; stage=Final Verification; owner=Codex; round_exec_utc=2026-05-09T10:08:00Z.

| task_id | task | artifact | check | status | evidence_id |
|---|---|---|---|---|---|
| TSK-01 | Implement V1/V2 real-slice mechanical comparison | `v2_discovery/replay/real_slice_v1_v2_comparison.py`, `v2_discovery/replay/mechanical_comparison_report.py` | Focused G6 tests | PASS | EVD-01 |
| TSK-02 | Preserve no-alpha/no-promotion boundary | `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`, G6 forbidden scan | Focused tests plus forbidden-path scan | PASS | EVD-02 |
| TSK-03 | Verify data/provenance and artifact integrity | `data/registry/g6_v1_v2_real_slice_mechanical_report.json*` | Artifact audit and Reviewer C checks | PASS | EVD-03 |
| TSK-04 | Complete operational closeout gates | `docs/context/e2e_evidence/phase65_g6_launch_smoke_20260509_*` | matrix, full regression, `pip check`, data readiness, validation lab, compileall, runtime smoke, secret scan | PASS | EVD-04 |
| TSK-05 | Refresh docs/context and close SAW | `docs/handover/phase65_g6_handover.md`, `docs/context/*.md`, this SAW report | Context validation, SAW validation, closure validation | PASS | EVD-05 |

Verification evidence:

| evidence_id | command | result | notes | evidence_utc | run_id |
|---|---|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py -q` | PASS (`20 passed`) | G6 focused invariant matrix | 2026-05-09T09:51:00Z | PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509 |
| EVD-02 | G6 implementation forbidden-path scan | PASS | No forbidden behavior/package/performance/promotion tokens in implementation files | 2026-05-09T10:01:00Z | PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509 |
| EVD-03 | G6 artifact hash audit | PASS | Report hash, fixture manifest hash, 123 positions per side, 41 ledger rows per side, zero mismatches | 2026-05-09T09:55:00Z | PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509 |
| EVD-04 | matrix/full regression/operational checks | PASS | `147 passed` matrix, full regression, data readiness warning carried, runtime smoke on port `8622` | 2026-05-09T10:08:00Z | PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509 |
| EVD-05 | Context/SAW/closure validators | PASS | Context packet rebuilt; validator outputs recorded below | 2026-05-09T10:08:30Z | PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05
EvidenceRows: EVD-01|PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509|2026-05-09T09:51:00Z;EVD-02|PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509|2026-05-09T10:01:00Z;EVD-03|PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509|2026-05-09T09:55:00Z;EVD-04|PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509|2026-05-09T10:08:00Z;EVD-05|PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509|2026-05-09T10:08:30Z
EvidenceValidation: PASS

## Verification Evidence

- `.venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py -q` -> PASS (`20 passed`).
- `.venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` -> PASS (`147 passed`).
- `.venv\Scripts\python -m pytest -q` -> PASS with existing skips/warnings.
- `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`).
- `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`; warning `stale_sidecars_max_date_2023-11-27`).
- `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS.
- `.venv\Scripts\python -m compileall v2_discovery\replay\real_slice_v1_v2_comparison.py v2_discovery\replay\mechanical_comparison_report.py tests\test_g6_v1_v2_real_slice_mechanical_comparison.py` -> PASS.
- Streamlit smoke through `.venv\Scripts\python launch.py --server.headless true --server.port 8622` -> PASS; listener alive after 20 seconds and stopped.
- G6 forbidden-path scan over `v2_discovery/replay/real_slice_v1_v2_comparison.py` and `v2_discovery/replay/mechanical_comparison_report.py` -> PASS; no forbidden behavior/package/performance/promotion tokens.
- G6 secret scan over G6 code/test/doc/report surfaces -> PASS.
- Artifact hash audit -> PASS; report manifest hash, fixture manifest hash, row count, symbol count, V1/V2 positions, V1/V2 ledger series, canonical source, and no-performance fields reconciled.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `v2_discovery/replay/__init__.py` | Published G6 comparison API exports | A/B/C PASS |
| `v2_discovery/replay/real_slice_v1_v2_comparison.py` | Added V1/V2 real canonical mechanical comparison and strict field comparison | A/B/C PASS |
| `v2_discovery/replay/mechanical_comparison_report.py` | Added report schema validation and explicit atomic report/manifest writing | A/B/C PASS |
| `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py` | Added G6 required invariant tests and strict V1/V2 DataFrame equality checks | A/B/C PASS |
| `data/registry/g6_v1_v2_real_slice_mechanical_report.json*` | Published optional G6 mechanical comparison report and manifest | B/C PASS |
| `docs/architecture/g6_v1_v2_real_slice_mechanical_policy.md` | Published G6 comparison-only policy and blocked scope | Reviewed |
| `docs/handover/phase65_g6_handover.md` | Published G6 handover and evidence matrix | Reviewed |
| `docs/phase_brief/phase65-brief.md`, `docs/context/done_checklist_current.md`, `docs/context/impact_packet_current.md` | Refreshed G6 closeout evidence and SAW visibility | Reviewed |
| `docs/context/e2e_evidence/phase65_g6_launch_smoke_20260509_*` | Captured G6 runtime smoke evidence | Reviewed |
| `docs/saw_reports/saw_phase65_g6_v1_v2_real_slice_mechanical_20260509.md` | Published this SAW reconciliation report | N/A |

## Document Sorting (GitHub-optimized)

1. `docs/architecture/g6_v1_v2_real_slice_mechanical_policy.md`
2. `v2_discovery/replay/real_slice_v1_v2_comparison.py`
3. `v2_discovery/replay/mechanical_comparison_report.py`
4. `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`
5. `data/registry/g6_v1_v2_real_slice_mechanical_report.json*`
6. `docs/handover/phase65_g6_handover.md`
7. `docs/context/*_current.md`, `docs/context/current_context.*`
8. `docs/saw_reports/saw_phase65_g6_v1_v2_real_slice_mechanical_20260509.md`

PhaseEndValidation: PASS
PhaseEndChecks: CHK-PH-01 PASS (full regression), CHK-PH-02 PASS (runtime smoke), CHK-PH-03 PASS (focused G6 comparison run + artifact audit), CHK-PH-04 PASS (atomic write path + manifest/hash/row-count sanity), CHK-PH-05 PASS (brief/handover/decision log/notes/lessonss/context docs), CHK-PH-06 PASS (context validation), CHK-PH-07 ADVISORY (dirty worktree contains intentional milestone files plus pre-existing unrelated files; no destructive cleanup)
HandoverDoc: `docs/handover/phase65_g6_handover.md`
HandoverAudience: PM
ContextPacketReady: PASS
ConfirmationRequired: YES

Open Risks:
- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Next phase must be an explicit G7-or-hold decision; no strategy search, promotion, alert, broker path, or paper trading can start from G6 comparison.

Next action:
- approve Phase G7 first controlled candidate-family definition, no search, or hold.

SAW Verdict: PASS
ClosurePacket: RoundID=PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_20260509; ScopeID=PH65_G6_MECHANICAL_COMPARISON_ONLY; ChecksTotal=15; ChecksPassed=15; ChecksFailed=0; Verdict=PASS; OpenRisks=yfinance_migration_sidecar_freshness; NextAction=approve_phase_g7_hold_or_first_controlled_candidate_family_definition_no_search
ClosureValidation: PASS
SAWBlockValidation: PASS
