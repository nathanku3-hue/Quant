# MEMO: Phase 55 Kickoff - Opportunity-Set Controller (Allocator Governance)

Date: 2026-03-17  
Updated: 2026-03-17 (docs-only kickoff)  
To: Project Lead  
From: Codex (repo SSOT draft)  
Status: Docs-only kickoff recorded. Execution remains blocked pending the exact approval token.

## Scope Lock
- Phase 52 remains closed at the Week 3 endpoint under `D-284`.
- Phase 53 research-v0 data-kernel closeout remains complete under `D-292`.
- Phase 54 Rule-of-100 sleeve rejected under `D-309`; Rule-of-100 remains disabled for Phase 55.
- Execution token remains exact `approve next phase` (not yet issued for Phase 55).
- `NextPhaseApproval = PENDING`.
- Execution is blocked; this memo is docs-only.
- Holdout quarantine and same-window/same-cost/`core.engine.run_simulation` evidence gate remain in force; `end_date <= 2022-12-31`.
- Default governance ceiling stays `global_active_variants <= 18` unless explicitly narrowed later.

## Repo Walk-Through Summary (Allocator Governance Surface)
- **Research kernel surface (read-only)**:
  - `research_data/catalog.duckdb` with `allocator_state` view over `research_data/allocator_state_cube`
  - `allocator_cpcv.sql` + `scripts/run_allocator_cpcv.py` over `research_data/alloc_cpcv_splits`
- **Guarded SQL lineage**:
  - `guard = f"snapshot_date <= DATE '{max_date}'"` in `scripts/run_allocator_cpcv.py`
- **Governance math reuse**:
  - `utils/statistics.py` (CSCV/PBO/DSR helpers)
- **Missing hooks**:
  - SPA/WRC helper (future execution, not in scope for this docs-only kickoff)
  - Phase 55 allocator wrapper (future execution, not in scope for this docs-only kickoff)

## Hook Traceability Snapshot
| Hook | Path / Symbol | State | Verification Intent |
| --- | --- | --- | --- |
| Allocator state (research-v0) | `research_data/catalog.duckdb` + `allocator_state` view | Existing | Read-only evidence surface for Phase 55. |
| CPCV SQL surface | `allocator_cpcv.sql` | Existing | Guarded CPCV shard query. |
| CPCV runner | `scripts/run_allocator_cpcv.py` | Existing | Enforces `snapshot_date <= 2022-12-31`. |
| Governance math | `utils/statistics.py` | Existing | CSCV/PBO/DSR reuse anchor. |
| SPA/WRC helper | allocator governance helper | Missing | Future Phase 55 execution scope only. |

## Governance Clarification
- `global_active_variants <= 18` is the default governance ceiling; only an explicit execution packet may narrow or override it.
- Evidence gate: any risk/execution/meta layer must show delta metrics vs the latest baseline in the same window, at the same costs, using the same `core.engine.run_simulation` path.
- Allocator gate formula (locked): `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`.

## Execution Gate Checklist (Docs-Only)
- `D-284` remains the authority for the closed Phase 52 endpoint.
- `D-292` confirms the Phase 53 research-v0 closeout is complete.
- `D-309` rejects the Rule-of-100 sleeve; it remains disabled for Phase 55.
- Phase 55 execution is not authorized; the exact `approve next phase` token is required.
- `NextPhaseApproval = PENDING`.
- Allocator/meta/event/shadow execution remains blocked.

## Phase 55 - Opportunity-Set Controller (Allocator Governance)
- **Expert-Locked Definitions (canonical)**: See `docs/phase_brief/phase55-brief.md` Section 4.1.

## Acceptance Checks (Phase 55 Kickoff)
- `CHK-P55-01`: Phase 55 boundary documented with locks and canonical evidence input surface.
- `CHK-P55-02`: Nested CPCV definition recorded verbatim.
- `CHK-P55-03`: WRC diagnostic role and gate definition recorded verbatim.
- `CHK-P55-04`: Same-engine definition recorded verbatim.
- `CHK-P55-05`: Evidence citations recorded verbatim in `docs/notes.md`.
- `CHK-P55-06`: D-310 kickoff record logged; `docs/lessonss.md` updated.
- `CHK-P55-07`: Context packet refreshed; execution remains blocked.
- `CHK-P55-08`: Docs-only SAW acceptance recorded in `docs/saw_reports/saw_phase55_d310_kickoff_20260317.md` with `SAW Verdict: PASS`.

## Out of Scope (Phase 55 Docs-Only Kickoff)
- Any code/data changes
- Loader/kernel reopen or Phase 53 mutation
- Rule-of-100 reintroduction
- Post-2022 window changes
- Allocator execution or production promotion
