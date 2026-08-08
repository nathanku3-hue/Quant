# Planner Packet — Current

Date: 2026-08-08
Active product gate: `PRE_SEAL_REAL_CIQ_ADMISSION`
ACTIVE_STATUS: `WINNER/AUTHORITY RECUT APPROVED ~99/100; TOP-LEVEL DESIGN EFFECTIVELY CLOSED; PRIOR STRATEGIC + SIM-TO-REAL RECUTS RETAINED; PRE_SEAL_REAL_CIQ_ADMISSION UNCHANGED; REAL CLOCK BLOCKED ONLY ON REAL CIQ SECURITY/TRADING + COMPLETED MARKET BYTES`
Canonical product maturity: `70/100`
Portfolio-alpha evidence: `0`
Limited Live: `CLOSED`

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
- The CIQ Security/market admission path is now executable locally: `research/aov0/ciq_market.py` + `scripts/aov0_build_ciq_market.py` accept one primary-security master plus same-cut daily market history, mechanically exclude ambiguous/missing identity, `<3` factor coverage, missing/short market history, non-finite target state, or identity collision, and never fall back to ticker/entity/PERMNO/yfinance. Historical market rows warm the 20d/200d state only; because `run_4` is current-cut-only, the builder emits exactly one current Rule100 target row and one matching current total-return row rather than fabricating historical Rule100 replay. For the frozen U.S.-listed universe, a same-day daily target is invalid unless the market export was retrieved at/after 16:00 America/New_York; pre-close daily rows and future-stamped retrievals block before output.
- Frozen current-cut market formulas reuse the existing Rule100/feature law: `ADV20=rolling20(close*volume)`, `realized_vol=rolling20_std(total_return)*sqrt(252)`, SMA20/SMA200 trend, Rule100 v1 hold law `factor_present_count>=3 AND factor_positive_count>=2`, and the product/AOV `0.35` max-weight path. AOV-only local regression is now `75/75 PASS`. Synthetic v3 coverage proves Seal Candidate → actual fresh-process `FULL_CHAIN_REOPEN_VERIFIED` proof → separate Clock-Start Receipt with `financial_alpha_evidence=0`.
- Direct NY Fed SOFR is admitted after the 15:00 America/New_York gate: retrieval `2026-08-07T19:00:08.894288Z`, raw SHA-256 `445ca1ae93a7ae904681716d8e37088fab905ae4f74f32fc2619a459918d54cc`, 30-row Parquet SHA-256 `ed75219416a524f17cb3e29b9e4fadff2dcfa1d12a8368d752007aac779c4e5e`, latest effective date `2026-08-06`. `scripts/aov0_build_decision_cut.py` now constructs/self-validates v3 from the four active source receipts, reconciles target Rule100/return/primitive sets, and requires the exact next frozen NYSE 16:00 ET close evaluation boundary. `scripts/aov0_first_seal.py` creates only the Seal Candidate; `scripts/aov0_reopen_seal.py` emits a fresh-process verification proof, and only the separate immutable Clock-Start Receipt can authorize the prospective clock.
- Production insurance V0 is frozen at materiality `0.05` and annual premium ceiling `0.0015`; changes require a new contract/model family.
- Real `official_sofr.parquet` now exists at the seal input path. Real current AOV Rule100 targets/primitives/returns/decision-cut do not yet exist because the CIQ primary-security mapping and completed post-16:00 ET market export have not arrived.
- No A1 real AOV result, no real prospective seal, no A3 evidence.
- Latest Winner/authority recut is owner-approved at ~99/100 after recuts. Top-level design is effectively closed: `CYCLE_RESONANCE_v1` is preregistered as the first Alpha Discovery Lane but `NOT IMPLEMENTED`; the Right-Tail Atlas is Minimum-Viable-Atlas-first rather than full-history-first; future current-authority transitions obey the system-wide Destructive Authority Replacement Law; owner governance is six constitutions; and implementation forks choose one incumbent rather than parallel menus. None of this changes `PRE_SEAL_REAL_CIQ_ADMISSION` or `financial_alpha_evidence=0`.
- Sim-to-real alignment still finds a post-Clock operational tail, not a pre-Seal blocker. Existing primitives are reusable: broker submit/recovery/fill telemetry, orchestrator idempotent retry + reconciliation quarantine, signed replay protection, and deterministic event/book/replay. Initial PAPER execution incumbent is `MOC_CLOSE_AUCTION_V1 = market + cls`; missing authority is the thin binding/projection layer: one promoted policy/seal → one `live_rebalance_id`; PIT hash-bound `CIQSEC`↔broker instrument/account map; full broker lifecycle/open-orders → canonical live book; broker-first restart reconciliation + rebalance fencing + persistent `FREEZE_NEW_RISK`; and research-vs-broker implementation-shortfall attribution. Current rebalancer submission does not yet propagate close TIF even though the low-level broker adapter accepts `time_in_force`.

## Active bottleneck

```text
PRE-CLOCK GATE:
A. destructive v3 temporal authority                         [CLOSED LOCAL]
   cut_v3 + seal_v3 + clock_start_receipt_v1 + close-based evaluation
B. mandatory adversarial authority tests                    [CLOSED LOCAL]
C. real CIQ admission                                       [OPEN EXTERNAL DATA]
   rule100_targets + vertical_primitives + total_returns + decision_cut_v3
   (official_sofr.parquet already admitted)

→ SEAL CANDIDATE
→ fresh-process verify
→ CLOCK-START RECEIPT
```

Architecture is closed. Active P0 is now **real CIQ admission only**. No refactor, optimizer, performance work, historical-PIT rebuild or platform work may enter the first Clock-Start critical path.

## Immediate sequence

1. Export the frozen 109-company primary Security/Trading Item mapping; record the actual retrieval timestamp and raw hash.
2. Export completed same-cut daily primary-security total-return/price/volume history after the U.S. daily bar is complete; record the actual retrieval timestamp and raw hash.
3. Admit those two real CIQ objects through the existing fail-closed builder to produce `rule100_targets`, `vertical_primitives`, and `total_returns`; then build `decision_cut_v3`.
4. Write the real Seal Candidate → require fresh-process full-chain verification proof → write the immutable Clock-Start Receipt. Only the receipt starts the clock.
6. Immediately after Clock #1, freeze the laboratory/refresh measurements operating contract: same original 109 candidate entities; fresh fundamentals, security/status, market, benchmark/rate and staleness validation each weekly cut; do not rerun the growth screen.
7. After Clock #1, enforce one active **Alpha build** lane, not one running experiment. Release the preregistered `CYCLE_RESONANCE_v1` lane first: build only enough legitimate PIT history for honest discovery/contemporaneous controls → freeze the family/implementation/falsifiers/search budget → untouched PIT test where available → seal prospectively as soon as honest; expand historical risk-set/false-winner/replication coverage underneath the running tape. Weekly AOV tape + review/custody remain active.
8. Start external/operational lead-time clocks as soon as dependencies permit: borrow/locate feasibility from Clock #1; independent-replication data/identity/PIT preparation after the first Challenger seal; and independent Ops/Engineering starts the thin Alpaca PAPER Capitalization Vertical immediately after Clock #1 using current frozen AOV targets for operational learning only (`financial_alpha_evidence=0`).
9. Capitalization Vertical scope: initial execution incumbent=`MOC_CLOSE_AUCTION_V1`; exactly one promoted policy/seal → one `live_rebalance_id`; hash-bound `CIQSEC`↔broker instrument/account map; signed account-bound intent; full broker lifecycle/open-orders → canonical live authority; broker positions/cash/open-orders/recent execution reconciliation plus rebalance fencing before new risk on restart; implementation-shortfall/fees/timing/cash-drag bridge between research and actual broker P&L. LOC/close-window/actual-fill variants are challengers only; reuse existing execution substrate; do not build a second OMS.
10. Treat simple deterministic allocation as incumbent and optimizer as a portfolio-construction challenger that must prove incremental net utility. Bounded long/cash requires prospective edge evidence + genuinely independent replication + Capitalization Vertical authority; it does not wait for true L/S. PIT-borrow-backed L/S is a separate optional extension.
10. At major matured-evidence checkpoints classify the Alpha Program `CONTINUE`, `PIVOT`, or `STOP / HOLD`; absent alpha does not automatically authorize more architecture/data/optimizer/L-S complexity.
11. Code-quality debt is post-Seal only: central authority validators first, then `ciq_market.py` split, schema registry, structured errors, policy-comment cleanup as capacity permits. No pre-Seal cleanup refactor.

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

Before Clock #1: no score uplift, financial-alpha claim, historical Right-Tail Atlas build, AI/source pipeline implementation, provider programme, candidate-app PIT authority, AOV-2/event authority, optimizer/RL-first route, broker/order work, live capital, compatibility restoration, Episode-3 milestone, universal PIT/data/AI platform, distributed-compute/GPU/streaming platform, or pre-Seal code-quality refactor. `CYCLE_RESONANCE_v1` preregistration is docs/research-governance only. After Clock #1, the first Alpha lane and thin independently owned PAPER Capitalization Vertical are approved under their frozen constitutions; strategy live capital remains closed.
