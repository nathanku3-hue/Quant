# SAW Report - Phase 61 D-350 Raw Tape Ingest Preparation

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase61-data-sidecar | Domains: Multi-Sleeve Research Kernel + Governance Stack | FallbackSource: docs/spec.md + docs/phase_brief/phase60-brief.md

## Scope and Ownership
- Scope: prepare the literal S&P daily-tape ingest path for `data/raw/sp500_pro_avantax_tape.csv`, harden it against malformed CSV inputs, and truthfully report the current local blocker because the raw tape cannot yet be produced on this machine.
- RoundID: `R61_D350_TAPE_INGEST_BLOCK_20260320`
- ScopeID: `PH61_D350_RAW_TAPE_INGEST`
- Primary editor: Codex (main agent)
- Implementer pass: Codex local implementation + verification pass
- Reviewer A (strategy/correctness): Euler
- Reviewer B (runtime/ops): Newton
- Reviewer C (data/perf): Hilbert
- Ownership check: implementer and reviewers are distinct agents -> PASS.

## Acceptance Checks
- CHK-01: The builder prefers the raw tape CSV path and keeps metadata fallback opt-in only -> PASS.
- CHK-02: The raw tape loader rejects duplicate dates -> PASS.
- CHK-03: The raw tape loader rejects all-NaN `price` and all-NaN `total_return` columns -> PASS.
- CHK-04: The raw tape loader parses accounting-style negatives -> PASS.
- CHK-05: Focused verification passes -> PASS.
- CHK-06: Default builder invocation now blocks cleanly when the raw tape CSV is absent -> PASS.
- CHK-07: The literal daily tape itself is present locally and the sidecar is rebuilt from it -> FAIL.

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Duplicate tape dates could inflate the C3 view-layer join | Added explicit duplicate-date rejection in the raw tape loader | Codex | Resolved |
| Medium | Float columns could be entirely non-parseable while the build still appeared successful | Added fail-closed checks for all-NaN `price` and all-NaN `total_return` | Codex | Resolved |
| Medium | The D-350 objective could look complete even when the literal daily tape was still absent | Made raw tape mode the default and metadata fallback opt-in only; default run now blocks when the tape is missing | Codex | Resolved |
| High | The literal Avantax daily tape is still unavailable locally because the Capital IQ add-in is absent and the raw CSV does not exist | External vendor extraction must produce `data/raw/sp500_pro_avantax_tape.csv` before the real sidecar rebuild can occur | External / operator | Open |

## Scope Split Summary
- in-scope findings/actions:
  - upgraded the builder for the real raw tape CSV path;
  - added focused tests for duplicate dates, floatless tapes, accounting-style negatives, missing raw tape, metadata fallback, and raw-tape success mode;
  - verified the default run blocks cleanly on missing tape;
  - published blocker evidence and this SAW report.
- inherited out-of-scope findings/actions:
  - the current workstation does not have an active Capital IQ COM add-in;
  - the literal raw tape CSV has not yet been produced by the external vendor workflow;
  - C3 patch execution remains blocked until the tape exists.

## Verification Evidence
- `.venv\Scripts\python -m pytest tests\test_build_sp500_pro_sidecar.py -q` -> PASS (`8 passed`).
- `.venv\Scripts\python scripts\build_sp500_pro_sidecar.py` -> BLOCK (`Raw tape CSV is missing ...`).
- `docs/context/e2e_evidence/phase61_sp500_pro_tape_block_20260320.json` -> PASS.
- Reviewer lanes:
  - Reviewer A -> ADVISORY_PASS; resolved raw-CUSIP fallback correctness risk.
  - Reviewer B -> ADVISORY_PASS; resolved silent-success and naming risks, but objective remains blocked on missing tape.
  - Reviewer C -> ADVISORY_PASS; resolved duplicate-date and floatless-tape hardening gaps.

## Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| `scripts/build_sp500_pro_sidecar.py` | Added real raw-tape CSV ingest path, duplicate-date rejection, float-presence guards, accounting-negative parsing, and default fail-closed blocking on missing tape | A/B/C reviewed |
| `tests/test_build_sp500_pro_sidecar.py` | Added raw-tape ingest, duplicate-date, missing-tape, and numeric-coercion coverage | A/B/C reviewed |
| `docs/context/e2e_evidence/phase61_sp500_pro_tape_block_20260320.json` | Published blocker evidence for missing Capital IQ tape/add-in | B/C reviewed |
| `docs/decision log.md` | Appended `D-350` blocked ingest-preparation packet | A/B/C reviewed |
| `docs/lessonss.md` | Added guardrail about preparing ingest before external vendor tape arrives | C reviewed |
| `docs/saw_reports/saw_phase61_d350_tape_ingest_block_20260320.md` | Published this SAW report | N/A |

## Document Sorting (GitHub-optimized)
1. `docs/lessonss.md`
2. `docs/decision log.md`
3. `docs/saw_reports/saw_phase61_d350_tape_ingest_block_20260320.md`

Open Risks:
- The literal Capital IQ daily tape is still unavailable locally.
- `data/processed/sidecar_sp500_pro_2023_2024.parquet` has not yet been rebuilt from the real tape.
- The 274-cell C3 view-layer patch remains blocked until `data/raw/sp500_pro_avantax_tape.csv` exists.

Next action:
- Produce `data/raw/sp500_pro_avantax_tape.csv` from a workstation with the active Capital IQ Excel plug-in, then rerun `.\.venv\Scripts\python scripts\build_sp500_pro_sidecar.py` without `--allow-metadata-fallback`.

SAW Verdict: BLOCK
ClosurePacket: RoundID=R61_D350_TAPE_INGEST_BLOCK_20260320; ScopeID=PH61_D350_RAW_TAPE_INGEST; ChecksTotal=7; ChecksPassed=6; ChecksFailed=1; Verdict=BLOCK; OpenRisks=capital_iq_addin_absent_and_raw_tape_csv_missing_so_literal_daily_tape_rebuild_cannot_run; NextAction=produce_data_raw_sp500_pro_avantax_tape_csv_then_rerun_builder_without_allow_metadata_fallback
ClosureValidation: PASS
SAWBlockValidation: PASS
