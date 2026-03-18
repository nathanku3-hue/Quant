# Phase 48: Worker Implementation Guide — Bounded Coverage-Floor Enactment

**Status**: COMPLETE / READ-ONLY  
**Round**: Phase 48 bounded implementation + gate rerun  
**Authorization Source**: CEO directive dated 2026-03-10 recorded in the governance packet

---

## 1. Scope

This guide documented the bounded enactment of:

- `MIN_ACTIVE_DAYS_THRESHOLD = 150`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`

This was not a broader portfolio, product, or deployment round. It was a narrow gate-policy enactment and bounded rerun only. The implementation is now complete and this guide is retained as read-only evidence.

---

## 2. Owned Runtime Surface Used

The completed runtime round touched only:
- `strategies/phase37_portfolio_registry.py`
- `scripts/phase38_gate_execution.py`
- `scripts/validate_phase38_gate_outputs.py`
- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`

The completed runtime round used these targeted tests:
- `tests/test_phase37_portfolio_registry.py`
- `tests/test_phase38_gate_execution.py`

An in-scope SAW reconciliation later required bounded test repair to catch duplicate-sleeve regime geometry. No broader runtime surface was opened.

---

## 3. Required Runtime Behavior

1. Keep `MIN_ACTIVE_DAYS_THRESHOLD = 150` unchanged.
2. Enact `MIN_COVERAGE_RATIO_THRESHOLD = 0.65` in the authoritative registry owner.
3. Keep the runtime gate logic sourced from the registry owner; do not inline constants in gate code.
4. Keep validation and holdout checks independent.
5. Keep any gate miss mapped to `Pause`.
6. Regenerate only the two bounded outputs.
7. Fail closed if duplicate sleeve rows disagree on the governed `n_days` geometry for the same `(window, regime)`.

---

## 4. Validation Commands

```powershell
.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase38_gate_execution.py -q
.venv\Scripts\python scripts\phase38_gate_execution.py
.venv\Scripts\python scripts\validate_phase38_gate_outputs.py
```

---

## 5. Stop Conditions

These stop conditions governed the completed round:
- an edit is required outside the owned runtime surface
- the rerun attempts to touch broader Phase 37 evidence or unrelated outputs
- a change would open production, shadow deployment, or unrelated strategy work
- the work would require reopening threshold choice or broader policy design inside Phase 48

---

## 6. Hard Blocks

- No deployment or shadow-ship activation
- No vendor workaround
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves
- No Sovereign cartridge integration in this packet
- No unrelated runtime work

---

## 7. Deliverables

- Updated registry constant owner with `150 / 0.65`
- Bounded rerun output files:
  - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
  - `data/processed/phase38_gate/gate_recommendation.json`
- Clean targeted test run
- Clean output validation run
- Handoff to `docs/handover/phase48_governance_review.md` for CEO/PM disposition

---

## 8. Completion Note

The repaired Phase 48 packet returns:

- Validation: `130` active days, `0.6952` coverage
- Holdout: `126` active days, `0.6597` coverage
- Corrected portfolio decision: `Pause`

The next round is docs-only governance review. No further implementation is authorized under this guide.
