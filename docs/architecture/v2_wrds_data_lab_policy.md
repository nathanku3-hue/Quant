# V2-D0 WRDS Data Lab Policy

Status: Contract-only implementation
Date: 2026-06-01
Owner: Data / Backend + Docs/Ops
RoundID: ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT
ScopeID: V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT

## 2026-06-02 V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping Addendum

RoundID: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING`
ScopeID: `V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING`

`TODO-MATRIX-001` is resolved for offline V2-D0.1 permission-truth metadata by `v2_discovery/data_lab/permission_truth.py`.

- V2-D0.1 has exactly five default rows: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`.
- Each V2-D0.1 row is `pending` by default.
- A row can become `approved` only with a row/table-specific `approval_ref`.
- Approved rows have `allowed_uses` strictly equal to `["provenance_contract"]`.
- PEAD_V2_001 starter scope is separate; `ibes.det_epsus` is `pending` for V2-D0.1 and `not_requested` for PEAD_V2_001 starter.

Evidence: focused V2 permission-truth/matrix/snapshot/no-write suite PASS, 51 passed; compileall `v2_discovery\data_lab` plus permission-truth test PASS.

This addendum does not authorize WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, legacy cleanup, public/main closure, or V2 validity/C3 lock claims.

## 2026-06-02 V2-D0.1 Scope and Clean-Room Runtime Decision Addendum

Decision handover: `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`

Accepted decisions:

- V2-D0.1 entitlement-truth request covers all five default rows now.
- PEAD_V2_001 starter execution is scoped to the four-row Compustat PEAD set.
- `ibes.det_epsus` is `pending` for V2-D0.1 once requested, but `not_requested` for PEAD_V2_001 starter.
- `schema_registry.py` is excluded from credentialed clean-room runtime by default and remains a non-credentialed review/source anchor unless explicit exception criteria are met.

Rows:

| Scope | Rows | I/B/E/S status |
|---|---|---|
| V2-D0.1 entitlement truth | `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus` | `pending` once requested |
| PEAD_V2_001 starter | `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq` | `not_requested` |

Runtime rule: credentialed runtime uses the narrower surface. `schema_registry.py` is not included by default because the probe should classify permission status only, not table schemas or provider metadata.

Superseded guard: `TODO-MATRIX-001` is resolved by `v2_discovery/data_lab/permission_truth.py`; entitlement evidence and explicit approval text remain pending.

## 2026-06-02 V2-D0.1 Expert 1-6 Follow-Up Addendum

Follow-up handover: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`

Agreement status:

- Data / WRDS Provenance: `AGREE_HIGH`, confidence `8.5/10`.
- Backend / Data Contract: `AGREE_HIGH`, confidence `9/10`, status `PATCH_RESOLVED_LOCAL`.
- Architecture / Governance: `AGREE_HIGH`, confidence `8.5/10`.
- Quant Research: `PARTIAL_AGREE_HIGH`, confidence `7.5/10`, in the earlier follow-up because the PEAD starter signal was still unresolved then. Superseding decision: PEAD_V2_001 starter is now the four-row Compustat PEAD set.
- Research Validity / Statistical Methods: `AGREE_HIGH`, confidence `8.5/10`.
- Security / Ops / Compliance: `AGREE_HIGH`, confidence `9/10`.

V2-D0.1 entitlement-truth rows:

- `crsp.dsf`
- `crsp.stocknames`
- `crsp.ccmxpf_linktable`
- `comp.fundq`
- `ibes.det_epsus`

Rows outside those five remain `not_requested` unless a later permission-matrix amendment explicitly adds them.

Clean-room rule: a future credentialed probe surface must be created from empty state by SHA256 allowlist, must not copy or import the Quant root, and must emit only redacted permission-status evidence. Dirty-root classification can be deferred only for that sealed clean-room probe, and is mandatory before merge-back or any root-derived claim.

Security rule: the approval addendum, audit schema, denylist, stop rules, and legacy WRDS triage/rotation/quarantine sequence are future gates only. They do not authorize provider access or legacy cleanup in this round.

Open TODOs: `TODO-ENTITLEMENT-001`, `TODO-APPROVAL-001`, `TODO-CLEANROOM-001`, `TODO-LEGACY-WRDS-001`, `TODO-VALIDITY-001`, `TODO-PUBLIC-MAIN-001`. `TODO-PEAD-DECISION-001` is superseded/resolved by the four-row Compustat PEAD starter decision.

Matrix guard: the V2-D0 default permission matrix is not the V2-D0.1 approved permission-truth artifact. A V2-D0.1-specific builder or explicit row override must narrow approved rows to `allowed_uses=["provenance_contract"]` before any permission-truth artifact can be treated as approved-row evidence. The default V2-D0 allowed-use planning labels do not authorize read-only probe, schema discovery, or PIT snapshot design.

Resolved TODO: `TODO-MATRIX-001` is now closed by `v2_discovery/data_lab/permission_truth.py`; entitlement evidence and explicit approval text remain pending.

## Authority

This policy implements the approved immediate next stream after the G9 FINRA packet ADVISORY_PASS decision:

- G9 is accepted as static context-only evidence.
- Dashboard reader remains HOLD.
- V2-D0 is the active main stream.

V2-D0 is an offline permission and provenance contract only. It does not authorize WRDS/provider access, live probe execution, PIT snapshot generation, committed WRDS outputs, V1 canonical data writes, dashboard runtime integration, candidate ranking, candidate scoring, alerts, recommendations, broker/order paths, SQLite storage, SafeBoot, or BootReady claims.

## Implemented Contract

Runtime-neutral contract modules:

- `v2_discovery/data_lab/wrds_probe.py`
- `v2_discovery/data_lab/permission_matrix.py`
- `v2_discovery/data_lab/snapshot_manifest.py`
- `v2_discovery/data_lab/schema_registry.py`

Schema contracts:

- `contracts/data_snapshot/wrds_permission_matrix.schema.json`
- `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`

Focused tests:

- `tests/test_v2_wrds_permission_matrix.py`
- `tests/test_v2_snapshot_manifest_contract.py`
- `tests/test_v2_data_lab_no_v1_writes.py`

## Permission Matrix

The permission matrix records intended WRDS datasets and their permission truth without opening a network connection.

Initial dataset rows:

- `crsp_daily_stock_file`
- `crsp_stocknames`
- `crsp_ccm_linktable`
- `compustat_fundamentals_quarterly`
- `ibes_detail_eps_us`

Root flags must remain false:

- `provider_access_allowed`
- `snapshot_generation_allowed`
- `data_output_allowed`
- `v1_canonical_write_allowed`

An entry may be marked `approved` only with an explicit `approval_ref`.

## Snapshot Manifest Contract

The snapshot manifest is a planned manifest contract, not a generated snapshot manifest. It records:

- `manifest_status = contract_only`
- `provider = wrds`
- `planned_storage_uri = data/runtime_cache/v2_data_lab/wrds_snapshots/v2_d0_contract_only/`
- permission matrix id and stable hash
- dataset primary keys and PIT fields
- release-date and effective-date fields where known

Forbidden storage targets are rejected:

- `data/processed/`
- `data/registry/`
- `runtime/boot_status_current.json`
- `docs/context/boot_status_current.json`

## PIT Policy

The V2-D0 snapshot contract is valid only when all PIT policy flags remain true:

- `point_in_time_required`
- `release_date_required`
- `no_future_leakage`
- `snapshot_as_of_required`
- `extraction_log_required`
- `manifest_hash_required`

## Formula Register

`permission_matrix_sha256 = sha256(canonical_json(permission_matrix_without_created_at_utc))`

Source path: `v2_discovery/data_lab/permission_matrix.py`

`snapshot_manifest_valid = true iff provider_access_allowed=false AND snapshot_generation_allowed=false AND committed_wrds_output_allowed=false AND data_output_allowed=false AND v1_canonical_write_allowed=false AND PIT policy flags are all true AND planned_storage_uri is outside forbidden V1/boot paths`

Source path: `v2_discovery/data_lab/snapshot_manifest.py`

## Acceptance Checks

- Permission matrix validates through dataclass and JSON Schema.
- WRDS probe contract is offline-only and records no connection attempt.
- Snapshot manifest validates through dataclass and JSON Schema.
- Snapshot storage cannot target V1 canonical, registry, or boot-status paths.
- Data lab modules expose no provider, Streamlit, alert, broker, candidate promotion, parquet-write, CSV-write, manifest-write, or atomic-write primitives.
- Builders do not modify existing V1 data or boot-status artifacts.

## Logic Chain

G9 context-only signal artifact -> V2-D0 permission matrix -> contract-only snapshot manifest -> schema registry validation -> later explicit approval for any read-only WRDS probe or snapshot generation.

## Rollback

Remove the `v2_discovery/data_lab/` package, `contracts/data_snapshot/` schema files, and the three focused V2-D0 test files. No generated data, runtime cache, V1 canonical artifact, boot status, provider credential, dashboard surface, candidate registry, alert, broker path, or SQLite store is created by this policy.
