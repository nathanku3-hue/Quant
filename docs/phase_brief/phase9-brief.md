# Phase 9 Brief — FR-035 Macro-Regime Awareness

## Objective
Build an institutional-grade macro feature layer that is PIT-safe, restartable, and directly consumable by strategy/runtime.

## Scope
- Build `data/macro_loader.py` to generate `data/processed/macro_features.parquet`.
- Integrate `regime_scalar` into strategy scoring with safe fallback to legacy macro logic.
- Add Data Manager control to rebuild macro features.
- Add validator `scripts/validate_macro_layer.py`.

## Data Sources (Phase 9)
- Yahoo: `^VIX`, `^VIX3M`, `^VVIX`, `DX-Y.NYB`, `^GSPC`, `HYG`, `LQD`, `MTUM`, `SPY`, `BND`, `BTC-USD`.
- FRED: `SOFR`, `DFF`, `T10Y2Y`, `DFII10`.
- Out of scope: DIX/GEX (deferred to Phase 10).

## PIT Policy
- Fast market series: same-day (T+0) alignment.
- Slow FRED series: conservative one-day lag (T+1).
- Forward fill limit for market-closed days: max 3 trading sessions.

## Acceptance Criteria
- `macro_features.parquet` is generated successfully with FR-035 schema.
- March 2020 has at least one `liquidity_air_pocket=True`.
- 2022 shows `momentum_crowding` state changes.
- App loads macro via `macro_features.parquet` fallback-safe.
- `pytest -q` and macro validator pass.

## Risks
- External API instability (Yahoo/FRED).
- Coverage gaps in historical SOFR period (pre-2018).

## Rollback
- App keeps fallback to legacy `macro.parquet`.
- Macro integration path can be disabled by removing `macro_features.parquet`.
