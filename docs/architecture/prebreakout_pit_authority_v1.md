# PREBREAKOUT PIT Authority v1 — W3 Source / Identity / Availability / Corporate Actions

**Date:** 2026-08-10
**Owner lane:** W3
**Family:** `PREBREAKOUT_DISCOVERY_v1`
**Status:** `MECHANICS_CLOSED / DATA_GATE_OPEN / B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE`
**Evidence authority:** `financial_alpha_evidence=0`; statistical weight=`0`; capital authority=`NONE`

## 1. Scope

W3 owns only point-in-time source authority for the pre-breakout stock-winner path:

- date-local risk-set membership;
- exact Capital IQ Security + Trading Item listing identity;
- information availability at the decision cut;
- date-local primary-listing proof;
- complete corporate-action state for every candidate;
- deterministic eligible/excluded status;
- zero-weight B-1 engineering proof for named smoke cases such as MU/SNDK.

W3 does **not** own the breakout algorithm `B`, TTFLD, horizons, labels, Atlas outcomes, model/search choices, walk-forward, lockbox evaluation, VSB confirmation, sector rotation, replication outcomes, PAPER orders, or capital.

The W2 breakout contract is therefore an input to the B-1 proof. W3 may not invent `B` or derive a convenient prior session from hindsight. Current immutable W2 authority is `PREBREAKOUT_W2_CONTRACT_v1`, with `methodology_contract_sha256 = breakout_contract_sha256 = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`; canonical handoff=`docs/context/prebreakout_w2_binding_current.md`.

## 2. Frozen identities

```text
family_id                 = PREBREAKOUT_DISCOVERY_v1
risk_set_spec_id          = PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1
pit_authority_schema      = prebreakout_pit_authority_v1
source_authority_schema   = prebreakout_pit_source_authority_v1
candidate_row_schema      = prebreakout_pit_candidate_row_v1
corporate_action_schema   = prebreakout_pit_corporate_action_row_v1
smoke_proof_schema        = prebreakout_bminus1_eligibility_proof_v1
corporate_action_policy   = PREBREAKOUT_DATE_LOCAL_CORPORATE_ACTION_V1
```

Implementation: `research/prebreakout_pit_v1/authority.py`.

### 2.1 Future shared raw stock-data round with W9

W3 and W9 may coordinate one future raw CIQ stock capture when the same provider identity/market bytes and receipts are legitimately usable by both lanes. This is **raw-custody sharing only**; it is not authority sharing.

```text
shared raw CIQ identity / market bytes
        ├─> W3 independent compiler
        │     PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1
        │     + date-local availability
        │     + date-local primary proof
        │     + complete corporate-action authority
        │
        └─> W9 independent compiler
              CRV1_US_PRIMARY_COMMON_V1
              + non-growth law
              + exact CIQSEC + Trading Item
              + >=200 source-derived complete market observations
```

A W3 risk-set artifact, W3 admission receipt, corporate-action decision, or B-1 proof can never satisfy W9. A W9 risk-set artifact or admission receipt can never satisfy W3. Equal raw-object hashes merely prove shared custody of provider bytes; they do **not** prove equal family membership, eligibility, availability semantics, exclusion law, or risk-set authority. AOV-109 remains forbidden to both lanes as a substitute. Independent CRV1 fundamentals, expectations, and SEC claims remain W9 `MISSING_SOURCE` unless separately landed; W3 corporate-action custody does not fill those surfaces.

No provider capture is authorized by this coordination record today. W9 remains closed until that future shared raw-data round/admission.

## 3. Exact risky-asset / listing identity

A candidate row is admissible only with all of:

```text
security_id               matches CIQSEC:IQ<digits>
company_id                numeric provider entity provenance
trading_item_id           numeric Capital IQ Trading Item ID
spt_instrument_item_id    exactly SPT<trading_item_id>
membership_as_of_date     exactly the decision session date
```

Ticker is display metadata only in the smoke proof and is never an identity key. Company entity ID and PERMNO are never risky-asset identity. Alternate-listing repair is forbidden.

The source authority must explicitly assert all of these are false:

```text
current_survivor_back_projection_used
current_primary_back_projection_used
alternate_listing_backfill_used
ticker_fallback_used
company_entity_fallback_used
permno_fallback_used
```

Any true value fails the entire authority packet closed.

## 4. Date-local primary-listing law

Historical primary identity is not licensed to use today's Primary Issue / current-primary state. A row carries both a date-local state and its proof kind.

Allowed primary states:

```text
PRIMARY_DATE_LOCAL
NON_PRIMARY_DATE_LOCAL
AMBIGUOUS_DATE_LOCAL
```

Allowed proof kinds:

```text
DATE_LOCAL_PROVIDER_PRIMARY
UNIQUE_DATE_LOCAL_QUALIFYING_LISTING
DATE_LOCAL_PROVIDER_NON_PRIMARY
DATE_LOCAL_AMBIGUOUS_MULTIPLE
```

`PRIMARY_DATE_LOCAL` is admitted only with either a provider-declared date-local primary proof or exact uniqueness among the date-local qualifying listings. If date-local selection is ambiguous, the row is deterministically excluded as `AMBIGUOUS_PRIMARY_LISTING`; no current-primary lookup or alternate-listing substitution may resolve it.

This deliberately generalizes the legitimate Lane-2 lesson without generalizing the Lane-2 high-growth cohort itself: date-local uniqueness can prove one listing when it truly exists, but AOV-109/current-primary bytes never become the PREBREAKOUT historical risk set.

## 5. Availability / knowledge-cutoff law

For every candidate and corporate-action row:

```text
observed_at <= available_at <= as_of
membership_as_of_date == decision_session_date
```

For every source receipt:

```text
observed_range_start <= observed_range_end <= decision_session_date
PROSPECTIVE_SAME_DAY => retrieved_at <= as_of
```

`as_of` must be timezone-aware and is canonicalized to UTC. Future-available rows fail closed. A prospective raw receipt retrieved after the decision cut also fails closed even if a row claims an earlier `available_at`.

Two capture modes exist:

```text
HISTORICAL_PIT_DATE_LOCAL
  requires historical_as_of_mechanically_bound = true

PROSPECTIVE_SAME_DAY
  requires historical_as_of_mechanically_bound = false
```

Historical retrieval may occur later in wall-clock time, but the provider query/receipt must mechanically bind the historical as-of state and its observed range may not extend past the decision session. A later retrieval timestamp does not itself make later facts PIT-available.

The source packet must also assert:

```text
date_local_membership_query      = true
source_population_complete       = true
corporate_action_coverage_complete = true
```

An incomplete source population or incomplete corporate-action census is not converted into a smaller survivor-clean risk set; it blocks authority.

## 6. Corporate-action truth

Every candidate identity must have exactly one corporate-action state row with the same `CIQSEC` + Trading Item pair and a hash-bound source receipt. Allowed states:

```text
CLEAR
PENDING_TERMINAL
EFFECTIVE_TERMINAL
UNRESOLVED
```

Semantics:

- `CLEAR`: no terminal event known at the cut.
- `PENDING_TERMINAL`: terminal event is already known but effective strictly after the decision session; the listing may remain eligible if all listing criteria pass.
- `EFFECTIVE_TERMINAL`: event effective on/before the decision session; deterministic exclusion `CORPORATE_ACTION_TERMINAL_EFFECTIVE`.
- `UNRESOLVED`: source evidence does not establish safe lifecycle state; deterministic exclusion `CORPORATE_ACTION_UNRESOLVED`.

There is no post-terminal alternate-listing rescue and no disappearance/survivor filter. Corporate-action state changes eligibility; it does not create a second P&L path or Alpha evidence.

## 7. Deterministic W3 eligibility compiler

For each exact candidate/action pair, exclusions are applied in this fixed order:

```text
listing_country != US              -> NON_US_LISTING
security_class != COMMON_EQUITY    -> NON_COMMON_EQUITY
primary == AMBIGUOUS_DATE_LOCAL    -> AMBIGUOUS_PRIMARY_LISTING
primary != PRIMARY_DATE_LOCAL      -> NON_PRIMARY_LISTING
active_tradable != true            -> NOT_ACTIVE_TRADABLE
action == UNRESOLVED               -> CORPORATE_ACTION_UNRESOLVED
action == EFFECTIVE_TERMINAL       -> CORPORATE_ACTION_TERMINAL_EFFECTIVE
otherwise                          -> ELIGIBLE
```

After compilation, eligible `security_id`, `trading_item_id`, and `company_id` must each be unique. A packet with multiple eligible listings for one company is contradictory authority and fails closed rather than choosing one.

The packet is content-addressed and revalidated on reopen. It always carries:

```text
outcome_access_performed = false
statistical_evidence_weight = 0
financial_alpha_evidence = 0
capital_authority = NONE
```

## 8. B-1 smoke-proof contract

`build_b_minus_one_eligibility_proof(...)` consumes, but does not define:

```text
breakout_contract_sha256   # frozen W2 contract hash
breakout_session           # W2 algorithmic B
b_minus_1_session          # exact prior trading session supplied by W2
expected_security_id       # exact CIQSEC identity
expected_trading_item_id   # exact listing identity
W3 authority for b_minus_1_session
```

W3 verifies `b_minus_1_session < breakout_session` and requires the authority packet's decision session to equal the supplied B-1 session. It does not infer a calendar or rescue a wrong-date packet.

Outcomes:

```text
exact eligible identity at B-1
  -> PIT_ELIGIBLE_B_MINUS_1

exact identity present but excluded
  -> DETERMINISTIC_EXCLUSION + frozen exclusion reason

exact identity absent from a source-complete B-1 packet
  -> DETERMINISTIC_EXCLUSION / NOT_IN_DATE_LOCAL_SOURCE_POPULATION

historical pre-W2 receipt only
  -> DETERMINISTIC_UNAVAILABLE / BREAKOUT_CONTRACT_UNBOUND
  -> historical custody only; never current authority

current frozen-W2 state with missing W3 B-1 source packet
  -> DETERMINISTIC_UNAVAILABLE / B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE
  -> blocker; never a pass or accepted deterministic exclusion

exact identity not yet bound
  -> DETERMINISTIC_UNAVAILABLE / IDENTITY_UNBOUND
```

`display_symbol` is retained only for audit readability; `display_symbol_used_for_logic=false` is sealed in every proof.

Every smoke proof has:

```text
statistical_weight = 0
promotion_denominator_weight = 0
outcome_access_performed = false
financial_alpha_evidence = 0
capital_authority = NONE
```

Thus MU/SNDK can prove engineering honesty without becoming two-name hindsight acceptance criteria.

## 9. MU / SNDK current proof state

Current W2 state is **bound**, not unbound:

```text
W2 authority version            = PREBREAKOUT_W2_CONTRACT_v1
methodology_contract_sha256     = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
breakout_contract_sha256        = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
B law                           = strict close > prior 20 observed-session high
accepted-episode cooldown       = 20 full observed sessions
B-1 law                         = immediately prior observed session for the exact listing
TTFLD admissible window         = B-20 ... B-1
```

The retained receipt `docs/context/e2e_evidence/prebreakout_pit_w3_mu_sndk_20260810.json` predates this closure and correctly records `BREAKOUT_CONTRACT_UNBOUND` **as historical state at the time that receipt was created**. It is classified `HISTORICAL_PRE_W2_CUSTODY_ONLY`, carries no current authority, and does not satisfy the frozen W2 smoke obligation.

The later fast-path acquisition round has now landed real provider custody under the frozen acquisition contract. Combined market/listing custody spans 346 provider sessions from 2025-03-24 through 2026-08-07, 1,894,207 date-local rows, 5,919 companies and 6,018 exact listings. Filtered Key Developments lifecycle custody covers the same 5,919-company union in 12/12 parts with 176,353 normalized lifecycle rows. AOV-109/current-primary custody remains forbidden.

MU and SNDK are now resolved from provider bytes, not from symbol inference:

```text
MU   = CIQSEC:IQ289030 / Trading Item 2630498 / SPT2630498
SNDK = CIQSEC:IQ1860586153 / Trading Item 1929119896 / SPT1929119896
```

The frozen W2 law produces 11 accepted MU breakout episodes and 12 accepted SNDK breakout episodes across the captured exact-listing histories; all episodes are retained with zero statistical/promotion weight. However the captured raw bytes have not yet been compiled into date-local W3 authority packets with exact corporate-action state, so the current smoke gate remains:

```text
MU   -> B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE
SNDK -> B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE
```

This is an upstream compile blocker, never a pass. Current gate receipt=`docs/context/e2e_evidence/prebreakout_pit_w3_current_gate_20260810.json`; real raw-capture evidence=`docs/context/e2e_evidence/prebreakout_w3_real_data_capture_20260810.json`.

Acceptance sequence is now fixed at the remaining compile step: hash-bind the landed corpus, compile date-local primary and corporate-action state, build source-complete W3 authority for each required B-1 date, and then resolve each smoke episode to `PIT_ELIGIBLE_B_MINUS_1`, a canonical `DETERMINISTIC_EXCLUSION`, or a still-blocking `DETERMINISTIC_UNAVAILABLE`. If eligible, downstream PREBREAKOUT must flag inside `B-20..B-1`.

## 10. Frozen future acquisition manifest / W9 raw-byte coordination

Machine-readable acquisition authority: `docs/architecture/prebreakout_pit_acquisition_manifest_v1.json`, SHA-256 `f3cac6961707fc653c00016ff715fb7250236ad443854051a387ab330473dc3f`.

The manifest freezes future acquisition for the full date-local U.S. primary-common population, exact CIQSEC + Trading Item identity, date-local primary proof, availability timestamps, complete corporate-action state, historical as-of binding, and exact primary-listing market history sufficient for W2 `B`.

W9 coordination is raw-byte-only. When W3 and CRV1 require the same provider, same date/as-of, same exact listing rows, and same identity/market fields/range, byte-identical raw identity/market objects may be captured once. PREBREAKOUT and CRV1 still produce separate family/risk-set receipts and apply separate admission semantics. W3 does not inherit W9's `>=200` history as a membership filter; W9 does not inherit W3 corporate-action admission. A later W9 current identity snapshot can never satisfy an earlier PREBREAKOUT B-1 date.

The acquisition manifest was the pre-capture frozen contract and did not itself authorize provider access. A later explicit user acquisition action executed the capture under that frozen law. The post-capture evidence is `docs/context/e2e_evidence/prebreakout_w3_real_data_capture_20260810.json`; do not mutate the preregistered manifest to describe results.

## 11. Acceptance / no-go boundary

W3 mechanical contract acceptance requires:

- exact CIQSEC + Trading Item identity tests;
- date-local primary proof tests;
- no survivor/current-primary/ticker/entity/PERMNO/alternate-listing fallback tests;
- future-availability rejection;
- exact corporate-action coverage and effective/unresolved exclusions;
- packet tamper/reopen rejection;
- B-1 exact-date and exact-identity proof tests;
- exact frozen-W2 contract-hash enforcement;
- historical-only classification of the pre-W2 `BREAKOUT_CONTRACT_UNBOUND` receipt;
- current `B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE` blocker semantics;
- frozen future acquisition manifest with W9 raw-byte-only coordination.

W3 does **not** authorize W4 Atlas outcome access. No true/false/missed-winner census, label opening, model evaluation, search, prospective prediction, broker action, or capital action follows from this contract alone.
