# SAW Report - Phase 21 Round 2.6 Geometry Structural Fix
Date: 2026-02-21

Builds on prior round: `docs/saw_phase21_round2_5.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: geometry-two-line-fix | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_GEOMETRY_FIX_20260221`
ScopeID: `S21_GEOMETRY_ONELINE_R26`

## Scope and Ownership
- Scope: apply locked 2-line geometry scoring replacement and rerun 2024-12-24 slice.
- Applied in `strategies/ticker_pool.py`:
  - `odds_ratio = (R[:, k_cyc] + 1e-5) / (np.max(np.delete(R, k_cyc, axis=1), axis=1) + 1e-5)`
  - `score = np.where(odds_ratio > 0.5, -mah_dist_cyc, -9999.0)`
- Supporting telemetry wiring:
  - propagated `odds_ratio` and `mahalanobis_k_cyc`
  - summary gate now reports deep-space count (`MahDist to k_cyc > 5.0`)

## Harper Verbatim Gate
"Approve only if the top-8 ranked by the updated k_cyc + 1-vs-rest odds has MU-style >=4, defensives <=25%, PLUG/TZA = 0, and min OddsRatio across the top-8 >= 3.0."

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | MU-style and seed-presence gates still fail after geometry fix. | Stop at gate; no promotion. | Strategy | Open |
| Medium | Raw odds gate (`>=0.5`) passes, but verbatim Harper odds floor (`>=3.0`) still fails. | Keep as open risk and await orchestrator next action. | Strategy | Open |

## Check Results
- CHK-641: PASS (2-line geometry score replacement applied)
- CHK-642: PASS (2024-12-24 slice rerun completed)
- CHK-643: PASS (`py_compile` on touched files)
- CHK-644: PASS (`pytest tests/test_ticker_pool.py -q`)
- CHK-645: PASS (deep-space telemetry added using `mahalanobis_k_cyc`)
- CHK-646: FAIL (Harper gate overall)

ChecksTotal: 6
ChecksPassed: 5
ChecksFailed: 1

## Gate Telemetry (2024-12-24)
- Top-8 table (Ticker | OddsScore | OddsRatio | CompounderProb | MahDist to k_cyc):
  - LVS | -0.686620 | 0.995337 | 0.917197 | 0.686620
  - OXY | -0.692635 | 0.876179 | 0.980892 | 0.692635
  - MOS | -0.705874 | 0.989043 | 0.904459 | 0.705874
  - HAL | -0.715178 | 0.919682 | 0.961783 | 0.715178
  - NTR | -0.715274 | 0.882843 | 0.949045 | 0.715274
  - LOW | -0.739903 | 0.848150 | 0.898089 | 0.739903
  - CMCSA | -0.747042 | 0.981675 | 0.859873 | 0.747042
  - TGT | -0.762573 | 0.987158 | 0.847134 | 0.762573
- MU-style count top-8: `0` (FAIL, need `>=4`)
- Defensives % top-8: `0.0%` (PASS, need `<=25%`)
- PLUG/TZA count: `0` (PASS)
- Deep-space MahDist>5.0 count: `0` (PASS)
- Min raw OddsRatio top-8: `0.848150` (PASS, need `>=0.5`)
- Harper verbatim min OddsRatio gate (`>=3.0`): FAIL
- MU/CIEN seed presence: `False` (FAIL)

## Scope Split Summary
in-scope findings/actions:
- Implemented geometry scoring lines and reran slice.
- Added explicit `mahalanobis_k_cyc` and raw `odds_ratio` telemetry output.
- Added deep-space gate metric in summary output.

inherited out-of-scope findings/actions:
- No factor/model/rebuild changes.
- No Phase 22 or production lock changes.

## Evidence
- Rerun:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24`
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py`
- Tests:
  - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py -q`
- Artifacts:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`

## Document Changes Showing
- `strategies/ticker_pool.py` - geometry score + raw odds ratio + k_cyc distance output.
- `strategies/company_scorecard.py` - propagated raw odds ratio and k_cyc Mahalanobis fields.
- `scripts/phase21_1_ticker_pool_slice.py` - raw odds telemetry + deep-space gate metric.
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - regenerated telemetry.
- `docs/saw_phase21_round2_6.md` - this report.

SAW Verdict: BLOCK

Open Risks:
- Harper gate remains unmet (MU-style dominance and seed presence fail; verbatim odds threshold >=3.0 not met).

Next action:
- Pause and await orchestrator GO/ABORT decision.

ClosurePacket: RoundID=R21_GEOMETRY_FIX_20260221; ScopeID=S21_GEOMETRY_ONELINE_R26; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=harper gate unmet on mu style seed presence and >=3 odds threshold; NextAction=pause and await orchestrator decision
ClosureValidation: PASS
SAWBlockValidation: PASS
