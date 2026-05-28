# Governance Boundary Policy - Gate v0

Date: 2026-05-26
Scope: Terminal Zero local-first quantitative research console
Status: v0 mechanical boot boundary

## Mission

Boot-ready means research-only boundaries are mechanically enforced, not only that the app imports and renders. Governance Gate v0 blocks action-shaped UI language, missing candidate-card governance, score/rank/action fields in research objects, runtime broker/order/alert enablement, and unbound candidate-card artifacts.

The scanner is intentionally narrow. It scans runtime/UI files and candidate-card JSON bundles, while ignoring docs, tests, patch files, zip packets, historical packets, and generated evidence by default.

## Canonical Disclaimer

Research-only console. Terminal Zero outputs are local research context, historical replay, simulation weights, and diagnostics only. They are not investment advice, recommendations, rankings, suitability determinations, price targets, alerts, orders, broker instructions, or authorization to trade.

The disclaimer is required but not sufficient. It cannot substitute for hard gates on action-shaped labels, score/rank displays, optimizer outputs that look like allocation instructions, replay codes shown as trade instructions, alert/broker/order pathways, missing governance fields, or manifest/hash gaps.

## Gate Rules

```text
GOV-000 artifact-vs-root drift:
  If governance_gate_v0.patch or governance_gate_v0_implementation_20260526.zip exists, expected root files and boot integration must exist.

GOV-001 runtime defaults:
  T0_GOVERNANCE_MODE defaults to research_only; alert, broker, order, escalation, and notifier flags are disabled by default.

GOV-002 UI-visible phrases:
  dashboard.py and views/*.py string literals must not contain action-shaped visible phrases such as Strong Buy, BUY AGGRESSIVE, ENTER: BUY, Action Status, Buy/Sell Decision Log, investment recommendation, trade alert, broker order, Estimated Shares, EXECUTE IF, or Qualifying Tickers. Exact neutral research-console labels such as Portfolio & Allocation, Entry/Exit Strategy, Replay allocation snapshot, Current allocation snapshot, Entry/Exit Events, ENTER event, EXIT event, Replay Weight, Current Weight, and Context Role are allowed only as exact labels.

GOV-003 candidate-card flags:
  Candidate cards must include governance and forbidden_outputs objects with explicit true flags for no score, no rank, no buy/sell signal, no buying range, no alert, no broker action, not validated, and not actionable.

GOV-004 candidate-card forbidden fields:
  Candidate cards must not expose score, rank, target price, buying range, entry price, stop loss, buy/sell/hold signal, alert, broker, order, or equivalent fields except as negated governance flags.

GOV-005 replay-code display:
  Internal BUY/SELL/HOLD/ENTER/EXIT replay codes are allowed in storage and logic, but v0 display phrase checks must keep them from being presented as trade instructions.

GOV-007 dashboard/view action-token scan:
  Default dashboard and view source paths must not contain broker/order/trade-alert action tokens such as submit_order, broker_call, order_action, buy_alert, sell_alert, entry_alert, exit_alert, rebalance_alert, or ticker_action_alert.

GOV-008 manifest binding:
  Candidate cards must point to sidecar manifests whose artifact_uri and artifact_sha256 match the card bytes.

GOV-009 execution-module inventory:
  Broker/order/rebalance/notifier/alert surfaces in execution-sensitive files must be scanned and classified through docs/context/execution_module_inventory_current.json. Classifications are dead_code_historical, test_fixture, ops_health_only, research_only_blocked, and unknown_blocker. Any unknown_blocker, uncovered sensitive term, stale manifest entry, missing evidence token, or execution import from default dashboard/view boot surfaces fails governance preflight.
```

## Execution Inventory Scope

GOV-009 scans these execution-sensitive surfaces by default:

```text
execution/broker_api.py
execution/rebalancer.py
main_console.py
main_bot_orchestrator.py
scripts/test_rebalance.py
scripts/test_alpaca_connection.py
scripts/execution_bridge.py
data/providers/alpaca_provider.py
execution/execution_payload_*.json
views/drift_monitor_view.py
```

The inventory is a research-only boot proof, not an authorization layer. Real broker/order paths remain blocked from default research boot unless separately approved; historical execution payloads remain inert; drift alerts are ops-health only when no broker/order/webhook path is reachable; replay output remains outside this gate and is still uncertified unless a separate replay-output artifact certificate exists.

## Candidate-Card Required Flags

```json
{
  "not_validated": true,
  "not_actionable": true,
  "no_score": true,
  "no_rank": true,
  "no_buy_sell_signal": true,
  "no_buying_range": true,
  "no_alert": true,
  "no_broker_action": true
}
```

## Boundary

Gate v0 does not approve trading, alerts, broker connectivity, candidate scoring, ranking, recommendations, provider ingestion, or dashboard candidate-card promotion. It only adds a mechanical boot blocker for existing research-only boundaries.
