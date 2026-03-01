# Terminal Zero Operations Runbook

All commands in this runbook must use the project virtual environment interpreter (`.venv\Scripts\python` on Windows, `.venv/bin/python` on POSIX).

## 1. Startup
- **Standard Launch**: `.venv\Scripts\python launch.py`
- **Debug Mode**: `.venv\Scripts\streamlit run app.py -- --debug`

## 1b. Startup Quickstart (Context Bootstrap)
- **Build Context Artifacts**: `.venv\Scripts\python scripts/build_context_packet.py`
- **Invoke Context Bootstrap Skill**: `invoke $context-bootstrap`
- **Validate Context Artifacts**: `.venv\Scripts\python scripts/build_context_packet.py --validate`

## 1c. Release Promotion (Area 4)
- **Build immutable runtime image**:
  - `docker build -t ghcr.io/terminal-zero/quant:<version> .`
  - dependency install source inside `Dockerfile`: `requirements.lock` (fully pinned lock, transitive included)
- **Resolve digest-locked image ref** (required):
  - `docker image inspect ghcr.io/terminal-zero/quant:<version> --format "{{index .RepoDigests 0}}"`
- **Promote with auto rollback (docker mode default)**:
  - `.venv\Scripts\python scripts/release_controller.py --candidate-version <version> --candidate-ref <digest-ref> --service-name terminal_zero_orchestrator --startup-wait-seconds 45`
- **Dry metadata-only registration** (no container orchestration):
  - `.venv\Scripts\python scripts/release_controller.py --mode metadata-only --candidate-version <version> --candidate-ref <digest-ref>`
- **External probe mode** (custom health command):
  - `.venv\Scripts\python scripts/release_controller.py --mode external-probe --allow-external-probe-promote --candidate-version <version> --candidate-ref <digest-ref> --probe-command .venv\Scripts\python scripts/test_visual.py`
  - Use only when deployment/rollback is managed externally; without `--allow-external-probe-promote`, controller exits before promotion.
- **Release state artifact**:
  - `data/processed/release_metadata.json`
  - terminal statuses: `active`, `rolled_back`, `rollback_failed`

## 2. Data Management
- **Update Prices (Daily / Watchlist)**: `.venv\Scripts\python data/updater.py --scope "Custom" --tickers "AAPL,MSFT,SPY"`
- **Hydrate Universe (Monthly)**: `.venv\Scripts\python data/updater.py --scope "Top 3000"`
- **Update Fundamentals**: `.venv\Scripts\python data/fundamentals_updater.py --scope "Top 500"`
- **Build Feature Store (Incremental default)**: `.venv\Scripts\python data/feature_store.py --start-year 2000 --universe-mode yearly_union --yearly-top-n 100`
- **Build Feature Store (Forced full rebuild)**: `.venv\Scripts\python data/feature_store.py --start-year 2000 --full-rebuild`
- **Rebuild Sector Map**: `.venv\Scripts\python data/build_sector_map.py`
- **PiT strict binding (optional hard gate)**:
  - `set T0_STRICT_SIMULATION_TS_BINDING=1`
  - `set T0_SIMULATION_TS_BINDING_SECRET=<secure-secret>`
  - when enabled, fundamentals reads with `as_of_date` require a valid timestamp-binding token (fail-closed on missing/mismatch).
- **Yearly-union runtime contract**:
  - active selector is strict `t-1` (`date < anchor_date`) and ranks by last tradable date liquidity,
  - same-day and future liquidity rows are excluded by design.

## 3. Testing
- **Run All Tests**: `.venv\Scripts\python -m pytest`
- **Run Data Layer Tests**: `.venv\Scripts\python -m pytest tests/test_updater_parallel.py tests/test_feature_store.py tests/test_parallel_utils.py`
- **Run Data Validation Gate**: `.venv\Scripts\python scripts/validate_data_layer.py`

## 4. Baseline Benchmarking (Phase 18 Day 1)
- **Run Baseline Report**: `.venv\Scripts\python scripts/baseline_report.py --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --trend-risk-off-weight 0.5`
- **Output CSV (default)**: `data/processed/phase18_day1_baselines.csv`
- **Output Plot (default)**: `data/processed/phase18_day1_equity_curves.png`
- **Path Resolution Note**: relative CLI paths in `scripts/baseline_report.py` are resolved against repo root (`E:\Code\Quant`), not the caller working directory. Use absolute paths if external schedulers need other destinations.

## 4b. TRI Migration (Phase 18 Day 2)
- **Build TRI prices artifact**: `.venv\Scripts\python data/build_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --output data/processed/prices_tri.parquet --validation-csv data/processed/phase18_day2_tri_validation.csv --split-plot data/processed/phase18_day2_split_events.png`
- **Build macro TRI artifact**: `.venv\Scripts\python data/build_macro_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --input data/processed/macro_features.parquet --output data/processed/macro_features_tri.parquet`
- **Primary Day 2 outputs**:
  - `data/processed/prices_tri.parquet`
  - `data/processed/macro_features_tri.parquet`
  - `data/processed/phase18_day2_tri_validation.csv`
  - `data/processed/phase18_day2_split_events.png`

## 4c. Cash Overlay Benchmarking (Phase 18 Day 3)
- **Prerequisites**:
  - `data/processed/prices_tri.parquet` must exist (built in Day 2 via `data/build_tri.py`).
  - `data/processed/macro_features_tri.parquet` recommended (fallback: `macro_features.parquet`).
  - `data/processed/liquidity_features.parquet` recommended for EFFR context.
- **Run overlay comparison (6 scenarios)**: `.venv\Scripts\python scripts/cash_overlay_report.py --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --target-vol 0.15 --vol-lookbacks 20,60,120 --output-csv data/processed/phase18_day3_overlay_metrics.csv --output-plot data/processed/phase18_day3_overlay_3panel.png --output-stress-csv data/processed/phase18_day3_overlay_stress_checks.csv --output-corr-csv data/processed/phase18_day3_overlay_exposure_corr.csv`
- **Primary Day 3 outputs**:
  - `data/processed/phase18_day3_overlay_metrics.csv`
  - `data/processed/phase18_day3_overlay_stress_checks.csv`
  - `data/processed/phase18_day3_overlay_exposure_corr.csv`
  - `data/processed/phase18_day3_overlay_3panel.png`
- **Expected scenarios in metrics CSV**:
  - `Buy & Hold`
  - `Trend SMA200`
  - `Vol Target 15% (20d)`
  - `Vol Target 15% (60d)`
  - `Vol Target 15% (120d)`
  - `Trend Multi-Horizon`
- **Operational note**:
  - Script reuses FR-050 cash hierarchy from Phase 13 helpers and routes returns through `engine.run_simulation`; keep `--cost-bps` aligned with baseline comparables unless intentionally testing sensitivity.

## 4d. Company Scorecard Validation (Phase 18 Day 4)
- **Run scorecard validation**: `.venv\Scripts\python scripts/scorecard_validation.py --input-features data/processed/features.parquet --scoring-method complete_case --start-date 2015-01-01 --end-date 2024-12-31 --output-validation-csv data/processed/phase18_day4_scorecard_validation.csv --output-scores-csv data/processed/phase18_day4_company_scores.csv`
- **POSIX equivalent**: `.venv/bin/python scripts/scorecard_validation.py --input-features data/processed/features.parquet --scoring-method complete_case --start-date 2015-01-01 --end-date 2024-12-31 --output-validation-csv data/processed/phase18_day4_scorecard_validation.csv --output-scores-csv data/processed/phase18_day4_company_scores.csv`
- **Primary Day 4 outputs**:
  - `data/processed/phase18_day4_company_scores.csv`
  - `data/processed/phase18_day4_scorecard_validation.csv`
- **Expected validation checks**:
  - `score_coverage`
  - `factor_balance_max_share`
  - `adjacent_rank_correlation`
  - `quartile_spread_sigma`
- **Schema alignment note**:
  - `data/feature_store.py` now emits scorecard aliases:
    - `quality_composite`
    - `realized_vol_21d`
    - `illiq_21d`

## 4e. Day 5 Ablation Matrix (Phase 18 Day 5)
- **Run 9-config ablation matrix**: `.venv\Scripts\python scripts/day5_ablation_report.py --input-features data/processed/features.parquet --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --top-quantile 0.10 --allow-missing-returns --output-metrics-csv data/processed/phase18_day5_ablation_metrics.csv --output-deltas-csv data/processed/phase18_day5_ablation_deltas.csv --output-summary-json data/processed/phase18_day5_ablation_summary.json`
- **Strict mode (fail on missing active returns)**: remove `--allow-missing-returns`.
- **Matrix safety control**:
  - default `--max-matrix-cells 25000000`
  - increase only with explicit memory headroom.
- **Primary Day 5 outputs**:
  - `data/processed/phase18_day5_ablation_metrics.csv`
  - `data/processed/phase18_day5_ablation_deltas.csv`
  - `data/processed/phase18_day5_ablation_summary.json`
- **Expected summary fields**:
  - `baseline_id`
  - `optimal_id`
  - `acceptance.coverage_met`
  - `acceptance.spread_met`
  - `acceptance.turnover_reduction_met`
  - `acceptance.sharpe_preservation_met`

## 4f. Day 6 Walk-Forward Validation (Phase 18 Day 6)
- **Run Day 6 validator**: `.venv\Scripts\python scripts/day6_walkforward_validation.py --input-features data/processed/features.parquet --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --top-quantile 0.10 --c3-decay 0.95 --allow-missing-returns --output-dir data/processed`
- **Strict missing-return mode**: remove `--allow-missing-returns` to fail-fast when active-position return cells are missing.
- **Primary Day 6 outputs**:
  - `data/processed/phase18_day6_walkforward.csv`
  - `data/processed/phase18_day6_decay_sensitivity.csv`
  - `data/processed/phase18_day6_crisis_turnover.csv`
  - `data/processed/phase18_day6_checks.csv`
  - `data/processed/phase18_day6_summary.json`
- **Critical gate check**:
  - `CHK-54` from `phase18_day6_checks.csv` must be `pass=True`.
- **Mandatory missing-data check (when using `--allow-missing-returns`)**:
  - open `phase18_day6_summary.json`
  - inspect:
    - `missing_active_return_cells.baseline`
    - `missing_active_return_cells.c3`
  - if either value is `> 0`, treat run as **data-quality warning** and do not promote as hard-pass without explicit acknowledgment.
- **Matrix safety control**:
  - default `--max-matrix-cells 25000000`
  - if raised, confirm memory headroom and record override in run notes.

## 4g. Stop-Loss Module Validation (Phase 21 Day 1)
- **Compile gate**: `.venv\Scripts\python -m py_compile strategies/stop_loss.py tests/test_stop_loss.py`
- **Unit gate**: `.venv\Scripts\python -m pytest tests/test_stop_loss.py -q`
- **Compatibility smoke**: `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q`
- **Behavioral contract**:
  - ATR mode must stay `proxy_close_only`.
  - ATR method must remain SMA over `abs(diff(close))`.
  - D-57 ratchet must keep stop non-decreasing (`stop_t >= stop_{t-1}`).
  - Drawdown tiers remain `-8%/-12%/-15%` with scales `0.75/0.50/0.00`.
- **Integration activation gate (Phase 21 Day 2+)**:
  - Do **not** enable stop-loss execution in live runtime until integration PR passes:
    - integration tests for stop-trigger exits and drawdown scaling,
    - telemetry emission checks for stop/drawdown state,
    - SAW round sign-off for wiring changes.
  - Owner/Handoff:
    - Owner: Strategy Engineering
    - Handoff: Quant Ops + Risk review
- **Runtime observability checks after activation**:
  - verify `atr_mode` logged as `proxy_close_only` in runtime context.
  - verify stop ratchet invariant on sampled positions (`stop_t >= stop_{t-1}`).
  - monitor stop-hit counts, underwater timeout exits, and drawdown tier transitions.
  - alert when:
    - tier-3 (`scale=0.0`) persists unexpectedly,
    - stop levels become non-finite/NaN,
    - ATR series becomes unavailable for active symbols.
- **Rollback if post-activation behavior deviates**:
  1. disable stop-loss wiring feature flag / integration path.
  2. revert to prior strategy execution path (pre-Phase 21 stop module usage).
  3. rerun compatibility smoke:
     - `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q`
  4. record incident and rollback details in `docs/decision log.md`.

## 4h. SDM 3-Pillar Ingestion + Assembly (Phase 23)
- **Fundamentals SDM dry-run (scoped)**:
  - `.venv\Scripts\python scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31 --dry-run`
- **Fundamentals SDM write (scoped)**:
  - `.venv\Scripts\python scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31`
- **Macro rates dry-run/write**:
  - `.venv\Scripts\python scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run`
  - `.venv\Scripts\python scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31`
- **FF five-factor dry-run/write**:
  - `.venv\Scripts\python scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run`
  - `.venv\Scripts\python scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31`
- **Final SDM assembler dry-run/write**:
  - `.venv\Scripts\python scripts/assemble_sdm_features.py --dry-run`
  - `.venv\Scripts\python scripts/assemble_sdm_features.py`
- **Outputs**:
  - `data/processed/fundamentals_sdm.parquet`
  - `data/processed/macro_rates.parquet`
  - `data/processed/ff_factors.parquet`
  - `data/processed/features_sdm.parquet`
  - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`

## 5. Execution Safety Controls (P0)
- **Immediate key response (required if secret was exposed)**:
  1. Revoke and rotate broker API credentials in the broker console.
  2. Update local environment variables only (never commit credentials to source files).
  3. Validate with `.venv\Scripts\python scripts/test_alpaca_connection.py`.
  4. Revoke and rotate WRDS + FMP credentials if any key touched source/data artifacts.
- **Paper-default broker guardrail**:
  - Runtime defaults to paper endpoint (`https://paper-api.alpaca.markets`).
  - Any non-paper `APCA_API_BASE_URL`/`ALPACA_BASE_URL` requires explicit break-glass:
    - `TZ_ALPACA_ALLOW_LIVE=YES`
  - Without break-glass, broker initialization is fail-closed.
- **Zero-trust secret ingress (no dotenv fallback)**:
  - Runtime secrets must be process-injected env vars only:
    - `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` (or Alpaca aliases),
    - `WRDS_USER`, `WRDS_PASS`,
    - `FMP_API_KEY`.
  - `.env`-file auto-loading is disallowed on broker startup.
- **Non-interactive payload guardrail**:
  - Payload generation in non-TTY sessions requires:
    - `TZ_EXECUTION_CONFIRM=YES`
- **HMAC signing key lifecycle contract (daily rotation)**:
  - Required payload-generation env vars:
    - `TZ_HMAC_KEY_VERSION`
    - `TZ_HMAC_KEY_ACTIVATED_AT_UTC` (ISO-8601 UTC)
  - Optional controls:
    - `TZ_HMAC_ROTATION_DAYS` (default `1`)
    - `TZ_HMAC_MAX_FUTURE_SKEW_SECONDS` (default `300`)
    - `TZ_HMAC_KEY_LEGAL_HOLD=YES` (legal-hold exception; suppresses overdue block)
  - Fail-closed behavior:
    - if key age exceeds rotation window and legal hold is not set, payload generation aborts.
    - if activation timestamp is in the future beyond allowed clock skew, payload generation aborts.
- **Deny-by-default outbound policy**:
  - Allowed host suffixes (default):
    - `alpaca.markets`
    - `wrds-pgdata.wharton.upenn.edu`
    - `financialmodelingprep.com`
  - Default transport policy:
    - outbound URLs must use `https`.
  - Allowlist extension via explicit env:
    - `TZ_ALLOWED_EGRESS_HOST_SUFFIXES=host1,host2,...`
  - Full override mode (use only when intentionally replacing defaults):
    - `TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE=override`
  - Dev-only localhost HTTP break-glass (never production):
    - `TZ_ALLOW_HTTP_EGRESS_LOCALHOST=YES`
  - Non-allowlisted egress is blocked at runtime.
  - Post-submit notification behavior:
    - webhook transport failures degrade with warning (`[WATCHTOWER-DEGRADED]`) after successful local submit,
    - pre-submit/payload-only notification remains fail-closed.
- **HF Data Health operator contract (binary)**:
  - Data health is derived from the in-memory HF proxy payload passed to the scan run.
  - Status is binary:
    - `HEALTHY` when `degraded_count == 0`
    - `DEGRADED` when `degraded_count > 0`
  - Dashboard exposes:
    - compact badge (`Data Health: HEALTHY|DEGRADED`, degraded percent),
    - expandable per-signal detail table (`signal`, `status`, `reason`, `span`).
  - No soft threshold bands (`green/yellow/red`) are used for this first-pass control.
- **Orchestrator hard-stop contract**:
  - `main_bot_orchestrator.py` scanner subprocesses run with strict timeout (`300s` each).
  - Any non-zero return code or timeout is a fail-stop for the scan run.

## 5a. P1 Closeout Validation Pack (Implementer Evidence)
- **Strict missing returns (executed exposure semantics)**:
  - `.venv\Scripts\python -m pytest tests/test_engine.py -q`
  - `.venv\Scripts\python -m pytest tests/test_day5_ablation_report.py tests/test_day6_walkforward_validation.py -q`
  - Strict runtime mode in scripts: omit `--allow-missing-returns` so executed-exposure missing cells fail fast.
- **Strict idempotency (`client_order_id`) wiring**:
  - `.venv\Scripts\python -m pytest tests/test_execution_controls.py -q`
  - Validate pass-through, deterministic fallback ID generation, and recovery lookup path via `get_order_by_client_order_id(...)`.
  - Enforced fail-closed controls:
    - duplicate `client_order_id` in one batch is rejected before submit;
    - empty `client_order_id` is rejected at broker submit boundary;
    - recovered orders must match intended `symbol/side/qty` or return `recovery_mismatch`.
- **Fundamentals ingest checkpoint/resume**:
  - `.venv\Scripts\python -m pytest tests/test_fundamentals_updater_checkpoint.py -q`
  - Resume flow:
    - first pass (checkpoint enabled): `.venv\Scripts\python data/fundamentals_updater.py --scope "Top 500" --checkpoint`
    - retain artifacts for inspection: add `--checkpoint-keep`
    - restart fresh when needed: add `--checkpoint-reset`
  - Mismatch policy:
    - default `--checkpoint-mismatch fail` (fail closed)
    - explicit recovery path `--checkpoint-mismatch reset` (discard stale checkpoint and rebuild)
  - Integrity guardrails:
    - checkpoint metadata is semantically validated (numeric fields/stage schema);
    - checkpoint partial rows must have valid target tickers and positive `permno`;
    - `permno_map` is frozen across resume to prevent `tickers.parquet` drift on `final_write`.

## 5b. P2 Auto-Backtest UI Control-Plane Validation Pack
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile core/auto_backtest_control_plane.py views/auto_backtest_view.py app.py`
- **Control-plane unit gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_auto_backtest_control_plane.py`
- **Impacted control-plane regression gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py`
- **Cache artifact path**:
  - `data/auto_backtest_cache.json`
- **Cache policy contract**:
  - loader default = fail-closed (`error_policy="fail"`),
  - explicit reset path (`error_policy="reset"`) is required for bootstrap/recovery.
- **Cost unit contract**:
  - view input is bps-labeled and converted to decimal rate before normalization,
  - control-plane normalization accepts explicit `cost_bps_unit` (`"rate"` or `"bps"`).
- **Atomic write contract**:
  - write to temp JSON, promote with `os.replace`, cleanup temp file in `finally`,
  - bounded retry on `PermissionError` for Windows lock contention.
- **View routing contract**:
  - `app.py` must route `"🔬 Lab / Backtest"` through `views/auto_backtest_view.py` only.
- **Fail-closed runtime contract**:
  - if start-state cache persist fails, Lab/Backtest run is aborted (no simulation execution).
  - corrupted cache payload (`invalid_json` / `invalid_payload`) must require explicit reset action before run.

## 5c. Phase 25 Orchestrator E2E Idempotency Reconciliation Pack
- **Targeted regression gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py tests/test_main_console.py tests/test_execution_controls.py`
- **Focused orchestrator gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py`
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`
- **Execution integrity contracts (`execute_orders_with_idempotent_retry`)**:
  - `client_order_id` must remain static across retries for the same intent.
  - `already exists` is accepted only when recovered payload strictly matches original pending intent (`symbol/side/qty`); else fail closed with `recovery_mismatch`.
  - per-attempt result rows are reconciled by expected CID set:
    - missing CIDs are retried while attempts remain,
    - unresolved missing CIDs terminate as `batch_result_missing`.
  - retryable transport faults that reach `max_attempts` terminate as `retry_exhausted`.
  - malformed non-dict `result` rows are treated as unobserved and reconciled via missing-CID fail-closed path.
  - duplicate symbols in the initial order set are rejected before first submit attempt.

## 5d. Phase 26 Runtime Hardening Debt Burn-Down Pack
- **Targeted runtime regression gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py`
- **Focused orchestrator gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py`
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py scripts/test_rebalance.py tests/test_test_rebalance_script.py`
- **Runtime hardening contracts**:
  - scanner timeout path must terminate process tree and then raise timeout,
  - scheduler loop must not fail-dead on one scanner exception (log and continue),
  - Windows process-tree kill path must validate `taskkill` return code,
  - entrypoint seed contract requires `client_order_id` or `trade_day`,
  - non-list/malformed batch results must resolve through missing-CID fail-closed reconciliation,
  - rebalance script must return non-zero when any order submission result fails.

## 5e. Phase 27 Conditional-Block Remediation Pack
- **Targeted remediation regression gate**:
  - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py`
- **Focused orchestrator gate**:
  - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py`
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/rebalancer.py scripts/test_rebalance.py tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py`
- **Strict typing + parity contracts**:
  - `result.ok` is valid only when `isinstance(result["ok"], bool)`; non-boolean rows are unobserved and reconciled fail closed.
  - all `ok=True` rows must pass strict intent parity (`symbol/side/qty`) before acceptance.
  - sparse `ok=True` payloads may use `row.order` fallback for parity fields to avoid false mismatches.
  - boolean `qty` values are invalid in both request normalization and recovery matching.
- **Terminal kill contract**:
  - scanner timeout must call process-tree termination and confirm process death.
  - any unconfirmed kill raises terminal `ScannerTerminationError` and must stop orchestrator.
- **Containment contract**:
  - startup diagnostic scan uses scheduler-equivalent containment for non-terminal faults (log + continue).
  - terminal scanner kill-failure is critical + re-raised at startup and in scheduled loop.
- **Entrypoint strictness**:
  - `scripts/test_rebalance.py` treats success as `ok is True` only.
  - non-boolean `ok` values are counted as failure and produce non-zero exit.

## 5f. Phase 28 Entrypoint Contract Remediation Pack
- **Targeted entrypoint regression gate**:
  - `.venv\Scripts\python -m pytest tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py`
- **Impacted matrix gate**:
  - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py`
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile main_console.py main_bot_orchestrator.py execution/broker_api.py execution/rebalancer.py tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py`
- **Atomic payload contract**:
  - any malformed `execution_orders` row aborts full batch (no partial execution),
  - required fields:
    - `ticker/symbol`, `target_weight`, `action|side`, `order_type`, `limit_price`, `client_order_id`, `trade_day`,
  - `trade_day` must be `YYYYMMDD` and calendar-valid.
- **CID lineage contract**:
  - payload `client_order_id` must be preserved through local submit seam and broker submit boundary.
- **Intent parity contract**:
  - local-submit seam enforces strict parity:
    - `symbol/side/qty/order_type/limit_price/client_order_id`,
  - symbol-set parity required between payload and calculated orders.
- **Recovery strictness contract**:
  - broker recovery match enforces:
    - `symbol/side/qty/order_type/client_order_id`,
  - market recovery accepts only null-like `limit_price` values (`None`, `""`, `"none"`, `"null"`),
  - non-null numeric market `limit_price` fails closed as `recovery_mismatch`.
- **Safety typing contract**:
  - broker submit rejects boolean `qty`,
  - local strict integer guard rejects non-integral quantities (no truncation).

## 6. Emergency / Troubleshooting
- **Clear Cache**: Delete `data/processed/*.parquet` (Safe, will trigger redownload).
- **Force Rebuild**: Delete `data/processed/fundamentals_snapshot.parquet` to force a clean snapshot generation.
- **Dashboard cache recovery (`last_scan_state.json`)**:
  - if cockpit boot fails after interrupted write or malformed cache payload, delete:
    - `data/last_scan_state.json`
  - then relaunch dashboard and use `Force Engine Refresh` once.
  - cache writes are atomic (`temp -> replace`), so repeated corruption indicates upstream disk/permission issues.

## 5g. Phase 29 Microstructure Telemetry Pack
- **Targeted microstructure regression gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_main_console.py tests/test_execution_controls.py`
- **Focused broker telemetry gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_execution_controls.py -k "quote_snapshot or partial_fill"`
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile execution/microstructure.py execution/broker_api.py main_console.py tests/test_execution_microstructure.py`
- **Arrival anchor contract**:
  - `arrival_ts` is stamped at command generation (`ms` precision),
  - `arrival_price` uses command-time bid/ask midpoint,
  - captured fields include `arrival_bid_price`, `arrival_ask_price`, and `arrival_quote_ts`.
- **Partial-fill VWAP contract**:
  - aggregate fills by `client_order_id` into deterministic `fill_vwap` and `fill_qty`.
- **Cost/latency contract**:
  - `IS_buy = (VWAP_fill - arrival_price) * fill_qty`,
  - `slippage_bps` is cost-positive and normalized to arrival price,
  - latency decomposition includes command->submit, submit->ack, ack->first_fill, command->first_fill.
- **Post-trade sink contract**:
  - order rows: `data/processed/execution_microstructure.parquet` + DuckDB table `execution_microstructure`.
  - fill rows: `data/processed/execution_microstructure_fills.parquet` + DuckDB table `execution_microstructure_fills`.
  - local-submit path aborts if telemetry persistence fails.

## 5h. Phase 31 Sovereign Execution Hardening Pack
- **Targeted integrated gate**:
  - `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py`
- **Compile gate**:
  - `.venv\Scripts\python -m py_compile execution/signed_envelope.py execution/microstructure.py main_console.py strategies/alpha_engine.py strategies/ticker_pool.py core/dashboard_control_plane.py tests/test_signed_envelope_replay.py tests/test_execution_microstructure.py tests/test_alpha_engine.py tests/test_ticker_pool.py tests/test_dashboard_control_plane.py`
- **Replay-ledger contract**:
  - local-submit replay check+append is atomic under exclusive lock,
  - malformed ledger rows are quarantined to `<ledger>.malformed.jsonl` and do not block valid submits.
- **Telemetry spool contract**:
  - idempotent sink replay keyed by deterministic spool UID,
  - schema-invalid JSON spool records are quarantined to `.bad` and cursor advances,
  - stale trailing partial lines are quarantined after stale threshold,
  - drained spool is compacted to bound disk growth.
- **Durability contract**:
  - local submit must pass bounded telemetry durability gate (`drained && pending_bytes==0 && last_flush_error empty`) before success + post-submit notify.

## 7. Manual Capture Drop Zone Loop (Minimal)
Use this minimal loop when one or two repos are active and manual visual evidence is required.

- **1) Initialize Quant evidence structure (once per phase/task):**
  - `powershell -ExecutionPolicy Bypass -File E:\Code\SOP\quant_current_scope\scripts\init_manual_capture_repo.ps1 -RepoRoot E:\Code\Quant -TaskId T31`
- **2) Create one global drop zone shortcut (single file):**
  - `powershell -ExecutionPolicy Bypass -File E:\Code\SOP\quant_current_scope\scripts\setup_manual_capture_dropzone.ps1 -DropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop -ShortcutName "E2E Evidence Drop.lnk"`
- **3) Register Quant watcher task (logon auto-start, single-occupancy):**
  - `powershell -ExecutionPolicy Bypass -File E:\Code\SOP\quant_current_scope\scripts\register_manual_capture_watcher_task.ps1 -TaskName ManualCapture-Quant-P31 -RepoRoot E:\Code\Quant -DropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop -AcceptAnyFilename -SingleOccupancy -OwnerId ManualCapture-Quant-P31 -RepoKey Quant`
- **4) Mark Quant as active owner in shared drop zone:**
  - `powershell -ExecutionPolicy Bypass -File E:\Code\SOP\quant_current_scope\scripts\set_manual_capture_active_owner.ps1 -DropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop -OwnerId ManualCapture-Quant-P31`
- **5) Verify task registration:**
  - `Get-ScheduledTask -TaskName "ManualCapture-Quant-*"`
- **6) Optional one-shot verification (no write):**
  - `.venv\Scripts\python E:\Code\SOP\quant_current_scope\scripts\manual_capture_watcher.py --dry-run --index E:\Code\Quant\docs\context\e2e_evidence\index.md --queue E:\Code\Quant\docs\context\e2e_evidence\manual_capture_queue.json --alerts E:\Code\Quant\docs\context\e2e_evidence\manual_capture_alerts.json --drop-dir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop --evidence-dir E:\Code\Quant\docs\context\e2e_evidence --accept-any-filename --single-occupancy --owner-id ManualCapture-Quant-P31 --repo-key Quant --repo-root E:\Code\Quant --print-json`
- **Drop-and-go behavior:**
  - user can drop screenshots with any filename into `E2E Evidence Drop`; worker auto-assigns FIFO and auto-renames into canonical evidence filenames.
