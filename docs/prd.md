# Active PRD Cutover — All-Capital PIT Dashboard

Active product authority: 2026-08-03. Final planning round frozen.

Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`. Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`. Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`. Accepted score remains `62/100`; Limited Live remains closed.

The immediate product slice is a real read-only all-proposal PIT transaction: one certified five-field identity, verified MU-operated/MU-shadow/book-cash adapters, immutable typed proposals, command-handler identity acceptance, ordered digest-chained governance events, deterministic read projections, and the six-page Command Center through `dashboard.py`. Slice 1 contains no selection, optimizer/risk math, preview, authorization, book mutation, certification change, or deletion. MU is the first real case, not the pipeline model. Historical material below is retained but does not compete with this authority.

Research exception, 2026-08-04: `GV-FINANCIAL-CASCADE-SHADOW-0` adds an isolated, non-authoritative Leningrad bundle adapter and same-engine gross-exposure-cap challenger. It does not alter the active dashboard gate, `RegimeManager`, stock selection, entry/exit logic, certified portfolio state, or live capital. Promotion requires two distinct PIT stress windows and the frozen drawdown, expected-shortfall, alpha-drag, turnover, and replay checks in `docs/phase_brief/gv-financial-cascade-shadow-0-brief.md`; no real promotion evidence or score uplift currently exists.

---

V2 PEAD Alpha Interpretation Gate Notice (2026-06-24)

- The top-level PEAD next step is now a docs-only Alpha Interpretation Gate before any dashboard expansion.
- The current full-universe M1B result is descriptive methodology evidence only: not alpha, not tradable, not PIT, not net performance, and not strategy-promotion authority.
- Path A after gate approval is a descriptive evidence panel with hard disclaimers; Path B is an M5 PIT/data/method upgrade before any real alpha assertion.
- No alpha-named dashboard/code is authorized until gate approval and 28-commit/main reconciliation.

V2 PEAD M4A Memory-Bounded Full-Universe Expansion Notice (2026-06-22)

- M4A implements bounded-memory local full-universe build paths for D2A security-level returns and D2B fixed event-security windows.
- D2A --build uses DuckDB bounded execution, disk spill, one thread, and row-grouped Parquet instead of materializing full source/output pandas frames; D2A --sample remains unchanged.
- D2B --build resolves manifest-governed D1/D2A inputs, lazily validates full D2A, preserves deterministic fixed-security selection, and writes the full +1..+60 event-window output through bounded SQL and atomic publication.
- Formula and selection semantics are unchanged: D2A lags remain within (gvkey, iid), and D2B keeps prior-20-session liquidity, minimum 15 finite observations, deterministic score/count/IID/security ordering, and one fixed security per event.
- Evidence: focused M4A tests pass 55/55 and broader PEAD D2/D3/event-study tests pass 79/79.
- Terminal closure is blocked until Reviewer A/B/C capacity returns and full repository pytest returns a clean exit code.
- This notice does not authorize providers, PIT/full-universe alpha claims, estimator/UI changes, ranking/scoring, alerts, recommendations, broker/order paths, or new data artifact publication.

V2 PEAD Calendar-Time Inference M1B Notice (2026-06-21)

- Calendar-time M1B is implemented as bounded numbers-only methodology evidence at `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`.
- Artifact SHA256 is `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`; the protected 20260620 validation JSON remains SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- The method uses signal-only event-date quintiles, all-quantile latest-event overlap resolution, Q5-minus-Q1 equal-weight raw returns, D3 `mktrf`, and HAC(59).
- Evidence records 19,812 null-date rows excluded, 226,772 expected extreme rows, 1,519 missing rows, and 2,539 retained sessions.
- M1B rejects off-spine D2B dates and noncanonical output targets; zero-retained-session results use explicit null dates and null inference rather than invalid date placeholders.
- No alpha claim, strategy promotion, rank/score, alert, recommendation, broker/order path, PIT/full-universe claim, or dashboard action state is authorized.

V2 PEAD Read-Only Evidence Dashboard Notice (2026-06-20)

- Strategy Research Replay now exposes the locked PEAD validation JSON as a compact read-only evidence dashboard.
- The panel verifies SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e` and fails closed on missing, changed, or incomplete evidence.
- It displays only lineage/status, approved counts, HAC-null/descriptive-only warnings, and stated limitations.
- It adds no alpha claim, strategy promotion, ranking/scoring, alerts, recommendations, broker/order path, provider access, Parquet read, recomputation, or data mutation.

V2 PEAD D3 Benchmark Artifact Publication Notice (2026-06-20)

- D3 benchmark input is now published for the repaired 2,810-session D2B spine.
- Published Parquet: `data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`.
- Manifest pointer: `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`.
- Evidence: 2,810 rows, 2015-01-02 through 2026-03-06, complete 2,810 / 2,810 D2B coverage, zero missing sessions, formula `benchmark_return = mktrf + rf`, SHA256 `f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`.
- CAR/BHAR interpretation, quintiles, dashboard integration, ranking/scoring, alerts, broker/order paths, full build, staging, and commit remain blocked pending separate approval.

V2 PEAD D2B Market-Session Spine Repair Notice (2026-06-19)

- D2B now uses the source-backed Ken French daily date set as the authoritative market-session spine instead of all distinct D2A dates.
- The repaired spine contains 2,810 sessions and excludes 52 market-closed D2A dates.
- Fixed event-security selection semantics remain unchanged; the corrected artifact has 12,582 events, 754,920 rows, 11,450 eligible handoffs, and SHA256 `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`.
- The active strategy handoff validates D2A in bounded chunks and completes 687,000 strategy rows without full-frame normalization.
- D3 in-memory coverage is complete, but no D3 artifact or CAR/BHAR interpretation is authorized by this repair.

V2 PEAD D3 Benchmark Artifact Builder Notice (2026-06-19)

- D3 has an executable Ken French benchmark builder and focused tests, but artifact publication remains unperformed pending separate approval.
- The builder captures official source release/hash metadata, converts percent returns to decimals, and enforces `benchmark_return = mktrf + rf`.
- The historical pre-repair build stopped on 52 non-session dates; the active repaired D2B spine now validates 2,810 / 2,810 benchmark rows in memory.
- A narrow strategy-summary repair preserves raw cumulative asset return for complete asset windows when only benchmark coverage is missing; CAR/BHAR, eligibility, and interpretation remain blocked.
- Do not fill, drop, interpolate, zero, substitute, or splice missing benchmark dates. The next action is a separate bounded D3 artifact publication decision.

V2 PEAD D2B Fixed Event-Security Window Notice (2026-06-19)

- The bounded D2B Data slice is DONE: one deterministic event-level security, exact global `+1..+60` session skeleton, missingness retained, and immutable hash-addressed publication behind an atomic manifest pointer.
- Current evidence is 12,582 events, 362 issuers, 754,920 rows, 12,568 selected events, 14 no-security events, 522 short windows, 7,179 missing/non-finite windows, 4,867 eligible handoffs, and SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`.
- The strategy smoke uses only eligible events, unique canonical D2A return keys, and the identical global session spine; it produced 292,020 complete windows without a second D2B window algorithm.
- Final Reviewer A/B recheck remains pending. D2B completion is not PEAD phase-end and does not authorize provider, benchmark, CAR/alpha, dashboard, ranking, alert, broker, full-build, staging, or commit work.

G7.1A Canonical Notice (2026-05-09)

The current product canon is the root-level `PRD.md` and `PRODUCT_SPEC.md`.

V2 PEAD D2A Security-Level Return Notice (2026-06-18)

- D2A preserves `(gvkey, iid)` continuity and exposes canonical `security_id`, `date`, and `total_return` rows.
- The required total-return level is `prccd * trfd / ajexdi`; fallback uses same-security split-adjusted price returns only.
- Cross-IID lags, duplicate `(security_id,date)` rows, non-atomic output, and the old `trfd_t / trfd_{t-1} - 1` methodology are forbidden.
- The active manifest atomically points to an immutable hash-named Parquet; downstream readers must resolve that pointer.
- Only the 500-GVKEY sample is in scope. D2B, full build, benchmark, strategy interpretation, and UI remain downstream.

V2 PEAD D1 Repair Notice (2026-06-18)

- D1 is repaired and rebuilt using raw numeric `epspxq`, exact t-4 continuity, and `(gvkey, rdq)` deduplication before stateful lag/rolling work.
- Raw SUE is retained beside RDQ cross-sectional `+/-5` standard-deviation clipping. The liquidity rule uses `cshoq_lag1` in millions and is a flag only.
- The atomic Parquet/manifest pair records 346,511 rows, 233,586 valid SUE rows, 13,216 GVKEYs, and SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Manifest quality metrics record raw `abs(SUE) > 5` at 0.1888% of valid rows, below the 0.5% fail-closed threshold, and record that current-vintage Compustat EPS may include restatement hindsight.
- Empty processed-output paths preserve the existing Parquet/manifest bundle.
- The next action is a separate D2 repair beginning with returns computed by `gvkey+iid` before any daily ADV selection.

V2 PEAD Strategy Contract Notice (2026-06-18)

- The canonical product surfaces now permit a strategy-only, in-memory PEAD contract for schema validation, strict `+1..+60` event windows, complete-window return outcomes, cohort quintiles, and HAC spread statistics.
- Reviewer A/B/C rerun has passed, so the strategy skeleton is handoff-ready for corrected D1/D2 inputs only.
- Data-layer repair, real artifact builds, and alpha interpretation remain blocked and owned by the Data stream.

V2-D0.4C Local Read-Only Permission Probe Approval Notice (2026-06-03)

- Root-level `PRD.md` and `PRODUCT_SPEC.md` now record D0.4C as docs-only approval for one future local human permission probe.
- Exact future probe rows are `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`.
- D0.4C itself executes no WRDS login, no provider action, and no data output.
- All approval refs remain null and formal permission truth remains not closed.
- D0.4D is queued as the first local human execution packet.

V2-D0.4B WRDS Local Auth Method Confirmed Notice (2026-06-03)

- Root-level `PRD.md` and `PRODUCT_SPEC.md` now record V2-D0.4B as the latest PM stance.
- Required correction: `WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed.`
- Artifacts exist at `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.md` and `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.json`.
- Local auth method is user-attested available; actual login is not agent-verified; formal approval_ref remains null; permission truth remains not closed.
- Rows `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus` are probe_plan_pending, not_approved, and approval_ref null.
- Only plan-only local read-only permission probe outline language is allowed; probe execution needs separate approval.
- No secret.txt/credential read or use, WRDS/provider execution, schema discovery, row counts, sample rows, snapshots, data output, runtime/trading, approval_ref fabrication, or row approval is granted.

V2-D0.2 WRDS Entitlement Evidence Request Notice (2026-06-03)

- Root-level `PRD.md` and `PRODUCT_SPEC.md` now record the V2-D0.2 evidence request as request-only, not approval.
- Request artifacts exist at `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.md` and `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.json`.
- The copyable request asks an institutional data librarian, WRDS representative, PI, license owner, or data administrator for dated attributable non-secret table-level entitlement evidence.
- Exact rows remain `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`.
- All five rows remain evidence_missing/pending with approval_ref null.
- No credential, provider, probe, schema/table discovery, row count, snapshot, data-output, runtime, trading, cleanup, secret-remediation, SafeBoot, or BootReady authority is granted.

V2-D0.1 Authorization Intent Evidence Missing Notice (2026-06-03)

- Root-level `PRD.md` and `PRODUCT_SPEC.md` now record V2-D0.1 authorization intent as intent-only, not final approval.
- All five V2-D0.1 rows remain evidence_missing/pending with approval_ref null.
- `secret.txt` is local secret material and is not non-secret entitlement evidence.
- `TODO-ENTITLEMENT-001` and `TODO-APPROVAL-001` remain pending/blocking.
- No provider/probe/snapshot/data-write/runtime/trading/cleanup/secret-remediation authority is granted.

V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping Notice (2026-06-02)

- `TODO-MATRIX-001` is resolved for offline permission-truth metadata via `v2_discovery/data_lab/permission_truth.py`.
- Focused evidence: V2 permission-truth/matrix/snapshot/no-write suite PASS, 51 passed; compileall `v2_discovery\data_lab` plus permission-truth test PASS.
- Exact five V2-D0.1 rows default `pending`; row approval requires row/table `approval_ref`; approved `allowed_uses` is strictly `["provenance_contract"]`.
- PEAD_V2_001 starter remains separate; `ibes.det_epsus` is `pending` for V2-D0.1 and `not_requested` for PEAD starter.
- Entitlement evidence, explicit approval text, clean-room/proof packet, legacy WRDS cleanup, validity/C3 lock, and public/main mismatch remain pending or blocked.
- No WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, or legacy cleanup is authorized.

V2-D0.1 Scope and Clean-Room Runtime Decision Notice (2026-06-02)

- V2-D0.1 requests all five entitlement rows; PEAD_V2_001 starter uses only the four-row Compustat PEAD set.
- `ibes.det_epsus` is `pending` for V2-D0.1 once requested and `not_requested` for PEAD_V2_001 starter.
- `schema_registry.py` is excluded from credentialed clean-room runtime by default.
- `TODO-PEAD-DECISION-001` and `TODO-CLEANROOM-RUNTIME-001` are resolved.
- Remaining gaps are entitlement evidence, approval text, full clean-room proof packet, V2-D0.1 matrix metadata/builder, legacy WRDS cleanup authority, V2 validity packet/C3 lock, and public-main status.
- No provider/probe/snapshot/data-write/runtime/trading/cleanup authority is granted.

V2-D0.1 Expert 1-6 Follow-Up Reconciliation Notice (2026-06-02)

- Root-level `PRD.md` and `PRODUCT_SPEC.md` now record the Expert 1-6 follow-up agreement/confidence matrix.
- V2-D0.1 is still entitlement-only and now has a five-row target: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus`.
- Quant Research is partial agreement because the first PEAD primary signal is unresolved: I/B/E/S analyst surprise vs Compustat-rdq starter.
- TODO gaps remain entitlement evidence, approval text, PEAD starter decision, clean-room probe surface, legacy WRDS triage/cleanup authority, V2 alpha validity packet/C3 lock, public-main status, and V2-D0.1 permission-matrix narrowing.
- No provider/probe/snapshot/data-write/runtime/trading/cleanup authority is granted.

V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates Notice (2026-06-02)

- Expert 1-6 agreement is recorded as high-confidence TODO gates; missing numeric rating source values are not inferred.
- V2-D0.1 is entitlement-only and may collect non-secret WRDS entitlement evidence plus explicit approval text only.
- Backend/Data row-level validator is `PATCH_RESOLVED` after tests.
- Security approval text and legacy WRDS helper/quarantine risk remain open gates.
- `PEAD_V2_001_BOUNDARY_PACKET` is conditional only after WRDS/PIT authority.
- No V2 alpha is currently `research_valid`; `V2_ALPHA_VALIDITY_PACKET` template is needed.
- No WRDS/provider access, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, or BootReady is authorized.

V2-D0 Multi-Expert Reconciliation Gate Notice (2026-06-02)

- Expert A/B/C reconciliation accepts V2-D0 as offline contract substrate after Backend PATCH hardening.
- Expert A says probe authorization needs user/source WRDS entitlement evidence first.
- Expert C keeps dashboard reader HOLD and G9 context-only.
- Expert B PATCH is fixed through stricter probe contract validation and snapshot storage schema parity.
- Next stream is permission-truth authorization only, not a WRDS probe.

V2-D0 WRDS Permission + Snapshot Provenance Contract Notice (2026-06-01)

- V2-D0 is the approved active main stream after G9 is held as context-only and dashboard reader remains HOLD.
- The delivered shape is offline contract code in `v2_discovery/data_lab/`, JSON Schema contracts in `contracts/data_snapshot/`, and focused pytest guardrails.
- It records WRDS permission truth and planned PIT provenance only; it does not run WRDS probes, generate snapshots, write outputs, mutate V1 canonical data, or change dashboard runtime.
- No ranking, scoring, recommendation, alert, broker/order path, SQLite store, SafeBoot, or BootReady claim is authorized.
- Immediate next action: approve exact WRDS account/library/table permission truth before any read-only probe.

V2 Alpha Factory Immediate Todo Directive Notice (2026-06-01)

- Root-level `PRD.md` and `PRODUCT_SPEC.md` now record the immediate TODO-first directive as idea/directive intake, not an implementation decision.
- Immediate TODO-first order is WRDS Permission + PIT Snapshot + Provenance Layer; PEAD Variant Factory; Corporate Actions / Capital Return Edge Lab; Meta-labeling / Edge Survival Model; Orbis/BvD Private Company Network Edge.
- LLM market-news agents, DRL allocator work, and live routing remain deferred/blocked.
- No provider access, snapshot generation, SQLite storage, candidate ranking/scoring, promotion, live trading, broker behavior, alerts, recommendations, autonomous allocation, or BootReady claim is authorized.
- Immediate next action: `prepare_wrds_permission_pit_provenance_planning_scope_or_hold`.

Boot Status Path Contract + Governance Scanner Integration Notice (2026-05-26)

- The canonical machine-readable boot verdict is `runtime/boot_status_current.json`.
- `docs/context/boot_status_current.json` is a noncanonical context snapshot path only; runtime safe-boot readers and writers must not fall back to it.
- `scripts/boot_preflight.py` runs Governance Gate v0 through `scripts.governance_preflight.run_governance_preflight(...)`; governance FAIL blocks preflight.
- Data-readiness, dashboard runtime smoke, replay/optimizer certification, and clean GitHub safe-boot proof remain separate gates before any boot-ready claim.
- This does not authorize provider ingestion, canonical market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Research Validity Runner v0 Notice (2026-05-26)

- Terminal Zero now has a mechanical research-validity contract: `No cartridge + no canonical engine run + no PIT proof + no benchmark + no costs + no evidence packet = not research-valid`.
- The first implementation adds a top-level `research/` package and keeps `core.engine.run_simulation(...)` as the official PnL/cost/turnover primitive.
- Research evidence output is path-confined and atomic: unsafe `run_id` values are rejected, artifact files are promoted by temp-to-replace, and the final packet manifest is written last.
- Rule100 replay can be adapted into runner target weights, but it remains `diagnostic_only` by default and is not promoted as validated alpha.
- This does not authorize provider ingestion, canonical market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Portfolio Replay Role Contract Notice (2026-05-15)

- Portfolio & Allocation replay rows must expose explicit `context_role` semantics so current holdings, historical context rows, flat replay exposure, cash, and unavailable rows cannot be confused.
- Replay-facing labels must avoid generic `Weight` when the value means selected-method replay exposure; use role-aware labels such as `Replay Weight`, `Current Weight`, `Replay Target`, and `Aux Audit Wt`.
- Lifecycle/event/decision `weight` remains audit intent only; selected-method `target_weight` remains replay exposure truth.
- Diagnostics for closed trades, zero-exposure BUY rows, hold time, exit reason quality, and reason concentration must come from the rendered replay context, not a second replay.
- This does not authorize provider ingestion, canonical writes, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Dashboard Replay Aux Weight Semantics + Stacked Timeline Notice (2026-05-15)

- Portfolio & Allocation replay-facing event/decision surfaces display replay `target_weight` as their primary weight.
- Legacy aux weights are retained only as audit metadata and must not override the daily replay target-weight truth.
- Strategy Replay Timeline is a stacked step-area allocation view over replay target weights.
- Partial saved/transitional schemas render empty/unavailable states rather than crashing replay-facing Portfolio surfaces.
- This does not authorize provider ingestion, canonical writes, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Replay Selected Price Loading + MU/SNDK Eligibility Trace Notice (2026-05-15)

- Dashboard replay optimization keeps full `r3000_pit` membership proof and only limits the loaded price/return matrix to selected replay permnos after that proof exists.
- MU/SNDK analysis is a separate strategy/data eligibility trace, not a replay-universe shortcut.
- Current trace through 2026-05-11: MU and SNDK are pinned, mapped, latest-date PIT-present, and locally priced; MU latest fails `technical quality`, SNDK latest fails `factor threshold` and has no Rule100 history rows.
- This does not authorize watchlist-only replay, provider ingestion, canonical writes, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Max Replay Timeline Sampling Fix Notice (2026-05-15)

- Strategy Replay Timeline max-window sampling normalizes weekly grouped dates with the pandas Series `.dt` accessor.
- Weekly display sampling is still derived only from daily replay rows and cannot become a Portfolio Performance source.
- This does not authorize provider ingestion, canonical market-data writes, recommendations, alerts, broker behavior, ranking, scoring, or strategy promotion.

Portfolio Single-Source Replay Page Notice (2026-05-14)

- Portfolio & Allocation is replay-source-first for allocation evidence, performance, timeline, events, latest buys/sells, and decision logs.
- The top allocation display is the latest daily replay snapshot for the selected method/window.
- Portfolio Performance refuses sampled replay and optimizer fallback; unavailable daily replay shows unavailable rather than mixing sources.
- Timeline sampling is only a visualization transform over daily replay rows.
- Latest Buys/Sells is derived from the same Buy/Sell Decision Log rows, not a separate trade tape.
- This does not authorize provider ingestion, canonical market-data writes, recommendations, alerts, broker behavior, ranking, scoring, or promotion claims.

Backend Replay Reader Identity Hardening Notice (2026-05-14)

- Saved selected-method replay manifests require non-empty `run_id`, `source_id`, and `method_id`.
- Blank manifest identity fails closed before optional expected IDs or parquet/manifest equality can validate the artifact.
- This is backend reader hardening only; it does not authorize provider ingestion, canonical market-data writes, recommendations, alerts, broker behavior, ranking, or scoring.

Saved Artifact Single-Source Aux Surface Fix Notice (2026-05-14)

- Portfolio & Allocation saved-artifact mode preserves artifact event and decision rows exactly, including empty frames.
- Empty saved-artifact aux surfaces must not be backfilled from separately loaded dashboard fallback frames while the context is labeled `source_mode="saved_artifact"`.
- This keeps replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell rows single-source under the saved artifact label.
- This does not authorize provider ingestion, canonical market-data writes, recommendations, alerts, broker behavior, ranking, or scoring.

Portfolio Market-Data Freshness Endpoint Cache Notice (2026-05-14)

- Portfolio & Allocation computes endpoint freshness once per loaded local price matrix signature, then reuses per-column endpoints downstream.
- The endpoint cache preserves the fail-closed freshness contract; it is not a relaxation of stale-data handling.
- Dashboard YTD, optimizer selected-price prep/default ordering, and optimizer universe eligibility consume the shared endpoint snapshot instead of rescanning full `prices_wide`.
- Actual local measurement on `(2857, 2000)` prices: snapshot `0.2966s`, legacy loop `0.9555s`, endpoint maps matched, downstream lookups were near-zero.
- This does not authorize provider ingestion, canonical market-data writes, recommendations, alerts, broker behavior, ranking, or scoring.

Portfolio Market-Data Freshness Fail-Closed Notice (2026-05-14)

- Portfolio & Allocation treats local/live price freshness per asset, not as one shared matrix date.
- Endpoint freshness semantics are centralized in `core.data_orchestrator`; universe eligibility passes tolerance explicitly through policy.
- Benchmark YTD, portfolio YTD, optimizer selected-price prep, optimizer default ordering, and optimizer universe eligibility must fail closed on stale ragged columns.
- Weighted portfolio YTD does not compute a partial portfolio when a weighted leg is stale at the required endpoint.
- Stale selected optimizer assets that cannot be refreshed are dropped/excluded with explicit diagnostics; selected live overlay requires same-column local/live overlap and cannot scale first live to last stale local as allocation evidence.
- This does not authorize provider ingestion, canonical market-data writes, recommendations, alerts, broker behavior, ranking, or scoring.

Dashboard Backend Bundle Integration Verification Notice (2026-05-14)

- Dashboard Strategy Replay consumes `build_selected_method_replay(...)` through `DashboardReplayContext`.
- The dashboard replay input loader remains PIT-safe with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- The verified path is a transitional build path; saved replay artifact-reader consumption is still future work.
- Full pytest and runtime smoke passed; this does not authorize provider ingestion, live trading, broker behavior, alerts, ranking, scoring, recommendations, or strategy promotion.

Replay Coverage Contract Audit Fix Notice (2026-05-14)

- Selected-method replay coverage must stay explainable: metadata records coverage segments and unavailable rows keep concrete `input_unavailable:*` reasons.
- Daily all-uncovered replay routing, including row-heavy `no_priced_members` windows, must be fast enough for audit use without calling the optimizer or loader.
- Replay performance must avoid same-date lookahead by applying allocation-date weights to the next tradable return.
- Context bootstrap must prefer the latest complete current-truth New Context Packet over older same-phase handovers.
- This is a reliability/performance fix only; it does not authorize provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, or promotion claims.

Data/PIT Strategy Replay Hardening Notice (2026-05-13)

- Strategy Replay cache signatures and input loaders require `r3000_pit` universe membership.
- Dashboard Strategy Replay consumes per-date `StrategyReplayInputs` before generating target weights.
- Display-only replay artifacts stay under `data/runtime_cache/strategy_replay`.
- No provider ingestion, canonical market-data write, alert, broker, ranking, scoring, or live trading is authorized.

Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay Notice (2026-05-13)

- Rule of 100 visible allocation uses `controls.max_weight` as both per-name budget and cap for direct UI and Strategy Replay.
- Frozen Rule100 history/audit artifacts are not rewritten into 35% policy artifacts.
- Benchmark YTD keeps good local data and live-overlays stale/missing tickers one ticker at a time, so stale QQQ does not remain flat merely because SPY is fresh.
- This does not authorize canonical provider ingestion, market-data writes, recommendations, alerts, broker behavior, ranking, or scoring.

This historical PRD remains for continuity, but G7.1A supersedes the old product framing:

- Product: Unified Opportunity Engine.
- Primary user: discretionary supercycle investor/operator.
- Primary job: find MU/SNDK-style de-risked asymmetric upside.
- Secondary job: read market behavior through GodView signals: IV, options whales, gamma, short squeeze, CTA/systematic pressure, sector rotation, ETF/passive flows, dark-pool/block activity, ownership whales, microstructure, catalysts, and regime.
- Output layer: dashboard states and paper-only prompts: wait, watch, accumulation, confirmation, buying range, let winner run, trim optional, exit risk, thesis broken.
- Boundary: the system is not a trading bot and G7.1A adds no search, candidate generation, backtest, replay, proxy run, options ingestion, ranking, alert, broker, provider, or dashboard-runtime implementation.
- Immediate next action: `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`.

G8 Candidate-Card Notice (2026-05-10)

- G8 creates exactly one human-nominated Supercycle Gem Candidate Card for `MU`.
- The card is a structured research object, not an investment recommendation.
- It records thesis placeholder, source-quality labels, missing evidence, thesis breakers, provider gaps, and forbidden state transitions.
- It does not produce an alpha score, ranking, buying range, alert, trade, promotion packet, backtest, replay, provider ingestion, dashboard runtime behavior, or broker action.
- Immediate next action: `approve_g9_one_market_behavior_signal_card_or_hold`.

G8.1 Discovery-Intake Notice (2026-05-10)

- G8.1 creates a controlled supercycle discovery intake layer.
- It seeds exactly six intake names: `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`.
- `MU` remains the only full candidate card; all other seed names are intake-only.
- Intake items record themes, why they might belong, evidence needed, source leads, official sources needed, relevant market-behavior modules, thesis breakers, and provider gaps.
- G8.1 does not produce alpha search, ranking, scoring, validated thesis status, buying range, alert, broker behavior, provider ingestion, dashboard runtime behavior, or investment recommendations.
- Immediate next action: `approve_g8_2_one_additional_candidate_card_or_g9_one_market_behavior_signal_card_or_hold`.

G8.1A Discovery-Drift Correction Notice (2026-05-10)

- G8.1A corrects the origin label for the six-name queue.
- The queue is user-seeded and theme/supply-chain-adjacent, not pure system-scouted output.
- Required fields now include `discovery_origin`, `origin_evidence`, `scout_path`, `is_user_seeded`, `is_system_scouted`, `is_validated`, and `is_actionable`.
- `LOCAL_FACTOR_SCOUT` is defined for G8.1B but is not used in G8.1A.
- G8.1A does not produce alpha search, ranking, scoring, factor-scout output, validated thesis status, buying range, alert, broker behavior, provider ingestion, dashboard runtime behavior, or investment recommendations.
- Immediate next action: `approve_g8_1b_pipeline_first_discovery_scout_or_hold`.

DASH-0 Dashboard IA Notice (2026-05-10)

- DASH-0 approves a planning-only GodView dashboard information architecture.
- Target pages are Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, and Settings & Ops.
- DASH-0 does not edit `dashboard.py`, `views/`, `optimizer_view.py`, Streamlit runtime navigation, providers, alerts, broker code, factor scout code, discovery intake output, candidate cards, or backtests.
- Immediate next action: `approve_dash_1_page_registry_shell_or_hold`.

DASH-1 Page Registry Shell Notice (2026-05-10)

- DASH-1 implements the approved GodView page registry/sidebar shell.
- Top-level pages are Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, and Settings & Ops.
- Legacy runtime content is only relocated: Ticker Pool & Proxies -> Opportunities; Data Health and Drift Monitor -> Settings & Ops; Daily Scan, Backtest Lab, Modular Strategies, and Hedge Harvester -> Research Lab; Portfolio Builder and Shadow Portfolio -> Portfolio & Allocation.
- DASH-1 adds no new data, metrics, product claims, provider calls, alerts, broker behavior, factor-scout integration, candidate generation, ranking, scoring, or buy/sell/hold output.
- Immediate next action: `approve_dash_2_command_center_placeholder_or_hold`.

G8.2 System-Scouted Candidate-Card Notice (2026-05-10)

- G8.2 creates exactly one additional Supercycle Gem Candidate Card for `MSFT`.
- `MSFT` is eligible only because G8.1B emitted it as the sole governed `LOCAL_FACTOR_SCOUT` output.
- The MSFT card is a structured research object, not a thesis validation, score, rank, buying range, alert, trade, promotion packet, or recommendation.
- `MU` and `MSFT` are the only candidate cards after G8.2.
- Existing dashboard rows that show `MSFT`, tactical labels, entry prices, or `IGNORE` are legacy runtime output, not the G8.2 card.
- G8.2 adds no new scout output, provider call, dashboard runtime behavior, candidate ranking, candidate scoring, buy/sell/hold output, alert, or broker behavior.
- Immediate next action: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.

Portfolio Universe Construction Notice (2026-05-10)

- Portfolio Optimizer defaults now come from an explicit optimizer universe builder, not from dashboard display order or `selected_tickers[:20]`.
- `EXIT`, `KILL`, `AVOID`, and `IGNORE` are excluded by default; generic `WATCH` is research-only by default.
- Ticker-map readiness, local price-history readiness, and max-weight feasibility must be visible before allocation.
- The current optimizer is thesis-neutral and does not encode MU conviction, MU hard floors, Black-Litterman views, thesis anchors, or manual overrides.
- Immediate next action: `approve_thesis_anchor_policy_or_hold`.

Optimizer Core Structured Diagnostics Notice (2026-05-11)

- Portfolio Optimizer now has structured diagnostics for feasibility, SLSQP status, active bounds, constraint residuals, equal-weight boundary pressure, and labeled fallback allocations.
- Fallback allocations must be visible as fallback and must state that they are not optimized results.
- This notice does not approve MU conviction, WATCH investability expansion, Black-Litterman, simple tilt / conviction optimizer, new objectives, scanner rules, manual overrides, provider ingestion, alerts, broker behavior, or replay behavior.
- Immediate next action: `approve_portfolio_thesis_anchor_policy_planning_or_hold`.

Portfolio Optimizer View Test and Performance Notice (2026-05-11)

- `/portfolio-and-allocation` optimizer rendering is covered by dedicated Streamlit `AppTest` integration tests.
- Recent selected-stock display refresh loads from a non-canonical Parquet cache and schedules background refresh on cold/stale cache misses.
- Optimizer math execution is cached by selected price frame and user parameters to avoid repeated SLSQP work on equivalent rerenders.
- This notice does not approve canonical provider ingestion, new optimizer objectives, lower-bound policy, MU conviction, WATCH investability expansion, alerts, broker behavior, rankings, scores, or candidate-card dashboard integration.
- Immediate next action: `hold_or_measure_next_dashboard_runtime_bottleneck`.

Portfolio Lifecycle Replay Churn + Weight Policy (2026-05-12)

- Position Lifecycle Replay current holds must not collapse to 100% cash unless lifecycle events are truly sell-all as of the PIT-safe cutoff.
- ENTER replay weights use a max-10 position budget (`0.10`) rather than `1 / replay_universe`.
- Entries require the raw PIT entry gate, a 3-day confirmation streak, and at least 3 positive present PIT vectors across demand, moat, inventory/quality, and discipline.
- Exits require a hard 20% SMA20 stretch or a confirmed raw exit after a 20-day minimum hold; re-entry waits 10 calendar days.
- This does not approve the rejected Phase 54 Rule-of-100 sleeve, ranking, scoring, optimizer objective changes, alerts, broker behavior, provider ingestion, or live trading.

Rule of 100 Method Label (2026-05-12)

- Portfolio & Allocation exposes `Rule of 100` in the `Method` dropdown.
- Selecting `Rule of 100` displays the current Rule100 lifecycle replay holdings plus residual cash; no optimizer objective is run.
- If the lifecycle replay has no open holdings, the allocation is cash-only.
- This does not authorize ranking, scoring, alerts, broker behavior, provider ingestion, live trading, or a new optimizer objective.

Product Requirements Document: Terminal Zero
Author: Atomic Mesh | Date: 2026-02-15 | Status: Active | Version: 15.0 (FR-080 Walk-Forward Optimization In Progress)

1. Executive Summary
Terminal Zero is a local-first quantitative research platform that has evolved through twelve phases:
  Phase 1: ETL + Engine (Data Plumbing & Vectorized PnL).
  Phase 2: Adaptive Trend Strategy (3-Regime Logic: Attack/Caution/Defense).
  Phase 3: Investor Cockpit (Daily Signal Monitor: Stops, Dips, Macro).
  Phase 4: Parameter Optimizer (Automated Grid Search & Adaptive Parameters).
  Phase 5: Quantamental Integration (PIT quality gate: ROIC + Revenue Growth).
  Phase 6: Portfolio Optimizer (Inverse Volatility + Mean-Variance with fallback).
  Phase 7: Context-Aware Intelligence (Sector/Industry map integration).
  Phase 8: Catalyst Radar (Top 3000 expansion + event-driven overlays). ✅
  Phase 9: Macro-Regime Awareness Layer (institutional stress state map). ✅
  Phase 10: Global Liquidity & Flow Layer (money supply + plumbing). ✅
  Phase 11: Regime Governor + Throttle Contract (deterministic risk matrix). ✅
  Phase 12: Regime Historical Verification (truth-table + stress validation). ✅
  Phase 13: Regime Walk-Forward Backtest (signal-to-PnL validation). ✅
  Phase 14: Feature Engineering & Micro-Alpha (selector data layer). ← CURRENT

Core Philosophy: "The Pilot's Checklist." Do not guess. Check the instruments. Then let the math optimize the instruments.

Current governance overlay (Phase 65, 2026-05-09):
  - Provenance and validation gates are executable before paper-alert expansion.
  - Alpaca operational/paper infrastructure uses `alpaca-py==0.43.4`; live orders remain blocked.
  - Phase F Candidate Registry is complete as registry-only work before strategy search or promotion packets.
  - Candidate intent must be recorded before results with `trial_count`, `parameters_searched`, `manifest_uri`, `source_quality`, and `code_ref`.
  - Candidate Registry snapshots are not promotion authority; strategy search, simulation, alerts, and broker behavior remain blocked until separately approved.
  - Phase G0 V2 Proxy Boundary is complete as boundary-only work; proxy outputs are advisory, `promotion_ready = false`, registry-note-proven, and future promotion requires `core.engine.run_simulation`.
  - Phase G2/G3 fixture lineage and canonical replay are complete: one registered fixture candidate can replay through V2 proxy lineage and the V1 canonical path, with V2 still blocked from promotion.
  - Phase G4/G5 real canonical control steps are complete: one tiny Tier 0 `prices_tri` slice passed readiness gates, then replayed once through the official V1 path with neutral weights and no alpha, ranking, alert, broker, V2 real-data proxy, or promotion behavior.
  - Phase G7 preregistered `PEAD_DAILY_V0` as a tactical signal family only; it is not the core roadmap center.
  - Phase G7.1 realigned the product around discretionary augmentation for de-risked asymmetric upside: 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting.
  - `SUPERCYCLE_GEM_DAILY_V0` is the primary product family target for the next definition-only phase; no candidate generation, search, ranking, alert, broker, or promotion behavior is authorized by G7.1.

2. System Architecture
Layer 1: Data Lake (ETL → Parquet files)
Layer 2: Compute Engine (Vectorized PnL with Shift(1), Turnover Tax)
Layer 3: Strategy Layer (Pluggable "Cartridge" API)
Layer 4: Optimizer (Grid Search over Strategy Parameters) ← NEW
Layer 5: Application (Streamlit Dashboard)

3. Features (Cumulative)

3.1 The Macro Advisor (Cash Management) [Phase 3]
[FR-011] Regime Gauge:
    - Input: VIX Proxy (Rolling Vol of SPY).
    - If VIX > 25: "🔴 DEFENSE (50% Cash)"
    - If VIX > 18: "⚠️ CAUTION (20-30% Cash)"
    - Else: "🟢 BULLISH (Full Port)"

3.2 The Position Monitor (Exit & Risk) [Phase 3]
[FR-012] Chandelier Exit Calculator:
    - Logic: Stop Price = HighestClose(22d) - (k * ATR(22d)).
    - Data Constraint: Close-Only (no High/Low). k raised to 3.5 to compensate.
    - Action: If Price < Stop Price → "SELL IMMEDIATELY".

3.3 The Dip Hunter (Entry Zones) [Phase 3]
[FR-013] Reversion Bands:
    - Logic: Buy Zone = MA(20d) + (z * StdDev(20d)), where z is negative (e.g., -2.5).
    - Uses Log-Price Z-Score for volatility symmetry.
    - Action: Place Limit Orders at this level.

3.4 The Parameter Optimizer [Phase 4] ← NEW
[FR-015] 2D Grid Search (Heatmap):
    - Sweep k (Exit Multiplier): 2.0 to 4.5, step 0.1.
    - Sweep z (Entry Threshold): -1.5 to -4.0, step -0.1.
    - Metric: Ulcer-Adjusted Sharpe Ratio (balances Return vs Drawdown Pain).
    - Output: Interactive Heatmap showing optimal (k, z) coordinate.
    - Goal: Replace manual slider-nudging with mathematical optimization.

[FR-016] Adaptive Regime Parameters:
    - Instead of fixed k and z, parameters auto-adjust based on VIX Proxy:
        - VIX < 15 (Low Vol):  k=2.5 (Tight stops), z=-1.5 (Buy mild dips).
        - VIX 15-25 (Normal):  k=3.5 (Standard),    z=-2.5 (Standard dips).
        - VIX > 25 (High Vol): k=4.5 (Loose stops),  z=-3.5 (Only deep crashes).
    - Goal: Solve the FOMO vs Left-Side Pain trade-off automatically.

[FR-017] Wait-for-Confirmation ("Green Candle" Check):
    - Dip signal triggers when Z < z_entry.
    - But entry only CONFIRMS if Price(T) > Price(T-1) (first green candle).
    - Goal: Reduce premature "Left-Side" entries.

3.5 Dynamic Volatility Mapping [Phase 4.1] ← NEW
[FR-019] Per-Stock Adaptive Parameters:
    - Instead of one global k/z, each stock gets its OWN parameters based on
      its cross-sectional volatility rank (60-day window).
    - Formula:
        k_i = 2.5 + (1.5 × Rank(Vol_i))   # Low Vol → 2.5, High Vol → 4.0
        z_i = -3.0 + (2.0 × Rank(Vol_i))   # Low Vol → -3.0, High Vol → -1.0
    - Goal: NVDA (high vol) gets loose stops; KO (low vol) gets tight stops.
    - Eliminates the contradiction of a single global parameter.

4. User Interface
[FR-014] The "Daily Action Report":
    - Watchlist-based table: Current Price, Stop Price, Risk Buffer %, Buy Zone, Action.
    - Signal Visualizer: Plotly chart with Stop Line (Red) and Buy Zone (Green).
    - Per-stock k/z values displayed with volatility rank badge.

[FR-018] The "Optimizer Lab" (New Tab):
    - 2D Heatmap (Plotly) showing Return/Drawdown for each (k, z) pair.
    - Fixed vs Adaptive comparison card.

5. Implementation Roadmap
  Phase 1: ETL + Engine ✅
  Phase 2: 3-Regime Strategy ✅
  Phase 3: Investor Cockpit ✅
  Phase 4: Parameter Optimizer ✅
    - [x] Create `core/optimizer.py` (Grid Search engine).
    - [x] Update `strategies/investor_cockpit.py` with Adaptive Regime logic (FR-016).
    - [x] Add "Green Candle" confirmation (FR-017).
    - [x] Add Optimizer tab to `app.py` (FR-018).
  Phase 4.1: Dynamic Volatility Mapping ✅
    - [x] Per-stock k/z via cross-sectional vol rank (FR-019).
    - [x] Adaptive toggle in Cockpit UI.
    - [x] Fixed vs Adaptive comparison in Optimizer.
  Phase 4.2: Live Data + UX ✅
    - [x] Searchable Ticker Dropdown (FR-020).
    - [x] Yahoo Bridge — Live Data Updater (FR-021).
    - [x] Data Manager Tab (FR-022).
  Phase 5: Quantamental Integration ✅
    - [x] PIT fundamentals ingestion + snapshot context.
    - [x] Scanner Pass 1.5 hard quality gate (ROIC > 0 and Revenue YoY > 0).
    - [x] Watchlist penalty mode with quality warning/cap behavior.
  Phase 6: Portfolio Optimizer ✅
    - [x] `strategies/optimizer.py` with inverse-volatility and mean-variance (SLSQP + fallback).
    - [x] `views/optimizer_view.py` allocation UI and shares table.
  Phase 7: Sector Context ✅
    - [x] Sector map builder (`data/build_sector_map.py`).
    - [x] Scanner + optimizer sector context wiring.
  Phase 8: Catalyst Radar Foundation (Steps 1-6) ✅
    - [x] Added Top 3000 scope support (`data/updater.py`, `data/fundamentals_updater.py`, `data/build_sector_map.py`, `app.py`).
    - [x] Hydrated fundamentals snapshot for expanded universe.
    - [x] Rebuilt sector map for 3000 symbols.
    - [x] Validated scanner path at Top 3000 scale with timing + gate metrics.
    - [x] Ingested local Compustat bedrock into canonical fundamentals store (FR-031).
    - [x] Added institutional valuation/cashflow factor layer with decumulation + EV/EBITDA validation (FR-033).
  Phase 8: Catalyst Radar (Steps 7-11) ✅
    - [x] Added Yahoo earnings calendar updater (`data/calendar_updater.py`) with lock + atomic writes.
    - [x] Integrated calendar context in `app.load_data()` and Data Manager refresh controls.
    - [x] Extended scanner strategy with `days_to_earnings`, `earnings_risk`, and `fresh_catalysts` mode.
    - [x] Added scanner UI earnings warning column and risk-hide toggle.
    - [x] Added validation script for calendar layer (`scripts/validate_calendar_layer.py`).
  Phase 11: FR-041 Regime Governor + Throttle (Docs-as-Code) 🟡
    - [x] Freeze Current Algorithm v1 behavior in `spec.md` before contract changes.
    - [x] Define `RegimeManager` contract, 3x3 mapping matrix, and explicit thresholds.
    - [x] Document long-only red safety clamps.
    - [x] Add phase brief and decision log entries for FR-041.
  Phase 12: FR-042 Regime Historical Verification 🟡
    - [x] Define strict truth-table windows in docs (`docs/phase12-brief.md`).
    - [x] Create verifier script (`backtests/verify_regime_history.py`).
    - [x] Emit `regime_history.csv` and overlay artifact contract.
    - [x] Run reviewer gate and close milestone.
  Phase 13: FR-050 Regime Walk-Forward Backtest 🟡
    - [x] Define FR-050 brief and artifacts (`docs/phase13-brief.md`).
    - [x] Implement walk-forward verifier (`backtests/verify_phase13_walkforward.py`).
    - [x] Add tests for T+1 execution and cash fallback behavior.
    - [x] Run verification + reviewer gate (milestone closed: software PASS, strategy BLOCK).
  Phase 14: FR-060 Feature Engineering & Micro-Alpha 🟡
    - [x] Define FR-060 brief and feature contract (`docs/phase14-brief.md`).
    - [x] Implement feature builder (`data/feature_store.py`).
    - [x] Add tests for PIT safety and close-only fallback behavior.
    - [x] Run verification + reviewer gate (current verdict: PASS).

3.6 Searchable Ticker Dropdown [Phase 4.2] ← NEW
[FR-020] Replace raw PERMNO text input with searchable multiselect:
    - Type "NV" → dropdown filters to "NVDA (86580)".
    - Backed by tickers.parquet (23K permno→ticker mappings).
    - Chart title and Action Report show human-readable ticker names.

3.7 Yahoo Finance Bridge [Phase 4.2] ← NEW
[FR-021] Live Data Updater (data/updater.py):
    - Architecture: "Append-Only Hybrid Lake"
      - Base: prices.parquet (47M rows, WRDS 2000-2024, NEVER modified)
      - Patch: yahoo_patch.parquet (Yahoo 2025+, overwritten on update)
      - app.py reads BOTH via DuckDB UNION ALL.
    - Batch download via yf.download([...]) — 50x faster than looping.
    - Macro (SPY + VIX Proxy) rebuilt on each update.
    - Scope options: Top 50 / Top 100 / Top 200 / Custom watchlist.
    - Synthetic permnos (900000+) for new tickers not in WRDS.

3.8 Data Manager Tab [Phase 4.2] ← NEW
[FR-022] Dashboard tab for data operations:
    - System Status: Last date, universe size, SPY, VIX, freshness badge.
    - Update Controls: Scope selector + "Run Update Now" button.
    - Auto-clears st.cache_data after update and refreshes dashboard.
    - Architecture diagram showing Hybrid Lake design.

3.9 Five-State Signal Model [Phase 4.2] ← NEW
[FR-023] Replace binary SELL/BUY with 5 actionable states:
    | State | Condition | Action |
    |-------|-----------|--------|
    | HOLD  | Price > Stop, above buy zone | Trend intact. Stop = protective floor. |
    | BUY   | Price > Stop, in buy zone + green candle | Dip confirmed. Safe entry. |
    | WATCH | Price > Stop, in buy zone + red candle | Dip detected. Wait for green candle. |
    | AVOID | Price < Stop, above buy zone | Trend broken. Wait for buy zone support. |
    | WAIT  | Price < Stop, below buy zone | Capitulation. Deep support = z - 1.5σ. |
    - Key insight: "SELL" when stop is already broken is stale advice.
    - Forward-looking: shows NEXT level to watch, not past triggers.
    - Support price: Buy Zone (AVOID) or z_deep (WAIT) for re-entry guidance.

3.10 Conviction Scorecard [Phase 4.2 — L5 Alpha Upgrade]
[FR-024v2] Institutional-grade conviction scoring (0-10):
    | Dimension | Points | Logic (v2) |
    |-----------|--------|------------|
    | A. Trend  | 0-3 | Price > MA200 → 3pts (unchanged) |
    | B. Value  | 0-3 | Robust Z (MAD) < -3.0 → 3pts, < -2.0 → 1pt |
    | C. Macro  | 0-2 | VIX < 20 + falling → 2pts, mixed → 1pt, panic → 0 |
    | D. Momentum | 0-2 | Price > MA20 + ER > 0.4 → 2pts, choppy → 1pt |
    
    Advanced Methods:
    - Robust Z: Median + MAD (1.4826 scaling). Crash-resistant.
    - Efficiency Ratio: |Direction|/TotalPath. Filters noise from signal.
    - VIX Trend: Absolute level + 20d MA direction.
    
    Score Interpretation:
    | Score | Label | Meaning |
    |-------|-------|---------|
    | 8-10 | 🔥 HIGH | Perfect storm — all factors aligned |
    | 5-7 | ✅ MODERATE | Good setup, 1-2 factors missing |
    | 1-4 | ⚠️ SPECULATIVE | Counter-trend or hostile environment |

3.11 Smart Watchlist + Auto-Update [Phase 4.2] ← NEW
[FR-025] Self-healing data pipeline with persistent state:
    - data/watchlist.json: Stores {defaults: [...], user_added: [...]}
    - Signal Monitor persists user's ticker selections automatically.
    - On app startup: business-day-aware freshness check → auto-update if stale.
    - data/auto_update.py: Standalone CLI script for Task Scheduler / cron.
    - Default watchlist: AAPL, MSFT, SPY, AMZN, GOOG, META, NVDA, TSLA, QQQ, IWM.

3.12 Scanner Cockpit Redesign [Phase 4.3] ← NEW
[FR-026v2] Replace multiselect+stacked-cards with scanner+detail architecture:
    - Scanner View: Radio toggle between High Conviction / My Watchlist (same position)
        - High Conviction: scan_universe() 2-pass filter on full 2000-stock universe
        - Always shows top 5 by score (no hard cutoff)
        - Score tiers: 🔥 9+ (PERFECT STORM), ✅ 7-8 (STRONG), ⚠️ 5-6, 💤 <5
        - Watchlist: generate_weights() on watchlist tickers only (fast)
        - Each row has 🔍 drill-down button
    - Smart Dropdown: Searchable selectbox sorted by latest price (popularity proxy)
        - Uses native UI (no layout shift)
        - Sorted high-to-low price so popular stocks appear first
        - Selection triggers instant drill-down
    - Detail View: Single-ticker chart + action report card
        - Reuses all existing chart + card rendering logic
        - "← Back to Scanner" navigation
    - Removed: st.multiselect dropdown, stacked cards view
    - Kept: Sidebar controls, Macro Advisor, Conviction scoring, Watchlist persistence
    - [D-28] JIT Patch: Auto-fetch Yahoo data when user drills into stale ticker.
      Architecture: "Bedrock (WRDS 2000-2024) + Fresh Snow (Yahoo 2025-now)".

3.13 Quantamental Quality Gate [Phase 5] ← NEW
[FR-027] Add a PIT-correct quality filter to eliminate value traps:
    - Fundamentals keyed by `release_date` (not quarter-end).
    - Scanner hard filter: Trend pass AND Quality pass.
    - Minimum Viable Quality (MVQ): `ROIC > 0` and `Revenue Growth YoY > 0`.
    - Missing or stale fundamentals default to fail-safe exclusion.
    - ETF bypass list for non-operating instruments (SPY/QQQ/IWM/DIA/GLD/TLT).

3.14 Portfolio Optimizer [Phase 6] ← NEW
[FR-029] Convert "good ideas" into allocation weights:
    - Inverse-Volatility baseline allocator.
    - Mean-Variance (max Sharpe) with long-only, fully-invested constraints.
    - Failure fallback to equal-weight / inverse-vol mode for resilience.
    - UI tab with allocation chart and shares-to-buy output.

3.15 Context-Aware Sector Map [Phase 7] ← NEW
[FR-028] Add static sector/industry metadata to scanner + optimizer:
    - One-off map builder persists `data/static/sector_map.parquet`.
    - Mapped into fundamentals snapshot context for UI explainability.
    - Scanner rows now include sector classification.

3.16 Phase 8 Data Expansion Foundation [Phase 8] ← NEW
[FR-030 Step Set: 1-6] Scale universe safely from Top 2000 baseline to Top 3000 optional scope:
    - Added Top 3000 controls in Data Manager and updater CLIs.
    - Dynamic load batching in `app.load_data()`:
      - `batch_size = 200` when universe > 2500.
      - `batch_size = 250` otherwise.
    - Data hydration status (2026-02-14):
      - `fundamentals.parquet`: 10,219 rows.
      - `fundamentals_snapshot.parquet`: 1,680 rows.
      - `sector_map.parquet`: 3,000 rows.
      - Latest observed release date: 2026-03-17.
    - Validation snapshot (2026-02-14 local run):
      - Top 2000: load 15.356s, scan 0.227s, gate `trend=6`, `quality=310`, survivors=2.
      - Top 3000: load 21.307s, scan 0.307s, gate `trend=6`, `quality=432`, survivors=2.
    - Operational rollout decision:
      - Keep default runtime at Top 2000 for responsiveness.
      - Expose Top 3000 as explicit scale-up mode for controlled expansion.

3.17 Compustat Bedrock Ingestion [Phase 8] ← NEW
[FR-031 Step Set: Data Layer Expansion Before Catalyst Logic]
    - Source: `data/e1o8zgcrz4nwbyif.csv` (local WRDS/Compustat quarterly file).
    - Scope guardrail: Top 3000 liquid universe only (no 28k full-universe pivot risk).
    - PIT alignment:
      - Primary release date: `rdq`.
      - Fallback when missing: `datadate + 45 days`.
    - Metric computation:
      - `revenue_growth_yoy = (revenue_q - lag4(revenue_q)) / lag4(revenue_q)` (per permno, ordered by quarter).
      - `roic = op_income_ttm / invested_capital_avg` with fail-safe null handling.
    - Merge precedence:
      - On `(permno, release_date)` collisions, `compustat_csv` overrides `yfinance`.
    - Safety:
      - `.update.lock` coordination.
      - Atomic parquet writes + timestamped backups.
      - Match/unmatched audit outputs for traceability.
    - Execution results (2026-02-14):
      - Top3000 match coverage: `2781/3000` (`92.70%`).
      - `fundamentals.parquet`: `10,219 -> 225,640` rows (initial merge).
      - `fundamentals_snapshot.parquet`: `1,680 -> 2,819` rows (initial merge).
      - Scanner gate (Top 3000): `trend=6`, `quality=428`, `survivors=2` (initial merge).
    - Post-remediation state (2026-02-15):
      - `fundamentals.parquet`: `215,876` rows (dedup + PIT clamp applied).
      - `fundamentals_snapshot.parquet`: `1,550` rows (active + complete metrics).
      - Data layer validator: PASS.

3.18 Russell 3000 PIT Universe Scaffold [Phase 8] ← NEW
[FR-032 Step Set: Forward-Test Universe Layer]
    - Added loader: `data/r3000_membership_loader.py`.
    - Input Gate (institutional hard stop):
      - Requires WRDS constituent-history columns: `gvkey`, `from`, `thru`.
      - Requires minimum constituent rows (default `>= 1000` with usable `gvkey`).
      - Rejects metadata-only exports.
    - Artifacts:
      - `data/processed/r3000_membership.parquet`
      - `data/processed/universe_r3000_daily.parquet`
      - `data/processed/r3000_unmatched.csv`
    - Dynamic PIT logic for forward testing:
      - Daily universe uses `from <= T <= thru` at each trade date `T`.
    - Current status (2026-02-15):
      - Provided file `data/t1nd1jyzkjc3hsmq.csv` failed input gate (metadata-only, no usable constituents).
      - Awaiting full WRDS index constituent history export to complete FR-032 execution.

3.19 Institutional Valuation Factor Layer [Phase 8] ← NEW
[FR-033 Step Set: Cashflow Decumulation + EV/EBITDA Matrix]
    - Added institutional factor schema to canonical fundamentals:
      - Raw fields: `oibdpq`, `atq`, `ltq`, `xrdq`, `oancfy`, `dlttq`, `dlcq`, `cheq`, `cshoq`, `prcraq`, `fyearq`, `fqtr`.
      - Derived fields: `oancf_q`, `oancf_ttm`, `ebitda_ttm`, `revenue_ttm`, `xrd_ttm`, `mv_q`, `total_debt`, `net_debt`, `ev`, `ev_ebitda`, `leverage_ratio`, `rd_intensity`.
    - Core logic:
      - Cashflow de-YTD: `oancf_q = oancfy - lag(oancfy)` for Q2-Q4 within `(permno, fyearq)`.
      - EV/EBITDA + leverage computed vectorized with safe denominators.
    - Validation outcomes (2026-02-15):
      - PIT violations: `0`.
      - Decumulation mismatch: `0.0698%`.
      - Q4 spike rate (>10x Q1-Q3 median): `1.69%`.
      - EV/EBITDA arithmetic bad-rate (>1% error): `0.00%`.
      - Snapshot factor coverage: EV/EBITDA `48.45%`, Leverage `73.94%`, RD Intensity `47.87%`, OANCF_TTM `85.35%`, EBITDA_TTM `80.90%`.
    - Runtime smoke (Top 3000):
      - Load `10.105s`, Scan `0.087s`.
    - Gate: `trend=6`, `quality=945`, `survivors=4`.

3.20 Catalyst Radar [Phase 8] ← NEW
[FR-034 Step Set: Event Risk + Fresh Catalysts]
    - New data artifact: `data/processed/earnings_calendar.parquet`.
    - Ingestion:
      - `data/calendar_updater.py` fetches earnings dates from Yahoo Finance.
      - Scope options: Top 20/50/100/200/500/3000 or custom watchlist.
      - Runtime safety: updater lock + atomic parquet writes.
    - Strategy integration (`strategies/investor_cockpit.py`):
      - Adds `days_to_earnings`, `days_since_earnings`, and `earnings_risk`.
      - Risk rule: `earnings_risk = 1` when earnings are within blackout window (default `<5 days`).
      - New scanner mode: `fresh_catalysts` (reported earnings in last 7 days + existing quality/trend gates).
    - UI integration:
      - Scanner table now includes an `Earnings` column with warning badge.
      - Controls include blackout-days selector and "Hide earnings risk" toggle.
      - Data Manager includes calendar coverage/freshness metrics and refresh trigger.

3.21 Macro-Regime Awareness Layer [Phase 9] ← NEW
[FR-035 Step Set: Institutional State Space]
    - Objective:
      - Convert market stress into explicit, PIT-safe features and regime flags.
      - Enable strategy behavior shifts via a deterministic macro scalar.
    - Canonical artifact:
      - `data/processed/macro_features.parquet` (single source of truth; no dual macro files).
    - Data sources (Phase 9):
      - Yahoo: `^VIX`, `^VIX3M`, `^VVIX`, `DX-Y.NYB`, `^GSPC`, `HYG`, `LQD`, `MTUM`, `SPY`, `BND`, `BTC-USD`.
      - FRED: `SOFR`, `DFF` (EFFR proxy), `T10Y2Y`, `DFII10`.
      - DIX/GEX explicitly deferred to Phase 10.
    - PIT alignment policy:
      - Fast market series: T+0 at market close.
      - Slow FRED series: conservative T+1 shift.
      - Weekend/holiday continuity: forward-fill max 3 trading days.
    - Regime checks:
      - `liquidity_air_pocket`: `(VIX - VIX3M > 0) & (VVIX > 110)`.
      - `collateral_crisis`: `(SOFR - EFFR) > 0.10` (10 bps).
      - `credit_freeze`: `zscore(HYG/LQD, 63d) < -2.0`.
      - `momentum_crowding`: `corr(MTUM, SPY, 60d) > 0.85`.
    - Acceptance criteria:
      - March 2020 triggers liquidity stress events.
      - 2022 shows momentum crowding state transitions.
      - Loader and validator pass (`macro_loader.py`, `validate_macro_layer.py`).

3.22 Global Liquidity & Flow Layer [Phase 10] ← NEW
[FR-040 Step Set: Money Supply + Plumbing]
    - Objective:
      - Measure macro liquidity causes (not just volatility symptoms).
      - Add a daily, PIT-safe liquidity feature layer for strategy conditioning.
    - Canonical artifact:
      - `data/processed/liquidity_features.parquet`
    - Core signals:
      - `us_net_liquidity_mm = WALCL - WDTGAL - (RRPONTSYD * 1000)`
      - `liquidity_impulse` (normalized 20-day ROC of net liquidity)
      - `repo_spread_bps = (SOFR - DFF) * 100`
      - `lrp_index = Z(DTB3) - Z(VIX)`
      - `dollar_stress_corr = Corr20(DXY, SPX returns)`
      - `smart_money_flow = CumSum(SPY Close - SPY Open)`
    - PIT guardrail:
      - Fed H.4.1 weekly series (`WALCL`, `WDTGAL`) availability is shifted +2 days (Wed -> Fri).
    - Exclusions for MVP:
      - DIX/GEX, FTD, and COT feeds deferred to later phase.

3.23 Regime Governor + Throttle Contract [Phase 11] ← NEW
[FR-041 Step Set: Deterministic Exposure Control]
    - Objective:
      - Separate "state safety" (Governor) from "opportunity context" (Throttle).
      - Replace implicit fallback behavior with an explicit 3x3 exposure matrix.
    - Inputs and thresholds (explicit):
      - RED if any:
        - `repo_spread_bps > 10.0` (basis points)
        - `credit_freeze == True` AND `vix_level > 15`
        - `liquidity_impulse < -1.90` AND `vix_level > 20`
        - `vix_level > 40`
      - AMBER if not RED and any:
        - `us_net_liquidity_mm < 0.997 * MA20(us_net_liquidity_mm)` AND `liquidity_impulse < 0`
        - `vix_level > 25`
        - `bocpd_prob > 0.80`
      - GREEN otherwise.
      - Throttle score:
        - `S = mean(Z(liquidity_impulse), Z(vrp), -Z(vix_level), Z(momentum_proxy))` in `[-2, 2]`.
        - POS if `S > 0.5`, NEUT if `-0.5 <= S <= 0.5`, NEG if `S < -0.5`.
      - Data contract:
        - `realized_vol_21d` and `vrp = vix_level - realized_vol_21d` are produced in `data/liquidity_loader.py`.
    - Regime matrix (`Governor x Throttle`):
      - GREEN: `NEG=0.70`, `NEUT=1.00`, `POS=1.30`
      - AMBER: `NEG=0.25`, `NEUT=0.50`, `POS=0.75`
      - RED: `NEG=0.00`, `NEUT=0.00`, `POS=0.20`
    - Long-only safety rule:
      - `RED+NEG` and `RED+NEUT` force `0.00` exposure (cash).
      - `RED+POS` is capped at `0.20` (tactical, no shorting).
      - Strategy remains long-only (`weights >= 0.0`).
    - Delivery criteria:
      - `spec.md` includes frozen "Current Algorithm v1" and FR-041 interface/matrix contract.
      - `docs/phase11-brief.md` captures objective, thresholds, matrix, and acceptance criteria.
      - `decision log.md` records FR-041 architecture and red-regime long-only safety decisions.

3.24 Regime Historical Verification [Phase 12] ← NEW
[FR-042 Step Set: Truth-Table Proof of Life]
    - Objective:
      - Validate that FR-041 regime logic matches known crisis/calm windows without curve-fitting.
      - Verify safety behavior (crisis capture) and opportunity behavior (false-positive control).
    - Verifier:
      - `backtests/verify_regime_history.py`
      - Replays `RegimeManager` over full history and emits:
        - `data/processed/regime_history.csv`
        - `data/processed/regime_overlay.png`
    - Mandatory truth windows:
      - `2008Q4`: predominantly RED.
      - `2020-03`: predominantly RED.
      - `2022H1`: predominantly AMBER/RED.
      - `2017`: predominantly GREEN (false-positive guardrail).
      - `2023-11`: transition toward GREEN.
    - Behavioral metrics:
      - Drawdown reduction vs buy-and-hold baseline.
      - Recovery speed vs baseline.

3.25 Regime Walk-Forward Backtest [Phase 13] ← NEW
[FR-050 Step Set: Governor-to-PnL Validation]
    - Objective:
      - Validate whether FR-041 regime routing improves realized risk-adjusted
        outcomes when translated into executable portfolio weights.
    - Deterministic routing:
      - `GREEN -> 1.0 SPY`, `AMBER -> 0.5 SPY`, `RED -> 0.0 SPY` (cash).
      - Signal at `t` is executed at `t+1` (no look-ahead).
    - Cash proxy hierarchy:
      - `BIL` return when available.
      - Else `EFFR / 252` daily accrual.
      - Else flat `2% / 252`.
    - Artifacts:
      - `data/processed/phase13_walkforward.csv`
      - `data/processed/phase13_equity_curve.png`
    - Primary checks:
      - Ulcer index improvement.
      - Max drawdown compression.
      - Sharpe improvement.

3.26 Feature Engineering & Micro-Alpha [Phase 14] ← NEW
[FR-060 Step Set: Selector Data Layer]
    - Objective:
      - Add stock-level feature vectors for ranking, sizing, and execution.
    - Ranking features:
      - `resid_mom_60d`, `amihud_20d`, `rolling_beta_63d`.
    - Sizing feature:
      - `yz_vol_20d` (Yang-Zhang annualized volatility).
    - Execution features:
      - `atr_14d`, `rsi_14d`, `dist_sma20`.
    - Minimal signal scaffold:
      - `composite_score = Z(resid_mom_60d) + Z(flow_proxy) - Z(yz_vol_20d)`.
      - `trend_veto = price < SMA200`.
    - Data-constraint fallback:
      - If `open/high/low` are missing, use documented close-only fallback modes for YZ and ATR.
    - Artifact:
      - `data/processed/features.parquet`.

3.27 Alpha Engine & Tactical Execution [Phase 15] ← NEW
[FR-070 Step Set: Selector + Sizer + Executor]
    - Objective:
      - Connect the Governor (capital preservation) and Feature Store (asset-level alpha)
        into one deterministic execution layer.
    - Structural-fixed rules (not tuned):
      - Trend eligibility gate remains `price > SMA200`.
      - Regime budgets remain fixed: `GREEN=1.0`, `AMBER=0.5`, `RED=0.0`.
      - Score sign discipline remains fixed (momentum positive, volatility negative).
    - Adaptive knobs (walk-forward only):
      - RSI entry threshold via rolling percentile.
      - ATR stop multiplier via volatility regime.
      - Selection breadth via top-N / percentile depth.
    - Hard execution rules:
      - Hysteresis rank buffer: enter `Top 5`, hold until rank drops below `Top 20`.
      - Ratchet-only stop: stop level can only move upward after entry.
      - Regime budget hard cap always enforced at portfolio level.
    - Sizing contract:
      - Base: `target_risk / yz_vol_20d`.
      - Adjust: conviction scalar.
      - Enforce: hard cap to regime budget at portfolio level.
    - Executor contract:
      - Entry around pullback conditions (`SMA20` / RSI signal).
      - Dynamic stop using ATR multiple.
    - Artifacts:
      - Strategy module: `strategies/alpha_engine.py`
      - Strategy integration: `strategies/investor_cockpit.py`
      - Verifier: `backtests/verify_phase15_alpha_walkforward.py`
      - Unit tests: `tests/test_alpha_engine.py`

3.28 Walk-Forward Optimization & Honing [Phase 16] ← NEW
[FR-080 Step Set: Governance-First Parameter Honing]
    - Objective:
      - Hone adaptive execution parameters without changing fixed structural rules.
      - Improve out-of-sample robustness while preventing curve-fit drift.
    - WFO policy:
      - Fixed split protocol:
        - Train: `2015-01-01` to `2021-12-31`
        - OOS/Test: `2022-01-01` to `2024-12-31`
      - Parameter search and ranking use train metrics only.
      - OOS/Test is read-only for stability checks and pass/fail governance.
      - Promotion requires OOS stability acceptance and hard-constraint compliance.
    - Search space:
      - `entry_logic`: `dip`, `breakout`, `combined`.
      - `alpha_top_n` (selection depth).
      - `hysteresis_exit_rank` with mandatory `hysteresis_exit_rank >= alpha_top_n`.
      - `rsi_entry_percentile`.
      - `atr_multiplier`.
      - Phase 16.5 tournament baseline grid:
        - `alpha_top_n`: `10, 20`
        - `hysteresis_exit_rank`: `20, 30`
        - `adaptive_rsi_percentile`: `0.05, 0.10, 0.15`
        - `atr_preset`: `2.0, 3.0, 4.0, 5.0`
    - Runtime optimization patch:
      - Single-pass data loading and reuse across candidate evaluations.
      - Optional multi-core candidate evaluation with deterministic sequential fallback.
    - Acceptance criteria:
      - No OOS leakage in parameter selection path.
      - Structural-fixed rules from FR-070 remain unchanged.
      - Hard constraints pass for promoted parameter sets.
      - Required artifacts are generated and consumable.
    - Artifacts:
      - `data/processed/phase16_optimizer_results.csv`
      - `data/processed/phase16_best_params.json`
      - `data/processed/phase16_oos_summary.csv`

3.29 Position-Level Stop-Loss Control [Phase 21 Day 1] ← NEW
[FR-090 Step Set: Stop-Loss & Drawdown Control]
    - Objective:
      - provide a standalone, testable stop-loss subsystem for close-only environments.
    - ATR policy:
      - `atr_mode = proxy_close_only` (explicit).
      - `ATR_t = SMA(|Close_t - Close_{t-1}|, window=20)`.
    - Stop stages:
      - Initial: `entry - 2.0 * ATR_entry`.
      - Trailing: `price_t - 1.5 * ATR_t`.
      - Time override: exit when underwater for more than `60` days.
    - D-57 invariant:
      - `stop_t = max(stop_{t-1}, stop_candidate_t)` (stop never decreases).
    - Portfolio drawdown tiers:
      - `-8% => 0.75`, `-12% => 0.50`, `-15% => 0.00`; recover to full at `>-4%`.
    - Artifacts:
      - `strategies/stop_loss.py`
      - `tests/test_stop_loss.py`

3.30 SDM 3-Pillar Data Ingestion [Phase 23] ← NEW
[FR-100 Step Set: SDM Data Foundation]
    - Objective:
      - Build PIT-safe ingestion/assembly for Supply-Demand-Margin feature backbone.
    - Ingestion scripts:
      - `scripts/ingest_compustat_sdm.py` (Pillar 1 + 2)
      - `scripts/ingest_frb_macro.py` (Pillar 3a)
      - `scripts/ingest_ff_factors.py` (Pillar 3b)
      - `scripts/assemble_sdm_features.py` (final PIT assembler)
    - PIT merge contract:
      - Compustat anchor: `published_at = rdq`.
      - Peters & Taylor lag: `pit_date = datadate + 90 days`.
      - `merge_asof` requires global timeline-key sorting before join.
    - Identifier policy:
      - `permno` mapping uses `sector_map.parquet`.
      - unmapped rows are retained and audited (no silent drops).
    - Artifacts:
      - `data/processed/fundamentals_sdm.parquet`
      - `data/processed/macro_rates.parquet`
      - `data/processed/ff_factors.parquet`
      - `data/processed/features_sdm.parquet`

3.31 The Infinity Governor & Derivatives Trinity [Phase 62 & 64] ← NEW
[FR-110 Step Set: Non-Linear Risk & Leverage Abstraction]
    - Objective:
      - Match Buy & Hold on Compounders; Crush Buy & Hold on Manias.
    - Logic:
      - Bi-directional stop multiplier. Reward high $R^2$ with 5.4x stops. Penalize high Convexity with 1.5x stops.
      - Lookback Period strictly locked at 20 trading days to isolate immediate kinetic momentum.
      - Data Gaps (NaN/Null) fail-safe to baseline 3.0x ATR.
    - Leverage Engine:
      - Macro > 80 + Score 100 + Linear Trend = BUY 80-Delta LEAP.
      - If trend goes Parabolic = De-lever to 1.0x Stock.
      - Stop loss on LEAP is strictly tied to the underlying stock's trailing stop.
    - Polling Protocol:
      - Macro Gravity evaluated strictly at EOD (4:00 PM EST). No intraday regime changes.

3.32 Unified Command & Waterfall Entries [Phase 65] ← NEW
[FR-120 Step Set: Single Source of Truth Execution]
    - Objective:
      - Fuse regime, entry, and vehicle into one dashboard command.
    - Entry Logic:
      - Targets the *next* logical floor (21 -> 50 -> 200) instead of broken lines.
      - Applies empirical Wick Buffers based on kinetic cluster (Heavies, Sprinters, Scouts).
      - Applies Quality Premium to ensure fills on "Must Own" Score 100 assets.
    - Execution Mechanism:
      - Day Limit Orders ONLY (calculated EOD for next session). No GTC resting orders.
      - Zero FOMO protocol for fill failures; missing a trade costs nothing.

3.33 Microstructure Telemetry & Execution-Quality Analytics [Phase 29] ← NEW
[FR-130 Step Set: Arrival/Fill Quality Instrumentation]
    - Objective:
      - Upgrade execution assessment from binary `ok=True/False` to measurable microstructure quality.
    - Arrival Anchor:
      - At Sovereign_Command generation time, stamp `arrival_ts` (UTC ms precision).
      - Capture command-time midpoint: `arrival_price = (bid + ask) / 2`.
    - Fill Aggregation:
      - Aggregate partial fills by `client_order_id` and compute:
        - `VWAP_fill = sum(fill_price_i * fill_qty_i) / sum(fill_qty_i)`.
    - Slippage / Shortfall:
      - Buy shortfall: `IS_buy = (VWAP_fill - arrival_price) * qty`.
      - Sell shortfall (cost-positive): `IS_sell = (arrival_price - VWAP_fill) * qty`.
      - Normalize cross-asset costs via `slippage_bps` on arrival reference.
    - Latency Decomposition:
      - `command->submit`, `submit->ack`, `ack->first_fill`, `command->first_fill`.
    - Storage:
      - Persist order-level and fill-level telemetry in Parquet + DuckDB for OLAP analytics.

3.34 Release Engineering / MLOps Deterministic Pipeline [Phase 30] ← NEW
[FR-140 Step Set: Immutable Artifact Promotion + Automatic Rollback]
    - Objective:
      - Eliminate mutable deployment drift and guarantee deterministic startup-fault rollback.
    - Immutable Artifact Contract:
      - Every candidate release is a digest-locked image reference:
        - `release_ref = "<repo>:<tag>@sha256:<64-hex>"`.
      - Tags without digest lock are not promotable.
    - Promotion State Machine:
      - `pending_probe -> active | rolled_back`.
      - Metadata persisted atomically to:
        - `data/processed/release_metadata.json`.
    - Startup-Fault Rollback Contract:
      - Deployment controller watches candidate startup window.
      - If candidate exits during startup diagnostics, controller auto-restores N-1 image with no manual intervention.
    - UI Governance:
      - Cache invalidation is release-bound:
        - `cache_fingerprint = "<version>@sha256:<release_digest|local-dev>"`.

3.35 Sovereign Execution Hardening [Phase 31] <- NEW
[FR-150 Step Set: Trust Boundary + Telemetry Durability]
    - Objective:
      - close fail-open seams in signed replay, async telemetry durability, and semantic coercion boundaries.
    - Trust boundary:
      - local-submit replay gate is atomic across processes.
      - malformed replay ledger rows are quarantined and cannot hard-block valid submits.
    - Telemetry durability:
      - spool replay uses deterministic UID idempotence,
      - schema-invalid and stale-partial spool records are quarantined,
      - local-submit success/notify requires bounded durability gate pass.
    - Semantic contract:
      - snapshot paths validate required columns and date coercion,
      - candidate ranking is numeric-stable for `composite_score`,
      - boolean gates normalize explicit token sets (no unsafe truthiness coercion).
    - Artifacts:
      - `execution/signed_envelope.py`
      - `execution/microstructure.py`
      - `main_console.py`
      - `strategies/alpha_engine.py`
      - `strategies/ticker_pool.py`
      - `tests/test_signed_envelope_replay.py`
      - `tests/test_execution_microstructure.py`

3.36 Candidate Registry and Proxy Quarantine [Phase 65] <- NEW
[FR-160 Step Set: Candidate Intent + Synthetic Proxy Mechanics]
    - Objective:
      - prevent candidate results from outrunning identity, provenance, and official-truth boundaries.
    - Phase F registry:
      - candidate intent is registered before results;
      - append-only JSONL event log is the source of truth;
      - snapshot files are disposable projections;
      - no strategy search, alert, broker, or promotion path is authorized by registry presence.
    - Phase G0 proxy boundary:
      - V2 proxy outputs are advisory only;
      - `promotion_ready = false`;
      - `canonical_engine_required = true`;
      - future promotion still requires `core.engine.run_simulation`.
    - Phase G1 synthetic mechanics:
      - accepts only manifest-backed synthetic fixtures under `data/fixtures/v2_proxy/`;
      - reconciles fixture/golden row counts, date ranges, schema columns, and SHA-256 hashes before accepted output;
      - rejects `nan`, `+inf`, `-inf`, missing symbols, sparse target weights, and non-finite proxy metadata fail-closed;
      - does not repair invalid evidence with `nan_to_num`, sparse-weight `fillna(0)`, interpolation, or stringified nulls;
      - consumes prebaked target weights, not signals;
      - emits only positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, and boundary verdict;
      - blocks real market data, alpha/Sharpe/CAGR/max-drawdown/ranking metrics, alerts, broker calls, and promotion packets.
    - Phase G2/G3 fixture replay:
      - records one registered fixture candidate and one hash-linked proxy note before replay comparison;
      - calls `core.engine.run_simulation` for the V1 canonical replay proof;
      - compares only mechanical accounting fields;
      - emits `boundary_verdict = "v2_blocked_from_promotion"`;
      - keeps `promotion_ready = false` even when V1 and V2 match.
    - Phase G4 real canonical readiness:
      - uses one tiny Tier 0 `prices_tri` daily-bar slice only;
      - requires a dedicated manifest and reconciles SHA-256, row count, schema, and date range;
      - rejects Tier 2, public-web, operational-market-data, stale, ambiguous, duplicate-key, non-monotonic, non-finite, and impossible price/return evidence;
      - emits readiness only with `ready_for_g5`, not strategy performance;
      - keeps sidecars optional for the passing price slice and blocks stale sidecars only when explicitly required.
    - Phase G5/G6 real canonical replay and comparison:
      - G5 calls `core.engine.run_simulation` once on the G4 slice with predeclared neutral weights;
      - G6 runs V1 and V2 mechanics separately on the same real canonical slice and weights;
      - compares only mechanical accounting fields and records engine identity separately;
      - keeps `promotion_ready = false`, `v2_promotion_ready = false`, alerts blocked, broker calls blocked, and promotion packets blocked even when V1/V2 match;
      - does not emit alpha, Sharpe, CAGR, drawdown, rank, score, signal strength, or buy/sell decisions.
    - Phase G7 controlled candidate-family definition:
      - defines `PEAD_DAILY_V0` before any result observation;
      - declares hypothesis, universe, feature allowlist, finite parameter space, trial budget, data policy, validation gates, and multiple-testing policy;
      - uses manifest-backed append-only/versioned family definition artifacts;
      - blocks candidate generation, backtest/replay/proxy runs, alpha/performance metrics, rankings, alerts, broker calls, and promotion packets.
    - Artifacts:
      - `v2_discovery/registry.py`
      - `v2_discovery/fast_sim/boundary.py`
      - `v2_discovery/fast_sim/simulator.py`
      - `v2_discovery/replay/canonical_replay.py`
      - `v2_discovery/replay/comparison.py`
      - `v2_discovery/replay/canonical_real_replay.py`
      - `v2_discovery/replay/real_slice_v1_v2_comparison.py`
      - `v2_discovery/readiness/canonical_readiness.py`
      - `v2_discovery/readiness/canonical_slice.py`
      - `v2_discovery/families/registry.py`
      - `v2_discovery/families/schemas.py`
      - `v2_discovery/families/trial_budget.py`
      - `v2_discovery/families/validation.py`
      - `data/fixtures/v2_proxy/*`
      - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet`
      - `data/registry/candidate_families/pead_daily_v0.json`
      - `tests/test_candidate_registry.py`
      - `tests/test_v2_proxy_boundary.py`
      - `tests/test_v2_fast_proxy_synthetic.py`
      - `tests/test_v2_fast_proxy_invariants.py`
      - `tests/test_v2_canonical_replay_fixture.py`
      - `tests/test_g4_real_canonical_readiness_fixture.py`
      - `tests/test_g5_single_canonical_replay_no_alpha.py`
      - `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`
      - `tests/test_g7_candidate_family_definition.py`

3.37 Discretionary Augmentation Roadmap [Phase 65 G7.1] <- NEW
[FR-161 Step Set: Product Charter + Dashboard Taxonomy]
    - Objective:
      - reframe the roadmap before candidate generation so the system does not drift into generic alpha search by inertia.
    - Product charter:
      - Terminal Zero is a discretionary augmentation cockpit, not a trading bot;
      - roadmap focus is 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting;
      - `SUPERCYCLE_GEM_DAILY_V0` is the primary product-family target;
      - `PEAD_DAILY_V0` remains valid as a tactical signal family and evidence module only.
    - Roadmap vocabulary:
      - "alpha search" becomes "de-risked upside discovery";
      - "strategy candidate" becomes "thesis / signal candidate";
      - "buy/sell signal" becomes "decision-support state";
      - "backtest result" becomes "evidence layer";
      - "alert" becomes "buying-range / hold-discipline prompt";
      - "V2 discovery" becomes "research sandbox";
      - "promotion" becomes "human-reviewed thesis approval".
    - Dashboard taxonomy:
      - thesis health;
      - entry discipline;
      - hold discipline;
      - flow and positioning;
      - regime.
    - Flow and positioning boundary:
      - short-squeeze and CTA-type signals are context, not automatic triggers;
      - lagged source cadence and source quality must be shown before downstream use.
    - Phase sequence:
      - G7.1 roadmap realignment;
      - G7.2 define Supercycle Gem Family, no search;
      - G8 create one thesis candidate card, no search;
      - G9 build dashboard signal map, no alpha search;
      - G10 begin bounded discovery inside one approved family;
      - G11 entry/hold discipline monitor;
      - G12 paper-only buying-range prompts.
    - Blocked scope:
      - no candidate generation, backtest, replay, proxy run, search, ranking, metric output, alert emission, broker call, live order, or promotion packet.
    - Artifacts:
      - `docs/architecture/product_roadmap_discretionary_augmentation.md`
      - `docs/architecture/dashboard_signal_taxonomy.md`
      - `docs/architecture/supercycle_gem_family_policy.md`
      - `docs/handover/phase65_g71_handover.md`

[DASH-2 Product Delta: Portfolio Allocation Runtime Slice]
    - Objective:
      - keep Portfolio Optimizer as the primary Portfolio & Allocation workflow while adding a below-the-fold YTD comparison.
    - Product behavior:
      - Portfolio Optimizer renders top-level, not behind an expander/toggle;
      - YTD Performance renders below optimizer output;
      - portfolio return reflects current optimizer weights when available;
      - SPY and QQQ are displayed as comparison benchmarks.
    - Data boundary:
      - yfinance adjusted-close overlay is used only for runtime display freshness;
      - selected-stock overlay fetching/scaling and strategy-metrics parsing are delegated to `core/data_orchestrator.py`, not the Streamlit view;
      - no canonical provider ingestion, candidate scoring, ranking, alerting, broker behavior, or candidate-card merge is authorized.
    - Artifacts:
      - `core/data_orchestrator.py`
      - `dashboard.py`
      - `views/optimizer_view.py`
      - `tests/test_dash_2_portfolio_ytd.py`
      - `tests/test_data_orchestrator_portfolio_runtime.py`

[Dashboard Architecture Safety Slice - 2026-05-11]
    - Objective:
      - remove Windows-unsafe and duplicated process-liveness behavior from runtime paths without changing product behavior.
    - Runtime safety:
      - `utils/process.py::pid_is_running` is the shared process-liveness helper;
      - direct runtime `os.kill(pid, 0)` probes are blocked outside the shared utility;
      - dashboard backtest spawn refuses a second job when a PID file points to a live process, rather than terminating an unverified PID.
    - Dashboard helper boundary:
      - Modular Strategies and Portfolio Builder fallback use one strategy-matrix initializer path;
      - dashboard portfolio price cleanup delegates to `core.data_orchestrator.clean_price_frame`.
    - Blocked scope:
      - no provider ingestion, canonical data write, strategy search, ranking, scoring, alerting, broker behavior, dashboard content redesign, or candidate-card dashboard merge.
    - Artifacts:
      - `utils/process.py`
      - `dashboard.py`
      - `data/updater.py`
      - `scripts/parameter_sweep.py`
      - `scripts/release_controller.py`
      - `backtests/optimize_phase16_parameters.py`
      - `tests/test_process_utils.py`

[Portfolio Lifecycle Current Holds - 2026-05-11]
    - Objective:
      - make Portfolio & Allocation reflect open Position Lifecycle Replay holdings instead of showing 100% cash when replay has not sold all.
    - Product behavior:
      - current holdings are reconstructed from the latest ENTER/EXIT event per ticker as of today;
      - future-dated replay rows are ignored;
      - open replay positions remain current holds even when today's scanner row is EXIT/KILL;
      - no fresh PIT ENTER candidates means "hold existing replay positions plus cash," not "sell all to cash."
      - allocation and live ticker performance paths preserve residual cash for sub-100% holdings.
    - Data boundary:
      - lifecycle replay JSONL is read as local audit state;
      - no provider ingestion, canonical market-data write, alert, broker behavior, ranking, scoring, or new optimizer objective is authorized.
    - Artifacts:
      - `data/portfolio_lifecycle_log.py`
      - `strategies/portfolio_universe.py`
      - `views/optimizer_view.py`
      - `dashboard.py`
      - `tests/test_position_lifecycle.py`
      - `tests/test_portfolio_universe.py`
      - `tests/test_optimizer_view.py`
      - `tests/test_dash_2_portfolio_ytd.py`

[Portfolio Replay Selection Identity - 2026-05-15]
    - Objective:
      - make Portfolio replay identity explicit enough that stale hidden session state cannot produce a coherent replay for the wrong universe.
    - Product behavior:
      - optimizer controls publish a signed `PortfolioReplaySelection`;
      - dashboard replay request construction validates the signed selection before saved-artifact or transitional replay builds;
      - selection signatures bind typed asset identities and selected price content;
      - missing, stale, or mismatched selection renders replay unavailable;
      - first-10 price-column fallback and hidden `optimizer_universe` are forbidden replay sources.
    - Data boundary:
      - event/decision aux rows loaded by dashboard remain a labeled transitional producer bridge until backend artifacts emit dashboard cache signatures;
      - no provider ingestion, canonical market-data write, alert, broker behavior, ranking, scoring, recommendation, or live trading is authorized.
    - Artifacts:
      - `views/optimizer_view.py`
      - `dashboard.py`
      - `tests/test_optimizer_view.py`
      - `tests/test_dash_2_portfolio_ytd.py`

[Lifecycle Decision Export - 2026-05-12]
    - Objective:
      - export the replay buy/sell/hold/no-action decision tape before implementing the true Rule-of-100 lifecycle policy.
    - Product behavior:
      - export-only mode does not mutate current lifecycle holdings;
      - BUY/SELL export rows are audit labels and must match lifecycle ENTER/EXIT events;
      - every exported row includes reasons, gate state, streaks, hold days, cooldown state, and Rule-of-100 proxy fields.
    - Data boundary:
      - export artifacts are local JSONL/JSON analysis files;
      - no provider ingestion, canonical write, broker behavior, alert, ranking, scoring, dashboard action-label change, or optimizer objective change is authorized.
    - Artifacts:
      - `scripts/pit_lifecycle_replay.py`
      - `tests/test_pinned_universe.py`
      - `data/portfolio_lifecycle_decision_log.jsonl`
      - `data/portfolio_lifecycle_buy_sell_log.jsonl`
      - `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

[Rule100 Lifecycle Policy v0 - 2026-05-12]
    - Objective:
      - promote the current single lifecycle strategy to Rule100 v0 before any generic replay abstraction.
    - Product behavior:
      - demand/supply/pricing/margin state is explicit and proxy-provenanced;
      - BUY/HOLD/EXIT drive replay behavior while TRIM/TIGHTEN are audit-only lifecycle states;
      - current dashboard-compatible runtime events stay ENTER/EXIT;
      - entry sizing is conviction-based and capped at 15%.
    - Data boundary:
      - no provider ingestion, canonical write, broker behavior, alert, ranking, scoring, dashboard action-label change, generic replay framework, or Phase 54 sleeve reopen is authorized.
    - Artifacts:
      - `scripts/pit_lifecycle_replay.py`
      - `tests/test_pinned_universe.py`
      - `data/portfolio_lifecycle_log.jsonl`
      - `data/portfolio_lifecycle_decision_log.jsonl`
      - `docs/context/e2e_evidence/rule100_v0_lifecycle_replay_tmp.jsonl`

[Rule100 Softmax v1 Audit - 2026-05-12]
    - Objective:
      - add a softmax-first sizing path, wire it to the explicit Rule of 100 UI method, and keep Kelly as a thin comparator on the same harness.
    - Product behavior:
      - `strategies/rule100_softmax.py` owns pure softmax sizing helpers plus the comparator-only Kelly shim;
      - `scripts/rule100_softmax_v1_audit.py` builds the shared audit frame and writes summary/comparison/sample/cash/history artifacts;
      - selecting `Rule of 100` displays PIT softmax v1 target weights and stores `portfolio_allocation_state.source = rule100_softmax_v1`;
      - Position Lifecycle Replay preserves original event weights and shows softmax v1 target weights as a separate PIT audit overlay;
      - current target state is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%;
      - softmax v1 uses a 10% per-eligible-name gross budget, a 15% single-name cap, and explicit cash residual;
      - Kelly stays comparator-only and may under-allocate rather than becoming a second full stack.
    - Data boundary:
      - no lifecycle log mutation, provider ingestion, broker behavior, alert, ranking, optimizer objective change, or Phase 54 sleeve reopen is authorized.
    - Artifacts:
      - `strategies/rule100_softmax.py`
      - `scripts/rule100_softmax_v1_audit.py`
      - `data/processed/rule100_softmax_v1_summary.json`
      - `data/processed/rule100_softmax_v1_comparison.csv`
      - `data/processed/rule100_softmax_v1_sample_output.csv`
      - `data/processed/rule100_softmax_v1_cash_allocation.csv`
      - `data/processed/rule100_softmax_v1_history.csv`

[Rule100 Softmax v1.1 Research Contract - 2026-05-12]
    - Objective:
      - keep v1 frozen while correcting the research-only v1.1 artifact, coverage, and dashboard-test contracts.
    - Product behavior:
      - v1.1 does not replace the active Rule of 100 runtime path and does not mutate the lifecycle event log, position memory, provider data, broker path, alerts, ranking, or scoring;
      - active v1.1 artifacts are `rule100_softmax_v1_1_comparison.csv` and `rule100_softmax_v1_1_summary.json` only;
      - stale `rule100_softmax_v1_1_history.csv` is retired to `rule100_softmax_v1_1_history.retired.csv` and must not be treated as current;
      - approved factor coverage is group-based: demand, inventory/supply, moat/pricing, and capital discipline;
      - alternate columns inside capital discipline count once, not twice.
    - Formula:
      - `coverage_i = factor_present_count_i / 4`;
      - `factor_strength_i = mean_available_group_percentile_i * coverage_i + 0.50 * (1 - coverage_i)`;
      - if no groups are present, `factor_strength_i = 0.50`.
    - Evidence:
      - `.venv\Scripts\python -m pytest tests\test_rule100_softmax_v1_1.py tests\test_policy_target_timeline_apptest.py tests\test_rule100_softmax.py tests\test_position_lifecycle.py tests\test_dash_1_page_registry_shell.py -q` PASS, 61 passed;
      - `AppTest.from_file("dashboard.py")` route regression proves TSM 2026-05-11 renders target 0%, event weight 10%, cash 80%, and `tighten_below_hold_threshold`.

[Optimizer History Diagnostics Split - 2026-05-15]
    - Objective:
      - make optimizer universe price-readiness diagnostics unambiguous without changing eligibility.
    - Product behavior:
      - `Missing History` means no local price series or too few local observations;
      - `Stale Endpoint` means sufficient observations exist but the local latest price date is stale versus the required endpoint;
      - Universe Audit exposes `Latest Price Date` for stale endpoint rows.
    - Boundary:
      - no provider ingestion, canonical market-data write, price repair, eligibility relaxation, ranking, scoring, recommendation, alert, broker behavior, or live trading.
    - Evidence:
      - `.venv\Scripts\python -m py_compile views\optimizer_view.py strategies\portfolio_universe.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` PASS;
      - `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` PASS, 62 passed.

[V2 PEAD Calendar-Time Inference Method Gate - 2026-06-21]
    - Objective:
      - approve one bounded primary inference method before any estimator implementation or alpha claim.
    - Product behavior:
      - future M1B may publish a read-only, lineage-bound single-factor calendar-time intercept for a gross equal-weight Q5-minus-Q1 sample only after terminal M1A Reviewer C recheck passes;
      - existing daily cohort HAC remains null and quarterly remains descriptive-only;
      - no dashboard alpha verdict or strategy promotion is authorized.
    - Boundary:
      - no code, tests, provider access, data artifact, evidence JSON mutation, ranking/scoring, alert, recommendation, broker/order path, staging, or commit occurred in M1A.
      - terminal M1A SAW remains BLOCK pending independent Reviewer C count recheck.
    - Evidence:
      - `docs/phase_brief/v2-pead-alpha-inference-methodology-gate.md`.
