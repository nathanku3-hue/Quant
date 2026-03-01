# SAW Report - Phase 21 Final Structural Fix (Round 2.5)
Date: 2026-02-21

Builds on prior round: `docs/saw_phase21_round2_4.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: anchor-kcyc-one-line | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_FINAL_ANCHOR_ONELINE_20260221`
ScopeID: `S21_ANCHOR_ARGMAX_KCYC_R25`

## Scope and Ownership
- Scope: apply locked anchor-based `k_cyc` structural one-line and rerun 2024-12-24 slice.
- One-line applied in `strategies/ticker_pool.py`:
  - `k_cyc = int(np.argmax(X_anchor_sweetspot.mean(axis=0)))`
  - (anchor-driven equivalent of locked formula on current responsibility pipeline)
- Kept unchanged:
  - round2.4 1-vs-strongest-non-cyc odds score
  - junk fallback and pool semantics
  - no new factors/libraries/model rebuild
- Owned files:
  - `strategies/ticker_pool.py`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
  - `docs/saw_phase21_round2_5.md`

## Verbatim Gate (Locked)
"Approve only if the top-8 ranked by the updated k_cyc + 1-vs-rest odds has MU-style >=4, defensives <=25%, PLUG/TZA = 0, and min OddsRatio across the top-8 >= 3.0."

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Structural fix flipped component identity toward non-archetype names; top-8 longs include non-MU-style names and failed MU/seed gate. | Stop at gate; hold promotion and await orchestrator decision. | Strategy | Open |
| Medium | Score magnitudes saturate (`18.420681`) for several names because selected `k_cyc` component dominates via epsilon floor behavior. | Carry as follow-up diagnostics for `k_cyc` component validation prior to promotion. | Strategy | Open |

## Check Results
- CHK-631: PASS (anchor-driven k_cyc line applied)
- CHK-632: PASS (slice rerun completed for 2024-12-24)
- CHK-633: PASS (`py_compile strategies/ticker_pool.py`)
- CHK-634: PASS (`pytest tests/test_ticker_pool.py -q`)
- CHK-635: FAIL (verbatim gate)

ChecksTotal: 5
ChecksPassed: 4
ChecksFailed: 1

## Gate Telemetry (2024-12-24)
- MU-style count top-8: `0` (FAIL, need `>=4`)
- Defensives share top-8: `0.0%` (PASS, need `<=25%`)
- PLUG/TZA count top-8: `0` (PASS)
- Min OddsRatio top-8: `4.259641` (PASS, need `>=3.0`)
- Seed presence (MU/CIEN in top-8): `False` (FAIL)

Top-8 ranked by updated score:
- CSCO (score=18.420681, OddsRatio=100000000.0)
- USO (score=18.420681, OddsRatio=100000000.0)
- WBA (score=18.420681, OddsRatio=100000000.0)
- SMCI (score=18.420681, OddsRatio=100000000.0)
- NVDL (score=18.420681, OddsRatio=100000000.0)
- GEG (score=2.178248, OddsRatio=8.830821)
- COIN (score=1.585541, OddsRatio=4.881933)
- NVAX (score=1.449185, OddsRatio=4.259641)

## Scope Split Summary
in-scope findings/actions:
- Applied anchor-based `k_cyc` line and regenerated slice artifacts.
- Recomputed telemetry and verified compile/tests for touched scoring path.

inherited out-of-scope findings/actions:
- No model rebuild, no feature additions, no Phase 22/prod lock changes.

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
- `strategies/ticker_pool.py` - anchor-driven `k_cyc` one-line selection.
- `data/processed/phase21_1_ticker_pool_sample.csv` - rerun sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - rerun telemetry.
- `docs/saw_phase21_round2_5.md` - this SAW report.

SAW Verdict: BLOCK

Open Risks:
- Verbatim gate not met (MU-style and seed presence fail).

Next action:
- Pause and await orchestrator GO/ABORT decision.

ClosurePacket: RoundID=R21_FINAL_ANCHOR_ONELINE_20260221; ScopeID=S21_ANCHOR_ARGMAX_KCYC_R25; ChecksTotal=5; ChecksPassed=4; ChecksFailed=1; Verdict=BLOCK; OpenRisks=verbatim gate failed on mu style and seed presence; NextAction=pause and await orchestrator decision
ClosureValidation: PASS
SAWBlockValidation: PASS
