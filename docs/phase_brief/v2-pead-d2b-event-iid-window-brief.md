# V2 PEAD D2B Event-IID Window Closure Brief

Mode: `CLOSURE_REPORT`
Status: Bounded D2B Data slice DONE; final Reviewer A/B/C PASS; PEAD phase remains open
Date: 2026-06-19
RoundID: `ROUND-20260619-V2-D2B-EVENT-IID-WINDOW`
ScopeID: `V2_D2B_FIXED_EVENT_SECURITY_PLUS_60_SAMPLE`
Owner: Data + Docs/Ops

## 2026-06-19 market-session spine repair addendum

The original D2B artifact below remains historical evidence, but its session
spine is superseded. The corrected D2B manifest now uses 2,810 authoritative
Ken French daily factor dates instead of all 2,862 distinct D2A dates, excludes
52 market-closed dates, and points to immutable Parquet SHA256
`c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`.
Event/row counts remain 12,582 / 754,920; eligible handoffs are now 11,450.
The fixed-security selection formula is unchanged. See
`docs/phase_brief/v2-pead-d2b-session-spine-repair-brief.md`.

## Objective and boundary

Close the bounded 500-GVKEY D2B Data slice: choose one fixed security per event from pre-event liquidity, retain an exact global `+1..+60` session skeleton, publish a hash-addressed artifact behind an atomic manifest pointer, and prove the existing strategy adapter consumes the handoff without implementing another window algorithm.

This closure does not close PEAD and does not authorize provider access, benchmark acquisition/implementation, CAR or alpha interpretation, dashboard work, candidate ranking/scoring, alerts, broker/order paths, a full build, staging, or commit.

## Acceptance criteria

- [x] The prior 20 global sessions are strictly before each event; finite `dollar_volume` count is at least 15 and the score is the arithmetic mean of finite values.
- [x] Deterministic order is score descending, observation count descending, normalized `iid` ascending, then `security_id` ascending.
- [x] One event-level security is fixed for all 60 rows; there is no `IID01` preference, fallback, or switch.
- [x] Event day `+1` is the first global session strictly after the event and every event retains exactly `+1..+60`; missing rows remain missing without imputation or a delisting label.
- [x] `handoff_eligible` requires all 60 dates and all 60 finite returns for the fixed security.
- [x] Input validation/read is bound to stable hash-validated byte snapshots; output publication is immutable Parquet then atomic manifest, with pre-commit `BaseException` cleanup and one D2A normalization.
- [x] Strategy adapter uses 4,867 eligible D2B events, 881,588 unique canonical return rows, zero duplicate keys, and the identical global session spine; 292,020 complete strategy-window rows are produced by the canonical strategy algorithm.
- [x] Artifact evidence: 12,582 events, 362 issuers, 754,920 rows, 12,568 selected, 14 no-security, 522 short, 7,179 missing/non-finite, 4,867 eligible, 2,862 sessions from 2015-01-02 through 2026-03-06, SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`.
- [x] Tests pass: 26 D2B tests and 58 combined D2B/D2A/strategy tests.
- [x] Reviewer A/B initial High findings for overlapping-event return-key duplication and input hash-then-reopen TOCTOU are resolved in code/tests.
- [x] Final Reviewer A/B/C reconciliation PASS: A 11/11, B 10/10, C 12/12; no Critical/High finding remains open.

## Live loop

| Loop state | Result |
|---|---|
| Implement | Complete in `scripts/pead_d2b_event_window_contract.py` |
| Focused verification | 26 passed |
| Combined verification | 58 passed |
| Full-sample strategy smoke | 4,867 events; 881,588 unique return rows; 0 duplicate keys; 292,020 complete rows |
| Review reconciliation | Final Reviewer A/B/C PASS; both initial High findings and all in-scope Medium findings resolved |
| Docs/Ops closure | Product/spec/formula/decision/lesson/runbook/current truth refreshed and context packet rebuilt |

## Ship-Fast Decision Gate

Reference: `docs/templates/ship_fast_decision_gate.md`.

- What is done: the bounded D2B fixed-security event-window artifact, tests, strategy adapter smoke, and Docs/Ops closure evidence.
- What is blocked: all downstream benchmark/provider/interpretation/product work; final reviewer promotion is complete for this bounded D2B slice.
- User order interpreted as: close D2B only and preserve every downstream authorization boundary.
- Why this is correct: D2B has direct manifest, test, and full-sample adapter evidence; downstream benchmark semantics are a separate decision.
- Scope limit: this brief and the owned Docs/Ops truth surfaces only; no code, tests, data, or SAW report edits.
- Stop rule: stop if D3 requires provider access, benchmark acquisition, CAR/alpha interpretation, or any implementation outside a separately approved contract gate.
- Single next decision/action: approve or hold a bounded D3 benchmark-input contract/design gate, with no provider fetch or alpha interpretation.

## Risk and rollback

- Final-review assurance is closed for the bounded D2B slice; this must still not be described as PEAD phase-end.
- Missing selected-security returns and short global spines are retained and explicitly ineligible; they are not silently repaired.
- Rollback the active D2B output by atomically restoring the prior known-good manifest bytes. Because Parquet objects are immutable and hash named, do not delete either referenced object during rollback; validate the restored manifest SHA and row counts before readers resume.
