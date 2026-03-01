# Phase 14 Brief: Feature Engineering & Micro-Alpha (FR-060)

## Objective
Build a PIT-safe feature store that converts daily price/volume data into:
- Ranking features (who to buy),
- Sizing features (how much to buy),
- Execution features (when to enter/stop).

## Feature Contract

### A. Ranking & Selection (The "Who")
- `resid_mom_60d`: residual momentum (beta-adjusted vs market return).
- `amihud_20d`: rolling Amihud illiquidity proxy.
- `rolling_beta_63d`: rolling beta vs `SPY`.

### B. Sizing & Risk (The "How Much")
- `yz_vol_20d`: Yang-Zhang annualized volatility (20d window).

### C. Execution & Timing (The "When")
- `atr_14d`: ATR-14 (dynamic stop sizing).
- `rsi_14d`: RSI-14 (pullback timing).
- `dist_sma20`: percent distance to 20d SMA.

### D. Minimal Signal Scaffold
- `composite_score`: `Z(resid_mom_60d) + Z(flow_proxy) - Z(yz_vol_20d)`.
- `trend_veto`: `price < SMA200`.

## Data Constraint Rule (Critical)
The canonical WRDS lake is close-only (`adj_close`, `total_ret`, `volume`).
When `open/high/low` are unavailable:
- Yang-Zhang uses documented close-only pseudo-OHLC proxies.
- ATR uses close-to-close true-range proxy (`abs(diff(close))`).

These fallbacks are explicit in output metadata flags.

## Acceptance Criteria
1. PIT safety: rolling/statistical features are strictly backward-looking.
2. Stability: feature computation runs with NaN-safe behavior.
3. Artifact: `data/processed/features.parquet` is generated.
4. Explainability: output includes feature columns and fallback mode flags.
