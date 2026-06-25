# AGENTS.md

> SYSTEM CONTEXT: You are a contributor to Terminal Zero (T0), a local-first quantitative research console.
> ROOT PATH: `E:\code\Quant`

## 1. Tech Stack (Hard Constraints)
- Runtime: Python 3.12+ with strict `.venv` usage.
- Core: Streamlit (UI), DuckDB (SQL engine), Pandas/Polars (dataframes).
- Data: Parquet (storage), yfinance (live data bridge).
- Visualization: Plotly + Streamlit native components.
- Testing: `pytest` (unit), `streamlit.testing` (integration when applicable).
- Forbidden without explicit approval: SQLite, Flask, Django, or complex ORMs.

## 2. Directory Map
Keep strict separation of concerns:
- `app.py`: orchestrator and entry point. Keep thin.
- `data/`: ETL pipelines, updaters, static datasets, map builders.
- `strategies/`: strategy logic, scoring, optimization cartridges.
- `views/`: Streamlit rendering and interaction logic.
- `tests/`: test suites mirroring source structure.
- `docs/`: phase briefs and specifications.
- `docs/context/`: current truth surfaces (see Section 2.1)
- `docs/lessonss.md`: self-learning loop log for mistakes and guardrails.
- `docs/research/`: domain research PDFs and synthesized findings.
- `.codex/skills/`: canonical repo-local Codex skills (including `saw` and `research-analysis`).
- `skills/`: reserved for project deliverables; not the canonical agent-skill source.

### 2.1 Current Truth Surfaces (Mandatory Reading)

Before starting any work, check which truth surfaces exist and are required for this repo/round:

**Root SOP governance:**
- `E:\code\SOP\KERNEL_ACTIVATION_MATRIX.md` — when each kernel capability becomes mandatory
- `E:\code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` — 11-section checklist for multi-stream execution readiness
- `E:\code\SOP\ENDGAME.md` — target state for SOP governance control plane

**Current truth surfaces (in `docs/context/`):**
- `bridge_contract_current.md` — translates recent execution truth into PM/planner next-step language (SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP, DO_NOT_REDECIDE)
- `done_checklist_current.md` — machine-checkable done criteria for current phase
- `planner_packet_current.md` — compact fresh-context packet for planner (current context, active brief, bridge truth, decision tail, blocked next step, active bottleneck)
- `impact_packet_current.md` — impact view (changed files, owned files, touched interfaces, failing checks)
- `multi_stream_contract_current.md` — cross-stream coordination map (Backend, Frontend/UI, Data, Docs/Ops)
- `post_phase_alignment_current.md` — post-phase stream status update and bottleneck analysis
- `observability_pack_current.md` — drift detection markers (high-risk attempts, stuck sessions, skill under-triggering, budget pressure, compaction/hallucination pressure)

**Activation rules:**
- Bridge contract: always active (required for any repo with execution truth)
- Done checklist: always active (required when closure can drift)
- Planner packet: always active (required when planner rereads too much)
- Impact packet: active (mature repo with many files)
- Multi-stream contract: active (multi-stream repo: Backend, Frontend/UI, Data, Docs/Ops)
- Post-phase alignment: active (multi-stream repo with scope boundaries)
- Observability pack: active (drift risk is non-trivial, 5+ phases completed)

**Entry sequence:**
1. Start from `planner_packet_current.md` (compact entry point)
2. Load `impact_packet_current.md` (changed files, owned files, touched interfaces)
3. Load `bridge_contract_current.md` (PM/planner bridge)
4. Load `done_checklist_current.md` (acceptance criteria)
5. Only escalate to wider reads (phase briefs, decision log, full repo) if one of these conditions applies:
   - Impact surface is unclear from planner packet + impact packet
   - Interface ownership is unclear from owned files list
   - Evidence conflicts between bridge truth and decision tail
   - Bottleneck cannot be named from current context

## 3. Operating Principles (Core Commandments)
1. Docs-as-Code: if behavior changes, update docs (prd and product spec) and decision log in the same milestone. for explicit formulas used, document the explicit formula and where .py used ,in notes.md, 
2. Atomic Safety: critical data writes must be atomic (temp -> replace).
3. Top-Down Delivery: spec -> interface -> implementation -> test.
4. Defense in Depth: assume API failures and NaN-heavy data; fail gracefully.
5. Subagent-First: default to subagents for non-trivial work (multi-file changes, ETL, strategy logic, runtime/ops risk paths).
6. Guardrailed Delegation: each subagent must have bounded scope (owned files/tasks), explicit acceptance checks, and no destructive operations without user confirmation.
7. Review Gated: no milestone is done without subagent review (Section 5).
8. Self-Learning: after each work/review round, record mistakes, root causes, and guardrails in `docs/lessonss.md`.
9. Evidence Gate (Non-Negotiable): No new risk/execution layer may ship without delta metrics vs latest baseline (C3) in the same window, same costs, and same `engine.run_simulation` path.

## 4. Delivery Workflow
1. Brief: create or update `docs/<phase>-brief.md` with acceptance criteria and live loop state.
2. Plan: propose concrete file-level implementation steps using the mandatory contract in Section 11.
3. Orchestrate: assign subagents with clear ownership (`Implementer`, `Reviewer A/B/C`) and acceptance checks.
4. Execute: implement vertical slices (Data -> Strategy -> View -> Ops).
5. Verify: run `.venv\Scripts\python -m pytest` and runtime smoke checks (`.venv\Scripts\python launch.py` or `.venv\Scripts\streamlit run app.py`).
6. Review: execute the Section 5 milestone gate.
7. Bridge: refresh `docs/context/bridge_contract_current.md` with `SYSTEM_DELTA`, `PM / Product Delta`, `OPEN_DECISION`, `RECOMMENDED_NEXT_STEP`, and `DO_NOT_REDECIDE`.
8. Impact: refresh `docs/context/impact_packet_current.md` with changed files, owned files, touched interfaces, failing checks.
9. Alignment: refresh `docs/context/post_phase_alignment_current.md` when multi-stream or system-shaping work completes.
10. Report: include observability rating, evidence footer (Section 9), and top-down snapshot (Section 11).
11. SAW round: run Subagents-After-Work protocol from Section 12.
12. Planner return: refresh `docs/context/planner_packet_current.md` for next round entry.

## 5. Milestone Review Gate (Mandatory)
Before closing a milestone, spawn reviewer subagents using this prompt:
- Use the Section 12 reviewer mapping/schema and Section 14 interaction contract; do not duplicate prompt variants.

Risk tier checks:
- Low: touched-module unit tests and static checks.
- Medium: Low + integration/smoke checks.
- High: Medium + data integrity checks (atomic write path, row-count/sanity assertions) and rollback note.
- Critical: High + dry-run evidence and explicit user sign-off before any production-impacting operation.

## 6. Engineering Standards
- Vectorization first: avoid loops over DataFrame rows/columns when a vectorized path exists.
- PIT discipline: never leak future data; fundamentals align by `release_date`.
- Restartability: long ETL/update jobs should be resumable/checkpointed.
- Explainability: scoring outputs must expose human-readable reasoning in UI.
- Environment hygiene: keep `requirements.txt` in sync with imports.
- Windows process-liveness checks: never use `os.kill(pid, 0)` on Windows; require an OS-native non-destructive process query for lock ownership or stale-lock recovery.

## 7. Change Discipline
- No destructive operations without explicit user confirmation.
- Never revert unrelated local changes.
- Read files before overwriting; preserve surrounding architecture style.
- Keep new dependencies minimal and justified.

### 7.1 Expert Packet Deliverables
- When packing current status for expert guidance, produce exactly one deliverable zip.
- Do not publish loose sidecar files such as `main.diff`, `main_next_scope.md`, or separate packet folders as deliverables; if those aids are needed, include them inside the zip.
- Keep Quant packet build artifacts under the ignored `tmp\expert_packets\` area inside `E:\Code\Quant` rather than creating additional sibling folders under `E:\Code`.
- The zip remains advisory evidence only and does not authorize execution, provider ingestion, data generation, ranking/scoring, alerts, broker/order paths, or dashboard runtime scope widening.
- Before any expert handoff, approval gate, execution packet, or closure report, complete or reference the Ship-Fast Decision Gate from `docs/templates/ship_fast_decision_gate.md` and answer exactly one next decision before expanding into governance.
- Expert handoffs must use `docs/templates/ship_fast_expert_handoff_v0.md`: one question, current delta, evidence needed, forbidden scope, max 3 preconditions, max 3 stop rules, and one-line next action.
- Each expert/review/execution/closure artifact must declare exactly one mode: `ADVISORY_REVIEW`, `APPROVAL_GATE`, `EXECUTION_PACKET`, or `CLOSURE_REPORT`; no artifact may use more than one mode.
- If an expert report predates current truth, prepend: `Superseded on authorization status by <RoundID>; still valid only for guardrails.`
- Expert and reviewer outputs must not design downstream architecture unless it changes the immediate decision.

## 8. Definition of Done
- Code implemented with acceptance criteria met.
- Tests and smoke checks pass.
- A task remains `Incomplete` if proof it works is missing, even when code changes are finished.
- Docs updated (`docs/...` and `decision log.md`).
- Milestone review gate passes.
- Operational impact and rollback path are documented.

## 9. Observability and Reporting (Mandatory)
- Worker reports and SAW packets are evidence artifacts, not the default chat response.
- Final chat responses use at most four short plain-language lines: `Status`, `Why`, `Next`, and `Decision needed`.
- Lead with the practical result or blocker. Do not lead with internal workflow metadata.
- If requested execution, code, tests, provider access, commit, validation, or data output was not performed, state that plainly in `Status` or `Why` without exposing internal outcome enums.
- Do not lead with numbered command logs, subagent chatter, SAW internals, or generic activity summaries.
- Do not say work is docs-only unless the requested work was docs-only or execution was explicitly rejected/blocked.
- Hide `Outcome`, `Round`, `Progress`, `Confidence`, ship-gate labels, SAW internals, hashes, absolute paths, file allowlists, command logs, and accountability fields unless the user asks for the artifact or evidence.
- When the user asks for approval text, return only the pasteable approval block.
- Detailed validation remains in the worker report or SAW artifact. Chat includes only the evidence needed to make the next decision.

## 10. Self-Learning Feedback Loop (Mandatory)
- Source of truth: `docs/lessonss.md`.
- At session start for the relevant project: review recent lessons before proposing a plan.
- After each execution/review round: append one lesson entry with:
  - Date
  - Mistake or miss
  - Root cause
  - Fix applied
  - Guardrail for next time
  - Evidence paths (`.py`, `.md`, test output)
- If the same mistake repeats, promote the guardrail into this file (`AGENTS.md`) in the same milestone.

## 11. Plan Response Contract (Mandatory for Every Plan Request)
Every plan response must be concise and decision-oriented:
- State the recommended next action first.
- Separate high-confidence items from unknowns.
- Name P0/P1 risks before implementation.
- Name the exact files expected to change.
- Include forbidden scope when scope creep is likely.
- Use the Top-Down Snapshot only when the user asks for a formal plan or when multi-stream coordination is actually needed.
- Planning must not become the final report format.
- Canonical sample format lives in `docs/templates/plan_snapshot.txt`, but final answers use Section 9.

## 12. SAW: Subagents After Work (Mandatory)
SAW must run after each work round (even docs-only rounds):
- SAW reconciliation/report publication is terminal for the round and does not recursively trigger another SAW round.
- Exception: if the user explicitly requests a test-only rerun and explicitly waives SAW for that round, SAW may be skipped for that single round; still report test evidence.
- Ship-fast low-risk docs/template/protocol sync may use Thin SAW: one scope check, one forbidden-action scan, one evidence check, and one next-action line.
- Full Reviewer A/B/C SAW remains mandatory for code, tests, runtime, provider access, data output, high-risk work, or phase-end closeout.
- If SAW cannot select one next action, publish `SAW Verdict: BLOCK` with max 3 blockers.
1. Implementer pass
   - Owned files, acceptance checks, and non-destructive constraints.
2. Reviewer A/B/C pass (independent from implementer ownership)
   - Reviewer A: strategy correctness and regression risks.
   - Reviewer B: runtime and operational resilience.
   - Reviewer C: data integrity and performance path.
   - Record ownership check: implementer and reviewers must be different agents; include this check in the SAW report.
   - Before the final repair loop, preflight terminal Reviewer A/B/C capacity. If a required terminal rerun cannot be reserved, publish `SAW Verdict: BLOCK` immediately and do not imply closure from local machine evidence.
3. Reconciliation pass
   - Fix all Critical/High findings in current-round scope.
   - For inherited out-of-scope Critical/High findings, carry them in `Open Risks` with owner and target milestone, and request explicit user acceptance before milestone close if they remain unresolved.
   - Exploratory hypothesis rounds may use `ADVISORY_PASS` when:
     - all implementation checks and runtime/tests pass,
     - no in-scope Critical/High findings remain, and
     - remaining failed checks are explicitly classified as design-constraint discoveries (not execution defects).
   - `ADVISORY_PASS` must still include `Open Risks`, evidence, and explicit `Next action`.
4. SAW report format
   - `SAW Verdict: PASS/BLOCK/ADVISORY_PASS`
   - Findings table (Severity, Impact, Fix, Owner, Status)
   - Hierarchy Confirmation stamp (`Approved | Session | Trigger | Domains`)
   - Document Changes Showing: path + change summary + reviewer status
   - Document sorting order is maintained in `docs/checklist_milestone_review.md`.
5. Final-response rule
   - SAW detail is evidence, not the primary final answer.
   - SAW is an evidence artifact only. It must never be the primary final-answer skeleton.
   - The final answer must begin with the Ship-Fast PM Brief from Section 9.
   - Include SAW details only under `Validation / evidence` or as an evidence artifact path.
   - A verbose numbered SAW/logsheet cannot be the primary final response.

### 12.1 Post-worker GitHub Actions / SAW Checks
Post-worker GitHub Actions / SAW checks are read-only evidence wrappers. They may validate worker-report v2 shape, changed-file allowlists, YAML/Markdown hygiene, and SAW evidence placement. They must not use secrets, provider access, WRDS, runtime/data output, or repair edits without a separate approved round.

Quant vendors the post-worker SAW workflow locally because the reusable source workflow lives in private meta-harness and this repo is public. Keep the workflow aligned with meta-harness during explicit sync rounds only.

## 13. Skill Hooks (Mandatory)
- Call `$saw` (`.codex/skills/saw/SKILL.md`) for SAW rounds and reporting structure.
- Call `$research-analysis` (`.codex/skills/research-analysis/SKILL.md`) when plan confidence should be backed by external research evidence.
- Harness workflow skills/templates: use `scope-selector` before choosing bounded work, `expert-context-packer` before external/specialist review, then reconcile via `worker_done_contract`, `expert_reconciliation_matrix`, `stream_contract`, and `harness-feedback` when repeated workflow friction appears.
- Optional trigger-based skills (not mandatory on day 1):
  - `$se-executor` (`.codex/skills/se-executor/SKILL.md`) for software-engineering execution rigor on multi-file/high-risk changes.
  - `$architect-review` (`.codex/skills/architect-review/SKILL.md`) for architecture/coupling/scaling/security tradeoff reviews.
- Trigger policy for optional skills:
  - Invoke by trigger (`high complexity`, `architecture-impacting change`, `handoff risk`, or `elevated operational risk`), not by default.
  - If the same trigger recurs for `>= 2` rounds in the same milestone/session, propose upgrading that skill to mandatory for the milestone and request explicit user approval before enforcing.
- Project-init hierarchy confirmation policy (driven by shared skill templates):
  - confirm once per project session (hard stop before execution)
  - retrigger only when a new domain appears or user explicitly says `change hierarchy` / `new scope`
  - if in-thread confirmation stamp is missing during non-interactive reviewer passes, use persisted fallback from `docs/spec.md` + active `docs/phase*-brief.md`, mark `FallbackSource`, and request explicit reconfirmation at the next interactive planning step
- Research workflow requirements:
  - Pull/read relevant PDFs from `docs/research/`.
  - Analyze core methodology and key findings.
  - Cross-reference against existing `researches*.md` files for novel deltas.
  - End with one-line logic chain and one-line explicit formula summary.
- Skill closure tokens (when invoked):
  - `$saw`: must output `SAW Verdict: PASS/BLOCK`; if `BLOCK`, include `Open Risks` and `Next action`.
  - `$se-executor`: must output `Verdict: PASS/BLOCK`; if `BLOCK`, include failed checks, `Open Risks`, and `Next action`.
  - `$research-analysis`: must output `Verdict: PASS/BLOCK`; if `BLOCK`, include `Open Risks` and `Next verification step`.
  - `$architect-review`: must output `Verdict: PASS/BLOCK`; if required architecture inputs are missing, output `BLOCK` with required inputs in `Open Risks`.
- Invocation-close packet (required for every invoked skill):
  - `RoundID`, `ScopeID`, `ChecksTotal`, `ChecksPassed`, `ChecksFailed`, `Verdict`.
  - Emit as single machine-check line:
    - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
  - Validate using:
    - `.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
  - Any missing packet field forces `Verdict: BLOCK` for closure.
- Skill-output boundary:
  - Skill closure tokens are internal validation evidence.
  - They do not replace the Section 9 PM brief.
  - If requested work was code/test/provider/commit/validation, the worker accountability block must state what was actually performed.
  - Silent downgrade from execution, code, test, provider_probe, commit, validation, or data_output work to docs-only work is forbidden; use `Outcome: REJECTED` or `PARTIAL_WITH_EXPLICIT_SCOPE` and name the blocker.
- Evidence-link minimums by skill:
  - `$se-executor`: every task must have `TaskID` and linked `EvidenceID`; unlinked task => `BLOCK`.
  - `$research-analysis`: every high-confidence claim must include `ClaimID` + source locator (`SourceID`, page/section); missing locator => `BLOCK`.
  - `$architect-review`: every option must include normalized score components (`impact`, `risk`, `effort`, `maintainability`) and computed `OptionScore`; missing score components => `BLOCK`.
- Validator tokens (required when invoked):
  - `$saw`: emit `SAWBlockValidation: PASS/BLOCK` from `validate_saw_report_blocks.py`.
  - `$se-executor`: emit `EvidenceValidation: PASS/BLOCK` from `validate_se_evidence.py`.
  - `$research-analysis`: emit `ClaimValidation: PASS/BLOCK` from `validate_research_claims.py`.
  - `$architect-review`: emit `CalibrationValidation: PASS/DRIFT/INSUFFICIENT` from `validate_architect_calibration.py`.

## 14. Interactive Review Protocol (Plan/Code Review Requests)
When the user asks for review-mode analysis (architecture/code quality/tests/performance), follow this sequence:
1. Start mode gate (required)
   - Ask user to pick exactly one:
     - `BIG CHANGE`: work section-by-section (`Architecture -> Code Quality -> Tests -> Performance`) with at most 4 top issues per section.
     - `SMALL CHANGE`: one issue/question per section.
   - If mode is already provided by parent/orchestrator (for example SAW reviewer passes), inherit that mode and do not ask the user again.
2. Per-issue response contract (required)
   - Number each issue (`1, 2, 3...`) and label options with letters (`A, B, C...`).
   - Include concrete file references for findings (`path:line`).
   - Provide 2-3 options (include `do nothing` when reasonable).
   - For each option, include: implementation effort, risk, impact on other code, and maintenance burden.
   - Put recommended option first and explain why in one line mapped to user preferences.
   - Ask explicit user confirmation before implementation.
3. Interaction cadence (required)
   - Pause after each section and ask for feedback before moving to the next section.
   - Do not assume user priorities for timeline or scope without explicit confirmation.
