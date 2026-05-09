# Post-Phase Alignment - R64.1 Closeout

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, or scope widening by itself.
Purpose: update the multi-stream map after the accelerated provenance + validation milestone and dependency hygiene wedge.

## Header
- `ALIGNMENT_ID`: `20260509-d354-r64-1-closeout-alignment`
- `DATE_UTC`: `2026-05-09`
- `SCOPE`: `D-353 A-E complete + R64.1 dependency hygiene closed + Phase F approved/not started`
- `PREVIOUS_PHASE`: `Phase 61 complete / D-352 roadmap locked`
- `NEXT_PHASE`: `Phase F Candidate Registry`
- `OWNER`: `PM / Architecture Office`

## What Changed This Round

### System Shape Delta
- Source quality is now an executable contract.
- Validation reports require manifests.
- Promotion-intent validation is canonical-only.
- yfinance is quarantined as Tier 2 discovery/convenience.
- Alpaca quote snapshots now carry feed and quality metadata.
- Live Alpaca endpoint initialization now needs a signed decision in addition to break-glass.
- Main Alpaca SDK boundary now uses `alpaca-py==0.43.4`; `pip check` passes.

### Execution Delta
- Added provenance module, provider ports, readiness audit, validation lab, tests, and docs.
- Generated readiness and validation reports with manifests.
- Restored `.venv` onto Python 3.12.13 from the bundled Codex runtime because the previous Python 3.12.10 home path no longer existed.

### No Change
- No live orders.
- No broker automation.
- No `core/engine.py` mutation.
- No `research_data/` mutation.
- No yfinance canonical status.
- No promotion authority.

## Stream Status Update

### Backend
- **Previous Status**: ready for future platform hardening
- **Current Status**: provenance/validation gate complete
- **What Changed**: validation and promotion-source gates are now executable.
- **What Remains**: alert packet and paper portfolio loop.

### Frontend/UI
- **Previous Status**: Phase 62 ready
- **Current Status**: deferred in D-353
- **What Changed**: no UI code in this slice.
- **What Remains**: source-quality/readiness display can be added later.

### Data
- **Previous Status**: frozen-plus-sidecar
- **Current Status**: manifest-backed readiness audit complete
- **What Changed**: local daily US-equity readiness is now reported with a manifest.
- **What Remains**: refresh stale S&P sidecar provenance.

### Docs/Ops
- **Previous Status**: D-352 roadmap ready
- **Current Status**: D-353 current surfaces updated
- **What Changed**: policy, brief, handover, decision log, notes, and current packets now reflect provenance gates.
- **What Remains**: Candidate Registry implementation and future yfinance/sidecar cleanup.

## Current Bottleneck
- **Candidate lineage / registry** is the next product bottleneck.
- **Why**: Provenance gates exist; discovery ideas now need append-only candidate identity before advanced multiple-testing or alerts.

## Interface Drift
- yfinance legacy usage was broader than the original plan. The allowlist now reflects actual direct-use files and fails on new spread.
- Alpaca dependency drift is closed for the main environment; keep `pip check` green before future experiment multiplication.

## Next Stream Active
- **Backend/Data**
- **Why**: Candidate registry and alert packet will consume the new provenance/validation gates.

## PM Decision Required
- None for R64.1. Phase F Candidate Registry is approved as registry-only work.

## What Should Not Be Done Next
- Do not place live orders.
- Do not use pasted credentials.
- Do not promote Tier 2 data.
- Do not delete yfinance before legacy paths are behind adapters.

## Open Risks
- Broad yfinance quarantine surface.
- Stale S&P sidecar max date.

## Evidence Used
- `docs/phase_brief/phase64-brief.md`
- `docs/handover/phase64_handover.md`
- `docs/architecture/data_source_policy.md`
- `data/processed/data_readiness_report.json`
- `data/processed/minimal_validation_report.json`
