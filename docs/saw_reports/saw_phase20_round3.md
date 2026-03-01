# SAW Report - Phase 20 Round 3 (Minimal Viable Salvage)
Date: 2026-02-20

Builds on prior round: `docs/saw_phase20_round2.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase20-brief.md`

RoundID: `R20_R3_MINIMAL_VIABLE_20260220`  
ScopeID: `S20_R3_TOP20_NO_LEVERAGE_GATE`

## Scope and Ownership
- Scope: execute Minimal Viable salvage (no leverage, Top-20/12, same window/cost/path), run full gate validation, and stop at decision gate.
- Owned files:
  - `docs/lessonss.md`
  - `docs/phase20-brief.md`
  - `scripts/phase20_full_backtest.py`
  - `strategies/company_scorecard.py`
  - `tests/test_company_scorecard.py`
  - `data/processed/phase20_round3_delta_vs_c3.csv`
  - `data/processed/phase20_round3_equity_curves.png`
  - `data/processed/phase20_round3_cash_allocation.csv`
  - `data/processed/phase20_round3_top20_exposure.csv`
  - `data/processed/phase20_round3_crisis_turnover.csv`
  - `data/processed/phase20_round3_summary.json`
  - `data/processed/phase20_round3_sample_output.csv`
  - `docs/saw_phase20_round3.md`
- Acceptance checks:
  - CHK-311..CHK-320.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7a49-c4a0-73b1-9fb5-b1ed4d0c394d`
- Reviewer B: `019c7a49-c4b7-7832-b6dd-34f5c152d23f`
- Reviewer C: `019c7a49-c4bf-7170-9a30-f4f05093d412`
- Independence: PASS

## Top-Down Snapshot
L1: User Priority Delivery on Stable C3 Baseline
L2 Active Streams: Backend, Data, Ops (risk)
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Minimal Viable salvage on C3 (Top20/12, no leverage)    | 99/100 | Freeze full-backtest gates         |
| Executing          | Full 2015-2024 salvage run                                | 95/100 | Generate delta metrics + equity    |
| Iterate Loop       | Reconcile vs C3 + concentration/cash checks               | 92/100 | Apply promote/abort decision       |
| Final Verification | py_compile + pytest + SAW                                 | 90/100 | Publish SAW + lock config          |
| CI/CD              | Handoff to Phase 21 advanced track if blocked             | 88/100 | Open Phase 21 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Quantitative Gate Result
- Window/cost/path: `2015-01-01` to `2024-12-31`, `5 bps`, same `engine.run_simulation` path.
- Baseline: `C3_LEAKY_INTEGRATOR_V1`
- Variant: `PHASE20_MIN_VIABLE_TOP20_NO_LEVERAGE`
- Delta (`data/processed/phase20_round3_delta_vs_c3.csv`):
  - Sharpe: `1.0141 -> 0.9363` (gate FAIL; need `>= 0.9641`)
  - Turnover annual: `11.9470 -> 68.4186` (`5.7268x`; gate FAIL; need `<= 14.3365`)
  - Ulcer: `6.2823 -> 8.2821` (gate FAIL; need `<= 6.3023`)
  - Max name weight: `6.25%` (gate PASS)
  - Herfindahl: `0.0500`
  - Mean cash in RED: `50.0%` (gate PASS)
- Crisis turnover reductions (`data/processed/phase20_round3_crisis_turnover.csv`):
  - COVID crash: `-81.36%`
  - COVID volatility: `-220.83%`
  - Inflation spike: `-451.80%`
  - Bear market: `-493.31%`
  - Crisis gate: FAIL (all windows must be `>= 75%`)
- Gate tally: `2/6`
- Decision: `ABORT_PIVOT`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Minimal Viable salvage still fails 4 of 6 promotion gates (`2/6` pass) and is not promotable. | Keep C3 lock unchanged; stop at gate. | Strategy | Open (Mandatory Abort) |
| High | Reviewer C: turnover ratio (`5.73x`) and crisis reductions remain deeply negative, blocking promotion by contract. | Reduce turnover/cycle churn before reattempt (selection throttles or stricter trading cadence). | Strategy | Open |
| High | Reviewer C: Sharpe shortfall remains below allowed band (`0.936 < 0.964`). | Improve signal quality or reduce trading friction before next promotion attempt. | Strategy | Open |
| Medium | Reviewer B: summary does not explicitly encode allow-missing-returns mode while C3 missing cells are non-zero (`13704`). | Record execution mode/coverage tolerance in summary for ops traceability. | Ops | Open |
| Info | Reviewer A confirmed CHK-204 lag safety and no-leverage enforcement (`leverage_mult=1.0`) in sample output. | No further action. | Strategy | Closed |
| Info | Non-zero exit semantics on ABORT are now active (`return 1`), closing prior runtime high risk. | No further action. | Ops | Closed |

## Scope Split Summary
In-scope findings/actions:
- Appended Phase 20 aggressive-variant lesson row.
- Patched runner to Minimal Viable defaults (`GREEN=20`, `AMBER=12`, no leverage).
- Enforced non-zero exit on `ABORT_PIVOT`.
- Regenerated full Round 3 artifact set and halted at gate.
- Completed reviewer A/B/C passes.

Inherited out-of-scope findings/actions:
- Prior Phase 20 Round 2 unresolved promotion/deployment items remain inherited and tracked in `docs/saw_phase20_round2.md`.

## Document Changes Showing
- `docs/lessonss.md` - appended 2026-02-20 Phase 20 aggressive-variant lesson row; reviewer status: C reviewed.
- `docs/phase20-brief.md` - updated to Minimal Viable Round 3 locks and artifact contract; reviewer status: B reviewed.
- `scripts/phase20_full_backtest.py` - enforced Top-20/12, no leverage, and non-zero abort exit; reviewer status: A/B/C reviewed.
- `strategies/company_scorecard.py` - retained CHK-204 lag fix used in round execution; reviewer status: A reviewed.
- `tests/test_company_scorecard.py` - conviction helper tests remained passing after salvage changes; reviewer status: A reviewed.
- `data/processed/phase20_round3_delta_vs_c3.csv` - generated Round 3 full-run deltas.
- `data/processed/phase20_round3_equity_curves.png` - generated Round 3 equity overlay.
- `data/processed/phase20_round3_cash_allocation.csv` - generated Round 3 cash allocation evidence.
- `data/processed/phase20_round3_top20_exposure.csv` - generated Round 3 concentration evidence.
- `data/processed/phase20_round3_crisis_turnover.csv` - generated Round 3 crisis-turnover evidence.
- `data/processed/phase20_round3_summary.json` - generated Round 3 decision and gate summary.
- `data/processed/phase20_round3_sample_output.csv` - generated Round 3 sample ticker output.
- `docs/saw_phase20_round3.md` - canonical SAW closure for this round.

## Check Results
- CHK-311: PASS (lesson row appended)
- CHK-312: PASS (phase20 brief updated to Minimal Viable spec)
- CHK-313: PASS (runner patched to no leverage and Top-20/12)
- CHK-314: PASS (non-zero ABORT exit enforced)
- CHK-315: PASS (all Round 3 artifacts generated)
- CHK-316: FAIL (6-gate promotion contract not met)
- CHK-317: PASS (`py_compile` + `pytest tests/test_company_scorecard.py`)
- CHK-318: PASS (reviewer A/B/C passes completed)
- CHK-319: PASS (SAW publication complete)
- CHK-320: FAIL (in-scope Critical/High findings unresolved)

ChecksTotal: 10  
ChecksPassed: 8  
ChecksFailed: 2

SAW Verdict: BLOCK

Open Risks:
- Promotion remains blocked due to Sharpe, turnover, ulcer, and crisis gates.
- C3 baseline still relies on missing-return override mode in this comparable run.

Next action:
- Lock fallback as `C3 + conviction rating + cash governor` only (no concentration/leverage uplift), then open Phase 21 advanced-math track.

ClosurePacket: RoundID=R20_R3_MINIMAL_VIABLE_20260220; ScopeID=S20_R3_TOP20_NO_LEVERAGE_GATE; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=round3 still fails sharpe turnover ulcer and crisis gates with baseline override dependency; NextAction=lock c3 plus conviction and cash governor only then hand off to phase21 advanced track

ClosureValidation: PASS
SAWBlockValidation: PASS
