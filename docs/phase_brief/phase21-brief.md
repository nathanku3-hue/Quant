# Phase 21 Brief: Stop-Loss & Drawdown Control (Day 1)
Date: 2026-02-20
Status: Day 1 Complete (PASS) / Phase Active
Owner: Atomic Mesh

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Stop-Loss & Drawdown Control
- L2 Active Streams: Backend, Data, Ops
- L2 Deferred Streams: Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Backend
- Active Stage Level: L3
- Current Stage: Final Verification
- Planning Gate Boundary: in-scope = standalone stop-loss module + unit tests + docs-as-code updates; out-of-scope = strategy reparameterization, live trading integration rewiring.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-101..CHK-108.

## 1. Objective
- Deliver a standalone position-level stop-loss and drawdown control module for Phase 21 Day 1.
- Enforce architecture rulings:
  - ATR via close-only proxy with simple moving average.
  - D-57 ratchet invariant (`stop_t >= stop_{t-1}`).
  - Two-stage stop framework + time-based underwater exit.
  - Portfolio drawdown circuit-breaker scaling tiers.

## 2. Implementation Summary
- Added `strategies/stop_loss.py`:
  - `StopLossConfig` with explicit `atr_mode='proxy_close_only'`.
  - `ATRCalculator`:
    - `ATR_t = SMA(|close_t - close_{t-1}|, window=20)`.
  - `StopLossManager`:
    - stage 1 initial stop (`entry - 2.0 * ATR`),
    - stage 2 trailing stop (`price - 1.5 * ATR`),
    - stage 3 time-based underwater exit (`days_held > 60`),
    - D-57 ratchet via `max(previous_stop, candidate_stop)`.
  - `PortfolioDrawdownMonitor`:
    - drawdown tiers at `-8%`, `-12%`, `-15%`,
    - scaling at `0.75`, `0.50`, `0.00`,
    - recovery reset at `>-4%`.
  - Optional edge-case guard:
    - `min_stop_distance_abs` (default `0.0`) to avoid zero-distance stops when ATR is exactly zero.
- Added `tests/test_stop_loss.py` with 18 unit tests covering ATR, stage transitions, ratchet invariants, time exits, drawdown tiers, factory behavior, and zero-volatility edge cases.

## 3. Day 1 Artifacts
- `strategies/stop_loss.py`
- `tests/test_stop_loss.py`
- `docs/phase21-brief.md`
- `docs/decision log.md` (D-102)
- `docs/notes.md` (Phase 21 formulas)
- `docs/lessonss.md` (new lesson entry)
- `docs/saw_phase21_day1_round1.md`

## 4. Acceptance Checks
- CHK-101: close-only ATR SMA implementation exists and rejects non-proxy ATR mode -> PASS.
- CHK-102: initial + trailing stop stages implemented with configurable ATR multipliers -> PASS.
- CHK-103: D-57 ratchet invariant enforced in stop updates -> PASS.
- CHK-104: time-based underwater exit implemented -> PASS.
- CHK-105: portfolio drawdown tier scaling implemented with recovery gate -> PASS.
- CHK-106: zero-volatility behavior covered in unit tests -> PASS.
- CHK-107: stop-loss test suite passes -> PASS.
- CHK-108: docs-as-code updates (brief, notes, decision log, lessons, SAW) completed -> PASS.

## 5. Verification Evidence
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/stop_loss.py tests/test_stop_loss.py` -> PASS
- Unit tests:
  - `.venv\Scripts\python -m pytest tests/test_stop_loss.py -q` -> PASS (`18 passed`)
- Regression check:
  - `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q` -> PASS (`3 passed`)

## 6. Rollback Note
- If Day 1 is rejected:
  - remove:
    - `strategies/stop_loss.py`
    - `tests/test_stop_loss.py`
    - `docs/phase21-brief.md`
    - `docs/saw_phase21_day1_round1.md`
  - revert doc append sections in:
    - `docs/decision log.md`
    - `docs/notes.md`
    - `docs/lessonss.md`

## 7. Day 2 Integration Gate (Planned)
- Integration is intentionally deferred from Day 1 implementation scope.
- Before enabling module in live execution paths:
  - add wiring into strategy runtime with explicit feature gate,
  - add integration tests validating stop-trigger exits + drawdown scaling in portfolio loop,
  - verify telemetry fields for stop state and drawdown tier transitions,
  - complete SAW review for wiring changes with Quant Ops + Risk handoff.

---

## 8. Phase 21.1 Final Hardening (Weighted Centroid)
Date: 2026-02-20
Status: Active (Round 1.3 complete; awaiting orchestrator review)

Top-Down Snapshot
L1: Advanced Math Track (Phase 21.1 Final Hardening – Weighted Centroid)
L2 Active Streams: Backend
L2 Deferred Streams: Research
L3 Stage Flow: Executing -> Iterate Loop -> Final Verification
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Distance-Weighted Centroid (Option 1)                   | 99/100 | Freeze lambda & checks             |
| Executing          | Implement weighted centroid + re-run sample               | 98/100 | Generate final hardened CSV        |
| Iterate Loop       | Verify archetype (MU/CIEN/COHR/TER-style dominate)        | 96/100 | Reconcile defensive % <50 %        |
| Final Verification | py_compile + pytest + SAW + lesson                        | 94/100 | Publish round1.3 & report back     |
| CI/CD              | Hold for orchestrator review                              | 92/100 | Await GO for Phase 21.2            |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

---

## 9. Phase 21.1 Final Hardening Attempt (Lambda + Feature Re-weight)
Date: 2026-02-20
Status: Complete (awaiting orchestrator decision)

Top-Down Snapshot
L1: Advanced Math Track (Phase 21.1 Final Hardening Attempt)
L2 Active Streams: Backend
L2 Deferred Streams: Research
L3 Stage Flow: Executing -> Iterate Loop -> Final Verification
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Stronger lambda + feature re-weighting                  | 99/100 | Freeze strict gate                 |
| Executing          | Implement + re-run sample                                 | 98/100 | Generate final sample CSV          |
| Iterate Loop       | Enforce archetype dominance gate                          | 96/100 | Reconcile in SAW                   |
| Final Verification | py_compile + pytest + SAW + lesson                        | 94/100 | Publish round1.4 & report          |
| CI/CD              | Hold for orchestrator review                              | 92/100 | Await GO for next step             |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

---

## 10. Phase 21 Final Leverage Run (Target-Vol + Beta/Accounting Hardening)
Date: 2026-02-20
Status: Complete (decision-gate hold)

Execution scope:
- Implemented leverage ride using:
  - `L_raw = clip(Target_Vol / sigma_continuous, 1.0, 1.5)`
  - continuous sigmoid jump veto (`k=30`, `x0=0.15`)
  - EMA smoothing (`span=10`)
- Implemented linear portfolio beta cap with:
  - pre-check scaling
  - hard post-cap scaling
- Implemented strict accounting outputs:
  - `gross_exposure`, `net_exposure`
  - `short_borrow_balance (B_t)`
  - `borrow_cost_daily = B_t * annual_rate / 252` (daily simple accrual)

Verification evidence:
- Compile: `.venv\Scripts\python -m py_compile strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py` -> PASS
- Tests: `.venv\Scripts\python -m pytest tests/test_company_scorecard.py tests/test_ticker_pool.py -q` -> PASS
- Sample run:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
  - leverage checks: PASS (`L in [1.0,1.5]`, `|beta|<=1.0`, gross/net accounting pass, borrow cost non-negative)

Artifacts:
- `data/processed/phase21_1_ticker_pool_sample.csv`
- `data/processed/phase21_1_ticker_pool_summary.json`
- `docs/saw_phase21_round2_1.md`

---

## 11. Phase 21 Final Odds Fix (Posterior Odds vs Defensive Component)
Date: 2026-02-20
Status: Complete (BLOCK at gate)

Execution scope:
- Added posterior odds ranking:
  - `S_i = log(r_cyc + 1e-8) - log(r_def + 1e-8)`
- Defensive component:
  - lowest transformed realized-vol cluster (3 quantile buckets)
- Hard gate:
  - only `S_i > 0` candidates are eligible for long pool
  - final top-8 ranked by `S_i`

Run result (as-of 2024-12-24):
- Defensive share top-8: `0.0%` (PASS)
- `TZA/PLUG` out of top-8: `False` (FAIL)
- MU-style count in top-12: `2` (FAIL vs `>=4`)
- Seed presence in top-8 (MU/CIEN available): `False` (FAIL)

Decision:
- Round blocked; no promotion.

Artifacts:
- `data/processed/phase21_1_ticker_pool_sample.csv`
- `data/processed/phase21_1_ticker_pool_summary.json`
- `docs/saw_phase21_round2_2.md`

---

## 12. Phase 21 Final Odds vs Junk Fix (Posterior Odds Refinement)
Date: 2026-02-20
Status: Complete (BLOCK at gate)

Execution scope:
- Replaced odds target with `max(defensive, junk)` denominator:
  - `S_i = log(r_cyc + 1e-8) - log(max(r_def, r_junk) + 1e-8)`
- Added junk component detection by locked median rule:
  - lowest `ebitda_roic_accel` + lowest `gm_accel` proxy + lowest `revenue_growth` proxy
- Kept hard gate:
  - only `S_i > 0` eligible, top-8 by `S_i`
- Decoupled pool state semantics:
  - `WAIT/AVOID/LONG/SHORT`

Run result (as-of 2024-12-24):
- `TZA/PLUG` out of top-8: `True` (PASS)
- Defensive share top-8: `12.5%` (PASS)
- MU-style count in top-12: `0` (FAIL vs `>=4`)
- Seed presence in top-8 (MU/CIEN available): `False` (FAIL)
- Odds integrity:
  - `posterior_sum_close_to_one_pass = True`
  - `posterior_bounds_pass = True`
  - `posterior_coverage = 0.4036`

Decision:
- Round blocked; no Phase 22 start.

Artifacts:
- `data/processed/phase21_1_ticker_pool_sample.csv`
- `data/processed/phase21_1_ticker_pool_summary.json`
- `docs/saw_phase21_round2_2.md`

---

## 13. Phase 21 Final Finetune (Round 2.3: Odds-vs-Max(def,junk) Hardening)
Date: 2026-02-21
Status: Complete (BLOCK at gate)

Execution scope:
- Kept locked odds score:
  - `S_i = log(r_cyc + 1e-8) - log(max(r_def, r_junk) + 1e-8)`
- Locked junk labeling clarifications:
  - defensive component = lowest transformed realized-vol bucket
  - junk component = lowest medians on quality trio proxies
  - missing quality trio fallback = force junk-dominant posterior for that row
- Locked fallback source ordering:
  - GM proxy: `gm_accel_q -> operating_margin_delta_q -> ebitda_accel`
  - Revenue proxy: `revenue_growth_q -> revenue_growth_yoy -> revenue_growth_lag`
- Added telemetry contract fields:
  - `mu_style_count_top8`
  - `plug_tza_count_top_longs`
  - `min_odds_ratio_top8` and `min_odds_ratio_top8_ge_3`

Run result (as-of 2024-12-24):
- `TZA/PLUG` out of top-8: `True` (PASS)
- Defensive share top-8: `12.5%` (PASS vs `<35%`)
- MU-style count top-8: `0` (FAIL vs `>=4`)
- MU-style count top-12: `0` (FAIL vs `>=4`)
- Min odds ratio top-8: `2.5793` (FAIL vs `>=3.0`)
- Seed presence in top-8 (MU/CIEN available): `False` (FAIL)

Decision:
- Round blocked; no Phase 22 start.

Artifacts:
- `data/processed/phase21_1_ticker_pool_sample.csv`
- `data/processed/phase21_1_ticker_pool_summary.json`
- `docs/saw_phase21_round2_3.md`
