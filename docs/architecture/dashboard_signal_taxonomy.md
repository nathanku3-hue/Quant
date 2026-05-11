# Dashboard Signal Taxonomy

Status: Phase 65 G7.1 product taxonomy
Authority: D-365 Phase G7.1 roadmap realignment / product charter
Date: 2026-05-09

## Purpose

The future dashboard is a decision cockpit for discretionary augmentation. It should show state, evidence, freshness, and uncertainty. It must not present automatic buy/sell orders, strategy rankings, broker instructions, or promotion verdicts.

## Five Panels

### 1. Thesis Health

Question: is the supercycle thesis strengthening or weakening?

Allowed future evidence categories:

- fundamental thesis milestones;
- revenue or adoption inflection evidence;
- margin, capacity, or supply-chain evidence;
- governance/source-quality badges;
- contradiction log.

Decision-support state examples:

- `thesis_strengthening`
- `thesis_uncertain`
- `thesis_weakening`
- `evidence_stale`

### 2. Entry Discipline

Question: is this still left-side / falling-knife risk, or is confirmation improving?

Allowed future evidence categories:

- trend stabilization;
- volatility contraction or expansion;
- failed-breakdown / reclaim behavior;
- liquidity and spread sanity;
- regime compatibility.

Decision-support state examples:

- `left_side_risk_high`
- `confirmation_improving`
- `entry_range_watch`
- `entry_blocked_by_freshness`

### 3. Hold Discipline

Question: is momentum still healthy enough to avoid selling too early?

Allowed future evidence categories:

- trend continuation;
- relative strength persistence;
- drawdown versus expected volatility;
- thesis-health alignment;
- deterioration and invalidation markers.

Decision-support state examples:

- `hold_thesis_intact`
- `momentum_constructive`
- `trim_review_needed`
- `invalidated_or_stale`

### 4. Flow and Positioning

Question: are flow and positioning conditions supportive, crowded, stale, or squeeze-prone?

Allowed future evidence categories:

- short-interest context;
- options or volume behavior;
- futures positioning context;
- trend-following pressure proxies;
- liquidity and borrow-quality warnings.

Important boundary:

- short-squeeze and CTA-type signals are dashboard context, not automatic triggers.
- FINRA short interest is lagged because firms report twice monthly, around mid-month and month-end.
- CFTC Traders in Financial Futures data can inform broad positioning context, but CFTC notes that trader classifications do not encode the specific reason for each position.
- CFTC Leveraged Funds includes hedge funds and money managers such as registered CTAs/CPOs and unregistered funds identified by CFTC; this supports regime/flow context, not precise single-stock triggers.

Decision-support state examples:

- `positioning_supportive`
- `positioning_crowded`
- `squeeze_context_present`
- `positioning_lagged_or_stale`

### 5. Regime

Question: is the market rewarding this type of setup now?

Allowed future evidence categories:

- market trend and breadth;
- liquidity regime;
- volatility regime;
- sector leadership;
- factor/risk appetite context.

Decision-support state examples:

- `regime_supportive`
- `regime_neutral`
- `regime_hostile`
- `regime_data_stale`

## Source-Quality Policy

- Tier 0 canonical sources are required for promotion evidence.
- Tier 2, yfinance, OpenBB, public web, and operational Alpaca sources may not become promotion evidence.
- Operational/paper data can support monitoring only when labeled by source quality and freshness.
- Lagged sources must show their reporting frequency and latest available timestamp.

## Forbidden Dashboard Behavior

- No automatic buy/sell signal.
- No candidate ranking.
- No best-parameter selection.
- No Sharpe, CAGR, alpha, drawdown, score, or rank in G7.1.
- No alert emission.
- No broker, Alpaca, OpenClaw, or notifier action.
- No promotion packet or human-reviewed approval claim.

## External Reference Anchors

- FINRA short interest reporting schedule: https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest
- FINRA short interest explainer: https://www.finra.org/investors/insights/short-interest
- CFTC Commitments of Traders: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- CFTC Traders in Financial Futures explanatory notes: https://www.cftc.gov/sites/default/files/idc/groups/public/%40commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf
