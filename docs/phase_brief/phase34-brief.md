# Phase 34: Factor Attribution Analysis

**Status**: Planning
**Started**: 2026-03-05
**Owner**: System
**Phase**: 34 (Alpha Decomposition & Causal Clarity)

## Objective

Build causal clarity on alpha drivers by decomposing portfolio returns into factor contributions and analyzing performance by regime. This provides decision leverage for subsequent optimization phases (sizing, risk budget, rebalancing).

## Context

Phase 33B delivered:
- Async drift monitoring with escalation policy
- Production-hardened alert lifecycle management
- Telemetry integration for observability

Current gap: No systematic understanding of which factors drive alpha performance in different market regimes. Operators cannot answer:
- Which signals are working vs failing?
- How does factor performance vary by regime (GREEN/YELLOW/AMBER/RED)?
- What is the stability of factor information coefficients (IC)?
- Are factor contributions consistent with expectations?

## Strategic Value

Factor attribution is the **highest decision leverage** next step because it:

1. **Informs Position Sizing** (Phase 35): Identify high-IC factors to overweight
2. **Informs Risk Budget** (Phase 36): Quantify factor risk contributions for allocation
3. **Informs Rebalancing** (Phase 37): Understand regime-dependent factor decay rates
4. **Validates Alpha Engine**: Confirms which signals contribute to returns vs noise

**Recommended Sequence**: Attribution → Sizing → Risk Budget → Rebalancing

## Roadmap Lock (Phases 34-40)

Sequence confirmation from current Rectification Sprint through "Done Done":

1. **Phase 34**: Factor Attribution + Behavior Ledger (prove causal and behavioral edge)
2. **Phase 35**: Targeted feature engineering (conditional, only if Phase 34 instability detected)
3. **Phase 36**: Sizing, risk, rebalancing mechanics
4. **Phase 37**: Evidence Gate cost/friction simulation vs latest baseline
5. **Phase 38**: Execution microstructure reintegration (fail-closed path)
6. **Phase 39**: Governed shadow deployment (event-based graduation gate)
7. **Phase 40**: Terminal institutional grade ("Done Done")

This sequence remains aligned with AGENTS Evidence Gate policy: no new risk/execution layer ships without delta metrics vs latest baseline in the same window/cost/simulation path.

## Resolved Ambiguities (Patched 2026-03-05)

### A1) Phase 34 Threshold Method (Behavior Ledger)

Adopted method: **Bootstrap confidence-interval gate (Method B)**.

Rationale: fixed regime-percentage thresholds are vulnerable to sample-size artifacts in rare regimes.

Hard gate:
- Lower bound of the **95% bootstrap CI** for `Patience Gain` must be `> 0`.
- Lower bound of the **95% bootstrap CI** for `Premature Exit Drag` must be `> 0`.

Definitions:
- `Patience Gain = CAGR(wait_rule_entries) - CAGR(immediate_entries)`
- `Premature Exit Drag = return_if_held_to_rule_exit - actual_realized_return`

### A2) Phase 39 Shadow Graduation Method

Adopted method: **Event-based graduation (Method B)**.

Graduation gates (all mandatory):
- Minimum trade count `N` reached (configured before shadow starts)
- Drift false-positive rate `< X%` over the shadow window
- **Zero Severity-1 SRE incidents**

### A3) Phase 40 Throttle Aggressiveness Method

Adopted method: **Rule-based stepped mapping (Method A)**.

Rationale: explicit step-down mapping by regime/drift flags is auditable and operationally governable; black-box throttle optimization is deferred.

### A4) Triage Injection for Current Rectification Sprint

**Rank 1 (Urgent, immediate in current sprint)**:
- Add scheduled-maintenance blackout handling in `core/data_orchestrator.py` and `execution/microstructure.py`.
- Detect provider maintenance conditions (for example HTTP `503`, explicit maintenance flags, and timeout signatures tied to maintenance windows).
- Fail closed: park engine safely, emit clean terminal state (`exit code 0` for planned blackout), and sleep until the maintenance window expires.
- Prevent infinite retry storms/log flooding during known maintenance windows (for example Saturday, 2026-03-07).

**Rank 2 (Critical but deferred)**:
- Institutional-grade screener/price foundation swap is **Phase 34 Step 0 prerequisite** (before attribution math).
- Do not execute data-foundation migration inside current status-red rectification closure.
- Once fail-closed rectification is complete, run data-foundation migration first, then execute attribution/behavior ledger.

## Acceptance Criteria

### Core Attribution Logic
- [ ] Factor IC computed for each signal across rolling windows
- [ ] Regime-conditional IC analysis (GREEN/YELLOW/AMBER/RED regimes)
- [ ] Contribution decomposition: `total_return = Σ(factor_weight × factor_return)`
- [ ] Attribution report with factor performance by regime
- [ ] Historical IC stability tracking (rolling 60-day windows)

### Success Metrics
- [ ] Factor IC stability > 0.02 (statistically significant signal)
- [ ] Regime hit-rate > 70% (correct regime classification)
- [ ] Contribution R² > 0.5 (explained variance by factors)
- [ ] IC consistency: Spearman rank correlation > 0.3 across windows

### Behavior Ledger Gate (Mandatory Before Phase 35/36)
- [ ] Patience Gain computed and bootstrapped (95% CI)
- [ ] Premature Exit Drag computed and bootstrapped (95% CI)
- [ ] `CI95_lower(Patience Gain) > 0`
- [ ] `CI95_lower(Premature Exit Drag) > 0`
- [ ] Holding Adherence Ratio distribution published by regime/horizon
- [ ] Signal Capture Ratio distribution published by regime/horizon

### Shadow/Throttle Forward Gates (Phases 39-40)
- [ ] Phase 39 graduation is event-gated (`N` trades, false-positive `< X%`, zero Sev-1)
- [ ] Phase 40 throttle policy is explicit rule-based stepped mapping (auditable table)

### Validation
- [ ] Attribution sums to total portfolio return (accounting identity)
- [ ] Factor contributions align with expected signs (quality → positive, etc.)
- [ ] Regime-conditional IC shows expected patterns (quality works in GREEN, fails in RED)
- [ ] No spurious correlations (IC stability test across subperiods)

### Deliverables
- [ ] `strategies/factor_attribution.py` - Attribution engine
- [ ] `scripts/attribution_report.py` - Report generator
- [ ] `views/attribution_view.py` - Dashboard tab
- [ ] `tests/test_factor_attribution.py` - Test suite
- [ ] `data/processed/phase34_attribution_report.csv` - Historical attribution
- [ ] `data/processed/phase34_behavior_ledger.csv` - Patience/holding diagnostics with CI bounds

### Rectification Sprint Carry-Forward Deliverables (Rank 1)
- [ ] `core/data_orchestrator.py` - scheduled maintenance blackout taxonomy and fail-closed handling
- [ ] `execution/microstructure.py` - maintenance-aware park/sleep behavior with bounded retries
- [ ] `tests/test_data_orchestrator_maintenance.py` - 503/maintenance classification + blackout behavior
- [ ] `tests/test_execution_microstructure_maintenance.py` - no retry storm, clean parked state
- [ ] runbook update documenting blackout window handling and restart semantics

## Technical Design

### Attribution Framework

**Brinson-Fachler Attribution Model** (industry standard):
```
Total Return = Allocation Effect + Selection Effect + Interaction Effect

Where:
- Allocation Effect = Σ(w_p - w_b) × r_b  (sector/factor weight decisions)
- Selection Effect = Σ w_b × (r_p - r_b)  (stock selection within sectors)
- Interaction Effect = Σ(w_p - w_b) × (r_p - r_b)  (combined effect)
```

**Factor-Based Attribution** (for our use case):
```
Portfolio Return = Σ(factor_exposure_i × factor_return_i) + residual

Where:
- factor_exposure_i = portfolio weight on factor i
- factor_return_i = return of factor i in period
- residual = unexplained return (idiosyncratic)
```

### Factor Definitions

**Existing Factors** (from Phase 21 scorecard):
1. **Quality**: ROIC, gross margin, operating margin
2. **Growth**: Revenue growth, EBITDA growth
3. **Momentum**: Price momentum, earnings momentum
4. **Value**: P/E, P/B, EV/EBITDA
5. **Cyclical Exposure**: Beta to macro factors

**Factor Returns Calculation**:
- Long-short portfolio: Long top quintile, short bottom quintile
- Equal-weighted within quintiles
- Daily rebalancing (or weekly for stability)

### Information Coefficient (IC)

**Definition**: Spearman rank correlation between factor scores and forward returns

```python
IC_t = spearman_corr(factor_scores_t, forward_returns_{t+1})
```

**Interpretation**:
- IC > 0.05: Strong predictive signal
- IC > 0.02: Statistically significant
- IC < 0.02: Weak/noise
- IC < 0: Contrarian signal (investigate)

**Rolling IC**: Compute IC over rolling 60-day windows to track stability

### Regime-Conditional Analysis

**Regime Classification** (from existing regime manager):
- GREEN: Low volatility, positive trend
- YELLOW: Moderate volatility, uncertain trend
- AMBER: High volatility, negative trend
- RED: Crisis conditions

**Regime-Conditional IC**:
```python
IC_regime = {
    "GREEN": IC computed on GREEN days only,
    "YELLOW": IC computed on YELLOW days only,
    "AMBER": IC computed on AMBER days only,
    "RED": IC computed on RED days only,
}
```

**Expected Patterns**:
- Quality factors: High IC in GREEN, low IC in RED
- Momentum factors: High IC in GREEN/YELLOW, reversal in RED
- Value factors: Low IC in GREEN, high IC in AMBER/RED (mean reversion)

### Implementation Architecture

```
FactorAttributionEngine (strategies/factor_attribution.py)
  ├─ compute_factor_returns() → DataFrame[date, factor, return]
  ├─ compute_factor_ic() → DataFrame[date, factor, ic, p_value]
  ├─ compute_regime_conditional_ic() → DataFrame[regime, factor, ic]
  ├─ decompose_portfolio_return() → DataFrame[date, factor, contribution]
  └─ validate_attribution() → bool (accounting identity check)

AttributionReport (scripts/attribution_report.py)
  ├─ load_portfolio_history()
  ├─ load_factor_scores()
  ├─ run_attribution_engine()
  ├─ generate_summary_stats()
  └─ export_to_csv()

AttributionView (views/attribution_view.py)
  ├─ IC heatmap by factor × regime
  ├─ Rolling IC time series
  ├─ Factor contribution waterfall chart
  ├─ Regime hit-rate gauge
  └─ Contribution R² metric
```

### Data Requirements

**Phase 34 Step 0 Prerequisite (deferred Rank 2):**
- Institutional-grade screener/price source replacement completed and validated.
- Survivorship-bias controls confirmed before attribution and behavior-ledger runs.

**Inputs**:
- Portfolio weights history (from backtest/live trading)
- Factor scores history (from company scorecard)
- Forward returns (1-day, 5-day, 20-day)
- Regime classifications (from regime manager)

**Outputs**:
- `data/processed/phase34_factor_ic.csv` - IC time series
- `data/processed/phase34_regime_ic.csv` - Regime-conditional IC
- `data/processed/phase34_attribution.csv` - Factor contributions
- `data/processed/phase34_summary.json` - Summary statistics

## Testing Strategy

### Unit Tests
- `test_factor_attribution.py`: IC computation, contribution decomposition, accounting identity
- Mock factor scores and returns for deterministic tests
- Test edge cases: zero returns, missing data, single-factor portfolios

### Integration Tests
- `test_attribution_integration.py`: Full pipeline with real backtest data
- Validate attribution sums to total return
- Test regime-conditional IC computation
- Verify IC stability across subperiods

### Validation Tests
- `test_attribution_validation.py`: Statistical properties
- IC significance tests (t-test, bootstrap)
- Contribution R² threshold checks
- Regime hit-rate validation

## Rollback Plan

If attribution reveals unexpected results:
1. Validate factor score quality (check for data issues)
2. Verify return calculation (corporate actions, splits)
3. Check regime classification accuracy
4. Review attribution methodology (Brinson vs factor-based)
5. Document findings as "Known Limitations" in SAW report

## Dependencies

- Phase 21 (Company Scorecard) for factor scores
- Phase 15 (Alpha Engine) for portfolio weights history
- Phase 13 (Regime Manager) for regime classifications
- Phase 18 (TRI/Returns) for clean return data
- Rectification Sprint (Phase 32 patch) maintenance-blackout fail-closed controls completed
- Institutional data-foundation migration completed (Phase 34 Step 0) before attribution execution

## Risks

1. **Low IC Across All Factors**: Signals may be weak/noisy
   - Mitigation: Document as baseline, inform Phase 35 sizing decisions

2. **Regime Misclassification**: Incorrect regime labels corrupt conditional IC
   - Mitigation: Validate regime hit-rate > 70% threshold

3. **Attribution Residual Too Large**: Factors don't explain returns
   - Mitigation: Investigate idiosyncratic risk, consider additional factors

4. **Maintenance-window retry storms** (if Rank 1 patch not completed)
   - Mitigation: ship blackout taxonomy + bounded retries before rectification close

5. **Data foundation bias leakage** (if Rank 2 prereq skipped)
   - Mitigation: enforce institutional data swap as Step 0 gate before attribution

## Success Metrics

- Factor IC stability > 0.02 for at least 3 factors
- Regime hit-rate > 70% (correct classification)
- Contribution R² > 0.5 (factors explain >50% of variance)
- IC consistency: Spearman rank correlation > 0.3 across rolling windows

## Next Steps

1. Complete Rank 1 maintenance-blackout patch in current rectification sprint (must-do before sprint close)
2. Execute Phase 34 Step 0 data-foundation migration gate (deferred until rectification is stable)
3. Implement FactorAttributionEngine class
4. Add IC computation with bootstrap CI gates for behavior-ledger metrics
5. Implement regime-conditional IC analysis
6. Create attribution + behavior-ledger report generator
7. Add dashboard views for attribution and behavior-ledger diagnostics
8. Comprehensive test suite (unit + integration + validation)

## Implementation Tasks

### Task 1: Factor Attribution Engine
- Implement `FactorAttributionEngine` class
- Add `compute_factor_returns()` method
- Add `compute_factor_ic()` with significance tests
- Add `compute_regime_conditional_ic()` method
- Add `decompose_portfolio_return()` method
- Add `validate_attribution()` accounting identity check

### Task 2: Attribution Report Generator
- Create `scripts/attribution_report.py`
- Load portfolio weights and factor scores
- Run attribution engine
- Generate summary statistics
- Export to CSV/JSON

### Task 3: Dashboard Integration
- Create `views/attribution_view.py`
- Add IC heatmap (factor × regime)
- Add rolling IC time series chart
- Add factor contribution waterfall chart
- Add regime hit-rate gauge
- Add contribution R² metric

### Task 4: Testing
- Create `tests/test_factor_attribution.py`
- Test IC computation correctness
- Test contribution decomposition
- Test accounting identity (sum = total return)
- Test regime-conditional IC
- Integration test with real backtest data

### Task 5: Validation & Documentation
- Run attribution on Phase 21 backtest data
- Validate IC stability > 0.02 threshold
- Validate regime hit-rate > 70%
- Validate contribution R² > 0.5
- Document findings in SAW report

## Production Deployment

To enable attribution in production:

```bash
# Run attribution report
python scripts/attribution_report.py \
  --start-date 2022-01-01 \
  --end-date 2024-12-31 \
  --output data/processed/phase34_attribution_report.csv

# View in dashboard
# Navigate to "📊 Attribution" tab
```

## Implementation Status

**Status**: Planning (awaiting approval)

**Estimated Timeline**: 2-3 days
- Day 1: Attribution engine + IC computation
- Day 2: Report generator + dashboard view
- Day 3: Testing + validation + documentation

---

**Signed**: Claude Opus 4.6
**Date**: 2026-03-05
**Phase**: 34 - Factor Attribution Analysis
**Status**: Planning
