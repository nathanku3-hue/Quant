# M7F5-ID0 DATED_IDENTIFIER_AUTHORITY

Mode: `EXECUTION_PACKET`
RoundID: `ROUND-20260714-M7F5-ID0-DATED-IDENTIFIER-AUTHORITY`
ScopeID: `M7F5_ID0_DATED_IDENTIFIER_AUTHORITY_COMMIT_A`
Branch: `c0x/m7f4-v8`
Base: `ea0da956fd9dca4da47801d7a0a45b39c45a3251`
Implementation: `m7f5-id0`

Hierarchy Confirmation: Approved by owner after G0 independent audit PASS | Session: current-thread | Trigger: historical/as-of data authority | Domains: Quant Research, Data Integrity, Docs/Ops | FallbackSource: M7F4-v8 terminal brief plus repository specification

## Recommended next action

Bank Commit A only: a standalone validator, focused tests, and this brief. Run it against the locked D1 artifact and the current Compustat security master. The required current result is `BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SOURCE_ABSENT`. Do not acquire historical identifiers or reopen portfolio mechanics in this round.

## Purpose

M7F4-v8 is durably closed as a mechanically valid diagnostic, but research validity remains near 30/100 because identity was selected through a current snapshot rather than a dated as-of authority. M7F5-ID0 establishes the smallest fail-closed decision gate before any further strict-PIT work.

This round answers one question only:

> Does a supplied Compustat identifier source contain unambiguous effective-date intervals that uniquely identify every locked pre-identity 2019 D1 event as of its RDQ?

## Functional slices

### Slice A0 — immutable pre-identity universe lock

The validator must reconstruct the event population directly from D1 before any identifier join:

- D1 Parquet SHA-256: `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Cohort: valid, non-null clipped-SUE events with RDQ in calendar 2019.
- Unique identity before mapping: `(gvkey, rdq)`.
- Locked count: `21,882`.
- Event-set SHA-256 over sorted `gvkey|YYYY-MM-DD` lines: `2922192aba299a7ab741e2ff1183f033291312614fbb4b3dce60f760fe7e06a5`.
- Canonical-row SHA-256 over sorted compact JSON `{gvkey, rdq, sue}`: `3592137066ad74290e988ac06f4b6e29ccce64fc29ce8be4e864a3d0b7a882bd`.

Any mismatch returns `BLOCKED_D1_PRE_IDENTITY_LOCK_MISMATCH` and skips identifier-source evaluation. Neither the 16,843 mapped subset nor the 2,448 selected portfolio subset may replace this universe.

### Slice A1 — dated-source authority decision

The source must provide:

- `gvkey`;
- a normalized eight-character security identifier from an explicitly named or canonical identifier column;
- a genuine effective-start column;
- a genuine effective-end column, nullable only for an open-ended interval.

`updated_at`, file modification time, extraction time, or source maximum date are load/snapshot metadata and are never effective-date authority.

For every locked event, exactly one active source row and one identifier must satisfy:

`effective_start <= rdq <= effective_end`, with null `effective_end` treated as open-ended.

Missing coverage, invalid intervals, overlapping active rows, or multiple active identifiers block separately. No best-effort mapping is emitted.

### Slice A2 — deterministic evidence interface

The CLI prints deterministic, sorted JSON and may atomically write the same evidence to an explicit output path. Blocked research states exit successfully as evaluated evidence; malformed or unreadable inputs exit `2` without partial output.

The evidence must declare all of the following false:

- historical identifier acquisition authority;
- provider access authority;
- mapping-artifact generation authority;
- portfolio or curve execution authority;
- readiness promotion authority.

### Slice A3 — focused validation

Tests must cover:

- exact locked constants;
- pre-identity filtering and shuffle-stable hashes;
- current snapshot-only master blocker;
- complete unique dated-source PASS;
- missing event coverage;
- overlapping intervals;
- invalid interval order;
- D1 lock failure before source evaluation;
- explicit effective-column pairing;
- deterministic atomic evidence output.

## Current-source expected result

`data/processed/security_master_compustat.parquet` currently has 75,913 rows, one non-null `updated_at` value from 2026, and no effective-date interval pair. Its deterministic result must be:

`BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SOURCE_ABSENT`

This blocker is evidence that the required authority is absent, not a request to infer dates from the snapshot.

## P0 / P1 risks

### P0

- Treating `updated_at` or source-max-date as historical identity authority.
- Locking a post-identity mapped/selected subset instead of all 21,882 pre-identity events.
- Allowing overlapping intervals or duplicate active rows to pass because they share the same identifier.

### P1

- Non-deterministic evidence hashes or output bytes.
- Partial output after an input or write failure.
- Accidental imports from M7F4, portfolio accounting, strategy, provider, or UI paths.

## Expected Commit A paths

- `docs/phase_brief/v2-pead-m7f5-id0-dated-identifier-authority.md`
- `scripts/pead_m7f5_id0_dated_identifier_authority.py`
- `tests/test_pead_m7f5_id0_dated_identifier_authority.py`

No evidence JSON, current-truth reconciliation, acquisition request, source data, mapping Parquet, or research output belongs in Commit A.

## Acceptance checks

- The script imports no M7F4/v8 or portfolio module.
- D1 real bytes reproduce the exact locked count and both canonical hashes.
- The current Compustat master returns the exact required blocker.
- A valid synthetic dated source passes only with complete one-row-per-event coverage.
- Missing, invalid, overlapping, and ambiguous interval cases fail closed.
- Compile and focused tests pass.
- Two real CLI runs produce byte-identical evidence.
- Git status contains only the three expected Commit A paths.

## Forbidden scope

- Historical identifier acquisition, WRDS/provider login, credentials, API calls, or source extraction.
- Identifier map publication or use in event selection.
- Imports or calls into M7F4/v8, portfolio accounting, curve, Shapley, or sensitivity paths.
- Curve, return, ledger, map, or portfolio reruns.
- Readiness, strict-curve, PIT, alpha, tradability, Strategy, or UI promotion.
- Event allowlists or inferred effective dates.
- Current-truth/SAW closure before independent review.
- Remote, push, merge, dispatch, or publication.

## Rollback

Commit A is additive. Rollback removes only the three expected paths. It does not alter M7F4-v8 code, evidence, ignored Parquets, current data files, or terminal closure truth.

## Live loop

- G0 independent audit of `ea0da956` — PASS.
- Slice A0/A1/A2 implementation — active in Commit A worktree.
- Focused validation and real current-source evidence — pending.
- Independent Reviewer A/B/C and terminal truth reconciliation — not part of Commit A and not yet authorized as closure.

## Decision after evidence

If the current source returns the required absence blocker, choose exactly one separately authorized next action:

1. authorize acquisition of a historical/effective-dated identifier source; or
2. terminate PEAD strict-PIT work.

No additional mechanics round is justified by this gate.
