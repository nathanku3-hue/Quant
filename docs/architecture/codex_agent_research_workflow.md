# Codex / Chrome Research Agent Workflow

Status: Phase 65 G7.1A research-agent SOP
Date: 2026-05-09
Authority: G7.1A starter docs / product-spec rewrite

## Purpose

Codex and browser-assisted workflows can help collect and organize research evidence for the Unified Opportunity Engine. They cannot approve alpha, bypass source policy, touch credentials, or trigger execution.

This SOP describes allowed and forbidden uses for Codex local agents, the Codex Chrome extension, and in-app browser previews.

## Tool Roles

### Codex CLI / Local Agent

Codex CLI is a local coding agent that can operate in a selected directory. It can read, change, and run code where the operator grants workspace access.

Allowed in this repo:

- inspect docs;
- update PRD/spec/roadmap;
- create research notes;
- organize source excerpts and evidence tables;
- run local validation commands;
- review dashboard screenshots;
- inspect vendor documentation copied or opened by the operator.

### Codex Chrome Extension

The Codex Chrome extension lets Codex use Chrome for browser tasks that need signed-in browser state, with site approvals and browser-permission management.

Use this for authenticated or stateful browser workflows, such as:

- broker/vendor documentation review behind login;
- SEC/FINRA/CFTC page inspection where the user needs Chrome state;
- dashboard screenshot review in a normal browser;
- manual web workflows that require the user's existing browser session.

### Codex In-App Browser

The in-app Codex browser is suitable for previews and public pages. It should not be treated as a signed-in browser environment. It does not provide the same existing-tab, cookie, extension, or authenticated-session behavior as the Chrome extension.

Use the Chrome extension rather than the in-app browser when authenticated research workflows require signed-in browser state.

## Allowed Uses

Codex/Chrome agents may:

- inspect docs;
- research source pages;
- capture evidence;
- extract source metadata;
- create research notes;
- update PRD, product spec, roadmap, and architecture docs;
- review dashboard pages and screenshots;
- inspect broker/vendor documentation;
- inspect SEC, FINRA, CFTC, OCC, OPRA, exchange, or vendor pages for source-policy planning.

## Forbidden Uses

Codex/Chrome agents may not:

- generate alpha evidence;
- approve a signal;
- bypass source-quality rules;
- touch credentials;
- place trades;
- emit alerts;
- scrape without source policy;
- write unvetted market data into canonical paths;
- mutate Candidate Registry state as a side effect of research;
- promote a family, candidate, or signal;
- create backtest/replay/proxy evidence unless a later phase explicitly approves that scope.

## Research Note Requirements

Research notes should capture:

```text
source_title
source_url_or_locator
access_date
provider_or_authority
source_quality_candidate
freshness_or_reporting_lag
observed_vs_estimated
allowed_use_candidate
forbidden_use_candidate
summary
open_questions
```

## Source Policy Guardrail

Research capture is not source approval.

A captured page or vendor document can inform a future policy decision, but the signal remains blocked until a later source policy defines provider, feed, freshness, confidence, allowed use, forbidden use, manifest handling, and validation path.

## G7.1A Boundary

This SOP adds no browser automation, no scraping job, no provider, no credential handling, no runtime dashboard behavior, no alerts, and no broker path.
