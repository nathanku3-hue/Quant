# ALPHA-ORGANISM-VERTICAL-0 — Active Brief

Date: 2026-08-06
Branch: `codex/pit-source-authority-1`
Status: `MECHANICAL VERTICAL IMPLEMENTED LOCALLY; FIRST REAL SEAL BLOCKED; LIVE CLOSED`
Episode-2 local immutable candidate: `39f7be3894623c095994066b8f0ea2895b968643`
AOV local executable tip: `dca69fc72dd3192913aa921323ff48f68610a925`
Canonical product maturity: `70/100` (accepted operability/custody/replay only)
Portfolio-alpha evidence: `0`
Limited Live: `CLOSED; NOT AUTHORIZED`

## Product result

The sole active product milestone is the **first immutable real same-cut five-arm prospective seal**:

```text
admitted PIT vertical cube
→ Rule100 control
→ deterministic CFTD Parent
→ one frozen risk-reducing Child
→ PIT equal weight
→ economic cash
→ one immutable same-cut prospective seal
→ exact reopen
```

Architecture completion, test fixture seals, or historical mechanics do not start the prospective clock and do not earn financial-alpha evidence.

## Gate A — Episode-2 local predecessor

Local custody is complete:

- [x] exact Episode-2 runtime/test/data pathset committed at `39f7be3`;
- [x] exact `git archive` reconstruction performed;
- [x] exact selected matrix collects `115` tests;
- [x] exact archived bytes pass `115/115`;
- [x] stale `142/142` receipt identified and superseded.

External custody is deliberately still open:

- [ ] push exact candidate SHA;
- [ ] hosted Windows exact-head proof;
- [ ] hosted Ubuntu exact-head proof;
- [ ] independent cross-domain audit;
- [ ] owner-authorized fast-forward/tag publication.

Those external actions were not authorized in this round and do not reopen local Gate-B engineering.

## Gate B — hard cut + AOV vertical

Implemented locally:

- [x] four duplicate root app/launcher surfaces removed from current authority;
- [x] historical Alpha runtime/build code moved to `docs/archive/legacy_runtime_source/`;
- [x] historical Alpha release converted to receipt-integrity authority rather than current-root rebuild compatibility;
- [x] `dashboard.py` reduced to one canonical authority shell;
- [x] legacy book projection removed;
- [x] ZERO-COMPAT scan passes all six counters at zero;
- [x] five research-spine defects repaired without compatibility shims;
- [x] minimal `VERTICAL-CUBE-SLICE-V0` implemented;
- [x] deterministic Rule100 / Parent / one Child policy implemented;
- [x] hash-addressed DAG and selective recomputation implemented;
- [x] five-arm experiment/evidence machinery implemented;
- [x] immutable prospective-seal/reopen machinery implemented;
- [x] deterministic Parent–Child review core implemented;
- [x] official-SOFR economic cash construction implemented under existing owner authority;
- [x] local AOV suite passes `17/17`.

## Executable P0 contract

### Frozen

1. `F_proxy = robust_z(sign(total_return) × min(abs(total_return)/realized_vol,3) × dollar_volume/ADV20)`.
2. `C_proxy = EWMA20(abs(F_proxy))`; no second ADV division.
3. Permanent identity is `permno`; ticker/asset aliases are invalid on the AOV path.
4. Universe is the date-local Rule100 eligible universe.
5. PIT total-return matrix is the sole P&L authority; corporate actions are reconciliation-only.
6. Parent preserves Rule100 risky gross budget, cap, decision schedule, and residual-cash behavior; no forced full-investment softmax.
7. Rule100 degenerate equivalence tolerance is frozen in the executable contract.
8. One V0 engineering configuration is frozen; no result-driven calibration.
9. Child differs from Parent by one frozen reversal-insurance mutation and may only reduce risk/increase cash.
10. Execution uses one-bar lag; attempts are weekly; the experimental horizon is fixed at 30 calendar days.
11. Inference uses paired weekly Child-minus-Parent net-return evidence with overlap-aware weekly HAC/block structure.
12. Economic cash inherits the existing owner mandate: official SOFR minus 25 bp, ACT/360, no zero floor, usable only after official publication, no proxy substitution.
13. Insurance primary endpoint is Expected Shortfall / CVaR.

### Owner decision still open

The production contract deliberately leaves these `None`:

- [ ] insurance materiality floor ratio;
- [ ] annual insurance-premium ceiling.

Development tests may inject example values to prove mechanics, but those examples are not product authority.

## Research-spine hardening

Closed defects:

- [x] evidence/frame identity hashes actual content;
- [x] headline benchmark is explicitly named rather than dict/list-order dependent;
- [x] NaN/non-finite costs are invalid;
- [x] benchmark contract is named/closed and requires cash + PIT-EW + economic cash;
- [x] PIT-EW follows the same strategy decision/rebalance schedule;
- [x] Rule100 adapter requires permanent IDs, daily-portfolio semantics, and reconciled cash;
- [x] evidence run directories are immutable and manifest-hash-bound.

## First real prospective seal — blocked correctly

`python scripts/aov0_first_seal.py` currently returns:

```text
status = BLOCKED_OWNER_DECISION_AND_ADMITTED_INPUTS
prospective_clock_started = false
alpha_evidence = 0
```

Owner fields required:

- `insurance_materiality_floor_ratio`;
- `insurance_premium_ceiling_annual_return`.

Current admitted artifacts required:

- `data/aov0/current/rule100_targets.parquet`;
- `data/aov0/current/vertical_primitives.parquet`;
- `data/aov0/current/total_returns.parquet`;
- `data/aov0/current/official_sofr.parquet`;
- `data/aov0/current/decision_cut.json`.

No historical equal-weight replay, ticker-only artifact, zero-return cash, or provider substitute may fill these gaps.

## Deterministic review status

Implemented now:

- [x] Parent–Child gross/cost/net reconciliation with tolerance;
- [x] accounting failure blocks review authority;
- [x] deterministic statuses for helped, hurt, cost-dominated, insufficient evidence, accounting failure;
- [x] exact review-packet hash verification;
- [x] single episode has no structural mutation authority;
- [x] synthetic helped/hurt/cost/accounting/non-finite/tamper fixtures.

Still to close while the real clock runs:

- [ ] full score→target→executed-weight→P&L lineage packet;
- [ ] global-redistribution fixture;
- [ ] regime-transition fixture;
- [ ] corporate-action/total-return reconciliation fixture;
- [ ] deterministic cohort/regime packet and B0 ontology completion.

## North-star sequence

```text
owner insurance decision
+ admit five current AOV inputs
→ FIRST REAL IMMUTABLE FIVE-ARM SEAL
→ clock runs
→ finish deterministic review lineage/fixtures
→ matured ReviewPacket
→ one bounded AI MutationManifest
→ deterministic development run
→ model portfolio begins expanding
→ hidden OOS
→ prospective replication
→ limited-live consideration
```

Initial model-portfolio direction after the first matured review:

```text
Safety Parent
Champion
1–3 Challengers
Negative Control
Sentinel
```

Full promotion-state machinery, search-debt automation, hidden-OOS platform, AOV-2, provider breadth, and sentinel governance are not prerequisites for the first seal or first bounded AI development mutation.

## Forbidden scope

No Episode-3 product milestone; no universal PIT platform; no second engine/app; no compatibility restoration; no ticker fallback; no unrestricted generated Python; no optimizer/RL-first route; no broad provider acquisition; no AOV-2/event/pattern authority; no broker; no outcome opening; no alpha claim; no live capital.

## Validation snapshot

- Gate A exact commit `39f7be3`: `115/115` selected tests PASS from `git archive` bytes.
- Gate B hard-cut tree: ZERO-COMPAT all six counters `0`.
- AOV suite: `17/17` PASS.
- Hardened research suite: `33/33` PASS.
- Canonical dashboard/book/historical-receipt suite: `33/33` PASS.
- Hard-cut Episode-2 regression: `107/107` PASS.
- Historical Alpha ship-runtime substrate in live Git checkout: `7/7` PASS.
- Python compilation, YAML parse, `pip check`, and `git diff --check`: PASS.

Portfolio-alpha evidence remains exactly `0`.

## What Was Done

- Froze Episode-2 locally at exact `39f7be3894623c095994066b8f0ea2895b968643` and proved the exact archived-byte selected matrix `115/115`.
- Performed the destructive AOV hard cut: removed duplicate root app/launcher authority, legacy book projection, current-root Alpha rebuild compatibility, ticker/asset aliases, transitional authority fallbacks, mutable evidence-manifest bypass, and unnamed benchmark selection.
- Hardened the canonical research spine and implemented the minimal AOV cube, Rule100 control, deterministic Parent, one risk-reducing Child, hash DAG, five-arm experiment/seal machinery, and official-SOFR economic cash.
- Built the deterministic Parent–Child review core with reconciliation, CVaR helped/hurt, cost-dominated/insufficient/accounting statuses, packet hashing, and single-episode no-mutation authority.
- Preserved the owner boundary by leaving insurance materiality floor and annual premium ceiling unresolved in the production contract.
- Created local commits only; no push, hosted CI execution, publication, provider access, outcome opening, or live-capital action occurred.

## What Is Locked

- The next product milestone is the first **real immutable five-arm prospective seal**, not another architecture or repair phase.
- `launch.py` → `dashboard.py` is the sole current application and `core.engine.run_simulation` through the hardened `research/` runner is the sole simulation authority.
- Gate-A local candidate is `39f7be3`; Gate-B local executable lineage ends at `dca69fc` before documentation closure.
- Economic cash is official SOFR minus 25 bp, ACT/360, no zero floor, post-publication only, with no proxy substitution.
- Production insurance materiality floor and annual premium ceiling are owner-open and may not be silently chosen.
- Portfolio-alpha evidence remains `0`; the prospective clock has not started; Limited Live remains closed.

## What Is Next

- Owner freezes `insurance_materiality_floor_ratio` and `insurance_premium_ceiling_annual_return`.
- Admit the five current AOV artifacts: permanent-ID Rule100 targets, vertical primitives, PIT total returns, official SOFR, and decision-cut receipt.
- Run the first real immutable five-arm seal immediately and require exact reopen before starting the prospective clock.
- While the clock runs, finish score→target→executed-weight→P&L lineage and redistribution/regime/corporate-action review fixtures.
- After a matured validated ReviewPacket, allow one bounded AI MutationManifest and deterministic development run, then begin model-portfolio expansion.

## First Command

```text
E:\code\quant\tmp\gv25env\Scripts\python.exe scripts\aov0_first_seal.py
```
