# Phase 47: Coverage-Ratio Remedy Lock

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: ACTIVE CURRENT GOVERNANCE STATE (docs-only planning; runtime enactment remains blocked)  
**Created**: 2026-03-10  
**Predecessor**: Phase 46 closed with `Continue`; the Phase 45 `Pause` packet was accepted as decision-grade evidence with coverage ratio identified as the sole binding constraint  
**Governance Disposition**: `Continue` → lock `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` under Method A  
**Execution Authorization**: None; current state remains docs-only planning until the locked P0 gate is clean

---

## Objective

Phase 47 is the authoritative current governance state for this repository. The active round is docs-only planning that keeps runtime enactment blocked while the locked P0 fail-closed and documentation-alignment work is completed.

Historical note: this brief originally captured the coverage-floor selection inside Method A. That selection remains part of the audit trail, but the present-tense repository state stays Phase 47 docs-only and does **not** treat Phase 48 as the active implementation packet.

---

## Governance-Locked Inputs

- `MIN_ACTIVE_DAYS_THRESHOLD = 150` remains enacted and is not reopened
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` is the superseded prior floor under review in this phase only
- Validation window evidence from Phase 45: `390` active days, `0.6952` coverage
- Holdout window evidence from Phase 45: `378` active days, `0.6597` coverage
- `min_current_coverage = min(0.6952, 0.6597) = 0.6597`
- Portfolio outcome from Phase 45 remains `Pause` with `0 Continue / 3 Pause / 0 Pivot`
- Frozen evidence inputs remain:
  - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
  - `data/processed/phase38_gate/gate_recommendation.json`

---

## Policy Decision

### Locked Policy
- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`
- Binding rule remains: validation and holdout must each pass the dual gate independently
- Miss disposition remains: `Pause`

### Selection Formula
```text
coverage_margin(candidate_floor) = min_current_coverage - candidate_floor
```

Applied to the accepted Phase 45 packet:
- `coverage_margin(0.65) = 0.6597 - 0.65 = 0.0097`
- `coverage_margin(0.60) = 0.6597 - 0.60 = 0.0597`
- `coverage_margin(0.55) = 0.6597 - 0.55 = 0.1097`

### Decision Rationale
- `0.65` is the narrowest floor that clears the current binding constraint while preserving institutional conservatism
- `0.60` provides more margin but loosens the gate more than required by the evidence
- `0.55` provides the widest margin but increases policy-drift and dilution risk without a stronger governance case
- One common floor across validation and holdout remains more auditable than window-specific values

---

## Phase 47 Closeout Effects

### What Closed Here
- Method A remains the only remedy family
- The candidate set `0.65 / 0.60 / 0.55` is no longer merely advisory in this packet
- `0.65` is now the locked future coverage floor

### What Did Not Happen Here
- No code or constant enactment in runtime files
- No rerun or recompute
- No regeneration of gate outputs
- No production or shadow-deployment activity

---

## Phase 48 Routing

Phase 48 opens immediately as a bounded implementation + rerun packet with the following target:

- enact `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` in the authoritative registry owner
- reuse the bounded Phase 38 gate path only
- regenerate only:
  - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
  - `data/processed/phase38_gate/gate_recommendation.json`
- keep all inherited quarantines active

The bounded implementation contract for that next round is defined in:
- `docs/phase_brief/phase48-brief.md`
- `docs/phase_brief/phase48-worker-implementation-guide.md`

---

## Acceptance Checks

- `CHK-P47-LOCK-01`: Phase 47 records `Continue` and closes as a completed policy-selection round
- `CHK-P47-LOCK-02`: `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` is explicit in the brief and review memo
- `CHK-P47-LOCK-03`: `MIN_ACTIVE_DAYS_THRESHOLD = 150` remains explicit and unchanged
- `CHK-P47-LOCK-04`: The `coverage_margin(c)` formula and candidate comparisons are preserved
- `CHK-P47-LOCK-05`: The rationale for preferring `0.65` over `0.60` and `0.55` is explicit
- `CHK-P47-LOCK-06`: Phase 48 bounded implementation packet is created with a worker guide
- `CHK-P47-LOCK-07`: Phase 48 governance review memo template is created
- `CHK-P47-LOCK-08`: `docs/notes.md` mirrors the selected constant, formula, and Python ownership
- `CHK-P47-LOCK-09`: Decision log records D-252 for the Phase 47 lock and Phase 48 routing
- `CHK-P47-LOCK-10`: Lessons log records the close-selection-then-route guardrail
- `CHK-P47-LOCK-11`: Context rebuild routes the repository to `active_phase = 48`

---

## Success Criteria

- Phase 47 is sealed as the governance round that selects `0.65`
- The active-days remedy remains closed
- The future runtime enactment surface is isolated to Phase 48
- The repository no longer boots into the superseded candidate-only Phase 47 state
- All inherited hard blocks remain explicit

---

## Failure Conditions

- Any Phase 47 runtime mutation, rerun, or artifact regeneration
- Any reopening of `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- Any broadening of the Phase 48 bounded surface beyond the governed gate path
- Any attempt to combine Phase 48 gate enactment with unrelated cartridge integration or deployment work

---

## Out of Boundary / Hard Blocks

- No Phase 47 rerun or recompute
- No mutation of the frozen Phase 45 evidence packet in this phase
- No reopening of `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- No production or shadow deployment activity
- No vendor workaround
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves or method-set expansion
- No Sovereign cartridge integration inside this Phase 47 closeout packet

---

## New Context Packet (Phase 47 Closeout)

### What Was Done
- Closed Phase 47 with `Continue` and selected `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`.
- Preserved `MIN_ACTIVE_DAYS_THRESHOLD = 150` and the per-window dual-gate family.
- Recorded the Phase 47 selection rationale from the accepted Phase 45 evidence packet.
- Opened the bounded Phase 48 implementation + rerun packet.

### What Is Locked
- `MIN_ACTIVE_DAYS_THRESHOLD = 150` remains enacted and unchanged.
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` is governance-locked for Phase 48 enactment.
- Phase 45 evidence remains the frozen comparator input.
- All inherited hard blocks remain active.

### What Is Next
- Execute the bounded Phase 48 packet only.
- Keep the rerun surface limited to the registry owner, gate path, validator, and two bounded outputs.
- Keep deployment and unrelated strategy work blocked.

### First Command
```text
Get-Content docs/phase_brief/phase48-brief.md
```

### Next Todos
- Enact `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` in the authoritative registry owner.
- Run the bounded Phase 38 gate rerun only.
- Publish the Phase 48 governance review memo after outputs validate.


