# SAW Report - Phase 21.1 Round 1.4 (Final Hardening Attempt)
Date: 2026-02-20

Builds on prior rounds: `docs/saw_phase21_round1.md`, `docs/saw_phase21_round1_2.md`, `docs/saw_phase21_round1_3.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase21-brief.md`

RoundID: `R21_1_FINAL_ATTEMPT_20260220`  
ScopeID: `S21_1_LAMBDA8_REWEIGHT`

## Scope and Ownership
- Scope: final Phase 21.1 hardening attempt with stronger seed anchoring (`lambda=8.0`) and cyclical feature re-weighting (`2.5x`) inside existing Mahalanobis framework, then re-run strict gate checks.
- Owned files:
  - `strategies/ticker_pool.py`
  - `strategies/company_scorecard.py`
  - `scripts/phase21_1_ticker_pool_slice.py`
  - `tests/test_ticker_pool.py`
  - `tests/test_company_scorecard.py`
  - `docs/phase21-brief.md`
  - `docs/lessonss.md`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
  - `docs/saw_phase21_round1_4.md`
- Acceptance checks:
  - CHK-461..CHK-470.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7ba5-aba5-7213-b0d5-73453a9644e1`
- Reviewer B: `019c7ba5-abbd-7ff0-864f-0e158ac43f86`
- Reviewer C: `019c7ba5-abd3-7fd1-b5a2-b42ca6b961bf`
- Independence: PASS

## Top-Down Snapshot
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

## Hardening Evidence
- Execution:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
- Sample output:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
- Summary output:
  - `data/processed/phase21_1_ticker_pool_summary.json`
- Key locks:
  - weighted centroid: `exp(-8.0 * dist_to_seed)` over top-30 neighbors
  - cyclical feature multiplier: `2.5x` on `resid_mom_lag`, `revenue_growth_lag`, `capital_cycle_lag`, `realized_vol_lag`
  - shrinkage: `Ledoit-Wolf` fallback `manual_fixed_constant_corr=0.5000`
  - eCDF mapping: daily average-rank

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Reviewer A/C found stale seed-anchor refresh risk in weighted recentering path. | Updated seed anchor to refresh whenever seed rows are present in each valid block. | Implementer | Closed |
| High | Reviewer C flagged integrity risk if no valid Mahalanobis rows were available and runner still produced sample artifacts. | `_select_sample_date` now fails fast with explicit RuntimeError when no valid Mahalanobis outputs exist. | Implementer | Closed |
| High | Strict success gate failed: defensive share and MU-style cyc count thresholds both missed. | No additional in-scope fix allowed under locked boundaries; stop and report. | Strategy | Open |
| Medium | Reviewer B flagged long-window memory pressure risk for full 2015→as-of load in slice runner. | Documented as open risk; out of scope for this strict attempt. | Ops | Open |

## Scope Split Summary
in-scope findings/actions:
- Implemented lambda=8 weighted centroid and cyclical feature re-weighting.
- Added `revenue_growth_lag` and `realized_vol_lag` into pool feature set using existing pipeline fields.
- Added strict archetype checks in summary artifact:
  - defensive `<35%` in top-8
  - MU-style cyclicals `>=4` in top-12
- Reconciled reviewer A/B/C high findings and reran validations.
- Regenerated sample + summary artifacts.

inherited out-of-scope findings/actions:
- Phase 21.2 (Matrix Profile/DTW) remains explicitly deferred.
- No production lock/live deployment modifications were made.

## Document Changes Showing
- `strategies/ticker_pool.py` - set centroid lambda to `8.0`, added cyclical feature weighting (`2.5x`), expanded feature vector with growth/volatility proxies, and refreshed seed anchor updates.
- `strategies/company_scorecard.py` - added `revenue_growth_lag` and `realized_vol_lag` derivations to conviction frame.
- `scripts/phase21_1_ticker_pool_slice.py` - added strict archetype gates (`<35%` defensive share and `>=4` MU-style cyclicals in top-12), required explicit `--as-of-date`, and fail-fast behavior for missing regime/no valid Mahalanobis.
- `tests/test_ticker_pool.py` - updated fixture coverage for added feature columns.
- `tests/test_company_scorecard.py` - revalidated conviction integration behavior.
- `docs/phase21-brief.md` - appended final hardening attempt snapshot.
- `docs/lessonss.md` - appended round1.4 lesson entry.
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated final-attempt sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - regenerated strict-gate summary.
- `docs/saw_phase21_round1_4.md` - this SAW report.

## Check Results
- CHK-461: PASS (lambda updated to 8.0 for weighted centroid anchoring)
- CHK-462: PASS (cyclical feature re-weighting 2.5x implemented before Mahalanobis)
- CHK-463: PASS (seed sparse handling kept Method A and missing seeds logged)
- CHK-464: PASS (`min(30, valid_count)` expansion policy preserved)
- CHK-465: PASS (daily average-rank eCDF mapping preserved)
- CHK-466: PASS (sample + summary regenerated for 2024-12-24)
- CHK-467: PASS (`TZA/PLUG` excluded from top-8 longs)
- CHK-468: FAIL (defensive share gate: `0.375`, required `<0.35`)
- CHK-469: FAIL (MU-style cyclicals in top-12: `2`, required `>=4`)
- CHK-470: PASS (`py_compile` + `pytest` + SAW validators)

ChecksTotal: 10  
ChecksPassed: 8  
ChecksFailed: 2

SAW Verdict: BLOCK

Open Risks:
- Final strict success gate not met:
  - defensive share top-8 = `37.5%` (target `<35%`)
  - MU-style cyclicals top-12 = `2` (target `>=4`)
- Memory pressure remains possible for long-window slice runs (reviewer B medium).

Next action:
- Stop Phase 21.1 implementation loop and prepare explicit direction-shift plan (GMM or Isolation Forest track), per locked instruction for repeated strict-gate failure.

ClosurePacket: RoundID=R21_1_FINAL_ATTEMPT_20260220; ScopeID=S21_1_LAMBDA8_REWEIGHT; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=strict gate failed with defensive share 37.5 percent and mu style cyclicals 2 of required 4 plus medium memory risk; NextAction=stop phase21.1 loop and prepare explicit direction shift plan gmm or isolation forest

ClosureValidation: PASS
SAWBlockValidation: PASS
