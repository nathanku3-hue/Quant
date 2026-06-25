# SAW Report - Phase 65 G2 Registered Fixture Candidate

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase65-g2-single-registered-fixture-candidate | Domains: Terminal Zero Research Console, Backend, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope and Ownership

- Scope: Phase G2 single registered synthetic fixture candidate through the quarantined V2 proxy; no real market data, strategy search, ranking, alerts, broker calls, or promotion packets.
- RoundID: `PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509`
- ScopeID: `PH65_G2_LINEAGE_ONLY`
- Primary editor: Codex main agent.
- Implementer pass: Newton.
- Reviewer A (strategy/correctness): Carver.
- Reviewer B (runtime/ops): Carson initial BLOCK, recheck PASS.
- Reviewer C (data/perf): Maxwell initial BLOCK, recheck PASS.
- Ownership check: implementer and reviewers were different agents; PASS.

## Acceptance Checks

- CHK-01: exactly one G2 synthetic fixture candidate can be registered or loaded -> PASS.
- CHK-02: candidate requires `manifest_uri`, `source_quality`, `trial_count = 1`, `code_ref`, `data_snapshot`, and reconciled `data_snapshot.manifest_sha256` -> PASS.
- CHK-03: proxy run uses only the G1 synthetic fixture and deterministic accounting path -> PASS.
- CHK-04: registry note proof is a real hash-linked `candidate.note_added` event for the same candidate/proxy run -> PASS.
- CHK-05: proxy result and lineage report keep `promotion_ready = false`, `canonical_engine_required = true`, and `boundary_verdict = blocked_from_promotion` -> PASS.
- CHK-06: snapshot/report artifacts rebuild from the append-only event log and reconcile report/fixture hashes -> PASS.
- CHK-07: G2 cannot emit a promotion packet, alert, broker action, real-data run, strategy search, or ranking output -> PASS.
- CHK-08: focused G2 tests pass -> PASS.
- CHK-09: G1 synthetic tests still pass -> PASS.
- CHK-10: G0 boundary tests still pass -> PASS.
- CHK-11: Candidate Registry tests still pass -> PASS.
- CHK-12: full regression passes after isolated rerun of a transient Windows microstructure file-lock teardown -> PASS.
- CHK-13: `pip check`, data readiness, minimal validation lab, runtime smoke, compileall, secret scan, and forbidden-path scans pass -> PASS.
- CHK-14: SAW implementer/reviewer passes are reconciled with no unresolved in-scope High/Medium findings -> PASS.

## SE Executor Closure

Scope line: stream=Backend/Data/Docs-Ops; stage=Final Verification; owner=Codex; round_exec_utc=2026-05-09T07:45:00Z

| TaskID | Task | Artifact | Check | Status | EvidenceID |
|---|---|---|---|---|---|
| TSK-01 | Add registered fixture candidate runner | `v2_discovery/fast_sim/run_candidate_proxy.py` | G2 candidate/run tests | PASS | EVD-01 |
| TSK-02 | Add lineage reconstruction helpers | `v2_discovery/fast_sim/lineage.py` | hash-linked event/report tests | PASS | EVD-02 |
| TSK-03 | Add G2 regression suite | `tests/test_v2_proxy_registered_candidate_flow.py` | focused G2 tests | PASS | EVD-03 |
| TSK-04 | Emit report artifacts | `data/registry/g2_single_fixture_candidate_report.json*` | artifact/hash audit | PASS | EVD-04 |
| TSK-05 | Publish policy and SAW docs | `docs/architecture/g2_registered_fixture_candidate_policy.md`, this report | doc review | PASS | EVD-05 |
| TSK-06 | Run final verification matrix | pytest, pip, readiness, validation lab, smoke, scans, SAW validators | final checks | PASS | EVD-06 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05,TSK-06:EVD-06
EvidenceRows: EVD-01|PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509|2026-05-09T07:37:00Z;EVD-02|PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509|2026-05-09T07:38:00Z;EVD-03|PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509|2026-05-09T07:39:00Z;EVD-04|PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509|2026-05-09T07:40:00Z;EVD-05|PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509|2026-05-09T07:42:00Z;EVD-06|PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509|2026-05-09T07:44:00Z
EvidenceValidation: PASS

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Candidate `data_snapshot.manifest_sha256` could be forged while the report computed the real manifest hash separately | Reconcile candidate snapshot manifest hash against `compute_sha256(candidate.manifest_uri)` in validation and lineage; added bogus-hash regression | Codex / Reviewer C | Resolved |
| Medium | Re-running the default G2 command could append duplicate notes for the same fixed proxy run | Reuse an existing hash-linked G2 note for the same candidate/proxy/verdict and added repeated-run regression | Codex / Reviewer B | Resolved |
| Low | yfinance migration and stale sidecar freshness remain inherited risks | Carry forward outside G2 scope | Future Data owner | Open, inherited |

## Scope Split Summary

- in-scope findings/actions:
  - added one registered synthetic fixture candidate runner;
  - added lineage helpers that rebuild proof from the append-only event log;
  - emitted optional lineage report and manifest-backed report artifact;
  - added regressions for forged note IDs, mismatched candidate notes, bogus manifest hashes, non-finite fixture evidence, row/date drift, and repeated-run note reuse.
- inherited out-of-scope findings/actions:
  - yfinance legacy migration remains future debt;
  - primary S&P sidecar freshness remains stale through `2023-11-27`;
  - unrelated pre-existing dirty/untracked files remain parked.

## Reviewer Passes

| Pass | Agent | Verdict | Notes |
|---|---|---|---|
| Implementer | Newton | PASS | Verified one fixture candidate, G1 fixture only, note proof, hash chain, report, and non-promotion |
| Reviewer A | Carver | PASS | No strategy, ranking, edge, alert, broker, or promotion drift |
| Reviewer B | Carson | BLOCK -> PASS | Initial duplicate-note repeated-run risk fixed by note reuse regression |
| Reviewer C | Maxwell | BLOCK -> PASS | Initial bogus manifest-hash acceptance fixed by candidate/report hash reconciliation |

## Verification Evidence

- `.venv\Scripts\python -m pytest tests\test_v2_proxy_registered_candidate_flow.py -q` -> PASS (`19 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py -q` -> PASS (`25 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_invariants.py -q` -> PASS (`9 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_proxy_boundary.py -q` -> PASS (`11 passed`).
- `.venv\Scripts\python -m pytest tests\test_candidate_registry.py -q` -> PASS (`12 passed`).
- `.venv\Scripts\python -m pytest tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` -> PASS (`76 passed`).
- `.venv\Scripts\python -m pytest -q` -> first run ERROR on transient Windows DuckDB file-lock teardown; isolated failing test rerun PASS; full regression rerun PASS with existing skips/warnings.
- `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`).
- `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`; warning `stale_sidecars_max_date_2023-11-27`).
- `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS.
- `.venv\Scripts\python -m compileall v2_discovery\fast_sim tests\test_v2_proxy_registered_candidate_flow.py` -> PASS.
- `.venv\Scripts\python -m v2_discovery.fast_sim.run_candidate_proxy` -> PASS; repeated run kept `event_lines_before=5` and `event_lines_after=5`.
- Artifact audit script -> PASS; required lineage fields present, report manifest hash matches report, fixture hashes match, registry hash chain valid, snapshot note hash matches.
- Runtime smoke on port 8605 -> PASS; `launch.py` stayed alive for 20s.
- G2-scoped secret scan -> PASS; no credential pattern matches.
- Production forbidden-path scan over `run_candidate_proxy.py` and `lineage.py` -> PASS; no forbidden behavior/package terms.
- `scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_se_evidence.py ...` -> PASS (`VALID`).

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `v2_discovery/fast_sim/run_candidate_proxy.py` | Added single registered fixture candidate runner, proxy note reuse, report writing, and candidate manifest-hash reconciliation | B/C PASS |
| `v2_discovery/fast_sim/lineage.py` | Added hash-linked event lookup, note proof validation, and required lineage report generation | A/B/C PASS |
| `tests/test_v2_proxy_registered_candidate_flow.py` | Added required G2 lineage, quarantine, forged-note, repeated-run, non-finite, and manifest reconciliation regressions | A/B/C PASS |
| `docs/architecture/g2_registered_fixture_candidate_policy.md` | Published G2 lineage-only policy and blocked scope | Reviewed |
| `data/registry/candidate_events.jsonl`, `candidate_snapshot.json` | Added/rebuilt one G2 synthetic fixture candidate and one proxy-run note event | C PASS |
| `data/registry/g2_single_fixture_candidate_report.json*` | Published optional lineage report and manifest | C PASS |
| `docs/context/e2e_evidence/phase65_g2_launch_smoke_20260509_*` | Captured G2 runtime smoke evidence | Reviewed |
| `docs/saw_reports/saw_phase65_g2_registered_fixture_candidate_20260509.md` | Published this SAW reconciliation report | N/A |

## Document Sorting (GitHub-optimized)

1. `docs/architecture/g2_registered_fixture_candidate_policy.md`
2. `v2_discovery/fast_sim/lineage.py`
3. `v2_discovery/fast_sim/run_candidate_proxy.py`
4. `tests/test_v2_proxy_registered_candidate_flow.py`
5. `data/registry/candidate_events.jsonl`, `candidate_snapshot.json`, `g2_single_fixture_candidate_report.json*`
6. `docs/context/e2e_evidence/phase65_g2_launch_smoke_20260509_*`
7. `docs/saw_reports/saw_phase65_g2_registered_fixture_candidate_20260509.md`

Open Risks:
- yfinance legacy migration remains future debt.
- Primary S&P sidecar is stale through `2023-11-27`.
- First full-regression run exposed a transient Windows DuckDB teardown lock in an unrelated execution microstructure test; isolated rerun and full rerun passed.

Next action:
- approve Phase G3 hold-or-first canonical replay fixture; do not start strategy search.

SAW Verdict: PASS
ClosurePacket: RoundID=PH65_G2_SINGLE_REGISTERED_FIXTURE_CANDIDATE_20260509; ScopeID=PH65_G2_LINEAGE_ONLY; ChecksTotal=14; ChecksPassed=14; ChecksFailed=0; Verdict=PASS; OpenRisks=yfinance_migration_sidecar_freshness; NextAction=approve_phase_g3_hold_or_first_canonical_replay_fixture
ClosureValidation: PASS
SAWBlockValidation: PASS
