# Phase Brief: GV-FS0 — One Decision, One Book, One Screen

Mode: `EXECUTION_PACKET`
Status: `PHASE_1_GO; PRECISION_PATCH_APPLIED; FREEZE_ARTIFACTS_AND_PROTOCOL_TESTS_IN_PROGRESS; REDUCER_BLOCKED`
Date: 2026-07-17
RoundID: `ROUND-20260717-GV-FS0-PROTOCOL-FREEZE-PHASE1`
ScopeID: `GV_FS0_PROTOCOL_V1_FREEZE_PROOF`
Authority: `docs/architecture/top_level_roadmap.md`, `docs/architecture/godview_portfolio_first_operating_model.md`, and `docs/architecture/gv_fs0_certification_and_data_authority_contract.md`
Hierarchy: L1 Terminal Zero quantitative research console; L2 active stream Docs/Ops protocol freeze; L2 deferred streams Backend accounting, Frontend/UI, Data admission, and Research integration; L3 flow Consolidation -> Machine Artifacts -> Golden Tests -> Freeze Audit -> Reducer Authorization.

## Objective

Replace the revoked six-stream concurrent execution order with one bounded first slice:

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot
→ Fs0Certification
→ Streamlit adapter
```

The authority cutover and P0-P4 design review are complete. The consolidated V1 protocol now incorporates the approved canonical byte rules, acyclic identities, event ordering and transition ownership, two verifier attempts, unique hash-addressed verifier-result retention, deterministic supervision boundaries, registry separation, certification semantics, blocked-artifact boundary, and fail-safe publication model.

The freeze is not yet effective. Before reducer work begins, the machine-readable schemas, both registries, event ranks, generated-event slots, transition-ownership definition, canonical vectors, protocol tests, artifact hashes, bootstrap and enforced CI immutability evidence, and clean freeze audit must pass.

The reviewed source bytes were transferred into the clean managed worktree and verified before amendment:

```text
contract_sha256_before_precision_patch = 085a4bcf672069320e69a40c010bbc6ad7bd5c63a844214cb140cb6292de8a02
phase_brief_sha256_before_phase1_update = 9b356b39a91190cd3c3f4aa74a7e85ea014323aff1827959c2ba77ceb522f5c6
git_base_commit = 601c69af874da252a15910802ae5036a0341db92
git_object_format = sha1
```

Current shipped-product score remains **39/100** because no user-visible certified portfolio slice exists yet.

## Frozen Research Boundary

The strict research artifacts remain byte-identical:

```text
e0_preregistration.yaml       0a6dc18a44d7532610a73f90b92477fc7bd36644c1a052d81a48162097176618
evidence_authority_matrix.csv 3306adbed26d27732a0a53d3819a09044e418e183ecc58ebebf82c6f9fe0dcb0
e0_model_spec.md              28a0ea062777d9364008480266ce933bd6a34348ce0defcac7185398068a38f0
e0_acceptance_tests.md         9d9a7f195bd8db2caea82859d6a73d951c862f229fc9d72e5302c58ba7b8d55c
```

GV-FS0 does not amend research claim authority.

## Authority Cutover

```text
ROADMAP_REVISION = APPROVED
EXECUTION_MODEL = GV_FS0_FIRST
SIX_STREAM_CONCURRENT_AUTHORITY = REVOKED
BACKWARD_COMPATIBILITY_LAYER = PROHIBITED
SYNTHETIC_FS0_PROTOCOL_PROOF = AUTHORIZED
SYNTHETIC_FS0_REDUCER_AND_PRODUCT = BLOCKED_PENDING_PROTOCOL_FREEZE
REAL_PROVIDER_READ = BLOCKED_PENDING_DATA_ACCESS_AUTHORIZATION
REAL_CANDIDATE = BLOCKED_PENDING_FULL_ADMISSION
YFINANCE_AUTHORITY = PROHIBITED
WRDS_PEAD_REOPEN = PROHIBITED
LIVE_TRADING_MONITORING = OUT_OF_SCOPE
```

Streams A–F remain later work packages only.

## Protocol-Freeze Boundary

Authorized before reducer implementation:

- exact canonical encoders and raw-token parsing;
- Draft 2020-12 schemas;
- certification-failure and operational-error registries;
- canonical vectors;
- event-rank, generated-event-slot, and transition-ownership definitions;
- verifier supervision primitives using the frozen deadlines, limits, caps, and predicate rules;
- protocol and golden tests;
- exact freeze-artifact hashes and two-mode CI guards: `BOOTSTRAP` for the initial candidate and `ENFORCED` after the protected base contains V1.

Reducer and product work remains blocked until the protocol-freeze commit passes clean audit.

The authoritative protocol is:

```text
docs/architecture/gv_fs0_certification_and_data_authority_contract.md
```

Earlier audit patches are historical evidence only and are not independent runtime authority.

The contract is the normative semantic source, the 18 generated artifacts are its machine-readable normative expression, and the generator is derivation machinery only. A generator-only constant or any disagreement among contract, artifacts, vectors, and regeneration output blocks the freeze.

Approved precision decisions are now binding:

- price freshness uses zero session lag, same security/session, one unique positive price, and no future timestamp;
- duplicate origin-order keys produce registered `DUPLICATE_ORIGIN_ORDER_KEY` and causality `FALSE`;
- NO_POSITION has zero execution intents without schema failure;
- post-replace verification failure creates no rollback or prior-preservation claim; and
- frozen V1 bytes permit no same-version correction.

## GV-FS0 Fixture

Two synthetic decisions:

```text
MANUAL_OWNER_PAPER / OPEN
MANUAL_OWNER_PAPER / NO_POSITION
```

Fixture constraints:

- one security;
- 5–10 valid sessions;
- initial cash;
- one execution;
- one explicit fee or cost;
- one dividend ex-date;
- one dividend pay date;
- no provider input;
- no benchmark;
- no optimizer;
- no corporate-action matrix beyond the dividend;
- no inference.

## Required Outputs

### Protocol-freeze outputs — authorized now

- consolidated normative V1 contract;
- machine-readable V1 schemas;
- certification-failure registry;
- operational-error registry;
- event-rank table;
- generated-event-slot table;
- transition-ownership table;
- canonical vectors;
- protocol and golden tests;
- exact frozen-artifact hash register;
- CI same-version immutability guard.

### Product outputs — blocked until freeze audit passes

- immutable `DecisionEnvelope`;
- append-only `PortfolioBook` event ledger;
- immutable `Fs0PortfolioSnapshot`;
- immutable `Fs0Certification`;
- certified decision results for OPEN and NO_POSITION;
- final two-component canonical bundle;
- read-only Streamlit rendering.

## Fs0Certification

The certification contains ten mandatory `TRUE | FALSE | UNKNOWN` checks:

```text
decision_authority_valid
timestamp_causality_valid
price_freshness_valid
cash_conserved
holdings_valid
nav_reconciled
receivables_reconciled
unsupported_events_absent
independent_reconstruction_passed
canonical_hash_reproduced
```

It also binds:

- exactly two ordered verifier attempts;
- unique hash-addressed retained verifier results;
- the certification-failure registry version and hash;
- ordered `{check, outcome, code}` failure bindings; and
- stable fixture, decision, book, snapshot, payload, and verifier-input identities.

Any false or unknown mandatory check produces `BLOCKED`. Operational publication or presentation errors use a separate registry and do not alter certification identity.

## Acceptance Checks

### Book and accounting

- `OPEN` creates exact whole shares, exact cost, and residual cash.
- `NO_POSITION` records the decision and preserves all-cash economics.
- Prior effective holdings earn each interval's result.
- Dividend entitlement is created on ex-date and paid exactly once on pay date.
- `NAV = cash + market_value + receivables` every session.
- Missing returns, stale prices, and unsupported events never become zero silently.
- Negative cash, negative shares, implicit leverage, and out-of-order events block.
- Duplicate events are idempotent; conflicting duplicates block.

### Independent certification

- reconstruction runs only as `sys.executable -I -X utf8 validation/gv_fs0_reconstruction.py --input <canonical_input.json>`;
- the script refuses non-isolated execution and in-process import, consumes original canonical decision/price/event/protocol JSON only, and emits canonical JSON to stdout only;
- reconstruction shares no accounting implementation, primary intermediate artifact, repository import, artifact writer, dynamic import, or path mutation with the primary path;
- static AST checks enforce standard-library-only imports and reject `strategies`, primary-book, artifact-writer, dynamic-import, and path-mutation dependencies;
- exactly two ordered attempts are required;
- identical successful attempts reference one unique retained result record, while differing schema-valid results retain two hash-addressed records;
- execution deadline is 30.000 seconds, shutdown observation is 2.000 seconds, stdout validity/cap is 1,048,576/1,048,577 bytes, and stderr validity/cap is 65,536/65,537 bytes;
- timeout, output-limit, process, stream, decode, canonicalization, schema, and binding predicates follow the frozen monotonic supervision rules;
- primary and independent quantities, cash, receivables, market value, NAV, contribution, canonical bytes, and payload hash match exactly;
- two runs produce the same canonical result;
- Windows and Linux CI produce the same canonical bytes and hashes.

### Presentation boundary

- Streamlit imports remain limited to `dashboard.py`, `views/**`, `launch.py`, or explicitly allowlisted presentation entrypoints;
- the adapter consumes only `Fs0PortfolioSnapshot` and `Fs0Certification`;
- the adapter does not import the reducer, mutate the book, calculate NAV, construct receivables, decide freshness, or aggregate certification;
- the default portfolio page renders authority, action, rationale reference, shares, cash, receivables, NAV, contribution, hash, and certification.

### Regression boundary

- existing focused replay and dashboard tests remain green;
- existing replay/dashboard outputs are explicitly non-certifying for FS0;
- no compatibility layer imports or converts legacy replay/lifecycle state.

## Data Authority

### DataAccessAuthorization

Required before any real provider read. It must bind exact provider/datasets, licence owner, use, coverage, restrictions, accountable authorizer, repository/artifact identity, authorized actions, and expiration/revocation state. It contains no credentials and cannot self-authorise.

### DataAdmissionCertificate

Created only after acquired bytes pass exact hashes, delivery/availability timestamps, bitemporal lineage, completeness, contradiction, schema, semantic, purpose, and rejected-use checks.

Synthetic fixtures require neither artifact. Real reads require the first. Real candidate admission requires both plus the unchanged full admission gate.

## Portability Rules

For all new FS0 paths:

- use `sys.executable`;
- use `pathlib`;
- no `.venv/Scripts/python.exe`;
- no drive-letter paths;
- no path-dependent serialization;
- no platform timestamps or absolute paths in canonical hashes.

No repository-wide portability programme is authorized before FS0.

## Legacy Boundary

Legacy code may remain physically present, but:

- `strategies/strategy_replay.py` exposes `__authority__ = "REVOKED_BY_GV_FS0_20260716"` and the marker is verified statically;
- `strategies/strategy_replay.py` is not official GodView truth;
- legacy replay is not imported by FS0;
- legacy lifecycle is not written by FS0;
- legacy artifacts cannot certify FS0;
- legacy performance cannot upgrade authority;
- deletion is not a prerequisite;
- backward-compatibility conversion is prohibited.

## Deferred Roadmap

- **GV-FS1:** C0/C1/P1/P2/P7, capped equal weight, costs, turnover, actual IWB shadow, 252-session replay.
- **GV-FS2:** bitemporal fixtures, corrections, broad corporate actions/delistings, 20+ goldens, property tests, certification aggregation.
- **GV-RA0:** detached data authorization, authorised acquisition, admission certificate, 60 sessions, 99.95% completeness, zero contradictions, independent review.
- **GV-E0:** connect the MU `G_supply` packet to the same decision/book/certification path.
- **GV-P1:** challengers, timing variants, search ledger, bootstrap, multiplicity, and long-horizon prospective assessment.

## Current Done Criteria

- [x] Roadmap revision approved.
- [x] Six-stream concurrent authority revoked.
- [x] GV-FS0 made the sole active execution gate.
- [x] `Fs0Certification` defined as a first-class immutable result.
- [x] Data access authorization separated from data admission.
- [x] FS0-only portability boundary defined.
- [x] Streamlit boundary made mechanically testable.
- [x] Legacy compatibility layer prohibited without requiring deletion.
- [x] Frozen E0 research artifacts and real-admission thresholds preserved.
- [x] Isolated standard-library reconstruction subprocess implemented with canonical JSON stdin-by-file/stdout-only contract.
- [x] Non-`-I` execution, in-process import, repository imports, dynamic imports, path mutation, and artifact writes mechanically blocked.
- [x] `strategy_replay.py` machine-checkable revocation marker and FS0 import/certification guards implemented.
- [x] Focused isolation/economic/authority tests pass for synthetic `OPEN` and `NO_POSITION` reconstruction.
- [x] P0-P4 architecture and protocol design received conditional final approval.
- [x] Approved v1-v6 clauses and the two final amendments consolidated into one authoritative V1 contract.
- [x] Reviewed contract and phase brief transferred into a clean managed worktree with exact pre-amendment SHA-256 verification.
- [x] Four precision gaps and four execution amendments incorporated into the normative contract.
- [x] Exact machine-readable V1 schemas generated and validated.
- [x] Certification-failure and operational-error registries generated and hashed.
- [x] Event ranks, generated-event slots, and transition ownership generated and hashed.
- [x] Canonical vectors and the protocol/golden proof suite pass locally.
- [x] Frozen artifact hashes, Git object format, Git blob OIDs, byte lengths, and terminal-LF counts are recorded in the freeze manifest.
- [x] Bootstrap-mode deterministic generation, manifest, vector, extra/missing artifact, and mutation guards pass locally.
- [x] Native Windows Python and Linux Python produce identical protocol parity records locally.
- [ ] Enforced-mode guard is proven relative to the committed frozen candidate, including the non-merged mutation-probe branch.
- [ ] Hosted Windows/Linux CI completes successfully on the candidate.
- [ ] Protocol-freeze commit receives a clean audit result.
- [ ] Primary GV-FS0 `PortfolioBook` and certification integration implemented after freeze approval.
- [ ] Synthetic `OPEN` and `NO_POSITION` certified.
- [ ] Primary and isolated reconstruction match exactly through certification.
- [x] Local Windows/Linux canonical hash parity passes; hosted workflow evidence remains pending.
- [ ] default portfolio screen renders certified output.
- [ ] focused legacy replay/dashboard regressions pass without certifying FS0.

## Held

- provider/network access;
- real data acquisition;
- real candidate admission;
- yfinance authority;
- WRDS-dependent PEAD reopening;
- benchmark and policy paths before GV-FS1;
- broad corporate actions before GV-FS2;
- research-to-decision integration before GV-E0;
- live-trading monitoring, broker, orders, leverage, shorts, derivatives, or live capital;
- financial-alpha claims.

## Next Action

Generate the machine-readable V1 schemas, both registries, event-rank table, generated-event-slot table, transition-ownership table, and canonical vectors from the consolidated contract. Implement and pass only the protocol/golden tests, record exact freeze hashes, add the CI same-version guard, and submit the protocol-freeze commit for clean audit.

Do not begin economic event reduction, fixture certification, permanent bundle publication, or Streamlit integration until the freeze audit passes.
