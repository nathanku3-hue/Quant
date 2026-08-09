# RESONANCE_LEVERAGE_POLICY_v1 — Evidence-Gated Capital Policy

**Date:** 2026-08-08
**Status:** `CAPITAL_POLICY_SPEC / EVIDENCE_GATED / NOT_IMPLEMENTED`
**Authority:** future capital-policy design only; not Core Alpha
**Current execution effect:** **NONE** — Clock #1 is running, but this capital-policy lane remains evidence/CRO-gated and unreleased. Multiple family clocks or multi-scale resonance do not themselves authorize leverage; one current portfolio/capital-policy authority remains singular even when several Alpha Families are evidence-qualified.
**Financial-alpha evidence:** `0`

---

# 0. Purpose

Define how valid stock Alpha, market-transition forecasts, entry-timing state and portfolio/risk constraints may eventually map into a desired capital regime without allowing a forecasting model to become CRO, execution or broker authority.

This policy is intentionally downstream of:

```text
single-name Core Alpha
MARKET_TRANSITION_ALPHA_v1
ENTRY_TIMING_COMPONENT_v1
```

It is not a prerequisite to their research.

---

# 1. Authority separation

Inputs may include:

```text
single-name Core Alpha
MARKET_TRANSITION_ALPHA_v1
ENTRY_TIMING_COMPONENT_v1
current portfolio state
cross-sectional alpha opportunity
liquidity / capacity
CRO envelope
optional hedge economics
```

Outputs are desired configuration only:

```text
desired_gross
desired_net
desired_single_name_concentration
desired_cash
desired_beta_hedge
desired_convex_hedge_budget
capital_regime_state
```

The policy cannot exceed CRO hard limits or directly generate broker orders. Evidence qualification may happen in parallel across families; capital-policy commits remain atomic/singular. No family receives leverage simply because several horizons agree.

---

# 2. Capital regime state machine

Do not use an opaque “resonance score → leverage multiplier” rule.

Canonical states:

```text
S0_NO_EDGE
S1_NORMAL_LONG
S2_FULL_RESONANCE
S3_DISPERSION_ALPHA
S4_DEFENSIVE_ALPHA
S5_CRISIS_HEDGE
S6_FLAT
```

`SHORT_ONLY` is outside the automatic state machine unless a genuine short Alpha Family with negative expected-return evidence and borrow authority exists.

## S0_NO_EDGE

Weak stock Alpha + weak timing + no compelling relative-value Alpha → `CASH / WAIT` is valid.

## S1_NORMAL_LONG

Positive stock-selection Alpha without exceptional market/timing resonance → ordinary long/cash configuration; no special leverage award.

## S2_FULL_RESONANCE

Eligibility requires jointly:

```text
strong single-name/core Alpha
favorable market-transition distribution
constructive price/volume timing
no severe liquidity/tail veto
capacity available
conviction calibrated
CRO authority available
```

Only then may **desired** gross/concentration exceed ordinary state. Actual capital remains mechanically capped.

## S3_DISPERSION_ALPHA

Broad direction ambiguous but cross-sectional opportunity high. Lower desired beta/net may coexist with meaningful gross only when independently valid long and short forecasts exist. Never create shorts as the inverse of longs.

## S4_DEFENSIVE_ALPHA

Market distribution deteriorating while some idiosyncratic long Alpha remains. Reduce weaker longs first, reduce net, optionally add beta hedge, preserve exceptional residual Alpha only when economics justify it.

## S5_CRISIS_HEDGE

Requires multi-clock crisis evidence. Desired policy may cut gross/net, increase cash and consider beta/convex hedges, while retaining only Alpha whose residual expected utility survives crisis assumptions.

## S6_FLAT

Severe risk and/or forecast uncertainty with no sufficient residual Alpha → `FLAT / CASH` is valid.

---

# 3. Separate kill concepts

## Operational kill

Existing `FREEZE_NEW_RISK` is triggered by broker/state/data/risk-control integrity failures. It is not a market view.

## Market-risk de-risk

A future capital state produced by valid market-transition evidence. It may reduce gross/net or increase cash/hedges without implying a system malfunction.

## Emergency flatten

Separate operator/CRO authority may flatten regardless of Alpha when survival requires it. Manual flatten is immutable; strategy code cannot unfreeze itself.

---

# 4. `RESONANCE_GATE`

Leveraged-resonance eligibility requires explicit gates:

```text
G1 CORE ALPHA
incremental stock-selection edge; valid PIT evidence; not redundant

G2 MARKET STATE
market-transition distribution does not materially contradict payoff;
liquidity/funding state acceptable

G3 TIMING
relevant inflection/confirmation state;
temporal sequence fits preregistered expectations;
waiting has not consumed most expected edge

G4 TAIL / LIQUIDITY
no critical crisis/tail veto;
capacity, liquidity and funding resilience sufficient

G5 PORTFOLIO FIT
marginally useful to existing book;
correlation/crowding/concentration acceptable
```

Only G1–G5 passing may create leveraged-resonance eligibility. A failed gate does not automatically mean sell; exact failures are recorded.

---

# 5. Desired / allowable / feasible / actual

Freeze distinct objects:

```text
DESIRED_CAPITAL
= PM / Alpha request

ALLOWABLE_CAPITAL
= CRO envelope

FEASIBLE_CAPITAL
= liquidity / capacity / operations

ACTUAL_CAPITAL
= deterministic reconciliation of desired, allowable and feasible
```

A forecasting model never modifies CRO hard limits. Strong backtest performance cannot auto-increase leverage.

---

# 6. Leverage authority states

```text
LEVERAGE_DISABLED
NORMAL_GROSS
RESONANCE_GROSS_ELIGIBLE
LEVERAGE_REDUCED
```

No numeric leverage multiplier is frozen in architecture docs. Exact gross/net ceilings belong to the Capital Risk Budget. Any research mapping is frozen in an implementation manifest before outcomes; post-result changes create a new version/trial.

Robust fractional-Kelly may be a sizing challenger/diagnostic only. Stress edge uncertainty, probability calibration error, correlation/tail error, capacity and horizon; fragile leverage recommendations remain classified as fragile.

---

# 7. Long / short eligibility

Define independently:

```text
LONG_ALPHA_ELIGIBLE
SHORT_ALPHA_ELIGIBLE
```

`not LONG_ALPHA_ELIGIBLE` does not imply short eligibility.

Short Alpha requires:

```text
negative expected-return evidence
+ short-specific Alpha Family / Component
+ PIT borrow / locate
+ borrow economics
+ capacity
+ execution evidence
+ CRO approval
```

Missing borrow kills the short leg only. Borrow cost and recall/availability risk belong to monetizability/capital authority.

---

# 8. Hedge intent

Every hedge binds intent before result:

```text
ALPHA_SHORT
BETA_HEDGE
TAIL_HEDGE
LIQUIDITY_RESERVE
FACTOR_HEDGE
```

Intent is not inferred ex post from profitability.

Long puts are not default bearish trades. A future `PUT_HEDGE_ELIGIBLE` requires meaningful long Alpha worth retaining, material left-tail risk, acceptable option economics/liquidity, valid operational path and CRO premium budget. Put payoff is insurance, not Core Alpha.

---

# 9. Insurance / policy attribution

Separate at least:

```text
forecast_alpha_pnl
portfolio_construction_effect
leverage_effect
beta_hedge_pnl
insurance_carry
insurance_payoff
execution_effect
net_fund_pnl
```

A put losing premium in normal markets does not automatically fail; a put paying in a crash does not become forecast Alpha.

---

# 10. Capital-policy counterfactual arms

Do not validate one complicated final policy only. Where upstream forecasts are valid, compare:

```text
A BASELINE CAPITAL POLICY
B + MARKET TRANSITION DE-RISK
C + ENTRY TIMING
D + STATE-DEPENDENT LEVERAGE
E + BETA HEDGE
F later + CONVEX OPTION INSURANCE
```

This separates forecast, timing, leverage, hedge and insurance value.

Canonical portfolio marginality test:

```text
INCUMBENT PORTFOLIO
vs
INCUMBENT + MARKET_TRANSITION_ALPHA + RESONANCE_LEVERAGE_POLICY
```

Hold stock Alpha, universe, PIT data, costs, execution assumptions and CRO envelope constant.

---

# 11. Drawdown / fish-body / fish-tail diagnostic

`DRAWDOWN_RECOVERY_ATTRIBUTION_v1` is diagnostic only. It cannot promote Alpha or tune contaminated Parent/Child history.

For mechanically defined drawdown episodes record pre-peak, peak, early/late decline, trough, 5d/20d/60d rebound and full recovery together with gross/net/cash/concentration/turnover/hedges/winner holdings/P&L.

Diagnostics include:

```text
DOWNSIDE_CAPTURE
LATE_DECLINE_AVOIDED
TROUGH_EXPOSURE
REBOUND_5D_CAPTURE
REBOUND_20D_CAPTURE
REBOUND_60D_CAPTURE
MISSED_REBOUND_PNL
REENTRY_DELAY_DAYS
REENTRY_PRICE_PENALTY
ORDINARY_BULL_UNDEREXPOSURE
RIGHT_TAIL_CLIPPED
CASH_DRAG
TURNOVER_DRAG
HEDGE_CARRY
INSURANCE_PAYOFF
```

Canonical question:

> Did risk control save meaningful downside, or mainly sell after the fish body was gone, miss the rebound fish tail and clip future winners?

For the same stock forecasts compare no timing overlay, actual timing, exit-only, re-entry-only, hedge-only and leverage-only counterfactuals.

Winner-clipping audit remains diagnostic and uses the existing Right-Tail firewall.

---

# 12. Capital-policy utility tests

Do not promote because a regime classifier has high accuracy. Require sustainable fund-level utility net of:

```text
turnover
cash drag
hedge carry
option premium
execution
leverage financing
capacity
survival/tail constraints
```

A state-dependent policy must add marginal net portfolio utility relative to the incumbent.

---

# 13. Failure tests

At minimum:

```text
desired leverage > CRO ceiling → cap/block
gross > account limit → block
capacity/liquidity insufficient → reduce/block
margin/funding failure → block
uncertain market state → no forced leverage
missing hedge pricing → no fabricated hedge
short locate absent → short leg blocked
put quote unavailable → unavailable, not zero-cost
CRO freeze active → no increase in risk
strategy attempts to unfreeze → hard fail
rapid regime oscillation / whipsaw
exit after most drawdown already occurred
re-entry after most rebound already occurred
crisis hedge activates at trough or remains after recovery
winner clipped despite continuation evidence
fast V-rebound / slow-bear scenarios
```

All implementation-specific thresholds are frozen before evaluation.

---

# 14. Activation gate

This policy is intentionally **later than Market Transition discovery**.

Do not implement `RESONANCE_LEVERAGE_POLICY_v1` merely because market-regime research starts. Implementation becomes eligible only when:

```text
upstream single-name Alpha has legitimate evidence
+ market/timing component has legitimate evidence/calibration
+ capital-policy counterfactual is the nearest capital-value question
+ PAPER/operations can measure the intended economics
+ CRO/Capital Constitution authorizes the research envelope
```

Options, leverage and shorts remain optional challengers/extensions. No generic options engine or macro platform is required.

---

# 15. Current authority statement

```text
ACTIVE_PRODUCT_STATE = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
CLOCK_1_STARTED = TRUE
RESONANCE_LEVERAGE_POLICY_v1 = SPECIFIED / EVIDENCE_GATED / NOT IMPLEMENTED
IMPLEMENTATION_AUTHORITY = BLOCKED_PENDING_UPSTREAM_EVIDENCE_AND_CRO_PRIORITY
LEVERAGE_AUTHORITY = DISABLED
SHORT_AUTHORITY = DISABLED
OPTIONS_CAPITAL_AUTHORITY = DISABLED
financial_alpha_evidence = 0
LIVE = CLOSED
```

Clock #1 does not release this policy by itself. This document creates no current target, hedge, leverage, short, option, broker or live-capital authority; implementation remains blocked until upstream Alpha/timing evidence exists and PM/CRO identify this as the nearest capital-value question.
