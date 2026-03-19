# Milestone Review Checklist

**Agent Instruction**: Act as a Senior Code Reviewer. Check the following before marking Phase [N] complete.

## 1. Code Quality
- [ ] **Vectorization**: Are there `for` loops iterating over DataFrames? (Reject if yes).
- [ ] **Safety**: Are file writes atomic? (Reject if direct write to `.parquet`).
- [ ] **Error Handling**: Does the code handle `NaN`, Empty DataFrames, or API failures gracefully?

## 2. Testing
- [ ] **Unit Tests**: Do `tests/` cover the new logic?
- [ ] **Integration**: Does `launch.py` still boot the app successfully?
- [ ] **Edge Cases**: What happens if the internet disconnects?

## 3. Documentation
- [ ] **Decision Log**: Is `decision log.md` updated with trade-offs?
- [ ] **Runbook**: Are there new ops commands (e.g., `python build_map.py`)?
- [ ] **Formula Log**: Are all new/changed formulas and derivations logged in `docs/notes.md` with source `.py` paths?
- [ ] **Phase Handover**: Is `docs/handover/phase<NN>_handover.md` published with PM summary + logic chain + formula register?
- [ ] **Lessons Loop**: Is `docs/lessonss.md` updated with date, mistake, root cause, fix, and guardrail?

## 4. Phase-End Closure (Mandatory at phase completion)
- [ ] **Git Sync**: Are all evidence artifacts committed and pushed to origin/main? (`git status --porcelain` empty AND `git log origin/main..HEAD --oneline` empty)
- [ ] **Subagent E2E Replay**: Did implementer and Reviewer B independently run an end-to-end phase path?
- [ ] **Full Regression**: Did `.venv\Scripts\python -m pytest -q` pass for the phase-close candidate?
- [ ] **Runtime Smoke**: Did one app boot smoke path pass (`launch.py` or headless `streamlit run app.py`)?
- [ ] **Data Integrity**: Are atomic write paths and artifact freshness/row-count sanity checks recorded with evidence artifact paths and observed values?
- [ ] **New Context Packet**: Is `/new` bootstrap summary prepared with `what was done`, `what is next`, `ConfirmationRequired: YES`, and `NextPhaseApproval: PENDING`?
- [ ] **Context Artifact Refresh**: Did `.venv\Scripts\python scripts/build_context_packet.py` refresh `docs/context/current_context.json` and `docs/context/current_context.md`, and did `.venv\Scripts\python scripts/build_context_packet.py --validate` pass?

## 5. Document Sorting (GitHub-optimized)
- [ ] Present changed docs in this order:
  1. `AGENTS.md`
  2. `docs/prd.md`, `docs/spec.md`
  3. `docs/phase*-brief.md` (numeric phase order)
  4. `docs/handover/*.md` (phase order)
  5. `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`
  6. `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md`
  7. `docs/research/*.md` (date/name ascending)

## 6. Manual Capture Policy (Strict Enforcement)
- **Rule 1 (No Mockups):** E2E evidence only accepts `REAL_CAPTURE` and script `.log`. AI-generated mockups are prohibited.
- **Rule 2 (Trigger):** Manual screenshot requests trigger only when automated script gates pass and required real captures are missing.
- **Rule 3 (SLA):** Missing manual evidence triggers warning at 15 minutes and escalates to `BLOCK` after 30 minutes.
- **Rule 4 (Verdict Gate):** Missing `REAL_CAPTURE` enforces `Machine PASS + Manual Pending`; milestone cannot close as `PASS`.
- **Rule 5 (Drop Zone Loop):** Evidence intake must use watcher-managed drop zones so `index.md`, queue, and alerts stay synchronized.

**Verdict**: [PASS / Manual Pending / BLOCK]
