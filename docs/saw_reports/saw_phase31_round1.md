SAW Report: Phase 31 Sovereign Execution Hardening Round 1

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Execution Trust Boundary, Runtime Ops, Data Integrity, Strategy Semantics
Ownership Check: PASS (Implementer and reviewers are distinct agents)
- Implementer agents: Newton (`019ca891-0088-7a23-9ba5-192704b0f1c5`), Lovelace (`019ca891-01c4-7e11-a1a5-fb2818ea0b21`), Nash (`019ca891-0176-7813-9bda-f43c96d079d6`), Plato (`019ca8a2-a9bd-7d93-8c5b-9447a2fe3a77`), Mill (`019ca8a2-a9ce-7da1-9837-538c1d247ce2`)
- Reviewer A: Faraday (`019ca89d-1760-76e2-a435-7d35b9f11018`)
- Reviewer B: Leibniz (`019ca89d-183b-7133-85da-58546bc1cfb0`)
- Reviewer C: Rawls (`019ca89d-1907-7e22-bcb6-c0933717f03d`)

RoundID: RND-20260301-PH31-SOVEREIGN-HARDENING-R1
ScopeID: SCOPE-PH31-TRUST-SPOOL-SEMANTIC-HARDENING

Scope
- In-scope: `execution/signed_envelope.py`, `execution/microstructure.py`, `main_console.py`, `strategies/alpha_engine.py`, `strategies/ticker_pool.py`, `core/dashboard_control_plane.py`, touched tests, and required docs updates.
- Out-of-scope: new strategy research, broker API feature expansion, full phase-end handover/context packet refresh.

Acceptance Checks
- CHK-01: Atomic replay check+append and duplicate replay rejection.
- CHK-02: Malformed replay ledger quarantine without blocking valid submits.
- CHK-03: Idempotent sink replay under partial failure.
- CHK-04: Quarantine + cursor progress for schema-invalid and stale partial spool records.
- CHK-05: Local-submit telemetry durability gate fail-closed behavior.
- CHK-06: Semantic coercion hardening (snapshot contracts, numeric score ranking, explicit boolean parsing).
- CHK-07: Runtime invariant enforcement (`ValueError` guards, malformed-date fail-fast, atomic watchlist persistence).
- CHK-08: Integrated regression matrix pass.

Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Critical | Schema-valid invalid spool records could be silently dropped with irreversible offset advance | Added schema validation + quarantine reasons + cursor advancement tests | Implementer | Resolved |
| High | Trailing partial spool lines could stall drain indefinitely | Added stale trailing-partial quarantine policy and regression | Implementer | Resolved |
| High | Legacy parquet single-file export could duplicate rows after cursor reset/loss | Added dedupe fallback on `{record_id, uid, _spool_record_uid}` and regression | Implementer | Resolved |
| High | Local submit could report success while telemetry flush unhealthy | Added bounded durability gate before success/notify; fail-closed on gate failure | Implementer | Resolved |
| High | Spool/cursor writes lacked explicit crash-durability fsync semantics | Added `flush + fsync` and parent-dir fsync best effort in atomic paths | Implementer | Resolved |
| High | Alpha selection could sort lexical/object `composite_score` incorrectly | Enforced numeric ranking with stable tie-break and regression | Implementer | Resolved |
| High | Weak-quality/style boolean strings were misparsed, suppressing short signals | Added explicit boolean token normalization and regressions | Implementer | Resolved |
| Medium | `score_col` remains no-op in current raw-geometry ranking path | Carried as follow-up design debt (no in-scope Critical/High remain) | Owner: Phase 31 follow-up | Open |
| Medium | Spool pipeline still uses thread-level locking, no cross-process file lock | Carried as runtime hardening follow-up | Owner: Phase 31 follow-up | Open |
| Medium | Replay lock path has no timeout budget and can block | Carried as operational hardening follow-up | Owner: Phase 31 follow-up | Open |
| Medium | `plan_auto_update` null-date handling can raise type error | Carried as control-plane follow-up | Owner: Phase 31 follow-up | Open |

Scope Split Summary
- in-scope findings/actions: all in-scope Critical/High findings from reviewer A/B/C were reconciled and re-tested to green.
- inherited out-of-scope findings/actions: none in this round.

Document Changes Showing
- `execution/signed_envelope.py`: atomic replay lock + malformed-row quarantine + durable append; Reviewer status: Cleared
- `execution/microstructure.py`: idempotent sink replay, schema/stale-line quarantine, offset reset/compaction, durability fsync hardening; Reviewer status: Cleared
- `main_console.py`: local-submit durability gate and accepted-result semantics; Reviewer status: Cleared
- `strategies/alpha_engine.py`: snapshot contract hardening, trend-veto parser, numeric candidate ranking; Reviewer status: Cleared
- `strategies/ticker_pool.py`: runtime guard hardening, malformed-date fail-fast, boolean normalization; Reviewer status: Cleared
- `core/dashboard_control_plane.py`: atomic watchlist save path; Reviewer status: Cleared
- `tests/test_signed_envelope_replay.py`: replay race/malformed ledger regressions; Reviewer status: Cleared
- `tests/test_execution_microstructure.py`: idempotence/corruption/quarantine/durability regressions; Reviewer status: Cleared
- `tests/test_main_console.py`: telemetry durability gate regressions; Reviewer status: Cleared
- `tests/test_alpha_engine.py`: snapshot and numeric-score ordering regressions; Reviewer status: Cleared
- `tests/test_ticker_pool.py`: boolean-token and invariant/date policy regressions; Reviewer status: Cleared
- `tests/test_dashboard_control_plane.py`: atomic persistence regressions; Reviewer status: Cleared
- `docs/phase_brief/phase31-brief.md`: phase scope/check matrix for this round; Reviewer status: Cleared
- `docs/spec.md`: FR-150 phase section addendum; Reviewer status: Cleared
- `docs/prd.md`: phase scope addendum; Reviewer status: Cleared
- `docs/runbook_ops.md`: Phase 31 operational validation pack; Reviewer status: Cleared
- `docs/notes.md`: formula/contract mapping for replay/spool/durability semantics; Reviewer status: Cleared
- `docs/lessonss.md`: round lesson entry; Reviewer status: Cleared
- `docs/decision log.md`: D-149 decision record; Reviewer status: Cleared

Document Sorting (GitHub-optimized)
1. `docs/prd.md`
2. `docs/spec.md`
3. `docs/phase_brief/phase31-brief.md`
4. `docs/runbook_ops.md`
5. `docs/notes.md`
6. `docs/lessonss.md`
7. `docs/decision log.md`

Checks Summary
- ChecksTotal: 8
- ChecksPassed: 8
- ChecksFailed: 0

SAW Verdict: PASS
ClosurePacket: RoundID=RND-20260301-PH31-SOVEREIGN-HARDENING-R1; ScopeID=SCOPE-PH31-TRUST-SPOOL-SEMANTIC-HARDENING; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=Medium_followups_remain_for_cross_process_spool_lock_replay_lock_timeout_score_col_semantics_and_null_date_staleness; NextAction=Proceed_with_phase31_merge_and_schedule_medium_hardening_followup
ClosureValidation: PASS
SAWBlockValidation: PASS

Evidence
- `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py` -> PASS
- `.venv\Scripts\python -m py_compile execution/signed_envelope.py execution/microstructure.py main_console.py strategies/alpha_engine.py strategies/ticker_pool.py core/dashboard_control_plane.py tests/test_signed_envelope_replay.py tests/test_execution_microstructure.py tests/test_alpha_engine.py tests/test_ticker_pool.py tests/test_dashboard_control_plane.py` -> PASS

Assumptions
- Phase 31 close criteria in this round require in-scope Critical/High closure plus integrated targeted regression, not full repository phase-end closeout.

Open Risks:
- Medium follow-ups remain: cross-process spool file-locking model, replay lock timeout budget, DuckDB growth-path throughput, `score_col` no-op semantic debt, and null-date staleness handling.
Next action:
- Execute a focused medium-risk hardening sprint and re-run SAW review before phase-close declaration.

Rollback Note
- Revert all files listed in this report as one batch if this round is rejected.
