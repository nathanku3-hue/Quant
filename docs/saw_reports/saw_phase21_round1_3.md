# SAW Report - Phase 21.1 Round 1.3 (Final Hardening, Weighted Centroid)
Date: 2026-02-20

Builds on prior rounds: `docs/saw_phase21_round1.md`, `docs/saw_phase21_round1_2.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase21-brief.md`

RoundID: `R21_1_FINAL_HARDENING_20260220`  
ScopeID: `S21_1_WEIGHTED_CENTROID_LAMBDA3`

## Scope and Ownership
- Scope: implement Option 1 distance-weighted centroid hardening (`exp(-3.0*dist_to_seed)`), regenerate 2024-12-24 artifacts, enforce archetype checks, and stop at gate.
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
  - `docs/saw_phase21_round1_3.md`
- Acceptance checks:
  - CHK-441..CHK-450.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7b88-58bf-7c41-990b-c7433f599d45`
- Reviewer B: `019c7b88-58cd-7740-826c-4658614f6b53`
- Reviewer C: `019c7b88-58d3-7441-982b-f4c4ef8f1c33`
- Independence: PASS

## Top-Down Snapshot
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

## Hardening Evidence
- Execution:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
- Sample artifact: `data/processed/phase21_1_ticker_pool_sample.csv`
- Summary artifact: `data/processed/phase21_1_ticker_pool_summary.json`
- Key math lock:
  - centroid weighting: `exp(-3.0 * dist_to_seed)` over top-30 neighbors
  - shrinkage: `Ledoit-Wolf if available`, fallback `manual_fixed_constant_corr=0.5000`
  - probability: daily `1 - eCDF(distance)` using average-rank ties

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Reviewer A/C found seed anchor refresh bug (anchor frozen from first available period), which could stale-weight quarterly recentering. | Updated `seed_anchor_ref` whenever seeds are present in each valid block. | Implementer | Closed |
| Medium | Reviewer B found reproducibility risk from default `--as-of-date=today`. | Made `--as-of-date` explicit-required in runner CLI. | Implementer | Closed |
| Medium | Final archetype gate `defensive_share < 50%` failed (`4/8 = 50.0%`). | No in-scope fix allowed without new heuristic overrides; hold for orchestrator decision. | Strategy | Open |

## Scope Split Summary
in-scope findings/actions:
- Added weighted centroid recentering (`quarterly_knn_expand_weighted_seed_dist`) in `strategies/ticker_pool.py`.
- Preserved locked shrinkage and eCDF methods.
- Added explicit archetype gate checks and defensive-share metric in summary JSON.
- Reconciled reviewer A/B/C findings and reran full validation suite.
- Updated phase brief snapshot and lessons log.

inherited out-of-scope findings/actions:
- Phase 21.2 (Matrix Profile/DTW) remains deferred by explicit boundary.
- No production lock/live deployment changes were attempted.

## Document Changes Showing
- `strategies/ticker_pool.py` - implemented distance-weighted centroid (lambda=3.0) and refreshed seed-anchor updates on each seed-bearing block.
- `scripts/phase21_1_ticker_pool_slice.py` - added defensive-share and seed-threshold checks; made `--as-of-date` required.
- `strategies/company_scorecard.py` - retained integration compatibility with ticker-pool metadata.
- `tests/test_ticker_pool.py` - regression checks remained green after weighted centroid patch.
- `tests/test_company_scorecard.py` - conviction-frame compatibility tests passed.
- `docs/phase21-brief.md` - appended Phase 21.1 final-hardening snapshot block.
- `docs/lessonss.md` - appended final hardening lesson entry.
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated final hardening sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - regenerated hardening summary with defensive/archetype gates.
- `docs/saw_phase21_round1_3.md` - this closure report.

## Check Results
- CHK-441: PASS (distance-weighted centroid logic implemented with lambda=3.0)
- CHK-442: PASS (seed availability handling Method A maintained with per-quarter missing-seed logs)
- CHK-443: PASS (top-30 expansion fallback `min(30, valid_count)` maintained)
- CHK-444: PASS (daily average-rank eCDF mapping retained)
- CHK-445: PASS (2024-12-24 sample + summary artifacts regenerated)
- CHK-446: PASS (TZA/PLUG excluded from top-8 longs)
- CHK-447: PASS (seed presence threshold met: available seeds=`2`, required=`2`, in top-8=`2`)
- CHK-448: FAIL (defensive share threshold `<50%` missed: `4/8 = 50.0%`)
- CHK-449: PASS (`py_compile` + `pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q`)
- CHK-450: PASS (SAW publication + validators complete)

ChecksTotal: 10  
ChecksPassed: 9  
ChecksFailed: 1

SAW Verdict: BLOCK

Open Risks:
- Defensive dominance gate remains unmet (`4/8 = 50.0%`, target `<50%`), so archetype hardening is not promotable under locked criteria.

Next action:
- Hold Phase 21.2 start and run an explicitly approved refinement for defensive concentration control (without violating no-new-factor boundary).

ClosurePacket: RoundID=R21_1_FINAL_HARDENING_20260220; ScopeID=S21_1_WEIGHTED_CENTROID_LAMBDA3; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=defensive share gate failed at 4 of 8 top longs equal to 50 percent; NextAction=hold phase21.2 and request approved refinement for defensive concentration control

ClosureValidation: PASS
SAWBlockValidation: PASS
