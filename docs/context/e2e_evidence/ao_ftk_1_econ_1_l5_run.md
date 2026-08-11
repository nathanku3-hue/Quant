# AO-FTK-1-ECON-1 L5 economic run

- run_id: `AO_FTK_1_ECON_1_L5_ECONOMIC_RUN_1`
- clock: TRANSITION_POSITION
- binds: H=63, RT=0.90, CAT=0.10, K=20, ΔJ=0.0, D7=OUT_OF_SCOPE
- evaluation_status: **COMPLETED_BLOCKED_FULL_W3_MARKET_CUSTODY_MISSING**
- market_flag: `FULL_W3_MARKET_CUSTODY_MISSING_FOR_ECONOMIC_ESTIMAND`
- delta_J: `None`
- financial_alpha_evidence: **0**
- AO-FTK-2: NOT_OPENED

## Session arithmetic (frozen)

Let t0 = decision_asof session. Entry session tE = next trading session after t0 (lag=1). Exit session tX = trading session H_VALUE steps after tE (H=63). Holding-period return uses close[tX]/close[tE]-1 under chosen return series; costs 20 bps RT on selected only. Deterministic & frozen.

## Note

Full-W3 market custody missing for economic estimand. No invented returns. No second run.
