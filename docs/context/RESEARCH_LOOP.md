# RESEARCH LOOP — Self-ID Surface

**Read this + JSON first when asked “which phase / what’s next.”**

| File | Role |
|---|---|
| `docs/context/research_loop_state_current.json` | **Canonical machine state** (phase, next, tracks, forbid) |
| `docs/architecture/alpha_scientific_method_v1.md` | Locked process constitution |
| `docs/context/ACTIVE_BRIEF` | Product/shadow one-pager |
| `scripts/print_research_loop_state.py` | CLI print |

---

## Loop phases (short)

```text
L0 QUESTION → L1 CAUSAL → L2 OBSERVATION → L3 REP/SNR GATE
→ L4 EMPIRICAL FREEZE → E7.5 RDV / OWNER L5 GATE → L5 RUN → L6 LAYERED DIAGNOSIS
→ L7 ROADMAP DECISION → L8 BOUNDED REFINE → (L9 re-qualify) → L10 REFREEZE → L4 → E7.5 GATE → L5…

After lockbox: P1 RUN → P2 MATURE → P3 EVALUATE → P4 PROMOTE|KILL
```

**Forward-gate lock (2026-08-12):** phase completion never self-authorizes the next expensive phase. `L4 → READY_FOR_L5_CANDIDATE`, then cross-family ordinal RDV allocation; `READY_BUT_NOT_PRIORITY` is legal. Before material work, preregister `DECISION_TO_CHANGE` plus PASS/FAIL/UNRESOLVED routes; identical routes mean `DO_NOT_RUN`.

Method amendment=`docs/architecture/result_first_ai_research_loop_v1.md`; machine preflight=`docs/architecture/opportunity_kernel_scientific_preflight_v2.json`.

**Every empirical RUN:** diagnose D1→D9 in order; route failure to **one** layer only.

---

## Current snapshot (maintain JSON as SoT)

Open `research_loop_state_current.json` for live values. As of the 2026-08-12 method lock:

```text
process.loop_phase     = L7_STOP_STAMPED
process.next_phase     = PARALLEL_FAMILY_OR_PARK
product                = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
financial_alpha        = 0
FTK                     = STOPPED; D6_SELECTION failure banked; no FTK rescue
TR-v0                   = HOLD_SOURCE / PARKED
next_worker_slice      = PARALLEL_FAMILY_WIP
recommended            = CRV1_OR_SECTOR_ISOLATED_OR_IDLE
method                  = RESULT_FIRST_AI_RESEARCH_LOOP_v1 / FORWARD_ONLY
L4→L5                   = candidate only; no automatic authorization
RDV                     = ordinal LOW/MED/HIGH; not Alpha evidence
```

---

## Agent protocol

```text
WHEN user asks phase / next / loop position:
  1. Read research_loop_state_current.json
  2. Answer ONLY from that file (+ ACTIVE_BRIEF if product detail needed)
  3. If JSON conflicts with chat, JSON wins until owner updates JSON
  4. After any freeze/run/decision, UPDATE the JSON in the same turn
```

---

## Update rules (who may change what)

| Field | When to update |
|---|---|
| `process.loop_phase` | After each L* or P* transition |
| `active_tracks[]` | Track status change |
| `next_worker_slice` | After L7 decision |
| `last_empirical_diagnosis` | After every L6 |
| `forbidden_now` / `allowed_now` | When gates change |

Do not invent phase by reading only planner essays.
