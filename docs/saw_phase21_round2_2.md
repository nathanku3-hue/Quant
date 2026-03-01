# SAW Report - Phase 21 Final Odds vs Junk Fix (Round 2.2)
Date: 2026-02-20

Builds on prior rounds: `docs/saw_phase21_round2_1.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: final-odds-vs-junk | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_FINAL_ODDS_JUNK_20260220`  
ScopeID: `S21_ODDS_MAX_DEF_JUNK`

## Scope and Ownership
- Scope: final ticker-pool fix using posterior odds vs max(defensive, junk):
  - `S_i = log(r_cyc + 1e-8) - log(max(r_def, r_junk) + 1e-8)`
  - defensive cluster by lowest transformed realized-vol bucket
  - junk cluster by lowest-median quality/growth proxies (`ebitda_roic_accel`, `gm_accel_q` fallback, `revenue_growth_lag`)
  - hard long gate `S_i > 0`, top-8 by `S_i`
  - decoupled pool state semantics (`WAIT/AVOID/LONG/SHORT`)
- Owned files:
  - `strategies/ticker_pool.py`
  - `strategies/company_scorecard.py`
  - `scripts/phase21_1_ticker_pool_slice.py`
  - `docs/saw_phase21_round2_2.md`
  - `docs/lessonss.md`
  - `docs/phase_brief/phase21-brief.md`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
- Acceptance checks:
  - CHK-571..CHK-579

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7e7e-270f-78e2-978a-85216e9e7119`
- Reviewer B: `019c7e7e-2726-7321-b63a-211d6e76c7ae`
- Reviewer C: `019c7e7e-272f-79d3-a459-68e1a86a9076`
- Independence: PASS

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Reviewer B: odds-row hard-fail path could abort the slice run when posterior rows were sparse/invalid. | Replaced fatal check with resilient summary gating (`odds_available`, coverage/bounds/sum checks) and preserved artifact emission. | Implementer | Closed |
| Medium | Reviewer A: `long_prob_threshold` config is currently unused in odds hard-gate path. | Left as-is for this round because policy lock was strict `S_i > 0`; carry as cleanup debt. | Strategy | Open |
| Medium | Reviewer C: posterior integrity gating should include component bounds and coverage, not only sum-to-one. | Added `posterior_bounds_pass` and `posterior_coverage` checks in summary JSON. | Implementer | Closed |
| High | Archetype gate still failed (seed/MU-style dominance not achieved). | Stop at decision gate per governance; no out-of-boundary factor changes in this round. | Strategy | Open |

## Check Results
- CHK-571: PASS (odds-vs-max(def,junk) score implemented with epsilon `1e-8`)
- CHK-572: PASS (junk component identification implemented from locked median proxy rule)
- CHK-573: PASS (pool state decoupled: `WAIT/AVOID/LONG/SHORT`)
- CHK-574: PASS (sample regenerated for `2024-12-24`)
- CHK-575: PASS (`py_compile` passed on touched modules)
- CHK-576: PASS (`pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` passed)
- CHK-577: PASS (odds integrity checks emitted: availability, coverage, bounds, posterior sum)
- CHK-578: FAIL (archetype gate: MU-style in top-12 failed; seed presence failed)
- CHK-579: PASS (SAW A/B/C review + reconciliation complete)

ChecksTotal: 9  
ChecksPassed: 8  
ChecksFailed: 1

## Gate Outcome (2024-12-24)
- `TZA/PLUG` out of top-8 longs: `True` (PASS)
- Defensive share top-8: `12.5%` (PASS vs `<35%`)
- MU-style count in top-12: `0` (FAIL vs `>=4`)
- Seed presence in top-8 (MU/CIEN available): `False` (FAIL)
- Odds integrity:
  - `odds_available`: `True`
  - `posterior_coverage`: `0.4036`
  - `posterior_bounds_pass`: `True`
  - `posterior_sum_close_to_one_pass`: `True`

## Scope Split Summary
in-scope findings/actions:
- Implemented odds vs max(defensive, junk) ranking and hard gate.
- Added junk cluster identification with locked fallback hierarchy.
- Added posterior outputs (`posterior_cyclical`, `posterior_defensive`, `posterior_junk`, `posterior_negative`) and IDs.
- Replaced brittle odds hard-fail in slice runner with integrity telemetry.
- Regenerated artifacts and reran compile/tests.

inherited out-of-scope findings/actions:
- Archetype dominance still fails under locked no-new-factor boundary.
- `long_prob_threshold` remains unused in hard-gate path by design choice for this round.

## Evidence
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py`
- Tests:
  - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q`
- Sample run:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
- Artifacts:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`

## Document Changes Showing
- `strategies/ticker_pool.py` - odds-vs-max(def,junk) ranking, junk cluster mask helper, posterior fields, WAIT/AVOID pool semantics.
- `strategies/company_scorecard.py` - propagated junk/odds posterior outputs.
- `scripts/phase21_1_ticker_pool_slice.py` - long sorting by odds, posterior integrity checks, resilient odds availability handling.
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - regenerated summary with updated odds checks.
- `docs/lessonss.md` - appended round2.2 lesson entry.
- `docs/phase_brief/phase21-brief.md` - appended round2.2 summary block.
- `docs/saw_phase21_round2_2.md` - this SAW report.

SAW Verdict: BLOCK

Open Risks:
- Archetype acceptance still unmet (`MU-style >=4/12` and seed presence in top-8 failed).

Next action:
- Stop at gate and await orchestrator pivot/expanded-scope decision before Phase 22.

ClosurePacket: RoundID=R21_FINAL_ODDS_JUNK_20260220; ScopeID=S21_ODDS_MAX_DEF_JUNK; ChecksTotal=9; ChecksPassed=8; ChecksFailed=1; Verdict=BLOCK; OpenRisks=archetype gate failed with mu style 0 of required 4 and seed presence false; NextAction=stop and await orchestrator pivot decision
ClosureValidation: PASS
SAWBlockValidation: PASS
