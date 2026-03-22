# Quant Trading System

A production-grade quantitative trading system with factor-based portfolio construction, regime-aware risk management, and real-time performance attribution.

## Overview

This system implements a multi-phase quantitative trading strategy with:
- **Factor Attribution Analysis** - IC-based factor evaluation with regime conditioning
- **Risk Management** - Maintenance blackout windows, drain strategies, and transient backoff
- **Dashboard** - Real-time monitoring with attribution views and performance metrics
- **Orchestration** - Event-driven architecture with retry/backoff mechanisms

## Project Status

**Current Phase**: Phase 61 (Comparator Remediation) — COMPLETE / KS-03 CLEARED
- **Phase 61 Status**: Complete under D-348/D-350/D-351
  - same-period C3 comparator repaired through bounded sidecar/view-layer logic
  - kernel immutable (`core/engine.py` unchanged)
  - governed audit now returns `status = "ok"`
- **Open Operational Risk**: Live WRDS authentication still fails with PAM rejection; current provenance uses bounded bedrock fallback
- **Next**: truth surfaces reconciled; next explicit platform phase should choose between frontend shell consolidation and execution-boundary hardening

## Current Truth Surfaces

Use these surfaces together to understand the current system state:

### Static Truth
- **[top_level_PM.md](top_level_PM.md)** — long-lived product/system intent
- **[docs/decision log.md](docs/decision%20log.md)** — authoritative decision history
- **Active phase brief** — current phase scope and boundaries (e.g., `docs/phase_brief/phase61-brief.md`)

### Live Truth
- **[docs/context/current_context.md](docs/context/current_context.md)** — current active phase and next immediate command

### Bridge Truth
- **[docs/context/bridge_contract_current.md](docs/context/bridge_contract_current.md)** — translates recent technical closeout state back into PM/planner language and names the next system-level decision

### Evidence Truth
- **[docs/context/done_checklist_current.md](docs/context/done_checklist_current.md)** — machine-checkable done criteria for current phase
- **[docs/context/multi_stream_contract_current.md](docs/context/multi_stream_contract_current.md)** — cross-stream coordination map (Backend, Frontend/UI, Data, Docs/Ops)
- **[docs/context/post_phase_alignment_current.md](docs/context/post_phase_alignment_current.md)** — post-phase stream status update and bottleneck analysis

### Planner Truth
- **[docs/context/planner_packet_current.md](docs/context/planner_packet_current.md)** — compact fresh-context packet for planner (current context, active brief, bridge truth, decision tail, blocked next step, active bottleneck)
- **[docs/context/impact_packet_current.md](docs/context/impact_packet_current.md)** — impact view for planner (changed files, owned files, touched interfaces, failing checks)

### Observability
- **[docs/context/observability_pack_current.md](docs/context/observability_pack_current.md)** — drift detection markers (high-risk attempts, stuck sessions, skill under-triggering, budget pressure, compaction/hallucination pressure)

These surfaces follow the SOP governance kernel (see `E:\code\SOP\ENDGAME.md` for the full truth model).

## Quick Start

### Prerequisites
- Python 3.12+
- Virtual environment recommended

### Installation

```bash
# Clone repository
git clone <repository-url>
cd Quant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

### Running Attribution Analysis

```bash
python scripts/attribution_report.py \
  --start-date 2022-01-01 \
  --end-date 2024-12-31 \
  --output-dir data/processed
```

## Architecture

### Core Modules

- **`core/`** - Core business logic
  - `data_orchestrator.py` - Data loading and orchestration
  - `dashboard_control_plane.py` - Dashboard state management
  - `maintenance_blackout.py` - Maintenance window enforcement
  - `retry_backoff.py` - Transient error handling

- **`strategies/`** - Trading strategies
  - `factor_attribution.py` - IC computation and attribution
  - `behavior_ledger.py` - Behavior tracking with bootstrap CI

- **`execution/`** - Order execution
  - `microstructure.py` - Market microstructure handling

- **`views/`** - Dashboard views
  - `attribution_view.py` - Attribution visualization

### Scripts

- **`scripts/phase60_preflight_verify.py`** - Preflight verification for governed cube
- **`scripts/phase60_governed_audit_runner.py`** - Bounded post-2022 audit runner
- **`scripts/phase60_governed_cube_runner.py`** - Governed daily holdings/weight cube generator
- **`scripts/phase60_d341_blocked_audit_review.py`** - Formal blocked-audit review

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run Phase 61 specific tests
pytest tests/test_phase60_governed_audit_runner.py tests/test_ingest_d350_wrds_sidecar.py tests/test_build_sp500_pro_sidecar.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage**: Phase 61 targeted tests and packet hygiene checks passing
- Governed audit runner regression tests
- WRDS sidecar extractor tests
- Raw-tape sidecar builder tests
- Context-builder and Phase 61 packet hygiene tests

## Phase 61 Deliverables

### Artifacts Generated

Key artifacts in `data/processed/`:

1. **sidecar_sp500_pro_2023_2024.parquet** - Bounded sidecar return surface for the repaired comparator path
2. **phase60_governed_audit_summary.json** - Governed audit summary now reporting `status = "ok"`
3. **phase61_d350_wrds_pivot_20260319_summary.json** - Evidence summary for sidecar overlay and coverage masking
4. **phase61_sp500_pro_tape_block_20260320.json** - Truthful raw-tape blocker evidence for the literal vendor export path

### Validation

**Governance State**: Phase 61 complete with `KS-03` cleared
- comparator repair bounded to sidecar/view-layer logic
- kernel immutable per D-347
- promotion, allocator carry-forward, and core inclusion still blocked

## Documentation

### Phase 61
- **`docs/phase_brief/phase61-brief.md`** - Phase 61 bounded remediation brief
- **`docs/saw_reports/saw_phase61_d349_sp500_pro_sidecar_20260320.md`** - Sidecar fallback review
- **`docs/saw_reports/saw_phase61_d350_tape_ingest_block_20260320.md`** - Raw-tape blocker review
- **`docs/saw_reports/saw_phase61_d350_wrds_tape_20260319.md`** - WRDS/bedrock fallback remediation review

### General
- **`docs/decision log.md`** - Architecture decision records (D-01 through D-351)
- **`docs/context/bridge_contract_current.md`** - Current PM/planner bridge

## Current System Status

- **Multi-Sleeve Research Kernel**: Phase 56/57/58/59/60 evidence surfaces preserved as immutable SSOT, with a bounded Phase 61 repair lane completed on top
- **Governance Stack**: 351 architecture decisions
- **Remaining Risks**: vendor-side provenance still indirect; promotion and widened execution remain blocked

## Development Workflow

### Branching Strategy
- `main` - Production-ready code
- Feature branches for new phases

### Commit Convention
```
feat: add new feature
fix: bug fix
chore: maintenance tasks
docs: documentation updates
test: test additions/modifications
```

### Phase Progression
1. Phase brief created in `docs/phase_brief/`
2. Implementation with tests
3. SAW report (Strengths, Areas for improvement, Warnings)
4. Closure report with acceptance criteria validation
5. Merge to main

## Configuration

Configuration files in `config/`:
- Factor definitions
- Regime thresholds
- Risk parameters

## Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass: `pytest tests/ -v`
4. Update documentation
5. Submit for review

## License

[Specify license]

## Contact

[Specify contact information]

---

**Last Updated**: 2026-03-22
**Phase**: 61 (Comparator Remediation Complete)
**Status**: Phase 61 COMPLETE / KS-03 CLEARED ✅ | Next Platform Phase Pending 🔄
