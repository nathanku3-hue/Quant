# SAW Report - Rule100 Softmax v1.1 Contract Fix

SAW Verdict: PASS

RoundID: RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512
ScopeID: RULE100_SOFTMAX_V1_1_CONTRACT_FIX
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Backend/Strategy, Frontend/UI, Data, Docs/Ops

## Scope and Ownership

Work round scope: fix the Rule100 softmax v1.1 research contract without promoting v1.1 into runtime.

Owned files changed in this round:

- `strategies/rule100_softmax_v1_1.py`
- `scripts/rule100_softmax_v1_1_audit.py`
- `tests/test_rule100_softmax_v1_1.py`
- `tests/test_policy_target_timeline_apptest.py`
- `docs/strategy_stream_v1_1_contract.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/current_context.json`
- `data/processed/rule100_softmax_v1_1_comparison.csv`
- `data/processed/rule100_softmax_v1_1_summary.json`
- `data/processed/rule100_softmax_v1_1_history.retired.csv`

Acceptance checks:

- CHK-01: v1.1 active artifacts are comparison CSV and summary JSON only.
- CHK-02: stale `rule100_softmax_v1_1_history.csv` is absent from active artifacts and retired.
- CHK-03: v1.1 factor coverage counts approved factor groups, not raw columns.
- CHK-04: missing factor strength shrinks toward neutral `0.50` by group coverage.
- CHK-05: Policy Target Timeline AppTest uses real `AppTest.from_file("dashboard.py")`.
- CHK-06: focused compile, audit refresh, route/runtime smoke, context validation, and focused tests pass.
- CHK-07: full pytest passes after the scoped fix.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| P1 | Stale v1.1 history could be treated as current despite the comparison/summary contract. | `run_v1_1_audit(...)` retires legacy history to `.retired.csv`; summary records retirement. | Implementer | Fixed |
| P1 | Factor coverage could double-count alternate capital-discipline columns. | Added group-value/count helpers and wired audit counts through approved groups. | Implementer | Fixed |
| P2 | Sparse factor coverage filled missing strength to 0.0 instead of neutral shrinkage. | `compute_factor_strength_continuous(...)` now shrinks missing groups toward `0.50`. | Implementer | Fixed |
| P2 | AppTest coverage copied table logic instead of rendering `dashboard.py`. | Replaced copied mini-app tests with `AppTest.from_file("dashboard.py")` route regression. | Implementer | Fixed |

## Scope Split Summary

In-scope findings/actions:

- All four user-reported findings are fixed and covered by focused tests.
- v1.1 remains research-only with no runtime promotion.
- Active v1.1 history artifact is absent; retired artifact is explicitly marked.

Inherited out-of-scope findings/actions:

- v1.1 still lacks multi-date return/risk/turnover promotion evidence; owner: future Strategy/Data round; target milestone: separate v1.1 shadow-evidence approval.
- Broad dirty worktree from earlier dashboard/lifecycle rounds remains inherited; owner: repo maintainer/current phase closure; target milestone: phase-close git hygiene.

## SAW Passes

| Pass | Agent | Ownership | Result | Evidence |
|---|---|---|---|---|
| Implementer | Averroes | implementation validation | PASS | 5/5 checks, focused `pytest` 16 passed, compile PASS |
| Reviewer A | Darwin | strategy correctness/regression risk | PASS | group coverage, neutral shrinkage, v1/v1.1 boundary checks PASS |
| Reviewer B | Curie | runtime/operational resilience | PASS | atomic writes, retired history, no dashboard v1.1 promotion, real AppTest PASS |
| Reviewer C | Feynman | data integrity/performance path | PASS | active history absent, retired history present, group counts max 4, focused tests PASS |

Ownership check: PASS. Implementer and Reviewers A/B/C were different agents.

## Verification Evidence

| EvidenceID | Command / Check | Result | Notes |
|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile strategies\rule100_softmax_v1_1.py scripts\rule100_softmax_v1_1_audit.py tests\test_rule100_softmax_v1_1.py tests\test_policy_target_timeline_apptest.py` | PASS | scoped compile |
| EVD-02 | `.venv\Scripts\python scripts\rule100_softmax_v1_1_audit.py --as-of-date 2026-05-12` | PASS | summary/comparison refreshed; stale history retired |
| EVD-03 | `.venv\Scripts\python -m pytest tests\test_rule100_softmax_v1_1.py tests\test_policy_target_timeline_apptest.py tests\test_rule100_softmax.py tests\test_position_lifecycle.py tests\test_dash_1_page_registry_shell.py -q` | PASS | 61 passed |
| EVD-04 | HTTP readiness on `http://127.0.0.1:8509` | PASS | HTTP 200 |
| EVD-05 | `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS | context validation |
| EVD-06 | Subagent SAW quorum | PASS | Implementer + Reviewers A/B/C all PASS |
| EVD-07 | `.venv\Scripts\python -m pytest -q` | PASS | full regression passed |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05,TSK-06:EVD-06,TSK-07:EVD-07
EvidenceRows: EVD-01|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:00:00Z;EVD-02|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:00:00Z;EVD-03|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:00:00Z;EVD-04|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:00:00Z;EVD-05|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:00:00Z;EVD-06|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:00:00Z;EVD-07|RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512|2026-05-12T11:05:00Z

## Document Changes Showing

- `docs/prd.md`: added v1.1 contract addendum with artifact, formula, and evidence.
- `docs/spec.md`: added v1.1 research contract and no-active-history boundary.
- `docs/phase_brief/phase65-brief.md`: added current round live-loop addendum.
- `docs/notes.md`: recorded explicit v1.1 group-count and shrinkage formulas with source paths.
- `docs/lessonss.md`: logged stale artifact/copy-test miss and guardrail.
- `docs/decision log.md`: added D-163 and superseded stale D-162 implementation detail.
- `docs/context/*_current.md`: refreshed bridge, impact, done, planner, multi-stream, alignment, and observability truth.

Reviewer status: approved by Implementer and Reviewers A/B/C.

Document sorting order is maintained per `docs/checklist_milestone_review.md`: PRD/spec surfaces first, phase brief, notes/lessons/decision log, then context surfaces.

## Open Risks

Open Risks:

- No in-scope Critical/High risks remain.
- Inherited risk: v1.1 requires multi-date shadow evidence before any promotion decision.
- Inherited risk: broad dirty worktree remains outside this scoped contract-fix round.

Next action: hold or separately approve v1.1 multi-date shadow evidence.

ClosurePacket: RoundID=RULE100_SOFTMAX_V1_1_CONTRACT_FIX_20260512; ScopeID=RULE100_SOFTMAX_V1_1_CONTRACT_FIX; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=none_in_scope; NextAction=hold_or_collect_v1_1_multi_date_shadow_evidence

ClosureValidation: PASS
SAWBlockValidation: PASS
EvidenceValidation: PASS

Rollback Note: revert only the v1.1 scoring/audit/test files, refreshed v1.1 processed artifacts, and this round's docs/context updates; do not revert unrelated dashboard/lifecycle changes already present in the worktree.
