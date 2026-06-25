# SAW Frontend/UI Saved Replay Source Selector - 2026-05-14

RoundID: `20260514-frontend-ui-saved-replay-selector`
ScopeID: `portfolio-allocation-replay-source-selector`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops

## Scope

Work round scope: Portfolio & Allocation consumes one `DashboardReplayContext` through a saved-artifact-first source selector, with labeled transitional backend build fallback.

Repair addendum scope: saved-artifact mode must preserve artifact event/decision rows exactly, including valid empty frames, and must not silently mix separately loaded fallback rows into `source_mode="saved_artifact"`.

Owned files changed:

```text
dashboard.py
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/*
```

Acceptance checks:

- CHK-01: Pure replay request construction is separated from artifact/backend execution.
- CHK-02: Valid saved artifact maps to `source_mode="saved_artifact"` and avoids backend rebuild.
- CHK-03: Stale/unavailable artifact clears replay/YTD state when fallback is disabled.
- CHK-04: Transitional backend build remains labeled and still works when fallback is allowed.
- CHK-05: One context feeds replay rows, latest snapshot, event rows, decision rows, and YTD latest weights.
- CHK-06: Focused compile, pytest, context validation, SE evidence validation, and SAW reviewer passes complete.
- CHK-07: Saved artifact event/decision rows remain artifact-owned and are preserved exactly when empty.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | Implementer pass validated source selector, context sharing, stale-state clearing, and factual labels. | No fix required. | Frontend/UI | PASS |
| None | Reviewer A found no in-scope correctness regression in PIT/date behavior, signatures, or single-context consumption. | No fix required. | Frontend/UI | PASS |
| None | Reviewer B found no in-scope runtime/session-state or source-labeling Critical/High issue. | No fix required. | Frontend/UI | PASS |
| None | Reviewer C found no in-scope data-integrity or performance-path Critical/High issue. | No fix required. | Frontend/UI | PASS |
| Medium | Saved-artifact mode could silently backfill empty artifact event/decision rows from separate dashboard frames. | Removed the aux-frame fallback and added empty-artifact regression coverage. | Frontend/UI | PASS |

## Scope Split Summary

in-scope findings/actions:

- Implemented and verified dashboard source selector, adapters, tests, docs, and context evidence.
- Repaired saved-artifact aux-surface preservation so empty artifact event/decision rows remain empty.
- Reconciled all reviewer passes; no in-scope Critical/High findings remain.

inherited out-of-scope findings/actions:

- Backend producers still need to emit `dashboard_cache_signature` before production saved artifacts can satisfy the dashboard UI selector without transitional fallback.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/notes.md` | Added frontend saved replay source-selector notes and evidence. | PASS |
| `docs/decision log.md` | Added source-selector decision record and contract lock. | PASS |
| `docs/lessonss.md` | Added lesson on dashboard-specific saved-artifact signatures. | PASS |
| `docs/context/bridge_contract_current.md` | Added PM/planner bridge delta for source selector. | PASS |
| `docs/context/planner_packet_current.md` | Added current/new context packet for source selector. | PASS |
| `docs/context/impact_packet_current.md` | Added changed files, touched interfaces, checks, and open risk. | PASS |
| `docs/context/done_checklist_current.md` | Added machine-checkable done criteria. | PASS |
| `docs/context/post_phase_alignment_current.md` | Added stream alignment and bottleneck. | PASS |
| `docs/context/observability_pack_current.md` | Added drift markers and evidence. | PASS |
| `docs/context/current_context.md` / `docs/context/current_context.json` | Rebuilt from the new current truth packet. | PASS |
| `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md` | Mirrored and updated report for discoverability under canonical SAW report path. | PASS |

## Verification Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `EVD-02`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_dashboard_replay_context_prefers_valid_saved_artifact tests\test_dash_2_portfolio_ytd.py::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows tests\test_dash_2_portfolio_ytd.py::test_dash_2_stale_saved_artifact_clears_replay_state_when_no_fallback -q` -> PASS, 3 passed.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 106 passed.
- `EVD-04`: `.venv\Scripts\python scripts\build_context_packet.py` and `--validate` -> PASS.
- `EVD-05`: `.venv\Scripts\python .codex\skills\_shared\scripts\validate_se_evidence.py ...` -> VALID.
- `EVD-06`: Implementer, Reviewer A, Reviewer B, and Reviewer C read-only SAW passes -> PASS.

## Closure

SAW Verdict: PASS

Open Risks: backend_dashboard_cache_signature_emission_followup; broad inherited dirty/untracked files remain outside this frontend slice.

Next action: hold_or_coordinate_backend_dashboard_cache_signature_emission

ClosurePacket: RoundID=20260514-frontend-ui-saved-replay-selector; ScopeID=portfolio-allocation-replay-source-selector; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=backend_dashboard_cache_signature_emission_followup; NextAction=hold_or_coordinate_backend_dashboard_cache_signature_emission

ClosureValidation: PASS

SAWBlockValidation: PASS
