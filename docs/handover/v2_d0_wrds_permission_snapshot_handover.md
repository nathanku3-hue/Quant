# V2-D0 WRDS Permission + Snapshot Provenance Handover

Status: Contract-only handover
Date: 2026-06-01
Owner: Data / Backend + Docs/Ops
RoundID: ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT
ScopeID: V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT

## Executive Summary

V2-D0 starts the WRDS-backed V2 Edge Finder substrate without touching WRDS, generating snapshots, or changing V1 runtime behavior. The round adds offline contracts for permission truth, planned PIT snapshot provenance, and JSON Schema validation.

G9 remains ADVISORY_PASS as a context-only artifact. The dashboard reader remains on HOLD.

## Delivered Scope

- Added `v2_discovery/data_lab/` with permission matrix, offline WRDS probe contract, snapshot manifest contract, and schema registry helpers.
- Added JSON Schema contracts under `contracts/data_snapshot/`.
- Added focused tests for permission matrix behavior, snapshot manifest behavior, and no-V1-write guardrails.
- Added policy, current truth-surface updates, decision/notes/lessons entries, and SAW report.

## Deferred Scope

- WRDS provider access.
- Live read-only probe execution.
- PIT snapshot generation.
- Data output persistence.
- V1 canonical mutation.
- Dashboard reader/runtime integration.
- Candidate ranking, scoring, recommendations, alerts, broker/order paths, SQLite storage, SafeBoot, and BootReady.

## Derivation And Formula Register

`permission_matrix_sha256 = sha256(canonical_json(permission_matrix_without_created_at_utc))`

Source path: `v2_discovery/data_lab/permission_matrix.py`

`snapshot_contract_valid = all(root write/provider flags false) AND all PIT policy flags true AND planned_storage_uri not in forbidden V1/boot prefixes`

Source path: `v2_discovery/data_lab/snapshot_manifest.py`

## Logic Chain

G9 static context -> HOLD dashboard reader -> V2-D0 permission authority -> contract-only snapshot provenance -> schema validation -> later separate approval for WRDS access or snapshot generation.

## Evidence Matrix

```text
.venv\Scripts\python -m py_compile v2_discovery\data_lab\__init__.py v2_discovery\data_lab\permission_matrix.py v2_discovery\data_lab\wrds_probe.py v2_discovery\data_lab\snapshot_manifest.py v2_discovery\data_lab\schema_registry.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py
.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q
```

## Open Risks / Assumptions / Rollback

Open risks:

- Actual WRDS permission truth is still unknown until user/source approval supplies account/license evidence.
- Snapshot generation remains blocked and must not be inferred from the contract.
- Existing dirty-root inherited files remain outside this V2-D0 scope.

Assumptions:

- User decision approves V2-D0 contract work but not WRDS access or snapshot generation.
- Runtime cache is acceptable as a future planned sandbox path only; no file is written there in this round.

Rollback:

- Remove `v2_discovery/data_lab/`, `contracts/data_snapshot/`, and the three V2-D0 focused test files.
- Remove V2-D0 addenda from policy/handover/truth-surface docs.
- No generated data, V1 canonical artifact, boot-status file, provider credential, dashboard surface, or SQLite store requires cleanup.

## Next Roadmap

1. User/source approval for exact WRDS account/library/table permission truth.
2. If approved, add a read-only probe implementation with credentials excluded and no snapshot output.
3. If approved after probe, add bounded PIT snapshot generation under an approved runtime-cache path with manifest/hash/extraction logs.
4. Add schema-specific row-count and freshness checks per dataset.
5. Only after provenance passes, open PEAD/corporate-actions/meta-labeling lanes as research-only V2 work.

## New Context Packet

What was done:

- Added offline V2-D0 WRDS permission matrix and snapshot manifest contracts.
- Added JSON Schema validation and focused no-V1-write tests.
- Recorded G9 as context-only and dashboard reader as HOLD.

What is locked:

- No WRDS/provider access, snapshot generation, committed WRDS output, data/processed write, V1 canonical mutation, dashboard runtime integration, ranking/scoring, alerts, recommendations, broker/order paths, SQLite, SafeBoot, or BootReady.

What remains:

- Approve exact WRDS permission truth before any read-only probe.
- Separately approve snapshot generation, storage path, manifest policy, and rollback/removal before any data output.

Immediate first step:

```text
.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q
```

ConfirmationRequired: YES
NextPhaseApproval: PENDING
