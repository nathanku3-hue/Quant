# SAW Report - Phase 21.1 Round 1 (Ticker Pool Slice)
Date: 2026-02-20

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase21-brief.md`

RoundID: `R21_1_TICKER_POOL_20260220`  
ScopeID: `S21_1_MAHALANOBIS_SLICE`

## Scope and Ownership
- Scope: implement and validate Phase 21.1 ticker-pool slice (Mahalanobis + shrinkage) on locked C3 conviction flow, produce sample artifact, and stop at slice decision gate.
- Owned files:
  - `strategies/ticker_pool.py`
  - `strategies/company_scorecard.py`
  - `scripts/phase21_1_ticker_pool_slice.py`
  - `tests/test_ticker_pool.py`
  - `tests/test_company_scorecard.py`
  - `docs/lessonss.md`
  - `data/processed/phase21_1_ticker_pool_sample.csv`
  - `docs/saw_phase21_round1.md`
- Acceptance checks:
  - CHK-401..CHK-410.

Ownership check:
- Implementer: `primary-codex`
- Reviewer A: `019c7a6d-d527-7753-95e6-60489c0f6d8a`
- Reviewer B: `019c7a6d-d545-7ac1-a7f5-f3ead8d19885`
- Reviewer C: `019c7a6d-d557-7e00-a9a9-a475dc99ea6e`
- Independence: PASS

## Top-Down Snapshot
L1: User Priority Delivery on Stable C3 Baseline
L2 Active Streams: Backend, Data, Ops (risk)
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Stage              | Current Scope                                              | Rating | Next Scope                         |
+--------------------+------------------------------------------------------------+--------+------------------------------------+
| Planning           | B=Phase21.1 ticker pool; OH=Impl->RevA/B/C; AC=CHK-401..410 | 98/100 | Freeze slice decision evidence     |
| Executing          | Mahalanobis+shrinkage ranker + conviction integration      | 94/100 | Generate sample output artifact    |
| Iterate Loop       | Reviewer reconciliation and hardening (ops/data)           | 92/100 | Finalize SAW closure               |
| Final Verification | py_compile + targeted pytest + SAW validators              | 90/100 | Publish SAW + report sample        |
| CI/CD              | Handoff to next Phase 21 slice (entry timing)              | 88/100 | Open Phase 21.2 plan               |
+--------------------+------------------------------------------------------------+--------+------------------------------------+

## Slice Evidence
- Runner: `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2015-01-01 --as-of-date 2026-02-20`
- Output artifact: `data/processed/phase21_1_ticker_pool_sample.csv`
- Result:
  - Sample date: `2024-12-24` (latest eligible GREEN date with valid Mahalanobis outputs and 8 long rows)
  - Shrinkage path: `manual_fixed` (coefficient `0.5`)
  - Long rows: `8`
  - Short rows: `8`

## Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Reviewer B flagged memory overhead risk from materializing group dict in ticker-pool daily loop. | Switched to streaming group iteration (`for _, block in groupby(...)`) to avoid full groups dict materialization. | Implementer | Closed |
| Medium | Reviewer B flagged brittle no-artifact failure when no valid Mahalanobis dates existed. | Added deterministic fallback in sample-date chooser to latest date <= as-of, even when Mahalanobis values are unavailable. | Implementer | Closed |
| Medium | Reviewer C flagged covariance instability path producing non-finite distances on near-singular blocks. | Added diagonal fallback covariance path and finite-distance filtering before probability ranking. | Implementer | Closed |
| Info | Reviewer C requested fundamentals merge dedupe safety check. | Added deterministic `drop_duplicates(["date","permno"], keep="last")` before merge. | Implementer | Closed |
| Info | Reviewer A found no PIT/regression issues in strategy logic. | No change required. | Reviewer A | Closed |

## Scope Split Summary
in-scope findings/actions:
- Implemented `strategies/ticker_pool.py` with robust z-score, covariance shrinkage fallback, finite-distance safeguards, and deterministic long fallback.
- Integrated pool outputs into `build_phase20_conviction_frame` in `strategies/company_scorecard.py`.
- Added Phase 21.1 runner `scripts/phase21_1_ticker_pool_slice.py`.
- Added unit tests `tests/test_ticker_pool.py` and reran `tests/test_company_scorecard.py`.
- Generated `data/processed/phase21_1_ticker_pool_sample.csv`.
- Reconciled reviewer B/C findings in-scope and revalidated.

inherited out-of-scope findings/actions:
- No inherited Critical/High findings were introduced by this round.
- Prior Phase 20 promotion blocks remain historical and out-of-scope for this slice.

## Document Changes Showing
- `docs/lessonss.md` - appended Phase 21.1 lesson on strict-gate sparsity and deterministic fallback; reviewer status: C reviewed.
- `strategies/ticker_pool.py` - added deterministic fallback long selection, finite-distance safeguards, and streaming group iteration; reviewer status: A/B/C reviewed.
- `strategies/company_scorecard.py` - tightened EBITDA/ROIC acceleration derivation with 63-bar lag + proxy fill; reviewer status: A/C reviewed.
- `scripts/phase21_1_ticker_pool_slice.py` - new slice runner with fundamentals merge, dedupe safety, regime mapping, and sample-date selection logic; reviewer status: B/C reviewed.
- `tests/test_ticker_pool.py` - new tests for contract columns, fallback long selection, and far-tail short selection; reviewer status: A reviewed.
- `data/processed/phase21_1_ticker_pool_sample.csv` - generated Phase 21.1 sample evidence artifact.
- `docs/saw_phase21_round1.md` - canonical SAW closure for this slice.

## Check Results
- CHK-401: PASS (lesson row appended in `docs/lessonss.md`)
- CHK-402: PASS (`strategies/ticker_pool.py` implemented with manual shrinkage fallback and deterministic long/short actions)
- CHK-403: PASS (`strategies/company_scorecard.py` conviction integration retained PIT-safe lag logic)
- CHK-404: PASS (`scripts/phase21_1_ticker_pool_slice.py` implemented with merged fundamentals + dedupe safety)
- CHK-405: PASS (`data/processed/phase21_1_ticker_pool_sample.csv` generated)
- CHK-406: PASS (`py_compile` on touched strategy/script/test modules)
- CHK-407: PASS (`pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q`)
- CHK-408: PASS (Reviewer A pass complete)
- CHK-409: PASS (Reviewer B/C findings reconciled and fixed)
- CHK-410: PASS (closure packet + SAW block validators passed)

ChecksTotal: 10  
ChecksPassed: 10  
ChecksFailed: 0

SAW Verdict: PASS

Open Risks:
- none

Next action:
- proceed to Phase 21.2 entry-timing slice with the same PIT-safe gate discipline.

ClosurePacket: RoundID=R21_1_TICKER_POOL_20260220; ScopeID=S21_1_MAHALANOBIS_SLICE; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=none; NextAction=proceed to phase21.2 entry timing slice with same pit safe gate discipline

ClosureValidation: PASS
SAWBlockValidation: PASS
