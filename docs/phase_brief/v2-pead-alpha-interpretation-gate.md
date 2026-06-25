# V2 PEAD Alpha Interpretation Gate

Mode: `APPROVAL_GATE`
Status: `OPEN_DOCS_ONLY; INITIAL CLAIM BOUNDARY SELECTED; NO ALPHA DASHBOARD AUTHORITY`
Date: 2026-06-24
RoundID: `ROUND-20260624-V2-PEAD-ALPHA-INTERPRETATION-GATE`
ScopeID: `V2_PEAD_ALPHA_INTERPRETATION_GATE_DOCS_ONLY`
Owner: Strategy + Docs/Ops

## Objective and authority

Open a docs-only interpretation gate for the current V2 PEAD evidence. The gate task is not how to display alpha. The gate task is to decide what the current evidence can honestly claim without violating its own evidence policy, data limitations, or product-action boundary.

This round authorizes documentation and planning alignment only. It does not authorize code, provider access, data generation, evidence mutation, dashboard implementation, ranking/scoring, alerts, recommendations, order paths, staging, or commit.

## Evidence under interpretation

Primary evidence file: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.

Key recorded figures:

- `primary_inference.alpha_ct = 0.0007053337347976517`
- `primary_inference.alpha_hac_t_stat = 9.582565792521386`
- `primary_inference.observations = 2552`
- `daily_summary.spread.mean = 0.0006903400931746636`

These figures are methodology evidence only. They are not an alpha claim.

## Evidence policy facts

The evidence policy is self-limiting:

- `allowed_use = bounded_methodology_review_only`
- `interpretation_performed = false`
- `strategy_promotion_authorized = false`
- `ranking_or_scoring_authorized = false`
- `alerts_or_recommendations_authorized = false`
- `broker_or_order_path_authorized = false`
- `forbidden_use` includes `alpha_claims`, `full_factor_alpha_claims`, `net_performance_claims`, `causal_claims`, `tradability_claims`, `strict_point_in_time_claims`, and `population_validity_claims`.

Therefore a product or roadmap surface that calls this evidence alpha, or implies alpha through a dashboard name, is not allowed by the evidence's own policy.

## Limitation facts

Current limitations are claim-limiting:

- `eps_vintage = current_vintage_compustat_eps`: current/restated EPS can create restatement hindsight and is not strict PIT EPS.
- `return_source = compustat_total_return_proxy`: return data is a Compustat proxy, not a final CRSP/delisting-adjusted stream.
- `delisting_adjustment = none`: no delisting-return adjustment is present.
- `factor_model = single_factor_mktrf_gross_equal_weight_q5_minus_q1`: inference is gross, equal-weight, Q5-minus-Q1, and single-factor only.
- `sample_universe = fixed_500_gvkey_current_vintage_sample`: population validity is not established.

## Gate conclusion: maximum honest current claim

Current evidence can support only this descriptive, methodology-only statement:

> Observed PEAD-style post-earnings-drift shape in a single-factor gross equal-weight Q5-minus-Q1 spread, using current-vintage Compustat EPS and Compustat proxy returns; explicitly non-alpha, non-tradable, non-PIT, non-causal, non-net, and not population-valid.

Forbidden wording: do not call it alpha, tradeable, PIT, net performance, or strategy promotion; do not imply ranking/scoring, alerts, recommendations, or order readiness; do not name the next panel `Alpha dashboard`, `Alpha dashboard MVP`, or any alpha-equivalent user-facing surface.

## Revised ship-fast roadmap branch

Replace the previous M4C dashboard-first route with this gate-controlled branch.

### Path A: owner wants to show only current facts

Build a descriptive evidence panel after gate approval only. Allowed framing is read-only CAR/BHAR/spread/coverage numbers plus hard disclaimers: `not alpha`, `not tradeable`, `not PIT`, `look-ahead/current-vintage EPS`, `gross`, `single-factor`, `proxy returns`, and `no delisting adjustment`.

Disallowed framing is alpha dashboard, alpha score, strategy promotion, action, alert, ranking, or recommendation state.

### Path B: owner wants a real alpha assertion

Do not build a dashboard first. Open a separate M5 data/method upgrade round first: PIT EPS vintage, delisting-adjusted returns, net-cost treatment, and multi-factor model specification. Until M5 evidence exists and passes a new interpretation gate, there is no interpretable alpha assertion.

## Hard stop before any alpha code

No alpha-named or alpha-implying code may be written while either condition remains true:

1. the pending 28-commit branch state has not been merged or reconciled into `main`; or
2. this Alpha Interpretation Gate spec has not been approved.

This hard stop applies to dashboard naming, UI labels, route names, cards, data model fields, tests, and docs that would imply alpha authority.

## Research-analysis backing

Hierarchy Confirmation: Approved | Session: current-thread fallback | Trigger: project-init fallback | Domains: financial | FallbackSource: `docs/spec.md` + active PEAD phase briefs.

High-confidence claim support:

- `CLM-01`: current evidence policy directly forbids alpha claims. Source: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`, section `evidence_policy.forbidden_use`.
- `CLM-02`: current evidence policy directly forbids strict point-in-time and tradability claims. Source: same JSON, section `evidence_policy.forbidden_use`.
- `CLM-03`: current evidence uses current-vintage Compustat EPS, so strict PIT EPS validity is not established. Source: same JSON, section `limitations.eps_vintage`.
- `CLM-04`: current evidence uses Compustat proxy returns and no delisting adjustment. Source: same JSON, sections `limitations.return_source` and `limitations.delisting_adjustment`.
- `CLM-05`: Fama (1998) supports calendar-time aggregation as a methodology choice for overlapping event-return inference, but does not remove this repo evidence's PIT/proxy/gross/single-factor limitations. Source: `docs/research/fama_1998_market_efficiency_long_term_returns.pdf`, journal page 295 / PDF page 13, as already extracted in `docs/research/pead_inference_methodology_claims_20260621.json`.

This gate uses the existing M1B evidence JSON policy/limitation fields as direct repo evidence and the existing Fama extraction at `docs/research/pead_inference_methodology_claims_20260621.json` for methodology support. No new research PDF extraction is needed in this docs-only round.

Logic chain: if the evidence policy forbids alpha/PIT/tradability claims and the limitations include current-vintage EPS, proxy returns, no delisting adjustment, and single-factor gross inference, then the only honest current claim is descriptive methodology evidence, not alpha.

Formula summary: current statistic is `R_HL,t = EW(Q5 raw return)_t - EW(Q1 raw return)_t`; `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`; `alpha_CT` is only a single-factor calendar-time intercept in this limited evidence context.

## Acceptance checks

- [ ] Gate spec approved or held by owner.
- [x] Current evidence policy and limitations are named explicitly.
- [x] Maximum honest current claim is bounded to descriptive methodology evidence.
- [x] Path A / Path B roadmap branch is specified.
- [x] Alpha-named dashboard/code is blocked until gate approval and branch/merge status is resolved.
- [x] No code, data, provider, evidence artifact, dashboard runtime, ranking/scoring, alert, recommendation, or order scope is authorized.

## Rollback

This is docs-only. Rollback is deletion of this brief and removal of the corresponding current-truth, PRD/spec, notes, decision-log, lesson, research-claim, and SAW addenda. No runtime state or data artifact is touched.
