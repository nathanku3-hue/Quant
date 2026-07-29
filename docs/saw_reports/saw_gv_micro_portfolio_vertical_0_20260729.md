# SAW — GV Micro-Portfolio Vertical 0 Final Audit Target

SAW Verdict: BLOCK
RoundID: `ROUND-20260729-GV-MICRO-PORTFOLIO-VERTICAL-0`
ScopeID: `GV-MICRO-PORTFOLIO-VERTICAL-0-PLUS-REPLAY-SHADOW`
Hierarchy Confirmation: Approved via persisted fallback | Session: current-thread | Trigger: inherited-product-execution | Domains: Portfolio Systems, Accounting, Decision Systems, Product UX, Replay/Certification, Docs/Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase0-gv-micro-portfolio-vertical-0-brief.md`

## Audit target

- branch: `codex/gv-micro-portfolio-v0`;
- candidate commit: `f64cadcb2a9aaf0708744099ddc03ea2c41617eb`;
- candidate tree: `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`;
- origin equality: PASS;
- audited R0 base: `1db250169cdfe57ffa5d5cc5e5d24b2e937d5d33`.

## Scope

Implement one bounded four-security deterministic paper-portfolio operator loop and exact replay shadow. Preserve released FS0, root custody, score, and forbidden scope. Verify independent-report custody as preflight, but do not mint terminal replay certification locally. Do not claim terminal Slice 0 acceptance, prospective evidence, or scale without independent Reviewer A/B/C reports and an external authority decision.

## Acceptance checks

| Check | Requirement | Result |
|---|---|---|
| CHK-01 | Candidate descends from audited `1db2501`; audit receipt and nine seams precede product code | PASS |
| CHK-02 | Released `gv_fs0_v1` and Alpha behavior remain substrate; new namespace only | PASS |
| CHK-03 | Four securities, benchmark, classified cash, principal/substitute/competitor/abstain/cash roles are visible | PASS |
| CHK-04 | Permanent identity, exact-byte evidence, and canonical events have one low-level authority and fail closed on tampering | PASS |
| CHK-05 | 2:1 split preserves value; book and NAV reconcile exactly to terminal NAV `1499` | PASS |
| CHK-06 | Living Thesis Lite, scenarios, explicit outcomes, deterministic competition, aim, order, and fill are complete | PASS |
| CHK-07 | Original decision snapshot remains byte-immutable through execution and later WATCH observation | PASS |
| CHK-08 | Product certification, atomic persistence, verified reopen, deterministic bytes, and corruption refusal pass | PASS |
| CHK-09 | Missing valuation produces `VALUATION_PENDING`; no price or NAV is invented | PASS |
| CHK-10 | Broker-free network-denied AppTest completes review → confirm → certify/reopen → WATCH explanation | PASS |
| CHK-11 | Exact shadow replay reconstructs economics/decision/thesis/product-certification state and passes idempotence, corrections, partial fills, overfill, and valuation fixtures | PASS |
| CHK-12 | GitHub preflight verifies origin repository, candidate commit/tree, reviewer identity, and exact report bytes; no local terminal-promotion capability remains | PASS |
| CHK-13 | Exact pinned environment reproduces 38/38 portfolio tests and 282/282 focused matrix; candidate is pushed, remote-equal, and root untouched | PASS |
| CHK-14 | Genuinely independent Reviewer A/B/C reproduce and accept exact candidate and submit externally authoritative reports | BLOCK — reports unavailable |

## Implementer pass

- Banked audit receipt and seam contract before product code.
- Implemented one custody backend for domain-separated IDs, evidence references, immutable events, split handling, classified cash, NAV, product certification, and atomic storage.
- Implemented thesis/scenario review, explicit outcomes, deterministic capital competition, aim, order, and fill.
- Implemented Streamlit operator flow, restart/reopen, later WATCH admission, and unchanged-aim explanation.
- Implemented exact shadow replay, duplicate-delivery idempotence, corrections, partial fills, valuation-pending, and prior-product-certification byte stability.
- Added fail-closed GitHub report-custody preflight, including wrapped base64 content.
- Removed local helpers capable of promoting caller-built data into terminal replay certification.
- Preserved score 39 and all provider-data, broker, alpha, and live-capital boundaries.

## Reviewer A — Strategy and product correctness

Local perspective: PASS.

- The slice changes user capability rather than adding horizontal architecture.
- Four outcome classes and cash compete explicitly.
- The substitute selection follows the declared deterministic formula.
- The later WATCH fixture cannot rewrite the original decision or claim real prospective evidence.
- Replay is complete as shadow evidence; terminal acceptance remains correctly external.

## Reviewer B — Runtime and operational resilience

Local perspective: PASS.

- Atomic temp-to-replace persistence and hash-bound reopen pass.
- Corrupt persisted state fails closed.
- AppTest operates with outbound network denied and no broker/provider-data imports.
- Restart/reopen preserves terminal state.
- GitHub preflight fails closed on dirty checkout, non-origin repository, provider failure, identity mismatch, candidate/tree mismatch, receipt URL mismatch, report absence, invalid base64, and byte mismatch.
- Exact locked dependencies reproduce the 282-test matrix.

## Reviewer C — Data integrity and performance path

Local perspective: PASS.

- Decimal strings own economic authority; binary floats are absent from truth.
- Split residual is exactly zero.
- Terminal arithmetic reconciles: `700 + 774 + 25 = 1499`.
- Missing price yields null NAV with `VALUATION_PENDING`.
- Event IDs, evidence hashes, book hash, order/fill IDs, and product certification are rebuilt on load.
- Replay is fixed-size and byte-deterministic; no unbounded data or performance path was introduced.

## Ownership check

The implementer and local review perspectives are not independent agents. No independent Reviewer A/B/C capacity is available through the current connector. Therefore local evidence cannot satisfy terminal ownership separation and SAW remains BLOCK.

## Validation evidence

- Exact environment: Python `3.12.10`, pytest `9.0.2`, Streamlit `1.54.0`, jsonschema `4.26.0`.
- Portfolio/custody/operator/replay suite: `38/38 PASS`.
- Focused pinned matrix: `282/282 PASS` = `38` portfolio/replay + `150` protocol + `25` context + `24` authority + `45` Alpha release/core.
- Runtime persist/reopen/WATCH/replay smoke: PASS; terminal NAV `1499`; shadow evidence hash `a4ad7ab7da0039fc5e7e4af19463091a72adf8ec4adb9b98c1c5fd47374d44d1`.
- Context build and fail-closed validation: PASS.
- Compile, JSON validation, and `git diff --check`: PASS.
- Candidate local/origin equality: PASS at `f64cadcb2a9aaf0708744099ddc03ea2c41617eb`.
- Candidate tree: `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`.
- Root non-interference: PASS; root remains at `accef5c6` with 5,600 status entries.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Future-dated WATCH fixture could be misread as prospective evidence | Use known deterministic chronology and explicit fixture-only boundary | Slice 0 | CLOSED |
| High | Certification projection initially applied full-ledger continuity to a lineage projection | Separate ordered projection semantics from strict persisted-ledger continuity | Slice 0 | CLOSED |
| High | Caller-generated reviewer fields could self-authorize replay | Structural receipts permanently non-authorizing; provider checks added as preflight | Replay | CLOSED |
| Critical | Local promotion helpers could mint terminal certification from caller-built provider records | Remove promotion helpers and authorizing tests; keep CLI shadow-only even after preflight | Replay/integrator | CLOSED |
| Medium | GitHub contents API wraps base64 across lines | Normalize whitespace before strict base64 decoding; add regression | Replay | CLOSED |
| Medium | Test package initially shadowed the product package | Explicit product-path resolution in test package | Slice 0 | CLOSED |
| Medium | Concurrent same-worktree writers created duplicate custody semantics and stale governance artifacts | Reconcile to one custody backend; preserve redundant artifacts under ignored `tmp/`; publish one active brief and SAW | Integrator | CLOSED |
| Medium | Stale FS0-first authority assertions rejected current roadmap | Rebind tests to Slice 0 → replay while preserving released substrate | Product closure | CLOSED |
| Medium | Independent Reviewer A/B/C reports do not exist | External reviewers audit exact candidate and publish authoritative reports | Independent auditors | OPEN |

## Scope split

### In-scope

- deterministic micro-portfolio truth, decision, execution, product certification, persistence, reopen, operator UX;
- exact replay shadow and external-report preflight;
- focused regression, candidate custody, and audit handoff.

### Inherited / out-of-scope

- terminal replay certification authority;
- real external prospective evidence;
- bounded portfolio expansion;
- providers/WRDS data, broad data, optimizer, tax/FX/derivatives/shorting, broker, score uplift, alpha, or live capital;
- dirty root recovery.

## Forbidden-action scan

PASS. No provider-data access, broker, live-capital, score uplift, alpha claim, root cleanup, or released-FS0 behavioral mutation occurred. GitHub access exists only in non-authorizing audit-report preflight and cannot alter portfolio truth or mint terminal certification.

## Document Changes Showing

| Path group | Change summary | Reviewer status |
|---|---|---|
| `contracts/gv_portfolio/v0/**`, `core/gv_portfolio_v0/**` | single identity/evidence/event custody authority | Local A/B/C PASS |
| `gv_portfolio_v0/**`, `validation/gv_portfolio_v0_replay.py` | bounded product, storage, exact shadow replay, safe provider preflight | Local A/B/C PASS |
| `portfolio_app.py`, `launch_portfolio.py`, `views/gv_portfolio_v0_workspace.py` | broker-free operator loop | Local A/B/C PASS |
| `tests/gv_portfolio_v0/**` | accounting, custody, persistence, AppTest, replay, correction, partial-fill, wrapped-report, provider-preflight cases | 38/38 PASS |
| active brief/current context/evidence | exact audit target, score/claim boundary, next gate | Local A/B/C PASS |
| `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md` | formulas, decisions, misses, and guardrails | Local A/B/C PASS |

## Open Risks:

- Independent Reviewer A/B/C ownership and externally authoritative reports are missing.
- Terminal replay certification and bounded portfolio remain blocked by that external evidence gate.

## Next action:

Independently audit commit `f64cadcb2a9aaf0708744099ddc03ea2c41617eb` / tree `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`. Publish exact Reviewer A/B/C reports. Use GitHub verification as custody preflight, then obtain an external terminal acceptance/certification decision. Bounded portfolio remains closed until then.

ChecksTotal: 14
ChecksPassed: 13
ChecksFailed: 1

ClosurePacket: RoundID=ROUND-20260729-GV-MICRO-PORTFOLIO-VERTICAL-0; ScopeID=GV-MICRO-PORTFOLIO-VERTICAL-0-PLUS-REPLAY-SHADOW; ChecksTotal=14; ChecksPassed=13; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent-reviewer-a-b-c-reports-missing; NextAction=audit-f64cadc-and-obtain-external-certification

ClosureValidation: PASS
SAWBlockValidation: PASS
SAW Verdict: BLOCK
