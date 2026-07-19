# SAW Report: GV-FS0 F1A Certified OPEN Vertical

Mode: `CLOSURE_REPORT`
RoundID: `ROUND-20260718-GV-FS0-F1A-OPEN`
ScopeID: `GV_FS0_F1A_CERTIFIED_OPEN_VERTICAL`
Hierarchy Confirmation: Approved via persisted fallback | Session: current-thread | Trigger: project-init fallback | Domains: portfolio accounting, verifier supervision, certification, read-only presentation | FallbackSource: `docs/spec.md` + `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`.

## Scope

Work round scope: implement only the synthetic `MANUAL_OWNER_PAPER / OPEN` path from canonical decision and book through exact snapshots, two isolated verifier attempts, certification, certification-reference event, certified result, and injected final adapter presentation.

Owned files changed:

- `core/gv_fs0_book.py`
- `core/gv_fs0_certify.py`
- `views/gv_fs0_portfolio_adapter.py`
- `tests/gv_fs0_product/test_open_vertical.py`
- `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_gv_fs0_f1a_open_vertical_20260718.md`

Acceptance checks:

| CheckID | Check | Status |
|---|---|---|
| CHK-01 | Exact source fixture, DecisionEnvelope, fixture hash, decision hash, and book ID are deterministic | PASS |
| CHK-02 | Canonical event trail uses frozen ranks, slots, ownership, IDs, and contiguous semantic sequence | PASS |
| CHK-03 | Five OPEN snapshots reproduce exact cash, shares, receivables, market value, NAV, and contribution | PASS |
| CHK-04 | Verifier input contains only original protocol, decision, price, and source-intent projections | PASS |
| CHK-05 | Exactly two isolated verifier attempts execute; timeout/output overflow terminate fail-closed | PASS |
| CHK-06 | Identical results retain one hash-addressed verifier record; disagreement blocks certification | PASS |
| CHK-07 | All ten certification checks are TRUE before CERTIFIED; frozen result schemas validate | PASS |
| CHK-08 | Final adapter consumes injected presentation/snapshot/certification only and renders no calculated truth | PASS |
| CHK-09 | No permanent bundle file is created or changed | PASS |
| CHK-10 | Product/protocol tests, generator, freeze bootstrap, compile, smoke, and diff hygiene pass | PASS |
| CHK-11 | Distinct independent Reviewer A/B/C agents approve the exact implementation identity | NOT RUN |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Snapshot-only nonnegative checks would not independently prove cash, holdings, and receivable transitions | Certification now replays the canonical event trail and reconciles each valuation snapshot | Implementer | Fixed |
| High | Post-hoc output-size checks could allow an overflowing verifier to run until natural exit | Added concurrent byte capture with early output-limit termination, monotonic deadline, bounded shutdown, and executable cap/timeout tests | Implementer | Fixed |
| Medium | A failing first verifier attempt could prevent execution of the required second attempt | Controller now executes both ordered attempts before failing certification | Implementer | Fixed |
| High | Required reviewer ownership independence cannot be proven with the tools available in this execution environment | Bank the exact implementation commit and run distinct Reviewer A/B/C agents against it | Product owner / next review round | Open |

## Reviewer Lanes

- Reviewer A domain evidence: exact OPEN economics, fee, dividend entitlement/payment, NAV and contribution assertions pass locally. Independent agent review: unavailable.
- Reviewer B domain evidence: process-only verifier, isolated environment, two attempts, timeout/output cap, no permanent writes, and injected adapter tests pass locally. Independent agent review: unavailable.
- Reviewer C domain evidence: deterministic bytes, frozen artifact checks, protocol regression, schema validation, and boundary AST checks pass locally. Independent agent review: unavailable.
- Ownership check: implementer and Reviewer A/B/C must be different agents. This condition is not satisfied in the current environment.

## Scope Split Summary

In-scope completed actions: OPEN primary economics, deterministic identities, snapshots, two verifier attempts, certification, certification-reference event, certified result, read-only adapter injection, tests, and thin behavior/formula documentation.

Inherited/out-of-scope actions: NO_POSITION, permanent bundle publication, publication lock/recovery, default dashboard routing, product CI, complete repository suite, providers, real data, legacy conversion, and FS1 remain unopened.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `core/gv_fs0_book.py` | Added canonical synthetic OPEN decision, event expansion, reducer, snapshots, and economic payload | Local checks PASS; independent review pending |
| `core/gv_fs0_certify.py` | Added bounded two-attempt supervision, formal verifier wrapping, independent reconciliation, certification, reference event, and certified result | Local checks PASS; independent review pending |
| `views/gv_fs0_portfolio_adapter.py` | Added final read-only injected-artifact adapter | Local checks PASS; independent review pending |
| `tests/gv_fs0_product/test_open_vertical.py` | Added exact economics, determinism, failure, supervision, adapter, and boundary tests | PASS |
| `docs/phase_brief/gv-fs0-f1-product-slice-brief.md` | Recorded local F1A implementation evidence and held later gates | PASS |
| `docs/notes.md` | Recorded formulas and exact values | PASS |
| `docs/decision log.md` | Recorded bounded F1A decision and scope | PASS |
| `docs/lessonss.md` | Recorded vertical-slice guardrail | PASS |

Document Sorting: maintained per `docs/checklist_milestone_review.md`; this SAW report is terminal evidence for the current work round and does not trigger nested SAW.

## Validation Evidence

```text
python -m pytest -q tests/gv_fs0_product
35 passed

python -c "import glob,pytest,sys; sys.exit(pytest.main(['-q',*glob.glob('tests/test_gv_fs0_*.py')]))"
137 passed

python scripts/generate_gv_fs0_protocol_v1.py --check
PASS

python scripts/verify_gv_fs0_protocol_freeze.py --mode bootstrap
PASS

python -m compileall -q core/gv_fs0_book.py core/gv_fs0_certify.py views/gv_fs0_portfolio_adapter.py
PASS

git diff --check
PASS
```

## Open Risks

1. The implementation is not banked to a commit in this managed detached worktree.
2. Distinct Reviewer A/B/C agents have not reviewed the exact banked implementation identity.
3. F1B/F1C/F1D remain unopened by design.

## Closure

ChecksTotal: 11
ChecksPassed: 10
ChecksFailed: 1

SAW Verdict: BLOCK

Open Risks: implementation is unbanked in the managed detached worktree and distinct Reviewer A/B/C evidence is unavailable.

Next action: bank the bounded F1A implementation on `codex/gv-fs0-f1-product`, run distinct Reviewer A/B/C against that exact commit, then open F1B only if all in-scope Critical/High findings are closed.

ClosurePacket: RoundID=ROUND-20260718-GV-FS0-F1A-OPEN; ScopeID=GV_FS0_F1A_CERTIFIED_OPEN_VERTICAL; ChecksTotal=11; ChecksPassed=10; ChecksFailed=1; Verdict=BLOCK; OpenRisks=implementation_unbanked_and_independent_review_pending; NextAction=bank_F1A_then_run_distinct_A_B_C

ClosureValidation: PASS

SAWBlockValidation: PASS
