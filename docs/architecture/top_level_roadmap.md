# GodView Top-Level Roadmap

Status: `P0 TERMINAL; SCALE REPAIR BANKED; PROSPECTIVE IMPLEMENTATION CANDIDATE; CHALLENGER/LIVE CLOSED`
Date: 2026-08-02
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Frozen original detail: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF`
Accepted endgame progress: `62/100`

## Binding state

```text
BASE = REPAIR_5687a2c_FROM_TERMINAL_MAIN_e564cd9
ACCEPTED_TERMINAL_PRODUCT = GV-OPERATED-PORTFOLIO-25-1
ACTIVE_PRODUCT_PHASE = GV-OPERATED-PORTFOLIO-25-1
ACTIVE_IMPLEMENTATION_PHASE = GV-PROSPECTIVE-PAPER-BASELINE-1
HISTORICAL_DIAGNOSTIC_PHASE = GV-ENGINE-SCALE-CHARACTERIZATION-1
DIAGNOSTIC_CANDIDATE = f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283
DIAGNOSTIC_STATUS = HISTORICAL_FROZEN_FINDING; REPAIR_COMPLETED_AT_5687a2c
ACCEPTED_PRODUCT = SLICE_0
ACCEPTED_INTEGRITY = REPLAY_0
UNIVERSE_SCALE = NOT_ACCEPTED
CHALLENGER = CLOSED
LIMITED_LIVE = CLOSED; NOT_AUTHORIZED
ROOT_CHECKOUT = UNSAFE; DO_NOT_USE
```

The accepted 25-security product remains terminal and immutable. The scale characterization is historical diagnostic custody; its two defects are repaired at `5687a2c`. `GV-PROSPECTIVE-PAPER-BASELINE-1` is the active implementation candidate and is not yet score-bearing prospective evidence. The terminal tag `gv-operated-portfolio-25-1-terminal` remains fixed at closure commit `e564cd9dfa45eb02ef8d7eb94b662543fb3776c9`.

## Accepted Slice 0 foundation — historical authority seams

The accepted Slice 0 product foundation remains binding as historical interface ancestry:

```text
InstrumentId
→ PortfolioBookEvent
→ DecisionSnapshotId
→ PortfolioAimId
→ CertificationId
```

`GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` remains an accepted historical terminal. `GV-OPERATED-PORTFOLIO-25-1` remains the accepted current product terminal. Replay 0 remains the accepted integrity foundation.

## Immutable accepted custody

The ten-security product remains historically certified by:

- executable candidate `0d15e9c59c6b3ca051b3aa815018889d1e94857f`;
- documentation-only closure `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e`;
- tag `gv-operated-portfolio-10-transition-1r-terminal`.

The 25-security product remains certified by:

- executable candidate `7ce85c41e9c3b6492ec884a69dc7857538386ba2`;
- documentation-only closure `e564cd9dfa45eb02ef8d7eb94b662543fb3776c9`;
- tag `gv-operated-portfolio-25-1-terminal`.

No P1 commit may amend, retarget, recreate, or move either terminal tag.

## Truthful classification

| Scope | Current classification | Decision |
|---|---|---|
| Slice 0 | accepted product foundation | retained |
| Replay 0 | accepted integrity foundation | retained |
| Operated 10 | immutable accepted historical terminal | retained |
| Operated 25 | immutable accepted current terminal | retained at `62/100` |
| 50-security engine stress | deterministic in memory; persistence/product path blocked | finding only |
| 100-security engine stress | deterministic in memory; persistence blocked; timestamps malformed | finding only |
| Universe Scale | survivorship-safe membership, actions, snapshots, and history unproven | closed |
| Challenger | baseline → shadow → prospective → replication → bounded authority incomplete | closed |
| Limited Live | legal/custody/pilot prerequisites incomplete | closed and unauthorized |

Sessions, cells, runs, slots, copied portfolios, and repeated executions never count as distinct securities.

## P1 — Engine scaling characterization

The authorized diagnostic sequence was:

```text
existing accepted 25-security engine
→ declarative 50-security synthetic scenario
→ two fresh-process domain runs
→ persistence/reopen probe
→ declarative 100-security synthetic stress scenario
→ two fresh-process domain runs
→ persistence/reopen and timestamp-validity probes
→ measure
→ stop on required repair
```

### Result

- Frozen diagnostic candidate `f9d271d` identified two substrate defects: scenario-closed persistence and invalid timestamps beyond minute 59.
- Repair candidate `5687a2c2ae61ef8b5de676cffad5b19df9224b01` fixes both defects while preserving exact 10/25 storage names and roots.
- Registered 50/100 scenarios now persist, reopen, correct, replay, and retain residual `0`; UTC timestamps roll over correctly.
- The repair remains infrastructure evidence and does not change the accepted score.

## Active implementation — GV-PROSPECTIVE-PAPER-BASELINE-1

`ACTIVE_IMPLEMENTATION_PHASE = GV-PROSPECTIVE-PAPER-BASELINE-1`

The prospective candidate derives from the accepted 25-security catalogue and bootstraps the certified funded portfolio. It accepts runtime observation content, source locator, UTC timestamp, owned instruments, explicit outcome/score/quantity/thesis proposals, and operator rationale. Preview is mutation-free; only explicit confirmation grants authority. Explicit rejection is append-only and cannot mutate evidence, reviews, snapshots, holdings, cash, orders, fills, or book economics.

The same event/state projector supports:

```text
runtime no-change confirmation
→ runtime SELL/REDUCE plus BUY/FUND transition
→ runtime proposal rejection
→ atomic persist
→ fresh-process reopen
→ exact full-state reconstruction
```

Automated tests inject runtime values and prove the capability path, not genuine prospective evidence. Accepted score remains `62/100`.

## Parallel custody decision

The provisional selected model remains:

```text
one beneficial owner
→ one owner-controlled proprietary account
→ regulated broker/custodian holds cash and securities
→ Terminal Zero produces paper decisions and certified records
→ human owner/approver reviews and submits every order
→ broker confirmations reconcile back to certified records
```

No client assets, pooled capital, discretionary activity for another person, public advice, system-held brokerage credentials, or autonomous order submission is permitted. Qualified Australian legal review and broker approval remain prerequisites before broker credentials, automated submission, client assets, advice activity, or real-capital operation. They are not blockers for paper baseline or paper Challenger work.

## P2 — Challenger comparison

P2 opens only after genuine operator-supplied prospective baseline evidence exists on the certified 25-security opportunity set. Universe custody and legal review are not mandatory predecessors to paper Challenger comparison.

The comparison sequence is:

```text
certified prospective baseline
→ independent shadow challenger proposal
→ prospective challenger
→ independent replication
→ bounded authority decision
```

The challenger must consume the same runtime observation envelope and share the baseline custody boundary, costs, workload measurement, and operating conditions. The obsolete slot/cell Challenger harness is historical only and must be replaced rather than adapted.

## P3 — Limited Live

Limited Live remains closed until custody and legal responsibilities are resolved, prospective paper operation is stable, exact replay and reconciliation remain proven, realistic cost/liquidity evidence exists, and a separately authorized pilot is small, liquid, long-only, unleveraged, supervised, and reversible.

No responsible score forecast is recorded for Limited Live.

## Next boundary

```text
preserve frozen remote candidate `9c7e75a`
→ exact-SHA hosted CI
→ three genuine operator-supplied prospective episodes
→ real shadow Challenger on the same 25-security set
→ Universe custody when broader membership is required
→ separately authorized Limited Live
```

Provider acquisition, optimizer frameworks, broker integration, client assets, autonomous orders, alpha claims, score uplift, and Limited Live remain prohibited until separately authorized.
