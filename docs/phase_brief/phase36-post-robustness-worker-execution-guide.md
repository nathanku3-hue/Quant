# Phase 36 Post-Robustness Worker Execution Guide

**Date**: 2026-03-09
**Round ID**: `P36-HO-01`
**Scope**: Governance review / PM handoff only for the frozen Phase 36 research packet
**Do Not Do**: start Phase 37 execution, promote to production, reopen Phase 35, change `permno`, rewrite the governed cost model, or wait on S&P IQ / BvD procurement

---

## Mission

Take the now-closed Phase 36 robustness packet and convert it into a governance-ready PM handoff package without reopening research execution.

This round is packaging, validation, and context-freeze work only. The worker must preserve the frozen artifact truth, refresh the project handoff/context surfaces, and stop at the approval boundary.

**Frozen packet truth**
- Portfolio decision: `Continue`
- Bundle split: `3 Continue / 1 Pause / 0 Pivot`
- Paused bundle: `bundle_quality_composite`
- Research quarantine: still in force

**Frozen source-of-truth docs**
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`

**Frozen source-of-truth artifacts**
- `data/processed/phase36_rule100/robustness/bundle_robustness_metrics.csv`
- `data/processed/phase36_rule100/robustness/bundle_robustness_recommendation.json`
- `data/processed/phase36_rule100/robustness/bundle_friction_stress.csv`
- `data/processed/phase36_rule100/robustness/robustness_input_manifest.json`
- `data/processed/phase36_rule100/robustness/robustness_comparator_snapshot.json`

**Governed comparator artifact**
- `data/processed/features_phase35_repaired.parquet`

**Governed windows**
- Calibration: `2022-01-01` -> `2023-06-30`
- Validation: `2023-07-01` -> `2024-03-31`
- Holdout: `2024-04-01` -> `2024-12-31`

---

## Scope Lock

### Allowed
- Read-only validation of the frozen robustness packet
- New PM handoff docs and context artifacts
- Brief / decision-log / lessons updates that preserve the frozen truth
- A new SAW closeout for the handoff round
- Phase-end validation commands if the worker is explicitly preparing a phase-close approval packet

### Forbidden
- Re-running signal discovery, evidence-gate, or robustness math unless a validator proves drift
- Editing `data/processed/features_phase35_repaired.parquet`
- Editing any robustness CSV/JSON/Parquet output to change economics or recommendations
- Adding new signals, new bundles, or new weighting schemes
- Any production-readiness, deployment, or live sizing language
- Any runtime identifier migration away from `permno`
- Any governed cost-model rewrite
- Waiting on vendor procurement before finishing the handoff packet

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase36-post-robustness-worker-execution-guide.md`
- `docs/handover/phase36_handover.md`
- `docs/saw_reports/saw_phase36_handover_20260309.md`

### Update
- `docs/phase_brief/phase36-brief.md`
- `docs/phase_brief/phase36-robustness-worker-execution-guide.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json` via `scripts/build_context_packet.py`
- `docs/context/current_context.md` via `scripts/build_context_packet.py`

### Read-Only Inputs
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`
- `docs/notes.md`
- `.codex/skills/saw/references/phase_end_handover_template.md`
- `scripts/build_context_packet.py`
- `launch.py`
- `tests/test_phase36_bundle_robustness_round.py`
- `tests/test_build_phase36_robustness_manifest.py`
- `tests/test_validate_phase36_bundle_robustness_outputs.py`

### Do Not Touch Unless a Validator Fails First
- `scripts/phase36_bundle_robustness_round.py`
- `scripts/validate_phase36_bundle_robustness_outputs.py`
- `data/processed/phase36_rule100/robustness/*`
- `strategies/phase36_bundle_registry.py`

---

## Execution Order

### Step 1 — Reconfirm the Frozen Packet
Before drafting new docs, rerun the frozen validation stack exactly as published.

Targeted robustness suite:
```powershell
.venv\Scripts\python -m pytest tests/test_phase36_bundle_robustness_round.py tests/test_build_phase36_robustness_manifest.py tests/test_validate_phase36_bundle_robustness_outputs.py -q
```

Robustness output validator:
```powershell
.venv\Scripts\python scripts/validate_phase36_bundle_robustness_outputs.py --output-dir data/processed/phase36_rule100/robustness
```

SAW block validator on the frozen robustness report:
```powershell
.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_phase36_robustness_20260308.md
```

Closure-packet validator on the frozen robustness report:
```powershell
$packet = Select-String -Path "docs/saw_reports/saw_phase36_robustness_20260308.md" -Pattern '^ClosurePacket:' | Select-Object -ExpandProperty Line
.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet $packet --require-open-risks-when-block --require-next-action-when-block
```

If any command fails, stop and publish `BLOCK`. Do not draft a handoff doc over a drifting packet.

### Step 2 — Build the PM Handover Artifact
Create `docs/handover/phase36_handover.md` using `.codex/skills/saw/references/phase_end_handover_template.md`.

The handover must include all required template blocks and must treat the robustness packet as the source of truth.

Minimum content requirements:
- **Executive Summary**
  - state that Phase 36 ends with a research-only `Continue` recommendation
  - state the truthful split `3 Continue / 1 Pause`
  - name `bundle_quality_composite` as paused due to the locked `20` bps holdout floor
- **Delivered Scope vs Deferred Scope**
  - delivered: Batch 1, bundle round, evidence gate, robustness round, generator/validator reconciliation
  - deferred: Batch 2 vendor enrichment, any production promotion, any runtime-key migration
- **Derivation and Formula Register**
  - cite the explicit friction formula from `docs/notes.md`
  - cite the `holdout_net_ic_at_20bps <= 0` fail-closed floor
  - cite the majority rubric (`Continue >= 3`, `Pause >= 3`, else `Pivot`)
- **Logic Chain**
  - `features_phase35_repaired.parquet -> bundle formulas -> robustness diagnostics -> majority rubric -> recommendation JSON`
- **Validation Evidence Matrix**
  - include the four frozen validation commands above
  - include any phase-end validation commands from Step 5 if run
- **Open Risks / Assumptions / Rollback**
  - keep research quarantine explicit
  - carry S&P IQ procurement as inherited
- **Next Phase Roadmap**
  - governance review
  - explicit `approve next phase` boundary
  - only then Phase 37 planning
- **New Context Packet**
  - what was done
  - what is locked
  - what remains
  - immediate first step
  - `ConfirmationRequired: YES`
  - `NextPhaseApproval: PENDING`
  - `Prompt: Reply "approve next phase" to start execution.`

### Step 3 — Refresh the Phase Brief and Governance Record
Update `docs/phase_brief/phase36-brief.md` so the active next milestone is the handoff round, not more engineering.

Required brief edits:
- add this new worker guide as the active next-step handoff
- add a governance-handoff acceptance block
- add the new PM handover artifact path
- keep the immediate next milestone at `governance review / PM handoff only`

Update `docs/decision log.md` with a new decision entry for the post-robustness handoff round.

Required decision points:
- the robustness packet is frozen as the source of truth
- the next worker is authorized to package and validate, not to extend the research scope
- no production promotion, no Phase 37 execution, and no comparator rewrites are allowed in this round

Update `docs/lessonss.md` with one entry that captures the transition guardrail.

Required lesson theme:
- once a governed packet is truly closed, the next worker must switch from execution mode to packaging mode and must not continue experimentation implicitly

### Step 4 — Refresh the `/new` Context Packet
Rebuild the context artifacts after the handoff doc and brief are current.

Build:
```powershell
.venv\Scripts\python scripts/build_context_packet.py
```

Validate:
```powershell
.venv\Scripts\python scripts/build_context_packet.py --validate
```

Done when both files exist and validate:
- `docs/context/current_context.json`
- `docs/context/current_context.md`

### Step 5 — Run the Phase-End Validation Sweep
This step is required if the worker is preparing a formal Phase 36 approval packet rather than an informal memo.

Full regression:
```powershell
.venv\Scripts\python -m pytest -q
```

Runtime smoke:
```powershell
.venv\Scripts\python launch.py
```

Interpretation rules:
- if full regression or smoke fails because of a new in-scope defect, publish `BLOCK`
- if an inherited unrelated failure appears, capture it under `Open Risks` with owner and target milestone before asking for approval
- do not silently downscope these checks once Phase 36 closeout is being requested

### Step 6 — Publish the Handoff SAW Report
Create `docs/saw_reports/saw_phase36_handover_20260309.md` for this docs/handoff round.

The SAW report must include:
- `SAW Verdict: PASS/BLOCK`
- ownership separation across implementer/reviewers
- findings table
- scope split summary
- document changes showing
- `ClosurePacket:` line
- `ClosureValidation:` line
- `SAWBlockValidation:` line

Validator commands:
```powershell
.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_phase36_handover_20260309.md
```

```powershell
$packet = Select-String -Path "docs/saw_reports/saw_phase36_handover_20260309.md" -Pattern '^ClosurePacket:' | Select-Object -ExpandProperty Line
.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet $packet --require-open-risks-when-block --require-next-action-when-block
```

---

## Phase 36 Approval Boundary

The worker must stop after packaging and validation.

### Explicit Boundary
- Allowed final state: `Phase 36 ready for governance review / PM handoff`
- Forbidden final state: `Phase 37 started`

### Approval Token Contract
Do not begin the next execution phase until an explicit approval token exists in-thread:
- approved: reply includes `approve next phase`
- not approved: anything else

---

## Definition of Done

All of the following must be true:
1. `docs/phase_brief/phase36-post-robustness-worker-execution-guide.md` exists and is current
2. Frozen robustness validators pass before any new handoff doc is published
3. `docs/handover/phase36_handover.md` exists and follows the phase-end handover template
4. `docs/phase_brief/phase36-brief.md` reflects governance-review-only next steps
5. `docs/decision log.md` and `docs/lessonss.md` are updated
6. `docs/context/current_context.json` and `docs/context/current_context.md` rebuild cleanly
7. `docs/saw_reports/saw_phase36_handover_20260309.md` is validator-clean
8. Research-only quarantine remains explicit in every new doc
9. No new research execution or production language appears in the round

---

## Stop Conditions

Stop and report `BLOCK` if any of the following occur:
- any frozen robustness validator fails
- the robustness packet no longer reconciles to `3 Continue / 1 Pause`
- the paused bundle is not `bundle_quality_composite`
- the context packet build or validate step fails
- the handover doc drifts into production-promotion or Phase 37 execution language
- full regression / smoke fails while a formal phase-close packet is being requested

---

## Non-Blocking Out-of-Boundary Items

Record these, do not solve them here:
- S&P IQ / BvD credentials and legal entitlement
- Production promotion or integration into the live engine
- Runtime key migration away from `permno`
- Rewrite of the governed base-case transaction-cost model
- Live capital sizing or allocation
- Phase 37 execution before explicit approval
