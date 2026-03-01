# Phase 31 Brief - Sovereign Execution Hardening

Date: 2026-03-01
Status: Active (Round 1 SAW reconciliation complete)

L1: Backtest/Execution Platform Reliability
L2 Streams: Backend, Data, Ops
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD

## Scope
- In scope:
  - signed trust-boundary replay hardening (`execution/signed_envelope.py`) with atomic check+append and malformed-ledger quarantine,
  - async telemetry spool integrity hardening (`execution/microstructure.py`) for idempotent sink replay, bad-record quarantine, stale-offset reset, bounded compaction, and durability fsync paths,
  - local-submit durability gate (`main_console.py`) so post-submit success is blocked when telemetry flush is unhealthy,
  - semantic contract hardening for snapshot/boolean/ranking paths (`strategies/alpha_engine.py`, `strategies/ticker_pool.py`),
  - atomic watchlist persistence hardening (`core/dashboard_control_plane.py`).
- Out of scope:
  - new strategy alpha research,
  - broker API expansion,
  - full-phase closeout handover/context refresh.

## Acceptance Checks
- CHK-01: Replay check+append is atomic across processes and replay duplicates are rejected fail-closed.
- CHK-02: Malformed replay-ledger lines are quarantined and do not block valid submits.
- CHK-03: Spool replay to sinks is idempotent under partial sink failures.
- CHK-04: Schema-invalid or stale-partial spool lines are quarantined with cursor progress.
- CHK-05: Local submit fails closed when telemetry durability gate fails.
- CHK-06: Robust semantic controls remain executable (`robust_sigma = max(1.4826 * MAD, epsilon_floor)` + fallback telemetry), with snapshot contracts explicit.
- CHK-07: Risk-invariant guards are runtime-enforced (`ValueError`, not `assert`) and malformed date policy is explicit.
- CHK-08: Integrated targeted regression matrix passes.

## Evidence Commands
- `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py`
- `.venv\Scripts\python -m py_compile execution/signed_envelope.py execution/microstructure.py main_console.py strategies/alpha_engine.py strategies/ticker_pool.py core/dashboard_control_plane.py tests/test_signed_envelope_replay.py tests/test_execution_microstructure.py tests/test_alpha_engine.py tests/test_ticker_pool.py tests/test_dashboard_control_plane.py`

## Artifacts
- `execution/signed_envelope.py`
- `execution/microstructure.py`
- `main_console.py`
- `strategies/alpha_engine.py`
- `strategies/ticker_pool.py`
- `core/dashboard_control_plane.py`
- `tests/test_signed_envelope_replay.py`
- `tests/test_execution_microstructure.py`
- `tests/test_alpha_engine.py`
- `tests/test_ticker_pool.py`
- `tests/test_dashboard_control_plane.py`

## Round Update (2026-03-01) - Stream 5 Adaptive Heartbeat Extension
- Status: In progress (Stream 5 execution-quant extension completed; SAW reconciliation pending).
- Added in this round:
  - adaptive heartbeat freshness telemetry (rolling MAD + hard ceiling) in `execution/microstructure.py`,
  - historical backfill runner: `scripts/backfill_execution_latency.py`,
  - baseline signed slippage evaluator: `scripts/evaluate_execution_slippage_baseline.py`,
  - new regressions in `tests/test_execution_microstructure.py` and `tests/test_execution_stream5_scripts.py`.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py tests/test_execution_controls.py tests/test_main_console.py`
  - `.venv\Scripts\python -m py_compile execution/microstructure.py scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py`

## Round Update (2026-03-01) - Stream 1 Option 1 Isolated Inherited-High Closure
- Status: Completed (SAW PASS, no unresolved in-scope Critical/High for Option1 scope).
- Added in this round:
  - as-of anchored `yearly_union` selector semantics in `data/feature_store.py`:
    - `anchor_date := append_start_ts` (incremental) or `start_ts` (full),
    - liquidity cutoff `date <= anchor_date`,
    - eligible years `year < year(anchor_date)` with earliest-year bootstrap fallback.
  - fail-closed feature-spec executor contracts in `data/feature_store.py`:
    - missing inputs, missing fundamental dependencies, runtime exceptions, invalid non-DataFrame outputs, and post-processing failures now raise `FeatureSpecExecutionError`.
  - regression coverage in `tests/test_feature_store.py` for:
    - as-of anchoring, same-day spike exclusion, patch-overlay precedence before anchor,
    - fail-closed spec exception/input/dependency/type handling and derived-dependency allowance.
- Verification:
  - `.venv\Scripts\python -m py_compile data/feature_store.py tests/test_feature_store.py` -> PASS
  - `.venv\Scripts\python -m pytest tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py -q` -> PASS (`[100%]`)

## Round Update (2026-03-01) - Option 1 Medium-Risk Reconciliation Sprint
- Status: Completed (SAW reconciliation pass complete for this round scope).
- Added in this round:
  - `execution/microstructure.py`:
    - deterministic business-key spool UID assignment (ignores `captured_at_utc` for retry idempotency),
    - truthful immediate-write accounting (`spool_records_appended` durable-only),
    - explicit `orders_prepared`/`fills_prepared` vs immediate `orders_written`/`fills_written`,
    - bounded retry buffer with fail-closed overflow (`RuntimeError`),
    - buffered-drain batch cap + retry backoff behavior,
    - UID preservation during spool read (`_spool_record_uid` no longer always offset-derived),
    - fail-closed shutdown gate when buffered/pending telemetry remains at stop.
  - `execution/signed_envelope.py`:
    - replay-ledger parent-directory `fsync` after rewrite `os.replace`,
    - malformed ledger detection now fail-closed (quarantine + rewrite + reject current submit),
    - replay ledger growth cap (`TZ_EXECUTION_REPLAY_LEDGER_MAX_ROWS`, default `50_000`) with trim telemetry event,
    - replay lock timeout default increased from `5ms` to `25ms` (still aggressively bounded).
  - `core/dashboard_control_plane.py` + `app.py`:
    - `pd.NaT` and null-like date tokens handled before date-type short-circuit in planner coercion,
    - spinner date label now sourced from planner normalized date key (no direct `.date()` on raw value).
  - Tests:
    - `tests/test_execution_microstructure.py`:
      - post-write append error no-duplicate assertion,
      - overflow fail-closed assertion,
      - cross-call retry idempotency assertion,
      - missing broker ack -> `latency_missing` heartbeat block assertion,
      - shutdown fail-closed assertion when buffered records remain.
    - `tests/test_signed_envelope_replay.py`:
      - malformed replay ledger now fail-closed on first attempt + subsequent clean retry path,
      - parent-dir `fsync` hook assertion after ledger rewrite.
    - `tests/test_dashboard_control_plane.py`:
      - `pd.NaT` invalid-state regression.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py` -> PASS (`58 passed`).
  - `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py` -> PASS (`256 passed`).
  - `.venv\Scripts\python -m py_compile execution/microstructure.py execution/signed_envelope.py core/dashboard_control_plane.py app.py tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py` -> PASS.

## Round Update (2026-03-01) - Stream 1 PiT Look-Ahead Bias Reconciliation Sprint
- Status: Completed (SAW reviewer recheck PASS; no unresolved in-scope Critical/High).
- Added in this round:
  - `data/fundamentals.py`:
    - timestamp-precision dual-time PiT gate (`published_at <= simulation_ts` and `release_date <= simulation_ts`),
    - strict-mode timestamp binding helpers + enforcement (`T0_STRICT_SIMULATION_TS_BINDING`, `T0_SIMULATION_TS_BINDING_SECRET`),
    - fallback daily-path valid-time mask and non-negative age quality gate,
    - deterministic dedupe tie-break (`_row_hash`) for equal-key/equal-`ingested_at` rows.
  - `data/feature_store.py`:
    - active `yearly_union` selector converted to strict t-1 daily-liquidity ranking (`date < anchor`, last tradable date),
    - strict-binding token/secret plumbing from feature-store compute path into fundamentals loaders.
  - tests:
    - `tests/test_bitemporal_integrity.py`: exact timestamp restatement crossover, fallback no-leak valid-time gate, deterministic dedupe tie regression.
    - `tests/test_feature_store.py`: strict-binding plumbing regression + t-1 selector adversarial tests.
    - `tests/test_fundamentals_daily.py`: fallback monkeypatch compatibility for new loader args.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py` -> PASS (`45 passed`).
  - `.venv\Scripts\python -m py_compile data/fundamentals.py data/feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py` -> PASS.

## Round Update (2026-03-01) - Stream 1 Cleanup Slice (Legacy Helper Retirement)
- Status: Completed (SAW PASS; no unresolved in-scope Critical/High).
- Added in this round:
  - `data/feature_store.py`:
    - removed legacy helper `_select_permnos_from_annual_liquidity`,
    - kept active runtime selector stack unchanged (`_select_universe_permnos -> _top_liquid_permnos_yearly_union`) with strict t-1 anchor semantics.
  - `tests/test_feature_store.py`:
    - removed retired-helper tests,
    - added active dispatch regression ensuring yearly-union path calls only active anchor selector,
    - retained as-of anchor, same-day spike exclusion, and patch precedence regressions.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py` -> PASS (`43 passed`).
  - `.venv\Scripts\python -m py_compile data/feature_store.py tests/test_feature_store.py` -> PASS.

## Round Update (2026-03-01) - Stream 5 Authoritative Receipt Gate Pivot
- Status: Completed (targeted Stream 5 matrix PASS).
- Added in this round:
  - `main_bot_orchestrator.py`:
    - hardened `ok=True` success acceptance to require authoritative receipt fields:
      - `filled_qty`, `filled_avg_price`, `execution_ts`,
    - sparse success payloads now force reconciliation polling via `get_order_by_client_order_id`,
    - unresolved sparse success after poll budget now raises `AmbiguousExecutionError`,
    - `already exists` recovery-success path now enforces the same authoritative receipt contract.
  - `execution/broker_api.py`:
    - added canonical `execution_ts` resolver from fill telemetry (`fill_summary.first_fill_ts` / `partial_fills.fill_ts` / `filled_at`) in submit-acceptance normalization.
  - Tests:
    - `tests/test_main_bot_orchestrator.py`:
      - sparse `ok=True` reconciliation success path regression,
      - sparse `already exists` ambiguity fail-closed regression,
      - updated success-path doubles to include authoritative execution fields.
    - `tests/test_execution_controls.py`:
      - asserted `execution_ts` is emitted for activity-derived and snapshot-fallback fill paths.
- Verification:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/broker_api.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py` -> PASS.
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`[100%]`).

## Round Update (2026-03-01) - Stream 5 Final Cleanup (Event-Time + Cohort Alignment)
- Status: Completed (targeted Stream 5 cleanup matrix PASS).
- Added in this round:
  - `execution/microstructure.py`:
    - heartbeat bootstrap history now requires explicit event-time ordering (`COALESCE(TRY_CAST(...))`) and removes unordered fallback.
    - positive-float coercion now rejects non-finite values (`inf`, `-inf`, `nan`) in execution-cost paths.
  - `scripts/backfill_execution_latency.py`:
    - backfill ordering now uses coalesced event-time key (`execution_ts/arrival_ts/submit_sent_ts/broker_ack_ts/filled_at/captured_at_utc/...`) with deterministic tie-breaks.
  - `scripts/evaluate_execution_slippage_baseline.py`:
    - baseline denominator now uses intended cohort rows with `cohort_slippage_bps = slippage_bps if observed else 0.0`,
    - non-finite numeric values are sanitized before cohort aggregation,
    - added `cohort_rows` and `zero_imputed_rows`,
    - side/symbol rollups now include full cohort rows plus `observed_rows`.
  - Tests:
    - `tests/test_execution_microstructure.py`: event-time bootstrap ordering regression.
    - `tests/test_execution_stream5_scripts.py`: event-time backfill sort regression + cohort-aligned slippage assertions.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py tests/test_execution_controls.py tests/test_main_console.py` -> PASS.
  - `.venv\Scripts\python -m py_compile execution/microstructure.py scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py` -> PASS.

## Round Update (2026-03-01) - Stream 5 Option 2 (Fail-Loud Script Source Contract)
- Status: Completed (targeted Stream 5 script matrix PASS).
- Added in this round:
  - `scripts/backfill_execution_latency.py`:
    - removed implicit DuckDB->Parquet fallback behavior,
    - added strict source mode contract:
      - default `duckdb_strict`,
      - explicit `parquet_override` only via CLI/env,
    - added fatal `PrimarySinkUnavailableError` for strict-mode DuckDB unavailability/query failures.
  - `scripts/evaluate_execution_slippage_baseline.py`:
    - mirrored the same strict source-mode contract and fatal failure semantics.
  - `tests/test_execution_stream5_scripts.py`:
    - strict-mode missing DuckDB fail-loud regression,
    - strict-mode query-error fail-loud regression,
    - explicit parquet override (CLI token and env override) regressions.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_execution_stream5_scripts.py` -> PASS.

## Round Update (2026-03-01) - Stream 5 Sprint+1 Follow-Through (Telemetry Constraints Hardening)
- Status: Completed (SAW reviewer recheck PASS; no unresolved in-scope Critical/High).
- Added in this round:
  - `main_bot_orchestrator.py`:
    - strict authoritative success gate hardened with:
      - parseable timezone-aware `execution_ts` normalization to UTC,
      - `filled_qty > 0`,
      - `filled_avg_price > 0`,
      - fill quantity bound `filled_qty <= order.qty`,
    - `ok=True` required-field validation made non-mutating (`candidate = dict(result)`),
    - reconciliation loop now uses per-poll timeout (`EXECUTION_RECONCILIATION_LOOKUP_TIMEOUT_SECONDS`) and issue-tag propagation into `AmbiguousExecutionError`,
    - duplicate output rows for the same `client_order_id` now fail closed deterministically (`duplicate_batch_result_cid`) via pre-scan CID counting before per-row acceptance logic.
  - `tests/test_main_bot_orchestrator.py`:
    - malformed `execution_ts` ambiguity regression,
    - overfilled quantity bound ambiguity regression,
    - duplicate CID fail-closed regression and row-order permutation coverage,
    - reconciliation lookup-timeout regression,
    - zero reconciliation poll-budget regression.
- Verification:
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`61 passed`).
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`[100%]`).
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
  - SAW reviewer recheck:
    - Reviewer A PASS,
    - Reviewer B PASS,
    - Reviewer C PASS.

## Round Update (2026-03-01) - Phase 31 Closeout Protocol
- Status: In Progress (artifact sealed; governance gate blocked by inherited full-repo failure).
- Closeout checks executed:
  - CHK-PH31-01 Full-repo matrix:
    - `.venv\Scripts\python -m pytest --maxfail=1` -> BLOCK (`472 passed, 1 failed, 2 warnings in 50.94s`).
    - evidence: `docs/context/e2e_evidence/phase31_chk_ph_01_pytest.log`.
    - failing test: `tests/test_phase15_integration.py::test_phase15_weights_respect_regime_cap` (`strategies/alpha_engine.py:488` single-day precomputed-field requirement violation).
  - CHK-PH31-02 Runtime smoke:
    - controlled dry-run of `main_bot_orchestrator.main()` with patched schedule loop -> PASS (`SMOKE_OK run_scanners=1 run_pending=1`).
    - evidence: `docs/context/e2e_evidence/phase31_chk_ph_02_smoke.log`.
  - CHK-PH31-03 Context packet refresh:
    - `docs/handover/phase31_handover.md` published with explicit New Context Packet block.
    - `.venv\Scripts\python scripts/build_context_packet.py --repo-root .` -> PASS.
    - `.venv\Scripts\python scripts/build_context_packet.py --repo-root . --validate` -> PASS.
  - CHK-PH31-04 Stream 1/5 isolation matrix:
    - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py --maxfail=1` -> PASS (`198 passed in 7.37s`).
    - evidence: `docs/context/e2e_evidence/phase31_chk_ph_04_stream_matrix.log`.
- Phase 32 carryover lock:
  - batch exception taxonomy split (transient vs non-transient),
  - routing diagnostics tail,
  - UTF-8 decode wedge backlog,
  - UID drift backlog,
  - inherited Phase 15 integration failure triage/fix.

## Round Update (2026-03-01) - Stream 5 SAW Reconciliation (D-209)
- Status: Completed (SAW PASS for Stream 5 scope).
- Scope completed in this round:
  - hardened authoritative success gate to require broker-origin `client_order_id` for all `ok=True` acceptances,
  - canonicalized terminal execution taxonomy (`terminal_reason`, canonical `error`, normalized `status`, preserved `broker_error_raw`),
  - added deterministic batch exception retry/exhaustion handling in orchestrator execution loop.
- Acceptance checks:
  - `CHK-01` Broker CID required on `ok=True` success paths -> PASS.
  - `CHK-02` Sparse success without broker CID fails closed via ambiguity path -> PASS.
  - `CHK-03` Terminal outcomes use canonical taxonomy (unfilled/partial) -> PASS.
  - `CHK-04` Batch submit exceptions are retry-aware and fail closed on exhaustion -> PASS.
  - `CHK-05` Targeted Stream 5 matrix remains green -> PASS.
- Verification:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`198 passed`).
  - SAW final reviewer confirmations -> PASS:
    - Reviewer A: PASS,
    - Reviewer B: PASS,
    - Reviewer C: PASS.
- Deferred/open follow-up (non-blocking for this round):
  - long-run reconciliation-timeout soak and daemon-thread cancellation hardening under prolonged hanging lookup calls.
