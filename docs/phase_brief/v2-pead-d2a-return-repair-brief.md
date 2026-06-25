# V2 PEAD D2A Security-Level Return Repair Brief

Mode: `EXECUTION_PACKET`
Status: D2A implementation, sample publication, and full Reviewer A/B/C SAW complete
Date: 2026-06-18
RoundID: `ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR`
ScopeID: `V2_D2A_SECURITY_LEVEL_TOTAL_RETURN_SAMPLE`
Owner: Data + Docs/Ops

## Objective

Repair the PEAD daily-return contract at security granularity and publish one atomic 500-GVKEY sample without widening into event-level primary-IID selection, event-window extraction, a full build, benchmark work, strategy interpretation, or UI integration.

## Contract

- Preserve every `(gvkey, iid)` time series through level and return construction.
- Define `security_id = gvkey + "-" + iid`.
- Define `TR_level_t = prccd_t * trfd_t / ajexdi_t` when all three inputs are finite and positive.
- Define canonical `total_return_t = TR_level_t / TR_level_{t-1} - 1`, with the lag taken only within `(gvkey, iid)`.
- When either total-return level is unavailable, use split-adjusted price level `prccd / ajexdi` and compute the fallback return within the same `(gvkey, iid)` series.
- Keep `dollar_volume` as a daily raw field. It is not ADV.
- Require output uniqueness on `(security_id, date)` and matching Parquet/manifest SHA256.
- Publish an immutable hash-named Parquet first, then atomically replace the stable manifest commit pointer under a single-writer OS lock; leave no temporary files.
- Require exactly 500 GVKEYs and reject `--build` during D2A.
- Reject `--event-window-only`; D2B owns fixed event-level IID selection and `+60` market-session extraction.

## Acceptance criteria

- [x] Formula, dividend, fallback, no-cross-IID, gap/extreme guardrail, duplicate, scope-gate, writer-lock, interruption, and atomic-pointer tests pass.
- [x] Formula identity matches source levels within numeric tolerance; observed maximum error is `0.0`.
- [x] More than 99% of rows with changed valid total-return levels produce nonzero canonical returns; observed share is `0.9999991170562655`.
- [x] Output is unique by `(security_id, date)` and preserves multiple IIDs per GVKEY: 795 securities across 500 GVKEYs, including 117 multi-IID GVKEYs.
- [x] Manifest records the exact formula, security counts, measured quality metrics, hash, superseded formula, pointer protocol, and D2B boundary.
- [x] The 500-GVKEY sample was rebuilt through the atomic manifest pointer and no temporary files remain.
- [x] Existing PEAD strategy contract tests remain green; focused D2A plus strategy suite is 32 passed.
- [x] Full Reviewer A/B/C SAW passes with no unresolved in-scope Critical/High finding.

## Ship-Fast Decision Gate

What is done: D1 is closed and the strategy contract is ready for corrected D1/D2 inputs.

What is blocked: D2B event-level IID selection and `+60` session extraction remain a separate, not-yet-started round.

User order interpreted as: repair only D2A security-level returns and the 500-GVKEY sample.

Recommended next step: start D2B fixed event-level IID selection and `+60` market-session extraction separately.

Why this is correct: issuer-level deduplication before lagging crosses security identities and the old `trfd_t / trfd_{t-1} - 1` formula omits the price level.

Alternatives considered: full-build, D2B event extraction, benchmark, provider, strategy, and dashboard work remain downstream and are excluded.

Decision needed from user: already supplied by `go`; no further D2A decision is open.

Scope limit: two code/test files plus required brief, product/spec, formula/decision/lesson, truth, context, sample, and SAW evidence artifacts.

Stop rule: stop on cross-IID lags, duplicate `(security_id,date)`, formula mismatch, non-atomic output, failed sample gates, or any need to change the D2B IID policy.

## Rollback

Restore the prior manifest pointer to its still-immutable referenced Parquet. Readers must resolve `manifest.parquet_file`; never mix a manifest with a different hash-named Parquet.

## Next action

After D2A passes, start D2B fixed event-level IID selection and `+60` market-session extraction in a separate round.
