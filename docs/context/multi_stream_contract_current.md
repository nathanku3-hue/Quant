# Multi-Stream Contract - Quant Current

## Active Addendum — Request Artifact Identity Repair V1 (2026-07-11)

| Stream | Current status | Handoff / boundary |
|---|---|---|
| Docs/Ops | Identity repair active; exact 20260701 request payloads banked in Commit 1, detached envelope pending | Keep lifecycle fail-closed; no dispatch claim |
| Data | Held | No source-byte inspection, provider, validation, readiness, or data output |
| Strategy | Held | No return/curve/alpha/tradability work |
| Frontend/UI | Held | No readiness or strategy surface expansion |

- Cross-stream rule: tracked payload bytes alone are not dispatch authority. A detached envelope may prove identity but must remain `PREPARED_NOT_SENT` and cannot authorize downstream work.
- Next action: bind Commit 1 in a tracked detached envelope, rerun preflights and fresh A/B/C, and keep dispatch denied.

## Prior Addendum — Checkout Hygiene / Governance Recovery (2026-07-11)

| Stream | Current status | Handoff / boundary |
|---|---|---|
| Docs/Ops | Hygiene green at `e470137`; exact request-artifact identity still failed | See active identity-repair addendum |
| Data / Strategy / Frontend | Held | Unchanged holds |

## Prior Addendum — P0 Trust-Substrate Repair (2026-07-11)

| Stream | Current status | Handoff / boundary |
|---|---|---|
| Docs/Ops | P0 identity repair banked; hygiene recovery subsequently cleared planning preflight | See active addendum |
| Data | Held | Unchanged hold |
| Strategy | Held | Unchanged hold |
| Frontend/UI | Held except GOV-002 wording repair in hygiene recovery | Unchanged hold on product claims |

- Cross-stream rule: a duplicate JSON key, ambient Git redirection, a non-commit/broken identity, or any Git replacement-ref state invalidates authority before downstream work begins.

## Active Addendum - V2 PEAD M6b Slice 0 Contract Correction (2026-07-02)

| Stream | Current status | Handoff / boundary |
|---|---|---|
| Data | Held at request-dispatch sequencing; strict Gate A accepts only first-public/unrestated EPS | No source inspection, factual validation, or readiness promotion |
| Strategy | Held | No return, curve, CAGR, alpha, or tradability work |
| Frontend/UI | Held | No readiness or strategy surface |
| Docs/Ops | Active phase brief corrected; repository-identity gate added to canonical approval/request template | Historical addenda remain unchanged; Thin SAW evidence is required before dispatch |

- Cross-stream rule: `release_date_aligned_but_restated` may remain a non-strict diagnostic label but cannot satisfy strict Gate A, `strict_vintage_pit`, or `m6b_data_contract_ready`.
- Repository-identity rule: a request or approval packet must resolve its declared repository, commit, tree, artifact path, and artifact hash before it can transfer authority.
- Next action: dispatch only the already prepared Gate A and Gate B/C source-access requests.

## Authoritative Addendum - V2 PEAD Strict M6b Phase 0 Successor Requests (2026-07-01)

| Stream | Current status | Handoff / boundary |
|---|---|---|
| Data | Gate A successor contract/request prepared; A blocked, B candidate-only, C attribute-scope blocked, D deferred | Await separate data-owner source-access approvals; no artifact inspection before approval |
| Strategy | Held | No flagged curve, long-only substitute, returns, CAGR, alpha, or tradability work |
| Frontend/UI | Held | No readiness or strategy surface |
| Docs/Ops | Successor contract/request artifacts and governance refresh in scope | Thin SAW is request-only and cannot substitute for real-artifact A/B/C review |

- Cross-stream dependency: Gate A approval must bind PIT-family bytes, timing artifact only when selected EPS timing is insufficient, and an immutable calendar source of record.
- Open decisions: data owner must approve or decline Gate A and Gate B/C source-access requests; Gate D waits for source-independent consumer-interface proof.
- Status claim: canonical current evidence and strict readiness remain unchanged.

## Authoritative Addendum - V2 PEAD Strict M6b Path A Gate Infrastructure (2026-06-30)

| Stream | Current status | Handoff / boundary |
|---|---|---|
| Data | Active Path A; Gates A/B/C/D `BLOCKED`; restated-EPS exception `NOT_AUTHORIZED` | Next action: obtain authorized, verifiable evidence for the smallest blocked strict-data gate. |
| Strategy | M6a sparse engine/framework evidence only; promotion held | No real return, curve, CAGR, alpha, or tradability output while `m6b_data_contract_ready=false` |
| Frontend/UI | Held | No alpha/readiness surface or action path |
| Docs/Ops | Evidence-only validator, tests, and fail-closed readiness JSON locally validated; terminal A/B/C infrastructure review pending | Review cannot promote data readiness |

- Cross-stream rule: B stays an isolated illustrative diagnostic and is never a strict-data fallback.
- Authorization rule: evidence content cannot self-authorize; malformed authorization JSON/schema is a CLI input error, and current gate PASS requires distinct exact-file-hash/scope/mode/action authorization plus all four verified local source-byte hashes.
- Exception reconciliation: inherited wording that permits a flagged restated-EPS exception is superseded on current truth surfaces; the exception remains `NOT_AUTHORIZED` and cannot satisfy strict Gate A.
- Evidence: `docs/context/e2e_evidence/pead_m6b_strict_path_a_readiness.json`, SHA-256 `0ef4b2504f7f573eab734614054e3c3e9ffa746b02522a6ef00a51453010574a`; strict-gate 68/68 and M6a 12/12 tests pass; well-formed authorization mismatch keeps A-D blocked with exit 0.
- Current contract: `strict_vintage_pit=false`, `m6b_data_contract_ready=false`, `workflow_status=blocked_fail_closed`.

## Latest Addendum - V2 PEAD M6b Option 1 Repair PASS & Strict M6b Path A Alignment (2026-06-25)

| Stream | M6b status | Boundary |
|---|---|---|
| Data | Option 1 B (Best-Available) diagnostic repaired for engine sanity; Strict M6b Path A data prep not yet "done done" (fails on restated EPS, proxy returns, missing liquidity screen) | Open only strict M6b gates next: first-public EPS or explicit flagged exception, delisting-adjusted tradable returns, as-of liquidity/tradability, borrow assumptions |
| Strategy | M6a.1 sparse portfolio engine core locally complete and Reviewer C rerun PASS; final closure pending Reviewer B | No tradable equity curve, CAGR, or alpha claims until strict M6b data gates pass |
| Frontend/UI | Held behind Alpha Interpretation Gate | No alpha-named panel, route, card, field, label, or dashboard action state |
| Docs/Ops | Stale cross-stream docs refreshed to June 25 M6 truth | Keep B path as illustrative engine sanity diagnostic only; align with original intent |

- Cross-stream rule: Fastest valid reboot is strict M6b Data Path A, not Strategy or Frontend. Best-available B artifacts remain illustrative-only / not_alpha / not_tradable_claim.
- Current bottleneck: Strict M6b data readiness fails due to restated EPS vintage, proxy/non-delisting returns, and lack of full as-of tradability/liquidity screen. Strategy closure is not cleanly reconciled; new frontend remains held behind the alpha-interpretation gate.

## Latest Addendum - V2 PEAD Alpha Interpretation Gate OPEN (2026-06-24)

| Stream | Gate status | Boundary |
|---|---|---|
| Strategy | Current M1B statistic reclassified as descriptive methodology evidence only | No alpha, PIT, tradability, net, causal, full-factor, or population-validity claim |
| Data | Existing evidence JSON is read-only input | No provider, Parquet, manifest, evidence, or artifact mutation |
| Frontend/UI | Held | No alpha-named panel, route, card, field, label, or test code |
| Docs/Ops | Gate brief and current-truth route updated | Owner must approve or hold gate before Path A/Path B |

- Cross-stream rule: dashboard scope must follow the interpretation gate, not precede it.
- Current bottleneck: owner approval of the Alpha Interpretation Gate plus 28-commit/main reconciliation before any alpha-implying code.

## Prior Addendum - V2 PEAD M4A Memory-Bounded Full-Universe Expansion (2026-06-22)

| Stream | M4A status | Boundary |
|---|---|---|
| Data | Bounded local full-universe D2A/D2B builders implemented and focused PEAD validation PASS | No provider access, no new data artifact publication in this round |
| Strategy | Unchanged | No estimator tuning, interpretation, alpha verdict, ranking, scoring, or promotion |
| Frontend/UI | Unchanged and deferred | No dashboard/action-state change |
| Docs/Ops | M4A brief, product/spec, notes, decision log, lesson, context, SE evidence, historical SAW BLOCK, and clean-exit rerun evidence refreshed | Strict independent Reviewer A/B/C remains optional governance before M4B; clean full-suite exit is complete |

- Cross-stream rule: M4A is Data builder readiness only; it must not be converted into a PIT/full-universe alpha claim or product action.
- Current bottleneck: M4B full-universe artifact dry-run/publication scope control; M3/M5 remain blocked on WRDS/CRSP entitlement.

## Latest Addendum - V2 PEAD M2 Read-Only Status (2026-06-21)

| Stream | M2 status | Boundary |
|---|---|---|
| Frontend/UI | PEAD Evidence Status tab implemented in Strategy Research Replay | Read-only PM-readable status only; no alpha approval language |
| Strategy | M1B estimator/evidence unchanged | No estimator tuning, interpretation, ranking, scoring, or promotion |
| Data | Locked validation JSON and M1B JSON read as byte snapshots only | No Parquet read, provider access, artifact mutation, or recomputation |
| Docs/Ops | Current truth surfaces updated for M2 status presentation | Next decision is product review of presentation, not alpha verdict |

- Cross-stream rule: M2 may display locked evidence readiness only; it must not convert M1B numbers into an alpha verdict or action surface.
- Presentation rule: successful UI should not lead with hashes, manifests, paths, or audit plumbing.
- Current bottleneck: owner review of the read-only status surface; alpha verdict remains separate.

## Latest Addendum - V2 PEAD M1B Dashboard Marker Closure PASS (2026-06-21)

| Stream | Closure status | Handoff / boundary |
|---|---|---|
| Frontend/UI | Event-ledger marker trace labels restored to `ENTER` and `EXIT` | Preserve hover wording and marker styling; no dashboard action state or feature expansion |
| Strategy | M1B estimator/evidence unchanged | No estimator tuning, alpha interpretation, promotion, or new signal contract |
| Data | D1/D2B/D3 and protected JSON unchanged | No provider access, no source/artifact mutation |
| Docs/Ops | Terminal M1B SAW PASS and current truth refreshed | Next decision is separate alpha-verdict review gate only |

- Cross-stream rule: the dashboard repair closes a display-contract regression only; M1B evidence remains numbers-only.
- Current bottleneck: alpha verdict and any product/action authority require separate approval.

## Latest Addendum - V2 PEAD Calendar-Time Inference M1B (2026-06-21)

| Stream | M1B status | Handoff / boundary |
|---|---|---|
| Strategy | Calendar-time estimator implemented in `strategies/pead_event_study.py` | Evidence-only method output; no alpha verdict or promotion |
| Data | D1/D2B/D3 consumed read-only through manifest/hash validation | No provider access, no source/artifact mutation, protected JSON unchanged |
| Frontend/UI | Unchanged and held | No dashboard action state, rank/score, alert, recommendation, or broker/order path |
| Docs/Ops | M1B phase brief, product/spec, notes, decision log, lesson, context, evidence, and BLOCK SAW refreshed | Recover the inherited dashboard test and terminal Reviewer C audit before any alpha-verdict decision |

- Cross-stream rule: M1B evidence may support a future bounded review decision only; it is not a product signal.
- Current bottleneck: one inherited Frontend/UI dashboard test failure plus unavailable hierarchy-only Reviewer C confirmation.

## Latest Addendum - V2 PEAD M1A Inference Methodology Gate (2026-06-21)

| Stream | M1A status | M1B ownership boundary |
|---|---|---|
| Strategy | Read-only; method contract selected, terminal approval pending Reviewer C | Calendar-time formation/regression/robustness helper inside `strategies/pead_event_study.py` only; all-quantile overlap resolution precedes Q1/Q5 filtering after Reviewer C PASS |
| Data | D1/D2B/D3 artifacts read-only | Validate existing manifest/hash/session inputs; no artifact mutation or provider access |
| Frontend/UI | Unchanged and held | No alpha verdict, monitor expansion, ranking/scoring, alerts, recommendations, or actions |
| Docs/Ops | M1A contract and truth surfaces owned; terminal SAW BLOCK pending Reviewer C | New M1B evidence artifact, deterministic schema, acceptance evidence, and closure updates only after Reviewer C PASS |

- Cross-stream rule: Strategy may consume only locked D2B/D3 lineage after terminal M1A review passes; Data remains immutable; UI remains read-only and cannot interpret M1B before a separate approval.
- Current bottleneck: independent Reviewer C terminal recheck plus unresolved data-quality limits.

## Latest Addendum - V2 PEAD Read-Only Evidence Dashboard DONE (2026-06-20)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Frontend/UI | Read-only evidence dashboard implemented in Strategy Research Replay | Preserve exact review-only framing and fail-closed UI behavior |
| Strategy | No formula/recomputation change; existing evidence fields are displayed only | Daily HAC inference remains unavailable; quarterly output remains descriptive-only |
| Data | Locked JSON is unchanged and hash-gated | Preserve SHA `96cdc975...`; no Parquet/provider/artifact access from the view |
| Docs/Ops | Product contracts, decision/notes/lesson, SAW, and current truth refreshed | Owner product review is the only next decision |

Shared boundary: JSON-read-only owner-review display only. No alpha proof/promotion, rank/score, alert, recommendation, broker/order, provider, Parquet, formula, or artifact mutation scope.

Single next action: owner product review of the implemented read-only evidence dashboard.

## Latest Addendum - V2 PEAD Real-Data Validation DONE (2026-06-20)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | Existing PEAD real-data validation JSON is locked for review; no artifacts changed | Preserve JSON SHA `96cdc975...`, D1/D2B/D3 lineage, and stated limitations |
| Strategy | Real-data CAR/BHAR numbers exist as evidence only | Daily event-date HAC inference is unavailable; quarterly output is ex-post descriptive only |
| Docs/Ops | Current truth surfaces reconciled to put PEAD real-data validation DONE first | Rebuild and validate `current_context.*`; next action is owner JSON review |
| Frontend/UI | Deferred | No dashboard scoping until owner approves JSON review; no implementation authorized |

Shared boundary: this is docs-context reconciliation only. It does not change formulas, artifacts, strategy code, dashboard code, or the evidence JSON, and it does not authorize alpha claims, promotion, ranking/scoring, alerts, or broker/order paths.

Single next action: owner review of `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`; if approved, make a separate dashboard-scoping decision.

## Latest Addendum - V2 PEAD D3 Strategy Benchmark Handoff DONE (2026-06-20)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D2B/D3 artifacts unchanged and validated at their manifest pointers | Preserve hashes, session semantics, and missingness |
| Strategy | D3 benchmark handoff test PASS; no production code change required | Existing CAR/BHAR summary path is the locked consumer contract |
| Docs/Ops | Reviewer A/B/C reconciliation, SAW PASS, and current truth refresh complete | Next decision is bounded D4 scope only |
| Frontend/UI | Deferred | No dashboard implementation until separate D4 scope approval |

Shared boundary: this round added test coverage only. It did not alter data, strategy behavior, benchmark formulas, dashboard code, rankings, alerts, broker paths, staging, or commits.

Single next action: approve or hold a bounded D4 dashboard-integration scoping round.

## Latest Addendum - V2 PEAD D3 Benchmark Artifact Publication DONE (2026-06-20)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D3 benchmark artifact is published with complete 2,810-session D2B coverage and SHA `f7dede99...` | Preserve immutable Parquet plus atomic manifest pointer; no date patching or fallback benchmark |
| Docs/Ops | D3 publication evidence and current truth refreshed | Next decision is separate strategy benchmark handoff validation |
| Strategy | Deferred for this round | May consume benchmark only in a separately approved validation round; no alpha interpretation now |
| Frontend/UI | Deferred | No dashboard work authorized |

Shared boundary: this round published benchmark input only. It did not change D1/D2A/D2B semantics, run CAR/BHAR interpretation, add dashboard scope, rank/score, alert, call broker paths, stage, or commit.

Single next action: approve or hold a separate bounded D3 strategy benchmark handoff validation round.

## Latest Addendum - V2 PEAD D2B Terminal Reviewer Rerun PASS (2026-06-20)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D2B session-spine repair is terminal reviewer PASS; active artifact remains SHA `c3da606a...` | Preserve the 2,810-session source-backed spine and fixed-security semantics |
| Docs/Ops | Rerun PASS SAW and current truth refreshed | Next gate is separate D3 benchmark artifact publication approval |
| Strategy | No code change; strategy handoff remains validated by the 70-test matrix and Reviewer A PASS | No CAR/quintile interpretation until D3 publication is separately validated |
| Frontend/UI | Deferred | No dashboard work authorized |

Shared boundary: this rerun changed only review/docs evidence. No D3 artifact was published, no alpha was interpreted, and no commit/staging occurred.

Single next action: approve or hold a separate bounded D3 benchmark artifact publication gate.

## Latest Addendum - V2 PEAD D2B Authoritative Market-Session Spine Repair (2026-06-19)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D2B session-spine repair, corrected immutable sample artifact, and chunked handoff memory repair complete; terminal SAW is BLOCK only on final reviewer unavailability | Preserve the 2,810-session source-backed spine and active SHA256 `c3da606a...` |
| Docs/Ops | Brief, product/spec, formulas, decision, lesson, current truth, and terminal BLOCK SAW refreshed | Rerun final Reviewer A/B/C after capacity returns and regenerate/validate `current_context.*` |
| Strategy | Active-scale handoff PASS with 11,450 events, 687,000 complete rows, and 1,756.7 MiB peak RSS; metadata/timing and normalized-key counterexamples fail closed | Continue using the same explicit authoritative spine; no CAR/quintile interpretation |
| Frontend/UI | Deferred | No dashboard work authorized |

Shared boundary: D2A rows were not deleted, D2B security-selection semantics were not changed, and no D3 artifact was published.

Single next action: rerun final independent Reviewer A/B/C on the repaired D2B state; after PASS, approve or hold a separate bounded D3 benchmark artifact publication round.

## Latest Addendum - V2 PEAD D3 Benchmark Artifact Builder PARTIAL (2026-06-19)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D3 builder/tests implemented; artifact publication blocked | Audit/repair D2B/D2A session spine before rerunning D3 publication |
| Docs/Ops | Partial implementation brief, formula notes, decision log, lesson, and current truth refreshed | Preserve fail-closed artifact boundary and generate/validate `current_context.*` |
| Strategy | Narrow summary repair only | Raw cumulative asset return is preserved when only benchmark coverage is missing; CAR/BHAR and eligibility remain benchmark-gated; no CAR/quintile interpretation |
| Frontend/UI | Deferred | No dashboard work authorized |

Shared boundary: no D3 benchmark Parquet/manifest was published. Missing benchmark dates must not be filled, dropped, interpolated, zeroed, or substituted.

Single next action: bounded D2B/D2A market-session spine audit and repair.

## Latest Addendum - V2 PEAD D3 Benchmark Input Design Gate (2026-06-19)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | Benchmark-input contract DONE; no artifact implementation | Future D3 implementation must use Ken French daily factors, decimal units, `mktrf + rf`, strict D2B spine alignment, no missing-date fill |
| Docs/Ops | D3 contract, formula notes, decision log, lesson, current truth, and thin SAW evidence refreshed | Generate/validate `current_context.*`; preserve blocked scope |
| Strategy | Unchanged | Existing `benchmark_return_column` semantics stand; `car` remains beta-1 market-adjusted CAR |
| Frontend/UI | Deferred | No dashboard work authorized |

Shared boundary: this is a design gate only. It does not authorize provider fetch, benchmark artifact publication, strategy code changes, CAR/quintile interpretation, dashboard, ranking, alerts, broker paths, full build, staging, or commit.

Single next action: bounded D3 benchmark artifact implementation only, if separately approved.

## Latest Addendum - V2 PEAD D2B Fixed Event-Security Window (2026-06-19)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | Bounded D2B slice DONE: fixed event security, exact global `+1..+60`, atomic artifact, 4,867 eligible handoffs, final Reviewer A/B/C PASS | Preserve D1/D2A/D2B formulas, immutable artifact lineage, and the bounded-slice boundary |
| Docs/Ops | D2B terminal SAW, brief final-review status, and current truth surfaces refreshed | Generate/validate `current_context.*`; do not edit code/tests/data/product canon |
| Strategy | Canonical adapter smoke PASS with 4,867 events, unique D2A keys, identical spine, and 292,020 complete rows | No second window algorithm; no alpha interpretation |
| Frontend/UI | Deferred | No dashboard work authorized |

Shared boundary: D2B is a final-review-promoted bounded Data slice, not PEAD phase-end. Final Reviewer A/B/C reconciliation is PASS.

Single next action: bounded D3 benchmark-input contract/design gate only; provider fetch and alpha interpretation require separate approval.

## Latest Addendum - V2 PEAD D2A Security-Level Return Repair (2026-06-19)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D2A corrected 500-GVKEY security-level return sample and atomic manifest pointer PASS | Hand off immutable `security_id/date/total_return` rows to a separate D2B round |
| Docs/Ops | Formula, decision, lesson, truth, artifact protocol, and SAW evidence refreshed | Preserve legacy sample as superseded evidence only |
| Strategy | Existing contract remains unchanged | Wait for D2B fixed event-security selection and `+60` session extraction |
| Frontend/UI | Deferred | Dashboard remains downstream of D2B and strategy smoke |

Single next action: D2B fixed event-level IID selection and `+60` market-session extraction.

## Latest Addendum - V2 PEAD D1 Parent Closure Reconciliation (2026-06-18)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | Existing D1 repair artifact and full SAW reconciled; no implementation performed in this round | D2 return/IID repair starts separately |
| Docs/Ops | Artifact hash, SAW path, ownership caveat, limitation, and current truth reconciled | Untracked local D1 files remain explicit; no clean tracked-repo closure claim |
| Strategy | Unchanged | Wait for corrected D2 and then run a separate contract smoke |
| Frontend/UI | Deferred | Dashboard remains downstream of corrected D1+D2 and strategy smoke |

Single next action: start D2 return/IID repair in a separate round.

## Latest Addendum - V2 PEAD D1 Repair (2026-06-18)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Data | D1 repaired and rebuilt; early RDQ dedup removed 1,447 contaminated lag-valid events | Own separate D2 repair beginning with `(gvkey, iid)` return continuity |
| Docs/Ops | D1 brief, product/spec, formula, decision, lesson, quality metrics, limitation, current-truth surfaces, and SAW report refreshed | D1 terminal evidence published |
| Strategy | Existing handoff-ready contract unchanged | Wait for a separately repaired D2 handoff |
| Frontend/UI | Deferred | No UI scope authorized |

Shared D1 lock: raw numeric `epspxq`, no `ajexq` division, identity dedup before stateful transforms, exact t-4, raw plus clipped SUE, flag-only liquidity, raw extreme-SUE quality gate, empty-output preservation, current-vintage limitation, and atomic artifact/manifest publication.

Single next action: separate D2 repair starting with `gvkey+iid` returns before any daily ADV selection.

## Latest Addendum — V2 PEAD Strategy Contract (2026-06-18)

| Stream | Current status | Handoff / dependency |
|---|---|---|
| Strategy | Contract implemented, tested, and Reviewer A/B/C rerun PASS | Handoff-ready for corrected D1/D2 inputs only |
| Data | Owns D1/D2 formula repairs and primary-security/benchmark/delisting policy | Must not be modified by Strategy stream |
| Docs/Ops | Product/spec/decision/lesson/context/SAW rerun evidence updated | Context packet refreshed from this addendum |
| Frontend/UI | Deferred | No UI scope authorized |

Shared success condition: corrected Data-stream D1/D2 handoff can plug into `strategies/pead_event_study.py` without changing formula semantics or widening scope.

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, strategy search, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, or scope widening by itself.
Purpose: coordinate streams after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - V2-D0.4C Local Read-Only Permission Probe Approval

RoundID: `ROUND-20260603-V2-D0-4C-LOCAL-READ-ONLY-PERMISSION-PROBE-APPROVAL`
ScopeID: `V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL_DOCS_ONLY`
Verdict: `PASS_DOCS_ONLY_APPROVAL`

### Data Authority

- **Status**: future local human permission probe approved for exactly five rows; not executed.
- **Rows**: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus` are probe_approved_not_executed with approval_ref null.

### Docs/Ops Governance

- **Status**: D0.4C approval artifacts exist; D0.4D queued as next packet.

### Blocked

- Credential reads, `secret.txt` reads, Codex/subagent login, WRDS execution in D0.4C, discovery, schema, row counts, samples, snapshots, data output, runtime writes, approval_ref changes, formal approval, SafeBoot, and BootReady remain blocked.

## Latest Addendum - V2-D0.4B WRDS Local Auth Method Confirmed

RoundID: `ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED`
ScopeID: `V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION`
Verdict: `WRDS_LOCAL_AUTH_USER_ATTESTED_AVAILABLE; FORMAL_PERMISSION_TRUTH_NOT_CLOSED`

### Data Authority

- **Status**: local auth method is user-attested available, but actual login is not agent-verified and formal permission truth is not closed.
- **Rows**: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus` are `probe_plan_pending`, `not_approved`, and `approval_ref=null`.
- **Must Deliver Next**: separate approval for a local read-only permission probe execution window, or hold.

### Docs/Ops Governance

- **Status**: correction artifacts exist; PM stance is no longer overbroad `provider access blocked`, but remains execution-blocked.
- **Guardrail**: credentials and `secret.txt` are local-only and must not be read, quoted, used, printed, tested, validated, or committed.

### Backend Contracts

- **Status**: no code/runtime change.
- **Allowed**: plan-only local read-only permission probe outline.
- **Blocked**: probe execution until separate approval.

### Blocked

- WRDS login/provider access, SSH, Python WRDS, SAS, SQL, `list_libraries`, `list_tables`, `describe`, schema discovery, row counts, sample rows, SQL logs with provider output, snapshots, data output, runtime/dashboard/scoring/broker writes, row approval, and approval_ref fabrication.

## Latest Addendum - V2-D0.2 WRDS Entitlement Evidence Request

RoundID: `ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST`
ScopeID: `V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST_NO_CREDENTIAL_USE`
Verdict: `REQUEST_PREPARED_EVIDENCE_MISSING`

### Data Authority

- **Status**: evidence request prepared; entitlement evidence still missing.
- **Rows**: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus` remain evidence_missing/pending with approval_ref null.
- **Must Deliver Next**: qualifying non-secret entitlement evidence or explicit decline/hold.

### Docs/Ops Governance

- **Status**: V2-D0.2 request artifacts exist; they are not approval artifacts.
- **Human Handoff**: send the copyable request to an institutional data librarian, WRDS representative, PI, license owner, or data administrator.

### Backend Contracts

- **Status**: no code/runtime change.
- **Guardrail**: no permission matrix row can be promoted without dated attributable evidence and exact approval_ref.

### Blocked

- Account/password use, WRDS/provider access, login, SSH, Python WRDS, SAS, SQL, schema/table discovery, row counts, snapshots, data output, runtime checks, row approval, legacy cleanup, secret remediation, SafeBoot, and BootReady remain blocked.

## Latest Addendum - V2-D0.1 Authorization Intent Evidence Missing

RoundID: `ROUND-20260603-V2-D0-1-AUTHORIZATION-INTENT`
ScopeID: `V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION_INTENT`
Verdict: `BLOCKED_PENDING_EVIDENCE`

### Data Authority

- **Status**: approval intent recorded, but entitlement evidence is missing.
- **Rows**: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus` remain evidence_missing/pending with approval_ref null.
- **Must Deliver Next**: qualifying non-secret entitlement evidence or explicit decline/hold.

### Docs/Ops Governance

- **Status**: authorization-intent packet exists; not final approval.
- **Secret Handling**: `secret.txt` is local secret material and is not non-secret entitlement evidence.

### Backend Contracts

- **Status**: no contract/runtime change in this Worker C round.
- **Guardrail**: existing permission-truth metadata must not promote rows without evidence and approval_ref.

### Quant Research

- **Status**: no PEAD, validity, scoring, or candidate work opened.

### Blocked

- Row approval, WRDS/provider access, credentials use, probe execution, snapshots, data writes, dashboard/runtime work, scoring/ranking, alerts, broker/order paths, legacy cleanup, secret remediation, SafeBoot, and BootReady remain blocked.

## Latest Addendum - V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping

RoundID: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING`
ScopeID: `V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING`
Verdict: `DOCS_BOOKKEEPING_PASS`

### Backend Contracts

- **Status**: `TODO-MATRIX-001` RESOLVED for offline permission-truth metadata.
- **Delivered**: `v2_discovery/data_lab/permission_truth.py` with exact five V2-D0.1 rows pending by default, approval_ref-required approval, and approved-row `allowed_uses=["provenance_contract"]`.
- **Evidence**: focused V2 permission-truth/matrix/snapshot/no-write suite PASS, 51 passed; compileall `v2_discovery\data_lab` plus permission-truth test PASS.

### Data Authority

- **Status**: entitlement and explicit approval text remain missing.
- **Must Deliver Next**: non-secret entitlement evidence and approval refs for `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`, or explicitly decline/hold.

### Quant Research

- **Status**: PEAD starter scope remains separate.
- **Guardrail**: `ibes.det_epsus` is `pending` for V2-D0.1 and `not_requested` for PEAD_V2_001 starter.

### Docs/Ops Governance

- **Status**: current truth/product/spec bookkeeping refreshed for TODO-MATRIX-001 closure.
- **Still Open**: entitlement evidence, explicit approval text, clean-room proof packet, legacy WRDS cleanup, V2 validity/C3 lock, and public/main mismatch.

### Blocked

- WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, BootReady, validity/C3 lock claims, public/main closure, and legacy cleanup actions remain blocked unless separately approved.

## Latest Addendum - V2-D0.1 Scope and Clean-Room Runtime Decision

RoundID: `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME`
ScopeID: `V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION`
Verdict: `ADVISORY_DOCS_PASS`

### Data Authority

- **Status**: V2-D0.1 row request resolved.
- **Must Deliver Next**: non-secret entitlement evidence and approval refs for all five rows: `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus`.

### Quant Research

- **Status**: PEAD starter conflict resolved.
- **Must Deliver Next**: if PEAD packet opens later, use four-row Compustat PEAD starter and mark `ibes.det_epsus=not_requested` in starter scope.

### Architecture / Security

- **Status**: clean-room runtime default resolved.
- **Must Deliver Next**: exclude `schema_registry.py` from credentialed runtime by default; keep as non-credentialed review/source anchor unless explicit exception criteria are met.

### Backend Contracts

- **Status**: matrix metadata gap resolved by `v2_discovery/data_lab/permission_truth.py`.
- **Must Deliver Next**: keep entitlement evidence and approval text gates separate from `TODO-MATRIX-001` closure.

### Blocked

- WRDS/provider access, probe execution, credentials, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, BootReady, and legacy cleanup actions remain blocked.

## Latest Addendum - V2-D0.1 Expert 1-6 Follow-Up Reconciliation

RoundID: `ROUND-20260602-V2-D0-1-EXPERT-1-6-FOLLOWUP`
ScopeID: `V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION`
Verdict: `ADVISORY_DOCS_PASS`

### Data Authority

- **Status**: five-row V2-D0.1 entitlement target accepted.
- **Must Deliver Next**: non-secret table-specific entitlement evidence and approval refs for `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`, or explicitly decline/hold.

### Backend Contracts

- **Status**: `PATCH_RESOLVED_LOCAL`.
- **Must Deliver Next**: future V2-D0.1 permission-truth artifact should use permission matrix only and approved rows should use `allowed_uses=["provenance_contract"]` until separate provider-facing approval exists.
- **Guardrail**: default V2-D0 matrix output is not the approved V2-D0.1 permission-truth artifact unless rows are narrowed through a V2-D0.1 builder or explicit override.

### Architecture / Governance

- **Status**: clean-room probe definition accepted as future gate.
- **Must Deliver Next**: no clean-room probe surface until entitlement evidence and explicit probe approval exist.

### Quant Research

- **Status**: partial agreement due to PEAD starter conflict.
- **Must Deliver Next**: choose I/B/E/S analyst-surprise PEAD vs Compustat-rdq PEAD starter before opening `PEAD_V2_001_BOUNDARY_PACKET`.

### Research Validity

- **Status**: fail-closed thresholds accepted.
- **Must Deliver Next**: `V2_ALPHA_VALIDITY_PACKET` and `C3_LOCK_PEAD_V2_001_v1` before any research-valid claim.

### Security / Ops

- **Status**: approval addendum, audit schema, denylist, and legacy-sequence accepted as future gate.
- **Must Deliver Next**: no legacy rotation/delete/history-scrub/quarantine without explicit security-remediation approval.

### Blocked

- WRDS/provider access, probe execution, credentials, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, BootReady, and legacy cleanup actions remain blocked.

## Latest Addendum - V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates

RoundID: `ROUND-20260602-V2-D0-1-EXPERT-1-6-TODO-GATES`
ScopeID: `V2_D0_1_EXPERT_1_6_AGREEMENT_TODO_GATES`
Verdict: `OFFLINE_CONTRACT_AND_DOCS_PASS`

### Data Authority

- **Status**: entitlement-only gate.
- **Must Deliver Next**: non-secret WRDS entitlement evidence and approval text: account/license owner, account scope, exact library.table permissions, license/access constraints, date/as-of coverage, and approval_ref.
- **Blocked**: provider access, WRDS connection, probe execution, row/sample/schema output, snapshots, data writes, and PIT claims.

### Backend Contracts

- **Status**: row-level validator PATCH_RESOLVED after tests.
- **Must Deliver Next**: keep exact row-key validation and no-write/no-provider contract tests in any future V2-D0.1 proposal.

### Security / Ops

- **Status**: approval text required; legacy WRDS helper/quarantine risk open.
- **Must Deliver Next**: explicit non-secret approval text and a separate audit/retirement decision before any legacy WRDS helper can be trusted.

### Quant Research

- **Status**: conditional only.
- **Must Deliver Next**: `PEAD_V2_001_BOUNDARY_PACKET` only after WRDS/PIT authority is approved.

### Research Validity

- **Status**: blocked for V2 alpha validity claims.
- **Must Deliver Next**: `V2_ALPHA_VALIDITY_PACKET` template before any V2 alpha can claim `research_valid`; currently no V2 alpha is `research_valid`.

### Docs/Ops Governance

- **Status**: current truth refresh and SAW closeout complete.
- **Must Deliver**: planner, bridge, impact, done checklist, multi-stream, post-phase, observability, product/spec, decision, notes, and lessons alignment.

### Blocked

- WRDS/provider access, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker/order paths, SQLite, SafeBoot, and BootReady remain blocked.

## Latest Addendum - V2-D0 Multi-Expert Reconciliation Gate

RoundID: `ROUND-20260602-V2-D0-MULTI-EXPERT-RECONCILIATION`
ScopeID: `MULTI_EXPERT_RECONCILIATION_GATE`
Verdict: `ADVISORY_PASS / PATCH_RESOLVED`
Handover: `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md`

### Data Authority

- **Status**: PASS boundary; probe authorization blocked.
- **Must Deliver Next**: non-secret WRDS entitlement evidence and approval text: account/license owner, account scope, exact library.table permissions, license/access constraints, date/as-of coverage, and approval_ref.
- **Blocked**: any provider access, WRDS connection, credential handling, query, row/sample/schema output, snapshot generation, data write, or PIT claim.

### Backend Contracts

- **Status**: PATCH resolved.
- **Delivered**: strict exact-key probe contract validation, credential/connection/output-like extra-field rejection, dataset row shape validation, and snapshot storage schema parity.
- **Owned Files**:
  - `v2_discovery/data_lab/wrds_probe.py`
  - `v2_discovery/data_lab/snapshot_manifest.py`
  - `tests/test_v2_wrds_permission_matrix.py`
  - `tests/test_v2_snapshot_manifest_contract.py`

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no dashboard reader/runtime integration in this gate.
- **Notes**: If reopened later, it must be separately approved as status-only static-file reading.

### Docs/Ops Governance

- **Status**: reconciliation complete.
- **Must Deliver**: reconciled verdict, SAW report, current truth updates, decision log, notes, lessons, product/spec notices, and context rebuild.

### Blocked

- WRDS/provider access, credential handling, read-only probe execution, PIT snapshot generation, committed WRDS outputs, V1 canonical mutation, dashboard runtime integration, candidate ranking/scoring, recommendations, alerts, broker/order paths, SQLite storage, SafeBoot, and BootReady remain blocked.

## Latest Addendum - V2-D0 WRDS Permission + Snapshot Provenance Contract

RoundID: `ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT`
ScopeID: `V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT`
Policy: `docs/architecture/v2_wrds_data_lab_policy.md`
StartingDecision: `G9 context-only; dashboard reader HOLD; V2-D0 active`

### Backend

- **Status**: contract-only implemented.
- **Must Deliver**: permission matrix, offline probe contract, snapshot manifest contract, schema registry, and focused tests.
- **Owned Files**:
  - `v2_discovery/data_lab/__init__.py`
  - `v2_discovery/data_lab/wrds_probe.py`
  - `v2_discovery/data_lab/permission_matrix.py`
  - `v2_discovery/data_lab/snapshot_manifest.py`
  - `v2_discovery/data_lab/schema_registry.py`

### Data

- **Status**: contract-only; no generated outputs.
- **Must Deliver**: JSON Schema contracts and storage/path guardrails.
- **Owned Files**:
  - `contracts/data_snapshot/wrds_permission_matrix.schema.json`
  - `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no dashboard reader/runtime integration in V2-D0.
- **Notes**: status-only dashboard reader remains a separately approved lane if reopened later.

### Docs/Ops

- **Status**: active closeout.
- **Must Deliver**: policy, handover, current truth surfaces, decision log, notes, lessons, SAW report, closure validation.

### Blocked

- WRDS/provider access, PIT snapshot generation, committed WRDS outputs, V1 canonical data mutation, dashboard runtime integration, candidate ranking/scoring, recommendations, alerts, broker/order paths, SQLite storage, SafeBoot, and BootReady remain blocked.

## Latest Addendum - V2 Alpha Factory Immediate Todo Directive

RoundID: `ROUND-20260601-V2-ALPHA-FACTORY-DIRECTIVE`
ScopeID: `SCOPE-DOCS-ONLY-IMMEDIATE-TODO-FIRSTS`
Packet: `docs/architecture/v2_alpha_factory_immediate_todo_directive_20260601.md`
StartingVerdict: `PASS_DOCS_ONLY`

### Backend

- **Status**: held for planning only.
- **Must Deliver**: no V2 implementation until WRDS/PIT/provenance scope, storage design, and acceptance checks are approved in a clean execution surface.

### Frontend/UI

- **Status**: deferred.
- **Must Deliver**: no dashboard content redesign, recommendations, candidate ranking/scoring, or promotion surface from this directive.

### Data

- **Status**: first active future stream once approved.
- **Must Deliver**: WRDS permission matrix, PIT snapshot plan, provenance schema, manifests, row-count/hash policy, and rollback/removal rules before PEAD/corporate-actions/meta-labeling/Orbis work.

### Docs/Ops

- **Status**: directive intake complete.
- **Must Deliver**: keep directive language distinct from implementation approval and keep local dirty/ignored artifacts out of BootReady truth.

### Blocked

- WRDS/provider access, snapshot generation, SQLite storage, candidate ranking/scoring, promotion claims, live trading, broker/order execution, alerts, autonomous allocation, boot-status edits, and BootReady claims remain blocked until explicit approval.

## Latest Addendum - Governed Data Source Provenance Intake

RoundID: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`
ScopeID: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`
Packet: `docs/architecture/governed_data_source_provenance_intake_20260528.md`
StartingVerdict: `BLOCK`

### Backend

- **Status**: held.
- **Must Deliver**: no boot preflight patch, no data-readiness weakening, no runtime writer, no generation during boot, and no BootReady claim.

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no dashboard/runtime generation approval and no SafeBoot or BootReady copy change.

### Data

- **Status**: blocked until raw/source provenance is approved.
- **Must Deliver**: approve source location, owner/approval, date/as-of coverage, license/access note, schema, generator command, output path, manifest path, SHA256 policy, validation command, and rollback/removal rule for prices, tickers/security master, WRDS/R3000 membership, and Rule100 history.
- **Gate Truth**: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.

### Docs/Ops

- **Status**: source-provenance intake packet and current-truth refresh only.
- **Must Deliver**: keep local artifacts, runtime boot status, and ignored data classified as not commit evidence.

### Blocked

- no boot_preflight.py patch; no DataReadyStrict weakening; no data/processed generation from incomplete provenance; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.

## Latest Addendum - Governed Data Source Acquisition / Bounded Regeneration Planning

RoundID: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`
ScopeID: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`
Packet: `docs/architecture/governed_data_source_acquisition_20260528.md`
StartingVerdict: `BLOCK`

### Backend

- **Status**: held.
- **Must Deliver**: no boot preflight patch, no data-readiness weakening, no runtime writer, no generation during boot, and no BootReady claim.

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no dashboard/runtime generation approval and no SafeBoot or BootReady copy change.

### Data

- **Status**: blocked until source approval.
- **Must Deliver**: choose trusted external governed bundle, or approve source acquisition + bounded offline regeneration planning for `prices.parquet`, `prices_tri.parquet`, `tickers.parquet`, `universe_r3000_daily.parquet`, and `rule100_softmax_v1_history.csv`.
- **Gate Truth**: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.

### Docs/Ops

- **Status**: source-acquisition planning packet and current-truth refresh only.
- **Must Deliver**: keep local artifacts, runtime boot status, and ignored data classified as not commit evidence.

### Blocked

- no boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.

## Latest Addendum - Governed Data Artifact Authorization

RoundID: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`
ScopeID: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`
Packet: `docs/architecture/governed_data_artifact_authorization_20260528.md`

### Backend

- **Status**: held.
- **Must Deliver**: no `boot_preflight.py` patch, no DataReadyStrict weakening, no runtime code change, and no BootReady claim.

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no dashboard/runtime change and no SafeBoot or BootReady copy change.

### Data

- **Status**: blocked until authorization.
- **Must Deliver**: approve bounded offline regeneration or approved external bundle for `data/processed/prices_tri.parquet`, `data/processed/prices.parquet`, `data/processed/tickers.parquet`, `data/processed/universe_r3000_daily.parquet`, and `data/processed/rule100_softmax_v1_history.csv`.
- **Gate Truth**: GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS/degraded; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.

### Docs/Ops

- **Status**: authorization packet and current-truth refresh only.
- **Must Deliver**: keep local artifacts and dirty context classified as not clean GitHub truth or BootReady evidence.

### Blocked

- no boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.

## Latest Addendum - Portfolio Replay Role Contract

### Backend/Strategy

- **Status**: replay, context, and artifact schemas now include `context_role` and `row_role`.
- **Must Deliver**: keep `normalize_context_frame_for_replay(...)` as the single normalization authority and keep legacy artifact role hydration backward-compatible.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`

### Frontend/UI

- **Status**: Portfolio tables render role-aware labels and dashboard context normalization delegates to backend/strategy.
- **Must Deliver**: do not reintroduce generic replay `Weight` labels or private dashboard context-normalization logic.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`
  - `tests/test_dash_1_page_registry_shell.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: no canonical data write; diagnostics are generated from the existing `DashboardReplayContext`.
- **Must Deliver**: diagnostic artifacts must include run/source/method/cache identity and must not rebuild replay.

### Docs/Ops

- **Status**: product/spec surfaces, phase brief, notes, decision log, lessons, and context packets record the role contract.
- **Must Deliver**: run SAW gate before claiming closure.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, strategy promotion, and diagnostic-triggered replay rebuilds remain blocked.

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

### Backend/Strategy

- **Status**: selected-method replay context normalization now exposes replay-derived `target_weight` for aux rows while retaining legacy `weight` as audit metadata.
- **Must Deliver**: keep daily replay rows as the only target-weight authority for event/decision display semantics.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`

### Frontend/UI

- **Status**: Portfolio Strategy Replay surfaces align saved/transitional aux rows to replay target weights and timeline displays stacked allocation composition.
- **Must Deliver**: keep partial saved/transitional schemas fail-soft, keep timeline display-only, and retain executable Plotly trace coverage for stacked allocation semantics.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added; saved-artifact schema compatibility is preserved through existing selected-method replay artifact columns.
- **Must Deliver**: legacy aux weight remains audit-only and must not override replay target weights.

### Docs/Ops

- **Status**: notes, decision log, product/spec surfaces, phase brief, lessons, and current truth surfaces record the replay-weight invariant and SAW reconciliation.
- **Must Deliver**: keep aux-weight and partial-schema regressions in focused verification.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, strategy promotion, and durable saved-artifact superset/subset policy remain blocked.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

### Backend/Strategy

- **Status**: backend replay/context filtering remains strict to replay rows; no strategy engine semantic change.
- **Must Deliver**: keep context normalization tied to replay tickers and do not add a separate lifecycle-history display source.

### Frontend/UI

- **Status**: dashboard replay request assets now expand from signed current assets to horizon-aware context assets when in-window lifecycle/history tickers exist; selected PIT loading still uses current-only allocation assets.
- **Must Deliver**: keep current allocation signed-current-only while replay history uses zero-weight context-only rows in the widened bundle.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added; ticker-to-permno mapping uses loaded local ticker map and price columns.
- **Must Deliver**: unresolved or unpriced history tickers remain excluded; full PIT membership rows must not leak through coverage pre-gate into dashboard replay evidence.

### Docs/Ops

- **Status**: notes, decision log, lesson, phase brief, and current truth surfaces record the current-allocation vs horizon-history split.
- **Must Deliver**: keep MU regression coverage in focused verification.

### Blocked

- Current-allocation universe widening, durable saved-artifact horizon supersets/subsets, provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

### Backend/Strategy

- **Status**: batched selected-method replay input loading preserves full PIT membership proof and shrinks only price/return loading for selected permnos.
- **Must Deliver**: keep membership proof and replay asset selection separate; do not let selected-price narrowing become watchlist-only replay.
- **Owned Files Referenced**:
  - `core/data_orchestrator.py`
  - `dashboard.py`
  - `tests/test_data_orchestrator_portfolio_runtime.py`
  - `tests/test_optimizer_view.py`

### Frontend/UI

- **Status**: dashboard passes signed numeric replay assets into the cached batched PIT loader while retaining signed-selection validation and final asset filtering.
- **Must Deliver**: keep replay request construction signed-selection driven and fail-closed when selection is unavailable.

### Data

- **Status**: MU/SNDK trace shows both names are pinned, mapped, PIT-present on latest replay date, and locally priced; latest exclusions are downstream gates, not missing local data.
- **Must Deliver**: investigate Rule100 candidate/history inclusion separately if requested.
- **Owned Files Referenced**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Docs/Ops

- **Status**: product/spec/notes/decision/lesson/phase/context surfaces record the two-track boundary and local evidence path.
- **Must Deliver**: preserve the "not watchlist-only" boundary in future replay performance work.

### Blocked

- Watchlist-only replay, provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

### Backend/Strategy

- **Status**: no backend replay engine or saved artifact reader change in this frontend cache repair.
- **Must Deliver**: keep saved-artifact acceptance exact until a separate superset/subset policy is designed and tested.

### Frontend/UI

- **Status**: `_ensure_daily_portfolio_replay_context(...)` now reuses a wider ready in-session daily replay for shorter covered horizons before rebuilding.
- **Must Deliver**: prove non-date replay identity and actual requested-date row coverage before reuse; return a horizon-scoped context.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added.
- **Must Deliver**: maintain PIT source semantics and signed-asset filtering; no provider ingestion or canonical write.

### Docs/Ops

- **Status**: notes, decision log, phase brief, and current truth surfaces record the in-session-only superset reuse rule.
- **Must Deliver**: keep superset-cache regressions in focused verification.

### Blocked

- Durable saved-artifact superset/subset reads, provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Max Replay Timeline Sampling Fix

### Backend/Strategy

- **Status**: no backend replay engine changes in this frontend display repair.
- **Must Deliver**: keep daily replay rows as the source for display sampling.

### Frontend/UI

- **Status**: max-window Strategy Replay Timeline sampling now normalizes grouped weekly date Series correctly.
- **Must Deliver**: keep sampled rows display-only and out of Portfolio Performance.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added.
- **Must Deliver**: no sampled replay artifact or canonical market-data write is created by timeline display sampling.

### Docs/Ops

- **Status**: notes, decision log, phase brief, lesson, and current truth surfaces record the max-window sampler fix.
- **Must Deliver**: keep the long-window regression in focused verification.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

### Backend/Strategy

- **Status**: no backend reader internals changed in this frontend repair.
- **Must Deliver**: backend producers still need to emit `dashboard_cache_signature` for production saved-artifact UI hits.

### Frontend/UI

- **Status**: saved-artifact adapter now preserves artifact event/decision rows exactly, including empty frames.
- **Must Deliver**: keep `source_mode="saved_artifact"` artifact-owned for replay rows, latest snapshot, event rows, and decision rows.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added.
- **Must Deliver**: empty artifact event/decision row sets remain valid saved evidence and must not be mixed with direct fallback frames.

### Docs/Ops

- **Status**: Frontend/UI saved replay source-selector SAW report is mirrored to `docs/saw_reports/`.
- **Must Deliver**: keep the single-source aux-surface regression and report path discoverable from current truth surfaces.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Backend Replay Reader Identity Hardening

### Backend/Strategy

- **Status**: saved replay manifest identity now rejects blank `run_id`, `source_id`, and `method_id` before optional expected-ID checks.
- **Must Deliver**: keep manifest identity validation ahead of parquet equality, context matching, and bundle reconstruction.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`

### Frontend/UI

- **Status**: no dashboard runtime changes in this backend hardening slice.
- **Must Deliver**: keep requiring exact `dashboard_cache_signature` before saved-artifact UI consumption can replace the labeled transitional fallback.

### Data

- **Status**: blank manifest+parquet identity now fails closed instead of reconstructing replay evidence.
- **Must Deliver**: selected-method replay artifacts must carry non-empty run/source/method identity and remain display-only evidence under runtime cache.

### Docs/Ops

- **Status**: backend SAW report published at `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`.
- **Must Deliver**: keep the prior reader/budget closure auditable from `docs/saw_reports/` and current truth surfaces.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Overlay Overlap Anchor Fix

### Backend/Strategy

- **Status**: scaled overlay helper now requires same-column local/live overlap.
- **Must Deliver**: do not add a permissive no-overlap evidence mode.

### Frontend/UI

- **Status**: selected-price and benchmark YTD evidence drops unanchored stale live overlays.
- **Must Deliver**: keep UI captions tied to available/dropped evidence rather than synthetic continuity.

### Data

- **Status**: live overlay remains display-only and non-canonical.
- **Must Deliver**: stale local ending dates cannot be scaled to fresh live rows without a same-ticker anchor date.

### Docs/Ops

- **Status**: SAW Implementer and Reviewer A/B/C all passed.
- **Must Deliver**: carry adjacent replay/YTD session-state advisory as future hygiene only.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

### Backend/Strategy

- **Status**: `PriceEndpointFreshness` snapshot and snapshot-aware endpoint helpers implemented.
- **Must Deliver**: keep endpoint snapshot as a reuse/performance layer only; freshness policy remains explicit and fail-closed.
- **Owned Files Referenced**:
  - `core/data_orchestrator.py`
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: dashboard and optimizer view consume a cached endpoint snapshot for YTD, selected-price prep, and default ordering.
- **Must Deliver**: do not reintroduce render-path full-matrix scans when adding new Portfolio & Allocation consumers.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `views/optimizer_view.py`

### Data

- **Status**: local matrix endpoint measurement recorded; no data writes performed.
- **Must Deliver**: preserve exact endpoint semantics for finite positive price values; NaN/inf/zero remain non-endpoints.

### Docs/Ops

- **Status**: truth surfaces updated; SAW implementer PASS received and reviewer reconciliation pending.
- **Must Deliver**: publish final SAW PASS/BLOCK for this performance slice before claiming governance closure.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

### Backend/Strategy

- **Status**: endpoint freshness helpers, shared tolerance predicate, and universe endpoint gate implemented.
- **Must Deliver**: keep history count separate from endpoint freshness; stale endpoints remain ineligible until refreshed unless an explicit policy tolerance permits them.
- **Owned Files Referenced**:
  - `core/data_orchestrator.py`
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: dashboard YTD and optimizer view now fail closed/drop stale selected assets instead of presenting stale columns as current.
- **Must Deliver**: keep captions and metrics tied to assets that pass endpoint checks.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `views/optimizer_view.py`

### Data

- **Status**: live overlay remains display-only and non-canonical.
- **Must Deliver**: endpoint/tolerance semantics stay centralized in `core.data_orchestrator`; unresolved stale columns must be dropped/unavailable rather than forward-filled; scaled overlays require same-column local/live overlap before live rows can become allocation or benchmark evidence.

### Docs/Ops

- **Status**: docs/truth surfaces refreshed; independent SAW Implementer and Reviewer A/B/C rerun completed PASS.
- **Must Deliver**: carry saved replay artifact-reader consumption and explicit performance-budget work as separate future scope.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

### Backend/Strategy

- **Status**: backend selected-method bundle consumer verified through dashboard transitional build.
- **Must Deliver**: keep `build_selected_method_replay(...)` as the only selected-method replay bundle API for dashboard replay consumption.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`

### Frontend/UI

- **Status**: dashboard consumption verified with full pytest and runtime smoke.
- **Must Deliver**: keep `_build_dashboard_strategy_replay_context(...)` wired to `build_selected_method_replay(...)` with `_dashboard_input_loader`; saved artifact-reader consumption remains future work.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_position_lifecycle.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: PIT input-loader boundary verified for dashboard bundle consumption.
- **Must Deliver**: maintain `end_date=as_of_date` and `universe_mode="r3000_pit"` for dashboard replay inputs.

### Docs/Ops

- **Status**: stale open-risk text refreshed; runtime smoke and full pytest evidence captured.
- **Must Deliver**: keep saved artifact-reader/performance-budget work separate from verified transitional bundle consumption.

### Blocked

- Provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Replay Coverage Contract Audit Fix

### Backend/Strategy

- **Status**: audit fix implemented and full pytest PASS.
- **Must Deliver**: preserve batched uncovered-date emission, row-heavy unavailable fast rows, next-tradable-return performance alignment, run-level loader equity, small-frame performance lookup, and inverse-volatility bound-feasible diagnostics fast path.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `strategies/optimizer.py`
  - `tests/test_strategy_replay_coverage.py`
  - `tests/test_optimizer_core_policy.py`

### Frontend/UI

- **Status**: no UI behavior changed in this audit fix.
- **Must Deliver**: dashboard backend-bundle consumption/runtime smoke are now verified; saved artifact-reader consumption remains future work.

### Data

- **Status**: replay coverage reasons, segments, PIT return alignment, and row-heavy unavailable performance are now preserved in tested outputs.
- **Must Deliver**: keep uncovered dates explicit as `input_unavailable:*` / `cash_closed`, never stale carry-forward.

### Docs/Ops

- **Status**: docs and context surfaces refreshed for the audit fix.
- **Must Deliver**: keep `current_context.*` bootstrapped from the latest current truth packet, and carry saved artifact-reader/performance-budget work as open phase-close work.

### Blocked

- Provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

### Backend/Strategy

- **Status**: focused implementation passed.
- **Must Deliver**: keep `build_selected_method_replay(...)` as the backend selected-method replay bundle API, preserve shared `REPLAY_COLUMNS`, CASH rows, context filtering, and performance fields, and keep `write_selected_method_replay_artifact_atomic(...)` rollback-safe for parquet+manifest evidence.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`
  - `tests/test_replay_non_cash_closed.py`

### Frontend/UI

- **Status**: implementation verified with backend bundle consumption, full pytest, and runtime smoke.
- **Must Deliver**: keep `DashboardReplayContext` as the dashboard context for Strategy Replay rows, latest snapshot, annotations, Buy/Sell rows, and YTD latest-weight preference; keep saved artifact-reader consumption separate until approved.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_position_lifecycle.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: PIT rule and durable artifact writer locked.
- **Must Deliver**: every replay date uses `end_date=as_of_date` and `universe_mode="r3000_pit"`; failed or empty dates must emit explicit `cash_closed` context; saved replay evidence stays under `data/runtime_cache/strategy_replay` with run id and manifest metadata.

### Docs/Ops

- **Status**: evidence handoff refreshed after dashboard backend-bundle integration, full regression, and runtime smoke passed.
- **Must Deliver**: keep saved artifact-reader consumption and performance-budget risks visible until separately implemented and tested.

### Blocked

- Saved-evidence PASS claims without dashboard backend-bundle traceability, stale carry-forward, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims without same-window/same-cost/same-engine deltas remain blocked.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

### Backend/Strategy

- **Status**: pending implementation approval.
- **Must Deliver**: selected-method adapters call one shared replay run/source and return a run/artifact identifier instead of independent UI/YTD computations.
- **Owned Files**: TBD by implementation worker; Worker 3 makes no code edits.

### Frontend/UI

- **Status**: pending implementation approval.
- **Must Deliver**: Portfolio & Allocation YTD, latest allocation snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log must render from the same selected-method replay source.
- **Owned Files**: TBD by implementation worker; current bridges remain transitional.

### Data

- **Status**: pending implementation approval.
- **Must Deliver**: saved evidence artifact records run id, method id, input signatures, date window, costs, baseline id, row/status counts, and timing.
- **Owned Files**: TBD by implementation worker.

### Docs/Ops

- **Status**: guardrail refreshed; docs-only SAW report maintained.
- **Must Deliver**: keep the invariant and performance budget in the done checklist until implementation proves it.

### Blocked

- Second replay stacks, stale allocation carry-forward, fake improvement claims, overfit promotion, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and unlabeled transitional bridges remain blocked.

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

### Backend/Strategy

- **Status**: implemented; focused and full tests PASS.
- **Must Deliver**: Rule100 visible allocation and Strategy Replay derive per-name budget and cap from `controls.max_weight` through `rule100_config_from_max_weight(...)`.
- **Owned Files**:
  - `strategies/rule100_softmax.py`
  - `strategies/strategy_replay.py`
  - `tests/test_rule100_softmax.py`
  - `tests/test_strategy_replay.py`

### Frontend/UI

- **Status**: implemented; direct UI and Strategy Replay agreement tests PASS.
- **Must Deliver**: direct Rule100 UI passes `controls.max_weight` into the softmax path and never rewrites frozen history to make current UI targets appear historical.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `dashboard.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: implemented; stale-aware benchmark behavior tests PASS.
- **Must Deliver**: benchmark freshness is evaluated per ticker; stale/missing QQQ can be live-overlaid while fresh SPY stays local, and stale columns are dropped if overlay fails.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Docs/Ops

- **Status**: refreshed; SAW PASS.
- **Must Deliver**: preserve the boundary that frozen Rule100 history/audit defaults remain 10%/15% unless a separate versioned/labeled UI-policy artifact is approved.

### Blocked

- Frozen history rewrite, canonical provider ingestion, benchmark backfill promotion, alerts, broker behavior, live trading, ranking/scoring, and new optimizer objectives remain blocked.

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

### Backend/Strategy

- **Status**: implemented; focused and affected tests PASS.
- **Must Deliver**: `build_strategy_replay(...)` consumes `StrategyReplayInputs` from the dashboard path; target-weight output is generated from per-date PIT slices.
- **Owned Files**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`

### Frontend/UI

- **Status**: implemented; source guards PASS.
- **Must Deliver**: Portfolio & Allocation Strategy Replay loads one PIT input per replay date and no longer passes raw `prices_wide[replay_assets]`.
- **Owned Files**:
  - `dashboard.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_position_lifecycle.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: implemented; path/signature guards PASS.
- **Must Deliver**: cache signatures require `r3000_pit`; repo-local replay input artifacts stay under `data/runtime_cache/strategy_replay`.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_data_orchestrator_portfolio_runtime.py`
  - `tests/test_strategy_replay_artifact.py`

### Docs/Ops

- **Status**: refreshed.
- **Must Deliver**: keep explicit boundary that input artifacts are not replay output artifacts.

### Blocked

- Target-weight artifact persistence, provider ingestion, canonical market-data writes, alerts, broker behavior, live trading, ranking/scoring, and new optimizer objectives remain blocked.

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: v1.1 factor strength and coverage use approved groups with neutral missing-value shrinkage.
- **Owned Files**:
  - `strategies/rule100_softmax_v1_1.py`
  - `tests/test_rule100_softmax_v1_1.py`

### Frontend/UI

- **Status**: implemented; real dashboard AppTest PASS.
- **Must Deliver**: Policy Target Timeline proof uses `AppTest.from_file("dashboard.py")`, not copied mini-app code.
- **Owned Files**:
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: refreshed; stale artifact retired.
- **Must Deliver**: v1.1 active artifacts are comparison CSV and summary JSON only; no active v1.1 history CSV.

### Docs/Ops

- **Status**: refreshed.
- **Must Deliver**: carry boundary that v1.1 is research-only and not promoted runtime sizing.

### Blocked

- v1.1 runtime promotion, recreated v1.1 history, lifecycle log mutation, broker behavior, alerts, provider ingestion, ranking/scoring, and new optimizer objectives remain blocked.

## Latest Addendum - Rule of 100 Method Label

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: softmax v1 history overlay uses the same sizing helper as current UI and does not fork Kelly into a second stack.
- **Owned Files**:
  - `scripts/rule100_softmax_v1_audit.py`
  - `tests/test_rule100_softmax.py`

### Frontend/UI

- **Status**: implemented; renderer source guard PASS.
- **Must Deliver**: transaction history distinguishes immutable event weights from derived softmax v1 targets.
- **Owned Files**:
  - `dashboard.py`
  - `tests/test_position_lifecycle.py`

### Data

- **Status**: implemented; artifact regenerated.
- **Must Deliver**: `data/processed/rule100_softmax_v1_history.csv` is additive and must not overwrite `data/portfolio_lifecycle_log.jsonl`.

### Docs/Ops

- **Status**: refreshed.
- **Must Deliver**: carry boundary that v0 event ledger and v1 target overlay are separate audit surfaces.

### Blocked

- Lifecycle log mutation, broker behavior, alerts, provider ingestion, ranking/scoring, new optimizer objective, and Kelly stack expansion remain blocked.

## Previous Addendum - Rule of 100 Method Label

### Backend/Strategy

- **Status**: implemented; focused registry tests PASS.
- **Must Deliver**: `Rule of 100` method label exists without becoming a mean-variance optimizer objective.
- **Owned Files**:
  - `strategies/optimizer.py`
  - `tests/test_portfolio_universe.py`

### Frontend/UI

- **Status**: implemented; focused AppTest PASS.
- **Must Deliver**: selecting `Rule of 100` renders Rule100 softmax v1 target weights plus residual cash and bypasses cached optimizer execution.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `tests/test_optimizer_view.py`

### Data

- **Status**: unchanged.
- **Must Deliver**: continue using PIT current lifecycle holds as the softmax candidate source; no provider ingestion or canonical data writes.

### Docs/Ops

- **Status**: context and spec surfaces refreshed; runtime manual audit PASS on port 8509.
- **Must Deliver**: record that the label is softmax sizing over lifecycle holds, not a new optimizer objective.

### Blocked

- New optimizer objective, ranking, scoring, broker behavior, alerting, provider ingestion, live trading, and generic strategy framework remain blocked.

## Latest Addendum - Rule100 Lifecycle Policy v0

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: concrete Rule100 lifecycle v0, not a generic replay framework.
- **Owned Files**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Data

- **Status**: v0 runtime and audit artifacts promoted.
- **Must Deliver**: 29-event runtime replay, v0 decision tape, baseline comparison.
- **Owned Files**:
  - `data/portfolio_lifecycle_log.jsonl`
  - `data/portfolio_lifecycle_decision_log.jsonl`
  - `data/portfolio_lifecycle_buy_sell_log.jsonl`
  - `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

### Frontend/UI

- **Status**: unchanged; focused portfolio tests PASS.
- **Must Deliver**: dashboard remains compatible with ENTER/EXIT runtime lifecycle log and must not render TRIM/TIGHTEN as live recommendations.

### Docs/Ops

- **Status**: docs/context updates in progress; SAW remains BLOCK without independent subagent passes.
- **Must Deliver**: carry Rule100 proxy/literal-column limitation and audit-only TRIM/TIGHTEN boundary.

### Blocked

- Generic replay framework, provider ingestion, canonical writes, broker orders, alerts, ranking, scoring, dashboard action-label changes, Phase 54 Rule-of-100 sleeve reopen, and live trading remain blocked.

## Latest Addendum - Lifecycle Decision Export

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: export-only PIT decision tape that matches replay events and preserves reason codes.
- **Owned Files**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Data

- **Status**: analysis artifacts published.
- **Must Deliver**: full decision JSONL, compact buy/sell JSONL, and audit summary.
- **Owned Files**:
  - `data/portfolio_lifecycle_decision_log.jsonl`
  - `data/portfolio_lifecycle_buy_sell_log.jsonl`
  - `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

### Frontend/UI

- **Status**: unchanged.
- **Must Deliver**: no UI action-label change; dashboard continues to render ENTER/EXIT lifecycle vocabulary.

### Docs/Ops

- **Status**: docs/context updates in progress; SAW remains BLOCK without independent subagent passes.
- **Must Deliver**: carry export as audit-only until user approves policy implementation.

### Blocked

- Broker orders, alerts, recommendations, ranking, scoring, provider ingestion, canonical writes, dashboard action-label changes, and full execution-ledger semantics remain blocked.

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: replay ENTER sizing, PIT factor confirmation, entry/exit confirmation, cooldown, and CLI repeatability.
- **Owned Files**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Data

- **Status**: final replay published to runtime JSONL after evidence verification.
- **Must Deliver**: open current holds must reflect lifecycle state, not full-cash fallback.
- **Owned Files**:
  - `data/portfolio_lifecycle_log.jsonl`
  - `docs/context/e2e_evidence/optimal_lifecycle_replay_tmp.jsonl`

### Frontend/UI

- **Status**: implemented; reboot/browser smoke PASS on port 8509.
- **Must Deliver**: Portfolio & Allocation shows lifecycle holds plus residual cash, not 100% cash.

### Docs/Ops

- **Status**: docs/context updates and context validation complete; closure/SAW handling in progress.
- **Must Deliver**: closure/SAW handling.

### Blocked

- Phase 54 Rule-of-100 sleeve reopen, ranking, scoring, optimizer objective changes, provider ingestion, canonical writes, broker calls, alerts, conviction mode, Black-Litterman, and live trading remain blocked.

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

### Backend

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: PIT-safe lifecycle open-position reconstruction and lifecycle-first current position memory.
- **Owned Files**:
  - `data/portfolio_lifecycle_log.py`
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: no-fresh-PIT-ENTER with open lifecycle holds renders holds plus residual cash instead of 100% cash.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `dashboard.py`

### Docs/Ops

- **Status**: SAW PASS; context validation and validator checks complete.
- **Must Deliver**: carry Low stale-lock recovery and inherited execution-ledger limits as future follow-ups.

### Blocked

- Provider ingestion, canonical writes, execution ledger, broker calls, alerts, ranking, scoring, conviction mode, Black-Litterman, and new optimizer objectives remain blocked.

## Latest Addendum - Frontend 3-Page Navigation Refactor

### Frontend/UI

- **Status**: implemented; 24 DASH tests + 70 broader tests PASS.
- **Must Deliver**: 3-page navigation model (Portfolio & Allocation, Discovery & Analysis, Entry/Exit Strategy) replacing 8-page shell.
- **Owned Files**:
  - `dashboard.py`
  - `views/page_registry.py`
  - `views/discovery_view.py`
  - `views/strategy_view.py`
  - `tests/test_dash_1_page_registry_shell.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Backend

- **Status**: no changes.
- **Must Deliver**: N/A.

### Docs/Ops

- **Status**: truth surfaces updated.
- **Must Deliver**: multi-stream contract addendum, planner packet refresh.

### Blocked

- Provider ingestion, canonical writes, scanner semantic changes, strategy search, ranking, scoring, alerts, brokers, optimizer objective changes, and candidate-card dashboard merge.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

### Frontend/UI

- **Status**: dashboard unified parquet package load is cached across Streamlit reruns; full pytest and SAW PASS.
- **Must Deliver**: keep top-level dashboard load responsive without changing page behavior or data authority.
- **Owned Files**:
  - `dashboard.py`
  - `tests/test_dashboard_sprint_a.py`

### Data/Ops

- **Status**: source parquet cache signature implemented and tested.
- **Must Deliver**: invalidate cached package when relevant processed/static parquet source files are added, removed, or rewritten.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_data_orchestrator_portfolio_runtime.py`

### Docs/Ops

- **Status**: bridge, impact, done checklist, planner packet, notes, decision log, lessons, SAW report, post-phase alignment, and observability pack updated.
- **Must Deliver**: carry mutable `st.cache_resource` residual risk as a future dashboard-owner guardrail.

### Blocked

- Provider ingestion, canonical market-data writes, alpha-engine loop rewrite, scanner financial-statement cache, scanner semantic changes, ranking, scoring, alerts, brokers, optimizer objective changes, and candidate-card dashboard merge.

## Latest Addendum - Dashboard Scanner Testability Hardening

### Backend/Strategy

- **Status**: scanner formula extraction implemented; focused tests PASS.
- **Must Deliver**: deterministic scanner math must be importable and tested outside Streamlit.
- **Owned Files**:
  - `strategies/scanner.py`
  - `tests/test_scanner.py`

### Frontend/UI

- **Status**: dashboard provider/cache/persistence boundary preserved; enrichment delegates to strategy module.
- **Must Deliver**: no dashboard product redesign or semantic expansion inside this testability lane.
- **Owned Files**:
  - `dashboard.py`

### Data/Ops

- **Status**: ETL/config/process guardrail coverage added or preserved; focused tests PASS.
- **Must Deliver**: keep canonical market-data writes and provider ingestion blocked.
- **Owned Files**:
  - `core/etl.py`
  - `tests/test_core_etl.py`
  - `tests/test_process_utils.py`

### Blocked

- Provider ingestion, canonical writes, scanner semantic changes, strategy search, ranking, scoring policy changes, alerts, brokers, dashboard redesign, and candidate-card dashboard merge.

## Latest Addendum - Dashboard Architecture Safety Slice

### Backend/Ops

- **Status**: shared process liveness helper implemented; focused tests PASS.
- **Must Deliver**: Windows-safe PID liveness and fail-closed backtest spawn behavior for live PID files.
- **Owned Files**:
  - `utils/process.py`
  - `data/updater.py`
  - `scripts/parameter_sweep.py`
  - `scripts/release_controller.py`
  - `backtests/optimize_phase16_parameters.py`

### Frontend/UI

- **Status**: dashboard helper cleanup implemented; focused tests PASS.
- **Must Deliver**: one strategy matrix initializer and canonical portfolio price cleanup delegation.
- **Owned Files**:
  - `dashboard.py`

### Docs/Ops

- **Status**: docs/context updated; independent SAW Implementer and Reviewer A/B/C passes complete.
- **Must Deliver**: longer full-regression window only if phase-close proof is requested.

### Blocked

- Provider ingestion, canonical writes, dashboard redesign, strategy search, ranking, scoring, alerts, brokers, and candidate-card dashboard merge.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

### Backend

- **Status**: display-only overlay cache and optimizer-run cache implemented; focused tests PASS.
- **Must Deliver**: non-canonical Parquet cache, background refresh scheduling, atomic temp->replace cache writes, copy-safe overlay scaling cache.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_optimizer_view.py`

### Frontend/UI

- **Status**: optimizer render path reconciled and AppTest coverage added; focused tests PASS.
- **Must Deliver**: view render coverage, mean-variance dropdown coverage, sector-cap control coverage, cached optimizer reruns.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `tests/test_optimizer_view.py`

### Docs/Ops

- **Status**: docs/context refreshed; runtime smoke, full/focused validation, and SAW PASS complete.
- **Must Deliver**: completed for this hardening round; future work may address Low executor-submit containment and background-refresh diagnostics.

### Blocked

- Canonical provider ingestion, market-data writes, optimizer objective changes, lower-bound policy, MU conviction, WATCH investability, Black-Litterman, alerts, brokers, ranking, scoring, and candidate-card dashboard merge.

## Latest Addendum - Portfolio Data Boundary Refactor

### Backend

- **Status**: data-boundary refactor implemented; focused tests PASS.
- **Must Deliver**: selected-stock display overlay fetching, local TRI scaling/stitching, and strategy metrics parsing in `core/data_orchestrator.py`.
- **Owned Files**:
  - `core/data_orchestrator.py`

### Frontend/UI

- **Status**: optimizer view consumes orchestrator helpers; focused tests PASS.
- **Must Deliver**: no direct yfinance import and no direct `data/backtest_results.json` parsing in `views/optimizer_view.py`.
- **Owned Files**:
  - `views/optimizer_view.py`

### Docs/Ops

- **Status**: data-boundary docs/context refresh and SAW PASS complete.
- **Must Deliver**: completed for that architecture hygiene round.

### Blocked

- Canonical provider ingestion, market-data writes, optimizer objective changes, MU conviction, WATCH investability, Black-Litterman, alerts, brokers, ranking, scoring, and candidate-card dashboard merge.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

### Backend

- **Status**: diagnostics implemented; focused tests PASS.
- **Must Deliver**: structured diagnostics module, diagnostic-returning optimizer methods, no objective/policy expansion.
- **Owned Files**:
  - `strategies/optimizer_diagnostics.py`
  - `strategies/optimizer.py`

### Frontend/UI

- **Status**: diagnostics UI implemented; focused tests PASS.
- **Must Deliver**: optimizer status, feasibility, active constraints, max-cap/lower-bound assets, equal-weight forced status, and fallback labels.
- **Owned Files**:
  - `views/optimizer_view.py`

### Docs/Ops

- **Status**: final validation and SAW PASS complete.
- **Must Deliver**: completed for that diagnostics round.

### Blocked

- MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new objective, scanner changes, manual override, providers, alerts, brokers, and replay behavior.

## Latest Addendum - Optimizer Core Policy Audit

### Backend

- **Status**: audit-only; no implementation changes.
- **Must Deliver**: optimizer constraints policy, lower-bound/SLSQP audit, and focused policy tests.

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no new active-bound UI until optimizer-core diagnostics are approved.

### Docs/Ops

- **Status**: active SAW closeout.
- **Must Deliver**: audit docs, tests, SAW report, closure/evidence validation.

### Blocked

- Runtime lower-bound support, conviction mode, WATCH investability, Black-Litterman, scanner changes, universe eligibility changes, providers, alerts, and brokers.

## Latest Addendum - Portfolio Universe Quarantine Closure

### Backend

- **Status**: universe fix PASS; optimizer-core diff quarantined.
- **Must Deliver**: no active `strategies/optimizer.py` diff in this closure.
- **Owned Files**:
  - `strategies/portfolio_universe.py`
  - `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`

### Frontend/UI

- **Status**: implemented, focused/browser checks PASS.
- **Must Deliver**: Universe Audit, fail-closed messaging, YTD below optimizer, no optimizer-core math acceptance.

### Docs/Ops

- **Status**: PASS closeout.
- **Must Deliver**: SAW PASS, quarantine note, current truth-surface refresh, separate optimizer audit branch when opened.

### Blocked

- Optimizer lower-bound/SLSQP policy, MU conviction mode, WATCH investability, Black-Litterman, thesis anchors, manual override, scanner rewrite, provider ingestion, alerts, and broker calls remain blocked.

## Latest Addendum - Portfolio Universe Construction Fix

### Backend

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: explicit optimizer universe builder, eligibility policy, ticker-map readiness, price-history readiness, max-weight feasibility diagnostics.
- **Owned Files**:
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: Universe Audit, Why This Allocation, thesis-neutral optimizer labels, no display-order default leakage.
- **Owned Files**:
  - `dashboard.py`
  - `views/optimizer_view.py`

### Docs/Ops

- **Status**: active-final-refresh.
- **Must Deliver**: portfolio construction contract, decision/notes/lessons/truth-surface updates, SAW report.

### Blocked

- MU hard floor, conviction mode, Black-Litterman, thesis anchors, manual override, scanner rewrite, provider ingestion, alerts, and broker calls remain blocked.

## Header

- `CONTRACT_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-streams`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `STATUS`: `current`
- `OWNER`: `PM / Architecture Office`

## Stream Map

### Backend

- **Status**: scoped-complete pending SAW.
- **Must Deliver**: candidate-card validator guardrail only.
- **Owned Files**:
  - `opportunity_engine/candidate_card_schema.py`

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no G8.2 dashboard runtime work.
- **Notes**: existing MSFT rows in the running dashboard are legacy runtime output, not the G8.2 card.

### Data

- **Status**: scoped-complete pending SAW.
- **Must Deliver**: exactly one MSFT candidate card and manifest from the existing scout output.
- **Owned Files**:
  - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
  - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`

### Docs/Ops

- **Status**: active-final-refresh.
- **Must Deliver**: G8.2 policy, handover, truth surfaces, governance logs, validation, and SAW.

## Blocked Streams

- G9 market-behavior signal card remains blocked until explicit approval.
- G8.3 user-seeded candidate card remains blocked until explicit approval.
- Dashboard card reader/status shell remains blocked until explicit approval.
- Provider ingestion, alerts, broker calls, rankings, scores, factor-model validation, buy/sell/hold output, and buying-range claims remain blocked.

## Governance Status

- G8.1B-R reviewer rerun: Complete, PASS.
- DASH-1 Page Registry Shell: Complete, shell-only PASS.
- G8.2 System-Scouted Candidate Card: Current, candidate-card-only pending SAW.
- Next action: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.
