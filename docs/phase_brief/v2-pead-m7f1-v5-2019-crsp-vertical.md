# M7F1-v5.2-final 2019 CRSP Formation-First Vertical

Mode: `EXECUTION_PACKET`  
RoundID: `ROUND-20260712-M7F1-V5-2-FINAL`  
ScopeID: `M7F1_V5_2_FINAL_2019_FORMATION_FIRST_VERTICAL`  
Branch: `c0x/m7f0-v4`  
Implementation: `m7f1-v5.2-final`

## Purpose

Replace non-durable M7F1-v5/v5.1 diagnostic BLOCK with a commit-bound package:
formation-first selection, source-wide session spine, forced map rebuild, and an
**explicit roadmap-deviation** prior-20 formation tradability gate.

## Roadmap deviation (mandatory record)

**Prior-20 gate is a formation-time tradability restriction, not a map repair.**

- Gate: ≥15/20 strictly pre-entry source sessions with finite `RET`, `abs(PRC)>0`, `VOL>0` (`VOL=0` fails).
- Does not use full-sample `max_date` for selection.
- First/last PERMNO date mismatch is **post-hoc diagnostic only**.
- Does not restore pre-Q5 complete-60 / future-return selection filters.

## Contract locks

1. No entry-day / future-return filter at selection.
2. Formation entry = first CRSP session strictly after RDQ on **source-wide** spine.
3. Panel load includes ≥20 source sessions before 2019 so January can evaluate prior-20.
4. Dedup one event per `(formation_date, PERMNO)` before breadth/Q5.
5. Pre-Q5 prior-20 observability (roadmap deviation above).
6. Breadth = distinct PERMNOs ≥ 50; Q5 = top `floor(n/5)` by SUE.
7. Suppress later event entirely on entry-overlap with earlier 60-session claim.
8. Post-select resolve 60-session windows; any invalid selected window BLOCKs.
9. Equal-weight active slots including post-delist cash.
10. Map always rebuilt; `cross_vintage_snapshot_cusip8_non_pit`.
11. Stale daily curve invalidated on BLOCK.
12. Commit sequence: A code/tests → rerun → B evidence/truth → C A/B/C+SAW pinned to B.

## Filter order

1. unique_permno_map  
2. assign_formation_entry_source_wide_spine_only_no_return_filter  
3. dedup_one_event_per_formation_date_permno  
4. pre_q5_prior20_observability_tradability_gate  
5. formation_breadth_distinct_permno_ge_50  
6. deterministic_q5  
7. suppress_later_event_on_entry_overlap  
8. resolve_selected_windows_or_block  
9. equal_weight_active_slots_incl_cash  

## Claim ceiling

- Flagged research only; not alpha; not tradable; `m6b_data_contract_ready=false`
- Link: non-PIT snapshot CUSIP8; research validity ceiling ~30
- Score: PASS target 68–72; durable residual BLOCK ~62

## Forbidden

- Strict readiness flip; alpha/tradable; multi-year expansion; as-of/historical-link claim
- UI/strategy promotion; WRDS login; silent pre-Q5 complete-60 filters
- Map reuse; leaving stale PASS curve after BLOCK
- Closing evidence + terminal review in one commit (B and C must separate)

## Commit protocol

| Commit | Contents |
|--------|----------|
| A | code + tests + this brief only; clean worktree |
| B | evidence JSON, manifests, truth surfaces (after rerun from A) |
| C | full independent Reviewer A/B/C + SAW pinned to B |

## Run outcome (2019, Commit A `138c8b7`)

| Metric | Value |
|--------|------:|
| D1 valid 2019 events | 21,882 |
| Unique mapped events | 16,843 |
| Pre-Q5 prior20 ok / fail | 15,793 / 1,050 |
| Formation dates ≥50 | 88 |
| Q5 before overlap | 2,612 |
| Suppressed entry-overlap | 164 |
| Q5 after overlap / selected | 2,448 |
| Selected OK windows | 2,441 |
| Selected invalid | 7 |
| Invalid breakdown | nonnumeric=5, unresolved_delist=1, missing_session=1 |
| Daily curve | **not promoted** (`curve_status=ABSENT`) |
| Status | `BLOCKED` (durable residual) |
| Score band note | ~62 durable residual BLOCK |
| Evidence SHA-256 | `0927826206247ea0ac07ce9c59afa196ac9982bc99c3cc90e0d1675626bba292` |
| Map builder | `source_max_date_one_to_one_cusip8_permno` (always rebuilt) |
| Panel load | 2018-11-30 .. 2020-12-31 (≥20 pre-2019 sessions) |
