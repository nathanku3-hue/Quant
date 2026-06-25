# Dirty Worktree Classification Manifest

Status: Current local intake artifact
Date: 2026-05-26
Workspace: `E:\Code\Quant`
Branch: `codex/optimizer-core-structured-diagnostics`
Authority: advisory-only worktree classification. This file does not authorize staging, deletion, revert, provider ingestion, dashboard redesign, scoring, ranking, alerting, broker behavior, live trading, expanded boot-preflight implementation, or scope widening by itself.

## Anchor State

Current remote anchor:

```text
37abd445bdee5ab771c85dc544c9ec1489b9cee3 Add boot-core preflight contract v0
```

Pushed anchors:

```text
8716c51781d8524de4147cf42f17e52466913de4 Add research-validity runner v0 evidence gate
c78d024618bb5553053e26b710904593b55492c6 Anchor research-validity runner v0 context
37abd445bdee5ab771c85dc544c9ec1489b9cee3 Add boot-core preflight contract v0
```

Verification at reconciliation:

```text
HEAD == origin/codex/optimizer-core-structured-diagnostics == 37abd445bdee5ab771c85dc544c9ec1489b9cee3
git diff --cached --name-status == empty
boot-core tracked file diff == empty
```

Boot-core pushed files now treated as GitHub truth:

```text
BOOT.md
launch.py
core/boot_status.py
scripts/boot_preflight.py
tests/test_boot_preflight.py
tests/test_boot_status_contract.py
docs/architecture/boot_preflight_contract.md
docs/context/boot_status_current.schema.json
```

Boot-core phase-2 residue:

```text
Classification: phase-2 expanded preflight/data-readiness work; not a blocking boot-core bug fix.
Action: reset from worktree after snapshot.
Preserved at: E:\Code\quant_dirty_snapshots\20260526_post_boot_core_reconciliation\boot_core_phase2_residue.patch
Additional core/boot_status.py residue preserved at: E:\Code\quant_dirty_snapshots\20260526_post_boot_core_reconciliation\core_boot_status_second_residue.patch
Reappeared core/boot_status.py residue preserved at: E:\Code\quant_dirty_snapshots\20260526_post_boot_core_reconciliation\core_boot_status_reappeared_residue.patch
Earlier residue snapshot: E:\Code\quant_dirty_snapshots\20260526_boot_core_post_commit_residue\boot_phase2_residue.patch
```

## Intake Rule

Do not implement expanded boot-preflight/data-readiness, stage files, commit files, delete files, clean files, stash files, or treat local dirty files as GitHub truth until this classification is reviewed.

## Bucket Definitions

- `A expanded boot-preflight/data-readiness candidate`: files that may belong to the next narrow data-readiness/preflight round.
- `B context/governance update`: files that document current state or policy.
- `C local evidence/archive only`: audit packets, generated evidence, review bundles, and archives that should not normally be committed.
- `D generated noise/delete-ignore`: pid/stdout/stderr/status/log/scratch outputs and timestamp-only noise.
- `E unrelated future work`: source/test/docs work outside the expanded preflight/data-readiness bucket.
- `F unknown/leave unstaged`: files whose role is unclear or patch bundles requiring explicit review.

## Bucket A - Expanded Boot-Preflight/Data-Readiness Candidate

Remaining dirty/untracked files that can plausibly belong to the next narrow slice:

```text
core/data_readiness_gate.py
scripts/run_data_readiness_gate.py
tests/test_data_readiness_gate.py
tests/test_data_readiness_gate_write_guard.py
tests/test_provider_ports.py
docs/architecture/data_readiness_gate_v0.md
docs/context/data_artifact_taxonomy_current.json
docs/context/portfolio_allocation_route_contract_v0.json
```

Potential integration files, currently clean after residue reset and not staged:

```text
core/boot_status.py
scripts/boot_preflight.py
tests/test_boot_preflight.py
```

If the next slice needs those integration files, reapply only the reviewed data-readiness portions from:

```text
E:\Code\quant_dirty_snapshots\20260526_post_boot_core_reconciliation\boot_core_phase2_residue.patch
```

Do not include in the first expanded data-readiness slice without explicit approval:

```text
scripts/governance_preflight.py
tests/test_boot_preflight_governance.py
docs/architecture/governance_boundary_policy.md
docs/context/boot_status_current.json
docs/saw_reports/saw_data_readiness_gate_v0_20260526.md
dashboard.py
views/page_registry.py
tests/test_dash_1_page_registry_shell.py
```

## Bucket B - Context/Governance Documentation

Tracked context and governance docs:

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/lessonss.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/context/bridge_contract_current.md
docs/context/current_context.json
docs/context/current_context.md
docs/context/dirty_worktree_manifest.md
docs/context/done_checklist_current.md
docs/context/impact_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/observability_pack_current.md
docs/context/planner_packet_current.md
docs/context/post_phase_alignment_current.md
docs/saw_reports/saw_research_validity_runner_v0_20260526.md
```

Untracked context/governance docs and reports:

```text
BOOT0_SHARED_BOOT_STATUS_RECONCILIATION_20260526.md
PRODUCT_UX_RECONCILIATION_20260526.md
docs/context/saw_frontend_ui_saved_replay_source_selector_20260514.md
docs/handover/phase65_rule100_dynamic_ui_replay_ytd_handover.md
docs/saw_reports/*.md
```

Context/governance warning:

```text
Do not create a broad docs/context-only commit from the current dirty docs.
The diff is mixed, large, and includes stale local context.
If a classification commit is needed, stage only this manifest after review.
```

## Bucket C - Local Evidence/Archive Only

Root packet and implementation archives:

```text
BOOT0_SHARED_BOOT_STATUS_PACKAGE_20260526.zip
governance_gate_v0_implementation_20260526.zip
reboot_expert_packet_20260526_boot_preflight_v0.zip
```

Expert packets and extracted packet folders:

```text
docs/context/e2e_evidence/data_engineering_market_integrity_packet_20260526.zip
docs/context/e2e_evidence/data_engineering_market_integrity_packet_20260526/
docs/context/e2e_evidence/governance_risk_boundary_packet_20260526.zip
docs/context/e2e_evidence/governance_risk_boundary_packet_20260526/
docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526.zip
docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526/
docs/context/e2e_evidence/quant_research_backtest_validity_packet_20260526.zip
docs/context/e2e_evidence/quant_research_backtest_validity_packet_20260526/
docs/context/e2e_evidence/reboot_expert_packet_20260526.zip
docs/context/e2e_evidence/reboot_expert_packet_20260526/
docs/context/e2e_evidence/reboot_expert_packet_20260526_v2/
docs/context/e2e_evidence/rule100_softmax_v1_expert_packet_20260512.zip
docs/context/e2e_evidence/rule100_softmax_v1_expert_packet_20260512/
```

Generated evidence JSONs and smoke outputs to archive only unless referenced by a committed evidence policy:

```text
docs/context/e2e_evidence/*smoke.json
docs/context/e2e_evidence/*audit*.json
docs/context/e2e_evidence/portfolio_replay_context_diagnostics_current.json
docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json
docs/context/e2e_evidence/lifecycle_churn_weight_8509_smoke.json
docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json
docs/context/e2e_evidence/lifecycle_decision_audit_20260513.json
docs/context/e2e_evidence/lifecycle_decision_audit_pre_rule100_v0_20260512.json
docs/context/e2e_evidence/portfolio_ytd_return_fix_8509_smoke.json
docs/context/e2e_evidence/rule100_method_label_8509_smoke.json
```

Packet/review reports that are archive-only unless explicitly promoted:

```text
docs/saw_reports/saw_reboot_expert_packet_20260526.md
docs/saw_reports/saw_quant_research_backtest_validity_packet_20260526.md
docs/saw_reports/saw_product_ux_ready_workflow_packet_20260526.md
docs/saw_reports/saw_data_engineering_market_integrity_packet_20260526.md
docs/saw_reports/saw_governance_risk_boundary_packet_20260526.md
research_backtest_runner_v0_codex_prompt.md
research_validity_contract.md
```

## Bucket D - Generated Noise/Delete-Ignore Candidate

Root generated hash/scratch files:

```text
.boot0a_hash_after.csv
.boot0a_hash_before.csv
```

Untracked runtime/process logs:

```text
docs/context/e2e_evidence/*_pid.txt
docs/context/e2e_evidence/*_stdout.txt
docs/context/e2e_evidence/*_stderr.txt
docs/context/e2e_evidence/*_status.json
docs/context/e2e_evidence/debug_import_8531_stdout.txt
docs/context/e2e_evidence/debug_import_8531_stderr.txt
```

Tracked timestamp-only noise:

```text
docs/context/e2e_evidence/manual_capture_alerts.json
docs/context/e2e_evidence/manual_capture_queue.json
```

Cleanup rule:

```text
Preview with git clean -nd before deleting anything.
No deletion was performed in this reconciliation round.
Do not run broad git clean -fdx.
Delete only explicit generated-noise paths after review and after preserving an external snapshot.
```

## Bucket E - Unrelated Future Work

Backend/data/dashboard/optimizer/replay work outside the expanded preflight/data-readiness staging set:

```text
core/data_orchestrator.py
dashboard.py
data/portfolio_lifecycle_log.py
opportunity_engine/candidate_card_schema.py
scripts/build_context_packet.py
scripts/pit_lifecycle_replay.py
scripts/build_strategy_replay_artifact.py
scripts/build_synthetic_r3000_universe.py
scripts/rule100_softmax_v1_audit.py
scripts/rule100_softmax_v1_1_audit.py
strategies/adapter.py
strategies/adapter_registry.py
strategies/optimizer.py
strategies/portfolio_universe.py
strategies/rule100_adapter.py
strategies/rule100_softmax.py
strategies/rule100_softmax_v1_1.py
strategies/strategy_replay.py
views/detail_view.py
views/optimizer_view.py
views/discovery_view.py
views/strategy_view.py
```

Candidate card/data changes outside the preflight slice:

```text
data/candidate_cards/MSFT_supercycle_candidate_card_v0.json
data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json
data/candidate_cards/MU_supercycle_candidate_card_v0.json
data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json
```

Unrelated or later-slice tests:

```text
tests/test_build_context_packet.py
tests/test_dash_1_page_registry_shell.py
tests/test_dash_2_portfolio_ytd.py
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_optimizer_core_policy.py
tests/test_optimizer_view.py
tests/test_pinned_universe.py
tests/test_portfolio_universe.py
tests/test_policy_target_timeline_apptest.py
tests/test_position_lifecycle.py
tests/test_replay_non_cash_closed.py
tests/test_rule100_softmax.py
tests/test_rule100_softmax_v1_1.py
tests/test_strategy_adapter.py
tests/test_strategy_replay.py
tests/test_strategy_replay_artifact.py
tests/test_strategy_replay_coverage.py
```

Later-slice docs:

```text
docs/strategy_stream_v1_1_contract.md
```

## Bucket F - Unknown / Leave Unstaged

Patch bundles requiring explicit review before use:

```text
boot_preflight_v0.patch
boot0_shared_boot_status_contract_20260526.patch
governance_gate_v0.patch
```

Root operator note needing an explicit role decision:

```text
quant.md
```

Unknown directory reported in previous cleanup preview:

```text
youtube_algorithm_flag/
```

Leave unknown paths untouched until their origin is confirmed.

## Proposed Expanded-Preflight/Data-Readiness v0 Staging Set

Do not stage yet. Proposed next staging set:

```text
core/data_readiness_gate.py
scripts/run_data_readiness_gate.py
tests/test_data_readiness_gate.py
tests/test_data_readiness_gate_write_guard.py
tests/test_provider_ports.py
docs/architecture/data_readiness_gate_v0.md
docs/context/data_artifact_taxonomy_current.json
docs/context/portfolio_allocation_route_contract_v0.json
```

Optional integration files only if the next implementation explicitly wires data readiness into boot status/preflight:

```text
core/boot_status.py
scripts/boot_preflight.py
tests/test_boot_preflight.py
docs/architecture/boot_preflight_contract.md
docs/context/boot_status_current.schema.json
```

Do not stage:

```text
docs/context/boot_status_current.json
docs/saw_reports/saw_data_readiness_gate_v0_20260526.md
scripts/governance_preflight.py
tests/test_boot_preflight_governance.py
docs/architecture/governance_boundary_policy.md
dashboard.py
views/page_registry.py
tests/test_dash_1_page_registry_shell.py
packet zips
patch bundles
hash residue
runtime pid/stdout/stderr/status files
```

## Required Pre-Staging Checks

Before any expanded-preflight/data-readiness staging:

```text
git status --short --branch
git diff --name-status
git diff --stat
git diff --cached --name-status
```

Then stage only by explicit path. Never use `git add .`.

Before any commit:

```text
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
```

## Subagent Classification Evidence

```text
Boot-core residue classifier: PASS
Bucket A classifier: PASS from prior sidecar result
Non-implementation classifier: PASS from prior sidecar result
One attempted sidecar failed externally with 403 insufficient balance and made no changes.
```

## Open Risks

- The worktree remains dirty and is not safe-boot truth.
- Expanded data-readiness integration needs explicit staging approval before reapplying boot-preflight residue.
- Broad docs/context diffs contain stale or mixed context; do not commit them as a blanket docs-only bucket.
- Local packet archives and extracted packet folders are valuable evidence but should be archived outside the product repo unless an explicit evidence-retention policy says otherwise.
- Generated pid/stdout/stderr/status files should be deleted or ignored only after explicit cleanup approval.

## Next Action

Review this refreshed classification, then approve the exact expanded-preflight/data-readiness v0 staging set or request reclassification of specific paths.
