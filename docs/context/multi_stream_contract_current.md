# Multi-Stream Contract - Quant Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, or scope widening by itself.
Purpose: coordinate Backend, Frontend/UI, Data, and Docs/Ops streams after D-353 and R64.1.

## Header
- `CONTRACT_ID`: `20260509-d354-r64-1-closeout-streams`
- `DATE_UTC`: `2026-05-09`
- `SCOPE`: `D-353 A-E complete + R64.1 dependency hygiene closed + Phase F approved/not started`
- `STATUS`: `current`
- `OWNER`: `PM / Architecture Office`

## Stream Map

### Stream 1: Backend
- **Purpose**: Validation lab, candidate registry, risk/alert contracts, broker boundary, and governed execution surfaces
- **Must Deliver**: Phase F Candidate Registry append-only lifecycle after R64.1 hygiene
- **Owned Files**:
  - `data/provenance.py`
  - `validation/*`
  - `execution/broker_api.py`
- **Interfaces**: Validation reports, Alpaca quote snapshots, promotion-source gates
- **Dependencies**: Needs Data manifests and Docs/Ops policy truth
- **Status**: `phase65-approved-not-started`

### Stream 2: Frontend/UI
- **Purpose**: Operator shell read surfaces and future data-source health display
- **Must Deliver**: No D-353 UI deliverable; future shell can consume readiness/provenance artifacts
- **Owned Files**:
  - `dashboard.py`
  - `views/*`
- **Interfaces**: Future source-quality/readiness badges
- **Dependencies**: Needs stable Candidate Registry artifacts before alert/readiness display
- **Status**: `deferred`

### Stream 3: Data
- **Purpose**: Canonical data, provider ports, data readiness, and source manifests
- **Must Deliver**: Provider ports, readiness audit, manifest-backed artifacts, yfinance quarantine allowlist
- **Owned Files**:
  - `data/providers/*`
  - `scripts/audit_data_readiness.py`
  - `data/processed/data_readiness_report.json*`
- **Interfaces**: `MarketDataPort`, readiness report, source-quality policy
- **Dependencies**: Needs broker wrapper for Alpaca operational quotes
- **Status**: `complete-d353-r64-1`

### Stream 4: Docs/Ops
- **Purpose**: Governance artifacts, phase brief, decision log, handover, current context, and SAW report
- **Must Deliver**: Current D-353/R64.1 truth surfaces and Phase F registry-only boundaries
- **Owned Files**:
  - `docs/architecture/data_source_policy.md`
  - `docs/phase_brief/phase64-brief.md`
  - `docs/handover/phase64_handover.md`
  - `docs/decision log.md`
  - `docs/notes.md`
  - `docs/context/*_current.md`
- **Interfaces**: Planner/PM bridge truth
- **Dependencies**: Needs evidence from Backend/Data streams
- **Status**: `complete-d353`

## Blocked Streams
- Live trading / broker automation remains blocked.
- Candidate registry implementation is not started yet; it is approved as the next narrow phase.
- Paper alert packet and paper portfolio loop are not started in D-353.

## Completion Criteria
- Backend manifest and validation tests pass.
- Data readiness report and manifest exist.
- Validation report and manifest exist.
- Docs/Ops current surfaces reflect D-353.
- No live trading path is introduced.

## Governance Status
- Phase 61: Complete; KS-03 cleared.
- D-353 / Phase 64 accelerated slice: Complete for provenance + validation A-E.
- R64.1 dependency hygiene: Complete; `pip check` passes.
- Next action: Phase F Candidate Registry only.
