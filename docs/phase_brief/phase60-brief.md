# Phase 60: Stable Shadow Portfolio

Current Governance State: Phase 59 is closed under `D-330` as evidence-only / no-promotion / no-widening with the bounded Shadow Portfolio surface preserved. `D-331` now opens Phase 60 in planning-only mode to lock the Stable Shadow Portfolio contracts before any implementation or post-2022 audit execution is considered.

**Status**: PLANNING-ONLY (D-331 kickoff; implementation blocked)
**Created**: 2026-03-18
**Authority**: `D-332` | `D-331` | `D-330` | `D-329` | `D-328` | `D-327` | `D-326` | `D-325` | `D-324` | `D-323` | `D-322` | `D-321` | `D-320` | `D-319` | `D-318` | `D-317` | `D-316` | `D-315` | `D-314` | `D-313` | `D-312` | `D-311` | `D-309` | `D-292` | `D-284`
**Execution Authorization**: None. `D-331` is planning-only; any Phase 60 implementation, post-2022 audit execution, or promotion path remains blocked until a later explicit packet consumes the exact token `approve next phase`.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Multi-Sleeve Research Kernel + Governance Stack
- **L2 Active Streams**: Docs/Ops | Backend | Data
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Docs/Ops
- **Active Stage Level**: L3
- **Current Stage**: Planning (`D-331` kickoff published; implementation blocked)
- **Planning Gate Boundary**: In = docs-only Phase 60 planning artifacts that lock the unified comparator surface, governed cost basis, one-shot post-2022 audit spec, allocator eligibility gate, bridge packet, and context refresh. Out = any code change, new evidence generation, post-2022 run, stable shadow execution, production promotion, `research_data/` mutation, or kernel reopen.
- **Owner/Handoff**: Codex docs planner -> PM/Architecture review -> later explicit implementation approval
- **Acceptance Checks**: `CHK-P60-01`..`CHK-P60-09`
- **Primary Next Scope**: Review the bounded Phase 60 planning brief, keep implementation blocked, and require a later explicit `approve next phase` token before any code or holdout run starts [92/100: given repo constraints]

## 0.5 Complete Institutional Pivot (Planning Snapshot - D-332)

**Critical Mission**: Restore validator PASS before opening any new sidecar testing or data-milestone execution path.

**Next Data Milestone**: Complete Institutional Pivot on the already-in-place PIT-clean CRSP/Compustat 2000-2024 bedrock with zero from-scratch replacement required.

**Operational Validator Failures (Must Clear Immediately)**:
- 14-day feature freshness gap
- 2 zombie snapshot rows

**S&P 500 Pro / Moody's B&D Designation Resolution (92/100 Confidence)**:
- **Preferred Method B**: Isolated Parquet sidecars joined only at view level (exactly like Osiris)
- **Rationale**: Protects the governed core updater schema and enables parallel deep-credit/factor testing
- **No expert delegation required**: Method B is the right planning default with no low-certainty gaps remaining

**Hybrid Institutional Lake Status**:
- CRSP/Compustat: PIT-clean 2000-2024 bedrock (governed core)
- Osiris: Isolated Parquet sidecar (view-layer join only)
- S&P 500 Pro / Moody's B&D: Method B preferred (isolated Parquet sidecars, view-layer join)
- Yahoo sidecars: Remain separate from institutional lake

**Out-of-Boundary Block (100/100 Confidence)**:
- Ingestion keys/schema mappings that violate the governed core updater schema are flagged and blocked from any execution
- No false-premise milestone may be opened

**Phase 60 Planning Deliverables**:
1. Validator fix (14-day freshness gap + 2 zombie snapshot rows) - Priority #1
2. Method B preference locked for S&P/Moody's sidecars
3. Out-of-boundary ingestion block enforced

**Locked Constraints**:
- D-284 through D-331 remain immutable
- RESEARCH_MAX_DATE = 2022-12-31 remains in force
- No code/evidence/execution surface changes during planning
- Prior SSOT artifacts remain unchanged

## 1. Problem Statement
- **Context**: Phase 60 is the roadmap step that would run a multi-sleeve plus allocator book as a paper-only stable shadow stack and execute a one-shot post-2022 audit on all gates. The repo does not yet expose a truthful unified governed holdings / weights surface for that work, and the existing upstream inputs remain mixed: PEAD is the only positive event sleeve signal, the core sleeve remains a non-promotion planning input, the allocator-selected variant remains negative on Sharpe / CAGR, and the Phase 59 shadow alert was `RED` because the compared surfaces were materially disjoint.
- **User Impact**: Without a planning-only contract lock, any future Stable Shadow implementation would risk inventing comparability, drifting cost assumptions, or breaching the post-2022 seal without agreed audit kill switches.

## 2. Goals & Non-Goals
- **Goal**: Lock the truthful unified comparator surface for any future Stable Shadow work.
- **Goal**: Freeze one governed cost policy for comparator use and one sensitivity policy for stress testing.
- **Goal**: Define the one-shot post-2022 audit preflight checks, gate family, and kill switches before any holdout run is authorized.
- **Goal**: Keep PEAD, core sleeve, and allocator statuses explicit so no failed planning input is silently promoted into the governed book.
- **Non-Goal**: No code changes, no new evidence generation, no post-2022 execution, no stable shadow paper-book launch, no loader/kernel reopen, no `research_data/` mutation, and no production promotion.

## 3. Phase Boundary Checklist
- **Phase 59 close lock**: `D-330` remains authoritative; Phase 59 is closed and immutable.
- **Phase 60 kickoff**: `D-331` opens the Stable Shadow Portfolio surface in planning-only mode.
- **Execution predicate**: `phase60_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`.
- **NextPhaseApproval**: `PENDING`.
- **Context predicate**: `active_phase = 60` becomes the planning SSOT label after `D-331` publishes and the context packet is refreshed.
- **Holdout predicate**: `post_2022_execution_authorized = 0` until a future explicit implementation packet consumes the exact approval token.
- **Variant-budget precedence**: `global_active_variants <= 18` remains the default governance ceiling unless a later implementation packet narrows it explicitly.

## 4. Codebase Walk-Through and Reusable Hooks

### 4.1 Existing Hooks
- `data/processed/phase56_pead_summary.json`
- `data/processed/phase58_governance_summary.json`
- `data/processed/phase59_shadow_summary.json`
- `data/processed/phase54_core_sleeve_summary.json`
- `data/processed/phase55_allocator_cpcv_evidence.json`
- `core/engine.py`
- `utils/statistics.py`
- `utils/spa.py`
- `docs/context/bridge_contract_current.md`

### 4.2 Locked Phase 53 Roadmap Evidence
- `- **Phase 60 - Stable Shadow Portfolio**: run the multi-sleeve + allocator book as a paper-only shadow stack and execute the one-shot post-2022 audit on all gates.`

## 5. Planning Guardrails (Locked)
- **Prior-phase SSOT preserved**: `D-330`, `D-326`, `D-322`, `D-317`, `D-312`, and the Phase 53 kernel under `D-292` remain immutable.
- **Holdout quarantine**: `RESEARCH_MAX_DATE = 2022-12-31` remains in force during planning; no post-2022 run is authorized in this round.
- **Same-engine discipline**: any future governed comparator evidence must keep the same-window / same-cost / same-`core.engine.run_simulation` path where comparator claims are made.
- **No invented comparability**: `phase50_shadow_ship` remains `reference_only` and cannot fill governed comparator fields in Phase 60.
- **Promotion block**: PEAD is the only sleeve with a positive pre-2023 governed signal, but Phase 60 planning does not promote PEAD, the core sleeve, or the allocator.
- **Core sleeve status lock**: Phase 54 remains `ABORT_PIVOT` with `gates_passed = 4/6`, `rule100_pass_controller = false`, and `rule100_pass_rate = 0.10132320319432121`; it is a planning input only.
- **Allocator status lock**: the currently selected allocator variant remains `v_3516a4bd6b65` with negative Sharpe / CAGR on the bounded research packet; allocator carry-forward is planning-only and blocked from governed use until eligibility clears.

## 6. Phase 60 Planning Contracts (Locked by D-331)

### 6.1 Contract A: Unified Comparator Surface = Option B
- **Decision**: adopt a governed daily holdings / weights cube built from sleeves plus allocator surfaces.
- **Purpose**: replace the disjoint Phase 50 vs Phase 54 reference comparison with one truthful governed comparator surface.
- **Planned cube fields**:
  - `date`
  - `book_id`
  - `sleeve_id`
  - `permno`
  - `ticker`
  - `eligibility_state`
  - `sleeve_weight_pre_allocator`
  - `allocator_overlay_weight`
  - `book_weight_final`
  - `gross_exposure`
  - `turnover_component`
  - `source_artifact`
- **Weight semantics**:
  - `book_pre_allocator_weight_{i,t} = sum_s(sleeve_weight_pre_allocator_{s,i,t})`
  - `book_weight_final_{i,t} = book_pre_allocator_weight_{i,t} + allocator_overlay_weight_{i,t}`
- **Governed comparator rule**: if allocator eligibility remains blocked, `allocator_overlay_weight_{i,t}` may exist in the planning cube but it cannot contribute to governed comparator or promotion claims.
- **Legacy reference rule**: `phase50_shadow_ship` artifacts remain `reference_only` and may not be used to backfill governed holdings, exposure, or turnover metrics.

### 6.2 Contract B: Governed Cost Policy = Option C
- **Decision**: freeze `5.0` bps as the gating comparator basis and require `10.0` bps as mandatory sensitivity-only evidence.
- **Comparator rule**: any future Phase 60 governed claim must first clear the same-window / same-cost / same-engine gate at `5.0` bps for continuity with Phases 54-59.
- **Sensitivity rule**: `10.0` bps must be reported as a separate sensitivity lane and is non-gating unless a later explicit packet changes the comparator basis.
- **No ambiguity rule**: Phase 60 may not mix `5.0` and `10.0` bps inside the same governed acceptance decision.

### 6.3 Contract C: One-Shot Post-2022 Audit = Option A
- **Decision**: define exactly one integrated post-2022 audit, not sleeve-by-sleeve staggered execution.
- **Audit window**:
  - start: `2023-01-01`
  - end: future approved `max_date`
- **Mandatory preflight checks**:
  - `PF-01`: `D-284`..`D-331` and `RESEARCH_MAX_DATE = 2022-12-31` remain unchanged and cited as the frozen pre-audit baseline.
  - `PF-02`: the unified governed daily cube exists and publishes holdings, gross exposure, and turnover fields without using `phase50_shadow_ship` as governed fill.
  - `PF-03`: the governed cost basis is frozen at `5.0` bps with a separate `10.0` bps sensitivity lane.
  - `PF-04`: the full audit gate list and thresholds are frozen before the holdout run starts.
  - `PF-05`: no artifact in `research_data/` or prior SSOT evidence surfaces will be mutated by the audit path.
  - `PF-06`: rollback scope and atomic output paths are documented before execution.
- **Integrated audit gates**:
  - `GATE-01`: family-level event governance remains `SPA_p < 0.05` and `WRC_p < 0.05`.
  - `GATE-02`: PEAD holdout evidence must stay on the same-period C3 comparator surface and may not claim promotion if Sharpe or CAGR delta is negative.
  - `GATE-03`: the core sleeve remains blocked from stable-shadow promotion unless its existing gate family is explicitly re-cleared in a future approved packet.
  - `GATE-04`: allocator eligibility remains `PBO < 0.05`, `DSR > 0.95`, `positive_outer_fold_share >= 0.60`, and `SPA_p < 0.05`.
  - `GATE-05`: the unified cube must publish non-empty governed holdings overlap, gross exposure, and turnover metrics from the same governed surface.
- **Kill switches**:
  - `KS-01`: stop immediately if the audit path requires `phase50_shadow_ship` to populate governed comparator fields.
  - `KS-02`: stop immediately if any post-2022 run attempts to mutate `research_data/` or prior SSOT artifacts.
  - `KS-03`: stop immediately if the gate list, thresholds, or cost basis drift after audit start.
  - `KS-04`: stop immediately if the unified cube cannot publish holdings, exposure, and turnover from the same governed surface.
  - `KS-05`: stop immediately if allocator or core-sleeve weight is silently promoted into the governed book while eligibility remains blocked.

### 6.4 Contract D: Allocator Carry-Forward = Option C
- **Decision**: exclude allocator carry-forward from the governed book until research eligibility clears.
- **Eligibility formula**:
  - `allocator_eligible = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
- **Current status**: blocked. The bounded allocator-selected variant `v_3516a4bd6b65` remains negative on Sharpe / CAGR and does not clear governed carry-forward eligibility.
- **Planning implication**: the planning cube may reserve allocator fields and zero / quarantine the overlay lane, but no governed capital may be assigned through allocator carry-forward until a later approved packet proves eligibility.

## 7. Acceptance Criteria (Phase 60 Planning-Only Kickoff - Active)
- [x] `CHK-P60-01`: Phase 60 boundary documented with inherited locks from `D-330`, `D-326`, `D-322`, `D-317`, `D-312`, and `D-292`.
- [x] `CHK-P60-02`: The Phase 53 roadmap bullet for Phase 60 is recorded verbatim in the active brief.
- [x] `CHK-P60-03`: `D-331` logs Phase 60 as planning-only and keeps implementation / post-2022 execution blocked.
- [x] `CHK-P60-04`: The unified comparator surface contract is locked to the governed daily holdings / weights cube.
- [x] `CHK-P60-05`: The governed cost policy is locked to `5.0` bps gate + `10.0` bps sensitivity-only evidence.
- [x] `CHK-P60-06`: The one-shot post-2022 integrated audit spec includes mandatory preflight checks and kill switches.
- [x] `CHK-P60-07`: Allocator carry-forward is explicitly excluded from governed use until research eligibility clears.
- [x] `CHK-P60-08`: `docs/handover/phase60_kickoff_memo_20260318.md` and `docs/context/bridge_contract_current.md` are published in the same round.
- [ ] `CHK-P60-09`: A later explicit implementation packet consumes the exact token `approve next phase` before any code or holdout run starts.

## 8. Rollback Plan
- **Trigger**: Any Phase 60 planning packet that implies implementation authority, reinterprets legacy reference artifacts as governed comparator truth, or weakens the `RESEARCH_MAX_DATE = 2022-12-31` quarantine without a separate explicit execution packet.
- **Action**: Revert Phase 60 planning docs/context/SAW edits only. Do not alter `D-330`, prior SSOT artifacts, or the Phase 53 kernel.

## 9. New Context Packet (Phase 60 Planning-Only)

## What Was Done
- Published `D-331` to open Phase 60 in planning-only mode for the Stable Shadow Portfolio roadmap step.
- Locked the four Phase 60 planning contracts in `docs/phase_brief/phase60-brief.md`: unified governed comparator surface, governed cost policy, one-shot post-2022 audit spec, and allocator carry-forward eligibility.
- Published the PM-facing kickoff memo and refreshed the planner bridge to the Phase 60 planning-only state.

## What Is Locked
- `D-284`, `D-292`, `D-309`, `D-311`, `D-312`, `D-313`, `D-314`, `D-315`, `D-316`, `D-317`, `D-318`, `D-319`, `D-320`, `D-321`, `D-322`, `D-323`, `D-324`, `D-325`, `D-326`, `D-327`, `D-328`, `D-329`, `D-330`, `D-331`, `RESEARCH_MAX_DATE = 2022-12-31`, `global_active_variants <= 18`, and the same-window / same-cost / same-`core.engine.run_simulation` evidence gate.
- Prior sleeve and shadow SSOT artifacts remain immutable; `phase50_shadow_ship` remains `reference_only`.
- Phase 60 is planning-only; no implementation, no post-2022 execution, and no promotion without a later explicit approval packet.

## What Is Next
- Review the bounded Phase 60 planning brief and keep implementation blocked.
- Stand by for a separate explicit `approve next phase` token before any code change or post-2022 audit execution.
- Preserve the four locked contracts as the only valid inputs for any later Phase 60 implementation packet.

## First Command
Await explicit approve next phase token before any Phase 60 implementation or post-2022 audit execution.
