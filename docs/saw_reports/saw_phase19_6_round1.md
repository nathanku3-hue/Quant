# SAW Report — Phase 19.6 Round 1 (Diagnostics & Orthogonality)
Date: 2026-02-20

Builds on prior round: `docs/saw_phase19_5_round1.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data | FallbackSource: `docs/spec.md` + `docs/phase19-brief.md`

RoundID: `R19_6_R1_20260220`  
ScopeID: `S19_6_DIAGNOSTICS_ORTHOGONALITY`

## Scope and Ownership
- Scope: execute Phase 19.6 pivot (docs + diagnostics primitives + renamed diagnostics sprint), run strict gate, and stop at decision gate.
- Owned files:
  - `docs/phase19-brief.md`
  - `docs/lessonss.md`
  - `strategies/factor_specs.py`
  - `strategies/company_scorecard.py`
  - `tests/test_company_scorecard.py`
  - `scripts/scorecard_diagnostics_sprint.py`
  - `scripts/scorecard_strengthening_sprint.py`
  - `data/processed/phase19_6_ablation_metrics.csv`
  - `data/processed/phase19_6_delta_vs_c3.csv`
  - `data/processed/phase19_6_orthogonality_report.csv`
  - `data/processed/phase19_6_walkforward.csv`
  - `data/processed/phase19_6_decay_sensitivity.csv`
  - `data/processed/phase19_6_crisis_turnover.csv`
  - `data/processed/phase19_6_checks.csv`
  - `data/processed/phase19_6_summary.json`
  - `docs/saw_phase19_6_round1.md`
- Acceptance checks:
  - CHK-221..CHK-230.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c79eb-3ce0-7d00-a463-7ee153bb008a`
- Reviewer B: `019c79eb-3cf2-7931-8af4-7f33c5c65150`
- Reviewer C: `019c79eb-3cf9-7141-8a2c-7b131695737e`
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
| Planning           | B=Phase 19.6 diagnostics; OH=Impl→RevA/B/C; AC=CHK-221..230 | 96/100 | Freeze correlation audit + veto rules |
| Executing          | Orthogonality matrix + regime-adaptive norm + liquidity veto | 90/100 | Run diagnostics sprint             |
| Iterate Loop       | Compare vs Phase 19.5 & original C3                        | 87/100 | Apply new C3 lock if all gates pass |
| Final Verification | py_compile + pytest + SAW                                  | 85/100 | Publish SAW + update production_config |
| CI/CD              | Handoff to Phase 20 (joint WFO with stops once spread fixed) | 82/100 | Open Phase 20 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Quantitative Gate Result
- Selected config: `P196_SPREAD_RANK_4F_PARTIAL`
- Baseline: `C3_LOCKED`
- Window/cost/path: `2015-01-01` to `2024-12-31`, `5 bps`, same C3 engine path.
- Delta (`data/processed/phase19_6_delta_vs_c3.csv`):
  - Coverage: `0.5237 -> 1.0000` (`+0.4763`)
  - Spread sigma: `1.8245 -> 2.4106` (`+0.5861`)
  - Sharpe: `1.0141 -> -0.6206` (`-1.6347`)
  - Turnover annual: `11.9470 -> 7.2346` (`0.6056x`)
- Strict gates (`data/processed/phase19_6_summary.json`):
  - `gate_coverage_ge_85`: PASS
  - `gate_spread_ge_2_10`: PASS
  - `gate_crisis_turnover_reduction_ge_75_all_windows`: FAIL
  - `gate_chk_bundle_4_of_5`: FAIL (`0/5`)
- Crisis reductions (`data/processed/phase19_6_crisis_turnover.csv`):
  - COVID crash: `70.63%`
  - COVID volatility: `43.16%`
  - Inflation spike: `60.24%`
  - Bear market: `41.81%`
- Gate tally: `2/4`
- Decision: `ABORT_PIVOT`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Strict Phase 19.6 gate failed (`2/4`); candidate cannot be promoted. | Keep ABORT_PIVOT and continue diagnostics iteration. | Strategy | Open (Mandatory Pivot) |
| High | Script returns exit code `0` even when decision is `ABORT_PIVOT`, weakening CI gate enforcement. | Return non-zero on non-promote decisions (or equivalent hard CI gate in wrapper). | Ops | Open |
| Medium | `phase19_6_checks.csv` evidence paths still reference `phase18_day6_*`, causing artifact metadata mismatch. | Parameterize evidence-file names for current phase outputs. | Data | Open |
| Info | Reviewer A found no direct strategy-correctness defect in new regime-adaptive/correlation primitives. | No immediate code fix required. | Strategy | Closed |

## Scope Split Summary
In-scope findings/actions:
- Added Phase 19.6 docs + lesson row.
- Implemented `correlation_audit` and `regime_adaptive_norm` primitives.
- Wired `CompanyScorecard` regime-adaptive normalization path.
- Renamed sprint flow to diagnostics runner with RED-regime veto/freeze logic.
- Generated full Phase 19.6 artifacts and halted at decision gate.

Inherited out-of-scope findings/actions:
- Phase 19.5 unresolved items remain tracked in `docs/saw_phase19_5_round1.md`.

## Document Changes Showing
- `docs/phase19-brief.md` — added Phase 19.6 section and locked snapshot table; reviewer status: B reviewed.
- `docs/lessonss.md` — appended new Phase 19.5 miss/guardrail lesson row; reviewer status: C reviewed.
- `strategies/factor_specs.py` — added `regime_adaptive_norm` and `correlation_audit`; reviewer status: A/C reviewed.
- `strategies/company_scorecard.py` — added regime-map-aware normalization path; reviewer status: A reviewed.
- `tests/test_company_scorecard.py` — added regime-adaptive and correlation-audit tests; reviewer status: A reviewed.
- `scripts/scorecard_diagnostics_sprint.py` — new Phase 19.6 diagnostics runner; reviewer status: B/C reviewed.
- `scripts/scorecard_strengthening_sprint.py` — compatibility wrapper to renamed runner.
- `data/processed/phase19_6_ablation_metrics.csv` — generated ablation table.
- `data/processed/phase19_6_delta_vs_c3.csv` — generated baseline delta table.
- `data/processed/phase19_6_orthogonality_report.csv` — generated correlation/orthogonality audit.
- `data/processed/phase19_6_walkforward.csv` — generated walk-forward outputs.
- `data/processed/phase19_6_decay_sensitivity.csv` — generated decay sweep outputs.
- `data/processed/phase19_6_crisis_turnover.csv` — generated crisis turnover evidence.
- `data/processed/phase19_6_checks.csv` — generated check ledger.
- `data/processed/phase19_6_summary.json` — generated gate verdict summary.

## Check Results
- CHK-221: PASS (lesson row appended)
- CHK-222: PASS (Phase 19.6 brief section + snapshot added)
- CHK-223: PASS (`correlation_audit` + `regime_adaptive_norm` implemented)
- CHK-224: PASS (runner renamed to diagnostics script, compatibility entrypoint retained)
- CHK-225: PASS (diagnostics sprint executed and orthogonality artifact produced)
- CHK-226: PASS (`py_compile` + `pytest tests/test_company_scorecard.py` passed)
- CHK-227: PASS (decision gate executed and halted)
- CHK-228: PASS (reviewer A/B/C passes completed)
- CHK-229: FAIL (strict 4/4 gate policy not met)
- CHK-230: FAIL (in-scope High reviewer issue unresolved)

ChecksTotal: 10  
ChecksPassed: 8  
ChecksFailed: 2

SAW Verdict: BLOCK

Open Risks:
- Candidate remains unpromotable under strict Phase 19.6 rules.
- CI gate weakness persists until non-zero exit handling is implemented for blocked decisions.
- Checks artifact currently references legacy evidence filenames.

Next action:
- Execute Phase 19.6 Round 2 focused on crisis-turnover protection and CHK bundle recovery, plus CI/evidence-file hardening before rerun.

ClosurePacket: RoundID=R19_6_R1_20260220; ScopeID=S19_6_DIAGNOSTICS_ORTHOGONALITY; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=strict gate failure plus unresolved high ci-gating issue and checks evidence path mismatch; NextAction=phase19_6_round2 crisis robustness plus ci and evidence hardening before rerun

ClosureValidation: PASS
SAWBlockValidation: PASS
