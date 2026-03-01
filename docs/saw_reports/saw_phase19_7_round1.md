# SAW Report - Phase 19.7 Round 1 (Regime Fidelity Forensics)
Date: 2026-02-20

Builds on prior round: `docs/saw_phase19_6_round1.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data

RoundID: `R19_7_R1_20260220`  
ScopeID: `S19_7_REGIME_FIDELITY_FORENSICS`

## Scope and Ownership
- Scope: execute Phase 19.7 strict RED-veto sprint, generate Phase 19.7 diagnostics artifacts, evaluate locked gates, and stop at decision gate.
- Owned files:
  - `docs/phase19-brief.md`
  - `docs/lessonss.md`
  - `strategies/factor_specs.py`
  - `strategies/company_scorecard.py`
  - `scripts/regime_fidelity_sprint.py`
  - `scripts/scorecard_diagnostics_sprint.py`
  - `scripts/scorecard_strengthening_sprint.py`
  - `tests/test_company_scorecard.py`
  - `data/processed/phase19_7_ablation_metrics.csv`
  - `data/processed/phase19_7_delta_vs_c3.csv`
  - `data/processed/phase19_7_regime_audit.csv`
  - `data/processed/phase19_7_walkforward.csv`
  - `data/processed/phase19_7_decay_sensitivity.csv`
  - `data/processed/phase19_7_crisis_turnover.csv`
  - `data/processed/phase19_7_checks.csv`
  - `data/processed/phase19_7_summary.json`
  - `docs/saw_phase19_7_round1.md`
- Acceptance checks:
  - CHK-231..CHK-240.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7a0e-37f7-7600-b74d-a43d8c6938f0`
- Reviewer B: `019c7a0e-3806-7ca2-9144-cb04c5ae43fc`
- Reviewer C: `019c7a0e-380e-7700-95d6-72c0b26f453b`
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
| Planning           | B=Phase 19.7 regime fidelity; strict RED-veto; OH=Impl->Rev | 97/100 | Freeze per-regime audit + veto rules |
| Executing          | RED-veto + per-regime audit matrix + weighted spread       | 92/100 | Run fidelity sprint                |
| Iterate Loop       | Compare vs 19.6 & original C3                              | 89/100 | Apply new C3 lock if all gates pass |
| Final Verification | py_compile + pytest + SAW                                  | 86/100 | Publish SAW + update production_config |
| CI/CD              | Handoff to Phase 20 (joint WFO with stops once fidelity fixed) | 84/100 | Open Phase 20 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Quantitative Gate Result
- Selected config: `P197_RANK_4F_STRICT_RED`
- Baseline: `C3_LOCKED`
- Window/cost/path: `2015-01-01` to `2024-12-31`, `5 bps`, same C3 engine path.
- Delta (`data/processed/phase19_7_delta_vs_c3.csv`):
  - Coverage: `0.5237 -> 0.8382` (`+0.3146`)
  - Spread sigma: `1.8245 -> 2.4115` (`+0.5870`)
  - Regime spread min: `2.4094`
  - Sharpe: `1.0141 -> -0.4617` (`-1.4757`)
  - Turnover annual: `11.9470 -> 6.3408` (`0.5307x`)
- Strict gates (`data/processed/phase19_7_summary.json`):
  - `gate_coverage_ge_90`: FAIL (`0.8382`)
  - `gate_spread_sigma_ge_2_30_all_regimes`: PASS
  - `gate_sharpe_ge_0_95`: FAIL (`-0.4617`)
  - `gate_crisis_turnover_reduction_ge_80_all_windows`: FAIL
- Crisis reductions (`data/processed/phase19_7_crisis_turnover.csv`):
  - COVID crash: `95.10%`
  - COVID volatility: `100.00%`
  - Inflation spike: `79.66%`
  - Bear market: `68.91%`
- CHK bundle (`CHK-41/48/50/51/53`) from `data/processed/phase19_7_summary.json`: `0/5` (required `4/5`)
- Gate tally: `1/4`
- Decision: `ABORT_PIVOT`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Quantitative promotion gate failed (`1/4`) and CHK bundle failed (`0/5`), so candidate is not promotable. | Keep ABORT_PIVOT; do not promote or lock a new C3. | Strategy | Open (Mandatory Pivot) |
| High | Runtime gate enforcement is weak: script/wrappers return success exit status even on blocked decisions, reducing CI fail-fast behavior. | Return non-zero when `decision != PROMOTE` after writing artifacts. | Ops | Open |
| High | Crisis turnover CSV `pass` flags are inconsistent with the strict `>=80%` gate for some windows, risking operator confusion. | Compute/store strict gate-aligned boolean separately (or overwrite `pass`) for Phase 19.7 crisis artifact. | Data | Open |
| Medium | `CHK-47` value missing in checks artifact weakens evidence completeness. | Enforce non-empty check `value` fields and fail generation on blanks. | Data | Open |
| Info | Reviewer A confirmed strict RED-veto wiring and ABORT decision consistency with generated metrics/artifacts. | No code change required. | Strategy | Closed |

## Scope Split Summary
In-scope findings/actions:
- Implemented Phase 19.7 regime fidelity code path (strict RED-veto + per-regime audit + new sprint runner).
- Generated full Phase 19.7 artifacts and evaluated locked strict gates.
- Executed reviewer A/B/C passes and captured operational/data risks.
- Stopped at decision gate with ABORT_PIVOT.

Inherited out-of-scope findings/actions:
- Prior unresolved governance/ops debts from earlier rounds remain tracked in `docs/saw_phase19_6_round1.md` and `docs/saw_phase21_day1.md`.

## Document Changes Showing
- `docs/phase19-brief.md` — added Phase 19.7 section and locked snapshot table; reviewer status: B/C reviewed.
- `docs/lessonss.md` — appended Phase 19.6 lesson row; reviewer status: C reviewed.
- `docs/saw_phase19_7_round1.md` — canonical SAW report for this round.
- `strategies/factor_specs.py` — added `regime_veto` and `per_regime_audit`; reviewer status: A/C reviewed.
- `strategies/company_scorecard.py` — wired strict RED-veto into score computation; reviewer status: A/C reviewed.
- `scripts/regime_fidelity_sprint.py` — added Phase 19.7 diagnostics and strict gate evaluation; reviewer status: A/B/C reviewed.
- `scripts/scorecard_diagnostics_sprint.py` — compatibility wrapper to regime fidelity runner; reviewer status: B reviewed.
- `scripts/scorecard_strengthening_sprint.py` — compatibility wrapper retained; reviewer status: B reviewed.
- `tests/test_company_scorecard.py` — added RED-veto/per-regime audit tests; reviewer status: A reviewed.
- `data/processed/phase19_7_ablation_metrics.csv` — generated ablation metrics.
- `data/processed/phase19_7_delta_vs_c3.csv` — generated baseline delta metrics.
- `data/processed/phase19_7_regime_audit.csv` — generated per-regime factor audit.
- `data/processed/phase19_7_walkforward.csv` — generated walk-forward evidence.
- `data/processed/phase19_7_decay_sensitivity.csv` — generated decay sensitivity evidence.
- `data/processed/phase19_7_crisis_turnover.csv` — generated crisis turnover evidence.
- `data/processed/phase19_7_checks.csv` — generated check ledger.
- `data/processed/phase19_7_summary.json` — generated gate summary and decision.

## Check Results
- CHK-231: PASS (Phase 19.7 brief/table updated)
- CHK-232: PASS (lesson row appended)
- CHK-233: PASS (`regime_veto` and `per_regime_audit` implemented)
- CHK-234: PASS (strict RED-veto wired into `CompanyScorecard`)
- CHK-235: PASS (`regime_fidelity_sprint.py` implemented; wrappers aligned)
- CHK-236: PASS (`py_compile` + `pytest tests/test_company_scorecard.py` passed)
- CHK-237: PASS (Phase 19.7 output artifacts generated)
- CHK-238: FAIL (strict 4/4 promotion gates not met)
- CHK-239: FAIL (CHK bundle requirement `>=4/5` not met; actual `0/5`)
- CHK-240: FAIL (in-scope High findings unresolved this round)

ChecksTotal: 10  
ChecksPassed: 7  
ChecksFailed: 3

SAW Verdict: BLOCK

Open Risks:
- Candidate remains unpromotable under strict Phase 19.7 gates.
- CI/runtime gating can mis-signal success until non-zero exit semantics are enforced.
- Crisis/check artifacts have metadata consistency gaps that can mislead operator review.

Next action:
- Pivot to the next approved forensics iteration focused on regime fidelity hardening and gate-enforcement/data-integrity fixes before any promotion attempt.

ClosurePacket: RoundID=R19_7_R1_20260220; ScopeID=S19_7_REGIME_FIDELITY_FORENSICS; ChecksTotal=10; ChecksPassed=7; ChecksFailed=3; Verdict=BLOCK; OpenRisks=strict gate failure plus unresolved high runtime and artifact integrity issues; NextAction=pivot to next regime-fidelity round with gate-enforcement and artifact consistency fixes before rerun

ClosureValidation: PASS
SAWBlockValidation: PASS
