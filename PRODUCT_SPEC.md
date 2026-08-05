# Product Specification: Terminal Zero / GodView Certified Portfolio OS

## Active Authority Cut Specification (2026-08-05)

This section supersedes every active product header below.

```text
AUTHORITY_CUT = PIT-ALPHA-AUTHORITY-CUT-1
BASE = e4cf949a895a5f987502328631ebac28af7d154f
C = a92745118aab1a857a0251ce747cab247ba94605
P_DONOR = a36a436e3253a939871299bed12a75eccdad05bb
PRODUCT_ENTRY = dashboard.py / Command Center
DUPLICATE_OPERATOR_SURFACE = DELETED_WITHOUT_COMPATIBILITY
SCORE = 62/100 UNTIL EXACT_FRESH_CLONE_PROOF
F_GATES = MERGE + TAG + MAIN ONLY
NEXT = PIT-SOURCE-AUTHORITY-1
LIVE = CLOSED
```

P must preserve one immutable PIT identity across operated MU, independent shadow MU, and certified cash; bind entry/rotation requests to displayed proposal, active book, certification, event count, and market packets; execute deterministic SELL-before-BUY accounting; persist and certify atomically; reject stale/tampered or buy-only requests; and reopen exact authority in a fresh process. Historical specifications below remain non-active audit history.

---

## Active Product Header (2026-07-29) — R0 Banked, Product Audit Pending

```text
PRODUCT = point-in-time certified portfolio operating system
RELEASED_SUBSTRATE = gv-alpha0-paper-decision-v0.1.0 @ a88ed05
RELEASE_PROOF_TIP = 93e7a55
FUNCTIONAL_STAGE = CERTIFIED_MULTI_SOURCE_CASE_OPERABLE
SHIPPED_PRODUCT_SCORE = 39/100 (unchanged; no alpha)
OBSERVED_COMPARISON_COUNT = 0
ROADMAP_CUSTODY = BANKED_AUDIT_PENDING
PRODUCT_SEQUENCE = SLICES_0_TO_6
EXECUTION_AUTHORIZED_AFTER_AUDIT = SLICES_0_TO_1
ACTIVE_SLICE = GV-MICRO-PORTFOLIO-VERTICAL-0
NEXT_INTEGRITY_GATE = GV-DETERMINISTIC-REPLAY-0
ACTIVE_BRIEF = docs/context/ACTIVE_BRIEF
```

### Canonical product unit

```text
one declared PIT opportunity set
→ complete portfolio including classified cash and abstentions
→ prospective operation
→ deterministic accounting and replay
→ lifecycle-based review
```

### Product layer stack

1. authority and custody;
2. accounting and portfolio book;
3. strategy and Living Thesis;
4. portfolio and capital competition;
5. transition and deterministic execution;
6. replay, attribution, and certification;
7. portfolio/universe scale and bounded challengers.

Detailed authority: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md` and `docs/architecture/top_level_roadmap.md`.

### R0 custody-repair contract

R0 is an internal repository repair, not a product slice. It must bank one checkoutable authority, explicitly supersede stale instructions, replace highest-numeric-phase selection with `docs/context/ACTIVE_BRIEF`, and preserve released FS0 unchanged.

### Slice 0 product contract

Operate one prospective portfolio containing 3–5 declared securities, one reference benchmark, classified cash, one principal thesis, substitute, competing opportunity, and rejection/abstention. The flow must admit content-addressed evidence, exercise permanent identity and one corporate action, compare capital, certify an aim, execute one paper transition/order/fill, reconcile value, persist, reopen, and process one later prospective update.

### Slice 1 product contract

Reconstruct the exact Slice 0 state from frozen manifests and event logs. Corrections append and restate later books without rewriting prior certifications. Replay must exercise corporate-action correction, partial fill, idempotence, valuation pending, and separation of market-risk actions from economic thesis state.

### Parallel Build × Learn contract

Use three mergeable packages: Truth core, Decision vertical, and Product closure. Freeze only the minimum shared identity/event seams before parallel work; freeze detailed fields when the acceptance fixture exercises them. Strategy and quantitative learning remain shadow-only until deterministic admission and prospective evidence. Replay implementation begins early but certification waits for actual Slice 0 events.

### Alpha-0 substrate behavior

The released Alpha-0 package retains its existing launch, sealed review, paper `NO_POSITION`, persistence, certification, and reopen behavior. Its manifest, confinement, deterministic packaging, and hosted parity remain release evidence. Alpha-0 is a banked substrate, not the active product endpoint.

### Exclusions for the first vertical and replay

- provider acquisition and broad historical data loaders;
- empirical copulas, MES, optimizers, or Kelly sizing;
- automated ownership/network propagation;
- adaptive intraday execution;
- tactical production capital;
- shorting, leverage, derivatives, and broker routing;
- live capital or alpha claims.

**Historical PEAD, UOE, Phase 62–80+, and pre-freeze sections below remain audit history only and cannot reopen competing active gates.**

---

## History — V2 PEAD Contracts (not active product gate)

## V2 PEAD Alpha Interpretation Gate Contract (2026-06-24)

- Gate file: `docs/phase_brief/v2-pead-alpha-interpretation-gate.md`.
- Evidence file under interpretation: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.
- Current maximum claim: observed PEAD-style drift shape in a limited single-factor gross Q5-minus-Q1 methodology exercise; explicitly not alpha, not tradable, not PIT, not net, not causal, and not population-valid.
- Path A contract: any future panel must be descriptive evidence only and must carry hard disclaimers for current-vintage EPS, proxy returns, no delisting adjustment, gross returns, and single-factor limits.
- Path B contract: no alpha assertion is interpretable until a future M5 round supplies PIT EPS, delisting-adjusted returns, net costs, and multi-factor evidence.
- Hard stop: no alpha-named dashboard, UI route, card, field, label, or test code until gate approval and 28-commit/main reconciliation.

## V2 PEAD M4A Memory-Bounded Full-Universe Expansion Contract (2026-06-22)

- Implementation: scripts/pead_d2_return_contract.py::build_full_contract and scripts/pead_d2b_event_window_contract.py::build_full_contract.
- D2A full build uses bounded DuckDB execution, one thread, 512 MB memory limit, disk spill, row-grouped Parquet, and the existing atomic manifest protocol.
- D2B full build resolves manifest-governed D1/D2A inputs, lazily validates full D2A, and emits event windows through bounded SQL and the existing atomic manifest protocol.
- D2A return formulas and D2B fixed event-security/session semantics are unchanged.
- Focused M4A tests pass 55/55 and broader PEAD D2/D3/event-study tests pass 79/79; latest targeted non-M4A rerun fails in execution microstructure spooler status/teardown; terminal closure remains blocked pending Reviewer A/B/C capacity and a clean full-suite exit code.
- No provider, PIT/full-universe alpha claim, estimator/UI, ranking/scoring, alert, recommendation, broker/order, or new artifact publication authority is added.

## V2 PEAD Calendar-Time Inference M1B Contract (2026-06-21)

- Implementation paths: `strategies/pead_event_study.py` and `scripts/pead_real_data_validation.py`; focused tests: `tests/test_pead_event_study.py` and `tests/test_pead_real_data_validation.py`.
- Evidence output: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`; SHA256 `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`.
- Protected input: `docs/context/e2e_evidence/pead_real_data_validation_20260620.json` must remain SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- Formation: signal-only event-date quintiles, authoritative `+1..+60` sessions, all-quantile latest-event `(security_id, return_date)` resolution before Q1/Q5 filtering, no older-event fallback, and no-security extreme rows counted as expected missing.
- Regression: `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`, where `R_HL,t = EW(Q5 raw returns) - EW(Q1 raw returns)` and `rf` is not subtracted from the zero-investment spread.
- Inference: Newey-West HAC uses `maxlags=59` and `use_correction=true`; paired stationary block bootstrap is robustness-only with expected block length 60, 10,000 replications, seed 20260621, and max batch size 256.
- Schema: the M1B JSON is closed and validated for exact root/nested fields, constants, date format, sorted/deduplicated arrays, nullability, and unknown-field rejection.
- Integrity: every non-null D2B `return_date` must belong to the authoritative D3 session spine; expected/finite/missing counts and missing rates must reconcile; zero retained sessions require null retained dates.
- Publication: `--calendar-time-m1b` may write only the resolved canonical M1B evidence path, preventing protected/input artifact clobber.
- Authorization boundary: M1B creates no alpha verdict, strategy promotion, ranking/scoring, alerts, recommendations, broker/order path, PIT/full-universe claim, or dashboard action state.

## V2 PEAD Read-Only Evidence Dashboard Contract (2026-06-20)

- Renderer: `views/pead_validation_evidence.py`; composition point: `views/strategy_view.py`; dashboard wiring: `dashboard.py::_render_strategy_page`.
- Evidence input: `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`; expected SHA256: `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- Required framing: `PEAD Validation Evidence — Review Only` plus the locked warning that the artifact is not alpha proof, a signal, ranking, recommendation, alert, or broker/order path.
- Required content: artifact path/hash status; D1/D2B/D3 lineage; 754,920 rows; 12,582 events; 362 issuers; 11,450 eligible; 1,132 ineligible; 2,777 daily HAC gaps with null HAC SE/t-stat; quarterly `ex_post_descriptive_only = true`; four approved limitations.
- Loader contract: capture JSON bytes once, verify SHA256 before parse/render, require evidence-only policy and mandatory fields, and fail closed on any mismatch.
- Forbidden dependencies and effects: provider calls, Parquet reads, PEAD recomputation, data writes, ranking/scoring, alerts, recommendations, and broker/order actions.

## V2 PEAD D3 Benchmark Artifact Publication Contract (2026-06-20)

- Implementation: `scripts/pead_d3_benchmark_artifact.py`; manifest pointer: `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`.
- Active Parquet: `data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`.
- Publication protocol: immutable hash-named Parquet first, then atomic manifest pointer replacement after hash validation.
- Required conversion: `mktrf = Mkt-RF_percent / 100`; `rf = RF_percent / 100`; `benchmark_return = mktrf + rf`.
- Published coverage: 2,810 rows, 2015-01-02 through 2026-03-06, 2,810 / 2,810 D2B sessions, zero missing dates.
- Source lock: Ken French source release `This file was created by using the 202604 CRSP database.` and source ZIP SHA256 `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`.
- Artifact integrity lock: SHA256 `f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`; formula max absolute error `0.0`; duplicate `return_date` count 0.
- This contract does not authorize CAR/BHAR or quintile interpretation, dashboard integration, ranking/scoring, alerts, broker/order paths, provider expansion, full build, staging, or commit.

## V2 PEAD D2B Authoritative Market-Session Contract (2026-06-19)

- `S_raw := unique(D2A.date)`.
- `S_market := {d in KenFrenchDaily.return_date | min(S_raw) <= d <= max(S_raw)}`.
- `S_excluded := S_raw \ S_market`; the current excluded count is 52.
- D2B liquidity selection and `+1..+60` event offsets use `S_market`. D2A return rows remain source observations and are joined only on authoritative dates.
- The D2B manifest records source release, source ZIP SHA256, source member, source/methodology URLs, session count/hash, and the excluded D2A dates.
- D3 validates this source provenance and reconstructs the same session hash before benchmark construction; it does not coerce benchmark dates.
- Corrected artifact: 2,810 sessions, 12,582 events, 754,920 rows, 11,450 eligible handoffs, SHA256 `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`.
- Strategy handoff validates the full D2A input in 100,000-row chunks, enforces exact normalized `(security_id,date)` uniqueness through a bounded DuckDB composite primary key, retains selected-security `{security_id,date,total_return}` columns using a shared categorical identity dtype, and does not full-copy/sort D2A.

## V2 PEAD D3 Benchmark Artifact Builder Contract (2026-06-19)

- Implementation: `scripts/pead_d3_benchmark_artifact.py`; tests: `tests/test_pead_d3_benchmark_artifact.py`.
- Source: Ken French daily Fama/French 3 Factors ZIP from the official Data Library.
- Required conversion: `mktrf = Mkt-RF_percent / 100`; `rf = RF_percent / 100`; `benchmark_return = mktrf + rf`.
- Publication contract exists and is tested: immutable hash-named Parquet first, then atomic manifest pointer replacement after hash validation.
- The historical pre-repair build was blocked by 52 non-session dates. Active D2B coverage is now 2,810 / 2,810; publication remains unperformed pending separate approval.
- D3 must not fill/drop missing benchmark sessions or reinterpret CAR/BHAR. D3 artifact publication is the next separate decision.
- Strategy summary semantics: complete asset windows may retain raw `cumulative_total_return` when benchmark coverage is missing, but `cumulative_benchmark_return`, CAR, BHAR, `window_complete`, and `eligible_for_analysis` remain blocked.

## V2 PEAD D2B Fixed Event-Security Window Contract (2026-06-19)

- D2B selects one fixed security per event from the 20 global market sessions strictly before `event_date` using finite daily `dollar_volume` only; a candidate requires at least 15 observations.
- Selection order is trailing arithmetic-mean dollar volume descending, finite observation count descending, normalized `iid` ascending, then `security_id` ascending. There is no `IID01` preference, fallback, or post-event switch.
- Event day `+1` is the first global D2A market session strictly after the event; every event retains an exact `+1..+60` skeleton. Missing rows and non-finite returns remain missing, with no return/delisting imputation or delisting label.
- `handoff_eligible` is true only when one selected security has all 60 global dates and all 60 finite returns. The canonical strategy adapter passes only eligible D2B events, unique D2A `(security_id,date,total_return)` rows, and the identical global session spine to `strategies/pead_event_study.py`; it implements no second window algorithm.
- Publication is immutable hash-named Parquet followed by an atomic manifest commit pointer, with stable hash-validated input byte snapshots and `BaseException` pre-commit cleanup. Implementation: `scripts/pead_d2b_event_window_contract.py`.
- Current bounded sample: 12,582 events, 362 issuers, 754,920 rows, 12,568 selected, 14 without an eligible security, 522 short windows, 7,179 missing/non-finite windows, and 4,867 handoff-eligible events. Output SHA256: `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`.
- D2B is a completed bounded Data slice, not PEAD phase-end. Final Reviewer A/B recheck remains pending; provider fetch, benchmark implementation, CAR/alpha interpretation, ranking, alerts, broker paths, full build, staging, and commit are not authorized.

## V2 PEAD D2A Security-Level Return Contract (2026-06-18)

- `security_id := gvkey + "-" + iid`; return rows are unique by `(security_id, date)`.
- `TR_level_t := prccd_t * trfd_t / ajexdi_t` when all inputs are finite and positive.
- `total_return_t := TR_level_t / TR_level_{t-1} - 1`, with `t-1` grouped by `(gvkey, iid)` only.
- Fallback level: `price_level_t := prccd_t / ajexdi_t`; when either total-return level is unavailable, `total_return_t := price_level_t / price_level_{t-1} - 1` within the same security and `return_type := price_return_fallback`.
- Date gaps above five calendar days and absolute returns above `5.0` are invalidated. The first row of every security series is null.
- Exact cross-source overlaps may prefer `prices_daily_compustat`; duplicate keys within one source or in final output fail closed.
- `dollar_volume` is a daily raw field, not ADV. The prior `trfd_t / trfd_{t-1} - 1` methodology is superseded.
- Publication uses an immutable hash-named Parquet and a stable manifest as the sole atomic commit pointer; readers must resolve `manifest.parquet_file` instead of assuming a fixed Parquet filename.
- `--event-window-only` is disabled. D2B owns fixed event-level IID selection and `+60` market-session extraction.
- `--build` is disabled in D2A, and sample publication requires exactly 500 GVKEYs.

## V2 PEAD D1 Repair Contract (2026-06-18)

- `adj_eps := numeric(epspxq)`; `ajexq` is not divided; the `adj_eps` name is compatibility-only.
- Identity ordering: deduplicate `(gvkey, rdq)` before exact t-4 lag and rolling transforms.
- `sue_price_scaled := (adj_eps_t - adj_eps_t_minus_4) / abs(prccq_lag1)`.
- `sue_price_scaled_clipped := clip_within_rdq(sue_price_scaled, mean_rdq - 5 * std_rdq, mean_rdq + 5 * std_rdq)`; raw SUE is retained.
- With `cshoq_lag1` in millions, `liquidity_pass := prccq_lag1 * cshoq_lag1 > 50`; this flag is independent of `valid_sue`.
- Parquet and manifest are promoted with temp-to-replace writes. Current artifact SHA256: `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Quality gate: fail if raw `abs(sue_price_scaled) > 5` reaches 0.5% or more of valid rows; current artifact is 441 / 233,586 = 0.1888%.
- Empty processed-output paths fail before Parquet or manifest promotion; current-vintage Compustat EPS/restatement-hindsight limitation is recorded in the manifest.
- D2, public benchmark acquisition, and provider replacement are not part of this contract.

## V2 PEAD Strategy Contract Notice (2026-06-18)

- `pead_event_schema = {event_id, issuer_id, security_id, event_date, sue, is_primary_security}`.
- `pead_return_schema = {security_id, date, total_return, optional_explicit_benchmark_return}` with unique `(security_id, date)` rows supplied after upstream primary-security selection.
- `market_sessions` is required; `event_day_1 = first_market_session_strictly_after_event_date`; default `event_window = [+1,+60]`.
- `window_complete = expected_sessions == valid_asset_returns == 60` and, when configured, `valid_benchmark_returns == 60`.
- `CAR = sum(total_return_d - benchmark_return_d)` and `BHAR = product(1 + total_return_d) - product(1 + benchmark_return_d)` only when benchmark data is explicit.
- `high_minus_low_t = mean(cohort_Q5_minus_Q1) / HAC_SE(mean)`; this is synthetic-contract capability, not alpha evidence.
- Implementation: `strategies/pead_event_study.py`; tests: `tests/test_pead_event_study.py`.
- `strategy_saw_rerun_status = PASS`; `strategy_handoff_ready = true` only for corrected D1/D2 rows that satisfy the schema contract.

Status: Canonical product/spec surface for Phase 65 Portfolio Universe Construction Fix
Date: 2026-05-10
Owner: PM / Architecture Office
Scope: docs and architecture only

## Current Phase 65 Notices

V2-D0.4C Local Read-Only Permission Probe Approval (2026-06-03):

- `d0_4c_round = ROUND-20260603-V2-D0-4C-LOCAL-READ-ONLY-PERMISSION-PROBE-APPROVAL`.
- `d0_4c_status = PASS_DOCS_ONLY_APPROVAL`.
- `future_probe_approval = LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVED_FOR_LOCAL_HUMAN_RUN`.
- `execution_in_d0_4c = false`.
- `future_probe_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `row_state = probe_approved_not_executed AND not_formally_approved AND approval_ref == null`.
- `allowed_future_output = exact_five_row_accessible_true_false_or_redacted_error_only`.
- `next_packet = V2_D0_4D_LOCAL_HUMAN_PROBE_EXECUTION_PACKET`.
- No credential read, `secret.txt` read, Codex/subagent login, WRDS execution in D0.4C, discovery helper, schema discovery, row count, sample row, snapshot, data output, runtime/dashboard/scoring/broker write, formal approval_ref change, SafeBoot, or BootReady is authorized.

V2-D0.4B WRDS Local Auth Method Confirmed (2026-06-03):

- `round_id = ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED`.
- `scope_id = V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION`.
- `status_fields = {WRDS_LOCAL_AUTH_USER_ATTESTED_AVAILABLE, FORMAL_PERMISSION_TRUTH_NOT_CLOSED, ALLOW_LOCAL_READ_ONLY_PERMISSION_PROBE_PLAN_ONLY, BLOCK_PROBE_EXECUTION_UNTIL_SEPARATE_APPROVAL, BLOCK_DATA_OUTPUT_RUNTIME_SNAPSHOTS}`.
- `required_decision_language = "WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed."`
- `local_auth_method = user_attested_local_auth_available`.
- `actual_login_verified_by_agent = false`.
- `credentials = local_only_do_not_read_do_not_quote_do_not_commit`.
- `secret_txt = do_not_read_do_not_quote_do_not_use`.
- `formal_approval_ref = null`.
- `permission_truth = not_closed`.
- `wrds_execution = governance_blocked_until_probe_approval`.
- `s_and_p_capital_iq_pro = deferred_fallback`.
- For every row in `{crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`: `probe_plan_status = probe_plan_pending`, `approval_status = not_approved`, and `approval_ref = null`.
- `probe_execution_allowed = false` until separate explicit approval.
- No secret/credential read, WRDS/provider login, SSH, Python WRDS, SAS, SQL, library/table/schema discovery, row count, sample row, snapshot, data output, runtime/dashboard/scoring/broker write, approval_ref fabrication, or row approval is authorized.

V2-D0.2 WRDS Entitlement Evidence Request - No Credential Use (2026-06-03):

- `evidence_request_round = ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST`.
- `evidence_request_status = REQUEST_PREPARED_EVIDENCE_MISSING`.
- `evidence_request_artifacts = {docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.md, docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.json}`.
- `requested_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `all_rows_pending = evidence_status == evidence_missing AND permission_status == pending AND approval_ref == null`.
- `allowed_next_action = send_non_secret_evidence_request_to_authorized_institutional_contact`.
- `approval_valid = false` until dated attributable non-secret entitlement evidence and exact approval_ref values exist.
- No WRDS/provider access, credential use, probe execution, schema/table discovery, row count, snapshot, data output, dashboard/runtime, scoring/ranking, alert, broker path, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.

V2-D0.1 Authorization Intent Evidence Missing (2026-06-03):

- `authorization_intent_round = ROUND-20260603-V2-D0-1-AUTHORIZATION-INTENT`.
- `authorization_packet_status = INTENT_RECORDED_EVIDENCE_MISSING`.
- `authorization_packet_is_final_approval = false`.
- `v2_d0_1_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- For every row: `evidence_status = evidence_missing`, `permission_status = pending`, and `approval_ref = null`.
- `secret.txt` is local secret material and is not non-secret entitlement evidence.
- `approval_valid = false` until qualifying non-secret entitlement evidence and exact row/table approval_ref text exist.
- No WRDS/provider access, credential use, probe execution, snapshot, data write, dashboard/runtime, scoring/ranking, alert, broker path, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.

V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping (2026-06-02):

- `TODO_MATRIX_001 = RESOLVED_BY_OFFLINE_PERMISSION_TRUTH_METADATA`.
- Artifact: `v2_discovery/data_lab/permission_truth.py`.
- Tests: `tests/test_v2_wrds_permission_truth_scope.py`, `tests/test_v2_wrds_permission_matrix.py`, `tests/test_v2_snapshot_manifest_contract.py`, `tests/test_v2_data_lab_no_v1_writes.py`; focused run PASS, 51 passed; compileall `v2_discovery\data_lab` plus permission-truth test PASS.
- `v2_d0_1_permission_truth_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `default_permission_status = pending`.
- `approved_status_valid = row_table_approval_ref_present AND allowed_uses == ["provenance_contract"]`.
- `pead_v2_001_starter_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq}`.
- `ibes_det_epsus_v2_d0_1_status = pending`; `ibes_det_epsus_pead_v2_001_starter_scope = not_requested`.
- This does not authorize WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, legacy cleanup, public/main closure, or V2 validity/C3 lock claims.

V2-D0.1 Scope and Clean-Room Runtime Decision (2026-06-02):

- `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md` records the scope/runtime clarification.
- `v2_d0_1_entitlement_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `pead_v2_001_compustat_starter_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq}`.
- `ibes.det_epsus.v2_d0_1_entitlement_status = pending once requested`.
- `ibes.det_epsus.pead_v2_001_starter_scope = not_requested`.
- `cleanroom_runtime_schema_registry_default = excluded`.
- `TODO-PEAD-DECISION-001 = RESOLVED`; `TODO-CLEANROOM-RUNTIME-001 = RESOLVED`.
- No provider access, probe, credential use, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup is authorized.

V2-D0.1 Expert 1-6 Follow-Up Reconciliation (2026-06-02):

- `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md` is the advisory follow-up artifact.
- Agreement/confidence levels: Data/WRDS `AGREE_HIGH 8.5/10`; Backend/Data `AGREE_HIGH 9/10 PATCH_RESOLVED_LOCAL`; Architecture/Governance `AGREE_HIGH 8.5/10`; Quant Research `PARTIAL_AGREE_HIGH 7.5/10`; Research Validity `AGREE_HIGH 8.5/10`; Security/Ops `AGREE_HIGH 9/10`.
- `v2_d0_1_default_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `pead_starter_conflict = ibes_analyst_surprise_primary_signal vs compustat_rdq_four_row_starter`.
- `v2_d0_1_permission_truth_artifact_valid = approved_rows_allowed_uses == ["provenance_contract"]`; the V2-D0 default matrix output is not itself an approved V2-D0.1 artifact.
- `research_valid_pead = false` until `C3_LOCK_PEAD_V2_001_v1` and fail-closed statistical gates exist.
- No WRDS/provider access, probe, credential use, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup is authorized.

V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates (2026-06-02):

- Expert 1-6 agreement ratings are captured as `AGREE_HIGH`; exact numeric source values were not present in the handoff.
- `V2-D0.1_WRDS_PERMISSION_TRUTH_AUTHORIZATION` is entitlement-only and can collect account/license owner, account scope, exact library.table permissions, license/access constraints, date/as-of coverage, and approval_ref text.
- Backend/Data row-level validator is `PATCH_RESOLVED` after focused tests; this does not authorize a WRDS connection, query, row output, or snapshot.
- Security approval text is required and legacy WRDS helper/quarantine risk remains open until a separate audit or retirement decision.
- `PEAD_V2_001_BOUNDARY_PACKET` is conditional only after WRDS/PIT authority.
- No V2 alpha is currently `research_valid`; `V2_ALPHA_VALIDITY_PACKET` template must exist before any V2 alpha validity assertion.
- No WRDS/provider access, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, or BootReady is authorized.

V2-D0 Multi-Expert Reconciliation Gate (2026-06-02):

- `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md` records Expert A/B/C reconciliation.
- `validate_wrds_permission_probe_contract(...)` now rejects root-key drift, credential/connection/output-looking extras, changed `next_allowed_action`, changed `denied_actions`, changed `code_ref`, and widened dataset row shapes.
- `snapshot_manifest._normalize_storage_uri(...)` now matches the JSON Schema prefix contract and rejects bare `data/runtime_cache/v2_data_lab`.
- Focused V2-D0 tests pass with 20 tests after hardening.
- No WRDS access, read-only probe, snapshot generation, data output, dashboard reader, SQLite, SafeBoot, or BootReady claim is authorized.

V2-D0 WRDS Permission + Snapshot Provenance Contract (2026-06-01):

- `v2_discovery/data_lab/permission_matrix.py` builds a contract-only WRDS permission matrix with root flags `provider_access_allowed=false`, `snapshot_generation_allowed=false`, `data_output_allowed=false`, and `v1_canonical_write_allowed=false`.
- `v2_discovery/data_lab/wrds_probe.py` builds an offline probe contract and records `wrds_connection_attempted=false`.
- `v2_discovery/data_lab/snapshot_manifest.py` builds a contract-only snapshot manifest with required PIT flags and rejects planned storage under `data/processed/`, `data/registry/`, `runtime/boot_status_current.json`, and `docs/context/boot_status_current.json`.
- `v2_discovery/data_lab/schema_registry.py` validates the contracts against `contracts/data_snapshot/wrds_permission_matrix.schema.json` and `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`.
- Focused tests prove schema validity, false root flags, release-date/PIT fields, blocked V1 paths, no provider/runtime surfaces, and no V1 artifact writes.
- No WRDS access, snapshot generation, provider ingestion, dashboard integration, ranking/scoring, recommendations, alerts, broker/order paths, SQLite storage, SafeBoot, or BootReady claim is authorized.

V2 Alpha Factory Immediate Todo Directive (2026-06-01):

- `docs/architecture/v2_alpha_factory_immediate_todo_directive_20260601.md` records a docs-only idea/directive.
- First technical planning target is a WRDS permission/PIT/provenance layer with permission matrix, snapshot manifest, schema registry, row-count/hash policy, extraction log, and rollback/removal rule.
- PEAD variants, corporate-actions variants, meta-labeling survival, and Orbis/BvD network shock follow only after the data/provenance foundation is approved.
- `sqlite_store.py` is not approved; SQLite remains forbidden without explicit approval, so registry storage must default to repo-approved Parquet/DuckDB-compatible design unless policy changes.
- No provider access, snapshot generation, candidate ranking/scoring, promotion, live trading, broker behavior, alerts, recommendations, autonomous allocation, or BootReady claim is authorized.

Boot Status Path Contract + Governance Scanner Integration (2026-05-26):

- `core.boot_status.DEFAULT_BOOT_STATUS_PATH` and `BOOT_STATUS_CURRENT_PATH` point to `runtime/boot_status_current.json`.
- `BOOT_STATUS_CONTEXT_SNAPSHOT_PATH` points to `docs/context/boot_status_current.json` only as a noncanonical snapshot path; loaders do not use it as a safe-boot fallback.
- `scripts/boot_preflight.py --repo-root ...` imports and runs `run_governance_preflight(...)`, records `checks["governance"]`, and blocks on governance FAIL.
- Strict preflight may write boot status only with `--write-status`, only after PASS, and only to `runtime/boot_status_current.json`.
- Data-readiness, dashboard runtime smoke, replay/optimizer certification, and clean GitHub safe-boot proof remain separate gates before boot-ready can be claimed.

Research Validity Runner v0 (2026-05-26):

- `research.backtest_runner.run_research_backtest(...)` is the v0 canonical evidence wrapper over `core.engine.run_simulation(...)`.
- `research.status.ResearchStatus` locks the status vocabulary: `diagnostic_only`, `exploratory`, `research_valid`, `candidate_ready`, `blocked`.
- `research.adapters.rule100_replay_adapter` filters Rule100 daily replay rows, excludes CASH, ignores replay equity/performance columns, and emits runner-ready target weights while preserving diagnostic-only status.
- V0 evidence requires strict missing-return behavior, declared costs, required benchmarks, PIT proof, input signatures, leakage checks, metrics, and a verdict packet.
- V0 evidence output rejects unsafe `run_id` values, confines the run directory under cartridge `output_dir`, writes JSON/CSV artifacts with temp-to-`os.replace`, and emits `evidence_packet.json` last.
- No provider ingestion, canonical market-data write, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion is authorized.

Portfolio Replay Role Contract (2026-05-15):

- `strategies.strategy_replay.REPLAY_COLUMNS`, `REPLAY_CONTEXT_COLUMNS`, and `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` carry `context_role` / `row_role`.
- `context_role` separates `current_holding`, `historical_context`, `flat_in_replay`, `cash`, and `unavailable` semantics.
- `row_role` separates `daily_portfolio`, `event_annotation`, and `buy_sell_decision` artifact rows.
- `dashboard.py::_normalize_dashboard_context_frame(...)` delegates to `strategies.strategy_replay.normalize_context_frame_for_replay(...)`.
- Older selected-method artifacts without role columns hydrate default roles on read; unrelated schema mismatches still fail closed.
- Diagnostics are generated from `DashboardReplayContext` and bind run/source/method/cache identity.
- No provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Dashboard Replay Aux Weight Semantics + Stacked Timeline (2026-05-15):

- `strategies.strategy_replay._normalize_context_frame(...)` emits replay-derived `target_weight` for event/decision context rows by joining normalized `(date, ticker)` back to replay output.
- `dashboard.py` aligns saved-artifact and transitional event/decision rows with `_align_context_weights_to_replay(...)`; `audit_weight` preserves the original auxiliary `weight` value.
- `dashboard.py::_render_replay_timeline_chart(...)` renders a stacked step-area allocation view from replay `target_weight`; `CASH` is muted and display-only.
- `dashboard.py::_render_strategy_replay_section(...)` fails soft when partial saved/transitional rows lack latest-snapshot display fields or event `action` fields.
- Tests cover backend aux alignment, dashboard aux alignment, MU context-only zero replay weight with preserved audit weight, stacked timeline source guards, and partial-schema render regressions.
- No provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Replay Selected Price Loading + MU/SNDK Eligibility Trace (2026-05-15):

- `load_batched_pit_replay_data(..., selected_permnos=...)` records full-window PIT membership metadata while limiting price/return columns to selected PIT members.
- Dashboard selected-method replay passes signed replay assets as numeric permnos into the batched loader and still filters the returned matrix to signed assets before backend replay execution.
- `trace_thesis_ticker_eligibility(...)` is the separate MU/SNDK diagnostic surface for pinned thesis universe, ticker-map, `r3000_pit`, local price/return, Rule100 history, current-hold/sizing, and failed gate truth.
- No watchlist-only replay, provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Max Replay Timeline Sampling Fix (2026-05-15):

- `dashboard.py::_sample_replay_timeline_from_daily(...)` uses `pd.to_datetime(weekly_index, errors="coerce").dropna().dt.normalize()` for weekly grouped keep-dates.
- The sampler keeps the last replay date per ISO year/week plus the final daily replay date.
- `tests.test_dash_2_portfolio_ytd::test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay` covers a max-window branch with more than 160 daily replay dates.
- Weekly timeline sampling remains display-only and cannot feed Portfolio Performance or replace the daily replay source.

Portfolio Single-Source Replay Page (2026-05-14):

- `/portfolio-and-allocation` now coordinates one daily `DashboardReplayContext` for Portfolio Performance, allocation snapshot, Strategy Replay Timeline, ENTER/EXIT Events, Latest Buys/Sells, and Buy/Sell Decision Log.
- `views.optimizer_view.render_optimizer_view(..., show_allocation_outputs=False)` leaves the top optimizer area as controls-only; the visible allocation evidence is `Allocation (Latest Daily Replay Snapshot)`.
- Portfolio Performance rejects non-daily replay and no longer falls back to optimizer weights or local/live/equal-weight price paths for replay-facing output.
- Strategy Replay Timeline uses display sampling only after daily replay rows exist.
- Latest Buys/Sells is a filtered view of `bundle.decision_rows`; no separate latest trade source is allowed in the render path.
- Focused source-guard tests cover the no-second-source render path; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Saved Artifact Single-Source Aux Surface Fix (2026-05-14):

- `dashboard.py::_dashboard_context_from_artifact_read(...)` preserves saved artifact `event_rows` and `decision_rows` exactly, including empty DataFrames.
- `tests.test_dash_2_portfolio_ytd::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows` covers daily saved rows with empty saved aux rows and non-empty fallback frames.
- `source_mode="saved_artifact"` now means replay rows, latest snapshot, ENTER/EXIT rows, and Buy/Sell rows are all artifact-owned.
- Focused compile and the focused frontend suite pass; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Backend Replay Reader Identity Hardening (2026-05-14):

- `strategies.strategy_replay._validate_manifest_bundle_fields(...)` rejects blank or non-string top-level manifest `run_id`, `source_id`, and `method_id`.
- `read_selected_method_replay_artifact(...)` performs that manifest bundle validation before optional expected-ID matching, parquet reads, or bundle reconstruction.
- `tests.test_strategy_replay_artifact` covers matching blank manifest+parquet identity with no expected `run_id` / `source_id` supplied by the caller.
- Focused replay artifact/strategy/coverage tests pass; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Portfolio Market-Data Freshness Endpoint Cache (2026-05-14):

- `core.data_orchestrator.PriceEndpointFreshness` is the reusable endpoint snapshot for a loaded price matrix.
- `core.data_orchestrator.build_price_endpoint_freshness(...)` computes per-column endpoints and the matrix required endpoint in one chunked pass.
- `dashboard.py` caches the endpoint snapshot by unified source file signatures, loader arguments, and matrix shape before passing it to portfolio YTD, optimizer rendering, and universe construction.
- `views.optimizer_view` and `strategies.portfolio_universe` accept the snapshot and avoid repeated full-matrix scans on render paths.
- Focused regressions prove stale assets still fail closed/drop while callers reuse supplied endpoint snapshots.

Portfolio Market-Data Freshness Fail-Closed Fix (2026-05-14):

- `core.data_orchestrator.price_latest_dates_by_column(...)`, `price_frame_latest_date(...)`, and `filter_price_frame_to_fresh_columns(...)` define the per-column endpoint freshness contract for display price frames.
- `core.data_orchestrator.price_column_latest_date(...)` and `price_endpoint_is_fresh(..., max_staleness_days=0)` define the shared endpoint/tolerance predicate; strict freshness is the default, and callers must pass tolerance explicitly.
- `core.data_orchestrator.build_benchmark_equity_from_prices(...)` drops stale benchmark columns that cannot be live-overlaid and reports a shared benchmark endpoint for remaining curves.
- `dashboard.py::_weighted_equity_curve(...)` accepts a required endpoint and returns unavailable when any nonzero weighted local leg is stale.
- `core.data_orchestrator.refresh_selected_prices_with_live_overlay(...)` accepts `required_latest`; `views.optimizer_view._prepare_selected_prices(...)` supplies the global price endpoint so stale selected assets are dropped instead of captioned as fresh.
- Selected optimizer overlays must pass the shared endpoint freshness filter after stitching; unresolved stale selected assets are dropped instead of treated as current evidence.
- `views.optimizer_view._order_assets_by_trailing_one_year_return(...)` demotes assets whose own endpoint is stale against the global endpoint.
- `strategies.portfolio_universe.build_optimizer_universe(...)` imports the shared core endpoint helpers and excludes assets whose price endpoint is older than `OptimizerUniversePolicy.max_endpoint_staleness_days`, even when history observation count is sufficient.
- Focused stale-data regressions and affected replay/dashboard tests pass; no provider ingestion, canonical write, broker behavior, alerts, ranking, scoring, recommendation, or promotion claim is authorized.

Dashboard Backend Bundle Integration Verification (2026-05-14):

- `dashboard.py::_build_dashboard_strategy_replay_context(...)` consumes `strategies.strategy_replay.build_selected_method_replay(...)`.
- The dashboard backend-bundle call uses `_dashboard_input_loader(...)` for per-date PIT inputs with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- `DashboardReplayContext` carries replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log rows, and the latest replay weights used by Portfolio Performance.
- The current consumer is a `transitional_build` path, not the saved artifact-reader path.
- Full pytest and runtime smoke passed for this verification; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Replay Coverage Contract Audit Fix (2026-05-14):

- `strategies.strategy_replay._build_run_metadata(...)` records contiguous replay coverage segments in `date_window["coverage_segments"]`.
- `strategies.strategy_replay._build_replay_from_input_loader(...)` preserves specific unavailable causes as `input_unavailable:<coverage_reason>` and batches uncovered-date cash-closed rows before attaching performance.
- `strategies.strategy_replay._build_replay_from_input_loader(...)` preserves row-heavy explicit-member unavailable windows under the daily-scale budget.
- `strategies.strategy_replay._attach_replay_performance(...)` aligns allocation-date weights to next tradable returns and uses a small-frame lookup for tiny PIT frames while preserving the vectorized path for larger replay frames.
- `strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics(...)` can return the closed-form inverse-volatility target without SLSQP when that target already satisfies max-weight bounds.
- `scripts.build_context_packet.build_context_packet(...)` selects complete New Context Packets from current truth surfaces before older same-phase handovers.
- The replay coverage/performance tests and full pytest suite pass after the audit fix.

Data/PIT Strategy Replay Hardening (2026-05-13):

- `core.data_orchestrator.build_strategy_replay_cache_signature(...)` has `universe_mode="r3000_pit"` as the default and rejects any other mode.
- `core.data_orchestrator.load_strategy_replay_inputs(...)` loads local parquet matrices with `asof_date` and clamps rows to `date <= as_of_date`.
- `core.data_orchestrator.write_strategy_replay_artifact_atomic(...)` rejects repo-local `data/` writes outside `data/runtime_cache/strategy_replay`.
- `dashboard.py::_render_strategy_replay_section()` loads one `StrategyReplayInputs` object per replay date and calls `strategies.strategy_replay.build_strategy_replay(..., prices=replay_inputs, as_of_range=None)`.
- Input artifacts contain price/return matrices; target-weight output is generated by `build_strategy_replay(...)` and displayed only.

Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay (2026-05-13):

- `strategies.rule100_softmax.Rule100SoftmaxConfig()` remains the frozen audit default with `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- `strategies.rule100_softmax.rule100_config_from_max_weight(max_weight)` is the dynamic visible allocation helper and sets `gross_budget_per_name=max_weight`, `max_single_name_weight=max_weight`, and `gross_budget_cap=1.0`.
- `views.optimizer_view.render_optimizer_view(...)` passes the optimizer `Max weight` control into the direct `Rule of 100` allocation path.
- `strategies.strategy_replay.build_strategy_replay(...)` uses the same dynamic Rule100 config for `OptimizationMethod.RULE_OF_100`.
- `core.data_orchestrator.build_benchmark_equity_from_prices(...)` detects stale/missing benchmark columns per ticker and calls live overlay only for those tickers; columns that cannot be refreshed are not forward-filled into fresh benchmark curves.
- `dashboard.py::_build_benchmark_equity(...)` delegates to that helper and labels blended benchmark sources as `local+live_overlay`.

G8.1A Discovery Drift Correction (2026-05-10):

- Discovery intake items now require origin provenance fields before any later scout work can consume them.
- Current seed labels are `MU = USER_SEEDED`; `DELL`, `INTC`, `AMD`, and `ALB = USER_SEEDED + THEME_ADJACENT`; `LRCX = USER_SEEDED + SUPPLY_CHAIN_ADJACENT`.
- `SYSTEM_SCOUTED` requires a governed scout path and is not used by the current six-name queue.
- `LOCAL_FACTOR_SCOUT` is defined for the later pipeline-first 4-factor scout baseline, but G8.1A does not inspect or wrap factor artifacts.
- Intake origin metadata is not candidate-card promotion, thesis validation, actionability, ranking, scoring, or recommendation authority.

G8.2 System-Scouted Candidate Card (2026-05-10):

- G8.2 converts the sole G8.1B `LOCAL_FACTOR_SCOUT` output, `MSFT`, into one static candidate-card-only research object.
- Required provenance fields are `discovery_origin = LOCAL_FACTOR_SCOUT`, `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`, `source_intake_item_id`, `source_intake_manifest_uri`, and `candidate_card_manifest_uri`.
- The card may carry light official/public source pointers, missing evidence, provider gaps, thesis breakers, and forbidden jumps only.
- The card must not emit or imply factor score, rank, validation, actionability, buy/sell/hold, buying range, alert, broker action, provider ingestion, or dashboard runtime behavior.
- Existing dashboard `MSFT` rows are legacy ticker-list output and are not card-reader integration.

Portfolio Universe Construction Fix (2026-05-10):

- `strategies/portfolio_universe.py` owns optimizer eligibility, ticker-map readiness, local price-history readiness, and max-weight feasibility diagnostics.
- `dashboard.py` must pass `universe.included_permnos`; it must not pass display-sorted `df_scan["Ticker"][:20]`.
- `views/optimizer_view.py` renders Universe Audit and Why This Allocation diagnostics and labels max-Sharpe optimization as thesis-neutral.
- Generic `WATCH` is research-only until a later approved portfolio-ready watch state exists.
- MU hard floors, Black-Litterman, conviction mode, thesis anchors, manual overrides, scanner rewrites, provider ingestion, alerts, broker paths, and new objectives are blocked.

Optimizer Core Structured Diagnostics (2026-05-11):

- `strategies/optimizer_diagnostics.py` owns optimizer feasibility, bound, constraint, solver, fallback, and severity report objects.
- `strategies/optimizer.py` exposes diagnostic-returning optimizer methods while preserving existing weight-returning methods.
- `views/optimizer_view.py` surfaces optimization status, feasibility status, active constraints, assets at max cap, assets at lower bound, equal-weight-forced status, residuals, and fallback labels.
- This is diagnostics-only; it does not approve lower-bound allocation policy, MU conviction, WATCH investability expansion, Black-Litterman, new objectives, scanner rules, manual overrides, provider ingestion, alerts, broker behavior, or replay behavior.

Portfolio Data Boundary Refactor (2026-05-11):

- `core/data_orchestrator.py` owns portfolio display-refresh close-price extraction, yfinance/provider-port calls, local TRI overlay scaling, selected-price stitching, and strategy metrics parsing from `data/backtest_results.json`.
- `views/optimizer_view.py` consumes those helpers and renders only controls, diagnostics, allocation explanations, charts, and tables.
- The overlay remains display-freshness only: no canonical market-data write, provider ingestion, alert, broker call, rank, score, recommendation, or candidate-card dashboard merge is authorized.

Portfolio Optimizer View Test and Performance Hardening (2026-05-11):

- `tests/test_optimizer_view.py` uses Streamlit `AppTest` to exercise optimizer view rendering, mean-variance selection, and sector-cap controls.
- `tests/test_optimizer_core_policy.py` now validates UI-derived max-weight/risk-free-rate bounds through the real SLSQP optimizer and validates sector caps as post-solver constraints.
- `core/data_orchestrator.py` owns the display-only Parquet cache for recent close-price overlays and schedules background refresh on cold/stale cache misses.
- `views/optimizer_view.py` caches optimizer runs by selected price frame and user parameters without changing the approved optimizer objective.
- No canonical provider ingestion, lower-bound allocation policy, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker path, score, rank, or candidate-card dashboard merge is authorized.

Portfolio Lifecycle Replay Churn + Weight Policy (2026-05-12):

- `scripts/pit_lifecycle_replay.py` owns replay entry sizing, lifecycle factor confirmation, entry/exit confirmation, minimum-hold, hard-exit, and cooldown state.
- `replay_entry_weight()` returns `0.10` by default from `DEFAULT_MAX_POSITIONS = 10`.
- `lifecycle_factor_confirmation(...)` requires at least 3 present and positive values across `z_demand`, `z_moat`, `z_inventory_quality_proxy`, and `z_discipline_cond`.
- ENTER needs raw PIT eligibility plus 3 consecutive confirmed days and no active 10-day post-exit cooldown.
- EXIT needs either `dist_sma20 > 0.20` or a raw exit after 20 holding days with 2 consecutive exit confirmations.
- This is replay/current-hold state discipline only; it does not approve the rejected Phase 54 Rule-of-100 sleeve, ranking, scoring, optimizer objective changes, alerts, broker behavior, provider ingestion, or live trading.

Rule of 100 Method Label (2026-05-12):

- `strategies.optimizer.OptimizationMethod.RULE_OF_100` exposes the exact dropdown label `Rule of 100`.
- `views.optimizer_view.render_optimizer_view(...)` routes `Rule of 100` directly to Rule100 softmax v1 target weights plus residual cash and does not call the cached optimizer run.
- Empty or all-ineligible softmax state under `Rule of 100` renders cash-only session state instead of stale lifecycle weights.
- This is a UI label for the concrete lifecycle policy, not a new optimizer objective, ranking model, alert, broker path, or live recommendation.

Rule100 Softmax v1 Audit (2026-05-12):
- `strategies/rule100_softmax.py` owns the pure softmax sizing helpers and the Kelly comparator shim.
- `scripts/rule100_softmax_v1_audit.py` owns the shared PIT replay/audit harness and writes versioned audit artifacts.
- Softmax v1 is the primary sizing path for both audit artifacts and the explicit `Rule of 100` UI method; Kelly is comparator-only on the same frame.
- Current live target is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%.
- `data/processed/rule100_softmax_v1_history.csv` is the historical v1 target-weight overlay; it keeps v0 lifecycle event weights separate from `softmax_v1_target_weight`.
- `dashboard.py` Position Lifecycle Replay transaction log must label the original ledger weight as `Event Weight` and the overlay as `Softmax v1 Target`.
- This does not change the lifecycle replay log or any broker/alert/ranking/scoring behavior.

Rule100 Softmax v1.1 Research Contract (2026-05-12):

- `strategies/rule100_softmax_v1_1.py` owns the research-only v1.1 scoring helper; `scripts/rule100_softmax_v1_1_audit.py` owns the audit artifact writer.
- The active artifact set is `data/processed/rule100_softmax_v1_1_comparison.csv` and `data/processed/rule100_softmax_v1_1_summary.json`; `rule100_softmax_v1_1_history.csv` is not an active v1.1 artifact.
- `factor_present_count` and `factor_positive_count` count approved groups only: demand, inventory/supply, moat/pricing, and capital discipline.
- Factor strength uses group percentile ranks and neutral missing-group shrinkage: `mean_available_rank * coverage + 0.50 * (1 - coverage)`.
- `tests/test_policy_target_timeline_apptest.py` must exercise `AppTest.from_file("dashboard.py")`, not copied mini-apps, for the Policy Target Timeline regression.

Dashboard Architecture Safety Slice (2026-05-11):

- `utils/process.py` owns `pid_is_running`, including the Windows `OpenProcess` / `GetExitCodeProcess` liveness probe.
- `dashboard.py`, `data/updater.py`, `scripts/parameter_sweep.py`, `scripts/release_controller.py`, and `backtests/optimize_phase16_parameters.py` must delegate process liveness to that shared helper or compatibility wrappers over it.
- `dashboard.py::spawn_backtest` must fail closed when an existing PID file is live; it must not terminate an unverified PID-file owner.
- `dashboard.py` owns a single strategy-matrix builder/initializer path for Modular Strategies and Portfolio Builder fallback.
- `dashboard.py::_clean_portfolio_price_frame` must delegate to `core.data_orchestrator.clean_price_frame` so display cleanup semantics stay canonical.
- No canonical provider ingestion, market-data write, dashboard content redesign, ranking, scoring, alert, broker path, or strategy-search behavior is authorized.

DASH-0 Dashboard IA Plan (2026-05-10):

- Future dashboard IA is state-first and organized as Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, and Settings & Ops.
- The future shell should use a page registry/sidebar model after DASH-1 approval.
- Full Drift Monitor and Data Health workflows belong in Settings & Ops; only compact status badges belong on Command Center.
- Backtests, Modular Strategies, Daily Scan, and experiments belong in Research Lab.
- No runtime implementation is authorized by DASH-0.

## 1. System Purpose

The Unified Opportunity Engine is the product layer of Terminal Zero.

It combines:

```text
Supercycle Gem Discovery
  + GodView Market Behavior Intelligence
  + Decision Augmentation States
= Unified Opportunity Engine
```

The product helps a human operator identify de-risked asymmetric upside and read market behavior around that opportunity. It does not trade.

## 2. Product Pillars

### 2.1 Primary Alpha: Supercycle Gem Discovery

Goal: find MU/SNDK-style structural winners before they are obvious, while avoiding low-quality left-side speculation.

Required future evidence categories:

- thesis summary;
- structural demand driver;
- supply constraint or capacity bottleneck;
- financial quality / balance-sheet context;
- catalyst path;
- ownership and sponsorship context;
- valuation and expectation reset context;
- contradiction log;
- source-quality and freshness metadata.

G7.1A does not define a family artifact and does not create candidates.

### 2.2 Secondary Alpha: GodView Market Behavior Intelligence

Goal: read how the market is behaving around the thesis.

Signal families to document and later source-policy:

- IV / volatility surface;
- options whales;
- gamma / dealer map;
- short squeeze context;
- CTA/systematic pressure;
- sector rotation;
- ETF/passive flows;
- dark-pool / ATS / block activity;
- ownership whales;
- microstructure / order book;
- catalysts and narrative velocity;
- regime.

GodView signals are context. They do not approve trades or override source-quality rules.

### 2.3 Output Layer: Decision Augmentation

Goal: turn evidence into human-readable states:

```text
wait
watch
accumulation
confirmation
buying range
let winner run
trim optional
exit risk
thesis broken
```

These states are paper-only prompts after future approval. In G7.1A they are product vocabulary only.

## 3. Unified State Engine

The future state engine should merge primary and secondary alpha:

```text
thesis_state
  + market_behavior_state
  + entry_discipline_state
  + hold_discipline_state
  + source_quality_state
-> dashboard_state
```

Example future state mapping:

| Thesis state | Market behavior | Entry/hold discipline | Output state |
| --- | --- | --- | --- |
| intact | supportive | left-side risk high | wait |
| intact | improving | base forming | watch |
| strengthening | supportive | entry window improving | accumulation |
| strengthening | confirming | price/flow confirmation | confirmation |
| intact | supportive but volatile | price near defined range | buying range |
| intact | momentum supportive | crowding acceptable | let winner run |
| intact | mixed/crowded | risk rising but thesis alive | trim optional |
| weakening | hostile | exit conditions emerging | exit risk |
| broken | unsupported | invalidation confirmed | thesis broken |

This table is product design, not executable logic.

## 4. Source Metadata Contract

Every future signal must carry:

```text
source_quality
provider
provider_feed
freshness
latency
confidence
observed_vs_estimated
allowed_use
forbidden_use
manifest_uri
```

Allowed-use examples:

- research context;
- dashboard context;
- paper-only prompt context after approval;
- promotion evidence only if Tier 0/canonical policy is satisfied.

Forbidden-use examples:

- live order trigger;
- broker instruction;
- alpha evidence without validation;
- canonical write without manifest;
- source-quality bypass;
- unreviewed signal approval.

## 5. Observed Facts vs Estimates

The product must distinguish:

- observed facts: reported price/volume, reported short interest, published filings, official exchange/OCC/CFTC/FINRA/SEC reports;
- vendor transforms: vendor-calculated IV, unusual options flags, ETF flow fields, dark-pool aggregations;
- model estimates: dealer gamma maps, CTA pressure proxies, squeeze probability, narrative velocity scores.

Estimated fields may be useful, but they must be labeled and cannot masquerade as observed truth.

## 6. Current Infrastructure Fit

Current infrastructure is enough for:

- canonical daily price governance;
- manifest/provenance checks;
- Candidate Registry;
- V1/V2 mechanical replay discipline;
- dashboard smoke checks;
- minimal validation lab;
- paper-alert readiness foundations.

Current infrastructure is not enough for full GodView until future provider layers exist:

- `data/providers/options_provider.py`
- `data/providers/short_interest_provider.py`
- `data/providers/cftc_provider.py`
- `data/providers/sec_filings_provider.py`
- `data/providers/etf_flow_provider.py`
- `data/providers/news_research_provider.py`
- `signals/source_registry.py`
- `signals/freshness_policy.py`
- `signals/confidence_policy.py`
- `signals/godview_state_machine.py`

These are future upgrades. G7.1A does not create them.

## 7. Dashboard Product Surface

Future dashboard areas:

- opportunity watchlist;
- thesis card;
- GodView market-behavior panel;
- entry discipline panel;
- hold discipline panel;
- source-quality and freshness rail;
- paper-only prompt state.

The dashboard must not show automatic buy/sell orders, broker actions, unqualified rankings, or unreviewed signal approvals.

## 8. Roadmap

```text
G7.1A - Starter Docs / PRD / Product Spec Rewrite
G7.1B - Data + Infra Gap Assessment for GodView signals
G7.1C - Codex/Chrome Research Agent SOP
G7.2  - Unified Opportunity Engine State Machine
G7.3  - GodView Signal Source Policy
G7.4  - Supercycle Gem Family Definition, no search
G7.5  - Market Behavior Signal Family Definitions, no search
G8    - One Supercycle Gem Candidate Card, no search
G9    - One Market Behavior Signal Card, no search
G10   - Dashboard Prototype: watchlist state view
G11   - Bounded discovery under sealed families
G12   - Paper-only buying-range / hold-discipline alerts
```

Immediate next action:

```text
approve_g7_1b_data_infra_gap_or_g7_2_state_machine
```

## 9. G7.1A Boundary

G7.1A may change docs, architecture docs, phase brief, current truth surfaces, handover, SAW report, decision log, notes, and lessons.

G7.1A must not add:

- candidate generation;
- alpha search;
- backtest;
- replay;
- proxy run;
- options ingestion;
- signal ranking;
- buy/sell alerts;
- broker calls;
- Alpaca live behavior;
- OpenClaw notification;
- new runtime dashboard behavior.

## 10. Acceptance Status

This spec is complete for G7.1A when the root PRD/spec, architecture package, phase brief, current truth surfaces, handover, and SAW report all describe the Unified Opportunity Engine as the product center and keep G7.2/G8 held.

## Portfolio Lifecycle Current Holds Addendum

- Current holdings are reconstructed from latest lifecycle ENTER/EXIT events at or before the current as-of timestamp.
- A later EXIT closes a holding; future-dated replay rows do not affect today's current portfolio.
- Portfolio & Allocation renders open lifecycle holdings plus residual cash when replay is not sell-all and there are no fresh PIT ENTER candidates.
- JSON position memory is a fallback only when lifecycle replay evidence is empty.
- Residual cash is preserved in both allocation display and live ticker performance paths for sub-100% lifecycle holdings.
- No provider ingestion, broker behavior, alert, ranking, scoring, or new optimizer objective is added.

## Portfolio Replay Selection Identity Addendum

- Portfolio & Allocation publishes `PortfolioReplaySelection` from optimizer controls before replay surfaces render.
- Replay request construction validates the signed selection against method, cap, risk-free rate, typed replay assets, current price-frame identity, and selected price content.
- Missing or stale selection renders replay unavailable; hidden `optimizer_universe` and first-10 column fallback are forbidden replay sources.
- Dashboard-loaded aux event/decision rows remain a labeled transitional bridge until backend artifacts own dashboard cache signature emission.

## Lifecycle Decision Export Addendum

- `scripts/pit_lifecycle_replay.py --export-only` writes a full PIT decision tape and compact buy/sell tape without mutating lifecycle event state.
- BUY/SELL export rows must exactly match replay ENTER/EXIT events.
- Each export row includes reason codes, factor/gate state, streaks, hold days, cooldown state, and Rule-of-100 proxy fields.
- BUY/SELL fields are audit labels only and do not create recommendations, broker orders, alerts, rankings, scores, or dashboard action labels.

## Rule100 Lifecycle Policy v0 Addendum

- `Rule100State` owns the v0 factor adapter and exposes proxy provenance for demand, supply, pricing, and margin.
- Runtime lifecycle events remain ENTER/EXIT for dashboard compatibility.
- Decision tape lifecycle actions are BUY, HOLD, TRIM, TIGHTEN, EXIT, and NO_ACTION.
- TRIM has `suggested_weight_delta = -0.025`; TIGHTEN has `suggested_weight_delta = 0.0`; neither changes actual v0 weights.
- Entry sizing formula is `min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15)`.
- No generic replay framework, provider ingestion, broker behavior, alert, ranking, scoring, or dashboard recommendation label is added.

## Optimizer History Diagnostics Split Addendum

- `OptimizerUniverseResult.insufficient_history` remains the fail-closed backend bucket for local price-readiness failures.
- The Portfolio Optimizer UI splits that bucket into:
  - `Missing History`: no local price column or fewer than the policy minimum observations.
  - `Stale Endpoint`: sufficient observations exist, but the column endpoint is older than the required local matrix endpoint tolerance.
- The Universe Audit table includes `Latest Price Date` so stale endpoint rows are diagnosable without implying short history.
- `History Fail` must not be used as the visible aggregate label for this mixed condition.
- No provider ingestion, canonical write, broker behavior, alert, ranking, scoring, recommendation, or live trading is added.

## PEAD Calendar-Time Inference Method Addendum

- Signal assignment uses existing event-date `signal_bucket_eligible` status and must not depend on future window completeness.
- Assign all signal-eligible quantiles first; across authoritative event sessions `+1..+60`, latest event wins per `(security_id, return_date)` before Q1/Q5 filtering. Equal-date ambiguity fails closed, a newer middle-quantile event closes an older extreme exposure, and missing latest returns never fall back to older events.
- Daily legs are equal-weight finite raw returns with expected/finite/missing counts and a minimum of 10 distinct securities per leg. Interior count failures make inference null.
- Primary model: `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`, Newey-West `maxlags=59`, corrected covariance, no tuning.
- Exact M1B evidence path is `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`, published as strict canonical JSON by same-directory `fsync` plus atomic replace.
- `alpha_CT` is only a single-factor calendar-time intercept for the bounded sample. Terminal M1A approval, M1B, and any alpha interpretation remain unexecuted.
