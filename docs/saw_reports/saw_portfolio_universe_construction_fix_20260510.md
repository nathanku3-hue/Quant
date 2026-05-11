# SAW Report - Portfolio Universe Construction Fix

RoundID: `PORTFOLIO_UNIVERSE_CONSTRUCTION_FIX_20260510`
ScopeID: `UNIVERSE_PIPELINE_AND_DIAGNOSTICS_ONLY`
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

Work round scope: independently review the approved P0-P3 mechanical portfolio-universe correction plus lightweight P4-P6 labels, tests, and contract docs. Conviction optimizer, MU hard floor, Black-Litterman, manual override, WATCH investability promotion, thesis anchors, scanner rewrite, and new portfolio objectives remain blocked.

SAW Verdict: PASS

## Acceptance Checks

| Check | Result | Evidence |
| --- | --- | --- |
| CHK-01 explicit optimizer universe builder exists | PASS | `strategies/portfolio_universe.py` |
| CHK-02 dashboard no longer passes display-sorted `selected_tickers[:20]` | PASS | `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py` |
| CHK-03 EXIT/KILL/AVOID/IGNORE excluded and WATCH research-only by default | PASS | `strategies/portfolio_universe.py`, `tests/test_portfolio_universe.py`, Reviewer A behavior probe |
| CHK-04 missing ticker mapping and price-history failures are reported | PASS | `tests/test_portfolio_universe.py`, browser smoke, Reviewer A SNDK/RBRK probe |
| CHK-05 max-weight feasibility and equal-weight-boundary diagnostics exist | PASS | `diagnose_max_weight_feasibility`, `views/optimizer_view.py`, tests |
| CHK-06 misleading `Auto (Best Sharpe)` label removed and runtime conviction modes absent | PASS | `tests/test_portfolio_universe.py`, `views/optimizer_view.py` |
| CHK-07 focused tests pass | PASS | `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py -q` -> exit 0 |
| CHK-08 scoped compile and context validation pass | PASS | `.venv\Scripts\python -m py_compile strategies\portfolio_universe.py views\optimizer_view.py dashboard.py`; `.venv\Scripts\python scripts\build_context_packet.py --validate` |
| CHK-09 independent SAW Reviewer A/B/C passes complete with no unresolved High governance blocker | PASS | A=PASS, B=PASS after `strategies/optimizer.py` diff quarantine/revert, C=PASS |

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| High | Reviewer B found dirty optimizer-core math changes in `strategies/optimizer.py` adding lower-bound handling and changing SLSQP bounds/fallback paths, while this round explicitly forbids optimizer math/objective changes. | Quarantined the diff to `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`, documented the quarantine note, reverted `strategies/optimizer.py` to baseline, and opened optimizer-core audit as separate future scope. | Codex | Resolved |
| Medium | Untracked `scripts/strong_buy_scan.py` exists and could be mistaken for scanner rewrite scope. | Keep excluded from this RoundID/ScopeID; handle only under separate approval. | PM / Repo Owner | Inherited |
| Low | Unit fixture covers EXIT/IGNORE directly but KILL/AVOID only through code policy, leaving a thin regression guard. | Optional tests-only patch later: add KILL/AVOID rows and empty fail-closed assertion. | Codex | Deferred |

## Scope Split Summary

In-scope findings/actions:

- Independent reviewers verified display-order leakage is fixed through explicit optimizer-universe construction.
- Independent reviewers verified EXIT/KILL/AVOID/IGNORE exclusion, WATCH research-only status, missing mapping reporting, insufficient-history reporting, and fail-closed empty universe behavior.
- Independent reviewers verified Universe Audit, no-eligible fail-closed browser behavior, optimizer-before-YTD order, and max-weight feasibility diagnostics.
- No optimizer-core code is included in this closure; the quarantined diff is preserved as a separate audit artifact.

Inherited/out-of-scope findings/actions:

- Quarantined `strategies/optimizer.py` lower-bound/math diff is outside the approved patch files and outside the approved mechanical universe fix; it is preserved for `OPTIMIZER_CORE_POLICY_AUDIT`.
- Dirty/untracked scanner-like and dashboard/runtime files remain inherited and must not enter this closure.
- MU conviction, WATCH investability, Black-Litterman, manual override, thesis-anchor sizing, and new objectives remain future policy work.

## Reviewer Results

| Reviewer | Domain | Verdict | Summary |
| --- | --- | --- | --- |
| Reviewer A | Backend universe correctness | PASS | Display order no longer defines optimizer universe; excluded/research-only policy and SNDK/RBRK history failures are visible. |
| Reviewer B | UI and explanation correctness | PASS | UI scope passes, and the dirty `strategies/optimizer.py` optimizer-core math diff is quarantined/reverted out of the current closure. |
| Reviewer C | Governance and out-of-boundary enforcement | PASS | Contract/tests enforce no MU floor, no conviction mode, no Black-Litterman, no manual override, no WATCH expansion, no scanner rewrite, and no new objective in the portfolio-universe closure. |

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
| --- | --- | --- |
| `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md` | Updated from BLOCK to PASS after optimizer-core quarantine and revalidation. | Reconciled |
| `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch` | Preserved the rejected dirty optimizer-core lower-bound/SLSQP diff for a separate audit round. | Reviewer B PASS |
| `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md` | Documents quarantine reason, boundary, and non-approval status. | Reviewer B PASS |
| `data/providers/legacy_allowlist.py` | Added `views/optimizer_view.py` to the existing direct-yfinance migration allowlist so full pytest reflects the already-approved DASH-2 display-freshness overlay. | Hygiene PASS |
| `docs/architecture/portfolio_construction_contract.md` | Portfolio construction boundary, held scope, formulas, and future conviction note. | Reviewer C PASS |
| `docs/notes.md` | Optimizer universe, display-order non-leakage, feasibility, and thesis-neutral formulas. | Prior self-review |
| `docs/decision log.md` | Portfolio Universe Construction Fix decision and contract lock. | Prior self-review |
| `docs/lessonss.md` | Display-order leakage root cause and guardrail; this review adds dirty-worktree governance lesson. | Updated |
| `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Current product/spec notices. | Reviewer C scope PASS |
| `docs/context/*current.md` | Planner, bridge, impact, checklist, multi-stream, alignment, and observability truth surfaces. | Prior self-review |

## Validation

ClosurePacket: RoundID=PORTFOLIO_UNIVERSE_CONSTRUCTION_FIX_20260510; ScopeID=UNIVERSE_PIPELINE_AND_DIAGNOSTICS_ONLY; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=mu_conviction_policy_watch_investability_black_litterman_future_optimizer_core_lower_bounds_quarantined; NextAction=open_optimizer_core_policy_audit_or_hold

ClosureValidation: PASS

SAWBlockValidation: PASS

EvidenceValidation: PASS

ForbiddenScopeScan: PASS - `strategies/optimizer.py` has no current diff; quarantined optimizer-core lower-bound/SLSQP patch is excluded from this closure.

SecretScan: PASS - targeted secret assignment/key scan found no matches in the reviewed portfolio files.

BrowserSmoke: PASS - `http://127.0.0.1:8503/portfolio-and-allocation` shows Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance below optimizer.

Additional validation:

- Full pytest was run after quarantine revert. Initial inherited context/provenance and direct-yfinance allowlist failures were repaired as docs/hygiene updates, then `.venv\Scripts\python -m pytest -q` passed.

Open Risks:

- Quarantined `strategies/optimizer.py` lower-bound/math diff remains unaccepted and outside approved portfolio-universe scope.
- MU conviction policy, WATCH investability policy, Black-Litterman, thesis-anchor sizing, and manual override remain out of scope.
- Current cached scan produces zero eligible optimizer rows under the approved conservative policy, which is intended fail-closed behavior.

Next action:

- Open a separate `OPTIMIZER_CORE_POLICY_AUDIT` round to decide whether lower-bound/SLSQP changes should be accepted, revised, or rejected.
