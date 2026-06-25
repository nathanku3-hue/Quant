# Governed Data Source Provenance Intake - 2026-05-28

Status: source-provenance intake packet only
RoundID: ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE
ScopeID: SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION
StartingVerdict: BLOCK
Recommended path: approve source provenance first, then bounded offline regeneration in a later round

This packet records the decision boundary before any `data/processed` output can be generated or accepted. It does not close data readiness and does not authorize generation yet.

## Current State

```text
GovernanceGateV0: PASS
BootStatusPathContract: PASS
GovernedDataAuthorizationPacket: PASS
DataSourceAcquisitionPacket: PASS
DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS
SafeBoot: false
BootReady: BLOCKED
```

Required state equivalence: GovernanceGateV0 = PASS; BootStatusPathContract = PASS; GovernedDataAuthorizationPacket = PASS; DataSourceAcquisitionPacket = PASS; DataReadyStrict = BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot = false; BootReady = BLOCKED.

Runtime boot status, ignored local data, and dirty-worktree artifacts are not commit evidence and must not be used as strict data-readiness proof.

BlockingReason: strict data readiness still lacks approved source provenance, manifests, hashes, generated artifacts, and validation proof.

## Correct Next Decision

Do not regenerate yet. The next decision is source provenance intake.

Required sequence:

1. Approve source provenance.
2. Approve bounded offline regeneration outside `boot_preflight.py`.
3. Emit manifests and SHA256 hashes.
4. Run strict data-readiness validation.
5. Rerun strict `--require-github`.
6. Generate `runtime/boot_status_current.json` only after strict PASS.

If any source line cannot be approved, keep BootReady explicitly quarantined as blocked.

## Required Prohibitions

- Do not patch `boot_preflight.py`.
- Do not weaken DataReadyStrict.
- Do not generate `data/processed` artifacts from incomplete provenance.
- Do not create placeholder parquet or CSV files.
- Do not edit `runtime/boot_status_current.json`.
- Do not commit ignored/local-governed data unless policy explicitly changes.
- Do not claim BootReady.

## Source Provenance Fields Required For Every Intake Line

Each source line must be approved before any dependent output is generated or accepted:

- source location
- source owner / approval
- source date / as-of coverage
- license/access note
- expected schema
- generator command
- output path
- manifest path
- SHA256 hash policy
- validation command
- rollback/removal rule

## Intake Lines

### 1. Prices Source -> `data/processed/prices.parquet` -> `data/processed/prices_tri.parquet`

| Field | Required Provenance Before Generation |
| --- | --- |
| Source location | Approved raw prices CSV/source bundle, approved daily prices export, or trusted governed `prices.parquet` bundle. Local hardcoded source paths are not approved by themselves. |
| Source owner / approval | Named owner and approval id for source access and use in local governed regeneration. |
| Source date / as-of coverage | Covered daily date range, source vintage/as-of date, trading calendar assumptions, and route/replay window coverage. |
| License/access note | License, WRDS/vendor/account boundary, redistribution rule, and local-only storage decision. |
| Expected schema | For `prices.parquet`: `date`, `permno`, `raw_close`, `adj_close`, `total_ret`, `volume`; `(date, permno)` unique; finite route-required values. For `prices_tri.parquet`: `date`, `permno`, `ticker`, `tri`, `total_ret`, `legacy_adj_close`, `raw_close`, `volume`. |
| Generator command | `prices.parquet`: command must be approved separately because `core/etl.py` is legacy/local-bound. `prices_tri.parquet`: approved `data/build_tri.py` argv after `prices.parquet` provenance passes. |
| Output path | `data/processed/prices.parquet`; then `data/processed/prices_tri.parquet`. |
| Manifest path | Required approved sidecar or governed manifest path for each output before strict-readiness use. |
| SHA256 hash policy | Hash source files and generated artifacts by bytes; include source hashes, artifact hash, generator argv, row count, date range, and schema columns. |
| Validation command | Read-only schema/hash/date-window validation after generation approval, not during boot and not as this packet's proof. |
| Rollback/removal rule | If source, schema, hash, freshness, or validation fails, remove the output and manifest together; do not leave placeholders. |

Known static generator state:

- `core/etl.py` is a legacy/local-bound raw CSV builder for `prices.parquet` and appears tied to a hardcoded local CSV path. It is not approved until the raw source, argv, schema, manifest, and validation are approved.
- `data/build_tri.py` exists and depends on `prices.parquet`; optional patch/ticker inputs also need approval if used.

### 2. Ticker / Security Master Source -> `data/processed/tickers.parquet`

| Field | Required Provenance Before Generation |
| --- | --- |
| Source location | Approved security-master source or trusted governed `tickers.parquet` bundle. |
| Source owner / approval | Named owner and approval id for identifier source use. |
| Source date / as-of coverage | Source vintage/as-of date, identifier validity window, and coverage for route assets, selected assets, and pinned thesis universe. |
| License/access note | License/account boundary and whether the security master can be stored as local-governed data only. |
| Expected schema | Minimum `permno`, `ticker`; preferred `security_name`, `cusip`, `gvkey`, `start_date`, `end_date`, `source`, `as_of_date`; duplicate/conflicting active mappings fail. |
| Generator command | No complete governed standalone generator is confirmed; command or external bundle intake must be approved before write. |
| Output path | `data/processed/tickers.parquet`. |
| Manifest path | Required approved sidecar or governed manifest path before strict-readiness use. |
| SHA256 hash policy | Hash source files and output; manifest must record source vintage, coverage, duplicate/conflict counts, and approved conflict policy. |
| Validation command | Read-only schema, duplicate/conflict, and selected-asset coverage validation after generation or intake approval. |
| Rollback/removal rule | If provenance, coverage, duplicate/conflict, schema, or hash checks fail, remove output and manifest together. |

Known static generator state:

- No complete governed security-master generator was confirmed.
- Existing map update paths can mutate/extend an existing map opportunistically and are not a substitute for an authoritative source approval.

### 3. WRDS / R3000 Membership Source -> `data/processed/universe_r3000_daily.parquet`

| Field | Required Provenance Before Generation |
| --- | --- |
| Source location | Approved WRDS/Russell 3000 membership source or trusted governed `universe_r3000_daily.parquet` bundle. |
| Source owner / approval | Named owner and approval id for membership-source access and use. |
| Source date / as-of coverage | Membership source vintage, PIT coverage start/end, replay-window coverage, and effective-date semantics. |
| License/access note | WRDS/Russell/vendor access boundary, redistribution rule, and local-governed storage policy. |
| Expected schema | Minimum `date`, `permno`; preferred `ticker`, `gvkey`, `membership_flag`, `source`, `provenance`; `(date, permno)` unique; no future-membership leakage. |
| Generator command | Approved `data/r3000_membership_loader.py` argv or trusted bundle intake command after source provenance passes. |
| Output path | `data/processed/universe_r3000_daily.parquet`. |
| Manifest path | Required approved sidecar or governed manifest path before strict-readiness use. |
| SHA256 hash policy | Hash source files and output; manifest must record PIT policy, date range, unique permnos, duplicate keys, source vintage, and synthetic proxy flag. |
| Validation command | Read-only schema, PIT date coverage, duplicate-key, and source-vintage validation after generation approval. |
| Rollback/removal rule | If source proof, PIT coverage, schema, duplicate-key, hash, or validation fails, remove output and manifest together. |

Known static generator state:

- `data/r3000_membership_loader.py` exists as a WRDS-style PIT membership loader and writes the daily universe output path.
- Approved WRDS/R3000 source provenance, input hashes, argv, manifest, and PIT validation are still missing.
- `scripts/build_synthetic_r3000_universe.py` is a synthetic liquidity proxy and is not strict R3000 truth unless policy explicitly downgrades and relabels it.

### 4. Rule100 History Source / Generator -> `data/processed/rule100_softmax_v1_history.csv`

| Field | Required Provenance Before Generation |
| --- | --- |
| Source location | Approved Rule100 replay/history source, approved lifecycle decision log source, approved feature source, or trusted governed CSV bundle. |
| Source owner / approval | Named owner and approval id for the source and generator design. |
| Source date / as-of coverage | Evidence window, method id, source as-of date, replay window, and lifecycle-decision coverage. |
| License/access note | Local artifact governance and any source redistribution/access constraints. |
| Expected schema | `date`, `ticker`, `permno`, `lifecycle_action`, `buy_sell`, `event_weight`, `event_target_weight`, `softmax_v1_target_weight`, `softmax_v1_cash_residual`, `softmax_v1_gross_weight`, `sizing_eligible`, `eligibility_reason`, `factor_positive_count`, `factor_present_count`, `technical_quality`, `score`, `hold_days`, `source`. |
| Generator command | Approved offline `scripts/rule100_softmax_v1_audit.py` argv or trusted bundle intake command; runtime/dashboard auto-build paths are not readiness evidence. |
| Output path | `data/processed/rule100_softmax_v1_history.csv`. |
| Manifest path | Required approved sidecar or governed manifest path before strict-readiness use. |
| SHA256 hash policy | Hash source logs/features/config and output CSV; manifest must record method id, generator argv, source manifests, evidence window, and row counts. |
| Validation command | Read-only CSV schema, method/source, finite-field, evidence-window, and hash validation after generation approval. |
| Rollback/removal rule | If schema, method provenance, source approval, hash, freshness, or validation fails, remove CSV and manifest together; do not create an empty placeholder. |

Known static generator state:

- `scripts/rule100_softmax_v1_audit.py` has a partial history writer.
- Governed source/generator approval and manifest/hash policy are still missing.
- Runtime or dashboard-triggered history creation must not count as strict readiness evidence.

## Validation Commands For A Later Approved Generation Round

These commands are examples of post-approval read-only validation. They are not authorization to generate or run boot preflight in this round.

```powershell
.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/prices.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'date','permno','raw_close','adj_close','total_ret','volume'} <= cols; print(pf.metadata.num_rows)"
.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/prices_tri.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'date','permno','ticker','tri','total_ret','legacy_adj_close','raw_close','volume'} <= cols; print(pf.metadata.num_rows)"
.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/tickers.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'permno','ticker'} <= cols; print(pf.metadata.num_rows)"
.venv\Scripts\python -c "import pyarrow.parquet as pq; p='data/processed/universe_r3000_daily.parquet'; pf=pq.ParquetFile(p); cols=set(pf.schema.names); assert {'date','permno'} <= cols; print(pf.metadata.num_rows)"
.venv\Scripts\python -c "import pandas as pd; p='data/processed/rule100_softmax_v1_history.csv'; df=pd.read_csv(p, nrows=1000); req={'date','ticker','permno','lifecycle_action','buy_sell','event_weight','event_target_weight','softmax_v1_target_weight','softmax_v1_cash_residual','softmax_v1_gross_weight','sizing_eligible','eligibility_reason','factor_positive_count','factor_present_count','technical_quality','score','hold_days','source'}; assert req <= set(df.columns); print(len(df.columns))"
```

## Read-Only Validation For This Docs-Only Round

This implementer pass validates only documentation tokens and Git tracking/ignore state. Do not run generation, boot preflight, or data-readiness scripts as proof for this packet.

```powershell
rg -n "ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE|SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION|StartingVerdict: BLOCK|DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS|BootReady: BLOCKED|does not authorize generation yet|Approve source provenance first" docs/architecture/governed_data_source_provenance_intake_20260528.md docs/context/bridge_contract_current.md docs/context/impact_packet_current.md docs/context/done_checklist_current.md docs/context/planner_packet_current.md docs/context/multi_stream_contract_current.md docs/context/post_phase_alignment_current.md docs/context/observability_pack_current.md "docs/decision log.md" docs/notes.md docs/lessonss.md docs/phase_brief/phase65-brief.md
git ls-files -- data/processed/prices.parquet data/processed/prices_tri.parquet data/processed/tickers.parquet data/processed/universe_r3000_daily.parquet data/processed/rule100_softmax_v1_history.csv
git check-ignore -v data/processed/prices.parquet data/processed/prices_tri.parquet data/processed/tickers.parquet data/processed/universe_r3000_daily.parquet data/processed/rule100_softmax_v1_history.csv
```

## Correct SAW Wording To Carry Forward

```text
SAW Verdict: BLOCK

GovernanceGateV0: PASS
BootStatusPathContract: PASS
GovernedDataAuthorizationPacket: PASS
DataSourceAcquisitionPacket: PASS
DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS
SafeBoot: false
BootReady: BLOCKED

BlockingReason:
- Strict data readiness still lacks approved source provenance, manifests, hashes, generated artifacts, and validation proof.

NextAction:
- Approve source provenance first.
- Then approve bounded offline regeneration.
- Then rerun strict data readiness and strict GitHub-aligned boot proof.
```

## Acceptance Criteria

- This packet exists at `docs/architecture/governed_data_source_provenance_intake_20260528.md`.
- RoundID, ScopeID, StartingVerdict, current blocked state, blocking reason, and "does not authorize generation yet" boundary are explicit.
- The four source intake lines cover all five required strict data artifacts.
- Each line requires source location, source owner/approval, source date/as-of coverage, license/access note, expected schema, generator command, output path, manifest path, SHA256 hash policy, validation command, and rollback/removal rule.
- Known static generator state is recorded without approving or running generators.
- Current truth surfaces and governance docs receive concise BLOCK addenda for this round.
- No code, tests, data artifacts, runtime files, boot preflight code, or `runtime/boot_status_current.json` are changed.
- Validation is limited to `rg` checks plus `git ls-files` and `git check-ignore` for the five artifacts.

## Rollback Note

Rollback is documentation-only: remove this packet and its truth-surface addenda if superseded or rejected. If a future source-provenance or regeneration round introduces local artifacts that fail source, schema, hash, manifest, or approval checks, remove the artifact and its manifest together and keep `DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS`, `SafeBoot: false`, and `BootReady: BLOCKED`.
