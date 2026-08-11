# AO-FTK-1-ECON-1 — Economic / Asymmetry Estimand Freeze

**Freeze ID:** `AO-FTK-1-ECON-1`  
**Parent program:** `AO-FTK-1-20260812`  
**Name:** `FTK_ECONOMIC_ASYMMETRY_FREEZE`  
**Date:** 2026-08-12  
**Spec:** `v1.0`  
**Role:** `SHADOW_RESEARCH / RESEARCH_ONLY`  
**Science mode:** `OUTCOME_BLIND_ECONOMIC_ASYMMETRY_FREEZE`  
**Status:** `ECON_FREEZE_PASS_WAITING_OWNER_NUMERICS`  
**Authorized phase:** `ECONOMIC_ESTIMAND_FREEZE` only  
**L7 route:** `LATER_ECONOMIC_CUT_FREEZE_PLUS_SECOND_TRIAL` (owner dispatch of this freeze)  
**Economic L5 authorized:** `false`  
**financial_alpha_evidence:** `0`  
**Material trials charged this turn:** `0`

Machine freeze: `docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.json`

---

## Constitution

> **Freeze the economic estimand outcome-blind on the unchanged 2-DOF sensing law.**  
> Debit nothing. Join nothing. Run nothing.  
> **Stop at WAIT_OWNER_L5_ECONOMIC.**

---

## Why this freeze exists

### Trial 1 already answered (do not re-litigate)

| Question | Answer |
|---|---|
| Does frozen 2-DOF FTK sense next-PIT transition under full-W3? | **YES** — `BOTH_NODES_MEASURABLE_SIGNAL`; D1–D5 PASS @ `948471c` |

### This freeze prepares Trial 2’s question (not the trial)

> Does the **unchanged** sensing law identify economically asymmetric wagers after preregistered payoff horizon, right-tail, catastrophe, and cost law?

### Governing distinction

| Step | Meaning |
|---|---|
| L7 route selection | What the next evidence dollar buys |
| **THIS FREEZE** | Define the economic estimand outcome-blind |
| Second L5 | Separate owner authorization + debit 1 + join once + one eval |
| L8 refinement | Only after Trial 2 earns it |

**Not authorized this turn:** Trial 2 debit · economic label join · auto L5 · H grid · DOF rewrite · AO-FTK-2 · invent D7 · invent E13/E14 · capital / W6 / alpha claim.

---

## Surface inheritance (binding — no redesign)

```text
parent_program           = AO-FTK-1-20260812
parent_l4_freeze         = docs/architecture/ao_ftk_1_20260812_l4_charged_slice_freeze.json
parent_l5_run            = docs/context/e2e_evidence/ao_ftk_1_20260812_l5_run.json
kernel_id                = AO_FTK_0_TRANSITION_SPARSE_BASIS_V1
effective_decision_dof   = 2   # FROZEN
inventory_state          = continuous lag-1 inventory economic-level delta
margin_state             = continuous operating-margin M1 state
operators                = INV_DELTA_MEAN_REVERSION
                         + MARGIN_M1_STATE_MEAN_REVERSION
operator_bytes           = FROZEN (M1 mutation FORBIDDEN)
routing                  = DOMAIN_LIMITED_EX_ANTE
```

| Slot | Operator | Immutability pin (sha256) |
|---|---|---|
| 1 | `INV_DELTA_MEAN_REVERSION` | `9434b495…0fdd85` |
| 2 | `MARGIN_M1_STATE_MEAN_REVERSION` | `a464058d…b633cd` |

Pins match parent L4 exactly. Silent 1-DOF collapse, third DOF, operator rewrite, drop inventory, free composite trophy: **FORBIDDEN**.

---

## Constitutional D6–D9 mapping (do not rename layers)

| Layer | Economic subclaim |
|---|---|
| **D6_SELECTION_ENRICHMENT** | Unchanged FTK surface under fixed-breadth action map improves predeclared forward-payoff and/or right-tail vs frozen comparator? |
| **D7_CONFIRMATION_TIMING** | Apply **existing** repo-authoritative confirmation only. **None found → `BLOCKED_UNSET` → L5 blocker.** Do not invent. |
| **D8_HOLD_EXIT_CONVEXITY** | Frozen holding/exit law avoids unacceptable catastrophe under ex-ante definition? |
| **D9_ECONOMICS_COST_CAPACITY** | After lag + costs + fixed breadth + abstention→cash, does ΔJ clear materiality floor? |

First-fail order remains **D1→D9** for any later economic RUN.

### Precommitted Trial-2 routes (record only — do not execute)

| Outcome | Route |
|---|---|
| D6 FAIL | HOLD or STOP FTK; do not refine rep |
| D6 PASS / D7 FAIL | Transition sensor only; no winner-kernel claim |
| D7 PASS / D8 FAIL | Reject action law; only separately frozen safety-policy may continue |
| D6–D8 PASS / D9 FAIL | No capital path; refine only if cheap falsifiable seam |
| D6–D9 PASS | Research candidate only; **not** capital authority; alpha not automatic |

---

## E1–E12 freeze contract (form + ownership)

Outcome-blind. No E13/E14 as authority.

| ID | Form (frozen) | Value / owner |
|---|---|---|
| **E1** Payoff horizon | Fixed executable wager horizon (single H; no grid) | `H_VALUE` = **OWNER_BLOCKED_UNSET** |
| **E2** Net return | decision_asof → lag → entry → H → exit → CA/TR adj → costs = R_net | price/return law = **BLOCKED_UNSET** (L5 blocker) |
| **E3** Execution & cost | Fixed lag + ex-ante cost; `free_fit=false` | lag/cost = **BLOCKED_UNSET** (L5 blocker) |
| **E4** Right tail | Date-local percentile of forward R_net on full-W3 | percentile = **OWNER_BLOCKED_UNSET** |
| **E5** Catastrophe | Date-local left-tail percentile of R_net (ONE primary) | percentile = **OWNER_BLOCKED_UNSET** |
| **E6** Utility J | FTK fixed-breadth net − PIT-EW Full W3 net; catastrophe separate gate | `delta_J_required` = **OWNER_OR_CRO_BLOCKED_UNSET** |
| **E7** Action map | Continuous FTK node scores; dual-node equal-weight rank → top-K; abstain→cash; no threshold search | `K` = **OWNER_BLOCKED_UNSET** |
| **E8** Comparator pop | PRIMARY Full-W3 (abstain→cash); DIAGNOSTIC support ledger never rewrites denom | **FROZEN** |
| **E9** Stability | Identical folds to sensing Trial 1 (4 temporal folds; min N=30; cov≥0.2; ≥3 supporting) | **INHERITED_AUTHORITY** |
| **E10** D6→D9 map | § mapping above; D7 rule absent | D7 = **BLOCKED_UNSET** |
| **E11** Economic labels | New ECONOMIC pack; identity+hash frozen; bytes unjoined | **FROZEN** unjoined |
| **E12** IDs | Parent = AO-FTK-1-20260812; Freeze = AO-FTK-1-ECON-1 | **FROZEN** (not AO-FTK-2) |

### Forbidden on E1/E4/E7

- Horizon grid `{5d,10d,21d}` or borrowed Breakout clocks  
- Named-winner (MU/SNDK) or CAGR as primary success  
- Threshold / policy optimizer search  
- Reuse sensing label pack for economic estimand  

---

## Authority survey (no invention)

| Topic | Finding | Disposition |
|---|---|---|
| Executable H | No FTK-canonical executable wager horizon (sensing H is next-PIT structured transition) | E1 OWNER_BLOCKED_UNSET |
| Price / total-return | AOV/PIT narrative exists; no FTK-ECON bound law | E2 BLOCKED_UNSET |
| Lag / cost | AOV `one_bar` / `turnover*0.0010` are not FTK-ECON authority | E3 BLOCKED_UNSET |
| PIT-EW Full W3 | Form inherit from endgame / OpportunityKernel accounting | E6/E8 form frozen |
| D7 confirmation | Layer ID only in method constitution; no FTK rule object | D7 BLOCKED_UNSET |
| Trial-1 folds | L5 run receipt | E9 inherited |

---

## Later Trial-2 debit plan (not debited)

```text
plan_id                                          = FTK1_ECON_TRIAL_DEBIT_PLAN_V1
material_trials_total_remaining_before_trial2    = 2
next_debit                                       = 1
remaining_after_trial2                           = 1
debit_trigger                                    = ECONOMIC_L5_AUTHORIZATION_RECEIPT only
debit_this_turn                                  = FORBIDDEN
```

---

## Economic label custody (identity + hash only)

```text
label_pack_type   = ECONOMIC
identity          = data/prebreakout/compiled/ao_ftk_1_econ_1_label_custody/economic_label_pack.identity.json
hash_procedure    = data/prebreakout/compiled/ao_ftk_1_econ_1_label_custody/economic_label_pack.hash_procedure.json
bytes_joined      = false
join_authorized   = false until economic L5_AUTHORIZE
```

Sensing pack path `ao_ftk_1_20260812_label_custody/` must **not** be reused for the economic estimand.

---

## Fail-closed guards

If `economic_l5_authorized == false`:

| Call | Result |
|---|---|
| `economic_label_join()` | FAIL CLOSED |
| `trial_debit()` | FAIL CLOSED |
| `economic_evaluator.run()` | FAIL CLOSED |

Implementation: `research/asymmetric_opportunity_v1/ao_ftk_1_econ_1_contract.py`

---

## L5 readiness checklist

| # | Item | Status |
|---|---|---|
| 1 | L7 route machine-effective | **PASS** |
| 2 | ECON freeze form PASS | **PASS_FORM** |
| 3 | H_VALUE bound | OWNER_BLOCKED_UNSET |
| 4 | E2 price/return authoritative | BLOCKED_UNSET |
| 5 | E3 lag/cost bound or owner waive | BLOCKED_UNSET |
| 6 | E4/E5 percentiles bound | OWNER_BLOCKED_UNSET |
| 7 | E6 delta_J_required bound | OWNER_OR_CRO_BLOCKED_UNSET |
| 8 | E7 K bound | OWNER_BLOCKED_UNSET |
| 9 | D7 rule or owner scope-out | BLOCKED_UNSET |
| 10 | E11 identity+hash; join false | **PASS** |
| 11 | Surface dof=2 pins match parent | **PASS** |
| 12 | Separate L5_AUTHORIZE receipt | **NOT_ISSUED** |

Any missing item → **WAIT_OWNER / HOLD**, not improvise.

---

## Authority flags

```text
l5_authorized / economic_l5_authorized = false
l5_auto_open                           = false
runnable_evaluation                    = false
capital_authority                      = false
financial_alpha_evidence               = 0
ao_ftk_2                               = NOT_AUTHORIZED
l8_bounded_refinement                  = DEFER
q_source_status                        = Q_SOURCE_BLOCKED_TERMINAL
w6                                     = UNTOUCHED
product_state                          = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
```

---

## Next

```text
next_phase              = WAIT_OWNER_L5_ECONOMIC
next_owner_action       = bind remaining numerics if any → L5_AUTHORIZE_ECONOMIC | HOLD | STOP
next_worker_recommended = L5_AUTHORIZE_ECONOMIC_SEPARATE  (not auto)
```

Correct loop:

```text
OWNER L7 route → FREEZE (this) → WAIT_OWNER_L5_ECONOMIC
  → L5_AUTHORIZE (later) → one debit · one join · one eval
  → L6 first-fail · info-gain → L7 again
```

Not: run → diagnose → refine → run.

---

## Stop-lines (refuse)

`TRIAL2_DEBIT_THIS_TURN` · `ECONOMIC_LABEL_JOIN_THIS_TURN` · `AUTO_L5_AFTER_FREEZE` · `H_OR_PERCENTILE_GRID_SEARCH` · `POST_PEEK_CUT_BINDING` · `DOF_COLLAPSE_OR_THIRD_DOF` · `OPERATOR_OR_REPRESENTATION_REWRITE` · `DROP_INVENTORY_PRE_RESULT` · `FEATURE_ADD` · `OPEN_AO_FTK_2` · `INVENT_D7_CONFIRMATION_RULE` · `INVENT_E13_E14_AS_AUTHORITY` · `INVENT_PRICE_LAG_COST_LAW` · `REUSE_SENSING_LABELS_FOR_ECONOMIC_ESTIMAND` · `Q_INVENT_OR_S2` · `REOPEN_AO_FTK_0` · `W6_OPEN` · `CAPITAL_OR_ALPHA_CLAIM` · `L8_REFINEMENT_THIS_TURN` · `CAGR_OR_MU_SNDK_AS_PRIMARY_SUCCESS`

**stop_lines_hit this turn:** none
