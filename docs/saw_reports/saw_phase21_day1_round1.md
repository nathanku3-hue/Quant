# SAW Report — Phase 21 Day 1 Round 1
Date: 2026-02-20

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase21-brief.md`

RoundID: `R21_D1_STOPLOSS_20260220`  
ScopeID: `S21_DAY1_STOPLOSS_MODULE`

## Scope and Ownership
- Scope: implement standalone stop-loss/drawdown module, add unit coverage, and publish Phase 21 Day 1 docs-as-code updates.
- Owned files:
  - `strategies/stop_loss.py`
  - `tests/test_stop_loss.py`
  - `docs/phase21-brief.md`
  - `docs/runbook_ops.md`
  - `docs/notes.md`
  - `docs/decision log.md`
  - `docs/lessonss.md`
  - `docs/prd.md`
  - `docs/spec.md`
  - `docs/saw_phase21_day1_round1.md`
- Acceptance checks:
  - CHK-101..CHK-108 (Phase 21 Day 1 brief contract).

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c798f-cf53-7063-bdb4-38f01a806190`
- Reviewer B: `019c798f-cf6e-70b2-88fa-1915158ee8c6`
- Reviewer C: `019c7990-04ea-7f40-ad61-77ffacf0332c`
- Independence: PASS

## Top-Down Snapshot
L1: Stop-Loss & Drawdown Control
L2 Active Streams: Backend, Data, Ops
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+--------------------------------------------------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope                                                | Rating | Next Scope                                                   |
+--------------------+--------------------------------------------------------------+--------+--------------------------------------------------------------+
| Planning           | Boundary=module+tests+docs; Owner/Handoff=Impl->Rev A/B/C;  | 100/100| 1) Move to Day 2 integration wiring [88/100]: Day 1 module  |
|                    | Acceptance Checks=CHK-101..CHK-108                          |        | contract is stable and validated.                            |
| Executing          | Implement ATR/stop/drawdown module and tests                | 100/100| 1) Add runtime wiring with feature gate [84/100]: preserve  |
|                    |                                                              |        | current standalone behavior while integrating safely.         |
| Iterate Loop       | Reviewer A/B/C findings reconciled                           | 100/100| 1) Track medium design note on trailing anchor [79/100]:     |
|                    |                                                              |        | validate in integration simulation before changing behavior.  |
| Final Verification | Compile + pytest + docs + SAW validators                    | 100/100| 1) Proceed to Phase 21 Day 2 gate [90/100]: all Day 1 checks |
|                    |                                                              |        | passed and docs/runbook updated.                             |
+--------------------+--------------------------------------------------------------+--------+--------------------------------------------------------------+

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Reviewer A noted trailing candidate currently anchored to `current_price`, while `highest_price` is tracked but not used; this may tighten stops on rebounds. | Accepted by design for Day 1 because architecture ruling specified `price_t - K*ATR_t`; carry as Day 2 evaluation note. | Strategy | Open (Accepted) |
| High | Reviewer B flagged missing activation gate for live integration. | Added explicit Day 2 integration gate + owner/handoff + prerequisites in brief/runbook/decision log. | Ops | Closed |
| Medium | Reviewer B flagged missing runtime observability and rollback steps for future activation. | Added runtime checks/alerts and rollback procedure to runbook Section 4g. | Ops | Closed |
| Info | Reviewer C found formula/value consistency across code, notes, spec, and tests. | No action required. | Data | Closed |

## Scope Split Summary
In-scope findings/actions:
- Implemented stop-loss module and tests.
- Added Phase 21 Day 1 brief and formula documentation.
- Updated runbook, decision log, lessons, prd/spec addendum.
- Reconciled reviewer B operational findings to closed.

Inherited out-of-scope findings/actions:
- Live runtime integration wiring remains deferred by scope boundary to Phase 21 Day 2.

## Document Changes Showing
Code/Test:
- `strategies/stop_loss.py` — ATR proxy, stop manager, drawdown monitor, factory; reviewer status: A reviewed.
- `tests/test_stop_loss.py` — 18-unit test contract for Day 1 stop-loss behavior; reviewer status: A/C reviewed.

Docs (GitHub-optimized order):
- `docs/prd.md` — Phase 21 Day 1 stop-loss requirement addendum; reviewer status: C reviewed.
- `docs/spec.md` — Phase 21 Day 1 module contract addendum; reviewer status: C reviewed.
- `docs/phase21-brief.md` — Day 1 summary, checks, and Day 2 integration gate; reviewer status: B reviewed.
- `docs/runbook_ops.md` — Section 4g validation, activation gate, observability, rollback; reviewer status: B reviewed.
- `docs/notes.md` — explicit formulas + file mapping for stop-loss module; reviewer status: C reviewed.
- `docs/lessonss.md` — Day 1 lesson entry.
- `docs/decision log.md` — D-102 decision and mitigation gate.

## Check Results
- CHK-101: PASS
- CHK-102: PASS
- CHK-103: PASS
- CHK-104: PASS
- CHK-105: PASS
- CHK-106: PASS
- CHK-107: PASS
- CHK-108: PASS

ChecksTotal: 8  
ChecksPassed: 8  
ChecksFailed: 0

SAW Verdict: PASS

Open Risks:
- Medium accepted: trailing-stop anchor choice (`current_price` vs `highest_price`) should be re-evaluated during Day 2 integration backtests.
- Environment warning persists: `.pytest_cache` ACL warning on Windows (non-blocking).

Next action:
- Start Phase 21 Day 2 integration wiring with feature-gated activation and runtime observability checks.

ClosurePacket: RoundID=R21_D1_STOPLOSS_20260220; ScopeID=S21_DAY1_STOPLOSS_MODULE; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=medium trailing-anchor design note and non-blocking pytest cache ACL warning; NextAction=phase21 day2 integration wiring with feature-gated activation

ClosureValidation: PASS
SAWBlockValidation: PASS

