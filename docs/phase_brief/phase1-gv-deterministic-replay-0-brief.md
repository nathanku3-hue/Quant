# GV-DETERMINISTIC-REPLAY-0 Brief

Date: 2026-07-30
Mode: `EXECUTION_PACKET`
Status: `OPEN; IMPLEMENTATION_AUTHORIZED_ON_IMMUTABLE_BASE`
Authority: Slice 0 accepted; relocatable custody supersede A/B/C PASS

## Immutable bases

| Role | Exact SHA | Note |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | immutable; do not rewrite |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | Path-1 supersede; remote-equal on `codex/repository-custody-repair` |

Ancestry: `85e6601` → `bd07f61` (relocatable G4/MSFT) → `03a5c92` (restore V2-B0 MU non-binding + explicit G8 MU retirement).

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 active phase: **`GV-DETERMINISTIC-REPLAY-0` only**.
- L2 closed / immutable: `GV-MICRO-PORTFOLIO-VERTICAL-0` product terminal at `85e6601`.
- L2 deferred: Bounded Portfolio, Portfolio Scale, Universe Scale, Challenger Promotion, Limited Live Capital.
- L3 stage flow: Replay skeleton from Slice 0 events → exact reconstruction fixtures → independent audit → certification.

## Recommended next action

In a clean isolated worktree descended from exact Replay 0 base `03a5c92`, implement **only** deterministic replay certification for actual Slice 0 portfolio events. Do not open bounded-portfolio scale, provider, optimizer, or live-capital work.

## Product target

```text
frozen Slice 0 event log + manifests
→ reconstruct exact book, cash, quantities, costs, NAV
→ reconstruct thesis / decision state
→ preserve byte-stable prior certifications under corrections
→ exercise corporate-action correction, partial fill, idempotence
→ valuation-pending without fabricated prices
→ zero unexplained residual at declared precision
```

## Acceptance

- exact cash, quantities, costs, NAV, and thesis state versus Slice 0 operated books;
- prior certifications remain byte-stable under append-only corrections;
- idempotent replay of the same event prefix;
- correction lineage without rewrite of prior certs;
- partial-fill residual state;
- valuation-pending without inventing prices;
- one split or equivalent value transfer already exercised by Slice 0;
- zero unexplained residual at declared precision;
- no optimizer, provider programme, alpha claim, broker, or live capital.

## Custody gates already banked (do not reopen)

- Relocatable G4 path + `repo_root` resolve (`docs/architecture/gv_relocatable_custody_gate.md`).
- MSFT G8.2 hash hygiene retained.
- MU live package keeps historical non-binding `368c4fb3…` for V2-B0; G8 same-path hash-match PASS is **retired** from the custody gate with replacement truth test.
- Independent A/B/C PASS on `03a5c92`; candidate-only failures versus `85e6601` = 0.

## Operational gates

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Terminal remote Slice 0            1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

## Forbidden scope

providers · WRDS acquisition · broad historical loaders · optimizer · copula/MES production · automated graph propagation · adaptive intraday execution · tactical capital · broad tax · multi-currency · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · reopening Slice 0 product feature work · “fixing” MU declared hash to green old G8

## Stop rules

1. Stop if implementation is not descended from exact `03a5c92` (or a later audited Replay-only descendant that preserves the custody pins).
2. Stop if Slice 0 base `85e6601` is rewritten or force-moved.
3. Stop if MU historical non-binding is broken without a full V2-B0 product redesign packet.
4. Stop if work expands into bounded-portfolio scale before exact replay PASS.
