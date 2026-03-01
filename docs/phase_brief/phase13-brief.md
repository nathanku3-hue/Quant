# Phase 13 Brief: Walk-Forward Regime Backtest (FR-050)

## Objective
Isolate and quantify the value of the FR-041 Governor by applying it to a simple
beta sleeve (`SPY` vs cash), independent of stock-selection alpha.

## Methodology
- Simulation window: `2000-01-01` to latest available session.
- Signal source: `RegimeManager` Governor (`GREEN`, `AMBER`, `RED`).
- Execution lag (PIT-safe): signal at close `t` executes at close `t+1`.
- Trading friction: `5 bps` per unit turnover.

## Deterministic Allocation Rules
| Governor State | Signal Weight (`w_t`) | Executed Weight (`w_{t+1}`) | Exposure |
|---|---:|---:|---|
| `GREEN` | `1.0` | shifted by 1 day | 100% `SPY` |
| `AMBER` | `0.5` | shifted by 1 day | 50% `SPY` / 50% cash |
| `RED` | `0.0` | shifted by 1 day | 100% cash |

## Cash Proxy Rule (Critical)
- Primary: `BIL` daily total return (when available).
- Fallback: `EFFR` simple daily accrual (`effr_rate / 100 / 252`).
- Final fallback (if both missing): constant `0.02 / 252`.

This prevents underestimating cash performance in pre-ETF periods.

## Acceptance Criteria
1. `UlcerIndex(strategy) < UlcerIndex(SPY)`.
2. `|MaxDD(strategy)| < 0.5 * |MaxDD(SPY)|`.
3. `Sharpe(strategy) > Sharpe(SPY)`.
4. Report total return comparison (`strategy vs SPY`) explicitly.

## Artifacts
- `data/processed/phase13_walkforward.csv`
- `data/processed/phase13_equity_curve.png`
