SAW Round Report

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Data, Strategy, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase23-brief.md

RoundID: R23_D1_20260222_R3
ScopeID: phase23_step2_sdm_ingest_assembler
Scope: Execute and verify the 4-script SDM ingestion slice (fundamentals + macro + FF + assembler), fix PIT merge blocker, and close reviewer findings.

Acceptance Checks
- CHK-01: Fix `merge_asof` sort order + assertions in `ingest_compustat_sdm.py` -> PASS
- CHK-02: Implement dynamic `totalq.total_q` probing + graceful fallback -> PASS
- CHK-03: Enforce allow+audit unmapped `permno` policy -> PASS
- CHK-04: Hardwire FF ingest to `ff.fivefactors_daily` and require full five-factor + momentum columns in assembler -> PASS
- CHK-05: Implement PIT-safe `assemble_sdm_features.py` with backward asof joins -> PASS
- CHK-06: Preserve atomic writes for all output artifacts -> PASS
- CHK-07: Dry-runs pass without destructive writes (including audit dry-run skip) -> PASS
- CHK-08: Non-dry execution writes all SDM outputs -> PASS
- CHK-09: Targeted pytest suite passes for new/changed logic -> PASS
- CHK-10: Docs-as-code updates completed (brief/spec/prd/runbook/notes/lessons/decision log) -> PASS

Ownership Check
- Implementer: Codex-main
- Reviewer A: explorer `019c84a5-70da-7492-af58-ca90cf77164c`
- Reviewer B: explorer `019c84a5-70e3-7181-8053-7018a61a6d49`
- Reviewer C: explorer `019c84a5-70f3-7951-9094-d08a0da2bfab`
- Independence check: PASS (implementer and reviewers are distinct agents)

Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `--dry-run` on fundamentals ingest still wrote unmapped audit CSV, violating dry-run semantics | Added `_crosswalk_permno(..., write_audit)` and wired `write_audit=not args.dry_run`; added regression test | Codex-main | Resolved |
| Medium | Assembler accepted FF files with missing factor columns, risking downstream factor regressions | Enforced full required FF schema (`date,mktrf,smb,hml,rmw,cma,umd`) and added regression test | Codex-main | Resolved |
| Medium | Assembler has no optional graceful mode for empty/missing upstream data dependencies | Keep fail-fast behavior for now; consider `--allow-empty-data` operational mode in next round | Data Eng | Open |
| Medium | FRB feed currently ends at 2025-02-13, leaving macro nulls on later fundamentals rows | Backfill FRB source or gate publish window to macro coverage horizon | Data Ops | Open |
| Medium | FF factors end at 2025-12-31, leaving early-2026 factor nulls | Backfill FF source or gate publish window to factor coverage horizon | Data Ops | Open |
| Low | Earliest rows lack `k_int` coverage due `totalq` historical availability gaps | Keep PIT-safe nulls + scoring gate on required columns | Data Eng | Open |

Scope Split Summary
- in-scope: all Critical/High findings were fixed and retested in this round.
- inherited: none.

Top-Down Snapshot
L1: Phase 23 SDM Ingestion Engine
L2 Active Streams: Data, Ops
L2 Deferred Streams: Backend, Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Data
Active Stage Level: L3

+--------------------+--------------------------------------------------------------------------------+--------+----------------------------------------------------------------------------------+
| Stage              | Current Scope                                                                  | Rating | Next Scope                                                                       |
+--------------------+--------------------------------------------------------------------------------+--------+----------------------------------------------------------------------------------+
| Planning           | Boundary=scripts/tests/docs; Owner/Handoff=Codex->SAW A/B/C; Acceptance=CHK01-10 | 100/100 | 1) Keep PIT + schema guards as baseline [92/100]: fixes are stable and tested. |
| Executing          | 4-script SDM slice completed with atomic writes and dry-run safety             | 100/100 | 1) Add optional empty-input operational mode [74/100]: improve recovery paths. |
| Iterate Loop       | Reviewer findings reconciled; High resolved                                     | 100/100 | 1) Add coverage alert thresholds for macro/factor null spikes [72/100].        |
| Final Verification | Dry-runs, writes, and pytest evidence captured                                 | 100/100 | 1) Monitor feed horizon gaps in ops checks [70/100].                           |
| CI/CD              | SAW closure packet + validator outputs                                          | 100/100 | 1) Move to next Phase 23 integration step [88/100].                            |
+--------------------+--------------------------------------------------------------------------------+--------+----------------------------------------------------------------------------------+

Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| scripts/ingest_compustat_sdm.py | Fixed `merge_asof` sort/assert contract; added dynamic `totalq` probing; allow+audit policy; dry-run audit skip | Reviewed |
| scripts/assemble_sdm_features.py | Added PIT-safe asof assembler with tolerance + sector context attach + atomic write | Reviewed |
| tests/test_ingest_compustat_sdm.py | Added regression coverage for sort guard, dynamic columns, audit behavior (including dry-run no-write) | Reviewed |
| tests/test_assemble_sdm_features.py | Added assembler asof/tolerance tests and FF required-column gate test | Reviewed |
| docs/prd.md | Added Phase 23 SDM ingestion section (FR-100) | Reviewed |
| docs/spec.md | Added Phase 23 ingestion/assembly contract addendum | Reviewed |
| docs/phase_brief/phase23-brief.md | Added active Phase 23 execution brief, checks, evidence, rollback | Reviewed |
| docs/runbook_ops.md | Added SDM ingest/assemble operational commands and outputs | Reviewed |
| docs/notes.md | Added explicit formulas and `.py` references for merge/order, PIT, and assembler joins | Reviewed |
| docs/lessonss.md | Added new lesson entry for `merge_asof` global sort rule | Reviewed |
| docs/decision log.md | Added D-108 decision entry for SDM ingestion hardening | Reviewed |

Document Sorting (GitHub-optimized)
1. `docs/prd.md`, `docs/spec.md`
2. `docs/phase_brief/phase23-brief.md`
3. `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`
4. `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md`

Open Risks:
- `frb.rates_daily` feed in current runtime ends 2025-02-13; macro joins are null for later fundamentals rows.
- `ff.fivefactors_daily` currently ends 2025-12-31; early-2026 fundamentals rows have missing factor joins.
- Assembler currently fail-fasts on missing/empty dependencies; no optional degrade-mode path yet.

Next action:
- Add feed-horizon alerts and optional empty-input operational mode in `scripts/assemble_sdm_features.py`, then rerun the same scoped ingestion window.

SAW Verdict: PASS
ClosurePacket: RoundID=R23_D1_20260222_R3; ScopeID=phase23_step2_sdm_ingest_assembler; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=Macro/FF source horizon gaps and no optional empty-input degrade mode; NextAction=Add feed-horizon alerts and optional empty-input mode then rerun scoped window
ClosureValidation: PASS
SAWBlockValidation: PASS
