# Phase 57 Handover (PM-Friendly)

Date: 2026-03-18
Phase Window: 2015-01-01 to 2022-12-31
Status: PASS (Phase 57 closed; evidence-only / no promotion / no widening)
Owner: Codex

## 1) Executive Summary
- Objective completed: Phase 57 Corporate Actions Event Sleeve 2 is closed with its first bounded evidence packet preserved and no promotion or widening authorized.
- Business/user impact: The repo now has a truthful governed Corporate Actions packet on the locked same-window / same-cost / same-engine surface, but leadership is explicitly protected from over-interpreting it because the packet underperformed the locked C3 baseline on Sharpe and CAGR.
- Current readiness: Phase 57 closed; Phase 58 may proceed only in planning-only mode until a later explicit execution token is issued.

## 2) Delivered Scope vs Deferred Scope
- Delivered:
  - Bounded Corporate Actions runner and focused tests.
  - First same-window / same-cost / same-engine summary, daily evidence, and delta-vs-C3 artifacts.
  - Evidence-only review / no-promotion disposition and clean phase closeout.
- Deferred:
  - Any follow-up Phase 57 comparator widening or alternative Corporate Actions design (Owner: PM/CEO approval required; Target: future explicit approval packet).
  - Any promotion or new Corporate Actions execution beyond the first bounded packet (Owner: PM/CEO; Target: explicit approval packet).

## 3) Derivation and Formula Register
| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-57-01 | `corp_action_yield_t = total_ret_t - ((raw_close_t / raw_close_{t-1}) - 1)` | `total_ret_t`, `raw_close_t`, `raw_close_{t-1}` | Defines the bounded Corporate Actions event proxy from repo-local price history without inventing a missing taxonomy feed | `scripts/phase57_corporate_actions_runner.py`, `docs/notes.md` |
| F-57-02 | `eligible_t = 1[(quality_pass_t = 1) and (adv_usd_t >= 5_000_000) and (0.005 <= corp_action_yield_t <= 0.25)]` | `quality_pass_t`, `adv_usd_t`, `corp_action_yield_t` | Pins the first bounded denominator contract to the same family as prior event sleeves | `scripts/phase57_corporate_actions_runner.py`, `docs/notes.md` |
| F-57-03 | `confirmed_t = 1[value_rank_pct_t >= 0.60]` and `target_weight_{t,i} = 1 / N_t` for confirmed names on event day | `value_rank_pct_t`, `N_t` | Keeps the first packet simple, vectorized, and governed on the locked surface | `scripts/phase57_corporate_actions_runner.py`, `docs/notes.md` |
| F-57-04 | `phase57_promotion_ready = 1[(same_window_same_cost_same_engine = 1) and (sharpe_delta >= 0) and (cagr_delta >= 0)]` | `same_window_same_cost_same_engine`, `sharpe_delta`, `cagr_delta` | Encodes why the first packet remains evidence-only and not promotion-ready | `docs/notes.md`, `docs/decision log.md` |

## 4) Logic Chain
| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-57-01 | `prices.parquet`, `features.parquet`, `daily_fundamentals_panel.parquet`, locked Phase 54 C3 baseline summary | Build `corp_action_yield` candidates -> apply quality / ADV / event-yield gates -> rank by `capital_cycle_score` -> equal-weight event basket -> full trading-calendar reindex -> `core.engine.run_simulation` -> delta vs C3 | Keep packet evidence-only if Sharpe / CAGR do not clear the locked baseline | Phase 57 summary + daily evidence + delta-vs-C3 artifacts plus no-promotion closeout |

## 5) Validation Evidence Matrix
| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-PH-01 | `.venv\Scripts\python -m pytest -q` | PASS | `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.stdout.log`, `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.stderr.log`, `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.status.txt` | exit code `0` |
| CHK-PH-02 | `.venv\Scripts\python launch.py --help` | PASS | `docs/context/e2e_evidence/phase57_launch_smoke_20260318.stdout.log`, `docs/context/e2e_evidence/phase57_launch_smoke_20260318.stderr.log`, `docs/context/e2e_evidence/phase57_launch_smoke_20260318.status.txt` | exit code `0` |
| CHK-PH-03 | `.venv\Scripts\python scripts\phase57_corporate_actions_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase57_corporate_actions_replay_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase57_corporate_actions_replay_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase57_corporate_actions_replay_delta_vs_c3_20260318.csv` | PASS | `docs/context/e2e_evidence/phase57_corporate_actions_replay_20260318.*` | `rows=2021`, `active_days=866`, `candidate_rows=972`, `sharpe=0.2392571448595545` |
| CHK-PH-04 | Reviewer B independent replay with replay_revb output paths | PASS | `docs/context/e2e_evidence/phase57_corporate_actions_replay_revb_20260318.*` | matched replay summary metrics and `rows=2021` |

## 6) Open Risks / Assumptions / Rollback
- Open Risks:
  - The first bounded packet remains below C3 on Sharpe and CAGR, so no promotion or automatic follow-up is authorized from this closeout.
- Assumptions:
  - Phase 57 remains closed unless a new explicit approval packet is issued.
- Rollback Note:
  - Revert Phase 57 closeout docs/context/SAW and `data/processed/phase57_*` only; do not alter `D-317`, the Phase 56 PEAD artifacts, `D-312`, or the Phase 53 kernel.

## 6.1) Data Integrity Evidence (Required)
- Atomic write path proof:
  - `scripts/phase57_corporate_actions_runner.py` writes summary/evidence/delta via `_atomic_json_write` and `_atomic_csv_write` (temp -> replace).
- Row-count sanity:
  - Replay summary `rows = 2021`; replay CSV has `2021` data rows and `866` event days.
  - Reviewer-B replay summary matches `rows = 2021` and `active_days = 866`.
- Runtime/performance sanity:
  - Both replay commands completed successfully with matching artifact metrics.

## 7) Next Phase Roadmap
| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | Phase 58 planning-only kickoff | Phase 58 brief + kickoff memo + decision-log entry + context refresh | Docs/Ops |
| 2 | Phase 58 execution authorization (if approved later) | Exact explicit approval token recorded in-thread | PM/CEO |
| 3 | Governance-layer implementation (if approved later) | Same-window / same-cost / same-engine propagation contract documented before code | Backend/Data |

## 8) New Context Packet (for /new)
- What was done:
  - Closed Phase 57 as evidence-only / no promotion / no widening with the first bounded Corporate Actions artifacts preserved.
  - Captured full regression, runtime smoke, and dual replay evidence under `docs/context/e2e_evidence/`.
- What is locked:
  - `D-284`, `D-292`, `D-309`, `D-311`, `D-312`, `D-313`, `D-314`, `D-315`, `D-316`, `D-317`, `D-318`, `D-319`, `D-320`, `D-321`, `D-322`, `RESEARCH_MAX_DATE = 2022-12-31`, and same-window/same-cost/`core.engine.run_simulation` discipline.
  - Phase 57 is closed; no promotion or widening without a new explicit packet.
- What remains:
  - Phase 58 execution remains blocked pending a separate explicit approval token.
- Next-phase roadmap summary:
  - Phase 58 planning-only kickoff -> Phase 58 execution token (if approved) -> governance-layer bounded implementation.
- Immediate first step:
  - Await explicit approval token before any Phase 58 execution work.

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve next phase" to start execution.
