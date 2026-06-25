# V2-D0.1 Scope and Clean-Room Runtime Decision - 2026-06-02

Final verdict: ADVISORY_PASS for scope clarification and TODO-state update only. This decision does not authorize WRDS/provider access, credentials, read-only probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, or legacy cleanup.

Update - TODO-MATRIX-001 bookkeeping: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING` resolved the offline permission-truth metadata gap with `v2_discovery/data_lab/permission_truth.py` and `tests/test_v2_wrds_permission_truth_scope.py`. Focused evidence: `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_truth_scope.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` PASS, 51 passed; `.venv\Scripts\python -m compileall v2_discovery\data_lab tests\test_v2_wrds_permission_truth_scope.py -q` PASS. This does not authorize WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, or legacy cleanup.

## Agreement

| Decision | Agreement | Confidence | Result |
|---|---:|---:|---|
| V2-D0.1 requests all five default rows now while PEAD_V2_001 starter uses four-row Compustat PEAD set | AGREE_HIGH | 9/10 | Accept |
| Credentialed clean-room runtime excludes `schema_registry.py` by default | AGREE_HIGH | 8.5/10 | Accept |

## Row-Scope Decision

V2-D0.1 entitlement-truth request covers all five default rows:

| Row | V2-D0.1 status | Approval rule |
|---|---|---|
| `crsp.dsf` | `pending` once requested | approved only with table-specific `approval_ref` |
| `crsp.stocknames` | `pending` once requested | approved only with table-specific `approval_ref` |
| `crsp.ccmxpf_linktable` | `pending` once requested | approved only with explicit CCM/link-table evidence |
| `comp.fundq` | `pending` once requested | approved only with Compustat evidence |
| `ibes.det_epsus` | `pending` once requested | approved only with exact I/B/E/S table-level `approval_ref` |

PEAD_V2_001 starter execution is scoped to the four-row Compustat PEAD set:

| Row | PEAD_V2_001 starter status |
|---|---|
| `crsp.dsf` | required |
| `crsp.stocknames` | required |
| `crsp.ccmxpf_linktable` | required |
| `comp.fundq` | required |
| `ibes.det_epsus` | `not_requested` |

Do not mark `ibes.det_epsus` as `unknown` inside PEAD_V2_001 starter. It is deliberately outside the starter dependency set, even if V2-D0.1 entitlement truth is requested in parallel.

If a future artifact has only one `permission_status` field, set `ibes.det_epsus = pending` because the artifact is V2-D0.1 entitlement truth. Add separate PEAD scope metadata, for example:

```json
{
  "dataset_id": "ibes_detail_eps_us",
  "library_table": "ibes.det_epsus",
  "v2_d0_1_entitlement_status": "pending",
  "pead_v2_001_starter_scope": "not_requested",
  "reason": "PEAD_V2_001 starter is Compustat-rdq PEAD, not analyst-estimate-surprise PEAD."
}
```

## Clean-Room Runtime Decision

For a future credentialed clean-room read-only WRDS permission probe, exclude `schema_registry.py` from credentialed runtime by default.

Credentialed runtime default:

- `v2_discovery/data_lab/permission_matrix.py`
- `v2_discovery/data_lab/wrds_probe.py`, only if patched, reviewed, and actually needed
- `contracts/data_snapshot/wrds_permission_matrix.schema.json`
- `probe/v2_d0_1_permission_probe_result.schema.json`
- `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json`

Non-credentialed review/source anchor:

- `v2_discovery/data_lab/schema_registry.py`

`schema_registry.py` may enter credentialed runtime only by explicit exception when all are true:

1. The probe runner has a hard reviewed import dependency on it.
2. The file is hash-pinned in `ALLOWLIST.sha256`.
3. It performs only local/static validation.
4. It does not import provider clients, WRDS, `data.provenance`, root `data/**`, or root runtime code.
5. It does not enumerate schemas, tables, columns, libraries, row counts, or provider metadata.
6. `IMPORT_PROVENANCE.json` proves it resolved only inside the clean surface.
7. `FORBIDDEN_SCAN_RESULTS.txt` shows no schema-discovery or provider-output primitives.

## TODO State

| TODO ID | Status | Note |
|---|---|---|
| `TODO-PEAD-DECISION-001` | RESOLVED | PEAD_V2_001 starter is four-row Compustat PEAD; `ibes.det_epsus` is `not_requested` for starter. |
| `TODO-CLEANROOM-RUNTIME-001` | RESOLVED | `schema_registry.py` is excluded from credentialed runtime by default. |
| `TODO-ENTITLEMENT-001` | PENDING | Non-secret entitlement evidence for all five V2-D0.1 rows is still missing. |
| `TODO-APPROVAL-001` | PENDING | Explicit V2-D0.1 approval text is still missing. |
| `TODO-CLEANROOM-001` | PENDING | Full clean-room surface, allowlist, manifest, import provenance, forbidden scan, ledger, and post-run proof are not built. |
| `TODO-MATRIX-001` | RESOLVED | Offline V2-D0.1 permission-truth metadata/builder exists in `v2_discovery/data_lab/permission_truth.py`; approved rows still require row/table `approval_ref` and `allowed_uses=["provenance_contract"]`. |
| `TODO-LEGACY-WRDS-001` | OPEN | Legacy WRDS/BvD triage/cleanup authority remains unapproved. |
| `TODO-VALIDITY-001` | PENDING | V2 alpha validity packet and `C3_LOCK_PEAD_V2_001_v1` are not built. |
| `TODO-PUBLIC-MAIN-001` | OPEN | Public/main status mismatch remains unresolved. |

## Boundary

This decision clarifies scope and runtime surface only. It does not authorize provider access, credentials, read-only probe execution, snapshot generation, data output, `data/processed` writes, runtime writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, or legacy cleanup.
