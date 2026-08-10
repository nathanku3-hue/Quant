# Lane 2 status — 2026-08-09

## Custody / non-negotiable boundary

- Authoritative worktree: `.worktrees/devspace-053ca7a4f582fb3e` (`codex/pit-source-authority-1`)
- Strategic lock: `docs/architecture/aov_strategic_direction_lock_20260809.md`
- Historical vintage authority: `docs/architecture/historical_fundamental_vintage_authority.md`
- `financial_alpha_evidence` remains **0**
- Prospective Clock #1 remains untouched; outcomes stay sealed
- Parent / Child parameters remain untouched

## Current evidence gate

```text
Vintage authority                 CLOSED — CIQ SPG historical as-of + FilingVer=Original
Current↔historical AOV parity     CLOSED — historical decisions call exact current-cut builder
Historical high-growth risk set   CLOSED — 104-company 2025-05-16 reconstruction admitted, current-screen conditioning rejected
Historical primary identity       CLOSED — exact dated Major-US/funding security selection, 104/104, no current-primary conditioning
Terminal lifecycle authority      CLOSED — 3 source-bound cash-merger/terminal events, no survivor filtering
A1                                ADMITTED — 264 trading days / 94 active CIQ securities / all canonical gates PASS
A2                                CLOSED — one frozen/query-metered untouched read, query_count=1
```

A1 report classification is `A1_ADMITTED_HISTORICAL_PIT`; A2 result classification is `A2_UNTOUCHED_HISTORICAL_PIT`. Both remain historical-only evidence and keep `financial_alpha_evidence=0`. The A2 chronology is A1 report `2026-08-10T07:33:38Z` → freeze `07:36:04Z` → held-out PIT capture after freeze → query lock `07:43:15Z` → result/receipt `07:45:03Z`. Any lower section that still describes these gates as open is retained only as pre-closure investigation history and is superseded by this gate block.

## Fundamental vintage / parity work completed

The prior Original-vs-Current/Restated contradiction is closed:

- all four active historical fundamental acquisition scripts request and emit `FilingVer=Original`;
- replay source validation rejects non-Original rows;
- retained CIQ provider probing proved that the SPG historical as-of argument gates observable fundamentals across cutoffs;
- `research/aov0/ciq_historical_pit.py` is explicitly demoted to `LEGACY_DIAGNOSTIC_ONLY_NOT_A1_A2_AUTHORITY`;
- historical weekly decisions now call `research.aov0.ciq_market.build_ciq_market_slice` directly;
- same-input tests cover identity, ADV20, realized volatility, SMA/trend, Q/U inputs, technical state, exit capacity/regime, sizing eligibility, Rule100 weights, and Q/M/F/C/L/R/U cube state;
- decision-cut cube state is frozen onto the next observed close through `activate_decision_cube_states`, preventing activation-day information from entering the decision;
- a canonical five-arm test runs successfully on the activated historical cube.

## Formal source-authority blockers

### 1. Historical high-growth start risk set — OPEN, narrowed to company-state history

`run_4.xlsx` is the sole frozen **current-cut** 109-name screen baseline; `run_2` is diagnostic/older export only and has no A1 authority. The current 109 is not promoted into historical membership.

The authenticated CIQ Pro web session now closes the historical market and revenue components at the A1 start date without Xpress:

- Securities perspective `321247` + `SPT_PRICE_CLOSE` field `324251` with date secondary `sk_557=05/16/2025` returns the target-date traded-security population.
- Provider exchange group field `406718`, value `-1,-4`, is **exactly** the 2025-05-16 union of NYSE=`0`, NYSEAM=`1`, NASDAQGM=`2`, NASDAQCM=`211`, NASDAQGS=`212`: 5,394 security rows on both paths, zero differences. ARCA=`33` adds eight and is correctly outside the group.
- Funding-type field `321268` uses the retained equity values `1,16`.
- Companies perspective `266637`, `IQ_TOTAL_REV` field `329288`, exposes period `sk_854`, Reporting Basis `sk_858`, and As Of Date `sk_860`. Capital IQ's own serializer generates historical tokens such as `{IQ_TOTAL_REV(FY0|Originally Reported|05/16/2025|0)}`.
- The three exact 30% revenue formulas validate in the provider formula engine. Intersecting the date-qualified market population with all three **Original + 2025-05-16** revenue predicates yields **104 companies**.
- Those 104 names are frozen as non-authoritative evidence at `data/aov0/historical/source_authority/20250516/ciq_productquery/market_original_revenue_candidates_20250516.csv`, SHA-256 `02a7daa757cfbaeae6cf37e70509e787f4705d54f9bd2d234074e5ee61b946ae`, membership hash `de5c7c83a87a7e8af1cdb54ac792bd91e95ee8edf69facd4c2a13c9be679f751`. Its receipt explicitly carries `historical_risk_set_admission_authority=NONE`.

The remaining risk-set blocker is **historical Company Type / Company Status**. CIQ's current profile fields are not PIT: among securities that definitely traded on 2025-05-16, current labels include later `Acquired` / `Private Company` states, and the Office `SPG` as-of parameter does not rewind those profile fields. In the bounded 104-name cut, 101 are still labeled Public today and three are now Private (Global Blue, Evoke Pharma, ZEEKR); all 104 are still Operating / Operating Subsidiary today. Global Blue has provider M&A evidence that its acquisition completed 2025-07-02, after the A1 cutoff, proving its current Private label cannot be back-projected. Formal membership nevertheless remains open until historical company-state semantics are mechanically reconstructed for the exact cohort.

### 2. Historical primary security / trading-item identity — OPEN, narrowed

Formal A1 still requires the separate hash-bound historical-start primary-security receipt. `research/aov0/historical_security_master.py` rejects current-conditioned mappings, as-of drift, membership drift, hash/size/name drift, and CIQSEC/SPT alias inconsistency.

The target-date Securities query materially narrows this gate:

- every one of the 104 candidate companies has **exactly one** qualifying Major-US-exchange security/trading row on 2025-05-16;
- all 104 of those exact dated rows are currently marked `Primary Issue? = Yes`;
- the rows carry SPT instrument item ID, SecurityID, SPCIQ ID, ticker, exchange, equity type, ISIN and SEDOL.

This is strong corroboration, but not yet historical-primary authority. `SPT_PRIMARY_ISSUE` and `SPT_SECURITY_STATUS` expose no effective-date secondary key and were independently proved current-conditioned outside the final cohort (Ascendis Pharma's historical dated row is now marked non-primary after a later primary change). An exhaustive field/schema + installed-client search found no readable `Primary Since` / effective-primary or Base Security/GICRS endpoint. No historical-primary receipt is minted from current flags or uniqueness alone.

## Market custody

- Warmup complete: `data/aov0/historical/raw/market_warmup_to_20250516` parts **000–032**, 2024-07-08 → 2025-05-16, 217 sessions, 96 CIQ securities with any history.
- Older SMA200/252-day backfill: `market_backfill_to_20240705` remains **1/34** (part 000 only, 2023-08-14 → 2023-08-22).
- Current/gap custody already extends beyond the driver A1 start (`2025-05-16`), so the older 2023 backfill is no longer the first formal blocker. The historical risk set + historical primary identity own the critical path.
- Market continuity remains fail-closed; alternate listings are not substituted for short histories.

## Fundamental diagnostic custody

A current-109 diagnostic period matrix is now fully landed at:

`data/aov0/historical/raw/period_matrix_min_a1_diag`

| Cut | Rows | Missing FQ0 |
|---|---:|---:|
| 2025-04-25 | 109 | 87 |
| 2025-05-02 | 109 | 87 |
| 2025-05-09 | 109 | 52 |
| 2025-05-16 | 109 | 19 |

These bytes are **diagnostic only** because the cohort is current-screen/current-primary conditioned. The old permissive transition plan contained 183 transitions; after removing planner/engine semantic drift, the authoritative planner now stops immediately on the missing-FQ0 gate. No expensive transition capture will be spent on a matrix that cannot replay.

Official SOFR historical custody remains admitted: `nyfed_sofr_20230101_20260807.json`, 897 rows, 2023-01-03 → 2026-08-06.

## Driver / code hardening

`scripts/aov0_lane2_a1_driver.ps1` now:

- requires both the historical risk-set receipt and historical primary-security receipt for admitted A1;
- defaults to one period date and one factor transition per Excel process under the observed Office stability envelope;
- derives exact expected part counts / filenames;
- verifies each landed file and exact row count;
- does not advance after partial output;
- can tolerate a nonzero COM teardown only when the final expected complete file is already atomically landed.

`plan-transitions` delegates to the authoritative `build_factor_transition_plan`, so missing FQ0 fails before provider spend.

## Excel / CIQ operational state

Office remains intermittently unstable after repeated automation restarts (`RPC_S_CALL_FAILED`, transport 502s, modal/in-progress CIQ states). Several captures nevertheless landed before COM teardown. Do not infer failure or success from process/transport state alone; landed final bytes + validation own custody.

Do not force-kill ambiguous Excel processes because they may contain unrelated user work. Prefer bounded fresh-process calls when Office is healthy; if a call transports poorly, check final landed bytes before retrying the same chunk.

### Host diagnosis update (Trial 5 series, same day)

- Orphan thrash Excel cleaned; Quark HKCU `LoadBehavior=0` held.
- **Dismisser bug fixed:** never `WM_CLOSE` the main CIQ shell title `S&P Capital IQ Pro` (was killing boot in Trial 5a).
- Trial **5b** proved 1×1 smoke still works after clean boot, then Excel died on first bulk entity batch (N=8).
- Trial **5c** serial (N=1) failed to obtain CIQ add-in object after thrash — **stop unattended bulk**; require interactive recovery first.
- Packet: `docs/phase_brief/lane2_host_diagnosis_trial5_20260809.md`. Scripts: `tmp/lane2_host_cleanup.ps1`, `tmp/aov0_backfill_trial5_tiny.ps1`.
- Backfill remains **1/34**; no `part_001` yet.

### Recovery checkpoint after interactive cleanup

- The failed-trial orphan was removed by exact PID; no ambiguous/user Excel process was force-killed.
- Quark remains disabled (`HKCU LoadBehavior=0`). `SPGMI.ExcelShell` now has a per-user `LoadBehavior=0` override and verifies `Connect=False`, while the core `SNL.Clients.Office.Excel.ExcelAddIn` can remain connected independently.
- Office resiliency re-quarantined the **core** CIQ Excel add-in after a crash. The new `DisabledItems` payload was byte-identical to the previously backed-up SNL core entry; clearing only that entry restored `CIQ_READY`. The current cleanup state is no Excel process, zero `DisabledItems`, and `SPGMI.ExcelShell LoadBehavior=0`.
- Micro-shape probes briefly proved row expansion at 5×2, 10×2, 20×2 and 25×2. Real part capture then degraded back to the sparse host mode: 10×7=`21` filled, 5×7=`21` filled, and date-subbatch 25×2=`6` filled; cell-by-cell and bulk `Range.Value2` both showed only the first entity row populated.
- Sparse-fill gates rejected every attempt; **no `part_001` was written**. `part_000` reverified at 530 rows / 76 entities, SHA-256 `24d24848388a66d7183804c4ad1a5f932371563be04d92225c5e1dafba123c31`.
- Capture tooling is hardened for any later controlled retry: owned-session boot uses `/x` + ROT rather than `New-Object`, refuses pre-existing Excel instead of broad-killing it, verifies the Office Tools shell is disconnected, and live attach has a single-writer mutex plus fail-closed sparse coverage. These mechanics do **not** make the host reliable.
- Stop rule is active: no further unattended SPGTable retries this round. The older 2023 market backfill remains continuity work; the historical risk-set and historical-primary-identity source blockers own the formal A1 critical path.

## Fastest automatic unblock route

`scripts/aov0_lane2_unblock_fast.ps1` is the fail-closed source-authority controller. It launches **no Excel** and intentionally prioritizes the two formal A1 source blockers over `part_001`.

- `-Mode Status` reports which source authority is missing without touching provider state.
- If a valid historical risk-set membership/receipt already exists, the controller validates it through `load_historical_start_risk_set`.
- Xpress remains a supported alternate market-candidate path, but it is **no longer the Lane-2 critical dependency**. Authenticated CIQ Securities ProductQuery now provides the target-date market component directly, and the reconstruction/admission code accepts either the pre-existing Xpress receipt or a fail-closed CIQ Securities receipt.
- The CIQ Securities receipt contract binds perspective `321247`, close-price date gate `324251/sk_557`, exchange group `406718=-1,-4`, funding field `321268=1,16`, and exact same-date parity against the explicit five-exchange union. It still carries no A1 authority by itself.
- A final risk-set reconstruction still requires historically bound company type/status plus the already-proved Original/as-of revenue law. The 104-name market+revenue intersection is a bounded candidate set, not admitted membership.
- The historical-primary identity gate still requires provider historical primary/effective relationship evidence or an equivalent provider-generated same-date snapshot. Current primary flags, even when corroborated 104/104, remain insufficient under the current contract.
- Once both final receipts validate, the controller may report `A1_SOURCE_AUTHORITY=UNBLOCKED`; only then should the existing Lane-2 A1 driver materialize replay inputs for the exact admitted cohort.

Current dry status: the Xpress credential gap no longer blocks the target-date market component. A provider-verifiable 104-name market+Original-revenue candidate freeze exists, but no final historical risk-set receipt and no historical-primary receipt exist. The authenticated Screener has no global historical-date switch; date authority is bound explicitly through Securities `SPT_PRICE_CLOSE[2025-05-16]` and `IQ_TOTAL_REV(...|Originally Reported|05/16/2025|...)` secondary keys. Company profile type/status fields remain current-state and therefore cannot complete the risk set without separate historical reconstruction.

## Ordered next steps

0. **Market backfill is quarantined, not the current A1 critical path:** do not restart bulk SPGTable this round. Any later retry requires a clean interactive Excel/CIQ core host with `SPGMI.ExcelShell` still off, then one bounded part_001 trial behind the ≥40-entity / ≥200-row gate.
1. Use `scripts/aov0_lane2_unblock_fast.ps1 -Mode Status`; prefer API/feed source authority over desktop capture.
2. Complete **historical Company Type / Company Status** reconstruction for the frozen 104-name market+Original-revenue candidate cohort. Do not use current profile labels as historical truth; bind dated provider event/state evidence to every inclusion/exclusion needed by the final screen.
3. Complete **historical primary security + trading-item** selection for the exact final cohort. The one-row-per-entity dated Securities evidence and 104/104 current-primary corroboration may support the proof, but cannot replace an effective-dated provider-primary relationship under the current contract.
4. Finalize/admit the historical risk-set + historical-primary receipts; then materialize historical market/fundamental replay inputs for exactly that admitted cohort and only then spend transition-query budget.
5. **DONE:** A1 admitted through the exact current-cut decision builder + activated historical cube: 264 trading days, 94 active CIQ securities, Original/as-of PIT semantics, source-bound terminal lifecycle, and all canonical arm gates pass.
6. **DONE:** immutable A2 freeze binds the admitted A1 report, 94 frozen active securities, implementation hashes, source cohort, terminal-event packet, A2 window `2026-06-12..2026-08-07`, and one-query law.
7. **DONE:** exactly one untouched A2 query executed after the freeze; result and query receipt are append-only/hash-bound and second evaluation is forbidden.
8. **NEXT:** keep Parent/Child frozen and use the already-visible A1/A2 economics for loss/missed-winner and regime diagnosis; continue prospective Lane 1 independently. A1/A2 never increment `financial_alpha_evidence` under current law.

## Non-claims

- A1/A2 are historical evidence only, not prospective financial-alpha evidence
- No Parent / Child mutation occurred between or after A1/A2 in this closure
- No prospective Clock #1 outcome was opened
- No `financial_alpha_evidence` uplift occurred
- No live-capital authority was created
