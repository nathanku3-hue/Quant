# Phase 48: Bounded Coverage-Floor Enactment and Gate Rerun

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: HISTORICAL REFERENCE ONLY (not the active current-state packet)  
**Created**: 2026-03-10  
**Predecessor**: Phase 47 closed with `Continue` and locked `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` under Method A  
**Authorization Source**: CEO directive dated 2026-03-10 recorded in the active governance packet  
**Execution Authorization**: No active authority in the current Phase 47 docs-only state

---

## Objective

This brief is retained as historical context only. It does not describe the active current-state packet while the repository remains in Phase 47 docs-only planning.

Historical objective:

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`

Then rerun only the bounded Phase 38 gate path against frozen evidence inputs and regenerate only the governed output pair:
- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`

This implementation is now complete. The corrected packet has been returned to governance review.

---

## Governance-Locked Inputs

- Authoritative constant owner: `strategies/phase37_portfolio_registry.py`
- Runtime gate path: `scripts/phase38_gate_execution.py`
- Output validator: `scripts/validate_phase38_gate_outputs.py`
- Frozen comparator evidence:
  - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
  - `data/processed/phase38_gate/gate_recommendation.json`
- Phase 47 locked policy:
  - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
  - `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`

---

## Corrected Implementation Outcome

The bounded rerun completed after an in-scope SAW reconciliation repaired active-day derivation.

- Validation window: `130` active days, `0.6952` coverage
- Holdout window: `126` active days, `0.6597` coverage
- Coverage floor `0.65` passes in both governed windows
- Active-days floor `150` fails in both governed windows
- Corrected portfolio decision: `Pause`
- Corrected method votes: `0 Continue / 3 Pause`

### Withdrawn Pre-Fix Result

An earlier interim `Continue` result is explicitly withdrawn.

- Root cause: duplicated sleeve-row `n_days` values were summed as if they were distinct governed day counts
- Repair: governed window geometry now dedupes `(window, regime)` rows and fails closed if duplicate sleeve rows disagree on `n_days`
- Governance implication: the repaired packet, not the withdrawn interim output, is the only decision-grade Phase 48 evidence

---

## Authorized Surface

### Runtime Write Surface Used
- `strategies/phase37_portfolio_registry.py`
- `scripts/phase38_gate_execution.py`
- `scripts/validate_phase38_gate_outputs.py`
- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`

### Validation Surface Used
- `tests/test_phase37_portfolio_registry.py`
- `tests/test_phase38_gate_execution.py`

### Governance Closeout Surface
- `docs/handover/phase48_governance_review.md`
- `docs/phase_brief/phase48-worker-implementation-guide.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`
- Phase 48 SAW report

The bounded runtime work is complete. No further implementation edits are authorized in this phase.

---

## Validation Path Used

Use the repo-local virtual environment for all commands.

### Targeted tests
```powershell
.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase38_gate_execution.py -q
```

### Bounded rerun
```powershell
.venv\Scripts\python scripts\phase38_gate_execution.py
```

### Output validation
```powershell
.venv\Scripts\python scripts\validate_phase38_gate_outputs.py
```

### Context refresh after closeout
```powershell
.venv\Scripts\python scripts\build_context_packet.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

---

## Acceptance Checks

- `CHK-P48-01`: Phase 47 locked `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` is reflected in the Phase 48 packet
- `CHK-P48-02`: `MIN_ACTIVE_DAYS_THRESHOLD = 150` remains unchanged
- `CHK-P48-03`: The registry remains the authoritative constant owner
- `CHK-P48-04`: No inline gate literals are introduced outside registry ownership
- `CHK-P48-05`: The bounded rerun stays inside the existing Phase 38 gate path
- `CHK-P48-06`: Only the two governed outputs are regenerated
- `CHK-P48-07`: Targeted tests pass on the repaired packet
- `CHK-P48-08`: Output validator passes on the repaired packet
- `CHK-P48-09`: Corrected rerun output is `Pause` with validation `130 / 0.6952` and holdout `126 / 0.6597`
- `CHK-P48-10`: Earlier false `Continue` is explicitly withdrawn and root-caused
- `CHK-P48-11`: Phase 48 governance review memo is ready for post-rerun disposition
- `CHK-P48-12`: Notes mirror the explicit dual-gate formula and Python ownership
- `CHK-P48-13`: All inherited hard blocks remain active

---

## Hard Blocks

- No production or shadow deployment activity
- No rerun outside the bounded Phase 38 gate path
- No reopening of policy selection inside Phase 48
- No vendor workaround
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves
- No Sovereign cartridge integration inside this packet

---

## Immediate Next Milestone

Record the CEO/PM `Continue / Edit / Hold` disposition against the corrected `Pause` packet. No further rerun is authorized in Phase 48.

---

## New Context Packet (Phase 48)

### What Was Done
- Closed Phase 47 with `Continue` and locked `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`.
- Completed the bounded Phase 48 enactment and corrected an in-scope active-day derivation defect.
- Re-ran the bounded Phase 38 gate path and regenerated the governed output pair.
- Returned the corrected Phase 48 packet to governance review with `Pause`.

### What Is Locked
- `MIN_ACTIVE_DAYS_THRESHOLD = 150` remains enacted and unchanged.
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` remains enacted and unchanged.
- The corrected Phase 48 output packet is `Pause` and supersedes the withdrawn pre-fix interim `Continue`.
- All inherited hard blocks remain active.

### What Is Next
- Review `docs/handover/phase48_governance_review.md`.
- Record the Phase 48 `Continue / Edit / Hold` disposition against the corrected `Pause` packet.
- Keep the corrected Phase 48 evidence packet read-only until that disposition is recorded.

### First Command
```text
Get-Content docs/handover/phase48_governance_review.md
```

### Next Todos
- Keep the corrected Phase 48 evidence packet read-only.
- Route all interpretation changes through docs-only governance review.
- Do not reopen policy selection, deployment, or Sovereign integration in this round.


