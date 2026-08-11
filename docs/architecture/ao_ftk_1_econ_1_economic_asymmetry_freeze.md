# AO-FTK-1-ECON-1 — Economic / Asymmetry Estimand Freeze + Trial 2 Complete

**Freeze ID:** `AO-FTK-1-ECON-1`  
**Parent program:** `AO-FTK-1-20260812`  
**Name:** `FTK_ECONOMIC_ASYMMETRY_FREEZE`  
**Bind name:** `FTK_ECON1_ACCEPT_DRAFT_TRANSITION_POSITION_BIND`  
**Date:** 2026-08-12  
**Spec:** `v1.0` (ACCEPT_DRAFT long session)  
**Role:** `SHADOW_RESEARCH / RESEARCH_ONLY`  
**Science mode:** `OUTCOME_BLIND_ECONOMIC_ASYMMETRY_FREEZE` + `TRANSITION_POSITION_ECONOMIC`  
**Status:** `ECON_L5_COMPLETE_WAITING_OWNER_L7`  
**Bind verdict:** `PASS_L5_READY` (ACCEPT_DRAFT)  
**Authorized phase:** `L5_COMPLETE_WAITING_OWNER_L7`  
**Session path:** `C_TRIAL2_COMPLETE`  
**L7 route:** `LATER_ECONOMIC_CUT_FREEZE_PLUS_SECOND_TRIAL` (machine-effective; Trial 2 spent)  
**Economic L5 authorized:** `true` (one-shot spent)  
**financial_alpha_evidence:** `0`  
**Material trials after:** charged `2` / remaining `1`  
**First fail layer:** `D2_DATA_OBSERVABLE` (Full-W3 market custody missing)  
**Prior freeze commit:** `febd8e4`  
**Prior sensing commit:** `948471c`  
**Prior Path A:** `0350082` empty attachment

Machine freeze: `docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.json`  
Owner bind receipt: `docs/context/e2e_evidence/ao_ftk_1_econ_1_owner_bind_transition_position.json`  
L5 run: `docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_run.json`  
L6: `docs/context/e2e_evidence/ao_ftk_1_econ_1_l6_layered_diagnosis.json`  
L7: `docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_owner_packet.json`

---

## Constitution

> **Accept draft binds. One transition-position economic trial.**  
> Same return law both sides. ΔJ>0 is a screen not capital.  
> L6 first-fail. L7 stop. No slice 2.

---

## Economic clock (binding this turn)

```text
economic_clock_class     = TRANSITION_POSITION
product_class_band       = months → quarters
not_fast_trading         = true
not_great_enterprise_hodl= true
great_enterprise_kernel  = OUT_OF_SCOPE
```

| Class | Horizon band | Role |
|---|---|---|
| FAST / TRADING | weeks → months | Other families; **not** this trial’s primary |
| **FTK / TRANSITION** | **months → quarters** | **THIS trial’s product class** |
| GREAT ENTERPRISE | quarters → years | OUT OF SCOPE (separate future program) |

Trial-2 hypothesis (when later authorized): company enters favorable economic transition → transition persists long enough → market/economics improve → capture repricing over the transition horizon.

**Primary H requirement:** one scalar `H_VALUE` only — no band search, no multi-primary H, no Breakout borrow, no GE multi-year primary.

---

## Why this bind exists

### Already true

| Fact | Status |
|---|---|
| Trial 1 sensing PASS (both nodes measurable; D1–D5) | `@948471c` |
| ECON-1 form freeze PASS_WAITING_NUMERICS | `@febd8e4` |
| surface dof=2; operators frozen | pins match parent L4 |
| trials = 1 charged / 2 remaining | debit this turn = 0 |
| economic labels identity+hash frozen | bytes unjoined |
| L5_AUTHORIZED | false |

### This turn’s question

Bind the economic clock and laws so Trial 2 can test a **transition-position** wager — not a breakout scalp and not a permanent compounder hold.

### Owner attachment this dispatch

**Empty.** Worker surveyed inheritance only. **No invented numerics.** Verdict = `WAITING_NUMERICS`.

---

## Surface inheritance (binding — no redesign)

```text
parent_program           = AO-FTK-1-20260812
kernel_id                = AO_FTK_0_TRANSITION_SPARSE_BASIS_V1
effective_decision_dof   = 2   # FROZEN
operators                = INV_DELTA_MEAN_REVERSION
                         + MARGIN_M1_STATE_MEAN_REVERSION
routing                  = DOMAIN_LIMITED_EX_ANTE
score_map form           = DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K
```

| Slot | Operator | Immutability pin (sha256) |
|---|---|---|
| 1 | `INV_DELTA_MEAN_REVERSION` | `9434b495…0fdd85` |
| 2 | `MARGIN_M1_STATE_MEAN_REVERSION` | `a464058d…b633cd` |

---

## Bind pack (outcome-blind)

| Field | Source | Value |
|---|---|---|
| **Clock** | OWNER stamp | `TRANSITION_POSITION` |
| **E1 H_VALUE** | OWNER_BLOCKED_UNSET | unset (no attachment) |
| **E2 price/return** | BLOCKED_UNSET | no FTK-ECON law; refuse invent |
| **E3 lag/cost** | BLOCKED_UNSET | AOV defaults not authority; refuse invent |
| **E4 RT%** | OWNER_BLOCKED_UNSET | unset |
| **E5 catastrophe%** | OWNER_BLOCKED_UNSET | unset |
| **E6 ΔJ floor** | OWNER_OR_CRO_BLOCKED_UNSET | unset (comparator form inherited) |
| **E7 K** | OWNER_BLOCKED_UNSET | unset (score map form frozen) |
| **E9 folds** | INHERITED_AUTHORITY | L5 run @ sensing Trial 1 |
| **D7** | BLOCKED_UNSET | no invent; owner may later INHERIT or OUT_OF_SCOPE |

All binds carry `outcome_blind=true`, `residual_peek=false`.

### Hold/exit thinness (Trial-2 form only — not executed)

Primary hold law: enter under frozen action map at `decision_asof` → hold for frozen H → exit under frozen exit-price convention.  
**FORBIDDEN this turn:** adaptive “hold while transition remains alive” exit search.

---

## Authority survey (reconfirmed; no invention)

| Topic | Finding | Disposition |
|---|---|---|
| Executable H | No FTK-canonical executable wager horizon | E1 OWNER_BLOCKED_UNSET |
| Price / total-return | AOV/PIT narrative exists; no FTK-ECON bound law | E2 BLOCKED_UNSET |
| Lag / cost | AOV `one_bar` / `turnover*0.0010` not FTK-ECON authority | E3 BLOCKED_UNSET |
| PIT-EW Full W3 | Form inherit | E6/E8 form frozen |
| D7 confirmation | Layer ID only; no FTK rule object | D7 BLOCKED_UNSET |
| Trial-1 folds | L5 run receipt | E9 INHERITED |

---

## Constitutional D6–D9 map (unchanged IDs)

| Layer | Economic subclaim |
|---|---|
| **D6** | Fixed-breadth selection improves predeclared payoff/RT traits |
| **D7** | Only if rule inherited or de-scoped; never invented |
| **D8** | Frozen hold-for-H (thin exit law) vs catastrophe gate |
| **D9** | ΔJ ≥ floor after lag+costs+breadth |

### Precommitted Trial-2 routes (record only — do not execute)

| Outcome | Route |
|---|---|
| D6 FAIL | HOLD/STOP FTK; no representation refine |
| D6 PASS / D7 FAIL | Sensor not confirmed selection kernel |
| D7 PASS / D8 FAIL | Reject action/hold law; safety-policy only later |
| D6–D8 PASS / D9 FAIL | No capital path; refine only cheap seam later |
| D6–D9 PASS | Research candidate only; still not capital/alpha auto |

---

## L5 readiness checklist

| # | Item | Status |
|---|---|---|
| 1 | economic_clock_class = TRANSITION_POSITION | **PASS** |
| 2 | H_VALUE bound (single) | OWNER_BLOCKED_UNSET |
| 3 | E2 price/return INHERITED or OWNER_BOUND | BLOCKED_UNSET |
| 4 | E3 lag/cost INHERITED or OWNER_BOUND | BLOCKED_UNSET |
| 5 | E4 percentile bound | OWNER_BLOCKED_UNSET |
| 6 | E5 percentile bound | OWNER_BLOCKED_UNSET |
| 7 | E6 delta_J_required bound | OWNER_OR_CRO_BLOCKED_UNSET |
| 8 | E7 K bound | OWNER_BLOCKED_UNSET |
| 9 | D7 inherited OR explicitly out of scope | BLOCKED_UNSET |
| 10 | E11 identity+hash; join false | **PASS** |
| 11 | surface dof=2 pins unchanged | **PASS** |
| 12 | l5_authorized still false | **PASS** |
| 13 | fail-closed guards still true | **PASS** |

**l5_ready = false** → next = `WAITING_OWNER_NUMERICS` (not auto L5).

---

## Fail-closed guards

If `economic_l5_authorized == false`:

| Call | Result |
|---|---|
| `economic_label_join()` | FAIL CLOSED |
| `trial_debit()` | FAIL CLOSED |
| `economic_evaluator.run()` | FAIL CLOSED |
| invent E2/E3/D7/H | FAIL CLOSED |

Implementation: `research/asymmetric_opportunity_v1/ao_ftk_1_econ_1_contract.py`

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

## Next

```text
bind_verdict            = WAITING_NUMERICS
l5_ready                = false
next_phase              = WAITING_OWNER_NUMERICS
next_owner_action       = provide owner bind attachment | HOLD | STOP
next_worker_recommended = OWNER_NUMERICS_OR_HOLD
```

Correct chain after owner binds:

```text
BIND complete (L5_READY)
  → WAIT_OWNER_L5_ECONOMIC
  → separate L5_AUTHORIZE prompt
  → debit 1 · join once · one eval · L6 · L7
```

---

## Stop-lines (refuse)

`TRIAL2_DEBIT` · `ECONOMIC_LABEL_JOIN` · `EVALUATION_RUN` · `AUTO_L5` · `H_GRID_OR_MULTI_PRIMARY_H` · `BORROW_BREAKOUT_CLOCK_AS_DEFAULT` · `GREAT_ENTERPRISE_HORIZON_AS_PRIMARY` · `INVENT_E2_PRICE_RETURN_LAW` · `INVENT_E3_LAG_COST_LAW` · `INVENT_D7_CONFIRMATION` · `POST_PEEK_CUTS_FROM_SENSING_RESIDUALS` · `ADAPTIVE_TRANSITION_EXIT_SEARCH` · `DOF_COLLAPSE_OR_THIRD_DOF` · `OPEN_AO_FTK_2` · `L8_REFINEMENT` · `Q_INVENT_OR_S2` · `REOPEN_AO_FTK_0` · `W6_OPEN` · `CAPITAL_OR_ALPHA_CLAIM` · `CAGR_OR_MU_SNDK_PRIMARY_SUCCESS`

**stop_lines_hit this turn:** none
