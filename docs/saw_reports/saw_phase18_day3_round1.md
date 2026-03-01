# SAW Report — Phase 18 Day 3 Round 1
Date: 2026-02-20

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops

RoundID: `R18_D3_OVERLAY_20260220`  
ScopeID: `S18_DAY3_CASH_OVERLAY`

## SAW Verdict: ADVISORY_PASS

## Closure Packet (Final)
- ChecksTotal: 10
- ChecksPassed: 9
- ChecksFailed: 1 (`CHK-26: Sharpe Preservation`)
- Verdict: `ADVISORY_PASS`

ClosurePacket: RoundID=R18_D3_OVERLAY_20260220; ScopeID=S18_DAY3_CASH_OVERLAY; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=ADVISORY_PASS; OpenRisks=CHK-26_sharpe_under_target|PytestCacheACLWarning|FeatureStoreLargeINClause; NextAction=Proceed to Day4 company scorecard with TrendSMA200 as locked reference overlay

## Failed Checks (Informative Negative Results)
- `CHK-26: Sharpe Preservation` ❌
  - Target: `Sharpe >= 0.894` (Trend SMA200 reference)
  - Result: `0.761` (Vol Target 15% 20d best in this decision frame)
  - Root cause class: design constraint discovery, not execution defect

## Architectural Discovery
Continuous volatility targeting underperforms discrete binary trend filtering in transaction-cost-constrained environments without leverage.

Evidence frame:
- Vol Target 20d turnover: `8.452 annual` -> `~42 bps` annual cost drag at `5 bps` transaction cost
- Trend SMA200 turnover: `0.123 annual` -> `~0.6 bps` annual cost drag
- Sharpe penalty: `-0.133` (`0.761` vs `0.894`)

Implication:
- This validates Phase 11 `FR-041` governor architecture.
- Discrete 3-state machine (`GREEN/AMBER/RED`) with binary trend filters is superior to continuous scaling under this constraint set.

## Closure Decision
- Proceed to Day 4: `YES`
- Locked reference overlay: `Trend SMA200` (`Sharpe 0.894`, `Ulcer 5.800`)
- Continuous overlay optimization: deferred to Phase 19 (out of critical path)

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Info | `CHK-26` failed under continuous overlay variants due turnover drag. | Reframe as design discovery and lock discrete governor reference overlay. | Strategy/Ops | Closed |
| Low | `.pytest_cache` ACL warning on Windows (`WinError 5`) persists. | Infra permission cleanup outside Day 3 critical path. | Infrastructure | Open |
| Medium (Inherited, out-of-scope) | `data/feature_store.py` large literal `IN (...)` can degrade at very large universes. | Temp-table join migration in future optimization milestone. | Data/Ops | Open |

## Scope Split Summary
In-scope findings/actions:
- Day 3 implementation verified.
- Negative hypothesis result formally documented as architectural validation.
- Day 4 progression explicitly approved.

Inherited out-of-scope findings/actions:
- Feature-store large literal `IN (...)` query performance path remains tracked.

## Document Changes Showing
- `docs/saw_phase18_day3_round1.md` — verdict/frame updated to `ADVISORY_PASS`; reviewer status: Closed.
- `docs/phase18-brief.md` — Day 3 reframed as complete with informative failure; reviewer status: Closed.
- `docs/decision log.md` — D-97 updated to lock Trend SMA200 reference overlay; reviewer status: Closed.
- `docs/lessonss.md` — added negative-results architectural-learning entry; reviewer status: Closed.

Open Risks:
- `CHK-26` remains below target under continuous overlays.
- Non-blocking `.pytest_cache` ACL warning.
- Inherited feature-store large `IN (...)` performance risk.

Next action:
- Execute Day 4 company scorecard implementation using Trend SMA200 as locked top-level overlay reference.

ClosureValidation: N/A (operator-overridden advisory closure)  
SAWBlockValidation: N/A (operator-overridden advisory closure)
