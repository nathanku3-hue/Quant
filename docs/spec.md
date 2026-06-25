V2 PEAD Alpha Interpretation Gate Contract (2026-06-24)

- Gate file: `docs/phase_brief/v2-pead-alpha-interpretation-gate.md`.
- Evidence file: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.
- Current maximum claim: descriptive PEAD-style methodology evidence only, with no alpha, tradeability, PIT, net, causal, full-factor, or population-validity claim.
- Path A: descriptive evidence panel only after gate approval, with hard disclaimers.
- Path B: M5 PIT/data/method upgrade before any real alpha assertion.
- Hard stop: no alpha-named dashboard/code until gate approval and 28-commit/main reconciliation.

V2 PEAD M4A Memory-Bounded Full-Universe Expansion Contract (2026-06-22)

- Hierarchy: L1 Terminal Zero quantitative research console; L2 active streams Data and Docs/Ops; L2 deferred streams Strategy interpretation and Frontend/UI; L3 M4A local full-universe expansion implementation with terminal closure blocked pending reviewers and a clean full-suite exit.
- Implementation paths: scripts/pead_d2_return_contract.py::build_full_contract and scripts/pead_d2b_event_window_contract.py::build_full_contract.
- D2A full build uses bounded DuckDB execution with one thread, 512 MB memory limit, disk spill, and row-grouped Parquet. Sample D2A behavior remains available and unchanged.
- D2A formula is unchanged: TR_level_t = prccd_t * trfd_t / ajexdi_t; total_return_t = TR_level_t / TR_level_{t-1} - 1; fallback price returns use prccd / ajexdi; all lags remain inside (gvkey, iid).
- D2B full build resolves D1/D2A manifests by metadata/hash, validates full D2A lazily, and writes event windows through bounded SQL and row-grouped Parquet.
- D2B fixed-security semantics are unchanged: prior 20 authoritative sessions, minimum 15 finite dollar_volume observations, deterministic score/count/IID/security tie-break, one fixed security per event, and exact +1..+60 session skeleton.
- Publication remains immutable hash-named Parquet followed by atomic manifest pointer replacement. Failed pre-commit publication preserves the previous pointer and cleans temporary files.
- M4A authorizes local code/test readiness only. It does not authorize provider access, PIT EPS/population/tradable alpha claims, estimator/UI changes, ranking/scoring, alerts, recommendations, broker/order actions, or new data artifact publication in this round.
- Evidence: focused D2A/D2B tests PASS 55/55; broader PEAD D2/D3/event-study tests PASS 79/79; latest targeted non-M4A rerun fails in execution microstructure spooler status/teardown while context-hygiene and timing checks pass; full repository pytest rerun reached 100% with no failure summary but did not return an exit code and was stopped; terminal Reviewer A/B/C unavailable due subagent usage limit.

V2 PEAD Calendar-Time Inference M1B Contract (2026-06-21)

- `m1b_evidence_path = docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`.
- `m1b_evidence_sha256 = c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`.
- `protected_validation_json_sha256 = 96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- `R_HL,t = EW(raw return | active Q5, t) - EW(raw return | active Q1, t)`.
- `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`; HAC uses `maxlags = 59` and `use_correction = true`.
- Formation runs all-quantile latest-event `(security_id, return_date)` resolution before Q1/Q5 filtering; no-security extreme rows remain expected missing and missing latest returns do not fall back to older events.
- Robustness-only bootstrap: paired stationary block bootstrap, expected block length 60, 10,000 replications, seed 20260621, max batch size 256.
- `non_null(D2B.return_date) subset_of D3.return_date`; any off-spine date fails closed before estimation.
- `extreme_expected = extreme_finite + extreme_missing`, with matching Q1/Q5 sums and rates bounded to `[0,1]`; zero retained sessions use null retained-date endpoints.
- `--calendar-time-m1b` output is fixed to the resolved canonical evidence path.
- `allowed_use = bounded_methodology_review_only`; no product/action authority is added.

V2 PEAD Read-Only Evidence Dashboard Contract (2026-06-20)

- `surface = Strategy Research Replay -> Read-Only Evidence`.
- `renderer = views/pead_validation_evidence.py`; `evidence_path = docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.
- `expected_sha256 = 96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- `failure_policy = fail_closed_before_metrics_or_lineage_render` for missing JSON, hash mismatch, schema mismatch, or unreadable limitations.
- `allowed_use = owner_review_only`; no provider, Parquet, recomputation, write, rank/score, alert, recommendation, or broker/order capability is added.

V2 PEAD D3 Benchmark Artifact Publication Contract (2026-06-20)

- `benchmark_manifest_path = data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`.
- `benchmark_parquet_file = data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`.
- `benchmark_rows = 2810`; `date_min = 2015-01-02`; `date_max = 2026-03-06`.
- `required_d2b_sessions = 2810`; `matched_d2b_sessions = 2810`; `missing_d2b_sessions = []`.
- `source_release = "This file was created by using the 202604 CRSP database."`.
- `source_download_sha256 = 4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`.
- `benchmark_return = (Mkt-RF_percent / 100) + (RF_percent / 100)`.
- `artifact_sha256 = f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`.
- `allowed_use = benchmark_input_for_pead_d3_only`.
- No CAR/BHAR interpretation, dashboard, ranking/scoring, alert, broker/order, provider expansion, full-build, staging, or commit authority is added.

V2 PEAD D2B Authoritative Market-Session Contract (2026-06-19)

- Hierarchy: L1 Terminal Zero quantitative research console; L2 active streams Data and Docs/Ops; L2 deferred streams Strategy interpretation and Frontend/UI; L3 D2B session-spine repair in final verification.
- `S_market = KenFrenchDaily.return_date` restricted to the D2A date range; distinct D2A dates are source observations, not calendar authority.
- D2B selection remains prior-20 authoritative sessions, minimum 15 finite `dollar_volume` observations, and deterministic mean/count/IID/security ordering.
- The active D2B manifest records 2,810 sessions, 52 excluded non-session dates, 11,450 eligible events, and SHA256 `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`.
- D3 must validate the exact source release/hash and D2B session hash before construction; no date coercion inside D3 is allowed.
- Strategy handoff performs full D2A validation in bounded chunks, enforces exact normalized key uniqueness with a bounded DuckDB composite primary key, validates event metadata across all 60 rows, and materializes only selected-security canonical return columns before calling the existing strategy algorithm.

V2 PEAD D3 Benchmark Artifact Builder Contract (2026-06-19)

- `benchmark_builder_path = scripts/pead_d3_benchmark_artifact.py`.
- `benchmark_test_path = tests/test_pead_d3_benchmark_artifact.py`.
- `source = official Ken French daily Fama/French 3 Factors ZIP`.
- `mktrf = Mkt-RF_percent / 100`; `rf = RF_percent / 100`; `benchmark_return = mktrf + rf`.
- `publication_protocol = immutable_hash_named_parquet_then_atomic_manifest_pointer`.
- `publication_status = pending_separate_approval`; the historical 52-date coverage blocker is repaired and current in-memory coverage is 2,810 / 2,810.
- `strategy_summary_raw_return_preserved = true` when the asset window is complete but benchmark coverage is missing; `car`, `bhar`, `window_complete`, and `eligible_for_analysis` remain blocked.
- No CAR/BHAR interpretation, dashboard, ranking/scoring, alert, broker/order, full-build, staging, or commit authority is added.

V2 PEAD D2B Fixed Event-Security Window Contract (2026-06-19)

- Hierarchy: L1 Terminal Zero quantitative research console; L2 active streams Data and Docs/Ops; L2 deferred streams Strategy and Frontend/UI; L3 D2B bounded Data slice DONE with final Reviewer A/B recheck pending.
- For event `e`, use the last 20 global sessions strictly before `event_date`; candidate `i` is eligible when finite `dollar_volume` count is at least 15, then sort mean descending, count descending, normalized `iid` ascending, and `security_id` ascending.
- Select exactly one fixed event-level security. No `IID01` preference, fallback, or within-window switch is allowed.
- `return_date(e,k)` is the `k`th global market session after the event for `k=1..60`; missing rows remain null and do not compress event time.
- `handoff_eligible` requires all 60 return dates and all 60 finite selected-security returns. Strategy receives only eligible events, unique canonical D2A return keys, and the same global spine through `strategies/pead_event_study.py`.
- Input manifest/hash validation and pandas reads are bound to stable byte snapshots. Publish immutable Parquet first and atomically replace the manifest pointer; clean all pre-commit temporary/versioned outputs on `BaseException`.
- Implementation: `scripts/pead_d2b_event_window_contract.py`; tests: `tests/test_pead_d2b_event_window_contract.py`; artifact manifest: `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json`.
- D2B is not PEAD phase-end. The only next recommendation is a bounded D3 benchmark-input contract/design gate; provider fetch and alpha interpretation require separate approval.

G7.1A Canonical Notice (2026-05-09)

The current product/spec canon is the root-level `PRD.md` and `PRODUCT_SPEC.md`.

V2 PEAD D2A Security-Level Return Contract (2026-06-18)

- Hierarchy remains L1 Terminal Zero quantitative research console; L2 active streams Data and Docs/Ops; L2 deferred streams Strategy and Frontend/UI; L3 stage is Executing D2A.
- `security_id = gvkey + "-" + iid`; all stateful levels, lags, guardrails, and returns are grouped by `(gvkey, iid)`.
- `TR_level_t = prccd_t * trfd_t / ajexdi_t` and `total_return_t = TR_level_t / TR_level_{t-1} - 1`.
- Fallback is `((prccd_t / ajexdi_t) / (prccd_{t-1} / ajexdi_{t-1})) - 1` within the same security when the total-return level pair is unavailable.
- Output uniqueness is `(security_id,date)`; exact cross-source overlap prefers the newer daily source, while same-source duplicates fail closed.
- Publish the immutable hash-named Parquet first, then atomically replace the manifest commit pointer under a single-writer OS lock; matching SHA256 is mandatory. `dollar_volume` is not ADV.
- D2A rejects `--build` and requires exactly 500 sample GVKEYs.
- D2A is limited to the 500-GVKEY sample. D2B owns event-level IID selection and `+60` market sessions.

V2 PEAD D1 Repair Contract (2026-06-18)

- Hierarchy remains unchanged: L1 Terminal Zero quantitative research console; L2 active streams Data and Docs/Ops; L2 deferred streams Strategy and Frontend/UI; L3 stage is Final Verification for D1 and Planning for separate D2.
- `adj_eps = numeric(epspxq)` with no `ajexq` division; the legacy name is retained for compatibility.
- Deduplicate `(gvkey, rdq)` before exact t-4 and rolling calculations.
- Preserve raw `sue_price_scaled`; add within-RDQ `+/-5 * std` `sue_price_scaled_clipped`.
- `liquidity_pass = prccq_lag1 * cshoq_lag1 > 50`, where `cshoq_lag1` is in millions; this is a flag only and `valid_sue` is independent.
- Parquet and manifest use temp-to-replace. Rebuilt SHA256 is `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Quality gate: raw `abs(sue_price_scaled) > 5` must remain below 0.5% of valid rows; current artifact is 441 / 233,586 = 0.1888%.
- Empty processed-output paths fail before publication, preserving the prior bundle.
- D1 is current-vintage Compustat EPS only; strict filing-vintage PIT EPS/restatement-hindsight exclusion is not established.
- No architecture redesign is introduced. D2, Ken French, and provider work remain separate.

V2 PEAD Strategy Contract Notice (2026-06-18)

- `strategy_contract_path = strategies/pead_event_study.py`.
- `event_schema = {event_id, issuer_id, security_id, event_date, sue, is_primary_security}` and requires one primary security per issuer/event date.
- `event_window = market_sessions[+1:+60]`, where `+1` is the first market session strictly after `event_date`; missing security returns remain null skeleton rows.
- `raw_window_return = product(1 + total_return_d) - 1`.
- `CAR = sum(total_return_d - benchmark_return_d)` and `BHAR = product(1 + total_return_d) - product(1 + benchmark_return_d)` only with an explicit benchmark column.
- `quantile_scope = event_date_cohort` by default; wider ex-post cohorts require `allow_ex_post_cohorts=True` and remain descriptive-only.
- `spread_inference = HAC(Newey-West) on cohort-level Q_high - Q_low`.
- `strategy_saw_rerun_status = PASS`; `strategy_handoff_ready = true` only for corrected D1/D2 rows and synthetic/contract smoke.
- Strategy contract does not read/write data artifacts and does not approve D1/D2, primary-IID, total-return, benchmark, alpha, ranking, or promotion claims.

V2-D0.4C Local Read-Only Permission Probe Approval Notice (2026-06-03)

- `d0_4c_status = PASS_DOCS_ONLY_APPROVAL`.
- `local_human_probe_approval = approved_for_future_run`.
- `execution_in_d0_4c = false`.
- `probe_scope = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `row_state = probe_approved_not_executed AND not_formally_approved AND approval_ref == null`.
- `allowed_output = exact_five_row_accessible_true_false_or_redacted_error_only`.
- `permission_truth = not_closed`.
- `next_packet = V2_D0_4D_LOCAL_HUMAN_PROBE_EXECUTION_PACKET`.
- No credential read, `secret.txt` read, Codex/subagent login, WRDS execution in D0.4C, discovery helper, schema discovery, row count, sample row, snapshot, data output, runtime/dashboard/scoring/broker write, approval_ref change, SafeBoot, or BootReady is authorized.

V2-D0.4B WRDS Local Auth Method Confirmed Notice (2026-06-03)

- `round_id = ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED`.
- `scope_id = V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION`.
- `required_decision_language = "WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed."`
- `local_auth_method = user_attested_local_auth_available`.
- `actual_login_verified_by_agent = false`.
- `credentials = local_only_do_not_read_do_not_quote_do_not_commit`.
- `secret_txt = do_not_read_do_not_quote_do_not_use`.
- `formal_approval_ref = null`.
- `permission_truth = not_closed`.
- `wrds_execution = governance_blocked_until_probe_approval`.
- `s_and_p_capital_iq_pro = deferred_fallback`.
- `v2_d0_4b_valid = local_auth_method_user_attested AND not actual_login_verified_by_agent AND credentials_not_read AND secret_txt_not_used AND formal_approval_ref_null AND permission_truth_not_closed AND probe_execution_blocked`.
- Rows `{crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}` remain `probe_plan_pending`, `not_approved`, and `approval_ref=null`.
- No secret/credential read, provider login, SSH, Python WRDS, SAS, SQL, discovery, row count, sample row, snapshot, data output, runtime write, approval_ref fabrication, or row approval is authorized.

V2-D0.2 WRDS Entitlement Evidence Request Notice (2026-06-03)

- `evidence_request_round = ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST`.
- `evidence_request_status = REQUEST_PREPARED_EVIDENCE_MISSING`.
- `evidence_request_is_approval = false`.
- `evidence_request_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `all_rows_pending = evidence_status == evidence_missing AND permission_status == pending AND approval_ref == null`.
- `next_human_action = send_copyable_request_to_authorized_institutional_contact`.
- `row_approval_valid = dated_attributable_non_secret_entitlement_evidence_present AND exact_approval_ref_present`.
- No WRDS/provider access, credential use, probe execution, schema/table discovery, row count, snapshot, data write, dashboard/runtime, scoring/ranking, alert, broker path, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.

V2-D0.1 Authorization Intent Evidence Missing Notice (2026-06-03)

- `authorization_intent_round = ROUND-20260603-V2-D0-1-AUTHORIZATION-INTENT`.
- `authorization_packet_status = INTENT_RECORDED_EVIDENCE_MISSING`.
- `authorization_packet_is_final_approval = false`.
- `authorization_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `all_rows_pending = evidence_status == evidence_missing AND permission_status == pending AND approval_ref == null`.
- `secret_txt_status = local_secret_material_not_non_secret_entitlement_evidence`.
- `TODO_ENTITLEMENT_001 = PENDING_BLOCKING`; `TODO_APPROVAL_001 = PENDING_BLOCKING`.
- No WRDS/provider access, credential use, probe execution, snapshot, data write, dashboard/runtime, scoring/ranking, alert, broker path, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.

V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping Notice (2026-06-02)

- `todo_matrix_001_status = resolved`.
- `permission_truth_artifact = v2_discovery/data_lab/permission_truth.py`.
- `permission_truth_tests = tests/test_v2_wrds_permission_truth_scope.py + tests/test_v2_wrds_permission_matrix.py + tests/test_v2_data_lab_no_v1_writes.py`.
- `permission_truth_test_evidence = PASS_51_tests`; `permission_truth_compileall = PASS`.
- `v2_d0_1_default_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `permission_status_default = pending`.
- `approval_valid = row_table_approval_ref_present AND allowed_uses == ["provenance_contract"]`.
- `ibes_det_epsus_v2_d0_1_status = pending`.
- `ibes_det_epsus_pead_v2_001_starter_scope = not_requested`.
- No WRDS/provider access, credentials, probe, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, legacy cleanup, public/main closure, or V2 validity/C3 lock claim is authorized.

V2-D0.1 Scope and Clean-Room Runtime Decision Notice (2026-06-02)

- Scope artifact: `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`.
- `v2_d0_1_entitlement_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `pead_v2_001_compustat_starter_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq}`.
- `ibes_det_epsus_v2_d0_1_status = pending_once_requested`.
- `ibes_det_epsus_pead_v2_001_starter_scope = not_requested`.
- `cleanroom_runtime_schema_registry_default = excluded`.
- `cleanroom_schema_registry_exception_valid = hard_reviewed_import_dependency AND hash_pinned AND local_static_validation_only AND no_provider_imports AND no_root_imports AND no_schema_table_column_library_rowcount_metadata_enumeration AND clean_import_provenance AND clean_forbidden_scan`.
- `TODO_PEAD_DECISION_001 = RESOLVED`.
- `TODO_CLEANROOM_RUNTIME_001 = RESOLVED`.
- No WRDS/provider access, credentials, probe, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized.

V2-D0.1 Expert 1-6 Follow-Up Reconciliation Notice (2026-06-02)

- Follow-up artifact: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`.
- `v2_d0_1_default_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `pead_compustat_starter_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq}`.
- `pead_ibes_primary_rows = v2_d0_1_default_rows`.
- `pead_starter_decision_open = 1` until PM/Quant chooses I/B/E/S analyst-surprise first cell vs Compustat-rdq starter.
- `v2_d0_1_permission_truth_artifact_valid = 1` only if approved rows use `allowed_uses=["provenance_contract"]`; default V2-D0 matrix allowed-use planning labels are not approval authority.
- `research_valid_pead = 1` only if `C3_LOCK_PEAD_V2_001_v1` exists and HAC LCB95(delta)>0, annualized net alpha delta>=2%, FDR q<=0.05, DSR>=0.95, PBO<=0.10, base/2x cost stress pass, PEAD slippage stress passes, OOS/walk-forward evidence exists, leakage audit passes, negative controls pass, robustness passes, concentration checks pass, and reproducibility rerun passes.
- No WRDS/provider access, credentials, probe, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized.

V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates Notice (2026-06-02)

- Expert 1-6 agreement ratings are captured as `AGREE_HIGH`; exact numeric source values were not present in the handoff.
- V2-D0.1 authority is entitlement-only: `approval_ready = entitlement_evidence_present AND explicit_non_secret_approval_text_present`.
- Row-level validator status is `PATCH_RESOLVED` after tests; this remains no-provider/no-output contract evidence.
- Security gate: legacy WRDS helper surfaces remain quarantined risk until separately audited or retired.
- Quant Research gate: `PEAD_V2_001_BOUNDARY_PACKET` may exist only after WRDS/PIT authority is approved.
- Research Validity gate: `v2_alpha_research_valid = false` until `V2_ALPHA_VALIDITY_PACKET` exists and passes the research-validity runner contract.
- No WRDS/provider access, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, or BootReady is authorized.

V2-D0 Multi-Expert Reconciliation Gate Notice (2026-06-02)

- `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md` is the reconciled A/B/C expert verdict.
- Expert A: PASS boundary, but probe authorization is NEEDS USER EVIDENCE.
- Expert B: PATCH fixed by exact-key probe contract validation and snapshot storage schema parity.
- Expert C: PASS governance, dashboard HOLD, G9 context-only, no promotion readiness.
- `probe_contract_valid = exact_root_keys AND exact_dataset_row_keys AND root flags false AND next_allowed_action="record_permission_decision_only" AND denied_actions unchanged AND code_ref unchanged AND no credential/connection/output extras`.
- `snapshot_storage_valid = planned_storage_uri startswith "data/runtime_cache/v2_data_lab/" AND rejects bare prefix, V1 data paths, boot-status paths, absolute paths, drive letters, UNC paths, URI schemes, and traversal`.
- No WRDS/provider access, snapshot generation, data output persistence, V1 canonical mutation, dashboard runtime integration, ranking/scoring, recommendations, alerts, broker/order paths, SQLite storage, SafeBoot, or BootReady claim is authorized.

V2-D0 WRDS Permission + Snapshot Provenance Contract Notice (2026-06-01)

- `v2_discovery/data_lab/permission_matrix.py` is the contract owner for the WRDS permission matrix.
- `v2_discovery/data_lab/wrds_probe.py` is the offline probe-contract owner and must keep `wrds_connection_attempted = false`.
- `v2_discovery/data_lab/snapshot_manifest.py` is the contract-only snapshot manifest owner and must keep provider/snapshot/output/V1-write flags false.
- `v2_discovery/data_lab/schema_registry.py` validates against `contracts/data_snapshot/wrds_permission_matrix.schema.json` and `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`.
- `permission_matrix_sha256 = sha256(canonical_json(permission_matrix_without_created_at_utc))`.
- `snapshot_contract_valid = all(root write/provider flags false) AND all PIT policy flags true AND planned_storage_uri not in forbidden V1/boot prefixes`.
- Forbidden planned storage prefixes: `data/processed/`, `data/registry/`, `runtime/boot_status_current.json`, and `docs/context/boot_status_current.json`.
- No WRDS/provider access, snapshot generation, data output persistence, V1 canonical mutation, dashboard runtime integration, ranking/scoring, recommendations, alerts, broker/order paths, SQLite storage, SafeBoot, or BootReady claim is authorized.

V2 Alpha Factory Immediate Todo Directive Notice (2026-06-01)

- `docs/architecture/v2_alpha_factory_immediate_todo_directive_20260601.md` is a docs-only directive record.
- First TODO is a WRDS permission/PIT/provenance planning scope; subsequent TODOs are PEAD variants, corporate-actions variants, meta-labeling survival, and Orbis/BvD network shock.
- Proposed implementation paths under `v2_discovery/` remain unapproved until a clean bounded execution scope is selected.
- SQLite remains forbidden without explicit approval; candidate registry design must use repo-approved storage unless policy changes.
- No provider access, snapshot generation, candidate ranking/scoring, promotion, live trading, broker behavior, alerts, recommendations, autonomous allocation, or BootReady claim is authorized.
- Immediate next action: `prepare_wrds_permission_pit_provenance_planning_scope_or_hold`.

Boot Status Path Contract + Governance Scanner Integration Notice (2026-05-26)

- `core.boot_status.DEFAULT_BOOT_STATUS_PATH` and `BOOT_STATUS_CURRENT_PATH` point to `runtime/boot_status_current.json`.
- `BOOT_STATUS_CONTEXT_SNAPSHOT_PATH` points to `docs/context/boot_status_current.json` only as a noncanonical snapshot path; loaders do not use it as a safe-boot fallback.
- `scripts/boot_preflight.py --repo-root ...` imports and runs `run_governance_preflight(...)`, records `checks["governance"]`, and blocks on governance FAIL.
- Strict preflight may write boot status only with `--write-status`, only after PASS, and only to `runtime/boot_status_current.json`.
- Data-readiness, dashboard runtime smoke, replay/optimizer certification, and clean GitHub safe-boot proof remain separate gates before boot-ready can be claimed.
- No provider ingestion, canonical market-data write, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion is authorized.

Research Validity Runner v0 Notice (2026-05-26)

- `docs/architecture/research_validity_contract.md` defines the mechanical promotion rule: `No cartridge + no canonical engine run + no PIT proof + no benchmark + no costs + no evidence packet = not research-valid`.
- `research.backtest_runner.run_research_backtest(...)` is the v0 wrapper around `core.engine.run_simulation(...)`; research-valid paths force `strict_missing_returns=True`.
- V0 target weights are risky-asset-only and full-calendar: no `CASH` column, sorted unique dates matching the returns calendar, finite numeric long-only weights, and row sums `<= 1.0`.
- Evidence output is path-confined by safe `run_id`, written with temp files plus `os.replace`, and final `evidence_packet.json` is emitted only after component artifacts succeed.
- Cash is implicit residual weight; Rule100 replay remains `diagnostic_only` through `research.adapters.rule100_replay_adapter`.
- No provider ingestion, canonical market-data write, strategy promotion, ranking, scoring, recommendation, alert, broker automation, autonomous allocation, or live trading is authorized.

Portfolio Replay Role Contract Notice (2026-05-15)

- `context_role` is the machine-checkable replay row semantics field: `current_holding`, `historical_context`, `flat_in_replay`, `cash`, or `unavailable`.
- `row_role` is the artifact/table row-shape field: `daily_portfolio`, `event_annotation`, or `buy_sell_decision`.
- `strategies.strategy_replay.normalize_context_frame_for_replay(...)` is the shared context-normalization owner; dashboard adapters must call it instead of duplicating replay-window/ticker/method joins.
- Selected-method replay artifacts hydrate missing role columns for older saved artifacts while unrelated schema drift still fails closed.
- Diagnostics must be post-processing over `DashboardReplayContext` and must not rebuild replay.
- No broker/live trading, provider ingestion, ranking, recommendation, scoring, or promotion claim is authorized.

Dashboard Replay Aux Weight Semantics + Stacked Timeline Notice (2026-05-15)

- `strategies.strategy_replay.REPLAY_CONTEXT_COLUMNS` includes `target_weight` so event/decision context rows can carry replay-derived target-weight semantics.
- `strategies.strategy_replay._normalize_context_frame(...)` preserves original auxiliary `weight` but derives visible `target_weight` from matching replay rows.
- `dashboard.py::_align_context_weights_to_replay(...)` stores original aux weight as `audit_weight` and sets visible `weight` to replay `target_weight` for display compatibility.
- `dashboard.py::_render_replay_timeline_chart(...)` uses stacked step-area traces from replay `target_weight`, not independent line traces.
- `dashboard.py::_render_strategy_replay_section(...)` guards partial latest-snapshot and event schemas before table/chart render.
- No broker/live trading, provider ingestion, ranking, recommendation, scoring, or promotion claim is authorized.

Replay Selected Price Loading + MU/SNDK Eligibility Trace Notice (2026-05-15)

- `core.data_orchestrator.load_batched_pit_replay_data(..., selected_permnos=...)` builds the full replay-window `r3000_pit` membership index, then loads price/return columns only for selected permnos that are members in that PIT window.
- `dashboard.py::_build_dashboard_strategy_replay_context(...)` passes `_numeric_replay_permnos(request.replay_assets)` to the batched loader; `_filter_dashboard_replay_inputs_to_assets(...)` remains the final signed-asset filter.
- `scripts.pit_lifecycle_replay.trace_thesis_ticker_eligibility(...)` reports pinned universe, ticker-map, PIT membership, local price/return, Rule100 history, current-hold/sizing, and final gate for MU/SNDK without changing replay selection.
- No watchlist-only replay, broker/live trading, provider ingestion, ranking, recommendation, scoring, or promotion claim is authorized.

Max Replay Timeline Sampling Fix Notice (2026-05-15)

- `dashboard.py::_sample_replay_timeline_from_daily(...)` normalizes weekly grouped dates with `pd.to_datetime(...).dropna().dt.normalize()`.
- The sampled timeline keeps the last daily replay date per ISO year/week plus the final daily replay date.
- Sampling remains a visualization transform over daily replay rows; Portfolio Performance still requires daily replay output.
- No broker/live trading, provider ingestion, ranking, recommendation, or promotion claim is authorized.

Portfolio Single-Source Replay Page Notice (2026-05-14)

- `/portfolio-and-allocation` now builds one daily `DashboardReplayContext` before rendering replay-facing surfaces.
- Portfolio Performance consumes only daily replay `portfolio_return`; optimizer weights/local weighted prices/live weighted prices/equal-weight local are not fallback evidence for this replay-facing curve.
- The page allocation display is the latest daily replay snapshot, not a separate optimizer allocation panel.
- Strategy Replay Timeline sampling is display-only and derived from daily replay rows.
- ENTER/EXIT Events, Latest Buys/Sells, and Buy/Sell Decision Log share the same replay bundle identity as Portfolio Performance and latest snapshot.
- Latest Buys/Sells is a filtered view of `bundle.decision_rows`, not a separate loader/cache.
- The duplicate Trade Event Log table is removed; ENTER/EXIT hover context carries date, ticker, action, weight, and reason.
- No broker/live trading, provider ingestion, ranking, recommendation, or promotion claim is authorized.

Backend Replay Reader Identity Hardening Notice (2026-05-14)

- `strategies.strategy_replay._validate_manifest_bundle_fields(...)` rejects blank or non-string top-level manifest `run_id`, `source_id`, and `method_id`.
- Manifest identity validation runs before optional `run_id` / `source_id` request matching, parquet reads, parquet/manifest equality checks, and bundle reconstruction.
- The regression blanks both manifest and parquet identity while omitting expected IDs, and expects `manifest_identity_blank:<field>`.
- No broker/live trading, provider ingestion, ranking, recommendation, or promotion claim is authorized.

Saved Artifact Single-Source Aux Surface Fix Notice (2026-05-14)

- `dashboard.py::_dashboard_context_from_artifact_read(...)` preserves saved artifact event and decision rows exactly, including empty DataFrames.
- Saved artifacts with daily portfolio rows but empty event/decision rows keep those aux surfaces empty even when fallback dashboard frames have rows.
- `DashboardReplayContext.source_mode="saved_artifact"` is artifact-owned for replay rows, latest snapshot, event annotations, and Buy/Sell decisions.
- No broker/live trading, provider ingestion, ranking, recommendation, or promotion claim is authorized.

Portfolio Market-Data Freshness Fail-Closed Notice (2026-05-14)

- `PriceEndpointFreshness` is the cached endpoint snapshot for a loaded price matrix; render paths should prefer passing it downstream over rescanning `prices_wide`.
- `build_price_endpoint_freshness(...)` records each asset column's own final valid positive price date and the matrix required endpoint in one chunked pass.
- `price_latest_dates_by_column(...)` records each asset column's own final valid positive price date.
- `price_column_latest_date(...)` and `price_endpoint_is_fresh(..., max_staleness_days=0)` are the shared endpoint/tolerance predicates; strict freshness is the default.
- `price_frame_latest_date(...)` is the matrix endpoint helper; consumers must not use a shared max date as proof that every selected column is fresh.
- `filter_price_frame_to_fresh_columns(...)` keeps only columns whose endpoint reaches the required date.
- Benchmark YTD drops stale benchmark columns that fail live overlay and returns the common endpoint for remaining curves.
- Portfolio YTD fallback returns unavailable when any nonzero weighted local leg is stale at the required endpoint.
- Optimizer selected-price preparation passes the global price endpoint into the live-overlay stitcher; stale selected assets are dropped before optimization.
- Optimizer selected-price overlay must pass the shared endpoint freshness filter after stitching; unresolved stale selected assets cannot be used as allocation evidence.
- Optimizer default ordering demotes stale endpoint assets before ranking trailing 1Y returns.
- Optimizer universe eligibility imports the shared core endpoint helpers and passes `OptimizerUniversePolicy.max_endpoint_staleness_days` explicitly in addition to history observation count.

Dashboard Backend Bundle Integration Verification Notice (2026-05-14)

- Dashboard selected-method replay consumes `strategies.strategy_replay.build_selected_method_replay(...)` through `_build_dashboard_strategy_replay_context(...)`.
- The dashboard backend-bundle call uses a per-date `input_loader`; PIT replay inputs still require `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- `DashboardReplayContext` remains the dashboard handoff object for replay rows, latest snapshot, event annotations, Buy/Sell decisions, and latest replay weights for YTD.
- The verified path is still `source_mode="transitional_build"`; saved artifact-reader consumption and explicit performance-budget enforcement remain future work.
- Full pytest and runtime smoke passed for this verification, but no broker/live trading, provider ingestion, ranking, recommendation, or promotion claim is authorized.

Replay Coverage Contract Audit Fix Notice (2026-05-14)

- Selected-method replay metadata includes `date_window["coverage_segments"]` derived from the replay coverage plan.
- Unavailable replay rows preserve concrete reasons as `input_unavailable:<coverage_reason>`.
- Uncovered replay dates are batched before performance attachment so daily all-uncovered replay windows do not scale by per-date DataFrame concatenation, including row-heavy explicit-member unavailable windows.
- Replay performance uses next-tradable-return alignment: weights generated from date `t` data do not earn the return ending at `t`.
- Tiny PIT replay frames may use a direct return lookup path; larger replay frames keep the vectorized long-form join path.
- Inverse-volatility optimization may skip SLSQP only when the closed-form inverse-vol target already satisfies long-only full-investment max-weight constraints.
- `scripts/build_context_packet.py` selects complete New Context Packets from current truth surfaces before older same-phase handovers.

Data/PIT Strategy Replay Hardening Notice (2026-05-13)

- `build_strategy_replay_cache_signature(...)` and `load_strategy_replay_inputs(...)` require `universe_mode="r3000_pit"`.
- Repo-local strategy replay artifact writes are valid only under `data/runtime_cache/strategy_replay`.
- Dashboard Strategy Replay builds one `StrategyReplayInputs` object per replay date and passes it to `build_strategy_replay(...)`.
- Input artifacts are price/return matrix slices; replay target weights are display-only output.

Backend Shared Selected-Method Replay Notice (2026-05-13)

- `strategies.strategy_replay.build_selected_method_replay(...)` is the public backend bundle API for one selected method.
- The bundle uses `build_strategy_replay(...)` as the single replay frame source for Rule of 100 and optimizer methods.
- Replay rows include target weights, `CASH`, cap metadata, source/status/reason, and performance fields (`asset_return`, `return_contribution`, `portfolio_return`, `portfolio_equity`).
- Event annotations and buy/sell decision context must enter through typed optional context frames and are filtered to the replay method/window/tickers; absent context returns explicit empty status/reason.
- No dashboard-only ad hoc read is accepted as the backend replay contract, and no replay output authorizes broker/live trading, provider ingestion, rankings, or recommendations.

Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay Notice (2026-05-13)

- Frozen Rule100 audit defaults remain `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- `rule100_config_from_max_weight(max_weight)` is the only approved dynamic UI/replay sizing helper; it sets both per-name budget and single-name cap from `controls.max_weight`.
- Direct Rule of 100 UI allocation and Strategy Replay must agree for the same PIT candidate frame and max-weight control.
- `rule100_softmax_v1_history.csv` remains a frozen audit/history artifact unless a separately versioned and labeled UI-policy artifact is explicitly approved.
- Benchmark YTD uses local TRI first, then live-overlays only stale/missing benchmark tickers; stale columns must not forward-fill past their own local cutoff without an overlay attempt.
- AppTest route coverage may cap Strategy Replay dates for determinism; production dashboard replay horizon is unchanged.

This historical technical specification remains for continuity, but G7.1A supersedes the old product framing:

- Product: Unified Opportunity Engine.
- Architecture: Supercycle Gem Discovery + GodView Market Behavior Intelligence + Decision Augmentation.
- Future state engine target: `thesis_state + market_behavior_state + entry_discipline_state + hold_discipline_state + source_quality_state -> dashboard_state`.
- GodView families: IV, options whales, gamma, short squeeze, CTA/systematic pressure, sector rotation, ETF/passive flows, dark-pool/block activity, ownership whales, microstructure, catalysts/news/narrative, and regime.
- Required future signal metadata: `source_quality`, `provider`, `provider_feed`, `freshness`, `latency`, `confidence`, `observed_vs_estimated`, `allowed_use`, `forbidden_use`, `manifest_uri`.
- Boundary: G7.1A is docs/architecture only and adds no search, candidate generation, backtest, replay, proxy run, provider ingestion, ranking, alerts, broker calls, or new runtime dashboard behavior.
- Immediate next action: `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`.

G8 Candidate-Card Notice (2026-05-10)

- G8 creates exactly one human-nominated Supercycle Gem Candidate Card for `MU`.
- The card is a structured research object, not an investment recommendation.
- Initial state is limited to `THESIS_CANDIDATE` or `EVIDENCE_BUILDING`.
- `BUYING_RANGE`, `ADD_ON_SETUP`, `LET_WINNER_RUN`, and `TRIM_OPTIONAL` remain forbidden for G8.
- The validator rejects score, rank, buy/sell signal, alert, broker action, yfinance canonical evidence, estimated-as-observed signals, and missing options/IV/gamma provider-gap labels.
- Immediate next action: `approve_g9_one_market_behavior_signal_card_or_hold`.

G8.1 Discovery-Intake Notice (2026-05-10)

- G8.1 creates the first Supercycle Discovery Intake layer.
- The seed taxonomy is `AI_COMPUTE_INFRA`, `AI_SERVER_SUPPLY_CHAIN`, `MEMORY_STORAGE_SUPERCYCLE`, `SEMICAP_EQUIPMENT`, `POWER_COOLING_GRID`, `CRITICAL_MINERALS_LITHIUM`, `RESHORING_FOUNDRY`, `DEFENSE_INDUSTRIAL`, and `BIOTECH_PLATFORM`.
- The seed queue is exactly `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`.
- `MU` is the only `candidate_card_exists` item; all other names are `intake_only`.
- The validator requires `ticker`, `theme_candidates`, `evidence_needed`, `thesis_breakers_to_check`, `provider_gaps`, and the negated output flags.
- The validator rejects score/rank fields, buy/sell/hold calls, validated-thesis status, action-state promotion, yfinance canonical evidence, and missing manifests.
- Immediate next action: `approve_g8_2_one_additional_candidate_card_or_g9_one_market_behavior_signal_card_or_hold`.

G8.1A Discovery-Drift Correction Notice (2026-05-10)

- G8.1A adds discovery-origin schema discipline to the G8.1 queue.
- Allowed origin values are `USER_SEEDED`, `THEME_ADJACENT`, `SUPPLY_CHAIN_ADJACENT`, `PEER_CLUSTER`, `CUSTOMER_SUPPLIER_LINK`, `ETF_HOLDING_LINK`, `SEC_INDUSTRY_LINK`, `NEWS_RESEARCH_CAPTURE`, `LOCAL_FACTOR_SCOUT`, and `SYSTEM_SCOUTED`.
- Current seed labels are: `MU = USER_SEEDED`; `DELL/INTC/AMD/ALB = USER_SEEDED + THEME_ADJACENT`; `LRCX = USER_SEEDED + SUPPLY_CHAIN_ADJACENT`.
- All six current names must keep `is_system_scouted = false`, `is_validated = false`, and `is_actionable = false`.
- `LOCAL_FACTOR_SCOUT` is reserved for G8.1B and cannot appear in G8.1A intake output.
- Immediate next action: `approve_g8_1b_pipeline_first_discovery_scout_or_hold`.

DASH-0 Dashboard IA Notice (2026-05-10)

- DASH-0 approves the dashboard IA only.
- Target page order: Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, Settings & Ops.
- Future navigation should use an explicit page registry/sidebar shell, likely via Streamlit `st.Page` and `st.navigation`, after DASH-1 approval.
- Data Health and Drift Monitor move to future Settings & Ops; Backtests, Modular Strategies, and Daily Scan move to future Research Lab.
- The optimizer risk-limit alignment is recorded as a future runtime task, not implemented in DASH-0.
- Immediate next action: `approve_dash_1_page_registry_shell_or_hold`.

DASH-1 Page Registry Shell Notice (2026-05-10)

- DASH-1 uses Streamlit `st.Page` and `st.navigation` for the runtime page registry/sidebar shell.
- The entrypoint remains the shared frame/router and executes the selected page with `page.run()`.
- The implementation preserves legacy page internals while relocating them behind the approved IA buckets.
- `views/page_registry.py` owns the approved page order, page groups, and legacy movement map.
- Command Center, Thesis Card, Market Behavior, and Entry & Hold Discipline are shell placeholders only; Command Center status badges are deferred to DASH-2.
- No optimizer risk-limit control redesign, new metric, score, rank, signal, alert, broker, provider, ingestion, candidate generation, factor-scout integration, or buy/sell/hold output is authorized.
- Immediate next action: `approve_dash_2_command_center_placeholder_or_hold`.

G8.2 System-Scouted Candidate-Card Notice (2026-05-10)

- G8.2 converts the sole G8.1B `LOCAL_FACTOR_SCOUT` output, `MSFT`, into one candidate-card-only research object.
- Required provenance fields include `discovery_origin = LOCAL_FACTOR_SCOUT`, `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`, `source_intake_item_id`, `source_intake_manifest_uri`, and `candidate_card_manifest_uri`.
- The optional `governance` block must preserve `not_validated`, `not_actionable`, `no_score`, `no_rank`, `no_buy_sell_signal`, `no_alert`, and `no_broker_action` as true.
- Candidate-card validation rejects factor-score leakage and all direct score, rank, buy/sell, buying-range, alert, broker, order, target-price, or action fields.
- The MSFT card is not merged into dashboard runtime. Existing dashboard MSFT ticker-list rows remain legacy runtime output and are not candidate-card status.
- Immediate next action: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.

Portfolio Lifecycle Replay Churn + Weight Notice (2026-05-12)

- Position Lifecycle Replay ENTER weights now use a max-10 position budget: `round(1 / 10, 4) = 0.10`.
- Replay entries require the raw PIT gate plus 3 consecutive confirmed days and at least 3 positive present vectors among `z_demand`, `z_moat`, `z_inventory_quality_proxy`, and `z_discipline_cond`.
- Replay exits require either a hard 20% SMA20 stretch or a raw exit after 20 holding days with 2 consecutive exit confirmations.
- A ticker cannot re-enter until 10 calendar days after its last EXIT.
- This is lifecycle-state discipline only; it does not reopen the rejected Phase 54 Rule-of-100 sleeve or authorize ranking, scoring, optimizer objective changes, alerts, broker behavior, or provider ingestion.

Portfolio Universe Construction Notice (2026-05-10)

- `strategies/portfolio_universe.py` owns optimizer-universe eligibility, ticker-map readiness, local price-history readiness, and max-weight feasibility diagnostics.
- `dashboard.py` must pass `universe.included_permnos` from `build_optimizer_universe(...)`; it must not pass display-sorted `df_scan["Ticker"][:20]`.
- Default optimizer eligibility is limited to `ENTER STRONG BUY` and `ENTER BUY`; generic `WATCH` remains research-only and `EXIT`/`KILL`/`AVOID`/`IGNORE` remain excluded.
- Runtime conviction modes, Black-Litterman, MU floors, thesis anchors, manual overrides, scanner rewrites, and new objectives remain blocked until separately approved.
- Immediate next action: `approve_thesis_anchor_policy_or_hold`.

Optimizer Core Structured Diagnostics Notice (2026-05-11)

Dashboard Architecture Safety Notice (2026-05-11)

- Runtime PID liveness checks now use `utils.process.pid_is_running`.
- Direct `os.kill(pid, 0)` style liveness probing is prohibited in runtime callers because Windows can treat it as a real signal.
- Existing local wrapper names remain as compatibility seams for tests and lock-owner recovery code.
- `dashboard.py` strategy-matrix initialization now uses one helper path.
- Dashboard portfolio price cleanup delegates to `core.data_orchestrator.clean_price_frame`.
- This is architecture safety/hygiene only: no provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker, or dashboard content redesign is authorized.
- Immediate next action: `hold_or_continue_code_quality_review_section`.

- `strategies/optimizer_diagnostics.py` owns structured optimizer diagnostic objects and formulas.
- `strategies/optimizer.py` exposes diagnostic-returning optimizer methods while preserving existing weight-returning methods.
- `views/optimizer_view.py` renders optimization status, feasibility status, active constraints, assets at max cap, assets at lower bound, equal-weight-forced status, solver status, residuals, and fallback labels.
- The approved formulas are `upper_bound_feasible = n_assets > 0 and max_weight * n_assets >= 1`, `equal_weight_forced = max_weight <= (1 / n_assets) + tolerance`, `active_upper_i = weight_i >= max_weight - tolerance`, and `full_investment_constraint_residual = sum(weights) - 1`.
- This is diagnostics-only; no lower-bound allocation policy, MU conviction, WATCH investability expansion, Black-Litterman, new objective, scanner rule, manual override, provider ingestion, alert, broker, or replay behavior is approved.

Portfolio Optimizer View Test and Performance Notice (2026-05-11)

- `tests/test_optimizer_view.py` uses Streamlit `AppTest` for optimizer view rendering, mean-variance control selection, and sector-cap UI coverage.
- `core/data_orchestrator.py` owns a display-only Parquet cache for recent close-price overlays; cache misses schedule background refresh and return local TRI data immediately when no cached overlay exists.
- `views/optimizer_view.py` caches optimizer runs by `method`, selected price frame, `max_weight`, and `risk_free_rate`.
- Sector caps remain post-solver soft constraints; they are not SLSQP constraints and do not approve new optimizer policy.
- No canonical provider ingestion, lower-bound allocation policy, MU conviction, WATCH investability expansion, Black-Litterman, new objective, alert, broker, score, rank, or card-reader integration is approved.

Technical Specification: Terminal Zero (Ironclad Architecture)
Author: Atomic Mesh | Date: 2026-02-19 | Status: Active Blueprint | Version: 14.1 (PM Hierarchy + Stage Loop Governance Sync)
Guiding Principle: "Signals from Price, PnL from Returns."

0. Project Hierarchy and Stage Loop (PM Governance)
  Purpose:
    Keep planning MECE and execution-focused by using a project-based hierarchy, not a technical-layer checklist.

  Canonical hierarchy (initialize at project start):
    - L1 (Project Pillar): e.g., "Backtest Engine (Signal System)"
    - L2 (Streams): Backend | Frontend/UI | Data | Ops
    - L3 (Stage Flow): Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD

  Snapshot reporting contract:
    - Header must include:
      - L1
      - L2 Active Streams
      - L2 Deferred Streams
      - L3 Stage Flow
      - Active Stream
      - Active Stage Level (L2/L3/L4)
    - Main table shows only stage rows under the active level for the selected active stream.
    - Stage set must be MECE under the same parent scope.
    - Stage rows are stream-specific and include current scope, rating, and next scope.
    - Planning stage is a confirmation gate: scope boundary, ownership/handoff, and acceptance checks.
    - Planning row must explicitly carry `Boundary`, `Owner/Handoff`, and `Acceptance Checks`.
    - ASCII table schema is fixed: `Stage | Current Scope | Rating | Next Scope`.
    - Rows must be single-line; truncate text to avoid wrapped-cell leakage.
    - Secondary next suggestion is outside table as `Remark:` and appears only when:
      - `next_step_certainty < 75`
      - `rating_diff_between_top_next_steps < 20`
    - If all rows share the same scope, keep `L1` as header only and do not repeat `L1` in table rows/columns.

  Scoring rubric:
    - `Rating`: `0-100` progress/readiness for the current stage row.
    - `next_step_certainty`: `0-100` confidence for the next-step recommendation.
    - `rating_diff_between_top_next_steps`: absolute delta between primary and secondary next-step ratings.

  Minimal iteration loop (anti-sprawl):
    - Keep main table at active level.
    - Expand only one stage into next depth (L4) when required.
    - Expand only if:
      - two or more plausible sub-steps block start, or
      - next-step certainty < 75, or
      - high-payoff ambiguity exists, or
      - handoff risk exists.
    - Expanded stage contains 3-5 MECE children, each tied to an artifact and "done when" stop condition.
    - Collapse back after action when certainty >= 75.

  Document placement:
    - Canonical policy: `docs/spec.md` (this section).
    - Reusable rendering snippet: `docs/templates/plan_snapshot.txt`.
    - Live loop status: active `docs/phase*-brief.md`.

  Regime contract precedence note (cross-phase consistency):
    - FR-041 matrix entries are historical freeze documentation.
    - Current runtime budget contract is FR-050/FR-070 (`GREEN=1.0`, `AMBER=0.5`, `RED=0.0`).

  R64.1 dependency hygiene note:
    - Alpaca operational/paper quote infrastructure uses `alpaca-py==0.43.4` as the main SDK boundary.
    - The legacy `alpaca-trade-api` package is excluded from the main research environment.
    - This SDK migration does not authorize live orders, broker automation, or any scope beyond paper operational quote metadata.

  Phase 65 Candidate Registry note:
    - Phase F Candidate Registry is complete as registry-only work.
    - Candidate intent must be registered before results with `candidate_id`, `family_id`, `hypothesis`, `universe`, `features`, `parameters_searched`, `trial_count`, `train_window`, `test_window`, `cost_model`, `data_snapshot`, `manifest_uri`, `source_quality`, `created_at`, `created_by`, `code_ref`, and `status`.
    - Registry events are append-only JSONL records chained by `previous_event_hash` and `event_hash`.
    - Snapshot files are disposable projections from the event log, not source of truth.
    - This registry does not authorize strategy generation, simulation, alerts, promotion packets, broker calls, or live execution.

  Phase G0 V2 Proxy Boundary note:
    - V2 proxy boundary harness is complete as boundary-only work under `v2_discovery/fast_sim/`.
    - Proxy outputs must carry `promotion_ready = false`, `canonical_engine_required = true`, `source_quality`, `manifest_uri`, `registry_event_id`, `registry_note_event_id`, `code_ref`, and `data_snapshot`.
    - `core.engine.run_simulation` remains the only official truth path.
    - The no-op proxy computes no alpha, Sharpe, return curve, ranking, or best candidate; it may append only a registry note, and result validation must resolve that note back to the same candidate, proxy run, and boundary verdict.
    - This boundary does not authorize a real fast simulator, strategy search, parameter sweeps, alerts, promotion packets, broker calls, or external engine adapters.

  Phase G1 Deterministic Synthetic Fast-Proxy note:
    - Phase G1 is complete as synthetic mechanics only under `v2_discovery/fast_sim/`.
    - The simulator accepts only manifest-backed fixture files under `data/fixtures/v2_proxy/`.
    - Fixture/golden artifacts must reconcile row count, date range, schema columns, and SHA-256 hash metadata before accepted output.
    - `nan`, `+inf`, `-inf`, missing symbols, sparse target weights, and non-finite proxy metadata fail closed.
    - Invalid fixture evidence must not be repaired with `nan_to_num`, sparse-weight `fillna(0)`, interpolation, or stringified nulls.
    - The only simulator weight input is prebaked `date,symbol,target_weight`; no signal function, strategy factory, PEAD variant, parameter search, or ranking surface is authorized.
    - Allowed outputs are positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, boundary verdict, `promotion_ready = false`, and `canonical_engine_required = true`.
    - Real market data paths, alerts, broker calls, promotion packets, and performance metrics such as alpha, Sharpe, CAGR, and max drawdown remain blocked.
    - V2 proxy output remains separate from official truth; future promotion still requires V1 `core.engine.run_simulation`.

  Phase G2 Single Registered Fixture Candidate note:
    - Phase G2 is complete as lineage-only work under `v2_discovery/fast_sim/run_candidate_proxy.py` and `lineage.py`.
    - Exactly one synthetic fixture candidate is registered or loaded from the Candidate Registry before proxy output exists.
    - The proxy run appends or reuses one hash-linked `candidate.note_added` registry event and emits `data/registry/g2_single_fixture_candidate_report.json`.
    - G2 remains blocked from strategy search, ranking, alerts, broker calls, promotion packets, real market data, and external engines.

  Phase G3 First Canonical Replay Fixture note:
    - Phase G3 is complete as truth-alignment work under `v2_discovery/replay/`.
    - G3 requires exactly one registered G2 fixture candidate, its manifest, source quality, data snapshot, and manifest hash.
    - G3 calls the official V1 path, `core.engine.run_simulation`, and compares V1/V2 only on positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, manifest URI, source quality, and candidate ID.
    - `data/registry/g3_canonical_replay_report.json` records `comparison_result = "match"`, `mismatch_count = 0`, `promotion_ready = false`, `canonical_engine_required = true`, and `boundary_verdict = "v2_blocked_from_promotion"`.
    - A V1/V2 match is accounting evidence only; it does not create a promotion packet or trading permission.

  Phase G4 Real Canonical Dataset Readiness note:
    - Phase G4 is complete as readiness-only work under `v2_discovery/readiness/`.
    - The first real canonical contact is a tiny `prices_tri` slice with 123 rows, 3 symbols, daily bars, and its own Tier 0 manifest.
    - G4 reconciles manifest hash, row count, schema, date range, finite numeric values, duplicate keys, monotonic dates, price domain, return domain, freshness, and no-sidecar-required status.
    - `ready_for_g5 = true` is dataset readiness only, not alpha evidence, ranking evidence, alert evidence, or promotion authority.

  Phase G5 Single Canonical Replay No Alpha note:
    - Phase G5 is complete as V1-only mechanical replay work under `v2_discovery/replay/canonical_real_replay.py`.
    - G5 uses the G4 tiny real canonical slice, predeclared neutral equal weights only, and the official V1 path `core.engine.run_simulation`.
    - G5 does not call V2 proxy on real data.
    - Allowed outputs are positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, source quality, manifest identity, `promotion_ready = false`, `alerts_emitted = false`, and `broker_calls = false`.
    - No alpha, Sharpe, CAGR, drawdown, score, rank, buy/sell decision, alert, broker call, promotion packet, or trading permission is authorized.

  Phase G7.1 Roadmap Realignment note:
    - Phase G7.1 is complete as product-charter and docs/context work only.
    - Terminal Zero is framed as discretionary augmentation for de-risked asymmetric upside, not generic alpha search and not a trading bot.
    - The planning allocation model is 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting.
    - `PEAD_DAILY_V0` remains valid as a tactical signal family only.
    - `SUPERCYCLE_GEM_DAILY_V0` is the primary product family target for a later definition-only phase.
    - The dashboard taxonomy has five panels: thesis health, entry discipline, hold discipline, flow/positioning, and regime.
    - Short-squeeze and CTA-type inputs are future dashboard context only, not automatic triggers.
    - G7.1 authorizes no candidate generation, backtest, replay, proxy run, search, ranking, alert emission, broker call, live order, or promotion packet.

1. System Architecture Diagram
The system is composed of six strictly isolated layers:
  Data Layer (The Lake): Hybrid Parquet lake (WRDS base + Yahoo patch).
  Compute Layer (The Console): A stateless, vectorized simulation kernel.
  Strategy Layer (The Cartridge): Pluggable signal generators.
  Optimizer Layer (The Grid): Automated parameter sweep engine.
  Updater Layer (The Bridge): Yahoo Finance live data feed. ← NEW
  Application Layer (The Cockpit): A Streamlit dashboard for interaction.

2. Data Layer Specification

2.1 Storage Format
  Format: Apache Parquet (Snappy Compression).
  Location: ./data/processed/
  Partitioning: None (Single file for MVP efficiency).

2.2 Schema Definitions

A. prices.parquet (The Asset Universe)
  Sort Order: permno, date
  Fill Policy: ffill() on price columns (handling holidays/suspensions).
  | Column    | Type          | Origin / Formula                        | Critical Usage           |
  |-----------|---------------|-----------------------------------------|--------------------------|
  | date      | datetime64[ns]| CRSP date                               | Index Alignment          |
  | permno    | int64         | CRSP permno                             | Unique Asset ID          |
  | raw_close | float32       | abs(prc)                                | Liquidity Filters        |
  | adj_close | float32       | abs(prc) [no cfacpr available]           | Signals ONLY (RSI, MA)   |
  | total_ret | float32       | ret (filled with dlret on death)         | Execution / PnL          |
  | volume    | float32       | vol                                     | Liquidity Filters        |

  DATA CONSTRAINT: No ASKHI/BIDLO columns available.
  All High/Low logic uses Adj Close approximations.
  ATR = abs(Close_t - Close_{t-1}). k raised to 3.5 to compensate.

D. yahoo_patch.parquet (The Yahoo Bridge) ← NEW
  Same schema as prices.parquet.
  Contains Yahoo Finance data from 2025-01-01 onwards.
  Generated by data/updater.py via batch yf.download().
  app.py reads prices.parquet UNION ALL yahoo_patch.parquet via DuckDB.
  The base prices.parquet is NEVER modified (append-only architecture, D-21).

E. tickers.parquet (The Ticker Map)
  | Column | Type     | Description |
  |--------|----------|-------------|
  | permno | uint32   | CRSP asset ID |
  | ticker | varchar  | Human-readable symbol (AAPL, NVDA, ...) |
  Source: Latest ticker per permno from raw CRSP CSV.
  Auto-expanded with synthetic permnos (900000+) for new Yahoo tickers.

B. fundamentals.parquet (The Quality Bedrock) [FR-027]
  Quarterly sparse fundamentals keyed by `release_date` for PIT safety.
  Core columns:
  | Column             | Type          | Description |
  |--------------------|---------------|-------------|
  | permno             | int64         | Asset ID |
  | ticker             | varchar       | Symbol alias |
  | release_date       | datetime64[ns]| First date fundamentals become tradable |
  | roic               | float32       | Return on invested capital proxy |
  | revenue_growth_yoy | float32       | YoY growth proxy |
  | quality_pass       | int8          | MVQ gate (1 pass, 0 fail) |

F. fundamentals_snapshot.parquet (Scanner-Ready Snapshot) [FR-027]
  Write-time compressed latest fundamentals state per symbol.
  Purpose: O(1)-style scanner quality lookup without loading full sparse history.
  Current observed size (2026-02-14): 1,680 symbols.

G. sector_map.parquet (Static Context Map) [FR-028]
  Location: `./data/static/sector_map.parquet`
  Columns: `ticker`, `permno` (optional), `sector`, `industry`, `updated_at`.
  Purpose: Attach contextual risk buckets to scanner and optimizer outputs.

H. Compustat Loader Artifacts [FR-031]
  Loader: `data/fundamentals_compustat_loader.py`
  Inputs:
    - Local quarterly CSV (`data/e1o8zgcrz4nwbyif.csv`)
    - `tickers.parquet` + Top3000 liquid ranking
  Outputs:
    - Canonical merge into `fundamentals.parquet` (source precedence applied)
    - Rebuilt `fundamentals_snapshot.parquet`
    - `compustat_ticker_match_top3000.parquet` (mapping audit)
    - `compustat_unmatched_top3000.csv` (coverage gap audit)
  Safety controls:
    - updater lock reuse (`.update.lock`)
    - Atomic writes (`os.replace`) through updater helper
    - Timestamped backups under `data/processed/backups/`

I. R3000 PIT Membership Artifacts [FR-032]
  Loader: `data/r3000_membership_loader.py`
  Input gate:
    - Required columns: `gvkey`, `from`, `thru`
    - Minimum usable rows: default `>= 1000`
    - Fails fast on metadata-only index-label exports
  Outputs:
    - `data/processed/r3000_membership.parquet`
    - `data/processed/universe_r3000_daily.parquet`
    - `data/processed/r3000_unmatched.csv`
  PIT membership expansion:
    - daily universe row exists only if `from_date <= date <= thru_date`

J. earnings_calendar.parquet (Catalyst Event Layer) [FR-034]
  Location: `./data/processed/earnings_calendar.parquet`
  Columns:
  | Column             | Type          | Description |
  |--------------------|---------------|-------------|
  | permno             | uint32        | Asset ID |
  | ticker             | varchar       | Symbol |
  | next_earnings_date | datetime64[ns]| Upcoming earnings date (if known) |
  | last_earnings_date | datetime64[ns]| Most recent earnings date (if known) |
  | fetched_at         | datetime64[ns]| Calendar ingestion timestamp |
  | source             | varchar       | Data source tag (`yfinance`) |
  Loader: `data/calendar_updater.py` (lock-safe + atomic write)

C. macro.parquet (The Regime)
  Sort Order: date
  | Column    | Type    | Origin                 | Critical Usage                    |
  |-----------|---------|------------------------|-----------------------------------|
  | spy_close | float32 | SPY (permno 84398)     | Market Trend Filter               |
  | vix_proxy | float32 | Rolling StdDev of SPY  | Adaptive Stops (k), Vol Sizing    |

K. macro_features.parquet (FR-035 Canonical Macro Layer)
  Location: `./data/processed/macro_features.parquet`
  PIT policy:
    - Fast market series: T+0.
    - Slow FRED series: shifted by +1 trading day.
  Core columns:
  | Column | Type | Rule |
  |---|---|---|
  | date | datetime64[ns] | trading calendar index |
  | spy_close | float32 | Yahoo SPY close (legacy-compatible) |
  | vix_proxy | float32 | 20d realized vol proxy from SPY returns |
  | qqq_close | float32 | Yahoo QQQ close |
  | vix_level / vix3m_level / vvix_level | float32 | Yahoo volatility surface |
  | vix_vix3m_spread | float32 | `vix_level - vix3m_level` |
  | vix_term_ratio | float32 | `vix_level / vix3m_level` |
  | vix_backwardation | bool | `vix_term_ratio > 1.0` |
  | liquidity_air_pocket | bool | `(spread > 0) & (vvix > 110)` |
  | qqq_peak_252d | float32 | rolling 252d max of QQQ close |
  | qqq_drawdown_252d | float32 | `qqq_close / qqq_peak_252d - 1` |
  | qqq_drawdown_252d_z_adapt | float32 | rolling z-score(252d) of `qqq_drawdown_252d` |
  | qqq_ma200 | float32 | rolling 200d average of QQQ close |
  | qqq_ma200_trend_gate | bool | `qqq_close >= qqq_ma200` |
  | qqq_ret_5d_z_adapt | float32 | adaptive z-score of 5d QQQ return |
  | qqq_ret_21d_z_adapt | float32 | rolling z-score(252d) of 21d QQQ return |
  | qqq_drawdown_5d_delta_z_adapt | float32 | adaptive z-score of 5d change in `qqq_drawdown_252d` |
  | slow_bleed_label | bool | `qqq_ret_21d_z_adapt <= -1.0` and `qqq_drawdown_252d_z_adapt <= -0.5` |
  | sharp_shock_label | bool | `qqq_ret_5d_z_adapt <= -2.5` or `qqq_drawdown_5d_delta_z_adapt <= -2.5` |
  | dxy_spx_corr_20d | float32 | rolling 20d corr of returns |
  | dollar_squeeze | bool | `corr > 0.50` |
  | sofr_effr_spread | float32 | `SOFR - DFF` (pre-2018 missing -> 0.0) |
  | collateral_crisis | bool | `sofr_effr_spread > 0.10` |
  | hyg_lqd_ratio | float32 | `HYG / LQD` |
  | hyg_lqd_ratio_z63 | float32 | rolling z-score(63d) |
  | credit_freeze | bool | `hyg_lqd_ratio_z63 < -2.0` |
  | mtum_spy_corr_60d | float32 | rolling 60d corr of returns |
  | momentum_crowding | bool | `mtum_spy_corr_60d > 0.85` |
  | month_end_rebalance_flag | bool | last 3 trading days of month |
  | month_end_rebalance_direction | float32 | sign(MTD SPY - MTD BND) |
  | stress_count | int8 | sum of boolean stress flags |
  | regime_scalar | float32 | stress map: 1.0 / 0.7 / 0.5 / 0.0 |
  Builder: `data/macro_loader.py`
  Validator: `scripts/validate_macro_layer.py`
  Performance notes (Phase 9.2):
    - Rolling percentile uses vectorized `rolling().rank(pct=True)` path (fallback retained).
    - FRED ingestion fetches series in parallel and bounds payload to requested date window (`cosd`, `coed`).

K.1 macro_gates.parquet (FR-035 Hard-Gate Daily Overlay)
  Location: `./data/processed/macro_gates.parquet`
  Build source: `data/macro_loader.py::build_macro_gates` (derived strictly from `macro_features.parquet` dates).
  Strategy consumption policy:
    - `state`, `scalar`, `cash_buffer`, `momentum_entry` are consumed with strict `t signal -> t+1 execution`.
    - Warmup defaults after shift: `state=AMBER`, `scalar=0.5`, `cash_buffer=0.25`, `momentum_entry=False`.
  Columns:
  | Column | Type | Rule |
  |---|---|---|
  | date | datetime64[ns] | trading calendar index |
  | state | string | `RED/AMBER/GREEN` hard-gate state |
  | scalar | float32 | exposure scalar map (`RED=0.0`, `AMBER=0.5`, `GREEN=1.0`) |
  | cash_buffer | float32 | cash reserve map (`RED=0.50`, `AMBER=0.25`, `GREEN=0.0`) |
  | momentum_entry | bool | only true in `GREEN` with trend support and no stress labels |
  | reasons | string | pipe-delimited gate reasons (`sharp_shock`, `vix_backwardation`, etc.) |
  | qqq_drawdown_252d | float32 | pass-through from macro features |
  | qqq_ma200_trend_gate | bool | pass-through from macro features |
  | slow_bleed / sharp_shock | bool | pass-through labels for strategy consumption |
  | qqq_ret_5d_z_adapt / qqq_ret_21d_z_adapt | float32 | adaptive return stress diagnostics |
  | qqq_drawdown_252d_z_adapt | float32 | adaptive drawdown stress diagnostic |
  | vix_term_ratio / vix_backwardation | float32/bool | term-structure stress diagnostics |

L. liquidity_features.parquet (FR-040 Canonical Liquidity Layer)
  Location: `./data/processed/liquidity_features.parquet`
  Columns:
  | Column | Type | Unit | Description |
  |---|---|---|---|
  | date | datetime64[ns] | date | Trading-day index |
  | us_net_liquidity_mm | float32 | USD millions | `WALCL - WDTGAL - (RRPONTSYD*1000)` |
  | liquidity_impulse | float32 | z-score | Normalized 20-day ROC of net liquidity |
  | repo_spread_bps | float32 | basis points | `(SOFR - DFF) * 100` |
  | repo_stress | bool | flag | `repo_spread_bps > 5` |
  | lrp_index | float32 | index | `Z(DTB3) - Z(VIX)` |
  | dollar_stress_corr | float32 | corr | rolling 20d corr(DXY, SPX returns) |
  | global_dollar_stress | bool | flag | `dollar_stress_corr > 0.5` |
  | smart_money_flow | float32 | index | cumulative `(SPY close - SPY open)` |
  | realized_vol_21d | float32 | pct annualized | 21d realized SPY volatility (`std(ret)*sqrt(252)*100`) |
  | vrp | float32 | pct points | volatility risk premium proxy: `vix_level - realized_vol_21d` |
  Engineering guardrails:
    - H.4.1 PIT lag rule: shift `WALCL/WDTGAL` by +2 calendar days.
    - Weekly series forward-fill capped at 14 days; daily series capped at 3 days.
    - Loader aborts if critical FRED series are unavailable.
  Builder: `data/liquidity_loader.py`
  Validator: `scripts/validate_liquidity_layer.py`


M. orbis_daily_aligned.parquet (L2 Macro Alternative Data Stream)
  Location: `./data/processed/orbis_daily_aligned.parquet`
  Source: Moody's Orbis Americas via WRDS Postgres Pipeline
  Note: Currently querying `bvd_orbis_trial` tables. Must update table queries to full volume schema (`bvd_orbis` and `orbis_qvards`) upon unlocking full tier.
  Columns:
  | Column | Type | Description |
  |---|---|---|
  | fiscal_date | datetime64[ns] | Daily interpolated business calendar |
  | median_inventory_turnover | float32 | Median `opre / stok` |
  | median_acquisition_yield | float32 | Median `ibaq / toas` |
  Pipeline (3-Script Flow):
    1. `data/orbis_loader.py` (SQL Extraction & Aggregation): Pulls `ibaq`, `toas`, `opre`, `stok` filtered by NAICS (`334%`) and private limit (`sd_ticker`).
    2. `scripts/align_orbis_macro.py` (Bitemporal Lag & Z-Score): Enforces a strict 90-day reporting delay via `merge_asof(backward)`.
    3. `scripts/orbis_signal_generator.py` (IC Validation): Calculates 252-day rolling z-scores against QQQ forward returns.

3. Compute Layer (The Engine)

3.1 The Vectorized Kernel (core/engine.py)
  Implements the Invisible Walls:
    D-04: shift(1) — no look-ahead bias.
    D-05: Turnover Tax — transaction cost deduction.
    D-08: Matrix Alignment — Engine accepts pre-pivoted Returns Matrix (T x N).

  ```python
  def run_simulation(target_weights, returns_df, cost_bps=0.0010):
      executed_weights = target_weights.shift(1).fillna(0.0)
      aligned_returns = returns_df.reindex(
          index=executed_weights.index,
          columns=executed_weights.columns
      ).fillna(0.0)
      gross_ret = (executed_weights * aligned_returns).sum(axis=1)
      turnover = executed_weights.diff().abs().sum(axis=1).fillna(0.0)
      costs = turnover * cost_bps
      net_ret = gross_ret - costs
      return pd.DataFrame({
          'gross_ret': gross_ret, 'net_ret': net_ret,
          'turnover': turnover, 'cost': costs
      })
  ```

4. Strategy Layer (The Cartridge API)

4.1 Base Class (strategies/base.py)
  All strategies return a triple: (weights, regime_signal, debug_details).

  ```python
  class BaseStrategy(ABC):
      @abstractmethod
      def generate_weights(self, prices, fundamentals, macro)
          -> tuple[pd.DataFrame, pd.DataFrame, dict]:
          pass
  ```

4.2 Adaptive Trend Strategy (strategies/adaptive_trend.py)
  3-Regime Logic:
    Attack (1.0): SPY > MA200 & VIX < 20.
    Caution (0.7): SPY > MA200 & VIX >= 20.
    Defense (0.5): SPY < MA200.

4.3 Investor Cockpit Strategy (strategies/investor_cockpit.py)
  Signal-Oriented logic for daily monitoring:
    Chandelier Stop: HighestClose(22d) - k * ATR(22d).
    Dip Hunter: Log-Price Z-Score < z_entry.
    Exposes `get_signals()` public API for Dashboard.

  4.3.1 Five-State Classifier [FR-023] ← NEW
    Hardcoded state machine computed per-stock:
    | State | Condition                                | Support Level      |
    |-------|------------------------------------------|--------------------|
    | HOLD  | Price > Stop, Price > Buy                | Stop (floor)       |
    | BUY   | Price > Stop, Price < Buy, GreenCandle   | Stop (floor)       |
    | WATCH | Price > Stop, Price < Buy, RedCandle     | Stop (floor)       |
    | AVOID | Price < Stop, Price > Buy                | Buy Zone           |
    | WAIT  | Price < Stop, Price < Buy                | z_deep = z - 1.5σ  |
    Design: Deterministic (no LLM). Microsecond-speed. Fully transparent.

  4.3.2 Conviction Scorecard [FR-024v2 — L5 Alpha] ← UPGRADED
    Vectorized per-stock scoring (0-10):
      A. Trend  (3pts): Price > MA200 (unchanged)
      B. Value  (3pts): Robust Z (MAD) < -3.0=3, < -2.0=1
      C. Macro  (2pts): VIX<20+falling=2, mixed=1, panic=0
      D. Momentum (2pts): Price>MA20 + ER>0.4=2, choppy=1
    New methods: _calculate_efficiency_ratio(), _calculate_robust_z()
    Output: conviction dict + metrics dict {rz_score, er_score} in details.

  4.3.3 Smart Watchlist + Auto-Update [FR-025] ← NEW
    Files:
      data/watchlist.json — {defaults: [...], user_added: [...]}
      data/auto_update.py — CLI: reads watchlist → updater.run_update()
    App Integration:
      - Signal Monitor saves user selections → watchlist.json
      - main() checks _is_data_stale() → auto-triggers update on startup
      - Business-day aware: skips weekends (Fri data valid on Mon)

  4.3.5 Catalyst Radar Overlays [FR-034] ← NEW
    `scan_universe()` accepts:
      - `mode`: `default` or `fresh_catalysts`
      - `earnings_blackout_days` (default 5)
      - `catalyst_lookback_days` (default 7)
    Additional outputs:
      - `days_to_earnings`
      - `days_since_earnings`
      - `earnings_risk` (bool, earnings inside blackout window)
    Behavior:
      - Default mode keeps ranking logic intact and annotates event risk.
      - Fresh catalysts mode filters to names with earnings in the last 7 days
        after trend+quality gates.

  4.3.6 Historical Baseline v1 (Frozen Pre FR-041)
    Historical reference only (not the active runtime budget contract).
    Weight pipeline (historical):
      - Dynamic params (if enabled): `k = 2.5 + 1.5*vol_rank`, `z = -3.0 + 2.0*vol_rank`.
      - Stop: `highest_close(22) - k*ATR(22)` where ATR is close-to-close absolute diff mean.
      - Dip signal: `price < buy_zone`, with optional green-candle confirmation.
      - Raw hold signal: `(price > stop) OR dip_signal`.
      - Equal-weight normalization across active signals, then macro scaling applied.
    Regime scaling (historical fallback):
      - Legacy VIX fallback scalar:
        - `1.0` when `vix_proxy < 20`
        - `0.7` when `20 <= vix_proxy <= 30`
        - `0.5` when `vix_proxy > 30`
      - If `regime_scalar` is present, strategy uses clipped scalar `[0.0, 1.0]` and falls back to VIX mapping only on NaNs.
    Macro conviction score (current `_macro_score`, 0..2):
      - Priority 1: `regime_scalar` mapping
        - `<= 0.5 -> 0`, `<= 0.7 -> 1`, `> 0.7 -> 2`.
      - Priority 2: liquidity fallback (`liquidity_impulse`, `repo_stress`, `global_dollar_stress`, `lrp_index`)
        - `stress_hits = repo_stress + global_dollar_stress + (liquidity_impulse < -1.0) + (lrp_index > 1.0)`
        - `stress_hits >= 2 -> 0`; `stress_hits == 1 or liquidity_impulse < 0 -> 1`; else `2`.
      - Priority 3: VIX heuristic fallback
        - If `vix_proxy < 20`: `2` when below its 20d MA, else `1`.
        - If `vix_proxy >= 20`: `1` when below its 20d MA, else `0`.
    Liquidity threshold note (current):
      - `repo_stress` flag currently comes from `repo_spread_bps > 5` bps in the liquidity layer config.

4.4 FR-041 Contract: Regime Governor + Throttle (Historical Freeze; runtime precedence is FR-050/FR-070)
  Purpose:
    Freeze v1 behavior above, then introduce a deterministic two-layer controller
    with explicit veto (Governor) and sizing context (Throttle).

  4.4.1 RegimeManager Interface (Contract)
  ```python
  class RegimeManager(Protocol):
      def bocpd_probability(self, net_liquidity: pd.Series) -> pd.Series: ...
      def matrix_exposure(self, governor_state: str, market_state: str) -> float: ...
      def evaluate(self, macro: pd.DataFrame, idx: pd.Index) -> RegimeManagerResult: ...
  ```
  Expected outputs (per date):
    - `governor_state`: `GREEN|AMBER|RED`
    - `market_state`: `NEG|NEUT|POS`
    - `throttle_score`: continuous score in `[-2, 2]`
    - `matrix_exposure`: matrix-selected exposure
    - `target_exposure`: final enforced exposure after long-only safety clamps
    - `reason`: explainability string

  4.4.2 Governor Rules (Explicit Thresholds)
    - RED if any:
      - `repo_spread_bps > 10.0` (basis points, explicit unit)
      - `credit_freeze == True` AND `vix_level > 15`
      - `liquidity_impulse < -1.90` AND `vix_level > 20`
      - `vix_level > 40`
    - AMBER if not RED and any:
      - `us_net_liquidity_mm < 0.997 * MA20(us_net_liquidity_mm)` AND `liquidity_impulse < 0`
      - `vix_level > 25`
      - `bocpd_prob > 0.80`
    - GREEN otherwise.

  4.4.3 BOCPD Field Contract
    - Field name: `bocpd_prob` (posterior changepoint probability, 0..1).
    - Usage in Governor:
      - `bocpd_prob > 0.80` contributes to AMBER (when not already RED).

  4.4.4 Throttle Score and Binning
    - Score definition:
      - `S = mean(Z(liquidity_impulse), Z(vrp), -Z(vix_level), Z(momentum_proxy))`
      - clip `S` to `[-2, 2]`
    - Bins:
      - POS: `S > 0.5`
      - NEUT: `-0.5 <= S <= 0.5`
      - NEG: `S < -0.5`

  4.4.5 3x3 Mapping Matrix (Governor x Throttle -> Exposure)
    | Governor \ Throttle | NEG | NEUT | POS |
    |---|---:|---:|---:|
    | GREEN | 0.70 | 1.00 | 1.30 |
    | AMBER | 0.25 | 0.50 | 0.75 |
    | RED | 0.00 | 0.00 | 0.20 |

  4.4.6 Long-Only Safety Rule (FR-041)
    - No shorting in V1.
    - Hard enforcement:
      - RED + NEG -> `0.00`
      - RED + NEUT -> `0.00`
      - RED + POS -> `<= 0.20`
    - `target_exposure` is the matrix output after these clamps.

5. Optimizer Layer (NEW)

5.1 The Grid Search Engine (core/optimizer.py)
  Purpose: Automate parameter tuning for the InvestorCockpit strategy.

  ```python
  def run_grid_search(
      prices: pd.DataFrame,
      returns: pd.DataFrame,
      macro: pd.DataFrame,
      k_range: tuple = (2.0, 4.5, 0.25),  # (start, stop, step)
      z_range: tuple = (-4.0, -1.5, 0.25), # (start, stop, step)
      cost_bps: float = 0.001,
      metric: str = "ulcer_sharpe"
  ) -> pd.DataFrame:
      """
      Returns a DataFrame with columns: k, z, cagr, max_dd, sharpe, ulcer_index, ulcer_sharpe.
      Each row is one (k, z) combination.
      """
  ```

  Optimization Metric: Ulcer-Adjusted Sharpe
    Ulcer Index = sqrt(mean(drawdown^2))  — measures BOTH depth AND duration of pain.
    Ulcer Sharpe = CAGR / Ulcer Index
    Higher is better.

5.2 Adaptive Regime Parameters (FR-016)
  Instead of fixed k/z values, parameters are functions of VIX:
    | VIX Level    | k (Stop) | z (Entry) | Behavior                         |
    |-------------|----------|-----------|----------------------------------|
    | < 15        | 2.5      | -1.5      | Tight stops, buy mild pullbacks  |
    | 15 – 25     | 3.5      | -2.5      | Standard                         |
    | > 25        | 4.5      | -3.5      | Wide stops, only buy deep crashes|

5.3 Wait-for-Confirmation (FR-017)
  Signal triggers when Z < z_entry.
  Confirmation: Entry only executes if Price(T) > Price(T-1) (Green Candle).

6. Application Layer (The Dashboard)

6.1 Console Modes
  Mode 1: "✈️ Investor Cockpit" — Daily Signal Monitor + Searchable Ticker Dropdown.
  Mode 2: "🔬 Lab / Backtest" — Full backtest with equity curve.
  Mode 3: "🎯 Optimizer" — 2D Heatmap parameter sweep.
  Mode 4: "🔄 Data Manager" — System status + Yahoo update trigger. ← NEW

6.2 Implementation Roadmap
  Phase 1: Data Plumbing (ETL) ✅
  Phase 2: Vectorized Engine ✅
  Phase 3: Investor Cockpit ✅
  Phase 4: Parameter Optimizer ✅
  Phase 4.1: Dynamic Volatility Mapping ✅
  Phase 4.2: Live Data + UX ✅
    - Searchable Ticker Dropdown (FR-020)
    - Yahoo Finance Bridge (FR-021, data/updater.py)
    - Data Manager Tab (FR-022)
    - Batch download: Top 50/100/200 scope
  Phase 5: Quantamental Integration ✅
    - PIT quality gate with `release_date` alignment (FR-027)
    - Hybrid behavior: scanner hard filter + watchlist penalty cap
  Phase 6: Portfolio Optimizer ✅
    - Inverse Volatility + Mean-Variance (SLSQP) + deterministic fallback
  Phase 7: Context-Aware Intelligence ✅
    - Sector/industry static map and runtime merge
  Phase 8: Catalyst Radar Foundation (Steps 1-6) ✅
    - Top 3000 scope added to updater, fundamentals updater, sector map builder, and Data Manager UI
    - Dynamic loading batch size (`200` if universe > 2500 else `250`)
    - Top 3000 hydration completed and validated
    - Compustat bedrock ingestion merged with precedence (`compustat_csv > yfinance`) for Top3000 scope
    - Institutional factor layer added (cashflow decumulation + EV/EBITDA matrix, FR-033)
  Phase 8: Catalyst Radar (Steps 7-11) ✅
    - Added earnings calendar updater and data contract (`earnings_calendar.parquet`).
    - Wired calendar context into `load_data()` and Data Manager refresh flow.
    - Scanner now renders earnings risk labels + catalyst mode/filter controls.
    - Added calendar integrity validator (`scripts/validate_calendar_layer.py`).
  Phase 9: Macro-Regime Awareness (FR-035) 🟡
    - Added `data/macro_loader.py` to build canonical `macro_features.parquet`.
    - Added daily hard-gate artifact `macro_gates.parquet` (QQQ drawdown/MA200 + VIX term structure).
    - Added `scripts/validate_macro_layer.py` with crisis-window sanity checks.
    - Strategy consumes `regime_scalar` when available; falls back to legacy VIX logic.
    - Data Manager includes macro rebuild control and live regime metrics.
  Phase 10: Global Liquidity & Flow Layer (FR-040) 🟡
    - Add `data/liquidity_loader.py` to build `liquidity_features.parquet`.
    - Add `scripts/validate_liquidity_layer.py` for schema/PIT/event checks.
    - Enforce H.4.1 release lag in liquidity construction.
  Current phase status is tracked in active `docs/phase*-brief.md` (not in this historical roadmap block).

  4.3.4 Scanner Cockpit Architecture [FR-026] ← NEW
    Session State: cockpit_view ("scanner"|"detail"), selected_ticker (permno|None)
    Scanner View (views/scanner_view.py):
      - Calls scan_universe() on full prices_wide (2-pass, memory-safe)
      - Calls generate_weights() on watchlist permnos only (5-15 tickers)
      - Renders two styled tables with drill-down buttons
    Detail View (views/detail_view.py):
      - Receives single permno from session state
      - Runs strategy on 1 ticker only (fast)
      - Renders chart (Price+Stop+BuyZone) + action report card
    Router in render_investor_cockpit(): dispatches to scanner or detail view

6.3 Phase 8 Step 1-6 Validation (2026-02-14)
  Data Hydration Outcomes:
    - `data/processed/fundamentals.parquet`: 10,219 rows
    - `data/processed/fundamentals_snapshot.parquet`: 1,680 rows
    - `data/static/sector_map.parquet`: 3,000 rows
    - Max `release_date`: 2026-03-17

  Runtime Metrics (local smoke checks):
    - Top 2000: `prices_shape=(6574, 2000)`, load=15.356s, scan=0.227s
    - Top 3000: `prices_shape=(6576, 3000)`, load=21.307s, scan=0.307s
    - Gate metrics at Top 3000: trend=6, quality=432, survivors=2, shown=2

  Rollout Decision:
    - Keep default app load at Top 2000 for responsiveness.
    - Provide Top 3000 as explicit operator-selected expansion mode.

6.4 FR-031 Execution Results (2026-02-14)
  Compustat Ingestion Outcomes:
    - Match coverage vs Top3000: `2781/3000` (`92.70%`)
    - `fundamentals.parquet`: `10,219 -> 225,640` rows (initial merge)
    - `fundamentals_snapshot.parquet`: `1,680 -> 2,819` rows (initial merge)
    - Latest release date retained: `2026-03-17`

  Post-merge Runtime Smoke:
    - Top 3000 load: 9.384s
    - Top 3000 scan: 0.078s
    - Gate metrics: trend=6, quality=428, survivors=2, shown=2

  Notes:
    - `revenue_growth_yoy` is computed with DuckDB window `LAG(revenue, 4)` per permno.
    - Missing lag4 or zero lag denominator is set to `NaN` (fail-safe quality behavior).

6.5 FR-032 Current Status (2026-02-15)
  Implemented:
    - PIT membership loader and daily-universe generator scaffold.
    - `app.load_data()` optional `universe_mode='r3000_pit'` with as-of date support.
  Blocker:
    - Input file `data/t1nd1jyzkjc3hsmq.csv` contains only index metadata (1 row).
    - Loader correctly fails input gate until a full WRDS constituent-history export is supplied.

6.6 FR-033 Institutional Factor Layer (2026-02-15)
  Implemented:
    - Expanded canonical fundamentals schema with institutional fields:
      - raw: `oibdpq`, `atq`, `ltq`, `xrdq`, `oancfy`, `dlttq`, `dlcq`, `cheq`, `cshoq`, `prcraq`, `fyearq`, `fqtr`
      - derived: `oancf_q`, `oancf_ttm`, `ebitda_ttm`, `revenue_ttm`, `xrd_ttm`, `mv_q`, `total_debt`, `net_debt`, `ev`, `ev_ebitda`, `leverage_ratio`, `rd_intensity`
    - Cashflow decumulation and valuation ratio matrix integrated in
      `data/fundamentals_compustat_loader.py::compute_institutional_factors()`.
    - Snapshot now carries factor subset:
      `ev_ebitda`, `leverage_ratio`, `rd_intensity`, `oancf_ttm`, `ebitda_ttm`.

  Validation (`scripts/validate_factor_layer.py`):
    - PIT violations: `0`
    - Decumulation mismatch: `0.0698%` (`126,066` comparable rows)
    - Q4 spike rate (>10x median Q1-Q3): `1.69%` (`n=41,065`, p95=`5.429`)
    - Debt fallback zero-rate (dlttq/dlcq missing): `99.1482%`
    - EV/EBITDA arithmetic bad-rate (>1% rel err): `0.00%` (`n=84,014`)
    - Snapshot non-null coverage:
      - `ev_ebitda`: `48.45%`
      - `leverage_ratio`: `73.94%`
      - `rd_intensity`: `47.87%`
      - `oancf_ttm`: `85.35%`
      - `ebitda_ttm`: `80.90%`

  Post-remediation runtime:
    - `fundamentals.parquet`: `215,876` rows
    - `fundamentals_snapshot.parquet`: `1,550` rows
    - Top 3000 load: `10.105s`
    - Top 3000 scan: `0.087s`

6.7 FR-042 Verification Artifacts (2026-02-15)
  Required outputs:
    - `data/processed/regime_history.csv`
    - `data/processed/regime_overlay.png`

  `regime_history.csv` key columns:
    - `date`: trading session date
    - `governor_state`: `GREEN|AMBER|RED`
    - `market_state`: `NEG|NEUT|POS`
    - `throttle_score`: continuous score in `[-2, 2]`
    - `matrix_exposure`: exposure selected from 3x3 matrix
    - `target_exposure`: final long-only clamped exposure
    - `reason`: explainability reason string
    - `truth_window`: FR-042 validation bucket label
    - `truth_expected`: allowed/expected state set for the bucket
    - `truth_pass`: window-rule compliance flag (`0|1`)

  `regime_overlay.png` requirements:
    - Plot market proxy (`SPY` close or equivalent) with date index.
    - Overlay Governor states with color bands:
      - GREEN = risk-on
      - AMBER = caution
      - RED = defensive
    - Include legend and title with FR id (`FR-042`).

6.8 FR-050 Walk-Forward Artifacts (2026-02-15)
  Required outputs:
    - `data/processed/phase13_walkforward.csv`
    - `data/processed/phase13_equity_curve.png`

  `phase13_walkforward.csv` key columns:
    - `date`: trading session date
    - `governor_state`: FR-041 Governor at `t`
    - `signal_weight`: deterministic signal weight at `t` (`1.0|0.5|0.0`)
    - `executed_weight`: shifted weight executed at `t` from prior signal
    - `spy_close`: SPY close
    - `spy_ret`: SPY daily return
    - `cash_ret`: chosen cash return for session
    - `cash_source`: `BIL|EFFR|FLAT`
    - `turnover`: `abs(executed_weight_t - executed_weight_{t-1})`
    - `cost`: `turnover * cost_bps`
    - `strategy_ret`: `executed_weight*spy_ret + (1-executed_weight)*cash_ret - cost`
    - `buyhold_ret`: SPY buy-and-hold return
    - `equity_curve`: cumulative strategy equity (start `1.0`)
    - `buyhold_curve`: cumulative SPY equity (start `1.0`)
    - `drawdown`: strategy drawdown from running peak
    - `buyhold_drawdown`: SPY drawdown from running peak

  FR-050 rules:
    - Execution lag: strict `t -> t+1`.
    - Cash hierarchy: `BIL` first, then `EFFR/252`, then flat `0.02/252`.

6.9 FR-060 Feature Store Artifacts (2026-02-15)
  Required outputs:
    - `data/processed/features.parquet`

  `features.parquet` key columns:
    - `date`: trading session date
    - `permno`: asset id
    - `ticker`: symbol (when available from ticker map)
    - `adj_close`: close used for feature construction
    - `volume`: volume used for flow/liquidity features
    - `rolling_beta_63d`: rolling beta vs market return
    - `resid_mom_60d`: rolling residual momentum
    - `amihud_20d`: rolling Amihud illiquidity
    - `yz_vol_20d`: Yang-Zhang annualized volatility
    - `atr_14d`: ATR-14 (or close-proxy ATR when OHLC unavailable)
    - `rsi_14d`: RSI-14
    - `dist_sma20`: `(close - sma20) / sma20`
    - `sma200`: 200-day simple moving average
    - `trend_veto`: `close < sma200`
    - `z_resid_mom`: cross-sectional z-score leg
    - `z_flow_proxy`: cross-sectional z-score leg for flow
    - `z_vol_penalty`: cross-sectional z-score leg for volatility penalty
    - `composite_score`: `z_resid_mom + z_flow_proxy - z_vol_penalty`
    - `yz_mode`: `true_ohlc|proxy_close_only`
    - `atr_mode`: `true_ohlc|proxy_close_only`

  FR-060 rules:
    - PIT-safe rolling computations only (backward-looking windows).
    - Close-only fallback must be explicit through mode flags.
    - Feature universe selection supports:
      - `universe_mode='yearly_union'` (default): as-of anchored yearly union.
        - let `anchor_date := append_start_ts` for incremental builds, else `start_date`.
        - annual liquidity is computed from rows with `date <= anchor_date`.
        - eligible union years are `year < year(anchor_date)` (bootstrap fallback: `year == year(anchor_date)` only when no prior year exists).
        - top `yearly_top_n` permnos are selected per eligible year and unioned.
      - `universe_mode='global'` (legacy): single global top `top_n` liquidity ranking.
    - Default knobs:
      - `yearly_top_n=100`
      - `top_n=3000` retained for legacy/global mode compatibility.
    - Safety guard:
      - Build must abort when selected yearly-union universe breaches the memory-envelope abort threshold.

6.10 FR-070 Alpha Engine Contract (2026-02-15)
  Module:
    - `strategies/alpha_engine.py`

  Primary interface:
  ```python
  class AlphaEngine:
      def build_daily_plan(
          self,
          features: pd.DataFrame,
          regime_state: str,
          asof_date: pd.Timestamp | None = None,
      ) -> AlphaPlanResult: ...
  ```

  Input schema (minimum):
    - `date`, `permno`
    - `adj_close`, `sma200`, `dist_sma20`
    - `rsi_14d`, `atr_14d`, `yz_vol_20d`
    - `composite_score`, `trend_veto`
    - `adj_close` history is used to derive PIT-safe `prior_50d_high` when absent.

  Structural rules (fixed):
    - Long-only universe gate requires `adj_close > sma200`.
    - Regime state normalization is strict (`strip().upper()`), with unknown tokens fail-safe to `RED`.
    - Regime budgets are fixed:
      - `GREEN -> 1.0`
      - `AMBER -> 0.5`
      - `RED -> 0.0`
    - Final exposure must satisfy:
      - `sum(weights) <= regime_budget`
      - `weights_i >= 0` for all assets.

  Adaptive rules (tunable via walk-forward only):
    - RSI entry gate supports:
      - fixed threshold mode (e.g., 30)
      - rolling percentile mode (e.g., bottom 5% over 252 days)
    - Entry trigger composition:
      - `dip_entry = rsi_gate & (pullback_gate | rsi_cross)`
      - `breakout_entry_green = (regime_state == "GREEN") & (adj_close > prior_50d_high)`
      - `entry = tradable & trend_ok & (dip_entry | breakout_entry_green)`
      - `prior_50d_high` is per-asset rolling 50-day high shifted by one bar (prior-only).
      - If both paths are true, dip reason code takes precedence.
    - ATR stop multiplier supports volatility-aware schedule.
    - Selection depth supports top-N or percentile depth.

  Output fields:
    - `weights`: normalized target weights for selected symbols.
    - `entries`: boolean entry mask.
    - `stop_price`: per-asset stop level (`entry - k*ATR`).
    - `reason_code`: deterministic explainability string.
      - Dip path: `MOM_DIP_<REGIME>_<ADAPT|FIXED>`
      - Breakout path: `MOM_BREAKOUT_GREEN_<ADAPT|FIXED>`
    - `regime_budget` and `budget_utilization`.
    - `alpha_telemetry` fields:
      - `alpha_score`
      - `entry_trigger`
      - `stop_loss_level`
      - `turnover`

  Integration hard rules:
    - Hysteresis:
      - Enter when rank `<= 5`.
      - Hold while rank `<= 20`.
      - Exit when rank `> 20`.
    - Ratchet-only stop:
      - `stop_t = max(stop_{t-1}, price_t - K*ATR_t)`.
    - Portfolio hard cap:
      - `sum(weights_t) <= regime_budget_t`.

  Walk-forward verifier:
    - `backtests/verify_phase15_alpha_walkforward.py`
    - Outputs:
      - `data/processed/phase15_walkforward.csv`
      - `data/processed/phase15_equity_curve.png`
    - Benchmark table:
      - `SPY` vs `Phase13_Governor` vs `Phase15_Alpha`

  FR-070 validation checks:
    - Regime hard-cap invariant always passes.
    - RED regime produces zero exposure.
    - Reason codes are non-empty for all selected names.

6.11 FR-080 Walk-Forward Optimization & Honing Contract (2026-02-15)
  Required outputs:
    - `data/processed/phase16_optimizer_results.csv`
    - `data/processed/phase16_best_params.json`
    - `data/processed/phase16_oos_summary.csv`

  Governance contract (FIX vs FINETUNE):
    - FIX (non-tunable):
      - FR-070 structural rules remain unchanged.
      - Regime budgets and long-only hard-cap invariants remain unchanged.
    - FINETUNE (WFO-tunable):
      - `entry_logic` (`dip`, `breakout`, `combined`)
      - `alpha_top_n`
      - `hysteresis_exit_rank`
      - `rsi_entry_percentile`
      - `atr_multiplier`

  Hard constraints:
    - `hysteresis_exit_rank >= alpha_top_n`.
    - Structural rules are fixed and may not be tuned in FR-080.
    - No OOS leakage:
      - OOS observations cannot participate in objective scoring, ranking,
        or tie-breaks.
      - OOS may only be used as a post-selection promotion gate (`stability_pass`).
    - Promotion selection policy (FR-080 mismatch fix):
      - Build promotable pool first:
        - `stability_pass AND activity_guard_pass`
        - valid train metrics (`objective_score`, `train_cagr`,
          `train_robust_score`, `train_ulcer`)
      - If promotable pool is non-empty, rank only promotable rows by:
        - `objective_score` (desc)
        - `train_cagr` (desc)
        - `train_robust_score` (desc)
        - `train_ulcer` (asc)
        - deterministic parameter tie-breakers:
          `entry_logic`, `alpha_top_n`, `hysteresis_exit_rank`, `adaptive_rsi_percentile`,
          `atr_preset` (ascending).
      - If promotable pool is empty:
        - keep train-only ranked fallback for diagnostics.
        - do not promote any candidate.
    - Phase 16.2 activity guards (strict `>`):
      - `trades_per_year > min_trades_per_year` (default `10.0`).
      - `exposure_time > min_exposure_time` (default `0.30`).
      - Promotion requires both: `stability_pass AND activity_guard_pass`.
      - Activity metrics are computed on the OOS/Test window only.

  Promoted defaults (candidate profile; runtime default only after Phase15 verifier PASS):
    - `alpha_top_n=10`
    - `hysteresis_exit_rank=20`
    - `adaptive_rsi_percentile=0.05`
    - `atr_preset=3.0` mapped to:
      - `atr_mult_low_vol=3.0`
      - `atr_mult_mid_vol=4.0`
      - `atr_mult_high_vol=5.0`

  Operational guardrail:
    - Promoted parameters are not runtime defaults unless Phase15 verifier status is `PASS`.
    - Current rollback defaults:
      - Alpha Engine is disabled by default in runtime/UI.
      - Safer RSI fallback default is `adaptive_rsi_percentile=0.15`.

  Performance controls:
    - Dataset hydration is single-pass per run (load once, reuse for all candidates).
    - Candidate evaluation supports optional multi-process execution:
      - `--max-workers` (`0` = auto core count cap by task count)
      - `--chunk-size`
      - `--disable-parallel`
      - `--progress-interval-seconds`
      - `--progress-path`
      - `--live-results-path`
      - `--live-results-every`
      - `--disable-live-results`
      - `--lock-stale-seconds`
      - `--lock-wait-seconds`
    - Runtime fallback is deterministic:
      - If parallel execution fails, optimizer retries sequentially in-process.
    - Artifact commit safety:
      - Outputs are staged and promoted as a bundle with rollback on promotion failure.
    - Runtime heartbeat artifacts:
      - `phase16_optimizer_progress.json` (status, completed/total, ETA, promotable-so-far, best candidate snapshot)
      - `phase16_optimizer_live_results.csv` (interim candidate table)

  Tournament baseline grid (Phase 16.5):
    - `entry_logic`: `dip`, `breakout`, `combined`
    - `alpha_top_n`: `10`, `20`
    - `hysteresis_exit_rank`: `20`, `30`
    - `adaptive_rsi_percentile`: `0.05`, `0.10`, `0.15`
    - `atr_preset`: `2.0`, `3.0`, `4.0`, `5.0`

  `phase16_optimizer_results.csv` minimum columns:
    - `candidate_id`
    - `train_start`, `train_end`
    - `test_start`, `test_end`
    - `entry_logic`
    - `alpha_top_n`, `hysteresis_exit_rank`
    - `adaptive_rsi_percentile`, `atr_preset`
    - `atr_mult_low_vol`, `atr_mult_mid_vol`, `atr_mult_high_vol`
    - `train_cagr`, `train_sharpe`, `train_max_dd`, `train_ulcer`
    - `test_cagr`, `test_sharpe`, `test_max_dd`, `test_ulcer`
    - `train_robust_score`, `test_robust_score`
    - `sharpe_degradation`, `stability_pass`, `objective_score`
    - `exposure_time`, `trades_per_year`, `activity_guard_pass`
    - `min_trades_per_year_guard`, `min_exposure_time_guard`
    - `selected_flag`, `promoted_flag`

  `phase16_best_params.json` minimum keys:
    - `train_window`
    - `test_window`
    - `strict_mode`
    - `max_sharpe_degradation`, `min_test_sharpe`
    - `min_trades_per_year_guard`, `min_exposure_time_guard`
    - `total_candidates`, `stable_candidates`, `activity_guard_candidates`, `promotable_candidates`, `selection_pool`
    - `selection_pool` values include:
      - `promotable_train_ranked`
      - `train_only_rejected_guardrails`
      - `no_valid_candidates`
    - `selected_activity`
    - `selected`
    - `train_selected`

  `phase16_oos_summary.csv` minimum columns:
    - `train_start`, `train_end`
    - `test_start`, `test_end`
    - selected parameter fields
    - `test_cagr`, `test_sharpe`, `test_ulcer`, `test_max_dd`
    - `stability_pass`, `selection_pool`
    - `exposure_time`, `trades_per_year`, `activity_guard_pass`
    - `min_trades_per_year_guard`, `min_exposure_time_guard`

## Phase 21 Day 1 Addendum: Stop-Loss Module Contract

Scope:
- Standalone module for position stops and portfolio drawdown scaling without OHLC dependency.

Module:
- `strategies/stop_loss.py`

Config contract (`StopLossConfig`):
- `atr_mode`: must be `proxy_close_only`.
- `atr_window`: default `20`.
- `initial_stop_atr_multiple`: default `2.0`.
- `trailing_stop_atr_multiple`: default `1.5`.
- `max_underwater_days`: default `60`.
- drawdown thresholds/scales:
  - `dd_tier1_threshold=-0.08`, `dd_tier1_scale=0.75`
  - `dd_tier2_threshold=-0.12`, `dd_tier2_scale=0.50`
  - `dd_tier3_threshold=-0.15`, `dd_tier3_scale=0.00`
  - `dd_recovery_threshold=-0.04`
- optional safety:
  - `min_stop_distance_abs` (default `0.0`).

Formula contract:
- ATR proxy:
  - `ATR_t = SMA(|close_t - close_{t-1}|, atr_window)`
- Initial stop:
  - `stop_initial = entry_price - initial_stop_atr_multiple * ATR_entry`
- Trailing stop candidate:
  - `stop_trailing_t = price_t - trailing_stop_atr_multiple * ATR_t`
- Ratchet (D-57):
  - `stop_t = max(stop_{t-1}, stop_candidate_t)`
- Time-based forced exit:
  - if underwater and `days_held > max_underwater_days`, exit.
- Portfolio drawdown:
  - `dd_t = (equity_t - peak_equity_t) / peak_equity_t`
  - tier mapping to scaling via thresholds above.

Test contract:
- `tests/test_stop_loss.py` validates:
  - ATR behavior and insufficient-history handling,
  - stage transitions and ratchet non-decreasing invariant,
  - underwater timeout exits,
  - drawdown tier/recovery logic,
  - zero-volatility edge behavior.

## Post-Phase-18 Alignment

Date: 2026-02-20  
Scope: retro-map current repository state to the ideal roadmap checkpoint before new risk-layer promotion.

Alignment mapping (current -> ideal endpoint):
- Data foundation:
  - TRI lake, macro/liquidity layers, and partition-aware feature contracts are implemented.
  - This maps to the ideal pre-risk endpoint where signal and execution data contracts are already stable.
- Strategy baseline:
  - C3 scorecard baseline is locked and auditable (`strategies/production_config.py`).
  - This is treated as the control group for all subsequent risk/execution deltas.
- Governance baseline:
  - SAW workflow, decision logs, and lessons loop are active and enforced.
  - This maps to the ideal endpoint requiring evidence-first promotion discipline before extra complexity.

Retro-enforced gate policy from this point forward:
- No new risk/execution layer may ship without quantified deltas vs latest C3 baseline under:
  - same date window,
  - same `cost_bps`,
  - same `engine.run_simulation` path.
- If promotion gates fail, the layer is blocked/aborted and work pivots to upstream signal quality.

Forward reference:
- Active alignment execution state and roadmap are tracked in `docs/phase19-brief.md`.

## Phase 23 Addendum: SDM Ingestion/Assembly Contract

Date: 2026-02-22  
Scope: lock PIT-safe 3-pillar SDM ingestion path and final feature assembly contract.

Pipelines:
- `scripts/ingest_compustat_sdm.py`:
  - pulls `comp.fundq` + `totalq.total_q`,
  - computes trajectory/intangible features,
  - writes `data/processed/fundamentals_sdm.parquet`.
- `scripts/ingest_frb_macro.py`:
  - pulls `frb.rates_daily`,
  - computes macro cycle derivatives,
  - writes `data/processed/macro_rates.parquet`.
- `scripts/ingest_ff_factors.py`:
  - pulls `ff.fivefactors_daily` (+ momentum),
  - writes `data/processed/ff_factors.parquet`.
- `scripts/assemble_sdm_features.py`:
  - backward `merge_asof` joins fundamentals to macro/factors on `published_at`,
  - writes `data/processed/features_sdm.parquet`.

Critical safety rules:
- PIT anchors:
  - fundamentals availability = `rdq`,
  - Peters & Taylor availability = `datadate + 90 days`.
- `merge_asof` key ordering:
  - must be globally monotonic on timeline key before join.
- Atomic writes:
  - all SDM parquet writes are `tmp -> os.replace`.
- Identifier traceability:
  - allow+audit unmapped `permno` rows via:
    - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`.

## Phase 25B Addendum: Global Hardware Supply Chain (Osiris)

Date: 2026-02-24  
Scope: lock the public-data fallback macro signal path derived from global non-US hardware fundamentals in `bvd_osiris`.

Data source contract:
- WRDS library and tables:
  - `bvd_osiris.os_fin_ind` (financial statement fields),
  - `bvd_osiris.os_activ_naics12cde` (secondary NAICS),
  - `bvd_osiris.os_gen` (country and core NAICS context).
- Hardware filter:
  - include rows where either core or secondary NAICS starts with `334`:
    - `caics12cod LIKE '334%' OR naics12cde LIKE '334%'`.
- Geography filter:
  - non-US only:
    - `cntrycde <> 'US'`.

Extraction and dedup contract (`data/osiris_loader.py`):
- SQL-level duplication guard:
  - `SELECT DISTINCT` over joined records.
- pandas-level duplication guard:
  - `drop_duplicates(subset=['os_id_number', 'closdate'])`.
- Financial fields:
  - `revenue = COALESCE(data13004, data13002, data13000)`,
  - `inventory = data20010`.
- Base signal formula:
  - `inv_turnover = revenue / inventory`.
- Global daily aggregation:
  - `median_inv_turnover = median(inv_turnover) by closdate`.
- Regional daily aggregation:
  - same metric by `closdate, iso_country` for `TW, KR, DE, JP, CN`.

Alignment and PIT lag contract (`scripts/align_osiris_macro.py`):
- Public reporting lag:
  - `knowledge_date = closdate + 60 days`.
- Daily calendar:
  - business days from `2015-01-01` through run-date `today`.
- Alignment method:
  - `merge_asof(direction='backward')` from daily calendar to `knowledge_date`.
- Daily continuation:
  - forward-fill aligned `median_inv_turnover`.
- 252-day normalization:
  - `z252_t = (x_t - mean_252_t) / std_252_t`,
  - where `x_t = median_inv_turnover_t`.

Validation contract:
- Market target:
  - QQQ 60-trading-day forward return:
    - `fwd_ret_60d_t = Close_{t+60} / Close_t - 1`.
- IC metric:
  - Spearman correlation between `median_inv_turnover_z252` and `fwd_ret_60d`.
- Latest observed evidence (2026-02-24 run):
  - `IC = +0.087636`, `p = 1.18113e-05`, `N = 2492`.

Artifacts:
- `data/processed/osiris_global_hardware_daily.parquet`
- `data/processed/osiris_regional_hardware_daily.parquet`
- `data/processed/osiris_aligned_macro.parquet`

## Phase 29 Addendum: Microstructure Telemetry Contract

Date: 2026-03-01  
Scope: execution-quant instrumentation at broker/orchestrator seam for arrival anchoring, partial-fill VWAP, deterministic slippage, and latency decomposition.

### Command-time arrival anchor (`main_console.py`)
- For each seeded `Sovereign_Command` row, capture:
  - `arrival_ts`: UTC timestamp at command generation (`ms` precision).
  - `arrival_quote_ts`: broker quote timestamp when available.
  - `arrival_bid_price`, `arrival_ask_price`.
  - `arrival_price`: midpoint at command-time quote snapshot.
- Midpoint formula:
  - `arrival_price = (arrival_bid_price + arrival_ask_price) / 2`.

### Broker execution telemetry (`execution/broker_api.py`)
- Submit path captures:
  - `submit_sent_ts`, `broker_ack_ts`.
  - order lifecycle fields (`created_at`, `submitted_at`, `updated_at`, `filled_at`, `filled_qty`, `filled_avg_price`).
- Partial-fill extraction:
  - primary: broker activity feed rows (`FILL`) filtered to the same `order_id`.
  - fallback: snapshot-level synthetic fill from `filled_qty` + `filled_avg_price` when activity rows are unavailable.
- Fill summary fields:
  - `fill_count`, `fill_qty`, `fill_notional`, `fill_vwap`, `first_fill_ts`, `last_fill_ts`.

### Deterministic execution-cost formulas (`execution/microstructure.py`)
- Partial-fill VWAP per `client_order_id`:
  - `VWAP_fill = sum(fill_price_i * fill_qty_i) / sum(fill_qty_i)`.
- Buy implementation shortfall:
  - `IS_buy = (VWAP_fill - arrival_price) * fill_qty`.
- Sell implementation shortfall (sign-normalized to cost):
  - `IS_sell = (arrival_price - VWAP_fill) * fill_qty`.
- Slippage in basis points (cost-positive convention):
  - `slippage_bps = ((signed_delta) / arrival_price) * 10,000`,
  - where `signed_delta = VWAP_fill - arrival_price` for buys,
  - and `signed_delta = arrival_price - VWAP_fill` for sells.
- Baseline cohort alignment (`scripts/evaluate_execution_slippage_baseline.py`):
  - intended-cohort denominator is total rows, not observed-only rows.
  - `cohort_slippage_bps_i = slippage_bps_i` when observed, else `0.0` for no-fill/uncaptured rows.
  - non-finite numeric inputs are sanitized before aggregation:
    - `sanitize(x) = x if isfinite(x) else null`.
  - aggregate baseline uses `cohort_slippage_bps`:
    - `mean_slippage_bps = mean(cohort_slippage_bps)`,
    - `median_slippage_bps = median(cohort_slippage_bps)`.
  - observability counters are still emitted:
    - `observed_rows`, `zero_imputed_rows`.

### Latency decomposition (`execution/microstructure.py`)
- `latency_ms_command_to_submit = submit_sent_ts - arrival_ts`.
- `latency_ms_submit_to_ack = broker_ack_ts - submit_sent_ts`.
- `latency_ms_ack_to_first_fill = first_fill_ts - broker_ack_ts`.
- `latency_ms_command_to_first_fill = first_fill_ts - arrival_ts`.

### Adaptive heartbeat freshness (`execution/microstructure.py`)
- Scope:
  - execution heartbeat freshness is evaluated from rolling `latency_ms_submit_to_ack` observations without look-ahead.
- Rolling baseline:
  - `history_t = {latency_{t-k}, ..., latency_{t-1}}` with window size `N=64`.
  - cross-batch bootstrap history must be ordered by explicit event-time (coalesced timestamp columns), not append order / row id.
  - `median_t = median(history_t)`.
  - `MAD_t = median(|history_t - median_t|)`.
  - `robust_sigma_t = max(1.4826 * MAD_t, 5.0 ms)`.
- Adaptive limit:
  - when `len(history_t) >= 12`:
    - `adaptive_limit_t = median_t + 4.0 * robust_sigma_t`.
  - bootstrap fallback (insufficient history):
    - `adaptive_limit_t = 150.0 ms`.
  - clamp:
    - `adaptive_limit_t = clip(adaptive_limit_t, 25.0 ms, hard_ceiling_ms)`.
- Hard ceiling:
  - `hard_ceiling_ms = env(TZ_EXEC_HEARTBEAT_HARD_CEILING_MS, default=500.0)`.
- Deterministic decision:
  - `BLOCK` if `latency_ms_submit_to_ack` is missing.
  - `BLOCK` with `reason=hard_ceiling_exceeded` if `latency > hard_ceiling_ms`.
  - `BLOCK` with `reason=adaptive_limit_exceeded` if `latency > adaptive_limit_t`.
  - otherwise `PASS`.
- Persisted telemetry fields:
  - `heartbeat_decision`, `heartbeat_reason`,
  - `heartbeat_is_blocked`, `heartbeat_is_hard_block`,
  - `heartbeat_mode`, `heartbeat_window_count`,
  - `heartbeat_window_median_ms`, `heartbeat_window_mad_ms`, `heartbeat_robust_sigma_ms`,
  - `heartbeat_adaptive_limit_ms`, `heartbeat_hard_ceiling_ms`,
  - `heartbeat_latency_ms`, `heartbeat_latency_zscore`.

### Post-trade sink
- Order-level sink:
  - `data/processed/execution_microstructure.parquet`
  - `data/processed/execution_microstructure.duckdb` table `execution_microstructure`
- Fill-level sink:
  - `data/processed/execution_microstructure_fills.parquet`
  - DuckDB table `execution_microstructure_fills`
- Persistence wiring:
  - local submit path (`main_console.py`) persists telemetry immediately after helper returns and fails closed if telemetry write fails.
- Backfill + baseline evaluation runners:
  - `scripts/backfill_execution_latency.py`:
    - deterministic historical annotation of heartbeat freshness columns into
    - `data/processed/execution_microstructure_latency_backfill.parquet`,
    - plus summary JSON `data/processed/execution_microstructure_latency_backfill_summary.json`.
  - `scripts/evaluate_execution_slippage_baseline.py`:
    - baseline signed-slippage report outputs:
    - `data/processed/execution_slippage_baseline_summary.json`,
    - `data/processed/execution_slippage_baseline_by_side.csv`,
    - `data/processed/execution_slippage_baseline_by_symbol.csv`.
  - Source-of-truth loader contract (Option 2 fail-loud):
    - default mode is strict DuckDB primary sink:
      - `source_mode = duckdb_strict`.
      - if DuckDB file is missing/unreadable/query-failing, scripts raise `PrimarySinkUnavailableError` (no implicit parquet fallback).
    - explicit parquet override is opt-in only:
      - CLI: `--source-mode parquet_override`
      - env override: `TZ_EXEC_TELEMETRY_SOURCE_MODE=parquet_override`
    - unsupported mode tokens are rejected (`ValueError`).

## Phase 30 Addendum: Release Engineering / MLOps Deterministic Pipeline

Date: 2026-03-01  
Scope: immutable image artifacts, deterministic promotion, and automatic N-1 rollback tied to startup diagnostics.

### Immutable artifact contract
- Deployable unit is a digest-locked container reference:
  - `release_ref = "<repo>:<tag>@sha256:<64-hex>"`
- Runtime release metadata schema:
  - `core/release_metadata.py` (`ReleaseRecord`, `ReleaseMetadata`)
- Canonical state artifact:
  - `data/processed/release_metadata.json`

### Promotion and rollback controller
- Controller:
  - `scripts/release_controller.py`
- Required sequence:
  1. stage candidate (`status=pending_probe`),
  2. run startup probe (docker mode deploy + startup watch),
  3. finalize:
     - `status=active` on success,
     - `status=rolled_back` when restore N-1 is verified on failure,
     - `status=rollback_failed` when restore N-1 cannot be verified.
- External probe safety gate:
  - `--mode external-probe` requires explicit `--allow-external-probe-promote` acknowledgement.
  - This mode is only valid when runtime deploy/rollback is managed outside `scripts/release_controller.py`.
- Atomicity:
  - metadata writes use `tmp -> fsync -> os.replace`.

### Startup containment wiring
- Docker mode deploy probe:
  - starts candidate service container with:
    - `TZ_RELEASE_DIGEST=<candidate_digest>`
  - monitors startup watch window,
  - if candidate exits during watch, controller:
    - removes candidate container,
    - starts previous known-good release image automatically.

### UI cache governance formula
- Cache fingerprint is release-bound:
  - `cache_fingerprint = "<version>@sha256:<release_digest|local-dev>"`
- Implementation path:
  - `core/release_metadata.py` (`build_release_cache_fingerprint`)
  - `dashboard.py` (`_release_bound_cache_version`)

## Phase 29.1 Addendum: Stream 5 Option 2 Production Patch

Date: 2026-03-01  
Scope: execution submit/recovery semantics hardening for terminal unfilled outcomes, latency-anchor recovery backfill, drift-safe latency decomposition, and signed slippage assertions.

### Local-submit acceptance contract
- Terminal unfilled outcomes are non-accepted:
  - `terminal_unfilled := status in {canceled, cancelled, rejected, expired} AND fill_qty <= 0`.
  - `accepted_local_submit := (ok is True) AND NOT terminal_unfilled`.
- Fail-closed behavior:
  - when `terminal_unfilled` is true, emit `ok=False` with deterministic error:
  - `error = "terminal_unfilled:<status>"` (or existing explicit error if present in orchestrator row).
- Implementation path:
  - `execution/broker_api.py` (`_is_terminal_unfilled_result`, `_normalize_submit_acceptance`)
  - `main_bot_orchestrator.py` (`_is_terminal_unfilled_execution_result`, retry loop fail-closed branch)

### Recovery latency-anchor backfill contract
- For recovery payloads (client-order-id lookup), anchor fields are backfilled from broker lifecycle timestamps:
  - `submit_sent_ts := submit_sent_ts || submitted_at || created_at || updated_at`
  - `broker_ack_ts := broker_ack_ts || updated_at || submitted_at || created_at`
  - where `||` means first non-empty value.
- Implementation path:
  - `execution/broker_api.py` (`_backfill_latency_anchors`)
  - `execution/microstructure.py` (`_resolve_latency_anchors`)

### Clock-drift guard contract
- Latency decomposition is fail-closed against negative wall-clock deltas:
  - `latency_ms = max(0, (t_end - t_start) * 1000)`.
- Applies to:
  - command-to-submit,
  - submit-to-ack,
  - ack-to-first-fill,
  - command-to-first-fill.
- Implementation path:
  - `execution/microstructure.py` (`_ms_diff`)

### Slippage sign-preservation contract
- Slippage retains directional sign and must not be absolute-value coerced:
  - buy: `delta = fill_vwap - arrival_price`
  - sell: `delta = arrival_price - fill_vwap`
  - `slippage_bps = (delta / arrival_price) * 10,000`
- Expected behavior:
  - favorable execution => negative slippage,
  - parity execution => zero slippage.
- Validation path:
  - `tests/test_execution_microstructure.py` (negative and zero slippage assertions)

3.35 Sovereign Execution Hardening [Phase 31] <- NEW
[FR-150 Step Set: Trust Boundary + Telemetry Durability]
    - Objective:
      - eliminate replay-race, spool-corruption, and semantic-coercion fail-open pathways.
    - Hard contracts:
      - signed envelope replay check+append executes atomically under lock,
      - malformed replay rows are quarantined (`.malformed.jsonl`) with valid-ledger rewrite,
      - spool replay is idempotent with deterministic UID,
      - schema-invalid and stale trailing-partial spool lines are quarantined (`.bad`) with cursor progress,
      - local-submit path must pass bounded telemetry durability gate before success/notify.
    - Semantic guards:
      - `trend_veto`/quality flags use tokenized boolean normalization,
      - `composite_score` selection is numeric + stable tie-break,
      - malformed dates in ticker ranking are explicit fail-fast errors.
    - Verification matrix:
      - targeted integrated pytest matrix + compile gate required for stream close.

### Stream 5 Option 2 Reconciliation Addendum (2026-03-01)

#### Terminal status fail-closed refinement
- Terminal statuses (execution seam):
  - `{canceled, cancelled, rejected, expired, done_for_day, stopped, suspended}`.
- Unfilled terminal rule:
  - `terminal_unfilled := terminal_status AND fill_qty <= 0` -> final `ok=False`, non-retry.
- Partial-fill terminal rule:
  - `terminal_partial := terminal_status AND fill_qty > 0` -> final `ok=False`, non-retry.

#### Telemetry row consistency refinement
- If `partial_fills` is empty but aggregate fill summary is present (`fill_count>0`, `fill_qty>0`, `fill_vwap>0`), telemetry must emit a synthesized fill row so order/fill tables stay join-consistent.
- Synthesized row contract:
  - `fill_source = summary_fallback`.

#### Legacy parquet replay safety refinement
- Legacy single-file parquet dedupe must preserve historical rows with missing dedupe keys.
- Null-safe key rule:
  - for each key in `{record_id, uid, _spool_record_uid}` dedupe only records with non-empty key values and preserve null/empty-key rows.

## Phase G4 Addendum: Real Canonical Dataset Readiness Fixture

Date: 2026-05-09
Scope: first tiny Tier 0 canonical price-slice readiness gate; no strategy search or alpha evidence.

### Canonical slice contract
- Artifact:
  - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet`
- Manifest:
  - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet.manifest.json`
- Source:
  - `data/processed/prices_tri.parquet`
- Required source fields:
  - `source_quality = "canonical"`
  - `extra.source_tier = "tier0"`
  - `provider = "terminal_zero"`
  - `provider_feed = "tri_repaired_prices"`
- Slice:
  - `row_count = 123`
  - `symbol_count = 3`
  - `date_range = 2024-01-02 -> 2024-02-29`
  - `primary_key = {date, permno}`

### Readiness formula
- `g4_ready_for_g5 = true` iff:
  - `manifest.sha256 == compute_sha256(artifact)`;
  - `manifest.row_count == len(df)`;
  - `manifest.schema.columns == list(df.columns)`;
  - `manifest.date_range == {min(df.date), max(df.date)}`;
  - all required numeric fields are finite;
  - `count_duplicates(df[date, permno]) = 0`;
  - dates are monotonic increasing per `permno`;
  - `tri > 0`, `legacy_adj_close > 0`, `raw_close > 0`, `volume >= 0`;
  - `-1.0 < total_ret <= 10.0`;
  - `sidecar_required = false` for the passing slice.

### Boundary lock
- G4 report is readiness-only:
  - no alpha metrics;
  - no strategy ranking;
  - no alerts;
  - no broker action;
  - no promotion packet;
  - no registry candidate status mutation.
- Implementation paths:
  - `v2_discovery/readiness/canonical_slice.py`
  - `v2_discovery/readiness/canonical_readiness.py`
  - `tests/test_g4_real_canonical_readiness_fixture.py`

## Phase G6 Addendum: V1/V2 Real-Slice Mechanical Comparison

Date: 2026-05-09
Scope: compare official V1 replay and V2 proxy mechanics on one tiny Tier 0 canonical price slice; no strategy search or alpha evidence.

### Comparison contract
- Artifact:
  - `data/registry/g6_v1_v2_real_slice_mechanical_report.json`
- Manifest:
  - `data/registry/g6_v1_v2_real_slice_mechanical_report.json.manifest.json`
- Input slice:
  - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet`
- Required source fields:
  - `source_quality = "canonical"`
  - `extra.source_tier = "tier0"`
  - `provider = "terminal_zero"`
  - `provider_feed = "tri_repaired_prices"`
- Slice:
  - `row_count = 123`
  - `symbol_count = 3`
  - `date_range = 2024-01-02 -> 2024-02-29`

### Mechanical comparison formula
- `g6_match = true` iff:
  - V1 positions equal V2 positions exactly after normalized date/permno ordering;
  - V1 cash equals V2 cash exactly;
  - V1 turnover equals V2 turnover exactly;
  - V1 transaction cost equals V2 transaction cost exactly;
  - V1 gross exposure equals V2 gross exposure exactly;
  - V1 net exposure equals V2 net exposure exactly;
  - V1/V2 row count, date range, source quality, and manifest URI match.
- Engine names and versions are recorded, not equality-forced, because V1 and V2 are intentionally distinct engines.

### Boundary lock
- G6 report is mechanical-comparison-only:
  - no alpha metrics;
  - no strategy ranking;
  - no alerts;
  - no broker action;
  - no promotion packet;
  - `promotion_ready = false`;
  - `v2_promotion_ready = false`.
- Implementation paths:
  - `v2_discovery/replay/real_slice_v1_v2_comparison.py`
  - `v2_discovery/replay/mechanical_comparison_report.py`
  - `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`

## Phase G7 Addendum: Candidate Family Definition

Date: 2026-05-09
Scope: define the first controlled candidate family before search; no candidate generation, backtest, replay, proxy run, alpha evidence, ranking, alert, broker call, or promotion packet.

### Family contract
- Artifact:
  - `data/registry/candidate_families/pead_daily_v0.json`
- Manifest:
  - `data/registry/candidate_families/pead_daily_v0.json.manifest.json`
- Registry report:
  - `data/registry/candidate_family_registry_report.json`
- Family:
  - `family_id = "PEAD_DAILY_V0"`
  - `status = "defined"`
  - `data_tier_required = "tier0"`
  - `source_quality_required = "canonical"`
  - `sidecar_required = false`

### Trial-budget formula
- `finite_trial_count = product(count(options_p) for p in parameter_space)`.
- For `PEAD_DAILY_V0`:
  - `holding_days = {1, 3, 5, 10}` -> 4 options;
  - `liquidity_floor = {adv_usd_5m, adv_usd_20m, adv_usd_50m}` -> 3 options;
  - `event_window_lag = {1, 2}` -> 2 options;
  - `finite_trial_count = 4 * 3 * 2 = 24`.
- `trial_budget_valid = true` iff `finite_trial_count <= trial_budget_max`.

### Boundary lock
- G7 report is definition-only:
  - `defined_only = true`;
  - `candidate_generation_enabled = false`;
  - `result_generation_enabled = false`;
  - `promotion_ready = false`;
  - `alerts_emitted = false`;
  - `broker_calls = false`.
- Family definitions are append-only/versioned; silent mutation is rejected.
- Tier 2, yfinance, OpenBB, and operational Alpaca cannot be allowed as promotion evidence.
- Implementation paths:
  - `v2_discovery/families/schemas.py`
  - `v2_discovery/families/trial_budget.py`
  - `v2_discovery/families/registry.py`
  - `v2_discovery/families/validation.py`
  - `tests/test_g7_candidate_family_definition.py`

## Phase G7.1 Addendum: Roadmap Realignment / Product Charter

Date: 2026-05-09
Scope: product roadmap and dashboard taxonomy realignment only; no candidate generation, backtest, replay, proxy run, alpha evidence, ranking, alert, broker call, or promotion packet.

### Product charter
- Terminal Zero is discretionary augmentation for de-risked asymmetric upside.
- Product focus:
  - `product_focus = 0.90 * supercycle_gem_discovery + 0.10 * buying_range_hold_discipline_prompting`.
- This is a planning allocation model only. It is not a portfolio allocation, signal weight, score, threshold, or execution rule.

### Family classification
- Primary product family target:
  - `SUPERCYCLE_GEM_DAILY_V0`
  - status: planned for definition, not implemented
- Tactical signal family:
  - `PEAD_DAILY_V0`
  - status: defined by G7 and still valid
  - role: tactical signal family / future evidence module, not the roadmap center

### Dashboard taxonomy
- Five panels:
  - thesis health;
  - entry discipline;
  - hold discipline;
  - flow and positioning;
  - regime.
- Flow and positioning inputs are contextual and source-quality labeled.
- Short-squeeze and CTA-type signals are not automatic triggers.

### Roadmap sequence
- G7.1: roadmap realignment, discretionary augmentation + supercycle gem framing.
- G7.2: define `SUPERCYCLE_GEM_DAILY_V0`, no search.
- G8: create one thesis candidate card, no search.
- G9: build dashboard signal map, no alpha search.
- G10: begin bounded discovery inside one approved family.
- G11: entry/hold discipline monitor.
- G12: paper-only buying-range prompts.

### Boundary lock
- G8 PEAD candidate generation is held until a separate approval.
- No implementation code is added by G7.1.
- No G7 family artifacts are mutated by G7.1.
- No buy/sell signal, ranking, alert emission, broker path, live order, paper trade, promotion packet, or human-reviewed approval is authorized.

### Documentation paths
- `docs/architecture/product_roadmap_discretionary_augmentation.md`
- `docs/architecture/dashboard_signal_taxonomy.md`
- `docs/architecture/supercycle_gem_family_policy.md`
- `docs/handover/phase65_g71_handover.md`

## DASH-2 Portfolio Allocation Runtime Slice

### Runtime ordering
- `Portfolio & Allocation` renders:
  - `Portfolio Optimizer`
  - `YTD Performance`
  - `Shadow Portfolio`
- Portfolio Optimizer remains top-level and is not hidden behind an expander.

### Return formula
- `portfolio_daily_return_t = sum(weight_i * price_return_i_t)`.
- `portfolio_ytd_equity_t = cumulative_product(1 + portfolio_daily_return_t)`.
- `portfolio_ytd_return = portfolio_ytd_equity_last - 1`.
- `weight_i` comes from current optimizer output when available.

### Freshness boundary
- Selected stocks plus SPY/QQQ may use an in-memory yfinance adjusted-close overlay for display freshness.
- The overlay does not write canonical data and does not authorize provider ingestion, alerting, broker calls, candidate scoring, or candidate ranking.
- Portfolio Optimizer selected-stock overlay fetching, scaling, stitching, and strategy-metrics JSON parsing are owned by `core/data_orchestrator.py`, not the Streamlit view.
- Recent close overlays are cached under `data/runtime_cache/optimizer_live_overlay` as display-only Parquet files.
- `overlay_cache_key = sha256(version, sorted_tickers, start_iso)[:24]`.
- `overlay_cache_hit = cache_file_exists and cache_age_seconds <= cache_ttl_seconds`.
- `cold_cache_behavior = schedule_background_refresh and return local_TRI_prices`.
- The overlay scaling cache key is `sha256(local_price_frame) + ":" + sha256(live_price_frame)` and returns copy-safe cached dataframes.

### Optimizer runtime cache
- Optimizer reruns are cached with Streamlit `st.cache_data`.
- `optimizer_cache_inputs = method + selected_price_frame + max_weight + risk_free_rate`.
- Sector caps are applied after optimizer weights and are tested as post-solver constraints; they are not encoded as SLSQP constraints.

### Evidence paths
- `core/data_orchestrator.py`
- `dashboard.py`
- `views/optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_optimizer_view.py`
- `tests/test_optimizer_core_policy.py`

## Portfolio Replay Selection Identity

- `PortfolioReplaySelection` is the explicit Portfolio replay universe handoff from optimizer controls to dashboard replay.
- The selection stores method, max-weight cap, risk-free rate, selected replay assets, latest price date, source, and a validation signature.
- Signature formula: `selection_signature = f(version, method, max_weight, risk_free_rate, replay_asset_identities, price_frame_identity)`.
- `price_frame_identity = {rows, columns, index_start, index_end, columns_hash, selected_price_hash}`.
- `selected_price_hash = sha256(hash_pandas_object(prices_wide[replay_assets], index=True) + typed_replay_asset_identities)`.
- Dashboard replay cache signatures preserve typed asset identities such as `int:1` and `str:1`.
- Dashboard replay requests must fail closed with `portfolio_replay_selection_unavailable` when the signed selection is missing, stale, mismatched, or not present in the current price frame.
- Hidden `optimizer_universe` state and first-10 price-column fallback are not replay asset sources.
- Optimizer builder failures clear the signed selection and replay/YTD caches.
- Transitional dashboard aux-row producer loading remains a backend follow-up until saved artifacts emit dashboard cache signatures for event/decision surfaces.

## Portfolio Lifecycle Current Holds

### Current holding state
- Position Lifecycle Replay is the authority for current open holdings when replay evidence exists.
- A ticker is currently held when its latest lifecycle event at or before the current as-of timestamp is `ENTER`.
- A ticker is closed only when a later lifecycle `EXIT` exists at or before the current as-of timestamp.
- Future-dated lifecycle rows must not affect today's current portfolio.
- Lifecycle JSONL writes must use temp-file replacement, and malformed rows must fail closed instead of being ignored.

### Portfolio & Allocation behavior
- If lifecycle replay is not sell-all, Portfolio & Allocation must not render the current allocation as `100% Cash`.
- Open lifecycle holdings enter the universe as `included_current_hold`, even when today's scanner label is `EXIT` or `KILL`.
- When there are open lifecycle holdings and no fresh PIT `ENTER` candidates, the allocation surface renders lifecycle holds plus residual cash instead of running a new optimizer allocation.
- Residual cash is preserved for performance math; weights are normalized only when their sum exceeds 100%.
- Live ticker-mapped performance weights preserve sub-100% exposure and normalize only when mapped weights exceed 100%.

### Rule of 100 method label
- The Portfolio Optimizer `Method` dropdown includes `Rule of 100`.
- `Rule of 100` is a lifecycle allocation mode: it renders current Rule100 lifecycle replay holdings plus residual cash.
- If there are no open lifecycle holdings, `Rule of 100` renders cash-only session state.
- `Rule of 100` does not call `_run_optimizer_cached(...)` and is not a new optimizer objective.

### Evidence paths
- `data/portfolio_lifecycle_log.py`
- `strategies/portfolio_universe.py`
- `strategies/optimizer.py`
- `views/optimizer_view.py`
- `dashboard.py`
- `tests/test_position_lifecycle.py`
- `tests/test_portfolio_universe.py`
- `tests/test_optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Lifecycle Decision Export

### Export behavior
- `export_lifecycle_decision_log(...)` writes PIT replay-analysis rows without appending lifecycle events.
- `BUY` rows must match lifecycle `ENTER` events.
- `SELL` rows must match lifecycle `EXIT` events.
- `HOLD` rows explain held ticker-days that did not emit a sell.
- `NO_ACTION` rows explain flat ticker-days that did not emit a buy.

### Rule-of-100 proxy fields
- `demand = z_demand`
- `supply = z_inventory_quality_proxy`
- `pricing = z_moat`
- `margin = z_discipline_cond`
- `rule100_confirmed = count(present factors) >= 3 AND count(positive factors) >= 3`
- These are audit proxies only until literal Rule-of-100 factor columns exist.

### Evidence paths
- `scripts/pit_lifecycle_replay.py`
- `tests/test_pinned_universe.py`
- `data/portfolio_lifecycle_decision_log.jsonl`
- `data/portfolio_lifecycle_buy_sell_log.jsonl`
- `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

## Rule100 Lifecycle Policy v0

### Rule100State adapter
- `Rule100State.demand = z_demand`
- `Rule100State.supply = z_inventory_quality_proxy`
- `Rule100State.pricing = z_moat`
- `Rule100State.margin = z_discipline_cond`
- `Rule100State.provenance` records the source column for every proxy field.

### Lifecycle transitions
- `BUY`: flat ticker, 3/4 positive Rule100 state, technical entry zone, three-day confirmation, and no cooldown.
- `HOLD`: held ticker with at least 2/4 positive factors, unless full exit or trim condition applies.
- `TIGHTEN`: held ticker with fewer than 2/4 positive factors; audit-only in v0.
- `TRIM`: held ticker with `0.12 < dist_sma20 <= 0.20`; audit-only in v0.
- `EXIT`: held ticker with `dist_sma20 > 0.20` or confirmed trend veto.
- `NO_ACTION`: flat ticker without confirmed BUY.

### Sizing
- `target_weight = min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15)`.
- v0 does not apply TRIM/TIGHTEN suggested deltas to actual weights.

### Evidence paths
- `scripts/pit_lifecycle_replay.py`
- `tests/test_pinned_universe.py`
- `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`
- `docs/context/e2e_evidence/rule100_v0_lifecycle_replay_tmp.jsonl`

## Rule100 Softmax v1 Audit

- `strategies/rule100_softmax.py` owns the pure softmax v1 sizing helpers and the thin Kelly comparator.
- `scripts/rule100_softmax_v1_audit.py` owns the shared PIT replay/audit harness.
- `views/optimizer_view.py` owns the explicit `Rule of 100` UI routing to softmax v1 target weights.
- `dashboard.py` owns the lifecycle transaction-log display overlay; it must label v0 ledger weight as `Event Weight` and derived sizing as `Softmax v1 Target`.
- Softmax v1 is the primary sizing path for the audit set: `budget = min(1.0, 0.10 * eligible_count)`, `weights = cap_15pct(softmax(score / tau) * budget)`, and cash residual is explicit.
- Kelly remains comparator-only on the same candidate frame; it is not a second full stack or a new optimizer objective.
- Artifact set: `data/processed/rule100_softmax_v1_summary.json`, `data/processed/rule100_softmax_v1_comparison.csv`, `data/processed/rule100_softmax_v1_sample_output.csv`, `data/processed/rule100_softmax_v1_cash_allocation.csv`, `data/processed/rule100_softmax_v1_history.csv`.
- Selecting `Rule of 100` stores `portfolio_allocation_state.source = "rule100_softmax_v1"` and writes softmax target weights into the same allocation state consumed by YTD.
- Current-state contract: AMAT and LRCX are the only softmax-eligible current holds, each at 10%; TSM is `tighten_below_hold_threshold` and target 0%; cash residual is 80%.
- This does not change the lifecycle replay log, provider ingestion, broker behavior, alerts, ranking, or optimizer objective.

## Rule100 Softmax v1.1 Research Contract

- `strategies/rule100_softmax_v1_1.py` owns research-only continuous v1.1 scoring.
- `scripts/rule100_softmax_v1_1_audit.py` writes only the active v1.1 comparison CSV and summary JSON artifacts.
- Active artifacts: `data/processed/rule100_softmax_v1_1_comparison.csv` and `data/processed/rule100_softmax_v1_1_summary.json`.
- `data/processed/rule100_softmax_v1_1_history.csv` is not current; if present, the audit script retires it to `data/processed/rule100_softmax_v1_1_history.retired.csv`.
- Factor coverage counts one value per approved group: demand, inventory/supply, moat/pricing, and capital discipline.
- Alternate capital-discipline columns (`capital_cycle_score`, `quality_composite`) cannot double-count coverage.
- Missing factor strength shrinks toward neutral with `factor_strength = mean_available_rank * coverage + 0.50 * (1 - coverage)`.
- Current same-window artifact has AMAT/LRCX factor coverage 4/4, TSM factor coverage 4/1 positive, and no active v1.1 history artifact.
- Real dashboard regression coverage uses `AppTest.from_file("dashboard.py")` for the Policy Target Timeline TSM row.

## Optimizer History Diagnostics Split

- `OptimizerUniverseResult.insufficient_history` remains the backend fail-closed gate.
- Visible Portfolio Optimizer diagnostics split that bucket into `Missing History` and `Stale Endpoint`.
- `Missing History` maps to `local_price_history_unavailable` and `open_position_price_history_unavailable`.
- `Stale Endpoint` maps to `stale_price_endpoint` and `open_position_stale_price_endpoint`.
- Universe Audit rows expose `Latest Price Date`.
- Contract: `OPTIMIZER_HISTORY_DIAGNOSTIC_SPLIT := VALID iff (missing_history_visible = 1) and (stale_endpoint_visible = 1) and (latest_price_date_visible = 1) and (insufficient_history_gate_relaxed = 0) and (provider_ingestion = 0) and (canonical_write = 0)`.

## V2 PEAD Calendar-Time Inference Method Contract

- Formation: assign every event-date `signal_bucket_eligible` event, resolve latest event per security/date across all quantiles, then retain Q1/Q5 on authoritative `+1..+60` sessions; no future-completeness filter affects signal assignment.
- Daily portfolio: equal-weight finite raw returns, explicit expected/finite/missing counts, minimum 10 distinct securities per leg, endpoint trimming by counts only, and no internal gaps.
- Primary formula: `R_HL,t = EW(r_i,t | Q5) - EW(r_i,t | Q1)` and `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`.
- Covariance: Newey-West HAC with `maxlags=59` and corrected covariance; no tuning or fallback.
- Robustness: exact 10,000-replication paired stationary block bootstrap, expected block length 60, seed 20260621, same-regression intercept refit, 95% percentile interval, centered-null two-sided p-value, and fail-closed invalid replications; it cannot override the primary result.
- Evidence path: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`, canonical strict JSON, same-directory temporary file, `fsync`, and atomic replace.
- Contract: `V2_PEAD_M1A := TERMINAL_APPROVED iff (calendar_time_primary = 1) and (signal_only_assignment = 1) and (one_security_date_exposure = 1) and (minimum_leg_count = 10) and (HAC_lags = 59) and (quarterly_descriptive_only = 1) and (M1B_executed = 0) and (alpha_claim = 0) and (reviewer_C_terminal_count_recheck = PASS)`.
