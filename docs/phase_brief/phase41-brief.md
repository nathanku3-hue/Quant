# Phase 41: Threshold Trade-Off Analysis

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: DORMANT (planning-only; execution not authorized)
**Created**: 2026-03-10
**Predecessor**: Phase 40 closed with Method A anchored; no execution token issued
**Governance Disposition**: `Continue` (planning directive locked; threshold selection still pending Phase 42 governance review)
**Execution Authorization**: Not granted in this brief; no Phase 41 execution token exists

---

## Objective

Analyze candidate active-days threshold floors (180, 150, 126 days) under Method A remedy design. Evaluate each candidate across auditability, geometry reachability, dual-gate preservation, downstream governance impact, and shadow-ship path impact. Produce a weighted scorecard, ranked option set, and CEO decision surface for Phase 42 governance review without enacting any threshold value.

Phase 41 is comparative analysis only. It does not execute or re-execute any data, strategy, simulation, or portfolio-construction workflow. It does not enact any threshold value.

---

## Context

Phase 40 approved Method A (lower active-days threshold to reachable fixed floor) as the anchored starting option for geometry remedy. The current threshold (252 days) exceeds both validation window length (187 eligible days) and holdout window length (191 eligible days), creating impossible reachability geometry.

No threshold value has been enacted. Phase 41 evaluates candidate threshold floors comparatively to inform future governance threshold selection.

---

## Candidate Floor Matrix

### Reachability Constraint

All candidate thresholds must satisfy:
```
threshold <= min(validation_window_length, holdout_window_length)
threshold <= min(187, 191) = 187
```

### Candidate Floors

1. **180 days** (conservative floor)
2. **150 days** (moderate floor)
3. **126 days** (aggressive floor)

All three candidates satisfy the reachability constraint: `180 <= 187`, `150 <= 187`, `126 <= 187`.

---

## Evaluation Dimensions

### 1. Auditability
- Transparency of threshold selection rationale
- Explainability to governance and external auditors
- Alignment with industry standards or precedent
- Simplicity of threshold constant change

### 2. Geometry Reachability
- Satisfaction of validation window constraint (187 days)
- Satisfaction of holdout window constraint (191 days)
- Margin of safety against window boundary
- Robustness to future window adjustments

### 3. Dual-Gate Preservation
- Coverage ratio gate unchanged (0.80 threshold preserved)
- Active-days gate family preserved (fixed floor structure)
- Dual-gate policy family continuity
- No governance precedent drift

### 4. Downstream Governance Impact
- Future phase complexity (Phase 42-50 roadmap)
- Governance review surface area
- Risk closure optimization requirements (Phase 46)
- Shadow ship readiness (Phase 48)

### 5. Shadow-Ship Path Impact
- Shadow deployment complexity
- Monitoring and validation requirements (Phase 49)
- Capital decision boundary readiness (Phase 50+)
- Production promotion risk profile

---

## Weighted Scorecard Rubric

### Fixed Weight Vector

The Phase 41 weighted scorecard uses a fixed `100`-point weight vector:

| Dimension | Weight |
|-----------|--------|
| Auditability | 25 |
| Geometry Reachability | 30 |
| Dual-Gate Preservation | 15 |
| Downstream Governance Impact | 15 |
| Shadow-Ship Path Impact | 15 |

### Ordinal Scale

Each dimension is scored on a `1-5` ordinal scale:

- `5` = strongest governance fit / lowest friction
- `4` = strong fit with modest trade-off cost
- `3` = acceptable fit with meaningful trade-off cost
- `2` = weak fit; narrow margin or elevated governance burden
- `1` = unacceptable fit for current governance objectives

### Score Formula

For each threshold candidate:

```text
weighted_score(candidate) =
  (25*auditability
 + 30*geometry_reachability
 + 15*dual_gate_preservation
 + 15*downstream_governance_impact
 + 15*shadow_ship_path_impact) / 100
```

The scorecard is semi-quantitative. It ranks options for governance review; it does not authorize or enact any threshold.

---

## Trade-Off Matrix

### Candidate: 180 Days (Conservative Floor)

**Auditability**:
- High transparency (conservative margin below 187-day constraint)
- Strong explainability (clear safety buffer)
- Alignment with ~6-month trading window precedent
- Minimal governance friction

**Geometry Reachability**:
- Full satisfaction: `180 <= min(187, 191) = true`
- Safety margin: 7 days below validation window (187 - 180 = 7)
- Safety margin: 11 days below holdout window (191 - 180 = 11)
- Moderate robustness to future window adjustments

**Dual-Gate Preservation**:
- Full preservation (coverage ratio 0.80 unchanged)
- Active-days gate family preserved
- No policy drift
- Governance precedent continuity maintained

**Downstream Governance Impact**:
- Low complexity for Phase 42 governance review
- Minimal risk closure optimization surface (Phase 46)
- Standard shadow ship readiness (Phase 48)
- Low governance review friction

**Shadow-Ship Path Impact**:
- Standard shadow deployment complexity
- Standard monitoring requirements (Phase 49)
- Low capital decision boundary risk (Phase 50+)
- Conservative production promotion profile

**Trade-Off Summary**:
- Strengths: High auditability, low governance friction, conservative risk profile
- Weaknesses: Moderate safety margin, less aggressive coverage expansion
- Net Assessment: Conservative choice with strong governance alignment

---

### Candidate: 150 Days (Moderate Floor)

**Auditability**:
- Moderate transparency (balanced margin below 187-day constraint)
- Good explainability (~5-month trading window)
- Alignment with quarterly + buffer precedent
- Moderate governance friction

**Geometry Reachability**:
- Full satisfaction: `150 <= min(187, 191) = true`
- Safety margin: 37 days below validation window (187 - 150 = 37)
- Safety margin: 41 days below holdout window (191 - 150 = 41)
- High robustness to future window adjustments

**Dual-Gate Preservation**:
- Full preservation (coverage ratio 0.80 unchanged)
- Active-days gate family preserved
- No policy drift
- Governance precedent continuity maintained

**Downstream Governance Impact**:
- Moderate complexity for Phase 42 governance review
- Moderate risk closure optimization surface (Phase 46)
- Standard shadow ship readiness (Phase 48)
- Moderate governance review friction

**Shadow-Ship Path Impact**:
- Standard shadow deployment complexity
- Standard monitoring requirements (Phase 49)
- Moderate capital decision boundary risk (Phase 50+)
- Balanced production promotion profile

**Trade-Off Summary**:
- Strengths: Balanced auditability, strong safety margin, high robustness
- Weaknesses: Moderate governance friction, requires trade-off justification
- Net Assessment: Balanced choice with strong reachability margin

---

### Candidate: 126 Days (Aggressive Floor)

**Auditability**:
- Moderate transparency (large margin below 187-day constraint)
- Requires stronger explainability (~4-month trading window)
- Less alignment with standard precedent
- Higher governance friction

**Geometry Reachability**:
- Full satisfaction: `126 <= min(187, 191) = true`
- Safety margin: 61 days below validation window (187 - 126 = 61)
- Safety margin: 65 days below holdout window (191 - 126 = 65)
- Very high robustness to future window adjustments

**Dual-Gate Preservation**:
- Full preservation (coverage ratio 0.80 unchanged)
- Active-days gate family preserved
- No policy drift
- Governance precedent continuity maintained

**Downstream Governance Impact**:
- Higher complexity for Phase 42 governance review
- Higher risk closure optimization surface (Phase 46)
- Requires stronger shadow ship validation (Phase 48)
- Higher governance review friction

**Shadow-Ship Path Impact**:
- Higher shadow deployment validation requirements
- Enhanced monitoring requirements (Phase 49)
- Higher capital decision boundary risk (Phase 50+)
- Aggressive production promotion profile

**Trade-Off Summary**:
- Strengths: Maximum safety margin, very high robustness, maximum coverage expansion
- Weaknesses: Higher governance friction, requires stronger justification, higher validation requirements
- Net Assessment: Aggressive choice with maximum reachability margin but higher governance surface

---

## Weighted Scorecard Results

| Dimension | Weight | 180 Days | 150 Days | 126 Days |
|-----------|--------|----------|----------|----------|
| Auditability | 25 | 5 | 4 | 3 |
| Geometry Reachability | 30 | 2 | 4 | 5 |
| Dual-Gate Preservation | 15 | 5 | 5 | 5 |
| Downstream Governance Impact | 15 | 5 | 4 | 3 |
| Shadow-Ship Path Impact | 15 | 4 | 4 | 3 |
| **Weighted Score** | **100** | **3.95 / 5.00** | **4.15 / 5.00** | **3.90 / 5.00** |

### Ranked Options

1. **150 Days** — `4.15 / 5.00`
   - Balanced lead option: strongest combined reachability margin and governance manageability.
2. **180 Days** — `3.95 / 5.00`
   - Conservative fallback: strongest auditability profile but thinner geometric safety margin.
3. **126 Days** — `3.90 / 5.00`
   - Aggressive reserve option: maximum reachability buffer but highest governance and shadow-validation burden.

### Interpretation Rule

- The scorecard produces a ranked option set for CEO/PM review.
- The ranking does **not** force a single threshold recommendation.
- Any threshold selection remains explicitly deferred to Phase 42 governance review.

### Phase 42 Decision Surface

The Phase 42 governance round will use `Continue / Edit / Hold`:

- **Continue**: accept the ranked option set and select one threshold for Phase 43 implementation.
- **Edit**: request docs-only revision of weights, ordinal scores, or rationale without enacting a threshold.
- **Hold**: freeze the packet and advance no threshold path.

### Dormant Review Template

- Phase 42 review template path: `docs/handover/phase42_threshold_governance_review_template.md`
- Template status: dormant planning surface only; no execution or enactment authority.

---

## Locked Constraints

### Method A Remains Only Anchored Option
- Method B (redesign governed windows) remains deferred
- Method C (redesign dual-gate metric) remains deferred
- Method A threshold selection remains open (no value enacted)

### Exact Threshold Value Remains Open
- No threshold enacted in Phase 41
- Threshold selection deferred to Phase 42 governance review
- All three candidates (180/150/126) remain viable pending governance approval
- Ranked order does not enact a threshold and does not reduce CEO/PM discretion

### No Threshold Enacted in Phase 41
- `MIN_ACTIVE_DAYS_THRESHOLD = 252` remains unchanged in code
- No constant rewrites authorized in this phase
- Threshold implementation deferred to Phase 43 (conditional on Phase 42 approval)

### Threshold Selection Deferred to Future Governance Review
- Phase 42 governance review required before threshold selection
- Explicit governance approval required before Phase 43 implementation
- No execution token exists for threshold enactment

---

## Hard Blocks (Carry-Forward from Phase 40)

### No Phase 37/38 Mutation
- Phase 37 portfolio construction evidence remains frozen
- Phase 38 gate diagnostics evidence remains frozen
- No rerun, recompute, or mutation of frozen evidence packets

### No Threshold Rewrite Until Future Approval
- `MIN_ACTIVE_DAYS_THRESHOLD = 252` remains unchanged
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` remains unchanged
- No dual-gate constant rewrites authorized in Phase 41

### No Code/Test/Artifact Generation
- No script creation or modification
- No test execution or validation
- No artifact generation or evidence freezing
- Analysis and documentation only

### No Execution Token
- No execution authorization granted in Phase 41
- No data pipeline execution
- No strategy simulation execution
- No portfolio construction execution

### No Worker-Execution-Guide Yet
- No Phase 41 worker-execution-guide authorized
- Execution guide deferred to Phase 43 (conditional on Phase 42 approval)
- Phase 41 remains docs-only planning round

### Research Quarantine Maintained
- Research-only quarantine remains in force
- No production promotion authorized
- No live capital deployment authorized
- Shadow ship target remains Phase 48

### 10 bps Cost Locked
- Governed cost model remains `10` bps
- No cost model rewrites authorized
- Cost model continuity preserved

### permno Key Locked
- Runtime key remains `permno`
- No runtime-key migration authorized
- Key continuity preserved

---

## Approval Boundary

This brief does **not** authorize execution.

Phase 41 is comparative analysis only. No threshold value is enacted. No code, test, or artifact generation is authorized.

Any future Phase 41 execution requires:
- Explicit future governance instruction issued in-thread
- A separate execution contract document
- Clear confirmation that out-of-scope hard blocks remain intact

Any threshold selection requires:
- Phase 42 governance review and explicit approval
- Phase 43 implementation authorization
- Phase 44 gate re-execution authorization

---

## Immediate Next Milestone

Keep the Phase 41 trade-off analysis packet sealed and dormant.

Any future proposal must first complete Phase 42 governance review and receive explicit threshold selection approval before Phase 43 implementation surface can be opened.

---

## New Context Packet (Phase 41)

### What Was Done
- Locked the Phase 41 threshold trade-off analysis as a docs-only planning packet.
- Evaluated three candidate threshold floors (180, 150, 126 days) across five dimensions.
- Produced a fixed weighted scorecard and ranked option set without enacting any threshold value.
- Prepared the Phase 42 governance decision surface and dormant review memo template.
- Preserved frozen Phase 37 and Phase 38 evidence without rerun, recompute, or mutation.

### What Is Locked
- `252 / 0.80` thresholds remain unchanged until Phase 42 governance approval and Phase 43 implementation.
- Method A remains anchored as starting option; threshold value remains open.
- Three candidate floors (180/150/126) remain viable pending Phase 42 governance review.
- Phase 40-50 roadmap locked with explicit governance boundaries.
- Frozen Phase 37 and Phase 38 packets remain immutable.
- Comparator/runtime-key/cost/quarantine contracts remain unchanged.
- No Phase 41 execution token exists in this packet.

### What Is Next
- Maintain the sealed docs-only Phase 41 trade-off analysis packet.
- Require Phase 42 governance review for threshold selection approval.
- Keep all execution paths blocked until Phase 42 approval and Phase 43 authorization.
- Optimize for risk closure toward Phase 48 shadow ship, not phase compression.

### First Command
```text
Get-Content docs/phase_brief/phase41-brief.md
```

### Next Todos
- Keep the Method A anchor and candidate floor matrix explicit in all Phase 41 follow-up docs.
- Preserve the fixed scorecard weights and ordinal scores unless a docs-only Edit disposition is issued.
- Carry the ranked option set into the Phase 42 governance review surface without enacting any threshold.
- Preserve frozen Phase 37 and Phase 38 evidence with no reruns or recomputation.
- Keep research quarantine and all hard blocks unchanged.
- Maintain Phase 40-50 roadmap alignment with explicit governance boundaries.
- Defer threshold selection to Phase 42 governance review.


