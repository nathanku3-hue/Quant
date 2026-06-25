# Quant Research / Backtest Validity Expert Packet

Date: 2026-05-26
Workspace: `E:\Code\Quant`
Purpose: compact context for expert review of Terminal Zero's quant research, backtest validity, strategy evidence gates, and promotion boundaries.

## GitHub Alignment

- GitHub repo: https://github.com/nathanku3-hue/Quant
- Active branch: `codex/optimizer-core-structured-diagnostics`
- GitHub branch link: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
- Local HEAD: `cec79312e091107e9a4bbd14ba855c59f2ca5a75`
- Commit link: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75
- Alignment note: local HEAD matches the GitHub remote branch at packet creation, but the workspace has substantial uncommitted local context. This packet includes local current truth and selected dirty-worktree artifacts, so it is not a pure GitHub snapshot.

## Recommended Read Order

1. `GITHUB_ALIGNMENT.txt`
2. `docs/context/current_context.md`
3. `docs/context/planner_packet_current.md`
4. `docs/context/bridge_contract_current.md`
5. `docs/context/impact_packet_current.md`
6. `docs/context/done_checklist_current.md`
7. `docs/context/dirty_worktree_manifest.md`
8. `docs/architecture/g5_single_canonical_replay_no_alpha_policy.md`
9. `docs/architecture/portfolio_construction_contract.md`
10. `docs/architecture/optimizer_core_policy_audit.md`
11. `strategies/strategy_replay.py`
12. `scripts/pit_lifecycle_replay.py`
13. `core/engine.py`
14. `core/data_orchestrator.py`
15. `strategies/optimizer.py`
16. `strategies/portfolio_universe.py`
17. `tests/test_strategy_replay.py`
18. `tests/test_strategy_replay_artifact.py`
19. `tests/test_strategy_replay_coverage.py`
20. `tests/test_optimizer_core_policy.py`
21. `tests/test_portfolio_universe.py`
22. `QUANT_RESEARCH_BACKTEST_QUESTIONS.md`

## Included Context Classes

- Current truth surfaces: context, planner, bridge, impact, done, multi-stream, post-phase, observability, dirty-worktree manifest.
- Strategy/replay contracts: strategy replay, Rule100 lifecycle replay, optimizer policy, portfolio universe, softmax audits, adapters.
- Backtest/engine surfaces: `core/engine.py`, baseline registry, auto-backtest control plane, historical backtest scripts.
- Data integrity dependencies: data orchestrator, feature store/specs, PIT membership loader, lifecycle logs, candidate-card/discovery evidence.
- Focused tests: replay, optimizer policy, portfolio universe, pinned universe, lifecycle, data orchestrator, dashboard route/YTD, baseline and engine tests.
- Review/audit evidence: SAW reports for replay, Rule100, lifecycle, optimizer, freshness, overlay, data engineering.

## Expert Caveats

- Do not treat candidate cards, dashboard labels, optimizer outputs, or replay artifacts as validated alpha unless a testable evidence gate says so.
- Do not treat local dirty files as GitHub state. Use `GITHUB_ALIGNMENT.txt` and `GIT_STATUS_SHORT.txt`.
- The review target is research/backtest validity, not UI polish or boot-control-plane implementation.
- If a claim depends on full local data not included in this packet, mark it as "requires local run" instead of inferring validity.
