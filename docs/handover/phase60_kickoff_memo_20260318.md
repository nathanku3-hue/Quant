# MEMO: Phase 60 Kickoff - Stable Shadow Portfolio

Date: 2026-03-18
Updated: 2026-03-18 (D-335 planning-only kickoff published)
To: Project Lead
From: Codex (repo SSOT draft)
Status: Planning-only kickoff published under `D-335`. Execution remains blocked pending a separate explicit token.

## Scope Lock
- Phase 59 remains closed again under `D-334`; the bounded Shadow Portfolio artifacts stay immutable SSOT.
- Phase 58 remains closed under `D-326`; the bounded Governance Layer artifacts stay immutable SSOT.
- Phase 57 remains closed under `D-322`; the bounded Corporate Actions artifacts stay immutable SSOT.
- Phase 56 remains closed under `D-317`; the bounded PEAD artifacts stay immutable SSOT.
- Phase 55 remains closed under `D-312`; allocator governance evidence stays immutable SSOT.
- Phase 53 research-v0 kernel remains complete and read-only under `D-292`.
- Rule-of-100 remains inactive under `D-309`.
- Phase 60 is active in planning-only mode under `D-335`; `NextPhaseApproval = PENDING` for implementation.
- Holdout quarantine and same-window / same-cost / same-`core.engine.run_simulation` evidence discipline remain in force; `RESEARCH_MAX_DATE = 2022-12-31`.

## Complete Institutional Pivot (D-332 Planning Snapshot)
- **Critical Mission**: Restore validator PASS before opening any new sidecar testing or data-milestone execution path.
- **Next Data Milestone**: Complete Institutional Pivot on the already-in-place PIT-clean CRSP/Compustat 2000-2024 bedrock with zero from-scratch replacement required.
- **Operational Validator Failures (Must Clear Immediately)**: 14-day feature freshness gap + 2 zombie snapshot rows.
- **S&P 500 Pro / Moody's B&D Resolution**: Method B preferred (isolated Parquet sidecars, view-layer join only) at 92/100 confidence.
- **Hybrid Institutional Lake Status**: CRSP/Compustat (governed core), Osiris (isolated sidecar), S&P/Moody's (Method B preferred), Yahoo (separate from institutional lake).
- **Out-of-Boundary Block**: Ingestion keys/schema mappings that violate governed core updater schema are flagged and blocked at 100/100 confidence.
- **Phase 60 Planning Deliverables**: (1) Validator fix as Priority #1, (2) Method B preference locked, (3) Out-of-boundary ingestion block enforced.

## Repo Walk-Through Summary (Stable Shadow Planning Inputs)
- **Positive governed sleeve input**:
  - `data/processed/phase56_pead_summary.json`
  - `data/processed/phase58_governance_summary.json`
- **Blocked planning inputs**:
  - `data/processed/phase54_core_sleeve_summary.json`
  - `data/processed/phase55_allocator_cpcv_evidence.json`
  - `data/processed/phase59_shadow_summary.json`
- **Locked roadmap evidence**:
  - Phase 53 roadmap: `Phase 60 - Stable Shadow Portfolio`

## Locked Planning Contracts
- **Unified surface**: adopt a governed daily holdings / weights cube from sleeves plus allocator surfaces. Legacy `phase50_shadow_ship` stays `reference_only` and cannot populate governed comparator metrics.
- **Governed cost policy**: `5.0` bps is the only gating comparator basis; `10.0` bps is required sensitivity-only evidence and is non-gating.
- **Post-2022 audit**: exactly one integrated audit is allowed, with mandatory preflight checks and kill switches defined before any holdout run starts.
- **Allocator carry-forward**: allocator overlay fields may exist in planning artifacts, but governed carry-forward remains excluded until research eligibility clears.

## Governance Clarification
- Phase 60 is planning-only in this round under `D-335`.
- No Phase 60 code, tests, evidence generation, or post-2022 run are authorized.
- No comparator widening beyond the locked planning contracts is authorized here.
- No prior sleeve or shadow artifact may be reinterpreted or rewritten in this round.

## Execution Gate Checklist (Planning-Only)
- `D-334` remains the authority for the closed Phase 59 endpoint.
- `D-326`, `D-322`, `D-317`, and `D-312` remain the authorities for the closed prior sleeve/governance endpoints.
- `D-292` confirms the Phase 53 kernel remains read-only.
- `D-309` keeps Rule-of-100 inactive.
- Phase 60 implementation and evidence generation are not authorized; a future exact `approve next phase` token is required.
- `NextPhaseApproval = PENDING`.
- All Stable Shadow implementation, post-2022 audit execution, and production promotion remain blocked.

## Acceptance Checks (Phase 60 Kickoff Refresh + D-332 Institutional Pivot)
- `CHK-P60-01`: Boundary documented with inherited locks.
- `CHK-P60-02`: Phase 53 roadmap scope recorded verbatim.
- `CHK-P60-03`: `D-335` logged as planning-only.
- `CHK-P60-04`: Unified governed comparator surface contract recorded.
- `CHK-P60-05`: Governed cost policy recorded.
- `CHK-P60-06`: One-shot post-2022 audit preflight + kill-switch contract recorded.
- `CHK-P60-07`: Allocator carry-forward exclusion recorded.
- `CHK-P60-08`: Bridge and context refreshed.
- `CHK-P60-09`: Implementation remains blocked pending a future exact `approve next phase` token.
- `CHK-P60-10`: `D-332` institutional pivot snapshot remains incorporated inside the active planning boundary.
- `CHK-P60-11`: Method B remains locked as planning default for S&P/Moody's sidecars.
- `CHK-P60-12`: Out-of-boundary ingestion block remains enforced.

## Out of Scope (Phase 60 Planning-Only Kickoff)
- Any code/data changes
- Any post-2022 run
- Stable Shadow implementation
- New evidence generation
- Prior-phase widening or reopening
- Loader/kernel mutation
- Production promotion
