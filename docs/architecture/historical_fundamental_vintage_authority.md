# Historical Fundamental Vintage Authority

**Date:** 2026-08-09  
**Status:** `REQUIRED / UNRESOLVED / A1_A2_HARD_BLOCK`  
**Strategic lock:** `docs/architecture/aov_strategic_direction_lock_20260809.md`  
**Roadmap authority:** `docs/architecture/aov_endgame_generalization_spec_current.md`  
**Runtime effect of this document alone:** `NONE`  
**A1 / A2 admission:** `BLOCKED UNTIL VINTAGE + PARITY CLOSE`  
**financial_alpha_evidence:** `0`

---

## 0. Purpose

Freeze exactly one explicit, economically legitimate historical-fundamental vintage semantic for Capital IQ PIT work, and prevent misleading labels, dual authorities or compatibility bridges from manufacturing A1/A2 claims.

This is an **evidence gate**, not an architecture reopen.

---

## 1. Verified contradiction (current working tree)

```text
research/aov0/historical_pit.py
→ requires FilingVer = Original
→ rejects non-Original filing version

scripts/aov0_capture_ciq_historical_pit_fundamentals.ps1
scripts/aov0_capture_ciq_historical_pit_fundamental_chunk.ps1
→ request FilingVer = Current/Restated
→ emit filing_version = Current/Restated

scripts/aov0_historical_pit_replay.py
→ A1 report currently writes historical_spg_asof_original = true
```

This combination is **non-authoritative**. No A1/A2 economic claim may be admitted while it stands.

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

## 3. Allowed resolutions (choose exactly one)

### Option A — Original-filing historical PIT

```text
historical PIT authority = FilingVer = Original
```

Then:

- all active historical fundamental capture must request Original
- receipts must state Original
- provider semantics must be verified
- Current/Restated active acquisition path removed

### Option B — Explicit as-of Current/Restated historical authority

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

## 4. What the authority must answer

Any frozen vintage contract must document:

```text
what was observable at decision time
what could change later (revisions)
what is revision information vs contemporaneous fact
what is permitted in A1 / A2 feature construction
what labels/receipts must carry
```

---

## 5. Exact-replay parity gate (with vintage)

After vintage authority freezes, current and historical AOV implementations must prove same-input parity for shared economics before A1 may claim `exact frozen-AOV historical replay`.

Minimum parity surfaces:

```text
identity
ADV20
realized volatility
SMA / trend state
Q / U and technical state
sizing eligibility
Rule100 weights
```

Only explicitly declared temporal-activation differences are allowed. Extract the smallest pure feature/policy kernel justified by this real Rule-of-Two reuse; do not rewrite the already-running Clock #1 organism.

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
| Winning vintage authority chosen | **OPEN** |
| Provider-semantic proof banked | **OPEN** |
| Losing path/label removed | **OPEN** |
| Current↔historical AOV parity proof | **OPEN** |
| A1 admission | **BLOCKED** |
| A2 admission | **BLOCKED** |

Until the open rows close, any Lane-2 capture/prototype work is **instrumentation only** and creates no A1/A2 economic authority.
