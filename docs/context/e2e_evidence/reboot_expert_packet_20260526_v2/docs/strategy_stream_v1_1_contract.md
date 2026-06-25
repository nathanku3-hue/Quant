# Strategy Stream v1.1: Three-Object Data Contract

Date: 2026-05-12
Status: Research candidate — not promoted to runtime
Authority: Approved expert contract

## Three Objects

### Object 1: v1 Frozen Baseline (PRODUCTION)

| Property | Value |
|----------|-------|
| Source module | `strategies/rule100_softmax.py` |
| Audit script | `scripts/rule100_softmax_v1_audit.py` |
| Score formula | `0.75 * (factor_positive_count - 3).clip(0) + 0.25 * technical_quality` |
| Sizing | softmax(scores / tau) * budget, capped at 15% |
| Mutation | None — frozen ordinal audit baseline |

### Object 2: v1.1 Research Candidate (RESEARCH ONLY)

| Property | Value |
|----------|-------|
| Source module | `strategies/rule100_softmax_v1_1.py` |
| Audit script | `scripts/rule100_softmax_v1_1_audit.py` |
| Current artifacts | `data/processed/rule100_softmax_v1_1_comparison.csv`, `data/processed/rule100_softmax_v1_1_summary.json` |
| Mutation | None — does NOT touch v1 artifacts, lifecycle log, position memory, or UI |

There is no active v1.1 history artifact. Any stale
`data/processed/rule100_softmax_v1_1_history.csv` is retired by the audit
script to `data/processed/rule100_softmax_v1_1_history.retired.csv`.

**v1.1 approved formula:**

```
base_score =
    0.50 * factor_strength_continuous
  + 0.35 * technical_quality_continuous
  + 0.15 * hold_intact
  - 0.10 * thesis_staleness_penalty

raw_weight = budget * softmax(base_score / tau)
target_weight = min(0.15, raw_weight) * lifecycle_state_multiplier
cash = 1.0 - sum(target_weight)
```

**Lifecycle multipliers (applied post-softmax, no redistribution):**

| State | Multiplier |
|-------|-----------|
| BUY / HOLD | 1.00 |
| TRIM | 0.75 |
| TIGHTEN | 0.50 |
| EXIT / hard stop / trend veto | 0.00 |

**Factor strength (4 approved groups, cross-sectional percentile rank):**

| Group | Column(s) |
|-------|-----------|
| Demand | z_demand |
| Inventory/supply | z_inventory_quality_proxy |
| Moat/pricing | z_moat |
| Capital discipline | capital_cycle_score, quality_composite |

Coverage is counted by approved factor group, not by raw column. Alternate
columns inside a group contribute at most one value. Missing groups shrink
factor strength toward neutral:

```
coverage_i = present_group_count_i / 4
factor_strength_i =
    mean_available_group_percentile_i * coverage_i
  + 0.50 * (1 - coverage_i)
```

If zero groups are present, `factor_strength_i = 0.50`.

**Technical quality (4 approved sub-groups, each [0,1]):**

| Sub-group | Inputs | Method |
|-----------|--------|--------|
| Momentum | resid_mom_60d, rel_strength_60d | Cross-sectional percentile rank, averaged |
| Trend health | dist_sma20, trend_veto | Proximity (1 - dist/0.10).clip(0,1), zeroed on veto |
| Stretch | rsi_14d | Peak at RSI 55, linear decay to 0 at 20 or 85 |
| Vol/liquidity | yz_vol_20d | Inverted percentile rank (low vol = high quality) |

**Staleness penalty:**
- `min(days_since_factor_positive_change / 120, 1.0)`
- Uses stale-refresh age only (not raw hold age)

### Object 3: PIT Comparison Artifacts

| Property | Value |
|----------|-------|
| Comparison location | `data/processed/rule100_softmax_v1_1_comparison.csv` |
| Summary location | `data/processed/rule100_softmax_v1_1_summary.json` |
| Content | v1.1 score, target weight, current weight delta, lifecycle multiplier, four-group coverage counts |

## Hard Exclusions (from score inputs)

- event_weight, current_weight, softmax_v1_target_weight, kelly_weight
- buy_sell, raw hold_days, raw age_penalty
- comparison/output columns
- undocumented restated accounting fields

## Same-Window Results (2026-05-11)

```
v1 (frozen):  AMAT=10.00%, LRCX=10.00%, TSM=0.00%, GROSS=20%
v1.1 tau=0.75: AMAT=10.01%, LRCX=9.99%,  TSM=0.00%, GROSS=20%
v1.1 tau=1.0:  AMAT=10.00%, LRCX=10.00%, TSM=0.00%, GROSS=20%
v1.1 tau=1.25: AMAT=10.00%, LRCX=10.00%, TSM=0.00%, GROSS=20%
```

Minimal differentiation in current window: only 2 eligible names with near-identical scores (0.572449 vs 0.571679). Tau has negligible impact with 2 names. Differentiation will emerge with more eligible names or wider score dispersion.

## Promotion Gate (Hard Blockers)

1. ☐ Same universe, same dates, same PIT availability
2. ☐ Same lifecycle state machine, same budget, same 15% cap
3. ☐ Same costs/slippage, same cash treatment
4. ☐ No PIT leak
5. ☐ No undocumented restated feature
6. ☐ Net return >= v1
7. ☐ Risk-adjusted return >= v1
8. ☐ Max drawdown not worse by > max(100bps, 5% relative)
9. ☐ Annualized turnover below threshold
10. ☐ No negative cash
11. ☐ No unexplained target-event divergence
12. ☐ Walk-forward evidence present

## P1 Closure Criteria

1. ✅ v1.1 scoring module matches approved expert contract
2. ✅ Lifecycle multiplier applied post-softmax (no redistribution)
3. ✅ Factor strength uses 4 approved groups with full cross-section percentile and neutral missing-group shrinkage
4. ✅ Technical quality uses 4 approved sub-groups
5. ✅ Staleness uses stale-refresh age only (not raw hold age)
6. ✅ Hard exclusions enforced (no excluded columns in score inputs)
7. ✅ v1 tests (13) pass unchanged
8. ✅ v1.1 tests (12) pass
9. ✅ v1.1 active artifact contract is comparison CSV + summary JSON only; stale history is retired
10. ✅ Real `AppTest.from_file("dashboard.py")` captures the Policy Target Timeline regression for TSM 2026-05-11

## P2 Closure Criteria (Required Before Promotion)

1. ☐ Multi-date PIT replay (minimum 3 calendar years or shadow comparator)
2. ☐ Return attribution vs v1
3. ☐ Coefficient sensitivity grid (small, locked)
4. ☐ Freeze tau choice
5. ☐ Walk-forward evidence
