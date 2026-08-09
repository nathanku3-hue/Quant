# MARKET_TRANSITION_ALPHA_v1 — Post-Clock Discovery / Forecast Specification

**Date:** 2026-08-08
**Status:** `PREREGISTERED_DISCOVERY_INCUBATOR / CLOCK_1_DISCOVERY_RELEASED / NOT_IMPLEMENTED`
**Authority:** supporting post-Clock discovery/preregistration lane; no capital authority. It remains discovery-only until explicitly admitted into one of the active Alpha-family WIP slots under the 2026-08-09 strategic lock.
**Current gate effect:** **DISCOVERY INCUBATOR / MAY COMPETE FOR A FUTURE FAMILY WIP SLOT / NO AUTOMATIC CONFIRMATORY AUTHORITY** — Clock #1 is running; the strategic lock allows multiple independent family clocks but does not automatically promote Market Transition
**Relationship to CYCLE_RESONANCE_v1:** separate Alpha Family; no mutation of CRV1

---

# 0. Purpose

Test whether PIT market, breadth, volatility, credit, fundamental-revision and macro state can forecast broad market transitions early enough to change a capital decision rather than merely describe a regime after the move.

This family is distinct from:

```text
CYCLE_RESONANCE_v1          single-name / cycle-resonance Alpha Family
ENTRY_TIMING_COMPONENT_v1   separate timing Alpha Component
RESONANCE_LEVERAGE_POLICY_v1 Capital Policy
```

A market forecast does not directly choose leverage, shorts, hedges or broker orders. Market-state classification is not Alpha by itself; confirmatory/prospective authority requires immutable future-directed predictions frozen before outcome access. Multiple evidence-qualified families may coexist, but only one current portfolio/capital-policy authority commits financial risk.

---

# 1. Scope / authority boundary

```text
family_id = MARKET_TRANSITION_ALPHA_v1
pre_clock_implementation = FALSE
post_clock_discovery_incubator = ALLOWED
parallel_confirmatory_family_build_beside_CRV1 = REQUIRES_EXPLICIT_FAMILY_WIP_ADMISSION
financial_alpha_evidence = 0
```

Any market/timing overlay applied to CRV1 becomes a new Component / Implementation / Trial with new identity and search-budget charge. No macro threshold, timing rule, leverage multiplier, bearish rule or option input is smuggled into CRV1.

No generic market-regime, macro, options or optimizer platform is authorized.

---

# 2. Forecast output

Primary output is a forecast object, not an action:

```text
P(BULL_TRANSITION)
P(BEAR_TRANSITION)
P(CRISIS_TRANSITION)
expected_market_return
expected_market_volatility
expected_tail_loss
epistemic_uncertainty
forecast_horizon
```

Optional later states require a versioned contract:

```text
P(V_SHAPED_RECOVERY)
P(SLOW_BEAR)
P(SYSTEMIC_STRESS)
```

Every prediction binds:

```text
decision_cut
information_manifest_hash
model_hash
horizon
calibration_version
prediction_id
```

No output is automatically a target weight or trade instruction.

---

# 3. `ENTRY_TIMING_COMPONENT_v1`

Timing is a separate Alpha Component. Preserve distinct attribution:

```text
DISCOVERY ALPHA
ENTRY TIMING ALPHA
CONTINUATION / HOLD ALPHA
EXIT / FALSIFIER ALPHA
```

Required timing states:

```text
PRE_INFLECTION
LEFT_INFLECTION
RIGHT_CONFIRMATION
MATURE_TREND
EXHAUSTION_WATCH
EXIT_RISK
UNKNOWN
```

`LEFT_INFLECTION` means deterioration appears to have stopped/reversed before full confirmation. `RIGHT_CONFIRMATION` means sufficient subsequent PIT evidence confirms the transition. `UNKNOWN` is valid; no forced weekly action.

A stock-selection model receives no timing/hold/exit credit without separate evidence.

---

# 4. Market evidence clocks

The discovery surface may study the following only with explicit PIT/availability semantics.

## 4.1 Price / volume

```text
multi-horizon trend / slope
breakout / breakdown
failed breakout / failed breakdown
range compression / expansion
relative strength
volume confirmation / exhaustion / capitulation
ADV / liquidity
gap behavior
breadth
```

## 4.2 Volatility / correlation

```text
realized-vol level / delta / inflection
cross-sectional realized-vol dispersion
index vs constituent vol
correlation state
vol-of-vol where legitimately sourced
```

## 4.3 Breadth / participation

```text
advance/decline breadth
new highs/new lows
% above intermediate/long moving averages
equal-weight vs cap-weight
sector participation
leadership concentration
breadth thrust / collapse
```

## 4.4 Credit / funding

```text
credit-spread level / acceleration
HY/IG relative stress
funding stress
financial conditions
liquidity proxies
```

Every observation binds `observed_at / available_at`.

## 4.5 Earnings / fundamental breadth

```text
positive / negative revision percentage
revision acceleration
margin revision breadth
revenue revision breadth
earnings diffusion across sectors
```

## 4.6 Macro

```text
growth
employment
inflation
rates
yield curve
liquidity / financial conditions
credit impulse where legitimately PIT
```

Revisable series use vintage/release-time semantics. Future revised macro data are forbidden.

---

# 5. `MarketStatePacketV1`

Use a narrow immutable derived packet rather than a generic provider platform:

```text
market_state_packet_id
decision_cut
source_manifest_hash
price_volume_state
breadth_state
realized_vol_state
dispersion_state
correlation_state
credit_state
macro_state
earnings_revision_state
optional_options_state
coverage
missingness
max_available_at
semantic_hash
```

Every underlying source remains separately attributable. Missing optional options data does not invalidate V1; missing required state fails closed. No caller-supplied `available_at`; no forward-filled unreleased vintage; no future revision.

---

# 6. Left-side vs right-side timing

## 6.1 Left-side inflection

Do not define as “price down a lot.” Candidate evidence may include:

```text
deterioration decelerating
failed breakdown
capitulation / absorption
breadth deterioration stops
credit deterioration stops
revisions stop worsening
volatility acceleration peaks
stock-specific causal clock turns
```

Test earlier entry against false-bottom probability.

## 6.2 Right-side confirmation

Candidate evidence may include:

```text
trend confirmation
breakout
breadth expansion
volume confirmation
estimate confirmation
stock / industry clock confirmation
```

Test lower false-positive rate against edge consumed by waiting.

## 6.3 Canonical comparison

For the same Core Alpha opportunity:

```text
no timing overlay
vs left-inflection entry
vs right-confirmation entry
```

Hold PIT inputs, outcome, sizing framework, execution, costs and universe constant.

---

# 7. Transition / hazard methodology

Approved research toolkit includes discrete-time hazard models, change-point models, state-space models, HMM/state models as challengers and ordered temporal motifs.

Canonical questions:

```text
P(positive transition during next h | state_t)
P(bear transition during next h | state_t)
P(crisis transition during next h | state_t)
P(recovery transition during next h | state_t)
```

Every materially different state specification, variable transformation, threshold, persistence law or model class consumes search budget.

---

# 8. Hysteresis

Regime/timing logic must not mechanically oscillate around one threshold.

- entry and exit thresholds are distinct where the implementation uses thresholds;
- crisis activation and recovery are distinct;
- changing state may require stronger evidence than remaining in state;
- minimum-persistence rules belong in the frozen implementation manifest, not roadmap prose;
- every transition records prior state, reason, uncertainty and changed gates.

---

# 9. `CRISIS_TRANSITION_ATLAS` — discovery only

Historical crisis review is outcome-visible `DISCOVERY_ONLY`, analogous to Right-Tail forensics. 2008/2020 or other famous episodes cannot become tuning targets.

Required episode classes where history supports them:

```text
systemic financial crisis
fast crash
slow grinding bear
high-volatility correction
false bear signal
high-vol bull market
V-shaped recovery
sideways / high-dispersion market
credit event without major equity bear
equity selloff without systemic credit event
```

For each episode reconstruct, where legitimate:

```text
T-12m
T-6m
T-3m
T-1m
T0
trough
early recovery
```

Record what was knowable then, which clocks turned first, which never turned, and which warnings were false alarms.

No historical crisis outcome alone constitutes confirmatory/OOS/prospective authority.

---

# 10. False-crisis controls

False alarms are mandatory controls. Collect periods with elevated vol, weak breadth, alarming macro/credit or high dispersion where severe bear/crisis outcomes did not follow.

Measure:

```text
P(crisis | proposed crisis state)
crisis recall
false-crisis rate
days unnecessarily defensive
missed bull return
hedge carry
re-entry delay
```

A system that “predicts crisis” on every correction fails economically even if it contains famous crises.

---

# 11. Leave-one-crisis-out / effective episode count

Where sample breadth supports it:

```text
discovery on subset
→ freeze signal family
→ one major episode untouched
→ rotate untouched episode
```

Do not overstate independence when episodes share macro structures. Report raw observations and effective independent episode count grouped by macro episode, industry cycle and shared shock. Prospective evidence remains superior to retrospective crisis count.

---

# 12. Dispersion contract

High dispersion alone is neither bullish nor bearish.

Interpret jointly with:

```text
dispersion
correlation
breadth
index trend
constituent trend
credit
liquidity
volatility
earnings-revision breadth
```

Possible interpretation classes:

```text
CROSS_SECTIONAL_OPPORTUNITY
LEADERSHIP_CONCENTRATION
SYSTEMIC_STRESS
ROTATION
UNKNOWN
```

No one-dimensional `dispersion > threshold → L/S` rule.

A separate `DISPERSION_ALPHA` diagnostic asks whether high-dispersion periods improve long-short forecast spread, winner/loser precision or gross-alpha opportunity conditional on correlation, market vol, liquidity and concentration.

---

# 13. Discovery / confirmation firewall

## Discovery

May inspect historical crises and outcomes, generate semantic mechanisms and control populations. Zero alpha authority.

## Frozen historical validation

Before untouched inspection freeze:

```text
inputs
horizons
transition/crisis definitions
state model
falsifiers
search budget
```

## Prospective

Future market states only. No crisis-history rescue and no outcome-informed threshold change under the same version.

---

# 14. Search accounting

Material degrees of freedom include:

```text
macro variable / transform / release lag
trend horizon
breadth definition
vol horizon
dispersion / correlation definition
credit spread
options field
state count
change-point law
threshold
minimum persistence
crisis / bear label
entry / exit horizon
```

All enter Trial/Search Ledger. Material target/horizon/mechanism changes create a new family/version where required by the Research Constitution.

---

# 15. Calibration / forecast quality

For probability forecasts, evaluate reliability, Brier score, log loss and calibration by regime/decade/volatility state/extreme probability.

Before a future capital policy maps forecast strength into sizing, require probability calibration and conviction monotonicity; extreme probabilities cannot be treated as high conviction merely because the model emits them.

---

# 16. Independent evidence requirement

Before this family can become Core Alpha require, as available/applicable:

```text
legitimate PIT historical validation
false-alarm analysis
effective independent episode count
untouched time/regime evidence
prospective evidence
monetizability
marginal portfolio utility
```

A model trained/tested on the same famous crisis narrative does not qualify.

---

# 17. Failure / adversarial tests

At minimum test fail-closed behavior for:

```text
future macro release
revised macro vintage substituted
future earnings revisions
future options/OI observation
available_at > decision_cut
missing required breadth / credit state
stale market state
invalid security identity
outcome field imported by confirmatory code
discovery artifact enters prospective dependency graph
crisis label changed after result
state threshold changed after result
operational freeze interpreted as market signal
dispersion alone triggers direction
not-long silently becomes short
```

A scientific implementation should also fail/hold if it detects famous crises but has excessive false alarms, relies on revised/future data, exits after most damage, systematically misses rebound, incurs excessive defensive carry, is poorly calibrated, works only in one crisis or has excessive search contamination.

---

# 18. V1 provider order

V1 should use the cheapest honest PIT surface first:

```text
price
volume
breadth
realized vol
dispersion / correlation from legitimate market data
credit
PIT macro vintages
earnings-revision breadth if legitimately available
```

Options/IV/skew/OI/implied correlation/dealer-gamma/positioning are V2 challengers only. Dealer gamma is derived/estimated; “whale intent” is inferred, never observed fact.

Do not build a generic provider/data platform. First consumer gets exact adapters; a second genuine consumer triggers abstraction discussion under Rule of Two.

---

# 19. Post-Clock sequencing — final strategic lock

`MARKET_TRANSITION_ALPHA_v1` remains a registered Discovery Incubator by default:

```text
Crisis Transition Atlas
+ false-crisis controls
+ PIT source-gap inventory
+ transition-label / mechanism candidates
+ preregistered falsifiers / search budget
```

The 2026-08-09 strategic lock allows multiple independently owned Alpha-family prediction clocks/evidence streams. Market Transition may enter confirmatory/prospective implementation only through an explicit local family-WIP admission that proves separate owner/writer custody, search budget, Prediction/Trial Ledger identity, artifact namespace, risk-set/label contract and no shared mutable outcome authority.

CRV1 sealing is **not** a constitutional prerequisite to that admission. Default active family WIP is `2`, initial ceiling `3`. Evidence qualification may occur in parallel; current portfolio/capital-policy authority remains singular.

---

# 20. Exit criteria for this design

This design is sufficiently frozen when:

- market forecast is distinct from capital policy;
- operational kill is distinct from market-risk de-risk;
- left/right timing is testable;
- crisis review is discovery-only;
- false-crisis controls are mandatory;
- `not bullish` cannot create short authority;
- dispersion alone cannot create direction;
- search degrees of freedom are registered;
- options are incremental challenger data;
- no current Alpha Family is silently mutated;
- the immutable Clock #1 chain remains unchanged.

---

# 21. Current authority statement

```text
ACTIVE_PRODUCT_STATE = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
CLOCK_1_STARTED = TRUE
MARKET_TRANSITION_ALPHA_v1 = PREREGISTERED_DISCOVERY_INCUBATOR / DISCOVERY_LANE_RELEASED / NOT IMPLEMENTED
ENTRY_TIMING_COMPONENT_v1 = SPECIFIED / DISCOVERY_ONLY / NOT IMPLEMENTED
CONFIRMATORY_ALPHA_FAMILY_WIP = DEFAULT_2 / INITIAL_CEILING_3
CURRENT_STATUS = DISCOVERY_ONLY_UNLESS_EXPLICIT_WIP_ADMISSION
financial_alpha_evidence = 0
LIVE = CLOSED
```

Clock #1 releases the Crisis Transition Atlas, false-crisis controls, PIT source-gap inventory and preregistration work for this family. Confirmatory/prospective implementation requires explicit family-WIP admission under the final strategic lock; it is not granted automatically by this spec and no market-transition discovery/evidence result carries capital authority by itself.
