# Phase 43: Worker Implementation Guide — Threshold Enactment Contract (DORMANT)

**Status**: DORMANT (planning-only; no implementation authorization)  
**Created**: 2026-03-10  
**Round**: Implementation-contract definition only  
**Activation Token**: None in this round

---

## 1. Scope and Dormant Boundary

This guide defines the bounded future implementation contract for enacting the governance-selected gate constants:

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`

This guide is planning-only. It does **not** authorize code changes, test execution, artifact regeneration, or gate reruns.

**What This Guide Does**
- Locks the future code/doc/test surface
- Names the authoritative constant owner
- Defines acceptance checks, reviewer ownership, rollback, and later validation
- Keeps the future implementation bounded to frozen Phase 37 evidence and Phase 38 gate outputs

**What This Guide Does NOT Do**
- Authorize implementation in `strategies/`, `scripts/`, `tests/`, or `data/`
- Authorize any runtime worker-execution guide
- Authorize any output regeneration
- Reopen threshold selection or coverage-ratio policy

---

## 2. Governance-Locked Inputs

- `MIN_ACTIVE_DAYS_THRESHOLD_target = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
- Phase 37 packet remains frozen comparator truth
- Phase 38 packet remains frozen gate-execution evidence
- Phase 48 remains the shadow-ship target
- Inherited quarantines remain active: production, vendor workaround, `permno` migration, governed cost rewrite, new sleeves

---

## 3. Authoritative Constant Owner

The future implementation must use a single source of truth:

- `strategies/phase37_portfolio_registry.py`

The later authorized implementation round will add or update:

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`

**Binding rule**
- All future runtime consumers must import gate constants from the registry
- No inline threshold literals are allowed in runtime code
- Tests may reference `150` and `0.80` only to assert that the registry contract is loaded correctly

**Why this owner is locked**
- It already owns the Phase 37 method/window contract
- It minimizes surface area versus introducing a new config system
- It preserves a single auditable import path for later gate enactment

---

## 4. Exact Future File Surface

### Existing files to update later

1. `strategies/phase37_portfolio_registry.py`
2. `tests/test_phase37_portfolio_registry.py`
3. `docs/notes.md`
4. `docs/decision log.md`
5. `docs/lessonss.md`

### Future files to create or update later

1. `scripts/phase38_gate_execution.py`
2. `scripts/validate_phase38_gate_outputs.py`
3. `tests/test_phase38_gate_execution.py`

### Future generated outputs allowed only after explicit authorization

1. `data/processed/phase38_gate/gate_diagnostics_delta.csv`
2. `data/processed/phase38_gate/gate_recommendation.json`
3. `docs/saw_reports/saw_phaseXX_gate_enactment_YYYYMMDD.md`

No other runtime files or artifacts may be introduced without a new governance round.

---

## 5. Future Implementer Responsibilities

When a later explicitly authorized implementation round begins, the implementer must:

1. Update `strategies/phase37_portfolio_registry.py` to hold the selected constants
2. Create or update `scripts/phase38_gate_execution.py` so it imports the constants from the registry
3. Create or update `tests/test_phase37_portfolio_registry.py` to assert registry ownership and constant stability
4. Create or update `tests/test_phase38_gate_execution.py` to assert per-window gate application and `Pause` mapping
5. Create or update `scripts/validate_phase38_gate_outputs.py` to validate the two bounded outputs only
6. Update docs-as-code artifacts in the same round (`docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md`)

---

## 6. Future Reviewer Responsibilities

**Reviewer A — Strategy correctness / regression risk**
- Confirm the 150-day floor is imported from the registry
- Confirm coverage-ratio gate remains `0.80`
- Confirm gate semantics stay per-window and `Pause` on miss

**Reviewer B — Runtime / operational resilience**
- Confirm frozen Phase 37 evidence is reused without mutation
- Confirm no runtime scope expansion beyond the two bounded outputs
- Confirm no production/shadow activation or token drift

**Reviewer C — Data integrity / performance path**
- Confirm validator coverage for generated outputs
- Confirm docs, registry constants, and tests remain aligned
- Confirm no duplicate or stale gate artifacts are introduced

---

## 7. Future Acceptance Checks

- `CHK-P43-IMPL-01`: Registry owns `MIN_ACTIVE_DAYS_THRESHOLD = 150` and `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
- `CHK-P43-IMPL-02`: Runtime consumer imports gate constants from `strategies/phase37_portfolio_registry.py`
- `CHK-P43-IMPL-03`: No inline threshold literals appear in runtime gate code
- `CHK-P43-IMPL-04`: Validation and holdout windows are checked independently
- `CHK-P43-IMPL-05`: Gate miss still maps to `Pause`, not `Blocked`
- `CHK-P43-IMPL-06`: Only `gate_diagnostics_delta.csv` and `gate_recommendation.json` are regenerated
- `CHK-P43-IMPL-07`: Frozen Phase 37 outputs remain unchanged
- `CHK-P43-IMPL-08`: Targeted tests for registry and gate execution pass
- `CHK-P43-IMPL-09`: Gate-output validator passes
- `CHK-P43-IMPL-10`: SAW closeout passes with no unresolved in-scope Critical/High findings

---

## 8. Future Validation Path

The later explicitly authorized enactment round is bounded to this validation path:

### Targeted constant-propagation checks
```powershell
.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase38_gate_execution.py -q
```

### Bounded rerun against frozen Phase 37 evidence
```powershell
.venv\Scripts\python scripts\phase38_gate_execution.py
```

### Bounded output validation
```powershell
.venv\Scripts\python scripts\validate_phase38_gate_outputs.py
```

### SAW closeout validation
```powershell
.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phaseXX_gate_enactment_YYYYMMDD.md
```

The rerun above is forbidden in Phase 43. It is recorded here only as the future validation contract.

---

## 9. Rollback Note

If a later implementation round must be reverted before runtime authorization:

- revert `strategies/phase37_portfolio_registry.py`
- revert `scripts/phase38_gate_execution.py`
- revert `scripts/validate_phase38_gate_outputs.py`
- revert `tests/test_phase37_portfolio_registry.py`
- revert `tests/test_phase38_gate_execution.py`
- revert same-round docs updates

No rollback in this round touches generated artifacts because none are authorized.

---

## 10. Hard Blocks

- No code changes in this round
- No test execution in this round
- No artifact generation in this round
- No rerun or recompute of frozen Phase 37/38 evidence in this round
- No execution token in this round
- No production or shadow deployment activity
- No vendor workaround
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves

---

## 11. Approval Boundary

This guide is dormant until a later governance review accepts the implementation contract and a separate future authorization round explicitly opens implementation.

Required sequence:

1. Phase 43 planning packet remains sealed and dormant
2. Phase 44 reviews this contract
3. A later round authorizes implementation
4. A separate later round authorizes rerun/execution

No step in this guide collapses those boundaries.
