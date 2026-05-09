# Laptop Quant Stack Review

Date: 2026-05-09
Status: Advisory research note
Scope: External repo list, methodology ladder, and top-level roadmap for a one-person laptop quant system

## Executive Verdict

The proposal is helpful, but only if treated as a methodology and reference map rather than a shopping list of dependencies.

For Terminal Zero, the right synthesis is:

1. Keep this repo as the system of record.
2. Use external repos as study material and spike references.
3. Add only narrow adapters or libraries after a phase gate justifies them.
4. Make the first production deliverable a paper-trading alert loop, not auto-execution.

The strongest sentence in the proposal is: the first alpha is not a trading signal, it is a research operating system that kills bad strategies automatically.

## Original Proposal Snapshot

The source proposal recommends starting with `stefan-jansen/machine-learning-for-trading` as the best single learning repo, then studying an ordered stack:

1. `stefan-jansen/machine-learning-for-trading`
2. `microsoft/qlib`
3. `QuantConnect/Lean`
4. `polakowo/vectorbt`
5. `nautechsystems/nautilus_trader`
6. `kernc/backtesting.py`
7. `OpenBB-finance/OpenBB`
8. `PyPortfolio/PyPortfolioOpt`
9. `dcajasn/Riskfolio-Lib`
10. `cvxgrp/cvxportfolio`

It then groups broader repos by subsystem:

- Learning and notebooks: ML4T, Packt ML trading, FinRL, FinRL-X, TradeMaster, Qlib.
- Backtesting engines: Qlib, Lean, vectorbt, NautilusTrader, backtesting.py, backtrader, bt, finmarketpy, zipline, vn.py.
- Data: yfinance, OpenBB, pandas-datareader, AKShare, TuShare, cryptofeed, ccxt, ArcticDB, Arctic.
- Portfolio and risk: PyPortfolioOpt, Riskfolio-Lib, cvxportfolio, ffn, quantstats, pyfolio, alphalens, empyrical.
- Derivatives and quant finance math: QuantLib, FinancePy, tf-quant-finance, gs-quant, pyql, smaller option libraries.
- Crypto systems: freqtrade, hummingbot, jesse, ccxt, cryptofeed, example strategy repos.
- Broker/execution APIs: ib_async, ib_insync, Lean, vn.py, NautilusTrader.

The methodology proposal asks Terminal Zero to become a validation laboratory first:

`idea -> clean data -> baseline backtest -> OOS -> walk-forward -> bootstrap/permutation -> multiple-testing correction -> regime stratification -> CPCV if labels overlap -> PSR/DSR -> Reality Check -> paper trading -> tiny live capital only after gates`

## Research Check

The main recommendation is directionally right.

- `stefan-jansen/machine-learning-for-trading` is a strong curriculum reference: the repo says it contains 150+ notebooks covering data, signals, ML models, backtesting, and evaluation.
- `microsoft/qlib` is a serious ML quant platform: its own README describes an AI-oriented investment platform covering data processing, model training, backtesting, alpha, risk, portfolio optimization, and order execution.
- `QuantConnect/Lean` is a professional event-driven architecture reference: its README describes a modular, professional-caliber algorithmic trading platform with backtesting and live trading support.
- `vectorbt` is the right mental model for the V2 fast simulator: its README emphasizes matrix/vectorized sweeps over many configurations.
- `NautilusTrader` is the best production-architecture study target: its README describes a Rust-native engine spanning research, deterministic simulation, and live execution with Python strategy orchestration.
- `OpenBB` is useful for data adapter thinking: its README frames it as a data integration layer for Python, APIs, dashboards, and AI agents.
- `PyPortfolioOpt`, `Riskfolio-Lib`, and `cvxportfolio` map well to allocator and risk research, but should not all become dependencies.

The methodology claims are also right in spirit:

- White's Reality Check exists to control data snooping across many tested rules.
- Harvey, Liu, and Zhu argue that usual factor-significance hurdles are too low after many factors have been tested.
- Bailey, Borwein, Lopez de Prado, and Zhu's PBO work uses combinatorially symmetric cross-validation to estimate backtest overfitting risk.
- PSR/DSR are appropriate later-stage gates for short samples, non-normal returns, and strategy selection bias.

## Modified Stack For This Repo

Terminal Zero should not clone and absorb every stack. Use this modified stack instead.

### Tier A: Learn And Mine Ideas

Use these as reading material and pattern sources, not dependencies:

- `stefan-jansen/machine-learning-for-trading`
- `microsoft/qlib`
- `QuantConnect/Lean`
- `nautechsystems/nautilus_trader`
- `OpenBB-finance/OpenBB`
- `AI4Finance-Foundation/FinRL-Trading`

Output expected from each: one short design note, not imported code.

### Tier B: Candidate Dependencies Or Spikes

Only add after a phase brief names the exact interface and acceptance checks:

- `PyPortfolio/PyPortfolioOpt`: candidate for simple allocator prototypes.
- `dcajasn/Riskfolio-Lib`: candidate for advanced risk and risk parity research.
- `polakowo/vectorbt`: candidate reference for V2 fast simulator behavior; avoid hard dependency until compatibility and license posture are clear.
- `OpenBB-finance/OpenBB`: candidate data adapter layer; keep optional.
- `ib-api-reloaded/ib_async`: candidate Interactive Brokers adapter for a future BrokerPort implementation.

### Tier C: Study Only

Useful to read, but not useful enough to import:

- `QuantConnect/Lean`
- `nautechsystems/nautilus_trader`
- `cvxgrp/cvxportfolio`
- `stefan-jansen/zipline-reloaded`
- `mementum/backtrader`
- `pmorissette/bt`
- `pmorissette/ffn`
- `ranaroussi/quantstats`
- `quantopian/alphalens`
- `quantopian/empyrical`

### Tier D: Reject Or Defer

Reject for current scope unless a later decision log entry reopens them:

- Crypto execution systems.
- Derivatives pricing stacks.
- Deep RL stacks.
- Legacy archived wrappers.
- Full replacement engines.
- Duplicate book-code forks.

## Repo Decision Matrix

| Repo | Decision | Why |
|---|---:|---|
| `stefan-jansen/machine-learning-for-trading` | Study | Best curriculum reference; no dependency need. |
| `PacktPublishing/Machine-Learning-for-Algorithmic-Trading-Second-Edition` | Reject | Duplicate of the Jansen learning path. |
| `microsoft/qlib` | Study / later spike | Strong ML pipeline reference; too large as core dependency. |
| `QuantConnect/Lean` | Study | Best event-driven architecture reference; heavy C#/platform dependency. |
| `polakowo/vectorbt` | Spike later | Matches fast-sweep goal; validate compatibility before dependency. |
| `nautechsystems/nautilus_trader` | Study / Phase 69 decision | Excellent production architecture; not needed before paper alert loop. |
| `kernc/backtesting.py` | Study, maybe toy examples | Clean API; AGPL and overlap with internal engine argue against core dependency. |
| `OpenBB-finance/OpenBB` | Optional adapter candidate | Useful data integration layer; keep outside canonical lake until provenance gates exist. |
| `PyPortfolio/PyPortfolioOpt` | Candidate dependency | Simple allocator prototyping; MIT and focused. |
| `dcajasn/Riskfolio-Lib` | Candidate spike | Strong risk toolbox; heavy CVXPY stack means isolate behind adapter. |
| `cvxgrp/cvxportfolio` | Study / defer | Good causal portfolio backtesting model; GPL and scope make it non-core. |
| `AI4Finance-Foundation/FinRL` | Defer | Educational RL; not needed before Phase 73. |
| `AI4Finance-Foundation/FinRL-Trading` | Study / defer | Modern weight-centric architecture is relevant; DRL/live scope is late-roadmap. |
| `TradeMaster-NTU/TradeMaster` | Defer | RL research platform; too far from current equity alert objective. |
| `mementum/backtrader` | Study only | Classic examples; do not add another engine. |
| `pmorissette/bt` | Study / optional | Strategy-tree idea is useful; dependency optional. |
| `cuemacro/finmarketpy` | Defer | Good market templates; low priority versus existing stack. |
| `stefan-jansen/zipline-reloaded` | Study only | Useful for Zipline mental model; not a dependency. |
| `quantopian/zipline` | Reject | Legacy historical reference; prefer zipline-reloaded if needed. |
| `vnpy/vnpy` | Defer | Useful for China-market gateway architecture; not current scope. |
| `ranaroussi/yfinance` | Keep current | Already in repo; prototype/live bridge only, not final truth source. |
| `pydata/pandas-datareader` | Keep current | Already in requirements; useful but not sufficient provenance. |
| `akfamily/akshare` | Defer | Add only if China data becomes explicit scope. |
| `waditu/tushare` | Defer | Same as AKShare; China data only. |
| `bmoscon/cryptofeed` | Reject current scope | Crypto feed not in current one-man equity alert scope. |
| `ccxt/ccxt` | Reject current scope | Crypto exchange connector; not current scope. |
| `man-group/ArcticDB` | Defer | Interesting time-series store; current hard constraint is DuckDB + Parquet. |
| `man-group/arctic` | Reject | Older generation; ArcticDB is the relevant successor if reopened. |
| `pmorissette/ffn` | Study / maybe metrics | Useful utility ideas; avoid duplicate metrics until gap is proven. |
| `ranaroussi/quantstats` | Study / maybe reports | Useful tearsheets; keep optional. |
| `quantopian/pyfolio` | Reject dependency | Legacy reports; use as historical reference only. |
| `quantopian/alphalens` | Study | Good factor-analysis concepts; likely reimplement minimal IC/turnover gates. |
| `quantopian/empyrical` | Study / maybe metrics | Useful metric definitions; avoid dependency unless needed. |
| `lballabio/QuantLib` | Defer | Gold-standard derivatives library, but out of current equity-alert scope. |
| `domokane/FinancePy` | Defer | Derivatives/fixed income scope only. |
| `google/tf-quant-finance` | Defer | TensorFlow quant math; out of current laptop equity loop. |
| `goldmansachs/gs-quant` | Defer | Useful ideas, but institutional access/API assumptions reduce fit. |
| `enthought/pyql` | Defer | QuantLib wrapper; same derivatives-only gate. |
| `freqtrade/freqtrade` | Reject current scope | Full crypto bot; do not mix with equity research kernel. |
| `hummingbot/hummingbot` | Reject current scope | Market-making crypto bot; not current scope. |
| `jesse-ai/jesse` | Reject current scope | Crypto system; not current scope. |
| `freqtrade/freqtrade-strategies` | Reject current scope | Example crypto strategies are high contamination risk. |
| `hummingbot/awesome-hummingbot` | Reject current scope | Resource list only; no repo value now. |
| `ib-api-reloaded/ib_async` | Candidate later | Good IBKR candidate after `BrokerPort` exists. |
| `erdewit/ib_insync` | Reject | Archived; use `ib_async` if IBKR is reopened. |

## Reframed One-Man Quant Product

Target product:

`research candidate -> validation gates -> portfolio/risk gate -> paper alert -> human decision -> audit trail`

Example final alert:

```text
BUY MU @ 600
score 94 | risk ok | max size 3% | expires 2026-05-09 15:55 ET
reason: PEAD + momentum + liquidity pass
gate: OOS pass, WFO pass, DSR pass, paper-only
```

Non-goals until later:

- No auto-live trading by default.
- No unmanaged crypto connectors.
- No direct broker dependency before `BrokerPort`.
- No ML candidate promotion without official `engine.py` verification.
- No external engine replacing Terminal Zero's canonical V1 evidence path.

## Methodology Ladder For Terminal Zero

This is the modified ladder to implement inside the repo.

| Level | Gate | Terminal Zero artifact |
|---:|---|---|
| 0 | Data hygiene | provenance manifests, PIT checks, corporate action policy |
| 1 | Baseline backtest | official `core/engine.py` or V2 proxy with explicit non-promotion label |
| 2 | OOS split | `validation/oos.py` |
| 3 | Walk-forward | `validation/walk_forward.py` |
| 4 | Permutation / MCPT | `validation/permutation.py` |
| 5 | Block bootstrap | `validation/bootstrap.py` |
| 6 | Multiple testing | `validation/multiple_testing.py` |
| 7 | Regime stratification | `validation/regime_tests.py` |
| 8 | Purged CV / CPCV | `validation/purged_cv.py` |
| 9 | PSR / DSR | `validation/probabilistic_sharpe.py` |
| 10 | Reality Check / SPA | `validation/reality_check.py` |
| 11 | Paper trading | `paper_trading/alert_loop.py` and delivery audit log |

Gate principle: a strategy can be interesting after Level 1, research-worthy after Level 4, promotable only after Levels 7-10, and operationally usable only after Level 11.

## Top-Level Roadmap

### Pillar 1: Platform Hygiene

Goal: make the current repo easier to change without breaking truth surfaces.

TODO:

- Finish Phase 62 frontend shell consolidation.
- Finish Phase 63 execution boundary hardening.
- Finish Phase 64 provenance hardening.
- Finish Phase 65 MLOps skeleton.
- Keep `core/engine.py` and canonical evidence rules protected.

### Pillar 2: Methodology Laboratory

Goal: build the validation gates before scaling strategy search.

TODO:

- Add `validation/` package with OOS, walk-forward, bootstrap, permutation, multiple-testing, regime tests, CPCV, PSR/DSR, Reality Check.
- Add unified `ValidationReport` schema.
- Add a strategy verdict vocabulary: `screened_out`, `incubating`, `replicated`, `queued_for_v1`, `promoted`, `rejected`, `retired`.
- Add tests with synthetic return streams where expected pass/fail behavior is known.

### Pillar 3: V2 Discovery Pipeline

Goal: let the laptop generate many candidates without contaminating V1.

TODO:

- Implement Phase 66 candidate registry.
- Implement Phase 67 fast proxy simulator.
- Seed Phase 68 PEAD variant family.
- Kill weak candidates cheaply before official V1 tests.
- Export promotion packets only for top survivors.

### Pillar 4: Official V1 Promotion Gate

Goal: preserve institutional discipline.

TODO:

- Implement Phase 69 V1 intake handler.
- Validate promotion packet schema.
- Run official same-window / same-cost / same-engine tests.
- Record all accepts/rejects in decision log.
- Make Nautilus adapter a decision, not an assumption.

### Pillar 5: Portfolio And Risk Layer

Goal: turn strategy outputs into size-aware trade ideas.

TODO:

- Pick one simple optimizer first: internal inverse vol or PyPortfolioOpt.
- Compare Riskfolio-Lib and cvxportfolio in isolated notebooks only.
- Add constraints: max single-name, max sector, turnover, liquidity, VIX kill switch, drawdown throttle.
- Emit a `RiskDecision` before every alert.

### Pillar 6: Alert Delivery Loop

Goal: deliver human-readable paper-trading calls.

TODO:

- Add `notifiers/` abstraction.
- Add `OpenClawNotifier` using `openclaw message send` once a channel exists.
- Keep existing Discord webhook as optional legacy path.
- Persist every sent alert to DuckDB/JSONL with idempotency key.
- Add alert expiry, cancellation, and correction messages.

### Pillar 7: Paper Trading And Audit

Goal: prove the system behaves in live time with zero capital.

TODO:

- Add paper portfolio state.
- Log signal time, quote time, alert time, hypothetical fill, slippage, and next-day outcome.
- Track missed fills and stale signals.
- Require minimum paper-trading sample before live approval.

### Pillar 8: Broker Adapter Decision

Goal: avoid execution fantasy.

TODO:

- Complete `BrokerPort` before adding broker-specific clients.
- Evaluate `ib_async` only after `BrokerPort`.
- Keep Alpaca adapter contained in `execution/broker_api.py`.
- Do not add Lean/Nautilus as live dependencies unless a decision log entry approves an adapter spike.

### Pillar 9: Optional Advanced Research

Goal: keep shiny tools in their lane.

TODO:

- Defer FinRL/TradeMaster until Phase 73 DRL spike.
- Defer crypto systems unless the product scope explicitly changes.
- Defer QuantLib/FinancePy/tf-quant-finance until derivatives become a named strategy family.
- Use external repos to write design memos, not to expand requirements prematurely.

## Immediate Next 10 TODOs

1. Do not clone the whole external repo list into Terminal Zero.
2. Create a `docs/research/external_repo_watchlist.md` only if repeated tracking is needed.
3. Keep Phase 62 as the active roadmap item; do not let research disrupt platform hardening.
4. During Phase 65, choose the experiment tracking interface before choosing ML frameworks.
5. During Phase 66, make the candidate registry the center of the discovery process.
6. During Phase 67, benchmark internal proxy sim against vectorbt-style expectations, not necessarily vectorbt itself.
7. During Phase 69, add Reality Check / DSR / PBO gates to the promotion verdict.
8. Add OpenClaw notification only after at least one OpenClaw chat channel is configured.
9. Make every alert paper-only until paper trading has enough live-time evidence.
10. Use external engines as architecture teachers, not replacements for the Terminal Zero kernel.

## Source Links

- `stefan-jansen/machine-learning-for-trading`: https://github.com/stefan-jansen/machine-learning-for-trading
- `microsoft/qlib`: https://github.com/microsoft/qlib
- `QuantConnect/Lean`: https://github.com/QuantConnect/Lean
- `polakowo/vectorbt`: https://github.com/polakowo/vectorbt
- `nautechsystems/nautilus_trader`: https://github.com/nautechsystems/nautilus_trader
- `OpenBB-finance/OpenBB`: https://github.com/OpenBB-finance/OpenBB
- `PyPortfolio/PyPortfolioOpt`: https://github.com/PyPortfolio/PyPortfolioOpt
- `dcajasn/Riskfolio-Lib`: https://github.com/dcajasn/Riskfolio-Lib
- `cvxgrp/cvxportfolio`: https://github.com/cvxgrp/cvxportfolio
- `AI4Finance-Foundation/FinRL-Trading`: https://github.com/AI4Finance-Foundation/FinRL-Trading
- `lballabio/QuantLib`: https://github.com/lballabio/QuantLib
- Harvey, Liu, Zhu factor multiple-testing paper: https://www.nber.org/papers/w20592
- White Reality Check DOI reference: https://doi.org/10.1111/1468-0262.00152
- Bailey et al. PBO reference: https://doi.org/10.2139/SSRN.2326253
- Bailey and Lopez de Prado DSR paper: https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf

## Confidence

Confidence: 8/10.

The repo map is high-confidence for roadmap shaping. Lower-confidence items are dependency-level decisions because they require local compatibility checks, license review, and benchmark spikes before acceptance.
