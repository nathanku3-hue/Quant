# SAW Report - V2 PEAD Real-Data Validation

RoundID: `ROUND-20260620-V2-PEAD-REAL-DATA-VALIDATION`
ScopeID: `V2_PEAD_CAR_BHAR_QUINTILE_REAL_DATA_VALIDATION`
Mode: `CLOSURE_REPORT`
SAW Verdict: PASS
SE Executor Verdict: PASS
EvidenceValidation: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Financial Research, Data Engineering, Software Engineering, Docs/Ops

## Scope and Ownership

Work round scope: run one bounded, reproducible PEAD CAR/BHAR/quintile real-data validation from the locked D1/D2B/D3 lineage, publish one atomic numbers-only JSON artifact, and reconcile owner-review evidence only.

Owned files changed or produced in this round:

- `scripts/pead_real_data_validation.py`
- `tests/test_pead_real_data_validation.py`
- `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`
- `docs/phase_brief/v2-pead-real-data-validation-brief.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`
- `docs/saw_reports/saw_v2_pead_real_data_validation_20260620.md`

Acceptance checks:

| Check | Evidence | Status |
|---|---|---|
| CHK-01 D1/D2B/D3 lineage hashes recorded and validated | JSON `lineage` block records manifest and Parquet SHA256 for D1, D2B, and D3 | PASS |
| CHK-02 D2B rows/events preserved | 754,920 rows, 12,582 events, and 362 issuers | PASS |
| CHK-03 D2B-to-D3 benchmark join remains many-to-one | Script validates the row-preserving `return_date` join before summarization | PASS |
| CHK-04 Strategy path is canonical | Calls `summarize_event_windows` then `summarize_quantile_performance` without formula edits | PASS |
| CHK-05 Event-date output keeps locked fail-closed HAC behavior | Daily CAR/BHAR each retain 2,777 HAC gaps, null HAC standard error, and null t-statistic | PASS |
| CHK-06 Quarterly output is descriptive-only | `ex_post_descriptive_only = true`, 40 cohorts, zero HAC gaps | PASS |
| CHK-07 JSON is strict and deterministic | Strict JSON write passed; rerun reproduced SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e` | PASS |
| CHK-08 Atomic output protocol is covered | Same-directory temp file, fsync, and atomic replace are implemented and tested | PASS |
| CHK-09 Limitations are explicit | 500-GVKEY sample, current-vintage EPS, Compustat return proxy, no delisting adjustment | PASS |
| CHK-10 Focused and PEAD regressions pass | Focused validation tests 10/10; full PEAD regression 99/99 | PASS |
| CHK-11 Review and validator evidence pass | Reviewer A/B/C PASS; closure, SE evidence, SAW block, and context validators PASS | PASS |

## Reviewer Passes

Ownership check: implementer agent `019ee3a2-f3d6-7ae1-ad99-c3882e8feff0` owned script/test implementation; Reviewer A `019ee3af-c4a4-7341-adbf-c6f79c88a47e`, Reviewer B `019ee3af-f402-7f71-b3d3-5e321b374cc9`, and Reviewer C `019ee3b0-1d30-73f2-b977-a2781bc8a71a` were separate independent reviewers.

| Reviewer | Focus | Verdict | Reconciliation |
|---|---|---|---|
| Reviewer A | Strategy correctness and regression risk | PASS | Verified canonical strategy path, daily HAC gap null behavior, quarterly descriptive labeling, and no tuning or alpha claims. |
| Reviewer B | Runtime and operational resilience | PASS | Verified focused tests, deterministic temp-output CLI byte match, failure cleanup, atomic write behavior, and forbidden-scope boundaries. |
| Reviewer C | Data integrity and performance path | PASS | Verified lineage hashes, row preservation, benchmark coverage, JSON byte-identical rebuild, daily null HAC, and quarterly descriptive-only output. |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | Rebuild peaked at 674.8 MiB RSS, acceptable for a bounded offline evidence run but unsuitable as an interactive dashboard path without a memory design. | Keep this script as offline evidence generation only; require a separate reader/memory design if dashboard scoping opens. | Future dashboard-scope owner | Open as Low follow-up; non-blocking |
| Info | Daily cohorts contain HAC gaps, including weekends; forcing a t-stat would misstate the locked fail-closed behavior. | Published daily event-date result with null HAC SE/t-stat and separately published quarterly output as descriptive-only. | Parent implementer | Resolved |
| Info | Dashboard scoping could be overread as unlocked by a numerical artifact. | Current truth surfaces state owner review is next; dashboard scoping and implementation remain separate decisions. | Docs/Ops | Resolved |

## Scope Split Summary

in-scope actions:

- Generate CAR/BHAR/quintile evidence from the locked D1/D2B/D3 sample lineage.
- Publish event-date daily evidence with fail-closed HAC gap behavior unchanged.
- Publish quarterly evidence only with `ex_post_descriptive_only = true`.
- Record counts, lineage, strategy configuration, coverage reasons, quantile summaries, high-minus-low spreads, HAC settings, limitations, tests, and review evidence.

inherited out-of-scope findings/actions:

- Dashboard scoping remains a separate owner decision after reviewing the JSON.
- Alpha claims, strategy promotion, dashboard implementation, ranking/scoring, alerts, broker/order paths, provider ingestion, cohort-frequency tuning, and HAC-lag tuning remain blocked.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `scripts/pead_real_data_validation.py` | Added bounded validation CLI with lineage checks, canonical strategy calls, strict deterministic JSON, and atomic write | PASS |
| `tests/test_pead_real_data_validation.py` | Added focused tests for lineage, config, fail-closed daily HAC, quarterly descriptive labeling, strict JSON, and atomic behavior | PASS |
| `docs/context/e2e_evidence/pead_real_data_validation_20260620.json` | Published numbers-only evidence artifact with D1/D2B/D3 lineage, counts, CAR/BHAR quintiles, HML spreads, HAC fields, and limitations | PASS |
| `docs/phase_brief/v2-pead-real-data-validation-brief.md` | Closed the execution packet and recorded evidence/status | PASS |
| `docs/notes.md` | Recorded formulas, logic chain, counts, daily/quarterly HAC behavior, and artifact SHA | PASS |
| `docs/decision log.md` | Recorded the validation decision and owner-review next gate | PASS |
| `docs/lessonss.md` | Added guardrail that handoff tests do not replace numerical evidence artifacts | PASS |
| `docs/context/*.md` | Refreshed planner, bridge, checklist, impact, multistream, alignment, and observability truth surfaces | PASS |
| `docs/context/current_context.md`; `docs/context/current_context.json` | Rebuilt compact context from the real-data validation DONE packet | PASS |

Document sorting order follows `docs/checklist_milestone_review.md`: phase brief, notes, lessons, decision log, current truth surfaces, then SAW evidence.

## Closure

Open Risks: LOW_memory_peak_674.8_MiB_keep_offline_bounded
Next action: owner_review_then_separate_dashboard_scoping_decision
ClosurePacket: RoundID=ROUND-20260620-V2-PEAD-REAL-DATA-VALIDATION; ScopeID=V2_PEAD_CAR_BHAR_QUINTILE_REAL_DATA_VALIDATION; ChecksTotal=11; ChecksPassed=11; ChecksFailed=0; Verdict=PASS; OpenRisks=LOW_memory_peak_674.8_MiB_keep_offline_bounded; NextAction=owner_review_then_separate_dashboard_scoping_decision
ClosureValidation: PASS
SAWBlockValidation: PASS
