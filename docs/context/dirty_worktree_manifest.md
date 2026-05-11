# Dirty Worktree Classification Manifest

Status: Current classification artifact
Date: 2026-05-11
Workspace: `E:\Code\Quant`
Branch: `codex/optimizer-core-structured-diagnostics`
Authority: advisory-only worktree classification. This file does not authorize staging, deletion, revert, provider ingestion, dashboard redesign, scoring, ranking, alerting, broker behavior, live trading, or scope widening by itself.

## Purpose

Classify the broader dirty worktree into reviewable buckets before any staging or cleanup action. This manifest is the handoff artifact for the next staging plan.

## Current Local Evidence

- `git diff --name-only` observed `36` tracked modified files.
- `git ls-files --others --exclude-standard` observed `350` untracked files after this manifest was created and context validation was rerun.
- Commit 1 (`a2d2d2a`, `.gitignore`) ignored root temp/runtime/vendor artifacts and reduced the visible untracked count to `346`.
- Prior inventory used `345` untracked files; after Commit 1 the remaining visible drift is `+1` and sits inside the docs/source staging surface, not the ignore bucket.
- `scripts/build_context_packet.py --validate` passed in the immediately preceding planning pass.
- No files were staged, deleted, reverted, or cleaned as part of this manifest write.

## Buckets

- `accepted-source`: source, tests, docs, fixtures, policies, and static data intended to become reviewable committed work after validation.
- `generated-evidence`: generated context, smoke, capture, audit, or profiling artifacts. Keep only when referenced by docs/tests or needed for evidence.
- `quarantine`: preserved out-of-scope diffs or notes that should not be merged into active runtime behavior without a separate approval.
- `ignore`: local temp/runtime/vendor artifacts that should not be staged.

## Tracked Modified Files

### accepted-source

```text
.gitignore
README.md
core/data_orchestrator.py
dashboard.py
views/optimizer_view.py
strategies/optimizer.py
data/updater.py
scripts/build_context_packet.py
scripts/check_user_tickers.py
scripts/parameter_sweep.py
scripts/release_controller.py
backtests/optimize_phase16_parameters.py
tests/conftest.py
tests/test_build_context_packet.py
tests/test_dashboard_sprint_a.py
tests/test_strategy.py
docs/prd.md
docs/spec.md
docs/notes.md
docs/lessonss.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/phase_brief/dashboard-ui-fixes-sprint-a.md
data/registry/candidate_events.jsonl
data/registry/candidate_snapshot.json
```

### generated-evidence

```text
docs/context/bridge_contract_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/impact_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/observability_pack_current.md
docs/context/post_phase_alignment_current.md
docs/context/current_context.json
docs/context/current_context.md
docs/context/e2e_evidence/manual_capture_alerts.json
docs/context/e2e_evidence/manual_capture_queue.json
```

## Untracked Files By Group

| Bucket | Group | Count | Staging Guidance |
| --- | --- | ---: | --- |
| accepted-source | `docs/architecture` | 71 | Stage by phase or policy family after doc-review pass. |
| accepted-source | `docs/saw_reports` | 36 | Stage with matching phase/source changes after SAW validation. |
| accepted-source | `docs/handover` | 34 | Stage with matching phase/source changes. |
| accepted-source | `tests` | 33 source tests plus ignored `tests/pytest_out.txt` | Stage test files with owned source buckets only. |
| accepted-source | `v2_discovery` | 28 | Stage as a dedicated V2 discovery bucket after focused tests. |
| accepted-source | `data/fixtures` | 20 | Stage with manifest/hash checks. |
| accepted-source | `data/registry` | 13 | Stage with registry report validation. |
| accepted-source | `opportunity_engine` | 12 | Stage as opportunity-engine bucket after focused tests. |
| accepted-source | `data/discovery` | 7 | Stage with discovery-policy docs and manifest checks. |
| accepted-source | `data/candidate_cards` | 4 | Stage with candidate-card tests and manifest hash checks. |
| accepted-source | `strategies` (`optimizer_diagnostics.py`, `portfolio_universe.py`, `scanner.py`) | 3 | Stage with optimizer/portfolio/scanner-focused tests. |
| accepted-source | `scripts/strong_buy_scan.py` | 1 | Stage only if paired with tests or docs proving boundary. |
| accepted-source | `utils/process.py` | 1 | Stage with process utility tests. |
| accepted-source | `views/page_registry.py` | 1 | Stage with dashboard page-registry tests. |
| accepted-source | `PRD.md`, `PRODUCT_SPEC.md` | 2 | Stage with docs-as-code changes. |
| accepted-source | `docs/research/g7_1c_*.md` | 1 | Stage with research/source-audit docs. |
| generated-evidence | `docs/context/e2e_evidence` | 73 | Stage only evidence files referenced by SAW/context docs. |
| generated-evidence | `data/test_audit.json` | 1 | Stage only if referenced by a validation artifact. |
| generated-evidence | `docs/architect/profile_outcomes.csv` | 1 | Stage only if referenced by architecture review evidence. |
| quarantine | `docs/quarantine` (`patch` + `note`) | 2 | Preserve; do not merge quarantined runtime diff without separate approval. |
| ignore | `SPGlobal_Avantax,Inc._SecurityDetail_19-Mar-2026.xlsx` | 1 | Do not stage; add ignore/quarantine decision before cleanup. |
| ignore | `_optimizer_diff_tmp.txt` | 1 | Do not stage; delete only after explicit cleanup approval. |
| ignore | `_untracked_tmp.txt` | 1 | Do not stage; delete only after explicit cleanup approval. |
| ignore | `backtest_results.json` | 1 | Do not stage; already expected runtime output. |
| ignore | `tests/pytest_out.txt` | 1 | Do not stage; generated test output. |

## High-Risk Diff Verdict

### `strategies/optimizer.py`

Classification: `accepted-source`.

Verdict: the current `strategies/optimizer.py` diff is classified as the accepted Optimizer Core Structured Diagnostics implementation, including `OptimizationMethod`, diagnostic-returning methods, SLSQP status capture, and feasibility checks.

Boundary: this is not the quarantined lower-bound/SLSQP policy diff. The quarantined lower-bound policy remains preserved under `docs/quarantine` and must not be merged as active optimizer policy without a separate approved implementation round.

## Required Reconciliation Before Staging

1. Reconcile the current `346` untracked-file count against the prior `345` inventory before committing docs canon.
2. Confirm each generated-evidence file is referenced by a SAW report, context packet, or evidence matrix before staging.
3. Keep `ignore` artifacts unstaged; update `.gitignore` only for recurring runtime/temp artifacts after inspection.
4. Stage `accepted-source` in logical buckets, not as one broad commit.
5. Run focused tests for each bucket before staging.
6. Run context rebuild and validation after context/docs buckets.
7. Run SAW/review before claiming milestone closure.

## Suggested Staging Buckets

```text
1. process-safety-runtime
   utils/process.py
   dashboard.py
   data/updater.py
   scripts/parameter_sweep.py
   scripts/release_controller.py
   backtests/optimize_phase16_parameters.py
   tests/test_process_utils.py

2. optimizer-diagnostics-and-view
   strategies/optimizer.py
   strategies/optimizer_diagnostics.py
   core/data_orchestrator.py
   views/optimizer_view.py
   tests/test_optimizer_core_policy.py
   tests/test_optimizer_view.py
   tests/test_data_orchestrator_portfolio_runtime.py

3. portfolio-universe-and-dashboard
   strategies/portfolio_universe.py
   views/page_registry.py
   tests/test_portfolio_universe.py
   tests/test_dash_1_page_registry_shell.py
   tests/test_dash_2_portfolio_ytd.py
   tests/test_dashboard_sprint_a.py

4. opportunity-engine-and-candidate-cards
   opportunity_engine/
   data/discovery/
   data/candidate_cards/
   tests/test_g8_supercycle_candidate_card.py
   tests/test_g8_1_supercycle_discovery_intake.py
   tests/test_g8_1b_pipeline_first_discovery_scout.py
   tests/test_g8_2_system_scouted_candidate_card.py

5. v2-discovery-fixtures-and-registry
   v2_discovery/
   data/fixtures/
   data/registry/
   tests/test_v2_*.py
   tests/test_g4_*.py
   tests/test_g5_*.py
   tests/test_g6_*.py
   tests/test_g7_*.py

6. governance-docs-and-context
   docs/architecture/
   docs/handover/
   docs/saw_reports/
   docs/context/
   docs/phase_brief/
   docs/prd.md
   docs/spec.md
   docs/notes.md
   docs/lessonss.md
   docs/decision log.md
   README.md
   PRD.md
   PRODUCT_SPEC.md
```

## Minimum Verification Matrix

```text
.venv\Scripts\python -m pytest tests\test_process_utils.py -q
.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py tests\test_optimizer_view.py tests\test_data_orchestrator_portfolio_runtime.py -q
.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py -q
.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1_supercycle_discovery_intake.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q
.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Open Risks

- Count drift remains unresolved until the next inventory pass explains the current `346` untracked files versus the prior `345`.
- Generated evidence may include obsolete smoke logs and should not be staged blindly.
- Full repository regression previously timed out in a dashboard architecture safety round; a longer window is required for phase-close proof.
- Dirty worktree breadth makes one-shot staging high risk; staged buckets should stay logically small and independently verified.

## Next Action

Proceed to the staging plan: reconcile the count drift, then stage only the first logical bucket after focused verification.
