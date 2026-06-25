
Phase 65 Frontend/UI Shared Replay Bundle (2026-05-13)

  - Decision record:
    - rewire the dashboard Strategy Replay surfaces to consume one selected-method `DashboardReplayContext`.
    - make latest snapshot and Portfolio YTD prefer the selected-method replay snapshot before legacy optimizer allocation state.
    - keep cheap Buy/Sell audit display before the heavy replay loop, but source it from the shared replay context.
  - The Decision (Hardcoded):
    - `DashboardReplayContext` includes `replay_df`, `latest_snapshot`, `event_annotations`, and `buy_sell_decisions`.
    - `_render_strategy_replay_section()` calls `_build_dashboard_strategy_replay_context(...)` and passes that context into `_render_buy_sell_decision_log(context)`.
    - `_render_strategy_replay_section()` does not call `read_lifecycle_log()` and does not read `data/portfolio_lifecycle_buy_sell_log.jsonl` directly.
    - `_prime_strategy_replay_latest_snapshot_for_ytd()` runs before `_render_portfolio_ytd_chart()` so YTD can share selected-method replay weights.
  - Evidence:
    - `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py` PASS.
    - `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py -q` PASS, 89 passed.
  - Contract lock:
    - `FRONTEND_SHARED_REPLAY_BUNDLE := VALID iff (one_selected_method_context = 1) and (latest_snapshot_from_context = 1) and (ytd_prefers_replay_snapshot = 1) and (enter_exit_from_context = 1) and (buy_sell_from_context = 1) and (direct_surface_jsonl_read = 0) and (direct_surface_lifecycle_read = 0) and (backend_replay_artifact_followup_recorded = 1)`.

Phase 65 Optimizer History Diagnostics Split (2026-05-15)

  - Decision record:
    - keep `insufficient_history` as the backend fail-closed optimizer universe gate.
    - split the visible Portfolio Optimizer diagnostics into `Missing History` and `Stale Endpoint`.
    - expose `Latest Price Date` in Universe Audit rows so stale endpoints do not look like short local history.
  - The Decision (Hardcoded):
    - `optimizer_universe_health_summary(...)` returns `missing_history` and `stale_endpoint` counts.
    - `_render_universe_audit(...)` renders `Missing History` and `Stale Endpoint` metrics.
    - `_render_allocation_explanation(...)` uses split labels and does not use `Price-history failures`.
  - Evidence:
    - `.venv\Scripts\python -m py_compile views\optimizer_view.py strategies\portfolio_universe.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` PASS.
    - `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` PASS, 62 passed.
  - Contract lock:
    - `OPTIMIZER_HISTORY_DIAGNOSTIC_SPLIT := VALID iff (stale_endpoint_rows_remain_ineligible = 1) and (missing_history_label_visible = 1) and (stale_endpoint_label_visible = 1) and (latest_price_date_visible = 1) and (provider_ingestion = 0) and (canonical_market_data_write = 0)`.

Phase 65 Portfolio Replay Role Contract (2026-05-15)

  - Decision record:
    - make replay exposure truth mechanically distinguishable from lifecycle audit intent using explicit role columns.
    - make strategy replay the owner of aux context normalization and dashboard a caller of that shared contract.
    - keep diagnostics as post-processing over the visible `DashboardReplayContext`, not a second replay build.
  - The Decision (Hardcoded):
    - `REPLAY_COLUMNS`, `REPLAY_CONTEXT_COLUMNS`, and `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` include `context_role` / `row_role`.
    - `context_role` values distinguish current holdings, historical context rows, flat replay rows, cash, and unavailable rows.
    - legacy selected-method artifacts without role columns hydrate default roles on read; unrelated schema drift remains `schema_mismatch`.
    - Dashboard latest snapshot labels replay exposure as `Replay Weight`; allocation snapshot labels latest exposure as `Current Weight`.
    - Diagnostic artifact generation records replay identity and cache-signature hash from the same rendered context.
  - Evidence:
    - `.venv\Scripts\python -m py_compile strategies\strategy_replay.py dashboard.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py` PASS.
    - Targeted role/compat/diagnostic hardening regressions PASS, 3 passed after SAW Reviewer C suggestions.
    - `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py -q` PASS, 169 passed.
    - SAW Implementer and Reviewer A/B/C PASS.
  - Contract lock:
    - `PORTFOLIO_REPLAY_ROLE_CONTRACT := VALID iff (context_role_schema = 1) and (row_role_schema = 1) and (strategy_replay_normalizer_owner = 1) and (dashboard_private_normalizer = 0) and (legacy_artifact_roles_hydrate = 1) and (diagnostics_from_dashboard_context = 1) and (diagnostic_replay_rebuild = 0)`.

Phase 65 Data/PIT Strategy Replay Artifact (2026-05-12)

  - Decision record:
    - provide local-first replay input artifacts for full forward-walk strategy replay without provider calls or canonical market-data writes.
    - use local `prices_tri.parquet` when available, with TRI levels as the price matrix and `total_ret` as the return matrix.
    - require `r3000_pit` membership for replay input generation; row slicing alone is not enough PIT protection.
    - keep persisted outputs display-only under `data/runtime_cache/strategy_replay`.
  - The Decision (Hardcoded):
    - `core.data_orchestrator.load_strategy_replay_inputs(...)` returns `StrategyReplayInputs` with `prices`, `returns`, `ticker_map`, `cache_signature`, `cache_key`, and metadata.
    - replay matrix slices clamp dates to `date <= min(end_date, as_of_date)`.
    - `build_strategy_replay_cache_signature(...)` includes source file signatures, method, controls, date range, as-of date, `max_weight`, `top_n`, `start_year`, and `universe_mode`.
    - `write_strategy_replay_artifact_atomic(...)` rejects repo `data/` output paths outside the configured runtime cache, pre-serializes manifest JSON, and uses temp files plus `os.replace`.
    - artifacts store compact wide `matrix=price` / `matrix=return` rows; ticker labels live in the manifest map.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py -q` PASS, 22 passed.
    - `.venv\Scripts\python -m py_compile core\data_orchestrator.py scripts\build_strategy_replay_artifact.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py` PASS.
    - `docs/saw_reports/saw_data_pit_strategy_replay_artifact_20260512.md` records initial SAW blockers and local reconciliation; post-fix independent recheck is blocked by account usage limit.
  - Contract lock:
    - `DATA_PIT_STRATEGY_REPLAY_ARTIFACT := VALID iff (local_prices_tri_source = 1) and (replay_universe_mode = r3000_pit) and (future_rows_excluded = 1) and (provider_call = 0) and (canonical_market_data_write = 0) and (cache_key_tracks_source_method_controls_dates_max_weight = 1) and (artifact_path_confined_to_runtime_cache = 1) and (atomic_temp_replace = 1)`.

Phase 65 Research Validity Runner v0 (2026-05-26)

  - Decision record:
    - make research validity mechanical before any strategy, signal, candidate, replay, optimizer output, or dashboard surface can claim research-valid status.
    - approve a top-level `research/` package as the evidence-runner layer while keeping `core.engine.run_simulation(...)` as the official PnL/cost/turnover primitive.
    - route Rule100 replay rows through a diagnostic-only adapter first; this does not promote Rule100 as validated alpha.
  - The Decision (Hardcoded):
    - `ResearchStatus` is a closed vocabulary: `diagnostic_only`, `exploratory`, `research_valid`, `candidate_ready`, `blocked`.
    - `research.backtest_runner.run_research_backtest(...)` forces `strict_missing_returns=True` and blocks missing cartridge, cost policy, benchmark policy, PIT proof, input signatures, leakage checks, CASH columns, non-finite executed returns, malformed target-weight dates, and sparse-calendar target weights in v0.
    - caller-supplied `run_id` values must be a single safe path segment; absolute paths, traversal, nested paths, empty ids, and unsupported characters fail before artifact path creation.
    - `research.evidence_schema.write_evidence_packet(...)` writes JSON/CSV artifacts through temp files in the run directory plus `os.replace`, removes stale final manifests before same-run rewrites, and emits `evidence_packet.json` last.
    - v0 cash handling is implicit residual cash only; the engine target-weight matrix must not include a `CASH` column.
    - `research.benchmarks.build_pit_equal_weight_benchmark(...)` constructs same-date PIT equal-weight target weights and the benchmark is run through the same engine/cost/strict policy.
    - `research.adapters.rule100_replay_adapter` filters daily portfolio rows, excludes CASH, pivots date x asset target weights, rejects conflicting duplicate date/asset rows, and ignores replay equity/performance columns.
  - Evidence:
    - `.venv\Scripts\python -m py_compile research\__init__.py research\status.py research\strategy_cartridge.py research\metrics.py research\evidence_schema.py research\benchmarks.py research\backtest_runner.py research\adapters\__init__.py research\adapters\rule100_replay_adapter.py tests\test_research_status.py tests\test_research_evidence_schema.py tests\test_research_benchmarks.py tests\test_research_backtest_runner.py tests\test_research_rule100_adapter.py` PASS.
    - `.venv\Scripts\python -m pytest tests\test_research_status.py tests\test_research_evidence_schema.py tests\test_research_benchmarks.py tests\test_research_backtest_runner.py tests\test_research_rule100_adapter.py tests\test_engine.py -q` PASS, 45 passed.
    - `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_position_lifecycle.py tests\test_pinned_universe.py tests\test_portfolio_universe.py tests\test_optimizer_core_policy.py -q` PASS, 186 passed.
  - Contract lock:
    - `RESEARCH_VALIDITY_RUNNER_V0 := VALID iff (closed_status_vocab = 1) and (canonical_engine_wrapper = 1) and (strict_missing_returns_forced = 1) and (cash_column_forbidden = 1) and (implicit_cash_residual = 1) and (full_calendar_target_weights = 1) and (run_id_path_confined = 1) and (evidence_writes_atomic = 1) and (final_manifest_last = 1) and (pit_equal_weight_benchmark_same_engine = 1) and (rule100_adapter_diagnostic_only = 1) and (replay_equity_authority = 0) and (provider_ingestion = 0) and (canonical_market_data_write = 0) and (ranking = 0) and (scoring = 0) and (broker_call = 0)`.

BOOT-0A Shared Boot Status Contract (2026-05-26)

  - Decision record:
    - reconcile the living boot preflight with a shared `core.boot_status` contract instead of replacing `scripts/boot_preflight.py`.
    - keep `core.data_readiness_gate` as the data authority and make `core.boot_status` the verdict/schema authority.
    - move the canonical generated status artifact to `runtime/boot_status_current.json` and treat `docs/context/boot_status_current.json` only as a noncanonical context snapshot path.
    - keep `dashboard.py`, `views/page_registry.py`, `dashboard_preflight.py`, and Command Center work out of BOOT-0A.
  - The Decision (Hardcoded):
    - `BootStatus` derives `ready`, `degraded`, or `blocked` from typed readiness checks.
    - `local_planning`, `boot_candidate`, and `safe_boot` are flags, not separate primary verdicts.
    - data readiness `PASS/WARN/FAIL` maps to `ready/degraded/blocked`.
    - missing or invalid boot-status artifacts load as `blocked`.
    - strict default runs boot-control tests, the Portfolio route smoke, and `current_context.first_command` unless `--no-tests` is passed.
    - `--require-github` blocks non-identical status writes; the safe-boot flow is write first, commit/push, then read-only GitHub proof.
    - focused commands must parse as `python -m pytest`, run without `shell=True`, reject shell metacharacters, and use bounded timeouts.
    - `--require-github` performs a final post-run Git proof so a gate cannot mutate the worktree and still claim read-only GitHub alignment.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q` PASS, 108 passed.
    - `.venv\Scripts\python -m py_compile core\boot_status.py core\data_readiness_gate.py scripts\boot_preflight.py scripts\run_data_readiness_gate.py scripts\governance_preflight.py tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py` PASS.
    - `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py::test_dash_1_portfolio_allocation_route_renders_without_overlay -q` PASS.
    - `.venv\Scripts\python scripts\governance_preflight.py --json` PASS, zero findings.
    - Temp-repo probe wrote `runtime/boot_status_current.json`, did not write `docs/context/boot_status_current.json`, and produced a fail-closed `blocked` artifact when context/data were absent.
  - Contract lock:
    - `BOOT_0A_SHARED_STATUS := VALID iff (boot_status_contract_owner = core.boot_status) and (data_readiness_owner = core.data_readiness_gate) and (canonical_status_path = runtime/boot_status_current.json) and (docs_context_status_fallback = 0) and (missing_artifact_blocked = 1) and (invalid_artifact_blocked = 1) and (strict_data_fail_blocked = 1) and (strict_route_smoke_default = 1) and (strict_focused_command_default = 1) and (focused_command_shell = 0) and (focused_command_allowlisted_pytest = 1) and (strict_gate_timeouts = 1) and (require_github_status_mutation = 0) and (require_github_postrun_git_proof = 1) and (dashboard_route_change = 0) and (command_center_added = 0)`.

Boot Status Path Contract + Governance Scanner Integration (2026-05-26)

  - Decision record:
    - choose exactly one canonical boot-status path for runtime/safe-boot truth: `runtime/boot_status_current.json`.
    - treat `docs/context/boot_status_current.json` as a noncanonical docs/context snapshot path only; delete stale snapshots rather than letting them masquerade as current runtime truth.
    - integrate Governance Gate v0 directly into `scripts/boot_preflight.py --repo-root` so GOV-000 can prove root application instead of artifact-only presence.
    - keep data-readiness, dashboard smoke, replay/optimizer certification, and GitHub clean safe-boot proof out of this narrow path-contract repair.
  - The Decision (Hardcoded):
    - `core.boot_status._resolve_boot_status_target(...)` allows only `runtime/boot_status_current.json`.
    - `core.boot_status.load_boot_status_fail_closed()` reads the runtime canonical path only when no explicit path is supplied and does not fall back to docs/context.
    - `scripts.boot_preflight.BOOT_CONTROL_TEST_COMMAND` includes `tests/test_boot_preflight_governance.py`.
    - `scripts.boot_preflight.build_status(...)` records `checks["governance"]` and fails closed on governance `FAIL`.
    - strict `--write-status` writes only after PASS and only to the runtime path.
  - Evidence:
    - `.venv\Scripts\python -c "from core import boot_status as b; from scripts import boot_preflight as p; import core.data_readiness_gate as d; ..."` -> runtime path sentinel PASS.
    - `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json` PASS, zero findings.
    - `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py -q` PASS, 80 passed.
    - `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict` exits 0 with `overall_status=WARN`, no blockers.
    - `.venv\Scripts\python scripts\boot_preflight.py --repo-root . --mode strict --no-tests --json` FAIL only because dirty source/test/runtime files remain unclassified.
  - Contract lock:
    - `BOOT_STATUS_PATH_CONTRACT := VALID iff (canonical_status_path = runtime/boot_status_current.json) and (docs_context_status_fallback = 0) and (runtime_writer_only = 1) and (write_status_requires_pass = 1) and (governance_scanner_integrated = 1) and (governance_fail_blocks = 1) and (boot_ready_claim = 0 until strict_clean_github_preflight_passes)`.

Boot Status Path Contract SAW Reconciliation (2026-05-26)

  - Decision record:
    - keep `runtime/boot_status_current.json` as the only executable boot-status current path.
    - keep `docs/context/boot_status_current.json` as a noncanonical context snapshot path only; it is not a reader fallback, writer fallback, mirror, or safe-boot source.
    - require path-contract closure evidence to include both runtime import sentinels and docs/context stale-authority grep.
    - do not generate canonical runtime boot status while strict preflight is blocked by dirty source/test/runtime files.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py -q` PASS, 92 passed.
    - `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json` PASS, zero findings.
    - `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict` exits 0 with `overall_status=WARN` and no blockers.
    - runtime path sentinel reports `core.boot_status`, `scripts.boot_preflight`, and `core.data_readiness_gate` all using `runtime/boot_status_current.json`; docs/context snapshot constant exists but no legacy fallback exists.
    - strict `--require-github --no-tests` preflight fails because dirty source/test/runtime files remain and the worktree is not clean; HEAD is aligned.
  - Contract lock:
    - `BOOT_STATUS_PATH_SAW := BLOCK_UNTIL_STRICT_CLEAN iff (runtime_current_path = 1) and (docs_context_fallback = 0) and (docs_context_allowed_write = 0) and (governance_pass = 1) and (data_readiness_blockers = 0) and (strict_preflight_dirty_blocker = 1) and (boot_ready_claim = 0)`.

Governance Gate v0 Root Application (2026-05-26)

  - Decision record:
    - treat Governance Gate v0 packet/patch/zip files as porting inputs until root preflight and tests prove the actual implementation.
    - integrate `scripts.governance_preflight.run_governance_preflight(...)` into the existing `scripts/boot_preflight.py --repo-root` flow.
    - make governance `FAIL` fail closed in both raw preflight and normalized boot-status output; governance `WARN` is advisory/degraded.
    - separate `safe_boot` from final GitHub proof: strict all-gates PASS can set `safe_boot`, while `--require-github` remains the clean pushed-alignment proof.
    - strengthen the boot write guard so atomic-write `.tmp` residue under guarded data/cache roots is disallowed evidence of mutation.
  - The Decision (Hardcoded):
    - `GOV-000` blocks packet-artifact drift when expected root policy/test/integration files are missing.
    - `GOV-001/002/003/004/005/007/008` run as a root scanner over dashboard/view literals and candidate-card bundles.
    - `make_boot_status_from_preflight(...)` maps governance `PASS/WARN/FAIL` to readiness `pass/warn/fail` and severity `ready/degraded/blocked`.
    - default strict runs boot-control tests, Portfolio route smoke, and `current_context.first_command`.
    - `core.data_readiness_gate._is_snapshot_ignored(...)` ignores bytecode/cache artifacts but not `.tmp` files in guarded roots.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py -q` PASS, 74 passed.
    - `.venv\Scripts\python -m pytest tests\test_data_readiness_gate_write_guard.py -q` PASS, 6 passed.
    - `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_g8_2_system_scouted_candidate_card.py -q` PASS, 46 passed.
    - `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json` PASS, zero findings.
    - `.venv\Scripts\python scripts\boot_preflight.py --repo-root . --strict --json` returns `primary_verdict=blocked`, `preflight_verdict=ERROR`, governance PASS, data readiness WARN, and write guard FAIL due to disallowed runtime/evidence/code mutation.
  - Contract lock:
    - `GOVERNANCE_GATE_V0_ROOT := VALID iff (artifact_drift_guard = 1) and (root_governance_scanner_pass = 1) and (governance_fail_blocks = 1) and (governance_warn_degrades = 1) and (candidate_card_governance_required = 1) and (candidate_manifest_hash_bound = 1) and (strict_focused_contract_default = 1) and (safe_boot_github_proof_separated = 1) and (tmp_residue_guarded = 1) and (boot_ready_claim = 0 until strict_preflight_passes_cleanly)`.
