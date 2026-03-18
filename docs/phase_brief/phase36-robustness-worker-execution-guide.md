# Phase 36 Robustness Worker Execution Guide

> Historical note: this guide is the closed robustness-round contract. The active next-step handoff is now `docs/phase_brief/phase36-post-robustness-worker-execution-guide.md` for governance review / PM handoff only.

**Date**: 2026-03-08
**Round ID**: `P36-RB-01`
**Scope**: Research-only robustness diagnostics on the 4 locked Phase 36 bundles
**Do Not Do**: promote to production, reopen Phase 35, change `permno`, rewrite the governed cost model, or wait on S&P IQ / BvD procurement

---

## Mission

Take the 4 evidence-gate survivors and run a governed robustness round that proves whether the signal thesis survives deeper regime and friction stress without changing the repaired comparator contract.

**Locked bundle set**
- `bundle_quality_vol`
- `bundle_quality_composite`
- `bundle_vol_composite`
- `bundle_all_three`

**Comparator artifact**
- `data/processed/features_phase35_repaired.parquet`

**Governed windows**
- Calibration: `2022-01-01` -> `2023-06-30`
- Validation: `2023-07-01` -> `2024-03-31`
- Holdout: `2024-04-01` -> `2024-12-31`

**Comparator sidecars**
- `data/processed/phase35_reruns/phase35_baseline_corrected_calibration/phase34_summary.json`
- `data/processed/phase35_reruns/phase35_baseline_corrected_validation/phase34_summary.json`
- `data/processed/phase35_reruns/phase35_baseline_corrected_holdout/phase34_summary.json`
- `data/processed/phase35_reruns/phase35_baseline_corrected_calibration/phase34_behavior_ledger.csv`
- `data/processed/phase35_reruns/phase35_baseline_corrected_validation/phase34_behavior_ledger.csv`
- `data/processed/phase35_reruns/phase35_baseline_corrected_holdout/phase34_behavior_ledger.csv`

---

## Scope Lock

### Allowed
- New robustness runner, tests, validators, and docs
- New robustness outputs under `data/processed/phase36_rule100/robustness/`
- Read-only reuse of governed Phase 35 / Phase 36 evidence artifacts
- Regime diagnostics using existing Phase 35 behavior-ledger daily labels
- Diagnostic friction stress on `10 / 20 / 30` bps only

### Forbidden
- Editing `data/processed/features_phase35_repaired.parquet`
- Adding new bundles or changing the 4-bundle survivor set
- Re-optimizing bundle weights or introducing coefficient fitting
- Changing runtime identifiers away from `permno`
- Rewriting the governed base-case cost model
- Any production-readiness, deployment, or live sizing language
- Blocking work on S&P IQ / BvD credentials or legal entitlement

---

## Locked Decisions To Encode

1. **Friction stress grid**
   - Implement only `10 / 20 / 30` bps
   - Treat the grid as diagnostic-only; do not rewrite the primary comparator contract

2. **Recommendation rubric**
   - Portfolio-level output must be one of `Continue`, `Pause`, or `Pivot`
   - Use a majority-based rule over the 4 locked bundles
   - Do not use best-bundle-wins logic

3. **Fail-closed floor**
   - A bundle that breaches the robustness floor under `20` bps holdout conditions is killed immediately for this round
   - Surface the kill decision explicitly in `bundle_friction_stress.csv` and `bundle_robustness_recommendation.json`
   - The exact floor check must be named explicitly in code and documented in `docs/notes.md`; do not hide it in an unnamed magic threshold

4. **Diagnostic-only calibration rule**
   - Negative average calibration delta IC remains diagnostic-only
   - Do not convert calibration weakness into a new hard promotion gate mid-round

5. **Regime source lock**
   - Use only Phase 35 behavior-ledger regime labels
   - Do not introduce a new regime classifier or re-label history during this round

---

## File Ownership for This Round

### Create
- `scripts/phase36_bundle_robustness_round.py`
- `scripts/build_phase36_robustness_manifest.py`
- `tests/test_phase36_bundle_robustness_round.py`
- `tests/test_build_phase36_robustness_manifest.py`
- `scripts/validate_phase36_bundle_robustness_outputs.py`
- `tests/test_validate_phase36_bundle_robustness_outputs.py`
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`

### Update
- `docs/phase_brief/phase36-brief.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/notes.md` when the robustness floor or stress formulas are implemented in code

### Read-Only Inputs
- `strategies/phase36_bundle_registry.py`
- `scripts/phase36_bundle_evidence_gate.py`
- `scripts/signal_sweep_runner.py`
- `data/processed/phase36_rule100/bundles_sweep_results.csv`
- `data/processed/phase36_rule100/bundles_summary.json`
- `data/processed/phase36_rule100/bundles_promoted.txt`
- `data/processed/phase36_rule100/evidence_gate/bundle_exec_metrics.csv`
- `data/processed/phase36_rule100/evidence_gate/bundle_recommendation.json`

---

## Required Helper Reuse

Reuse these helpers instead of rebuilding simulation math from scratch:
- `scripts/day5_ablation_report.py:431` — `_build_target_weights`
- `scripts/day6_walkforward_validation.py:261` — `_simulate_from_scores`
- `scripts/day6_walkforward_validation.py:316` — `_period_metrics`
- `scripts/signal_sweep_runner.py:524` — `load_baseline_metrics`
- `scripts/signal_sweep_runner.py:647` — `apply_bundle_baseline_gate`
- `scripts/phase36_bundle_evidence_gate.py:34` — `load_regime_labels`

If helper signatures drift, adapt the new robustness runner to the helper contract. Do not fork the simulation logic unless reuse is impossible and documented.

---

## Output Contract

Write all robustness outputs under `data/processed/phase36_rule100/robustness/`.

Required artifacts:
- `locked_bundle_set.json`
- `bundle_robustness_metrics.csv`
- `bundle_robustness_metrics.json`
- `bundle_regime_robustness.csv`
- `bundle_friction_stress.csv`
- `bundle_equity_curves.parquet`
- `bundle_robustness_recommendation.json`

Required sidecars:
- `data/processed/phase36_rule100/robustness/robustness_input_manifest.json`
- `data/processed/phase36_rule100/robustness/robustness_comparator_snapshot.json`

---

## Execution Order

### Step 1 — Freeze the Locked Bundle Set
Read the survivor source of truth and materialize an explicit freeze file:
- Source: `data/processed/phase36_rule100/bundles_promoted.txt`
- Output: `data/processed/phase36_rule100/robustness/locked_bundle_set.json`

The JSON must contain exactly 4 bundle names and the round metadata.

### Step 2 — Implement the Robustness Runner
Create `scripts/phase36_bundle_robustness_round.py`.

Minimum contract:
- loads the 4 locked bundles only
- reads the repaired comparator artifact only
- reuses the governed simulation path
- computes base-case bundle metrics on the same windows
- computes regime diagnostics using the Phase 35 behavior ledgers
- computes friction stress at `10`, `20`, and `30` bps
- emits per-bundle and portfolio-level `Continue / Pause / Pivot` decisions
- fails closed on missing columns, missing sidecars, or comparator mutations

Required CLI shape:
```powershell
.venv\Scripts\python scripts/phase36_bundle_robustness_round.py `
  --features-path data/processed/features_phase35_repaired.parquet `
  --bundle-set data/processed/phase36_rule100/robustness/locked_bundle_set.json `
  --bundle-results data/processed/phase36_rule100/bundles_sweep_results.csv `
  --baseline-dir data/processed/phase35_reruns `
  --output-dir data/processed/phase36_rule100/robustness `
  --stress-grid-bps 10 20 30 `
  --calibration-start 2022-01-01 `
  --calibration-end 2023-06-30 `
  --validation-start 2023-07-01 `
  --validation-end 2024-03-31 `
  --holdout-start 2024-04-01 `
  --holdout-end 2024-12-31
```

### Step 3 — Implement the Test Pack
Create `tests/test_phase36_bundle_robustness_round.py`.

Minimum coverage:
- only the 4 locked bundles are loaded
- missing/mutated comparator fails closed
- regime labels load only from Phase 35 behavior ledgers
- `10 / 20 / 30` bps grid is enforced exactly
- portfolio recommendation uses majority logic, not best-bundle-wins
- per-bundle kill state is surfaced when the robustness floor breaches
- outputs use the required schemas and filenames

Test command:
```powershell
.venv\Scripts\python -m pytest tests/test_phase36_bundle_robustness_round.py -q
```

### Step 4 — Implement the Output Validator
Create `scripts/validate_phase36_bundle_robustness_outputs.py` and `tests/test_validate_phase36_bundle_robustness_outputs.py`.

Validator must check:
- all required output artifacts exist
- all 4 bundle names are present in metrics and recommendation files
- stress grid contains exactly `10`, `20`, `30`
- recommendation file contains per-bundle decisions plus portfolio recommendation
- comparator snapshot passes

Validator command:
```powershell
.venv\Scripts\python scripts/validate_phase36_bundle_robustness_outputs.py `
  --output-dir data/processed/phase36_rule100/robustness
```

### Step 5 — Freeze Inputs for Audit
Reuse the evidence-gate audit pattern for robustness:

Before run:
```powershell
.venv\Scripts\python scripts/snapshot_phase36_comparator_integrity.py `
  --mode before `
  --output data/processed/phase36_rule100/robustness/robustness_comparator_snapshot.json
```

Create input manifest (new robustness-specific builder or cloned evidence-gate builder path):
```powershell
.venv\Scripts\python scripts/build_phase36_robustness_manifest.py `
  --output data/processed/phase36_rule100/robustness/robustness_input_manifest.json
```

### Step 6 — Run the Robustness Round
Execute the runner only after tests pass and the before-snapshot exists.

Run command:
```powershell
.venv\Scripts\python scripts/phase36_bundle_robustness_round.py `
  --features-path data/processed/features_phase35_repaired.parquet `
  --bundle-set data/processed/phase36_rule100/robustness/locked_bundle_set.json `
  --bundle-results data/processed/phase36_rule100/bundles_sweep_results.csv `
  --baseline-dir data/processed/phase35_reruns `
  --output-dir data/processed/phase36_rule100/robustness `
  --stress-grid-bps 10 20 30 `
  --calibration-start 2022-01-01 `
  --calibration-end 2023-06-30 `
  --validation-start 2023-07-01 `
  --validation-end 2024-03-31 `
  --holdout-start 2024-04-01 `
  --holdout-end 2024-12-31
```

### Step 7 — Validate Outputs and Comparator Integrity
Run validator:
```powershell
.venv\Scripts\python scripts/validate_phase36_bundle_robustness_outputs.py `
  --output-dir data/processed/phase36_rule100/robustness
```

Take after-snapshot:
```powershell
.venv\Scripts\python scripts/snapshot_phase36_comparator_integrity.py `
  --mode after `
  --output data/processed/phase36_rule100/robustness/robustness_comparator_snapshot.json
```

Run targeted tests:
```powershell
.venv\Scripts\python -m pytest tests/test_phase36_bundle_robustness_round.py tests/test_validate_phase36_bundle_robustness_outputs.py -q
```

### Step 8 — Publish Docs and SAW Closeout
Create:
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`

The executive summary must:
- state the portfolio-level `Continue / Pause / Pivot` decision
- list all 4 bundles without pre-ranking bias in the narrative lead
- keep research quarantine explicit
- state that `10 / 20 / 30` bps are diagnostic stress points, not a baseline rewrite

The technical report must:
- include base-case metrics
- include regime diagnostics from Phase 35 ledgers
- include friction stress outputs
- identify any killed bundles and why

The SAW report must be validator-clean and must not use production-deployment language.

---

## Recommendation Rubric

### Per-Bundle
- `Continue`: bundle stays positive on governed validation + holdout delta IC and survives robustness floor checks
- `Pivot`: bundle stays analytically interesting but loses robustness on stress or regime splits without a hard kill
- `Pause`: bundle fails the governed path, validator checks, or the robustness floor

### Portfolio-Level
- `Continue`: at least 3 of the 4 locked bundles land on `Continue`
- `Pivot`: exactly 2 bundles land on `Continue`, or the recommendation is mixed after stress diagnostics
- `Pause`: 0 or 1 bundles land on `Continue`, or audit / validator checks fail

### Hard Guardrail
- Do not upgrade the portfolio decision based on the single best bundle
- Do not downgrade solely because calibration mean delta IC is negative; keep calibration weakness diagnostic-only

---

## Definition of Done

All of the following must be true:
1. `docs/phase_brief/phase36-robustness-worker-execution-guide.md` is current
2. `scripts/phase36_bundle_robustness_round.py` exists and targeted tests pass
3. `scripts/validate_phase36_bundle_robustness_outputs.py` exists and targeted tests pass
4. `locked_bundle_set.json` exists with exactly 4 bundles
5. All robustness output artifacts exist under `data/processed/phase36_rule100/robustness/`
6. Comparator integrity snapshot passes before/after verification
7. Executive summary, technical report, SAW report, decision log, and lessons are updated
8. Research quarantine remains explicit; no production language appears in the round closeout

---

## Stop Conditions

Stop and report `BLOCK` if any of the following occur:
- locked bundle set is not exactly 4 bundles
- comparator snapshot shows mutation
- Phase 35 behavior ledgers are missing or unreadable
- stress grid output is missing one of `10`, `20`, `30`
- required helper reuse is impossible and a forked simulation path would be needed
- docs drift into production-promotion language

---

## Non-Blocking Out-of-Boundary Items

Record these, do not solve them here:
- S&P IQ / BvD credentials and legal entitlement
- Production promotion or integration into the live engine
- Runtime key migration away from `permno`
- Rewrite of the governed base-case transaction-cost model
- Live capital sizing or allocation
