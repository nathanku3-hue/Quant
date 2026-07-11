# V2 PEAD M6b Gate A Definition and Session-Mapping Contract Request

Status: `PROPOSED_FOR_DATA_OWNER_APPROVAL`  
RoundID: `ROUND-20260701-V2-PEAD-M6B-STRICT-DATA-PHASE0-SUCCESSOR`  
ScopeID: `V2_PEAD_M6B_STRICT_DATA_PHASE0_DOCS_ONLY`  
Authority: Definition and request-contract artifact only; not source access, entitlement proof, export authority, provider access, archive inspection, factual gate validation, or readiness authority.

## Historical lineage

- Supersedes: `docs/authorization/V2_PEAD_M6B_GATE_A_EPS_DEFINITION_CONTRACT_REQUEST_20260630.md`
- Prior Markdown SHA-256: `14e139629e7da4f864808f64869f0f822ebd0d1bb52d06f28f51a797aa6f98e3`
- Prior machine contract: `docs/authorization/V2_PEAD_M6B_GATE_A_EPS_DEFINITION_CONTRACT_REQUEST_20260630.json`
- Prior machine-contract SHA-256: `78487de768b1f399e8b9ea4837858b50e46f79b71959c45757603d2f86257374`
- Historical artifacts are preserved without modification.

The authoritative machine-readable successor is:

`docs/authorization/V2_PEAD_M6B_GATE_A_EPS_DEFINITION_CONTRACT_REQUEST_20260701.json`

SHA-256: `27a065e5a37d44acd5e423e448d0a894274b48215eb0bcfc32968d5ba5931063`

## Core Gate A definition

Strict Gate A selects only company-reported GAAP diluted EPS that the licensed dictionary explicitly identifies as the first public company earnings release for the issuer-quarter. Preliminary History is the primary candidate layer. Snapshot and PIT establish lineage; Unrestated Quarterly corroborates original 10-Q status. No later amended or restated record can replace the selected first-public record.

A missing or conflicting candidate fails closed. `comp_fundq` remains non-strict; `rdq` may be a cross-check only.

## Capability attestation at source-access approval

The data owner must provide a non-secret capability attestation **as part of approving the Gate A export/source-access request**, before any human export or agent inspection. It must identify exact licensed fields and dictionary definitions for first-public identity, revision/source status, minute-or-finer timing capability, timezone semantics, issuer-quarter identity, and date-ranged mapping.

## Conditional timing-artifact dependency

A separate timing artifact is required only when the selected EPS source record lacks a complete eligible release timestamp with unambiguous timezone semantics.

A complete eligible timestamp has minute-or-finer precision, an IANA zone or explicit UTC offset, deterministic conversion to UTC and exchange-local time, and deterministic association with the selected source record or issuer-quarter.

When timing is already complete on the selected EPS record:

```text
timing_artifact_required=false
timing_artifact_path=null
timing_artifact_sha256=null
timing_join_key=null
timing_join_cardinality=not_required
```

When a timing artifact is required, its path, SHA-256, and join key are non-null, and its join cardinality must be `one_to_one`. Any zero-match, many-match, ambiguous, or coverage-gap join fails closed.

## Authorized calendar source of record

Gate A source-access approval must bind an immutable calendar artifact with license/owner attestation, source identity, exchange timezone, version/export provenance, path, SHA-256, coverage, `is_trading_session`, `scheduled_close_local`, holiday dates, and early-close schedule.

Generic weekday logic, an undocumented cache, unpinned library behavior, undocumented services, and dynamic network lookups are prohibited.

Eligible trading sessions are all calendar dates where:

```text
is_trading_session=true
and scheduled_close_local is non-null
```

This includes normal and officially early-close trading dates.

## Executable daily decision-session rule

```text
decision_session =
  first eligible_trading_session date
  strictly later than
  release_local_exchange_date
```

Same-session entry is forbidden. Release-close classification is provenance only and does not alter `decision_session`.

## Session-mapping replay contract

Every selected or fail-closed candidate requires a staging-only mapping record with source identity/hash, raw timestamp/timezone, normalized UTC and exchange-local timestamps, timing-artifact fields, calendar identity/hash, event classification, scheduled close, rule result, and stable fail-closed reason.

Consistency requirements include:

- `is_trading_session=true` requires `normal_session` or `early_close_session`, with a non-null close timestamp on the same exchange-local date and timezone/offset.
- `is_trading_session=false` requires `holiday`, `weekend`, or `non_session`, with null close.
- `is_trading_session=null` requires `unclassifiable`, null close and decision session, and a stable fail-closed reason.
- Normal or early-close dates classify release timing as `before_close`, `at_close`, or `after_close`.
- Non-session dates classify release timing as `non_session`; unclassifiable dates as `unclassifiable`.

Reviewer C must reproduce mapping solely from authorized raw bytes, this locked contract, and the exact calendar artifact. No package defaults, generic weekday logic, private notes, or external service may supply unstated logic.

## Scope boundary

This request does not authorize credentials, `secret.txt`, provider access, APIs, downloads, export generation, raw-byte inspection, ETL, validator redesign, data outputs, Gate A factual validation, or readiness promotion.
