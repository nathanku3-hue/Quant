# GodView Portfolio P0 Owner Freeze

Status: Active Canon — High-Confidence Audit Reconciliation Applied
Date: 2026-07-16
Mode: `APPROVAL_GATE`
Authority: owner-approved portfolio architecture, owner-decision audit, and 2026-07-16 independent pre-build audit reconciliation

## Decision

```text
BUILD_SYNTHETIC_NOW
MAX_PARALLEL_IMPLEMENTATION_AUTHORIZED
FIRST_REAL_PROSPECTIVE_CANDIDATE_ONLY_AFTER_PORTFOLIO_P0_AND_REAL_DATA_ADMISSION_GATE_PASS
```

This document authorizes deterministic synthetic implementation, contract fixtures, accounting, policy controls, and an independent verification path. It does not authorize provider acquisition, establish real-data availability, prove alpha, or authorize live capital.

## Reconciliation Register

### Accepted and frozen

- portfolio-first truth before optimizer complexity;
- permanent capped-equal-weight control;
- explicit residual cash and an actual IWB residual-cash shadow portfolio;
- authoritative bitemporal universe, identity, sector, market, benchmark, cash-rate, corporate-action, and delisting inputs;
- raw-price accounting with explicit corporate actions rather than adjusted-close portfolio truth;
- complete search-family history and multiplicity-aware inference;
- issuer-level clustering and complete portfolio time series as the primary evidence unit;
- independent replication using new future information, independent implementation, independent raw-data reconstruction, and an independent reviewer;
- deterministic primary ledger plus a separate verifier; optimizer output may propose targets but never owns official returns.

### Modified

- `IWB_total_return_USD` means **IWB market-price total return with distributions reinvested and fund expenses embedded**. IWB NAV total return is a secondary reconciliation series. IWB holdings are not Russell 1000 membership authority.
- The external audit proposed 5% ADV20 order participation and 25% ADV20 position capacity. The existing owner freeze remains more conservative at 2% and 5% respectively until empirical calibration supports relaxation.
- The previous monthly turnover wording becomes an exact rolling-session rule: 25% one-way turnover over 21 trading sessions and 150% over 252 trading sessions.
- Exact economic-return and drawdown thresholds remain owner calibration choices. Dependence-aware inference and hard disposition structure are frozen now; numerical financial hurdles are not silently treated as universal truths.
- External repositories are implementation candidates only. No new platform dependency becomes canon before a measured need and bounded adoption decision.

### Rejected

- current constituents, ETF holdings, ticker continuity, current sector labels, adjusted closes, or reconstructed lists as point-in-time authority;
- silent substitution or forward filling for missing membership, identity, corporate action, delisting, benchmark, or SOFR authority;
- pasting a benchmark return onto residual cash instead of simulating the IWB shadow as a real hypothetical holding;
- treating repeated issuer episodes, reruns, bootstrap samples, code forks, or same-data reprocessing as independent replication;
- optimizer replacement of the permanent capped-equal-weight control;
- Sharpe, significance, episode count, synthetic performance, or architecture correctness as sufficient alpha evidence.

## 1. Frozen Initial Mandate

```yaml
mandate_id: US_R1000_STRUCTURAL_EW_V1
market: US_primary_listed_common_equities
universe: point_in_time_russell_1000_common_equities
primary_benchmark: IWB_market_price_total_return_USD
secondary_benchmark_reconciliation: IWB_NAV_total_return_USD
currency: USD
reference_nav: 10000000
cash_return: compounded_SOFR_minus_25bp_ACT360
sector_taxonomy: point_in_time_ICB_industry_level_1
policy: capped_equal_weight
security_cap: 0.10
issuer_cap: 0.10
sector_cap_total_nav: 0.30
max_positions: 20
min_valid_sessions_in_prior_20: 15
min_20d_median_dollar_volume: 20000000
max_trade_share_of_ADV20_per_session: 0.02
max_position_share_of_ADV20: 0.05
rolling_21_session_one_way_turnover_cap: 0.25
rolling_252_session_one_way_turnover_cap: 1.50
residual_cash: retain_in_cash
forced_full_investment: false
leverage: false
shorting: false
derivatives: false
fx_positions: false
```

Excluded securities include ETFs, funds, preferred shares, warrants, OTC securities, blank-check shells, and non-primary ADR listings.

## 2. Authoritative Bitemporal Data Contract

Every source record or source file used by a real run must preserve:

```text
source_identity
raw_content_hash
vendor_publication_timestamp
system_receipt_timestamp
first_available_timestamp
announced_effective_timestamp
actual_effective_timestamp
valid_from
valid_to
correction_or_restated_from_identity
```

Corrections append a new version. They never overwrite the exact input available to a prior prospective decision.

### Russell 1000 membership

Required properties:

- official or demonstrably equivalent licensed constituent files and change notices;
- preliminary, lock-down, final, correction, and effective states retained when supplied;
- permanent security and issuer identities, share-class state, addition/deletion reason, and effective date;
- immutable copies of exact files available before each decision.

Eligibility uses final effective membership known at the decision cutoff. Preliminary lists are archived but cannot create early eligibility.

When membership is missing, contradictory, late, or not tied unambiguously to a permanent security:

- no new position or increase;
- existing positions continue to be marked from authoritative market data;
- confirmed mandatory exits may proceed;
- the decision records `DATA_ABSTENTION`;
- current membership, ETF holdings, Wikipedia, price history, or ticker continuity cannot repair the gap.

### Permanent security and issuer identity

The security master must provide validity-dated equivalents of:

```text
permanent_security_id
permanent_issuer_id
CUSIP / ISIN / FIGI when available
exchange symbol and primary listing
security type and share class
active / halted / suspended / when-issued / delisted state
predecessor / successor / merger / spin-off lineage
```

Ticker, company name, current CUSIP, or current FIGI alone is insufficient. Issuer limits and observation clustering follow permanent issuer lineage.

### Point-in-time sector classification

- taxonomy: ICB Industry Level 1 or an owner-approved equivalent encoded before the first candidate;
- classification effective at the decision timestamp;
- issuer-level aggregation;
- 30% cap measured against total portfolio NAV, not invested-equity NAV;
- unknown or conflicting classification blocks a new position or increase;
- reclassification begins only at its published effective time.

### Raw market and execution inputs

The canonical package must support:

- unadjusted daily OHLC;
- official auction prices or consolidated trades/quotes sufficient for the frozen execution window;
- raw share and dollar volume;
- correction, price-condition, and trade-status flags;
- halt, suspension, reopening, and listing-status events;
- official primary-exchange calendars, early closes, unscheduled closures, and trade-date timestamps.

Adjusted close may be retained only as an independent reconciliation field.

### Corporate actions and delistings

Required event classes include:

- ordinary, special, and liquidating cash distributions;
- splits, reverse splits, stock dividends, and rights;
- cash, stock, and mixed mergers, election terms, fractional-share treatment, and delayed consideration;
- spin-off ratio, distributed security identity, when-issued state, first tradable date, and later cash proceeds;
- ticker, name, exchange, and share-class changes;
- halts, suspensions, resumptions, bankruptcies, delistings, final consideration, and recoveries.

Fail-closed rules:

- never infer a split from a price jump alone;
- never remove a delisted security without official consideration, a registered impairment, or an unresolved receivable state;
- never convert a missing price to zero;
- unresolved corporate actions quarantine the security from new trades and discretionary resizing;
- prior prospective records remain visible after vendor corrections.

## 3. Benchmark, Shadow, and Cash Semantics

### Primary benchmark

`C0_PRIMARY_BENCHMARK` is IWB market-price total return with distributions reinvested. Fund expenses remain embedded. No benchmark transaction-cost deduction is added.

IWB NAV total return is a secondary reconciliation series. Monthly cumulative market-price and NAV returns are compared with published series; differences greater than 5 basis points require investigation before certification.

### Residual-IWB shadow

`P7_RESEARCH_EW_RESIDUAL_BENCHMARK_FIXED_TIMING_NET` is an actual hypothetical portfolio:

- it holds the same common-equity quantities as `P2`;
- every dollar held as cash in `P2` is instead held in IWB;
- IWB trades use the same timing, availability, transaction-cost, dividend, and corporate-action rules;
- the shadow is not constructed by applying a published benchmark return to the cash balance.

Interpretation:

```text
total_policy_active_return = P2 versus C0
security_choice_diagnostic = P7 versus C0
cash_and_abstention_effect = P2 versus P7
```

Full-period comparisons use geometrically linked wealth ratios. Daily arithmetic differences may be used for reconciled attribution only.

### SOFR cash return

For an accrual interval of `calendar_days`:

```text
cash_factor = 1 + ((SOFR_percent / 100) - 0.0025) * calendar_days / 360
```

Rules:

- ACT/360;
- no zero floor;
- the official rate is used only after publication;
- interest accrues to a separate cash-interest ledger account;
- missing official SOFR blocks certification; no silent proxy substitution.

## 4. Capped Equal Weight and Constraint Order

For `N <= 20` eligible issuers:

```text
uncapped_target_i = min(0.10, 1 / N)
```

Apply in this order:

1. aggregate all share classes at issuer level;
2. proportionally scale issuers in any sector above 30% of total NAV;
3. apply security, issuer, and liquidity capacity ceilings;
4. round down using the frozen whole-share rule;
5. retain every removed or rounded amount as cash.

No cap-induced reduction is redistributed. No high-conviction or discretionary override exists.

Excess eligible issuers are ordered deterministically by decision timestamp and candidate ID until the 20-issuer limit is reached.

## 5. Liquidity, Turnover, and Passive Drift

- `ADV20` is the median consolidated daily dollar volume over at least 15 valid sessions in the prior 20 sessions.
- Maximum simulated order per issuer per session is 2% of ADV20.
- Maximum post-trade issuer position is 5% of ADV20.
- No order executes during a halt, suspension, stale-price state, unresolved corporate action, or ambiguous listing state.
- Liquidity-constrained weight remains cash.

One-way turnover is:

```text
turnover_t = 0.5 * sum_j(abs(post_trade_weight_j - pre_trade_drifted_weight_j))
```

Cash and IWB shadow holdings are included. Limits are 25% over rolling 21 sessions and 150% over rolling 252 sessions. Initial formation is exempt from the numerical limit but remains fully costed and reported. Forced corporate-action trades are included and separately tagged.

Trade targets obey the 10% issuer and 30% sector caps. Passive drift creates:

- warning above 10% issuer or 30% sector;
- mandatory reduction at the next eligible execution above 11% issuer or 32% sector;
- temporary additional positions from corporate actions are resolved by a frozen disposition rule.

## 6. Execution and Cost Contract

Two permitted timing variants are frozen as interfaces:

```text
T1_OPENING: information complete by 20:00 ET before session; execute next eligible session 09:35–10:05 ET consolidated VWAP
T2_CLOSING: information complete by 20:00 ET before session; execute next eligible session 15:30–16:00 ET consolidated VWAP
```

The candidate method must select one primary timing variant before admission. The other counts against the timing-variant search budget. Missing the cutoff moves execution to the following eligible session. Same-day retroactive execution is prohibited.

A base and conservative-stress one-way cost model are mandatory. Both apply to identical gross trades; stress results cannot be re-optimized after outcomes. Spread, volatility, participation, dated fee inputs, coefficients, calibration sample, and frozen floors must be encoded before the first real candidate. Any post-unblinding recalibration that changes cumulative candidate net return by more than 10 basis points is material and resets the affected prospective window.

## 7. Candidate Episodes and Observation Independence

Required identity:

```text
parent_thesis_id
episode_id
issuer_id
mechanism_id
decision_timestamp
registered_horizon
observation_cluster_id
```

- permitted horizons: `12M`, `18M`, `24M`; default `18M`;
- non-material research updates remain in the same episode and do not reset maturity;
- changes to hypothesis, mechanism, horizon, falsifier/invalidation logic, authority, eligibility, earliest execution time, benchmark, or primary endpoint close the prior episode as `SUPERSEDED`;
- reopening in an active episode is another action under the same episode;
- reopening after a terminal state creates a new episode under the same parent thesis;
- same-issuer overlapping episodes are one issuer-time cluster;
- same-issuer/same-mechanism episodes remain one thesis cluster for the protocol version;
- complete prospective portfolio time series is primary;
- candidate outcomes are diagnostics and are dependence-clustered when inference is reported.

Terminal states:

```text
MATURED_HORIZON
INVALIDATED_EARLY
CLOSED_BY_POLICY
EXPIRED_NO_POSITION
REJECTED
SUPERSEDED
CENSORED_PROGRAM_END
BLOCKED_DATA_OR_CORPORATE_ACTION
```

## 8. Evidence Clock and Search Budget

Governance clock:

```text
12 months + 8 qualified episodes + 6 unique issuers: operational checkpoint
36 months + 24 matured unique-issuer clusters: first directional economic assessment
48 months + 40 matured clusters + untouched future segment: promotion-quality paper assessment
60 months: mandatory final disposition; no automatic extension
```

These thresholds do not prove statistical sufficiency or alpha.

Search budget:

```yaml
candidate_method_material_versions: 3
policy_variants:
  equal_weight: 1
  return_aware: 2
  optimizer: 3
  timing: 2
cost_models:
  base: 1
  conservative_stress: 1
review_after_failed_independent_methods: 3
terminate_or_reset_after_failed_independent_methods: 5
```

Every outcome-exposed parameter vector, informal chart inspection, notebook experiment, abandoned run, and manual tuning attempt counts. Closed families remain visible and cannot be reopened through renamed nearby specifications.

## 9. Dependence-Aware Inference Contract

Freeze the method family now:

- joint stationary bootstrap across policy, controls, shadow, timing, and challenger returns;
- primary mean block length: 20 trading days;
- 50,000 replications and one published seed;
- identical bootstrap indices across all compared strategies;
- studentized statistics;
- 5-day and 60-day block-length sensitivities reported but not used to choose the verdict;
- Romano–Wolf stepdown family-wise-error control as primary multiplicity procedure;
- Hansen SPA as secondary family-level diagnostic;
- issuer-cluster analysis as a secondary candidate-level diagnostic;
- testing family includes every outcome-exposed variant, failure, abandonment, and manually inspected specification.

Exact financial hurdles for 36-, 48-, optimizer-, and 60-month decisions remain separately frozen before the relevant assessment. Sharpe or nominal significance alone is never a promotion gate.

## 10. Independent Replication Contract

Replication requires all of:

1. untouched future information beginning only after protocol, code, data schema, cost model, and execution rules are sealed;
2. materially new issuers and preregistered mechanism or market-context coverage;
3. a second implementation created from the frozen prose specification without sharing primary strategy/accounting/corporate-action/return modules;
4. independent reconstruction of universe, identity, sector, corporate-action, execution-price, daily-return, and cash tables from immutable raw inputs;
5. an independent reviewer with no signal, parameter, or optimizer-selection role and authority to fail unblinding;
6. the same primary execution and cost assumptions as the original protocol;
7. reconciliation before unblinding: exact eligibility and quantities after rounding, cash within USD 0.01 per event, daily NAV within 1 bp, and cumulative return within 5 bp.

Reruns, new random seeds, same-data cross-validation, bootstrap samples, another optimizer, alternative timing/cost stress, code forks sharing logic, or reprocessing cleaned intermediate data are reproducibility or robustness—not replication.

The exact untouched duration and required new-issuer/mechanism counts remain an owner calibration because they must be consistent with 12/18/24-month candidate horizons.

## 11. First Real Candidate Admission Gate

No waiver is permitted. Before the first prospective decision:

- all four portfolio P0 artifacts encode and validate this freeze;
- at least 60 consecutive trading sessions of authoritative universe, identity, sector, market, corporate-action, IWB, and SOFR feeds are captured immutably;
- expected-file delivery completeness is at least 99.95%;
- unresolved membership, issuer, sector, benchmark, SOFR, or corporate-action contradictions equal zero;
- raw snapshots, canonical tables, code, configuration, and protocol have immutable signed hashes;
- capped equal weight, P7 shadow, timing, cost, liquidity, turnover, and accounting rules are sealed;
- at least 252 synthetic sessions replay identically on two consecutive runs;
- at least 20 golden corporate-action scenarios pass;
- property tests show no NAV, share, cash, causality, identity, or constraint violation;
- the independent path agrees on eligibility and holdings exactly, cash within USD 0.01 per event, daily NAV within 1 bp, and cumulative return within 5 bp;
- candidate mechanism, availability map, clustering/maturity, ranking/tie-break, timing, and search-family manifest are preregistered;
- an independent reviewer signs the data, accounting, protocol, and unblinding checklist;
- the first decision timestamp is strictly after that signature and protocol timestamp.

## 12. Portfolio P0 Artifacts and First Policies

Exactly four P0 artifacts:

```text
p0_economic_protocol.yaml
candidate_contract.schema.json
portfolio_truth_spec.md
p0_acceptance_tests.md
```

Implement now:

```text
C0_PRIMARY_BENCHMARK
C1_CASH_CONTROL
P1_RESEARCH_EW_FIXED_TIMING_GROSS
P2_RESEARCH_EW_FIXED_TIMING_NET
P7_RESEARCH_EW_RESIDUAL_BENCHMARK_FIXED_TIMING_NET
```

Freeze interfaces only:

```text
P3_RESEARCH_EW_CASH_EXPOSURE_MATCHED_CONTROL
P4_RETURN_AWARE_FIXED_TIMING_NET
P5_OPTIMIZER_FIXED_TIMING_NET
P6_RESEARCH_EW_TIMING_OVERLAY_NET
```

## Remaining High-Value Questions

None blocks synthetic implementation.

1. Which licensed or otherwise authoritative sources satisfy the bitemporal Russell membership, permanent identity, point-in-time ICB, execution, corporate-action, delisting, IWB, and SOFR contract, and what acquisition rights are authorized?
2. Which timing variant is primary for structural candidates: `T1_OPENING` or `T2_CLOSING`?
3. What exact base/stress cost coefficients and non-candidate calibration sample are frozen before the first real candidate?
4. What exact net-active-return, security-choice, drawdown, concentration, cost-stress, and optimizer-increment hurdles govern the 36-, 48-, and 60-month assessments?
5. What untouched duration and new-issuer/mechanism counts constitute replication without conflicting with 12/18/24-month candidate horizons?

## Held

- provider or data acquisition without separate authority;
- real candidate admission before the full admission gate;
- automatic factor-adjusted alpha as the first endpoint;
- return-aware or optimizer production preference;
- event-alpha implementation in P0;
- external platform adoption without a bounded dependency decision;
- broker, live orders, leverage, shorts, derivatives, or live capital;
- persistent-alpha claims from architecture, synthetic tests, historical backtests, or paper accounting correctness.
