# Multi-Stream Contract - Quant Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: coordinate Docs/Ops, Backend, Frontend/UI, and Data streams so they stay connected instead of drifting into local loops.

## Header
- `CONTRACT_ID`: `20260322-quant-phase61-streams`
- `DATE_UTC`: `2026-03-22`
- `SCOPE`: `Phase 61 complete - KS-03 cleared, next platform-hardening phase pending`
- `STATUS`: `current`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- Quant has multiple active streams (Docs/Ops, Backend, Frontend/UI, Data) that can drift into local loops if not explicitly coordinated through shared integration checkpoints after the Phase 61 comparator repair.

## Static Truth Inputs
- `top_level_PM.md`
- `docs/decision log.md`
- `docs/phase_brief/phase61-brief.md`
- `README.md`

## Stream Map

### Stream 1: Backend
- **Purpose**: Core research kernel, portfolio construction, shadow monitoring, and bounded execution surfaces
- **Must Deliver**: Completed Phase 61 comparator repair path with sidecar overlay + post-coverage masking
- **Owned Files**:
  - `scripts/phase60_governed_audit_runner.py`
  - `scripts/ingest_d350_wrds_sidecar.py`
  - `scripts/build_sp500_pro_sidecar.py`
  - `data/processed/sidecar_sp500_pro_2023_2024.parquet`
  - `data/processed/phase60_governed_audit_summary.json`
- **Interfaces**: Exposes the cleared governed-audit summary and bounded sidecar surface to Frontend/UI and Docs/Ops
- **Dependencies**: Needs immutable prior sleeve SSOT from Data stream (phase54-60 artifacts)
- **Status**: `complete` (Phase 61 comparator-remediation packet complete under `D-351`)

### Stream 2: Frontend/UI
- **Purpose**: Dashboard monitoring, visualization, and PM/operator read surfaces
- **Must Deliver**: Current operator shell and read surfaces that match the cleared Phase 61 truth
- **Owned Files**:
  - `dashboard.py`
  - `views/shadow_portfolio_view.py`
  - `views/auto_backtest_view.py`
  - `views/optimizer_view.py`
- **Interfaces**: Consumes current context packets, governed audit status, and bounded sidecar truth from Backend and Docs/Ops
- **Dependencies**: Needs Docs/Ops packet refresh and stable backend interfaces before shell consolidation starts
- **Status**: `ready-next` (Phase 61 removed the comparator blocker; shell consolidation is the leading next-stream candidate)

### Stream 3: Data
- **Purpose**: Raw data, feature store, fundamentals panel, sleeve surfaces, and comparator baselines
- **Must Deliver**: Immutable prior sleeve SSOT plus additive-only sidecar lanes
- **Owned Files**:
  - `data/feature_store.py`
  - `data/updater.py`
  - `data/fundamentals_panel.py`
  - `data/processed/phase54-60_*` artifacts
  - `data/processed/sidecar_*.parquet`
- **Interfaces**: Exposes feature/sleeve/comparator surfaces to Backend stream
- **Dependencies**: Needs no mutation of `research_data/` or prior artifacts
- **Status**: `frozen-plus-sidecar` (bedrock surfaces unchanged; additive sidecar lane active)

### Stream 4: Docs/Ops
- **Purpose**: Governance artifacts, decision log, phase briefs, SAW reports, and context packets
- **Must Deliver**: Current packet set aligned to the Phase 61 complete state
- **Owned Files**:
  - `docs/phase_brief/phase61-brief.md`
  - `docs/saw_reports/saw_phase61_*.md`
  - `docs/context/current_context.md`
  - `docs/context/bridge_contract_current.md`
  - `docs/context/done_checklist_current.md`
  - `docs/context/multi_stream_contract_current.md`
  - `docs/context/impact_packet_current.md`
  - `docs/context/observability_pack_current.md`
  - `docs/context/planner_packet_current.md`
  - `docs/context/post_phase_alignment_current.md`
  - `docs/decision log.md`
  - `README.md`
- **Interfaces**: Consumes all stream outputs for governance review and next-phase planning
- **Dependencies**: Needs backend evidence truth to stay current and frontend roadmap decisions to be explicit
- **Status**: `complete` (Phase 61 packet reconciliation complete)

## Blocked Streams
- None on comparator correctness; remaining blocks are governance or prioritization choices, not `KS-03`.

## Completion Criteria
Phase 61 bounded comparator-remediation packet is complete when:
- Backend publishes a passing governed-audit summary and bounded sidecar evidence
- Frontend/UI consumes current packet truth rather than the older Phase 60 hold narrative
- Data stream confirms bedrock immutability and additive-only sidecar writes
- Docs/Ops publishes current brief, SAW reports, and reconciled context packets
- Targeted Phase 61 tests and context-builder validation pass

## Governance Status
- Phase 60: Closed as `CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD` under `D-345`
- Phase 61: Complete; `KS-03` cleared under `D-351`
- Next packet required: choose the next platform-hardening phase (frontend shell consolidation or execution-boundary hardening)
