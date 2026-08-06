# AOV-0 Full Local Hard Cut + Vertical — SAW Receipt

Mode: `CLOSURE_REPORT`
Date: 2026-08-06
RoundID: `ROUND-20260806-AOV0-FULL-LOCAL`
ScopeID: `AOV0-HARD-CUT-VERTICAL-LOCAL`
Branch: `codex/pit-source-authority-1`
Gate-A candidate: `39f7be3894623c095994066b8f0ea2895b968643`
Gate-B executable tip before docs closure: `dca69fc72dd3192913aa921323ff48f68610a925`

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-scope | Domains: Product, Software Engineering, Data Provenance, Quant Research, Governance

## Scope

In scope: freeze Episode-2 locally; destructively remove current compatibility authority; harden the research spine; implement the minimal AOV cube, Rule100/Parent/Child, hash DAG, five-arm evidence/seal machinery, official-SOFR cash, deterministic review core, zero-compat scan, local tests, and local commits.

Out of scope by explicit user boundary: push, hosted Windows/Linux execution, main fast-forward, tags/publication, provider access, outcome opening, broker/live capital.

## Acceptance checks

| Check | Result |
|---|---|
| CHK-01 Episode-2 exact immutable local SHA plus exact archived-byte selected matrix | PASS — `39f7be3`, `115/115` |
| CHK-02 destructive hard cut and ZERO-COMPAT six-count scan | PASS — all six counts `0` |
| CHK-03 five research-spine audit defects fixed without compatibility shims | PASS — hardened research `33/33` |
| CHK-04 minimal AOV cube/Rule100/Parent/Child/DAG/five-arm/seal/review mechanics | PASS — AOV `17/17` |
| CHK-05 current dashboard/book/historical-receipt regression | PASS — `33/33` |
| CHK-06 hard-cut Episode-2 domain regression | PASS — `107/107` |
| CHK-07 compile, workflow YAML, dependency and whitespace checks | PASS |
| CHK-08 first real prospective seal | FAIL/BLOCKED — owner insurance budget + five admitted inputs missing |
| CHK-09 real-seal fail-closed behavior preserves alpha evidence 0 and clock false | PASS |
| CHK-10 independent Reviewer A/B/C pass with separate ownership | NOT RUN — independent reviewer lane unavailable/not authorized in this local round |

ChecksTotal: 10
ChecksPassed: 8
ChecksFailed: 2

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Blocking | First real prospective clock cannot start without product-approved insurance budget. | Freeze `insurance_materiality_floor_ratio` and `insurance_premium_ceiling_annual_return`; production defaults remain `None`. | Product owner | Open |
| Blocking | Real seal lacks admitted current experiment bytes. | Admit permanent-ID Rule100 targets, vertical primitives, PIT total returns, official SOFR, and decision-cut receipt; do not substitute historical/synthetic/provider data. | Data / Product | Open |
| Blocking for SAW PASS | Mandatory independent Reviewer A/B/C ownership separation was not available in the local-only execution lane. | Run independent review against the exact local candidate when that review lane is authorized/available. | Review / Owner | Open external |
| Advisory | Episode-2 hosted Windows/Linux and publication custody remain open. | Preserve exact `39f7be3`; run hosted/push/publication only under separate authority. | Release | Open external |

## Implementer pass

The requested local execution was performed: Gate-A candidate commit, exact archive proof, destructive hard cut, research hardening, AOV vertical, test fixtures, first-seal fail-closed entrypoint, and local Git commits. No external-authority action occurred.

## Reviewer A/B/C pass

Reviewer A: `Unavailable` — independent strategy reviewer not available in this local execution channel.

Reviewer B: `Unavailable` — independent runtime reviewer not available in this local execution channel.

Reviewer C: `Unavailable` — independent data-integrity reviewer not available in this local execution channel.

Ownership check: `BLOCK` for terminal SAW PASS because implementer/reviewer independence was not established. Local deterministic regression evidence remains valid but is not a substitute for independent review.

## Scope split summary

In-scope implementation/hard-cut/local validation: complete except the real seal, which correctly fails closed on missing owner/data authority.

Inherited/external: hosted E2 proof, independent reviews, push/publication remain outside this local authorization. Provider acquisition is not a valid workaround for missing first-seal data in this round.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `dashboard.py`, `views/page_registry.py` | one canonical three-page application shell; legacy authority removed | local regression PASS; independent unavailable |
| root Alpha/Portfolio app/launch files + `docs/archive/legacy_runtime_source/` | current runtime compatibility deleted; historical source archived | zero-compat PASS; independent unavailable |
| `release/gv-alpha0/RECEIPT.json`, FS0 workflow/tests | historical release becomes receipt-integrity contract, not root rebuild | local tests PASS |
| `gv_portfolio_v0/book.py` | legacy byte-compatible book projection removed | local book tests PASS |
| `research/*`, `research/adapters/rule100_replay_adapter.py` | content identity, named benchmarks, finite costs, PIT-EW schedule, permanent-ID/cash strictness, immutable evidence manifest | research `33/33` PASS |
| `research/aov0/*` | contract, cash, cube, policy, DAG, experiment/seal, deterministic review | AOV `17/17` PASS |
| `scripts/aov_zero_compat_scan.py` | six-counter hard-cut acceptance | PASS all zero |
| `scripts/aov0_first_seal.py` | real-seal fail-closed entrypoint | BLOCKED as expected; alpha 0, clock false |
| `tests/aov0/*` and updated regression suites | hard-cut/mechanical/owner-boundary tests | PASS |
| current authority docs/context | recut to two-gate executed state and first-seal blocker | validation pending at report draft |

## Validation / evidence

- Gate-A exact candidate `39f7be3`: `115/115 PASS` from `git archive` bytes.
- Gate-B hard-cut exact candidate lineage: AOV `17/17`; hardened research `33/33`; canonical dashboard/book/receipt `33/33`; hard-cut E2 regression `107/107`.
- Historical Alpha runtime substrate in live Git checkout: `7/7 PASS`; bare archive intentionally refuses without Git/package manifest.
- ZERO-COMPAT: six counters exactly zero.
- Python compile: PASS.
- Workflow YAML parse: PASS.
- `pip check`: PASS.
- `git diff --check`: PASS before docs closure; rerun required after current-truth synchronization.
- First real seal command: `BLOCKED_OWNER_DECISION_AND_ADMITTED_INPUTS`, `prospective_clock_started=false`, `alpha_evidence=0`.

## Open Risks

Open Risks: owner insurance materiality/premium values are not frozen; five admitted current AOV input artifacts are missing; independent Reviewer A/B/C and hosted external custody are not run.

## Next action

Next action: owner freezes the insurance materiality floor and annual premium ceiling, then admit the five current AOV artifacts and execute the first real immutable five-arm seal immediately. Do not add another architecture phase.

ClosurePacket: RoundID=ROUND-20260806-AOV0-FULL-LOCAL; ScopeID=AOV0-HARD-CUT-VERTICAL-LOCAL; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=Owner insurance budget and five admitted AOV inputs are missing, independent Reviewer A/B/C not run; NextAction=Freeze owner insurance budget and admit five current inputs, then execute first real seal
ClosureValidation: PASS
SAWBlockValidation: PASS
