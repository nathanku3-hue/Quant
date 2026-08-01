# GodView Top-Level Roadmap

Status: `P0 TERMINAL; P1 FROZEN FINDING / REVIEW BLOCKED; P2/P3 CLOSED`
Date: 2026-08-01
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Frozen original detail: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF`
Accepted endgame progress: `62/100`

## Binding state

```text
BASE = TERMINAL_MAIN_e564cd9
ACCEPTED_TERMINAL_PRODUCT = GV-OPERATED-PORTFOLIO-25-1
ACTIVE_PRODUCT_PHASE = GV-OPERATED-PORTFOLIO-25-1
ACTIVE_DIAGNOSTIC_PHASE = GV-ENGINE-SCALE-CHARACTERIZATION-1
DIAGNOSTIC_CANDIDATE = f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283
DIAGNOSTIC_STATUS = FROZEN_FINDING; REVIEW_BLOCKED; NO_REPAIR_IN_PHASE
ACCEPTED_PRODUCT = SLICE_0
ACCEPTED_INTEGRITY = REPLAY_0
UNIVERSE_SCALE = NOT_ACCEPTED
CHALLENGER = CLOSED
LIMITED_LIVE = CLOSED; NOT_AUTHORIZED
ROOT_CHECKOUT = UNSAFE; DO_NOT_USE
```

The accepted 25-security product remains terminal and immutable. P1 is a diagnostic successor, not a replacement product terminal and not a score-bearing product gate. The terminal tag `gv-operated-portfolio-25-1-terminal` remains fixed at closure commit `e564cd9dfa45eb02ef8d7eb94b662543fb3776c9`.

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

- 50 securities: two fresh-process in-memory runs complete correction with identical scenario, state, event, and book hashes; residual is `0`; 48 events and 18 orders/fills; wall-clock 6.43–6.45 seconds; peak working set 30.1–30.3 MB.
- 100 securities: two fresh-process in-memory runs complete correction with identical hashes; residual is `0`; 80 events and 34 orders/fills; wall-clock 11.77–11.96 seconds; peak working set 32.3–32.4 MB.
- Existing persistence rejects both diagnostic scenario IDs before writing, so save size, save duration, reopen duration, correction-after-reopen, and executable product workload are unavailable.
- The existing initial-evidence timestamp formatter produces 40 invalid timestamps at 100 securities, from minute `60` through `99`.

This is a frozen `FINDING` at candidate `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283`, not an accepted product gate. Independent Reviewer A/B/C and a current hierarchy confirmation remain unavailable, so SAW is BLOCKED. It does not accept 50-security Portfolio Scale and does not accept 100-security Universe Scale.

## Parallel custody decision

The provisional selected model is:

```text
one beneficial owner
→ one owner-controlled proprietary account
→ regulated broker/custodian holds cash and securities
→ Terminal Zero produces paper decisions and certified records
→ human owner/approver reviews and submits every order
→ broker confirmations reconcile back to certified records
```

No client assets, pooled capital, discretionary activity for another person, public advice, system-held brokerage credentials, or autonomous order submission is permitted. The model is an operational boundary, not legal advice or a licence determination. Qualified Australian legal review and broker approval remain prerequisites before any real-capital pilot.

## P2 — Challenger comparison

P2 remains closed. It may open only when both exist:

1. a persistent, reopenable, measured operating baseline with repeated prospective paper episodes; and
2. a legally reviewed custody and authority model applicable to the exact operator/entity/broker arrangement.

The comparison sequence remains:

```text
certified baseline
→ shadow challenger
→ prospective challenger
→ independent replication
→ bounded authority decision
```

The challenger must share the baseline custody boundary, costs, workload measurement, and operating conditions.

## P3 — Limited Live

Limited Live remains closed until custody and legal responsibilities are resolved, prospective paper operation is stable, exact replay and reconciliation remain proven, realistic cost/liquidity evidence exists, and a separate pilot is small, liquid, long-only, unleveraged, supervised, and reversible.

No responsible score forecast is recorded for Limited Live.

## Next boundary

First close or explicitly accept the procedural review gap for frozen diagnostic candidate `f9d271d`. The next valid implementation decision is then a separate bounded repair round, not implementation inside this spike. Its maximum scope is:

- scenario-safe shared persistence naming/root selection without parallel storage; and
- valid monotonic evidence timestamps beyond 60 instruments.

P2, Universe acceptance, provider acquisition, optimizer work, broker integration, alpha claims, and Limited Live remain prohibited until the repaired product path passes persistence, fresh-process reopen, correction, workload, and prospective-baseline evidence.
