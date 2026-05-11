# Phase 65 G1 Handover

Date: 2026-05-09
Status: COMPLETE - SYNTHETIC MECHANICS ONLY / DATA-INTEGRITY RECONCILED
Audience: PM

## Executive Summary (PM-friendly)

Phase G1 is complete as a deterministic synthetic fast-proxy simulator. It proves the proxy can mechanically consume registered intent plus manifest-backed synthetic fixtures and produce replayable accounting output, while failing closed on non-finite values and manifest drift.

This is still not strategy discovery. G1 uses only prebaked target weights, no real market data, no PEAD logic, no alpha metrics, no alerts, no broker calls, and no promotion packets. Proxy output remains quarantined: `promotion_ready = false` and `canonical_engine_required = true`.

## Delivered Scope vs Deferred Scope

Delivered:
- synthetic fixture manifest with component hashes;
- deterministic prices and target weights fixtures;
- expected ledger, positions, and result golden files;
- cost model;
- fixture loader and real-data path rejection;
- reusable finite/null/domain validators;
- manifest row count, date range, schema, and SHA-256 reconciliation for fixture and golden artifacts;
- fail-closed rejection for missing symbols, sparse weights, `nan`, `+inf`, `-inf`, and non-finite proxy metadata;
- ledger/position accounting;
- simulator wrapper that reuses the G0 boundary and registry note proof;
- focused tests for required G1 invariants.

Deferred:
- real market data;
- strategy signals or strategy search;
- PEAD variants;
- alpha, Sharpe, CAGR, max drawdown, rank, or score;
- alerts;
- broker or Alpaca calls;
- promotion packets;
- MLflow/DVC integration.

## Derivation and Formula Register

See `docs/notes.md` for formulas.

Core formulas:
- `cost_rate = total_cost_bps / 10000`
- `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`
- `turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))`
- `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`
- `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`

## Logic Chain

Input -> Transform -> Decision -> Output

Registered synthetic candidate + synthetic manifest + fixture hashes + prebaked target weights -> fixture validation -> deterministic ledger/position accounting -> G0 boundary validation and registry note append -> non-promotable proxy output.

## Evidence Matrix

| Command / Artifact | Result |
|---|---|
| `data/fixtures/v2_proxy/synthetic_manifest.json` | fixture manifest published |
| `data/fixtures/v2_proxy/expected_ledger.csv` | golden ledger published |
| `data/fixtures/v2_proxy/expected_positions.csv` | golden positions published |
| `data/fixtures/v2_proxy/expected_result.json` | golden result published |
| `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py -q` | PASS, `25 passed` |
| `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_invariants.py -q` | PASS, `9 passed` |
| `.venv\Scripts\python -m pytest tests\test_v2_proxy_boundary.py -q` | PASS, `11 passed` |
| `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` | PASS, `57 passed` |
| `.venv\Scripts\python -m compileall v2_discovery\fast_sim tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py` | PASS |
| `.venv\Scripts\python -m pip check` | PASS, `No broken requirements found.` |
| `.venv\Scripts\python -m pytest -q` | PASS with existing skips/warnings |
| `.venv\Scripts\python launch.py --server.headless true --server.port 8604` | PASS, stayed alive for 20s |
| `.venv\Scripts\python scripts\audit_data_readiness.py` | PASS, `ready_for_paper_alerts = true`, warning `stale_sidecars_max_date_2023-11-27` |
| `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` | PASS |
| `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS |
| Reviewer B recheck | PASS, prior missing-symbol, sparse-weight, and non-finite metadata blockers resolved |
| Reviewer C final recheck | PASS, no remaining High/Medium data-integrity findings |

## Open Risks / Assumptions / Rollback

Open risks:
- yfinance legacy migration remains future debt.
- S&P sidecar freshness remains stale through `2023-11-27`.
- G2 must remain synthetic/no-search unless explicitly widened.

Assumptions:
- Synthetic fixtures are not official market truth.
- G1 output is mechanics evidence only.
- G1 data-integrity failures must be corrected at source; do not repair evidence with `nan_to_num`, `fillna(0)`, or sparse-weight imputation.
- Future promotion still requires V1 `core.engine.run_simulation`.

Rollback:
- Revert only Phase G1 simulator files, tests, fixture files, policy/brief/context docs, handover, and SAW report. Do not revert Phase G0 boundary, Phase F Candidate Registry, D-353 provenance gates, or R64.1 dependency hygiene.

## Next Phase Roadmap

- Option A: approve Phase G2 single registered synthetic fixture candidate through the proxy, still no real data and no strategy search.
- Option B: hold for registry accounting refinements.
- Later only after explicit approval: useful V2 simulation, strategy discovery, paper alerts, promotion packets, or external tracking integrations.

## New Context Packet

## What Was Done
- Closed D-353 A-E provenance + validation gates.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.
- Closed Phase F Candidate Registry as registry-only work.
- Closed Phase G0 V2 Proxy Boundary Harness as boundary-only work.
- Closed Phase G1 deterministic fast-proxy simulator as synthetic mechanics only with fixture hashes, golden outputs, finite-value guards, manifest reconciliation, and quarantine invariants.

## What Is Locked
- No live trading, broker automation, paper alerts, strategy search, real market data proxy runs, promotion packets, or broker calls.
- Candidate Registry is append-only and must require intent metadata before results.
- V2 proxy outputs are not official truth and still require future `core.engine.run_simulation` for promotion.
- G1 accepts only prebaked target weights from manifest-backed synthetic fixtures and fails closed on non-finite values, missing symbols, sparse weights, and manifest metadata drift.

## What Remains
- Decide whether to approve Phase G2 single registered synthetic fixture candidate through the proxy, or hold.
- Do not start strategy search until explicitly approved.

## Next-phase Roadmap
- Phase G2 option: one registered synthetic fixture candidate through the proxy, still no real data/search.
- Alternative: advanced registry accounting, no simulator widening.
- Later only after approval: useful fast simulation, alert packets, promotion packets.

## Immediate First Step
```text
.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q
```

ConfirmationRequired: YES
Prompt: Reply "approve next phase" to start execution.
NextPhaseApproval: PENDING
