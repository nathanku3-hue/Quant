# SAW Report - DASH-0 GodView Dashboard IA Redesign Plan

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Frontend/UI, Docs/Ops, Backend, Data | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: PH65_DASH_0_IA_GODVIEW_REDESIGN_PLAN_20260510
ScopeID: DASH_0_IA_SPEC_ONLY

## Scope

DASH-0 approved dashboard information architecture only. It created planning docs for the future GodView page map, page registry/sidebar shell, legacy migration, and ops relocation. It did not edit `dashboard.py`, `views/`, `optimizer_view.py`, Streamlit runtime navigation, providers, alerts, broker code, factor-scout code, discovery-intake output, candidate cards, or backtests.

## Ownership Check

Implementer and reviewers were different agents:

- Implementer pass: Carson
- Reviewer A: Hooke
- Reviewer B: Boole
- Reviewer C: Curie

Ownership check: PASS

## Acceptance Checks

- CHK-01: Target page map is documented.
- CHK-02: Legacy tab movement is documented.
- CHK-03: `st.Page` / `st.navigation` basis is documented from official Streamlit docs.
- CHK-04: Data Health and Drift Monitor relocation to Settings & Ops is documented.
- CHK-05: DASH-1 page registry shell remains held.
- CHK-06: `dashboard.py`, `views/`, and `optimizer_view.py` are not DASH-0-owned runtime files.
- CHK-07: Factor scout, discovery intake output, candidate cards, providers, backtests, alerts, and broker paths remain out of DASH-0 scope.
- CHK-08: Context selector resolves DASH-0 deterministically after inherited G8.1B but before future G9.
- CHK-09: Focused context tests, context validation, scoped compile, closure validation, and architect calibration check pass or produce accepted first-row `INSUFFICIENT`.

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| High | Ops policy allowed `active-alert count` outside Settings & Ops, weakening the no-alert boundary. | Renamed to `active issue count`. | Parent reconciler | Fixed |
| High | Dashboard product spec still mentioned future paper-only alerts, weakening DASH-0's no-alert stance. | Reworded as future signed-decision-only review prompts, not authorized by DASH-0. | Parent reconciler | Fixed |
| High | Context validation drifted to an inherited G8.1B handover, making DASH-0 current context unstable. | Updated context selector to rank `dashboard_ia_handover_*.md` after G8.1B but before future G9, added regression test, rebuilt/validated context. | Parent reconciler | Fixed |
| Medium | Older `Future Dashboard Areas` section was panel-based rather than the DASH-0 page IA. | Marked the section as superseded by DASH-0 and listed the eight approved pages. | Parent reconciler | Fixed |
| Medium | Inherited dirty `dashboard.py` and other non-DASH-0 artifacts can confuse review provenance. | Carried as inherited/out-of-scope and repeated no-runtime boundary in truth surfaces. | Future runtime owner | Carried |
| Low | SAW report was missing during reviewer passes. | Published this SAW report and validated closure/report blocks. | Parent reconciler | Fixed |

## Scope Split Summary

In-scope findings/actions:

- Removed alert-language leakage from DASH-0 docs.
- Marked older panel-based dashboard spec as superseded by DASH-0 IA.
- Fixed context selector ordering for the requested `dashboard_ia_handover_20260510.md`.
- Added context-builder regression coverage.
- Refreshed current truth surfaces to DASH-0 after inherited G8.1B packets reappeared.

Inherited out-of-scope findings/actions:

- Existing `dashboard.py` dirty diff remains inherited runtime work.
- Existing G8.1B factor-scout artifacts exist in the dirty workspace but are not DASH-0-owned.
- Existing `data/discovery`, `data/candidate_cards`, registry artifacts, and backtest artifacts remain outside DASH-0 ownership.
- DASH-1 runtime shell remains future work.

## Reviewer Passes

- Implementer pass: PASS. Confirmed page map, no-runtime scope, and DASH-1 hold.
- Reviewer A product/IA correctness: BLOCK initially for alert-language leakage; PASS after wording fixes.
- Reviewer B runtime/ops resilience: BLOCK initially for context selector drift to G8.1B; PASS after selector ordering fix, context rebuild, and validation.
- Reviewer C data/performance boundary: PASS. Confirmed no factor artifact, discovery-intake output, candidate-card, provider, backtest, alert, broker, or runtime data-write authorization.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
| --- | --- | --- |
| `docs/architecture/dashboard_information_architecture.md` | Approved target page map and DASH-0 no-runtime boundary. | PASS |
| `docs/architecture/dashboard_page_registry_plan.md` | Planned future `st.Page` / `st.navigation` registry/sidebar shell. | PASS |
| `docs/architecture/dashboard_redesign_migration_plan.md` | Mapped old tabs into future state-first pages. | PASS |
| `docs/architecture/dashboard_ops_relocation_policy.md` | Moved Data Health and Drift Monitor to future Settings & Ops; replaced alert wording with issue wording. | PASS |
| `docs/architecture/godview_dashboard_wireframe.md` | Added DASH-0 page-order update. | PASS |
| `docs/architecture/dashboard_product_spec.md` | Marked older panel section superseded and removed DASH-0 alert authority. | PASS |
| `docs/handover/dashboard_ia_handover_20260510.md` | Added PM handover and new-context packet. | PASS |
| `scripts/build_context_packet.py` | Added `dashboard_ia_handover_*.md` discovery and deterministic subphase ordering. | PASS |
| `tests/test_build_context_packet.py` | Added DASH-0 selector regression tests. | PASS |
| `docs/context/*_current.md` and `docs/context/current_context.*` | Refreshed DASH-0 truth surfaces and context packet. | PASS |
| `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`, `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md` | Updated product/governance/formula/lesson surfaces for DASH-0. | PASS |
| `docs/architect/profile_outcomes.csv` | Added first balanced-profile outcome row for architect calibration history. | PASS |

## Document Sorting

Canonical order preserved for GitHub review:

1. Product/governance docs.
2. Architecture docs.
3. Context and handover surfaces.
4. Context builder/test support.
5. SAW report.

## Architect Review

Risk profile: balanced (`w_impact=1.0`, `w_maintainability=1.0`, `w_risk=1.0`, `w_effort=1.0`)

| Option | impact | risk | effort | maintainability | OptionScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: Future `st.Page` / `st.navigation` page registry shell | 5 | 2 | 3 | 5 | 5 |
| B: Keep flat tabs and only reorder | 2 | 3 | 1 | 2 | 0 |
| C: Use automatic `pages/` directory | 4 | 3 | 2 | 3 | 2 |

Recommendation: Option A for DASH-1 because it supports explicit grouping and shared app frame while keeping DASH-0 planning-only.

CalibrationValidation: INSUFFICIENT

## Evidence

- Official Streamlit docs: `st.Page` / `st.navigation` recommended for maximum flexibility; entrypoint acts as shared frame/router; `pages/` directory remains the simpler automatic method.
- `.venv\Scripts\python -m pytest tests\test_build_context_packet.py tests\test_phase61_context_hygiene.py -q` -> PASS, 17 passed.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python -m py_compile scripts\build_context_packet.py` -> PASS.
- Runtime no-touch scan -> PASS for DASH-0 scope; inherited dirty runtime/data paths remain out-of-scope.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_architect_calibration.py --history-csv docs\architect\profile_outcomes.csv --active-profile balanced` -> INSUFFICIENT.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py ...` -> VALID.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_dashboard_ia_redesign_plan_20260510.md` -> VALID.

## Handover

HandoverDoc: docs/handover/dashboard_ia_handover_20260510.md
HandoverAudience: CEO, PM, Frontend/UI implementer

## New Context

ContextPacketReady: PASS
ConfirmationRequired: YES

NewContextPacket:

- What was done: DASH-0 approved dashboard IA planning only.
- What is locked: no runtime code, no new data, no new metrics, no alerts, no broker calls, no rankings, no scores.
- What remains: approve DASH-1 page registry/sidebar shell or hold.
- Immediate first step: wait for explicit DASH-1 approval.

## Open Risks

Open Risks:

- Inherited dirty dashboard runtime worktree.
- Separate G8.1B factor-scout lane artifacts exist in the dirty workspace and remain outside DASH-0 ownership.
- DASH-1 runtime shell and visual QA remain future work.
- Future implementers must keep Research Lab and Settings & Ops from leaking into Command Center.

Next action: approve_dash_1_page_registry_shell_or_hold

ClosureValidation: PASS
SAWBlockValidation: PASS

ClosurePacket: RoundID=PH65_DASH_0_IA_GODVIEW_REDESIGN_PLAN_20260510; ScopeID=DASH_0_IA_SPEC_ONLY; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=inherited_dirty_dashboard_runtime_worktree_dash1_runtime_shell_pending_g8_1b_factor_scout_separate_lane; NextAction=approve_dash_1_page_registry_shell_or_hold
