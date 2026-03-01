# Phase 11 Brief: Regime Governor + Throttle (FR-041)

## Objective
Implement a deterministic regime layer that separates:
- Governor: market safety veto (RED/AMBER/GREEN).
- Throttle: opportunity score and binning (NEG/NEUT/POS).

The output is a fixed 3x3 exposure matrix, long-only by default.

## Inputs
- `repo_spread_bps` (explicit units in basis points).
- `credit_freeze` (bool, when available from macro layer).
- `liquidity_impulse`.
- `vix_level` (fallback `vix_proxy` if needed).
- `us_net_liquidity_mm` (for MA20 and BOCPD).
- `vrp` (from liquidity layer): `vix_level - realized_vol_21d`.
- `momentum_proxy` (or SPY 20d return fallback).

## Governor Rules
- RED if any:
  - `repo_spread_bps > 10.0`
  - `credit_freeze == True` AND `vix_level > 15`
  - `liquidity_impulse < -1.90` AND `vix_level > 20`
  - `vix_level > 40`
- AMBER if not RED and any:
  - `us_net_liquidity_mm < 0.997 * MA20(us_net_liquidity_mm)` AND `liquidity_impulse < 0`
  - `vix_level > 25`
  - `bocpd_prob > 0.80`
- GREEN otherwise.

## Throttle Rules
- Continuous score:
  - `S = mean(Z(liquidity_impulse), Z(vrp), -Z(vix_level), Z(momentum_proxy))`
  - clipped to `[-2.0, 2.0]`.
- Bins:
  - POS: `S > 0.5`
  - NEUT: `-0.5 <= S <= 0.5`
  - NEG: `S < -0.5`

## 3x3 Exposure Matrix
| Governor \ Throttle | NEG | NEUT | POS |
|---|---:|---:|---:|
| GREEN | 0.70 | 1.00 | 1.30 |
| AMBER | 0.25 | 0.50 | 0.75 |
| RED | 0.00 | 0.00 | 0.20 |

## Long-Only Safety
- No shorting in V1.
- Hard safety for RED:
  - RED + NEG => `0.00`
  - RED + NEUT => `0.00`
  - RED + POS => capped at `0.20`

## Acceptance Criteria
1. `RegimeManager` returns state, throttle score, matrix exposure, and explainable reason.
2. `investor_cockpit` scales weights using FR-041 target exposure.
3. UI shows traffic light + reason.
4. Loader provides `realized_vol_21d` and `vrp`.
5. Unit tests cover matrix mapping, red-floor behavior, and fallback behavior.
