# SAW Report - Phase 20 Closeout Round 4

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase20-brief.md`

## Scope and Ownership
- Round scope: finalize Phase 20 closure package (lock formulas, consolidate evidence ledger, publish PM handover + new-context packet, and run phase-end validations).
- RoundID: `R20_CLOSEOUT_R4_20260222`
- ScopeID: `S20_CLOSEOUT_DOCS_LOCK_AND_VALIDATION`
- Implementer: Codex (this agent)
- Reviewer A (strategy/regression): subagent `019c8685-b753-7a11-89e6-4b7d74313ec3`
- Reviewer B (runtime/ops replay): subagent `019c8681-631f-7a33-97d8-ef7ddb504c5d`
- Reviewer C (data/perf integrity): subagent `019c868a-e078-7991-a330-57f7db035118`
- Ownership check: implementer and reviewers are different agents -> PASS.

## Acceptance Checks
- CHK-P20-01: Phase 20 brief closure rewrite -> PASS.
- CHK-P20-02: Formula registry update in notes -> PASS.
- CHK-P20-03: Decision log closure entry appended -> PASS.
- CHK-P20-04: Lessons loop entry appended -> PASS.
- CHK-P20-05: PM handover doc published -> PASS.
- CHK-PH-01: Full regression `.venv\Scripts\python -m pytest -q` -> FAIL (6 tests).
- CHK-PH-02: Runtime smoke `.venv\Scripts\python launch.py --help` -> PASS.
- CHK-PH-03: End-to-end replay (implementer + Reviewer B independent run) -> PASS (matching exit code + metrics + row counts).
- CHK-PH-04: Data integrity and atomic-write verification -> PASS.
- CHK-PH-05: Docs-as-code gate (brief + notes + decision + lessons + handover) -> PASS.

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Phase-end hard gate not satisfied because full regression has 6 failing tests. | Resolve failing tests and rerun full suite before final PASS closure. | Implementer | Open |
| High | Post-lock provenance risk: closure formulas were relocked in code, but no fresh 5-year run was executed in this round to bind evidence to new lock state. | Run fresh 2020-01-01..2024-12-31 replay on locked code and publish lock-era artifacts. | Implementer | Open |
| Medium | `docs/notes.md` still carries an older 10-feature geometry contract section that can conflict with current lock narrative. | Mark old section superseded and add effective-date tag to current lock section. | Implementer | Open |
| Medium | Closeout summary JSON contains `NaN` (`mean_cash_pct_red`), which is non-standard JSON for strict parsers. | Coerce non-finite to `null` before `_atomic_json_write`. | Implementer | Open |
| Low | Freshness is currently inferred by file mtime; no explicit `generated_at_utc` field in summary payload. | Add `generated_at_utc` in summary payload and handover evidence references. | Implementer | Open |

## Scope Split Summary
- in-scope findings/actions:
  - closure docs/log updates completed;
  - replay evidence completed;
  - full regression failure remains unresolved and blocks PASS close;
  - lock-state provenance rerun deferred.
- inherited out-of-scope findings/actions:
  - existing SDM/ticker-pool test fragility from prior rounds remains part of broader test stabilization backlog.

## Verification Evidence
- Full regression:
  - `.venv\Scripts\python -m pytest -q` -> FAIL (6 tests):
    - `tests/test_assemble_sdm_features.py::test_assemble_features_cyclesetup_formula`
    - `tests/test_company_scorecard.py::test_phase20_conviction_support_proximity_is_lagged`
    - `tests/test_phase20_full_backtest_loader.py::test_load_features_window_dual_read_merges_sdm`
    - `tests/test_ticker_pool.py::test_rank_ticker_pool_emits_contract_columns`
    - `tests/test_ticker_pool.py::test_rank_ticker_pool_anchor_injected_prioritizes_anchor_names`
    - `tests/test_ticker_pool.py::test_rank_ticker_pool_hierarchical_imputation_preserves_cross_section`
- Runtime smoke:
  - `.venv\Scripts\python launch.py --help` -> PASS.
- Replay (implementer):
  - `.venv\Scripts\python scripts/phase20_full_backtest.py --start-date 2024-01-01 --end-date 2024-03-31 --allow-missing-returns --option-a-sector-specialist ...phase20_closeout_impl_*` -> exit `1` with `ABORT_PIVOT` by gate enforcement.
- Replay (Reviewer B independent):
  - same command with `...phase20_closeout_revB_*` -> exit `1` with matching decision/metrics/row counts.
- Data integrity:
  - atomic helpers confirmed at `scripts/day5_ablation_report.py` (`_atomic_csv_write`, `_atomic_json_write`, `os.replace`).
  - replay artifact row counts match impl vs reviewer B (`delta=1`, `cash=61`, `top20=61`, `sample=40`, `crisis=4`).
  - replay memory telemetry peak ~`263.27 MB`.

## Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/phase_brief/phase20-brief.md` | Rewrote stale Round-3 brief into formal Phase 20 closure brief with lock formulas and empirical ledger. | A reviewed |
| `docs/handover/phase20_handover.md` | Added PM handover artifact with formula register, logic chain, evidence matrix, and new-context packet. | B/C reviewed |
| `docs/notes.md` | Added explicit Phase 20 closure formulas and source-path register. | A reviewed |
| `docs/lessonss.md` | Added closure-round lesson for lock-state drift guardrail. | A reviewed |
| `docs/decision log.md` | Added D-115 Phase 20 closeout governance record. | A reviewed |
| `strategies/ticker_pool.py` | Restored Option A cyclical-trough centroid ranker formula in `_conviction_cluster_score`. | A reviewed |
| `data/processed/phase20_closeout_impl_*` | Implementer replay evidence artifacts for CHK-PH-03. | B/C reviewed |
| `data/processed/phase20_closeout_revB_*` | Reviewer-B independent replay evidence artifacts for CHK-PH-03. | B/C reviewed |

## Phase-End Block
- PhaseEndValidation: BLOCK
- PhaseEndChecks:
  - CHK-PH-01: BLOCK
  - CHK-PH-02: PASS
  - CHK-PH-03: PASS
  - CHK-PH-04: PASS
  - CHK-PH-05: PASS

## Handover Block
- HandoverDoc: `docs/handover/phase20_handover.md`
- HandoverAudience: PM

## New-Context Block
- ContextPacketReady: PASS
- ConfirmationRequired: YES

Open Risks:
- Full regression remains red and blocks phase-end PASS closure.
- Lock-state provenance rerun for 5-year window is still pending on current formula lock.
- Strict-JSON compatibility issue (`NaN`) remains unresolved in summary writer.

Next action:
- Fix failing tests and rerun `pytest -q`, then execute a fresh 2020-2024 locked-formula replay and republish close artifacts before requesting final phase PASS.

SAW Verdict: BLOCK
ClosurePacket: RoundID=R20_CLOSEOUT_R4_20260222; ScopeID=S20_CLOSEOUT_DOCS_LOCK_AND_VALIDATION; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=full regression red plus lock-provenance replay pending and strict-json nan issue; NextAction=fix tests rerun full suite then rerun 2020-2024 locked replay and republish closure artifacts
ClosureValidation: PASS
SAWBlockValidation: PASS
