# Governed Data Artifact Authorization - 2026-05-28

Status: authorization packet only
RoundID: ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION
ScopeID: SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS
StartingVerdict: BLOCK
Recommended path: B - bounded offline regeneration authorization packet

## Current Gate Truth

```text
GovernanceGateV0: PASS
BootStatusPathContract: PASS
StrictProof: PASS/degraded
DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS
SafeBoot: false
BootReady: BLOCKED
```

Core caveat: local artifacts and dirty context are not clean GitHub truth and are not BootReady evidence. This packet may authorize the next governed intake/regeneration decision, but it does not prove strict boot readiness.

## Decision Options

| Option | Path | Use When | Verdict |
| --- | --- | --- | --- |
| A | External artifact bundle | A trusted, signed, schema-matched bundle already exists and can be reviewed without boot/runtime writes. | Accept only with manifest/hash proof. |
| B | Bounded offline regeneration | No trusted bundle exists, but source inputs, generator commands, schemas, owners, validation, and rollback rules can be approved before generation. | Recommended path. |
| C | BootReady quarantine | No trusted bundle and no approved regeneration path exists. | Keep BootReady blocked and quarantine strict data readiness. |

Decision: choose B unless a trusted external bundle exists and passes the same manifest, schema, freshness, and owner approval checks.

## Missing Artifact Authorization Contracts

### 1. `data/processed/prices_tri.parquet`

| Field | Contract |
| --- | --- |
| Source input path | Approved offline total-return price source bundle or governed staging input recorded in the intake manifest; boot must not fetch it. |
| Generator command/external source | Operator-approved offline market data generation command, run outside boot; exact argv must be recorded before execution. |
| Schema contract | Date-indexed or date-columned wide price/total-return frame; unique dates; unique asset columns; numeric finite route-required values; no slot-swapped returns/prices. |
| As-of/freshness policy | As-of date must be explicit in manifest; strict route assets must cover the requested replay/current window and endpoint freshness policy. |
| Hash/manifest output | SHA256 for parquet file plus row count, column count, min/max date, source bundle id, generator argv, and as_of date in a governed manifest. |
| Owner/approval | Data owner approval plus boot/governance reviewer signoff before strict readiness can consume it. |
| Local-governed vs tracked policy | Local-governed artifact by default; do not commit `data/processed` unless policy changes explicitly. |
| Expected validation command | `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict --repo-root .` only if confirmed read-only for this check. |
| Rollback/removal rule | Remove the local file and manifest entry together if schema, hash, provenance, or freshness fails; BootReady remains blocked. |

### 2. `data/processed/prices.parquet`

| Field | Contract |
| --- | --- |
| Source input path | Approved offline adjusted/local price source bundle or governed staging input recorded in the intake manifest. |
| Generator command/external source | Operator-approved offline price generation command or trusted external artifact bundle; no provider calls during boot. |
| Schema contract | Date-indexed or date-columned wide price frame; unique dates/assets; numeric nonnegative price values where required; compatible with loader return semantics. |
| As-of/freshness policy | Manifest must record as_of date; selected/current strict assets must not require stale endpoint repair during boot. |
| Hash/manifest output | SHA256, row count, column count, min/max date, source id, generator argv or external bundle id, and as_of date. |
| Owner/approval | Data owner approval plus reviewer confirmation that fallback use is policy-allowed when `prices_tri.parquet` is absent. |
| Local-governed vs tracked policy | Local-governed artifact by default; not tracked unless the data policy changes. |
| Expected validation command | `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict --repo-root .` only after read-only behavior is confirmed. |
| Rollback/removal rule | Remove artifact and manifest entry on any provenance/schema/freshness failure; do not substitute placeholders. |

### 3. `data/processed/tickers.parquet`

| Field | Contract |
| --- | --- |
| Source input path | Approved offline identifier map source or governed staging map recorded in the intake manifest. |
| Generator command/external source | Operator-approved offline ticker/permno map build or trusted bundle intake; no boot-time provider lookup. |
| Schema contract | Must map ticker to stable asset id/permno for route-required selected assets; required keys non-null; duplicate conflicting mappings fail. |
| As-of/freshness policy | Manifest must include map vintage/as_of; route assets must resolve for the strict check window. |
| Hash/manifest output | SHA256, row count, key coverage summary, duplicate/conflict count, source id, and map vintage/as_of. |
| Owner/approval | Data owner approval and strategy/replay reviewer acceptance for selected-asset mapping coverage. |
| Local-governed vs tracked policy | Local-governed artifact by default; keep out of Git unless policy changes. |
| Expected validation command | `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict --repo-root .` after confirming read-only gate behavior. |
| Rollback/removal rule | Remove artifact and manifest entry if coverage, duplicate, or provenance checks fail; strict readiness stays blocked. |

### 4. `data/processed/universe_r3000_daily.parquet`

| Field | Contract |
| --- | --- |
| Source input path | Approved offline PIT Russell 3000 membership source or governed staging universe input recorded in the intake manifest. |
| Generator command/external source | Operator-approved offline PIT universe builder or trusted external bundle; no generation during boot. |
| Schema contract | Daily PIT membership with `date` and stable asset id/permno; no duplicate `(date, permno)` rows; covers requested replay window. |
| As-of/freshness policy | Manifest must record membership source vintage and covered date range; strict replay fails if requested dates are outside coverage. |
| Hash/manifest output | SHA256, row count, min/max date, unique asset count, duplicate-key count, source id, and as_of/vintage. |
| Owner/approval | Data owner approval plus reviewer confirmation that PIT discipline is preserved. |
| Local-governed vs tracked policy | Local-governed artifact by default; do not commit under `data/processed` without explicit policy change. |
| Expected validation command | `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict --repo-root .` only as a read-only validation pass. |
| Rollback/removal rule | Remove artifact and manifest entry if PIT coverage, duplicate-key, hash, or provenance proof fails. |

### 5. `data/processed/rule100_softmax_v1_history.csv`

| Field | Contract |
| --- | --- |
| Source input path | Approved offline Rule100 candidate/evidence history input or governed strategy-evidence staging path recorded in the intake manifest. |
| Generator command/external source | Operator-approved offline Rule100 history builder or trusted external evidence bundle; never generated during boot. |
| Schema contract | CSV with selected-method history columns required by Rule of 100 replay; dates parse cleanly; selected method rows have finite required scores/weights/status fields. |
| As-of/freshness policy | Manifest must record evidence window and as_of date; strict Rule100 replay fails when the requested window/method is not covered. |
| Hash/manifest output | SHA256, row count, min/max date, method id, source evidence id, generator argv or bundle id, and as_of date. |
| Owner/approval | Strategy owner plus data/governance reviewer approval before strict Rule100 readiness can consume it. |
| Local-governed vs tracked policy | Local-governed evidence artifact by default; do not commit `data/processed` unless policy changes. |
| Expected validation command | `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict --repo-root .` only when confirmed read-only. |
| Rollback/removal rule | Remove CSV and manifest entry if schema, evidence provenance, method id, or freshness fails; no placeholder CSV allowed. |

## Explicit Forbidden Actions

```text
no boot_preflight.py patch
no DataReadyStrict weakening
no generation during boot
no placeholder parquet/CSV
no data/processed commit unless policy changes
no runtime/boot_status_current.json edit
no BootReady claim
```

## Read-Only Validation Commands

These commands are validation/intake checks only. They must not generate data, patch boot code, or edit runtime status.

```powershell
git ls-files -- data/processed/prices_tri.parquet data/processed/prices.parquet data/processed/tickers.parquet data/processed/universe_r3000_daily.parquet data/processed/rule100_softmax_v1_history.csv
git check-ignore -v data/processed/prices_tri.parquet data/processed/prices.parquet data/processed/tickers.parquet data/processed/universe_r3000_daily.parquet data/processed/rule100_softmax_v1_history.csv
.venv\Scripts\python scripts\run_data_readiness_gate.py --strict --repo-root .
rg -n "BootReady:\s+P[A]SS|SafeBoot:\s+tr[u]e|DataReadyStrict:\s+P[A]SS|no BootReady claim|no DataReadyStrict weakening|no generation during boot|no placeholder parquet/CSV|no runtime/boot_status_current.json edit" docs/architecture/governed_data_artifact_authorization_20260528.md
```

Warning: `launch.py --preflight --strict` is not a valid validation command for this docs-only artifact-authorization packet while inherited boot-control diffs and data-readiness deferral remain unresolved. Do not use launch preflight output as DataReadyStrict or BootReady proof for this packet; it belongs to a separate boot-control readiness round after those inherited diffs are classified and resolved.

Use `scripts\run_data_readiness_gate.py --strict` only after confirming the invocation is read-only or uses an explicit no-write-status mode if available. If it would write status or generate artifacts, skip it and keep `BootReady: BLOCKED`.

## Acceptance Criteria

- This file exists as the sole new architecture packet/artifact for this implementation pass; current truth surfaces were refreshed separately.
- All five missing artifact paths are listed with source input path, generator/external source, schema, freshness, hash/manifest, owner/approval, local-governed vs tracked policy, expected validation, and rollback/removal rule.
- Option B is selected unless a trusted external bundle exists.
- Forbidden actions are explicit and unchanged.
- Validation commands are read-only in intent, exclude launch preflight, and include artifact tracking/ignore checks plus forbidden-claim `rg` checks.
- No data is generated, no boot code is patched, no data readiness gate is weakened, no `runtime/boot_status_current.json` edit is made, and no BootReady claim is made.

## Rollback Note

Rollback is documentation-only: remove this authorization packet if the round is superseded or rejected. If any governed artifact is later introduced and then fails provenance, schema, hash, freshness, or owner-approval checks, remove the local artifact and its manifest entry together, keep `DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS` or the relevant blocked reason, and do not claim BootReady.
