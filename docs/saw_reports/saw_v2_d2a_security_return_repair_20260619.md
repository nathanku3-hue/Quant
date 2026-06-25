# SAW Report - V2 PEAD D2A Security-Level Return Repair

Mode: `CLOSURE_REPORT`

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-project-scope | Domains: Data, Financial, Python

RoundID: `ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR`
ScopeID: `V2_D2A_SECURITY_LEVEL_TOTAL_RETURN_SAMPLE`

Ship-Fast Decision Gate: completed in `docs/phase_brief/v2-pead-d2a-return-repair-brief.md`; the single next decision is D2B fixed event-level IID selection and `+60` market-session extraction.

## Scope and Ownership

Work round scope: repair D2A security-level daily returns, tests, exactly-500-GVKEY sample, active manifest pointer, superseded legacy evidence, and required docs/truth surfaces without widening into D2B, full build, benchmark, provider, strategy interpretation, or UI.

Owned files changed or produced in this round:

- `scripts/pead_d2_return_contract.py`
- `tests/test_pead_d2_returns.py`
- `data/processed/pead_d2_daily_returns_sample.f8b988055c99c42e28ebf470acbe9d7b6477a08c2ff2c5c71357b292a0fae957.parquet`
- `data/processed/pead_d2_daily_returns_sample.parquet.manifest.json`
- `data/processed/pead_d2_daily_returns_sample.parquet.lock`
- `data/processed/pead_d2_daily_returns_sample_legacy_formula_superseded_20260618.parquet`
- `data/processed/pead_d2_daily_returns_sample_legacy_formula_superseded_20260618.parquet.manifest.json`
- `docs/phase_brief/v2-pead-d2a-return-repair-brief.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`
- `docs/saw_reports/saw_v2_d2a_security_return_repair_20260619.md`

Acceptance checks:

- `CHK-01`: total-return level is `prccd * trfd / ajexdi`; canonical return lags only within `(gvkey, iid)`.
- `CHK-02`: same-security price fallback, date-gap guardrail, and extreme-return guardrail are correct and tested.
- `CHK-03`: `security_id` is one-to-one with `(gvkey, iid)`; output is unique by `(security_id,date)` and preserves all IID series.
- `CHK-04`: D2A requires exactly 500 GVKEYs and rejects `--build` and `--event-window-only` before unauthorized work.
- `CHK-05`: immutable hash-named Parquet plus atomic manifest commit pointer, OS writer lock, interruption safety, and temp cleanup pass.
- `CHK-06`: corrected sample hash, rows, securities, formula residuals, >99% quality gate, and no-temp evidence pass.
- `CHK-07`: invalid legacy sample is reproduced byte-for-byte and labeled superseded evidence only.
- `CHK-08`: focused D2A, strategy, context hygiene, and context builder tests pass.
- `CHK-09`: Reviewer A final strategy/formula/regression re-review passes.
- `CHK-10`: Reviewer B final runtime/operational re-review passes.
- `CHK-11`: Reviewer C final data-integrity/performance re-review passes.

## Subagent Passes

Implementer pass: PASS. A bounded implementer changed only the D2A builder and new synthetic test module; initial implementation evidence was 14 D2A tests plus 13 strategy tests.

Reviewer A final pass: PASS. Formula semantics, same-security fallback, identity injectivity, exactly-500 gate, full-build rejection, strategy schema, and D2A/D2B boundary pass with no remaining finding.

Reviewer B final pass: PASS. Full-build scope, exactly-500 enforcement, immutable Parquet/atomic manifest commit, writer lock, interruption handling, measured formula metrics, and production artifact consistency pass with no in-scope Critical/High/Medium finding.

Reviewer C final pass: PASS. Source union, identity preservation, artifact/hash integrity, quality gates, and crash-consistent pointer publication pass; bounded-sample pandas memory headroom remains a non-blocking Medium performance risk.

Ownership check: PASS. Implementer and Reviewers A/B/C were different agents; reviewers were read-only.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `--build` exposed an unapproved full-build path. | D2A now rejects `--build` before source reads; regression added. | Parent reconciliation / Reviewer B | Fixed |
| High | Sequential replacement could expose a mixed Parquet/manifest pair after a crash. | Publish immutable hash-named Parquet first; atomically replace stable manifest pointer under an OS-released writer lock; add interruption and concurrent-writer tests. | Parent reconciliation / Reviewers B/C | Fixed |
| Medium | Sample label could overstate fewer than 500 GVKEYs. | Require exactly 500 and test 499 rejection before source processing. | Parent reconciliation / Reviewer A | Fixed |
| Medium | Formula residual was hard-coded and >99% evidence was not fail-closed. | Measure canonical/fallback residuals and reject changed-level nonzero share at or below 99%. | Parent reconciliation / Reviewers B/C | Fixed |
| Medium | Pandas sorting/copying expands the bounded sample in memory. | Keep full build disabled; carry optimization to a future Data performance round before any scope expansion. | Future Data performance | Open, non-blocking |
| Low | Corrected sample initially replaced legacy evidence before archival. | Reproduced legacy Parquet at its original SHA and labeled it superseded-only; lesson guardrail added. | Parent reconciliation | Fixed |
| Low | Brief test count and blocked wording became stale during reconciliation. | Refreshed brief to 32 tests and D2B-separate status. | Docs/Ops | Fixed |

## Scope Split Summary

In-scope findings/actions:

- Repaired security-level formula, lags, fallback, identity, duplicate, guardrail, and strategy handoff fields.
- Enforced exactly-500 sample-only CLI scope.
- Replaced two-file sequential promotion with immutable Parquet plus atomic manifest pointer and writer lock.
- Published corrected and superseded evidence artifacts, tests, docs, context, and SAW evidence.

Inherited/out-of-scope findings/actions:

- D2B event-level primary-IID policy and `+60` market-session extraction remain separate.
- Full build, provider reconciliation, benchmark, strategy interpretation, and dashboard integration remain deferred.
- Bounded-sample pandas memory headroom is carried to a future Data performance round; it does not authorize a full build.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/prd.md`, `docs/spec.md` | Added security-level formula, schema, sample-only, and manifest-pointer contract. | PASS |
| `docs/phase_brief/v2-pead-d2a-return-repair-brief.md` | Added Ship-Fast gate, acceptance evidence, rollback, boundaries, and D2B next action. | PASS |
| `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md` | Added formula registry, artifact-retention lesson, and hardcoded D2A decisions. | PASS |
| `PRD.md`, `PRODUCT_SPEC.md` | Updated canonical product and technical requirements. | PASS |
| `docs/context/*_current.md`, `docs/context/current_context.*` | Refreshed bridge, done, impact, streams, alignment, observability, planner, and generated context. | PASS |
| `scripts/pead_d2_return_contract.py` | Implemented security returns, fail-closed gates, measured quality, and crash-consistent publication. | PASS |
| `tests/test_pead_d2_returns.py` | Added synthetic formula, identity, scope, publication, interruption, and quality regressions. | PASS |
| `data/processed/pead_d2_daily_returns_sample*` | Published corrected active sample/pointer and exact legacy superseded evidence. | PASS |
| `docs/saw_reports/saw_v2_d2a_security_return_repair_20260619.md` | Terminal SAW and SE evidence. | PASS |

Document sorting follows `docs/checklist_milestone_review.md`: canonical product/spec, phase brief, notes/lesson/decision, context/evidence, then implementation/test artifacts.

## Validation Evidence

- Runtime sample: `.\.venv\Scripts\python scripts\pead_d2_return_contract.py` -> PASS; 1,491,022 rows, exactly 500 GVKEYs, 795 securities.
- Active artifact: manifest points to immutable Parquet SHA256 `f8b988055c99c42e28ebf470acbe9d7b6477a08c2ff2c5c71357b292a0fae957`; zero duplicate `(security_id,date)` rows; 117 multi-IID GVKEYs.
- Formula evidence: direct source-level TR and price-level maximum errors `0.0`; manifest canonical/fallback residuals `0.0`.
- Quality evidence: 1,132,574 / 1,132,575 changed valid TR levels produce nonzero returns (`0.9999991170562655`).
- Legacy evidence: reproduced invalid sample SHA256 equals original `0432fc703fab997329801c02352c359984544889da8097abb76e7765758652ab`; manifest forbids validation/strategy use.
- Publication evidence: fixed-name Parquet alias absent; active manifest pointer present; no `.tmp` files; stable OS lock file present.
- Focused and context tests: `.\.venv\Scripts\python -m pytest tests\test_pead_d2_returns.py tests\test_pead_event_study.py tests\test_phase61_context_hygiene.py::test_current_context_promotes_latest_active_phase tests\test_build_context_packet.py -q` -> PASS, 54 passed.
- Compile: `.\.venv\Scripts\python -m py_compile scripts\pead_d2_return_contract.py tests\test_pead_d2_returns.py` -> PASS.
- Context build/validation: `.\.venv\Scripts\python scripts\build_context_packet.py` and `--validate` -> PASS.
- Reviewer A/B/C final re-review -> PASS; no unresolved in-scope Critical/High finding.

## SE Evidence Map

Scope line: stream=Data; stage=Final Verification; owner=parent-agent; round_exec_utc=2026-06-19T03:47:27Z.

| task_id | task | artifact | check | status | evidence_id |
|---|---|---|---|---|---|
| TSK-01 | Correct stale D2 truth and lock bounded D2A scope. | Done checklist and D2A brief | Scope, formula, boundary, and stop rules are explicit. | PASS | EVD-01 |
| TSK-02 | Repair security-level return builder and regression suite. | Builder and tests | Formula, fallback, identity, scope, and publication tests pass. | PASS | EVD-02 |
| TSK-03 | Publish and independently validate corrected and superseded samples. | Active manifest/Parquet and legacy pair | Hashes, counts, uniqueness, quality, and no-temp checks pass. | PASS | EVD-03 |
| TSK-04 | Refresh docs-as-code and current truth surfaces. | Product/spec/brief/notes/decision/lesson/context | Context build, validation, and hygiene tests pass. | PASS | EVD-04 |
| TSK-05 | Run independent A/B/C review and reconcile all blockers. | Reviewer outputs and this SAW report | Final A/B/C PASS; no in-scope Critical/High remains. | PASS | EVD-05 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05

EvidenceRows: EVD-01|ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR|2026-06-19T03:47:27Z;EVD-02|ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR|2026-06-19T03:47:27Z;EVD-03|ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR|2026-06-19T03:47:27Z;EVD-04|ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR|2026-06-19T03:47:27Z;EVD-05|ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR|2026-06-19T03:47:27Z

EvidenceValidation: PASS

Rollback note: atomically restore the prior manifest pointer to its still-immutable referenced Parquet; do not copy or rename data behind an active manifest.

Open Risks: bounded-sample pandas memory headroom is non-blocking; D2B/full-build/benchmark/provider/strategy/UI remain separate.

Next action: start_D2B_fixed_event_level_IID_selection_and_plus_60_market_sessions_separately

ClosurePacket: RoundID=ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR; ScopeID=V2_D2A_SECURITY_LEVEL_TOTAL_RETURN_SAMPLE; ChecksTotal=11; ChecksPassed=11; ChecksFailed=0; Verdict=PASS; OpenRisks=bounded_sample_memory_headroom_and_deferred_D2B_full_build_benchmark_provider_strategy_UI; NextAction=start_D2B_fixed_event_level_IID_selection_and_plus_60_market_sessions_separately

ClosureValidation: PASS

SAWBlockValidation: PASS
