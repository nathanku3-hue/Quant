# AOV-0 Insurance V0 + Data Authority — SAW Receipt

Mode: `CLOSURE_REPORT`
Date: 2026-08-06
RoundID: `ROUND-20260806-AOV0-INSURANCE-DATA-AUTHORITY`
ScopeID: `AOV0-INSURANCE-V0-DATA-ADMISSION-CUT`
Branch: `codex/pit-source-authority-1`

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-scope | Domains: Product, Software Engineering, Data Provenance, Quant Research, Governance | FallbackSource: `docs/spec.md` + `docs/phase_brief/alpha-organism-vertical-0-brief.md`

## Scope

In scope: freeze the user-approved AOV-0 V0 insurance budget; preserve the strengthened first-seal cut binding; narrow data authority to one bounded CRSP/PERMNO admission plus direct Federal Reserve Bank of New York SOFR; verify current official SOFR availability; attempt the authorized CRSP credential path without reading arbitrary secret files; reconcile active truth surfaces; rerun local AOV/research/zero-compat/compile/JSON/whitespace checks.

Out of scope: identity redesign, provider programme, schema exploration, WRDS SOFR mirror, proxy data, compatibility restoration, hidden-OOS platformization, broker/live capital, Git publication.

## Acceptance checks

| Check | Result |
|---|---|
| CHK-01 Production insurance V0 exact values | PASS — materiality `0.05`, annual premium ceiling `0.0015` |
| CHK-02 Prospective contract validates with frozen production values | PASS |
| CHK-03 Decision-cut authority + missing-input state | PASS — requires frozen contract hash, recomputed universe hash, five source receipts/retrieval times/raw hashes; missing state is `BLOCKED_MISSING_ADMITTED_INPUTS` with owner list empty |
| CHK-04 Direct New York Fed SOFR authority reachable after revision-safe time | PASS — effective `2026-08-05`, `3.64%`, raw response 256 bytes, SHA-256 `39e5124aed482dff5f5dba5265da34c82f67fbce10e1704d379d33827d61f9a2` |
| CHK-05 Authorized CRSP/PERMNO credential surface available to local runtime | FAIL/BLOCKED — Windows standard `pgpass.conf` exists, but no WRDS/PG username is surfaced and default-user libpq auth returns `fe_sendauth: no password supplied` |
| CHK-06 AOV + hardened research regression | PASS — 61/61 (AOV 27/27 + hardened research 34/34) |
| CHK-07 ZERO-COMPAT seven-count scan | PASS — all seven counters `0` |
| CHK-08 Compile, current-context JSON, whitespace | PASS |
| CHK-09 Financial-evidence terminology remains honest | PASS — seal readiness/clock may rise; financial-alpha evidence stays `0` until matured outcome |
| CHK-10 Independent Reviewer A/B/C ownership separation | NOT RUN — independent reviewer lane unavailable in this execution channel |

ChecksTotal: 10
ChecksPassed: 8
ChecksFailed: 2

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Blocking | No honest CRSP/PERMNO bytes can be acquired from the authorized source family because the existing Windows pgpass file cannot be matched without a surfaced WRDS/PG username. | Surface the existing WRDS username to the runtime first; if the standard pgpass entry matches, keep the password inside pgpass. Otherwise repair standard libpq credential configuration without copying secrets into repo/evidence or substituting another provider. | Operator / Data | Open |
| Blocking for SAW PASS | Mandatory independent Reviewer A/B/C ownership separation is unavailable here. | Run independent review against the exact candidate when that lane is available; do not reinterpret local tests as independent review. | Review | Open external |
| Advisory | Direct NY Fed SOFR source was verified but no final `official_sofr.parquet` was written because the five-artifact admission must remain one coherent cut with the CRSP/PERMNO side. | Materialize the official SOFR parquet/receipt in the same bounded admission cut once CRSP acquisition is executable. | Data | Open |

## Scope split summary

in-scope complete: production insurance freeze, direct NY Fed source decision, CRSP/PERMNO authority decision, no-proxy/no-compat boundary, first-seal cut-binding mechanics, active truth reconciliation, local regressions.

in-scope operationally blocked: actual current CRSP/PERMNO acquisition and therefore the five admitted real artifacts and first prospective seal.

inherited out-of-scope: E2 hosted/audit/publication remains parallel and non-blocking; independent reviewer ownership remains external.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `research/aov0/contracts.py` | freezes production V0 insurance at `0.05 / 0.0015` | local tests PASS; independent unavailable |
| `tests/aov0/test_cube_policy.py`, `test_first_seal_entrypoint.py` | production contract and data-only blocker expectations | local tests PASS |
| `PRD.md`, `PRODUCT_SPEC.md`, `PHASE_QUEUE.md`, `README.md` | active gate reconciled to insurance-frozen/data-only blocker | local consistency scan PASS |
| `docs/context/*`, active AOV brief/checklist/spec | current authority reconciled; direct NY Fed + bounded CRSP/PERMNO path frozen | local consistency scan PASS |
| `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md` | insurance/data authority and evidence terminology recorded | local validation PASS |
| `scripts/aov0_first_seal.py`, `research/aov0/experiment.py`, `scripts/aov_zero_compat_scan.py` | prior cut-binding and no-compat hardening retained | AOV/research/zero-compat PASS |

## Validation / evidence

- AOV + hardened research selected matrix: `61/61 PASS` (AOV `27/27`, hardened research `34/34`).
- ZERO-COMPAT: all seven counters exactly zero.
- Python compile: PASS.
- `docs/context/current_context.json` parse: PASS.
- `git diff --check`: PASS.
- Default first-seal command: `BLOCKED_MISSING_ADMITTED_INPUTS`; `owner_decisions_required=[]`; `prospective_clock_started=false`; `financial_alpha_evidence=0`; no `alpha_evidence` compatibility key remains.
- Direct New York Fed SOFR raw response: effective date `2026-08-05`; rate `3.64`; revision indicator empty; 256 bytes; SHA-256 `39e5124aed482dff5f5dba5265da34c82f67fbce10e1704d379d33827d61f9a2`.
- WRDS runtime preflight: `WRDS_USER`, `WRDS_PASS`, `PGUSER`, `PGPASSFILE` absent; Windows standard `%APPDATA%\\postgresql\\pgpass.conf` present; `psycopg2` available; default-user connection returns `fe_sendauth: no password supplied`; no credential file content or arbitrary secret file was read.

## Open Risks

Open Risks: CRSP/PERMNO acquisition cannot execute until the existing WRDS username/authentication mapping is surfaced to this runtime; no five-artifact real admission or prospective seal exists yet; independent Reviewer A/B/C not run.

## Next action

Next action: surface the existing WRDS username to the local runtime and let standard libpq pgpass supply the password if the matching entry exists; then immediately execute one bounded CRSP/PERMNO + direct New York Fed SOFR admission, construct the bound `aov0_decision_cut_v1`, run the first real seal, exact-reopen it, and start the weekly tape. Do not reopen architecture or insurance methodology.

ClosurePacket: RoundID=ROUND-20260806-AOV0-INSURANCE-DATA-AUTHORITY; ScopeID=AOV0-INSURANCE-V0-DATA-ADMISSION-CUT; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=CRSP/PERMNO acquisition blocked because existing WRDS credentials are not surfaced to this runtime and independent Reviewer A/B/C not run; NextAction=Surface existing WRDS entitlement then run bounded CRSP plus direct NY Fed admission and seal immediately
ClosureValidation: PASS
SAWBlockValidation: PASS
