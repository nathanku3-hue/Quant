# Phase 12 Brief: FR-042 Truth-Table Verification Contract

## Objective
Lock FR-041 regime behavior to a strict historical truth table so crisis windows
stay defensive and calm windows do not remain permanently risk-off.

## Methodology
- Run `RegimeManager` across the full backtest calendar and persist daily outputs.
- Evaluate Governor state against fixed truth-table windows with explicit pass rules.
- Score behavioral quality with two performance metrics:
  - drawdown reduction vs baseline
  - recovery speed improvement vs baseline
- Baseline for comparison: SPY buy-and-hold curve built from the same date index.

## Strict Truth-Table Acceptance Windows
| Window (inclusive) | Expected Regime Behavior | Strict Pass Rule |
|---|---|---|
| 2008-10-01 to 2008-12-31 (2008 Q4) | RED crisis regime | `RED >= 80%` of sessions and `GREEN == 0%` |
| 2020-03-01 to 2020-03-31 (COVID crash month) | RED crisis regime | `RED >= 85%` of sessions and `GREEN == 0%` |
| 2022-01-01 to 2022-06-30 (2022 H1) | AMBER/RED risk regime | `(AMBER + RED) >= 75%` and `RED >= 15%` |
| 2017-01-01 to 2017-12-31 (calm guardrail year) | Mostly GREEN | `GREEN >= 75%` and `RED <= 5%` |
| 2023-11-01 to 2023-11-30 (transition month) | Transition toward GREEN | `GREEN(last 10 sessions) > GREEN(first 10 sessions)` and `RED <= 20%` |

## Performance Metrics
- Drawdown reduction:
  - `dd_reduction_pct = (abs(max_dd_baseline) - abs(max_dd_candidate)) / abs(max_dd_baseline) * 100`
  - Acceptance: `dd_reduction_pct > 0` on full sample and non-negative in each crisis window.
- Recovery speed:
  - `recovery_days`: trading days from trough back to prior equity peak.
  - `recovery_gain_days = recovery_days_baseline - recovery_days_candidate`
  - Acceptance: median `recovery_gain_days >= 0` across crisis windows.
  - Edge case rule: if all crisis-window recovery values are undefined (no full
    in-window recovery), use full-sample `recovery_gain_days >= 0` as fallback.

## Acceptance Criteria
1. Truth-table windows all pass strict rules above.
2. `data/processed/regime_history.csv` is generated with FR-042 verification columns.
3. `data/processed/regime_overlay.png` is generated with state overlays for visual audit.
4. Drawdown and recovery metrics are reported against baseline in the FR-042 validation output.
