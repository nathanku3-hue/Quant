# Top-Level Roadmap: GodView GV-FS0-First Build

Status: Active Architecture Canon — GV-FS0 First
Date: 2026-07-16
Authority: `godview_endgame_vision.md`, `godview_portfolio_first_operating_model.md`, `godview_portfolio_p0_owner_freeze.md`, and `gv_fs0_certification_and_data_authority_contract.md`

## Executive Decision

```text
ROADMAP_REVISION = APPROVED
EXECUTION_MODEL = GV_FS0_FIRST
SIX_STREAM_CONCURRENT_AUTHORITY = REVOKED
BACKWARD_COMPATIBILITY_LAYER = PROHIBITED
SYNTHETIC_FS0 = AUTHORIZED
REAL_PROVIDER_READ = BLOCKED_PENDING_DATA_ACCESS_AUTHORIZATION
REAL_CANDIDATE = BLOCKED_PENDING_FULL_ADMISSION
YFINANCE_AUTHORITY = PROHIBITED
WRDS_PEAD_REOPEN = PROHIBITED
LIVE_TRADING_MONITORING = OUT_OF_SCOPE
```

The only active implementation gate is **GV-FS0: one certified synthetic `OPEN` and one certified synthetic `NO_POSITION` through one new canonical book and one visible screen**.

Current shipped-product score remains **39/100**. This documentation cutover changes no code, runtime evidence, provider status, data output, or financial-alpha evidence.

- Revised-plan quality: **9.2/10**.
- Revoked six-stream execution plan: **5.8/10**.

## Why the Prior Order Was Rejected

The prior roadmap made six endgame work packages concurrently active. That was architecturally complete but operationally unsound for a local-first, single-operator system. It also retained `strategies/strategy_replay.py` as official GodView portfolio truth and placed policy controls, 252 sessions, 20+ corporate-action cases, and full P0 contracts inside the first integration gate.

Those claims are revoked. Streams A–F remain useful endgame work packages, but they are not concurrently active implementation streams.

## Active Canonical Chain

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot
→ Fs0Certification
→ Streamlit adapter
```

`Fs0Certification` is a first-class immutable result. It is not UI logic, a test comment, or a discretionary reviewer conclusion.

## GV-FS0 — One Decision, One Book, One Screen

### Scope

Two synthetic decision envelopes:

```text
MANUAL_OWNER_PAPER / OPEN
MANUAL_OWNER_PAPER / NO_POSITION
```

One small deterministic fixture:

- one security;
- 5–10 valid sessions;
- initial cash;
- one execution;
- one explicit fee or cost;
- one dividend ex-date;
- one dividend pay date;
- no provider input;
- no benchmark requirement;
- no optimizer;
- no corporate-action matrix beyond the dividend;
- no inference.

### Required outputs

```text
DecisionEnvelope
PortfolioBook event ledger
Fs0PortfolioSnapshot
Fs0Certification
canonical artifact bundle
independent reconstruction result
Streamlit rendering
```

### DecisionEnvelope

The envelope binds at minimum:

- authority tier and action;
- decision timestamp and effective timestamp;
- security identity;
- requested quantity or deterministic sizing input;
- rationale reference;
- protocol and fixture identity;
- operator identity;
- supersession identity where applicable.

Unknown authority, missing timestamps, ambiguous identity, or unsupported action blocks before book mutation.

### PortfolioBook

`PortfolioBook` is the only active official GodView economic book for FS0. It owns:

- append-only decision and economic events;
- executions and explicit costs;
- cash;
- whole-share holdings;
- dividend receivables;
- paid income;
- session valuation;
- NAV and contribution;
- deterministic canonical serialization.

No compatibility conversion from the legacy lifecycle or target-weight replay is permitted.

### Fs0PortfolioSnapshot

The snapshot is an immutable projection of the certified book at one session. It reports at minimum:

- authority and action;
- rationale reference;
- security and shares;
- cash;
- receivables;
- market value;
- NAV;
- session and cumulative contribution;
- source event range;
- canonical book hash;
- certification identity and status.

### Fs0Certification

The certification reports independently:

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
certification_status
failure_reasons
```

Any false or unknown mandatory result produces `BLOCKED`.

### Acceptance

- `OPEN` creates an exact whole-share position, exact cost, and residual cash.
- `NO_POSITION` records the decision while preserving all-cash economics.
- Prior effective holdings earn each interval's result.
- Dividend entitlement is created on ex-date and paid exactly once on pay date.
- `NAV = cash + market_value + receivables` every session.
- No missing return, stale price, or unsupported event is silently converted to zero.
- Negative cash, negative shares, implicit leverage, and out-of-order events block.
- Duplicate events are idempotent.
- Independent reconstruction starts from the original decision, price, event, and protocol inputs and shares no accounting implementation.
- Primary and independent quantities, cash, receivables, and NAV match exactly for FS0.
- Two runs generate the same canonical hash.
- Windows and Linux CI generate the same canonical payload hash.
- The default portfolio page displays authority, action, rationale reference, shares, cash, receivables, NAV, contribution, hash, and certification.
- Existing focused replay and dashboard tests remain green, but their outputs do not certify FS0.

## Data Authorization and Admission

Permission and factual data quality are separate detached authorities.

### DataAccessAuthorization

Required before any real provider read, including WRDS or a local licensed source. It records:

- provider and exact datasets or tables;
- account or licence owner;
- permitted use;
- date and entity coverage;
- restrictions;
- authorising natural person or accountable owner;
- repository remote/root, commit, tree, artifact path, and artifact hash;
- explicit actions authorised;
- expiration or revocation state.

It must not contain credentials. Payload fields cannot self-authorise the artifact.

### DataAdmissionCertificate

Created only after acquired bytes pass:

- exact raw hashes;
- delivery and availability timestamps;
- bitemporal lineage;
- completeness;
- contradiction checks;
- schema and semantic checks;
- admitted purpose;
- rejected uses.

Synthetic adapters and fixtures need neither artifact. Real reads require `DataAccessAuthorization`. Real candidate admission requires both artifacts plus the unchanged owner-freeze admission gate.

## Portability Boundary

For every new FS0 path:

- use `sys.executable`;
- use `pathlib`;
- do not use `.venv/Scripts/python.exe`;
- do not use drive-letter paths;
- do not use path-dependent serialization;
- do not include platform timestamps or absolute paths in canonical hashes.

Do not begin a repository-wide portability rewrite before FS0. Historical commands may remain until their owning path is activated.

## Streamlit Boundary

The existing presentation separation is enforced, not redesigned.

Streamlit imports are allowed only in:

```text
dashboard.py
views/**
launch.py or explicitly allowlisted presentation entrypoints
```

The Streamlit adapter may consume `Fs0PortfolioSnapshot` and `Fs0Certification`. It must not import the portfolio reducer, mutate the book, calculate NAV, or decide certification.

A static architecture test is required in the FS0 implementation round.

## Hard Authority Cutover

Immediately revoked:

- Streams A–F all start now;
- `strategies/strategy_replay.py` owns official GodView returns;
- four full P0 artifacts are prerequisites for the first synthetic slice;
- C0/C1/P1/P2/P7 belong in the first integration gate;
- 252 sessions belong in the first integration gate;
- 20+ corporate-action cases belong in the first integration gate.

Legacy code may remain physically present and serve unrelated historical screens temporarily, but:

- legacy replay is not imported by FS0;
- legacy lifecycle is not written by FS0;
- legacy artifacts cannot certify FS0;
- legacy performance cannot upgrade authority.

This is a hard authority cutover without making deletion a prerequisite.

## GV-FS1 — Policy and Benchmark Paths

After GV-FS0 passes, add:

```text
C0
C1
P1
P2
P7
capped equal weight
base and stress costs
turnover
actual IWB shadow
252-session deterministic replay
```

No real data is authorized in GV-FS1.

## GV-FS2 — Authority and Accounting Hardening

After GV-FS1 passes, add:

- bitemporal membership, identity, and sector fixtures;
- corrections;
- splits, mergers, spin-offs, rights, and delistings;
- at least 20 corporate-action golden cases;
- property tests;
- frozen reconciliation tolerances;
- certification aggregation.

## GV-RA0 — Real-Data Admission

Require all of:

- `DataAccessAuthorization`;
- authorised source acquisition;
- `DataAdmissionCertificate`;
- 60 consecutive authoritative sessions;
- 99.95% expected-file completeness;
- zero unresolved contradictions;
- independent review.

The thresholds in `godview_portfolio_p0_owner_freeze.md` remain unchanged. No threshold may be relaxed to accommodate available data.

## GV-E0 — Research-to-Decision Slice

Connect the MU `G_supply` falsification packet to the same:

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot
→ Fs0Certification
```

This is where GodView begins testing whether it improves research decisions rather than only accounting correctly. The four frozen E0 research artifacts remain byte-identical and retain sole research-promotion authority.

## GV-P1 — Prospective Policy Evaluation

Only after the preceding gates:

- return-aware challengers;
- optimizer challengers;
- timing variants;
- full search ledger;
- stationary bootstrap;
- multiplicity control;
- long-horizon prospective assessment.

## Streams A–F — Deferred Endgame Work Packages

The prior labels remain as planning categories only:

```text
A — P0 contracts and golden cases
B — bitemporal data authority and canonical inputs
C — portfolio ledger and deterministic replay
D — candidate, episode, authority, and search ledger
E — policy, execution, cost, and counterfactual controls
F — independent verification, property testing, and inference
```

They are activated only through the staged gates above. They have no concurrent-start authority.

## Preserved Boundaries

- current constituents, ETF holdings, ticker continuity, current sectors, adjusted close, and silent proxy substitution remain invalid authority;
- yfinance and convenience data remain discovery-only and cannot certify or admit a real candidate;
- all five WRDS permission rows remain pending until detached table-specific evidence and approval exist;
- WRDS-dependent PEAD reopening is prohibited;
- live-trading monitoring, broker paths, orders, leverage, shorts, derivatives, and live capital remain out of scope;
- architecture correctness, synthetic success, or portfolio accounting do not establish financial alpha.

## Active Next Action

Implement **GV-FS0 only**: one synthetic `OPEN`, one synthetic `NO_POSITION`, one new canonical `PortfolioBook`, one immutable `Fs0Certification`, one independent reconstruction, one cross-platform canonical hash, and one read-only Streamlit screen.
