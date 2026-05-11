# GodView Observed vs Estimated Policy

Status: Phase 65 G7.1B policy draft
Date: 2026-05-09
Authority: architecture policy only, not runtime implementation

## Purpose

GodView must not present estimated market behavior as observed fact.

Every future signal must label whether it is:

```text
observed
estimated
inferred
```

This distinction is critical for operator trust, dashboard wording, source-quality review, and future state-machine design.

## Definitions

Observed:

- source reports a directly observed or official field;
- examples include price, volume, exchange/OPRA prints if licensed, official short interest, official COT, SEC filings, official/vendor OI fields.

Estimated:

- model, vendor, or internal transform estimates a hidden state from observed inputs;
- examples include CTA buying, gamma exposure, dealer positioning, whale intent, dark-pool accumulation, squeeze pressure.

Inferred:

- qualitative or composite interpretation from multiple signals or human research;
- examples include narrative velocity, thesis health, rotation state, entry discipline, hold discipline.

## Signal Family Labels

| Signal family | Label | Why |
| --- | --- | --- |
| Canonical price/volume | Observed | Reported price/volume fields in canonical artifacts. |
| Supercycle thesis docs | Inferred | Thesis health is a structured interpretation of sourced research. |
| IV / volatility surface | Estimated | Options quotes are observed; IV is model/vendor implied. |
| Options tape | Observed | Licensed prints/quotes can be observed. |
| Options whales | Estimated | Trade size is observed, but intent/classification is estimated. |
| Options OI / volume | Observed | Reported OI/volume fields if sourced. |
| Gamma / dealer map | Estimated | Dealer positioning/gamma exposure is model-estimated. |
| Short interest | Observed | FINRA reported short interest is official but lagged. |
| Squeeze pressure | Estimated | Pressure combines short, borrow, price, volume, and positioning proxies. |
| CTA / systematic pressure | Estimated | CFTC reports are observed; single-name CTA pressure is proxy/model-estimated. |
| Ownership whales | Observed | SEC filings are official records, with lag/entity-mapping caveats. |
| ETF/passive flows | Observed or estimated | Holdings/flows may be observed/vendor-derived; impact is inferred. |
| Dark pool / block | Observed plus inferred | Prints/aggregates may be observed; accumulation/distribution is inferred. |
| Microstructure | Observed | Licensed order-book/trade fields can be observed. |
| News/narrative | Inferred | Narrative velocity and sentiment require interpretation. |
| Entry/hold discipline | Inferred | Product state synthesized from thesis, price, and market behavior. |

## Dashboard Label Requirements

Future dashboard UI must separate labels:

```text
Observed: official/reported field
Estimated: model/vendor estimate
Inferred: interpretation/context
```

Forbidden dashboard wording:

- label estimated dealer gamma as observed dealer positioning;
- label options whale intent as fact;
- label dark-pool accumulation as fact from venue prints alone;
- label narrative velocity as alpha evidence;
- label lagged short interest as real-time squeeze timing.

## Allowed Use By Label

| Label | Allowed future use | Forbidden future use |
| --- | --- | --- |
| Observed | source-quality evidence, dashboard context, future paper prompt input after policy | live order trigger without later approval |
| Estimated | dashboard context and risk/crowding context after source policy | masquerade as observed truth or sole promotion evidence |
| Inferred | human review, thesis context, operator discipline | source-quality bypass, automatic signal approval |

## G7.1B Boundary

This policy adds no state machine, no confidence engine, no signal ranking, no dashboard behavior, and no provider code.
