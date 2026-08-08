# Planner Packet — Current

Date: 2026-08-08
Active product state: `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`
ACTIVE_STATUS: `REAL CIQ ADMITTED; V3 SEAL FULL-CHAIN VERIFIED; IMMUTABLE CLOCK-START RECEIPT ISSUED; FINANCIAL_ALPHA_EVIDENCE_0; LIVE CLOSED`
Canonical product maturity: `70/100`
Portfolio-alpha evidence: `0`
Limited Live: `CLOSED`

## Lane 1 implementation update — 2026-08-08

- Weekly-tape preflight is implemented independently of Alpha PIT/CRV1. It fixes the candidate laboratory to the original 109 entities and fails closed unless all four required current source receipts are newly retrieved after the prior cut. It does not acquire data, build a cut/seal, rerun the growth screen, open outcomes, or mutate Parent/Child.
- `alpha_pit_data_api_v1` mechanical capability is now implemented with deterministic fixture artifacts: permanent `CIQSEC:` identity, `available_at <= as_of`, source-receipt/hash bindings, explicit coverage/missingness, and lazily imported discovery-only outcomes. CONFIRMATORY/PROSPECTIVE objects expose no `outcomes` method.
- `CYCLE_RESONANCE_v1` mechanical fixture consumer is now implemented against the provider-blind Alpha PIT interface and emits a deterministic input-packet hash with `financial_alpha_evidence=0`. Real PIT integration and a frozen empirical CRV1 candidate remain open; fixture output has zero PIT/OOS/prospective/financial-alpha authority.
- Validation for this slice: Lane-1 focused `13/13 PASS`; AOV `79/79 PASS`; ZERO-COMPAT contract test PASS asserting all seven counters are zero; selected Lane-1 modules compile PASS. Direct ZERO-COMPAT CLI execution was blocked by the tool host before execution and is not separately claimed.
- Current P0 is now dual-lane: keep weekly fresh-data acquisition/sealing on its own cadence **and** make historical PIT A1→A2 measurement of the frozen incumbent a first-class critical lane. Alpha PIT/CRV1 mechanics may continue behind their frozen interface, but no outcome-informed mutation is legal before a matured, reconciled, validated ReviewPacket.

## Owner execution recut — Lane 2 Historical Compression — 2026-08-08

- Owner rating=`9.77/10`; philosophy/roadmap approved with one execution recut: `A1_A2_SECOND_CRITICAL_LANE`.
- Lane 2 sequence: legitimate historical PIT CIQ reconstruction → exact frozen-AOV replay → A1 → freeze immutable A2 split/query/metric/executable contract → query-metered untouched historical PIT OOS → A2 → Parent/Child incremental economics + loss/missed-winner diagnosis.
- Lane 2 does not open Clock #1 outcomes, tune Parent/Child between A1 and A2, or grant prospective/capital authority. If historical universe/source/availability semantics are insufficient, fail closed to a bounded diagnostic rather than claiming A1/A2.
- A2 may drive `CONTINUE / PIVOT / HOLD` for future challenger research, but once A2 is used to design a challenger it is not untouched evidence for that challenger. Material changes to a frozen CRV1 object require a new version/family rather than in-place rescue.
- Operating objective=`EVIDENCE_VELOCITY × ECONOMIC_RELEVANCE`. Broad second-family/AI/data/provider/UI/options/leverage/optimizer/platform work remains suppressed until evidence makes it the nearest economic blocker.

## Clock #1 completion update — 2026-08-08

- Exact-primary-SPT parts `004..033` supplied sufficient history. Final market raw object: `data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv`, 21,345 rows, zero duplicate-key conflicts, SHA-256 `897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48`. The 109-name primary master reverified at SHA-256 `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`.
- CIQ admission succeeded with 99 canonical securities, 10 mechanical exclusions, 26 Rule100 sizing-eligible names, and risky gross `1.0`. Five short-history listings were not backfilled; two of those were already excluded by factor coverage.
- `decision_cut_v3` is `AOV0_CIQ_20260807_ad2faf0533cec19c`, SHA-256 `81926aa896485a4a646228920ae0769283f143328ff8fe1f6671929136cd9b80`.
- Real Seal Candidate `c78088ace7819170cd0064154fba138da4b4f8183dbd4ec48c347a942985ba88` was written clock-false, then a distinct Python process returned `FULL_CHAIN_REOPEN_VERIFIED`. Immutable Clock-Start Receipt `eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78` started Clock #1 at `2026-08-08T19:48:52.440503Z`.
- Evaluation begins `2026-08-10T20:00:00Z`; outcome authority remains sealed until `2026-09-09T20:00:00Z`. `financial_alpha_evidence=0`; Limited Live remains closed. The repo `.venv` is restored on Python 3.12 and AOV regression is `75/75 PASS`. Repository-wide pytest still has nine unrelated/inherited collection errors, so no full-suite PASS is claimed.
- The remainder of this packet contains pre-Clock history plus post-Clock roadmap detail. Where it says the real CIQ/Clock #1 path is still open, this completion update supersedes that stale execution-state wording.

## Current truth

- Published main/tag remains exact `9af5259`; no publication action occurred this round.
- Episode 1 remains release-ready at `ab258c3`.
- Episode 2 is locally immutable at `39f7be3894623c095994066b8f0ea2895b968643` and passes exact archived-byte `115/115`; `142/142` is stale.
- E2 push, hosted Windows/Linux, independent audit, FF/tag publication remain open external actions.
- AOV local executable lineage ends at `dca69fc72dd3192913aa921323ff48f68610a925`.
- Four duplicate root apps/launchers and current-root legacy release rebuild compatibility are removed.
- ZERO-COMPAT all seven counters are zero, including the archived/release executable-source import guard.
- Research-spine identity/benchmark/cost/PIT-EW/Rule100/evidence defects are repaired.
- Minimal cube, Rule100, Parent, one Child, hash DAG, five-arm/seal machinery, official-SOFR cash, and deterministic review core exist locally.
- Active AOV equity authority is destructively recut to S&P Capital IQ Pro because the available WRDS account lacks CRSP entitlement: canonical identity is `CIQSEC:<Capital IQ Security ID>`; company `SP_ENTITY_ID`, ticker, legacy PERMNO, and dual-provider compatibility fail closed.
- First-seal v2 custody remains historical/mechanical evidence only. The destructive v3 recut is now implemented locally: active code uses `aov0_ciq_decision_cut_v3`, `aov0_prospective_seal_v3`, `aov0_prospective_clock_start_receipt_v1`, and `NYSE_2026_CORE_CLOSE_1600_ET`; active runtime contains no v2/open compatibility reader or writer. Seal construction writes a clock-false Seal Candidate; a fresh child Python process must produce exact full-chain verification proof before a separate immutable Clock-Start Receipt can set clock authority. Daily-return attribution rejects intervals whose left endpoint precedes `evaluation_start`, and maturity is exactly `evaluation_start + 30 calendar days`.
- `run_4.xlsx` is now the single hash-bound 109-company universe + current-cut fundamentals authority and is locally materialized into `data/aov0/intermediate/ciq_entity_quarterly_panel.parquet` (1,203 rows) plus `ciq_entity_fundamental_state.parquet` (109 rows): 56 complete four-group states, 52 partial states, one no-absolute-quarter-history state. Its receipt carries both `COMPANY_UNIVERSE` and `QUARTERLY_FUNDAMENTALS`; `run_2.xlsx` is historical evidence only and no longer enters the decision cut. Canonical Rule100 V1.1 `factor_positive_count` is available locally; `SP_ENTITY_ID` remains temporary company identity only. This current-cut artifact uses absolute `FQqYYYY` history and conservative local admission-time `known_at`, so it is not historical PIT replay proof.
- The CIQ Security/market admission path is executable locally: `research/aov0/ciq_market.py` + `scripts/aov0_build_ciq_market.py` accept one primary-security master plus same-cut daily market history, mechanically exclude ambiguous/missing identity, `<3` factor coverage, missing/short market history, non-finite target state, or identity collision, and never fall back to ticker/entity/PERMNO/yfinance. Historical market rows warm the 20d/200d state only; because `run_4` is current-cut-only, the builder emits exactly one current Rule100 target row and one matching current total-return row rather than fabricating historical Rule100 replay. For the frozen U.S.-listed universe, a same-day daily target is invalid unless the market export was retrieved at/after 16:00 America/New_York; pre-close daily rows and future-stamped retrievals block before output.
- CIQ provider capability is now proven, not hypothetical. The installed S&P Capital IQ Pro Office client is authenticated; the modern SPG/Genix function path works; direct Genix auth/HTTP/serialization was proved with `SPGLabel`; and the supported Excel `SPGTable` path returns exact-date market values needed by the admission builder. Full diagnostic details are frozen in `docs/context/ciq_provider_acquisition_findings_20260808.md`.
- The current market field contract is now concrete: `SP_TOTAL_RETURN` (provider percent total return), `SP_PRICE_CLOSE`, and `SP_VOLUME` all return by exact date through `SPGTable`. For probe entity `4094286` on `2024-06-28`, the provider returned total return `-0.362932`, close `123.54`, and volume `315516740`. The remaining market work is bulk raw-object materialization for the frozen universe with `>=200` completed daily rows plus explicit retrieval timestamp/hash; it is no longer field-discovery work.
- Historical PIT fundamentals capability was also proved through `SPG(entity, metric, period, as_of_date, options)`: for entity `4094286`, `FQ0` period/revenue changed from `2024-01-28 / 22103000` at as-of `2024-04-30` to `2024-04-28 / 26044000` at as-of `2024-06-30`, and `FQ12025` was `NA` before becoming available. This is banked post-Clock capability only; it does not convert `run_4` into historical PIT authority and must not be used to tune Parent/Child before first Clock.
- Primary Security/Trading Item identity is solved. Identifier Lookup proved primary `SPT344984472` and alternate `SPT364472819` for `COE`; both share `SP_CIQ_ID=IQ337968870` while `SP_TRADING_ITEM_ID` differs, proving `SP_CIQ_ID` is security-level and `SP_TRADING_ITEM_ID` is listing-level. Direct company-key `SPGTable` returns the same primary pair, so 109 UI traversals are unnecessary. A real 109-row master is in raw custody at `data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv`, retrieval `2026-08-08T16:23:22.0736860Z`, SHA-256 `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`; all security/trading IDs are unique and ticker/exchange match the frozen universe. It is captured but not yet admitted.
- Frozen current-cut market formulas reuse the existing Rule100/feature law: `ADV20=rolling20(close*volume)`, `realized_vol=rolling20_std(total_return)*sqrt(252)`, SMA20/SMA200 trend, Rule100 v1 hold law `factor_present_count>=3 AND factor_positive_count>=2`, and the product/AOV `0.35` max-weight path. AOV-only local regression is now `75/75 PASS`. Synthetic v3 coverage proves Seal Candidate → actual fresh-process `FULL_CHAIN_REOPEN_VERIFIED` proof → separate Clock-Start Receipt with `financial_alpha_evidence=0`.
- Direct NY Fed SOFR is admitted after the 15:00 America/New_York gate: retrieval `2026-08-07T19:00:08.894288Z`, raw SHA-256 `445ca1ae93a7ae904681716d8e37088fab905ae4f74f32fc2619a459918d54cc`, 30-row Parquet SHA-256 `ed75219416a524f17cb3e29b9e4fadff2dcfa1d12a8368d752007aac779c4e5e`, latest effective date `2026-08-06`. `scripts/aov0_build_decision_cut.py` now constructs/self-validates v3 from the four active source receipts, reconciles target Rule100/return/primitive sets, and requires the exact next frozen NYSE 16:00 ET close evaluation boundary. `scripts/aov0_first_seal.py` creates only the Seal Candidate; `scripts/aov0_reopen_seal.py` emits a fresh-process verification proof, and only the separate immutable Clock-Start Receipt can authorize the prospective clock.
- Production insurance V0 is frozen at materiality `0.05` and annual premium ceiling `0.0015`; changes require a new contract/model family.
- Real `official_sofr.parquet`, the 109-name primary Security/Trading Item master, the 21,345-row exact-primary-SPT market object, current Rule100 targets/primitives/returns, and `decision_cut_v3` are admitted. CIQ admission yields 99 canonical securities, 10 mechanical exclusions, 26 Rule100 sizing-eligible names, and risky gross `1.0`; no alternate-listing backfill was used.
- Real Seal Candidate + fresh-process verification + immutable Clock-Start Receipt exist and Clock #1 is running. Evaluation has not started; outcomes remain sealed; no matured A3 evidence exists; `financial_alpha_evidence=0`.
- Latest roadmap verdict is `APPROVED_WITH_VELOCITY_PARALLELISM_RECUT`. Prior Winner/authority semantics remain intact: `CYCLE_RESONANCE_v1` is first confirmatory Alpha Family and `NOT IMPLEMENTED`; Right-Tail Atlas is Minimum-Viable-Atlas-first and discovery-only episode forensics; winner-blindness is diagnostic only; entry/hold/exit remain separable. Post-Clock construction is authority-domain-scoped under one writer + immutable join gates.
- Sim-to-real alignment still finds a post-Clock operational tail, not a pre-Seal blocker. Existing primitives are reusable: broker submit/recovery/fill telemetry, orchestrator idempotent retry + reconciliation quarantine, signed replay protection, and deterministic event/book/replay. Initial PAPER execution incumbent is `MOC_CLOSE_AUCTION_V1 = market + cls`; missing authority is the thin binding/projection layer: one promoted policy/seal → one `live_rebalance_id`; PIT hash-bound `CIQSEC`↔broker instrument/account map; full broker lifecycle/open-orders → canonical live book; broker-first restart reconciliation + rebalance fencing + persistent `FREEZE_NEW_RISK`; and research-vs-broker implementation-shortfall attribution. Current rebalancer submission does not yet propagate close TIF even though the low-level broker adapter accepts `time_in_force`.

## Active bottleneck

```text
CLOCK #1 CUSTODY                                      [CLOSED / RUNNING]
→ evaluation_start = 2026-08-10T20:00:00Z
→ outcome_open_not_before = 2026-09-09T20:00:00Z

ACTIVE SHIP-FAST BOTTLENECK
→ LANE 1 FUTURE TRUTH: weekly AOV/review custody stays always-on; Alpha PIT + CRV1 mechanics advance behind frozen joins
→ LANE 2 COMPRESSED LEARNING: historical PIT CIQ → exact frozen-AOV A1 → freeze → untouched/query-metered A2
→ use A1/A2 economics to identify where Parent/Child lose money or miss/clip winners

PARALLEL ONLY WITH INDEPENDENT OWNERSHIP / NON-CRITICAL
→ bounded AI Research Tooling
→ thin PAPER Capitalization
→ Market Transition discovery incubator
```

Architecture is closed. The active P0 is now **time-to-first-honest prospective Challenger plus uninterrupted Clock #1 custody**, not more pre-Seal infrastructure. Outcomes remain sealed and Parent/Child stay frozen.

## Immediate sequence

1. Preserve/reverify the immutable Clock #1 chain; keep the frozen-109 weekly prospective tape alive and do not open outcome authority before `2026-09-09T20:00:00Z`.
2. Open **Lane 2 Historical Compression** immediately under separate writer custody: define the legitimate historical universe/source/availability/identity contract and capture/reconstruct PIT CIQ inputs without touching Clock #1 outcome authority.
3. Run exact frozen-AOV historical replay with the current Rule100/Parent/Child/insurance/cash/cost/execution semantics. Admit A1 only if the historical contract actually supports the claim; otherwise record the strongest honest diagnostic scope.
4. Before any hidden historical OOS inspection, freeze the A2 split/query budget/metrics/executable hashes and outcome-access contract. Then perform the query-metered untouched A2 evaluation once and retain the result append-only.
5. Put the incumbent economics on the board: Parent, Child, Child-minus-Parent, compounding, drawdown, turnover/cost/cash drag, loss concentration, missed winners, under-sizing, premature reductions/exits, and right-tail clipping. This is the primary near-term research decision input.
6. Continue Alpha PIT + CRV1 **mechanical** producer/consumer work in its independent authority domain against frozen contracts/fixtures. A1/A2 may determine `CONTINUE / PIVOT / HOLD`, but may not silently retune a frozen CRV1 v1; a material change requires a new version/family.
7. Keep deterministic review/custody closure ahead of first prospective outcome maturity. Real outcome-informed AI mutation remains blocked until a matured, reconciled, validated ReviewPacket.
8. Supporting work may run only with independent ownership and without slowing Lane 1/Lane 2: bounded AI receipt/schema/fixture/source-claim tooling; thin PAPER Capitalization; Market Transition Crisis/false-crisis discovery only; async borrow/replication preparation.
9. Suppress a second confirmatory Alpha family, generic AI/data/provider platform, elaborate research UI, options infrastructure, leverage system, universal Right-Tail Atlas, optimizer-first work, generalized external-strategy ingestion, and generic execution architecture until measured evidence identifies one as the nearest economic blocker.
10. Preserve the destructive-authority law: new current authority deletes old active reader/writer/fallback/alias/dual-write/old-authority feature flag/compatibility adapter in the same slice; immutable historical evidence remains replayable only with pinned historical code/schema.
11. Do **not** make unrelated inherited repository-wide pytest/SAW failures an Alpha research critical-path dependency. They still block a repository phase-close claim, but an owned deterministic Lane-1/Lane-2 slice may ship when its scoped gates pass and the unrelated failures are recorded.
12. Bounded long/cash remains downstream of prospective edge + genuinely independent replication + PAPER capturability + owner/risk approval. Leverage/short/options remain disabled until separately evidenced and authorized.

## Validation already banked locally

- E2 exact `39f7be3`: `115/115 PASS`.
- AOV including CIQ fundamentals + Security/market admission + SOFR + destructive v3 cut/seal/clock promotion: `75/75 PASS`; synthetic current-cut v3 Seal Candidate → fresh-process verification proof → Clock-Start Receipt PASS.
- Hardened research selected suite: `33/33 PASS`.
- Dashboard/book/historical receipt: `33/33 PASS`.
- Hard-cut E2 regression: `107/107 PASS`.
- Historical Alpha runtime substrate live checkout: `7/7 PASS`.
- ZERO-COMPAT: `0/0/0/0/0/0/0`.
- Compile, YAML parse, `pip check`, whitespace: PASS.
- Calibration validation: `INSUFFICIENT` (one historical row); fallback accepted for now and must not be mislabeled `DRIFT`.
- Pre-Seal adversarial v3 test gate: PASS — bound market one-byte mutation, +1bp serialized target mutation, Security-ID/ticker mutation, SOFR substitution, same-process promotion denial, weekend/wrong-close/legacy-open/pre-cut timing, pre-evaluation return interval, early maturity, and pre-receipt/pre-evaluation/pre-maturity availability all fail closed as required.
- Performance disposition: no compute optimization; current 109-name daily-scale workload is not the bottleneck.

## Stop conditions

- frozen insurance V0 values are changed in place or calibrated from outcomes;
- historical/equal-weight/ticker data is relabeled as current Rule100/PIT authority;
- official SOFR is substituted or used before publication;
- duplicate app/engine or compatibility alias reappears;
- evidence manifest becomes mutable or benchmark selection becomes positional;
- Parent/Child drift outside the declared mutation;
- accounting/review residual fails;
- outcome data opens early;
- alpha/live claim precedes matured replicated evidence.

## Claim boundary

Before Clock #1: no score uplift, financial-alpha claim, historical Right-Tail Atlas build, AI/source pipeline implementation, Market Transition implementation, provider programme, candidate-app PIT authority, AOV-2/event authority, optimizer/RL-first route, broker/order work, leverage/short/options authority, live capital, compatibility restoration, Episode-3 milestone, universal PIT/data/AI platform, distributed-compute/GPU/streaming platform, or pre-Seal code-quality refactor. `CYCLE_RESONANCE_v1`, AI Research Pipeline v0, Market Transition and Resonance Leverage specifications are docs/research-governance only. After Clock #1, domain-parallel construction is approved only under one-writer/immutable-join law; strategy live capital remains closed.
