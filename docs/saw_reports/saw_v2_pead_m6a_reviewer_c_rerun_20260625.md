# SAW Report - V2 PEAD M6a Reviewer C Rerun

Hierarchy Confirmation: Approved | Session: inherited-project-session | Trigger: inherited reviewer-only rerun | Domains: quantitative-research, data-engineering, governance

## Scope

Round scope: Reviewer C rerun of M6a data-integrity and performance-path evidence only. No source code, data artifact, provider, strategy, or UI change was made.

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-REVIEWER-C-RERUN`
- `ScopeID`: `V2_PEAD_M6A_REVIEWER_C_DATA_INTEGRITY_AND_PERFORMANCE_RERUN`

NoChangeReason: This round reviewed the existing M6a implementation and canonical blocked evidence; it did not alter implementation or published evidence.

## Acceptance checks

- `CHK-01`: Focused M6a test suite passes.
- `CHK-02`: M5a plus M6a focused regression passes.
- `CHK-03`: Broader PEAD D1/D2/D2B/D3/event-study/M5a/M6 regression passes.
- `CHK-04`: M6a module compiles.
- `CHK-05`: Live contract replay exactly matches canonical evidence; real `--run` remains fail-closed, emits no curve, and does not mutate canonical evidence.
- `CHK-06`: M6a portfolio engine satisfies the repository vectorization and bounded-memory performance requirements for a full-universe future run.
- `CHK-07`: Independent terminal Reviewer A/B/C evidence is complete for M6a closure.

## Reviewer C evidence

- Focused M6a tests: PASS, 7/7.
- M5a plus M6a tests: PASS, 11/11.
- Broader PEAD slice: PASS, 104/104.
- Module compile: PASS.
- Live replay: PASS. The regenerated `mode=run` evidence exactly matched the canonical JSON; the temporary real `--run` returned exit code `2`, emitted neither daily returns nor an equity curve, and the canonical JSON SHA256 was unchanged at `aabd78d26f696ba780d605c0d225e626ecbc5c5d65e7c0ad647b19b378654b7f`.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | High | `build_daily_portfolio_returns` expands one DataFrame per selected event and then materializes a dense date-by-security pivot for turnover. That violates the repository vectorization rule and is not bounded for the full-universe path represented by 233,586 events and 14,015,160 D2B rows. | Do not wire this engine to real M6 inputs. Before any real curve, replace the per-event loop and dense pivot with a bounded/vectorized or DuckDB-based position and turnover path; add an active-scale memory/runtime acceptance test. | M6b/M6 real-run | Open |
| F-02 | High | Reviewer C is now rerun, but independent Reviewer A and Reviewer B terminal evidence remains absent; M6a cannot claim terminal SAW closure. | Run independent Reviewer A and B, or obtain explicit owner acceptance to proceed with local evidence only. | Governance | Open |
| F-03 | Low | All M6a source, test, evidence, brief, and original SAW files are currently untracked in the dirty worktree, so Git does not provide a committed baseline for provenance. | Preserve the current files; reconcile/stage only in a separate approved Git round. | Repo hygiene | Open inherited |

## Scope split summary

### In scope

- M6a fail-closed input-contract replay.
- Canonical-evidence consistency and no-mutation check.
- Portfolio-engine data-integrity and performance-path review.

### Inherited / out of scope

- Dirty worktree and unresolved prior main-PR reconciliation.
- Provider access, first-public EPS data, CRSP/delisting data, tradability screens, alpha interpretation, ranking/scoring, alerts, recommendations, and broker/order paths.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_v2_pead_m6a_reviewer_c_rerun_20260625.md` | New reviewer-only rerun evidence; no implementation or canonical evidence mutation. | Reviewer C BLOCK |

## Document Sorting

Reviewer evidence is a terminal review artifact for this no-code rerun. No product, strategy, data, provider, or UI document changed.

## Closure packet

ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6A-REVIEWER-C-RERUN; ScopeID=V2_PEAD_M6A_REVIEWER_C_DATA_INTEGRITY_AND_PERFORMANCE_RERUN; ChecksTotal=7; ChecksPassed=5; ChecksFailed=2; Verdict=BLOCK; OpenRisks=Unbounded_full_universe_engine_and_missing_independent_Reviewer_A_B; NextAction=Keep_M6a_blocked_and_scope_M6b_data_prep_with_a_bounded_real_run_engine_precondition

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- M6a must not emit a real daily-return parquet or equity curve while the full-universe engine remains unbounded.
- Independent Reviewer A and Reviewer B terminal evidence is still absent.
- Strict EPS vintage, delisting-adjusted tradable returns, and a full as-of tradability/liquidity screen remain unavailable.

Next action:

Keep M6a fail-closed. M6b may be scoped as data-prep only, but its acceptance criteria must include a bounded/vectorized real-run engine before any strict-input curve is enabled.

SAW Verdict: BLOCK
