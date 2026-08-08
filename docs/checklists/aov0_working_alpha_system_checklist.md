# AOV-0 Working Alpha System Checklist

Date: 2026-08-07
Purpose: current executable/evidence truth after Gate-A local freeze and Gate-B hard cut.

Legend: `[x]` locally implemented/proven; `[ ]` open; `OWNER OPEN` needs owner product judgment; `EVIDENCE OPEN` cannot be earned from code alone.

## A. Gate A — Episode-2 custody

- [x] Episode 1 remains release-ready at `ab258c3`.
- [x] Episode 2 later common MU/NVDA cut exists.
- [x] Adjacent chronology, decision-after-knowledge, capture/knowledge equality, distinct cut identity, and horizon-derived opening fail closed.
- [x] Exact Episode-2 runtime/test/data pathset committed at `39f7be3894623c095994066b8f0ea2895b968643`.
- [x] Exact candidate reconstructed from `git archive`.
- [x] Exact selected matrix collects `115` tests.
- [x] Exact archived candidate passes `115/115`.
- [x] Stale `142/142` receipt superseded.
- [ ] Push exact candidate SHA.
- [ ] Hosted Windows exact-head validation.
- [ ] Hosted Ubuntu exact-head validation.
- [ ] Independent cross-domain audit.
- [ ] Owner-authorized fast-forward/tag publication.
- [x] Episode 3 is not a product milestone.

## B. Gate B — zero compatibility hard cut

- [x] Root `alpha_app.py` removed from current runtime authority.
- [x] Root `launch_alpha.py` removed.
- [x] Root `portfolio_app.py` removed.
- [x] Root `launch_portfolio.py` removed.
- [x] `launch.py` → `dashboard.py` is the sole launcher/application path.
- [x] Historical Alpha source/build/test material moved to `docs/archive/legacy_runtime_source/`.
- [x] Historical Alpha release is governed by `release/gv-alpha0/RECEIPT.json`, not current-root rebuild compatibility.
- [x] Legacy book projection removed from `gv_portfolio_v0/book.py`.
- [x] Current dashboard has no legacy provider/optimizer/backtest/replay fallback authority.
- [x] Rule100 AOV adapter has no ticker/asset fallback.
- [x] ZERO-COMPAT scan reports zero for all seven acceptance counters, including archived/release executable-source imports.

## C. AOV executable P0 contract

### C1. Data/time/identity

- [x] Permanent active AOV identity = `CIQSEC:<Capital IQ Security ID>`; ticker/company `SP_ENTITY_ID`/legacy PERMNO/un-namespaced identity blocks.
- [x] PIT universe = date-local Rule100 eligible universe.
- [x] Required primitive time fields: `valid_at`, `known_at`, `computed_at`, `model_available_at`.
- [x] Total-return matrix is sole P&L authority.
- [x] Corporate actions are reconciliation-only, never a second P&L path.
- [x] Missing/non-finite/identity-mismatched primitives fail closed.
- [x] Economic cash is distinct from engine residual cash and future broker cash.

### C2. State mathematics

- [x] `Q` explicit primitive.
- [x] `M` deterministic fast/slow trend state.
- [x] `F_proxy = robust_z(sign(total_return)*min(abs(total_return)/realized_vol,3)*dollar_volume/adv20)`.
- [x] `C_proxy = EWMA20(abs(F_proxy))`; no second ADV division.
- [x] `L` bounded to `[0,1]`.
- [x] `R` explicit regime state.
- [x] `U` bounded uncertainty state.
- [x] Source, formula, contract, and cube hashes are retained.

### C3. Rule100 / Parent / Child

- [x] Parent reuses Rule100 risky gross budget, decision schedule, cap, and residual-cash semantics.
- [x] Dynamic components disabled reproduce Rule100 within frozen tolerance.
- [x] Single-name cap frozen.
- [x] One V0 engineering configuration frozen; no optimization/calibration.
- [x] Child differs by one frozen reversal-insurance mutation.
- [x] Child cannot raise asset exposure above Parent and can only return risk to cash.

### C4. Insurance

- [x] Reversal Hazard classified as bounded risk insurance, not standalone alpha.
- [x] Primary safety endpoint = Expected Shortfall / CVaR.
- [x] Insurance materiality floor ratio = `0.05`.
- [x] Annual insurance-premium ceiling = `0.0015`.
- [x] Production `DEFAULT_CONTRACT` freezes both V0 values; changing either creates a new contract/model family.
- [x] Prospective seal and deterministic review classification use the exact frozen V0 budget; no result-driven calibration in place.

### C5. Economic cash

- [x] Existing owner mandate controls: official SOFR minus 25 bp.
- [x] ACT/360.
- [x] No zero floor.
- [x] Rate usable only after official publication.
- [x] Missing official SOFR blocks; no proxy substitution.
- [x] Cash return constructed in `research/aov0/cash.py`.

### C6. Sleeve / inference

- [x] Execution lag = one bar.
- [x] Attempt frequency = weekly.
- [x] Fixed horizon = 30 calendar days.
- [x] Subsequent attempts are separate experiment identities, not overwrites.
- [x] Primary inference endpoint = paired Child-minus-Parent net return.
- [x] Weekly dependence-aware HAC/block policy frozen for V0 engineering evidence.

## D. Research spine hardening

- [x] Uses `core.engine.run_simulation(..., strict_missing_returns=True)`.
- [x] Frame identity hashes actual content.
- [x] Non-finite/NaN costs are invalid.
- [x] Benchmark policy is closed/named, not a positional list.
- [x] Mandatory benchmarks: implicit cash, PIT equal-weight eligible universe, economic cash.
- [x] Headline benchmark is explicitly named and list/dict order independent.
- [x] PIT equal-weight changes only on the strategy decision schedule and forward-fills between decisions.
- [x] Active AOV Rule100/cube/seal path requires canonical `CIQSEC:` security identity. The historical Rule100 replay adapter remains PERMNO-specific audit/component code but is not active first-seal authority.
- [x] Evidence output uses immutable run directory plus hash-bound `evidence_manifest.json`.

## E. Vertical cube / DAG / model mechanics

- [x] Minimal AOV-only cube implemented; no universal data platform.
- [x] Source/formula/contract/cube identity hashes implemented.
- [x] Deterministic synthetic fixtures implemented.
- [x] Deterministic Parent implemented.
- [x] One frozen Child mutation manifest implemented.
- [x] Hash DAG implemented.
- [x] Mutation-only change reuses Rule100 and Parent cache nodes while recomputing Child.
- [x] Cache hit/miss counts and node hashes retained.
- [x] Five-arm experiment machinery implemented under one engine/cost/return/calendar contract.
- [ ] `EVIDENCE OPEN` Admitted real A1 AOV historical result; no current permanent-ID Rule100 package is admitted yet.

## F. First real five-arm prospective operation

- [x] Destructive v3 cut/seal/clock identity and hashing implemented; active runtime has no v2/open reader or writer.
- [x] `scripts/aov0_first_seal.py` fail-closes instead of substituting historical/synthetic inputs and produces a clock-false Seal Candidate only.
- [x] `decision_cut.json` active schema is `aov0_ciq_decision_cut_v3`; it hash-binds all four Parquet inputs, frozen CIQ contract hash, mechanically recomputed date-local CIQ-security universe hash, four required source receipts/retrieval times/raw hashes, `knowledge_cutoff`, `cut_built_at`, target date, `execution_calendar_id=NYSE_2026_CORE_CLOSE_1600_ET`, and the exact next eligible close `evaluation_start`.
- [x] First-seal/cut validation rejects input-byte drift, contract/universe drift, missing/invalid/future source receipts, NY Fed retrieval before 15:00 ET, same-day U.S. daily market retrieval before 16:00 ET, post-cut target/return history, future primitive knowledge/SOFR publication, target-date drift, weekend/non-session/wrong-close/legacy-09:30 evaluation, cut build before knowledge, evaluation<=cut, and actual seal write at/after evaluation start.
- [x] Seal v3 binds current target-vector hashes plus serialized target vectors, `evaluation_start`, return-interval policy, maturity from evaluation start + 30 calendar days, and `aov0_executable_byte_manifest_v1`; it cannot claim clock start.
- [x] Fresh child-process full-chain verification emits a bound immutable proof; only a separate `aov0_prospective_clock_start_receipt_v1` may set clock authority.
- [x] Owner insurance materiality/premium values supplied and frozen at `0.05 / 0.0015`.
- [x] `run_4.xlsx` is the single frozen 109-company universe + current-cut quarterly-fundamentals receipt, SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`; `run_2.xlsx` is historical evidence only and not an active cut dependency.
- [x] Local primary-security/market admission path implemented: unique `CIQSEC:` + Trading Item identity, explicit exclusion rather than fallback, factor coverage gate, 200-day market warmup, ADV20/realized-vol/SMA20/SMA200 technical state, product/AOV Rule100 v1 `0.35` max-weight path, current-only Rule100 target/return emission, atomic source/output receipts, same-day U.S. daily-bar retrieval at/after 16:00 ET, and future-timestamp rejection.
- [x] Direct NY Fed SOFR intake implemented with hard pre-network 15:00 ET gate; direct raw bytes + actual retrieval time + raw hash are required.
- [x] Decision-cut builder implemented and parsed by the real first-seal validator; it consumes only the four active source receipts and has no legacy screen-retrieval parameter; target-date Rule100/return/primitive asset sets must match and primitive `total_return` must equal the P&L return matrix; first-seal admission independently rechecks that equality.
- [x] Synthetic current-cut CIQ→SOFR→v3 decision-cut package passes Seal Candidate + fresh-process `FULL_CHAIN_REOPEN_VERIFIED` proof + separate immutable Clock-Start Receipt with `financial_alpha_evidence=0`.
- [x] Mandatory adversarial v3 gate passes: bound market byte flip, +1bp serialized target mutation, Security-ID/ticker mutation, SOFR substitution, same-process promotion denial, calendar/timing mutation, pre-evaluation return interval, early maturity, and pre-receipt/pre-evaluation/pre-maturity authority unavailability.
- [ ] Real Capital IQ Security/Trading Item IDs + same-cut primary-security daily total-return/price/volume bytes are admitted with actual retrieval timestamps; for the current U.S. same-day target the daily market export must be retrieved at/after 16:00 ET. No real 109-name master/market exports are currently present.
- [ ] `data/aov0/current/rule100_targets.parquet` admitted.
- [ ] `data/aov0/current/vertical_primitives.parquet` admitted.
- [ ] `data/aov0/current/total_returns.parquet` admitted.
- [x] `data/aov0/current/official_sofr.parquet` admitted directly from NY Fed after the real 15:00 ET gate.
- [ ] `data/aov0/current/decision_cut.json` admitted.
- [ ] First real same-cut five-arm v3 Seal Candidate written.
- [ ] Exact real seal verified in a fresh process and verification proof retained.
- [ ] Immutable real Clock-Start Receipt issued.
- [ ] Recurring weekly prospective attempts started.
- [x] `EVIDENCE OPEN` Alpha evidence remains `0` before mature outcome opening.

## G. Deterministic review core

- [x] Parent–Child gross/cost/net reconciliation.
- [x] Reconciliation tolerance enforced.
- [x] Accounting failure blocks review authority.
- [x] CVaR helped/hurt classification.
- [x] Cost-dominated classification.
- [x] Insufficient-evidence classification.
- [x] Review packet content hash / tamper rejection.
- [x] Non-finite/missing simulation evidence blocks.
- [x] Single episode cannot authorize structural mutation.
- [ ] Full score→target→executed-weight→P&L lineage artifact.
- [ ] Global redistribution fixture.
- [ ] Regime-transition fixture.
- [ ] Corporate-action / total-return reconciliation fixture.
- [ ] Cohort/regime aggregation packet.

## H. Failure ontology / bounded AI

- [ ] Complete deterministic B0 closed ontology after the first real ReviewPackets exist.
- [ ] Experiment/mutation-family search-debt ledger beyond V0 experiment identity.
- [ ] One schema-valid AI MutationManifest from a matured validated ReviewPacket.
- [ ] Deterministic compiler rejects changes outside approved grammar.
- [ ] AI cannot alter data authority, risk limits, costs, owner insurance budget, or hidden-OOS budget.

## I. Model portfolio direction

Not a prerequisite for first seal. As soon as the first evidence-backed mutation exists, establish the minimal structural roles:

- [ ] Safety Parent.
- [ ] Incumbent.
- [ ] Challenger.
- [ ] Negative Control.
- [ ] Additional Challengers / Sentinel only when real evidence creates the need.

## J. Evidence ladder

- [x] A0 mechanical substrate: local hash/DAG/evidence/seal/review machinery exists.
- [ ] `A1` admitted real exploratory AOV result.
- [ ] `A2` query-metered hidden OOS.
- [ ] `A3` matured prospective paper evidence.
- [ ] `A4` independent future replication.
- [ ] `A5` bounded live operational parity.

## K. Operational / Limited Live

- [ ] One paper broker only after replicated prospective evidence.
- [ ] Idempotent orders, partial fills, reconciliation, disconnect recovery, kill switch.
- [ ] Research/paper semantics remain identical.
- [ ] Live starts bounded, no leverage/shorting/derivatives.
- [x] Limited Live remains closed.

## L. Deferred source/event extensions

- [x] Candidate finance-app inventory retained at `docs/research/aov2_identification_candidate_source_pool.md`.
- [ ] AOV-2 event-state integration only after base organism starts producing real prospective evidence.
- [ ] Identification-readiness probe remains non-blocking.
- [ ] No candidate app becomes PIT truth from catalog presence or Connect success.

## Validation snapshot

- Gate-A exact `39f7be3`: `115/115 PASS`.
- AOV: `75/75 PASS` including current-cut CIQ Security/market admission + SOFR/v3 cut tooling + Seal Candidate/fresh-process proof/Clock-Start Receipt promotion + adversarial authority suite; prior v2 mechanics remain historical evidence only.
- Hardened research selected suite: `33/33 PASS`.
- Current dashboard/book/historical receipt: `33/33 PASS`.
- Hard-cut Episode-2 regression: `107/107 PASS`.
- Historical Alpha ship-runtime live checkout: `7/7 PASS`.
- ZERO-COMPAT: all seven counts `0`.
- Compile, YAML parse, `pip check`, `git diff --check`: PASS.

## Fastest critical path

```text
DATA: admit real CIQ Security/Trading Item mapping + completed post-close market bytes; direct New York Fed SOFR is already admitted
→ build real decision_cut_v3
→ FIRST REAL IMMUTABLE FIVE-ARM SEAL CANDIDATE
→ fresh-process verification proof
→ immutable Clock-Start Receipt
→ clock runs
→ finish review lineage/fixture closure
→ matured ReviewPacket
→ first bounded AI MutationManifest
→ model portfolio expansion
→ hidden OOS
→ prospective replication
→ limited-live consideration
```
