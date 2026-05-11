# G7 Candidate Family Definition Policy

Status: Phase 65 G7 policy
Authority: D-364 Phase G7 first controlled candidate-family definition, no search

## Purpose

G7 creates the first family-level research contract before any candidate generation or result observation. It is preregistration-style governance for future research: family boundaries, allowed features, finite parameter space, trial budget, data policy, validation gates, and multiple-testing policy are declared before outcomes exist.

This policy is not strategy search, alpha evidence, candidate ranking, paper alert readiness, broker permission, or promotion authority.

## Allowed Scope

- Family ID: `PEAD_DAILY_V0`.
- Status: `defined`.
- Universe: `US_EQUITIES_DAILY_CANONICAL`.
- Data policy: Tier 0 and `source_quality = canonical` for future promotion evidence.
- Sidecar policy: `sidecar_required = false` for the G7 definition artifact.
- Feature allowlist:
  - `earnings_event_flag`
  - `earnings_surprise_bucket`
  - `liquidity_filter`
  - `price_return_window`
- Finite parameter space:
  - `holding_days = {1, 3, 5, 10}`
  - `liquidity_floor = {adv_usd_5m, adv_usd_20m, adv_usd_50m}`
  - `event_window_lag = {1, 2}`
- Trial budget:
  - `trial_budget_max = 24`
  - `finite_trial_count = 4 * 3 * 2 = 24`
- Required future validation gates:
  - OOS
  - walk-forward
  - regime tests
  - permutation
  - bootstrap
- Future multiple-testing/accounting gates:
  - multiple-testing policy
  - PSR or DSR
  - reality check or SPA

## Required Gates

- Family definition must exist before any candidate in that family can be created.
- Family definition must be manifest-backed.
- Family definitions are append-only/versioned. Silent mutation is blocked.
- `trial_budget_max` is required.
- `parameter_space` must be finite and non-empty.
- `allowed_features` must be finite and non-empty.
- `data_tier_required = tier0`.
- `source_quality_required = canonical`.
- Tier 2, yfinance, OpenBB, and operational Alpaca sources cannot be allowed as promotion evidence.
- Report output must remain definition-only with candidate generation disabled, result generation disabled, `promotion_ready = false`, `alerts_emitted = false`, and `broker_calls = false`.

## Blocked Scope

- No candidate generation.
- No backtest, replay, proxy run, strategy search, factor model, PEAD run, momentum, value, ML, parameter sweep, or result comparison.
- No Sharpe, CAGR, alpha, drawdown, score, rank, signal strength, buy/sell decision, best parameter, promotion verdict, paper alert, alert emission, broker call, Alpaca call, OpenClaw message, notifier path, or promotion packet.

## Formula Register

- `finite_trial_count = product(count(options_p) for p in parameter_space)`.
- For `PEAD_DAILY_V0`: `finite_trial_count = 4 * 3 * 2 = 24`.
- `trial_budget_valid = true` iff `finite_trial_count <= trial_budget_max`.
- `family_defined_for_candidate = true` iff the family JSON exists, its manifest exists, the manifest SHA-256 matches the JSON artifact, `row_count = 1`, `family_id` matches, and `version` matches.

Source paths:
- `v2_discovery/families/schemas.py`
- `v2_discovery/families/trial_budget.py`
- `v2_discovery/families/registry.py`
- `v2_discovery/families/validation.py`

## Evidence

- `tests/test_g7_candidate_family_definition.py`
- `data/registry/candidate_families/pead_daily_v0.json`
- `data/registry/candidate_families/pead_daily_v0.json.manifest.json`
- `data/registry/candidate_family_registry_report.json`
