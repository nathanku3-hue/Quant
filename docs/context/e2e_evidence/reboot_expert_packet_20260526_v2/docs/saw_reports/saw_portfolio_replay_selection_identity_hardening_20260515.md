# SAW Portfolio Replay Selection Identity Hardening - 2026-05-15

RoundID: `20260515-portfolio-replay-selection-identity`
ScopeID: `portfolio-replay-selection-identity-hardening`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope

Work round scope: Portfolio & Allocation replay identity must come from explicit signed selection state, not hidden optimizer session state or first-N price-column fallback.

Owned files changed:

```text
dashboard.py
views/optimizer_view.py
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
docs/saw_reports/saw_portfolio_replay_selection_identity_hardening_20260515.md
```

Acceptance checks:

- CHK-01: Explicit `PortfolioReplaySelection` exists and is published by optimizer controls.
- CHK-02: Selection signature binds method, max-weight cap, risk-free rate, typed assets, current price-frame identity, and selected price content.
- CHK-03: Missing, stale, mismatched, or price-content-drifted selection fails closed as `portfolio_replay_selection_unavailable`.
- CHK-04: Runtime replay request construction does not use hidden `optimizer_universe` or first-10 price-column fallback.
- CHK-05: Optimizer builder errors/skips clear replay selection, replay/YTD caches, and legacy allocation mirrors.
- CHK-06: Stale saved-artifact contexts surface the concrete stale reason before empty-data copy.
- CHK-07: Aux event/decision producer ownership remains a tracked backend follow-up.
- CHK-08: Focused compile passes.
- CHK-09: Focused dashboard/optimizer pytest passes.
- CHK-10: Context build/validation and SAW reviewer gate pass.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | Implementer pass found no blocking implementation gap in explicit replay selection, cache clearing, or regressions. | No fix required. | Implementer | PASS |
| None | Reviewer A found no strategy correctness regression; hidden `optimizer_universe` and first-10 fallback are not runtime replay sources. | No fix required. | Reviewer A | PASS |
| Medium | Reviewer C found price-frame identity did not include selected price content. | Added `selected_price_hash` using `hash_pandas_object` over selected prices plus typed asset IDs; added same-shape price edit regression. | Frontend/UI | PASS |
| Medium | Reviewer C found dashboard replay cache signature stringified assets and could collide int `1` with string `"1"`. | Preserved typed asset identities in replay cache signatures and PIT input loader column matching; added int/string signature regression. | Frontend/UI | PASS |
| Medium | Reviewer B found builder exceptions could leave legacy allocation mirrors available to drift/live-weight readers. | Added allocation-session clearing on builder errors/skipped data and extended regression to prove stale optimizer weights are not reused. | Frontend/UI | PASS |
| Low | Reviewer B found stale saved-artifact reason could be hidden by empty-data copy. | Added stale-context render branch that surfaces the exact reason before empty-data handling; added focused render regression. | Frontend/UI | PASS |

## Scope Split Summary

in-scope findings/actions:

- Added signed `PortfolioReplaySelection` in `views/optimizer_view.py`.
- Dashboard validates signed selection before request construction and fails closed when unavailable.
- Removed runtime replay dependence on hidden `optimizer_universe` and first-10 fallback.
- Reconciled Reviewer B/C findings in the current patch and covered them with focused tests.

inherited out-of-scope findings/actions:

- Backend artifact producers still need to emit `dashboard_cache_signature` and own aux event/decision production for final artifact-owned replay surfaces.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/prd.md` | Added Portfolio replay selection identity product behavior and boundary. | PASS |
| `docs/spec.md` | Added signature formula with typed asset identity and selected price hash. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added live loop state, evidence, and backend aux follow-up. | PASS |
| `docs/notes.md` | Added formula/source notes for selection signature and dashboard request rule. | PASS |
| `docs/lessonss.md` | Added self-learning entry for explicit replay selection guardrail. | PASS |
| `docs/decision log.md` | Added hardcoded decision and contract lock. | PASS |
| `docs/context/bridge_contract_current.md` | Added PM/planner bridge delta. | PASS |
| `docs/context/planner_packet_current.md` | Added fresh context packet and next-step command. | PASS |
| `docs/context/impact_packet_current.md` | Added changed files, touched interfaces, checks, and open risk. | PASS |
| `docs/context/done_checklist_current.md` | Added machine-checkable done criteria. | PASS |
| `docs/context/post_phase_alignment_current.md` | Added stream alignment and bottleneck. | PASS |
| `docs/context/observability_pack_current.md` | Added drift markers for hidden state, first-N fallback, content hash, and typed assets. | PASS |
| `docs/context/current_context.md` / `docs/context/current_context.json` | Rebuilt and validated from current truth surfaces. | PASS |
| `docs/saw_reports/saw_portfolio_replay_selection_identity_hardening_20260515.md` | Published SAW report for this round. | PASS |

## Verification Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py` -> PASS.
- `EVD-02`: focused replay-selection/advisory regression subset -> PASS, 5-6 targeted tests depending on slice.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py -q` -> PASS, 88 passed.
- `EVD-04`: `.venv\Scripts\python scripts\build_context_packet.py` -> PASS after one transient Windows replace retry.
- `EVD-05`: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `EVD-06`: `git diff --check` -> PASS, line-ending warnings only.
- `EVD-07`: SAW Implementer -> PASS; Reviewer A -> PASS; Reviewer B -> PASS after runtime findings reconciled; Reviewer C -> PASS after data-integrity advisories reconciled.

## Closure

SAW Verdict: PASS

Open Risks: backend_dashboard_cache_signature_aux_producer_followup; broad inherited dirty/untracked files remain outside this frontend slice.

Next action: hold_or_coordinate_backend_dashboard_cache_signature_aux_producer_followup

ClosurePacket: RoundID=20260515-portfolio-replay-selection-identity; ScopeID=portfolio-replay-selection-identity-hardening; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=backend_dashboard_cache_signature_aux_producer_followup; NextAction=hold_or_coordinate_backend_dashboard_cache_signature_aux_producer_followup

ClosureValidation: PASS

SAWBlockValidation: PASS
