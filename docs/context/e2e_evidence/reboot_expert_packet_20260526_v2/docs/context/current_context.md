## What Was Done
- Added explicit role schema fields to replay, context, and selected-method artifact outputs.
- Centralized context normalization in strategy replay and made dashboard call the shared contract.
- Hydrated role defaults for older saved artifacts while preserving fail-closed behavior for unrelated schema drift.
- Renamed replay-facing visible weights to role-aware labels.
- Added diagnostics from the existing DashboardReplayContext.

## What Is Locked
- Lifecycle/event `weight` is audit intent; replay `target_weight` is exposure truth.
- `context_role` is the durable row-semantics field.
- Dashboard must not maintain a private replay/context normalization copy.
- Diagnostics must not rebuild replay.

## What Is Next
- Hold, or continue the separate backend dashboard_cache_signature / saved-artifact policy work.

## First Command
`.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py -q`
