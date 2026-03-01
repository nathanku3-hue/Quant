# SAW Report - Phase 21 Round 2.8 True Bayesian Log-Odds Update
Date: 2026-02-21

Builds on prior round: `docs/saw_phase21_round2_7.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: bayesian-logodds-pm-view | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_BAYES_LOGODDS_20260221`
ScopeID: `S21_BAYESIAN_VIEW_R28`

## Scope and Ownership
- Scope: apply True Bayesian Log-Odds Update and rerun 2024-12-24 slice.
- Applied in `strategies/ticker_pool.py` (replaced lines 633–675):
  1. PM View: `mu_view = X_anchor.mean(axis=0)`, `prec_view = LedoitWolf().fit(X_anchor).precision_`
  2. BGM Prior Log-Odds: `logO_prior = log(R[:,k_cyc]) - log(1 - R[:,k_cyc])`
  3. Bayes Factor: `logLambda = log_p_archetype - log_p_mixture`
     - `log_p_archetype = -0.5 * einsum("ij,jk,ik->i", diff, prec_view, diff)`
     - `log_p_mixture = logsumexp([-0.5*d_cyc^2, -0.5*d_def^2, -0.5*d_junk^2])` (replaces `bgm.score_samples`)
  4. Posterior: `score = logO_prior + logLambda`; `odds_ratio = exp(clip(score, -500, 500))`
- LedoitWolf fallback to `inv_cov` if fewer than 2 anchors or LedoitWolf fails.
- `k_cyc` and `mah_dist_cyc` retained for telemetry column compatibility.
- No new factors, no model rebuild, no Phase 22 / prod lock changes.
- Owned files: `strategies/ticker_pool.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `docs/saw_phase21_round2_8.md`

## Harper Verbatim Gate (Round 2.8)
"PROMOTE only if the Top-8 ranked by score = ln(O_post) contains MU-style >=4 with explicit MU and CIEN present, defensives <=25%, PLUG/TZA = 0, and deep-space anomalies = 0 (no selected ticker with MahDist > 5.0)."

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Bayesian update did not break saturation tier: SMCI now ranks 1st (score=20.98) above MU/CIEN because its archetype proximity d2_view is smallest while its mixture log-evidence is also small. The logLambda term amplifies rather than suppresses deep-space tickers when they happen to lie close to mu_view on a given date. | Root cause: mu_view computed from only MU+CIEN (N=2) spans an 8-dimensional centroid that SMCI/WBA/USO also lie near in z-score space on 2024-12-24. The LedoitWolf precision matrix with N=2 collapses to near-identity, making d2_view effectively isotropic and unable to discriminate archetype geometry from noise. | Strategy | Open |
| High | MU and CIEN remain absent from top-8. MU action=LONG but ranks 9th+ in score. CIEN action=WAIT (junk-dominant on this date). | Seed presence gate continues to fail. | Strategy | Open |
| Medium | PLUG still in top-8 (score=4.13). Deep-space violations remain: 3 names with MahDist>5.0 (SMCI=6.75, NVDL=12.44, NBIS=5.21). | Gate continues to fail on PLUG/TZA and deep-space criteria. | Strategy | Open |
| Low | MU-style count improved from 1 to 2 (NBIS, BB). Still short of >=4 gate. | Marginal improvement but gate not met. | Strategy | Open |

## Check Results
- CHK-661: PASS (Bayesian log-odds block applied to strategies/ticker_pool.py)
- CHK-662: PASS (2024-12-24 slice rerun completed, exit code 0)
- CHK-663: PASS (py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py)
- CHK-664: PASS (pytest tests/test_ticker_pool.py -q -> 5 passed, 0 failed)
- CHK-665: FAIL (Harper verbatim gate overall)

ChecksTotal: 5
ChecksPassed: 4
ChecksFailed: 1
## Gate Telemetry (2024-12-24)
Top-8 LONG table (ranked by odds_score = ln(O_post)):
| Rank | Ticker | OddsScore | OddsRatio | CompounderProb | MahDist_k_cyc |
|------|--------|-----------|-----------|----------------|---------------|
| 1 | SMCI | 20.9796 | 1,292,203,682 | 0.0191 | 6.7470 DEEP-SPACE |
| 2 | WBA | 19.6090 | 328,157,122 | 0.2611 | 2.0941 |
| 3 | USO | 15.3025 | 4,423,809 | 0.3503 | 1.4359 |
| 4 | CSCO | 14.3875 | 1,771,709 | 0.4076 | 1.3937 |
| 5 | NVDL | 13.6037 | 809,148 | 0.0000 | 12.4350 DEEP-SPACE |
| 6 | NBIS | 5.4176 | 225.34 | 0.0573 | 5.2099 DEEP-SPACE |
| 7 | PLUG | 4.1324 | 62.33 | 0.0955 | 3.7751 |
| 8 | BB | 3.1290 | 22.85 | 0.1210 | 3.6576 |

Gate criterion results:
- MU-style count top-8: 2 (NBIS, BB) -- FAIL need >=4
- Explicit MU in top-8: False -- FAIL (MU action=LONG, ranks below top-8 in Bayesian score)
- Explicit CIEN in top-8: False -- FAIL (CIEN junk-dominant on this date, action=WAIT)
- Defensives <=25% top-8: 0.0% -- PASS
- PLUG/TZA count: 1 (PLUG) -- FAIL need = 0
- Deep-space MahDist>5.0 count: 3 (SMCI=6.75, NVDL=12.44, NBIS=5.21) -- FAIL need = 0
- Min OddsRatio top-8: 22.85 -- PASS (>=3.0)

## Scope Split Summary
in-scope findings/actions:
- Implemented True Bayesian Log-Odds Update (PM View x Mixture Prior) in ticker_pool.py.
- Translated bgm.score_samples to logsumexp of existing 3-component log-densities (mathematically exact).
- LedoitWolf try/except fallback implemented. Reran slice, verified compile and tests.
inherited out-of-scope findings/actions:
- No factor/model/rebuild changes. No Phase 22 or production lock changes.


## Evidence
- Rerun: .venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24
- Compile: .venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py -> PASS
- Tests: .venv\Scripts\python -m pytest tests/test_ticker_pool.py -q -> 5 passed, 0 failed
- Artifacts: data/processed/phase21_1_ticker_pool_sample.csv | data/processed/phase21_1_ticker_pool_summary.json

## Document Changes Showing
- strategies/ticker_pool.py - Round 2.8 True Bayesian Log-Odds block (replaces Patch A).
- data/processed/phase21_1_ticker_pool_sample.csv - regenerated sample.
- data/processed/phase21_1_ticker_pool_summary.json - regenerated telemetry.
- docs/saw_phase21_round2_8.md - this report.

## Structural Diagnostic (R_anchor on 2024-12-24)
- Anchor tickers present: MU (cyc=0.817, def=0.024, junk=0.159), CIEN (cyc=0.394, def=0.181, junk=0.425)
- R_anchor mean: cyc=0.606, def=0.103, junk=0.292 -> k_cyc=0
- mu_view: centroid of MU+CIEN in 8-D z-score space (N=2 rows)
- prec_view: LedoitWolf with N=2 -> shrinkage~1.0 -> near-identity precision -> isotropic view
- Root cause of persistent failure: with N=2 anchors and 8 features, LedoitWolf precision is near-identity.
  d2_view = diff @ I @ diff.T = sum of squared z-differences from mu_view, isotropic.
  SMCI/WBA/USO sit close to mu_view in Euclidean z-space on this date despite not being MU-style.
  The Bayesian update cannot discriminate them because the PM view carries no directional information.

SAW Verdict: BLOCK

Open Risks:
- Gate fails on 4 of 5 primary criteria: MU-style count (2 vs 4), seed presence (MU+CIEN absent),
  PLUG/TZA (PLUG in top-8), deep-space (3 violations).
- Root cause is structural: with N=2 anchors and 8 feature dimensions, LedoitWolf precision collapses
  to near-identity. The PM view cannot encode directional archetype geometry. The Bayesian update
  degenerates to an isotropic Euclidean distance from mu_view, which SMCI/WBA/USO happen to win.
- Both Patch A (logit) and Round 2.8 (Bayesian) scoring upgrades have been applied and blocked.
  The 3-component hand-crafted posterior is not producing a clean cyclical cluster on 2024-12-24.

Next action:
- Patch A + Round 2.8 complete -- paused, no other changes. Await orchestrator GO/ABORT/DIAGNOSE decision.
- Key diagnostic for orchestrator: on 2024-12-24, MU scores logO_prior=1.497 but is outranked by
  tickers with high logLambda (close to isotropic mu_view). The fix likely requires either
  (a) expanding the anchor basket to include COHR/TER to give LedoitWolf more than 2 rows, or
  (b) switching from Euclidean mu_view to a directional axis (first principal component of anchor basket).

ClosurePacket: RoundID=R21_BAYES_LOGODDS_20260221; ScopeID=S21_BAYESIAN_VIEW_R28; ChecksTotal=5; ChecksPassed=4; ChecksFailed=1; Verdict=BLOCK; OpenRisks=gate fails mu_style(2 of 4) seed_presence(MU+CIEN absent) plug_tza(PLUG) deep_space(3 violations) LedoitWolf_near_identity_N2; NextAction=paused await orchestrator decision
ClosureValidation: PASS
SAWBlockValidation: PASS
