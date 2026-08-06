# GodView Top-Level Roadmap

Status: `PAIR-DECISION-SERIES-1 EPISODE 1 IMPLEMENTED; AUDIT/PUBLICATION PENDING; LIVE CLOSED`
Date: 2026-08-06
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Active brief: `docs/context/ACTIVE_BRIEF`
Canonical product maturity: `70/100` (operability, custody, replay only)
Portfolio-alpha evidence: `0`

## Endgame

GodView is one all-capital point-in-time certified portfolio operating system:

```text
certified book + banked evidence + source-derived market identity
→ verified immutable security decisions
→ governed real-security/cash comparison
→ bounded operator disposition
→ calculation-only preview
→ explicit confirm or reject-all
→ deterministic accounting
→ atomic persistence
→ certification lineage
→ exact replay
→ sequential prospective outcome evidence
```

`dashboard.py` is the sole operator product. Domain modules own evidence verification, packet derivation, accounting, persistence, certification, and replay. The dashboard owns no independent market or capital math.

## Banked substrate

- Published authority cut: `9af5259`, tagged `pit-alpha-authority-cut-1-terminal`.
- Source-packet candidate base: `7191613`, clean and remote-equal.
- Existing loop: preview, explicit disposition, persistence, certification, exact reopen, residual `0`.
- Existing scale substrate remains reusable but is not the next gate.

The operator-entered source-authority overclaim at `7191613` is repaired inside the first real pair episode. It is not a separate product milestone.

## Active result — PAIR-DECISION-SERIES-1 Episode 1

```text
one pinned Cboe BZX MU/NVDA source capture
+ one bounded permission manifest
+ one XML-row parser
+ one common PIT cut
→ MU row / packet
→ NVDA row / packet
→ banked MU subject decision
→ banked-only NVDA subject decision
→ MU / NVDA / cash comparison
→ sealed episode 1 cash/abstention
→ preview / confirm or reject-all
→ persist / certify / exact reopen
```

Each packet has a separate permanent identity, instrument ID, row locator, row hash, and packet hash. Both share the exact source object, permission manifest, parser, valid time, knowledge time, and decision cut.

Manual price, source, permission, receipt, parser, and market-time authority is deleted without compatibility. Synthetic `MERID` is excluded from acceptance.

## Episode-1 forward evidence contract

Before outcomes are visible, episode 1 seals:

```text
decision_series_id
+ episode_number = 1
+ decision_cut_id
+ outcome_horizon_spec
+ outcome_open_not_before
+ comparator_spec
+ cost_model_id
+ decision_policy_version
+ source_contract_version
```

Those terms are bound into proposal, event ledger, certification, persistence, and reconstruction. Outcome data remains unopened.

Both securities remain `ABSTAIN / NO_POSITION`; the accepted capital disposition is certified cash. This is valid negative/neutral evidence, not a failed demonstration and not alpha.

## Evidence state

| Measure | Current |
|---|---:|
| Source-derived packet path | PASS locally |
| Real investable identities | 2 |
| Real cross-sectional episodes | 1 on confirmation |
| Sealed sequential episodes | 1 on confirmation |
| Opened outcome episodes | 0 |
| Unexplained residual | 0 |
| Fresh-process equality | PASS locally |
| Canonical product maturity | 70/100 |
| Portfolio-alpha evidence | 0 |

Focused integrated matrix: `71/71 PASS`; inherited non-blocking `websockets.legacy` warning only.

## Publication gate

One candidate, one audit, one publication:

```text
immutable candidate SHA
→ review-only PR and hosted exact-head proof
→ one independent cross-domain audit
→ audit PASS
→ owner-authorized fast-forward-only main update
→ annotated pair-decision-series-1-e1-terminal tag
→ local main == origin/main == peeled tag
```

Publication fails closed without authority to perform or authorize the exact fast-forward and protected-branch bypass. No squash, rebase, merge commit, force push, or tag rewrite.

## Next — temporal evidence, not breadth

After episode 1 is terminally published:

```text
episode 2
→ episode 3+
→ open each preregistered outcome only when eligible
→ apply fixed costs and comparators
→ retain wins, losses, neutral results, abstentions, and rejects
→ evaluate repeated out-of-sample decision evidence
```

Do not expand to 5 or 25 real securities until the sequential series demonstrates that security breadth—not time-series evidence—is the limiting constraint.

## Claim and scope boundary

No new portfolio engine, provider framework, optimizer, broker, advice, live capital, compatibility route, score uplift, alpha claim, premature outcome opening, or Limited Live. Canonical product maturity remains `70/100`; portfolio-alpha evidence remains `0`.
