# Handover — GV Engine Scale Characterization 1

Date: 2026-08-01
Status: `FROZEN_FINDING; REVIEW_BLOCKED`
Audience: PM
Diagnostic candidate: `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283`
Accepted score: `62/100`

## Executive Summary (PM-friendly)

The existing engine can deterministically complete synthetic 50- and 100-security flows in memory with exact repeated hashes and zero unexplained accounting residual. The product cannot operate those scenarios because shared persistence recognizes only the accepted 10- and 25-security IDs. At 100 securities, the engine also creates 40 invalid evidence timestamps. The spike stopped as required and did not repair either issue.

The parallel custody track selected a provisional owner-controlled proprietary model: one beneficial owner, broker custody, and human order submission. This is an operational boundary, not legal approval. The diagnostic candidate is frozen and remote-equal, but independent Reviewer A/B/C and a current hierarchy confirmation are unavailable, so SAW is BLOCKED. P2 Challenger and P3 Limited Live remain closed.

## Delivered Scope vs Deferred Scope

### Delivered

- Declarative synthetic 50- and 100-security scenarios.
- Two fresh-process domain measurements at each size.
- Wall-clock, peak working set, positions, events, orders, fills, NAV, residual, and canonical hashes.
- Persistence and timestamp-validity probes.
- Focused tests preserving the findings and retained 25-security behavior.
- Current roadmap/truth alignment.
- One custody and handoff decision record with options, discriminator, unresolved legal questions, and stop rules.

### Deferred

- Scenario-safe shared persistence naming and roots.
- Valid timestamp generation beyond 60 initial evidence rows.
- Product UI operation at 50/100.
- Save/reopen/correction-after-reopen evidence at 50/100.
- Repeated prospective paper-baseline episodes.
- Universe custody, Challenger, broker integration, and Limited Live.

## Derivation and Formula Register

No portfolio formula changed. Measurements use direct elapsed monotonic time, externally polled child-process peak working set, direct collection counts, canonical SHA-256 hashes, and existing accounting residuals.

- Wall-clock: `process_end_monotonic - process_start_monotonic`.
- Peak memory: maximum observed child-process working set.
- Repeat equality: exact equality of scenario, canonical state, canonical event, and book hashes across fresh processes.
- Timestamp validity: ISO 8601 parse success for every timestamp-like field.

Source: `scripts/characterize_gv_engine_scale.py`.

## Logic Chain

```text
Synthetic scenario declaration
→ existing engine flow
→ canonical state/events/book
→ fresh-process repeat comparison
→ unchanged persistence probe
→ timestamp parse probe
→ finding and stop
```

Custody:

```text
one beneficial owner
→ broker custody
→ Terminal Zero paper decision packet
→ human approval/submission
→ broker confirmation
→ certified reconciliation
```

## Evidence Matrix

| Evidence | Result | Artifact |
|---|---|---|
| Focused characterization and operated-product regressions | PASS in split retained runs | `tests/gv_portfolio_v0/test_engine_scale_characterization.py`, `test_operated*.py` |
| 50 fresh-process characterization | deterministic; persistence blocked | `docs/context/e2e_evidence/gv_engine_scale_characterization_1_20260801.md` |
| 100 fresh-process characterization | deterministic; persistence blocked; 40 invalid timestamps | same evidence packet |
| Custody decision | provisional proprietary-human model selected | `docs/context/gv_p1_custody_model_decision.md` |
| Roadmap alignment | P0 terminal, P1 finding, P2/P3 closed | `docs/architecture/top_level_roadmap.md` |

## Open Risks / Assumptions / Rollback

- Storage repair may affect accepted 10/25 path custody; it must be a separate bounded change with regression proof.
- Timestamp repair changes canonical identities because timestamps participate in evidence identity; exact expected migration/compatibility behavior must be decided before implementation.
- Custody selection assumes one Australian beneficial owner and no client/advisory activity; qualified legal review must test the exact facts.
- Independent Reviewer A/B/C and a current scale/custody hierarchy confirmation are unavailable; local self-review cannot substitute for them.
- Rollback is deletion/reversion of the diagnostic scenarios, script, tests, and docs; P0 terminal bytes and tags remain independently immutable.

## Next Phase Roadmap

1. Preserve immutable diagnostic candidate `f9d271d` without moving the terminal tag.
2. Complete independent Reviewer A/B/C and current hierarchy confirmation, or explicitly accept those procedural risks.
3. Select one bounded P1R1 repair decision for shared persistence scenario naming/root selection and monotonic timestamps.
4. Require retained 10/25 regression plus 50/100 save, reopen, correction, and product-path workload proof.
5. Define genuinely prospective paper episodes with new observations; do not count fixture replay.
6. Obtain qualified legal review of the exact owner/entity/broker/communication arrangement.
7. Open P2 only after persistent prospective baseline and custody/legal prerequisites exist.

## NewContextPacket

### What was done

P1 characterized 50/100 with the existing engine, recorded deterministic in-memory behavior, found persistence and timestamp scale limits, and selected a provisional custody model.

### What is locked

P0 terminal candidate, closure, tag, and accepted score `62/100`; no Universe, Challenger, broker, or Limited Live authority.

### What remains

Separate repair, persistent product-path proof, prospective paper episodes, and qualified legal review.

### Immediate first step

Preserve `f9d271d`; close or explicitly accept the review gap before any repair.
