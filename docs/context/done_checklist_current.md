# Done Checklist — Current

Date: 2026-08-01
Phase: `GV-ENGINE-SCALE-CHARACTERIZATION-1`
Status: `FROZEN_FINDING; REVIEW_BLOCKED`
Accepted score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Scope and custody

- [x] P0 terminal closure `e564cd9` remains immutable.
- [x] `gv-operated-portfolio-25-1-terminal` remains unchanged.
- [x] Diagnostic candidate `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283` is immutable and remote-equal.
- [x] P1 uses the existing engine and probes the existing persistence implementation.
- [x] No parallel engine, storage path, schema family, application, or view was added.
- [x] The 100-security run is explicitly diagnostic and not Universe acceptance.

## Characterization

- [x] Declarative 50-security scenario contains 50 unique permanent keys and symbols.
- [x] Declarative 100-security scenario contains 100 unique permanent keys and symbols.
- [x] Each size completed two fresh-process in-memory flows through correction.
- [x] Scenario, canonical state, canonical events, and book hashes match across repeats.
- [x] Accounting residual is `0` for both sizes.
- [x] Wall-clock, peak working set, funded positions, events, orders, fills, NAV, and hashes are recorded.
- [x] Existing persistence was probed unchanged.
- [x] Persistence rejection for both diagnostic scenario IDs is recorded as a stop finding.
- [x] Forty malformed 100-security evidence timestamps are recorded as a stop finding.
- [ ] Exact persistence and reopen at 50/100 — blocked by finding.
- [ ] Fresh-process product UI workload at 50/100 — blocked before first executable action.
- [ ] Repeated prospective paper baseline — not started; fixture replay is not prospective evidence.

## Custody decision

- [x] Who, what, when, where, how, and exposure are recorded.
- [x] Credible proprietary-human, proprietary-automated, and client/advisory options are compared.
- [x] Owner-controlled proprietary account with broker custody and human submission is selected provisionally.
- [x] Unresolved Australian legal questions and explicit stop rules are recorded.
- [x] The record states that it is not legal advice or licence clearance.

## Validation

- [x] Focused characterization tests pass.
- [x] Retained 25-security regression tests pass.
- [x] Characterization script reproduces both findings.
- [x] Roadmap and current truth surfaces preserve the accepted score `62/100`.
- [x] P2 Challenger and P3 Limited Live remain closed.
- [ ] Independent Reviewer A/B/C — unavailable in the current execution environment.
- [ ] Current hierarchy confirmation — persisted fallback is stale for this scale/custody scope.

## Stop condition

Preserve P1 as a frozen diagnostic finding with SAW BLOCK. Do not repair storage or timestamp generation inside this spike. Any repair is a separate bounded round and must preserve accepted 10/25 behavior; it must not be represented as reviewed until independent A/B/C and hierarchy closure exist or their risks are explicitly accepted.
