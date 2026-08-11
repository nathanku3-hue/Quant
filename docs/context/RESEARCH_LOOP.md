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
→ L4 EMPIRICAL FREEZE → L5 RUN → L6 LAYERED DIAGNOSIS
→ L7 ROADMAP DECISION → L8 BOUNDED REFINE → (L9 re-qualify) → L10 REFREEZE → L5…

After lockbox: P1 RUN → P2 MATURE → P3 EVALUATE → P4 PROMOTE|KILL
```

**Every empirical RUN:** diagnose D1→D9 in order; route failure to **one** layer only.

---

## Current snapshot (maintain JSON as SoT)

Open `research_loop_state_current.json` for live values. As of last lock:

```text
process.loop_phase     ≈ L4_EMPIRICAL_FREEZE (AO-FTK-1 L4 freeze PASS)
process.next_phase     ≈ WAIT_OWNER_L5 (authorize L5 | hold | stop; never silent L5)
product                = Clock #1 sealed, capital closed, alpha_evidence=0
OK-SBI Q/M             = Q_SOURCE_BLOCKED_TERMINAL (parked)
AO-FTK-0               = CLOSED pre-open READY / NO_WORKER
AO-FTK-1               = L4_FREEZE_PASS, effective_dof=2, trials_charged=0, labels_unjoined, L5=false
next_worker_slice      = AO-FTK-1-20260812 / recommended=L5_AUTHORIZE_SEPARATE
next                   = owner L5 authorization under binding L4 freeze
                         OR hold/stop OR Q custody admit OR parallel-only
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
