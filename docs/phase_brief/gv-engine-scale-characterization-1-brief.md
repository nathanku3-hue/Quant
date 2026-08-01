# Phase Brief — GV-ENGINE-SCALE-CHARACTERIZATION-1

Date: 2026-08-01
Status: `FROZEN_FINDING; REVIEW_BLOCKED; NO_REPAIR_IN_THIS_PHASE`
Terminal base: `e564cd9dfa45eb02ef8d7eb94b662543fb3776c9`
Diagnostic candidate: `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283`
Diagnostic candidate tree: `e048f2483c64fcf7a9cae58e8454b70d7e993e78`
Immutable terminal tag: `gv-operated-portfolio-25-1-terminal`
Accepted score: `62/100`
Primary authority: `docs/context/gv_endgame_authority_current.md`
Custody decision: `docs/context/gv_p1_custody_model_decision.md`

## Objective

Time-box the existing operated engine at declarative 50- and 100-security synthetic scenarios, measure the current boundary without adding a parallel engine, storage path, schema family, application, or view, and stop if repair or redesign is required.

The 100-security scenario is diagnostic engine stress only. It is not Universe acceptance and does not prove survivorship-safe membership, corporate-action custody, historical universe snapshots, alpha, challenger quality, or live-capital readiness.

## Functional sequence

```text
immutable 25-security terminal
→ declarative 50-security synthetic scenario
→ two fresh-process deterministic domain runs
→ persistence/reopen probe
→ declarative 100-security synthetic stress scenario
→ two fresh-process deterministic domain runs
→ persistence/reopen and timestamp-validity probes
→ measure and report
→ stop on required repair
```

## Architecture boundary

The phase adds scenario declarations and a diagnostic harness only. Selection, funding, execution, accounting, replay, certification, correction, and validation remain in the accepted shared engine. The existing persistence implementation is probed unchanged. No alternate storage, engine, UI, compatibility adapter, provider, broker, or live path is added.

## Measured result

| Measure | 50 securities | 100 securities |
|---|---:|---:|
| Fresh-process runs | 2 | 2 |
| In-memory status | `CORRECTED_CERTIFIED` | `CORRECTED_CERTIFIED` |
| Wall-clock | 6.43–6.45 s | 11.77–11.96 s |
| Peak working set | 30.1–30.3 MB | 32.3–32.4 MB |
| Funded positions | 17 | 33 |
| Events | 48 | 80 |
| Orders / fills | 18 / 18 | 34 / 34 |
| Unexplained residual | `0` | `0` |
| State/event/book/scenario repeat equality | PASS | PASS |
| Timestamp validity | PASS | FAIL: 40 malformed timestamps |
| Persistence, save, reopen | FAIL before write | FAIL before write |
| Product operator path | NOT EXECUTABLE | NOT EXECUTABLE |

The in-memory domain sequence remains four transitions and declares zero per-security confirmation requirements. Those facts are not accepted as an operational workload result because the existing product path cannot persist either new scenario and therefore cannot complete save/reopen or a real UI operation.

## Stop findings

### F1 — Persistence scenario identity is closed over 10 and 25

`gv_portfolio_v0.operated_storage._workspace_filename()` accepts only the retained 10-security and accepted 25-security scenario IDs. Both diagnostic scenarios fail immediately with:

```text
OperatedPortfolioError:UNKNOWN_OPERATED_SCENARIO:GV_ENGINE_SCALE_CHARACTERIZATION_50
OperatedPortfolioError:UNKNOWN_OPERATED_SCENARIO:GV_ENGINE_SCALE_CHARACTERIZATION_100
```

Persistence size, save duration, reopen duration, correction-after-reopen, and fresh-process product operation are therefore unavailable. Repair would change shared storage behavior and is outside this spike.

### F2 — Initial evidence timestamps stop being valid after index 59

The existing engine formats initial evidence times as one fixed hour plus the instrument index as the minute. At 100 securities, indices 60–99 produce 40 invalid timestamps from `12:60` through `12:99`. Repair would change shared engine behavior and is outside this spike.

## Acceptance disposition

| Acceptance condition | Result |
|---|---|
| No more than four required operator actions | NOT ACCEPTED; product path is not executable |
| Zero per-security confirmations | NOT ACCEPTED operationally; declarative contract remains zero |
| Deterministic hashes across fresh processes | PASS |
| Zero unexplained accounting residual | PASS |
| Exact persistence and reopen | FAIL |
| Correction and fresh-process reopen | FAIL at persistence boundary |
| No parallel engine, storage, or view | PASS |
| No feature or architecture expansion | PASS |
| Operationally bounded workload | NOT ACCEPTED |

The spike verdict is `FINDING`, not product acceptance. The diagnostic implementation is frozen at `f9d271d`, but phase review remains blocked because independent Reviewer A/B/C and a current hierarchy confirmation are unavailable. The accepted score remains `62/100`.

## Parallel custody decision

The selected provisional operating model is owner-controlled proprietary activity in one beneficially owned account, with a regulated broker/custodian holding cash and securities and a human owner/approver entering or submitting every order. Terminal Zero remains a paper decision, certification, and audit system; it does not hold client assets, broker credentials, or autonomous order authority.

This selection is not legal clearance. Client assets, advisory or discretionary operation for another person, pooled capital, public recommendations intended to influence product decisions, system-held brokerage credentials, or automated order submission are explicit stop conditions pending qualified Australian legal advice and broker approval.

## Prospective baseline disposition

Repeated prospective paper-baseline operation did not start. Repeating the same deterministic fixture would be replay evidence, not prospective evidence, and the 50/100 product path cannot persist or reopen. P2 Challenger comparison therefore remains closed.

## Forbidden scope

Do not repair storage or timestamp generation in this phase. Do not claim Universe Scale, challenger acceptance, alpha, legal clearance, AFS-licence exemption, brokerage readiness, Limited Live, or score uplift. Never move or recreate `gv-operated-portfolio-25-1-terminal`.

## Next valid decision

After this frozen finding is independently reviewed or its review risk is explicitly accepted, the harness may separately select one bounded repair round covering only:

1. scenario-safe shared persistence naming/root selection without parallel storage; and
2. valid monotonic evidence timestamp generation beyond 60 instruments.

That repair must preserve 10/25 behavior and must complete persistence, reopen, correction, and product-path workload evidence before prospective baseline operation or P2 can open.

## New Context Packet

## What Was Done

- Characterized synthetic 50- and 100-security scenarios through the existing engine in two fresh processes each.
- Recorded deterministic hashes, accounting, timing, peak working set, event/order/fill counts, and timestamp validity.
- Probed existing persistence unchanged and stopped when both scale scenarios were rejected before write.
- Recorded the 100-security malformed timestamp boundary.
- Selected a provisional owner-controlled proprietary custody model with broker custody and human order submission.

## What Is Locked

- Prior terminal `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` remains immutable.
- P0 25-security terminal `GV-OPERATED-PORTFOLIO-25-1`, its candidate, closure, terminal tag, and accepted score `62/100` remain immutable.
- P1 is a diagnostic finding, not Portfolio Scale or Universe acceptance.
- No repair is included in this phase.
- P2 Challenger and P3 Limited Live remain closed.

## What Is Next

- Preserve diagnostic candidate `f9d271d`; do not amend or recut it.
- Complete independent Reviewer A/B/C and current hierarchy confirmation, or record explicit acceptance of those procedural risks.
- Separately select one bounded repair for scenario-safe shared persistence and valid monotonic timestamps.
- Require retained 10/25 regression plus 50/100 persistence, reopen, correction, product workload, and prospective paper evidence before P2.

## First Command

```text
git status --short
```
