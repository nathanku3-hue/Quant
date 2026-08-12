# SECTOR_ROTATION_ALPHA_v1 — ETF-First Orthogonal Alpha Family Preregistration

**Date:** 2026-08-10  
**Status:** `BUILD_SLICE_CLOSED / PARKED_CAPTURE_HOLD / ETF_FIRST / M0_FROZEN / ACQUISITION_REQUEST_FROZEN / NO_RESULT / NO_CAPITAL_AUTHORITY`  
**Family ID:** `SECTOR_ROTATION_ALPHA_v1`  
**Risk-set spec:** `SRA_US_SELECT_SECTOR_ETF_11_V1`  
**Primary label:** `SRA_RIGHT_TAIL_20D_TOP2_V1`  
**Secondary label:** `SRA_RIGHT_TAIL_40D_TOP2_V1`  
**Implementation:** `SRA_M0_RELSTR_20_60_DVP_5_20_EQUAL_RANK_v1`  
**Search family:** `SRA_M0_SEARCH_v1`  
**Material trial budget:** `1`  
**Financial Alpha evidence:** `0`  
**Capital authority:** `NONE`  
**Relationship to stock-winner path:** orthogonal; MUST NOT delay Clock #1 or VSB/PREBREAKOUT custody.

---

## 0. Purpose

Test one deliberately small ETF-first economic mechanism:

```text
persistent sector-relative ETF strength
+
recent ETF-level dollar-volume participation
→
leadership persistence over the next multi-week horizon
```

The family asks whether ETF-level sector information improves allocation of the next unit of research risk without importing stock-selection breadth or the legacy stock-sector map.

This is not:

```text
old stock sector map repaired under a new name
stock constituent breadth
ETF flow-vendor research
fundamental sector aggregation
optimizer / ML / boosting search
Child redesign
capital routing authority
```

The family is intentionally self-contained so it can advance on independent engineering/provider capacity while the stock path retains priority.

---

## 1. Authority boundary

```text
family_id                    = SECTOR_ROTATION_ALPHA_v1
risk_set_spec_id             = SRA_US_SELECT_SECTOR_ETF_11_V1
primary_label_spec_id        = SRA_RIGHT_TAIL_20D_TOP2_V1
secondary_label_spec_id      = SRA_RIGHT_TAIL_40D_TOP2_V1
search_family_id             = SRA_M0_SEARCH_v1
implementation_id            = SRA_M0_RELSTR_20_60_DVP_5_20_EQUAL_RANK_v1
prediction_ledger_scope      = SRA_V1_PREDICTION_LEDGER
trial_ledger_scope           = SRA_V1_TRIAL_LEDGER
trial_budget_max             = 1
financial_alpha_evidence     = 0
capital_policy_authority     = NONE
broker_orders                = FORBIDDEN
Parent/Child mutation        = FORBIDDEN
A2 re-query                  = FORBIDDEN
```

A current W8 artifact cannot satisfy VSB, PREBREAKOUT, CRV1, AOV, or broker authority. No shared mutable outcome authority is permitted.

---

## 2. ETF-first risk set

### 2.1 Frozen economic universe

`SRA_US_SELECT_SECTOR_ETF_11_V1` contains exactly one source-authorized U.S.-listed primary ETF observation for each frozen sector key:

```text
COMMUNICATION_SERVICES
CONSUMER_DISCRETIONARY
CONSUMER_STAPLES
ENERGY
FINANCIALS
HEALTH_CARE
INDUSTRIALS
INFORMATION_TECHNOLOGY
MATERIALS
REAL_ESTATE
UTILITIES
```

The economic benchmark-family identity is:

```text
US_SELECT_SECTOR_ETF_11_V1
```

Display tickers are not identity authority. Every admitted date binds exact:

```text
CIQSEC:<Capital IQ Security ID>
SP_TRADING_ITEM_ID
primary-listing ID
sector_key
benchmark-family membership receipt
```

The source receipt must prove the date-local benchmark membership/identity mapping. The implementation contains no hard-coded ETF ticker literals and therefore cannot silently switch identity through ticker reuse.

### 2.2 Hard prohibitions

Every source authority must assert and the producer must verify:

```text
stock_sector_map_used                    = false
stock_breadth_used                       = false
underlying_stock_membership_used         = false
current_survivor_back_projection_used    = false
alternate_listing_backfill_used          = false
legacy_identity_fallback_used            = false
etf_flow_vendor_used                     = false
corporate_action_total_return_authority_bound = true
```

Any true forbidden flag blocks admission. There is no stock-constituent fallback, ticker/entity/PERMNO identity fallback, current-survivor reconstruction, or alternate-listing repair.

---

## 3. PIT / availability / corporate-action law

For prospective input at decision close `t`:

```text
source rows are date-local
membership_effective_at <= observed_at <= available_at <= knowledge_cutoff
exact CIQ security + exact trading item must reconcile
market history contains no session after t
>= 60 observed sessions exist for every admitted ETF
close > 0
volume > 0
total_return_1d > -1
source receipt hash is exact
```

The no-network producer accepts already-landed, hash-receipted CIQ source objects only. It does not acquire data itself.

### 3.1 Frozen acquisition request under capture hold

The exact parked source-acquisition request is:

```text
docs/context/e2e_evidence/sector_rotation_alpha_v1_acquisition_request_20260810.json
request_id     = SRA_ETF_11_CIQ_ACQUISITION_V1
request_sha256 = 7d4a46c0fa2e0292ab42d0f88f90dc800bb25c5edebcd00bdd1a209a73915c0c
capture_state  = PARKED_CAPTURE_HOLD
```

For each of the exact 11 frozen sector keys, the later acquisition must first resolve and source-bind:

```text
SP_CIQ_ID          → canonical CIQSEC identity
SP_TRADING_ITEM_ID → exact listing/trading-item identity
sector-key membership receipt
```

Those provider values are not present in retained local custody today and are therefore **not guessed, ticker-derived, or queried under the capture hold**. Unresolved identity is `BLOCK`. Only after all 11 exact CIQSEC + Trading Item pairs are returned by the source-authorized benchmark-membership receipt may the market-history leg request:

```text
SP_TOTAL_RETURN
SP_PRICE_CLOSE
SP_VOLUME
>= 60 observed sessions per ETF
through the decision session only
```

`SP_TOTAL_RETURN` is the required corporate-action/total-return authority. Price-only history cannot substitute. The request remains non-executable until a new explicit reopen occurs with truly independent provider capacity that cannot delay the stock path.

For the current daily implementation, source admission uses a conservative completed-primary-close gate. In the present 2026 calendar scope, a prediction-date receipt may not be admitted before `16:00 America/New_York`. This is a custody gate, not a claim that every future exchange session closes at 16:00; calendar authority must be extended before this code is used outside its declared scope.

Corporate actions are represented through the admitted total-return authority. Raw price-only continuation cannot substitute for total-return outcome truth.

---

## 4. Allowed information surface

W8 M0 uses only:

```text
market.close
market.total_return_1d
market.volume
```

Explicitly absent:

```text
stock breadth
stock sector membership
stock winners / stock labels
fundamentals
earnings revisions
news / text
options
short interest
ETF flows / creation-redemption vendor data
VSB features
AOV Rule100/Parent/Child state
```

A later feature family may be opened only under a new charged implementation/version before result inspection.

---

## 5. Frozen M0 transform

For each ETF `i` on completed decision session `t`, use observed sessions only.

### 5.1 ETF total-return persistence

```text
R20(i,t) = product(1 + total_return_1d) - 1 over the last 20 observed sessions through t
R60(i,t) = product(1 + total_return_1d) - 1 over the last 60 observed sessions through t

M20(t) = cross-sectional median_i R20(i,t)
M60(t) = cross-sectional median_i R60(i,t)

RS20(i,t) = R20(i,t) - M20(t)
RS60(i,t) = R60(i,t) - M60(t)
```

This makes leadership date-local and cross-sectional without any stock constituent map.

### 5.2 ETF-level participation

```text
DV(i,s) = close(i,s) * volume(i,s)

DVP(i,t) = ln(
    mean(DV over last 5 observed sessions through t)
    /
    mean(DV over last 20 observed sessions through t)
)
```

This is ETF trading participation only. It is not interpreted as creation/redemption flow, passive-flow truth, or constituent breadth.

### 5.3 Trigger

```text
M0_TRIGGER(i,t) =
    RS20(i,t) > 0
and RS60(i,t) > 0
and DVP(i,t) > 0
```

All thresholds are mechanism signs fixed at zero, not tuned cutoffs.

### 5.4 Cross-sectional score

Across the exact 11-ETF date-local risk set, calculate average-tie percentile ranks:

```text
r20  = pct_rank(RS20)
r60  = pct_rank(RS60)
rDVP = pct_rank(DVP)

I_score       = (r20 + r60) / 2
I_support     = RS20 > 0 and RS60 > 0

I_plus_X_raw  = (r20 + r60 + rDVP) / 3
forecast_score = I_plus_X_raw if M0_TRIGGER else 0
support        = forecast_score > 0
```

The prediction artifact seals both `I` and `I+X` fields. The comparator therefore exists before labels and cannot be invented after a disappointing result.

---

## 6. Frozen horizons and labels

Prediction frequency is daily when a legitimate completed-close source packet exists.

```text
knowledge_cutoff = completed session t data
prediction_made_at > knowledge_cutoff
first outcome interval begins after prediction cut
primary horizon = next 20 observed sessions
secondary horizon = next 40 observed sessions
```

For each matured prediction date:

```text
F20(i,t) = product(1 + r(i,s)) - 1 over next 20 observed sessions
F40(i,t) = product(1 + r(i,s)) - 1 over next 40 observed sessions
```

The primary winner set is the top `2` ETFs by `F20`; the secondary winner set is the top `2` by `F40`. Deterministic ties are resolved by `forward_total_return DESC, security_id ASC`.

Incomplete horizons are `INCOMPLETE_HORIZON`, never imputed. Corporate-action/identity ambiguity fails closed rather than survivor-filtering the denominator.

---

## 7. Search / Trial Ledger

M0 consumes the entire initial material search budget:

```text
search_family_id          = SRA_M0_SEARCH_v1
implementation_id         = SRA_M0_RELSTR_20_60_DVP_5_20_EQUAL_RANK_v1
trial_budget_max          = 1
material_trials_consumed  = 1
outcome_accessed          = false at preregistration
```

The append-only Trial/Search ledger accepts exactly one M0 material-trial receipt. A second material trial under the same search identity fails closed.

The trial receipt hash-binds:

```text
family/search/implementation identity
code-manifest SHA256
falsifiers
budget consumption
zero-outcome-access state
zero financial/capital authority
```

The following are material changes and require a new charged implementation/version before evaluation:

```text
changing 20/60 return windows
changing 5/20 participation windows
changing any sign threshold
changing equal feature weights
changing top-2 label law
changing 20d/40d horizons
changing the ETF benchmark family or sector set
adding stock breadth/constituents
adding ETF-flow vendor fields
adding fundamentals/news/options/short interest
adding fitted coefficients, ML, boosting or optimizer output
changing I vs I+X comparator after result inspection
changing acceptance/falsifier rules after result inspection
```

---

## 8. Prediction Ledger

Every valid prediction batch is sealed strictly after its knowledge cutoff and before outcome access.

The append-only prediction tape is independent from every other family and binds:

```text
family / implementation / search identity
trial_receipt_sha256
decision context/date
knowledge cutoff
prediction time
risk-set identity
input / feature / model hashes
per-ETF CIQSEC + sector key
I score/support
I+X forecast score/support
reason codes
20d/40d label identities
zero-authority state
previous chain hash
current chain hash
```

Custody rules:

```text
exclusive writer lock
one batch per decision date
no duplicate prediction ID
fsync before success
reload verification after append
tamper detection
partial-final-line rejection
UNMATURED_NOT_EVALUATED until a separately authorized evaluator opens labels
```

No current W8 code reads an outcome source.

---

## 9. Falsifiers and acceptance law

M0 is falsifiable. Pre-frozen family falsifiers are:

```text
PRIMARY_WINNER_RECALL_LIFT_NOT_ABOVE_ONE
PRIMARY_80PCT_BLOCK_BOOTSTRAP_LB_NOT_ABOVE_ONE
NO_INCREMENTAL_VALUE_VS_RELATIVE_STRENGTH_ONLY_BASELINE
PIT_IDENTITY_OR_AVAILABILITY_VIOLATION
MATERIAL_TRIAL_BUDGET_EXCEEDED
```

The first confirmatory/untouched acceptance read may occur only after a separately frozen outcome/lockbox protocol exists and at least:

```text
30 matured primary 20d decision dates
```

Primary mechanism statistics are right-tail/incremental rather than portfolio-CAGR first:

```text
Precision / Recall / Lift for top-2 20d sector winners
PR-AUC / Average Precision
false winners
missed winners
catastrophic false winners
effective episode count / temporal dependence diagnostics
right-tail wealth capture
I vs I+X incremental winner capture / net utility
```

Bootstrap law is frozen now:

```text
unit = decision date
moving block length = 20 decision dates
replicates = 10000
seed = 20260810
confidence = 0.80 percentile interval
```

The screening gate requires:

```text
primary winner-recall lift > 1.0
80% moving-block-bootstrap lower bound of primary lift > 1.0
I+X not falsified by the preregistered incremental comparator
PIT/custody violations = 0
search-budget violations = 0
```

CAGR/Sharpe/MDD remain secondary. A historical or prospective mechanism-screen pass is not capital authority.

---

## 10. Full W8 evidence ladder

W8 follows its own ETF ladder without consuming stock lockbox or mutable stock outcomes:

```text
ETF PIT/source authority
→ ETF-only discovery census when legitimate historical PIT bytes exist
→ small charged development / walk-forward if authorized
→ freeze
→ untouched historical lockbox where legitimate
→ prospective prediction tape
→ matured deterministic evaluator
→ shadow economics / right-tail wealth
→ independent replication
→ PAPER capturability only after separate promotion authority
→ bounded capital only after CRO/owner gate
```

The currently implemented slice stops before outcome evaluation. It establishes preregistration, source/PIT admission, frozen M0, one-trial Search Ledger, future-directed sealing, and independent Prediction Ledger custody.

---

## 11. Non-blocking law

W8 has no right to slow the stock path.

Therefore the current implementation:

- creates only `research/sector_rotation_alpha_v1/`, its dedicated tests, and this family specification/evidence receipt;
- performs no provider/network acquisition;
- does not modify VSB/PREBREAKOUT prediction tapes;
- does not consume stock lockbox outcomes;
- does not use the old rotation backtest as authority;
- does not repair or import the old sector map;
- does not construct stock breadth;
- does not create a generic provider, feature-store, registry, optimizer, or execution platform.

If shared provider/custody capacity conflicts with VSB or Clock #1, W8 waits rather than taking the resource.

---

## 12. Current execution state

```text
family identity                         FROZEN
ETF-first risk-set contract             FROZEN
exact 11 sector keys                    FROZEN
CIQSEC + trading-item identity law      IMPLEMENTED
availability / no-survivor law          IMPLEMENTED
corporate-action total-return flag      IMPLEMENTED
old sector-map dependency               FORBIDDEN / TESTED
stock breadth dependency                FORBIDDEN / TESTED
ETF-flow vendor dependency              FORBIDDEN / TESTED
M0 20/60 + 5/20 transform               IMPLEMENTED
I vs I+X comparator                     IMPLEMENTED / SEALED BEFORE LABELS
search budget                           FROZEN = 1
Trial/Search Ledger                     IMPLEMENTED / APPEND-ONLY
prediction seal                         IMPLEMENTED / STRICTLY POST-CUT
Prediction Ledger                       IMPLEMENTED / HASH-CHAINED / EXCLUSIVE WRITER
acquisition request                     FROZEN = SRA_ETF_11_CIQ_ACQUISITION_V1
acquisition request SHA256              7d4a46c0fa2e0292ab42d0f88f90dc800bb25c5edebcd00bdd1a209a73915c0c
capture state                            PARKED_CAPTURE_HOLD
provider acquisition                    NOT PERFORMED / FORBIDDEN THIS SLICE
historical outcome evaluation           NOT PERFORMED
untouched result                        NONE
prospective real CIQ prediction         NOT YET SEALED
financial_alpha_evidence                0
capital authority                       NONE
worker state                             RELEASED / PARKED
```

The W8 build slice is closed. **Do not tune or expand M0 and do not acquire W8 data under the current capture hold.** Reopen only when truly independent provider capacity is available and can operate without delaying Clock #1 / VSB / stock-winner custody. At reopen, execute the already-frozen acquisition request exactly; unresolved CIQSEC/Trading Item identity blocks rather than falling back to ticker, entity, stock-sector map, stock breadth, ETF-flow vendor, ML, or optimizer work.
