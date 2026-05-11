# Phase 65 G7 Handover - Candidate Family Definition

Status: CLOSED - DEFINITION ONLY
Date: 2026-05-09
Authority: D-364 Phase G7 first controlled candidate-family definition, no search

## Executive Summary

G7 added the first controlled candidate-family contract before search begins. `PEAD_DAILY_V0` is now defined with a Tier 0 canonical data policy, finite allowed features, finite parameter space, fixed trial budget, future validation gates, and multiple-testing policy. No candidate was generated, no backtest/replay/proxy run started, no metric/ranking appeared, and no alert, broker, notifier, OpenClaw, or promotion path was introduced.

## Delivered Scope

- Added `v2_discovery/families/` with frozen schema, trial-budget validation, manifest reconciliation, append-only registry behavior, and definition-only report validation.
- Added focused G7 tests for required fields, manifest backing, Tier 0 policy, finite parameter space, trial budget, append-only/versioned behavior, candidate/result blocking, no metrics/rankings, no alert/broker action, and report hygiene.
- Published `data/registry/candidate_families/pead_daily_v0.json`.
- Published `data/registry/candidate_families/pead_daily_v0.json.manifest.json`.
- Published `data/registry/candidate_family_registry_report.json`.
- Published `docs/architecture/g7_candidate_family_definition_policy.md`.

## Deferred Scope

- No candidate generation.
- No backtest, replay, proxy run, strategy search, alpha/performance metric, candidate ranking, alerts, broker calls, paper trading, or promotion packet.
- No Tier 2/yfinance/operational Alpaca data for promotion evidence.
- No G8 candidate generation until a separate approval or hold decision.

## Derivation and Formula Register

```text
finite_trial_count = product(count(options_p) for p in parameter_space)
PEAD_DAILY_V0 finite_trial_count = 4 holding_days * 3 liquidity_floor bins * 2 event_window_lag values = 24
trial_budget_valid = finite_trial_count <= trial_budget_max
family_defined_for_candidate = manifest_exists AND sha256_matches AND row_count=1 AND family_id/version match
```

Source paths:
- `v2_discovery/families/schemas.py`
- `v2_discovery/families/trial_budget.py`
- `v2_discovery/families/registry.py`
- `v2_discovery/families/validation.py`

## Logic Chain

```text
G6 mechanical equivalence -> pre-result family contract -> finite feature/parameter/trial budget -> manifest-backed definition -> future G8-or-hold decision
```

## Evidence Matrix

```text
G7 focused tests: .venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py -q -> PASS (19 passed)
G7/G6/G5/G4/G3/G2/G1/G0/F matrix: .venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py tests\test_g6_v1_v2_real_slice_mechanical_comparison.py tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q -> PASS (166 passed)
Family artifact: data/registry/candidate_families/pead_daily_v0.json -> manifest-backed definition, trial_budget_max=24, finite_trial_count=24
Registry report: data/registry/candidate_family_registry_report.json -> defined_only=true, candidate_generation_enabled=false, result_generation_enabled=false, promotion_ready=false, alerts_emitted=false, broker_calls=false
Policy: docs/architecture/g7_candidate_family_definition_policy.md
```

## Open Risks / Assumptions / Rollback

- Open risks: yfinance migration remains future debt; primary S&P sidecar freshness remains stale through `2023-11-27`.
- Assumptions: G8, if approved, is exactly one candidate generated from the predeclared family and still no search.
- Rollback: revert only G7 family package additions, focused test, family/report artifacts, policy, handover, SAW report, and G7 documentation/context updates; do not revert G6/G5/G4/G3/G2/G1/G0/F/D-353/R64.1.

## New Context Packet

## What Was Done

- Preserved D-353 provenance gates, R64.1 dependency hygiene, Candidate Registry, G0/G1/G2/G3, G4 readiness, G5 V1 replay, and G6 V1/V2 mechanical comparison as closed prerequisites.
- Closed Phase G7 first controlled candidate-family definition, no search.
- Defined `PEAD_DAILY_V0` before outcomes exist.
- Declared allowed features, forbidden features, finite parameter space, `trial_budget_max = 24`, future validation gates, multiple-testing policy, and Tier 0 canonical promotion-evidence policy.
- Published manifest-backed `data/registry/candidate_families/pead_daily_v0.json`.
- Published definition-only `data/registry/candidate_family_registry_report.json`.
- Kept candidate generation, result generation, promotion, alerts, broker calls, and performance metrics disabled.

## What Is Locked

- G7 is definition-only governance, not research output.
- Family definition must exist and reconcile with its manifest before future candidate creation.
- Parameter space is finite; silent expansion requires a new version or later explicit decision.
- `PEAD_DAILY_V0` has `finite_trial_count = 24` and `trial_budget_max = 24`.
- Tier 2, yfinance, OpenBB, and operational Alpaca cannot be promotion evidence.
- No strategy search, backtest, replay, proxy run, metric, ranking, alert, broker call, paper trading, or promotion packet is authorized by G7.

## What Is Next

- Decide whether to hold or approve Phase G8: generate exactly one candidate from `PEAD_DAILY_V0`, still with no search.
- Carry yfinance migration and stale S&P sidecar freshness as open risks.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py tests\test_g6_v1_v2_real_slice_mechanical_comparison.py tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q
```

## Next Todos

- Prepare only the G8-or-hold decision: exactly one candidate from the predeclared family, no search, or hold.
- Keep strategy search, rankings, alerts, broker calls, V2 promotion, paper trading, and promotion packets blocked until explicitly approved.
- Preserve G7 append-only/versioned family-definition behavior.

ConfirmationRequired: YES
Prompt: Reply "approve next phase" to start execution.
NextPhaseApproval: PENDING
