# SAW Report - Phase 21 Final Finetune (Round 2.3)
Date: 2026-02-21

Builds on prior round: `docs/saw_phase21_round2_2.md`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: final-finetune-guided | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase21-brief.md`

RoundID: `R21_FINAL_FINETUNE_20260221`
ScopeID: `S21_ODDS_MAX_DEF_JUNK_R23`

## Scope and Ownership
- Scope: final finetune of ticker-pool odds scoring and telemetry under locked boundaries.
  - score: `S_i = log(r_cyc + 1e-8) - log(max(r_def, r_junk) + 1e-8)`
  - junk labeling: lowest medians on quality trio with ordered fallbacks
  - missing quality triplet fallback: junk-dominant posterior for that row
  - pool/execution decoupling retained (`WAIT/AVOID/LONG/SHORT`)
  - telemetry added: `mu_style_count_top8`, `plug_tza_count_top_longs`, `min_odds_ratio_top8`
- Owned files:
  - `strategies/ticker_pool.py`
  - `strategies/company_scorecard.py`
  - `scripts/phase21_1_ticker_pool_slice.py`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`
  - `docs/saw_phase21_round2_3.md`
  - `docs/lessonss.md`
  - `docs/phase_brief/phase21-brief.md`
- Acceptance checks: CHK-601..CHK-610

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7eba-af4c-7030-9f85-0a7d7d25e857`
- Reviewer B: `019c7eba-af6c-72a1-a302-f96293091919`
- Reviewer C: `019c7eba-af76-7f62-8695-abfa8a6faa27`
- Independence: PASS

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Decision gate failed: MU-style dominance absent (`0/8`, `0/12`), seed presence failed, and `min_odds_ratio_top8=2.5793<3.0`. | Stop at gate; keep Phase 22 blocked; require direction shift before promotion. | Strategy | Open |
| Medium | Reviewer A: style gate signal is currently telemetry-only and not enforced in long candidate filter. | Carry as out-of-scope refinement candidate; do not change in locked finetune round. | Strategy | Open |
| Medium | Reviewer B: posterior integrity flags are emitted but not hard-failing run status/exit code. | Carry as ops hardening candidate in next allowed scope. | Runtime | Open |
| Medium | Reviewer C: strict complete-case feature row filtering may reduce coverage near panel edges. | Carry as data-quality/performance hardening candidate (degraded-mode handling). | Data | Open |

## Check Results
- CHK-601: PASS (odds-vs-max(def,junk) score retained with epsilon `1e-8`)
- CHK-602: PASS (junk component quality trio mapping and missing-row fallback implemented)
- CHK-603: PASS (pool/execution decoupling retained: `WAIT/AVOID/LONG/SHORT`)
- CHK-604: PASS (sample/summary regenerated for `2024-12-24`)
- CHK-605: PASS (`py_compile` passed on touched modules)
- CHK-606: PASS (`pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` passed)
- CHK-607: PASS (telemetry contract emitted: MU-style count, PLUG/TZA count, min odds ratio)
- CHK-608: FAIL (archetype gate failed: MU-style count target not met)
- CHK-609: FAIL (odds gate failed: `min_odds_ratio_top8` below `3.0`)
- CHK-610: PASS (SAW reviewer A/B/C passes completed and reconciled)

ChecksTotal: 10
ChecksPassed: 8
ChecksFailed: 2

## Gate Outcome (2024-12-24)
- `TZA/PLUG` out of top-8 longs: `True` (PASS)
- Defensive share top-8: `12.5%` (PASS vs `<35%`)
- MU-style count top-8: `0` (FAIL vs `>=4`)
- MU-style count top-12: `0` (FAIL vs `>=4`)
- Seed presence in top-8 (MU/CIEN available): `False` (FAIL)
- Min odds ratio top-8: `2.5793` (FAIL vs `>=3.0`)

## Scope Split Summary
in-scope findings/actions:
- Added locked quality-triplet fallback order by non-null availability.
- Added missing-quality junk-dominance fallback in posterior scoring path.
- Added round2.3 telemetry fields for explicit gate auditing.
- Regenerated artifacts and reran compile/tests.

inherited out-of-scope findings/actions:
- Reviewer A suggestion to enforce style gate in long selection (policy decision required).
- Reviewer B suggestion to hard-fail on posterior integrity flags.
- Reviewer C suggestion to relax/annotate complete-case row filtering.

## Evidence
- Slice run:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2024-12-24`
- Compile:
  - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py`
- Tests:
  - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q`
- Artifacts:
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `data/processed/phase21_1_ticker_pool_summary.json`

## Document Changes Showing
- `docs/phase_brief/phase21-brief.md` - appended round2.3 scope/results block (reviewed).
- `docs/lessonss.md` - appended round2.3 lesson row (reviewed).
- `docs/saw_phase21_round2_3.md` - new SAW report (reviewed).
- `strategies/company_scorecard.py` - propagated fallback source columns (`revenue_growth_yoy`, `gm_accel_q`) into conviction frame.
- `strategies/ticker_pool.py` - quality-triplet fallback hardening; missing-row junk fallback in posterior odds.
- `scripts/phase21_1_ticker_pool_slice.py` - round2.3 telemetry fields and sample output extension (`odds_ratio`).
- `data/processed/phase21_1_ticker_pool_sample.csv` - regenerated 2024-12-24 sample.
- `data/processed/phase21_1_ticker_pool_summary.json` - regenerated summary and gate telemetry.

SAW Verdict: BLOCK

Open Risks:
- Archetype promotion gate remains failed (MU-style dominance and minimum odds ratio).

Next action:
- Hold Phase 22; request orchestrator decision for direction shift or expanded-scope model change.

ClosurePacket: RoundID=R21_FINAL_FINETUNE_20260221; ScopeID=S21_ODDS_MAX_DEF_JUNK_R23; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=archetype gate failed with mu style count and min odds ratio below threshold; NextAction=hold phase22 and request orchestrator direction shift
ClosureValidation: PASS
SAWBlockValidation: PASS
