# Phase 50: Shadow-Ship Readiness (Paper-Trading Equity Curve Only)

> Historical note: this guide locked the initial Phase 50 activation and early daily runway surfaces. The active handoff subsequently moved to `docs/phase_brief/phase50-final-gate-package-20260410.md`, and the formal Day 30 review later passed under `D-278`, authorizing shipping, accepting the reviewer-lane `503` availability risk, unlocking production-default usage, retiring the active Phase 50 paper-runway quarantines, and ending the daily memo chain. Phase 51 is now governance-unlocked for implementation, although this historical file does not edit its brief. Shared `docs/context/current_context.*` may still resolve to the parallel Phase 51 brief, but the authoritative Phase 50 historical closeout remains `docs/phase_brief/phase50-brief.md` plus the final memo.

**Status**: HISTORICAL AUTHORIZATION BASELINE (superseded for the current next-step handoff by the accelerated final gate package brief)
**Created**: 2026-03-11
**Authorization Source**: CEO disposition dated 2026-03-11 02:39 PDT
**Predecessor**: Phase 49 opened and closed in one docs-only reconciliation round; the Phase 48 shadow-evidence bundle was accepted as demo-only governance evidence for simulation-stage paper runway.

---

## 1. Scope and Active Boundary

This round authorizes a bounded Phase 50 paper-only surface:

- draft and publish the exact Phase 50 readiness brief
- seed a 30-day paper-trading curve from the accepted demo bundle
- generate Day 1 curve, telemetry, and gate-stub artifacts
- expose Phase 50 telemetry in the Elite Sovereign dashboard tab
- preserve explicit demo-only provenance in docs and logs

**What This Round Authorizes**
- `docs/phase_brief/phase50-shadow-ship-readiness.md`
- `docs/phase_brief/phase50-brief.md`
- `docs/phase_brief/phase50-final-gate-package-20260410.md`
- `docs/phase_brief/phase51-factor-algebra-design.md` as a downstream reference artifact; later governance unlocked implementation without editing that file here
- `scripts/run_phase50_paper_curve.py`
- `views/elite_sovereign_view.py`
- targeted tests for the new paper-curve and dashboard telemetry loaders
- canonical Phase 50 output artifacts under `data/processed/phase50_shadow_ship/`
- compatibility mirrors for CEO memo consumption at `data/shadow_evidence/` and `data/processed/phase50_gate/`
- same-round docs-as-code updates and SAW closeout

**What This Round Does NOT Authorize**
- live broker routing or order submission
- live capital deployment
- threshold rewrites
- `permno` migration
- governed `10` bps rewrite
- new sleeves
- vendor workaround
- production promotion

---

## 2. Governance-Locked Inputs

- Demo-only baseline evidence:
  - `docs/handover/phase48_shadow_evidence_review_20260311.md`
  - `data/shadow_evidence/daily_scanner_day1.json`
  - `data/shadow_evidence/telemetry_summary_5day.json`
  - `data/shadow_evidence/c3_delta_day1.json`
- Canonical bridge remains unchanged:
  - `docs/handover/sovereign_promotion_package_20260313.md`
- Hard blocks preserved:
  - no live capital
  - no broker submission
  - no threshold changes
  - no `permno` migration
  - no governed `10` bps rewrite
  - no new sleeves
  - no vendor workaround

---

## 3. Worker Guidance

### Harper — Documentation / Governance
- Own:
  - `docs/phase_brief/phase50-shadow-ship-readiness.md`
  - `docs/phase_brief/phase50-brief.md`
  - same-round governance notes and context routing
- Acceptance focus:
  - demo-only baseline is explicit
  - 30-day acceptance matrix is explicit
  - rollback gates and paper-only banner are explicit

### Benjamin — Paper Curve / Artifacts
- Own:
  - `scripts/run_phase50_paper_curve.py`
  - `data/processed/phase50_shadow_ship/`
  - compatibility mirror exports at `data/shadow_evidence/` and `data/processed/phase50_gate/`
- Acceptance focus:
  - Day 1 curve goes through `core.engine.run_simulation`
  - gate stub exists
  - telemetry records daily PnL, turnover, crisis-turnover, slippage, and active-days progress
  - canonical and compatibility artifacts stay byte-equivalent for mirrored payloads

### Lucas — Dashboard / Observability
- Own:
  - `views/elite_sovereign_view.py`
  - telemetry log visibility for Phase 50 artifacts
- Acceptance focus:
  - zero broker calls remains explicit
  - demo provenance note is visible
  - paper-curve telemetry columns render from bounded artifacts only

---

## 4. Authorized Write Surface

### Existing files
1. `docs/handover/phase48_shadow_evidence_review_20260311.md`
2. `docs/notes.md`
3. `docs/decision log.md`
4. `docs/lessonss.md`
5. `docs/context/current_context.json`
6. `docs/context/current_context.md`
7. `views/elite_sovereign_view.py`
8. `tests/test_elite_sovereign_view.py`

### Files to create or update
1. `docs/phase_brief/phase50-shadow-ship-readiness.md`
2. `docs/phase_brief/phase50-brief.md`
3. `docs/phase_brief/phase50-day5-worker-execution-guide.md`
4. `docs/handover/phase50_day1_ceo_memo_20260312.md`
5. `scripts/run_phase50_paper_curve.py`
6. `tests/test_phase50_paper_curve.py`
7. `docs/saw_reports/saw_phase50_shadow_ship_readiness_20260311.md`

### Generated outputs allowed in this round
1. `data/processed/phase50_shadow_ship/paper_curve_day1.csv`
2. `data/processed/phase50_shadow_ship/paper_curve_positions_day1.csv`
3. `data/processed/phase50_shadow_ship/telemetry_day1.json`
4. `data/processed/phase50_shadow_ship/gate_recommendation.json`
5. `data/shadow_evidence/paper_curve_day1.csv`
6. `data/shadow_evidence/telemetry_day1.json`
7. `data/processed/phase50_gate/gate_recommendation.json`
8. `data/telemetry/phase50_paper_curve_events.jsonl`

No other runtime, deployment, or broker surfaces are opened by this brief.

---

## 5. 30-Day Paper-Trading Acceptance Matrix

- `CHK-P50-01`: Day 1 curve uses `core.engine.run_simulation` rather than a standalone PnL formula.
- `CHK-P50-02`: Canonical Phase 50 outputs are written to `data/processed/phase50_shadow_ship/`; compatibility mirrors are emitted to the CEO memo paths without changing the canonical source of truth.
- `CHK-P50-03`: Day 1 telemetry includes `daily_pnl_pct`, `turnover`, `crisis_turnover`, `slippage_bps`, and `active_days_observed`.
- `CHK-P50-04`: Demo-only provenance is explicit in docs and in the Phase 50 telemetry payload.
- `CHK-P50-05`: Zero broker calls remain explicit (`status=SIMULATED`, `broker_calls_detected=0`).
- `CHK-P50-06`: Dashboard reads bounded Phase 50 artifacts and renders paper-curve telemetry without opening execution surfaces.
- `CHK-P50-07`: Rollback surface is documented and bounded.
- `CHK-P50-08`: Targeted tests pass.
- `CHK-P50-09`: Context packet rebuilds cleanly to active Phase 50 state.

### 30-Day Monitoring Expectations
- Daily curve update cadence: one simulated paper day per authorized run
- Equity target: monotonic monitoring only, not a promotion gate by itself
- Active-days tracker: report observed days vs `150` threshold every day
- Crisis-turnover: record daily value and compare against the demo baseline
- Turnover/slippage: report daily values and cumulative mean

---

## 6. Demo-Mode Modeling Contract

- Day 0 seed comes from the accepted demo bundle
- Day 1 paper curve is synthetic but deterministic and auditable
- No claim is made that the Day 1 curve reflects live market execution
- All artifacts must carry demo-only provenance language

### Explicit demo formulas
- `target_weight_i = sovereign_score_i / sum_j(sovereign_score_j)`
- `signal_edge_i = demand_i + pricing_i + margin_i - supply_i`
- `demo_return_i = clip((0.002 * signal_edge_i) + (0.0001 * hf_scalar_i) + regime_bias_i, -0.02, 0.02)`
- `regime_bias_i = 0.0004 if regime contains "Super Cycle", 0.0001 if regime contains "Turnaround", else 0.0`
- `day1_slippage_bps = mean(vol_constraint_i) * 50`
- `active_days_progress_to_threshold = active_days_observed / 150`

---

## 7. Validation Commands

```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
.venv\Scripts\python scripts\run_phase50_paper_curve.py
.venv\Scripts\python scripts\build_context_packet.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

---

## 8. Rollback Gates

Rollback is required if any of the following occur:
- a broker or live-capital surface is introduced
- Phase 50 artifacts are written outside the authorized canonical or compatibility output surfaces
- demo provenance disappears from docs or telemetry
- dashboard rendering tries to submit or imply execution
- targeted tests fail

### Exact Rollback Scope
- revert `scripts/run_phase50_paper_curve.py`
- revert `views/elite_sovereign_view.py`
- revert targeted tests
- revert same-round docs changes
- remove Phase 50 generated artifacts listed in Section 4

---

## 9. Hard Blocks

- No broker submission
- No live capital
- No threshold changes
- No production promotion
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves
- No vendor workaround
- No worker-opened future phase without explicit CEO sign-off in the decision log

---

## 10. Deliverables

- exact Phase 50 brief published
- Day 1 paper curve artifact
- Day 1 positions artifact
- Day 1 telemetry payload
- Phase 50 gate recommendation stub
- Phase 50 dashboard telemetry panel
- Day 1 CEO checkpoint memo
- same-round SAW closeout
