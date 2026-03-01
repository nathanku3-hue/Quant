# Phase 10 Brief: Global Liquidity & Flow Layer (FR-040)

## Objective
Implement a PIT-safe market hydraulics layer that measures liquidity supply, collateral stress, and flow/crowding behavior.

## Scope (MVP)
Generate `data/processed/liquidity_features.parquet` with:
- `us_net_liquidity_mm`: `WALCL - WDTGAL - (RRPONTSYD * 1000)`
- `liquidity_impulse`: normalized 20-day ROC of net liquidity
- `repo_spread_bps`: `(SOFR - DFF) * 100`
- `lrp_index`: `Z(DTB3) - Z(VIX)`
- `dollar_stress_corr`: rolling 20-day correlation of DXY vs SPX returns
- `smart_money_flow`: cumulative `SPY(Close - Open)`

## H.4.1 PIT Rule (Critical)
- `WALCL` and `WDTGAL` are weekly with reporting date Wednesday.
- They are released Thursday 4:30 PM ET.
- Engineering rule: shift availability by +2 calendar days (Wednesday -> Friday session) before joining to trading bars.

## In Scope Data Sources
- FRED: `WALCL`, `WDTGAL`, `RRPONTSYD`, `SOFR`, `DFF`, `DTB3`
- Yahoo: `^VIX`, `DX-Y.NYB`, `^GSPC`, `SPY` OHLC

## Out of Scope (Phase 10 MVP)
- Fails-to-deliver series
- COT parsing
- DIX/GEX and proprietary flow feeds

## Acceptance Criteria
1. PIT-safe weekly lag rule for Fed H.4.1 series is enforced.
2. Validation checks pass:
   - Sept 2019 repo spike: `repo_spread_bps > 10`.
   - 2022 liquidity impulse shows sustained negative regime periods.
3. Loader and validator run successfully:
   - `data/liquidity_loader.py`
   - `scripts/validate_liquidity_layer.py`
