# Phase 55: Opportunity-Set Controller (Allocator Governance)

Current Governance State: Phase 54 is closed (Rule-of-100 sleeve rejected under D-309). Phase 55 execution is now authorized and moves to the allocator governance implementation stage under the locked Phase 53 research kernel surface.

**Status**: ACTIVE (Executing; D-310 closed)
**Created**: 2026-03-17
**Authority**: `D-311` (Phase 55 execution authorization) | `D-310` (Phase 55 kickoff, docs-only) | `D-309` (Phase 54 Rule-of-100 sleeve rejected; Phase 55 baseline excludes Rule-of-100) | `D-292` (Phase 53 closeout) | `D-284` (Phase 52 lock)
**Execution Authorization**: Approved on 2026-03-17 via the exact token predicate (recorded in-thread). Scope is limited to the Phase 55 allocator governance wrapper + SPA/WRC helper under the read-only Phase 53 research kernel.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Multi-Sleeve Research Kernel + Governance Stack
- **L2 Active Streams**: Backend | Data | Docs/Ops
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Backend
- **Active Stage Level**: L3
- **Current Stage**: Executing (D-310 closed; bounded wrapper implementation authorized)
- **Planning Gate Boundary**: Out = any code outside the locked Phase 53 research-kernel surface; no loader/kernel reopen, no Rule-of-100, no post-2022 expansion, no production promotion.
- **Owner/Handoff**: Codex implementer -> PM/CEO review
- **Acceptance Checks**: `CHK-P55-01`..`CHK-P55-08`
- **Primary Next Scope**: Implement allocator governance wrapper (`utils/spa.py` + `scripts/phase55_allocator_governance.py`) and publish first Phase 55 evidence artifacts under `data/processed/phase55_*` [82/100: given repo constraints]

## 1. Problem Statement
- **Context**: Phase 54 closed with a Rule-of-100 sleeve rejection (D-309). Phase 55 must establish allocator governance using nested CPCV + DSR/PBO/SPA so allocator rules are evaluated under the same rigorous evidence discipline as prior signal work, without touching the frozen Phase 53 kernel or post-2022 data.
- **User Impact**: Without a governed allocator controller, allocator-level decisions can silently overfit and reintroduce the instability that defeated prior sleeves. Phase 55 delivers a strict statistical gate before any allocator promotion.

## 2. Goals & Non-Goals
- **Goal**: Lock the allocator governance contract on the read-only Phase 53 research kernel and prevent scope drift.
- **Goal**: Publish docs-only Phase 55 kickoff artifacts (brief, D-310 record, kickoff memo, notes evidence, context refresh) without opening execution scope.
- **Goal**: Preserve same-window/same-cost/same-engine discipline and the Rule-of-100 exclusion under D-309.
- **Non-Goal**: No loader/kernel reopen, no Rule-of-100 reintroduction, no post-2022 leakage, no new data sources, and no allocator execution in Phase 55.

**Rationale (hypothesis)**: The expert-locked definitions in Section 4.1 are designed to prevent outer-fold leakage and gate drift while preserving the D-292 quarantine. Any performance or post-2022 claims remain out of scope for this docs-only kickoff.

## 3. Phase Boundary Checklist
- **Phase 52 close lock**: `D-284` remains the authority; Week 3 is the endpoint and Week 4 is not reopened here.
- **Phase 53 closeout**: `D-292` confirms the research-v0 data-kernel closeout; no Phase 53 execution is in scope.
- **Phase 55 execution**: blocked until explicit approval is recorded.
- **Execution predicate**: `phase55_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`.
- **NextPhaseApproval**: `PENDING` (must be explicitly updated).
- **Context predicate**: `active_phase = 55` is a context label only; it is not an execution token by itself.
- **Variant-budget precedence**: `global_active_variants <= 18` is the default governance ceiling; only an explicit execution packet may narrow or override it.

## 4. Codebase Walk-Through and Reusable Hooks

### 4.1 Expert-Locked Definitions (Canonical; verbatim)
- Canonical evidence input surface = read-only Phase 53 research kernel only: (i) allocator_state via research_data/catalog.duckdb / research_data/allocator_state_cube, and (ii) CPCV shard reads via allocator_cpcv.sql + scripts/run_allocator_cpcv.py over research_data/alloc_cpcv_splits, both hard-clamped to snapshot_date <= 2022-12-31. Phase 54 SSOT artifacts may be cited as comparator/governance references only
- Nested CPCV = each outer CPCV split is the sole source of final allocator evidence, while allocator ranking/selection is performed only inside an inner CPCV loop built from that outer-train partition. The selected allocator is then executed exactly once on the untouched outer-test fold
- WRC = WRC_p is a co-reported diagnostic and governance corroborator, not a new hard unlock clause in Phase 55. Publish WRC_p beside SPA_p in the evidence pack, but keep the hard gate unchanged as allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]
- Same-engine = same_window_same_cost_same_engine = 1[(all compared runs share identical start_date/end_date and end_date <= 2022-12-31) and (all compared runs share one fixed cost_bps) and (all governed return/equity series are produced by core.engine.run_simulation under D-04 shift(1) and D-05 turnover-tax semantics)]. Any result computed outside that path is diagnostic-only and non-gating.

### 4.2 Evidence (Verbatim; cite in comments + notes.md)
- `rule100_pass_rate = 0.024419920141969833`
- `docs/phase_brief/phase53-brief.md` Phase 55 roadmap bullet: `- **Phase 55 - Opportunity-Set Controller**: apply nested CPCV + DSR/PBO/SPA to allocator rules; reuse Phase 17 math; new allocator wrapper and SPA helper required.`
- `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
- `guard = f"snapshot_date <= DATE '{max_date}'"`

## 5. Execution Guardrails (Locked)
- **Rule-of-100 disabled**: D-309 rejects the Rule-of-100 sleeve; it must remain inactive for Phase 55 unless a new governance packet reopens it.
- **Holdout quarantine**: enforce `RESEARCH_MAX_DATE = 2022-12-31`; no post-2022 data in development windows.
- **Phase 53 kernel read-only**: no mutation or loader reopen; Phase 53 artifacts remain immutable under `D-292`.
- **Variant ceiling**: `global_active_variants <= 18` remains default unless explicitly overridden by a new packet.
- **Atomic writes**: any future Phase 55 artifacts must use atomic write/replace semantics.
- **Expert-locked definitions**: See Section 4.1 (canonical; no duplicate copies elsewhere).

## 6. Acceptance Criteria (Phase 55 Kickoff - Closed)
- [x] `CHK-P55-01`: Phase 55 boundary documented with explicit locks (D-284, D-292, D-309, max-date guard, Rule-of-100 disabled) and the canonical evidence input surface recorded verbatim in Section 4.1.
- [x] `CHK-P55-02`: Nested CPCV definition recorded verbatim in Section 4.1.
- [x] `CHK-P55-03`: WRC role and gate definition recorded verbatim in Section 4.1.
- [x] `CHK-P55-04`: Same-engine definition recorded verbatim in Section 4.1.
- [x] `CHK-P55-05`: Evidence citations recorded verbatim in brief + `docs/notes.md` (`rule100_pass_rate = 0.024419920141969833`, Phase 55 roadmap bullet in `docs/phase_brief/phase53-brief.md`, notes.md gate formula, `guard = f"snapshot_date <= DATE '{max_date}'"`).
- [x] `CHK-P55-06`: D-310 kickoff record logged; Phase 55 kickoff memo published.
- [x] `CHK-P55-07`: Context packet refreshed to planning-only state with execution still blocked; validation is required before any execution approval (`.venv\Scripts\python scripts/build_context_packet.py --validate`).
- [x] `CHK-P55-08`: Docs-only SAW acceptance recorded in `docs/saw_reports/saw_phase55_d310_kickoff_20260317.md` with `SAW Verdict: PASS`; no execution artifacts created.
- [x] `CHK-P55-09`: `docs/lessonss.md` updated in the same round as the D-310 docs-only closeout.

## 6B. Acceptance Criteria (Phase 55 Execution - Active)
- [ ] `CHK-P55-EXEC-01`: Implement `utils/spa.py` with SPA/WRC helpers; document formulas + code locations in `docs/notes.md`.
- [ ] `CHK-P55-EXEC-02`: Implement `scripts/phase55_allocator_governance.py` (nested CPCV wrapper) on the read-only Phase 53 research kernel surface.
- [ ] `CHK-P55-EXEC-03`: Enforce nested CPCV (inner selection on outer-train only; outer-test executed once) and log outer-fold evidence.
- [ ] `CHK-P55-EXEC-04`: Publish `data/processed/phase55_allocator_cpcv_summary.json` and `data/processed/phase55_dsr_pbo_spa_evidence.json` with atomic writes.
- [ ] `CHK-P55-EXEC-05`: Same-window/same-cost/same-engine parity documented; `snapshot_date <= 2022-12-31` enforced.
- [ ] `CHK-P55-EXEC-06`: First bounded run executed on strict path; SAW verdict recorded before any lattice promotion.

## 7. Acceptance Criteria (Docs-Only Kickoff - Closed)
- [x] `CHK-P55-PLAN-01`: Phase 55 brief published with the locked definitions and approval predicate.
- [x] `CHK-P55-PLAN-02`: Decision log records the D-310 kickoff (docs-only).
- [x] `CHK-P55-PLAN-03`: `docs/handover/phase55_kickoff_memo_20260317.md` published.
- [x] `CHK-P55-PLAN-04`: Context packet refreshed after kickoff docs update; execution remains blocked.

## 8. Rollback Plan
- **Trigger**: Any Phase 55 change that violates the holdout quarantine, same-window/same-cost evidence, or Phase 53 kernel lock.
- **Action**: Revert Phase 55 docs-only kickoff artifacts only. Do not alter the Phase 53 kernel or Phase 52 endpoint under `D-284`.

## 9. New Context Packet (Phase 55 Execution - Active)

## What Was Done
- Closed D-310 as a docs-only kickoff (PASS) and published `docs/saw_reports/saw_phase55_d310_kickoff_20260317.md`.
- Updated `docs/notes.md` + `docs/lessonss.md`, refreshed the kickoff memo, and aligned the Phase 55 brief to executing stage.
- Execution authorization granted; Phase 55 moves to allocator governance implementation under the read-only Phase 53 research kernel.

## What Is Locked
- `D-284`, `D-292`, `D-309`, `D-301`, `RESEARCH_MAX_DATE = 2022-12-31`, `global_active_variants <= 18`, and the same-window/same-cost/`core.engine.run_simulation` evidence gate.
- Canonical evidence input surface is the read-only Phase 53 research kernel only; Phase 54 SSOT artifacts are comparator/governance references only.
- Rule-of-100 sleeve remains disabled unless a new governance packet reopens it.

## What Is Next
- Implement allocator governance wrapper (`utils/spa.py` + `scripts/phase55_allocator_governance.py`) under the locked surface.
- Run the first bounded nested CPCV pass and publish `data/processed/phase55_allocator_cpcv_summary.json` + `data/processed/phase55_dsr_pbo_spa_evidence.json`.
- SAW verdict required before any lattice promotion.

## First Command
```text
Get-Content data\processed\phase55_allocator_cpcv_summary.json
```
