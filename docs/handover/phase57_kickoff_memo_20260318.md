# MEMO: Phase 57 Kickoff - Event Sleeve 2 (Corporate Actions)

Date: 2026-03-18  
Updated: 2026-03-18 (planning-only kickoff)  
To: Project Lead  
From: Codex (repo SSOT draft)  
Status: Planning-only kickoff recorded. Execution remains blocked pending a separate explicit token.

## Scope Lock
- Phase 56 remains closed under `D-317`; the bounded PEAD artifacts stay immutable SSOT.
- Phase 55 remains closed under `D-312`; `D-311` evidence stays permanent SSOT.
- Phase 53 research-v0 kernel remains complete and read-only under `D-292`.
- Rule-of-100 remains inactive under `D-309`.
- Phase 57 is opened for planning only; `NextPhaseApproval = PENDING` for execution.
- Holdout quarantine and same-window/same-cost/`core.engine.run_simulation` evidence gate remain in force; `end_date <= 2022-12-31`.
- Default governance ceiling remains `global_active_variants <= 18` unless a future execution packet narrows it explicitly.

## Repo Walk-Through Summary (Corporate Actions Surface)
- **Existing hooks**:
  - `data/build_tri.py`
  - `tests/test_build_tri.py`
  - `data/dashboard_data_loader.py`
  - `data/feature_store.py`
  - `core/instrument_mapper.py`
  - `scripts/generate_instrument_mapping.py`
  - `data/calendar_updater.py`
  - `backtests/event_study_csco.py::run_event_study`
  - `scripts/phase56_pead_runner.py::run_pead`
  - `core.engine.run_simulation`
- **Locked roadmap evidence**:
  - Phase 53 roadmap: `Phase 57 - Event Sleeve 2 (Corporate Actions)`
  - Missing-hook table row: `corporate-actions taxonomy`

## Governance Clarification
- Phase 57 is planning-only in this round.
- No Phase 57 code, tests, or evidence generation are authorized.
- No comparator widening or Phase 56 reopening is authorized here.
- Any future Corporate Actions evidence must define the eligible denominator and confirmation logic family explicitly, stay on the same-window / same-cost / same-`core.engine.run_simulation` path, and respect `RESEARCH_MAX_DATE = 2022-12-31`.

## Execution Gate Checklist (Planning-Only)
- `D-317` remains the authority for the closed Phase 56 endpoint.
- `D-312` keeps Phase 55 closed and immutable.
- `D-292` confirms the Phase 53 kernel remains read-only.
- `D-309` keeps Rule-of-100 inactive.
- Phase 57 execution is not authorized; a future exact `approve next phase` token is required.
- `NextPhaseApproval = PENDING`.
- All Corporate Actions implementation and production promotion remain blocked.

## Acceptance Checks (Phase 57 Kickoff)
- `CHK-P57-01`: Boundary documented with inherited locks.
- `CHK-P57-02`: Phase 53 roadmap scope recorded verbatim.
- `CHK-P57-03`: Existing hooks inventoried from repo-local files only.
- `CHK-P57-04`: Execution predicate and blocked state recorded.
- `CHK-P57-05`: `D-318` logged.
- `CHK-P57-06`: Context refreshed and validated.
- `CHK-P57-07`: `docs/lessonss.md` updated.
- `CHK-P57-08`: Docs-only SAW acceptance recorded.

## Out of Scope (Phase 57 Planning-Only Kickoff)
- Any code/data changes
- Corporate Actions taxonomy implementation
- Eligible-denominator or confirmation-logic execution
- Phase 57 evidence generation
- Phase 56 comparator widening or reopening
- Loader/kernel mutation
- Post-2022 window changes
- Production promotion
