# CIQ Market Custody Handover — 2026-08-08

Status: `COMPLETED / SUPERSEDED_BY_CLOCK_1_AUTHORITY`
Active state: `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`
Target date: `2026-08-07`
Claim boundary: `prospective_clock_started=true`; `evaluation_started=false`; `financial_alpha_evidence=0`; Parent/Child remain frozen

## Completion receipt — 2026-08-08

This handover mission is complete. The master hash reverified exactly at `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`. Exact-primary-SPT parts `004..033` were sufficient; the final raw market object is `data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv`, 21,345 rows, zero duplicate-key conflicts, SHA-256 `897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48`. Per-security counts are recorded in `data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.counts.csv` (SHA-256 `deffc13cf7364d628e1ecd879d8280c75d490cde4098327d0de0da49c074c9fe`).

CIQ admission produced 99 canonical securities and 10 mechanical exclusions; five genuine short histories were never backfilled. `decision_cut_v3`=`AOV0_CIQ_20260807_ad2faf0533cec19c`; real Seal Candidate=`c78088ace7819170cd0064154fba138da4b4f8183dbd4ec48c347a942985ba88`; fresh-process verification=`55ba4e2f3670d4fc01839bd22bb164cfd0755efb1ce47f3641b9ca88d61c344c`; immutable Clock-Start Receipt=`eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78`. Clock #1 started `2026-08-08T19:48:52.440503Z`; evaluation begins `2026-08-10T20:00:00Z`; outcomes remain sealed until `2026-09-09T20:00:00Z`.

The `.venv` was restored with Python 3.12; `pip check` and AOV `75/75` pass. Repository-wide pytest has nine unrelated/inherited collection errors and is not claimed green. No commit or push was performed. The remaining sections are preserved as the acquisition-time contract/lessons and are historical where they describe work as still open.

## Mission — historical

Complete the remaining exact-primary-SPT historical market chunks until every name that survives the existing factor-coverage gate has at least 200 completed close observations through `2026-08-07`; combine and hash the real raw market object; then run the existing fail-closed CIQ admission builder → `decision_cut_v3` → real Seal Candidate → fresh-process verification → immutable Clock-Start Receipt.

Do not spend another round on provider capability, Security-vs-Trading-Item semantics, historical PIT formula discovery, or Parent/Child tuning. Those are not the current bottleneck.

## Frozen contract

- Frozen company universe/fundamentals: `run_4.xlsx`, 109 entities.
- Canonical risky-asset identity: `CIQSEC:<Capital IQ Security ID>`.
- Provider security-level field: `SP_CIQ_ID`.
- Provider listing/trading-item field: `SP_TRADING_ITEM_ID`.
- Market query key for this completion round: exact primary `SPT_INSTRUMENT_ITEM_ID` / `SPT...` value from the captured master.
- Required daily market fields, unchanged:
  - `SP_TOTAL_RETURN`
  - `SP_PRICE_CLOSE`
  - `SP_VOLUME`
- Historical market rows are warmup only. Current-cut factor authority exists only on the target date.
- Admission remains fail closed: factor coverage below the existing threshold, insufficient market history, identity ambiguity/collision, missing target state, or invalid target state excludes/blocks; no compatibility path opens.
- No ticker, company `SP_ENTITY_ID`, PERMNO, alternate listing, yfinance, SNLPrice, or other fallback may become canonical authority.

## What is already solved

### 1. Security vs Trading Item identity

Cross-listing proof on frozen entity `COE` / `SP_ENTITY_ID=4913905` established the provider layers:

- primary listing: `SPT344984472`, ticker `COE`, exchange `NYSEAM`;
- alternate listing: `SPT364472819`, ticker `C4G0`, exchange `DB`;
- both return `SP_CIQ_ID=IQ337968870`;
- primary `SP_TRADING_ITEM_ID=344984472`;
- alternate `SP_TRADING_ITEM_ID=364472819`;
- both share CUSIP `16954L204`, ISIN `US16954L2043`, SEDOL `BNQN627`, and the same security description.

Therefore `SP_CIQ_ID` is security-level and `SP_TRADING_ITEM_ID` is listing/trading-item-level. Identifier Lookup output type `MI ID` writes the `SPT...` trading-item identifier, not the security-level identifier.

Direct company-key `SPGTable` also returns the same primary Security + Trading Item pair, so 109 UI traversals are unnecessary.

### 2. 109-name primary master is already raw custody

Use this object; do not recapture it unless an integrity check fails:

- path: `data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv`
- retrieval: `2026-08-08T16:23:22.0736860Z`
- rows: `109`
- bytes: `27861`
- SHA-256: `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`
- all 109 frozen entities have required identity values;
- provider `SP_CIQ_ID` values are unique across entities;
- primary `SP_TRADING_ITEM_ID` values are unique across entities;
- provider ticker/exchange match the frozen `run_4` universe.

Important schema note: the raw master also carries an internal `SP_SECURITY_ID` input column to satisfy the existing generic parser. Its values come from provider `SP_CIQ_ID`, and rows explicitly record `SECURITY_ID_SOURCE_METRIC=SP_CIQ_ID`. Do not claim that Capital IQ exposes a generic `SP_SECURITY_ID` metric.

## Market acquisition lessons already banked

The stable production pattern is one bounded Office query per atomic part with atomic temp-file → final-file landing. The current script is:

`tmp/ciq_capture_market_chunk.ps1`

For the full 109-name universe and three exact daily fields:

- 5 weekdays: stable;
- 6 weekdays: stable;
- 7 weekdays: stable;
- 8 weekdays: failed at the bounded execution window;
- 10 weekdays: failed at the bounded execution window.

**Frozen incumbent: 7 weekdays × 109 exact primary SPTs × 3 fields.** Do not keep tuning query width while this works.

A 6-day company-key output and a 6-day exact-SPT-key output were compared after excluding `chunk_retrieved_at_utc`; data values were identical. Use exact primary SPT keys for the remaining history.

The chunk script:

- requires exactly 109 master rows;
- uses `SPT_INSTRUMENT_ITEM_ID` when `-UseTradingItemKey` is supplied;
- queries exactly `SP_TOTAL_RETURN`, `SP_PRICE_CLOSE`, `SP_VOLUME` for each requested date;
- skips missing/error/non-numeric row-days rather than fabricating values;
- writes provider metric aliases plus exact provider metric/source columns;
- records `chunk_retrieved_at_utc`;
- writes through a unique temp file and atomically moves it to the final part path;
- clears the `SPGTable` formula before workbook close.

The script calls `GetActiveObject('Excel.Application')`; it does **not** launch/authenticate Excel itself. A usable authenticated Capital IQ Office Excel process must exist when the chunk runs.

## Existing market raw custody

### Earlier 5-day parts

Nine real provider parts already exist under:

`data/aov0/raw/ciq_market_parts_v3_20260808/`

Known files:

- `part_000_20250519_20250523.csv`
- `part_001_20250526_20250530.csv`
- `part_002_20250602_20250606.csv`
- `part_003_20250609_20250613.csv`
- `part_004_20250616_20250620.csv`
- `part_018_20250922_20250926.csv`
- `part_019_20250929_20251003.csv`
- `part_020_20251006_20251010.csv`
- `part_063_20260803_20260807.csv`

These are legitimate raw custody/evidence. Preserve them. The preferred completion path, however, is one consistent exact-primary-SPT 7-day series so the final raw object has a simple acquisition contract.

There is also an earlier standalone 5-day target-week object:

- path: `data/aov0/raw/ciq_primary_security_market_history_20260808T163540Z.csv`
- rows: `545`
- names: `109`
- dates: `2026-08-03` through `2026-08-07`
- retrieval: `2026-08-08T16:35:40.2352282Z`
- SHA-256: `4674c8f81d3d3ac3be3e44491a92b0abba48e9bcb296ae5cb6f85951870e45ed`

### Validated 7-day exact-SPT target part

Already captured and validated:

- path: `data/aov0/raw/ciq_market_parts_spt_7d_test_20260808/part_033_20260730_20260807.csv`
- SHA-256: `81779d8ed04b80a5b79298821f9ff5d89c96abf025e8bb06d9a67f864cd744aa`
- size: `163617` bytes

The directory name contains `test`, but this file contains real provider output. Do not rename/delete it merely for naming aesthetics. It may be reused as the target chunk for the consistent 7-day series.

## Exact resume plan

### A. Complete the consistent 7-day SPT series

The validated target part is index `33` under a `Weekdays=238`, `ChunkDays=7` layout, which implies 34 total chunks (`0..33`). Unless a filesystem/hash audit proves otherwise, capture the remaining indices `0..32` and reuse part `33`.

Invocation pattern from the worktree:

```powershell
C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe `
  -NoProfile -ExecutionPolicy Bypass `
  -File tmp\ciq_capture_market_chunk.ps1 `
  -ChunkIndex <0..32> `
  -PartsDir E:\code\quant\.worktrees\devspace-053ca7a4f582fb3e\data\aov0\raw\ciq_market_parts_spt_7d_test_20260808 `
  -TargetDate 2026-08-07 `
  -Weekdays 238 `
  -ChunkDays 7 `
  -UseTradingItemKey
```

Before each bounded unit, ensure the Excel process the script will attach to is authenticated and usable by the Capital IQ Office add-in. Verify the resulting final CSV exists and is non-empty before moving to the next unit. A running PowerShell/Excel PID is not progress authority.

Do not intentionally leave an unattended supervisor/worker running across handover. Process-isolated chunks are useful, but completion authority is the landed part file plus its contents/hash.

### B. Do not use the current supervisor script as-is

`tmp/ciq_fill_market_parts.ps1` is stale for this exact completion contract. Its current child invocation passes only `-ChunkIndex`; it does **not** pass:

- `-Weekdays 238`
- `-ChunkDays 7`
- `-UseTradingItemKey`
- the 7-day SPT parts directory

Therefore do not treat it as the production supervisor without first changing it to the frozen 7-day SPT contract or invoking the chunk script directly with all parameters.

### C. Final raw market materialization

After the required parts are present:

1. Read only real landed provider CSV part files.
2. Preserve:
   - `SPT_DATE`
   - `SP_ENTITY_ID` as join/audit metadata only
   - `SP_CIQ_ID`
   - `SPT_INSTRUMENT_ITEM_ID`
   - `SP_TRADING_ITEM_ID`
   - exact market values/aliases
   - `chunk_retrieved_at_utc`
   - `RETURN_SOURCE_METRIC`
   - `CLOSE_SOURCE_METRIC`
   - `VOLUME_SOURCE_METRIC`
3. Dedupe on exactly:
   - (`SPT_DATE`, `SP_CIQ_ID`, `SP_TRADING_ITEM_ID`)
4. Fail if duplicate keys disagree on market values or provider identity.
5. Sort deterministically before writing the final raw object.
6. Compute SHA-256 of the exact final raw bytes.
7. Count actual completed observations per `SP_CIQ_ID`/primary `SP_TRADING_ITEM_ID` through `2026-08-07`.

A 238-weekday request is only a holiday/listing-history cushion. The gate is **actual completed observations**, not requested weekdays.

Names with genuinely shorter listing histories may remain below 200. The existing builder is designed to exclude them. Do not splice history from alternate trading items, predecessor identities, or ticker aliases to force them through the gate.

## Admission and first-seal sequence

After final raw custody is complete:

1. Verify the primary-master raw SHA-256.
2. Verify the final market raw SHA-256 and per-security completed-row counts.
3. Restore the repository-approved `.venv` interpreter before running Python. At this handover, the `.venv` directory exists but `.venv/Scripts/python.exe` is absent. **Do not silently use system Python.**
4. Run the existing fail-closed CIQ market admission entrypoint (`scripts/aov0_build_ciq_market.py`) with the captured master and final raw market object.
5. Confirm admitted current outputs are produced only from provider bytes and that mechanical exclusions are recorded rather than backfilled.
6. Build `decision_cut_v3` using the existing decision-cut builder and already admitted official SOFR.
7. Run the real first-seal path. Seal construction must remain clock-false.
8. Run the required fresh-process full-chain verification.
9. Only after successful verification, issue the separate immutable Clock-Start Receipt.

The prospective clock starts from the Clock-Start Receipt, not from raw data completion, the builder, `decision_cut_v3`, or a Seal Candidate.

## Do not retry / do not change

- Do not restart embedded SNLQuery/persisted-query extraction.
- Do not retry `SNLPrice` or SPGRANGE-family history as incumbent paths.
- Do not spend time reconstructing raw Genix `SPGTable` metric normalization while the supported Office path works.
- Do not widen Office chunks beyond the proven 7-day unit as the next move.
- Do not redo 109-name Identifier Lookup traversal; identity is solved and the master is captured.
- Do not use ticker, company entity, PERMNO, or alternate listings as canonical fallback.
- Do not infer that provider metric `SP_SECURITY_ID` exists because the internal parser has an input column with that name.
- Do not backfill short histories from an alternate SPT.
- Do not tune Parent/Child from historical PIT probes or these acquisition results.
- Do not execute v2/open authority.
- Do not delete the orphan temp file in the 6-day SPT test directory without explicit owner approval.
- Do not commit/push unless separately authorized.

## Known orphan / hygiene item

A prior 6-day SPT test left an orphan temp file:

`data/aov0/raw/ciq_market_parts_spt_6d_test_20260808/part_038_20260731_20260807.csv.35ebee9c51504997bee5c8f838b49265.tmp`

It is not authority. Leave it in place unless the owner explicitly authorizes destructive cleanup.

## Handover environment note

The repo requires `.venv` for Python commands. The `.venv` directory exists in the current worktree, but the required `.venv/Scripts/python.exe` interpreter is absent. Raw Office/PowerShell custody can continue without pretending Python admission has run. Before the builder/cut/seal stage, restore the approved repo virtual-environment interpreter under repository policy.

The generated context artifacts were manually synchronized for this handover because the Python context-packet builder could not be run under the required `.venv`. Do not claim `scripts/build_context_packet.py --validate` has passed for this handover until `.venv` is restored and that command is actually run.

## Exit criteria for the next worker

The handover task is complete only when all of the following are true:

- the 109-name primary master hash matches `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`;
- the required real 7-day SPT history parts are present and verified;
- one deterministic combined raw market object exists with an exact SHA-256 receipt;
- duplicate-key conflicts are zero;
- completed-observation counts are explicitly reported for every security;
- every admitted name satisfies the existing `>=200` completed-close rule through `2026-08-07`;
- short-history/non-admissible names are mechanically excluded rather than backfilled;
- the CIQ builder produces the current Rule100 targets, vertical primitives, and total returns from the captured provider bytes;
- `decision_cut_v3` is built successfully;
- the real Seal Candidate is written clock-false;
- fresh-process full-chain verification succeeds;
- the separate immutable Clock-Start Receipt is written before any prospective-clock claim.

Until the final receipt exists: `prospective_clock_started=false`, `financial_alpha_evidence=0`, Limited Live remains closed.
