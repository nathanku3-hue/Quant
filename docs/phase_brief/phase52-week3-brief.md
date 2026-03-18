# Phase 52 Week 3: SMA200 Trend Filter

Current Governance State: Phase 52 Week 3 (SMA200 trend overlay) complete. Runtime surface: `backtests/`, `scripts/`, `tests/`, `docs/`. Goal completed: layer SMA200 trend filter on top of Week 2b best config (Trial 14) to test orthogonal "when to be in market" dimension.

**Status**: COMPLETED - FINAL ENDPOINT LOCKED UNDER D-284
**Created**: 2026-03-13
**Authority**: D-282 (Week 3 authorized despite Week 2b "HOLD" status)
**Execution Authorization**: CLOSED. Week 3 completed and is now the final Phase 52 endpoint under D-284. No Week 4 enhancement is opened by this brief.

**Closeout Update (2026-03-14)**: Research-only A/B adjudication selected **B** overall. Week 3 is accepted as the Phase 52 endpoint. Any future sector-cap test or modular overlay work requires separate authorization with explicit holdout design and search-control accounting. See `docs/handover/phase52_week3_research_closeout_20260314.md`.

**Verification Update (2026-03-14 late)**: The exact-RV replay and rewritten Week 3 artifact are aligned, focused Week 3 tests now pass `17/17`, the repo-wide regression reached `[100%]`, the launch smoke bundle passed, and local Reviewer C verification cleared `CHK-PH-04` on the final artifact set. Phase 52 is closeout-complete and remains locked at Week 3 under `D-284`.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Current Strategy Crisis Validation with Remedial Enhancements
- **L2 Active Streams**: Backend | Data | Docs/Ops
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Backend
- **Active Stage Level**: L3
- **Current Stage**: Final Verification / Closed
- **Planning Gate Boundary**: Closed. Historical execution scope was `backtests/phase52_week3_sma200.py`, focused tests, SMA200 computation, trend × regime logic, and same-round docs updates. Week 4+ enhancements remain out of scope.
- **Owner/Handoff**: Codex implementer -> CEO review
- **Acceptance Checks**: `CHK-P52-W3-01`..`CHK-P52-W3-08`
- **Primary Next Scope**: Maintain Week 3 as the locked Phase 52 endpoint and require separate authorization before any future cap-constraint or modular overlay experiment [94/100: research evidence]

## 1. Problem Statement
- **Context**: Phase 52 Week 2b tightened grid delivered Trial 14 (RV=25%, exp=0.4, top_n=5) with +22.68% improvement in 2008 GFC vs Week 1 baseline. However, full-period metrics missed acceptance (Sharpe 0.644 vs target 0.65, recovery 297 days vs target 240). CEO authorized Week 3 under D-282 to test if SMA200 trend filter can provide incremental value via orthogonal "when to be in market" dimension.
- **User Impact**: The repo can now test if a simple SMA200 trend filter (SPY-based) improves full-period metrics while preserving crisis protection from Trial 14's regime filter. Orthogonal design ensures clean attribution: regime filter = "how much exposure in crisis", trend filter = "when to be in market".

## 2. Goals & Non-Goals
- **Goal**: Layer SMA200 trend filter on Trial 14 baseline (RV=25%, exp=0.4, top_n=5).
- **Goal**: Implement orthogonal exposure formula: `final_exposure = trend_multiplier × regime_exposure`.
- **Goal**: Measure delta vs Trial 14: Sharpe, Max DD, recovery time, crisis performance.
- **Goal**: Apply dual acceptance criteria: 3/4 absolute thresholds OR 2/3 delta guardrails vs Trial 14.
- **Non-Goal**: Modify regime filter logic (locked at Trial 14 parameters).
- **Non-Goal**: Implement sector caps or drawdown deleveraging under this brief.
- **Non-Goal**: Change 4-factor scorecard, cost model, or portfolio construction logic.

## 3. Trial 14 Baseline (Week 2b Governed Endpoint)

### Trial 14 Configuration
```python
rv_threshold: 0.25  # 25% annualized realized vol
defensive_exposure: 0.4  # 40% exposure in high-vol regime
defensive_top_n: 5  # 5 stocks in defensive mode
normal_exposure: 1.0  # Full exposure in normal regime
normal_top_n: 5  # 5 stocks in normal mode
```

### Trial 14 Results (2007-2024)
```
Full Period:
  Sharpe: 0.644 (target: >0.65) ✗ MISS
  Max DD: -67.60%
  CAGR: 15.89%
  Recovery: 297 days (target: <240 days) ✗ MISS

Crisis Periods:
  GFC 2008: Max DD -39.32% (vs Week 1: -60.69%) → +21.37% improvement ✓
  COVID 2020: Max DD -20.56% (vs Week 1: -27.97%) → +7.41% improvement ✓
  BEAR 2022: Max DD -54.71% (vs Week 1: -55.51%) → +0.80% improvement

Week 2b Status: 2/4 acceptance criteria met (crisis targets passed, full-period missed)
```

## 4. Week 3 SMA200 Trend Filter Design

### Orthogonal Exposure Formula
```python
# Two independent dimensions
trend_multiplier = 1.0 if SPY_price >= SPY_SMA200 else 0.5
regime_exposure = 0.4 if realized_vol > 0.25 else 1.0

# Final exposure (multiplicative)
final_exposure = trend_multiplier × regime_exposure

# Four possible states:
# 1. Normal market, uptrend: 1.0 × 1.0 = 1.0 (full exposure)
# 2. Crisis, uptrend: 1.0 × 0.4 = 0.4 (regime protection)
# 3. Normal market, downtrend: 0.5 × 1.0 = 0.5 (trend caution)
# 4. Crisis, downtrend: 0.5 × 0.4 = 0.2 (maximum defense)
```

### SMA200 Data Source
- **SPY**: permno=84398 from `prices.parquet`
- **Coverage**: 2000-01-03 to 2024-12-31 (full 2007-2024 backtest coverage)
- **SMA200**: 200-day simple moving average of SPY adj_close
- **Warmup**: First 200 days (2000-01-03 to 2000-09-22) used for SMA200 initialization

### Unchanged from Trial 14
- 4-factor equal-weight (momentum 0.25, quality 0.25, volatility 0.25, illiquidity 0.25)
- RV threshold: 25% (annualized)
- Defensive exposure: 0.4
- Defensive top_n: 5
- Transaction cost: 10bps
- Windows: 2007-2024

## 5. Week 3 Acceptance Criteria (Dual Gate)

### Absolute Thresholds (3/4 required)
| Criterion | Target | Week 1 Baseline | Trial 14 | Week 3 Goal |
|-----------|--------|----------------|----------|-------------|
| Max DD 2008 | <45% | -60.69% | -39.32% ✓ | Maintain or improve |
| Max DD 2020 | <25% | -27.97% | -20.56% ✓ | Maintain or improve |
| Sharpe 2007-2024 | >0.65 | 0.606 | 0.644 ✗ | Improve to >0.65 |
| Recovery Time | <240 days | 297 days | 297 days ✗ | Improve to <240 days |

### Delta Guardrails vs Trial 14 (2/3 required)
| Criterion | Target | Interpretation |
|-----------|--------|----------------|
| Sharpe Delta | ≥+0.05 | At least +0.05 improvement vs Trial 14 (0.644) |
| Max DD Delta | ≥-3% | At least -3% improvement (less negative = better) |
| Recovery Delta | ≥-30 days | At least -30 days improvement vs Week 1 (297 days) |

**Overall Week 3 Status**: PASS if (3/4 absolute) OR (2/3 delta)

**Rationale**: Dual gate allows Week 3 to pass if either:
1. Absolute thresholds met (proves crisis robustness + full-period quality)
2. Delta guardrails met (proves incremental value vs Trial 14, even if absolute targets missed)

## 6. Week 3 Deliverables
- `backtests/phase52_week3_sma200.py` (SMA200 trend filter implementation)
- `tests/test_phase52_week3_sma200.py` (focused tests: SMA200 computation, trend multiplier, orthogonality)
- `data/processed/phase52_week3/week3_sma200_results.json` (full-period + crisis metrics)
- `docs/handover/phase52_week3_trend_evidence.md` (delta attribution vs Trial 14)
- `docs/phase_brief/phase52-week3-brief.md` (this file)

## 7. Scope Boundaries (Week 3)
- **In scope**: SMA200 trend filter, orthogonal exposure formula, delta attribution vs Trial 14, dual acceptance criteria
- **Out of scope**: Regime filter modifications, sector caps, drawdown deleveraging, 4-factor changes, cost model changes, Week 4+ enhancements

## 8. Acceptance Checks (Week 3)
- `CHK-P52-W3-01` - SMA200 computed correctly from SPY prices (permno=84398), 200-day rolling mean
- `CHK-P52-W3-02` - Trend multiplier binary (1.0 or 0.5), based on SPY ≥ SMA200
- `CHK-P52-W3-03` - Final exposure formula implemented: trend_multiplier × regime_exposure
- `CHK-P52-W3-04` - Orthogonality validated: trend and regime filters operate independently
- `CHK-P52-W3-05` - Delta attribution measured: Sharpe, Max DD, recovery vs Trial 14
- `CHK-P52-W3-06` - Dual acceptance criteria applied: 3/4 absolute OR 2/3 delta
- `CHK-P52-W3-07` - Focused tests pass: 17/17 tests in test_phase52_week3_sma200.py
- `CHK-P52-W3-08` - Week 3 evidence summary published: docs/handover/phase52_week3_trend_evidence.md

## 9. Rollback Note
If Week 3 fails both acceptance gates (absolute AND delta), SMA200 trend filter provides insufficient incremental value. Options: (1) proceed to Week 4 sector caps as alternative enhancement, (2) require fundamental redesign, (3) accept Trial 14 as final configuration and close Phase 52.

## 10. Future Work (Not Authorized By This Brief)

Week 4 is **not** opened by this brief.

Research-only closeout under D-284 concluded that:

- Week 3 should be treated as the Phase 52 endpoint.
- The earlier "proceed to Week 4 sector caps" recommendation is superseded.
- A future isolated cap-constraint test may be considered only under a new authorization record with explicit holdout design and DSR/PBO-style search control.
- Broader modular boolean composition, tactical trims, or rotation overlays are deferred to a separately scoped future phase.
