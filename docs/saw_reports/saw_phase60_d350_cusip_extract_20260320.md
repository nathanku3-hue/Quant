# SAW Report - Phase 60 D-350 Readonly CUSIP Extract

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: readonly-cusip-extract | Domains: Multi-Sleeve Research Kernel + Governance Stack | FallbackSource: docs/spec.md + docs/phase_brief/phase60-brief.md

## Scope and Ownership
- Scope: generate readonly PERMNO-to-CUSIP sidecar outputs for the D-341 missing executed-exposure return-cell remediation slice only, without mutating `prices_tri.parquet`, the kernel, or prior SSOT artifacts.
- RoundID: `R60_D350_CUSIP_EXTRACT_20260320`
- ScopeID: `PH60_D350_READONLY_CUSIP_EXTRACT`
- Primary editor: Codex (main agent)
- Implementer pass: Codex local readonly extraction pass
- Reviewer A (strategy/correctness): Huygens
- Reviewer B (runtime/ops): Aquinas
- Reviewer C (data/perf): Leibniz
- Ownership check: implementer and reviewers are distinct agents -> PASS.

## Acceptance Checks
- CHK-01: The extract remains additive-only and does not mutate `prices_tri.parquet`, `research_data/`, or prior SSOT artifacts -> PASS.
- CHK-02: The S&P input file is emitted as a single-column newline-delimited text file with no header, commas, quotes, or brackets -> PASS.
- CHK-03: The local key-pair outputs are emitted as `[PERMNO,CUSIP]` CSV and Parquet artifacts -> PASS.
- CHK-04: Raw identifier lineage resolves `PERMNO 86544` to one CUSIP base (`09522910`) with no ambiguity in the on-disk CRSP-style source -> PASS.
- CHK-05: The 9th CUSIP check digit is computed and the emitted CUSIP9 is `095229100` -> PASS.
- CHK-06: The evidence summary records the D-341 authority anchor (`274`) and the current live reconstruction drift (`275`) explicitly -> PASS.
- CHK-07: Reviewer A/B/C passes completed and no in-scope Critical/High findings remain -> PASS.

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Exact D-341 scoping is not fully replay-stable because the frozen review packet preserved the count but not the exact `(date, permno)` manifest; the current live reconstruction now yields `275` cells while collapsing to the same single PERMNO universe | Keep the emitted files bounded to the single inferred PERMNO and carry the drift explicitly in the evidence summary; on the next repair-oriented round, persist a frozen D-341 `(date, permno)` manifest before any replay | Codex | Open |
| Low | The round used bounded inline atomic writes rather than a checked-in reusable runner, so temp->replace behavior is not independently replay-auditable by a future operator | If this extract must be rerun operationally, promote it into a small readonly script with explicit test coverage | Codex | Open |

## Scope Split Summary
- in-scope findings/actions:
  - identified the affected universe as a single PERMNO (`86544`) for the current bounded extract;
  - resolved raw CUSIP lineage from `data/hkcj1itkyvfsmibz.csv`;
  - computed and emitted the 9-character CUSIP `095229100`;
  - published the S&P flat file, local key-pair CSV/Parquet, and the evidence summary;
  - recorded the D-341 authority anchor and the current live drift in the evidence summary.
- inherited out-of-scope findings/actions:
  - the frozen D-341 packet still does not include the exact `(date, permno)` manifest;
  - the current mutable live comparator reconstruction differs from the frozen D-341 count (`275` vs `274`);
  - any comparator repair, post-2022 audit rerun, or wider Phase 61+ execution remains outside this readonly extract round.

## Verification Evidence
- Output artifacts:
  - `data/processed/d341_missing_executed_exposure_cusips.txt` -> PASS.
  - `data/processed/d341_missing_executed_exposure_permno_cusip.csv` -> PASS.
  - `data/processed/d341_missing_executed_exposure_permno_cusip.parquet` -> PASS.
- Evidence summary:
  - `docs/context/e2e_evidence/phase60_d350_cusip_extract_20260320_summary.json` -> PASS.
- Reviewer lanes:
  - Reviewer A (Huygens) -> ADVISORY_PASS with one medium replay-stability risk.
  - Reviewer B (Aquinas) -> ADVISORY_PASS with one medium replay-stability risk and one low reusable-runner risk.
  - Reviewer C (Leibniz) -> PASS with no findings.

## Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| `data/processed/d341_missing_executed_exposure_cusips.txt` | Published S&P flat-list CUSIP input file (`095229100`) with newline-only formatting | B reviewed |
| `data/processed/d341_missing_executed_exposure_permno_cusip.csv` | Published local `[PERMNO,CUSIP]` key-pair CSV | A/B/C reviewed |
| `data/processed/d341_missing_executed_exposure_permno_cusip.parquet` | Published local `[PERMNO,CUSIP]` key-pair Parquet | C reviewed |
| `docs/context/e2e_evidence/phase60_d350_cusip_extract_20260320_summary.json` | Published readonly evidence summary with D-341 anchor and live drift note | A/B/C reviewed |
| `docs/lessonss.md` | Added round guardrail about persisting frozen missing-cell manifests for downstream repair extracts | C reviewed |
| `docs/saw_reports/saw_phase60_d350_cusip_extract_20260320.md` | Published this SAW report | N/A |

## Document Sorting (GitHub-optimized)
1. `docs/lessonss.md`
2. `docs/saw_reports/saw_phase60_d350_cusip_extract_20260320.md`

Open Risks:
- The emitted identifier set is internally consistent, but exact D-341 scoping is still inferred through a live reconstruction because the frozen D-341 packet does not publish the underlying `(date, permno)` manifest.
- The current live comparator path reconstructs `275` missing cells while the frozen D-341 packet remains authoritative at `274`.
- If this extract needs operational replay, a checked-in readonly runner plus frozen manifest should be added before relying on replay stability.

Next action:
- Use the emitted CUSIP and key-pair files for the bounded readonly supplement now; if a rerun or broader repair is required later, first persist the frozen D-341 `(date, permno)` manifest and key future extracts to that manifest.

SAW Verdict: PASS
ClosurePacket: RoundID=R60_D350_CUSIP_EXTRACT_20260320; ScopeID=PH60_D350_READONLY_CUSIP_EXTRACT; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=frozen_d341_manifest_missing_and_live_reconstruction_drift_275_vs_274; NextAction=persist_frozen_d341_date_permno_manifest_before_any_future_rerun
ClosureValidation: PASS
SAWBlockValidation: PASS
