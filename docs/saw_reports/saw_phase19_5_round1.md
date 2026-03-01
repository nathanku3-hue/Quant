# SAW Report — Phase 19.5 Round 1 (Scorecard Strengthening)
Date: 2026-02-20

Builds on prior gate closure: `docs/saw_phase21_day1.md`.

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data | FallbackSource: `docs/spec.md` + `docs/phase19-brief.md`

RoundID: `R19_5_R1_20260220`  
ScopeID: `S19_5_SCORECARD_STRENGTHENING`

## Scope and Ownership
- Scope: execute Phase 19.5 signal-strengthening sprint (docs + candidate factor sets + sprint runner), run ablation/walk-forward gates, and stop at decision gate.
- Owned files:
  - `docs/phase19-brief.md`
  - `docs/lessonss.md`
  - `strategies/factor_specs.py`
  - `strategies/company_scorecard.py`
  - `tests/test_company_scorecard.py`
  - `scripts/scorecard_strengthening_sprint.py`
  - `data/processed/phase19_5_ablation_metrics.csv`
  - `data/processed/phase19_5_delta_vs_c3.csv`
  - `data/processed/phase19_5_walkforward.csv`
  - `data/processed/phase19_5_decay_sensitivity.csv`
  - `data/processed/phase19_5_crisis_turnover.csv`
  - `data/processed/phase19_5_checks.csv`
  - `data/processed/phase19_5_summary.json`
  - `docs/saw_phase19_5_round1.md`
- Acceptance checks:
  - CHK-211..CHK-220.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c79d0-a22c-70d2-a5f8-41d3075ce0d9`
- Reviewer B: `019c79d0-a238-7e01-916c-c600a3b0d5dc`
- Reviewer C: `019c79d0-a23f-7111-8a97-a0f2eba9948d`
- Independence: PASS

## Top-Down Snapshot
L1: Alignment & Evidence Discipline (Phase 19)
L2 Active Streams: Backend, Data
L2 Deferred Streams: Frontend/UI, Ops (risk)
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Phase 19.5 signal sprint; OH=Impl→RevA/B/C; AC=CHK-211..220 | 95/100 | Freeze factor candidates + gates   |
| Executing          | New factors + validity modes + strengthening script        | 88/100 | Run ablation + walk-forward        |
| Iterate Loop       | Reconcile vs C3 baseline                                   | 85/100 | Apply new C3 lock if gates pass    |
| Final Verification | py_compile + pytest + SAW                                  | 82/100 | Publish SAW + update production_config |
| CI/CD              | Handoff to Phase 20 (joint WFO with future stops)          | 80/100 | Open Phase 20 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Quantitative Gate Result
- Selected config: `C3_PARTIAL`
- Baseline config: `C3_LOCKED`
- Window/cost/path: `2015-01-01` to `2024-12-31`, `5 bps`, same C3 engine path.
- Core deltas (`data/processed/phase19_5_delta_vs_c3.csv`):
  - Coverage: `0.5237 -> 0.9016` (`+0.3779`)
  - Spread: `1.8245 -> 1.5614` (`-0.2631`)
  - Sharpe: `1.0141 -> 1.0274` (`+0.0133`)
  - Turnover annual: `11.9470 -> 11.6066` (`0.9715x`)
  - |MaxDD|: `0.1925 -> 0.2004` (`+0.0079`)
- Gate status (`data/processed/phase19_5_summary.json`):
  - `gate_coverage_ge_80`: PASS
  - `gate_spread_ge_2_0`: FAIL
  - `gate_sharpe_ge_c3`: PASS
  - `gate_crisis_turnover_reduction_ge_70_all_windows`: FAIL
  - `gate_chk_41_48_50_51_53_group_3_of_4`: FAIL
- Gate tally: `2/5`
- Decision: `ABORT_PIVOT`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Phase 19.5 promotion gate failed (`2/5`), so sprint cannot lock new C3 baseline. | Keep abort decision and pivot to next signal-strengthening iteration. | Strategy | Open (Mandatory Pivot) |
| High | CI gating risk: script exits `0` even when decision is `BLOCK/ABORT`, allowing false green in automation. | Return non-zero exit for non-pass decisions or enforce gate in wrapper. | Ops | Open |
| High | Crisis gate robustness risk: empty crisis-frame path can evaluate as pass under `.all()` semantics. | Require explicit crisis window row-count + non-null reductions before pass. | Data/Ops | Open |
| Medium | No dedicated regression test covers `scripts/scorecard_strengthening_sprint.py` gate logic/artifact contract. | Add script-level regression fixture for gate booleans and output schema. | Backend | Open |
| Medium | CHK-47 missing value (`bear_recovery_days_c3` NaN) forces fail and weakens robustness evidence. | Extend horizon or add explicit unresolved-recovery handling contract. | Data | Open |

## Scope Split Summary
In-scope findings/actions:
- Added Phase 19.5 docs alignment and explicit lesson entry.
- Implemented candidate factor sets and preset scorecard loader.
- Added scorecard preset tests and passed suite.
- Implemented and executed sprint runner with ablation/walk-forward/decay/crisis/check artifacts.
- Reached decision gate and stopped at `ABORT_PIVOT`.

Inherited out-of-scope findings/actions:
- Prior Phase 21 high findings remain open in `docs/saw_phase21_day1.md` and are not modified in this round.

## Document Changes Showing
- `docs/phase19-brief.md` — added Phase 19.5 section, gate contract, and locked top-down snapshot table; reviewer status: B reviewed.
- `docs/lessonss.md` — appended 2026-02-20 lesson row for Day 1 stop-layer abort; reviewer status: C reviewed.
- `strategies/factor_specs.py` — added Phase 19.5 candidate factor sets (4F, 5F, rank-4F) using inventory-quality/disciplined families; reviewer status: A reviewed.
- `strategies/company_scorecard.py` — added `from_factor_preset(...)` constructor for default and Phase 19.5 presets; reviewer status: A reviewed.
- `tests/test_company_scorecard.py` — added tests for candidate set validation and preset loading; reviewer status: A/C reviewed.
- `scripts/scorecard_strengthening_sprint.py` — added sprint runner (ablation + walk-forward + decay + crisis + gate summary); reviewer status: B/C reviewed.
- `data/processed/phase19_5_ablation_metrics.csv` — ablation results for 7 configs.
- `data/processed/phase19_5_delta_vs_c3.csv` — selected-vs-baseline delta metrics.
- `data/processed/phase19_5_walkforward.csv` — walk-forward stress outputs.
- `data/processed/phase19_5_decay_sensitivity.csv` — selected config decay sensitivity.
- `data/processed/phase19_5_crisis_turnover.csv` — crisis-window turnover deltas.
- `data/processed/phase19_5_checks.csv` — CHK-39..54 status for selected config.
- `data/processed/phase19_5_summary.json` — canonical gate tally and decision.

## Check Results
- CHK-211: PASS (Phase 19.5 section + snapshot table added in brief)
- CHK-212: PASS (requested lesson row appended)
- CHK-213: PASS (new candidate factor families added)
- CHK-214: PASS (scorecard preset support implemented)
- CHK-215: PASS (`tests/test_company_scorecard.py` passed)
- CHK-216: PASS (new sprint script implemented)
- CHK-217: PASS (phase19_5 artifacts generated)
- CHK-218: PASS (decision gate executed and halted at gate)
- CHK-219: PASS (reviewer A/B/C passes executed)
- CHK-220: FAIL (in-scope High findings unresolved)

ChecksTotal: 10  
ChecksPassed: 9  
ChecksFailed: 1

SAW Verdict: BLOCK

Open Risks:
- Promotion remains blocked (`2/5` gate pass) with spread and crisis-turnover gates failing.
- In-scope High findings (CI exit-code gate and crisis-gate robustness) remain unresolved.
- Walk-forward robustness has unresolved CHK-47 NaN recovery-days signal.

Next action:
- Start Phase 19.5 Round 2 focused on spread-lift and crisis-turnover behavior, while fixing CI/non-empty crisis gate hardening in sprint script before rerun.

ClosurePacket: RoundID=R19_5_R1_20260220; ScopeID=S19_5_SCORECARD_STRENGTHENING; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=gate failures plus unresolved high findings in ci exit behavior and crisis gate robustness; NextAction=phase19_5_round2 spread and crisis turnover improvements with script hardening then rerun

ClosureValidation: PASS
SAWBlockValidation: PASS
