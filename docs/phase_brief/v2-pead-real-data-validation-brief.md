# V2 PEAD Real-Data Validation

Mode: `EXECUTION_PACKET`
Status: `DONE`
Date: 2026-06-20
RoundID: `ROUND-20260620-V2-PEAD-REAL-DATA-VALIDATION`
ScopeID: `V2_PEAD_CAR_BHAR_QUINTILE_REAL_DATA_VALIDATION`
Owner: Strategy + Data + Docs/Ops

Hierarchy: L1 Terminal Zero quantitative research console; L2 active streams Strategy, Data, and Docs/Ops; L2 deferred stream Frontend/UI; L3 Closed -> Owner Review.

## Objective

Produce one reproducible, atomic, numbers-only JSON artifact from the published
D1/D2B/D3 sample lineage so the owner can decide whether dashboard scoping has
enough evidence to open as a separate round.

## Ship-Fast Decision Gate

Reference: `docs/templates/ship_fast_decision_gate.md`.

- What is done: D3 artifact-to-strategy handoff is validated and its 26-test
  regression passed before this round.
- What is blocked: owner review lacks reproducible real-data CAR/BHAR/quintile
  numbers; dashboard scoping therefore remains unopened.
- User order interpreted as: run one bounded PEAD real-data sample validation,
  publish one atomic numbers-only JSON, run focused tests and full SAW, and make
  no interpretation or dashboard changes.
- Recommended next step: execute this validation and return the artifact for
  owner review.
- Why this is correct: it is the smallest evidence-producing action between the
  completed D3 handoff and a separate dashboard-scoping decision.
- Alternatives considered: direct dashboard scoping, strategy promotion, or an
  ad hoc console dump; all are rejected by the approved boundary.
- Decision needed from user: `APPROVED` by the explicit `go` instruction.
- Scope limit: one script, one focused test module, one JSON artifact, and
  required documentation/SAW evidence only.
- Stop rule: halt on lineage/hash mismatch, partial/corrupt bundle, row or join
  drift, strict-JSON failure, non-atomic output, or formula/configuration drift.

## Approved scope

- Read and hash-validate the published D1, D2B, and D3 bundles.
- Preserve the D2B-to-D3 `return_date` many-to-one, row-preserving join.
- Use the existing `summarize_event_windows` and
  `summarize_quantile_performance` strategy path without changing formulas.
- Publish event-date CAR/BHAR quintile evidence with locked fail-closed HAC gap
  behavior.
- Publish quarterly CAR/BHAR quintile evidence with
  `ex_post_descriptive_only = true`.
- Atomically write
  `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.

## Acceptance criteria

- [x] Script exists at `scripts/pead_real_data_validation.py`.
- [x] Focused tests exist at `tests/test_pead_real_data_validation.py` and pass.
- [x] JSON records D1/D2B/D3 manifest and Parquet lineage hashes.
- [x] JSON records the exact event-date and quarterly strategy configurations.
- [x] JSON records event, issuer, eligibility, and coverage-reason counts.
- [x] JSON records CAR and BHAR quantile summaries, cohort spreads, requested and
      used HAC lags, HAC gaps, standard errors, and t-statistics.
- [x] Event-date HAC gaps remain visible and its HAC standard error/t-statistic
      remain null when the locked fail-closed rule applies.
- [x] Quarterly output is explicitly labeled `ex_post_descriptive_only = true`.
- [x] JSON is strict JSON, deterministic for fixed inputs, and written by
      same-directory temporary file followed by atomic replace.
- [x] Limitations explicitly include the 500-GVKEY sample, current-vintage EPS,
      Compustat return proxy, and no delisting adjustment.
- [x] Focused PEAD regression and CLI runtime evidence pass.
- [x] Independent Reviewer A/B/C and SAW validators pass with no unresolved
      in-scope Critical/High findings.

## Closeout evidence

- Published JSON:
  `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.
- JSON SHA256:
  `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- Deterministic rerun: same SHA256 and 1,729,927 bytes.
- Counts: 754,920 rows, 12,582 events, 362 issuers, 11,450 eligible events,
  1,132 ineligible events.
- Event-date output: `cohort_frequency = "D"`, CAR/BHAR each have 2,777 HAC
  gaps, `hac_maxlags_used = 0`, and null HAC standard error/t-statistic.
- Quarterly output: `cohort_frequency = "Q"`,
  `ex_post_descriptive_only = true`, 40 cohorts, zero HAC gaps.
- Validation: focused tests passed 10/10; full PEAD regression passed 99/99;
  Reviewer A/B/C returned PASS; SAW validators PASS.

## Locked decisions

- Event-date cohorts retain `cohort_frequency = "D"` and the existing HAC gap
  fail-closed behavior.
- Quarterly cohorts require `allow_ex_post_cohorts = true` and are descriptive
  only; they do not replace the event-date result.
- HAC lag settings are not changed to obtain significance.
- The published D1/D2B/D3 artifacts and `strategies/pead_event_study.py` remain
  read-only.

## Forbidden scope

No alpha claim, strategy promotion, dashboard implementation, dashboard scope
approval, ranking/scoring, recommendation, alert, provider ingestion, broker or
order path, cohort-frequency tuning, HAC-lag tuning, staging, or commit is
authorized by this round.

## Rollback

Delete the new script, focused test, and evidence JSON, then remove this round's
documentation addenda. No published D1/D2B/D3 artifact rollback is required
because those inputs are read-only.
