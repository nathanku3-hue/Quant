# SAW Report - Phase 21 Final Leverage Run (Round 2.1)
Date: 2026-02-20

Builds on prior rounds: `docs/saw_phase21_round1_4.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: leverage-final-run | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_FINAL_LEVERAGE_20260220`  
ScopeID: `S21_TARGETVOL_SIGMOID_BETACAP_ACCOUNTING`

## Scope and Ownership
- Scope: leverage-only hardening in Phase 21 final run:
  - target-vol leverage sizing
  - continuous sigmoid jump veto (`k=30`, `x0=0.15`)
  - EMA smoothing (`span=10`)
  - linear portfolio beta capping (pre-check + hard post-cap)
  - strict net/gross accounting + daily simple borrow cost on `B_t`
- Owned files:
  - `strategies/company_scorecard.py`
  - `scripts/phase21_1_ticker_pool_slice.py`
  - `tests/test_company_scorecard.py`
  - `docs/saw_phase21_round2_1.md`
  - `docs/lessonss.md`
  - `docs/phase_brief/phase21-brief.md`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
- Acceptance checks:
  - CHK-541..CHK-549

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7c5a-a02c-70c3-b1ff-dac040922f70`
- Reviewer B: `019c7c5a-a053-7a20-bfd3-c1fd71668788`
- Reviewer C: `019c7c5a-a062-7fe2-aaee-dc4f1b275dfd`
- Independence: PASS

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Reviewer C: beta-cap math used zero-fill in portfolio beta sums, which could understate beta during missing beta windows. | Replaced cap math inputs to use non-zero lagged beta assumptions (`beta_lag` defaults to 1.0) and removed zero-fill path. | Implementer | Closed |
| High | Reviewer B/C: rolling beta path used Python per-permno loop and could become a long-window runtime bottleneck. | Replaced with vectorized rolling moment formulation (`E[xy]-E[x]E[y]`) grouped by `permno`. | Implementer | Closed |
| Medium | Reviewer B: sample-date selector hard-fails when no valid Mahalanobis rows exist. | Kept fail-fast behavior for artifact integrity in this round; documented as inherited monitoring risk. | Ops | Open (inherited) |
| Medium | Inherited from Round 1.4: archetype dominance checks still fail (`defensive<35%`, `MU-style>=4/12`). | Out-of-scope for leverage-only run; carried as open risk for ticker-pool track. | Strategy | Open (inherited) |

## Check Results
- CHK-541: PASS (target-vol leverage formula implemented: `clip(Target_Vol / sigma_continuous, 1.0, 1.5)`)
- CHK-542: PASS (continuous sigmoid jump veto implemented with `k=30`, `x0=0.15`)
- CHK-543: PASS (EMA smoothing span=10 applied to post-veto leverage)
- CHK-544: PASS (linear beta cap implemented both pre-check and hard post-cap, `|beta|<=1`)
- CHK-545: PASS (strict net/gross accounting implemented; `gross_exposure >= |net_exposure|`)
- CHK-546: PASS (daily simple borrow cost on `B_t` implemented: `borrow_cost_daily = B_t * annual_rate / 252`)
- CHK-547: PASS (sample artifact includes `leverage_multiplier`, `portfolio_beta`, and borrow-cost/accounting columns)
- CHK-548: PASS (`py_compile` + `pytest tests/test_company_scorecard.py tests/test_ticker_pool.py -q`)
- CHK-549: PASS (reviewer A/B/C reconciliation completed; in-scope High findings closed)

ChecksTotal: 9  
ChecksPassed: 9  
ChecksFailed: 0

## Evidence
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py`
- Tests:
  - `.venv\Scripts\python -m pytest tests/test_company_scorecard.py tests/test_ticker_pool.py -q`
- Sample run:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
- Artifacts:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`

## Document Changes Showing
- `strategies/company_scorecard.py` - leverage logic replaced with target-vol + jump veto + EMA10 + pre/post beta cap + strict accounting and borrow-cost outputs.
- `scripts/phase21_1_ticker_pool_slice.py` - sample contract expanded with leverage/beta/cost fields and leverage gate checks in summary JSON/log output.
- `tests/test_company_scorecard.py` - conviction frame contract test expanded for leverage and accounting fields.
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated final leverage sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - regenerated with leverage checks.
- `docs/lessonss.md` - appended final leverage-run lesson entry.
- `docs/phase_brief/phase21-brief.md` - appended final leverage-run execution summary.
- `docs/saw_phase21_round2_1.md` - this SAW report.

SAW Verdict: PASS

Open Risks:
- Inherited ticker-pool archetype gate remains failed from prior round (`defensive 37.5%`, `MU-style 2/12`), out-of-scope for leverage-only run.
- `_select_sample_date` remains fail-fast by design when no valid Mahalanobis rows exist.

Next action:
- Hold for orchestrator decision gate on leverage slice; if approved, proceed to next phase planning with ticker-pool open-risk tracking.

ClosurePacket: RoundID=R21_FINAL_LEVERAGE_20260220; ScopeID=S21_TARGETVOL_SIGMOID_BETACAP_ACCOUNTING; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=inherited archetype gate failure and fail fast selector behavior; NextAction=hold at decision gate and await orchestrator direction
ClosureValidation: PASS
SAWBlockValidation: PASS
