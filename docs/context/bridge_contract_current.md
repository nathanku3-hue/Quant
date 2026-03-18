# Bridge Contract - Current

Status: Current integration bridge  
Authority: advisory-only PM/planner bridge. This file does not authorize Phase 60 implementation, post-2022 audit execution, promotion, or scope widening beyond the `D-331` and `D-332` planning-only packets.  
Purpose: connect Quant's current technical closeout state back to planner truth and product/system truth.

## Header
- `BRIDGE_ID`: `20260318-phase60-system-bridge`
- `DATE_UTC`: `2026-03-18`
- `SCOPE`: `Phase 60 planning-only Stable Shadow kickoff`
- `STATUS`: `planning-only`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- Quant has strong phase briefs, review packets, and evidence artifacts, but it still needs one thin artifact that says what the system now means and what the planner should do next.

## Static Truth Inputs
- `top_level_PM.md`
- `README.md`
- `docs/decision log.md`
- `docs/phase_brief/phase60-brief.md`

## Live Truth Now
- `SYSTEM_NOW`: `Quant is currently a Multi-Sleeve Research Kernel plus Governance Stack with bounded Phase 56 / 57 / 58 / 59 evidence surfaces preserved as immutable SSOT and an active Phase 60 planning-only contract lock.`
- `ACTIVE_SCOPE`: `Phase 60 planning-only kickoff / contract-lock state.`
- `BLOCKED_SCOPE`: `Any Phase 60 implementation, any post-2022 audit execution, any production promotion, any research_data mutation, and any kernel mutation remain blocked.`

## What Changed This Round
- `SYSTEM_DELTA`: `The system now has an explicit Phase 60 planning-only contract set for the Stable Shadow roadmap step: unified governed comparator surface, governed cost policy, integrated post-2022 audit preflight, and allocator carry-forward exclusion. D-332 adds the Complete Institutional Pivot planning snapshot with validator fix as Priority #1, Method B locked for S&P/Moody's sidecars, and out-of-boundary ingestion block enforced.`
- `EXECUTION_DELTA`: `No execution occurred. The round published D-331, D-332, the Phase 60 planning brief with institutional pivot snapshot, the kickoff memo, and the refreshed planner bridge/context state while keeping implementation blocked.`
- `NO_CHANGE`: `Promotion is still blocked, prior sleeves remain immutable SSOT, RESEARCH_MAX_DATE = 2022-12-31 remains active, and the same-window / same-cost / same-engine discipline remains unchanged where comparator evidence applies.`

## PM / Product Delta
- `STRONGER_NOW`: `The repo now has one explicit planning contract for how a future Stable Shadow scope must be structured without inventing comparability or silently reopening the post-2022 seal. The Complete Institutional Pivot snapshot locks validator fix as Priority #1 and Method B as the planning default for S&P/Moody's sidecars.`
- `WEAKER_NOW`: `The governed daily holdings / weights cube is still a planning artifact only; no implementation or holdout evidence exists yet. Validator failures (14-day freshness gap + 2 zombie snapshot rows) remain uncleared.`
- `STILL_UNKNOWN`: `Whether a later explicit implementation packet will be granted after the Phase 60 planning brief is reviewed.`

## Planner Bridge
- `OPEN_DECISION`: `Should the bounded Phase 60 planning brief with Complete Institutional Pivot snapshot be accepted as the only valid contract for any later implementation packet?`
- `RECOMMENDED_NEXT_STEP`: `Clear validator failures (14-day freshness gap + 2 zombie snapshot rows) as Priority #1, review docs/phase_brief/phase60-brief.md, keep implementation blocked, and require a later explicit approve next phase token before any code or post-2022 audit run starts.`
- `WHY_THIS_NEXT`: `The planning-only round has now resolved the scope-choice ambiguity and locked the institutional pivot snapshot, so the correct next action is validator fix followed by governance review of the locked contracts rather than silent implementation drift.`
- `NOT_RECOMMENDED_NEXT`: `Do not implement the unified cube, do not run the post-2022 audit, and do not promote allocator or core-sleeve inputs without a later explicit implementation packet. Do not open any sidecar testing or data-milestone execution path until validator PASS is achieved.`

## Locked Boundaries
- `DO_NOT_REDECIDE`:
  - `Phase 59 is closed under D-330 as evidence-only / no promotion / no widening.`
  - `Prior sleeve / governance / shadow SSOT artifacts for Phases 55 / 56 / 57 / 58 / 59 remain immutable.`
  - `RESEARCH_MAX_DATE = 2022-12-31 and the same-window / same-cost / core.engine.run_simulation evidence gate remain active.`
- `BLOCKED_UNTIL`:
  - `Any Phase 60 implementation, stable shadow execution, or post-2022 audit execution requires a separate explicit approval packet.`
  - `Any scope that mutates research_data or reopens prior sleeves remains blocked.`
  - `Allocator carry-forward and core-sleeve promotion remain blocked until later approved eligibility evidence exists.`

## Evidence Used
- `docs/context/current_context.md`
- `docs/phase_brief/phase60-brief.md`
- `docs/handover/phase60_kickoff_memo_20260318.md`
- `data/processed/phase59_shadow_summary.json`
- `data/processed/phase58_governance_summary.json`
- `data/processed/phase54_core_sleeve_summary.json`
- `data/processed/phase55_allocator_cpcv_evidence.json`
- `README.md`

## Open Risks
- `Validator failures (14-day feature freshness gap + 2 zombie snapshot rows) remain uncleared and block reliable pipeline testing.`
- `Family-level governance still fails the 5% threshold (event_family_spa_p = 0.066, event_family_wrc_p = 0.086), so the event family is not yet promotion-ready.`
- `The core sleeve remains below promotion readiness (gates_passed = 4/6, rule100_pass_rate = 0.10132320319432121), so it can only be treated as a planning input.`
- `The allocator-selected variant remains negative on Sharpe / CAGR and allocator carry-forward is therefore excluded from governed use until eligibility clears.`
