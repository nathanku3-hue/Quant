# Historical Fundamental Vintage Authority

**Date:** 2026-08-09  
**Status:** `RESOLVED / OPTION_A_ORIGINAL / PARITY_CLOSED`
**Strategic lock:** `docs/architecture/aov_strategic_direction_lock_20260809.md`  
**Roadmap authority:** `docs/architecture/aov_endgame_generalization_spec_current.md`  
**Runtime effect of this document alone:** `NONE`  
**A1 / A2 admission:** `VINTAGE + PARITY CLOSED; A1 STILL BLOCKED BY HISTORICAL RISK-SET + PRIMARY-IDENTITY AUTHORITY`
**financial_alpha_evidence:** `0`

---

## 0. Purpose

Freeze exactly one explicit, economically legitimate historical-fundamental vintage semantic for Capital IQ PIT work, and prevent misleading labels, dual authorities or compatibility bridges from manufacturing A1/A2 claims.

This is an **evidence gate**, not an architecture reopen.

---

## 1. Resolved authority (current working tree)

The prior contradiction is closed. The one active A1/A2 fundamental-vintage path is:

```text
Capital IQ SPG historical as-of date
+ FilingVer = Original
→ provider-captured raw rows retain as_of_date + retrieved_at_utc
→ research/aov0/historical_pit.py rejects any non-Original row
→ exact frozen current-cut AOV builder
→ historical replay only
```

Active historical fundamental capture paths all request and emit `Original`:

```text
scripts/aov0_capture_ciq_historical_pit_fundamentals.ps1
scripts/aov0_capture_ciq_historical_pit_fundamental_chunk.ps1
scripts/aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1
scripts/aov0_capture_ciq_historical_pit_transition_batch.ps1
```

`research/aov0/ciq_historical_pit.py` is retained only as an explicitly labeled legacy diagnostic fixture normalizer and emits `LEGACY_DIAGNOSTIC_ONLY_NOT_A1_A2_AUTHORITY`; it is not an A1/A2 reader or alternate vintage authority.

---

## 2. Board / Quant decision rule

Do **not** choose `Original` versus as-of `Current/Restated` by executive preference.

```text
Quant/Data must prove provider semantics
→ freeze the economically legitimate contract
→ one explicit historical-vintage authority
→ one active implementation
→ no misleading labels
→ no compatibility bridge
```

The leadership group approves the **rule** above, not a preferred label without proof.

---

## 3. Frozen resolution

### WINNER — Option A: Original-filing historical PIT

```text
historical PIT authority = CIQ SPG historical as-of + FilingVer = Original
```

Required and now enforced:

- all active historical fundamental capture requests `Original`
- raw rows / receipts state `Original`
- replay source-semantic validation rejects non-Original rows
- the as-of cutoff and current retrieval timestamp are both retained
- the legacy generic historical normalizer is diagnostic-only and cannot admit A1/A2
- no active Current/Restated fundamental acquisition path exists for Lane 2

### Rejected active alternative — Option B: Explicit as-of Current/Restated historical authority

If Capital IQ as-of / Current/Restated semantics are intentionally selected:

```text
create a new explicit schema/version
document what the row represents
bind provider/vintage semantics
test temporal validity
```

Do **not** describe Current/Restated bytes as Original.

### Forbidden

```text
Current/Restated bytes → historical_spg_asof_original = true
dual active vintage authorities
fallback / alias / dual-write / feature-flag bridge
silent label repair after results inspection
```

When the winning authority becomes current, remove the losing active reader/writer/path/label in the same implementation slice (Destructive Authority Replacement Law). Historical artifacts remain immutable evidence under their pinned contract.

---

## 4. Frozen semantic contract

The authority is deliberately narrow:

```text
observable at decision cut
= values returned by CIQ SPG for that historical as-of date under FilingVer=Original

later revisions / restatements
= later information; forbidden from the A1/A2 feature state under this authority

current retrieval timestamp
= custody timestamp only; never economic availability time

historical as-of date
= provider information cutoff, conservatively activated only after the decision cut

permitted A1/A2 features
= only factor state reconstructed from the admitted Original/as-of rows and then passed through the frozen AOV policy path
```

S&P's retained provider capability probe demonstrates that the SPG fourth argument genuinely gates historical availability: for entity `4094286`, FQ0 moved from `2024-01-28` at the `2024-04-30` cutoff to `2024-04-28` at the `2024-06-30` cutoff, while fixed `FQ12025` revenue was unavailable at the earlier cutoff and populated only at the later one. The installed client also accepts `FilingVer=Original`. This is the local provider-semantic proof bank for the frozen authority.

---

## 5. Exact-replay parity gate — CLOSED

Historical decisions now call the exact frozen current-cut builder (`research.aov0.ciq_market.build_ciq_market_slice`) rather than reimplementing its policy logic. Tests prove same-input parity for:

```text
security + trading-item identity
ADV20 / dollar volume
realized volatility
SMA20 / SMA200 / distance / trend veto / trend state
Q / U inputs and technical state
exit capacity / regime
sizing eligibility
Rule100 weights
Q / M / F_proxy / C_proxy / L / R / U cube state
```

The only declared temporal difference is mechanical: a completed-week decision state activates on the next observed close. `activate_decision_cube_states` freezes the decision-cut cube state onto that activation calendar, so no activation-day information enters the decision. A canonical five-arm test passes on the activated historical cube.

---

## 6. Acquisition concurrency after freeze

Provider acquisition may use bounded parallel Excel workers **only after** the vintage semantic is frozen:

```text
start = 2 independent Excel workers
→ measure COM/provider stability + integrity + wall-clock
→ scale to 3–4 only from measured stability
```

Do not respond to Office latency by building a generic provider platform.

---

## 7. A1 / A2 law under this authority

```text
legitimate historical PIT CIQ (winning vintage only)
→ exact frozen-AOV replay (parity-proven)
→ A1
→ FREEZE A2 CONTRACT
→ one query-metered untouched historical PIT OOS
→ A2
```

- Lane 2 may not open Clock #1 outcomes
- Lane 2 may not tune Parent/Child between A1 and A2
- A2 used to design a challenger is no longer untouched evidence for that challenger
- A1/A2 do not increment `financial_alpha_evidence` under current prospective-evidence law

---

## 8. Current status record

| Item | Status |
|---|---|
| Winning vintage authority chosen | **CLOSED — Option A / Original** |
| Provider-semantic proof banked | **CLOSED — retained SPG as-of availability probe + Original callable** |
| Losing active fundamental-vintage path removed | **CLOSED — no active Current/Restated Lane-2 fundamental writer/reader** |
| Legacy generic historical normalizer | **DIAGNOSTIC ONLY / NOT A1_A2 AUTHORITY** |
| Current↔historical AOV parity proof | **CLOSED — exact current-cut builder + activation-cube test** |
| Historical high-growth start risk set | **OPEN / A1 HARD BLOCK** |
| Historical primary security/trading-item identity at A1 start | **OPEN / A1 HARD BLOCK** |
| A1 admission | **BLOCKED ON THE TWO SOURCE-AUTHORITY ITEMS ABOVE** |
| A2 admission | **BLOCKED BEHIND ADMITTED A1 + FREEZE + ONE QUERY-METERED OOS READ** |

The vintage/parity gate itself no longer blocks Lane 2. No current-screen-conditioned cohort, current-primary mapping, diagnostic provider probe, or backtest result may substitute for the two remaining historical source-authority objects. `financial_alpha_evidence` remains `0`.
