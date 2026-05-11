# GodView Dashboard Wireframe

Status: Phase 65 G7.4 product-state spec only
Date: 2026-05-09
Authority: dashboard wireframe/spec only

## Purpose

Define the first GodView dashboard product spec around opportunity states, not scores.

No dashboard runtime code is added. This file does not authorize Streamlit edits, callbacks, candidate generation, search, scoring, rankings, alerts, broker calls, provider calls, ingestion, or buy/sell orders.

## DASH-0 Information Architecture Update

Phase 65 DASH-0 approves the future page order:

```text
Command Center
Opportunities
Thesis Card
Market Behavior
Entry & Hold Discipline
Portfolio & Allocation
Research Lab
Settings & Ops
```

This update is planning-only. It does not modify `dashboard.py`, `views/`, Streamlit navigation, providers, alerts, broker behavior, candidate cards, discovery intake output, factor-scout code, or backtests.

## Design Principle

The dashboard answers:

```text
What state is this opportunity in, why, what changed, and what is blocked?
```

It does not answer:

```text
What should the system buy, sell, rank, alert, or execute?
```

## Section 1: Commander View

Purpose:

- show total watchlist state distribution;
- show stale/unknown source counts;
- show state changes since prior review;
- show blocked actions and unresolved provider gaps.

Must display:

- current opportunity-state counts;
- source-quality/freshness health;
- open risks;
- next monitoring focus.

Must not display:

- scores;
- rankings;
- buy or sell orders;
- alerts;
- broker status.

## Section 2: Watchlist Opportunity States

Purpose:

- show one card per tracked ticker/theme;
- make current state and prior state visible;
- explain state-change reason codes and source classes.

This is a watchlist view, not a candidate generator.

## Section 3: Thesis Health

Purpose:

- show thesis state, thesis evidence freshness, contradiction log status, and ownership/context support.

Allowed content:

- thesis evidence;
- SEC filing/ownership context;
- research freshness;
- contradiction/invalidation notes.

Forbidden content:

- alpha score;
- candidate ranking;
- automatic thesis approval.

## Section 4: Entry Discipline

Purpose:

- show whether the opportunity is still left-side risk, accumulation watch, confirmation watch, or buying range.

Boundary:

- `BUYING_RANGE` is a state label only.
- It is not a buy order, alert, or execution instruction.

## Section 5: Hold Discipline

Purpose:

- show whether thesis and behavior support holding, trimming review, or exit-risk review.

Boundary:

- `LET_WINNER_RUN`, `TRIM_OPTIONAL`, and `EXIT_RISK` are state labels only.
- They do not emit sell orders or alerts.

## Section 6: GodView Market Behavior

Purpose:

- summarize price/volume behavior, IV/vol behavior, options/whale context, short-squeeze base, CTA/systematic context, rotation, macro/factor context, and ownership context.

Every row must show:

- observed/estimated/inferred label;
- source class;
- freshness;
- provider/feed or provider gap;
- allowed and forbidden state influence.

## Section 7: Risk and Invalidation

Purpose:

- show risk invalidation evidence and thesis-broken override status.

Boundary:

- `THESIS_BROKEN` overrides market-behavior strength.
- Risk states are review states, not orders.

## Section 8: What Changed Today

Purpose:

- show state changes, evidence additions, freshness changes, and newly blocked/unblocked evidence paths.

Boundary:

- no alert emission;
- no push notification;
- no watchlist mutation outside future approved runtime.

## Section 9: Why Not Buy Yet

Purpose:

- show blockers such as left-side risk, stale evidence, insufficient observed support, provider gaps, crowded/frothy risk, or missing thesis evidence.

No buy or sell orders.

## Section 10: Why Not Sell Yet

Purpose:

- show reasons a winner remains intact, such as thesis not broken, market behavior constructive, deterioration evidence absent, or trim optional but not required.

No buy or sell orders.

## Product-State Footer

Every dashboard view must keep these footer facts visible in future runtime work:

```text
state_label_only = true
orders_enabled = false
alerts_enabled = false
scores_enabled = false
rankings_enabled = false
providers_enabled = false
```

## G7.4 Boundary

G7.4 creates product specs only:

- no dashboard runtime code;
- no Streamlit edits;
- no provider/source registry implementation;
- no candidate card;
- no search;
- no score;
- no ranking;
- no alerts;
- no broker call.
