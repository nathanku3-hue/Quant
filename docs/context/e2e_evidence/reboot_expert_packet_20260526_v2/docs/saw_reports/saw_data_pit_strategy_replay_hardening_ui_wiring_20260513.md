# SAW Report - Data/PIT Strategy Replay Hardening + UI Wiring

SAW Verdict: PASS

RoundID: 20260513-data-pit-strategy-replay-hardening-ui
ScopeID: data-pit-strategy-replay-hardening-ui-wiring
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Strategy, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope

Fix audit blockers and integration risk for Strategy Replay PIT inputs: fail-closed r3000 PIT signatures, runtime-cache-only artifact writes, dashboard replay consumption of per-date `StrategyReplayInputs`, explicit cash-closed rows for empty/failed PIT dates, and docs-as-code updates.

## Acceptance Checks

- CHK-01: cache signature default is `r3000_pit` and non-PIT signatures fail closed.
- CHK-02: repo-local artifacts are confined to `data/runtime_cache/strategy_replay`; `data/processed` cache-dir escapes fail closed.
- CHK-03: dashboard Strategy Replay loads per-date `StrategyReplayInputs` and calls `build_strategy_replay(..., prices=replay_inputs, as_of_range=None)`.
- CHK-04: empty selected-asset PIT slices and per-date PIT input exceptions produce visible `cash_closed` rows.
- CHK-05: input artifacts remain price/return matrices, not target-weight output artifacts.
- CHK-06: focused compile and focused replay/data/dashboard tests pass.
- CHK-07: broader affected replay/portfolio/lifecycle/DASH tests pass.
- CHK-08: full pytest, context validation, and HTTP readiness smoke pass after reconciliation.
- CHK-09: docs-as-code surfaces and lesson loop are refreshed.

## Subagent Passes

| Role | Agent | Status | Notes |
|---|---|---|---|
| Implementer | Helmholtz | PASS | Validated r3000 PIT defaults, path guards, matrix-only artifacts, dashboard PIT input wiring, and focused tests. |
| Reviewer A | Nash | PASS | Initial Medium on dropped empty PIT dates reconciled; recheck PASS, 70 focused tests passed. |
| Reviewer B | Curie | PASS | Initial Medium on whole-section abort reconciled; recheck PASS. |
| Reviewer C | McClintock | PASS | PIT visibility improved; performance/cache-key caveats are non-blocking residuals. |

Ownership Check: PASS. Implementer and Reviewer A/B/C were different agents.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Public cache signature could bless non-PIT universe membership. | `build_strategy_replay_cache_signature(...)` now defaults to and requires `r3000_pit`; regression rejects `top_liquid`. | Data/PIT | Fixed |
| Medium | Caller-controlled `cache_dir` could make `data/processed` look like an allowed display cache. | Artifact path guard rejects repo `data/` writes outside `data/runtime_cache/strategy_replay` and rejects `cache_dir=data/processed`. | Data/PIT | Fixed |
| Medium | Dashboard replay could bypass PIT input slices by using raw `prices_wide`. | Dashboard now loads per-date `StrategyReplayInputs` and passes `prices=replay_inputs` into `build_strategy_replay(...)`. | Frontend/UI | Fixed |
| Medium | Empty selected-asset PIT dates could disappear from replay output. | Empty PIT inputs now emit `CASH` with `status=cash_closed` and reason `no_selected_assets_in_pit_universe_as_of_date`. | Backend/Strategy | Fixed |
| Medium | One PIT input exception could abort the whole replay section. | Dashboard catches per-date exceptions and emits visible `cash_closed` rows with `pit_input_exception:<type>`. | Frontend/UI | Fixed |
| Low | Dashboard replay can be cold-start expensive over many dates. | Current scope accepts bounded display cost; full pytest and HTTP smoke pass. Future optimization can project selected assets after PIT validation. | Frontend/UI | Carried |
| Low | Trimmed dashboard input cache signatures do not include selected assets. | Non-blocking because trimmed inputs are not persisted as approved artifacts. Future selected-slice artifacts must add selected asset IDs. | Data/PIT | Carried |

## Scope Split Summary

In-scope findings/actions:

- All in-scope Critical/High/Medium findings were fixed and rechecked PASS.
- No remaining in-scope Critical/High findings.

Inherited out-of-scope findings/actions:

- Broad dirty worktree remains inherited from prior/parallel rounds and was not reverted.
- Full phase-close git-sync gate is out of scope for this fix round.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/prd.md` | Historical PRD notice for PIT replay hardening and blocked scope. | PASS |
| `docs/spec.md` | Historical spec notice for r3000 PIT signatures, runtime cache root, and dashboard PIT inputs. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added Data/PIT Strategy Replay Hardening + UI Wiring addendum and acceptance checks. | PASS |
| `docs/notes.md` | Added formula/logic notes for per-date PIT inputs, empty-slice cash-closed behavior, and boundary. | PASS |
| `docs/lessonss.md` | Added lesson entry for public helper/UI PIT safety. | PASS |
| `docs/decision log.md` | Added decision record, hardcoded contract, evidence, and contract lock. | PASS |
| `docs/context/bridge_contract_current.md` | Added bridge delta and SAW reconciliation delta. | PASS |
| `docs/context/impact_packet_current.md` | Added changed files, touched interfaces, tests, and residual risks. | PASS |
| `docs/context/done_checklist_current.md` | Added machine-checkable done criteria for replay hardening. | PASS |
| `docs/context/planner_packet_current.md` | Added compact planner delta and next step. | PASS |
| `docs/context/multi_stream_contract_current.md` | Added Backend/UI/Data/Docs stream map. | PASS |
| `docs/context/post_phase_alignment_current.md` | Added stream alignment and bottleneck summary. | PASS |
| `docs/context/observability_pack_current.md` | Added drift signals for replay PIT signatures, path guards, and dropped dates. | PASS |

Document Sorting: PASS. Changed docs are shown in the checklist order for repo-local docs.

## Verification Evidence

- EVD-01: `.venv\Scripts\python -m py_compile core\data_orchestrator.py dashboard.py strategies\strategy_replay.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- EVD-02: `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 95 passed.
- EVD-03: `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_portfolio_universe.py tests\test_pinned_universe.py -q` -> PASS, 182 passed.
- EVD-04: `.venv\Scripts\python -m pytest -q` -> PASS.
- EVD-05: `.venv\Scripts\python scripts\build_context_packet.py` and `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- EVD-06: headless Streamlit readiness on `http://127.0.0.1:8513/portfolio-and-allocation` -> PASS; process stopped after check.
- EVD-07: Reviewer A/B/C rechecks after reconciliation -> PASS, no remaining Critical/High/Medium findings.

## Top-Down Snapshot

L1: Terminal Zero Data/PIT Replay Safety
L2 Active Streams: Backend/Strategy, Frontend/UI, Data, Docs/Ops
L2 Deferred Streams: target-weight artifact persistence, provider ingestion, broker/alerts
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Data
Active Stage Level: L3

+--------------------+----------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope        | Rating | Next Scope                                                   |
+--------------------+----------------------+--------+--------------------------------------------------------------+
| Planning           | B:PIT/OH:Data/AC:9   | 100/100| 1) hold_or_collect_output_evidence [84/100]: scope closed    |
| Executing          | guards+UI wiring     | 100/100| 1) no in-scope code blockers [92/100]: fixes rechecked PASS  |
| Iterate Loop       | SAW meds fixed       | 100/100| 1) preserve cash_closed dates [95/100]: implemented/tests    |
| Final Verification | pytest+smoke+context | 100/100| 1) publish report [94/100]: closure packet validated next    |
| CI/CD              | not requested        | 0/100  | 1) no git sync in this round [70/100]: not phase close       |
+--------------------+----------------------+--------+--------------------------------------------------------------+

## Open Risks:

- Dashboard PIT replay can still be cold-start expensive if the visible replay horizon grows; current readiness smoke and tests pass.
- If future work persists selected-slice replay artifacts, selected asset IDs must enter that artifact signature.
- Broad inherited dirty/untracked worktree remains and was not reverted.

## Rollback Note:

Revert the Data/PIT replay hardening changes in `core/data_orchestrator.py`, `dashboard.py`, `strategies/strategy_replay.py`, the replay-focused tests, and the matching docs/context updates. Display-only artifacts under `data/runtime_cache/strategy_replay` can be deleted without affecting canonical market data.

Next action: hold_or_collect_strategy_replay_multi_date_output_evidence

SAWBlockValidation: PASS
ClosureValidation: PASS
ClosurePacket: RoundID=20260513-data-pit-strategy-replay-hardening-ui; ScopeID=data-pit-strategy-replay-hardening-ui-wiring; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=dashboard_replay_cold_start_cost_and_future_selected_slice_signature_if_persisted; NextAction=hold_or_collect_strategy_replay_multi_date_output_evidence
