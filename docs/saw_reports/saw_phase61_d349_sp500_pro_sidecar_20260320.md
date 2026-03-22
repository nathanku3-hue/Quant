# SAW Report - Phase 61 D-349 S&P 500 Pro Sidecar Fallback

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase61-data-sidecar | Domains: Multi-Sleeve Research Kernel + Governance Stack | FallbackSource: docs/spec.md + docs/phase_brief/phase60-brief.md

## Scope and Ownership
- Scope: ingest the supplied S&P Security Detail workbook, apply the strict `date >= 2023-01-01` mask on the truthful workbook date surface, join it to the D-350 `PERMNO/CUSIP` map, and emit `sidecar_sp500_pro_2023_2024.parquet` as an additive-only view-layer sidecar.
- RoundID: `R61_D349_SP500_PRO_SIDECAR_20260320`
- ScopeID: `PH61_D349_SP500_PRO_SIDECAR`
- Primary editor: Codex (main agent)
- Implementer pass: Codex local implementation + verification pass
- Reviewer A (strategy/correctness): Plato
- Reviewer B (runtime/ops): Confucius
- Reviewer C (data/perf): Sagan
- Ownership check: implementer and reviewers are distinct agents -> PASS.

## Acceptance Checks
- CHK-01: The builder reads the supplied workbook without adding new Excel dependencies and without mutating bedrock price artifacts -> PASS.
- CHK-02: The strict `date >= 2023-01-01` mask is applied to the truthful workbook date surface and the emitted row remains bounded to `2023-11-06` -> PASS.
- CHK-03: The sidecar joins through the D-350 `PERMNO/CUSIP` map and emits `permno = 86544`, `cusip = 095229100` -> PASS.
- CHK-04: `sp_rating` and `sp_score` remain null because the workbook does not expose those fields in machine-readable form -> PASS.
- CHK-05: The raw-CUSIP fallback path now handles both true 8-character bases and Excel-stripped leading-zero numerics -> PASS.
- CHK-06: The builder now fails closed if the strict date mask removes every row -> PASS.
- CHK-07: Targeted verification (`py_compile`, focused pytest, sidecar build) passes -> PASS.
- CHK-08: Decision log, notes, lessons, evidence summary, and this SAW report are published in the same round -> PASS.

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Raw CUSIP fallback could mis-normalize a true 8-character base or an Excel-stripped leading-zero numeric workbook value | Replaced naive zero-padding with candidate generation that includes real CUSIP check-digit logic plus Excel-numeric fallback matching | Codex | Resolved |
| Medium | Empty-mask runs could have written a zero-row sidecar while still returning success | Added explicit fail-closed runtime error when the strict date mask removes every row | Codex | Resolved |
| Low | Fixed summary filename would have preserved a stale date label across reruns | Default summary path now derives from the run date tag | Codex | Resolved |

## Scope Split Summary
- in-scope findings/actions:
  - implemented `scripts/build_sp500_pro_sidecar.py` as the bounded builder;
  - added `tests/test_build_sp500_pro_sidecar.py`;
  - emitted `data/processed/sidecar_sp500_pro_2023_2024.parquet`;
  - emitted `docs/context/e2e_evidence/phase61_sp500_pro_sidecar_20260320_summary.json`;
  - updated decision log, notes, lessons, and this SAW report.
- inherited out-of-scope findings/actions:
  - the supplied workbook remains metadata-only and does not contain a machine-readable dated S&P ratings history;
  - if full dated vendor history is required later, it must come from the actual bulk export rather than this Security Detail workbook;
  - all broader Phase 61 comparator repair and re-audit work remains outside this sidecar-only slice.

## Verification Evidence
- `.venv\Scripts\python -m py_compile scripts\build_sp500_pro_sidecar.py tests\test_build_sp500_pro_sidecar.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_build_sp500_pro_sidecar.py -q` -> PASS (`4 passed`).
- `.venv\Scripts\python scripts\build_sp500_pro_sidecar.py` -> PASS.
- `data/processed/sidecar_sp500_pro_2023_2024.parquet` -> PASS.
- `docs/context/e2e_evidence/phase61_sp500_pro_sidecar_20260320_summary.json` -> PASS.
- Reviewer lanes:
  - Reviewer A -> ADVISORY_PASS after fix; no remaining in-scope High/Critical issues.
  - Reviewer B -> ADVISORY_PASS after fix; no remaining in-scope High/Critical issues.
  - Reviewer C -> PASS.

## Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| `scripts/build_sp500_pro_sidecar.py` | Added bounded dependency-free S&P sidecar builder with strict mask, D-350 map join, atomic parquet/json writes, and fail-closed empty-mask handling | A/B/C reviewed |
| `tests/test_build_sp500_pro_sidecar.py` | Added focused workbook-parse, join, fallback-candidate, and empty-mask tests | A/B/C reviewed |
| `data/processed/sidecar_sp500_pro_2023_2024.parquet` | Published bounded metadata-only S&P sidecar row for `2023-11-06` | A/B/C reviewed |
| `docs/context/e2e_evidence/phase61_sp500_pro_sidecar_20260320_summary.json` | Published sidecar evidence summary with truthful metadata-only fallback disclosure | A/B/C reviewed |
| `docs/notes.md` | Added sidecar parse/mask/join contract and null-preservation rule | C reviewed |
| `docs/decision log.md` | Appended `D-349` bounded sidecar fallback decision | A/B/C reviewed |
| `docs/lessonss.md` | Added guardrail about vendor Security Detail exports masquerading as bulk history | C reviewed |
| `docs/saw_reports/saw_phase61_d349_sp500_pro_sidecar_20260320.md` | Published this SAW report | N/A |

## Document Sorting (GitHub-optimized)
1. `docs/notes.md`
2. `docs/lessonss.md`
3. `docs/decision log.md`
4. `docs/saw_reports/saw_phase61_d349_sp500_pro_sidecar_20260320.md`

Open Risks:
- The supplied workbook is metadata-only, so the emitted sidecar is a truthful one-row fallback and not a dated S&P ratings history.
- `sp_rating` and `sp_score` remain null until a machine-readable vendor history export is provided.
- Future full-history ingestion should use the actual bulk export, not this Security Detail workbook.

Next action:
- Use `data/processed/sidecar_sp500_pro_2023_2024.parquet` as the bounded view-layer sidecar for this source file now; if you want full dated S&P history later, provide the actual bulk export and keep the same strict mask/join path.

SAW Verdict: PASS
ClosurePacket: RoundID=R61_D349_SP500_PRO_SIDECAR_20260320; ScopeID=PH61_D349_SP500_PRO_SIDECAR; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=metadata_only_workbook_null_sp_rating_and_sp_score_until_true_bulk_export_arrives; NextAction=use_bounded_sidecar_now_and_switch_to_bulk_export_if_full_history_is_needed
ClosureValidation: PASS
SAWBlockValidation: PASS
