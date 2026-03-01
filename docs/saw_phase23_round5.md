SAW Round Report

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource | Domains: Data, Strategy, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase23-brief.md

RoundID: R23_D1_20260222_R5
ScopeID: phase23_step6_action2_manifold_swap
Scope: Execute Action 2 manifold swap (daily SDM broadcast + dual-read adapter + BGM geometry isolation) and validate runtime smoke.

Top-Down Snapshot
L1: SDM Ingestion Engine
L2 Active Streams: Data, Backend, Ops
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Data
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                                                   |
+--------------------+------------------------------------------------------------+--------+--------------------------------------------------------------+
| Planning           | Boundary=A2 files only; Owner/Handoff=Codex->SAW; AC=CHKs | 100/100| 1) Keep medium open risks tracked [80/100]: feed+memory hardening |
| Final Verification | Tests+smoke+SAW reconciliation completed                   | 96/100 | 1) Proceed to next phase wiring after user sign-off [85/100] |
+--------------------+------------------------------------------------------------+--------+--------------------------------------------------------------+

Acceptance Checks
- CHK-01: Daily SDM forward-fill expansion implemented in assembler (`_expand_fundamentals_daily`) -> PASS
- CHK-02: Industry median precompute (`ind_*`) implemented in assembler -> PASS
- CHK-03: `CycleSetup` interaction (`yield_slope_10y2y * rmw * cma`) implemented in assembler -> PASS
- CHK-04: Dual-read adapter merges `features.parquet` + `features_sdm.parquet` on `[date, permno]` with date normalization -> PASS
- CHK-05: SDM overlay precedence fixed so SDM wins on overlapping columns -> PASS
- CHK-06: BGM geometry feature set restricted to SDM/macro-only and risk leak asserts added -> PASS
- CHK-07: Risk layer preserved in scorecard sizing/governor path; geometry receives lagged SDM/macro manifold fields -> PASS
- CHK-08: Validation evidence complete (pytest + smoke + artifact write + docs updates) -> PASS

Ownership Check
- Implementer: explorer `019c84de-e027-76c2-a604-bb859e39bb28`
- Reviewer A: explorer `019c84de-e043-7720-b8a0-79d2a26efacb`
- Reviewer B: explorer `019c84de-e056-7041-95d8-687a0421aed9`
- Reviewer C: explorer `019c84de-e068-73f1-9fe2-d319e50aac16`
- Independence check: PASS

Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | SDM overlay precedence in dual-read adapter could let base features shadow manifold fields | Changed merge overlay to `merged[c] = merged[c_sfx].combine_first(merged[c])`; added overlap regression assertion in loader test | Codex-main | Resolved |
| Medium | Daily SDM expansion buffers per-entity frames then concatenates, creating memory pressure risk at larger universes | Keep as open hardening item; plan chunked/streaming expansion in follow-up | Data/Ops | Open |
| Medium | Upstream FRB/FF horizon caps can leave newer rows with null macro/factor manifold inputs | Retained strict tolerance telemetry + explicit warning counts; track feed refresh/gating in next ops round | Data/Ops | Open |
| Low | Geometry contract drift risk if future config adds beta/vol columns | Added assert-based token and blocklist guards in ticker-pool geometry setup | Codex-main | Resolved |

Scope Split Summary
- in-scope: all Action 2 implementation requirements were delivered and revalidated after SAW reconciliation patch.
- inherited: none.

Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| scripts/assemble_sdm_features.py | Added daily SDM expansion, industry medians, CycleSetup, kept strict 14d tolerance telemetry | Reviewed |
| scripts/phase20_full_backtest.py | Added dual-read adapter, date-key normalization, SDM-preferred overlay precedence | Reviewed |
| strategies/company_scorecard.py | Added SDM/macro manifold columns and lagged routing into ticker-pool geometry input | Reviewed |
| strategies/ticker_pool.py | Swapped geometry feature set to SDM/macro-only and added risk-leak assert guards | Reviewed |
| tests/test_assemble_sdm_features.py | Updated for daily expansion/ind medians/CycleSetup behavior | Reviewed |
| tests/test_phase20_full_backtest_loader.py | Added dual-read merge tests + SDM overlay precedence regression guard | Reviewed |
| tests/test_ticker_pool.py | Updated fixtures for new geometry fields and risk-column rejection test | Reviewed |
| docs/phase_brief/phase23-brief.md | Added Action 2 execution record and verification evidence | Reviewed |
| docs/notes.md | Added explicit Action 2 formulas and file references | Reviewed |
| docs/decision log.md | Added D-110 decision entry for manifold swap | Reviewed |
| docs/lessonss.md | Added Action 2 timezone-merge lesson entry | Reviewed |

Open Risks:
- Medium: assembler daily expansion currently holds all per-entity chunks in memory before concat.
- Medium: macro/factor feed horizon caps still produce sparse geometry availability on late rows.

Next action:
- Implement chunked daily expansion hardening and feed-horizon gating/refresh policy in the next Data/Ops round.

SAW Verdict: PASS
ClosurePacket: RoundID=R23_D1_20260222_R5; ScopeID=phase23_step6_action2_manifold_swap; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=Medium memory pressure in daily expansion and medium feed-horizon sparsity remain; NextAction=Run follow-up Data/Ops hardening for chunked expansion and feed refresh gating
ClosureValidation: PASS
SAWBlockValidation: PASS
