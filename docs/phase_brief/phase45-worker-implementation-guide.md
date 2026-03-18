# Phase 45: Worker Implementation Guide — Bounded Gate Enactment (AUTHORIZED)

**Status**: AUTHORIZED (bounded implementation round open; execution/deployment still blocked)  
**Created**: 2026-03-10  
**Round**: Phase 45 bounded implementation enactment  
**Authorization Token**: `approve phase45 implementation`

---

## 1. Scope and Active Boundary

This guide authorizes the bounded implementation of the governance-locked gate constants:

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`

This round is implementation-authorized, but it remains tightly bounded. It authorizes only the file, test, rerun, and artifact surface already sealed in the Phase 43 contract and Phase 45 authorization packet.

**What This Guide Authorizes**
- Enact the registry-owned gate constants in the authoritative owner
- Create the bounded Phase 38 gate execution script and validator
- Add the targeted tests for registry ownership and gate behavior
- Run the targeted tests
- Run one bounded gate rerun against frozen Phase 37 evidence
- Regenerate only the two bounded Phase 38 gate outputs
- Update same-round governance records and publish SAW closeout

**What This Guide Does NOT Authorize**
- Production or shadow deployment
- Any rerun outside the bounded Phase 38 gate path
- Threshold re-selection or policy rewrite
- `permno` migration
- Governed `10` bps cost-model rewrite
- New sleeves, new signals, or broader scope expansion

---

## 2. Governance-Locked Inputs

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
- Authoritative constant owner: `strategies/phase37_portfolio_registry.py`
- Phase 37 packet remains frozen comparator truth
- Phase 38 gate path remains the only bounded rerun surface
- Phase 48 remains the shadow-ship target
- Inherited hard blocks remain active: production, vendor workaround, `permno` migration, governed cost rewrite, new sleeves

---

## 3. Authorized Write Surface

Only the following files may be changed in this round.

### Existing files
1. `strategies/phase37_portfolio_registry.py`
2. `tests/test_phase37_portfolio_registry.py`
3. `docs/notes.md`
4. `docs/decision log.md`
5. `docs/lessonss.md`

### Files to create or update
1. `scripts/phase38_gate_execution.py`
2. `scripts/validate_phase38_gate_outputs.py`
3. `tests/test_phase38_gate_execution.py`
4. `docs/saw_reports/saw_phase45_implementation_20260310.md`

### Generated outputs allowed in this round
1. `data/processed/phase38_gate/gate_diagnostics_delta.csv`
2. `data/processed/phase38_gate/gate_recommendation.json`

No other runtime files, tests, scripts, outputs, or docs may be introduced without a new governance round.

---

## 4. Implementer Responsibilities

The implementer must complete all items below within the bounded surface:

1. Update `strategies/phase37_portfolio_registry.py` so it owns:
   - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
2. Create or update `scripts/phase38_gate_execution.py` so it imports the constants from the registry and applies the dual gate per validation and holdout window.
3. Create or update `scripts/validate_phase38_gate_outputs.py` so it validates only the two bounded outputs.
4. Create or update `tests/test_phase37_portfolio_registry.py` to assert registry ownership and constant stability.
5. Create or update `tests/test_phase38_gate_execution.py` to assert:
   - import-based constant propagation
   - independent per-window checks
   - `Pause` on gate miss
6. Update same-round docs-as-code artifacts:
   - `docs/notes.md`
   - `docs/decision log.md`
   - `docs/lessonss.md`
7. Run the bounded validation path exactly as defined in Section 7.
8. Publish SAW closeout with implementer/reviewer separation intact.

---

## 5. Reviewer Responsibilities

**Implementer**
- Own only the authorized write surface listed above
- Do not touch unrelated runtime or product surfaces

**Reviewer A — Strategy correctness / regression risk**
- Confirm the registry is the single source of truth for `150 / 0.80`
- Confirm gate semantics stay per-window and map misses to `Pause`
- Confirm no threshold reselection or scope drift occurs

**Reviewer B — Runtime / operational resilience**
- Confirm rerun scope is limited to the bounded Phase 38 gate path
- Confirm frozen Phase 37 evidence remains unchanged
- Confirm no deployment or activation surface is opened

**Reviewer C — Data integrity / performance path**
- Confirm output validator covers both bounded outputs
- Confirm tests and regenerated artifacts match the locked contract
- Confirm no duplicate or stale gate artifacts are introduced

Implementer and reviewers must be different agents in the SAW report.

---

## 6. Acceptance Checks

- `CHK-P45-IMPL-01`: `strategies/phase37_portfolio_registry.py` owns `MIN_ACTIVE_DAYS_THRESHOLD = 150` and `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
- `CHK-P45-IMPL-02`: `scripts/phase38_gate_execution.py` imports gate constants from the registry
- `CHK-P45-IMPL-03`: No inline threshold literals appear in runtime gate code outside registry ownership
- `CHK-P45-IMPL-04`: Validation and holdout windows are checked independently
- `CHK-P45-IMPL-05`: Gate miss maps to `Pause`, never `Blocked`
- `CHK-P45-IMPL-06`: Rerun reuses frozen Phase 37 evidence without mutation
- `CHK-P45-IMPL-07`: Only `gate_diagnostics_delta.csv` and `gate_recommendation.json` are regenerated
- `CHK-P45-IMPL-08`: Targeted tests for registry ownership and gate execution pass
- `CHK-P45-IMPL-09`: Gate-output validator passes
- `CHK-P45-IMPL-10`: Docs-as-code updates record the enactment and guardrail
- `CHK-P45-IMPL-11`: SAW closeout passes with no unresolved in-scope Critical/High findings
- `CHK-P45-IMPL-12`: All inherited hard blocks remain intact after implementation

---

## 7. Authorized Validation Path

Use the repo-local virtual environment for all commands.

### Targeted tests
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

### Context packet refresh and validation
```powershell
.venv\Scripts\python scripts\build_context_packet.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

### SAW report validation
```powershell
.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase45_implementation_20260310.md
```

---

## 8. Deliverables

The round is complete only when all items below exist and validate:

- registry update in `strategies/phase37_portfolio_registry.py`
- gate execution script in `scripts/phase38_gate_execution.py`
- gate output validator in `scripts/validate_phase38_gate_outputs.py`
- targeted tests in `tests/test_phase37_portfolio_registry.py` and `tests/test_phase38_gate_execution.py`
- bounded outputs:
  - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
  - `data/processed/phase38_gate/gate_recommendation.json`
- same-round docs updates:
  - `docs/notes.md`
  - `docs/decision log.md`
  - `docs/lessonss.md`
- SAW closeout:
  - `docs/saw_reports/saw_phase45_implementation_20260310.md`

---

## 9. Rollback Note

If this bounded implementation round must be reverted before any later deployment authorization:

- revert `strategies/phase37_portfolio_registry.py`
- revert `scripts/phase38_gate_execution.py`
- revert `scripts/validate_phase38_gate_outputs.py`
- revert `tests/test_phase37_portfolio_registry.py`
- revert `tests/test_phase38_gate_execution.py`
- revert same-round docs updates
- remove regenerated bounded outputs if they were produced in this round

Rollback remains limited to the bounded Phase 45 surface. It does not reopen policy selection or mutate frozen pre-round evidence.

---

## 10. Hard Blocks

- No production or shadow deployment activity
- No rerun outside the bounded Phase 38 gate path
- No threshold reselection or coverage-ratio rewrite
- No mutation of frozen Phase 37 outputs beyond the bounded gate outputs
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves, factors, or strategy discovery
- No scope expansion beyond the authorized write surface

---

## 11. Closeout Requirement

This round closes only after:

1. all acceptance checks pass
2. the bounded outputs validate
3. the context packet rebuilds cleanly
4. SAW reports `PASS` or `ADVISORY_PASS` with no unresolved in-scope Critical/High findings

Anything less leaves Phase 45 incomplete.
