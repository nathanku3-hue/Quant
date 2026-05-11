# G7.1C Open-Source Repo + Data/API Availability Survey

Status: research capture; source audit pending
Date: 2026-05-09
Authority: docs/research artifact only
Owner: PM / Architecture Office

## Purpose

Capture the G7.1C study result as a planning artifact before any GodView source, provider, or state-machine work.

This file intentionally does not authorize provider code, ingestion, search, ranking, dashboard runtime behavior, alerts, broker calls, candidate generation, or trading actions.

## Executive Conclusion

Open-source quant repositories mostly solve data access through four patterns:

| Pattern | Example repos | Meaning for Terminal Zero |
| --- | --- | --- |
| Unified provider abstraction | OpenBB | Best long-term architecture pattern for swappable providers and credential isolation. |
| Bring-your-own canonical data | QuantConnect LEAN, Qlib | Best truth pattern for serious research: local governed datasets with manifests. |
| Research convenience fetchers | vectorbt, FinRL, pandas-datareader, yfinance examples | Useful for discovery and examples, not canonical evidence. |
| Exchange connectors | Freqtrade, Hummingbot, CCXT | Strong connector design, mostly crypto, low direct fit for US equity/options GodView. |
| Data-agnostic backtest engines | backtesting.py / PyBroker-style tools | Useful only after clean OHLCV exists; not a source governance answer. |

Recommended architecture:

```text
OpenBB-style provider abstraction
+
LEAN/Qlib-style local canonical data discipline
+
Terminal Zero observed / estimated / inferred signal policy
+
Terminal Zero GodView state engine
```

## Boundary Lock

G7.1C is a research-capture and architecture-planning round.

Allowed now:

- record open-source architecture lessons;
- record no-cost/public API availability candidates;
- record paid/licensed gaps;
- plan the audit sequence before implementation;
- keep yfinance quarantined as Tier 2 discovery only;
- keep options, IV, whales, gamma, dark-pool, and microstructure behind provider/license decisions.

Blocked now:

- no provider code;
- no ingestion;
- no source registry implementation;
- no SEC, FINRA, CFTC, OPRA, OCC, Alpaca, or OpenBB runtime integration;
- no state machine;
- no candidate generation;
- no ranking;
- no dashboard runtime behavior;
- no alerts;
- no broker calls;
- no trading or paper-trading actions.

## Open-Source Repo Study Summary

| Repo/tool | Data-access pattern | API/data reliance | GodView fit |
| --- | --- | --- | --- |
| OpenBB | Provider-extension framework | Many provider modules; coverage depends on provider/key/subscription | High architecture reference; not a free canonical source |
| QuantConnect LEAN | Engine accepts local/custom data | Local files, cloud datasets, custom data SDK | High architecture reference; medium-low dependency fit |
| Qlib | Offline data layer and feature framework | Prepared local Qlib format; Yahoo collector examples | Medium data-pipeline reference; not enough for advanced flow |
| vectorbt | Fast data-agnostic simulation plus convenience connectors | Yahoo, Alpaca, Binance, CCXT wrappers | Medium for simulation speed; low for data governance |
| FinRL / FinRL-Meta | Unified data processor | Common Yahoo Finance examples plus processors | Medium-low; useful abstraction idea, not canonical source |
| Freqtrade | Exchange candle downloader and backtest stack | CCXT crypto exchange APIs | Low data fit; medium connector-pattern fit |
| Hummingbot | Exchange/blockchain REST/WebSocket connectors | Crypto exchange connectors | Low current fit; future connector reference only |
| CCXT | Crypto exchange connector library | Public/private crypto exchange APIs | Low for US equity/options GodView |
| pandas-datareader | Remote data wrapper into pandas | Public/keyed macro/factor/equity sources | Medium for macro/context; low for core GodView |

## API Availability Matrix

### Ready Or Already Easy In Current Repo

| Signal/data | Source/API | Availability | Use classification |
| --- | --- | --- | --- |
| Canonical daily price/volume | Existing local Tier 0 lake | Already ready | Canonical |
| Manifest/provenance | Existing repo | Already ready | Governance |
| V1/V2 mechanical replay | Existing repo | Already ready | Validation |
| Data readiness audit | Existing repo | Already ready | Governance |
| Yahoo convenience data | yfinance | Free-ish, unofficial | Tier 2 discovery only |

### Public Or Mostly Public APIs Worth Auditing For Later

| Signal/data | Source/API | Availability | Use classification |
| --- | --- | --- | --- |
| SEC submissions / XBRL facts | SEC data.sec.gov APIs | Public, no auth/API key per supplied study | High-value observed source after audit |
| 13F ownership | SEC EDGAR | Public, delayed after quarter end | Ownership whale, delayed |
| Form 4 insider trades | SEC EDGAR | Public, faster filing cycle | Insider confirmation |
| Short interest | FINRA | Public/API-style, twice monthly | Squeeze base, delayed |
| Daily short-sale volume | FINRA Reg SHO | Public, daily aggregate volume | Context only; not short interest |
| CFTC positioning | CFTC COT/TFF/Socrata | Public, weekly | CTA/systematic proxy |
| Macro/Fama-French/FRED | pandas-datareader/FRED/Ken French | Public/mixed | Context |

### Options / IV / Whale / Gamma Gap

| Signal/data | Source/API | Availability | Use classification |
| --- | --- | --- | --- |
| Consolidated options tape | OPRA | Licensed/paid | Observed options tape |
| Options volume/OI | OCC reports/data | Public reports plus data products | Observed, mostly daily |
| IV/Greeks | Tradier + ORATS | Key/account/vendor terms | Observed/model vendor |
| IV/Greeks/OI/trades | Massive/Polygon-style options API | Paid/tiered | Observed plus vendor fields |
| Real-time/historical options | ThetaData | Paid/tiered | Observed plus vendor |
| OpenBB options chains | OpenBB provider layer | Depends on provider/key | Provider abstraction |

Conclusion: options data is the largest GodView gap and should not be built from free/public scraps.

### Operational Market Data

| Signal/data | Source/API | Availability | Use classification |
| --- | --- | --- | --- |
| Latest bars/trades/quotes | Alpaca | Requires keys; feed depends on plan | Operational |
| IEX feed | Alpaca Basic | Limited single-exchange coverage | Operational/sandbox |
| SIP/full market | Alpaca paid plan | Paid/subscription | Better operational |
| Options data | Alpaca | Indicative/free vs OPRA in paid plan | Operational, not canonical by default |

### Dark Pool, Blocks, And Microstructure

| Signal/data | Source/API | Availability | Use classification |
| --- | --- | --- | --- |
| ATS/OTC transparency | FINRA OTC Transparency | Public/delayed datasets | Observed but delayed/contextual |
| OTC block summary | FINRA Developer Catalog | Public dataset family | Observed summary |
| Full order book | Nasdaq TotalView | Paid/subscription | Observed microstructure |
| Historical TAQ | NYSE TAQ / WRDS | Paid/licensed / academic | Observed historical microstructure |
| Dark-pool accumulation | Model inference | Not directly observed | Estimated only |

## Practical Roadmap Captured

P0 already ready:

- canonical daily price/volume;
- manifest/provenance;
- data readiness;
- candidate registry;
- V1/V2 replay validation;
- dashboard smoke discipline.

P1 no-cost/public candidates after audit:

- SEC filings provider design: 13F, 13D/G, Form 4, companyfacts, submissions;
- FINRA provider design: short interest, Reg SHO short-sale volume, OTC block/ATS datasets;
- CFTC provider design: COT/TFF futures positioning.

P2 provider/license decision:

- OPRA direct/vendor;
- Tradier/ORATS;
- ThetaData;
- Massive/Polygon-style API;
- OpenBB provider route.

P3 later paid/liquidity layer:

- NYSE TAQ;
- Nasdaq TotalView;
- ETF/passive flow vendor;
- dark-pool/block vendor;
- news/narrative vendor.

## Audit Queue

The supplied study cites the following source URLs. G7.1C captures them for audit; it does not mark them independently verified.

| SourceID | Topic | URL | Audit status |
| --- | --- | --- | --- |
| SRC-01 | OpenBB repo | https://github.com/OpenBB-finance/OpenBB | Pending |
| SRC-02 | OpenBB providers | https://docs.openbb.co/odp/python/extensions/providers | Pending |
| SRC-03 | QuantConnect custom data | https://www.quantconnect.com/docs/v1/algorithm-reference/importing-custom-data | Pending |
| SRC-04 | LEAN CLI custom data | https://www.quantconnect.com/docs/v2/lean-cli/datasets/custom-data | Pending |
| SRC-05 | Qlib data layer | https://qlib.readthedocs.io/en/latest/component/data.html | Pending |
| SRC-06 | Qlib Yahoo collector | https://github.com/microsoft/qlib/blob/main/scripts/data_collector/yahoo/README.md | Pending |
| SRC-07 | vectorbt features | https://vectorbt.dev/getting-started/features/ | Pending |
| SRC-08 | FinRL data layer | https://finrl.readthedocs.io/en/latest/finrl_meta/Data_layer.html | Pending |
| SRC-09 | FinRL repo/examples | https://github.com/AI4Finance-Foundation/FinRL | Pending |
| SRC-10 | Freqtrade data download | https://www.freqtrade.io/en/stable/data-download/ | Pending |
| SRC-11 | Freqtrade exchanges | https://www.freqtrade.io/en/stable/exchanges/ | Pending |
| SRC-12 | Hummingbot connectors | https://hummingbot.org/connectors/ | Pending |
| SRC-13 | CCXT repo | https://github.com/ccxt/ccxt | Pending |
| SRC-14 | pandas-datareader remote data | https://pandas-datareader.readthedocs.io/en/latest/remote_data.html | Pending |
| SRC-15 | yfinance README | https://github.com/ranaroussi/yfinance/blob/main/README.md | Pending |
| SRC-16 | SEC EDGAR APIs | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | Pending |
| SRC-17 | SEC Form 13F FAQ | https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f | Pending |
| SRC-18 | SEC Form 4 investor bulletin | https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins-69 | Pending |
| SRC-19 | FINRA short interest API PDF | https://www.finra.org/sites/default/files/Equity_Short_Interest_Data_File_Download_API.pdf | Pending |
| SRC-20 | OPRA | https://www.opraplan.com/ | Pending |
| SRC-21 | OCC open interest | https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/open-interest | Pending |
| SRC-22 | Tradier options chains | https://docs.tradier.com/reference/brokerage-api-markets-get-options-chains | Pending |
| SRC-23 | Massive options API | https://massive.com/docs/rest/options/overview | Pending |
| SRC-24 | ThetaData options | https://www.thetadata.net/options-data | Pending |
| SRC-25 | Alpaca real-time stock data | https://docs.alpaca.markets/docs/real-time-stock-pricing-data | Pending |
| SRC-26 | FINRA dataset catalog | https://developer.finra.org/catalog | Pending |

## Central Finding

Open source can teach architecture, but GodView's strongest signals - IV, options whales, gamma, dark pools, and microstructure - require licensed or paid data. The immediate no-cost path is SEC + FINRA + CFTC + existing canonical price/volume, while keeping yfinance quarantined and advanced options/GodView feeds behind a provider decision.

