# Phase 59 Handover (PM-Friendly)

Date: 2026-03-18
Phase Window: 2015-01-01 to 2022-12-31
Status: PASS (Phase 59 closed; evidence-only / no promotion / no widening)
Owner: Codex

## 1) Executive Summary
- Objective completed: Phase 59 Shadow Portfolio closed with its first bounded packet preserved and no promotion or widening authorized.
- Business/user impact: The repo now has a truthful read-only Shadow NAV / alert packet tied to the research-v0 kernel and historical Phase 50 reference artifacts, but leadership is explicitly protected from over-interpreting it because the research lane remains below the locked C3 baseline on Sharpe / CAGR and the reference-only alert lane is `RED`.
- Current readiness: Phase 59 closed; any Phase 60 or widened Shadow Portfolio work requires a later explicit approval token.

## 2) Delivered Scope vs Deferred Scope
- Delivered:
  - Bounded read-only Shadow Portfolio runner and focused tests.
  - First same-window / same-cost structural Shadow NAV summary, daily evidence, and delta-vs-C3 artifact.
  - Reference-only alert contract over the historical Phase 50 shadow artifacts.
  - Bounded dashboard reader for the `phase59_*` artifacts.
  - Evidence-only review / no-promotion / no-widening disposition and clean phase closeout.
- Deferred:
  - Any unified governed holdings / turnover surface (Owner: PM/CEO approval required; Target: future explicit packet).
  - Any stable shadow / multi-sleeve stack execution or post-2022 audit work (Owner: PM/CEO; Target: future explicit packet).
  - Any promotion or widened Shadow Portfolio execution beyond the first bounded packet (Owner: PM/CEO; Target: explicit review packet).

## 3) Derivation and Formula Register
| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-59-01 | `selected_variant = argmax(selection_count, median_outer_test_sharpe, variant_id_ascending)` | `selection_count`, `median_outer_test_sharpe`, `variant_id` | Locks the research-side variant selector to the on-disk Phase 55 governance evidence | `data/phase59_shadow_portfolio.py`, `docs/notes.md` |
| F-59-02 | `research_shadow_equity_t = cumprod(1 + research_shadow_ret_t)` | `research_shadow_ret_t` | Produces the bounded read-only research-side Shadow NAV surface | `data/phase59_shadow_portfolio.py`, `docs/notes.md` |
| F-59-03 | `holdings_overlap = |shadow_latest_tickers ∩ core_sample_selected_tickers| / max(1, |shadow_latest_tickers|)` | `shadow_latest_tickers`, `core_sample_selected_tickers` | Encodes the reference-only basket overlap alert | `data/phase59_shadow_portfolio.py`, `docs/notes.md` |
| F-59-04 | `gross_exposure_delta = abs(core_gross_exposure_latest - shadow_gross_exposure_latest)` | `core_gross_exposure_latest`, `shadow_gross_exposure_latest` | Encodes the reference-only exposure alert | `data/phase59_shadow_portfolio.py`, `docs/notes.md` |
| F-59-05 | `turnover_delta_rel = turnover_delta_abs / max(abs(shadow_average_turnover), 1e-12)` | `turnover_delta_abs`, `shadow_average_turnover` | Encodes the reference-only turnover alert severity | `data/phase59_shadow_portfolio.py`, `docs/notes.md` |
| F-59-06 | `phase59_review_hold = 1[(research_sharpe_delta < 0) or (research_cagr_delta < 0) or (shadow_reference_alert_level != "GREEN")]` | `research_sharpe_delta`, `research_cagr_delta`, `shadow_reference_alert_level` | Explains why the first packet remains evidence-only and not promotion-ready | `data/phase59_shadow_portfolio.py`, `docs/decision log.md` |

## 4) Logic Chain
| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-59-01 | Phase 55 evidence, Phase 54 locked C3 baseline, `allocator_state`, Phase 50 shadow artifacts | Select governed variant -> build read-only research lane -> build reference-only alert lane -> compare structural metrics to locked C3 / reference thresholds | Keep packet evidence-only if research deltas remain negative or reference alert level is not `GREEN` | Phase 59 summary + evidence + delta-vs-C3 artifacts plus no-promotion closeout |

## 5) Validation Evidence Matrix
| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-PH-01 | `.venv\Scripts\python -m pytest -q` | PASS | `docs/context/e2e_evidence/phase59_full_pytest_20260318.stdout.log`, `docs/context/e2e_evidence/phase59_full_pytest_20260318.stderr.log`, `docs/context/e2e_evidence/phase59_full_pytest_20260318.status.txt` | exit code `0` |
| CHK-PH-02 | `.venv\Scripts\python launch.py --help` | PASS | `docs/context/e2e_evidence/phase59_launch_smoke_20260318.stdout.log`, `docs/context/e2e_evidence/phase59_launch_smoke_20260318.stderr.log`, `docs/context/e2e_evidence/phase59_launch_smoke_20260318.status.txt` | exit code `0` |
| CHK-PH-03 | `.venv\Scripts\python scripts\phase59_shadow_portfolio_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase59_shadow_replay_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase59_shadow_replay_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase59_shadow_replay_delta_vs_c3_20260318.csv` | PASS | `docs/context/e2e_evidence/phase59_shadow_replay_20260318.*` | `selected_variant=v_3516a4bd6b65`, `alert_level=RED` |
| CHK-PH-04 | Reviewer B independent replay with replay_revb output paths | PASS | `docs/context/e2e_evidence/phase59_shadow_replay_revb_20260318.*` | matched replay summary metrics and review/hold reasons |
| CHK-PH-05 | `.venv\Scripts\python -m pytest tests\test_phase59_shadow_portfolio.py tests\test_shadow_portfolio_view.py tests\test_release_controller.py -q` | PASS | `docs/context/e2e_evidence/phase59_targeted_tests_20260318.*` | focused packet/view/release-controller coverage |
| CHK-PH-06 | `.venv\Scripts\python scripts/build_context_packet.py` and `--validate` | PASS | `docs/context/e2e_evidence/phase59_execution_context_build_20260318.*`, `docs/context/e2e_evidence/phase59_execution_context_validate_20260318.*` | exit code `0` |

## 6) Open Risks / Assumptions / Rollback
- Open Risks:
  - The research lane remains below the locked C3 baseline on Sharpe / CAGR.
  - The reference-only alert lane is `RED` (`holdings_overlap = 0.0`, `gross_exposure_delta = 1.0`).
  - No unified governed holdings / turnover surface exists yet.
- Assumptions:
  - Phase 59 remains closed unless a new explicit approval packet is issued.
  - Phase 50 artifacts remain reference-only and are not reinterpreted as governed comparator evidence.
- Rollback Note:
  - Revert Phase 59 closeout docs/context/SAW and `data/processed/phase59_*` only; do not alter `D-328`, `D-327`, `D-326`, prior-sleeve artifacts, or the Phase 53 kernel.

## 6.1) Data Integrity Evidence (Required)
- Atomic write path proof:
  - `scripts/phase59_shadow_portfolio_runner.py` writes summary/evidence/delta via `_atomic_json_write` and `_atomic_csv_write` (temp -> replace).
- Row-count sanity:
  - Summary `packet_id = PHASE59_SHADOW_MONITOR_V1`, `catalog_rows = 105081`, `selected_variant.observed_rows = 20`, `shadow_reference.curve_rows = 31`.
  - Reviewer-B replay summary matches the bounded replay metrics and `review_hold_reasons`.
- Runtime/performance sanity:
  - Full regression, launch smoke, and both replay commands completed successfully after the Windows lock-liveness bug in `release_controller` was removed.

## 7) Next Phase Roadmap
| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | Explicit CEO approval for any next packet | Exact in-thread approval token recorded | PM/CEO |
| 2 | Decide whether next scope is widened Phase 59 or Phase 60 | Review packet disposition accepted and scope boundary chosen explicitly | PM/Architecture |
| 3 | Future unified shadow holdings surface (if approved later) | Real governed holdings / turnover contract exists before any new alert semantics are claimed | Backend/Ops |

## 8) New Context Packet (for /new)
- What was done:
  - Closed Phase 59 as evidence-only / no promotion / no widening with the first bounded Shadow Portfolio artifacts preserved.
  - Captured focused tests, full regression, runtime smoke, and dual replay evidence under `docs/context/e2e_evidence/`.
- What is locked:
  - `D-284`, `D-292`, `D-309`, `D-311`, `D-312`, `D-313`, `D-314`, `D-315`, `D-316`, `D-317`, `D-318`, `D-319`, `D-320`, `D-321`, `D-322`, `D-323`, `D-324`, `D-325`, `D-326`, `D-327`, `D-328`, `D-329`, `D-330`, `RESEARCH_MAX_DATE = 2022-12-31`, and same-window/same-cost/`core.engine.run_simulation` discipline.
  - Phase 59 is closed; no promotion or widening without a new explicit packet.
- What remains:
  - Any Phase 60 or widened Shadow Portfolio work remains blocked pending a separate explicit approval token.
- Next-phase roadmap summary:
  - Explicit approval token -> bounded next-scope selection -> future unified shadow surface only if explicitly approved.
- Immediate first step:
  - Await explicit CEO approval packet before any Phase 60 or widened Shadow Portfolio work.

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve next phase" to start the next bounded packet.
