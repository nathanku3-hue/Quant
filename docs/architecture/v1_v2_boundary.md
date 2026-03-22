# V1/V2 Architecture Boundary Contract

Date: 2026-03-23
Authority: Terminal Zero v2.6 Roadmap
Status: ACTIVE
Referenced by: `docs/roadmap/terminal_zero_v2.6.md`

---

## Principle

Do not make one system do both jobs.

- **V1 Core** = truth, governance, promotion, shadow/live control
- **V2 Discovery** = high-throughput idea generation, feature search, candidate triage

The contract between them is narrow and strict.

---

## 1. Hard Boundaries

### A. Data Boundary

**V1 owns:**
- Canonical PIT-clean datasets (CRSP/Compustat, CapIQ Pro, Moody's Orbis)
- Official universes, costs, calendars, corporate action policy
- Frozen research windows and holdout policy (`RESEARCH_MAX_DATE = 2022-12-31`)
- All artifacts under `data/processed/` and `research_data/`

**V2 may:**
- Read approved source snapshots (read-only reference)
- Build derived exploratory features in `v2_discovery/data_lab/`
- Cache aggressively and transform freely within its own directories

**V2 must NOT:**
- Write to `data/processed/`, `research_data/`, or any V1 canonical path
- Redefine official truth surfaces silently
- Overwrite canonical parquet, feature store, or evidence artifacts

**Rule: V2 may derive. V1 defines.**

### B. Simulation Boundary

**V1 owns:**
- Official engine (`core/engine.py`) — immutable
- Same-window / same-cost / same-engine comparator discipline
- Official promotion statistics

**V2 may:**
- Use fast approximate engines (`v2_discovery/fast_sim/`)
- Use vectorized shortcut simulations
- Use cheaper proxy cost models for pruning

**V2 must NOT:**
- Claim promotion readiness from proxy results
- Bypass V1 gate checks (SPA/WRC/PBO/DSR)

**Rule: V2 can estimate. V1 adjudicates.**

### C. Governance Boundary

**V1 owns:**
- Decision log (`docs/decision log.md`)
- Kill switches (KS-01 through KS-05)
- SSOT artifacts
- Phase briefs, handovers, promotion decisions
- Sleeve status and promotion verdicts

**V2 owns:**
- Experiment registry
- Candidate lineage
- Candidate ranking and scorecards
- No architectural authority

**Rule: V2 discovers candidates. V1 decides status.**

### D. Deployment Boundary

**V1 owns:**
- Shadow portfolio
- Operational alerts
- Live execution interfaces (via BrokerPort)
- Demotion and rollback

**V2 must NOT:**
- Have any direct trade path
- Make direct production writes
- Issue live alert authority

**Rule: Nothing discovered in V2 touches capital without V1 promotion.**

---

## 2. Directory Boundaries

```
quant/
  # ── V1 Core (governed, immutable where marked) ──
  core/                    # engine.py (IMMUTABLE), data_orchestrator, drift_detector
  data/                    # canonical loaders, feature_store, updater
  data/processed/          # canonical parquet artifacts (V1 ONLY)
  research_data/           # frozen research artifacts (V1 ONLY, IMMUTABLE)
  strategies/              # official alpha_engine, regime_manager, factor_attribution
  execution/               # broker_api (BrokerPort), risk_interceptor, microstructure
  views/                   # operator shell view modules
  dashboard.py             # shell frame (post-Phase 62 refactor)
  main_bot_orchestrator.py # scheduling/reconciliation (post-Phase 63 refactor)
  docs/                    # governance docs, decision log, phase briefs, SAW reports
  tests/                   # V1 regression and governance tests

  # ── V2 Discovery (exploratory, no V1 writes) ──
  v2_discovery/
    data_lab/              # derived features, exploratory joins, sandbox transforms
    feature_lab/           # rapid factor transforms, interaction terms
    generators/            # candidate generators (rules, sweeps, combinatorial, ML)
    fast_sim/              # proxy simulator (screening-grade only)
    screening/             # fast kill screens, rank IC, monotonicity checks
    robustness/            # mini-lab: alternate windows, costs, universes, stress
    registry/              # candidate registry (SQLite or Parquet)
    mlops/                 # experiment tracking, model versioning, checkpoints
    notebooks/             # exploratory research notebooks
    tests/                 # V2-specific tests

  # ── Contracts (shared schemas, versioned) ──
  contracts/
    candidate_packet/      # promotion packet JSON schema
    data_snapshot/         # snapshot manifest schema
    feature_schema/        # official feature definition references
    promotion_schema/      # promotion request / verdict schema
```

### Strict Exclusion Rules

| Directory | V1 Write | V2 Write | ML Write |
|-----------|----------|----------|----------|
| `data/processed/` | YES | NO | NO |
| `research_data/` | NO (immutable) | NO | NO |
| `core/` | Governed only | NO | NO |
| `docs/` | YES | NO | NO |
| `v2_discovery/` | NO | YES | YES |
| `v2_discovery/mlops/` | NO | NO | YES |
| `contracts/` | YES (schema owner) | Read only | Read only |

---

## 3. Promotion Contract: V2 → V1

V2 hands V1 a standardized **promotion packet**, not a fuzzy story.

### Promotion Packet Schema

```json
{
  "schema_version": "1.0.0",
  "candidate_identity": {
    "candidate_id": "string (UUID)",
    "hypothesis_family": "string",
    "owner": "string",
    "parent_lineage": ["string"],
    "code_commit_hash": "string",
    "data_snapshot_id": "string"
  },
  "economic_thesis": {
    "targeted_inefficiency": "string",
    "persistence_rationale": "string",
    "expected_decay_horizon": "string",
    "crowding_risk": "string",
    "distinction_from_existing_sleeves": "string"
  },
  "construction_spec": {
    "universe": "string",
    "rebalance_frequency": "string",
    "ranking_method": "string",
    "entry_exit_rules": "string",
    "position_sizing": "string",
    "liquidity_screens": "string",
    "risk_controls": "string"
  },
  "fast_evidence": {
    "proxy_sharpe": "number",
    "proxy_cagr": "number",
    "turnover": "number",
    "capacity_estimate": "string",
    "robustness_summary": "string",
    "sensitivity_map": "string",
    "regime_notes": "string",
    "failure_modes": "string"
  },
  "reproducibility_bundle": {
    "config_hash": "string",
    "data_refs": ["string"],
    "feature_definitions": ["string"],
    "experiment_code_hash": "string"
  },
  "requested_v1_action": {
    "type": "enum: official_backtest | sleeve_comparison | event_family_review | allocator_eligibility | regime_validation | shadow_trial"
  }
}
```

### V1 Intake Verdicts

| Verdict | Action |
|---------|--------|
| `rejected_intake` | Schema invalid or missing fields; returned to V2 |
| `revision_requested` | Specific feedback provided; candidate stays in V2 |
| `accepted_for_validation` | Official engine.py backtest + gate checks run |
| `promoted_to_sleeve` | Enters approved sleeve registry + shadow monitoring |
| `rejected_after_validation` | Gate checks failed; reason recorded in D-log |

---

## 4. Candidate Lifecycle

```
V2: generated
  → V2: screened_out (killed by fast screen)
  → V2: incubating (passed fast screen, in robustness lab)
    → V2: replicated (passed robustness)
      → V2: queued_for_v1 (promotion packet exported)
        → V1: accepted_for_validation
          → V1: promoted_to_sleeve (enters shadow)
          → V1: rejected_after_validation (reason in D-log)
        → V1: rejected_intake (packet invalid)
        → V1: revision_requested (feedback to V2)
  → V2: retired (superseded or decayed)
```

---

## 5. Online Model Governance

Online learning models deployed in shadow (Phases 75–79) are subject to:
- Same drift escalation as static models
- Same KS-03 kill-switch governance
- Explicit rollback contract: if drift exceeds threshold, model reverts to last stable checkpoint
- All retraining events logged in SAW governance trail
- 30% temporal holdout partition (30% of historical data reserved as validation, never used in training)

---

## 6. ML Allocator Failure Path

If the ML-guided allocator fails the 6-month shadow portfolio test (Phases 78–79):
1. Immediately assigned `BLOCKED` status
2. Decommissioned from shadow trading
3. Formal D-log retirement decision recorded
4. Any re-attempt requires new explicit D-log approval after minimum 30-day cooldown
5. Re-submitted model must demonstrate material architectural change, not parameter tuning
