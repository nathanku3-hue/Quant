# Phase 23 Masterplan: Supply-Demand-Margin (SDM) Cycle Rebuild

## Status
- Phase: `23`
- Scope: Replace Phase 22 BGM input geometry with economically causal SDM cycle features.
- Owner: Research/Strategy Engineering

## Core Thesis
\(Alpha = f(\text{Supply}, \text{Demand}, \text{Margin} \mid \text{Cycle})\)

\[
\text{Alpha} = f(\text{Supply},\text{Demand},\text{Margin}\mid\text{Cycle})
\]

This roadmap formalizes an unsupervised feature rebuild so clustering and ranking learn **economic cycle state** rather than backward-looking price/risk buckets.

## Declaration of Replacement (Non-Optional)
The SDM rebuild in this document **replaces** the statistical/price-exhaust feature set currently feeding the Phase 22 BGM model (dominant vol/beta/momentum/liquidity geometry). Those inputs may remain for risk sizing/control, but they are no longer the primary clustering manifold.

## Notation
- \(i\): firm, \(g(i)\): firm industry, \(t\): date.
- \(\epsilon\): small positive constant for numerical safety.
- \(z(\cdot)\): cross-sectional robust standardization at date \(t\).
- \(\text{IndMedian}_g(\cdot)\): cross-sectional median within industry \(g\) at date \(t\).
- \(\Delta x_{t} = x_t - x_{t-1}\).

## Minimal MVP Feature Set (9 + 1 Interaction)

### A) Industry State (3)

1. **SupplyTight**
\[
\text{SupplyTight}_{g,t} = -z(\text{ind\_capex\_growth}_{g,t}) - z(\Delta\text{ind\_inv\_to\_sales}_{g,t}) - z(\text{ind\_inv\_growth}_{g,t})
\]

2. **DemandImpulse**
\[
\text{DemandImpulse}_{g,t} = z\!\left(\text{IndMedian}_g(\text{rev\_rev3m}_{i,t})\right) + z\!\left(\text{IndMedian}_g(\text{diffusion}_{i,t})\right) + z\!\left(\Delta\text{IndMedian}_g(\text{btb}_{i,t})\right)
\]

3. **MarginInflect**
\[
\text{MarginInflect}_{g,t} = z\!\left(\text{IndMedian}_g(\Delta GM_{i,t})\right) + z\!\left(\text{IndMedian}_g(\text{margin\_rev}_{i,t})\right)
\]

### B) Firm Relative (2)

4. **rel_capex_disc**
\[
\text{rel\_capex\_disc}_{i,t} = -\left(\text{capex\_to\_sales}_{i,t} - \text{IndMedian}_{g(i)}(\text{capex\_to\_sales}_{\cdot,t})\right)
\]

5. **rel_inv_clean**
\[
\text{rel\_inv\_clean}_{i,t} = -\left(\text{inv\_to\_sales}_{i,t} - \text{IndMedian}_{g(i)}(\text{inv\_to\_sales}_{\cdot,t})\right)
\]

### C) Revisions (4)

6. **rev_rev1m**
\[
\text{rev\_rev1m}_{i,t} = \frac{\text{RevEst}^{NTM}_{i,t}-\text{RevEst}^{NTM}_{i,t-21}}{\max\!\left(\left|\text{RevEst}^{NTM}_{i,t-21}\right|,\epsilon\right)}
\]

7. **rev_rev3m**
\[
\text{rev\_rev3m}_{i,t} = \frac{\text{RevEst}^{NTM}_{i,t}-\text{RevEst}^{NTM}_{i,t-63}}{\max\!\left(\left|\text{RevEst}^{NTM}_{i,t-63}\right|,\epsilon\right)}
\]

8. **eps_rev3m**
\[
\text{eps\_rev3m}_{i,t} = \frac{\text{EPSEst}^{NTM}_{i,t}-\text{EPSEst}^{NTM}_{i,t-63}}{\max\!\left(\left|\text{EPSEst}^{NTM}_{i,t-63}\right|,\epsilon\right)}
\]

9. **margin_rev**
\[
\text{margin\_rev}_{i,t} = z(\text{eps\_rev3m}_{i,t}) - z(\text{rev\_rev3m}_{i,t})
\]

### D) Interaction (1)

10. **CycleSetup**
\[
\text{CycleSetup}_{i,t} = \text{SupplyTight}_{g(i),t} \times \text{DemandImpulse}_{g(i),t}
\]

## 8-Step Integration Plan (Data Engineering Sequence)

1. **Create PIT consensus-estimates lake** (`data/processed/estimates.parquet`).
- Required fields: `permno`, `ticker`, `published_at`, `horizon`, `metric`, `value`, optional `up_count/down_count/dispersion`.
- **Hard requirement:** all estimate features must be queryable by `published_at <= as_of_date`.

2. **Build daily PIT estimates panel** (`data/processed/daily_estimates_panel.parquet`).
- Use interval expansion: \([published\_at_k, published\_at_{k+1})\).
- Enforce deterministic expansion and atomic write.

3. **Join layer extension (PIT-safe)**.
- Join `prices × daily_fundamentals_panel × daily_estimates_panel × sector_map` using date-as-of semantics.

4. **Implement SDM FeatureSpecs (vectorized)**.
- Add the 9 MVP features + `CycleSetup` into FeatureSpec registry.
- Add industry aggregates and relative transforms.

5. **Neutralization/conditioning policy**.
- Keep SDM industry-state variables unneutralized.
- Reserve price/risk features for risk controls only.

6. **Swap Phase 22 BGM input manifold to SDM**.
- Primary clustering matrix = SDM features (+ optional minimal residual momentum validator).
- Remove statistical/price-exhaust inputs from primary geometry.

7. **Cycle conditioning output wiring**.
- Emit `cycle_state_probs`, `cycle_confirm_industry`, and `cycle_conditioned_score` pre-selection.

8. **Acceptance tests (must pass before promotion)**.
- PIT leak test for estimate revisions.
- Determinism/hash stability test.
- Missingness/fallback behavior test.
- Slice reproducibility tests vs fixed seeds.

## Implementation Guardrails
- Point-in-Time policy is non-negotiable for consensus estimates.
- No silent NaN propagation; explicit fallback or explicit exclusion only.
- Keep all material writes atomic (`tmp -> os.replace`).
- Preserve deterministic sampling/seed behavior.

## Promotion Gate (Phase 23 Entry)
- SDM manifold replaces Phase 22 geometry in ranking path.
- Baseline telemetry must include Jaccard stability, silhouette, and archetype recall.
- Final hard thresholds are set by PM after baseline review.

## Deliverables
- `data/processed/estimates.parquet`
- `data/processed/daily_estimates_panel.parquet`
- FeatureSpec additions for SDM + `CycleSetup`
- Updated BGM input pipeline using SDM manifold
- PIT + determinism test evidence
