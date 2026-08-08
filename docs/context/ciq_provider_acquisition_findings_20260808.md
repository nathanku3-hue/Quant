# CIQ Provider Acquisition Findings — 2026-08-08

Status: `PROVIDER_CAPABILITY_PROVEN / PRIMARY_IDENTITY_RAW_CUSTODY_CAPTURED / MARKET_CUSTODY_INCOMPLETE`
Active gate: `PRE_SEAL_REAL_CIQ_ADMISSION`
Scope: S&P Capital IQ Pro Office acquisition only
Claim boundary: `prospective_clock_started=false`; `financial_alpha_evidence=0`; Parent/Child parameters remain frozen

## Executive result

The Capital IQ provider path is no longer an unknown-capability or identity-semantics problem. The installed S&P Capital IQ Pro Office client is present, authenticated, and capable of returning the current-cut market fields required by `research/aov0/ciq_market.py`. The provider identity layers are now resolved as well: `SP_CIQ_ID` is the security-level identifier and `SP_TRADING_ITEM_ID` is the listing/trading-item identifier; the exact primary pair can be returned directly from the frozen company key through supported `SPGTable` behavior.

A real 109-row primary Security/Trading Item master is now in raw custody at `data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv`, retrieved `2026-08-08T16:23:22.0736860Z`, SHA-256 `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`. It has 109 unique provider `SP_CIQ_ID` values and 109 unique primary `SP_TRADING_ITEM_ID` values, with provider ticker/exchange matching the frozen `run_4` universe. This raw object has **not** yet been admitted through the fail-closed builder.

The remaining pre-clock blocker is bulk market custody only: complete a primary-SPT-keyed historical series with at least 200 completed observations for each name that survives the existing factor-coverage and market-history gates, combine/hash the raw market object, then run the already-built admission → `decision_cut_v3` → Seal Candidate verification path. No Rule100 target, primitive, admitted total-return Parquet, real decision cut, real Seal Candidate, verification proof, or Clock-Start Receipt was produced from these provider bytes. Historical PIT capability remains post-Clock research capability only and must not be used to tune Parent/Child from biased historical results.

## 1. Run-health and process-custody findings

- The prior pasted acquisition status was stale. A later `ciq_snlquery_range_payload_probe.ps1` had run after the visible status text.
- The previous unmanaged PowerShell/cmd runner had exited while an Excel automation server remained. CPU/handle/memory samples showed the remaining Excel instance was idle, not progressing.
- Repeatedly killing only Excel was insufficient because an unmanaged PowerShell runner could respawn its COM child. The correct cleanup boundary was the owning PowerShell/cmd process tree plus its automation Excel child.
- DevSpace-managed restarts correctly exposed a reproducible hang at the embedded-query execution boundary. A process reporting `RUNNING` was not treated as healthy when Excel CPU flattened and the probe exceeded its own bounded polling path.
- The embedded-query/SNLQuery line was explicitly terminated rather than repeatedly restarted.

Disposition: do not use process existence as progress authority. Managed task state + bounded output/CPU movement is required.

## 2. Provider / Office environment

- S&P Capital IQ Pro Office is installed and registered in Excel.
- The S&P Office add-ins load in Excel and the main add-in object is available through `SNL.Clients.Office.Excel.ExcelAddIn`.
- Installed assemblies expose the Office bootstrap/container, `SecurityProvider`, ProductQuery service factory, FunctionModel, Genix request manager, formula descriptors, and the Identifier Lookup host.
- The current Office logs identify the modern Genix ProductQuery endpoint as:
  - `https://www.capitaliq.spglobal.com/apisv3/ht/office-micro-data-service/v1/ProductQuery`
- The older WCF ProductQuery endpoint is also present:
  - `https://www.capitaliq.spglobal.com/snl.services.data.service/v2/productQuery.svc/$net`
  but this legacy path did not become the preferred extraction route.

## 3. Authentication findings

- Standalone `ExcelBootstrapper.Run()` successfully composes the real S&P Unity container and resolves the Office service objects without relying on worksheet formulas.
- The installed security layer uses a shared-memory session clipboard. Static analysis of `SecurityProvider.Initialize` identified the shared session channel as:
  - `{14719706-D523-4BFC-9890-0669D589EF37}`
- A correctly composed standalone `SecurityProvider` successfully imported the live Office session from that channel: authenticated state and access-token presence both became true. Token contents were not printed or persisted.
- S&P Office logs independently show successful desktop sessions acquiring CIQ access/refresh tokens and calling `UpdateClipboard`.
- An automation Excel process does not reliably publish the authenticated session by itself; the normal Office security initialization transition is required.

Disposition: authentication is solved. Do not reverse-engineer or print bearer/refresh tokens. Reuse the Office session/bootstrap path only as needed.

## 4. Direct ProductQuery / Genix transport findings

- `OfficeGenixRequestManager.ExecuteFunctionsAsync` sends `Authorization: Bearer <SecurityProvider.AccessToken>` and posts a serialized `FunctionsRequest`.
- A valid Genix envelope requires, among other fields:
  - `ConversionInformation.DataSource = ""`
  - `ConversionInformation.HeaderCurrency = model.Currency` (`USD` in the probe)
- After those fields were supplied, Genix returned HTTP 200.
- Provider function dispatch IDs recovered from the installed descriptors include:
  - `SPG = 12`
  - `SPGTable = 14`
  - `SPGLabel = 15`
- A direct authenticated Genix `SPGLabel(266637,267969,...)` request returned `Entity Name`, proving end-to-end auth, serialization, endpoint, and response handling.
- Current Office feature flags/logs show Genix delegation for `spgtable|spg|spglabel`; legacy `SNLData` is not a Genix-delegated function in this client.
- Raw direct `SPGTable` requests require the same metric/key normalization performed by the Office function engine. Reconstructing that private transformation is unnecessary for the current gate because the worksheet SPG/SPGTable path already works.

Disposition: direct Genix is a proven fallback/service surface, but the first-Clock acquisition path should prefer the supported Office SPG/Identifier Lookup behavior rather than reimplementing its metric normalization.

## 5. Historical PIT fundamentals capability — proved but NOT first-Clock authority

The fourth argument of `SPG` is a genuine historical as-of date for company fundamentals.

Probe entity `4094286` demonstrated:

| Formula concept | As-of 2024-04-30 | As-of 2024-06-30 |
|---|---:|---:|
| `IQ_PERIOD_END`, `FQ0` | 2024-01-28 | 2024-04-28 |
| `IQ_TOTAL_REV`, `FQ0` | 22,103,000 | 26,044,000 |
| `IQ_TOTAL_REV`, `FQ12025` | `NA` | 26,044,000 |

`FilingVer=Original` is also callable; in the sampled observation it matched Current/Restated.

This proves that the licensed Office client can perform historical PIT-style as-of fundamentals retrieval. It does **not** upgrade the hash-bound `run_4.xlsx` current-cut artifact into historical PIT authority, and it does not authorize a historical Rule100 replay before Clock #1.

Disposition: bank as post-Clock research capability. Do not tune Parent/Child from these historical results.

## 6. `run_4.xlsx` formula / input findings

The retained hash-bound workbook contains the working formula pattern:

`SPGTable($B$8:$B$116,$C$5:$GE$5,$C$6:$GE$6,"Options:Curr=USD,Mag=Thousands,ConvMethod=R,FilingVer=Current/Restated")`

and many `SPGLabel(...)` formulas.

Examples from its cached input cells:

- `B8 = 4913905`
- `A8 = 51Talk Online Education Group (NYSEAM:COE)`
- field keys include `SP_COMPANY_TYPE`, `SP_COMPANY_STATUS`, `MI_PRIMARY_INDUSTRY`, `SP_TOTAL_REV`, `IQ_TOTAL_REV`, `SP_EXCHANGE`
- `K8 = NYSEAM`

The workbook does **not** contain the required primary Capital IQ Security ID / Trading Item ID master. Header inspection found exchange but no retained security/trading identifier columns.

Disposition: continue treating `run_4.xlsx` as frozen company universe + current-cut fundamentals only.

## 7. Current market authority — required fields are proved

The modern `SPGTable` path returns the current admission builder's required market primitives by exact historical date.

For probe entity `4094286` / date `2024-06-28`:

- `SP_TOTAL_RETURN` → `-0.362932` (provider percent total return; UI text `-0.36`)
- `SP_VOLUME` → `315,516,740`
- `SP_PRICE_CLOSE` → `123.54`

Additional observations:

- `SP_VOLUME` also returns a current/no-secondary value.
- `SP_TOTAL_RETURN` is a recognized provider metric; attempts to force it through scalar `SPG` produced parameter/magnitude errors, while `SPGTable` is the working surface.
- `IQ_CLOSEPRICE`, `IQ_CLOSEPRICE_ADJ`, and `IQ_VOLUME` were not the correct `SPGTable` field keys in this context.
- `SP_PRICE_CLOSE` is the correct close field found by bounded field search.

These values line up with `research/aov0/ciq_market.py`, which accepts total-return percent (divides by 100), close, volume, exact Trading Item ID, and optionally Capital IQ Security ID.

Disposition: market *capability* is solved. Remaining work is bulk materialization/custody for the frozen universe with >=200 completed daily observations and an explicit post-close retrieval timestamp.

## 8. Legacy market path — reject

- `SNLPrice` is a legacy indirect/vector compatibility function.
- A bounded `SNLPrice` smoke generated multiple Excel automation processes and failed to produce bounded terminal output within the expected window.
- The managed task was cancelled and the automation children were cleaned.
- `SPGRANGEV` retained probes returned `#ERROR`/invalid-ticker states for the attempted market/history use.

Disposition: do not resume `SNLPrice`, `CIQTRADINGRANGE*`, embedded SNLQuery, or SPGRANGEV as the first-Clock market path while the proven `SPGTable` route exists.

## 9. Primary Security / Trading Item identity — solved and raw master captured

The provider identity semantics are now mechanically resolved.

Identifier Lookup proof on frozen company `COE` / `SP_ENTITY_ID=4913905`:

- exact company-row selection succeeded in the supported Identifier Lookup WebView;
- `SHOW SECURITIES` exposed the primary NYSEAM row `SPT344984472`, ticker `COE`, CUSIP `16954L204`, security description `American Depositary Receipts Class A Ordinary Shares`;
- it also exposed the alternate DB listing `SPT364472819`, ticker `C4G0`, with the same underlying security descriptors;
- selecting the primary row and using Identifier Lookup output type `MI ID` wrote exactly `SPT344984472` into Excel. Therefore Identifier Lookup `MI ID` is the Trading/Instrument Item layer, not the security-level identifier.

Formula Builder / SPG catalog proof:

- `SP_TRADING_ITEM_ID` is a valid Market Data → Identifier Information field;
- `SP_CIQ_ID` is a valid provider field;
- `SP_CUSIP`, `SP_ISIN`, `SP_SEDOL`, `SP_SECURITY_DESCRIPTION`, and `SP_SECURITY_STATUS` are valid supporting identity fields;
- a literal generic `SP_SECURITY_ID` provider metric was **not** found and must not be claimed as a provider field.

Scalar identity validation:

- primary `SPT344984472` returns `SP_CIQ_ID=IQ337968870` and `SP_TRADING_ITEM_ID=344984472`;
- alternate listing `SPT364472819` returns the same `SP_CIQ_ID=IQ337968870` but `SP_TRADING_ITEM_ID=364472819`;
- both rows share CUSIP `16954L204`, ISIN `US16954L2043`, SEDOL `BNQN627`, and the same security description, while exchange differs (`NYSEAM` vs `DB`).

This proves `SP_CIQ_ID` is security-level and `SP_TRADING_ITEM_ID` is listing/trading-item-level.

A further direct company-key `SPGTable` probe on `4913905` returned the same **primary** pair (`SP_CIQ_ID=IQ337968870`, `SP_TRADING_ITEM_ID=344984472`, ticker `COE`, exchange `NYSEAM`). This eliminates the need for 109 UI traversals: the frozen company IDs can directly materialize the current primary Security + Trading Item mapping.

The 109-row raw master was then captured in one provider query using company IDs and fields `SP_CIQ_ID`, `SP_TRADING_ITEM_ID`, `SP_TICKER`, `SP_EXCHANGE`, `SP_CUSIP`, `SP_ISIN`, `SP_SEDOL`, `SP_SECURITY_DESCRIPTION`, and `SP_SECURITY_STATUS`:

- path: `data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv`;
- retrieval: `2026-08-08T16:23:22.0736860Z`;
- rows: `109`;
- SHA-256: `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`;
- all 109 frozen entities have required identity values;
- provider security IDs are unique across entities;
- provider trading-item IDs are unique across entities;
- provider ticker/exchange match the frozen `run_4` ticker/exchange.

The raw master includes an input column named `SP_SECURITY_ID` only to satisfy the existing parser's generic security-column contract; its values are the provider `SP_CIQ_ID`, and the rows explicitly record `SECURITY_ID_SOURCE_METRIC=SP_CIQ_ID`. Do not misstate this as evidence that Capital IQ exposes a generic `SP_SECURITY_ID` metric.

Disposition: primary identity is solved. Do not spend another round on Identifier Lookup traversal unless independently auditing the mapping. Use the captured master and exact primary SPT values for market acquisition.

## 10. Stale / failed approaches that must not be retried as incumbents

- embedded SNLQuery / persisted-query execution via synthetic `ExcelModel` / synthetic Unity provider — reproducible hang;
- repeated unmanaged PowerShell + COM Excel restarts — produced orphan automation processes and ambiguous ROT attachment;
- automation Excel as auth publisher — does not reliably run the normal `initSecurity` transition;
- raw legacy WCF ProductQuery as the main route — direct endpoint reachable but not the current Office transport incumbent;
- direct raw Genix `SPGTable` without Office metric normalization — auth/HTTP works but function keys are transformed by the Office engine;
- `SNLPrice` / legacy compatibility market history — stalled and cancelled;
- UI SendKeys/autocomplete as the identity incumbent — focus/timing-sensitive; exact UIA `ValuePattern` + `SelectionItemPattern` is preferred.

## 10.1 Bulk market acquisition / query-width findings

Bulk acquisition is an operational throughput problem, not a field or identity problem.

The stable extraction pattern is one fresh Excel/Office process per atomic chunk, with atomic temp-file → final-file landing. The current chunk script is `tmp/ciq_capture_market_chunk.ps1`; it can query either company IDs or exact primary SPT keys, clears the `SPGTable` formula before workbook close, and writes a part only after the provider result is fully materialized.

Observed width boundary for the full 109-name universe and exactly three daily market fields (`SP_TOTAL_RETURN`, `SP_PRICE_CLOSE`, `SP_VOLUME`):

- 5 weekdays = stable;
- 6 weekdays = stable;
- 7 weekdays = stable;
- 8 weekdays = failed at the bounded execution window with no final part;
- 10 weekdays = failed at the bounded execution window with no final part.

The same boundary held with direct primary `SPT...` query keys, so the limiting factor is query width/cell load, not company→primary lookup. **Seven weekdays is the largest proven stable atomic unit and should be treated as the incumbent.** Do not keep widening the chunk while this path works.

A 6-weekday company-key part and 6-weekday exact-SPT-key part for the target week were compared after excluding the per-row retrieval timestamp column; data values were identical. Exact SPT keys are therefore semantically equivalent to company-primary results and are the cleaner authority for the remaining history capture.

Existing raw custody at handover includes:

- nine earlier 5-weekday parts under `data/aov0/raw/ciq_market_parts_v3_20260808/`;
- an earlier standalone 5-day target-week object `data/aov0/raw/ciq_primary_security_market_history_20260808T163540Z.csv`, 545 rows, SHA-256 `4674c8f81d3d3ac3be3e44491a92b0abba48e9bcb296ae5cb6f85951870e45ed`;
- a validated exact-SPT 7-weekday target-week part at `data/aov0/raw/ciq_market_parts_spt_7d_test_20260808/part_033_20260730_20260807.csv`, SHA-256 `81779d8ed04b80a5b79298821f9ff5d89c96abf025e8bb06d9a67f864cd744aa`.

The earlier 5-day parts are real provider custody and may be retained as evidence/fill material, but the preferred completion path is one consistent exact-primary-SPT 7-day series. Reuse the validated target-week 7-day part rather than rerunning it unless an integrity check fails. Always verify final coverage by actual completed observations per security; requested weekdays are not equivalent to exchange sessions.

For target `2026-08-07`, a requested history horizon of roughly 230–238 weekdays gives cushion for exchange holidays. A 238-weekday request at 7 weekdays per chunk is 34 chunks. This is a planning heuristic only; the authoritative gate is the builder's actual completed-row count (`>=200` closes through the target date), not the requested date count.

There is an orphan `.tmp` file in the SPT 6-day test directory from a prior process. Repo policy forbids destructive cleanup without explicit owner confirmation; leave it alone unless authorized.

No chunk supervisor/worker is active at handover. Do not treat process existence as progress, and do not intentionally leave an unattended background worker running across handover.

## 11. Current gate and exact remaining work

The first-Clock gate is now:

1. **Use the already captured 109-name primary master** at `data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv`; verify its SHA-256 before use and preserve provider-source metric labels.
2. Complete exact-primary-SPT market history in 7-weekday atomic chunks using:
   - date;
   - provider `SP_CIQ_ID`;
   - exact primary `SP_TRADING_ITEM_ID` / `SPT...` query key;
   - `SP_TOTAL_RETURN`;
   - `SP_PRICE_CLOSE`;
   - `SP_VOLUME`;
   - actual provider retrieval timestamp.
3. Combine only real landed provider part CSVs into one raw market object; dedupe on (`SPT_DATE`, `SP_CIQ_ID`, `SP_TRADING_ITEM_ID`), retain the exact provider metric/source columns and retrieval timestamps, compute SHA-256, and count completed observations per security.
4. Require at least 200 completed close observations through `2026-08-07` for every name that survives the existing factor-coverage gate. Names with genuinely shorter listing history are excluded by the existing builder; do not backfill from alternate listings or identities.
5. Admit the raw master + final raw market object through the existing fail-closed builder to produce `rule100_targets`, `vertical_primitives`, and `total_returns`.
6. Build `decision_cut_v3` and execute Seal Candidate → fresh-process verification proof → immutable Clock-Start Receipt.

At handover, the `.venv` directory exists but the required `.venv/Scripts/python.exe` interpreter is absent. The repository requires `.venv` for Python execution, so do **not** silently run the builder with system Python. Restore the approved virtual-environment interpreter before the admission/build step.

No historical PIT rebuild, optimizer, architecture, broker work, SNLQuery/SNLPrice/SPGRANGE retry, or Parent/Child tuning is authorized on this path.

## 12. Custody / claim boundary at documentation time

- A real 109-name primary-security raw export is captured and hash-bound, but it is **not yet admitted**.
- Market raw custody is partial: nine earlier 5-day parts plus a validated 7-day exact-SPT target-week part exist, but no complete >=200-observation combined market object has been admitted.
- No real `rule100_targets.parquet`, `vertical_primitives.parquet`, or `total_returns.parquet` produced from the captured provider bytes.
- No real `decision_cut_v3` produced.
- No real Seal Candidate / verification proof / Clock-Start Receipt.
- Prospective clock remains false.
- Portfolio-alpha evidence remains `0`.
- The provider findings above are capability/diagnostic evidence only until raw source objects are materialized, hash-bound, timestamped, and admitted.
