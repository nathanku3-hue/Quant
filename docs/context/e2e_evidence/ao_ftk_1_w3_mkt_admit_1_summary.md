# AO-FTK-1-W3-MKT-ADMIT-1 — Full-W3 market custody admit + D2 preflight

**Date:** 2026-08-12  
**Parent:** AO-FTK-1-ECON-1 / AO-FTK-1-20260812  
**Terminal:** `W3_MKT_ADMIT_PASS_D2_GREEN`  
**D2_PRECHECK:** `GREEN`  
**Full-W3 admitted:** `True`  
**Trials remaining:** `1` (unspent)  
**Debit this turn:** `false`  
**L5 authorized:** `false`  
**Alpha:** `0`

## Why this slice

ECON-1 Trial 2 first-failed at `D2_DATA_OBSERVABLE` because the economic probe only saw AOV ~104-name market custody and refused to proxy it as Full-W3. This slice surveys and admits real Full-W3 market price/return custody and proves D2 preflight before any final trial debit.

## Demand (frozen ECON-1)

- Denominator: `PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1`
- Comparator: `PIT_EqualWeight_Full_W3`
- H=63, lag=1, K=20, cost=20 bps RT selected only
- Same return convention FTK book ↔ Full-W3 benchmark
- Missingness → abstain; no impute; no row-delete denominator rewrite

## Survey

- Lawful Full-W3 candidates: `['PREBREAKOUT_W3_DATE_LOCAL_MARKET_CORPUS']`
- AOV-104 productquery market: `NOT_FULL_W3` (promotion forbidden)
- CRSP/Compustat/WRDS daily dirs: absent in authority worktree

## Admit

- **Admitted:** `PREBREAKOUT_W3_DATE_LOCAL_MARKET_CORPUS`
- **Security count (companies):** `5919`
- **Date range:** `{'first_session': '2025-03-24', 'last_session': '2026-08-07', 'session_count': 346, 'row_count': 1894207}`
- **Return convention:** `SP_PRICE_CLOSE_CLOSE_TO_CLOSE` with flag `CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE` on BOTH legs
- **Identity:** `['CIQSEC:<SP_CIQ_ID>', 'SP_TRADING_ITEM_ID', 'SPT_INSTRUMENT_ITEM_ID', 'SP_ENTITY_ID']`
- **AOV-104 promoted:** false

## D2 preflight

- **D2_PRECHECK:** `GREEN`
- **Coverage rate (min/mean/max):** `[0.9861216730038023, 0.993346019960318, 0.996415770609319]`
- **N_w3_eligible range:** `[4638, 5260]`
- **H=63 calendar-complete decision dates:** `282`
- **Symmetry FTK↔W3:** `True`
- **Blockers:** `[]`
- **debit_allowed_now:** false
- **l5_ready_recommendation:** `True`

### Thresholds used (conservative)

```json
{
  "min_coverage_rate_usable_h63_close_path": 0.9,
  "min_decision_dates_h63_calendar_complete": 60,
  "min_n_w3_eligible_sample": 1000,
  "min_security_count_for_full_w3_admit": 1000,
  "require_same_return_convention_ftk_and_w3": true,
  "forbid_aov_proxy_as_full_w3": true,
  "forbid_imputation": true,
  "forbid_row_delete_denominator_rewrite": true
}
```

## Stop lines

- Material trial debit: **not performed**
- Economic L5: **not run / not authorized**
- AOV-as-W3: **refused**
- Invent returns / impute / peer fill: **refused**
- AO-FTK-2 / L8 / capital / alpha: **not opened**

## Next owner action

1. Verify D2_PRECHECK=GREEN receipts
2. Issue **separate** `L5_AUTHORIZE_ECONOMIC_FINAL` (not silent)
3. Worker must **re-run D2 preflight** at L5 open; abort without debit if RED
4. Then: debit 1 · join once · one eval · L6 D6/D8/D9 · L7

This worker stops before step 2.

## Constitution

Admit real Full-W3 market custody or HOLD. Prove D2 green before the last trial. Never fake W3. Never debit here.
