# Observability Pack — Current

Date: 2026-08-02
Phase: `GV-PROSPECTIVE-PAPER-BASELINE-1`
Status: `IMPLEMENTED_CANDIDATE; REAL_PROSPECTIVE_EVIDENCE_PENDING`
Accepted score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Immutable sentinels

- Accepted 25-security closure and terminal tag remain immutable.
- Repair base `5687a2c` remains immutable and remote-equal.
- Accepted score remains `62/100` until genuine prospective evidence is banked.
- Retained 10/25 and scale 50/100 scenarios continue through one engine, persistence implementation, app, and view.
- Existing 10/25 storage filenames and roots remain exact.

## Prospective authority sentinels

- Runtime observation content must not appear in scenario code.
- Evidence content hash is derived from the supplied content, never trusted from UI input.
- Observation timestamps must be valid UTC and strictly after current authority.
- Owned instrument IDs must exist and cannot repeat within one request.
- Per-security outcomes are exactly `ADMIT`, `REJECT`, or `ABSTAIN`.
- `CASH` is a portfolio capital candidate only.
- Non-`ADMIT` target quantity must be `0`.
- Preview cannot modify workspace bytes or event count.
- Confirm/reject proposal identity must be recomputed and byte-equal; stale or mutated proposals fail closed.
- Confirmed evidence must bind only to owned instruments.
- Rejected proposal evidence must not enter authoritative evidence or thesis state.

## Projection sentinels

- The baseline event prefix remains byte-identical.
- Every episode is represented by an append-only event tail.
- Reconstructed evidence, reviews, observations, snapshots, orders, fills, certifications, rejection history, and book must match persisted bytes.
- No-change episodes preserve book bytes.
- Transition episodes require at least one SELL and one BUY leg.
- Accounting residual remains `0`.
- Rejected episodes preserve authoritative evidence/reviews/snapshots/orders/fills/book and append only rejection custody plus certification.

## Product sentinels

- Existing environment-selected app is the product entry point.
- Each episode requires at most two authorization actions: preview and confirm/reject.
- No per-security confirmation loop is introduced.
- No provider, broker, optimizer, autonomous-order, client-asset, or live-capital path is imported.
- Automated fixtures are capability evidence only; do not label them prospective evidence.

## Roadmap sentinels

- Real operator-supplied prospective episodes precede real shadow Challenger opening.
- Challenger uses the same certified 25-security opportunity set and runtime observation envelope.
- Old Challenger slot/cell harness is historical only and must not become a compatibility contract.
- Universe custody is deferred until broader membership is required.
- Legal review is not a paper Challenger blocker and remains mandatory before broker credentials, automated submission, client assets, advice activity, or real capital.
- Limited Live requires separate authorization.

## Current signal

- Prospective core `11/11 PASS`.
- Prospective UI `3/3 PASS`.
- Retained operated/25/App `23/23 PASS`.
- Scale repair `13/13 PASS`.
- Shared accounting/replay `104/104 PASS`.
- Historical harnesses `24/24 PASS`.
- Final FS0/context validation, exact candidate custody, hosted CI, and genuine prospective evidence remain open.
