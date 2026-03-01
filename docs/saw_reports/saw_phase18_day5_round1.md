# SAW Report — Phase 18 Day 5 Round 1
Date: 2026-02-20

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase18-brief.md`

RoundID: `R18_D5_ABLATION_20260220`  
ScopeID: `S18_DAY5_ABLATION_MATRIX`

## Scope and Ownership
- Scope: Day 5 ablation matrix implementation, execution, guardrail reconciliation, and docs-as-code closure.
- Owned files:
  - `scripts/day5_ablation_report.py`
  - `strategies/company_scorecard.py`
  - `scripts/scorecard_validation.py`
  - `tests/test_day5_ablation_report.py`
  - `tests/test_company_scorecard.py`
  - `docs/phase18-brief.md`
  - `docs/runbook_ops.md`
  - `docs/notes.md`
  - `docs/lessonss.md`
  - `docs/decision log.md`
  - `docs/saw_phase18_day5_round1.md`
- Acceptance checks:
  - CHK-33 ablation matrix executes all 9 configurations
  - CHK-34 optimal config coverage >= 95%
  - CHK-35 optimal config quartile spread >= 2.0 sigma
  - CHK-36 turnover reduction >= 20% vs baseline
  - CHK-37 Sharpe preservation/improvement vs baseline
  - CHK-38 touched-scope test gate pass

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7727-dcec-7cd2-906c-e1bc8f6255ec`
- Reviewer B: `019c7727-dd26-7152-b094-0c08282642fe`
- Reviewer C: `019c7727-dd3b-7a83-b57d-ae0b60a49ec1`
- Independence: PASS

## Top-Down Snapshot
L1: 7-Day Alpha Sprint (Baseline Benchmarking)
L2 Active Streams: Backend, Data, Ops
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+--------------------------------------------------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope                                                | Rating | Next Scope                                                   |
+--------------------+--------------------------------------------------------------+--------+--------------------------------------------------------------+
| Planning           | Boundary=Day5 ablation; Owner/Handoff=Impl->Rev A/B/C;      | 100/100| 1) Promote Day6 robustness gate with C3 candidate [82/100]: |
|                    | Acceptance Checks=CHK-33..CHK-38                            |        | best Sharpe/turnover found but coverage/spread still bind.   |
| Executing          | Add ablation runner + scoring modes + guardrails + tests    | 100/100| 1) Keep fail-fast defaults for data-integrity paths [88/100]:|
|                    |                                                              |        | override only with explicit operator flag.                   |
| Iterate Loop       | Reconcile reviewer findings and rerun matrix                | 100/100| 1) Carry unresolved metric gates as design constraints       |
|                    |                                                              |        | [79/100]: no in-scope Critical/High defects remain.          |
| Final Verification | Runtime matrix + impacted regression + docs + SAW           | 90/100 | 1) Close Day6 with robustness/walk-forward evidence [80/100]:|
|                    |                                                              |        | convert advisory outcomes into acceptance decision.           |
+--------------------+--------------------------------------------------------------+--------+--------------------------------------------------------------+

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Day 5 optimal config did not meet coverage target (`52.37% < 95%`). | Carry as Day 6 robustness risk; do not force parameter salvage in Day 5. | Strategy | Open |
| Medium | Day 5 optimal config did not meet spread target (`1.80 < 2.0`). | Carry as Day 6 robustness risk; evaluate structural factor alternatives. | Strategy | Open |
| Medium | Quantile boundary selected extra names at cutoff and could bias turnover/Sharpe. | Switched to exact `ceil(q*n)` cardinality with descending rank in `_build_target_weights`. | Implementer | Closed |
| Medium | Missing active returns were implicitly masked in simulation alignment. | Added fail-fast + explicit `--allow-missing-returns` override and warning path. | Implementer | Closed |
| Medium | Potential wide-matrix memory blowup in dense pivot path. | Added `--max-matrix-cells` guardrail before simulation. | Implementer | Closed |
| Low | `scorecard_validation` atomic CSV writer lacked replace retry under Windows locks. | Added retry/backoff around `os.replace`. | Implementer | Closed |
| Low | `.pytest_cache` ACL warning persists (`WinError 5`). | Defer to ops ACL cleanup outside strategy scope. | Infrastructure | Open |

## Scope Split Summary
In-scope findings/actions:
- Implemented Day 5 ablation runner and scoring-mode contract.
- Reconciled reviewer medium findings in ranking precision, missing-return handling, and matrix-size safety.
- Produced Day 5 artifacts and reran impacted regression tests.

Inherited out-of-scope findings/actions:
- Existing `.pytest_cache` ACL warning remains non-blocking.

## Document Changes Showing
Code/Test changes:
- `strategies/company_scorecard.py` — explicit scoring modes (`complete_case`, `partial`, `impute_neutral`); reviewer status: Closed.
- `scripts/day5_ablation_report.py` — 9-config matrix runner, guardrails, artifact outputs; reviewer status: Closed.
- `scripts/scorecard_validation.py` — scoring-method flag + atomic replace retry; reviewer status: Closed.
- `tests/test_day5_ablation_report.py` — Day 5 matrix contract and quantile-cardinality tests; reviewer status: Closed.
- `tests/test_company_scorecard.py` — scoring-mode validity-order regression test; reviewer status: Closed.

Docs changes (GitHub-optimized order):
- `docs/phase18-brief.md` — Day 5 implementation/results/checks/evidence.
- `docs/runbook_ops.md` — Day 5 runbook command and strict/override modes.
- `docs/notes.md` — Day 5 formulas and file-level references.
- `docs/lessonss.md` — Day 5 guardrail lesson entry.
- `docs/decision log.md` — D-99 Day 5 decision and result framing.

## Check Results
- CHK-33: PASS
- CHK-34: FAIL
- CHK-35: FAIL
- CHK-36: PASS
- CHK-37: PASS
- CHK-38: PASS

ChecksTotal: 6  
ChecksPassed: 4  
ChecksFailed: 2

SAW Verdict: ADVISORY_PASS

Open Risks:
- Coverage gate remains open under complete-case semantics.
- Spread gate remains open under current factor stack.
- Missing active returns exist in several configs; override mode was used to complete matrix run.

Next action:
- Use `ABLATION_C3_INTEGRATOR` as Day 6 robustness candidate and resolve CHK-34/CHK-35 via walk-forward evidence, not Day 5 salvage tuning.

ClosurePacket: RoundID=R18_D5_ABLATION_20260220; ScopeID=S18_DAY5_ABLATION_MATRIX; ChecksTotal=6; ChecksPassed=4; ChecksFailed=2; Verdict=ADVISORY_PASS; OpenRisks=coverage+spread gates open; NextAction=Day6 robustness on C3 candidate

ClosureValidation: N/A (closure validator enforces PASS/BLOCK verdicts only)  
SAWBlockValidation: PASS
