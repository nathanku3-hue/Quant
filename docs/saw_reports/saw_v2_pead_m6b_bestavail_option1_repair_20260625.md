# SAW Report - V2 PEAD M6b Best-Available Option 1 Repair

`SAW Verdict: PASS`

## Scope

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REPAIR`
- `ScopeID`: `V2_PEAD_M6B_BESTAVAIL_OPTION1_TERMINAL_WINDOW_AND_COMMIT_REPAIR`
- Mode: `EXECUTION_PACKET`

## Result

The B artifact was repaired in one ordered round: full 60-session eligibility is enforced before the engine run, then the data gate runs before a rollback-protected B JSON/parquet package commit. B remains illustrative-only and is still not alpha, not tradable, and not strict M6b readiness evidence.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Late-2019 selected B cohorts could not complete the configured 60-session holding window inside the 2015-2019 return frame. | Added `filter_events_for_full_holding_window(...)` before the sparse engine and recorded terminal eligibility in the run evidence. | Implementer + Reviewer A/C | Closed |
| High | Direct standalone execution failed before argparse because repo root was not on `sys.path`. | Bootstrapped `ROOT` into `sys.path` before importing `scripts.*`; direct `--data-gate` and `--commit-bestavail-run` now pass. | Implementer + Reviewer B | Closed |
| High | B JSON/parquet publication was per-file atomic but not rollback-protected as a package. | Added `--commit-bestavail-run`: gate first, stage both run outputs, then rollback-protected public replacement. Added regression for second-replace failure rollback. | Implementer + Reviewer B | Closed |
| Medium | The historical Reviewer A/C BLOCK reports could be overread as current after repair. | Published this repair report and refreshed current truth surfaces with the repaired counts and reviewer outcomes. | Parent reconciler | Closed |

## Reviewer Rerun Summary

- Reviewer A strategy correctness: PASS. Full-window selected events now report `selected_events_with_incomplete_60_session_window = 0`; all B claim-ceiling flags remain hard locked.
- Reviewer B runtime/ops resilience: PASS. Direct script invocation reaches argparse; `--data-gate` and `--commit-bestavail-run` pass; rollback regression passes.
- Reviewer C data integrity/performance path: PASS. JSON/parquet row counts match at 975 rows, parquet SHA matches JSON, dates span `2016-01-15` through `2019-11-27`, duplicate dates = 0, and gross/net daily return fields have no nulls.

## Evidence

- Code: `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- Tests: `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py`.
- Gate artifact: `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`.
- Repaired run artifact: `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json`.
- Repaired daily parquet: `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`.

## Checks

- Direct data gate: PASS via `.venv/Scripts/python.exe scripts/pead_m6b_bestavail_illustrative_2015_2019.py --data-gate`.
- Direct commit run: PASS via `.venv/Scripts/python.exe scripts/pead_m6b_bestavail_illustrative_2015_2019.py --commit-bestavail-run`.
- B focused pytest: PASS 5/5 via `.venv/Scripts/python.exe -m pytest tests/test_pead_m6b_bestavail_illustrative_2015_2019.py -q`.
- M6 sparse-engine pytest: PASS 12/12 via `.venv/Scripts/python.exe -m pytest tests/test_pead_m6_pit_walk_forward_equity_curve.py -q`.
- Compile: PASS via `.venv/Scripts/python.exe -m py_compile scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- Artifact consistency: PASS; JSON rows = parquet rows = 975; JSON parquet SHA matches; duplicate dates = 0; null gross/net returns = 0.
- Runtime isolation scan: PASS for `scripts/` and `tests/`; references are limited to the standalone script and its test.
- Combined pytest command for both files in one invocation: tool safety filter blocked command execution; the same two files passed separately as 5/5 and 12/12.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `scripts/pead_m6b_bestavail_illustrative_2015_2019.py` | Added direct invocation bootstrap, full-window eligibility filter, terminal eligibility evidence, and rollback-protected `--commit-bestavail-run`. | Reviewer A/B/C PASS |
| `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py` | Added direct invocation, full-window filter, and rollback regression coverage. | Reviewer A/B PASS |
| `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json` | Regenerated through the new commit path; selected incomplete windows now zero. | Reviewer A/C PASS |
| `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet` | Regenerated daily-return parquet with 975 rows and matching JSON SHA. | Reviewer C PASS |
| `docs/context/*_current.md` | Refreshed current truth for repaired B status and remaining claim boundary. | Reviewer A/B/C PASS |

## Hierarchy Confirmation:

Approved | Session | Trigger: user approved one-round ordered repair | Domains: Strategy/Research, Data/Ops, Docs/Ops

## Open Risks:

- In-scope open risk: none for the B repair blockers; terminal-window, direct invocation, and package commit findings are closed.
- Inherited open risk: B remains illustrative-only; it must not be used as alpha/tradable or strict M6b readiness evidence.
- Inherited open risk: the repo working tree was already very dirty before this repair; unrelated files were not cleaned or reverted.

## Next action:

Keep B closed only as a flagged engine sanity diagnostic; move any alpha/tradable work to separately authorized strict Path A data gates.

ClosureValidation: PASS
SAWBlockValidation: PASS
ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REPAIR; ScopeID=V2_PEAD_M6B_BESTAVAIL_OPTION1_TERMINAL_WINDOW_AND_COMMIT_REPAIR; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=B remains illustrative only and dirty repo is inherited; NextAction=Keep B closed as flagged engine sanity diagnostic only
