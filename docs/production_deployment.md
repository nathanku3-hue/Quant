# Production Deployment Guide: C3 Leaky Integrator v1

Date: 2026-02-20  
Status: Locked for Phase 18 closure

## 1) Canonical Config
- Source: `strategies/production_config.py`
- Import:

```python
from strategies.production_config import PRODUCTION_CONFIG_V1
```

- Parameters:
  - `config_id`: `C3_LEAKY_INTEGRATOR_V1`
  - `scoring_method`: `complete_case`
  - `c3_decay`: `0.95` (`leaky_alpha=0.05`)
  - `top_quantile`: `0.10`
  - `cost_bps`: `5.0`
  - factors: default 4-factor set, equal weights, integrator-only toggles ON

## 2) Evidence Snapshot

### Day 5 selection result (`data/processed/phase18_day5_ablation_metrics.csv`)
- Baseline (`BASELINE_DAY4`):
  - coverage `0.4782`
  - spread `1.8421`
  - Sharpe `0.7640`
  - turnover annual `64.9335`
- Selected (`ABLATION_C3_INTEGRATOR`):
  - coverage `0.5237`
  - spread `1.8001`
  - Sharpe `1.0070`
  - turnover annual `19.7940`

### Day 6 robustness result (`data/processed/phase18_day6_summary.json`)
- checks: `9/16` pass, `7/16` fail
- critical gate CHK-54: PASS (all crisis windows reduced turnover >=15%)
- missing active return cells (override run): baseline `0`, c3 `13704`

### Crisis turnover evidence (`data/processed/phase18_day6_crisis_turnover.csv`)
- COVID_CRASH: `84.69%` reduction
- COVID_VOLATILITY: `80.38%` reduction
- INFLATION_SPIKE: `80.45%` reduction
- BEAR_MARKET: `81.04%` reduction

## 3) Accepted Tradeoffs
- Upside/recovery checks remain advisory failures (CHK-41, CHK-48, CHK-50).
- Decay plateau checks remain advisory failures (CHK-51, CHK-52, CHK-53).
- Operator decision is to accept these as design tradeoffs for this phase closure and avoid extra adaptive complexity.

## 4) Deployment Steps
1. Wire scorecard construction to `PRODUCTION_CONFIG_V1.factor_specs`.
2. Use `scoring_method=PRODUCTION_CONFIG_V1.scoring_method`.
3. Keep transaction-cost model at `5 bps`.
4. Keep top-quantile selector at `10%`.
5. Preserve missing-return observability in post-run summary (`phase18_day6_summary.json` pattern).

## 5) Pre-Flight Verification (Required)
1. Config identity check:
   - verify runtime loads `config_id=C3_LEAKY_INTEGRATOR_V1` and `c3_decay=0.95`.
2. Structural check:
   - verify all factor specs have `use_leaky_integrator=True`, and `use_sigmoid_blend=False`, `use_dirty_derivative=False`.
3. Dry-run check:
   - run one non-production simulation cycle and confirm no schema/runtime errors.
4. Observability check:
   - confirm post-run summary includes missing-return counts and check status fields.
5. Go-live gate:
   - only proceed when all four pre-flight checks pass and are recorded in ops notes.

## 6) Monitoring Protocol
- Monthly:
  - track trailing Sharpe, turnover, max drawdown, and CHK-54-style crisis windows.
- Trigger investigation when either condition holds:
  - annual Sharpe materially below Phase 18 lock reference, or
  - turnover reverts toward Day 4 baseline regime.
- Recalibration gate:
  - requires new ablation + walk-forward + SAW approval before changing `c3_decay`.

## 7) Rollback (Operational Runbook)
Owner/Handoff:
- Primary owner: Quant Ops
- Handoff: Strategy lead + Risk sign-off

1. Freeze new order generation (do not force-liquidate existing positions).
2. Capture incident snapshot:
   - active config id, deployment timestamp, recent checks summary, and error logs.
3. Perform atomic deploy rollback:
   - restore prior release artifact/config bundle in one deploy transaction.
4. Run post-rollback verification:
   - confirm scorecard path is pre-lock configuration and runtime starts cleanly.
5. Publish incident record:
   - append rollback action + rationale to ops log and decision trail.
6. Preserve audit artifacts:
   - `docs/saw_phase18_day6_final.md`
   - `docs/phase18_closure_report.md`
   - `docs/decision log.md` (D-101)

## 8) Release Engineering (Area 4)

### Immutable artifact contract
- Every deployable release must be a digest-locked image reference:
  - `registry/repo:tag@sha256:<64-hex>`
- Tags alone are forbidden for promotion decisions.
- Canonical release state artifact:
  - `data/processed/release_metadata.json`
  - schema implemented in `core/release_metadata.py`
  - controller implemented in `scripts/release_controller.py`

### Deterministic promotion contract
1. Build immutable image artifact:
   - `docker build -t ghcr.io/terminal-zero/quant:<version> .`
   - dependency install source inside `Dockerfile`: `requirements.lock` (strict pinned lock install)
2. Resolve digest reference (must include `@sha256:`):
   - `docker image inspect ghcr.io/terminal-zero/quant:<version> --format "{{index .RepoDigests 0}}"`
3. Promote via controller (docker mode default):
   - `.venv\Scripts\python scripts/release_controller.py --candidate-version <version> --candidate-ref <digest-ref> --service-name terminal_zero_orchestrator --startup-wait-seconds 45`

### Automatic rollback wiring
- Controller behavior:
  - stage candidate in metadata (`pending_probe`),
  - deploy candidate container with `TZ_RELEASE_DIGEST`,
  - monitor startup watch window,
  - if container exits during startup diagnostics, immediately stop candidate and start N-1 image automatically,
  - persist final state as:
    - `active` when promotion succeeds,
    - `rolled_back` when rollback is explicitly verified,
    - `rollback_failed` when rollback cannot be verified.
- Rollback is automatic in docker mode; no human intervention is required for startup-fault rollback.
- `external-probe` mode requires explicit operator acknowledgement:
  - `--allow-external-probe-promote`
  - only use when runtime deployment/rollback is handled outside this controller.

### UI cache governance
- UI cache invalidation is bound to release identity:
  - `cache_fingerprint = "<schema_version>@sha256:<release_digest|local-dev>"`
- Implementation path:
  - `core/release_metadata.py` -> `build_release_cache_fingerprint(...)`
  - `dashboard.py` -> `_release_bound_cache_version(...)`

### Strict orchestrator Dockerfile contract (Track B Stream 4 draft)
- Draft file: `Dockerfile.orchestrator.strict`
- Contract requirements enforced in-image:
  - digest-pinned base image (`python:3.12-slim@sha256:...`)
  - deterministic Debian snapshot source (`snapshot.debian.org`) for apt resolution
  - OS runtime libraries installed with explicit version pins:
    - `ca-certificates`
    - `libgcc-s1`
    - `libstdc++6`
    - `libgomp1`
  - cryptographic integrity gate on dependency lock artifact:
    - `requirements.lock` SHA-256 must match `REQUIREMENTS_LOCK_SHA256` build arg before pip install
- Runtime scope is intentionally narrow for orchestrator execution:
  - `main_bot_orchestrator.py`
  - `core/`
  - `execution/`
  - `scripts/`

Build example:
```powershell
docker build -f Dockerfile.orchestrator.strict `
  --build-arg DEBIAN_SNAPSHOT=20260220T000000Z `
  --build-arg CA_CERTIFICATES_VERSION=20230311+deb12u1 `
  --build-arg LIBGCC_S1_VERSION=12.2.0-14+deb12u1 `
  --build-arg LIBSTDCXX6_VERSION=12.2.0-14+deb12u1 `
  --build-arg LIBGOMP1_VERSION=12.2.0-14+deb12u1 `
  --build-arg REQUIREMENTS_LOCK_SHA256=950750baf22977b902955cf03a913af2964accf9a9178021e799701ee177b25f `
  -t ghcr.io/terminal-zero/quant-orchestrator:strict-draft .
```
