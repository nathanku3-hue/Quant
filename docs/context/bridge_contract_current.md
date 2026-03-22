# Bridge Contract - Current

Status: Current integration bridge
Authority: advisory-only PM/planner bridge. This file reflects the bounded `D-348` / `D-350` / `D-351` Phase 61 remediation packet and the reconciled current truth surfaces. It does not authorize promotion, allocator carry-forward, core inclusion, or widening beyond the bounded sidecar/view-layer slice.
Purpose: connect Quant's current technical state back to planner truth and product/system truth.

## Header
- `BRIDGE_ID`: `20260322-phase61-d351-system-bridge`
- `DATE_UTC`: `2026-03-22`
- `SCOPE`: `Phase 61 complete - comparator remediation bounded and KS-03 cleared`
- `STATUS`: `complete-bounded-ks03-cleared`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- Quant has strong phase briefs, review packets, and evidence artifacts, but it still needs one thin artifact that says what the system now means and what the planner should do next after the `D-351` repair path.

## Static Truth Inputs
- `top_level_PM.md`
- `README.md`
- `docs/decision log.md`
- `docs/phase_brief/phase61-brief.md`

## Live Truth Now
- `SYSTEM_NOW`: `Quant is currently a Multi-Sleeve Research Kernel plus Governance Stack with immutable Phase 56 / 57 / 58 / 59 / 60 evidence surfaces preserved as SSOT and a completed bounded Phase 61 comparator-remediation packet whose governed audit now returns status = ok after sidecar overlay plus post-coverage feature masking.`
- `ACTIVE_SCOPE`: `Phase 61 is complete; the current packet set now reflects the cleared KS-03 state and bounded provenance risks.`
- `BLOCKED_SCOPE`: `Any production promotion, allocator carry-forward, core inclusion, research_data mutation, core/engine.py mutation, or widening beyond the bounded sidecar/view-layer slice remains blocked until the next explicit packet.`

## What Changed This Round
- `SYSTEM_DELTA`: `The system moved from a Phase 60 blocked hold to a Phase 61 completed bounded remediation path. KS-03 is cleared and the governed audit now returns ok without kernel mutation.`
- `EXECUTION_DELTA`: `The repo hardened the raw-tape ingest path, overlaid bounded sidecar returns into the governed audit, masked post-coverage feature rows, and refreshed stale current truth surfaces to match that result.`
- `NO_CHANGE`: `Promotion is still blocked, prior sleeves remain immutable SSOT, RESEARCH_MAX_DATE = 2022-12-31 remains active, and the same-window / same-cost / same-engine discipline remains unchanged where comparator evidence applies.`

## PM / Product Delta
- `STRONGER_NOW`: `The same-period comparator failure is no longer the active system blocker: Phase 61 proved the bounded repair path and the governed audit now reports status = ok with empty kill_switches_triggered.`
- `WEAKER_NOW`: `Live WRDS authentication still fails with PAM rejection, so the repo currently relies on a bounded bedrock fallback for the sidecar provenance chain.`
- `STILL_UNKNOWN`: `Which next explicit packet should be prioritized after the comparator repair: frontend shell consolidation, execution-boundary hardening, or another bounded product-hardening slice.`

## Planner Bridge
- `OPEN_DECISION`: `Should the next explicit packet prioritize frontend shell consolidation or execution-boundary hardening now that KS-03 is cleared?`
- `RECOMMENDED_NEXT_STEP`: `Treat Phase 61 as the new cleared comparator baseline, keep the V1 research kernel unchanged, and start the next platform-hardening phase with frontend shell consolidation before broader runtime expansion.`
- `WHY_THIS_NEXT`: `The highest remaining risk is no longer comparator correctness; it is state drift and operator-shell debt. Frontend shell consolidation reduces future truth-surface drift while keeping the repaired backend path stable.`
- `NOT_RECOMMENDED_NEXT`: `Do not reopen core-engine mutation proposals, do not treat Phase 61 completion as promotion authority, and do not widen into live trading or allocator/core-sleeve promotion without a new explicit packet.`

## Locked Boundaries
- `DO_NOT_REDECIDE`:
  - `Phase 59 remains closed as evidence-only / no promotion / no widening.`
  - `Prior sleeve / governance / shadow SSOT artifacts for Phases 55 / 56 / 57 / 58 / 59 / 60 remain immutable.`
  - `RESEARCH_MAX_DATE = 2022-12-31 and the same-window / same-cost / core.engine.run_simulation evidence gate remain active.`
- `BLOCKED_UNTIL`:
  - `Any promotion, live-routing widening, allocator carry-forward, core inclusion, or post-Phase-61 scope requires a separate explicit packet.`
  - `Any scope that mutates research_data or core/engine.py remains blocked.`
  - `Fresh vendor-side provenance for the sidecar remains pending successful WRDS auth or a delivered raw-tape export.`

## Evidence Used
- `docs/context/current_context.md`
- `docs/phase_brief/phase61-brief.md`
- `docs/saw_reports/saw_phase61_d349_sp500_pro_sidecar_20260320.md`
- `docs/saw_reports/saw_phase61_d350_tape_ingest_block_20260320.md`
- `docs/saw_reports/saw_phase61_d350_wrds_tape_20260319.md`
- `docs/context/e2e_evidence/phase61_d350_wrds_pivot_20260319_summary.json`
- `docs/context/e2e_evidence/phase61_sp500_pro_tape_block_20260320.json`
- `README.md`

## Open Risks
- `Live WRDS authentication still fails with PAM rejection, so future extractions may require account recovery or a later vendor rerun.`
- `The current sidecar provenance chain is bounded but indirect because the cleared KS-03 path used bedrock fallback data rather than a fresh WRDS pull.`
- `Allocator carry-forward remains blocked because its eligibility metrics are still negative.`
- `The core sleeve remains below promotion readiness and cannot be promoted from the cleared comparator alone.`
