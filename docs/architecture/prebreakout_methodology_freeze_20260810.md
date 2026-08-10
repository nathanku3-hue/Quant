# Methodology Freeze — Pre-Breakout Discovery Stack / Evidence Contract

**Date:** 2026-08-10
**Decision owner:** CEO (this record)
**Board status:** `5/5 GO on methodology; 5/5 NO-GO on today's capture`
**Meeting verdict:** `PASS — METHODOLOGY_FROZEN / CAPTURE_CLOCK_HELD`
**Runtime effect:** `NONE BY THIS DOCUMENT ALONE` — freezes research law and forbids today's capture/evaluation actions; implementation still requires contracts, tests, and custody receipts
**financial_alpha_evidence:** `0` (unchanged)
**Strategy live capital:** `CLOSED` (unchanged)
**Clock #1 / Parent / Child:** `UNCHANGED / NO MUTATION AUTHORITY FROM THIS DECISION`
**VSB M0 tape:** `RETAINED AS CONFIRMATION BENCHMARK ONLY — NOT PRE-BREAKOUT AUTHORITY`
**A2 re-query:** `FORBIDDEN`
**Capital / broker / PAPER alpha authority:** `NONE FROM THIS DECISION`

**Related authority (retained, not reopened):**
- `docs/architecture/aov_strategic_direction_lock_20260809.md`
- `docs/architecture/aov_endgame_generalization_spec_current.md`
- `docs/architecture/vol_squeeze_breakout_v1_spec.md`
- `docs/architecture/cycle_resonance_v1_build_spec.md` (evaluation metric constitution)
- `docs/architecture/winner_capture_diagnostic_v0.md` (diagnostic-only A1/A2 forensics)

---

## 0. Executive decision

### 0.1 Disposition

```text
METHODOLOGY          = FREEZE / GO
TODAY'S CAPTURE      = NO-GO
NEW FORWARD CLOCK    = DO NOT START until evidence contract answers the right question
RESEARCH STACK       = ADOPTED (below)
SECTOR ROTATION      = ORTHOGONAL PARALLEL LADDER (does not delay stock-winner path)
CAPITAL / ALPHA AUTH = UNCHANGED / ZERO
```

### 0.2 One-line ruling

> **Freeze the methodology before collecting new forward observations. Prove, on full PIT universes, who was identifiable before the payoff, how early, how often, with how many false winners, and how much of the eventual right tail could have been owned—then let prospective time, not another backtest optimization loop, decide promotion.**

### 0.3 Why this is the decision (not another search loop)

Historical A2 already shows the economic problem: winner recall is only modestly above breadth, while a few winners dominate Parent→Child return give-up. The endgame constitution states primary evaluation is **right-tail / incremental**, not standalone CAGR/Sharpe.

Therefore:

1. A frozen breakout-confirmation trigger cannot answer “find SNDK/MU-style names **before** breakout.”
2. Starting another capture clock today would burn lockbox / prospective time on the wrong question.
3. The correct next act is a methodology freeze + evidence-contract recut, not provider capture, prediction append, A2 re-query, Parent/Child mutation, or capital action.

---

## 1. Stakeholder votes (recorded)

| Seat | Vote | Binding constraint |
|---|---|---|
| Board (5/5) | GO methodology / NO-GO today capture | Programme authority |
| CEO | GO freeze; hold clock | No new clock until evidence contract answers the right question |
| CRO / Risk | GO freeze | Preserve PIT, lockbox, search-budget, no-rescue |
| Quant | GO stack split | Split pre-breakout discovery from breakout confirmation |
| Alpha Manager | GO stack split | VSB M0 is confirmation benchmark only; pre-breakout needs separately preregistered component/version |

No dissenting seat remains open on this decision.

---

## 2. Frozen research stack

### 2.1 Stock-winner path (ordered)

```text
PREBREAKOUT_DISCOVERY_v1
        ↓ (early-warning / pre-payoff identification)
VSB_CONFIRMATION_v1          (= retained VOL_SQUEEZE_BREAKOUT_v1 M0 role)
        ↓ (optional, only after confirmation economics are honest)
CONTINUATION_HOLD_v1
```

### 2.2 Orthogonal parallel path

```text
SECTOR_ROTATION_ALPHA_v1
  - independent family / risk set / search budget / prediction ledger
  - ETF universe ladder
  - MUST NOT delay the stock-winner path
  - MUST NOT share mutable outcome authority with stock components
```

### 2.3 Component identity law

These are **separate Alpha Components / Implementations**, not one rescuable model:

| Component | Economic question | May use VSB M0 breakout>0? |
|---|---|---|
| `PREBREAKOUT_DISCOVERY_v1` | Was the name identifiable **≥1 full session before** algorithmically defined breakout? | **No** as pass criterion |
| `VSB_CONFIRMATION_v1` | Conditional on breakout/vol-squeeze mechanics, is right-tail recall lift >1 prospectively? | **Yes** (frozen M0 trigger retained) |
| `CONTINUATION_HOLD_v1` | After legitimate entry, does hold/exit capture continuation vs premature exit? | Separate preregistration |
| Sector Rotation | Cross-sector ETF relative strength / rotation economics | Independent |

Any material merge of pre-breakout into VSB M0 after seeing outcomes is a **no-rescue violation** and requires a new charged version/family, not an in-place repair.

---

## 3. Evidence contract freeze (primary question)

### 3.1 Right question (primary)

```text
On a full date-local PIT risk set, before outcome labels open:

Who was identifiable before the payoff?
How early?
How often?
With how many false winners at that detection threshold?
How much of the eventual right-tail wealth could actually have been owned
  under fixed policy, realistic costs/capacity, and wrong-winner stress?
What is I vs I+X incremental value of the component?
```

### 3.2 Wrong questions (non-primary; may be diagnostic only)

```text
Standalone CAGR / Sharpe / MDD of a single sleeve
Famous-winner-only backtests
Hindsight-tuned thresholds on SNDK/MU
Re-optimizing VSB M0 breakout>0 to “catch” pre-breakout names
Rescue of failed trials by silent horizon/universe/feature mutation
```

### 3.3 Primary metrics (binding)

Primary evaluation is right-tail and incremental:

```text
Precision@K / Recall@K / Lift@K
PR-AUC / Average Precision
False winners
Missed winners
Catastrophic false winners
Time-to-First-Legitimate-Detection (TTFLD)
Continuation / exit capture
Right-tail wealth capture
Capital-weighted right-tail capture (shadow)
I vs I+X incremental net utility
```

Secondary only:

```text
CAGR, Sharpe, MDD, ROC-AUC, generic hit rate, feature importance
```

### 3.4 VSB confirmation gate (retained, not reassigned)

For `VSB_CONFIRMATION_v1` / frozen `VOL_SQUEEZE_BREAKOUT_v1` M0:

```text
>= 20 matured primary 10d decision dates
winner_recall_lift_10d > 1.0
80% moving-block-bootstrap lower bound of lift_10d > 1.0
(block_length=10, replicates=10000, seed=20260810)
```

This gate **cannot** satisfy the pre-breakout question. It remains the confirmation benchmark only.

### 3.5 Pre-breakout additional gate (new component)

For `PREBREAKOUT_DISCOVERY_v1`, after separate preregistration and freeze:

```text
Prospective / untouched evaluation must show positive ex-ante detection lead
across future winner episodes (not only historical smoke cases).

Lead definition (engineering minimum for smoke; statistical gate is full-census):
  algorithmically defined breakout date B
  legitimate flag required at decision cut of session B-1 or earlier
  if eligible name not flagged pre-breakout → deterministic PIT exclusion / miss logged
  no post-breakout rescue counted as early detection
```

Exact windows, score thresholds, falsifiers, and search budget for PREBREAKOUT are **not** invented in this freeze; they must be preregistered before any result-bearing evaluation.

---

## 4. SNDK / MU law (hard)

```text
ROLE              = engineering smoke cases for early-warning component
STATISTICAL WEIGHT= 0 in promotion / acceptance denominators
SPECIAL BRANCHING = FORBIDDEN (no ticker-literal code paths)
PASS/FAIL TARGET  = FORBIDDEN as family acceptance criterion
```

Using algorithmically defined breakout dates:

```text
IF name is PIT-eligible at B-1:
  MUST be flagged by PREBREAKOUT component at least one full session before breakout
  OR system emits deterministic PIT exclusion reason
ELSE:
  deterministic exclusion / unavailable — not a silent miss and not a free pass
```

Purpose: prove the pipeline can emit pre-breakout state honestly.
Non-purpose: build a two-name hindsight machine.

Historical AOV facts (e.g., MU technical eligibility failures; SNDK Rule100 feature-date gaps) remain **diagnostic-only**.

---

## 5. Custody / risk constitution (non-negotiable)

CRO/Risk constraints are constitutional for all components in this stack:

```text
PIT timing / knowledge-cutoff law
exact listing identity (CIQSEC + trading-item; no ticker/entity/PERMNO fallback)
date-local risk set (no survivor back-projection)
immutable Prediction Ledger
Trial Ledger / search-budget honesty
untouched lockbox before label open
no-rescue after prospective/lockbox start
no A2 re-query
no Parent/Child mutation from discovery diagnostics
no capital authority from this freeze
```

Break obsolete software authority if needed. **Do not** break scientific custody or risk authority for speed.

---

## 6. Full pre-production ladder (frozen order)

Applies independently to the stock-winner path. Sector Rotation runs the same ladder on the ETF universe without blocking stock work.

```text
(1) Data / PIT authority
    date-local CIQSEC risk set
    exact listing identity
    availability timestamps
    corporate-action truth
    no survivor / ticker fallback

(2) Discovery backtest / Atlas
    full cross-sectional right-tail census (not famous winners only)
    enumerate true winners, false winners, missed winners, matched controls
    diagnose SNDK/MU and all other episodes as zero-weight smoke/forensics

(3) Development walk-forward
    small preregistered search budget
    rolling/expanding training
    ~4 temporal OOS folds where legitimate
    cross-sectional holdout where feasible
    optimize mechanism evidence, not Sharpe

(4) Freeze
    universe, primary/secondary horizons, transforms, thresholds, model,
    falsifiers, costs, bootstrap/inference, code/data hashes, Trial Ledger

(5) Untouched historical lockbox
    predictions written before labels open
    at least one untouched period
    evaluate Recall/Lift@K, Precision@K, PR-AUC,
    false/missed/catastrophic winners, lead time,
    regime/effective-episode robustness, I vs I+X
    CAGR/Sharpe/MDD secondary

(6) Prospective forward test
    immutable daily/weekly predictions
    absolutely no refit/rescue
    VSB-confirmation: retain frozen ≥20 matured 10d dates,
      lift>1 and 80% block-bootstrap LB>1
    PREBREAKOUT: additionally require positive ex-ante detection lead
      across future winner episodes

(7) Shadow economics
    fixed-policy shadow weights
    capital-weighted right-tail capture
    clipping, realistic cost/capacity, wrong-winner stress

(8) PAPER-0
    broker capturability / reconciliation only
    still zero alpha authority

(9) Independent future replication
    quarantined source / time / provider replication

(10) Production gate
     only after:
       prospective edge
       + independent replication
       + PAPER capturability
       + CRO / owner approval
```

No stage may be skipped by renaming a backtest “prospective.”

---

## 7. Explicit NO-GO list for today (2026-08-10)

The following are **forbidden by this decision** until the PREBREAKOUT evidence contract is preregistered and the methodology freeze is operationally acknowledged in the active worktree:

```text
NO provider capture for a new pre-breakout or VSB “rescue” clock
NO prediction append intended to start pre-breakout prospective time
NO A2 query / re-query
NO Parent / Child change
NO Clock #1 outcome open or mutation
NO capital action / live or paper alpha authority expansion
NO silent threshold/window retune of VSB M0 to catch SNDK/MU pre-breakout
NO promotion claim from discovery Atlas alone
```

### Allowed immediately (non-capture)

```text
Write / align preregistration contracts for PREBREAKOUT_DISCOVERY_v1
Atlas design against already-retained custody only
PIT identity / risk-set authority engineering (no new outcome evaluation)
Trial Ledger / search-budget schema for the new component
Sector Rotation preregistration work that does not consume stock lockbox
Documentation and test scaffolding with synthetic/fixture data
```

---

## 8. WIP / concurrency accounting

Under the strategic direction lock:

```text
Initial active Alpha-family WIP = 2
Ceiling = 3 until explicit WIP review
```

Current intent after this freeze:

```text
Clock A     CYCLE_RESONANCE_v1          (unchanged slow family)
Clock B     VSB_CONFIRMATION_v1         (retained M0 confirmation; already Family #2)
Component   PREBREAKOUT_DISCOVERY_v1    (new; requires own search budget + preregistration
                                         before any confirmatory/prospective clock starts)
Parallel    SECTOR_ROTATION_ALPHA_v1    (orthogonal; does not auto-consume stock lockbox)
Optional    CONTINUATION_HOLD_v1        (not opened until confirmation economics are honest)
```

PREBREAKOUT may share economic *theme* with VSB but **must not** share:
- mutable implementation authority
- search-budget ledger identity
- prediction-ledger identity
- outcome-open authority

If admitting PREBREAKOUT as a concurrent confirmatory clock would breach WIP ceiling or custody isolation, **hold the clock** and finish preregistration/contracts first. Methodology freeze does not itself admit a third running prospective clock.

---

## 9. Promotion constitution

```text
DISCOVERY ATLAS SUCCESS  ≠  EVIDENCE QUALIFICATION
EVIDENCE QUALIFICATION    ≠  PORTFOLIO USEFULNESS
PORTFOLIO USEFULNESS      ≠  CAPITAL AUTHORITY
```

Promotion to any capital-relevant state requires the full ladder through prospective edge, independent replication, PAPER capturability, and CRO/owner approval.

`financial_alpha_evidence` remains `0` until prospective law is satisfied. Historical A1/A2 and discovery Atlas never increment it.

---

## 10. Decision matrix (final)

| Question | Decision |
|---|---|
| Freeze methodology now? | **YES** |
| Start new capture / forward clock today? | **NO** |
| Keep VSB M0? | **YES — confirmation benchmark only** |
| Can VSB M0 answer pre-breakout? | **NO** |
| Adopt PREBREAKOUT → VSB → optional CONTINUATION stack? | **YES** |
| Sector Rotation blocks stock path? | **NO — parallel orthogonal** |
| SNDK/MU statistical weight? | **ZERO** |
| A2 / Parent-Child / capital today? | **FORBIDDEN** |
| Primary metrics? | **Right-tail / incremental (not CAGR/Sharpe)** |
| Fastest path to real alpha? | **Full-PIT pre-payoff identifiability + prospective time** |

---

## 11. Immediate next authorized work (priority order)

1. **Preregister `PREBREAKOUT_DISCOVERY_v1`**
   Mechanism, PIT inputs, algorithmic breakout definition, horizons, falsifiers, search budget, primary metrics, TTFLD law, zero-weight smoke policy for SNDK/MU.

2. **Bind Data/PIT authority checklist** for the stock-winner path (date-local CIQSEC, listing identity, availability timestamps, corporate-action truth).

3. **Design Discovery Atlas protocol** for full right-tail census + matched controls (discovery-only; no confirmatory authority).

4. **Leave VSB M0 frozen** as confirmation; do not retune; do not append capture for the purpose of answering the pre-breakout question.

5. **Continue Sector Rotation** only on its own ladder/custody.

6. **Reconvene for clock-start authorization** only when the PREBREAKOUT evidence contract is complete and CRO confirms lockbox / search-budget / no-rescue binding.

---

## 12. Stop conditions

Reject or stop rather than “repair”:

```text
Any attempt to start prospective time before PREBREAKOUT preregistration
Any A2 second query
Any Parent/Child mutation justified by Atlas forensics
Any ticker-special case for SNDK/MU
Any in-place VSB M0 mutation after outcome visibility
Any claim that discovery backtest lift is financial alpha
Any capital or PAPER alpha authority expansion from this memo
```

---

## 13. Final approval statement

> **Board 5/5 accepted. Methodology is frozen. Today's capture is NO-GO. VSB M0 remains a useful confirmation benchmark and cannot satisfy pre-breakout discovery. Adopt the ordered stack PREBREAKOUT_DISCOVERY_v1 → VSB_CONFIRMATION_v1 → optional CONTINUATION_HOLD_v1, with Sector Rotation orthogonal in parallel. Preserve PIT, lockbox, search-budget and no-rescue. Use SNDK/MU only as zero-weight engineering smoke. Do not open provider capture, prediction append, A2, Parent/Child, or capital until the evidence contract answers who was identifiable before the payoff—and prospective time, not another optimization loop, decides promotion.**

**Status after this record:**

```text
METHODOLOGY_FREEZE_20260810     = LOCKED
TODAY_CAPTURE                   = NO-GO
PREBREAKOUT_PREREGISTRATION     = AUTHORIZED (contracts only)
VSB_M0                          = RETAINED / CONFIRMATION ONLY
CONTINUATION_HOLD_v1            = OPTIONAL / NOT OPENED
SECTOR_ROTATION                 = PARALLEL / NON-BLOCKING
financial_alpha_evidence        = 0
STRATEGY_LIVE_CAPITAL           = CLOSED
```
