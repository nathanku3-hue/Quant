# SAW Report - Phase 21.1 Round 1.2 (Hardening)
Date: 2026-02-20

Builds on prior round: `docs/saw_phase21_round1.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase21-brief.md`

RoundID: `R21_1_HARDENING_20260220`  
ScopeID: `S21_1_LW_DYNCENTROID_ECDF`

## Scope and Ownership
- Scope: harden Phase 21.1 ticker-pool math layer with Ledoit-Wolf/manual constant-correlation shrinkage, quarterly dynamic centroid expansion, and daily eCDF probabilities; regenerate 2024-12-24 sample and validate.
- Owned files:
  - `strategies/ticker_pool.py`
  - `strategies/company_scorecard.py`
  - `scripts/phase21_1_ticker_pool_slice.py`
  - `tests/test_ticker_pool.py`
  - `tests/test_company_scorecard.py`
  - `docs/lessonss.md`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
  - `docs/saw_phase21_round1_2.md`
- Acceptance checks:
  - CHK-421..CHK-430.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7b71-4ade-76b1-92dc-f92174684da3`
- Reviewer B: `019c7b71-4ad2-7bc1-977b-20de81fee67d`
- Reviewer C: `019c7b71-4ae4-7af1-9041-580799a191c4`
- Independence: PASS

## Top-Down Snapshot
L1: Advanced Math Track (Phase 21.1 Hardening)
L2 Active Streams: Backend
L2 Deferred Streams: Research (DTW/Matrix Profile)
L3 Stage Flow: Executing -> Iterate Loop -> Final Verification
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=LW+dynamic centroid+eCDF; OH=Impl->RevA/B/C; AC=CHK-421..430 | 99/100 | Freeze implementation contract     |
| Executing          | Refactor ticker_pool.py and regenerate 2024-12-24 sample   | 97/100 | Generate hardened sample CSV+JSON  |
| Iterate Loop       | Archetype checks + reviewer reconciliation                  | 94/100 | Reconcile SAW findings             |
| Final Verification | py_compile + pytest + SAW validators                        | 92/100 | Publish round1.2 closure           |
| CI/CD              | Hold for orchestrator review                                | 90/100 | Await GO for Phase 21.2            |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Hardening Evidence
- Sample run:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
- Artifact outputs:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
- Result highlights:
  - Sample date: `2024-12-24`
  - Shrinkage method: `manual_fixed_constant_corr` (coefficient `0.5000`)
  - Dynamic centroid: `quarterly_knn_expand` with seed anchor (`MU/CIEN`; missing `COHR/TER` logged)
  - Archetype checks:
    - `tza_plug_out_top_longs = true`
    - `seed_presence_pass = true` with available seeds `['CIEN','MU']` and in-top seeds `['CIEN','MU']`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Reviewer B flagged potential non-determinism from KNN tie handling using unstable partial sort. | Replaced KNN selection with stable `np.argsort(..., kind='mergesort')` ordering. | Implementer | Closed |
| Medium | Reviewer A flagged style gate signal computed upstream but not applied in long-selection path. | Activated style gate when sufficiently populated (`>= min_center_count`) for non-seed long candidates. | Implementer | Closed |
| Info | Reviewer C found no data-integrity/performance regressions in current hardening patch. | No action required. | Reviewer C | Closed |

## Scope Split Summary
in-scope findings/actions:
- Implemented Ledoit-Wolf/manual constant-correlation shrinkage path in `strategies/ticker_pool.py`.
- Implemented quarterly dynamic centroid update with seed anchor + top-30 KNN expansion.
- Switched to explicit daily average-rank eCDF probability mapping.
- Added deterministic run safeguards and archetype checks to summary JSON output.
- Re-generated Phase 21.1 sample/summary artifacts for `2024-12-24`.
- Added tests for eCDF ordering and dynamic centroid metadata.
- Reconciled reviewer A/B findings and revalidated.

inherited out-of-scope findings/actions:
- No inherited Critical/High findings were carried into this round.
- Phase 21.2 (Matrix Profile/DTW) remains deferred by scope boundary.

## Document Changes Showing
- `strategies/ticker_pool.py` - implemented hardening math contract (LW/manual const-corr, quarterly dynamic centroid, eCDF mapping, deterministic KNN, style-gate activation).
- `strategies/company_scorecard.py` - propagated centroid metadata columns from pool outputs into conviction frame.
- `scripts/phase21_1_ticker_pool_slice.py` - added summary JSON artifact with seed-missing logs and archetype checks.
- `tests/test_ticker_pool.py` - expanded coverage for new output contract, eCDF monotonicity, and dynamic centroid behavior.
- `tests/test_company_scorecard.py` - revalidated conviction flow compatibility with ticker-pool hardening.
- `docs/lessonss.md` - appended Phase 21.1 hardening lesson row.
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated hardened sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - generated hardening summary with audit checks.
- `docs/saw_phase21_round1_2.md` - this closure report.

## Check Results
- CHK-421: PASS (Ledoit-Wolf path + deterministic manual fallback toward constant-correlation target implemented)
- CHK-422: PASS (quarterly dynamic centroid implemented with seed set `MU/CIEN/COHR/TER` + top-30 expansion)
- CHK-423: PASS (daily empirical CDF probability mapping implemented with average-rank method)
- CHK-424: PASS (`2024-12-24` sample artifact regenerated)
- CHK-425: PASS (archetype checks logged in summary JSON: `TZA/PLUG out`, seed presence pass)
- CHK-426: PASS (seed missing ticker log emitted by quarter in summary JSON)
- CHK-427: PASS (`py_compile` passes on touched files)
- CHK-428: PASS (`pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` passes)
- CHK-429: PASS (reviewer A/B/C passes completed; A/B medium findings reconciled)
- CHK-430: PASS (SAW closure + validators complete)

ChecksTotal: 10  
ChecksPassed: 10  
ChecksFailed: 0

SAW Verdict: PASS

Open Risks:
- none

Next action:
- wait for orchestrator decision gate review before any Phase 21.2 work.

ClosurePacket: RoundID=R21_1_HARDENING_20260220; ScopeID=S21_1_LW_DYNCENTROID_ECDF; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=none; NextAction=wait for orchestrator decision gate review before any phase21.2 work

ClosureValidation: PASS
SAWBlockValidation: PASS
