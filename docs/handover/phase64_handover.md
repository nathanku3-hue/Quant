# Phase 64 Handover

Date: 2026-05-09
Status: COMPLETE - PROVENANCE + VALIDATION A-E + R64.1 HYGIENE
Audience: PM

## Executive Summary (PM-friendly)

Provenance is now an executable gate. The repo can distinguish canonical research data, operational Alpaca paper-market data, quarantined yfinance discovery data, and rejected sources in code rather than prose.

The local lake passed the daily US-equity paper-alert readiness audit, and an existing PEAD return stream passed the minimal validation lab with manifest-backed evidence. Live Alpaca trading remains blocked.

R64.1 dependency hygiene is also closed: the main environment now uses `alpaca-py==0.43.4`, the legacy `alpaca-trade-api` package is out of the main dependency set, and `pip check` passes.

## Delivered Scope vs Deferred Scope

Delivered:
- source policy;
- manifest schema and fail-closed checks;
- provider ports for Yahoo and Alpaca;
- yfinance quarantine allowlist;
- data readiness audit;
- minimal validation lab;
- Alpaca quote feed metadata tags;
- additional signed-decision gate for non-paper Alpaca endpoint initialization;
- Alpaca SDK hygiene migrated to `alpaca-py==0.43.4` without expanding Alpaca functionality.

Deferred:
- live Alpaca orders;
- broker automation;
- candidate registry;
- paper alert packet;
- paper portfolio loop;
- advanced anti-overfit gates;
- notifier integration.

## Derivation and Formula Register

See `docs/notes.md` for formula details.

Core formulas:
- `ready_for_paper_alerts = (blockers == [])`
- `sharpe_annualized = mean_daily_return / daily_volatility * sqrt(252)`
- `cumulative_return = prod(1 + net_ret_t) - 1`
- `drawdown_t = equity_t / rolling_peak_t - 1`
- `permutation_p = (count(null_mean >= observed_mean) + 1) / (n_permutations + 1)`
- `bootstrap_pass = lower_mean_ci > 0`

## Logic Chain

Input -> Transform -> Decision -> Output

Local parquet/CSV evidence -> manifest and source-quality validation -> canonical-only validation and Tier 2 promotion block -> readiness and validation reports with manifests.

## Evidence Matrix

| Command / Artifact | Result |
|---|---|
| `.venv\Scripts\python -m pytest tests/test_provenance_policy.py tests/test_provider_ports.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_execution_controls.py -q` | PASS, 75 passed |
| `.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_execution_controls.py tests/test_provider_ports.py tests/test_provenance_policy.py -q` | PASS |
| `.venv\Scripts\python -m pip check` | PASS, no broken requirements |
| `.venv\Scripts\python scripts\audit_data_readiness.py` | PASS, `ready_for_paper_alerts = true`, warning on stale sidecar |
| `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` | PASS, validation report emitted |
| `data/processed/data_readiness_report.json.manifest.json` | Manifest present |
| `data/processed/minimal_validation_report.json.manifest.json` | Manifest present |
| `data/processed/phase56_pead_evidence.csv.manifest.json` | Manifest present |

## Open Risks / Assumptions / Rollback

Open risks:
- yfinance direct usage exists in many legacy scripts; it is quarantined, not removed.
- S&P sidecar provenance is stale relative to newer market surfaces.

Assumptions:
- User-provided D-353 instruction authorizes this out-of-sequence accelerated provenance slice.
- Paper-alert readiness means daily US-equity alerts only, not live execution readiness.

Rollback:
- Revert the D-353 files and generated reports if leadership rejects the accelerated provenance milestone; do not alter prior Phase 61 SSOT artifacts or `core/engine.py`.

## Next Phase Roadmap

- Candidate registry: append-only candidate metadata and state transitions.
- Alert packet: schema requiring risk decision, source-quality, provider feed, and idempotency key.
- Paper portfolio loop: live-time zero-capital tracking of alerts, fills, slippage, and stale-rate.
- Advanced validation: multiple-testing, PSR/DSR, PBO/CSCV, SPA/Reality Check.
- Environment hygiene: keep `pip check` green before any experiment multiplication.

## New Context Packet

## What Was Done
- Completed D-353 accelerated provenance + validation A-E.
- Added source policy, manifest gates, provider ports, readiness audit, and minimal validation lab.
- Produced manifest-backed readiness and validation artifacts.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.

## What Is Locked
- No live trading, no broker automation, no Tier 2 promotion, and no yfinance canonical truth.
- Alpaca remains operational/paper data only unless a later signed decision-log packet changes scope.
- Validation reports require manifests and canonical source quality for promotion intent.
- Phase F Candidate Registry is approved as registry-only work; strategy factories, V2 fast simulation, promotion packets, and live execution remain blocked.

## What Remains
- Candidate registry implementation, alert packet, paper portfolio loop, advanced anti-overfit gates, and notifier integration.

## Next-phase Roadmap
- Phase F candidate registry: append-only lifecycle, `trial_count`, and manifest pointer requirements.
- Phase H alert packet after candidate registry and risk decision schema.
- Phase I paper trading loop after alert packet.

## Immediate First Step
```text
.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_provenance_policy.py tests/test_provider_ports.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_execution_controls.py -q
```

ConfirmationRequired: YES
Prompt: Reply "approve next phase" to start execution.
NextPhaseApproval: APPROVED_FOR_REGISTRY_ONLY
