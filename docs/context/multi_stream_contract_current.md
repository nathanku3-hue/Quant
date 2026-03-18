# Multi-Stream Contract - Quant Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: coordinate Docs/Ops, Backend, Frontend/UI, and Data streams so they stay connected instead of drifting into local loops.

## Header
- `CONTRACT_ID`: `20260318-quant-phase59-streams`
- `DATE_UTC`: `2026-03-18`
- `SCOPE`: `Phase 59 bounded Shadow Portfolio packet + ongoing governance maintenance`
- `STATUS`: `active`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- Quant has multiple active streams (Docs/Ops, Backend, Frontend/UI, Data) that can drift into local loops if not explicitly coordinated through shared integration checkpoints.

## Static Truth Inputs
- `top_level_PM.md`
- `docs/decision log.md`
- `docs/phase_brief/phase59-brief.md`
- `README.md`

## Stream Map

### Stream 1: Backend
- **Purpose**: Core research kernel, portfolio construction, shadow monitoring, and bounded execution surfaces
- **Must Deliver**: Phase 59 bounded Shadow Portfolio packet (read-only NAV/alert surface)
- **Owned Files**:
  - `data/phase59_shadow_portfolio.py`
  - `scripts/phase59_shadow_portfolio_runner.py`
  - `data/research_connector.py`
  - `research_data/catalog.duckdb`
  - `data/processed/phase59_*` artifacts
- **Interfaces**: Exposes `phase59_shadow_summary.json`, `phase59_shadow_evidence.csv`, `phase59_shadow_delta_vs_c3.csv` to Frontend/UI
- **Dependencies**: Needs immutable prior sleeve SSOT from Data stream (phase54-58 artifacts)
- **Status**: `executing` (D-329 bounded packet implemented)

### Stream 2: Frontend/UI
- **Purpose**: Dashboard monitoring, visualization, and PM/operator read surfaces
- **Must Deliver**: Bounded dashboard reader for Phase 59 Shadow Portfolio surface
- **Owned Files**:
  - `views/shadow_portfolio_view.py`
  - `dashboard.py` (bounded tab hook)
  - `tests/test_shadow_portfolio_view.py`
- **Interfaces**: Consumes `phase59_*` artifacts from Backend, exposes dashboard UI to PM/operators
- **Dependencies**: Needs Backend to persist `phase59_*` artifacts first
- **Status**: `executing` (bounded dashboard hook added)

### Stream 3: Data
- **Purpose**: Research data catalog, allocator state, historical shadow artifacts, and prior sleeve SSOT
- **Must Deliver**: Immutable prior sleeve SSOT (phase54-58), read-only allocator_state catalog
- **Owned Files**:
  - `research_data/catalog.duckdb`
  - `research_data/allocator_state_cube/`
  - `data/processed/phase50_shadow_ship/` (reference-only)
  - `data/processed/phase54_core_sleeve_summary.json`
  - `data/processed/phase55_allocator_cpcv_evidence.json`
  - `data/processed/phase56_pead_evidence.json`
  - `data/processed/phase57_governance_evidence.json`
  - `data/processed/phase58_governance_layer_evidence.json`
- **Interfaces**: Exposes read-only `allocator_state` catalog and immutable prior sleeve SSOT to Backend
- **Dependencies**: None (SSOT is locked)
- **Status**: `complete` (prior sleeve SSOT immutable, catalog read-only)

### Stream 4: Docs/Ops
- **Purpose**: Governance artifacts, phase briefs, decision log, handover memos, bridge contracts
- **Must Deliver**: Phase 59 brief, execution memo, bridge contract, done checklist, multi-stream contract
- **Owned Files**:
  - `docs/phase_brief/phase59-brief.md`
  - `docs/handover/phase59_execution_memo_20260318.md`
  - `docs/context/bridge_contract_current.md`
  - `docs/context/done_checklist_current.md`
  - `docs/context/multi_stream_contract_current.md`
  - `docs/context/current_context.md`
  - `docs/decision log.md` (D-327, D-328, D-329)
- **Interfaces**: Exposes governance truth to all streams, consumes execution evidence from Backend/Frontend
- **Dependencies**: Needs Backend/Frontend execution evidence to update bridge contract and done checklist
- **Status**: `executing` (Phase 59 governance artifacts in progress)

## Active Stream Now
- **Backend** (Phase 59 bounded packet execution)
- **Frontend/UI** (bounded dashboard reader)
- **Docs/Ops** (governance artifact updates)

## Deferred Streams
- None (all streams active for Phase 59 bounded packet)

## Blocked Streams
- None currently blocked

## Shared Success Condition
- Phase 59 bounded Shadow Portfolio packet is complete when:
  - Backend persists all `phase59_*` artifacts
  - Frontend/UI exposes bounded dashboard reader
  - Data stream maintains immutable prior sleeve SSOT
  - Docs/Ops publishes complete governance artifacts (brief, memo, bridge, checklist, contract)
  - All tests pass
  - PM/CEO can review bounded packet as evidence-only before Phase 60 decision

## Integration Checkpoints
- **Checkpoint 1**: Backend persists `phase59_*` artifacts → Frontend can build dashboard reader
- **Checkpoint 2**: Backend + Frontend execution complete → Docs/Ops updates bridge contract and done checklist
- **Checkpoint 3**: All streams complete → PM/CEO bounded packet review (evidence-only / no promotion / no widening)

## Cross-Stream Risks
- Backend could mutate prior sleeve SSOT (Data stream) → mitigated by immutability lock and git diff checks
- Frontend could read stale artifacts if Backend changes schema → mitigated by bounded artifact contract
- Docs/Ops could drift from execution truth if Backend/Frontend don't update handover → mitigated by bridge contract refresh after execution

## Pre-Flight Conditions
- D-328 execution authorization consumed (approved 2026-03-18)
- Prior sleeve SSOT immutable (phase54-58 artifacts locked)
- RESEARCH_MAX_DATE = 2022-12-31 enforced
- Same-window / same-cost / same-engine discipline active

## Evidence Used
- `docs/context/current_context.md`
- `docs/phase_brief/phase59-brief.md`
- `docs/context/bridge_contract_current.md`
- `README.md`

## Writing Rules
- Keep this file top-level and PM-readable.
- Prefer system language over file-changelog language.
- Make stream boundaries explicit: what each stream owns, what it exposes, what it needs.
- If a stream is deferred, say why and when it becomes active.
- If a stream is blocked, say what unblocks it.
- Keep the artifact thin: one current contract, not a growing archive.
