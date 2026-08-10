## 2026-08-10 Lane 2 Historical Compression — Capital IQ / A1→A2 Formula and Authority Registry

- Historical screen law at start date `t0=2025-05-16`: dated Major-US/funding market membership AND reconstructed Public/Operating bucket AND `Revenue_FY0 >= 1.3 * Revenue_FY-1` AND `Revenue_FY-1 >= 1.3 * Revenue_FY-2` AND `Revenue_FY-2 >= 1.3 * Revenue_FY-3`, with annual revenue requested as `Originally Reported` and mechanically bound to `t0`. Implementation: `research/aov0/historical_screen_reconstruction.py`; source admission: `research/aov0/historical_risk_set.py`.
- Historical risky identity law: company membership stays at `SP_ENTITY_ID`, risky-asset permanent identity is `CIQSEC:<SP_CIQ_ID>`, listing identity is `SPT<SP_TRADING_ITEM_ID>`. The admitted 2025-05-16 law selects exactly one dated Major-US/funding security per entity without current-primary conditioning. Implementation: `research/aov0/historical_security_master.py`.
- Historical market-source contract: Securities perspective `321247`; Total Return field `322797` with `sk_100=1D`; Close field `324251`; Volume field `324277`; date secondary `sk_557`; query identity is exact SPT instrument/trading item. Missing provider values remain missing; no ticker/company/alternate-listing fallback. Capture: `scripts/aov0_capture_ciq_historical_market_productquery.py`.
- Historical PIT fundamental contract: SPG `dispid=12`; `FilingVer=Original`; weekly transition detector is `IQ_PERIOD_END/FQ0`; transition snapshots request `FQ0..FQ-4` for `IQ_TOTAL_REV`, `IQ_TOTAL_ASSETS`, `IQ_INVENTORY`, `IQ_DA_SUPPL_CF`, `IQ_TOTAL_EQUITY`, `IQ_TOTAL_DEBT`, `IQ_CASH_ST_INVEST`, `IQ_OPER_INC`, `IQ_CAPEX_BNK`. Capture: `scripts/aov0_capture_ciq_historical_pit_productquery.py`; normalization/replay: `research/aov0/historical_pit.py`.
- Terminal cash-event law: for an exact source-bound terminal security with last actual close `P_last`, effective-date cash consideration `C`, `terminal_return := C / P_last - 1`. On the effective date the fixed security column realizes `terminal_return`, `close=C`, `volume=0`; from the following session onward `return=0`, `close=C`, `volume=0`; the security is removed from risky target/eligibility at/after the effective date but remains in the fixed replay matrix to prevent future-completeness survivor filtering. Implementation: `research/aov0/historical_lifecycle.py` + `research/aov0/historical_pit.py`.
- Replay activation law: each completed-week decision is computed from that decision close using the exact current-cut builder; decision state activates at the next observed close, then the canonical engine's one-bar lag controls first credited P&L. Implementation: `research/aov0/historical_pit.py::build_historical_replay_inputs`.
- A1 admission law: `stage=A1 AND trading_days>=252 AND canonical_arm_gates_pass AND real_CIQ_identity AND historical_screen_membership_reconstructed AND historical_primary_identity_reconstructed AND terminal_lifecycle_authority_pass`. Closed result: `A1_ADMITTED_HISTORICAL_PIT`, 264 trading days, 94 active CIQ securities, `financial_alpha_evidence=0`.
- A2 law: A1 must be admitted before freeze; freeze binds A1 report/hash, exact 94 active security IDs, source cohort, lifecycle packet, executable hashes, A2 window `2026-06-12..2026-08-07`, and `evaluation_query_count=1`. Held-out PIT fundamental retrieval timestamps must be strictly after freeze; query lock is written before evaluation; second evaluation is forbidden. Closed result: `A2_UNTOUCHED_HISTORICAL_PIT`, 38 trading days, one query, `financial_alpha_evidence=0`.
- Economic closure: A1 Parent cumulative return `+0.7145%`, Child `+0.3501%`; A2 Parent `+6.7152%`, Child `+5.3701%`. Child improves max drawdown/CVaR/turnover but reduces return/Sharpe in both windows. This is historical diagnostic evidence only; no in-place Parent/Child tuning, prospective evidence uplift, or second A2 read is authorized.

## 2026-08-09 Strategic Direction Lock — Prediction / Multi-Clock / PAPER-0 Registry

- Strategic authority: `STRATEGIC_DIRECTION=APPROVED_AND_LOCKED`; `BROAD_ARCHITECTURE_REOPEN=NO`; `MANDATORY_RECUTS=AUTHORIZED_FOR_EXECUTION`; canonical record=`docs/architecture/aov_strategic_direction_lock_20260809.md`.
- PAPER-0 authority=`docs/architecture/paper_0_authority.md`; historical vintage gate=`docs/architecture/historical_fundamental_vintage_authority.md`; method endgame=`docs/architecture/alpha_organism_endgame_current.md`.
- Evidence/capital law: `parallel_evidence_qualification = true`; `current_capital_policy_authority_count = 1`. Several Alpha Families may independently qualify evidence; qualification is not a capital commit.
- Family WIP law: `default_active_alpha_families = 2`; `initial_alpha_family_ceiling = 3`; CRV1 keeps `primary_horizon=252 trading days`; one fast family with economically justified multi-week horizon is preregistered separately.
- Prediction law: `State_t != Forecast_t(h) != TargetWeight_t != Execution_t`. `Forecast_t(h)` is an immutable future-directed statistic/distribution/probability bound to `as_of`, target, horizon, execution boundary, input/model hashes, comparator and prediction identity before outcome visibility.
- Composition law: every additional family/component is tested as `I` versus `I+X`; multi-scale agreement is not automatic capital authority.
- Event-family law: `AlphaEventFamily := economic mechanism + PIT event/state definition + ForecastTarget + Horizon + Falsifier + SearchBudget + Cost/Capacity + A1/A2/A3 contract`. Models such as GMM/HMM/Hawkes/XGBoost/TFT/DeepLOB are internal implementations, not family authority.
- Historical vintage hard gate: current replay semantics require `FilingVer=Original`; current capture scripts request/emit `FilingVer=Current/Restated`; A1/A2 remains blocked until one provider-vintage contract wins destructively and the A1 report cannot claim `historical_spg_asof_original=true` from conflicting bytes.
- Historical parity law: before `exact frozen-AOV replay`, same-input current/historical paths must reconcile permanent IDs, `ADV20`, realized vol, SMA/trend state, Q/U, technical quality, sizing eligibility and Rule100 weights; only explicit temporal activation-lag differences may remain.
- PAPER-0 intent law: future `ExecutionIntentV1 := {account_id, live_rebalance_id, promoted_policy_id/seal_id, execution_map_hash, instrument_id, side, quantity, execution_policy_id, time_in_force, rebalance_epoch}`; intent hash/signature/CID derive from that object. Current legacy day/symbol/side/qty CID authority is superseded only when this new contract lands destructively.
- PAPER-0 calendar law: first order must resolve actual session close, including early-close semantics, or be restricted to a verified regular full-session day and fail closed otherwise.
- PAPER live-state law: broker accepted/open/partial/fill/cancel/reject state projects into a versioned canonical PAPER state whose commitment includes open orders and partial-fill residual risk; restart begins `FREEZE_NEW_RISK=true` and `rebalance_epoch` fences stale workers.
- Provider throughput law: after historical-vintage semantics freeze, start `2` disjoint Excel workers and scale to `3–4` only from measured COM/provider stability and deterministic part integrity. Python simulation performance is not the current bottleneck.
- Replication readiness law: entitlement/identity/PIT-vintage/license/retention/acquisition-latency preparation starts now in quarantine; replication outcomes are not discovery/confirmatory inputs.
- Claim boundary: Clock #1/Parent/Child unchanged; `financial_alpha_evidence=0`; PAPER operational evidence is not Alpha; strategy live capital/leverage/short/options remain closed.

## 2026-08-08 Lane 1 Prospective Slice 1 Formula Registry

- Weekly tape preflight: `candidate_set_t == frozen_candidate_set_109` and, for every required source `s` in `{CIQ fundamentals, CIQ primary-security master/status, CIQ completed market data, NY Fed SOFR}`, `previous_cut_at < retrieved_at_s <= current_cut_at`. Any candidate-set drift, missing required source, stale receipt, future-stamped receipt, invalid source identity, or invalid raw SHA-256 fails closed before v3 decision-cut construction.
- Selection law: the weekly preflight never reruns the growth screen and grants no seal, outcome, Parent/Child mutation, or financial-alpha authority. It emits only `READY_FOR_V3_DECISION_CUT_CONSTRUCTION`; the existing cut → Seal Candidate → fresh-process verification → Clock-Start Receipt chain remains the sole prospective authority path.
- Alpha PIT fixture law: deterministic fixtures are content-addressed by request/payload/manifest hashes; rows expose permanent `CIQSEC:` identity, `available_at`, source receipt binding, coverage status and explicit missingness semantics. Confirmatory/prospective capability objects have no `outcomes` method; discovery outcome capability is imported lazily only for discovery sessions.
- Alpha PIT real-producer law: `CIQCycleV1Adapter` verifies the exact current CIQ security-master, market-history and quarterly-panel custody hashes before use and refuses to backdate those current-cut bytes before their conservative availability boundary. `fund.gross_margin_q` and `fund.cash_from_ops_q` remain source-level `MISSING_SOURCE` for every requested security because those fields are absent from the landed `run_4` source; CIQ expectations and SEC claims remain explicit source-level missingness when their source bytes are not landed. No fallback provider is allowed.
- CRV1 risk-set admission law: the AOV frozen-109 growth-screen laboratory is forbidden as `CRV1_US_PRIMARY_COMMON_V1`. A future CRV1 risk-set source must bind `CRV1_US_PRIMARY_COMMON_ELIGIBILITY_V1`, its exact contract hash, no growth/current-survivor/future-membership filter, row-level U.S. primary-common/active-tradable/unique-identity/`>=200` prior-market-observation proofs, and an independently hash-bound identity receipt. Label-only admission is insufficient.
- CRV1 fixture/input-packet law: the consumer imports the provider-blind Alpha PIT API only, closes risk-set/observation/claim/expectation manifest hashes into `cycle_resonance_input_packet_v1`, rejects mixed real/fixture authority, and fixes `financial_alpha_evidence=0`. Fixture authority is `MECHANICAL_FIXTURE_ZERO_EVIDENCE`; it carries zero PIT/OOS/prospective/financial-alpha evidence.
- CRV1 implementation-manifest law: `freeze_implementation_manifest()` has no scientific defaults. Family/risk-set/label identity, requested fields/measures/topics, coverage policy, clock transform hashes, claim interpreter, ordered-sequence semantics, falsifiers, model/hyperparameters, training/calibration/ranking, search family/budget, cost assumptions and code-byte manifest are all mandatory. `actual_trials_consumed_at_freeze <= preregistered_search_budget`; sealed manifest hash tampering fails closed.
- Current real-custody diagnostic: 109 current CIQ identities; market close/return/volume/ADV20/realized-vol/SMA20 present for 109/109, SMA200 present for 104/109 with five explicit short histories; `fund.gross_margin_q` and `fund.cash_from_ops_q` are 109/109 `MISSING_SOURCE`; all 981 expectation rows are `MISSING_SOURCE`; SEC claims source is unlanded; independent CRV1 risk-set status=`BLOCKED_INDEPENDENT_CRV1_RISK_SET_NOT_LANDED`. This is mechanical current-custody validation only, not CRV1 empirical evidence.
- Mutation boundary: no outcome-informed change to Parent, Child, or CRV1 is authorized before a matured, reconciled, validated ReviewPacket. This slice implements no ReviewPacket opening or MutationManifest execution.
- Validation: Alpha-PIT + CRV1 focused matrix `19/19 PASS`; full AOV regression `102/102 PASS`; ZERO-COMPAT contract test PASS and asserts all seven counters are zero; selected Lane-1 modules compile cleanly; `git diff --check` PASS. No separate ZERO-COMPAT CLI result is claimed.

## 2026-08-08 AOV-0 Destructive V3 Temporal Authority Registry

- Active cut/seal/clock schemas: `aov0_ciq_decision_cut_v3`, `aov0_prospective_seal_v3`, `aov0_prospective_clock_start_receipt_v1`; active runtime has no v2/open reader or writer. Historical v2 artifacts remain immutable mechanical evidence only.
- Calendar/evaluation law: `execution_calendar_id=NYSE_2026_CORE_CLOSE_1600_ET`; `evaluation_start := next eligible 2026 NYSE session after decision_target_date at 16:00 America/New_York`; Friday 2026-08-07 therefore maps to Monday 2026-08-10T20:00:00Z. Weekend, wrong-close, legacy 09:30 open, and evaluation<=cut values fail closed.
- Candidate timing law: `knowledge_cutoff <= cut_built_at <= sealed_at < evaluation_start`. Seal construction returns `SEAL_CANDIDATE_WRITTEN` and `prospective_clock_started=false`; the seal payload itself cannot contain a clock-start claim.
- Promotion law: a child Python process performs full-chain reopen and atomically writes `aov0_fresh_process_verification_v1`; only a separate immutable Clock-Start Receipt bound to seal bytes, verification proof/ID, verifier bytes, and verification time may set `prospective_clock_started=true`.
- Return/maturity law: `attributed_interval_start >= evaluation_start`; `outcome_open_not_before := evaluation_start + 30 calendar days`. Self-consistent early-maturity seal rehashes still fail semantic validation.
- Cash law: official SOFR minus 25 bp / ACT-360 / post-publication / no proxy substitution is now explicitly validated in the executable contract; proxy/ETF cash authority fails before Seal authority.
- Adversarial gate: bound market one-byte mutation, +1bp serialized target-vector mutation, ticker/non-CIQ identity injection, SOFR source substitution, same-process promotion, calendar/timing mutation, pre-evaluation interval, early maturity, and pre-receipt/pre-evaluation/pre-maturity future-authority checks all fail closed.
- Validation: AOV `75/75 PASS`; ZERO-COMPAT `0/0/0/0/0/0/0`; active runtime source grep contains no v2/open authority reference. Synthetic v3 promotion reaches fresh-process proof + separate Clock-Start Receipt with `financial_alpha_evidence=0`.
- Real Clock #1 completion: primary master SHA-256=`8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`; final exact-primary-SPT market object=`data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv`, 21,345 rows, SHA-256=`897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48`, duplicate-key conflicts=`0`. CIQ admission produced 99 canonical securities and 10 mechanical exclusions. Real `decision_cut_v3`=`AOV0_CIQ_20260807_ad2faf0533cec19c`; Seal Candidate=`c78088ace7819170cd0064154fba138da4b4f8183dbd4ec48c347a942985ba88`; fresh-process verification succeeded; immutable Clock-Start Receipt=`eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78` started Clock #1 at `2026-08-08T19:48:52.440503Z`. Evaluation begins `2026-08-10T20:00:00Z`; outcomes remain sealed until `2026-09-09T20:00:00Z`; `financial_alpha_evidence=0`.

## 2026-08-07 AOV-0 `run_4` Dual-Role Authority Registry

- Raw company authority: `run_4.xlsx`, SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`, 215,249 bytes, 109 source entities. One raw object owns both `COMPANY_UNIVERSE` and `QUARTERLY_FUNDAMENTALS`; `run_2.xlsx` is historical evidence only.
- Fundamental outputs: 1,203 absolute `FQqYYYY` entity-quarter rows and 109 current states; 56 complete four-group states, 52 partial states, one no-absolute-quarter-history state. `SP_ENTITY_ID` remains temporary company provenance, never active security identity.
- Active source-receipt set: `{ciq_quarterly_fundamentals, ciq_security_master, ciq_market_data, nyfed_sofr}` exactly. The separate `ciq_screen_universe` role and `screen_retrieved_at` override are deleted rather than aliased.
- Knowledge-cutoff law: `knowledge_cutoff := max(four active source receipt retrieval/admission times, max(primitive.known_at), max(official_sofr.published_at))`. File mtime is never retrieval authority; no `run_2` time is needed because `run_2` is outside the active cut.
- Decision-cut law remains: four Parquet SHA-256 bindings + frozen contract hash + date-local `CIQSEC:` universe hash + four source receipts + target/seal/execution chronology; target Rule100/return/primitive asset sets must match and primitive `total_return` must equal the P&L matrix within absolute `1e-15`.
- Remaining external gate: real primary Capital IQ Security ID + Trading/Instrument Item mapping; completed daily primary-security total-return/price/volume retrieved at/after 16:00 America/New_York; direct NY Fed SOFR retrieved at/after 15:00 America/New_York; then cut → seal → exact reopen.

## 2026-08-07 AOV-0 Prospective Custody V2 Registry

- Implementation: `scripts/aov0_build_decision_cut.py`, `scripts/aov0_first_seal.py`, `scripts/aov0_reopen_seal.py`, `research/aov0/experiment.py`.
- Active cut schema: `aov0_ciq_decision_cut_v2`; active seal schema: `aov0_prospective_seal_v2`.
- Temporal authority: `knowledge_cutoff <= cut_built_at <= sealed_at < first_eligible_execution_bar`; `cut_built_at` is stamped by cut construction and `sealed_at` is independently system-stamped at the actual prospective seal write.
- Execution-bar authority: `first_eligible_execution_bar := next NYSE 2026 trading session after decision_target_date at 09:30 America/New_York`; frozen calendar identity=`NYSE_2026_CORE_OPEN_0930_ET`. For target `2026-08-07`, first execution=`2026-08-10T13:30:00Z`. Weekend/holiday/wrong-open timestamps fail closed.
- Executable identity: `aov0_executable_byte_manifest_v1 := domain_hash(files[path -> {bytes,sha256}], python_version, interpreter{path,bytes,sha256})`; required and actually loaded repo Python modules are included, so a dirty Git worktree cannot masquerade as a Git-SHA-identified executable.
- Target-vector authority: each current arm stores both `target_hash := frame_hash(target_frame)` and canonical serialized `{date, columns, values(.17g)}`; fresh reopen reconstructs the frame and recomputes the hash.
- Full-chain reopen: separate Python process verifies executable manifest/files/interpreter → seal hash → decision-cut bytes/fields → four Parquet bytes/cut hashes → experiment manifest identity → each Rule100/Parent/Child evidence manifest and all files it binds → all five current target vectors. Only exact closure returns `FULL_CHAIN_REOPEN_VERIFIED`.
- Validation: custody/CIQ focused matrix `36/36 PASS`; explicit fresh-process integration PASS; full AOV `61/61 PASS`. Real seal remains absent because CIQ Security/Trading Item mapping and completed post-16:00 ET market bytes are not yet admitted; `financial_alpha_evidence=0`.

## 2026-08-06 AOV-0 Formula and Decision Registry

- Method authority: `docs/architecture/alpha_organism_endgame_current.md`; active brief: `docs/phase_brief/alpha-organism-vertical-0-brief.md`; detailed checklist: `docs/checklists/aov0_working_alpha_system_checklist.md`.
- State vector: `x_(i,t) := (Q, M, F_proxy, C_proxy, L, R, U)`.
- Control law: `dynamic_deltas = 0 => AOV target weights numerically equal Rule100 target weights within the frozen tolerance`; canonical serialized evidence is byte-identical after sorting and formatting.
- Parent/Child law: Parent and Child use one PIT cube, universe, return matrix, execution lag, cost policy, and Rule100 budget/cap/lifecycle/cash harness. Child differs by exactly one declared mutation.
- Hazard mandate: `ReversalHazard` is a bounded risk-insurance overlay. Its promotion objective is safety improvement subject to a frozen premium budget; no positive-average-return requirement may be silently added.
- P&L authority: PIT total-return matrix is the sole return authority; corporate-action records are reconciliation-only and cannot inject a second P&L path.
- Cash separation: engine residual cash, economic cash benchmark, and future broker cash are distinct authorities.
- Seal semantics: a prospective seal binds model/data/universe/cost/endpoint/execution/horizon identities and starts the clock; it contributes zero financial-alpha evidence until outcome maturity.
- Review identity: `delta_net := delta_gross - delta_cost`; `abs(observed_delta_net - calculated_delta_net) <= frozen_tolerance` before ontology. Contribution partitions are realized accounting partitions, not causal components.
- Search-debt separation: search debt reduces promotion confidence, not current target weights.
- Current P0 decisions still open: dimensionally coherent `F_proxy/C_proxy`; Rule100 equivalence implementation; Parent policy; insurance endpoint/materiality/premium; total-return source; economic-cash total-return convention; sleeve execution/horizon; PIT universe; V0 parameters; dependence-aware inference.
- Current claim boundary: AOV implementation not started; AOV evidence `0`; Limited Live closed.

## 2026-08-06 PAIR-DECISION-SERIES-1 Temporal Contract Formula Registry

- Runtime: `gv_portfolio_v0/market_source_adapter.py`; execution/replay binding: `gv_portfolio_v0/prospective.py`.
- Strict decision timestamp: `decision_observed_at_n := floor_to_minute(decision_cut_knowledge_at_n) + 1 minute`; therefore `decision_observed_at_n > decision_cut_knowledge_at_n`, including knowledge cuts exactly on a minute boundary.
- Adjacent-cut sequence: for every `n > 1`, `decision_cut_knowledge_at_n > decision_cut_knowledge_at_(n-1)` and `decision_cut_id_n != decision_cut_id_(n-1)`.
- Capture binding: `episode.decision_cut_knowledge_at == capture.retrieval_knowledge_at` and `capture.source_timestamp_utc <= capture.retrieval_knowledge_at`.
- Outcome opening: `outcome_open_not_before_n := decision_cut_knowledge_at_n + minimum_elapsed_calendar_days`; the current invariant horizon uses 30 calendar days.
- Series invariants: pair, comparator, cost model, decision policy, source contract, outcome-horizon specification, and banked subject-evidence identities remain byte-equivalent to episode 1.
- Current evidence: Episode 1 and Episode 2 remain `ABSTAIN / NO_POSITION`; cash `11000`, costs `0`, unexplained residual `0`; local bounded matrix `142/142 PASS` after adjacent-cut, exact-minute, and outcome-open regressions.
- Claim boundary: sealed forward paper episodes only; opened outcomes `0`, portfolio-alpha evidence `0`, Limited Live closed.

## 2026-07-21 E0B Observation / Decision-Value Formula Registry

- Runtime: `core/gv_e0b_dv1_contradiction.py::decision_value_disposition_from_comparison`.
- Observation gate: `comparison_observed_eligible := real_same_operator_baseline_post AND different_real_blinded_reviewer AND operator_freshness_attested AND reviewer_blinded_receipt_attested AND full_seal_chain_replay_valid`.
- Observed count: `observed_comparison_count := 1 if comparison_observed_eligible else 0`.
- Item delta: `delta_i := post_packet_score_i - baseline_score_i` for each frozen rubric item.
- Total delta: `delta_total := Σ_i delta_i`; the runtime rejects any stored total inconsistent with the six item deltas.
- Targeted gain: `targeted_gain := (delta_indispensable_missing_evidence_identification > 0) OR (delta_falsifier_and_contradiction_recognition > 0)`.
- Core safety preservation: `safety_not_worse := (delta_selected_action_defensibility >= 0) AND (delta_avoidance_of_claims_beyond_evidence >= 0)`.
- Value disposition: `IMPROVED iff delta_total > 0 AND targeted_gain AND safety_not_worse; else NOT_IMPROVED`.
- Claim boundary: observation eligibility is sign-independent and controls publication/count. Only `IMPROVED` is positive one-case decision-value evidence for S-009X. `NOT_IMPROVED` is retained falsification, not product PASS. Neither disposition establishes general causal superiority, alpha, population effectiveness, or score uplift.
- No compatibility alias: `e0b_close_eligible` is deleted rather than mapped to either observation or value.
- Custody lineage: `main@2653eb1 → e9e9a9a → C0=b7a24d3 → C1 observation/value repair`; C1 must have parent `b7a24d3`.
- C1 source transfer: exactly 15 source-of-truth files. `current_context.json`, `current_context.md`, stale SAW, caches, and test output are excluded and regenerated after C1 source stabilization.

## 2026-07-19 Score Semantics + Functional Stage Definition

### SHIPPED_PRODUCT_SCORE
- Current value: **39/100**.
- Meaning: **owner claim ceiling** for shipped product claims. Metric confidence is low. **No alpha**.
- Non-uplift rule: do **not** numerically move to 40+ because dual-fixture demo, local green paths, CI parity, or docs recuts exist. Uplift requires separate rubric-based owner claim authorization.
- Rationale repair: obsolete language such as `no visible certified slice` is superseded. A certified dual-fixture static branch demo **does** exist on product tip lineage `490a234`; that fact is expressed via **FUNCTIONAL_STAGE**, not score inflation.

### FUNCTIONAL_STAGE (separate from score)
| Stage | Meaning | Promote when |
|---|---|---|
| `CERTIFIED_STATIC_BRANCH_DEMO` | Permanent dual-fixture certified bundle + default Certified Portfolio route exist on product lineage; deterministic certification substrate closed | Default current stage post-F1C |
| `CERTIFIED_SINGLE_DECISION_OPERABLE` | One operator-visible **current** decision path: frozen E0 custody → HOLD_FOR_EVIDENCE/NO_POSITION → DecisionEnvelope → book/cert → atomic current publication → visible decision → Streamlit smoke | Only with branch evidence for full E0A vertical |

Stage promotion does **not** auto-change SHIPPED_PRODUCT_SCORE.

### ACTIVE_GATE
- Sole active gate: **GV-E0A-OPERABLE**.
- F1C-SHIP: CLOSED_SUBSTRATE (not active).
- FS1+: future stages only; not next action.

### Formula / identity notes
- E0 custody hashes (must remain exact):
  - e0_preregistration.yaml `0a6dc18a44d7532610a73f90b92477fc7bd36644c1a052d81a48162097176618`
  - evidence_authority_matrix.csv `3306adbed26d27732a0a53d3819a09044e418e183ecc58ebebf82c6f9fe0dcb0`
  - e0_model_spec.md `28a0ea062777d9364008480266ce933bd6a34348ce0defcac7185398068a38f0`
  - e0_acceptance_tests.md `9d9a7f195bd8db2caea82859d6a73d951c862f229fc9d72e5302c58ba7b8d55c`
- Implementation paths for E0A code: owned by parallel code agent; not registered complete in this docs round.
## 2026-07-19 GV-FS0 F1C-SHIP Terminal

- Permanent two-role certified bundle tracked; default Certified Portfolio loads permanent bytes only.
- Transport C 48ad053, C2 91b9bf1; hosted product CI 29651784244 PASS; A/B/C PASS; terminal SAW PASS.
- Official score remains 39/100. Obsolete sequential F1C/F1D active-gate language removed.
- Boundary: no provider/PEAD/FS1/main merge.

# Feature Engineering Notes

## 2026-07-18 GV-FS0 F1C-SHIP Formula Registry

- Bundle preimage: `bundle_preimage := {schema_version, protocol_id, currency, components=[OPEN_complete_result, NO_POSITION_complete_result]}`.
- Bundle identity: `bundle_hash := SHA256("GV-FS0:CERTIFIED_BUNDLE:V1\n" || canonical_document(bundle_preimage))`; `bundle_id := "BUNDLE_" || bundle_hash`.
- Candidate identity: bundle hash `527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c`; file SHA-256 `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5`; byte length `55774`.
- Publication compare: `current_bytes == candidate_bytes => IDEMPOTENT`; else `current_hash != observed_prebuild_hash => PUBLICATION_TARGET_CHANGED`; else atomic replacement may proceed.
- Post-replace safety: any exact-byte/hash/schema reread failure yields `PUBLICATION_POST_REPLACE_VERIFICATION_FAILED` and converts the lock to durable `RECOVERY_REQUIRED`; recovery-record failure yields `PUBLICATION_RECOVERY_RECORD_FAILED` and retains the lock.
- Regression rule: `candidate_failure_nodeids ⊆ baseline_c37db09_failure_nodeids`; candidate count is 105 vs baseline 106, therefore zero new failures.
- Implementation paths: `core/gv_fs0_bundle.py`, `core/gv_fs0_publish.py`, `views/gv_fs0_portfolio_adapter.py`, and `dashboard.py`.

## 2026-07-18 GV-FS0 F1B NO_POSITION Formula Registry

- Normative source-intent rule: `NO_POSITION => requested_quantity = null AND every source_intent.intent_type = VALUATION_INSTRUCTION`.
- Primary state for every session `t`: `shares_t = 0`; `cash_t = initial_cash = 1000`; `receivables_t = 0`; `market_value_t = shares_t × close_t = 0`; `NAV_t = cash_t + market_value_t + receivables_t = 1000`.
- Contribution formulas: `session_contribution_t = NAV_t - NAV_(t-1) = 0`; `cumulative_contribution_t = NAV_t - initial_cash = 0`.
- Certification rule: the same two isolated verifier attempts must reproduce the same canonical primary economic payload and hash; every frozen check must be `TRUE` before status `CERTIFIED`.
- Implementation paths: `core/gv_fs0_book.py`, `core/gv_fs0_certify.py`, `views/gv_fs0_portfolio_adapter.py`; tests in `tests/gv_fs0_product/test_no_position_vertical.py`.
- Boundary: F1B remains in memory only; no bundle publication or default routing until F1C/F1D.

## 2026-07-18 GV-FS0 F1A Review Reconciliation Formula Registry

- Raw verifier binding: `raw_verifier_valid := economic_payload == expected_projection(primary_snapshots, decision, fixture, fees) AND canonical_payload_hash == H("GV-FS0:ECONOMIC_PAYLOAD:V1", expected_projection)`. Every semantic field, every session, final state, total cost, and the raw canonical hash must match before a formal verifier result exists.
- Presentation binding: `presentation_valid := rows == projection(terminal_snapshot, certification) AND presentation_hash == H("GV-FS0:PRESENTATION:V1", {rows})`.
- Duplicate handling: byte-identical identity preimages with the same event ID collapse; the same event ID with a different preimage blocks as `CONFLICTING_EVENT_ID`; different event IDs with the same economic-effect key block as `DUPLICATE_SEMANTIC_EVENT`.
- Attempt rule: both ordinals execute even when a runner raises an infrastructure exception; any failure blocks certification.
- Source authority tokens: `DECISION:<decision_hash>` and `CERTIFICATION:<certification_id>`.
- Implementation paths: `core/gv_fs0_book.py`, `core/gv_fs0_certify.py`, and `views/gv_fs0_portfolio_adapter.py`.

## 2026-07-11 Request Artifact Identity Repair V1 Registry

- RoundID: `ROUND-20260711-REQUEST-ARTIFACT-IDENTITY-REPAIR-V1`; ScopeID: `REQUEST_ARTIFACT_IDENTITY_REPAIR_V1`.
- Payload identity formula: `payload_identity_valid := canonical_remote_match AND repository_root_match AND payload_commit_resolves_as_commit AND payload_tree_matches_commit AND every_declared_path_exists_in_payload_commit AND every_declared_SHA256_matches_exact_blob_bytes`.
- Detached-binding formula: `identity_envelope_valid := tracked_separate_envelope AND envelope_binds_prior_payload_commit AND distinct_markdown_json_paths_and_hashes AND lifecycle_status == PREPARED_NOT_SENT`. The envelope never binds its own commit/tree.
- Failure rule: `legacy OR divergent OR reconstructed OR redirected OR cherry_picked OR self_referential OR ambiguous_hash_label OR unbound => dispatch_denied`.
- Current evidence: Commit 1 `a86c3a0fcc34d29e8d76cded5616c6cbe77f500e` / tree `17d7dd85bee600b3658337b129774ffc629bad11`; tracked detached envelope with four distinct path/hash pairs and `PREPARED_NOT_SENT`; governance PASS 0 findings; planning boot PASS; fresh A/B/C technical check sets PASS.
- Current boundary: distinct-agent ownership unavailable, therefore terminal SAW BLOCK. No remote, dispatch, source/provider access, validation, readiness, Gate D, publication, strategy/UI, or data output.

## 2026-07-11 P0 Trust-Substrate Repair Registry

- RoundID: `ROUND-20260711-V2-PEAD-P0-TRUST-SUBSTRATE-REPAIR`; ScopeID: `V2_PEAD_P0_TRUST_SUBSTRATE_REPAIR`.
- Git identity formula: `git_identity_valid := git_worktree_available AND git_redirection_env_sanitized AND GIT_NO_REPLACE_OBJECTS == "1" AND replacement_refs_status == CLEAR AND raw_HEAD == HEAD^{commit} AND raw_upstream == @{u}^{commit} AND tree == HEAD^{tree} AND identity_verified`. Any false term is a hard authority failure; loose and packed refs are both enumerated through Git.
- JSON authority formula: `authority_json_valid := JSON_object_parse_succeeds AND every_object_member_name_is_unique`. `duplicate_key_at_any_depth => authority_json_valid = false` before authorization, schema, source-byte, or output-write evaluation.
- Current state: the adversarial code/test matrix and fresh independent A/B/C review pass; this checkout reports `git_identity_valid = true`, but dirty/unclassified workspace state and broader governance-preflight failure keep authority transfer blocked. P2 remains locally reviewed and non-publishable.
- Boundary: no backward compatibility for ambiguous JSON; no source-owner dispatch, publication, remote action, source/provider work, Gate D, Strategy/UI, data output, or readiness promotion.

## 2026-07-02 V2 PEAD M6b Slice 0 Active-Contract Deconfliction Registry

- RoundID: `ROUND-20260702-V2-PEAD-M6B-SLICE0-CONTRACT-DECONFLICTION`; ScopeID: `V2_PEAD_M6B_SLICE0_ACTIVE_CONTRACT_DECONFLICTION_DOCS_ONLY`.
- Strict Gate A rule: `strict_gate_A_PASS := eps_vintage == first_public_unrestated AND all other locked Gate A provenance and validation requirements pass`. `release_date_aligned_but_restated` is non-strict diagnostic evidence only and cannot satisfy `strict_gate_A_PASS`, `strict_vintage_pit`, or `m6b_data_contract_ready`.
- Repository-identity rule for approval/request packets: `identity_valid := commit_resolves AND commit_tree == declared_tree AND artifact_exists_at_declared_path AND SHA256(artifact_bytes) == declared_artifact_sha256 AND payload_identity_matches`. Any false term requires denial and repository rerouting.
- Quant verification: `cc96053513f445f143632103c478367bbf674e12` does not resolve as a Quant commit and `R0.1-preflight-plan.md` is absent at the repository root; no R0.1 authority is valid here.
- Boundary: historical addenda are preserved; Slice 0 changes active contract and packet-template language only. No data, provider, source-byte, ETL, curve, readiness, or R0.1 work.
- Next action: dispatch only the existing Gate A and Gate B/C source-access requests.

## 2026-06-30 V2 PEAD Strict M6b Path A Gate Formula Registry

- RoundID: `ROUND-20260629-V2-PEAD-M6B-STRICT-PATH-A-INFRA`; implementation: `scripts/pead_m6b_strict_path_a_data_gate.py`; tests: `tests/test_pead_m6b_strict_path_a_data_gate.py`.
- Authorization formula: evidence payload fields never authorize; `authoritative_current_evidence := distinct_authorization_artifact AND exact_evidence_file_sha256_match AND round/scope/mode/action_match`. Malformed authorization JSON/schema and any authorization supplied for `synthetic_test` are CLI input errors; structurally valid but unapproved or mismatched current-evidence authorization is `NOT_AUTHORIZED`.
- Gate formula: current `gate_status_g = PASS` only when detached authorization is `AUTHORIZED`, all four source-byte SHA-256 checks are verified, and the gate's required provenance, complete coverage, temporal proofs, gate-specific evidence, and validation checks pass; otherwise every current gate is `BLOCKED`.
- Readiness formula used in the script: `m6b_data_contract_ready := authoritative_current_evidence AND all(A,B,C,D = PASS) AND strict_vintage_pit`.
- Restatement rule: release-date-aligned/restated EPS has `strict_vintage_pit=false` and is `BLOCKED`; its exception is `NOT_AUTHORIZED`. Inherited exception wording is superseded on current truth surfaces, and even an explicitly approved exception retains hard flags and cannot make strict Gate A or readiness pass.
- Current evidence: A/B/C/D=`BLOCKED`, source bytes unverified, `m6b_data_contract_ready=false`, `workflow_status=blocked_fail_closed`; JSON SHA-256 `0ef4b2504f7f573eab734614054e3c3e9ffa746b02522a6ef00a51453010574a`.
- Validation: strict-gate tests PASS 68/68; existing M6a tests PASS 12/12; compile, deterministic atomic CLI replay, missing explicit `--output`, synthetic canonical-output rejection before atomic write, payload-only restated-approval rejection, malformed-evidence and malformed-authorization JSON/schema CLI errors with no output, authorization mismatch, source-byte tamper, static-isolation, output-isolation, and canonical context build/validation checks PASS.
- Boundary: M6a remains sparse engine/framework evidence only; Data Path A is active; UI/frontend and Strategy promotion are held; B remains illustrative-only and is never a strict-data fallback.
- Next action: obtain authorized, verifiable evidence for the smallest blocked strict-data gate.

## 2026-06-25 V2 PEAD M6b Best-Available Option 1 Repair Registry

- RoundID: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REPAIR`.
- ScopeID: `V2_PEAD_M6B_BESTAVAIL_OPTION1_TERMINAL_WINDOW_AND_COMMIT_REPAIR`.
- Code/test: `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`; `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py`.
- Formula added: `full_window_eligible_event := searchsorted(return_calendar, decision_date, side="right") <= len(return_calendar) - holding_period_sessions`; with B config this enforces `entry_idx + 60 - 1 <= max_return_idx` before the sparse engine.
- Commit rule added: `--commit-bestavail-run` writes the read-only gate first, stages B parquet and JSON, then replaces both public run outputs with rollback protection if either replacement fails.
- Repaired evidence: `selected_events_after_signal_filter=27941`; `selected_events_with_incomplete_60_session_window=0`; daily rows `975`; date range `2016-01-15..2019-11-27`; parquet SHA `10bba1fb7189af3c629a28e9ef39d674db80fe9816bbf4a13254384ea1eda01e`.
- Validation: direct `--data-gate` PASS; direct `--commit-bestavail-run` PASS; B focused pytest PASS 5/5; M6 sparse-engine pytest PASS 12/12; compile PASS.
- Boundary: B remains illustrative-only, not alpha, not tradable, and not strict M6b readiness evidence.

## 2026-06-25 V2 PEAD M6b Best-Available Option 1 Registry

- Option 1 selected: read-only gate first, standalone flagged 2015-2019 diagnostic second.
- Gate artifact: `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`.
- Code/test: `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`; `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py`.
- Required flags: `illustrative_only`, `restated_vintage`, `no_delisting`, `survivorship_biased`, `coverage_2015_2019`, `provider_limited`, `not_alpha`, `not_tradable_claim`.
- Validation: data-gate replay PASS; standalone `--run-bestavail` PASS; focused combined pytest PASS 14/14; compile PASS.

## 2026-06-24 V2 PEAD M6a PIT Walk-Forward Equity Framework Registry

- RoundID: `ROUND-20260624-V2-PEAD-M6A-PIT-WALK-FORWARD-EQUITY-FRAMEWORK`.
- ScopeID: `V2_PEAD_M6A_PIT_WALK_FORWARD_EQUITY_FRAMEWORK_FAIL_CLOSED`.
- Code path: `scripts/pead_m6_pit_walk_forward_equity_curve.py`; test path: `tests/test_pead_m6_pit_walk_forward_equity_curve.py`.
- Evidence path: `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`.
- Plan revision: M6 is split into M6a framework/input-contract fail-closed evidence and M6b data-prep/real-run. M6a is complete only as evidence scaffolding; M6b remains required before any real tradable equity curve.
- PIT formula: `timing_PIT_ok := rdq_or_release_date_aligned`; `strict_vintage_PIT_ok := timing_PIT_ok AND not_current_vintage_or_restated`. Current status is `timing_PIT_ok = true`, `strict_vintage_PIT_ok = false`, `eps_vintage = release_date_aligned_but_restated`.
- Input gate formula: `m6_run_allowed := strict_vintage_PIT_ok AND tradable_return_source AND delisting_adjusted_returns AND full_asof_liquidity_screen`. Current evidence sets this false and emits `pit_vintage_blocked`, `delisting_missing`, `tradable_return_missing`, and `tradability_liquidity_screen_missing`.
- Portfolio formula for future strict inputs: `daily_gross_return_t = sum_i weight_{i,t} * tradable_total_return_{i,t}` with +0.5 gross exposure across Q5 and -0.5 across Q1 after active-name normalization.
- Cost formula: `one_way_turnover_cost_bps = (entry_cost_bps + exit_cost_bps) / 2 + slippage_bps`; `turnover_cost_t = turnover_t * one_way_turnover_cost_bps / 10000`; `short_borrow_cost_t = short_exposure_t * daily_short_borrow_bps / 10000`; `daily_net_return_t = daily_gross_return_t - turnover_cost_t - short_borrow_cost_t`.
- Equity formula: `equity_t = equity_{t-1} * (1 + daily_net_return_t)`; `CAGR = (ending_equity / starting_equity) ** (365.25 / calendar_days) - 1`.
- Validation: M6 focused tests PASS 7/7; M5a+M6 focused tests PASS 11/11; broader PEAD regression PASS 104/104; `--validate-inputs` writes blocked evidence; `--run` returns exit code 2 when strict inputs are missing.
- Boundary: no locked D3/D2B mutation, UI, alpha label, ranking/scoring, recommendations, alerts, broker/order path, provider access, or daily return parquet publication.

## 2026-06-24 V2 PEAD Alpha Interpretation Gate Registry

- RoundID: `ROUND-20260624-V2-PEAD-ALPHA-INTERPRETATION-GATE`.
- ScopeID: `V2_PEAD_ALPHA_INTERPRETATION_GATE_DOCS_ONLY`.
- Gate path: `docs/phase_brief/v2-pead-alpha-interpretation-gate.md`.
- Evidence input: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.
- Formula change: none. Current statistic remains `R_HL,t = EW(Q5 raw return)_t - EW(Q1 raw return)_t`; regression remains `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`.
- Interpretation rule: `alpha_CT` is only a single-factor calendar-time intercept under current-vintage EPS, proxy-return, no-delisting, gross equal-weight Q5-minus-Q1 limitations.
- Gate result: current evidence supports descriptive methodology evidence only; no alpha, tradability, PIT, net-performance, causal, full-factor, or population-validity claim.
- Route formula: `next_step = owner_gate_decision -> (Path_A_descriptive_panel | Path_B_M5_PIT_data_method_upgrade)`.
- Boundary: no code, provider, data output, evidence mutation, dashboard runtime, ranking/scoring, alerts, recommendations, order path, staging, or commit.

## 2026-06-22 V2 PEAD M4A Memory-Bounded Full-Universe Expansion Registry

- RoundID: ROUND-20260622-V2-PEAD-M4A-MEMORY-BOUNDED-FULL-UNIVERSE.
- ScopeID: V2_PEAD_M4A_MEMORY_BOUNDED_D2A_D2B_EXPANSION.
- Code paths: scripts/pead_d2_return_contract.py::build_full_contract, scripts/pead_d2_return_contract.py::_full_output_sql, scripts/pead_d2b_event_window_contract.py::build_full_contract, and scripts/pead_d2b_event_window_contract.py::_full_output_sql.
- Test paths: tests/test_pead_d2_returns.py and tests/test_pead_d2b_event_window_contract.py.
- Formula change: none. D2A still defines TR_level_t = prccd_t * trfd_t / ajexdi_t, total_return_t = TR_level_t / TR_level_{t-1} - 1, and fallback price return from prccd / ajexdi, with lags scoped to (gvkey, iid).
- D2B selection formula change: none. Selection still uses the prior 20 authoritative market sessions, at least 15 finite dollar_volume observations, arithmetic mean score, and deterministic tie-break score DESC, observations DESC, normalized iid ASC, security_id ASC.
- Bounded execution formula: M4A_full_build_valid := bounded_sql_execution AND disk_spill_enabled AND row_grouped_parquet AND immutable_hash_named_output AND atomic_manifest_replace AND formulas_unchanged AND iid_semantics_unchanged.
- Evidence: focused M4A tests PASS 55/55; broader PEAD D2/D3/event-study tests PASS 79/79; latest targeted non-M4A rerun fails in execution microstructure spooler status/teardown while context-hygiene and timing checks pass; full repository pytest rerun reached 100% with no failure summary but did not return an exit code and was stopped; terminal Reviewer A/B/C unavailable due subagent usage limit.
- Boundary: no provider access, PIT EPS/population/tradable alpha claim, estimator/UI change, ranking/scoring, alert, recommendation, broker/order action, or new data artifact publication in this round.

## 2026-06-20 V2 PEAD Read-Only Evidence Dashboard Registry

- RoundID: `ROUND-20260620-V2-PEAD-READ-ONLY-EVIDENCE-DASHBOARD`.
- ScopeID: `V2_PEAD_READ_ONLY_EVIDENCE_DASHBOARD`.
- Runtime paths: `views/pead_validation_evidence.py::load_pead_validation_evidence`, `views/pead_validation_evidence.py::render_pead_validation_evidence`, `views/strategy_view.py::render_strategy_page`, and `dashboard.py::_render_strategy_page`.
- Formula change: none. The panel performs no PEAD, CAR, BHAR, quantile, HAC, or benchmark computation; it only verifies and renders locked JSON fields.
- Integrity formula: `render_allowed := file_exists AND sha256(json_bytes) == expected_sha256 AND required_schema_valid AND limitations_renderable`.
- Evidence lock: `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`, SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- Boundary: no Parquet reads, provider calls, data writes, scoring/ranking, alerts, recommendations, or broker/order actions.

## 2026-06-20 V2 PEAD D2B Terminal Reviewer Rerun Proof Registry

- RoundID: `ROUND-20260620-V2-D2B-SESSION-SPINE-FINAL-REVIEW-RERUN`.
- ScopeID: `V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE_FINAL_REVIEW`.
- Code/formula change: none. This rerun validates the existing formula registry below.
- Terminal proof formula: `V2_D2B_SESSION_SPINE_TERMINAL_PASS = focused_70_tests_PASS AND reviewer_A_PASS AND reviewer_B_PASS AND reviewer_C_PASS AND no_in_scope_Critical_or_High AND d3_artifact_absent AND forbidden_actions_zero`.
- Evidence path: `docs/saw_reports/saw_v2_d2b_session_spine_repair_rerun_20260620.md`.
- Parent matrix: 70 collected tests across `tests/test_pead_d2_returns.py`, `tests/test_pead_d2b_event_window_contract.py`, `tests/test_pead_d3_benchmark_artifact.py`, and `tests/test_pead_event_study.py`.
- Reviewer evidence: A/B/C all PASS; Reviewer B/C carry only non-blocking D3 publication-hardening follow-ups.
- Boundary: no D3 publication, no CAR/BHAR/quintile interpretation, no dashboard, no provider, no staging, no commit.

## 2026-06-19 V2 PEAD D2B Market-Session Spine Formula Registry

- RoundID: `ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR`.
- ScopeID: `V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE`.
- Code paths: `scripts/pead_d2b_event_window_contract.py::market_session_spine`, `scripts/pead_d2b_event_window_contract.py::_load_authoritative_market_sessions`, and `scripts/pead_d3_benchmark_artifact.py::_sessions_from_authoritative_source`.
- Raw date set: `S_raw = unique(D2A.date)`.
- Authoritative session set: `S_market = {d in KenFrenchDaily.return_date | min(S_raw) <= d <= max(S_raw)}`.
- Exclusion set: `S_excluded = S_raw \ S_market`.
- Current values: `|S_raw| = 2,862`, `|S_market| = 2,810`, `|S_excluded| = 52`.
- Event offset: `return_date(e,k) = kth S_market date strictly after event_date(e)`, for `k=1..60`.
- Selection window: the last 20 `S_market` dates strictly before the event; candidate eligibility and tie-break formulas are unchanged.
- D3 validation: source release/hash/member/URLs in the D2B manifest must equal the exact parsed Ken French source, then the reconstructed session hash must equal the D2B manifest hash.
- Artifact delta: D2B SHA `8e2f39... -> c3da606...`; eligible events `4,867 -> 11,450`; selected security changes `2 / 12,582`.
- Strategy handoff path: `prepare_strategy_handoff -> _prepare_selected_strategy_returns`; validate all D2A rows in chunks of at most 100,000, enforce exact normalized `(security_id,date)` uniqueness with a 128 MiB/one-thread DuckDB composite primary key, retain only selected `{security_id,date,total_return}`, and validate event metadata/timing before `strategies.pead_event_study.build_event_windows`.
- Active-scale memory evidence: loaded D2B+D2A RSS 1,222.4 MiB; post-handoff RSS 1,271.4 MiB; process peak 1,756.7 MiB; 11,450 events, 911,707 canonical returns, and 687,000 complete strategy rows.
- Boundary: no benchmark-return fill/drop/interpolation, no D3 publication, and no CAR/BHAR/quintile interpretation.

## 2026-06-18 V2 PEAD D1 Parent Closure Reconciliation

- RoundID: `ROUND-20260618-V2-D1-PARENT-CLOSURE-RECONCILIATION`.
- ScopeID: `V2_D1_PARENT_CLOSURE_EVIDENCE_RECONCILIATION`.
- Authoritative repair SAW: `docs/saw_reports/saw_v2_d1_repair_20260618.md`.
- Reconciliation SAW: `docs/saw_reports/saw_v2_d1_parent_closure_reconciliation_20260618.md`.
- Read-only evidence: Parquet SHA256 equals manifest SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Ownership: D1 builder, test, brief, and SAW files are untracked local D1-owned files; clean tracked-repo closure is not claimed.
- Limitation: current-vintage Compustat fundamentals may include restatement hindsight; strict filing-vintage PIT EPS is not established.
- Formula/code delta: none. The D1 formula registry below remains authoritative and no D1 Python was changed or executed in this closure-only pass.
- Boundary: no D1 tests/rebuild, D2/Ken French/provider work, dashboard work, strategy execution, staging, or commit.

## 2026-06-18 V2 PEAD D1 Repair Formula Registry

- RoundID: `ROUND-20260618-V2-D1-REPAIR`.
- ScopeID: `V2_D1_SUE_FORMULA_LIQUIDITY_ATOMIC_REPAIR`.
- Code path: `scripts/pead_d1_sue_builder.py`; test path: `tests/test_pead_d1_sue.py`.
- EPS basis: `adj_eps_t = numeric(epspxq_t)`. `ajexq` is not divided; `adj_eps` is a compatibility name.
- Identity order: `deduplicate(gvkey, rdq) -> exact_t4_lag -> rolling_std -> SUE`. This order prevents discarded duplicate-RDQ rows from entering lag state.
- Exact t-4 surprise: `surprise_t = adj_eps_t - adj_eps_{t-4}` only when fiscal-quarter distance equals four.
- Price-scaled SUE: `sue_price_scaled_t = surprise_t / abs(prccq_lag1_t)`.
- RDQ clipping: `sue_price_scaled_clipped_t = clip(sue_price_scaled_t, mean_rdq - 5 * std_rdq, mean_rdq + 5 * std_rdq)`; raw `sue_price_scaled` remains unchanged.
- Liquidity: `liquidity_market_cap_millions_t = prccq_lag1_t * cshoq_lag1_t`; `liquidity_pass_t = liquidity_market_cap_millions_t > 50`. `cshoq_lag1` is in millions, and the flag does not enter `valid_sue`.
- Publication: Parquet and manifest are staged to temporary siblings and promoted with replace operations.
- Artifact evidence: 346,511 rows; 233,586 valid SUE; 13,216 GVKEYs; RDQ 2015-01-02 through 2026-06-16; SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Quality gate: raw `abs(sue_price_scaled) > 5` is 441 / 233,586 valid rows (0.001887955613778223), below the 0.005 fail-closed threshold; clipped valid rows are 1,992; valid rows passing the liquidity flag are 204,227.
- Empty output guard: if no processed D1 rows remain after filtering/deduplication, the builder exits before writing either Parquet or manifest so the prior bundle is preserved.
- Limitation: D1 uses a current-vintage Compustat fundamentals extract; strict point-in-time filing-vintage EPS and freedom from restatement hindsight are not established.
- Reconciliation delta: 235,033 pre-reconciliation valid rows minus 1,447 duplicate-RDQ-contaminated lag-valid rows equals 233,586 final valid rows.
- Boundary: D2 return/IID/event-window logic, Ken French acquisition, and provider paths are not implemented in this round.

## 2026-06-18 V2 PEAD Strategy Contract Formula Registry

- RoundID: `ROUND-20260618-V2-PEAD-STRATEGY-CONTRACT`.
- ScopeID: `V2_PEAD_STRATEGY_SCHEMA_EVENT_WINDOW_STATS`.
- Code path: `strategies/pead_event_study.py`; test path: `tests/test_pead_event_study.py`.
- Event schema: `{event_id, issuer_id, security_id, event_date, sue, is_primary_security}`; events must be unique by `(issuer_id, event_date)` after upstream primary-security selection.
- Event index: `event_day_1 = min(market_session > event_date)`; `event_day_k` is the `k`th subsequent market session, not the `k`th observed security row.
- Completeness: `window_complete_e = 1[calendar_obs_e = asset_return_obs_e = H]`, additionally requiring `benchmark_obs_e = H` when benchmark adjustment is configured; `H = end_day - start_day + 1`, default `60`.
- Raw outcome: `cumulative_total_return_e = product_{d=+1..+60}(1 + r_{e,d}) - 1`.
- Abnormal return: `AR_{e,d} = r_{e,d} - r^b_{e,d}`.
- CAR: `CAR_e = sum_{d=+1..+60} AR_{e,d}`.
- BHAR: `BHAR_e = product_{d=+1..+60}(1 + r_{e,d}) - product_{d=+1..+60}(1 + r^b_{e,d})`.
- Quantiles: SUE percentile ranks are computed inside explicit event-date cohorts; incomplete events and undersized cohorts are not assigned.
- Spread inference: `spread_c = mean(outcome | Q_high,c) - mean(outcome | Q_low,c)`; `t_HAC = mean(spread_c) / HAC_SE(mean(spread_c))`.
- Boundary: no Data-stream builder/artifact/provider code changed; synthetic tests do not authorize real-alpha interpretation.

## 2026-06-03 V2-D0.4C Local Read-Only Permission Probe Approval

- RoundID: `ROUND-20260603-V2-D0-4C-LOCAL-READ-ONLY-PERMISSION-PROBE-APPROVAL`.
- ScopeID: `V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL_DOCS_ONLY`.
- Artifacts: `docs/authorization/V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL.md`; `docs/authorization/V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL.json`.
- Status: `PASS_DOCS_ONLY_APPROVAL`; `LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVED_FOR_LOCAL_HUMAN_RUN`; `WRDS_OUTPUT_BLOCKED`; `DISCOVERY_BLOCKED`; `FORMAL_PERMISSION_TRUTH_NOT_CLOSED`.
- Formula: `D0_4C_VALID = execution_in_d0_4c_false AND exact_five_rows AND all_rows_probe_approved_not_executed AND all_approval_ref_null AND wrds_output_blocked AND discovery_blocked AND data_output_blocked`.
- Next packet: `V2_D0_4D_LOCAL_HUMAN_PROBE_EXECUTION_PACKET`, queued but not run.
- Boundary: no credential read, `secret.txt` read, Codex/subagent login, WRDS execution in D0.4C, discovery helper, schema, row count, sample, snapshot, data output, runtime write, approval_ref change, SafeBoot, or BootReady.

## 2026-06-03 V2-D0.4B WRDS Local Auth Method Confirmed

- RoundID: `ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED`.
- ScopeID: `V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION`.
- Artifacts: `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.md`; `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.json`.
- Formula change: policy/status formulas only; no `.py` strategy, scoring, replay, optimizer, provider, data-readiness, boot-status, or research-validity code changed.
- Required language: `WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed.`
- Formula: `V2_D0_4B_VALID = local_auth_method_user_attested_available AND actual_login_verified_by_agent_false AND credentials_not_read AND secret_txt_not_used AND formal_approval_ref_null AND permission_truth_not_closed AND wrds_execution_governance_blocked_until_probe_approval`.
- Row formula: `row_valid = probe_plan_status == probe_plan_pending AND approval_status == not_approved AND approval_ref == null` for `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`.
- Boundary: no secret.txt/credential read or use, WRDS/provider execution, schema discovery, row counts, sample rows, snapshots, data output, runtime/dashboard/scoring/broker writes, approval_ref fabrication, or row approval is authorized.

## 2026-06-02 V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping

- RoundID: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING`.
- ScopeID: `V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING`.
- Artifact: `v2_discovery/data_lab/permission_truth.py`.
- Test artifact: `tests/test_v2_wrds_permission_truth_scope.py`.
- Evidence: `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_truth_scope.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` -> PASS, 51 passed.
- Evidence: `.venv\Scripts\python -m compileall v2_discovery\data_lab -q` -> PASS.
- Formula: `TODO_MATRIX_001_RESOLVED = permission_truth_artifact_exists AND exact_five_v2_d0_1_rows AND default_status_pending AND row_table_approval_ref_required_for_approved AND approved_allowed_uses_exactly_provenance_contract AND separate_pead_starter_scope`.
- Formula: `approved_status_valid(row) = row.approval_ref_present AND row.allowed_uses == ["provenance_contract"]`.
- Formula: `ibes_det_epsus_scope = {v2_d0_1: pending, pead_v2_001_starter: not_requested}`.
- Boundary: no WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, legacy cleanup, public/main closure, or V2 validity/C3 lock claim is authorized.

## 2026-06-02 V2-D0.1 Scope and Clean-Room Runtime Decision

- RoundID: `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME`.
- ScopeID: `V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION`.
- Handover: `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`.
- Formula change: policy formulas only; no `.py` strategy, scoring, replay, optimizer, data-readiness, boot-status, or research-validity code changed.
- `v2_d0_1_entitlement_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `pead_v2_001_compustat_starter_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq}`.
- `ibes_det_epsus_v2_d0_1_status = pending_once_requested`.
- `ibes_det_epsus_pead_v2_001_starter_scope = not_requested`.
- `cleanroom_runtime_schema_registry_default = excluded`.
- `TODO_PEAD_DECISION_001 = RESOLVED`.
- `TODO_CLEANROOM_RUNTIME_001 = RESOLVED`.
- `v2_d0_1_scope_artifact_needs_dual_status = 1` until `v2_d0_1_entitlement_status` and `pead_v2_001_starter_scope` are represented separately or equivalent builder/override exists.
- Boundary: no WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized.

## 2026-06-02 V2-D0.1 Expert 1-6 Follow-Up Reconciliation

- RoundID: `ROUND-20260602-V2-D0-1-EXPERT-1-6-FOLLOWUP`.
- ScopeID: `V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION`.
- Handover: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`.
- Formula change: policy formulas only; no `.py` strategy, scoring, replay, optimizer, data-readiness, boot-status, or research-validity code changed.
- Agreement/confidence: Data/WRDS `AGREE_HIGH 8.5/10`; Backend/Data `AGREE_HIGH 9/10`; Architecture/Governance `AGREE_HIGH 8.5/10`; Quant Research `PARTIAL_AGREE_HIGH 7.5/10`; Research Validity `AGREE_HIGH 8.5/10`; Security/Ops `AGREE_HIGH 9/10`.
- `v2_d0_1_default_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq, ibes.det_epsus}`.
- `pead_compustat_starter_rows = {crsp.dsf, crsp.stocknames, crsp.ccmxpf_linktable, comp.fundq}`.
- `pead_ibes_primary_rows = v2_d0_1_default_rows`.
- `pead_starter_decision_open = 1` until I/B/E/S analyst-surprise PEAD vs Compustat-rdq PEAD starter is resolved.
- `approval_ready = entitlement_evidence_present AND explicit_non_secret_approval_text_present`.
- `hac_lag = min(63, max(5, primary_holding_window_trading_days))`.
- `research_valid_pead = 1` iff canonical PEAD evidence exists, `C3_LOCK_PEAD_V2_001_v1` exists, HAC LCB95(delta)>0, annualized net alpha delta>=2%, FDR q<=0.05, DSR>=0.95, PBO<=0.10, base and 2x cost stress pass, PEAD slippage stress passes, OOS/walk-forward evidence exists, PIT event timestamp leakage audit passes, negative controls pass, robustness passes, concentration checks pass, and reproducibility rerun passes.
- TODOs: `TODO-ENTITLEMENT-001`, `TODO-APPROVAL-001`, `TODO-PEAD-DECISION-001`, `TODO-CLEANROOM-001`, `TODO-LEGACY-WRDS-001`, `TODO-VALIDITY-001`, `TODO-PUBLIC-MAIN-001`.
- `TODO-MATRIX-001`: `v2_d0_1_permission_truth_artifact_valid = 1` only if approved rows use `allowed_uses=["provenance_contract"]`; the V2-D0 default matrix output is not a V2-D0.1 approved-row artifact unless overridden.
- Boundary: no WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized.

## 2026-06-02 V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates

- RoundID: `ROUND-20260602-V2-D0-1-EXPERT-1-6-TODO-GATES`.
- ScopeID: `V2_D0_1_EXPERT_1_6_AGREEMENT_TODO_GATES`.
- Formula change: none. No strategy formula, scoring formula, replay formula, optimizer formula, data-readiness formula, boot-status formula, or research-validity formula changed in this docs-only truth refresh.
- Agreement rating record: `Expert 1=AGREE_HIGH; Expert 2=AGREE_HIGH; Expert 3=AGREE_HIGH; Expert 4=AGREE_HIGH; Expert 5=AGREE_HIGH; Expert 6=AGREE_HIGH`; numeric source values were not supplied and must not be invented.
- V2-D0.1 authority formula: `approval_ready = entitlement_evidence_present AND explicit_non_secret_approval_text_present`.
- Backend/Data status: row-level validator `PATCH_RESOLVED` after tests; it is contract evidence only and does not prove provider/probe/snapshot execution.
- Security status: approval text is required; legacy WRDS helper surfaces remain quarantine risk until separately audited or retired.
- Quant Research conditional next: `PEAD_V2_001_BOUNDARY_PACKET` only after WRDS/PIT authority.
- Research Validity status: no V2 alpha is currently `research_valid`; `V2_ALPHA_VALIDITY_PACKET` template is needed before any V2 alpha validity claim.
- Boundary: no WRDS/provider access, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, or BootReady is authorized.

## 2026-06-01 V2 Alpha Factory Immediate Todo Directive

- RoundID: `ROUND-20260601-V2-ALPHA-FACTORY-DIRECTIVE`.
- ScopeID: `SCOPE-DOCS-ONLY-IMMEDIATE-TODO-FIRSTS`.
- Packet path: `docs/architecture/v2_alpha_factory_immediate_todo_directive_20260601.md`.
- Formula change: none. No strategy formula, scoring formula, replay formula, optimizer formula, data-readiness formula, boot-status formula, or research-validity formula changed in this docs-only directive intake.
- Immediate TODO-first order:
  - WRDS Permission + PIT Snapshot + Provenance Layer.
  - PEAD Variant Factory.
  - Corporate Actions / Capital Return Edge Lab.
  - Meta-labeling / Edge Survival Model.
  - Orbis/BvD Private Company Network Edge.
- Deferred/blocked lead directions: LLM market-news agents, DRL allocator work, and live routing.
- Logic chain: approved source access -> PIT/provenance snapshot -> V2 research-only feature families -> proxy/robustness evidence -> candidate packet -> requested V1 official backtest.
- Storage note: proposed SQLite candidate storage is not approved; repo constraints require Parquet/DuckDB-compatible storage unless explicit SQLite approval is granted.
- Boundary: no WRDS/provider access, snapshot generation, candidate ranking/scoring, promotion, live trading, broker/order execution, alerts, recommendations, autonomous allocation, runtime behavior, or BootReady claim is authorized by this docs-only directive.

## 2026-05-28 Governed Data Source Provenance Intake

- RoundID: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`.
- ScopeID: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`.
- Packet path: `docs/architecture/governed_data_source_provenance_intake_20260528.md`.
- Formula change: none. No strategy formula, scoring formula, replay formula, optimizer formula, data-readiness formula, or boot-status formula changed in this docs-only source-provenance intake refresh.
- Provenance registry note: future strict data recovery must record source location, source owner/approval, source date/as-of coverage, license/access note, expected schema, generator command, output path, manifest path, SHA256 policy, validation command, and rollback/removal rule before generation.
- Current state: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.
- BlockingReason: strict data readiness still lacks approved source provenance, manifests, hashes, generated artifacts, and validation proof.
- Intake lines documented:
  - prices source -> `data/processed/prices.parquet` -> `data/processed/prices_tri.parquet`.
  - ticker/security master source -> `data/processed/tickers.parquet`.
  - WRDS/R3000 membership source -> `data/processed/universe_r3000_daily.parquet`.
  - Rule100 history source/generator -> `data/processed/rule100_softmax_v1_history.csv`.
- Existing generator/gap notes are cautious only: `core/etl.py` is legacy/local-bound for prices; `data/build_tri.py` exists and depends on prices; no complete governed security master generator is confirmed; `data/r3000_membership_loader.py` exists as WRDS-style PIT loader but lacks approved WRDS provenance; `scripts/build_synthetic_r3000_universe.py` is not strict source; `scripts/rule100_softmax_v1_audit.py` has a partial history writer but still needs source/generator approval and manifest/hash.
- Correct next step: approve source provenance first; then approve bounded offline regeneration; then rerun strict data readiness and strict GitHub-aligned boot proof.
- Forbidden actions: no boot_preflight.py patch; no DataReadyStrict weakening; no data/processed generation from incomplete provenance; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.

## 2026-05-28 Governed Data Source Acquisition / Bounded Regeneration Planning

- RoundID: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`.
- ScopeID: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`.
- Packet path: `docs/architecture/governed_data_source_acquisition_20260528.md`.
- Formula change: none. No strategy formula, scoring formula, replay formula, optimizer formula, data-readiness formula, or boot-status formula changed in this docs-only source-acquisition planning refresh.
- Current state: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED; RuntimeBootStatus local / ignored / not commit evidence.
- BlockingReason: required canonical data artifacts are absent/ignored/local-governed and not backed by approved source manifests or generators.
- Dependency order documented:
  - raw prices CSV/source -> `data/processed/prices.parquet`.
  - `data/processed/prices.parquet` -> `data/processed/prices_tri.parquet`.
  - approved ticker/security master source -> `data/processed/tickers.parquet`.
  - approved WRDS/R3000 membership source -> `data/processed/universe_r3000_daily.parquet`.
  - approved Rule100 replay/history source or generator -> `data/processed/rule100_softmax_v1_history.csv`.
- Existing generator/gap notes are cautious only: `core/etl.py`, `data/build_tri.py`, `scripts/build_synthetic_r3000_universe.py`, and `scripts/rule100_softmax_v1_audit.py` were statically identified, but none is approved or run by this round.
- Recommended next step: choose A trusted external governed bundle, B source acquisition + bounded offline regeneration planning, or C quarantine BootReady; recommended B unless a trusted governed bundle already exists.
- Forbidden actions: no boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.

## 2026-05-28 Governed Data Artifact Authorization

- RoundID: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`.
- ScopeID: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`.
- Packet path: `docs/architecture/governed_data_artifact_authorization_20260528.md`.
- Formula change: none. No strategy formula, scoring formula, replay formula, optimizer formula, data-readiness formula, or boot-status formula changed in this docs-only authorization refresh.
- Gate truth: GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS/degraded; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.
- Explicit artifact authorization requirements:
  - `data/processed/prices_tri.parquet`: approved offline total-return source or trusted bundle, schema/freshness/hash/manifest/owner approval, rollback with manifest removal.
  - `data/processed/prices.parquet`: approved offline adjusted/local price source or trusted bundle, schema/freshness/hash/manifest/owner approval, rollback with manifest removal.
  - `data/processed/tickers.parquet`: approved offline identifier map or trusted bundle, coverage/conflict checks, hash/manifest/owner approval, rollback with manifest removal.
  - `data/processed/universe_r3000_daily.parquet`: approved offline PIT membership source or trusted bundle, PIT coverage/duplicate checks, hash/manifest/owner approval, rollback with manifest removal.
  - `data/processed/rule100_softmax_v1_history.csv`: approved offline Rule100 evidence history or trusted bundle, schema/evidence-window/method provenance/hash/manifest/owner approval, rollback with manifest removal.
- Local artifacts and dirty context are not clean GitHub truth and are not BootReady evidence.
- Inherited boot-control diffs remain unresolved, out-of-scope for this docs-only packet, and not evidence for or against governed artifact authorization, DataReadyStrict, or BootReady.
- Recommended next step: approve bounded offline regeneration authorization or approved external bundle; otherwise quarantine BootReady.
- Forbidden actions: no boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.

## 2026-05-15 Dashboard Replay Aux Weight Semantics + Stacked Timeline

- Implementation files: `dashboard.py`, `strategies/strategy_replay.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_strategy_replay.py`.
- Diagnosis: Portfolio & Allocation was structurally using one `DashboardReplayContext`, but ENTER/EXIT and Buy/Sell rows could still display auxiliary `weight` fields from lifecycle/event/decision context rather than the daily selected-method replay `target_weight` used by the timeline and latest snapshot.
- Weight alignment formula: `aux.target_weight = replay_df.target_weight where normalize(aux.date) = normalize(replay_df.date) and upper(aux.ticker) = upper(replay_df.ticker)`; `aux.audit_weight = original aux weight` when present; visible aux `weight` is set back to `target_weight` for display compatibility.
- Backend normalization rule: `strategies.strategy_replay._normalize_context_frame(...)` now emits replay-derived `target_weight` for context rows and preserves legacy `weight` only as audit metadata.
- Dashboard normalization rule: saved-artifact and transitional contexts pass event/decision rows through `_align_context_weights_to_replay(...)` before rendering or cache storage.
- Visualization rule: Strategy Replay Timeline now renders a stacked step-area allocation chart over replay `target_weight`, with `CASH` muted and equities ordered by latest weight/active days.
- Fail-soft rule: partial saved/transitional schemas no longer crash the Strategy Replay section when event rows lack `action` or latest snapshot rows lack optional display metadata.
- Boundary: no replay engine promotion, provider ingestion, canonical market-data write, broker/live trading, alerting, ranking, scoring, recommendation, autonomous allocation, or strategy promotion was added.
- Evidence: `.venv\Scripts\python -m py_compile dashboard.py strategies\strategy_replay.py tests\test_dash_2_portfolio_ytd.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py` PASS; targeted aux/timeline/fail-soft regressions PASS, including executable Plotly trace assertions for stacked `hv` allocation areas; affected backend replay suite PASS, 80 tests; affected frontend replay suite PASS, 134 tests; latest focused dashboard file PASS, 66 tests.

## 2026-05-15 Dashboard Replay Horizon-Aware Asset Universe Fix

- Implementation files: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`.
- Diagnosis: the Portfolio page had one mechanical replay source, but the source was under-scoped to the latest signed current allocation assets. A 1Y replay could therefore exclude MU after its current state became flat, even though MU BUY/SELL rows existed inside the selected replay horizon.
- Asset-union rule: `DashboardReplayRequest.replay_assets = current signed PortfolioReplaySelection assets + mapped ENTER/EXIT or BUY/SELL context tickers in the selected replay window + Rule100 history tickers in the selected replay window`.
- Allocation split rule: `DashboardReplayRequest.allocation_assets` remains the current signed selection and is the only asset list used for PIT price loading, coverage pre-gate row emission, and non-Rule100 optimizer allocation. History-only replay assets are appended after backend bundle construction as zero-weight `context_only` rows so strict context normalization can keep their decision rows without making them allocatable.
- Cache identity rule: dashboard replay cache signatures include both `replay_assets` and `allocation_assets`, so the same horizon union cannot be reused when a context-only ticker becomes a current allocatable ticker.
- Boundary rule: `PortfolioReplaySelection` itself remains the signed current allocation handoff, so MU/NVDA/SNDK are not forced into current positive-weight allocation merely because they appear in lifecycle or thesis history.
- Single-source rule: `_normalize_context_frame(...)` remains strict; replay context rows are kept because the replay frame is now horizon-aware and contains the relevant historical asset rows.
- Evidence: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` PASS; targeted MU/context/coverage/cache regressions PASS, 4 passed; `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` PASS, 61 passed; `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay.py tests\test_strategy_replay_coverage.py -q` PASS, 71 passed.

## 2026-05-15 Dashboard Replay Horizon Superset Cache Fix

- Implementation files: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`.
- Diagnosis: after building a wider daily replay such as `Max`, switching to a shorter horizon such as `1Y` still called `_ensure_daily_portfolio_replay_context(...)`, entered the `Building daily portfolio replay source...` spinner, and rebuilt the transitional replay because the existing cache validation required exact `replay_dates` equality and was only consulted by the chart fallback path.
- Cache reuse rule: an in-session daily `DashboardReplayContext` may serve a shorter horizon only when method, cap, controls, signed replay assets, sampling, and dashboard data signature match after removing `replay_dates`, and the requested daily dates are a subset of both `context.replay_dates` and actual `context.replay_df["date"]`.
- Scoping rule: reused superset contexts are returned as horizon-scoped views, with replay rows restricted to exact requested daily dates and event/decision rows filtered to the requested date window, so a `1Y` UI selection does not render a `Max` timeline.
- Boundary: saved replay artifact reads still require exact `dashboard_cache_signature`; this change is only an in-session daily replay reuse policy for already-built dashboard contexts.
- Evidence: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` PASS; targeted superset-cache regressions PASS, 3 passed; `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` PASS, 56 passed; `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay_coverage.py -q` PASS, 50 passed.

## 2026-05-15 Max Replay Timeline Sampling Fix

- Implementation files: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`.
- Bug fixed: max-window Strategy Replay timeline sampling grouped daily replay dates by ISO year/week, then called `.normalize()` on the grouped pandas `Series`; pandas exposes date normalization for Series through `.dt.normalize()`.
- Sampling formula: `weekly_display_dates = normalize(last(date) grouped by (ISO year, ISO week)) union normalize(final_daily_date)`.
- Behavior rule: weekly timeline sampling remains a display-only transform over the already-built daily replay rows; it does not create a second replay request and cannot feed Portfolio Performance.
- Evidence: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` PASS; `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay tests\test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_is_display_only_from_daily_replay -q` PASS, 2 passed; `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` PASS, 53 passed.

## 2026-05-15 Dashboard Batched Replay Runtime Fix

- Implementation files: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`.
- Behavior rule: Portfolio replay still requests the selected UI horizon only (`YTD`, `1Y`, `3Y`, `5Y`, or `Max`); YTD does not intentionally request a five-year date list.
- Performance fix: transitional dashboard replay now bulk-loads PIT price/membership data once with `load_batched_pit_replay_data(...)`, wraps it with `build_batched_pit_input_loader(...)`, and filters each PIT input back to the signed `PortfolioReplaySelection` assets.
- Boundary: saved replay artifacts remain exact-signature consumers; a future 5Y superset artifact needs separate acceptance logic before it can satisfy shorter YTD/1Y requests.
- Evidence: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py` PASS; `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py -q` PASS, 89 passed; `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q` PASS, 12 passed; Streamlit readiness on `http://127.0.0.1:8509` PASS, HTTP 200.

## 2026-05-14 Portfolio Single-Source Replay Page

- Implementation files: `dashboard.py`, `views/optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `tests/test_policy_target_timeline_apptest.py`, `tests/test_position_lifecycle.py`.
- Page coordinator rule: `/portfolio-and-allocation` renders optimizer controls first, then builds one daily `DashboardReplayContext`, then feeds allocation snapshot, Portfolio Performance, Strategy Replay Timeline, ENTER/EXIT Events, Latest Buys/Sells, and Buy/Sell Decision Log from that context.
- Allocation display rule: the top allocation display is now `Allocation (Latest Daily Replay Snapshot)` from `DashboardReplayContext.latest_snapshot`; optimizer output on this page is controls-only and does not render a separate allocation evidence panel.
- Performance rule: `_render_portfolio_ytd_chart(...)` only compounds `portfolio_return` from a valid daily replay context; non-daily or missing replay context renders "Daily replay performance unavailable" and does not fall back to optimizer weights, local weighted prices, live weighted prices, or equal-weight local prices.
- Replay identity rule: replay-facing surfaces expose the same `run_id`, `source_id`, `method_id`, and `date_window` through `DashboardReplayContext`.
- Timeline sampling rule: weekly/sampled display is derived only by `_sample_replay_timeline_from_daily(...)` from daily replay rows; no sampled replay request is built for Portfolio Performance or Strategy Replay source evidence.
- Sampling formula: `weekly_display_dates = last(date) grouped by (ISO year, ISO week)` with the final daily date always retained; this is a visualization transform only.
- Event/decision UI rule: the duplicate `Trade Event Log` expander/table is removed; ENTER/EXIT Events remains the event visualization with date/ticker/action/weight/reason hover context, scoped to the selected Portfolio horizon.
- Latest buys/sells rule: `Latest Buys/Sells` is a filtered `BUY`/`SELL` view of `DashboardReplayContext.buy_sell_decisions` / `bundle.decision_rows`; no separate latest-trades loader, cache, or fallback source exists in the render path.
- Source guard: focused tests reject direct `pd.read_json`, `read_lifecycle_log`, lifecycle JSONL constants, or latest-trades cache reads inside the Portfolio render path outside the bundle-building boundary.
- Evidence: `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py` PASS; `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q` PASS, 178 tests; Streamlit smoke `http://127.0.0.1:8526/portfolio-and-allocation` PASS, HTTP 200.

## 2026-05-14 Saved Selected-Method Replay Artifact Reader + Budget

- Implementation files: `strategies/strategy_replay.py`, `scripts/build_strategy_replay_artifact.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_strategy_replay_coverage.py`.
- Reader API: `read_selected_method_replay_artifact(path, method=..., controls=..., start_date=..., end_date=..., as_of_range=..., input_signatures=..., source_file_signatures=..., budget_policy=...) -> SelectedMethodReplayResult`.
- Result contract: `SelectedMethodReplayResult.available` is true only when parquet + manifest validate as one bundle and reconstruct a `StrategyReplayBundle`; invalid/stale/over-budget reads return `status="unavailable"`, an explicit `reason`, and an empty `replay` frame.
- Manifest bundle rule: saved selected-method replay output manifests now expose top-level `input_signatures`, `controls_signature`, and `timing` in addition to `run_metadata`, `run_id`, `source_id`, `method_id`, `row_count`, `row_counts`, `status_counts`, and `date_window`.
- Manifest identity rule: top-level manifest `run_id`, `source_id`, and `method_id` must be non-empty strings after trimming; blank manifest identity is rejected before optional caller-supplied expected ids or parquet/manifest equality can make the bundle look valid.
- Freshness rule: reader rejects mismatched method, controls, requested/replay date window, input signatures, source file signatures, run id, source id, artifact type, schema, and manifest/parquet row/status/date-window drift.
- Control-content rule: DataFrame controls, including Rule100 candidate frames, carry a deterministic content hash so same-shape/date candidate edits cannot reuse stale replay artifacts.
- Identity rule: every parquet row must carry exact non-null `artifact_scope`, `run_id`, `source_id`, `method`, and valid `row_type` identity matching the manifest.
- Timing rule: manifest and run-metadata timing must include finite non-negative `elapsed_ms`; malformed timing fails closed before budget comparison.
- Budget policy: `ReplayBudgetPolicy(cold_start_max_seconds, rerun_cache_max_seconds, max_rows, max_dates, max_elapsed_ms)` gates both saved-artifact reads and `build_selected_method_replay_with_budget(...)`.
- CLI rule: `scripts/build_strategy_replay_artifact.py --artifact-kind selected-method-output` uses `build_selected_method_replay_with_budget(...)` and exposes `--budget-max-rows`, `--budget-max-dates`, and `--budget-max-elapsed-ms` alongside the existing `--budget-max-seconds`.
- Fail-closed rule: over-budget or invalid reads/builds do not return stale replay output; callers must treat `available=False` as unavailable/cash-closed state and not carry forward prior weights.
- Evidence: `.venv\Scripts\python -m py_compile strategies\strategy_replay.py scripts\build_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py` PASS; `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py::test_read_selected_method_replay_artifact_rejects_blank_manifest_identity_without_expected_ids -q` PASS, 3 tests; `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12` PASS, 79 tests.

## 2026-05-14 Endpoint Freshness Contract Centralization

- Implementation files: `core/data_orchestrator.py`, `strategies/portfolio_universe.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_portfolio_universe.py`.
- Shared endpoint helper: `price_column_latest_date(prices, column) = max(valid_positive_price_date_column)`.
- Shared freshness predicate: `price_endpoint_is_fresh(endpoint, required_latest, max_staleness_days=0) = (endpoint is present) and ((required_latest is absent) or ((required_latest - endpoint).days <= max_staleness_days))`.
- Strict-default rule: core benchmark/YTD/overlay paths keep strict freshness by using `max_staleness_days=0` unless a caller explicitly chooses a tolerance.
- Scaled-overlay evidence rule: `scale_live_overlay_to_local(...)` requires same-column local/live overlap; no-overlap live rows cannot be scaled from first-live to last-stale-local and then treated as allocation or benchmark evidence.
- Selected-overlay evidence rule: optimizer selected-price refresh must pass the shared endpoint freshness filter after any live overlay stitch, so unresolved stale selected assets are dropped rather than treated as current allocation evidence.
- Benchmark-overlay evidence rule: benchmark live overlays use the same overlap-anchor invariant; a stale benchmark ticker with no overlap is dropped while fresh local peers remain available.
- Universe policy rule: `strategies.portfolio_universe.build_optimizer_universe(...)` imports the shared core endpoint helpers and passes `OptimizerUniversePolicy.max_endpoint_staleness_days`.
- Drift guard: `tests/test_portfolio_universe.py::test_portfolio_universe_uses_shared_endpoint_freshness_contract` rejects reintroduced private endpoint/tolerance helper clones.
- Evidence: focused centralization regressions PASS, 5 tests; affected stale-data suite PASS, 110 tests.

## 2026-05-14 Dashboard Backend Bundle Integration Verification

- Implementation files verified: `dashboard.py`, `strategies/strategy_replay.py`, `core/data_orchestrator.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `tests/test_position_lifecycle.py`, `tests/test_policy_target_timeline_apptest.py`.
- Dashboard bundle rule: `_build_dashboard_strategy_replay_context(...)` imports and calls `strategies.strategy_replay.build_selected_method_replay(...)`.
- PIT input-loader rule: dashboard passes `prices=None` and `input_loader=_dashboard_input_loader`; the loader calls `_load_dashboard_strategy_replay_inputs_cached(...)`, which delegates to `load_strategy_replay_inputs(..., end_date=as_of_date, universe_mode="r3000_pit")`.
- Shared context rule: Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log rows, and `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY` are sourced through `DashboardReplayContext`.
- Source-mode boundary: the dashboard path remains `source_mode="transitional_build"` because it builds the backend bundle directly; saved artifact-reader consumption is a separate future architecture slice.
- Evidence: focused replay/dashboard suite PASS; scoped compile PASS; full pytest PASS; Streamlit readiness smoke `http://127.0.0.1:8520/portfolio-and-allocation` PASS with HTTP 200.
- Open risks: saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future work; no promotion claim is made without same-window/same-cost/same-engine baseline delta evidence.

## 2026-05-14 Replay Coverage Contract Audit Fix

- Implementation files: `strategies/strategy_replay.py`, `strategies/optimizer.py`, `tests/test_strategy_replay_coverage.py`, `tests/test_optimizer_core_policy.py`.
- Coverage metadata rule: `_build_run_metadata(..., coverage_plan=plan)` writes contiguous covered/uncovered intervals to `date_window["coverage_segments"]` as `{start, end, covered}` records.
- Unavailable reason rule: uncovered dates from `_compute_coverage_plan(...)` emit `reason=f"input_unavailable:{cov.reason}"`, preserving causes such as `membership_gap_exceeded`, `no_priced_members`, and `candidate_coverage_not_started`.
- Uncovered-date batching rule: `_build_replay_from_input_loader(...)` accumulates cash-closed `input_unavailable:*` rows in memory and flushes them through `_attach_replay_performance(...)` once per contiguous unavailable run instead of one frame per date.
- Row-heavy unavailable rule: `_cash_closed_rows_fast(...)` preserves explicit member rows for `no_priced_members` windows without the pandas Series/clip/reindex overhead of the generic weighted-row builder.
- Performance alignment rule: weights emitted for allocation date `t` earn the next tradable return, not the return ending at `t`; `_returns_for_allocation_dates(...)` shifts realized returns back to the preceding allocation date.
- Run-level equity rule: loader-based replay concatenates raw rows first and then runs `_attach_replay_performance(...)` once against combined returns, so `portfolio_equity` is continuous across the full replay window.
- Small-frame performance rule: `_attach_replay_performance(...)` uses a direct `(date, permno/ticker) -> return` lookup for tiny PIT return frames and treats a real `0.0` permno return as a match, not a missing value; larger replay frames still use the vectorized stack/merge path.
- Inverse-volatility fast-path formula: `target_i = (1 / vol_i) / sum_j(1 / vol_j)`. If `max_i(target_i) <= max_weight`, the target is already feasible for `min ||w - target||^2` under long-only full-investment cap constraints, so diagnostics return `solver_status="deterministic_inverse_volatility_target"` without SLSQP.
- Context bootstrap source rule: `scripts/build_context_packet.py` treats `docs/context/*_current.md` truth surfaces as context-source candidates when they contain a complete `New Context Packet`; those sources sort before same-phase handovers, so `planner_packet_current.md` can supersede stale handoff packets without requiring a new handover file.
- Context baseline rule: new current-truth bootstrap packets must preserve closed baseline tokens such as `D-353` and `R64.1` when existing hygiene tests still use them as anti-regression anchors.
- Test hygiene: the duplicate shadowed coverage-segments and daily-scale tests were removed; pytest now collects one canonical definition for each.
- Evidence: strategy replay coverage PASS, 11 tests; affected replay/optimizer suite PASS, 68 tests; full pytest PASS.

## 2026-05-13 Selected-Method Replay Source Evidence Handoff

- Implementation files: `strategies/strategy_replay.py`, `dashboard.py`, `tests/test_strategy_replay.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_replay_non_cash_closed.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `tests/test_position_lifecycle.py`, `tests/test_policy_target_timeline_apptest.py`.
- Backend invariant: `build_selected_method_replay(method, controls, prices, ticker_map, sector_map, as_of_range, event_context=..., decision_context=...) -> StrategyReplayBundle(replay, event_context, decision_context)`.
- Shared target-weight source: `StrategyReplayBundle.replay` is produced by `build_strategy_replay(...)`; Rule of 100 and optimizer methods share `REPLAY_COLUMNS`, required `CASH` rows, `cap_used`, `cap_source`, `source`, `status`, and `reason`.
- Durable evidence artifact: `write_selected_method_replay_artifact_atomic(...)` writes one selected-method replay output parquet plus manifest with `run_id`, `source_id`, `method_id`, date window, input signatures, row/status counts, and timing under `data/runtime_cache/strategy_replay`.
- Bundle atomicity rule: artifact parquet and manifest JSON are both staged before promotion; if manifest promotion fails after parquet promotion, the writer rolls back the parquet path so no orphan replay artifact remains.
- Performance derivation formula: `return_contribution_{i,t} = target_weight_{i,t} * asset_return_{i,t}`; `portfolio_return_t = sum_i(return_contribution_{i,t})`; `portfolio_equity_t = cumprod(1 + portfolio_return_t)`.
- Timeframe/PIT formula: for each display/replay date `t`, dashboard replay loads `load_strategy_replay_inputs(as_of_date=t, end_date=t, universe_mode="r3000_pit")`; event and decision context then filters to `replay_start <= date <= replay_end`, selected method, and replay tickers.
- Latest snapshot/YTD rule: `_prime_strategy_replay_latest_snapshot_for_ytd()` builds the latest selected-method replay date; `_current_optimizer_weights()` then prefers `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY` before legacy optimizer weights.
- Latest-trades-default UX rule: `_load_dashboard_replay_buy_sell_decisions_cached(...)` sorts compact buy/sell rows by `date` descending; `_render_buy_sell_decision_log(context)` renders that latest-first audit table before the heavier replay timeline and keeps the "replay audit only" / "not live orders or trade signals" boundary.
- Fail-closed rule: missing/failed PIT dates emit `cash_closed` rows with explicit reason; downstream surfaces must not carry forward stale weights, annotations, or buy/sell rows as selected-method evidence.
- Rollback note: disable dashboard context consumption and remove the `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY` preference to return Portfolio Performance to legacy optimizer weights; do not rewrite canonical market data or lifecycle ledgers during rollback.
- Open risks: saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future work; dashboard backend-bundle consumption and full regression/runtime smoke were verified on 2026-05-14.
- Evidence: selected-method artifact suite PASS, 16 tests; strategy replay suite PASS, 21 tests; focused dashboard shared replay suite PASS, 89 tests; scoped compile PASS for runtime/test files listed above; 2026-05-14 full pytest and runtime smoke PASS.

## 2026-05-13 Backend Shared Selected-Method Replay Source

- Implementation files: `strategies/strategy_replay.py`, `tests/test_strategy_replay.py`, `docs/lessonss.md`.
- Public API: `build_selected_method_replay(method, controls, prices, ticker_map, sector_map, as_of_range, event_context=..., decision_context=...)` returns `StrategyReplayBundle(replay, event_context, decision_context)`.
- Shared frame source: the bundle calls `build_strategy_replay(...)`; Rule of 100 and non-Rule100 optimizer methods therefore emit the same `REPLAY_COLUMNS` schema.
- Daily portfolio output: every replay date emits target-weight rows plus `CASH`, with `cap_used`, `cap_source`, `source`, `status`, and `reason`.
- Performance path: replay rows now include `asset_return`, `weight_for_return`, `return_contribution`, `portfolio_return`, and `portfolio_equity`, so YTD/performance can be derived from replay output without reading optimizer session weights.
- Context interface: event annotations and buy/sell decision rows are optional typed context frames. They are method/window/ticker filtered; absent context returns an explicit empty `StrategyReplayContext` with status/reason.
- Fail-closed guard: missing/failed replay dates continue to emit `cash_closed` rows and do not carry stale weights.
- Boundary: no dashboard rewiring, no broker/live trading, no provider ingestion, no canonical market-data writes, no rankings, and no recommendations.
- Evidence: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q` PASS, 27 passed; `.venv\Scripts\python -m pytest tests\test_replay_non_cash_closed.py -q` PASS, 2 passed.

## 2026-05-13 Visible Rule100 / QQQ / Buy-Sell Replay Audit

- Runtime visible audit: fresh Streamlit run on `http://localhost:8509/` renders `Rule of 100` as the selected Portfolio Optimizer method, `max_weight=0.35`, and Strategy Replay caption `Replaying: Rule of 100 | max_weight=35%`.
- Benchmark visibility: Portfolio Performance renders `SPY +11.07%` and `QQQ +15.50%`; benchmark source label is `local+live_overlay`.
- Buy/sell log visibility: `_render_buy_sell_decision_log()` now renders immediately under the Strategy Replay caption, before the heavier forward-walk replay loop, so the audit tape is visible even while replay output is warming.
- Buy/sell audit tape state: visible expander shows `Buy/Sell Decision Log (29 trades, replay audit only)`, caption `PIT replay analysis decisions - not live orders or trade signals`, and metrics `BUY 16`, `SELL 13`.
- Remaining runtime watch item: full YTD forward-walk replay can still be cold-start expensive; this is an acceptance/performance target for the upcoming ultra-modular replay architecture milestone.

## 2026-05-13 Urgent Ultra-Modular Replay Architecture Milestone Note

- Scope split: the current focused patch is visible Portfolio & Allocation behavior only: default method, QQQ/YTD freshness, Rule100 UI/replay sizing parity, and stale benchmark handling. The larger milestone is a separate ultra-modular replay architecture for the AI auto-research loop.
- Research-loop contract: the loop may propose research variants, replay them, annotate outcomes, compare evidence, and save artifacts for human review. It must not become an unchecked optimizer, broker, live-trading system, ranking engine, or autonomous capital allocator.
- Target architecture contract:
  - one replay engine;
  - one strategy plug-in contract;
  - one daily portfolio output format;
  - one event/annotation format;
  - one YTD/performance path;
  - one saved evidence artifact.
- Guardrails:
  - PIT: replay input validity requires both row-date availability and asset-universe membership as of each replay date.
  - stale data: stale/missing inputs must fail closed with explicit status such as `cash_closed`, `skipped`, or `stale_input`, not forward-filled as fresh evidence.
  - overfitting: promotion needs delta metrics vs the latest baseline in the same window, same costs, and the same `engine.run_simulation` path.
  - fake improvement rejection: claimed improvement requires replayable artifact lineage, comparison metrics, and visible rejected/failed attempts when applicable.
  - no broker/live trading: replay artifacts cannot emit orders, alerts, live trades, rankings, recommendations, or broker calls.
- Acceptance tests carried into the architecture milestone:
  - default Portfolio & Allocation method and QQQ/YTD visible fixes are verified before architecture work starts;
  - Rule100 visible sizing remains dynamic for UI/replay at `controls.max_weight`, while frozen audit defaults remain 10% budget / 15% cap;
  - QQQ benchmark freshness is per-ticker stale-aware and does not forward-fill stale local data into a fresh-looking curve when live overlay fails.

## 2026-05-13 Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

- Implementation files: `strategies/rule100_softmax.py`, `strategies/strategy_replay.py`, `views/optimizer_view.py`, `core/data_orchestrator.py`, `dashboard.py`, `tests/test_rule100_softmax.py`, `tests/test_strategy_replay.py`, `tests/test_optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_policy_target_timeline_apptest.py`.
- Frozen audit default preserved: `Rule100SoftmaxConfig()` remains `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`; `data/processed/rule100_softmax_v1_history.csv` is not regenerated as a 35% UI-policy artifact.
- Dynamic UI/replay formula: `rule100_config_from_max_weight(max_weight)` sets `max_single_name_weight=max_weight`, `gross_budget_per_name=max_weight`, and `gross_budget_cap=1.0`.
- Direct Rule100 UI path now passes `controls.max_weight` into `_rule100_softmax_weights_for_ui(...)`; Strategy Replay uses the same dynamic config through `build_strategy_replay(...)`.
- Resulting current UI/replay semantics: one eligible name at `max_weight=0.35` can target `35%`; two equal eligible names target `35% / 35% / 30% cash`.
- Benchmark stale overlay rule: local benchmark TRI history remains first source, but `build_benchmark_equity_from_prices(...)` identifies stale/missing tickers per column and calls a live loader only for those tickers; fresh local peers such as SPY remain local.
- No-forward-fill guard: stale benchmark columns are not allowed to create a visible benchmark curve past their own last valid local date unless a live overlay supplies fresh rows.
- Runtime hygiene: dashboard yfinance YTD download uses `timeout=3`; AppTest caps Strategy Replay dates to the latest 3 dates to avoid turning route coverage into full cold-start replay benchmarking.
- Boundary: no canonical market-data write, no provider ingestion, no broker/alert/ranking/scoring behavior, and no Rule100 audit-baseline rewrite.
- Evidence: focused Rule100/replay/YTD suite PASS, 83 tests; broader affected replay/data/dashboard/lifecycle suite PASS, 151 tests.

## 2026-05-13 Data/PIT Strategy Replay Hardening + UI Wiring

- Implementation files: `core/data_orchestrator.py`, `dashboard.py`, `strategies/strategy_replay.py`, `scripts/build_strategy_replay_artifact.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_strategy_replay.py`, `tests/test_optimizer_view.py`, `tests/test_position_lifecycle.py`, `tests/test_policy_target_timeline_apptest.py`.
- Signature guard: `build_strategy_replay_cache_signature(..., universe_mode="r3000_pit")` is fail-closed; any non-`r3000_pit` universe mode raises before a cache key can be accepted.
- Path guard: repo-local strategy replay artifacts may write only under `data/runtime_cache/strategy_replay`; passing `cache_dir=data/processed` or writing `data/processed/*.parquet` is rejected.
- Dashboard replay integration: `_render_strategy_replay_section()` loads one `StrategyReplayInputs` object per replay date through `_load_dashboard_strategy_replay_inputs_cached(...)`, then calls `build_strategy_replay(..., prices=replay_inputs, as_of_range=None)`.
- PIT output formula: for each replay date `t`, `inputs_t = load_strategy_replay_inputs(as_of_date=t, start_date=t0, end_date=t, universe_mode="r3000_pit")`; replay output uses `prices_t = inputs_t.prices[:, selected_assets ∩ PIT_members(t)]`.
- Empty-slice behavior: if selected assets are absent from a PIT slice, `build_strategy_replay(...)` emits a visible `CASH` row with `status="cash_closed"` and `reason="no_selected_assets_in_pit_universe_as_of_date"` rather than dropping the date.
- Per-date failure behavior: dashboard replay catches PIT input/build exceptions per replay date and emits a visible `cash_closed` row with `reason="pit_input_exception:<type>"` instead of aborting the full 30-date section.
- Boundary: input artifacts store price/return matrices only; replay target weights are generated by `strategies/strategy_replay.py::build_strategy_replay(...)` and are not canonical market data, broker instructions, alerts, rankings, or scores.
- Evidence: focused replay/data/dashboard suite PASS, 93 tests; broader affected replay/portfolio/lifecycle/DASH suite PASS, 179 tests.

## 2026-05-12 Data/PIT Strategy Replay Artifact Notes

- Implementation files: `core/data_orchestrator.py`, `scripts/build_strategy_replay_artifact.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_strategy_replay_artifact.py`.
- Local replay input source: `data/processed/prices_tri.parquet` when present, using `tri` as the price/level matrix and `total_ret` as the return matrix through `data.dashboard_data_loader.load_dashboard_data(...)`.
- PIT replay input rule: `replay_slice(as_of_date) = local_matrix[(date >= start_date) and (date <= min(end_date, as_of_date))]`; future rows are excluded before artifact writing.
- PIT universe guard: `load_strategy_replay_inputs(...)` requires `universe_mode = "r3000_pit"` so replay membership is selected through the date-aware PIT universe path rather than full-history top-liquidity ranking.
- Cache key formula: `strategy_replay_cache_key = sha256(version, source_file_signatures, method, controls, start_date, end_date, as_of_date, max_weight, top_n, start_year, universe_mode)[:32]`.
- Display-only artifact rule: replay artifacts may write only under `data/runtime_cache/strategy_replay` by default; repo `data/` paths outside the configured runtime cache are rejected to avoid canonical market-data confusion.
- Atomic write rule: manifest JSON is pre-serialized first; artifact parquet and manifest JSON then use same-directory temp files followed by `os.replace`.
- Artifact efficiency: persisted replay artifacts use compact wide rows (`matrix=price` and `matrix=return`) instead of long melted rows; ticker labels live in the manifest `ticker_map`.

## 2026-05-12 Rule100 Softmax v1 Historical Weight Overlay

- Implementation files: `scripts/rule100_softmax_v1_audit.py`, `dashboard.py`, `tests/test_rule100_softmax.py`, `tests/test_position_lifecycle.py`.
- Source split: lifecycle event `weight` remains immutable v0 replay/audit truth; softmax v1 writes a derived PIT overlay column, not a replacement.
- History artifact: `data/processed/rule100_softmax_v1_history.csv`.
- Formula source: per date, candidates are lifecycle decision rows with `position_state_after == "HELD"`; eligible rows satisfy `(factor_present_count >= 3) and (factor_positive_count >= 2) and not trend_veto and dist_sma20 <= 0.20`.
- Sizing formula reused from `strategies/rule100_softmax.py`: `score_i = 0.75 * max(factor_positive_count_i - 3, 0) + 0.25 * technical_quality_i`; `budget_t = min(1, 0.10 * eligible_count_t)`; `weight_i = capped_softmax(score_i / tau) * budget_t` with `tau=1.0` and `cap=0.15`.
- Dashboard transaction log columns now distinguish `Event Weight` from `Softmax v1 Target` and `Softmax v1 Cash`.
- Current evidence: on `2026-05-11`, TSM keeps event weight `0.10` but softmax v1 target is `0.00`; AMAT and LRCX are `0.10` each and residual cash is `0.80`.

## 2026-05-12 Portfolio Lifecycle Replay Drop-In + Optimal Formula

- Implementation file: `scripts/pit_lifecycle_replay.py`.
- Drop-in sizing: `dropin_entry_weight = round(1 / DEFAULT_MAX_POSITIONS, 4)` with `DEFAULT_MAX_POSITIONS = 10`, so each new replay ENTER uses `0.10` instead of stale `1 / len(replay_universe) = 0.04`.
- Raw PIT entry gate: `raw_enter = (z_demand > 0) and (capital_cycle_score > 0) and (dist_sma20 <= 0.05) and (not trend_veto)`.
- Optimal lifecycle confirmation filter: `lifecycle_factor_confirmed = (count_present(z_demand, z_moat, z_inventory_quality_proxy, z_discipline_cond) >= 3) and (count_positive(z_demand, z_moat, z_inventory_quality_proxy, z_discipline_cond) >= 3)`.
- Confirmed entry: `emit_enter = raw_enter and lifecycle_factor_confirmed and entry_streak >= 3 and not reentry_cooldown_active`.
- Re-entry cooldown: `reentry_cooldown_active = trade_date < last_exit_date + 10 calendar days`.
- Raw PIT exit gate: `raw_exit = (dist_sma20 > 0.12) or trend_veto`.
- Confirmed exit: `emit_exit = (dist_sma20 > 0.20) or (raw_exit and hold_days >= 20 and exit_streak >= 2)`.
- Rule-of-100 interpretation: the four-factor idea is used only as a PIT lifecycle confirmation layer over existing feature columns; it does not reopen the rejected Phase 54 Rule-of-100 core sleeve or authorize ranking/scoring/promotion.
- Evidence: pre-fix lifecycle replay had `103` events and all ENTER weights were `0.04`; drop-in replay had `69` events and ENTER weights `0.10`; optimal replay has `33` events, ENTER weights `0.10`, no holds `<= 5` days, and current open holds `AMAT`, `LRCX`, and `TSM`.

## 2026-05-12 Portfolio YTD Price/Return Slot Fix

- Implementation files: `core/data_orchestrator.py`, `dashboard.py`.
- Root cause of the visible `+7645112.18%` portfolio metric: `core.data_orchestrator._load_historical_data()` assigned `load_dashboard_data()` outputs in the wrong order, so `UnifiedDataPackage.prices` contained `total_ret` values while `UnifiedDataPackage.returns` contained TRI price levels.
- Correct assignment: `returns_wide, prices_wide, macro, ticker_map, fundamentals_wide = load_dashboard_data(...)`.
- YTD portfolio return formula after fix: `portfolio_daily_return_t = sum_i(weight_i * pct_change(price_i)_t)` with residual cash implicitly contributing `0` unless weights exceed 100%.
- YTD chart data source priority after fix: local TRI history first for portfolio and benchmarks, live yfinance only as fallback when local history is unavailable.
- Evidence: direct current-hold calculation on AMAT/LRCX/TSM 10% each plus 70% cash gives `+14.252580373698297%` from `2026-01-02` to `2026-05-11`; port 8509 smoke shows Portfolio `+14.25%`, SPY/QQQ traces, and no `7645112.18%`.

## Phase 53-61 Planning Formula Notes

**Date**: 2026-03-15

### Governance Reuse Anchors (Already Implemented)
- `N_eff ~= N * (1 - rho_avg) + 1`
- `lambda_logit_rank = log(r / (1 - r))`
- `PBO = mean(lambda_logit_rank <= 0)`
- `DSR = PSR(sr_hat, sr_benchmark, n_obs, skewness, kurtosis)`
- Existing implementation files:
  - `utils/statistics.py`
  - `scripts/parameter_sweep.py`
  - `tests/test_statistics.py`
  - `tests/test_parameter_sweep.py`

### Phase 53-61 Contracts (Execution Status Noted)
- `trial_budget_outer_fold in [9, 18]`
- `global_active_variants <= 18` is the default governance ceiling; only an explicit execution packet may narrow or override it.
- `phase53_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`
- `research_catalog_path = "research_data/catalog.duckdb"` (read-only research contract)
- `allocator_state_view = read_parquet("research_data/allocator_state_cube/variant_id=*/*.parquet", hive_partitioning=true)` (registered in read-only catalog)
- `research_guard = snapshot_date <= 2022-12-31` (required SQL wrapper predicate for research queries; enforced in `scripts/run_allocator_cpcv.py`, which hard-rejects any `max_date > 2022-12-31`)
- `phase53_memory_gate = peak_process_memory_mb < 2048` (recorded by `scripts/benchmark_phase53_data_kernel.py` for allocator_state and CPCV shard scans)
- Phase 53 research-v0 data-kernel contracts are runtime-enabled and evidenced in:
  - `data/processed/phase53_source_manifest.json`
  - `research_data/allocator_state_cube/allocator_state_manifest.json`
  - `research_data/alloc_cpcv_splits/cpcv_splits_manifest.json`
  - `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json`
  - `docs/context/e2e_evidence/phase53_data_kernel_benchmark.json`
- `allocator_state_source_{i,t} = melt(phase17_3_parameter_sweep_return_streams)[variant_id=i, snapshot_date=t, period_return_{i,t}]` for `snapshot_date_t <= 2022-12-31` (implemented in `scripts/derive_phase53_sources_from_phase17.py`)
- `fold_t = build_cscv_block_series(unique(snapshot_date), n_blocks=6)` and `cpcv_source_{i,t} = (fold_t, snapshot_date_t, variant_id_i, period_return_{i,t})` (implemented in `scripts/derive_phase53_sources_from_phase17.py` via `utils/statistics.py`)
- `research_quarantine_windows = deny_root(WriteData/AddFile, AppendData/AddSubdirectory) + allow_tree(ReadAndExecute)` for `research_data/` so `connect_research()` temp-write probe fails closed while the DuckDB catalog stays readable
- `f(margin, supply, demand, pricing_power) := score_100` for Phase 54 (authoritative mapping for Rule-of-100 pass flag)
- `rule100_pass_t = score_100` (authoritative Rule-of-100 pass flag for Phase 54)
- `score_100` is computed in `strategies/supercycle_signal.py::calculate_supercycle_score`
- `rule100_pass_lag = shift(rule100_pass_t, 1) by permno` and `rule100_boost = 0.5 * rule100_pass_lag` (Phase 54 core sleeve booster in `strategies/company_scorecard.py::build_phase20_conviction_frame`)
- `conviction_score = clip(raw_conviction + rule100_boost, 0, 10)` (Phase 54 core sleeve lattice path in `strategies/company_scorecard.py::build_phase20_conviction_frame`)
- `rule100_pass_rate = mean(rule100_pass_t)` and `rule100_pass_controller = 1[0.15 <= rule100_pass_rate <= 0.20]` (controller uses raw pass rate)
- `rule100_input_complete = 1[inputs_complete]` and `rule100_pass_rate_eligible = mean(rule100_pass_t | rule100_input_complete = 1)` (diagnostic only)
- `rule100_input_complete_share = mean(rule100_input_complete)` (diagnostic coverage of Rule-of-100 inputs)
- Rule-of-100 input sourcing: when `delta_revenue_inventory`, `gm_accel_q`, or `operating_margin_delta_q` are missing from features/SDM, they may be sourced from `data/processed/daily_fundamentals_panel.parquet`; `sales_accel_q` is optional and falls back to `delta_revenue_inventory` inside `strategies/supercycle_signal.py::calculate_supercycle_score`
- Phase 54 returns coverage filter: features are restricted to permnos with price rows in the evidence window; runner outputs `permnos_total`, `permnos_with_returns`, `permnos_dropped`
- Phase 54 returns merge: when using `prices_tri.parquet`, missing return rows/values are backfilled from `prices.parquet` with primary precedence
- Phase 54 returns repair artifact: `data/processed/phase54_core_sleeve_returns_repaired.parquet` persists the TRI+prices union with `pct_change` fallback and keep-last dedupe on `date/permno`
- Phase 54 raw overlap diagnostics in `scripts/phase20_full_backtest.py`: `overlap_pairs_total = |{(date, permno) in features} ∩ {(date, permno) in repaired_returns}|`, `feature_overlap_rate = overlap_pairs_total / feature_pairs_total`, and `returns_overlap_rate = overlap_pairs_total / returns_pairs_total`
- Phase 54 executed-exposure diagnostics in `scripts/phase20_full_backtest.py`: `executed_exposure_total_cells = sum(shift(weights_ex_cash, 1) != 0)`, `executed_exposure_missing_cells = sum(1[shift(weights_ex_cash, 1) != 0 and isna(aligned_returns_ex_cash)])`, and `executed_exposure_missing_rate = executed_exposure_missing_cells / executed_exposure_total_cells`
- Phase 54 overlap sidecar artifact: `data/processed/phase54_core_sleeve_overlap_diagnostics.json` persists both raw pair overlap and executed-exposure overlap ahead of the strict evidence gate
- Target Rule-of-100 breadth: `15%-20%` pass rate measured on `rule100_pass_t`, pending the final `mu_c / delta_c` lattice check
- Phase 54 evidence guard: `end_date <= 2022-12-31` enforced by `_validate_end_date_guard` in `scripts/phase20_full_backtest.py` via `RESEARCH_MAX_DATE`
- Phase 54 C3 loader current-price guard in `scripts/phase20_full_backtest.py::_apply_c3_current_price_guard`: `c3_current_price_ok_t = 1[notna(adj_close_t)]`
- Phase 54 baseline validity guard: `c3_score_valid_t = score_valid_t * c3_current_price_ok_t` and `c3_score_t = score_t if c3_score_valid_t = 1 else NaN` (applies to C3 baseline rows only; Phase 20 scoring path unchanged)
- Phase 54 C3 loader diagnostics: `c3_loader_price_guard_rows = sum(1[score_valid_t = 1 and isna(adj_close_t)])`, `c3_loader_price_guard_permnos = nunique(permno | invalidated)`, and `c3_loader_price_guard_applied = 1[c3_loader_price_guard_rows > 0]`
- Phase 54 evidence-clear predicate (technical gate only): `phase54_evidence_clear = 1[(missing_active_return_cells.c3 = 0) and (missing_active_return_cells.phase20 = 0) and (same_window_same_cost_same_engine = 1) and (SAW Verdict = PASS)]`
- Phase 54 D-304 strategic follow-up uses the published `phase54_core_sleeve_summary.json` and `phase54_core_sleeve_overlap_diagnostics.json` as SSOT baseline; `ABORT_PIVOT`, `rule100_pass_rate`, and `rule100_pass_controller` affect strategic evaluation only and do not negate `phase54_evidence_clear`
- Phase 54 D-305 strategic rejection predicate: `phase54_baseline_accept = 1[(decision != "ABORT_PIVOT") and (rule100_pass_controller = 1)]`
- Phase 54 D-305 targeted-tuning trigger: `phase54_tuning_trigger = 1[(decision = "ABORT_PIVOT") or (rule100_pass_controller = 0)]` with the live packet currently evaluating `1`
- Phase 54 D-306 movable tuning knobs only: `{demand_floor, margin_floor, r2_threshold, convexity_threshold, ramp_exception_threshold, ramp_margin_floor}` from `strategies/supercycle_signal.py::SupercycleConfig`
- Phase 54 D-306 bounds: `demand_floor in [-0.02, 0.02]`, `margin_floor in [-0.02, 0.02]`, `r2_threshold in [0.80, 0.95]`, `convexity_threshold in [1.25, 2.00]`, `ramp_exception_threshold in [0.12, 0.24]`, `ramp_margin_floor in [-0.05, 0.00]`
- Phase 54 D-306 frozen surfaces: `rule100_pass_t = score_100`, `rule100_boost = 0.5 * shift(rule100_pass_t, 1)`, `power_law_exponent`, `gravity_multiplier`, `demand_power_scale`, `margin_power_scale`, `gravity_denominator`, `support_sma_window`, `momentum_lookback`, `softmax_temperature`, `top_n_green`, `top_n_amber`, `max_gross_exposure`, loader/evidence semantics, and all Phase 53/kernel paths
- Phase 54 D-306 success predicate: `phase54_tuning_success = 1[(phase54_evidence_clear = 1) and (rule100_pass_controller = 1) and (fresh_artifacts = 1) and (SAW Verdict = PASS)]`
- Phase 54 D-307 tuned artifact fields in `scripts/phase20_full_backtest.py`: `{rule100_demand_floor, rule100_margin_floor, rule100_r2_threshold, rule100_convexity_threshold, rule100_ramp_exception_threshold, rule100_ramp_margin_floor}` emitted by `_rule100_tuning_summary_fields`
- Phase 54 D-307 ceiling config: `phase54_d307_ceiling_config = 1[(rule100_demand_floor = -0.02) and (rule100_margin_floor = -0.02) and (rule100_r2_threshold = 0.80) and (rule100_convexity_threshold = 1.25) and (rule100_ramp_exception_threshold = 0.12) and (rule100_ramp_margin_floor = -0.05)]`
- Phase 54 D-307 controller gap: `phase54_controller_gap = max(0, 0.15 - rule100_pass_rate)`; the fresh tuned packet in `data/processed/phase54_d306_tuned_summary.json` evaluates to `0.02357808340727594`
- Phase 54 D-307 hard-stop predicate: `phase54_d307_hard_stop = 1[(phase54_evidence_clear = 1) and (phase54_d307_ceiling_config = 1) and (rule100_pass_controller = 0)]`
- Phase 54 D-308 SSOT baseline for strategic disposition: `{data/processed/phase54_core_sleeve_summary.json, data/processed/phase54_core_sleeve_overlap_diagnostics.json}`
- Phase 54 D-308 option set is closed: `phase54_d308_option in {A_accept_current_baseline, B_final_bounded_widening}`
- Phase 54 D-308 option A predicate: `phase54_d308_accept_current_baseline = 1[(phase54_evidence_clear = 1) and (rule100_pass_controller = 0)]`
- Phase 54 D-308 option B predicate: `phase54_d308_final_bounded_widening = 1[(phase54_evidence_clear = 1) and (phase54_d307_hard_stop = 1) and (surface = six SupercycleConfig thresholds inside D-301 only)]`
- Phase 54 D-308 option B bounds: `demand_floor in [-0.05, 0.05]`, `margin_floor in [-0.05, 0.05]`, `r2_threshold in [0.65, 0.98]`, `convexity_threshold in [1.00, 2.75]`, `ramp_exception_threshold in [0.05, 0.35]`, `ramp_margin_floor in [-0.15, 0.15]`
- Phase 54 D-308 selected option: `phase54_d308_option = B_final_bounded_widening`
- Phase 54 D-308 option A rejected: `phase54_d308_option_a_rejected = 1[(phase54_d308_option = B_final_bounded_widening)]`
- Phase 54 D-308 option B authorized: `phase54_d308_option_b_authorized = 1[(phase54_d308_option = B_final_bounded_widening)]`
- Phase 54 closeout predicate: `phase54_complete = 1[(phase54_evidence_clear = 1) and (phase54_rule100_rejected = 1) and (SAW Verdict = PASS)]`
- Phase 54 D-309 rejection: `phase54_rule100_rejected = 1[(phase54_evidence_clear = 1) and (rule100_pass_controller = 0) and (d308b_max_bound_executed = 1)]`
- Phase 55 baseline: Rule-of-100 sleeve inactive (`rule100_pass_t` forced to 0 or removed from lattice path) unless a new governance packet explicitly reopens it
- `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
- Phase 55 Expert-Locked Definitions (verbatim):
  - Canonical evidence input surface = read-only Phase 53 research kernel only: (i) allocator_state via research_data/catalog.duckdb / research_data/allocator_state_cube, and (ii) CPCV shard reads via allocator_cpcv.sql + scripts/run_allocator_cpcv.py over research_data/alloc_cpcv_splits, both hard-clamped to snapshot_date <= 2022-12-31. Phase 54 SSOT artifacts may be cited as comparator/governance references only
  - Nested CPCV = each outer CPCV split is the sole source of final allocator evidence, while allocator ranking/selection is performed only inside an inner CPCV loop built from that outer-train partition. The selected allocator is then executed exactly once on the untouched outer-test fold
  - WRC = WRC_p is a co-reported diagnostic and governance corroborator, not a new hard unlock clause in Phase 55. Publish WRC_p beside SPA_p in the evidence pack, but keep the hard gate unchanged as allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]
  - Same-engine = same_window_same_cost_same_engine = 1[(all compared runs share identical start_date/end_date and end_date <= 2022-12-31) and (all compared runs share one fixed cost_bps) and (all governed return/equity series are produced by core.engine.run_simulation under D-04 shift(1) and D-05 turnover-tax semantics)]. Any result computed outside that path is diagnostic-only and non-gating.
- Phase 55 Evidence (verbatim):
  - `rule100_pass_rate = 0.024419920141969833`
  - `- **Phase 55 - Opportunity-Set Controller**: apply nested CPCV + DSR/PBO/SPA to allocator rules; reuse Phase 17 math; new allocator wrapper and SPA helper required.`
  - `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
  - `guard = f"snapshot_date <= DATE '{max_date}'"`
- Phase 55 Allocator Gate:
  - Phase 55 SPA/WRC helpers: `utils/spa.py::spa_p_value`, `utils/spa.py::wrc_p_value`
  - Nested CPCV wrapper: `scripts/phase55_allocator_governance.py::compute_nested_cpcv`
  - Gate formula (unchanged): `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
  - Scalar reducers: `pbo=mean`, `dsr=median`, `spa_p=median`, `wrc_p=median`
  - Inner selection reducer: `selected_variant = argmax(selection_count, median_test_sharpe, median_train_sharpe, variant_id_ascending)`
  - `WRC_p = diagnostic only`
- `pead_window_return_{i,e} = prod_{d=1..5}(1 + r_{i,e+d}) - 1`
- Initial PEAD gates:
  - `value_rank_pct >= 0.60`
  - `adv_usd >= 5_000_000`
  - `days_since_earnings <= 63`
- Phase 56 bounded PEAD runner (`scripts/phase56_pead_runner.py`):
  - `pead_score_{i,t} = capital_cycle_score_{i,t}`
  - `adv_usd_{i,t} = mean_{k=0..19}(adj_close_{i,t-k} * volume_{i,t-k})`
  - `days_since_earnings_{i,t} = date_t - release_date_{i,t}`
  - `pead_gate_{i,t} = 1[(quality_pass_{i,t} = 1) and (adv_usd_{i,t} >= 5_000_000) and (0 <= days_since_earnings_{i,t} <= 63) and (value_rank_pct_{i,t} >= 0.60)]`
  - `value_rank_pct_{i,t} = pct_rank(capital_cycle_score_{i,t} within date t, ascending)`
  - `target_weight_{i,t} = 1 / n_selected_t if pead_gate_{i,t} = 1 else 0`
  - governed return, turnover, and cost series are produced by `core.engine.run_simulation` under D-04 shift(1) and D-05 turnover-tax semantics
  - bounded source paths: `data/processed/features.parquet`, `data/processed/daily_fundamentals_panel.parquet`, `data/processed/prices.parquet`, `scripts/phase56_pead_runner.py`, `core/engine.py`
- `shadow_nav_t = sum_s w_{s,t-1} * (1 + r_{s,t}) - costs_t`
- `w_{t+1} = Pi_Delta(w_0 + B x_t)` for the planned Phase 61 BPPP meta-layer

### Planned Implementation Anchors / Gaps
- Reuse candidates:
  - `utils/statistics.py`
  - `scripts/parameter_sweep.py`
  - `strategies/supercycle_signal.py`
  - `data/calendar_updater.py`
  - `scripts/build_shadow_monthly.py`
  - `scripts/phase37_portfolio_construction_runner.py`
- New implementation still required:
  - allocator CPCV / SPA wrapper
  - BPPP meta-layer runner
  - Shadow-v1 monitoring/alert surface built on allocator_state

### Hook Verification Ledger (Planning Round Evidence)
| Claim | checked_at | command | result |
| --- | --- | --- | --- |
| Governance math exists | 2026-03-15 Asia/Macau | `rg -n "effective_number_of_trials|cscv_analysis|deflated_sharpe_ratio" utils/statistics.py` | Matched the three reusable governance functions in `utils/statistics.py`. |
| Sweep checkpoint/governance runner exists | 2026-03-15 Asia/Macau | `rg -n "effective_number_of_trials|cscv_analysis|deflated_sharpe_ratio|checkpoint" scripts/parameter_sweep.py` | Matched the imported governance functions plus checkpoint/resume flow in `scripts/parameter_sweep.py`. |
| Rule-of-100 score anchor exists | 2026-03-15 Asia/Macau | `rg -n "score_100" strategies/supercycle_signal.py scripts/rule_100_backtest_decades.py dashboard.py docs/phase36_rule100_registry.md` | Matched `score_100` in `strategies/supercycle_signal.py`; no competing Phase 53 bridge exists yet. |
| Earnings calendar reuse surface exists | 2026-03-15 Asia/Macau | `rg -n "earnings_calendar" data/calendar_updater.py data/dashboard_data_loader.py strategies/investor_cockpit.py` | Matched current calendar write/read/consume surfaces for future PEAD work. |
| Event-study scaffold exists | 2026-03-15 Asia/Macau | `rg -n "event study|event_study|earnings" backtests/event_study_csco.py` | Matched the bounded event-study scaffold in `backtests/event_study_csco.py`. |
| Shadow/risk primitive reuse exists | 2026-03-15 Asia/Macau | `rg -n "phase37|shadow|atomic|replace" strategies/phase37_portfolio_registry.py scripts/phase37_risk_diagnostics.py scripts/phase37_portfolio_construction_runner.py scripts/build_shadow_monthly.py views/elite_sovereign_view.py` | Matched Phase 37 registry, atomic write helpers, shadow builder, and dashboard reader surfaces. |
| Allocator kernel hooks now present; meta hooks remain missing | 2026-03-15 Asia/Macau | `rg -n "allocator_cpcv\\.sql|allocator_state|connect_research|BPPP|White Reality Check|Hansen SPA|Reality Check" . -g "!docs/context/**" -g "!docs/handover/phase53_kickoff_memo_20260314.md" -g "!docs/phase_brief/phase53-brief.md" -g "!docs/notes.md" -g "!docs/decision log.md"` | Matches `allocator_cpcv.sql`, `allocator_state`, and `connect_research()` in Phase 53 data-kernel files; SPA/Reality Check/BPPP remain absent. |
| No direct repo-local Phase 53 source-contract parquet existed; explicit transform required | 2026-03-15 Asia/Macau | `python duckdb schema scan across data/processed/**/*.parquet for {variant_id,snapshot_date} and {fold,snapshot_date}` | No direct local parquet exposed both required source contracts; fixed by adding `scripts/derive_phase53_sources_from_phase17.py` over Phase 17.3 sweep artifacts. |
| Phase 53 source contracts derived from Phase 17.3 sweep artifacts | 2026-03-15 Asia/Macau | `.venv\Scripts\python scripts\derive_phase53_sources_from_phase17.py` | Produced `data/processed/phase53_allocator_state_source.parquet` and `data/processed/phase53_cpcv_source.parquet` with `105081` rows, `165` variants, `6` folds, and max `snapshot_date = 2022-12-21`. |
| Phase 53 guarded SQL evidence captured | 2026-03-15 Asia/Macau | `.venv\Scripts\python scripts\run_allocator_cpcv.py` | Wrote `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json` with `row_count = 105081` and `guard_predicate = snapshot_date <= DATE '2022-12-31'`. |
| Phase 53 8-thread benchmark evidence captured | 2026-03-15 Asia/Macau | `.venv\Scripts\python scripts\benchmark_phase53_data_kernel.py` | Wrote `docs/context/e2e_evidence/phase53_data_kernel_benchmark.json` with `overall_peak_memory_mb = 44.363281`, `memory_source = winapi_working_set`, and `within_memory_limit = true`. |

## Phase 52 Week 3 SMA200 Trend Filter

**Date**: 2026-03-13

### Orthogonal Exposure Formula
```python
# Two independent dimensions
trend_multiplier = 1.0 if SPY_price >= SPY_SMA200 else 0.5
regime_exposure = 0.4 if realized_vol > 0.25 else 1.0

# Final exposure (multiplicative, not additive)
final_exposure = trend_multiplier × regime_exposure
```

### Four Market States
| State | RV Condition | SPY Condition | Regime Exp | Trend Mult | Final Exp |
|-------|-------------|---------------|------------|------------|-----------|
| 1. Normal + Uptrend | RV ≤25% | SPY ≥ SMA200 | 1.0 | 1.0 | 1.0 |
| 2. Crisis + Uptrend | RV >25% | SPY ≥ SMA200 | 0.4 | 1.0 | 0.4 |
| 3. Normal + Downtrend | RV ≤25% | SPY < SMA200 | 1.0 | 0.5 | 0.5 |
| 4. Crisis + Downtrend | RV >25% | SPY < SMA200 | 0.4 | 0.5 | 0.2 |

### Data Sources
- **SPY**: permno=84398 from prices.parquet
- **SMA200**: 200-day simple moving average of SPY adj_close
- **Coverage**: 2000-01-03 to 2024-12-31 (full backtest coverage)
- **Warmup**: First 200 days for SMA200 initialization

### Trial 14 Baseline (Locked)
- RV threshold: 25% (annualized)
- Defensive exposure: 0.4 (40% in high-vol regime)
- Defensive top_n: 5 stocks
- Sharpe: 0.644 (target: >0.65)
- Max DD 2008: -39.32% (+22.68% vs Week 1 baseline)

### Dual Acceptance Criteria
**Absolute Thresholds** (3/4 required):
- Max DD 2008 < 45%
- Max DD 2020 < 25%
- Sharpe 2007-2024 > 0.65
- Recovery < 240 days

**Delta Guardrails** (2/3 required):
- Sharpe ≥ +0.05 vs Trial 14
- Max DD ≥ -3% vs Trial 14
- Recovery ≥ -30 days vs Week 1

**Pass**: 3/4 absolute OR 2/3 delta

### Execution Parity and Exact RV Aggregation
```python
# Keep Week 3 on the shared engine path so turnover/costs match Weeks 1/2
results = run_simulation(target_weights=target_weights, returns_df=returns_matrix, cost_bps=10)

# Aggregate chunked market RV exactly per date
rv_t = sum(chunk_return_sq_t) / sum(chunk_obs_t)
```

- Shared engine path source: `backtests/phase52_week3_sma200.py` (`run_sma200_trial`)
- Exact RV aggregation source: `backtests/phase52_week3_sma200.py` (`compute_market_realized_vol_efficient`)
- Why it matters: preserves apples-to-apples turnover/cost semantics and avoids mean-of-means drift in the market-state series that drives the Week 3 overlay

### Implementation Status
- ✓ Code complete: `backtests/phase52_week3_sma200.py`
- ✓ Tests pass: 17/17 in `tests/test_phase52_week3_sma200.py`
- ✓ Backtest execution complete: exact-RV artifact published in `data/processed/phase52_week3/week3_sma200_results.json`
- ✓ Shared-engine parity restored: Week 3 now uses `core.engine.run_simulation` for turnover/cost accounting
- ✓ Closeout lock: Week 3 accepted as the final Phase 52 endpoint under `D-284`
- ✓ Local Reviewer C verification passed on the final artifact set; the earlier block was reviewer-lane artifact access, not a data-integrity defect

## Phase 51 Supercycle Formula Notes

**Date**: 2026-03-13

### Scorer Contract
- `sales_accel_eff = sales_accel_q if finite else delta_revenue_inventory`
- `gm_accel_eff = gm_accel_q if finite else operating_margin_delta_q`
- `demand_pass = (sales_accel_eff > demand_floor) and (delta_revenue_inventory > demand_floor)`
- `margin_pass = (gm_accel_eff > margin_floor) and (operating_margin_delta_q > margin_floor)`
- `demand_strength = max(sales_accel_eff, 0) + max(delta_revenue_inventory, 0)`
- `margin_strength = max(gm_accel_eff, 0) + max(operating_margin_delta_q, 0)`
- `alpha_quad_raw = sum((1 + scale_i * max(component_i, 0)) ^ power_law_exponent - 1)`
- Demand scales: `2.0` for `sales_accel_eff` and `delta_revenue_inventory`
- Margin scales: `8.0` for `gm_accel_eff` and `operating_margin_delta_q`
- `gravity_haircut = (delta_us10y_3m / 0.50) * gravity_multiplier`
- `alpha_quad_adjusted = alpha_quad_raw - gravity_haircut`
- `r2_proxy = clip(cosine(demand_vector, margin_vector), 0, 1) ^ 2`
- `convexity_proxy = 1 + 10 * min(demand_strength, margin_strength)`
- `ramp_exception = demand_pass and demand_strength >= 0.18 and gm_accel_eff >= -0.02 and operating_margin_delta_q >= -0.02`
- `score_100 = 1` iff:
  - `demand_pass`
  - `alpha_quad_adjusted > 0`
  - and either:
    - `margin_pass and r2_proxy >= r2_threshold and convexity_proxy >= convexity_threshold`
    - or `ramp_exception`

### Grid Harness Contract
- Grid size: `5 x 5 x 3 x 3 = 225`
- Training rows: `225 x 3 x 8 = 5,400`
- `strategy_returns_t = signal_{t-1} * asset_return_t`
- `total_return = prod(1 + strategy_returns) - 1`
- `sharpe_ratio = mean(strategy_returns) / std(strategy_returns) * sqrt(252)`
- `max_drawdown = min(equity / cummax(equity) - 1)`
- `information_coefficient = corr(signal_t, strategy_returns_{t+1})`
- Strict survivor filter:
  - `mean_sharpe > 0.8`
  - `ticker_success_rate > 0.75`
  - `window_success_rate > 0.66`
  - `mean_max_dd > -0.25`
- Fallback survivor rule:
  - if no row passes the strict filter, emit the top-ranked `top_n` rows with `passes_filters = False` and `selection_basis = "top_ranked_fallback"`

### Implementation Files
- `strategies/supercycle_signal.py`
- `backtests/optimize_supercycle_grid.py`
- `tests/test_supercycle_signal.py`
- `tests/test_optimize_supercycle_grid.py`

---

## Quality Composite Formula

**Formula**: `quality_composite = 0.4 * ROIC + 0.3 * ROE + 0.3 * Revenue_Growth_YoY`

**Components**:

1. **ROIC (Return on Invested Capital)**: 40% weight
   - `ROIC = operating_income_ttm / invested_capital_avg`
   - `operating_income_ttm` = trailing 4-quarter sum of `oibdpq`
   - `invested_capital` = `ceqq` (equity) + `dlttq` (long-term debt) + `dlcq` (short-term debt)
   - `invested_capital_avg` = 4-quarter rolling average

2. **ROE (Return on Equity)**: 30% weight
   - `ROE = niq / ceqq`
   - `niq` = net income quarterly
   - `ceqq` = common equity quarterly

3. **Revenue Growth YoY**: 30% weight
   - `Revenue_Growth_YoY = (revtq - revtq_lag4) / revtq_lag4`
   - Year-over-year quarterly revenue growth

**Rationale**:
- Simple, auditable 3-term blend
- Temporary explicit formula for Phase 35 pilot
- Future: Replace with research-backed quality basket after pilot validation

**Source**: Phase 1.1 closure report, Phase 2 implementation

---

# Phase 16.13 Formula Notes (Proxy Gate)

Date: 2026-02-17

## 1) Derived Quarterly Metrics
- `sales_growth_q = pct_change(total_revenue_q, 1)`
- `sales_accel_q = delta(sales_growth_q)`
- `op_margin_accel_q = delta(operating_margin_delta_q)`
- `bloat_q = delta(ln(total_assets_q - inventory_q)) - delta(ln(total_revenue_q))`
- `net_investment_q = (abs(capex_q) - depreciation_q) / lag(total_assets_q, 1)`

## 2) Inventory Quality Proxy
- `z_inventory_quality_proxy = z(sales_accel_q) + z(op_margin_accel_q) - z(bloat_q) - 0.5*z(net_investment_q)`

## 3) Discipline Conditional Gate
- Base penalty: `penalty = asset_growth_yoy * (1 - sigmoid(operating_margin_delta_q / smooth_factor))`
- Proxy gate waiver: if `z_inventory_quality_proxy > 0`, then `penalty = 0`
- Output term: `z_discipline_cond = z(-penalty)` (cross-sectional per date)

## 4) Capital Cycle Score
- `capital_cycle_score = 0.4*z_moat + 0.4*z_discipline_cond + 0.2*z_demand`

## 5) Implementation Files
- `data/fundamentals_updater.py` (raw + derived quarterly fields)
- `data/fundamentals_compustat_loader.py` (Compustat parity for derived fields)
- `data/fundamentals.py` (snapshot/daily broadcast propagation)
- `data/fundamentals_panel.py` (daily panel schema + SQL projection)
- `data/feature_specs.py` (proxy score + discipline waiver logic)

---

## Phase 36 Survivor/Bundle Formula Notes

**Date**: 2026-03-08

### Frozen Survivor -> Feature Mapping
- `quality_composite_raw -> quality_composite`
- `vol_beta_63d -> rolling_beta_63d`
- `composite_score_baseline -> composite_score`

### Bundle Execution Contract
- Bundle registry lives in: `strategies/phase36_bundle_registry.py`
- Bundle execution path lives in: `scripts/signal_sweep_runner.py` (`--mode bundle`)
- Each bundle input column is first cross-sectionally z-scored by `date`
- Equal-weight bundle formulas are then evaluated on the normalized feature columns

### Explicit Bundle Formulas
- `bundle_quality_vol = (zscore(quality_composite) + zscore(rolling_beta_63d)) / 2`
- `bundle_quality_composite = (zscore(quality_composite) + zscore(composite_score)) / 2`
- `bundle_vol_composite = (zscore(rolling_beta_63d) + zscore(composite_score)) / 2`
- `bundle_all_three = (zscore(quality_composite) + zscore(rolling_beta_63d) + zscore(composite_score)) / 3`

### Baseline Delta Gate
- Validation gate: `delta_ic_val = bundle_ic_validation - baseline_ic_validation`
- Holdout gate: `delta_ic_hold = bundle_ic_holdout - baseline_ic_holdout`
- Promotion contract: validation and holdout delta IC must both be populated and `> 0`
- Calibration delta IC is recorded as a diagnostic, not a gating requirement

### Robustness Round Stress Contract
- `friction_drag = turnover_monthly * 12 * (cost_bps / 10000)`
- `ic_net_estimated = ic_gross - friction_drag`
- `kill_triggered = (window == "holdout") and (cost_bps == 20) and (ic_net_estimated <= 0)`
- `bundle_decision = Pause if kill_triggered; Continue if delta_ic_val > 0 and delta_ic_hold > 0; otherwise Pivot`
- `portfolio_decision = Continue if continue_votes >= 3; Pause if pause_votes >= 3; otherwise Pivot`
- Implementation file: `scripts/phase36_bundle_robustness_round.py`

### Implementation Files
- `strategies/phase36_bundle_registry.py` (bundle definitions and survivor mapping)
- `scripts/signal_sweep_runner.py` (cross-sectional normalization, baseline loading, delta computation, fail-closed bundle gate)
- `scripts/phase36_bundle_robustness_round.py` (robustness stress grid, 20bps holdout floor, majority rubric, artifact emission)

---

## Phase 37 Portfolio Construction Formula Notes

**Date**: 2026-03-09

### Frozen Sleeve Contract
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`
- Registry file: `strategies/phase37_portfolio_registry.py`
- Comparator path: `data/processed/features_phase35_repaired.parquet`
- PnL path: `core/engine.py` via `run_simulation(...)`

### Sleeve Return and Risk-Primitive Contract
- `sleeve_return_t = equity_t / equity_{t-1} - 1`
- `vol_63d_i(t) = std(sleeve_return_{i,t-62:t}) * sqrt(252)`
- `cov_126d_{i,j}(t) = cov(sleeve_return_{i,t-125:t}, sleeve_return_{j,t-125:t})`
- `corr_126d_{i,j}(t) = cov_126d_{i,j}(t) / (vol_63d_i(t) * vol_63d_j(t))`
- Risk primitives are persisted in `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- Implementation file: `scripts/phase37_risk_diagnostics.py`

### Portfolio Method Formulas
- `equal_weight_i = 1 / 3`
- `inverse_vol_raw_i = 1 / vol_63d_i`
- `inverse_vol_weight_i = normalize(clamp(inverse_vol_raw_i, 15%, 50%))`
- `capped_risk_budget = argmin_w Σ_i (risk_share_i - 1/3)^2`
- Subject to: `Σ_i w_i = 1`, `0.15 <= w_i <= 0.50`, `w_i >= 0`, `gross_exposure = 1.0`
- Implementation file: `scripts/phase37_portfolio_construction_runner.py`

### Ex-Ante Risk and Guardrail Formulas
- `portfolio_var = w' Σ w`
- `marginal_risk_i = (Σ w)_i`
- `risk_contribution_i = w_i * marginal_risk_i`
- `risk_share_i = risk_contribution_i / portfolio_var`
- `gross_turnover_t = 0 if first valid rebalance else 0.5 * Σ_i |w_{i,t} - w_{i,t-1}|`
- `HHI_t = Σ_i w_{i,t}^2`
- Hard guards:
  - optimized methods require `15% <= w_i <= 50%`
  - optimized methods require `risk_share_i <= 40%`
  - all methods require `gross_turnover_t <= 25%` after the first valid rebalance
  - optimized methods require `HHI_t <= 0.375`
  - infeasible or unstable optimized methods are fail-closed, never silently relaxed

### Performance and Delta Contract
- `equity_t = Π_{k<=t} (1 + net_ret_k)` from `run_simulation(...)`
- `CAGR = equity_T^(252 / N_days) - 1`
- `realized_vol = std(net_ret) * sqrt(252)`
- `Sharpe = mean(net_ret) / std(net_ret) * sqrt(252)` when `std(net_ret) > 0`, else `0`
- `max_drawdown = min(equity / cummax(equity) - 1)`
- `delta_cagr_window = portfolio_cagr_window - baseline_cagr_window`
- `delta_sharpe_window = portfolio_sharpe_window - baseline_sharpe_window`
- Baseline files: `data/processed/phase35_reruns/phase35_baseline_corrected_*_target_weights.parquet`

### Recommendation Contract
- `method_decision = Pause` if any hard block occurs
- `method_decision = Continue` if `delta_cagr_validation > 0`, `delta_cagr_holdout > 0`, `delta_sharpe_validation > 0`, and `delta_sharpe_holdout > 0`
- `method_decision = Pivot` otherwise
- `portfolio_decision = Continue` if `continue_votes >= 2`; `Pause` if `pause_votes >= 2`; otherwise `Pivot`
- Validator file: `scripts/validate_phase37_portfolio_outputs.py`

### Implementation Files
- `strategies/phase37_portfolio_registry.py` (sleeve/method registry and locked constraint surface)
- `scripts/phase37_risk_diagnostics.py` (sleeve inputs, risk primitives, regime diagnostics, manifest)
- `scripts/phase37_portfolio_construction_runner.py` (monthly weights, engine path evaluation, guardrails, recommendation)
- `scripts/validate_phase37_portfolio_outputs.py` (fail-closed schema and decision validation)

# Phase 17.1 Formula Notes (Cross-Sectional Backtester)

Date: 2026-02-19

## 1) Forward Return
- `fwd_return_{t,h} = adj_close_{t+h} / adj_close_t - 1`
- Implementation:
  - `scripts/evaluate_cross_section.py` (`load_eval_frame`, DuckDB `LEAD(adj_close, h)` window).

## 2) Double Sort
- Sort 1 (high growth bucket, by date/industry):
  - `High_Asset_Growth = top 30% of asset_growth_yoy within (date, industry)`
- Sort 2 (inside Sort 1 bucket):
  - assign proxy deciles from ordered `z_inventory_quality_proxy` within `(date, industry)`:
    - `decile = floor((rank_position * 9) / (n-1)) + 1`, clipped to `[1, 10]`
- Spread:
  - `spread_t = mean(fwd_return_t | decile=10) - mean(fwd_return_t | decile=1)`
- Implementation:
  - `scripts/evaluate_cross_section.py` (`compute_double_sort`).

## 3) Inference Metrics
- Period mean:
  - `mean = E[spread_t]`
- Period volatility:
  - `vol = std(spread_t)`
- Sharpe:
  - `period_sharpe = mean / vol`
  - `annualized_sharpe = period_sharpe * sqrt(252 / horizon_days)`
- Newey-West lag (auto):
  - `lag = floor(4 * (T/100)^(2/9))`
- Newey-West t-stat for spread mean:
  - OLS on constant with HAC covariance.
- Implementation:
  - `scripts/evaluate_cross_section.py` (`auto_newey_west_lags`, `newey_west_mean_test`, `summarize_spread`).

## 4) Fama-MacBeth Specification
- Cross-sectional regression per date:
  - `fwd_return_{i,t+h} = alpha_t + beta1_t*asset_growth_{i,t} + beta2_t*z_proxy_{i,t} + beta3_t*(asset_growth_{i,t}*z_proxy_{i,t}) + eps_{i,t}`
- Time-series stage:
  - report mean beta and Newey-West t-stat for each beta series (`beta1_t`, `beta2_t`, `beta3_t`).
- Interaction acceptance diagnostic:
  - `beta3_mean > 0` and statistically significant (`p < 0.05`).
- Implementation:
  - `scripts/evaluate_cross_section.py` (`run_fama_macbeth`).

---

# Phase 17.2 Formula Notes (Parameter Sweep, CSCV, DSR)

Date: 2026-02-19

## 1) Correlation-Adjusted Effective Trials
- Let `N` be the number of tested variants and `rho_avg` the average off-diagonal correlation of variant return streams.
- Effective trial count:
  - `N_eff ~= N * (1 - rho_avg) + 1`
  - bounded in implementation to `[1, N]`.
- Implementation:
  - `utils/statistics.py` (`average_pairwise_correlation`, `effective_number_of_trials`).
  - Used by `scripts/parameter_sweep.py`.

## 2) CSCV Split Geometry and PBO
- Split time index into `S` contiguous even blocks (`S in {6, 8, 10}`).
- Enumerate all train/test splits:
  - `splits = C(S, S/2)` where train uses `S/2` blocks and test is the complement.
- Per split:
  - pick train-best variant by Sharpe.
  - evaluate that variant rank in test cross-section.
  - transform relative rank `r` to:
    - `lambda = log(r / (1 - r))`.
- Probability of Backtest Overfitting:
  - `PBO = mean(lambda <= 0)`.
- Implementation:
  - `utils/statistics.py` (`build_cscv_splits`, `build_cscv_block_series`, `cscv_analysis`).
  - Called in `scripts/parameter_sweep.py`.

## 3) Deflated Sharpe Ratio (Bailey & Lopez de Prado Convention)
- Estimated Sharpe of each variant stream:
  - `SR_hat = mean(R) / std(R) * sqrt(periods_per_year)`.
- Expected max Sharpe benchmark under multiple testing:
  - `SR* = E[max(SR)]` approximation from estimated Sharpe distribution and `N_eff`.
- Non-normality-adjusted probabilistic Sharpe:
  - `PSR = Phi( (SR_hat - SR*) * sqrt(n-1) / sqrt(1 - skew*SR_hat + ((kurt-1)/4)*SR_hat^2) )`
  - where `Phi` is the standard normal CDF.
- Deflated Sharpe Ratio:
  - `DSR = PSR`.
- Implementation:
  - `utils/statistics.py` (`safe_sharpe`, `expected_max_sharpe`, `probabilistic_sharpe_ratio`, `deflated_sharpe_ratio`).
  - Applied per variant in `scripts/parameter_sweep.py`.

## 4) Coarse-to-Fine Sweep Topology
- Stage 1 (coarse):
  - evaluate bounded coarse grid (local cap <= 200 combos).
- Stage 2 (fine):
  - center around coarse winner and test neighborhood steps.
- Ranking contract:
  - sort by `DSR` first, then `t_stat_nw`, then spread mean.
- Implementation:
  - `scripts/parameter_sweep.py` (`_build_coarse_grid`, `_build_fine_grid`, `_evaluate_grid`, ranking block in `main`).

---

# Phase 17.3 Prep Notes (Execution Hardening)

Date: 2026-02-19

## 1) Deterministic Variant Identity
- Variant key generation:
  - `variant_id = md5(json(sorted(params)))`
- Contract:
  - stable under key-order changes and robust to grid-order reshuffles.
  - hash payload is restricted to canonical sweep parameter keys (non-parameter metadata ignored).
- Implementation:
  - `scripts/parameter_sweep.py` (`_variant_id_from_params`).

## 2) Fine-Grid Anchor Rule
- Coarse winner selection for fine search:
  - primary: `DSR`
  - tie-break 1: `t_stat_nw`
  - tie-break 2: `period_mean`
  - tie-break 3: deterministic `variant_id` lexical order (stable sort).
- Rationale:
  - refines around the most robust candidate instead of highest raw in-sample signal.
- Implementation:
  - `scripts/parameter_sweep.py` (`_best_row(..., primary_metric='dsr')` in `main`).

## 3) Checkpoint / Resume Policy
- Checkpoint artifacts:
  - `.checkpoint_<prefix>.json`
  - `.checkpoint_<prefix>_results.csv`
  - `.checkpoint_<prefix>_streams.csv`
- Auto checkpoint cadence (`--checkpoint-every=0`):
  - `<=80 variants -> 10`
  - `<=250 variants -> 20`
  - `>250 variants -> 50`
- Resume behavior:
  - default ON, disable with `--no-resume`
  - stage skips use completed `(result + stream)` variant IDs.
- Implementation:
  - `scripts/parameter_sweep.py` (`_checkpoint_paths`, `_save_checkpoint`, `_load_checkpoint`, `_resolve_checkpoint_every`, `_evaluate_grid`).

## 4) Partition-Read Batching for Feature Upsert
- Upsert read optimization:
  - load all touched `(year, month)` partitions in one DuckDB query.
  - reuse one DuckDB connection per `_atomic_upsert_features` execution.
- Implementation:
  - `data/feature_store.py` (`_load_feature_partition_slices`, `_atomic_upsert_features`).

---

# Phase 17 Closeout Notes (Windows Lock Safety)

Date: 2026-02-19

## 1) Windows PID Liveness Contract
- Windows path avoids `os.kill(pid, 0)` and uses WinAPI:
  - `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, ...)`
  - `GetExitCodeProcess(handle, ...)`
  - liveness condition: `exit_code == STILL_ACTIVE (259)`.
- Non-Windows path keeps:
  - `os.kill(pid, 0)` probe semantics.
- Implementation:
  - `scripts/parameter_sweep.py` (`_pid_is_running`).

## 2) Corrupt Lock TTL Recovery Fallback
- Primary lock age:
  - `age_seconds = now_utc - created_at_utc` (from lock payload).
- Fallback lock age when payload is unreadable/missing:
  - `age_seconds = now_utc - file_mtime(lock_path)`.
- Recovery rule:
  - if `age_seconds >= stale_lock_seconds`, attempt stale-lock removal with bounded retries.
- Implementation:
  - `scripts/parameter_sweep.py` (`_lock_age_seconds`, `_lock_file_age_seconds`, `_acquire_sweep_lock`, `_recover_stale_lock`).

## 3) Regression Coverage
- Lock regression tests:
  - `tests/test_parameter_sweep.py::test_sweep_lock_rejects_live_pid`
  - `tests/test_parameter_sweep.py::test_sweep_lock_recovers_dead_pid`
  - `tests/test_parameter_sweep.py::test_sweep_lock_ttl_fallback_recovers_invalid_pid_lock`
  - `tests/test_parameter_sweep.py::test_sweep_lock_ttl_fallback_recovers_corrupt_lock_by_file_mtime`
  - `tests/test_parameter_sweep.py::test_sweep_lock_recovery_is_bounded_when_remove_fails`
  - `tests/test_parameter_sweep.py::test_evaluate_grid_resume_only_path_keeps_existing_state_and_triggers_checkpoint`

---

# Phase 18 Day 1 Formula Notes (Baseline Benchmarking)

Date: 2026-02-19

## 1) SPY Return and Cash Return
- SPY daily return:
  - `spy_ret_t = spy_close_t / spy_close_{t-1} - 1`
- Cash daily return hierarchy:
  - `cash_ret_t = bil_ret_t` when available
  - else `cash_ret_t = effr_rate_t / 100 / 252`
  - else `cash_ret_t = 0.02 / 252`
- Implementation:
  - `scripts/baseline_report.py` (`load_market_inputs`)
  - FR-050 helper: `backtests/verify_phase13_walkforward.py` (`build_cash_return`)

## 2) Baseline Target Weights
- Buy & Hold:
  - `w_target_t = 1.0`
- Static 50/50:
  - `w_target_t = 0.5`
- Trend SMA200:
  - `sma200_t = mean(spy_close_{t-199..t})`
  - `w_target_t = 1.0 if spy_close_t > sma200_t else w_risk_off`
  - default `w_risk_off = 0.5` (CLI override via `--trend-risk-off-weight`)
- Implementation:
  - `scripts/baseline_report.py` (`build_trend_target_weight`, `run_baselines`)

## 3) Engine-Parity Execution and Costs
- Executed weight (D-04):
  - `w_exec_t = w_target_{t-1}`
- Excess-return sleeve passed to engine:
  - `r_excess_t = spy_ret_t - cash_ret_t`
- Engine net excess return:
  - `r_net_excess_t = w_exec_t * r_excess_t - cost_t`
- Turnover/cost (D-05):
  - `turnover_t = |w_exec_t - w_exec_{t-1}|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Portfolio net return:
  - `r_port_t = cash_ret_t + r_net_excess_t`
- Implementation:
  - `scripts/baseline_report.py` (`simulate_single_baseline`)
  - `engine.py` (`run_simulation`)

## 4) Report Metrics
- Equity curve:
  - `equity_t = Π(1 + r_port_i), i=1..t`
- Annualized volatility:
  - `ann_vol = std(r_port) * sqrt(252)`
- Annualized turnover:
  - `turnover_annualized = mean(turnover_t) * 252`
- Total turnover:
  - `turnover_total = Σ turnover_t`
- CAGR / Sharpe / MaxDD / Ulcer:
  - FR-050 helpers reused directly from `backtests/verify_phase13_walkforward.py`
- Implementation:
  - `scripts/baseline_report.py` (`simulate_single_baseline`, `run_baselines`)

---

# Phase 18 Day 1 Addendum (SSOT Metrics + Final Artifact Contract)

Date: 2026-02-19

## 1) Metric SSOT Consolidation
- Metric functions extracted to:
  - `utils/metrics.py`
- Canonical formulas used by code:
  - `CAGR = (equity_T / equity_0)^(1/years) - 1`
  - `Sharpe = mean(excess_ret) / std(excess_ret) * sqrt(periods_per_year)`
  - `MaxDD = min((equity / cummax(equity)) - 1)`
  - `Ulcer = sqrt(mean((100 * drawdown)^2))`
  - `Turnover_t = sum(abs(weights_t - weights_{t-1}))`
- Delegation compatibility:
  - `backtests/verify_phase13_walkforward.py` keeps existing helper names but delegates to `utils/metrics.py`.

## 2) Day 1 Output Contract (Final)
- CSV output (single summary table):
  - `data/processed/phase18_day1_baselines.csv`
- CSV columns:
  - `baseline,cagr,sharpe,max_dd,ulcer,turnover_annual,turnover_total,start_date,end_date,n_days`
- Plot output:
  - `data/processed/phase18_day1_equity_curves.png`
  - log-scale y-axis
  - matplotlib primary path, Pillow fallback when matplotlib is unavailable.

## 3) Baseline Return Equation (Implemented)
- `w_exec_t = shift(w_target_t, 1)` (D-04)
- `r_excess_t = spy_ret_t - cash_ret_t`
- `cost_t = turnover_t * (cost_bps / 10000)` where `turnover_t = |w_exec_t - w_exec_{t-1}|` (D-05)
- `r_port_t = cash_ret_t + w_exec_t * r_excess_t - cost_t`
- File reference:
  - `scripts/baseline_report.py` (`simulate_single_baseline`)

---

# Phase 18 Day 2 Formula Notes (TRI Migration)

Date: 2026-02-19

## 1) Per-Asset TRI Construction
- Core factor:
  - `factor_t = 1 + total_ret_t`
- Guardrail handling:
  - if `total_ret_t` is missing -> `factor_t = 1`
  - if `total_ret_t <= -1` -> `factor_t = 0` (terminal/invalid loss cap)
- TRI path:
  - `TRI_t = base_value * cumprod(factor_t)`
- File reference:
  - `data/build_tri.py` (`build_prices_tri`)

## 2) Schema Guardrail (Split Trap Barrier)
- Legacy signal source renamed:
  - `adj_close -> legacy_adj_close`
- Day 2 contract:
  - signal/indicator layer uses `tri`
  - execution layer keeps `total_ret`
- File references:
  - `data/build_tri.py` (artifact schema projection)
  - `data/feature_store.py` (TRI-first source selection + compatibility output)

## 3) Split Continuity Validation
- For known split dates:
  - `tri_pct_t = TRI_t / TRI_{t-1} - 1`
  - `expected_pct_t = total_ret_t`
  - pass when `abs(tri_pct_t - expected_pct_t) <= tolerance`
- This checks continuity against causal return input (avoids false failure from genuine split-day market moves).
- File reference:
  - `data/build_tri.py` (`build_validation_report`)

## 4) Dividend Capture Sanity Check
- Trailing 1-year delta:
  - `delta_dividend_effect = tri_return_1y - legacy_adj_close_return_1y`
- Expected sign:
  - `delta_dividend_effect >= 0` for high-yield validation tickers.
- File reference:
  - `data/build_tri.py` (`build_validation_report`)

## 5) Macro TRI Extension
- Added TRI columns:
  - `spy_tri`, `vix_tri`, `mtum_tri`, `dxy_tri`
- Recomputed derived fields:
  - `vix_proxy = rolling_std(pct_change(spy_tri), 20) * sqrt(252) * 100`
  - `mtum_spy_corr_60d = rolling_corr(pct_change(mtum_tri), pct_change(spy_tri), 60)`
  - `dxy_spx_corr_20d = rolling_corr(pct_change(dxy_tri), pct_change(spy_tri), 20)`
- File reference:
  - `data/build_macro_tri.py`

## 6) Runtime Integration Notes
- `app.py` prefers `prices_tri.parquet` and `macro_features_tri.parquet` when present.
- `strategies/investor_cockpit.py` carries `tri` in feature history and uses it when available for price-side checks.
- `data/feature_store.py` persists both `adj_close` (compatibility) and `tri` (signal-safe column).

---

# Phase 18 Day 3 Formula Notes (Cash Overlay)

Date: 2026-02-20

## 1) Scenario Set (6 total)
- `Buy & Hold`: `w_target_t = 1.0`
- `Trend SMA200`: `w_target_t = 1.0 if TRI_t > SMA200_t else 0.5`
- `Vol Target 15% (20/60/120d)`: three lookback variants
- `Trend Multi-Horizon`: weighted MA score (`50/100/200`, weights `0.5/0.3/0.2`)
- File reference:
  - `scripts/cash_overlay_report.py` (`run_scenarios`)

## 2) Volatility-Target Overlay Formula
- Realized volatility (lag-safe):
  - `sigma_t = std(spy_ret_{t-lookback..t-1}) * sqrt(252)`
- Target exposure:
  - `w_target_t = clip(0.15 / sigma_t, 0, 1)`
- Warm-up handling:
  - before valid window, fill `w_target_t = 1.0`
- File reference:
  - `strategies/cash_overlay.py` (`VolatilityTargetOverlay.compute_exposure`)

## 3) Trend Multi-Horizon Overlay Formula
- Lagged price:
  - `p_lag_t = TRI_{t-1}`
- For each MA window `i`:
  - `MA_i,t = mean(p_lag_{t-i+1..t})`
  - `signal_i,t = +1 if p_lag_t > MA_i,t else -1`
- Weighted score:
  - `score_t = sum_i(weight_i * signal_i,t)`
- Exposure mapping:
  - `w_target_t = clip(0.5 + 0.5 * score_t, 0, 1)`
- File reference:
  - `strategies/cash_overlay.py` (`TrendFollowingOverlay.compute_exposure`)

## 4) Portfolio Return, Lag, and Cost Path
- Executed exposure (D-04):
  - `w_exec_t = shift(w_target_t, 1)`
- Excess-return sleeve sent to engine:
  - `r_excess_t = spy_ret_t - cash_ret_t`
- Engine net excess:
  - `r_net_excess_t = w_exec_t * r_excess_t - cost_t`
- Turnover/cost (D-05):
  - `turnover_t = |w_exec_t - w_exec_{t-1}|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Portfolio net return (FR-050 cash hierarchy applied):
  - `r_port_t = cash_ret_t + r_net_excess_t`
- File references:
  - `scripts/cash_overlay_report.py` (`simulate_overlay_strategy`)
  - `engine.py` (`run_simulation`)

## 5) Stress and Correlation Diagnostics
- Stress-window exposure summary:
  - `exposure_min`, `exposure_mean`, `exposure_max` per scenario/window
  - windows: `covid_crash`, `inflation_shock`, `low_vol_meltup`, `rate_hikes_q4`
- Exposure orthogonality:
  - Pearson correlation matrix on executed exposure series.
- File references:
  - `scripts/cash_overlay_report.py` (`build_stress_checks`, `build_exposure_corr`)

## 6) Day 3 Regression Fix Note
- `_load_inputs` now passes datetime-indexed macro context into FR-050 `_build_context`.
- Prevents mixed-index sort error (`Timestamp` vs `int`) when liquidity context is present.
- File references:
  - `scripts/cash_overlay_report.py` (`_load_inputs`)
  - `tests/test_cash_overlay.py` (`test_load_inputs_uses_datetime_index_for_fr050_context`)

---

# Phase 18 Day 4 Formula Notes (Company Scorecard)

Date: 2026-02-20

## 1) Linear Factor Score
- Core equation:
  - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t))`
- where:
  - `w_k`: factor weight
  - `sign_k`: `+1` for positive factors, `-1` for negative factors
  - `N_k(i,t)`: normalized factor value for stock `i` on date `t`
- File references:
  - `strategies/company_scorecard.py` (`compute_scores`)
  - `strategies/factor_specs.py` (`build_default_factor_specs`)

## 2) Cross-Sectional Normalization
- Z-score normalization (default):
  - `N_k(i,t) = (x_k(i,t) - μ_k,t) / σ_k,t`
- Rank normalization:
  - `N_k(i,t) = rank_pct(x_k(i,t))`
- Raw normalization:
  - `N_k(i,t) = x_k(i,t)`
- File reference:
  - `strategies/company_scorecard.py` (`_normalize`)

## 3) Day 4 Default Factor Set (Equal Weights)
- Momentum (`+`): `resid_mom_60d`
- Quality (`+`): `quality_composite` (fallback `capital_cycle_score`)
- Volatility (`-`): `realized_vol_21d` (fallback `yz_vol_20d`)
- Illiquidity (`-`): `illiq_21d` (fallback `amihud_20d`)
- Weight vector:
  - `[0.25, 0.25, 0.25, 0.25]`
- File references:
  - `strategies/factor_specs.py`
  - `data/feature_store.py` (Day 4 alias columns)

## 4) Control-Theory Upgrade Toggles (Default OFF)
- Sigmoid blender:
  - `sigmoid(x) = 2 / (1 + exp(-k*x)) - 1`
- Dirty derivative:
  - `x'_t = x_t - x_{t-1}`
- Leaky integrator:
  - `x~_t = EWMA_alpha(x_t)`
- Day 4 baseline policy:
  - all toggles `False`; wiring only, no ablation activation
- File references:
  - `strategies/factor_specs.py` (`FactorSpec` toggles)
  - `strategies/company_scorecard.py` (`_apply_control_toggles`)

## 5) Validation Metrics
- Score coverage:
  - `coverage = non_null(score) / total_rows`
- Factor dominance:
  - per-row share `= |contrib_k| / Σ_j |contrib_j|`
  - evaluate max mean share across factors
- Stability:
  - Spearman rank correlation between adjacent dates
- Quartile separation:
  - `spread_sigma = (mean(Q1) - mean(Q4)) / std(score)`
- File reference:
  - `scripts/scorecard_validation.py` (`build_validation_table`)

---

# Phase 18 Day 5 Formula Notes (Ablation Matrix)

Date: 2026-02-20

## 1) Score Validity Modes
- Complete-case:
  - `valid_i,t = AND_k isfinite(N_k(i,t))`
  - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t))` only when `valid_i,t = True`
- Partial:
  - `valid_i,t = OR_k isfinite(N_k(i,t))`
  - `Score_i,t = [Σ_k (w_k * sign_k * N_k(i,t))] / [Σ_k (w_k * 1_{k available})]`
- Impute-neutral:
  - `valid_i,t = OR_k isfinite(N_k(i,t))`
  - missing factor contribution treated as `0`:
    - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t, missing->0))`
- File reference:
  - `strategies/company_scorecard.py` (`compute_scores`)

## 2) Top-Quantile Portfolio Construction
- Per-date descending rank:
  - `rank_desc(i,t) = rank(score_i,t, descending, method=first)`
- Selected names:
  - `n_select_t = ceil(top_quantile * n_valid_t)`
  - `selected_i,t = 1 if rank_desc(i,t) <= n_select_t else 0`
- Target weight:
  - `w_target(i,t) = selected_i,t / n_select_t`
- File reference:
  - `scripts/day5_ablation_report.py` (`_build_target_weights`)

## 3) Backtest Path (D-04/D-05)
- Engine input:
  - target matrix `W_target(t,i)` from Day 5 scores
  - return matrix `R(t,i)` from `prices_tri.total_ret`
- Execution lag:
  - `W_exec(t,i) = W_target(t-1,i)` (inside `engine.run_simulation`)
- Turnover/cost:
  - `turnover_t = Σ_i |W_exec(t,i) - W_exec(t-1,i)|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Net return:
  - `r_net_t = Σ_i (W_exec(t,i) * R(t,i)) - cost_t`
- Equity:
  - `equity_t = Π(1 + r_net_j), j=1..t`
- File references:
  - `scripts/day5_ablation_report.py` (`_simulate_scores_strategy`)
  - `engine.py` (`run_simulation`)

## 4) Day 5 Delta Metrics
- Baseline anchor: `BASELINE_DAY4`
- For each metric `m`:
  - `delta_m(config) = m(config) - m(baseline)`
- Turnover reduction:
  - `turnover_reduction = 1 - turnover_annual(config) / turnover_annual(baseline)`
- Optimal selection gates:
  - `coverage >= target_coverage`
  - `quartile_spread_sigma >= target_spread`
  - `turnover_reduction >= target_turnover_reduction`
  - `sharpe >= sharpe_baseline`
- File references:
  - `scripts/day5_ablation_report.py` (`_build_deltas`, `_select_optimal`)

## 5) Runtime Guardrails Added
- Dense matrix cap:
  - fail if `n_dates * max(1, n_permnos) > max_matrix_cells`
- Missing active returns:
  - default fail-fast on active-position missing cells
  - optional override: `--allow-missing-returns` => warn + zero-impute
- Empty input window:
  - writes empty artifacts with `status=no_data` and exits non-zero.
- File reference:
  - `scripts/day5_ablation_report.py` (`main`, `_simulate_scores_strategy`)

---

# Phase 18 Day 6 Formula Notes (Walk-Forward Validation)

Date: 2026-02-20

## 1) Leaky Integrator Parameterization
- Day 6 C3 setting:
  - `decay = 0.95`
  - `alpha = 1 - decay = 0.05`
- Integrator recurrence (per factor series per permno):
  - `I_t = (1 - alpha) * I_{t-1} + alpha * x_t`
  - implemented as EWMA with `alpha=0.05`, `adjust=False`.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`_build_c3_specs`)
  - `strategies/company_scorecard.py` (`_apply_control_toggles`)

## 2) Walk-Forward Window Mechanics
- Train/test windows (`W1..W4`) are evaluated as:
  - train metrics on `[train_start, train_end]`
  - test metrics on `[test_start, test_end]`
- Temporal isolation:
  - scores are generated on chronologically ordered history only,
  - no future rows are used in score computation,
  - execution remains `shift(1)` through engine path.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`run_walk_forward_validation`)

## 3) Portfolio Simulation Path
- Selection:
  - `n_select_t = ceil(top_quantile * n_valid_t)`
  - top-ranked names get equal target weights.
- Execution/cost:
  - `w_exec_t = w_target_{t-1}`
  - `turnover_t = sum_i |w_exec_t(i) - w_exec_{t-1}(i)|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
  - `net_ret_t = sum_i(w_exec_t(i) * ret_t(i)) - cost_t`
- File references:
  - `scripts/day6_walkforward_validation.py` (`_simulate_from_scores`)
  - `engine.py` (`run_simulation`)

## 4) Day 6 Check Computations
- Drawdown duration:
  - longest consecutive run where `equity_t < rolling_peak_t`.
- Recovery speed:
  - index distance from `recovery_start` to first date where equity regains pre-start peak.
- Beta:
  - `beta = cov(port_ret, spy_ret) / var(spy_ret)`.
- Rank stability:
  - mean adjacent-date Spearman rank correlation on cross-sectional scores.
- File references:
  - `scripts/day6_walkforward_validation.py` (`_compute_drawdown_duration`, `_days_to_new_high`, `_compute_beta`, `_adjacent_rank_corr`)

## 5) Decay Plateau Diagnostics (CHK-51..53)
- Gradient smoothness:
  - `max(abs(gradient(sharpe(decay_grid)))) < 0.05`.
- Peak-width:
  - at least 3 decay points within `0.03` Sharpe of the best decay.
- Symmetry:
  - `abs((S_0.95 - S_0.90) - (S_0.95 - S_0.98)) < 0.05`.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`analyze_decay_sensitivity`, `evaluate_checks`)

## 6) Crisis Turnover Gate (CHK-54)
- For each crisis window:
  - `reduction_pct = 100 * (turnover_base - turnover_c3) / turnover_base`
  - pass condition: `reduction_pct >= 15` and `turnover_c3 < turnover_base`
- Global CHK-54 pass:
  - all crisis windows pass simultaneously.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`validate_crisis_turnover`)

---

# Phase 21 Day 1 Formula Notes (Stop-Loss & Drawdown Control)

Date: 2026-02-20

## 1) ATR Proxy (Close-Only, SMA)
- Mode:
  - `atr_mode = proxy_close_only`
- Daily range proxy:
  - `range_t = |close_t - close_{t-1}|`
- ATR:
  - `ATR_t = SMA(range_t, window=20)`
- File reference:
  - `strategies/stop_loss.py` (`ATRCalculator.compute_atr`)

## 2) Initial and Trailing Stop Formulas
- Initial stop at entry:
  - `stop_initial = entry_price - (K_initial * ATR_entry)`
  - `K_initial = 2.0`
- Trailing candidate:
  - `stop_trailing_candidate_t = price_t - (K_trailing * ATR_t)`
  - `K_trailing = 1.5`
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.enter_position`, `StopLossManager.update_stop`)

## 3) D-57 Ratchet Invariant
- Non-decreasing stop:
  - `stop_t = max(stop_{t-1}, stop_candidate_t)`
- Invariant:
  - `stop_t >= stop_{t-1}` for every update step.
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.update_stop`)

## 4) Time-Based Underwater Exit
- Underwater condition:
  - `price_t <= entry_price`
- Exit rule:
  - force exit when `days_held > max_underwater_days` while underwater.
- Day 1 default:
  - `max_underwater_days = 60`
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.update_stop`)

## 5) Drawdown Circuit Breakers
- Drawdown:
  - `dd_t = (equity_t - peak_equity_t) / peak_equity_t`
- Tiers:
  - if `dd_t <= -0.15` => scale `0.00`
  - else if `dd_t <= -0.12` => scale `0.50`
  - else if `dd_t <= -0.08` => scale `0.75`
  - else scale `1.00`
- Recovery:
  - if currently in tier mode and `dd_t > -0.04`, reset to scale `1.00`.
- File reference:
  - `strategies/stop_loss.py` (`PortfolioDrawdownMonitor.update_equity`)

## 6) Zero-Volatility Safety Switch
- Optional microscopic floor:
  - `stop <= reference_price - min_stop_distance_abs`
- Default Day 1 setting:
  - `min_stop_distance_abs = 0.0` (disabled by default)
- Intended use:
  - avoid zero-distance stop placement when ATR is exactly zero.
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager._enforce_min_stop_distance`)

---

# Phase 21.1 Formula Notes (Anchor-Injected Cyclical Centroid)

Date: 2026-02-21

## 1) Anchor-Injected Cyclical Centroid in z-Space
- Anchor set:
  - `A = {MU, LRCX, AMAT, KLAC, STX, WDC}`
- Daily available anchors:
  - `A_t = {i in slice_t | ticker_i in A}`
- Centroid (primary path):
  - `mu_cyc_t = mean_{i in A_t}(z_i_t)`
- File reference:
  - `strategies/ticker_pool.py` (`_compute_cyc_centroid_anchor_injected`)

## 2) No-Anchor Fallback Centroid (Legacy Top-k)
- Trigger:
  - `|A_t| = 0`
- Fallback index set:
  - `K_t = TopK(score_col_prepool, k=centroid_top_k)`
- Fallback centroid:
  - `mu_cyc_t = mean_{i in K_t}(z_i_t)`
- Empty fallback safety:
  - if `K_t` is empty after NaN filtering, return zero vector.
- File reference:
  - `strategies/ticker_pool.py` (`_compute_cyc_centroid_anchor_injected`)

## 3) Pre-Pool Score Guard (Chicken-and-Egg Prevention)
- Rule:
  - `score_col` must not be pool-derived (`mahalanobis_*`, `posterior_*`, `odds_*`, `pool_*`, `compounder_prob`).
- Behavior:
  - raise `ValueError` if forbidden score column is passed.
- File reference:
  - `strategies/ticker_pool.py` (`_assert_pre_pool_score_col`)

## 4) Anchor-Priority Long Ranking Boost
- Base eligibility:
  - `valid_i = (MahDist_k_cyc_i <= 5.0) and (odds_ratio_i > 0.5)`
- Anchor bonus level:
  - `B_t = max_{j notin A}(odds_ratio_j) + 1`, fallback `B_t = 10` when non-anchor set is empty.
- Final score:
  - `odds_score_i = odds_ratio_i + B_t * 1_{i in A}` if `valid_i`, else `-9999`.
- File reference:
  - `strategies/ticker_pool.py` (inside `rank_ticker_pool`)

## 5) Path1 Runtime Gates and Deterministic Resample Rule
- Sector-balanced resample depth is computed on known sector labels only:
  - `counts_known = counts(sector != 'UNKNOWN')`
  - `per_sector = min(counts_known)`
  - if `per_sector < 2`, fallback mode is used.
- Non-finite sector projection residualization is hard-fail for that date slice:
  - `if residual_mode == 'projection_nonfinite_fallback': skip date slice + CRITICAL log`
- Slice runner exposes explicit mode toggle:
  - `--dictatorship-mode on|off`
  - `on -> DICTATORSHIP_MODE='PATH1_STRICT'`
  - `off -> DICTATORSHIP_MODE='PATH1_DEPRECATED'`
- File reference:
  - `strategies/ticker_pool.py` (`_deterministic_sector_balanced_resample`, `rank_ticker_pool`)
  - `scripts/phase21_1_ticker_pool_slice.py` (`parse_args`, `main`)

---

# Phase 21.1 Path1 Formula Notes (Sector Context + Dictatorship Telemetry)

Date: 2026-02-21

## 1) Deterministic Sector/Industry Attach (Before Pool Ranking)
- Source:
  - `data/static/sector_map.parquet`
- Priority order:
  - `context_permno = latest(sector, industry by permno)`
  - `context_ticker = latest(sector, industry by ticker)`
  - `context = coalesce(context_permno, context_ticker, 'Unknown')`
- Deterministic selection:
  - sort rows by `updated_at DESC`, then stable tie-breakers, then keep first key row.
- File reference:
  - `strategies/company_scorecard.py` (`_load_sector_context_maps`, `_attach_sector_industry_context`)

## 2) Path1 Context Attachment Flag
- Source label:
  - `sector_context_source_i = 'permno' if permno-map hit else 'ticker' if ticker-map hit else 'unknown'`
- Attachment flag:
  - `path1_sector_context_attached_i = 1{sector_context_source_i != 'unknown'}`
- File reference:
  - `strategies/company_scorecard.py` (`_attach_sector_industry_context`)

## 3) Path1 Directive and DICTATORSHIP_MODE Output Fields
- Constant fields:
  - `DICTATORSHIP_MODE = 'PATH1_STRICT'`
  - `path1_directive_id = 'PATH1_SECTOR_CONTEXT_PRE_RANK'`
- Emitted to:
  - sample CSV rows and summary JSON telemetry.
- File reference:
  - `scripts/phase21_1_ticker_pool_slice.py` (`main`)

## 4) Path1 Summary Telemetry Formulas
- Block-level attachment coverage:
  - `context_attached_ratio_in_block = context_attached_rows_in_block / max(1, block_rows)`
- Sector/industry known counts:
  - `known_sector_rows_in_block = sum(1{sector not in ['', 'Unknown', NaN]})`
  - `known_industry_rows_in_block = sum(1{industry not in ['', 'Unknown', NaN]})`
- Source mix:
  - `context_source_counts_in_block = frequency(sector_context_source)`
- Sample composition:
  - `sample_sector_counts = frequency(sample.sector)`
  - `sample_industry_counts = frequency(sample.industry)`
- File reference:
  - `scripts/phase21_1_ticker_pool_slice.py` (`main`, `_known_context_mask`)

---

# Phase 22 Formula Notes (Separability Harness)

Date: 2026-02-21

## 1) Cluster Stability (Jaccard Overlap)
- Ranking basis:
  - `odds_score` descending.
- Sets:
  - `S_decile_t = top ceil(0.10 * N_t) tickers by odds_score`
  - `S_30_t = top min(30, N_t) tickers by odds_score`
- Daily stability:
  - `J(S_t, S_{t-1}) = |S_t ∩ S_{t-1}| / |S_t ∪ S_{t-1}|`
- Emitted metrics:
  - `jaccard_top_decile`
  - `jaccard_top_30`
- File reference:
  - `scripts/phase22_separability_harness.py` (`_jaccard_index`, `_build_daily_metrics`)

## 2) Manifold Separation (Silhouette in Path1 Geometry)
- Feature space:
  - post-MAD robust z-scored features
  - then sector-projection residualized geometry (`z_geom_resid`).
- Labels:
  - `label_i = argmax(posterior_cyclical_i, posterior_defensive_i, posterior_junk_i)`.
- Score:
  - silhouette score on `(z_geom_resid, label)` rows.
- One-class policy:
  - if only one effective class on a day, emit `silhouette_score = NaN` with class coverage counters.
- Runtime fallback:
  - when `sklearn.metrics` is unavailable, use deterministic manual Euclidean silhouette implementation.
- File reference:
  - `scripts/phase22_separability_harness.py` (`_build_geometry_residuals`, `_compute_silhouette_metrics`, `_manual_silhouette_score`)

## 3) Invariant Truth Checks (Archetype Recall)
- Archetype set:
  - `{MU, LRCX, AMAT, KLAC}`
- Daily rank:
  - `rank_i_t = 1-based rank of ticker i by odds_score on day t`
- Daily hits:
  - `hit_decile_i_t = 1{rank_i_t <= top_decile_n_t}`
  - `hit_top30_i_t = 1{rank_i_t <= top_30_n_t}`
- Aggregate rates:
  - mean of daily hit indicators across the evaluation window.
- File reference:
  - `scripts/phase22_separability_harness.py` (`_archetype_rank_metrics`, `_build_summary`)

---

# Phase 23 Formula Notes (FMP PIT Estimates Ingestion - Step 1)

Date: 2026-02-22

## 1) Internal Schema Contract
- Cleaned output schema:
  - `permno, ticker, published_at, horizon, metric, value`
- Metric names ingested from FMP:
  - `estimatedRevenueAvg`
  - `estimatedEpsAvg`
- Horizon:
  - normalized to `NTM`.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_build_processed_estimates`)

## 2) PIT Publication-Time Rule
- Publication timestamp:
  - `published_at = coalesce(date, publishedDate, published_at, acceptedDate, updatedAt, fetched_at_utc)`
- PIT firewall for NTM aggregation:
  - include forecast periods only when `period_end > published_at`.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_derive_period_fields`, `_normalize_ntm_for_metric`)

## 3) NTM Normalization Rule (Quarterly/Annual)
- For each `(permno, ticker, published_at, metric)` group:
  - if at least 4 future quarterly rows exist:
    - `NTM = sum(first 4 future quarters by period_end ascending)`
  - else if 2-3 future quarterly rows exist:
    - `NTM = sum(quarters) * (4 / n_quarters)` (annualized partial forward set)
  - else if annual (`FY`) row exists:
    - `NTM = FY value`
  - else if exactly 1 future quarter exists:
    - `NTM = quarter_value * 4`
  - else:
    - fallback to first finite metric value.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_normalize_ntm_for_metric`)

## 4) Identifier Integrity Rule
- Mapping source:
  - `data/static/sector_map.parquet`
- Join key:
  - uppercased cleaned ticker (`ticker_u`)
- Integrity behavior:
  - drop unmapped ticker rows from processed output.
  - log unmapped ticker sample for audit.
  - if processed output is empty after mapping/normalization, abort write (preserve existing outputs).
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_load_ticker_permno_crosswalk`, `_build_processed_estimates`, `main`)

## 5) Rate-Aware Cache-First Ingestion Rules
- Per-ticker cache path:
  - `cache_path(ticker) = data/raw/fmp_cache/{ticker}.json`
- Cache priority:
  - if cache exists and `--refresh-cache` is not set:
    - use cache rowset, skip network request.
- 429 handling:
  - exponential backoff:
    - `wait_k = min(backoff_initial_sec * 2^k, 300)` for retry `k`.
  - after retry budget is exhausted:
    - set rate-limited mode,
    - stop new network requests,
    - continue cache-only for remaining scoped tickers,
    - exit cleanly (`code 0`) if no fresh rows can be fetched.
- Scoped universe:
  - target list resolved from `--tickers` and/or `--tickers-file`,
  - capped by `--max-tickers` (default `500`),
  - pre-filtered to tickers with known `permno` in crosswalk before API calls.
- Merge policy:
  - if `--merge-existing` and prior `data/processed/estimates.parquet` exists:
    - `final = dedup(existing ∪ new)` on key
      - `(permno, ticker, published_at, horizon, metric)`
    - source rank enforces **new rows win** on key collisions.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_resolve_target_tickers`, `_load_cached_rows`, `_fetch_with_backoff`, `_merge_existing_processed`, `main`)

---

# Phase 23 Formula Notes (3-Pillar SDM Ingest + Assembler Round 3)

Date: 2026-02-22

## 1) merge_asof Sorting Contract (Pillar 1 + 2)
- Required global order before `merge_asof(..., by='gvkey')`:
  - `left sort = sort_values(['published_at_dt', 'gvkey'])`
  - `right sort = sort_values(['pit_date', 'gvkey'])`
- Hard assertions:
  - `published_at_dt` monotonic increasing globally.
  - `pit_date` monotonic increasing globally.
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_assert_merge_asof_sorted`, `_join_totalq`)

## 2) Peters & Taylor PIT Join + Dynamic Schema
- Filing lag:
  - `pit_date = datadate + 90 days`
- Dynamic probe:
  - `available_cols = information_schema.columns(totalq.total_q)`
  - `selected_cols = required + stable + optional_intersection`
- Required:
  - `gvkey`, `datadate`
- Stable:
  - `k_int`, `k_int_know`, `k_int_org`, `q_tot`
- Optional enrichment:
  - `k_phy`, `invest_int`, `invest_phy`, `ik_tot`
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_probe_totalq_columns`, `_select_totalq_columns`, `_query_totalq`)

## 3) Pillar 2 Derived Features
- Intangible intensity:
  - `intang_intensity = k_int / (k_int + ppentq)` when denominator `> 0`
- Investment discipline:
  - preferred: `invest_disc = ik_tot - lag4(ik_tot)` when `ik_tot` exists
  - fallback: `invest_disc = (k_int - lag4(k_int)) / lag4(k_int)` when `lag4(k_int) > 0`
- Regime flag:
  - `q_regime = 1(q_tot > 1.0)` (NaN-preserving when `q_tot` unavailable)
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_join_totalq`)

## 4) Allow + Audit Identifier Policy
- Mapping:
  - `permno = map(ticker -> permno from sector_map.parquet)`
- Policy:
  - never drop unmapped rows.
  - emit audit CSV for unmapped rows:
    - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_crosswalk_permno`, `_atomic_write_csv`)

## 5) Assembler PIT Join Rules
- Inputs:
  - `fundamentals_sdm.parquet`
  - `macro_rates.parquet`
  - `ff_factors.parquet`
- Key normalization:
  - `published_at_dt = to_datetime(published_at, utc=True).tz_convert(None)`
  - `macro_at = to_datetime(date, utc=True).tz_convert(None)`
  - `ff_at = to_datetime(date, utc=True).tz_convert(None)`
- Asof joins:
  - `fundamentals ⟵ macro` by backward join on `published_at_dt` to `macro_at`
  - `fundamentals ⟵ ff` by backward join on `published_at_dt` to `ff_at`
  - strict staleness cap: `tolerance = Timedelta('14d')`
- Tolerance-null audit:
  - `baseline_match = merge_asof(..., tolerance=None)`
  - `strict_match = merge_asof(..., tolerance='14d')`
  - `nulled_by_tolerance = count(baseline_match exists AND strict_match is null)`
  - emit warning counts for macro and factor joins.
- Sector attach:
  - `permno` map first, then ticker fallback.
- File reference:
  - `scripts/assemble_sdm_features.py` (`assemble_features`, `_count_rows_nulled_by_tolerance`, `_attach_sector_context`)

---

# Phase 23 Formula Notes (Action 2: BGM Manifold Swap)

Date: 2026-02-22

## 1) Daily SDM Broadcast (Method A)
- Entity-wise daily forward fill from quarterly release timeline:
  - `date = normalize(published_at)`
  - For each `gvkey`: reindex to daily calendar and `ffill` latest released snapshot.
- Calendar:
  - `calendar = date_range(min(fundamentals, macro, ff), max(fundamentals, macro, ff), 'D')`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_build_daily_calendar`, `_expand_fundamentals_daily`, `assemble_features`)

## 2) Industry Median Precompute (Method B)
- Daily industry medians:
  - `ind_rev_accel = median(rev_accel | date, industry)`
  - `ind_inv_vel_traj = median(inv_vel_traj | date, industry)`
  - `ind_gm_traj = median(gm_traj | date, industry)`
  - `ind_op_lev = median(op_lev | date, industry)`
  - `ind_intang_intensity = median(intang_intensity | date, industry)`
  - `ind_q_tot = median(q_tot | date, industry)`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_add_industry_medians`)

## 3) Macro-Cycle Interaction (Method B)
- Cycle setup interaction:
  - `CycleSetup = yield_slope_10y2y * rmw * cma`
  - alias: `cycle_setup = CycleSetup`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_add_cycle_setup`)

## 4) Dual-Read Migration Adapter
- Data loader merge contract:
  - `features_window = left_join(features.parquet, features_sdm.parquet, on=[date, permno])`
  - Date normalization before merge:
    - `date = to_datetime(date, utc=True).tz_convert(None)`
  - Overlap policy:
    - for duplicate column name `x`, use `combine_first(x_left, x_sdm)`.
- File reference:
  - `scripts/phase20_full_backtest.py` (`_read_feature_window`, `_load_features_window`)

## 5) BGM Geometry Isolation Contract (Superseded by Phase 20 Lock on 2026-02-22)
- Current locked Phase 20 geometry set must include only:
  - `rev_accel, inv_vel_traj, op_lev, q_tot, CycleSetup`
- Historical note:
  - prior Phase 23 experimentation used a broader 10-feature geometry set;
    this is retained as historical context only and is not the current lock state.
- Explicit risk exclusion asserts:
  - reject exact risk columns:
    - `realized_vol_lag, yz_vol_20d, atr_14d, sigma_continuous, asset_beta_lag, portfolio_beta, rolling_beta_63d`
  - reject any geometry column containing token:
    - `beta` or `vol`
- File reference:
  - `strategies/ticker_pool.py` (`TickerPoolConfig`, `_assert_geometry_excludes_risk`, `rank_ticker_pool`)

## 6) Risk Routing Separation
- Risk features kept for sizing/governor only:
  - volatility path: `sigma_continuous`, `realized_vol_lag`, `atr_14d`, `yz_vol_20d`
  - beta path: `asset_beta_lag`, `portfolio_beta`, `beta_scale_pre`, `beta_scale_post`
- Geometry path uses lagged SDM/macro fields only.
- File reference:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 7) Hierarchical Imputation for SDM Geometry (Universe Preservation)
- Scope:
  - Applied in ticker-pool geometry build before robust MAD scaling.
- Level 1 (Industry Fill, PIT cross-section):
  - For each date and feature:
    - `x_i = median(feature | date, industry)` when firm value is NaN
  - Fallback grouping key:
    - `industry` else `sector` else `UNKNOWN`.
- Level 2 (Neutral Fill):
  - Remaining NaN -> `0.0` in robust-scaled geometry space.
  - Interpretation:
    - `0.0` is neutral market-average exposure on that feature.
- Telemetry:
  - `geometry_universe_before_imputation`
  - `geometry_universe_after_imputation`
  - `geometry_industry_impute_cells`
  - `geometry_zero_impute_cells`
- File reference:
  - `strategies/ticker_pool.py` (`_hierarchical_impute_geometry`, `_build_weighted_zmat_with_imputation`, `rank_ticker_pool`)
  - `scripts/phase22_separability_harness.py` (`_build_geometry_residuals`, `_build_daily_metrics`, `_build_summary`)

---

# Phase 20 Closure Formula Notes (Golden Master Lock)

Date: 2026-02-22

## 1) Cluster Ranker (Option A, Cyclical Trough)
- Formula:
  - `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`
- Interpretation:
  - reward cycle inflection + operating leverage + revenue acceleration + inventory clearing,
  - penalize high `q_tot` to avoid buying supply-heavy/capital-loose profiles.
- Source path:
  - `strategies/ticker_pool.py` (`_conviction_cluster_score`)

## 2) Hard Entry Gate (Trend-Confirmed)
- Formula:
  - `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity`
- Interpretation:
  - no entry without both momentum confirmation and support confirmation.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 3) Hard Exit / Selection Rule
- Formula:
  - `selected = entry_gate & (rank <= n_target)`
- Interpretation:
  - positions must still pass hard gate and rank threshold each day (no winner-retention hysteresis in locked state).
- Source path:
  - `scripts/phase20_full_backtest.py` (`_build_phase20_plan`)

## 4) Concentrated Portfolio and Structural Cash
- Defaults:
  - `top_n_green = 8`
  - `top_n_amber = 4`
  - `cash_pct_GREEN = 0.20`
  - `gross_cap_GREEN = 0.80`
- Source path:
  - `scripts/phase20_full_backtest.py` (`parse_args`, `_build_phase20_plan`)

## 5) Fundamental Continuity Repair (PIT-safe Missing Data)
- Rule:
  - grouped ticker-level `ffill(limit=120)` for `q_tot`, `inv_vel_traj`, `op_lev`, `rev_accel`, `CycleSetup`.
  - remaining NaNs filled by same-date sector median, then same-date market median, then `0.0`.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 6) MU Reverse-Engineer Diagnostic (Boundary Evidence)
- October 2022 means from `data/processed/diagnostic_MU_reverse_engineer.csv`:
  - `q_tot = 3.2634692142857142`
  - `inv_vel_traj = 0.0`
  - `conviction_score = 3.510820467875683`
- Interpretation:
  - backward-looking fundamentals can lag market forward-pricing at cycle bottoms.

---

# Context Bootstrap Formula/Contract Notes

Date: 2026-02-23

## 1) Context Artifact Schema Contract (`current_context.json`)
- Required top-level fields:
  - `schema_version`
  - `generated_at_utc`
  - `source_files`
  - `active_phase`
  - `what_was_done`
  - `what_is_locked`
  - `what_is_next`
  - `first_command`
  - `next_todos`
- Field constraints:
  - `generated_at_utc`: ISO-8601 UTC timestamp.
  - `what_was_done`, `what_is_locked`, `what_is_next`, `next_todos`: non-empty string arrays.
  - `first_command`: non-empty string.
  - key order is fixed to `PACKET_KEYS` in `scripts/build_context_packet.py`.

## 2) Markdown Packet Section Contract (`current_context.md`)
- Required section order:
  - `## What Was Done`
  - `## What Is Locked`
  - `## What Is Next`
  - `## First Command`

## 3) Refresh/Validation Command Contract
- Build command:
  - `.venv\Scripts\python scripts/build_context_packet.py`
- Validation command:
  - `.venv\Scripts\python scripts/build_context_packet.py --validate`
- Phase-end freshness check formula:
  - `artifact_age_hours = (now_utc - generated_at_utc) / 3600`
  - pass condition: `artifact_age_hours <= 24`

## 4) Source Selection + Active Phase Rule
- Candidate order:
  - inspect phase handovers and phase briefs by descending phase number.
  - select first document that satisfies required sections.
- `active_phase` rule:
  - use phase number parsed from selected source document.
  - fallback to max phase brief number only if selected source has no parseable phase token.
- File reference:
  - `scripts/build_context_packet.py` (`_select_context_source`, `_active_phase`, `build_context_packet`)

## 5) Validate Mode Integrity Rule
- Validation command:
  - `.venv\Scripts\python scripts/build_context_packet.py --validate`
- Pass conditions:
  - JSON schema matches `PACKET_KEYS`.
  - `generated_at_utc` parseable + age <= 24h.
  - existing JSON equals expected packet except timestamp field.
  - markdown headers match required contract.
  - markdown body equals canonical render from JSON payload (parity check).
- File reference:
  - `scripts/build_context_packet.py` (`validate_existing_outputs`, `render_context_markdown`)

---

# Phase 23 Macro Gates Formula Notes

Date: 2026-02-23

## 1) QQQ Drawdown and Trend Features
- `qqq_peak_252d_t = max(qqq_close_{t-251..t})`
- `qqq_drawdown_252d_t = qqq_close_t / qqq_peak_252d_t - 1`
- `qqq_ma200_t = mean(qqq_close_{t-199..t})`
- `qqq_ma200_trend_gate_t = 1[qqq_close_t >= qqq_ma200_t]`

## 2) Adaptive Stress Labels (Slow Bleed / Sharp Shock)
- `qqq_ret_5d_t = qqq_close_t / qqq_close_{t-5} - 1`
- `qqq_ret_21d_t = qqq_close_t / qqq_close_{t-21} - 1`
- `qqq_ret_5d_z_adapt_t = z_ewm(qqq_ret_5d_t; mean_span=20, vol_span=126)`
- `qqq_ret_21d_z_adapt_t = z_roll(qqq_ret_21d_t; window=252)`
- `qqq_drawdown_252d_z_adapt_t = z_roll(qqq_drawdown_252d_t; window=252)`
- `qqq_drawdown_5d_delta_t = qqq_drawdown_252d_t - qqq_drawdown_252d_{t-5}`
- `qqq_drawdown_5d_delta_z_adapt_t = z_ewm(qqq_drawdown_5d_delta_t; mean_span=20, vol_span=126)`
- `slow_bleed_label_t = 1[(qqq_ret_21d_z_adapt_t <= -1.0) and (qqq_drawdown_252d_z_adapt_t <= -0.5)]`
- `sharp_shock_label_t = 1[(qqq_ret_5d_z_adapt_t <= -2.5) or (qqq_drawdown_5d_delta_z_adapt_t <= -2.5)]`

## 3) VIX Term Structure Gate
- `vix_term_ratio_t = vix_level_t / vix3m_level_t`
- `vix_backwardation_t = 1[vix_term_ratio_t > 1.0]`

## 4) Hard-Gate State Mapping
- `RED_t = sharp_shock_label_t or vix_backwardation_t`
- `AMBER_t = (not RED_t) and (slow_bleed_label_t or not qqq_ma200_trend_gate_t)`
- `GREEN_t = not (RED_t or AMBER_t)`
- `scalar_t = {RED: 0.0, AMBER: 0.5, GREEN: 1.0}`
- `cash_buffer_t = {RED: 0.50, AMBER: 0.25, GREEN: 0.0}`
- `momentum_entry_t = 1[state_t == GREEN and qqq_ma200_trend_gate_t and not slow_bleed_label_t and not sharp_shock_label_t]`

## 5) Implementation Files
- `data/macro_loader.py`
  - `build_macro_features` (QQQ + VIX term + adaptive labels)
  - `build_macro_gates` (daily hard-gate artifact construction)
  - `run_build` (atomic write of `macro_features.parquet` and `macro_gates.parquet`)
- `scripts/validate_macro_layer.py` (macro_features + macro_gates contract validation)

---

# Phase 23 Macro Gate Consumption Notes

Date: 2026-02-23

## 1) Strategy Consumption Contract (PiT)
- Gate outputs are consumed with strict one-day lag:
  - `state_exec_t = state_signal_{t-1}`
  - `scalar_exec_t = scalar_signal_{t-1}`
  - `cash_buffer_exec_t = cash_buffer_signal_{t-1}`
  - `momentum_entry_exec_t = momentum_entry_signal_{t-1}`
- Warmup defaults after shift:
  - `state = AMBER`
  - `scalar = 0.5`
  - `cash_buffer = 0.25`
  - `momentum_entry = False`

## 2) Phase 20 Plan Wiring
- `selected = entry_gate AND momentum_entry_exec AND (rank <= n_target)`
- `risk_budget = min(1 - cash_buffer_exec, scalar_exec)`
- `base_weight_i = risk_budget / n_selected` for selected names.

## 3) Deferred Risk Scope
- Explicitly deferred to next iteration:
  - integrating `liquidity_air_pocket`, `credit_freeze`, and `momentum_crowding` into hard-gate `RED/AMBER` state transitions.

## 4) Implementation Files
- `scripts/phase20_full_backtest.py`
  - `_load_regime_states(..., macro_gates_path, return_controls=True)`
  - `_build_phase20_plan(..., gate_scalar_by_date, gate_cash_buffer_by_date, gate_momentum_entry_by_date)`
- `strategies/regime_manager.py`
  - Direct hard-gate consumption path when macro context includes gate columns.

---

# Phase 23 Softmax Sizing Notes

Date: 2026-02-23

## 1) GREEN Allocation Rule (Orthogonal Sizing Upgrade)
- For each date `t`, on selected GREEN names only:
  - `p_i,t = exp(conviction_score_i,t / tau) / sum_j exp(conviction_score_j,t / tau)`
  - `tau = softmax_temperature` (default `1.0`)
- GREEN risk budget:
  - `risk_budget_t = 1 - cash_pct_t = 0.80`
- Final GREEN weight:
  - `w_i,t = risk_budget_t * p_i,t`

## 2) Non-GREEN Allocation Rule (Unchanged)
- For AMBER/RED regimes:
  - `w_i,t = risk_budget_t / n_selected_t` on selected names.

## 3) Numerical Stability Rule
- Softmax is computed in stabilized form:
  - `exp((x - max(x))/tau)` with clipping to bounded exponent range.
- Invalid/degenerate denominator fallback:
  - use uniform probabilities over selected GREEN names.

## 4) Implementation Files
- `scripts/phase20_full_backtest.py`
  - `parse_args` (`--softmax-temperature`)
  - `_build_phase20_plan` (GREEN softmax allocation path)

---

# Phase 23 WFO Temperature Notes

Date: 2026-02-23

## 1) Walk-Forward Protocol
- In-Sample (train):
  - `2020-01-01 -> 2022-12-31`
- Out-of-Sample (test):
  - `2023-01-01 -> 2024-12-31`
- Search space:
  - `T_values = [0.2, 0.5, 0.8, 1.0, 1.5, 2.0]`

## 2) Selection Rule
- For each `T` in `T_values`, run Phase 20 backtest on IS window.
- Record `CAGR` and `Sharpe`.
- Winning parameter:
  - `T* = argmax_T Sharpe_IS(T)`
- Tie-break in implementation:
  - higher `CAGR_IS`, then lower `T`.

## 3) OOS Verification Rule
- Execute exactly one OOS backtest using `T*`.
- No additional temperature candidates are evaluated on OOS.

## 4) Implementation Files
- `scripts/optimize_softmax_temperature.py`
  - imports and executes `scripts/phase20_full_backtest.py` logic via `phase20.main()`
  - writes IS grid + OOS result artifact:
    - `data/processed/phase23_wfo_temperature_summary.json`

---

# Phase 23 Institutional Overlay Notes

Date: 2026-02-23

## 1) Bitemporal Continuity Restoration
- Restored bounded core-fundamental continuity in conviction builder:
  - grouped by `permno`, `ffill(limit=120)` for:
    - `q_tot`, `inv_vel_traj`, `op_lev`, `rev_accel`, `CycleSetup`.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 2) Softmax Concentration Overlays
- Minimum portfolio breadth guard:
  - if `len(eligible_tickers) < 4`, abort stock sizing and force:
    - `cash_pct = 1.0`,
    - stock weights = `0.0`.
- Max single-name cap:
  - `max_weight = 0.25` (absolute portfolio weight).
  - softmax weights are capped and excess is iteratively redistributed to uncapped names.
- Source path:
  - `scripts/phase20_full_backtest.py` (`_build_phase20_plan`)

## 3) Single-Day Diagnostic Contract
- Diagnostic script:
- `scripts/diagnostic_softmax_weights.py`
- Target date:
  - requested `2021-06-01`, using closest valid day in available IS feature coverage.
- Telemetry:
  - hard-gate eligible universe (`mom_ok & support_proximity`),
  - raw conviction scores,
  - softmax allocation under `T=0.2` and `T=2.0`,
  - NaN/Inf checks.

---

# Phase 23 Wrap Notes

Date: 2026-02-23

## 1) Revertibility Lock (No-Git Safe)
- Freeze pack created to preserve code + best result artifacts in a manifest-backed snapshot:
  - `scripts/phase23_freeze_pack.py`
- Restore utility for deterministic rollback:
  - `scripts/phase23_restore_from_freeze.py`

## 2) Snapshot Output
- Latest pointer:
  - `data/processed/phase23_freeze_latest.json`
- Snapshot manifest:
  - `data/processed/phase23_freeze/<snapshot_id>/manifest.json`
- Manifest includes:
  - captured code files,
  - captured artifact files,
  - ranked best-result table (by `CAGR`, tie-break `Sharpe`),
  - per-file SHA256 for integrity verification.

## 3) Pivot Readiness (Orbis)
- Current repository scan shows no staged Orbis ingest artifacts or schema exports under project files.
- Next engineering step before `data/orbis_loader.py` implementation:
  - confirm source format/access mode,
  - confirm target feature extraction scope,
  - confirm initial regional universe filter.

---

# Phase 25B Osiris Macro Notes

Date: 2026-02-24

## 1) Core Signal Formula
- Source fields in `bvd_osiris.os_fin_ind`:
  - `inventory = data20010` (Net Stated Inventory),
  - `revenue = COALESCE(data13004, data13002, data13000)`.
- Per-company metric:
  - `inv_turnover = revenue / inventory`.
- Implementation path:
  - `data/osiris_loader.py`.

## 2) Dedup and PIT Controls
- SQL-level dedup:
  - `SELECT DISTINCT`.
- Dataframe-level dedup:
  - `drop_duplicates(subset=['os_id_number', 'closdate'])`.
- Public reporting lag:
  - `knowledge_date = closdate + 60 days`.
- Daily alignment:
  - business-day calendar + `merge_asof(direction='backward')`.
- Implementation path:
  - `data/osiris_loader.py`,
  - `scripts/align_osiris_macro.py`.

## 3) Daily Z-Score Formula
- Rolling normalization on aligned daily signal:
  - `z252_t = (x_t - mean_252_t) / std_252_t`,
  - where `x_t = median_inv_turnover_t`.
- Implementation path:
  - `scripts/align_osiris_macro.py`.

## 4) Validation Formula
- Forward return target:
  - `qqq_fwd_ret_60d_t = Close_{t+60} / Close_t - 1`.
- IC test:
  - `Spearman( median_inv_turnover_z252_t, qqq_fwd_ret_60d_t )`.
- Latest run evidence:
  - `IC = +0.087636`, `p = 1.18113e-05`, `N = 2492`.
- Implementation path:
  - `scripts/align_osiris_macro.py`.

---

# P1 Closeout Validation Formula Notes

Date: 2026-02-28

## 1) Strict Missing Returns on Executed Exposure
- Executed weight (D-04 timing contract):
  - `w_exec[t, i] = w_target[t-1, i]`
- Strict missing-return cell count:
  - `missing_executed = sum_{t,i} 1[ isna(ret_aligned[t, i]) and (w_exec[t, i] != 0) ]`
- Fail-fast rule:
  - if `strict_missing_returns=True` and `missing_executed > 0`, raise runtime error.
- Implementation path:
  - `core/engine.py` (`run_simulation`: executed-exposure mask + strict fail path).
  - Script parity:
    - `scripts/day5_ablation_report.py` (`strict_missing_returns = not allow_missing_returns`)
    - `scripts/day6_walkforward_validation.py` (`strict_missing_returns = not allow_missing_returns`)

## 2) Strict Idempotency Wiring with `client_order_id`
- Deterministic fallback ID (when order omits explicit ID):
  - `digest = UPPER(SHA256(symbol + "|" + side + "|" + qty))[0:12]`
  - `client_order_id = trade_day + "-" + symbol + "-" + UPPER(side) + "-" + qty + "-" + digest`
- Pass-through rule:
  - `submit_order(..., client_order_id)` must carry the same ID in broker payload and result payload.
- Recovery rule on submit exception:
  - if `client_order_id` exists, call `get_order_by_client_order_id(client_order_id)` and return recovered order if found.
- Recovery intent predicate (fail-closed if false):
  - `match = (recovered_symbol == intended_symbol) and (recovered_side == intended_side) and (abs(recovered_qty - intended_qty) <= 1e-9)`
  - if `match == False`: return `error='recovery_mismatch'` and do not mark order accepted.
- Implementation path:
  - `execution/rebalancer.py` (`_generate_client_order_id`, `execute_orders`)
  - `execution/broker_api.py` (`submit_order`, `get_order_by_client_order_id`)

## 3) Fundamentals Ingest Checkpoint/Resume State Machine
- Stage set:
  - `stage in {fetch, merge, final_write, done}`
- Resume gate:
  - continue only when `frozen_targets == requested_targets`;
  - else follow mismatch policy (`fail` or `reset`).
- Identity freeze:
  - `permno_map[ticker] = frozen permno` is persisted in checkpoint metadata and re-applied before resume writes.
- Semantic corruption gate:
  - metadata fields (`version`, `rows_in_partial`, `tickers_with_data`, `stage`) must pass semantic validation;
  - invalid checkpoint rows (`permno <= 0` or non-numeric/null) are routed through mismatch policy and fail closed by default.
- Checkpoint artifacts:
  - metadata JSON: `fundamentals_ingest.checkpoint.json`
  - partial rows parquet: `fundamentals_ingest.partial.parquet`
- Completion policy:
  - success + `checkpoint_keep=False` => cleanup checkpoint artifacts;
  - success + `checkpoint_keep=True` => persist with `stage=done`.
- Implementation path:
  - `data/fundamentals_updater.py` (`run_update`, checkpoint helpers, CLI flags)
  - regression coverage: `tests/test_fundamentals_updater_checkpoint.py`

---

# P2 Auto-Backtest UI Control-Plane Notes

Date: 2026-02-28

## 1) Lab/Backtest Config Normalization
- Control config tuple:
  - `(ma_lookback, stop_lookback, atr_period, vol_target, max_positions, cost_bps, min_price)`
- Normalization rules:
  - `ma_lookback_norm = clamp(round(ma_lookback / 10) * 10, 50, 300)`
  - `stop_lookback_norm = clamp(stop_lookback, 10, 60)`
  - `atr_period_norm = clamp(atr_period, 10, 40)`
  - `vol_target_norm = clamp(vol_target, 0.05, 0.30)` (percent inputs >1 are converted by `/100`)
  - `max_positions_norm = clamp(max_positions, 10, 100)`
  - `cost_bps_norm = max(0, cost_bps)`
    - when `cost_bps_unit = "bps"`: convert by `/10000`,
    - when `cost_bps_unit = "rate"`: use as-is (decimal rate).
  - `min_price_norm = max(1.0, min_price)`
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`normalize_config`)

## 2) Run-Key and Staleness Contract
- Config fingerprint:
  - `fp = SHA256(JSON(normalized_config, sort_keys=True))`
- Run key:
  - `run_key = normalize_date(latest_prices_date) + ":" + fp`
- Planner staleness:
  - `is_stale = (last_run_key != run_key)`
- Attempted-state gate:
  - `attempted = run_attempted and (run_attempted_for_key == run_key)`
  - `should_run = is_stale and not attempted`
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`compute_config_fingerprint`, `compute_run_key`, `build_auto_backtest_plan`)

## 3) Cache State Machine
- Start transition:
  - `status = "running"`
  - `run_attempted = True`
  - `run_attempted_for_key = run_key`
  - `last_started_at = utc_now`
- Finish transition:
  - `status in {"finished","failed"}`
  - `last_run_key = run_key`
  - `last_finished_at = utc_now`
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`mark_started`, `mark_finished`)
  - `views/auto_backtest_view.py` (start/finish/failure writes around simulation)

## 4) Atomic JSON Persist Contract
- Temp path:
  - `tmp = target + "." + pid + "." + epoch_ms + ".tmp"`
- Commit:
  - `write(tmp) -> os.replace(tmp, target)`
- Retry policy:
  - bounded retries on `PermissionError` with short sleep backoff.
- Cleanup:
  - always remove temp file in `finally`.
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`persist_cache_atomic`)

## 5) Cache Integrity Recovery Contract
- Default load policy:
  - `error_policy = "fail"` for normal runtime.
- Bootstrap policy:
  - auto-bootstrap defaults only when cache file is missing.
- Corruption policy:
  - `invalid_json` / `invalid_payload` must block execution path and require explicit operator reset action.
- Start-state durability policy:
  - if start-state write fails, simulation is aborted (fail closed).

---

# Phase 25 Orchestrator E2E Reconciliation Notes

Date: 2026-02-28

## 1) Authoritative Intent Anchor by CID
- Let `O0[cid]` be the normalized original pending order map before submit.
- Let `Rk` be one downstream row on attempt `k`.
- CID extraction:
  - `cid = first_non_empty(Rk.result.client_order_id, Rk.order.client_order_id)`
- Authoritative order for all parity/retry decisions:
  - `O[cid] = O0[cid]` (never trust downstream echoed `Rk.order` fields as intent source).
- Implementation path:
  - `main_bot_orchestrator.py` (`execute_orders_with_idempotent_retry`)

## 2) Batch Completeness and Fail-Closed Rule
- Per attempt `k`:
  - `Expected_k = set(pending_by_cid.keys())`
  - `Observed_k = set(cids accepted from well-formed rows)`
  - `Missing_k = Expected_k - Observed_k`
- Reconciliation:
  - if `k < max_attempts`: `next_pending <- Missing_k`
  - else: emit terminal result per missing CID with:
    - `ok=False`
    - `error='batch_result_missing'`
    - `attempt=k`
- Implementation path:
  - `main_bot_orchestrator.py` (`execute_orders_with_idempotent_retry`)

## 3) Recovery Match Predicate (Already Exists)
- Strict match on original intent:
  - `match = (symbol_rec == symbol_intent) and (side_rec == side_intent) and (abs(qty_rec - qty_intent) <= 1e-9)`
- Decision:
  - if `error contains 'already exists'` and `match=True`: accept as recovered success.
  - else if `error contains 'already exists'` and `match=False`: fail closed as `recovery_mismatch` (no retry).
- Implementation path:
  - `main_bot_orchestrator.py`

## 4) Retry Terminalization Rule
- For retryable transport faults:
  - if `attempt < max_attempts`: retry with same CID.
  - else: terminalize as:
    - `ok=False`
    - `error='retry_exhausted'`
    - `last_error=<normalized error text>`
- Implementation path:
  - `main_bot_orchestrator.py`

## 5) Malformed Row Handling Rule
- Row is considered malformed when:
  - `row` is not a dict, or
  - `row.result` is not a dict.
- Malformed rows are ignored for observation accounting (treated as unobserved), so missing-CID reconciliation applies.
- Implementation path:
  - `main_bot_orchestrator.py`
  - regression coverage in `tests/test_main_bot_orchestrator.py`

---

# Phase 26 Runtime Hardening Notes

Date: 2026-02-28

## 1) Process-Tree Timeout Termination Contract
- Spawn semantics:
  - Windows: create new process group (`CREATE_NEW_PROCESS_GROUP`).
  - POSIX: create new session (`start_new_session=True`).
- Timeout semantics:
  - on scanner timeout, terminate process tree first, then re-raise timeout.
- Windows kill contract:
  - execute `taskkill /PID <pid> /T /F`,
  - require `returncode == 0`, else log hard error.
- POSIX kill contract:
  - send `SIGTERM` to process group,
  - wait bounded grace window,
  - escalate to `SIGKILL` if still alive.
- Implementation path:
  - `main_bot_orchestrator.py` (`_spawn_scanner_process`, `_terminate_process_tree`, `_run_scanner_step`)

## 2) Scheduler Resilience Contract
- Runtime loop behavior:
  - scanner run failure logs error and loop continues,
  - only explicit `KeyboardInterrupt` disarms orchestrator loop.
- Implementation path:
  - `main_bot_orchestrator.py` (`main`)

## 3) Canonical Seed Boundary Contract
- Entry seed rule:
  - every order must provide at least one canonical seed:
    - explicit `client_order_id`, or
    - canonical `trade_day`.
- Null-like normalization:
  - `None`, `null`, `nan` textual forms are treated as missing.
- Enforcement path:
  - pre-normalization gate in `execute_orders_with_idempotent_retry`.
- Implementation path:
  - `main_bot_orchestrator.py` (`_clean_optional_str`, `execute_orders_with_idempotent_retry`)

## 4) Malformed Batch Schema Contract
- Non-list `batch_results` from downstream are treated as empty.
- Dict-shaped rows missing `result.ok` are treated as malformed/unobserved.
- Unobserved CIDs are reconciled through:
  - retry when attempts remain,
  - terminal fail-closed `batch_result_missing` when retries are exhausted.
- Implementation path:
  - `main_bot_orchestrator.py`
  - `tests/test_main_bot_orchestrator.py`

## 5) Rebalance Entrypoint Contract
- Script-level wiring:
  - `scripts/test_rebalance.py` seeds `trade_day`,
  - submits via `execute_orders_with_idempotent_retry(...)`,
  - exits with non-zero code when any submission fails.
- Regression coverage:
  - `tests/test_test_rebalance_script.py`.

---

# Phase 27 Conditional-Block Remediation Notes

Date: 2026-02-28

## 1) Strict Boolean `ok` Gate (Fail-Closed)
- Row admissibility predicate:
  - `admissible_row = isinstance(row, dict) and isinstance(row.result, dict) and isinstance(row.result.ok, bool)`
- Non-admissible rows are treated as unobserved:
  - `Observed_k` excludes these rows.
  - Missing CID reconciliation then applies:
    - retry while attempts remain,
    - terminal `batch_result_missing` at exhaustion.
- Entrypoint success accounting:
  - `ok_count = sum(1 for row in execute_results if row.result.ok is True)`
  - any non-boolean `ok` value is counted as failed.

## 2) Universal Success Parity with Sparse-Payload Fallback
- Acceptance predicate for all `ok=True` rows:
  - `match = (symbol_rec == symbol_intent) and (side_rec == side_intent) and (abs(qty_rec - qty_intent) <= 1e-9)`
- Fallback resolution when success payload omits fields:
  - `symbol_rec = first_non_empty(result.symbol, row.order.symbol)`
  - `side_rec = first_non_empty(result.side, row.order.side)`
  - `qty_rec = first_non_null(result.qty, row.order.qty)`
- Decision:
  - if `match=False`: fail closed with `intent_mismatch` (or `recovery_mismatch` for recovered payloads).
  - if `match=True`: accept terminal success.

## 3) Strict `qty` Type Guardrails
- Input normalization guard:
  - reject boolean quantities:
    - `if isinstance(order.qty, bool): raise ValueError`
  - parse numeric quantity:
    - `qty = int(order.qty)` else fail closed.
- Recovery matcher guard:
  - reject boolean recovered quantity:
    - `if isinstance(result.qty, bool): return False`
  - parse numeric recovered quantity:
    - `qty_rec = float(result.qty)` else fail closed.

## 4) Terminate-Confirmed-or-Fail Contract
- Timeout sequence:
  1. scanner process times out,
  2. invoke process-tree termination,
  3. require liveness confirmation (`proc.poll() is not None`) within grace windows,
  4. if not confirmed, raise terminal `ScannerTerminationError`.
- Terminal propagation:
  - startup diagnostic path and scheduler loop re-raise `ScannerTerminationError` after critical logging.

## 5) Startup Containment Parity
- Startup diagnostic follows scheduler-style containment for non-terminal exceptions:
  - `except Exception -> log error -> continue to armed scheduler mode`
- Terminal scanner-kill failures are not contained:
  - `except ScannerTerminationError -> critical log -> raise`

---

# Phase 28 Entrypoint Contract Remediation Notes

Date: 2026-02-28

## 1) Atomic Payload Entry Gate (Local Submit)
- Payload row admissibility:
  - `admissible_row = is_dict(row) AND has_required_fields(row) AND all_field_validators_pass`
- Batch policy:
  - if any row is non-admissible, abort entire batch:
    - `raise ValueError(...)`
  - no partial-row skipping is allowed.
- Required row fields:
  - `ticker|symbol`, `target_weight`, `action|side`, `order_type`, `limit_price`, `client_order_id`, `trade_day`.
- Validation highlights:
  - `target_weight > 0` and finite,
  - `order_type in {MARKET, LIMIT}`,
  - `trade_day` must be `YYYYMMDD` and a valid calendar date,
  - duplicate `ticker` or duplicate `client_order_id` is rejected.
- Implementation path:
  - `main_console.py` (`_validate_payload_execution_rows`)

## 2) Local Intent Parity Contract
- After target-weight -> order calculation, enforce exact symbol-set parity:
  - `set(payload_symbols) == set(calculated_symbols)`
- For each symbol, seed order intent and assert parity:
  - `symbol`, `side`, `qty`, `order_type`, `limit_price`, `client_order_id` must match expected intent.
- Limit-price policy:
  - `MARKET` -> `limit_price = None`,
  - `LIMIT + fixed numeric` -> use fixed numeric,
  - `LIMIT + Bid_Ask_Mid token` -> resolve from calculated price.
- Implementation path:
  - `main_console.py` (`_resolve_seeded_limit_price`, `_assert_seeded_order_parity`, `_execute_payload_via_idempotent_helper`)

## 3) CID Reconciliation Contract (Helper Output)
- Expected set:
  - `ExpectedCID = {payload_row.client_order_id}`
- Observed set:
  - `ObservedCID = {row.order.client_order_id from helper results}`
- Acceptance:
  - `ObservedCID == ExpectedCID` and no duplicates/unknown CIDs.
- Else fail closed:
  - unknown CID, duplicate CID, or missing CID rows -> `ValueError`.
- Implementation path:
  - `main_console.py` (`_execute_payload_via_idempotent_helper`)

## 4) Broker Submit/Recovery Intent Contract
- Submit boundary:
  - reject bool qty:
    - `if isinstance(qty, bool): invalid_qty`
  - enforce `order_type`/`limit_price` consistency:
    - market: no valid non-null limit semantics,
    - limit: finite positive `limit_price` required.
- Recovery parity:
  - strict match on:
    - `symbol`, `side`, `qty`, `order_type`, `client_order_id`
  - market-order recovery accepts only null-like `limit_price`:
    - `{None, "", "none", "null"}`
  - non-null numeric market `limit_price` fails closed as `recovery_mismatch`.
- Implementation path:
  - `execution/broker_api.py` (`submit_order`, `_recovery_matches_intent`, `get_order_by_client_order_id`)

## 5) Orchestrator Recovery Parity Extension
- Retry normalization now carries:
  - `order_type`, `limit_price` in addition to `symbol/side/qty/client_order_id`.
- Recovery acceptance predicate extends to:
  - `symbol/side/qty/order_type/limit_price` parity (plus CID anchoring).
- Implementation path:
  - `main_bot_orchestrator.py` (`_normalize_order_for_retry`, `_recovery_result_matches_intent`)

## DevSecOps Stream Controls (2026-03-01)
- Scope:
  - secret scrub for WRDS/FMP credentials,
  - cache-level API-key redaction,
  - deny-by-default egress policy,
  - HMAC key lifecycle contract with legal-hold exception.
- Explicit formulas and code loci:
  - key-age (days) with future-skew guard:
    - `age_seconds = (now_utc - hmac_key_activated_at_utc).total_seconds()`
    - `if age_seconds < -max_future_skew_seconds: fail_closed`
    - `age_days = max(0, age_seconds / 86400)`
    - implemented in `core/security_policy.py` (`get_hmac_rotation_status`).
  - rotation due:
    - `rotation_due = (age_days >= rotation_days) and (not legal_hold)`
    - implemented in `core/security_policy.py` (`get_hmac_rotation_status` / `require_hmac_rotation_compliance`).
- Runtime contracts:
  - required env:
    - `TZ_HMAC_KEY_VERSION`, `TZ_HMAC_KEY_ACTIVATED_AT_UTC`,
    - `WRDS_USER`, `WRDS_PASS`, `FMP_API_KEY`,
    - Alpaca key pair (`APCA_API_KEY_ID` + `APCA_API_SECRET_KEY` or aliases).
  - legal-hold exception:
    - `TZ_HMAC_KEY_LEGAL_HOLD=YES`.
  - egress allowlist extension:
    - `TZ_ALLOWED_EGRESS_HOST_SUFFIXES=host1,host2,...` (extends defaults).
  - egress allowlist override mode:
    - `TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE=override`.
  - transport and notification controls:
    - HTTPS required for egress by default,
    - optional localhost-only HTTP break-glass: `TZ_ALLOW_HTTP_EGRESS_LOCALHOST=YES`,
    - post-submit webhook failures degrade with warning while payload-only notification remains fail-closed.
- Follow-through controls (Track 3 approved):
  - Data Health derivation is sourced from in-memory HF proxy input payload (same object passed as `manual_inputs` to the scanner).
  - Explicit formulas:
    - `degraded_count = count(signal.status == "DEGRADED")`
    - `degraded_ratio = degraded_count / total_signals`
    - `status = "DEGRADED" if degraded_count > 0 else "HEALTHY"`
  - Implementation path:
    - `core/dashboard_control_plane.py`:
      - `derive_hf_proxy_data_health`
      - `ensure_payload_data_health`
    - `dashboard.py`:
      - payload persistence: `payload["data_health"]`
      - operator surface: compact badge + expandable details panel.
  - Malformed FMP payload hardening expansion:
    - added regression classes for non-rate-limit dict, unexpected scalar payload, and invalid JSON decode paths in `tests/test_ingest_fmp_estimates.py`.

---

# Phase 29 Microstructure Telemetry Notes

Date: 2026-03-01

## 1) Arrival Midpoint Anchor (Sovereign_Command Time)
- At command generation, each seeded order captures:
  - `arrival_ts` (UTC, ms precision),
  - `arrival_quote_ts`,
  - `arrival_bid_price`, `arrival_ask_price`,
  - `arrival_price`.
- Formula:
  - `arrival_price = (arrival_bid_price + arrival_ask_price) / 2`.
- Implementation path:
  - `main_console.py` (`_execute_payload_via_idempotent_helper`)
  - `execution/broker_api.py` (`get_latest_quote_snapshot`)

## 2) Partial-Fill Aggregation by `client_order_id`
- Fill rows are captured from broker activity feed when available.
- Fallback is snapshot-level fill (`filled_qty`, `filled_avg_price`) when activity rows are unavailable.
- Fill VWAP formula:
  - `VWAP_fill = sum(fill_price_i * fill_qty_i) / sum(fill_qty_i)`.
- Implementation path:
  - `execution/broker_api.py` (`_list_fill_activities`, `_summarize_partial_fills`, `_extract_fill_telemetry`)

## 3) Deterministic Slippage / Implementation Shortfall
- Buy shortfall:
  - `IS_buy = (VWAP_fill - arrival_price) * fill_qty`.
- Sell shortfall (cost-positive):
  - `IS_sell = (arrival_price - VWAP_fill) * fill_qty`.
- Slippage standardization:
  - `slippage_bps = (signed_delta / arrival_price) * 10,000`.
  - `signed_delta = VWAP_fill - arrival_price` for buys.
  - `signed_delta = arrival_price - VWAP_fill` for sells.
- Implementation path:
  - `execution/microstructure.py` (`_calc_execution_cost_metrics`)

## 4) Latency Decomposition
- `latency_ms_command_to_submit = submit_sent_ts - arrival_ts`.
- `latency_ms_submit_to_ack = broker_ack_ts - submit_sent_ts`.
- `latency_ms_ack_to_first_fill = first_fill_ts - broker_ack_ts`.
- `latency_ms_command_to_first_fill = first_fill_ts - arrival_ts`.
- Implementation path:
  - `execution/microstructure.py` (`_ms_diff`, `build_execution_telemetry_rows`)

## 5) Post-Trade Telemetry Sink
- Order rows:
  - `data/processed/execution_microstructure.parquet`
  - DuckDB: `data/processed/execution_microstructure.duckdb` table `execution_microstructure`.
- Fill rows:
  - `data/processed/execution_microstructure_fills.parquet`
  - DuckDB table `execution_microstructure_fills`.
- Local-submit integration path:
  - `main_console.py` (`_persist_execution_microstructure`, `main` local-submit branch)
- Persistence behavior:
  - telemetry sink write failure is fail-closed for local submit.

---

# Phase 30 Release Engineering Notes

Date: 2026-03-01

## 1) Digest-Locked Release Identity
- Canonical release reference formula:
  - `release_ref = "<repo>:<tag>@sha256:<64-hex>"`
- Validation path:
  - `core/release_metadata.py` (`is_digest_locked_release_ref`, `require_digest_locked_release_ref`)

## 2) UI Cache Fingerprint Bound To Artifact Identity
- Explicit formula:
  - `cache_fingerprint = "<version>@sha256:<release_digest|local-dev>"`
- Implementation path:
  - `core/release_metadata.py` (`build_release_cache_fingerprint`)
  - `dashboard.py` (`_release_bound_cache_version`)

## 3) Promotion and Rollback State Machine
- State transition (high level):
  - `idle/active -> pending_probe -> active|rolled_back|rollback_failed`
- Rollback target contract:
  - on failed startup probe:
    - restore `N-1` (`current_release` before candidate stage),
    - fallback to `previous_release` only when `current_release` is absent.
  - `status=rolled_back` is valid only when rollback verification succeeds (`rollback_ok=True`).
  - `status=rollback_failed` records unresolved runtime rollback outcome.
- External probe safety gate:
  - `--mode external-probe` requires explicit `--allow-external-probe-promote`.
- Implementation path:
  - `scripts/release_controller.py` (`execute_release_controller`, `build_docker_startup_probe`)

---

# Phase 31 Stream 2 Risk Interceptor Notes

Date: 2026-03-01

## 1) Post-Trade Exposure and Weight Checks
- Portfolio-state ingest contract:
  - malformed or non-finite broker position quantities are fail-closed (`risk_check_error`), not silently dropped.
- Post-trade quantity projection:
  - `qty_post_i = qty_current_i + qty_order_i` for buy orders.
  - `qty_post_i = qty_current_i - qty_order_i` for sell orders.
- Long-only invariant:
  - if `long_only=True`, enforce `qty_post_i >= 0` for every symbol projection.
  - if violated, return deterministic block with `reason_code=invalid_order_projection`.
- Notional exposure:
  - `exposure_i = abs(qty_post_i) * price_i`.
- Weight:
  - `weight_i = exposure_i / equity`.
- Single-asset hard limit:
  - `max_i(weight_i) <= max_single_asset_weight`.
- Implementation path:
  - `execution/risk_interceptor.py` (`project_state`, `evaluate`)

## 2) Sector Concentration Hard Limit
- Sector exposure aggregation:
  - `sector_exposure_s = sum(exposure_i for i in sector s)`.
- Sector weight:
  - `sector_weight_s = sector_exposure_s / equity`.
- Hard limit:
  - `max_s(sector_weight_s) <= max_sector_weight`.
- Sector source resolution order:
  - broker `get_sector_map/get_sector_for_symbol` -> portfolio state `sector_map/sectors` -> order row `sector` fallback -> `UNKNOWN`.
- Implementation path:
  - `execution/risk_interceptor.py` (`_resolve_sector_map`, `evaluate`)

## 3) VIX Kill-Switch Gate
- Decision rule:
  - if `side == buy` and `vix > 45`, then `BLOCK`.
  - sell orders remain eligible (gate does not block exits).
- VIX source resolution order:
  - broker (`get_vix_level/get_vix`) -> portfolio state (`vix`/`vix_level`) -> order row (`vix`/`vix_level`) fallback.
- Implementation path:
  - `execution/risk_interceptor.py` (`_resolve_vix`, `evaluate`)

## 4) VaR Proxy Hard Limit
- Per-symbol volatility input:
  - broker `get_symbol_volatility` -> portfolio-state map -> order row `volatility`/`volatility_1d`/`vol` fallback -> default.
- Portfolio VaR proxy:
  - `var_proxy = z * sqrt(sum((weight_i * sigma_i)^2))`
  - where `z = var_confidence_z`.
- Hard limit:
  - `var_proxy <= max_var_proxy`.
- Implementation path:
  - `execution/risk_interceptor.py` (`_resolve_symbol_volatility`, `_compute_var_proxy`, `evaluate`)

## 5) Fail-Closed Execution and Block Audit Trail
- Rebalancer integration point:
  - Risk check executes after order-shape validation and before `broker.submit_order(...)`.
- Batch preflight contract:
  - normalize/validate the entire order batch before first submit side effect.
- Rebalance ordering contract:
  - sell orders are sequenced before buys to reduce avoidable cash-constraint rejects.
- Fail-closed contract:
  - any interceptor/bootstrap/state-update exception returns a `BLOCK` result and skips broker submit.
- State-commit ordering:
  - projected risk state is committed only when `result["ok"] is True` after submit.
  - conservative pending-order policy: only buy legs are projected pre-fill; sells are not credited until downstream fill telemetry confirms execution.
- Batch halt contract (optional):
  - when `halt_on_risk_block=True` (or order flag `halt_batch_on_block=True`), the first block halts remaining batch rows as `risk_batch_halt`.
- Atomic audit persistence:
  - write JSON to `logs/risk/<unique>.tmp`, then `os.replace(tmp, final)` to `logs/risk/risk_block_*.json`.
- Audit-write failure semantics:
  - if audit persistence fails, return `reason_code=risk_blocked_audit_failed` and force batch halt fail-stop.
- Implementation path:
  - `execution/rebalancer.py` (`execute_orders`)
  - `execution/risk_interceptor.py` (`persist_block_decision`)

---

# Phase 30 Truth Layer Formula Notes (PiT + Scaling + Atomic Commit)

Date: 2026-03-01

## 1) PiT Fundamentals Availability Contract
- Daily availability interval:
  - `active(date) := published_at <= date < next_published_at`
- Join discipline:
  - features must consume fundamentals values on panel date rows only, not `release_date` forward-fill.
- Implementation path:
  - `data/fundamentals_panel.py` (`build_daily_fundamentals_panel`, interval SQL join)
  - `data/fundamentals.py` (`build_fundamentals_daily`, panel-first path)

## 2) Robust Cross-Sectional Scaling Contract
- For each date cross-section:
  - `median_t = median(x_{i,t})`
  - `MAD_t = median(|x_{i,t} - median_t|)`
  - `robust_sigma_t = max(1.4826 * MAD_t, epsilon_floor)`
  - `z_{i,t}^{robust} = (x_{i,t} - median_t) / robust_sigma_t`
- Sparse cross-section fallback:
  - if `window_size_t < min_window_size`, use percentile fallback:
  - `z_{i,t}^{pct} = (rank_pct_{i,t} - 0.5) * 2`
- Observability:
  - `fallback_rate = fallback_rows / total_rows`
- Implementation path:
  - `data/feature_store.py` (`_cross_sectional_scale`, `_cross_sectional_percentile_fallback`, `run_build` telemetry)

## 3) Incremental Patch Upsert Contract (Yahoo Bridge)
- Partitioning:
  - `partition_key = (year(date), month(date))`
- Upsert dedupe key:
  - `(permno, date)`, keep latest row in merge order.
- Write path:
  - touched-partition-only rewrite under updater lock.
- Implementation path:
  - `data/updater.py` (`_upsert_partitioned_patch_rows`, `_atomic_partition_swap`, `publish_patch_rows`)

## 4) Feature Store Atomic Commit Contract
- Single-visible-commit protocol:
  - apply partition merges in stage dataset root
  - write commit manifest and tombstone metadata
  - atomically swap stage root into `features.parquet`
- Read-side policy gate:
  - `stale_while_revalidate_sec = 0`
  - `tombstone_priority = enforced`
- Implementation path:
  - `data/feature_store.py` (`_atomic_upsert_features`, `_write_feature_commit_manifest`, `_validate_feature_manifest_policy`)

## 5) Crash-Recovery + Lock Ownership Contract
- Backup-swap recovery:
  - if `target_path` is missing and `target_path.bak.*` exists, restore newest backup before any read/write merge path.
  - if live `target_path` exists, stale backups are pruned.
- Lock-owner rule:
  - backup recovery is blocked only for a live external owner lock.
  - self-owned lock (`lock_pid == current_pid`) is recovery-eligible.
- Lock-release rule:
  - `release` is token-owned only.
  - if no token exists, lock file is not removed (`no token => no delete`).
- Implementation path:
  - `data/updater.py` (`_recover_backup_swap`, `_update_lock_owner_live`, `_release_update_lock`)
  - `data/feature_store.py` (`_recover_atomic_replace_backups`, `_update_lock_owner_live`, `run_build`)

## 6) Yahoo Chunk Failure Fail-Closed Contract
- Chunk accounting:
  - treat transport exceptions as explicit `chunk_failed=True`.
  - `failed_chunks = count(None results + chunk_failed frames)`.
- Update gate:
  - if `failed_chunks > 0`, abort update before ticker-map or patch writes.
  - if all chunks fail (`all_chunks_failed=True`), return hard failure (`success=False`).
- Implementation path:
  - `data/updater.py` (`batch_download_yahoo`, `parallel_batch_download_yahoo`, `run_update`)

## 7) Feature Manifest V2 (Pointer + Cryptographic Seal)
- Commit pointer:
  - `CURRENT -> <commit_id>` (atomic pointer swap via `os.replace`).
- Manifest identity:
  - `commit_id = sha256(seed|time_ns|pid)[:16]`.
- Partition seal:
  - each active partition entry includes:
  - `file` (immutable parquet path)
  - `sha256 = SHA256(file_bytes)`
  - `size_bytes`
- Read acceptance gate:
  - before scan, verify:
  - cache policy contract (`stale_while_revalidate_sec=0`, `tombstone_priority=enforced`)
  - GC grace contract (`retention_hours_min >= 24`)
  - physical file existence and `sha256(file_bytes) == manifest.sha256`.
- Implementation path:
  - `data/feature_store.py` (`_build_feature_manifest_v2`, `_set_feature_current_commit`, `_validate_feature_manifest_hashes`, `_feature_store_scan_sql`)

## 8) Touched-Partition Commit Assembly (No Full Root Clone)
- Incremental commit path:
  - read current active slice by partition
  - merge `(date, permno)` with new rows (new wins)
  - write immutable parquet only for touched partitions
  - write v2 manifest
  - atomically swap `CURRENT` pointer
  - refresh root current-view cache (`part-000.parquet`) only for touched partitions
- Filesystem atomicity invariant:
  - every replace path asserts same-filesystem requirement before `os.replace`.
- Complexity shift:
  - old: `O(total_dataset_size)` (`copytree`)
  - new: `O(touched_partitions + metadata)`
- Implementation path:
  - `data/feature_store.py` (`_atomic_upsert_features`, `_write_partition_file_atomic`, `_refresh_current_partition_cache`, `_assert_same_filesystem_for_replace`)

## 9) MVCC Retention Safety Baseline
- Tombstone retention model:
  - replaced/removed partition files are recorded in manifest tombstones with:
  - `retained_until_utc = now + retention_hours_min`.
- Current safety posture:
  - commit path performs no aggressive physical deletion of immutable version files.
  - this is intentional to avoid invalidating long-running readers.
- Implementation path:
  - `data/feature_store.py` (`_atomic_upsert_features`, manifest `gc_policy` + `tombstones`)

## 10) Publish Lock Ownership Gate (Token-Validated)
- Publish authorization contract:
  - if update lock file exists, feature-store publish is allowed only when:
  - `expected_lock_token != ""`
  - `expected_lock_token == live_lock_token`.
- Fail-closed rules:
  - missing token -> block publish.
  - mismatched token -> block publish.
  - lock file without token metadata -> block publish.
- Enforcement path:
  - `data/feature_store.py` (`_assert_feature_write_lock`, `_set_feature_current_commit`, `_atomic_upsert_features`)
  - `run_build` now threads acquired updater lock token into partitioned write/upsert paths.

## 11) Manifest Read Strictness (Version + Partition-Key/File Consistency)
- Version gate:
  - partitioned read path requires `manifest.version == "v2"`.
  - downgraded/non-v2 pointed manifests are rejected fail-closed.
- Partition identity gate:
  - for each manifest partition entry:
  - `derived_partition(file_path) == manifest_partition_key`.
  - mismatch is rejected before scan.
- Enforcement path:
  - `data/feature_store.py` (`_feature_store_scan_sql`, `_partition_relpath_from_file_path`, `_validate_feature_manifest_hashes`)
  - tests:
    - `tests/test_feature_store.py::test_feature_store_scan_fails_closed_on_manifest_version_downgrade`
    - `tests/test_feature_store.py::test_feature_store_scan_fails_closed_on_manifest_partition_mismatch`

## 12) Fail-Loud Bootstrap Invariant (No mtime Guessing)
- Bootstrap policy:
  - for existing partitioned datasets, missing `CURRENT`/manifest lineage is treated as ambiguous state.
  - system raises `AmbiguousFeatureStoreStateError` and refuses implicit state reconstruction.
- Deterministic exception:
  - unsealed bootstrap is allowed only during the same-process `full_rebuild` handoff where dataset state is freshly materialized.
- Removed behavior:
  - no "latest mtime wins" partition inference.
- Implementation path:
  - `data/feature_store.py` (`AmbiguousFeatureStoreStateError`, `_scan_current_partition_files`, `_bootstrap_feature_manifest_v2`, `_ensure_partitioned_feature_store`)
  - tests:
    - `tests/test_feature_store.py::test_ensure_partitioned_feature_store_fails_closed_when_manifest_missing`
    - `tests/test_feature_store.py::test_bootstrap_feature_manifest_v2_fails_on_ambiguous_partition_files`

## 13) EXDEV / Cross-Filesystem Fail-Closed Contract
- Atomic replace requirement:
  - all replace paths require same-filesystem check before `os.replace`.
- Adversarial validation:
  - simulated cross-device st_dev mismatch raises fail-closed runtime error.
  - simulated pointer-swap `EXDEV` leaves previous `CURRENT` pointer unchanged.
- Implementation path:
  - `data/feature_store.py` (`_assert_same_filesystem_for_replace`, `_set_feature_current_commit`)
  - tests:
    - `tests/test_feature_store.py::test_assert_same_filesystem_for_replace_fails_closed_on_cross_device`
    - `tests/test_feature_store.py::test_set_feature_current_commit_fails_closed_on_exdev_and_preserves_pointer`

## 14) Tombstone Retention + Priority Enforcement
- Retention gate:
  - every manifest v2 tombstone requires `retained_until_utc`.
- Priority gate:
  - active partition files must not overlap with tombstoned file paths.
  - overlap triggers fail-closed read rejection (`tombstone_priority='enforced'`).
- Implementation path:
  - `data/feature_store.py` (`_validate_feature_manifest_tombstones`, `_feature_store_scan_sql`)
  - tests:
    - `tests/test_feature_store.py::test_manifest_tombstones_include_retention_window`
    - `tests/test_feature_store.py::test_feature_store_scan_fails_closed_on_missing_tombstone_retention`
    - `tests/test_feature_store.py::test_feature_store_scan_blocks_tombstoned_active_file`

## 15) Strict Orchestrator Docker Draft Contract (Stream 4 Track B)
- Draft artifact:
  - `Dockerfile.orchestrator.strict`
- Immutable base:
  - `PYTHON_BASE_REF` must be digest-pinned (`@sha256:...`).
- OS dependency determinism:
  - apt resolution pinned to `snapshot.debian.org` with fixed `DEBIAN_SNAPSHOT`.
  - runtime shared libraries are version-pinned (`ca-certificates`, `libgcc-s1`, `libstdc++6`, `libgomp1`).
- Lock artifact integrity gate:
  - dependency install source is `requirements.lock`.
  - `REQUIREMENTS_LOCK_SHA256` must match `SHA256(requirements.lock)` before install.
- Runtime scope:
  - orchestrator-focused copy set (`main_bot_orchestrator.py`, `core/`, `execution/`, `scripts/`) and deterministic entrypoint.
- Implementation path:
  - `Dockerfile.orchestrator.strict`
  - `docs/production_deployment.md` (strict draft subsection)

---

# Stream 5 Option 2 Formula Notes (Terminal-Unfilled Semantics + Recovery Anchor Backfill)

Date: 2026-03-01

## 1) Terminal unfilled local-submit contract
- Terminal unfilled predicate:
  - `terminal_unfilled := status in {canceled, cancelled, rejected, expired} AND fill_qty <= 0`
- Local-submit acceptance rule:
  - `accepted_local_submit := (ok == True) AND (terminal_unfilled == False)`
- Fail-closed output normalization:
  - `ok = False`
  - `error = "terminal_unfilled:<status>"` (unless an explicit row error already exists in orchestrator reconciliation)
- Implementation path:
  - `execution/broker_api.py` (`_is_terminal_unfilled_result`, `_normalize_submit_acceptance`)
  - `main_bot_orchestrator.py` (`_is_terminal_unfilled_execution_result`, fail-closed non-retry branch)

## 2) Recovery latency-anchor backfill formulas
- Recovery payload anchor assignment (first non-empty field wins):
  - `submit_sent_ts := submit_sent_ts || submitted_at || created_at || updated_at`
  - `broker_ack_ts := broker_ack_ts || updated_at || submitted_at || created_at`
- Implementation path:
  - `execution/broker_api.py` (`_backfill_latency_anchors`)
  - `execution/microstructure.py` (`_resolve_latency_anchors`)

## 3) Clock-drift-safe latency decomposition
- Drift-safe latency formula:
  - `latency_ms = max(0, (t_end - t_start) * 1000)`
- Applied in telemetry decomposition:
  - `command_to_submit`, `submit_to_ack`, `ack_to_first_fill`, `command_to_first_fill`.
- Implementation path:
  - `execution/microstructure.py` (`_ms_diff`)

## 4) Signed slippage invariants (no abs coercion)
- Buy delta:
  - `delta_buy = fill_vwap - arrival_price`
- Sell delta:
  - `delta_sell = arrival_price - fill_vwap`
- Slippage:
  - `slippage_bps = (delta / arrival_price) * 10,000`
- Test invariants:
  - favorable buy => `slippage_bps < 0`
  - neutral fill => `slippage_bps = 0`
- Validation path:
  - `tests/test_execution_microstructure.py`

## 5) Adaptive heartbeat freshness (rolling MAD + hard ceiling)
- Objective:
  - convert submit-to-ack latency telemetry into deterministic `PASS/BLOCK` freshness decisions without look-ahead.
- Rolling context (strictly point-in-time):
  - for row `t`, baseline uses only historical rows:
  - `history_t = {latency_{t-k}, ..., latency_{t-1}}`, `N=64`.
  - cross-batch history bootstrap is event-time ordered from sink rows:
  - `event_time_t = coalesce(arrival_ts, submit_sent_ts, broker_ack_ts, filled_at, execution_ts, captured_at_utc, created_at, updated_at)`
  - sort invariant before baseline extraction: `ORDER BY event_time_t DESC NULLS LAST`.
- Robust statistics:
  - `median_t = median(history_t)`
  - `MAD_t = median(|history_t - median_t|)`
  - `robust_sigma_t = max(1.4826 * MAD_t, 5.0)`
- Adaptive threshold:
  - when `len(history_t) >= 12`:
  - `adaptive_limit_t = median_t + 4.0 * robust_sigma_t`
  - bootstrap fallback otherwise:
  - `adaptive_limit_t = 150.0`
  - clamp:
  - `adaptive_limit_t = clip(adaptive_limit_t, 25.0, hard_ceiling_ms)`
- Hard ceiling:
  - `hard_ceiling_ms = env(TZ_EXEC_HEARTBEAT_HARD_CEILING_MS, default=500.0)`
- Deterministic decision:
  - `BLOCK(latency_missing)` if `latency_ms_submit_to_ack` is missing/non-finite
  - `BLOCK(hard_ceiling_exceeded)` if `latency_ms_submit_to_ack > hard_ceiling_ms`
  - `BLOCK(adaptive_limit_exceeded)` if `latency_ms_submit_to_ack > adaptive_limit_t`
  - else `PASS(within_limit)`
- Implementation path:
  - `execution/microstructure.py`
  - functions:
    - `evaluate_heartbeat_freshness`
    - `annotate_heartbeat_freshness_frame`
    - `build_execution_telemetry_rows` (row-level persistence fields)
    - `_load_recent_submit_to_ack_history_ms` (cross-batch history bootstrap)
- Backfill/eval runners:
  - `scripts/backfill_execution_latency.py`
  - `scripts/evaluate_execution_slippage_baseline.py`
  - source loader mode contract:
  - default: `source_mode = duckdb_strict` (fail-loud on missing/unreadable/query-failing DuckDB).
  - explicit override only: `source_mode = parquet_override` via `--source-mode parquet_override` or `TZ_EXEC_TELEMETRY_SOURCE_MODE=parquet_override`.
  - no implicit DuckDB->Parquet fallback.
  - cohort-aligned baseline formulas in `compute_slippage_baseline(...)`:
  - `sanitize(x) = x if isfinite(x) else null`
  - `cohort_slippage_bps_i = slippage_bps_i if observed else 0.0`
  - `mean_slippage_bps = mean(cohort_slippage_bps)`
  - `median_slippage_bps = median(cohort_slippage_bps)`
  - report transparency fields:
  - `cohort_rows`, `observed_rows`, `zero_imputed_rows`.

## Phase 31 Addendum: Trust-Boundary + Telemetry Durability Contracts

Date: 2026-03-01

### 1) Signed replay atomicity (`execution/signed_envelope.py`)
- Replay key:
  - `replay_key = intent_id + ":" + nonce`
- Atomic replay gate:
  - under exclusive ledger lock, apply:
  - `reject if replay_key in seen`
  - else append replay row and fsync.
- Malformed ledger handling:
  - malformed rows are quarantined to `<ledger>.malformed.jsonl`,
  - ledger is rewritten with valid lines only.

### 2) Spool UID + idempotent sink replay (`execution/microstructure.py`)
- Deterministic spool UID per consumed line:
  - `_spool_record_uid = sha1(f"{generation}:{line_start}:{payload}")`
- DuckDB idempotent insert contract:
  - insert only rows where `_spool_record_uid` is not present in target table.
- Legacy single-file parquet idempotent fallback:
  - merge and `drop_duplicates(subset in {record_id, uid, _spool_record_uid}, keep="first")` before atomic rewrite.

### 3) Corruption quarantine + stale partial-line self-heal (`execution/microstructure.py`)
- Schema-invalid JSON record quarantine reasons:
  - `schema_invalid_record_type`, `schema_row_not_object`.
- JSON parse corruption quarantine reason:
  - `json_decode_error`.
- Trailing partial-line stale policy:
  - `quarantine_trailing_partial := (line has no '\n') AND (now - spool_mtime >= 2.0s)`.

### 4) Local-submit telemetry durability gate (`main_console.py`)
- Durability acceptance rule:
  - `durability_pass := drained == True AND pending_bytes == 0 AND last_flush_error == ""`.
- Local-submit success/notify is blocked unless `durability_pass` is true.

### 5) Snapshot/semantic coercion contracts
- Alpha candidate ranking:
  - `rank_key = (-numeric(composite_score), +numeric(permno))` (stable sort; NaN last).
  - file: `strategies/alpha_engine.py`.
- Trend veto parser:
  - `True tokens = {true,1,yes,on,t,y}`,
  - `False tokens = {false,0,no,off,f,n}`,
  - unknown -> default policy.
  - file: `strategies/alpha_engine.py`.
- Ticker-pool boolean parser uses deterministic token sets for `style_compounder_gate` and `weak_quality_liquidity`.
  - file: `strategies/ticker_pool.py`.

### 6) Stream 5 Option 2 reconciliation addendum (`main_bot_orchestrator.py`, `execution/microstructure.py`)
- Terminal partial-fill fail-closed rule (retry loop):
  - `terminal_partial := status in {canceled,cancelled,rejected,expired,done_for_day,stopped,suspended} AND fill_qty > 0`
  - action: finalize row with `ok=False` and no retry enqueue.
- Summary-only fill consistency rule:
  - if `partial_fills == []` and order-level summary is present (`fill_count>0`, `fill_qty>0`, `fill_vwap>0`), synthesize one fill row:
  - `fill_source = summary_fallback`, `fill_qty = fill_summary.fill_qty`, `fill_price = fill_summary.fill_vwap`.
- Legacy parquet null-key dedupe rule:
- for each dedupe key in `{record_id, uid, _spool_record_uid}`:
- dedupe only rows with non-empty key;
- preserve all rows where key is null/empty token (`'', none, null, nan`).

## Phase 31 Option 1 Medium-Risk Reconciliation Addendum (2026-03-01)

### 1) Deterministic spool record identity (retry-idempotent across append calls)
- Record UID payload (capture-time excluded):
  - `uid_payload := {"record_type": record_type, "row": row_without(captured_at_utc)}`
- UID formula:
  - `_spool_record_uid := sha1(json.dumps(uid_payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True))`
- Implementation path:
  - `execution/microstructure.py` (`_build_spool_records`)

### 2) Immediate-write vs prepared counters
- Prepared counters:
  - `orders_prepared := len(order_rows)`
  - `fills_prepared := len(fill_rows)`
- Immediate durable counters:
  - `fully_appended := (spool_records_appended == spool_records_total)`
  - `orders_written := orders_prepared if fully_appended else 0`
  - `fills_written := fills_prepared if fully_appended else 0`
- Intent:
  - prevent reporting immediate writes when append was buffered/contended/failed.
- Implementation path:
  - `execution/microstructure.py` (`append_execution_microstructure`)

### 3) Retry-buffer overflow contract (fail-closed)
- Overflow predicate:
  - `overflow := (projected_records > SPOOL_BUFFER_MAX_RECORDS) OR (projected_bytes > SPOOL_BUFFER_MAX_BYTES)`
- Overflow action:
  - do not partially enqueue retry batch,
  - emit `last_flush_error`,
  - raise `RuntimeError("telemetry spool retry buffer overflow: ...")`.
- Implementation path:
  - `execution/microstructure.py` (`_buffer_records_for_retry`, `_TelemetrySpooler.append`)

### 4) Shutdown durability gate (fail-closed if pending telemetry remains)
- Shutdown sequence:
  - set stop signal,
  - best-effort synchronous flush attempts until deadline,
  - if any of `{pending_bytes > 0, buffer_drop_count > 0, last_flush_error != none}` after deadline
    => raise `MicrostructureFlushError("telemetry spool shutdown fail-closed: ...")`.
- Intent:
  - remove silent buffered-data loss and sink-error suppression on shutdown.
- Implementation path:
  - `execution/microstructure.py` (`_TelemetrySpooler.stop`, `_shutdown_execution_microstructure_spoolers`)

### 5) Recovery anchor strictness for heartbeat classification
- Submit anchor:
  - `submit_sent_ts := submit_sent_ts || submitted_at || created_at || updated_at`
- Ack anchor (no submit/created fallback):
  - `broker_ack_ts := broker_ack_ts || ack_ts || updated_at`
- Result:
  - if ack anchor missing then `latency_ms_submit_to_ack = None` and heartbeat classification is `BLOCK(latency_missing)`.
- Implementation path:
  - `execution/microstructure.py` (`_resolve_latency_anchors`, `evaluate_heartbeat_freshness`)

### 6) Replay-ledger malformed-state contract + growth cap
- Malformed-line detection contract:
  - if malformed rows detected in replay ledger under lock:
  - `quarantine(malformed)` + `rewrite(valid_lines)` + reject current submit (`fail-closed`).
- Ledger growth cap:
  - `max_rows := env(TZ_EXECUTION_REPLAY_LEDGER_MAX_ROWS, default=50000)`
  - `valid_lines := tail(valid_lines, max_rows)` + rewrite + trim telemetry event.
- Replay lock budget:
  - `DEFAULT_EXECUTION_REPLAY_LOCK_TIMEOUT_MS := 25`
- Implementation path:
  - `execution/signed_envelope.py` (`assert_not_replayed_and_append_atomic`, `_resolve_replay_ledger_max_rows`)

## Stream 1 PiT Sprint Addendum (2026-03-01)

### 1) Dual-time PiT gate (`data/fundamentals.py`)
- Time axes:
  - `T_valid := release_date`
  - `T_knowledge := published_at`
  - `T_simulation := as_of_date` (timestamp precision retained)
- Gate invariant:
  - record is visible iff:
  - `T_knowledge <= T_simulation` and `T_valid <= T_simulation`
- Loader application:
  - `load_quarterly_fundamentals(...)`
  - `load_fundamentals_snapshot(...)`

### 2) Timestamp binding contract (`data/fundamentals.py`, `data/feature_store.py`)
- Binding token:
  - `token := HMAC_SHA256(secret, iso8601(T_simulation))`
- Validation:
  - `compare_digest(token, HMAC_SHA256(secret, iso8601(T_simulation)))`
- Strict mode:
  - `T0_STRICT_SIMULATION_TS_BINDING=1` => token required when `as_of_date` is supplied.
  - secret source:
  - `T0_SIMULATION_TS_BINDING_SECRET` or explicit arg.
- Feature-store integration:
  - strict-mode token is generated once at `close_wide.index[-1]`
  - token/secret are plumbed to:
  - `build_fundamentals_daily(...)`
  - `load_fundamentals_snapshot(...)`

### 3) Fallback valid-time masking (`data/fundamentals.py`)
- Fallback path builds matrices from `published_at` broadcasts.
- Reconciliation guard:
  - `valid_time_mask(date, permno) := release_date(date, permno) <= date`
  - all fallback matrices are masked by `valid_time_mask`.
- Quality gate:
  - `quality_pass := (roic > 0) AND (revenue_growth_yoy > 0) AND (0 <= age_days <= max_age_days)`.

### 4) Deterministic dedupe tie-break (`data/fundamentals.py`)
- Dedupe key remains:
  - `(permno, release_date, published_at)` keep latest.
- Deterministic tie-break for equal `ingested_at`:
  - `_row_hash := hash_pandas_object(sorted_row_columns)`
  - sort order:
  - `(permno, release_date, published_at, ingested_at, _row_hash)`
  - dedupe then drop `_row_hash`.

### 5) Yearly-union eradication to t-1 daily selector (`data/feature_store.py`)
- Universe anchor:
  - `anchor := normalize(start_date)` (or clamped `end_date`).
- Eligibility:
  - `date < anchor` (strict t-1, no same-day usage).
- Selector:
  - compute last tradable date `< anchor`,
  - rank by `dollar_volume = signal_price * volume` on that date,
  - choose `top yearly_top_n` by `(dollar_volume desc, permno asc)`.
- Result:
  - active selector path no longer uses full-year pre-calculated blocks.

## Stream 1 Option 1 Isolated High Backlog Reconciliation (2026-03-01)

### 1) Yearly-union as-of anchor contract (`data/feature_store.py`)
- Selector anchor:
  - `anchor_date := append_start_ts` when incremental universe refresh is active.
  - `anchor_date := start_date` otherwise.
- Liquidity cutoff:
  - annual-liquidity source rows must satisfy `date <= anchor_date`.
- Eligible union years:
  - primary set: `eligible_years = {y | y < year(anchor_date)}`
  - bootstrap fallback: `eligible_years = {year(anchor_date)}` only when no prior year is available.
- Selection:
  - for each `y in eligible_years`, choose top `yearly_top_n` by annual dollar volume, then union.
- Implementation path:
  - `data/feature_store.py` (`_top_liquid_permnos_yearly_union`, `run_build`)
  - tests:
    - `tests/test_feature_store.py::test_top_liquid_permnos_yearly_union_is_asof_anchored`
    - `tests/test_feature_store.py::test_top_liquid_permnos_yearly_union_excludes_same_day_spike`
    - `tests/test_feature_store.py::test_top_liquid_permnos_yearly_union_uses_patch_precedence_before_anchor`

### 2) Feature-spec fail-closed execution contract (`data/feature_store.py`)
- Missing context inputs:
  - `missing_inputs(spec) != empty => raise FeatureSpecExecutionError`.
- Missing fundamental dependencies:
  - for fundamental specs, let `generated = prior_spec_outputs`.
  - `missing_dep = {i in spec.inputs | i not in dependency_columns and i not in generated}`.
  - `missing_dep != empty => raise FeatureSpecExecutionError`.
- Runtime and post-processing failures:
  - `spec.func` exceptions must be wrapped as `FeatureSpecExecutionError`.
  - `result` type must satisfy `isinstance(result, pandas.DataFrame)`.
  - non-DataFrame or reindex failures must raise `FeatureSpecExecutionError`.
- Implementation path:
  - `data/feature_store.py` (`_execute_feature_specs`)
  - tests:
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_spec_exception`
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_non_dataframe_result`
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_missing_inputs`
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_missing_fundamental_dependencies`
    - `tests/test_feature_store.py::test_execute_feature_specs_allows_fundamental_inputs_from_prior_spec_outputs`

## Stream 5 Telemetry Constraint Reconciliation (2026-03-01)

### 1) Authoritative execution-receipt gate (`main_bot_orchestrator.py`)
- For any success-path receipt (`ok == True`), required authoritative fields are:
  - `filled_qty > 0`
  - `filled_avg_price > 0`
  - `execution_ts != ""`
- Acceptance formula:
  - `authoritative_ok := ok AND has(symbol, side, qty) AND has(filled_qty, filled_avg_price, execution_ts)`
- Fail-closed contract:
  - if `ok == True` but authoritative fields are missing:
  - trigger reconciliation polling via `get_order_by_client_order_id(client_order_id)`.
  - if reconciliation still lacks authoritative fields after poll budget:
  - raise `AmbiguousExecutionError` and abort acceptance.
- Applies to:
  - direct `ok=True` submit payloads,
  - `already exists` recovery path promoted to success.
- Implementation path:
  - `main_bot_orchestrator.py`:
    - `_normalize_execution_receipt_fields`
    - `_ok_true_result_missing_required_broker_fields`
    - `_poll_reconciliation_receipt`
    - `execute_orders_with_idempotent_retry`

### 2) Canonical execution timestamp resolution (`execution/broker_api.py`)
- Canonical resolver:
  - `execution_ts := execution_ts || fill_summary.first_fill_ts || min(partial_fills.fill_ts) || filled_at`
- Normalization rule:
  - `_normalize_submit_acceptance(...)` now injects `execution_ts` when resolvable from broker snapshot/fill telemetry.
- Implementation path:
  - `execution/broker_api.py`:
    - `_resolve_execution_ts`
    - `_normalize_submit_acceptance`

### 3) Regression coverage
- `tests/test_main_bot_orchestrator.py`:
  - sparse `ok=True` payload with symbol/side/qty but missing authoritative execution fields now raises `AmbiguousExecutionError` and polls reconciliation,
  - sparse `ok=True` payload reconciles to success when lookup returns definitive receipt,
  - sparse `already exists` recovery now also raises `AmbiguousExecutionError` when reconciliation is unavailable,
  - existing success-path doubles upgraded with `filled_qty`, `filled_avg_price`, `execution_ts`.
- `tests/test_execution_controls.py`:
  - broker submit result now asserts `execution_ts` derivation for:
    - activity-derived fill summary path,
    - snapshot fallback fill path.

## Stream 5 Sprint+1 Follow-Through (2026-03-01)

### 1) Strict success invariant (`main_bot_orchestrator.py`)
- Authoritative success formula:
  - `success := (ok == True)`
  - `AND (filled_qty > 0)`
  - `AND (filled_avg_price > 0)`
  - `AND (execution_ts parses as ISO-8601 with timezone)`
  - `AND (filled_qty <= order_qty)`
- Implementation path:
  - `_to_utc_execution_ts_or_none`
  - `_normalize_execution_receipt_fields`
  - `_execution_fill_qty_within_order_bounds`
  - `_ok_true_result_missing_required_broker_fields`

### 2) Ambiguity trap hardening (`main_bot_orchestrator.py`)
- Reconciliation lookup contract:
  - `lookup_result := timeout_guard(get_order_by_client_order_id, per_poll_timeout)`
  - `if timeout/exception: record issue tag and continue within poll budget`
  - `if budget exhausted without authoritative receipt: raise AmbiguousExecutionError(issue_tag)`
- Duplicate row deterministic fail-closed contract:
  - `dup_cid := {cid | count(batch_rows[cid]) > 1}`
  - `if cid in dup_cid: result.ok = False; result.error = duplicate_batch_result_cid`
- Implementation path:
  - `_poll_lookup_with_timeout`
  - `_poll_reconciliation_receipt`
  - `execute_orders_with_idempotent_retry` (duplicate CID pre-scan + fail-closed output)

### 3) Regression coverage
- `tests/test_main_bot_orchestrator.py`:
  - malformed `execution_ts` fail-closed ambiguity,
  - overfilled-qty bound fail-closed ambiguity,
  - duplicate-output-CID fail-closed determinism (both row orders),
  - reconciliation lookup timeout issue surfacing,
  - zero-poll-budget ambiguity.

## Round Update (2026-03-01) - Stream 5 Authoritative Receipt SAW Reconciliation (CID + Terminal Taxonomy)
- Status: Completed (SAW reviewer recheck PASS; no unresolved in-scope Critical/High).
- Added in this round:
  - `main_bot_orchestrator.py`:
    - success receipt gate now requires broker-origin `client_order_id` for all `ok=True` acceptance paths,
    - reconciliation remains mandatory for sparse success payloads and now also covers missing broker CID in direct `ok=True` paths,
    - terminal outcomes are now canonicalized with deterministic taxonomy:
      - normalized terminal `status`,
      - `terminal_reason` (`terminal_unfilled` or `terminal_partial_fill`),
      - canonical `error = <terminal_reason>:<status>`,
      - preserved passthrough diagnostics in `broker_error_raw`,
    - batch submit exceptions from `rebalancer.execute_orders(...)` are now fail-closed/retry-aware:
      - retry until `max_attempts`,
      - emit deterministic `retry_exhausted` with `last_error=batch_exception:<ExceptionType>` on exhaustion.
  - `tests/test_main_bot_orchestrator.py`:
    - added non-recovery sparse `ok=True` missing broker CID ambiguity regression,
    - added terminal status normalization + broker error preservation regression,
    - updated terminal fail-closed expectations to canonical terminal taxonomy fields,
    - added batch-exception retry recovery and retry-exhaustion regressions.
- Formula/contract lock:
  - `authoritative_ok := (ok == True) AND has(client_order_id, symbol, side, qty) AND (filled_qty > 0) AND (filled_avg_price > 0) AND (execution_ts is valid_iso8601_tz) AND (filled_qty <= order_qty)`.
  - `if authoritative_ok == False: poll_reconciliation(client_order_id)`.
  - `if reconciliation unavailable after budget: raise AmbiguousExecutionError(reconciliation_issue)`.
  - `terminal_reason := terminal_unfilled if effective_fill_qty <= 0 or invalid else terminal_partial_fill`.
  - `terminal_error := terminal_reason + ":" + normalized_terminal_status`.
  - `if execute_orders batch raises and attempt < max_attempts: retry; else fail_closed(error=retry_exhausted, last_error=batch_exception:<ExceptionType>)`.
- Verification:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`196 passed`).
  - SAW reviewer final confirmations:
    - Reviewer A PASS,
    - Reviewer B PASS,
    - Reviewer C PASS.

## Phase 32 Step 4 Exception Taxonomy Split Addendum (2026-03-02)

### 1) Binary broker-exception taxonomy (`main_bot_orchestrator.py`)
- Canonical classes:
  - `TERMINAL`: hard business/validation/auth rejects (fail-closed now).
  - `TRANSIENT`: network/timeout/service/rate-limit errors (bounded retry).
- Classifier contract:
  - `exception_class := _classify_broker_exception(exc)` where `exception_class in {"TERMINAL","TRANSIENT"}`.
  - unknown exception patterns default to `TRANSIENT` (bounded retry safety).

### 2) Deterministic routing contract (`execute_orders_with_idempotent_retry`)
- Batch exception path:
  - `if TERMINAL -> error=FAILED_REJECTED, exception_class=TERMINAL, bypass retry loop`.
  - `if TRANSIENT -> bounded retry; on exhaustion error=retry_exhausted, exception_class=TRANSIENT`.
- Row-level broker-result path:
  - classify terminal/transient before retry token evaluation.
  - terminal precedence rule:
    - if classifier returns `TERMINAL`, fail closed immediately even when error text also contains retryable tokens.
  - `if non-retryable error text and terminal classification -> FAILED_REJECTED` (no raw free-form pass-through).
  - `retry_exhausted` outputs are emitted via one shared builder so canonical fields are stable across all transient exhaustion branches.

### 3) Canonical output schema
- Terminal fail-closed:
  - `{"ok":false,"error":"FAILED_REJECTED","exception_class":"TERMINAL","canonical_reason":...,"rejection_reason":...,"client_order_id":...,"attempt":...}`
- Transient exhausted:
  - `{"ok":false,"error":"retry_exhausted","exception_class":"TRANSIENT","canonical_reason":...,"last_error":...,"client_order_id":...,"attempt":...}`

### 4) Bounded zero-timeout lookup safety
- Reconciliation timeout guard:
  - `effective_timeout := max(timeout_seconds, 0.01)`
- Intent:
  - remove synchronous `timeout<=0` lookup execution path that could stall on hanging broker lookups.

## Phase 32 Step 1 (2026-03-02) - Reconciliation Timeout Soak and Thread Isolation

### 1) Cooperative cancellation semantics (`main_bot_orchestrator.py`)
- Lookup timeout wrapper now attempts cooperative cancellation when broker adapter exposes `cancel_event`.
- Canonical taxonomy:
  - `lookup_cancelled` when lookup raises `asyncio.CancelledError`,
  - `lookup_timeout:<seconds>s` when timed-out worker exits but does not emit explicit cancel/exception,
  - `lookup_timeout:<seconds>s:uncooperative` when worker remains alive beyond timeout path.

### 2) Sticky lookup issue precedence (`main_bot_orchestrator.py`)
- Reconciliation polling now preserves the highest-priority lookup issue across poll cycles.
- Contract:
  - once a `lookup_*` issue appears, later generic states (`reconciliation_receipt_unavailable`, `non_authoritative_reconciliation_receipt`) cannot overwrite forensic taxonomy.
  - `:uncooperative` timeout is terminal for the current reconciliation attempt to avoid spawning additional stuck lookup workers.

### 3) Dedicated reconciliation quarantine sink (`main_bot_orchestrator.py`)
- Added durable JSONL quarantine writer for lookup timeout/cancel/exception families only.
- Writer contract:
  - lock-serialized append via sidecar `.lock`,
  - low-level append write (`O_APPEND`) + `fsync`,
  - parent-dir fsync on first create where supported,
  - schema-stable payload with `schema_version=1`.

### 4) Synthetic chaos + isolation coverage (`tests/test_main_bot_orchestrator.py`)
- Added synthetic chaos broker with deterministic cancel-aware hanging lookup.
- Added regressions:
  - timeout path quarantines with `:uncooperative`,
  - cooperative cancellation path surfaces `lookup_cancelled` and quarantines deterministically,
  - mixed-poll precedence keeps `lookup_cancelled`,
  - blocked reconciliation lookup does not block telemetry spool append/flush,
  - concurrent quarantine writers remain lossless and parseable.

## Phase 35 Repaired `permno` Overlay Notes (2026-03-08)

### 1) Canonical repaired feature formulas
- `mom_12m`:
  - formula: `(adj_close_t / adj_close_t-252) - 1`
  - implemented in: `data/feature_derivation.py` (`derive_mom_12m`)
  - materialized by: `scripts/build_phase35_repaired_features.py`
- `realized_vol_21d`:
  - formula: `std(pct_change(adj_close), 21d) * sqrt(252)`
  - implemented in: `data/feature_derivation.py` (`derive_realized_vol_21d`)
  - materialized by: `scripts/build_phase35_repaired_features.py`
- `illiq_21d`:
  - formula: `mean(abs(daily_return) / dollar_volume, 21d) * 1e6`
  - where `dollar_volume = adj_close * volume`
  - implemented in: `data/feature_derivation.py` (`derive_illiq_21d`)
  - materialized by: `scripts/build_phase35_repaired_features.py`
- `quality_composite`:
  - explicit formula: `0.4 * roic + 0.3 * roe_q + 0.3 * revenue_growth_yoy`
  - implemented in: `data/feature_derivation.py` (`derive_quality_composite_from_panel`)
  - materialized by: `scripts/build_phase35_repaired_features.py`

### 2) Repaired validation contract
- Provenance nulls are treated as `missing`, not skipped.
- Price-derived factors are validated only on rows with the required raw inputs:
  - `mom_12m`: `adj_close`
  - `realized_vol_21d`: `adj_close`
  - `illiq_21d`: `adj_close` and non-zero `volume`
- Implemented in: `data/validation.py` (`summarize_derived_feature_missingness`, `validate_phase35_repaired_window`)

### 3) Attribution numeric-column contract
- `scripts/attribution_report.py` must exclude `*_source` and `score_valid` from numeric IC and attribution math.
- Only numeric factor columns should be pivoted into factor IC / attribution calculations.

### 4) Governed evidence windows
- Calibration: `2022-01-01` → `2023-06-30`
- Validation: `2023-07-01` → `2024-03-31`
- Holdout: `2024-04-01` → `2024-12-31`
- `2020-2021` are warmup only for the repaired Phase 35 rerun path.



## Phase 36 Robustness Contract Notes (2026-03-08)

### 1) Locked friction-stress formula
- explicit formula: `ic_net_estimated = ic_gross - ((cost_bps / 10000) * turnover_monthly * 12.0)`
- implemented in: `scripts/phase36_bundle_robustness_round.py` (`compute_friction_stress`)
- validated by: `scripts/validate_phase36_bundle_robustness_outputs.py`

### 2) Locked 20bps holdout fail-closed floor
- explicit rule: `kill_triggered = holdout_net_ic_at_20bps <= 0`
- implemented in: `scripts/phase36_bundle_robustness_round.py` (`compute_friction_stress`, `apply_majority_rubric`)
- validated by: `scripts/validate_phase36_bundle_robustness_outputs.py`, `tests/test_phase36_bundle_robustness_round.py`, `tests/test_validate_phase36_bundle_robustness_outputs.py`

### 3) Locked portfolio rubric
- explicit rule:
  - `Continue` if `continue_votes >= 3`
  - `Pause` if `pause_votes >= 3`
  - otherwise `Pivot`
- implemented in: `scripts/phase36_bundle_robustness_round.py` (`apply_majority_rubric`)
- evidence artifact: `data/processed/phase36_rule100/robustness/bundle_robustness_recommendation.json`

## Phase 38 Bounded Gate Contract Notes (2026-03-09)

### 1) Locked dual-gate formulas
- `active_days = count(governed trading days in the window where the latest in-window frozen method status is 'ready' or 'valid')`
- `eligible_days = count(governed trading days in the target window recovered from frozen equal_weight diagnostics)`
- `coverage_ratio = active_days / eligible_days`
- `method_gate_pass = (validation_active_days >= 252) and (validation_coverage_ratio >= 0.80) and (holdout_active_days >= 252) and (holdout_coverage_ratio >= 0.80)`
- `portfolio_gate_decision = Continue if continue_votes >= 2; Pause if pause_votes >= 2; otherwise Pivot`

### 2) Frozen execution reconstruction
- Daily governed calendar source: `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv` rows for `equal_weight`.
- Optimized-method state expansion: forward-fill each month's frozen `status` within the same governed window to the recovered daily calendar; do not cross window boundaries.
- Consistency check: `reconstructed_warmup_days == portfolio_method_comparison.warmup_days` for `inverse_vol_63d` and `capped_risk_budget`.

### 3) Evidence surface
- Bounded execution path: one-off `.venv` inline Python execution from the terminal using frozen artifacts only; no persisted Phase 38 execution script was added by contract.
- Evidence artifacts: `data/processed/phase38_gate/gate_diagnostics_delta.csv`, `data/processed/phase38_gate/gate_recommendation.json`.

## Phase 39 Reachability Policy Notes (2026-03-09)

### 1) Locked policy formulas
- `active_days_window = count(governed trading days in the window where the method is in a valid investable state)`
- `eligible_days_window = count(governed trading days available inside the governed window)`
- `coverage_ratio_window = active_days_window / eligible_days_window`
- `threshold_reachable = MIN_ACTIVE_DAYS_THRESHOLD <= min(eligible_days_validation, eligible_days_holdout)`
- `dual_gate_window_pass = (active_days_window >= MIN_ACTIVE_DAYS_THRESHOLD) and (coverage_ratio_window >= MIN_COVERAGE_RATIO_THRESHOLD)`
- `future_gate_proposal_allowed = threshold_reachable`
- `future_execution_authorized = threshold_reachable and explicit_future_governance_instruction`

### 2) Locked governance interpretation
- If `threshold_reachable = false`, the disposition is governance `Hold` before any threshold approval, worker guide, or execution proposal can advance.
- Impossible geometry is a policy/window-design issue, not a method-quality failure and not a reason to mutate frozen Phase 37/38 evidence.
- The dual gate family is preserved; Phase 39 does not rewrite the frozen `252 / 0.80` constants.

### 3) Evidence and implementation boundary
- Docs-only evidence surface: `docs/phase_brief/phase39-brief.md`, `docs/notes.md`, `docs/context/current_context.json`, `docs/context/current_context.md`, `docs/decision log.md`, `docs/lessonss.md`, `docs/saw_reports/saw_phase39_reachability_policy_20260309.md`.
- No `.py` implementation file is authorized in Phase 39; the pre-execution reachability screen is a governance policy contract only in this round.

## Phase 40 Geometry Remedy Notes

1. Reachability formula: threshold_reachable = MIN_ACTIVE_DAYS_THRESHOLD <= min(eligible_days_validation, eligible_days_holdout)
2. Remedy options: Method A (lower threshold - PRIMARY), Method B (redesign windows), Method C (redesign metric)
3. Planning anchor: Method A, no threshold value activated in Phase 40
4. Product targets: shadow_ship_target_phase = 48, capital_decision_target_phase >= 50
5. Boundaries: Docs-only, no execution token, no remedy execution

## Phase 41 Threshold Trade-Off Notes

1. Candidate set: `T = {180, 150, 126}` days under Method A only
2. Fixed dimension weights:
   - `w_auditability = 25`
   - `w_geometry = 30`
   - `w_dual_gate = 15`
   - `w_governance = 15`
   - `w_shadow_path = 15`
3. Ordinal scoring scale: `s_i(t) ∈ {1,2,3,4,5}` where `5` is strongest governance fit and `1` is unacceptable for current objectives
4. Weighted score formula:
   - `score(t) = (25*s_auditability(t) + 30*s_geometry(t) + 15*s_dual_gate(t) + 15*s_governance(t) + 15*s_shadow_path(t)) / 100`
5. Locked Phase 41 ordinal scores:
   - `score_components(180) = {auditability:5, geometry:2, dual_gate:5, governance:5, shadow_path:4}`
   - `score_components(150) = {auditability:4, geometry:4, dual_gate:5, governance:4, shadow_path:4}`
   - `score_components(126) = {auditability:3, geometry:5, dual_gate:5, governance:3, shadow_path:3}`
6. Ranked output:
   - `score(150) = 4.15`
   - `score(180) = 3.95`
   - `score(126) = 3.90`
   - ranked order = `150 > 180 > 126`
7. Governance interpretation:
   - ranked order is a CEO decision surface only
   - no threshold is enacted in Phase 41
   - threshold selection remains deferred to Phase 42 governance review
8. Implementation boundary:
   - no `.py` implementation file is authorized in Phase 41
   - no rerun or recomputation of frozen Phase 37/38 evidence is authorized in Phase 41

## Phase 42 Threshold Governance Notes

1. Governance-selected implementation target:
   - `MIN_ACTIVE_DAYS_THRESHOLD_target = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` (unchanged)
2. Selection interpretation:
   - `150` is selected as the balanced option under the sealed Phase 41 scorecard
   - `180` remains conservative fallback
   - `126` remains aggressive reserve option
3. Governance rationale:
   - `150` preserves the dual-gate family with materially stronger reachability margin than `180`
   - `150` avoids the higher governance and shadow-validation burden associated with `126`
4. Implementation boundary:
   - selected threshold is governance-locked for future planning only
   - code/constants remain unchanged until a later explicitly authorized implementation round
   - no rerun or recomputation of frozen Phase 37/38 evidence is authorized in Phase 42
   - no gate re-execution or execution token is authorized in Phase 42
5. Next-phase boundary:
   - Phase 43 is opened for implementation planning only
   - research quarantine and inherited hard blocks remain unchanged

## Phase 43 Implementation Planning Notes

1. Future authoritative constant owner:
   - `strategies/phase37_portfolio_registry.py`
   - planned registry constants:
     - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
     - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
2. Future consumer rule:
   - `scripts/phase38_gate_execution.py` must import the gate constants from `strategies/phase37_portfolio_registry.py`
   - runtime code may not hardcode `150` or `0.80` outside the registry
3. Future gate formulas (implementation target only; not enacted in Phase 43):
   - `dual_gate_window_pass = (active_days_window >= MIN_ACTIVE_DAYS_THRESHOLD) and (coverage_ratio_window >= MIN_COVERAGE_RATIO_THRESHOLD)`
   - `method_gate_pass = dual_gate_window_pass_validation and dual_gate_window_pass_holdout`
4. Future validation path (post-authorization only):
   - targeted constant propagation:
     - `.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase38_gate_execution.py -q`
   - bounded rerun:
     - `.venv\Scripts\python scripts\phase38_gate_execution.py`
   - bounded output validator:
     - `.venv\Scripts\python scripts\validate_phase38_gate_outputs.py`
5. Planning boundary:
   - Phase 43 seals the implementation contract only
   - Phase 44 reviews the contract before any later implementation authorization
   - Phase 37 and Phase 38 evidence remain frozen throughout Phase 43

## Phase 45 Implementation Completion Notes

1. Bounded implementation enactment:
   - Registry constants enacted in `strategies/phase37_portfolio_registry.py`:
     - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
     - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
   - Gate execution script implemented: `scripts/phase38_gate_execution.py`
   - Gate output validator implemented: `scripts/validate_phase38_gate_outputs.py`
   - Targeted tests added for registry ownership and gate propagation
2. Gate execution results (150/0.80 thresholds):
   - Portfolio gate decision: **Pause**
   - Vote counts: Continue=0, Pause=3, Pivot=0
   - All three approved methods (equal_weight, inverse_vol_63d, capped_risk_budget) failed dual-gate thresholds
   - Validation window: 390 active days, 69.5% coverage (passes 150 active days, fails 80% coverage)
   - Holdout window: 378 active days, 66.0% coverage (passes 150 active days, fails 80% coverage)
3. Bounded outputs regenerated:
   - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
   - `data/processed/phase38_gate/gate_recommendation.json`
4. Implementation scope discipline:
   - Write surface limited to authorized files only
   - No production or shadow deployment
   - No rerun outside bounded Phase 38 gate path
   - Frozen Phase 37 evidence preserved
5. Next-phase boundary:
   - Phase 45 implementation complete
   - Phase 46 opens for governance review of gate results
   - Research quarantine and inherited hard blocks remain unchanged

## Phase 47 Coverage-Ratio Remedy Notes

1. Locked planning path:
   - coverage ratio is the sole in-scope problem
   - `Method A` is the only active remedy family in Phase 47
   - future policy shape remains one common coverage floor across validation and holdout
   - any later evidence refresh is limited to one narrow bounded rerun against frozen Phase 37 / Phase 45 evidence
2. Accepted packet constants and evidence:
   - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
   - validation coverage = `0.6952`
   - holdout coverage = `0.6597`
   - `min_current_coverage = min(0.6952, 0.6597) = 0.6597`
3. Candidate coverage-floor set carried forward for later governance:
   - `C = {0.65, 0.60, 0.55}`
4. Coverage-margin formula:
   - `coverage_margin(c) = min_current_coverage - c`
5. Candidate margins from the accepted packet:
   - `coverage_margin(0.65) = 0.0097`
   - `coverage_margin(0.60) = 0.0597`
   - `coverage_margin(0.55) = 0.1097`
6. Planning interpretation:
   - `0.65` = conservative near-pass option
   - `0.60` = balanced option
   - `0.55` = aggressive reserve option
7. Boundary:
   - no coverage floor is selected in Phase 47
   - no coverage floor is enacted in Phase 47
   - no `.py` implementation file is authorized in Phase 47

## Phase 47 Coverage-Floor Selection Notes

1. Selected policy constant:
   - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`
2. Selection formula:
   - `coverage_margin(c) = min_current_coverage - c`
   - `min_current_coverage = min(0.6952, 0.6597) = 0.6597`
3. Decision rationale:
   - `coverage_margin(0.65) = 0.0097` → selected as the narrow conservative pass floor
   - `coverage_margin(0.60) = 0.0597` → feasible but looser than required
   - `coverage_margin(0.55) = 0.1097` → widest margin with the highest dilution risk
4. Governance interpretation:
   - `0.65` is selected in Phase 47
   - enactment is deferred to the bounded Phase 48 packet
   - active-days remedy remains closed

## Phase 48 Bounded Enactment Notes

1. Authoritative Python ownership:
   - constant owner: `strategies/phase37_portfolio_registry.py`
   - runtime gate consumer: `scripts/phase38_gate_execution.py`
   - bounded output validator: `scripts/validate_phase38_gate_outputs.py`
2. Runtime formulas:
   - `gate_pass(window) = (active_days(window) >= 150) AND (coverage_ratio(window) >= 0.65)`
   - `window_regime_days(window, regime) = max(n_days)` across duplicate sleeve rows for the same `(window, regime)`; if duplicate rows disagree on `n_days`, fail closed
   - `active_days(window) = SUM(window_regime_days(window, regime))` for `regime in {GREEN, AMBER}`
   - `total_days(window) = SUM(window_regime_days(window, regime))` for all regimes
   - `coverage_ratio(window) = active_days(window) / total_days(window)`
   - portfolio disposition remains `Pause` on any governed window miss
3. Bounded output surface:
   - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
   - `data/processed/phase38_gate/gate_recommendation.json`
4. Corrected Phase 48 rerun result:
   - validation = `130` active days, `0.6952` coverage
   - holdout = `126` active days, `0.6597` coverage
   - coverage clears `0.65`, active days fail `150`
   - corrected packet = `Pause`
5. Corrective note:
   - an earlier interim `Continue` was withdrawn after SAW found duplicated sleeve-row day counts were being summed as distinct governed days
6. Hard blocks preserved:
   - no production or shadow deployment
   - no `permno` migration
   - no governed `10` bps rewrite
   - no new sleeves
   - no Sovereign cartridge integration inside the bounded gate packet

## Phase 49 Shadow-Evidence Integrity Notes

1. Readiness formulas:
   - `shadow_capture_day_count = count(distinct artifact_trade_date)`
   - `shadow_capture_window_ok = (min(artifact_trade_date) >= approved_window_start) AND (max(artifact_trade_date) <= approved_window_end)`
   - `shadow_capture_source_ok = scanner_outputs_from_runtime AND c3_deltas_from_day_specific_telemetry AND no_placeholder_synthesis`
   - `shadow_capture_ready = (shadow_capture_day_count >= 5) AND shadow_capture_window_ok AND shadow_capture_source_ok`
2. Current repository state on 2026-03-11:
   - `scripts/collect_shadow_evidence.py` writes all five day files in a single run
   - `collect_daily_scanner_output()` emits synthetic ticker rows rather than runtime-captured scanner output
   - `collect_c3_delta_snapshot()` selects the latest available telemetry event, so day files are relabeled snapshots rather than day-specific captures
3. Phase boundary:
   - Phase 49 is docs-only reconciliation
   - Phase 50 paper-curve remains blocked until `shadow_capture_ready = True` or governance explicitly accepts demo-only evidence
4. Source paths:
   - `scripts/collect_shadow_evidence.py`
   - `data/shadow_evidence/*.json`
   - `data/telemetry/simulated_routing_intents.log`

## Phase 50 Shadow-Ship Readiness Notes

1. Authoritative Python ownership:
   - paper-curve generator: `scripts/run_phase50_paper_curve.py`
   - paper-only dashboard surface: `views/elite_sovereign_view.py`
2. Demo-mode paper formulas:
   - `target_weight_i = sovereign_score_i / sum_j(sovereign_score_j)`
   - `signal_edge_i = demand_i + pricing_i + margin_i - supply_i`
   - `demo_return_i = clip((0.002 * signal_edge_i) + (0.0001 * hf_scalar_i) + regime_bias_i, -0.02, 0.02)`
   - `regime_bias_i = 0.0004 if regime contains "Super Cycle", 0.0001 if regime contains "Turnaround", else 0.0`
   - `day1_slippage_bps = mean(vol_constraint_i) * 50`
   - `active_days_progress_to_threshold = active_days_observed / 150`
3. Engine path:
   - `core.engine.run_simulation` remains the source of truth for `gross_ret`, `net_ret`, `turnover`, and `cost`
   - `equity_t = cumprod(1 + net_ret_t)`
4. Bounded output surface:
   - `data/processed/phase50_shadow_ship/paper_curve_day1.csv`
   - `data/processed/phase50_shadow_ship/paper_curve_positions_day1.csv`
   - `data/processed/phase50_shadow_ship/telemetry_day1.json`
   - `data/processed/phase50_shadow_ship/gate_recommendation.json`
   - compatibility mirrors:
     - `data/shadow_evidence/paper_curve_day1.csv`
     - `data/shadow_evidence/telemetry_day1.json`
     - `data/processed/phase50_gate/gate_recommendation.json`
   - `data/telemetry/phase50_paper_curve_events.jsonl`
   - canonical Phase 50 runtime reads stay on `data/processed/phase50_shadow_ship/`; compatibility mirrors exist only to satisfy CEO memo / handoff path contracts
5. Governance rule:
   - workers may not unilaterally open new phases; each phase opening requires explicit CEO sign-off in `docs/decision log.md`

## Phase 50 Final Gate Aggregation Notes

1. Final gate package artifacts:
   - full curve snapshot: `data/processed/phase50_shadow_ship/phase50_curve_full_20260410.csv`
   - aggregated telemetry: `data/processed/phase50_shadow_ship/phase50_aggregated_telemetry_20260410.json`
   - event-log snapshot: `data/processed/phase50_shadow_ship/phase50_event_log_full_20260410.jsonl`
2. Final gate aggregation formulas used in the accelerated package:
   - `cumulative_equity_factor = equity_day30`
   - `cumulative_return_pct = cumulative_equity_factor - 1`
   - `average_turnover = mean(turnover_days1_30)`
   - `stability_score = 1 - min(std(net_ret_days1_30) / max(abs(mean(net_ret_days1_30)), 1e-12), 1.0)`
3. Runtime source of truth:
   - `scripts/run_phase50_paper_curve.py` remains the only generator for the day-indexed curve and telemetry
   - the accelerated final package reuses those day-indexed outputs; it does not introduce a new simulation model

## Sovereign Shipping State Notes (2026-04-10)

### 1) Selector and routing state formulas
- `production_default_selector = "sovereign"`
- `governed_intent_valid = selector == "sovereign" and intent_payload_complete and audit_fields_present`
- `live_route_allowed = governed_intent_valid and live_break_glass_enabled and risk_interceptor_pass`
- `route_mode = "live" if live_route_allowed else "paper_fallback"`

### 2) Governance state changes
- `docs/handover/sovereign_promotion_package_20260313.md` is now the canonical live artifact rather than a contingent draft.
- Live-routing surfaces are permitted only through the existing governed execution path (`main_bot_orchestrator.py` -> `execution/rebalancer.py` -> `execution/risk_interceptor.py` -> `execution/broker_api.py`).
- Paper fallback remains mandatory whenever any live gate fails.
- Comparator and telemetry lineage remain part of the live audit trail; production unlock does not erase baseline evidence requirements.

### 3) Phase 51 design-state change
- `docs/phase_brief/phase51-factor-algebra-design.md` is now an implementation-authorized design starting point.
- The design brief remains a design artifact, not a source-of-truth runtime spec for executed production behavior.

## Live-Market Validation Round Criteria Notes

### 1) Entry and path lock
- Governed live-routing path remains:
  - `main_bot_orchestrator.py` -> `execution/rebalancer.py` -> `execution/risk_interceptor.py` -> `execution/broker_api.py`
- Validation mode token:
  - `validation_mode = "micro_capital_pilot"`
- Shadow comparator requirement:
  - same-window, same-cost, same `engine.run_simulation` path vs latest governed C3 baseline

### 2) Explicit formulas
- `telemetry_completeness = complete_lineage_orders / total_submitted_orders`
- `cash_drift = abs(local_cash_eod - broker_cash_eod)`
- `position_drift = max_symbol(abs(local_qty_eod - broker_qty_eod))`
- `slippage_deterioration_bps = live_median_adverse_slippage_bps - 7.5`
- `holdings_overlap = |live_symbols ∩ shadow_symbols| / max(1, |shadow_symbols|)`
- `gross_exposure_delta = abs(live_gross_exposure - shadow_gross_exposure)`
- `turnover_delta_abs = abs(live_turnover - shadow_turnover)`
- `turnover_delta_rel = turnover_delta_abs / max(abs(shadow_turnover), 1e-12)`
- `validation_round_pass = all(CHK_LMV_01..CHK_LMV_11) and no_rollback_trigger`

### 3) Runtime code loci
- Intent and authoritative execution result handling:
  - `main_bot_orchestrator.py`
- Batch normalization, routing, and risk-block persistence:
  - `execution/rebalancer.py`
- Projection, VIX kill switch, sector/single-name/VAR checks:
  - `execution/risk_interceptor.py`
- Fill aggregation, slippage, latency, heartbeat, and durable telemetry sinks:
  - `execution/microstructure.py`

### 4) Truthfulness boundary
- The current raw runtime path emits order/fill telemetry and slippage only when `arrival_price` context exists.
- The current raw runtime path does **not** by itself emit:
  - end-of-day cash/position reconciliation summaries
  - live-vs-shadow holdings overlap
  - gross-exposure delta
  - turnover delta
  - same-window C3 delta summaries for a live round
- Those checks therefore require a dedicated validation summarizer/reconciliation layer before a micro-capital live-market validation round can be authorized.

### 5) Artifact contract
- Raw telemetry remains in:
  - `data/processed/execution_microstructure.parquet`
  - `data/processed/execution_microstructure_fills.parquet`
  - `data/processed/execution_microstructure.duckdb`
- Future round summaries should live under:
  - `data/processed/live_market_validation/<round_id>/`

## Phase 57 Corporate Actions Formula Notes

1. Bounded Corporate Actions event proxy:
   - `corp_action_yield_t = total_ret_t - ((raw_close_t / raw_close_{t-1}) - 1)`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`load_corporate_action_frame`)
2. Eligible denominator family:
   - `eligible_t = 1[(quality_pass_t = 1) and (adv_usd_t >= 5_000_000) and (0.005 <= corp_action_yield_t <= 0.25)]`
   - `adv_usd_t = mean(raw_close_t * volume_t over 20 trading days by permno)`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`load_corporate_action_frame`, `select_corporate_action_candidates`)
3. Confirmation family:
   - `value_rank_pct_t = rank_pct(capital_cycle_score_t by date, ascending)`
   - `confirmed_t = 1[value_rank_pct_t >= 0.60]`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`select_corporate_action_candidates`)
4. Portfolio construction:
   - `target_weight_{t,i} = 1 / N_t` for confirmed names on event day `t`
   - non-event dates are explicitly reindexed to `0` target weight across the full trading calendar
   - executed exposure remains next-day because `core.engine.run_simulation` applies `shift(1)`
   - source paths:
     - `scripts/phase57_corporate_actions_runner.py` (`build_corporate_action_target_weights`)
     - `core/engine.py` (`run_simulation`)
5. Same-window / same-cost comparator discipline:
   - bounded Phase 57 packet window = `2015-01-01 -> 2022-12-31`
   - `cost_bps = 5.0`
   - locked comparator baseline = `data/processed/phase54_core_sleeve_summary.json` with `baseline_config_id = C3_LEAKY_INTEGRATOR_V1`
   - delta metrics:
     - `sharpe_delta = sharpe_phase57 - sharpe_c3`
     - `cagr_delta = cagr_phase57 - cagr_c3`
     - `turnover_ratio_phase57_vs_c3 = turnover_annual_phase57 / turnover_annual_c3`
     - `max_dd_delta = max_dd_phase57 - max_dd_c3`
     - `ulcer_delta = ulcer_phase57 - ulcer_c3`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`load_baseline_summary`, `build_delta_frame`)
6. Phase 57 closeout governance predicate:
   - `phase57_promotion_ready = 1[(same_window_same_cost_same_engine = 1) and (sharpe_delta >= 0) and (cagr_delta >= 0)]`
   - `phase57_closeout_no_promotion = 1[phase57_promotion_ready = 0]`
   - source paths:
     - `docs/decision log.md` (`D-321`, `D-322`)
     - `docs/phase_brief/phase57-brief.md`

## Phase 58 Governance Layer Formula Notes

1. Comparable event-family scope:
   - `event_family = {phase56_event_pead, phase57_event_corporate_actions}`
   - `allocator_reference = phase55 summary only` with `reference_only = true`
   - source path:
     - `scripts/phase58_governance_runner.py`
2. Same-window / same-cost / same-engine packet discipline:
   - `window = 2015-01-01 -> 2022-12-31`
   - `cost_bps = 5.0`
   - `same_window_same_cost_same_engine = 1[(all included event sleeves share the window, cost, and core.engine.run_simulation path)]`
   - source path:
     - `scripts/phase58_governance_runner.py`
3. Family trial-pool normalization:
   - `event_return_matrix_t = outer_join(net_ret_phase56_t, net_ret_phase57_t).fillna(0)`
   - `N_eff = effective_number_of_trials(event_return_matrix)`
   - `sr_estimates = {safe_sharpe(sleeve_i)}`
   - `dsr_i = deflated_sharpe_ratio(returns_i, sr_estimates, N_eff)`
   - `family_spa_p, family_wrc_p = spa_wrc_pvalues(event_return_matrix)`
   - source paths:
     - `scripts/phase58_governance_runner.py`
     - `utils/statistics.py`
     - `utils/spa.py`
4. Comparator deltas vs the locked C3 baseline:
   - `sharpe_delta_i = sharpe_i - sharpe_c3`
   - `cagr_delta_i = cagr_i - cagr_c3`
   - `turnover_ratio_i = turnover_annual_i / turnover_annual_c3`
   - `max_dd_delta_i = max_dd_i - max_dd_c3`
   - `ulcer_delta_i = ulcer_i - ulcer_c3`
   - source path:
     - `scripts/phase58_governance_runner.py` (`build_delta_row`)
5. Explicit bounded-packet non-applicability:
   - `pbo_applicable_event_family = 0`
   - reason: `single-packet event sleeves do not expose a CSCV search lattice in this bounded packet`
   - source path:
     - `scripts/phase58_governance_runner.py`
6. Review / hold predicate:
   - `phase58_review_hold = 1[(event_family_spa_p >= 0.05) or (event_family_wrc_p >= 0.05) or any(sharpe_delta_i < 0) or any(cagr_delta_i < 0)]`
   - source path:
     - `scripts/phase58_governance_runner.py` (`build_review_hold_reasons`)

## Phase 59 Shadow Portfolio Formula Notes

1. Phase 55-governed research-variant selector:
   - `selected_variant = argmax(selection_count, median_outer_test_sharpe, variant_id_ascending)`
   - input surface: `data/processed/phase55_allocator_cpcv_evidence.json::fold_results`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`select_phase55_variant`)
2. Research-side Shadow NAV surface:
   - `research_shadow_ret_t = allocator_state(period_return_{selected_variant,t})`
   - `research_shadow_ret_t = 0` on business dates in `2015-01-01 -> 2022-12-31` where the selected variant has no observed row
   - `research_shadow_equity_t = cumprod(1 + research_shadow_ret_t)`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`_build_research_surface`)
3. Research-side comparator deltas vs locked C3 baseline:
   - `sharpe_delta = sharpe_shadow - sharpe_c3`
   - `cagr_delta = cagr_shadow - cagr_c3`
   - `max_dd_delta = max_dd_shadow - max_dd_c3`
   - `ulcer_delta = ulcer_shadow - ulcer_c3`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`_build_research_delta_row`)
4. Reference-only alert contract:
   - `holdings_overlap = |shadow_latest_tickers ∩ core_sample_selected_tickers| / max(1, |shadow_latest_tickers|)`
   - `gross_exposure_delta = abs(core_gross_exposure_latest - shadow_gross_exposure_latest)`
   - `turnover_delta_abs = abs(turnover_delta_vs_c3_phase50)`
   - `turnover_delta_rel = turnover_delta_abs / max(abs(shadow_average_turnover), 1e-12)`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`_build_shadow_reference_surface`)
5. Review / hold predicate:
   - `phase59_review_hold = 1[(research_sharpe_delta < 0) or (research_cagr_delta < 0) or (shadow_reference_alert_level != "GREEN")]`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`build_phase59_packet`)

## Phase 60 Validator + Governed Cube Formula Notes

1. Validator freshness reference:
   - `governed_price_surface = _price_source_config()`
   - if `mode = tri`, use `prices_tri.parquet` only
   - else use `prices.parquet` plus `yahoo_patch.parquet` when patch exists
   - freshness delta:
     - `freshness_delta_days = latest_governed_price_date - latest_feature_date`
     - positive = lag
     - zero = current
     - negative = features extend beyond governed price source and are acceptable for the current build mode
   - source path:
     - `scripts/validate_data_layer.py` (`_freshness_status_text`, `_validate_feature_store_layer`)
2. Bounded governed sleeve surfaces:
   - `phase56_event_pead_weight_{i,t}` reconstructed from locked Phase 56 PEAD selection/weight logic on `2015-01-01 -> 2022-12-31`
   - `phase57_event_corporate_actions_weight_{i,t}` reconstructed from locked Phase 57 Corporate Actions selection/weight logic on `2015-01-01 -> 2022-12-31`
   - source paths:
     - `scripts/phase56_pead_runner.py`
     - `scripts/phase57_corporate_actions_runner.py`
     - `scripts/phase60_governed_cube_runner.py`
3. Governed cube construction:
   - `book_weight_pre_allocator_{i,t} = phase56_event_pead_weight_{i,t} + phase57_event_corporate_actions_weight_{i,t}`
   - `allocator_overlay_weight_{i,t} = 0` while allocator carry-forward remains blocked
   - `book_weight_final_{i,t} = book_weight_pre_allocator_{i,t} + allocator_overlay_weight_{i,t}`
   - `gross_exposure_t = sum_i(abs(book_weight_final_{i,t}))`
   - `turnover_component_{i,t} = abs(book_weight_final_{i,t} - book_weight_final_{i,t-1})`
   - source path:
     - `scripts/phase60_governed_cube_runner.py` (`_build_cube_rows`)
4. Eligibility contract in the cube:
   - active row:
     - `eligibility_state = governed_active__allocator_blocked`
   - zero-weight exit row retained for turnover proof:
     - `eligibility_state = turnover_exit__allocator_blocked`
   - source path:
     - `scripts/phase60_governed_cube_runner.py`
5. D-340 preflight contract over the published cube:
   - `PF-01`: cube summary matches locked packet id, window, max_date, and `5.0` bps gate
   - `PF-02`: cube publishes non-empty holdings/exposure/turnover fields and excludes `phase50_shadow_ship`
   - `PF-03`: governed gate remains `5.0` bps with `10.0` bps reserved for sensitivity
   - `PF-04`: audit gate list and kill-switch list are frozen before execution
   - `PF-05`: output paths remain outside `research_data/`
   - `PF-06`: summary paths point to the exact published cube artifacts
   - source path:
     - `scripts/phase60_preflight_verify.py`
6. D-340 bounded audit contract:
   - audit window:
     - `2023-01-01 -> 2024-12-31`
   - `book_weights_{i,t} = phase56_event_pead_weight_{i,t} + phase57_event_corporate_actions_weight_{i,t}`
   - `allocator_overlay_weight_{i,t} = 0`
   - `GATE-01`: `spa_p < 0.05 and wrc_p < 0.05`
   - `GATE-02`: `sharpe_pead >= sharpe_c3 and cagr_pead >= cagr_c3`
   - `GATE-03`: `core_sleeve_block_enforced = True`
   - `GATE-04`: `allocator_block_enforced = 1[(allocator_gate_pass = 0) and (allocator_overlay_applied = 0)]`
   - `GATE-05`: unified cube overlap/exposure/turnover metrics are non-empty on the governed surface
   - `KS-03_same_period_c3_unavailable`:
     - triggers when the same-period C3 comparator cannot be produced under strict missing-return rules
   - source path:
     - `scripts/phase60_governed_audit_runner.py`
7. D-341 blocked-audit review contract:
   - review inputs are locked to exactly four immutable SSOT artifacts:
     - `docs/context/e2e_evidence/phase60_d340_preflight_20260319_summary.json`
     - `data/processed/phase60_governed_audit_summary.json`
     - `data/processed/phase60_governed_audit_evidence.csv`
     - `data/processed/phase60_governed_audit_delta.csv`
   - `review_status = blocked_confirmed`
   - `disposition = evidence_only_hold`
   - `missing_executed_exposure_return_cells = 274`
   - `comparator_available = False`
   - reviewed delta lanes:
     - `5bps_gate`
     - `10bps_sensitivity`
   - authorization flags must all remain false:
     - `promotion_authorized`
     - `remediation_authorized`
     - `widening_authorized`
     - `allocator_carry_forward_authorized`
     - `core_sleeve_inclusion_authorized`
     - `research_data_mutation_authorized`
     - `kernel_mutation_authorized`
   - source path:
     - `scripts/phase60_d341_blocked_audit_review.py`
8. D-343 documentation hygiene contract:
   - active brief must not present resolved validator failures as current blockers after `D-339`
   - bridge `Evidence Used` must point to the current execution-era handover, not the historical kickoff memo, once Phase 60 is in execution-era hold state
   - source of truth paths:
     - `docs/phase_brief/phase60-brief.md`
     - `docs/context/bridge_contract_current.md`
9. D-344 hold-formalization contract:
   - active brief status must be `BLOCKED_EVIDENCE_ONLY_HOLD`
   - `D-341` remains the current authoritative evidence-only hold packet
   - no new remediation, widening, promotion, allocator carry-forward, core inclusion, or kernel mutation authority may appear in the D-344 packet
   - source of truth paths:
     - `docs/phase_brief/phase60-brief.md`
     - `docs/decision log.md`
     - `docs/context/bridge_contract_current.md`
10. D-345 formal closeout contract:
   - active brief status must be `CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD`
   - the exact blocked root cause must remain:
     - `KS-03_same_period_c3_unavailable`
     - `274` missing executed-exposure return cells
   - no remediation, widening, promotion, allocator carry-forward, core inclusion, kernel mutation, or Phase 61+ authority may appear in the D-345 packet
   - source of truth paths:
     - `docs/phase_brief/phase60-brief.md`
     - `docs/decision log.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/handover/phase60_execution_handover_20260318.md`

## Phase 64 Provenance + Validation Formula Notes

1. Source-quality gate:
   - `source_quality in {"canonical", "operational", "non_canonical", "rejected"}`
   - promotion-intent validation requires:
     - `source_quality = "canonical"`
   - source path:
     - `data/provenance.py` (`require_source_quality`, `assert_can_promote`, `assert_can_validate_artifact`)
2. Data readiness predicate:
   - `ready_for_paper_alerts = 1[blockers == []]`
   - blocker examples:
     - missing required artifact group;
     - empty artifact;
     - null `(date, permno)` keys;
     - duplicate `(date, permno)` keys;
     - price/return null ratio over threshold on `prices_tri`.
   - source path:
     - `scripts/audit_data_readiness.py` (`run_audit`)
3. Return summary formulas:
   - `equity_t = prod_{i<=t}(1 + net_ret_i)`
   - `cumulative_return = equity_T - 1`
   - `drawdown_t = equity_t / max_{i<=t}(equity_i) - 1`
   - `max_drawdown = min_t(drawdown_t)`
   - `sharpe_annualized = mean(net_ret) / stdev(net_ret) * sqrt(252)`
   - source path:
     - `validation/metrics.py` (`summarize_returns`)
4. OOS validation:
   - default split:
     - `train = first 70% of ordered returns`
     - `test = final 30% of ordered returns`
   - pass predicate:
     - `mean(test_net_ret) > 0`
   - source path:
     - `validation/oos.py` (`run_oos_test`)
5. Walk-forward validation:
   - default windows:
     - `train_size = 60`
     - `test_size = 20`
     - `step_size = 20`
   - pass predicate:
     - `positive_test_windows >= max(1, floor(window_count / 2))`
   - source path:
     - `validation/walk_forward.py` (`run_walk_forward`)
6. Regime validation:
   - if no regime column exists:
     - `regime_t = high_vol if rolling_std_20(net_ret)_t > median(rolling_std_20(net_ret)) else low_vol`
   - pass predicate:
     - each reported regime has enough observations and `worst_mean_daily_return > -0.01`
   - source path:
     - `validation/regime_tests.py` (`run_regime_tests`)
7. Permutation validation:
   - sign-flip null:
     - `null_mean_j = mean(net_ret_i * random_choice([-1, 1]))`
   - `permutation_p = (count(null_mean_j >= observed_mean) + 1) / (n_permutations + 1)`
   - pass predicate:
     - `observed_mean > 0 and permutation_p <= 0.10`
   - source path:
     - `validation/permutation.py` (`run_permutation_test`)
8. Bootstrap validation:
   - sample returns with replacement `n_bootstrap` times;
   - compute percentile confidence interval for mean daily return;
   - pass predicate:
     - `mean_ci_low > 0`
   - source path:
     - `validation/bootstrap.py` (`run_bootstrap_ci`)

## Phase 64.1 Dependency Hygiene Notes

1. Alpaca SDK boundary:
   - no formula changes in R64.1;
   - main dependency set uses `alpaca-py==0.43.4`;
   - legacy `alpaca-trade-api` is excluded from `requirements.txt`, `requirements.lock`, and `pyproject.toml`;
   - source paths:
     - `execution/broker_api.py`
     - `requirements.txt`
     - `requirements.lock`
     - `pyproject.toml`
     - `tests/test_dependency_hygiene.py`

## Phase 65 Candidate Registry Notes

1. Candidate intent predicate:
   - `candidate_valid = 1` iff all required intent fields are present before results:
     - `candidate_id`
     - `family_id`
     - `hypothesis`
     - `universe`
     - `features`
     - `parameters_searched`
     - `trial_count`
     - `train_window`
     - `test_window`
     - `cost_model`
     - `data_snapshot`
     - `manifest_uri`
     - `source_quality`
     - `created_at`
     - `created_by`
     - `code_ref`
     - `status`
   - source path:
     - `v2_discovery/schemas.py` (`CandidateSpec`)
2. Event hash formula:
   - `event_hash_i = SHA256(canonical_json(event_i without event_hash))`
   - `previous_event_hash_1 = "GENESIS"`
   - `hash_chain_valid = 1` iff `previous_event_hash_i == event_hash_{i-1}` for all `i > 1` and every stored `event_hash_i` recomputes exactly.
   - source path:
     - `v2_discovery/schemas.py` (`compute_event_hash`)
     - `v2_discovery/registry.py` (`verify_hash_chain`)
3. Snapshot projection:
   - `candidate_snapshot = replay(candidate_events_jsonl)`
   - event log is source of truth; snapshot is disposable projection.
   - source path:
     - `v2_discovery/registry.py` (`rebuild_snapshot`, `write_snapshot`)
4. Phase F status machine:
   - allowed:
     - `generated -> incubating`
     - `incubating -> rejected`
     - `generated -> rejected`
     - `generated -> retired`
     - `generated -> quarantined`
   - forbidden:
     - `incubating -> promoted`
     - `any -> alerted`
     - `any -> executed`
   - source path:
     - `v2_discovery/schemas.py` (`ALLOWED_STATUS_TRANSITIONS`, `FORBIDDEN_PHASE_F_STATUSES`)
5. Promotion readiness:
   - `promotion_ready = false` for every Phase F snapshot.
   - if `source_quality != "canonical"`, then `promotion_block_reason = "non_canonical_source_quality"`.
   - source path:
     - `v2_discovery/schemas.py` (`CandidateSnapshot`)

## Phase G0 V2 Proxy Boundary Notes

1. Proxy truth boundary:
   - `proxy_truth_official = false` for every V2 proxy result.
   - `promotion_ready = false` for every V2 proxy run/result.
   - `canonical_engine_required = true` for every V2 proxy run/result.
   - source path:
     - `v2_discovery/fast_sim/schemas.py` (`ProxyRunSpec`, `ProxyRunResult`)
2. Canonical engine rule:
   - `promotion_packet_draft_valid = 1` only if:
     - `source_quality = "canonical"`
     - `canonical_engine_name = "core.engine.run_simulation"`
     - `canonical_result_ref != ""`
     - `promotion_ready = false`
     - `canonical_engine_required = true`
   - source path:
     - `v2_discovery/fast_sim/schemas.py` (`PromotionPacketDraft`)
3. Proxy boundary predicate:
   - `proxy_boundary_valid = 1` iff:
     - candidate exists in `CandidateRegistry.rebuild_snapshot()`;
     - `registry_event_id` exists and points to `candidate_id`;
     - `manifest_uri` exists;
     - candidate, proxy, and manifest `source_quality` values match;
     - `registry_note_event_id` exists, points to the same `candidate_id`, has `event_type = "candidate.note_added"`, and references the `proxy_run_id` plus `boundary_verdict`;
     - proxy result verdict matches boundary policy.
   - source path:
     - `v2_discovery/fast_sim/boundary.py` (`V2ProxyBoundary`)
4. No-op proxy rule:
   - no alpha, Sharpe, return curve, ranking, search, alert, or broker behavior is computed.
   - no-op proxy run may append a registry note only.
   - `registry_note_event_valid = 1` iff the note event resolves from the append-only event log and names the same proxy run and boundary verdict.
   - source path:
     - `v2_discovery/fast_sim/noop_proxy.py` (`NoopProxy`)

## Phase G1 Synthetic Fast-Proxy Mechanics Notes

1. Synthetic fixture gate:
   - `synthetic_fixture_valid = 1` iff:
     - manifest path is under `data/fixtures/v2_proxy/`;
     - manifest `provider = "synthetic_fixture"`;
     - manifest `provider_feed = "prebaked_target_weights"`;
     - manifest `license_scope = "synthetic_fixture_only"`;
     - manifest `source_quality in {"non_canonical", "rejected"}`;
     - component hashes for prices and target weights match `compute_sha256(file)`;
     - target weights have strict columns `date,symbol,target_weight`.
   - source path:
     - `v2_discovery/fast_sim/fixtures.py` (`load_synthetic_proxy_fixture`)
2. Transaction-cost formula:
   - `cost_rate = total_cost_bps / 10000`
   - `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`
   - source path:
     - `v2_discovery/fast_sim/cost_model.py` (`FastProxyCostModel`)
3. Synthetic ledger formulas:
   - `current_value_{t,s} = quantity_{t-1,s} * price_{t,s}`
   - `equity_before_cost_t = cash_{t-1} + sum_s(current_value_{t,s})`
   - `current_weight_{t,s} = current_value_{t,s} / equity_before_cost_t`
   - `turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))`
   - `equity_after_cost_t = equity_before_cost_t - transaction_cost_t`
   - `target_value_{t,s} = target_weight_{t,s} * equity_after_cost_t`
   - `quantity_{t,s} = target_value_{t,s} / price_{t,s}`
   - `cash_t = equity_after_cost_t - sum_s(target_value_{t,s})`
   - source path:
     - `v2_discovery/fast_sim/ledger.py` (`build_synthetic_ledger`)
4. Exposure formulas:
   - `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`
   - `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`
   - invariant:
     - `gross_exposure_t >= abs(net_exposure_t)`
   - source path:
     - `v2_discovery/fast_sim/ledger.py` (`build_synthetic_ledger`)
5. Proxy result quarantine:
   - `promotion_ready = false`
   - `canonical_engine_required = true`
   - `boundary_verdict = tier2_blocked` for the non-canonical synthetic fixture
   - source path:
     - `v2_discovery/fast_sim/simulator.py` (`SyntheticFastProxySimulator`)
6. Finite-value gate:
   - `finite_numeric_valid = 1` iff every checked numeric value satisfies `np.isfinite(value)`.
   - rejected classes:
     - `nan`
     - `+inf`
     - `-inf`
   - checked boundaries:
     - fixture load: prices, weights, cost-model inputs;
     - pre-ledger: prices, target weights, cost assumptions;
     - post-ledger: positions, cash, turnover, transaction cost, gross exposure, net exposure;
     - result summary and proxy metadata: strict JSON finite values only.
   - source paths:
     - `v2_discovery/fast_sim/validation.py` (`validate_finite_numeric`, `validate_positive_numeric`)
     - `v2_discovery/fast_sim/cost_model.py` (`FastProxyCostModel`)
     - `v2_discovery/fast_sim/ledger.py` (`_validate_pre_ledger_inputs`, `validate_synthetic_ledger_output`)
     - `v2_discovery/fast_sim/simulator.py` (`_validate_result_summary`)
     - `v2_discovery/fast_sim/schemas.py` (`_require_json_finite`)
7. Manifest reconciliation gate:
   - `manifest_reconciles = 1` iff:
     - `manifest.row_count == len(df)`;
     - `manifest.date_range.start == min(df[date])`;
     - `manifest.date_range.end == max(df[date])`;
     - `manifest.sha256 == compute_sha256(file_path)`;
     - if schema columns are present, `manifest.schema.columns == list(df.columns)`.
   - source paths:
     - `v2_discovery/fast_sim/validation.py` (`validate_manifest_reconciles`)
     - `v2_discovery/fast_sim/fixtures.py` (`load_synthetic_proxy_fixture`)
     - `data/fixtures/v2_proxy/synthetic_manifest.json`
8. No-repair invariant:
   - `repair_used = 0` for invalid evidence.
   - missing symbols, sparse target weights, non-finite values, and manifest drift must raise `ProxyBoundaryError`.
   - forbidden repair patterns in G1 validation path:
     - `nan_to_num`
     - sparse-weight `fillna(0)`
     - forward/backward fill or interpolation.
   - source paths:
     - `v2_discovery/fast_sim/fixtures.py`
     - `v2_discovery/fast_sim/ledger.py`
     - `tests/test_v2_fast_proxy_synthetic.py`
     - `tests/test_v2_fast_proxy_invariants.py`

## Phase G3 Canonical Replay Fixture Notes

1. Canonical replay call gate:
   - `g3_v1_called = 1` iff the replay adapter calls `core.engine.run_simulation` with the fixture target-weight matrix, fixture return matrix, configured cost rate, and `strict_missing_returns = true`.
   - source path:
     - `v2_discovery/replay/canonical_replay.py` (`run_v1_canonical_replay`)
2. Allowed comparison field set:
   - `comparison_fields = {positions, cash, turnover, transaction_cost, gross_exposure, net_exposure, row_count, date_range, manifest_uri, source_quality, candidate_id}`.
   - `comparison_result = "match"` iff every allowed field matches under the G3 tolerance.
   - `mismatch_count = count(field where v1_field != v2_field)`.
   - source path:
     - `v2_discovery/replay/comparison.py` (`compare_allowed_mechanical_fields`)
3. G3 accounting formulas:
   - `returns_{t,s} = price_{t,s} / price_{t-1,s} - 1`, first row filled with `0.0` only for the V1 engine call surface.
   - `cost_rate = total_cost_bps / 10000`.
   - `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`.
   - `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`.
   - `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`.
   - source path:
     - `v2_discovery/replay/canonical_replay.py` (`_returns_matrix`, `_build_v1_accounting`)
4. Non-promotion invariant:
   - `g3_promotion_ready = false`.
   - `canonical_engine_required = true`.
   - `boundary_verdict = "v2_blocked_from_promotion"`.
   - A V1/V2 mechanical match does not create a promotion packet and does not grant trading permission.
   - source path:
     - `v2_discovery/replay/canonical_replay.py` (`build_g3_replay_report`)

## Phase G4 Real Canonical Dataset Readiness Notes

1. Canonical slice gate:
   - `g4_canonical_slice_valid = 1` iff:
     - `source_quality = "canonical"`;
     - manifest `extra.source_tier = "tier0"`;
     - provider/feed are not public-web, Tier 2, or operational-market-data sources;
     - artifact and manifest exist.
   - source path:
     - `v2_discovery/readiness/canonical_slice.py` (`load_g4_canonical_slice`)
2. Manifest reconciliation formula:
   - `manifest_reconciles = 1` iff:
     - `manifest.sha256 == compute_sha256(artifact)`;
     - `manifest.row_count == len(df)`;
     - `manifest.date_range.start == min(df.date)`;
     - `manifest.date_range.end == max(df.date)`;
     - `manifest.schema.columns == list(df.columns)`.
   - source path:
     - `v2_discovery/readiness/canonical_slice.py` (`_validate_manifest_contract`, `_validate_slice_data`)
3. Primary-key and monotonicity rules:
   - `duplicate_key_check = pass` iff `count_duplicates(df[date, permno]) = 0`.
   - `date_monotonicity_check = pass` iff dates are monotonic increasing within each `permno`.
   - source path:
     - `v2_discovery/readiness/canonical_slice.py` (`_validate_duplicate_primary_keys`, `_validate_date_monotonicity`)
4. Price and return domain rules:
   - `price_domain_check = pass` iff `tri > 0`, `legacy_adj_close > 0`, `raw_close > 0`, and `volume >= 0`.
   - `return_domain_check = pass` iff `-1.0 < total_ret <= 10.0`.
   - source path:
     - `v2_discovery/readiness/canonical_slice.py` (`_validate_price_domain`, `_validate_return_domain`)
5. G4 report invariant:
   - `ready_for_g5 = true` means dataset readiness only.
   - `sidecar_required = false` for the passing price slice.
   - report contains no alpha, performance, ranking, alert, broker, or promotion fields.
  - source path:
     - `v2_discovery/readiness/canonical_readiness.py` (`build_g4_readiness_report`)

## Phase G5 Single Canonical Replay Notes

1. Canonical replay call gate:
   - `g5_v1_called = 1` iff `run_g5_single_canonical_replay` calls `core.engine.run_simulation` with the G4 canonical returns matrix, predeclared neutral target weights, configured cost rate, and `strict_missing_returns = true`.
   - source path:
     - `v2_discovery/replay/canonical_real_replay.py` (`run_g5_single_canonical_replay`)
2. Neutral fixture weights:
   - `target_weight_{t,s} = 1 / count_symbols_t` for each `permno` on date `t`.
   - only `weight_mode = "equal_weight"` is accepted.
   - signal functions, rankers, selectors, and dynamic callbacks are rejected.
   - source path:
     - `v2_discovery/replay/canonical_real_replay.py` (`build_predeclared_neutral_weights`)
3. G5 accounting formulas:
   - `engine_returns_{t,s} = total_ret_{t,s}`.
   - `cost_rate = total_cost_bps / 10000`.
   - `turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))`.
   - `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`.
   - `target_value_{t,s} = target_weight_{t,s} * equity_after_cost_t`.
   - `cash_t = equity_after_cost_t - sum_s(target_value_{t,s})`.
   - `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`.
   - `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`.
   - source path:
     - `v2_discovery/replay/canonical_real_replay.py` (`build_g5_mechanical_replay`)
4. Non-promotion invariant:
   - `g5_promotion_ready = false`.
   - `alerts_emitted = false`.
   - `broker_calls = false`.
   - `mechanical_replay_result = "completed"` means official-path replay plumbing only, not alpha evidence.
   - source path:
     - `v2_discovery/replay/canonical_replay_report.py` (`build_g5_replay_report`)

## Phase G6 V1/V2 Real-Slice Mechanical Comparison Notes

1. Real-slice comparison gate:
   - `g6_v1_v2_comparison_valid = 1` iff the G4 canonical slice passes manifest/source gates, G5 V1 replay runs through `core.engine.run_simulation`, V2 proxy ledger mechanics run on the same predeclared weights, and all approved equality fields match.
   - source path:
     - `v2_discovery/replay/real_slice_v1_v2_comparison.py` (`run_g6_v1_v2_real_slice_mechanical_comparison`)
2. Approved comparison field set:
   - `comparison_fields = {positions, cash, turnover, transaction_cost, gross_exposure, net_exposure, row_count, date_range, source_quality, manifest_uri, engine_name, engine_version}`.
   - Equality is required for positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, source quality, and manifest URI.
   - Engine name and engine version are recorded as identity metadata because V1 and V2 are intentionally distinct engines.
   - source path:
     - `v2_discovery/replay/real_slice_v1_v2_comparison.py` (`compare_g6_mechanical_fields`)
3. G6 accounting formulas:
   - `target_weight_{t,s} = 1 / count_symbols_t`.
   - `cost_rate = total_cost_bps / 10000`.
   - `turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))`.
   - `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`.
   - `cash_t = equity_after_cost_t - sum_s(target_value_{t,s})`.
   - `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`.
   - `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`.
   - `mismatch_count = count(field where V1_field != V2_field)`.
   - source path:
     - `v2_discovery/replay/real_slice_v1_v2_comparison.py`
4. Non-promotion invariant:
   - `g6_promotion_ready = false`.
   - `v2_promotion_ready = false`.
   - `canonical_engine_required = true`.
   - `alerts_emitted = false`.
   - `broker_calls = false`.
   - A V1/V2 mechanical match does not create a promotion packet and does not grant trading permission.
   - source path:
     - `v2_discovery/replay/mechanical_comparison_report.py` (`build_g6_mechanical_comparison_report`)

## Phase G7 Candidate Family Definition Notes

1. Family manifest gate:
   - `family_manifest_valid = 1` iff:
     - family definition JSON exists;
     - manifest JSON exists;
     - `manifest.sha256 == compute_sha256(family_json)`;
     - `manifest.row_count == 1`;
     - `manifest.extra.family_id == family.family_id`;
     - `manifest.extra.version == family.version`;
     - `manifest.extra.trial_budget_max == family.trial_budget_max`.
   - source path:
     - `v2_discovery/families/validation.py` (`validate_manifest_backing`)
2. Trial-budget formula:
   - `finite_trial_count = product(count(options_p) for p in parameter_space)`.
   - For `PEAD_DAILY_V0`:
     - `holding_days = {1, 3, 5, 10}` -> 4 options;
     - `liquidity_floor = {adv_usd_5m, adv_usd_20m, adv_usd_50m}` -> 3 options;
     - `event_window_lag = {1, 2}` -> 2 options;
     - `finite_trial_count = 4 * 3 * 2 = 24`.
   - `trial_budget_valid = finite_trial_count <= trial_budget_max`.
   - source paths:
     - `v2_discovery/families/schemas.py` (`CandidateFamilyDefinition.finite_trial_count`)
     - `v2_discovery/families/trial_budget.py` (`calculate_trial_budget`, `validate_trial_budget`)
3. Definition-only report invariant:
   - `g7_definition_only = true` iff:
     - `defined_only = true`;
     - `candidate_generation_enabled = false`;
     - `result_generation_enabled = false`;
     - `promotion_ready = false`;
     - `alerts_emitted = false`;
     - `broker_calls = false`;
     - no outcome/performance/ranking field is present.
   - source path:
     - `v2_discovery/families/validation.py` (`validate_registry_report`)

## Phase G7.1 Roadmap Realignment / Product Charter Notes

1. Product focus planning model:
   - `product_focus = 0.90 * supercycle_gem_discovery + 0.10 * buying_range_hold_discipline_prompting`.
   - This is a planning allocation model only; it is not a portfolio allocation, ranking score, signal weight, or execution rule.
   - source paths:
     - `docs/architecture/product_roadmap_discretionary_augmentation.md`
     - `docs/handover/phase65_g71_handover.md`
2. Family classification:
   - `SUPERCYCLE_GEM_DAILY_V0 = primary_product_family_target`.
   - `PEAD_DAILY_V0 = tactical_signal_family`.
   - G7 `PEAD_DAILY_V0` artifacts remain valid and are not modified by G7.1.
   - source path:
     - `docs/architecture/supercycle_gem_family_policy.md`
3. Dashboard taxonomy:
   - `dashboard_panels = {thesis_health, entry_discipline, hold_discipline, flow_positioning, regime}`.
   - future short-squeeze and CTA-type inputs are dashboard context, not automatic triggers.
   - source path:
     - `docs/architecture/dashboard_signal_taxonomy.md`
4. G7.1 non-execution invariant:
   - `g7_1_valid = 1` iff docs/context are updated, `PEAD_DAILY_V0` remains tactical, `SUPERCYCLE_GEM_DAILY_V0` is primary target, G8 PEAD generation is held, and no candidate generation/backtest/replay/proxy/search/ranking/alert/broker/promotion code or artifact is added.
   - source paths:
     - `docs/architecture/product_roadmap_discretionary_augmentation.md`
     - `docs/phase_brief/phase65-brief.md`

## Phase G7.1A Starter Docs / Product Spec Rewrite Notes

1. Unified Opportunity Engine product formula:
   - `Unified Opportunity Engine = Supercycle Gem Discovery + GodView Market Behavior Intelligence + Decision Augmentation`.
   - This is a product architecture formula only; it is not a score, trading rule, allocation rule, or implemented state machine.
   - source paths:
     - `README.md`
     - `PRD.md`
     - `PRODUCT_SPEC.md`
     - `docs/architecture/unified_opportunity_engine.md`
2. Future state-engine concept:
   - `dashboard_state = f(thesis_state, market_behavior_state, entry_discipline_state, hold_discipline_state, source_quality_state)`.
   - This is future G7.2 design vocabulary only; G7.1A does not implement state-machine code.
   - source paths:
     - `PRODUCT_SPEC.md`
     - `docs/architecture/unified_opportunity_engine.md`
     - `docs/architecture/dashboard_product_spec.md`
3. GodView signal metadata contract:
   - every future signal must carry `source_quality`, `provider`, `provider_feed`, `freshness`, `latency`, `confidence`, `observed_vs_estimated`, `allowed_use`, `forbidden_use`, and `manifest_uri`.
   - source paths:
     - `PRD.md`
     - `PRODUCT_SPEC.md`
     - `docs/architecture/godview_signal_taxonomy.md`
     - `docs/architecture/data_infra_gap_assessment.md`
4. G7.1A non-execution invariant:
   - `g7_1a_valid = 1` iff root product canon exists, current truth surfaces point to `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`, G7.2/G7.4/G7.5/G8 remain held, and no candidate generation/search/backtest/replay/proxy/provider/ranking/alert/broker/dashboard-runtime implementation is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`

## Phase G7.1B Data + Infra Gap Assessment Notes

1. GodView infrastructure fit formula:
   - `godview_current_infra = governance_ready + price_volume_ready + provider_port_pattern_ready`.
   - `godview_current_infra != full_market_behavior_ready`.
   - This is an architecture assessment formula only; it is not an implemented capability check or signal score.
   - source paths:
     - `docs/architecture/godview_data_infra_gap_assessment.md`
     - `docs/architecture/godview_provider_roadmap.md`
2. GodView source label formula:
   - `godview_signal_label = observed | estimated | inferred`.
   - Observed examples: price, volume, official filings, official short interest, official COT, licensed options prints.
   - Estimated examples: CTA buying, gamma exposure, dealer positioning, whale intent, dark-pool accumulation, squeeze pressure.
   - Inferred examples: narrative velocity, thesis health, rotation state, entry discipline, hold discipline.
   - source path:
     - `docs/architecture/godview_observed_vs_estimated_policy.md`
3. GodView freshness formula:
   - `freshness_state = fresh | delayed | stale | unknown`.
   - Required time fields are `asof_ts`, `captured_at_utc`, `freshness`, `latency`, `provider`, `provider_feed`, and `manifest_uri`.
   - source path:
     - `docs/architecture/godview_signal_freshness_policy.md`
4. GodView future signal metadata contract:
   - every future signal must carry `signal_id`, `signal_family`, `ticker_or_theme`, `source_quality`, `provider`, `provider_feed`, `observed_vs_estimated`, `freshness`, `latency`, `asof_ts`, `confidence`, `allowed_use`, `forbidden_use`, and `manifest_uri`.
   - source path:
     - `docs/architecture/godview_signal_source_matrix.md`
5. G7.1B non-execution invariant:
   - `g7_1b_valid = 1` iff GodView source matrix/provider roadmap/freshness policy/observed-vs-estimated policy/Codex-Chrome SOP are documented, current infra is classified as governance-ready but not full-GodView-ready, G7.2/G7.4/G7.5/G8 remain held, and no provider code/ingestion/search/candidate/backtest/replay/proxy/ranking/alert/broker/dashboard-runtime behavior is added.
  - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`

## Phase G7.1C Open-Source Repo + API Availability Survey Notes

1. No-cost public-source planning formula:
   - `godview_no_cost_path_after_audit = existing_tier0_price_volume + SEC + FINRA + CFTC + public_macro`.
   - This is a planning formula only; it is not provider approval, ingestion, signal scoring, ranking, alerting, or trading authority.
   - source paths:
     - `docs/research/g7_1c_open_source_repo_data_api_availability_survey_20260509.md`
     - `docs/architecture/godview_api_availability_matrix.md`
     - `docs/architecture/godview_build_vs_borrow_decision.md`
2. Advanced-flow gap formula:
   - `godview_advanced_flow_gap = options_iv_whales_gamma + dark_pool_block + microstructure`.
   - These remain paid/licensed or provider-decision gaps; they are not no-cost implementation candidates in G7.1C.
   - source paths:
     - `docs/architecture/godview_api_availability_matrix.md`
     - `docs/architecture/godview_provider_selection_policy.md`
3. Provider audit gate:
   - `provider_candidate_eligible = true` iff rights/terms, cost, authentication, as-of semantics, capture time, freshness, raw locator, manifest fit, source label, allowed use, forbidden use, and rollback path are documented.
   - G7.1C documents the gate but does not execute the audit.
   - source path:
     - `docs/architecture/godview_provider_selection_policy.md`
4. G7.1C non-execution invariant:
   - `g7_1c_valid = 1` iff research/architecture docs are updated, source claims are marked audit-pending, G7.2/G7.3/G7.4/G7.5/G8 remain held, and no provider code/ingestion/search/candidate/backtest/replay/proxy/ranking/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`

## Phase G7.1C Official Public Source Audit Notes

1. Public source eligibility formula:
   - `public_source_candidate_eligible = official_source + terms_reviewed + cost_auth_key_known + freshness_known + raw_locator_known + asof_semantics_known + allowed_forbidden_use_known`.
   - This is an audit/planning formula only; it is not provider code, signal scoring, ranking, alerting, or trading authority.
   - source paths:
     - `docs/architecture/godview_public_source_audit.md`
     - `docs/architecture/godview_source_terms_matrix.md`
2. Tiny fixture gate formula:
   - `tiny_fixture_allowed = explicit_future_approval and source_policy_published and manifest_contract_defined`.
   - In G7.1C source audit, `tiny_fixture_allowed = false`; schemas are plans only and no data is downloaded.
   - source path:
     - `docs/architecture/godview_tiny_fixture_schema_plan.md`
3. Observed / estimated / inferred classification:
   - Observed: official filings, official short interest, Reg SHO volume, CFTC reported positioning, FRED macro series, Ken French factor returns.
   - Estimated: CTA pressure, squeeze pressure, whale intent, dark-pool accumulation, dealer/gamma pressure.
   - Inferred: thesis health, market regime state, entry discipline, hold discipline.
   - source path:
     - `docs/architecture/godview_public_source_audit.md`
4. CFTC source-use constraint:
   - `cftc_allowed_use = broad_regime_or_futures_positioning`.
   - `cftc_forbidden_use = direct_single_name_cta_buying_evidence`.
   - source path:
     - `docs/architecture/godview_public_source_audit.md`
5. G7.1C audit-only invariant:
   - `g7_1c_source_audit_valid = 1` iff official source audit/docs/context/handover/SAW are updated, the terms matrix and schema plan are published, G7.2/G7.3/G7.4/G7.5/G8 remain held, and no physical fixture/provider code/ingestion/search/candidate/backtest/replay/proxy/ranking/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_1c_public_source_audit_20260509.md`

## Phase G7.1D SEC Tiny Fixture Notes

1. SEC fixture validity formula:
   - `g7_1d_sec_fixture_valid = static_fixture and manifest_hash_matches and row_count_reconciles and cik_is_10_digit_string and date_fields_parse and duplicate_primary_keys == 0 and numeric_fact_values_are_finite and observed_estimated_or_inferred == observed and provider_code_added == false and ingestion_added == false`.
   - This is a fixture/provenance formula only; it is not a signal score, ranking rule, state-machine rule, or provider approval.
   - source paths:
     - `docs/architecture/sec_tiny_fixture_policy.md`
     - `tests/test_g7_1d_sec_tiny_fixture.py`
2. SEC manifest identity formula:
   - `sec_manifest_identity = source_name + source_quality + provider + provider_feed + api_endpoint + retrieved_at + asof_ts + CIK + form_types + row_count + date_range + sha256 + allowed_use + forbidden_use`.
   - source paths:
     - `data/fixtures/sec/sec_companyfacts_tiny.json.manifest.json`
     - `data/fixtures/sec/sec_submissions_tiny.json.manifest.json`
3. G7.1D non-provider invariant:
   - `g7_1d_provider_scope_valid = 1` iff SEC fixture docs/fixtures/tests/context/handover/SAW are updated, G7.2 remains held, and no live provider/broad downloader/ingestion/canonical lake write/signal score/candidate generation/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_1d_sec_tiny_fixture_20260509.md`

## Phase G7.1E FINRA Short Interest Tiny Fixture Notes

1. FINRA fixture validity formula:
   - `g7_1e_finra_fixture_valid = static_fixture and dataset_type == short_interest and manifest_hash_matches and row_count_reconciles and settlement_date_parses and ticker_present and short_interest_is_finite_non_negative and average_daily_volume_is_finite_non_negative and days_to_cover_is_finite_non_negative_when_present and duplicate_primary_keys == 0 and observed_estimated_or_inferred == observed and reg_sho_fields_present == false and provider_code_added == false`.
   - This is a fixture/provenance formula only; it is not a squeeze score, ranking rule, state-machine rule, alert rule, or provider approval.
   - source paths:
     - `docs/architecture/finra_short_interest_tiny_fixture_policy.md`
     - `tests/test_g7_1e_finra_short_interest_tiny_fixture.py`
2. FINRA short-interest interpretation formula:
   - `short_interest_context = delayed_short_crowding_evidence`.
   - `squeeze_signal_allowed = short_interest_context + additional_validated_evidence + explicit_future_scoring_approval`.
   - Therefore, `short_interest_context_only != real_time_squeeze_trigger`.
   - source path:
     - `docs/architecture/finra_short_interest_vs_short_volume_policy.md`
3. FINRA non-provider invariant:
   - `g7_1e_provider_scope_valid = 1` iff FINRA fixture docs/fixture/test/context/handover/SAW are updated, G7.2 remains held, and no FINRA provider/live API/bulk download/Reg SHO ingestion/OTC-ATS ingestion/squeeze score/candidate generation/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_1e_finra_tiny_fixture_20260509.md`

## Phase G7.1F CFTC TFF Tiny Fixture Notes

1. CFTC fixture validity formula:
   - `g7_1f_cftc_fixture_valid = static_fixture and dataset_type == futures_positioning and manifest_hash_matches and row_count_reconciles and report_date_parses and asof_position_date_parses and market_name_present and contract_market_code_present and trader_category_in_allowed_categories and long_positions_is_finite_non_negative and short_positions_is_finite_non_negative and spreading_positions_is_finite_non_negative_when_present and open_interest_is_finite_non_negative and duplicate_primary_keys == 0 and observed_estimated_or_inferred == observed and single_name_inference_forbidden == true and provider_code_added == false`.
   - This is a fixture/provenance formula only; it is not a CTA score, ranking rule, state-machine rule, alert rule, or provider approval.
   - source paths:
     - `docs/architecture/cftc_tff_tiny_fixture_policy.md`
     - `tests/test_g7_1f_cftc_tff_tiny_fixture.py`
2. CFTC COT/TFF interpretation formula:
   - `cftc_tff_allowed_context = observed_futures_positioning and broad_market_contract and weekly_delayed and source_quality == public_official_observed and single_name_inference == false`.
   - `cftc_tff_forbidden_signal = single_name_cta_claim or standalone_buy_sell_signal or ranking_factor or alert_emission or alpha_evidence_without_validation`.
   - Therefore, `cftc_tff_context_only != single_name_cta_buying_evidence`.
   - source path:
     - `docs/architecture/cftc_cot_tff_usage_policy.md`
3. CFTC non-provider invariant:
   - `g7_1f_provider_scope_valid = 1` iff CFTC fixture docs/fixture/test/context/handover/SAW are updated, G7.2 remains held, and no CFTC provider/live API/bulk download/CTA score/single-name inference/candidate generation/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_1f_cftc_tiny_fixture_20260509.md`

## Phase G7.1G FRED / Ken French Tiny Fixture Notes

1. FRED fixture validity formula:
   - `g7_1g_fred_fixture_valid = static_fixture and dataset_type == macro_series and manifest_hash_matches and row_count_reconciles and date_range_reconciles and date_fields_parse and series_id_present and value_is_finite and duplicate_primary_keys == 0 and observed_estimated_or_inferred == observed and api_key_required == true_for_live_api and provider_code_added == false`.
   - This is a fixture/provenance formula only; it is not a macro regime score, ranking rule, state-machine rule, alert rule, or provider approval.
   - source paths:
     - `docs/architecture/fred_ken_french_tiny_fixture_policy.md`
     - `tests/test_g7_1g_fred_ken_french_tiny_fixture.py`
2. Ken French fixture validity formula:
   - `g7_1g_ken_french_fixture_valid = static_fixture and dataset_type == factor_returns and manifest_hash_matches and row_count_reconciles and date_range_reconciles and date_fields_parse and dataset_id_present and factor_name_present and factor_return_is_finite and duplicate_primary_keys == 0 and observed_estimated_or_inferred == observed and provider_code_added == false`.
   - This is a fixture/provenance formula only; it is not factor alpha proof, a factor regime score, ranking rule, state-machine rule, alert rule, or provider approval.
   - source paths:
     - `docs/architecture/fred_ken_french_tiny_fixture_policy.md`
     - `tests/test_g7_1g_fred_ken_french_tiny_fixture.py`
3. Macro/factor interpretation formula:
   - `macro_factor_context_allowed = observed_macro_series_or_factor_returns and manifest_hash_matches and allowed_use_present and forbidden_use_present`.
   - `macro_factor_forbidden_signal = macro_regime_score or factor_regime_score or candidate_rank or alert_emission or broker_call or state_machine_input_without_future_approval`.
   - Therefore, `macro_factor_fixture_context_only != alpha_proof_or_ranking_signal`.
   - source path:
     - `docs/architecture/macro_factor_context_usage_policy.md`
4. FRED / Ken French non-provider invariant:
   - `g7_1g_provider_scope_valid = 1` iff FRED/Ken French fixture docs/fixtures/tests/context/handover/SAW are updated, G7.2 remains held, and no FRED provider/Ken French provider/live API/API key handling/bulk download/macro score/factor score/candidate generation/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_1g_fred_ken_french_tiny_fixture_20260509.md`

## Phase G7.2 Opportunity State Machine Notes

1. State validation formula:
   - `g7_2_transition_valid = state_enum_complete and reason_codes_present and source_classes_present and forbidden_jump_not_requested and thesis_broken_override_applied and estimated_only_buying_range == false and inferred_only_let_winner_run == false and score_rank_alert_broker_fields_absent`.
   - This is a definition/validator formula only; it is not a score, rank, alert, order, or provider rule.
   - source paths:
     - `docs/architecture/unified_opportunity_state_machine.md`
     - `docs/architecture/opportunity_state_transition_policy.md`
     - `docs/architecture/opportunity_state_forbidden_jumps.md`
     - `opportunity_engine/states.py`
     - `opportunity_engine/schemas.py`
     - `opportunity_engine/transitions.py`
     - `tests/test_g7_2_opportunity_state_machine.py`
2. State semantics formula:
   - `thesis_broken_override = thesis_broken ? THESIS_BROKEN : requested_state`.
   - `left_side_confirmation_gate = LEFT_SIDE_RISK -> ACCUMULATION_WATCH|CONFIRMATION_WATCH -> BUYING_RANGE`.
   - `estimated_only_action_state = false`.
   - `inferred_only_hold_state = false`.
   - source paths:
     - `docs/architecture/opportunity_state_forbidden_jumps.md`
     - `opportunity_engine/transitions.py`
3. G7.2 non-action invariant:
   - `g7_2_provider_scope_valid = 1` iff G7.2 docs/code/tests/context/handover/SAW are updated and no candidate generation/search/backtest/replay/proxy/ranking/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_2_state_machine_20260509.md`

## Phase G7.3 Signal-to-State Source Eligibility Notes

1. Source eligibility formula:
   - `state_eligible = source_class_allowed and freshness_known and forbidden_state_influence_excludes(target_state)`.
   - This is a source-policy formula only; it is not provider implementation or ranking authority.
   - source paths:
     - `docs/architecture/godview_signal_to_state_map.md`
     - `docs/architecture/godview_source_eligibility_policy.md`
     - `docs/architecture/godview_signal_confidence_policy.md`
     - `opportunity_engine/source_classes.py`
     - `opportunity_engine/signal_policy.py`
     - `tests/test_g7_3_signal_to_state_source_map.py`
2. Source labels formula:
   - `observed_official_context = SEC|FINRA|CFTC|FRED|KenFrench`.
   - `estimated_only_action_state = false`.
   - `tier2_yfinance_action_state = false`.
   - source paths:
     - `docs/architecture/godview_source_eligibility_policy.md`
     - `docs/architecture/godview_signal_confidence_policy.md`
3. G7.3 non-provider invariant:
   - `g7_3_provider_scope_valid = 1` iff G7.3 docs/code/tests/context/handover/SAW are updated and no provider/source-registry/live API/ranking/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_3_signal_to_state_map_20260509.md`

## Phase G7.4 Dashboard Wireframe / Product-State Spec Notes

1. Dashboard state spec formula:
   - `dashboard_card = state + prior_state + reason_codes + source_breakdown + blockers + monitoring_questions`.
   - `brief_state_only = state_changes + freshness_gaps + blockers + questions`.
   - This is a product-spec formula only; it is not runtime UI behavior.
   - source paths:
     - `docs/architecture/godview_dashboard_wireframe.md`
     - `docs/architecture/godview_watchlist_card_spec.md`
     - `docs/architecture/godview_daily_brief_spec.md`
     - `tests/test_g7_4_dashboard_state_spec.py`
2. Dashboard wording formula:
   - `state_label_only = true`.
   - `no_buy_sell_alert_score_rank = true`.
   - `no_runtime_streamlit = true`.
   - source paths:
     - `docs/architecture/godview_dashboard_wireframe.md`
     - `docs/architecture/godview_watchlist_card_spec.md`
     - `docs/architecture/godview_daily_brief_spec.md`
3. G7.4 non-runtime invariant:
   - `g7_4_provider_scope_valid = 1` iff G7.4 docs/tests/context/handover/SAW are updated and no dashboard runtime code, Streamlit edits, candidate card, alert, broker, or provider behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_4_dashboard_wireframe_20260509.md`

## Phase G8 Supercycle Candidate Card Notes

1. Candidate-card validation formula:
   - `g8_card_valid = required_fields_present and manifest_present and initial_state in {THESIS_CANDIDATE,EVIDENCE_BUILDING} and forbidden_action_states_absent and no_score_rank_signal_alert_broker and provider_gap_signals_explicit`.
   - This is a definition/evidence-card formula only; it is not alpha evidence, ranking, scoring, buy/sell logic, alerting, provider ingestion, replay, backtest, or broker behavior.
   - source paths:
     - `opportunity_engine/candidate_card_schema.py`
     - `opportunity_engine/candidate_card.py`
     - `tests/test_g8_supercycle_candidate_card.py`
2. Source-quality formula:
   - `source_quality_complete = observed + estimated + inferred + research_only + not_canonical + missing + stale + forbidden + canonical_sources`.
   - `yfinance_canonical_source = false`.
   - `estimated_signal_presented_as_observed = false`.
   - source paths:
     - `data/candidate_cards/MU_supercycle_candidate_card_v0.json`
     - `data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json`
     - `docs/architecture/supercycle_candidate_card_schema.md`
3. G8 non-action invariant:
   - `g8_scope_valid = 1` iff the MU card and docs/tests/context/handover/SAW are updated and no alpha search, candidate screening, ranking, scoring, backtest, replay, provider ingestion, dashboard runtime, buy/sell alert, or broker action is added.
   - source paths:
     - `docs/architecture/g8_supercycle_candidate_card_policy.md`
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/saw_reports/saw_phase65_g8_supercycle_candidate_card_20260510.md`

## Phase G8.1 Supercycle Discovery Intake Notes

1. Discovery-intake validity formula:
   - `g8_1_intake_valid = required_seed_tickers_exact and theme_candidates_present and evidence_needed_present and thesis_breakers_present and provider_gaps_present and no_score_fields and no_rank_fields and no_buy_sell_hold_calls and validated_status_absent and action_states_absent and yfinance_canonical_absent and manifest_hash_matches`.
   - This is an intake/planning formula only; it is not alpha evidence, ranking, scoring, thesis validation, buying-range logic, alerting, provider ingestion, replay, backtest, or broker behavior.
   - source paths:
     - `opportunity_engine/discovery_intake_schema.py`
     - `opportunity_engine/discovery_intake.py`
     - `tests/test_g8_1_supercycle_discovery_intake.py`
2. Seed queue formula:
   - `g8_1_seed_queue = [MU, DELL, INTC, AMD, LRCX, ALB]`.
   - `candidate_card_exists = {MU}`.
   - `intake_only = {DELL, INTC, AMD, LRCX, ALB}`.
   - source paths:
     - `data/discovery/supercycle_candidate_intake_queue_v0.json`
     - `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json`
3. Theme taxonomy formula:
   - `g8_1_theme_taxonomy = {AI_COMPUTE_INFRA, AI_SERVER_SUPPLY_CHAIN, MEMORY_STORAGE_SUPERCYCLE, SEMICAP_EQUIPMENT, POWER_COOLING_GRID, CRITICAL_MINERALS_LITHIUM, RESHORING_FOUNDRY, DEFENSE_INDUSTRIAL, BIOTECH_PLATFORM}`.
   - source path:
     - `data/discovery/supercycle_discovery_themes_v0.json`
4. G8.1 non-action invariant:
   - `g8_1_scope_valid = 1` iff the taxonomy, queue, manifest, docs, tests, context, handover, and SAW are updated and no alpha search, candidate ranking, candidate scoring, thesis validation, buying range, provider ingestion, dashboard runtime, alert, or broker behavior is added.
   - source paths:
     - `docs/architecture/g8_1_supercycle_discovery_intake_policy.md`
     - `docs/architecture/supercycle_candidate_intake_schema.md`
     - `docs/context/done_checklist_current.md`
     - `docs/saw_reports/saw_phase65_g8_1_supercycle_discovery_intake_20260510.md`

## Phase G8.1A Discovery Drift Correction Notes

1. Discovery-origin formula:
   - `g8_1a_origin_valid = origin_present and origin_evidence_present and scout_path_present and user_seeded_flag_matches_origin and system_scouted_flag_matches_origin and current_six_system_scouted == false and is_validated == false and is_actionable == false`.
   - This is provenance governance only; it is not alpha evidence, ranking, scoring, validation, actionability, or recommendation logic.
   - source paths:
     - `opportunity_engine/discovery_intake_schema.py`
     - `data/discovery/supercycle_candidate_intake_queue_v0.json`
     - `tests/test_g8_1a_discovery_drift_policy.py`
2. Current seed-origin map:
   - `MU = USER_SEEDED`.
   - `DELL = USER_SEEDED + THEME_ADJACENT`.
   - `INTC = USER_SEEDED + THEME_ADJACENT`.
   - `AMD = USER_SEEDED + THEME_ADJACENT`.
   - `LRCX = USER_SEEDED + SUPPLY_CHAIN_ADJACENT`.
   - `ALB = USER_SEEDED + THEME_ADJACENT`.
3. G8.1B guardrail:
   - `LOCAL_FACTOR_SCOUT` is defined in `opportunity_engine/discovery_intake_schema.py` but is rejected in G8.1A intake output.
   - `data/processed/phase34_factor_scores.parquet` remains held until a manifest-backed G8.1B scout contract is approved.

## Phase DASH-0 Dashboard IA Notes

1. Dashboard IA formula:
   - `dash_0_ia_valid = page_map_approved and legacy_movement_mapped and ops_relocation_defined and streamlit_registry_basis_documented and runtime_files_touched == false`.
   - This is a planning formula only; it is not a Streamlit runtime shell, dashboard implementation, alert path, provider path, broker path, score, or rank.
   - source paths:
     - `docs/architecture/dashboard_information_architecture.md`
     - `docs/architecture/dashboard_page_registry_plan.md`
     - `docs/architecture/dashboard_redesign_migration_plan.md`
     - `docs/architecture/dashboard_ops_relocation_policy.md`
2. Target page map:
   - `Command Center -> state distribution, freshness, risks, next monitoring focus`.
   - `Opportunities -> intake/candidate cards with origin/status labels`.
   - `Thesis Card -> MU/current candidate thesis, evidence, contradictions, blockers`.
   - `Market Behavior -> GodView signal families with observed/estimated/inferred labels`.
   - `Entry & Hold Discipline -> why not buy yet / why not sell yet`.
   - `Portfolio & Allocation -> risk limits, allocation, shadow portfolio`.
   - `Research Lab -> backtests, modular strategies, daily scan, experiments`.
   - `Settings & Ops -> data health, drift monitor, diagnostics, refresh`.
3. Runtime hold:
   - Future `Max weight` + `Max sector weight` alignment in `views/optimizer_view.py` is recorded as a future Risk limits UX task only.
   - No `dashboard.py`, `views/`, or `optimizer_view.py` edits are authorized by DASH-0.
## Phase G7.2 Opportunity State Machine Notes

1. State validation formula:
   - `g7_2_transition_valid = state_enum_complete and reason_codes_present and source_classes_present and forbidden_jump_not_requested and thesis_broken_override_applied and estimated_only_buying_range == false and inferred_only_let_winner_run == false and score_rank_alert_broker_fields_absent`.
   - This is a definition/validator formula only; it is not a score, rank, alert, order, or provider rule.
   - source paths:
     - `docs/architecture/unified_opportunity_state_machine.md`
     - `docs/architecture/opportunity_state_transition_policy.md`
     - `docs/architecture/opportunity_state_forbidden_jumps.md`
     - `opportunity_engine/states.py`
     - `opportunity_engine/schemas.py`
     - `opportunity_engine/transitions.py`
     - `tests/test_g7_2_opportunity_state_machine.py`
2. State semantics formula:
   - `thesis_broken_override = thesis_broken ? THESIS_BROKEN : requested_state`.
   - `left_side_confirmation_gate = LEFT_SIDE_RISK -> ACCUMULATION_WATCH|CONFIRMATION_WATCH -> BUYING_RANGE`.
   - `estimated_only_action_state = false`.
   - `inferred_only_hold_state = false`.
   - source paths:
     - `docs/architecture/opportunity_state_forbidden_jumps.md`
     - `opportunity_engine/transitions.py`
3. G7.2 non-action invariant:
   - `g7_2_provider_scope_valid = 1` iff G7.2 docs/code/tests/context/handover/SAW are updated and no candidate generation/search/backtest/replay/proxy/ranking/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_2_state_machine_20260509.md`

## Phase G7.3 Signal-to-State Source Eligibility Notes

1. Source eligibility formula:
   - `state_eligible = source_class_allowed and freshness_known and forbidden_state_influence_excludes(target_state)`.
   - This is a source-policy formula only; it is not provider implementation or ranking authority.
   - source paths:
     - `docs/architecture/godview_signal_to_state_map.md`
     - `docs/architecture/godview_source_eligibility_policy.md`
     - `docs/architecture/godview_signal_confidence_policy.md`
     - `opportunity_engine/source_classes.py`
     - `opportunity_engine/signal_policy.py`
     - `tests/test_g7_3_signal_to_state_source_map.py`
2. Source labels formula:
   - `observed_official_context = SEC|FINRA|CFTC|FRED|KenFrench`.
   - `estimated_only_action_state = false`.
   - `tier2_yfinance_action_state = false`.
   - source paths:
     - `docs/architecture/godview_source_eligibility_policy.md`
     - `docs/architecture/godview_signal_confidence_policy.md`
3. G7.3 non-provider invariant:
   - `g7_3_provider_scope_valid = 1` iff G7.3 docs/code/tests/context/handover/SAW are updated and no provider/source-registry/live API/ranking/alert/broker/dashboard-runtime behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_3_signal_to_state_map_20260509.md`

## Phase G7.4 Dashboard Wireframe / Product-State Spec Notes

1. Dashboard state spec formula:
   - `dashboard_card = state + prior_state + reason_codes + source_breakdown + blockers + monitoring_questions`.
   - `brief_state_only = state_changes + freshness_gaps + blockers + questions`.
   - This is a product-spec formula only; it is not runtime UI behavior.
   - source paths:
     - `docs/architecture/godview_dashboard_wireframe.md`
     - `docs/architecture/godview_watchlist_card_spec.md`
     - `docs/architecture/godview_daily_brief_spec.md`
     - `tests/test_g7_4_dashboard_state_spec.py`
2. Dashboard wording formula:
   - `state_label_only = true`.
   - `no_buy_sell_alert_score_rank = true`.
   - `no_runtime_streamlit = true`.
   - source paths:
     - `docs/architecture/godview_dashboard_wireframe.md`
     - `docs/architecture/godview_watchlist_card_spec.md`
     - `docs/architecture/godview_daily_brief_spec.md`
3. G7.4 non-runtime invariant:
   - `g7_4_provider_scope_valid = 1` iff G7.4 docs/tests/context/handover/SAW are updated and no dashboard runtime code, Streamlit edits, candidate card, alert, broker, or provider behavior is added.
   - source paths:
     - `docs/phase_brief/phase65-brief.md`
     - `docs/context/done_checklist_current.md`
     - `docs/context/bridge_contract_current.md`
     - `docs/saw_reports/saw_phase65_g7_4_dashboard_wireframe_20260509.md`
## Phase G8.1B Pipeline-First Discovery Scout Notes

1. Equal-weight scout wrapper formula:
   - `factor_weights = {momentum_normalized: 0.25, quality_normalized: 0.25, volatility_normalized: 0.25, illiquidity_normalized: 0.25}`.
   - `sum(factor_weights) = 1.0`.
   - This is wrapper metadata for the existing local artifact, not optimization or model validation.
   - source paths:
     - `opportunity_engine/factor_scout_schema.py`
     - `data/discovery/local_factor_scout_baseline_v0.json`
2. Deterministic fixture-selection formula:
   - `eligible = (date == max(date)) and score_valid and non_null(momentum_normalized, quality_normalized, volatility_normalized, illiquidity_normalized) and local_ticker_company_metadata_present`.
   - `selected_row = first eligible row ordered by asof_date descending and permno ascending`.
   - observed selection: `asof_date = 2026-02-13`, `permno = 10107`, `ticker = MSFT`.
   - source paths:
     - `opportunity_engine/factor_scout.py`
     - `data/discovery/local_factor_scout_output_tiny_v0.json`
3. G8.1B non-leakage invariant:
   - `g8_1b_valid = baseline_valid and output_count == 1 and discovery_origin == LOCAL_FACTOR_SCOUT and status == intake_only and is_system_scouted == true and is_user_seeded == false and is_validated == false and is_actionable == false and score_display == false and rank == false and buy_sell_signal == false and candidate_card == false`.
   - source paths:
     - `tests/test_g8_1b_pipeline_first_discovery_scout.py`
     - `docs/architecture/factor_scout_output_contract.md`

## DASH-1 Page Registry Shell Notes

1. Navigation shell formula:
   - `dash_1_shell_valid = approved_page_order_present and streamlit_page_registry_present and selected_page_run_called and old_flat_tabs_absent`.
   - source paths:
     - `views/page_registry.py`
     - `dashboard.py`
     - `tests/test_dash_1_page_registry_shell.py`
2. Legacy relocation formula:
   - `Ticker Pool & Proxies -> Opportunities`.
   - `Data Health + Drift Monitor -> Settings & Ops`.
   - `Daily Scan + Backtest Lab + Modular Strategies + Hedge Harvester -> Research Lab`.
   - `Portfolio Builder + Shadow Portfolio -> Portfolio & Allocation`.
   - source paths:
     - `views/page_registry.py`
     - `dashboard.py`
3. DASH-1 non-expansion invariant:
   - `dash_1_scope_valid = shell_only and legacy_relocation_only and no_new_metrics and no_new_data and no_ranking and no_scoring and no_alerts and no_broker_calls and no_provider_ingestion and no_factor_scout_integration`.
   - source paths:
     - `tests/test_dash_1_page_registry_shell.py`
     - `docs/saw_reports/saw_dash_1_page_registry_shell_20260510.md`

## Phase G8.2 System-Scouted Candidate Card Notes

1. Scout-to-card eligibility formula:
   - `eligible_card_ticker = scout_output.items[0].ticker = MSFT`.
   - `eligible_card_count = 1`.
   - This uses the existing governed `LOCAL_FACTOR_SCOUT` output only; it does not create a new scout output.
   - source paths:
     - `data/discovery/local_factor_scout_output_tiny_v0.json`
     - `data/discovery/local_factor_scout_output_tiny_v0.manifest.json`
     - `tests/test_g8_2_system_scouted_candidate_card.py`
2. Candidate-card validity formula:
   - `g8_2_card_valid = card_valid and ticker_matches_scout and source_intake_manifest_present and candidate_manifest_present and no_score_rank_action`.
   - `no_score_rank_action = no_factor_score and no_rank and no_buy_sell_hold and not_validated and not_actionable and no_buying_range and no_alert and no_broker_action`.
   - source paths:
     - `opportunity_engine/candidate_card_schema.py`
     - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
     - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
     - `tests/test_g8_2_system_scouted_candidate_card.py`
3. Candidate-card universe formula:
   - `candidate_cards = {MU, MSFT}`.
   - `new_user_seeded_cards = 0` for G8.2.
   - source paths:
     - `data/candidate_cards/`
     - `tests/test_g8_2_system_scouted_candidate_card.py`
4. Dashboard boundary formula:
   - `dashboard_msft_legacy_row != g8_2_msft_candidate_card`.
   - `dashboard_card_reader_authorized = false` until a later approved DASH lane.
   - source paths:
     - `dashboard.py`
     - `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
     - `docs/context/bridge_contract_current.md`

## DASH-2 Portfolio Allocation Runtime Notes

1. Optimized portfolio YTD return formula:
   - `portfolio_daily_return_t = sum(weight_i * price_return_i_t)` where `weight_i` is the current optimizer allocation normalized to sum to 1.
   - `portfolio_ytd_equity_t = cumulative_product(1 + portfolio_daily_return_t)`.
   - `portfolio_ytd_return = portfolio_ytd_equity_last - 1`.
   - source paths:
     - `core/data_orchestrator.py`
     - `views/optimizer_view.py`
     - `dashboard.py`
     - `tests/test_dash_2_portfolio_ytd.py`
2. Fresh price overlay formula:
   - `live_scaled_ticker_price = live_adjusted_close * (local_TRI_anchor / live_adjusted_close_anchor)`.
   - `refreshed_prices = local_TRI_history + live_scaled_overlay` with duplicate dates kept from the freshest overlay.
   - This is a runtime display freshness overlay only; it is not canonical provider ingestion or evidence-card validation.
   - source paths:
     - `core/data_orchestrator.py`
     - `views/optimizer_view.py`
     - `dashboard.py`
3. Portfolio page ordering formula:
   - `Portfolio & Allocation = Portfolio Optimizer -> YTD Performance vs SPY/QQQ -> Shadow Portfolio`.
   - source paths:
     - `dashboard.py`

## Portfolio Universe Construction Fix Notes

1. Optimizer universe formula:
   - `optimizer_universe = scanner_rows where policy_status = eligible and ticker_map_resolved = true and local_history_obs >= min_history_obs`.
   - `eligible = rating contains ENTER STRONG BUY or ENTER BUY`.
   - `research_only = rating contains WATCH`.
   - `excluded = rating_or_action contains EXIT or KILL or AVOID or IGNORE`.
   - source paths:
     - `strategies/portfolio_universe.py`
     - `dashboard.py`
     - `views/optimizer_view.py`
     - `tests/test_portfolio_universe.py`
2. Display-order non-leakage formula:
   - `portfolio_input_valid = explicit_optimizer_universe and not df_scan_display_order[:20]`.
   - source paths:
     - `dashboard.py`
     - `tests/test_dash_2_portfolio_ytd.py`
3. Max-weight feasibility formula:
   - `min_feasible_max_weight = 1 / n_assets`.
   - `is_feasible = max_weight * n_assets >= 1`.
   - `is_boundary_forced = is_feasible and max_weight <= min_feasible_max_weight + tolerance`.
   - source paths:
     - `strategies/portfolio_universe.py`
     - `views/optimizer_view.py`
     - `tests/test_portfolio_universe.py`
4. Thesis-neutral boundary:
   - `current_optimizer_conviction = 0`.
   - `mu_hard_floor = false`.
   - `black_litterman_runtime = false`.
   - Future conviction work requires a separate thesis-anchor policy before any expected-return tilt, confidence parameter, or anchor sizing can be implemented.
   - source paths:
     - `docs/architecture/portfolio_construction_contract.md`

## Portfolio Universe Optimizer-Core Quarantine Notes

1. Quarantine formula:
   - `portfolio_universe_closure_valid = universe_patch_scope_valid and strategies_optimizer_diff == empty and optimizer_core_diff_preserved_for_audit`.
   - `optimizer_core_diff_preserved_for_audit = exists(docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch)`.
   - source paths:
     - `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`
     - `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md`
     - `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md`
2. Optimizer-core policy boundary:
   - `lower_bound_slsqp_changes_accepted = false`.
   - `optimizer_core_policy_audit_required = true`.
   - Future acceptance requires policy docs, infeasibility tests, active-bound reporting rules, and a separate SAW report.
   - source paths:
     - `docs/architecture/optimizer_core_policy_audit.md`
     - `docs/architecture/optimizer_constraints_policy.md`
     - `docs/architecture/optimizer_lower_bound_slsqp_policy.md`
3. Provider-hygiene repair:
   - `views/optimizer_view.py` no longer imports yfinance or reads `data/backtest_results.json` directly.
   - Portfolio display-refresh price stitching and strategy metrics parsing are owned by `core/data_orchestrator.py`.
   - Direct yfinance usage remains behind provider ports or legacy allowlisted files; `views/optimizer_view.py` is no longer in `data/providers/legacy_allowlist.py`.
   - source paths:
      - `core/data_orchestrator.py`
      - `views/optimizer_view.py`
      - `data/providers/legacy_allowlist.py`
      - `tests/test_data_orchestrator_portfolio_runtime.py`

## Optimizer Core Structured Diagnostics Notes

1. Pre-solver feasibility formulas:
   - `upper_bound_feasible = n_assets > 0 and max_weight * n_assets >= 1`.
   - `lower_sum_feasible = min_weight * n_assets <= 1` for uniform diagnostic floors.
   - `required_min_sum_feasible = sum(required_min_weights) <= 1`.
   - `per_asset_bound_feasible = all(0 <= lower_i <= max_weight <= 1)`.
   - source paths:
     - `strategies/optimizer_diagnostics.py`
     - `strategies/optimizer.py`
     - `tests/test_optimizer_core_policy.py`
2. Equal-weight boundary formula:
   - `min_feasible_max_weight = 1 / n_assets`.
   - `equal_weight_forced = upper_bound_feasible and max_weight <= min_feasible_max_weight + tolerance`.
   - source paths:
     - `strategies/optimizer_diagnostics.py`
     - `views/optimizer_view.py`
     - `tests/test_optimizer_core_policy.py`
3. Bound and constraint diagnostics formulas:
   - `active_lower_i = weight_i <= lower_bound + tolerance`.
   - `active_upper_i = weight_i >= max_weight - tolerance`.
   - `cash_residual = 1 - sum(weights)`.
   - `full_investment_constraint_residual = sum(weights) - 1`.
   - source paths:
     - `strategies/optimizer_diagnostics.py`
     - `views/optimizer_view.py`
4. Fallback labeling formula:
   - `fallback_valid = fallback_used and result_is_optimized == false and fallback_reason is visible`.
   - `silent_fallback_valid = false`.
   - `non_finite_weight_valid = false`.
   - `non_finite_weight_result = ERROR and constraints_satisfied == false and result_is_optimized == false`.
   - source paths:
     - `strategies/optimizer.py`
     - `strategies/optimizer_diagnostics.py`
     - `views/optimizer_view.py`
     - `tests/test_optimizer_core_policy.py`
5. Scope boundary:
   - `optimizer_diagnostics_only = true`.
   - `mu_conviction = false`, `watch_investability_expansion = false`, `black_litterman = false`, `new_objective = false`, `scanner_rule_change = false`.
   - source paths:
     - `docs/architecture/optimizer_core_policy_audit.md`
     - `docs/architecture/optimizer_constraints_policy.md`
     - `docs/architecture/optimizer_lower_bound_slsqp_policy.md`

## Portfolio Optimizer View Test and Performance Notes

1. Display-only overlay cache formula:
   - `overlay_cache_key = sha256(version, sorted_tickers, start_iso)[:24]`.
   - `overlay_cache_hit = cache_path_exists and cache_age_seconds <= cache_ttl_seconds`.
   - `cold_cache_behavior = schedule_background_refresh and return local_TRI_prices`.
   - `stale_cache_behavior = return_cached_display_prices and schedule_background_refresh`; stale overlay data is display-only and never canonical provider evidence.
   - `future_mtime_cache_state = not_fresh`.
   - `cache_write = temp_parquet_same_dir -> os.replace(cache_path)`.
   - This cache is display freshness only; it is not canonical provider ingestion or candidate-card evidence.
   - source paths:
      - `core/data_orchestrator.py`
      - `.gitignore`
     - `tests/test_optimizer_view.py`
2. Live overlay scale cache formula:
   - `scale_cache_key = sha256(local_price_frame) + ":" + sha256(live_price_frame)`.
   - `clean_price_frame = numeric_coerce -> drop_all_nan_rows -> datetime_index -> sort -> duplicate_index_keep_last`.
   - `live_scaled_ticker_price = live_adjusted_close * (local_TRI_anchor / live_adjusted_close_anchor)`.
   - `refreshed_selected_prices = scaled_live_overlay.combine_first(local_TRI_prices)`, so partial live rows update only non-null live cells and cannot erase local prices for missing tickers.
   - Cached dataframes are returned as copies to prevent caller mutation from poisoning cache state.
   - source paths:
      - `core/data_orchestrator.py`
      - `tests/test_data_orchestrator_portfolio_runtime.py`
      - `tests/test_optimizer_view.py`
3. Optimizer run cache formula:
   - `optimizer_cache_inputs = method + selected_price_frame + max_weight + risk_free_rate`.
   - `sector_cap_path = post_solver_apply_sector_cap(weights, sector_map, max_sector_weight)`.
   - Sector cap remains a post-solver soft constraint and is not represented as an SLSQP bound or equality/inequality constraint.
   - source paths:
     - `views/optimizer_view.py`
     - `tests/test_optimizer_core_policy.py`
     - `tests/test_optimizer_view.py`

## Dashboard Scanner Testability Notes

1. Scanner macro score formula:
   - `rate_score = 50` when 63-day `^TNX` velocity is `<= 0`; `rate_score = 0` when velocity is `>= 0.50`; otherwise linearly interpolate over `[0.00, 0.50]`.
   - `credit_score = 50` when `VWEHX/VFISX` distance from its 200-day SMA is `>= 4.65%`; `credit_score = 0` when distance is `<= -2.0%`; otherwise linearly interpolate over `[-2.0%, 4.65%]`.
   - `macro_score = round(rate_score + credit_score)`.
   - `macro_score = None` when required close series contain non-finite values, invalid rate endpoints, non-positive credit denominator rows in an otherwise eligible credit window, or non-finite 200-day credit ratio math.
   - source paths:
     - `strategies/scanner.py`
     - `dashboard.py`
     - `tests/test_scanner.py`
2. Scanner entry/tactics formula:
   - `cluster = Heavy if ATR/current_price < 0.025; Sprinter if <= 0.045; else Scout`.
   - `base_support = EMA21` only when `macro_score >= 80`, `Score >= 95`, and `Convexity <= 1.5`; mania or macro defense uses `SMA50`.
   - `max_flush = 0.16` for Scout, `0.11` for Sprinter, `0.05` otherwise.
   - `premium = 0.05` when `Score >= 95`, `0.03` when `Score >= 90`, otherwise `0`.
   - `entry_price = base_support * (1 - max(0, max_flush - premium))`.
   - `support_distance_pct = ((current_price / entry_price) - 1) * 100`.
   - `tactics_multiplier = clamp(3.0 / (1.0 + 0.5 * max(0, convexity - 1.0) * max(0, support_distance_pct) / cluster_limit), 1.5, 3.0)`.
   - `target_price = entry_price + 3.0 * abs(entry_price - stop_loss)`.
   - source paths:
     - `strategies/scanner.py`
     - `dashboard.py`
     - `tests/test_scanner.py`
3. Scanner action label formula:
   - `Proxy_Signal = COILED SPRING` when proxy is strong and price is not stretched; `CORRELATED` when both proxy and price are strong; `DIVERGING`, `CORRECTING`, and `MISPRICED` follow the same proxy/price truth table.
   - `Rating` precedence: `KILL` action -> exit; parabolic warning -> tight-trail exit; terminal stretch -> wait; score-100 rows require proxy and distance gates before `ENTER`.
   - `Leverage = LEAPs` only when rating includes `STRONG BUY`, `macro_score >= 80`, and `Convexity <= 1.5`.
   - Breadth status returns `UNKNOWN (No Data)` when latest or 50-day SMA inputs are non-finite.
   - source paths:
     - `strategies/scanner.py`
     - `dashboard.py`
     - `tests/test_scanner.py`

## Dashboard Architecture Safety Notes

1. Process liveness probe:
   - `pid_is_running(pid) = false` when PID is invalid or confirmed not live.
   - Windows path: `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION) -> GetExitCodeProcess -> STILL_ACTIVE`.
   - Access denied is treated as live; probe failure is conservative and does not reclaim a potentially live lock owner.
   - Non-Windows path may use `os.kill(pid, 0)` only inside `utils/process.py`.
   - source paths:
     - `utils/process.py`
     - `dashboard.py`
     - `data/updater.py`
     - `scripts/parameter_sweep.py`
     - `scripts/release_controller.py`
     - `backtests/optimize_phase16_parameters.py`
     - `tests/test_process_utils.py`
2. Strategy-matrix builder:
   - `cagr_display = signed_percent(cagr_raw)` for numeric non-zero CAGR, raw string when preformatted, otherwise blank.
   - `max_dd_display = percent(max_dd_raw)` for numeric non-zero max drawdown, raw string when preformatted, otherwise blank.
   - `bt_status = Running... if running_name matches; else Done if cagr exists; else first sufficient strategy is Next; later sufficient strategies are Pending; insufficient strategies are Insufficient`.
   - source paths:
     - `dashboard.py`
3. Dashboard portfolio price cleanup:
   - `dashboard._clean_portfolio_price_frame(prices) = core.data_orchestrator.clean_price_frame(prices)`.
   - This inherits numeric coercion, all-NaN row dropping, datetime index normalization, timezone removal, sorting, and duplicate timestamp `keep=last`.
   - source paths:
     - `dashboard.py`
     - `core/data_orchestrator.py`

## Dashboard Unified Data Cache Notes

1. Unified parquet package cache:
   - `dashboard._load_unified_data_cached(...)` wraps `core.data_orchestrator.load_unified_data(...)` with `st.cache_resource`.
   - Cache key includes loader args plus `data_signature = build_unified_data_cache_signature(processed_dir, static_dir)`.
   - `build_unified_data_cache_signature(...)` records `(resolved_path, st_mtime_ns, st_size)` for the dashboard source parquet files, including price, patch, macro/liquidity, ticker, fundamentals, calendar, and sector-map inputs.
   - This removes repeated DuckDB/pivot/concat work on normal Streamlit widget reruns while invalidating when relevant parquet inputs are added, removed, or rewritten.
   - source paths:
     - `dashboard.py`
     - `core/data_orchestrator.py`
     - `tests/test_data_orchestrator_portfolio_runtime.py`
     - `tests/test_dashboard_sprint_a.py`

## Portfolio Lifecycle Current-Hold Notes

1. PIT-safe open-position reconstruction:
   - `open_position_ticker = true` iff the latest lifecycle event for that ticker with `event_date <= as_of` has `action = ENTER`.
   - A later `EXIT` event removes the ticker from the open-position set.
   - Future-dated replay rows are ignored for the current portfolio view.
   - `current_position_memory = open_lifecycle_positions` when lifecycle replay evidence exists; JSON position memory is only a fallback when the lifecycle log is empty.
   - Lifecycle JSONL appends use a lock plus temp-file write and `os.replace`.
   - Malformed JSONL rows raise a visible error instead of being silently skipped.
   - source paths:
     - `data/portfolio_lifecycle_log.py`
     - `strategies/portfolio_universe.py`
     - `tests/test_position_lifecycle.py`
2. Current-hold allocation formula:
   - Open lifecycle holdings enter the optimizer universe as `included_current_hold`, even when today's scanner row is `EXIT` / `KILL`; only lifecycle `EXIT` closes the current holding.
   - When the included universe has current holds and no fresh `eligible_rating` entry candidates, the Portfolio Optimizer renders current lifecycle holdings rather than a 100% cash pie.
   - `hold_weight_i = last_weight_i` from lifecycle position memory.
   - If `sum(hold_weight_i) <= 1`, `cash_weight = 1 - sum(hold_weight_i)`.
   - If `sum(hold_weight_i) > 1`, hold weights are normalized by their total and `cash_weight = 0`.
   - Portfolio performance preserves residual cash by normalizing session, ticker-mapped, and aligned weights only when their sum exceeds 100%.
   - source paths:
     - `views/optimizer_view.py`
     - `dashboard.py`
     - `tests/test_optimizer_view.py`
     - `tests/test_dash_2_portfolio_ytd.py`


## Pinned Strategy Universe Formula (2026-05-12)

### Manifest
- Source: `data/universe/pinned_thesis_universe.yml`
- Tickers: MU, AMD, AVGO, TSM, INTC, LRCX, SNDK, WDC, NVDA, AMAT

### Feature Universe Construction
```
feature_universe = yearly_top_n(200) ∪ get_pinned_permnos()
```
- `data/feature_store.py run_build()` unions pinned permnos after yearly selector
- Build aborts if pinned loader fails (unless `allow_missing_pinned_universe=True`)

### PIT Replay Eligibility (shared gate: `is_pit_eligible()`)
```
ENTER when:
  z_demand > 0
  AND capital_cycle_score > 0
  AND dist_sma20 ≤ 0.05
  AND NOT trend_veto

EXIT when:
  dist_sma20 > 0.12
  OR trend_veto (on held position)
```
- Used by: `scripts/pit_lifecycle_replay.py` (both `run_pit_replay` and `diagnose_pinned_exclusions`)
- PIT-equivalent of live scanner logic (not identical — live uses Delta_Demand/Supply/Pricing/Margin + crisis gates)

### Replay Ticker Universe
```
replay_tickers = SCANNER_TICKERS ∪ get_pinned_tickers()
```
- Raises on loader failure (no silent fallback to scanner-only)

### Fail-Closed Invariants
- Missing manifest → FileNotFoundError (not empty list)
- Empty/malformed manifest → ValueError
- Duplicate tickers → ValueError
- Feature build without pinned → aborts (not warns)
- Replay without pinned → raises (not falls back)

## Lifecycle Decision Export Notes (2026-05-12)

1. Export-only decision tape:
   - `export_lifecycle_decision_log(...)` replays the PIT lifecycle state machine and writes analysis rows without appending to `data/portfolio_lifecycle_log.jsonl`.
   - `decision_action = BUY` iff the replay would emit lifecycle `ENTER`.
   - `decision_action = SELL` iff the replay would emit lifecycle `EXIT`.
   - `decision_action = HOLD` iff a ticker is already held and no confirmed exit is emitted.
   - `decision_action = NO_ACTION` iff the ticker is flat and no confirmed entry is emitted.
   - source paths:
     - `scripts/pit_lifecycle_replay.py`
     - `tests/test_pinned_universe.py`
2. Exported Rule-of-100 proxy state:
   - `demand = z_demand`
   - `supply = z_inventory_quality_proxy`
   - `pricing = z_moat`
   - `margin = z_discipline_cond`
   - `rule100_confirmed = count(present factors) >= 3 AND count(positive factors) >= 3`
   - These fields are audit proxies only; literal Rule-of-100 supply/pricing/margin columns do not yet exist in `features.parquet`.
3. Export artifacts:
   - Full tape: `data/portfolio_lifecycle_decision_log.jsonl`
   - Buy/sell-only tape: `data/portfolio_lifecycle_buy_sell_log.jsonl`
   - Audit summary: `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`
   - Latest export: 5424 decision rows, 18 BUY, 15 SELL, open AMAT/LRCX/TSM, and no <=5-day round trips.

## Rule100 Lifecycle Policy v0 Notes (2026-05-12)

1. Rule100State adapter:
   - `demand = z_demand`
   - `supply = z_inventory_quality_proxy`
   - `pricing = z_moat`
   - `margin = z_discipline_cond`
   - `rule100_confirmed = factor_present_count >= 3 AND factor_positive_count >= 3`
   - `rule100_hold_intact = factor_present_count >= 3 AND factor_positive_count >= 2`
   - `rule100_provenance` records each proxy source column.
   - source paths:
     - `scripts/pit_lifecycle_replay.py`
     - `tests/test_pinned_universe.py`
2. Lifecycle action formula:
   - `BUY = FLAT AND rule100_confirmed AND dist_sma20 <= 0.05 AND NOT trend_veto AND entry_streak >= 3 AND NOT cooldown`.
   - `HOLD = HELD AND factor_positive_count >= 2 AND NOT trim_signal AND NOT full_exit`.
   - `TIGHTEN = HELD AND factor_positive_count < 2`; audit-only, no v0 weight change.
   - `TRIM = HELD AND 0.12 < dist_sma20 <= 0.20`; audit-only, `suggested_weight_delta = -0.025`, no v0 weight change.
   - `EXIT = HELD AND (dist_sma20 > 0.20 OR confirmed trend_veto)`.
   - `NO_ACTION = FLAT and no confirmed BUY`.
3. Conviction entry sizing:
   - `target_weight = min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15)`.
   - Current v0 replay has no 4/4 entry rows, so all promoted ENTER weights remain `0.10`.
4. Delta evidence:
   - Prior baseline: 33 runtime events, BUY=18, SELL=15, HOLD=993, NO_ACTION=4398.
   - Rule100 v0: 29 runtime events, BUY=16, SELL=13, HOLD=739, TRIM=55, TIGHTEN=257, NO_ACTION=4344.
   - Open holds remain AMAT, LRCX, and TSM.
   - source artifacts:
     - `docs/context/e2e_evidence/portfolio_lifecycle_log_pre_rule100_v0_20260512.jsonl`
     - `docs/context/e2e_evidence/rule100_v0_lifecycle_replay_tmp.jsonl`
     - `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

## Rule of 100 Method Label Notes (2026-05-12)

1. Dropdown contract:
   - `OptimizationMethod.RULE_OF_100.value = "Rule of 100"`.
   - `Rule of 100` is included in `OPTIMIZATION_METHOD_OPTIONS`.
   - `Rule of 100` is not part of `MEAN_VARIANCE_METHODS`.
   - source paths:
     - `strategies/optimizer.py`
     - `tests/test_portfolio_universe.py`
2. Allocation routing:
   - `if controls.method == OptimizationMethod.RULE_OF_100`, Portfolio & Allocation now bypasses `_run_optimizer_cached(...)` and renders Rule100 softmax v1 target weights.
   - `rule100_target_weight_i = softmax_v1_weight_i` for `sizing_eligible == True` lifecycle holds.
   - `cash_weight = 1 - sum(rule100_target_weight_i)` when target weights sum below 100%.
   - If no lifecycle holds are softmax-eligible, session state is cash-only and no stale lifecycle `last_weight` is displayed.
   - Current 2026-05-12 live target: `AMAT=0.10`, `LRCX=0.10`, `TSM=0.00`, `CASH=0.80`; `portfolio_allocation_state.source = "rule100_softmax_v1"`.
   - source paths:
     - `views/optimizer_view.py`
     - `tests/test_optimizer_view.py`

## Rule100 Softmax v1 Audit Notes (2026-05-12)

1. Primary sizing formula:
   - `eligible_count = count(sizing_eligible == True)`
   - `gross_budget = min(1.0, 0.10 * eligible_count)`
   - `score_i = 0.75 * max(factor_positive_count_i - 3, 0) + 0.25 * technical_quality_i + hold_weight * hold_intact_i - age_penalty_weight * age_penalty_i - trim_penalty_weight * trim_penalty_i`
   - Default v1 audit parameters set `hold_weight = age_penalty_weight = trim_penalty_weight = 0`, so the live artifact formula is the expert-report v1 score until those optional knobs are explicitly approved.
   - `softmax_weight_i = cap_15pct(gross_budget * softmax(score_i / tau))`
   - `cash_residual = 1 - sum(softmax_weight_i)`
   - source paths:
     - `strategies/rule100_softmax.py`
     - `scripts/rule100_softmax_v1_audit.py`

2. Kelly comparator formula:
   - `kelly_fraction_i = max(0, ((odds * p_i) - (1 - p_i)) / odds)`
   - `p_i` is the same shared audit score proxy, clipped into `[0, 1]`.
   - comparator budget is the same harness budget, but only positive-edge names participate; leftover cash stays explicit.
   - source paths:
     - `strategies/rule100_softmax.py`
     - `scripts/rule100_softmax_v1_audit.py`

3. Audit outputs:
   - `data/processed/rule100_softmax_v1_summary.json`
   - `data/processed/rule100_softmax_v1_comparison.csv`
   - `data/processed/rule100_softmax_v1_sample_output.csv`
   - `data/processed/rule100_softmax_v1_cash_allocation.csv`
   - softmax remains the primary path; Kelly stays comparator-only.

4. Live UI wiring:
   - `_rule100_softmax_weights_for_ui(...)` builds/receives the PIT candidate frame, filters `sizing_eligible`, calls `softmax_v1_weights(...)`, maps ticker weights back to selected permnos, and preserves residual cash.
    - `dashboard._render_portfolio_ytd_chart()` reads the same `portfolio_allocation_state.weights`, so YTD now follows the softmax v1 target weights after the user selects `Rule of 100`.
    - With current equal AMAT/LRCX scores, visible max allocation is still 10%; a >10% winner needs richer continuous score inputs or unequal eligible scores, not a Kelly stack.

## Portfolio Market-Data Freshness Endpoint Cache Notes (2026-05-14)

1. Endpoint snapshot contract:
   - `PriceEndpointFreshness.latest_by_column[col] = max(date where price_col(date) is finite and price_col(date) > 0)`.
   - `PriceEndpointFreshness.required_latest = max(latest_by_column values where value is not None)`.
   - `build_price_endpoint_freshness(...)` computes this once per loaded matrix/supplied column set.
   - source path: `core/data_orchestrator.py`.

2. Dashboard cache contract:
   - `dashboard.py` computes the endpoint snapshot once after the cached unified parquet package loads.
   - cache key includes unified source file signatures, loader arguments, and matrix shape.
   - the snapshot is passed to portfolio YTD, optimizer universe construction, and optimizer rendering.
   - source path: `dashboard.py`.

3. Downstream reuse:
   - `views.optimizer_view._order_assets_by_trailing_one_year_return(...)` uses the supplied snapshot for endpoint demotion.
   - `views.optimizer_view._prepare_selected_prices(...)` uses the supplied snapshot for `required_latest`.
   - `strategies.portfolio_universe.build_optimizer_universe(...)` uses the supplied snapshot for matrix endpoint and per-column endpoint checks.
   - direct callers without a snapshot build one snapshot once rather than repeatedly scanning per helper call.

4. SAW reconciliation guardrails:
   - weighted portfolio YTD requires every positive-weight asset to be present in the local or live price frame before computing returns;
   - partial live provider responses cannot become partial portfolio performance evidence;
   - replay-derived latest weights are valid only when their replay signature matches the current latest-date method, cap, assets, and data signature;
   - cached full replay/YTD contexts are valid only when their replay signature matches the current full-horizon method, cap, assets, data, replay dates, and sampling signature;
   - non-ready or failed replay contexts clear stale replay/YTD session weights.

5. Measured local performance:
   - actual `prices_wide` shape `(2857, 2000)`;
   - snapshot build: `0.2966s`;
   - old per-column loop: `0.9555s`;
   - maps matched exactly;
   - downstream 50 endpoint lookups after snapshot: `0.001531s`.

## Portfolio Market-Data Freshness Fail-Closed Notes (2026-05-14)

1. Per-asset endpoint freshness:
   - `endpoint_i = max(date where price_i(date) is finite and price_i(date) > 0)`.
   - `matrix_endpoint = max(endpoint_i for available columns)`.
   - `fresh_i(required_endpoint) = endpoint_i >= required_endpoint`.
   - source path: `core/data_orchestrator.py`.

2. Benchmark YTD:
   - local benchmark TRI remains the first source;
   - stale/missing benchmark tickers attempt display-only live overlay;
   - tickers that still fail freshness are dropped rather than forward-filled;
   - remaining benchmark curves are reported through a common endpoint.
   - source paths: `core/data_orchestrator.py`, `dashboard.py`.

3. Portfolio YTD:
   - local weighted YTD requires every nonzero weighted leg to reach the required endpoint;
   - stale weighted legs make the local portfolio curve unavailable instead of creating a partial portfolio;
   - residual cash remains preserved unless weights exceed 100%.
   - source path: `dashboard.py`.

4. Optimizer freshness:
   - selected-price overlay takes `required_latest=price_frame_latest_date(prices_wide)`;
   - stale selected assets that cannot be refreshed are dropped before optimization;
   - default asset ordering demotes assets whose own endpoint is stale before trailing-return ranking;
   - universe eligibility requires both enough observations and endpoint freshness.
   - source paths: `core/data_orchestrator.py`, `views/optimizer_view.py`, `strategies/portfolio_universe.py`.

## Frontend/UI Saved Replay Source Selector Notes (2026-05-14)

1. Source selector contract:
   - `_build_dashboard_replay_request(...)` constructs the selected-method replay request without reading saved artifacts or calling the backend builder.
   - `_read_dashboard_saved_replay_artifact(...)` calls backend `read_selected_method_replay_artifact(...)` and accepts a saved bundle only when the manifest also carries an exact `dashboard_cache_signature`.
   - `dashboard_cache_signature` binds method, max-weight cap, non-frame controls, selected replay assets, replay dates, sampling, and dashboard data signature.
   - Valid saved artifacts produce `DashboardReplayContext.source_mode = "saved_artifact"`.
   - Missing, stale, mismatched, or over-budget artifacts return unavailable context when transitional fallback is disabled, or fall back to the labeled backend build when fallback is allowed.
2. Shared consumer contract:
   - YTD latest weights, Portfolio YTD replay equity, Strategy Replay rows, Latest Snapshot, ENTER/EXIT annotations, and Buy/Sell Decision Log consume the same `DashboardReplayContext`.
   - `_render_strategy_replay_section()` does not directly read lifecycle JSONL or compact Buy/Sell JSONL.
   - Stale artifact paths clear replay/YTD session keys rather than reusing prior latest weights.
3. Source labels:
   - UI copy uses factual source labels only: `saved artifact`, `transitional build`, or `saved artifact unavailable`.
   - No promotion, action, recommendation, alert, broker, or trading language was added.
4. Evidence:
   - `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
   - `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 105 passed.

### Saved Artifact Single-Source Aux Surface Repair (2026-05-14)

1. Repair:
   - `_dashboard_context_from_artifact_read(...)` now preserves saved artifact event and decision rows exactly.
   - A saved artifact with daily portfolio rows but empty event/decision rows keeps those aux surfaces empty, even if separately loaded dashboard fallback frames are non-empty.
   - This keeps `source_mode="saved_artifact"` truthful for replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell Decision Log rows.
2. Evidence:
   - `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
   - `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_dashboard_replay_context_prefers_valid_saved_artifact tests\test_dash_2_portfolio_ytd.py::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows tests\test_dash_2_portfolio_ytd.py::test_dash_2_stale_saved_artifact_clears_replay_state_when_no_fallback -q` -> PASS, 3 passed.
   - `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 106 passed.
   - `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md` records the reconciled SAW PASS.

## Ultra-Modular Replay Architecture Enforcement Notes (2026-05-13)

1. Selected-method replay-source invariant:
   - `selected_method_replay_source := one replay run/source feeding YTD + current allocation/latest snapshot + Strategy Replay + ENTER/EXIT annotations + Buy/Sell Decision Log + saved evidence`.
   - No downstream surface may recompute selected-method weights independently, reuse stale allocation session state, read a separate overlay artifact, or summarize a different decision tape and still claim selected-method replay authority.
   - If the source is missing, stale, partial, over budget, or not PIT-safe, downstream surfaces must fail closed as unavailable/cash-closed.
2. Architecture goal:
   - `selected-method adapter -> one replay run -> daily portfolio output -> event/annotation output -> YTD/performance -> decision log -> saved evidence artifact`.
   - Transitional bridges are allowed only as labeled, bounded, non-canonical migration aids.
3. Required implementation proof:
   - shared replay run id / artifact id;
   - selected-method adapter mapping;
   - shared daily portfolio output for YTD and latest allocation snapshot;
   - shared event/annotation output for ENTER/EXIT annotations and Buy/Sell Decision Log;
   - saved evidence artifact with input signatures, method id, date window, costs, baseline id, row/status counts, and timing;
   - performance budget covering cold-start replay, rerun/cache path, max rows/dates, and fail-closed timeout behavior.
4. Guardrails:
   - no future-data leakage;
   - no stale-data carry-forward;
   - no fake improvements without same-window/same-cost/same-engine baseline deltas;
   - no overfit promotion;
   - no broker/live trading, alerts, rankings, recommendations, candidate scoring, or autonomous allocation.
5. Source paths:
   - `docs/phase_brief/phase65-brief.md`
   - `docs/context/done_checklist_current.md`
   - `docs/context/bridge_contract_current.md`
   - `docs/context/planner_packet_current.md`
   - `docs/context/impact_packet_current.md`
   - `docs/saw_reports/saw_ultra_modular_replay_architecture_note_20260513.md`

## Replay Selected Price Loading + MU/SNDK Eligibility Trace Notes (2026-05-15)

1. Dashboard replay performance path:
   - `core.data_orchestrator.load_batched_pit_replay_data(...)` now accepts `selected_permnos`.
   - The loader still builds the full `r3000_pit` membership index for the replay window before loading prices.
   - Price/return matrix loading is limited to `selected_permnos ∩ PIT membership union` when selected permnos are provided.
   - `BatchedPITReplayData.metadata.pit_membership_proof = "full_window_membership_index"` records that selected price loading is not watchlist-only replay.
2. Dashboard call rule:
   - `_build_dashboard_strategy_replay_context(...)` passes `_numeric_replay_permnos(request.replay_assets)` into the batched loader.
   - `_filter_dashboard_replay_inputs_to_assets(...)` remains the final signed-asset filter before backend replay execution.
3. MU/SNDK diagnostic rule:
   - `scripts.pit_lifecycle_replay.trace_thesis_ticker_eligibility(...)` is a strategy/data diagnostic, not a replay performance hot-path dependency.
   - The trace answers pinned thesis universe presence, ticker-map permno, `r3000_pit` membership, local price/return rows, Rule100 history presence, and final exclusion gate.
   - Local price/return evidence requires a positive finite price and finite `total_ret`; non-finite returns fail closed as no local price/return row for that date.
4. Current local trace through 2026-05-11:
   - MU: pinned, permno `53613`, PIT member on latest date, local price/return row present, 104 Rule100 history dates, 70 eligible feature dates; latest exclusion gate is `technical quality` (`technical_entry_zone_failed`).
   - SNDK: pinned, permno `82618`, PIT member on latest date, local price/return row present, no Rule100 history dates, no eligible feature dates; latest exclusion gate is `factor threshold` (`technical_entry_zone_failed,factor_confirmation_failed_2_of_4`).
5. Evidence paths:
   - `core/data_orchestrator.py`
   - `dashboard.py`
   - `scripts/pit_lifecycle_replay.py`
   - `tests/test_data_orchestrator_portfolio_runtime.py`
   - `tests/test_optimizer_view.py`
   - `tests/test_pinned_universe.py`
   - `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json`
6. Verification:
   - Targeted non-finite return and selected-permno handoff regressions PASS.
   - Broader affected replay/data/dashboard/diagnostic suite PASS, 112 tests.

## Portfolio Replay Selection Identity Hardening Notes (2026-05-15)

1. Explicit replay selection:
   - `views.optimizer_view.PortfolioReplaySelection` is the page-level replay universe handoff.
   - It is stored under `portfolio_replay_selection` only after selected prices and optimizer controls render successfully.
   - The selection carries `method`, `max_weight`, `risk_free_rate`, `replay_assets`, `latest_price_date`, `source`, and `signature`.
2. Selection signature formula:
   - `selection_signature = f(version, method, max_weight, risk_free_rate, replay_asset_identities, price_frame_identity)`.
   - `price_frame_identity = {rows, columns, index_start, index_end, columns_hash, selected_price_hash}`.
   - `columns_hash = sha256(json([type(asset) + ":" + str(asset) for asset in prices_wide.columns]))`.
   - `selected_price_hash = sha256(hash_pandas_object(prices_wide[replay_assets], index=True) + typed_replay_asset_identities)`.
   - Dashboard replay cache signatures carry typed asset identities such as `int:1` and `str:1`.
3. Dashboard replay request rule:
   - `_build_dashboard_replay_request(...)` consumes `_current_portfolio_replay_selection(...)`.
   - Missing, stale, mismatched, or unavailable selection returns `portfolio_replay_selection_unavailable`.
   - Hidden `optimizer_universe` and first-10 price-column fallback cannot produce replay assets.
4. Fail-closed runtime paths:
   - optimizer builder errors/skips clear `portfolio_replay_selection` and replay/YTD session caches.
   - stale signed selections clear both the selection and replay session caches before a request can be built.
5. Open backend follow-up:
   - dashboard still loads lifecycle/decision JSONL as a labeled transitional producer-side bridge before bundle attachment.
   - final ownership remains backend artifact/dashboard-cache-signature producer work, not a UI render-surface change.
6. Evidence paths:
   - `views/optimizer_view.py`
   - `dashboard.py`
   - `tests/test_optimizer_view.py`
   - `tests/test_dash_2_portfolio_ytd.py`

## Frontend/UI Shared Replay Bundle Notes (2026-05-13)

1. Dashboard shared replay context:
   - `dashboard.DashboardReplayContext` is the selected-method UI bundle for Strategy Replay.
   - The bundle carries method, max-weight controls, replay rows, latest snapshot rows, ENTER/EXIT annotations, and compact Buy/Sell audit rows.
   - `_render_strategy_replay_section()` now consumes `context.event_annotations` and `context.buy_sell_decisions`; it does not call `read_lifecycle_log()` or read `data/portfolio_lifecycle_buy_sell_log.jsonl` directly in the render surface.
2. YTD and latest snapshot:
   - `_prime_strategy_replay_latest_snapshot_for_ytd()` builds the latest selected-method replay date before Portfolio Performance renders.
   - `_current_optimizer_weights()` prefers `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY` and falls back to legacy `optimizer_weights` only when no replay snapshot is available.
   - The Strategy Replay `Latest Snapshot` table is derived from `DashboardReplayContext.latest_snapshot`.
3. Transitional boundary:
   - Backend replay output artifacts are still input/display-cache oriented; this UI slice creates a minimal dashboard adapter rather than changing `strategies/strategy_replay.py`.
   - Full saved replay-output artifact integration remains the backend follow-up.
4. Evidence:
   - `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py` -> PASS.
   - `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py -q` -> PASS, 89 passed.

## Rule100 Softmax v1.1 Research Contract Notes (2026-05-12)

1. Artifact contract:
   - Active v1.1 artifacts:
     - `data/processed/rule100_softmax_v1_1_comparison.csv`
     - `data/processed/rule100_softmax_v1_1_summary.json`
   - `data/processed/rule100_softmax_v1_1_history.csv` is not current; `scripts/rule100_softmax_v1_1_audit.py` retires it to `data/processed/rule100_softmax_v1_1_history.retired.csv` when present.
   - v1.1 remains research-only and does not mutate v1 artifacts, lifecycle log, position memory, UI routing, broker behavior, alerts, ranking, or scoring.
2. Approved factor groups:
   - demand: `z_demand`
   - inventory/supply: `z_inventory_quality_proxy`
   - moat/pricing: `z_moat`
   - capital discipline: first available value from `capital_cycle_score`, then `quality_composite`
   - `factor_present_count` and `factor_positive_count` count these groups, not raw columns.
3. Factor-strength shrinkage formula:
   - `coverage_i = factor_present_count_i / 4`
   - `factor_strength_continuous_i = mean_available_group_percentile_i * coverage_i + 0.50 * (1 - coverage_i)`
   - If no approved groups are present, `factor_strength_continuous_i = 0.50`.
4. Current same-window evidence:
   - AMAT/LRCX/TSM all have `factor_present_count = 4` in the refreshed v1.1 comparison artifact.
   - TSM has `factor_positive_count = 1` and remains ineligible for v1.1 sizing.
   - Real dashboard AppTest coverage now uses `AppTest.from_file("dashboard.py")` for the Policy Target Timeline TSM 2026-05-11 regression.
   - source paths:
     - `strategies/rule100_softmax_v1_1.py`
     - `scripts/rule100_softmax_v1_1_audit.py`
     - `tests/test_rule100_softmax_v1_1.py`
     - `tests/test_policy_target_timeline_apptest.py`

## Optimizer History Diagnostics Split Notes (2026-05-15)

1. Diagnostic split:
   - `OptimizerUniverseResult.insufficient_history` is still the backend fail-closed gate.
   - `missing_history` contains `local_price_history_unavailable` and `open_position_price_history_unavailable`.
   - `stale_endpoint` contains `stale_price_endpoint` and `open_position_stale_price_endpoint`.
2. UI contract:
   - Universe Audit metrics show `Missing History` and `Stale Endpoint` instead of the old mixed `History Fail` label.
   - Universe Audit table includes `Latest Price Date`.
   - Allocation explanation uses `Missing local price history` and `Stale local price endpoints`.
3. Boundary:
   - This is diagnostics-only and does not repair or backfill stale columns.
   - The stale endpoint gate remains fail-closed.
4. Evidence paths:
   - `strategies/portfolio_universe.py`
   - `views/optimizer_view.py`
   - `tests/test_portfolio_universe.py`
   - `tests/test_optimizer_view.py`

## Portfolio Replay Role Contract Notes (2026-05-15)

1. Replay row semantics:
   - `context_role` is the durable exposure-semantics contract: `current_holding`, `historical_context`, `flat_in_replay`, `cash`, or `unavailable`.
   - `row_role` is the durable artifact/table-shape contract: `daily_portfolio`, `event_annotation`, or `buy_sell_decision`.
   - `target_weight` remains selected-method replay exposure; aux `weight` remains lifecycle/event audit intent and dashboard aliases it as `audit_weight`.
2. Normalization authority:
   - `strategies.strategy_replay.normalize_context_frame_for_replay(...)` is the shared context-normalization owner.
   - Dashboard `_normalize_dashboard_context_frame(...)` delegates to that contract rather than mirroring date/ticker/method/replay-weight joins.
3. Artifact compatibility:
   - `REPLAY_COLUMNS`, `REPLAY_CONTEXT_COLUMNS`, and `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` now include role fields.
   - Legacy selected-method artifacts without `context_role` / `row_role` hydrate defaults on read; unrelated schema mismatches still fail closed.
4. Diagnostics:
   - `_build_replay_context_diagnostics(...)` computes closed-trade return summary, exit reason quality, zero-exposure BUY rows, hold-time summary, and reason concentration from the existing `DashboardReplayContext`.
   - Diagnostic artifacts bind `run_id`, `source_id`, `method_id`, and a cache-signature hash to the visible replay source.
5. Evidence paths:
   - `strategies/strategy_replay.py`
   - `dashboard.py`
   - `tests/test_strategy_replay.py`
   - `tests/test_strategy_replay_artifact.py`
   - `tests/test_dash_2_portfolio_ytd.py`
   - `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 169 passed.

## Portfolio Allocation State Split Notes (2026-05-12)

1. Explicit dashboard state:
   - `portfolio_allocation_state.mode` stores `optimizer`, `cash_only`, `current_hold_replay`, or `rule_of_100_replay`.
   - `portfolio_allocation_state.source` stores `optimizer` or `lifecycle_replay`.
   - `portfolio_allocation_state.weights` mirrors the active weights payload for the current view state.
   - Legacy session mirrors remain for compatibility: `optimizer_weights`, `optimizer_cash_only`, and `optimizer_price_latest_date`.
2. Route contract:
   - `Portfolio & Allocation` stays the default visible page.
   - `/portfolio-and-allocation` resolves through the explicit Streamlit page url path.
3. Copy split:
   - Optimizer output is described as optimizer output.
   - Lifecycle replay output is described as replay output, not optimizer output.
4. Evidence paths:
   - `views/optimizer_view.py`
   - `views/page_registry.py`
   - `dashboard.py`
   - `tests/test_optimizer_view.py`
   - `tests/test_dash_1_page_registry_shell.py`

## Research Validity Runner v0 Notes (2026-05-26)

1. Promotion formula:
   - `No cartridge + no canonical engine run + no PIT proof + no benchmark + no costs + no evidence packet = not research-valid`.
   - Code path: `docs/architecture/research_validity_contract.md`, `research/backtest_runner.py`.
2. Canonical engine wrapper:
   - `research.backtest_runner.run_research_backtest(...)` is the v0 evidence wrapper over `core.engine.run_simulation(...)`.
   - It forces `strict_missing_returns=True` and records `canonical_engine = core.engine.run_simulation`.
   - Caller-supplied `run_id` values are restricted to a single safe path segment before the evidence run directory is resolved.
3. Cash and target-weight policy:
   - Cash is implicit residual weight, not an engine column.
   - `cash_residual = 1.0 - sum(executed_risky_weights)`.
   - V0 target weights must have sorted unique dates, match the returns calendar, be numeric/finite/long-only, exclude `CASH`, and have row sums `<= 1.0`.
4. Cost formula:
   - `turnover_cost_rate = 0.0010 = 10 bps per unit one-way risky-asset turnover`.
   - Current engine bridge: `core.engine.run_simulation(..., cost_bps=turnover_cost_rate)`.
   - Engine cost formula remains `cost = turnover * cost_bps`; evidence reports both decimal rate and bps equivalent.
5. Benchmark and Rule100 adapter:
   - `research.benchmarks.build_pit_equal_weight_benchmark(...)` constructs same-date PIT equal-weight risky-asset weights and the benchmark runs through the same engine/cost/strict policy.
   - `research.adapters.rule100_replay_adapter` filters `daily_portfolio` rows, excludes CASH, pivots date x asset `target_weight`, rejects conflicting duplicate date/asset rows, ignores replay equity/performance columns, and leaves Rule100 `diagnostic_only`.
6. Evidence-write policy:
   - `research.evidence_schema.write_evidence_packet(...)` writes JSON/CSV artifacts through temp files in the destination run directory and promotes them with `os.replace`.
   - Existing `evidence_packet.json` is removed before same-run overwrite attempts, and the new final packet manifest is emitted only after component artifacts succeed.
7. Boundary:
   - No provider ingestion, canonical market-data write, strategy promotion, ranking, scoring, recommendation, alert, broker automation, autonomous allocation, or live trading is authorized.
8. Evidence paths:
   - `research/status.py`
   - `research/strategy_cartridge.py`
   - `research/backtest_runner.py`
   - `research/benchmarks.py`
   - `research/metrics.py`
   - `research/evidence_schema.py`
   - `research/adapters/rule100_replay_adapter.py`
   - `tests/test_research_status.py`
   - `tests/test_research_evidence_schema.py`
   - `tests/test_research_benchmarks.py`
   - `tests/test_research_backtest_runner.py`
   - `tests/test_research_rule100_adapter.py`

## Harness Workflow Notes (2026-05-30)

1. Skill/template flow:
   - `scope-selector` chooses the bounded scope before execution.
   - `expert-context-packer` prepares compact specialist/external review context.
   - `worker_done_contract` records worker completion, owned files, checks, and handoff status.
   - `expert_reconciliation_matrix` maps reviewer findings to fixes, owners, status, and open risks.
   - `stream_contract` records cross-stream ownership, boundaries, and handoffs.
   - `harness-feedback` captures repeated harness/SAW friction after the round.
2. Boundary:
   - This is docs-only workflow recording; no formulas, code, templates, skills, packet scripts, truth packets, data artifacts, or runtime behavior changed.
3. Evidence paths:
   - `AGENTS.md`
   - `docs/decision log.md`
   - `docs/notes.md`
   - `docs/lessonss.md`

## V2-D0 WRDS Permission + Snapshot Provenance Contract Notes (2026-06-01)

1. Contract scope:
   - `v2_discovery/data_lab/permission_matrix.py` owns the WRDS permission matrix.
   - `v2_discovery/data_lab/wrds_probe.py` owns the offline permission-probe contract and records no WRDS connection attempt.
   - `v2_discovery/data_lab/snapshot_manifest.py` owns the contract-only PIT snapshot manifest.
   - `v2_discovery/data_lab/schema_registry.py` owns JSON Schema validation.
2. Permission hash formula:
   - `permission_matrix_sha256 = sha256(canonical_json(permission_matrix_without_created_at_utc))`.
   - Source path: `v2_discovery/data_lab/permission_matrix.py`.
3. Snapshot validity formula:
   - `snapshot_contract_valid = all(provider/output/V1-write flags false) AND all PIT policy flags true AND planned_storage_uri not in forbidden V1/boot prefixes`.
   - Forbidden prefixes: `data/processed/`, `data/registry/`, `runtime/boot_status_current.json`, `docs/context/boot_status_current.json`.
   - Source path: `v2_discovery/data_lab/snapshot_manifest.py`.
4. Boundary:
   - No WRDS/provider access, PIT snapshot generation, committed WRDS output, V1 canonical mutation, dashboard runtime integration, ranking/scoring, recommendations, alerts, broker/order paths, SQLite, SafeBoot, or BootReady is authorized.
5. Reviewer reconciliation:
   - Root false flags require literal `False`, not merely falsey values.
   - `denied_actions` includes provider, snapshot, output, V1 write, ranking/scoring, candidate promotion, recommendations, dashboard integration, alert/broker, SQLite, SafeBoot, and BootReady blocks.
   - Storage planning is confined to repo-relative `data/runtime_cache/v2_data_lab/` paths and rejects absolute, drive-letter, UNC, URI-scheme, traversal, and V1/boot paths.
   - `jsonschema==4.26.0` is now a direct dependency in `pyproject.toml` and `requirements.txt`.
6. Evidence paths:
   - `tests/test_v2_wrds_permission_matrix.py`
   - `tests/test_v2_snapshot_manifest_contract.py`
   - `tests/test_v2_data_lab_no_v1_writes.py`

## V2-D0 Multi-Expert Reconciliation Gate Notes (2026-06-02)

1. Reconciliation logic:
   - Expert A PASS + NEEDS USER EVIDENCE means no read-only WRDS probe is authorized.
   - Expert B PATCH means patch only contract/tests and do not probe.
   - Expert C PASS keeps dashboard reader HOLD and G9 context-only.
2. Probe contract validity formula:
   - `probe_contract_valid = exact_root_keys AND exact_dataset_row_keys AND all(root provider/output/V1 flags false) AND next_allowed_action == "record_permission_decision_only" AND denied_actions == DENIED_ACTIONS AND code_ref == WRDS_PROBE_CODE_REF AND no credential/connection/output extra keys`.
   - Source path: `v2_discovery/data_lab/wrds_probe.py`.
3. Snapshot storage validity formula:
   - `snapshot_storage_valid = planned_storage_uri startswith "data/runtime_cache/v2_data_lab/" AND not bare_prefix AND not forbidden_V1_or_boot_path AND not absolute_or_drive_or_unc_or_uri_or_traversal`.
   - Source path: `v2_discovery/data_lab/snapshot_manifest.py`.
4. Boundary:
   - No WRDS/provider access, credential handling, snapshot generation, data output, `data/processed` write, runtime write, dashboard reader, ranking/scoring, recommendations, alerts, broker/order path, SQLite, SafeBoot, or BootReady is authorized.
5. Evidence paths:
   - `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md`
   - `docs/saw_reports/saw_v2_d0_multi_expert_reconciliation_20260602.md`
   - `tests/test_v2_wrds_permission_matrix.py`
   - `tests/test_v2_snapshot_manifest_contract.py`

## V2-D0.1 Authorization Intent Evidence Missing Notes (2026-06-03)

1. Authorization status:
   - `ROUND-20260603-V2-D0-1-AUTHORIZATION-INTENT` records approval intent only.
   - The packet is not final approval and does not create approval_ref values.
2. Row-state formula:
   - `authorization_row_approved = entitlement_evidence_present AND exact_approval_ref_present`.
   - Current value for all five rows is false because `entitlement_evidence_present = false`.
   - Rows: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus`.
3. Secret handling:
   - `secret.txt` is local secret material and is not non-secret entitlement evidence.
   - Do not read, quote, copy, or use `secret.txt` as an approval/evidence artifact.
4. Boundary:
   - No row approval, WRDS/provider access, credentials use, probe execution, snapshots, data writes, dashboard/runtime/scoring/broker paths, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.
5. Evidence paths:
   - `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md`
   - `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json`
   - `docs/saw_reports/saw_v2_d0_1_authorization_intent_20260603.md`

## V2-D0.2 WRDS Entitlement Evidence Request Notes (2026-06-03)

1. Request scope:
   - `ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST` prepares a copyable request for non-secret entitlement evidence only.
   - Target contacts are institutional data librarian, WRDS representative, PI, license owner, or data administrator.
2. Row-state formula:
   - `row_approval_valid = dated_attributable_non_secret_entitlement_evidence_present AND exact_approval_ref_present`.
   - Current value for all five rows remains false because evidence has not been obtained.
   - Rows: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus`.
3. Boundary:
   - The request does not authorize account/password use, WRDS/provider access, login, SSH, Python WRDS, SAS, SQL, schema/table discovery, row counts, snapshots, data output, runtime checks, row approval, legacy cleanup, secret remediation, SafeBoot, or BootReady.
4. Evidence paths:
   - `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.md`
   - `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.json`
# V2 PEAD D2A Formula Registry (2026-06-18)

- Security identity: `security_id = gvkey + "-" + iid` in `scripts/pead_d2_return_contract.py`.
- Total-return level: `TR_level_t = prccd_t * trfd_t / ajexdi_t` in `scripts/pead_d2_return_contract.py`.
- Canonical return: `total_return_t = TR_level_t / TR_level_{t-1} - 1`, lagged only within `(gvkey, iid)`.
- Fallback level: `price_level_t = prccd_t / ajexdi_t`; fallback return is `price_level_t / price_level_{t-1} - 1` within the same security.
- Logic chain: raw security-day levels -> exact source-overlap reconciliation -> within-security lag -> guardrails -> canonical return rows -> immutable hash-named Parquet -> atomic manifest commit pointer.
- Publication: `manifest.parquet_file` names the active immutable Parquet; readers load the manifest first. A process-scoped OS file lock rejects concurrent writers and is released automatically on process exit.
- The prior `trfd_t / trfd_{t-1} - 1` methodology is invalid and superseded because `trfd` is used with price and split adjustment to form the total-return level.
- `dollar_volume` remains a daily raw field and must not be described as ADV.
- D2B separately owns fixed event-level IID selection and `+60` market-session extraction.

# V2 PEAD D2B Formula Registry (2026-06-19)

Implementation path for every formula below: `scripts/pead_d2b_event_window_contract.py`. The downstream canonical window implementation remains `strategies/pead_event_study.py`; the D2B adapter does not implement a second window algorithm.

- Let `S = (s_1, ..., s_T)` be the sorted unique global D2A market-session spine and let `d_e` be event `e`'s event date.
- Prior-liquidity window: `W_e = last_20({s in S : s < d_e})`. The inequality is strict, so event-day and future liquidity are excluded.
- Finite observation count for event `e`, candidate security `i`: `n_ei = sum_{s in W_e} 1[isfinite(dollar_volume_i,s)]`.
- Candidate eligibility: `eligible_ei = 1[n_ei >= 15]`.
- Liquidity score: `L_ei = (1 / n_ei) * sum_{s in W_e, finite} dollar_volume_i,s`.
- Fixed-security selection: `i_e* = first(arg-sort_i(-L_ei, -n_ei, normalized_iid_i ASC, security_id_i ASC))` over eligible candidates. There is no `IID01` preference/fallback, and `i_e*` cannot switch after the event.
- First post-event index: `j_e = min{j : s_j > d_e}`.
- Return-date map: `return_date(e,k) = s_(j_e + k - 1)` for `k = 1,...,60`; when the global spine has no such session, the date remains missing. Security-row absence never compresses this map.
- Handoff eligibility: `H_e = 1[(i_e* exists) AND (all 60 return_date(e,k) exist) AND (all 60 returns r_(i_e*,return_date(e,k)) are finite)]`.
- Missing asset rows/non-finite returns remain missing; zero-return, `-100%`, and delisting imputations are false and no delisting label is emitted.
- Logic chain: stable D1/D2A byte snapshots -> prior-20 finite-liquidity selection -> one fixed event security -> exact global `+1..+60` skeleton -> eligibility gate -> immutable hash-named Parquet -> atomic manifest pointer -> eligible-only canonical strategy adapter.
- Current evidence: 12,582 events, 754,920 rows, 4,867 eligible events, output SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`.

# V2 PEAD D3 Benchmark Input Formula Registry (2026-06-19)

Contract path: `docs/phase_brief/v2-pead-d3-benchmark-input-contract.md`. Future implementation path is intentionally unassigned in this design gate.

- Canonical source: Kenneth R. French Data Library `Fama/French 3 Factors [Daily]`.
- Source URL: `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html`.
- Methodology URL: `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html`.
- Source units: Ken French factors are percent returns; canonical D3 artifact units must be decimal returns.
- Conversion: `mktrf = mktrf_percent / 100`; `rf = rf_percent / 100`.
- Benchmark formula: `benchmark_return = mktrf + rf`.
- Forbidden formula: `benchmark_return = mktrf` alone, because `mktrf` is excess market return.
- Strategy terminology: existing `car` in `strategies/pead_event_study.py` is beta-1 market-adjusted CAR, `sum(asset_return - benchmark_return)`, not regression alpha.
- BHAR terminology: existing `bhar` is `product(1 + asset_return) - product(1 + benchmark_return)`.
- Join rule: join strictly by `return_date` against the D2B market-session spine.
- Coverage rule: CAR/BHAR requires all 60 benchmark observations; missing benchmark dates remain missing with no fill, interpolation, or zero substitution.
- Current local artifact finding: `data/processed/ff_factors.parquet` has 1,003 rows from 2022-01-03 through 2025-12-31 and is insufficient for D2B's 2,862-session 2015-01-02 through 2026-03-06 spine.
- Logic chain: official daily factors -> percent-to-decimal conversion -> `mktrf + rf` total benchmark return -> strict D2B spine join -> 60-observation benchmark gate -> strategy CAR/BHAR semantics.

# V2 PEAD D3 Benchmark Artifact Builder Notes (2026-06-19)

Implementation path: `scripts/pead_d3_benchmark_artifact.py`. Focused tests: `tests/test_pead_d3_benchmark_artifact.py`.

- Parser source: official Ken French daily ZIP at `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip`.
- Source release observed during this round: `This file was created by using the 202604 CRSP database.`
- Source download SHA256 observed during this round: `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`.
- Parsed source coverage: 26,233 daily rows from 1926-07-01 through 2026-04-30.
- D3 builder derives required benchmark sessions from the D2A input recorded inside the D2B manifest, then verifies that session list against the D2B `session_spine` hash.
- Publication formula remains `benchmark_return = (Mkt-RF_percent / 100) + (RF_percent / 100)`.
- Strategy summary formula: `cumulative_total_return_e = product(1 + asset_return_d) - 1` remains reportable when the asset calendar and asset returns are complete; `cumulative_benchmark_return`, `car`, and `bhar` require complete benchmark observations, and `eligible_for_analysis` remains false when benchmark coverage is missing. Code path: `strategies/pead_event_study.py`.
- Publication rule: immutable hash-named Parquet is written before atomic manifest replacement, but only after required D2B coverage is complete.
- Stop-rule evidence: current D2B required sessions = 2,862; 52 are absent from Ken French daily factors, including U.S. market holidays/special closures such as 2015-01-19, 2015-05-25, 2015-11-26, 2018-12-05, 2022-06-20, 2025-01-09, and 2026-01-19.
- No D3 benchmark Parquet or manifest was published because missing benchmark dates must fail closed.
- Logic chain for this partial round: official daily ZIP -> parse release/source hash -> decimal conversion and formula tests -> D2B/D2A session-spine validation -> 52-date coverage miss -> stop before artifact publication.

# V2 PEAD D3 Benchmark Artifact Publication Notes (2026-06-20)

Implementation path: `scripts/pead_d3_benchmark_artifact.py`. Manifest path: `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`.

- Published Parquet: `data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`.
- Artifact SHA256: `f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`.
- Source release: `This file was created by using the 202604 CRSP database.`.
- Source download SHA256: `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`.
- Published coverage: 2,810 rows, 2015-01-02 through 2026-03-06, 2,810 / 2,810 D2B required sessions, zero missing.
- Formula: `benchmark_return = (Mkt-RF_percent / 100) + (RF_percent / 100)`.
- Integrity evidence: manifest SHA matches the Parquet, formula max absolute error is `0.0`, all numeric fields are finite, and duplicate `return_date` count is zero.
- Logic chain: official daily ZIP -> D2B-recorded source/hash match -> D2B source-backed session spine validation -> decimal conversion -> `mktrf + rf` benchmark rows -> immutable hash-named Parquet -> atomic manifest pointer.
- Boundary: this artifact is benchmark input only. CAR/BHAR interpretation, quintiles, dashboard integration, ranking/scoring, alerts, broker/order paths, full build, staging, and commit remain blocked.

# V2 PEAD D3 Strategy Benchmark Handoff Notes (2026-06-20)

Test path: `tests/test_pead_d3_strategy_handoff.py`. Production formula path: `strategies/pead_event_study.py`.

- No formula changed in this round.
- Join contract: `D2B LEFT JOIN D3 ON return_date`, validated `many_to_one`; row count remains 754,920.
- Benchmark completeness: `benchmark_observations_e = count(benchmark_return_e,d)` and every complete event requires exactly 60.
- CAR: `CAR_e = sum_d(asset_return_e,d - benchmark_return_d)`.
- BHAR: `BHAR_e = product_d(1 + asset_return_e,d) - product_d(1 + benchmark_return_d)`.
- Missingness: fewer than 60 benchmark observations makes CAR/BHAR null; complete asset observations still yield `cumulative_total_return_e = product_d(1 + asset_return_e,d) - 1`.
- Logic chain: D2B manifest pointer + D3 manifest pointer -> hash/cardinality/coverage checks -> strict date join -> complete-window benchmark count -> existing strategy summary -> D3 handoff closure.

# V2 PEAD Real-Data Validation Formula Registry (2026-06-20)

Implementation path: `scripts/pead_real_data_validation.py`. Focused tests:
`tests/test_pead_real_data_validation.py`. Evidence artifact:
`docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.

- Input lineage: D1 manifest/Parquet SHA256, D2B manifest/Parquet SHA256, and D3
  manifest/Parquet SHA256 are recomputed from stable file handles and reconciled
  against the D2B and D3 lineage declarations before analysis.
- Join: `D2B LEFT JOIN D3 ON return_date`, validated `many_to_one`; rows remain
  `754,920`, events remain `12,582`, issuers remain `362`, and strategy-eligible
  events remain `11,450`.
- Event outcomes: `CAR_e = sum_d(asset_return_e,d - benchmark_return_d)` and
  `BHAR_e = product_d(1 + asset_return_e,d) - product_d(1 + benchmark_return_d)`
  through `strategies/pead_event_study.py`.
- Quantile spread: `HML_c = mean(outcome | signal_quantile = 5, cohort = c) -
  mean(outcome | signal_quantile = 1, cohort = c)`.
- HAC: intercept-only OLS on the complete HML cohort series with Newey-West
  covariance and `requested_maxlags = 4`; any reindexed cohort gap returns null
  HAC standard error and t-stat with `hac_maxlags_used = 0`.
- Event-date locked result (`cohort_frequency = D`, `allow_ex_post_cohorts =
  false`): quantile-eligible events `9,040`; finite HML cohorts `831`; observed
  gaps `2,777`; CAR mean HML `0.03431429094213828`; BHAR mean HML
  `0.04531550411889198`; both HAC standard errors and t-statistics are null.
- Quarterly descriptive result (`cohort_frequency = Q`,
  `allow_ex_post_cohorts = true`, `ex_post_descriptive_only = true`):
  quantile-eligible events `11,447`; cohorts `40`; gaps `0`; CAR mean HML
  `0.036820699930804536`, HAC SE `0.011594221850280308`, t-stat
  `3.175780177943924`; BHAR mean HML `0.043028445081442365`, HAC SE
  `0.011270927611145428`, t-stat `3.817648960755726`.
- Coverage reasons from D2B: complete `11,450`, insufficient market sessions
  `526`, missing/non-finite asset returns `592`, no eligible security `14`.
- Limitations: 500-GVKEY sample; current-vintage EPS; Compustat return proxy; no
  delisting adjustment.
- Artifact SHA256: `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`;
  a second full script run reproduced the same bytes.
- Logic chain: locked D1/D2B/D3 manifest pointers -> stable hash/schema/row
  validation -> row-preserving D2B/D3 join -> existing event summary -> locked
  event-date and descriptive-quarterly quantiles -> strict JSON -> same-directory
  temp file -> fsync -> atomic replace.
- Formula summary: `D1/D2B/D3 -> CAR/BHAR_e -> cohort-local SUE quintiles ->
  HML_c -> fail-closed HAC(4)`; no result interpretation is authorized.

# V2 PEAD M1A Calendar-Time Inference Formula Registry (2026-06-21)

Future implementation paths: `strategies/pead_event_study.py` and
`scripts/pead_real_data_validation.py`. M1A changes no Python implementation.

- Signal formation uses event-date `signal_bucket_eligible`; future outcome or complete-window status must not affect quantile assignment.
- Position rule: assign all signal-eligible quantiles, then resolve one active exposure per `(security_id, return_date)` over event sessions `+1..+60`; latest `event_date` wins, equal-date ambiguity fails closed, and only then are Q1/Q5 retained.
- Daily legs: `R_Q,t = (1 / N_Q,t) * sum_i r_i,t` over finite distinct securities in Q1 or Q5, with `N_Q,t >= 10`.
- Spread: `R_HL,t = R_Q5,t - R_Q1,t`.
- Primary model: `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`; do not subtract `rf` from the zero-investment spread.
- Inference: Newey-West HAC with `maxlags = 59` and `use_correction = true`.
- Robustness: paired stationary block bootstrap on `(R_HL,t, mktrf_t)`, expected block length 60, exactly 10,000 replications, seed 20260621, same-regression intercept refit, 95% percentile interval, and centered-null two-sided p-value.
- Missingness: publish Q1/Q5 expected, finite, missing, and missing-rate diagnostics plus a complete-window sensitivity labeled descriptive-only.
- Parent-side feasibility count: 19,812 null-`return_date` signal-eligible rows are excluded before portfolio formation; after all-quantile latest-event overlap resolution and Q1/Q5 filtering, expected rows are 226,772 and missing asset rows are 1,519.
- Research support: Fama (1998), journal page 295 / PDF page 13, supports rolling calendar-time portfolios for cross-event return correlation; the daily frequency and exact parameters remain repo-policy adaptations.
- Logic chain: all signal-only event-date buckets -> authoritative active sessions -> all-quantile latest-event security/date dedup -> Q1/Q5 filter -> finite equal-weight spread -> D3-bound single-factor regression -> fixed HAC(59) -> robustness-only stationary bootstrap.
- Formula summary: `events + D2B + D3 -> R_HL,t -> alpha_CT(single-factor, HAC59)`; terminal M1A approval, M1B, and any alpha verdict remain unexecuted.

# V2 PEAD M1B Calendar-Time Inference Formula Registry (2026-06-21)

Implementation paths: `strategies/pead_event_study.py` and
`scripts/pead_real_data_validation.py`. Focused tests:
`tests/test_pead_event_study.py` and `tests/test_pead_real_data_validation.py`.
Evidence artifact:
`docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`.

- Formation input: D2B event-window rows plus D3 `mktrf`; D1/D2B/D3 lineage is
  rehashed and validated before output.
- Session-spine guard: `non_null(D2B.return_date) subset_of D3.return_date`;
  any off-spine date fails closed before the estimator can drop it.
- Signal assignment: `signal_bucket_eligible = isfinite(sue) and
  event_date_cohort_count >= 5`; this does not depend on future return
  completeness.
- Null-date handling: `null_return_date_rows_excluded = count(signal_eligible
  rows where return_date is null) = 19,812`; these rows are excluded before
  portfolio formation and are not asset-return missingness.
- Overlap: for non-null `security_id`, keep the max `event_date` for each
  `(security_id, return_date)` across all signal quantiles; tied latest event
  IDs fail closed. Rows with no eligible security are retained as expected
  missing when their assigned signal quantile is Q1 or Q5.
- Daily leg return: `R_Q,t = mean_i(asset_return_i,t)` over finite distinct
  securities in leg Q. Expected/missing diagnostics still count no-security and
  non-finite latest rows.
- Spread: `R_HL,t = R_Q5,t - R_Q1,t`.
- Primary model: `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t`.
- HAC: Newey-West with `maxlags = 59` and `use_correction = true`; retained
  `T = 2,539`, internal count gaps `0`, and `hac_maxlags_used = 59`.
- Robustness: paired stationary block bootstrap over `(R_HL,t, mktrf_t)` with
  expected block length `60`, replications `10,000`, seed `20260621`, and max
  batch size `256`; robustness cannot override the primary result.
- Published counts: expected extreme rows `226,772`; finite rows `225,253`;
  missing rows `1,519`; Q1 expected/finite/missing `96,310 / 95,465 / 845`; Q5
  expected/finite/missing `130,462 / 129,788 / 674`.
- Evidence arithmetic: `expected = finite + missing`, Q1/Q5 totals reconcile
  to extreme totals, and `missing_rate = missing / expected` in `[0,1]`.
- Null/output semantics: zero retained sessions publish null retained-date
  endpoints and null inference; the M1B CLI writes only the resolved canonical
  evidence path.
- Artifact SHA256:
  `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`.
- Formula summary: `D1/D2B/D3 -> signal-only buckets -> latest active
  security/date exposure -> R_HL,t -> alpha_CT(HAC59) + robustness bootstrap`;
  interpretation and product/action use remain unauthorized.

# V2 PEAD M6a.1 Sparse Portfolio Engine Formula Registry (2026-06-25)

Implementation path: `scripts/pead_m6_pit_walk_forward_equity_curve.py`.
Focused tests: `tests/test_pead_m6_pit_walk_forward_equity_curve.py`.

- Sparse event interval: for each selected event, `first_return_ordinal` is the first finite tradable return whose date is strictly after `decision_date`; active positions satisfy `first_return_ordinal <= return_ordinal < first_return_ordinal + holding_period_sessions`.
- Daily event weight: `w_event,t = side * (gross_exposure_target / 2) / active_event_count_side,t`.
- Security aggregation: `w_security,t = sum(w_event,t)` for every active event in the same security/date; `daily_gross_return_t = sum_security(w_security,t * tradable_total_return_security,t)`.
- Sparse turnover: `turnover_t = sum_{i in H_t union H_{t-1}} |w_i,t - w_i,t-1|`; the last session adds `sum_{i in H_T} |w_i,T|` so the final exit trades to zero.
- Runtime boundary: the engine does not materialize a return-date by security matrix or persist position-days. The configured DuckDB cap is `1024MB`; the synthetic full-universe smoke covers `196,638 * 60 = 11,798,280` bounded position-days.
- Gate semantics: `m6b_real_run_wiring_allowed=true` means only that this engine is scale-ready. It does not override `m6b_data_contract_ready=false` for EPS vintage, delisting-adjusted tradable returns, or full as-of tradability/liquidity requirements.

# V2 PEAD M6a.1 Calendar Index, Projection, and Determinism Guard (2026-06-25)

- Calendar index: project the distinct finite return dates, sort them once, assign `return_idx:int32`, then set `entry_idx = first(return_idx where return_date > decision_date)` and `exit_idx = entry_idx + holding_period_sessions - 1`. Sparse membership is exactly `entry_idx <= return_idx <= exit_idx`.
- Projection/dtype guard: DuckDB receives only `event_idx/security_idx/entry_idx/exit_idx/side`, `security_idx/return_idx/tradable_total_return`, and `return_idx/return_date`. Event/security identifiers are numeric `int32`; object-dtype DuckDB relations are rejected before registration.
- Determinism: relations are canonically sorted, DuckDB runs one worker with compensated `fsum`, output rows are ordered by `return_idx`, and `daily_portfolio_output_hash = SHA256(canonical_daily_csv_bytes)`; shuffled event/return input must preserve the same hash.
- Scope boundary: do not introduce physical repartitioning, chunking, Numba, or fold multiprocessing unless a future profile demonstrates a breached memory/latency bound and identifies it as the necessary lever.

# Request Artifact Identity Truth Reconciliation V1 (2026-07-11)

- Closure evidence: terminal reviewer-independence PASS is fixed at commit `e50219051df8bc8fc1f21312325f01cea4a8e18d`, reviewing envelope commit `c642a94944831adbd7ecc06fb16259c87fcdd213` and payload commit `a86c3a0fcc34d29e8d76cded5616c6cbe77f500e`.
- Byte boundary: the four request payloads and detached envelope are unchanged; this round updates governance truth only.
- Lifecycle boundary: `PREPARED_NOT_SENT`; no message is proven sent and dispatch remains denied.
- Authority boundary: identity closure does not authorize remotes, source/provider access, factual validation, readiness promotion, Gate D, publication, strategy/UI work, or data output.
- Formula impact: none; no quantitative formula, estimator, or runtime path changed.

# GV-FS0 Protocol V1 Canonical and Identity Formula Registry (2026-07-17)

Implementation paths: `core/gv_fs0_canonical.py`, `validation/gv_fs0_reconstruction.py`, `validation/gv_fs0_ci_reference_encoder.py`, `scripts/generate_gv_fs0_protocol_v1.py`, and `scripts/verify_gv_fs0_protocol_freeze.py`.

- Canonical document bytes: `canonical_json_text.encode("utf-8") + b"\n"`, with sorted Unicode scalar keys, exact string escapes, no extra whitespace, and exactly one terminal LF.
- Domain hash: `SHA256(domain_prefix.encode("utf-8") + b"\n" + canonical_json_document_bytes)`, emitted as lowercase 64-character hexadecimal.
- Price freshness: one unique positive price for the same security/session, `price_timestamp <= valuation_timestamp`, and `max_session_lag = 0`.
- Origin order key: `(source_sequence, source_intent_id, generated_event_slot)` within `(effective_timestamp_utc, session, event_type_rank)`; duplicate keys block with `DUPLICATE_ORIGIN_ORDER_KEY`.
- Manifest Git blob identity: `HASH("blob " + ascii(byte_length) + NUL + exact_file_bytes)` using the manifest-declared repository object format `sha1` or `sha256`.
- Terminal newline count: number of consecutive LF bytes at end of file; every frozen surface requires exactly `1`.
- Scope boundary: these formulas certify protocol bytes and identities only; they do not authorize economic reduction, certification execution, publication, or UI behavior.

# GV-FS0 Protocol V1 Freeze Audit Formula Registry Addendum (2026-07-17)

Additional implementation paths: `.github/workflows/gv-fs0-protocol-freeze.yml`, `tests/test_gv_fs0_freeze_immutability_v1.py`, and `scripts/verify_gv_fs0_protocol_freeze.py`.

- Hosted branch base selection: feature-branch push and PR bootstrap/enforced decisions must use the default branch or PR base, while only default-branch pushes may use the previous pushed SHA as the accepted base candidate.
- Windows protocol test expansion: hosted pytest file globs are expanded inside Python with `glob.glob("tests/test_gv_fs0_*.py")`, so Windows and Linux run the same focused protocol suite.
- Mutation acceptance formula: `freeze_candidate_accepted = deterministic_generation_pass AND independent_vectors_pass AND enforced_self_check_pass AND all_required_mutations_rejected AND restored_tree_equals_candidate_tree AND hosted_windows_linux_ci_pass`.
- Current value: true as of hosted run `29567754495`.

# GV-FS0 F1A OPEN Portfolio Economics and Certification (2026-07-18)

Implementation paths: `core/gv_fs0_book.py`, `core/gv_fs0_certify.py`, and `views/gv_fs0_portfolio_adapter.py`.
Focused tests: `tests/gv_fs0_product/test_open_vertical.py`.

- Execution cash delta: `-(shares * execution_price) = -(10 * 10) = -100`.
- Explicit fee cash delta: `-fee = -1`; post-entry residual cash is `1000 - 100 - 1 = 899`.
- Dividend receivable: `entitled_shares * amount_per_share = 10 * 0.5 = 5` on the ex-date.
- Dividend payment: atomically decreases receivables by `5` and increases cash by `5`, producing cash `904` and receivables `0`.
- Market value: `shares * session_close`; terminal value is `10 * 14 = 140`.
- NAV: `cash + market_value + receivables`; terminal NAV is `904 + 140 + 0 = 1044`.
- Session contribution: `current_NAV - previous_NAV`; canonical series is `0, 9, 15, 10, 10`.
- Cumulative contribution: `current_NAV - initial_cash`; terminal contribution is `44`.
- Certification: exactly two isolated verifier attempts must both reproduce the primary economic payload and hash; all ten tri-state checks must be TRUE before status may be CERTIFIED.
- F1A boundary: certified OPEN remains in memory and is injected into the final read-only adapter. No permanent two-component bundle or default dashboard route is authorized.


## 2026-07-22 — E0B C1 custody formulas

- IMPROVED: total_delta > 0 AND >=1 targeted delta > 0 AND every core-safety delta >= 0; else valid complete comparison is NOT_IMPROVED.
- One-shot artifact hash = domain_hash(ONESHOT_AUTH, {tag_object, case_id, attempt=1, candidate_commit, candidate_tree, preregistration_sha256}).
- GitHub receipt hash = domain_hash(GITHUB_RECEIPT, receipt body without receipt_hash); rubric_sha256 must equal SHA-256 of exact imported bytes.

## G08 Attempt-1 (2026-07-22)
- Banked IMPROVED observed comparison on tip fb4769d5…; observed_count=1; score 39 frozen.
- Product loop exercised: DecisionEnvelope NO_POSITION + certification bound to comparison hash.
- Residual: operational principal labels / same-process agent execution; GitHub receipt is operational separation only.
- Next: V2-B0 real block-only admission after this result-bearing commit hosted green.


## G08 Attempt-1 invalidation (2026-07-22)
- INVALID_REVIEWER_INDEPENDENCE_NOT_ESTABLISHED; observed authority 0; score 39; stage CERTIFIED_SINGLE_DECISION_OPERABLE.
- Sealed Attempt-1 evidence preserved; observation eligibility superseded by append-only invalidation.
- Receipts now require provider-authenticated GitHub author login (v2).

## GV Micro-Portfolio V0 integration checkpoint (2026-07-29)

- Base: exact remote-equal `b3d5092`; dirty root untouched.
- Local stream commits: S2 `92f587d`, S3 `3040a77`, S4 `1f11c0c`.
- Accounting: `PORTFOLIO_TRANSITION_PLANNED` is accepted as non-economic; fills remain fail-closed; reconciled V2 book exposes opening NAV 1500, execution cost 1, terminal NAV 1499, and unexplained residual 0.
- Strategy: canonical Living Thesis Lite has no persisted product-only `state`; decision snapshot owns reviews, cash outcome, competition, and selection.
- Execution: canonical chain is aim confirmation → transition planned → order created → fill completed, with immutable identifiers and lineage validation.
- Product: review/confirm/certify/persist/reopen/later-WATCH flow remains intact; render-time state is derived; persisted schema is `gv_portfolio_v0_workspace_v2`.
- Verification: portfolio 82/82 PASS; frozen protocol 150/150 PASS; legacy product 259/263 with four unrelated authority-document failures.
- Full suite: blocked at collection by incomplete declared environments (`alpaca`, `psycopg2`, `schedule`, `yaml` across available pinned venvs). No full-pinned PASS claim.
- Custody: terminal branch is pushed and local/remote-equal; independent audit remains open.
- Score: canonical shipped 39/100; observed 0; no alpha or live-capital claim.

## GV Operated Portfolio 10 replan checkpoint (2026-07-30)

- Base inspected: clean Challenger terminal worktree at `3e4dc957f475945169ddf33ed359254bd98dc64d`; dirty operator root untouched.
- Authority: created one canonical endgame record; reclassified Bounded/Scale/Universe/Challenger as substrates while preserving tags and restoring original frozen quantities.
- Product: exactly ten permanent identities, two clusters, unique evidence/theses, one portfolio book, four funded positions, classified cash, no-change observation, and one Harbor-to-Meridian transition.
- Accounting: SELL credits proceeds net of fees and reduces positions; oversized SELL is rejected; terminal NAV `4988`, total costs `12`, unexplained residual `0`.
- Replay: exact reconstruction, idempotence, certification lineage, and append-only non-economic correction execute successfully.
- Persistence: atomic content-addressed save/load equality verified after funded, no-change, transition, and correction stages.
- UI: `operated_portfolio_app.py` and `launch_operated_portfolio.py` provide review → confirm → no-change → transition → changed-why → reopen.
- Manual verification: changed modules compile; legacy Slice 0 still reaches `OBSERVED_WATCH_AIM_UNCHANGED` with NAV `1499`; full operated path reaches `5000 → 4992 → 4992 → 4988 → 4988`.
- Open: no repository `.venv`, pytest, or Streamlit AppTest environment found; full terminal regression, independent A/B/C, immutable commit/push/main/tag remain open.
- Score: accepted endgame progress remains `52/100` until terminal evidence passes.

## GV Operated Portfolio 10 acceptance-kernel repair (2026-07-31)

- Decision selection formula: `selected = sort(eligible candidates, -net_score_bps, instrument_id) where target_quantity > 0`; initial orders must equal this ordered set exactly.
- Transition delta formula: `delta_i = target_after_i - target_before_i`; `delta_i > 0 → BUY abs(delta_i)`, `delta_i < 0 → SELL abs(delta_i)`, `delta_i = 0 → no leg`.
- Projection rule: persisted `orders`, `fills`, `trade_authority_chains`, `observations`, and `changed_why` must equal deterministic reconstruction from canonical decision snapshots, events, and books.
- Certification rule: for each `CERTIFICATION_RECORDED` marker, replay the exact prior event prefix with the declared decision snapshot, aim, and prior complete certification object; byte inequality fails closed.
- Persistence rule: reject any symlink/junction in the lexical ancestor chain, resolve every existing ancestor, require canonical same-or-within-root before directory creation, temp write, replacement, and load.
- Schema changes: operated workspace `...transition_1r_v2`; persisted envelope `...persisted_v2`; no backward-compatibility adapter.
- Pinned narrow proof: `requirements-alpha.txt` provisions Windows Python 3.12.10 with pytest 9.0.2 and Streamlit 1.54.0; `pip check` PASS; operated/AppTest `15/15`; focused book/execution/replay/operated `70/70`; context/authority `33/33`; complete `gv_portfolio_v0` `145/145`; combined gate `178/178`.
- CI custody: `.github/workflows/gv-operated-portfolio.yml` runs the same narrow gate on `ubuntu-latest` and `windows-latest`, triggers on operated product/test/authority paths, validates generated context, and fails on tracked-byte drift.
- Root-lock boundary: `requirements.lock` is a stale monorepo-wide environment covering unrelated broker/data stacks and is not an acceptance gate for this product slice.

## GV Operated Portfolio 10 terminal closure (2026-08-01)

- Certified executable candidate: `0d15e9c59c6b3ca051b3aa815018889d1e94857f`; tree `4dc013e2b50da8c22456719f8fba75d7de0dfa41`.
- Transition formula remains `delta_i = target_after_i - target_before_i`; positive delta emits BUY, negative delta emits SELL of the absolute quantity, and zero delta emits no trade.
- Terminal accounting remains `NAV = classified_cash + Σ(position_quantity_i × deterministic_mark_i)`; terminal NAV is `4988`, explicit costs are `12`, and unexplained residual is `0`.
- Regression identity formula: `candidate_only = candidate_failset - base_failset`; terminal value is the empty set. Base failures `23`; candidate failures `19`; inherited `19`; fixed `4`; candidate-only `0`.
- Executable-byte identity formula: compare the complete Git tree entry set outside `docs/` between the certified executable candidate and the closure commit; terminal closure requires exact equality.
- Hosted proof: run `30640915560` passes exact-head clean-checkout jobs on Windows and Linux with the complete operated + FS0 package.
- Review proof: Reviewer A/B/C PASS against exact `0d15e9c`.
- Score: pre-terminal `52/100`; terminal accepted `62/100`.
- No runtime formula or implementation byte changes in the documentation-only closure commit. Limited Live remains closed.

## GV Operated Portfolio 25 pre-freeze checkpoint (2026-08-01)

- Scenario identity formula: `scenario_definition_hash = domain_hash("GV-OPERATED-SCENARIO:V1", canonical_scenario)`; the persisted envelope binds both `scenario_id` and this hash before workspace validation.
- Instrument identity formula remains content-derived from namespace, permanent key, and security class; exactly one candidate row per scenario instrument is required in every capital competition.
- Evidence ownership rule: each review must retain the initial evidence identity owned by its instrument; a reference to another instrument's owned evidence fails even when text is identical.
- Selection formula remains `selected = sort(eligible candidates, -net_score_bps, instrument_id) where target_quantity > 0`.
- Transition formula remains `delta_i = target_after_i - target_before_i`; positive delta emits BUY, negative delta emits SELL of absolute quantity, zero emits no leg.
- Workload acceptance: `required_actions = confirm + no_change + transition + correction <= 4`; per-security confirmations must equal zero.
- Fixture parameters: 25 identities, five clusters, eight initial positions, and current transition-leg count. Only exactly 25 identities and the semantic acceptance contract are phase authority.
- Local pre-freeze gate: 449 tests, 0 failures, 0 errors, 0 skips; receipts under `%TEMP%`; combined single-command attempts returning DevSpace HTTP 502 are not evidence.
- Candidate custody remains open until current bytes are attached to `codex/gv-operated-portfolio-25-1`; no score uplift or terminal claim.

## AOV-0 CIQ Security/Market Current-Cut Admission Tail (2026-08-07)

Implementation: `research/aov0/ciq_market.py`; builders: `scripts/aov0_build_ciq_market.py`, `scripts/aov0_fetch_nyfed_sofr.py`, `scripts/aov0_build_decision_cut.py`; tests: `tests/aov0/test_ciq_market.py`, `test_nyfed_sofr_intake.py`, `test_decision_cut_builder.py`.

- Identity admission: raw company entity ID is provenance only. A real source Capital IQ Security ID is normalized to `CIQSEC:<id>` and paired with the exact Trading/Instrument Item ID. If one entity has multiple rows without one unique explicit primary row, if identity is missing, or if Security/Trading IDs collide across entities, exclude all ambiguous names. Never repair via ticker, `SP_ENTITY_ID`, PERMNO, synthetic CIQSEC, yfinance, or local substitute returns.
- Coverage law: reuse current Rule100 v1 owner thresholds: `factor_present_count >= 3` for data admission and `hold_intact = (factor_present_count >= 3) AND (factor_positive_count >= 2)`. `<3` factor coverage excludes the entity; enough coverage but insufficient positives remains a valid market-universe row with zero Rule100 target if the technical/hold gate is false.
- Current-cut law: `run_4` does not prove historical PIT factors. Therefore historical CIQ market rows are admitted only as rolling-state warmup. The builder emits exactly one Rule100 target row and one matching risky-asset total-return row on the current decision target date; it never backcasts current factor states into historical Rule100 targets.
- Market history minimum: require at least 200 observations through the target date for every admitted name so SMA200 is real. Missing target-date row, short history, non-finite target total return/close/volume/ADV20/volatility/trend, non-positive ADV20/volatility, or missing vertical primitive excludes the name.
- Total-return authority: accept explicit decimal total return, Capital IQ `Total Return (%) / 100`, or daily `pct_change` of an exported total-return index. Adjusted/close price is technical/liquidity input only, never a second P&L path. For the frozen U.S.-listed universe, a target on the market-retrieval date requires retrieval at/after 16:00 America/New_York so the daily close/volume/return row is not admitted pre-close; a source retrieval timestamp later than the system-stamped build time blocks. The final decision-cut builder independently rechecks the same completed-bar rule.
- Technical formulas: `dollar_volume = close * volume`; `ADV20 = rolling_mean20(dollar_volume)`; `realized_vol = rolling_std20(total_return) * sqrt(252)`; `dist_sma20 = (close-SMA20)/SMA20`; `trend_veto = close < SMA200`; `trend_fast = sign(close-SMA20)`; `trend_slow = sign(close-SMA200)`.
- Rule100 v1 technical quality reuses existing runtime law: `hard_exit = trend_veto OR dist_sma20 > 0.20`; `proximity = clip(1 - max(dist_sma20,0)/0.05,0,1)`; `technical_quality = 1` when hold-intact and not hard-exit, otherwise proximity only when not vetoed. Current target sizing calls `softmax_v1_weights(rule100_config_from_max_weight(0.35))`; v1.1 continuous sizing remains research-only and is not substituted.
- Minimal AOV primitive freeze: on the target date only, `quality = clip(3*(2*(factor_positive_count/factor_present_count)-1),-3,3)` (monotone transform of the already-frozen group count, no second quality model) and `uncertainty = clip(1-factor_present_count/4,0,1)`. Pre-target market warmup rows carry `quality=0`, `uncertainty=1`, null factor counts, and no sizing eligibility so current factors are not backcast. Market-only primitives remain historical where observable: `exit_capacity = date-local percentile_rank(ADV20)` and `regime = date-local mean(trend_slow)`. `F_proxy/C_proxy` remain owned by `research/aov0/cube.py` and are not duplicated here.
- SOFR intake law: the production fetch function performs no network call before 15:00 America/New_York. After the gate it accepts only HTTPS responses whose final host is exactly `markets.newyorkfed.org`, hashes the raw response, and uses actual direct retrieval time as conservative `published_at`/information availability rather than inventing the provider publication instant.
- Decision-cut law: derive target date mechanically from equal maxima of current Rule100, total returns, and primitives; require the target-date Rule100/return/primitive security sets to match and primitive `total_return` to equal the P&L return matrix within `1e-15` absolute tolerance; knowledge cutoff is the max of all five source retrieval times, primitive `known_at`, and SOFR information time; bind exact four-Parquet hashes, frozen contract hash, recomputed universe hash, and exact receipts. The actual first-seal intake independently rechecks the target-return reconciliation. The old `run_2` receipt has no `retrieved_at`, so an explicit actual screen retrieval time is mandatory and file mtime is not promoted.
- Validation: AOV `59/59 PASS`; ZERO-COMPAT all seven counters zero; focused synthetic current-cut CIQ→SOFR→decision-cut package reaches the real `SEALED_NOT_OPENED` path and exact reopen with `financial_alpha_evidence=0`.
- Real-data status: no 109-name primary-security master or market-history export exists locally yet; no real `rule100_targets`, primitives, total returns, SOFR, decision cut, or prospective seal is claimed.

## AOV-0 `run_4.xlsx` Current-Cut Fundamental Slice (2026-08-07)

Implementation: `research/aov0/ciq_fundamentals.py`; builder: `scripts/aov0_build_ciq_fundamentals.py`; receipt: `data/aov0/source_receipts/ciq_quarterly_fundamentals_run_4_20260807.json`.

- Raw custody: `run_4.xlsx` SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`, 215,249 bytes; source entity set is exactly the frozen 109-company `run_2.xlsx` set.
- Quarter normalization law: use only absolute Capital IQ `FQqYYYY` references for the historical panel. Relative `FQ0/IQ_FQ` is excluded because it is as-of-relative and can disagree with the fixed-quarter cells in the same export. One entity (`SP_ENTITY_ID=4096690`, Gyrodyne) has only relative `FQ0` and no absolute-quarter history; retain the entity in current state with `factor_present_count=0`, `factor_positive_count=0`, and `NO_ABSOLUTE_QUARTER_HISTORY` rather than fabricating history.
- PIT law: `run_4.xlsx` does not embed a complete historical publication/filing timestamp for every quarter. Therefore each normalized row keeps its accounting `period_end` but receives `known_at = local raw-object admission time`; this is conservative current-cut admission only, not historical PIT replay proof.
- Identity law: `SP_ENTITY_ID` remains `TEMPORARY_COMPANY_ENTITY_NOT_SECURITY`; this slice never manufactures `CIQSEC:`, ticker identity, PERMNO, technical data, target weights, or returns.
- Quarterly formulas (same algebra as `data/fundamentals_compustat_loader.py` / `data/fundamentals_updater.py`): `invested_capital_q = equity_q + total_debt_q - cash_q` when positive; `ROIC = rolling4(operating_income_q) / rolling_mean4(invested_capital_q)`; `sales_growth_q = pct_change(total_revenue_q)`; `sales_accel_q = diff(sales_growth_q)`; `operating_margin_q = operating_income_q / total_revenue_q`; `operating_margin_delta_q = diff(operating_margin_q)`; `op_margin_accel_q = diff(operating_margin_delta_q)`; `delta_revenue_inventory = diff(total_revenue_q / inventory_q)` when inventory is positive; `bloat_q = diff(log(total_assets_q-inventory_q)) - diff(log(total_revenue_q))`; `net_investment_q = (abs(capex_q)-depreciation_q)/lag1(total_assets_q)`; `asset_growth_yoy = pct_change(total_assets_q,4)`; revenue YoY uses TTM `pct_change(4)` with quarter-level fallback.
- Factor algebra reuses `data/feature_specs.py` and the FeatureStore robust cross-sectional scale: `z_moat <- robust_scale(CS-z(ROIC))`; `z_demand <- robust_scale(CS-z(delta_revenue_inventory))`; inventory-quality raw = `CS-z(sales_accel_q) + CS-z(op_margin_accel_q) - CS-z(bloat_q) - 0.5*CS-z(net_investment_q)`, then robust-scaled; conditional discipline uses `-asset_growth_yoy*(1-sigmoid(operating_margin_delta_q/0.02))` with the existing positive inventory-quality waiver, then CS-z and robust-scale. `capital_cycle_score = 0.4*z_moat_raw + 0.4*z_discipline_cond_raw + 0.2*z_demand_raw`.
- Rule100 V1.1 count law: `factor_positive_count` counts approved groups, not raw columns: demand=`z_demand`; inventory/supply=`z_inventory_quality_proxy`; moat/pricing=`z_moat`; capital discipline=`capital_cycle_score` with `quality_composite` fallback. `z_discipline_cond` is an input to capital-cycle score, not the directly counted fourth group.
- Real output: 1,203 absolute entity-quarter rows; 109 current-state rows; 56 `COMPLETE_FACTOR_STATE`, 52 `PARTIAL_FACTOR_STATE`, 1 `NO_ABSOLUTE_QUARTER_HISTORY`. Factor coverage is intentionally reported rather than imputed away; `z_demand` is the sparse leg at 59/109.
- Boundary: this slice advances local Rule100 fundamentals only. `technical_quality`, canonical `CIQSEC:` universe, final Rule100 target weights, `vertical_primitives.parquet`, `total_returns.parquet`, SOFR cut binding, and the first seal still require the security/market-data leg.

## AOV-0 Capital IQ Authority Recut Formula / Identity Registry (2026-08-07)

Implementation paths: `research/aov0/contracts.py`, `cube.py`, `policy.py`, `experiment.py`, `scripts/aov0_first_seal.py`; source receipt `data/aov0/source_receipts/ciq_screen_run_2_20260807.json`.

- Trigger truth: WRDS login is not the blocker; the available account lacks CRSP entitlement. Active CRSP/PERMNO authority is therefore superseded rather than retried.
- Active executable schema: `aov0_ciq_executable_contract_v1`; contract hash domain is `AOV0:CIQ_EXECUTABLE_CONTRACT:V1` so the new family cannot be confused with the superseded AOV contract domain.
- Active security identity: `security_id = "CIQSEC:" + CapitalIQSecurityID`; `normalize_security_id` rejects empty, whitespace-bearing, unnamespaced IDs. Company `SP_ENTITY_ID`, ticker, and legacy PERMNO are not active identity aliases.
- Active risky-asset source family: screen universe=`SPCIQPRO:COMPANIES_SCREENER_RESULT`; Rule100 quarterly fundamentals=`SPCIQPRO:QUARTERLY_FUNDAMENTALS`; identity=`SPCIQPRO:PRIMARY_SECURITY_MASTER`; returns=`SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA`.
- Active risky-asset P&L authority: `SPCIQPRO_PRIMARY_SECURITY_TOTAL_RETURN_MATRIX_ONLY`; the target-weight and return matrices share canonical `CIQSEC:` column identities.
- Active decision-cut schema: `aov0_ciq_decision_cut_v1`; required source receipts are CIQ screen result + quarterly Rule100 fundamentals + primary-security master + primary-security market data + direct NY Fed SOFR. All prior input-hash, knowledge-cut, target-date, execution-bar, pre/post re-hash, and five current target-vector invariants remain unchanged.
- `run_2.xlsx`: SHA-256 `f610c43b336142b3366136fa71e1fbae82bf4eac301401ac9ef1d0c0ddbe3e0e`, 71,320 bytes, 109 screen candidates. It is candidate-screen evidence only because the export contains company `SP_ENTITY_ID`, not Capital IQ Security ID, lacks the PIT quarterly factors needed to derive canonical Rule100 V1 `factor_positive_count`, and has no primary-security history to derive `technical_quality`/total returns.
- Canonical Rule100 V1 candidate scoring is not the three-year revenue screen: runtime requires `factor_positive_count` and `technical_quality`. Current `factor_positive_count` reuses the approved four-group state: demand=`z_demand`, inventory/supply=`z_inventory_quality_proxy`, moat/pricing=`z_moat`, capital discipline=`capital_cycle_score` with `quality_composite` fallback; `z_discipline_cond` feeds capital-cycle score but is not itself the directly counted fourth group. Current technical quality is derived from the same-cut market path (`dist_sma20`, `trend_veto`, plus hold-intact state). Do not hand-enter either Rule100 score.
- Economic cash remains `annual_rate = SOFR_percent / 100 - 0.0025`; interval return `= annual_rate * calendar_days / 360`; direct NY Fed only; same after-15:00-ET retrieval gate.
- No compatibility bridge: historical PERMNO-specific replay adapter may remain as component/audit code, but active AOV first-seal code does not accept PERMNO.

## PIT Alpha Authority Cut publication (2026-08-06)

- Tip: `9af5259`; tag: `pit-alpha-authority-cut-1-terminal`; remote main equality verified.
- Score: terminal accepted operability/custody/replay maturity `70/100`; prior construction held `62/100` until publication.
- Active gate after publication: `PIT-SOURCE-AUTHORITY-1` on branch `codex/pit-source-authority-1`.
- Non-claims: alpha, source quality, realized value, broker, live readiness remain closed.

## AOV-0 Full Local Hard Cut + Vertical Formula Registry (2026-08-06)

Implementation paths: `research/aov0/contracts.py`, `cube.py`, `policy.py`, `dag.py`, `cash.py`, `experiment.py`, `review.py`; research hardening in `research/backtest_runner.py`, `benchmarks.py`, `evidence_schema.py`, `strategy_cartridge.py`, and `research/adapters/rule100_replay_adapter.py`.

- Local immutable Episode-2 candidate: `39f7be3894623c095994066b8f0ea2895b968643`; exact archived selected matrix `115/115 PASS`; old `142/142` count superseded.
- AOV local executable lineage before docs closure: `39f7be3 → 4b14846015c952242d4bf17819bc615435bda091 → dca69fc72dd3192913aa921323ff48f68610a925`.
- Capital-pressure proxy: `F_proxy = robust_z(sign(total_return) * min(abs(total_return) / realized_vol, 3) * dollar_volume / adv20)`.
- Crowding proxy: `C_proxy = EWMA20(abs(F_proxy))`; no second ADV division.
- Parent policy: preserve Rule100 date-local eligibility, risky gross budget, target-change schedule, single-name cap, and residual cash; state deltas redistribute only inside that budget.
- Child policy: `child_weight_i,t <= parent_weight_i,t`; the one frozen reversal-insurance mutation may only reduce risky exposure and increase residual cash.
- Economic cash: `annual_rate = SOFR_percent / 100 - 0.0025`; interval return `= annual_rate * calendar_days / 360`; no zero floor. Authority is direct Federal Reserve Bank of New York SOFR, retrieved after 15:00 America/New_York with actual retrieval timestamp and raw-object SHA-256; WRDS mirrors/proxies are invalid.
- Research identity: frame/evidence signatures include actual cell bytes/content rather than shape/date metadata only; final `evidence_manifest.json` hashes every component and the run directory is immutable.
- Benchmark contract: required named arms are implicit cash, PIT equal-weight eligible universe, and economic cash; headline primary benchmark is explicit; PIT-EW changes only when the strategy target schedule changes and forward-fills otherwise.
- Rule100 adapter: `permno` mandatory; `daily_portfolio` mandatory; ticker/asset fallback forbidden; replay residual cash must equal `1 - sum(risky_target_weights)` within tolerance.
- Review reconciliation: `net_delta = gross_delta - cost_delta`; max absolute residual must be `<= 1e-12`; otherwise status `ACCOUNTING_FAILURE` and no review authority.
- Insurance endpoint: Expected Shortfall/CVaR with frozen level `0.95`; production AOV-0 V0 freezes materiality floor `0.05` and annual premium ceiling `0.0015` (15 bp/year expected net-return sacrifice). Changing either creates a new contract/model family; no result-driven calibration in place.
- First real seal input contract: `data/aov0/current/{rule100_targets.parquet,vertical_primitives.parquet,total_returns.parquet,official_sofr.parquet,decision_cut.json}`. Owner methodology is closed; current status is fail-closed on data admission only with `prospective_clock_started=false` and `financial_alpha_evidence=0`.
- Decision-cut binding: `decision_cut.json` schema `aov0_decision_cut_v1` binds `SHA256(rule100_targets)`, `SHA256(vertical_primitives)`, `SHA256(total_returns)`, `SHA256(official_sofr)`, frozen `contract_hash`, mechanically recomputed date-local `universe_hash`, source receipts/retrieval times/raw-object hashes for `crsp.dsf`, `crsp.stocknames`, `comp.fundq`, `crsp.ccmxpf_linktable`, and direct NY Fed SOFR, plus `knowledge_cutoff`, `decision_target_date`, `sealed_at`, and `first_eligible_execution_bar`. NY Fed receipt time must be at/after 15:00 America/New_York. The four Parquets are re-hashed before and after experiment execution.
- Cut-time admission law: `max(rule100_date) = max(total_return_date) = max(primitive_date) = decision_target_date`; no Rule100/return/primitive history may exceed that target date; `primitive.known_at <= knowledge_cutoff`; `official_sofr.published_at <= knowledge_cutoff`; `official_sofr.effective_date <= decision_target_date`; `first_eligible_execution_bar > sealed_at >= knowledge_cutoff` and its normalized date is strictly after `decision_target_date`.
- Current-target binding: for each real seal, store a content hash of the current decision target vector for Rule100, Parent, Child, PIT equal weight, and economic cash in addition to whole-history DAG node hashes.
- ZERO-COMPAT gate: root duplicate apps, AOV ticker/asset aliases, legacy book projection, transitional authority fallback, mutable evidence-manifest bypass, unnamed benchmark selection, and archived/release executable-source imports outside the historical receipt-integrity test must all equal zero.


