# Quant Trading System

A production-grade quantitative trading system with factor-based portfolio construction, regime-aware risk management, and real-time performance attribution.

## Overview

This system implements a multi-phase quantitative trading strategy with:
- **Factor Attribution Analysis** - IC-based factor evaluation with regime conditioning
- **Risk Management** - Maintenance blackout windows, drain strategies, and transient backoff
- **Dashboard** - Real-time monitoring with attribution views and performance metrics
- **Orchestration** - Event-driven architecture with retry/backoff mechanisms

## Project Status

**Current Phase**: Phase 35 Closed and Pivoted 🔄
- **Phase 34**: Attribution pipeline production-ready ✅
  - All 17 tests passing
  - Accounting identity verified (error < 1e-14)
- **Phase 35 (candidate/reweight branch)**: Closed due to blockers 🚫
  - Invalid experiments (missing data columns)
  - Model misspecification (R² = -17.85)
  - Turnover crisis (90-100% daily)
- **Next**: Data engineering + model fixes, or pivot to Rule of 100 integration

## Current Truth Surfaces

Use these surfaces together to understand the current system state:

### Static Truth
- **[top_level_PM.md](top_level_PM.md)** — long-lived product/system intent
- **[docs/decision log.md](docs/decision%20log.md)** — authoritative decision history
- **Active phase brief** — current phase scope and boundaries (e.g., `docs/phase_brief/phase59-brief.md`)

### Live Truth
- **[docs/context/current_context.md](docs/context/current_context.md)** — current active phase and blocked next step

### Bridge Truth
- **[docs/context/bridge_contract_current.md](docs/context/bridge_contract_current.md)** — translates recent technical closeout state back into PM/planner language and names the next system-level decision

### Evidence Truth
- **[docs/context/done_checklist_current.md](docs/context/done_checklist_current.md)** — machine-checkable done criteria for current phase
- **[docs/context/multi_stream_contract_current.md](docs/context/multi_stream_contract_current.md)** — cross-stream coordination map (Backend, Frontend/UI, Data, Docs/Ops)
- **[docs/context/post_phase_alignment_current.md](docs/context/post_phase_alignment_current.md)** — post-phase stream status update and bottleneck analysis

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

- **`scripts/attribution_report.py`** - Generate Phase 34 attribution artifacts
- **`scripts/generate_phase34_factor_scores.py`** - Materialize factor scores
- **`scripts/generate_phase34_weights.py`** - Generate target weights

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_factor_attribution.py -v
pytest tests/test_attribution_integration.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage**: 17/17 tests passing
- Factor attribution: 5 tests
- Behavior ledger: 5 tests
- Attribution validation: 6 tests
- Integration: 1 test

## Phase 34 Deliverables

### Artifacts Generated

All artifacts in `data/processed/`:

1. **phase34_factor_ic.csv** (228 KB, 3,012 rows)
   - Long-format IC values for 4 factors across 753 dates
   - Schema: `['date', 'factor', 'ic', 'p_value', 'n_assets']`

2. **phase34_regime_ic.csv** (776 bytes)
   - Regime-conditional IC statistics
   - Schema: `['regime', 'factor', 'mean_ic', 'std_ic', 'n_obs']`

3. **phase34_attribution.csv** (89 KB, 684 rows)
   - Performance attribution with accounting identity
   - Schema: `['portfolio_return', 'residual', '*_contribution']`

4. **phase34_behavior_ledger.csv** (32 KB)
   - Weight changes and regime transitions
   - Schema: `['date', 'regime', 'regime_changed', 'total_weight_change', 'n_positions']`

5. **phase34_summary.json** (529 bytes)
   - Summary statistics: IC stability, regime hit-rates, R²

### Validation

**Accounting Identity**: Perfect floating-point precision
```
Mean error: 3.05e-16
Max error: 1.42e-14
sum(contributions) + residual = portfolio_return ✅
```

## Documentation

### Phase 34
- **`docs/PHASE34_CONDITIONAL_APPROVAL.md`** - Final approval status
- **`docs/PHASE34_FINAL_VERIFICATION.md`** - Engineering verification
- **`docs/phase_brief/phase34-brief.md`** - Phase 34 specification

### Phase 35
- **`docs/PHASE35_CLOSURE.md`** - Closure report (candidate/reweight branch blocked)
- **`docs/saw_reports/saw_phase35_round1.md`** - SAW report with BLOCK verdict
- **`docs/phase_brief/phase35-brief.md`** - Phase 35 specification

### General
- **`docs/decision log.md`** - Architecture decision records
- **`docs/context/bridge_contract_current.md`** - Current PM/planner bridge from technical execution back to system-level planning

## Performance Metrics

Current factor performance (Phase 34):
- Mean IC: -0.002 (target: > 0.02)
- Contribution R²: -0.268 (target: > 0.5)
- Regime hit-rates: GREEN 25%, AMBER 0%, RED 50% (target: > 70%)

**Note**: Engineering pipeline is production-ready. Performance improvement planned for Phase 35 (Targeted Feature Engineering).

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

**Last Updated**: 2026-03-07
**Phase**: 35 (Closed and Pivoted)
**Status**: Phase 34 Engineering Complete ✅, Phase 35 Candidate/Reweight Branch Blocked 🚫
