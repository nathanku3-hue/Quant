# Multi-Stream Contract - Quant Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: coordinate Docs/Ops, Backend, Frontend/UI, and Data streams so they stay connected instead of drifting into local loops.

## Header
- `CONTRACT_ID`: `20260320-quant-phase60-streams`
- `DATE_UTC`: `2026-03-20`
- `SCOPE`: `Phase 60 closed-blocked-evidence-only-hold`
- `STATUS`: `closed`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- Quant has multiple active streams (Docs/Ops, Backend, Frontend/UI, Data) that can drift into local loops if not explicitly coordinated through shared integration checkpoints.

## Static Truth Inputs
- `top_level_PM.md`
- `docs/decision log.md`
- `docs/phase_brief/phase60-brief.md`
- `README.md`

## Stream Map

### Stream 1: Backend
- **Purpose**: Core research kernel, portfolio construction, shadow monitoring, and governed execution surfaces
- **Must Deliver**: Phase 60 governed cube and blocked audit evidence (read-only)
- **Owned Files**:
  - `scripts/phase60_preflight_verify.py`
  - `scripts/phase60_governed_audit_runner.py`
  - `scripts/phase60_governed_cube_runner.py`
  - `scripts/phase60_d341_blocked_audit_review.py`
  - `data/processed/phase60_*` artifacts
- **Interfaces**: Exposes `phase60_governed_cube.parquet`, `phase60_d340_audit_*.status.txt`, `phase60_d341_review_*.csv` to Frontend/UI
- **Dependencies**: Needs immutable prior sleeve SSOT from Data stream (phase54-59 artifacts)
- **Status**: `closed` (Phase 60 closed as blocked evidence-only hold under D-345)

### Stream 2: Frontend/UI
- **Purpose**: Dashboard monitoring, visualization, and PM/operator read surfaces
- **Must Deliver**: Bounded dashboard reader for Phase 60 evidence surface (read-only)
- **Owned Files**:
  - `views/shadow_portfolio_view.py`
  - `dashboard.py`
- **Interfaces**: Consumes `phase60_governed_cube.parquet`, `phase60_*` evidence artifacts from Backend
- **Dependencies**: Needs Backend stream to publish bounded evidence artifacts
- **Status**: `complete` (Phase 60 bounded read surface complete)

### Stream 3: Data
- **Purpose**: Raw data, feature store, fundamentals panel, sleeve surfaces, and comparator baselines
- **Must Deliver**: Immutable prior sleeve SSOT (Phase 56/57/58/59 artifacts), C3 comparator baseline
- **Owned Files**:
  - `data/feature_store.py`
  - `data/updater.py`
  - `data/fundamentals_panel.py`
  - `data/processed/phase54-59_*` artifacts
- **Interfaces**: Exposes feature/sleeve/comparator surfaces to Backend stream
- **Dependencies**: Needs no mutation of `research_data/` or prior artifacts
- **Status**: `frozen` (RESEARCH_MAX_DATE = 2022-12-31)

### Stream 4: Docs/Ops
- **Purpose**: Governance artifacts, decision log, phase briefs, handovers, SAW reports, context packets
- **Must Deliver**: Phase 60 brief, handover, SAW reports, done checklist, multi-stream contract
- **Owned Files**:
  - `docs/phase_brief/phase60-brief.md`
  - `docs/handover/phase60_handover.md`
  - `docs/handover/phase60_execution_handover_20260318.md`
  - `docs/saw_reports/saw_phase60_*.md`
  - `docs/context/current_context.md`
  - `docs/context/bridge_contract_current.md`
  - `docs/context/done_checklist_current.md`
  - `docs/context/multi_stream_contract_current.md`
  - `docs/context/impact_packet_current.md`
  - `docs/context/observability_pack_current.md`
  - `docs/context/planner_packet_current.md`
  - `docs/context/post_phase_alignment_current.md`
  - `docs/decision log.md`
- **Interfaces**: Consumes all stream outputs for governance review
- **Dependencies**: Needs all streams to complete their Phase 60 deliverables
- **Status**: `complete` (Phase 60 governance artifacts complete)

## Blocked Streams
None (all streams complete for Phase 60 bounded packet)

## Completion Criteria
Phase 60 bounded Stable Shadow Portfolio packet is complete when:
- Backend publishes governed cube and blocked audit evidence artifacts
- Frontend/UI exposes read-only dashboard surface for evidence
- Data stream confirms immutable prior sleeve SSOT
- Docs/Ops publishes Phase 60 brief, handover, SAW reports, context packets
- All Phase 60 tests passing
- PM/CEO can review bounded packet as evidence-only before Phase 61 decision

## Governance Status
- Phase 60: CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD (D-345)
- Phase 61: Bootstrap authorized (D-348) but not yet publicly executed
- All streams awaiting explicit `approve next phase` token before Phase 61 work begins
