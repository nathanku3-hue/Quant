# TRANSITION_RECOGNITION_v0 — L2 Observation Contract

**Slice:** `TR-v0-L2-OBSERVATION-CONTRACT-1`  
**Date:** 2026-08-12  
**Status:** `L2_CONTRACT_FROZEN_WAITING_RECOGNITION_SOURCE`  
**Parent admission:** G0–G2 `ALL_PASS_ADMIT_L1_FROZEN`  
**FTK primary:** STOPPED (no rescue)

---

## Golden question

Among companies with a **real operating transition**, what independently observable **PIT** state distinguishes a merely real transition from an **economically selectable, not-yet-recognized** transition?

This slice freezes **how to observe** Reality and Recognition. It does **not** evaluate selection, timing, or economics.

---

## Selection vs timing

| Track | In this slice? |
|---|---|
| **A. Recognition as selection** (Reality vs Reality+Gap) | Contract only |
| **B. Recognition as timing / entry trigger** | **Forbidden** |

---

## Reality observation (not FTK policy)

Reality is a **PIT operating-transition observation**.

**Bound observation primitives** (admitted S0 / FTK-0 lineage as *observation*, not economic policy):

- `IQ_PERIOD_END`, `IQ_TOTAL_REV`, `IQ_INVENTORY`, `IQ_OPER_INC`
- Derived: inventory economic level, operating margin

**Forbidden as Reality:**

- FTK K=20 rank / selected set
- FTK H=63 hold policy
- FTK residual outcomes

Missingness → **ABSTAIN**. No return-based Reality flags.

---

## Recognition observation

**API:** `alpha_pit_data_api_v1.expectations(ids, as_of)`  
**Purpose:** consensus/expectation state for expectation-gap science (not company quality alone).

### Primary measures (v0 decision surface)

| Measure | Role |
|---|---|
| `EPS_FY1` | level recognition |
| `EPS_FY1_REVISION_30D` | primary revision recognition |
| `EPS_FY1_REVISION_90D` | secondary revision recognition |

### Parked (not free feature search)

`EPS_FY2`, revenue levels/revisions, `FORWARD_PE` — may enter only via a later freeze slice.

### PIT law

- `available_at <= decision_as_of`
- latest lawful vintage only
- `OBSERVED_CONSENSUS` vs `INFERRED_MARKET_IMPLIED` labeled distinctly
- missing / not entitled / stale → **ABSTAIN**

### Source bind (honest)

```text
status = MISSING_SOURCE
reason = CIQ_EXPECTATIONS_CAPTURE_NOT_LANDED
```

Adapter behavior already emits `MISSING_SOURCE` sentinel rows when expectations source pair is absent.  
**This slice does not invent bytes and does not open provider capture.**  
CRV1 family artifacts are **not** TR-v0 authority.

---

## Recognition gap (form frozen; cuts unset)

Given `Reality=true`, gap means contemporaneous recognition has **not** incorporated the transition.

Operator **forms** (cuts `BLOCKED_UNSET` until L3/L4; no residual fit):

1. **REV_LAG_AFTER_REALITY** — Reality true and short-horizon EPS revision not material up-update  
2. **LEVEL_STALE_VS_REALITY** — Reality true and level recognition classified not-yet-updated  

**Already recognized form:** Reality true and material concurrent recognition update under the same frozen cuts.

**Later contrast (not this slice):**

- Arm A: Reality only  
- Arm B: Reality + Gap  
- Test: D6 selection enrichment B vs A under a separate preregistered wager law  

---

## Explicit non-goals

No returns/labels, no H/K/threshold grid, no debit/L5, no timing research, no FTK rescue, no AO-FTK-2, no alpha claim, no inventing expectation bytes.

---

## Exit

| State | Meaning |
|---|---|
| **This terminal** | L2 observation contract frozen; recognition **source missing** |
| **Next if source lands** | Source-admit slice or L3 SNR under bound source |
| **Next if source blocked long** | HOLD_SOURCE — do not invent; do not L5 |

---

## One-line

> Freeze how Reality and Recognition are observed. Do not spend a trial. Do not invent consensus. Do not open timing or FTK rescue.
