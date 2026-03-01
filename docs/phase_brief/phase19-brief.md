# Phase 19 Brief: Alignment & Evidence Discipline Sprint
Date: 2026-02-20
Status: Day 0 Active (48-hour alignment sprint)
Owner: Atomic Mesh

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Alignment & Evidence Discipline
- L2 Active Streams: Backend, Data, Ops
- L2 Deferred Streams: Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Ops
- Active Stage Level: L3
- Current Stage: Executing
- Planning Gate Boundary: in-scope = docs alignment + governance lock + Phase 21 Day 1 delta gate; out-of-scope = roadmap restart or legacy rollback.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-201..CHK-210.

### Aligned Forward Roadmap (Post-Phase-18 C3 State)

| Phase | Duration | L1 Focus | Key Deliverables | Acceptance Gates (must PASS or explicit ADVISORY_PASS with documented risks) | Why this order? |
|-------|----------|----------|------------------|-------------------------------------------------------|-----------------|
| **19** | 2 days | Alignment & Evidence Discipline | spec.md mapping, phase19-brief.md, AGENTS.md rule, lessonss.md entry, Phase 21 Day 1 delta script | All docs updated, delta script produces CSV+PNG, SAW verdict published | Locks evidence discipline before any risk layer ships |
| **20** | 2.5 weeks | Risk & Position Management | Adaptive stop-loss (regime/conviction-weighted K), drawdown monitor wired through engine, full C3 integration | Sharpe delta ≥ -0.03, turnover increase ≤15%, MaxDD neutral-or-better, crisis turnover ≥70%, SAW PASS | Risk only after edge proven; prevents polishing weak signal |
| **21** | 3 weeks | Optimizer & Robustness | Joint WFO on scorecard+stops, DSR-first promotion, activity guards | Promoted candidate passes strict OOS (stability + activity + DSR), Sharpe degradation ≤12% | Optimization is refinement, never discovery |
| **22** | 2 weeks | Production & Monitoring | Live cockpit + risk dashboard, auto-SAW stub, 30-day live sim | End-to-end daily run <50 s (Top-2000), zero manual intervention | Production only after everything else validated |
| **23+** | Ongoing | Factor Evolution | New families, ensembles, alt-data | Monthly SAW + lessons entry, net alpha contribution positive | Continuous improvement, never “done” |

## 1. Quantitative Day 1 Promotion Gate (Locked)
- `Sharpe_C3+Stops ≥ Sharpe_C3 - 0.03`
- `Turnover_annual_C3+Stops ≤ Turnover_C3 × 1.15`
- `MaxDD_C3+Stops ≤ MaxDD_C3 + 0.03` (absolute)
- `Crisis turnover reduction (all windows) ≥ 70%`
- Decision rule:
  - `>= 3/4` gates pass -> `PROMOTE` (full `PASS` only if all 4 pass)
  - `>= 2` failures -> `ABORT` Phase 21 Day 1 and pivot to Phase 19.5 (`Scorecard Coverage & Spread Sprint`)

## 2. Top-Down Snapshot
L1: Alignment & Evidence Discipline Sprint
L2 Active Streams: Backend, Data, Ops
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning → Executing → Iterate Loop → Final Verification → CI/CD
Active Stream: Ops
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                                                 |
+--------------------+------------------------------------------------------------+--------+------------------------------------------------------------+
| Planning           | B=Phase19 docs+gates; OH=Impl->RevA/B/C; AC=CHK-201..210  | 92/100 | 1) Freeze check IDs + artifact paths [90/100]: prevents   |
|                    |                                                            |        | drift before edits and runtime gate runs.                 |
| Executing          | Update spec/phase18/phase19 + AGENTS + lessonss + script  | 86/100 | 1) Implement strict delta script outputs [88/100]: core   |
|                    |                                                            |        | evidence gate for Day 1 risk layer.                       |
| Iterate Loop       | Reconcile delta results against C3 baseline decision gate  | 82/100 | 1) Apply abort/pivot rule if needed [84/100]: preserve    |
|                    |                                                            |        | governance integrity over feature momentum.                |
| Final Verification | py_compile + pytest + artifact existence + SAW validators  | 80/100 | 1) Publish docs/saw_phase21_day1.md [85/100]: closure     |
|                    |                                                            |        | must include quantified deltas and verdict.                |
| CI/CD              | Handoff for next phase stream (Phase 20 WFO integration)   | 88/100 | 1) Open Phase 20 execution brief [78/100]: continue from  |
|                    |                                                            |        | aligned roadmap with locked evidence discipline.           |
+--------------------+------------------------------------------------------------+--------+------------------------------------------------------------+

## 3. Day 0 Execution Contract
- Keep existing codebase; no restart path.
- Enforce evidence discipline before any additional risk-layer promotion.
- Canonical Day 1 risk impact artifacts:
  - `data/processed/phase21_day1_delta_metrics.csv`
  - `data/processed/phase21_day1_equity_overlay.png`
  - `docs/saw_phase21_day1.md`

## 4. Rollback Note
- If Phase 19 alignment is rejected:
  - revert Phase 19 documentation changes (`spec.md`, `phase18-brief.md`, `phase19-brief.md`, `AGENTS.md`, `lessonss.md` entries),
  - remove Day 1 impact artifacts and restore pre-sprint governance state.

## 5. Phase 19.5 Pivot (Post Day-1 Gate Abort)
Date: 2026-02-20
Status: Active
Mission: Scorecard Coverage & Spread Sprint (signal first, risk second).

Scope:
- Lift scorecard quality before any new stop/risk promotion attempt.
- Keep same window/cost/engine path versus locked C3 baseline.
- Run ablation + walk-forward and stop at quantitative decision gate.

Deliverables:
- Coverage >= 80%.
- Quartile spread sigma >= 2.0.
- At least one new factor family or validity mode explored.
- Re-run Day-5 style ablation and Day-6 style walk-forward.
- Publish SAW round and decision for promote/hold/abort.

Gate Contract:
- Coverage >= 80%.
- Quartile spread >= 2.0.
- Sharpe >= locked C3 baseline in same path.
- Crisis turnover reduction >= 70% in all crisis windows.
- At least 3/4 grouped checks pass: CHK-41, CHK-48, CHK-50, CHK-51..53 bundle.

Top-Down Snapshot
L1: Alignment & Evidence Discipline (Phase 19)
L2 Active Streams: Backend, Data
L2 Deferred Streams: Frontend/UI, Ops (risk)
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Phase 19.5 signal sprint; OH=Impl→RevA/B/C; AC=CHK-211..220 | 95/100 | Freeze factor candidates + gates   |
| Executing          | New factors + validity modes + strengthening script        | 88/100 | Run ablation + walk-forward        |
| Iterate Loop       | Reconcile vs C3 baseline                                   | 85/100 | Apply new C3 lock if gates pass    |
| Final Verification | py_compile + pytest + SAW                                  | 82/100 | Publish SAW + update production_config |
| CI/CD              | Handoff to Phase 20 (joint WFO with future stops)          | 80/100 | Open Phase 20 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## 6. Phase 19.6 Pivot (Deep Diagnostics & Orthogonality)
Date: 2026-02-20
Status: Active
Mission: Recover spread and crisis robustness before any new risk-layer work.

Scope:
- Diagnose spread regression with orthogonality evidence.
- Introduce regime-adaptive normalization for stress regimes.
- Add liquidity/quality veto logic for RED-regime short diagnostics.
- Re-run diagnostics sprint and stop at strict decision gate.

Deliverables:
- `phase19_6_orthogonality_report.csv`
- `phase19_6_delta_vs_c3.csv`
- `phase19_6_crisis_turnover.csv`
- `docs/saw_phase19_6_round1.md`

Gate Contract (all required):
- Coverage >= 85%
- Spread sigma >= 2.10
- Crisis turnover reduction >= 75% in all windows
- CHK bundle pass >= 4/5

Top-Down Snapshot
L1: Alignment & Evidence Discipline (Phase 19)
L2 Active Streams: Backend, Data
L2 Deferred Streams: Frontend/UI, Ops (risk)
L3 Stage Flow: Planning → Executing → Iterate Loop → Final Verification → CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Phase 19.6 diagnostics; focus spread + crisis; OH=Impl→Rev | 96/100 | Freeze correlation audit + veto rules |
| Executing          | Orthogonality matrix + regime-adaptive norm + liquidity veto | 90/100 | Run diagnostics sprint             |
| Iterate Loop       | Compare vs Phase 19.5 & original C3                        | 87/100 | Apply new C3 lock if all gates pass |
| Final Verification | py_compile + pytest + SAW                                  | 85/100 | Publish SAW + update production_config |
| CI/CD              | Handoff to Phase 20 (joint WFO with stops once spread fixed) | 82/100 | Open Phase 20 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## 7. Phase 19.7 Pivot (Regime Fidelity Forensics)
Date: 2026-02-20
Status: Active
Mission: enforce strict RED-veto fidelity so stress behavior matches governor intent.

Scope:
- Force RED governor fidelity (cash/zero exposure in RED).
- Add per-regime factor/correlation/contribution audit.
- Gate selection on regime-spread and crisis-turnover protection.
- Keep baseline comparability (same window/cost/engine path).

Deliverables:
- `data/processed/phase19_7_regime_audit.csv`
- `data/processed/phase19_7_delta_vs_c3.csv`
- `data/processed/phase19_7_crisis_turnover.csv`
- `docs/saw_phase19_7_round1.md`

Gate Contract:
- Coverage >= 90%
- Spread sigma >= 2.30 in every regime
- Sharpe >= 0.95
- Crisis turnover reduction >= 80% in all windows
- CHK bundle pass >= 4/5

Top-Down Snapshot
L1: Alignment & Evidence Discipline (Phase 19)
L2 Active Streams: Backend, Data
L2 Deferred Streams: Frontend/UI, Ops (risk)
L3 Stage Flow: Planning → Executing → Iterate Loop → Final Verification → CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Phase 19.7 regime fidelity; strict RED-veto; OH=Impl→Rev | 97/100 | Freeze per-regime audit + veto rules |
| Executing          | RED-veto + per-regime audit matrix + weighted spread       | 92/100 | Run fidelity sprint                |
| Iterate Loop       | Compare vs 19.6 & original C3                              | 89/100 | Apply new C3 lock if all gates pass |
| Final Verification | py_compile + pytest + SAW                                  | 86/100 | Publish SAW + update production_config |
| CI/CD              | Handoff to Phase 20 (joint WFO with stops once fidelity fixed) | 84/100 | Open Phase 20 brief                |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
