# SAW Report - Phase 65 G3 Canonical Replay Fixture

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase65-g3-canonical-replay-fixture | Domains: Terminal Zero Research Console, Backend, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope and Ownership

- Scope: Phase G3 first canonical replay fixture; exactly one registered fixture candidate replayed through V1 and compared with quarantined V2 proxy output on allowed mechanical fields only.
- RoundID: `PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509`
- ScopeID: `PH65_G3_CANONICAL_REPLAY_ONLY`
- Primary editor: Codex main agent.
- Implementer pass: Harvey.
- Reviewer A (strategy/correctness): Kierkegaard.
- Reviewer B (runtime/ops): Hooke.
- Reviewer C (data/perf): Carver.
- Ownership check: implementer and reviewers were different agents; PASS.

## Acceptance Checks

- CHK-01: G3 requires exactly one existing registered fixture candidate -> PASS.
- CHK-02: G3 requires candidate manifest, source quality, data snapshot, and manifest SHA-256 -> PASS.
- CHK-03: G3 rejects Tier 2/non-fixture market-data manifests -> PASS.
- CHK-04: G3 calls `core.engine.run_simulation` through the V1 replay adapter -> PASS.
- CHK-05: G3 compares only allowed mechanical accounting fields -> PASS.
- CHK-06: G3 detects V1/V2 positions, cash, and transaction-cost mismatches -> PASS.
- CHK-07: V2 remains `promotion_ready = false` after a V1/V2 match -> PASS.
- CHK-08: V1/V2 match does not create a promotion packet -> PASS.
- CHK-09: G3 cannot emit alert, broker, Alpaca, OpenClaw, notifier, or external-engine actions -> PASS.
- CHK-10: G3 replay report has required fields, manifest, and hash reconciliation -> PASS.
- CHK-11: Focused G3 tests pass -> PASS.
- CHK-12: G2, G1, G0, and Candidate Registry tests still pass -> PASS.
- CHK-13: Full regression, `pip check`, data readiness, minimal validation lab, smoke, compileall, secret scan, artifact audit, and context validation pass -> PASS.
- CHK-14: SAW implementer/reviewer passes are reconciled with no unresolved in-scope High findings -> PASS.

## SE Executor Closure

Scope line: stream=Backend/Data/Docs-Ops; stage=Final Verification; owner=Codex; round_exec_utc=2026-05-09T08:35:00Z

| TaskID | Task | Artifact | Check | Status | EvidenceID |
|---|---|---|---|---|---|
| TSK-01 | Add G3 replay package | `v2_discovery/replay/*` | focused G3 tests | PASS | EVD-01 |
| TSK-02 | Add G3 regression suite | `tests/test_v2_canonical_replay_fixture.py` | 15 focused tests | PASS | EVD-02 |
| TSK-03 | Emit replay report artifact | `data/registry/g3_canonical_replay_report.json*` | hash/report audit | PASS | EVD-03 |
| TSK-04 | Publish G3 policy/docs | policy, handover, notes, decision log, PRD/spec/README/context | docs-as-code review | PASS | EVD-04 |
| TSK-05 | Run final verification matrix | pytest, pip, readiness, lab, smoke, scans, context validators | final checks | PASS | EVD-05 |
| TSK-06 | Run SAW passes | implementer + reviewers A/B/C | SAW reconciliation | PASS | EVD-06 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05,TSK-06:EVD-06
EvidenceRows: EVD-01|PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509|2026-05-09T08:05:00Z;EVD-02|PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509|2026-05-09T08:06:00Z;EVD-03|PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509|2026-05-09T08:10:00Z;EVD-04|PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509|2026-05-09T08:18:00Z;EVD-05|PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509|2026-05-09T08:25:00Z;EVD-06|PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509|2026-05-09T08:34:00Z
EvidenceValidation: PASS

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | Bare/default G3 execution refreshes `data/registry/g3_canonical_replay_report.json*`; repeated manual runs can update artifact timestamps/hashes even though writes are atomic | Documented as operational hygiene; tests use `report_path=None` when no artifact write is intended | Future Ops | Advisory |
| Low | Same-phase context builder initially selected older G1 handover after G3 phase-brief updates | Published `docs/handover/phase65_g3_handover.md` and rebuilt/validated context packets | Codex | Resolved |
| Low | Optional candidate selector initially hid duplicate fixture-candidate state before global count check | Enforced global one-fixture invariant before candidate-ID filter and added focused regression | Codex | Resolved |
| Low | Lower-level G2/proxy errors could bubble without G3 error type | Wrapped proxy boundary failures as `G3ReplayError` | Codex | Resolved |
| Low | yfinance migration and stale sidecar freshness remain inherited risks | Carry forward outside G3 scope | Future Data owner | Open, inherited |

## Scope Split Summary

- in-scope findings/actions:
  - added G3 replay package and allowed-field comparison;
  - added G3 focused tests for registration, manifest/source gates, V1 call proof, mismatch detection, non-promotion, forbidden paths, and manifest/hash report proof;
  - emitted G3 replay report and manifest;
  - refreshed G3 policy, handover, notes, decision log, PRD/spec/README, and current truth surfaces;
  - fixed G3 duplicate-candidate filtering and error normalization before closeout.
- inherited out-of-scope findings/actions:
  - yfinance legacy migration remains future debt;
  - primary S&P sidecar freshness remains stale through `2023-11-27`;
  - G4 must stay readiness-only unless explicitly approved.

## Reviewer Passes

| Pass | Agent | Verdict | Notes |
|---|---|---|---|
| Implementer | Harvey | PASS | Validated G3 requirements, report hashes, V1 call, allowed fields, and no forbidden paths |
| Reviewer A | Kierkegaard | PASS | No strategy-search, ranking, performance metric, promotion, alert, or trading-permission drift |
| Reviewer B | Hooke | PASS | Atomic report writes and no broker/operational path; one Low artifact-refresh advisory |
| Reviewer C | Carver | PASS | Manifest/hash/source-quality reconciliation, non-finite fail-closed behavior, allowed-field comparison, and performance scope pass |

## Verification Evidence

- `.venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py -q` -> PASS (`15 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_proxy_registered_candidate_flow.py -q` -> PASS (`19 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py -q` -> PASS (`25 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_invariants.py -q` -> PASS (`9 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_proxy_boundary.py -q` -> PASS (`11 passed`).
- `.venv\Scripts\python -m pytest tests\test_candidate_registry.py -q` -> PASS (`12 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` -> PASS (`91 passed`).
- `.venv\Scripts\python -m pytest -q` -> PASS with existing skips/warnings.
- `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`).
- `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`; warning `stale_sidecars_max_date_2023-11-27`).
- `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS.
- `.venv\Scripts\python -m compileall v2_discovery\replay tests\test_v2_canonical_replay_fixture.py` -> PASS.
- Streamlit smoke on port `8610` -> PASS; listener alive after 20s and stopped.
- G3 forbidden-path scan over `v2_discovery\replay` -> PASS; no forbidden behavior/package terms.
- G3 secret scan -> PASS; no credential pattern matches.
- Artifact audit -> PASS; required fields present, report manifest hash matches report, fixture manifest hash matches report.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` -> PASS (`10 passed`).

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `v2_discovery/replay/__init__.py` | Published G3 replay API exports | A/B/C PASS |
| `v2_discovery/replay/canonical_replay.py` | Added one-candidate validation, V1 replay adapter, V2 mechanical output binding, report builder, and artifact writer | A/B/C PASS |
| `v2_discovery/replay/comparison.py` | Added allowed mechanical field comparison and mismatch reporting | A/C PASS |
| `v2_discovery/replay/schemas.py` | Added G3 replay/result schema objects and non-promotion guards | A/B/C PASS |
| `tests/test_v2_canonical_replay_fixture.py` | Added G3 required invariant tests | A/B/C PASS |
| `docs/architecture/g3_canonical_replay_fixture_policy.md` | Published G3 replay policy and blocked scope | Reviewed |
| `docs/handover/phase65_g3_handover.md` | Published G3 handover and fresh context packet source | Reviewed |
| `data/registry/g3_canonical_replay_report.json*` | Published optional G3 replay report and manifest | C PASS |
| `docs/phase_brief/phase65-brief.md`, `docs/decision log.md`, `docs/notes.md`, `docs/prd.md`, `docs/spec.md`, `README.md` | Updated docs-as-code truth for G2/G3 and next G4 hold/readiness decision | Reviewed |
| `docs/context/*_current.md`, `docs/context/current_context.*` | Refreshed planner, bridge, impact, done checklist, stream, alignment, observability, and current context surfaces | Reviewed |
| `docs/context/e2e_evidence/phase65_g3_*_20260509_*` | Captured G3 smoke/status evidence | Reviewed |
| `docs/saw_reports/saw_phase65_g3_canonical_replay_fixture_20260509.md` | Published this SAW reconciliation report | N/A |

## Document Sorting (GitHub-optimized)

1. `docs/architecture/g3_canonical_replay_fixture_policy.md`
2. `v2_discovery/replay/schemas.py`
3. `v2_discovery/replay/comparison.py`
4. `v2_discovery/replay/canonical_replay.py`
5. `tests/test_v2_canonical_replay_fixture.py`
6. `data/registry/g3_canonical_replay_report.json*`
7. `docs/handover/phase65_g3_handover.md`
8. `docs/context/*_current.md`, `docs/context/current_context.*`
9. `docs/saw_reports/saw_phase65_g3_canonical_replay_fixture_20260509.md`

Open Risks:
- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Default G3 report generation refreshes report artifacts; use `report_path=None` for non-artifact tests or dry reads.

Next action:
- approve Phase G4 hold-or-first real canonical dataset readiness fixture; do not start strategy search.

SAW Verdict: PASS
ClosurePacket: RoundID=PH65_G3_CANONICAL_REPLAY_FIXTURE_20260509; ScopeID=PH65_G3_CANONICAL_REPLAY_ONLY; ChecksTotal=14; ChecksPassed=14; ChecksFailed=0; Verdict=PASS; OpenRisks=yfinance_migration_sidecar_freshness; NextAction=approve_phase_g4_hold_or_first_real_canonical_dataset_readiness
ClosureValidation: PASS
SAWBlockValidation: PASS
