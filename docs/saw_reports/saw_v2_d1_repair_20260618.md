# SAW Report - V2 PEAD D1 Repair

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-project-scope | Domains: Data, Quant Strategy, Runtime/Ops, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/v2-pead-d1-repair-brief.md

RoundID: `ROUND-20260618-V2-D1-REPAIR`
ScopeID: `V2_D1_SUE_FORMULA_LIQUIDITY_ATOMIC_REPAIR`

## Scope and Ownership

Work round scope: repair the bounded D1 PEAD SUE builder, tests, artifact/manifest bundle, and docs-as-code surfaces without widening into D2 returns, Ken French benchmark acquisition, provider replacement, strategy interpretation, UI, alerts, ranking, promotion, or broker paths.

Owned files changed in this round:

- `scripts/pead_d1_sue_builder.py`
- `tests/test_pead_d1_sue.py`
- `data/processed/pead_d1_sue_signal.parquet`
- `data/processed/pead_d1_sue_signal.parquet.manifest.json`
- `docs/phase_brief/v2-pead-d1-repair-brief.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`
- `docs/saw_reports/saw_v2_d1_repair_20260618.md`

Acceptance checks:

- `CHK-01`: D1 uses raw numeric `epspxq` under compatibility field `adj_eps`; `ajexq` is not divided.
- `CHK-02`: Duplicate `(gvkey, rdq)` identities are removed before exact t-4 lag and rolling transforms.
- `CHK-03`: Raw SUE, clipped SUE, lagged shares, and flag-only liquidity semantics are implemented and tested.
- `CHK-04`: Parquet/manifest publication uses temp-to-replace writes, and empty processed-output paths preserve prior outputs.
- `CHK-05`: Production D1 artifact/manifest are rebuilt and internally consistent.
- `CHK-06`: Focused D1/PEAD tests, compile, dry-run, context validation, and context hygiene pass.
- `CHK-07`: Docs-as-code and current truth surfaces record formulas, quality metrics, limitation, rollback, and next step.
- `CHK-08`: Reviewer A final strategy/formula re-review returns PASS with no in-scope Critical/High findings.
- `CHK-09`: Reviewer B final runtime/ops re-review returns PASS with no in-scope Critical/High findings.
- `CHK-10`: Reviewer C final data-integrity/performance re-review returns PASS with no in-scope Critical/High findings.

## Subagent Passes

Implementer pass: PASS. The implementer repaired D1 formula, stage order, SUE clipping, liquidity flag, atomic write path, quality manifest, empty-output guard, and tests.

Reviewer A pass: PASS. Strategy/formula review confirmed raw `epspxq` without `ajexq`, early RDQ deduplication, exact t-4 continuity, raw/clipped SUE coexistence, liquidity flag-only behavior, current-vintage limitation disclosure, and no D2/provider widening.

Reviewer B pass: PASS. Runtime/ops review confirmed the prior High empty-output overwrite risk is fixed for dry-run and production paths, zero-safe summary output exists, parquet replacement precedes manifest replacement, temp cleanup is covered, and final artifact/manifest state is consistent.

Reviewer C pass: PASS. Data-integrity/performance review confirmed 346,511 rows, 233,586 valid SUE rows, zero duplicate `(gvkey, rdq)` groups, zero exact-t4 failures for valid rows, quality metrics below threshold, no D1 temp files, and no D2/provider widening.

Ownership check: PASS. Implementer and Reviewers A/B/C were different agents. Reviewers were read-only and scoped to D1-owned files/evidence.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Early implementation could promote an empty Parquet before later summary failure. | Added pre-write empty-output guard and dry-run/non-dry-run preservation regressions. | Implementer / Reviewer B | Fixed |
| Medium | Duplicate `(gvkey, rdq)` rows could contaminate lag state when deduplication occurred after stateful transforms. | Moved RDQ identity deduplication before t-4 lag and rolling transforms; added counterexample regression. | Implementer / Reviewer A/C | Fixed |
| None | Final Reviewer A found no in-scope Critical/High formula defects. | No further fix required. | Reviewer A | PASS |
| None | Final Reviewer B found no in-scope Critical/High runtime/ops defects. | No further fix required. | Reviewer B | PASS |
| None | Final Reviewer C found no in-scope Critical/High data-integrity/performance defects. | No further fix required. | Reviewer C | PASS |
| Low | Deterministic temp names and the two-file parquet/manifest publish window remain possible future hardening items. | Carry as future hardening; current D1 atomic order and preservation tests pass. | Future Data/Ops | Non-blocking |
| Low | Current-vintage Compustat EPS may include restatement hindsight. | Limitation recorded in manifest/docs; strict filing-vintage PIT EPS remains out of scope. | Future Data PIT | Non-blocking |

## Scope Split Summary

in-scope findings/actions:

- Removed `ajexq` division from D1 EPS basis.
- Moved RDQ identity deduplication before stateful t-4/rolling transforms.
- Added retained raw SUE plus RDQ cross-sectional clipped SUE.
- Added `cshoq_lag1` and flag-only `liquidity_pass` with units in millions.
- Added manifest quality metrics, current-vintage limitation, atomic publication, and empty-output preservation.
- Rebuilt D1 artifact and refreshed docs/current truth surfaces.

inherited out-of-scope findings/actions:

- D2 total-return level, IID continuity, event-window extraction, and sample reconciliation remain a separate Data round.
- Ken French public benchmark patch remains deferred.
- Provider total-return replacement or reconciliation remains deferred.
- Full repository pytest still has an inherited dashboard lifecycle marker failure outside D1: `tests/test_position_lifecycle.py::test_event_ledger_chart_unchanged_enter_exit_markers`.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `scripts/pead_d1_sue_builder.py` | Raw EPS basis, early RDQ dedup, clipping, liquidity flag, quality gate, current-vintage limitation, empty-output guard, atomic write path. | PASS |
| `tests/test_pead_d1_sue.py` | Added D1 regressions for ajexq removal, units, stage order, clipping, quality gate, atomic write, temp cleanup, manifest ordering, and empty-output preservation. | PASS |
| `data/processed/pead_d1_sue_signal.parquet` | Rebuilt D1 artifact with 346,511 rows and 233,586 valid SUE rows. | PASS |
| `data/processed/pead_d1_sue_signal.parquet.manifest.json` | Manifest records SHA256, quality metrics, methodology, guardrails, and current-vintage limitation. | PASS |
| `docs/phase_brief/v2-pead-d1-repair-brief.md` | Added D1 acceptance, quality metrics, limitation, rollback, and D2-separate next step. | PASS |
| `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Recorded D1 product/spec contract and deferred D2/provider boundaries. | PASS |
| `docs/notes.md` | Added explicit D1 formula registry, artifact evidence, quality gate, empty-output guard, and limitation. | PASS |
| `docs/decision log.md` | Locked bounded D1 repair decision and next D2 separation. | PASS |
| `docs/lessonss.md` | Added guardrails for early identity dedup and empty-output preservation. | PASS |
| `docs/context/*_current.md`, `docs/context/current_context.*` | Refreshed bridge, done, impact, multi-stream, observability, post-phase, planner, and generated context surfaces. | PASS |
| `docs/saw_reports/saw_v2_d1_repair_20260618.md` | Added terminal SAW/SE evidence artifact. | PASS |

## Validation Evidence

- Production rebuild: `.\.venv\Scripts\python scripts\pead_d1_sue_builder.py` -> PASS; 346,511 rows, 233,586 valid SUE rows, 13,216 GVKEYs, RDQ 2015-01-02 through 2026-06-16.
- Artifact hash: computed Parquet SHA256 equals manifest SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Manifest quality metrics: raw `abs(SUE) > 5` count 441, share 0.001887955613778223; clipped count 1,992; liquidity-pass valid rows 204,227.
- Manifest limitation: current-vintage Compustat fundamentals may include restatement hindsight; strict filing-vintage PIT EPS is not established.
- Temp files: D1 expected temp paths absent after rebuild.
- Focused tests: `.\.venv\Scripts\python -m pytest tests\test_pead_d1_sue.py tests\test_pead_event_study.py -q` -> PASS, 27 passed.
- Compile: `.\.venv\Scripts\python -m py_compile scripts\pead_d1_sue_builder.py tests\test_pead_d1_sue.py` -> PASS.
- Dry-run: `.\.venv\Scripts\python scripts\pead_d1_sue_builder.py --dry-run` -> PASS with the same D1 quality metrics and no write.
- Context validation: `.\.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Context hygiene/build tests: `.\.venv\Scripts\python -m pytest tests\test_phase61_context_hygiene.py::test_current_context_promotes_latest_active_phase tests\test_build_context_packet.py -q` -> PASS, 22 passed.
- Whitespace check: `git diff --check -- <D1-owned files>` -> PASS with line-ending warnings only.
- Full-suite residual: `.\.venv\Scripts\python -m pytest tests\test_position_lifecycle.py::test_event_ledger_chart_unchanged_enter_exit_markers -q` -> FAIL, inherited dashboard lifecycle marker test outside D1.
- Reviewer A final re-review -> PASS; no in-scope Critical/High findings.
- Reviewer B final re-review -> PASS; no in-scope Critical/High findings.
- Reviewer C final re-review -> PASS; no in-scope Critical/High findings.

## SE Evidence Map

Scope line: stream=Data; stage=Final Verification; owner=parent-agent; round_exec_utc=2026-06-18T14:25:06Z.

| task_id | task | artifact | check | status | evidence_id |
|---|---|---|---|---|---|
| TSK-01 | Repair D1 formula, stage order, clipping, liquidity, quality gate, empty-output guard, and atomic publication. | `scripts/pead_d1_sue_builder.py`, `tests/test_pead_d1_sue.py` | Code review and focused tests pass. | PASS | EVD-01 |
| TSK-02 | Rebuild and verify D1 artifact/manifest. | `data/processed/pead_d1_sue_signal.parquet`, `.manifest.json` | Row counts, SHA256, quality metrics, limitation, and temp cleanup match contract. | PASS | EVD-02 |
| TSK-03 | Refresh docs-as-code and current truth surfaces. | Product/spec/notes/decision/lesson/context docs | Context build/validate and context hygiene tests pass. | PASS | EVD-03 |
| TSK-04 | Run independent A/B/C review gate and reconcile findings. | Reviewer final outputs and this SAW report | A/B/C PASS; prior High fixed. | PASS | EVD-04 |
| TSK-05 | Record residual out-of-scope checks and next action. | This SAW report and current truth surfaces | D2/provider/deferred scope and inherited dashboard failure are explicit. | PASS | EVD-05 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05

EvidenceRows: EVD-01|ROUND-20260618-V2-D1-REPAIR|2026-06-18T14:25:06Z;EVD-02|ROUND-20260618-V2-D1-REPAIR|2026-06-18T14:25:06Z;EVD-03|ROUND-20260618-V2-D1-REPAIR|2026-06-18T14:25:06Z;EVD-04|ROUND-20260618-V2-D1-REPAIR|2026-06-18T14:25:06Z;EVD-05|ROUND-20260618-V2-D1-REPAIR|2026-06-18T14:25:06Z

EvidenceValidation: PASS

Open Risks: D2 return/IID/event-window repair remains separate; Ken French and provider validation remain deferred; current-vintage Compustat EPS may include restatement hindsight; inherited dashboard lifecycle marker test fails outside D1.

Next action: start_separate_D2_repair_with_gvkey_iid_returns_before_daily_ADV_selection

ClosurePacket: RoundID=ROUND-20260618-V2-D1-REPAIR; ScopeID=V2_D1_SUE_FORMULA_LIQUIDITY_ATOMIC_REPAIR; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=D2_KenFrench_provider_current_vintage_and_inherited_dashboard_test_out_of_scope; NextAction=start_separate_D2_repair_with_gvkey_iid_returns_before_daily_ADV_selection

ClosureValidation: PASS

SAWBlockValidation: PASS
