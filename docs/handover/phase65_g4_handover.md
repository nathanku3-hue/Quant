# Phase 65 G4 Handover - Real Canonical Dataset Readiness Fixture

Status: CLOSED - READINESS ONLY
Date: 2026-05-09
Authority: D-361 Phase G4 first real canonical dataset readiness fixture

## Executive Summary

G4 proved that Terminal Zero can touch one tiny real Tier 0 canonical daily price slice,
reconcile it against a manifest, run readiness gates, and emit a readiness-only report.
The result is `ready_for_g5 = true` for dataset readiness only. No strategy logic, alpha,
ranking, alerting, broker action, V2 real-data proxy, or promotion packet was introduced.

## Delivered Scope

- Added `v2_discovery/readiness/` with canonical slice loading, manifest reconciliation,
  readiness-report construction, and fail-closed schema/error objects.
- Added a tiny canonical fixture derived from `data/processed/prices_tri.parquet`:
  `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet`.
- Added a dedicated Tier 0 canonical manifest for the tiny slice.
- Added focused G4 tests for source-tier rejection, manifest drift, finite/domain/key/date
  checks, stale sidecar failure, report field hygiene, registry non-mutation, and no
  alert/broker action.
- Added optional report artifacts under `data/registry/`.
- Published `docs/architecture/g4_real_canonical_readiness_policy.md`.

## Deferred Scope

- No strategy search.
- No alpha, Sharpe, CAGR, drawdown, score, rank, PnL, or performance metrics.
- No candidate ranking, alerts, broker calls, Alpaca, OpenClaw, notifier, promotion packet,
  MLflow, DVC, or external engine.
- No V2 proxy run on real data.
- No S&P sidecar freshness repair except the stale-sidecar negative test.

## Evidence Matrix

```text
G4 focused tests: .venv\Scripts\python -m pytest tests\test_g4_real_canonical_readiness_fixture.py -q -> PASS (18 passed)
G3 tests: .venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py -q -> PASS (15 passed)
G2 tests: .venv\Scripts\python -m pytest tests\test_v2_proxy_registered_candidate_flow.py -q -> PASS (19 passed)
G1 tests: .venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py -q and tests\test_v2_fast_proxy_invariants.py -q -> PASS (25 + 9 passed)
G0 tests: .venv\Scripts\python -m pytest tests\test_v2_proxy_boundary.py -q -> PASS (11 passed)
Candidate Registry tests: .venv\Scripts\python -m pytest tests\test_candidate_registry.py -q -> PASS (12 passed)
Combined G/F matrix: .venv\Scripts\python -m pytest tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q -> PASS (109 passed)
Full regression: .venv\Scripts\python -m pytest -q -> PASS
pip check: .venv\Scripts\python -m pip check -> PASS
Data readiness: .venv\Scripts\python scripts\audit_data_readiness.py -> PASS, warning stale_sidecars_max_date_2023-11-27
Minimal validation lab: .venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent -> PASS
Compileall: .venv\Scripts\python -m compileall v2_discovery\readiness tests\test_g4_real_canonical_readiness_fixture.py -> PASS
Runtime smoke: .venv\Scripts\python launch.py --server.headless true --server.port 8620 -> PASS, listener alive after 20s and stopped
Forbidden-path scan: rg forbidden strategy/performance/broker terms v2_discovery/readiness -> PASS, no matches
Secret scan: scoped regex scan over G4 code/test/doc/report surfaces -> PASS
Artifact hash audit: fixture/report manifest hashes, row_count, symbol_count, date_range, no-performance report fields -> PASS
Context packet validation: .venv\Scripts\python scripts\build_context_packet.py --validate -> PASS
SAW report: docs/saw_reports/saw_phase65_g4_real_canonical_readiness_20260509.md -> PASS after validation
Readiness report: data/registry/g4_real_canonical_readiness_report.json
Readiness manifest: data/registry/g4_real_canonical_readiness_report.json.manifest.json
Policy: docs/architecture/g4_real_canonical_readiness_policy.md
```

## Open Risks / Assumptions / Rollback

- Open risks: yfinance migration remains future debt; primary S&P sidecar freshness remains stale through `2023-11-27`.
- Assumptions: G5, if approved, remains a single canonical replay with no alpha search.
- Rollback: revert only G4 readiness package, focused test, G4 fixture/report artifacts, policy, handover, SAW report, and G4 documentation/context updates; do not revert G3/G2/G1/G0/F/D-353/R64.1.

## New Context Packet

## What Was Done

- Preserved D-353 provenance gates and R64.1 dependency hygiene as closed prerequisites.
- Closed Phase G4 first real canonical dataset readiness fixture.
- Added `v2_discovery/readiness/` for readiness-only canonical slice validation.
- Added a tiny Tier 0 `prices_tri` fixture with 123 rows, 3 symbols, daily bars, and a dedicated manifest.
- Reconciled manifest SHA-256, row count, schema, date range, finite numeric values, duplicate keys, date monotonicity, price domain, return domain, and freshness.
- Published `data/registry/g4_real_canonical_readiness_report.json` with `ready_for_g5 = true` and no performance metrics.

## What Is Locked

- G4 is readiness-only and not strategy evidence.
- No strategy search, V2 discovery, alpha, ranking, alerts, broker calls, promotion packets, or real-data proxy runs are authorized.
- yfinance, public web, OpenBB, Alpaca, and Tier 2 artifacts are rejected for G4 readiness.
- Sidecars are not required for the passing G4 price slice; stale sidecars block readiness only when explicitly required.

## What Is Next

- Decide whether to approve Phase G5: single canonical replay, no alpha, or hold.
- Carry yfinance migration and stale S&P sidecar freshness as open risks.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q
```

## Next Todos

- Prepare only the G5 decision: single canonical replay, no alpha, or hold.
- Keep candidate rankings, alerts, broker calls, and promotion packets blocked.
- Preserve G4 default execution with `report_path=None` unless artifact refresh is explicitly intended.
