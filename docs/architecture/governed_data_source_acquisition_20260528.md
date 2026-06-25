# Governed Data Source Acquisition / Bounded Regeneration Planning - 2026-05-28

Status: source-acquisition and bounded-regeneration planning packet only
RoundID: ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION
ScopeID: SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS
StartingVerdict: BLOCK
Recommended path: B - source acquisition + bounded offline regeneration planning, unless a trusted external governed bundle already exists

This packet approves planning and governed source acquisition only. It does not approve data generation, boot-time generation, placeholder artifacts, runtime status edits, or a BootReady claim.

## Current State

```text
GovernanceGateV0: PASS
BootStatusPathContract: PASS
GovernedDataAuthorizationPacket: PASS
StrictProof: PASS / DEGRADED
DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS
SafeBoot: false
BootReady: BLOCKED
RuntimeBootStatus: local / ignored / not commit evidence
```

BlockingReason: required canonical data artifacts are absent, ignored, or local-governed and are not backed by approved source manifests or approved generators.

Runtime boot status, ignored local artifacts, and dirty-worktree evidence are not commit evidence and do not prove strict data readiness.

## Correct Next Decision

| Option | Decision | Use When | Current Recommendation |
| --- | --- | --- | --- |
| A | Trusted external governed bundle | A complete signed bundle for all five required outputs already exists with manifest/hash/schema/source approval. | Accept only if the bundle exists and passes intake review. |
| B | Source acquisition + bounded offline regeneration | No trusted complete bundle exists, but source inputs, generator commands, manifests, validation, and rollback can be approved before any write. | Recommended path. |
| C | Quarantine BootReady | Neither trusted bundle nor approved source/regeneration plan exists. | Keep BootReady blocked. |

Decision rule: choose B unless a trusted governed bundle already exists. This round does not choose or run generation; it only defines the source inputs, generator boundaries, manifest format, validation gates, and rollback rules needed for a later approval.

## Shared Governance Rules

- No `boot_preflight.py` patch.
- No DataReadyStrict weakening.
- No placeholder parquet or CSV files.
- No data generation during boot.
- No edit to `runtime/boot_status_current.json`.
- No `data/processed` artifact commit unless data policy explicitly changes.
- No BootReady claim.
- All outputs remain local-governed by default and ignored/local until source approval, manifest approval, and commit policy change are explicit.
- Every generated or intaken artifact must have a sidecar manifest/hash before it can be considered for strict-readiness evidence.

## Shared Manifest / Hash Format

Each artifact must have a sidecar manifest stored beside the artifact or in an approved governed manifest directory. Minimum JSON fields:

```json
{
  "artifact_path": "data/processed/<artifact>",
  "artifact_sha256": "<sha256-of-artifact-bytes>",
  "artifact_bytes": 0,
  "schema_columns": [],
  "row_count": 0,
  "min_date": null,
  "max_date": null,
  "source_input_id": "<approved-source-id>",
  "source_input_hashes": [],
  "generator_id": "<approved-generator-or-external-bundle>",
  "generator_argv": [],
  "generated_or_intaken_at_utc": "<ISO-8601>",
  "approval_ids": [],
  "storage_policy": "local_governed_ignored",
  "boot_generation_allowed": false
}
```

Artifact-specific manifests may add coverage metrics, duplicate-key counts, identifier conflict counts, source vintage, method id, or replay window fields.

## Artifact Contracts In Dependency Order

### 1. Raw Prices CSV / Source -> `data/processed/prices.parquet`

| Field | Contract |
| --- | --- |
| Trusted source input needed | Approved raw CRSP-style daily prices CSV/source bundle, trusted external `prices.parquet`, or equivalent governed daily OHLC/return source with `RET`/`DLRET` or explicit total-return derivation fields. |
| Existing generator / gap status | `core/etl.py` appears to contain a legacy raw CRSP CSV -> `prices.parquet` builder using a hardcoded local CSV path. This was only statically inspected in this round and is not approved as a governed generator until source path, argv, manifest, and output validation are approved. |
| Source acquisition approval needed | Approve source owner, license/terms, source file hashes, date range, required columns, and whether the source is external bundle intake or offline regeneration input. |
| Output schema | Minimum long-form parquet columns: `date`, `permno`, `raw_close`, `adj_close`, `total_ret`, `volume`. Dates parse to daily dates; `(date, permno)` is unique; numeric required values are finite where route-required; returns stay in bounded return units, not price levels. |
| Manifest/hash format | Shared manifest plus `source_date_range`, `permno_count`, `duplicate_date_permno_count`, `ret_dlret_policy`, and `total_ret_formula`. |
| Validation command | Targeted read-only schema check after approval: `.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/prices.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'date','permno','raw_close','adj_close','total_ret','volume'} <= cols; print(pf.metadata.num_rows)"`. |
| Rollback/removal rule | If source approval, schema, hash, or freshness fails, remove `prices.parquet` and its manifest together; do not fall back to placeholders. |
| Local-governed storage policy | `data/processed/prices.parquet` stays local-governed/ignored by default; source bundle and manifest are not commit evidence unless policy changes. |
| Blocked until | Approved raw/source bundle or trusted external artifact exists, manifest/hash is accepted, generator argv is approved if regenerated, and read-only schema/freshness validation passes. |

### 2. `data/processed/prices.parquet` -> `data/processed/prices_tri.parquet`

| Field | Contract |
| --- | --- |
| Trusted source input needed | Approved `prices.parquet` from contract 1, plus any approved `yahoo_patch.parquet` or corporate-action/patch source if the TRI builder uses one. Ticker join input must be approved if ticker labels are populated. |
| Existing generator / gap status | `data/build_tri.py` exists and appears to build `prices_tri.parquet` from `prices.parquet`, optional `yahoo_patch.parquet`, and optional `tickers.parquet`. It is not approved for this round until source inputs, date window, argv, and manifest behavior are reviewed. |
| Source acquisition approval needed | Approve base price artifact, patch artifact if used, date window, base-value convention, split/dividend treatment, and whether missing ticker labels are acceptable. |
| Output schema | Minimum long-form parquet columns: `date`, `permno`, `ticker`, `tri`, `total_ret`, `legacy_adj_close`, `raw_close`, `volume`. `(date, permno)` is unique; `tri` is nonnegative and price-level-like; `total_ret` is return-like; no price/return slot swap. |
| Manifest/hash format | Shared manifest plus `base_prices_manifest_id`, `patch_manifest_id` if any, `ticker_manifest_id` if any, `base_value`, `date_window`, `tri_min`, `tri_max`, and duplicate-key count. |
| Validation command | Targeted read-only schema check after approval: `.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/prices_tri.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'date','permno','ticker','tri','total_ret','legacy_adj_close','raw_close','volume'} <= cols; print(pf.metadata.num_rows)"`. |
| Rollback/removal rule | If TRI validation fails, remove `prices_tri.parquet` and its manifest; keep `prices.parquet` blocked from strict TRI use until the cause is corrected and approved. |
| Local-governed storage policy | `prices_tri.parquet` remains local-governed/ignored by default; not committed under `data/processed` unless policy changes. |
| Blocked until | `prices.parquet` is approved, optional patch/ticker inputs are approved, generator argv is approved, and read-only schema/hash validation passes. |

### 3. Approved Ticker / Security Master Source -> `data/processed/tickers.parquet`

| Field | Contract |
| --- | --- |
| Trusted source input needed | Approved security master or ticker/permno map source with stable identifiers, ticker symbols, effective-date/vintage policy when available, and conflict handling. |
| Existing generator / gap status | No fully verified governed generator for `tickers.parquet` was confirmed in this round. `scripts/generate_instrument_mapping.py` consumes `tickers.parquet`; it is not a generator for the required security master. |
| Source acquisition approval needed | Approve security-master source, license/terms, vintage/as-of date, identifier coverage for route assets and pinned thesis universe, and conflict-resolution policy for ticker changes or duplicate mappings. |
| Output schema | Minimum parquet columns: `permno`, `ticker`. Preferred additions: `security_name`, `cusip`, `gvkey`, `start_date`, `end_date`, `source`, `as_of_date`. Required route keys are non-null; duplicate conflicting active mappings fail. |
| Manifest/hash format | Shared manifest plus `source_vintage`, `permno_count`, `ticker_count`, `duplicate_permno_count`, `duplicate_ticker_count`, `conflict_count`, and pinned/selected asset coverage summary. |
| Validation command | Targeted read-only schema check after approval: `.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/tickers.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'permno','ticker'} <= cols; print(pf.metadata.num_rows)"`. |
| Rollback/removal rule | If mapping coverage, duplicate/conflict, provenance, or hash checks fail, remove `tickers.parquet` and its manifest; strict selected-asset mapping remains blocked. |
| Local-governed storage policy | `tickers.parquet` remains local-governed/ignored by default; not committed unless policy changes. |
| Blocked until | Approved security-master source and manifest exist, route-required/pinned asset mappings are covered, and conflicts are reviewed. |

### 4. Approved WRDS / R3000 Membership Source -> `data/processed/universe_r3000_daily.parquet`

| Field | Contract |
| --- | --- |
| Trusted source input needed | Approved point-in-time WRDS/Russell 3000 membership source or trusted external governed `universe_r3000_daily.parquet` bundle. |
| Existing generator / gap status | `data/r3000_membership_loader.py` exists as a WRDS-style point-in-time membership loader and writes the daily universe output path, but it is not approved for strict readiness until the WRDS/R3000 source, provenance, input hashes, argv, manifest, and PIT validation are approved. `scripts/build_synthetic_r3000_universe.py` remains explicitly synthetic top-3000 liquidity proxy logic, not actual Russell 3000 membership, and cannot satisfy strict R3000 truth unless policy explicitly downgrades and relabels the output as synthetic. |
| Source acquisition approval needed | Approve WRDS/Russell source, license/terms, covered dates, PIT semantics, identifier alignment to `tickers.parquet`, and whether any synthetic fallback is forbidden or separately labeled. |
| Output schema | Minimum parquet columns: `date`, `permno`. Preferred additions: `ticker`, `gvkey`, `membership_flag`, `source`, `provenance`. `(date, permno)` is unique; date range covers replay windows; PIT membership does not use future membership leakage. |
| Manifest/hash format | Shared manifest plus `membership_source`, `source_vintage`, `min_date`, `max_date`, `unique_permno_count`, `duplicate_date_permno_count`, `pit_policy`, and `synthetic_proxy_allowed=false` unless explicitly approved. |
| Validation command | Targeted read-only schema check after approval: `.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/universe_r3000_daily.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'date','permno'} <= cols; print(pf.metadata.num_rows)"`. |
| Rollback/removal rule | If PIT coverage, duplicate-key checks, provenance, or approved-source proof fails, remove artifact and manifest; replay strict readiness remains blocked. |
| Local-governed storage policy | `universe_r3000_daily.parquet` and manifest remain local-governed/ignored by default; synthetic local files are not commit evidence. |
| Blocked until | Approved WRDS/R3000 source or trusted external bundle exists, PIT coverage is proven, and synthetic proxy use is either rejected or explicitly reclassified by policy. |

### 5. Approved Rule100 Replay / History Source Or Generator -> `data/processed/rule100_softmax_v1_history.csv`

| Field | Contract |
| --- | --- |
| Trusted source input needed | Approved Rule100 replay/history evidence source, approved lifecycle decision log source, or approved offline generator inputs for the softmax v1 history. |
| Existing generator / gap status | `scripts/rule100_softmax_v1_audit.py` contains `build_rule100_softmax_v1_history(...)` and `write_rule100_softmax_v1_history(...)`. Static inspection also found a dashboard helper that appears able to call the writer when history is missing. This round does not patch that code and does not approve boot/runtime generation. |
| Source acquisition approval needed | Approve source lifecycle decision log, feature source, method id, softmax config, evidence window, as-of date, generator argv, and no-boot/no-runtime-generation boundary. |
| Output schema | CSV columns must include `date`, `ticker`, `permno`, `lifecycle_action`, `buy_sell`, `event_weight`, `event_target_weight`, `softmax_v1_target_weight`, `softmax_v1_cash_residual`, `softmax_v1_gross_weight`, `sizing_eligible`, `eligibility_reason`, `factor_positive_count`, `factor_present_count`, `technical_quality`, `score`, `hold_days`, `source`. Dates parse cleanly; method/source rows are finite where required. |
| Manifest/hash format | Shared manifest plus `method_id`, `softmax_config_hash`, `decision_log_manifest_id`, `feature_source_manifest_id`, `evidence_window`, `eligible_row_count`, `cash_only_row_count`, and `generator_argv`. |
| Validation command | Targeted read-only schema check after approval: `.venv\Scripts\python -c "import pandas as pd; p='data/processed/rule100_softmax_v1_history.csv'; df=pd.read_csv(p, nrows=1000); req={'date','ticker','permno','lifecycle_action','buy_sell','event_weight','event_target_weight','softmax_v1_target_weight','softmax_v1_cash_residual','softmax_v1_gross_weight','sizing_eligible','eligibility_reason','factor_positive_count','factor_present_count','technical_quality','score','hold_days','source'}; assert req <= set(df.columns); print(len(df.columns))"`. |
| Rollback/removal rule | If schema, method provenance, source approval, hash, or freshness fails, remove CSV and manifest; do not create an empty placeholder CSV. |
| Local-governed storage policy | `rule100_softmax_v1_history.csv` remains local-governed/ignored by default and cannot be used as commit evidence unless policy changes. |
| Blocked until | Approved source/generator inputs and argv exist, method/evidence manifest is accepted, and no boot/runtime generation path is used as readiness evidence. |

## Read-Only Validation For This Docs-Only Round

This implementer round should validate only documentation tokens and Git tracking/ignore status. Do not run generation, boot preflight, or data-readiness scripts as proof for this packet.

```powershell
rg -n "ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION|SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS|StartingVerdict: BLOCK|DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS|BootReady: BLOCKED|planning/source acquisition only|not generation|no BootReady claim" docs/architecture/governed_data_source_acquisition_20260528.md docs/context/bridge_contract_current.md docs/context/impact_packet_current.md docs/context/done_checklist_current.md docs/context/planner_packet_current.md docs/context/multi_stream_contract_current.md docs/context/post_phase_alignment_current.md docs/context/observability_pack_current.md "docs/decision log.md" docs/notes.md docs/lessonss.md docs/phase_brief/phase65-brief.md
git ls-files -- data/processed/prices.parquet data/processed/prices_tri.parquet data/processed/tickers.parquet data/processed/universe_r3000_daily.parquet data/processed/rule100_softmax_v1_history.csv
git check-ignore -v data/processed/prices.parquet data/processed/prices_tri.parquet data/processed/tickers.parquet data/processed/universe_r3000_daily.parquet data/processed/rule100_softmax_v1_history.csv
```

## Acceptance Criteria

- This packet exists at `docs/architecture/governed_data_source_acquisition_20260528.md`.
- RoundID, ScopeID, StartingVerdict, current state, blocking reason, decision options, and "planning/source acquisition only, not generation" boundary are explicit.
- The five artifacts are documented in dependency order with source input, generator/gap status, acquisition approval, output schema, manifest/hash format, validation command, rollback/removal rule, local-governed storage policy, and blocked-until condition.
- Current truth surfaces and governance docs receive concise BLOCK addenda for this round.
- No code, tests, data artifacts, runtime files, boot preflight code, or `runtime/boot_status_current.json` are changed.
- Validation is limited to `rg` checks plus `git ls-files` / `git check-ignore` for the five artifacts.

## Rollback Note

Rollback is documentation-only: remove this packet and its truth-surface addenda if superseded or rejected. If a future source-acquisition or regeneration round introduces local artifacts that fail source, schema, hash, manifest, or approval checks, remove the artifact and its manifest together and keep `DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS` and `BootReady: BLOCKED`.
