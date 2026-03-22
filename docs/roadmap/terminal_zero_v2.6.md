# Terminal Zero v2.6 — Official Adopted & Locked Roadmap

Date: 2026-03-23
Authority: D-352
Status: LOCKED
Origin: Alpha Rating Discussion reconciliation (Expert 1 / Expert 2 / Local Worker)
Agreement Score: 99/100

---

## Endgame Vision

V2 discovers many possible alphas cheaply.
V1 decides which are real, governable, and deployable.
The operator shell gives the human a single pane of glass.
The execution boundary routes governed decisions to capital — and nothing else touches capital without V1 promotion.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TERMINAL ZERO — ENDGAME STATE                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              V2 DISCOVERY (Alpha Factory)                            │  │
│  │                                                                      │  │
│  │  Feature Lab ──► Generators ──► Fast Screen ──► Robustness Lab      │  │
│  │       │               │              │               │              │  │
│  │       ▼               ▼              ▼               ▼              │  │
│  │  [Sandbox Data]  [Candidates]   [Kill 95%]   [Replicate Top 5%]    │  │
│  │                                      │                              │  │
│  │                                      ▼                              │  │
│  │                          ┌─────────────────────┐                    │  │
│  │                          │  Candidate Registry  │                   │  │
│  │                          └─────────┬───────────┘                    │  │
│  └────────────────────────────────────┼────────────────────────────────┘  │
│                                       │                                    │
│                             PROMOTION CONTRACT                             │
│                             (candidate packet)                             │
│                                       ▼                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              V1 CORE (Governed Research Kernel)                      │  │
│  │                                                                      │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │  │
│  │  │  Canonical   │ │   Official   │ │  Portfolio  │ │  Authority   │  │  │
│  │  │  Data Layer  │ │  Validation  │ │  Governance │ │  & Evidence  │  │  │
│  │  │             │ │   Engine     │ │   Layer     │ │    Layer     │  │  │
│  │  │ CRSP/Comp   │ │ engine.py    │ │ Allocator   │ │ D-log        │  │  │
│  │  │ CapIQ Pro   │ │ Attribution  │ │ Sleeve Reg  │ │ Kill Sw      │  │  │
│  │  │ Moody's     │ │ SPA/WRC/PBO  │ │ Regime Bud  │ │ SSOT         │  │  │
│  │  │ Feature St  │ │ Gate Checks  │ │ Limits      │ │ Phases       │  │  │
│  │  └──────┬──────┘ └──────┬───────┘ └──────┬─────┘ └──────┬───────┘  │  │
│  │         └───────────────┴────────┬───────┘              │          │  │
│  │                                  ▼                      │          │  │
│  │                     ┌───────────────────┐               │          │  │
│  │                     │  Promoted Sleeves  │◄──────────────┘          │  │
│  │                     │  (PEAD, Event, ..) │                          │  │
│  │                     └────────┬──────────┘                          │  │
│  └──────────────────────────────┼─────────────────────────────────────┘  │
│                                 │                                        │
│                                 ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              OPERATOR SHELL (Frontend)                               │  │
│  │                                                                      │  │
│  │  Shell Frame ──► Route Registry ──► Shared Loaders ──► View Modules │  │
│  │  (app chrome)    (page dispatch)    (packet/status)    (8+ views)   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│                                 ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              EXECUTION BOUNDARY                                      │  │
│  │                                                                      │  │
│  │  ┌──────────────────┐ ┌───────────────┐ ┌────────────────────────┐  │  │
│  │  │  Orchestrator    │ │     Risk      │ │   Broker Adapter       │  │  │
│  │  │  (scheduling,    │ │  Interceptor  │ │   (Alpaca paper/live   │  │  │
│  │  │   reconciliation)│ │  (fail-closed)│ │    or Nautilus OMS)    │  │  │
│  │  └──────────────────┘ └───────────────┘ └────────────────────────┘  │  │
│  │                                                                      │  │
│  │  Microstructure Telemetry ──► Signed Envelope ──► Audit Trail       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current State Anchor (Post-Phase 61)

| Layer                | Status                                                |
|----------------------|-------------------------------------------------------|
| V1 Core / Governance | STRONG — 61 phases, 351 decisions, KS-03 cleared      |
| V1 Data Layer        | STRONG — PIT-clean, sidecar lane, frozen+additive     |
| V1 Validation Engine | STRONG — engine.py immutable, audit passing           |
| Operator Shell       | DEBT — dashboard.py 2084 lines, views split thin      |
| Execution Boundary   | INCOMPLETE — paper-only, no live fills, 4309 LOC      |
| V2 Discovery         | DOES NOT EXIST YET                                    |

---

## Reconciled Thesis

Public evidence conclusively proves that firms like AQR and WorldQuant have integrated machine learning and agentic AI as foundational layers in their research, simulation, and discovery workflows. Public evidence does not provide live Sharpe ratios or production PnL, as this data is strictly proprietary across the industry. Therefore, waiting for public proof of live deployed alpha is a strategic error. We build our aggressive production roadmap based on verified public research signals and validate through our own internal shadow testing.

Machine learning and automation are horizontal infrastructure layers from Phase 62 onward. Milestones are anchored in provable internal outcomes, not assumptions about competitor live deployment.

---

## Tier 1: Platform Hardening + ML Skeleton (Phases 62–65)

### The 80/20 Split

**80% Engineering Focus**: Clear verified technical debt.
- Execute shell consolidation (dashboard.py → shell_frame + route_registry + shared_loaders)
- Extract execution boundary (define BrokerPort interface in Phase 63)
- Establish data provenance manifests
- Refactor dashboard.py to < 400 lines

**20% ML Focus**: Deploy MLOps skeleton.
- Basic experiment tracking
- Model versioning
- Meta-labeling prototype
- No distributed compute (Ray/Kubernetes) in this tier

**Data Isolation Contract (Phase 62–65 Exit Criteria)**:
- ML experiment artifacts (model checkpoints, feature importance logs, tracking DB) live in `v2_discovery/` or `mlops/` directory
- V1 canonical artifacts (`data/processed/`, `research_data/`, governance docs) are strictly excluded from ML experiment writes
- This boundary is enforced by directory convention and verified by hygiene tests

**Nautilus Decision (D-352)**:
- BrokerPort interface is defined in Phase 63 (execution boundary hardening)
- Nautilus adapter spike is deferred to Phases 69–70
- No Nautilus work before V2 pipeline baseline proves structural integrity

**Exit Criteria**:
- Legacy debt addressed (dashboard.py < 400 lines, BrokerPort interface defined, provenance manifests on all canonical artifacts)
- Observability stabilized
- MLOps skeleton live and tied to SAW governance logs
- Data isolation boundary verified by tests

### Phase 62 — Frontend Shell Consolidation
- Emphasis: Frontend 70 / Backend 20 / Docs 10
- Break dashboard.py into shell_frame.py, route_registry.py, shared_loaders.py
- Keep existing 8 view modules, wire through registry
- Exit: dashboard.py < 400 lines, all views load through registry, Streamlit smoke test passes

### Phase 63 — Execution Boundary Hardening
- Emphasis: Backend 80 / Frontend 20
- Extract scheduling/reconciliation/subprocess from main_bot_orchestrator.py (1556 lines → < 600)
- Define BrokerPort interface (submit/cancel/positions/account)
- Extract telemetry spool from microstructure.py
- No direct Alpaca imports outside broker_api.py
- Exit: orchestrator < 600 lines, BrokerPort defined, all execution tests green

### Phase 64 — Data Provenance Hardening
- Emphasis: Backend/Data 85 / Frontend 15
- Provenance manifest on every sidecar parquet (source, extraction date, row count, hash)
- Surface provenance state in operator shell (green/amber/red per source)
- Complete Method B sidecar integration for S&P 500 Pro / Moody's Orbis
- WRDS either resolved or formally retired with documented fallback
- Exit: every canonical artifact has provenance manifest, shell shows data-source health

### Phase 65 — MLOps Skeleton
- Emphasis: Backend 70 / ML 30
- Experiment tracking (MLflow or lightweight equivalent)
- Model versioning with artifact store in `v2_discovery/mlops/`
- Meta-labeling prototype on existing PEAD feature set
- Exit: MLOps skeleton operational, tied to SAW logs, data isolation tests passing

---

## Tier 2: Core V2 Discovery Pipeline — Non-ML Baseline (Phases 66–69)

**Goal**: Build the alpha factory plumbing and prove it works without ML before adding ML.

### Phase 66 — V2 Scaffold & Candidate Registry
- Create `v2_discovery/` package
- Build candidate registry (SQLite or Parquet)
  - Columns: candidate_id, family, parent_id, data_snapshot, feature_hash, metrics, status, created_at
  - Statuses: generated → screened_out | incubating → replicated → queued_for_v1 → promoted | rejected | retired
- Define promotion packet JSON schema (see docs/architecture/v1_v2_boundary.md)
- Exit: registry operational, one dummy candidate round-trips all statuses

### Phase 67 — Fast Proxy Simulator
- Vectorized approximate backtest in `v2_discovery/fast_sim/`
- Screening-grade only, ~10x faster than engine.py
- Supports: long-only equity, daily rebalance, approximate costs, basic turnover
- Cannot claim promotion readiness from proxy results (enforced by schema)
- Exit: proxy sim produces Sharpe/CAGR/turnover for 1000+ candidates in < 10 min

### Phase 68 — PEAD Variant Expansion (Pilot Family)
- Seed from existing PEAD sleeve (Phase 56, Sharpe 0.63, CAGR 10.9%)
- Generate 50–200 PEAD variants: analyst-revision interactions, delayed entry, alternative holding periods, regime-conditioned entry, sector-neutral
- Screen through proxy sim, kill bottom 90%
- Run top 5–10 through robustness mini-lab
- Export top 1–3 as formal promotion packets to V1
- Exit: at least 1 PEAD variant promotion packet submitted to V1

### Phase 69 — V1 Promotion Pipeline + Nautilus Spike Decision
- Build V1 intake handler: receives packet, validates schema, runs official engine.py backtest, applies gate checks (SPA/WRC/PBO/DSR)
- Records verdict in D-log
- Accepted → approved sleeve registry + shadow monitoring
- Rejected → reason recorded, candidate returned to V2
- Nautilus spike decision point: evaluate whether to proceed with Phase 69b (Nautilus adapter) or defer further
- Exit: one real candidate processed end-to-end, verdict recorded

---

## Tier 3: AI-Augmented Discovery Ramp (Phases 70–74)

**Prerequisite**: At least one non-ML candidate family has been processed end-to-end through V2 → V1.

### ML Promotion Metric
- Target: ≥40% of promoted candidate families are ML-augmented
- Floor: minimum N ≥ 5 total promotions attempted in this tier
- Measurement: automated script reads candidate registry, counts total promotions attempted, counts ML-augmented promotions, fails if either percentage or floor not met
- Evaluator script must be written and tested before Phase 74 exit

### Phase 70 — Discovery Dashboard & ML Hooks
- Add "Discovery" view to operator shell (candidate pipeline status, family summaries, survival rates)
- Activate lightweight ML feature extraction stubs in V2 generators
- Exit: researcher can see full candidate pipeline in shell

### Phase 71 — LLM/Agent-Assisted Hypothesis Generation
- LLM-assisted hypothesis generation as primary discovery channel
- AutoML framework for rapid feature discovery
- Mandatory meta-labeling and economic sanity filters before promotion
- Exit: ML-generated candidates entering registry

### Phase 72 — Genetic Programming & Distributed Compute
- Genetic programming frameworks on distributed clusters (Ray/Kubernetes)
- Combinatorial feature crosses and symbolic rule search
- Exit: distributed pipeline operational, candidates flowing

### Phase 73 — DRL Spike (Prove or Kill)
- Deep Reinforcement Learning for portfolio allocation as strict bounded research spike
- NOT approved for standard promotion pipeline
- Exit: formal D-log decision — Approve for future integration OR Kill
- If killed: DRL is retired with recorded rationale

### Phase 74 — ML Promotion Gate Verification
- Run ML promotion metric evaluator
- Verify ≥40% ML-augmented with N ≥ 5 floor
- Exit: metric passes or explicit D-log decision to adjust target

---

## Tier 4: ML-Driven Scaling & Production Hardening (Phases 75–79)

### Phase 75–77 — ML Allocator & Ensemble Integration
- Integrate ML ensembles into allocator and risk engines
- Deploy online learning and regime-detection models in production shadow
- Online models subject to same drift escalation and kill-switch governance as static models
- Automate continuous drift and decay monitoring
- Exit: ML-guided allocator running in shadow

### Phase 78–79 — 6-Month Shadow Portfolio Test

**Exit Criteria & Failure Path**:
- ML-guided allocator must outperform legacy baseline in 6-month shadow test
- If PASS: allocator promoted to production candidate status
- If FAIL:
  - ML allocator immediately assigned BLOCKED status
  - Decommissioned from shadow trading
  - Formal D-log retirement decision recorded
  - Any re-attempt requires a new explicit D-log approval after minimum 30-day cooldown period
  - Re-submitted model must demonstrate material architectural change, not parameter tuning

---

## Tier 5: Controlled Agentic Automation (Phases 80+)

- Self-improving loops governed by explicit triggers (performance decay > defined threshold)
- 30% temporal holdout data partition for all retraining (30% of historical data reserved as validation, not used in training)
- Strict SAW kill-switch (KS-03) governance integration
- Autonomous promotion to live capital occurs ONLY when real-time drift alerts and automated governance checks explicitly authorize it
- Every automated decision is logged and auditable

---

## Summary Table

| Phases | Theme                              | Outcome                                    |
|--------|------------------------------------|--------------------------------------------|
| 62–65  | Platform Hardening + ML Skeleton   | Clean shell, stable execution seam,        |
|        |                                    | provenance, MLOps skeleton                 |
| 66–69  | Core V2 Discovery (Non-ML)         | Alpha factory operational, first promotion |
| 70–74  | AI-Augmented Discovery Ramp        | ML candidates, distributed compute, DRL    |
|        |                                    | spike decision                             |
| 75–79  | ML Scaling & Production Hardening  | ML allocator shadow test, pass/fail gate   |
| 80+    | Controlled Agentic Automation      | Governed self-improving loops, live capital |

---

## Governance Contracts Referenced

- V1/V2 Boundary: `docs/architecture/v1_v2_boundary.md`
- Phase Queue: `PHASE_QUEUE.md` (repo root)
- Decision Log: `docs/decision log.md`
- Promotion Packet Schema: defined in `docs/architecture/v1_v2_boundary.md`
- ML Allocator Failure Path: this document, Tier 4
- DRL Spike Governance: this document, Phase 73
- Data Isolation: this document, Tier 1 exit criteria
