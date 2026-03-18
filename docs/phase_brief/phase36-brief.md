# Phase 36: Governed Signal Discovery on Repaired Baseline

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: CLOSED (Governance review complete on 2026-03-09)
**Created**: 2026-03-08
**Phase 35 Status**: CLOSED on repaired `permno` path; W1/W2 no-go; Wave 3 blocked

---

## Objective

Run a governed signal-discovery phase on top of the repaired Phase 35 baseline without reopening the data layer or changing runtime identifiers.

The purpose of Phase 36 is to discover whether any single-factor or small-bundle candidates can beat the corrected baseline on the same path, same windows, and same cost discipline.

---

## Locked Comparator Contract

**Governed comparator artifact**
- `data/processed/features_phase35_repaired.parquet`

**Governed evaluation windows**
- Calibration: `2022-01-01` -> `2023-06-30`
- Validation: `2023-07-01` -> `2024-03-31`
- Holdout: `2024-04-01` -> `2024-12-31`

**Warmup only**
- `2020-01-01` -> `2021-12-31`

**Path discipline**
- Same repaired `permno` evidence path only
- Same `engine.run_simulation` evaluation path only
- Same friction/cost assumptions only
- No production promotion decisions in this phase

---

## Scope Boundary

### In Scope
1. Create a dedicated Phase 36 candidate registry outside `strategies/factor_specs.py`
2. Run a broad Rule-of-100 style candidate sweep in governed research mode
3. Execute single-factor ablations first on the repaired baseline
4. Promote survivors only into small 2-4 factor research bundles
5. Probe S&P IQ API capability in parallel without blocking the core sweep
6. Publish evidence docs and SAW closeout for each execution round

### Explicitly Out of Scope
1. Reopening Phase 35 evidence or unblocking Wave 3
2. Migrating runtime identifiers away from `permno`
3. Full S&P IQ or BvD ingestion buildout
4. Any production promotion or live-engine merge decision
5. Any change to the governed comparator artifact other than read-only usage

---

## Final Execution Locks

1. **Registry footprint locked**
   - Scaffold the full Rule-of-100 registry structure in `strategies/phase36_candidate_registry.py`
   - Execute only the currently runnable `20-30` `ready_now` candidates in Batch 1
   - Do not wait for vendor-dependent candidates before starting the sweep

2. **S&P IQ depth locked**
   - Build only a lightweight capability probe plus interface scaffold in `scripts/signal_sweep_runner.py` sidecar flow and `scripts/probe_spiq_api.py`
   - Do not build heavy ingestion/orchestrator integration in Phase 36

3. **Bundle promotion policy locked**
   - Promotion is threshold-based, not rank-based
   - A candidate must show a positive, statistically defensible delta versus the corrected baseline in both validation and holdout to earn a bundle slot
   - Never promote by arbitrary `Top-N` rank alone

There are no remaining low-certainty items on the critical execution path.

---

## Post-Evidence-Gate Locks

1. **Locked survivor set**
   - Freeze exactly these 4 research bundles for the robustness round:
     - `bundle_quality_vol`
     - `bundle_quality_composite`
     - `bundle_vol_composite`
     - `bundle_all_three`
   - Do not add new bundles, reweight bundles, or pre-rank them before robustness diagnostics complete

2. **Robustness diagnostics depth locked**
   - Run the robustness round on the exact same repaired `permno` path and the exact same governed windows
   - Reuse Phase 35 behavior-ledger daily labels for regime diagnostics; do not introduce a new regime model in this round
   - Keep negative average calibration delta IC diagnostic-only; it is not a new kill switch

3. **Friction stress grid locked**
   - Use a compact diagnostic stress grid of `10 / 20 / 30` bps only
   - Do not expand to finer-grained stress points such as `15` or `25` bps
   - Do not reinterpret the governed base-case comparator path; this grid is diagnostic only and must not rewrite the primary baseline contract

4. **Portfolio recommendation rule locked**
   - Use a majority-based rubric with a fail-closed floor
   - Portfolio recommendation may be `Continue`, `Pause`, or `Pivot`
   - No single best-bundle shortcut is allowed; final recommendation must reflect robustness across the frozen 4-bundle set

---

## Acceptance Criteria

### Round 1 — Registry + Sweep Scaffold
- `strategies/phase36_candidate_registry.py` exists with a full Rule-of-100 schema footprint
- `scripts/signal_sweep_runner.py` exists
- `tests/test_phase36_candidate_registry.py` passes
- `tests/test_signal_sweep_runner.py` passes
- `docs/phase36_rule100_registry.md` exists
- `docs/phase_brief/phase36-worker-execution-guide.md` exists

### Round 2 — Smoke Evidence
- Smoke sweep runs on `3-5` ready-now candidates
- Outputs are written under `data/processed/phase36_rule100/`
- Report compares each candidate vs corrected baseline on the same governed windows
- No writes occur to governed Phase 35 comparator artifacts

### Round 3 — Batch 1 Evidence
- Active batch of `20-30` ready-now candidates executes
- Single-factor results are ranked and documented
- Survivors are explicitly tagged for bundle round
- SAW closes the round with `PASS`, `BLOCK`, or `ADVISORY_PASS`

### Round 4 — Evidence Gate
- Locked bundle evidence gate executes on the governed path
- Executive summary and technical appendix are published
- SAW report is validator-clean
- Bundle recommendation stays research-only with production quarantine explicit

### Round 5 — Robustness Round
- `docs/phase_brief/phase36-robustness-worker-execution-guide.md` exists
- `scripts/phase36_bundle_robustness_round.py` exists
- `tests/test_phase36_bundle_robustness_round.py` passes
- `scripts/validate_phase36_bundle_robustness_outputs.py` exists
- Stress diagnostics publish `10 / 20 / 30` bps outputs under `data/processed/phase36_rule100/robustness/`
- Final recommendation uses the locked `Continue / Pause / Pivot` rubric with majority logic and fail-closed floor behavior documented

### Round 6 — Governance Handoff
- `docs/phase_brief/phase36-post-robustness-worker-execution-guide.md` exists
- `docs/handover/phase36_handover.md` exists
- Frozen robustness validators pass before handoff publication
- `scripts/build_context_packet.py --validate` passes after handoff docs refresh
- Any new handoff SAW report is validator-clean
- No new research execution begins without explicit next-phase approval

---

## Target Artifacts

### New Code
- `strategies/phase36_candidate_registry.py`
- `scripts/signal_sweep_runner.py`
- `scripts/probe_spiq_api.py`
- `tests/test_phase36_candidate_registry.py`
- `tests/test_signal_sweep_runner.py`

### New Docs
- `docs/phase36_rule100_registry.md`
- `docs/spiq_capability_report.md`
- `docs/phase_brief/phase36-worker-execution-guide.md`
- `docs/phase_brief/phase36-batch1-report.md`
- `docs/phase_brief/phase36-robustness-worker-execution-guide.md`
- `docs/phase_brief/phase36-post-robustness-worker-execution-guide.md`
- `docs/handover/phase36_handover.md`
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`
- `docs/saw_reports/saw_phase36_handover_20260309.md`

### New Data / Outputs
- `data/processed/phase36_rule100/registry_snapshot.json`
- `data/processed/phase36_rule100/single_factor_smoke_summary.parquet`
- `data/processed/phase36_rule100/single_factor_batch1_summary.parquet`
- `data/processed/phase36_rule100/candidate_reports/`
- `data/processed/phase36_rule100/robustness/locked_bundle_set.json`
- `data/processed/phase36_rule100/robustness/bundle_robustness_metrics.csv`
- `data/processed/phase36_rule100/robustness/bundle_robustness_metrics.json`
- `data/processed/phase36_rule100/robustness/bundle_regime_robustness.csv`
- `data/processed/phase36_rule100/robustness/bundle_friction_stress.csv`
- `data/processed/phase36_rule100/robustness/bundle_equity_curves.parquet`
- `data/processed/phase36_rule100/robustness/bundle_robustness_recommendation.json`
- `data/processed/phase36_rule100/robustness/robustness_input_manifest.json`
- `data/processed/phase36_rule100/robustness/robustness_comparator_snapshot.json`

---

## Execution Order

1. Freeze comparator contract and result directories
2. Build dedicated Phase 36 candidate registry with full Rule-of-100 scaffold
3. Build `scripts/signal_sweep_runner.py`
4. Add registry and runner tests
5. Run smoke sweep on `3-5` ready-now candidates
6. Publish smoke evidence
7. Run Batch 1 on the currently runnable `20-30` ready-now candidates
8. Probe S&P IQ API in parallel
9. Publish Phase 36 batch-1 report
10. Run SAW and close the round

---

## Operational Guardrails

- Use `.venv\Scripts\python` only
- Treat `data/processed/features_phase35_repaired.parquet` as read-only
- Keep all Phase 36 outputs under `data/processed/phase36_rule100/`
- Keep all Phase 36 docs under `docs/phase_brief/` or `docs/`
- Do not add unproven candidates into `strategies/factor_specs.py`
- Do not modify runtime key contracts (`permno` stays governed)
- Do not wait on procurement/legal to start discovery work

---

## Live Loop State

**Current state**
- Data layer: closed and trusted
- Phase 35: closed/no-go on repaired reruns
- Phase 36 Batch 1: closed with 30 single-factor candidates and 3 frozen survivors
- Phase 36 bundle round: closed with 4/4 research bundles and populated baseline deltas
- Phase 36 evidence gate: closed with Continue recommendation and research quarantine intact
- Phase 36 robustness round: closed with portfolio `Continue`, vote split `3 Continue / 1 Pause`, and the locked `20` bps holdout fail-closed floor enforced on `bundle_quality_composite`

**Immediate next milestone**
- Review `docs/phase_brief/phase37-brief.md` as a dormant planning skeleton for the 3 surviving bundles; do not start Phase 37 execution, production promotion, runtime-key migration, or cost-model changes until the structure is explicitly reviewed and approved


