# Quant Trading System

A production-grade quantitative trading system with factor-based portfolio construction, regime-aware risk management, and real-time performance attribution.

## Overview

This system implements a multi-phase quantitative trading strategy with:
- **Factor Attribution Analysis** - IC-based factor evaluation with regime conditioning
- **Risk Management** - Maintenance blackout windows, drain strategies, and transient backoff
- **Dashboard** - Real-time monitoring with attribution views and performance metrics
- **Orchestration** - Event-driven architecture with retry/backoff mechanisms

## Project Status

**Current Phase**: Phase 34 Complete ✅ (Conditional Approval)
- Attribution pipeline production-ready
- All 17 tests passing
- Accounting identity verified (error < 1e-14)
- Performance improvement deferred to Phase 35

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

- **`docs/PHASE34_CONDITIONAL_APPROVAL.md`** - Final approval status
- **`docs/PHASE34_FINAL_VERIFICATION.md`** - Engineering verification
- **`docs/phase_brief/phase34-brief.md`** - Phase 34 specification
- **`docs/decision log.md`** - Architecture decision records

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

**Last Updated**: 2026-03-06
**Phase**: 34 (Conditional Approval)
**Status**: Engineering Complete ✅, Performance Improvement Planned
