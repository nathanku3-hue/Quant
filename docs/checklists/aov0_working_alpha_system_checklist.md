# AOV-0 Working Alpha System Checklist

Date: 2026-08-06
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
- [x] ZERO-COMPAT scan reports zero for all six acceptance counters.

## C. AOV executable P0 contract

### C1. Data/time/identity

- [x] Permanent identity = `permno`; missing permanent ID blocks.
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
- [ ] `OWNER OPEN` Insurance materiality floor ratio.
- [ ] `OWNER OPEN` Annual insurance-premium ceiling.
- [x] Production `DEFAULT_CONTRACT` leaves both owner values unresolved (`None`).
- [x] Prospective seal and deterministic review classification fail closed while owner values are unresolved.

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
- [x] Rule100 adapter requires `daily_portfolio`, permanent `permno`, exact duplicate handling, and cash reconciliation.
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

- [x] Prospective seal schema/identity/hashing implemented.
- [x] Seal exact-reopen and tamper tests implemented.
- [x] `scripts/aov0_first_seal.py` fail-closes instead of substituting historical/synthetic inputs.
- [ ] Owner insurance materiality/premium values supplied.
- [ ] `data/aov0/current/rule100_targets.parquet` admitted.
- [ ] `data/aov0/current/vertical_primitives.parquet` admitted.
- [ ] `data/aov0/current/total_returns.parquet` admitted.
- [ ] `data/aov0/current/official_sofr.parquet` admitted.
- [ ] `data/aov0/current/decision_cut.json` admitted.
- [ ] First real same-cut five-arm prospective seal written.
- [ ] Exact real seal reopened.
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

Not a prerequisite for first seal. After matured review evidence:

- [ ] Safety Parent.
- [ ] Champion.
- [ ] 1–3 Challengers.
- [ ] Negative Control.
- [ ] Sentinel.

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
- AOV: `17/17 PASS`.
- Hardened research: `33/33 PASS`.
- Current dashboard/book/historical receipt: `33/33 PASS`.
- Hard-cut Episode-2 regression: `107/107 PASS`.
- Historical Alpha ship-runtime live checkout: `7/7 PASS`.
- ZERO-COMPAT: all six counts `0`.
- Compile, YAML parse, `pip check`, `git diff --check`: PASS.

## Fastest critical path

```text
OWNER: freeze insurance materiality + premium ceiling
+ DATA: admit five current AOV artifacts
→ FIRST REAL IMMUTABLE FIVE-ARM SEAL
→ clock runs
→ finish review lineage/fixture closure
→ matured ReviewPacket
→ first bounded AI MutationManifest
→ model portfolio expansion
→ hidden OOS
→ prospective replication
→ limited-live consideration
```
