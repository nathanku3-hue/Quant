# M7F5-ID0 DATED_IDENTIFIER_AUTHORITY

Mode: `EXECUTION_PACKET`
RoundID: `ROUND-20260714-M7F5-ID0-DATED-IDENTIFIER-AUTHORITY`
ScopeID: `M7F5_ID0_DATED_IDENTIFIER_AUTHORITY_COMMIT_A`
Branch: `c0x/m7f4-v8`
Base: `ea0da956fd9dca4da47801d7a0a45b39c45a3251`
Implementation: `m7f5-id0`

Hierarchy Confirmation: Approved by owner after G0 independent audit PASS | Session: current-thread | Trigger: historical/as-of data authority | Domains: Quant Research, Data Integrity, Docs/Ops | FallbackSource: M7F4-v8 terminal brief plus repository specification

## Recommended next action

Bank Commit A only after the standalone validator, focused tests, and this brief prove that no caller-created JSON can authorize owner identity. Then publish deterministic BLOCK evidence as Commit B and stop before the terminal Reviewer A/B/C+SAW rerun. The required current-source result is `BLOCKED_DATED_COMPUSTAT_IDENTIFIER_PROVENANCE_REQUIRED`. Do not acquire historical identifiers or reopen portfolio mechanics in this round.

## Purpose

M7F4-v8 is durably closed as a mechanically valid diagnostic, but research validity remains near 30/100 because identity was selected through a current snapshot rather than a dated as-of authority. M7F5-ID0 establishes the smallest fail-closed decision gate before any further strict-PIT work.

This round answers one question only:

> Does an exact Compustat identifier source, together with an exact-byte semantics envelope and a repository-authoritative committed data-owner approval blob, establish unambiguous identifier-validity intervals that uniquely identify every locked pre-identity 2019 D1 event as of its RDQ?

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

The source must provide the columns named by a detached exact-byte source-semantics envelope and approved by a committed repository authority object:

- a `gvkey` binding;
- an identifier binding with explicit type `CUSIP`, `CUSIP8`, or `NCUSIP`;
- a genuine effective-start binding for identifier validity;
- a genuine effective-end binding for identifier validity, nullable only for an open-ended interval.

Direct CLI/API column binding is removed and cannot authorize semantics. The detached JSON envelope uses schema `pead_m7f5_id0_source_semantics_v2` and binds only nonblank dataset name/version, exact source SHA-256, all four source columns, identifier type, interval meaning exactly `IDENTIFIER_VALIDITY`, inclusive start and end, and null end as open-ended. It contains no owner, role, approval reference, or decision field; unexpected attestation fields fail structurally.

Authority is accepted only from a regular JSON blob under `docs/authorization/` at an exact full Git commit ID in the current repository. The approval commit must resolve exactly, be reachable from raw `HEAD`, and the exact blob must still be present unchanged at `HEAD`; deletion or mutation is revocation. The committed object uses schema `pead_m7f5_id0_git_blob_approval_v1` and binds the exact envelope SHA-256, source SHA-256, dataset name/version, owner identity, role `DATA_OWNER`, approval reference, scope `M7F5_ID0_DATED_IDENTIFIER_AUTHORITY`, decision `APPROVED`, and the complete identifier-validity binding. Ambient Git redirection, replacement objects, global/system configuration, loose files, abbreviated object IDs, noncanonical paths, non-blob entries, and blobs outside `docs/authorization/` cannot supply authority. Repository authority is not a cryptographic natural-person signature; terminal review must still validate the committed owner record and branch governance.

Duplicate JSON keys, malformed structure, missing or extra fields, unsupported semantics, source/envelope hash mismatch, approval-scope mismatch, revoked approval, and missing bound columns fail closed. Column names alone—including unrelated `employment_start/employment_end` or generic relationship pairs such as `start_date/end_date`, `linkdt/linkenddt`, and `namedt/nameendt`—never establish identifier-validity semantics.

Identifier values must retain lexical scalar-string provenance; numeric, categorical, nested, and list-valued inputs are not string-coerced because leading zeros or singular identity may already be lost. Original trimmed values must match the ASCII shape before case normalization, so Unicode case folding cannot create authority. A `CUSIP` value must be exactly 8 ASCII alphanumeric characters or 9 with a numeric ninth character that matches the computed CUSIP check digit; `CUSIP8` and `NCUSIP` must be exactly 8 ASCII alphanumeric characters. Unsupported punctuation, embedded spaces, invalid or nonnumeric check digits, and other lengths fail closed instead of being removed or truncated.

`updated_at`, file modification time, extraction time, or source maximum date are load/snapshot metadata and are never effective-date authority. A null effective end is open-ended; blank, whitespace, or unparsable non-null values are invalid intervals.

For every locked event, exactly one active source row and one identifier must satisfy:

`effective_start <= rdq <= effective_end`, with null `effective_end` treated as open-ended.

Missing coverage, invalid intervals, overlapping active rows, or multiple active identifiers block separately. No best-effort mapping is emitted.

### Slice A2 — deterministic evidence interface

The CLI prints deterministic, sorted JSON and may atomically write the same evidence to an explicit output path. The output must not resolve to, link to, or otherwise alias the D1 input, identifier source, or provenance envelope; the envelope must also be detached from both Parquet inputs. Each Parquet is copied once into a private immutable snapshot while hashing, and parsing uses that exact snapshot, so an A→B→A source replacement cannot bind parsed rows to different reported bytes. The envelope is parsed and hashed from the same exact byte payload with duplicate-key rejection. The approval is read only from the verified Git blob, never from a caller-supplied filesystem path. Blocked research states exit successfully as evaluated evidence; malformed or unreadable inputs or partial authority arguments exit `2` without partial output. Output-write failures return controlled exit `3` without a traceback or partial file.

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
- removal of direct three-column self-authorization and generic relationship-date rejection;
- unrelated `employment_start/employment_end` columns without an envelope;
- valid committed Git-blob approval PASS plus absent authority, envelope-only invocation, caller-attestation rejection, duplicate keys, source/envelope-hash mismatch, owner-role/scope mismatch, unsupported interval semantics, blank fields, missing bound columns, approval revocation, path confinement, and ambient Git redirection isolation;
- malformed non-null ends, blank bindings, non-string/non-scalar identifier values, Unicode case-expansion attempts, malformed/overlong/punctuated identifiers, and invalid CUSIP9 check digits;
- mixed missing-plus-overlap blocker preservation;
- immutable-snapshot read/hash binding, including A→B→A replacement;
- direct-path and hardlink output/input alias rejection;
- deterministic atomic evidence output and partial cleanup after replace failure.

## Current-source expected result

`data/processed/security_master_compustat.parquet` currently has 75,913 rows, one non-null `updated_at` value from 2026, and no effective-date interval pair. Its deterministic result must be:

`BLOCKED_DATED_COMPUSTAT_IDENTIFIER_PROVENANCE_REQUIRED`

This blocker is evidence that the current bytes have neither dated identifier intervals nor a repository-authoritative committed approval binding exact source and envelope bytes. It is not a request to infer dates from the snapshot or to treat load metadata as identifier validity.

Executable clean-checkout command (using the canonical data checkout explicitly):

`E:\Code\Quant\.venv\Scripts\python.exe E:\Code\Quant_c0x_m7f4_v8\scripts\pead_m7f5_id0_dated_identifier_authority.py --d1 E:\Code\Quant\data\processed\pead_d1_sue_signal.parquet --identifier-source E:\Code\Quant\data\processed\security_master_compustat.parquet`

A candidate dated source may be evaluated only by supplying all three of `--provenance-envelope <detached-json>`, `--approval-commit <full-object-id>`, and `--approval-path <docs/authorization/...json>`. The validator never creates, commits, repairs, or signs either authority object.

## P0 / P1 risks

### P0

- Treating direct column names, `updated_at`, or source-max-date as historical identity authority.
- Accepting a caller-created envelope as approval, or accepting a committed approval whose envelope hash, source hash, owner role, scope, dataset/version, or identifier-validity semantics do not bind the evaluated bytes.
- Treating repository blob authority as cryptographic proof of a natural person's identity; terminal review and repository governance remain required.
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
- A valid synthetic dated source passes only with a detached exact-byte semantics envelope plus an unchanged, reachable committed Git approval blob that binds owner, scope, both hashes, and complete identifier-validity semantics.
- Missing authority, envelope-only input, malformed/duplicate-key objects, caller attestation, source/envelope hash mismatch, revoked or misplaced approval, invalid semantics/bindings, malformed intervals, overlap, missing coverage, and ambiguity all fail closed without losing simultaneous blocker reasons.
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
- Repair commit `e4122330a794bad7bd27b849ebbec482e7d43952` — compile, 22/22 tests, and two byte-identical real runs PASS; Reviewer B PASS, Reviewer A/C BLOCK on adversarial identifier, blank-binding, and A→B→A findings.
- Repair commit `d7f38973af9e3c8df9320b6a758e86a4a38ae66b` — compile, 28/28 tests, and two byte-identical real runs PASS; Reviewer B/C PASS, Reviewer A BLOCK on missing CUSIP9 checksum validation.
- Checksum repair commit `93822b57e7be94a78a176505484dd852e0f45cb1` — compile, 34/34 tests, and two byte-identical real runs PASS; Reviewer A/B PASS, Reviewer C BLOCK on numeric identifier string coercion.
- Lexical repair commit `0e6d708da227bb49cabf2d8015ebad6e6d130736` — compile, 36/36 tests, and two byte-identical real runs PASS; Reviewer A/B/C BLOCK on Unicode case expansion and list-valued identifier crash paths.
- Scalar-safe ASCII-order validator/test/brief repair — superseded by the authority-object repair.
- Detached-provenance candidate — superseded because caller-created owner and approval strings could self-authorize synthetic bytes despite 47/47 tests.
- Repository-authoritative approval hard replacement — complete in the same three Commit A paths: the envelope is semantics-only; authority is an exact, reachable, unchanged Git blob under `docs/authorization/` in this checkout only, binding owner, scope, envelope hash, source hash, and full identifier-validity semantics. No CLI or Python evaluation parameter can redirect the authority repository.
- Compile and 59/59 focused tests — PASS, including caller-attestation rejection, approval binding mismatches, duplicate committed keys, unreachable commits, revocation, path confinement, and ambient Git redirection isolation.
- Two real current-source runs — byte-identical, schema `pead_m7f5_id0_dated_identifier_authority_v2`, runtime/check-out evidence SHA-256 `4abd0112cd535bb1250952296860d8e3d7c160e4bcd510ec97091427580aa903`, committed Git-blob evidence SHA-256 `f15bac8a6b8702b5c91d915812821605a3b4e33253d11ccee3dfd59ee9816913`, and returned `BLOCKED_DATED_COMPUSTAT_IDENTIFIER_PROVENANCE_REQUIRED` with reason `committed_git_blob_data_owner_approval_required`, the locked 21,882-event universe, and both canonical hashes.
- Commit A banking — PASS at `c5a9ab8377d3a455b003a5166e9b1f93e8dc686e`.
- Deterministic evidence Commit B banking — PASS at `410d0caf327646de2447e049ae0d1d66482e7c8a`; evidence path `docs/context/e2e_evidence/pead_m7f5_id0_dated_identifier_authority_20260714.json`.
- Terminal Reviewer A/B/C+SAW rerun — in progress after A/B banking; no truth closure before PASS.
- Acquisition, mapping, curves, readiness, Strategy/UI, and current-truth reconciliation remain closed.

## Decision after evidence

If the current source returns the required provenance blocker, choose exactly one separately authorized next action:

1. obtain a genuine effective-dated source plus a repository-authoritative committed data-owner approval object binding its exact semantics envelope and source bytes;
2. authorize acquisition of a historical/effective-dated identifier source; or
3. terminate PEAD strict-PIT work.

No additional mechanics round is justified by this gate, and none of these decisions is authorized by the present implementation repair.
