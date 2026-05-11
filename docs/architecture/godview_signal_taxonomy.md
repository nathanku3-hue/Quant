# GodView Signal Taxonomy

Status: Phase 65 G7.1A taxonomy canon
Date: 2026-05-09
Authority: G7.1A starter docs / product-spec rewrite

## Purpose

GodView is the Unified Opportunity Engine's market-behavior intelligence layer.

It reads market behavior around a thesis. It does not approve a trade, generate alpha evidence by itself, or replace source-quality rules.

## Required Metadata

Every future GodView signal must carry:

```text
source_quality
provider
provider_feed
freshness
latency
confidence
observed_vs_estimated
allowed_use
forbidden_use
manifest_uri
```

## Signal Families

### 1. IV / Volatility Surface

Question:

```text
Is implied volatility pricing stress, complacency, demand, or event risk?
```

Data status:

- current readiness: not ready;
- future source type: OPRA-style listed-options quotes/trades or licensed options vendor;
- observed vs estimated: quoted prices are observed; IV is usually vendor/model-estimated.

Allowed use:

- dashboard context after source policy.

Forbidden use:

- automatic entry/exit trigger.

### 2. Options Whales

Question:

```text
Are large options trades supporting, hedging, or crowding the thesis?
```

Data status:

- current readiness: not ready;
- future source type: options tape, open interest, volume, trade classification vendor.

Important boundary:

- unusual options activity is not automatically bullish or bearish.

### 3. Gamma / Dealer Map

Question:

```text
Could dealer positioning amplify or dampen moves near key price levels?
```

Data status:

- current readiness: not ready;
- future source type: options chain, open interest, model-estimated gamma layer.

Observed vs estimated:

- options chain and OI are observed/reporting fields;
- dealer gamma is model-estimated.

### 4. Short Squeeze

Question:

```text
Is short positioning a risk amplifier or a potential upside accelerant?
```

Data status:

- current readiness: not ready;
- future source type: FINRA short interest, stock-loan/borrow provider.

Boundary:

- lagged short-interest data is context, not a live squeeze trigger.

### 5. CTA / Systematic Pressure

Question:

```text
Are systematic trend-following flows likely supportive or hostile?
```

Data status:

- current readiness: not ready;
- future source type: CFTC COT/TFF reports, futures positioning, model proxy.

Observed vs estimated:

- CFTC reports are observed official reports;
- single-name CTA pressure is proxy/model-estimated.

### 6. Sector Rotation

Question:

```text
Is capital rotating into the thesis neighborhood or away from it?
```

Data status:

- current readiness: partially ready for price/volume proxies;
- future source type: ETF/sector flow and holdings provider.

### 7. ETF / Passive Flows

Question:

```text
Are ETF and passive flows creating support, pressure, or distortion?
```

Data status:

- current readiness: not ready;
- future source type: ETF holdings/flow provider.

### 8. Dark-Pool / ATS / Block Activity

Question:

```text
Is large off-exchange or block activity changing sponsorship context?
```

Data status:

- current readiness: not ready;
- future source type: FINRA ATS/OTC data or licensed vendor.

Boundary:

- venue prints require careful interpretation and must not be treated as simple accumulation/distribution proof.

### 9. Ownership Whales

Question:

```text
Are institutions, insiders, or activists accumulating, distributing, or changing the thesis setup?
```

Data status:

- current readiness: not ready;
- future source type: SEC 13F, 13D, 13G, Form 4 ingestion.

Boundary:

- filing lag must be visible.

### 10. Microstructure / Order Book

Question:

```text
Is liquidity improving, deteriorating, or showing execution risk?
```

Data status:

- current readiness: not ready;
- future source type: TAQ, TotalView, exchange, or vendor feed.

Boundary:

- microstructure is execution context and confidence context, not thesis approval.

### 11. Catalysts / News / Narrative Velocity

Question:

```text
Is narrative pressure confirming, exhausting, or contradicting the thesis?
```

Data status:

- current readiness: not ready;
- future source type: browser/research capture, vendor news, source-quality tagged notes.

Boundary:

- research notes may support human review but are not alpha evidence by themselves.

### 12. Regime

Question:

```text
Is the market rewarding this type of setup now?
```

Data status:

- current readiness: partially ready through existing regime and canonical price foundations;
- future source type: broadened macro, volatility, liquidity, and cross-asset context.

## State Contribution

GodView should contribute to dashboard states through labeled context:

```text
supportive
hostile
crowded
squeeze_prone
confirming
contradicting
stale
unknown
```

It should not emit direct commands.

## G7.1A Boundary

This taxonomy is documentation only. It creates no provider, ingestion job, ranking score, signal, dashboard runtime change, or prompt emission.
