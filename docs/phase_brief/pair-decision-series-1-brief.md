# PAIR-DECISION-SERIES-1 — Episode 1 Brief

Date: 2026-08-06
Branch: `codex/pit-source-authority-1`
Base: `7191613f6e3bb00ac2f19eb1201f8723d9d695fe`
Status: `IMPLEMENTED LOCALLY; AUDIT AND PUBLICATION PENDING; LIVE CLOSED`
Canonical product maturity: `70/100` (operability, custody, and replay only)
Portfolio-alpha evidence: `0`
Limited Live: `CLOSED; NOT AUTHORIZED`

## Product result

One integrated source-authority and real-pair slice:

```text
one pinned Cboe BZX MU/NVDA source capture
+ one permission manifest
+ one XML-row parser
+ one common PIT cut
→ source-derived MU packet
→ source-derived NVDA packet
→ banked MU subject package
→ banked-only NVDA subject package
→ real MU / real NVDA / cash comparison
→ sealed PAIR-DECISION-SERIES-1 episode 1
→ calculation-only preview
→ explicit cash/abstention confirmation or reject-all
→ atomic persistence
→ certification lineage
→ exact fresh-process reopen
```

Both subject packages remain `ABSTAIN / NO_POSITION`. The valid episode-1 confirmation retains certified cash, creates no orders or fills, charges no cost, and preserves unexplained residual `0`. No positive capital claim is manufactured.

## Source contract

- Source capture: `data/gv_pair_decision_series/mu_nvda_episode_1/common_market_source_capture.json`.
- Permission: `data/gv_pair_decision_series/mu_nvda_episode_1/permission_manifest.json`.
- Parser: `GV_CBOE_BZX_SYMBOL_XML_ROW` version `1.0.0`.
- Common source timestamp: `2026-08-06T08:55:50.000000Z`.
- Retrieval/knowledge time: `2026-08-06T09:04:14.959920Z`.
- Decision timestamp: `2026-08-06T09:05:00.000000Z`.
- Each packet retains its own permanent identity, local instrument ID, row locator, row SHA-256, and packet SHA-256.
- The Command Center cannot author price, source, permission, parser, row, receipt, or market timestamps.

## Episode preregistration

Episode 1 seals before outcome access:

- `decision_series_id = PAIR_DECISION_SERIES_1`;
- `episode_number = 1`;
- immutable `decision_cut_id`;
- 30-calendar-day common-source-cut outcome horizon;
- `outcome_open_not_before = 2026-09-05T09:04:14.959920Z`;
- certified-cash primary comparator plus retained A, B, and equal-pair comparators;
- fixed `$2` paper fee per order cost model;
- banked-evidence abstain/cash decision policy;
- source contract `CBOE_BZX_TWO_ROW_CAPTURE_V1`;
- `outcome_data_loaded = false` and `outcome_status = SEALED_NOT_OPENED`.

These terms travel inside the proposal, event ledger, certification identity, persistence envelope, and exact reconstruction.

## Acceptance

- [x] One common source object covers MU and NVDA.
- [x] One permission manifest and one parser derive both packets.
- [x] Raw/source, permission, parser, row, instrument, packet, and PIT drift fail closed.
- [x] Manual market-authority controls and request fields are removed without compatibility.
- [x] Synthetic `MERID` is absent from the acceptance path.
- [x] Two real permanent identities and cash are compared.
- [x] Episode 1 preregistration is sealed before outcomes.
- [x] Preview is mutation-free.
- [x] Confirmation and reject-all preserve cash, costs, residual, persistence, and certification.
- [x] Fresh-process reconstruction is byte-exact.
- [x] Focused integrated matrix passes `71/71` locally.
- [ ] One independent cross-domain audit passes against an immutable candidate SHA.
- [ ] Candidate branch is pushed and hosted exact-head checks pass.
- [ ] Owner-authorized fast-forward and protected-branch bypass are available.
- [ ] Local main, remote main, and peeled terminal tag equal the exact accepted SHA.

## Publication route

Publication remains fail-closed:

```text
candidate branch push
→ review-only PR and hosted exact-head proof
→ one independent cross-domain audit
→ audit PASS
→ owner clean checkout
→ git merge --ff-only exact candidate
→ push main
→ annotated pair-decision-series-1-e1-terminal tag
→ local main == origin/main == peeled tag
```

No merge commit, squash, rebase, force push, tag rewrite, or publication without owner authority to perform or authorize the exact fast-forward and any protected-branch bypass.

## Forbidden scope

No new portfolio engine, provider framework, compatibility path, synthetic acceptance security, optimizer, broker, advice, live capital, score uplift, outcome opening, alpha claim, or 5/25-security expansion.

## What Was Done

- Replaced operator-authored market authority with one pinned multi-security source capture, one permission manifest, one parser, and two source-derived packets.
- Added a banked-only NVDA subject decision beside the existing MU authority and removed synthetic companion acceptance.
- Implemented real MU / real NVDA / cash episode 1 with sealed horizon, comparator, cost, policy, and source terms.
- Removed all manual market price, source, permission, receipt, and market-time controls without compatibility.
- Proved mutation-free preview, cash/abstention confirmation, reject-all, atomic persistence, certification lineage, residual `0`, and exact fresh-process reconstruction.
- Passed the focused integrated matrix `71/71`; the only warning is the inherited `websockets.legacy` deprecation.

## What Is Locked

- Active product gate is `PAIR-DECISION-SERIES-1 — EPISODE 1`.
- Published main `9af5259` and `pit-alpha-authority-cut-1-terminal` remain immutable prior receipts.
- `dashboard.py` / Command Center remains the sole operator product.
- Episode 1 uses real MU, real NVDA, and cash only; no synthetic companion is accepted.
- Subject evidence is banked-only; the bounded acquisition covered one market observation object only.
- Outcomes remain sealed and unopened until the preregistered date and rule.
- Canonical product maturity remains `70/100`; portfolio-alpha evidence remains `0`.
- Limited Live remains closed.
- Publication requires audit PASS plus owner authority for exact fast-forward and protected-branch bypass.

## What Is Next

- Freeze one immutable candidate SHA and run the exact focused/hosted matrix plus one independent cross-domain audit.
- On audit PASS, push the candidate and execute the named owner fast-forward/tag publication route only if authority exists.
- After terminal equality is proved, immediately execute episode 2 under the unchanged pair, comparator, cost, policy, horizon, and source contracts.

## First Command

`E:\code\quant\tmp\gv25env\Scripts\python.exe -m pytest -q tests/test_gv_immutable_market_packet.py tests/test_gv_pit_transaction.py tests/test_gv_pit_operated_capital.py tests/test_gv_pit_operated_rotation.py tests/test_dash_1_page_registry_shell.py tests/gv_portfolio_v0/test_operated.py tests/gv_portfolio_v0/test_operated_25.py tests/gv_portfolio_v0/test_prospective.py tests/gv_portfolio_v0/test_real_evidence_mu.py tests/gv_portfolio_v0/test_same_evidence_shadow.py`

## Next Todos

- run the complete candidate matrix from a clean exact checkout;
- run one independent cross-domain audit;
- push candidate branch and collect hosted exact-head proof;
- publish only through owner-authorized fast-forward and tag equality;
- begin episode 2 without widening security breadth.
