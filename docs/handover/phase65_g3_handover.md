# Phase 65 G3 Handover

Status: CLOSED - TRUTH-ALIGNMENT FIXTURE ONLY
Date: 2026-05-09
Audience: PM / Architecture Office

## Executive Summary

Phase G3 proved the first canonical replay fixture. One existing registered G2 fixture candidate now replays through the official V1 engine call path, `core.engine.run_simulation`, and compares against the quarantined V2 proxy output only on allowed mechanical accounting fields.

The match is not a trading signal, promotion packet, ranking, alert, or research result. V2 remains blocked with `promotion_ready = false`, `canonical_engine_required = true`, and `boundary_verdict = "v2_blocked_from_promotion"`.

## Delivered Scope

- Added `v2_discovery/replay/` for G3 replay schemas, V1 replay adapter, and allowed-field comparison.
- Added `tests/test_v2_canonical_replay_fixture.py`.
- Published `docs/architecture/g3_canonical_replay_fixture_policy.md`.
- Emitted `data/registry/g3_canonical_replay_report.json` and `.manifest.json`.

## Deferred Scope

- No strategy search.
- No real market data expansion.
- No candidate ranking.
- No alerts or broker calls.
- No promotion packet.
- No MLflow, DVC, OpenClaw, or external engine integration.

## Evidence Matrix

```text
.venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py -q -> PASS, 15 passed
.venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q -> PASS, 91 passed
.venv\Scripts\python -m pytest -q -> PASS
.venv\Scripts\python -m pip check -> PASS
.venv\Scripts\python scripts\audit_data_readiness.py -> PASS, ready_for_paper_alerts=true, warning stale_sidecars_max_date_2023-11-27
.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent -> PASS
Streamlit smoke on port 8610 -> PASS, listener alive after 20s and stopped
```

## Open Risks

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.

## Rollback

Revert only the G3 replay package, focused test, G3 policy/report/handover/SAW artifacts, and G3 context/doc updates. Do not revert G2, G1, G0, Candidate Registry, D-353, or R64.1.

## New Context Packet

## What Was Done
- Closed D-353 A-E provenance + validation gates.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.
- Closed Phase F Candidate Registry, Phase G0 proxy boundary, Phase G1 synthetic mechanics, and Phase G2 single registered fixture candidate lineage.
- Closed Phase G3 canonical replay fixture: one registered fixture candidate calls `core.engine.run_simulation`, compares only mechanical accounting fields, and keeps V2 blocked from promotion.

## What Is Locked
- No live trading, broker automation, paper alerts, strategy search, candidate ranking, promotion packets, or broker calls.
- Candidate Registry is append-only and must require intent metadata before results.
- V2 proxy outputs are not official truth and cannot become `promotion_ready = true`.
- G3 V1/V2 matches are replay/inventory evidence only, not trading permission.

## What Is Next
- Decide whether to hold or approve Phase G4 first real canonical dataset readiness fixture.
- Do not start strategy search, alerts, broker calls, or promotion packets.

## First Command
```text
.venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q
```

## Next Todos
- Choose Phase G4 first real canonical dataset readiness fixture or hold.
- Keep G4 readiness separate from alpha search and candidate ranking.
- Preserve yfinance migration and stale-sidecar freshness as carried risks.
