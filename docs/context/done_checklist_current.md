# Done Checklist — Current

Date: 2026-08-09
Active state: `STRATEGIC_DIRECTION_APPROVED_AND_LOCKED / MANDATORY_RECUTS_AUTHORIZED / CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`
Canonical score: `70/100`
Portfolio-alpha evidence: `0`

## Clock #1 completion — 2026-08-08

- [x] Final exact-primary-SPT market object written deterministically: `data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv`, 21,345 rows, zero duplicate-key conflicts, SHA-256 `897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48`.
- [x] Primary-master SHA-256 reverified exactly at `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`.
- [x] CIQ fail-closed admission completed: 99 canonical securities, 10 mechanical exclusions, 26 Rule100 sizing-eligible names, risky gross `1.0`; no alternate-listing backfill.
- [x] Real `rule100_targets.parquet`, `vertical_primitives.parquet`, `total_returns.parquet`, and `decision_cut.json` produced from admitted provider bytes plus official SOFR.
- [x] `decision_cut_v3`=`AOV0_CIQ_20260807_ad2faf0533cec19c`, SHA-256 `81926aa896485a4a646228920ae0769283f143328ff8fe1f6671929136cd9b80`.
- [x] Real Seal Candidate `c78088ace7819170cd0064154fba138da4b4f8183dbd4ec48c347a942985ba88` written clock-false and re-opened successfully.
- [x] Fresh-process full-chain verification `55ba4e2f3670d4fc01839bd22bb164cfd0755efb1ce47f3641b9ca88d61c344c` succeeded.
- [x] Immutable Clock-Start Receipt `eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78` issued; Clock #1 started `2026-08-08T19:48:52.440503Z`.
- [x] Current authority check: `prospective_clock_started=true`, `evaluation_started=false`, `outcome_open_authorized=false`, `financial_alpha_evidence=0`.
- [x] Restored repository `.venv` on Python 3.12; `pip check` PASS; AOV suite `75/75 PASS`.
- [ ] Repository-wide pytest phase-close gate is not green: nine unrelated/inherited collection errors remain (stale `views.page_registry` imports; missing `psycopg2`, `schedule`, `yaml`).

## Lane 1 prospective slice 1 — 2026-08-08

- [x] Weekly preflight fixes candidate membership to the original 109 entities and rejects membership drift.
- [x] Weekly preflight requires fresh post-prior-cut receipts for fundamentals, primary-security/status, completed market data, and SOFR; missing/stale/future source state fails closed.
- [x] Weekly preflight cannot rerun the growth screen, open outcomes, mutate Parent/Child, or create financial-alpha evidence.
- [x] `alpha_pit_data_api_v1` mechanical interface + deterministic fixtures implemented with `CIQSEC:` identity, availability timestamps, source/hash binding, and explicit coverage/missingness.
- [x] CONFIRMATORY and PROSPECTIVE Alpha PIT capability objects have no `outcomes` method; discovery outcomes are lazy/import-separated.
- [x] `CYCLE_RESONANCE_v1` provider-blind fixture consumer implemented; it binds the risk-set/observation/claim/expectation manifests and keeps `financial_alpha_evidence=0`.
- [x] Alpha-PIT + CRV1 focused matrix `19/19 PASS`; AOV regression `102/102 PASS`; ZERO-COMPAT contract test PASS asserting seven zero counters; selected modules compile PASS; Git whitespace PASS.
- [x] Concrete Alpha PIT producer boundaries implemented: CIQ structured adapter verifies current custody bytes/availability and SEC claims adapter has no generic-web fallback; unlanded fields/sources remain explicit missingness.
- [x] Current real CIQ structured-custody diagnostic completed mechanically: 109 identities; SMA200 `104/109`; gross-margin/CFO `109/109 MISSING_SOURCE`; expectations `981/981 MISSING_SOURCE`; SEC claims source unlanded; `financial_alpha_evidence=0`.
- [x] CRV1 risk-set admission hardened: AOV growth-screen 109 forbidden; future `CRV1_US_PRIMARY_COMMON_V1` source must bind the frozen eligibility contract/hash, no growth/current-survivor/future-membership filter, row-level eligibility proofs, and an independent identity receipt.
- [x] CRV1 implementation-manifest freeze gate implemented with no scientific defaults, explicit search-budget custody, code-byte binding and tamper verification.
- [ ] First recurring post-Clock weekly provider refresh / next v3 Seal Candidate; preflight mechanics do not substitute for fresh provider bytes.
- [ ] Independent non-growth `CRV1_US_PRIMARY_COMMON_V1` risk-set capture plus required expectation/SEC source surfaces; current AOV 109 cannot substitute.
- [ ] Clock/claim/resonance/model/runner mechanics and frozen empirical CRV1 candidate from legitimate real PIT data.
- [ ] Matured, reconciled, validated ReviewPacket; no real outcome-informed MutationManifest before this gate.

## Closed locally

- [x] Published prior authority remains `9af5259`; untouched this round.
- [x] `launch.py` → `dashboard.py` is the sole current root product application.
- [x] Episode 1 remains banked at `ab258c3`.
- [x] Episode 2 immutable local candidate exists at `39f7be3`.
- [x] Episode 2 exact archived selected matrix passes `115/115`.
- [x] Stale `142/142` receipt superseded.
- [x] AOV hard-cut/mechanical executable is locally committed through `dca69fc`.
- [x] Root duplicate Alpha/Portfolio app launch surfaces removed.
- [x] Current-root legacy Alpha rebuild contract removed; historical release is receipt-only.
- [x] ZERO-COMPAT scan all seven counters zero, including no archived/release executable-source imports outside receipt integrity.
- [x] Hardened research runner/benchmarks/evidence/Rule100 semantics.
- [x] Minimal PIT AOV cube, destructively recut to canonical `CIQSEC:<Capital IQ Security ID>` active identity.
- [x] Active AOV rejects ticker, company `SP_ENTITY_ID`, legacy PERMNO, and dual-provider identity compatibility.
- [x] Rule100 control / deterministic Parent / one frozen Child.
- [x] Hash DAG and selective recomputation.
- [x] Five-arm evidence and baseline seal/reopen mechanics.
- [x] Final strategic re-audit=`PASS — STRATEGIC_DIRECTION_LOCKED`; broad architecture reopen=`NO`; mandatory recuts authorized. `CYCLE_RESONANCE_v1` retains its 252d primary horizon as the slow business-cycle family; one fast multi-week family is authorized for immediate preregistration. Parallel evidence qualification is allowed under default family WIP=`2`, initial ceiling=`3`; current portfolio/capital-policy authority remains singular. Destructive Authority Replacement and PIT/OOS/accounting/risk custody remain frozen. Current execution state remains `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`; `financial_alpha_evidence=0`.
- [x] Decision-cut/seal v2 custody fixes are locally closed: actual seal time separation, NYSE-session validation, exact executable-byte manifest, and fresh-process full-chain reopen.
- [x] First-seal path rejects post-cut target/return history, future primitive knowledge/SOFR publication, input byte drift, and target/execution timing inconsistency.
- [x] Seal binds current decision target-vector hashes for all five arms.
- [x] Economic cash constructor follows official SOFR−25bp owner mandate.
- [x] Deterministic Parent–Child review core.

## Closed — Winner / authority roadmap recut (docs/research governance only)

- [x] Fund mandate = sustainable net compounding through capital-weighted right-tail capture per unit capital-time, subject to false-winner/catastrophic-risk/frequency/liquidity/capacity/survival constraints; raw Precision@K is first-class but not the final utility.
- [x] `CYCLE_RESONANCE_v1` = first Alpha Discovery Lane, `PREREGISTERED / NOT IMPLEMENTED`; primary family outcome frozen to top-5% date-local cross-sectional total return over 252 trading days from the legitimate execution boundary.
- [x] Minimum-Viable-Atlas-first law: honest family-specific PIT discovery/controls → freeze → untouched test where available → prospective seal; deeper historical risk-set/false-winner/replication work continues underneath the running clock.
- [x] Alpha ontology separates Family / Component / Implementation / Trial / Portfolio Role / Capital Policy; evidence maturity, portfolio usefulness and capital authority are separate axes.
- [x] System-wide Destructive Authority Replacement Law: new current authority removes old active writer/reader/fallback/alias/dual-write/feature flag/compatibility adapter in the same slice; old artifacts remain historical evidence only.
- [x] Six owner constitutions: Fund Mandate, Research, Capital, Execution, Live-Risk, Operator; detailed implementation beneath them is delegated unless constitutional semantics change.
- [x] One-incumbent law: first family=`CYCLE_RESONANCE_v1`; narrow family-demanded source pipeline; simple allocation incumbent; Alpaca PAPER; `MOC_CLOSE_AUCTION_V1`; alternatives are challengers only.
- [x] Research toolkit includes right-tail rare-event/ranking/calibration, hazard/survival timing, dependence/effective-episode counts, search-integrity diagnostics, base-rate/pre-mortem/mosaic analysis, Alpha Redundancy Matrix, robust fractional-Kelly sensitivity, wrong-winner stress, Research Option Value, AI role firewalls, reconstruction coverage, and Alpha Half-Life.
- [x] Right-tail forensics are discovery-only and episode-based: enumerate all qualifying episodes inside legitimately covered history under the frozen label; retain true-right-tail, false-winner, missed-right-tail, and matched ordinary/left-tail contrasts; final confirmation returns to the full eligible risk set/base rates.
- [x] Incumbent winner-blindness audit is diagnostic only: test whether universe/Rule100/Parent/Child/caps/missingness/exit logic would have found and held historical winners in time, but do not tune Parent/Child or award financial-alpha evidence from survivor inspection.
- [x] Winner capture is decomposed into discovery/entry, continuation/hold, and exit/falsifier alpha; a successful entry implementation does not automatically own hold/exit skill, and unrealized P&L is not an alpha input.
- [x] No historical Atlas, SEC/text/AI pipeline, provider acquisition, or broker implementation starts before Clock #1; preregistration creates no financial-alpha evidence.

## Closed — Final strategic direction lock / mandatory recuts (docs/research governance only)

- [x] Meeting verdict=`PASS — STRATEGIC_DIRECTION_LOCKED`; final record=`docs/architecture/aov_strategic_direction_lock_20260809.md`; no further broad architecture cycle required.
- [x] `PARALLEL_EVIDENCE_QUALIFICATION=YES`; `SINGLE_CURRENT_CAPITAL_POLICY_AUTHORITY=YES`.
- [x] CRV1 252d primary outcome remains unchanged; separate fast multi-week Alpha clock authorized for preregistration now.
- [x] Initial active family WIP default=`2`, ceiling=`3` until explicit ownership/search-budget/risk-capacity review.
- [x] PAPER-0 implementation authorized behind minimum `ExecutionIntentV1` / `market+cls` / broker canonical state / restart / fencing / `FREEZE_NEW_RISK` / session-close gates; strategy live capital remains closed.
- [x] Replication-readiness entitlement/identity/PIT/license quarantine starts now; replication outcomes stay inaccessible to research.
- [x] A1/A2 is hard-blocked until one historical CIQ filing-vintage semantic wins destructively and current-vs-historical AOV semantics pass same-input parity.
- [x] No generic data/agent/model/event platform, second OMS, optimizer programme, L2/L3 acquisition or broad UI response is authorized by these recuts.

## Closed — Velocity / AI / Market Transition roadmap recut (historical docs/research governance)

- [x] CEO / Quant / PM / Risk / Architecture / Engineering council = `6/6 APPROVE_WITH_MODIFICATIONS`; canonical record=`docs/architecture/aov_velocity_council_20260808.md`.
- [x] Historical velocity recut replaced one global build queue with domain-scoped WIP. Final 2026-08-09 lock supersedes the earlier single-family cap: one narrow Alpha PIT incumbent remains, but multiple independently owned family clocks may qualify evidence in parallel within default WIP=`2` / ceiling=`3`; current capital-policy authority stays singular.
- [x] Frozen deterministic join gates: Clock → contract/visibility freeze → lane-local fixture proof → real PIT integration → immutable seal → matured deterministic ReviewPacket → replicated/capturable owner-risk promotion.
- [x] `alpha_pit_data_api_v1` and `CYCLE_RESONANCE_v1` may implement concurrently after Clock #1 against their frozen contract; CRV1 fixtures prove mechanics only and never PIT/OOS/prospective evidence.
- [x] Added `AI Research Pipeline v0`: `AIInvocationReceipt`, role/visibility firewall, non-authoritative drafts, Trial/Search accounting, hostile-source boundary, one-incumbent tooling policy, and external-repo quarantine. Post-Clock fixture/source-claim engineering may start with independent ownership; **real outcome-informed mutation still requires a matured reconciled ReviewPacket**.
- [x] Added `MARKET_TRANSITION_ALPHA_v1` as a separate forecast family and `ENTRY_TIMING_COMPONENT_v1` as a separate Alpha Component. Final lock keeps Market Transition discovery-only by default, but it may compete for an active family WIP slot through explicit local family admission; CRV1 seal is no longer a constitutional prerequisite.
- [x] Added `RESONANCE_LEVERAGE_POLICY_v1` as downstream Capital Policy, not Core Alpha. Market de-risk is distinct from operational kill; `not long != short`; desired/allowable/feasible/actual capital remain distinct; leverage/short/options authority stays disabled.
- [x] External repositories remain references/future bounded consumers only; no external repo code, dependency, AI SDK, second runner, second OMS, universal data layer or universal agent platform was introduced.
- [x] Pre-Clock path was unchanged by the velocity recut and is now closed: real CIQ custody/admission → `decision_cut_v3` → Seal Candidate → fresh-process verification → Clock-Start Receipt. No new pre-Seal gate was introduced.

## Closed — Owner A1→A2 second-critical-lane recut (docs/research governance)

- [x] Historical owner execution review=`9.77/10` with recut=`A1_A2_SECOND_CRITICAL_LANE`; superseded as current finality by the 2026-08-09 `PASS — STRATEGIC_DIRECTION_LOCKED` decision while retained as audit history.
- [x] Programme objective frozen to `EVIDENCE_VELOCITY × ECONOMIC_RELEVANCE`, not architecture completeness.
- [x] Lane 1 remains Future Truth: weekly prospective tape + Alpha PIT/CRV1 + matured ReviewPacket→bounded mutation + prospective Challenger/replication.
- [x] Lane 2 is first-class Compressed Learning: legitimate historical PIT CIQ → exact frozen-AOV replay → A1 → freeze immutable A2 contract → untouched/query-metered historical PIT OOS → A2 → incumbent loss/missed-winner diagnosis.
- [x] Lane 2 cannot open Clock #1 outcomes, tune Parent/Child between A1 and A2, or relabel current-screen-conditioned/PIT-insufficient history as A1/A2.
- [x] A2 may inform `CONTINUE / PIVOT / HOLD`, but once used to design a challenger it is not untouched evidence for that challenger; frozen CRV1 is not rescued in place.
- [x] Destructive shipping is explicitly aimed at obsolete active readers/writers/fallbacks/aliases/dual-writes/old-authority feature flags/compatibility adapters; immutable receipts, PIT timing, prospective seals, Trial/Search custody, exact accounting and hidden-OOS discipline remain protected.
- [x] Unrelated inherited full-repository failures remain phase-close blockers only; they do not automatically serialize an owned deterministic Alpha/Lane-2 slice whose scoped gates pass.
- [x] Broad second-family/AI/data/provider/UI/options/leverage/universal-Atlas/optimizer/external-strategy/execution-platform work stays suppressed until evidence makes it the nearest economic blocker.

## Open — external Episode-2 custody

- [ ] Push exact `39f7be3` candidate.
- [ ] Hosted Windows exact-head proof.
- [ ] Hosted Ubuntu exact-head proof.
- [ ] Independent cross-domain audit.
- [ ] Owner-authorized FF/tag publication if sought.

These are external and were explicitly outside this local authorization.

## Closed — insurance V0 owner decision

- [x] Insurance materiality floor ratio = `0.05`.
- [x] Annual insurance-premium ceiling = `0.0015`.

These values are frozen for AOV-0 V0. Changing either creates a new contract/model family; subsequent results do not calibrate them in place.

## Closed — active equity authority recut

- [x] WRDS authentication is not treated as the blocker; the available account lacks CRSP entitlement.
- [x] Owner explicitly authorized Path B: S&P Capital IQ Pro becomes the single active AOV equity source family.
- [x] `run_4.xlsx` is the single frozen 109-company universe + current-cut company-fundamental source, SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`; 1,203 absolute-quarter rows and 109 current factor-state rows are materialized locally with explicit admission-time PIT limitation and temporary company identity. Its receipt carries both `COMPANY_UNIVERSE` and `QUARTERLY_FUNDAMENTALS` authority roles.
- [x] `run_2.xlsx` is retired from active admission; its historical receipt is preserved but no retrieval time or source role is required by the current cut.
- [x] Canonical Rule100 V1.1 `factor_positive_count` is derived locally from the existing factor contracts; 56 states are complete, 52 partial, and one has no absolute-quarter history.
- [x] Historical/mechanical v2 baseline exists and is tested: `aov0_ciq_decision_cut_v2` + `NYSE_2026_CORE_OPEN_0930_ET`. BIG CHANGE re-audit explicitly demotes v2 from future execution authority; v3 is now the only active target contract.
- [x] Bounded CIQ primary-security/market admission builder implemented: unique `CIQSEC:` identity only; ambiguous/missing mappings, cross-entity collisions, `<3` factor coverage, insufficient 200-day market history, and invalid target state are excluded without compatibility fallback.
- [x] Current-cut law implemented: historical market rows warm technical/AOV state only; the admission builder emits one current Rule100 v1 target row and one matching current total-return row because `run_4` does not prove historical PIT factors.
- [x] Current Rule100 v1 market law is mechanically reused on the product/AOV `0.35` max-weight path; ADV20, realized volatility, SMA20/SMA200 trend, Q/L/R/U primitives, and source receipts are deterministic and tested.
- [x] Same-day U.S. daily market admission rejects retrieval before 16:00 America/New_York and rejects source retrieval timestamps later than the system-stamped build time; the decision-cut builder independently rechecks the completed-bar rule.
- [x] Direct New York Fed SOFR intake is hard-gated before network access at 15:00 America/New_York and hash-binds raw bytes; real admission succeeded at `2026-08-07T19:00:08.894288Z`, raw SHA-256 `445ca1ae93a7ae904681716d8e37088fab905ae4f74f32fc2619a459918d54cc`, output SHA-256 `ed75219416a524f17cb3e29b9e4fadff2dcfa1d12a8368d752007aac779c4e5e`.
- [x] Decision-cut builder binds exact current inputs and the four active source receipts, has no `run_2`/screen timestamp parameter, requires target-date Rule100/return/primitive asset-set equality and primitive-vs-P&L total-return equality; the actual first-seal entrypoint independently enforces the same return reconciliation.
- [x] Synthetic current-cut CIQ → SOFR → v3 decision cut reaches clock-false Seal Candidate → fresh-process `FULL_CHAIN_REOPEN_VERIFIED` proof → separate immutable Clock-Start Receipt; this remains mechanical proof only and `financial_alpha_evidence=0`.
- [x] CIQ provider environment/authentication capability proved: installed S&P Capital IQ Pro Office add-in loads; Office security session can be imported without exposing token contents; modern Genix ProductQuery transport returns HTTP 200 with the provider envelope.
- [x] Current market field semantics proved through supported `SPGTable`: exact-date `SP_TOTAL_RETURN`, `SP_PRICE_CLOSE`, and `SP_VOLUME` all return real provider values. Probe entity `4094286` on `2024-06-28` returned `-0.362932`, `123.54`, and `315516740`, respectively.
- [x] Historical as-of fundamentals capability proved through `SPG(..., as_of_date, ...)`; this is explicitly banked post-Clock capability and is not historical Rule100 authority for the first seal.
- [x] Supported Identifier Lookup + scalar SPG identity semantics proved: primary `SPT344984472` and alternate `SPT364472819` for `COE` share `SP_CIQ_ID=IQ337968870` while `SP_TRADING_ITEM_ID` differs, proving security-level vs listing-level identity. Direct company-key `SPGTable` returns the primary pair without 109 UI traversals.
- [x] Real 109-name primary Security/Trading Item raw master captured at `data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv`, retrieval `2026-08-08T16:23:22.0736860Z`, SHA-256 `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4`; 109/109 required pairs present, provider security IDs unique, trading IDs unique, ticker/exchange match frozen universe. Raw custody only; admission remains open.
- [x] Bulk market chunk boundary characterized: one fresh Office process per atomic part; 5/6/7 weekdays stable for 109 names × 3 fields, 8/10 weekdays fail at the bounded window. Exact-primary-SPT 6-day data equals company-primary data excluding retrieval timestamp, so SPT-keyed 7-day chunks are the incumbent.
- [x] Existing market raw custody includes nine earlier 5-day parts plus validated exact-SPT target-week `data/aov0/raw/ciq_market_parts_spt_7d_test_20260808/part_033_20260730_20260807.csv`, SHA-256 `81779d8ed04b80a5b79298821f9ff5d89c96abf025e8bb06d9a67f864cd744aa`.
- [x] Legacy/rejected acquisition paths classified: embedded SNLQuery/synthetic-provider execution hangs; `SNLPrice` compatibility market history stalled and was cancelled; direct raw Genix `SPGTable` metric normalization is unnecessary; widening beyond the proven 7-day Office chunk is not the incumbent; ticker fallback remains forbidden.
- [x] Detailed acquisition findings frozen in `docs/context/ciq_provider_acquisition_findings_20260808.md` so failed approaches and solved identity work are not retried as incumbents.

## Closed — admitted current first-seal inputs

- [x] Frozen-universe primary Security ID / Trading Item ID master admitted after exact SHA-256 verification.
- [x] Exact-primary-SPT market history combined, conflict-checked, hash-bound, and admitted without alternate-listing backfill.
- [x] `data/aov0/current/rule100_targets.parquet`.
- [x] `data/aov0/current/vertical_primitives.parquet`.
- [x] `data/aov0/current/total_returns.parquet`.
- [x] `data/aov0/current/official_sofr.parquet` admitted directly from NY Fed after the 15:00 ET gate.
- [x] `data/aov0/current/decision_cut.json` using `aov0_ciq_decision_cut_v3`.

## Closed — pre-seal custody fixes from re-audit

- [x] Actual prospective `sealed_at` is system-stamped at the real seal write, distinct from decision-cut `cut_built_at`, hash-bound, and mechanically required to be strictly before the v3 `evaluation_start` close boundary.
- [x] v2 proved exact NYSE-session/open validation mechanically; these tests remain historical baseline evidence. v3 must replace active calendar authority with exact 16:00 America/New_York Core Close under `NYSE_2026_CORE_CLOSE_1600_ET` and retain equivalent negative coverage.
- [x] Fresh-process reopen walks the full cryptographic closure: exact executable bytes → seal → decision cut → four Parquets → experiment manifest → run evidence manifests/files → serialized target vectors/hashes, and returns `FULL_CHAIN_REOPEN_VERIFIED` only on exact closure.
- [x] `aov0_executable_byte_manifest_v1` hashes the exact implementation files loaded/required plus the Python interpreter bytes; dirty-worktree code is therefore reproducibly identified without pretending Git HEAD alone is sufficient.
- [x] Approved roadmap/change spec is resident at `docs/architecture/aov_endgame_generalization_spec_current.md`; runtime implementation now satisfies its four required pre-seal custody repairs locally.

## Closed — destructive v3 temporal authority before first real clock

- [x] Active authority schema = `aov0_ciq_decision_cut_v3`; active v2 cut execution compatibility removed.
- [x] Active seal schema = `aov0_prospective_seal_v3`; v2 seal remains historical/mechanical evidence only.
- [x] Clock authority schema = `aov0_prospective_clock_start_receipt_v1`.
- [x] `execution_calendar_id = NYSE_2026_CORE_CLOSE_1600_ET` under current daily-return authority.
- [x] Seal write produces immutable **Seal Candidate** only and returns `prospective_clock_started=false`.
- [x] Successful fresh-process full-chain verification produces a distinct immutable verification proof; only then can a separate immutable Clock-Start Receipt bind the seal/verifier identity + verification time.
- [x] Official promotion path cannot claim prospective clock start unless that receipt exists.
- [x] Every admitted attributed return interval must have left endpoint at/after next-eligible-close evaluation start.
- [x] `outcome_open_not_before = evaluation_start + 30 calendar days`, not `sealed_at + 30 days`.

## Closed — mandatory pre-Seal adversarial v3 tests

- [x] bound market artifact one-byte mutation → full-chain verification BLOCK.
- [x] target-vector +1bp/serialized-byte mutation → BLOCK.
- [x] canonical Security ID mutation / ticker injection → BLOCK.
- [x] official SOFR−25bp replaced by proxy/ETF authority → BLOCK.
- [x] same-process-only verification cannot issue Clock-Start Receipt.
- [x] weekend/non-session/wrong-close/legacy-09:30/evaluation<=cut timing → BLOCK.
- [x] attributed return interval begins before evaluation start → BLOCK.
- [x] maturity < evaluation_start + 30 calendar days → BLOCK even when a new self-consistent seal hash is supplied.
- [x] before Clock-Start Receipt / before evaluation / before maturity, future outcome authority remains unavailable.

Current AOV v3 suite is `75/75 PASS`; ZERO-COMPAT remains seven zeros.

## Active — first real prospective evidence

- [x] First real five-arm same-cut Seal Candidate from admitted CIQ bytes.
- [x] Fresh-process full-closure real-seal verification.
- [x] Immutable Clock-Start Receipt issued.
- [x] Prospective clock starts only from the receipt.
- [ ] Recurring weekly attempts.
- [ ] **P0 A1 BLOCKER:** freeze exactly one legitimate CIQ historical fundamental vintage semantic. Current replay requires `FilingVer=Original` while capture scripts request/emit `Current/Restated`; no A1/A2 claim until the contradiction is removed destructively.
- [ ] **P0 A1 PARITY GATE:** same provider snapshot through current AOV and historical AOV semantics reconciles identity, ADV20, realized vol, SMA/trend, Q/U, technical state, sizing eligibility and Rule100 weights, except explicitly declared activation-lag differences.
- [ ] `A1` exact frozen-AOV historical PIT replay admitted only after vintage + parity gates, or explicitly downgraded to diagnostic scope.
- [ ] A2 split/query budget/metrics/executable hashes frozen before hidden historical outcome inspection.
- [ ] `A2` query-metered untouched historical PIT OOS evaluated once under the frozen contract and retained append-only.
- [ ] `A3` matured prospective evidence; unavailable before `2026-09-09T20:00:00Z`.

## Open — review closure while clock runs

- [ ] score→target→executed-weight→P&L lineage artifact.
- [ ] global-redistribution fixture.
- [ ] regime-transition fixture.
- [ ] corporate-action/total-return reconciliation fixture.
- [ ] cohort/regime packet and complete deterministic B0 ontology.

## Open — post-Seal WIP-capped execution

Always-on / active:
- [ ] prospective weekly AOV tape.
- [ ] **LANE 2 HISTORICAL COMPRESSION:** historical PIT CIQ reconstruction → exact frozen-AOV replay → A1 → freeze A2 contract → query-metered untouched PIT A2 → Parent/Child economics + incumbent loss/missed-winner diagnosis. Lane 2 may not open Clock #1 outcomes or tune Parent/Child between A1 and A2.
- [ ] weekly fresh-data contract: same frozen 109 candidate entities; fresh fundamentals + identity/status + completed market + benchmark/rate + staleness validation; no weekly rerun of the growth screen.
- [ ] deterministic review + custody/replay closure.
- [ ] `ALPHA_PIT_PIPELINE` WIP slot: one narrow `alpha_pit_data_api_v1` incumbent; only first-family-required fields/sources; no generic provider platform.
- [ ] `ALPHA_FAMILY_BUILD` WIP: default `2` independent confirmatory/prediction family clocks, initial ceiling `3`; first slow clock=`CYCLE_RESONANCE_v1` with unchanged 252d primary outcome, plus one fast multi-week family to preregister. Each family has isolated owner/writer, search budget, Prediction/Trial Ledger scope and artifact namespace.
- [ ] Alpha PIT + CRV1 may build concurrently against the frozen interface; deterministic API fixtures are allowed for engineering but have zero PIT/OOS/prospective evidence authority until real integration.
- [ ] `AI_RESEARCH_TOOLING` WIP slot may run only with independent ownership and without slowing the critical PIT+CRV1 pair; first scope=`AIInvocationReceipt` + role firewall + source-claim/discovery schema + ReviewPacket/Mutation fixture mechanics.
- [ ] registered discovery incubators may run with explicit Trial/Search budgets and zero automatic confirmatory/capital authority; an incubator enters confirmatory WIP only through explicit family admission. Leading fast-family candidates=`SECTOR_ROTATION_ALPHA_v1` / `VOL_SQUEEZE_BREAKOUT_v1`.
- [ ] Minimum Viable Atlas first: enough legitimate PIT history for honest discovery/contemporaneous controls → freeze implementation → untouched PIT test where available → seal prospectively as soon as honest; deepen full risk-set/false-winner/replication coverage underneath the running clock.
- [ ] once a Challenger is sealed, it leaves Alpha-family build WIP and continues as an immutable running tape while the family slot may move only to the next evidence-justified preregistered family/component; Trial Ledger retains all attempts/failures.

Async external lead-time:
- [ ] borrow/locate entitlement feasibility + forward-capture plan from Clock #1; true short authority remains closed.
- [ ] **START NOW:** quarantined independent-replication entitlement / permanent identity / PIT-vintage / retention-license / acquisition-latency preparation; no replication outcomes exposed to research.

Independent ownership required after Clock #1:
- [ ] **PAPER-0 starts immediately:** current frozen AOV targets may exercise the smallest lineage-correct broker path for operational learning only; `financial_alpha_evidence=0`.
- [ ] Exactly one promoted policy/seal feeds exactly one `live_rebalance_id`; research arms/cohorts/Challenger tapes never become broker sleeves automatically.
- [ ] PIT hash-bound `CIQSEC:<id>` ↔ broker instrument/account execution map with fail-closed ambiguity/staleness.
- [ ] Initial PAPER execution incumbent=`MOC_CLOSE_AUCTION_V1 = market + cls`; rebalancer propagates/verifies the incumbent policy/TIF rather than silently using ordinary default submission. LOC/close-window/actual-fill variants are challengers only.
- [ ] PAPER-0 canonical lifecycle must cover accepted/open/partial/fill/cancel/reject plus exact open-order residual state; unsupported rare states fail closed. Trade bust/correct and fuller replacement/correction normalization may close in PAPER-1 before bounded capital.
- [ ] Live open-order / partial-fill residual state is included in the live-state commitment; historical exclusion of `partial_fill_residuals` is not reused as live authority.
- [ ] Restart begins with `FREEZE_NEW_RISK=true`, then broker account + positions + cash/equity + open orders + recent executions/corrections reconcile against local rebalance/order/event state; only clean reconciliation may clear freeze.
- [ ] Account-level `rebalance_epoch` / fencing token prevents stale or zombie workers from creating new-risk intents after authority changes.
- [ ] Research CIQ-return P&L and broker/account P&L remain separate ledgers bridged by implementation shortfall, fees, timing, unfilled quantity, and cash drag.
- [ ] Production signed intent/client-order identity binds account + `live_rebalance_id` + promoted policy/seal + execution-map hash + instrument + side/qty + execution policy/TIF + `rebalance_epoch`; legacy day+symbol+side+qty identity is removed from current authority when the new identity lands.
- [ ] First PAPER order either resolves the actual session close (including early closes) or is explicitly restricted to a verified regular full-session day and fails closed otherwise; fixed 16:00 is not perpetual PAPER/LIVE authority.
- [ ] Reuse existing broker submit/recovery, reconciliation quarantine, signed replay, and deterministic event/book/replay primitives; no second OMS.

Queued until nearest blocker or independent ownership:
- [ ] global long/cash optimizer **challenger**; simple deterministic sizing remains incumbent and optimizer is not a capital prerequisite.
- [ ] long-side Parent-order IS / capacity.
- [ ] minimal OMS / long-cash shadow/live operations.
- [ ] code-quality CQ1: central `research/aov0/authority.py` validators (highest maintenance priority after Clock #1).
- [ ] CQ2: split `ciq_market.py` by identity/ingest/features/admission invariant boundaries.
- [ ] CQ3: typed status/schema registry; CQ4: structured authority error taxonomy; CQ5: move governance-history comments to decision/ADR docs.
- [ ] S2 exact-recompute runtime/package manifest hash before claiming complete environment-reproducible replay; shared abstractions follow the Rule of Two. Current/historical AOV duplication is now a real Rule-of-Two trigger for the smallest pure feature/policy kernel, but Clock #1 bytes are not rewritten in place.

## Open — post-Clock AI tooling before outcome maturity

- [ ] implement one `AIInvocationReceipt` format and deterministic authority/schema validator.
- [ ] implement one bounded discovery/source-claim AI schema against immutable source-bound packets or fixtures; exact model/prompt/procedure hash-bound.
- [ ] implement ReviewPacket→ReviewExplanationDraft/MutationManifestDraft fixture path; fixture results remain mechanical only.
- [ ] one AI/provider incumbent + one orchestration approach; no generic agent platform.

## Open — after matured ReviewPacket

- [ ] first **real outcome-informed** bounded AI `MutationManifestDraft` from a matured reconciled validated ReviewPacket.
- [ ] deterministic compile and development run.
- [ ] model portfolio: Safety Parent / Champion / 1–3 Challengers / Negative Control / Sentinel as evidence requires.
- [ ] Trial Ledger/search-family accounting retains all attempts/failures plus trial count, preregistered/actual search budget, feature/target/horizon variants, OOS/prospective failures and data/compute/research cost.
- [ ] hidden OOS where legitimate.
- [ ] first bounded long/cash capital gate = prospective capital-relevant edge + one genuinely independent replication + Capitalization Vertical authority (promotion/rebalance identity, execution map, close/fill contract, lifecycle/open-orders, restart reconciliation, dual-ledger bridge, kill controls) + owner/risk approval.
- [ ] true L/S is not a prerequisite for bounded long/cash.
- [ ] Full Long-Short Shadow B only after PIT borrow/locate authority; bounded L/S is a separate optional capital extension with its own independent replication.
- [ ] at each major matured evidence checkpoint, program decision is explicitly `CONTINUE`, `PIVOT`, or `STOP / HOLD` before authorizing material new engineering/data complexity.

## Claim boundary

- [x] Mechanical/test seals are not A1/A3 evidence.
- [x] Portfolio-alpha evidence remains `0`.
- [x] Limited Live remains closed.
- [x] Before Clock #1: no compatibility restoration, historical Right-Tail Atlas build, AI/source pipeline, second app/engine, provider breadth, AOV-2/event authority, optimizer/RL-first path, broker/order work, or live capital. `CYCLE_RESONANCE_v1` preregistration is docs/research-governance only. After Clock #1, the first Alpha lane and thin PAPER Capitalization Vertical are approved under their constitutions; optional micro-live requires explicit owner/risk authority and remains operational-only, not strategy promotion.
