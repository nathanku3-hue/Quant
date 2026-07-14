# M7F3-v7 SELF_FINANCING_PORTFOLIO_TRUTH

Mode: `EXECUTION_PACKET`  
RoundID: `ROUND-20260712-M7F3-V7-SELF-FINANCING`  
ScopeID: `M7F3_V7_SELF_FINANCING_PORTFOLIO_TRUTH`  
Branch: `c0x/m7f0-v4`  
Implementation: `m7f3-v7`  
Supersedes: `m7f2-v6-final` (hard replace; no active v6 executable path)

## Purpose

Close the v6 audit gap (score 61/100) with a mechanically correct self-financing portfolio engine, exact residual attribution, and honest residual exposure. Target diagnostic band **~70–73**; research validity remains capped near **30** (snapshot CUSIP8).

## Delta locks (owner GO 2026-07-12)

1. **Daily sequence (locked):**  
   `drifted prior weights → trade to today's target & charge equity turnover → apply today's RET → process close-state transitions`.
2. **Bridge parity:** conservative price/RET parity with documented abs tol `1e-4` on  
   `||PRC_next|/|PRC_prev| − 1 − RET_next|`. Mismatch → residual window status only.  
   **Bridge never changes the 2,448-event selection set.**
3. **Residual exposure (primary):** summed **first-bad-date** equal-weight target weights  
   (audit band ~0.72%). **Not** weight-time share; **not** `n_bad/n_selected`.
4. **write_down_100pct:** −100% once, then **dead zero weight** (not recapitalized into EW).
5. **Turnover:** equity L1 only; cash-weight changes do **not** double-count.
6. **Attribution:** exact **16-state Shapley** over four residual ambiguities; contributions sum to scenario terminal NAV gap vs ok-only.
7. **Selection identity:** SHA-256 of canonical sorted selected `event_id` set.
8. **Commits:** A code/tests/brief; B evidence only (no full seven-surface reconcile); C distinct A/B/C reviewer artifacts + SAW + seven-surface reconcile.

## Forbidden

- Local CCM path (NL-only, zero PERMNO)
- WRDS login, as-of/historical link, readiness flip, alpha/tradable, UI/strategy
- Event-id production policy
- Treating neutral carry as justified upper bound
- Active v6 executable product path (historical evidence retained)

## Artifacts

- Script: `scripts/pead_m7f3_v7_2019_crsp_vertical.py`
- Tests: `tests/test_pead_m7f3_v7_2019_crsp_vertical.py`
- Evidence: `docs/context/e2e_evidence/pead_m7f3_v7_2019_crsp_vertical.json`
- Legs: `data/processed/pead_m7f3_v7_2019_daily_returns_{neutral_carry_to_cash,write_down_100pct}.parquet`
