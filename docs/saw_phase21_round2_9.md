# SAW Report - Phase 21 Round 2.9 Patch B (Expanded Anchor + MahDist Ceiling)
Date: 2026-02-21

Builds on prior rounds: docs/saw_phase21_round2_7.md, docs/saw_phase21_round2_8.md

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: patch-b-expanded-anchor-mahdist-ceiling | Domains: Backend, Data | FallbackSource: docs/spec.md + docs/phase_brief/phase21-brief.md

RoundID: R21_PATCH_B_20260221
ScopeID: S21_PATCHB_R29

## Scope and Ownership
- Scope: Patch B - expanded anchor basket + hard MahDist ceiling (<=5.0) + r_cyc_multi ranking.
- Data injection: run_update(scope=Custom, custom_list=LRCX,AMAT,KLAC,STX,WDC) -> success, 6 tickers patched (live layer; STX/WDC absent from WRDS base, not present on 2024-12-24).
- Effective anchor basket on 2024-12-24: MU, CIEN, LRCX, AMAT, KLAC (N=5; COHR, TER, STX, WDC absent from universe on this date).
- Applied in strategies/ticker_pool.py:
  1. seed_tickers extended: (MU, CIEN, COHR, TER, LRCX, AMAT, KLAC, STX, WDC)
  2. Scoring block: r_cyc_multi = R[:,k_cyc_components].sum(axis=1), above-uniform threshold (> 1/3)
  3. Hard ceiling: valid = mah_dist_cyc <= 5.0; score = where(valid and odds_ratio > 0.5, odds_ratio, -9999.0)
- Owned files: strategies/ticker_pool.py, data/processed/phase21_1_ticker_pool_sample.csv, data/processed/phase21_1_ticker_pool_summary.json, docs/saw_phase21_round2_9.md

## Harper Verbatim Gate (Round 2.9)
PROMOTE only if the Top-8 ranked by score contains MU-style >=4 with explicit MU and CIEN present, defensives <=25%, PLUG/TZA = 0, and deep-space anomalies = 0 (no selected ticker with MahDist > 5.0).

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | CSCO/USO/WBA still saturate (score=49999999) with r_cyc_multi near 1.0. MahDist ceiling correctly vetoed SMCI/NVDL/NBIS. MU is LONG but ranks below saturation tier. | Root cause: CSCO/USO/WBA have near-100% cyclical responsibility independently of anchor basket - structural BGM posterior issue. | Strategy | Open |
| High | Explicit MU and CIEN absent from top-8. MU ranks 9th+; CIEN junk-dominant (action=WAIT). | CIEN impasse escalated to orchestrator. | Orchestrator | Open - Escalated |
| Medium | PLUG still in top-8 (score=24.71, MahDist=3.78 passes ceiling filter but fails PLUG/TZA gate). | Requires explicit PLUG exclusion or posterior shift. | Strategy | Open |
| Low | Deep-space violations: 0. MahDist ceiling working correctly. | Ceiling fix confirmed effective. | Strategy | Closed |
| Low | mu_style_count_top8 = 1 (AVGO). Sentinel -9999 pushed SMCI/NVDL/NBIS out. | Still short of >=4 gate. | Strategy | Open |

## Check Results
- CHK-671: PASS (run_update Custom LRCX,AMAT,KLAC,STX,WDC -> success, 6 tickers)
- CHK-672: PASS (seed_tickers extended in TickerPoolConfig)
- CHK-673: PASS (Patch B scoring block applied to strategies/ticker_pool.py)
- CHK-674: PASS (2024-12-24 slice rerun, exit code 0)
- CHK-675: PASS (py_compile touched files)
- CHK-676: PASS (pytest tests/test_ticker_pool.py -q -> 5 passed, 0 failed)
- CHK-677: FAIL (Harper verbatim gate overall)

ChecksTotal: 7
ChecksPassed: 6
ChecksFailed: 1

## Gate Telemetry (2024-12-24)

Top-8 LONG table (ranked by score = odds_ratio after MahDist ceiling):
| Rank | Ticker | Score/OddsRatio | CompounderProb | MahDist_k_cyc |
|------|--------|-----------------|----------------|---------------|
| 1 | CSCO | 49,999,999 | 0.4076 | 1.3937 |
| 2 | USO | 49,999,999 | 0.3503 | 1.4359 |
| 3 | WBA | 49,999,999 | 0.2611 | 2.0941 |
| 4 | PLUG | 24.71 | 0.0955 | 3.7751 |
| 5 | AVGO | 13.29 | 0.1146 | 3.7345 |
| 6 | LCID | 13.04 | 0.2166 | 2.3772 |
| 7 | BB | 12.92 | 0.1210 | 3.6576 |
| 8 | NVAX | 12.61 | 0.1465 | 2.7189 |

Gate criterion results:
- MU-style count top-8: 1 (AVGO) -- FAIL, need >=4
- Explicit MU in top-8: False -- FAIL (MU action=LONG, ranks ~9th)
- Explicit CIEN in top-8: False -- FAIL (CIEN junk-dominant, ESCALATED TO ORCHESTRATOR)
- Defensives <=25% top-8: 0.0% -- PASS
- PLUG/TZA count: 1 (PLUG, MahDist=3.78 passes ceiling) -- FAIL, need = 0
- Deep-space MahDist>5.0 count: 0 -- PASS (ceiling filter working)
- Min OddsRatio top-8: 12.61 -- PASS (>=3.0)

Progress vs prior rounds:
- Round 2.7: deep_space=4, mu_style=1, MU absent -- BLOCK
- Round 2.8: deep_space=3, mu_style=2, MU absent -- BLOCK
- Round 2.9: deep_space=0 (FIXED), mu_style=1, MU absent -- BLOCK

## CIEN Escalation (Section 3 Upstream Investigation Required)
CIEN on 2024-12-24: posterior_cyclical=0.394, posterior_junk=0.425, action=WAIT.
Even with N=5 anchor basket, CIEN odds_ratio < 1.0 (junk-dominant).
Orchestrator options:
- Option 1 (Waive): Accept CIEN absent for 2024-12-24; gate passes if MU + 3 other MU-style anchors present.
- Option 2 (Investigate): Check CIEN ebitda_accel, roic_accel, quality_lag, revenue_growth_q on 2024-12-24 for pipeline misalignment or stale fundamental input.

## Scope Split Summary
in-scope findings/actions:
- Patch B applied. Data injection via run_update. MahDist ceiling confirmed effective (deep_space=0). py_compile PASS. pytest 5/5 PASS.
inherited out-of-scope:
- CSCO/USO/WBA saturation tier persists. PLUG MahDist below ceiling (3.78). CIEN structural impasse.

## Evidence
- Data injection: run_update(scope=Custom, custom_list=LRCX,AMAT,KLAC,STX,WDC) -> success, tickers_updated=6
- Slice: .venv/Scripts/python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24
- Compile: PASS. Tests: 5 passed, 0 failed.
- CSV: data/processed/phase21_1_ticker_pool_sample.csv
- JSON: data/processed/phase21_1_ticker_pool_summary.json

SAW Verdict: BLOCK

Open Risks:
- CSCO/USO/WBA saturation (r_cyc_multi near 1.0) persists - structural BGM posterior issue unresolved.
- PLUG (MahDist=3.78) passes MahDist ceiling but fails PLUG/TZA gate.
- CIEN junk-dominance on 2024-12-24 - escalated to orchestrator.
- MU cannot break into top-8 while CSCO/USO/WBA saturation tier occupies ranks 1-3.

Next action: Patch B complete - paused, no other changes. Await orchestrator GO/ABORT/DIAGNOSE/WAIVE-CIEN decision.

ClosurePacket: RoundID=R21_PATCH_B_20260221; ScopeID=S21_PATCHB_R29; ChecksTotal=7; ChecksPassed=6; ChecksFailed=1; Verdict=BLOCK; OpenRisks=CSCO_USO_WBA_saturation PLUG_in_top8 CIEN_escalated MU_below_saturation_tier; NextAction=paused await orchestrator decision
ClosureValidation: PASS
SAWBlockValidation: PASS
