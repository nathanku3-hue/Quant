# Quant Trading System

A production-grade quantitative trading system with factor-based portfolio construction, regime-aware risk management, and real-time performance attribution.

## Overview

This system implements a multi-phase quantitative trading strategy with:
- **Factor Attribution Analysis** - IC-based factor evaluation with regime conditioning
- **Risk Management** - Maintenance blackout windows, drain strategies, and transient backoff
- **Dashboard** - Real-time monitoring with attribution views and performance metrics
- **Orchestration** - Event-driven architecture with retry/backoff mechanisms

## Project Status

**Current Phase**: Phase 60 (Stable Shadow Portfolio) — CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD 🚫
- **Phase 60 Status**: Closed under D-345/D-347/D-348
  - 274-cell C3 return gap preserved verbatim
  - Kernel immutable (core/engine.py locked)
  - Audit blocked on same-period comparator unavailable
- **Phase 61**: Bootstrap authorized (D-348) but not yet publicly executed; pending explicit `approve next phase` token
- **Next**: Data-level completeness patch for 274 C3 return cells + Method B sidecar integration

## Current Truth Surfaces

Use these surfaces together to understand the current system state:

### Static Truth
- **[top_level_PM.md](top_level_PM.md)** — long-lived product/system intent
- **[docs/decision log.md](docs/decision%20log.md)** — authoritative decision history
- **Active phase brief** — current phase scope and boundaries (e.g., `docs/phase_brief/phase60-brief.md`)

### Live Truth
- **[docs/context/current_context.md](docs/context/current_context.md)** — current active phase and blocked next step

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

# Run Phase 60 specific tests
pytest tests/test_phase60_*.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage**: All Phase 60 tests passing
- Preflight verification tests
- Governed audit runner tests
- Governed cube tests
- Blocked-audit review tests
- Documentation hygiene tests
- Closeout tests

## Phase 60 Deliverables

### Artifacts Generated

All artifacts in `data/processed/`:

1. **phase60_governed_cube.parquet** - Governed daily holdings/weight cube
2. **phase60_d340_preflight_*.json** - Preflight check results (PF-01..PF-06)
3. **phase60_d340_audit_*.status.txt** - Blocked audit evidence (274-cell gap preserved)
4. **phase60_d341_review_*.csv/json** - Formal blocked-audit review findings

### Validation

**Governance State**: Phase 60 closed as CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD
- 274-cell C3 comparator gap preserved verbatim
- Kernel immutable per D-347
- Phase 61 bootstrap authorized (D-348) but not yet executing publicly

## Documentation

### Phase 60
- **`docs/phase_brief/phase60-brief.md`** - Phase 60 specification
- **`docs/handover/phase60_handover.md`** - CEO handover memo
- **`docs/handover/phase60_execution_handover_20260318.md`** - Execution handover

### General
- **`docs/decision log.md`** - Architecture decision records (D-01 through D-348)
- **`docs/context/bridge_contract_current.md`** - Current PM/planner bridge

## Current System Status

- **Multi-Sleeve Research Kernel**: Phase 56/57/58/59/60 evidence surfaces preserved as immutable SSOT
- **Governance Stack**: 348 architecture decisions
- **Blockers**: 274-cell C3 comparator gap; Phase 61 pending explicit approval

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

**Last Updated**: 2026-03-20
**Phase**: 60 (Closed as Blocked Evidence-Only Hold)
**Status**: Phase 60 CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD ✅ | Phase 61 Bootstrap Pending (D-348) 🔄
