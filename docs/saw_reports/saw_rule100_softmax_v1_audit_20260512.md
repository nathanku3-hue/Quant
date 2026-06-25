# SAW Report - Rule100 Softmax v1 Audit

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Data, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: RULE100_SOFTMAX_V1_AUDIT_20260512
ScopeID: RULE100_SOFTMAX_V1

Scope: Build one first-class Rule100 softmax v1 sizing artifact stack and keep Kelly as a thin ablation on the same replay/audit harness.

Owned files changed in this round:

- strategies/rule100_softmax.py
- scripts/rule100_softmax_v1_audit.py
- tests/test_rule100_softmax.py
- data/processed/rule100_softmax_v1_summary.json
- data/processed/rule100_softmax_v1_comparison.csv
- data/processed/rule100_softmax_v1_sample_output.csv
- data/processed/rule100_softmax_v1_cash_allocation.csv
- docs/prd.md
- PRD.md
- PRODUCT_SPEC.md
- docs/spec.md
- docs/phase_brief/phase65-brief.md
- docs/notes.md
- docs/lessonss.md
- docs/decision log.md
- docs/context/bridge_contract_current.md
- docs/context/impact_packet_current.md
- docs/context/done_checklist_current.md
- docs/context/current_context.json
- docs/context/current_context.md

Acceptance checks:

- CHK-01: Softmax v1 sizing helpers exist, are pure, and enforce score -> softmax -> cap -> cash.
- CHK-02: Shared audit harness writes summary, comparison, sample, and cash artifacts atomically.
- CHK-03: Kelly remains comparator-only on the same candidate frame and does not backfill zero-edge names.
- CHK-04: Focused softmax tests pass, including cash-only replay edge case.
- CHK-05: Affected lifecycle/optimizer tests pass.
- CHK-06: Full repository pytest passes.
- CHK-07: Docs-as-code, formula notes, decision log, lessons log, and context packets are refreshed.
- CHK-08: Required independent SAW implementer plus Reviewer A/B/C passes complete.

Findings table:

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | SAW governance cannot close PASS because independent implementer/reviewer agents were unavailable after usage-limit/capacity failures. | Record BLOCK verdict and carry next action to rerun independent SAW when agent quota is available or user explicitly accepts proceeding risk. | Parent orchestration | Open |
| Low | Audit harness could fail to sort a cash-only zero-open-position frame because `sizing_eligible` was absent on the empty frame. | Sort only by columns that exist and add a cash-only artifact regression. | Parent orchestration | Fixed |
| Low | Formula note could imply age/trim penalties were active by default. | Document optional coefficient weights and default-zero behavior. | Parent orchestration | Fixed |

Scope split summary:

- in-scope findings/actions: fixed cash-only artifact edge case; clarified formula notes; regenerated artifacts; reran focused, affected, and full regression checks.
- inherited findings/actions: broader dirty worktree contains pre-existing unrelated edits from prior lifecycle/UI rounds and is not reverted here; independent SAW reviewer availability remains an inherited governance constraint.

Document Changes Showing:

| Path | Change summary | Reviewer status |
|---|---|---|
| docs/prd.md | Added Rule100 softmax v1 audit product delta and held scope. | Parent-reviewed |
| docs/spec.md | Added softmax v1 audit contract, helper/harness paths, and boundary. | Parent-reviewed |
| docs/phase_brief/phase65-brief.md | Added softmax v1 audit addendum with acceptance checks. | Parent-reviewed |
| docs/notes.md | Added explicit softmax and Kelly comparator formulas with source paths. | Parent-reviewed |
| docs/lessonss.md | Added Kelly comparator guardrail for zero-edge cash residuals. | Parent-reviewed |
| docs/decision log.md | Added decision row for softmax-first v1 and Kelly comparator-only stance. | Parent-reviewed |
| docs/context/bridge_contract_current.md | Added PM/system bridge for softmax v1 audit artifacts. | Parent-reviewed |
| docs/context/impact_packet_current.md | Added changed files, interfaces, checks, and open risks. | Parent-reviewed |
| docs/context/done_checklist_current.md | Added machine-checkable softmax v1 audit checklist. | Parent-reviewed |

Document Sorting:

1. docs/prd.md, docs/spec.md
2. docs/phase_brief/phase65-brief.md
3. docs/notes.md, docs/lessonss.md, docs/decision log.md
4. docs/context/bridge_contract_current.md, docs/context/impact_packet_current.md, docs/context/done_checklist_current.md

Subagent ownership check:

- Implementer pass: attempted; unavailable after usage-limit/capacity failures.
- Reviewer A strategy correctness: attempted; unavailable after usage-limit/capacity failures.
- Reviewer B runtime and operational resilience: attempted; remaining agent id was not found after resume, so no completed independent review artifact is available.
- Reviewer C data integrity and performance path: attempted; unavailable after usage-limit/capacity failures.
- Ownership check result: BLOCK because required independent agents did not complete.

Verification evidence:

- `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py -q` -> PASS, 11 passed.
- `.venv\Scripts\python scripts\rule100_softmax_v1_audit.py --as-of-date 2026-05-12` -> PASS, status ok.
- `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_pinned_universe.py tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

Audit artifact sanity:

- Current v0 gross: 0.30; cash residual: 0.70; nonzero names: 3.
- Softmax v1 eligible names: 2; gross budget: 0.20; gross weight: 0.20; cash residual: 0.80.
- Kelly ablation gross weight: 0.00; cash residual: 1.00; comparator-only: true.
- TSM is included in the comparison artifact but `sizing_eligible=False` with `tighten_below_hold_threshold`, so its softmax target is 0.

Open Risks:

- Independent SAW reviewer passes are unavailable in this session; governance closure remains BLOCK until rerun or explicitly waived by the user.
- No UI/runtime routing was changed; these artifacts are an audit/sizing stack only.

Next action:

- Rerun independent SAW Implementer and Reviewer A/B/C passes when agent quota is available, or get explicit user acceptance to proceed with machine-test evidence only.

ClosurePacket: RoundID=RULE100_SOFTMAX_V1_AUDIT_20260512; ScopeID=RULE100_SOFTMAX_V1; ChecksTotal=8; ChecksPassed=7; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_SAW_review_unavailable; NextAction=rerun_independent_SAW_or_get_user_acceptance

ClosureValidation: PASS
SAWBlockValidation: PASS
