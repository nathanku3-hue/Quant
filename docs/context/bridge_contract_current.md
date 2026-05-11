# Bridge Contract - Current

Status: Current integration bridge
Authority: advisory-only PM/planner bridge. This file does not authorize live trading, broker automation, promotion, provider ingestion, strategy search, candidate ranking, candidate scoring, candidate validation, alerts, dashboard content redesign, macro scoring, factor scoring, or scope widening.
Purpose: connect Quant's technical state back to product/system truth after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

- `SYSTEM_DELTA`: `Dashboard unified parquet data load is now wrapped in st.cache_resource and keyed by processed/static parquet file signatures.`
- `PM_DELTA`: `Normal Streamlit widget reruns should no longer pay the verified ~8s DuckDB/parquet wide-frame load when source data has not changed.`
- `DATA_DELTA`: `Cache invalidation tracks source parquet resolved path, mtime_ns, and size for price, patch, macro/liquidity, ticker, fundamentals, calendar, and sector-map inputs.`
- `CLOSURE_DELTA`: `Focused compile/tests, portfolio regressions, full pytest, Streamlit HTTP smoke, context validation, and independent SAW Implementer/Reviewer A/B/C passes completed.`
- `OPEN_DECISION`: `Hold or separately measure the alpha-engine daily loop and scanner financial-statement cache follow-ups.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_alpha_backtest_runtime_or_scanner_financial_cache.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, optimizer objective change, or scanner rule change is authorized.`

## Latest Addendum - Dashboard Scanner Testability Hardening

- `SYSTEM_DELTA`: `Dashboard scanner deterministic math now lives in strategies/scanner.py with focused boundary-value tests; dashboard.py preserves provider/cache/persistence ownership and delegates enrichment.`
- `PM_DELTA`: `Scanner labels and tactical fields are more regression-resistant without changing product semantics or authorizing new recommendations.`
- `TEST_DELTA`: `Scanner formula tests, strategy/config/ETL coverage, and the process guardrail passed in the focused suite.`
- `CLOSURE_DELTA`: `Focused compile, 46-test affected suite, and full pytest passed.`
- `OPEN_DECISION`: `Hold, run longer full regression, or continue the next review section.`
- `RECOMMENDED_NEXT_STEP`: `continue_review_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, scanner semantic change, strategy search, ranking, scoring policy change, alert, broker call, dashboard redesign, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Dashboard Architecture Safety Slice

- `SYSTEM_DELTA`: `PID liveness probing is centralized in utils.process.pid_is_running; dashboard/updater/parameter-sweep/release-controller/phase16 wrappers delegate to it.`
- `PM_DELTA`: `The dashboard and runtime lock paths are safer on Windows without changing product behavior.`
- `UI_DELTA`: `dashboard.py now uses one modular-strategy matrix initializer, delegates portfolio price cleanup to core.data_orchestrator.clean_price_frame, and refuses to spawn a second backtest when a PID file points to a live process.`
- `CLOSURE_DELTA`: `Focused compile/tests and HTTP smoke passed; full pytest was attempted but timed out after 304 seconds, so closure relies on affected-suite evidence plus SAW review.`
- `OPEN_DECISION`: `Hold or continue to Section 2 Code Quality review.`
- `RECOMMENDED_NEXT_STEP`: `continue_code_quality_review_section_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, dashboard content redesign, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

- `SYSTEM_DELTA`: `/portfolio-and-allocation` optimizer rendering now has Streamlit AppTest coverage, UI-to-SLSQP bound coverage, display-only Parquet overlay cache, copy-safe overlay scaling cache, and cached optimizer reruns.`
- `PM_DELTA`: `The Portfolio & Allocation surface is more reliable and responsive without changing product semantics or allocation policy.`
- `DATA_DELTA`: `Recent close overlays are cached under data/runtime_cache/optimizer_live_overlay as display-only Parquet files with temp->replace writes; cold misses schedule background refresh and return local TRI prices.`
- `CLOSURE_DELTA`: `Implementation evidence and independent SAW rerun are PASS; Low runtime hygiene follow-ups are carried without blocking closure.`
- `OPEN_DECISION`: `Hold, measure next dashboard runtime bottleneck, or separately approve portfolio thesis-anchor policy planning.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck_or_approve_portfolio_thesis_anchor_policy_planning.`
- `DO_NOT_REDECIDE`: `No canonical provider ingestion, market-data write, lower-bound allocation policy, new optimizer objective, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker call, ranking, scoring, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Portfolio Data Boundary Refactor

- `SYSTEM_DELTA`: `Portfolio Optimizer selected-stock display freshness and strategy-metrics parsing are now data-orchestrator responsibilities rather than Streamlit view responsibilities.`
- `PM_DELTA`: `The product keeps the same Portfolio & Allocation behavior while reducing UI/provider coupling on the approved DASH-2 freshness path.`
- `DATA_DELTA`: `core/data_orchestrator.py owns close extraction, duplicate-safe local TRI overlay scaling/stitching, stale-while-revalidate display cache behavior, scheduler fail-soft handling, and data/backtest_results.json metrics parsing; views/optimizer_view.py no longer imports yfinance or parses that JSON file.`
- `CLOSURE_DELTA`: `SAW rerun is PASS after reconciling partial live overlay preservation, stale session-state clearing, duplicate anchor dates, stale cache semantics, and scheduler submit failure.`
- `OPEN_DECISION`: `Approve PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING, request more hygiene, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold.`
- `DO_NOT_REDECIDE`: `No canonical provider ingestion, market-data write, optimizer objective change, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker call, ranking, scoring, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

- `SYSTEM_DELTA`: `Optimizer-core diagnostics are now implemented as a structured reporting layer without changing the approved objective or accepting lower-bound policy.`
- `PM_DELTA`: `The product can now explain infeasible caps, forced equal weight, SLSQP failures, active bounds, and fallback allocations without silently treating fallback as optimized output.`
- `CLOSURE_DELTA`: `SAW PASS after reconciling the data-integrity finding: non-finite diagnostic weights now fail closed as errors and cannot be reported as optimized.`
- `OPEN_DECISION`: `Approve PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING, request more diagnostics, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold.`
- `DO_NOT_REDECIDE`: `MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new optimizer objective, scanner rules, manual override, provider ingestion, broker calls, alerts, and replay behavior remain blocked.`

## Latest Addendum - Optimizer Core Policy Audit

- `SYSTEM_DELTA`: `Optimizer-core lower-bound/SLSQP policy is now separated from the universe-construction closure into its own audit artifacts.`
- `PM_DELTA`: `The quarantined diff is rejected as-is; the product can discuss optimizer constraints without silently accepting model math.`
- `OPEN_DECISION`: `Approve a future optimizer-core implementation round, request revisions, or hold.`
- `RECOMMENDED_NEXT_STEP`: `hold_optimizer_core_implementation_until_policy_approval.`
- `DO_NOT_REDECIDE`: `Universe eligibility, WATCH investability, MU conviction, Black-Litterman, scanner behavior, provider ingestion, broker calls, alerts, and new objectives remain blocked.`

## Latest Addendum - Portfolio Universe Closure Quarantine

- `SYSTEM_DELTA`: `Portfolio Universe Construction Fix is closed as PASS with optimizer-core lower-bound/SLSQP math quarantined out of scope.`
- `PM_DELTA`: `The allocation-universe patch remains mechanical: universe construction, eligibility, diagnostics, labels, tests, audit UI, and contract docs only.`
- `QUARANTINE_DELTA`: `Dirty strategies/optimizer.py lower-bound/SLSQP changes were saved to docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch and reverted from the active closure.`
- `OPEN_DECISION`: `Open OPTIMIZER_CORE_POLICY_AUDIT or hold; do not accept optimizer-core math changes without separate policy, tests, and SAW.`
- `RECOMMENDED_NEXT_STEP`: `open_optimizer_core_policy_audit_or_hold.`
- `DO_NOT_REDECIDE`: `No MU hard floor, conviction mode, WATCH investability, Black-Litterman, manual override, scanner rewrite, provider ingestion, broker call, alert, or new objective is authorized.`
- `PROVENANCE_ANCHOR`: `D-353 / Phase 64 provenance and validation gates remain closed; evidence anchor includes docs/phase_brief/phase64-brief.md and R64.1 dependency hygiene.`

## Latest Addendum - Portfolio Universe Construction Fix

- `PORTFOLIO_DELTA`: `Portfolio Optimizer defaults now come from build_optimizer_universe(...) rather than df_scan display order or selected_tickers[:20].`
- `ELIGIBILITY_DELTA`: `ENTER STRONG BUY and ENTER BUY are eligible; WATCH is research-only; EXIT/KILL/AVOID/IGNORE are excluded by default.`
- `DIAGNOSTIC_DELTA`: `Universe Audit now reports included/excluded rows, missing ticker mappings, local price-history failures, and max-weight feasibility or equal-weight-boundary risk.`
- `NO_CHANGE`: `No MU hard floor, Black-Litterman, conviction mode, thesis anchor sizing, manual override, scanner rewrite, provider ingestion, broker call, alert, or new objective was added.`
- `EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` PASS; scoped compile PASS for `strategies/portfolio_universe.py`, `views/optimizer_view.py`, and `dashboard.py`; browser smoke PASS on port `8503`.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

- `DASHBOARD_DELTA`: `Portfolio & Allocation now keeps Portfolio Optimizer top-level, renders YTD Performance below it, calculates portfolio YTD from current optimizer weights, and shows SPY/QQQ comparison metrics.`
- `DATA_DELTA`: `Selected stock and benchmark prices use an in-memory yfinance adjusted-close freshness overlay for runtime display only; no canonical provider ingestion or file write was added.`
- `NO_CHANGE`: `No broker call, alert, candidate ranking, candidate scoring, factor-scout integration, candidate-card merge, or canonical evidence change was added.`
- `EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` PASS; `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py -q` PASS; scoped compile PASS; browser check at `http://127.0.0.1:8502/portfolio-and-allocation` showed optimizer before YTD and prices through `2026-05-08`.

## Header

- `BRIDGE_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-bridge`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `D-353/R64.1/F/G0/G1/G2/G3/G4/G5/G6/G7/G7.1/G7.1A/G7.1B/G7.1C/G7.1D/G7.1E/G7.1F/G7.1G/G7.2/G7.3/G7.4/G8/G8.1/G8.1A/G8.1B-R/DASH-1 complete + G8.2 current`
- `STATUS`: `phase65-g8-2-system-scouted-candidate-card-current`
- `OWNER`: `PM / Architecture Office`

## Live Truth Now

- `SYSTEM_NOW`: `Quant has two candidate-card-only research objects: MU from human nomination and MSFT from the governed LOCAL_FACTOR_SCOUT output.`
- `ACTIVE_SCOPE`: `G8.2 is candidate-card-only Data + Docs/Ops work: one MSFT static card, manifest, policy, handover, focused tests, truth surfaces, and SAW.`
- `BLOCKED_SCOPE`: `New scout outputs, DELL/AMD/LRCX/ALB cards, rankings, scores, thesis validation, buy/sell/hold, buying range, dashboard merge, provider ingestion, alerts, and broker behavior remain blocked.`

## What Changed This Round

- `SYSTEM_DELTA`: `MSFT can now move from governed LOCAL_FACTOR_SCOUT intake to a structured candidate-card-only research object without becoming validated alpha.`
- `PRODUCT_DELTA`: `Terminal Zero now proves both intake-to-card paths: human-nominated MU and pipeline-scouted MSFT.`
- `DATA_DELTA`: `Added one static MSFT candidate card and manifest; no canonical market-data write or provider ingestion occurred.`
- `GOVERNANCE_DELTA`: `Candidate-card validation now rejects factor-score leakage and optional governance flags must remain true when present.`
- `DASHBOARD_DELTA`: `No dashboard runtime change. Existing MSFT dashboard rows are legacy runtime output, not the G8.2 card.`
- `NO_CHANGE`: `No new scout output, no score, no rank, no actionability, no buying range, no alert, no broker call, no provider call, no dashboard merge, and no cards for user-seeded tickers.`

## PM / Product Delta

- `STRONGER_NOW`: `The discovery proof is more complete because a system-scouted intake item can become a governed research object.`
- `WEAKER_NOW`: `Dashboard semantics are still split: legacy runtime rows can show action-shaped labels while candidate cards remain file-backed status objects only.`
- `STILL_UNKNOWN`: `Whether the next move should be G9 market-behavior signal card, G8.3 user-seeded candidate card, a dashboard card reader, or hold.`

## Planner Bridge

- `OPEN_DECISION`: `Approve G9 one market-behavior signal card, approve G8.3 one user-seeded candidate card, approve dashboard card reader/status shell, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold.`
- `WHY_THIS_NEXT`: `G8.2 completed the system-scouted intake-to-card proof; the next safe choices either add one evidence signal, test the user-seeded card path, or expose cards as status-only dashboard objects.`
- `NOT_RECOMMENDED_NEXT`: `Do not start ranking, scoring, buying range, provider ingestion, alerts, broker paths, or merge MSFT into legacy dashboard action labels.`

## Locked Boundaries

- `DO_NOT_REDECIDE`:
  - `MSFT is the only G8.2 ticker because it is the sole governed LOCAL_FACTOR_SCOUT output.`
  - `MU and MSFT are the only candidate cards after G8.2.`
  - `Candidate-card-only does not mean validated, actionable, ranked, scored, or recommended.`
  - `The existing dashboard MSFT row at runtime is not the G8.2 candidate card.`
  - `Future dashboard integration must be status-only unless separately approved.`
  - `No live trading, broker automation, alerting, ranking, scoring, recommendation, or provider ingestion is authorized.`

## Evidence Used

- `opportunity_engine/candidate_card_schema.py`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
- `data/discovery/local_factor_scout_output_tiny_v0.json`
- `tests/test_g8_2_system_scouted_candidate_card.py`
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
- `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`

## Open Risks

- `Inherited dirty dashboard runtime worktree remains visible in git status.`
- `Legacy dashboard rows still use action-shaped labels that are separate from candidate cards.`
- `Factor model validation remains future debt before predictive or ranked use.`
- `GodView provider, options-license, ownership, insider, and market-behavior gaps remain open.`
