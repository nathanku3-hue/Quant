# SAW Report - Optimizer History Diagnostics Split

RoundID: 20260515-optimizer-history-diagnostics-split
ScopeID: optimizer-history-diagnostics-split
SAW Verdict: BLOCK
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Backend, Frontend/UI, Data, Docs/Ops

## Scope

This round split Portfolio Optimizer price-readiness diagnostics into true missing local history vs stale local endpoint labels while preserving the fail-closed `insufficient_history` gate.

Owned files changed in this round:

- `views/optimizer_view.py`
- `tests/test_portfolio_universe.py`
- `tests/test_optimizer_view.py`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`

## Acceptance Checks

- CHK-01: Missing-history and stale-endpoint counts are split without changing backend ineligibility.
- CHK-02: Universe Audit renders `Missing History`, `Stale Endpoint`, and `Latest Price Date`.
- CHK-03: Focused optimizer universe/view tests pass.
- CHK-04: Docs-as-code surfaces record the split and boundary.
- CHK-05: Context packet builds and validates.
- CHK-06: Independent Implementer and Reviewer A/B/C passes complete.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Formal SAW independence was not completed in this turn; implementer and reviewers are not different agents. | Carry SAW governance as BLOCK until independent implementer/reviewer passes are run, or user accepts advisory closure for this narrow diagnostic slice. | Parent orchestration | Open |
| Low | Stale local price columns remain diagnosed but unrepaired. | Keep as Data follow-up: repair stale endpoint columns through canonical market-data update path. | Data | Carried |
| Low | Pre-2025 Rule100 candidate/decision artifacts remain absent. | Keep as Backend/Data follow-up: build PIT-safe historical evidence artifacts before expecting pre-2025 BUY/SELL replay. | Backend/Data | Carried |

## Scope Split

In-scope:

- Split UI diagnostics and tests for optimizer universe price-readiness causes.
- Preserve fail-closed stale endpoint behavior.
- Update docs/current truth surfaces.

Inherited/out-of-scope:

- Broad dirty worktree.
- Stale local price repair.
- Pre-2025 Rule100 candidate/decision artifact rebuild.
- Provider ingestion, canonical market-data writes, broker behavior, alerts, rankings, scoring, or recommendations.

## Document Changes Showing

- `PRD.md` - added product requirement for Missing History vs Stale Endpoint diagnostics. Reviewer status: parent-checked.
- `PRODUCT_SPEC.md` - added spec contract for split labels and `Latest Price Date`. Reviewer status: parent-checked.
- `docs/prd.md` - added implementation addendum and evidence. Reviewer status: parent-checked.
- `docs/spec.md` - added contract lock formula. Reviewer status: parent-checked.
- `docs/notes.md` - added diagnostic split notes. Reviewer status: parent-checked.
- `docs/decision log.md` - added hardcoded decision record. Reviewer status: parent-checked.
- `docs/lessonss.md` - added guardrail lesson. Reviewer status: parent-checked.
- `docs/phase_brief/phase65-brief.md` - added live-loop addendum. Reviewer status: parent-checked.
- `docs/context/*current*` - refreshed bridge, impact, done, planner, and generated current context. Reviewer status: parent-checked.

## Document Sorting

Order follows checklist-milestone-review priority where applicable: root product docs, canonical docs, decision/notes/lessons, phase brief, current truth surfaces, report.

## Verification Evidence

| EvidenceID | Command | Result | Notes |
|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile views\optimizer_view.py strategies\portfolio_universe.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` | PASS | Scoped compile. |
| EVD-02 | `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` | PASS, 62 passed | Focused backend/UI regression. |
| EVD-03 | `.venv\Scripts\python scripts\build_context_packet.py` | PASS | Context packet generated. |
| EVD-04 | `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS | Context validation. |
| EVD-05 | `.venv\Scripts\python .codex\skills\_shared\scripts\validate_se_evidence.py ...` | PASS | SE evidence map valid. |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-02,TSK-04:EVD-03,TSK-05:EVD-04
EvidenceRows: EVD-01|20260515-optimizer-history-diagnostics-split|2026-05-15T14:50:20Z;EVD-02|20260515-optimizer-history-diagnostics-split|2026-05-15T14:50:20Z;EVD-03|20260515-optimizer-history-diagnostics-split|2026-05-15T14:51:00Z;EVD-04|20260515-optimizer-history-diagnostics-split|2026-05-15T14:51:25Z;EVD-05|20260515-optimizer-history-diagnostics-split|2026-05-15T14:51:42Z
EvidenceValidation: PASS

## Open Risks

Open Risks:

- Independent SAW Implementer and Reviewer A/B/C passes were not run in this turn, so formal SAW closure is BLOCK.
- Stale local price endpoints are diagnosed only; repair remains open.
- Pre-2025 Rule100 evidence artifacts remain absent and replay remains cash-closed before candidate coverage.

## Next action

Next action:

Run independent SAW implementer/reviewer passes for this diagnostic slice, or proceed to one of the separate follow-ups: stale endpoint repair or Rule100 historical evidence artifact rebuild.

ClosurePacket: RoundID=20260515-optimizer-history-diagnostics-split; ScopeID=optimizer-history-diagnostics-split; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_saw_reviews_not_run; NextAction=run_independent_saw_reviews_or_accept_advisory_closure
ClosureValidation: PASS
SAWBlockValidation: PASS
