# SAW Report: Stream 1 Cleanup Slice - Legacy Helper Retirement (Round 5)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Stream 1 Truth Layer (Data)

RoundID: R20260301-STREAM1-CLEANUP-R5
ScopeID: STREAM1-CLEANUP-HELPER-RETIRE-R5
Scope: Retire legacy annual-liquidity helper surface and keep tests aligned only to active t-1 runtime selector semantics.

Ownership Check:
- Implementer: `Halley` (`019ca97f-5985-71f1-8635-94a82b57953d`)
- Reviewer A: `Einstein` (`019ca983-a589-7913-8166-aa9c04bbf86e`)
- Reviewer B: `Chandrasekhar` (`019ca983-a5ad-7ea0-9909-a9dd7a4d4edd`)
- Reviewer C: `Dalton` (`019ca983-a5c2-75b3-a536-db83d17fd627`)
- Parent reconciler: Codex
- Result: Implementer and reviewers are distinct agents/roles.

Acceptance Checks:
- CHK-01: Retire `_select_permnos_from_annual_liquidity` callable surface from `data/feature_store.py`.
- CHK-02: Active runtime selector path remains `_select_universe_permnos -> _top_liquid_permnos_yearly_union`.
- CHK-03: Active t-1 selector regressions remain covered (`as-of anchor`, `same-day spike exclusion`, `patch precedence`).
- CHK-04: Add regression proving yearly-union dispatch uses active anchor selector path.
- CHK-05: Targeted Stream 1 matrix remains green after cleanup.
- CHK-06: Compile gate passes for touched files.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Legacy helper surface preserved potential future reintroduction of historical yearly-block semantics | Removed helper and replaced helper-level tests with active-dispatch regression | Implementer | Resolved |
| Low | Test suite could drift toward validating retired internals instead of runtime path contracts | Kept only runtime-path tests and strengthened dispatch contract coverage | Implementer | Resolved |

Scope Split Summary:
- in-scope:
  - Retired legacy helper surface.
  - Updated tests to runtime-selector-only contract.
  - Verified active selector behavior unchanged and deterministic.
- inherited out-of-scope:
  - none.

Document Changes Showing:
1. `data/feature_store.py`
   - Removed `_select_permnos_from_annual_liquidity`.
   - Active dispatch/selector path preserved unchanged.
   - Reviewer status: A PASS, B PASS, C PASS.
2. `tests/test_feature_store.py`
   - Removed retired-helper tests.
   - Added `test_select_universe_permnos_yearly_union_uses_active_anchor_selector`.
   - Retained t-1 anchor/same-day spike/patch precedence regressions.
   - Reviewer status: A PASS, B PASS, C PASS.
3. `docs/phase_brief/phase31-brief.md`
   - Added round update for cleanup slice.
   - Reviewer status: Parent reconciliation.
4. `docs/decision log.md`
   - Added D-204 entry for helper-retirement cleanup.
   - Reviewer status: Parent reconciliation.
5. `docs/lessonss.md`
   - Added Stream 1 cleanup lesson and guardrail row.
   - Reviewer status: Parent reconciliation.

Document Sorting (GitHub-optimized):
1. `docs/phase_brief/phase31-brief.md`
2. `docs/lessonss.md`
3. `docs/decision log.md`
4. `docs/saw_reports/saw_stream1_cleanup_round5_20260301.md`

Evidence:
- `.venv\Scripts\python -m pytest -q tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py`
- Result: pass (`43 passed`)
- `.venv\Scripts\python -m py_compile data/feature_store.py tests/test_feature_store.py`
- Result: pass
- Reviewer rechecks:
  - Reviewer A PASS (active semantics unchanged + t-1 tests intact),
  - Reviewer B PASS (no runtime references to retired helper, deterministic/fail-safe behavior),
  - Reviewer C PASS (t-1 PIT integrity and query-path sanity preserved).

Open Risks:
- None in-scope for this cleanup round.

Next action:
- Proceed to Stream 5 Sprint+1 broker payload telemetry constraints as previously queued.

ClosurePacket: RoundID=R20260301-STREAM1-CLEANUP-R5; ScopeID=STREAM1-CLEANUP-HELPER-RETIRE-R5; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=none; NextAction=proceed-to-stream5-sprint-plus-1-broker-payload-telemetry-constraints
ClosureValidation: PASS
SAWBlockValidation: PASS
