# Quant Trading System

A production-grade quantitative trading system with factor-based portfolio construction, regime-aware risk management, and real-time performance attribution.

## Overview

This system implements a multi-phase quantitative trading strategy with:
- **Factor Attribution Analysis** - IC-based factor evaluation with regime conditioning
- **Risk Management** - Maintenance blackout windows, drain strategies, and transient backoff
- **Dashboard** - Real-time monitoring with attribution views and performance metrics
- **Orchestration** - Event-driven architecture with retry/backoff mechanisms

## Project Status

**Current Phase**: Phase 64.1 closeout hygiene — COMPLETE; Phase F Candidate Registry approved, not started
- **D-353 Status**: Complete for source policy, manifest enforcement, provider ports, data readiness audit, and minimal validation lab
  - validation reports now require manifests
  - yfinance is quarantined as Tier 2 discovery/convenience data
  - Alpaca is operational/paper market data only; live orders remain blocked
- **R64.1 Status**: Dependency hygiene closed with `alpaca-py==0.43.4`; `pip check` passes
- **Open Operational Risk**: primary S&P sidecar is stale through 2023-11-27; yfinance remains quarantined legacy debt
- **Next**: Phase F Candidate Registry only. See `docs/phase_brief/phase65-brief.md`.

## Current Truth Surfaces

Use these surfaces together to understand the current system state:

### Static Truth
- **[top_level_PM.md](top_level_PM.md)** — long-lived product/system intent
- **[docs/decision log.md](docs/decision%20log.md)** — authoritative decision history
- **Active phase brief** — current phase scope and boundaries (e.g., `docs/phase_brief/phase64-brief.md`)

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

# Run D-353 provenance + validation gate tests
pytest tests/test_provenance_policy.py tests/test_provider_ports.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_execution_controls.py -v

# Run R64.1 dependency hygiene tests
pytest tests/test_dependency_hygiene.py tests/test_execution_controls.py tests/test_provider_ports.py -v
python -m pip check

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage**: D-353 targeted tests and packet hygiene checks passing
- Provenance manifest and promotion-source gates
- Provider-port and yfinance quarantine tests
- Data readiness audit tests
- Minimal validation lab tests
- Alpaca paper/live boundary tests
- Alpaca SDK dependency hygiene tests

## Phase 64 / D-353 Deliverables

### Artifacts Generated

Key artifacts in `data/processed/`:

1. **data_readiness_report.json** - Daily US-equity paper-alert readiness audit
2. **data_readiness_report.json.manifest.json** - Manifest for the readiness audit
3. **minimal_validation_report.json** - OOS, walk-forward, regime, permutation, and bootstrap validation report
4. **minimal_validation_report.json.manifest.json** - Manifest for the validation report
5. **phase56_pead_evidence.csv.manifest.json** - Canonical input manifest for PEAD evidence

### Validation

**Governance State**: D-353 complete for provenance + validation gates
- data readiness audit returns `ready_for_paper_alerts = true`
- minimal validation lab passes on existing PEAD evidence
- live trading, broker automation, and Tier 2 promotion remain blocked

## Documentation

### Phase 64 / D-353
- **`docs/architecture/data_source_policy.md`** - Data source tiers and executable invariants
- **`docs/phase_brief/phase64-brief.md`** - D-353 accelerated provenance + validation brief
- **`docs/phase_brief/phase65-brief.md`** - Phase F Candidate Registry approval brief
- **`docs/handover/phase64_handover.md`** - PM handover for provenance + validation gates

### General
- **`docs/decision log.md`** - Architecture decision records (D-01 through D-353)
- **`docs/context/bridge_contract_current.md`** - Current PM/planner bridge

## Current System Status

- **Multi-Sleeve Research Kernel**: Prior evidence surfaces preserved as immutable SSOT, with D-353 provenance gates layered on top
- **Governance Stack**: 353 architecture decisions
- **Remaining Risks**: yfinance quarantine migration, stale S&P sidecar provenance, and blocked live execution

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

**Last Updated**: 2026-05-09
**Phase**: 64 accelerated provenance + validation gates
**Status**: D-353 Complete | Paper-alert readiness gates active
