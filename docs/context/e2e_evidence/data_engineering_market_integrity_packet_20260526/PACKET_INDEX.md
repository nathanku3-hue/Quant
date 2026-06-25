# Terminal Zero Data Engineering / Market-Data Integrity Expert Packet

Date: 2026-05-26
Workspace: `E:\Code\Quant`
Purpose: compact context for expert review of the data layer, market-data integrity, PIT discipline, replay artifacts, provider boundaries, and the proposed `Data Readiness Gate v0` for Terminal Zero boot readiness.

## GitHub Alignment

- GitHub repo: https://github.com/nathanku3-hue/Quant
- Active branch: `codex/optimizer-core-structured-diagnostics`
- GitHub branch link: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
- Local HEAD: `cec79312e091107e9a4bbd14ba855c59f2ca5a75`
- Remote branch HEAD: `cec79312e091107e9a4bbd14ba855c59f2ca5a75`
- Commit link: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75
- Alignment note: local HEAD matches GitHub remote branch, but the workspace has substantial local uncommitted changes. This packet includes local current truth surfaces and selected dirty-worktree context, so treat it as a data-integrity review packet, not a pure GitHub snapshot.

## Recommended Read Order

1. `DATA_ENGINEERING_QUESTIONS.md`
2. `docs/context/current_context.md`
3. `docs/context/planner_packet_current.md`
4. `docs/context/impact_packet_current.md`
5. `docs/context/bridge_contract_current.md`
6. `docs/context/done_checklist_current.md`
7. `docs/context/dirty_worktree_manifest.md`
8. `docs/architecture/data_source_policy.md`
9. `docs/architecture/data_infra_gap_assessment.md`
10. `core/data_orchestrator.py`
11. `strategies/strategy_replay.py`
12. `strategies/portfolio_universe.py`
13. `scripts/pit_lifecycle_replay.py`
14. `tests/test_data_orchestrator_portfolio_runtime.py`
15. `tests/test_strategy_replay.py`
16. `tests/test_strategy_replay_artifact.py`
17. `tests/test_portfolio_universe.py`
18. `tests/test_pinned_universe.py`

## Included Context Classes

- Current truth surfaces: current context, planner, impact, bridge, done, multi-stream, alignment, observability, dirty-worktree manifest.
- Data contracts: source policy, data infrastructure gaps, provider roadmap/selection, signal freshness policy, replay fixture policies.
- Runtime contracts: `core/data_orchestrator.py`, provider ports, pinned universe loader, R3000/PIT loader, portfolio universe, strategy replay, lifecycle replay.
- Static evidence objects: MU/MSFT candidate cards and manifests, discovery outputs, canonical replay reports, selected data-readiness report.
- Tests: focused data orchestrator, provider ports, PIT replay, strategy replay artifact, portfolio universe, pinned universe, dashboard route/YTD, feature store/specs.
- Evidence: selected JSON smoke/audit outputs and SAW reports for data freshness, endpoint centralization, overlay anchoring, replay identity, selected price loading, and portfolio single-source replay.

## What Is Deliberately Not Included

- Full `data/processed` parquet payloads.
- Full `data/runtime_cache` replay/overlay caches.
- Streamlit PID/stdout/stderr logs except selected JSON evidence.
- Extracted expert packets from prior reviews.

Reason: this packet is for expert judgment on contracts and boot-readiness checks, not for full local replay execution.

## Key Caveat

Do not treat every local file as committed product intent. Use the current truth surfaces and dirty-worktree manifest to separate:

- committed GitHub baseline,
- accepted but uncommitted source,
- generated evidence,
- quarantine,
- local runtime noise.

