# Codex / Chrome Research SOP for GodView

Status: Phase 65 G7.1B research SOP
Date: 2026-05-09
Authority: research capture and documentation only

## Purpose

Codex and Chrome-assisted workflows can help collect source notes for GodView provider planning and thesis research. They cannot create alpha evidence, approve signals, write canonical market data, place trades, emit alerts, or bypass source policy.

This SOP is stricter than a general browsing workflow because GodView will eventually touch market-behavior claims that can be mistaken for trading signals.

## Tool Roles

### Codex Local Agent / CLI

OpenAI describes Codex as a coding agent that can pair with local tools and navigate a repo to edit files, run commands, and execute tests. Source: `https://help.openai.com/en/articles/11369540-codex-in-chatgpt-faq`

Allowed role:

- read and edit approved repo docs;
- inspect local source code and architecture;
- run validation commands in the selected workspace;
- organize source notes;
- prepare source matrices, policies, and handovers.

Forbidden role:

- create provider code in G7.1B;
- write canonical market data;
- mutate Candidate Registry state;
- generate candidate cards;
- run search, backtest, replay, proxy, alerts, broker calls, or dashboard behavior.

### Codex Chrome Extension

The Chrome Web Store listing for Codex says it lets Codex control Chrome for work in websites/apps where the operator is already signed in, with site access and sensitive-action prompts. Source: `https://chromewebstore.google.com/detail/codex/hehggadaopoacecdllhhajmbjkdcmajg`

Allowed role:

- use the operator's approved Chrome context for browser tasks that need signed-in state, vendor portals, or site approvals;
- inspect official/vendor documentation;
- capture source metadata for docs and future source policy;
- review dashboard screenshots when explicitly requested.

Forbidden role:

- scrape without source policy;
- exfiltrate or store credentials;
- click trading or broker actions;
- treat web findings as canonical market data;
- approve a signal or family.

### Codex In-App Browser

Allowed role:

- inspect public pages and local app previews;
- gather publicly available documentation sources.

Boundary:

- do not assume in-app browser state is the user's signed-in Chrome state;
- use Chrome extension workflow only when the user explicitly approves stateful browser work.

## Research Capture Template

Every research note should include:

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
manifest_or_note_uri
```

## Source Authority Rules

Preferred order:

1. official regulator/exchange/plan source;
2. licensed vendor documentation;
3. issuer/provider documentation;
4. high-quality secondary explanation;
5. general web notes, which remain non-canonical and research-only.

Examples:

- OPRA/OLPP for consolidated listed-options last-sale and quote authority;
- FINRA for short-interest reporting and short-interest caveats;
- CFTC for COT/TFF reporting cadence and positioning definitions;
- SEC for filings and ownership data;
- vendor documentation for licensed feed semantics and redistribution rules.

## Allowed Uses

Codex/Chrome research may support:

- architecture docs;
- source matrix;
- source-quality planning;
- provider-roadmap planning;
- thesis memo drafts;
- contradiction logs;
- human-review packets.

## Forbidden Uses

Codex/Chrome research may not support:

- alpha evidence by itself;
- signal approval;
- source-quality bypass;
- candidate generation;
- ranking;
- backtest/replay/proxy proof;
- alert emission;
- broker action;
- canonical market-data writes;
- credential handling;
- scraping outside an approved policy.

## G7.1B Boundary

This SOP creates no browser automation, no scraper, no provider adapter, no ingestion path, no dashboard runtime feature, no alert, and no trading behavior.
