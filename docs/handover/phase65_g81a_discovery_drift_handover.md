# Phase 65 G8.1A Handover - Discovery Drift Correction

Status: Complete
Authority: Phase 65 G8.1A policy/schema-only work
Date: 2026-05-10
Owner: PM / Architecture Office

## Executive Summary (PM-friendly)

G8.1A corrects the discovery-origin label on the existing six-name intake queue. The queue is still useful, but it is not a system-discovered list. It is user-seeded, with theme or supply-chain adjacency labels added where appropriate.

The correction prevents a future planner from treating `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` as pure `SYSTEM_SCOUTED` output.

## Delivered Scope vs Deferred Scope

Delivered:

- discovery-origin taxonomy;
- required origin fields on every intake item;
- relabeled six-name static queue;
- validator rules for user-seeded vs system-scouted distinction;
- policy docs separating intake, candidate card, system scout, and factor scout.

Deferred:

- G8.1B pipeline-first 4-factor scout baseline;
- factor-artifact inspection;
- system-scouted intake output;
- G8.2 second candidate card;
- G9 market-behavior signal card;
- alpha search, ranking, scoring, buy/sell/hold, dashboard runtime, alerts, and broker calls.

## Derivation and Formula Register

G8.1A validity formula:

```text
g8_1a_origin_valid =
  discovery_origin_present
  and origin_evidence_present
  and scout_path_present
  and user_seeded_flag_matches_origin
  and system_scouted_flag_matches_origin
  and current_six_system_scouted == false
  and current_six_validated == false
  and current_six_actionable == false
  and local_factor_scout_used == false
```

Implementation paths:

- `opportunity_engine/discovery_intake_schema.py`
- `opportunity_engine/discovery_intake.py`
- `tests/test_g8_1a_discovery_drift_policy.py`

## Logic Chain

```text
User-seeded names -> origin taxonomy -> provenance fields -> intake-only queue -> G8.1B/G8.2/G9 decision held
```

## Evidence Matrix

| Check | Result | Artifact |
| --- | --- | --- |
| Focused G8.1/G8.1A tests | PASS | `tests/test_g8_1_supercycle_discovery_intake.py`, `tests/test_g8_1a_discovery_drift_policy.py` |
| Context selector regression | PASS | `tests/test_build_context_packet.py` |
| Scoped compile | PASS | `opportunity_engine/discovery_intake_schema.py`, `opportunity_engine/discovery_intake.py`, `opportunity_engine/__init__.py` |
| Queue manifest hash | PASS | `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json` |
| Full pytest | PASS | `.venv\Scripts\python -m pytest -q` |
| Context rebuild/validate | PASS | `docs/context/current_context.json`, `docs/context/current_context.md` |
| Runtime smoke | PASS | `docs/context/e2e_evidence/phase65_g81a_launch_smoke_20260510_status.txt` |

## Open Risks / Assumptions / Rollback

Open risks:

- inherited yfinance migration debt;
- inherited S&P sidecar freshness debt;
- inherited Reg SHO and provider-policy gaps;
- inherited options/license gap;
- inherited dashboard runtime dirty worktree;
- broad compileall workspace hygiene debt;
- G8.1B factor-scout manifest gap remains open.

Assumptions:

- user-seeded examples are provenance labels, not validation;
- theme adjacency is a discovery hint, not canonical evidence;
- no math/modeling review is needed until G8.1B or later factor definitions.

Rollback:

- revert only G8.1A schema changes, queue origin fields, focused tests, G8.1A docs, context surfaces, handover, and SAW report.
- do not revert G8.1, G8, or earlier Phase 65 work.

## Next Phase Roadmap

1. `G8.1B`: pipeline-first 4-factor scout baseline, wrapping `data/processed/phase34_factor_scores.parquet` behind a manifest-backed `LOCAL_FACTOR_SCOUT` contract.
2. `G8.2`: one additional candidate card from the intake queue.
3. `G9`: one market-behavior signal card.
4. Hold.

## New Context Packet

## What Was Done

- Completed G8.1A Discovery Drift Correction as policy/schema-only governance.
- Preserved the R64.1/D-353 provenance anchor while superseding the G8.1 bridge with the G8.1A origin-governance bridge.
- Added discovery-origin taxonomy values including `USER_SEEDED`, `THEME_ADJACENT`, `SUPPLY_CHAIN_ADJACENT`, `LOCAL_FACTOR_SCOUT`, and `SYSTEM_SCOUTED`.
- Relabeled the six-name queue so `MU` is `USER_SEEDED`, `DELL`/`INTC`/`AMD`/`ALB` are `USER_SEEDED + THEME_ADJACENT`, and `LRCX` is `USER_SEEDED + SUPPLY_CHAIN_ADJACENT`.
- Preserved all six names as not system-scouted, not validated, and not actionable.
- Defined `LOCAL_FACTOR_SCOUT` for G8.1B but kept it unused in G8.1A.
- Added tests proving the intake queue cannot rank, score, emit buy/sell/hold, treat research capture as canonical evidence, or use factor scout output yet.

## What Is Locked

- The current six-name queue is user-seeded, not pure `SYSTEM_SCOUTED`.
- `MU` may have `candidate_card_exists`, but it is not validated and not actionable.
- `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` remain intake-only.
- `LOCAL_FACTOR_SCOUT` remains held until G8.1B wraps a governed scout artifact.
- No alpha search, ranking, scoring, factor display, buy/sell/hold call, dashboard runtime, alert, broker behavior, or recommendation is authorized.

## What Is Next

- Recommended next action: `approve_g8_1b_pipeline_first_discovery_scout_or_hold`.
- G8.1B should narrowly inspect `data/processed/phase34_factor_scores.parquet` and wrap it as a governed `LOCAL_FACTOR_SCOUT` baseline before any system-scouted intake.
- Alternative: approve G8.2 one additional candidate card.
- Alternative: approve G9 one market-behavior signal card.
- Alternative: hold.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g8_1_supercycle_discovery_intake.py tests\test_g8_1a_discovery_drift_policy.py -q
```

## Next Todos

- Wait for explicit G8.1B, G8.2, G9, or hold decision.

## Confirmation

ConfirmationRequired: YES
Prompt: Reply "approve G8.1B pipeline-first discovery scout" or "hold".
NextPhaseApproval: PENDING
