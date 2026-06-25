# V2 PEAD D2B Market-Session Spine Repair

Mode: `EXECUTION_PACKET`
Status: terminal Reviewer A/B/C rerun PASS; D2B session-spine repair reviewer-promoted, D3 publication still separate
Date: 2026-06-19
RoundID: `ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR`
ScopeID: `V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE`
Owner: Data + Docs/Ops

## Objective and boundary

Repair the D2B market-session spine without changing D2B security-selection
semantics. D2A security-level return rows remain immutable input evidence, but
their distinct dates no longer define the market calendar. The authoritative
session spine is the official Ken French daily factor date set restricted to
the D2A sample range.

This round does not publish a D3 benchmark artifact, calculate or interpret
CAR/BHAR, run quintiles, change dashboard behavior, rank or score candidates,
emit alerts, touch broker/order paths, run a full build, stage files, or commit.

## Acceptance criteria

- [x] Independent Reviewer B/C rerun for the D3 partial round returns no new Critical/High finding.
- [x] The 52 D2A dates absent from official Ken French daily factors are classified as non-session dates and excluded only from the D2B market-session spine.
- [x] D2B selection remains prior-20 authoritative sessions, minimum 15 finite `dollar_volume` observations, and deterministic score/count/IID/security order.
- [x] No benchmark date is filled, dropped, interpolated, zeroed, substituted, or spliced inside D3.
- [x] Corrected D2B output keeps 12,582 events and 754,920 rows with exactly 60 rows per event and no within-event security switch.
- [x] Immutable D2B output and atomic manifest publish successfully while preserving the prior hash-named artifact.
- [x] D3 reconstructs and hash-validates the explicit upstream session source and produces 2,810 complete benchmark rows in memory without publication.
- [x] Full strategy handoff uses the same 2,810-session spine and produces only complete `+1..+60` rows for eligible events.
- [x] Full D2A validation is chunked before selected-security return materialization; the active-scale strategy handoff completes without a full-frame D2A copy/sort.
- [x] Final independent Reviewer A/B/C rerun after all fixes. PASS on 2026-06-20; no in-scope Critical/High findings.

## Implementation

- `scripts/pead_d2b_event_window_contract.py`
  - accepts an explicit authoritative market-session spine;
  - records official source release/hash/member/URLs in the D2B manifest;
  - records all excluded D2A dates;
  - preserves fixed-security selection and missing-return semantics;
  - passes the same explicit spine to the strategy handoff.
- `scripts/pead_d3_benchmark_artifact.py`
  - validates the D2B session-source provenance against the exact Ken French source bytes;
  - reconstructs the required sessions from that source and verifies the D2B session hash;
  - leaves benchmark-return construction and fail-closed publication rules unchanged.
- `tests/test_pead_d2b_event_window_contract.py`
  - proves a closed date cannot enter liquidity selection or event windows.
  - proves strategy handoff validates unselected D2A rows in bounded chunks and never calls the full-frame normalizer.
  - proves cross-row event metadata drift and normalization-colliding D2A duplicate keys fail closed.
- `tests/test_pead_d3_benchmark_artifact.py`
  - proves authoritative source provenance and session hashes fail closed on drift.

## Evidence delta

- Session count: `2,862 -> 2,810`.
- Excluded non-session dates: `52`.
- Event rows: `754,920 -> 754,920`.
- Events: `12,582 -> 12,582`.
- Selected-security changes under the same rule: `2 / 12,582`.
- Eligible handoffs: `4,867 -> 11,450`.
- Eligibility transitions: `6,583 false -> true`; `0 true -> false`.
- Coverage after repair: 11,450 complete; 592 missing/non-finite; 526 insufficient sessions; 14 no eligible security.
- New D2B SHA256: `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`.
- Prior D2B SHA256 retained: `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`.
- D3 in-memory coverage: 2,810 / 2,810, zero missing, no D3 artifact published.
- Strategy smoke: 11,450 events; 911,707 unique canonical return rows; 687,000 complete strategy rows; zero duplicate keys and zero closed dates.
- Active-scale memory smoke: loaded RSS 1,222.4 MiB; handoff RSS 1,271.4 MiB; process peak 1,756.7 MiB; no `ArrayMemoryError`.
- Focused validation: 70 tests passed.
- Historical terminal SAW: `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md` is BLOCK because final independent Reviewer A/B/C could not run after the last code fixes.
- Final rerun SAW: `docs/saw_reports/saw_v2_d2b_session_spine_repair_rerun_20260620.md` is PASS after Reviewer A/B/C reran against the repaired state.

## Formula and invariants

`S_raw = unique(D2A.date)`

`S_market = {d in KenFrenchDaily.return_date | min(S_raw) <= d <= max(S_raw)}`

`S_excluded = S_raw \ S_market`

For event `e`, selection and event-window offsets use `S_market`; D2A return
values are joined only on the resulting authoritative dates. No return is
imputed. Selection is recomputed against the repaired prior-20-session
calendar, then that one selected security remains fixed across all 60 rows.

## Risk and rollback

- Medium follow-up: D3 downloader should validate the final redirect host.
- Medium follow-up: D3 publication tests should add partial-write,
  `BaseException`, and post-commit interruption coverage.
- Medium follow-up: retain the exact source ZIP bytes or an approved immutable
  source cache if future release reconstruction must not depend on remote
  availability.
- Rollback: atomically restore the prior D2B manifest bytes pointing to SHA
  `8e2f39...`; retain both immutable Parquet objects and validate the restored
  manifest/hash before readers resume.

## Next decision

The final independent Reviewer A/B/C gate now passes. The next decision is
whether to approve or hold a separate D3 benchmark artifact publication round.
This repair proves coverage but does not itself authorize D3 publication or PEAD
interpretation.
