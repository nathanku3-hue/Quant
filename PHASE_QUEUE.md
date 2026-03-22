# PHASE_QUEUE.md — Terminal Zero Worker Pickup List

Status: ACTIVE
Authority: Terminal Zero v2.6 Roadmap (`docs/roadmap/terminal_zero_v2.6.md`)
Last Updated: 2026-03-23
Baseline: Phase 61 COMPLETE / KS-03 CLEARED (committed as b266870, pushed to origin/main)

---

## How to Use This File

1. Pick the first phase with status `READY`.
2. Change its status to `IN_PROGRESS` and add your name/agent-id.
3. Write the phase brief at `docs/phase_brief/phaseNN-brief.md`.
4. Execute. Run tests. Publish SAW report.
5. Update status to `DONE` with evidence references.
6. Check if the next phase is unblocked.

---

## Tier 1: Platform Hardening + ML Skeleton

### Phase 62 — Frontend Shell Consolidation
- **Status**: READY
- **Blocked by**: —
- **Emphasis**: Frontend 70 / Backend 20 / Docs 10
- **Scope**:
  - Break `dashboard.py` (2084 lines) into `shell_frame.py`, `route_registry.py`, `shared_loaders.py`
  - Keep existing 8 view modules, wire through route registry
  - Move packet reads / status banners into shared loader layer
- **Exit Criteria**:
  - `dashboard.py` < 400 lines
  - All views load through route registry
  - Streamlit smoke test passes
  - No functional regression in existing views
- **Owner**: _unclaimed_

### Phase 63 — Execution Boundary Hardening
- **Status**: QUEUED
- **Blocked by**: Phase 62
- **Emphasis**: Backend 80 / Frontend 20
- **Scope**:
  - Extract scheduling / reconciliation / subprocess from `main_bot_orchestrator.py` (1556 lines → < 600)
  - Define `BrokerPort` interface: `submit_order()`, `cancel_order()`, `get_positions()`, `get_account()`
  - Extract telemetry spool from `execution/microstructure.py` (2122 lines)
  - Ensure no direct Alpaca imports outside `execution/broker_api.py`
  - Add contract tests for `BrokerPort`
- **Exit Criteria**:
  - Orchestrator < 600 lines
  - `BrokerPort` interface defined and tested
  - All execution tests green
  - Zero Alpaca imports outside `broker_api.py`
- **Owner**: _unclaimed_

### Phase 64 — Data Provenance Hardening
- **Status**: QUEUED
- **Blocked by**: Phase 63
- **Emphasis**: Backend/Data 85 / Frontend 15
- **Scope**:
  - Add provenance manifest to every sidecar parquet (source, extraction date, row count, hash)
  - Surface provenance state in operator shell (green/amber/red per data source)
  - Complete Method B sidecar integration for S&P 500 Pro / Moody's Orbis
  - WRDS: resolve PAM auth or formally retire with documented fallback
- **Exit Criteria**:
  - Every canonical data artifact has provenance manifest
  - Shell shows data-source health indicators
  - WRDS resolved or retired with D-log decision
- **Owner**: _unclaimed_

### Phase 65 — MLOps Skeleton
- **Status**: QUEUED
- **Blocked by**: Phase 64
- **Emphasis**: Backend 70 / ML 30
- **Scope**:
  - Deploy experiment tracking (MLflow or lightweight equivalent)
  - Model versioning with artifact store in `v2_discovery/mlops/`
  - Meta-labeling prototype on existing PEAD feature set
  - Data isolation tests: verify ML artifacts never write to V1 canonical paths
- **Exit Criteria**:
  - MLOps skeleton operational
  - Tied to SAW governance logs
  - Data isolation hygiene tests passing
  - `v2_discovery/mlops/` directory structure established
- **Owner**: _unclaimed_

---

## Tier 2: Core V2 Discovery Pipeline (Non-ML Baseline)

### Phase 66 — V2 Scaffold & Candidate Registry
- **Status**: QUEUED
- **Blocked by**: Phase 65
- **Emphasis**: Backend 80 / Docs 20
- **Scope**:
  - Create `v2_discovery/` package structure
  - Build candidate registry (SQLite or Parquet)
  - Columns: `candidate_id`, `family`, `parent_id`, `data_snapshot`, `feature_hash`, `metrics`, `status`, `created_at`
  - Statuses: `generated → screened_out | incubating → replicated → queued_for_v1 → promoted | rejected | retired`
  - Define promotion packet JSON schema (per `docs/architecture/v1_v2_boundary.md`)
- **Exit Criteria**:
  - Registry operational
  - One dummy candidate round-trips through all statuses
  - Promotion packet schema validated
- **Owner**: _unclaimed_

### Phase 67 — Fast Proxy Simulator
- **Status**: QUEUED
- **Blocked by**: Phase 66
- **Emphasis**: Backend 90 / Frontend 10
- **Scope**:
  - Vectorized approximate backtest in `v2_discovery/fast_sim/`
  - Screening-grade only, ~10x faster than `engine.py`
  - Supports: long-only equity, daily rebalance, approximate costs, basic turnover
  - Cannot claim promotion readiness from proxy results (enforced by schema)
- **Exit Criteria**:
  - Proxy sim produces Sharpe/CAGR/turnover for 1000+ candidates in < 10 min on local hardware
- **Owner**: _unclaimed_

### Phase 68 — PEAD Variant Expansion (Pilot Family)
- **Status**: QUEUED
- **Blocked by**: Phase 67
- **Emphasis**: Research 70 / Backend 30
- **Scope**:
  - Seed from PEAD sleeve (Phase 56: Sharpe 0.63, CAGR 10.9%)
  - Generate 50–200 variants: analyst-revision interactions, delayed entry, alternative holding periods, regime-conditioned, sector-neutral
  - Screen through proxy sim, kill bottom 90%
  - Top 5–10 through robustness mini-lab (alternate windows, costs, universes)
  - Export top 1–3 as formal promotion packets
- **Exit Criteria**:
  - At least 1 PEAD variant promotion packet submitted to V1
- **Owner**: _unclaimed_

### Phase 69 — V1 Promotion Pipeline + Nautilus Spike Decision
- **Status**: QUEUED
- **Blocked by**: Phase 68
- **Emphasis**: Backend 60 / Governance 40
- **Scope**:
  - Build V1 intake handler: receive packet → validate schema → run official `engine.py` backtest → apply gate checks (SPA/WRC/PBO/DSR)
  - Record verdict in D-log
  - Accepted → approved sleeve registry + shadow monitoring
  - Rejected → reason recorded, candidate returned to V2
  - **Decision point**: evaluate Nautilus adapter spike (proceed to Phase 69b or defer)
- **Exit Criteria**:
  - One real candidate processed end-to-end through V1 intake
  - Verdict recorded in D-log
  - Nautilus decision recorded
- **Owner**: _unclaimed_

---

## Tier 3: AI-Augmented Discovery Ramp

### Phase 70 — Discovery Dashboard & ML Hooks
- **Status**: QUEUED
- **Blocked by**: Phase 69
- **Emphasis**: Frontend 70 / Backend 30
- **Scope**:
  - Add "Discovery" view to operator shell
  - Show: candidate registry status, family summaries, survival rates, proxy vs official comparisons
  - Activate lightweight ML feature extraction stubs in V2 generators
- **Exit Criteria**:
  - Researcher can see full candidate pipeline in shell
- **Owner**: _unclaimed_

### Phase 71 — LLM/Agent-Assisted Hypothesis Generation
- **Status**: QUEUED
- **Blocked by**: Phase 70
- **Emphasis**: ML 70 / Backend 30
- **Scope**:
  - LLM-assisted hypothesis generation as primary discovery channel
  - AutoML framework for rapid feature discovery
  - Mandatory meta-labeling and economic sanity filters
- **Exit Criteria**:
  - ML-generated candidates entering registry
- **Owner**: _unclaimed_

### Phase 72 — Genetic Programming & Distributed Compute
- **Status**: QUEUED
- **Blocked by**: Phase 71
- **Emphasis**: ML 80 / Infra 20
- **Scope**:
  - Genetic programming on distributed clusters (Ray/Kubernetes)
  - Combinatorial feature crosses and symbolic rule search
- **Exit Criteria**:
  - Distributed pipeline operational, candidates flowing
- **Owner**: _unclaimed_

### Phase 73 — DRL Spike (Prove or Kill)
- **Status**: QUEUED
- **Blocked by**: Phase 72
- **Emphasis**: Research 90 / Governance 10
- **Scope**:
  - Deep Reinforcement Learning for portfolio allocation — bounded research spike
  - NOT approved for standard promotion pipeline
- **Exit Criteria**:
  - Formal D-log decision: Approve for future integration OR Kill
  - If killed: retired with recorded rationale
- **Owner**: _unclaimed_

### Phase 74 — ML Promotion Gate Verification
- **Status**: QUEUED
- **Blocked by**: Phase 73
- **Emphasis**: Governance 60 / ML 40
- **Scope**:
  - Write and run ML promotion metric evaluator script
  - Verify ≥40% ML-augmented promotions with N ≥ 5 floor
- **Exit Criteria**:
  - Metric passes OR explicit D-log decision to adjust target
- **Owner**: _unclaimed_

---

## Tier 4: ML-Driven Scaling & Production Hardening

### Phases 75–77 — ML Allocator & Ensemble Integration
- **Status**: QUEUED
- **Blocked by**: Phase 74
- **Emphasis**: Backend 70 / ML 30
- **Scope**:
  - Integrate ML ensembles into allocator and risk engines
  - Deploy online learning + regime-detection in production shadow
  - Online models subject to same drift escalation and KS-03 governance as static models
  - Automate continuous drift and decay monitoring
- **Exit Criteria**:
  - ML-guided allocator running in shadow environment
- **Owner**: _unclaimed_

### Phases 78–79 — 6-Month Shadow Portfolio Test
- **Status**: QUEUED
- **Blocked by**: Phase 77
- **Emphasis**: Governance 50 / ML 30 / Ops 20
- **Scope**:
  - ML allocator vs legacy baseline, 6-month shadow comparison
- **Exit Criteria**:
  - PASS: allocator promoted to production candidate
  - FAIL: BLOCKED status, decommissioned, D-log retirement, 30-day cooldown before re-attempt, material architectural change required
- **Owner**: _unclaimed_

---

## Tier 5: Controlled Agentic Automation

### Phases 80+ — Self-Improving Governed Loops
- **Status**: QUEUED
- **Blocked by**: Phase 79 PASS
- **Emphasis**: ML 50 / Governance 30 / Ops 20
- **Scope**:
  - Self-improving loops with explicit performance-decay triggers
  - 30% temporal holdout data partition for retraining
  - SAW kill-switch (KS-03) integration
  - Autonomous live capital promotion only when drift alerts + governance checks authorize
- **Exit Criteria**:
  - Governed autonomous operation with full audit trail
- **Owner**: _unclaimed_

---

## Quick Reference

| Phase | Name | Status | Blocked By |
|-------|------|--------|------------|
| 62    | Frontend Shell Consolidation | READY | — |
| 63    | Execution Boundary Hardening | QUEUED | 62 |
| 64    | Data Provenance Hardening | QUEUED | 63 |
| 65    | MLOps Skeleton | QUEUED | 64 |
| 66    | V2 Scaffold & Candidate Registry | QUEUED | 65 |
| 67    | Fast Proxy Simulator | QUEUED | 66 |
| 68    | PEAD Variant Expansion | QUEUED | 67 |
| 69    | V1 Promotion Pipeline + Nautilus Decision | QUEUED | 68 |
| 70    | Discovery Dashboard & ML Hooks | QUEUED | 69 |
| 71    | LLM/Agent Hypothesis Generation | QUEUED | 70 |
| 72    | Genetic Programming & Distributed Compute | QUEUED | 71 |
| 73    | DRL Spike (Prove or Kill) | QUEUED | 72 |
| 74    | ML Promotion Gate Verification | QUEUED | 73 |
| 75–77 | ML Allocator & Ensemble Integration | QUEUED | 74 |
| 78–79 | 6-Month Shadow Portfolio Test | QUEUED | 77 |
| 80+   | Controlled Agentic Automation | QUEUED | 79 PASS |
