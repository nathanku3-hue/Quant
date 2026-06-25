# SAW Report - Rule100 Softmax v1 History Overlay

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512
ScopeID: RULE100_SOFTMAX_V1_HISTORY_OVERLAY

Scope: Add a PIT-safe softmax v1 historical target-weight overlay for Position Lifecycle Replay history, keep v0 event weights immutable, and show both sources in the dashboard transaction log.

Owned files changed in this round:

- scripts/rule100_softmax_v1_audit.py
- dashboard.py
- tests/test_rule100_softmax.py
- tests/test_position_lifecycle.py
- data/processed/rule100_softmax_v1_history.csv
- PRD.md
- PRODUCT_SPEC.md
- docs/prd.md
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

- CHK-01: Historical overlay artifact is additive and does not overwrite `data/portfolio_lifecycle_log.jsonl`.
- CHK-02: `data/processed/rule100_softmax_v1_history.csv` includes `event_weight`, `softmax_v1_target_weight`, `softmax_v1_cash_residual`, and eligibility reason.
- CHK-03: Dashboard transaction log labels original ledger weight as `Event Weight`.
- CHK-04: Dashboard transaction log labels derived v1 sizing as `Softmax v1 Target` and `Softmax v1 Cash`.
- CHK-05: Regression proves current TSM on 2026-05-11 keeps event weight 10% but has softmax v1 target 0% and cash residual 80%.
- CHK-06: Focused and affected pytest suites pass.
- CHK-07: Full pytest and context packet validation pass.
- CHK-08: Independent SAW implementer plus Reviewer A/B/C passes complete.

SE Executor Summary:

Scope line: stream=Backend/Data+Frontend/UI+Docs/Ops; stage=Executing->Final Verification; owner=parent orchestration; round_exec_utc=2026-05-12T06:01:37Z.

| task_id | task | artifact | check | status | evidence_id |
|---|---|---|---|---|---|
| TSK-01 | Build PIT softmax v1 history overlay writer | scripts/rule100_softmax_v1_audit.py | py_compile and generated history artifact | PASS | EVD-01 |
| TSK-02 | Wire transaction log to overlay columns | dashboard.py | renderer source guard and affected tests | PASS | EVD-02 |
| TSK-03 | Add regression for stale-history bug | tests/test_rule100_softmax.py, tests/test_position_lifecycle.py | current TSM 10% event vs 0% v1 target/cash 80% | PASS | EVD-03 |
| TSK-04 | Refresh docs/context and verify suite | docs/*, docs/context/* | full pytest and context validation | PASS | EVD-04 |

Verification evidence:

| evidence_id | command | result | notes | evidence_utc | run_id |
|---|---|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile dashboard.py scripts\rule100_softmax_v1_audit.py tests\test_rule100_softmax.py tests\test_position_lifecycle.py` | PASS | Syntax check for touched runtime/test files. | 2026-05-12T06:01:37Z | RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512 |
| EVD-02 | `.venv\Scripts\python scripts\rule100_softmax_v1_audit.py --as-of-date 2026-05-12` | PASS | Regenerated `rule100_softmax_v1_history.csv`. | 2026-05-12T06:01:37Z | RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512 |
| EVD-03 | `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_position_lifecycle.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_pinned_universe.py -q` | PASS | 97 tests passed; one third-party deprecation warning. | 2026-05-12T06:01:37Z | RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512 |
| EVD-04 | `.venv\Scripts\python -m pytest -q`; `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS | Full pytest passed; context packet validation returned cleanly. | 2026-05-12T06:01:37Z | RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04
EvidenceRows: EVD-01|RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512|2026-05-12T06:01:37Z;EVD-02|RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512|2026-05-12T06:01:37Z;EVD-03|RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512|2026-05-12T06:01:37Z;EVD-04|RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512|2026-05-12T06:01:37Z

EvidenceValidation: PASS

Findings table:

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | SAW governance cannot close PASS because independent Implementer plus Reviewer A/B/C agents were not spawned in this thread. | Keep SAW verdict BLOCK and carry explicit next action. | Parent orchestration | Open |
| Medium | Lifecycle history implied stale v0 10% sizing because the UI showed only event `weight`. | Added derived v1 history overlay and separate dashboard columns. | Parent orchestration | Fixed |
| Low | Historical BUY rows still remain 10% under v1 because promoted BUY rows are equal 3/4 ordinal scores. | Documented that visible >10% needs richer continuous score inputs, not event-log mutation. | Product/Strategy | Carried |

Scope split summary:

- In-scope findings/actions: added additive v1 history artifact, dashboard overlay merge, stale-history regressions, docs/context/lesson updates, and verification.
- Inherited/out-of-scope findings/actions: broader dirty worktree contains prior lifecycle/navigation/YTD changes and remains untouched; independent SAW reviewer quorum remains pending.

Document Changes Showing:

| Path | Change summary | Reviewer status |
|---|---|---|
| docs/prd.md | Recorded softmax history overlay and artifact set. | Parent-reviewed |
| docs/spec.md | Added dashboard transaction-log source split contract. | Parent-reviewed |
| docs/phase_brief/phase65-brief.md | Extended softmax v1 audit addendum to historical overlay. | Parent-reviewed |
| docs/notes.md | Added explicit formula and source paths for the history overlay. | Parent-reviewed |
| docs/lessonss.md | Added guardrail against repurposing event ledgers as target histories. | Parent-reviewed |
| docs/decision log.md | Added D-161 for Rule100 history audit overlay. | Parent-reviewed |
| docs/context/bridge_contract_current.md | Updated PM bridge with history overlay and current TSM proof. | Parent-reviewed |
| docs/context/planner_packet_current.md | Updated next-session packet for history overlay source split. | Parent-reviewed |
| docs/context/impact_packet_current.md | Updated touched files, interfaces, and checks. | Parent-reviewed |
| docs/context/done_checklist_current.md | Added done checks for v1 history overlay. | Parent-reviewed |
| docs/context/multi_stream_contract_current.md | Updated stream ownership for overlay artifact and UI merge. | Parent-reviewed |
| docs/context/post_phase_alignment_current.md | Updated bottleneck and no-change boundaries. | Parent-reviewed |
| docs/context/observability_pack_current.md | Added drift signals for event-vs-target history confusion. | Parent-reviewed |

Document Sorting:

1. PRD.md, PRODUCT_SPEC.md, docs/prd.md, docs/spec.md
2. docs/phase_brief/phase65-brief.md
3. docs/notes.md, docs/lessonss.md, docs/decision log.md
4. docs/context/bridge_contract_current.md, docs/context/planner_packet_current.md, docs/context/impact_packet_current.md, docs/context/done_checklist_current.md, docs/context/multi_stream_contract_current.md, docs/context/post_phase_alignment_current.md, docs/context/observability_pack_current.md

Subagent ownership check:

- Implementer pass: performed by parent orchestration, not an independent subagent.
- Reviewer A/B/C pass: not performed by independent subagents because the active system only permits spawning subagents when the user explicitly asks for subagent/delegated/parallel agent work.
- Ownership check result: BLOCK for formal SAW quorum; machine tests and artifacts pass.

Current target sanity:

- AMAT on 2026-05-11: event weight 10%, softmax v1 target 10%.
- LRCX on 2026-05-11: event weight 10%, softmax v1 target 10%.
- TSM on 2026-05-11: event weight 10%, softmax v1 target 0%, eligibility `tighten_below_hold_threshold`.
- Cash residual on 2026-05-11: 80%.

Open Risks:

- Independent SAW implementer/reviewer quorum is unavailable in this session; governance closure remains BLOCK until rerun or explicitly waived by the user.
- Historical BUY rows remain 10% under softmax v1 because all promoted BUY rows have equal 3/4 ordinal score; visible >10% sizing requires richer continuous score inputs.
- In-app browser smoke was attempted after implementation but interrupted/timed out; HTTP readiness and test evidence are used for this closure proof.

Next action:

- Manually audit the Transaction Log on port 8509, then either hold v1 or separately approve richer continuous score inputs for v1.1.

ClosurePacket: RoundID=RULE100_SOFTMAX_V1_HISTORY_OVERLAY_20260512; ScopeID=RULE100_SOFTMAX_V1_HISTORY_OVERLAY; ChecksTotal=8; ChecksPassed=7; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_SAW_quorum_unavailable; NextAction=rerun_independent_SAW_or_accept_machine_test_evidence

ClosureValidation: PASS
SAWBlockValidation: PASS
