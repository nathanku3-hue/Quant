# Phase 64 Brief

Status: COMPLETE - ACCELERATED PROVENANCE + VALIDATION A-E + R64.1 HYGIENE
Authority: D-353 user-approved bounded milestone + D-354 R64.1 closeout
Date: 2026-05-09
Owner: PM / Architecture Office

## Goal

Make provenance executable before any further paper-alert or validation work: freeze source policy, enforce manifests, quarantine direct yfinance usage, expose provider ports, run data readiness, and run a minimal validation lab on an existing PEAD-style return stream.

## Non-Goals

- No live Alpaca orders.
- No broker automation.
- No intraday/HFT.
- No options/futures.
- No Tier 2 promotion packets.
- No yfinance as canonical research truth.
- No credentials in source, docs, tests, logs, or artifacts.

## Delivered Scope

- Phase A: `docs/architecture/data_source_policy.md` defines canonical, operational, discovery, and rejected source tiers.
- Phase B: `data/provenance.py` defines manifest schema, hash checks, validation gates, promotion gates, alert gates, and quote metadata gates.
- Phase C: `data/providers/` defines `MarketDataPort`, Yahoo quarantine adapter, Alpaca operational adapter, provider selector, and yfinance migration allowlist.
- Phase D: `scripts/audit_data_readiness.py` audits local daily US-equity readiness and writes a manifest-backed report.
- Phase E: `validation/` plus `scripts/run_minimal_validation_lab.py` implement OOS, walk-forward, regime, permutation, and bootstrap checks.
- Broker boundary: `execution/broker_api.py` now tags Alpaca quote snapshots by feed and requires a signed decision env gate in addition to live break-glass for non-paper endpoints.
- R64.1 dependency hygiene: main dependencies now use `alpaca-py==0.43.4`; `alpaca-trade-api` was removed from the main research environment and the broker boundary keeps the same paper/live gates.

## Validation State

- Focused invariant tests pass: `75 passed`.
- Data readiness audit pass: `ready_for_paper_alerts = true`.
- Data readiness warning: primary S&P sidecar max date is `2023-11-27`.
- Minimal validation lab pass on `data/processed/phase56_pead_evidence.csv`.
- Venv restored to Python `3.12.13` from the bundled Codex runtime after the original `.venv` pointed at a missing Python `3.12.10` install.
- `pip check` passes after migrating the main Alpaca dependency to `alpaca-py==0.43.4`.

## Acceptance Checks

- [x] CHK-P64-01: Source policy is committed as docs-as-code.
- [x] CHK-P64-02: Validation reports fail closed without manifests.
- [x] CHK-P64-03: Tier 2 data cannot enter promotion-intent validation.
- [x] CHK-P64-04: Alerts/quotes require `source_quality` and provider/feed tags.
- [x] CHK-P64-05: Alpaca IEX quotes are tagged `iex_only`; SIP/delayed SIP tags are explicit.
- [x] CHK-P64-06: yfinance direct usage is quarantined by a migration allowlist.
- [x] CHK-P64-07: Data readiness audit emits report + manifest.
- [x] CHK-P64-08: Minimal validation lab runs against existing PEAD evidence and emits report + manifest.
- [x] CHK-P64-09: No live Alpaca order path is introduced.
- [x] CHK-P64-10: Secret scan over touched milestone files contains no pasted Alpaca key material.
- [x] CHK-P64-11: `pip check` passes.
- [x] CHK-P64-12: `requirements.txt`, `requirements.lock`, and `pyproject.toml` reflect `alpaca-py==0.43.4` and exclude `alpaca-trade-api`.
- [x] CHK-P64-13: Dependency hygiene tests prove the broker boundary no longer imports the legacy Alpaca SDK.

## Evidence

- `data/processed/data_readiness_report.json`
- `data/processed/data_readiness_report.json.manifest.json`
- `data/processed/minimal_validation_report.json`
- `data/processed/minimal_validation_report.json.manifest.json`
- `data/processed/phase56_pead_evidence.csv.manifest.json`
- `tests/test_provenance_policy.py`
- `tests/test_provider_ports.py`
- `tests/test_data_readiness_audit.py`
- `tests/test_minimal_validation_lab.py`
- `tests/test_dependency_hygiene.py`
- `.venv\Scripts\python -m pip check`

## Open Risks

- The yfinance quarantine surface is larger than the planning artifact listed; it includes numerous legacy scripts now explicitly allowlisted for migration.
- Data readiness is sufficient for daily paper alerts, but the S&P sidecar is stale relative to 2024+ surfaces.
- Paper alert packet creation and paper portfolio loop remain future phases; this milestone only enforces the source/provenance/validation gates that those phases must consume.

## New Context Packet

## What Was Done
- Completed the accelerated provenance + validation A-E milestone under D-353.
- Added executable provenance gates, provider ports, yfinance quarantine allowlist, data readiness audit, and minimal validation lab.
- Produced manifest-backed readiness and validation artifacts proving daily paper-alert readiness and PEAD validation-lab execution.
- Closed R64.1 dependency hygiene by migrating the main Alpaca dependency to `alpaca-py==0.43.4` and making `pip check` pass.

## What Is Locked
- yfinance remains Tier 2 discovery/convenience only and cannot enter promotion-intent validation.
- Alpaca is operational/paper market data only in this milestone; live orders and broker automation remain blocked.
- Validation reports require manifests, and promotion-intent validation accepts canonical sources only.
- Candidate Registry is approved as the next phase, but strategy search, promotion packets, and live execution remain blocked.

## What Is Next
- Implement Phase F Candidate Registry only: append-only state transitions, candidate metadata before results, `trial_count`, and manifest pointer requirements.
- Refresh stale sidecar provenance when vendor access is available.

## First Command
```text
.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_provenance_policy.py tests/test_provider_ports.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_execution_controls.py -q
```

## Next Todos
- Candidate registry before multiple-testing correction.
- Alert packet schema before any notifier or paper portfolio loop.
