"""Append remaining SAW round2_8 sections in one shot."""
remaining = """
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
"""
with open("docs/saw_phase21_round2_8.md", "a", encoding="utf-8") as f:
    f.write(remaining)
print("SAW round2_8 complete.")
