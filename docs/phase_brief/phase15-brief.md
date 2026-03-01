# Phase 15 Brief: Alpha Engine & Tactical Execution (FR-070)

## 1. Objective
Integrate the Regime Governor (FR-041/FR-050) with the Feature Store (FR-060) into one deterministic alpha engine that answers:
- Who to buy.
- How much to size.
- When to enter/exit.

## 2. Policy: Structural Fixed vs Adaptive Tunable
### Structural (Fixed)
- Market filter stays fixed: `price > SMA200` for long eligibility.
- Regime budget stays fixed: `GREEN=1.0`, `AMBER=0.5`, `RED=0.0`.
- Score sign discipline stays fixed:
  - Momentum/quality terms are positive contributors.
  - Volatility/illiquidity terms are penalties.
- Safety invariant stays fixed: total portfolio exposure never exceeds regime budget.

### Adaptive (Tunable, Walk-Forward Only)
- Entry sensitivity uses rolling RSI percentile instead of static RSI number.
- Stop multiplier uses volatility-aware ATR multiplier.
- Selection depth uses cross-sectional score percentile / top-N policy.

## 3. Logic Pipeline (Selector -> Sizer -> Executor)
1. Selector
- Apply tradability constraints.
- Apply trend veto (`price > SMA200`).
- Apply tactical entry gate (RSI static or rolling percentile mode).
- Rank by `composite_score`; select top N.

2. Sizer
- Base weight per asset: `target_risk / yz_vol_20d`.
- Conviction scalar: optional boost for high score.
- Regime scalar: `1.0/0.5/0.0`.
- Normalize and hard-cap to regime budget.

3. Executor
- Entry trigger:
  - Mean-reversion mode: `price <= SMA20` or RSI crossover.
- Stop logic:
  - `stop = entry_price - (atr_multiplier * atr_14d)`.

## 4. Hard Rules (Execution Safety)
- Hysteresis rank buffer:
  - Enter if `rank <= 5`.
  - Hold if `rank <= 20`.
  - Exit if `rank > 20`.
- Ratchet-only stop:
  - `stop_t = max(stop_{t-1}, price_t - (K * ATR_t))`.
  - Stop can move up only, never down.
- Regime cap:
  - `sum(weights_t) <= regime_budget_t` is mandatory even under high conviction.

## 5. Acceptance Criteria
- No exposure breach: `sum(weights_t) <= regime_budget_t` for all dates.
- Explainability: every selected position emits `reason_code`.
- PIT safety: decisions at `t` only use information available at `t`.
- Tuning governance: adaptive knobs may be changed only through walk-forward validation.
- Verifier outputs include benchmark comparison table:
  - SPY vs Phase 13 (Governor) vs Phase 15 (Alpha).
