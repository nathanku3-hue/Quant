SAW Round Report

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource | Domains: Data, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase23-brief.md

RoundID: R23_SDM_STEP2_RC_20260222
ScopeID: phase23_step2_sdm_ingest_assembler
Scope: Reviewer C pass covering scripts/ingest_compustat_sdm.py, scripts/ingest_frb_macro.py, scripts/ingest_ff_factors.py, scripts/assemble_sdm_features.py, and the processed parquet outputs for data integrity/performance.

Acceptance Checks
- CHK-01: merge_asof sort bug fixed with timeline-first ordering and assertions -> PASS.
- CHK-02: 	otalq.total_q dynamic schema probing + graceful fallback implemented -> PASS.
- CHK-03: allow+audit unmapped permno policy implemented without row drops -> PASS.
- CHK-04: Pillar 3b source fixed to f.fivefactors_daily with 5 factors + momentum -> PASS.
- CHK-05: ssemble_sdm_features.py implemented with PIT-safe asof joins -> PASS.
- CHK-06: atomic writes preserved for all output artifacts -> PASS.
- CHK-07: dry-run validation passes on all 4 scripts -> PASS.
- CHK-08: non-dry execution writes all 4 target parquets -> PASS.

Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | rb.rates_daily stops at 2025-02-13 but fundamentals extend through 2025/2026, leaving 31 rows with yield_slope_10y2y and other macro columns null after the backward merge_asof. | Refresh the FRB feed past 2025-02-13 or gate fundamentals/releases so that macro joins always find a match (or emit alerts when tolerance fails). | Data / Updater | Open |
| Medium | f.fivefactors_daily ends at 2025-12-31, so the four published_at rows in early 2026 have mktrf/factor columns null in eatures_sdm.parquet. | Backfill the FF factors feed or delay new feature builds until the factor history includes the requested dates. | Data / Updater | Open |
| Low | k_int (Pillar 2) remains null for about 22 rows (the earliest quarter per ticker) because 	otalq.total_q does not cover those gvkey+datadate pairs. | Log or gate scoring on those quarters, or source earlier annual filings so that k_int and derived trajectories can populate the feature matrix. | Data / Updater | Observed |

Scope Split Summary
- in-scope: review of PIT guard, join cardinality, null patterns, and data completeness for the ingestion/assembler scripts and their parquet outputs.
- inherited: none.

Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| docs/saw_phase23_step2_review_c.md | Added Reviewer C data-integrity/performance pass for Phase 23 SDM ingestion/assembly and documented findings/open risks. | Reviewed |

Open Risks:
- FRB macro feed stops at 2025-02-13, so any fundamentals row with published_at > 2025-02-13 is missing macro-derived signals even though the tolerance window is 7 days (eatures_sdm shows 31 rows with null yield_slope_10y2y).
- FF factors feed stops at 2025-12-31, so the earliest 2026 published_at rows do not have mktrf/factor inputs, leaving the feature matrix incomplete for those shipments.

Next action:
- Coordinate a refresh/backfill of the FRB and FF datasets or gate new published_at rows to the current data window before exposing the downstream feature matrix to scoring flows.

SAW Verdict: PASS
ClosurePacket: RoundID=R23_SDM_STEP2_RC_20260222; ScopeID=phase23_step2_sdm_ingest_assembler; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=FRB macro feed cuts off at 2025-02-13 (31 rows lose macro columns) and FF factors stop at 2025-12-31 (early-2026 rows lose mktrf); NextAction=Refresh/backfill FRB+FF feeds or gate published_at dates before enabling the new feature matrix.
ClosureValidation: PASS
SAWBlockValidation: PASS
