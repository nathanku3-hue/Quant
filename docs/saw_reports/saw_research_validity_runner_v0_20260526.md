# SAW Report - Research Validity Runner v0

RoundID: `ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0`
ScopeID: `SCOPE-RESEARCH-VALIDITY-RUNNER-V0`
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-user-approved-domain | Domains: Quant Research, Backend, Data, Docs/Ops
SAW Verdict: PASS
Commit Anchor: `8716c51781d8524de4147cf42f17e52466913de4`
Commit Scope: local isolated commit `Add research-validity runner v0 evidence gate`
GitHub Status: pushed and verified on `origin/codex/optimizer-core-structured-diagnostics` at `8716c51781d8524de4147cf42f17e52466913de4`.
Dirty Worktree Status: inherited/local dirty context remains outside the pushed commit.

## Scope

Implement the first research-validity control layer: a canonical runner/evidence packet path that can classify a run as `blocked`, `diagnostic_only`, `exploratory`, or `research_valid` without authorizing strategy promotion, ranking, recommendation, alerts, broker behavior, provider ingestion, canonical market-data writes, or live trading.

## Owned Files

- `docs/architecture/research_validity_contract.md`
- `research/__init__.py`
- `research/status.py`
- `research/strategy_cartridge.py`
- `research/metrics.py`
- `research/evidence_schema.py`
- `research/benchmarks.py`
- `research/backtest_runner.py`
- `research/adapters/__init__.py`
- `research/adapters/rule100_replay_adapter.py`
- `tests/test_research_status.py`
- `tests/test_research_evidence_schema.py`
- `tests/test_research_benchmarks.py`
- `tests/test_research_backtest_runner.py`
- `tests/test_research_rule100_adapter.py`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/spec.md`
- `docs/prd.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/lessonss.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`

## Acceptance Checks

- CHK-01: Closed status vocabulary exists and rejects unknown statuses.
- CHK-02: Canonical runner calls `core.engine.run_simulation(...)` with `strict_missing_returns=True`.
- CHK-03: Runner blocks missing cartridge/cost/benchmark/PIT/input/leakage gates and malformed target-weight inputs.
- CHK-04: V0 target weights are risky-asset-only, full-calendar, long-only, finite, and exclude `CASH`.
- CHK-05: Required cash and PIT equal-weight benchmarks run through the same engine/cost/strict policy.
- CHK-06: Rule100 adapter converts replay rows to target weights while ignoring replay equity/performance authority and preserving diagnostic-only status.
- CHK-07: Evidence output is path-confined, atomic temp-to-replace, removes stale final manifests on failed same-run rewrites, and emits `evidence_packet.json` last.
- CHK-08: Docs-as-code and lesson entries record the contract, formulas, boundaries, and review hardening.
- CHK-09: Context artifacts rebuild and validate.

## Subagent Pass Summary

- Implementer A: created core `research/` package and docs contract; parent completed tests and reconciliation.
- Implementer B: created Rule100 adapter and focused adapter tests.
- Reviewer A: PASS after diagnostic lifecycle policy was forced to remain `diagnostic_only`; prior High finding fixed.
- Reviewer B: PASS after output-path containment, atomic evidence writes, final manifest ordering, and stale-manifest cleanup rechecks.
- Reviewer C: PASS after PIT equal-weight benchmark duplicate-provider asset rejection.
- Ownership check: PASS. Implementer and Reviewer A/B/C roles were different subagents or parent reconciliation roles.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `diagnostic_lifecycle_policy` / Rule100-style runs could previously emit `research_valid` when the window was long enough. | Added status gate returning `ResearchStatus.DIAGNOSTIC_ONLY` and regression `test_diagnostic_lifecycle_policy_cannot_emit_research_valid`. | Parent + Reviewer A | Closed |
| High | PIT equal-weight benchmark accepted duplicate provider assets and could divide by duplicate count. | Duplicate eligible assets now fail closed with `duplicate_pit_eligible_assets:<date>` and regression coverage. | Parent + Reviewer C | Closed |
| High | Caller `run_id` could create escaped or nested evidence paths. | Added `_normalize_run_identifier(...)` and `_resolve_evidence_output_dir(...)`; unsafe ids raise `unsafe_run_id` before artifact path creation. | Parent + Reviewer B | Closed |
| High | Evidence writes used direct writes and could leave partial artifacts. | JSON/CSV writes now use same-directory temp files and `os.replace`; `evidence_packet.json` is emitted after component artifacts. | Parent + Reviewer B | Closed |
| Medium | Malformed target-weight dates could raise before returning a blocked result. | Full-calendar validation now short-circuits malformed date indexes and records `target_weight_index_not_date_like`. | Parent + Reviewer B | Closed |
| Medium | Same-run overwrite failure could leave a stale final `evidence_packet.json`. | Existing final manifest is removed before component writes; failure leaves no stale final packet and temp files are cleaned. | Parent + Reviewer B addendum | Closed |

## Scope Split Summary

In-scope findings/actions:

- Closed all Reviewer A/B/C High and Medium findings tied to the Research Validity Runner v0 implementation.
- Added focused regressions for diagnostic role status, duplicate PIT benchmark assets, unsafe run ids, malformed target-weight dates, atomic writes, final manifest ordering, and stale final-manifest cleanup.

Inherited out-of-scope findings/actions:

- Broad inherited dirty/untracked worktree remains and was not cleaned or reverted.
- Full repo phase-close regression was not required for this implementation slice.
- Existing dashboard/replay/local data follow-ups remain separate from the research-validity runner.

## Verification Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile research\__init__.py research\status.py research\strategy_cartridge.py research\metrics.py research\evidence_schema.py research\benchmarks.py research\backtest_runner.py research\adapters\__init__.py research\adapters\rule100_replay_adapter.py tests\test_research_status.py tests\test_research_evidence_schema.py tests\test_research_benchmarks.py tests\test_research_backtest_runner.py tests\test_research_rule100_adapter.py` -> PASS.
- `EVD-02`: `.venv\Scripts\python -m pytest tests\test_research_status.py tests\test_research_evidence_schema.py tests\test_research_benchmarks.py tests\test_research_backtest_runner.py tests\test_research_rule100_adapter.py tests\test_engine.py -q` -> PASS, 45 passed.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_position_lifecycle.py tests\test_pinned_universe.py tests\test_portfolio_universe.py tests\test_optimizer_core_policy.py -q` -> PASS, 186 passed, one inherited `websockets.legacy` deprecation warning.
- `EVD-04`: `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` -> PASS, 21 passed.
- `EVD-05`: `.venv\Scripts\python scripts\build_context_packet.py` and `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `EVD-06`: SE evidence map validation -> PASS.
- `EVD-07`: Reviewer A targeted recheck -> PASS.
- `EVD-08`: Reviewer B runtime recheck and final-manifest addendum recheck -> PASS.
- `EVD-09`: Reviewer C targeted recheck -> PASS.

## SE Executor Closure

Scope line: stream=Backend/Data, stage=Final Verification, owner=parent, round_exec_utc=2026-05-26T09:28:48Z

| task_id | task | artifact | check | status | evidence_id |
|---|---|---|---|---|---|
| TSK-01 | Status/cartridge/runner implementation | `research/status.py`, `research/strategy_cartridge.py`, `research/backtest_runner.py` | compile + focused pytest | PASS | EVD-01,EVD-02 |
| TSK-02 | Evidence schema and atomic output hardening | `research/evidence_schema.py`, `tests/test_research_evidence_schema.py` | focused pytest + Reviewer B addendum | PASS | EVD-02,EVD-08 |
| TSK-03 | Benchmark and Rule100 adapter boundary | `research/benchmarks.py`, `research/adapters/rule100_replay_adapter.py` | focused pytest + Reviewer A/C | PASS | EVD-02,EVD-07,EVD-09 |
| TSK-04 | Affected replay/lifecycle/optimizer regression | replay/lifecycle/optimizer tests | affected suite | PASS | EVD-03 |
| TSK-05 | Docs/context/lessons closure | docs/context and governance docs | context build/validate | PASS | EVD-04,EVD-05 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05
EvidenceRows: EVD-01|ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0|2026-05-26T09:00:00Z;EVD-02|ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0|2026-05-26T09:05:00Z;EVD-03|ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0|2026-05-26T09:12:00Z;EVD-04|ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0|2026-05-26T09:20:00Z;EVD-05|ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0|2026-05-26T09:26:00Z
EvidenceValidation: PASS

## Document Changes Showing

| path | change summary | reviewer status |
|---|---|---|
| `docs/architecture/research_validity_contract.md` | Added mechanical research-validity contract, promotion rule, roles, evidence schema, benchmark policy, PIT/leakage gates, and first implementation slice. | PASS |
| `docs/notes.md` | Added formula and implementation notes for canonical runner, implicit cash, cost rate, Rule100 adapter, and atomic evidence writes. | PASS |
| `docs/decision log.md` | Added Phase 65 decision record and updated contract lock with path confinement and atomic evidence output. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added Research Validity Runner v0 addendum and current evidence counts. | PASS |
| `docs/spec.md`, `docs/prd.md`, `PRD.md`, `PRODUCT_SPEC.md` | Added current notices describing the research-validity runner boundary and output hardening. | PASS |
| `docs/lessonss.md` | Added guardrail lesson for evidence-output path and completion gates. | PASS |
| `docs/context/current_context.json`, `docs/context/current_context.md` | Regenerated current context after docs/code updates. | PASS |

## Document Sorting

GitHub-optimized ordering is maintained: contract docs under `docs/architecture/`, current truth under `docs/context/`, active phase brief under `docs/phase_brief/`, SAW report under `docs/saw_reports/`, and canonical PRD/spec notices at root plus `docs/`.

## Open Risks:

- Inherited dirty/untracked worktree remains outside this round; this SAW does not claim safe-boot or clean GitHub state.
- Full repository phase-close regression was not run in this round; focused and affected suites passed.
- The first Rule100 path is diagnostic-only; strategy promotion remains blocked until a full evidence packet plus robustness/OOS/promotion policy exists.

## Next action:

Commit the Research Validity Runner v0 slice as its own bucket, or continue with the boot-preflight control-plane staging plan using this runner as a future research gate.

ClosurePacket: RoundID=ROUND-20260526-RESEARCH-VALIDITY-RUNNER-V0; ScopeID=SCOPE-RESEARCH-VALIDITY-RUNNER-V0; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=inherited-dirty-worktree-not-closed-this-round; NextAction=commit-research-validity-runner-v0-slice-or-continue-boot-preflight-staging
ClosureValidation: PASS
SAWBlockValidation: PASS
