# Phase 40: Geometry Remedy Design Charter + Phase 40-50 Roadmap

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: CLOSED (planning-only; remedy design locked; execution not authorized)
**Created**: 2026-03-10
**Predecessor**: Phase 39 closed with reachability policy locked; no execution token issued
**Governance Disposition**: `Continue` (design packet sealed; phase closed; no execution token issued in this round)
**Execution Authorization**: Not granted in this brief; no Phase 40 execution token exists

---

## Objective

Design geometry remedy for Phase 38 threshold unreachability (252 active-days threshold exceeds validation 187 days and holdout 191 days window lengths). Anchor Method A (lower active-days threshold to reachable fixed floor) as starting option while preserving dual-gate family and governed windows. Embed Phase 40-50 roadmap with explicit Phase 48 shadow ship target and Phase 50+ capital decision boundary.

Phase 40 is remedy design and roadmap alignment only. It does not execute or re-execute any data, strategy, simulation, or portfolio-construction workflow.

---

## Problem Statement

Phase 38 gate diagnostics proved impossible geometry:
- Active-days threshold: 252 days
- Validation window length: 187 eligible days
- Holdout window length: 191 eligible days
- Reachability condition: `252 <= min(187, 191) = false`

Even perfect coverage (equal_weight: 187/187 validation, 191/191 holdout) fails the active-days gate because the threshold exceeds the governed window length.

---

## Frozen Inputs (Read-Only)

- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`
- `docs/saw_reports/saw_phase38_gate_execution_20260309.md`
- `docs/handover/phase38_governance_review.md`
- `docs/handover/phase38_execution_gate_ceo_memo.md`
- `docs/phase_brief/phase38-brief.md`
- `docs/phase_brief/phase39-brief.md`
- `docs/decision log.md` (D-240)

---

## Remedy Options

### Method A: Lower Active-Days Threshold (PRIMARY STARTING OPTION)

**Description**: Reduce `MIN_ACTIVE_DAYS_THRESHOLD` from 252 to a reachable fixed floor (e.g., 180, 150, 126) while preserving dual-gate structure and governed windows.

**Trade-offs**:
- Auditability: High (single constant change, dual-gate family preserved)
- Surface area: Minimal (threshold parameter only)
- Dual-gate preservation: Full (coverage ratio gate unchanged)
- Policy drift: Low (same governance family)
- Product impact: Moderate (threshold selection requires trade-off analysis)

**Status**: Anchored as starting option; no threshold value enacted in this phase.

### Method B: Redesign Governed Windows

**Description**: Expand validation/holdout window lengths to exceed 252 days or redesign window boundaries.

**Trade-offs**:
- Auditability: Moderate (window boundary changes affect all methods)
- Surface area: High (window design, comparator alignment, frozen evidence recomputation)
- Dual-gate preservation: Full (thresholds unchanged)
- Policy drift: Moderate (window policy change)
- Product impact: High (requires Phase 37/38 evidence recomputation)

**Status**: Deferred (higher surface area change).

### Method C: Redesign Dual-Gate Metric

**Description**: Replace active-days gate with alternative metric (e.g., percentage-based floor, rolling window).

**Trade-offs**:
- Auditability: Low (new metric family, governance precedent change)
- Surface area: Very high (metric design, validation, policy rewrite)
- Dual-gate preservation: None (new gate family)
- Policy drift: High (governance framework change)
- Product impact: Very high (new metric validation required)

**Status**: Deferred (highest surface area and policy drift).

---

## Locked Contracts (Carry-Forward)

- Comparator remains `data/processed/features_phase35_repaired.parquet`
- Runtime key remains `permno`
- Governed cost model remains `10` bps
- Dual gate remains the frozen policy family (active-days + coverage-ratio)
- Locked constants remain `MIN_ACTIVE_DAYS_THRESHOLD = 252` and `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` until Method A threshold selection is approved
- Research-only quarantine remains in force
- Phase 37 and Phase 38 evidence packets remain immutable
- No Phase 37/38 mutation, rerun, or recomputation authorized

---

## Phase 40-50 Roadmap Alignment

### Phase 40: Geometry Remedy Design (CURRENT - DORMANT)
- **Objective**: Design geometry remedy; anchor Method A as starting option
- **Success Criteria**: Remedy options documented with trade-off analysis; Method A anchored; roadmap locked
- **Failure Conditions**: Premature threshold selection; Method A not anchored; roadmap missing
- **Acceptance Matrix**: Brief published; decision log updated; no execution token; no threshold enacted
- **Governance Boundary**: Design packet sealed; execution not authorized

### Phase 41: Threshold Trade-Off Analysis (DORMANT)
- **Objective**: Analyze threshold candidates (180, 150, 126) under Method A; document auditability/product trade-offs
- **Success Criteria**: Trade-off matrix published; governance-ready threshold recommendation
- **Failure Conditions**: Threshold selection without trade-off analysis; dual-gate family violated
- **Acceptance Matrix**: Trade-off memo published; acceptance matrix defined; no execution token
- **Governance Boundary**: Analysis packet sealed; execution not authorized

### Phase 42: Threshold Governance Review (DORMANT)
- **Objective**: Governance review of threshold recommendation; explicit approval or hold
- **Success Criteria**: Governance disposition recorded; threshold locked or held
- **Failure Conditions**: Execution before governance approval; threshold enacted without review
- **Acceptance Matrix**: Governance memo published; disposition recorded; execution token conditional
- **Governance Boundary**: Governance review complete; execution conditional on approval

### Phase 43: Threshold Implementation (DORMANT)
- **Objective**: Implement approved threshold; update dual-gate constants
- **Success Criteria**: Threshold constant updated; reachability precheck passes; dual-gate family preserved
- **Failure Conditions**: Threshold change without approval; dual-gate family violated; reachability fails
- **Acceptance Matrix**: Code updated; tests pass; reachability verified; no Phase 37/38 mutation
- **Governance Boundary**: Implementation complete; gate re-execution authorized

### Phase 44: Gate Re-Execution (DORMANT)
- **Objective**: Re-execute Phase 38 gate with approved threshold; freeze new evidence
- **Success Criteria**: Gate diagnostics published; governance disposition recorded; evidence frozen
- **Failure Conditions**: Gate execution without threshold approval; evidence not frozen
- **Acceptance Matrix**: Gate diagnostics published; recommendation recorded; evidence frozen
- **Governance Boundary**: Gate evidence sealed; governance review required

### Phase 45: Gate Governance Review (DORMANT)
- **Objective**: Governance review of gate re-execution; explicit approval or hold
- **Success Criteria**: Governance disposition recorded; gate evidence approved or held
- **Failure Conditions**: Execution before governance approval; gate evidence not reviewed
- **Acceptance Matrix**: Governance memo published; disposition recorded; execution token conditional
- **Governance Boundary**: Governance review complete; execution conditional on approval

### Phase 46: Risk Closure Optimization (DORMANT)
- **Objective**: Optimize risk primitives and guardrails for approved methods
- **Success Criteria**: Risk diagnostics published; guardrails validated; governance-ready
- **Failure Conditions**: Risk optimization without gate approval; guardrails violated
- **Acceptance Matrix**: Risk diagnostics published; guardrails validated; governance review required
- **Governance Boundary**: Risk packet sealed; governance review required

### Phase 47: Pre-Ship Governance Review (DORMANT)
- **Objective**: Final governance review before shadow ship; explicit approval or hold
- **Success Criteria**: Governance disposition recorded; shadow ship authorized or held
- **Failure Conditions**: Shadow ship without governance approval; risk closure incomplete
- **Acceptance Matrix**: Governance memo published; disposition recorded; shadow ship token conditional
- **Governance Boundary**: Governance review complete; shadow ship conditional on approval

### Phase 48: Shadow Ship (DORMANT - SHADOW SHIP TARGET)
- **Objective**: Deploy approved methods to shadow environment; monitor without live capital
- **Success Criteria**: Shadow deployment complete; monitoring active; no live capital
- **Failure Conditions**: Live capital deployment; shadow monitoring incomplete
- **Acceptance Matrix**: Shadow deployment verified; monitoring active; no live capital
- **Governance Boundary**: Shadow ship complete; capital decision boundary ahead

### Phase 49: Shadow Monitoring and Validation (DORMANT)
- **Objective**: Monitor shadow performance; validate against frozen evidence
- **Success Criteria**: Shadow performance validated; governance-ready capital recommendation
- **Failure Conditions**: Shadow performance not validated; capital recommendation premature
- **Acceptance Matrix**: Shadow performance report published; capital recommendation documented
- **Governance Boundary**: Shadow validation complete; capital decision required

### Phase 50+: Capital Decision Boundary (DORMANT - CAPITAL DECISION)
- **Objective**: Governance decision on live capital deployment
- **Success Criteria**: Governance disposition recorded; capital deployment authorized or held
- **Failure Conditions**: Capital deployment without governance approval
- **Acceptance Matrix**: Governance memo published; disposition recorded; capital deployment conditional
- **Governance Boundary**: Capital decision boundary; live deployment conditional on approval

---

## Explicitly Out of Scope (Hard Block)

- Threshold rewrites (`252 / 0.80` remains unchanged in this phase; Method A threshold selection deferred to Phase 42 governance approval after Phase 41 analysis)
- Any rerun or recompute of Phase 37 or Phase 38 outputs
- Any mutation of frozen Phase 37 or Phase 38 evidence packets
- Portfolio method rewrites or sleeve-set changes
- Production promotion, deployment, or live-capital actions
- Vendor bypass (S&P IQ / BvD remains asynchronous)
- Runtime-key migration away from `permno`
- Governed cost-model rewrite
- Code scaffolding, script creation, test execution, or artifact generation
- Any execution activity before future explicit governance approval

## Approval Boundary

This brief does **not** authorize execution.

Any future remedy execution path requires:
- Phase 41 threshold trade-off analysis completed
- Method A threshold selection approved in Phase 42
- Explicit future governance instruction issued in-thread
- A separate execution contract document
- Clear confirmation that out-of-scope hard blocks remain intact

---

## Immediate Next Milestone

Keep the Phase 40 design packet sealed and closed.

Any future proposal must first complete Phase 41 threshold trade-off analysis and then receive explicit governance direction before any execution surface can be opened.

---

## New Context Packet (Phase 40)

### What Was Done
- Locked the Phase 40 geometry remedy design as a docs-only planning packet.
- Anchored Method A (lower active-days threshold) as starting option without enacting threshold value.
- Embedded Phase 40-50 roadmap with explicit Phase 48 shadow ship target and Phase 50+ capital decision boundary.
- Preserved frozen Phase 37 and Phase 38 evidence without rerun, recompute, or mutation.

### What Is Locked
- `252 / 0.80` thresholds remain unchanged until Method A threshold selection is approved in Phase 42 after Phase 41 analysis.
- Method A remains anchored as starting option; Method B and Method C deferred.
- Phase 40-50 roadmap locked with explicit governance boundaries.
- Phase 48 marked as shadow ship target; Phase 50+ marked as capital decision boundary.
- Frozen Phase 37 and Phase 38 packets remain immutable.
- Comparator/runtime-key/cost/quarantine contracts remain unchanged.
- No Phase 40 execution token exists in this packet.

### What Is Next
- Maintain the sealed docs-only Phase 40 design packet.
- Require Phase 41 threshold trade-off analysis before any threshold selection.
- Keep all execution paths blocked until future explicit governance approval.
- Optimize for risk closure toward Phase 48 shadow ship, not phase compression.

### First Command
```text
Get-Content docs/phase_brief/phase40-brief.md
```

### Next Todos
- Keep the Method A anchor explicit in all Phase 40 follow-up docs.
- Preserve frozen Phase 37 and Phase 38 evidence with no reruns or recomputation.
- Keep research quarantine and all hard blocks unchanged.
- Maintain Phase 40-50 roadmap alignment with explicit governance boundaries.


