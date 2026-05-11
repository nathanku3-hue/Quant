# Phase 65 G5 Handover - Single Canonical Replay, No Alpha

Status: CLOSED - V1 CANONICAL MECHANICAL REPLAY ONLY
Date: 2026-05-09
Authority: D-362 Phase G5 single canonical replay, no alpha

## Executive Summary

G5 proved that Terminal Zero can run one tiny real Tier 0 canonical price slice through the official V1 path, `core.engine.run_simulation`, with predeclared neutral weights only. The output is a manifest-backed mechanical replay report. No V2 proxy, strategy search, alpha metric, ranking, alert, broker call, or promotion packet was introduced.

## Delivered Scope

- Added `v2_discovery/replay/canonical_real_replay.py` for V1-only real-slice replay.
- Added `v2_discovery/replay/canonical_replay_report.py` for mechanical report validation and explicit artifact writing.
- Added focused G5 tests covering canonical source gates, manifest drift, finite data, predeclared weights, V1 engine call proof, V2 non-use, no performance fields, no alerts/broker calls, no promotion, and no default artifact refresh.
- Published `data/registry/g5_single_canonical_replay_report.json` and its manifest through an explicit report path.
- Published `docs/architecture/g5_single_canonical_replay_no_alpha_policy.md`.

## Deferred Scope

- No V2 proxy run on real canonical data.
- No V1/V2 real-slice comparison; this is a possible G6 decision only.
- No alpha, Sharpe, CAGR, drawdown, score, rank, buy/sell decision, paper alert, broker call, Alpaca, OpenClaw, notifier, promotion packet, MLflow, DVC, vectorbt, qlib, or external engine.

## Derivation and Formula Register

```text
target_weight_{t,s} = 1 / count_symbols_t
engine_returns_{t,s} = total_ret_{t,s}
cost_rate = total_cost_bps / 10000
turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))
transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate
target_value_{t,s} = target_weight_{t,s} * equity_after_cost_t
cash_t = equity_after_cost_t - sum_s(target_value_{t,s})
gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t
net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t
```

Source path: `v2_discovery/replay/canonical_real_replay.py`.

## Logic Chain

```text
G4 canonical slice + manifest -> load/reconcile readiness gate -> predeclared equal weights -> core.engine.run_simulation -> mechanical ledger/report -> no promotion/alert/broker/V2
```

## Evidence Matrix

```text
G5 focused tests: .venv\Scripts\python -m pytest tests\test_g5_single_canonical_replay_no_alpha.py -q -> PASS (18 passed)
G5+G4 focused tests: .venv\Scripts\python -m pytest tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py -q -> PASS (36 passed)
G5/G4/G3/G2/G1/G0/F matrix: .venv\Scripts\python -m pytest tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q -> PASS (127 passed)
Full regression: .venv\Scripts\python -m pytest -q -> PASS
pip check: .venv\Scripts\python -m pip check -> PASS
Data readiness: .venv\Scripts\python scripts\audit_data_readiness.py -> PASS (ready_for_paper_alerts=true; warning stale_sidecars_max_date_2023-11-27)
Minimal validation lab: .venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent -> PASS
Compileall: .venv\Scripts\python -m compileall v2_discovery\replay\canonical_real_replay.py v2_discovery\replay\canonical_replay_report.py tests\test_g5_single_canonical_replay_no_alpha.py -> PASS
Runtime smoke: .venv\Scripts\python launch.py --server.headless true --server.port 8621 -> PASS; listener alive after 20 seconds and stopped
G5 artifact audit: data/registry/g5_single_canonical_replay_report.json* -> PASS
G5 forbidden-path scan: v2_discovery/replay/canonical_real_replay.py and canonical_replay_report.py -> PASS
G5 secret scan: G5 code/test/doc/report surfaces -> PASS
Context packet: .venv\Scripts\python scripts\build_context_packet.py --validate -> PASS
SAW validation: .venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase65_g5_single_canonical_replay_no_alpha_20260509.md -> PASS
Closure packet validation: .venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "<G5 ClosurePacket>" --require-open-risks-when-block --require-next-action-when-block -> PASS
Policy: docs/architecture/g5_single_canonical_replay_no_alpha_policy.md
```

## Open Risks / Assumptions / Rollback

- Open risks: yfinance migration remains future debt; primary S&P sidecar freshness remains stale through `2023-11-27`.
- Assumptions: G6, if approved, is V1 vs V2 real-slice mechanical comparison only and still no alpha.
- Rollback: revert only G5 replay package additions, focused test, G5 report artifacts, policy, handover, SAW report, and G5 documentation/context updates; do not revert G4/G3/G2/G1/G0/F/D-353/R64.1.

## New Context Packet

## What Was Done

- Preserved D-353 provenance gates, R64.1 dependency hygiene, Candidate Registry, G0/G1/G2/G3, and G4 readiness as closed prerequisites.
- Closed Phase G5 single canonical replay, no alpha.
- Reused the G4 Tier 0 `prices_tri` tiny canonical slice.
- Built predeclared neutral equal weights and called `core.engine.run_simulation` once.
- Emitted `data/registry/g5_single_canonical_replay_report.json` with mechanical replay fields only.
- Kept `promotion_ready = false`, `alerts_emitted = false`, and `broker_calls = false`.

## What Is Locked

- G5 is V1 canonical mechanical replay only and not strategy evidence.
- No V2 proxy run on real canonical data is authorized in G5.
- No strategy search, alpha, ranking, alerts, broker calls, promotion packets, or trading permission is authorized.
- G5 default execution must keep `report_path=None`; report artifacts refresh only when explicitly requested.

## What Is Next

- Decide whether to approve Phase G6: V1 vs V2 real-slice mechanical comparison, no alpha, or hold.
- Carry yfinance migration and stale S&P sidecar freshness as open risks.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q
```

## Next Todos

- Prepare only the G6 decision: V1 vs V2 real-slice mechanical comparison, no alpha, or hold.
- Keep candidate rankings, alerts, broker calls, V2 real-data proxy comparison, and promotion packets blocked until explicitly approved.
- Preserve G5 default execution with `report_path=None` unless artifact refresh is explicitly intended.
