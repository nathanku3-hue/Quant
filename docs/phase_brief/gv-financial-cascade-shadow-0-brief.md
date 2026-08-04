# Phase Brief — GV-FINANCIAL-CASCADE-SHADOW-0

Date: 2026-08-04
Status: `IMPLEMENTED LOCALLY; SHADOW RESEARCH ONLY; TERMINAL REVIEW UNAVAILABLE`
Accepted product score: `62/100 — unchanged`
Limited Live: `CLOSED; NOT AUTHORIZED`
Active product gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1 — unchanged`

## Decision

Do not defer the adapter and simulation harness. Defer only capital authority.

Leningrad's financial-clearing output is useful to Quant as a counterparty-payment cascade challenger at the macro/regime and portfolio-exposure layers. It is not an alpha generator, stock selector, entry signal, exit signal, bailout trade, or current critical-path module.

## Module-by-module boundary

| Quant module | Usefulness | Implemented use | Explicit exclusion |
|---|---|---|---|
| Macro/regime | High | Discrete `CLEAR/WATCH/SEVERE` evidence state derived from shock defaults, unpaid obligations, and non-unique clearing states | No continuous pseudo-precision macro score and no replacement of `RegimeManager` |
| Stock selection | None with current model/data | No change | Institution IDs and `inject-A`/`inject-B` are not mapped to securities, banks, rankings, or long/short views |
| Entry | None | No change | No entry gate, price, technical trigger, or timing rule consumes cascade output |
| Exit/stops | None | No change | No per-name stop, forced sale, or rank exit consumes cascade output |
| Portfolio exposure | High | PIT-aligned proportional gross-exposure cap in a shadow copy of existing target weights | No mutation of baseline weights, certified books, or live capital |
| Research validation | High | Baseline and challenger use the same `core.engine.run_simulation` path, dates, returns, and cost rate | No promotion from synthetic fixtures or one stress window |

## Leningrad ingestion contract

Quant consumes only the independently verified four-file finance bundle:

```text
scenario.json
comparison.json
report.md
bundle_index.json
```

The adapter requires the exact bundle identity from a Leningrad verifier/custody receipt and validates:

- exact four-file tree and regular-file status;
- strict JSON with duplicate-key rejection;
- raw payload SHA-256 values;
- reconstructed bundle and scenario identities;
- supported v2 choice schemas;
- scenario/comparison identity consistency;
- institution and candidate coverage;
- least/greatest accounting-invariant PASS;
- valid decision, ranking-stability, and non-uniqueness fields.

Quant does not import or copy Leningrad's clearing solver. CRLF and LF are accepted as semantically canonical JSON line endings, while exact raw hashes and the external bundle identity still bind custody.

## PIT law

A daily observation becomes effective no earlier than the calendar day after `available_at_utc`. Same-day use fails closed. The daily overlay uses backward as-of projection only after the effective date; it never backfills evidence into earlier dates.

## Exposure formula

For date `t`:

```text
G_t = Σ_i |w_i,t|
cap_t = configured WATCH/SEVERE gross cap, otherwise unavailable
scale_t = min(1, cap_t / G_t) when cap_t is available and G_t > 0; otherwise 1
w'_i,t = scale_t × w_i,t
```

This preserves security membership, signs, relative cross-sectional proportions, and existing entry/exit support. It only moves the residual toward cash in the shadow simulation.

Default research policy:

```text
SEVERE if:
  non_unique_states is non-empty
  OR shock_default_fraction >= 1/3
  OR shock_unpaid_fraction >= 1/10

WATCH if:
  shock_default_count > 0
  OR shock_unpaid_obligations > 0

WATCH gross cap = 0.75
SEVERE gross cap = 0.50
CLEAR/UNAVAILABLE = no cascade cap
```

These are explicit challenger parameters, not calibrated truths.

## Promotion / kill contract

Promotion requires all of the following in one same-engine comparison:

- at least two non-overlapping stress windows;
- at least two distinct verified bundle identities;
- PIT lineage for every observation;
- at least 15% relative max-drawdown improvement in every window;
- at least 10% expected-shortfall improvement in every window;
- annualized mean net-return drag no greater than 1 percentage point;
- relative turnover increase no greater than 20%;
- exact replay.

Disposition:

```text
insufficient independent PIT evidence -> DEFER_INSUFFICIENT_EVIDENCE
all gates pass -> PROMOTE_TO_LATER_PORTFOLIO_PREVIEW_CHALLENGER
adequate evidence but any performance/cost/replay gate fails -> KILL_CHALLENGER
```

Promotion means eligibility for a later portfolio-preview challenger only. It does not grant current proposal, selection, authorization, book, broker, or live-capital authority.

## Files

```text
A  strategies/financial_cascade.py
A  research/financial_cascade_shadow.py
A  scripts/run_financial_cascade_shadow.py
A  tests/test_financial_cascade_shadow.py
M  docs/prd.md
M  PRD.md
M  PRODUCT_SPEC.md
M  docs/notes.md
M  docs/lessonss.md
M  docs/decision log.md
```

## Validation

- New cascade tests: `6 passed`.
- Pinned Quant regression: `78 passed` across engine, RegimeManager, AlphaEngine, stop-loss, research runner, and cascade tests.
- Real interoperability: a bundle generated and independently verified by Leningrad's v0.4 finance code loaded successfully in Quant; observed sample identity `88b9ff3e3634c2a533e84476198c0eacb3b1aaa2b46cfcd88ac8e84c9b14b0b9`, state `SEVERE`, defaults `3`, unpaid fraction `217/440`.
- The CLI writes one atomic JSON report with input hashes, report identity, and execution identity.

## Current blocker

No real Quant promotion result exists. Quant still lacks a governed PIT bilateral-exposure history with at least two independent stress windows and a financial/credit-sensitive paper portfolio evaluated under this layer. Synthetic tests prove mechanics only.

Independent Reviewer A/B/C capacity is unavailable in the current tool surface, so this local implementation is not a terminally reviewed or publishable milestone. No commit, push, dashboard wiring, portfolio authority, or score uplift is claimed.
