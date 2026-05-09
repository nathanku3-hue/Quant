# Data Source Policy

Date: 2026-05-09
Authority: D-353 provenance + validation + paper-alert milestone
Status: ACTIVE

## Scope

This policy governs US equities, daily bars, validation-lab evidence, paper-only alerts, human decisioning, and audit-trail artifacts.

This policy does not authorize live trading, broker automation, intraday/HFT, options/futures, Tier 2 promotion packets, or yfinance as canonical truth.

## Source Tiers

### Tier 0: Canonical Research

Allowed uses:
- official backtests;
- validation reports;
- promotion-intent checks;
- decision-log evidence;
- governed manifests.

Approved sources:
- WRDS/CRSP/Compustat base parquet;
- TRI repaired price surfaces;
- PIT fundamentals;
- approved Capital IQ, Orbis, S&P, and Moody's sidecars with manifests;
- governed static files with row counts, hashes, source date, and schema.

Required tag:
- `source_quality = "canonical"`

### Tier 1: Operational Market Data

Allowed uses:
- paper-alert marking;
- latest quote snapshots;
- estimated bid/ask and midpoint;
- paper execution receipts;
- simulation and operator display.

Approved providers:
- Alpaca latest trade, quote, and bar snapshots.

Required tags:
- `source_quality = "operational"`
- `provider = "alpaca"`
- `provider_feed = "iex" | "delayed_sip" | "sip"`
- `quote_quality = "iex_only" | "delayed_sip_quality" | "sip_quality"`

IEX may be used only as sandbox/paper operational data and must not be reported as consolidated SIP market truth.

### Tier 2: Discovery / Convenience

Allowed uses:
- hypothesis discovery;
- dashboard convenience views;
- legacy scans while migration is in progress.

Disallowed uses:
- promotion packets;
- canonical validation reports;
- live execution truth;
- claims of institutional market-data quality.

Approved current provider:
- yfinance, behind provider ports or explicitly allowlisted legacy files only.

Required tag:
- `source_quality = "non_canonical"`

### Tier 3: Rejected For Current Scope

Rejected sources:
- crypto exchange feeds;
- derivatives libraries;
- full external trading engines;
- unofficial scraped datasets used as canonical evidence.

Required tag if encountered:
- `source_quality = "rejected"`

## Executable Invariants

The repo now enforces these rules in code and tests:

- No validation report without a manifest.
- No V1 promotion packet from Tier 2 or operational data.
- No alert or quote snapshot without `source_quality`.
- No Alpaca IEX quote may omit `quote_quality = "iex_only"`.
- No new direct yfinance import/call may appear outside the quarantine allowlist.
- No non-paper Alpaca endpoint may initialize unless both break-glass and signed-decision env gates are present.

## Manifest Fields

Every artifact that can feed a validation report must have a sidecar manifest with:

- `manifest_schema_version`
- `schema_version`
- `source_quality`
- `provider`
- `provider_feed`
- `asof_ts`
- `license_scope`
- `row_count`
- `date_range`
- `sha256`

## Implementation Map

- Manifest policy and gates: `data/provenance.py`
- Provider port contract: `data/providers/base.py`
- Yahoo quarantine adapter: `data/providers/yahoo_provider.py`
- Alpaca operational adapter: `data/providers/alpaca_provider.py`
- yfinance migration allowlist: `data/providers/legacy_allowlist.py`
- Alpaca feed/live boundary: `execution/broker_api.py`
- Alpaca SDK boundary: main environment uses `alpaca-py==0.43.4`; legacy `alpaca-trade-api` is not part of the main dependency set.
- Readiness audit: `scripts/audit_data_readiness.py`
- Minimal validation lab: `validation/`

## Current Evidence

- `data/processed/data_readiness_report.json`
- `data/processed/data_readiness_report.json.manifest.json`
- `data/processed/minimal_validation_report.json`
- `data/processed/minimal_validation_report.json.manifest.json`
- `data/processed/phase56_pead_evidence.csv.manifest.json`
