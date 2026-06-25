# SAW Report - V2 PEAD M6a.1 Sparse Portfolio Engine Scale Remediation

Hierarchy Confirmation: Approved | Session: inherited-project-session | Trigger: user-approved scope | Domains: quantitative-research, data-engineering, governance

## Scope

Round scope: Complete only the M6a.1 sparse-engine core: bounded DuckDB interval aggregation, integer trading-calendar indices, numeric projection/dtype guards, turnover parity, deterministic output hash, and scale tests. No M6b data-prep, provider access, data artifact mutation, UI, alpha interpretation, ranking/scoring, alert, recommendation, broker/order path, or daily-return parquet publication is included.

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE`
- `ScopeID`: `V2_PEAD_M6A_SCALE_SPARSE_PORTFOLIO_ENGINE`

## Acceptance checks

- `CHK-01`: Event-row loop, dataframe-list accumulation, and dense turnover pivot are removed from the M6a engine.
- `CHK-02`: A global `return_idx:int32` trading calendar enforces `entry_idx <= return_idx <= exit_idx` for sparse positions.
- `CHK-03`: Required-column projection uses numeric `int32` identifiers and rejects object-dtype DuckDB relations.
- `CHK-04`: Turnover matches entry, exit, overlapping-cohort, and final trade-to-zero semantics.
- `CHK-05`: Full-universe synthetic smoke covers 196,638 events x 60 sessions under the configured 1024MB DuckDB cap and 60-second latency budget.
- `CHK-06`: M6 focused, M5a+M6, broader PEAD regression, compile, fail-closed CLI, and shuffled-input output-hash checks pass.
- `CHK-07`: Independent Reviewer A/B/C terminal evidence is complete for this code-change round.

## Implementer evidence

- `CHK-01`: PASS. `build_daily_portfolio_returns` retains direct DuckDB sparse aggregation; source guard rejects `itertuples`, `position_rows`, `pivot_table`, and the retired ASOF start path.
- `CHK-02`: PASS. A sorted global `return_idx:int32` calendar maps every selected event to `entry_idx/exit_idx`; no position-day output is persisted.
- `CHK-03`: PASS. Engine relations are projected, numeric-only, and object-dtype registration is rejected before DuckDB.
- `CHK-04`: PASS. Fixture locks turnover at `[1.0, 1.0, 2.0]` across entry, overlap, rebalance, and final liquidation.
- `CHK-05`: PASS. Synthetic 196,638-event x 60-session smoke produced 60 daily rows within the configured 1024MB/60-second bound.
- `CHK-06`: PASS. M6 focused 12/12; M5a+M6 16/16; broader PEAD 109/109; compile PASS; shuffled-input daily hash parity PASS; `--validate-inputs` exit 0 and `--run` exit 2 with blocked evidence and no curve.
- `CHK-07`: BLOCK. Independent Reviewer A/B/C agents were not available in this session; local evidence cannot substitute for the required terminal review gate.

## Reviewer status

- Implementer: completed code, test, compile, full-scale smoke, and CLI verification.
- Reviewer A: Unavailable for this terminal code-change rerun.
- Reviewer B: Unavailable for this terminal code-change rerun.
- Reviewer C: Prior review identified the resolved scale defect, but no independent terminal rerun against the changed implementation occurred.
- Ownership check: BLOCK — independent implementer/reviewer separation is incomplete.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | High | Required independent terminal Reviewer A/B/C evidence is absent for the changed sparse engine. | Do not close SAW or promote M6a.1 to terminal PASS until independent reviewers rerun. | Governance | Open |
| F-02 | Info | M6b strict data gates remain blocked independently of engine scale. | Preserve fail-closed behavior and keep `m6b_data_contract_ready=false`. | M6b data-prep | Open |

## Scope split summary

### In-scope

- Sparse engine replacement, turnover parity, source guard, memory-cap/latency smoke, and engine-scale evidence flags.

### Inherited / out of scope

- Dirty worktree and prior main-PR reconciliation.
- EPS vintage decision, delisting-adjusted returns, as-of tradability/liquidity screen, M6b data-prep, real equity curve, daily-return parquet, provider access, UI, alpha claims, ranking/scoring, alerts, recommendations, and broker/order paths.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `scripts/pead_m6_pit_walk_forward_equity_curve.py` | Calendar-indexed sparse DuckDB engine, numeric projection/dtype guard, deterministic hash, sparse turnover, and gate separation. | Local PASS; terminal independent review pending |
| `tests/test_pead_m6_pit_walk_forward_equity_curve.py` | Entry/exit/overlap parity, calendar/dtype static guard, shuffled-input hash parity, full-universe smoke. | Local PASS; terminal independent review pending |
| `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json` | Scale/runtime flags refreshed; data gate remains blocked. | Local PASS |
| `docs/phase_brief/v2-pead-m6-pit-walk-forward-equity-curve.md` | Scope, formula/evidence, and gate semantics refreshed. | Local PASS |
| `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md`, `docs/context/*_current.md` | Formula, decision, lesson, and current truth refresh. | Local PASS |

## Document Sorting

This report is the terminal evidence artifact for the M6a.1 code-change round. The implementation and tests are listed before evidence, phase documentation, and current-truth surfaces.

## Closure packet

ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE; ScopeID=V2_PEAD_M6A_SCALE_SPARSE_PORTFOLIO_ENGINE; ChecksTotal=7; ChecksPassed=6; ChecksFailed=1; Verdict=BLOCK; OpenRisks=Independent_Reviewer_A_B_C_terminal_rerun_missing_and_M6b_data_gates_still_blocked; NextAction=Run_independent_Reviewer_A_B_C_on_completed_sparse_engine_before_M6b_data_prep

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Independent Reviewer A/B/C terminal review is required before SAW PASS.
- Strict PIT EPS vintage, delisting-adjusted tradable returns, and full as-of tradability/liquidity data still block any M6 real-run curve.
- The checkout remains heavily dirty; no unrelated file was reverted, staged, or committed.

Next action:

Run independent Reviewer A/B/C on the sparse-engine change. After a terminal review PASS, M6b may begin only as data-prep for the independent strict data gates.

SAW Verdict: BLOCK
