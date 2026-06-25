# SAW Report - Rule100 Softmax v1 UI Wiring

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: RULE100_SOFTMAX_V1_UI_WIRING_20260512
ScopeID: RULE100_SOFTMAX_V1_UI

Scope: Route the explicit `Rule of 100` UI method to Rule100 softmax v1 target weights, update session source to `rule100_softmax_v1`, and prove TSM drops from stale 10% to 0% while cash rises to 80%.

Owned files changed in this round:

- views/optimizer_view.py
- tests/test_optimizer_view.py
- docs/prd.md
- PRD.md
- PRODUCT_SPEC.md
- docs/spec.md
- docs/phase_brief/phase65-brief.md
- docs/notes.md
- docs/lessonss.md
- docs/decision log.md
- docs/context/bridge_contract_current.md
- docs/context/planner_packet_current.md
- docs/context/impact_packet_current.md
- docs/context/done_checklist_current.md
- docs/context/multi_stream_contract_current.md
- docs/context/post_phase_alignment_current.md
- docs/context/observability_pack_current.md
- docs/context/current_context.json
- docs/context/current_context.md

Acceptance checks:

- CHK-01: Explicit `Rule of 100` method writes softmax v1 target weights instead of lifecycle `last_weight`.
- CHK-02: Allocation session state uses `source=rule100_softmax_v1`, and YTD consumes that state through the existing path.
- CHK-03: Regression proves AMAT 10%, LRCX 10%, TSM 0%, CASH 80%, with no stale TSM 10% fallback.
- CHK-04: All-ineligible Rule100 candidate state renders cash-only instead of stale lifecycle weights.
- CHK-05: Rule of 100 continues to bypass cached optimizer execution and mean-variance diagnostics.
- CHK-06: Focused, affected, and full pytest pass.
- CHK-07: Browser smoke on port 8509 confirms the live copy is `Rule of 100 softmax v1 sizing output` and lifecycle replay copy is gone.
- CHK-08: Required independent SAW implementer plus Reviewer A/B/C passes complete.

Findings table:

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | SAW governance cannot close PASS because the required independent Implementer plus Reviewer A/B/C quorum did not complete. | Record BLOCK verdict and carry next action to rerun independent SAW or get explicit user acceptance of machine-test evidence. | Parent orchestration | Open |
| Medium | Existing softmax artifacts did not affect the live page, causing the user-visible 10%/10%/10% allocation loop. | Routed the explicit Rule of 100 branch to softmax v1 targets and added UI/session-state regressions. | Parent orchestration | Fixed |
| Low | Current ordinal scores tie AMAT/LRCX, so max visible allocation remains 10% even after correct wiring. | Documented that visible >10% requires richer continuous score inputs or unequal eligible scores, not a Kelly stack. | Parent orchestration | Carried as product decision |

Scope split summary:

- in-scope findings/actions: fixed the Rule of 100 UI weight source; updated session source; proved TSM drops to 0% and cash rises to 80%; updated docs/context/lesson/decision surfaces.
- inherited findings/actions: broader dirty worktree contains pre-existing unrelated edits from prior lifecycle/navigation rounds and is not reverted here; full SAW quorum remains unavailable.

Document Changes Showing:

| Path | Change summary | Reviewer status |
|---|---|---|
| docs/prd.md | Updated softmax v1 behavior from audit-only to live Rule of 100 UI source. | Parent-reviewed |
| docs/spec.md | Added UI state contract and current-state softmax target contract. | Parent-reviewed |
| docs/phase_brief/phase65-brief.md | Marked softmax v1 audit harness as wired to Rule of 100 UI. | Parent-reviewed |
| docs/notes.md | Updated formula/routing notes with `rule100_softmax_v1` source and current target weights. | Parent-reviewed |
| docs/lessonss.md | Added guardrail that visible sizing artifacts require UI/session-state regressions. | Parent-reviewed |
| docs/decision log.md | Added D-160 for Rule100 softmax v1 UI source routing. | Parent-reviewed |
| docs/context/bridge_contract_current.md | Updated PM bridge with live softmax UI target state. | Parent-reviewed |
| docs/context/impact_packet_current.md | Updated changed files, tests, checks, and current open risk. | Parent-reviewed |
| docs/context/done_checklist_current.md | Added checks for source, TSM drop, and cash-only fallback. | Parent-reviewed |
| docs/context/multi_stream_contract_current.md | Updated stream contract from lifecycle-only to softmax-over-lifecycle. | Parent-reviewed |
| docs/context/post_phase_alignment_current.md | Updated alignment and bottleneck to score richness decision. | Parent-reviewed |
| docs/context/observability_pack_current.md | Updated drift signal for `rule100_softmax_v1` source. | Parent-reviewed |

Document Sorting:

1. docs/prd.md, docs/spec.md
2. docs/phase_brief/phase65-brief.md
3. docs/notes.md, docs/lessonss.md, docs/decision log.md
4. docs/context/bridge_contract_current.md, docs/context/impact_packet_current.md, docs/context/done_checklist_current.md

Subagent ownership check:

- Explorer/Reviewer A completed with the same minimal recommendation: route explicit Rule of 100 to softmax v1 over lifecycle holds, keep optimizer bypass, preserve residual cash.
- Implementer pass: not completed by an independent subagent.
- Reviewer A/B/C quorum: not completed by three independent reviewer agents.
- Ownership check result: BLOCK because required independent agents did not complete.

Verification evidence:

- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py -k rule100 -vv -s` -> PASS, 2 passed.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_rule100_softmax.py -q` -> PASS.
- `.venv\Scripts\python scripts\rule100_softmax_v1_audit.py --as-of-date 2026-05-12` -> PASS, status ok.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_rule100_softmax.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke on `http://127.0.0.1:8509/` -> PASS; selecting Rule of 100 shows softmax v1 copy and no lifecycle replay copy.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

Current target sanity:

- AMAT: current 10%, softmax target 10%.
- LRCX: current 10%, softmax target 10%.
- TSM: current 10%, softmax target 0%, reason `tighten_below_hold_threshold`.
- CASH: current 70%, softmax target 80%.

Open Risks:

- Independent SAW implementer/reviewer quorum is unavailable in this session; governance closure remains BLOCK until rerun or explicitly waived by the user.
- Current softmax v1 ordinal score ties AMAT and LRCX at 10% each; richer continuous score inputs are required if visible >10% concentration is desired.

Next action:

- Decide whether to keep v1 ordinal/equal-score behavior or approve richer continuous score inputs for v1.1; rerun independent SAW quorum when agent capacity is available or accept machine-test evidence for this round.

ClosurePacket: RoundID=RULE100_SOFTMAX_V1_UI_WIRING_20260512; ScopeID=RULE100_SOFTMAX_V1_UI; ChecksTotal=8; ChecksPassed=7; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_SAW_quorum_unavailable; NextAction=decide_score_richness_and_rerun_or_accept_SAW_risk

ClosureValidation: PASS
SAWBlockValidation: PASS
