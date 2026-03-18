# Phase 59: Shadow Portfolio

Current Governance State: Phase 58 is closed under `D-326` as evidence-only / no-promotion / no-widening with the bounded Governance Layer surface preserved. `D-327` opened Phase 59 in planning-only mode, `D-328` consumed the exact execution token for one bounded Shadow Portfolio packet, and `D-329` now publishes the first bounded read-only Shadow NAV / alert surface while promotion and widening remain blocked.

**Status**: EXECUTING (D-328 execution authorization + D-329 first bounded packet; evidence-only / no promotion / no widening)
**Created**: 2026-03-18
**Authority**: `D-329` | `D-328` | `D-327` | `D-326` | `D-325` | `D-324` | `D-323` | `D-322` | `D-321` | `D-320` | `D-319` | `D-318` | `D-317` | `D-316` | `D-315` | `D-314` | `D-313` | `D-312` | `D-311` | `D-309` | `D-292` | `D-284`
**Execution Authorization**: `D-328` was approved on 2026-03-18 via the exact token `approve next phase` for the first bounded Phase 59 packet only. Promotion, widening, loader/kernel reopen, post-2022 expansion, and any non-Phase-59 execution remain blocked absent a separate explicit review packet.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Multi-Sleeve Research Kernel + Governance Stack
- **L2 Active Streams**: Docs/Ops | Backend | Frontend/UI | Data
- **L2 Deferred Streams**: none
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Backend
- **Active Stage Level**: L3
- **Current Stage**: Executing (`D-328` published; `D-329` bounded packet implemented and evidenced)
- **Planning Gate Boundary**: In = `data/phase59_shadow_portfolio.py`, `scripts/phase59_shadow_portfolio_runner.py`, `views/shadow_portfolio_view.py`, the bounded dashboard hook in `dashboard.py`, targeted tests, replay evidence, and same-round docs/context/SAW updates. Out = any mutation of the Phase 53 research kernel, any post-2022 execution, live-routing or production promotion, prior-phase widening, or any non-Phase-59 execution.
- **Owner/Handoff**: Codex implementation review -> PM/CEO bounded packet review
- **Acceptance Checks**: `CHK-P59-01`..`CHK-P59-08`, `CHK-P59-EXEC-01`..`CHK-P59-EXEC-09`
- **Primary Next Scope**: Review the first bounded packet as evidence-only / no-promotion / no-widening before any follow-up scope [95/100: given repo constraints]

## 1. Problem Statement
- **Context**: The Phase 53 roadmap reserved Phase 59 for a read-only Shadow NAV / alert surface built on the research-v0 kernel. The repo now needs the first bounded packet that ties the read-only `allocator_state` catalog to a dashboard-visible shadow monitor while carrying the historical Phase 50 shadow artifacts as explicit reference-only operational context.
- **User Impact**: Leadership can inspect one bounded Shadow Portfolio monitoring surface with persisted artifacts, comparator deltas, and alert metrics without reopening the research kernel or authorizing live execution.

## 2. Goals & Non-Goals
- **Goal**: Consume the exact approval token into a bounded Phase 59 execution authorization.
- **Goal**: Implement a read-only Shadow NAV / alert surface using `research_data/catalog.duckdb`, `allocator_state`, and historical `phase50_shadow_ship` artifacts only.
- **Goal**: Persist `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv`.
- **Goal**: Add a minimal dashboard reader that only consumes the bounded `phase59_*` artifacts.
- **Non-Goal**: No mutation of `research_data/`, no post-2022 evidence generation, no production promotion, no live-routing work, no widening of prior sleeves, and no stable shadow / multi-sleeve stack execution (Phase 60).

## 3. Phase Boundary Checklist
- **Phase 58 close lock**: `D-326` remains authoritative; Phase 58 is closed and immutable.
- **Phase 59 kickoff**: `D-327` opened Phase 59 in planning-only mode.
- **Phase 59 execution authorization**: `D-328` consumed the exact token and opened the first bounded packet only.
- **Phase 59 first packet**: `D-329` implements the read-only Shadow NAV / alert surface and keeps promotion blocked.
- **Execution predicate**: `phase59_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`.
- **NextPhaseApproval**: `APPROVED` was consumed by `D-328` for the first bounded packet only; any follow-up round still requires a new explicit review packet.
- **Context predicate**: `active_phase = 59` remains the current phase label while the bounded packet is active; this phase label is not a promotion grant by itself.
- **Variant-budget precedence**: `global_active_variants <= 18` remains the default governance ceiling unless a later execution packet narrows it explicitly.

## 4. Codebase Walk-Through and Reusable Hooks

### 4.1 Existing Hooks
- **Read-only research connector / allocator-state surface**:
  - `data/research_connector.py`
  - `research_data/catalog.duckdb`
  - `research_data/allocator_state_cube/allocator_state_manifest.json`
- **Historical shadow-ship artifact surface**:
  - `data/processed/phase50_shadow_ship/gate_recommendation.json`
  - `data/processed/phase50_shadow_ship/phase50_curve_full_20260410.csv`
  - `data/processed/phase50_shadow_ship/phase50_aggregated_telemetry_20260410.json`
  - `data/processed/phase50_shadow_ship/paper_curve_positions_day1.csv`
  - `data/processed/phase50_shadow_ship/paper_curve_positions_day30.csv`
- **Governance carry-forward surfaces**:
  - `data/processed/phase54_core_sleeve_summary.json`
  - `data/processed/phase54_core_sleeve_top20_exposure.csv`
  - `data/processed/phase54_core_sleeve_sample_output.csv`
  - `data/processed/phase55_allocator_cpcv_evidence.json`

### 4.2 Delivered in the First Bounded Packet
- `data/phase59_shadow_portfolio.py`
- `scripts/phase59_shadow_portfolio_runner.py`
- `views/shadow_portfolio_view.py`
- `dashboard.py` bounded tab hook
- `tests/test_phase59_shadow_portfolio.py`
- `tests/test_shadow_portfolio_view.py`

### 4.3 Locked Roadmap Evidence
- `- **Phase 59 - Shadow Portfolio**: extend shadow builders and dashboard surfaces into a read-only DuckDB/Polars monitoring stack with explicit holdout quarantine.`

## 5. Execution Guardrails (Locked)
- **Phase 58 closeout preserved**: `D-326` stays authoritative; the bounded Phase 58 artifacts remain immutable SSOT.
- **Phase 57 closeout preserved**: `D-322` stays authoritative; the bounded Phase 57 artifacts remain immutable SSOT.
- **Phase 56 closeout preserved**: `D-317` stays authoritative; the bounded PEAD artifacts remain immutable SSOT.
- **Phase 55 closeout preserved**: `D-312` stays authoritative; no retry or reinterpretation is permitted.
- **Holdout quarantine**: `RESEARCH_MAX_DATE = 2022-12-31` remains mandatory for any research-side Phase 59 evidence.
- **Same-engine evidence discipline**: where comparator evidence applies, Phase 59 must stay on the same-window / same-cost / same-`core.engine.run_simulation` discipline anchored to `data/processed/phase54_core_sleeve_summary.json`.
- **Phase 53 kernel read-only**: no loader reopen or mutation of the frozen research kernel under `D-292`.
- **Execution scope**: `D-328` / `D-329` authorize only the bounded Shadow NAV / alert surface described by `CHK-P59-EXEC-01`..`CHK-P59-EXEC-09`.

## 6. Acceptance Criteria (Phase 59 Kickoff - Closed)
- [x] `CHK-P59-01`: Phase 59 boundary documented with inherited locks.
- [x] `CHK-P59-02`: The Phase 53 roadmap bullet for Phase 59 is recorded verbatim in the active brief.
- [x] `CHK-P59-03`: Existing Shadow Portfolio reuse hooks are inventoried from the repo-local surfaces only.
- [x] `CHK-P59-04`: Phase 59 execution predicate and blocked state were explicit during kickoff.
- [x] `CHK-P59-05`: `D-327` kickoff record is logged in `docs/decision log.md`.
- [x] `CHK-P59-06`: `docs/handover/phase59_kickoff_memo_20260318.md` is published.
- [x] `CHK-P59-07`: Context packet refreshed and validated from the kickoff brief.
- [x] `CHK-P59-08`: Docs-only SAW acceptance is recorded for the kickoff round.

## 6B. Acceptance Criteria (Phase 59 Execution - Active)
- [x] `CHK-P59-EXEC-01`: Exact execution token consumed into `D-328`.
- [x] `CHK-P59-EXEC-02`: `data/phase59_shadow_portfolio.py` implements a read-only Shadow NAV / alert packet over `allocator_state` plus `phase50_shadow_ship` reference artifacts.
- [x] `CHK-P59-EXEC-03`: `scripts/phase59_shadow_portfolio_runner.py` publishes `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv` with atomic writes.
- [x] `CHK-P59-EXEC-04`: The research-side packet remains clamped to `2015-01-01 -> 2022-12-31` with `max_date <= 2022-12-31`.
- [x] `CHK-P59-EXEC-05`: The reference-side alert contract publishes `holdings_overlap`, `gross_exposure_delta`, `turnover_delta_abs`, and `turnover_delta_rel` from read-only artifacts only.
- [x] `CHK-P59-EXEC-06`: `views/shadow_portfolio_view.py` and `dashboard.py` expose a bounded dashboard reader without opening any execution path.
- [x] `CHK-P59-EXEC-07`: Targeted tests for the packet + view pass.
- [x] `CHK-P59-EXEC-08`: Launch smoke and dual replay evidence are captured under `docs/context/e2e_evidence/`.
- [x] `CHK-P59-EXEC-09`: Same-round docs / notes / decision-log / lessons / context / SAW updates are published with the packet.

## 7. Rollback Plan
- **Trigger**: Any Phase 59 packet that mutates `research_data`, invents non-existent holdings/turnover data on the research lane, weakens prior locks, or implies promotion/live execution authority.
- **Action**: Revert the synchronized Phase 59 code/docs/context/SAW edits and remove `data/processed/phase59_*`. Do not alter `D-326`, `D-322`, `D-317`, `D-312`, or the Phase 53 research kernel.

## 8. New Context Packet (Phase 59 Executing)

## What Was Done
- Consumed the exact `approve next phase` token into `D-328` and opened the first bounded Phase 59 execution packet only.
- Implemented `data/phase59_shadow_portfolio.py`, `scripts/phase59_shadow_portfolio_runner.py`, `views/shadow_portfolio_view.py`, and the bounded dashboard hook in `dashboard.py`.
- Published `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv` from the read-only research catalog plus historical Phase 50 reference artifacts.

## What Is Locked
- `D-284`, `D-292`, `D-309`, `D-311`, `D-312`, `D-313`, `D-314`, `D-315`, `D-316`, `D-317`, `D-318`, `D-319`, `D-320`, `D-321`, `D-322`, `D-323`, `D-324`, `D-325`, `D-326`, `D-327`, `D-328`, `D-329`, `RESEARCH_MAX_DATE = 2022-12-31`, `global_active_variants <= 18`, and the same-window / same-cost / same-engine evidence gate.
- `research_data/catalog.duckdb` and `research_data/allocator_state_cube/` remain read-only.
- `data/processed/phase56_*`, `data/processed/phase57_*`, `data/processed/phase58_*`, and the new `data/processed/phase59_*` packet remain evidence-only surfaces; no promotion or widening is authorized.

## What Is Next
- Review the first bounded Phase 59 packet as evidence-only / no-promotion / no-widening before any follow-up scope is proposed.
- Keep the research lane and reference-only alert lane explicitly separate; do not invent a unified holdings/turnover surface that does not exist on disk.
- Treat any stable shadow stack, post-2022 audit, or multi-sleeve shadow execution as future-scope work only.

## First Command
Get-Content data\processed\phase59_shadow_summary.json
