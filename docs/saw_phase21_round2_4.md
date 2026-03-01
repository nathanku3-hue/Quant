# SAW Report - Phase 21 Final 1-Line Tweak (Round 2.4)
Date: 2026-02-21

Builds on prior rounds: `docs/saw_phase21_round2_3.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: final-one-line-tweak | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_FINAL_ONELINE_20260221`
ScopeID: `S21_ODDS_STRONGEST_NONCYC_R24`

## Scope and Ownership
- Scope: apply Harper's minimal 1-line scoring tweak and rerun validation artifacts.
- Change applied in `strategies/ticker_pool.py`:
  - `score = log(R[:, k_cyc] + eps) - log(max(non-cyc posteriors) + eps)`
  - implemented as strongest non-cyc denominator over `R[:, np.arange(R.shape[1]) != k_cyc]`.
- Boundaries honored:
  - no model rebuild
  - no new factors/libs
  - no Phase 22/prod lock changes
- Owned files:
  - `strategies/ticker_pool.py`
  - `AGENTS.md`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
  - `docs/saw_phase21_round2_4.md`

## Socratic Verbatim Gate
- MU-style count top-8: `>=4`
- Defensives share top-8: `<=25%`
- PLUG/TZA count top-8: `0`
- Min OddsRatio top-8: `>=3.0`
- Seed presence in top-8 (MU/CIEN): required

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Gate still fails after one-line tweak (MU-style and seed presence fail; min odds ratio fails). | Stop at gate and hold promotion; await orchestrator GO/ABORT. | Strategy | Open |
| Low | Full-window rerun (`2015-01-01`) is memory-constrained in current environment. | Used successful rerun window `2024-01-01 -> 2024-12-24` for validation evidence. | Runtime | Open |

## Check Results
- CHK-621: PASS (1-line strongest non-cyc denominator applied)
- CHK-622: PASS (slice rerun completed for 2024-12-24)
- CHK-623: PASS (`py_compile strategies/ticker_pool.py`)
- CHK-624: PASS (`pytest tests/test_ticker_pool.py -q`)
- CHK-625: PASS (top-8 table includes `OddsRatio=exp(score)`)
- CHK-626: FAIL (Socratic gate overall)

ChecksTotal: 6
ChecksPassed: 5
ChecksFailed: 1

## Gate Telemetry (2024-12-24)
- Top-8 by score (OddsRatio=exp(score)):
  - NVDA 8.847963
  - PFE 4.778404
  - GOOGL 4.406171
  - TSM 4.184429
  - WPM 3.637904
  - AMZN 3.573210
  - SIRI 3.287861
  - INTU 2.579291
- MU-style count top-8: `0` (FAIL, need `>=4`)
- Defensives share top-8: `12.5%` (PASS, `<=25%`)
- PLUG/TZA count top-8: `0` (PASS)
- Min OddsRatio top-8: `2.579291` (FAIL, need `>=3.0`)
- Seed presence MU/CIEN in top-8: `False` (FAIL)

## Scope Split Summary
in-scope findings/actions:
- Applied the 1-line strongest-non-cyc denominator scoring tweak in `strategies/ticker_pool.py`.
- Regenerated slice artifacts for 2024-12-24 and recomputed gate telemetry.
- Ran targeted compile/test checks for touched scoring path.

inherited out-of-scope findings/actions:
- Full-window (2015 start) rerun remains memory constrained in this environment.
- No model rebuild/new factors/Phase 22 work by scope lock.

## Evidence
- Rerun:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24`
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py`
- Tests:
  - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py -q`
- Artifacts:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`

## Document Changes Showing
- `strategies/ticker_pool.py` - strongest non-cyc denominator applied for odds score.
- `AGENTS.md` - test-only rerun SAW exception note retained.
- `data/processed/phase21_1_ticker_pool_sample.csv` - rerun output refreshed.
- `data/processed/phase21_1_ticker_pool_summary.json` - rerun telemetry refreshed.
- `docs/saw_phase21_round2_4.md` - this report.

SAW Verdict: BLOCK

Open Risks:
- Socratic gate not met (MU-style dominance + seed presence + min odds ratio).

Next action:
- Pause and await orchestrator decision for next minimal change or direction shift.

ClosurePacket: RoundID=R21_FINAL_ONELINE_20260221; ScopeID=S21_ODDS_STRONGEST_NONCYC_R24; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=socratic gate unmet for mu style seed presence and min odds ratio; NextAction=pause and await orchestrator decision
ClosureValidation: PASS
SAWBlockValidation: PASS
