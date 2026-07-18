# Top-Level Roadmap: GodView Certified Portfolio OS

Status: Active Architecture Canon — GV-E0A-OPERABLE sole active gate
Date: 2026-07-19
Product tip lineage: `490a234` (F1C-SHIP closed substrate on product branch lineage)
Active working branch (this recut): `codex/gv-e0a-operable`
Authority: `godview_endgame_vision.md`, `godview_portfolio_first_operating_model.md`, `godview_portfolio_p0_owner_freeze.md`, `gv_fs0_certification_and_data_authority_contract.md`, and `docs/phase_brief/gv-e0a-operable-brief.md`

## Executive Decision (Active Canon)

```text
PRODUCT_PIVOT = AUTHORIZED (UOE discretionary cockpit → GodView certified portfolio OS)
F1C_SHIP = CLOSED_SUBSTRATE (deterministic certification + permanent dual-fixture evidence; not operator-usable product endpoint)
ACTIVE_GATE = GV-E0A-OPERABLE
SHIPPED_PRODUCT_SCORE = 39/100 (owner claim ceiling; metric confidence low; no alpha)
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
  (stage-only; score stays 39/100; no alpha)
SIX_STREAM_CONCURRENT_AUTHORITY = REVOKED
BACKWARD_COMPATIBILITY_LAYER = PROHIBITED
REAL_PROVIDER_READ = BLOCKED_PENDING_DATA_ACCESS_AUTHORIZATION
REAL_CANDIDATE = BLOCKED_PENDING_FULL_ADMISSION
YFINANCE_AUTHORITY = PROHIBITED
WRDS_PEAD_REOPEN = PROHIBITED
LIVE_TRADING_MONITORING = OUT_OF_SCOPE
FS1_BATCH = NOT_NEXT
```

**One active gate only:** **GV-E0A-OPERABLE** — a combined research→decision→book→cert→publish→visible vertical on frozen MU `G_supply` custody. F1C-SHIP is closed substrate, not an active shipment gate. Broad FS1 is a future stage, not next action.

### Score semantics (do not conflate)

| Measure | Value | Meaning |
|---|---|---|
| `SHIPPED_PRODUCT_SCORE` | **39/100** | Owner claim ceiling. Does **not** auto-uplift for demos, dual-fixture screens, or local green paths. No alpha. Metric confidence low. |
| `FUNCTIONAL_STAGE` | **`CERTIFIED_SINGLE_DECISION_OPERABLE`** | E0 custody + `HOLD_FOR_EVIDENCE`→paper `NO_POSITION` + certify + atomic current publish + one default Streamlit decision on branch `codex/gv-e0a-operable`. Prior stage was dual-fixture static demo on `490a234`. |
| Score rule | no auto-uplift | Stage promotion does **not** raise `SHIPPED_PRODUCT_SCORE`. Score stays 39/100 unless a separate rubric-based owner claim is authorized. |

### Active gate — GV-E0A-OPERABLE

```text
frozen MU G_supply evidence (4 files exact hashes)
→ explicit HOLD_FOR_EVIDENCE research decision / portfolio NO_POSITION
→ one active DecisionEnvelope
→ PortfolioBook + independent certification
→ atomic publication of current decision
→ one visible current decision
→ real Streamlit smoke
```

**Forbidden for this gate:** providers, real prices, FS1 batch, PEAD reopen, alpha claims, broker paths, compatibility dual-authority UI, historical-suite repair.

### Closed substrate (history — not active gates)

- **F1A OPEN / F1B NO_POSITION / F1C-SHIP**: closed on product tip lineage `490a234` (transport C/C2 + closeout T). Permanent two-role certified bundle + default Certified Portfolio route + product CI. Demoted to substrate; do not reopen as active shipment language.
- **GV-FS0 protocol V1 freeze**: closed earlier; frozen contracts remain byte-immutable authority for certification bytes.
- **PEAD strict-PIT**: `TERMINATED_DIAGNOSTIC_ONLY` — not active product work.
- **UOE / six-stream concurrent execution**: revoked as active product framing; retained only as historical product lineage.

### Why multi-gate language is revoked

Prior truth surfaces stacked “F1C closed / still active / still blocked / implement next” and left FS0 dual-demo language as if still the shipment gate. That multi-active-gate drift is revoked. **Only GV-E0A-OPERABLE is active.**

Six concurrent endgame streams (A–F) remain deferred work packages, not concurrent implementation streams.

## Active Canonical Chain

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot
→ Fs0Certification
→ Streamlit adapter
```

`Fs0Certification` is a first-class immutable result. It is not UI logic, a test comment, or a discretionary reviewer conclusion.

## GV-E0A-OPERABLE — Sole Active Gate (Research → One Operable Decision)

### Objective

Connect frozen MU `G_supply` research custody to one operator-visible **current** certified decision, without reopening FS0 dual-demo shipment language and without starting broad FS1.

### Vertical (must ship as one)

```text
frozen MU G_supply evidence (4 files exact hashes)
→ explicit HOLD_FOR_EVIDENCE research decision / portfolio NO_POSITION
→ one active DecisionEnvelope
→ PortfolioBook + independent certification
→ atomic publication of current decision
→ one visible current decision
→ real Streamlit smoke
```

### Frozen E0 research artifacts (byte-identical; sole research-promotion custody)

```text
docs/architecture/godview_e0/e0_preregistration.yaml
  sha256 0a6dc18a44d7532610a73f90b92477fc7bd36644c1a052d81a48162097176618
docs/architecture/godview_e0/evidence_authority_matrix.csv
  sha256 3306adbed26d27732a0a53d3819a09044e418e183ecc58ebebf82c6f9fe0dcb0
docs/architecture/godview_e0/e0_model_spec.md
  sha256 28a0ea062777d9364008480266ce933bd6a34348ce0defcac7185398068a38f0
docs/architecture/godview_e0/e0_acceptance_tests.md
  sha256 9d9a7f195bd8db2caea82859d6a73d951c862f229fc9d72e5302c58ba7b8d55c
```

Any hash drift blocks E0A. E0A does not rewrite research claim authority; it consumes sealed custody for one paper `HOLD_FOR_EVIDENCE` / portfolio `NO_POSITION` path.

### Acceptance (gate-level)

- One active current DecisionEnvelope exists (not dual static fixture-only UI).
- Portfolio path is `NO_POSITION` (or explicit paper hold) bound to that envelope.
- Independent certification PASS for the operable path.
- Atomic publication of **current** decision (not dual-fixture F1C bundle as the operator endpoint).
- One visible current decision on the product surface.
- Real Streamlit smoke (not headless-only proof as sole evidence).
- Score remains 39/100; stage may move to `CERTIFIED_SINGLE_DECISION_OPERABLE` **only** when the above evidence exists on branch.

### Forbidden

providers · real prices · FS1 batch · PEAD · alpha claims · broker · compatibility dual-authority UI · historical-suite repair · reopening F1C-SHIP as active gate · broad six-stream concurrency

---

## History / Substrate — GV-FS0 Dual-Fixture Demo (CLOSED)

> **Status:** `CLOSED_SUBSTRATE`. Not the active gate. Retained for architecture and certification byte authority.

F1A synthetic `OPEN`, F1B synthetic `NO_POSITION`, and F1C-SHIP permanent dual-role bundle shipment closed on product tip lineage `490a234`. That path proves deterministic certification and a permanent dual-fixture Certified Portfolio demo. It is **not** an operator single-decision product endpoint.

### Historical scope (FS0 dual-demo)

Two synthetic decision envelopes:

```text
MANUAL_OWNER_PAPER / OPEN
MANUAL_OWNER_PAPER / NO_POSITION
```

One small deterministic fixture (one security; 5–10 sessions; cash; one execution; fee; dividend; no provider/benchmark/optimizer/inference).

### Historical required outputs

```text
DecisionEnvelope
PortfolioBook event ledger
Fs0PortfolioSnapshot
Fs0Certification
canonical artifact bundle
independent reconstruction result
Streamlit rendering
```

### DecisionEnvelope (retained contract)

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

### PortfolioBook (retained contract)

`PortfolioBook` is the official GodView economic book for certified paper paths. It owns append-only decision/economic events, executions and costs, cash, whole-share holdings, dividend receivables, paid income, session valuation, NAV/contribution, and deterministic canonical serialization. No compatibility conversion from legacy lifecycle or target-weight replay.

### Fs0PortfolioSnapshot / Fs0Certification (retained contract)

Snapshot is an immutable projection at one session. Certification independently reports:

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

### Historical FS0 acceptance (substrate evidence — closed)

- `OPEN` / `NO_POSITION` economics, dividend, NAV identity, reconstruction, dual-platform hash, and dual-fixture default page as closed on product lineage.
- Existing focused replay/dashboard tests may remain green without certifying FS0 or E0A.

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

## GV-FS1 — Policy and Benchmark Paths (Future — NOT next action)

After **GV-E0A-OPERABLE** closes (and only then), add:

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

## GV-E0 / GV-E0A — Research-to-Decision

- **Historical label `GV-E0`**: research packet freeze (four artifacts) — custody closed; hashes locked above.
- **Active label `GV-E0A-OPERABLE`**: sole active gate — see Active gate section. Combined vertical from frozen custody to one visible current decision. Do not treat broad “E0 research expansion” or FS1 as next.

## GV-P1 — Prospective Policy Evaluation (Future)

Only after the preceding gates (E0A then FS1+ as staged):

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

Implement **GV-E0A-OPERABLE only**:

```text
frozen E0 custody → HOLD_FOR_EVIDENCE / NO_POSITION → one DecisionEnvelope
→ book/cert → atomic current publication → one visible decision → Streamlit smoke
```

Do **not** reopen F1C-SHIP as an active gate. Do **not** start FS1, providers, PEAD, alpha claims, broker paths, dual-authority UI, or historical-suite repair. Keep `SHIPPED_PRODUCT_SCORE = 39/100`. `FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE` is stage-only and does not authorize alpha or score uplift.
