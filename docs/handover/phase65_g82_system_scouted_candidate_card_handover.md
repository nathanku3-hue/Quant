# Phase 65 G8.2 System-Scouted Candidate Card Handover

Date: 2026-05-10
Phase Window: 2026-05-10 to 2026-05-10
Status: PASS after SAW closeout
Owner: Codex

## 1) Executive Summary

- Objective completed: converted the sole governed `LOCAL_FACTOR_SCOUT` output item, `MSFT`, into one candidate-card-only research object.
- Business/user impact: Terminal Zero can now prove both intake paths: a human-nominated card (`MU`) and a pipeline-scouted card (`MSFT`), while preserving no-score/no-rank/no-action governance.
- Current readiness: static card, manifest, validator update, policy doc, and focused tests are in place; dashboard runtime remains unchanged.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json` stores the MSFT system-scouted candidate card.
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json` stores card provenance, source policy, and hash.
- `tests/test_g8_2_system_scouted_candidate_card.py` validates the system-scouted card path and forbidden-output boundaries.
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md` records the policy and dashboard boundary.
- `opportunity_engine/candidate_card_schema.py` now rejects `factor_score` / `factor_scores` and validates optional governance flags when present.
- `scripts/build_context_packet.py` now sorts G8.2 handovers after DASH-1 and before G9.

Deferred:

- Dashboard card reader/status panel: future DASH lane only.
- G9 market-behavior signal card: held until separate approval.
- G8.3 user-seeded candidate card: held until separate approval.
- Factor model validation: future expert review before any predictive or ranked use.
- Provider ingestion, alerts, buying range, and broker paths: held.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-G82-01 | `eligible_card_ticker = scout_output.items[0].ticker = MSFT` | scout output has exactly one item | Prevents substituting user-seeded names for the system-scouted proof | `data/discovery/local_factor_scout_output_tiny_v0.json`, `tests/test_g8_2_system_scouted_candidate_card.py` |
| F-G82-02 | `g8_2_card_valid = card_valid and ticker_matches_scout and source_manifest_present and no_score_rank_action` | card/manifest/scout bundle | Defines card-only success without validation/actionability | `opportunity_engine/candidate_card_schema.py`, `tests/test_g8_2_system_scouted_candidate_card.py` |
| F-G82-03 | `candidate_cards = {MU, MSFT}` | candidate-card directory | Prevents accidental DELL/AMD/LRCX/ALB card creation | `tests/test_g8_2_system_scouted_candidate_card.py` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-G82-01 | G8.1B scout output | Read the sole intake item | Use `MSFT` only | MSFT card identity |
| L-G82-02 | MSFT intake item + light official/public pointers | Structure thesis, missing evidence, blockers, and provider gaps | Keep `candidate_card_only` | MSFT candidate card |
| L-G82-03 | Card + manifest + scout bundle | Run focused validators | PASS only with no score/rank/action leakage | G8.2 focused test pass |

## 5) Validation Evidence Matrix

| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-G82-01 | `.venv\Scripts\python -m pytest tests\test_g8_2_system_scouted_candidate_card.py -q` | PASS | test output | 13 passed |
| CHK-G82-02 | `.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q` | PASS | test output | 45 passed |
| CHK-G82-03 | `.venv\Scripts\python -m py_compile opportunity_engine\candidate_card_schema.py opportunity_engine\candidate_card.py tests\test_g8_2_system_scouted_candidate_card.py` | PASS | compile output | no errors |
| CHK-G82-04 | `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` | PASS | context-builder tests | 16 passed |
| CHK-G82-05 | `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS | context packet | validation exit 0 |
| CHK-G82-06 | `.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase65_g8_2_system_scouted_candidate_card_20260510.md` | PASS | SAW report | VALID |
| CHK-G82-07 | `.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "<G8.2 ClosurePacket>" --require-open-risks-when-block --require-next-action-when-block` | PASS | closure packet | VALID |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- yfinance migration remains future debt.
- S&P sidecar freshness remains stale.
- Reg SHO policy gap remains future work.
- GodView provider, options license, ownership, insider, and market-behavior gaps remain open.
- Dashboard runtime list still contains legacy action-shaped labels; G8.2 does not merge into that runtime surface.
- Factor model validation remains open before any predictive or ranked use.
- Broad dirty worktree and inherited compileall hygiene remain out of scope.

Assumptions:

- `MSFT` is eligible only because G8.1B emitted it as the sole governed system-scouted item.
- Official/public evidence pointers are research orientation, not validation.
- SEC Form 13F can support slow ownership context later, not live whale behavior.

Rollback Note:

- Remove only the MSFT card/manifest, G8.2 tests, G8.2 policy/handover/SAW docs, current truth-surface updates, and the narrow candidate-card/context-builder validator updates if rejected.
- Do not revert MU, G8.1B scout artifacts, DASH-1 shell work, or unrelated dirty worktree files.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | G9 market-behavior signal card | One signal card, no score/rank/action, source policy tested | PM |
| 2 | G8.3 user-seeded candidate card | One DELL/AMD/LRCX/ALB-style card from user-seeded intake, no scout claims | PM |
| 3 | DASH card reader/status shell | Dashboard reads cards as status-only objects, no action labels | Frontend/UI |
| 4 | Factor model validation | Expert review covers leakage, universe, weights, normalization, costs, and rebalance logic | Modeling review |

## 8) New Context Packet

## What Was Done

- Preserved D-353 provenance gates and R64.1 dependency hygiene as closed baseline truth.
- Closed the Portfolio Universe Construction Fix as PASS after quarantining and reverting the out-of-scope optimizer-core lower-bound/SLSQP diff.
- Opened the Optimizer Core Policy Audit as docs/tests-first work and rejected the quarantined lower-bound/SLSQP diff as-is.
- Completed G8.2 as one system-scouted MSFT candidate card from the existing `LOCAL_FACTOR_SCOUT` output.
- Added no new scout output, no additional ticker cards beyond MSFT, and no dashboard runtime behavior.
- Preserved MU as the existing human-nominated candidate card.
- Added focused tests proving MSFT matches the scout output and cannot expose factor score, rank, buy/sell/hold, validation, actionability, buying range, alert, or broker action.

## What Is Locked

- The quarantined optimizer-core lower-bound/SLSQP diff is not accepted and is preserved only for a separate optimizer-policy audit.
- Optimizer-core implementation remains held until policy approval replaces strict audit xfails with passing implementation tests.
- `MSFT` is the only G8.2 card because it is the sole governed G8.1B `LOCAL_FACTOR_SCOUT` output.
- `MU` and `MSFT` are the only candidate-card artifacts.
- G8.2 card status is `candidate_card_only`.
- The card is not validated, not actionable, not ranked, not scored, and not merged into the dashboard.
- Existing dashboard MSFT rows remain legacy runtime output, not the G8.2 card.

## What Is Next

- Recommended immediate action: `open_optimizer_core_policy_audit_or_hold`.
- Optimizer-core implementation next action: `hold_optimizer_core_implementation_until_policy_approval`.
- Recommended next action: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.
- G9 should remain one market-behavior signal card only if approved.
- G8.3 should use a user-seeded intake item only if approved.
- A future dashboard reader should show candidate cards as status-only objects, not action labels.
- Alternative: hold.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q
```

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve G9 one market behavior signal card", "approve G8.3 one user-seeded candidate card", "approve dashboard card reader", or "hold".
