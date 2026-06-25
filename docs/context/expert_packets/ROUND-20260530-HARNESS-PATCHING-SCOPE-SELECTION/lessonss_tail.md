- Root cause: Terminal Zero's dashboard, replay, candidate-card, and portfolio vocabulary share action-shaped terms, so UX review needs explicit product-boundary rails before asking workflow questions.
- Fix applied: Created a Product / UX ready-workflow packet with GitHub alignment, current truth, dashboard IA, view/test context, and explicit non-goals against recommendations, rankings, scoring, alerts, provider ingestion, and broker paths.
- Guardrail for next time: Any UX/product expert packet must ask for screen/workflow/copy decisions while explicitly forbidding product-authority expansion; include GitHub/local-truth caveats and focused UI tests.
- Evidence paths: `docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526/EXPERT_QUESTIONS.md`, `docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526/PACKET_INDEX.md`, `docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526.zip`, `docs/saw_reports/saw_product_ux_ready_workflow_packet_20260526.md`.

## 2026-05-26 Round Entry (Evidence Runners Need Output-Path and Completion Gates)
- Date: 2026-05-26
- Mistake or miss: Research-validity runner v0 initially focused on PIT/cost/benchmark math but did not fully prove evidence-output containment, atomic writes, or stale final-manifest cleanup.
- Root cause: The first implementation treated the evidence directory as a passive artifact sink, while reviewer runtime analysis correctly treated it as part of the research-validity boundary.
- Fix applied: Rejected unsafe `run_id` values, resolved evidence run directories under the cartridge output root, wrote JSON/CSV artifacts through same-directory temp files plus `os.replace`, removed stale `evidence_packet.json` before same-run rewrites, emitted final manifest last, and added focused regressions.
- Guardrail for next time: Any runner that emits evidence must test path confinement, temp-to-replace writes, final-manifest ordering, stale-manifest failure behavior, and malformed-input blocked paths before SAW closure.
- Evidence paths: `research/backtest_runner.py`, `research/evidence_schema.py`, `tests/test_research_backtest_runner.py`, `tests/test_research_evidence_schema.py`, `.venv\Scripts\python -m pytest tests\test_research_status.py tests\test_research_evidence_schema.py tests\test_research_benchmarks.py tests\test_research_backtest_runner.py tests\test_research_rule100_adapter.py tests\test_engine.py -q`.

## 2026-05-26 Round Entry (Route Smokes Need Fail-Closed Alternatives)
- Date: 2026-05-26
- Mistake or miss: The Portfolio route smoke required replay/current allocation tables even when the route rendered an explicit fail-closed replay-unavailable state.
- Root cause: The smoke contract only recognized the success table path and did not encode the page's valid unavailable-state copy.
- Fix applied: Updated the AppTest smoke to accept either role-aware replay/current allocation dataframes or the full explicit unavailable state, and restored strict preflight to run that smoke by default.
- Guardrail for next time: A boot smoke may accept a fail-closed state, but it must assert the exact visible unavailable messages; never downgrade to header-only, and never skip the route smoke in strict boot.
- Evidence paths: `tests/test_dash_1_page_registry_shell.py`, `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py::test_dash_1_portfolio_allocation_route_renders_without_overlay -q`, `.venv\Scripts\python launch.py --preflight --strict`.

## 2026-05-26 Round Entry (Runtime Boot Truth Is Not Context Documentation)
- Date: 2026-05-26
- Mistake or miss: The first shared boot-status patch treated `docs/context/boot_status_current.json` as both canonical runtime artifact and legacy compatibility path.
- Root cause: BOOT-0A mixed context-packet truth with runtime preflight truth, so tests and docs accidentally preserved the old docs/context-only path.
- Fix applied: Set `core.boot_status.DEFAULT_BOOT_STATUS_PATH` to `runtime/boot_status_current.json`, kept `docs/context/boot_status_current.json` as `LEGACY_BOOT_STATUS_PATH`, updated preflight/data write guards, and added canonical-vs-legacy tests.
- Guardrail for next time: Runtime verdicts belong under `runtime/`; docs/context may provide schemas, context packets, or temporary compatibility fallbacks, but not the canonical generated boot verdict.
- Evidence paths: `core/boot_status.py`, `scripts/boot_preflight.py`, `core/data_readiness_gate.py`, `tests/test_boot_status_contract.py`, `tests/test_boot_preflight.py`, `tests/test_data_readiness_gate_write_guard.py`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q`.

## 2026-05-26 Round Entry (Boot Preflight Commands Must Be Argv-Bounded)
- Date: 2026-05-26
- Mistake or miss: BOOT-0A initially ran `current_context.first_command` through `shell=True` and relied on entry-state Git checks for `--require-github`.
- Root cause: The preflight treated the context packet command as trusted operator text and treated GitHub alignment as a precondition rather than an after-gates proof.
- Fix applied: Parsed focused commands with `shlex`, allowed only Python `-m pytest`, rejected shell metacharacters, ran without shell, added gate timeouts, path-confined status writers, and rechecked Git after all gates in `--require-github`.
- Guardrail for next time: Any boot/control-plane command sourced from an artifact must be parsed into argv, allowlisted, timeout-bounded, and followed by a post-run mutation proof before claiming read-only alignment.
- Evidence paths: `scripts/boot_preflight.py`, `core/boot_status.py`, `tests/test_boot_preflight.py`, `tests/test_boot_status_contract.py`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q`.

## 2026-05-26 Round Entry (Boot-Status Contract Contention Must Stop Work)
- Date: 2026-05-26
- Mistake or miss: I continued reconciling Data Readiness Gate v0 after boot-status files repeatedly flipped between the user-locked `docs/context/boot_status_current.json` contract and a competing `runtime/boot_status_current.json` contract.
- Root cause: Multiple active boot/status streams were operating in the same dirty workspace, so focused tests could pass once and then fail after a concurrent or reapplied patch restored older semantics.
- Fix applied: Stopped the implementation loop, preserved the deterministic residue/import evidence, and published a SAW BLOCK instead of claiming boot readiness.
- Guardrail for next time: If a canonical boot/status path or write guard changes during verification, stop coding immediately, freeze competing streams, choose the contract explicitly, and only then rerun tests.
- Evidence paths: `core/boot_status.py`, `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `tests/test_boot_status_contract.py`, `tests/test_data_readiness_gate_write_guard.py`, `docs/saw_reports/saw_data_readiness_gate_v0_20260526.md`.

## 2026-05-26 Round Entry (Strict Boot Must Stay Fast And Governance-Exact)
- Date: 2026-05-26
- Mistake or miss: Strict boot preflight semantics drifted between packet-era assumptions and root truth: governance WARN was sometimes treated as blocking, while focused-contract execution was described as printed-only in places.
- Root cause: Boot readiness, safe-boot evidence, governance copy policy, and final GitHub proof were conflated while multiple BOOT-0A streams were active.
- Fix applied: Made governance WARN advisory/degraded, kept governance FAIL blocked, made default strict run boot-control tests, Portfolio smoke, and the focused current-context command, and kept `--require-github` as final read-only alignment proof rather than the `safe_boot` flag owner.
- Guardrail for next time: Keep verdict semantics in `core.boot_status` and producer mapping tests first; distinguish `safe_boot` from GitHub alignment proof, and test exact allowed labels separately from blocked action-shaped copy including whitespace variants.
- Evidence paths: `scripts/boot_preflight.py`, `scripts/governance_preflight.py`, `tests/test_boot_preflight.py`, `tests/test_boot_preflight_governance.py`, `docs/architecture/data_readiness_gate_v0.md`, `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py -q`, `.venv\Scripts\python launch.py --preflight --strict`.

## 2026-05-26 Round Entry (Root Evidence Beats Packet Artifacts)
- Date: 2026-05-26
- Mistake or miss: Governance Gate v0 packet artifacts and patch files were initially treated too much like implementation evidence, while live root files were still flipping under concurrent boot-control writers.
- Root cause: Multiple streams were editing `scripts/boot_preflight.py` and `tests/test_boot_preflight.py`, so a passing targeted run could become stale before strict root proof completed.
- Fix applied: Re-verified the live root after each flip, stopped background boot-preflight runners, mapped governance WARN to degraded and FAIL to blocked, made default strict execute the focused current-context contract, and separated `safe_boot` from the final `--require-github` GitHub-alignment proof.
- Guardrail for next time: If boot-control semantics change during verification, stop broad work, freeze to a single writer, rerun the root-supported commands, and label packet/zip/patch outputs as porting inputs until root preflight and tests prove them.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `scripts/governance_preflight.py`, `docs/architecture/boot_preflight_contract.md`, `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py -q`, `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json`, `.venv\Scripts\python scripts\boot_preflight.py --repo-root . --strict --json`.

## 2026-05-26 Round Entry (Post-Test Sentinels Must Prove BOOT File Stability)
- Date: 2026-05-26
- Mistake or miss: BOOT-0A could have been closed from a passing targeted test even though earlier evidence showed untracked boot files sometimes snapped back to stale semantics after verification.
- Root cause: The key files were untracked and competing BOOT streams had previously run background preflight/test processes, so a single passing test was not enough proof of live-root stability.
- Fix applied: Added before/after root sentinels for governance WARN mapping, `safe_boot`/GitHub separation, final-verdict blocking, and stale test names; reran the full BOOT-0A suite and only closed after the post-suite sentinel still matched.
- Guardrail for next time: For untracked control-plane files, treat post-test source sentinels as acceptance evidence, not optional debugging.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `docs/saw_reports/saw_boot_0a_shared_boot_status_contract_20260526.md`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q`.

## 2026-05-26 Round Entry (Boot Gate Copy And Writes Need Their Own Guards)
- Date: 2026-05-26
- Mistake or miss: The first boot-preflight data-readiness integration carried data-gate `next_actions` into boot-status details and allowed failed preflight to refresh runtime boot-status evidence when `--write-status` was supplied.
- Root cause: The integration reused the gate payload too directly and treated explicit write intent as enough authority even after the assembled preflight verdict was blocked.
- Fix applied: Added a boot-facing sanitizer that keeps only data-readiness blockers/warnings, explicitly deferred research-validity in boot metadata/docs, blocked status writes until preflight PASS, and added focused regressions.
- Guardrail for next time: Any boot/control-plane integration must separately test copy sanitization and failed-run write blocking; explicit write flags should authorize a path, not override a blocked verdict.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `docs/architecture/boot_preflight_contract.md`, `docs/saw_reports/saw_boot_preflight_data_readiness_integration_20260526.md`, `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests/test_boot_preflight.py tests/test_boot_status_contract.py -q`.

## 2026-05-27 Round Entry (Dirty-Worktree Classification Must Follow Live Root State)
- Date: 2026-05-27
- Mistake or miss: The first pass at BOOT-0A/BOOT-0B classification relied too much on stale manifest/context text and not enough on the live `git status` / `git diff` split.
- Root cause: The repository already carried mixed BOOT, governance, UI, and evidence residue, so archived truth surfaces no longer matched the current dirty worktree exactly.
- Fix applied: Reclassified from live root diffs, kept `core/boot_status.py` and `tests/test_boot_status_contract.py` in BOOT-0A, kept `scripts/governance_preflight.py` and `tests/test_boot_preflight_governance.py` in BOOT-0B, and kept `dashboard.py` and broad docs/evidence/runtime residue out of the boot-control closure.
- Guardrail for next time: Never promote a dirty-worktree manifest over live `git status` when deciding boot buckets; split mixed boot/governance files before any strict `--require-github` claim.
- Evidence paths: `git status --short`, `git diff --name-status`, `scripts/governance_preflight.py`, `tests/test_boot_preflight_governance.py`, `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `scripts\boot_preflight.py --repo-root . --mode strict --no-tests`, `scripts\boot_preflight.py --repo-root . --mode strict --require-github --no-tests`.

## 2026-05-28 Round Entry (Local Ignored Data Is Not BootReady Truth)
- Date: 2026-05-28
- Mistake or miss: Local ignored data and dirty-worktree artifacts can be mistaken for clean GitHub truth or BootReady evidence during strict data-readiness recovery.
- Root cause: The repository can contain useful local artifacts that are intentionally not tracked, but strict BootReady requires governed provenance, manifest/hash proof, and an approved intake or regeneration path before the artifacts count.
- Fix applied: Refreshed current truth surfaces for `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`, kept DataReadyStrict blocked, and recorded that authorization packets must precede regeneration or external-bundle intake.
- Guardrail for next time: Before regenerating or accepting strict-readiness artifacts, publish/approve the bounded authorization packet and keep local ignored artifacts out of GitHub truth and BootReady claims.
- Evidence paths: `docs/architecture/governed_data_artifact_authorization_20260528.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`, `docs/context/planner_packet_current.md`, `docs/context/observability_pack_current.md`, `docs/notes.md`, `docs/decision log.md`.

## 2026-05-28 Round Entry (Boot Preflight Is Not Artifact Authorization Evidence)
- Date: 2026-05-28
- Mistake or miss: The governed artifact-authorization packet listed `.venv\Scripts\python launch.py --preflight --strict` as a read-only validation command, which could be misread as DataReadyStrict or BootReady proof.
- Root cause: Boot-control preflight evidence was conflated with docs-only artifact authorization while inherited boot-control diffs and data-readiness deferral remained unresolved.
- Fix applied: Removed launch preflight from the packet validation commands, added a warning, and refreshed current truth surfaces so inherited boot-control diffs are open risk, out-of-scope, and not evidence for or against this packet.
- Guardrail for next time: Do not list boot preflight commands as artifact-authorization validation when data readiness is blocked; keep BootReady BLOCKED until a separate boot-control round proves readiness.
- Evidence paths: `docs/architecture/governed_data_artifact_authorization_20260528.md`, `docs/context/impact_packet_current.md`, `docs/context/planner_packet_current.md`, `docs/context/observability_pack_current.md`, `docs/notes.md`, `docs/lessonss.md`.
