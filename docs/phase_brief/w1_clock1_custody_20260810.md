# W1 — Clock #1 Custody — Engineering Slice Closed — 2026-08-10

**Owner:** recurring/event-driven W1 Clock #1 custody lane
**Disposition:** `CLOSE_CURRENT_ENGINEERING_SLICE / KEEP_RECURRING_CUSTODY_LANE_OPEN`
**Custody state:** `WAITING_FOR_LEGITIMATE_FRESH_WEEKLY_SOURCE_RECEIPTS`
**Clock state:** `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`
**Financial alpha evidence:** `0`
**Outcome open not before:** `2026-09-09T20:00:00Z`

## Binding objective

Preserve Clock #1 exactly, keep the original frozen 109-company laboratory byte/identity-bound, require genuinely fresh required-source receipts before every later weekly v3 cut, and never open or consume prospective outcomes before authority matures.

## Exact Clock #1 custody reverified

| Artifact | SHA-256 |
|---|---|
| frozen candidate source `run_4.xlsx` | `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056` |
| primary-security master | `8aefbbd751a714b8689402ccbf8fa2b776c6388d4bbc3870ec4f8b975306eca4` |
| primary-security market history | `897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48` |
| decision cut | `81926aa896485a4a646228920ae0769283f143328ff8fe1f6671929136cd9b80` |
| seal candidate | `1b8c44db8b4129a69dbf8386b0eb1de397183807d27339186625071a60baca68` |
| fresh-process verification proof | `0192d4115c744ebfed980fb8942b96eecc41d848bb526f6eea1d57f63a326430` |
| Clock-Start Receipt | `562781089c728e57eed8fabb116262f44ac15b844571a986d32c28ed299665fc` |

Clock-Start Receipt ID remains `eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78`.

Runtime authority check on takeover returned:

```text
prospective_clock_started = true
evaluation_started = false
outcome_open_authorized = false
future_outcome_authority_available = false
```

No outcome-bearing artifact was opened during this takeover or closure pass.

## Frozen-109 hardening landed

`research/aov0/weekly_tape.py` now freezes the exact original 109 `SP_ENTITY_ID` values into the W1 contract and binds them to:

- semantic candidate-universe hash `f4f7ac7ed1ff21b95580bb623953e875bda0106ed478887b7d5ed6ccff456075`;
- source raw-object SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`.

A self-consistent but different 109-name set now fails closed with `aov0_weekly_frozen_candidate_universe_not_clock1`.

## Fresh-receipt state

Previous Clock #1 cut build time: `2026-08-08T19:48:38.199059Z`.

The complete current W1 receipt directory contains only the original pre-cut receipts:

| Required source | Retrieved at | Fresh after prior cut? |
|---|---|---|
| quarterly fundamentals | `2026-08-07T18:53:00.470779Z` | NO |
| primary-security master | `2026-08-08T16:23:22.073686Z` | NO |
| primary-security market data | `2026-08-08T19:39:21.924796Z` | NO |
| NY Fed SOFR | `2026-08-07T19:00:08.894288Z` | NO |

The real W1 preflight therefore correctly fails closed today; first observed blocker is `aov0_weekly_stale_required_source:ciq_market_data`. No stale source is silently reused as a weekly measurement.

## Validation

- `tests/aov0/test_weekly_tape.py`: `5/5 PASS`.
- full `tests/aov0`: `167/167 PASS`.
- `git diff --check` for the W1 code/test patch: PASS.
- immutable Clock #1 file hashes: exact match to handover authority.
- Clock-Start Receipt full-chain loader: PASS.

## W1 operating law from here

1. Do not mutate Clock #1 artifacts or Parent/Child.
2. Do not rerun the high-growth candidate screen.
3. Do not acquire fresh provider data while the 2026-08-10 methodology hold remains in force.
4. When a legitimate weekly custody event is authorized, require fresh receipts for all four required sources after the previous cut, against the exact frozen 109, before any new v3 decision cut.
5. A stale, missing, future-dated, wrong-source, wrong-count, or membership-drift input fails closed.
6. Do not open prospective outcomes before `2026-09-09T20:00:00Z`.
7. W1 does not retune, rescue, or borrow authority from W2–W10.
8. Do not add more W1 custody code unless a concrete custody defect is demonstrated.

## Handback / staffing model

W1 is no longer a continuously staffed engineering worker. The current engineering slice is frozen and handed back as a recurring/event-driven custody responsibility. Reactivate it only for a legitimate weekly custody event, a newly landed authorized receipt set, a concrete custody defect, or the later maturity/open-authority checkpoint.

## Current stop condition

`WAITING_FOR_LEGITIMATE_FRESH_WEEKLY_SOURCE_RECEIPTS` — this is a data-time/event boundary, not a code blocker. W1 custody is intact, fail-closed, and the current engineering slice is closed.
