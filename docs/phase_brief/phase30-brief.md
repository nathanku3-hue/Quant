# Phase 30 Brief - Release Engineering / MLOps

Date: 2026-03-01  
Status: Active

L1: Backtest/Execution Platform Reliability  
L2 Streams: Backend, Frontend/UI, Ops  
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD

## Scope
- In scope:
  - immutable Docker artifact contract (digest-locked references),
  - deterministic release state machine (`pending_probe -> active|rolled_back|rollback_failed`),
  - automatic N-1 rollback on startup-fault deployments,
  - UI cache version bound to runtime release digest.
- Out of scope:
  - QA test-strategy expansion,
  - system-engineering feature/runtime behavior changes beyond deploy wiring,
  - data engineering pipelines,
  - DevSecOps network/secret policy.

## Acceptance Checks
- CHK-01:
  - release refs must be digest-locked (`name[:tag]@sha256:<64-hex>`).
- CHK-02:
  - release metadata writes are atomic and schema-validated.
- CHK-03:
  - startup probe success promotes candidate to `active`.
- CHK-04:
  - startup probe failure performs N-1 rollback attempt and records truthful terminal status:
    - `rolled_back` only when rollback is verified,
    - `rollback_failed` when rollback is not verified.
- CHK-05:
  - UI cache fingerprint includes version + release digest identity.

## Evidence Commands
- `.venv\Scripts\python -m pytest tests/test_release_controller.py -q`
- `.venv\Scripts\python -m py_compile scripts/release_controller.py core/release_metadata.py dashboard.py`

## Artifacts
- `Dockerfile`
- `.dockerignore`
- `core/release_metadata.py`
- `scripts/release_controller.py`
- `tests/test_release_controller.py`
- `data/processed/release_metadata.json` (runtime artifact)
