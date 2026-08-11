# OK-SBI-0 / AO-K0B-D — Sparse Basis Identification v1.2

**Slice:** `OK-SBI-0`  
**Alias:** `AO-K0B-D — DEVELOPMENT BASIS DIAGNOSTIC`  
**Date:** 2026-08-11  
**Spec:** `v1.2`  
**State:** `S0_DESIGN_LOCKED_RELEASE_BLOCKED`  
**Design:** `PASS / LOCKED`  
**Science order:** `LOCKED`  
**Outcome open now:** `NO`  
**Release now:** `NO`  
**runnable_evaluation:** `false` until `blocked_field_count == 0`  
**Alpha / capital / production:** `NONE`

## Constitution

> **Science is locked. Release is not.**  
> Build pre-open machinery only.  
> Q may be amended at most once outcome-blind.  
> Every future claim must bind clock + ledger + population + denominator.  
> While any release blocker remains, `runnable_evaluation=false` and outcome open is forbidden.  
> This is **not** a Q/M⊥/Q+M⊥ trophy slice. It is sparse basis identification infrastructure.

## Inherited AO-K0A law (live, not OFF)

| Object | Path |
|---|---|
| Canonical contract | `docs/architecture/orthogonalization_contract_v1.md` |
| Evidence receipt | `docs/context/e2e_evidence/ao_k0a_orthogonal_basis_preflight_20260811.json` |

Key freezes already true:

- full-W3 denominator `PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1`
- missingness = persistent `ABSTENTION` (no row deletion / no PASS-FAIL coverage gate)
- Q rank over Q-observed; Q∩M re-rank before residualization
- date-local OLS: `rank(M) ~ 1 + rank(Q) → M_perp`
- residual capital = economic cash
- opportunity comparator = PIT-EW full W3
- numeric Q **not** rederived in K0A
- result-bearing Q/M/Q+M_perp **forbidden** without new carve-out

OK-SBI-0 **must not** rewrite the K0A denominator law.

## Locked science (do not debate)

```text
good wager / forward net-payoff distribution (not “good company”)
missingness map → raw Q×M joint law → Residual-M novelty → deployability
multi-arm probes; A5 residual is a probe, not presumed winner
dual clocks (no forced common horizon)
Q clock: 9–15 months
M clock: 20–60 trading days
capital-time = REPORT ONLY (never leaderboard / promotion / allocation)
four ledgers with ledger-tagged claims only
shared_cause_test = NOT_RUN; economic_independence_claim = FORBIDDEN (v1.2 default)
max_outcome_blind_q_amendment_cycles = 1
```

## Comparison arms (formulas only until carve-out)

| Arm | Definition | Role |
|---|---|---|
| A1 `Q_NATIVE` | date-local Q rank on Q-observed | full/applicable Q baseline |
| A1C `Q_COMMON` | Q re-ranked on Q∩M | paired conditional baseline |
| A2 `M_RAW` | M rank on common support | raw M |
| A3 `Q+M` | 0.5·rank(Q)+0.5·rank(M) | additive raw |
| A4 `Q×M` | min(rank(Q),rank(M)) | sparse conjunction |
| A5 `Q+M⊥` | 0.5·rank(Q)+0.5·rank(M⊥) | K0A residual incumbent **probe** |

Also freeze low-DOF Q×M 2D surface template (bins fixed pre-open; **no post-label change**).

Arm constraints:

```text
No post-label tuning
No arm-specific K_t
No arm-specific denominator
No arm-specific tail/label/cost/lag
No extra sector/size/beta/vol neutralization in arm scores
```

## S0 queue (ordered; no queue-jumping)

1. `QSourceContractV1` feasibility (max 1 outcome-blind amendment)
2. Applicability / `NOT_APPLICABLE` law
3. Status-stratified basis-status extension (no K0A denominator rewrite)
4. Numeric gate population (honest `BLOCKED_UNSET`)
5. Seal Q/M clock label packs (hash only, no join)
6. Land v1.2 authority docs + machine freeze + claim schema
7. `PRODUCT_PREOPEN` packet only if Steps 1–6 ready and blockers path is real
8. Owner/CRO carve-out `OK-SBI-0-DEV-OPEN-1` — **not this worker** unless blockers zero + PRODUCT_PREOPEN PASS

## Q source law

`RevGrowth_12m + ROIC` is a **conceptual candidate only**, not authority.

Every primitive must bind:

```text
primitive_id, provider/source object, exact field identifier,
CIQSEC + trading_item identity, period/perspective semantics,
PIT availability timestamp, minimum publication/processing lag,
unit/currency law, formula/denominator, restatement/carry law,
applicability rule, missingness reason, corporate-action treatment,
source receipt hash, no-bridge proof
```

Legal feasibility verdicts only:

```text
Q_GF_BOUND
Q_MINIMAL_AMENDMENT_REQUIRED
Q_AMENDED_BOUND
Q_SOURCE_BLOCKED
```

Rules: max one outcome-blind amendment; no silent synthetic substitute; no unavailable-field bridge; no ticker/entity/PERMNO fallback; second redesign requires a **new** `slice_id`.

## Applicability law

```text
W3_INELIGIBLE
NOT_APPLICABLE          # in full-W3 census, outside kernel domain; not missingness; not abstention; no K_t; no cash-drag narrative
APPLICABLE_OBSERVED
APPLICABLE_UNOBSERVED   # ABSTAIN; unfilled = economic cash; counts in foregone-right-tail / avoided-catastrophe
```

Outcome-blind `claim_scope = DOMAIN_LIMITED_EX_ANTE` is allowed (e.g. banks/insurers if Q economics require it).

## Status strata (report separately)

```text
ELIGIBLE_COMPLETE
Q_UNOBSERVED
M_WARMUP
M_MISSING_HISTORY
Q_AND_M_MISSING
Q_NOT_APPLICABLE
M_NOT_APPLICABLE
OTHER_EXPLICIT_STATUS
```

No mixed “~20% unobserved” mashup language. No label join for retention metrics in S0.

## Ledgers (never merge)

```text
COMMON_SUPPORT_SCIENTIFIC_LEDGER   → conditional novelty / redundancy / synergy only
APPLICABLE_SYSTEM_LEDGER           → applicable-domain deployability only
FULL_W3_OPPORTUNITY_CENSUS         → full-W3 opportunity + tail census only
ABSTENTION_ATTRIBUTION_LEDGER      → foregone right-tail / avoided catastrophe only
```

Invalid by construction:

- common-support lift sold as full-W3 deployability
- opportunity census sold as strategy P&L
- abstention attribution sold as Alpha
- any result sentence without `ledger_id` or `clock_id`

## Context C firewall

Allowlist (outcome-blind, source-bound buckets only):

```text
decision_date_block, sector_group, market_cap_bucket, liquidity_bucket,
ipo_age_bucket, volatility_bucket, drawdown_bucket, distress_bucket,
corporate_action_state
```

Forbidden uses of C: arm score, Q/M rank, K_t fill, applicability rewrite, threshold selection, domain/router discovery, position sizing, cost/lag choice.

## Breadth fill law

**Common-support:** same population, same K_t, same tie-break; support < K_t → identical residual economic cash for all arms; no outside-support backfill.

**Applicable-system:** select only `APPLICABLE_OBSERVED` up to same K_t; unfilled → economic cash; `NOT_APPLICABLE` is not candidate / not abstention / not backfill pool.

## Implementation modules

```text
research/asymmetric_opportunity_v1/
  q_source_contract.py
  applicability.py
  status_strata.py
  arms.py
  context_c_firewall.py
  claim_schema.py
  ledgers.py
  label_packs.py
  release_gates.py
  preopen_freeze.py
  orthogonalization.py          # K0A authority (unchanged law)
```

## Hard stop-lines

```text
NEW_WINNER_OR_FUTURE_OUTCOME_OPEN
EMPIRICAL_Q_MPERP_QPLUSMPERP_RESULT
W6 / prospective / replication / untouched lockbox outcomes
new provider calls / source substitution / ticker-PERMNO bridges
K_t / tail / threshold / cost / lag / arm / Q / M tuning after any seal
post-hoc domain or router discovery
second run / rescue run
composite trophy / overall winner / cross-horizon leaderboard
PAPER / broker / capital / production / live authority
complete-case alpha claim
denominator rewrite / missingness row deletion
residual orthogonality = economic independence
using C in arm score / K fill / applicability rewrite
claiming full-W3 deployability from common-support lift
any untagged claim (missing ledger_id or clock_id)
```

There is **no** `OK-SBI-0-DEV-OPEN-1` yet. Workers must refuse outcome join.

## Authority companions

- Release hardening: `docs/architecture/ok_sbi_0_release_hardening_v1_2.md`
- Machine freeze: `docs/context/e2e_evidence/ok_sbi_0_machine_freeze_v1_2.json`
- Claim schema: `docs/context/e2e_evidence/ok_sbi_0_claim_receipt_schema_v1_2.json`
- Worker prompt (root mirror): `OK-SBI-0_Worker_Prompt_S0.md`
