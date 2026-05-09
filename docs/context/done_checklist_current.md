# Done Checklist - R64.1 Dependency + Git Hygiene Closeout

Status: Closed
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, or scope widening by itself.
Purpose: define machine-checkable done criteria for closing D-353/R64.1 before Phase F Candidate Registry starts.

## Header
- `CHECKLIST_ID`: `20260509-d354-r64-1-closeout`
- `DATE_UTC`: `2026-05-09`
- `SCOPE`: `D-353 A-E complete + R64.1 dependency hygiene closed + Phase F approved/not started`
- `STATUS`: `closed`
- `OWNER`: `PM / Architecture Office`

## Done Criteria

### Governance Closeout
- [x] `D-353` decision log entry records yfinance quarantine, Alpaca operational/paper scope, no live orders, and manifest-first validation.
- [x] `D-354` decision log entry records Alpaca SDK migration, `pip check` closure, and Phase F registry-only approval.
- [x] `docs/architecture/data_source_policy.md` is published.
- [x] `docs/phase_brief/phase64-brief.md`, `docs/phase_brief/phase65-brief.md`, and `docs/handover/phase64_handover.md` are published.
- [x] `docs/lessonss.md` and `docs/saw_reports/saw_phase64_d353_provenance_validation_20260509.md` are published.

### Executable Gate Completeness
- [x] Manifest schema exists in `data/provenance.py`.
- [x] Missing-manifest validation fails closed.
- [x] Tier 2/non-canonical promotion-intent validation fails closed.
- [x] Alert/quote records require `source_quality`, provider, and feed tags.
- [x] Alpaca IEX quote snapshots are tagged `iex_only`.
- [x] Non-paper Alpaca endpoint initialization requires both break-glass and signed-decision env gates.

### Provider-Port Completeness
- [x] `MarketDataPort` exists in `data/providers/base.py`.
- [x] Yahoo adapter exists and emits `source_quality = non_canonical`.
- [x] Alpaca adapter exists and routes through the broker wrapper.
- [x] `TZ_MARKET_DATA_PROVIDER` selector exists.
- [x] Current direct yfinance usage is captured by the migration allowlist.

### Audit + Validation Completeness
- [x] Data readiness audit emits `data/processed/data_readiness_report.json`.
- [x] Data readiness audit emits `data/processed/data_readiness_report.json.manifest.json`.
- [x] Minimal validation lab emits `data/processed/minimal_validation_report.json`.
- [x] Minimal validation lab emits `data/processed/minimal_validation_report.json.manifest.json`.
- [x] PEAD evidence input manifest exists at `data/processed/phase56_pead_evidence.csv.manifest.json`.

### Verification Completeness
- [x] Targeted tests pass: `75 passed`.
- [x] Data readiness audit passes: `ready_for_paper_alerts = true`.
- [x] Minimal validation lab passes on existing PEAD evidence.
- [x] Secret scan over touched milestone files contains no pasted Alpaca key material.
- [x] SAW block validation and closure-packet validation pass.
- [x] `pip check` passes.
- [x] Dependency files use `alpaca-py==0.43.4` and exclude the legacy Alpaca SDK.
- [x] Milestone commits are surgical and unrelated dirty files are excluded.
- [x] A-E evidence artifacts under `data/processed/` are intentionally ignored by repo policy and reproducible with the audit/validation commands.

## Explicit Non-Goals
- No live Alpaca orders.
- No broker automation.
- No intraday/HFT.
- No options/futures.
- No Tier 2 promotion packets.
- No yfinance canonical truth.
- No credentials in source/docs/tests/logs/artifacts.

## Machine-Checkable Rules

### Pass Conditions
```text
.venv\Scripts\python -m pytest tests/test_provenance_policy.py tests/test_provider_ports.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_execution_controls.py -q
.venv\Scripts\python scripts\audit_data_readiness.py
.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent
.venv\Scripts\python -m pip check
.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_execution_controls.py tests/test_provider_ports.py tests/test_provenance_policy.py -q
.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_phase64_d353_provenance_validation_20260509.md
test -f data/processed/data_readiness_report.json.manifest.json
test -f data/processed/minimal_validation_report.json.manifest.json
test -f data/processed/phase56_pead_evidence.csv.manifest.json
```

### Fail Conditions
```text
run a secret scanner over data docs scripts tests execution validation and fail on credential material
rg "submit_order\\(" data/providers validation scripts/run_minimal_validation_lab.py scripts/audit_data_readiness.py
```

## Evidence Used
- `docs/phase_brief/phase64-brief.md`
- `docs/handover/phase64_handover.md`
- `docs/architecture/data_source_policy.md`
- `data/processed/data_readiness_report.json`
- `data/processed/minimal_validation_report.json`
- `tests/test_provenance_policy.py`
- `tests/test_provider_ports.py`
- `docs/saw_reports/saw_phase64_d353_provenance_validation_20260509.md`
- `docs/saw_reports/saw_phase64_1_dependency_git_hygiene_20260509.md`

## Open Risks
- yfinance quarantine surface is broad and should be migrated gradually.
- S&P sidecar provenance is stale through `2023-11-27`.
