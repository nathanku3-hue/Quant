# Open-Source Data Source Survey

Status: Phase 65 G7.1C architecture reference
Date: 2026-05-09
Authority: documentation and planning only; source audit pending

## Purpose

Translate the G7.1C open-source repository survey into architecture lessons for Terminal Zero's GodView roadmap.

This file records patterns to learn from. It does not select a dependency, approve a source, create a provider, or authorize ingestion.

## Pattern Verdict

| Pattern | Best reference | What to borrow | What not to borrow |
| --- | --- | --- | --- |
| Unified provider abstraction | OpenBB | Swappable provider ports, credential isolation, one interface across multiple sources | Treating the framework itself as canonical data |
| Local canonical data discipline | LEAN, Qlib | Bring-your-own governed datasets, typed custom data, offline research layer | Assuming examples/collectors are truth-grade |
| Research convenience fetchers | vectorbt, FinRL, pandas-datareader, yfinance examples | Fast exploration wrappers and notebook ergonomics | Promotion evidence, live signal authority, or source policy |
| Exchange connector architecture | Freqtrade, Hummingbot, CCXT | Adapter boundaries, exchange-specific capability maps, REST/WebSocket separation | Crypto-first assumptions for US equity/options GodView |
| Data-agnostic engines | backtesting.py / PyBroker-style tools | Clean input contracts after data is governed | Solving source provenance or licensing |

## Repo Lessons

### OpenBB

OpenBB is the closest architecture reference for a future multi-provider GodView layer because providers are separate from the core interface. The useful lesson is architectural: provider extensions should be swappable, credentials should be isolated, and one endpoint family can have multiple providers.

Fit: high architecture fit; not a canonical source by itself.

### QuantConnect LEAN

LEAN is a strong reference for separating engine logic from data sources and for making custom datasets explicit. It reinforces that local research requires bringing governed data rather than assuming the engine supplies free truth.

Fit: high as an engine/data-separation reference; medium-low as a dependency.

### Qlib

Qlib's useful lesson is that machine-learning research needs an offline data layer, feature handlers, caching, and prepared formats. Yahoo-style collectors remain example/discovery inputs, not canonical evidence.

Fit: medium for pipeline architecture; weak for advanced GodView flow signals.

### vectorbt

vectorbt is useful as a fast simulation and DataFrame wrapper reference. It solves speed and ergonomics; it does not solve provenance, licensing, source confidence, or observed-vs-estimated labeling.

Fit: medium later for proxy-speed ideas; low for source trust.

### FinRL / FinRL-Meta

FinRL's unified data processor is a useful abstraction reference, but its common examples rely on convenience market data. The design lesson is processor separation, not source approval.

Fit: medium-low.

### Freqtrade, Hummingbot, And CCXT

These tools are strong connector-pattern references for capability maps and exchange-specific behavior, but they are crypto-first and do not solve US equity/options licensing, filings, short interest, or OPRA tape.

Fit: low for current data; medium for connector design.

### pandas-datareader

pandas-datareader remains useful for macro, factors, and low-friction research context. It is not enough for core GodView source governance.

Fit: medium for macro/context; low for advanced flow.

## Architecture Decision

Terminal Zero should borrow architecture patterns, not outsource GodView source truth to a single open-source project.

Target pattern:

```text
provider ports -> source policy -> manifest/provenance -> local canonical artifacts -> state engine
```

Provider records must stay upstream of decision logic. They must not directly emit ranks, alerts, dashboard states, broker calls, or promotion verdicts.

## Boundary

No source from this survey is approved for canonical use until the audit checks:

- terms and license status;
- authentication and cost;
- as-of semantics;
- freshness/latency;
- reproducible raw locator;
- manifest compatibility;
- observed/estimated/inferred label;
- allowed and forbidden downstream uses.

