# SAW Report - Phase 20 Round 2 (Full 2015-2024 Validation)
Date: 2026-02-20

Builds on prior round: `docs/saw_phase19_7_round1.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase20-brief.md`

RoundID: `R20_R2_FULLRUN_20260220`  
ScopeID: `S20_FULL_2015_2024_DELTA_GATE`

## Scope and Ownership
- Scope: apply CHK-204 lookahead fix, run full Phase 20 simulation against locked C3 baseline, publish gate evidence, and stop at decision gate.
- Owned files:
  - `docs/phase20-brief.md`
  - `strategies/company_scorecard.py`
  - `tests/test_company_scorecard.py`
  - `scripts/phase20_full_backtest.py`
  - `data/processed/phase20_round2_sample_output.csv`
  - `data/processed/phase20_full_delta_vs_c3.csv`
  - `data/processed/phase20_full_equity_curves.png`
  - `data/processed/phase20_full_cash_allocation.csv`
  - `data/processed/phase20_full_top12_exposure.csv`
  - `data/processed/phase20_full_crisis_turnover.csv`
  - `data/processed/phase20_full_summary.json`
  - `docs/saw_phase20_round2.md`
- Acceptance checks:
  - CHK-301..CHK-310.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7a33-f5e6-7c33-aaa1-fab9a452b5f7`
- Reviewer B: `019c7a33-f601-7e33-adc3-3d2494acc0d5`
- Reviewer C: `019c7a33-f614-7c52-a8e1-3ec0a89ee71c`
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
| Planning           | B=Phase20 heuristics on C3; map 4 user priorities         | 99/100 | Freeze full-backtest gates         |
| Executing          | Full 2015-2024 simulation run                             | 95/100 | Generate delta metrics + equity    |
| Iterate Loop       | Reconcile vs C3 + concentration/cash protection check     | 92/100 | Apply promote/abort decision       |
| Final Verification | py_compile + pytest + SAW                                 | 90/100 | Publish SAW + lock config          |
| CI/CD              | Handoff to Phase 21 (leverage refinement + advanced track)| 88/100 | Open Phase 21 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Quantitative Gate Result
- Window/cost/path: `2015-01-01` to `2024-12-31`, `5 bps`, same `engine.run_simulation` path.
- Baseline: `C3_LEAKY_INTEGRATOR_V1`
- Variant: `PHASE20_HEURISTIC_TOP12_CASH_LEVERAGE`
- Delta summary (`data/processed/phase20_full_delta_vs_c3.csv`):
  - Sharpe: `1.0141 -> 0.8517` (gate FAIL: need `>= 0.9641`)
  - Turnover annual: `11.9470 -> 91.5265` (`7.6610x`, gate FAIL: need `<= 14.3365`)
  - Ulcer: `6.2823 -> 17.4644` (gate FAIL: need `<= 6.3023`)
  - Max name weight: `12.50%` (gate PASS: need `<= 15%`)
  - Herfindahl: `0.1875`
  - Mean cash in RED: `50.0%` (gate PASS: need `>= 40%`)
- Crisis turnover reductions (`data/processed/phase20_full_crisis_turnover.csv`):
  - COVID crash: `-162.50%`
  - COVID volatility: `-235.42%`
  - Inflation spike: `-548.05%`
  - Bear market: `-608.61%`
  - Crisis gate: FAIL (all windows must be `>= 75%`)
- Gate tally: `2/6`
- Decision: `ABORT_PIVOT`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Phase 20 promotion gates failed (`2/6`), so candidate is not promotable. | Keep C3 lock unchanged; stop at gate and pivot. | Strategy | Open (Mandatory Abort) |
| High | Script exits with code `0` even when decision is `ABORT_PIVOT`, weakening CI fail-fast enforcement. | Return non-zero when `decision != PROMOTE` after artifact write. | Ops | Open |
| Medium | `illiquid_flag` threshold in conviction helper uses full-series quantile and may leak future info. | Switch to causal thresholding (`shift(1)` + rolling/expanding quantile) and rerun artifacts. | Strategy | Open |
| Medium | Baseline run still contains `missing_active_return_cells.c3=13704` with zero-fill override enabled. | Add tolerance/strict mode enforcement and explicit offender logging before promotion attempts. | Data | Open |
| Info | CHK-204 support-proximity lag fix applied and sample output regenerated (GREEN sample shows Top-12 + leverage states). | No further action for this check. | Strategy | Closed |

## Scope Split Summary
In-scope findings/actions:
- Added Phase 20 brief and full-run backtest runner.
- Applied CHK-204 lagged support-proximity fix in conviction helper.
- Re-ran sample output and generated full artifact set.
- Executed decision gates and halted on ABORT_PIVOT.

Inherited out-of-scope findings/actions:
- Prior round governance/performance debts remain tracked in `docs/saw_phase19_7_round1.md`.

## Document Changes Showing
- `docs/phase20-brief.md` - created Phase 20 plan, locks, gates, and snapshot table; reviewer status: B reviewed.
- `strategies/company_scorecard.py` - added `build_phase20_conviction_frame` and lagged support-proximity fix; reviewer status: A/C reviewed.
- `tests/test_company_scorecard.py` - added conviction helper tests including lag behavior; reviewer status: A reviewed.
- `scripts/phase20_full_backtest.py` - created full-run simulation/gating script and artifact writer; reviewer status: A/B/C reviewed.
- `data/processed/phase20_round2_sample_output.csv` - regenerated post-fix sample output.
- `data/processed/phase20_full_delta_vs_c3.csv` - generated full-run delta/gate metrics.
- `data/processed/phase20_full_equity_curves.png` - generated log-scale equity overlay.
- `data/processed/phase20_full_cash_allocation.csv` - generated daily cash/governor allocation.
- `data/processed/phase20_full_top12_exposure.csv` - generated concentration metrics.
- `data/processed/phase20_full_crisis_turnover.csv` - generated crisis turnover gate evidence.
- `data/processed/phase20_full_summary.json` - generated run summary and final decision.
- `docs/saw_phase20_round2.md` - canonical SAW closure for this round.

## Check Results
- CHK-301: PASS (lookahead fix applied in conviction support-proximity)
- CHK-302: PASS (sample output regenerated post-fix)
- CHK-303: PASS (`scripts/phase20_full_backtest.py` created)
- CHK-304: PASS (strict signal lagging enforced: support + regime + engine execution lag)
- CHK-305: PASS (all required artifacts generated)
- CHK-306: FAIL (promotion gate criteria not met: `2/6`)
- CHK-307: PASS (`py_compile` + `pytest tests/test_company_scorecard.py`)
- CHK-308: PASS (reviewer A/B/C passes completed)
- CHK-309: PASS (SAW report published)
- CHK-310: PASS (stopped at decision gate)

ChecksTotal: 10  
ChecksPassed: 9  
ChecksFailed: 1

SAW Verdict: BLOCK

Open Risks:
- Phase 20 variant failed four core promotion gates and cannot be promoted.
- Runtime exit semantics do not yet enforce non-zero status on aborted decisions.
- Causal integrity tightening is still needed for the illiquidity threshold.
- Baseline missing-return padding remains present under `--allow-missing-returns`.

Next action:
- Keep C3 baseline locked, then run a focused Phase 20.1 stabilization pass (turnover/crisis control + causal liquidity threshold + non-zero abort exits) before any promotion retry.

ClosurePacket: RoundID=R20_R2_FULLRUN_20260220; ScopeID=S20_FULL_2015_2024_DELTA_GATE; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=phase20 failed four promotion gates plus unresolved runtime and causal-data issues; NextAction=phase20_1 stabilization pass then rerun full gate pack before promotion

ClosureValidation: PASS
SAWBlockValidation: PASS
