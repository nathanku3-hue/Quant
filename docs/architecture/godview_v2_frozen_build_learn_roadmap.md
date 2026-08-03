# Active Supersession Notice — 2026-08-03

The accepted historical slices and custody below remain immutable evidence. Active forward authority is now `docs/architecture/top_level_roadmap.md`, `docs/architecture/dashboard_all_capital_pit_contract.md`, and `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`. The next gate is `GV-DASHBOARD-ALL-CAPITAL-PIT-1`, executed layer first as one real read-only transaction: baseline bank → contracts → verified adapters → command-handler identity decision → ordered events → pure projector/read models → six-page Command Center. Selection, risk/preview authority, mutation, certification change, deletion, strategy expansion, and Live remain later or closed. Accepted score remains `62/100`; Limited Live remains closed.

---

# GodView v2 Corrected Build × Learn Roadmap

Status: `R0_BANKED; INDEPENDENT_AUDIT_PENDING`
Date: 2026-07-29
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`), release-proof tip `93e7a55`
Current shipped truth: score `39/100`, observed comparisons `0`, no alpha claim
Roadmap authority: branch tip containing this R0 repair, designated `ROADMAP_FREEZE_COMMIT`
Active brief selector: `docs/context/ACTIVE_BRIEF`

## 1. Corrected decision

The prior roadmap was a validated but unbanked candidate. It incorrectly treated a contract catalogue as the first product slice and retained highest-numeric-phase tooling as active authority.

R0 repairs that once, then the product sequence begins with the missing user capability: one complete multi-security portfolio operating loop.

```text
R0 ROADMAP-CUSTODY-REPAIR                  = INTERNAL / BANKED / AUDIT_PENDING
PRODUCT_SEQUENCE                           = SLICES_0_TO_6
EXECUTION_AUTHORIZED_AFTER_R0_AUDIT        = SLICES_0_TO_1
ACTIVE_PRODUCT_SLICE                       = GV-MICRO-PORTFOLIO-VERTICAL-0
NEXT_INTEGRITY_GATE                        = GV-DETERMINISTIC-REPLAY-0
OPEN_ENDED_ARCHITECTURE_DISCOVERY          = CLOSED
```

Binding sequence:

```text
R0 ROADMAP-CUSTODY-REPAIR
→ GV-MICRO-PORTFOLIO-VERTICAL-0
→ GV-DETERMINISTIC-REPLAY-0
→ GV-BOUNDED-PORTFOLIO-1
→ GV-PORTFOLIO-SCALE-1
→ GV-UNIVERSE-SCALE-1
→ GV-CHALLENGER-PROMOTION-1
→ GV-LIMITED-LIVE-1
```

## 2. Product law

The canonical product unit is:

```text
one declared PIT opportunity set
→ complete portfolio including classified cash, rejection, and abstention
→ prospective operation
→ deterministic accounting and replay
→ lifecycle-based review
```

GodView is not an optimizer-first research platform. It is a point-in-time portfolio operating system in which research earns bounded capital authority through prospective operation and replayable evidence.

## 3. R0 — Roadmap custody repair

R0 is not marketed, scored, or accepted as a product slice.

Required outcomes:

- explicitly supersede stale instructions that branch implementation from raw `93e7a55`;
- remove standalone `GV-CANON-RESET-0` from the product sequence;
- preserve released `gv_fs0_v1` unchanged;
- require a new `gv_portfolio_v0` namespace for portfolio work;
- replace highest-numeric-phase authority with `docs/context/ACTIVE_BRIEF`;
- fail closed when the active pointer is absent or invalid;
- retain numeric discovery only behind explicit migration flag `--allow-legacy-discovery`;
- retire the Phase 66 bridge from active authority;
- reconcile root product docs, current truth, decision log, lessons, SAW evidence, and handover;
- bank and push one checkoutable `ROADMAP_FREEZE_COMMIT`;
- leave the dirty root checkout untouched.

R0 acceptance is independent-audit evidence, not self-declaration.

## 4. Authority separation

Deterministic pipelines own admitted facts, calculations, official thesis state, portfolio aims, capital, orders, fills, accounting, attribution, and authority decisions.

Agents may extract, normalize, propose hypotheses, find contradictions, propose analogies, and interpret deterministic outputs. Agents may not directly assign canonical probabilities, weights, orders, official falsification, promotion, or demotion.

Historical model output may generate present-day research proposals. It cannot be projected backward as historical decision authority.

## 5. Layered architecture

### L0 — Authority and custody

Immutable evidence versions, raw objects, admission timestamps, frozen decision manifests, permanent instrument identity, corporate-action events, and invocation custody.

### L1 — Accounting and portfolio book

Positions, quantities, classified cash, receivables, liabilities, fixture-required lots, raw marks, NAV, and reconciliation.

### L2 — Strategy and thesis

Candidate admission, Living Thesis state, milestones, economic falsifiers, scenarios, reference evidence, and bounded proposals.

### L3 — Portfolio and capital

Opportunity floors, candidate-specific capacity, simultaneous capital competition, cash classification, concentration, dependency, liquidity, and simple stress limits.

### L4 — Transition and execution

Current-versus-aim comparison, deterministic hysteresis, mandatory-action overrides, authorized transition, paper orders/fills, and cost custody.

### L5 — Replay and certification

Exact state reconstruction, correction lineage, corporate-action and partial-fill fixtures, accounting attribution, thesis-state replay, and certification.

### L6 — Scale and bounded challengers

Repeated portfolio operation, portfolio throughput, universe custody, challenger promotion, and separately authorized limited-live eligibility.

## 6. Minimum seams and parallelism law

Freeze these cross-layer seams before parallel implementation:

- `InstrumentId`;
- `EventId`;
- `EvidenceReference`;
- `PortfolioBookEvent`;
- `DecisionSnapshotId`;
- `PortfolioAimId`;
- `OrderId`;
- `FillId`;
- `CertificationId`.

Corrected interface rule:

```text
freeze minimum cross-layer seams before parallel work
freeze field-level detail only when the operator fixture exercises it
```

Maximum parallelism means maximum independent executable work, not maximum branch or worker count.

A package may run separately only when:

- it owns disjoint files;
- its seam is exercised by the shared fixture;
- it can merge independently;
- its failure does not force redesign of every package.

## 7. Three mergeable work packages

### Package A — Truth core

Combines conceptual lanes B0 Authority/Custody, B1 Book/Accounting, and B4 Replay skeleton.

Owns:

- permanent IDs and aliases;
- immutable events;
- content-addressed evidence references;
- book reducer;
- classified cash and NAV reconciliation;
- replay API skeleton.

### Package B — Decision vertical

Combines conceptual lanes B2 Strategy/Thesis and B3 Portfolio/Execution.

Owns:

- Living Thesis Lite;
- Bull/Base/Bear ranges;
- candidate outcomes: admit, reject, abstain, cash;
- deterministic capital competition;
- portfolio aim and transition;
- paper order and fill.

### Package C — Product closure

Combines conceptual lanes B5 Operator and B6 Docs/Ops.

Owns:

- launch/review/confirm/persist/reopen;
- read models;
- acceptance-fixture orchestration;
- later-observation explanation;
- authority synchronization.

Learn work may run in shadow only when it cannot mutate the prospective book, cannot create competing authority, and cannot block delivery without a P0/P1 correctness finding.

## 8. Slice 0 — `GV-MICRO-PORTFOLIO-VERTICAL-0`

Purpose: ship one complete prospective portfolio operating loop, not a schema catalogue.

Demo target:

```text
launch
→ review 3–5 securities, benchmark, and classified cash
→ inspect principal thesis, substitute, competitor, and rejection
→ confirm portfolio aim
→ generate deterministic paper order and fill
→ certify book
→ persist
→ reopen
→ admit one later observation
→ explain what changed and why
```

Minimum custody scope:

- content-addressed evidence references;
- permanent instrument IDs plus aliases;
- immutable event identity;
- one core corporate-action path actually exercised.

Minimum book scope:

- positions by permanent instrument ID;
- classified cash;
- receivables and costs only when exercised;
- NAV reconciliation;
- immutable original decision snapshot.

Minimum strategy scope:

- Living Thesis Lite;
- Bull/Base/Bear ranges;
- one hard economic falsifier;
- admit, reject, abstain, and cash outcomes.

Minimum portfolio/execution scope:

- deterministic capital competition;
- target quantities or weights;
- one transition;
- one paper order and fill;
- no optimizer.

Minimum product scope:

- new portfolio entry point;
- released `alpha_app.py` and `gv_fs0_v1` remain unchanged;
- one complete operator workspace;
- later prospective observation explains changed or preserved state.

Namespace:

```text
contracts/gv_portfolio/v0/
core/gv_portfolio_v0/
tests/gv_portfolio_v0/
```

Do not design unused tax, FX, derivatives, shorting, broad corporate-action, provider, or historical-loader frameworks.

## 9. Slice 1 — `GV-DETERMINISTIC-REPLAY-0`

Purpose: prove that the operated product is exactly reconstructable.

Acceptance:

- exact cash, quantities, costs, NAV, and thesis state;
- byte-stable prior certified decision;
- idempotent rerun;
- correction lineage;
- partial-fill residual state;
- valuation-pending without fabricated price;
- at least one split or equivalent value-transfer event;
- zero unexplained reconciliation residual within declared precision.

No bounded-portfolio expansion before this passes.

## 10. Later evidence-gated slices

### Slice 2 — `GV-BOUNDED-PORTFOLIO-1`

Operate 8–15 securities across at least two economic clusters repeatedly without custody, accounting, or review collapse.

### Slice 3 — `GV-PORTFOLIO-SCALE-1`

Scale the operated portfolio to 25–50 securities while preserving deterministic books, replay, and bounded operator workload.

### Slice 4 — `GV-UNIVERSE-SCALE-1`

Scale candidate custody to 100–300+ securities with survivorship-safe membership, permanent identity, corporate actions, corrections, and reproducible universe snapshots.

### Slice 5 — `GV-CHALLENGER-PROMOTION-1`

Promote challengers only through baseline → shadow → prospective challenger → independent replication → bounded authority.

### Slice 6 — `GV-LIMITED-LIVE-1`

Consider only a small, liquid, long-only, unleveraged, supervised, reversible pilot after repeated prospective paper operation, exact replay, stable custody, realistic cost/liquidity evidence, and separate owner authorization.

## 11. Gate score and planning forecast

Canonical shipped score remains `39/100` until accepted product evidence is banked.

Binary operational gates:

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      0/1
Prospective later observation      0/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

Nonbinding forecast after Slice 0 acceptance:

| Dimension | Current | After Slice 0 | After Slice 1 |
|---|---:|---:|---:|
| Product capability | 28 | 60–65 | 65–70 |
| User flow | 42 | 70–75 | 72–78 |
| Portfolio completeness | 18 | 65–70 | 70–75 |
| Integrity and replay | 64 | 70–75 | 90–95 |
| Prospective evidence | 10 | 20–30 | 30–40 |
| Shipping and custody | 78 | 85–90 | 90–95 |
| Weighted audit maturity | ≈39 | 62–66 | 70–74 |

These forecasts are explanatory only. They are not shipment or alpha evidence.

## 12. Anti-governance and velocity law

A gate may block delivery only when it prevents:

- look-ahead or invalid evidence;
- identity or corporate-action corruption;
- unauthorized or unreconciled capital;
- legal, mandate, solvency, or mandatory-action failure;
- irreversible operational harm;
- loss of deterministic replay.

The following do not block the first vertical and replay:

- complete ontology design;
- broad reference-class automation;
- factor-model perfection;
- fitted copulas or optimizers;
- ownership-network models;
- adaptive intraday control;
- tactical capital;
- broad provider acquisition;
- comprehensive tax optimization;
- live-capital machinery.

## 13. Change-control law

The sequence may be amended only when:

1. a completed slice exposes an impossible or contradictory boundary;
2. a P0/P1 custody, accounting, mandate, or replay defect requires a boundary change;
3. the owner explicitly changes the end mandate;
4. external legal or operational requirements invalidate a constraint.

Thresholds, vendors, models, and implementation techniques may evolve inside a slice without reopening the product architecture.

## 14. Immediate directive

```text
1. Independently audit ROADMAP_FREEZE_COMMIT.
2. After PASS, create a clean isolated worktree from that exact commit.
3. Ship GV-MICRO-PORTFOLIO-VERTICAL-0 through Packages A/B/C.
4. Certify GV-DETERMINISTIC-REPLAY-0 from real vertical events.
5. Keep the dirty root checkout untouched.
```

`93e7a55` is released ancestry, not a valid direct implementation base for the corrected product sequence.
