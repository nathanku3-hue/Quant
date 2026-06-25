# V2-D0.1 Expert 1-6 Follow-Up Reconciliation - 2026-06-02

Final verdict: ADVISORY_PASS for guidance capture and TODO marking only. This document does not authorize WRDS/provider access, read-only probe execution, credentials, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, or BootReady.

Superseding note: `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME` resolves the PEAD starter question after this follow-up. PEAD_V2_001 starter is now the four-row Compustat PEAD set, and `ibes.det_epsus` is `not_requested` for starter scope.

Superseding note: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING` resolves `TODO-MATRIX-001` after this follow-up. The offline builder and validator now live at `v2_discovery/data_lab/permission_truth.py`, with regression coverage in `tests/test_v2_wrds_permission_truth_scope.py`.

## Agreement Matrix

| Expert | Agreement | Confidence | Disposition |
|---|---:|---:|---|
| Data / WRDS Provenance | AGREE_HIGH | 8.5/10 | Record five-row V2-D0.1 entitlement scope and separate PEAD starter scope. |
| Backend / Data Contract | AGREE_HIGH | 9/10 | Record `PATCH_RESOLVED_LOCAL`; current local validators already cover raw-payload strictness. |
| Architecture / Governance | AGREE_HIGH | 8.5/10 | Record clean-room probe-surface definition and dirty-root classification rule. |
| Quant Research | PARTIAL_AGREE_HIGH | 7.5/10 | Accept `PEAD_V2_001` label and kill gates; mark primary-signal conflict with Data/WRDS. |
| Research Validity / Statistical Methods | AGREE_HIGH | 8.5/10 | Record fail-closed validity thresholds and C3 lock requirement. |
| Security / Ops / Compliance | AGREE_HIGH | 9/10 | Record approval addendum, audit schema, denylist, stop rules, and legacy WRDS sequence. |

## Reconciled Decisions

### Data / WRDS Provenance

V2-D0.1 entitlement truth should request the five default packet rows:

| Dataset ID | Exact library.table | V2-D0.1 target | PEAD Compustat starter |
|---|---|---|---|
| `crsp_daily_stock_file` | `crsp.dsf` | request entitlement truth | required |
| `crsp_stocknames` | `crsp.stocknames` | request entitlement truth | required |
| `crsp_ccm_linktable` | `crsp.ccmxpf_linktable` | request entitlement truth | required |
| `compustat_fundamentals_quarterly` | `comp.fundq` | request entitlement truth | required |
| `ibes_detail_eps_us` | `ibes.det_epsus` | request entitlement truth | not requested for Compustat starter |

Rows outside those five remain `not_requested` unless a later matrix amendment explicitly adds them. No substitute tables, summary tables, TAQ, OptionMetrics, Zacks, FactSet, Orbis/BvD, or alternate link table is implied.

Evidence must be non-secret, dated, attributable, table-specific, and must prove account authority, vendor/product entitlement, exact table scope, approved use, and constraints. Successful login, old query output, library lists, row counts, raw SQL logs, or prior activity are not entitlement evidence.

### Backend / Data Contract

The expert's PATCH_REQUIRED warning is accepted as correct for an exact-key-only patch, but current local code has already moved beyond that state. Local direct validators now reject raw-payload drift such as uppercase provider/status/use values, non-string timestamps and row fields, non-bool `pit_required`, non-string notes, uppercase SHA values, backslash schema URI, invalid dataset status, non-string primary keys, and non-string/null release-date fields.

Disposition: `PATCH_RESOLVED_LOCAL`; public/main merge status remains `TODO-PUBLIC-MAIN-001`.

For a future V2-D0.1 permission-truth artifact, use one permission-matrix artifact only. Do not add a probe artifact, provider adapter, credential reference, query text, output path, snapshot manifest refresh, or generated data artifact. For V2-D0.1 approved rows, `allowed_uses` should be limited to `["provenance_contract"]` until separate approval authorizes a read-only probe, schema discovery, or PIT snapshot design.

Do not reuse the V2-D0 default permission-matrix builder output as the V2-D0.1 approved permission-truth artifact unless every approved row is explicitly overridden to `allowed_uses=["provenance_contract"]`. The V2-D0 default matrix can carry future planning labels, but it is not a provider-facing approval artifact and is not proof that read-only probe, schema discovery, or PIT snapshot design is authorized.

Direct Python validators should remain standalone and strict. JSON Schema wrappers should run JSON Schema validation and then direct Python validation. Direct validators should not depend on schema files internally.

### Architecture / Governance

A clean isolated probe surface is not the current Quant root, not a clone of the root, and not a copied working tree. It must be created from empty state, populated by explicit SHA256 allowlist, credential-minimal, not importable from the dirty root, and able to emit only sanitized permission-status evidence.

Dirty-root classification is deferred only for a sealed clean-room probe surface that never imports, copies, mounts, or consults the root. Dirty-root classification is mandatory before merge-back, root-derived evidence, snapshots, dashboard/runtime integration, scoring/ranking, broker/alert paths, promotion, SafeBoot, or BootReady.

The clean-room allowlist and proof packet are accepted as governance requirements for any future provider-facing permission probe, but they do not authorize that probe.

### Quant Research

The first lane label is `PEAD_V2_001`, not `PEAD Variant Factory`.

Accepted first-packet constraints:

- fixed event flag, surprise bucket, liquidity filter, and post-event return window only.
- no analyst revisions, volume shock, gap return, short interest, options, meta-labeling, ML, Orbis/BvD, dynamic holding period, neutralization tuning, or post-result best-cell selection.
- hard kill if PIT/provenance, net effect, monotonicity, OOS stability, cost/liquidity, or scope gates fail.

Conflict to resolve: Data/WRDS allows a four-row Compustat-rdq PEAD starter that excludes I/B/E/S, while Quant Research prefers the first primary PEAD hypothesis to use I/B/E/S analyst EPS surprise. This is a real decision gap, not a documentation typo.

### Research Validity / Statistical Methods

Default V2 validity gates are fail-closed:

- one-sided 95% HAC lower confidence bound on annualized daily net alpha delta vs locked C3 must be greater than zero.
- annualized daily net alpha delta point estimate must be at least +2.00% per year vs locked C3.
- FDR family-level adjusted q must be at most 0.05.
- DSR confidence must be at least 0.95 after effective-trial adjustment.
- PBO must be at most 0.10 for `research_valid`.
- base cost and 2x cost stress must pass.
- PEAD also needs at least +5 bps one-way adverse slippage stress unless a larger model-based stress applies.

No `C3_LOCK_PEAD_V2_001_v1` means no `research_valid` PEAD claim. Without a PIT event ledger or canonical engine run, status is `blocked`, not exploratory.

### Security / Ops / Compliance

The credential/access addendum is accepted as the required future approval shape, provided it is target-specific, signed or recorded, expires, and is validated against an approved-target allowlist.

The audit schema must use `additionalProperties: false`, allow only redacted permission-classification fields, and reject any credential, SQL/query, provider discovery, row/schema/count/sample, file-output, cache, raw exception, provider payload, or freeform text field.

Legacy WRDS scripts and outputs require risk-based handling before any probe approval:

- secret-bearing material: rotate first, delete working-tree copy, and history-scrub if committed or pushed.
- non-secret runnable provider code: disable and quarantine outside importable paths.
- WRDS-derived outputs: delete from repo/release paths or compliance-quarantine only if retention is legally required.
- unknown dirty/untracked WRDS material: blocks approval until triaged.

## Real Follow-Up Questions

1. Data/WRDS and Quant Research: Should the first PEAD starter be four-row Compustat-rdq PEAD, or I/B/E/S analyst-surprise PEAD? This determines whether `ibes.det_epsus` is only V2-D0.1 pending entitlement truth or also required for the first PEAD research packet.
2. Architecture/Governance, only if moving toward a probe: Should the credentialed clean-room allowlist include `schema_registry.py`, or should runtime validation use only permission-matrix code plus a local audit schema?
3. Security/Ops, only before probe approval or cleanup: Should secret-bearing legacy WRDS material be rotated/deleted/history-scrubbed now, or should all legacy cleanup remain on hold until explicit security-remediation approval?

No new question is needed for Backend/Data Contract or Research Validity/Stats; both produced concrete enough gates to record.

## TODO Gaps

| TODO ID | Gap | Owner | Status |
|---|---|---|---|
| `TODO-ENTITLEMENT-001` | Non-secret V2-D0.1 entitlement evidence for the five default rows is missing. | Data Authority / User Source | PENDING |
| `TODO-APPROVAL-001` | Explicit V2-D0.1 approval text is missing. | Data Authority / Security | PENDING |
| `TODO-PEAD-DECISION-001` | Choose I/B/E/S analyst-surprise PEAD vs Compustat-rdq PEAD starter. | Quant Research / PM | RESOLVED by `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME` |
| `TODO-CLEANROOM-001` | Clean-room probe allowlist, policy, manifest, and proof packet are not built. | Architecture / Security | PENDING |
| `TODO-LEGACY-WRDS-001` | Legacy WRDS/BvD file triage, rotate/delete/history-scrub/quarantine decision is not approved or complete. | Security / Ops | OPEN |
| `TODO-VALIDITY-001` | V2 alpha validity packet and `C3_LOCK_PEAD_V2_001_v1` manifest are not built. | Research Validity | PENDING |
| `TODO-PUBLIC-MAIN-001` | Public/main status may lag local V2-D0.1 patches and remains unresolved. | Repo Maintainer | OPEN |
| `TODO-MATRIX-001` | V2-D0.1-specific permission-truth builder and validator now exist; default V2-D0 matrix output still must not be reused as an approved V2-D0.1 artifact without narrowing `allowed_uses` to `["provenance_contract"]`. | Backend/Data | RESOLVED by `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING` |

## Boundary

This follow-up records agreement levels, confidence, high-value questions, and TODO gaps only. It does not authorize WRDS/provider access, credentials, probe execution, snapshot generation, data output, data/processed writes, runtime writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, BootReady, or legacy cleanup operations.
