# V2 PEAD M6a PIT Walk-Forward Equity Curve Framework

## Mode

`EXECUTION_PACKET`

## Round

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE`
- `ScopeID`: `V2_PEAD_M6A_SCALE_SPARSE_PORTFOLIO_ENGINE`
- Scope name: `M6a.1 Sparse Portfolio Engine Scale Remediation`
- Implemented slice: `M6a input-contract and framework evidence plus a bounded sparse engine`, not a real tradable curve.
- Prior framework round: `ROUND-20260624-V2-PEAD-M6A-PIT-WALK-FORWARD-EQUITY-FRAMEWORK`; its data-contract gate remains unchanged.

## Revised plan

M6 is split into two gates because the current local artifacts support timing-PIT but not strict vintage-PIT EPS, and they do not establish a delisting-adjusted tradable return stream.

### M6a — implemented now

M6a owns:

- PIT input contract and fail-closed validation.
- Explicit distinction between timing-PIT and vintage-PIT / unrestated EPS.
- Walk-forward fold builder split on `decision_date`.
- Dollar-neutral Q5-minus-Q1 portfolio engine for strict dataframe inputs, implemented with a DuckDB sparse interval/window join, prebuilt integer trading-calendar bounds, numeric-only projected relations, deterministic compensated aggregation, and direct daily aggregation.
- Explicit nonzero cost model.
- Equity curve, CAGR, drawdown, Sharpe, turnover, exposure, and fold metrics functions.
- Evidence JSON schema and CLI gates.

M6a intentionally does not claim a real backtest when the strict input contract fails.

### M6b — deferred data-prep/run gate

M6b requires one of these EPS decisions plus return/tradability data:

- Add true first-public / unrestated EPS vintage data, or
- explicitly accept `release_date_aligned_but_restated` as best-available and keep that flag in every claim boundary.

M6b also requires:

- delisting-adjusted tradable daily returns,
- a full as-of tradability/liquidity screen,
- short/borrow assumption evidence before any tradable net CAGR claim.

## M5a interpretation carried into M6a

M5a remains a clean diagnostic pass, not net/tradable evidence.

- Gross FF3 intercept: `0.0006992875170429098` per day.
- Gross FF3 HAC t-stat: `8.975032890536228`.
- Net FF3 is identical to gross because `spread_cost_bps_per_day = 0.0`.
- M5a flags remain diagnostic-only: strict PIT EPS vintage false, delisting-adjusted returns false, tradable return source false, exact turnover model false.

## Current M6a data contract result

Current local artifacts fail closed for M6 real-run use.

- Timing PIT status: available through `rdq` / release-date alignment semantics.
- EPS vintage status: `release_date_aligned_but_restated`.
- Strict PIT EPS vintage: false.
- Tradable return source: false.
- Delisting-adjusted returns: false.
- Full M6 as-of liquidity/tradability screen: false.

Failure reasons emitted by the evidence JSON:

```text
pit_vintage_blocked
delisting_missing
tradable_return_missing
tradability_liquidity_screen_missing
```

## Files changed

- `scripts/pead_m6_pit_walk_forward_equity_curve.py`
- `tests/test_pead_m6_pit_walk_forward_equity_curve.py`
- `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`
- `docs/phase_brief/v2-pead-m6-pit-walk-forward-equity-curve.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/saw_reports/saw_v2_pead_m6a_pit_walk_forward_equity_curve_20260624.md` (prior framework evidence)
- `docs/saw_reports/saw_v2_pead_m6a_scale_sparse_portfolio_engine_20260625.md` (current scale-engine SAW evidence)

## CLI contract

```text
.venv\Scripts\python.exe scripts\pead_m6_pit_walk_forward_equity_curve.py --validate-inputs
```

Writes evidence and returns success even when blocked, because validation evidence is the product of M6a.

```text
.venv\Scripts\python.exe scripts\pead_m6_pit_walk_forward_equity_curve.py --run
```

Writes blocked evidence and exits non-zero when strict M6 inputs are missing.

## Formula registry

Daily portfolio return, for future strict input rows:

```text
daily_gross_return_t = sum_i weight_{i,t} * tradable_total_return_{i,t}
```

Cost model:

```text
one_way_turnover_cost_bps = (entry_cost_bps + exit_cost_bps) / 2 + slippage_bps
turnover_cost_t = turnover_t * one_way_turnover_cost_bps / 10000
short_borrow_cost_t = short_exposure_t * daily_short_borrow_bps / 10000
daily_net_return_t = daily_gross_return_t - turnover_cost_t - short_borrow_cost_t
```

Equity and CAGR:

```text
equity_t = equity_{t-1} * (1 + daily_net_return_t)
CAGR = (ending_equity / starting_equity) ** (365.25 / calendar_days) - 1
```

Walk-forward split rule:

```text
folds are expanding annual folds keyed on decision_date/event_date, never hindsight return dates
```

## Acceptance checks

- [x] No current-vintage EPS fallback is allowed by default.
- [x] Evidence distinguishes timing-PIT from vintage-PIT.
- [x] Current EPS label is `release_date_aligned_but_restated`.
- [x] `--validate-inputs` writes fail-closed evidence for current artifacts.
- [x] `--run` exits non-zero when strict inputs are missing.
- [x] Explicit nonzero costs are required by the framework.
- [x] Synthetic strict-input tests prove daily gross/net returns and reproducible equity metrics.
- [x] Sparse turnover parity covers entry, overlapping cohorts, exit, and final trade-to-zero liquidation.
- [x] A prebuilt global trading-calendar `return_idx:int32` enforces `entry_idx <= return_idx <= exit_idx`; no date-range interval predicate remains in the sparse join.
- [x] Projection/dtype guards retain only required engine columns, encode DuckDB identifiers as `int32`, and reject object-dtype DuckDB relations.
- [x] Canonical daily SHA-256 hash is identical across shuffled event/return input order under single-thread compensated aggregation.
- [x] No event-level Python loop, dataframe list accumulation, or dense return-date-by-security weight pivot remains in the engine.
- [x] Full-universe synthetic smoke covers 196,638 selected events x 60 sessions (11,798,280 bounded position-days) within a DuckDB 1024MB cap and a 60-second latency budget.
- [x] Evidence flags separate `m6b_real_run_wiring_allowed=true` (engine scale only) from `m6b_data_contract_ready=false` (strict data inputs still blocked).
- [x] Walk-forward folds are time-ordered by decision date.
- [x] Output remains evidence-only and emits no strategy promotion/action authority.

## Evidence

- `.venv\Scripts\python.exe -m pytest tests/test_pead_m6_pit_walk_forward_equity_curve.py -q` -> PASS, 12 tests.
- `.venv\Scripts\python.exe -m pytest tests/test_pead_m5a_multifactor_alpha_test.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q` -> PASS, 16 tests.
- `.venv\Scripts\python.exe -m pytest tests/test_pead_d1_sue.py tests/test_pead_d2_returns.py tests/test_pead_d2b_event_window_contract.py tests/test_pead_d3_benchmark_artifact.py tests/test_pead_event_study.py tests/test_pead_m5a_multifactor_alpha_test.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q` -> PASS, 109 tests.
- `.venv\Scripts\python.exe -m py_compile scripts/pead_m6_pit_walk_forward_equity_curve.py` -> PASS.
- `--validate-inputs` -> wrote `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`, status `blocked_fail_closed`.
- `--run` -> wrote blocked evidence and returned exit code `2`.

## Forbidden scope preserved

No locked D3/D2B mutation, UI, alpha-named label, ranking/scoring, recommendation, alert, broker/order path, provider access, or daily return parquet was added.

## Next action

M6a.1 in-scope core delivery is complete locally. Obtain independent Reviewer A/B/C terminal review before any M6b data-prep; M6b remains limited to its EPS-vintage, delisting-adjusted tradable-return, and full as-of tradability/liquidity gates, and no real `--run` curve is authorized before they close.
