# Laptop Quant Implementation Plan

Date: 2026-05-09
Status: Planning artifact
Scope: Provenance + validation + paper-alert roadmap, data-source policy, yfinance/Alpaca decision, and step-by-step implementation plan

## Executive Decision

This is not a trading-system milestone yet. It is a provenance + validation + paper-alert milestone.

Do not delete `yfinance` immediately.

Do remove `yfinance` from any path that claims canonical research quality, promotion readiness, or live execution truth. Keep it only as a quarantined convenience provider until an audited replacement exists.

Use Alpaca for:

- latest quote snapshots,
- paper-trading execution receipts,
- paper alert mark/fill simulation,
- future official live market-data provider if SIP entitlement is available.

Do not use Alpaca as a replacement for the full historical research lake. Alpaca is useful for live/paper operations, but it is not a substitute for WRDS/CRSP/Compustat/Capital IQ/Orbis historical governance.

Live Alpaca credentials must not be committed, logged, embedded in docs, or used in this milestone. This milestone is paper-only unless a later signed decision explicitly changes the scope.

## Current Infra Assessment

Terminal Zero already has enough infrastructure for the next stage if scope is:

- US equities,
- daily bars,
- paper-only alerts,
- human-in-the-loop decisions,
- canonical research through existing parquet/WRDS-style artifacts.

Evidence in the repo:

- `data/processed/prices.parquet`: large WRDS-style base lake.
- `data/processed/prices_tri.parquet`: TRI repaired signal price path.
- `data/processed/fundamentals.parquet`, `fundamentals_pit.parquet`, `daily_fundamentals_panel.parquet`: fundamental surfaces.
- `data/processed/fundamentals_sdm.parquet`, `features_sdm.parquet`: SDM feature paths.
- `data/processed/orbis_daily_aligned.parquet`, `sidecar_moodys_bd.parquet`, `sidecar_sp500_pro*.parquet`: bounded sidecar/provenance surfaces.
- `data/processed/phase56_pead_summary.json`, `phase57_corporate_actions_summary.json`, `phase60_governed_audit_summary.json`: evidence trails for existing strategy families.
- `execution/broker_api.py`: Alpaca paper broker wrapper with live-trading break-glass protection.
- `execution/risk_interceptor.py`: risk gate already exists.
- `scripts/execution_bridge.py`: payload generation and notification hook already exists.
- `core/data_orchestrator.py` and `data/dashboard_data_loader.py`: separation between historical parquet mode and legacy live mode already started.

Current infra is not enough for:

- intraday or HFT research,
- options/futures/derivatives,
- reliable live execution automation,
- institutional real-time market-data coverage without paid feeds,
- non-US universes,
- strategy promotion from `yfinance` or free IEX-only data.

## Hard Invariants

These are runtime/CI fail-closed rules, not just documentation preferences.

1. No alert without a `source_quality` tag.
2. No validation report without a manifest.
3. No promotion packet from Tier 2 data.
4. No execution path without `BrokerPort` plus a signed decision.
5. No live Alpaca order path in this milestone.
6. No provider credential in source, docs, tests, shell logs, or generated artifacts.
7. No Yahoo-derived artifact may be silently upgraded to canonical status.
8. No Alpaca IEX/free quote may be reported as SIP/consolidated market truth.

## Data Source Policy

Adopt four explicit data tiers.

### Tier 0: Canonical Research

Allowed to drive backtests, validation gates, promotion packets, and decision logs.

- WRDS/CRSP/Compustat base parquet.
- TRI repaired surfaces.
- PIT fundamentals.
- Approved Capital IQ / Orbis / S&P sidecars with manifests.
- Governed static files with row counts, hashes, source date, and schema.

### Tier 1: Operational Market Data

Allowed to mark paper alerts, quote latest price, estimate current bid/ask, and simulate fills.

- Alpaca latest trade/quote/bar.
- Alpaca historical bars only when explicitly marked operational or replay support.
- Prefer SIP where entitlement exists; free IEX is acceptable only for sandbox/paper labels.

### Tier 2: Discovery / Convenience

Allowed to generate hypotheses and dashboard convenience views, not promotion evidence.

- `yfinance`.
- OpenBB adapters.
- public web/API feeds.

Every Tier 2 artifact must carry `source_quality = "non_canonical"` and cannot enter V1 promotion.

### Tier 3: Rejected For Current Scope

- crypto exchange feeds,
- derivatives libraries,
- full external trading engines,
- unofficial scraped datasets used as if canonical.

## yfinance Decision

Do not delete now. Quarantine and phase down.

Reasoning:

- The repo currently uses `yfinance` in `data/updater.py`, `data/fundamentals_updater.py`, `data/calendar_updater.py`, `dashboard.py`, `execution/alpha_sniper.py`, and `scripts/strong_buy_scan.py`.
- Deleting it now would break existing dashboard/update paths without improving canonical evidence.
- The `yfinance` project states it is not affiliated with Yahoo and is intended for research/educational use; Yahoo data rights remain governed by Yahoo terms.
- Therefore, it is unsuitable for promoted research truth or live execution truth.

Action:

1. Keep `yfinance` installed for now.
2. Rename its logical role from "live data bridge" to "non-canonical convenience patch".
3. Add source metadata to every Yahoo-derived artifact.
4. Block Yahoo-derived artifacts from V1 promotion packets.
5. Replace dashboard calls gradually with provider-port calls.
6. Delete only after all uses are behind adapters and Alpaca/OpenBB/vendor replacements pass tests.

## Alpaca Decision

Use Alpaca, but do not overclaim it.

Alpaca is already the right operational provider for paper execution and quote snapshots because the repo has an `AlpacaBroker` wrapper with paper-default safety.

Important constraints from Alpaca documentation:

- Alpaca historical stock data supports multiple feeds via a `feed` parameter.
- Free IEX data is a single-exchange feed and is described by Alpaca as about 2.5% of market volume.
- SIP covers all US exchanges and consolidated quote/trade activity, but recent SIP/latest endpoint access can require subscription.
- Alpaca market-data plans advertise 7+ years of history, which is not a replacement for the repo's 2000-2024 canonical lake.

Action:

1. Use Alpaca for latest quote snapshots in paper alert marking.
2. Use Alpaca paper account for execution receipt tests only.
3. Add `feed = iex | delayed_sip | sip` to all Alpaca market-data calls.
4. Mark IEX-derived quotes as `quote_quality = "iex_only"`.
5. Require SIP or delayed SIP for any report that claims operational mark quality.
6. Keep WRDS/CRSP/Compustat/sidecars as canonical historical research.

## Step-By-Step Plan

### Phase A: Scope Freeze And Source Policy

Goal: prevent data-source ambiguity before more strategy work.

Steps:

1. Write `docs/architecture/data_source_policy.md`.
2. Define `canonical`, `operational`, `discovery`, and `rejected` source tiers.
3. Add decision-log entry: yfinance is non-canonical; Alpaca is operational, not historical canonical.
4. Add `source_quality`, `provider`, `provider_feed`, `asof_ts`, and `license_scope` fields to planned manifests.
5. Acceptance check: no doc claims Yahoo/Alpaca free data is promotion-grade.

### Phase B: Provenance Manifest Enforcement

Goal: make provenance the first executable gate.

Steps:

1. Add manifest schema for research artifacts, operational quotes, alerts, and validation reports.
2. Add required fields: `source_quality`, `provider`, `provider_feed`, `asof_ts`, `license_scope`, `row_count`, `date_range`, `schema_version`, `sha256`.
3. Hash every emitted parquet/JSONL/CSV artifact that can feed a validation report.
4. Add fail-closed read check for canonical validation: missing manifest means non-canonical.
5. Add CI/runtime invariant tests:
   - validation report without manifest fails,
   - promotion packet from Tier 2 source fails,
   - alert without source-quality tag fails.
6. Acceptance check: validation code refuses Yahoo/Alpaca operational artifacts for V1 promotion.

### Phase C: Provider Ports

Goal: stop direct provider calls from spreading.

Steps:

1. Add `data/providers/base.py` with `MarketDataPort`.
2. Add `data/providers/yahoo_provider.py` wrapping current yfinance paths.
3. Add `data/providers/alpaca_provider.py` for latest quote/bar snapshots.
4. Add config selector: `TZ_MARKET_DATA_PROVIDER=yahoo|alpaca`.
5. Replace direct `yf.download` in new code with provider-port calls.
6. Acceptance check: `rg "import yfinance|yf\\."` shows only provider modules and legacy files explicitly listed in a migration allowlist.

### Phase D: Data Health Audit

Goal: decide if the current local lake is enough for daily US-equity paper alerts.

Steps:

1. Build `scripts/audit_data_readiness.py`.
2. Check presence of `prices_tri.parquet`, fundamentals, ticker map, sector map, macro, liquidity, sidecars.
3. Check date ranges, null rates, duplicate `(date, permno)`, return/price continuity, split continuity, and universe coverage.
4. Emit `data/processed/data_readiness_report.json`.
5. Acceptance check: report returns `ready_for_paper_alerts = true|false` with blockers.

### Phase E: Methodology Lab Minimal Gates

Goal: implement the useful anti-overfit gates first.

Steps:

1. Add `validation/schemas.py` with `ValidationReport`.
2. Add `validation/oos.py`.
3. Add `validation/walk_forward.py`.
4. Add `validation/regime_tests.py`.
5. Add `validation/permutation.py`.
6. Add `validation/bootstrap.py`.
7. Add tests using synthetic strategies with known pass/fail behavior.
8. Acceptance check: one existing PEAD-style return stream can run through the minimal validation lab.

### Phase F: Candidate Registry

Goal: make multiple-testing correction possible later.

Steps:

1. Add `v2_discovery/registry.py`.
2. Store candidate metadata before results are evaluated.
3. Required fields: `candidate_id`, `family_id`, `hypothesis`, `universe`, `features`, `parameters_searched`, `trial_count`, `train_window`, `test_window`, `cost_model`, `data_snapshot`, `status`.
4. Add append-only state transitions.
5. Acceptance check: a dummy candidate round-trips through `generated -> incubating -> rejected`.

### Phase G: Canonical Backtest And V2 Proxy Boundary

Goal: keep fast experimentation separate from official truth.

Steps:

1. Keep `core/engine.py` as official V1 truth.
2. Add V2 proxy simulator only under `v2_discovery/fast_sim/`.
3. Stamp V2 outputs with `promotion_ready = false`.
4. Require V1 re-run for every promotion packet.
5. Acceptance check: schema prevents proxy-only results from becoming promoted.

### Phase H: Risk-To-Alert Packet

Goal: turn validated research into human-readable paper alerts.

Steps:

1. Define `AlertRecord` schema.
2. Define alert fields: symbol, side, reference price, max size, confidence, expiry, validation summary, risk decision, source feed, source quality, idempotency key.
3. Use `RiskInterceptor` before alert creation.
4. Use Alpaca quote snapshot for operational mark.
5. If Alpaca unavailable, degrade to no-alert or stale-alert warning rather than Yahoo fallback.
6. Add invariant test: alert cannot be emitted without risk decision and source-quality tag.
7. Acceptance check: dry-run alert packet emits without broker order capability.

### Phase I: Paper Trading Loop

Goal: prove live-time behavior with zero capital.

Steps:

1. Add paper portfolio state.
2. Record signal time, quote time, alert time, next bar, hypothetical fill, slippage, and PnL.
3. Track stale alerts, missed fills, cancellations, and manual overrides.
4. Persist every paper decision with manifest pointer and alert idempotency key.
5. Require minimum sample before any live-trading decision.
6. Acceptance check: daily paper report shows hit rate, avg slippage, stale rate, drawdown, and rejected-alert count.

### Phase J: Advanced Anti-Overfit Gates

Goal: add heavier tests only after candidate volume exists.

Steps:

1. Add multiple-testing module: Bonferroni, Holm, Benjamini-Hochberg/FDR.
2. Add PSR.
3. Add DSR.
4. Add PBO/CSCV.
5. Add Reality Check / SPA wrapper.
6. Acceptance check: registry trial counts flow into DSR and multiple-testing outputs.

### Phase K: OpenClaw Notification

Goal: deliver paper alerts through the human channel.

Steps:

1. Add `notifiers/base.py`.
2. Add `notifiers/openclaw_notifier.py`.
3. Add `notifiers/discord_webhook_notifier.py` only as legacy optional path.
4. Persist every sent alert to JSONL or DuckDB.
5. Add cancellation and correction alert types.
6. Acceptance check: dry-run OpenClaw notification emits payload without requiring live broker execution.

### Phase L: Broker Automation Decision

Goal: keep live trading behind an explicit capital decision.

Steps:

1. Finish `BrokerPort` in Phase 63.
2. Keep Alpaca paper implementation behind `BrokerPort`.
3. Evaluate `ib_async` only after BrokerPort tests pass.
4. Require user sign-off and decision-log entry before live execution.
5. Acceptance check: no code path can place live orders without explicit break-glass and signed decision.

## Top-Level Roadmap

1. Platform hygiene: Phase 62-65.
2. Source policy and provenance: yfinance quarantine, Alpaca operational tier, canonical data manifests.
3. Provider ports: no new direct provider calls outside adapters.
4. Data health audit: prove readiness before strategy work.
5. Minimal validation lab: OOS, WFO, regime, permutation, bootstrap.
6. Candidate registry: every idea logged before results.
7. Risk and sizing: risk decision before alert.
8. Paper portfolio: live-time zero-capital evidence.
9. Advanced anti-overfit gates: DSR, PBO/CPCV, Reality Check/SPA.
10. Broker decision: only after paper evidence and explicit approval.

## Direct Answer

Current infra and data layer are sufficient for the next one-man quant milestone if the milestone is provenance + validation + daily US-equity paper alerts.

Current infra and data layer are not sufficient for fully automated live trading or institutional real-time execution.

Do not delete `yfinance` today. Quarantine it, forbid it from canonical evidence, and gradually replace direct calls with provider ports.

Use Alpaca now for paper-execution operations and quote snapshots. Use Alpaca as a broader market-data replacement only if the account has appropriate feed entitlement, preferably SIP or delayed SIP depending on latency needs.

Do not use pasted live Alpaca credentials in this milestone. If credentials are needed later, provide them through environment variables or a secret manager outside git, and use the paper endpoint by default.

## Sources Checked

- yfinance README: https://github.com/ranaroussi/yfinance
- Alpaca historical stock data: https://docs.alpaca.markets/v1.3/docs/historical-stock-data-1
- Alpaca market data FAQ: https://docs.alpaca.markets/docs/market-data-faq
- Alpaca market data plans: https://alpaca.markets/data
- Terminal Zero local files: `AGENTS.md`, `PHASE_QUEUE.md`, `data/updater.py`, `data/dashboard_data_loader.py`, `core/data_orchestrator.py`, `execution/broker_api.py`

## Confidence

Confidence: 8/10.

The source-policy decision is high confidence. Exact Alpaca replacement scope depends on the user's Alpaca data subscription and whether the system needs SIP-quality real-time marks or only delayed/paper marks.
