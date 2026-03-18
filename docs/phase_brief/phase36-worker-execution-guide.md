# Phase 36 Worker Execution Guide

> Historical note: this guide is the Batch 1 discovery/scaffold contract. The active next-step handoff is now `docs/phase_brief/phase36-robustness-worker-execution-guide.md` for the locked 4-bundle robustness round.

**Date**: 2026-03-08
**Scope**: Governed signal discovery only
**Do Not Do**: reopen Phase 35, unblock Wave 3, migrate identifiers, or promote to production

---

## Mission

Discover whether any new candidate signals beat the corrected baseline using the repaired `permno` evidence path and the exact same governed windows.

**Comparator artifact**
- `data/processed/features_phase35_repaired.parquet`

**Governed windows**
- Calibration: `2022-01-01` -> `2023-06-30`
- Validation: `2023-07-01` -> `2024-03-31`
- Holdout: `2024-04-01` -> `2024-12-31`

---

## Scope Lock

### Allowed
- New Phase 36 registry files
- New Phase 36 runner files
- New Phase 36 tests
- New Phase 36 docs
- New Phase 36 outputs under `data/processed/phase36_rule100/`
- Parallel S&P IQ capability probe scaffold

### Forbidden
- Editing governed Phase 35 evidence outputs
- Editing `strategies/factor_specs.py` to add research candidates
- Reclassifying shadow `gvkey/iid` artifacts as governed
- Changing runtime identifier contracts away from `permno`
- Any production promotion language or decisions

---

## File Ownership for This Round

### Create
- `docs/phase36_rule100_registry.md`
- `docs/spiq_capability_report.md`
- `scripts/signal_sweep_runner.py`
- `scripts/probe_spiq_api.py`
- `strategies/phase36_candidate_registry.py`
- `tests/test_phase36_candidate_registry.py`
- `tests/test_signal_sweep_runner.py`

### Update
- `docs/phase_brief/phase36-brief.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/notes.md` only if explicit formulas or scoring rules are introduced in code

### Do Not Touch Unless Required by Test Fix
- `strategies/factor_specs.py`
- `strategies/company_scorecard.py`
- `scripts/generate_phase34_factor_scores.py`
- `scripts/attribution_report.py`
- `data/processed/features_phase35_repaired.parquet`

---

## Execution Order

### Step 1 — Freeze Working Directories
Create these output locations if missing:
- `data/processed/phase36_rule100/`
- `data/processed/phase36_rule100/candidate_reports/`

PowerShell:
```powershell
New-Item -ItemType Directory -Force "data/processed/phase36_rule100" | Out-Null
New-Item -ItemType Directory -Force "data/processed/phase36_rule100/candidate_reports" | Out-Null
```

### Step 2 — Build Candidate Registry
Create `strategies/phase36_candidate_registry.py`.

Minimum contract:
- define a `CandidateSpec` dataclass
- keep registry separate from production presets
- tag each candidate with one of:
  - `ready_now`
  - `needs_vendor`
  - `blocked`
- include factor family grouping:
  - momentum
  - quality
  - value
  - accruals
  - operating_leverage
  - analyst_revision
  - capital_discipline
  - liquidity / risk
- expose helpers:
  - `build_phase36_registry()`
  - `get_ready_now_candidates()`
  - `get_vendor_candidates()`
  - `registry_snapshot()`

Acceptance check:
- full Rule-of-100 schema footprint exists even if some candidates are vendor-blocked
- active batch returns the currently runnable `20-30` `ready_now` candidates if available
- registry explicitly tags every candidate as `ready_now`, `needs_vendor`, or `blocked`

### Step 3 — Build Single-Factor Sweep Runner
Create `scripts/signal_sweep_runner.py`.

Minimum contract:
- input features path defaults to `data/processed/features_phase35_repaired.parquet`
- runner consumes only Phase 36 registry entries
- executes one candidate at a time
- writes summary outputs under `data/processed/phase36_rule100/`
- compares each candidate against corrected baseline on the same windows
- preserves strict same-path comparator logic
- fails closed if required source columns are missing
- implements threshold-based promotion logic for later bundle eligibility
- never promotes by arbitrary `Top-N` rank alone

Required CLI shape:
```powershell
.venv\Scripts\python scripts/signal_sweep_runner.py `
  --features-path data/processed/features_phase35_repaired.parquet `
  --batch ACTIVE_BATCH_1 `
  --calibration-start 2022-01-01 `
  --calibration-end 2023-06-30 `
  --validation-start 2023-07-01 `
  --validation-end 2024-03-31 `
  --holdout-start 2024-04-01 `
  --holdout-end 2024-12-31 `
  --output-dir data/processed/phase36_rule100
```

### Step 4 — Add Tests Before Sweep
Create:
- `tests/test_phase36_candidate_registry.py`
- `tests/test_signal_sweep_runner.py`

Minimum coverage:
- registry returns only recognized statuses
- ready-now batch excludes vendor-only candidates
- runner fails closed on missing columns
- runner does not mutate comparator artifact
- runner emits deterministic summary schema
- promotion tagging is threshold-based and never rank-only

Test command:
```powershell
.venv\Scripts\python -m pytest tests/test_phase36_candidate_registry.py tests/test_signal_sweep_runner.py -q
```

### Step 5 — Publish Registry Doc
Create `docs/phase36_rule100_registry.md`.

Must include:
- candidate families
- readiness status
- required source columns
- vendor dependency flag
- first active batch list
- explicit note that `factor_specs.py` remains unchanged until promotion phase

### Step 6 — Smoke Sweep (3-5 Candidates)
Run a smoke sweep on a small ready-now subset first.

Example command:
```powershell
.venv\Scripts\python scripts/signal_sweep_runner.py `
  --features-path data/processed/features_phase35_repaired.parquet `
  --candidates mom_12m quality_composite realized_vol_21d illiq_21d `
  --calibration-start 2022-01-01 `
  --calibration-end 2023-06-30 `
  --validation-start 2023-07-01 `
  --validation-end 2024-03-31 `
  --holdout-start 2024-04-01 `
  --holdout-end 2024-12-31 `
  --output-dir data/processed/phase36_rule100
```

Smoke round done when:
- summary file exists
- candidate reports exist
- same-window baseline comparison is documented
- no governed Phase 35 artifacts were modified

### Step 7 — Batch 1 Active Sweep
Run the first active batch of the currently runnable `20-30` `ready_now` candidates.

Example command:
```powershell
.venv\Scripts\python scripts/signal_sweep_runner.py `
  --features-path data/processed/features_phase35_repaired.parquet `
  --batch ACTIVE_BATCH_1 `
  --calibration-start 2022-01-01 `
  --calibration-end 2023-06-30 `
  --validation-start 2023-07-01 `
  --validation-end 2024-03-31 `
  --holdout-start 2024-04-01 `
  --holdout-end 2024-12-31 `
  --output-dir data/processed/phase36_rule100
```

Batch 1 done when:
- `data/processed/phase36_rule100/single_factor_batch1_summary.parquet` exists
- survivors are tagged by threshold-based eligibility, not raw rank order
- weak candidates are explicitly rejected
- report written to `docs/phase_brief/phase36-batch1-report.md`

### Step 8 — Parallel S&P IQ Capability Probe
Create `scripts/probe_spiq_api.py` and `docs/spiq_capability_report.md`.

Purpose:
- capability probe only
- no full ingestion buildout
- no blocking dependency on credentials

Required behavior:
- if credentials exist, attempt auth + small sample pull
- if credentials do not exist, emit blocked report with expected interface contract
- do not block the registry/sweep path

Example command:
```powershell
.venv\Scripts\python scripts/probe_spiq_api.py `
  --sample-size 50 `
  --start-date 2024-01-01 `
  --end-date 2024-12-31 `
  --report docs/spiq_capability_report.md
```

---

## Definition of Done for This Round

All of the following must be true:
1. `docs/phase_brief/phase36-brief.md` is current
2. Registry module exists and is tested
3. Sweep runner exists and is tested
4. Smoke sweep has executed on repaired baseline
5. Batch 1 plan is runnable or already executed
6. S&P IQ capability probe exists and does not block research path
7. `docs/decision log.md` updated
8. `docs/lessonss.md` updated
9. SAW round published

---

## Non-Blocking Open Items

These remain out of boundary for the worker and should be recorded, not solved here:
- S&P IQ production credentials and legal entitlement
- BvD / Orbis production entitlement
- Production promotion of any new factor
- Runtime identifier migration away from `permno`

---

## Stop Conditions

Stop and escalate only if one of these occurs:
1. `data/processed/features_phase35_repaired.parquet` is missing or corrupted
2. governed-window evaluation cannot be reproduced on the repaired path
3. runner requires production-path edits to execute
4. candidate registry cannot populate even a minimal smoke batch from current data
5. tests fail on comparator integrity or same-path evaluation discipline
