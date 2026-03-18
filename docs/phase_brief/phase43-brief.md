# Phase 43: Threshold Implementation Planning

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: DORMANT (planning-only; implementation not authorized)  
**Created**: 2026-03-10  
**Predecessor**: Phase 42 selected `MIN_ACTIVE_DAYS_THRESHOLD = 150` with coverage-ratio gate unchanged at `0.80`; no execution token issued  
**Governance Disposition**: `Continue` (Phase 42 threshold selection locked; translation to bounded implementation contract only)  
**Execution Authorization**: Not granted in this brief; no Phase 43 implementation or execution token exists

---

## Objective

Translate the governance-selected Method A target (`MIN_ACTIVE_DAYS_THRESHOLD = 150`, `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`) into a bounded future implementation contract. Lock the exact file surface, authoritative constant owner, acceptance checks, reviewer ownership, rollback note, and validation path required for a later explicitly authorized implementation round.

Phase 43 is implementation planning only. It does not modify code, rewrite constants, generate tests, rerun evidence, or authorize execution.

---

## Governance-Locked Inputs

- `MIN_ACTIVE_DAYS_THRESHOLD_target = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` (unchanged)
- `threshold_reachable = 150 <= min(eligible_days_validation, eligible_days_holdout)` remains satisfied under the sealed Phase 39 policy
- Phase 37 and Phase 38 evidence remain frozen
- Method A remains the only active remedy path
- Phase 48 remains the shadow-ship target

---

## Implementation Planning Scope

### Authoritative Constant Owner

The future implementation round will use a single authoritative owner for the gate constants:

- `strategies/phase37_portfolio_registry.py`

Planned future registry constants:

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`

The future runtime consumer must import these values from the registry. Inline threshold literals are forbidden outside tests that explicitly assert the registry contract.

### Exact Future File Surface

The later explicitly authorized implementation round is bounded to the following surfaces:

**Existing files to update later**
- `strategies/phase37_portfolio_registry.py`
- `tests/test_phase37_portfolio_registry.py`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`

**Future files to create or update later**
- `scripts/phase38_gate_execution.py`
- `scripts/validate_phase38_gate_outputs.py`
- `tests/test_phase38_gate_execution.py`

**Future generated evidence to refresh only after explicit authorization**
- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`
- `docs/saw_reports/saw_phaseXX_gate_enactment_YYYYMMDD.md`

### Required Planning Outputs

1. Bounded future file list for the implementation round
2. Dedicated dormant worker implementation guide
3. Acceptance matrix for constant update and propagation validation
4. Explicit implementer and reviewer ownership
5. Rollback note for reverting the selected target before any later runtime authorization
6. Shadow-ship alignment note explaining why the implementation still preserves the Phase 48 path

---

## Ownership and Review Surface

**Future implementer ownership**
- Registry constants in `strategies/phase37_portfolio_registry.py`
- Gate consumer in `scripts/phase38_gate_execution.py`
- Gate validator/test surface in `scripts/validate_phase38_gate_outputs.py`, `tests/test_phase37_portfolio_registry.py`, and `tests/test_phase38_gate_execution.py`

**Future reviewer ownership**
- Reviewer A: strategy correctness, constant propagation, and unchanged method semantics
- Reviewer B: runtime boundary integrity, frozen-input discipline, and no-scope-creep enforcement
- Reviewer C: data/output integrity, validator coverage, and docs-to-code alignment

---

## Acceptance Matrix for the Later Implementation Round

- `CHK-P43-IMPL-01`: Registry owns `MIN_ACTIVE_DAYS_THRESHOLD = 150` and `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` as the single source of truth
- `CHK-P43-IMPL-02`: `scripts/phase38_gate_execution.py` imports the gate constants from the registry rather than using inline literals
- `CHK-P43-IMPL-03`: `tests/test_phase37_portfolio_registry.py` asserts the registry constants and gate contract remain locked
- `CHK-P43-IMPL-04`: `tests/test_phase38_gate_execution.py` verifies per-window gate application, `Pause` disposition on gate miss, and no threshold derivation
- `CHK-P43-IMPL-05`: `scripts/validate_phase38_gate_outputs.py` validates the bounded delta outputs only
- `CHK-P43-IMPL-06`: Bounded rerun uses frozen Phase 37 evidence and does not mutate upstream artifacts
- `CHK-P43-IMPL-07`: Only `data/processed/phase38_gate/gate_diagnostics_delta.csv` and `data/processed/phase38_gate/gate_recommendation.json` are regenerated
- `CHK-P43-IMPL-08`: Targeted tests for registry and gate execution pass
- `CHK-P43-IMPL-09`: Gate-output validator passes
- `CHK-P43-IMPL-10`: SAW closeout passes with no unresolved in-scope Critical/High findings

---

## Success Criteria

- The future implementation round can identify the exact constant owner and downstream consumers without further policy ambiguity
- The future acceptance checks are explicit and auditable
- The future validation path is narrow: targeted constant-propagation checks, one bounded rerun against frozen Phase 37 evidence, and SAW
- The planning packet keeps implementation blocked until later explicit authorization
- Phase 48 shadow-ship path remains the product target

---

## Failure Conditions

- Any code or constant rewrite in this phase
- Any test execution or artifact generation in this phase
- Any rerun or recompute of frozen Phase 37/38 evidence in this phase
- Any change to `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
- Any reopening of the `150` threshold decision
- Any introduction of production/shadow execution authority

---

## Locked Constraints

### Threshold Selection Is Locked, Not Enacted
- `150` is the governance-selected target for future implementation
- `0.80` remains unchanged
- code/constants remain unchanged in Phase 43

### No Execution Surface
- no implementation token exists
- no runtime worker-execution guide is authorized in this phase
- the dedicated `phase43-worker-implementation-guide.md` is planning-only and does not authorize runtime work
- no runtime or portfolio execution is authorized

### Frozen Evidence Preserved
- no Phase 37 or Phase 38 mutation
- no rerun, recompute, or artifact regeneration in this phase
- comparator/runtime-key/cost/quarantine contracts remain unchanged

---

## Hard Blocks

- No code changes
- No test execution
- No artifact generation
- No execution-token issuance
- No runtime worker-execution guide for active execution
- No vendor workaround
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves
- No production or shadow deployment activity

---

## Rollback Note

Phase 43 is docs-only. Rollback is limited to the planning packet artifacts:

- `docs/phase_brief/phase43-brief.md`
- `docs/phase_brief/phase43-worker-implementation-guide.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`
- `docs/saw_reports/saw_phase43_implementation_planning_20260310.md`

No runtime artifacts are touched in this round.

---

## Approval Boundary

This brief does **not** authorize implementation.

The next governance step is Phase 44 review of the sealed implementation contract. Any later implementation requires:
- explicit future governance instruction issued in-thread
- a separate implementation-authorization round
- confirmation that inherited hard blocks remain intact

Any future gate re-execution requires:
- implementation completion in a later authorized round
- a separate execution authorization step
- future governance review of the resulting packet

---

## Immediate Next Milestone

Keep the Phase 43 implementation planning packet sealed and dormant.

The next governance action is Phase 44 review of the implementation contract defined in this brief and in `docs/phase_brief/phase43-worker-implementation-guide.md`.

---

## New Context Packet (Phase 43)

### What Was Done
- Recorded the Phase 42 governance selection of `150` as the Method A threshold target.
- Sealed Phase 43 as a docs-only implementation-planning packet with a dedicated dormant worker guide.
- Locked `strategies/phase37_portfolio_registry.py` as the future authoritative constant owner and preserved the unchanged `0.80` coverage-ratio gate.

### What Is Locked
- `MIN_ACTIVE_DAYS_THRESHOLD_target = 150` is selected for future implementation planning.
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` remains unchanged.
- `strategies/phase37_portfolio_registry.py` is the future single source of truth for the gate constants.
- Code/constants remain unchanged until a later explicitly authorized implementation round.
- Phase 37 and Phase 38 packets remain immutable.
- No Phase 43 implementation or execution token exists in this packet.

### What Is Next
- Review the sealed implementation contract in Phase 44 governance review.
- Keep execution blocked until a later explicit authorization step.
- Preserve the Phase 48 shadow-ship path and all quarantines.
- Use the future validation path only after implementation is explicitly authorized.

### First Command
```text
Get-Content docs/phase_brief/phase43-worker-implementation-guide.md
```

### Next Todos
- Confirm the bounded future file surface for the 150-day constant enactment.
- Keep the registry as the only authoritative owner for gate constants.
- Preserve frozen Phase 37/38 evidence and inherited quarantines.
- Defer all code, test, rerun, and output regeneration work until later explicit authorization.


