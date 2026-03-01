# SAW Report: Stream 1 PiT Look-Ahead Bias Reconciliation (Round 4)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Stream 1 Truth Layer (Data)

RoundID: R20260301-STREAM1-PIT-R4
ScopeID: STREAM1-PIT-RECON-R4
Scope: Reconcile Stream 1 PiT sprint to enforce dual-time invariants across primary/fallback paths, strict-binding runtime integration, deterministic dedupe, and t-1 universe selection.

Ownership Check:
- Implementer: Codex (primary agent)
- Reviewer A: `Confucius` (`019ca972-89c7-71d0-8f3a-401437b4c383`)
- Reviewer B: `Epicurus` (`019ca975-e9ac-76f0-8af8-b6b577a53f81`)
- Reviewer C: `Kuhn` (`019ca975-e9ba-7920-bd50-53e749e05dbc`)
- Result: Implementer and reviewers are distinct agents/roles.

Acceptance Checks:
- CHK-01: Loader/snapshot enforce dual-time PiT gate (`published_at <= simulation_ts` and `release_date <= simulation_ts`).
- CHK-02: Q1/Q3 restatement chronology flips exactly at `published_at` timestamp boundary.
- CHK-03: Fallback daily fundamentals path respects valid-time (`release_date <= trading date`) and blocks pre-release leakage.
- CHK-04: Quality gate rejects future-valid observations (non-negative age requirement).
- CHK-05: Equal-key/equal-`ingested_at` quarterly dedupe is deterministic.
- CHK-06: Strict binding (`T0_STRICT_SIMULATION_TS_BINDING=1`) is plumbed through feature-store path and remains fail-closed.
- CHK-07: Active yearly-union selector enforces strict t-1 (`date < anchor`) and excludes same-day spikes.
- CHK-08: Targeted Stream 1 regression + compile gates pass.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Fallback daily fundamentals could surface rows before `release_date` under panel failure path | Added release-date valid-time mask across fallback/normal daily matrices and regression test | Implementer | Resolved |
| High | Strict binding could hard-fail feature-store runtime in strict env due to missing token plumbing | Added strict-mode token generation and token/secret plumbing from feature-store into fundamentals loaders; added regression test | Implementer | Resolved |
| High | Quarterly dedupe could be non-deterministic under equal-key/equal-`ingested_at` ties | Added deterministic `_row_hash` tie-break sort key before dedupe and deterministic regression test | Implementer | Resolved |
| Medium | Legacy annual-liquidity helper retains full-year semantics and could be reused accidentally in future refactors | Kept active runtime path on strict t-1 selector; carried helper cleanup as separate hardening follow-up | Owner: Stream 1 backlog | Open |

Scope Split Summary:
- in-scope:
  - Closed all in-scope Critical/High findings raised by initial Reviewer A/B/C BLOCK passes.
  - Added regression coverage for fallback valid-time, strict binding integration, and deterministic dedupe ties.
  - Converted active yearly-union runtime selector to strict t-1 daily-liquidity ranking.
  - Updated docs/runbook/decision/lessons/brief for this reconciliation round.
- inherited out-of-scope:
  - Legacy helper `_select_permnos_from_annual_liquidity` remains for compatibility/tests and is not used by active runtime selector flow.

Document Changes Showing:
1. `data/fundamentals.py`
   - Added deterministic row-hash tie-break dedupe, strict binding helpers/validation, dual-time gate application, fallback valid-time masking, and non-negative age quality gate.
   - Reviewer status: A PASS, B PASS, C PASS.
2. `data/feature_store.py`
   - Active yearly-union path now strict t-1 (`date < anchor`) last-tradable-date liquidity ranking; strict binding token plumbing to fundamentals calls.
   - Reviewer status: A PASS, B PASS, C PASS.
3. `tests/test_bitemporal_integrity.py`
   - Added exact timestamp crossover, fallback valid-time no-leak, and deterministic dedupe tie regression tests.
   - Reviewer status: A PASS, C PASS.
4. `tests/test_fundamentals_daily.py`
   - Updated fallback monkeypatch signature compatibility for new optional binding kwargs.
   - Reviewer status: C PASS.
5. `tests/test_feature_store.py`
   - Added same-day spike exclusion + patch precedence regressions and strict-binding plumbing regression.
   - Reviewer status: A PASS, B PASS, C PASS.
6. `docs/phase_brief/phase31-brief.md`
   - Added Stream 1 PiT reconciliation round update with scope and evidence commands.
   - Reviewer status: Parent reconciliation.
7. `docs/runbook_ops.md`
   - Added optional strict-binding env contract and explicit yearly-union t-1 runtime contract.
   - Reviewer status: Parent reconciliation.
8. `docs/notes.md`
   - Added Stream 1 PiT addendum with formulas and code loci.
   - Reviewer status: Parent reconciliation.
9. `docs/lessonss.md`
   - Appended Stream 1 PiT reconciliation lesson row and guardrail.
   - Reviewer status: Parent reconciliation.
10. `docs/decision log.md`
   - Added D-203 decision entry for this reconciliation round.
   - Reviewer status: Parent reconciliation.

Document Sorting (GitHub-optimized):
1. `docs/phase_brief/phase31-brief.md`
2. `docs/runbook_ops.md`
3. `docs/notes.md`
4. `docs/lessonss.md`
5. `docs/decision log.md`
6. `docs/saw_reports/saw_stream1_pit_reconciliation_round4_20260301.md`

Evidence:
- `.venv\Scripts\python -m pytest -q tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py`
- Result: pass (`45 passed`)
- `.venv\Scripts\python -m py_compile data/fundamentals.py data/feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py`
- Result: pass
- Reviewer recheck summaries:
  - Reviewer A: PASS (fallback valid-time + active t-1 selector contract verified),
  - Reviewer B: PASS (strict binding integration + fail-closed coherence verified),
  - Reviewer C: PASS (fallback valid-time, deterministic dedupe, t-1 query integrity verified).

Open Risks:
- Medium inherited: legacy `_select_permnos_from_annual_liquidity` helper still exists for compatibility/test surfaces and can be removed in a dedicated cleanup slice.
- Medium operational: strict binding remains env-policy dependent and requires secure secret provisioning discipline.

Next action:
- Execute a bounded Stream 1 cleanup slice to deprecate/remove legacy annual-liquidity helper and align remaining helper tests to active t-1 runtime semantics.

ClosurePacket: RoundID=R20260301-STREAM1-PIT-R4; ScopeID=STREAM1-PIT-RECON-R4; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=legacy-annual-liquidity-helper-compatibility-and-strict-binding-env-policy; NextAction=run-stream1-cleanup-slice-to-retire-legacy-helper-and-align-tests
ClosureValidation: PASS
SAWBlockValidation: PASS
