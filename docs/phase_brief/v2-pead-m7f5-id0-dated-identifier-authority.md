# M7F5-ID0 DATED_IDENTIFIER_AUTHORITY

Mode: `EXECUTION_PACKET`
RoundID: `ROUND-20260714-M7F5-ID0-DATED-IDENTIFIER-AUTHORITY`
ScopeID: `M7F5_ID0_DATED_IDENTIFIER_AUTHORITY_COMMIT_A`
Branch: `c0x/m7f4-v8`
Base: `ea0da956fd9dca4da47801d7a0a45b39c45a3251`
Implementation: `m7f5-id0`

Hierarchy Confirmation: Approved by owner after G0 independent audit PASS | Session: current-thread | Trigger: historical/as-of data authority | Domains: Quant Research, Data Integrity, Docs/Ops | FallbackSource: M7F4-v8 terminal brief plus repository specification

## Recommended next action

Repair Commit A only in the standalone validator, focused tests, and this brief, then rerun independent Reviewer A/B/C against the immutable repair commit. The required current-source result remains `BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SOURCE_ABSENT`. Do not acquire historical identifiers or reopen portfolio mechanics in this round.

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
- a normalized eight-character security identifier from an explicitly bound identifier column;
- a genuine effective-start column explicitly bound to identifier validity;
- a genuine effective-end column explicitly bound to identifier validity, nullable only for an open-ended interval.

The identifier, effective-start, and effective-end columns must be supplied together through the CLI/API. Column names alone—including generic relationship pairs such as `start_date/end_date`, `linkdt/linkenddt`, and `namedt/nameendt`—never establish identifier-validity semantics. A `cusip` value may contain exactly 8 characters or a 9th check digit; `cusip8` and `ncusip` must contain exactly 8. Other lengths fail closed instead of being truncated.

`updated_at`, file modification time, extraction time, or source maximum date are load/snapshot metadata and are never effective-date authority. A null effective end is open-ended; blank, whitespace, or unparsable non-null values are invalid intervals.

For every locked event, exactly one active source row and one identifier must satisfy:

`effective_start <= rdq <= effective_end`, with null `effective_end` treated as open-ended.

Missing coverage, invalid intervals, overlapping active rows, or multiple active identifiers block separately. No best-effort mapping is emitted.

### Slice A2 — deterministic evidence interface

The CLI prints deterministic, sorted JSON and may atomically write the same evidence to an explicit output path. The output must not resolve to, link to, or otherwise alias either input. Each Parquet is hashed before and after its read so evidence cannot bind parsed rows to different bytes. Blocked research states exit successfully as evaluated evidence; malformed or unreadable inputs exit `2` without partial output.

The evidence must declare all of the following false:

- historical identifier acquisition authority;
- provider access authority;
- mapping-artifact generation authority;
- portfolio or curve execution authority;
- readiness promotion authority.

### Slice A3 — focused validation

Tests must cover:

- exact locked constants;
- pre-identity filtering, non-finite SUE exclusion, and shuffle-stable hashes;
- current snapshot-only master blocker;
- complete unique dated-source PASS;
- missing event coverage;
- overlapping intervals;
- invalid interval order;
- D1 lock failure before source evaluation;
- explicit three-column semantic binding and generic relationship-date rejection;
- malformed non-null ends and malformed/overlong identifiers;
- mixed missing-plus-overlap blocker preservation;
- read/hash drift rejection;
- direct-path and hardlink output/input alias rejection;
- deterministic atomic evidence output and partial cleanup after replace failure.

## Current-source expected result

`data/processed/security_master_compustat.parquet` currently has 75,913 rows, one non-null `updated_at` value from 2026, and no effective-date interval pair. Its deterministic result must be:

`BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SOURCE_ABSENT`

This blocker is evidence that the required authority is absent, not a request to infer dates from the snapshot.

Executable clean-checkout command (using the canonical data checkout explicitly):

`E:\Code\Quant\.venv\Scripts\python.exe E:\Code\Quant_c0x_m7f4_v8\scripts\pead_m7f5_id0_dated_identifier_authority.py --d1 E:\Code\Quant\data\processed\pead_d1_sue_signal.parquet --identifier-source E:\Code\Quant\data\processed\security_master_compustat.parquet`

A candidate dated source may be evaluated only by additionally supplying all three of `--identifier-column`, `--effective-start-column`, and `--effective-end-column` with provenance-backed semantics.

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
- A valid synthetic dated source passes only with explicitly bound semantics and complete one-row-per-event coverage.
- Missing, malformed, invalid, overlapping, and ambiguous interval cases fail closed without losing simultaneous blocker reasons.
- Output/input aliases and read/hash drift fail before evidence can overwrite or misdescribe input bytes.
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
- Commit A `466a485a3f1b91c697073d1ccec3fee386d13539` — created; initial Reviewer A/B/C verdict blocked on fail-closed defects.
- Validator/test/brief repair — active, restricted to the three Commit A paths.
- Compile and 22/22 focused tests — PASS.
- Two real current-source runs — byte-identical and returned the required absence blocker with the locked 21,882-event universe and both canonical hashes.
- Independent Reviewer A/B/C repair audit — pending against the immutable repair commit.
- Acquisition, mapping, curves, readiness, Strategy/UI, and current-truth reconciliation remain closed.

## Decision after evidence

If the current source returns the required absence blocker, choose exactly one separately authorized next action:

1. authorize acquisition of a historical/effective-dated identifier source; or
2. terminate PEAD strict-PIT work.

No additional mechanics round is justified by this gate.
