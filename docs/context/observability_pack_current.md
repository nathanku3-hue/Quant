# Observability Pack — Current

Date: 2026-08-01
Phase: `GV-ENGINE-SCALE-CHARACTERIZATION-1`
Status: `FROZEN_FINDING; REVIEW_BLOCKED`
Accepted score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Immutable sentinels

- P0 terminal closure and `gv-operated-portfolio-25-1-terminal` must remain at `e564cd9`.
- Accepted score remains `62/100`.
- Retained 10/25 scenarios must continue through one engine, persistence implementation, app, and view.
- Diagnostic candidate `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283` is immutable and remote-equal.
- The scale scenarios are synthetic diagnostics, not accepted securities custody.

## Characterization sentinels

- 50 identities and permanent keys are unique; two fresh-process state/event/book/scenario hash sets are equal.
- 100 identities and permanent keys are unique; two fresh-process state/event/book/scenario hash sets are equal.
- Accounting residual remains `0` at both sizes.
- Peak working set remains externally measured, not inferred from object size.
- Persistence rejection occurs before write for both diagnostic IDs.
- 100-security timestamp issue count is exactly 40, beginning at `12:60`.
- Product workload must not be reported as accepted while persistence prevents the product path from starting.

## Custody sentinels

- One beneficial owner only.
- Broker/custodian retains cash, securities, account ledger, and executed-order authority.
- Human owner approves and submits every real order.
- Terminal Zero stores no broker credentials and submits no real order.
- Any client/advisory/discretionary/pooled/public-recommendation use triggers legal and scope stop.

## Current signal

- **GREEN:** declarative scenario uniqueness, existing-engine in-memory completion, repeat equality, residual `0`, accepted-25 regression, no parallel architecture.
- **AMBER:** custody direction is selected but qualified legal review and exact broker terms remain open; independent Reviewer A/B/C and current hierarchy confirmation are unavailable.
- **RED:** scale persistence/reopen unavailable; 100-security timestamps invalid; prospective paper evidence absent.
- **STOP:** representing P1 as reviewed or accepted, amending `f9d271d`, repair inside this spike, Universe/Challenger claims, score uplift, broker integration, automated orders, client assets, Limited Live, or terminal-tag movement.
