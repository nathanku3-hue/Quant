# Stream Handover Memo
## Roadmap Alignment Owner + Worker Dispatcher

**Date:** 2026-08-12  
**Roles of this memo:** (1) roadmap alignment owner — what is true / closed / forbidden; (2) worker dispatcher — who may run what next.  
**Authority lineage:** `codex/pit-source-authority-1`  
**Worktree:** `E:/Code/Quant/.worktrees/devspace-053ca7a4f582fb3e`  
**Public main:** `NON_AUTHORITY_UNTIL_MERGE`

---

## 0. Read order for the next operator / agent

```text
1. docs/context/research_loop_state_current.json     # phase/next SoT
2. python scripts/print_research_loop_state.py
3. docs/context/ACTIVE_BRIEF
4. this handover
5. only then planner/bridge/endgame essays
```

**JSON wins over chat.** Update the loop JSON when phase or dispatch changes.

---

## 1. Roadmap alignment — current truth

### 1.1 Product

```text
ACTIVE_PRODUCT_STATE     = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
CAPITAL_ALPHA_PATH       = CLOSED
FINANCIAL_ALPHA_EVIDENCE = 0
W6                       = UNTOUCHED
Parent/Child             = FROZEN (no retune)
```

**Must preserve:** Clock #1 custody, weekly tape, sealed outcomes until legitimate maturity.  
**Must not:** early outcome open, capital inference, fourth evidence clock.

### 1.2 Process constitution

```text
METHOD                   = ALPHA_SCIENTIFIC_METHOD_v1 (LOCKED)
LOOP_PHASE (program)     = L7_ROADMAP_DECISION
LAST_COMPLETED           = L4_EMPIRICAL_FREEZE (AO-FTK-0 pre-open)
NEXT_PHASE (program)     = L0_QUESTION for a NEW charged slice_id
                           OR parallel-only / stop stock-discovery
```

Loop: `L0→L1→L2→L3(rep/SNR)→L4→L5 RUN→L6 layered diagnose D1–D9→L7→…`  
After lockbox: `P1→P2→P3→P4` only (no adaptive redesign).

### 1.3 Stock-discovery tracks

| Track | Status | Alignment |
|---|---|---|
| **AO-K0A** | FROZEN preflight, no empirical result | Active **basis law** (full-W3, abstention, residual geometry). Do not erase. |
| **OK-SBI-0 / Q·M** | `Q_SOURCE_BLOCKED_TERMINAL` (commit `9dfe9e9`) | **Parked.** No S2, no invent Q, no 20-gate optics fill. Amendment unspent, reserved for future admit slice only. |
| **AO-FTK-0** | Pre-open `READY_FOR_LATER_CHARGED_DEVELOPMENT_READ` (commit `6832066`) | **Closed as freeze.** No worker. Charged L5 only under **new slice_id** + L3 rep/SNR + authorization. |
| **S0 M0/M1** | `NO_EXTRACTION_LIFT` (v2) | Last empirical diagnosis: mechanism fail / under-sensing; **not** selector problem. Do not open winner-selection shootout on same surface. |

### 1.4 Parallel families (do not merge into FTK/Q)

| Stream | Dispatch |
|---|---|
| CRV1 | Isolated research OK; own WIP |
| Sector Rotation | Isolated research OK; own WIP |
| VSB | **PARKED** — no worker until VSB matured 10d feed |
| PAPER-0 | Ops only; `alpha_evidence=0` |

### 1.5 Explicit supersessions (do not rehydrate)

```text
SUPERSEDED: "continue ordinary OK-SBI S0 Q bind"
SUPERSEDED: "GO_AFTER_PRECONDITIONS" as soft release
SUPERSEDED: "next = Q/M⊥/Q+M⊥ leaderboard"
SUPERSEDED: "fill 20 OK-SBI gates now"
SUPERSEDED: every slice returns CAGR or MU/SNDK pass/fail
LIVE:       Q_SOURCE_BLOCKED_TERMINAL under admitted S0+W3
LIVE:       FTK pre-open READY; charged read needs new slice_id
LIVE:       methodology constitution + loop JSON for self-ID
```

### 1.6 Endgame alignment (one line)

Maximize `EVIDENCE_VELOCITY × ECONOMIC_RELEVANCE`: parallel evidence clocks, **one** serialized capital authority, no forcing dead Q/M. First honest prospective edge may come from FTK (or other lawful kernel), not an AO-K0B trophy.

---

## 2. Worker dispatcher — authorization matrix

### 2.1 Owner action required before primary research worker

**Primary field is `OWNER_SELECT`.** Until owner picks, **do not** auto-dispatch a charged stock-discovery L5.

| Option | Slice | When to dispatch |
|---|---|---|
| **B (recommended)** | `AO-FTK-1` (or equivalent **new** slice_id) charged development prep/read | Default if no immediate lawful ROIC/Q custody |
| **A** | `OK-SBI-0-Q-CUSTODY-ADMIT-1` | Only if exact growth + capital-efficiency (or preregistered pair) + CIQSEC+trading_item admit is bounded and ready |
| **C** | `STOP_STOCK_DISCOVERY` / free WIP | If owner wants only Clock + CRV1 + Sector + PAPER |

**Do not dual-run A and B** without explicit dual WIP authorization.

### 2.2 Streams that may run **now** without new owner vote

| Worker stream | Prompt / contract | Allowed | Forbidden |
|---|---|---|---|
| **W-CLOCK** | Clock #1 custody | Preserve tape, sealed outcomes, reverify | Outcome open, Parent/Child mutate |
| **W-CRV1** | CRV1 family contracts | Isolated build/research under CRV1 law | Merge into FTK/Q; capital |
| **W-SECTOR** | Sector Rotation contracts | Isolated ETF-first work | Capital; block Clock/FTK custody |
| **W-PAPER** | `paper_0_authority.md` | Execution/capturability at alpha=0 | Alpha claims; strategy live |
| **W-HARNESS** | loop JSON / method / brief sync | Keep SoT consistent after decisions | Invent new product phases |

### 2.3 Streams **not** to staff

| Stream | Reason |
|---|---|
| OK-SBI S2 / composite trophy | Q terminal; S2 not authorized |
| OK-SBI 20-gate fill | Optics only until Q binds |
| AO-FTK-0 outcome open | Pre-open closed; need **new** slice_id |
| VSB engineering worker | Parked |
| W6 / capital / fourth clock | Forbidden |
| Q invent / Rule100 bridge | Forbidden |

### 2.4 If owner selects **B** — dispatch packet (FTK charged path)

```text
SLICE_ID:   AO-FTK-1-<date>   # MUST be new; not AO-FTK-0
ROLE:       SHADOW charged development prep → later L5 only if authorized
ENTRY:      L0_QUESTION under ALPHA_SCIENTIFIC_METHOD_v1
MANDATORY:  L3 Representation/SNR gate BEFORE expensive RUN
INPUTS:     AO-FTK-0 freeze bytes (6832066 lineage) + admitted S0/W3 only
INVARIANTS: full-W3, abstention, no Q/M terms, no W6, financial_alpha_evidence=0
DIAGNOSE:   after any RUN, D1→D9 layered; one failure route only
RETURN:     not CAGR/MU-SNDK by default — freeze/run receipt + layer diagnosis + info-gain
PROMPT SEED:
  docs/phase_brief/ao_ftk_0_transition_sparse_basis_worker_prompt_20260812.md
  (adapt: new slice_id; charged path; L3 gate; no re-freeze of closed AO-FTK-0 as open worker)
```

**Before L5 outcome join:** explicit authorization receipt (analogous to one-shot carve-out), sealed labels, `runnable_evaluation` law, PRODUCT preopen as policy requires.

### 2.5 If owner selects **A** — dispatch packet (Q custody admit)

```text
SLICE_ID:   OK-SBI-0-Q-CUSTODY-ADMIT-1
ROLE:       source admission only
OUTPUT:     Q_GF_BOUND | Q_AMENDED_BOUND | reaffirm Q_SOURCE_BLOCKED
AMENDMENT:  at most one outcome-blind cycle after lawful primitives exist
FORBIDDEN:  S2, leaderboard, invent ROIC, fill 20 gates, providers for cosmetics
```

### 2.6 Always-on dispatcher rules

```text
1. One primary stock-discovery worker max unless dual WIP authorized
2. Parallel family workers must not share outcome authority with FTK/Q
3. Scoped commits only — do not mix unrelated dirty tree into authority commits
4. After every freeze/run/decision: update research_loop_state_current.json
5. Public GitHub may lag local — dispatch on worktree authority, then push
6. SAW unavailable blocks candidate promotion, not mechanical pre-open research
```

---

## 3. Continuity five (paste into every worker brief)

```text
Result:     <what becomes true>
Journey:    <loop_phase from JSON>
Do now:     <single next action>
Done when:  <acceptance>
Stop only:  <outcome open / invent Q / capital / W6 / dual ungoverned tracks>
```

---

## 4. Evidence index (do not re-open for fun)

| Artifact | Path / id |
|---|---|
| Loop SoT | `docs/context/research_loop_state_current.json` |
| Method | `docs/architecture/alpha_scientific_method_v1.md` |
| ACTIVE_BRIEF | `docs/context/ACTIVE_BRIEF` |
| Q terminal | `9dfe9e9`, `docs/context/e2e_evidence/ok_sbi_0_q_source_bind_attempt_20260812.json` |
| Q/M park | `docs/context/e2e_evidence/qm_track_parked_terminal_20260812.json` |
| FTK freeze | `docs/architecture/ao_ftk_0_transition_sparse_basis_v1.*`, preopen `…/ao_ftk_0_preopen_freeze_20260812.json`, commit `6832066` |
| AO-K0A | `orthogonalization_contract_v1.md`, receipt `ao_k0a_orthogonal_basis_preflight_20260811.json` |
| S0 shootout v2 | `data/prebreakout/analysis/econphysics_s0_m0_m1_shootout_v2.json` |
| Harness pain points | `E:/Code/post_phase_reflection.md` (harness-only) |

---

## 5. Handover checklist (dispatcher out)

```text
[ ] Next human/agent can print loop state without chat
[ ] Owner selection A|B|C recorded (or explicitly PENDING)
[ ] No worker staffed on parked Q/M S2 or FTK-0 outcome open
[ ] Clock #1 still sealed; capital closed
[ ] Parallel CRV1/Sector/PAPER instructions isolated
[ ] Loop JSON updated after owner decision
[ ] Authority commits pushed if external workers will use GitHub
```

---

## 6. Owner decision needed (single)

```text
SELECT ONE:
  A = OK-SBI-0-Q-CUSTODY-ADMIT-1
  B = AO-FTK-1 (new slice_id) charged path   ← recommended default
  C = stop stock-discovery primary WIP

UNTIL SELECTED:
  dispatch only W-CLOCK / W-CRV1 / W-SECTOR / W-PAPER / W-HARNESS
```

---

## 7. One-line dispatch constitution

> **Align to loop JSON, not chat. Preserve Clock #1. Q/M is terminal under current custody. FTK is pre-open ready only. Staff parallel families freely; staff one stock-discovery primary only after owner A/B/C; never invent Q, open S2, or treat process hygiene as alpha.**

---

**Memo status:** `HANDOVER_ACTIVE`  
**Next memo trigger:** owner A/B/C selection **or** any L5/P3 transition **or** capital-path change.
