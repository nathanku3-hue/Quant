# SAW Report - Overlay Overlap Anchor Fix

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Data, Frontend/UI, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: SAW-20260514-OVERLAY-ANCHOR
ScopeID: overlay_overlap_anchor_fix

## Scope

Implement option A: require same-ticker local/live overlap before scaled live overlays can feed selected-price or benchmark evidence.

## Acceptance Checks

- CHK-01: No public permissive no-overlap overlay flag remains.
- CHK-02: Selected-price no-overlap stale assets are dropped instead of stitched.
- CHK-03: Benchmark no-overlap stale tickers are dropped instead of stitched.
- CHK-04: Docs/truth surfaces state no-overlap overlays are unavailable/dropped evidence.
- CHK-05: Focused and affected stale-data tests pass.
- CHK-06: SAW Implementer and Reviewer A/B/C passes complete with different agents.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | Adjacent replay/YTD session state can retain `strategy_replay_latest_weights` when replay latest snapshot is empty/all-CASH, while `_current_optimizer_weights()` prefers that key. This is outside the live-overlay anchor scope. | Carry as future replay-state hygiene work; do not block overlay-anchor closure. | Frontend/UI | Open / Future |

## Scope Split Summary

In-scope actions completed:

- `scale_live_overlay_to_local(...)` now requires same-column local/live overlap and has no public permissive no-overlap evidence flag.
- `refresh_selected_prices_with_live_overlay(...)` uses the strict scaler; unanchored live columns are dropped by the existing freshness gate.
- `merge_benchmark_live_overlay(...)` now requires same-ticker overlap before scaling benchmark overlays.
- `build_benchmark_equity_from_prices(...)` identifies live data that was available but not overlap-anchorable and drops the stale benchmark ticker.
- Regression tests cover selected no-overlap dropping and benchmark no-overlap dropping.
- Current notes, decision log, lessons, and context surfaces document the invariant.

Inherited out-of-scope findings/actions:

- Saved replay artifact-reader consumption and explicit cold-start/rerun performance budget remain future work.
- Broad inherited dirty/untracked files remain present and were not reverted.
- The adjacent replay/YTD session-state advisory remains a future hygiene item.

## Document Changes Showing

- `docs/notes.md` - added scaled-overlay same-overlap evidence rule - reviewer status: PASS.
- `docs/decision log.md` - locked no-overlap scaling as non-evidence - reviewer status: PASS.
- `docs/lessonss.md` - added self-learning guardrail for scaled live overlays - reviewer status: PASS.
- `docs/context/bridge_contract_current.md` - added PM bridge for overlap-anchor fix - reviewer status: PASS.
- `docs/context/planner_packet_current.md` - added fresh New Context Packet for this round - reviewer status: PASS.
- `docs/context/done_checklist_current.md` - added machine-checkable overlay-anchor criteria - reviewer status: PASS.
- `docs/context/impact_packet_current.md` - added touched interfaces and evidence - reviewer status: PASS.
- `docs/context/multi_stream_contract_current.md` - added stream coordination note - reviewer status: PASS.
- `docs/context/post_phase_alignment_current.md` - added no-overlap non-evidence alignment - reviewer status: PASS.
- `docs/context/observability_pack_current.md` - added drift signals for no-overlap overlay scaling - reviewer status: PASS.

## Document Sorting

1. `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md`
2. `docs/context/bridge_contract_current.md`
3. `docs/context/done_checklist_current.md`
4. `docs/context/impact_packet_current.md`
5. `docs/context/multi_stream_contract_current.md`
6. `docs/context/post_phase_alignment_current.md`
7. `docs/context/observability_pack_current.md`
8. `docs/context/planner_packet_current.md`
9. `docs/context/current_context.md`, `docs/context/current_context.json`

## Verification Evidence

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q` -> PASS, 110 passed.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- SAW Implementer pass -> PASS; key overlay tests 3 passed and direct YTD suite 54 passed.
- SAW Reviewer A strategy correctness -> PASS; targeted overlay/YTD/optimizer tests 9 passed.
- SAW Reviewer B runtime/operational resilience -> PASS; affected suite 110 passed.
- SAW Reviewer C data integrity/performance -> PASS; focused regression command 11 passed and no canonical market-data write path found.

## Ownership Check

- Implementer: `019e25fb-86dd-7470-9825-b63551e10411`.
- Reviewer A: `019e25fb-8746-79e1-b48b-ce344dba19d6`.
- Reviewer B: `019e25fb-87b7-7c92-a8dc-276b8495df11`.
- Reviewer C: `019e25fb-8838-7523-a1ff-ea7d68335c54`.
- Implementer and reviewers are different agents: PASS.

## Closure

ChecksTotal: 6
ChecksPassed: 6
ChecksFailed: 0

Open Risks:

- Adjacent replay/YTD session-state advisory is out of scope for this overlay-anchor fix.

Next action:

- Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.

ClosurePacket: RoundID=SAW-20260514-OVERLAY-ANCHOR; ScopeID=overlay_overlap_anchor_fix; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=adjacent replay YTD session-state advisory out of scope; NextAction=hold or separately approve replay-state hygiene or saved replay artifact-reader performance-budget work

ClosureValidation: PASS
SAWBlockValidation: PASS
