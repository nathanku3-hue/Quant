# GV-MICRO-PORTFOLIO-VERTICAL-0 Brief

Date: 2026-07-29
Mode: `EXECUTION_PACKET`
Status: `IMPLEMENTED_PUSHED_CANDIDATE; REPLAY_SHADOW_COMPLETE; INDEPENDENT_AUDIT_PENDING`
Authority base: `1db250169cdfe57ffa5d5cc5e5d24b2e937d5d33`
Candidate branch: `codex/gv-micro-portfolio-v0`
Audit target commit: `f64cadcb2a9aaf0708744099ddc03ea2c41617eb`
Audit target tree: `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`
Namespace: `gv_portfolio_v0`

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 completed implementation streams: Truth core, Decision vertical, Product closure, Replay shadow.
- L2 active gate: independent Slice 0 Reviewer A/B/C audit.
- L2 deferred: terminal replay certification, Bounded Portfolio, Portfolio Scale, Universe Scale, Challenger Promotion, Limited Live Capital.
- L3 flow: R0 Audit PASS → Slice 0 Candidate → Independent Product Audit → External Replay Certification → Bounded Portfolio.

## Product result

```text
launch
→ review four securities, benchmark, and classified cash
→ inspect principal thesis, substitute, competitor, rejection, and abstention
→ confirm portfolio aim
→ generate one deterministic paper order and fill
→ certify book
→ persist
→ reopen
→ admit one later WATCH observation
→ explain why the aim remained unchanged
```

The complete broker-free operator loop is implemented and pushed. It remains a candidate until genuinely independent Reviewer A/B/C reports accept the exact audit target.

## Delivered vertical

- permanent instrument IDs and domain-separated content identities;
- content-addressed evidence references with exact-byte verification;
- one immutable canonical event stream with append-only prefix checks;
- four reviewed securities: principal, substitute, rejected competitor, and abstained alternative;
- benchmark plus classified `AVAILABLE` and `RESEARCH_RESERVE` cash;
- Living Thesis Lite with Bull/Base/Bear ranges;
- explicit `ADMIT`, `REJECT`, `ABSTAIN`, and `CASH` outcomes;
- deterministic capital competition selecting the substitute;
- one confirmed portfolio aim, one immutable decision snapshot, one paper order, and one fill;
- one exercised value-preserving 2:1 split;
- event-reduced multi-position book and NAV reconciliation;
- certification, atomic persistence, verified reopen, and corruption refusal;
- one later deterministic WATCH observation that changes evidence but not the aim because no hard falsifier fired;
- one broker-free Streamlit operator workspace.

## Replay result

`GV-DETERMINISTIC-REPLAY-0` is implemented as shadow evidence from the real Slice 0 event stream. It proves locally:

- exact cash, position, cost, NAV, aim, decision-snapshot, thesis-state, and product-certification reconstruction;
- byte-idempotent replay and duplicate-delivery deduplication;
- explicit correction lineage;
- partial-fill residual quantity and cash state;
- overfill rejection;
- `VALUATION_PENDING` without invented prices or NAV;
- value-preserving split residual of zero;
- byte-stable prior product certifications.

Terminal replay certification remains external. The local CLI can verify GitHub repository, candidate commit/tree, reviewer account identity, and exact remote report bytes, but it cannot mint a terminal certificate from caller-built data. Provider preflight remains non-authorizing and `--require-certification` returns blocked.

## Exact fixture economics

```text
Opening available cash        975
Opening research reserve       25
Opening Northstar value       500
Opening NAV                  1500
2:1 split residual              0
Harbor fill                 5 × 40
Explicit fee                    1
Terminal available cash       774
Terminal research reserve      25
Terminal position value       700
Terminal NAV                 1499
```

Formulae:

- `fill_cash_cost = quantity × price + fee = 5 × 40 + 1 = 201`;
- `terminal_available_cash = 975 - 201 = 774`;
- `terminal_NAV = 700 + 774 + 25 = 1499`;
- `split_value_residual = (20 × 25) - (10 × 50) = 0`;
- `capital_score_bps = expected_value_bps - risk_penalty_bps - cost_penalty_bps`.

## Minimum seams frozen and exercised

`InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, and `CertificationId`.

The custody backend under `contracts/gv_portfolio/v0` and `core/gv_portfolio_v0` is the single low-level identity/event authority. `gv_portfolio_v0.vertical` remains the product-orchestration facade. Released `gv_fs0_v1` remains unchanged.

## Validation state

Pinned environment:

- Python `3.12.10`;
- pytest `9.0.2`;
- Streamlit `1.54.0`;
- jsonschema `4.26.0`.

Evidence:

- portfolio, custody, operator, and replay tests: `38/38 PASS`;
- exact pinned focused matrix: `282/282 PASS` = `38` portfolio/replay + `150` protocol + `25` context + `24` current-authority + `45` Alpha release/core;
- context generation and fail-closed validation: PASS;
- network-denied Streamlit AppTest: PASS;
- deterministic bytes across independent workspace roots: PASS;
- compile, JSON, runtime smoke, and diff hygiene: PASS;
- local/origin equality at audit target: PASS;
- root checkout untouched at `accef5c6` with 5,600 status entries.

Independent Reviewer A/B/C ownership is not available through the current connector. Terminal Slice 0 acceptance and replay certification therefore remain blocked.

## Score update

Canonical shipped score remains `39/100`. No score uplift is earned before independent audit.

| Dimension | Current canonical | Pushed candidate | After audited replay forecast |
|---|---:|---:|---:|
| Product capability | 28 | 63–65 | 65–70 |
| User flow | 42 | 73–75 | 74–78 |
| Portfolio completeness | 18 | 67–70 | 70–75 |
| Integrity and replay | 64 | 82–86 shadow | 90–95 |
| Prospective evidence | 10 | 20–25 fixture-only | 30–40 |
| Shipping and custody | 78 | 88–91 | 90–95 |
| Weighted audit maturity | ≈39 | 65–68 candidate | 70–74 |

Operational evidence:

```text
Roadmap custody banked                         1/1
Micro-portfolio implementation pushed          1/1
Replay shadow exact                            1/1
Independent Slice 0 product audit              0/1
Terminal replay certification                  0/1
Real prospective external observation          0/1
Bounded repeated portfolio                     0/1
```

The later WATCH step is a deterministic acceptance fixture, not a real externally observed prospective result.

## P0/P1 controls

| Risk | Severity | Current control |
|---|---|---|
| stale implementation ancestry | P0 | exact audited base verified |
| root checkout contamination | P0 | root untouched; isolated worktree only |
| invented valuation | P0 | `VALUATION_PENDING`, never fabricated NAV |
| split accounting drift | P0 | exact value-preservation check and test |
| persisted corruption | P0 | envelope hash plus full identity/book/certification rebuild |
| original decision rewrite | P1 | canonical snapshot bytes asserted unchanged |
| duplicate identity/event authority | P1 | one custody backend; vertical delegates exercised primitives |
| released FS0 mutation | P1 | new namespace; integrity guards preserve substrate boundary |
| fixture mistaken for prospective evidence | P1 | explicit claim boundary and score freeze |
| caller-mintable terminal certification | P1 | local promotion path removed; provider checks are preflight-only |

## Forbidden scope

providers/WRDS data acquisition · broad historical loaders · optimizer · copula/MES production · automated graph propagation · adaptive intraday execution · tactical capital · broad tax · FX · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim

## Stop rules

1. Stop if independent audit finds any P0/P1 identity, accounting, mandate, persistence, replay, or custody defect.
2. Stop terminal replay certification until an external authority accepts exact independent reports.
3. Stop before bounded portfolio work until replay certification passes.

## Next action

Independently audit commit `f64cadcb2a9aaf0708744099ddc03ea2c41617eb` and tree `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`. Publish exact Reviewer A/B/C reports and use the GitHub verifier as preflight evidence. Terminal certification remains external; bounded portfolio remains closed.

## What Was Done

- Banked the independent R0 receipt and nine-seam contract before implementation.
- Implemented and pushed the complete micro-portfolio operator loop.
- Integrated one custody backend for identity, evidence, and immutable events.
- Implemented exact shadow replay, corrections, partial fills, valuation-pending, and provider preflight.
- Removed caller-mintable terminal-certification promotion.
- Reproduced the focused matrix under exact pinned dependencies.

## What Is Locked

- Exact implementation ancestry is `1db250169cdfe57ffa5d5cc5e5d24b2e937d5d33`.
- Exact audit target is `f64cadc` / tree `8c6dc885`.
- Released FS0/Alpha remain substrate; product namespace is `gv_portfolio_v0`.
- Canonical score remains 39; real prospective evidence remains 0/1.
- Terminal replay certification remains external; bounded portfolio remains blocked.

## What Is Next

- Run genuinely independent Reviewer A/B/C audit against the exact target.
- Verify report custody and provider identity as preflight.
- Accept Slice 0 and issue replay certification only through an external authority.

## First Command

```text
git status --short --branch && git rev-parse HEAD && .venv\Scripts\python -m pytest -q tests/gv_portfolio_v0
```
