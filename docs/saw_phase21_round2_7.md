# SAW Report - Phase 21 Round 2.7 Structural Patch A (Multi-Component Logit Odds)
Date: 2026-02-21

Builds on prior round: `docs/saw_phase21_round2_6.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: patch-a-multi-component-logit | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_PATCH_A_LOGIT_20260221`
ScopeID: `S21_MULTICOMP_LOGIT_R27`

## Scope and Ownership
- Scope: apply Harper's Patch A (multi-component `k_cyc_components` + pure logit odds) and rerun 2024-12-24 slice.
- Applied in `strategies/ticker_pool.py`:
  - `k_cyc_components = np.flatnonzero(R_anchor.mean(axis=0) > 1/n_components)`  (above-uniform threshold)
  - `r_cyc_multi = R[:, k_cyc_components].sum(axis=1)`
  - `r_cyc_multi = np.clip(r_cyc_multi, eps, 1.0 - eps)`
  - `score = np.log(r_cyc_multi + eps) - np.log(1.0 - r_cyc_multi + eps)` (pure logit odds)
  - `odds_ratio = r_cyc_multi / (1.0 - r_cyc_multi + eps)`
- `k_cyc` retained for `mah_dist_cyc` telemetry column compatibility.
- No new factors, no model rebuild, no Phase 22 / prod lock changes.
- Owned files:
  - `strategies/ticker_pool.py`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
  - `docs/saw_phase21_round2_7.md`

## Harper Verbatim Gate (Corrected, Round 2.7)
"PROMOTE the ticker pool only if top-8 contains ≥4 MU-style cyclicals including explicit MU and CIEN seed presence, defensives ≤25%, PLUG/TZA count = 0, and deep-space violations are zero (no selected name with MahDist > 5.0)."

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Logit score saturates (17.73) for tickers whose single-component `r_cyc ≈ 1.0` (CSCO, USO, WBA, SMCI, NVDL) — these dominate top-5 and block MU/CIEN from entering top-8. | Root cause: 3-component softmax assigns near-100% cyclical responsibility to tickers that are close to centroid but not MU-style archetypes. Pure logit faithfully surfaces this mass but cannot distinguish "genuinely cyclical" from "not defensive or junk". | Strategy | Open |
| High | MU and CIEN are present in the full universe (389 rows) but score below saturation tier. MU ranks ~2nd in live conviction at `odds_score=1.497`; CIEN scores `-0.429` (junk-dominant on this date). Neither enters top-8. | Patch A is structurally correct per Harper's spec; the ontology failure is upstream in the 3-component posterior. | Strategy | Open |
| Medium | Threshold calibration: initial `> 0.05` threshold selected all 3 components (sum = 1.0, full saturation). Corrected to `> 1/n_components` (above-uniform = 0.333). With current anchor mean [0.61, 0.10, 0.29], this selects only column 0 (cyclical). | Threshold fix applied in this round. | Strategy | Closed |
| Medium | PLUG appears in top-8 longs with `odds_score=3.21` due to moderate cyclical responsibility. Deep-space violations: 4 names exceed MahDist > 5.0. | Gate fails on both criteria. | Strategy | Open |

## Check Results
- CHK-651: PASS (Patch A multi-component logit score block applied to `strategies/ticker_pool.py`)
- CHK-652: PASS (threshold correction applied: `> 1/n_components` instead of `> 0.05`)
- CHK-653: PASS (2024-12-24 slice rerun completed)
- CHK-654: PASS (`py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py`)
- CHK-655: PASS (`pytest tests/test_ticker_pool.py -q` → 5 passed, 0 failed)
- CHK-656: FAIL (Harper verbatim gate overall)

ChecksTotal: 6
ChecksPassed: 5
ChecksFailed: 1

## Gate Telemetry (2024-12-24)

### Top-8 LONG table (ranked by odds_score desc):
| Rank | Ticker | OddsScore  | OddsRatio        | CompounderProb | MahDist_k_cyc |
|------|--------|------------|------------------|----------------|---------------|
| 1    | CSCO   | 17.727534  | 49,999,999.374   | 0.407643       | 1.393745      |
| 2    | USO    | 17.727534  | 49,999,999.374   | 0.350318       | 1.435940      |
| 3    | WBA    | 17.727534  | 49,999,999.374   | 0.261146       | 2.094077      |
| 4    | SMCI   | 17.727534  | 49,999,999.374   | 0.019108       | 6.747034      |
| 5    | NVDL   | 17.727534  | 49,999,999.374   | 0.000000       | 12.435033     |
| 6    | NBIS   | 3.348153   | 28.450133        | 0.057325       | 5.209910      |
| 7    | PLUG   | 3.207145   | 24.708432        | 0.095541       | 3.775053      |
| 8    | GEG    | 2.890229   | 17.997431        | 0.006369       | 12.334826     |

### Gate criterion results:
- MU-style count top-8: `1` (NBIS) — **FAIL**, need `≥4`
- Explicit MU in top-8: `False` — **FAIL** (MU is rank ~2 in full conviction at odds_score=1.497, below saturation tier)
- Explicit CIEN in top-8: `False` — **FAIL** (CIEN cyc=0.39, junk=0.42 → odds_score=-0.429, action=WAIT)
- Defensives ≤ 25% top-8: `0.0%` — **PASS**
- PLUG/TZA count: `1` (PLUG) — **FAIL**, need `= 0`
- Deep-space MahDist > 5.0 count: `4` (SMCI=6.75, NVDL=12.44, NBIS=5.21, GEG=12.33) — **FAIL**, need `= 0`
- Min OddsRatio top-8: `17.997431` — **PASS** (`≥ 3.0`), but note: saturated values are numerically valid but represent degenerate single-component mass, not genuine multi-component signal

### Structural Diagnostic (R_anchor on 2024-12-24):
- Anchor tickers present: `MU`, `CIEN` (COHR, TER absent from universe)
- MU posterior: `cyc=0.817, def=0.024, junk=0.159`
- CIEN posterior: `cyc=0.394, def=0.181, junk=0.425`
- R_anchor mean: `cyc=0.606, def=0.103, junk=0.292`
- `k_cyc = 0` (cyclical column, argmax)
- `k_cyc_components = [0]` (only column 0 exceeds uniform threshold 0.333)
- Saturation source: tickers CSCO/USO/WBA/SMCI/NVDL have `r_cyc ≈ 1.0` individually → `r_cyc_multi ≈ 1.0 - eps` → logit = 17.727

## Scope Split Summary
in-scope findings/actions:
- Implemented Harper's Patch A (multi-component `k_cyc_components` + pure logit odds + `np.clip` guard).
- Applied above-uniform threshold calibration to prevent all-component saturation.
- Reran 2024-12-24 slice, verified compile and tests.
- Reported full diagnostics including R_anchor structure and saturation source.

inherited out-of-scope findings/actions:
- No factor/model/rebuild changes.
- No Phase 22 or production lock changes.
- No changes to `company_scorecard.py`, slice script, or any other file.

## Evidence
- Rerun:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24`
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py` → PASS
- Tests:
  - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py -q` → `5 passed, 0 failed`
- Artifacts:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`

## Document Changes Showing
- `strategies/ticker_pool.py` — Patch A: multi-component `k_cyc_components` + pure logit odds + above-uniform threshold + `np.clip` guard.
- `data/processed/phase21_1_ticker_pool_sample.csv` — regenerated sample.
- `data/processed/phase21_1_ticker_pool_summary.json` — regenerated telemetry.
- `docs/saw_phase21_round2_7.md` — this report.

SAW Verdict: BLOCK

Open Risks:
- Harper gate fails on 4 of 5 criteria: MU-style count, explicit seed presence (MU+CIEN), PLUG/TZA presence, and deep-space violations.
- Logit saturation tier (score=17.73) is produced by tickers with single-component near-100% cyclical posteriors — structurally different from MU-style genuine cyclicals.
- Root cause is upstream in 3-component posterior ontology, not in the scoring formula itself.

Next action:
- Patch A complete — paused, no other changes. Await orchestrator GO/ABORT/DIAGNOSE decision.

ClosurePacket: RoundID=R21_PATCH_A_LOGIT_20260221; ScopeID=S21_MULTICOMP_LOGIT_R27; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=gate fails on mu_style_count(1 of 4) seed_presence(MU+CIEN absent) plug_tza(PLUG in top8) deep_space(4 violations); NextAction=patch A complete paused await orchestrator decision
ClosureValidation: PASS
SAWBlockValidation: PASS
